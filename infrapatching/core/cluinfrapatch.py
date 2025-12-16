# $Header: ecs/exacloud/exabox/infrapatching/core/cluinfrapatch.py /main/15 2025/08/13 05:47:58 jyotdas Exp $
#
# cluinfrapatch.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cluinfrapatch.py - Contains method to start infra patching operation
#
#    DESCRIPTION
#      Entry point for infra patching code execution handler
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jyotdas     07/18/25 - ER 38056425 - Handle elu in racks with node qmr at
#                           different versions on ecra
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    diguma      06/06/24 - Enh 36691192 - IN CASE OF ADBS, DURING DOM0/KVM
#                           HOST INFRA PATCHING RETRY EXECUTE DOM0DOMU PLUGIN
#    diguma      04/09/24 - Bug 36497510: EXACS:23.4.1.2.1:EXACLOUD:PATCHING:
#                           DOM0 PRECHECK DELETES
#                           '/OPT/EXACLOUD/CLUSTERS/SHARED_ENV_ENABLED' FILE
#    araghave    03/11/24 - Enh 36295801 - IMPLEMENT ONEOFFV2 PLUGIN EXACLOUD
#                           CHANGES
#    diguma      02/05/24 - Bug 36253736 - NEED TO ADD STORAGE TYPE ATTRIBUTE
#                           IN INFRAPATCHING WORKFLOW
#    jyotdas     05/15/23 - ENH 35382596 - Store idempotency metadata in ecra
#                           db for active-active upgrade during infrapatching
#    jyotdas     10/12/22 - BUG 34681939 - Infrapatching compute nodes should
#                           be sorted by dbserver name from ecra
#    jyotdas     07/07/22 - ENH 34316717 - Pass dom0 list and cell list as part
#                           of infrapatching payload
#    jyotdas     05/17/22 - ENH 34168677 - Enhance patch list api to consume
#                           the display flag based on retention policy
#    jyotdas     04/18/22 - ENH 34042048 - Exacloud api to list prior patch
#                           version
#    jyotdas     09/01/21 - Enh 33193949 - Move infra patching code execution
#                           from clucontrol.py
#    jyotdas     09/01/21 - Creation
#

import json, os
from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB
from exabox.infrapatching.handlers.handlertypes import getInfraPatchingTaskHandlerInstance
from exabox.infrapatching.handlers.loghandler import LogHandler
from exabox.core.Error import ebError
from exabox.infrapatching.utils.constants import KEY_NAME_CellPatchFile, KEY_NAME_SwitchPatchFile, KEY_NAME_DBPatchFile, \
KEY_NAME_Dom0_YumRepository, KEY_NAME_Domu_YumRepository, KEY_NAME_PatchFile, PATCH_CELL, PATCH_IBSWITCH, PATCH_ROCESWITCH, \
PAYLOAD_NON_RELEASE, PATCH_ALL, PATCH_DOM0 ,PATCH_DOMU, TASK_BACKUP_IMAGE, PATCH_SWITCH, EXADATA_BUNDLES_METADATA_FILE


class ebCluInfraPatch(LogHandler):

    def __init__(self, aExaBoxCluCtrl, aOptions):
        self.__config = get_gcontext().mGetConfigOptions()
        self.__basepath = get_gcontext().mGetBasePath()
        self.__xmlpath = aOptions.configpath
        self.__eboxCluCtrl = aExaBoxCluCtrl
        self.__options = aOptions

    def mInvokePatchExecutor(self,aCmd,aLogPath):

        self.mPatchLogInfo("Invoking Patch Executor in ebCluInfraPatch")
        # we create this additional directory 'patchmgr_logs or patch_logs'
        self.__eboxCluCtrl.mExecuteCmdLog('/bin/mkdir -p ' + aLogPath)
        self.mPatchLogInfo(f"Created directory {aLogPath}")
        _target_type = ['all_nodes']
        _op_style = 'rolling'
        _payload = 'release'
        _target_env = 'production'
        _patch_file_cells = ''
        _patch_files_dom0s_or_domus = ''
        _target_version = ''
        _cluster_id = None
        _provided_files = ''
        _enable_plugins = ''
        _plugin_types = ''
        _backup_mode = ''
        _fedramp = ''
        _retry_flag = ''
        _request_id = ''
        _rack_name = ''
        _computeNodeList = {}
        _storageNodeList = {}
        _dom0domuDetails = {}
        _eluTargetVersionToNodeMappings = {}
        _computeNodeListByAlias = {}
        _idemPotencyData = {}
        _infra_patch_plugin_metadata = {}
        _oneoff_script_alias = ''
        
        _isMVM = ''
        _shared_env = ''
        _storageType = ''
        _isADBS = ''

        # Patch called through a recursive call to exacloud
        if self.__options.jsonconf:
            _jconf = self.__options.jsonconf

            self.mPatchLogInfo("Infraptching payload :\n"+json.dumps(_jconf, indent=2))

            if 'TargetType' in _jconf:
                _target_type = _jconf['TargetType']
            else:
                self.mPatchLogError("'TargetType' field not provided.")
                return ebError(0x0602)

            if 'OperationStyle' in _jconf:
                _op_style = _jconf['OperationStyle']
            else:
                self.mPatchLogError("'OperationStyle' field not provided.")
                return ebError(0x0602)

            if 'BackupMode' in _jconf:
                _backup_mode = _jconf['BackupMode']
            else:
                self.mPatchLogError("'BackupMode' field not provided.")
                return ebError(0x0602)

            if 'EnablePlugins' in _jconf:
                _enable_plugins = _jconf['EnablePlugins']
            else:
                self.mPatchLogError("'EnablePlugins' field not provided.")
                return ebError(0x0602)

            if 'PluginTypes' in _jconf:
                _plugin_types = _jconf['PluginTypes']
            else:
                self.mPatchLogError("'PluginTypes' field not provided.")
                return ebError(0x0602)

            if 'Retry' in _jconf:
                _retry_flag = _jconf['Retry']
            else:
                self.mPatchLogError("'Retry' field not provided.")
                return ebError(0x0602)

            if 'RequestId' in _jconf:
                _request_id = _jconf['RequestId']
            else:
                self.mPatchLogError("Master Request id field not provided.")
                return ebError(0x0602)

            if 'RackName' in _jconf:
                _rack_name = _jconf['RackName']
            else:
                self.mPatchLogError("'RackName' field not provided.")
                return ebError(0x0602)

            if 'AdditionalOptions' in _jconf:
                _additional_options = _jconf['AdditionalOptions']

            if 'Fedramp' in _jconf:
                _fedramp = _jconf['Fedramp']
            else:
                self.mPatchLogError("'Fedramp' field not provided.")
                return ebError(0x0602)

            if 'PayloadType' in _jconf:
                _payload = _jconf['PayloadType']
            else:
                self.mPatchLogError("'PayloadType' field not provided.")
                return ebError(0x0602)

            if 'TargetEnv' in _jconf:
                _target_env = _jconf['TargetEnv']
            else:
                self.mPatchLogError("'TargetEnv' field not provided.")
                return ebError(0x0602)

            if 'TargetVersion' in _jconf:
                _target_version = _jconf['TargetVersion']
            else:
                self.mPatchLogError("'TargetVersion' field not provided.")
                return ebError(0x0602)

            if 'ComputeNodeList' in _jconf:
                _computeNodeList = _jconf['ComputeNodeList']
            else:
                self.mPatchLogInfo("ComputeNodeList field not provided.")

            if 'ComputeNodeListByAlias' in _jconf:
                _computeNodeListByAlias = _jconf['ComputeNodeListByAlias']
            else:
                self.mPatchLogInfo("ComputeNodeListByAlias field not provided.")

            if 'isMVM' in _jconf:
                _isMVM = _jconf['isMVM']
                if _isMVM.upper() == 'YES':
                    _shared_env = 'True'
            else:
                self.mPatchLogInfo("isMVM field not provided.")

            if 'storageType' in _jconf:
                _storageType = _jconf['storageType']
            else:
                self.mPatchLogInfo("storageType field not provided.")

            if 'adb_s' in _jconf:
                _isADBS = _jconf['adb_s']

            if 'StorageNodeList' in _jconf:
                _storageNodeList = _jconf['StorageNodeList']
            else:
                self.mPatchLogInfo("StorageNodeList field not provided.")

            if 'Dom0domUDetails' in _jconf:
                _dom0domuDetails = _jconf['Dom0domUDetails']
            else:
                self.mPatchLogInfo("Dom0domUDetails field not provided.")

            if 'ELUTargetVersiontoNodeMappings' in _jconf:
                _eluTargetVersionToNodeMappings = _jconf['ELUTargetVersiontoNodeMappings']
            else:
                self.mPatchLogInfo("ELUTargetVersiontoNodeMappings field not provided.")

            if 'InfraPatchPluginMetaData' in _jconf:
                _infra_patch_plugin_metadata = _jconf['InfraPatchPluginMetaData']
            else:
                self.mPatchLogInfo("InfraPatchPluginMetadata field not provided.")

            if 'OneoffScriptAlias' in _jconf:
                _oneoff_script_alias = _jconf['OneoffScriptAlias']
            else:
                self.mPatchLogInfo("OneoffScriptAlias field not provided.")

            if 'Idempotency' in _jconf:
                _idemPotencyData = _jconf['Idempotency']
            else:
                self.mPatchLogInfo("Idempotency field not provided.")

            if KEY_NAME_CellPatchFile in _jconf:
                _patch_file_cells = \
                    _jconf[KEY_NAME_CellPatchFile]

            elif KEY_NAME_SwitchPatchFile in _jconf:
                _patch_file_cells = \
                    _jconf[KEY_NAME_SwitchPatchFile]

            if KEY_NAME_DBPatchFile in _jconf:
                if KEY_NAME_Dom0_YumRepository in _jconf:
                    _patch_files_dom0s_or_domus = \
                        [_jconf[KEY_NAME_DBPatchFile],
                         _jconf[KEY_NAME_Dom0_YumRepository]]
                elif KEY_NAME_Domu_YumRepository in _jconf:
                    _patch_files_dom0s_or_domus = \
                        [_jconf[KEY_NAME_DBPatchFile],
                         _jconf[KEY_NAME_Domu_YumRepository]]
                else:
                    if PATCH_DOM0 in _target_type:
                        self.mPatchLogError(f"'{KEY_NAME_Dom0_YumRepository}' field not provided.")
                    if PATCH_DOMU in _target_type:
                        self.mPatchLogError(f"'{KEY_NAME_Domu_YumRepository}' field not provided.")

                    return ebError(0x0602)

            if KEY_NAME_PatchFile in _jconf:
                if PATCH_DOM0 in _target_type:
                    _patch_files_dom0s_or_domus = \
                        [_jconf[KEY_NAME_PatchFile]]

                    if KEY_NAME_Dom0_YumRepository in _jconf:
                        _patch_files_dom0s_or_domus.append(
                            _jconf[KEY_NAME_Dom0_YumRepository])

                if PATCH_DOMU in _target_type:
                    _patch_files_dom0s_or_domus = \
                        [_jconf[KEY_NAME_PatchFile]]

                    if KEY_NAME_Domu_YumRepository in _jconf:
                        _patch_files_dom0s_or_domus.append(
                            _jconf[KEY_NAME_Domu_YumRepository])

                if PATCH_CELL in _target_type or \
                        PATCH_IBSWITCH in _target_type or \
                        PATCH_SWITCH in _target_type:
                    _patch_file_cells = \
                        _jconf[KEY_NAME_PatchFile]

            if 'ClusterID' in _jconf:
                _cluster_id = int(_jconf['ClusterID'])

            # backup_image on cell and ibswitch is not supported
            if 'TargetType' in _jconf and 'Operation' in _jconf:
                for _type in _jconf['TargetType']:
                    if ((_type == PATCH_CELL or
                         _type == PATCH_IBSWITCH or
                         _type == PATCH_SWITCH) and
                            _jconf['Operation'] == TASK_BACKUP_IMAGE):
                        self.mPatchLogError(f"Image Backup on {_type.upper()} is not supported.")
                        return ebError(0x0602)

        # Patch called directly from cli
        else:

            if 'pnode_type' in self.__options and self.__options.pnode_type:
                _target_type = [self.__options.pnode_type.strip().lower()]
            else:
                self.mPatchLogError("Target type nos specified.")
                return ebError(0x0602)

            if 'patch_version_dom0s' in self.__options and self.__options.patch_version_dom0s:
                _target_version = self.__options.patch_version_dom0s

            else:
                self.mPatchLogError("Target version not specified.")
                return ebError(0x0602)

            if _target_type[0] in [PATCH_DOM0, PATCH_ALL]:

                for i in [0]:
                    _provided_files = ""
                    if 'patch_files_dom0s' in self.__options and self.__options.patch_files_dom0s:
                        _provided_files = self.__options.patch_files_dom0s
                        _patch_files_dom0s_or_domus = self.__options.patch_files_dom0s.strip().split(",")
                        if len(_patch_files_dom0s_or_domus) == 2:
                            break
                else:
                    self.mPatchLogError(
                        f"Dom0 patch zip files not specified. 2 files seperated by ',' are needed for dom0 patching. you provided '{_provided_files}' ")
                    return ebError(0x0602)

            if 'patch_file_cells' in self.__options and self.__options.patch_file_cells:
                _patch_file_cells = self.__options.patch_file_cells.strip()

            if _patch_file_cells == '' and _target_type[0] in [PATCH_CELL, \
                                                               PATCH_IBSWITCH, PATCH_SWITCH, PATCH_ALL]:
                self.mPatchLogError("Cell/Switch patch .zip file not specified.")
                return ebError(0x0602)

        if _payload == PAYLOAD_NON_RELEASE:
            self.mPatchLogWarn(f"Payload '{PAYLOAD_NON_RELEASE}' not supported yet. Nothing to be done.")
            return 0

        # Dump input information
        self.mPatchLogInfo(f'TargetType: {str(_target_type)}')
        self.mPatchLogInfo(f'OpStyle: {_op_style}')
        self.mPatchLogInfo(f'Payload: {_payload}')
        self.mPatchLogInfo(f'TargetEnv: {_target_env}')
        self.mPatchLogInfo(f'CellSwitchFile: {str(_patch_file_cells)}')
        self.mPatchLogInfo(f'DBPatchFiles: {str(_patch_files_dom0s_or_domus)}')
        self.mPatchLogInfo(f'TargetVersion: {_target_version}')

        # # Create clupatching instance
        # ER Bug31817570 - New entry to infra patching refactor code.
        _patch_args_dict = {
            "CluControl": self.__eboxCluCtrl,
            "LocalLogFile": aLogPath,
            "TargetType": _target_type,
            "isMVM": _isMVM,
            "shared_env": _shared_env,
            "storageType": _storageType,
            "Operation": aCmd,
            "OperationStyle": _op_style,
            "PayloadType": _payload,
            "TargetEnv": _target_env,
            "EnablePlugins": _enable_plugins,
            "PluginTypes": _plugin_types,
            "CellIBSwitchesPatchZipFile": _patch_file_cells,
            "Dom0DomuPatchZipFile": _patch_files_dom0s_or_domus,
            "TargetVersion": _target_version,
            "ClusterID": _cluster_id,
            "BackupMode": _backup_mode,
            "Fedramp": _fedramp,
            "Retry": _retry_flag,
            "RequestId": _request_id,
            "RackName": _rack_name,
            "AdditionalOptions": _additional_options,
            "ComputeNodeList":_computeNodeList,
            "ComputeNodeListByAlias": _computeNodeListByAlias,
            "StorageNodeList":_storageNodeList,
            "Dom0domUDetails":_dom0domuDetails,
            "ELUTargetVersiontoNodeMappings": _eluTargetVersionToNodeMappings,
            "Idempotency":_idemPotencyData,
            "InfraPatchPluginMetaData":_infra_patch_plugin_metadata,
            "OneoffScriptAlias":_oneoff_script_alias,
            "adb_s": _isADBS
        }

        _patch_mgr_return_val = 0
        _taskHandlerInstance = getInfraPatchingTaskHandlerInstance(_patch_args_dict)
        _patch_mgr_return_val = _taskHandlerInstance.mExecuteTask()
        return _patch_mgr_return_val

    def mEXACCInfraPatchPayloadList(self, aOptions):
        """
        List Patches Metadata file from /u01/downloads which describes PatchPayloads Directory
        :param aOptions:
        :return:
            {
                "priorpatchlist":
                [{"imageVersion": "21.2.6.0.0.211112", "patchType": "quarterly", "targetType": "dom0", "serviceType": "EXACC",'bpDate': '211112', 'bpName': '21.2.6.0.0'},
                {"imageVersion": "21.2.8.0.0.211012", "patchType": "quarterly", "targetType": "dom0", "serviceType": "EXACC", 'bpDate': '211012', 'bpName': '21.2.8.0.0'}}],
                "error": ""
            }
        """
        _ebox = self.__eboxCluCtrl
        _ociexacc = _ebox.mIsOciEXACC()
        _result_list = []
        _error_msg = None
        _final_response = {}

        self.mPatchLogInfo("Executing mEXACCInfraPatchPayloadList to fetch patch payloads from metadata")
        _rc = 0
        if not _ociexacc:
            _error_msg = "Fetching Patch Payload Versions from metadata is applicable only for EXACC"
            self.mPatchLogError(_error_msg)
        else:
            _repository_root = _ebox.mCheckConfigOption("repository_root")
            if _repository_root is None:
                _repository_root = '/u01/downloads'
            else:
                self.mPatchLogInfo(f"_repository_root from config file {str(_repository_root)} ")

            _patch_payloads_json_metadata = os.path.join(_repository_root, EXADATA_BUNDLES_METADATA_FILE)
            self.mPatchLogInfo(f"_patch_payloads_json_metadata {str(_patch_payloads_json_metadata)} ")

            if os.path.exists(_patch_payloads_json_metadata) and os.stat(_patch_payloads_json_metadata).st_size > 0:
                try:
                    with open(_patch_payloads_json_metadata) as json_read:
                        _patch_payloads_json_obj = json.load(json_read)
                except:
                    _error_msg = f"Patch Payloads JSON metadata file {str(_patch_payloads_json_metadata)} has Invalid JSON"
                    self.mPatchLogError(_error_msg)
            else:
                _error_msg = f"Patch Payloads JSON metadata file {str(_patch_payloads_json_metadata)}  does not exist"
                self.mPatchLogError(_error_msg)

            # Get filter values
            _target_types_filter_value = None
            _patch_type_filter_value = None
            _service_type_filter_value = None
            if aOptions is not None and aOptions.jsonconf is not None:
                if 'target_types' in aOptions.jsonconf.keys():
                    _target_types_filter_value = aOptions.jsonconf.get('target_types')
                if 'patch_type' in aOptions.jsonconf.keys():
                    _patch_type_filter_value = aOptions.jsonconf.get('patch_type')
                if 'service_type' in aOptions.jsonconf.keys():
                    _service_type_filter_value = aOptions.jsonconf.get('service_type')

            if _target_types_filter_value is None or _patch_type_filter_value is None or _service_type_filter_value is None:
                _error_msg = "One or more of filter values not specified properly for mEXACCInfraPatchPayloadList"
                self.mPatchLogError(_error_msg)
            else:
                self.mPatchLogInfo(f"Target Types filter specified from params is {_target_types_filter_value} ")
                self.mPatchLogInfo(f"Patch Type filter specified is {_patch_type_filter_value} ")
                self.mPatchLogInfo(f"Service Type filter specified  is {_service_type_filter_value} ")


            if not _error_msg:
                #Multiple targetTypes can be specified like dom0+cell
                targetTypesParamList = []
                if _target_types_filter_value.find("+") > -1:
                    targetTypesParamList = _target_types_filter_value.split("+")
                else:
                    targetTypesParamList.append(_target_types_filter_value)

                self.mPatchLogInfo(f"Filtering data for target types {str(targetTypesParamList)} ")
                for _target in targetTypesParamList:
                    for _item in _patch_payloads_json_obj['payloads']:

                        #If display attribute is not present in json, bundle will be displayed.
                        # bundles which are not to be displayed must have displayed:no set as part of the json
                        if "display" in _item.keys() and _item["display"].upper() == "NO":
                            continue
                        if _target in _item["targetTypes"][0]:
                            _bp_date = ""
                            _bp_name = ""
                            _patch_type = _item["patchType"]
                            _image_version = _item["imageVersion"]
                            _service_type = _item["serviceType"]
                            if _item["bp_date"]:
                                _bp_date = _item["bp_date"]
                            if _item["bp_name"]:
                                _bp_name = _item["bp_name"]
                            if _patch_type.upper() == _patch_type_filter_value.upper() and _service_type.upper() == _service_type_filter_value.upper():
                                _result_list.append({'imageVersion': _image_version, 'patchType': _patch_type.upper(),
                                          'targetType': _target, 'serviceType': _service_type,
                                           'bpDate': _bp_date, 'bpName': _bp_name})

        if _result_list == [] and _error_msg is None:
            self.mPatchLogInfo("Final result is empty")
            _error_msg = "No Data Found for Patch List"

        if _error_msg:
            _final_response["error"] = _error_msg
        _final_response["patchlist"] = _result_list
        if _final_response:
            self.mPatchLogInfo(f"Final Response {str(_final_response)} ")

        #
        # Update Data request obj
        #
        _db = ebGetDefaultDB()
        _reqobj = _ebox.mGetRequestObj()
        if _reqobj:
            _reqobj.mSetData(json.dumps(_final_response, indent=4))
            _db.mUpdateRequest(_reqobj)

        return 0 #Success
