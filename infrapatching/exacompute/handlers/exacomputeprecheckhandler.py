#!/bin/python
#
# $Header: ecs/exacloud/exabox/infrapatching/exacompute/handlers/exacomputeprecheckhandler.py /main/6 2025/05/07 04:51:45 araghave Exp $
#
# exacomputepatchhandler.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      exacomputepatchhandler.py
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
#    sdevasek    10/04/23 - ENH 35853718 - CHECK FOR EXISTING VMS BEFORE
#                           PATCHING NODES FOR EXACOMPUTE
#    araghave    01/04/23 - Enh 34823378 - EXACLOUD CHANGES TO HANDLE
#                           EXACOMPUTE PRECHECK AND BACKUP OPERATIONS
#    araghave    01/04/23 - Enh 34915866 - ADD SUPPORT FOR ROLLBACK IN
#                           EXACOMPUTE PATCHING
#    araghave    01/04/23 - Creation
#

import os
import sys
import traceback
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.infrapatching.exacompute.handlers.exacomputegenerichandler import ExaGenericHandler
from exabox.infrapatching.core.infrapatcherror import *
from exabox.infrapatching.utils.constants import TASK_PREREQ_CHECK, PATCH_EXACOMPUTE, INFRA_PATCHING_HANDLERS
from exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler import InfraPatchManager
from exabox.infrapatching.utils.utility import mRegisterInfraPatchingHandlers, getTargetHandlerInstance

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

class ExaPrecheckHandler(ExaGenericHandler):

    def __init__(self, *initial_data, **kwargs):
        super(ExaPrecheckHandler, self).__init__(*initial_data, **kwargs)
        self.mPatchLogInfo("ExaComputePrecheckHandler")
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [TASK_PREREQ_CHECK], self)

    def mPreCheck(self, aPrecheckpatchOperation=False):
        """
            Does the setup, filter the nodes to perform pre-check,
            idempotency check , custom check and then run the pre-check
            of Compute nodes.
            Return codes:
               1) ret -->
                   PATCH_SUCCESS_EXIT_CODE for success
                   Any other exit code other than PATCH_SUCCESS_EXIT_CODE for failure
               2) Precheck operation always run as non-rolling to save the
                  time. Also, since patchmgr notification has some issue
                  with rolling, it's always recommended to run precheck as
                  non-rolling.
        """

        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_required_further = False
        _launch_ping_node = None
        _consolidated_precheck_failure_nodes = []
        _node_set_where_vms_are_running = set()
        self.mSetSubOperation("PATCHMGR_PRECHECK")

        try:
            # 1. Set up environment
            self.mSetEnvironment()

            self.mPatchLogInfo(
                f"\n\n---------------> Starting {TASK_PREREQ_CHECK} on {self.mGetCurrentTargetType()}s <---------------\n")

            # Get customized list of nodes
            _, _, _list_of_nodes, _already_upgraded_node_list = self.mFilterNodesToPatch(self.mGetCustomizedDom0List(), PATCH_DOM0,  TASK_PREREQ_CHECK)

            # Set initial Patch Status Json.
            self.mUpdatePatchProgressStatus(aNodeList=_list_of_nodes, aAlreadyUpgradedNodeList=_already_upgraded_node_list)

            if len(_list_of_nodes) <= 0:
                # We need to populate more info about the patching operation when
                # no action is required and it requires to update ecra rack status
                # to previous status.
                _suggestion_msg = f"No available {(self.mGetCurrentTargetType()).upper()}s to run the patchmgr. Nothing to do here."
                _ret = PATCH_SUCCESS_EXIT_CODE
                if aPrecheckpatchOperation:
                    _no_action_required_further = True
                    return _ret, _no_action_required_further, _consolidated_precheck_failure_nodes
                else:
                    return _ret

            # Prepare the computenode list where vms are running
            _node_set_where_vms_are_running = self.mGetComputeNodeListWhereVMsAreRunning(_list_of_nodes)
            self.mUpdateNodeProgressDataForComputeNodesWhereVMsAreRunning(_node_set_where_vms_are_running)
            _patch_failure_nodes = list(_node_set_where_vms_are_running)

            # 3. Perform customcheck
            if len(_already_upgraded_node_list) > 0:
                self.__nodes_already_upgraded = _already_upgraded_node_list[:]
                _ret = self.mCustomCheck(aNodes=_already_upgraded_node_list)
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    for _node in _already_upgraded_node_list:
                        _suggestion_msg = f"Although '{self.mGetCurrentTargetType()}' nodes {_node} are on requested version, critical services are not running."
                        _ret = self.mAddError(INFRA_PATCHING_DOM0_SERVICES_NOT_RUNNING, _suggestion_msg)

                    if aPrecheckpatchOperation:
                        _no_action_required_further = True
                        return _ret, _no_action_required_further, _consolidated_precheck_failure_nodes
                    else:
                        return _ret

            self.mSetPatchmgrLogPathOnLaunchNode(
                self.mGetNodePatchBaseAfterUnzip() + "patchmgr_log_" + self.mGetMasterReqId() + "_" + TASK_PREREQ_CHECK)
            self.mPatchLogInfo(f"Patch manager Log Path on Launch Node is {self.mGetPatchmgrLogPathOnLaunchNode()}")

            # Perform system consistency check
            _is_system_valid_state, _suggestion_msg = self.mCheckSystemConsitency(_list_of_nodes)
            if not _is_system_valid_state:
                _ret = self.mAddError(DOM0_SYSTEM_CONSISTENCY_CHECK_FAILED, _suggestion_msg)

                if aPrecheckpatchOperation:
                    return _ret, _no_action_required_further, _consolidated_precheck_failure_nodes
                else:
                    return _ret

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
                _ret = self.mAddError(DOM0_NOT_PINGABLE, _suggestion_msg)
                if aPrecheckpatchOperation:
                    _no_action_required_further = True
                    return _ret, _no_action_required_further, _consolidated_precheck_failure_nodes
                else:
                    return _ret

            def _patch_precheck_node(aNode):
                _nodes_count = len(self.mGetCustomizedDom0List())
                _domOUs_count_on_same_target_version = 0
                _exit_code = PATCH_SUCCESS_EXIT_CODE
                _patchmgr_precheck_failure_nodes = []
                aNodeListToPatch = self.mGetCustomizedDom0List()
                _patchMgrObj = None

                if aNode is None:
                    _suggestion_msg = f"None of the launch nodes provided are reachable, unable to proceed with precheck. Launch node list provided : {str(self.mGetLaunchNodes())}"
                    _exit_code = self.mAddError(DOM0_NOT_PINGABLE, _suggestion_msg)
                    self.mPatchLogInfo(f'Launch node = {aNode}, List of Nodes to work on = {str(aNodeListToPatch)}')

                ##### TBD: check if all vms are in the cluster (heartbeat).
                for _node_to_patch in aNodeListToPatch[:]:
                    # check if all dom[0u]s are healthy/pingable first
                    if not self.mGetCluPatchCheck().mPingNode(_node_to_patch):
                        self.mPatchLogWarn(
                            f"{self.mGetCurrentTargetType().upper()} {_node_to_patch} is not pingable. Discarding for precheck")
                        aNodeListToPatch.remove(_node_to_patch)
                        continue

                    # Bug 23149472 - PATCHMGR INTERNAL ERROR PREREQ CHECK IF A NODE
                    #               IS ALREADY AT TARGET VERSION
                    #  to work around this, we will manually check to see if the
                    #  requested precheck version is already the installed version
                    #  on every node to precheck
                    if (self.mGetCluPatchCheck().mCheckTargetVersion(_node_to_patch, PATCH_DOM0, self.mGetTargetVersion(),
                                                                     aIsexasplice=self.mIsExaSplice()) >= 0):
                        self.mPatchLogInfo(
                            f"{_node_to_patch} is already at the requested version {self.mGetTargetVersion()} (or higher)")
                        # Remove this node from the list that we will run pre-checks
                        # with patchmgr
                        aNodeListToPatch.remove(_node_to_patch)
                        _domOUs_count_on_same_target_version += 1

                if (aNodeListToPatch and
                        ((_nodes_count - len(aNodeListToPatch)) !=
                         _domOUs_count_on_same_target_version)):
                    self.mPatchLogWarn(
                        f"Cluster is not coherent. Expected {str(_nodes_count)} {self.mGetCurrentTargetType().upper()}s, but got {str(len(aNodeListToPatch))}")

                self.mPatchLogInfo(
                    f"Compute node details : _nodes_count = {_nodes_count}, aListOfNodesToPatch = {len(aNodeListToPatch)}, doums_count_on_same_target_version = {_domOUs_count_on_same_target_version}")

                # if we removed all of the nodes to run pre-check, because they were
                # already at the requested version just return success
                if (len(aNodeListToPatch) <= 0 and
                        _nodes_count == _domOUs_count_on_same_target_version):
                    self.mPatchLogInfo("All the Compute Nodes are in the requested version. "
                                       "No action required")
                    return PATCH_SUCCESS_EXIT_CODE, list(_node_set_where_vms_are_running)

                # Remove the nodes where vms are running from patchable node list
                if len(_node_set_where_vms_are_running) > 0:
                    self.mPatchLogInfo(
                        f"Following compute nodes {str(_node_set_where_vms_are_running)} are skipped for precheck/patch since VMs are running on this/these node(s).")
                    aNodeListToPatch = [ x for x in aNodeListToPatch if x not in _node_set_where_vms_are_running]

                # Return failure if no Compute Nodes to precheck
                if len(aNodeListToPatch) <= 0:
                    _suggestion_msg = f"No {self.mGetCurrentTargetType().upper()}s to run precheck."
                    _exit_code = self.mAddError(NO_NODES_AVAILABLE_FOR_PRECHECK, _suggestion_msg)
                    return _exit_code, list(_node_set_where_vms_are_running)

                # create patchmgr object with bare minimum arguments
                # Use common methods and attributes from infrapatchmgrhandler
                _patchMgrObj = InfraPatchManager(aTarget=PATCH_DOM0, aOperation=TASK_PREREQ_CHECK, aPatchBaseAfterUnzip=self.mGetNodePatchBaseAfterUnzip(),
                                           aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

                # now set the component's operation specific arguments
                _patchMgrObj.mSetIsoRepo(aIsoRepo=self.mGetNodePatchZip2Name())
                _patchMgrObj.mSetIsExaSpliceEnabled(aIsExaSpliceEnabled=self.mIsExaSplice())
                _patchMgrObj.mSetTargetVersion(aTargetVersion=self.mGetTargetVersion())

                # create patchmgr nodes file
                _input_file = _patchMgrObj.mCreateNodesToBePatchedFile(aLaunchNode=aNode, aHostList=aNodeListToPatch)
                self.__node_patchmgr_input_file = _input_file

                # prepare the patchmgr command for execution using the ExaPatchManager object
                _patch_precheck_cmd = _patchMgrObj.mGetPatchMgrCmd()

                # 1.- Run pre_check
                # set the launch node and execute patchmgr cmd
                _patchMgrObj.mSetLaunchNode(aLaunchNode=aNode)
                
                _patchMgrObj.mExecutePatchMgrCmd(aPatchMgrCmd=_patch_precheck_cmd)

                # 2. - Monitor console log
                # Following ExaPatchManager api sets the patchmgr execution status into mStatusCode method
                # hence not required to return/read a value from this api
                # this will help to use the patchMgr status apis 
                # (mIsSuccess/mIsFailed/mIsTimedOut/mIsCompleted) wherever required
                _patchMgrObj.mWaitForExacomputePatchMgrCmdExecutionToComplete()
                
                self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")

                _exit_code = _patchMgrObj.mGetStatusCode()
                _patchmgr_precheck_failure_nodes = _patchMgrObj.mGetPatchFailedNodeList()
                if len(_patchmgr_precheck_failure_nodes) > 0:
                    self.mPatchLogError(
                        f"Patchmgr precheck operation failed on nodes : {str(_patchmgr_precheck_failure_nodes)}")

                # 3.- Get patchmgr pre-check logs
                _precheck_log = str(self.mGetDom0FileCode(aNode, self.mGetPatchmgrLogPathOnLaunchNode()))
                self.mGetPatchMgrOutFiles(aNode, self.mGetPatchmgrLogPathOnLaunchNode(), _precheck_log)

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

                self.mGetPatchMgrMiscLogFiles(aNode,
                                              self.mGetPatchmgrLogPathOnLaunchNode(),
                                              TASK_PREREQ_CHECK,
                                              aNodeListToPatch)

                # Print all the log details at the end of log files copy.
                self.mPrintPatchmgrLogFormattedDetails()

                # 4. Remove temporary patchmgr log files
                self.mPatchLogInfo("Remove temporary patchmgr log files")
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=aNode)
                _node.mExecuteCmdLog(f"rm -f {_input_file}")
                if _node.mIsConnected():
                    _node.mDisconnect()

                # Combine computenode list where VMs are running with patchmgr precheck failure node list
                for _compute_node in _node_set_where_vms_are_running:
                    _patchmgr_precheck_failure_nodes.append(_compute_node)

                return _exit_code, _patchmgr_precheck_failure_nodes
                # end of _patch_precheck_node

            # Run the pre_check in all the dom[0U]s except one
            _ret, _consolidated_precheck_failure_nodes = _patch_precheck_node(_launch_ping_node)

            # There are nodes on which precheck failed so return failed error code
            if len(_consolidated_precheck_failure_nodes) > 0 and _ret == PATCH_SUCCESS_EXIT_CODE:
                _suggestion_msg = f"Precheck operation failed on {str(_consolidated_precheck_failure_nodes)} ."
                _ret = self.mAddError(PRECHECK_OPERATION_FAILED_ON_COMPUTE_NODES, _suggestion_msg)

            if _ret == PATCH_SUCCESS_EXIT_CODE:
                self.mAddSuccess()

        except Exception as e:
            self.mPatchLogError(traceback.format_exc())
            _suggestion_msg = "Exception in Running Compute Node Precheck  " + str(e)
            _ret = self.mAddError(INDIVIDUAL_PATCH_REQUEST_EXCEPTION_ERROR, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            if aPrecheckpatchOperation:
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    self.mPatchLogError(
                        f"Precheck returned with error : {str(_ret)}, Precheck failure nodes : {str(_consolidated_precheck_failure_nodes)}")
                return _ret, _no_action_required_further, _consolidated_precheck_failure_nodes
            else:
                return _ret
