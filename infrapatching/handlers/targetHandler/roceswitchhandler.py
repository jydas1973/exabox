#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/targetHandler/roceswitchhandler.py /main/37 2025/09/02 17:58:33 ajayasin Exp $
#
# roceswitchhandler.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      roceswitchhandler.py - Patch - RoCE Switch Basic Functionality.
#    DESCRIPTION
#      Provide basic/core RocE Switch patching API (prereq, patch, rollback)
#      for managing the Exadata patching in the cluster implementation.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ajayasin    08/05/25 - moving handler function from clucontrol.py
#                           clucommandhandler.py to reduce the clucontrol.py
#                           size
#    araghave    06/05/25 - Enh 38039225 - RE-RUN PATCHMGR VERIFY CONFIG IN
#                           CASE OF A FAILURE DUE TO SWITCH MISCONFIGURATION
#                           DURING PROVISIONING
#    araghave    05/07/25 - Enh 37892080 - TO IMPLEMENT NEWER PATCHSWITCHTYPE
#                           CHANGES APPLICABLE TO ALL SWITCH TARGET TYPES AND
#                           PATCH COMBINATIONS
#    araghave    02/17/25 - Bug 36456705 - VERSION NAMING CONVENTION CHANGES
#                           FROM CISCO RESULTING IN ROCESWITCH PATCHING TO BE
#                           SKIPPED
#    araghave    01/23/25 - Enh 37106126 - PROVIDE A MECHANISM TO PATCH SPINE
#                           SWITCHES
#    araghave    12/20/24 - ER 37156971 - USE ENCRYPTED NON-DEFAULT PASSWORD TO
#                           SETUP KEYS DURING ADMIN SWITCH PATCHING
#    araghave    11/05/24 - Enh 37115530 - ADD NEW SWITCH TARGET REFERENCE IN
#                           INFRA PATCHING CODE
#    asrigiri    10/22/24 - Bug 36860928 - AIM4ECS:0X03090001 - SWITCH PATCHMGR
#                           COMMAND FAILED.
#    araghave    09/16/24 - Enh 36971721 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE TARGET HANDLER FILES
#    araghave    08/14/24 - Enh 36923844 - INFRA PATCHING CHANGES TO SUPPORT
#                           PATCHING ADMIN SWITCH
#    emekala     08/13/24 - ENH 36679949 - REMOVE OVERHEAD OF INDEPENDENT
#                           MONITORING PROCESS FROM INFRAPATCHING
#    emekala     07/19/24 - ENH 36794217 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE EXACOMPUTE AND DOMU PATCHMGR CMDS
#    emekala     06/25/24 - ENH 36748433 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE DOM0, CELL, IBSWITCH AND ROCESWITCH PATCHMGR
#                           CMDS
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    araghave    04/19/24 - ER 36452945 - TERMINATE INFRA PATCHING THREAD EARLY
#                           IN CASE OF PATCHMGR COMMAND DID NOT RUN
#    antamil     09/29/23 - Bug 35851548 - Append request Id to dbnodes file name
#                           to be unique
#    araghave    06/24/22 - Enh 34258082 - COPY PATCHMGR DIAG LOGS FROM LAUNCH
#                           NODES POST PATCHING ONLY IF THE EXIT STATUS IS A
#                           FAILURE
#    sdevasek    05/22/22 - ENH 33859232 - TRACK TIME PROFILE INFORMATION FOR
#                           INFRAPATCH OPERATIONS
#    araghave    04/19/22 - Enh 33516791 - EXACLOUD: DO NOT OVER WRITE THE
#                           ERROR SET BY RAISE EXCEPTION
#    araghave    04/12/22 - Enh 34048154 - ONEOFF PATCH OPERATION TO SUPPORT A
#                           PLUGIN FRAMEWORK WITH GENERIC OPTIONS
#    araghave    03/23/22 - Bug 33994901 - ENABLE VERIFY_CONFIG AND REMOVE
#                           FORCE FLAGS FROM ROCESWITCH INFRA PATCH FILES
#    araghave    02/02/22 - Enh 33808723 - Make Roceswitch unkey option
#                           configurable in infrapatching.conf
#    araghave    12/09/21 - Bug 33574929 - ROCE SWITCH PRECHECKS FAILS DUE TO
#                           CLUMISC.PY COMMAND FORMAT MODIFICATION CHANGES
#    araghave    11/23/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES
#                           FROM ERROR.PY TO INFRAPATCHERROR.PY
#    araghave    07/08/21 - BUG 33081173 - Remove older error codes from Infra
#                           patching core files
#    araghave    06/03/21 - Enh 32958968 - BUG 32888765 - GET GRANULAR ERROR
#                           HANDLING DETAILS FOR ROCESWITCHES
#    kartdura    07/22/21 - 33053150 : patchmgr existence check for cells and
#                           switches
#    araghave    07/11/21 - ENH 33099120 - INTRODUCE A SPECIFIC ERROR CODE FOR
#                           PATCHMGR CONSOLE READ TIME OUT
#    araghave    06/06/21 - BUG 32888765 - GET GRANULAR ERROR HANDLING DETAILS
#                           FOR CELLS AND IBSWITCHES
#    araghave    04/20/21 - Bug 32397257 - Get granular error handling details
#                           for Dom0 and DomU targets
#    araghave    02/16/21 - ENH 31423563 - PROVIDE A MECHANISM TO MONITOR
#                           INFRA PATCHING PROGRESS
#    araghave    01/12/21 - Enh 31446326 - SUPPORT OF SWITCH OPTION AS TARGET
#                           TYPE THAT TAKES CARE OF BOTH IB AND ROCESWITCH
#    araghave    01/07/21 - Bug 32320030 - ROCE SWITCH REFACTOR CODE CHANGES
#    araghave    11/27/20 - Enh 31604386 - RETURN ERROR CODES TO DBCP FOR CELLS
#                           AND SWITCHES
#    araghave    08/12/20 - Enh 30829107 - Patchmgr log detailed output and log
#                           collection fix
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#

"""
History:
    MODIFIED (MM/DD/YY)
    antamil     09/29/23 - Bug 35851548 - Append thread Id to dbnodes file name
                       to be unique
    pbellary 08/19/20 - Bug 31768768 - Revised fortify fix
    nmallego 08/17/20 - Bug 31761732 - target_version list with return payload
    pbellary 08/10/20 - Bug 31364037 - FORTIFY: COMMAND INJECTION IN LOCAL.PY
    nmallego 08/09/20 - Bug31730630 - Fix string decode in ANSI Escape chars
    vgerard  08/07/20 - Bug 31677145 - Fix error no '_EXABOXCLUCTRL__UUID'
    nmallego 08/07/20 - ER  31678601 - Upgrade free nodes from elastic cabinet
    vmallu   08/06/20 - Bug 31536500 - xml entity expansion
    scoral   07/30/20 - Bug30590874 - Adding compatible code to support python3.
    vmallu   07/29/20 - Enh 31690438 - Support heterogeneous patch versions
    araghave 07/28/20 - BUG 31678870 - DBMCLI STATUS OUTPUT CHANGES REQUIRED IN
                        NEWER EXADATA VERSIONS
    naps     07/24/20 - XbranchMerge naps_bug-31637189_19.4.3.3.0 from
                        st_ecs_19.4.3.0.0
    jyotdas  07/15/20 - Enh 31606581 - EXACLOUD: SUPPORT SINGLE NODE DOM UPGRADE
                        WITH NON ROLLING STYLE
    nmallego 07/13/20 - Bug31605216 - Connect as opc user for dom0domu plugins
                        console log read
    araghave 07/01/20 - Bug 31465889 - RESTORE ATP SPECIFIC SYSCTL SETTINGS
                        POST DOMU UPGRADE
    araghave 05/29/20 - Bug 31420579 - CONFIG PATH CHANGES FOR EXACC
                        ENVIRONMENTS TO STORE PATCH CHECKSUM FILES
    vmallu   05/28/20 - BUG 31395282 - EXACS domo patching failed to establish
                        domu heartbeat with cell
    nmallego 05/19/20 - Bug31376251 - Wrong PatchPayload path on ExaCC
    nmallego 05/15/20 - Bug31115077: Upgrade RocE/KVM based components
    devbabu  05/04/20 - remove the duplicate error code
    nmallego 04/28/20 - Bug31234669: Read RackName from ecra payload
    scoral   04/23/20 - Bug 31145240 - Python 3 migration code adaption
    nmallego 04/07/20 - Enh 30995812 - Make pre and post plugins idempotent
    nmallego 03/30/20 - ER 30995919 - store patching states in metadata json
    vmallu   03/30/20 - Bug 31049092 - EXACCOCI: INFRA PATCHING FAILING AT
                        IMPORTKEYS WITH KMS
    vmallu   03/30/20 - Bug 31101389 - fix ociexacc patch payload patch
    araghave 03/22/20 - Bug 31065254 - Non log rotation, heartbeat check is
                        failed.
    araghave 03/20/20 - Enh 31052954 - MAKE PRE AND POST PLUGINS SCRIPTS RUN IN
                        BACKGROUND
    nmallego 03/16/20 - Bug30922125 - fix concurrent issue
    jyotdas  03/10/20 - Bug 31007529 - Cleanup and fix the ssh leaks in
                        clupatching layer
    araghave 03/03/20 - Bug 30536095 - COPYING THE SYSTEM IMAGE ISO FOR THE
                        WRONG TARGET VERSION
    araghave 02/27/20 - Bug 30932804 - PRECHECK FAILS TO FIND DOMU HEARTBEAT IN
                        CELL ALERT LOG
    araghave 02/19/20 - Enh 30908782 - ksplice and one-off configuration on dom0
                        and cells
    nmallego 02/05/20 - Enh Bug30687255 - Idempotent on patching
    araghave 02/17/20 - BUG 30908200 - DISABLE EXAWATCHER LOG COLLECTION FOR
                        PATCHING DURING INCIDENT LOG COLLECTION.
    araghave 01/15/20 - Bug 30768661 - ADD MISSING LOG DIRECTORY PATH FOR ALL
                        THE DOMU OPERATIONS
    nmallego 01/08/20 - Bug-30327503 - fix fortify errors
    araghave 12/24/19 - Enh 30687229 - EXACLOUD: PATCHMGR SHOULD RUN WITH NOHUP
                        ON LAUNCH NODE
    nmallego 11/24/19 - Bug29997448 - Add detail to return payload in case of
                        no action taken
    araghave 11/13/19 - Bug 30511640 - Exception handling for validating
                        services on Roceswitch
    araghave 10/30/19 - Bug 28493752 - Enable patchmgr to run in Non-rolling
                        fashion during prereq operations for the notifications
                        to work
    araghave 10/29/19 - BUG 30458885 - Import SSH  keys in a KMS environment
    araghave 09/30/19 - ER-30208083 - ATP/EXACLOUD INFRA PATCHING: DISALLOW
                        PATCHING UNLESS POSTCHECKS SUCCEEDED
    araghave 10/03/19 - ENH 30208068 - ATP/EXACLOUD INFRA PATCHING: DETECT
                        KNOWN H/W INTERFACE ALERTS GENERATED
    araghave 09/23/19 - Enh 30337815 - COMPARE CRS RESOURCES BEFORE AND AFTER
                        DOMU PATCHING ACTIVITY
    sringran 09/23/19 - BUG 30336872 - INCORRECT DISK SPACE CALCULATION CAUSING
                        19.2.6 PATCHING FAILURE
    araghave 09/04/19 - BUG 30174632 - PATCHING PRE-CHECK SHOULD CHECK THE NTP
                        CONFIGURATION OF IB SWITCH.
    araghave 09/03/19 - Bug 30243541 - EXCEPTION IN RUNNING PATCHING
                        OPERATION MULTIPLE TIME
    araghave 08/13/19 - Bug 30176781 - Correct invalid path reference to
                        exadata system image bits
    nmallego 08/07/19 - Bug30115824: Read customer name based on xmlns tag
                        in oeda xml
    nmallego 08/01/19 - Bug30125729 - Use common plugin directory path
    araghave 07/18/19 - Bug 30069717 - MAP PATCHPAYLOAD TO IMAGE DOWNLOAD
                        LOCATION FOR OCI-EXACC
    araghave 07/18/19 - ENH 30006991 - GENERATE INCIDENT ZIP FILE DURING INFRA
                        PATCHING OPERATION
    oespinos 07/16/19 - 30052539 - CLUSTER MEMORY RESHAPE IS FAILING
    araghave 07/10/19 - Bug 30034127 - REVERTING CHANGES OF ENH 29833650
    nmallego 07/09/19 - Bug30014992: Receive oeda xml data and written
                        to a file with base64
    araghave 07/02/19 - ENH 29911293 - POSTCHECK OPTION FOR ALL PATCH
                        OPERATIONS.
    araghave 06/20/19 - ENH 29833650 EXADATA INFRA PATCHING: MAP TO DOWNLOAD
                        LOCATION FROM IMAGE MGT SERVICE FOR PATCHPAYLOAD
    araghave 05/19/19 - Bug 29800200 - Pass non-rolling option for prereq
                        on all the targets.
    araghave 05/16/19 - Bug 29669900 - griddisk status check during prereq
                        and patch operations
    nmallego 05/08/19 - Bug29719329 - fix disk free (df) command option
    araghave 04/10/19 - Bug 29623387 - Exacloud mount point validation as
                        per exabox.conf file
    nmallego 04/08/19 - Bug29608693 - plugins version 3
    araghave 03/29/19 - Bug 28248796 - fedramp configuration check
    araghave 03/18/19 - Bug 28584487 - Exacloud mount point storage check
                        before proceeding with patch requests.
    araghave 03/15/19 - ENH 29486325 - Additional options added for
                        IgnoreAlerts, ForceRemoveCustomRpms and ModifyAtPrereq
                        cases.
    nmallego 02/13/19 - Bug29305666: Patch specified node
    vmallu   03/06/19 - Bug 29435285 - fix running cellsrv count logic
    araghave 03/04/19 - Bug29434322 - Roceswitch patch logs copy fix.
    nmallego 02/26/19 - Bug29324353 - Add Diag code: log exec command in
                        mCheckTargetVersion() when fetching image version
    araghave 02/16/19 - Bug 28823221 : Post checks - higgs configuration
    nmallego 01/23/19 - Bug29052011: Pre and Post Exalcoud Plugins-V2
    nmallego 01/07/19 - Bug29136926: Replace service command with cellcli to
                        check cellsrv status
    nmallego 12/14/18 - bug29056361 - Stop node upgrade if there any failure
                        and do not continue
    vmallu   12/13/18 - Bug 29052055 - NEED TO HAVE EXECUTE PERMISSION ON THE
                        PRE POST PLUGINS AFTER COPY TO DOMU AND DOM0 NODE
    nmallego 12/02/18 - Bug29002621 - fix the typo
    nmallego 11/16/18 - Bug26774129 - pre-post plugins/scripts run
    nmallego 11/08/18 - Bug28876616 - Need adjust to correct version format
    nmallego 10/29/18 - Bug28845368: Add diag code
    pnkrishn 10/19/18 - 28568167: Ib switch ssh connection leak
    pnkrishn 09/22/18 - 28632087: asmdeactivationoutcome check
    nmallego 09/03/18 - Bug28585904: Log appropriate message if node list
                        turn out to be empty.
    nmallego 07/06/18 - Bug28225552 - Add log path to output json of exacloud
    nmallego 06/13/18 - ER Bug28155938 - Pass additional options for exadata
                        infra patching and integrate of Roceswitch upgrade per
                        rack basis
    nmallego 06/06/18 - Bug28126586 - Validate the image version of the node
                        during prereq and upgrade
    nmallego 04/02/18 - Bug27796233 - evaluate latest target version properly
                        to cover version format 18.1.3.0.0.171219.2'
    nmallego 03/14/18 - Bug27643616 - add option BackupMode for upgrade of
                        domU/dom0
    nmallego 03/07/18 - Bug27643008 - Enhance exadata infra patching capability
                        to take image backup separately
    nmallego 03/02/18 - Bug27556005 - have single class object for ssh setup
                        and cleanup to retain the host_key comment
    nmallego 02/23/18 - Bug27589883 - Patchmgr and postcheck steps needs to be
                        corrected for dom0 and domU upgrade
    nmallego 02/20/18 - Bug27574842 - Invalid string format in
                        mPatchDom0sOrDomus()
    nmallego 02/10/18 - Bug27409907 - fix the issue of parsing cell heartbeat
                        logic
    nmallego 01/09/18 - Bug27156405 - Scan OSS to get the latest verion and
                        also download missing files from OSS
    nmallego 01/02/18 - Bug27263414 - read grid hb timeout and exacloud patch
                        size from exabox.conf, instead from system env variable
    nkedlaya 12/08/17 - Bug 27239627 - EXABMC:17.4.2:DOM0 PATCH
                        FAILURE-NAMEERROR: GLOBAL NAME TR IS NOT DEFINED
    nmallego 12/04/17 - bug27084627 - update logdir path for domu/dom0
    nmallego 11/17/17 - Bug27130067 - mPatchDom0sOrDomus should take
                        appropriate action for CNS
    nmallego 11/09/17 - bug27099983 - fix undefined var node_to_patch_nodes
    nkedlaya 10/28/17 - BUG 27032704 - DOMU EXADATA UPDATE TO USE DOMU S LAUNCH
                        POINT NOT DOM0
    nmallego 10/27/17 - Bug26830429 - add option LATEST to patch operation
    nmallego 10/03/17 - Bug26726236 - Additional post check for Roceswitch
    nmallego 10/09/17 - Bug26943824 - fix the Roceswitch post check failure
    nmallego 10/05/17 - bug26863775 - add exadata_rack to cns payload
    nmallego 08/18/17 - patch notification for dom0, cell, domu, Roceswitch
    nkedlaya 08/24/17 - Bug 26678535 - APPLY SECURITY FIXES EXADATA
                        12.2.1.1.2.170714 FAILED ON SECOND DOM0
    pnkrishn 08/11/17 - 26618330: Incorrect validate of RoceswitchVersion
                        upgrade/downgrade
    nkedlaya 08/09/17 - bug 26608328 : DOM0 patching fails with
                        __domu_patch_base_after_unzip object has no attribute
    nmallego 07/20/17 - bug26499199 - Use log_dir option with patchmgr (for
                        cell and Roceswitch patch operations)
    nkedlaya 06/14/17 - bug 26242636 : EXACLOUD DOMU PATCHING SHOULD COPY
                        PATCHMGR DIAGS,TRACES TO DOM0
    nkedlaya 05/17/17 - add patching input json key constants
    nkedlaya    12/05/2017 - bug 25892555 - implement domu patching in exacloud
    bmartin     03/17/2016 - Dom0 patchmgr functionality
    marrorod    03/17/2016 - Cell/Roceswitch patchmgr functionality
    bmartin     03/18/2016 - post dom0 patch heartbeat checks
    marrorod    04/15/2016 - Master request support. Monitor added
    bmartin     04/22/2016 - Environment variables support
    marrorod    04/25/2016 - Error handling
    marrorod    04/26/2016 - Added checks: DB services, cell services, ping host, SM state
    bmartin     04/26/2016 - Added target version check
    marrorod    04/28/2016 - Lock changes. Master request acquires the lock before sending a request
"""
import traceback
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.infrapatching.handlers.targetHandler.targethandler import TargetHandler
from exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler import InfraPatchManager
from exabox.infrapatching.utils.utility import mRegisterInfraPatchingHandlers
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.ovm.clumisc import OracleVersion

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))


class RoceSwitchHandler(TargetHandler):

    def __init__(self, *initial_data, **kwargs):

        super(RoceSwitchHandler, self).__init__(*initial_data, **kwargs)
        self.mPatchLogInfo("RoceSwitchHandler")
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [PATCH_ROCESWITCH], self)

        '''
         Generate keys for the admin switches and return the list
         of admin switches only in case of PatchSwitchType Flag has 
         all or admin set.
        '''
        if self.mCheckIfAdminSwitchCanBePatched().lower() in [ "all", "admin" ]:
            # Set the list of admin switches
            self.mSetListOfAdminSwitches(self.mGetCluControl().mGetCommandHandler().mHandlerAdminSwitchConnect())

    def mSetEnvironment(self):

        # Set patch environment
        self.mSetcellSwitchesBaseEnvironment()

        self.mSetCurrentTargetType(PATCH_ROCESWITCH)

        # Add to executed targets
        self.mGetExecutedTargets().append(self.mGetCurrentTargetType())

        # Set collect time stats flag
        self.mSetCollectTimeStatsFlag(self.mGetCollectTimeStatsParam(self.mGetCurrentTargetType()))

        # Set admin switch apply flag
        self.mSetPatchSwitchType(self.mCheckIfAdminSwitchCanBePatched())

    def mPreCheck(self):
        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken =0
        _task_type = self.mGetTask()

        try:
            # 1. Set up environment
            self.mSetEnvironment()

            # Skip switch patching in case of PatchSwitchType flag is set to null, none or "".
            if self.mIsSwitchPatchingSkipped():
                self.mPatchLogInfo(f"Switch patching will be skipped in case of PatchSwitchType flag is passed is null or none or empty.")
                return _ret , _no_action_taken

            self.mPrintPatchSwitchTypePrintActions()

            # Check for idempotency
            # Roce switch patch flow
            if self.mGetPatchSwitchType().lower() != "admin":

                self.mPatchLogInfo(
                    f"\n\n---------------> Starting {self.mGetTask()} in {self.mGetCurrentTargetType()} <---------------\n\n")

                if self.mPatchRequestRetried():
                    _ret  = self.mCheckIdemPotency()
                else:
                    _ret, _no_action_taken = self.mRegularPatchRun()

            # Admin switch patch flow
            if self.mIsAdminSwitchPatchingEnabled():
                _ret, _no_action_taken = self.mExecuteAdminSwitchInfraPatchOperations()

            self.mPatchLogInfo(f"Task: {self.mGetCurrentTargetType()} - Type: {self.mGetCurrentTargetType()}\t\t[ ret_code = {_ret} ]")                
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"{self.mGetCurrentTargetType()} '{_task_type}' failed.")

        except Exception as e:
            self.mPatchLogError(f"Exception in Running Switch PreCheck  {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _ret = SWITCH_PATCH_PRECHECK_FAILED
                _suggestion_msg = f"{self.mGetCurrentTargetType()} '{_task_type}' failed. Error:{str(e)}"
                self.mAddError(_ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            return _ret, _no_action_taken

    def mRollBackPreCheck(self):
        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken =0
        _task_type = self.mGetTask()

        try:
            # 1. Set up environment
            self.mSetEnvironment()

            # Skip switch patching in case of PatchSwitchType flag is set to null, none or "".
            if self.mIsSwitchPatchingSkipped():
                self.mPatchLogInfo(f"Switch patching will be skipped in case of PatchSwitchType flag is passed is null or none or empty.")
                return _ret , _no_action_taken

            self.mPrintPatchSwitchTypePrintActions()

            # Check for idempotency
            # Roce switch patch flow
            if self.mGetPatchSwitchType().lower() != "admin":

                self.mPatchLogInfo(
                    f"\n\n---------------> Starting {self.mGetTask()} in {self.mGetCurrentTargetType()} <---------------\n\n")

                if self.mPatchRequestRetried():
                    _ret  = self.mCheckIdemPotency()
                else:
                    _ret, _no_action_taken = self.mRegularPatchRun()

            # Admin switch patch flow
            if self.mIsAdminSwitchPatchingEnabled():
                _ret, _no_action_taken = self.mExecuteAdminSwitchInfraPatchOperations()

            self.mPatchLogInfo(f"Task: {self.mGetCurrentTargetType()} - Type: {self.mGetCurrentTargetType()}\t\t[ ret_code = {_ret} ]")
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"{self.mGetCurrentTargetType()} '{_task_type}' failed.")

        except Exception as e:
            self.mPatchLogError(f"Exception in Running Switch Rollback PreCheck {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _ret = SWITCH_ROLLBACK_PRECHECK_FAILED
                _suggestion_msg = f"{self.mGetCurrentTargetType()} '{_task_type}' failed. Error: {str(e)}"
                self.mAddError(_ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            return _ret , _no_action_taken

    def mPatch(self):
        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken =0
        _task_type = self.mGetTask()

        try:
            # 1. Set up environment
            self.mSetEnvironment()

            # Skip switch patching in case of PatchSwitchType flag is set to null, none or "".
            if self.mIsSwitchPatchingSkipped():
                self.mPatchLogInfo(f"Switch patching will be skipped in case of PatchSwitchType flag is passed is null or none or empty.")
                return _ret , _no_action_taken

            self.mPrintPatchSwitchTypePrintActions()

            # Check for idempotency
            # Roce switch patch flow
            if self.mGetPatchSwitchType().lower() != "admin":

                self.mPatchLogInfo(
                    f"\n\n---------------> Starting {self.mGetTask()} in {self.mGetCurrentTargetType()} <---------------\n\n")

                if self.mPatchRequestRetried():
                    _ret  = self.mCheckIdemPotency()
                else:
                    _ret, _no_action_taken = self.mRegularPatchRun()

            # Admin switch patch flow
            if self.mIsAdminSwitchPatchingEnabled():
                _ret, _no_action_taken = self.mExecuteAdminSwitchInfraPatchOperations()

            self.mPatchLogInfo(f"Task: {self.mGetCurrentTargetType()} - Type: {self.mGetCurrentTargetType()}\t\t[ ret_code = {_ret} ]")
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"{self.mGetCurrentTargetType()} '{_task_type}' failed.")

        except Exception as e:
            self.mPatchLogError(f"Exception in Running Switch Patch {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _ret = SWITCH_PATCH_FAILED
                _suggestion_msg = f"{self.mGetCurrentTargetType()} '{_task_type}' failed. Error: {str(e)}"
                self.mAddError(_ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {self.mGetCurrentTargetType()}s <---------------\n\n")
            return _ret, _no_action_taken

    def mRollBack(self):
        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken =0
        _task_type = self.mGetTask()

        try:
            # 1. Set up environment
            self.mSetEnvironment()

            # Skip switch patching in case of PatchSwitchType flag is set to null, none or "".
            if self.mIsSwitchPatchingSkipped():
                self.mPatchLogInfo(f"Switch patching will be skipped in case of PatchSwitchType flag is passed is null or none or empty.")
                return _ret , _no_action_taken

            self.mPrintPatchSwitchTypePrintActions()

            # Check for idempotency
            # Roce switch patch flow
            if self.mGetPatchSwitchType().lower() != "admin":

                self.mPatchLogInfo(
                    f"\n\n---------------> Starting {self.mGetTask()} in {self.mGetCurrentTargetType()} <---------------\n\n")

                if self.mPatchRequestRetried():
                    _ret  = self.mCheckIdemPotency()
                else:
                    _ret, _no_action_taken = self.mRegularPatchRun()

            # Admin switch patch flow
            if self.mIsAdminSwitchPatchingEnabled():
                _ret, _no_action_taken = self.mExecuteAdminSwitchInfraPatchOperations()

            self.mPatchLogInfo(f"Task: {self.mGetCurrentTargetType()} - Type: {self.mGetCurrentTargetType()}\t\t[ ret_code = {_ret} ]")
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"{self.mGetCurrentTargetType()} '{_task_type}' failed.")

        except Exception as e:
            self.mPatchLogError(f"Exception in Running Switch Rollback {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _ret = SWITCH_ROLLBACK_FAILED
                _suggestion_msg = f"{self.mGetCurrentTargetType()} '{_task_type}' failed. Error: {str(e)}"
                self.mAddError(_ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {self.mGetCurrentTargetType()}s <---------------\n\n")
            return _ret , _no_action_taken

    def mCheckIdemPotency(self):
        # Default patch exit code
        _ret = PATCH_SUCCESS_EXIT_CODE
        _task_type = self.mGetTask()
        _patchMgrObj = None
        # This is for purely for patch retry operation

        # create patchmgr object with bare minimum arguments
        _patchMgrObj = InfraPatchManager(aTarget=PATCH_ROCESWITCH, aOperation=_task_type, aPatchBaseAfterUnzip=self.mGetCellSwitchesPatchBaseAfterUnzip(),
                                   aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

        # now set the component's operation specific arguments
        _patchMgrObj.mSetLaunchNode(aLaunchNode=self.mGetDom0ToPatchcellSwitches())

        _patchMgrObj.mWaitForPatchMgrCmdExecutionToComplete()

        self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")
        _ret = _patchMgrObj.mGetStatusCode()        

        # Clean up and gather diagnostic files:-
        # Reading the path of the input file from the reference of last request_id run
        _input_file_retry_case = _patchMgrObj.mGetNodesToBePatchedFile()

        # Read list of roceswitch from input file
        _list_of_roceswitches_retry_case = _patchMgrObj.mGetNodeListFromNodesToBePatchedFile(aHost=self.mGetDom0ToPatchcellSwitches())

        # Clean the environment: Delete passwordless, delete input file
        self.mCleanEnvironment(self.mGetDom0ToPatchcellSwitches(), _list_of_roceswitches_retry_case,
                                _input_file_retry_case, self.mGetCellSwitchesPatchBaseAfterUnzip(),
                                self.mGetPatchmgrLogPathOnLaunchNode(), self.mGetCurrentTargetType(), _ret)

        return _ret

    def mRegularPatchRun(self):
        _no_action_taken = 0
        _ret = PATCH_SUCCESS_EXIT_CODE
        # filter valid Roceswitches. This is for regular flow
        _task_type = self.mGetTask()
        _list_of_roceswitches = []
        _discarded = []
        _patchMgrObj = None
        _list_of_nodes_for_node_progress_details = []

        self.mSetDom0ToPatchcellSwitches()
        '''
         Switch are not filtered on the infra patching
         based on the version as there could be missing
         oneoff patches even when the switch version is
         already upto date.
        '''
        if len(self.mGetSwitchList()) > 0:
            _list_of_roceswitches = self.mGetSwitchList()

        # Set initial Patch Status Json.
        # In case of admin switches patched, node progress
        # will be captured for admin switches as well.
        _list_of_nodes_for_node_progress_details = _list_of_roceswitches[:]
        if self.mIsAdminSwitchPatchingEnabled():
            # Get list of all the nodes in the cluster
            if len(self.mGetListOfAdminSwitches()) > 0:
                _list_of_nodes_for_node_progress_details += self.mGetListOfAdminSwitches()
                self.mPatchLogInfo(f"Admin switch patching flag is enabled and node progress details will be collected on {_list_of_nodes_for_node_progress_details}")
        self.mUpdatePatchProgressStatus(aNodeList=_list_of_nodes_for_node_progress_details, aDiscardedNodeList=_discarded)

        if not self.mPatchRequestRetried() and len(self.mGetSwitchList()) > 0 and _no_action_taken == 0:
            # Prepare environment: passwordless between dom0 and cells, create input file
            _key = self.mPrepareEnvironment(self.mGetDom0ToPatchcellSwitches(), self.mGetSwitchList(),
                                                           self.mGetCellSwitchesPatchBaseAfterUnzip())

            if not self.mGetDom0ToPatchcellSwitches():
                _suggestion_msg = f"Launch node is either down or patches are not staged, unable to proceed with {self.mGetCurrentTargetType()} operation on {_task_type} target."
                _ret = SWITCH_PATCH_FILES_MISSING
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            # create patchmgr object with bare minimum arguments
            _patchMgrObj = InfraPatchManager(aTarget=PATCH_ROCESWITCH, aOperation=_task_type, aPatchBaseAfterUnzip=self.mGetCellSwitchesPatchBaseAfterUnzip(),
                                       aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

            # check for patchmgr session existence
            _patchMgrObj.mSetLaunchNode(aLaunchNode=self.mGetDom0ToPatchcellSwitches())

            _ret, _patchmgr_active_node = _patchMgrObj.mCheckForPatchMgrSessionExistence()

            if _ret == PATCHMGR_SESSION_ALREADY_EXIST:
                return _ret, _no_action_taken

            # create patchmgr nodes file
            _input_file = _patchMgrObj.mCreateNodesToBePatchedFile(aLaunchNode=self.mGetDom0ToPatchcellSwitches(), aHostList=self.mGetSwitchList())

            # Run patchmgr command
            _ret = self.mPatchRoceswitchesRolling(self.mGetSwitchList(), _patchMgrObj)

            '''
             After the Roceswitch upgrade/rollback, do the postcheck and
             compare the result against the precheck data collected
             before patching/rollback.
            '''
            if _ret == PATCH_SUCCESS_EXIT_CODE and _task_type not in [ TASK_PREREQ_CHECK, TASK_ROLLBACK_PREREQ_CHECK ]:
                for _roce in self.mGetSwitchList():
                    if not self.mGetCluPatchCheck().mPingNode(_roce):
                        _suggestion_msg = f"Switch ping check failed : {_roce}"
                        _ret = SWITCH_PING_CHECK_FAILED
                        self.mAddError(_ret, _suggestion_msg)
                        return _ret

            # Clean the environment: Delete passwordless, delete input file
            self.mCleanEnvironment(self.mGetDom0ToPatchcellSwitches(), _list_of_roceswitches, _input_file,
                                    self.mGetCellSwitchesPatchBaseAfterUnzip(),
                                    self.mGetPatchmgrLogPathOnLaunchNode(), self.mGetCurrentTargetType(), _ret)

        elif not self.mPatchRequestRetried() and _no_action_taken == 0:
            _no_action_taken += 1
            # We need to populate more info about the patching operation when
            # no action is required and it requires to update ecra rack
            # status to previous
            _suggestion_msg = "No available Roceswitches to run the patchmgr. Nothing to do here."
            _ret = PATCH_SUCCESS_EXIT_CODE
            self.mAddError(_ret, _suggestion_msg)

        return _ret, _no_action_taken

    def mPatchRoceswitchesRolling(self, aListOfNodes, aPatchMgrObj):

        """
        Runs the Roceswitches patch operations in rolling mode.
        """

        aNodeType = self.mGetCurrentTargetType()
        _task_type = self.mGetTask()

        _exit_code = PATCH_SUCCESS_EXIT_CODE
        _patchmgr_cmd = ""
        _patchMgrObj = aPatchMgrObj

        '''
         Bug 33994901:

         Below "--verify_config no" and "--force" options were removed as part 
         of Bug 33994901.

         Remove "--verify_config no" option - By using this option, internally 
         patchmgr would skip polling until all of the services to come up and 
         also skip postcheck validation before proceeding with patch on next 
         switch, by default --verify_config is set to yes and hence it need 
         not be specified in the patchmgr command.

         Remove --force option from Infra patching code - When --force is used 
         with the patchmgr command, certain validations if patching enounters a 
         warning message, they might get skipped. 

         Append sfleaf tag - Since all of the EXACC roceswitches are secure 
         fabric enabled, exadata dev suggested to append sfleaf tag to each of 
         the switches in the list so that the time taken to generate new switch 
         file can be reduced.
        '''

        # Update status
        self.mUpdatePatchStatus(True, STEP_RUN_PATCH_SWITCH)

        # Prepare the node list file with appropriate tags for execution using the InfraPatchManager object.
        _patchmgr_cmd = _patchMgrObj.mGetPatchMgrCmd(aPrepareRoceVerifyCfgCmd=True)

        # run patchmgr
        _patchMgrObj.mSetLaunchNode(aLaunchNode=self.mGetDom0ToPatchcellSwitches())

        _patchMgrObj.mExecutePatchMgrCmd(aPatchMgrCmd=_patchmgr_cmd, aPrepareRoceVerifyCfgCmd=True)
        _exit_code = _patchMgrObj.mGetStatusCode()
        if _exit_code != PATCH_SUCCESS_EXIT_CODE:
            return _exit_code

        # prepare the patchmgr command for execution using the InfraPatchManager object
        _patchmgr_cmd = _patchMgrObj.mGetPatchMgrCmd()

        _patchMgrObj.mExecutePatchMgrCmd(aPatchMgrCmd=_patchmgr_cmd)
        _exit_code = _patchMgrObj.mGetStatusCode()
        if _exit_code != PATCH_SUCCESS_EXIT_CODE:
            return _exit_code

        # Capture time profile details
        self.mPopulateInfrapatchingTimeStatsEntries(aNewStage="PATCH_MGR", aNewSubStage="",
                                                    aNewStageNodes=str(aListOfNodes),
                                                    aCompletedStage="PRE_PATCH", aCompletedSubStage="")

        # Monitor console log
        if _task_type in [ TASK_PATCH, TASK_ROLLBACK ]:
            _input_file = _patchMgrObj.mGetListOfSwitchesToBePatchedWithAppropriateTagsFile()
            _patchMgrObj.mWaitForPatchMgrCmdExecutionToComplete(aInputListFile=_input_file, aPatchStates=STEP_RUN_PATCH_SWITCH)
        else:
            _patchMgrObj.mWaitForPatchMgrCmdExecutionToComplete()

        self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")
        _exit_code = _patchMgrObj.mGetStatusCode()

        self.mPatchLogInfo(f'Infra Patching exit_code = {_exit_code}')

        # Capture time profile details
        self.mPopulateInfrapatchingTimeStatsEntries(aNewStage="POST_PATCH", aNewSubStage="",
                                                    aNewStageNodes=str(aListOfNodes),
                                                    aCompletedStage="PATCH_MGR", aCompletedSubStage="")
        return _exit_code

    def mPostCheck(self):
        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0

        try:
            self.mPatchLogInfo(
                f"\n\n---------------> Starting {self.mGetTask()} in {self.mGetCurrentTargetType()} <---------------\n\n")
            _ret = self.mCustomCheck()
        except Exception as e:
            self.mPatchLogError(f"Exception in Running Switch Postcheck  {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _ret = SWITCH_POSTCHECK_FAILED
                _suggestion_msg = f"{self.mGetCurrentTargetType()} '{self.mGetTask()}' failed."
                self.mAddError(_ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {self.mGetCurrentTargetType()}s <---------------\n\n")
            return _ret , _no_action_taken

    def mOneOff(self):
        """
         PATCH_SUCCESS_EXIT_CODE for success
         Any other error code other than PATCH_SUCCESS_EXIT_CODE
        """

        _ret = PATCH_SUCCESS_EXIT_CODE
        self.mPatchLogInfo(f"\n\n---------------> Starting {TASK_ONEOFF} in {self.mGetCurrentTargetType()}s <---------------\n\n")
        try:
            # Check if oneoff is enabled by the framework
            if self.mGetPluginHandler() and self.mIsOneOffPluginEnabled():
                _node_list = self.mGetSwitchList()
                self.mGetPluginHandler().mSetNodeList(_node_list)
                self.mGetPluginHandler().mSetPluginTarget(self.mGetCurrentTargetType())

                # Execute oneoff plugin
                _ret = self.mGetPluginHandler().mApply()
                return _ret
            else:
                _ret = ONEOFF_APPLY_FAILED
                _suggestion_msg = TASK_ONEOFF.upper() + " plugin is unavailable for " + self.mGetCurrentTargetType().upper()
                self.mAddError(_ret, _suggestion_msg)
                raise self.mPatchLogError(TASK_ONEOFF.upper() +
                                          " plugin is unavailable for " + self.mGetCurrentTargetType().upper())
        except Exception as e:
            self.mPatchLogWarn(f"Exception in Running Switch OneOff Plugin {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {self.mGetCurrentTargetType()}s <---------------\n\n")

    def mCustomCheck(self):
        """
         This method performs a post checks independently on
         all of the Exadata targets like Dom0, DomU,Roceswitches
         and cells.

         Return value :
          PATCH_SUCCESS_EXIT_CODE -> if post check is success
          any other error code other than PATCH_SUCCESS_EXIT_CODE  -> if
          post check fails
          Otherwise, pre-defined non zero error code
        """

        # Enh 30208083 - Disallow patching if required/critical services
        # are not running on the upgraded node(s).
        _ret = PATCH_SUCCESS_EXIT_CODE
        for _roce in self.mGetSwitchList():
            if not self.mGetCluPatchCheck().mPingNode(_roce):
                _suggestion_msg = f"Switch ping check failed : {_roce}"
                _ret = SWITCH_PING_CHECK_FAILED
                self.mAddError(_ret, _suggestion_msg)
        return _ret
