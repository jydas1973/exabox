#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/mockTargetHandler/roceswitchmockhandler.py /main/2 2024/11/04 07:22:22 emekala Exp $
#
# roceswitchmockhandler.py
#
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
#
#    NAME
#      roceswitchmockhandler.py - Patch - RoCE Switch Basic Functionality.
#    DESCRIPTION
#      Provide basic/core RocE Switch patching API (prereq, patch, rollback)
#      for managing the Exadata patching in the cluster implementation.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    emekala     10/25/24 - ENH 37070223 - SYNC MOCK HANLDERS WITH LATEST CODE
#                           FROM CORE INFRAPATCHING HANDLERS AND ADD SUPPORT
#                           FOR CUSTOM RESPONSE AND RACK DETAILS
#    araghave    09/16/24 - Enh 36971721 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE TARGET HANDLER FILES
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
from exabox.infrapatching.handlers.mockTargetHandler.targetmockhandler import TargetMockHandler
from exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler import InfraPatchManager
from exabox.infrapatching.utils.utility import mRegisterInfraPatchingHandlers
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.ovm.clumisc import OracleVersion

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))


class RoceSwitchMockHandler(TargetMockHandler):

    def __init__(self, *initial_data, **kwargs):

        super(RoceSwitchMockHandler, self).__init__(*initial_data, **kwargs)
        self.mPatchLogInfo("RoceSwitchMockHandler")
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [PATCH_ROCESWITCH], self)

    def mPrePostRoceSwitchCheck(self, aRoceSwitch, aTaskType):

        """
        This method performs basic sanity checks on all RoceSwitches
        in the rack during RoceSwitch prereq and postcheck operations.

            - return PATCH_SUCCESS_EXIT_CODE if success
            - return any other error code other than PATCH_SUCCESS_EXIT_CODE
              if failure
        """

        if self.mIsMockEnv():
            # in mock setup, skip rack specific operations
            return PATCH_SUCCESS_EXIT_CODE

        # Ping Check

        if aTaskType in [TASK_POSTCHECK]:
            # Ping test to each RoceSwitch in the cluster.
            if not self.mGetCluPatchCheck().mPingNode(aRoceSwitch):
                _suggestion_msg = f"Switch ping check failed : {aRoceSwitch}"
                ret = SWITCH_PING_CHECK_FAILED
                self.mAddError(ret, _suggestion_msg)
                return ret

        return PATCH_SUCCESS_EXIT_CODE

    def mDoRoceSwitchPostCheck(self, aRoceSwitchesData):
        """
        Runs a basic postcheck in the roceswitches. It compares the data taken before running the patchmgr.
        """

        if self.mIsMockEnv():
            # in mock setup, skip rack specific operations
            return PATCH_SUCCESS_EXIT_CODE

        def _check_roceswitch(aRoceSwitch, aData):
            # Ping host
            if not self.mGetCluPatchCheck().mPingNode(aRoceSwitch):
                _suggestion_msg = f"Ping failed for the RoceSwitch : {aRoceSwitch}"
                _ret = SWITCH_PING_CHECK_FAILED
                self.mAddError(_ret, _suggestion_msg)
                return False,_ret

            ### Check version
            _ret = self.mCheckRoceSwitchVersion(aRoceSwitch, aData['version'])

            if self.mGetTask() == TASK_PATCH:
                if int(_ret) <= 0:
                    _suggestion_msg = f"Current version on the Switch is expected to be higher than the target version : {aRoceSwitch}"
                    _ret = SWITCH_CURRENT_VERSION_EXPECTED_HIGHER_THAN_ORIGINAL_VER
                    self.mAddError(_ret, _suggestion_msg)
                    return False, _ret
            elif self.mGetTask() == TASK_ROLLBACK:
                if int(_ret) >= 0:
                    _suggestion_msg = f"Current version on the Switch is expected to be lower than the target version : {aRoceSwitch}"
                    _ret = SWITCH_CURRENT_VERSION_SHOULD_BE_LOWER_THAN_ORIGINAL_VER
                    self.mAddError(_ret, _suggestion_msg)
                    return False, _ret

            return True, PATCH_SUCCESS_EXIT_CODE
        # End of _check_roceswitch method

        _rc = PATCH_SUCCESS_EXIT_CODE
        _ret = True
        _failure_history_code = PATCH_SUCCESS_EXIT_CODE

        for _roceswitch in aRoceSwitchesData.keys():
            # Update status
            self.mUpdatePatchStatus(True, STEP_POSTCHECKS + "_" + PATCH_ROCESWITCH)
            # Start check
            self.mPatchLogInfo(f'Starting basic postcheck in roceswitch {_roceswitch}')
            _out, _error_code = _check_roceswitch(_roceswitch, aRoceSwitchesData[_roceswitch])
            if _out:
                self.mPatchLogInfo(f"Successful postcheck in roceswitch {_roceswitch}")

            _ret &= _out
            if _error_code != PATCH_SUCCESS_EXIT_CODE:
                _failure_history_code = _error_code

        # Consolidate and return Error code for all switches.
        if not _ret:
            _rc = _failure_history_code

        return _rc

    def mFilterRoceswitchesToPatch(self, aRoceswitchList):
        """
        Filters the Roceswitches that must be patched based on the active/inactive version and
        the target version. It returns two lists: one for availables switches and one for discarded switches:
        [Roceswitches_to_patch, discarded_Roceswitches]
        """

        _nodes_to_patch = []
        _discarded_nodes = []

        if not self.mIsMockEnv():
            # Get version details
            _Roceswitch_upgrade_version, _Roceswitch_rollback_version = self.mGetSwitchTargetVersion(PATCH_ROCESWITCH)

        # Update status
        self.mUpdatePatchStatus(True, STEP_FILTER_NODES + "_" + PATCH_ROCESWITCH)

        for _Roceswitch in aRoceswitchList:
            if not self.mIsMockEnv() and self.mGetTask() in [TASK_PATCH, TASK_PREREQ_CHECK]:
                _ret = self.mCheckRoceSwitchVersion(_Roceswitch, _Roceswitch_upgrade_version)
                if int(_ret) >= 0:
                    self.mPatchLogInfo(
                        f"Roceswitch firmware already up to date in {_Roceswitch}. Roceswitch will be discarded.")
                    _discarded_nodes.append(_Roceswitch)
                    continue
            if not self.mIsMockEnv() and self.mGetTask() in [TASK_ROLLBACK, TASK_ROLLBACK_PREREQ_CHECK]:
                _ret = self.mCheckRoceSwitchVersion(_Roceswitch, _Roceswitch_rollback_version)
                if int(_ret) <= 0:
                    self.mPatchLogInfo(
                        f"Roceswitch firmware already at a lower version in {_Roceswitch}. Roceswitch will be discarded.")
                    _discarded_nodes.append(_Roceswitch)
                    continue
            self.mPatchLogInfo(f'Adding {_Roceswitch} to available Roceswitches list')
            _nodes_to_patch.append(_Roceswitch)

        return [_nodes_to_patch, _discarded_nodes]

    def mCheckRoceSwitchVersion(self, aRoceSwitch, aVersionToCompare=None):
        """
         Returns the firmware version installed in aRoceSwitch. If aVersionToCompare is provided, then
         it returns 0 if aRoceSwitch version is equal to aVersionToCompare, <0 if aRoceSwitch version is lower or
         >0 if aRoceSwitch version is higher.
        """

        _cmd = "show version | grep 'NXOS: version' | awk '{print $3}'"
        _current_version = None

        # instantiate the class oracle version
        _verobj = OracleVersion()

        _switch = exaBoxNode(get_gcontext())
        _switch.mConnect(aHost=aRoceSwitch)
        _in, _out, _err = _switch.mExecuteCmd(_cmd)
        _switch.mDisconnect()
        _output = _out.readlines()

        if _output:
            _current_version = _output[0].strip().split()[-1]

        if not _current_version or not aVersionToCompare:
            return _current_version

        _current_version_formatted = int(_current_version.replace("(", "").replace(")", "").replace('.', '').replace('I', ''))
        aVersionToCompare_formatted = int(aVersionToCompare.replace("(", "").replace(")", "").replace('"', '').replace('.', '').replace('I', ''))

        self.mPatchLogInfo(
            f'mCheckRoceSwitchVersion: Current version = {_current_version}, and Comparing Version = {aVersionToCompare}')

        return _verobj.mCompareVersions(_current_version_formatted, aVersionToCompare_formatted)

    def mSetEnvironment(self):

        # Set patch environment
        self.mSetcellSwitchesBaseEnvironment()

        # Add to executed targets
        self.mGetExecutedTargets().append(PATCH_ROCESWITCH)

        self.mSetCurrentTargetType(PATCH_ROCESWITCH)

        # Set collect time stats flag
        self.mSetCollectTimeStatsFlag(self.mGetCollectTimeStatsParam(PATCH_ROCESWITCH))

    def mGatherRoceSwitchPreCheckData(self, aRoceSwitchesList):
        """
        Gets the roceSwitches data before running any patch task. This data will be
        used to compare versions during the post patch phase.
        """

        _data = {}
        for _roceswitch in aRoceSwitchesList:
            _data[_roceswitch] = {'version': None}

            # Update status
            self.mUpdatePatchStatus(True, STEP_GATHER_NODE_DATA + "_" + PATCH_ROCESWITCH)

            self.mPatchLogInfo(f'Starting  basic pre-check in roceswitch {_roceswitch}')
            _data[_roceswitch]['version'] = self.mCheckRoceSwitchVersion(_roceswitch)

        return _data

    def mPreCheck(self):
        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken =0
        _task_type = self.mGetTask()

        try:
            # Run independent postcheck method before proceeding with Prereq.
            _ret = self.mCustomCheck()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                return _ret , _no_action_taken

            self.mPatchLogInfo(
                f"\n\n---------------> Starting {self.mGetTask()} in {PATCH_ROCESWITCH} <---------------\n\n")
            # 1. Set up environment
            self.mSetEnvironment()

            # 2. Get list of all the nodes in the cluster
            _Roceswitches_to_upgrade = self.mGetSwitchList()

            # 3. Check for idempotency
            if self.mPatchRequestRetried():
                _ret  = self.mCheckIdemPotency()
            else:
                _ret, _no_action_taken = self.mRegularPatchRun(_Roceswitches_to_upgrade)

            self.mPatchLogInfo(f"Task: {_task_type} - Type: {PATCH_ROCESWITCH}\t\t[ ret_code = {_ret} ]")
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"{PATCH_ROCESWITCH} '{_task_type}' failed.")

        except Exception as e:
            self.mPatchLogError(f"Exception in Running Switch PreCheck  {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _ret = SWITCH_PATCH_PRECHECK_FAILED
                _suggestion_msg = f"{PATCH_ROCESWITCH} '{_task_type}' failed."
                self.mAddError(_ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            return _ret, _no_action_taken

    def mRollBackPreCheck(self):
        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken =0
        _task_type = self.mGetTask()

        try:
            # Run independent postcheck method before proceeding with Rollback Prereq.
            _ret = self.mCustomCheck()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                return _ret , _no_action_taken

            self.mPatchLogInfo(
                f"\n\n---------------> Starting {self.mGetTask()} in {PATCH_ROCESWITCH} <---------------\n\n")
            # 1. Set up environment
            self.mSetEnvironment()

            # 2. Get list of all the nodes in the cluster
            _Roceswitches_to_upgrade = self.mGetSwitchList()

            # 3. Check for idempotency
            if self.mPatchRequestRetried():
                _ret  = self.mCheckIdemPotency()
            else:
                _ret, _no_action_taken = self.mRegularPatchRun(_Roceswitches_to_upgrade)

            self.mPatchLogInfo(f"Task: {_task_type} - Type: {PATCH_ROCESWITCH}\t\t[ ret_code = {_ret} ]")
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"{PATCH_ROCESWITCH} '{_task_type}' failed.")

        except Exception as e:
            self.mPatchLogError(f"Exception in Running Switch Rollback PreCheck {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _ret = SWITCH_ROLLBACK_PRECHECK_FAILED
                _suggestion_msg = f"{PATCH_ROCESWITCH} '{_task_type}' failed."
                self.mAddError(_ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            return _ret , _no_action_taken

    def mPatch(self):
        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken =0
        _task_type = self.mGetTask()

        try:
            self.mPatchLogInfo(
                f"\n\n---------------> Starting {self.mGetTask()} in {PATCH_ROCESWITCH} <---------------\n\n")
            # 1. Set up environment
            self.mSetEnvironment()

            # 2. Get list of all the nodes in the cluster
            _Roceswitches_to_upgrade = self.mGetSwitchList()

            # 3. Check for idempotency
            if self.mPatchRequestRetried():
                _ret  = self.mCheckIdemPotency()
            else:
                _ret, _no_action_taken = self.mRegularPatchRun(_Roceswitches_to_upgrade)

            self.mPatchLogInfo(f"Task: {_task_type} - Type: {PATCH_ROCESWITCH}\t\t[ ret_code = {_ret} ]")
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"{PATCH_ROCESWITCH} '{_task_type}' failed.")

        except Exception as e:
            self.mPatchLogError(f"Exception in Running Switch Patch {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _ret = SWITCH_PATCH_FAILED
                _suggestion_msg = f"{PATCH_ROCESWITCH} '{_task_type}' failed."
                self.mAddError(_ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_ROCESWITCH}s <---------------\n\n")
            return _ret, _no_action_taken

    def mRollBack(self):
        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken =0
        _task_type = self.mGetTask()

        try:
            self.mPatchLogInfo(
                f"\n\n---------------> Starting {self.mGetTask()} in {PATCH_ROCESWITCH} <---------------\n\n")

            # 1. Set up environment
            self.mSetEnvironment()

            # 2. Get list of all the nodes in the cluster
            _Roceswitches_to_upgrade = self.mGetSwitchList()

            # 3. Check for idempotency
            if self.mPatchRequestRetried():
                _ret  = self.mCheckIdemPotency()
            else:
                _ret, _no_action_taken = self.mRegularPatchRun(_Roceswitches_to_upgrade)

            self.mPatchLogInfo(f"Task: {PATCH_ROCESWITCH} - Type: {PATCH_ROCESWITCH}\t\t[ ret_code = {_ret} ]")
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"{PATCH_ROCESWITCH} '{_task_type}' failed.")

        except Exception as e:
            self.mPatchLogError(f"Exception in Running Switch Rollback {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _ret = SWITCH_ROLLBACK_FAILED
                _suggestion_msg = f"{PATCH_ROCESWITCH} '{_task_type}' failed."
                self.mAddError(_ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_ROCESWITCH}s <---------------\n\n")
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
        _list_of_Roceswitches_retry_case = _patchMgrObj.mGetNodeListFromNodesToBePatchedFile(aHost=self.mGetDom0ToPatchcellSwitches())

        # Clean the environment: Delete passwordless, delete input file
        self.mCleanEnvironment(self.mGetDom0ToPatchcellSwitches(), _list_of_Roceswitches_retry_case,
                                _input_file_retry_case, self.mGetCellSwitchesPatchBaseAfterUnzip(),
                                self.mGetPatchmgrLogPathOnLaunchNode(), PATCH_ROCESWITCH, _ret)

        return _ret

    def mRegularPatchRun(self, aRoceswitchesToUpgrade):
        _no_action_taken = 0
        _ret = PATCH_SUCCESS_EXIT_CODE
        # filter valid Roceswitches. This is for regular flow
        _task_type = self.mGetTask()
        _list_of_Roceswitches = []
        _discarded = []
        _precheck_data = {}
        _patchMgrObj = None

        if not self.mPatchRequestRetried():
            _list_of_Roceswitches, _discarded = self.mFilterRoceswitchesToPatch(aRoceswitchesToUpgrade)

        # Set initial Patch Status Json.
        self.mUpdatePatchProgressStatus(aNodeList=_list_of_Roceswitches, aDiscardedNodeList=_discarded)

        if not self.mPatchRequestRetried() and len(_discarded) > 0 \
                and _task_type not in [TASK_PREREQ_CHECK, TASK_ROLLBACK_PREREQ_CHECK]:
            _ret = self.mCustomCheck(_discarded)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(
                    f"Although some of the Roceswitch nodes '{_discarded}' are on requested version, required services are not running.")
                _no_action_taken += 1

        if not self.mPatchRequestRetried() and len(_list_of_Roceswitches) > 0 and _no_action_taken == 0:
            if self.mIsMockEnv():
                # in mock setup, skip rack specific operations
                return _ret, _no_action_taken

            # Prepare environment: passwordless between dom0 and cells, create input file
            _key = self.mPrepareEnvironment(self.mGetDom0ToPatchcellSwitches(), _list_of_Roceswitches,
                                                           self.mGetCellSwitchesPatchBaseAfterUnzip(), PATCH_ROCESWITCH)

            if not self.mGetDom0ToPatchcellSwitches():
                _suggestion_msg = f"Launch node is either down or patches are not staged, unable to proceed with {PATCH_ROCESWITCH} operation on {_task_type} target."
                _ret = SWITCH_PATCH_FILES_MISSING
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            if _task_type not in [TASK_PREREQ_CHECK, TASK_ROLLBACK_PREREQ_CHECK]:
                # Gather precheck data
                _precheck_data = self.mGatherRoceSwitchPreCheckData(_list_of_Roceswitches)

            # create patchmgr object with bare minimum arguments
            _patchMgrObj = InfraPatchManager(aTarget=PATCH_ROCESWITCH, aOperation=_task_type, aPatchBaseAfterUnzip=self.mGetCellSwitchesPatchBaseAfterUnzip(),
                                       aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

            # check for patchmgr session existence
            _patchMgrObj.mSetLaunchNode(aLaunchNode=self.mGetDom0ToPatchcellSwitches())

            _ret, _patchmgr_active_node = _patchMgrObj.mCheckForPatchMgrSessionExistence()

            if _ret == PATCHMGR_SESSION_ALREADY_EXIST:
                return _ret, _no_action_taken

            # create patchmgr nodes file
            _input_file = _patchMgrObj.mCreateNodesToBePatchedFile(aLaunchNode=self.mGetDom0ToPatchcellSwitches(), aHostList=_list_of_Roceswitches)

            # Run patchmgr command
            _ret = self.mPatchRoceswitchesRolling(_list_of_Roceswitches, _patchMgrObj)

            '''
             After the Roceswitch upgrade/rollback, do the postcheck and
             compare the result against the precheck data collected
             before patching/rollback.
            '''

            if _ret == PATCH_SUCCESS_EXIT_CODE and _task_type not in [ TASK_PREREQ_CHECK, TASK_ROLLBACK_PREREQ_CHECK ]:
                for _roceswitch in _list_of_Roceswitches:
                    _rc = self.mPrePostRoceSwitchCheck(_roceswitch, PATCH_ROCESWITCH)
                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                        _suggestion_msg = f"Switch postchecks failed on {_roceswitch}."
                        ret = SWITCH_POSTCHECK_FAILED
                        self.mAddError(ret, _suggestion_msg)

            # Clean the environment: Delete passwordless, delete input file
            self.mCleanEnvironment(self.mGetDom0ToPatchcellSwitches(), _list_of_Roceswitches, _input_file,
                                    self.mGetCellSwitchesPatchBaseAfterUnzip(),
                                    self.mGetPatchmgrLogPathOnLaunchNode(), PATCH_ROCESWITCH, _ret)

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

        aNodeType = PATCH_ROCESWITCH
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
        _nodes_to_be_patched_file = _patchMgrObj.mGetNodesToBePatchedFile()
        _set_tagname_switch_list_cmd = f"sed -e 's/$/:sfleaf/' -i {_nodes_to_be_patched_file}"
        _dom0 = exaBoxNode(get_gcontext())
        try:
            _dom0.mConnect(aHost=self.mGetDom0ToPatchcellSwitches())
            _i, _o, _e = _dom0.mExecuteCmd(_set_tagname_switch_list_cmd)
            _error = _e.readlines()
            _exit_code = int(_dom0.mGetCmdExitStatus())
            if _exit_code != 0:
                self.mPatchLogError(f"Unable to generate new switch file and failed with error : {str(_error)}")
                _suggestion_msg = f"Unable to generate new switch file with tag details on {self.mGetDom0ToPatchcellSwitches()}."
                _ret = SWITCH_PATCH_OPERATION_FAILED
                self.mAddError(_ret, _suggestion_msg)
                return _ret
            else:
                self.mPatchLogInfo(
                    f"Switch list file : {_nodes_to_be_patched_file} generated successfully as per current configuration.")

        except Exception as e:
            self.mPatchLogWarn("Exception encountered during creation of input list file \n.  "+str(e))
            self.mPatchLogTrace(traceback.format_exc())

        finally:
            if _dom0.mIsConnected():
                _dom0.mDisconnect()

        # Update status
        self.mUpdatePatchStatus(True, STEP_RUN_PATCH_SWITCH)

        # prepare the patchmgr command for execution using the InfraPatchManager object
        _patchmgr_cmd = _patchMgrObj.mGetPatchMgrCmd()

        # run patchmgr
        _patchMgrObj.mSetLaunchNode(aLaunchNode=self.mGetDom0ToPatchcellSwitches())

        _exit_code = _patchMgrObj.mExecutePatchMgrCmd(aPatchMgrCmd=_patchmgr_cmd)
        if _exit_code != PATCH_SUCCESS_EXIT_CODE:
            return _exit_code

        # Capture time profile details
        self.mPopulateInfrapatchingTimeStatsEntries(aNewStage="PATCH_MGR", aNewSubStage="",
                                                    aNewStageNodes=str(aListOfNodes),
                                                    aCompletedStage="PRE_PATCH", aCompletedSubStage="")

        # Monitor console log
        if _task_type in [ TASK_PATCH, TASK_ROLLBACK ]:
            _input_file = _patchMgrObj.mGetNodesToBePatchedFile()
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
                f"\n\n---------------> Starting {self.mGetTask()} in {PATCH_ROCESWITCH} <---------------\n\n")
            _ret = self.mCustomCheck()

        except Exception as e:
            self.mPatchLogError(f"Exception in Running Switch Postcheck  {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _ret = SWITCH_POSTCHECK_FAILED
                _suggestion_msg = f"{PATCH_ROCESWITCH} '{self.mGetTask()}' failed."
                self.mAddError(_ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_ROCESWITCH}s <---------------\n\n")
            return _ret , _no_action_taken

    def mOneOff(self):
        """
         PATCH_SUCCESS_EXIT_CODE for success
         Any other error code other than PATCH_SUCCESS_EXIT_CODE
        """

        _ret = PATCH_SUCCESS_EXIT_CODE
        self.mPatchLogInfo(f"\n\n---------------> Starting {TASK_ONEOFF} in {PATCH_ROCESWITCH}s <---------------\n\n")
        try:
            # Check if oneoff is enabled by the framework
            if self.mGetPluginHandler() and self.mIsOneOffPluginEnabled():
                _node_list = self.mGetSwitchList()
                self.mGetPluginHandler().mSetNodeList(_node_list)
                self.mGetPluginHandler().mSetPluginTarget(PATCH_ROCESWITCH)

                # Execute oneoff plugin
                _ret = self.mGetPluginHandler().mApply()
                return _ret
            else:
                _ret = ONEOFF_APPLY_FAILED
                _suggestion_msg = TASK_ONEOFF.upper() + " plugin is unavailable for " + PATCH_ROCESWITCH.upper()
                self.mAddError(_ret, _suggestion_msg)
                raise self.mPatchLogError(TASK_ONEOFF.upper() +
                                          " plugin is unavailable for " + PATCH_ROCESWITCH.upper())
        except Exception as e:
            self.mPatchLogWarn(f"Exception in Running Switch OneOff Plugin {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_ROCESWITCH}s <---------------\n\n")

    def mCustomCheck(self, aNodes=None):
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
        if aNodes:
            _final_Roce_list = aNodes
        else:
            # Get list of all the Roceswitches in the cluster
            _final_Roce_list = self.mGetSwitchList()

        for _roceswitch in _final_Roce_list:
            _ret = self.mPrePostRoceSwitchCheck(_roceswitch, TASK_POSTCHECK)

        return _ret
