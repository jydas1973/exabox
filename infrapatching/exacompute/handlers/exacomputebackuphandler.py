#!/bin/python
#
# $Header: ecs/exacloud/exabox/infrapatching/exacompute/handlers/exacomputebackuphandler.py /main/5 2025/05/07 04:51:45 araghave Exp $
#
# exacomputebackuphandler.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      exacomputebackuphandler.py
#
#    DESCRIPTION
#      Handler file for ExaCompute Patching
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
#    emekala     07/19/24 - ENH 36794217 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE EXACOMPUTE AND DOMU PATCHMGR CMDS
#    araghave    01/04/23 - Enh 34823378 - EXACLOUD CHANGES TO HANDLE 
#                           EXACOMPUTE PRECHECK AND BACKUP OPERATIONS
#    araghave    01/04/23 - Enh 34915866 - ADD SUPPORT FOR ROLLBACK IN
#                           EXACOMPUTE PATCHING
#    araghave    01/04/23 - Creation
#


from exabox.infrapatching.utils.constants import *
from exabox.ovm.hypervisorutils import *
from exabox.core.Context import get_gcontext
from exabox.infrapatching.exacompute.handlers.exacomputegenerichandler import ExaGenericHandler
from exabox.infrapatching.core.infrapatcherror import *
from exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler import InfraPatchManager
from exabox.infrapatching.utils.utility import mRegisterInfraPatchingHandlers, getTargetHandlerInstance
import traceback

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

class ExaBackupHandler(ExaGenericHandler):

    def __init__(self, *initial_data, **kwargs):
        super(ExaBackupHandler, self).__init__(*initial_data, **kwargs)
        self.mPatchLogInfo("ExaBackupHandler")
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [TASK_BACKUP_IMAGE], self)

    def mImageBackup(self):
        """
             Does the setup, filter the nodes to patch, idempotency check
             does customcheck and then performs the image rollback.
             Return codes:

               1) ret -->
                   PATCH_SUCCESS_EXIT_CODE for success
                   Any other exit code other than PATCH_SUCCESS_EXIT_CODE for failure

               2) Backup operation always run as non-rolling to save the
                  time. Also, since patchmgr notification has some issue
                  with rolling, it's always recommended to run backup as
                  non-rolling.
        """

        _ret = PATCH_SUCCESS_EXIT_CODE
        _node_patcher = None
        self.mSetSubOperation("PATCHMGR_BACKUP")

        try:
            # 1. Set up environment
            self.mSetEnvironment()

            self.mPatchLogInfo(
                f"\n\n---------------> Starting {TASK_BACKUP_IMAGE} on {self.mGetCurrentTargetType()}s <---------------\n")

            self.mSetPatchmgrLogPathOnLaunchNode(
                self.mGetNodePatchBaseAfterUnzip() + "patchmgr_log_" + self.mGetMasterReqId() + "_" + TASK_BACKUP_IMAGE)
            self.mPatchLogInfo(f"Patch manager Log Path on Launch Node is {self.mGetPatchmgrLogPathOnLaunchNode()}")

            # Get customized list of nodes
            _, _, _list_of_nodes, _already_upgraded_node_list = self.mFilterNodesToPatch(self.mGetCustomizedDom0List(), PATCH_DOM0,  TASK_BACKUP_IMAGE)

            # Set initial Patch Status Json.
            self.mUpdatePatchProgressStatus(aNodeList=_list_of_nodes, aAlreadyUpgradedNodeList=_already_upgraded_node_list)

            # 3. Perform customcheck
            if len(_already_upgraded_node_list) > 0:
                _ret = self.mCustomCheck(aNodes=_already_upgraded_node_list)
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    for aNode in _already_upgraded_node_list:
                        _suggestion_msg = f"Although '{self.mGetCurrentTargetType()}' nodes {aNode} are on requested version, critical services are not running."
                        _ret = self.mAddError(INFRA_PATCHING_DOM0_SERVICES_NOT_RUNNING, _suggestion_msg)
                    return _ret

            if len(_list_of_nodes) <= 0:
                # We need to populate more info about the patching operation when
                # no action is required and it requires to update ecra rack status
                # to previous status.
                self.mPatchLogInfo(
                    f"No available {self.mGetCurrentTargetType().upper()}s to run the patchmgr. Nothing to do here.")
                _ret = PATCH_SUCCESS_EXIT_CODE
                return _ret

            # Perform system consistency check
            _is_system_valid_state, _suggestion_msg = self.mCheckSystemConsitency(_list_of_nodes)
            if not _is_system_valid_state:
                _ret = self.mAddError(DOM0_SYSTEM_CONSISTENCY_CHECK_FAILED, _suggestion_msg)
                return _ret

            for _node in self.mGetLaunchNodes():
                if self.mGetCluPatchCheck().mPingNode(_node):
                    _node_patcher = _node
                    self.mSetEligibleLaunchNode(_node)
                    break
                else:
                    self.mPatchmgrLogInfo(f"Launch Node : {_node} is not pingable.")
                    continue

            if _node_patcher is None:
                _suggestion_msg = f"None of the launch nodes provided are reachable, unable to proceed with patch operations Launch node list provided : {str(self.mGetLaunchNodes())}"
                _ret = self.mAddError(DOM0_NOT_PINGABLE, _suggestion_msg)
                return _ret

            # Run the image backup in all the dom[0U]s except one
            _ret = self.mPatchImageBackupComputeNode(_node_patcher)

            if _ret == PATCH_SUCCESS_EXIT_CODE:
                self.mAddSuccess()

        except Exception as e:
            self.mPatchLogError(traceback.format_exc())
            _suggestion_msg = "Exception in Running Compute Node ImageBackup  " + str(e)
            _ret = self.mAddError(PATCH_DOM0_IMAGE_BACKUP_ERROR_EXCEPTION, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            return _ret

    def mPatchImageBackupComputeNode(self, aNode):
        """
               1) ret -->
                   PATCH_SUCCESS_EXIT_CODE for success
                   Any other exit code other than PATCH_SUCCESS_EXIT_CODE for failure
        """
        _exit_code = PATCH_SUCCESS_EXIT_CODE
        _patch_failure_nodes = []
        aListOfNodesToPatch = self.mGetCustomizedDom0List()
        _patchMgrObj = None

        ##### TBD: check if all vms are in the cluster (heartbeat).
        for _node_to_patch in aListOfNodesToPatch[:]:
            # check if all dom[0u]s are healthy/pingable first
            if not self.mGetCluPatchCheck().mPingNode(_node_to_patch):
                aListOfNodesToPatch.remove(_node_to_patch)
                self.mPatchLogWarn(f"{self.mGetCurrentTargetType().upper()} {_node_to_patch} is not pingable.")

        if not aListOfNodesToPatch:
            _suggestion_msg = f"No {self.mGetCurrentTargetType().upper()}s to take image backup."
            _exit_code = self.mAddError(PATCH_DOM0_IMAGE_BACKUP_ERROR_EXCEPTION, _suggestion_msg)
            return _exit_code

        # create patchmgr object with bare minimum arguments
        # Use common methods and attributes from infrapatchmgrhandler
        _patchMgrObj = InfraPatchManager(aTarget=PATCH_DOM0, aOperation=TASK_BACKUP_IMAGE, aPatchBaseAfterUnzip=self.mGetNodePatchBaseAfterUnzip(),
                                    aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

        # create patchmgr nodes file
        _input_file = _patchMgrObj.mCreateNodesToBePatchedFile(aLaunchNode=aNode, aHostList=aListOfNodesToPatch)
        self.__node_patchmgr_input_file = _input_file

        # prepare the patchmgr command for execution using the InfraPatchManager object
        _patch_backup_cmd = _patchMgrObj.mGetPatchMgrCmd()

        # If there are no patchmgr sessions running, then run patchmgr command
        # In this context, PATCH_SUCCESS_EXIT_CODE infers NO_PATCHMGR Session is running.

        # Same launch/_node_patcher
        # set the launch node and execute patchmgr cmd
        _patchMgrObj.mSetLaunchNode(aLaunchNode=aNode)
        
        _patchMgrObj.mExecutePatchMgrCmd(aPatchMgrCmd=_patch_backup_cmd)

        # Monitor console log
        # Following InfraPatchManager api sets the patchmgr execution status into mStatusCode method
        # hence not required to return/read a value from this api
        # this will help to use the patchMgr status apis 
        # (mIsSuccess/mIsFailed/mIsTimedOut/mIsCompleted) wherever required
        _patchMgrObj.mWaitForExaComputePatchMgrCmdExecutionToComplete()
        
        self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")

        _exit_code = _patchMgrObj.mGetStatusCode()
        _patch_failure_nodes = _patchMgrObj.mGetPatchFailedNodeList()
        if len(_patch_failure_nodes) > 0:
            self.mPatchLogError(f"Patchmgr backup operation failed on nodes : {str(_patch_failure_nodes)}")

        if len(aListOfNodesToPatch) > 0:

            # 3.- Get patchmgr backup logs
            _std_code = str(self.mGetDom0FileCode(aNode, self.mGetPatchmgrLogPathOnLaunchNode()))
            self.mGetPatchMgrOutFiles(aNode, self.mGetNodePatchBaseAfterUnzip(), _std_code)

            '''
             Collect patchmgr diag logs for debugging only
             when the final exit code from patch operation 
             is not PATCH_SUCCESS_EXIT_CODE.
            '''
            if _exit_code != PATCH_SUCCESS_EXIT_CODE:
                self.mGetPatchMgrDiagFiles(aNode)
            else:
                self.mPatchLogInfo(
                    "Patchmgr diag logs are not collected in case of a successful infra patch operation.")

        # 4. Remove temporary patchmgr log files
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aNode)
        _node.mExecuteCmdLog(f"rm -f {_input_file}")

        if _node.mIsConnected():
            _node.mDisconnect()

        return _exit_code
