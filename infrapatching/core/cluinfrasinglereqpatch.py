#!/bin/python
#
# $Header: ecs/exacloud/exabox/infrapatching/core/cluinfrasinglereqpatch.py /main/6 2025/08/20 05:15:38 apotluri Exp $
#
# cluinfrasinglereqpatch.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cluinfrasinglereqpatch.py - Executes infrapatching operation in a single thread
#
#    DESCRIPTION
#      Executes infrapatching operation in a single thread
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jyotdas     02/11/26 - Enh - Allow LATEST targetVersion for DOM0
#                           exasplice patching
#    apotluri    07/25/25 - Bug 38096654 - PRECHECK OF SMR FAILED WITH
#                           'DIRECTORY FOR EXADATA_RELEASE HAS MORE THAN ONE
#                           PATCH'
#    jyotdas     07/18/25 - ER 38056425 - Handle elu in racks with node qmr at
#                           different versions on ecra
#    jyotdas     06/11/25 - Enh 37912226 - Identify proper targetversion for
#                           elu in exacs infrapatching
#    araghave    04/02/25 - Enh 37515129 - EXACS | INFRAPATCHING NEED TO USE
#                           LATEST DBNU
#    apotluri    03/02/25 - Bug 37612704 - FIX INCORRECT VARIABLE DECLARATION
#                           IN MCHECKEXACLOUDMNT CAUSING
#                           EXACLOUD_PATCH_WORKING_SPACE_MB TO BE IGNORED
#    jyotdas     10/01/24 - ER 37089701 - ECRA Exacloud integration to enhance
#                           infrapatching operation to run on a single thread
#    jyotdas     10/01/24 - Creation
#

import datetime
import json
import traceback
import uuid
import glob
from pathlib import Path

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.ovm.clumisc import OracleVersion
from exabox.core.DBStore import ebGetDefaultDB
from exabox.infrapatching.core.cluinfrapatch import ebCluInfraPatch
from exabox.infrapatching.handlers.handlertypes import getInfraPatchingTaskHandlerInstance
from exabox.core.DBStore import ebGetDefaultDB
from exabox.log.LogMgr import ebLogInfo, ebLogError
from exabox.infrapatching.handlers.loghandler import LogHandler
from exabox.core.Error import ebError
from exabox.infrapatching.utils.constants import KEY_NAME_CellPatchFile, KEY_NAME_SwitchPatchFile, KEY_NAME_DBPatchFile, \
KEY_NAME_Dom0_YumRepository, KEY_NAME_Domu_YumRepository, KEY_NAME_PatchFile, PATCH_CELL, PATCH_IBSWITCH, PATCH_ROCESWITCH, \
PAYLOAD_NON_RELEASE, PATCH_ALL, PATCH_DOM0 ,PATCH_DOMU, TASK_BACKUP_IMAGE, PATCH_SWITCH, EXADATA_BUNDLES_METADATA_FILE
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.infrapatching.utils.utility import mGetInfraPatchingConfigParam, mTruncateErrorMessageDescription, runInfraPatchCommandsLocally, mQuarterlyVersionPatternMatch, mIsLatestTargetVersionAllowed


class ebCluInfraSingeRequestPatch(ebCluInfraPatch):

    LOG_DIRECTORY = 'log/patch/'
    LATEST_VER_FROM_FILESYSTEM = 'fileSystem'
    REGISTRY_ENTRY = 'patch_monitor_cmd'
    SLEEP_TIME = 30
    RETRY_TIME = 10
    EXACLOUD_PATCH_WORKING_SPACE_MB = 0
    CHECK_FOLDER_EXISTS_RETRY_TIME_IN_SECONDS = 3
    STEP_PARSE_JSON = 'parse_json_file'
    STEP_DOWNLOAD = 'download_patch_files'
    STEP_POPULATE_TABLES = 'populate_tables'
    STEP_MONITOR = 'patch_monitor'
    OCIEXACC_LOC = ''

    def __init__(self, aExaBoxCluCtrl, aOptions):
        self.__config = get_gcontext().mGetConfigOptions()
        self.__basepath = get_gcontext().mGetBasePath()
        self.__xmlpath = aOptions.configpath
        self.__hostname = None
        self.__options = aOptions
        self.__cluctrl = aExaBoxCluCtrl
        self.__object_store = {}
        self.__json_status = None
        self.__child_request_uuid = self.__cluctrl.mGetRequestObj().mGetUUID()
        self.__job =  self.__cluctrl.mGetRequestObj()
        self.__sanitizedPayload = {}

        if 'hostname' in aOptions:
            self.__hostname = aOptions.hostname

        # Get Patchpayload location.
        if not self.mGetPatchPayLoad():
            self.mPatchLogError("Patch Stage location for ociexacc environment not specified in exabox.conf")
        self.PATCH_PAYLOADS_DIRECTORY = self.mGetPatchPayLoad()
        self.__logDir = self.mCreateLogDirectory()
        #self.mGetLogPath() = $EC_HOME/oeda/requests/96c8c3f2-26fa-11ef-bb06-0200170667b1/log/patchmgr_logs
        self.__oeda_patch_mgr_log_dir = None
        self.__latest_verion_source_loc = self.LATEST_VER_FROM_FILESYSTEM

    def mCreateLogDirectory(self):
        """
        Creates a log directory for the master request. This will have symlinks to
        individual worker log directories for all the patch workers.
        Example: exacloud/log/patch/<master_request_UUID>
        """

        try:
            _req = self.__cluctrl.mGetRequestObj()
            if _req:
                _dir = self.LOG_DIRECTORY + _req.mGetUUID()
                _node = exaBoxNode(get_gcontext(), aLocal=True)
                _node.mConnect(aHost="localhost")
                _node.mExecuteCmd('mkdir -p ' + _dir)
                return _dir
            else:
                raise Exception
        except:
            self.mPatchLogWarn("No log directory will be created.")
            self.mPatchLogTrace(traceback.format_exc())

        return None

    def mGetPatchPayLoad(self):
        """
        In case of OCI EXACC environemnts, PatchPayload details are fetched
        from ociexacc_exadata_patch_download_loc parameter as per details from
        the exabox.conf file.
        """

        patch_payloads_directory = 'PatchPayloads/'
        self.OCIEXACC = self.__cluctrl.mCheckConfigOption('ociexacc')
        if self.OCIEXACC == "True":
            self.OCIEXACC_LOC = self.__cluctrl.mCheckConfigOption('ociexacc_exadata_patch_download_loc').strip()
            if (self.OCIEXACC_LOC == '' or self.OCIEXACC_LOC == None or not self.OCIEXACC_LOC):
                patch_payloads_directory = False
            else:
                patch_payloads_directory = self.OCIEXACC_LOC + 'PatchPayloads/'
        else:
            self.mPatchLogInfo('*** ociexacc parameter is set to False. Retaining the patch path to default exacloud location.')
        return patch_payloads_directory

    def mInvokePatchExecutor(self,aCmd,aLogPath):

        _rc = PATCH_SUCCESS_EXIT_CODE
        self.mPatchLogInfo("Invoking Single Request Patch Executor in ebCluInfraSingeRequestPatch")
        self.__cluctrl.mExecuteCmdLog('/bin/mkdir -p ' + aLogPath)
        self.mPatchLogInfo("Created oeda patchmgr_log directory %s" % aLogPath)
        self.__oeda_patch_mgr_log_dir = aLogPath

        #Perform validations and sanitize payload
        _rc , _suggestion_msg = self.mValidateandSanitizePayload(self.__options)

        if _rc != PATCH_SUCCESS_EXIT_CODE:
            self.mPatchLogInfo(f"mInvokePatchExecutor Error {_suggestion_msg}")
            self.mAddPrePatchError(_rc, _suggestion_msg)
            self.mPatchLogTrace(traceback.format_exc())
            _patch_json_status = self.mGetPatchJsonStatus()
            if _patch_json_status:
                ebLogInfo(f"mInvokePatchExecutor: Patch JSON report with error code and error message is{_patch_json_status}")
                self.__job.mSetData(json.dumps(_patch_json_status))
                _error_msg = _patch_json_status["data"]["error_message"]
                self.mPatchLogError(f"mDispatchCluster: Error Message {_error_msg}")
            return _rc

        # we create this additional directory 'patchmgr_logs or patch_logs'
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
        operation = ''
        
        _isMVM = ''
        _shared_env = ''
        _storageType = ''
        _isADBS = ''

        # Patch execution
        if self.__sanitizedPayload:
            if KEY_NAME_CellPatchFile in self.__sanitizedPayload:
                _patch_file_cells = \
                    self.__sanitizedPayload[KEY_NAME_CellPatchFile]

            elif KEY_NAME_SwitchPatchFile in self.__sanitizedPayload:
                _patch_file_cells = \
                    self.__sanitizedPayload[KEY_NAME_SwitchPatchFile]

            if KEY_NAME_DBPatchFile in self.__sanitizedPayload:
                if KEY_NAME_Dom0_YumRepository in self.__sanitizedPayload:
                    _patch_files_dom0s_or_domus = \
                        [self.__sanitizedPayload[KEY_NAME_DBPatchFile],
                         self.__sanitizedPayload[KEY_NAME_Dom0_YumRepository]]
                elif KEY_NAME_Domu_YumRepository in self.__sanitizedPayload:
                    _patch_files_dom0s_or_domus = \
                        [self.__sanitizedPayload[KEY_NAME_DBPatchFile],
                         self.__sanitizedPayload[KEY_NAME_Domu_YumRepository]]
                else:
                    if PATCH_DOM0 in _target_type:
                        self.mPatchLogError("'%s' field not provided." % \
                                   KEY_NAME_Dom0_YumRepository)
                    if PATCH_DOMU in _target_type:
                        self.mPatchLogError("'%s' field not provided." % \
                                   KEY_NAME_Domu_YumRepository)

                    return ebError(0x0602)

            if KEY_NAME_PatchFile in self.__sanitizedPayload:
                if PATCH_DOM0 in _target_type:
                    _patch_files_dom0s_or_domus = \
                        [self.__sanitizedPayload[KEY_NAME_PatchFile]]

                    if KEY_NAME_Dom0_YumRepository in self.__sanitizedPayload:
                        _patch_files_dom0s_or_domus.append(
                            self.__sanitizedPayload[KEY_NAME_Dom0_YumRepository])

                if PATCH_DOMU in _target_type:
                    _patch_files_dom0s_or_domus = \
                        [self.__sanitizedPayload[KEY_NAME_PatchFile]]

                    if KEY_NAME_Domu_YumRepository in self.__sanitizedPayload:
                        _patch_files_dom0s_or_domus.append(
                            self.__sanitizedPayload[KEY_NAME_Domu_YumRepository])

                if PATCH_CELL in _target_type or \
                        PATCH_IBSWITCH in _target_type or \
                        PATCH_SWITCH in _target_type:
                    _patch_file_cells = \
                        self.__sanitizedPayload[KEY_NAME_PatchFile]

            self.mPatchLogInfo(f'CellSwitchFile: {str(_patch_file_cells)}')
            self.mPatchLogInfo(f'DBPatchFiles: {str(_patch_files_dom0s_or_domus)}')
            self.__sanitizedPayload["CellIBSwitchesPatchZipFile"] = _patch_file_cells
            self.__sanitizedPayload["Dom0DomuPatchZipFile"] = _patch_files_dom0s_or_domus

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
                    self.mPatchLogError("Dom0 patch zip files not specified. 2 files seperated by ',' are "
                               "needed for dom0 patching. you provided '%s' " % (_provided_files))
                    return ebError(0x0602)

            if 'patch_file_cells' in self.__options and self.__options.patch_file_cells:
                _patch_file_cells = self.__options.patch_file_cells.strip()

            if _patch_file_cells == '' and _target_type[0] in [PATCH_CELL, \
                                                               PATCH_IBSWITCH, PATCH_SWITCH, PATCH_ALL]:
                self.mPatchLogError("Cell/Switch patch .zip file not specified.")
                return ebError(0x0602)

        if _payload == PAYLOAD_NON_RELEASE:
            self.mPatchLogWarn("Payload '%s' not supported yet. Nothing to be done." % PAYLOAD_NON_RELEASE)
            return _rc

        _target_type = []
        _operation = ''
        _rackName = ''
        _targetVersion = ''
        if 'TargetType' in self.__sanitizedPayload:
            _target_type = self.__sanitizedPayload['TargetType']
        if 'Operation' in self.__sanitizedPayload:
            _operation = self.__sanitizedPayload['Operation']
        if 'RackName' in self.__sanitizedPayload:
            _rackName = self.__sanitizedPayload['RackName']
        if 'TargetVersion' in self.__sanitizedPayload:
            _targetVersion = self.__sanitizedPayload['TargetVersion']

        _reqObjStatusUpdate = f"Singe Request  operation {_operation} started on cluster {_rackName} with TargetVersion {_targetVersion} for targetType {str(_target_type)}"
        self.mPatchLogInfo(_reqObjStatusUpdate)
        self.__cluctrl.mUpdateStatus(_reqObjStatusUpdate, False)

        #Create master request
        self.mUpdateRequestData(self.__cluctrl.mGetRequestObj(), aOptions= self.__sanitizedPayload)

        #Create child request for patchlist table which is same as master request
        _child_request_uuid = self.__cluctrl.mGetRequestObj().mGetUUID()
        _db = ebGetDefaultDB()
        _db.mInsertChildRequestToPatchList(self.__cluctrl.mGetRequestObj().mGetUUID(), _child_request_uuid,'Pending')

        self.mPatchLogInfo(f"ExacloudMasterReqUUID = {self.__cluctrl.mGetRequestObj().mGetUUID()}")
        self.mPatchLogInfo(f"ExacloudChildReqUUID = {_child_request_uuid}")

        self.mPatchLogInfo("Single Request Infraptching payload :\n"+json.dumps(self.__sanitizedPayload, indent=2))
        #Add the Clucontrol object after printing, since clucontrol object is not serializable
        self.__sanitizedPayload["CluControl"] =  self.__cluctrl
        _taskHandlerInstance = getInfraPatchingTaskHandlerInstance(self.__sanitizedPayload)
        _rc  = _taskHandlerInstance.mExecuteTask()
        return _rc

    def mUpdateRequestData(self, _requestObj, aData = None, aOptions = None, aStatusObj=None, aDetailsErr=None):
        _target_version = ''
        _op_style = ''
        _operation = ''
        _launchnodes = ''
        _reqobj = _requestObj
        _response = {}
        _data = {}
        _node_list = []

        if aOptions:
            _inputPayload = aOptions
            if 'TargetVersion' in _inputPayload:
                _target_version = _inputPayload['TargetVersion']
            if 'OperationStyle' in _inputPayload:
                _op_style = _inputPayload['OperationStyle']
            if 'Operation' in _inputPayload:
                _operation = _inputPayload['Operation']


        if aData is None:
            _data = {}
            _data["service"] = "ExadataPatch"
        else:
            _data = aData

        if aStatusObj:
            _data["status"] = aStatusObj[0]
            _data["status_message"] = aStatusObj[1]

        if aDetailsErr is not None:
            _data["status_message"] = aDetailsErr

        _data["TargetVersion"] = _target_version
        _data["OperationStyle"] = _op_style
        _data["Operation"] = _operation
        _data["service"] = "ExadataPatch"
        if _reqobj:
            _master_uuid=_reqobj.mGetUUID()
            if _master_uuid:
                _data["master_request_uuid"] =_master_uuid

        _response["output"] = _data

        if _reqobj is not None:
            _db = ebGetDefaultDB()
            _reqobj.mSetData(json.dumps(_response, sort_keys=True))
            _db.mUpdateRequest(_reqobj)
        elif aOptions and aOptions.jsonmode:
            (json.dumps(_response, indent=4, sort_keys=True))

    def mGetLatestPatchVersion(self):
        """
        Get the latest patch version by looking at the file system.
        """

        _valid_versions_fs = []
        _latest_ver_from_fs = None

        # instantiate the class oracle version
        _verobj = OracleVersion()

        # List the available patches from the file system PatchPayloads
        # -------------------------------------------------------------
        if os.path.isdir(self.PATCH_PAYLOADS_DIRECTORY) is True:
            _ldir = os.listdir(self.PATCH_PAYLOADS_DIRECTORY)
            # Go through the file system to get the latest patch version
            for _entry in _ldir:
                _patch_dir_path = ''
                _patch_dir_path = self.PATCH_PAYLOADS_DIRECTORY + _entry
                # validate the patch version is dir or not
                if os.path.isdir(_patch_dir_path) is True:
                    # Expect version in form a.b.c.d.e.f[.g] where f is 6 digits
                    # and g is an optional. Example: 12.2.1.1.1.170620,
                    # 18.1.4.0.0.180125.3, 18.1.10.0.0.181031.1.
                    _re_out = re.match('^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\.[0-9]{6,6}(|\.[0-9]+)$', _entry)
                    if _re_out:
                        _valid_versions_fs.append(_entry)
                    else:
                        self.mPatchLogWarn("Invalid version found in file system: %s " % _entry)

            self.mPatchLogInfo("Following versions are found in file system:")
            for _ver in _valid_versions_fs:
                self.mPatchLogInfo("%s" % _ver)

        # get the latest/highest version from file system
        _latest_ver_from_fs = _verobj.mGetHighestVer(_valid_versions_fs)
        self.mPatchLogInfo("Latest version from file system: %s" % _latest_ver_from_fs)
        return _latest_ver_from_fs

    def mParseLatestVersion(self, aPatchFile, aVersion, aOperation, aTargetType=None, aIsExasplice=False):
        """
        This function replaces the 'LATEST' with actual latest
        value in patch path and also construct correct path for the
        patching file.
        Returns a tuple containing three values: the first indicate the error code, the second is the patch file name,
        and the third is the error suggestion message for error scenarios
        """
        _invalid_json_sug_msg = "Failed to validate the input configuration file."
        _msg = ""
        _dom0YumRepo = False
        _DBPatchFileDir = False
        _domuYumRepo = False
        _cellPatchFileDir = False
        _switchPatchFileDir = False
        if aPatchFile.find(KEY_NAME_Dom0_YumRepository) > -1:
            _dom0YumRepo = True

        if aPatchFile.find(KEY_NAME_DBPatchFile) > -1:
            _DBPatchFileDir = True

        # No bundle comparison or validation required in
        # case of oneoff, oneoffv2 patching.
        if aOperation in [ TASK_ONEOFF, TASK_ONEOFFV2 ]:
            self.mPatchLogInfo(f"Patch file version validations are skipped during oneoff and oneoffv2 operations.")
            return PATCH_SUCCESS_EXIT_CODE, aPatchFile, _msg

        # Skip path validation for DOM0 exasplice with LATEST - handlers will resolve it later
        if (aVersion and aVersion.upper() == 'LATEST' and
            aTargetType and aTargetType.lower() == PATCH_DOM0 and
            aIsExasplice):
            self.mPatchLogInfo("Skipping path validation for DOM0 exasplice LATEST - will be resolved by handlers")
            return PATCH_SUCCESS_EXIT_CODE, aPatchFile, _msg

        # If directory path is not having 'LATEST' string and it's not exacc, then
        # no job here; simply return (aPatchFile) as it is.
        if not _DBPatchFileDir and ((not aPatchFile or aPatchFile.find('LATEST') == -1) and self.OCIEXACC != 'True'):
            self.mPatchLogInfo("mParseLatestVersion: PatchFile = '%s' " % aPatchFile)
            return PATCH_SUCCESS_EXIT_CODE, aPatchFile, _msg

        if not aVersion:
            self.mPatchLogError("Invalid input version: %s " % aVersion)
            return INCORRECT_INPUT_JSON, "", _invalid_json_sug_msg

        aPatchFile = aPatchFile.replace('LATEST', aVersion)
        if self.OCIEXACC == "True":
            aPatchFile = os.path.join(self.PATCH_PAYLOADS_DIRECTORY, aVersion, \
                    aPatchFile.rstrip('/').split('/')[-1])

        # If PatchPayloads/DBPatchFile/ is found then use dbserver.patch.zip from PatchPayloads/DBPatchFile/
        # otherwise use from PatchPayloads/version/DBPatchFile/
        if _DBPatchFileDir:
            if self.OCIEXACC == "True":
                aPatchFile = os.path.join(aPatchFile, "dbserver.patch.zip")
            if os.path.exists(aPatchFile):
                _version_common_directory = os.path.join((Path(os.path.dirname(aPatchFile))).parent.parent, "DBPatchFile/dbserver.patch.zip")
                if _version_common_directory and os.path.exists(_version_common_directory) is True:
                    self.mPatchLogInfo(f"Checking for the latest dbserver.patch.zip between {str(_version_common_directory)} and {str(aPatchFile)}")
                    aPatchFile = self.mCompareDbserverPatchFiles(aPatchFile, _version_common_directory)
            self.mPatchLogInfo("dbserver.patch.zip from %s is used for patching" % aPatchFile)
            aPatchFile = os.path.dirname(aPatchFile)


        if os.path.isdir(aPatchFile) is True:
            aPatchFile = os.path.abspath(aPatchFile)
            _listfile = os.listdir(aPatchFile)

            # Sample Path for dom0YumRepo for 19.3.6 version
            # ol7 is for KVM
            # aPatchFile =
            # exacloud/PatchPayloads/19.3.6.0.0.200317/Dom0YumRepository/exadata_ol7_19.3.6.0.0.200317_Linux-x86-64.zip,
            # exacloud/PatchPayloads/19.3.6.0.0.200317/Dom0YumRepository/exadata_ovs_19.3.6.0.0.200317_Linux-x86-64.zip
            # if there are multiple files are PatchPayloads/19.3.5.0.0.200228/Dom0YumRepository/
            _dom0files = []
            if _dom0YumRepo is True and len(_listfile) > 1:
                for f in (_listfile):
                    _dom0files.append(os.path.join(aPatchFile, f))
                aPatchFile = ','.join(_dom0files)
                self.mPatchLogInfo("Dom0Repository file for LATEST Version is %s " % aPatchFile)
            elif _domuYumRepo is True:
                files = glob.glob(os.path.join(aPatchFile, f'exadata_*_{aVersion}_Linux-x86-64.zip'))
                if files:
                    aPatchFile = files[0]
                    if not os.path.exists(aPatchFile):
                        _msg = f"Patch file not found: {aPatchFile}"
                        self.mPatchLogError(_msg)
                        return MISSING_PATCH_FILES, "", _msg
                else:
                    _msg = f"No matching file found in {aPatchFile} for version {aVersion}"
                    self.mPatchLogError(_msg)
                    return MISSING_PATCH_FILES, "", _msg
            elif _cellPatchFileDir is True:
                aPatchFile = os.path.join(aPatchFile, aVersion + ".patch.zip")
            elif _switchPatchFileDir is True:
                aPatchFile = os.path.join(aPatchFile, aVersion + ".switch.patch.zip")
            elif _DBPatchFileDir is True:
                aPatchFile = os.path.join(aPatchFile, "dbserver.patch.zip")
            # if there is a single file under PatchPayloads/19.3.5.0.0.200228/<any directory> , proceed as before
            elif len(_listfile) == 1:
                aPatchFile = os.path.join(aPatchFile, _listfile[0])
            else:
                _msg = "Patch file is not found in %s " % aPatchFile
                self.mPatchLogError(_msg)
                return MISSING_PATCH_FILES, "", _msg
        else:
            _msg= "Patch directory path does not exist: %s " % aPatchFile
            self.mPatchLogError(_msg)
            return MISSING_PATCH_DIRECTORY, "", _msg
        return PATCH_SUCCESS_EXIT_CODE, aPatchFile, _msg

    # end of method mParseLatestVersion()

    def mValidateandSanitizePayload(self, aOptions):
        """
        Validates and Sanitizes the payload by removing params and xml_oeda attribute
        """
        _invalid_json_sug_msg = "Failed to validate the input configuration file."
        # Valid target types
        _valid_plugin_types = ['domu', 'dom0', 'dom0domu', 'dom0+dom0domu', 'dom0domu+dom0']

        _jconf = aOptions.jsonconf
        _patch_file_cells = None
        _patch_files_dom0s_or_domus = None
        _patch_file_cells = None

        _target_type = None
        if _jconf and 'Params' in _jconf.keys():
            # Iterate on each entry in Params
            for _entry in _jconf['Params']:
                _operation = ''
                _payload = ''
                _style = ''
                _backupmode = ''
                _enableplugins = ''
                _plugintypes = ''
                _fedramp = ''
                _patch_retry_flag = ''
                _patch_master_request_id = ''
                _isMVM = ''
                _shared_env = ''
                _storageType = ''
                _additionaloption = {}
                _version = ''
                _target = []
                _download_files = []
                _computeNodeList = {}
                _storageNodeList = {}
                _dom0domuDetails = {}
                _eluTargetVersionToNodeMappings = {}
                _computeNodeListByAlias = {}
                _idemPotencyData = {}
                _infra_patch_plugin_metadata = {}
                _oneoff_script_alias = ''
                _isADBS = ''

                # Get patch operation
                if 'Operation' not in _entry:
                    self.mPatchLogError("'Operation' not provided in json entry")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg
                elif _entry['Operation'].lower() not in [TASK_BACKUP_IMAGE,
                                                         TASK_PREREQ_CHECK,
                                                         TASK_PATCH,
                                                         TASK_ROLLBACK_PREREQ_CHECK,
                                                         TASK_ROLLBACK,
                                                         TASK_POSTCHECK,
                                                         TASK_ONEOFF,
                                                         TASK_ONEOFFV2
                                                         ]:
                    self.mPatchLogError("Invalid 'Operation' value(%s) in json entry." % _entry['Operation'])
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg
                else:
                    _operation = _entry['Operation']

                # Get payload type. Default: release
                if 'PayloadType' in _entry and _entry['PayloadType'].lower() in [PAYLOAD_RELEASE, \
                                                                                 PAYLOAD_NON_RELEASE]:
                    _payload = _entry['PayloadType']
                else:
                    self.mPatchLogError("PayloadType not defined in json entry.")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                # Get operation style. Default: rolling
                if 'OperationStyle' in _entry and _entry['OperationStyle'].lower() in [
                    OP_STYLE_ROLLING,
                    OP_STYLE_AUTO,
                    OP_STYLE_NON_ROLLING]:
                    _style = _entry['OperationStyle']
                else:
                    self.mPatchLogError("OperationStyle not provided in json entry.")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                # Get backup mode. Default: no
                if 'BackupMode' in _entry and _entry['BackupMode'].lower() in ['', OP_BACKUPMODE_NO,
                                                                               OP_BACKUPMODE_YES]:
                    _backupmode = _entry['BackupMode']
                else:
                    self.mPatchLogError("BackupMode either not provided or invalid entry in json entry.")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                # Get additional options if any
                if 'AdditionalOptions' in _entry:
                    _additionaloption = _entry['AdditionalOptions']

                # Get StorageNodeList options if any
                if 'StorageNodeList' in _entry:
                    _storageNodeList = _entry['StorageNodeList']

                # Get Dom0domUDetails options if any
                if 'Dom0domUDetails' in _entry:
                    _dom0domuDetails = _entry['Dom0domUDetails']

                # Get ComputeNodeList options if any
                if 'ComputeNodeList' in _entry:
                    _computeNodeList = _entry['ComputeNodeList']

                # Get ComputeNodeList Sorted by Alias options if any
                if 'ComputeNodeListByAlias' in _entry:
                    _computeNodeListByAlias = _entry['ComputeNodeListByAlias']

                # Get IdemPotencyData in case of a retry
                if 'Idempotency' in _entry:
                    _idemPotencyData = _entry['Idempotency']

                # Get InfraPatchPluginMetaData in case of a oneoffv2 patch operation
                if 'InfraPatchPluginMetaData' in _entry:
                    _infra_patch_plugin_metadata = _entry['InfraPatchPluginMetaData']

                # Get OneoffScriptAlias in case of a oneoffv2 patch operation
                if 'OneoffScriptAlias' in _entry:
                    _oneoff_script_alias = _entry['OneoffScriptAlias']

                # Get MultiVM enables or not for EXACS
                if 'isMVM' in _entry:
                    _isMVM = _entry['isMVM']
                    # check for shared env
                    if _isMVM.upper() == 'YES':
                        _shared_env = 'True'

                # Indicator of exascale env
                if 'storageType' in _entry:
                    _storageType = _entry['storageType']

                # If it is ADBS
                if 'adb_s' in _entry:
                    _isADBS = _entry['adb_s']

                _is_exasplice = False
                if _additionaloption and 'exasplice' in _additionaloption[0] \
                    and _additionaloption[0]['exasplice']:
                    if _additionaloption[0]['exasplice'].lower() == 'yes':
                        _is_exasplice = True

                # Get FedrampEnabled value
                if 'FedrampEnabled' in _entry:
                    _fedramp = _entry['FedrampEnabled']
                    self.mPatchLogInfo("Current FedrampEnabled value in EcsProperty Table : %s" % _fedramp)
                else:
                    self.mPatchLogInfo("FedrampEnabled value is not configured or used in EcsProperty Table")

                # Get target version
                if 'TargetVersion' in _entry:
                    # Bug-26830429 - Evaluate the available latest version
                    if _entry['TargetVersion'].upper() == 'LATEST':
                        # Check if LATEST is allowed as literal for dom0 + exasplice=yes
                        _target_types = _entry.get('TargetType', [])
                        _target_type = _target_types[0] if len(_target_types) == 1 else None
                        _exasplice_value = 'yes' if _is_exasplice else 'no'

                        if mIsLatestTargetVersionAllowed(_entry['TargetVersion'], _target_type, _exasplice_value):
                            # Allow LATEST as literal string for dom0 exasplice patching
                            self.mPatchLogInfo(f"Allowing LATEST as literal targetVersion for DOM0 exasplice patching")
                            _version = _entry['TargetVersion']
                        else:
                            self.mPatchLogInfo("Finding the LATEST target version.")
                            _version = self.mGetLatestPatchVersion()
                    else:
                        _version = _entry['TargetVersion']
                        self.mPatchLogInfo("The TargetVersion selected: %s " % _version)

                    if _version not in self.__object_store:
                        self.__object_store[_version] = {'files': _download_files,
                                                         'dir': None}
                else:
                    self.mPatchLogError("TargetVersion not defined in json entry.")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                # Get target type: dom0, domu, cell, ibswitch
                if 'TargetType' in _entry:
                    for _ttype in _entry['TargetType']:
                        if _ttype.lower() in [PATCH_DOM0, PATCH_CELL, PATCH_SWITCH,
                                              PATCH_IBSWITCH, PATCH_DOMU]:
                            _target.append(_ttype.lower())
                        else:
                            self.mPatchLogWarn("TargetType '%s' not valid. Input will be ignored" % _ttype)
                else:
                    self.mPatchLogError("'TargetType' not provided in json entry")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                # Get Run Plugin value. Default: no
                if 'EnablePlugins' in _entry:
                    if _entry['EnablePlugins'].lower() in ['yes', 'no']:
                        _enableplugins = _entry['EnablePlugins'].lower()
                    else:
                        self.mPatchLogError("Invalid plugins option is specified: '%s'" % _entry['EnablePlugins'])
                        return INCORRECT_INPUT_JSON, _invalid_json_sug_msg
                else:
                    self.mPatchLogError("EnablePlugins param either not provided or invalid entry in json entry.")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                # Get the param value which indicate whether we need to run
                # plugins on dom0/domu/dom0's domu. Default: none
                if 'PluginTypes' in _entry:
                    if _entry['PluginTypes']:
                        _tmp_plugin_types = _entry['PluginTypes'].strip()
                        _tmp_plugin_types = _tmp_plugin_types.replace(" ", "")
                        _tmp_plugin_types = _entry['PluginTypes'].lower()

                        # Validate plugins types
                        if _enableplugins == 'yes' and _tmp_plugin_types in ["", " ", "none"]:
                            self.mPatchLogError("Invalid plugin types specified: '%s'." % _tmp_plugin_types)
                            return INCORRECT_INPUT_JSON, _invalid_json_sug_msg
                        elif _enableplugins == 'yes' and PATCH_DOM0 in _target:
                            if not _tmp_plugin_types in ['dom0', 'dom0domu', 'dom0+dom0domu', 'dom0domu+dom0']:
                                self.mPatchLogError("Invalid plugin types specified for dom0: '%s'." % _tmp_plugin_types)
                                return INCORRECT_INPUT_JSON, _invalid_json_sug_msg
                        elif _enableplugins == 'yes' and PATCH_DOMU in _target:
                            if not _tmp_plugin_types in ['domu']:
                                self.mPatchLogError("Invalid plugin types specified for domU: '%s'." % _tmp_plugin_types)
                                return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                        # Just copy as it's if no plugin enable specified.
                        _plugintypes = _tmp_plugin_types
                else:
                    self.mPatchLogError("PluginTypes param either not provided or invalid entry in json entry.")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                # Get patching request retry flag. Default: no
                if 'Retry' in _entry:
                    if _entry['Retry'].lower() in ['yes', 'no']:
                        _patch_retry_flag = _entry['Retry'].lower()
                    else:
                        self.mPatchLogError("Invalid Retry option is specified: '%s'" % _entry['Retry'])
                        return INCORRECT_INPUT_JSON, _invalid_json_sug_msg
                else:
                    self.mPatchLogError("Retry param either not provided or invalid entry in json entry.")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                # Get patching master request id. Default: none
                if 'RequestId' in _entry:
                    _patch_master_request_id = _entry['RequestId'].lower()
                else:
                    self.mPatchLogError("RequestId param either not provided or invalid entry in json entry.")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                # If not clusters specified for this entry, then ignore
                if 'Clusters' not in _entry:
                    self.mPatchLogWarn("'Clusters' not provided in json entry. This entry will be ignored")
                    continue

                # Get ELU to Node Mappings
                if _is_exasplice and (PATCH_DOM0 in _target or PATCH_DOMU in _target) and 'ELUTargetVersiontoNodeMappings' in _entry:
                    _eluTargetVersionToNodeMappings = _entry['ELUTargetVersiontoNodeMappings']

                # Get patch files
                if _payload == PAYLOAD_RELEASE:
                    if PATCH_CELL in _target:
                        _download_files.append('CellPatchFile')

                    if _target in [ PATCH_IBSWITCH, PATCH_SWITCH ]:
                        if 'CellPatchFile' in _entry:
                            self.mPatchLogWarn("'SwitchPatchFile' not specified in json. 'CellPatchfile' will be used instead.")
                            _entry['SwitchPatchFile'] = _entry['CellPatchFile']
                        else:
                            ### ATENTION: CellPatchFile is added here because it is the same for cells and ibswitches
                            _download_files.append('SwitchPatchFile')

                    # Refer Exasplice repository in case of exasplice patching on dom0.
                    if PATCH_DOM0 in _target and _is_exasplice:
                        _download_files.append('DBPatchFile')
                        if not mQuarterlyVersionPatternMatch(_version):
                            _download_files.append('ExaspliceRepository')
                    elif PATCH_DOM0 in _target:
                        for _input in ['DBPatchFile', 'Dom0YumRepository']:
                            _download_files.append(_input)

                    if PATCH_DOMU in _target:
                        for _input in ['DBPatchFile', 'DomuYumRepository']:
                            _download_files.append(_input)
                else:
                    if 'PatchFile' not in _entry:
                        self.mPatchLogWarn("'PatchFile' not provided in json entry.")
                        _download_files.append('PatchFile')
                        _entry['PatchFile'] = None

                # Create the sanitized Payload for Exacloud with the common attributes
                # CellIBSwitchesPatchZipFile and Dom0DomuPatchZipFile will be added later
                self.__sanitizedPayload = {
                    "LocalLogFile": self.__oeda_patch_mgr_log_dir ,
                    'Operation': _operation,
                    'PayloadType': _payload,
                    'OperationStyle': _style,
                    'TargetType': _target,
                    'TargetVersion': _version,
                    'BackupMode': _backupmode,
                    'EnablePlugins': _enableplugins,
                    'PluginTypes': _plugintypes,
                    'Fedramp': _fedramp,
                    'Retry': _patch_retry_flag,
                    'RequestId': _patch_master_request_id,
                    'AdditionalOptions': _additionaloption,
                    "ComputeNodeList": _computeNodeList,
                    "ComputeNodeListByAlias": _computeNodeListByAlias,
                    "isMVM":_isMVM,
                    "shared_env":_shared_env,
                    "storageType":_storageType,
                    "StorageNodeList": _storageNodeList,
                    "Dom0domUDetails": _dom0domuDetails,
                    "ELUTargetVersiontoNodeMappings": _eluTargetVersionToNodeMappings,
                    "Idempotency": _idemPotencyData,
                    "InfraPatchPluginMetaData": _infra_patch_plugin_metadata,
                    "OneoffScriptAlias": _oneoff_script_alias,
                    "adb_s": _isADBS,
                    "ExacloudChildReqUUID": self.__cluctrl.mGetRequestObj().mGetUUID(),
                    "ExacloudMasterReqUUID": self.__cluctrl.mGetRequestObj().mGetUUID(),
                    "isSingleWorkerRequest" : "yes"
                }

                # Save patch file or files necessary to run the patch.
                if _payload == PAYLOAD_RELEASE:

                    # Bug-26830429 - Construct the actual path for the target
                    # patch file if dir path has the 'LATEST' value.
                    for _ttype in _target:
                        if _ttype == PATCH_CELL:
                            self.__sanitizedPayload['CellPatchFile'] = _entry['CellPatchFile']
                            # Construct path with latest version for patch file
                            _ret, _patch_file, _msg = self.mParseLatestVersion(self.__sanitizedPayload['CellPatchFile'], _version, self.__sanitizedPayload['Operation'])
                            if _ret == PATCH_SUCCESS_EXIT_CODE:
                                self.__sanitizedPayload['CellPatchFile'] = _patch_file
                            if _ret != PATCH_SUCCESS_EXIT_CODE:
                                return _ret, _msg

                        elif _ttype in [ PATCH_IBSWITCH, PATCH_SWITCH ]:
                            self.__sanitizedPayload['SwitchPatchFile'] = _entry['SwitchPatchFile']
                            # Construct path with latest version for patch file
                            _ret, _patch_file, _msg  = self.mParseLatestVersion(self.__sanitizedPayload['SwitchPatchFile'], _version, self.__sanitizedPayload['Operation'])
                            if _ret == PATCH_SUCCESS_EXIT_CODE:
                                self.__sanitizedPayload['SwitchPatchFile'] = _patch_file
                            if _ret != PATCH_SUCCESS_EXIT_CODE:
                                return _ret, _msg


                        elif _ttype == PATCH_DOM0:
                            self.__sanitizedPayload['DBPatchFile'] = _entry['DBPatchFile']
                            # Construct path with latest version for patch file
                            _ret, _patch_file, _msg  = self.mParseLatestVersion(self.__sanitizedPayload['DBPatchFile'], _version, self.__sanitizedPayload['Operation'], _ttype, _is_exasplice)
                            if _ret == PATCH_SUCCESS_EXIT_CODE:
                                self.__sanitizedPayload['DBPatchFile'] = _patch_file
                            if _ret != PATCH_SUCCESS_EXIT_CODE:
                                return _ret, _msg

                            self.__sanitizedPayload['Dom0YumRepository'] = _entry['Dom0YumRepository']
                            # Construct path with latest version for patch file
                            _ret, _patch_file, _msg  = self.mParseLatestVersion(self.__sanitizedPayload['Dom0YumRepository'], _version, self.__sanitizedPayload['Operation'], _ttype, _is_exasplice)
                            if _ret == PATCH_SUCCESS_EXIT_CODE:
                                self.__sanitizedPayload['Dom0YumRepository'] = _patch_file
                            if _ret != PATCH_SUCCESS_EXIT_CODE:
                                return _ret, _msg

                        elif _ttype == PATCH_DOMU:
                            self.__sanitizedPayload['DBPatchFile'] = _entry['DBPatchFile']
                            # Construct path with latest version for patch file
                            _ret, _patch_file, _msg  = self.mParseLatestVersion(self.__sanitizedPayload['DBPatchFile'], _version, self.__sanitizedPayload['Operation'])
                            if _ret == PATCH_SUCCESS_EXIT_CODE:
                                self.__sanitizedPayload['DBPatchFile'] = _patch_file
                            if _ret != PATCH_SUCCESS_EXIT_CODE:
                                return _ret, _msg

                            self.__sanitizedPayload['DomuYumRepository'] = _entry['DomuYumRepository']
                            _ret, _patch_file, _msg  = self.mParseLatestVersion(self.__sanitizedPayload['DomuYumRepository'], _version, self.__sanitizedPayload['Operation'])
                            if _ret == PATCH_SUCCESS_EXIT_CODE:
                                self.__sanitizedPayload['DomuYumRepository'] = _patch_file
                            if _ret != PATCH_SUCCESS_EXIT_CODE:
                                return _ret, _msg
                else:
                    self.__sanitizedPayload['PatchFile'] = _entry['PatchFile']
                    for _ttype in _target:
                        if _ttype == PATCH_DOM0:
                            if 'Dom0YumRepository' in _entry:
                                self.__sanitizedPayload['Dom0YumRepository'] = \
                                    _entry['Dom0YumRepository']
                            break
                        if _ttype == PATCH_DOMU:
                            if 'DomuYumRepository' in _entry:
                                self.__sanitizedPayload['DomuYumRepository'] = \
                                    _entry['DomuYumRepository']
                            break

                # Iterate on each cluster specified in this entry
                for _cluster in _entry['Clusters']:
                    if 'target_env' in _cluster and _cluster['target_env'] in [ENV_PRODUCTION, \
                                                                               ENV_PREPRODUCTION,
                                                                               ENV_DEVELOPMENT, \
                                                                               ENV_TEST]:
                        self.__sanitizedPayload['TargetEnv'] = _cluster['target_env']
                        self.__sanitizedPayload['RackName'] = _cluster['rack_name']
                        # Add to object store only if necessary
                        if _download_files:
                            for _f in _download_files:
                                if _f not in self.__object_store[_version]['files']:
                                    self.__object_store[_version]['files'].append(_f)

            #return PATCH_SUCCESS_EXIT_CODE, ""

        #Validations other than payload parameters
        # Space usage check on exacloud mount point to ensure thread and
        # request logs are stored and patching completes without any issues.
        if not self.mCheckExacloudMnt():
            self.mPatchLogError("Insufficient disk space to store exacloud requests and thread logs.")
            _suggestion_msg = "Insufficient disk space to store exacloud requests and thread logs."
            _rc = INSUFFICIENT_SPACE_AT_EXACLOUD_THREAD_LOCATION
            return _rc, _suggestion_msg

        # Check if we should skip filesystem validation for DOM0 exasplice LATEST
        _skip_filesystem_validation = False
        if self.__sanitizedPayload:
            _target_version = self.__sanitizedPayload.get('TargetVersion', '')
            _target_types = self.__sanitizedPayload.get('TargetType', [])
            _additional_options = self.__sanitizedPayload.get('AdditionalOptions', [])

            _is_exasplice = False
            if _additional_options and len(_additional_options) > 0:
                _is_exasplice = _additional_options[0].get('exasplice', '').lower() == 'yes'

            # Skip validation if: LATEST + single dom0 target + exasplice=yes
            if (_target_version and _target_version.upper() == 'LATEST' and
                len(_target_types) == 1 and _target_types[0].lower() == PATCH_DOM0 and
                _is_exasplice):
                _skip_filesystem_validation = True
                self.mPatchLogInfo("Skipping filesystem validation for DOM0 exasplice LATEST - will be resolved by handlers")

        if not _skip_filesystem_validation and self.__latest_verion_source_loc == self.LATEST_VER_FROM_FILESYSTEM:
            self.mPatchLogInfo("Using file system to read patch files.")
            _rc, _suggestion_msg = self.mCheckPatchFileExistInFileSystem()
            if _rc != PATCH_SUCCESS_EXIT_CODE:
                return _rc, _suggestion_msg

        return PATCH_SUCCESS_EXIT_CODE, ""

        #return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

    def mCheckExacloudMnt(self):
        """
        Validates the disk space usage of thread and requests log location to
        accomdate newer logs once patching is complete. In the current case, if
        there is no space available on the logs location. Patching task would
        fail in the end due to unable to copy the logs from the patched nodes
        although upgrade was successful.
        """
        # Read exacloud patch working space size
        _rc = True
        self.EXACLOUD_PATCH_WORKING_SPACE_MB = self.__cluctrl.mCheckConfigOption('exacloud_patch_working_space_mb').strip()
        if (not self.EXACLOUD_PATCH_WORKING_SPACE_MB) or self.EXACLOUD_PATCH_WORKING_SPACE_MB == '' or (
                int(self.EXACLOUD_PATCH_WORKING_SPACE_MB) == 0):
            self.mPatchLogError(
                "Invalid exacloud disk space configured to store exacloud thread and request logs : %s , please validate the parameter 'exacloud_patch_working_space_mb' in exabox.conf and re-run patching." % self.EXACLOUD_PATCH_WORKING_SPACE_MB)
            _rc = False
        else:
            _df_cmd = "/bin/df -mP ."
            _in, _out, _err = self.__cluctrl.mExecuteCmd(_df_cmd)

            _df_cmd = "/bin/awk '{print $4}'"
            _in, _out, _err = self.__cluctrl.mExecuteCmd(_df_cmd, aStdIn=_out)

            _df_cmd = "/bin/grep -vi Avail"
            _in, _out, _err = self.__cluctrl.mExecuteCmd(_df_cmd, aStdIn=_out)
            #_cluTotal = int(self.EXACLOUD_PATCH_WORKING_SPACE_MB) * int(self.ClusterCount)
            _cluTotal = int(self.EXACLOUD_PATCH_WORKING_SPACE_MB)
            _output = _out.readlines()
            _out = _output[0].strip()
            if int(_out) < int(_cluTotal):
                self.mPatchLogInfo("\nDisk statistics on exacloud area before patch operation: ")
                self.mPatchLogInfo("   - Free disk space on exacloud area : %s MB" % _out)
                self.mPatchLogInfo("   - Disk space expected on exacloud area for thread and request logs: %sGB(Disk space required to store logs per cluster)  \n" % ((int(self.EXACLOUD_PATCH_WORKING_SPACE_MB)/1024)))
                _rc = False
        return _rc

    def mGetDbserverPatchVersionDetails(self, aDbPatchFileDir):
        """
         This method returns the db patch file along with version based
         on the input DB patch file path provided.

         -bash-4.4$ /bin/unzip -l /scratch/araghave/ecra_installs/abhi/mw_home/user_projects/
         domains/exacloud/PatchPayloads/DBPatchFile/dbserver.patch.zip | /bin/grep dbserver_ |
         /bin/head -1 | /bin/awk '{print $4}' | /bin/tr -d "/"
         dbserver_patch_250119
         -bash-4.4$

         -bash-4.2$ unzip -l PatchPayloads/DBPatchFile/dbserver.patch.zip | head -4
         Archive:  PatchPayloads/DBPatchFile/dbserver.patch.zip
          Length      Date    Time    Name
         ---------  ---------- -----   ----
               0  09-18-2024 23:46   dbserver_patch_240915.1/
         -bash-4.2$

        """
        _version = None
        _db_patch_file = None
        try:
            _cmd_list = []
            _out = []
            # Get Dbserver patch version details.
            _db_patch_file = os.path.join(aDbPatchFileDir)
            _cmd_list.append(["/bin/unzip", "-l", _db_patch_file])
            _cmd_list.append(["/bin/grep", "dbserver_"])
            _cmd_list.append(["/bin/head", "-1"])
            _cmd_list.append(["/bin/awk", '{print $4}'])
            _cmd_list.append(["/bin/tr", "-d", '/'])
            _cmd_list.append(["/bin/cut", "-d.", "-f1"])
            _rc, _o = runInfraPatchCommandsLocally(_cmd_list)
            if _o:
                _version = ((_o.split("\n"))[0]).split("_")[2]
        except Exception as e:
            self.mPatchLogWarn("Error in generating dbserver patch version. Error: %s" % str(e))
            self.mPatchLogTrace(traceback.format_exc())
        return _version

    def mCompareDbserverPatchFiles(self, aOldDbPatchFile, aNewDbPatchFile):
        """
         This method checks for the dbserver patch files staged at common
         and the exadata version stage locations and return the LATEST
         based on the date format details in the file naming convention.

         In the below example, 2 dbserver patch zip locations are provided
         as input for comparison to return the LATEST patch.

          [ araghave_dbserver ] bash-4.2$  unzip -l
          PatchPayloads/DBPatchFile/dbserver.patch.zip | grep 'dbserver_patch_' | head -1
            0  10-18-2023 00:09   dbserver_patch_231017/
          [ araghave_dbserver ] bash-4.2$

          [ araghave_dbserver ] bash-4.2$ unzip -l
          PatchPayloads/23.1.24.0.0.250306.1/DBPatchFile/dbserver.patch.zip | grep
          'dbserver_patch_' | head -1
            0  03-14-2025 00:00   dbserver_patch_250313/
          [ araghave_dbserver ] bash-4.2$

          Here dbserver_patch_250313 is LATEST compared to dbserver_patch_231017 and
          will be consumed for patching.
        """
        _old_db_patch_file_date_format = None
        _new_db_patch_file_date_format = None
        try:
            _old_db_patch_file_date_format = self.mGetDbserverPatchVersionDetails(aOldDbPatchFile)
            _new_db_patch_file_date_format = self.mGetDbserverPatchVersionDetails(aNewDbPatchFile)

            if _old_db_patch_file_date_format and _new_db_patch_file_date_format:
                if int(_old_db_patch_file_date_format) > int(_new_db_patch_file_date_format):
                    self.mPatchLogInfo(f"{aOldDbPatchFile} is the LATEST dbserver patch file available based on the date.")
                    return aOldDbPatchFile
                elif int(_old_db_patch_file_date_format) < int(_new_db_patch_file_date_format):
                    self.mPatchLogInfo(f"{aNewDbPatchFile} is the LATEST dbserver patch file available based on the date.")
                    return aNewDbPatchFile
                else:
                    self.mPatchLogInfo(f"Both the dbserver patch files have the same date: {_new_db_patch_file_date_format} and either of them can be used for patching.")
                    return aNewDbPatchFile
            else:
                self.mPatchLogInfo("DBPatch file not found in either of the Patch Stage locations.")
                return None
        except Exception as e:
            self.mPatchLogWarn("Error in generating dbserver patch version file for patching. Error: %s" % str(e))
            self.mPatchLogTrace(traceback.format_exc())
            return None

    def mCheckPatchFileExistInFileSystem(self):
        """
        Check the existance of required exadata patch files in local file system.
        """
        _rc = PATCH_SUCCESS_EXIT_CODE
        _version_common_directory = None
        for _version in self.__object_store.keys():
            # Skip validation for LATEST - it's for DOM0 exasplice and will be resolved by handlers
            if _version and _version.upper() == 'LATEST':
                self.mPatchLogInfo(f"Skipping filesystem validation for version '{_version}' - will be resolved by handlers")
                continue

            for _file in set(self.__object_store[_version]['files']):
                _version_directory = os.path.join(self.PATCH_PAYLOADS_DIRECTORY, _version, _file)

                """
                If dbserver.patch.zip from PatchPayloads/DBPatchFile exists, use this for patching 
                otherwise check for dbserver.patch.zip from PatchPayloads/version/DBPatchFile directory
                """
                if _file == KEY_NAME_DBPatchFile:
                    _version_directory = os.path.join(_version_directory, "dbserver.patch.zip")
                    if os.path.exists(_version_directory):
                        _version_common_directory = os.path.join(self.PATCH_PAYLOADS_DIRECTORY, _file, "dbserver.patch.zip")
                        if _version_common_directory and os.path.exists(_version_common_directory) is True:
                            self.mPatchLogInfo(f"Checking for the latest dbserver.patch.zip between {str(_version_common_directory)} and {str(_version_directory)}")
                            _version_directory = self.mCompareDbserverPatchFiles(_version_directory, _version_common_directory)
                    self.mPatchLogInfo("dbserver.patch.zip from %s is used for patching" % _version_directory)
                    _version_directory = os.path.dirname(_version_directory)

                if _version_directory and os.path.isdir(_version_directory) is True:
                    _version_directory = os.path.abspath(_version_directory)
                    _listfile = os.listdir(_version_directory)

                    if len(_listfile) <= 0:
                        self.mPatchLogError("Patch file not found in '%s'" % _version_directory)
                        _suggestion_msg = "Patch file not found in '%s'" % _version_directory
                        _rc = MISSING_PATCH_FILES
                        return _rc, _suggestion_msg
                else:
                    self.mPatchLogError("Patch directory '%s' not found" % _version_directory)
                    _suggestion_msg = "Patch directory '%s' not found" % _version_directory
                    _rc = MISSING_PATCH_DIRECTORY
                    return _rc, _suggestion_msg

        return _rc, ""

    #Error in validation even before patching request starts
    def mAddPrePatchError(self, aError, aSuggestion=None, aComment=None):
        """
        Generate the patch error report.
        """

        self.__json_status = {}
        _suggestion_msg = aSuggestion
        if aSuggestion and len(aSuggestion) > ERROR_MSG_TRUNCATE_LENGTH:
            _suggestion_msg = mTruncateErrorMessageDescription(aSuggestion)

        _code, _msg, _description, _error_action = ebPatchFormatBuildErrorWithErrorAction(aError, _suggestion_msg, aComment)

        self.__json_status["data"] = self.mAddPatchreport()
        self.__json_status["data"]["error_code"] = _code
        self.__json_status["data"]["error_message"] = _msg
        self.__json_status["data"]["error_detail"] = _description
        if _error_action:
            self.__json_status["data"]["error_action"] = _error_action
        else:
            self.mPatchLogInfo("Error action is empty for Error Code %s" % _code)

        #Keep track of the exacloud master uuid as part of ecra status call
        if self.__cluctrl.mGetRequestObj():
            self.__json_status["data"]["master_request_uuid"] = self.__cluctrl.mGetRequestObj().mGetUUID()
        if self.__child_request_uuid:
            self.__json_status["data"]["child_request_uuid"] = self.__child_request_uuid
        #Do not remove . Helpful for debugging purposes
        self.mPatchLogTrace("Dispatcher Error json details are as follows %s :\n" % json.dumps(self.__json_status))

    def mGetPatchJsonStatus(self):
        return self.__json_status

    def mSetPatchJsonStatus(self,aJsonStatus):
        self.__json_status = aJsonStatus

    def mAddPatchreport(self):
        """
        Return patch report with more detail. We try to maintain the same
        format of patching CNS payload so that it can be read uniformly
        in ecra side.
        """

        # fill up the payload json for notificaiton
        _patch_report_json = {}
        _patch_report_json['httpRequestId'] = self.__cluctrl.mGetRequestObj().mGetUUID()

        _patch_report_json['recipients'] = []
        _channel_info = {}
        _channel_info['channelType'] = "topics"
        _patch_report_json['recipients'].append(_channel_info)

        _patch_report_json['notificationType'] = {}
        _patch_report_json['notificationType']['componentId'] = "Patch_Exadata_Infra_SM"
        _patch_report_json['notificationType']['id'] = "Patch_Exadata_Infra_SMnotification_v1"

        _patch_report_json['service'] = "ExadataPatch"
        _patch_report_json['component'] = "Patch Exadata Infrastructure"
        _patch_report_json['subject'] = "Patch Exadata Infrastructure Service Update"
        _patch_report_json['event_post_time'] = datetime.datetime.now().strftime("%Y-%m-%d:%H.%M.%S %Z")

        # Exacloud log thread location
        _patch_report_json['log_dir'] = self.__logDir

        if 'RackName' in self.__sanitizedPayload:
            _rackName = self.__sanitizedPayload['RackName']
            _patch_report_json['cluster_name'] = self.__sanitizedPayload['RackName']
        if 'TargetType' in self.__sanitizedPayload:
            _targetType = self.__sanitizedPayload['TargetType']
            _patch_report_json['target_type'] = self.__sanitizedPayload["TargetType"]
        if 'Operation' in self.__sanitizedPayload:
            _operation = self.__sanitizedPayload['Operation']
            _patch_report_json['operation_type'] = self.__sanitizedPayload['Operation']
        if 'OperationStyle' in self.__sanitizedPayload:
            _operationStyle = self.__sanitizedPayload['OperationStyle']
            _patch_report_json['operation_style'] = self.__sanitizedPayload['OperationStyle']
        if 'TargetVersion' in self.__sanitizedPayload:
            _targetVersion = self.__sanitizedPayload['TargetVersion']
            _patch_report_json['target_version'] = self.__sanitizedPayload['TargetVersion']

        _patch_report_json['topic'] = ''

        return _patch_report_json
