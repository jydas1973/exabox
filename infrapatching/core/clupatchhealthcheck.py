#
# $Header: ecs/exacloud/exabox/infrapatching/core/clupatchhealthcheck.py /main/107 2025/12/02 17:57:52 ririgoye Exp $
#
# clupatchhealthcheck.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      clupatchhealthcheck.py - This contains health check methods
#
#    DESCRIPTION
#      This contains health check methods
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    11/26/25  - Bug 38636333 - EXACLOUD PYTHON:ADD INSTANTCLIENT
#                            TO LD_LIBRARY_PATH
#    araghave    11/13/25 - Bug 38651311 - REPLACE FULLCVSS ELU OPTION WITH
#                           FULL IN DOMU ELU INFRA PATCHING CODE
#    remamid     11/03/25  - Add a check for exadata-secure.conf upon ssh
#                            failure between nodes bug 38498588
#    sdevasek    10/16/25  - Enh 38397714 - DOMU ELU NODE PROGRESS INFORMATION
#    araghave    09/11/25 - Enh 38173247 - EXACLOUD CHANGES TO SUPPORT DOMU ELU
#                           INFRA PATCH OPERATIONS
#    mirrodri    08/26/25  - Bug 37391418 - CHANGE THE DESCRIPTION ON ONE LOG
#                            FOR THE START AND SHUTDOWN RESPECTVELY.
#    sdevasek    08/13/25  - Bug 38298923 - GMR: CELL NON-ROLLING PATCHING
#                            FAILING AT VMS STARTUP STAGE POST PATCHMGR RUN
#    gojoseph    08/07/25  - Enh 38262352 DUMP FULL OUTPUT OF LSSERVICE -L WHEN
#                            SERVICES ARE OFFLINE
#    apotluri    07/30/25  - Bug 38176674 - EXACS:25.2.2.1: DOM0 APPLY PATCH
#                            OPERATION HUNGWHILE CHECKING IMAGEINFO AFTER
#                            PATCHMGR FAILURE
#    araghave    06/24/25 - Enhancement Request 38082882 - HANDLING EXACLOUD
#                           ELU CHANGES FOR DOM0 PATCHING
#    antamil     05/23/25  - Bug 37969822 Changes to make infrapatching key tag to be
#                            used for all patch operations
#    diguma      05/15/25 - bug37954464: Bug 37954464 - EXACS:25.2.1:BB: ELU:
#                           DOM0 PATCHING NOT HAPPENING AS NODE IS GETTING
#                           PUSHED TO DISACARDED_NODE_LIST EVEN THOUGH ACTIVE
#                           EXADATA VERSION IS LESSER THAN TARGET VERSION
#    bhpati      04/17/25 - Bug 37823796 - EXACC GEN 2| PATCHING | QMR FAILURE
#                           - EXCEPTION REPORTED IN CELL POST PATCHING CHECKS
#    sdevasek    04/14/25 - Bug 37824905 -DOM0 PATCHING USING ROOT KEYS FOR CDB
#                           DOWNTIME CHECKS
#    sdevasek    03/18/25 - Bug 35265324 - PATCHING IS NOT CHECKING CRS HB WHEN
#                           GRIDDISK STATUS IS UNKNOWN
#    araghave    03/04/25 - Enh 37541740 - UPDATE ALL MISCONNECTABLE API INFRA
#                           PATCHING REFERENCES TO TAKE AKEY AS TRUE
#    araghave    03/04/25 - Bug 37417431 - EXACS | DOMU | UNWANTED SSH
#                           CONNECTION FROM 169.254.200.1 LOCKING OPC USER
#    araghave    02/17/25 - Bug 36456705 - VERSION NAMING CONVENTION CHANGES
#                           FROM CISCO RESULTING IN ROCESWITCH PATCHING TO BE
#                           SKIPPED
#    diguma      12/06/24 - bug 37365122 - EXACS:24.4.2.1:X11M: ROLLING DOM0
#                           PATCHING FAILS WITH SSH CONNECTIVITY CHECK FAILED
#                           DURING PATCHING EVEN THOUGH EXASSH TO DOMUS WORK
#    sdevasek    12/19/24 - Enh 37304854 - ADD DB HEALTH CHECKS METHODS TO
#                           CRS HELPER MODULE
#    sdevasek    11/22/24 - Bug 37307969 - DB HEALTH CHECKS : USE DBAASCLI  
#                           SYSTEM GETDATABASES -RELOAD TO GET REALTIME DETAILS
#    araghave    11/05/24 - Enh 37115530 - ADD NEW SWITCH TARGET REFERENCE IN
#                           INFRA PATCHING CODE
#    avimonda    11/01/24 - Bug 37164251 - EXACC GEN2 | REQUEST TO SHOW
#                           PATCHING FAILURE ISSUE AS AN ERROR IN THREAD
#                           LOG AND TRACE FILE
#    sdevasek    11/15/24 - Enh 37172948 - ISOLATE CRS/HEARTBEAT/DB HEALTH
#                           CHECKS TO A SEPARATE API BASED MODULE
#    avimonda    11/01/24 - Bug 37164251 - EXACC GEN2 | REQUEST TO SHOW
#    avimonda    10/15/24 - Enhancement Request 37164727 - ENHANCE LOGGING TO
#                           INCLUDE DETAILED STARTUP CHECK
#    sdevasek    10/25/24 - Bug 37215449 - PDB DEGRADATION CHECK IS NOT 
#                           PERFORMED DURING DOMU PATCHING
#    emekala     10/17/24 - ENH 36657637 - COMMANDS EXECUTED IN PRE AND POST
#                           CHECKS SHOULD HAVE TIMEOUT
#    bhpati      10/03/24 - EXACC GEN 2| PATCHING | PROPER LOGGING TO BE
#                           DISPLAYED WHEN EXACLOUD PROCESS IS STRUCK
#    sdevasek    09/23/24 - ENH 36654974 - ADD CDB HEALTH CHECKS DURING DOM0
#                           INFRA PATCHING
#    araghave    09/18/24 - Bug 37030766 - WHEN CRS IS DOWN IN ONE OF THE DOMU,
#                           SAME DOMU NAME IS BEING PRINTED TWICE IN LIST
#    sdevasek    09/18/24 - Bug 37062446 -DOMU OS UPDATE FAILED FOR A SETUP
#                           WHERE EACH NODE PDBS ARE DOWN EVEN BEFORE PATCHING
#    remamid     09/16/24 - Modify the fix for 36518641 to handle singlenode
#                           patching Bug 37053650
#    araghave    09/10/24 - EXACC GEN2 | PATCHING | TOOLING FAILS TO ABORT
#                           PATCHING DESPITE HB FAILURE, CRS VALIDATION ERRORS
#                           CAUSING UNNECESSARY DELAYS AND OUTAGES
#    sdevasek    09/08/24 - Bug 37023741 - DOMU OS PATCH FAILS WITH ERROR 
#                           ERROR OCCURRED WHILE READING AND VALIDATING PDB
#                           METADATA TO DETECT IF PDB IS IN A DEGRADED STATE
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    sdevasek    08/26/24 - ENH 36894678 - CHECK FOR LISTENER CRS RESOURCE
#                           AS PART DOMU DB HEALTHCHECKS
#    bhpati      08/22/24 - Enh 36902510 - ALREADY CONFIGURED ROOT SSH
#                           EQUIVALENCY BETWEEN DOMU'S REPORTS 0X03010040 AT
#                           POST PATCHING STAGE.
#    diguma      08/21/24 - bug 36871736:REPLACE EXASPLICE WITH ELU(EXADATA
#                           LIVE UPDATE) FOR EXADATA 24.X
#    araghave    08/05/24 - Bug 36914729 - FIX CLUPATCHHEALTHCHECK.PY ISSUES
#                           NOT REPORTED AS PART OF EXATEST VALIDATIONS
#    diguma      07/26/24 - Bug 36888324: CHECK FOR CELL SERVICES: MORE
#                           SERVICES IN EXASCALE
#    sdevasek    07/22/24 - ENH 36773605 - MAKE PDB_DEGRADED_STATES_MATRIX 
#                           CONFIGURABLE INSTEAD OF HAVING AS CONSTANT
#    araghave    07/16/24 - Bug 36846046 - PERFORM CLUSTER WIDE CRS DEGRADATION
#                           CHECK DURING SINGLE VM CLUSTER PATCHING
#    sdevasek    07/16/24 - ENH  36820129 - IGNORE PDB DOWNTIME LOGIC ON
#                           STANDBY NODES IN DG ENV DURING DOMU PATCHING
#    sdevasek    07/03/24 - ENH 36542989  -  VERIFY PDB HELATH CHECK ACROSS
#                           CLUSTER OF THE NODES DURING DOMU PATCH TO DETECT
#                           DOWNTIME  
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    sdevasek    06/07/24 - Bug 36630512 - ADD DEALY BEFORE VALIDATING CDB
#                           SERVICE DEGRADATION DETECTION IN INFRAPATCHING
#                           DOMU OS POSTCHECK
#    sdevasek    06/07/24 - ENH 36639315 - COPY SANITY_CHECK.LOG TO EXACLOUD
#                           LOCATION FOR CDB HEALTH CHECKS FAILURE SCENARIO
#    araghave    06/06/24 - Enh 36628557 - DOMU OS PATCHING CHECKS TO PREVENT
#                           OUTAGE
#    remamid     06/05/24 - Bug 36518641 - log ssh error upon failure in
#                           _node_connectivity_check
#    sdevasek    05/29/24 - ENH 36659116 - ECRA WR FOR DOMU OS PATCHING STATE
#                           IS NOT CHANGED FROM 202 TO 500 DUE TO ERROR_MESSAGE
#                           STRING OVERFLOW FOR TABLES ECS_REQUESTS_TABLE,
#                           ECS_EXA_APPLIED_PATCHES_TABLE
#    sdevasek    05/15/24 - ENH 36296976 - VALIDATE FOR PDBS RUNNING STATE AND
#                           FOR PDBS IN RESTRICTED MODE DURING DOMU PATCHING 
#    araghave    04/25/24 - Bug 36543876 - ERROR OUT WHEN GRID HOME PATH BINARY
#                           DOES NOT EXISTS FOR CRS AUTOSTART ENABLED CHECK
#    diguma      03/24/24 - Bug 36442733 - MORE ROBUST METHOD TO OBTAIN
#                           CRS HOME
#    emekala     03/12/24 - ENH 35494282 - ENABLE AND LOG CRS AND HA CHECK
#                           ERRORS DURING DOM0 PATCH PRECHECK AS WARNINGS
#    diguma      03/11/24 - Bug 36391782 - NO ENTRY IN /ETC/ORATAB IN EXADB-XS,
#                           NEED TO USE OLR.LOC
#    emekala     02/20/24 - ENH 36283462 - DISPLAY THE CUSTOMER HOSTNAME OF THE
#                           VM NAME IN PATCHING LOG WHEN PATCHING FAILED DUE TO
#                           CRS ISSUE
#    sdevasek    01/30/24 - ENH 35306246 - ADD DB HEALTH CHECKS 
#                           DURING DOMU OS PATCHING
#    sdevasek    12/11/23 - ENH 35976285 - COMMENT OUT UNUSED CODE TO INCREASE
#                           INFRAPATCHING CODE COVERAGE
#    diguma      11/14/23 - bug 35957793: NHI - EXACS: QUARTERLY INFRA PATCHING
#                           MISSING HEARTBEAT CHECK FOR DOMU ON 1ST COMPUTE
#                           NODE
#    araghave    10/25/23 - Bug 35902513 - EXACC | ERROR HANDLING TESTING - QMR
#                           DOM0 PRECHECK ENABLED DOMU AUTORESTART THEN FAILED
#                           IN EXACLOUD BUT PRECHECK CONTINUED WITH CELL
#    sdevasek    08/30/23 - BUG 35662405 - FAILED TO SHUTDOWN VMS DURING CELL
#                           NON-ROLLING UPGRADE FAILED
#    araghave    08/14/23 - Enh 35244586 - DISABLE PRE AND POST CHECKS NOT
#                           APPLICABLE DURING MONTHLY PATCHING
#    sdevasek    07/08/23 - BUG 35555704 - EXACS:BB:INFRAPATCHING:DOM0 PATCH
#                           FAILED AS VM IS NOT ACCESSIBLE
#    araghave    05/08/23 - Enh 35353733 - REFACTOR AND USE NEW SSH
#                           CONNECTIVITY VALIDATION METHODS FROM
#                           CLUAPATCHHEALTHCHECK.PY
#    sdevasek    04/12/23 - BUG 35272253 - PERFORM HEARTBEAT VALIDATIONS POST
#                           ADDING RELEVANT DISKMON MESSAGES IN ALERT LOG
#    araghave    02/24/23 - Enh 35113451 - SSH CONNECTIVITY TEST FOR
#                           INFRAPATCHING NOT WORKING
#    araghave    03/17/23 - Enh 35062878 - VALIDATE CRS AUTO STARTUP SETTINGS
#                           DURING DOM0 PATCHING
#    diguma      02/19/23 - Bug 35080646 - check if FS is encrypted
#    araghave    01/13/22 - Enh 34859379 - PERFORM CRS BOUNCE BEFORE HEARTBEAT
#                           CHECK TIMEOUT, IF DOMUs ARE UNABLE TO ESTABLISH
#                           A HEART BEAT TO THE CELLS
#    araghave    12/02/22 - Bug 34709138 - PROVIDE APPROPRIATE ERROR HANDLING
#                           DETAILS IN CASE OF IMAGE VERSION IS NONE
#    josedelg    11/03/22 - Bug 34760850 - Recreate auto startup symlinks
#    araghave    09/29/22 - Enh 34623863 - PERFORM SPACE CHECK VALIDATIONS
#                           BEFORE PATCH OPERATIONS ON TARGET NODES
#    sdevasek    09/26/22 - BUG 34636664 - NO NEED TO CALL FETCH SWITCH VERSION
#                           EVEN AFTER GETTING VERSION TO UPDATE NODE_PROGRESS
#    araghave    09/14/22 - Enh 34480945 - MVM IMPLEMENTATION ON INFRA PATCHING
#                           CORE FILES
#    sdevasek    09/01/22 - ENH 34510052 - EXACLOUD CHANGES TO GET IMAGEINFO
#                           DETAILS AS PART OF NODE_PROGRESS_STATUS
#    araghave    03/10/22 - Bug 33948815 - SSH KEYS CLEANUP FAILED POST PATCH
#                           OPERATION
#    araghave    03/08/22 - ER33689675 - Move MOS NOTE 2829056.1 messages to
#                           ecra_error_catalog.json
#    nmallego    01/12/22 - Bug33689655 - UPDATE DOMU FAIL AND SHOW ERROR
#                           MESSAGE WITH MOS NOTE 2829056.1
#    araghave    12/08/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES
#                           FROM ERROR.PY TO INFRAPATCHERROR.PY
#    araghave    12/06/21 - Enh 33052410 - Purge System first boot image file
#                           for Dom0 space management
#    araghave    11/25/21 - Bug 33607195 - Validate ssh connectivity check
#                           between Roceswitch and Dom0 using ciscoexa user
#    nmallego    11/23/21 - Bug33563022 - Call get-backup-version for compute
#                           rollback only
#    nmallego    11/19/21 - Bug33584494 - Optimize VM shutdown period 
#    nmallego    11/10/21 - Bug33521580 - Update griddisk msg appropriately
#    araghave    11/10/21 - Bug 33555311 - DOM0 PRECHECK AND POSTCHECKS FAIL
#                           WITH ERROR - AUTO STARTUP SOFT LINK MISSING FOR THE
#                           DOMU RUNNING ON THE CURRENT DOM0
#    nmallego    11/08/21 - Bug33531232 - Use standalone shutdown/startup 
#                           methods for VM operation. 
#    araghave    10/20/21 - Enh 33486853 - MOVE TIMEOUT AND OTHER CONSTANTS OUT
#                           OF CODE INTO CONFIG/CONSTANT FILES
#    araghave    10/05/21 - Enh 33378051 - VALIDATE FOR DOMU AUTO STARTUP
#                           DETAILS DURING PRE/POST DOM0 PATCH OPERATIONS
#    araghave    09/23/21 - Enh 33366173 - INFRA PATCHING TO NOTIFY END USER
#                           REGARDING GRID DISKS IN OFFLINE STATE
#    sdevasek    09/22/21 - Bug 32799615 - EXADATA VM CLUSTER OS IMAGE UPDATE
#                           MISSING FLAG ALLOW_ACTIVE_NETWORK_MOUNTS
#    araghave    09/17/21 - Enh 33345801 - ADD SSH PRE-CHECKS AS PART OF INFRA
#                           PATCHING PRECHECKS
#    araghave    09/03/21 - Enh 32626119 - Infra patching to notify end user
#                           regarding Grid Disks in Unused/Syncing status
#    araghave    09/01/21 - Enh 33297488 - Introduce exit point during 
#                           dbserver_backup run in case issues are observed.
#    nmallego    08/31/21 - Bug33249608 - Support non-rolling option
#    pkandhas    05/10/21 - Bug32864782 - use dbmcli instead of dbserverd
#    nmallego    04/30/21 - Bug32835753 - Support case: Exasplice version
#                           return empty
#    alsepulv    03/16/21 - Enh 32619413: remove any code related to Higgs
#    nmallego    12/23/20 - Bug32320037 - imageinfo verexasplice is not
#                           applicable on cell
#    vmallu      12/10/20 - bug-32245380 - virsh list cmd returing empty line 
#                           in end mCheckVMsUp is returning a list with 
#                           single quotes  
#    nmallego    11/06/20 - ER 32115347 - exasplice upgrade on fresh rack and
#                                         also support exasplice rollback 
#    nmallego    10/27/20 - Enh 31540038 - INFRA PATCHING TO APPLY/ROLLBACK
#                           EXASPLICE/MONTHLY BUNDLE
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#

import traceback
from time import sleep, time
import socket
import json
from exabox.core.Node import exaBoxNode
from exabox.infrapatching.handlers.loghandler import LogHandler
from exabox.core.Context import get_gcontext
from exabox.infrapatching.utils.utility import mGetInfraPatchingHandler, mIsFSEncryptedNode, \
    mGetInfraPatchingConfigParam, mTruncateErrorMessageDescription, mGetPdbDegradedStatesMatrix, \
    mCheckAndFailOnCmdTimeout, mGetSshTimeout, mExaspliceVersionPatternMatch, mQuarterlyVersionPatternMatch
from exabox.ovm.cludbaas import ebCluDbaas
from exabox.ovm.clumisc import OracleVersion, ebCluSshSetup
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.ovm.hypervisorutils import *
from exabox.infrapatching.utils.infrapatchexecutionvalidator import InfrapatchExecutionValidator
from exabox.ovm.vmcontrol import ebVgLifeCycle, exaBoxOVMCtrl
from exabox.infrapatching.utils.utility import runInfraPatchCommandsLocally
from exabox.infrapatching.utils.constants import EXAPATCHING_KEY_TAG

class ebCluPatchHealthCheck(LogHandler):
    """
    Handles the patch prechecks/postchecks done to ensure the state of the node
    after running the patchmgr
    """

    def __init__(self, aCluCtrlObj, aGenericHandler=None):
        super(ebCluPatchHealthCheck, self).__init__()
        self.cluctrl = aCluCtrlObj
        self.ghandler = aGenericHandler

    def mPingNode(self, aRemoteNode, aSshUser='root'):
        """
        Pings a host. Then it tries to connect via ssh.
        """
        _ret = True
        self.mPatchLogInfo(f"Checking connection to {aRemoteNode}.")

        if self.cluctrl.mPingHost(aRemoteNode):
            _node = exaBoxNode(get_gcontext())
            if aSshUser != "root":
                self.mPatchLogInfo(f"Connecting to {aRemoteNode} as {aSshUser} user")
                _node.mSetUser(aSshUser)
                _node.mSetMaxRetries(self.ghandler.mGetMaxNumberofSshRetries())
            try:
                _node.mConnectTimed(aHost=aRemoteNode, aTimeout=10)
                if _node.mIsConnected():
                    _node.mDisconnect()
            except:
                self.mPatchLogError(f'Failed to connect to {aRemoteNode} (pingable though).')
                _ret = False
            finally:
                # Reset back to root user once the ping check is complete.
                if aSshUser and aSshUser != "root":
                    _node.mSetUser('root')
                    _node.mSetMaxRetries(self.ghandler.mGetMaxNumberofSshRetries())
                return _ret
        else:
            self.mPatchLogError(f'Failed to ping {aRemoteNode}.')
            _ret = False
       
        return _ret

    def mCheckTargetVersionForElu(self, aNode, aNodeType, aVersionToCompare=None):
        """
         Returns the current image version installed on aNode. If aVersionToCompare is provided, the current version on
         aNode is extracted and compared to aVersionToCompare. returns 0 if equal, >0 if aNodes current version is bigger,
         <0 if aNodes current version is lower.
        """
        _suggestion_msg = None
        _node = exaBoxNode(get_gcontext())
        _current_version = None
        _live_version = None
        _cur_ver_exa = None
        _ret = PATCH_SUCCESS_EXIT_CODE
        _rc = 1
        _elu_info = {}
        _applied_elu_type_on_domu = None
        _is_elu_outstanding_work_applicable = False

        # instantiate the class oracle version
        _verobj = OracleVersion()

        try:
            _ret, _cur_ver_exa, _elu_info, _is_elu_outstanding_work_applicable = self.ghandler.mGetExadataLiveUpdateDetails(aNode)
            if _ret == PATCH_SUCCESS_EXIT_CODE and len(_elu_info) > 0:
                _live_version = _elu_info['elu_version']
                _applied_elu_type_on_domu = _elu_info['elu_type']

            if _cur_ver_exa:
                if not _cur_ver_exa.strip().lower().startswith('undefined'):
                    '''
                     If env is not having exasplice patches applied yet, then we need to simply
                     allow patching for fresh exasplice patch, by assigning lowest value ( i.e, 1).
                    '''
                    _current_version = _cur_ver_exa

                    if _applied_elu_type_on_domu and _applied_elu_type_on_domu in [ "high", "all", "full" ]:
                        _applied_elu_type_on_domu = _applied_elu_type_on_domu + "cvss"
                        self.mPatchLogInfo(f"Exadata live update applied - {_applied_elu_type_on_domu} on node - {aNode}")

                    if _live_version:
                        self.mPatchLogInfo(f"Exadata live update version - {_live_version}")
                        _current_version = _live_version
                        if _live_version:
                            # ELU option validations applicable only to domu patching.
                            if aNodeType == PATCH_DOMU and not _is_elu_outstanding_work_applicable:
                                _rc = 0
                            else:
                                self.mPatchLogInfo(f'mCheckTargetVersionForElu: Node {aNode} with QMR version {_cur_ver_exa} has a live update version {_live_version} and node will be updated to {self.ghandler.mGetTargetVersion()}')
                    else:
                        self.mPatchLogInfo(f'mCheckTargetVersionForElu: Node {aNode} with QMR version {_cur_ver_exa} has no live update version applied. Hence node will be updated to {self.ghandler.mGetTargetVersion()}')
                    self.mPatchLogInfo(f'mCheckTargetVersionForElu: Image version retrieved = {_current_version} on node - {aNode}.')
            else:
                self.mPatchLogInfo('mCheckTargetVersionForElu: Not able to fetch Image version on node - {aNode}..')

            if not _current_version:
                _suggestion_msg = f"mCheckTargetVersionForElu: Unable to obtain or parse image version for {aNode}. Got: {_current_version}"
                _ret = IMAGE_VERSION_EMPTY_OR_INVALID
                self.ghandler.mAddError(_ret, _suggestion_msg)
                raise Exception(_suggestion_msg)

            if not aVersionToCompare or not _current_version:
                _rc = _current_version

        except Exception as e:
            self.mPatchLogWarn(f"mCheckTargetVersionForElu: Exception {str(e)} occurred while fetching and comparing the version on DomU - {aNode}.")
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            if self.ghandler.mGetTask() in [ TASK_PATCH, TASK_PREREQ_CHECK ] and _current_version and aVersionToCompare:
                '''
                 Assumption is that the target version is always higher than the current version in the below case.
                '''
                _rc = _verobj.mCompareVersions(_current_version, aVersionToCompare)
        return _rc

    def mCheckTargetVersionDuringDomURollback(self, aNode):
        """
        Returns the current image version installed on aNode. If aVersionToCompare is provided, the current version on
        aNode is extracted and compared to aVersionToCompare. returns 0 if equal, >0 if aNodes current version is bigger,
        <0 if aNodes current version is lower. This method is specific to DomU rollback operations.
        """
        _suggestion_msg = None
        _rc = 0
        _live_update_version = None
        _is_elu_rollback = False
        _ret = PATCH_SUCCESS_EXIT_CODE

        _ret, _cur_ver_exa, _elu_info, _ = self.ghandler.mGetExadataLiveUpdateDetails(aNode)
        if _ret == PATCH_SUCCESS_EXIT_CODE and len(_elu_info) > 0:
            _live_update_version = _elu_info['elu_version']

        if _live_update_version:
            self.mPatchLogInfo(f"mCheckTargetVersionDuringDomURollback: Exadata live update version - {_live_update_version}")
            if _cur_ver_exa == _live_update_version:
                # Both Current and Target version will be the same in case of an ELU rollback in case of elu option applied is allcvss, full and highcvss.
                self.mPatchLogInfo(
                    f'mCheckTargetVersionDuringDomURollback: Both Current and Target version on node - {aNode} will be the same in case of an ELU rollback.')
            else:
                # ELU applied version will be higher than QMR version in cae of applypending performed previously.
                self.mPatchLogInfo(
                    f'mCheckTargetVersionDuringDomURollback: Current and Target version on node - {aNode} are different as applypending ELU operation performed and rollback is performed.')
            '''
             Rollback will only be performed in case of _rc returns 1, in case of 0 or -1 _rc returned,
             rollback operations are skipped as infra patching assumes node is already at an intended version.
            '''
            _rc = 1
            _is_elu_rollback = True
        return _rc, _is_elu_rollback

    def mCheckTargetVersion(self, aNode, aNodeType, aVersionToCompare=None, aInactiveImage=False, aIsexasplice=False, aDomUPostCheck=False):
        """
        Returns the current image version installed on aNode. If aVersionToCompare is provided, the current version on
        aNode is extracted and compared to aVersionToCompare. returns 0 if equal, >0 if aNodes current version is bigger,
        <0 if aNodes current version is lower
        """
        _suggestion_msg = None
        _is_elu_rollback = False

        '''
         Below API will be used in case of Dom0 and Domu ELU
         patching.
        '''
        if self.ghandler.mGetTask() in [ TASK_PATCH, TASK_PREREQ_CHECK ] and self.ghandler.mIsElu() and aNodeType == PATCH_DOMU:
            _rc = self.mCheckTargetVersionForElu(aNode, aNodeType, aVersionToCompare)
            return _rc

        '''
          Below method validates if a DomU rollback is performed based on
          the Elu details as per imageinfo command output or based on the 
          backup partition details. It does not depend on the exasplice or 
          ELU flag details sent through payload.
        '''
        if aNodeType == PATCH_DOMU and self.ghandler.mGetTask() in [ TASK_ROLLBACK ]:
            _rc, _is_elu_rollback = self.mCheckTargetVersionDuringDomURollback(aNode)
            if _is_elu_rollback:
                return _rc
            elif aDomUPostCheck:
                self.mPatchLogInfo(f'mCheckTargetVersion: DomU Rollback postchecks are performed on Domu - {aNode} and node is at an intended version, return code _rc is {_rc}.')
                return _rc
            else:
                self.mPatchLogInfo(f'mCheckTargetVersion: DomU rollback is performed based on the backup partition details on Domu - {aNode}.')

        # TODO this only works for dbnodes and cells
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aNode)

        _cur_ver_exa = None
        if aIsexasplice and aNodeType == PATCH_DOM0:
            # check if dom0 is not of the 6 digit exasplice version format.
            _cmd = 'imageinfo -ver'
            _i, _o, _e = _node.mExecuteCmd(_cmd, aTimeout=SHELL_CMD_DEFAULT_TIMEOUT_IN_SECONDS)
            mCheckAndFailOnCmdTimeout(aCmd=_cmd, aNode=_node, aHandler=self.ghandler)
            if _o:
                _cur_ver_exa = _o.read()

            if not self.ghandler.mIsElu():
                # if version is not of the 6 digit exasplice version format.
                _cmd = 'imageinfo -verexasplice'
        else:
            _cmd = 'imageinfo -ver'

        _current_version = None
        _live_version = None
        _parse = False

        # instantiate the class oracle version
        _verobj = OracleVersion()


        # Below code runs only when someone requested inactive version which will
        # be as part of dom0/domu rollback.
        if aInactiveImage:
            if aNodeType in [PATCH_DOM0, PATCH_DOMU]:


                '''
                  Command Example : If the version details are unavailable, Infra
                                    patching should terminate with Error details
                                    immediately.

                      [root@scaqar04dv0404 ~]# /opt/oracle.SupportTools/dbserver_backup.sh --check-rollback --get-backup-version
                      21.2.2.0.0.210709
                      [root@scaqar04dv0404 ~]# echo $?
                      2
                      [root@scaqar04dv0404 ~]#

                      In case above command exit status is 1 or 3, Infra patching terminates with errors, below exit
                      code details are observed when dbserver_backup.sh -h is provided.

                       - check rollback availability. Returns
                       - 0 - rollback is available.
                       - 1 - some error is occurred.
                       - 2 - rollback is available with the same version as an active partition has.
                       - 3 - rollback is not available.
                '''

                # need to check if filesystem is encrypted and pass extra option
                additional_dbserver_cmd = ''
                _isExaCC = self.ghandler.mIsExaCC()
                if aNodeType == PATCH_DOMU and not _isExaCC and \
                  self.cluctrl.mIsKVM(aHostname=aNode) and mIsFSEncryptedNode(_node, aNode, self.ghandler):
                    additional_dbserver_cmd = f" --key-api {KEY_API}"

                _cmd_exit_code_checker = f"/opt/oracle.SupportTools/dbserver_backup.sh --ignore-nfs-smbfs-mounts --check-rollback --get-backup-version {additional_dbserver_cmd}"
                _i, _o, _e = _node.mExecuteCmd(_cmd_exit_code_checker, aTimeout=SHELL_CMD_DEFAULT_TIMEOUT_IN_SECONDS)
                mCheckAndFailOnCmdTimeout(aCmd=_cmd_exit_code_checker, aNode=_node, aHandler=self.ghandler)
                _exit_code = int(_node.mGetCmdExitStatus())

                if int(_exit_code) == 0:
                    self.mPatchLogInfo(f"Rollback is available on {aNode}.")
                elif int(_exit_code) == DBSERVER_BACKUP_EXIT_CODE_ERROR:
                    _suggestion_msg = f"Error occurred during check of rollback version on {aNode}. Infra patch operation stopped."
                elif int(_exit_code) == 2:
                    self.mPatchLogInfo(f"Rollback is available with the same version as an active version on {aNode}.")
                elif int(_exit_code) == DBSERVER_BACKUP_EXIT_CODE_NO_ROLLBACK_AVAILABLE:
                    _suggestion_msg = f"Rollback not possible on {aNode}, unable to get inactive partition details. Infra patch operation stopped."

                if int(_exit_code) == DBSERVER_BACKUP_EXIT_CODE_ERROR or int(_exit_code) == DBSERVER_BACKUP_EXIT_CODE_NO_ROLLBACK_AVAILABLE:
                    if _node.mIsConnected():
                        _node.mDisconnect()
                    _rc = UNABLE_TO_GET_INACTIVE_PARTITION_IMAGE_VERSION
                    self.ghandler.mAddError(_rc, _suggestion_msg)
                    raise Exception(_suggestion_msg)

                # Below command is actually used to get the rollback version
                _cmd = (
                    f"/opt/oracle.SupportTools/dbserver_backup.sh --ignore-nfs-smbfs-mounts --check-rollback {additional_dbserver_cmd} | grep -a 'Image version on the spare root partition'")

                _parse = True

            elif aNodeType == PATCH_CELL:
                _cmd = "imageinfo -inactive -ver"

        _i, _o, _e = _node.mExecuteCmd(_cmd, aTimeout=SHELL_CMD_DEFAULT_TIMEOUT_IN_SECONDS)
        mCheckAndFailOnCmdTimeout(aCmd=_cmd, aNode=_node, aHandler=self.ghandler)
        _node.mDisconnect()

        _o = _o.readlines()
        if _o:
            if _parse:
                _re_out = re.match('.*Image version on the spare root partition is\s+(.+)', _o[0].strip())
                if _re_out:
                    _current_version = _re_out.groups()[0]
                    '''
                    In case of monthly/exasplice apply, we will get the following output:
                        INFO] Image version on the spare root partition is 20.1.1.0.0.200719.exasplice.201025
                    otherwise,
                        INFO] Image version on the spare root partition is 20.1.1.0.0.200719
                    '''
                    # In case 'exasplice' found in cmd output, then read exasplice version, otherwise
                    # regular patch version.
                    if aIsexasplice:
                        if _current_version.find('exasplice') > -1:
                            _current_version = _current_version.split('.exasplice.')[1]
                    else:
                        _current_version = _current_version.split('.exasplice.')[0]

                    self.mPatchLogInfo(f'Inactive image version retrieved = {_current_version}')
            else:
                if not _o[0].strip().lower().startswith('undefined'):
                    '''
                    If env is not having exasplice patches applied yet, then we need to simply
                    allow patching for fresh exasplice patch, by assigning lowest value ( i.e, 1).
                    '''
                    if aIsexasplice:
                        if not self.ghandler.mIsElu():
                            _re_out = re.match('Invalid command line option -verexasplice', _o[0].strip())
                            # Fresh install, assign '000000' to current_version so that it allow exasplice
                            # patch simply.
                            if _re_out:
                                self.mPatchLogInfo(f'Not found exasplice upgrade on node {aNode}. Allowing exasplice upgrade.')
                                _current_version = "000000"
                            # It has exasplice version. Example: 201025
                            else:
                                _current_version = _o[0].strip()
                        else:
                            _current_version = _o[0].strip()
                            _node.mConnect(aHost=aNode)
                            _cmd = 'imageinfo -versionliveupdate'
                            _i, _o, _e = _node.mExecuteCmd(_cmd, aTimeout=SHELL_CMD_DEFAULT_TIMEOUT_IN_SECONDS)
                            mCheckAndFailOnCmdTimeout(aCmd=_cmd, aNode=_node, aHandler=self.ghandler)
                            '''
                            [root@sea201323exdd011 ~]# imageinfo -versionliveupdate
                            24.1.1.0.0.240605 (Exadata Live Update Version: 24.1.2.0.0.240727 (CVSS 1-10))
                            '''
                            _node.mDisconnect()
                            _o = _o.readlines()
                            if _o:
                                _live_version = _o[0].strip()

                                _live_version = _live_version.split('Version: ')
                                _live_version = _live_version[-1].split(' ')[0]
                                if len(_live_version) > 0:
                                    _current_version = _live_version
                                    if _cur_ver_exa:
                                        if _live_version:
                                            self.mPatchLogInfo(f'Node {aNode} with QMR version {_cur_ver_exa} has a live update version {_live_version} and node will be updated to {self.ghandler.mGetTargetVersion()}')
                                        else:
                                            self.mPatchLogInfo(f'Node {aNode} with QMR version {_cur_ver_exa} has no live update version applied. Hence node will be updated to {self.ghandler.mGetTargetVersion()}')

                    # Regular patch version. Example: 20.1.1.0.0.200719
                    else:
                        _current_version = _o[0].strip()
                    self.mPatchLogInfo(f'Image version retrieved = {_current_version}')
        else:
            self.mPatchLogInfo('mCheckTargetVersion: Not able to fetch Image version.')

            # No exasplice patches applied and hence returning lowest version
            # so that, in some cases it indicates to allow exaplice patching
            if aIsexasplice and aNodeType == PATCH_DOM0:
                self.mPatchLogInfo('mCheckTargetVersion: No Exasplice patches found.')
                # note that the caller will receive the image version and compare if
                # the version of is the Exadata version naming convention.
                if mExaspliceVersionPatternMatch(_cur_ver_exa):
                    _current_version = "000000"
                else:
                    _current_version = _cur_ver_exa

        _e = _e.readlines()
        if _e:
            self.mPatchLogInfo(f'mCheckTargetVersion: Error in fetching image version: ({_e})')

        if not aInactiveImage and not _current_version:
            _suggestion_msg = f"Unable to obtain or parse image version for {aNode}. Got: {_current_version}"
            _rc = IMAGE_VERSION_EMPTY_OR_INVALID
            self.ghandler.mAddError(_rc, _suggestion_msg)
            raise Exception(_suggestion_msg)

        if not aVersionToCompare or not _current_version:
            return _current_version

        # if format of aVersionToCompare is like 240809, it indicates 23 or lower,
        # so keep current version 24 on current node
        # if new format it should use exacloud method
        if aIsexasplice and aNodeType == PATCH_DOM0 and mQuarterlyVersionPatternMatch(_current_version) and aVersionToCompare and len(aVersionToCompare) == 6:
            return 1

        """taken from  /opt/oracle.cellos/host_access_control """
        return _verobj.mCompareVersions(_current_version, aVersionToCompare)

    def mCheckIBSwitchVersion(self, aIBSwitch, aVersionToCompare=None):
        """
        Returns the firmware version installed in aIBSwitch. If aVersionToCompare is provided, then
        it returns 0 if aIBSwitch version is equal to aVersionToCompare, <0 if aIBSwitch version is lower or
        >0 if aIBSwitch version is higher.
        """

        _ret = 0
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

    def mCheckImageSuccess(self, aNode):
        """
        Checks the image installation status.
        """

        _ret = False
        _cmd = "/usr/local/bin/imageinfo -status "
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aNode)
        _in, _out, _err = _node.mExecuteCmd(_cmd, aTimeout=SHELL_CMD_DEFAULT_TIMEOUT_IN_SECONDS)
        mCheckAndFailOnCmdTimeout(aCmd=_cmd, aNode=_node, aHandler=self.ghandler)
        _output = _out.readlines()
        if _output:
            if _output[0].strip().lower().startswith('success'):
                _ret = True
            else:
                self.mPatchLogError(f"Imageinfo output: \n {str(_output)}")
        _node.mDisconnect()
        return _ret

    def mCheckFileExists(self, aNode, aFile):
        _file_exists = False
        _node = exaBoxNode(get_gcontext())
        try:
            _node.mConnect(aHost=aNode)
            if _node.mFileExists(aFile):
                _file_exists = True
        except Exception as e:
            self.mPatchLogWarn(
                f"Exception {str(e)} occurred while checking for the presence of the file {aFile} on the node {aNode}.")
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()

        return _file_exists

    def mCheckFileExistsWithUserContext(self, aNode, aFile, aUser=None):
        _file_exists = False
        _node = exaBoxNode(get_gcontext())
        try:
            if aUser:
                _node.mSetUser(aUser)
            _node.mConnect(aHost=aNode)
            _ls_cmd_str = f"/usr/bin/ls {aFile}"
            _, _out, _ = _node.mExecuteCmd(_ls_cmd_str)
            _exit_code = _node.mGetCmdExitStatus()
            if _exit_code == 0:
                self.mPatchLogInfo(f"File {aFile} exists so returning True")
                _file_exists = True

        except Exception as e:
            self.mPatchLogWarn(
                f"Exception {str(e)} occurred while checking for the presence of the file {aFile} on the node {aNode}.")
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()

        return _file_exists

    def mGetImageVersionInfoDetails(self, aNode, aTargeType):
        """
        This method used to get imageversion details.
        """

        _image_info_details = {}
        _image_info_keys_name_dict = {}
        _node = exaBoxNode(get_gcontext())

        """
        domu imageinfo output:
        ---------------------
        [root@slcs27dv0305m ~]# /usr/local/bin/imageinfo
        
        Kernel version: 4.14.35-2047.511.5.5.1.el7uek.x86_64 #2 SMP Wed Apr 6 10:05:39 PDT 2022 x86_64
        Uptrack kernel version: 4.14.35-2047.512.6.el7uek.x86_64 #2 SMP Wed Apr 6 16:48:21 PDT 2022 x86_64
        Image kernel version: 4.14.35-2047.511.5.5.1.el7uek
        Image version: 21.2.12.0.0.220513
        Image activated: 2022-08-12 16:25:09 +0000
        Image status: success
        Node type: GUEST
        System partition on device: /dev/mapper/VGExaDb-LVDbSys2
        
        [root@slcs27dv0305m ~]#        
        
        dom0 imageinfo output:
        ---------------------
        [root@scaqan04adm07 ~]# /usr/local/bin/imageinfo
        
        Kernel version: 4.14.35-2047.511.5.5.1.el7uek.x86_64 #2 SMP Wed Apr 6 10:05:39 PDT 2022 x86_64
        Uptrack kernel version: 4.14.35-2047.515.3.el7uek.x86_64 #2 SMP Thu Jun 30 18:46:19 PDT 2022 x86_64
        Image kernel version: 4.14.35-2047.511.5.5.1.el7uek
        Image version: 21.2.11.0.0.220525
        Image activated: 2022-07-13 03:20:18 -0700
        Image status: success
        Exadata software version: 21.2.11.0.0.220525
        Exasplice update version: 220811.1
        Exasplice update activated: 2022-08-16 07:52:04 -0700
        Node type: KVMHOST
        System partition on device: /dev/mapper/VGExaDb-LVDbSys1
        
        [root@scaqan04adm07 ~]#

        cell imageinfo output:
        --------------------- 
        [root@slcs27celadm04 ~]# /usr/local/bin/imageinfo
        
        Kernel version: 4.14.35-2047.511.5.5.1.el7uek.x86_64 #2 SMP Wed Apr 6 10:05:39 PDT 2022 x86_64
        Cell version: OSS_21.2.11.0.0_LINUX.X64_220414.1
        Cell rpm version: cell-21.2.11.0.0_LINUX.X64_220414.1-1.x86_64
        
        Active image version: 21.2.11.0.0.220414.1
        Active image kernel version: 4.14.35-2047.511.5.5.1.el7uek
        Active image activated: 2022-07-21 02:32:04 +0000
        Active image status: success
        Active node type: STORAGE
        Active system partition on device: /dev/md5
        Active software partition on device: /dev/md7
        
        Cell boot usb partition: /dev/sdm1
        Cell boot usb version: 21.2.11.0.0.220414.1
        
        Inactive image version: 21.2.9.0.0.220216
        Inactive image activated: 2022-07-20 18:01:40 +0000
        Inactive image status: success
        Inactive node type: STORAGE
        Inactive system partition on device: /dev/md6
        Inactive software partition on device: /dev/md8
        
        Inactive marker for the rollback: /boot/I_am_hd_boot.inactive
        Inactive grub config for the rollback: /boot/grub2/grub.cfg.inactive
        Inactive usb grub config for the rollback: /boot/grub2/grub.cfg.usb.inactive
        Inactive kernel version for the rollback: 4.14.35-2047.510.5.5.el7uek.x86_64
        Rollback to the inactive partitions: Possible
        [root@slcs27celadm04 ~]#

        ibswitch version command output:
        -------------------------------
        [root@slcs27sw-iba0 ~]# version | head -1
        SUN DCS 36p version: 2.2.16-3

        roceswitch show version command output :
        ---------------------------------------
        scaqan17sw-rocea0# show version | grep 'NXOS: version' | awk '{print $3}'
        7.0(3)I7(9)
        
        Note: for ibswitch/roceswitch existing fetch version info APIs are being used
        -----
        """
        if aNode and aTargeType:

            # _image_info_keys_name_dict is a map of actual string present in imageinfo output and strings to be
            # displayed in node_progress_data
            if aTargeType in [PATCH_DOM0, PATCH_DOMU]:
                # Note: Exasplice is applicable only to dom0 here
                _image_info_keys_name_dict = {"Image version":"image_version", "Image status":"image_status",
                                              "Image activated":"image_activation_date","Exasplice update version":"exasplice_version",
                                              "Exasplice update activated":"exasplice_activation_date"
                                              }
            elif aTargeType in [PATCH_CELL]:
                _image_info_keys_name_dict = {"Active image version":"image_version", "Active image status":"image_status",
                                              "Active image activated":"image_activation_date"
                                              }
            try:
                if aTargeType in [PATCH_DOMU, PATCH_DOM0, PATCH_CELL]:
                    _cmd = "/usr/local/bin/imageinfo -all"
                    _node.mConnect(aHost=aNode)
                    _image_info_cmd_output = {}
                    _node.mMultipleLineOutputWithSeparator(_cmd, ":", _image_info_cmd_output,
                                                               aTimeout=SHELL_CMD_DEFAULT_TIMEOUT_IN_SECONDS)
                    if len(_image_info_cmd_output) > 1:
                        for _info_key in _image_info_keys_name_dict.keys():
                            if _info_key in _image_info_cmd_output:
                                _image_info_details[_image_info_keys_name_dict[_info_key]] = _image_info_cmd_output[_info_key]
                    else:
                        self.mPatchLogInfo(
                            f"mGetImageVersionInfoDetails - imageinfo output for the Node : {str(aNode)} is empty.")

                    if _node.mIsConnected():
                        _node.mDisconnect()

                    """
                    imageinfo command output for elu:
                    
                    [root@auto-hbzvr2 ~]# imageinfo

                    Kernel version: 5.4.17-2136.343.5.3.el8uek.x86_64 #3 SMP Mon Jun 30 00:11:58 PDT 2025 x86_64
                    Uptrack kernel version: 5.4.17-2136.345.5.3.el8uek.x86_64 #3 SMP Wed Jul 9 10:52:40 PDT 2025 x86_64
                    Image kernel version: 5.4.17-2136.343.5.3.el8uek
                    Image version: 24.1.14.0.0.250706
                    Image activated: 2025-10-16 08:18:28 +0000
                    Image status: success
                    Exadata software version: 24.1.14.0.0.250706
                    Exadata Live Update Type: high (CVSS 7-10)
                    Exadata Live Update Version: 24.1.15.0.0.250805 (Live Update applied. Reboot at any time to finalize outstanding items.)
                    Node type: GUEST
                    System partition on device: /dev/mapper/VGExaDb-LVDbSys1
                    
                    [root@auto-hbzvr2 ~]# 

                    """
                    # For elu add exadata_live_update_version, exadata_live_update_type and elu_applypending_updates
                    if self.ghandler.mIsElu():
                        _, _, _elu_info, _ = self.ghandler.mGetExadataLiveUpdateDetails(aNode)

                        if _elu_info:
                            if 'elu_version' in _elu_info:
                                if _elu_info['elu_version']:
                                    _image_info_details["exadata_live_update_version"] = _elu_info['elu_version']
                                else:
                                    self.mPatchLogInfo("Exadata Live Update Version is empty.")
                                    _image_info_details["exadata_live_update_version"] = ""
                            else:
                                self.mPatchLogInfo("Exadata Live Update Version is missing.")
                                _image_info_details["exadata_live_update_version"] = ""

                            if 'elu_type' in _elu_info:
                                if _elu_info['elu_type']:
                                    _image_info_details["exadata_live_update_type"] = _elu_info['elu_type']
                                else:
                                    self.mPatchLogInfo("Exadata Live Update Type is empty.")
                                    _image_info_details["exadata_live_update_type"] = ""
                            else:
                                self.mPatchLogInfo("Exadata Live Update Type is missing.")
                                _image_info_details["exadata_live_update_type"] = ""

                            if 'elu_has_outstanding_work' in _elu_info:
                                if _elu_info['elu_has_outstanding_work']:
                                    _image_info_details["exadata_live_update_has_outstanding_work"] = _elu_info[
                                        'elu_has_outstanding_work']
                                else:
                                    self.mPatchLogInfo("Exadata Live Update Has Outstanding Work is empty.")
                                    _image_info_details["exadata_live_update_has_outstanding_work"] = ""
                            else:
                                self.mPatchLogInfo("Exadata Live Update Has Outstanding Work is missing.")
                                _image_info_details["exadata_live_update_has_outstanding_work"] = ""
                        else:
                            self.mPatchLogInfo("Exadata Live Update information is empty or not available.")
                            _image_info_details.update({
                                "exadata_live_update_version": "",
                                "exadata_live_update_type": "",
                                "exadata_live_update_has_outstanding_work": ""
                            })
                elif aTargeType in [PATCH_ROCESWITCH, PATCH_IBSWITCH]:
                    if aTargeType == PATCH_IBSWITCH:
                        _context_switch_target_handler = mGetInfraPatchingHandler(INFRA_PATCHING_HANDLERS,PATCH_IBSWITCH)
                    elif aTargeType == PATCH_ROCESWITCH:
                        _context_switch_target_handler = mGetInfraPatchingHandler(INFRA_PATCHING_HANDLERS,PATCH_ROCESWITCH)
                    if _context_switch_target_handler:
                        _cur_version = _context_switch_target_handler.mGetRoceIbSwitchTargetVersionToUpdateImageDetails()
                        if _cur_version:
                            _image_info_details["image_version"] = _cur_version
                        else:
                            self.mPatchLogInfo(
                                f"mGetImageVersionInfoDetails - imageinfo output for the Node : {str(aNode)} is empty.")

            except Exception as e:
                self.mPatchLogWarn(
                    f"\nException {str(e)} in getting imageversion info details on the node '{aNode}'.\n")
                self.mPatchLogTrace(traceback.format_exc())
            finally:
                if _node.mIsConnected():
                    _node.mDisconnect()
                self.mPatchLogInfo(
                    f"mGetImageVersionInfoDetails - _image_info_details for the node : {aNode} is {str(_image_info_details['image_version'])} ")
        else:
            self.mPatchLogWarn("mGetImageVersionInfoDetails - node_name and target type values are not correct.")

        return _image_info_details

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
                self.mPatchLogWarn(f'partitiond enabled - expected: {aOrigState["partitiond"]} current: {_partitiond}')
                self.mPatchLogWarn(f'SM enabled state   - expected: {aOrigState["sm_enabled"]} current: {_sm_enabled}')
                self.mPatchLogWarn(f'SM state           - expected: {aOrigState["sm_state"]} current: {_sm_state}')
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

    def mCheckCellServices(self, aCell, aOrigState={}, aCheckRunning=False):
        """
        Checks the cell services status. if aCheckRunning is set to True,
        it checks if services are up. If aOrigState provided, then it compares the
        current services state with the ones from the input.
        If aOrigState is no specified, then it returns the current services status.
        """
        
        _all_services = {}
        _services = {}
        _cmd = 'cellcli -e "list cell detail" | grep Status'

        self.mPatchLogInfo(f"Check running service flag: '{aCheckRunning}'")
        _cell = exaBoxNode(get_gcontext())
        _cell.mConnect(aHost=aCell)
        _in, _out, _err = _cell.mExecuteCmd(_cmd)
        _exit_code = _cell.mGetCmdExitStatus()
        _output = _out.readlines()
        if not aCheckRunning:
            _cell.mDisconnect()
        # we should get three exadata services to be up and running.
        # Example:
        #  cellsrvStatus:          running
        #  msStatus:               running
        #  rsStatus:               running

        # In Exascale on CC/CS:
        #  cellsrvStatus:          running
        #  msStatus:               running
        #  rsStatus:               running
        #  egsStatus:              running
        #  ersStatus:              running
        #  sysEdsStatus:           running
        #  usrEdsStatus:           running
        #  bsmStatus:              running
        #  bswStatus:              running
        #  ifdStatus:              running

        if _output:
            for _line in _output:
                _tmp = _line.split()
                _all_services[_tmp[0][:-1]] = _tmp[1].strip()
                if _tmp[1].lower() == "running":
                    _services[_tmp[0][:-1]] = _tmp[1].strip()
                
        if aCheckRunning:
            _ret = True
            #Enh 37825517 printing all  cell services status before and after patching.
            self.mPatchLogInfo(f"Cell service status on cell '{aCell}' is: '{_all_services}'")
            if not _services or not ('cellsrvStatus' in _services and 'msStatus' in _services and 'rsStatus' in _services):
                self.mPatchLogWarn(f"Cell service status on cell '{aCell}' is: '{_services}'")
                _ret = False
            # if exascale is present, the following escli command will show service offline only if it is configured
            # check if wallet is present
            elif _cell.mFileExists(ESCLI_WALLET_LOCATION):
                # check if authentication is working
                '''
                [root@scaqau11celadm01 ~]# /opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet lsinitiator
                id                                   hostName       giClusterName   giClusterId
                43b44267-f7d4-b24f-43b4-4267f7d4b24f scaqau11dv0201 iad1464clu012f7 8290e1b9-4706-cf76-bf52-90252dcf6ac9
                ddde8902-9426-3179-ddde-890294263179 scaqau11dv0101 iad1464clu012f7 8290e1b9-4706-cf76-bf52-90252dcf6ac9
                08747e3e-38e8-716e-0874-7e3e38e8716e scaqau11adm02
                ae6c98cf-fa88-d556-ae6c-98cffa88d556 scaqau11dv0202 iad1464clu024z8 cfb82eca-7395-6f98-bf21-bbe9ee10314b
                b5d5a3c2-2af2-8701-b5d5-a3c22af28701 scaqau11dv0102 iad1464clu024z8 cfb82eca-7395-6f98-bf21-bbe9ee10314b
                '''
                _cmd = f"{ESCLI_CMD} --wallet {ESCLI_WALLET_LOCATION} lsinitiator"
                _in, _out, _err = _cell.mExecuteCmd(_cmd)
                _exit_code = _cell.mGetCmdExitStatus()
                if int(_exit_code) == 0:
                    # check for OFFLINE services
                    '''
                    [root@scaqau11celadm01 ~]# /opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet lsservice -l
                    cellName         hostName         rackId  serviceType         name                     status incarnation
                    scaqau11celadm02 scaqau11celadm02 0-0-0-0 rootServices        egs_scaqau11celadm02     ONLINE
                    scaqau11celadm01 scaqau11celadm01 0-0-0-0 rootServices        egs_scaqau11celadm01     ONLINE
                    scaqau11celadm03 scaqau11celadm03 0-0-0-0 rootServices        egs_scaqau11celadm03     ONLINE
                    scaqau11adm02    scaqau11adm02    0-0-0-0 rootServices        egs_scaqau11adm02        ONLINE
                    scaqau11adm01    scaqau11adm01    0-0-0-0 rootServices        egs_scaqau11adm01        ONLINE
                    scaqau11celadm02 scaqau11celadm02 0-0-0-0 userVaultManagers   usreds_scaqau11celadm02  ONLINE           1
                    scaqau11celadm03 scaqau11celadm03 0-0-0-0 userVaultManagers   usreds_scaqau11celadm03  ONLINE           1
                    scaqau11celadm01 scaqau11celadm01 0-0-0-0 userVaultManagers   usreds_scaqau11celadm01  ONLINE           1
                    scaqau11celadm02 scaqau11celadm02 0-0-0-0 systemVaultManagers syseds_scaqau11celadm02  ONLINE           1
                    scaqau11celadm03 scaqau11celadm03 0-0-0-0 systemVaultManagers syseds_scaqau11celadm03  ONLINE           1
                    scaqau11celadm01 scaqau11celadm01 0-0-0-0 systemVaultManagers syseds_scaqau11celadm01  ONLINE           1
                    scaqau11celadm01 scaqau11celadm01 0-0-0-0 cellServices        cellsrv_scaqau11celadm01 ONLINE           4
                    scaqau11celadm02 scaqau11celadm02 0-0-0-0 cellServices        cellsrv_scaqau11celadm02 ONLINE           6
                    scaqau11celadm03 scaqau11celadm03 0-0-0-0 cellServices        cellsrv_scaqau11celadm03 ONLINE           6
                    scaqau11celadm01 scaqau11celadm01 0-0-0-0 controlServices     ers_scaqau11celadm01     ONLINE           2
                    scaqau11celadm02 scaqau11celadm02 0-0-0-0 controlServices     ers_scaqau11celadm02     ONLINE           2
                    scaqau11celadm03 scaqau11celadm03 0-0-0-0 controlServices     ers_scaqau11celadm03     ONLINE           3
                    scaqau11celadm02 scaqau11celadm02 0-0-0-0 volumeManagers      bsm_scaqau11celadm02     ONLINE           1
                    scaqau11celadm03 scaqau11celadm03 0-0-0-0 volumeManagers      bsm_scaqau11celadm03     ONLINE           1
                    scaqau11celadm01 scaqau11celadm01 0-0-0-0 volumeManagers      bsm_scaqau11celadm01     ONLINE           1
                    scaqau11celadm02 scaqau11celadm02 0-0-0-0 volumeWorkers       bsw_scaqau11celadm02     ONLINE           1
                    scaqau11celadm03 scaqau11celadm03 0-0-0-0 volumeWorkers       bsw_scaqau11celadm03     ONLINE           1
                    scaqau11celadm01 scaqau11celadm01 0-0-0-0 volumeWorkers       bsw_scaqau11celadm01     ONLINE           1
                    '''
                    _cmd = f"{ESCLI_CMD} --wallet {ESCLI_WALLET_LOCATION} lsservice -l | grep -i OFFLINE"
                    _max_retries = int(mGetInfraPatchingConfigParam('max_retries_for_esservice_online'))
                    self.mPatchLogInfo("Waiting to see if all ES services are online")
                    for _ in range(_max_retries):
                        sleep(15)
                        _in, _out, _err = _cell.mExecuteCmd(_cmd)
                        _exit_code = _cell.mGetCmdExitStatus()
                        if _exit_code != 0:
                            break
                    # if some service is offline
                    if _exit_code == 0:
                        _cmd = f"{ESCLI_CMD} --wallet {ESCLI_WALLET_LOCATION} lsservice -l"
                        _in, _out, _err = _cell.mExecuteCmd(_cmd)
                        _output = _out.readlines()
                        for _out in _output:
                            _out = _out.rstrip()
                            self.mPatchLogInfo(f"{_out}")
                        _ret = False
            # Note: if basic services are up but wallet or escli cant be executed
            # (exascale not correctly configured) continue
            if _cell.mIsConnected():
                _cell.mDisconnect()
            return _ret

        if aOrigState:
            self.mPatchLogInfo(f"Cell service status on cell '{aCell}' post patching: '{_all_services}'")
            for _service in _services.keys():
                if _service and _service in aOrigState and aOrigState[_service] == _services[_service]:
                    continue
                elif _service and _service in aOrigState: 
                    self.mPatchLogWarn(
                        f"Cell service Original state = '{aOrigState[_service]}', NewState ='{_services[_service]}' on cell '{aCell}'")
                    return False
                elif _service and _service not in aOrigState:
                    self.mPatchLogWarn(f"Cell service '{_service}' was not in running state before patching on cell '{aCell}'. NewState ='{_services[_service]}'")             
            return True

        return _services

    def mCheckDBServices(self, aDBNode, aOrigState={}, aCheckRunning=False):
        """
        Checks the dbserverd services status. if aCheckRunning is set to True,
        it checks if services are up. If aOrigState provided, then it compares the
        current services state with the ones from the input.
        If aOrigState is no specified, then it returns the current services status.
        """

        _services = {}

        self.mPatchLogInfo(f'DBMCLI services check performed on Node : {aDBNode}.')

        # Expecting two entries for RS and MS:
        # Example Output:
        # dbmcli -e "list dbserver detail" | egrep "msStatus|rsStatus"
        #   msStatus:    running
        #   rsStatus:    running

        _cmd = 'dbmcli -e "list dbserver detail" | egrep "msStatus|rsStatus"'

        # Count the lines of "running"
        # Expected output is 2
        if aCheckRunning:
            _cmd += ' | grep -asic running'

        _dbnode = exaBoxNode(get_gcontext())
        _dbnode.mConnect(aHost=aDBNode)
        _in, _out, _err = _dbnode.mExecuteCmd(_cmd)
        _exit_code = _dbnode.mGetCmdExitStatus()
        _output = _out.readlines()
        _dbnode.mDisconnect()

        if aCheckRunning:
            if int(_output[0].strip()) != 2:
                return False
            return True

        if _output:
            for _line in _output:
                _tmp = _line.split()
                _services[_tmp[0][:-1]] = _tmp[1].strip()

        if aOrigState:
            for _service in _services.keys():
                if _service and aOrigState[_service] == _services[_service]:
                    continue
                return False
            return True

        return _services

    def mCheckVMsUp(self, aDom0, aOrigVMsList=None):
        """
        Gets a list of active vms (xm list). If aOrigVMsList provided,
        if the dom0 has all the vms from the list up, True is returned.
        If the dom0 does not have all of the vms up, False is returned
        """

        _domUs = []
        # _cmd = "xm list | tail -n+3 | awk '{print $1}'"
        _cmd = ""

        if self.cluctrl.mIsKVM(aHostname=aDom0):
            self.mPatchLogInfo("KVM environment has been detected.")
            _cmd = "virsh list| grep -i 'running' |awk '{print $2}' | sed '/^$/d'"
        else:
            self.mPatchLogInfo("OVM environment has been detected.")
            _cmd = "xm list|tail -n+3|awk '{print $1}'"

        _dom0 = exaBoxNode(get_gcontext())
        _dom0.mConnect(aHost=aDom0)
        _in, _out, _err = _dom0.mExecuteCmd(_cmd)
        _output = _out.readlines()
        _dom0.mDisconnect()

        if _output:
            for _line in _output:
                _domUs.append(_line.strip())

        if aOrigVMsList is not None:
            for _vm in aOrigVMsList:
                if _vm not in _domUs:
                    return False
            return True

        return _domUs

    def mVerifyCellsInUseByASM(self, aCellList):
        """
        Returns the list of cells that are actually in use by ASM as well as listof cells that have griddisk status as UNKNWON
        """

        _cmd_cell = "cellcli -e 'list griddisk attributes name, asmmodestatus'| grep -asq 'ONLINE\|SYNC'"
        _cmd_cell_restart = 'cellcli -e "alter cell restart services all"'
        _cmd_cells_with_grid_disk_unknown = "cellcli -e 'list griddisk attributes name, asmmodestatus'| grep -asq 'UNKNOWN'"
        _cells_with_grid_disk_unknown = []
        _cells_in_use = []
        _attempts = 0
        # only wait for ASM disks to be online if non-rolling style
        if self.ghandler.mGetOpStyle() == OP_STYLE_NON_ROLLING:
            _max_attempts = int(mGetInfraPatchingConfigParam('max_retries_for_griddisk_online'))
        else:
            _max_attempts = 1

        # During non-rolilng, all cells and computes go down. It may take a while for ASM to mount the grid disks 
        # If at least one cell shows online/sync exit, otherwise tries up to _max_attempts for non-rolling case
        while len(_cells_in_use) == 0 and _attempts < _max_attempts:
            _attempts = _attempts + 1
            for _cell in aCellList:
                # Check cell services are up
                _up_services = self.mCheckCellServices(_cell, aCheckRunning=True)
                if not _up_services:
                    self.mPatchLogInfo(
                        f"Services are not up for cell {_cell} in mVerifyCellsInUseByASM. Cell services will be restarted")
                    # Restart services to see if they go up
                    self.mPatchLogInfo("Cell services will be restarted")
                    _node = exaBoxNode(get_gcontext())
                    _node.mConnect(aHost=_cell)
                    _node.mExecuteCmdLog(_cmd_cell_restart)
                    sleep(10)
                    _node.mDisconnect()
                    # Get celld status again
                    _up_services = self.mCheckCellServices(_cell, aCheckRunning=True)

                if _up_services:
                    _node = exaBoxNode(get_gcontext())
                    _node.mConnect(aHost=_cell)
                    _in, _out, _err = _node.mExecuteCmd(_cmd_cell)
                    _rc = _node.mGetCmdExitStatus()

                    if int(_rc) == 0:
                        _cells_in_use.append(_cell)
                    else:
                        self.mPatchLogInfo(
                            f"Cell {_cell} will not be added to list since return value from cellcli command in mVerifyCellsInUseByASM is not zero ")

                    _in, _out, _err = _node.mExecuteCmd(_cmd_cells_with_grid_disk_unknown)
                    _rc = _node.mGetCmdExitStatus()
                    _node.mDisconnect()

                    if int(_rc) == 0:
                        _cells_with_grid_disk_unknown.append(_cell)
                else:
                    self.mPatchLogError(f"Cell services not up in cell {_cell}. It will be ignored")

            if len(_cells_in_use) == 0 and _attempts < _max_attempts:
                sleep(10)

        return _cells_in_use, _cells_with_grid_disk_unknown

    '''
    def mControlCellServices(self, aCellList, aAction='start'):
        """
        Controls cell services by starting/stopping the services. It checks that celld status
        shows as expected.
        """

        _cmd = None
        _success = True

        if aAction == 'start':
            _cmd = 'service celld start'
        elif aAction == 'stop':
            _cmd = 'service celld stop'
        elif aAction == 'restart':
            _cmd = 'cellcli -e "alter cell restart services all"'
        else:
            self.mPatchLogError(f"Action '{aAction}' not valid in mControlCellServices")
            return False

        def _runCellServicesCmd(aCell):
            _ret = True

            _cell = exaBoxNode(get_gcontext())
            _cell.mConnect(aHost=aCell)
            _in, _out, _err = _cell.mExecuteCmd(_cmd)

            _errors = _err.readlines()
            if _errors:
                self.mPatchLogWarn("".join(_errors))

            _cell.mDisconnect()
            _services = self.mCheckCellServices(aCell)

            for _s in _services.keys():
                if aAction == 'start' or aAction == 'restart':
                    if _services[_s] != 'running':
                        self.mPatchLogError(f"Cell '{aCell}' service {_s} not running. Status = {_services[_s]}")
                        _ret = False
                else:
                    if _services[_s] == 'running':
                        self.mPatchLogError(f"Cell '{aCell}' service {_s} is running.")
                        _ret = False
            return _ret

        for _cell in aCellList:
            self.mPatchLogInfo(f"Run cell services action '{aAction}' in cell '{_cell}'")
            _success &= _runCellServicesCmd(_cell)

        return _success
    '''

    def mManageVMs(self, aDom0, aDomUList, aAction, aRcStatus):
        """
        Creates/shutdown VMs in aDom0

        Note: Use mShutDownVMs, if xm destroy/virsh destroy need to be done when graceful shutdown of the VM does not happen.
             This method for shutdown action, waits for graceful shutdown of the VM and fails if it does not happen.
        """
        # Mark success, initially.
        _success = True

        _ret = -1

        if aAction not in ['start', 'shutdown']:
            self.mPatchLogError(f"Action '{aAction}' not valid in mManageVMs")
            return 0

        _dom0 = exaBoxNode(get_gcontext())
        _dom0.mConnect(aHost=aDom0)

        _vmhandle = getHVInstance(aDom0)

        for _domU in aDomUList:
            self.mPatchLogInfo(f"Action '{aAction}' vm '{_domU}' on dom0 '{aDom0}'")

            if aAction == 'start':
                _ret = _vmhandle.mStartVM(_domU)
            elif aAction == 'shutdown':
                _ret = _vmhandle.mShutdownVM(_domU)

            if _ret != 0:
                # It is possible vms where already up/down. In those case, we should not return error
                _success = False
                self.mPatchLogError(f'*** mManageVMs: {aAction.capitalize()} operation failed on {_domU}') 
                aRcStatus.append({'domu': _domU, 'status': 'failed'})
                continue

            if aAction == 'shutdown':
                # Wait for VM startup/shutdown operation to complete.
                _starttime = time()
                _elapsed = 0
                _iterations = 0
                _timeout = 1800  # Max time is 30 minutes
                while _elapsed < _timeout:
                    sleep(SHUTDOWN_STARTUP_SLEEP_INTERVAL_IN_SECONDS)

                    if not _domU in _vmhandle.mRefreshDomUs():
                        self.mPatchLogInfo(
                            f'*** mManageVMs: Completed Shutdown of VM: {_domU}, elapsed time: {_elapsed}')
                        break
                    else:
                        if _iterations % 10 == 0:
                            self.mPatchLogInfo(
                                f'*** mManageVMs: Waiting for complete of Shutdown of VM: {_domU}, time: {_elapsed}')
                    _elapsed = time() - _starttime

                    _iterations += 1
                else:
                    _success = False
                    self.mPatchLogError(f'*** mManageVMs: Shutdown not completed in-time on {_domU}')
                    aRcStatus.append({'domu': _domU, 'status': 'failed'})
                    continue
            elif aAction == 'start':
                self.mPatchLogInfo(f"Waiting for vm '{_domU}' to come up (until cpu_time = 40)")
                if self.cluctrl.mIsKVM(aHostname=aDom0):
                    isKVM = True
                    self.mPatchLogInfo(
                        f"Firing command to check for vm  '{_domU}' in KVM host {aDom0} to come up (until cpu_time = 40)")
                    # virsh cpu-stats <domu> --total | grep -ia cpu_time | awk  '{print $2}'
                    # 190370.589664906
                    _cpu_cmd_to_execute = f"virsh cpu-stats  {_domU} --total | grep -ia cpu_time | awk  '{{print $2}}'"
                else:
                    isKVM = False
                    self.mPatchLogInfo(
                        f"Firing command to check for vm  '{_domU}' in OVM host {aDom0} to come up (until cpu_time = 40)")
                    # xm list <domU> -l | grep -ia cpu_time
                    # (cpu_time 224204.654947)
                    _cpu_cmd_to_execute = f"xm list {_domU} -l|grep -ia cpu_time"
                while True:
                    # _i, _o, _e = _dom0.mExecuteCmd(f"xm list {_domU} -l|grep -ia cpu_time")
                    _i, _o, _e = _dom0.mExecuteCmd(_cpu_cmd_to_execute)
                    _out = _o.readlines()
                    if _out:
                        _cpu_time = re.search("([0-9]+\.[0-9]+)", _out[0])
                        if _cpu_time:
                            if float(_cpu_time.groups()[0]) >= 40.0:
                                break
                        else:
                            self.mPatchLogError(f"Not able to parse cpu_time data in vm '{_domU}'")
                            break
                    else:
                        self.mPatchLogError(f"No vm '{_domU}' information available")
                        break

                    sleep(30)

        _dom0.mDisconnect()

        return _success

    def mShutDownVMs(self, aDom0, aDomUList, aRcStatus):
        """
        This method shutdown VMs in aDom0
        This is used to shutdown the VMs using mShutdownVM method of exaBoxOVMCtrl.

        As part of this, if the VM does not get gracefully shutdown with in 15 mins, it is going to do mDestroyVM
        ( which internally does xm destroy or virsh destroy )
        
        Reference bug: BUG 35662405 
        """
        # Mark success, initially.
        _shutdown_successful = True

        _ret = -1
        _dom0 = exaBoxNode(get_gcontext())
        _dom0.mConnect(aHost=aDom0)

        _vm_ctl_handle = exaBoxOVMCtrl(aCtx=get_gcontext(), aNode=_dom0)

        for _domU in aDomUList:
            self.mPatchLogInfo(f"Shutdown vm '{_domU}' on dom0 '{aDom0}'")

            _ret = _vm_ctl_handle.mShutdownVM(_domU)

            if _ret != 0:
                # If shutdown return non-zero
                _shutdown_successful = False
                self.mPatchLogError(f'*** mShutDownVMs: Shutdown operation failed on {_domU}')
                aRcStatus.append({'domu': _domU, 'status': 'failed'})
                continue

            _vm_ctl_handle.mRefreshDomUs()
            if not _domU in _vm_ctl_handle.mGetDomUs():
                self.mPatchLogInfo(f'*** mShutDownVMs: Completed Shutdown of VM: {_domU}')
            else:
                _shutdown_successful = False
                self.mPatchLogError(f'*** mShutDownVMs: Shutdown not completed in-time on {_domU}')
                aRcStatus.append({'domu': _domU, 'status': 'failed'})

        _dom0.mDisconnect()

        return _shutdown_successful

    def mStartVMs(self, aDom0, aDomUList, aRcStatus):
        """
        Starts a list of VMs on a specified dom0.

        Args:
            aDom0 (str): dom0 name.
            aDomUList (list): list of VMs to start.
            aRcStatus (list): list to store failure the status for which VM start failed.

        Returns:
            bool: True if all VMs are started successfully, False otherwise.

        Note:
            This method used to star the VMs and monitor the running status through polling. It relies on virsh list or
            xm list to verify the running status of the VMs, without checking the exit staus of the vm start command

        """
        # Mark success, initially.
        _start_successful = True

        _dom0 = exaBoxNode(get_gcontext())
        _dom0.mConnect(aHost=aDom0)
        _vmhandle = getHVInstance(aDom0)

        for _domU in aDomUList:
            self.mPatchLogInfo(f"mStartVMs: Starting  vm '{_domU}' on dom0 '{aDom0}'")
            _ret = _vmhandle.mStartVM(_domU)

            # Wait for VM startup operation to complete.
            _starttime = time()
            _elapsed = 0
            _iterations = 0
            _timeout = self.ghandler.mGetVMStartUpMaxTimeoutInSeconds()  # Max time is 30 minutes

            while _elapsed < _timeout:
                sleep(SHUTDOWN_STARTUP_SLEEP_INTERVAL_IN_SECONDS)
                _elapsed = time() - _starttime
                if _domU in _vmhandle.mRefreshDomUs():
                    self.mPatchLogInfo(
                        f'*** mStartVMs: VM {_domU} started successfully, elapsed time: {_elapsed} ')
                    break
                else:
                    if _iterations % 10 == 0:
                        self.mPatchLogInfo(
                            f'*** mStartVMs: Waiting for VM {_domU} to start, elapsed time: {_elapsed}')
                _iterations += 1
            else:
                _start_successful = False
                self.mPatchLogError(f'*** mStartVMs: Failed to start VM {_domU} within {_timeout} seconds')
                aRcStatus.append({'domu': _domU, 'status': 'failed'})
                continue

        _dom0.mDisconnect()

        return _start_successful

    def mVerifyGriddiskDeactivationOutcome(self, aCellList, aTaskType):
        """
        Returns True if asmdeactivationoutcome is set to 'Yes', otherwise, return False
        """

        _ret = True
        _cmd_cell = None

        if aTaskType in [OP_STYLE_NON_ROLLING]:
            _cmd_cell = "cellcli -e list griddisk attributes name,asmmodestatus,asmdeactivationoutcome where asmmodestatus='ONLINE'"
        elif aTaskType in [OP_STYLE_ROLLING, OP_STYLE_AUTO]:
            _cmd_cell = "cellcli -e list griddisk attributes name,asmmodestatus,asmdeactivationoutcome where asmmodestatus='ONLINE' and asmdeactivationoutcome !='Yes'"

        self.mPatchLogInfo(f'mVerifyGriddiskDeactivationOutcome: _cmd_cell = {_cmd_cell}')

        for _cell in aCellList:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_cell)
            _in, _out, _err = _node.mExecuteCmd(_cmd_cell)
            _output = _out.readlines()
            if _output:
                self.mPatchLogInfo(f'Following griddisks are not in appropriate status on cell: ({_cell})')
                for _line in _output:
                    _disk_split = _line.split(None, 2)
                    if _disk_split:
                        if aTaskType in [OP_STYLE_NON_ROLLING, OP_STYLE_AUTO]:
                            self.mPatchLogInfo(f'*** Disk name : {_disk_split[0]} , Reason : {_disk_split[1]}')
                        elif aTaskType in [OP_STYLE_ROLLING, OP_STYLE_AUTO]:
                            self.mPatchLogInfo(f'*** Disk name : {_disk_split[0]} , Reason : {_disk_split[2]}')
                        _ret = False
            _node.mDisconnect()

        return _ret

    """
    def mCheckGriddiskAsmModeStatus(self, aCellList):
        '''
        Returns 
             - CELL_ASM_MODE_STATUS_SYNCING_ERROR, if asmmodestatus is 'SYNCING' status.
             - CELL_ASM_MODE_STATUS_UNUSED_ERROR, if asmmodestatus is 'UNUSED' status.
             - CELL_ASM_MODE_STATUS_OFFLINE_ERROR, if asmmodestatus is 'OFFLINE' status.
             - PATCH_SUCCESS_EXIT_CODE, otherwise.
        '''

        def _mexecute_cell_cmd(_cell_cmd):

            _ret = True
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_remote_node)

            try:
                _in, _out, _err = _node.mExecuteCmd(_cell_cmd)
                _output = _out.readlines()
                if _output:
                    for _line in _output:
                        _disk_split = _line.split(None, 2)
                        if _disk_split:
                            self.mPatchLogError(f'*** Disk name : {_disk_split[0]} , Reason : {_disk_split[1]}')
                            _ret = False

            except Exception as e:
                self.mPatchLogWarn(f'Grid Disk checks failed with errors on Node : {_remote_node} Error : {str(e)}.')
                _ret = False

            finally:
                _node.mDisconnect()
                return _ret

        # End of _mexecute_cell_cmd sub method

        def _check_asmmodestatus_cell(_remote_node, aStatus):

            _cmd_cell_syncing = "cellcli -e list griddisk attributes name, asmmodestatus where asmmodestatus='SYNCING'"
            self.mPatchLogInfo(f"Performing ASM syncing status check on grid disks of cell : {_remote_node}")
            if not _mexecute_cell_cmd(_cmd_cell_syncing):
                aStatus.append({'cell': _remote_node, 'status': 'failed', 'errorcode':CELL_ASM_MODE_STATUS_SYNCING_ERROR})
                _suggestion_msg = f"Griddisks are in Syncing state on Cell : ({_remote_node})."
                self.ghandler.mAddError(CELL_ASM_MODE_STATUS_SYNCING_ERROR, _suggestion_msg)

            _cmd_cell_unused = "cellcli -e list griddisk attributes name, asmmodestatus where asmmodestatus='UNUSED'"
            self.mPatchLogInfo(f"Performing ASM Unused status check on grid disks of cell : {_remote_node}") 
            if not _mexecute_cell_cmd(_cmd_cell_unused):
                aStatus.append({'cell': _remote_node, 'status': 'failed', 'errorcode':CELL_ASM_MODE_STATUS_UNUSED_ERROR})
                _suggestion_msg = f"Griddisks are in Unused state on Cell : ({_remote_node})."
                self.ghandler.mAddError(CELL_ASM_MODE_STATUS_UNUSED_ERROR, _suggestion_msg)

            _cmd_cell_offline = "cellcli -e list griddisk attributes name, asmmodestatus where asmmodestatus='OFFLINE'"
            self.mPatchLogInfo(f"Performing ASM Offline status check on grid disks of cell : {_remote_node}")
            if not _mexecute_cell_cmd(_cmd_cell_offline):
                aStatus.append({'cell': _remote_node, 'status': 'failed', 'errorcode':CELL_ASM_MODE_STATUS_OFFLINE_ERROR})
                _suggestion_msg = f"Griddisks are in Offline state on Cell : ({_remote_node})."
                self.ghandler.mAddError(CELL_ASM_MODE_STATUS_OFFLINE_ERROR, _suggestion_msg)

        # End of _check_asmmodestatus_cell sub method

        '''
         Parallelize execution on all target nodes. In case
         of Cell patching, griddisk validations
         (UNUSED/SYNCING/OFFLINE status) are performed 
         parallelly on all cells.
        '''
        _plist = ProcessManager()
        _rc_status = _plist.mGetManager().list()

        for _remote_node in aCellList:
            _p = ProcessStructure(_check_asmmodestatus_cell, [_remote_node, _rc_status], _remote_node)

            '''
             Timeout parameter configurable in Infrapatching.conf
             Currently it is set to 60 minutes
            '''
            _p.mSetMaxExecutionTime(self.ghandler.mGetValidateAsmGridDiskStatusExecutionTimeoutInSeconds())

            '''
             BUG 32888598 - Increase timeout from 5 seconds to 15 seconds.
        
             In case of EXACC environments, delay in command response are
             observed in a few use cases and as a results, patch commands
             fail. Increasing the below timeout parameter avoids patch
             commands from failing and wait for the command to respond.
            '''

            _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
            _p.mSetLogTimeoutFx(self.mPatchLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()

        if _plist.mGetStatus() == "killed":
            _suggestion_msg = f'Timeout occurred and threads are terminated while validating Grid disk status on the list of Nodes : {str(aCellList)}.'
            self.ghandler.mAddError(CELL_ASM_MODE_STATUS_SYNCING_ERROR, _suggestion_msg)
            raise Exception(_suggestion_msg) 

        # validate the return codes
        for _rc_details in _rc_status:
            if _rc_details['status'] == "failed":
                self.mPatchLogError("Verify Griddisk status on all cells before retrying patch.")
                return _rc_details['errorcode']

        return PATCH_SUCCESS_EXIT_CODE
    """

    def mVerifyExacloudExadataHostSshConnectivity(self, aNodeList, aSshUser='root'):
        """
         This method validates the connection between Exacloud and
         target Exadata nodes.Exception is raised if error is
         encountered, else validations are performed and is just a
         pass through method.
        """

        def _node_connectivity_check(aNode, aStatus, aSshUser=aSshUser):

            self.mPatchLogInfo(
                f"Validating to check if {aNode} is accessible from Exacloud host via ssh.")
            _node = exaBoxNode(get_gcontext())
            try:
                if aSshUser and aSshUser != "root":
                    _node.mSetUser(aSshUser)
                    _node.mSetMaxRetries(self.ghandler.mGetMaxNumberofSshRetries())

                '''
                 SSH Validations are performed between
                 Exacloud and launch nodes.
                '''
                _host = socket.getfqdn()
                if not _node.mIsConnectable(aHost=aNode, aTimeout=mGetSshTimeout(), aKeyOnly=True):
                    _suggestion_msg = f"{aNode} is not accessible from Exacloud Node : {_host}. Validate for keys and host access control settings before retrying patch operation."
                    aStatus.append({'node': aNode, 'status': 'failed', 'errorcode': PATCHING_NODE_SSH_CHECK_FAILED})
                    self.ghandler.mAddError(PATCHING_NODE_SSH_CHECK_FAILED, _suggestion_msg)
                else:
                    self.mPatchLogInfo(
                        f"{aNode} is accessible from Exacloud Node {_host} during infra patching operation.")

            except Exception as e:
                 raise Exception(
                     f"Error while performing ssh connectivity validation between exacloud and target Exadata hosts : {str(aNodeList)}. Error : {str(e)}")
        # End of _node_connectivity_check method

        """
         Parallelly validate for ssh connectivity on all
         target types and Exacloud host.
        """
        _plist = ProcessManager()
        _rc_status = _plist.mGetManager().list()

        for _remote_node in aNodeList:
            _p = ProcessStructure(_node_connectivity_check, [_remote_node, _rc_status, aSshUser], _remote_node)

            '''
             Timeout parameter configurable in Infrapatching.conf
             Currently it is set to 10 minutes
            '''
            _p.mSetMaxExecutionTime(self.ghandler.mGetValidateSshConnectivityExecutionTimeoutInSeconds())

            _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
            _p.mSetLogTimeoutFx(self.mPatchLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()

        if _plist.mGetStatus() == "killed":
            _suggestion_msg = f'Timeout occurred and threads are terminated while validating ssh connection prior to patching on the list of Nodes : {str(aNodeList)}.'
            self.ghandler.mAddError(PATCHING_NODE_SSH_CHECK_FAILED, _suggestion_msg)
            raise Exception(_suggestion_msg)

        # validate the return codes
        _list_of_hosts_where_ssh_failed = []
        for _rc_details in _rc_status:
            if _rc_details['status'] == "failed":
                _list_of_hosts_where_ssh_failed.append(_rc_details['node'])

        if len(_list_of_hosts_where_ssh_failed) > 0:
            raise Exception(
                f"SSH connectivity check between exacloud host and target nodes failed, validate keys and host access control before retrying patch. List of hosts with ssh connectivity issues : {str(_list_of_hosts_where_ssh_failed)}")

    def mVerifyPatchmgrSshConnectivityBetweenExadataHosts(self, aNodeList, aSourceNode, aStage="PrePatch", aSshUser='root', aAdminSwitch=False):
        """
         This method validates the connection between Source and
         target Exadata nodes. Exception is raised if error is
         encountered, else validations are performed and is just
         a pass through method.
        """

        def _node_connectivity_check(aNode, aStatus):
            self.mPatchLogInfo(
                f"Validating to check if {self.ghandler.mGetCurrentTargetType()} : {aNode} is accessible from launch node : {aSourceNode} via ssh.")
            _rc = 0
            _node = exaBoxNode(get_gcontext())
            try:
                if aSourceNode != 'localhost':
                    if aSshUser and aSshUser != "root":
                        _node.mSetUser(aSshUser)
                        _node.mSetMaxRetries(self.ghandler.mGetMaxNumberofSshRetries())
                    _node.mConnect(aHost=aSourceNode)
                '''
                 SSH Validations are perfomed between Launch
                 and target nodes.

                 In case of Roceswitches, default root
                 access user is ciscoexa from Dom0.

                 [root@scaqan02adm01 ~]# ssh ciscoexa@scaqan02sw-rocea0
                 User Access Verification

                 Cisco Nexus Operating System (NX-OS) Software
                 TAC support: http://www.cisco.com/tac
                 Copyright (C) 2002-2020, Cisco and/or its affiliates.
                 All rights reserved.

                '''
                _cmd_ssh_validate_list = []
                _cmd_verify_infrapatchkey = ""

                if self.ghandler.mGetCurrentTargetType() == PATCH_ROCESWITCH or aAdminSwitch:
                    _cmd_ssh_validate = f"ssh {ROCESWITCH_USER}@{aNode} 'show version'"
                else:
                    if aSourceNode == 'localhost':
                        _cmd_ssh_validate_list.append(['sudo', 'ssh', aNode, "'uptime'"])
                    else:
                        _cmd_ssh_validate = f"ssh {aNode} 'uptime'"
                        _cmd_verify_infrapatchkey = f"ssh {aNode} 'grep \"{EXAPATCHING_KEY_TAG}\" /root/.ssh/authorized_keys'"

                if aStage == "PrePatch":
                    _e = None
                    if aSourceNode == 'localhost':
                        _rc, _ = runInfraPatchCommandsLocally(_cmd_ssh_validate_list)
                    else:
                        _i, _o, _e = _node.mExecuteCmd(_cmd_ssh_validate)
                        _rc = int(_node.mGetCmdExitStatus())
                    if _rc != 0:
                        #If the error code is 255 then ssh connectivity failed with common issue of host validation error
                        if _e:
                            _err = _e.readlines()
                        else:
                            _err = ''
                        _error = str(_err)
                        _hostValidationError = 'Host key verification failed'
                        _ConnectionClosedError = 'Connection closed by'
                        _clussh = ebCluSshSetup(self.ghandler.mGetCluControl())
                        if _hostValidationError in _error:
                            _suggestion_msg = f"Stage : Precheck, Node : {aNode} is not accessible from {aSourceNode}. Error: {_error}"
                            aStatus.append({'node': aNode, 'status': 'failed', 'errorcode': LAUNCH_NODE_SSH_CHECK_FAILED_KNOWNHOSTS})
                            self.ghandler.mAddError(LAUNCH_NODE_SSH_CHECK_FAILED_KNOWNHOSTS, _suggestion_msg)
                        elif _ConnectionClosedError in _error and (self.ghandler.mGetCurrentTargetType() == PATCH_DOM0 or  self.ghandler.mGetCurrentTargetType() == PATCH_CELL) and not self.cluctrl.mCheckConfigOption('secure_ssh_all', 'False'):
                            _suggestion_msg = f"Stage : Precheck, Node : {aNode} is not accessible from {aSourceNode}. Validate exadata-secure.conf/pam settings on exadata nodes. Error: {_error}"
                            aStatus.append({'node': aNode, 'status': 'failed', 'errorcode': PATCHING_NODE_SSH_CHECK_FAILED})
                            self.ghandler.mAddError(PATCHING_NODE_SSH_CHECK_FAILED, _suggestion_msg)                            
                        else:
                            _suggestion_msg = f"Stage : Precheck, Node : {aNode} is not accessible from {aSourceNode}. Validate for keys and host access control settings before retrying patch operation. Error: {_error}"
                            aStatus.append({'node': aNode, 'status': 'failed', 'errorcode': PATCHING_NODE_SSH_CHECK_FAILED})
                            self.ghandler.mAddError(PATCHING_NODE_SSH_CHECK_FAILED, _suggestion_msg)
                    else:
                        self.mPatchLogInfo(
                            f"{self.ghandler.mGetCurrentTargetType()} : {aNode} is accessible from {aSourceNode} during Pre-Patch operation.")
                elif aStage == "PostPatch":
                    '''
                     In case of EXACC environments, skip postcheck
                     ssh validations on all patch components.
                    '''
                    _oci_exacc = self.ghandler.mGetCluControl().mCheckConfigOption('ociexacc', 'True')
                    if _oci_exacc:
                        self.mPatchLogInfo("Skipping Ssh cleanup validations on EXACC environments during postcheck stage on all patch components.")
                    elif (aSourceNode in self.ghandler.mGetDomUList()) and (self.ghandler.mGetCurrentTargetType() == PATCH_DOMU):                   
                        _i, _o, _e = _node.mExecuteCmd(_cmd_ssh_validate)
                        _rc = int(_node.mGetCmdExitStatus())
                        if _rc == 0:
                            #Checking if Domu Infrapatch SSH equivalence key EXAPATCHING_KEY_TAG exists                      
                            _keycomment_exists=1
                            _i, _o, _e = _node.mExecuteCmd(_cmd_verify_infrapatchkey)
                            _keycomment_exists = int(_node.mGetCmdExitStatus())
                            #This means EXAPATCHING_KEY_TAG key cleanup failed and hence throw error                                           
                            if _keycomment_exists == 0:
                                _suggestion_msg = f"Stage : Postcheck, {self.ghandler.mGetCurrentTargetType()} : {aNode} is accessible from {aSourceNode}. Passwdless ssh key {EXAPATCHING_KEY_TAG} cleanup failed. Passwdless ssh need to cleaned up for security compliance."
                                aStatus.append({'node': aNode, 'status': 'failed', 'errorcode': PASSWDLESS_SSH_CLEANUP_FAILED})
                                self.ghandler.mAddError(PASSWDLESS_SSH_CLEANUP_FAILED, _suggestion_msg)
                            #EXAPATCHING_KEY_TAG key is not present
                            else: 
                                self.mPatchLogInfo(f"SSH equivalence exists  between Source Node: {aSourceNode} and Target Node: {aNode}  domu's through other means other than patchmgr shh equivalence even after cleanup of {EXAPATCHING_KEY_TAG} in  postcheck stage.")                             
                                
                    else:
                        if aSourceNode == 'localhost':
                            _rc, _ = runInfraPatchCommandsLocally(_cmd_ssh_validate_list)
                        else:
                            _i, _o, _e = _node.mExecuteCmd(_cmd_ssh_validate)
                            _rc = int(_node.mGetCmdExitStatus())
                        if _rc == 0:
                            _suggestion_msg = f"Stage : Postcheck, {self.ghandler.mGetCurrentTargetType()} : {aNode} is accessible from {aSourceNode}. Passwdless ssh cleanup failed. Passwdless ssh need to cleaned up for security compliance."
                            aStatus.append({'node': aNode, 'status': 'failed', 'errorcode': PASSWDLESS_SSH_CLEANUP_FAILED})
                            self.ghandler.mAddError(PASSWDLESS_SSH_CLEANUP_FAILED, _suggestion_msg)

            except Exception as e:
                 raise Exception(f"Error while performing ssh connectivity validation between Exadata source : {aSourceNode} and target nodes : {str(aNodeList)}. Error : {str(e)}")
            finally:
                if aSourceNode != "localhost" and  _node.mIsConnected():
                    _node.mDisconnect()
        # End of _node_connectivity_check method

        """
         Parallelly validate for ssh connectivity on all
         target types and nodes.
        """
        _plist = ProcessManager()
        _rc_status = _plist.mGetManager().list()

        for _remote_node in aNodeList:
            _p = ProcessStructure(_node_connectivity_check, [_remote_node, _rc_status], _remote_node)

            '''
             Timeout parameter configurable in Infrapatching.conf
             Currently it is set to 10 minutes
            '''
            _p.mSetMaxExecutionTime(self.ghandler.mGetValidateSshConnectivityExecutionTimeoutInSeconds())

            _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
            _p.mSetLogTimeoutFx(self.mPatchLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()

        if _plist.mGetStatus() == "killed":
            _suggestion_msg = f'Timeout occurred and threads are terminated while validating ssh connection prior to patching on the list of Nodes : {str(aNodeList)}.'
            self.ghandler.mAddError(PATCHING_NODE_SSH_CHECK_FAILED, _suggestion_msg)
            raise Exception(_suggestion_msg)

        # validate the return codes
        _list_of_hosts_where_ssh_failed = []
        for _rc_details in _rc_status:
            if _rc_details['status'] == "failed":
                _list_of_hosts_where_ssh_failed.append(_rc_details['node'])

        if len(_list_of_hosts_where_ssh_failed) > 0:
            if aStage == "PrePatch":
                raise Exception(
                    f"SSH connectivity check between launch and target nodes failed, validate keys and host access control before retrying patch. List of hosts with ssh connectivity issues : {str(_list_of_hosts_where_ssh_failed)}")
            elif aStage == "PostPatch":
                raise Exception(
                    f"SSH keys cleanup failed post patch operation. Ensure keys are cleaned up for security compliance. List of hosts with ssh connectivity issues : {str(_list_of_hosts_where_ssh_failed)}")

    def mValidateAndEnableDomuAutoStartup(self, aDom0, aDomUList):
        """
         This method validates for DomU auto startup details.
         Prior to patch or rollback, list of DomU up and running
         on the dom0 are preserved. Post patch operations, validations
         are performed to check for presence of Auto startup files for
         the previously preserved domU list.

         Return DOMU_AUTO_STARTUP_FILE_MISSING_ERROR 
                - In case Auto startup soft link file is missing 
                  for the preserved DomU list.

         Return DOMU_AUTO_STARTUP_ONREBOOT_PARAMETER_SET_INCORRECT 
                - In case 'on_reboot' parameter relevant to the current 
                  DomU does not have 'restart' set as the value.

         Return PATCH_SUCCESS_EXIT_CODE
                - In case all of the DomU as per preserved list have
                  auto startup files and 'on_reboot' has 'restart' value 
                  in vm.cfg.
        """

        _rc = PATCH_SUCCESS_EXIT_CODE
        _soft_link_missing_node = []
        _on_reboot_parameter_not_set = []
        _auto_start_file = None
        _ret = 0
        _autostart_rc = 0


        '''
         This check can be skipped in case of
         exasplice patching.
        '''
        if self.ghandler.mIsExaSplice():
            self.mPatchLogInfo("DomU Auto startup validations will be skipped in case of Exasplice patching.")
            return _rc
            
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDom0)

        self.mPatchLogInfo(f"Performing DomU Auto startup validations on {aDom0}")
        try:
            for _domU in aDomUList:

                if self.ghandler.mIsKvmEnv():
                    _auto_start_file = f"{KVM_AUTO_START_DIR}/{_domU}.xml"
                else:
                    _auto_start_file = f"{XEN_AUTO_START_DIR}/{_domU}.cfg"

                # Check for file Auto startup existence
                if not _node.mFileExists(_auto_start_file):
                    vm_handler = ebVgLifeCycle()
                    vm_handler.mSetOVMCtrl(get_gcontext(), _node)
                    '''
                     Disable auto startup in case of symlink manually
                     removed as enable auto startup will not work in case 
                     of missing symlink. 
                    '''
                    if self.ghandler.mIsKvmEnv():
                        _ret = vm_handler.mGetVmCtrl().mAutoStartVM(_domU, False)
                        if _ret and int(_ret) != 0:
                            self.mPatchLogWarn(
                                f"Error in disabling DomU Auto Startup on Dom0 {aDom0} for the DomU {str(_domU)} in a KVM environment.")
                        else:
                            self.mPatchLogInfo(f"KVM AutoStart on Dom0 {aDom0} for the DomU {str(_domU)} was disabled.")

                    _autostart_rc = vm_handler.mGetVmCtrl().mAutoStartVM(_domU, True)
                    if _autostart_rc and int(_autostart_rc) != 0:
                        _suggestion_msg = f'Failed to create AutoStart on Dom0 : {aDom0} for the DomU : {str(_domU)}. Re-create soft link file manually and re-try patch'
                        if self.ghandler.mGetTask() == TASK_PREREQ_CHECK:
                            self.mPatchLogWarn(f"{_suggestion_msg}")
                        else:
                            _rc = DOMU_AUTO_STARTUP_FILE_MISSING_ERROR
                            self.ghandler.mAddError(_rc, _suggestion_msg)
                        return _rc

                    # Check again for file Auto startup existence
                    if not _node.mFileExists(_auto_start_file):
                        _soft_link_missing_node.append(_domU)

            if len(_soft_link_missing_node) > 0:
                _suggestion_msg = f'Auto startup soft link file missing on Dom0 : {aDom0} for the DomU(s) : {str(_soft_link_missing_node)}. Re-create soft link file and re-try patch'
                if self.ghandler.mGetTask() == TASK_PREREQ_CHECK:
                    self.mPatchLogWarn(f"{_suggestion_msg}")
                else:
                    _rc = DOMU_AUTO_STARTUP_FILE_MISSING_ERROR
                    self.ghandler.mAddError(_rc, _suggestion_msg)
                return _rc
       
            '''
             Validate if on_reboot = 'restart' is set in
             <vm name>.cfg in case of Xen env.

             Validate if <on_reboot>restart</on_reboot> is set in
             <vm name>.xml in case of KVM env.

             Example message in case of a failure.

               Infra Patching error is 0x0303001B and error_str is Auto startup soft link
               missing for the DomU running on the current Dom0. Re-create soft link, verify if
               on-reboot in vm.cfg is set to restart and retry patch.
            '''
            for _domU in aDomUList:
                _cmd = f"grep on_reboot {_auto_start_file} | grep -i 'restart'"
                _node.mExecuteCmd(_cmd)
                if int(_node.mGetCmdExitStatus()) != 0:
                    _on_reboot_parameter_not_set.append(_domU)
                   
            if len(_on_reboot_parameter_not_set) > 0:
                _suggestion_msg = f"on_reboot parameter specific to DomU(s) - {str(_on_reboot_parameter_not_set)}'s {_auto_start_file} file not set to 'restart', DomU(s) will not startup post reboot of Dom0 - {aDom0}."
                if self.ghandler.mGetTask() == TASK_PREREQ_CHECK:
                    self.mPatchLogWarn(f"{_suggestion_msg}")
                else:
                    _rc = DOMU_AUTO_STARTUP_ONREBOOT_PARAMETER_SET_INCORRECT
                    self.ghandler.mAddError(_rc, _suggestion_msg)
                return _rc

        except Exception as e:
            self.mPatchLogError(f'Unable to validate DomU auto startup settings on {aDom0}. Error : {str(e)}')
        finally:
            _node.mDisconnect()
            return _rc
