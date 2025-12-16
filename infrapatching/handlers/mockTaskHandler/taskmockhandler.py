#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/mockTaskHandler/taskmockhandler.py /main/4 2025/01/17 05:22:26 emekala Exp $
#
# taskmockhandler.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      taskmockhandler.py - Place holder for common functionalities among exadata
#      tasks.
#
#    DESCRIPTION
#      This module contains common methods which are shared between one or more
#      exadata operations (Storage Cell, Dom0, domU and Switches).
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    emekala     12/12/24 - ENH 37374442 - SUPPORT INFRA PATCH MOCK FWK TO
#                           ACCEPT MOCK RESPONSE IN JSON FORMAT VIA REST API
#    emekala     11/28/24 - ENH 37328901 - Add support to initialize infra
#                           patch mock setup when payload has mock request
#                           attribute
#    emekala     10/25/24 - ENH 37070223 - SYNC MOCK HANLDERS WITH LATEST CODE
#                           FROM CORE INFRAPATCHING HANDLERS AND ADD SUPPORT
#                           FOR CUSTOM RESPONSE AND RACK DETAILS
#    jyotdas     10/01/24 - ER 37089701 - ECRA Exacloud integration to enhance
#                           infrapatching operation to run on a single thread
#    araghave    08/30/24 - ER 36977545 - REMOVE SYSTEM FIRST BOOT IMAGE
#                           SPECIFIC CODE FROM INFRA PATCHING FILES
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    avimonda    06/17/24 - Bug 36586172: Dump JSON status in a file for
#                           automatic filing of exacloud bug.
#    antamil     03/11/24 - Enh 36372221 - Code changes for single VM EXACS
#                           patching support
#    araghave    10/19/23 - Bug 35747726 - PATCHING FAILING WITH | ERROR -
#                           ERROR MESSAGE IN A SHARED IBFABRIC ENVIRONMENT,
#                           COMBINATION OF AN IBSWITCH/NON-IBSWITCH TARGET
#                           PATCH CANNOT BE RUN IN PARALLEL
#    sdevasek    08/09/23 - ENH 35687013 - CREATE AND DELETE MARKER FILE DURING
#                           PATCHING WHEN CPS IS USED AS LAUNCHNODE
#    jyotdas     02/14/23 - ENH 35029839 - Enhance exacloud to create json file
#                           with patch failure details
#    sdevasek    09/01/22 - ENH 34510052 - EXACLOUD CHANGES TO GET IMAGEINFO
#                           DETAILS AS PART OF NODE_PROGRESS_STATUS
#    sdevasek    07/18/22 - ENH 34384737 - CAPTURE EXACLOUD START_TIME,
#                           EXACLOUD_END_TIME AND PATCHING TIME TAKEN BY NODES
#    sdevasek    05/22/22 - ENH 33859232 - TRACK TIME PROFILE INFORMATION FOR
#                           INFRAPATCH OPERATIONS
#    araghave    12/06/21 - Enh 33052410 - Purge System first boot image file
#                           for Dom0 space management
#    araghave    11/23/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES
#                           FROM ERROR.PY TO INFRAPATCHERROR.PY
#    nmallego    07/12/21 - ER 32925372 - Delete patch entry in release lock 
#    jyotdas     06/18/21 - Bug 32997721 - Patch wf failure does not report as
#                           failure
#    araghave    01/07/21 - Bug 32320030 - ROCE SWITCH REFACTOR CODE CHANGES
#    araghave    10/21/20 - Enh 31925002 - Error code handling implementation 
#                           for Monthly Patching
#    nmallego    10/27/20 - Enh 31540038 - INFRA PATCHING TO APPLY/ROLLBACK
#                           EXASPLICE/MONTHLY BUNDLE
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#
import abc
import os, sys
import time
import traceback
from time import sleep

from exabox.infrapatching.handlers.mockTargetHandler.genericmockhandler import GenericMockHandler
from exabox.infrapatching.handlers.mockTargetHandler.targetmockhandler import TargetMockHandler
from exabox.infrapatching.handlers.mockTargetHandler.domumockhandler import DomUMockHandler
from exabox.infrapatching.utils.utility import mGetInfraPatchingHandler, convertSeconds
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.core.DBStore import ebGetDefaultDB
from exabox.infrapatching.utils.infrapatchexecutionvalidator import InfrapatchExecutionValidator
from exabox.infrapatching.handlers.mockTargetHandler.domumockhandler import DomUMockHandler


sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

class TaskMockHandler(GenericMockHandler):

    def __init__(self, *initial_data, **kwargs):
        __metaclass__ = abc.ABCMeta
        super(TaskMockHandler, self).__init__(*initial_data, **kwargs)
        self.mPatchLogInfo("TaskMockHandler")
        self.__set_lock = False

    @abc.abstractmethod
    def mExecute(self):
        pass

    def mGetLock(self):
        return self.__set_lock

    def mPatchRequestRetried(self):
        """
         This method would return whether the patching request is re-attempted by
         ecra, perhaps, after ecra/exacloud is upgraded or rebooted.
         Return value:
           True  --> Same patch request is tried with master request id
           False --> If patch request is fresh and new one
        """

        if self.mGetPatchRequestRetried() == 'yes':
            return True
        else:
            return False

    def mAcquireLock(self):
        if self.mPatchRequestRetried():
            self.mPatchLogInfo("\n############################################")
            self.mPatchLogInfo("### PATCH OPERATION RE ATTEMPTED BY ECRA ###")
            self.mPatchLogInfo("############################################\n")

        # Try to acquire the ibfabric and cluster lock
        if InfrapatchExecutionValidator.isSwitchFabricLockingMechanismEnabled():
            if self.mGetFabric():
                # The master request always acquires the lock before launching the
                # current request. However, we want to be sure the lock is still
                # there. If acquiring the lock returns False, it means the lock is
                # actually there.
                self.mPatchLogInfo("Checking IBFabric lock before running patchmgr")
                if (any(x in self.mGetTargetTypes() for x in [PATCH_IBSWITCH, PATCH_ROCESWITCH])):
                    _lock = self.mGetFabric().mLock(self.mGetClusterId(), False)
                else:
                    _lock = self.mGetFabric().mLock(self.mGetClusterId(), True)

                if _lock is False:
                    self.mPatchLogInfo("Lock was correctly acquired by master request")
                    self.__set_lock = True
        else:
            # Reset all stale entries in the ibfabriclocks table.
            self.mGetFabric().mResetSwitchFabricdata()

    def mReleaseLock(self):
        # Release ibfabric and cluster lock
        # No action required in case of switch fabric locking
        # is disabled in infrapatching.conf
        if self.__set_lock is True and self.mGetFabric():
            self.mPatchLogInfo("Releasing IBFabric lock")
            # If a switch task was executed, we must be sure do_switch is
            # updated to 'no'
            if (any(x in self.mGetTargetTypes() for x in [PATCH_IBSWITCH, PATCH_ROCESWITCH])):
                self.mGetFabric().mSetDoSwitch('no')
                self.mGetFabric().mUpdateDoSwitchDB()

            self.mGetFabric().mRelease(self.mGetClusterId())
        else:
            # Reset all stale entries in the ibfabriclocks table.
            self.mGetFabric().mResetSwitchFabricdata()

        if self.mGetFabric():
            _cluster_key = self.mGetCluControl().mBuildClusterId()

            # Delete patch operataion entry for the current operation if already exits.
            self.mPatchLogInfo(
                f"mReleaseLock: Deleting patch operation entry for {self.mGetTargetTypes()[0]} on {_cluster_key}")
            _db = ebGetDefaultDB()
            _db.mDeleteClusterPatchOperationsEntry(_cluster_key, self.mGetTargetTypes()[0])

            # Extra process should not be alive. This is an 'extra' check to
            # ensure the process is not longer alive
            if self.mGetProcess() and self.mGetProcess().is_alive():
                self.mPatchLogError(f'Terminate extra process: {str(self.mGetProcess().pid)}')
                self.mGetProcess().terminate()

            if self.mGetProcessCnsMonitor() and self.mGetProcessCnsMonitor().is_alive():
                self.mPatchLogError(f'Terminate monitor process for patch notification generation {str(self.mGetProcessCnsMonitor().pid)}')
                self.mGetProcessCnsMonitor().terminate()

    def mExecuteTask(self):
        """
         Called from clucontrol.py in the exacloud layer for any patching operation
         1. Acquires the lock

         2. Performs the appropriate operation on the selected target through the mExecute method
           e.g for patch operation on dom0
           a. the mExecute method on PatchHandler will be called
           b. Then the mPatch method on Dom0Handler will be called

         3. Finally , releases the lock

         Return codes:
            1) ret -->
                0 for success
                non-zero for failure
            This is the return code which is returned to clucontrol.py in the exacloud layer
        """

        _rc = PATCH_SUCCESS_EXIT_CODE
        _exacloud_start_time = None
        _exacloud_end_time = None
        _context_target_handler = None

        try:
            _exacloud_start_time = time.strftime("%Y-%m-%d %H:%M:%S%z")
            _task_type = self.mGetTask()
            if _task_type in [TASK_PREREQ_CHECK, TASK_PATCH, TASK_ROLLBACK_PREREQ_CHECK, TASK_ROLLBACK]:
                _target_types = self.mGetTargetTypes()
                _target_type = ''
                _nodes_patching_requested = []
                if PATCH_DOM0 in _target_types:
                    _nodes_patching_requested = self.mGetDom0List()
                    _target_type = PATCH_DOM0
                elif PATCH_DOMU in _target_types:
                    _nodes_patching_requested = self.mGetDomUList()
                    _target_type = PATCH_DOMU
                elif PATCH_CELL in _target_types:
                    _nodes_patching_requested = self.mGetCustomizedCellList()
                    _target_type = PATCH_CELL
                elif PATCH_IBSWITCH  in _target_types:
                    _target_type = PATCH_IBSWITCH
                    _nodes_patching_requested = self.mGetSwitchList()
                elif PATCH_ROCESWITCH in _target_types:
                    _target_type = PATCH_ROCESWITCH
                    _nodes_patching_requested = self.mGetSwitchList()

                # mIsTimeStatsEnabled is set to True or False by this call
                self.mSetCollectTimeStatsFlag(self.mGetCollectTimeStatsParam(_target_type))
                self.mCreateInfrapatchingTimeStatsEntry(_nodes_patching_requested, "PRE_PATCH")

        except Exception as exp:
            self.mPatchLogWarn(f"Exception {str(exp)} occurred while creating time stat entry for pre_patch stage")

        if not self.mIsSingleWorkerRequest():
            self.mPatchLogInfo("Acquiring lock since this is not a single Worker Request")
            self.mAcquireLock()

        _has_error = False
        try:
            # Run patch task/tasks
            _start = time.time()
            _rc = self.mExecute()
            if self.mIsMockEnv():
                _mock_response_details_for_target_in_task_type = self.mGetMockResponseDetailsForTargetInTaskType(aTaskType=self.mGetTask(), aTargetType=self.mGetTargetTypes())
                _error_code = _mock_response_details_for_target_in_task_type['error_code']
                if _error_code:
                    _rc = _error_code
                if 'run_mock_task_for_secs' in _mock_response_details_for_target_in_task_type:
                    _run_mock_task_for_secs = _mock_response_details_for_target_in_task_type['run_mock_task_for_secs']
                    self.mPatchLogInfo(f"run_mock_task_for_secs defined for target type: {self.mGetTargetTypes()} in task type: {self.mGetTask()} in mock_config and its value is: {_run_mock_task_for_secs}secs")
                    if _run_mock_task_for_secs is not None and len(_run_mock_task_for_secs) > 0 and _run_mock_task_for_secs > "0":
                        _run_mock_task_for_secs = str(_run_mock_task_for_secs).strip()
                        if _run_mock_task_for_secs.isnumeric():
                            """
                             useful for stress testing to mimic production usecase where one or more infra patch request(s) holding worker 
                             thread(s) for completion for the given numbder of secs and other concurrent requests hitting exacloud
                            """
                            self.mPatchLogInfo(f"Sleeping for: {_run_mock_task_for_secs}secs as requested by the user before completing the mock task {self.mGetTask()}...")
                            sleep(int(_run_mock_task_for_secs))

            _end = time.time()
            _time_elapsed = _end - _start
            self.mPatchLogInfo(
                f"Execution time for the operation {self.mGetTask()} on targets {self.mGetTargetTypes()} is {convertSeconds(_time_elapsed)} in hh:mm:ss ")
            if _rc == PATCH_SUCCESS_EXIT_CODE:
                #This statement will be used by tests to check for success
                self.mPatchLogInfo(f"Operation {self.mGetTask()} completed successfully")
            else:
                self.mPatchLogError(f"Operation {self.mGetTask()} Failed")
                _has_error = True

            if _rc == EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR:
                self.mUpdatePatchProgressStatusForTimedOutNodes()

        except Exception as e:
            self.mPatchLogError("mRunPatchMgr error:" + str(e))
            self.mPatchLogError(traceback.format_exc())
            _suggestion_msg = "mRunPatchMgr error:" + str(e)
            _rc = INFRA_PATCHING_TASK_HANDLER_PATCH_REQUEST_EXCEPTION
            self.mAddError(_rc, _suggestion_msg)
            _has_error = True
            return _rc

        finally:
            if not self.mIsSingleWorkerRequest():
                self.mPatchLogInfo("Releasing lock since this is not a single Worker Request")
                self.mReleaseLock()
            else:
                # for single thread patching , update patchlist request status
                # Values are  Failed, Done or Pending based on the _rc (Return code from patching)
                self.mPatchLogInfo(f"Updating Final status in patchlist table for single thread request based on return code {_rc}")
                self.mUpdatePatchListRequestStatus(_rc)

            #Update Patch Status for the END STEP by calling the appropriate function on the current targetHandler
            for _current_handler in INFRA_PATCHING_HANDLERS.values():
                if _current_handler and isinstance(_current_handler,TargetMockHandler):
                    _context_target_handler = _current_handler
                    if _current_handler.mGetExecutedTargets():
                        _comment = "_".join(_current_handler.mGetExecutedTargets())
                    else:
                        _comment = 'None'
                    _current_handler.mUpdatePatchStatus(True, STEP_END, _comment)
                    self.mPatchLogInfo("Updated Patch Status")
                    break

            # Purge System first boot image file only during Dom0 QMR upgrade operation.
            if self.mGetInfrapatchExecutionValidator().mCheckCondition('checkIfSystemImagesCanBeCleanedUp'): 
                _context_dom0_target_handler = mGetInfraPatchingHandler(INFRA_PATCHING_HANDLERS,PATCH_DOM0)
                if _context_dom0_target_handler and _rc == PATCH_SUCCESS_EXIT_CODE:
                    self.mPatchLogInfo("Invoking mCleanupSystemImages post Dom0 QMR upgrade.")
                    _context_dom0_target_handler.mCleanupSystemImages()

            # Update endtime for all unfilled stages
            self.mUpdateInfrapatchingTimeStatsForUnfilledStages()

            _exacloud_end_time = time.strftime("%Y-%m-%d %H:%M:%S%z")

            # Update time_stats into exacloud DB
            self.mUpdateCurrentInfrapactchOperationTimeStatsToDB(_exacloud_start_time, _exacloud_end_time)

            # Update image version details in node_progress_data
            self.mUpdateImageVersionInfoDetailsInNodeProgressData()

            #Dump data in file for Automatic filing of ExaCloud/Exadata tickets
            if _has_error == True:
                self.mDumpPatchFailureJsonFile()

            # Delete the ecra_request if marker file if exists.
            if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsPatchBaseMarkerFileApplicable'):
                if _context_target_handler and isinstance(_context_target_handler,DomUMockHandler) :
                    _patch_base_after_unzip = _context_target_handler.mGetDomUPatchBaseAfterUnzip()
                    if _patch_base_after_unzip:
                        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
                            self.mDeleteMarkerFileFromPatchBase(_patch_base_after_unzip, aNode=_context_target_handler.mGetDomUToPatchDomU())
                        else:
                            self.mDeleteMarkerFileFromPatchBase(_patch_base_after_unzip)


            # Finally clean up the registry of infra patching handlers
            INFRA_PATCHING_HANDLERS.clear()

        return _rc
