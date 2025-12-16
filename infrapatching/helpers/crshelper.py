#
# crshelper.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      crshelper.py - Place holder for common methods of crs and heartbeatcheck
#
#    DESCRIPTION
#      This module contains common methods of crs and heartbeatcheck
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    09/27/25 - Enhancement Request 38457501 - EXACC GEN2
#                           | INFRA PATCHING |ERFORM HEARTBEAT CHECKS AND
#                           CRS AUTOSTARTUP IN PARALLEL FOR NON-ROLLING
#                           PATCHING
#    rbhandar    10/09/25 - Bug 38510857 - NON ROLLING PATCHING OPERATION POST
#                           PATCH HAS DUPLICATE CELLS IN LIST
#    araghave    09/11/25  - Enh 38173247 - EXACLOUD CHANGES TO SUPPORT DOMU
#                            ELU INFRA PATCH OPERATIONS
#    sdevasek    08/28/25 - Enh 38282910 - CLUSTER-WIDE CRS CHECK SHOULD BE
#                           PERFORMED ONLY ON VM CLUSTERS BELONG TO THE DOM0S
#                           WITHIN THE MAINTENANCE WINDOW
#    araghave    08/13/25 - Enh 38228272 - EXACC GEN2 | PATCHING | SWITCH BACK
#                           TO OPC USER FOR ALL INFRA PATCH USE CASES IN CASE
#                           OF ROOT KEY INJECTION FAILS
#    apotluri    07/15/25 - Enhancement Request 38169498 - CAPTURE CRS START
#                           EXECUTION TIME IN PATCHING TIME STATS DURING DOM0
#                           AND DOMU OS PATCHING
#    rbhandar    07/11/25 - Enh 38081907 - DOMUOPS: ENHANCEMENTS IN GETTING
#                           THE GRID_HOME DURING VM OS PATCHING WHEN MULTIPLE
#                           ENTRIES EXIST IN /ETC/ORATAB 
#    araghave    07/09/25 - Enh 38168978 - REMOVE REDUNDANT VALIDATIONS DONE AS
#                           PART OF CRS AUTO STARTUP CHECKS
#    sdevasek    07/09/25 - Enh 38153648 - AVOID CALLING CELL LIST ON WHICH
#                           GRIDDISK ARE ONLINE/SYNCING STATE MULTIPLE TIMES
#                           DURING HEARTBEAT CHECK
#    araghave    06/24/25 - Bug 37923575 - DOM0 PATCH WITH INCLUDE NODE LIST IS
#                           FAILING WITH 'CRS IS DISABLED ON DOMU AND FURTHER
#                           CRS VALIDATIONS WILL BE SKIPPED' ON TWO NODE
#                           CLUSTER WHERE IT SHOULD ONLY SKIP THE CRS CHECKS
#                           INSTEAD OF FAILING
#    avimonda    06/23/25 - Bug 37899705 - DOMU IMAGE UPDATE PRECHECK IS NOT
#                           CHECKING CRS AUTOSTART STATUS
#    sdevasek    05/26/25 - Enh 38098176 - FILTER OUT WARNINGS OTHER MESSAGES
#                           WHEN CRSCTL CONFIG CRS IS RUN
#    avimonda    05/23/25 - Bug 37833454 - EXACC GEN2 - INFRA PATCHING - DOM0
#                           POST HEARTBEAT VALIDATION HUNG IF OUTPUT SIZE MORE
#                           THAN 1 MB
#    vikasras    05/21/25 - Enh 37252485 - EXACC GEN 2| PATCHING | ENHANCE CRS
#                           VALIDATION TOOLING TO DISTINGUISH BETWEEN
#                           PRE- AND POST-PATCHING FAILURES
#    diguma      04/24/25 - bug 37862181: EXACS:GMR:EXASCALE:DOM0 PATCHING
#                           FAILING WITH UNABLE TO ESTABLISH HEARTBEAT ON THE
#                           CELLS. NOT ALL CRS/DB SERVICES ARE UP ON DOMU. CRS
#                           DID NOT STARTUP EVEN AFTER TIMEOUT OF 1800 SECS.
#    sdevasek    04/14/25 - Bug 37824905 -DOM0 PATCHING USING ROOT KEYS FOR CDB
#                           DOWNTIME CHECKS
#    sdevasek    04/07/25 - Bug 37780190  - DOM0 DBHEALTHCHECKS: DOM0 PATCHING 
#                           IS NOT FAILING FOR CDB DEGRDADATION SCENARIO INCASE
#                           OF SINGLE NODE VM CLUSTER
#    avimonda    03/28/25 - Bug 37754307 - AIM4ECS:0X0305001D - PDB IS IN A
#                           DEGRADED STATE.
#    araghave    03/24/25 - Enh 37164753 - USE ROOT USER TO CONNECT TO DOMU TO
#                           PERFORM CRS CHECKS ON EXACC ENVIRONMENTS DURING
#                           DOM0 PATCHING
#    sdevasek    03/18/25 - Bug 35265324 - PATCHING IS NOT CHECKING CRS HB WHEN
#                           GRIDDISK STATUS IS UNKNOWN
#    sdevasek    03/18/25 - Enh 37661543 - DB HEALTHCHECKS - PROVIDE DB DETAILS
#                           ALSO IN THE ERROR MESSAGES DURING DOM0 PATCHING
#    araghave    03/04/25 - Bug 37417431 - EXACS | DOMU | UNWANTED SSH
#                           CONNECTION FROM 169.254.200.1 LOCKING OPC USER
#    sdevasek    02/25/25 - Bug 37612441 - PDB DEGRADATION CHECKS:CORRESPONDING
#                           CDB OF A DEGRADED PDB IS NOT MENTIONED IN THE ERROR
#                           MESSAGE
#    sdevasek    02/25/25 - Bug 37612441 - PDB DEGRADATION CHECKS:CORRESPONDING 
#                           CDB OF A DEGRADED PDB IS NOT MENTIONED IN THE ERROR
#                           MESSAGE
#    avimonda    02/09/25 - Enh 37291048: EXACC GEN 2 | POST PATCHING HB ISSUE,
#                           VM NOT ACCESSIBLE | ERROR DETAILS ENHANCEMNT NEEDED
#    nelango     01/21/25 - Bug 37500959: Grep only the gihome
#    sdevasek    01/07/24 - Bug 37442949 - DB HEALTH CHECKS - INCORRECT ERROR
#                           MESSAGE FOR LISTENER RESOURCE
#    sdevasek    12/13/24 - Enh 37390121 - PDB IS IN READ ONLY AND RESTRICTED
#                           NODE IN REMOTE NODE BUT PATCHING SUCCEEDED IN LOCAL
#                           NODE  
#    sdevasek    12/19/24 - Enh 37304854 - ADD DB HEALTH CHECKS METHODS TO
#                           CRS HELPER MODULE
#    bhpati      12/01/24 - Bug 36563682 - AIM4EXACLOUD:0X03030008 - UNABLE TO
#                           ESTABLISH HEARTBEAT ON THE CELLS. NOT ALL CRS/DB
#                           SERVICES ARE UP ON DOMU
#    sdevasek    11/15/24 - Creation
#    sdevasek    11/15/24 - Enh 37172948 - ISOLATE CRS/HEARTBEAT/DB HEALTH
#                           CHECKS TO A SEPARATE API BASED MODULE
#    sdevasek    11/15/24 - Creation

import logging
import traceback
from time import sleep, time
import json
from uuid import uuid4

from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.infrapatching.handlers.loghandler import LogHandler
from exabox.infrapatching.utils.utility import mValidateTime, mConvertTimeEscli, mTruncateErrorMessageDescription, \
    mGetPdbDegradedStatesMatrix
from exabox.ovm.cludbaas import ebCluDbaas

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))
log = logging.getLogger(__name__)


class CrsHelper(LogHandler):
    def __init__(self, aHandler=None):
        super(CrsHelper, self).__init__()
        self.__handler = aHandler
        self.__dom0_hb_info = {}
        # Contains all the vms on which crs auto start is enabled and crs is running
        self.__crs_autostart_enabled_vm_set = set()

    def mGetHandlerInstance(self):
        return self.__handler

    def mGetCRSAutoStartEnabledVMSet(self):
        return self.__crs_autostart_enabled_vm_set

    def mCheckCrsIsEnabled(self, aDomU):
        """
         Checks the CRS config is enabled or disabled. Returns PATCH_SUCCESS_EXIT_CODE if enabled
         else, DOMU_INVALID_CRS_HOME, CRS_IS_DISABLED

        This is used by both dom0 and domu patching. For dom0, crs operations are done using as opc user if exists and
        as root user during domu patching
        """

        _ret = PATCH_SUCCESS_EXIT_CODE
        _node = exaBoxNode(get_gcontext())
        _domu_customer_hostname = None
        _suggestion_msg = None
        try:
            _domu_customer_hostname = self.mGetHandlerInstance().mGetDomUCustomerNameforDomuNatHostName(aDomU)
            if self.mGetHandlerInstance().mGetCurrentTargetType() == PATCH_DOM0:
                _user_to_connect_with = self.mGetHandlerInstance().mGetUserDetailsBasedOnDomUhostname(aDomU)
                if _user_to_connect_with:
                    _node.mSetUser(_user_to_connect_with)
            _node.mSetMaxRetries(self.mGetHandlerInstance().mGetMaxNumberofSshRetries())
            _node.mConnect(aHost=aDomU)

            _ret, _cmd = self.mGenCrsctlCmd(_node, "config crs", _domu_customer_hostname)
            if _ret == DOMU_INVALID_CRS_HOME:
                if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                    self.mPatchLogWarn(
                        f"Error encountered while validating crs command path and CRS checks cannot be performed during precheck on DomU : {str(_domu_customer_hostname)}.. During prechecks, these errors are only logged as warnings in thread logs.")
                else:
                    self.mPatchLogError(
                        f"Error encountered while validating crs command path and CRS checks and further infra patch operation cannot proceed on DomU : {str(_domu_customer_hostname)}.")
                return _ret

            if _ret == PATCH_SUCCESS_EXIT_CODE:
                _in, _out, _err = _node.mExecuteCmd(_cmd)
                _output = _out.readlines()
                # expcting the following output
                # CRS-4622: Oracle High Availability Services autostart is enabled.

                _combined_output_str = ""
                if _output:
                    _combined_output_str = ''.join(_str.strip().lower() for _str in _output)

                if _combined_output_str and CRS_AUTO_START_CHECK_CODE.lower() in _combined_output_str and CRS_AUTO_START_CHECK_STR.lower() in _combined_output_str:
                    self.mPatchLogInfo(f"crsctl config output : {str(_output)}")
                else:
                    _errors = _err.readlines()
                    if _errors:
                        self.mPatchLogWarn(f"crsctl config error output:\n {str(_errors)}")
                    if _output:
                        self.mPatchLogWarn(f"crsctl config output:\n {str(_output)}")
                    _ret = CRS_IS_DISABLED
        except Exception as e:
            _suggestion_msg = f"Unable to get CRS service auto startup details on {_domu_customer_hostname}. Error : {str(e)}"
            _ret = CRS_COMMAND_EXCEPTION_ENCOUNTERED
            self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)
            if self.mGetHandlerInstance().mGetTask() != TASK_PREREQ_CHECK:
                self.mPatchLogError(traceback.format_exc())
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()
            return _ret

    def mGetCellListForCRSHeartbeatValidation(self, aCellList):
        """
        Filters the cell list to validate CRS (Cluster Ready Services) heartbeat during Dom0 post-check.

        Parameters:
        aCellList (list): The list of cells to be filtered.

        Returns:
        tuple: A tuple containing two lists.
               - _cell_list_to_validate_for_crs (list): The list of cells to validate CRS.
               - _cells_with_gd_unknown_state (list): The list of cells with griddisk status as UNKNOWN.

        Notes:
        This method is used during Dom0 patching to determine which cells to validate CRS heartbeat.
        The cell list is considered for CRS validation if the griddisks on the cells are in ONLINE or SYNCING state.
        The cells with griddisk status as UNKNOWN are also considered for CRS validation if they are not already in the list of cells in use by ASM.
        """

        # if domU belongs to an ASM cluster based
        _cell_list_to_validate_for_crs, _cells_with_gd_unknown_state = self.mGetHandlerInstance().mGetCluPatchCheck().mVerifyCellsInUseByASM(
            aCellList)

        self.mPatchLogInfo(f"Cell List with griddisk status as UNKNOWN is {str(_cells_with_gd_unknown_state)}")

        # Remove duplicate
        _cells_with_gd_unknown_state = list(set(_cells_with_gd_unknown_state))
        _cell_list_to_validate_for_crs = list(set(_cell_list_to_validate_for_crs))
        _cells_with_gd_unknown_state = [x for x in _cells_with_gd_unknown_state if
                                        x not in _cell_list_to_validate_for_crs]
        self.mPatchLogInfo(
            f"Cell List with griddisk status as UNKNOWN, after filtering the cells in use by ASM is {str(_cells_with_gd_unknown_state)}")

        if _cells_with_gd_unknown_state and _cell_list_to_validate_for_crs:
            _cell_list_to_validate_for_crs.extend(_cells_with_gd_unknown_state)

        if _cell_list_to_validate_for_crs is None or len(_cell_list_to_validate_for_crs) < 1:
            self.mPatchLogInfo(
                "Cell List to validate CRS is empty. So no CRS validation will happen for Dom0 postcheck")
        else:
            self.mPatchLogInfo(
                f"Cell List to validate CRS for Dom0 postcheck is {json.dumps(_cell_list_to_validate_for_crs, indent=4)} ")

        return _cell_list_to_validate_for_crs, _cells_with_gd_unknown_state

    def mValidateDomUHeartbeat(self, aDomUList, aIsDiscardedNodeListCheck):
        """
         This check ensures the domUs have a heartbeat to all the cells.
         This check is not required for exaplice/monthly patching and is
         applicable to patch operations that involves a node reboot like
         patch and Rollback.
        """

        ret = PATCH_SUCCESS_EXIT_CODE
        _ret_crs_validate = PATCH_SUCCESS_EXIT_CODE
        _failed_heartbeat_domu_list = []
        _domu_cell_name = None
        _domus_accessible_from_exacloud_node = []
        _domus_not_accessible_from_exacloud_node = []
        _failed_crs_domu_list = []
        _vms_where_crs_is_disabled = []
        _list_of_vms_crs_auto_startup_enabled = []
        _alert_log_file = CELL_ALERT_LOG
        _is_hb_issue_present_in_cell_with_gd_unknown_state = False
        _heartbeat_timeout_in_seconds = self.mGetHandlerInstance().mGetExadataPatchGridHeartBeatTimeoutSec()
        _heartbeat_in_cell_alert_log_execution_timeout_in_seconds = self.mGetHandlerInstance().mGetHeartBeatDetailsInCellAlertLogExecutionTimeoutSec()

        '''
         This validation is performed based on checkValidateHeartbeatRequired 
         returns True or False. Skipped during exasplice where checkValidateHeartbeatRequired  
         returns false
        '''
        if not self.mGetHandlerInstance().mGetInfrapatchExecutionValidator().mCheckCondition('checkValidateHeartbeatRequired',
                                                                       isDiscardedNodeListCheck=aIsDiscardedNodeListCheck):
            self.mPatchLogInfo("DomU Heartbeat validations will be skipped.")
            return ret, _failed_heartbeat_domu_list, _domus_accessible_from_exacloud_node

        self.mPatchLogInfo("Entered into mValidateDomUHeartbeat method for CRS related checks")

        if len(aDomUList) > 0:
            '''
             In case of VMs not accessible from exacloud node,
             heartbeat validations are performed on cells to 
             validate for CRS services to be up and running on
             DomU.
            '''
            _cell = exaBoxNode(get_gcontext())
            try:
                _list_domus_Exascale_storage = self.mGetHandlerInstance().mGetDomuListByClusterStorageType(EXASCALE_CLUSTER_STORAGE_TYPE)

                _cell_list = self.mGetHandlerInstance().mGetCellList()
                _cell_list_to_validate_for_crs, _cells_with_gd_unknown_state = self.mGetCellListForCRSHeartbeatValidation(_cell_list)

                # for each domU, check if it has started clusterware heartbeat with all the cells
                for _domU_name in aDomUList:
                    # Heartbeat validations are performed using
                    # customer hostname.
                    _cust_hostname = _domU_name
                    _domU_name = (self.mGetHandlerInstance().mGetDomUCustomerNameforDomuNatHostName(_domU_name)).strip()
                    # bug 26678535: heart beat message in the cell 'alert.log' only
                    # contains the DOMU hostnames without the FQDN. So strip off
                    # the FQDN from the DOMU hostname before doing anything.
                    _domu_hostname_no_fqdn = _domU_name.split('.')[0]

                    # host names are cut to 32 chars on the cell alert logs
                    _32_char_domU_name = _domu_hostname_no_fqdn[:32]

                    # if domU belongs to an exascale cluster based, check EDV info
                    if _cust_hostname in _list_domus_Exascale_storage:
                        _total_time_taken_to_perform_edv_based_hb_checks = 0 
                        _ret, _total_time_taken_to_perform_edv_based_hb_checks = self.mCheckEDVInfoForHB(_domu_hostname_no_fqdn, _cell_list,
                                                       _heartbeat_timeout_in_seconds)
                        if not _ret:
                            _failed_heartbeat_domu_list.append(_domU_name)
                            self.mPatchLogError(f'Heartbeat validation failed for DomU (on Exascale): {_domU_name}')
                        continue

                        '''
                         A sufficient duration of 30 minutes has already been allocated to 
                         validate heartbeat entries in alert logs on Exascale environments. 
                         This timeframe should be adequate for all DB/CRS services on all VMs 
                         to start up and hence _heartbeat_timeout_in_seconds is reset to the
                         remaining time available so that the time taken to perform non-exascle
                         environments could be further optimised.


                         Additional buffer time of 500 seconds is added below to consider additional
                         time taken to perform connect/disconnect to cells, network delays, command
                         execution delays. Please see below case where exascale based HB check took
                         31minutes 40 seconds to return results.

                           2025-11-13 14:19:43,310 - dfltlog - INFO - 257585 - CrsHelper - Start validating every 10 seconds if heartbeat between DomU and CELL is established or CRS is up on Exascale with a timeout of 1800 seconds.
                           2025-11-13 14:19:43,438 - dfltlog - INFO - 257585 - CrsHelper - Checking heartbeat from domU [scaqan02dv0502] to cell [scaqan02celadm07.us.oracle.com] on Exascale
                           .
                           .
                           2025-11-13 14:51:23,296 - dfltlog - INFO - 257585 - CrsHelper - Checking heartbeat from domU [scaqan02dv0502] to cell [scaqan02celadm08.us.oracle.com] on Exascale
                           2025-11-13 14:51:33,618 - dfltlog - ERROR - 257585 - CrsHelper - Heartbeat validation failed for DomU (on Exascale): scaqan02dv0502.us.oracle.com
                        '''
                        _heartbeat_timeout_in_seconds = _heartbeat_timeout_in_seconds - _total_time_taken_to_perform_edv_based_hb_checks + 500

                    # Only check for heartbeat on cells that have griddisks in use by asm
                    for _cell_name in _cell_list_to_validate_for_crs:

                        _cell.mConnect(aHost=_cell_name)

                        self.mPatchLogInfo(f"Checking heartbeat from domU [{_domU_name}] to cell [{_cell_name}]")

                        # Get alert log details based on the heartbeat details.
                        _cmd_get_heartbeat_alert_log_file = f'grep -ai "Heartbeat with diskmon" {CELL_ALERT_LOG} | egrep -ai "started on|stopped on"| grep "{_32_char_domU_name}"'

                        # By default check for hearbeat details in alert.log
                        _alert_log_file_cmd = f"ls {CELL_ALERT_LOG}"
                        _i, _o, _e = _cell.mExecuteCmd(_alert_log_file_cmd)

                        '''
                         Check for file existence of alert.log. Iif the file itself
                         is missing, we might find stale entries in other rotated alert 
                         log files and might not provide desired or updated heartbeat entries 
                         and is not reliable.

                         Return error handling details in case of alert log file missing and skip
                         checking heartbeat details on the current cell node.
                        '''
                        self.mPatchLogInfo(f"Alert log details are as follows : {_alert_log_file}")
                        if int(_cell.mGetCmdExitStatus()) != 0:
                            ret = HEARTBEAT_FAILURE_ERROR
                            _suggestion_msg = f"Alert log missing for the cell : {_cell_name} and heartbeat validation will not be performed."
                            if _cell.mIsConnected():
                                _cell.mDisconnect()
                            return ret, _failed_heartbeat_domu_list, _domus_accessible_from_exacloud_node
                        else:
                            if _o:
                                _out = _o.readlines()
                                _alert_log_file = (_out[0]).strip()
                            # Get the alert log that has the heartbeat details.
                            _cell.mExecuteCmd(_cmd_get_heartbeat_alert_log_file, aTimeout = _heartbeat_in_cell_alert_log_execution_timeout_in_seconds)
                            _exit_status = _cell.mGetCmdExitStatus()
                            if int (_exit_status) == 124:
                                _failed_heartbeat_domu_list.append(_domU_name)
                                break
                            if int(_exit_status) != 0:
                                for _alert_log_extension_counter_value in range(0, 5):
                                    _cmd_get_heartbeat_alert_log_file_extension = f'grep -ai "Heartbeat with diskmon" {CELL_ALERT_LOG}.{_alert_log_extension_counter_value} | egrep -ai "started on|stopped on" | grep "{_32_char_domU_name}"'
                                    _cell.mExecuteCmd(_cmd_get_heartbeat_alert_log_file_extension, aTimeout = _heartbeat_in_cell_alert_log_execution_timeout_in_seconds)
                                    _exit_status_alert_log_file = _cell.mGetCmdExitStatus()
                                    if int (_exit_status) == 124:
                                        _failed_heartbeat_domu_list.append(_domU_name)
                                        break
                                    if int(_exit_status_alert_log_file) == 0:
                                        _alert_log_file = _alert_log_file + "." + str(
                                            _alert_log_extension_counter_value)
                                        self.mPatchLogInfo(
                                            f"Alert log file used to perform heartbeat validations : {_alert_log_file}.")
                                        break

                            """
                             When there is a successful heartbeat

                               [root@slcs27celadm04 ~]# grep -ai "Heartbeat with diskmon" $CELLTRACE/alert.log | egrep -ai "started on|stopped on" | grep slcs27dv0406m | tail -1 | grep "started"
                               Heartbeat with diskmon (pid 42448) started on slcs27dv0406m
                               [root@slcs27celadm04 ~]# echo $?
                               0
                               [root@slcs27celadm04 ~]#

                             When there is no heartbeat

                               [root@slcs27celadm04 ~]# grep -ai "Heartbeat with diskmon" $CELLTRACE/alert.log | egrep -ai "started on|stopped on" | grep slcs27dv0406m | tail -1 | grep -i "started"
                               [root@slcs27celadm04 ~]# echo $?
                               1
                               [root@slcs27celadm04 ~]#
                            """

                            self.mPatchLogInfo(f"Start validating every {HEARTBEAT_CHECK_INTERVAL_IN_SECONDS} seconds if heartbeat between DomU: [{_domU_name}] and CELL: [{_cell_name}] is established with a timeout of {_heartbeat_timeout_in_seconds} seconds.")
                            _cmd_check_heartbeat_started = f'grep -ai "Heartbeat with diskmon" {_alert_log_file} | egrep -ai "started on|stopped on" | grep "{_32_char_domU_name}" | tail -1 | grep "started"'
                            self.mPatchLogInfo(f"Cell heartbeat check command = {_cmd_check_heartbeat_started} ")
                            _checked_for_secs = 0
                            while _checked_for_secs <= _heartbeat_timeout_in_seconds:

                                # Check heartbeat on alert log files.
                                _cell.mExecuteCmd(_cmd_check_heartbeat_started)
                                if int(_cell.mGetCmdExitStatus()) == 0:
                                    self.mPatchLogInfo(
                                        f"Latest domU [{_domU_name}] heartbeat message found on cell [{_cell_name}]")
                                    if _cell.mIsConnected():
                                        _cell.mDisconnect()
                                    break

                                sleep(9)
                                _checked_for_secs += HEARTBEAT_CHECK_INTERVAL_IN_SECONDS
                            else:
                                # Heartbeat check failed so for the next iteration combination of cell/domu,
                                # no need to wait until self.mGetExadataPatchGridHeartBeatTimeoutSec()
                                _heartbeat_timeout_in_seconds = 1
                                _failed_heartbeat_domu_list.append(_domU_name)

                                if _cell_name in _cells_with_gd_unknown_state:
                                    _is_hb_issue_present_in_cell_with_gd_unknown_state = True

                                _domu_cell_name = f"({_domU_name}-{_cell_name})"
                                self.mPatchLogError(
                                    f"Heartbeat validation failed for DomU/Cell combination : {str(_domu_cell_name)}")
                                if _cell.mIsConnected():
                                    _cell.mDisconnect()

                if len(_failed_heartbeat_domu_list) > 0:
                    '''
                     Perform CRS validation on DomU in case of
                     passwdless ssh is setup between exacloud node
                     and Domu.
                    '''

                    # Remove the duplicate entries from the list
                    _failed_heartbeat_domu_list = list(set(_failed_heartbeat_domu_list))

                    self.mPatchLogInfo(
                        f"Heartbeat check failed on : {json.dumps(_failed_heartbeat_domu_list, indent=4)}")
                    '''
                     Modifying _failed_heartbeat_domu_list Customer hostname
                     to NAT hostname list.
                    '''
                    _failed_heartbeat_domu_list = self.mGetHandlerInstance().mGetDomUNatHostNamesforDomuCustomerHostNames(
                        _failed_heartbeat_domu_list)
                    if _is_hb_issue_present_in_cell_with_gd_unknown_state:
                        self.mPatchLogInfo("Heartbeat issue is seen in cell with grid disk with unknown state so no crs start will be performed.")
                    else:
                        _domus_accessible_from_exacloud_node, _domus_not_accessible_from_exacloud_node = self.mGetHandlerInstance().mGetReachableDomuList(_failed_heartbeat_domu_list)

                if len(_domus_accessible_from_exacloud_node) > 0:
                    '''
                     Remove domu from heartbeat failure list in 
                     case of DomUs reachable from exacloud.
                    '''
                    for _domu in _domus_accessible_from_exacloud_node:
                        _failed_heartbeat_domu_list.remove(_domu)

                    '''
                     CRS Auto startup checks are done using NAT
                     hostname as ssh is performed from exacloud
                     host to DomUs.
                    '''
                    _ret, _list_of_vms_crs_auto_startup_enabled = self.mReturnListofVMsWithCRSAutoStartupEnabled(
                        _domus_accessible_from_exacloud_node)
                    if _ret in [DOMU_INVALID_CRS_HOME, CRS_COMMAND_EXCEPTION_ENCOUNTERED]:
                        return _ret, _failed_heartbeat_domu_list, _domus_accessible_from_exacloud_node

                    '''
                     Perform CRS validations only on VMs where CRS
                     Auto startup is enabled. Validations are performed
                     using NAT hostnames.
                    '''
                    if len(_list_of_vms_crs_auto_startup_enabled) > 0:
                        _ret_crs_validate, _failed_crs_domu_list = self.mCheckAndStartupCRSDuringDom0Patching(
                            _list_of_vms_crs_auto_startup_enabled)
                        if len(_failed_crs_domu_list) > 0:
                            for _domu_crs_down in _failed_crs_domu_list:
                                _failed_heartbeat_domu_list.append(_domu_crs_down)
                    else:
                        _set_of_vms_crs_auto_startup_enabled = set(_list_of_vms_crs_auto_startup_enabled)
                        _vms_where_crs_is_disabled = [_vm_list for _vm_list in _domus_accessible_from_exacloud_node if
                                                      _vm_list not in _set_of_vms_crs_auto_startup_enabled]

                    if len(_vms_where_crs_is_disabled) > 0:
                        self.mPatchLogWarn(
                            f"List of VMs where CRS auto startup is disabled : {json.dumps(_vms_where_crs_is_disabled, indent=4)}. CRS validation and startup will be skipped. Although VMs are up and running, CRS startup is disabled in this scenario.")

                if len(_domus_not_accessible_from_exacloud_node) > 0:
                    self.mPatchLogError(
                        f"CRS restart will not be tried on these DomUs : {str(_domus_not_accessible_from_exacloud_node)}, since they are not accessible from exacloud node.")

            except Exception as e:
                self.mPatchLogError(f"Error while validating heartbeat on cells. \n\n {str(e)}")
                self.mPatchLogTrace(traceback.format_exc())
                ret = DOMU_HEARTBEAT_VALIDATION_EXCEPTION_ENCOUNTERED

            finally:
                if len(_failed_heartbeat_domu_list) > 0:
                    _failed_heartbeat_domu_list_customer_nat_hostnames = self.mGetHandlerInstance().mReturnBothDomUNATCustomerHostNames(
                        _failed_heartbeat_domu_list)
                    ret = DOMU_HEARTBEAT_NOT_RECEIVED
                    _suggestion_msg =""
                    if len(_domus_not_accessible_from_exacloud_node) > 0:
                        _domus_not_accessible_from_exacloud_node_nat_customer_hostname = self.mGetHandlerInstance().mReturnBothDomUNATCustomerHostNames(
                            _domus_not_accessible_from_exacloud_node)
                        _suggestion_msg = f"CRS restart was skipped for DomUs: {str(_domus_not_accessible_from_exacloud_node_nat_customer_hostname)} due to inaccessibility from exacloud node. Additionally, "
                    _suggestion_msg += f"CRS did not startup on {str(_failed_heartbeat_domu_list_customer_nat_hostnames)} even after timeout of {str(_heartbeat_timeout_in_seconds)} secs."
                    '''
                     CRS error details takes higher precendence than 
                     that of the heartbeat error details. 

                     _failed_heartbeat_domu_list contains failed VM list both based on 
                     CRS check as well as heartbeat validations.
                    '''
                    if len(_failed_crs_domu_list) > 0:
                        ret = _ret_crs_validate
                        _suggestion_msg = f"POST-PATCH - Unable to startup CRS on the DomU list : {str(_failed_heartbeat_domu_list_customer_nat_hostnames)}"
                    self.mGetHandlerInstance().mAddError(ret, _suggestion_msg)

                if _cell.mIsConnected():
                    _cell.mDisconnect()

        return ret, _failed_heartbeat_domu_list, _domus_accessible_from_exacloud_node

    def mCheckandRestartCRSonDomU(self, aDomU):
        """
         Checks the CRS status to be down and retry starting up CRS services for a couple of iterations.

         Returns
            - PATCH_SUCCESS_EXIT_CODE in case of CRS services already running
              or were able to startup CRS services on consequent retries.
            - DOMU_CRS_SERVICES_DOWN in case of CRS service down and unable to
              startup.

         This method is used by both dom0 and domu patching. For dom0, crs operations are done
         using as opc user if exists and as root user during domu patching
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _counter_to_display_iteration_count = 0

        _node = exaBoxNode(get_gcontext())
        _domu_customer_hostname = None
        _output = []
        _errors = []
        try:
            _domu_customer_hostname = self.mGetHandlerInstance().mGetDomUCustomerNameforDomuNatHostName(aDomU)

            if self.mGetHandlerInstance().mGetCurrentTargetType() == PATCH_DOM0:
                _user_to_connect_with = self.mGetHandlerInstance().mGetUserDetailsBasedOnDomUhostname(aDomU)
                if _user_to_connect_with:
                    _node.mSetUser(_user_to_connect_with)
            _node.mSetMaxRetries(self.mGetHandlerInstance().mGetMaxNumberofSshRetries())
            _node.mConnect(aHost=aDomU)

            # Check if CRS auto startup is disabled on DomU during Dom0 Patching.
            _ret = self.mCheckCrsIsEnabled(aDomU)
            if _ret in [DOMU_INVALID_CRS_HOME, CRS_COMMAND_EXCEPTION_ENCOUNTERED]:
                if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                    self.mPatchLogWarn(
                        f"Error encountered while validating crs command path and CRS checks cannot be performed during precheck on DomU : {str(aDomU)}. During prechecks, these errors are only logged as warnings in thread logs.")
                else:
                    self.mPatchLogError(
                        f"Error encountered while validating crs command path and CRS checks and further infra patch operation cannot proceed on DomU : {str(aDomU)}.")
                return _ret

            elif _ret == PATCH_SUCCESS_EXIT_CODE:
                """

                [root@slcs27dv0305m ~]#  cat /etc/oratab|egrep -i 'grid|ASM' |grep -v '^#'|cut -d ':' -f2
                /u01/app/19.0.0.0/grida

                [opc@slcs27dv0305m ~]$ sudo $(cat /etc/oratab|egrep -i 'grid|ASM' |grep -v '^#'|cut -d ':' -f2)/bin/crsctl check crs
                CRS-4638: Oracle High Availability Services is online
                CRS-4537: Cluster Ready Services is online
                CRS-4529: Cluster Synchronization Services is online
                CRS-4533: Event Manager is online
                [opc@slcs27dv0305m ~]$

                """
                _ret, _cmd_check_crs = self.mGenCrsctlCmd(_node, "check crs", _domu_customer_hostname)
                if _ret == DOMU_INVALID_CRS_HOME:
                    if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                        self.mPatchLogWarn(
                            f"Error encountered while validating crs command path and CRS checks cannot be performed during precheck on DomU : {str(_domu_customer_hostname)}. During prechecks, these errors are only logged as warnings in thread logs.")
                    else:
                        self.mPatchLogError(
                            f"Error encountered while validating crs command path and CRS checks and further infra patch operation cannot proceed on DomU : {str(_domu_customer_hostname)}.")
                    return _ret

                elif _ret == PATCH_SUCCESS_EXIT_CODE:
                    _ret, _output = self.mRunCrsctlCheckCrsCommand(_node, _domu_customer_hostname, _cmd_check_crs)
                    if _ret == PATCH_SUCCESS_EXIT_CODE:
                        self.mPatchLogInfo(f"CRS is up and running on {_domu_customer_hostname}.")
                    else:
                        if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                            self.mPatchLogWarn(
                                f"CRS is not running on {_domu_customer_hostname}. Skipping CRS services startup for {self.mGetHandlerInstance().mGetCurrentTargetType()} {TASK_PREREQ_CHECK}. During prechecks, these errors are only logged as warnings in thread logs.")
                            return _ret
                        
                        _ret, _crsinit_output = self.mCheckCrsInitResourcesonDomU(aDomU, _node)
                        if _ret == PATCH_SUCCESS_EXIT_CODE:
                            if _crsinit_output:
                                self.mPatchLogInfo(f"crs Init resources status on {_domu_customer_hostname}: \n  {_crsinit_output}")
                        
                        #The -f (force) option is used only when CRS is not running on the domu and we forcefully stop the crs before trying to bring it up again
                        _stop_args = "stop crs -f"
                        _ret, _cmd_crs_stop = self.mGenCrsctlCmd(_node, _stop_args, _domu_customer_hostname)
                        if _ret == PATCH_SUCCESS_EXIT_CODE:
                            self.mPatchLogInfo(f"Stopping CRS on {_domu_customer_hostname}")
                            _in, _out, _err = _node.mExecuteCmd(_cmd_crs_stop)
                            if _out:
                                self.mPatchLogInfo(f"CRS is stopped on {_domu_customer_hostname}")
                            else:                            
                                if _err:
                                    _errors = _err.readlines()
                                self.mPatchLogWarn(f"Could not stop CRS on {_domu_customer_hostname} Error: {str(_errors)}")

                        _ret = self.mStartupCrsOnDomU(aDomU, _node)
                        if _ret != PATCH_SUCCESS_EXIT_CODE:
                            _retry_check_for_crs_startup_counter = RETRY_CRS_STARTUP_CHECK_MAX_COUNTER_VALUE
                            while _retry_check_for_crs_startup_counter > 0:
                                self.mPatchLogInfo(
                                    f"Performing CRS services startup for iteration - {_counter_to_display_iteration_count:d}, Maximum number of iterations - {_retry_check_for_crs_startup_counter:d}")
                                sleep(RETRY_CRS_SERVICES_SLEEP_IN_SECONDS)
                                _counter_to_display_iteration_count += 1
                                _ret = self.mStartupCrsOnDomU(aDomU, _node)
                                if _ret != PATCH_SUCCESS_EXIT_CODE:
                                    self.mPatchLogWarn(
                                        f"Unable to startup CRS in iteration - {_counter_to_display_iteration_count:d}. Polled for {RETRY_CRS_SERVICES_SLEEP_IN_SECONDS:d} seconds before retrying to startup CRS on {_domu_customer_hostname}.")
                                    _retry_check_for_crs_startup_counter -= 1
                                else:
                                    self.mPatchLogInfo(
                                        f"CRS startup succeeded after {_counter_to_display_iteration_count:d} retries")
                                    break

                        if _ret != PATCH_SUCCESS_EXIT_CODE and _counter_to_display_iteration_count == 0:
                            self.mPatchLogError(
                                f"Unable to startup CRS on {_domu_customer_hostname} even after {_counter_to_display_iteration_count:d} iterations. Need manual intervention and further debugging.")
            elif _ret == CRS_IS_DISABLED:
                '''
                 This case is encountered only in case of domu patching
                 as self.mGetCustomizedDomUList() is passed.

                 In case of dom0 patching, only the filtered list
                 where VMs CRS auto startup is enabled are passed as input.
                '''
                _suggestion_msg = f'CRS auto startup is disabled on domu : {str(_domu_customer_hostname)}, heartbeat validations failed and cannot startup CRS in this case.'
                if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                    self.mPatchLogWarn(f"{_suggestion_msg}")
                else:
                    self.mPatchLogError(f"{_suggestion_msg}")

        except Exception as e:
            _suggestion_msg = f'Failed to get crsctl check crs output from domu : {_domu_customer_hostname}. Error : {str(e)}'
            if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                self.mPatchLogWarn(f"{_suggestion_msg}")
            else:
                _ret = DOMU_CRS_VALIDATION_EXCEPTION_ENCOUNTERED
                self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)
                self.mPatchLogTrace(traceback.format_exc())
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()
            return _ret

    def mStartupCrsOnDomU(self, aDomU, aNode):
        """
        Startup CRS services if it is down for a couple of iterations.

        Returns
            - PATCH_SUCCESS_EXIT_CODE in case of successfully able to
              startup CRS services on DomU
            - DOMU_CRS_SERVICES_DOWN in case of unable to startup CRS
              on VM.
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _cmd_crs_startup = ""
        _cmd_check_crs = ""
        _output = []
        _errors = []
        _domu_customer_hostname = None
        try:
            _domu_customer_hostname = self.mGetHandlerInstance().mGetDomUCustomerNameforDomuNatHostName(aDomU)
            '''
             Sample snippet of a case where error can occur when CRS is started up.

              /u01/app/19.0.0.0/grid/bin/crsctl start crs
              CRS-4640: Oracle High Availability Services is already active
              CRS-4000: Command Start failed, or completed with errors.
            '''

            _args = "start crs"
            _ret, _cmd_crs_startup = self.mGenCrsctlCmd(aNode, _args, _domu_customer_hostname)
            if _ret == DOMU_INVALID_CRS_HOME:
                if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                    self.mPatchLogWarn(
                        f"Error encountered while validating crs command path and CRS checks cannot be performed during precheck on DomU : {str(_domu_customer_hostname)}.. During prechecks, these errors are only logged as warnings in thread logs.")
                else:
                    self.mPatchLogError(
                        f"Error encountered while validating crs command path and CRS checks and further infra patch operation cannot proceed on DomU : {str(_domu_customer_hostname)}.")
                return _ret

            if _ret == PATCH_SUCCESS_EXIT_CODE:
                _crs_start_time = time()
                _in, _out, _err = aNode.mExecuteCmd(_cmd_crs_startup)
                _crs_end_time = time()
                _crs_execution_time = _crs_end_time - _crs_start_time
                self.mPatchLogInfo(
                        f"Execution time for 'crsctl start crs' on {_domu_customer_hostname} : {_crs_execution_time:.2f} seconds")
                sleep(WAIT_FOR_CRSCTL_START_COMMAND_TO_COMPLETE_IN_SECONDS)
                if _out:
                    _output = _out.readlines()

                """
                  crsctl start cluster sample output :
                  root@test-host-slcs27 opc]#  /u01/app/19.0.0.0/grid/bin/crsctl start cluster
                  CRS-2672: Attempting to start 'ora.cssdmonitor' on 'test-host-slcs27'
                  CRS-2672: Attempting to start 'ora.evmd' on 'test-host-slcs27'
                  CRS-2676: Start of 'ora.cssdmonitor' on 'test-host-slcs27' succeeded
                  CRS-2672: Attempting to start 'ora.cssd' on 'test-host-slcs27'
                  CRS-2672: Attempting to start 'ora.diskmon' on 'test-host-slcs27'
                  CRS-2676: Start of 'ora.evmd' on 'test-host-slcs27' succeeded
                  CRS-2676: Start of 'ora.diskmon' on 'test-host-slcs27' succeeded
                  CRS-2676: Start of 'ora.cssd' on 'test-host-slcs27' succeeded
                  CRS-2672: Attempting to start 'ora.ctssd' on 'test-host-slcs27'
                  CRS-2676: Start of 'ora.ctssd' on 'test-host-slcs27' succeeded
                  CRS-2672: Attempting to start 'ora.asm' on 'test-host-slcs27'
                  CRS-2676: Start of 'ora.asm' on 'test-host-slcs27' succeeded
                  CRS-2672: Attempting to start 'ora.storage' on 'test-host-slcs27'
                  CRS-2676: Start of 'ora.storage' on 'test-host-slcs27' succeeded
                  CRS-2672: Attempting to start 'ora.crsd' on 'test-host-slcs27'
                  CRS-2676: Start of 'ora.crsd' on 'test-host-slcs27' succeeded
                  [root@test-host-slcs27 opc]#
                """
                if len(_output) > 0:
                    # note that if we are here, it means the previous call was successful, so no additional check
                    _ret, _cmd_check_crs = self.mGenCrsctlCmd(aNode, "check crs", _domu_customer_hostname)
                    if _ret == DOMU_INVALID_CRS_HOME:
                        if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                            self.mPatchLogWarn(
                                f"Error encountered while validating crs command path and CRS checks cannot be performed during precheck on DomU : {str(_domu_customer_hostname)}.. During prechecks, these errors are only logged as warnings in thread logs.")
                        else:
                            self.mPatchLogError(
                                f"Error encountered while validating crs command path and CRS checks and further infra patch operation cannot proceed on DomU : {str(_domu_customer_hostname)}.")
                        return _ret

                    _ret, _ = self.mRunCrsctlCheckCrsCommand(aNode, _domu_customer_hostname, _cmd_check_crs)
                    if _ret == PATCH_SUCCESS_EXIT_CODE:
                        if _output:
                            self.mPatchLogInfo(
                                f"CRS is up and running on {_domu_customer_hostname}.\n Output : {str(_output)}")
                            _, _crsinit_output = self.mCheckCrsInitResourcesonDomU(aDomU, aNode)
                            if _crsinit_output:
                                self.mPatchLogInfo(f"crs Init resources status on {_domu_customer_hostname}: \n  {_crsinit_output}")
                    else:                      
                        if _err:
                            _errors = _err.readlines()
                        self.mPatchLogWarn(f"CRS is down on {_domu_customer_hostname}.\n Output : {str(_errors)}")
        except Exception as e:
            _suggestion_msg = f'Failed to startup crs on domu : {_domu_customer_hostname}. Error : {str(e)}'
            _ret = DOMU_CRS_VALIDATION_EXCEPTION_ENCOUNTERED
            self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            return _ret

    def mRunCrsctlCheckCrsCommand(self, aNode, aDomUCustomerHostname, aCheckCrsCommand):
        """
         This method is used to validate CRS services to be
         up and running. it is called in multiple references
         and hence separated from mCheckandRestartCRSonDomU()

         Return PATCH_SUCCESS_EXIT_CODE in case of all CRS services up and running.
                DOMU_CRS_SERVICES_DOWN otherwise.
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _output = []
        _errors = []
        _crs_started_up = True
        _suggestion_msg = None
        try:
            self.mPatchLogInfo(f"Executing the command {aCheckCrsCommand}.")
            _check_crs_start_time = time()
            _in, _out, _err = aNode.mExecuteCmd(aCheckCrsCommand)
            _check_crs_end_time = time()
            _check_crs_execution_time = _check_crs_end_time - _check_crs_start_time
            self.mPatchLogInfo(
                f"Execution time for 'crsctl check crs' on {aDomUCustomerHostname} : {_check_crs_execution_time:.2f} seconds")
            '''
             Expected "crsctl check crs" command output 

             CRS-4638: Oracle High Availability Services is online
             CRS-4537: Cluster Ready Services is online
             CRS-4529: Cluster Synchronization Services is online
             CRS-4533: Event Manager is online
            '''
            if _out:
                _output = _out.readlines()
            if _output:
                for _line in _output:
                    _line = _line.strip()
                    if "is online" not in _line:
                        self.mPatchLogError(f"crs checks failed. crs check cluster output: {_line}")
                        _crs_started_up = False
                        break
            else:
                if _err:
                    _errors = _err.readlines()
                if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                    self.mPatchLogWarn(
                        f"CRS check output: {str(_errors)}. During prechecks, these errors are only logged as warnings in thread logs.")
                else:
                    self.mPatchLogError(f"CRS check output:\n\n : {str(_errors)}")
                    _crs_started_up = False
        except Exception as e:
            if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                self.mPatchLogWarn(
                    f"Unable to check crs on {aDomUCustomerHostname}. Error : {str(e)}. During prechecks, these errors are only logged as warnings in thread logs.")
            else:
                self.mPatchLogError(f"Unable to check crs on {aDomUCustomerHostname}. Error : {str(e)}")
                _crs_started_up = False
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            if not _crs_started_up:
                _ret = DOMU_CRS_SERVICES_DOWN
                self.mPatchLogWarn(
                    f"Unable to startup CRS services during infra patch operations on Guest VM : {aDomUCustomerHostname}. Validate CRS logs on the DomU : {aDomUCustomerHostname} for further debugging.")
            return _ret, _output

    def mCheckCrsInitResourcesonDomU(self, aDomU, aNode):

        """
           - check if the crs startup initiated 
           - check the existing status of the crs init daemons
           - crsctl status resource -init sample output
            
            NAME=ora.asm
            TYPE=ora.asm.type
            TARGET=ONLINE
            STATE=ONLINE on scaqan10dv0708
            
            NAME=ora.crf
            TYPE=ora.crf.type
            TARGET=ONLINE
            STATE=ONLINE on scaqan10dv0708
            
            NAME=ora.crsd
            TYPE=ora.crs.type
            TARGET=ONLINE
            STATE=ONLINE on scaqan10dv0708
            ....         
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _domu_customer_hostname = None
        _output = ""
        _output_lines = []
        _errors = []
        _names = []
        _types = []
        _targets = []
        _states = []


        try:
            _domu_customer_hostname = self.mGetHandlerInstance().mGetDomUCustomerNameforDomuNatHostName(aDomU)
            _stat_args = "status resource -init"
            _ret, _cmd_crs_stat = self.mGenCrsctlCmd(aNode, _stat_args, _domu_customer_hostname)

            if _ret == DOMU_INVALID_CRS_HOME:
                if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                    self.mPatchLogWarn(
                        f"Error encountered while validating crs command path and CRS checks cannot be performed during precheck on DomU : {str(_domu_customer_hostname)}. During prechecks, these errors are only logged as warnings in thread logs.")
                else:
                    self.mPatchLogError(
                        f"Error encountered while validating crs command path and CRS checks and further infra patch operation cannot proceed on DomU : {str(_domu_customer_hostname)}.")
                return _ret, _output

            elif _ret == PATCH_SUCCESS_EXIT_CODE:
                _in, _out, _err = aNode.mExecuteCmd(_cmd_crs_stat)
                if _out:
                    _output_lines = ''.join(_out.readlines())
                if _output_lines and "Could not contact Oracle High Availability Services" not in _output_lines:                    
                    _crs_init_resources = [_resource.strip() for _resource in _output_lines.split('NAME=') if _resource.strip()]
                    # Processing each resoure section
                    for _resource in _crs_init_resources:
                        _resource = "NAME=" + _resource
                        for line in _resource.splitlines():
                            if line.startswith("NAME="):
                                _names.append(line.split('=', 1)[1].strip())
                            elif line.startswith("TYPE="):
                                _types.append(line.split('=', 1)[1].strip())
                            elif line.startswith("TARGET="):
                                _targets.append(line.split('=', 1)[1].strip())
                            elif line.startswith("STATE="):
                                _states.append(line.split('=', 1)[1].strip())

                    # Find maximum length of columns for formatting purposes
                    _max_name_len = max(len(str(_name)) for _name in _names)
                    _max_type_len = max(len(str(_type)) for _type in _types)
                    _max_target_len = max(len(str(_target)) for _target in _targets)
                    _max_state_len = max(len(str(_state)) for _state in _states)

                    # Print header row
                    _output += f"{'Name'.ljust(_max_name_len)} | {'Type'.ljust(_max_type_len)} | {'Target'.ljust(_max_target_len)} | {'Current State'.ljust(_max_state_len)}\n"
                    _output += '-' * (_max_name_len + _max_type_len + _max_target_len + _max_state_len + 12) + "\n"

                    # Print rows
                    for _name, _type, _target, _state in zip(_names, _types, _targets, _states):
                        _output += f"{_name.ljust(_max_name_len)} | {_type.ljust(_max_type_len)} | {_target.ljust(_max_target_len)} | {_state.ljust(_max_state_len)}\n"                
                else:
                    if _err:
                        _errors = _err.readlines()                       
                    self.mPatchLogWarn(f"Unable to check crs Init deamons status on {_domu_customer_hostname}. Error : {str(_errors)}")
        except Exception as e:
            _ret = CRS_COMMAND_EXCEPTION_ENCOUNTERED
            self.mPatchLogWarn(f"Unable to check crs Init deamons status on {_domu_customer_hostname}. Error : {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            return _ret, _output

    def mCheckAndStartupCRSDuringDom0Patching(self, aDomUList):
        """
         This method validates for CRS services to be up and running
         post dom0 patching on all the DomUs currently running on
         the Dom0 patched.

         return - PATCH_SUCCESS_EXIT_CODE if the CRS services on all
                  DomUs under the Dom0 patched are up and running or
                  started up successfully.
                - DOMU_CRS_SERVICES_DOWN if the CRS services could not
                  be started up post patching even during retries.
        """
        _crs_did_not_start_up_on_vm_list = []
        _ret = PATCH_SUCCESS_EXIT_CODE
        try:
            def _start_crs_on_domu(_remote_node, aStatus):
                _domu_customer_hostname = self.mGetHandlerInstance().mGetDomUCustomerNameforDomuNatHostName(_remote_node)
                _ret = self.mCheckandRestartCRSonDomU(_remote_node)
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    if self.mGetHandlerInstance().mGetTask() != TASK_PREREQ_CHECK:
                        aStatus.append(
                            {'domu': _domu_customer_hostname, 'status': 'failed', 'errorcode': DOMU_CRS_SERVICES_DOWN})
                        _suggestion_msg = f"Unable to startup CRS on DomU : ({_domu_customer_hostname})."
                        self.mGetHandlerInstance().mAddError(DOMU_CRS_SERVICES_DOWN, _suggestion_msg)
                    self.mPatchLogError(f"CRS did not startup on DomU : {_domu_customer_hostname} running on Dom0")

            # End of _start_crs_on_domu sub method

            """
             Parallelize execution on all target nodes. In case
             of Dom0 patching, CRS services are required to be 
             started up in parallel on all DomUs running on the
             current Dom0.
            """
            _plist = ProcessManager()
            _rc_status = _plist.mGetManager().list()

            for _remote_node in aDomUList:
                _p = ProcessStructure(_start_crs_on_domu, [_remote_node, _rc_status], _remote_node)

                '''
                 Timeout parameter configurable in Infrapatching.conf
                 Currently it is set to 60 minutes
                '''
                _p.mSetMaxExecutionTime(self.mGetHandlerInstance().mGetStartupCrsonDomUExecutionTimeoutInSeconds())

                _p.mSetJoinTimeout(PARALLEL_OPERATION_CRS_TIMEOUT_IN_SECONDS)
                _p.mSetLogTimeoutFx(self.mPatchLogWarn)
                _plist.mStartAppend(_p)

            _plist.mJoinProcess()

            if _plist.mGetStatus() == "killed":
                _crs_did_not_start_up_on_vm_list = self.mGetHandlerInstance().mReturnBothDomUNATCustomerHostNames(aDomUList)
                _suggestion_msg = f'Timeout occurred and threads are terminated while validating CRS services on the list of Nodes : {str(_crs_did_not_start_up_on_vm_list)}.'
                if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                    self.mPatchLogWarn(_suggestion_msg)
                else:
                    _ret = DOMU_CRS_SERVICES_DOWN
                    self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)
                return _ret, _crs_did_not_start_up_on_vm_list

            # validate the return codes
            for _rc_details in _rc_status:
                if _rc_details['status'] == "failed":
                    if self.mGetHandlerInstance().mGetTask() != TASK_PREREQ_CHECK:
                        self.mPatchLogError("Unable to startup CRS on DomU during dom0 patching.")
                        _crs_did_not_start_up_on_vm_list.append(_rc_details['domu'])
                        _ret = _rc_details['errorcode']
        except Exception as e:
            _crs_did_not_start_up_on_vm_list = self.mGetHandlerInstance().mReturnBothDomUNATCustomerHostNames(aDomUList)
            _suggestion_msg = "Unable to startup CRS on DomU list : %s. Error : %s" % (
            str(_crs_did_not_start_up_on_vm_list), str(e))
            if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                self.mPatchLogWarn(_suggestion_msg)
            else:
                _ret = DOMU_CRS_SERVICES_DOWN
                self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)
            self.mPatchLogError(traceback.format_exc())
        finally:
            return _ret, _crs_did_not_start_up_on_vm_list

    def mReturnListofVMsWithCRSAutoStartupEnabled(self, aListofVMs):
        """
         Note : This is called only from dom0handler

         This method returns the list of VMs where auto CRS startup
         is enabled based on the VM list passed from ecra metadata
         as input.

         Return - List of VMs with CRS auto startup enabled.
                - None if CRS auto startup is disabled on all
                  VMs on the current Dom0. In this case, CRS
                  validations for the VMs running on the current
                  Dom0 will be skipped.
        """
        _list_of_vms_crs_auto_startup_enabled = []
        _ret = PATCH_SUCCESS_EXIT_CODE
        for _domu in aListofVMs:
            _ret = self.mCheckCrsIsEnabled(_domu)
            if _ret in [ DOMU_INVALID_CRS_HOME, CRS_COMMAND_EXCEPTION_ENCOUNTERED ]:
                if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                    self.mPatchLogWarn(
                        f"Error encountered while validating crs command path and CRS checks cannot be performed during precheck on DomU : {str(_domu)}. During prechecks, these errors are only logged as warnings in thread logs.")
                else:
                    self.mPatchLogError(
                        f"Error encountered while validating crs command path and CRS checks and further infra patch operation cannot proceed on DomU : {str(_domu)}.")
            elif _ret == PATCH_SUCCESS_EXIT_CODE:
                _list_of_vms_crs_auto_startup_enabled.append(_domu)
            elif _ret == CRS_IS_DISABLED:
                self.mPatchLogWarn(
                    f"Auto startup of CRS is disabled on {_domu}, CRS check and startup will be skipped.")

        return _ret, _list_of_vms_crs_auto_startup_enabled

    def mCheckandRestartCRSonAllDomUWithinCluster(self, aListOfEluNodes=[]):
        """
         This method performs cluster wide CRS check on a
         given list of DomUs belonging to a cluster and
         is applicable only for Domu specific operation like
         precheck , patch and rollback

          [root@scaqan04dv0201 ~]# cat /etc/oratab|grep grid|grep -v '^#'|grep -i asm|cut -d ':' -f2
          /u01/app/19.0.0.0/grid

          [root@scaqan04dv0201 ~]# /u01/app/19.0.0.0/grid/bin/crsctl config crs
          CRS-4622: Oracle High Availability Services autostart is enabled.

          [root@scaqan04dv0201 ~]# /u01/app/19.0.0.0/grid/bin/crsctl check crs
          CRS-4638: Oracle High Availability Services is online
          CRS-4537: Cluster Ready Services is online
          CRS-4529: Cluster Synchronization Services is online
          CRS-4533: Event Manager is online

          return PATCH_SUCCESS_EXIT_CODE in case of CRS validations successful on all VMs.
          else
             return : DOMU_CRS_SERVICES_DOWN
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _list_of_vms_where_crs_did_not_start = []
        _suggestion_msg = None
        _count_of_vms_where_auto_startup_is_enabled = 0
        _single_node_name = None
        _list_of_vms_where_auto_startup_is_disabled = []

        def _validate_crs_services(_domu, aStatus):
            _ret = self.mCheckandRestartCRSonDomU(_domu)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                aStatus.append({'domu': _domu, 'ret': _ret})

        #
        # Parallel Execution of check and addition of keys
        #
        _return_msg = None
        _plist = ProcessManager()
        _rc_status = _plist.mGetManager().list()
        _single_node_name = None

        # Here mGetCustomizedDomUList() provides the list of all
        # the vms belonging only to that cluster where patching is
        # required to be performed.
        _crs_check_node_list = self.mGetHandlerInstance().mGetCustomizedDomUList()[:]
        if len(aListOfEluNodes) > 0:
            _crs_check_node_list = aListOfEluNodes

        for _domu in _crs_check_node_list:
            _p = ProcessStructure(_validate_crs_services, [_domu, _rc_status])
            _p.mSetMaxExecutionTime(30 * 60)  # 30 minutes timeout
            _p.mSetJoinTimeout(30)  #30 seconds
            _p.mSetLogTimeoutFx(self.mPatchLogInfo)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()
        if _plist.mGetStatus() == "killed":
            _ret = DOMU_CRS_SERVICES_DOWN
            _suggestion_msg = f'Timeout occurred and threads are terminated while checking for CRS services on the VM list : {str(_crs_check_node_list)}'
            self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)
            return _ret

        for _rc_details in _rc_status:
            if _rc_details['ret'] != PATCH_SUCCESS_EXIT_CODE:
                if _rc_details['ret'] == CRS_IS_DISABLED:
                    _list_of_vms_where_auto_startup_is_disabled.append(_rc_details['domu'])
                else:
                    _list_of_vms_where_crs_did_not_start.append(_rc_details['domu'])

        '''
          VMs where auto startup was disabled must not be considered
          for performing cluster wide CRS validations during domu patching.
        '''
        if len(_list_of_vms_where_auto_startup_is_disabled) > 0:
            self.mPatchLogInfo("*** Note that CRS validations are not performed in case of CRS auto startup is disabled on VM and such VMs will not be eligible to validate CRS high availablity ***")
            self.mPatchLogInfo(
                f"List of VMs where CRS auto startup is disabled : {json.dumps(_list_of_vms_where_auto_startup_is_disabled, indent=4)}")

        _count_of_vms_where_auto_startup_is_enabled = int(len(_crs_check_node_list)) - int(len(_list_of_vms_where_auto_startup_is_disabled))
        '''
         In case of a single vm upgrade, crs must be up and running 
         on that VM where auto startup is enabled to cover the
         service degradation scenario. HA will not be applicable
         in this case.

         This includes both include node list scenario where
         one DomU will be patched one node at a time or as 
         part of single VM cluster setup. 
        '''
        if (self.mGetHandlerInstance().mGetCustomizedDomUList() and len(self.mGetHandlerInstance().mGetCustomizedDomUList()) == 1) or (aListOfEluNodes and len(aListOfEluNodes) == 1):
            if int(_count_of_vms_where_auto_startup_is_enabled) == 1 and len(_list_of_vms_where_crs_did_not_start) < 0:
                _suggestion_msg = f"CRS services were supposed to be running on the current : {str(_list_of_vms_where_crs_did_not_start)} VM in case of single node VM patching is performed and is currently down."
                if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                    self.mPatchLogWarn(_suggestion_msg)
                else:
                    _ret = DOMU_CRS_SERVICES_DOWN
                    self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)
        elif ((_count_of_vms_where_auto_startup_is_enabled - int(len(_list_of_vms_where_crs_did_not_start))) < 2):
            '''
             In case of qtr rack and CRS auto startup is disabled 
             on one of the VMs. CRS HA is not not maintained and 
             Infra patching will fail and this case, list of VMs
             where auto startup is disabled must br printed.
            '''
            if len(_list_of_vms_where_crs_did_not_start) > 0:
                _suggestion_msg = f"CRS services were supposed to be running on at least 2 VMs.It is currently down on {str(_list_of_vms_where_crs_did_not_start)} for the current cluster."
            elif len(_list_of_vms_where_auto_startup_is_disabled) > 0:
                _suggestion_msg = f"CRS services were supposed to be running on at least 2 VMs.CRS auto startup is currently disabled on {str(_list_of_vms_where_auto_startup_is_disabled)} for the current cluster."
            self.mPatchLogError(_suggestion_msg)
            _ret = DOMU_CRS_SERVICES_DOWN
            self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)
        else:
            if len(_list_of_vms_where_crs_did_not_start) > 0:
                self.mPatchLogWarn(
                    f"Although CRS is down on few VMs :{str(_list_of_vms_where_crs_did_not_start)} belonging to the current cluster, high availability is not impacted as CRS is running on at least 2 VMs.")
        return _ret

    def mValidateRDSPingOnDomuNodes(self, aHBCheckFailedDomUList, aConnectibleDomUList):
        """
        This method is going to execute netchk command on the VM list passed.
        With netchk, vm to vm and vm to cell connectivity over rds is evaluated.

        For success case, netchk command output shows like below
                [opc@celts-2ofzi1 ~]$ sudo /opt/oracle/dcs/exacd_netchk/netchk  --configfile=/tmp/exacd_netchk.json
                ---------------------------------------------
                Diag Tool - NetChk (version: 20230515)

                Time: Wed Nov 15 06:07:58 UTC 2023
                Command line: /opt/oracle/dcs/exacd_netchk/exacd_netchk.py --configfile=/tmp/exacd_netchk.json
                Image version: 22.1.7.0.0.230113
                ---------------------------------------------
                Diagnosis Results:
                - [DIAG-VM-NETWORK-004] Validate VM to VM and cell connectivity over RDS ...................... PASSED

                Summary:
                100% (1 out of 1) passed
                [opc@celts-2ofzi1 ~]$

        For failure case, netchk command output shows like below

                [opc@celts-2ofzi1 ~]$ sudo /opt/oracle/dcs/exacd_netchk/netchk  --configfile=/tmp/exacd_netchk.json
                ---------------------------------------------
                Diag Tool - NetChk (version: 20230515)

                Time: Wed Nov 15 05:07:17 UTC 2023
                Command line: /opt/oracle/dcs/exacd_netchk/exacd_netchk.py --configfile=/tmp/exacd_netchk.json
                Image version: 22.1.7.0.0.230113
                ---------------------------------------------
                Diagnosis Results:
                - [DIAG-VM-NETWORK-004] Validate VM to VM and cell connectivity over RDS ...................... FAILED

                Summary:
                0% (0 out of 1) passed

                Details of Failed Diagnosis Steps:
                - [DIAG-VM-NETWORK-004] Validate VM to VM and cell connectivity over RDS
                celts-2ofzi1 stre1(100.106.75.19) is able to reach sea201309exdcl04-priv2(100.106.33.127)
                celts-2ofzi1 stre1(100.106.75.19) is able to reach sea201309exdcl04-priv1(100.106.33.126)
                celts-2ofzi1 stre1(100.106.75.19) is able to reach sea201309exdcl03-priv1(100.106.33.124)
                celts-2ofzi1 stre1(100.106.75.19) is able to reach sea201309exdcl03-priv2(100.106.33.125)
                celts-2ofzi1 stre1(100.106.75.19) is able to reach sea201309exdcl01-priv2(100.106.33.121)
                celts-2ofzi1 stre1(100.106.75.19) is able to reach sea201309exdcl02-priv1(100.106.33.122)
                celts-2ofzi1 stre1(100.106.75.19) is able to reach sea201309exdcl01-priv1(100.106.33.120)
                celts-2ofzi1 stre1(100.106.75.19) is able to reach sea201309exdcl02-priv2(100.106.33.123)
                celts-2ofzi1 stre0(100.106.75.18) is able to reach sea201309exdcl04-priv2(100.106.33.127)
                celts-2ofzi1 stre0(100.106.75.18) is able to reach sea201309exdcl04-priv1(100.106.33.126)
                celts-2ofzi1 stre0(100.106.75.18) is able to reach sea201309exdcl03-priv1(100.106.33.124)
                celts-2ofzi1 stre0(100.106.75.18) is able to reach sea201309exdcl03-priv2(100.106.33.125)
                celts-2ofzi1 stre0(100.106.75.18) is able to reach sea201309exdcl01-priv2(100.106.33.121)
                celts-2ofzi1 stre0(100.106.75.18) is able to reach sea201309exdcl02-priv1(100.106.33.122)
                celts-2ofzi1 stre0(100.106.75.18) is able to reach sea201309exdcl01-priv1(100.106.33.120)
                celts-2ofzi1 stre0(100.106.75.18) is able to reach sea201309exdcl02-priv2(100.106.33.123)
                celts-2ofzi1 clre1(100.107.5.19) is not able to reach sea201323exddu1104-clre1(100.107.5.21)
                celts-2ofzi1 clre1(100.107.5.19) is not able to reach sea201323exddu1104-clre0(100.107.5.20)
                celts-2ofzi1 clre0(100.107.5.18) is not able to reach sea201323exddu1104-clre1(100.107.5.21)
                celts-2ofzi1 clre0(100.107.5.18) is not able to reach sea201323exddu1104-clre0(100.107.5.20)
                Mitigation suggestions:
                 - Please check if interface is running

                [opc@celts-2ofzi1 ~]$

        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _nodes_where_rds_ping_failed = []

        self.mPatchLogInfo("\n\n**** Performing RDS ping validations. ****\n")

        if aHBCheckFailedDomUList and len(aHBCheckFailedDomUList) > 0:

            if aConnectibleDomUList and len(aConnectibleDomUList) > 0:

                _hbcheck_failed_nathostname_vm_list = self.mGetHandlerInstance().mGetDomUNatHostNamesforDomuCustomerHostNames(
                    aHBCheckFailedDomUList)
                _hbcheck_failed_connectible_domu_list = [x for x in _hbcheck_failed_nathostname_vm_list if
                                                         x in aConnectibleDomUList]

                # This filter is to run rds_ping alone with netchk
                _netchk_cmd_filter_json = {
                    "netchk": {
                        "result_retention_days": 14
                    },
                    "prefix": {
                        "dom0": "DIAG-HV-NETWORK",
                        "domu": "DIAG-VM-NETWORK"
                    },
                    "scripts": {
                        "domu": {
                            "domu_rds_connectivity": {
                                "id": 4,
                                "classname": "DomuRdsConnectivity",
                                "desc": "Validate VM to VM and cell connectivity over RDS",
                                "filename": "domu_rds_connectivity.py",
                                "metricname": "NetchkVmRdsConnectivity",
                                "run_by_default": True
                            }
                        }
                    }
                };

                try:
                    # start of _mValidateRDSPing
                    def _mValidateRDSPing(aNode, aStatus):
                        """
                         This sub method invokes the netchk command
                        """
                        _node = exaBoxNode(get_gcontext())
                        try:
                            if self.mGetHandlerInstance().mGetCurrentTargetType() == PATCH_DOM0:
                                _user_to_connect_with = self.mGetHandlerInstance().mGetUserDetailsBasedOnDomUhostname(aNode)
                                if _user_to_connect_with:
                                    _node.mSetUser(_user_to_connect_with)
                            _node.mSetMaxRetries(self.mGetHandlerInstance().mGetMaxNumberofSshRetries())
                            _node.mConnect(aHost=aNode)
                            _netchk_file = "/opt/oracle/dcs/exacd_netchk/netchk"

                            # If the netchk file does not exist, dont fail the validation
                            if not _node.mFileExists(_netchk_file):
                                self.mPatchLogWarn(f"{_netchk_file} does not exist on {aNode}.")
                            else:
                                _netchk_cmd_filter_json_str = json.dumps(_netchk_cmd_filter_json, indent=4)
                                _exacd_netchk_json = "/tmp/exacd_netchk.json"
                                _node.mConnect(aHost=aNode)
                                # create exacd_netchk.json file
                                _node.mExecuteCmdLog(f"printf '{_netchk_cmd_filter_json_str}' > {_exacd_netchk_json}")
                                if not _node.mFileExists(_exacd_netchk_json):
                                    self.mPatchLogWarn(f"{_exacd_netchk_json} could not be created on {aNode}.")
                                else:
                                    _netchk_cmd = f" {_netchk_file}  --configfile={_exacd_netchk_json} | grep 'Validate VM to VM and cell connectivity over RDS' | grep PASSED "
                                    self.mPatchLogInfo(f"Executing {_netchk_cmd} on {aNode}.")
                                    _node.mExecuteCmd(_netchk_cmd)
                                    if int(_node.mGetCmdExitStatus()) != 0:
                                        self.mPatchLogError(f"rds_ping validation on {aNode} failed.")
                                        aStatus.append({'node': aNode, 'status': 'failed'})
                                    else:
                                        self.mPatchLogInfo(
                                            f"rds_ping validation between vm to vm and vm to cell succeeded on {aNode}.")

                        except Exception as e:
                            # Even if exception occurs here, do not fail. Exception could be due to mconnect etc, so even if rds_ping validation could not be evaluated, heartbeat error would be thrown anyway
                            self.mPatchLogWarn(
                                f"Exception {str(e)} occurred while executing _mValidateRDSPing on the node {aNode}.")
                            self.mPatchLogTrace(traceback.format_exc())

                        finally:
                            if _node.mIsConnected():
                                _node.mDisconnect()
                        # end of _mValidateRDSPing

                    """
                     Parallelize rds_ping validation on remote nodes.
                    """
                    _plist = ProcessManager()
                    _rc_status = _plist.mGetManager().list()
                    for _node_to_check in _hbcheck_failed_connectible_domu_list:
                        _p = ProcessStructure(_mValidateRDSPing, [_node_to_check, _rc_status], _node_to_check)

                        """
                         Timeout parameter validate_rds_ping_timeout_in_seconds is configurable in Infrapatching.conf. 
                         Currently it is set to 30 minutes
                         Thread join timeout is set to 180 seconds  
                         """
                        _p.mSetMaxExecutionTime(self.mGetHandlerInstance().mGetValidateRDSPingTimeoutInSeconds())
                        _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
                        _p.mSetLogTimeoutFx(self.mPatchLogWarn)
                        _plist.mStartAppend(_p)

                    _plist.mJoinProcess()

                    if _plist.mGetStatus() == "killed":
                        _suggestion_msg = f"Timeout occurred while validating RDSPing on the list of Nodes : {str(_hbcheck_failed_connectible_domu_list)}."
                        self.mGetHandlerInstance().mAddError(DOMU_RDS_PING_FAILED, _suggestion_msg)
                        return _ret

                    # Check for the nodes where rds_ping validation failed
                    for _rc_details in _rc_status:
                        if _rc_details['status'] == "failed":
                            _nodes_where_rds_ping_failed.append(_rc_details['node'])

                except Exception as e:
                    """
                    # Need to return either rds_ping succeeded or failed as part of this method.
                    Exception occurrence could be due to mconnect or parallel processing etc and does not convey rds_ping failed so ignoring the exception
                    """
                    self.mPatchLogWarn(f"Exception {str(e)} occurred while executing mValidateRDSPingOnDomuNodes.")
                    self.mPatchLogTrace(traceback.format_exc())
            else:
                self.mPatchLogWarn(
                    f"rds-ping could not be validated since keys are not available to connect vms : {json.dumps(aHBCheckFailedDomUList, indent=4)} ")

        if len(_nodes_where_rds_ping_failed) > 0:
            _ret = DOMU_RDS_PING_FAILED
            _suggestion_msg = f"Heartbeat validation failed on : {str(aHBCheckFailedDomUList)} and rds_ping failed on :{str(_nodes_where_rds_ping_failed)} "
            self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)

        self.mPatchLogInfo("**** RDS ping validations completed ****\n")
        return _ret

    def mGetGiHomePath(self, aNode):
        """
        This function returns the GI home location
        Note that the permission of oratab and olr.loc is open to all (19 and 23)
        -rw-rw-r-- 1 oracle oinstall 772 Oct 26 10:10 /etc/oratab
        drwxr-xr-x  7 root   root         163 Oct 26 09:50 oracle
        -rw-r--r-- 1 root oinstall 113 Oct 26 09:50 /etc/oracle/olr.loc
        """
        _gi_home = ""
        _ret = PATCH_SUCCESS_EXIT_CODE

        # try olr.loc for all exa cloud services viz exascale and ExaCS/CC
        _cmd = "cat /etc/oracle/olr.loc | grep 'crs_home' | cut -f 2 -d '='"
        _gi_home = self.mGetHandlerInstance().mReturnExecOutput(_cmd, aNode)

        if len(_gi_home) < 1:
            ebLogInfo(f"*** GI home could not be detected ")
            _ret = DOMU_INVALID_CRS_HOME
        else:
            ebLogInfo(f"*** GI home detected : {_gi_home}")

        return _ret, _gi_home

    def mGenCrsctlCmd(self, aNode, aArgs, aHostname, aQueueError=True):
        """
        This function builds the crsctl command
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _suggestion_msg = None
        _gi_home = ""
        _cmd = ""

        # get GI home
        _ret, _gi_home = self.mGetGiHomePath(aNode)

        # check if the crsctl binary exists if GI home is valid
        if _ret == PATCH_SUCCESS_EXIT_CODE and aNode.mFileExists(_gi_home + "/bin/crsctl"):
            _cmd = f"{str(_gi_home)}/bin/crsctl {str(aArgs)}"
        else:
            _ret = DOMU_INVALID_CRS_HOME
            # if error needs to be queued up and the patch operation is nor Patch_prereq_check
            if self.mGetHandlerInstance().mGetTask() not in [ TASK_PREREQ_CHECK ] and aQueueError:
                _suggestion_msg = f"Invalid CRS HOME on {aHostname}"
                self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)
                self.mPatchLogError(f"Unable to determine crs home on {aHostname}")
            else:
                self.mPatchLogWarn(f"Unable to determine crs home on {aHostname}")
        return _ret, _cmd

    def mCollectEDVCellInfo(self, aDomUList):
        _rc = PATCH_SUCCESS_EXIT_CODE
        _domu_list_no_fqdn = []

        if len(aDomUList) == 0:
            self.mPatchLogInfo('DomU list is empty.')
            return _rc

        _list_domus_Exascale_storage = self.mGetHandlerInstance().mGetDomuListByClusterStorageType(EXASCALE_CLUSTER_STORAGE_TYPE)

        for _domu in aDomUList:
            if _domu in _list_domus_Exascale_storage:
                _domu_list_no_fqdn.append(_domu.split('.')[0])
            else:
                self.mPatchLogInfo(f'Domu {_domu} not on exascale cluster')

        _idx_guid = 3
        _idx_hostname = 1
        _cell = exaBoxNode(get_gcontext())
        _cmd = f"{ESCLI_CMD} --wallet {ESCLI_WALLET_LOCATION} lsinitiator -l --attributes id,hostName,giClusterName,giClusterId,version,lastHeartbeat,registerTime"
        '''
        [root@scaqar01celadm01 ~]# /opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet lsinitiator -l --attributes id,hostName,giClusterName,giClusterId,version,lastHeartbeat,registerTime
        id                                   hostName       giClusterName   giClusterId                          version           lastHeartbeat             registerTime
        60b679ac-bafa-c910-60b6-79acbafac910 scaqar01dv0207 iad1376clu070a1 11a8f48a-da35-5f3c-ff7c-b37096bdf813 24.1.2.0.0.240711 2024-08-22T15:32:43-07:00 2024-08-06T05:26:09-07:00
        a0f6ad56-a639-c085-a0f6-ad56a639c085 scaqar01dv0107 iad1376clu070a1 11a8f48a-da35-5f3c-ff7c-b37096bdf813 24.1.2.0.0.240711 2024-08-22T15:32:43-07:00 2024-08-06T05:26:10-07:00

        If CRS stack is down, the line would be like:
        a0f6ad56-a639-c085-a0f6-ad56a639c085 scaqar01dv0107                                                      24.1.2.0.0.240711 2024-08-22T15:32:43-07:00 2024-08-06T05:26:10-07:00

        In case the node is down, because EDV will not be present, no line will be present in the output
        '''
        # info should be the same in all cells, but due to some connectivity issues, it coudl be behind, so connect to the majority
        # of cells. Not that some customers may have 50+ cells.
        _number_majority_cells = int(len(self.mGetHandlerInstance().mGetCellList()) / 2) + 1
        _count_cell = 1
        _good_cells = 0
        _localDict = {}
        for _cellName in self.mGetHandlerInstance().mGetCellList():
            _cell.mConnect(aHost=_cellName)

            _i, _o, _e = _cell.mExecuteCmd(_cmd)
            _exit_status = _cell.mGetCmdExitStatus()
            if int(_exit_status) == 0:
                _good_cells = _good_cells + 1
                _first_line = True
                _out = _o.readlines()
                _state = "up"
                _hb_time = None
                _guid = None
                _reg_time = None
                for _output in _out:
                    # skip header
                    if _first_line:
                        _first_line = False
                        continue
                    _line = re.split(r'[\n\t\f\v\r ]+', _output.strip())
                    _hostname = _line[_idx_hostname]
                    if _hostname in _domu_list_no_fqdn:
                        # 7 columns if info is complete
                        # a0f6ad56-a639-c085-a0f6-ad56a639c085 scaqar01dv0107 iad1376clu070a1 11a8f48a-da35-5f3c-ff7c-b37096bdf813 24.1.2.0.0.240711 2024-08-22T15:32:43-07:00 2024-08-06T05:26:10-07:00
                        # 6 columns, due to bug in EDV (either no clusterID or no clustername)
                        # a0f6ad56-a639-c085-a0f6-ad56a639c085 scaqar01dv0107 11a8f48a-da35-5f3c-ff7c-b37096bdf813 24.1.2.0.0.240711 2024-08-22T15:32:43-07:00 2024-08-06T05:26:10-07:00
                        # 5 columns, no info from EDV
                        # a0f6ad56-a639-c085-a0f6-ad56a639c085 24.1.2.0.0.240711 2024-08-22T15:32:43-07:00 2024-08-06T05:26:10-07:00

                        if len(_line) == 7:
                            _state = "up"
                            _hb_time = _line[-2]
                            _reg_time = _line[-1]
                            _guid = _line[_idx_guid]
                        elif len(_line) == 6:
                            # for the case where EDV hit this bug, providing either clusterId or clustername
                            # 0d72d0ef-2b28-b02c-0d72-d0ef2b28b02c scaqau05dv0207                 6ed854f2-0d12-4fcd-ffec-19496f550f6f 24.1.2.0.0.240727
                            # 2024-10-08T18:21:23+00:00 2024-10-08T16:09:04+00:00
                            _state = "up"
                            _hb_time = _line[-2]
                            _reg_time = _line[-1]
                            # note that we get either clustername or clusterid here, whatever is present
                            _guid = _line[_idx_guid - 1]
                        # we consider the cluster down here
                        else:
                            _state = "down"
                            _hb_time = _line[-2]
                            _reg_time = _line[-1]
                            _guid = None
                        # there was already info about the domU:
                        # if prev state was up and new state is down, discard new entry
                        # if prev state was up and new state is up, discard new entry
                        # if prev state was down and new state is down discard new entry
                        # if prev state was down and new state is up, replace
                        if _hostname in _localDict.keys():
                            _info_already_added = _localDict[_hostname]
                            # if previous state was down and new state is up, let's replace
                            if _info_already_added[0] == "down" and _state == "up":
                                _localDict[_hostname] = [_state, _guid, mValidateTime(_reg_time, _hb_time)]
                        else:
                            _localDict[_hostname] = [_state, _guid, mValidateTime(_reg_time, _hb_time)]

                if _cell.mIsConnected():
                    _cell.mDisconnect()
                # if majority of cells were checked, we can stop
                if _count_cell >= _number_majority_cells:
                    # if no cells were good to get EDV info, reset cell counter and go over all
                    if _good_cells == 0:
                        _count_cell = 0
                    else:
                        break
                _count_cell = _count_cell + 1

        # store the EDV info in the context
        for _hostname in _localDict.keys():
            self.__dom0_hb_info[_hostname] = [_localDict[_hostname][0], _localDict[_hostname][1],
                                              _localDict[_hostname][2]]
        self.mPatchLogInfo(f'HB info collected: {self.__dom0_hb_info}')

    def mCheckEDVInfoForHB(self, aDomuName, aCellList, aTimeoutInSec):
        '''
        This method is called in post patch. It will use the snapshot obtained prior
        to patching to compare with current output
        Collection phase: it stores the hostname, if up/down, and last EDV heartbeat.
        Comparison phase: when the node is rebooted, EDV, when it comes up in the node
        it will have to register in all cells. So the time has to be post last hb seen
        in the cell
        _checked_for_secs is also returned to optimise time taken to perform HB checks
        on non-Exascale environments.
        '''
        _idx_state = 0
        _idx_guid = 1
        _idx_reg_time = 2
        _detected_down = False
        _guid = None

        # if domU is not present, when the collection happened, EDV was down, what could indicate
        # that the node was down, or EDV had a bug and did not register. If the machine is not down
        # and EDV is not registered, it would be bug (corner case?). Note that if VM was down,
        # previous checks should have caught before here
        if aDomuName not in self.__dom0_hb_info.keys():
            self.mPatchLogInfo(f'EDV was down on DomU [{aDomuName}] prior to patching. No entry in escli')
            _detected_down = True
        else:
            _info = self.__dom0_hb_info[aDomuName]
            # if CRS stack was down prior to patching, skip it
            if _info[_idx_state] == "down":
                self.mPatchLogInfo(f'CRS stack was down on [{aDomuName}] prior to patching, with entry in escli')
                _detected_down = True

        if not _detected_down:
            _guid = _info[_idx_guid]
            self.mPatchLogInfo(f'Checking identifier {_guid}')

        # Note: even if the cluster was down prior to patching, we check if it is up now, to follow the same logic as checking for the alert/diskmon

        # cluster supports some connectivity issues with cells, so we will need to loop in the set of cells and
        # stop once we find one that has an updated info or if timetout is reached
        # the space is required to distinguish between node1 and node11. Also choosing GUID, since clustername could be a subset of hostname
        if not _guid:
            _cmd = f"{ESCLI_CMD} --wallet {ESCLI_WALLET_LOCATION} lsinitiator -l --attributes id,hostName,giClusterName,giClusterId,version,lastHeartbeat,registerTime| grep ' {aDomuName} ' "
        else:
            _cmd = f"{ESCLI_CMD} --wallet {ESCLI_WALLET_LOCATION} lsinitiator -l --attributes id,hostName,giClusterName,giClusterId,version,lastHeartbeat,registerTime| grep ' {aDomuName} ' |grep {_guid}"
        '''
        Output of lsinitiator
        [root@scaqar01celadm01 ~]# /opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet lsinitiator -l --attributes id,hostName,giClusterName,giClusterId,version,lastHeartbeat,registerTime
        id                                   hostName       giClusterName   giClusterId                          version           lastHeartbeat             registerTime
        60b679ac-bafa-c910-60b6-79acbafac910 scaqar01dv0207 iad1376clu070a1 11a8f48a-da35-5f3c-ff7c-b37096bdf813 24.1.2.0.0.240711 2024-08-22T15:32:43-07:00 2024-08-06T05:26:09-07:00
        a0f6ad56-a639-c085-a0f6-ad56a639c085 scaqar01dv0107 iad1376clu070a1 11a8f48a-da35-5f3c-ff7c-b37096bdf813 24.1.2.0.0.240711 2024-08-22T15:32:43-07:00 2024-08-06T05:26:10-07:00
        21b41409-6545-ca1c-21b4-14096545ca1c scaqar01dv0102 iad1376clu020a1 856f559a-f8ed-5f54-ff69-a9b99b8bb0f6 24.1.2.0.0.240711 2024-08-22T15:31:53-07:00 2024-08-22T06:01:56-07:00
        6c3f6a21-577d-71df-6c3f-6a21577d71df scaqar01dv0206 iad1376clu060a1 f328a2f0-fffb-ef59-ff6d-d1306e1dbf09 24.1.2.0.0.240711 2024-08-22T15:32:46-07:00 2024-08-07T20:50:41-07:00
        b5502659-6c5e-3de1-b550-26596c5e3de1 scaqar01dv0106 iad1376clu060a1 f328a2f0-fffb-ef59-ff6d-d1306e1dbf09 24.1.2.0.0.240711 2024-08-22T15:32:50-07:00 2024-08-07T20:50:46-07:00
        '''
        _cell = exaBoxNode(get_gcontext())
        if not _detected_down:
            _init_reg_time = mConvertTimeEscli(_info[_idx_reg_time])
        _crs_is_up = False
        _checked_for_secs = 0
        # exit the loop if time passed or if crs is up
        self.mPatchLogInfo(f"Start validating every {HEARTBEAT_CHECK_INTERVAL_IN_SECONDS} seconds if heartbeat between DomU and CELL is established or CRS is up on Exascale with a timeout of {aTimeoutInSec} seconds.")
        while _checked_for_secs <= aTimeoutInSec and not _crs_is_up:
            for _cell_name in aCellList:
                _cell.mConnect(aHost=_cell_name)

                self.mPatchLogInfo(f'Checking heartbeat from domU [{aDomuName}] to cell [{_cell_name}] on Exascale')

                _i, _o, _e = _cell.mExecuteCmd(_cmd)

                if int(_cell.mGetCmdExitStatus()) == 0:
                    _out = _o.readlines()
                    _out = (_out[0]).strip()
                    _list = re.split(r'[\n\t\f\v\r ]+', _out)
                    # reg time
                    _time = _list[-1]
                    # if the stack was initially detected down, no info to compare with
                    if _detected_down:
                        # if it was down before, no guid, just check the number of columns
                        if len(_list) == 7 or len(_list) == 6:
                            self.mPatchLogInfo(f'Stack is up on {aDomuName} and previously no info: {_list}')
                            _crs_is_up = True
                            break
                    else:
                        # check if registration time has changed. Note that even if the date is invalid, it means EDV is
                        # about to register, so it is a new incarnation
                        _valid_time = mValidateTime(_time, _time)
                        _reg_time = mConvertTimeEscli(_valid_time)
                        if _reg_time <= _init_reg_time:
                            self.mPatchLogInfo(f'Still waiting for stack on {aDomuName} to be up - registration time {str(_reg_time)}')
                        else:
                            self.mPatchLogInfo(f'CRS stack on {aDomuName} is up - registration time {str(_reg_time)}')
                            _crs_is_up = True
                            break

                if _cell.mIsConnected():
                    _cell.mDisconnect()
                sleep(9)
                _checked_for_secs += HEARTBEAT_CHECK_INTERVAL_IN_SECONDS

        if _cell.mIsConnected():
            _cell.mDisconnect()
        return _crs_is_up, _checked_for_secs

    def mPerformDomuCrsCheckForAllClusters(self):
        """
         This method can be invoked independent of patch operation.
         Heartbeat timeout is set to 1 seconds and is expected for
         the cells to have heartbeat status message in alert logs for
         the domu list provided.
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _clusters_with_crs_down_and_no_high_availability = {}
        _domus_accessible_from_exacloud_node = []
        _domus_not_accessible_from_exacloud_node = []

        if not self.mGetHandlerInstance().mGetInfrapatchExecutionValidator().mCheckCondition('checkHeartbeatValidationPriorToPatchmgrRun'):
            self.mPatchLogInfo("Cluster wide CRS checks will be skipped.")
            return _ret

        self.mPatchLogInfo(
            "\n ***Performing CRS checks on clusters. Checks are performed only in case of keys injected to DomUs during Dom0 patching.***\n")
        try:
            if len(self.mGetHandlerInstance().mGetClusterToVmMapWithNonZeroVcpu()) > 0 and self.mGetHandlerInstance().mGetOpStyle() != OP_STYLE_NON_ROLLING:

                _current_dom0_cluster_list = []
                if self.mGetHandlerInstance().mGetOpStyle() == OP_STYLE_ROLLING:
                    # For DOM0 rolling patching, since only one node is passed at a time by CP, extract the first element from the includeNode list.
                    if self.mGetHandlerInstance().mGetIncludeNodeList():
                        _current_dom0_node = self.mGetHandlerInstance().mGetIncludeNodeList()[0]
                        _current_dom0_cluster_list  = self.mGetHandlerInstance().mGetClusterListForDom0(_current_dom0_node)
                        if _current_dom0_cluster_list:
                            self.mPatchLogInfo(f"Cluster list associated with current dom0 {_current_dom0_node} is {json.dumps(_current_dom0_cluster_list, indent=4)}.")

                '''
                 Get domu details from Ecra metadata and perform
                 heartbeat validations for each cluster.
                '''
                for _clustername, _domu_list in self.mGetHandlerInstance().mGetClusterToVmMapWithNonZeroVcpu():

                    # Perform cluster-wide CRS check only on clusters belonging to the current Dom0 for rolling Dom0 patching. For rack nodes patching, perform across all clusters.
                    if len(_current_dom0_cluster_list) > 0 and _clustername not in _current_dom0_cluster_list:
                        continue

                    _domu_crs_failure_list = []

                    '''
                     SSH connectivity between exacloud &
                     DomU to be performed using NAT Hostname.
                     Input _domu_list has customer Hostnames.
                    '''
                    _domu_list = self.mGetHandlerInstance().mGetDomUNatHostNamesforDomuCustomerHostNames(_domu_list)

                    '''
                     In case of a quarter rack and CRS auto start is enabled
                     only on one of the VM, no heartbeat checks are performed.

                     Expectation is customer is aware that the CRS autostart is
                     disabled on one of the VMs in a given 2 VM list and the
                     downtime is expected.
                    '''
                    _domus_accessible_from_exacloud_node, _domus_not_accessible_from_exacloud_node = self.mGetHandlerInstance().mGetReachableDomuList(
                        _domu_list)
                    if len(_domus_accessible_from_exacloud_node) > 0:
                        _, _list_of_vms_crs_auto_startup_enabled = self.mReturnListofVMsWithCRSAutoStartupEnabled(
                            _domus_accessible_from_exacloud_node)

                        self.mPatchLogInfo(
                            f"List of VMs where CRS auto startup is currently enabled : {json.dumps(_list_of_vms_crs_auto_startup_enabled, indent=4)}.")

                        self.__crs_autostart_enabled_vm_set.update(set(self.mGetHandlerInstance().mGetDomUCustomerHostNamesforDomuNatHostNames(_list_of_vms_crs_auto_startup_enabled)))

                        if len(_list_of_vms_crs_auto_startup_enabled) < 2:
                            self.mPatchLogInfo(
                                "CRS auto startup must be enabled on atleast 2 VMs for the CRS validations to be performed.")
                            continue

                        '''
                         CRS is validated and started up in case of CRS services down on 
                         a given DomU and cluster. If we are unable to startup CRS even 
                         after 3 iterations, CRS validation and inturn infra patching operation 
                         is marked as failure.
                        '''
                        _, _domu_crs_failure_list = self.mCheckAndStartupCRSDuringDom0Patching(
                            _list_of_vms_crs_auto_startup_enabled)
                        """
                        Updating self.__crs_autostart_enabled_vm_set to have vms where crs auto start is enabled and crs is running 
                        """
                        self.__crs_autostart_enabled_vm_set -= set(_domu_crs_failure_list)

                        if ((int(len(_list_of_vms_crs_auto_startup_enabled)) - int(len(_domu_crs_failure_list))) < 2):
                            _domu_crs_failure_list_with_nat_and_customer_hostname = self.mGetHandlerInstance().mReturnBothDomUNATCustomerHostNames(
                                _domu_crs_failure_list)
                            _suggestion_msg = f"PRE-PATCH - CRS services were supposed to be running on at least 2 VMs.It is currently down on {str(_domu_crs_failure_list_with_nat_and_customer_hostname)} for the cluster : {str(_clustername)}."
                            if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                                self.mPatchLogWarn(f"{_suggestion_msg}")
                            else:
                                self.mPatchLogError(f"{_suggestion_msg}")
                            _clusters_with_crs_down_and_no_high_availability[_clustername] = _domu_crs_failure_list
                        elif len(_domu_crs_failure_list) > 0:
                            _domu_crs_failure_list_with_nat_and_customer_hostname = self.mGetHandlerInstance().mReturnBothDomUNATCustomerHostNames(
                                _domu_crs_failure_list)
                            self.mPatchLogInfo(
                                f"Although CRS is down on few VMs :{str(_domu_crs_failure_list_with_nat_and_customer_hostname)} belonging to the cluster : {str(_clustername)}, high availability is not impacted as CRS is running on at least 2 VMs.")
                    else:
                        _domus_not_accessible_from_exacloud_node_nat_customer_hostname = self.mGetHandlerInstance().mReturnBothDomUNATCustomerHostNames(
                            _domus_not_accessible_from_exacloud_node)
                        _suggestion_msg = f"PRE-PATCH - CRS validations are skipped as one or more VMs are not accessible : {str(_domus_not_accessible_from_exacloud_node_nat_customer_hostname)}."
                        if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                            self.mPatchLogWarn(f"{_suggestion_msg}")
                        else:
                            self.mPatchLogError(f"{_suggestion_msg}")

                self.mPatchLogInfo(
                    f"Current list of VMs where DB healthchecks are run : {str(self.__crs_autostart_enabled_vm_set)}.")

                if len(_clusters_with_crs_down_and_no_high_availability) > 0:
                    _suggestion_msg = f"PRE-PATCH - CRS services are supposed to be running on atleast 2 VMs. It is currently down on the given list of clusters and VMs : {str(_clusters_with_crs_down_and_no_high_availability)}. Please startup CRS services on required VMs and retry patch operations."
                    if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                        self.mPatchLogWarn(f"{_suggestion_msg}")
                    else:
                        _ret = DOMU_HEARTBEAT_NOT_RECEIVED
                        self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)
            else:
                self.mPatchLogInfo(
                    "DomU heartbeat checks on cells will be skipped in case of non-rolling patch operation or in case of CRS up and running only on one VM on a given cluster.")

        except Exception as e:
            _suggestion_msg = "PRE-PATCH - Exception in fetching DomU list and cluster details for heartbeat validations."
            if self.mGetHandlerInstance().mGetTask() == TASK_PREREQ_CHECK:
                self.mPatchLogWarn(f"{_suggestion_msg}")
            else:
                self.mPatchLogError("Exception in fetching DomU list for heartbeat validations." + str(e))
                self.mPatchLogTrace(traceback.format_exc())
                _ret = INDIVIDUAL_PATCH_REQUEST_EXCEPTION
                self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo("***Cluster wide CRS checks on clusters Completed.***")
            return _ret

    def mExtractCRSResourceFromDbaasapiError(self, aDbaasapiErrMsg, aIndexToParseFor):
        _resource_name = None
        try:
            _tmp_res = aDbaasapiErrMsg.split()[aIndexToParseFor]
            if _tmp_res.endswith('.'):
                _resource_name = _tmp_res[:-1]
            else:
                _resource_name = _tmp_res

        except Exception as e:
            self.mPatchLogWarn(
                f"Exception {str(e)} occurred while getting the crs resource name from dbaasapi error string {aDbaasapiErrMsg}")
            self.mPatchLogTrace(traceback.format_exc())
        return _resource_name

    def mExecuteInfraPostSanityCheck(self, aNode, aUser=None):
        """
        :param aNode: Remote domu node
        :param aUser: user context with which ssh connection would be done to connect to VM nodes
        :return: PATCH_SUCCESS_EXIT_CODE on success otherwise DOMU_DBS_DOWN or DOMU_DBAASAPI_COMMAND_FAILED

         output format of postcheck output when some dbs dont come up after patching :

        scenario1:
        ----------
        { "warning" : [], "error" : [ "Resource ora.db242901_tvs_sea.db242901_pdb1.paas.oracle.com.svc is online on
        only 1 vm(s)after patching whereas before patching it was online on 2 vm(s). Resource
        ora.db242901_tvs_sea.db242901_pdb1.paas.oracle.com.svc state is not ONLINE on some vms after infrapatching:
        scaqak04dv0401 -> OFFLINE. Please make sure it is running on atleast 2 vm(s) for maximum availability",
        "Resource ora.db242901_tvs_sea.db is online on only 1 vm(s)after patching whereas before patching it was
        online on 2 vm(s). Resource ora.db242901_tvs_sea.db state is not ONLINE on some vms after infrapatching:
        scaqak04dv0401 -> OFFLINE. Please make sure it is running on atleast 2 vm(s) for maximum availability" ],
        "sanity_postcheck_status" : 1 }

        scenario2:
        ----------
        { "sanity_postcheck_status": 1, "error": [ "Resource ora.db242901_tvs_sea.db is not online on any vm after
        patching whereas before patching it was online on 2 vm(s).Resource ora.db242901_tvs_sea.db state is not
        ONLINE on some vms after infrapatching:  scaqag01dv0501m -> OFFLINE scaqag01dv0601m -> OFFLINE. Please make
        sure it is running on atleast  2 vm(s) for maximum availability" ], "warning": [] }

        Example for crs service degradation messages from post sanity output:

        example1:
        "Resource ora.tnstr03p_db.tnstr03p_pdb1.paas.oracle.com.svc is not online on any vm after patching whereas before
         patching it was online on 1 vm(s). Please make sure it is running on atleast 1 vm(s) for maximum availability"

        example2:
        "Resource ora.adsdev.db is not online on any vm after patching whereas before patching it was online on 2 vm(s).
        Please make sure it is running on atleast 2 vm(s) for maximum availability"

        Note:  database,service and listener crs resources are only parsed for degradation check

        """
        _ret = PATCH_SUCCESS_EXIT_CODE

        _suggestion_msg_list = []
        _degraded_res = []
        _ret, _infra_sanity_check_output = self.mGetDBAASAPIOutputForInfraSanityCheckCommand(aNode,
                                                                                             INFRA_SANITY_POSTCHECK,
                                                                                             aUser=aUser)
        if _ret == PATCH_SUCCESS_EXIT_CODE:
            _infra_sanity_check_status_str = f"sanity_{INFRA_SANITY_POSTCHECK}_status"
            _regex_str_resource_online_on_few_vms = r'Resource ora\..*\.(db|svc|lsnr) is online on only'
            _regex_str_resource_not_online_on_any_vm = r'Resource ora\..*\.(db|svc|lsnr) is not online on any vm '
            if _infra_sanity_check_status_str in _infra_sanity_check_output and _infra_sanity_check_output[
                _infra_sanity_check_status_str] == 1:
                _errr_list = _infra_sanity_check_output[INFRA_SANITY_ERROR]
                for err_msg in _errr_list:
                    if re.search(_regex_str_resource_online_on_few_vms, err_msg) or re.search(
                            _regex_str_resource_not_online_on_any_vm, err_msg):
                        if self.mGetHandlerInstance().mGetCurrentTargetType() == PATCH_DOM0:
                            _ret = DOM0_PATCHING_DB_HEALTHCHECKS_CRS_RESOURCES_ARE_DOWN
                        else:
                            _ret = DOMU_CRS_RESOURCES_ARE_DOWN
                        _suggestion_msg_list.append(err_msg)
                        _resource_name = self.mExtractCRSResourceFromDbaasapiError(err_msg, 1)
                        if _resource_name:
                            _degraded_res.append(_resource_name)

        if _ret != PATCH_SUCCESS_EXIT_CODE:
            _suggestion_msg = str(_suggestion_msg_list)
            if _suggestion_msg and len(_suggestion_msg) > ERROR_MSG_TRUNCATE_LENGTH:
                _suggestion_msg = mTruncateErrorMessageDescription(str(_suggestion_msg_list),
                                                                   aSuffixStr=INFRA_SANITY_ERROR_MSG_SUGGESTION)

            self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)
        return _ret, _degraded_res

    def mExecuteInfraPreSanityCheck(self, aNode, aDetectOutage=True, aUser=None):
        """
        :param aNode: Remote domu node
        :param aDetectOutage: To determine outage happens or not based precheck sanity output
        :param aUser: user context with which ssh connection would be done to connect to VM nodes
        :return: PATCH_SUCCESS_EXIT_CODE on success otherwise DOMU_DBS_DOWN or DOMU_DBAASAPI_COMMAND_FAILED

        output format of precheck output for outage scenario:

         { "sanity_precheck_status" : 1, "error" : [ "Following database will have complete downtime during patching:
         ora.db242901_tvs_sea.db. Please make sure it is running on any vm other than scaqak04dv0301 to avoid
         complete downtime", "Following service will have complete downtime during patching:
         ora.db242901_tvs_sea.db242901_pdb1.paas.oracle.com.svc. Please make sure it is running on any vm other than
         scaqak04dv0301 to avoid complete downtime" ], "warning" : [] }

        Note:  database,service and listener crs resources are only parsed for downtime check
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _suggestion_msg_list = []
        _downtime_expected_res = []
        _ret, _infra_sanity_check_output = self.mGetDBAASAPIOutputForInfraSanityCheckCommand(aNode,
                                                                                             INFRA_SANITY_PRECHECK,
                                                                                             aUser)

        self.mPatchLogInfo("\nStarting DB and CRS sanity checks during infra patch operations.")
        if _ret == PATCH_SUCCESS_EXIT_CODE:
            if aDetectOutage:
                _infra_sanity_check_status_str = f"sanity_{INFRA_SANITY_PRECHECK}_status"
                _regex_str_for_downtime_detection = r'Following (database|service|listener)(\(s\))? will have complete downtime during patching'
                _regex_str_for_crs_not_running = r'Please make sure CRS and CRS resource commands are running successfully'
                if _infra_sanity_check_status_str in _infra_sanity_check_output and _infra_sanity_check_output[
                    _infra_sanity_check_status_str] == 1:
                    _errr_list = _infra_sanity_check_output[INFRA_SANITY_ERROR]
                    for err_msg in _errr_list:
                        # Parse for outage detection string
                        if re.search(_regex_str_for_downtime_detection, err_msg):
                            if self.mGetHandlerInstance().mGetCurrentTargetType() == PATCH_DOM0:
                                _ret = DOM0_PATCHING_DB_HEALTHCHECKS_CRS_RESOURCES_ARE_DOWN
                            else:
                                _ret = DOMU_CRS_RESOURCES_ARE_DOWN
                            _suggestion_msg_list.append(err_msg)
                            _resource_name = self.mExtractCRSResourceFromDbaasapiError(err_msg, 8)
                            if _resource_name:
                                _downtime_expected_res.append(_resource_name)

                                # Parse for crs start failure
                        if re.search(_regex_str_for_crs_not_running, err_msg):
                            if self.mGetHandlerInstance().mGetCurrentTargetType() == PATCH_DOM0:
                                _ret = DOM0_PATCHING_DB_HEALTHCHECKS_CRS_SERVICES_DOWN
                            else:
                                _ret = DOMU_CRS_SERVICES_DOWN
                            _suggestion_msg_list.append(err_msg)

        if _ret != PATCH_SUCCESS_EXIT_CODE:
            _suggestion_msg = str(_suggestion_msg_list)
            if _suggestion_msg and len(_suggestion_msg) > ERROR_MSG_TRUNCATE_LENGTH:
                _suggestion_msg = mTruncateErrorMessageDescription(str(_suggestion_msg_list),
                                                                   aSuffixStr=INFRA_SANITY_ERROR_MSG_SUGGESTION)

            self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)
        self.mPatchLogInfo("DB and CRS sanity checks during infra patch operations completed.\n")
        return _ret, _downtime_expected_res

    def mGetDBAASAPIOutputForInfraSanityCheckCommand(self, aNode, aTypeOfSanityCheckOperation, aUser=None):
        """
        This method is going to execute dbaasapi command for infrasanity check using mExecuteDBaaSAPIAction.

        Input for the dbaasapi command is
        {
          "object": "db",
          "action": "precheck",
          "operation": "sanity_check",
          "params": {
            "dbname": "grid",
            "target_type": "dom0",
            "operation_style": "rolling",
            "check_type": "infra",
            "scope": "vm",
            "infofile": "/var/opt/oracle/log/precheck_d5a6de0f-71d2-4ecf-8bfb-9de1533b27dd_infofile.out",
            "error_checks": [
              "CRS_RESOURCE"
            ]
          },
          "outputfile": "/var/opt/oracle/log/precheck_d5a6de0f-71d2-4ecf-8bfb-9de1533b27dd_outfile",
          "FLAGS": ""
        }

        Output of mExecuteDBaaSAPIAction is of the below format :
        -------------------------------------------------------

        { "Status": "Pass", "Log": "precheck for ALL cluster DBs succeeded on Node scaqag01dv0501m.us.oracle.com",
        "precheck": { "warning": [], "error": [ "Following database will have complete downtime during patching:
        ora.db242901_tvs_sea.db. Please make sure it is running on any vm other than scaqag01dv0501m to avoid
        complete downtime", "Following service will have complete downtime during patching:
        ora.db242901_tvs_sea.db242901_pdb1.paas.oracle.com.svc. Please make sure it is running on any vm other than
        scaqag01dv0501m to avoid complete downtime" ], "sanity_precheck_status": 1 } }

        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _infra_sanity_check_output = {}
        try:
            # Execute dbaasapi command only if dbaasapi binary exists
            if self.mGetHandlerInstance().mGetCluPatchCheck().mCheckFileExistsWithUserContext(aNode, DBAASAPI_COMMAND_PATH, aUser):
                _options = self.mGetHandlerInstance().mGetCluCtrlInstance().mGetArgsOptions()
                _dbaasobj = ebCluDbaas(self.mGetHandlerInstance().mGetCluCtrlInstance(), _options)
                _dbaasData = {}
                _params = {}
                _uuid = uuid4().hex
                _info_file = f"/var/opt/oracle/log/{aTypeOfSanityCheckOperation}_{_uuid}_infofile.out"

                _params["dbname"] = "grid"
                _params["target_type"] = PATCH_DOMU
                _params["operation_style"] = OP_STYLE_ROLLING
                _params["check_type"] = "infra"
                _params["scope"] = INFRA_SANITY_CHECK_SCOPE_VM
                _params["infofile"] = _info_file
                _params["error_checks"] = [INFRA_SANITY_CRS_RESOUCE_CHECK]
                self.mPatchLogInfo(
                    f"Invoking dbaasapi command with action - {INFRA_SANITY_CHECK_OPERATION}, operation - {aTypeOfSanityCheckOperation} and param -{json.dumps(_params, indent=4)} ")
                _dbaasobj.mExecuteDBaaSAPIAction(aTypeOfSanityCheckOperation, INFRA_SANITY_CHECK_OPERATION, _dbaasData,
                                                 aNode, _params, _options, aUser=aUser)
                self.mPatchLogInfo(
                    f"dbaasapi command output for operation  {aTypeOfSanityCheckOperation} is {str(_dbaasData)} ")

                _infra_sanity_check_status_str = f"sanity_{aTypeOfSanityCheckOperation}_status"
                if 'Status' in list(_dbaasData.keys()) and _dbaasData[
                    'Status'] == 'Pass' and aTypeOfSanityCheckOperation \
                        in list(_dbaasData.keys()) and _infra_sanity_check_status_str in _dbaasData[
                    aTypeOfSanityCheckOperation]:
                    _infra_sanity_check_output = _dbaasData[aTypeOfSanityCheckOperation]
                else:
                    _ret = DOMU_DBAASAPI_COMMAND_FAILED
            else:
                self.mPatchLogInfo(
                    f"{DBAASAPI_COMMAND_PATH} does not exist on remote node {aNode} so pre_post_sanity check is not run")

        except Exception as e:
            self.mPatchLogWarn(f"Exception {str(e)} occurred in mGetDBAASAPIOutputForInfraSanityCheckCommand ")
            self.mPatchLogTrace(traceback.format_exc())
            _ret = DOMU_DBAASAPI_COMMAND_FAILED
        return _ret, _infra_sanity_check_output

    def mCheckRemoteFileExistsHavingExaboxContext(self, aNodeCtx, aFile):
        """
        :param aNodeCtx: Exabox node context for remote node on which file presence need to be verified
        :param aFile: File name to be searched
        :return: Boolean value of True or False based on file existence
        """
        _ret = False
        try:
            if aFile:
                _ls_cmd_str = f"/usr/bin/ls {aFile}"
                _, _out, _ = aNodeCtx.mExecuteCmd(_ls_cmd_str)
                _exit_code = aNodeCtx.mGetCmdExitStatus()
                if _exit_code == 0:
                    self.mPatchLogInfo(f"File {aFile} exists so returning True")
                    _ret = True
        except Exception as e:
            self.mPatchLogWarn(f"Exception {str(e)} occurred in mCheckRemoteFileExists")
            self.mPatchLogTrace(traceback.format_exc())
        return _ret

    def mFetchAndStoreDBSystemDetailsToFile(self, aVM, aStage, aIsRetry=False, aUser=None):
        """
        :param aVM: VM name on which dbaascli comand is executed to get db system details
        :param aStage: Phase in which this method is triggered, it can be pre or post
        :param aIsRetry: Boolean value indicating that request is a retry request
        :param aUser: user context with which ssh connection would be done to connect to VM nodes
        :return: PATCH_SUCCESS_EXIT_CODE on success otherwise PDB_FETCH_DETAILS_ERROR

        This method executes /usr/bin/dbaascli system getDatabases --reload --showOutputDelimiter on the remote VM and store the json as
        /var/log/exadatatmp/{ecra_request_id}_{stage}_patch_pdb_states

        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _sug_msg = ""
        _pdb_states_file_location_on_remote_node = None
        _is_dom0_patching = True if self.mGetHandlerInstance().mGetCurrentTargetType() == PATCH_DOM0 else False
        _ret_fetch_error = DOM0_PATCHING_DB_HEALTHCHECKS_PDB_FETCH_DETAILS_ERROR if _is_dom0_patching else PDB_FETCH_DETAILS_ERROR
        _node = exaBoxNode(get_gcontext())
        if aUser:
            _node.mSetUser(aUser)
            _node.mSetMaxRetries(self.mGetHandlerInstance().mGetMaxNumberofSshRetries())
        try:
            _node.mConnect(aHost=aVM)
            # ECRA request ID. This value is used in the file name to store the db system details
            _ecra_request_id = self.mGetHandlerInstance().mGetMasterReqId()
            _dbaascli_time_out = self.mGetHandlerInstance().mGetDbaascliTimeOutInSeconds()
            if self.mCheckRemoteFileExistsHavingExaboxContext(_node, DBAASCLI_COMMAND_PATH):

                _pre_patch_file_name = f"{EXADATA_TMP_VAR_LOG_LOCATION}/{_ecra_request_id}_pre_patch_pdb_states"
                if aIsRetry and aStage.lower() == "post" and not self.mCheckRemoteFileExistsHavingExaboxContext(_node,
                                                                                                                _pre_patch_file_name):
                    self.mPatchLogInfo(
                        f"{_pre_patch_file_name} does not exist on the VM - {aVM} for the retry request so post patch "
                        f"file is not required to be generated")
                else:
                    _pdb_states_file_location_on_remote_node = f"{EXADATA_TMP_VAR_LOG_LOCATION}/{_ecra_request_id}_{aStage.lower()}_patch_pdb_states"

                    if aUser:
                        _node.mExecuteCmd(
                            f"{DBAASCLI_COMMAND_PATH} system getDatabases --reload --showOutputDelimiter | sudo tee {_pdb_states_file_location_on_remote_node}",
                            aTimeout=_dbaascli_time_out)
                        _pdb_states_tmp_file_location_on_remote_node = f"/tmp/{_ecra_request_id}_{aStage.lower()}_patch_pdb_states"
                        _node.mExecuteCmd(
                            f"cat  {_pdb_states_file_location_on_remote_node} > {_pdb_states_tmp_file_location_on_remote_node}")
                        _pdb_states_file_location_on_remote_node = _pdb_states_tmp_file_location_on_remote_node
                    else:
                        _node.mExecuteCmd(
                            f"{DBAASCLI_COMMAND_PATH} system getDatabases --reload --showOutputDelimiter > {_pdb_states_file_location_on_remote_node}",
                            aTimeout=_dbaascli_time_out)
                    _exit_status = _node.mGetCmdExitStatus()

                    if int(_exit_status) != 0:
                        _sug_msg = f"dbaascli system getDatabases exited with non zero value on the VM {aVM} "
                        _ret = _ret_fetch_error
                    else:
                        self.mPatchLogInfo(f"dbaascli system getDatabases exited with zero on the VM {aVM}")
                        if not self.mCheckRemoteFileExistsHavingExaboxContext(_node,
                                                                              _pdb_states_file_location_on_remote_node):
                            _sug_msg = f"dbaascli system getDatabases execution failed, file {_pdb_states_file_location_on_remote_node} is not present on the VM {aVM} "
                            _ret = _ret_fetch_error
            else:
                self.mPatchLogInfo(
                    f"{DBAASCLI_COMMAND_PATH} binary does not exist on the VM -{aVM} so pdb state data is not captured")
        except Exception as e:
            self.mPatchLogWarn(
                f"Exception occurred while getting dbsystem details using dbaascli on VM node {aVM}. Error : {str(e)}")
            _ret = _ret_fetch_error
            _sug_msg = f"Exception occurred while executing the command dbaascli system getDatabases on the VM {aVM} "
            self.mPatchLogError(traceback.format_exc())
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()

        if _ret != PATCH_SUCCESS_EXIT_CODE:
            self.mGetHandlerInstance().mAddError(_ret, _sug_msg)
        return _ret

    def mValidatePreAndPostPatchPDBSystemDetailsForDegradation(self, aVM, aUser=None):
        """
        :param aVM: VM name on which db system details json values are compared to detect pdb state degradation
        :param aUser: user context with which ssh connection would be done to connect to VM nodes
        :return:  PATCH_SUCCESS_EXIT_CODE on success otherwise PDB_IN_DEGRADED_STATE or PDB_FETCH_DETAILS_ERROR
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _sug_msg = ""
        _pdb_status_dict = {}
        _node = exaBoxNode(get_gcontext())
        if aUser:
            _node.mSetUser(aUser)
            _node.mSetMaxRetries(self.mGetHandlerInstance().mGetMaxNumberofSshRetries())
        try:
            # ECRA request ID. This value is used to identify the db system details json file
            _ecra_request_id = self.mGetHandlerInstance().mGetMasterReqId()
            _node.mConnect(aHost=aVM)
            _exacloud_pre_patch_pdb_states_file = f"{self.mGetHandlerInstance().mGetLogPath()}/{aVM}_pre_patch_pdb_states"
            _exacloud_post_patch_pdb_states_file = f"{self.mGetHandlerInstance().mGetLogPath()}/{aVM}_post_patch_pdb_states"
            _pdb_metadata_file_location = EXADATA_TMP_VAR_LOG_LOCATION
            if aUser:
                _pdb_metadata_file_location = "/tmp"
                _vm_pre_patch_pdb_states_file = f"{_pdb_metadata_file_location}/{_ecra_request_id}_pre_patch_pdb_states"
                _vm_post_patch_pdb_states_file = f"{_pdb_metadata_file_location}/{_ecra_request_id}_post_patch_pdb_states"
            else:
                _vm_pre_patch_pdb_states_file = f"{_pdb_metadata_file_location}/{_ecra_request_id}_pre_patch_pdb_states"
                _vm_post_patch_pdb_states_file = f"{_pdb_metadata_file_location}/{_ecra_request_id}_post_patch_pdb_states"

            self.mPatchLogInfo(
                f"Pdb state file locations are : pre state file location on VM is {_vm_pre_patch_pdb_states_file} and "
                f"on exacloud is {_exacloud_pre_patch_pdb_states_file} , post state file location on VM is "
                f"{_vm_post_patch_pdb_states_file} and on exacloud is {_exacloud_post_patch_pdb_states_file} ")

            _pre_json_exists = False
            _post_json_exists = False

            _pre_json_exists = _node.mFileExists(_vm_pre_patch_pdb_states_file)
            if _pre_json_exists:
                self.mPatchLogInfo(f"Copying pre pdb state file {_vm_pre_patch_pdb_states_file} to exacloud")
                _node.mCopy2Local(_vm_pre_patch_pdb_states_file, _exacloud_pre_patch_pdb_states_file)

            _post_json_exists = _node.mFileExists(_vm_post_patch_pdb_states_file)
            if _post_json_exists:
                self.mPatchLogInfo(f"Copying post pdb state file {_vm_post_patch_pdb_states_file} to exacloud")
                _node.mCopy2Local(_vm_post_patch_pdb_states_file, _exacloud_post_patch_pdb_states_file)

            if _pre_json_exists and _post_json_exists:
                _pre_patch_pdb_state_json = None
                _post_patch_pdb_state_json = None
                _pre_patch_db_system_details_str = None
                _post_patch_db_system_details_str = None

                with open(_exacloud_pre_patch_pdb_states_file) as fd:
                    _pre_patch_db_system_details_str = fd.read()
                _pre_patch_pdb_state_json = self.mGetJSONFromDbaascliCmdOutput(_pre_patch_db_system_details_str)

                with open(_exacloud_post_patch_pdb_states_file) as fd:
                    _post_patch_db_system_details_str = fd.read()
                _post_patch_pdb_state_json = self.mGetJSONFromDbaascliCmdOutput(_post_patch_db_system_details_str)

                _ret, _sug_msg, _pdb_status_dict = self.mComparePreAndPostPatchPDBSystemDetailsJson(
                    _pre_patch_pdb_state_json,
                    _post_patch_pdb_state_json, aVM)

                _node.mExecuteCmdLog(f"rm -f {_pdb_metadata_file_location}/*_patch_pdb_states")
            else:
                self.mPatchLogInfo(
                    f"Comparison cannot be done because either pre json ({str(_pre_json_exists)}) or post json ({str(_post_json_exists)}) does not exist")

        except Exception as e:
            self.mPatchLogWarn(
                f"Exception occurred while getting dbsystem details using dbaascli on VM node {aVM}. Error : {str(e)}")
            self.mPatchLogError(traceback.format_exc())
            _sug_msg = "Unable to get db system details to read PDB details to detect pdb degradation state"
            _ret = PDB_FETCH_DETAILS_ERROR
            if self.mGetHandlerInstance().mGetCurrentTargetType() == PATCH_DOM0:
                _ret = DOM0_PATCHING_DB_HEALTHCHECKS_PDB_FETCH_DETAILS_ERROR
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()

        if _ret != PATCH_SUCCESS_EXIT_CODE:
            self.mGetHandlerInstance().mAddError(_ret, _sug_msg)
        self.mPatchLogInfo(
            f"mValidatePreAndPostPatchPDBSystemDetailsForDegradation return value is {str(_ret)}")
        return _ret, _pdb_status_dict

    def mComparePreAndPostPatchPDBSystemDetailsJson(self, aPreJson, aPostJson, aVM):
        """
        :param aPreJson: db system details json content prior to patch
        :param aPostJson: db system details json content post patch
        :param aVM: VM name on which pdb state degradation need to be checked
        :return: PATCH_SUCCESS_EXIT_CODE on success otherwise PDB_IN_DEGRADED_STATE

        This method compares pdb state on the vm both in pre patch and post patch and return
        PDB_IN_DEGRADED_STATE if there is degradation

        Explanation:
        -----------

        This table represents pre-patch and post-patch openmode and restricted states and DEGRADED STATE coloumn indicates
        whether these state transistions are considered as DEGRADED or not

            PDB_PRE_OPENMODE_STATE	PRE_PDB_RESTRICTED_STATE   PDB_POST_OPENMODE_STATE  POST_PDB_RESTRICTED_STATE DEGRADED STATE
            ---------------------------------------------------------------------------------------------------------------------
            READ_WRITE              false                      READ_WRITE               false                      No
            READ_WRITE              false                      READ_WRITE               true                       Yes
            READ_WRITE              true                       READ_WRITE               true                       No
            READ_WRITE              true                       READ_WRITE               false                      Yes
            READ_WRITE              *                          READ                     *                          Yes
            READ_WRITE              *                          MOUNT                    *                          Yes
            READ                    false                      READ                     false                      No
            READ                    false                      READ                     true                       Yes
            READ                    true                       READ                     false                      Yes
            READ                    true                       READ                     true                       No
            READ                    false                      READ_WRITE               false                      No
            READ                    false                      READ_WRITE               true                       Yes
            READ                    true                       READ_WRITE               false                      Yes
            READ                    true                       READ_WRITE               true                       No
            READ                    *                          MOUNT                    *                          Yes
            MOUNT                   *                          MOUNT            	*                          No
            MOUNT                   *                          ~[MOUNT]       		*                          Yes
            MIGRATE                 *                          MIGRATE       		*                          No
            MIGRATE                 *                          ~[MIGRATE]       	*                          Yes

            Note:
                The '*' symbol represents any value of restricted ( it can be True or False)

        Pre json/Post json has the below format:
        ----------------------------------------
        {

            "orclcdb": {
              "id": "ca67d685-7ce7-4963-9e98-291fc9b68882",
              "dbSyncTime": 1717660575640,
              "createTime": 1712054111010,
              "updateTime": 0,
              "dbName": "orclcdb",
              "dbUniqueName": "orclcdb",
              "dbDomain": "us.oracle.com",
              "dbNodeLevelDetails": {
                "scaqag01dv0601m": {
                  "nodeName": "scaqag01dv0601m",
                  "instanceName": "orclcdb2",
                  "version": "19.22.0.0.0",
                  "homePath": "/u02/app/oracle/product/19.0.0.0/dbhome_1",
                  "status": "OPEN"
                },
                "scaqag01dv0501m": {
                  "nodeName": "scaqag01dv0501m",
                  "instanceName": "orclcdb1",
                  "version": "19.22.0.0.0",
                  "homePath": "/u02/app/oracle/product/19.0.0.0/dbhome_1",
                  "status": "OPEN"
                }
              },
              "pdbs": {
                "ORCLPDB": {
                  "pdbName": "ORCLPDB",
                  "pdbUID": "40819901",
                  "createTime": 1712054806000,
                  "cdbId": "ca67d685-7ce7-5963-9e98-291fc9b68882",
                  "refreshablePDB": false,
                  "refreshMode": null,
                  "refreshIntervalInMinutes": null,
                  "pdbNodeLevelDetails": {
                    "scaqag01dv0601m": {
                      "nodeName": "scaqag01dv0601m",
                      "openMode": "READ_WRITE",
                      "restricted": false
                    },
                    "scaqag01dv0501m": {
                      "nodeName": "scaqag01dv0501m",
                      "openMode": "READ_WRITE",
                      "restricted": false
                    }
                  }
                }
              },
              "messages": []
            }
        }

        """
        _vm = None
        _error_msg = ""
        _pdb_status_dict = {}
        _is_dom0_patching = True if self.mGetHandlerInstance().mGetCurrentTargetType() == PATCH_DOM0 else False
        _ret_pdb_degraded_error = DOM0_PATCHING_DB_HEALTHCHECKS_PDB_IN_DEGRADED_STATE if _is_dom0_patching else PDB_IN_DEGRADED_STATE
        if aVM:
            _vm_customer_hostname = self.mGetHandlerInstance().mGetDomUCustomerNameforDomuNatHostName(aVM)
            _vm = _vm_customer_hostname.split('.')[0]

        def _compare_hostnames(aHostName, aHostNameInJson):
            """
            This internal method compares the vm name with hostname present in db system details json. The vm name in
            db system details json can be FQDN or hostname without any domain name
            """
            return aHostName in [aHostNameInJson, aHostNameInJson.split('.')[0]]

        self.mPatchLogInfo(f"mComparePreAndPostPatchPDBSystemDetailsJson begins for the VM {aVM}")

        # databases metadata is not present in dbsystem details json in the pre patch stage itself
        if aPreJson is None:
            self.mPatchLogInfo("No databases data is present in pre patch json so returning success")
            return PATCH_SUCCESS_EXIT_CODE, _error_msg, _pdb_status_dict

        # databases details are present prior to patching but post patching those details are not present so failing
        if aPostJson is None:
            _error_msg = "databases details are missing in db system details json post patching."
            self.mPatchLogError(_error_msg)
            _pdb_status_dict["error"] = _error_msg
            return _ret_pdb_degraded_error, _error_msg, _pdb_status_dict

        # iterate through each cdb
        for _cdb_name, _cdb_info in aPreJson.items():
            if "pdbs" in _cdb_info:
                _pre_patch_pdb_info = _cdb_info.get("pdbs")
                # non cdb environment pdb values can be null
                if _pre_patch_pdb_info:
                    for _pdb_name, _pdb_info in _cdb_info["pdbs"].items():
                        for _vm_name, _vm_info in _pdb_info["pdbNodeLevelDetails"].items():

                            # If VM name is provided, do the comparison for that specific vm otherwise compare for all
                            if _vm is not None and not _compare_hostnames(_vm, _vm_name):
                                continue

                            _pre_restricted = _vm_info["restricted"]
                            _pre_openmode = _vm_info["openMode"]

                            if "pdbs" in aPostJson[_cdb_name] and _pdb_name in aPostJson[_cdb_name]["pdbs"] and \
                                    "pdbNodeLevelDetails" in aPostJson[_cdb_name]["pdbs"][_pdb_name]:
                                _post_pdb_vm_info = None
                                if _vm_name in aPostJson[_cdb_name]["pdbs"][_pdb_name]["pdbNodeLevelDetails"]:
                                    _post_pdb_vm_info = aPostJson[_cdb_name]["pdbs"][_pdb_name]["pdbNodeLevelDetails"][
                                        _vm_name]
                                else:
                                    _error_msg = f"PDB node details are missing for PDB {_pdb_name} within CDB {_cdb_name} on VM - {_vm_name}."
                                    self.mPatchLogError(_error_msg)
                                    _pdb_status_dict["error"] = _error_msg
                                    return _ret_pdb_degraded_error, _error_msg, _pdb_status_dict

                                _post_restricted = _post_pdb_vm_info["restricted"]
                                _post_openmode = _post_pdb_vm_info["openMode"]

                                _is_pdb_degraded = self.mIsPDBDegraded(_pre_openmode, _pre_restricted, _post_openmode,
                                                                       _post_restricted)
                                if _is_pdb_degraded:
                                    _error_msg = f"PDB {_pdb_name} within CDB {_cdb_name} is in degraded state on VM - {_vm_name}, prior to " \
                                                 f"patching it is in {_pre_openmode} state with restr" \
                                                 f"icted set to {str(_pre_restricted)}, where as post patching it is " \
                                                 f"in {_post_openmode} state with restricted set to " \
                                                 f"{str(_post_restricted)}."
                                    self.mPatchLogError(_error_msg)
                                    _pdb_status_dict = {"error": "degradation", "pdb": _pdb_name, "cdb": _cdb_name,
                                                        "pre_openmode": _pre_openmode, "post_openmode": _post_openmode,
                                                        "pre_restricted": _pre_restricted,
                                                        "post_restricted": _post_restricted}

                                    return _ret_pdb_degraded_error, _error_msg, _pdb_status_dict
                            else:
                                _error_msg = f"PDB details are missing for PDB {_pdb_name} within CDB {_cdb_name} on VM - {_vm_name}."
                                self.mPatchLogError(_error_msg)
                                _pdb_status_dict["error"] = _error_msg
                                return _ret_pdb_degraded_error, _error_msg, _pdb_status_dict
                else:
                    # here pdbs key is present but value is null
                    self.mPatchLogInfo("No pdbs present in pre patch json so returning success")
            else:
                self.mPatchLogInfo("No pdbs present in pre patch json so returning success")

        return PATCH_SUCCESS_EXIT_CODE, _error_msg, _pdb_status_dict

    def mCheckCDBPDBHealthPostPatch(self, aDomu, aIsRetry=False):
        """
        :param aDomu: VM name on which cdb/pdb healthchecks need to be performed
        :param aIsRetry: Whether this request is retry request
        :return: PATCH_SUCCESS_EXIT_CODE on success otherwise error code corresponding to cdb/pdb healthchecks

        This method executes both CDB and PDB healthchecks.
        1. First it performs CDB healthchecks.
          a) If the CDB healthchecks are not successful, it loops for 10 minutes with 1-minute sleep interval.
          b) If CDB healthchecks are successful, it means CDB/CRS services are up and running, so it proceeds to PDB healthchecks
        2. In the PDB healtchecks, it first fetches the json using dbaascli and compares the PDB meatadata to detect any degraded state
        """

        _enable_cdb_degradation_check = self.mGetHandlerInstance().mGetInfrapatchExecutionValidator().mCheckCondition(
            'mIsCDBDegradationCheckEnabled')

        _ret = PATCH_SUCCESS_EXIT_CODE
        if _enable_cdb_degradation_check:
            self.mPatchLogInfo("CDB degradation check started.")
            _db_healthchecks_wait_time = self.mGetHandlerInstance().mGetDBHealthChecksWaitTimeInSeconds()
            _starttime = time()
            _elapsed = 0
            _iteration = 0
            _sanity_chek_log_name = f"{self.mGetHandlerInstance().mGetLogPath()}/{DBAASAPI_SANITY_CHECK_LOG}"
            _sanity_check_log_on_remote_node = f"{DBAASAPI_SANITY_CHECK_LOG_PATH}/{DBAASAPI_SANITY_CHECK_LOG}"
            while _elapsed < _db_healthchecks_wait_time:
                _iteration = _iteration + 1
                sleep(60)
                _ret, _ = self.mExecuteInfraPostSanityCheck(aDomu)

                _elapsed = time() - _starttime
                if _ret == PATCH_SUCCESS_EXIT_CODE:
                    self.mPatchLogInfo(
                        f'mCheckCDBPDBHealthPostPatch: Completed CDB healtchecks of the VM: {aDomu}, elapsed time: {_elapsed}')
                    break

                self.mGetHandlerInstance().mCopyFileFromRemote(aDomu, _sanity_check_log_on_remote_node,
                                                  f"{_sanity_chek_log_name}.{_iteration:d}")

                self.mPatchLogInfo(
                    f'mCheckCDBPDBHealthPostPatch: Waiting for completion of CDB healtchecks of the VM: {aDomu}, iteration {_iteration} time elapsed: {_elapsed}')

            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError("CDB healthcheck has returned non zero exit status")
                self.mPatchLogInfo(
                    f"Copying {_sanity_check_log_on_remote_node} from remote node {aDomu} to {_sanity_chek_log_name}.{_iteration:d}")
                self.mGetHandlerInstance().mCopyFileFromRemote(aDomu, _sanity_check_log_on_remote_node,
                                                  f"{_sanity_chek_log_name}.{_iteration:d}")
                return _ret

            self.mPatchLogInfo("CDB degradation check completed.")
        else:
            self.mPatchLogInfo("CDB degradation check is not run as enable_cdb_degradation_check is False.")

        _enable_pdb_degradation_check = self.mGetHandlerInstance().mGetInfrapatchExecutionValidator().mCheckCondition(
            'mIsPDBDegradationCheckEnabled')
        # If cdb degradation check is successful then only we can do pdb degradation check
        if _enable_pdb_degradation_check:
            self.mPatchLogInfo("PDB degradation check started.")
            _ret, _ = self.mValidateForPDBDegradation(aDomu, aIsRetry)
            self.mPatchLogInfo("PDB degradation check completed.")
        else:
            self.mPatchLogInfo("PDB degradation check is not run as enable_pdb_degradation_check is False.")
        return _ret

    def mIsPDBDegraded(self, aPrePatchOpenMode, aPrePatchRestricted, aPostPatchOpenMode, aPostPatchRestricted):
        """
        This method provides flexible way to determine if PDB is in degraded state based on specified conditions, returns False
        if no match found in the provided matrix
        """
        _pdb_degraded_states_matrix = mGetPdbDegradedStatesMatrix()
        """
        The below matrix represents the conditions for determining if a PDB is degraded

        Each row corresponds to a specif combination of:
        [pre_patch_openmode, pre_patch_restricted,post_patch_openmode, post_patch_restricted, is_pdb_in_degraded]
        The '*' symbol represents any value of restricted ( it can be True or False) 

        Note: If the conditions do not match any row in the matrix, pdb is not in degraded state
        """
        if _pdb_degraded_states_matrix:
            # First, check for exact match with all the four input values
            for row in _pdb_degraded_states_matrix:
                if row[0] == aPrePatchOpenMode and row[1] == aPrePatchRestricted and row[2] == aPostPatchOpenMode and \
                        row[3] == aPostPatchRestricted:
                    self.mPatchLogInfo(
                        f"mIsPDBDegraded : matches exact condition, values are {aPrePatchOpenMode}-{str(aPrePatchRestricted)}-{aPostPatchOpenMode}-{str(aPostPatchRestricted)} and result is {str(row[4])} ")
                    return row[4]

            # If no exact match is found, check for matches with '*' in 2nd and 4th columns
            # eg:  ["READ_WRITE", "*", "READ", "*", True],
            for row in _pdb_degraded_states_matrix:
                if row[0] == aPrePatchOpenMode and row[2] == aPostPatchOpenMode and row[1] == "*" and row[3] == "*":
                    self.mPatchLogInfo(
                        f"mIsPDBDegraded : matches with * condition, values are {aPrePatchOpenMode}-{str(aPrePatchRestricted)}-{aPostPatchOpenMode}-{str(aPostPatchRestricted)} and result is {str(row[4])} ")
                    return row[4]

            # If no match is found, return False indicating pdb is not in degraded state
            self.mPatchLogInfo(
                f"mIsPDBDegraded : No match found values are {aPrePatchOpenMode}-{str(aPrePatchRestricted)}-{aPostPatchOpenMode}-{str(aPostPatchRestricted)} and result is {'False'} ")
        else:
            self.mPatchLogInfo("mIsPDBDegraded : pdb_degraded_states_matrix is empty so returning False")

        return False

    def mValidateForPDBDegradation(self, aVM, aIsRetry, aUser=None):
        """
        :param aVM: VM name on which db system details json values are compared to detect pdb state degradation
        :param aIsRetry: Boolean value indicating that request is a retry request
        :param aUser: user context with which ssh connection would be done to connect to VM nodes
        :return:  PATCH_SUCCESS_EXIT_CODE on success otherwise PDB_IN_DEGRADED_STATE or PDB_FETCH_DETAILS_ERROR

        This method does the following
        1. Fetch DB system details json
        2. Compare pre and post db system details json for PDB degradation
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _pdb_status_dict = {}
        _enable_pdb_degradation_check = self.mGetHandlerInstance().mGetInfrapatchExecutionValidator().mCheckCondition(
            'mIsPDBDegradationCheckEnabled')
        if _enable_pdb_degradation_check:
            _ret = self.mFetchAndStoreDBSystemDetailsToFile(aVM, "post", aIsRetry, aUser=aUser)
            if _ret == PATCH_SUCCESS_EXIT_CODE:
                _ret, _pdb_status_dict = self.mValidatePreAndPostPatchPDBSystemDetailsForDegradation(aVM, aUser=aUser)
            return _ret, _pdb_status_dict

    def mDetectPDBDowntime(self, aVM, aUser=None):
        """
        :param aVM: VM name on which db system details json values are parsed to detect pdb downtime
        :param aUser: user context with which ssh connection would be done to connect to VM nodes
        :return: PATCH_SUCCESS_EXIT_CODE on success otherwise VM_OS_PATCH_WILL_CAUSE_DOWNTIME or PDB_FETCH_DETAILS_ERROR

        This method does two things as part of the execution
        1. Copy the dbsystemdetails.json to exacloud location
        2. Parse dbsystemdetails.json to detect patching the current node would lead to downtime

        Note:
        If pdb is in restricted mode in all of the nodes or  pdb is not in restricted mode in any of the nodes then proceed with patching
        If there is a mix of restricted true and restricted false then do not proceed with patching.
        If one node is in restricted mode, then rebooting the other node which is not in restricted mode, may also cause the PDB get into restricted mode after OS patching so stopping the patching is suggested.

        PDB downtime check is performed only on PRIMARY nodes and not on STANDBY nodes(So in DataGuard env, this check is performed on PRIMARY only)

        db system details json:
        ----------------------
        {
          "databases": {
            "orclcdb": {
              "id": "ca67d685-7ce7-4963-9e98-291fc9b68782",
              "dbSyncTime": 1717660575630,
              "createTime": 1712054111000,
              "updateTime": 0,
              "dbName": "orclcdb",
              "dbUniqueName": "orclcdb",
              "dbDomain": "us.oracle.com",
              "dbNodeLevelDetails": {
                "scaqag01dv0601m": {
                  "nodeName": "scaqag01dv0601m",
                  "instanceName": "orclcdb2",
                  "version": "19.22.0.0.0",
                  "homePath": "/u02/app/oracle/product/19.0.0.0/dbhome_1",
                  "status": "OPEN"
                },
                "scaqag01dv0501m": {
                  "nodeName": "scaqag01dv0501m",
                  "instanceName": "orclcdb1",
                  "version": "19.22.0.0.0",
                  "homePath": "/u02/app/oracle/product/19.0.0.0/dbhome_1",
                  "status": "OPEN"
                }
              },
              "pdbs": {
                "ORCLPDB": {
                  "pdbName": "ORCLPDB",
                  "pdbUID": "408199009",
                  "createTime": 1712054809000,
                  "cdbId": "ca67d685-7ce6-4963-9e98-291fc9b68882",
                  "refreshablePDB": false,
                  "refreshMode": null,
                  "refreshIntervalInMinutes": null,
                  "pdbNodeLevelDetails": {
                    "scaqag01dv0601m": {
                      "nodeName": "scaqag01dv0601m",
                      "openMode": "READ_WRITE",
                      "restricted": false
                    },
                    "scaqag01dv0501m": {
                      "nodeName": "scaqag01dv0501m",
                      "openMode": "READ_WRITE",
                      "restricted": false
                    }
                  }
                }
              },
              "messages": []
            }
        }

        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _sug_msg = ""
        _affected_pdb_cdb_names = {}
        _is_dom0_patching = True if self.mGetHandlerInstance().mGetCurrentTargetType() == PATCH_DOM0 else False
        _ret_fetch_error = DOM0_PATCHING_DB_HEALTHCHECKS_PDB_FETCH_DETAILS_ERROR if _is_dom0_patching else PDB_FETCH_DETAILS_ERROR
        _node = exaBoxNode(get_gcontext())

        # By default aUser is None.
        if aUser:
            _node.mSetUser("opc")
            _node.mSetMaxRetries(self.mGetHandlerInstance().mGetMaxNumberofSshRetries())
        try:
            """
            Step1: Copy dbsystemdetails.json to exacloud location 
            """
            # ECRA request ID. This value is used to identify the db system details json file
            _ecra_request_id = self.mGetHandlerInstance().mGetMasterReqId()
            _node.mConnect(aHost=aVM)
            _exacloud_pre_patch_pdb_states_file = f"{self.mGetHandlerInstance().mGetLogPath()}/{aVM}_pre_patch_pdb_states"
            _vm_pre_patch_pdb_states_file = None

            if aUser:
                _vm_pre_patch_pdb_states_file = f"{'/tmp'}/{_ecra_request_id}_pre_patch_pdb_states"
            else:
                _vm_pre_patch_pdb_states_file = f"{EXADATA_TMP_VAR_LOG_LOCATION}/{_ecra_request_id}_pre_patch_pdb_states"

            if _node.mFileExists(_vm_pre_patch_pdb_states_file):
                self.mPatchLogInfo("Copying pdb state files to exacloud")
                _node.mCopy2Local(_vm_pre_patch_pdb_states_file, _exacloud_pre_patch_pdb_states_file)
                self.mPatchLogInfo("Copying pdb state files to exacloud completed")

                """
                Step2: Parse dbsystemdetails json to detect downtime
                """
                _pre_patch_pdb_state_json = None
                _pre_patch_db_system_details_str = None

                with open(_exacloud_pre_patch_pdb_states_file) as fd:
                    _pre_patch_db_system_details_str = fd.read()
                _pre_patch_pdb_state_json = self.mGetJSONFromDbaascliCmdOutput(_pre_patch_db_system_details_str)

                _vm = None
                _error_msg = ""
                if aVM:
                    _vm_customer_hostname = self.mGetHandlerInstance().mGetDomUCustomerNameforDomuNatHostName(aVM)
                    _vm = _vm_customer_hostname.split('.')[0]

                def _compare_hostnames(aHostName, aHostNameInJson):
                    """
                    This internal method compares the vm name with hostname present in db system details json. The vm name in
                    db system details json can be FQDN or hostname without any domain name
                    """
                    return aHostName in [aHostNameInJson, aHostNameInJson.split('.')[0]]

                # If no databases are present, no need to do parse pdb metadata
                if _pre_patch_pdb_state_json is None:
                    self.mPatchLogInfo("No pdb metadata is present")
                    return PATCH_SUCCESS_EXIT_CODE, _affected_pdb_cdb_names

                    # iterate through each cdb
                for _cdb_name, _cdb_info in _pre_patch_pdb_state_json.items():
                    if _cdb_info["dbRole"] != "PRIMARY":
                        self.mPatchLogInfo(
                            f"PDB downtime check is not executed if the dbRole is not primary. Here the dbRole is {_cdb_info['dbRole']} for the db {_cdb_name}")
                        continue
                    if "pdbs" in _cdb_info:
                        _pre_patch_pdb_info = _cdb_info.get("pdbs")
                        # non cdb environment pdb values can be null
                        if _pre_patch_pdb_info:
                            for _pdb_name, _pdb_info in _cdb_info["pdbs"].items():

                                # If it is single node PDB, dont throw error
                                if len(_pdb_info["pdbNodeLevelDetails"]) == 1:
                                    self.mPatchLogInfo(f"pdb - {_pdb_name} within CBD {_cdb_name} has one vm")
                                    continue

                                # If it is single node PDB, dont throw error
                                if len(_pdb_info["pdbNodeLevelDetails"]) == 0:
                                    _sug_msg = f"VM details are missing for the pdb - {_pdb_name} within the CDB {_cdb_name} in db system details json to detect pdb downtime."
                                    self.mPatchLogError(_sug_msg)
                                    _affected_pdb_cdb_names = {"error": _sug_msg}
                                    _ret = _ret_fetch_error 
                                    break

                                """
                                 If there is mix of restricted True and restricted False, then do not proceed with patching 
                                 If all the nodes are either restricted True or all restricted False, then proceed with patching 
                                """
                                _restricted_values_set = set()
                                for _vm_metadata in _pdb_info["pdbNodeLevelDetails"].values():
                                    _restricted_values_set.add(_vm_metadata["restricted"])

                                """
                                If there is mix of restricted True and restricted False, then do not proceed with patching
                                """
                                if len(_restricted_values_set) > 1:
                                    _sug_msg = f"{_pdb_name} within CDB {_cdb_name} is in restricted state in some of the nodes and while in other nodes in non-restricted state, So patching is stopped in {aVM} to fix inconsistencies"
                                    self.mPatchLogError(_sug_msg)
                                    _affected_pdb_cdb_names = {"error": "downtime", "pdb": _pdb_name, "cdb": _cdb_name}
                                    _ret = DOM0_PATCHING_DB_HEALTHCHECKS_VM_OS_REBOOT_WILL_CAUSE_DOWNTIME if _is_dom0_patching else VM_OS_PATCH_WILL_CAUSE_DOWNTIME
                                    break
                                else:
                                    _restricted_value = _restricted_values_set.pop()
                                    if _restricted_value:
                                        self.mPatchLogWarn(
                                            f"PDB {_pdb_name} within CDB {_cdb_name} is in restricted mode in all of the vms so continuing..")
                                    if not _restricted_value:
                                        self.mPatchLogWarn(
                                            f"PDB {_pdb_name} within CDB {_cdb_name} is in non-restricted mode in all of the vms so continuing..")

                        else:
                            # here pdbs key is present but value is null
                            self.mPatchLogInfo(
                                f"No pdbs info is empty in db system details json for the db -{_cdb_name} ")
                    else:
                        self.mPatchLogInfo(f"No pdbs present in db system details json for the db -{_cdb_name} ")

                    if _ret != PATCH_SUCCESS_EXIT_CODE:
                        break
            else:
                self.mPatchLogError(
                    f"File {_vm_pre_patch_pdb_states_file} does not exist on the remote node {aVM} so failing as db "
                    f"system details json value are not available to determine pdb downtime")
                _sug_msg = f"Error occured while fetching db system details on the vm -{aVM}"
                _affected_pdb_cdb_names = {"error": _sug_msg}
                _ret = _ret_fetch_error

        except Exception as e:
            self.mPatchLogWarn(
                "Exception occurred while fetching or parsing dbsystem details for the VM %s. Error : %s" % (
                    aVM, str(e)))
            _ret = _ret_fetch_error
            _sug_msg = f"Exception occurred while processing for dbsystemdetails json for the VM {aVM} "
            _affected_pdb_cdb_names = {"error": _sug_msg}
            self.mPatchLogError(traceback.format_exc())
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()

        if _ret != PATCH_SUCCESS_EXIT_CODE:
            self.mGetHandlerInstance().mAddError(_ret, _sug_msg)
        self.mPatchLogInfo(f"mDetectPDBDowntime return with {str(_ret)}")
        return _ret, _affected_pdb_cdb_names

    def mGetJSONFromDbaascliCmdOutput(self, aCmdOutput):
        """
        dbaascli command output is of the below format so will be extracting the json between "Start of output" and "End of output" marker lines

        [root@kacastro1 opc]# dbaascli system getDatabases --reload --showOutputDelimiter
        DBAAS CLI version 24.4.1.0.0
        Executing command system getDatabases --reload --showOutputDelimiter
        Job id: 6e034981-837d-4a59-8059-8c8b8768d1c5
        Session log: /var/opt/oracle/log/system/getDatabases/dbaastools_2024-11-26_03-36-11-AM_183954.log
        =========Start of output ============
        {
        ...
        }
        =========End of output ============

        dbaascli execution completed
        """
        _parsed_json = None

        if aCmdOutput:
            _lines = aCmdOutput.splitlines()
            _json_lines = []
            _in_json = False

            for _line in _lines:
                # Check for "Start of output" in _line
                if "Start of output" in _line:
                    _in_json = True
                    continue  # skip the "Start of output" line itself
                if "End of output" in _line:
                    _in_json = False
                    break  # stop collecting after this line

                # If we are in json, collect the line
                if _in_json:
                    _json_lines.append(_line)

            _json_content = "\n".join(_json_lines)
            try:
                _parsed_json = json.loads(_json_content)
            except Exception as e:
                self.mPatchLogWarn(f"Exception {str(e)} occurred while parsing for json from dbaascli command output")
        return _parsed_json

    def mDetectCDBDowntimeDuringDom0Patching(self, aDom0, aDomUList):
        """
        :param aDom0: dom0 node on which patching happens
        :param aDomUList: VM node list - contains customerhostnames
        :return: PATCH_SUCCESS_EXIT_CODE on success otherwise DOM0_PATCHING_DB_HEALTHCHECKS_CRS_RESOURCES_ARE_DOWN or DOMU_DBAASAPI_COMMAND_FAILED

        Note:
            1. mExecuteInfraPreSanityCheck in called parallely on all the vms here
            2. For EXACS, opc user and for EXACC root user keys are injected to connect to VM nodes
        """
        _cdb_downtime_detection_vm_list = []
        _ret = PATCH_SUCCESS_EXIT_CODE
        _suggestion_msg = ""

        _user = None

        _enable_health_checks_from_cp = self.mGetHandlerInstance().mGetInfrapatchExecutionValidator().mCheckCondition(
            'mEnableDBHealthChecks')
        _enable_cdb_downtime_check = self.mGetHandlerInstance().mGetInfrapatchExecutionValidator().mCheckCondition(
            'mIsCDBDowntimeCheckEnabled')

        if _enable_health_checks_from_cp and _enable_cdb_downtime_check:
            try:
                def _detect_cdbdowntime_during_dom0_patching(_domu_customer_hostname, aStatus):
                    _downtime_expected_res = []
                    _domu_node = self.mGetHandlerInstance().mGetDomUNatHostNameforDomuCustomerHostName(
                        _domu_customer_hostname)

                    _user = self.mGetHandlerInstance().mGetUserDetailsBasedOnDomUhostname(_domu_node)
                    # Default to None in case of _user is not opc.
                    _user = "opc" if _user == "opc" else None

                    _rc, _downtime_expected_res = self.mExecuteInfraPreSanityCheck(_domu_node, aUser=_user)
                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                        _sanity_check_log_on_remote_node = f"{DBAASAPI_SANITY_CHECK_LOG_PATH}/{DBAASAPI_SANITY_CHECK_LOG}"
                        _sanity_check_log_local_path = f"{self.mGetHandlerInstance().mGetLogPath()}/{_domu_node}_{DBAASAPI_SANITY_CHECK_LOG}"
                        self.mPatchLogInfo(
                            f"Copying {_sanity_check_log_on_remote_node} from remote node {_domu_node} to {_sanity_check_log_local_path}")
                        self.mGetHandlerInstance().mCopyFileFromRemote(_domu_node, _sanity_check_log_on_remote_node,
                                                                       _sanity_check_log_local_path, aCopytoTmp=True,
                                                                       aUser=_user)
                        aStatus.append({'domu': _domu_customer_hostname, 'status': 'failed', 'errorcode': _rc,
                                        'downtime_expected_resources': _downtime_expected_res})
                        self.mPatchLogError(f"cdb downtime detected on {_domu_customer_hostname}")

                # End of _detect_cdbdowntime_during_dom0_patching

                """
                 Parallelize execution on all target nodes.
                """
                _plist = ProcessManager()
                _rc_status = _plist.mGetManager().list()
                _non_autonomous_vm_list = [_non_autonomous_vm for _non_autonomous_vm in aDomUList if
                                           _non_autonomous_vm not in {_vm_name for _, _vms in
                                                                      self.mGetHandlerInstance().mGetAutonomousVMListWithCustomerHostnames()
                                                                      for _vm_name in _vms}]
                for _remote_node in _non_autonomous_vm_list:
                    _p = ProcessStructure(_detect_cdbdowntime_during_dom0_patching, [_remote_node, _rc_status],
                                          _remote_node)

                    '''
                     Timeout parameter configurable in Infrapatching.conf
                     Currently it is set to 60 minutes
                    '''
                    _p.mSetMaxExecutionTime(
                        self.mGetHandlerInstance().mGetDBHealthChecksParallelExecutionWaitTimeInSeconds())

                    _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
                    _p.mSetLogTimeoutFx(self.mPatchLogWarn)
                    _plist.mStartAppend(_p)

                _plist.mJoinProcess()

                if _plist.mGetStatus() == "killed":
                    _suggestion_msg = f"Timeout occured while validating for cdb downtime on the VM nodes of the dom0 {aDom0} "
                    _ret = DB_HEALTCHECKS_DETECTION_TIMEOUT_ERROR
                    self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)
                    return _ret

                # Error message handling start
                # validate the return codes
                _downtime_msg = ""
                _other_msg = ""
                for _rc_details in _rc_status:
                    if _rc_details['status'] == "failed":
                        if "downtime_expected_resources" in _rc_details and _rc_details["downtime_expected_resources"]:
                            if not _downtime_msg:
                                _downtime_msg = f"The following resource(s) will have complete downtime due to reboot of the vm(s) : "
                            _downtime_msg += f", ".join(_rc_details['downtime_expected_resources'])
                            _downtime_msg += f" on {_rc_details['domu']};"
                        else:
                            if not _other_msg:
                                _other_msg = "DB healthchecks could not be performed on the following vm(s): "
                            _other_msg += f"{_rc_details['domu']} ,"
                        _ret = _rc_details['errorcode']
                if _other_msg:
                    _other_msg = _other_msg[:-1]+"."
                _downtime_log_sug_msg = f" Please check the log /var/opt/oracle/log/sanity_check/sanity_check.log across vms for more details."
                _suggestion_msg += _downtime_msg
                _suggestion_msg += _other_msg
                _suggestion_msg += _downtime_log_sug_msg

                if _suggestion_msg and len(_suggestion_msg) > ERROR_MSG_TRUNCATE_LENGTH:
                    _suggestion_msg = mTruncateErrorMessageDescription(_suggestion_msg, aSuffixStr="..."+_downtime_log_sug_msg)

                # Error message handling end

            except Exception as e:
                _suggestion_msg = f"Exception {str(e)} occurred while validating for cdb downtime during {aDom0} patching"
                self.mPatchLogWarn(_suggestion_msg)
                _ret = DB_HEALTCHECKS_DETECTION_EXCEPTION_ENCOUNTERED
                self.mPatchLogTrace(traceback.format_exc())
        else:
            self.mPatchLogInfo(f"mEnableDBHealthChecks value is {str(_enable_health_checks_from_cp)} and "
                               f"mIsCDBDowntimeCheckEnabled value is {str(_enable_cdb_downtime_check)} so CDB "
                               f"downtime detection check is not run")
        if _ret != PATCH_SUCCESS_EXIT_CODE:
            self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)

        return _ret

    def mDetectCDBDegradationDuringDom0Patching(self, aDom0, aDomUList):
        """
        :param aDom0: dom0 node on which patching happened
        :param aDomUList: VM node list - contains customerhostnames
        :return: PATCH_SUCCESS_EXIT_CODE on success otherwise DOM0_PATCHING_DB_HEALTHCHECKS_CRS_RESOURCES_ARE_DOWN or DOMU_DBAASAPI_COMMAND_FAILED

        Note:
            1. mExecuteInfraPostSanityCheck in called parallely on all the vms here
            2. For EXACS, opc user and for EXACC root user keys are injected to connect to VM nodes
        """
        _cdb_degradation_failed_vm_list = []
        _ret = PATCH_SUCCESS_EXIT_CODE
        _suggestion_msg = ""
        _user = None

        _enable_health_checks_from_cp = self.mGetHandlerInstance().mGetInfrapatchExecutionValidator().mCheckCondition(
            'mEnableDBHealthChecks')
        _enable_cdb_degradation_check = self.mGetHandlerInstance().mGetInfrapatchExecutionValidator().mCheckCondition(
            'mIsCDBDegradationCheckEnabled')

        if _enable_health_checks_from_cp and _enable_cdb_degradation_check:
            try:
                def _detect_cdb_degradation_during_dom0_patching(_domu_customer_hostname, aStatus):
                    _domu_node = self.mGetHandlerInstance().mGetDomUNatHostNameforDomuCustomerHostName(
                        _domu_customer_hostname)
                    _rc = PATCH_SUCCESS_EXIT_CODE
                    _degraded_res = []
                    self.mPatchLogInfo(f"CDB degradation check started on {_domu_node}.")
                    _db_healthchecks_wait_time = self.mGetHandlerInstance().mGetDBHealthChecksWaitTimeInSeconds()
                    _starttime = time()
                    _elapsed = 0
                    _iteration = 0
                    _sanity_chek_log_name = f"{self.mGetHandlerInstance().mGetLogPath()}/{_domu_node}_{DBAASAPI_SANITY_CHECK_LOG}"
                    _sanity_check_log_on_remote_node = f"{DBAASAPI_SANITY_CHECK_LOG_PATH}/{DBAASAPI_SANITY_CHECK_LOG}"
                    self.mPatchLogInfo(
                        f"Start CDB healthchecks of the VM: [{_domu_node}] every {DBHEALTHCHECK_TIMEOUT_IN_SECONDS} seconds with a wait time of {_db_healthchecks_wait_time} seconds.")
                    while _elapsed < _db_healthchecks_wait_time:
                        _iteration = _iteration + 1
                        sleep(DBHEALTHCHECK_TIMEOUT_IN_SECONDS)
                        self.mPatchLogInfo(
                            f"**** DomU healthchecks are polled for another {DBHEALTHCHECK_TIMEOUT_IN_SECONDS} seconds and re-validated.")

                        _user = self.mGetHandlerInstance().mGetUserDetailsBasedOnDomUhostname(_domu_node)
                        # Default to None in case of _user is not opc.
                        _user = "opc" if _user == "opc" else None

                        _rc, _degraded_res = self.mExecuteInfraPostSanityCheck(_domu_node, aUser=_user)
                        _elapsed = time() - _starttime
                        if _rc == PATCH_SUCCESS_EXIT_CODE:
                            self.mPatchLogInfo(
                                f"mDetectCDBDegradationDuringDom0Patching: Completed CDB healtchecks of the VM: {_domu_node}, elapsed time: {str(_elapsed)}")
                            break

                        self.mGetHandlerInstance().mCopyFileFromRemote(_domu_node, _sanity_check_log_on_remote_node,
                                                                       f"{_sanity_chek_log_name}.{_iteration:d}",
                                                                       aCopytoTmp=True,
                                                                       aUser=_user)
                        self.mPatchLogInfo(
                            'mDetectCDBDegradationDuringDom0Patching: Waiting for completion of CDB healtchecks of the VM: {'
                            '0}, iteration {1} time elapsed: {2}'.format(_domu_node, _iteration, _elapsed))

                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                        self.mPatchLogError("CDB healthcheck has returned non zero exit status")
                        self.mPatchLogInfo(
                            f"Copying {_sanity_check_log_on_remote_node} from remote node {_domu_node} to {_sanity_chek_log_name}.{_iteration:d}")
                        self.mGetHandlerInstance().mCopyFileFromRemote(_domu_node, _sanity_check_log_on_remote_node,
                                                                       f"{_sanity_chek_log_name}.{_iteration:d}",
                                                                       aCopytoTmp=True,
                                                                       aUser=_user)
                        aStatus.append({'domu': _domu_customer_hostname, 'status': 'failed', 'errorcode': _rc, "degraded_resources":_degraded_res})
                        self.mPatchLogError(f"cdb degradation detected on {_domu_customer_hostname}")

                    self.mPatchLogInfo(f"CDB degradation check completed on {_domu_node}.")

                # End of _detect_cdb_degradation_during_dom0_patching

                """
                 Parallelize execution on all target nodes.
                """
                _plist = ProcessManager()
                _rc_status = _plist.mGetManager().list()

                _non_autonomous_vm_list = [_non_autonomous_vm for _non_autonomous_vm in aDomUList if
                                           _non_autonomous_vm not in {_vm_name for _, _vms in
                                                                      self.mGetHandlerInstance().mGetAutonomousVMListWithCustomerHostnames()
                                                                      for _vm_name in _vms}]
                for _remote_node in _non_autonomous_vm_list:
                    _p = ProcessStructure(_detect_cdb_degradation_during_dom0_patching, [_remote_node, _rc_status],
                                          _remote_node)

                    '''
                     Timeout parameter configurable in Infrapatching.conf
                     Currently it is set to 60 minutes
                    '''
                    _p.mSetMaxExecutionTime(
                        self.mGetHandlerInstance().mGetDBHealthChecksParallelExecutionWaitTimeInSeconds())

                    _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
                    _p.mSetLogTimeoutFx(self.mPatchLogWarn)
                    _plist.mStartAppend(_p)

                _plist.mJoinProcess()

                if _plist.mGetStatus() == "killed":
                    _suggestion_msg = f"Timeout occurred while validating for cdb downtime on the VM nodes of the dom0 {aDom0} "
                    _ret = DB_HEALTCHECKS_DETECTION_TIMEOUT_ERROR
                    self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)
                    return _ret

                # Error message handling start
                # validate the return codes
                _degraded_res_msg = ""
                _other_msg = ""
                for _rc_details in _rc_status:
                    if _rc_details['status'] == "failed":
                        if "degraded_resources" in _rc_details and _rc_details["degraded_resources"]:
                            if not _degraded_res_msg:
                                _degraded_res_msg = f"Post patching, the following resource(s) are down : "
                            _degraded_res_msg += f", ".join(_rc_details['degraded_resources'])
                            _degraded_res_msg += f" on {_rc_details['domu']};"
                        else:
                            if not _other_msg:
                                _other_msg = "DB healthchecks could not be performed on the following vm(s): "
                            _other_msg += f"{_rc_details['domu']} ,"
                        _ret = _rc_details['errorcode']
                if _other_msg:
                    _other_msg = _other_msg[:-1] + "."
                _degradation_log_sug_msg = f" Please check the log /var/opt/oracle/log/sanity_check/sanity_check.log across vms for more details."
                _suggestion_msg += _degraded_res_msg
                _suggestion_msg += _other_msg
                _suggestion_msg += _degradation_log_sug_msg

                if _suggestion_msg and len(_suggestion_msg) > ERROR_MSG_TRUNCATE_LENGTH:
                    _suggestion_msg = mTruncateErrorMessageDescription(_suggestion_msg, aSuffixStr="..."+_degradation_log_sug_msg)

                # Error message handling end

            except Exception as e:
                _suggestion_msg = f"Exception {str(e)} occurred while validating for cdb degradation during {aDom0} patching"
                self.mPatchLogWarn(_suggestion_msg)
                _ret = DB_HEALTCHECKS_DETECTION_EXCEPTION_ENCOUNTERED
                self.mPatchLogTrace(traceback.format_exc())
        else:
            self.mPatchLogInfo(f"mEnableDBHealthChecks value is {str(_enable_health_checks_from_cp)} and "
                               f"mIsCDBDegradationCheckEnabled value is {str(_enable_cdb_degradation_check)} so CDB "
                               f"downtime detection check is not run")
        if _ret != PATCH_SUCCESS_EXIT_CODE:
            self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)

        return _ret

    def mDetectPDBDowntimeDuringDom0Patching(self, aDom0, aDomUList):
        """
        :param aDom0: dom0 node on which patching happens
        :param aDomUList: VM node list - contains customerhostname
        :return: PATCH_SUCCESS_EXIT_CODE on success otherwise DOM0_PATCHING_DB_HEALTHCHECKS_VM_OS_REBOOT_WILL_CAUSE_DOWNTIME
                or DOM0_PATCHING_DB_HEALTHCHECKS_PDB_FETCH_DETAILS_ERROR

        Note:
            1. mDetectPDBDowntime in called parallely on all the vms here
            2. For EXACS, opc user and for EXACC root user keys are injected to connect to VM nodes
        """
        _pdb_downtime_detection_vm_list = []
        _ret = PATCH_SUCCESS_EXIT_CODE
        _suggestion_msg = ""
        _user = None

        _enable_health_checks_from_cp = self.mGetHandlerInstance().mGetInfrapatchExecutionValidator().mCheckCondition(
            'mEnableDBHealthChecks')
        _enable_pdb_downtime_check = self.mGetHandlerInstance().mGetInfrapatchExecutionValidator().mCheckCondition(
            'mIsPDBDowntimeCheckEnabled')
        _enable_pdb_degradation_check = self.mGetHandlerInstance().mGetInfrapatchExecutionValidator().mCheckCondition(
            'mIsPDBDegradationCheckEnabled')
        if _enable_health_checks_from_cp and (_enable_pdb_downtime_check or _enable_pdb_degradation_check):
            try:
                def _detect_pdb_downtime_during_dom0_patching(_domu_customer_hostname, aStatus):
                    _affected_pdb_cdb_names = {}
                    _domu_node = self.mGetHandlerInstance().mGetDomUNatHostNameforDomuCustomerHostName(
                        _domu_customer_hostname)

                    _user = self.mGetHandlerInstance().mGetUserDetailsBasedOnDomUhostname(_domu_node)
                    # Default to None in case of _user is not opc.
                    _user = "opc" if _user == "opc" else None

                    # Fetch dbsystem details json for post patch comparison to detect if pdb is in degraded state
                    _rc = self.mFetchAndStoreDBSystemDetailsToFile(_domu_node, "pre", aUser=_user)
                    if _rc == PATCH_SUCCESS_EXIT_CODE and _enable_pdb_downtime_check:
                        self.mPatchLogInfo("PDB downtime check started.")
                        _rc, _affected_pdb_cdb_names = self.mDetectPDBDowntime(_domu_node, aUser=_user)
                        self.mPatchLogInfo("PDB downtime check completed.")
                    else:
                        self.mPatchLogInfo("PDB downtime check is not run as enable_pdb_downtime_check is False.")

                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                        aStatus.append({'domu': _domu_customer_hostname, 'status': 'failed', 'errorcode': _rc,
                                        'pdb_error_details': _affected_pdb_cdb_names})
                        self.mPatchLogError(f"pdb downtime detected on {_domu_customer_hostname}")

                # End of _detect_pdb_downtime_during_dom0_patching

                """
                 Parallelize execution on all target nodes.
                """
                _plist = ProcessManager()
                _rc_status = _plist.mGetManager().list()

                _non_autonomous_vm_list = [_non_autonomous_vm for _non_autonomous_vm in aDomUList if
                                           _non_autonomous_vm not in {_vm_name for _, _vms in
                                                                      self.mGetHandlerInstance().mGetAutonomousVMListWithCustomerHostnames()
                                                                      for _vm_name in _vms}]
                for _remote_node in _non_autonomous_vm_list:
                    _p = ProcessStructure(_detect_pdb_downtime_during_dom0_patching, [_remote_node, _rc_status],
                                          _remote_node)

                    '''
                     Timeout parameter configurable in Infrapatching.conf
                     Currently it is set to 60 minutes
                    '''
                    _p.mSetMaxExecutionTime(
                        self.mGetHandlerInstance().mGetDBHealthChecksParallelExecutionWaitTimeInSeconds())

                    _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
                    _p.mSetLogTimeoutFx(self.mPatchLogWarn)
                    _plist.mStartAppend(_p)

                _plist.mJoinProcess()

                if _plist.mGetStatus() == "killed":
                    _suggestion_msg = f"Timeout occured while validating for cdb downtime on the VM nodes of the dom0 {aDom0}"
                    _ret = DB_HEALTCHECKS_DETECTION_TIMEOUT_ERROR
                    self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)
                    return _ret

                # Error message handling start
                _downtime_msgs = []
                _other_error_msgs = ""
                # validate the return codes
                for _rc_details in _rc_status:
                    if _rc_details['status'] == "failed":
                        _error_at_vm_level = _rc_details['pdb_error_details']
                        if 'error' in _error_at_vm_level:
                            if _error_at_vm_level['error'] == 'downtime':
                                _downtime_msgs.append(
                                    f"{_error_at_vm_level['pdb']} within {_error_at_vm_level['cdb']} on {_rc_details['domu']}")
                            else:
                                _other_error_msgs += _error_at_vm_level['error']
                        _ret = _rc_details['errorcode']

                if _other_error_msgs:
                    _suggestion_msg += _other_error_msgs

                if _downtime_msgs:
                    _suggestion_msg += "Patching is stopped to fix inconsistencies as certain pdbs within respective " \
                                       "cdbs are in restricted state on some VMs and non-restricted state on other. "
                    _suggestion_msg += ", ".join(_downtime_msgs)
                    _suggestion_msg += " showed such inconsistencies."

                _downtime_log_sug_msg = f" Please check pdb state values in /var/log/exadatatmp/{self.mGetHandlerInstance().mGetMasterReqId()}_pre_patch_pdb_states across all the vms and fix inconsistencies."
                _suggestion_msg += _downtime_log_sug_msg

                if _suggestion_msg and len(_suggestion_msg) > ERROR_MSG_TRUNCATE_LENGTH:
                    _suggestion_msg = mTruncateErrorMessageDescription(_suggestion_msg, aSuffixStr="..."+_downtime_log_sug_msg)

                # Error message handling end

            except Exception as e:
                _suggestion_msg = f"Exception {str(e)} occurred while validating for pdb downtime during {aDom0} patching "
                self.mPatchLogWarn(_suggestion_msg)
                _ret = DB_HEALTCHECKS_DETECTION_EXCEPTION_ENCOUNTERED
                self.mPatchLogTrace(traceback.format_exc())
        else:
            self.mPatchLogInfo(f"mEnableDBHealthChecks value is {str(_enable_health_checks_from_cp)} and "
                               f"mIsPDBDowntimeCheckEnabled value is {str(_enable_pdb_downtime_check)} so PDB "
                               f"downtime detection check is not run")
        if _ret != PATCH_SUCCESS_EXIT_CODE:
            self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)

        return _ret

    def mDetectPDBDegradationDuringDom0Patching(self, aDom0, aDomUList, aIsRetry=False):
        """
        :param aDom0: dom0 node on which patching happened
        :param aDomUList: VM node list - conatins customerhostname
        :return: PATCH_SUCCESS_EXIT_CODE on success otherwise DOM0_PATCHING_DB_HEALTHCHECKS_PDB_IN_DEGRADED_STATE or
                 DOM0_PATCHING_DB_HEALTHCHECKS_PDB_FETCH_DETAILS_ERROR

        Note:
            1. mValidateForPDBDegradation in called parallely on all the vms here
            2. For EXACS, opc user and for EXACC root user keys are injected to connect to VM nodes
        """
        _pdb_degradation_failed_vm_list = []
        _ret = PATCH_SUCCESS_EXIT_CODE
        _suggestion_msg = ""
        _user = None

        _enable_health_checks_from_cp = self.mGetHandlerInstance().mGetInfrapatchExecutionValidator().mCheckCondition(
            'mEnableDBHealthChecks')
        _enable_pdb_degradation_check = self.mGetHandlerInstance().mGetInfrapatchExecutionValidator().mCheckCondition(
            'mIsPDBDegradationCheckEnabled')

        if _enable_health_checks_from_cp and _enable_pdb_degradation_check:
            try:
                def _detect_pdb_degrdation_during_dom0_patching(_domu_customer_hostname, aStatus):
                    _pdb_status_dict = {}
                    _domu_node = self.mGetHandlerInstance().mGetDomUNatHostNameforDomuCustomerHostName(
                        _domu_customer_hostname)
                    self.mPatchLogInfo("PDB degradation check started.")

                    _user = self.mGetHandlerInstance().mGetUserDetailsBasedOnDomUhostname(_domu_node)
                    # Default to None in case of _user is not opc.
                    _user = "opc" if _user == "opc" else None

                    _rc, _pdb_status_dict = self.mValidateForPDBDegradation(_domu_node, aIsRetry, aUser=_user)
                    self.mPatchLogInfo("PDB degradation check completed.")
                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                        aStatus.append({'domu': _domu_customer_hostname, 'status': 'failed', 'errorcode': _rc,
                                        'pdb_error_details': _pdb_status_dict})
                        self.mPatchLogError(f"pdb degradation detected on {_domu_customer_hostname}")

                # End of _detect_pdb_degradation_during_dom0_patching

                """
                 Parallelize execution on all target nodes.
                """
                _plist = ProcessManager()
                _rc_status = _plist.mGetManager().list()

                _non_autonomous_vm_list = [_non_autonomous_vm for _non_autonomous_vm in aDomUList if
                                           _non_autonomous_vm not in {_vm_name for _, _vms in
                                                                      self.mGetHandlerInstance().mGetAutonomousVMListWithCustomerHostnames()
                                                                      for _vm_name in _vms}]
                for _remote_node in _non_autonomous_vm_list:
                    _p = ProcessStructure(_detect_pdb_degrdation_during_dom0_patching, [_remote_node, _rc_status],
                                          _remote_node)

                    '''
                     Timeout parameter configurable in Infrapatching.conf
                     Currently it is set to 60 minutes
                    '''
                    _p.mSetMaxExecutionTime(
                        self.mGetHandlerInstance().mGetDBHealthChecksParallelExecutionWaitTimeInSeconds())

                    _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
                    _p.mSetLogTimeoutFx(self.mPatchLogWarn)
                    _plist.mStartAppend(_p)

                _plist.mJoinProcess()

                if _plist.mGetStatus() == "killed":
                    _suggestion_msg = f"Timeout occured while validating for cdb downtime on the VM nodes of the dom0 {aDom0} "
                    _ret = DB_HEALTCHECKS_DETECTION_TIMEOUT_ERROR
                    self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)
                    return _ret

                # Error message handling start
                _degradation_msgs = []
                _other_error_msgs = ""
                # validate the return codes
                for _rc_details in _rc_status:
                    if _rc_details['status'] == "failed":
                        _error_at_vm_level = _rc_details['pdb_error_details']
                        if 'error' in _error_at_vm_level:
                            if _error_at_vm_level['error'] == 'degradation':
                                _degradation_msgs.append(
                                    f" {_error_at_vm_level['pdb']} within {_error_at_vm_level['cdb']} "
                                    f"on {_rc_details['domu']} was in {_error_at_vm_level['pre_openmode']} state"
                                    f" with restricted = {_error_at_vm_level['pre_restricted']} prior to patching "
                                    f"and changed to {_error_at_vm_level['post_openmode']} state with restricted = "
                                    f"{_error_at_vm_level['post_restricted']} post-patching")
                            else:
                                _other_error_msgs += _error_at_vm_level['error']
                        _ret = _rc_details['errorcode']

                if _degradation_msgs:
                    _suggestion_msg += "One or more PDBs within respective CDBs are in degraded state across various VMs."
                    _suggestion_msg += "; ".join(_degradation_msgs)
                    _suggestion_msg += "."

                if _other_error_msgs:
                    _suggestion_msg += _other_error_msgs

                _log_msg_sug = f" Please check prior patch and post patch state of the pdbs in /var/log/exadatatmp/{self.mGetHandlerInstance().mGetMasterReqId()}_pre_patch_pdb_states and /var/log/exadatatmp/{self.mGetHandlerInstance().mGetMasterReqId()}_post_patch_pdb_states across all VMs."
                _suggestion_msg += _log_msg_sug

                if _suggestion_msg and len(_suggestion_msg) > ERROR_MSG_TRUNCATE_LENGTH:
                    _suggestion_msg = mTruncateErrorMessageDescription(_suggestion_msg, aSuffixStr="..."+_log_msg_sug)

                # Error message handling end
            except Exception as e:
                _suggestion_msg = f"Exception {str(e)} occurred while validating for pdb degradation during {aDom0} patching"
                self.mPatchLogWarn(_suggestion_msg)
                _ret = DB_HEALTCHECKS_DETECTION_EXCEPTION_ENCOUNTERED
                self.mPatchLogTrace(traceback.format_exc())
        else:
            self.mPatchLogInfo(f"mEnableDBHealthChecks value is {str(_enable_health_checks_from_cp)} and "
                               f"mIsPDBDegradationCheckEnabled value is {str(_enable_pdb_degradation_check)} so PDB "
                               f"degradation detection check is not run")
        if _ret != PATCH_SUCCESS_EXIT_CODE:
            self.mGetHandlerInstance().mAddError(_ret, _suggestion_msg)

        return _ret
