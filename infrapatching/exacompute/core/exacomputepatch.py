#!/bin/python
#
# $Header: ecs/exacloud/exabox/infrapatching/exacompute/core/exacomputepatch.py /main/8 2025/05/07 04:51:45 araghave Exp $
#
# exacomputepatch.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      exacomputepatch.py -
#
#    DESCRIPTION
#      Landing file for exacompute patching
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    03/17/25 - Enh 37713042 - CONSUME ERROR HANDLING DETAILS FROM
#                           INFRAPATCHERROR.PY DURING EXACOMPUTE PATCHING
#    araghave    01/27/25 - Enh 37132175 - EXACOMPUTE MUST REUSE INFRA PATCHING
#                           MODULES FOR VALIDATION AND PATCH OPERATIONS
#    araghave    08/27/24 - Enh 36971710 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE EXACOMPUTE FILES
#    apotluri    12/14/23 - Bug 36107235 - ECRA REQUEST STATUS FOR EXACOMPUTE
#                           OPS SHOWS INVALID LOCATION IN EXACLOUD_THREAD_LOG
#    araghave    06/23/23 - Enh 35416441 - Support monthly security patching
#                           for exacompute hosts
#    sdevasek    11/16/22 - ENH 34384801 - CONSOLIDATE NOTIFICATION ACROSS
#                           MULTIPLE PATCHMGR OPERATIONS
#    araghave    08/12/22 - Enh 34350140 - EXACLOUD CHANGES TO HANDLE
#                           EXACOMPUTE PRECHECK AND PATCHING OPERATIONS
#    jyotdas     07/19/22 - ENH 34350151 - Exacompute Infrapatching
#    jyotdas     07/19/22 - Creation
#

import json
from exabox.core.Context import get_gcontext
from exabox.infrapatching.exacompute.handlers.exacomputehandlertypes import getExaComputeHandlerInstance
from exabox.infrapatching.core.infrapatcherror import *
from exabox.infrapatching.utils.constants import PATCH_DOM0
from exabox.infrapatching.handlers.loghandler import LogHandler
from exabox.core.DBStore import ebGetDefaultDB
from exabox.log.LogMgr import ebLogInfo, ebLogError
from exabox.infrapatching.utils.utility import mGetFirstDirInZip, mGetInfraPatchingKnownAlert, mFormatOut, mGetInfraPatchingConfigParam, mGetSshTimeout

class ebCluExaComputePatch(LogHandler):

    def __init__(self, aExaBoxCluCtrl, aOptions):
        self.__config = get_gcontext().mGetConfigOptions()
        self.__basepath = get_gcontext().mGetBasePath()
        self.__xmlpath = aOptions.configpath
        self.__eboxCluCtrl = aExaBoxCluCtrl
        self.__options = aOptions

    @staticmethod
    def mUpdateRequestData(_requestObj, aData = None, aOptions = None, aStatusObj=None, aDetailsErr=None):
        """
        Updates request object with the response payload
        Progress percent data is created based on the code below by the caller

        _data = {} <== Passed as aData argument above
        _data["service"] = "ExaCompute Patch"
        _node_progress_list = []
        patch_progressing_status_json = {}
        _node_progress_list.append({'node_name': "slcs27adm01.us.oracle.com",
                                    'patchmgr_start_time': "07-27-2022 10:50",
                                    'last_updated_time': "07-27-2022 10:55",
                                    'status': "Progressing", 'status_details': "Succeeded"}
                                   )
        _node_progress_list.append({'node_name': "slcs27adm02.us.oracle.com",
                                    'patchmgr_start_time': "07-27-2022 10:50",
                                    'last_updated_time': "07-27-2022 10:54",
                                    'status': "Pending", 'status_details': "Pending"}
                                   )

        patch_progressing_status_json['node_patching_progress_data'] = _node_progress_list
        _data["node_patching_status"] = patch_progressing_status_json
        ebCluExaComputePatch.mUpdateRequestData(self.mGetRequestObj(), aOptions=self.mGetInputPayload(), aData=_data)
        """
        _target_version = ''
        _op_style = ''
        _operation = ''
        _launchnodes = ''
        _reqobj = _requestObj
        _response = {}
        _data = {}
        _node_list = []

        if aOptions:
            _inputPayload = aOptions.jsonconf
            if 'TargetVersion' in _inputPayload:
                _target_version = _inputPayload['TargetVersion']
            if 'OperationStyle' in _inputPayload:
                _op_style = _inputPayload['OperationStyle']
            if 'Operation' in _inputPayload:
                _operation = _inputPayload['Operation']
            if 'NodeList' in _inputPayload:
                _node_list = _inputPayload['NodeList']

        if aData is None:
            _data = {}
            _data["service"] = "ExaCompute Patch"
            _data["node_patching_status"] = {}
        else:
            _data = aData

        if aStatusObj:
            _data["status"] = aStatusObj[0]
            _data["status_message"] = aStatusObj[1]

        if aDetailsErr is not None:
            _data["status_message"] = aDetailsErr

        #Calculate patch progress data based on the number of nodes completed/total number of nodes
        if aData and _node_list and len(_node_list) > 0:
            _completed_nodes = 0
            _total_nodes = len(_node_list)
            if "node_patching_status" in aData.keys():
                _node_patch_status = aData["node_patching_status"]
                if "launch_node" in _node_patch_status.keys():
                    _data["launch_node"] = _node_patch_status["launch_node"]
                if "node_patching_progress_data" in _node_patch_status.keys():
                    _node_progress_list = _node_patch_status["node_patching_progress_data"]
                    for _item in _node_progress_list:
                        if "status_details" in _item.keys() and _item["status_details"].upper() == "SUCCEEDED":
                            _completed_nodes = _completed_nodes + 1
                    if _completed_nodes > 0:
                        _data["completion_percentage"] = str(int(_completed_nodes * 100/_total_nodes))

        _data["TargetVersion"] = _target_version
        _data["OperationStyle"] = _op_style
        _data["Operation"] = _operation
        _data["service"] = "ExaCompute Patch"
        if _reqobj:
            _master_uuid=_reqobj.mGetUUID()
            if _master_uuid:
                _data["master_request_uuid"] =_master_uuid
                _exacloud_thread_log= f"{get_gcontext().mGetBasePath()}/log/threads/0000-0000-0000-0000/00000000-0000-0000-0000-000000000000/{_master_uuid}_cluctrl.exacompute_patch_nodes.log"
                _data["exacloud_thread_log"] = _exacloud_thread_log

        _response["output"] = _data

        if _reqobj is not None:
            _db = ebGetDefaultDB()
            _reqobj.mSetData(json.dumps(_response, sort_keys=True))
            _db.mUpdateRequest(_reqobj)
        elif aOptions and aOptions.jsonmode:
            ebLogInfo(json.dumps(_response, indent=4, sort_keys=True))

    @staticmethod
    def mGetRequestData(aRequestUUID):
        """
        Retrieves the content of data column from requests table for the requestid passed
        Sample output for the request id:
        {
          "output": {
            "Operation": "patch",
            "OperationStyle": "non-rolling",
            "TargetVersion": "22.1.3.0.0.220914",
            "node_patching_status": {
              "launch_node": "slcs27adm01",
              "node_patching_progress_data": [
                {
                  "from_version": "22.1.3.0.0.220914",
                  "last_updated_time": "2022-11-16 06:49:25+0000",
                  "node_name": "slcs27adm04.us.oracle.com",
                  "patch_sub_operation": "PATCHMGR_PATCH",
                  "patchmgr_start_time": "2022-11-16 06:48:56+0000",
                  "patchmgr_status": "Succeeded",
                  "status": "Completed",
                  "to_version": "22.1.3.0.0.220914"
                },
                {
                  "from_version": "21.1.0.0.0.210319",
                  "last_updated_time": "2022-11-16 06:48:09+0000",
                  "node_name": "slcs27adm02.us.oracle.com",
                  "patch_sub_operation": "PATCHMGR_PRECHECK",
                  "patchmgr_start_time": "2022-11-16 06:42:54+0000",
                  "patchmgr_status": "Failed",
                  "status": "Completed",
                  "to_version": "22.1.3.0.0.220914"
                },
                {
                  "from_version": "22.1.0.0.0.220518",
                  "last_updated_time": "2022-11-16 06:48:13+0000",
                  "node_name": "slcs27adm03.us.oracle.com",
                  "patch_sub_operation": "PATCHMGR_PRECHECK",
                  "patchmgr_start_time": "2022-11-16 06:42:54+0000",
                  "patchmgr_status": "Failed",
                  "status": "Completed",
                  "to_version": "22.1.3.0.0.220914"
                }
              ]
            },
            "service": "ExaCompute Patch",
            "status": "0x03010045",
            "status_message": "Although upgrade operation was successful on the nodes : ['slcs27adm04.us.oracle.com'], prechecks failed on ['slcs27adm02.us.oracle.com', 'slcs27adm03.us.oracle.com'] and hence were not upgraded."
          }
        }
        """

        _request_data = None
        try:
            _db = ebGetDefaultDB()
            _row = _db.mGetRequest(aRequestUUID)
            _request_data_str = _row[13]
            _request_data = json.loads(_request_data_str)
        except Exception as e:
            ebLogError(f'Exception in fetching data field from request table  {str(e)}')
        return _request_data

    def mInvokeExaComputePatch(self,aLogPath):

        '''
               {
                   "RequestId": "6d810350-1171-40cc-9cb5-ac5ca9dd4ca8",
                   "Operation": "patch",
                   "OperationStyle": "non-rolling",
                   "PatchingType":"ExaCompute", <== pass this flag to Exacloud for any specific checks
                   "TargetVersion":"21.2.8.0.0.211012",    <== version evaluated based on patch registration
                   "NodeList": [
                       "slcs27adm03.us.oracle.com",
                       "slcs27adm04.us.oracle.com"
                   ]
               }
        '''

        _ret = PATCH_SUCCESS_EXIT_CODE
        self.mPatchLogInfo("Invoking Patch Executor for ExaCompute")

        # we create this additional directory 'patchmgr_logs or patch_logs'
        self.__eboxCluCtrl.mExecuteCmdLog('/bin/mkdir -p ' + aLogPath)
        self.mPatchLogInfo(f"Created directory {aLogPath}")
        _node_list = []
        _launch_nodes = []
        _op_style = 'non-rolling'
        _target_type = [ PATCH_DOM0 ]
        _is_exacompute_patching = True
        _additional_options = [{"ClusterLess": "no"}]
        _rack_name = "exacompute"
        _ecra_request_id = ''
        _operation = ''
        _is_exasplice = ''
        _detail_error = ''
        _data = {}
        _errString = None
        _errObj = None

        _additional_options_list = mGetInfraPatchingConfigParam('exacompute_patchmgr_additional_options')
        _ignore_alerts_settings = _additional_options_list['IgnoreAlerts']
        if not _ignore_alerts_settings:
           _ignore_alerts_settings = "no"

        _allow_active_nfs_mounts_settings = _additional_options_list['AllowActiveNfsMounts']
        if not _allow_active_nfs_mounts_settings:
            _allow_active_nfs_mounts_settings = "no"

        _force_remove_custom_rpm_settings = _additional_options_list['ForceRemoveCustomRpms']
        if not _force_remove_custom_rpm_settings:
            _force_remove_custom_rpm_settings = "no"

        _is_additional_precheck_enabled = _additional_options_list['is_additional_precheck_priortopatch_enabled']
        if not _is_additional_precheck_enabled:
            _is_additional_precheck_enabled = "no"

        _additional_options = [{"ClusterLess": "no", "IgnoreAlerts": _ignore_alerts_settings, "AllowActiveNfsMounts": _allow_active_nfs_mounts_settings, "ForceRemoveCustomRpms": _force_remove_custom_rpm_settings, "is_additional_precheck_priortopatch_enabled": _is_additional_precheck_enabled}]

        # Response Data to be returned
        _data = {}
        _data["service"] = "ExaCompute Patch"
        _data["node_patching_status"] = {}

        if self.__options.jsonconf:
            _jconf = self.__options.jsonconf

            self.mPatchLogInfo(json.dumps(_jconf, indent=2))

            if 'TargetVersion' in _jconf:
                _target_version = _jconf['TargetVersion']
                self.mPatchLogInfo(f"TargetVersion is {_target_version} ")
            else:
                _errObj = ebPatchFormatBuildErrorWithErrorAction(TARGET_VERSION_NOT_SPECIFIED, aTargetTypes=_target_type)
                if _errObj:
                    mUpdateErrorObjectToDB(self.__eboxCluCtrl, _errObj)
                    _ret = _errObj[0]
                ebCluExaComputePatch.mUpdateRequestData(self.__eboxCluCtrl.mGetRequestObj(), aData=_data, aOptions=self.__options, aStatusObj= _errObj)
                return _ret

            if 'OperationStyle' in _jconf:
                _op_style = _jconf['OperationStyle']
                self.mPatchLogInfo(f"OperationStyle is {_op_style} ")
            else:
                _op_style = 'non-rolling'
                self.mPatchLogInfo(f"OperationStyle is {_op_style} ")

            if 'RequestId' in _jconf:
                _ecra_request_id = _jconf['RequestId']
                self.mPatchLogInfo(f"_ecra_request_id is {_ecra_request_id} ")

            # Currently only patch operation for ExaCompute
            if 'Operation' in _jconf:
                _operation = _jconf['Operation']
                self.mPatchLogInfo(f"Operation is {_operation} ")
            else:
                self.mPatchLogError("'Operation' field not provided.")
                _errObj = ebPatchFormatBuildErrorWithErrorAction(OPERATION_NOT_SPECIFIED, aTargetTypes=_target_type)
                if _errObj:
                    mUpdateErrorObjectToDB(self.__eboxCluCtrl, _errObj)
                    _ret = _errObj[0]
                ebCluExaComputePatch.mUpdateRequestData(self.__eboxCluCtrl.mGetRequestObj(), aData=_data, aOptions=self.__options, aStatusObj= _errObj)
                return _ret

            if 'LaunchNodes' in _jconf:
                _launch_nodes = _jconf['LaunchNodes']
                if _launch_nodes and len(_launch_nodes) > 0:
                    for _nd in _launch_nodes:
                        self.mPatchLogInfo(f"Launch Nodes are {_nd} ")
                else:
                    self.mPatchLogError("'LaunchNodes' field is Empty.")

            if 'exasplice' in _jconf:
                _is_exasplice = _jconf['exasplice']
                self.mPatchLogInfo(f"Exasplice patching specified = {str(_is_exasplice)}")
            else:
                self.mPatchLogWarn("exasplice field is Empty.")

            '''
             Since exacompute patching is done on Dom0 Target and 
             most of infra patching methods used during dom0 infra 
             patching are re-used during exacompute patching, target
             type is set to Dom0.
            '''
            _target_type = [ PATCH_DOM0 ]

            if 'NodeList' in _jconf:
                _node_list = _jconf['NodeList']
                if _node_list and len(_node_list) > 0:
                    for _nd in _node_list:
                        self.mPatchLogInfo(f"Node name is {_nd} ")
                else:
                    self.mPatchLogError("'NodeList' field is Empty.")
            else:
                _errObj = ebPatchFormatBuildErrorWithErrorAction(NODE_LIST_NOT_SPECIFIED, aTargetTypes=_target_type)
                if _errObj:
                    mUpdateErrorObjectToDB(self.__eboxCluCtrl, _errObj)
                    _ret = _errObj[0]
                ebCluExaComputePatch.mUpdateRequestData(self.__eboxCluCtrl.mGetRequestObj(), aData=_data, aOptions=self.__options, aStatusObj= _errObj)
                return _ret

            _patch_args_dict = {
                "CluControl": self.__eboxCluCtrl,
                "RequestObj": self.__eboxCluCtrl.mGetRequestObj(),
                "LocalLogFile": aLogPath,
                "Operation": _operation,
                "OperationStyle": _op_style,
                "TargetVersion": _target_version,
                "NodeList": _node_list,
                "LaunchNodes": _launch_nodes,
                "InputPayload":self.__options,
                "RequestId":_ecra_request_id,
                "IsExasplice":_is_exasplice,
                "isExaComputePatching": _is_exacompute_patching,
                "TargetType": _target_type,
                "AdditionalOptions": _additional_options,
                "RackName": _rack_name
            }

            _reqObjStatusUpdate = f"ExaCompute Node Patching Started for Nodes {str(_node_list)} with TargetVersion {_target_version} "

            _patch_mgr_return_val = PATCH_SUCCESS_EXIT_CODE
            self.__eboxCluCtrl.mUpdateStatus(_reqObjStatusUpdate, False)
            _exaHandlerInstance = getExaComputeHandlerInstance(_patch_args_dict)
            _patch_mgr_return_val = _exaHandlerInstance.mExecuteTask()
            return _patch_mgr_return_val

        else:
            _errObj = ebPatchFormatBuildErrorWithErrorAction(JSON_CONF_FILE_NOT_SPECIFIED, aTargetTypes=_target_type)
            if _errObj:
                mUpdateErrorObjectToDB(self.__eboxCluCtrl, _errObj)
                _ret = _errObj[0]
            ebCluExaComputePatch.mUpdateRequestData(self.__eboxCluCtrl.mGetRequestObj(), aData=_data, aOptions=self.__options, aStatusObj=_errObj)
            return _ret
