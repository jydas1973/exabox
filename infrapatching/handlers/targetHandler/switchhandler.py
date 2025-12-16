#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/targetHandler/switchhandler.py /main/39 2025/09/02 17:58:33 ajayasin Exp $
#
# switchhandler.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      switchhandler.py - Patch - Switch Basic Functionality
#    DESCRIPTION
#      Provide basic/core Switch patching API (prereq, patch, rollback)
#      for managing the Exadata patching in the cluster implementation.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ajayasin    08/05/25 - moving handler function from clucontrol.py
#                           clucommandhandler.py to reduce the clucontrol.py
#                           size
#    araghave    05/07/25 - Enh 37892080 - TO IMPLEMENT NEWER PATCHSWITCHTYPE
#                           CHANGES APPLICABLE TO ALL SWITCH TARGET TYPES AND
#                           PATCH COMBINATIONS
#    araghave    01/23/25 - Enh 37106126 - PROVIDE A MECHANISM TO PATCH SPINE
#                           SWITCHES
#    araghave    12/20/24 - ER 37156971 - USE ENCRYPTED NON-DEFAULT PASSWORD TO
#                           SETUP KEYS DURING ADMIN SWITCH PATCHING
#    araghave    11/26/24 - Bug 37247140 - ALLOW DOMU ONEOFF PATCH TO COPY AND
#                           EXECUTE PLUGINS BASED ON AVAILABLE KEYS
#    araghave    11/05/24 - Enh 37115530 - ADD NEW SWITCH TARGET REFERENCE IN
#                           INFRA PATCHING CODE
#    asrigiri    10/01/24 - Bug 36860928 - AIM4ECS:0X03090001 - SWITCH PATCHMGR
#                           COMMAND FAILED.
#    araghave    08/14/24 - Enh 36923844 - INFRA PATCHING CHANGES TO SUPPORT
#                           PATCHING ADMIN SWITCH
#    araghave    09/16/24 - Enh 36971721 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE TARGET HANDLER FILES
#    emekala     08/13/24 - ENH 36679949 - REMOVE OVERHEAD OF INDEPENDENT
#                           MONITORING PROCESS FROM INFRAPATCHING
#    avimonda    08/13/24 - Bug 36945308 - AIM4ECS:0X03080008 - FWVERIFY
#                           COMMAND VALIDATION ON IBSWITCHES FAILED.
#    emekala     07/19/24 - ENH 36794217 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE EXACOMPUTE AND DOMU PATCHMGR CMDS
#    araghave    07/15/24 - Enh 36830077 - CLEANUP KSPLICE CODE FROM
#                           INFRAPATCHING FILES
#    emekala     06/25/24 - ENH 36748433 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE DOM0, CELL, IBSWITCH AND ROCESWITCH PATCHMGR
#                           CMDS
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    araghave    04/19/24 - ER 36452945 - TERMINATE INFRA PATCHING THREAD EARLY
#                           IN CASE OF PATCHMGR COMMAND DID NOT RUN
#    antamil     09/29/23 - Bug 35851548 - Append request Id to dbnodes file name
#                           to be unique
#    araghave    07/31/23 - Enh 35568160 - Modify fwverify validations
#                           to run in serial on all Ibswitches
#    araghave    02/22/23 - ENH 35105936 - ADD FWVERIFY VALIDATIONS DURING
#                           IBSWITCH PRECHECK
#    araghave    06/24/22 - Enh 34258082 - COPY PATCHMGR DIAG LOGS FROM LAUNCH
#                           NODES POST PATCHING ONLY IF THE EXIT STATUS IS A
#                           FAILURE
#    sdevasek    05/22/22 - ENH 33859232 - TRACK TIME PROFILE INFORMATION FOR
#                           INFRAPATCH OPERATIONS
#    araghave    04/19/22 - Enh 33516791 - EXACLOUD: DO NOT OVER WRITE THE
#                           ERROR SET BY RAISE EXCEPTION
#    araghave    04/12/22 - Enh 34048154 - ONEOFF PATCH OPERATION TO SUPPORT A
#                           PLUGIN FRAMEWORK WITH GENERIC OPTIONS
#    araghave    03/27/22 - Bug 34005263 - FIX INCORRECT EXIT STATUS VALIDATION
#                           FOR MSMPARTITIONDISCREPANCYCHECK
#    araghave    03/02/22 - Enh 33911950 - ADD SMPARTITION VALIDATION BEFORE
#                           AND AFTER IB SWITCH PATCHING IN INFRAPATCH TOOLING
#    araghave    11/23/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES
#                           FROM ERROR.PY TO INFRAPATCHERROR.PY
#    kartdura    07/22/21 - 33053150 : patchmgr existence check for cells and
#                           switches
#    araghave    07/11/21 - ENH 33099120 - INTRODUCE A SPECIFIC ERROR CODE FOR
#                           PATCHMGR CONSOLE READ TIME OUT
#    araghave    07/08/21 - BUG 33081173 - Remove older error codes from Infra
#                           patching core files
#    araghave    05/19/21 - Bug 32888765 - Get Granular Error Handling details
#                           for Cells and Switches
#    araghave    04/20/21 - Bug 32397257 - Get granular error handling details
#                           for Dom0 and DomU targets
#    araghave    02/16/21 - ENH 31423563 - PROVIDE A MECHANISM TO MONITOR
#                           INFRA PATCHING PROGRESS
#    araghave    01/12/21 - Enh 31446326 - SUPPORT OF SWITCH OPTION AS TARGET
#                           TYPE THAT TAKES CARE OF BOTH IB AND ROCESWITCH
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
                        services on IbSwitch
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
    araghave 03/04/19 - Bug29434322 - IBSwitch patch logs copy fix.
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
                        infra patching and integrate of ibswitch upgrade per
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
    nmallego 10/03/17 - Bug26726236 - Additional post check for ibswitch
    nmallego 10/09/17 - Bug26943824 - fix the ibswitch post check failure
    nmallego 10/05/17 - bug26863775 - add exadata_rack to cns payload
    nmallego 08/18/17 - patch notification for dom0, cell, domu, ibswitch
    nkedlaya 08/24/17 - Bug 26678535 - APPLY SECURITY FIXES EXADATA
                        12.2.1.1.2.170714 FAILED ON SECOND DOM0
    pnkrishn 08/11/17 - 26618330: Incorrect validate of IBSwitchVersion
                        upgrade/downgrade
    nkedlaya 08/09/17 - bug 26608328 : DOM0 patching fails with
                        __domu_patch_base_after_unzip object has no attribute
    nmallego 07/20/17 - bug26499199 - Use log_dir option with patchmgr (for
                        cell and ibswitch patch operations)
    nkedlaya 06/14/17 - bug 26242636 : EXACLOUD DOMU PATCHING SHOULD COPY
                        PATCHMGR DIAGS,TRACES TO DOM0
    nkedlaya 05/17/17 - add patching input json key constants
    nkedlaya    12/05/2017 - bug 25892555 - implement domu patching in exacloud
    bmartin     03/17/2016 - Dom0 patchmgr functionality
    marrorod    03/17/2016 - Cell/IBSwitch patchmgr functionality
    bmartin     03/18/2016 - post dom0 patch heartbeat checks
    marrorod    04/15/2016 - Master request support. Monitor added
    bmartin     04/22/2016 - Environment variables support
    marrorod    04/25/2016 - Error handling
    marrorod    04/26/2016 - Added checks: DB services, cell services, ping host, SM state
    bmartin     04/26/2016 - Added target version check
    marrorod    04/28/2016 - Lock changes. Master request acquires the lock before sending a request
"""
import os, sys, logging
import re
import traceback
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.infrapatching.handlers.targetHandler.targethandler import TargetHandler
from exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler import InfraPatchManager
from exabox.infrapatching.utils.utility import mRegisterInfraPatchingHandlers
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.ovm.clumisc import OracleVersion
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))


class SwitchHandler(TargetHandler):

    def __init__(self, *initial_data, **kwargs):

        super(SwitchHandler, self).__init__(*initial_data, **kwargs)
        self.mPatchLogInfo("SwitchHandler")
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [PATCH_IBSWITCH], self)

        '''
         Generate keys for the admin switches and return the list
         of admin switches only in case of PatchSwitchType Flag has
         all r admin set.
        '''
        if self.mCheckIfAdminSwitchCanBePatched().lower() in [ "all", "admin" ]:
            # Set the list of admin switches
            self.mSetListOfAdminSwitches(self.mGetCluControl().mGetCommandHandler().mHandlerAdminSwitchConnect())

        self.__ibswitch_rollback_version = None
        self.__ibswitch_upgrade_version = None

    def mSetEnvironment(self):

        # Set current patch. Information necessary to update status in db
        self.mSetCurrentTargetType(PATCH_IBSWITCH)

        # Set patch environment
        self.mSetcellSwitchesBaseEnvironment()

        # Add to executed targets
        self.mGetExecutedTargets().append(self.mGetCurrentTargetType())

        # Set collect time stats flag
        self.mSetCollectTimeStatsFlag(self.mGetCollectTimeStatsParam(self.mGetCurrentTargetType()))

        # Set admin switch apply flag
        self.mSetPatchSwitchType(self.mCheckIfAdminSwitchCanBePatched())

    def mGetIBSwitchesList(self):

        # Get version details
        self.__ibswitch_upgrade_version, self.__ibswitch_rollback_version = self.mGetSwitchTargetVersion()

        _no_action_taken = 0

        _ibswitches_to_upgrade = []
        # Need to get the list of switches either from single rack or
        # from whole fabric
        if self.mGetAdditionalOptions() and 'RackSwitchesOnly' in self.mGetAdditionalOptions()[0] \
                and self.mGetAdditionalOptions()[0]['RackSwitchesOnly'] == 'yes':
            self.mPatchLogWarn(
                f"Warning: Attempting to upgrade only leaf switches of the cluster {self.mGetRackName()} ")
            # Get list of ibswitches (only leaf, mostly, two switches)
            # from single rack in a fabric.
            _switchCfg = self.mGetCluControl().mGetSwitches()

            _ib_switches_from_single_rack = _switchCfg.mGetSwitchesList()
            _ib_switches_from_fabric = self.mGetSwitchList()
            """
             Discard admin switches and remove _id from each ibswitch addresses.
             Ideally, mGetSwitchesList() returns list. Example:
               ['slcs16sw-adm01.us.oracle.com_id',
                'slcs16sw-ibb0.us.oracle.com_id',
                'slcs16sw-iba0.us.oracle.com_id'
               ]
            """
            # remove '_id' from swich entry
            _ib_switches_from_single_rack = [item[:-3] for item in _ib_switches_from_single_rack]
            # get common ibswitches
            _ib_set1 = set(_ib_switches_from_single_rack)
            _ib_set2 = set(_ib_switches_from_fabric)
            _ibswitches_to_upgrade = list(_ib_set1 & _ib_set2)
        else:
            # Get list of all the ibswitches in the cluster
            _ibswitches_to_upgrade = self.mGetSwitchList()

        return _ibswitches_to_upgrade

    def mCheckIBSwitchVersion(self, aIBSwitch, aVersionToCompare=None):
        """
        Returns the firmware version installed in aIBSwitch. If aVersionToCompare is provided, then
        it returns 0 if aIBSwitch version is equal to aVersionToCompare, <0 if aIBSwitch version is lower or
        >0 if aIBSwitch version is higher.
        """

        _cmd = 'version | head -1'
        _current_version = None

        # instantiate the class oracle version
        _verobj = OracleVersion()

        _switch = exaBoxNode(get_gcontext())
        _switch.mConnect(aHost=aIBSwitch)
        _in, _out, _err = _switch.mExecuteCmd(_cmd)
        _switch.mDisconnect()
        _output = _out.readlines()

        if _output:
            _current_version = _output[0].strip().split()[-1]

        if not _current_version or not aVersionToCompare:
            return _current_version

        self.mPatchLogInfo(
            f'mCheckIBSwitchVersion: Current version = {_current_version}, and Comparing Version = {aVersionToCompare}')
       
        return _verobj.mCompareVersions(_current_version, aVersionToCompare)

    def mFilterIBSwitchesToPatch(self, aIBSwitchList):
        """
        Filters the ibswitches that must be patched based on the active/inactive version and
        the target version. It returns two lists: one for availables switches and one for discarded switches:
        [ibswitches_to_patch, discarded_ibswitches]
        """

        _nodes_to_patch = []
        _discarded_nodes = []

        # Update status
        self.mUpdatePatchStatus(True, STEP_FILTER_NODES + "_" + self.mGetCurrentTargetType())

        for _ibswitch in aIBSwitchList:
            if self.mGetTask() in [TASK_PATCH, TASK_PREREQ_CHECK]:
                _ret = self.mCheckIBSwitchVersion(_ibswitch, self.__ibswitch_upgrade_version)
                if int(_ret) >= 0:
                    self.mPatchLogInfo(
                        f"IBSwitch firmware already up to date in {_ibswitch}. IBSwitch will be discarded.")
                    _discarded_nodes.append(_ibswitch)
                    continue
            if self.mGetTask() in [TASK_ROLLBACK, TASK_ROLLBACK_PREREQ_CHECK]:
                _ret = self.mCheckIBSwitchVersion(_ibswitch, self.__ibswitch_rollback_version)
                if int(_ret) <= 0:
                    self.mPatchLogInfo(
                        f"IBSwitch firmware already at a lower version in {_ibswitch}. IBSwitch will be discarded.")
                    _discarded_nodes.append(_ibswitch)
                    continue
            self.mPatchLogInfo(f'Adding {_ibswitch} to available ibswitches list')
            _nodes_to_patch.append(_ibswitch)

        return [_nodes_to_patch, _discarded_nodes]

    # Workaround bug 22750766 - IB SWITCH ROLLBACK FAILS IF MORE THAN ONE RUN IS DONE OF PATCHMGR
    def mBug22750766(self, aTask):
        """
        Workaround bug 22750766. Delete all patch files.
        This sould be called after a ibswitch rollback.
        """

        if aTask != TASK_ROLLBACK:
            return

        self.mPatchLogInfo("Deleting all files after ibswitch rollback. Bug 22750766.")
        _dom0 = exaBoxNode(get_gcontext())
        _dom0.mConnect(aHost=self.mGetDom0ToPatchcellSwitches())
        _dom0.mExecuteCmdLog(f"rm -rf {self.mGetCellSwitchesPatchBase()}")
        _dom0.mDisconnect()

    def mBug23519421_CleanupShm(self, aIBSwitch):
        """
        Workaround bug 23519421. Delete all sundcs_36p_repository* files
        from /dev/shm in the switches.
        """

        _cmd = "rm -rf /dev/shm/sundcs_36p_repository*"

        self.mPatchLogInfo(f"{aIBSwitch}: Deleting firmware images from /dev/shm")
        _switch = exaBoxNode(get_gcontext())
        _switch.mConnect(aHost=aIBSwitch)
        _switch.mExecuteCmdLog(_cmd)
        _switch.mDisconnect()

    def mGatherIBSwitchPreCheckData(self, aIBSwitchesList):
        """
        Gets the ibswitches data before running any patch task. This data 
        will be used to compare versions post patching operations.
        """

        _data = {}
        for _ibswitch in aIBSwitchesList:
            _data[_ibswitch] = {'version': None,
                                'sm': None}

            # Update status
            self.mUpdatePatchStatus(True, STEP_GATHER_NODE_DATA + "_" + self.mGetCurrentTargetType())

            self.mPatchLogInfo(f'Starting  basic data check in ibswitch {_ibswitch}')
            _data[_ibswitch]['version'] = self.mCheckIBSwitchVersion(_ibswitch)
            _data[_ibswitch]['sm'] = self.mCheckIBSwitchSMState(_ibswitch)
            _data[_ibswitch]['ib_partition_data'] = self.mCheckIBSwitchPartitions(_ibswitch)
        return _data

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

            # Run independent postcheck method before proceeding with Prereq.
            _ret = self.mCustomCheck()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                return _ret , _no_action_taken

            '''
              Run fwverify command on IBSwitches to validate the
              health of the switches. Checks are currently run only 
              on EXACS environments and only during IBSwitch precheck.
            '''
            if self.mGetPatchSwitchType().lower() != "admin":
                _ret = self.mvalidateFwverifyCommandOnIBSwitches()
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    return _ret , _no_action_taken

            # Check for idempotency
            # IB switch patch flow
            if self.mGetPatchSwitchType().lower() != "admin":
                # Get list of all the nodes in the cluster
                _ibswitches_to_upgrade = self.mGetIBSwitchesList()

                self.mPatchLogInfo(
                    f"\n\n---------------> Starting {self.mGetTask()} in {self.mGetCurrentTargetType()} <---------------\n\n")

                if self.mPatchRequestRetried():
                    _ret  = self.mCheckIdemPotency()
                else:
                    _ret, _no_action_taken = self.mRegularPatchRun(_ibswitches_to_upgrade)

            # Admin switch patch flow
            if self.mIsAdminSwitchPatchingEnabled():
                _ret, _no_action_taken = self.mExecuteAdminSwitchInfraPatchOperations()

            self.mPatchLogInfo(f"Task: {_task_type} - Type: {self.mGetCurrentTargetType()}\t\t[ ret_code = {_ret} ]")
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"{self.mGetCurrentTargetType()} '{_task_type}' failed. Patch execution stopped.")

        except Exception as e:
            self.mPatchLogError(f"Exception in Running Switch PreCheck {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _ret = SWITCH_PATCH_PRECHECK_FAILED
                _suggestion_msg = f"{self.mGetCurrentTargetType()} '{_task_type}' failed. Patch execution stopped. Error: {str(e)}"
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

            # Run independent postcheck method before proceeding with Rollback Prereq.
            _ret = self.mCustomCheck()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                return _ret , _no_action_taken

            # Check for idempotency
            # IB switch patch flow
            if self.mGetPatchSwitchType().lower() != "admin":
                # Get list of all the nodes in the cluster
                _ibswitches_to_upgrade = self.mGetIBSwitchesList()

                self.mPatchLogInfo(
                    f"\n\n---------------> Starting {self.mGetTask()} in {self.mGetCurrentTargetType()} <---------------\n\n")

                if self.mPatchRequestRetried():
                    _ret  = self.mCheckIdemPotency()
                else:
                    _ret, _no_action_taken = self.mRegularPatchRun(_ibswitches_to_upgrade)

            # Admin switch patch flow
            if self.mIsAdminSwitchPatchingEnabled():
                _ret, _no_action_taken = self.mExecuteAdminSwitchInfraPatchOperations()

            self.mPatchLogInfo(f"Task: {_task_type} - Type: {self.mGetCurrentTargetType()}\t\t[ ret_code = {_ret} ]")
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"{self.mGetCurrentTargetType()} '{_task_type}' failed. Patch execution stopped.")

        except Exception as e:
            self.mPatchLogError(f"Exception in Running Switch Rollback PreCheck {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _ret = SWITCH_ROLLBACK_PRECHECK_FAILED
                _suggestion_msg = f"{self.mGetCurrentTargetType()} '{_task_type}' failed. Rollback Precheck execution stopped. Error: {str(e)}"
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

            # 3. Check for idempotency
            # IB switch patch flow
            if self.mGetPatchSwitchType().lower() != "admin":
                # Get list of all the nodes in the cluster
                _ibswitches_to_upgrade = self.mGetIBSwitchesList()

                self.mPatchLogInfo(
                    f"\n\n---------------> Starting {self.mGetTask()} in {self.mGetCurrentTargetType()} <---------------\n\n")

                if self.mPatchRequestRetried():
                    _ret  = self.mCheckIdemPotency()
                else:
                    _ret, _no_action_taken = self.mRegularPatchRun(_ibswitches_to_upgrade)

            # Admin switch patch flow
            if self.mIsAdminSwitchPatchingEnabled():
                _ret, _no_action_taken = self.mExecuteAdminSwitchInfraPatchOperations()

            self.mPatchLogInfo(f"Task: {_task_type} - Type: {self.mGetCurrentTargetType()}\t\t[ ret_code = {_ret} ]")
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"{self.mGetCurrentTargetType()} '{_task_type}' failed. Patch execution stopped.")

        except Exception as e:
            self.mPatchLogError(f"Exception in Running Switch Patch {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _ret = SWITCH_PATCH_FAILED
                _suggestion_msg = f"{self.mGetCurrentTargetType()} '{_task_type}' failed. Patch execution stopped.Error: {str(e)}"
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
            # IB switch patch flow
            if self.mGetPatchSwitchType().lower() != "admin":
                # Get list of all the nodes in the cluster
                _ibswitches_to_upgrade = self.mGetIBSwitchesList()

                self.mPatchLogInfo(
                    f"\n\n---------------> Starting {self.mGetTask()} in {self.mGetCurrentTargetType()} <---------------\n\n")

                if self.mPatchRequestRetried():
                    _ret  = self.mCheckIdemPotency()
                else:
                    _ret, _no_action_taken = self.mRegularPatchRun(_ibswitches_to_upgrade)

            # Admin switch patch flow
            if self.mIsAdminSwitchPatchingEnabled():
                _ret, _no_action_taken = self.mExecuteAdminSwitchInfraPatchOperations()

            self.mPatchLogInfo(f"Task: {self.mGetCurrentTargetType()} - Type: {self.mGetCurrentTargetType()}\t\t[ ret_code = {_ret} ]")
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"{self.mGetCurrentTargetType()} '{_task_type}' failed. Patch execution stopped.")

        except Exception as e:
            self.mPatchLogError(f"Exception in Running Switch Rollback {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _ret = SWITCH_ROLLBACK_FAILED
                _suggestion_msg = f"{self.mGetCurrentTargetType()} '{_task_type}' failed. Rollback execution stopped.Error: {str(e)}"
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
        _patchMgrObj = InfraPatchManager(aTarget=PATCH_IBSWITCH, aOperation=_task_type, aPatchBaseAfterUnzip=self.mGetCellSwitchesPatchBaseAfterUnzip(),
                                   aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

        # now set the component's operation specific arguments
        _patchMgrObj.mSetLaunchNode(aLaunchNode=self.mGetDom0ToPatchcellSwitches())

        _patchMgrObj.mWaitForPatchMgrCmdExecutionToComplete()

        self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")
        _exit_code = _patchMgrObj.mGetStatusCode()        

        # Clean up and gather diagnostic files:-
        # Reading the path of the input file from the reference of last request_id run
        _input_file_retry_case = _patchMgrObj.mGetNodesToBePatchedFile()

        # Read list of ibswith from input file
        _list_of_ibswitches_retry_case = _patchMgrObj.mGetNodeListFromNodesToBePatchedFile(aHost=self.mGetDom0ToPatchcellSwitches())

        # Clean the environment: Delete passwordless, delete input file
        self.mCleanEnvironment(self.mGetDom0ToPatchcellSwitches(), _list_of_ibswitches_retry_case,
                                _input_file_retry_case, self.mGetCellSwitchesPatchBaseAfterUnzip(),
                                self.mGetPatchmgrLogPathOnLaunchNode(), self.mGetCurrentTargetType(), _exit_code)

        # Workaround bug 22750766 - IB SWITCH ROLLBACK FAILS IF MORE THAN ONE RUN IS DONE OF PATCHMGR
        self.mBug22750766(_task_type)

        return _exit_code

    def mRegularPatchRun(self, aIBswitchesToUpgrade):
        _no_action_taken = 0
        _ret = PATCH_SUCCESS_EXIT_CODE
        # filter valid ibswitches. This is for regular flow
        _task_type = self.mGetTask()
        _list_of_ibswitches = []
        _discarded = []
        _patchMgrObj = None
        _list_of_nodes_for_node_progress_details = []

        if not self.mPatchRequestRetried():
            _list_of_ibswitches, _discarded = self.mFilterIBSwitchesToPatch(aIBswitchesToUpgrade)

        # Set initial Patch Status Json.
        # In case of admin switches patched, node progress
        # will be captured for admin switches as well.
        _list_of_nodes_for_node_progress_details = _list_of_ibswitches[:]
        if self.mIsAdminSwitchPatchingEnabled():
            # Get list of all the nodes in the cluster
            if len(self.mGetListOfAdminSwitches()) > 0:
                _list_of_nodes_for_node_progress_details += self.mGetListOfAdminSwitches()
                self.mPatchLogInfo(f"Admin switch patching flag is enabled and node progress details will be collected on {_list_of_nodes_for_node_progress_details}")
        self.mUpdatePatchProgressStatus(aNodeList=_list_of_nodes_for_node_progress_details, aDiscardedNodeList=_discarded)

        if not self.mPatchRequestRetried() and len(_discarded) > 0 \
                and _task_type not in [TASK_PREREQ_CHECK, TASK_ROLLBACK_PREREQ_CHECK]:
            _ret = self.mCustomCheck(_discarded)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(
                    f"Although some of the IBSwitch nodes '{_discarded}' are on requested version, required services are not running.")
                _no_action_taken += 1

        if not self.mPatchRequestRetried() and len(_list_of_ibswitches) > 0 and _no_action_taken == 0:
            '''
             Collect the precheck data before the upgrade/rollback and
             same would be compare against the result after the
             patching.
            '''

            # Prepare environment: passwordless between dom0 and IBSwitches, create input file
            _key = self.mPrepareEnvironment(self.mGetDom0ToPatchcellSwitches(), _list_of_ibswitches,
                                                           self.mGetCellSwitchesPatchBaseAfterUnzip())

            # create patchmgr object with bare minimum arguments
            _patchMgrObj = InfraPatchManager(aTarget=PATCH_IBSWITCH, aOperation=_task_type, aPatchBaseAfterUnzip=self.mGetCellSwitchesPatchBaseAfterUnzip(),
                                       aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

            # check for patchmgr session existence
            _patchMgrObj.mSetLaunchNode(aLaunchNode=self.mGetDom0ToPatchcellSwitches())

            _ret, _patchmgr_active_node = _patchMgrObj.mCheckForPatchMgrSessionExistence()
            if _ret == PATCHMGR_SESSION_ALREADY_EXIST:
                return _ret, _no_action_taken

            # Delete images from /dev/shm on each switch
            for _ibswitch in _list_of_ibswitches:
                self.mBug23519421_CleanupShm(_ibswitch)

            # The below called method validates for the NTP synchronization
            # on all of the Ibswitches.
            _ret = self.mValidateIbSwitchNTPdata(_list_of_ibswitches)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                '''
                 Returning at this stage, because patchmgr will not 
                 be run in case of NTP issues and patchmgr logs will not 
                 be generated.
                '''
                return _ret, _no_action_taken

            # Check SM Partition count
            for _ibswitch in _list_of_ibswitches:
                if not self.mSmPartitionDiscrepancyCheck(_ibswitch):
                    _ret = SWITCH_SM_PARTITION_CONFIGURATION_ERROR
                    _suggestion_msg = f"IBSwitch SM partitioning is not configured on IBSwitch : {_ibswitch} appropriately."
                    self.mAddError(_ret, _suggestion_msg)
                    return _ret, _no_action_taken

            # Gather precheck data
            if _task_type not in [TASK_PREREQ_CHECK, TASK_ROLLBACK_PREREQ_CHECK]:
                _precheck_data = self.mGatherIBSwitchPreCheckData(_list_of_ibswitches)

            if not self.mGetDom0ToPatchcellSwitches():
                _suggestion_msg = f"Launch node is either down or patches are not staged, unable to proceed with {self.mGetCurrentTargetType()} operation on {_task_type} target."
                _ret = SWITCH_PATCH_FILES_MISSING
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            # create patchmgr nodes file
            _input_file = _patchMgrObj.mCreateNodesToBePatchedFile(aLaunchNode=self.mGetDom0ToPatchcellSwitches(), aHostList=_list_of_ibswitches)

            # Run patchmgr command
            _ret = self.mPatchIBSwitchesRolling(_list_of_ibswitches, _patchMgrObj)

            '''
             After the ibswitch upgrade/rollback, do the postcheck and
             compare the result against the precheck data collected
             before patching/rollback.
            '''

            if _ret == PATCH_SUCCESS_EXIT_CODE and _task_type not in [ TASK_PREREQ_CHECK,
                                                                      TASK_ROLLBACK_PREREQ_CHECK ]:
                _ret = self.mDoIBSwitchPostCheck(_precheck_data)

            # Clean the environment: Delete passwordless, delete input file
            self.mCleanEnvironment(self.mGetDom0ToPatchcellSwitches(), _list_of_ibswitches, _input_file,
                                    self.mGetCellSwitchesPatchBaseAfterUnzip(),
                                    self.mGetPatchmgrLogPathOnLaunchNode(), self.mGetCurrentTargetType(), _ret)

            # Workaround bug 22750766 - IB SWITCH ROLLBACK FAILS IF MORE THAN ONE RUN IS DONE OF PATCHMGR
            self.mBug22750766(_task_type)

        elif not self.mPatchRequestRetried() and _no_action_taken == 0:
            _no_action_taken += 1
            # We need to populate more info about the patching operation when
            # no action is required and it requires to update ecra rack
            # status to previous
            _ret = PATCH_SUCCESS_EXIT_CODE
            _suggestion_msg = "No available ibswitches to run the patchmgr. Nothing to do here."
            self.mAddError(_ret, _suggestion_msg)

        return _ret, _no_action_taken

    def mPatchIBSwitchesRolling(self, aListOfNodes, aPatchMgrObj):

        """
        Runs the ibswitches patch operations in rolling mode.
        """

        aNodeType = self.mGetCurrentTargetType()
        _task_type = self.mGetTask()
        _exit_code = 0
        _patchmgr_cmd = ""
        _patchMgrObj = aPatchMgrObj

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
        """
         PATCH_SUCCESS_EXIT_CODE for success
         Any other error code other than PATCH_SUCCESS_EXIT_CODE
        """

        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0

        try:
            self.mPatchLogInfo(
                f"\n\n---------------> Starting {self.mGetTask()} in {self.mGetCurrentTargetType()} <---------------\n\n")
            _ret = self.mCustomCheck()

        except Exception as e:
            self.mPatchLogError(f"Exception in Running Switch Postcheck {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _ret = SWITCH_POSTCHECK_FAILED
                _suggestion_msg = f"{self.mGetCurrentTargetType()} '{self.mGetTask()}' failed. Postcheck execution stopped."
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
            self.mPatchLogWarn(f"Exception in Running Switch OneOff Plugin {str(e):a}")
            self.mPatchLogTrace(traceback.format_exc())

            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _suggestion_msg = f"Exception in Running IBSwitch OneOff Plugin {str(e)}"
                _ret = INDIVIDUAL_PATCH_REQUEST_EXCEPTION_ERROR
                self.mAddError(_ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {self.mGetCurrentTargetType()}s <---------------\n\n")
            return _ret

    def mCheckIBSwitchSMState(self, aIBSwitch, aOrigState={}):
        """
        Checks SM state. It includes: opensmd, partconfig and getmaster.
        if aOrigState is provided.
        """

        _cmd = 'service opensmd status; service partconfigd status; getmaster ' \
               '| head -n 1'
        _opensm = True
        _partitiond = True
        _sm_enabled = True
        _sm_state = None

        try:
            _switch = exaBoxNode(get_gcontext())
            _switch.mConnect(aHost=aIBSwitch)
            _in, _out, _err = _switch.mExecuteCmd(_cmd)
            _output = _out.readlines()
            if _output and len(_output) >= 3:
                if re.match("opensm is stopped", _output[0].strip()):
                    _opensm = False
                if re.match("partitiond-daemon is stopped", _output[1].strip()):
                    _partitiond = False
                if re.match("Local SM not enabled", _output[2].strip()):
                    _sm_enabled = False
                elif re.match("Local SM enabled and running", _output[2].strip()):
                    _match = re.match(".*state\s+([A-Z\s]+)", _output[2].strip())
                    if _match:
                        _sm_state = _match.groups()[0]
            _switch.mDisconnect()

            if aOrigState:
                if aOrigState['opensm'] == _opensm and aOrigState['partitiond'] == _partitiond and \
                        aOrigState['sm_enabled'] == _sm_enabled:
                    # Bu26943824 - remove all white-space and special chars from
                    # sm_state and then compare with string 'STANDBY', so that we
                    # really don't worry about whether sm_state has either
                    # 'STAND BY' or 'STANDBY'
                    aOrigState['sm_state'] = re.sub('\s', '', aOrigState['sm_state'])
                    if _sm_state is not None:
                        _sm_state = re.sub('\s', '', _sm_state)

                    if aOrigState['sm_state'] == _sm_state:
                        return True
                    if aOrigState['sm_state'] == 'MASTER' and _sm_state == 'STANDBY':
                        return True
                    if _sm_state == 'MASTER' and aOrigState['sm_state'] == 'STANDBY':
                        return True

                self.mPatchLogWarn(f'opensmd enabled    - expected: {aOrigState["opensm"]} current: {_opensm}')
                self.mPatchLogWarn(
                    f'partitiond enabled - expected: {aOrigState["partitiond"]} current: {_partitiond}')
                self.mPatchLogWarn(
                    f'SM enabled state   - expected: {aOrigState["sm_enabled"]} current: {_sm_enabled}')
                self.mPatchLogWarn(
                    f'SM state           - expected: {aOrigState["sm_state"]} current: {_sm_state}')
                return False

        except Exception as e:
            self.mPatchLogError(f"\nError in populating IBSwitch service status on '{aIBSwitch}'.\n")
            self.mPatchLogError(f"*** {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())

        return {'opensm': _opensm,
                'partitiond': _partitiond,
                'sm_enabled': _sm_enabled,
                'sm_state': _sm_state}

    def mCheckIBSwitchPartitions(self, aIBSwitch, aOrigState={}):
        """
        Checks 'smnodes' and 'smpartition' are same even after patching/rollback
        apply. Return True if list is same, and return False if list is changed.
        It also collects original state of smnode_list and smpartition_list if
        this function doesn't have aOrigState argument is passed.
        """

        _smnode_list_output = None
        _smpartition_list_output = None

        try:
            _switch = exaBoxNode(get_gcontext())
            _switch.mConnect(aHost=aIBSwitch)

            _cmd = "smnodes list"
            _in, _out, _err = _switch.mExecuteCmd(_cmd)
            if _out:
                _smnode_list_output = _out.read()
                _smnode_list_output = re.sub('\s', '', _smnode_list_output)

            _cmd = "smpartition list active no-page"
            _in, _out, _err = _switch.mExecuteCmd(_cmd)
            if _out:
                _smpartition_list_output = _out.read()
                _smpartition_list_output = re.sub('\s', '', _smpartition_list_output)

            _switch.mDisconnect()

            if aOrigState:
                # Remove special char, white-spaces before comparison the sm list output
                if _smnode_list_output is not None:
                    _smnode_list_output = re.sub('\s', '', _smnode_list_output)
                if _smpartition_list_output is not None:
                    _smpartition_list_output = re.sub('\s', '', _smpartition_list_output)

                if aOrigState['smnodes_list'] == _smnode_list_output and \
                        aOrigState['smpartition_list'] == _smpartition_list_output:
                    return True

                self.mPatchLogWarn(
                    f'SM Node List      - expected: {aOrigState["smnodes_list"]} current: {_smnode_list_output}')
                self.mPatchLogWarn(
                    f'SM Partition List - expected: {aOrigState["smpartition_list"]} current: {_smpartition_list_output}')
                return False
        except Exception as e:
            self.mPatchLogError(f"\nError in populating IBSwitch service status on '{aIBSwitch}'.\n")
            self.mPatchLogError(f"*** {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())

        return {'smnodes_list': _smnode_list_output,
                'smpartition_list': _smpartition_list_output}

    def mSmPartitionDiscrepancyCheck(self, aIBSwitch):
        """
         This method checks for the MASTER switch and 
         fetches the count of sm partition list to 
         determine pkey details. 
        """
 
        _getmaster_cmd = "getmaster | grep 'Local SM enabled and running' | grep MASTER"
        '''
         [root@slcs27sw-ibb0 ~]# getmaster | grep 'Local SM enabled and running' | grep MASTER
          Local SM enabled and running, state MASTER
         [root@slcs27sw-ibb0 ~]#
        '''
        _ret = True
 
        try:
            _switch = exaBoxNode(get_gcontext())
            _switch.mConnect(aHost=aIBSwitch)
            _in, _out, _err = _switch.mExecuteCmd(_getmaster_cmd)
            if int(_switch.mGetCmdExitStatus()) == 0:
                '''

                 Terminate IBSwitch patch postcheck if the exit
                 status is non-zero, proceed otherwise.

                 [root@slcs27sw-ibb0 ~]# smpartition check
                 OK
                 [root@slcs27sw-ibb0 ~]# echo $?
                 0
                 [root@slcs27sw-ibb0 ~]#

                 Example of a non-zero exit status reference.
                 Actual error on the MASTER node might differ
                 and issue on the IB MASTER node could not be 
                 reproduced in this case.

                 [root@slcs27sw-iba0 ~]# smpartition check
                  This switch does not run Master SM.
                  Please run the command on the switch with Master SM.
                 [root@slcs27sw-iba0 ~]# echo $?
                  6
                 [root@slcs27sw-iba0 ~]#

                '''
                _smpartition_check_cmd = "smpartition check"
                _in, _out, _err = _switch.mExecuteCmd(_smpartition_check_cmd)
                _exit_code = int(_switch.mGetCmdExitStatus())
                if _exit_code != 0:
                    self.mPatchLogError(
                        f"IBSwitch smpartitioning is not configured appropriately on {aIBSwitch} and the exit status is {_exit_code:d}.")
                    _ret = False
 
        except Exception as e:
            _ret = False
            self.mPatchLogError(f"\nError in validating IBSwitch smpartition count on '{aIBSwitch}'.\n")
            self.mPatchLogError(f"*** {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())

        finally:
            if _switch.mIsConnected():
                _switch.mDisconnect()
            return _ret

    def mDoIBSwitchPostCheck(self, aIBSwitchesData):
        """
        Runs a basic postcheck in the ibswitches. It compares the data taken before running the patchmgr.
        """

        def _check_ibswitch(aIBSwitch, aData):
            # Ping host
            if not self.mGetCluPatchCheck().mPingNode(aIBSwitch):
                _suggestion_msg = f"Ping failed for the IBSwitch : {aIBSwitch}"
                _ret = SWITCH_PING_CHECK_FAILED
                self.mAddError(_ret, _suggestion_msg)
                return False,_ret

            ### Check version
            _ret = self.mCheckIBSwitchVersion(aIBSwitch, aData['version'])

            if self.mGetTask() == TASK_PATCH:
                if _ret <= 0:
                    _suggestion_msg = f"Current version on the IBSwitch is expected to be higher than original version : {aIBSwitch}"
                    _ret = SWITCH_CURRENT_VERSION_EXPECTED_HIGHER_THAN_ORIGINAL_VER
                    self.mAddError(_ret, _suggestion_msg)
                    return False, _ret
            elif self.mGetTask() == TASK_ROLLBACK:
                if _ret >= 0:
                    _suggestion_msg = f"Current version on the IBSwitch is expected to be lower than original version : {aIBSwitch}"
                    _ret = SWITCH_CURRENT_VERSION_SHOULD_BE_LOWER_THAN_ORIGINAL_VER
                    self.mAddError(_ret, _suggestion_msg)
                    return False, _ret

            # Check SM Partition count
            if not self.mSmPartitionDiscrepancyCheck(aIBSwitch):
                _ret = SWITCH_SM_PARTITION_CONFIGURATION_ERROR
                _suggestion_msg = f"IBSwitch SM partitioning is not configured on IBSwitch : {aIBSwitch} appropriately."
                self.mAddError(_ret, _suggestion_msg)
                return False, _ret

            # Check SM state
            if not self.mCheckIBSwitchSMState(aIBSwitch, aData['sm']):
                _ret = SWITCH_SM_STATE_MISMATCH_ERROR
                _suggestion_msg = f"SM state is not as before the upgrade/downgrade : {aIBSwitch}"
                self.mAddError(_ret, _suggestion_msg)
                return False, _ret

            # Check smnodes and smpartition list
            if not self.mCheckIBSwitchPartitions(aIBSwitch, aData['ib_partition_data']):
                _ret = SWITCH_IBSWITCH_PARTITIONS_MISMTACH_ERROR
                _suggestion_msg = f"The output for the command is changed across upgrade or rollback: (1) smnodes list (2) smpartition list active no-page on {aIBSwitch}"
                self.mAddError(_ret, _suggestion_msg)
                return False, _ret

            # Check for Fedramp configurtion and restore relevant files
            if self.mGetFedRamp() == 'ENABLED' and self.mGetTask() in [TASK_PATCH, TASK_ROLLBACK]:
                self.mFedrampRestoreConfig("ibswitch")

            return True, PATCH_SUCCESS_EXIT_CODE

        # End of _check_ibswitch method

        _rc = PATCH_SUCCESS_EXIT_CODE
        _ret = True
        _failure_history_code = PATCH_SUCCESS_EXIT_CODE

        for _ibswitch in aIBSwitchesData.keys():
            # Update status
            self.mUpdatePatchStatus(True, STEP_POSTCHECKS + "_" + self.mGetCurrentTargetType())
            # Start check
            self.mPatchLogInfo(f'Starting basic postcheck in ibswitch {_ibswitch}')
            _out, _error_code = _check_ibswitch(_ibswitch, aIBSwitchesData[_ibswitch])
            if _out:
                self.mPatchLogInfo(f"Successful postcheck in ibswitch {_ibswitch}")

            _ret &= _out
            if _error_code != PATCH_SUCCESS_EXIT_CODE:
                _failure_history_code = _error_code

        # Consolidate and return Error code for all switches.
        if not _ret:
            _rc = _failure_history_code

        return _rc

    def mCustomCheck(self, aNodes=None):
        """
         This method performs a post checks independently on
         all of the Exadata targets like Dom0, DomU,IbSwitches
         and cells.

         Return value :
          PATCH_SUCCESS_EXIT_CODE -> if post check is success
          Any other error code other than PATCH_SUCCESS_EXIT_CODE
             -> if post check fails
        """

        # Enh 30208083 - Disallow patching if required/critical services
        # are not running on the upgraded node(s).
        _ret = PATCH_SUCCESS_EXIT_CODE
        if aNodes:
            _final_IB_list = aNodes
        else:
            # Get list of all the ibswitches in the cluster
            _final_IB_list = self.mGetSwitchList()

        for _ibswitch in _final_IB_list:
            _ret = self.mPrePostIBSwitchCheck(_ibswitch)

        return _ret

    def mPrePostIBSwitchCheck(self, aIBSwitch):

        """
         This method performs basic sanity checks on all IBSwitches
         in the clusters during IBSwitch prereq and postcheck operations.
         These checks are independent of previous checks.
             - return PATCH_SUCCESS_EXIT_CODE if success
             - return any other error code other than PATCH_SUCCESS_EXIT_CODE
               if failure
        """

        '''
         Check ping check only during postcheck stage as
         they are checked at early stages of prereq while
         filtering the list of nodes and is a duplication
         of checks.
        '''
        _ret = PATCH_SUCCESS_EXIT_CODE

        if self.mGetTask() in [TASK_POSTCHECK]:
            # Ping test to each IBSwitch in the cluster.
            if not self.mGetCluPatchCheck().mPingNode(aIBSwitch):
                _ret = SWITCH_PING_CHECK_FAILED
                _suggestion_msg = f"Ping test on {aIBSwitch} failed."
                self.mAddError(_ret, _suggestion_msg)
                return _ret

            self.mPatchLogInfo(f"Ping to IBSwitch : {aIBSwitch} successful.")

        # Check SM Partition count
        if not self.mSmPartitionDiscrepancyCheck(aIBSwitch):
            _ret = SWITCH_SM_PARTITION_CONFIGURATION_ERROR
            _suggestion_msg = f"IBSwitch SM partitioning is not configured on IBSwitch : {aIBSwitch} appropriately."
            self.mAddError(_ret, _suggestion_msg)
            return _ret

        # Check SM state
        if not self.mCheckIBSwitchSMState(aIBSwitch):
            _ret = SWITCH_SM_STATE_MISMATCH_ERROR
            _suggestion_msg = f"SM state is not as before the upgrade/downgrade : {aIBSwitch}"
            self.mAddError(_ret, _suggestion_msg)
            return _ret

        self.mPatchLogInfo(f"SM state of IBSwitch : {aIBSwitch} good.")

        # Check smnodes and smpartition list
        if not self.mCheckIBSwitchPartitions(aIBSwitch):
            _ret = SWITCH_IBSWITCH_PARTITIONS_MISMTACH_ERROR
            _suggestion_msg = f"The output for the command is changed across upgrade or rollback: (1) smnodes list (2) smpartition list active no-page : {aIBSwitch}"
            self.mAddError(_ret, _suggestion_msg)
            return _ret

        self.mPatchLogInfo(f"IBSwitch partition of {aIBSwitch} good.")

        # Since this is taking longer to fetch the output
        # and is delaying the patch validation process,
        # below snippet of code is commented out for now.
        # In case of any future requirement, it will be
        # enabled.

        '''
        # FWVerify check validation.
        _aIBSwitch = exaBoxNode(get_gcontext())
        _aIBSwitch.mConnect(aHost=aIBSwitch)
        _i, _o, _e = _aIBSwitch.mExecuteCmd("/usr/local/bin/fwverify")
        _rc = int(_aIBSwitch.mGetCmdExitStatus())
        _aIBSwitch.mDisconnect()
        if _rc != 0:
            _out = _o.readlines()
            self.mPatchLogError("Fwverify command failed with error, Please fix the errors and re-run patch operations, more details below.")
            for _output in _out:
                self.mPatchLogError("%s" % _output.strip("\n"))
            return False
        '''
        return _ret

    def mvalidateFwverifyCommandOnIBSwitches(self):
        """
        This method executes the fwverify command on the IBSwitches
        to check the current health on the switches.

         return
            - PATCH_SUCCESS_EXIT_CODE - if fwverify command is successful on all IBSwitches
            - FWVERIFY_COMMAND_FAILED_ON_IBSWITCHES in case of fwverify command fails on
              atleast one IBSwitch.
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _fwverify_failed_ibswitch_list = []

        for _switch in self.mGetIBSwitchesList():
            '''
             In case of issues reported during fwverify command run on
             IBSwitches, fix the issues before retrying upgrade on IBSwitches.
            '''
            _node = exaBoxNode(get_gcontext())
            try:
                _node.mConnect(aHost=_switch)
                _i, _o, _e = _node.mExecuteCmd("/usr/local/bin/fwverify")
                if int(_node.mGetCmdExitStatus()) != 0:
                    _fwverify_failed_ibswitch_list.append(_switch)
                    _error = _e.readlines()
                    if _error:
                        self.mPatchLogError(f"Fwverify error details from IBSwitch : {_switch} are as follows :")
                        for _err in _error:
                            _err = _err.strip()
                            self.mPatchLogError(f"{str(_err)}")
                else:
                    self.mPatchLogInfo(f'Fwverify command on IBSwitch : {_switch} was successful')

                _output = _o.readlines()
                if _output:
                    self.mPatchLogInfo(f"Fwverify output details from IBSwitch : {_switch} are as follows :")
                    for _out in _output:
                        _out = _out.strip()
                        self.mPatchLogInfo(f"{str(_out)}")

            except Exception as e:
                 self.mPatchLogError(f"Error while performing fwverify validation on IBSwitches. \n\n {str(e)}")
                 self.mPatchLogTrace(traceback.format_exc())
                 _fwverify_failed_ibswitch_list.append(_switch)
            finally:
                if _node.mIsConnected():
                    _node.mDisconnect()

        if len(_fwverify_failed_ibswitch_list) > 0:
            _ret = FWVERIFY_COMMAND_FAILED_ON_IBSWITCHES
            _suggestion_msg = f"Fwverify command failed on ibswitches list : {_fwverify_failed_ibswitch_list}. Please refer to logs on the IBSwitches for more details."
            self.mPatchLogError(_suggestion_msg)
            self.mAddError(_ret, _suggestion_msg)

        return _ret
