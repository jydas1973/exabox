#!/bin/python
#
# $Header: ecs/exacloud/exabox/infrapatching/exacompute/handlers/exacomputepostcheckhandler.py /main/4 2025/05/07 04:51:45 araghave Exp $
#
# exacomputepostcheckhandler.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      exacomputepostcheckhandler.py
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
import traceback

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

class ExaPostcheckHandler(ExaGenericHandler):

    def __init__(self, *initial_data, **kwargs):
        super(ExaPostcheckHandler, self).__init__(*initial_data, **kwargs)
        self.mPatchLogInfo("ExaPostcheckHandler")

    def mPostcheck(self):
        """
             Does only customcheck which takes care of basic validations.
             Return codes:
               1) ret -->
                   PATCH_SUCCESS_EXIT_CODE for success
                   Any other exit code other than PATCH_SUCCESS_EXIT_CODE for failure
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        self.mSetSubOperation("PATCHMGR_POSTCHECK")

        try:
            # 1. Set up environment
            self.mSetEnvironment()

            self.mPatchLogInfo(
                f"\n\n---------------> Starting {TASK_POSTCHECK} on {self.mGetCurrentTargetType()}s <---------------\n")

            self.mSetPatchmgrLogPathOnLaunchNode(
                self.mGetNodePatchBaseAfterUnzip() + "patchmgr_log_" + self.mGetMasterReqId() + "_" + TASK_POSTCHECK)
            self.mPatchLogInfo(f"Patch manager Log Path on Launch Node is {self.mGetPatchmgrLogPathOnLaunchNode()}")

            # Get customized list of nodes
            _, _, _list_of_nodes, _already_upgraded_node_list = self.mFilterNodesToPatch(self.mGetCustomizedDom0List(), PATCH_DOM0, TASK_POSTCHECK)

            # Set initial Patch Status Json.
            self.mUpdatePatchProgressStatus(aNodeList=_list_of_nodes, aAlreadyUpgradedNodeList=_already_upgraded_node_list)

            if len(_list_of_nodes) <= 0:
                # We need to populate more info about the patching operation when
                # no action is required and it requires to update ecra rack status
                # to previous status.
                self.mPatchLogInfo(
                    f"No available {self.mGetCurrentTargetType().upper()}s to run the patchmgr. Nothing to do here.")
                _ret = PATCH_SUCCESS_EXIT_CODE
                return _ret

            # Compute node Independent Postchecks
            _ret = self.mCustomCheck(aNodes=self.mGetCustomizedDom0List())

            if _ret == PATCH_SUCCESS_EXIT_CODE:
                self.mAddSuccess()

        except Exception as e:
            self.mPatchLogError(traceback.format_exc())
            _suggestion_msg = "Failed to Perform PostCheck for Compute Node."
            _ret = self.mAddError(PATCH_OPERATION_FAILED, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            return _ret
