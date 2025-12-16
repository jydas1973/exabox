#!/bin/python
#
# $Header: ecs/exacloud/exabox/infrapatching/exacompute/handlers/exacomputerollbackhandler.py /main/4 2025/05/07 04:51:45 araghave Exp $
#
# exacomputerollbackhandler.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      exacomputerollbackhandler.py
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
#    araghave    01/04/23 - Enh 34823378 - EXACLOUD CHANGES TO HANDLE
#                           EXACOMPUTE PRECHECK AND BACKUP OPERATIONS
#    araghave    01/04/23 - Enh 34915866 - ADD SUPPORT FOR ROLLBACK IN
#                           EXACOMPUTE PATCHING
#    araghave    01/04/23 - Creation
#


from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.exacompute.handlers.exacomputegenerichandler import ExaGenericHandler
from exabox.infrapatching.core.infrapatcherror import *
from exabox.infrapatching.utils.utility import mRegisterInfraPatchingHandlers, getTargetHandlerInstance
import traceback

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

class ExaRollbackHandler(ExaGenericHandler):

    def __init__(self, *initial_data, **kwargs):
        super(ExaRollbackHandler, self).__init__(*initial_data, **kwargs)
        self.mPatchLogInfo("ExaRollbackHandler")
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [TASK_ROLLBACK], self)

    def mRollBack(self):

        """
            Does the setup, filter the nodes to rollback ,
            idempotency check, custom check and then run the rollback.
            Return codes:

               1) ret -->
                   PATCH_SUCCESS_EXIT_CODE for success
                   Any other exit code other than PATCH_SUCCESS_EXIT_CODE for failure
        """

        _ret = PATCH_SUCCESS_EXIT_CODE
        self.mSetSubOperation("PATCHMGR_ROLLBACK")

        _err_msg_template = "%s %s failed. Errors printed to screen and logs"
        try:
            # 1. Set up environment
            self.mSetEnvironment()

            self.mPatchLogInfo(
                f"\n\n---------------> Starting {TASK_ROLLBACK} on {self.mGetCurrentTargetType()}s <---------------\n")
            self.mSetPatchmgrLogPathOnLaunchNode(
                self.mGetNodePatchBaseAfterUnzip() + "patchmgr_log_" + self.mGetMasterReqId() + "_" + TASK_ROLLBACK)
            self.mPatchLogInfo(f"Patch manager Log Path on Launch Node is {self.mGetPatchmgrLogPathOnLaunchNode()}")

            # Get customized list of nodes
            _, _, _list_of_nodes, _already_upgraded_node_list = self.mFilterNodesToPatch(self.mGetCustomizedDom0List(), PATCH_DOM0,  TASK_ROLLBACK)

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
                self.mPatchmgrLogInfo(
                    f"No available {self.mGetCurrentTargetType().upper()}s to run the patchmgr. Nothing to do here.")
                _ret = PATCH_SUCCESS_EXIT_CODE
                return _ret

            _dont_rollback = False
            _list_of_nodes_rollback_possible = _list_of_nodes[:]
            for _node in _list_of_nodes:
                if self.mRollbackIsAvailable(_node):
                    # if the dbnode is at a lower version than the requested
                    # version, dont attempt to rollback.
                    # This is to stop doing a rollback after a rollback
                    # (ie: you can/should only rollback once)
                    # after a sucessfull upgrade
                    if (self.mGetCluPatchCheck().mCheckTargetVersion(_node, PATCH_DOM0, self.mGetTargetVersion(), aIsexasplice=self.mIsExaSplice()) < 0):
                        self.mPatchLogInfo(
                            f"{self.mGetCurrentTargetType().upper()} [{_node}] cannot be rolled back, its version is lower than the target version")
                        _dont_rollback = True
                        continue

                else:  # rollback is not available, just skip it
                    _list_of_nodes_rollback_possible.remove(_node)
                    self.mPatchLogInfo(
                        f"{self.mGetCurrentTargetType()} [{_node}] cannot be rolled back, rollback is not available")
                    continue

            if len(_list_of_nodes_rollback_possible) <= 0 or _dont_rollback:
                _suggestion_msg = _err_msg_template % (self.mGetCurrentTargetType().upper(),
                                                       "rollback unavailable because it would cause inconsistencies with versions on Compute Node.")
                _ret = self.mAddError(DOM0_ROLLBACK_FAILED_INCONSISTENT_DOM0_DOMU_VERSION, _suggestion_msg)
                return _ret

            _operationStyle = self.mGetOpStyle()
            if _operationStyle == OP_STYLE_NON_ROLLING:
                _ret = self.mPatchRollbackExaComputeNonRolling(self.mGetBackUpMode(), _list_of_nodes_rollback_possible, aRollback=True)
            else:
                _msg = f"{self.mGetCurrentTargetType().upper()} patching operation style [{_operationStyle}] not recognized or unsupported"
                self.mPatchLogError(_msg)
                raise Exception(_msg)

            if _ret == PATCH_SUCCESS_EXIT_CODE:
                self.mAddSuccess()

        except Exception as e:
            self.mPatchLogError(traceback.format_exc())
            _suggestion_msg = "Exception in Running Compute Node Rollback  " + str(e)
            _ret = self.mAddError(INDIVIDUAL_PATCH_REQUEST_EXCEPTION_ERROR, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            return _ret
