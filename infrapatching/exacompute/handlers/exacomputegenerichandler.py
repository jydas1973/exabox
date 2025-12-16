#!/bin/python
#
# $Header: ecs/exacloud/exabox/infrapatching/exacompute/handlers/exacomputegenerichandler.py /main/27 2025/08/20 05:15:38 apotluri Exp $
#
# exacomputegenerichandler.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      exacomputegenerichandler.py
#
#    DESCRIPTION
#      Base class for Exacompute patching handlers
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    apotluri    08/11/25 - Bug 38096654 - PRECHECK OF SMR FAILED WITH
#                           'DIRECTORY FOR EXADATA_RELEASE HAS MORE THAN ONE
#                           PATCH'
#    araghave    06/04/25 - Enh 37996638 - EXACOMPUTE PATCHING TO PICK LATEST
#                           DBSERVER PATCH BASED ON THE DATE NAMING CONVENTION
#    araghave    05/09/25 - Enh 37917899 - EXACOMPUTE PATCHING CHANGES FOR
#                           EXADATA PATCHMGR ERROR HANDLING
#    araghave    03/17/25 - Enh 37713042 - CONSUME ERROR HANDLING DETAILS FROM
#                           INFRAPATCHERROR.PY DURING EXACOMPUTE PATCHING
#    sdevasek    02/14/25 - ENH 37496197 - INFRAPATCHING TEST AUTOMATION -
#                           REVIEW AND ADD METHODS INTO METHODS_TO_EXCLUDE_
#                           COVERAGE_REPORT
#    araghave    01/27/25 - Enh 37132175 - EXACOMPUTE MUST REUSE INFRA PATCHING
#                           MODULES FOR VALIDATION AND PATCH OPERATIONS
#    diguma      12/06/24 - bug 37365122 - EXACS:24.4.2.1:X11M: ROLLING DOM0
#                           PATCHING FAILS WITH SSH CONNECTIVITY CHECK FAILED
#                           DURING PATCHING EVEN THOUGH EXASSH TO DOMUS WORK
#    araghave    10/08/24 - Enh 36505637 - IMPROVE POLLING MECHANISM IN CASE
#                           OF INFRA PATCHING OPERATIONS
#    araghave    09/02/24 - Enh 36977545 - REMOVE SYSTEM FIRST BOOT IMAGE
#                           SPECIFIC CODE FROM INFRA PATCHING FILES
#    araghave    08/27/24 - Enh 36971710 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE EXACOMPUTE FILES
#    emekala     07/19/24 - ENH 36794217 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE EXACOMPUTE AND DOMU PATCHMGR CMDS
#    antamil     05/20/24 - ENH 36595928 - Node progress status for precheck failed nodes
#    antamil     04/02/24 - ENH 36415878 - Exacompute patching after precheck support
#    sdevasek    10/04/23 - ENH 35853718 - CHECK FOR EXISTING VMS BEFORE
#                           PATCHING NODES FOR EXACOMPUTE
#    antamil     09/29/23 - Bug 35851548 - Append thread Id to dbnodes file name
#                           to be unique
#    vikasras    08/03/23 - Bug 35671592 - AFTER REFRESHING TO THE RECENT LABEL
#                           TEST FILES ARE REPORTING COMPILATION ERROR
#    vikasras    06/27/23 - Bug 35456901 - MOVE RPM LIST TO INFRAPATCHING.CONF
#                           FOR SYSTEM CONSISTIENCY DUPLICATE RPM CHECK
#    araghave    06/23/23 - Enh 35416441 - Support monthly security patching
#                           for exacompute hosts
#    araghave    05/08/23 - Bug 35361713 - REMOVE LOCAL CONTEXT CHANGES IN CASE
#                           OF EXACOMPUTE NODES
#    araghave    01/10/23 - Bug 34998203 - ADD MISSING SETTER TO EXACOMPUTE
#                           HANDLER FILES. 
#    araghave    01/04/23 - Enh 34823378 - EXACLOUD CHANGES TO HANDLE
#                           EXACOMPUTE PRECHECK AND BACKUP OPERATIONS
#    araghave    01/04/23 - Enh 34915866 - ADD SUPPORT FOR ROLLBACK IN
#                           EXACOMPUTE PATCHING
#    diguma      12/01/22 - Enh 34840180 - addition of specific alerts for
#                           ExaCC
#    sdevasek    11/16/22 - ENH 34384801 - CONSOLIDATE NOTIFICATION ACROSS
#                           MULTIPLE PATCHMGR OPERATIONS
#    araghave    08/09/22 - Enh 34350140 - EXACLOUD CHANGES TO HANDLE
#                           EXACOMPUTE PRECHECK AND PATCHING OPERATIONS
#    jyotdas     07/22/22 - ENH 34350151 - Exacompute Infrapatching
#    jyotdas     07/22/22 - Creation
#

import json
import socket
import traceback
from time import sleep
from datetime import datetime
from pathlib import Path

from exabox.infrapatching.exacompute.core.exacomputepatch import ebCluExaComputePatch
from exabox.infrapatching.handlers.loghandler import LogHandler
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.utils.utility import mGetFirstDirInZip, mGetInfraPatchingKnownAlert, mFormatOut, mGetSshTimeout
from exabox.ovm.hypervisorutils import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.ovm.clumisc import OracleVersion
from defusedxml import ElementTree as ET
from exabox.ovm.clumisc import ebCluSshSetup
from exabox.infrapatching.utils.utility import PATCH_BASE
from exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler import InfraPatchManager
from exabox.infrapatching.handlers.generichandler import GenericHandler
from exabox.infrapatching.handlers.targetHandler.targethandler import TargetHandler
from exabox.infrapatching.core.clupatchhealthcheck import ebCluPatchHealthCheck
from exabox.infrapatching.utils.utility import mGetInfraPatchingHandler, mRegisterInfraPatchingHandlers, getTargetHandlerInstance, mIsFSEncryptedList, runInfraPatchCommandsLocally

class ExaGenericHandler(TargetHandler):

    LATEST_VER_FROM_OBJECTSTORE = 'objectStore'

    def __init__(self, *initial_data, **kwargs):
        super(ExaGenericHandler, self).__init__(*initial_data, **kwargs)
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [TASK_PATCH], self)

        self.mPatchLogInfo("ExaGenericHandler")

        for dictionary in initial_data:
            if "CluControl" in dictionary.keys():
                self.__cluctrl = dictionary["CluControl"]
            if "LocalLogFile" in dictionary.keys():
                self.__log_path = dictionary["LocalLogFile"]
            if "Operation" in dictionary.keys():
                self.__task = dictionary["Operation"]
            if "OperationStyle" in dictionary.keys():
                self.__op_style = dictionary["OperationStyle"]
            if "RequestObj" in dictionary.keys():
                self.__requestObj = dictionary["RequestObj"]
            if "TargetVersion" in dictionary.keys():
                self.__target_version = dictionary["TargetVersion"]
            if "NodeList" in dictionary.keys():
                self.__nodeList = dictionary["NodeList"]
            if "InputPayload" in dictionary.keys():
                self.__input_payload = dictionary["InputPayload"]
            if "LaunchNodes" in dictionary.keys():
                self.__launch_nodes = dictionary["LaunchNodes"]
            if "RequestId" in dictionary.keys():
                self.__master_request_id = dictionary["RequestId"]
            if "TargetType" in dictionary.keys():
                self.__target_type = dictionary["TargetType"]
            if "IsExasplice" in dictionary.keys():
                self.__is_exasplice = dictionary["IsExasplice"]
            if "isExaComputePatching" in dictionary.keys():
                self.__is_exacompute_patching = dictionary["isExaComputePatching"]
            if "AdditionalOptions" in dictionary.keys():
                self.__additional_options = dictionary["AdditionalOptions"]
            if "RackName" in dictionary.keys():
                self.__rack_name = dictionary["RackName"]

            self.__allArgs = dictionary

        # Environment variables
        self.__sub_operation = None
        self.__kvm_env = False
        self.__exacc = False

        # Generic functions used by all
        self.__clupatchcheck = ebCluPatchHealthCheck(self.__cluctrl, aGenericHandler=self)

        # Set KVM environment value - True or False
        self.mSetKvmEnv()

        # Set ExaCC environment value - True or False
        self.mSetExaCC()

        # Set the current target type
        self.mSetCurrentTargetType(PATCH_DOM0)

        # Only Compute node related variables
        self.__node_local_patch_zip = self.mGetPatchFileDetails('DBPatchFile')
        if self.mIsExaSplice():
            self.__node_local_patch_zip2 = self.mGetPatchFileDetails('ExaspliceRepository')
        else:
            self.__node_local_patch_zip2 = self.mGetPatchFileDetails('Dom0YumRepository')
        self.__node_patch_zip_name = None
        self.__node_patch_zip2_name = None
        self.__node_patch_base = None
        self.__node_patch_zip = None
        self.__node_patch_base_after_unzip = None
        self.__node_patchmgr = None
        self.__node_patch_zip_size_mb = None
        self.__node_patch_zip2_size_mb = None
        self.__node_patch_necessary_space_mb = None
        self.__node_patchmgr_input_file = None
        self.__nodes_to_patch = []
        self.__node_patch_base_dir = PATCH_BASE
        self.__eligible_launch_node = None

    def mGetCluPatchCheck(self):
        return self.__clupatchcheck

    def mGetNodePatchBaseDir(self):
        return self.__node_patch_base_dir

    def mGetInputPayload(self):
        return self.__input_payload

    def mGetRequestObj(self):
        return self.__requestObj

    def mGetCustomizedDom0List(self):
        return self.__nodeList

    def mGetLaunchNodes(self):
        return self.__launch_nodes

    def mGetMasterReqId(self):
        return self.__master_request_id

    def mgetSubOperation(self):
        return self.__sub_operation

    def mSetSubOperation(self, aList):
        self.__sub_operation = aList

    def mGetEligibleLaunchNode(self):
        return self.__eligible_launch_node

    def mSetEligibleLaunchNode(self, aList):
        self.__eligible_launch_node = aList

    def mGetNodePatchZipName(self):
        return self.__node_patch_zip_name

    def mSetNodePatchZipName(self, aNodePatchZipName):
        self.__node_patch_zip_name = aNodePatchZipName
        
    def mGetNodePatchZip2Name(self):
        return self.__node_patch_zip2_name

    def mSetNodePatchZip2Name(self, aNodePatchZip2Name):
        self.__node_patch_zip2_name = aNodePatchZip2Name
        
    def mGetNodePatchBase(self):
        return self.__node_patch_base

    def mSetNodePatchBase(self, aNodePatchBase):
        self.__node_patch_base = aNodePatchBase
        
    def mGetNodePatchZip(self):
        return self.__node_patch_zip

    def mSetNodePatchZip(self, aNodePatchZip):
        self.__node_patch_zip = aNodePatchZip
        
    def mGetNodePatchBaseAfterUnzip(self):
        return self.__node_patch_base_after_unzip

    def mSetNodePatchBaseAfterUnzip(self, aNodePatchBaseAfterUnzip):
        self.__node_patch_base_after_unzip = aNodePatchBaseAfterUnzip
                
    def mGetNodePatchmgr(self):
        return self.__node_patchmgr

    def mSetNodePatchmgr(self, aNodePatchmgr):
        self.__node_patchmgr = aNodePatchmgr
        
    def mGetNodePatchZipSizeMB(self):
        return self.__node_patch_zip_size_mb

    def mSetNodePatchZipSizeMB(self, aNodePatchZipSizeMB):
        self.__node_patch_zip_size_mb = aNodePatchZipSizeMB
        
    def mGetNodePatchZip2SizeMB(self):
        return self.__node_patch_zip2_size_mb

    def mSetNodePatchZip2SizeMB(self, aNodePatchZip2SizeMB):
        self.__node_patch_zip2_size_mb = aNodePatchZip2SizeMB
        
    def mGetNodePatchNecessarySpaceMB(self):
        return self.__node_patch_necessary_space_mb

    def mSetNodePatchNecessarySpaceMB(self, aNodePatchNecessarySpaceMB):
        self.__node_patch_necessary_space_mb = aNodePatchNecessarySpaceMB

    # Abstract method definitions -- needed to be implemented by the child class
    # Can be left completely blank, or a base implementation can be provided
    # Note that ordinarily a blank interpretation implicitly returns `None`,
    # but by registering, this behaviour is no longer enforced.
    @abc.abstractmethod
    def mPreCheck(self):
        pass

    @abc.abstractmethod
    def mPatch(self):
        pass

    @abc.abstractmethod
    def mRollBack(self):
        pass

    @abc.abstractmethod
    def mPostcheck(self):
        pass

    @abc.abstractmethod
    def mImageBackup(self):
        pass

    def mExecuteTask(self):
        try:
            _task = self.mGetTask()
            if _task:
                if _task == TASK_PATCH:
                    return self.mPatch()
                elif _task == TASK_PREREQ_CHECK:
                    return self.mPreCheck()
                elif _task == TASK_ROLLBACK:
                    return self.mRollBack()
                elif _task == TASK_BACKUP_IMAGE:
                    return self.mImageBackup()
                elif _task == TASK_POSTCHECK:
                    return self.mPostcheck()
            else:
                self.mPatchLogError("No Task Mapped for ExaCompute Patching")
        except Exception as exp:
            self.mPatchLogWarn(f"Exception {str(exp)} occurred while executing ExaCompute Task")
            self.mPatchLogError(traceback.format_exc())

    def mGetAllArgs(self):
        return self.__allArgs

    """
     Currently backup mode is not sent through json payload. 
     By default, backups will be taken and set to YES.
    """
    def mGetBackUpMode(self):
        return OP_BACKUPMODE_YES

    def mGetEnvType(self):
        return ENV_PRODUCTION
    
    def mIsExacomputeAdditionalPreCheckEnabled(self):
        """
        Default value for patch_after_precheck is True in exacomputepatch.conf
        and parameter stored in the below format.

            "is_additional_precheck_priortopatch_enabled": "True"

        """
        if (self.mGetAdditionalOptions() and 'is_additional_precheck_priortopatch_enabled' in self.mGetAdditionalOptions()[0]\
                and (self.mGetAdditionalOptions()[0]['is_additional_precheck_priortopatch_enabled']).lower() == 'true'):
            return True
        else:
            return False

    def mIsExaSplice(self):
        """
        Check exasplice upgrade indicated or not.
        Return value:
            True  --> If exasplice or monthly upgrade is specified.
            False --> If exasplice is not specified.
        """
        # For Phase 1 implementation, additional options are not provided, so
        # Exasplice flag is by default sent False.
        if self.__is_exasplice and self.__is_exasplice.lower() == "yes":
            self.mPatchLogInfo("Patching type : Exasplice")
            _exasplice_patch_type = True
        else:
            self.mPatchLogInfo("Patching type : Quarterly")
            _exasplice_patch_type = False
        return _exasplice_patch_type

    def mGetPatchMgrDiagFiles(self, aNode):
        """
          Copies the last patchmgr_files found on all Compute Nodes
        """

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aNode)
        aRemotePath = self.mGetPatchmgrLogPathOnLaunchNode()
        _patchmgr_diag_tar = aRemotePath.split('/')[-1] + ".tar"

        self.mPatchLogInfo(
            f"aRemotePath = {aRemotePath}\n_patchmgr_diag_tar = {_patchmgr_diag_tar}\ndirname = {os.path.dirname(aRemotePath)}\n basename = {os.path.basename(aRemotePath)}\n")

        # tar the diagnostic files
        tar_cmd = f"cd {os.path.dirname(aRemotePath)}; tar cvf {_patchmgr_diag_tar} {os.path.basename(aRemotePath)};"
        try:
            self.mPatchLogInfo(f"Taring patch manager diagnosis files from Compute Node : {aNode}\n cmd={tar_cmd}")

            _in, _out, _err = _node.mExecuteCmd(tar_cmd)
        except Exception as e:
            self.mPatchLogWarn(f"Error while taring the diagnosis files({tar_cmd}) from Compute Node : {str(e)}")
            self.mPatchLogError(traceback.format_exc())

        # copy the tar to local
        try:
            self.mPatchLogInfo(
                f"Copying diagnosis '{_patchmgr_diag_tar}' file from node - {aNode} , location - {aRemotePath} to exacloud location - {self.mGetLogPath()}")
            _node.mCopy2Local(os.path.dirname(aRemotePath) + '/' + _patchmgr_diag_tar,
                              os.path.join(self.mGetLogPath(), _patchmgr_diag_tar))
        except Exception as e:
            self.mPatchLogWarn(
                f"Error while copying the diagnosis files from Compute Node error={str(e)}\n rfile={os.path.dirname(aRemotePath) + '/' + _patchmgr_diag_tar}\n lfile={os.path.join(self.mGetLogPath(), _patchmgr_diag_tar)} to exacloud location - {self.mGetLogPath()}")
            self.mPatchLogError(traceback.format_exc())

        # remove the tar file
        try:
            _in, _out, _err = _node.mExecuteCmd(f"cd {os.path.dirname(aRemotePath)}; rm -f {_patchmgr_diag_tar};")
        except Exception as e:
            self.mPatchLogWarn(f"Error while removing the diagnosis files from Compute Node : {str(e)}")
            self.mPatchLogError(traceback.format_exc())

        return

    def mGetNodeProgressData(self, aRequestUUID, aPrecheckState=None, aIncludeDataForAlreadyUpgradedNodes=False):
        """
        This method provides list of node progress data of the nodes based on the input arguments passed.
        If aPrecheckState is passed, it provides npdata list for the nodes which have patchmgr_status as aPrecheckState
        If aIncludeDataForAlreadyUpgradedNodes is passed, it provides npdata list for already upgraded nodes.
        """

        _requested_node_progress_data = []
        _already_upgraded_nodes = set()

        # Fetch current data for the current request from DB
        _request_data = ebCluExaComputePatch.mGetRequestData(aRequestUUID)
        if _request_data and "output" in _request_data:
            if "node_patching_status" in _request_data["output"] and "node_patching_progress_data" in _request_data["output"]["node_patching_status"]:
                _node_patching_progress_data = _request_data["output"]["node_patching_status"]["node_patching_progress_data"]

                for _node_patching_progress_data_elem in _node_patching_progress_data:
                    if aIncludeDataForAlreadyUpgradedNodes:
                        if (_node_patching_progress_data_elem["patchmgr_start_time"] ==
                                _node_patching_progress_data_elem["last_updated_time"] and
                                _node_patching_progress_data_elem["patchmgr_status"] == "Succeeded"):
                            _requested_node_progress_data.append(_node_patching_progress_data_elem)
                            _already_upgraded_nodes.add(_node_patching_progress_data_elem["node_name"])

                    if aPrecheckState:
                        if _node_patching_progress_data_elem["patch_sub_operation"] == "PATCHMGR_PRECHECK" and _node_patching_progress_data_elem["patchmgr_status"] == aPrecheckState:
                            if _node_patching_progress_data_elem["node_name"] not in _already_upgraded_nodes:
                                _requested_node_progress_data.append(_node_patching_progress_data_elem)

        if _requested_node_progress_data and len(_requested_node_progress_data) > 0:
            self.mPatchLogInfo(
                f"mGetNodeProgressData: filtered node progress data is {str(_requested_node_progress_data)}")

        return _requested_node_progress_data

    def mUpdateNodeProgressDataForComputeNodesWhereVMsAreRunning(self, aNodelistWhereVMsAreRunning):
        if aNodelistWhereVMsAreRunning and len(aNodelistWhereVMsAreRunning) > 0:
            _request_id = self.mGetRequestObj().mGetUUID()
            # Fetch current data for the current request from DB
            _request_data = ebCluExaComputePatch.mGetRequestData(_request_id)
            if _request_data and "output" in _request_data:
                if "node_patching_status" in _request_data["output"] and "node_patching_progress_data" in \
                        _request_data["output"]["node_patching_status"]:
                    _node_patching_progress_data = _request_data["output"]["node_patching_status"][
                        "node_patching_progress_data"]
                    for _node_patching_progress_data_elem in _node_patching_progress_data:
                        _node_name = _node_patching_progress_data_elem["node_name"]
                        if _node_name in aNodelistWhereVMsAreRunning:
                            _node_patching_progress_data_elem["last_updated_time"] = _node_patching_progress_data_elem[
                                "patchmgr_start_time"]
                            _node_patching_progress_data_elem["patchmgr_status"] = "Failed"
                            _node_patching_progress_data_elem["status"] = "Completed"

                    _patch_progressing_status_json = {}
                    _patch_progressing_status_json["node_patching_status"] = _request_data["output"][
                        "node_patching_status"]

                    '''
                     Write node progress details into requests table on Exacloud DB.
                    '''
                    try:
                        ebCluExaComputePatch.mUpdateRequestData(self.__requestObj, aData=_patch_progressing_status_json,
                                                                aOptions=self.mGetInputPayload(), aStatusObj=None)
                    except Exception as e:
                        self.mPatchLogError("Unable to write node progress details into Exacloud DB.")
                        self.mPatchLogError(traceback.format_exc())

    def mUpdatePatchProgressStatus(self, aNodeList=[], aAlreadyUpgradedNodeList=[], aNode=None, aMergeableNPDataList=[], aFailedNodeList=[]):
        """
           Following operation will be performed :-

               1. Update initial nodes status for discarded node
               2. Update initial nodes status for nodes which requires upgrade.

           Param list:
             aNodeList          --> List of nodes to which are expected undergo patching
             aDiscardedNodeList --> If the node is already upto date, default values
                                    are set
             aNode --> In case of mAdderror and mAddSuccess methods called.

             aMergeableNPDataList --> This is an optional parameter,
                                    this can contain npdata for precheck failed nodes and already upgraded nodes

             aFailedNodeList --> List of nodes where precheck failed before running patchmgr

             Sample json:
             "node_progressing_status": {
                    "infra_patch_start_time": "2022-05-10 09:31:43+0000",
                    "node_patching_progress_data": [
                        {
                            "node_name": "ecc201vm01.tawn.com",
                            "last_updated_time": "2022-02-09 10:20:33+0000",
                            "patchmgr_start_time": "2022-02-09 10:17:25+0000",
                            "status": "Pending",
                            "patchmgr_status": "Precheck",
                            "target_type": "dom0"
                        },
                        {
                            "node_name": "ecc201vm02.tawn.com",
                            "last_updated_time": "2022-02-09 10:16:54+0000",
                            "patchmgr_start_time": "2022-02-09 10:10:44+0000",
                            "status": "Completed",
                            "patchmgr_status": "Succeeded",
                            "target_type": "dom0"
                        }
                    ]
         },
        """

        patch_progressing_status_json = {}
        _data = {}
        _now = datetime.now()
        _patch_progressing_status_json = {}
        _patch_start_time = _now.strftime("%Y-%m-%d %H:%M:%S%z")
        _patch_failure_nodes = []
        _failed_to_get_npdata_from_xml = False
        _patchmgr_xml_data = None
        _patch_notification_file = None

        def _write_into_request_table_exacloud_db(_data):
            '''
             Write node progress details into requests
             table on Exacloud DB.
            '''
            try:
                ebCluExaComputePatch.mUpdateRequestData(self.__requestObj, aData=_data,
                                                  aOptions=self.mGetInputPayload(), aStatusObj=None)
            except Exception as e:
                self.mPatchLogError("Unable to write node progress details into Exacloud DB.")
                self.mPatchLogError(traceback.format_exc())


        if aNodeList or aAlreadyUpgradedNodeList or aFailedNodeList:

            # fill up the payload json for notification
            _data = {}
            patch_progressing_status_json = {}
            _patch_progressing_status_json = {}
            _patch_progress_data = []
            _node_progress_list = {}

            patch_progressing_status_json["launch_node"] = self.mGetLaunchNodes()
            if aAlreadyUpgradedNodeList and len(aAlreadyUpgradedNodeList) > 0:
                for _node_name in aAlreadyUpgradedNodeList:
                    _node_progress_list = {'node_name': _node_name, 'patchmgr_start_time': _patch_start_time,
                                           'last_updated_time': _patch_start_time, 'status': "Completed",
                                           'patchmgr_status': "Succeeded",
                                           'patch_sub_operation': self.mgetSubOperation()}
                    _patch_progress_data.append(_node_progress_list)

            if aNodeList and len(aNodeList) > 0:
                for _node_name in aNodeList:
                    _node_progress_list = {'node_name': _node_name, 'patchmgr_start_time': _patch_start_time,
                                           'last_updated_time': _patch_start_time, 'status': "NotStarted",
                                           'patchmgr_status': "Not Attempted",
                                           'patch_sub_operation': self.mgetSubOperation()}
                    _patch_progress_data.append(_node_progress_list)

            if aFailedNodeList and len(aFailedNodeList) > 0:
                for _node_name in aFailedNodeList:
                    _node_progress_list = {'node_name': _node_name, 'patchmgr_start_time': _patch_start_time,
                                           'last_updated_time': _patch_start_time, 'status': "Failed",
                                           'patchmgr_status': "Failed",
                                           'patch_sub_operation': self.mgetSubOperation()}
                    _patch_progress_data.append(_node_progress_list)


            patch_progressing_status_json["node_patching_progress_data"] = _patch_progress_data
            _data["node_patching_status"] = patch_progressing_status_json
            _patch_progressing_status_json = _data

        else:  # Update Case
            _node = exaBoxNode(get_gcontext())
            try:
                # Notification file.
                _notifications_dir = os.path.join(self.mGetPatchmgrLogPathOnLaunchNode(), "notifications")
                _node.mConnect(aHost=aNode)
                if _node.mFileExists(_notifications_dir):
                    # conisder the file without _ only from patchnotification directory
                    # Eg: /EXAVMIMAGES/dbserver.patch.zip_exadata_ovs_22.1.13.0.0.231006_Linux-x86-64.zip/dbserver_patch_231004/patchmgr_log_238eee1c-c529-47f3-8bb3-2054f7cedac7_patch_prereq_check/notifications/notification_patchmgr_2023101606441697438662223137712
                    _cmd_notification_file_cmd = f"ls {_notifications_dir} | grep -v '_$' | tail -1"
                    _i, _o, _e = _node.mExecuteCmd(_cmd_notification_file_cmd)
                    _out = _o.readlines()
                    if len(_out) > 0:
                        _patch_notification_file = _out[0]
               
                    if _patch_notification_file:
                        # read the content of new patchmgr xml
                        _notification_file_path = os.path.join(_notifications_dir, _patch_notification_file)
                        _read_patchmgr_xml_cmd = f"cat {_notification_file_path} 2>/dev/null"
                        _i, _o, _e = _node.mExecuteCmd(_read_patchmgr_xml_cmd)
                        if _o:
                            _patchmgr_xml_data = _o.read()

                if _node.mIsConnected():
                    _node.mDisconnect()
                
                # parse and get the json payload
                if _patchmgr_xml_data:
                    _patch_progressing_status_json, _patch_failure_nodes = self.mParsePatchmgrXml(_patchmgr_xml_data)

            except Exception as e:
                self.mPatchLogError(f"Failed to get patch notification status from node {str(e)}")
                self.mPatchLogError(traceback.format_exc())
                _failed_to_get_npdata_from_xml = True

        if not _failed_to_get_npdata_from_xml:
            # Merge current np data from DB and np data for precheck failed nodes/ nodes that are upto date
            _patch_progressing_status_json = self.mCombinePatchProgressData(_patch_progressing_status_json, aMergeableNPDataList)
            if len(_patch_progressing_status_json) != 0:
                _write_into_request_table_exacloud_db(_patch_progressing_status_json)
                
        return _patch_progressing_status_json, _patch_failure_nodes

    def mParsePatchmgrXml(self, patchmgrxml):
        """
            Parse the patchmgr xml file which has the current status of the software
            upgrade, running on Compute Node. Also, create the json output for sending the
            CNS (Cloud Notification Service).
        """

        # flag to indicate final status of the target
        _target_status_change_flag = False
        _patch_failure_node = []

        # fill up the payload json for notification
        _data = {}
        patch_progressing_status_json = {} 
        _patch_progress_data = []
        _node_progress_list = {}

        # To parse node target type within patchmgr xml and also update
        # topic/id appropriately for each target so that subscriber can also
        # opt CNS for any target(s), individually, while they can also opt
        # parent one 'critical.patch_of_exadata_infrastructure' to get all CNS.
        _node_type = ""
        _node_type = 'Compute_Node'

        # Get into the root of patchmgr xml notification and read launch node.
        try:
            _individual_node_data = {}
            _root = ET.fromstring(patchmgrxml)
            _launch_node = _root.findall('./Global_info/Launch_Node/Transition')
            if _launch_node:
                patch_progressing_status_json["launch_node"] = _launch_node[0].attrib['VALUE']
                _patchmgr_start_time = _launch_node[0].attrib['LAST_UPDATE_TIMESTAMP']

            for _each_node_type in _root.findall('./' + _node_type):
                _individual_node_data = {'status': "Pending", "patchmgr_start_time": _patchmgr_start_time,
                                         "node_name": _each_node_type.attrib['NAME']}

                _from_ver = _each_node_type.findall('./From_Version/Transition')
                if _from_ver:
                    _individual_node_data["from_version"] = _from_ver[0].attrib['VALUE']

                _to_ver = _each_node_type.findall('./To_Version/Transition')
                if _to_ver:
                    _individual_node_data["to_version"] = _to_ver[0].attrib['VALUE']

                _individual_node_data['patch_sub_operation'] = self.mgetSubOperation()

                # Goto last patch transition state
                _cur_pstate_tran = None
                for _each_pstate_tran in _each_node_type.findall('./Patch_State/Transition'):
                    _cur_pstate_tran = _each_pstate_tran

                if _cur_pstate_tran is not None:
                    _individual_node_data["patchmgr_status"] = _cur_pstate_tran.attrib['VALUE']
                    _individual_node_data["last_updated_time"] = _cur_pstate_tran.attrib['LAST_UPDATE_TIMESTAMP']
                    if _individual_node_data["patchmgr_status"] == "Started":
                        _individual_node_data["patchmgr_start_time"] = _cur_pstate_tran.attrib['LAST_UPDATE_TIMESTAMP']

                    _target_status_change_flag = True
                    if _individual_node_data["patchmgr_status"] in ["Succeeded", "Failed"]:
                        _individual_node_data['status'] = "Completed"
                    if _individual_node_data["patchmgr_status"] == "Failed":
                        _patch_failure_node.append(_individual_node_data["node_name"])
                    _patch_progress_data.append(_individual_node_data)

            patch_progressing_status_json["node_patching_progress_data"] = _patch_progress_data
            _data["node_patching_status"] = patch_progressing_status_json

            if not _target_status_change_flag:
                _data = {}

        except Exception as e:
            self.mPatchLogError(f'Error in parsing Patch Manager Notification XML. Error is : {str(e)} ')
            self.mPatchLogError(traceback.format_exc())

        return _data, _patch_failure_node

    def mAddError(self, aErrCode, aSuggestionMsg=None):
        """
         This method updates the request table with
         error handling details on exacloud DB
        """
        if aSuggestionMsg is not None:
            self.mPatchLogError(aSuggestionMsg)
        return self.mWriteCommonErrorHandlingParseXml(aErrCode, aSuggestionMsg)

    def mAddSuccess(self):
        """
         This method updates the request table with
         PATCH_SUCCESS_EXIT_CODE details on exacloud DB
        """
        return self.mWriteCommonErrorHandlingParseXml(PATCH_SUCCESS_EXIT_CODE)

    def mWriteCommonErrorHandlingParseXml(self, aErrCode, aSuggestionMsg=None):
        """
            Parses the notification xml for madderror and mAddSuccess methods.
            returns notification json based on parsed xml results.
        """
        _data = {}
        _patch_failure_nodes = []
        _notifications_dir = None
        _patchmgr_xml_data = None
        _patch_notification_file = None
        _ret = None
        _patch_progressing_status_json = {}

        try:
            _errObj = ebPatchFormatBuildErrorWithErrorAction(aErrCode, aSuggestionMsg, aTargetTypes=self.__target_type)
            if _errObj:
                mUpdateErrorObjectToDB(self.mGetCluControl(), _errObj)
                _ret = _errObj[0]

            if self.mGetEligibleLaunchNode() is not None:
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=self.mGetEligibleLaunchNode())

                # Notification file.
                _notifications_dir = os.path.join(self.mGetPatchmgrLogPathOnLaunchNode(), "notifications")

                # When error handling code is run, patchmgr log
                # might already be renamed.
                if _node.mFileExists(_notifications_dir+"_"+self.mGetTask()):
                    _notifications_dir = _notifications_dir+"_"+self.mGetTask()

                self.mPatchLogInfo(f"Patch notification directory : {_notifications_dir}")
                if _node.mFileExists(_notifications_dir):
                    self.mPatchLogInfo("Final patch progress details are collected..")
                    _cmd_notification_file_cmd = f"ls {_notifications_dir} | grep -v '_$' | tail -1"
                    _i, _o, _e = _node.mExecuteCmd(_cmd_notification_file_cmd)
                    _out = _o.readlines()
                    _patch_notification_file = _out[0]

                    # read the content of new patchmgr xml
                    if _patch_notification_file:
                        _read_patchmgr_xml_cmd = f"cat {_notifications_dir}/{_patch_notification_file} 2>/dev/null"
                        _i, _o, _e = _node.mExecuteCmd(_read_patchmgr_xml_cmd)
                        _patchmgr_xml_data = _o.read()
                    else:
                        self.mPatchLogWarn("Patchmgr notification log details are not available. Collecting notification details will be skipped.")

                    if _node.mIsConnected():
                        _node.mDisconnect()

                    if _patchmgr_xml_data:
                        # parse and get the json payload
                        _patch_progressing_status_json, _patch_failure_nodes = self.mParsePatchmgrXml(_patchmgr_xml_data)

            _npdata_for_precheck_failed_and_already_upgraded = None
            _npdata_for_precheck_failed_and_already_upgraded = self.mGetNodeProgressData(self.__requestObj.mGetUUID(), "Failed", aIncludeDataForAlreadyUpgradedNodes=True)

            _patch_progressing_status_json = self.mCombinePatchProgressData(_patch_progressing_status_json, _npdata_for_precheck_failed_and_already_upgraded)

            # AIM4EXA - Exadata/Exacloud error handling
            if aErrCode and aErrCode not in [ PATCH_SUCCESS_EXIT_CODE ]:
                self.mExacomputeAndExadataErrorhandling(_patch_progressing_status_json, _errObj, aErrCode)

            ebCluExaComputePatch.mUpdateRequestData(self.__requestObj, aData=_patch_progressing_status_json,
                                                aOptions=self.mGetInputPayload(), aStatusObj=_errObj,
                                                aDetailsErr=aSuggestionMsg)
        except Exception as e:
            self.mPatchLogError(f"Failed to get patch notification status from node {str(e)}")
            self.mPatchLogError(traceback.format_exc())
        finally:
            return _ret

    def mCombinePatchProgressData(self, aNPDataFromPatchMgrXml, aExistingNPDataList):
        """
        This method merges current npdata from db and existing npdata list provided.
        """
        _final_np_data = aNPDataFromPatchMgrXml
        _node_npdata_map_for_existing_data = {}
        if _final_np_data and len(_final_np_data) != 0:

            # Prepare the map of node to npdata for existing npdata provided
            if aExistingNPDataList and len(aExistingNPDataList) > 0:
                for _per_node_npdata in aExistingNPDataList:
                    _node_npdata_map_for_existing_data[_per_node_npdata["node_name"]] = _per_node_npdata

            # Merge two data lists into one
            if "node_patching_status" in _final_np_data and "node_patching_progress_data" in _final_np_data["node_patching_status"] and len(_node_npdata_map_for_existing_data) > 0:
                _cur_node_progress_data = _final_np_data["node_patching_status"]["node_patching_progress_data"]
                for _individual_node_data in _cur_node_progress_data:
                    if _individual_node_data["node_name"] in _node_npdata_map_for_existing_data:
                        _node_npdata_map_for_existing_data.pop(_individual_node_data["node_name"])

                for _node in _node_npdata_map_for_existing_data.keys():
                    _cur_node_progress_data.append(_node_npdata_map_for_existing_data[_node])

                _final_np_data["node_patching_status"]["node_patching_progress_data"] = _cur_node_progress_data

        return _final_np_data

    def mExacomputeAndExadataErrorhandling(self, aFinalNpData, aErrObj, aErrCode):
        '''
         This method populates exacompute patch failures
         related to AIM4EXA - Exadata error handling.
        '''
        _exadata_patch_err_json = {}
        _final_exacloud_error_json_data = {}
        _final_exacloud_error_json_data["node_patching_status"] = {}
        _simple_pairs = {}
        _nested_dicts = {}
        _combined_data = {}
        _err_code = None
        _patch_error_json_data = {}

        try:
            if aErrObj:
                _err_code = aErrObj[0]

            if aErrCode and aErrCode in [PATCHMGR_COMMAND_FAILED]:
                _final_exacloud_error_json_data["node_patching_status"] = {}
                _final_exacloud_error_json_data["node_patching_status"]['patch_mgr_error'] = {}
                for _launch_node in self.mGetLaunchNodes():
                    _exadata_patch_err_json = self.mGetPatchMgrErrorHandlingDetails(_launch_node)
                    if _exadata_patch_err_json and ("patch_mgr_error_details" in _exadata_patch_err_json):
                        _error_list = _exadata_patch_err_json["patch_mgr_error_details"]
                        if _error_list and len(_error_list) > 0:
                            if aFinalNpData and len(aFinalNpData) > 0:
                                for _existing_exadata_error in aFinalNpData:
                                    if _existing_exadata_error not in _exadata_patch_err_json["patch_mgr_error_details"]:
                                        _exadata_patch_err_json["patch_mgr_error_details"].append(_existing_exadata_error)
                                _final_exacloud_error_json_data["node_patching_status"][
                                    'patch_mgr_error'] = _exadata_patch_err_json
                            else:
                                _final_exacloud_error_json_data["node_patching_status"][
                                    'patch_mgr_error'] = _exadata_patch_err_json

            if self.mGetLogPath() and os.path.isdir(self.mGetLogPath()) is True:
                # self.mGetLogPath() = $EC_HOME/oeda/requests/96c8c3f2-26fa-11ef-bb06-0200170667b1/log/patchmgr_logs
                # Get rid of the patchmgr_logs. Final path e.g /u02/2011drop/admin/exacloud/oeda/requests/96c8c3f2-26fa-11ef-bb06-0200170667b1/log/
                _ec_home_log_dir = '/'.join((self.mGetLogPath()).split("/")[:-1])
            else:
                self.mPatchLogInfo("Output directory for generating exacloud patch failure json is not present")

            # Fetch current data for the current request from DB
            _request_data = ebCluExaComputePatch.mGetRequestData(self.__requestObj.mGetUUID())
            if _request_data and "output" in _request_data and "node_patching_status" in _request_data["output"]:
                _patch_error_json_data = _request_data["output"]["node_patching_status"]

            if _patch_error_json_data:
                _final_exacloud_error_json_data["node_patching_status"].update(_patch_error_json_data)

                _ecs_version = self.mGetECSLabelInformation()
                if _ecs_version:
                    _final_exacloud_error_json_data["ecs_label"] = _ecs_version

                # Will be useful once CP implementation for Exacompute patching will be in place.
                if self.mGetExternalWorkRequestID():
                        _final_exacloud_error_json_data["work_request_id"] = self.mGetExternalWorkRequestID()

                # Will be useful once CP implementation for Exacompute patching will be in place.
                if self.mGetControlPlaneRequestID():
                    _final_exacloud_error_json_data["control_plane_request_id"] = self.mGetControlPlaneRequestID()

                if self.mGetMasterReqId():
                    _final_exacloud_error_json_data["ecra_request_id"] = self.mGetMasterReqId()

                if self.mGetRequestObj():
                    _worker_id = self.mGetRequestObj().mGetUUID()
                    if _worker_id:
                        _final_exacloud_error_json_data["master_request_uuid"] = _worker_id
                        _exacloud_thread_log = f"{get_gcontext().mGetBasePath()}/log/threads/0000-0000-0000-0000/00000000-0000-0000-0000-000000000000/{_worker_id}_cluctrl.exacompute_patch_nodes.log"
                        _final_exacloud_error_json_data["exacloud_thread_log"] = _exacloud_thread_log

                _final_exacloud_error_json_data["TargetVersion"] = self.mGetTargetVersion()
                _final_exacloud_error_json_data["OperationStyle"] = self.mGetOpStyle()
                _final_exacloud_error_json_data["Operation"] = self.mGetTask()
                _final_exacloud_error_json_data["service"] = "ExaCompute Dom0 Patch"
                _final_exacloud_error_json_data["event_post_time"] = datetime.now().strftime("%Y-%m-%d:%H.%M.%S %Z")

                if self.mIsExaSplice():
                    _final_exacloud_error_json_data["PatchType"] = "Exasplice"
                else:
                    _final_exacloud_error_json_data["PatchType"] = "Quarterly"

                if aErrObj:
                    _final_exacloud_error_json_data["error_code"] = aErrObj[0]
                    _final_exacloud_error_json_data["error_msg"] = aErrObj[1]
                    _final_exacloud_error_json_data["error_detail"] = aErrObj[2]
                    _final_exacloud_error_json_data["error_action"] = aErrObj[3]

                # Separate simple key-value pairs and nested dictionaries for rearrangement
                for _key, _value in _final_exacloud_error_json_data.items():
                    if isinstance(_value, dict):
                        _nested_dicts[_key] = _value
                    else:
                        _simple_pairs[_key] = _value

                # Combine simple pairs and nested dictionaries, preserving their order
                _combined_data = {**_simple_pairs, **_nested_dicts}
                # Since Exacompute patching is not Fail fast, Exacloud and Patchmgr error can be observed during precheck
                # and the upgrade will continue on nodes where precheecks were successful.
                _exacloud_patch_error_json_file = f"{_ec_home_log_dir}/{self.mGetMasterReqId()}_exacloud_patch_error_{self.mgetSubOperation()}.json"
                self.mPatchLogInfo(
                    f"Generating a JSON file for the exacloud patch failure at {_exacloud_patch_error_json_file} ")
                with open(_exacloud_patch_error_json_file, 'w') as _ec_patch_error_fd:
                    json.dump(_combined_data, _ec_patch_error_fd, indent=4)

        except Exception as e:
            self.mPatchLogWarn(f"Failed to generate Exadata/Exacloud error handling json. Error - {str(e)}")
            self.mPatchLogError(traceback.format_exc())

    def mSetEnvironment(self):
        """
         Sets the common envrironment for all tasks in Compute node
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _launch_node = None
        _exacompute_node_list = None
        _unreachable_exacompute_node_list = None

        try:
            # Set current patch. Information necessary to update status in db
            self.mSetCurrentTargetType(PATCH_DOM0)

            if self.__node_local_patch_zip and self.__node_local_patch_zip2:
                # Select the appropriate zip file based on KVM (e.g exadata_ol7_19.3.6.0.0.200317_Linux-x86-64.zip ) or  OVM (e.g exadata_ovs_19.3.6.0.0.200317_Linux-x86-64.zip)
                nodezip2File = self.__node_local_patch_zip2
                if nodezip2File.find(',') > -1:
                    patchFiles = nodezip2File.strip().split(',')
                    for _file in (patchFiles):
                        if self.mIsKvmEnv() and (any(substring in _file for substring in KVM_FILE_IDENTIFIER_LIST)):
                            self.mPatchLogInfo(f"Dom0Repository KVM file is {_file} ")
                            self.__node_local_patch_zip2 = _file
                            break
                        elif not self.mIsKvmEnv() and ((any(substring in _file for substring in KVM_FILE_IDENTIFIER_LIST)) == False):
                            self.mPatchLogInfo(f"Dom0Repository NON KVM file is {_file} ")
                            self.__node_local_patch_zip2 = _file
                            break

                self.mPatchLogInfo(f"Compute node local patch zip file name {self.__node_local_patch_zip}")
                self.mPatchLogInfo(f"Compute node local patch zip-2 file name {self.__node_local_patch_zip2}")

                if not self.__node_local_patch_zip2:
                    _suggestion_msg = "Compute node Patch Zip file not found"
                    _ret = self.mAddError(PATCH_ZIP_FILE_NOT_FOUND, _suggestion_msg)
                    return _ret, _launch_node, _exacompute_node_list, _unreachable_exacompute_node_list


                # Compute node patching needs 2 zip files. first one has the patchmgr, second one is the actual patch
                self.mSetNodePatchZipName(self.__node_local_patch_zip.split("/")[-1])
                self.mSetNodePatchZip2Name(self.__node_local_patch_zip2.split("/")[-1])
                self.mSetNodePatchBase(self.mGetNodePatchBaseDir() + self.mGetNodePatchZipName() + "_" + self.mGetNodePatchZip2Name() + "/")
                self.mSetNodePatchZip(self.__node_patch_base + self.mGetNodePatchZipName())
                self.mSetNodePatchBaseAfterUnzip(self.mGetNodePatchBase() +
                                                      mGetFirstDirInZip(self.__node_local_patch_zip))
                self.mSetNodePatchmgr(self.mGetNodePatchBaseAfterUnzip() + "patchmgr")
                self.mSetNodePatchZipSizeMB(int(os.path.getsize(self.__node_local_patch_zip)) >> 20)
                self.mSetNodePatchZip2SizeMB(int(os.path.getsize(self.__node_local_patch_zip2.strip().strip())) >> 20)
                self.mSetNodePatchNecessarySpaceMB(
                        self.mGetNodePatchZipSizeMB() + self.mGetNodePatchZip2SizeMB() + int(
                    self.mGetExadataPatchWorkingSpaceMB()))

                '''
                mSetLaunchNodeToPatchOtherNodes call will choose a launch node which is pingable
                and eligible for patching operation
                If it is unable to find it will return appropriate error message
                '''
                _ret, _launch_node = self.mSetLaunchNodeToPatchOtherNodes()
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    return _ret, _launch_node, _exacompute_node_list, _unreachable_exacompute_node_list

                '''
                # Set target version based on the patch tar file version name.
                Quarterly:
                    ./PatchPayloads/19.3.2.0.0.191119/Dom0YumRepository/exadata_ovs_19.3.2.0.0.191119_Linux-x86-64.zip
                Monthly:
                    ./PatchPayloads/201015/ExaspliceRepository/exadata_exasplice_update_201015_Linux-x86-64.zip
                '''
                if not self.mIsExaSplice():
                    self.mSetTargetVersion(self.__node_local_patch_zip2.split("/")[-1].split("_")[2])
                else:
                    self.mSetTargetVersion(self.__node_local_patch_zip2.split("/")[-1].split("_")[3])

                '''
                 In this case, for _nodes_to_patch_except_initial All nodes from
                 xml need to be considered as passwdless ssh is required to be setup 
                 on all nodes and are used during ssh validation, patchmgr existence 
                 check and for performing a few config changes during CNS monitor start.
                '''
                _exacompute_node_list = self.mGetCustomizedDom0List()
                _unreachable_exacompute_node_list = []
                for _exacompute_node in self.mGetCustomizedDom0List():
                    if not self.mGetCluPatchCheck().mPingNode(_exacompute_node):
                        self.mPatchLogWarn(
                            f"{self.mGetCurrentTargetType().upper()} {_exacompute_node} is not pingable. Discarding for patching operation")
                        _exacompute_node_list.remove(_exacompute_node)
                        _unreachable_exacompute_node_list.append(_exacompute_node)

                if len(_exacompute_node_list) < 1:
                    _suggestion_msg = f"None of the target nodes provided are reachable, unable to proceed with precheck. Launch node list provided : {str(self.mGetCustomizedDom0List())}"
                    self.mPatchmgrLogInfo(_suggestion_msg)
                    _exit_code = self.mAddError(DOM0_NOT_PINGABLE, _suggestion_msg)
                    return _exit_code, _launch_node, _exacompute_node_list, _unreachable_exacompute_node_list

                # set ssh keys from node patchers to the nodes they will be patching
                _ssh_env_setup = ebCluSshSetup(self.mGetCluControl())
                _ssh_env_setup.mSetSSHPasswordlessForInfraPatching(_launch_node, _exacompute_node_list)
                # Store these in memory for clearing after each operation
                _sshEnvDict = {
                    "sshEnv": _ssh_env_setup,
                    "fromHost": [_launch_node],
                    "remoteHostLists": [_exacompute_node_list]
                }
                self.mSetSSHEnvSetUp(_sshEnvDict)
                self.mPatchLogInfo(
                    f"reachable_exacompute_node_list: {str(_exacompute_node_list)} unreachable_exacompute_node_list: {str(_unreachable_exacompute_node_list)}")
                return _ret, _launch_node, _exacompute_node_list, _unreachable_exacompute_node_list
        except Exception as e:
            _suggestion_msg = f"Unable to setup environment on {self.mGetTask()}"
            _ret = self.mAddError(INDIVIDUAL_PATCH_REQUEST_EXCEPTION_ERROR, _suggestion_msg)
            self.mPatchLogWarn(traceback.format_exc())
            _launch_node = None
            _exacompute_node_list = None
        finally:
            self.mPatchLogInfo("Finished Setting up Environment for Compute Nodes.")

    def mSetLaunchNodeToPatchOtherNodes(self):
        """
        Selects and sets 2 bases for Compute Node patching.
        use one to patch all other Compute Nodes
        and the other to patch initial Compute Nodes.
        """

        self.mPatchLogInfo("Set Launch Node for Compute nodes to patch other nodes.")
        _ret = PATCH_SUCCESS_EXIT_CODE
        _launch_ping_node = None
        _local_patch_zip = self.__node_local_patch_zip
        _patch_zip_name = self.mGetNodePatchZipName()
        _patch_zip_size_mb = self.mGetNodePatchZipSizeMB()
        _patch_base = self.mGetNodePatchBase()
        _patch_zip = self.mGetNodePatchZip()
        _patchmgr = self.mGetNodePatchmgr()
        _patch_necessary_space_mb = self.mGetNodePatchNecessarySpaceMB()
        _local_patch_zip2 = self.__node_local_patch_zip2
        _patch_base_after_unzip = self.mGetNodePatchBaseAfterUnzip()

        for _node in self.mGetLaunchNodes():
            if self.mGetCluPatchCheck().mPingNode(_node):
                _launch_ping_node = _node
                self.mSetEligibleLaunchNode(_node)
                break
            else:
                self.mPatchmgrLogInfo(f"Launch Node : {_node} is not pingable.")
                continue

        if _launch_ping_node is None:
            _suggestion_msg = f"None of the launch nodes provided are reachable, unable to proceed with patch operations. Launch node list provided : {str(self.mGetLaunchNodes())}"
            self.mPatchmgrLogInfo(_suggestion_msg)
            _ret = self.mAddError(DOM0_NOT_PINGABLE, _suggestion_msg)
            return _ret, None

        _launch_node_candidates = [ _launch_ping_node ]

        self.mPatchLogInfo(f"Launch node candidates: {str(_launch_node_candidates)}")

        # loop twice since we need to set 2 dom[0U]s as dom[0U] patchers
        _selected_launch_node = self.mSetLaunchNodeAsPatchBase(
            aLaunchNodeCandidates=_launch_node_candidates,
            aLocalPatchZipFile=_local_patch_zip,
            aPatchZipName=_patch_zip_name,
            aPatchZipSizeMb=_patch_zip_size_mb,
            aRemotePatchBase=_patch_base,
            aRemotePatchZipFile=_patch_zip,
            aRemotePatchmgr=_patchmgr,
            aRemoteNecessarySpaceMb=_patch_necessary_space_mb,
            aPatchBaseDir=self.__node_patch_base_dir,
            aSuccessMsg=((PATCH_DOM0.upper())),
            aMoreFilesToCopy=[(_local_patch_zip2,
                               _patch_base_after_unzip)])

        if _selected_launch_node is None:
            self.mPatchLogError(
                f"Unable to set Launch node for the current patch operation with Launch node name : {_selected_launch_node}.")
            _suggestion_msg = f"None of the launch nodes provided are eligible for patching operation : {str(self.mGetLaunchNodes())}"
            _ret = self.mAddError(UNABLE_TO_FIND_ELIGIBLE_LAUNCH_NODE, _suggestion_msg)
            return _ret, None

        self.mPatchLogInfo(f"Selected launch nodes {str(_selected_launch_node)}")
        return _ret, _selected_launch_node

    def mCustomCheck(self, aNodes=None, aTaskType=TASK_POSTCHECK):
        """
         This method performs a post checks independently on
         Exadata targets like Compute Node.

         Return value :
               1) ret -->
                   PATCH_SUCCESS_EXIT_CODE for success
                   Any other exit code other than PATCH_SUCCESS_EXIT_CODE for failure
        """

        _post_patch_failed_nodes = []
        _node_prepatch_version = {}
        _err_msg_template = "%s %s failed. Errors printed to screen and logs"
        _ret_code = PATCH_SUCCESS_EXIT_CODE

        '''
         Compute Node Independent Postchecks.
         aPrePatchVersion and aPostPatchTargetVersion are the image versions 
         before and after patches respectively. They do not have any 
         significance in case of running an independent post check, but they
         are only passed as they are mandatory arguments.
        '''

        for _node_to_patch in aNodes:
            _node_prepatch_version[_node_to_patch] = self.mGetCluPatchCheck().mCheckTargetVersion(_node_to_patch, PATCH_DOM0, aIsexasplice=self.mIsExaSplice())

            _ret_code = self.mNodePostCheck(aNode=_node_to_patch,
                                                 aPrePatchVersion=_node_prepatch_version[_node_to_patch],
                                                 aRollback=False,
                                                 aTaskType=aTaskType)

            if _ret_code != PATCH_SUCCESS_EXIT_CODE:
                _post_patch_failed_nodes.append(_node_to_patch)
                self.mPatchLogError(_err_msg_template % (self.mGetCurrentTargetType().upper(), "upgrade postchecks"))
                return _ret_code

        return _ret_code

    def mNodePostCheck(self, aNode, aPrePatchVersion, aRollback, aTaskType=None):
        """
        1) ret -->
            PATCH_SUCCESS_EXIT_CODE for success
            Any other exit code other than PATCH_SUCCESS_EXIT_CODE for failure

            checks currently done:
            *verify the image is listed as success
            *verify new version is what we expected for upgrade or rollback
            *check db services(dbserverd status) up on Compute Node.
        """

        self.mPatchLogInfo("Starting post patch checks for " + aNode)

        _check_node_up_for_secs = 0
        ret = PATCH_SUCCESS_EXIT_CODE
        aPostPatchTargetVersion = self.mGetTargetVersion()

        try:

            # check that the image is seen as success
            if not self.mGetCluPatchCheck().mCheckImageSuccess(aNode):
                _suggestion_msg = f"post-patch check: Compute Node : {aNode} image is not seen as success via imageinfo command"
                ret = self.mAddError(DOM0_IMAGE_NOT_SUCCESS, _suggestion_msg)
                return ret

            '''
             Image version checks are not performed as during
             independent postcheck option as we are not aware 
             whether upgrade or rollback was performed.
            '''
            if aTaskType not in [TASK_POSTCHECK]:
                # Check that the Compute node is at the requested version. if it was a rollback we just
                # check for the version to be lower than what it previously was.
                _current_node_version = self.mGetCluPatchCheck().mCheckTargetVersion(aNode, PATCH_DOM0, aIsexasplice= self.mIsExaSplice())
                if aRollback:
                    if self.mGetCluPatchCheck().mCheckTargetVersion(aNode, PATCH_DOM0, aPrePatchVersion, aIsexasplice= self.mIsExaSplice()) >= 0:
                        _suggestion_msg = f"Compute Node rollback was requested but the version seems to be unchanged, found version {aPrePatchVersion}, expected to be lower than {_current_node_version}"
                        ret = self.mAddError(VERSION_MISMATCH_DURING_ROLLBACK, _suggestion_msg)
                        return ret
                # if not a rollback, we need to be at the exact requested target version
                elif self.mGetCluPatchCheck().mCheckTargetVersion(aNode, PATCH_DOM0, aPostPatchTargetVersion, aIsexasplice= self.mIsExaSplice()) != 0:
                    _suggestion_msg = f"Compute node is not at the requested upgrade version {aPostPatchTargetVersion}, found version {_current_node_version}"
                    ret = self.mAddError(DOM0_NOT_AT_REQUESTED_VERSION, _suggestion_msg)
                    return ret

            # check that db services are up
            if not self.mGetCluPatchCheck().mCheckDBServices(aDBNode=aNode, aCheckRunning=True):
                self.mPatchLogInfo("Compute node postcheck for validating dbmcli services failed. Waiting for 120 seconds before retrying.")
                _sleep_monitor_iteration_count = 0
                # Max sleep time is 120 seconds
                while _sleep_monitor_iteration_count < 6:
                    if self.mGetCluPatchCheck().mCheckDBServices(aDBNode=aNode, aCheckRunning=True):
                        self.mPatchLogInfo(f"Dbmcli checks on {aNode} successful.")
                        break
                    else:
                        _sleep = 20
                        sleep(_sleep)
                        _sleep_monitor_iteration_count += 1
                        self.mPatchLogInfo(f"**** Iteration : [{_sleep_monitor_iteration_count:d}/6] - DBMCLI check is executed again after {_sleep} seconds.")

                if not self.mGetCluPatchCheck().mCheckDBServices(aDBNode=aNode, aCheckRunning=True):
                    _suggestion_msg = f"db services were not up on Compute Node : {aNode} "
                    ret = self.mAddError(DB_SERVER_SERVICE_DOWN, _suggestion_msg)
                    return ret

        except Exception as e:
            self.mPatchLogError("Unable to run Compute Node postchecks" + str(e))
        finally:
            return ret

    def mPatchRollbackExaComputeNonRolling(self, aBackupMode, aNodePatchList, aPrecheckpatchOperation=False, aRollback=False):
        """
         patch Compute nodes in non-rolling fashion
        """

        # List of launch nodes to update patch state metadata
        _ret = PATCH_SUCCESS_EXIT_CODE
        _task = ""
        _node_prepatch_version = {}
        _node_patcher = None
        _node = None
        _patch_failure_nodes = []
        _patchMgrObj = None
        _is_system_valid_state = True

        if aRollback:
            _task = TASK_ROLLBACK
        else:
            _task = TASK_PATCH

        _node_patch_base_after_unzip = self.mGetNodePatchBaseAfterUnzip()
        _node_patch_zip2_name = self.mGetNodePatchZip2Name()
        for _node in self.mGetLaunchNodes():
            if self.mGetCluPatchCheck().mPingNode(_node):
                _node_patcher = _node
                self.mSetEligibleLaunchNode(_node)
                break
            else:
                self.mPatchmgrLogInfo(f"Launch Node : {_node} is not pingable.")
                continue

        if _node_patcher is None:
            _suggestion_msg = f"None of the launch nodes provided are reachable, unable to proceed with patch operations. Launch node list provided : {str(self.mGetLaunchNodes())}"
            _ret = self.mAddError(DOM0_NOT_PINGABLE, _suggestion_msg)
            if aPrecheckpatchOperation:
                _no_action_required_further = True
                return _ret, _no_action_required_further, _patch_failure_nodes
            else:
                return _ret

        # Perform system consistency check only during patch operation on list of nodes.
        if not aRollback and not aPrecheckpatchOperation:
            _is_system_valid_state, _suggestion_msg = self.mCheckSystemConsitency(aNodePatchList)

        self.mPatchLogInfo(
            f"{self.mGetCurrentTargetType().upper()} {str(_node_patcher)} will be used to patch {str(aNodePatchList)} non-rolling")

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_node_patcher)

        for _node_to_patch in aNodePatchList:

            # stop rollback if it found to be a fresh install
            if aRollback and self.mCheckFreshInstall(_node_to_patch):
                _node_patch_failed = _node_to_patch
                _suggestion_msg = f"The node {_node_to_patch} seems to be fresh install and we cannot perform rollback operation. Current operation style is Non-Rolling"
                _ret = self.mAddError(DOM0_ROLLBACK_FAILED_FOR_FRESH_INSTALL, _suggestion_msg)
                break

            _pre_patch_version = self.mGetCluPatchCheck().mCheckTargetVersion(_node_to_patch, PATCH_DOM0, aIsexasplice=self.mIsExaSplice())
            _node_prepatch_version[_node_to_patch] = _pre_patch_version
            self.mPatchLogInfo(
                f"{self.mGetCurrentTargetType().upper()} {_node_to_patch} is at version {_pre_patch_version}")
        # end of for

        # create patchmgr object with bare minimum arguments
        # Use common methods and attributes from infrapatchmgrhandler
        _patchMgrObj = InfraPatchManager(aTarget=PATCH_DOM0, aOperation=_task, aPatchBaseAfterUnzip=self.mGetNodePatchBaseAfterUnzip(),
                                   aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

        # now set the component's operation specific arguments
        _patchMgrObj.mSetIsoRepo(aIsoRepo=_node_patch_zip2_name)
        _patchMgrObj.mSetIsExaSpliceEnabled(aIsExaSpliceEnabled=self.mIsExaSplice())
        _patchMgrObj.mSetTargetVersion(aTargetVersion=self.mGetTargetVersion())
        _patchMgrObj.mSetSystemConsistencyState(aSystemConsistencyState=_is_system_valid_state)

        # create patchmgr nodes file
        _input_file = _patchMgrObj.mCreateNodesToBePatchedFile(aLaunchNode=_node_patcher, aHostList=aNodePatchList)

        # prepare the patchmgr command for execution using the InfraPatchManager object
        _patch_cmd = _patchMgrObj.mGetPatchMgrCmd()

        # set the launch node and execute patchmgr cmd
        _patchMgrObj.mSetLaunchNode(aLaunchNode=_node_patcher)
        
        _patchMgrObj.mExecutePatchMgrCmd(aPatchMgrCmd=_patch_cmd)

        # Monitor console log
        # Following InfraPatchManager api sets the patchmgr execution status into mStatusCode method
        # hence not required to return/read a value from this api
        # this will help to use the patchMgr status apis 
        # (mIsSuccess/mIsFailed/mIsTimedOut/mIsCompleted) wherever required
        _patchMgrObj.mWaitForExaComputePatchMgrCmdExecutionToComplete()
        
        self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")

        _ret = _patchMgrObj.mGetStatusCode()
        _patch_failure_nodes = _patchMgrObj.mGetPatchFailedNodeList()
        if len(_patch_failure_nodes) > 0:
            self.mPatchLogError(f"Patchmgr {self.mGetTask()} operation failed on nodes : {str(_patch_failure_nodes)}")

        # Get the logs, diags and so on
        # Get the logs, diags and so on
        _patch_log = str(
            self.mGetDom0FileCode(_node_patcher, self.mGetPatchmgrLogPathOnLaunchNode()))
        self.mGetPatchMgrOutFiles(_node_patcher, self.mGetPatchmgrLogPathOnLaunchNode() ,_patch_log)

        '''
         Collect patchmgr diag logs for debugging only
         when the final exit code from patch operation 
         is not PATCH_SUCCESS_EXIT_CODE.
        '''
        if _ret != PATCH_SUCCESS_EXIT_CODE:
            self.mGetPatchMgrDiagFiles(_node_patcher)
        else:
            self.mPatchLogInfo("Patchmgr diag logs are not collected in case of a successful infra patch operation.")

        if aRollback:
            self.mGetPatchMgrMiscLogFiles(_node_patcher, self.mGetPatchmgrLogPathOnLaunchNode())
        else:
            self.mGetPatchMgrMiscLogFiles(_node_patcher, self.mGetPatchmgrLogPathOnLaunchNode(),
                                          TASK_PATCH,
                                          aNodePatchList)

        # Print all the log details at the end of log files copy.
        self.mPrintPatchmgrLogFormattedDetails()

        _node.mExecuteCmdLog(f"rm -f {_input_file}")

        if _ret != PATCH_SUCCESS_EXIT_CODE:
            _patch_failed_message = f"Error patching one of {str(aNodePatchList)} using {_node_patcher} to patch it. return code was {str(_ret)}. Errors on screen and in logs"
            self.mPatchLogError(_patch_failed_message)
            if _node.mIsConnected():
                _node.mDisconnect()
            return _ret

        # post checks on each node
        _post_patch_failed_nodes = []

        for _node_to_patch in aNodePatchList:
            _ret = self.mNodePostCheck(aNode=_node_to_patch,
                                           aPrePatchVersion=_node_prepatch_version[_node_to_patch],
                                           aRollback=aRollback)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                _post_patch_failed_nodes.append(_node_to_patch)

            if _post_patch_failed_nodes:
                _patch_failed_message = f"{self.mGetCurrentTargetType().upper()} {str(_post_patch_failed_nodes)} patching succeeded, but post-patch checks failed. Return code was = {str(_ret)} "
                self.mPatchLogError(_patch_failed_message)
                if _node.mIsConnected():
                    _node.mDisconnect()
                break

            if _node.mIsConnected():
                _node.mDisconnect()

            # if return code of previous patch operation is non-zero,
            # we had an issue so don't do any more patching
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                break

        return _ret

    def mCompareDbserverPatchFiles(self, aDbPatchFile1, aDbPatchFile2):
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

          -bash-4.2$ unzip -l PatchPayloads/DBPatchFile/dbserver.patch.zip | head -4
          Archive:  PatchPayloads/DBPatchFile/dbserver.patch.zip
           Length      Date    Time    Name
          ---------  ---------- -----   ----
                0  09-18-2024 23:46   dbserver_patch_240915.1/
          -bash-4.2$

          Here dbserver_patch_250313 is LATEST compared to dbserver_patch_231017 and
          will be consumed for patching.
        """
        _db_patch_file_date_format_1 = None
        _db_patch_file_date_format_2 = None
        try:
            _db_patch_file_date_format_1 = self.mGetDbserverPatchVersionDetails(aDbPatchFile1)
            _db_patch_file_date_format_2 = self.mGetDbserverPatchVersionDetails(aDbPatchFile2)

            if _db_patch_file_date_format_1 and _db_patch_file_date_format_2:
                if int(_db_patch_file_date_format_1) > int(_db_patch_file_date_format_2):
                    self.mPatchLogInfo(f"{aDbPatchFile1} is the LATEST dbserver patch file available based on the date.")
                    return aDbPatchFile1
                elif int(_db_patch_file_date_format_1) < int(_db_patch_file_date_format_2):
                    self.mPatchLogInfo(f"{aDbPatchFile2} is the LATEST dbserver patch file available based on the date.")
                    return aDbPatchFile2
                else:
                    self.mPatchLogInfo(f"Both the dbserver patch files have the same date: {_db_patch_file_date_format_2} and either of them can be used for patching.")
                    return aDbPatchFile2
            else:
                self.mPatchLogInfo("DBPatch file not found in either of the Patch Stage locations.")
                return None
        except Exception as e:
            self.mPatchLogWarn("Error in generating dbserver patch version file for patching. Error: %s" % str(e))
            self.mPatchLogTrace(traceback.format_exc())
            return None

    def mGetDbserverPatchVersionDetails(self, aDbPatchFileDir):
        """
         This method returns the db patch file along with version based
         on the input DB patch file path provided.

         -bash-4.4$ /bin/unzip -l /scratch/araghave/ecra_installs/abhi/mw_home/user_projects/
         domains/exacloud/PatchPayloads/DBPatchFile/dbserver.patch.zip | /bin/grep dbserver_ |
         /bin/head -1 | /bin/awk '{print $4}' | /bin/tr -d "/"
         dbserver_patch_250119
         -bash-4.4$
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

    def mGetPatchFileDetails(self, aPatchFileTag):
        """
          This function provides the exact location of
          the patch.
        """
        _version = self.mGetTargetVersion()
        patch_payloads_directory = 'PatchPayloads/'
        aPatchFile = None
        try:
            if self.mIsExaCC():
                self.__ociexacc_loc = self.__cluctrl.mCheckConfigOption('ociexacc_exadata_patch_download_loc').strip()
                if (self.__ociexacc_loc == '' or self.__ociexacc_loc == None or not self.__ociexacc_loc):
                    patch_payloads_directory = None
                else:
                    patch_payloads_directory = self.__ociexacc_loc + 'PatchPayloads/'

            _patch_loc_tmp = (os.path.join(patch_payloads_directory,_version))
            _patch_loc = (os.path.join(_patch_loc_tmp, aPatchFileTag))

            if aPatchFileTag == "DBPatchFile" and os.path.exists(os.path.join(patch_payloads_directory, "DBPatchFile")):
                aPatchFile = os.path.abspath((os.path.join(_patch_loc, "dbserver.patch.zip")))

                # As per convention, only dbserver.patch.zip must be staged under DBPatchFile directory.
                if os.path.exists(aPatchFile):
                    _version_common_directory = os.path.join((Path(os.path.dirname(aPatchFile))).parent.parent, "DBPatchFile/dbserver.patch.zip")
                    if _version_common_directory and os.path.exists(_version_common_directory) is True:
                        self.mPatchLogInfo(f"Checking for the latest dbserver.patch.zip between {str(_version_common_directory)} and {str(aPatchFile)}")
                        aPatchFile = self.mCompareDbserverPatchFiles(aPatchFile, _version_common_directory)
                    self.mPatchLogInfo(f"dbserver.patch.zip from {str(aPatchFile)} is used for patching.")
                    return aPatchFile

            if os.path.exists(_patch_loc):
                if not os.listdir(_patch_loc):
                    _suggestion_msg = f"Patch stage location : {_patch_loc} empty, please stage patch and retry."
                    _ret = self.mAddError(MISSING_PATCHES, _suggestion_msg)
                    raise Exception(_suggestion_msg)
            else:
                _suggestion_msg = f"Patch stage location : {_patch_loc} does not exist, please stage patch and retry."
                _ret = self.mAddError(MISSING_PATCHES, _suggestion_msg)
                raise Exception(_suggestion_msg)

            _nodeYumRepo = False
            if _patch_loc.find(KEY_NAME_Dom0_YumRepository) > -1:
                _nodeYumRepo = True

            if _patch_loc.find(KEY_NAME_DBPatchFile) > -1:
                _DBPatchFileDir = True
                
            if os.path.isdir(_patch_loc) is True:
                aPatchFile = os.path.abspath(_patch_loc)

                _nodefiles = []
                if _nodeYumRepo is True:
                    _listfile = [f for f in os.listdir(aPatchFile) if
                                 f.startswith('exadata_') and f.endswith('.zip') and _version in f]
                    _nodefiles = [os.path.join(aPatchFile, f) for f in _listfile]
                    aPatchFile = ','.join(_nodefiles)
                    self.mPatchLogInfo(f"Dom0Repository file for patch Version is {aPatchFile} ")
                elif _DBPatchFileDir is True:
                    self.mPatchLogInfo(f"DBserver patch file used for patch Version is {aPatchFile} ")
                    aPatchFile = os.path.join(aPatchFile, 'dbserver.patch.zip')
                else:
                    raise Exception(f"Patch file not found in {aPatchFile} ")
        except Exception as e:
            self.mPatchLogError('Unable to validate patch stage details on exacloud')
            self.mPatchLogError(traceback.format_exc())
        finally:
            return aPatchFile

    def mGetRunningVMList(self, aDom0):
        """
          Returns the list of VMs on the compute node
        """
        _domUs = []
        '''
        sed added at the end to remove empty line
        Example:
          # virsh list|tail -n+3|awk '{print $2}' | sed '/^$/d'
            scaqan03dv0208.us.oracle.com
            scaqan03dv0204.us.oracle.com
            scaqan03dv0201.us.oracle.com
            scaqan03dv0202.us.oracle.com
            scaqan03dv0203.us.oracle.com
        '''
        _cmd = ""

        """
        Note: In production, exacompute nodes are always kvm
        """
        if self.mIsKvmEnv():
            _cmd = "virsh list| grep -i 'running' | awk '{print $2}' | sed '/^$/d'"
        else:
            _cmd = "xm list|tail -n+3|awk '{print $1}'"

        if aDom0:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=aDom0)
            _in, _out, _err = _node.mExecuteCmd(_cmd)
            _output = _out.readlines()
            if _output:
                for _line in _output:
                    _domUs.append(_line.strip())
            _node.mDisconnect()

        return _domUs

    def mGetComputeNodeListWhereVMsAreRunning(self, aNodeListToPatch):
        """
          Returns the list of computenode list where VMs are in running state
        """
        _nodes_where_vms_are_running = set()
        if aNodeListToPatch and len(aNodeListToPatch) > 0 :
            for _compute_node in aNodeListToPatch:
                _vm_list = []
                _vm_list = self.mGetRunningVMList(_compute_node)
                if len(_vm_list) > 0:
                    _nodes_where_vms_are_running.add(_compute_node)

            if len(_nodes_where_vms_are_running) > 0:
                self.mPatchLogInfo(
                    f"ComputeNodes where VMs are still running  : {str(_nodes_where_vms_are_running)}")
            else:
                self.mPatchLogInfo("No ComputeNode has VMs in running state")
        return _nodes_where_vms_are_running
