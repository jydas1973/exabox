#
#
# constants.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      constants.py - This module contains all the constant used in each of the modules.
#
#    DESCRIPTION
#      This module contains all the constant used in each of the modules.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    09/11/25 - Enh 38173247 - EXACLOUD CHANGES TO SUPPORT DOMU ELU
#                           INFRA PATCH OPERATIONS
#    araghave    06/24/25 - Enhancement Request 38082882 - HANDLING EXACLOUD
#                           ELU CHANGES FOR DOM0 PATCHING
#    sdevasek    06/26/25 - Enh 38098176 - FILTER OUT WARNINGS OTHER MESSAGES
#                           WHEN CRSCTL CONFIG CRS IS RUN
#    antamil     01/31/25 - Enh 37300427 - Enable clusterless cell patching
#                           using management host
#    enrivera    31/01/25 - Bug 37524625 - INFRA PATCH DELETING PUBLIC KEYS ON DOM0,
#                           CAUSING VMBACKUP ISSUES
#    bhpati      12/02/24 - Bug 36563682 - AIM4EXACLOUD:0X03030008 - UNABLE TO
#                           ESTABLISH HEARTBEAT ON THE CELLS. NOT ALL CRS/DB
#                           SERVICES ARE UP ON DOMU
#    avimonda    10/15/24 - Enhancement Request 37164727 - Add
#                           HEARTBEAT_CHEK_INTERVAL_IN_SECONDS
#    emekala     10/25/24 - ENH 37070223 - SYNC MOCK HANLDERS WITH LATEST CODE
#                           FROM CORE INFRAPATCHING HANDLERS AND ADD SUPPORT
#                           FOR CUSTOM RESPONSE AND RACK DETAILS
#    emekala     10/17/24 - ENH 36657637 - COMMANDS EXECUTED IN PRE AND POST
#                           CHECKS SHOULD HAVE TIMEOUT
#    araghave    10/08/24 - Enh 36505637 - IMPROVE POLLING MECHANISM IN CASE
#                           OF INFRA PATCHING OPERATIONS
#    araghave    09/13/24 - Enh 36923844 - INFRA PATCHING CHANGES TO SUPPORT
#                           PATCHING ADMIN SWITCH
#    antamil     08/01/24 - Bug 36881089 - Configure passwordless ssh using
#                           ssh config file on management host
#    diguma      07/31/24 - Bug 36908409: NEED INDICATOR OF CLUSTER STORAGE
#                           TYPE IN THE EXACLOUD PAYLOAD
#    diguma      07/26/24 - Bug 36888324: CHECK FOR CELL SERVICES: MORE
#                           SERVICES IN EXASCALE
#    sdevasek    07/22/24 - ENH 36773605 - MAKE PDB_DEGRADED_STATES_MATRIX
#    emekala     07/19/24 - ENH 36794217 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE EXACOMPUTE AND DOMU PATCHMGR CMDS
#    araghave    07/15/24 - Enh 36830077 - CLEANUP KSPLICE CODE FROM
#                           INFRAPATCHING FILES
#    diguma      07/10/24 - bug 36727709: CONFIGURE LISTENINGINTERFACE ON CELL
#                           NODES AFTER 24.1 PATCHING
#    sdevasek    05/20/24 - ENH 36696921 - UPDATE ERROR_MSG COL TO HAVE 4K LEN
#                           IN ECS_EXA_APPLIED_PATCHES_TABLE TO ACCOMODATE 4000
#                           CHAR LENGTH FOR MADDERROR ERROR MESG SUGGESTION
#    araghave    05/30/24 - Enh 36293209 - USE PLUGIN FILES FROM THE NEW
#                           EXADATA VERSION PLUGIN LOCATION
#    sdevasek    05/29/24 - ENH 36659116 - ECRA WR FOR DOMU OS PATCHING STATE
#                           IS NOT CHANGED FROM 202 TO 500 DUE TO ERROR_MESSAGE
#                           STRING OVERFLOW FOR TABLES ECS_REQUESTS_TABLE,
#                           ECS_EXA_APPLIED_PATCHES_TABLE
#    sdevasek    05/20/24 - ENH 36296976 - VALIDATE FOR PDBS RUNNING STATE AND
#                           FOR PDBS IN RESTRICTED MODE DURING DOMU PATCHING
#    antamil     03/11/24 - Enh 36372221 - Code changes for single VM EXACS
#                           patching support
#    araghave    02/28/24 - Enh 36295801 - IMPLEMENT ONEOFFV2 PLUGIN EXACLOUD
#                           CHANGES
#    emekala     02/14/24 - ENH 36261828 - ADD MOCK SUPPORT WITHIN
#                           INFRAPATCHING LAYER TO RUN INFRAPATCHING OPERATIONS
#                           IN MOCK MODE
#    sdevasek    01/30/24 - ENH 35306246 - ADD DB HEALTH CHECKS 
#                           DURING DOMU OS PATCHING
#    diguma      01/29/24 - Bug 36237643: EXACS - INFRAPATCHING - ADD SUPPORT 
#                           TO UPGRADE DOMU KVM GUEST WITH ONLY U02 ENCRYPTED
#                           IN OL8
#    avimonda    01/18/24 - 35972504 - EXACS | EXACLOUD TAKES 10HOURS FOR CELL
#                           PATCH CLEANUP
#    josedelg    12/18/23 - Enh 36073825 - Create static ordered cell list
#    emekala     10/04/23 - ENH 35545568 - STASH GUEST VM EXADATA PATCHMGR LOGS
#                           TO ADBD LOGGER LOCATION
#    antamil     08/03/23 - ENH 35621978 - ENABLE CPS AS LAUNCHNODE FOR
#                           DOMU PATCH OPERATION
#    jyotdas     06/30/23 - BUG 35460949 - Infra prechecks blocked by domu
#                           prechecks
#    diguma      04/18/23 - bug 34582467 - constants for custom plugin scripts
#    diguma      02/16/23 - Bug 35080646 - key api script location
#    araghave    01/04/23 - Enh 34823378 - EXACLOUD CHANGES TO HANDLE
#                           EXACOMPUTE PRECHECK AND BACKUP OPERATIONS
#    araghave    01/04/23 - Enh 34915866 - ADD SUPPORT FOR ROLLBACK IN
#                           EXACOMPUTE PATCHING
#    araghave    01/13/22 - Enh 34859379 - PERFORM CRS BOUNCE BEFORE HEARTBEAT
#                           CHECK TIMEOUT, IF DOMUs ARE UNABLE TO ESTABLISH
#                           A HEART BEAT TO THE CELLS
#    josedelg    01/03/23 - Bug 34905057 - Identify properly OL8 kvm file
#    antamil     12/13/22 - BUG 34863652 - CHANGES ON INFRAPATCHING PRECHECK
#                           TO COMPLETE WITHIN 15mins     
#    diguma      12/01/22 - Enh 34840180 - addition of specific alerts for
#                           ExaCC
#    sdevasek    10/21/22 - BUG 34632765 - IPTABLES SVC IS NOT STARTED IN POST
#                           PATCHING WHEN ANY OF THE POSTCHECK FAILS
#    araghave    10/07/22 - Enh 34623863 - PERFORM SPACE CHECK VALIDATIONS
#                           BEFORE PATCH OPERATIONS ON TARGET NODES
#    vmallu      08/29/22 - INCREASE RETRY PATCHMGR CLEANUP CHECK MAX COUNTER
#                           VALUE TO FIX INFRA PATCHING FAILURE DURING CELL
#                           CLEANUP
#    josedelg    08/23/22 - Bug 34520998 - Cleanup fix 21.2.14.0.0
#    araghave    08/17/22 - Enh 34350140 - EXACLOUD CHANGES TO HANDLE
#                           EXACOMPUTE PRECHECK AND PATCHING OPERATIONS
#    josedelg    08/17/22 - Bug 34480937 - Increase cell cleanup timeout
#    jyotdas     07/22/22 - ENH 34350151 - Exacompute Infrapatching
#    pkandhas    06/16/22 - Bug 34050453 - Change the value of 
#                           PARALLEL_OPERATION_TIMEOUT_IN_SECONDS to 180
#    sdevasek    05/22/22 - ENH 33859232 - TRACK TIME PROFILE INFORMATION FOR
#                           INFRAPATCH OPERATIONS
#    jyotdas     05/17/22 - ENH 34168677 - Enhance patch list api to consume
#                           the display flag based on retention policy
#    sdevasek    05/11/22 - ENH 34053202 - INFRAPATCHING PRECHECK TO VALIDATE
#                           THE PRESENCE OF DOM0_IPTABLES_SETUP.SH SCRIPT
#    nmallego    04/25/22 - Bug33689792 - Skip dummy domu for exacloud plugins
#    araghave    02/09/22 - Bug 33686503 - Populate status reporting details for 
#                           all the nodes in the list.
#    araghave    02/20/22 - Bug 33847682 - DELAYED PATCHMGR PROCESS EXIT CAUSES
#                           SUBSEQUENT PATCHMGR CLEANUP TO FAIL
#    araghave    02/02/22 - Enh 33813626 - Add switchexa user access during
#                           Roce Switch
#    araghave    12/06/21 - Enh 33052410 - Purge System first boot image file
#                           for Dom0 space management
#    araghave    11/25/21 - Bug 33607195 - Validate ssh connectivity check
#                           between Roceswitch and Dom0 using ciscoexa user
#    araghave    11/23/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES
#                           FROM CONSTANTS.PY TO INFRAPATCHERROR.PY
#    nmallego    11/19/21 - Bug33584494 - Add 
#                            SHUTDOWN_STARTUP_SLEEP_INTERVAL_IN_SECONDS
#    nmallego    11/12/21 - Bug33521580 - add
#                           CELL_ASM_MODE_STATUS_STILL_ONLINE_ERROR
#    nmallego    11/09/21 - Bug33531232 - Add
#                           WAIT_FOR_VM_OPERATION_TO_COMPLETE_IN_SEC
#    araghave    10/21/21 - Enh 33387834 - THROW APPROPRIATE ERROR MSG WHEN
#                           ONLY ONE NODE IS AVAILABLE
#    araghave    10/20/21 - Enh 33486853 - MOVE TIMEOUT AND OTHER CONSTANTS OUT
#                           OF CODE INTO CONFIG/CONSTANT FILES
#    araghave    10/05/21 - Enh 33378051 - VALIDATE FOR DOMU AUTO STARTUP
#                           DETAILS DURING PRE/POST DOM0 PATCH OPERATIONS
#    josedelg    10/04/21 - Bug 33285054 - VIF-BRIDGE symlinks validation in
#                           the post check operation
#    jyotdas     09/20/21 - Enh 33290086 - stale mount check before starting
#                           dbserver patching for all nodes
#    araghave    09/17/21 - Enh 33345801 - ADD SSH PRE-CHECKS AS PART OF INFRA
#                           PATCHING PRECHECKS
#    nmallego    09/02/21 - Bug33249608 - Support non-rolling option
#    araghave    09/07/21 - Enh 32626119 - Infra patching to notify end user
#                           regarding Grid Disks in Unused/Syncing status
#    araghave    08/02/21 - Enh 33182904 - Move all configurable parameters
#                           from constants.py to Infrapatching.conf
#    sdevasek    08/19/21 - ENH 33238101 - CHANGE SLEEP TIME BETWEEN NODE TO 
#                           120 MINS FROM 30 MINS
#    araghave    07/27/21 - BUG 32888598 - ISSUE WITH ASYNC CALLS DURING INFRA
#                           PATCHING
#    araghave    07/09/21 - BUG 33081173 - Remove older error codes from Infra
#                           patching core files
#    nmallego    07/14/21 - ER 32925372 - Allow domU patching when dom0 monthly
#                           progressing 
#    araghave    07/11/21 - ENH 33099120 - INTRODUCE A SPECIFIC ERROR CODE FOR
#                           PATCHMGR CONSOLE READ TIME OUT
#    araghave    05/19/21 - Bug 32888765 - Get Granular Error Handling details
#                           for Cells and Switches
#    josedelg    05/08/21 - ENH 32586428 - Configure known alerts in
#                           infrapatching.conf
#    jyotdas     05/13/21 - ENH 32803507 - populate error message from exacloud
#                           outside patchlist attribute
#    araghave    04/20/21 - Bug 32397257 - Get granular error handling details
#                           for Dom0 and DomU targets
#    josedelg    04/15/21 - Bug 32711562 - Patch failed/stuck due to corrupted
#                           rpm database
#    alsepulv    03/22/21 - Enh 32619413: remove any code related to Higgs
#    nmallego    03/18/21 - ER 32581076: Add constants for domU exist check
#    araghave    03/15/21 - Enh 32415170 - Introduce specific Error Codes for
#                           Dom0 and DomU Exacloud Plugins
#    nmallego    02/08/21 - Bug32433614 - constants for sleep b/w nodes
#    araghave    02/02/21 - Bug 32120772 - EXASPLICE AND PYTHON 3 FIXES
#    araghave    01/19/21 - Bug 32395969 - MONTHLY PATCHING: FOUND FEW ISSUES
#                           WHILE TESTING AND NEED TO FIX
#    araghave    01/12/21 - Enh 31446326 - SUPPORT OF SWITCH OPTION AS TARGET
#                           TYPE THAT TAKES CARE OF BOTH IB AND ROCESWITCH
#    araghave    01/07/21 - Bug 32320030 - ROCE SWITCH REFACTOR CODE CHANGES
#    araghave    01/06/21 - Enh 31869399 - INTRODUCE SPECIFIC ERROR CODES IN
#                           CPS OS UPGRADE SCRIPTS
#    araghave    01/05/21 - Bug 32343803 - INFRAPATCHING: INVALID REQUEST ADDED
#                           WHEN PATCHING ATTEMPTED VIA CURL
#    josedelg    12/23/20 - Bug 32319928 - Error handling format issue
#    nmallego    12/07/20 - Bug31982131 - Error for hardware alert
#    araghave    12/01/20 - Enh 31604386 - RETURN ERROR CODES TO DBCP FOR CELLS
#                           AND SWITCHES
#    araghave    12/08/20 - Enh 31984849 - RETURN ERROR CODES TO DBCP FROM DOMU
#                           AND PLUGINS
#    araghave    11/11/20 - Enh 31925002 - Error code handling implementation
#                           for Monthly Patching
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#

import os
import re
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

#All Tasks
TASK_PREREQ_CHECK = "patch_prereq_check"
TASK_PATCH = "patch"
TASK_POSTCHECK = "postcheck"
TASK_ROLLBACK_PREREQ_CHECK = "rollback_prereq_check"
TASK_ROLLBACK = "rollback"
TASK_BACKUP_IMAGE = "backup_image"
TASK_ONEOFF = "oneoff"
TASK_ONEOFFV2 = "oneoffv2"
TASK_SWITCHOVER = "switchover"
TASK_SWITCHOVER_STATUS = "switchoverstatus"

#All Targets
PATCH_DOM0 = "dom0"
PATCH_CELL = "cell"

PATCH_CELL_CLUSTERLESS = "cell_clusterless"
PATCH_DOM0_CLUSTERLESS = "dom0_clusterless"


# Switch naming convention applicable to both IB and Roce Switches
PATCH_SWITCH = "switch"

#for backward compatibility .. remove later
#Switches in non KVM environment
PATCH_IBSWITCH = "ibswitch"

# Switches in ROCE environment
PATCH_ROCESWITCH = "roceswitch"

# Switches in both Xen/Kvm env
PATCH_ADMINSWITCH = "adminswitch" 
PATCH_DOMU = "domu"
PRE_PATCH = "pre_patch"
PATCH_EXACOMPUTE = "exacompute"
PLUGIN_DBNU = "dbnu_plugins"
PLUGIN_EXACLOUD = "exacloud_plugins"
POST_PATCH = "post_patch"
PATCH_ALL = "all_nodes"
PATCH_TYPE_QUARTERLY = "quarterly"
PATCH_TYPE_MONTHLY   = "monthly"

THREADS_LOG_DIRECTORY = "log/threads/0000-0000-0000-0000"

#Task Handler Map
TASK_HANDLER_MAP = {
    TASK_PREREQ_CHECK:"exabox.infrapatching.handlers.taskHandler.prereqhandler.PreReqHandler",
    TASK_PATCH : "exabox.infrapatching.handlers.taskHandler.patchhandler.PatchHandler",
    TASK_POSTCHECK : "exabox.infrapatching.handlers.taskHandler.postcheckhandler.PostCheckHandler",
    TASK_ROLLBACK : "exabox.infrapatching.handlers.taskHandler.rollbackhandler.RollBackHandler",
    TASK_ROLLBACK_PREREQ_CHECK : "exabox.infrapatching.handlers.taskHandler.rollbackprereqhandler.RollbackPreReqHandler",
    TASK_BACKUP_IMAGE : "exabox.infrapatching.handlers.taskHandler.backupimagehandler.BackupImageHandler",
    TASK_ONEOFF : "exabox.infrapatching.handlers.taskHandler.plugintaskshandler.PluginTasksHandler",
    TASK_ONEOFFV2 : "exabox.infrapatching.handlers.taskHandler.plugintaskshandler.PluginTasksHandler"
}

#Target Handler Map
TARGET_HANDLER_MAP = {
    PATCH_DOM0:"exabox.infrapatching.handlers.targetHandler.dom0handler.Dom0Handler",
    PATCH_DOM0_CLUSTERLESS: "exabox.infrapatching.handlers.targetHandler.dom0handlerclusterless.Dom0HandlerClusterless",
    PATCH_DOMU : "exabox.infrapatching.handlers.targetHandler.domuhandler.DomUHandler",
    PATCH_IBSWITCH : "exabox.infrapatching.handlers.targetHandler.switchhandler.SwitchHandler",
    PATCH_CELL : "exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler",
    PATCH_CELL_CLUSTERLESS : "exabox.infrapatching.handlers.targetHandler.cellhandlerclusterless.CellHandlerClusterless",
    PATCH_ROCESWITCH : "exabox.infrapatching.handlers.targetHandler.roceswitchhandler.RoceSwitchHandler"
}

#Task Mock Handler Map
TASK_MOCK_HANDLER_MAP = {
    TASK_PREREQ_CHECK:"exabox.infrapatching.handlers.mockTaskHandler.prereqmockhandler.PreReqMockHandler",
    TASK_PATCH : "exabox.infrapatching.handlers.mockTaskHandler.patchmockhandler.PatchMockHandler",
    TASK_POSTCHECK : "exabox.infrapatching.handlers.mockTaskHandler.postcheckmockhandler.PostCheckMockHandler",
    TASK_ROLLBACK : "exabox.infrapatching.handlers.mockTaskHandler.rollbackmockhandler.RollBackMockHandler",
    TASK_ROLLBACK_PREREQ_CHECK : "exabox.infrapatching.handlers.mockTaskHandler.rollbackprereqmockhandler.RollbackPreReqMockHandler",
    TASK_BACKUP_IMAGE : "exabox.infrapatching.handlers.mockTaskHandler.backupimagemockhandler.BackupImageMockHandler",
    TASK_ONEOFF : "exabox.infrapatching.handlers.mockTaskHandler.plugintasksmockhandler.PluginTasksMockHandler"
}

#Target Mock Handler Map
TARGET_MOCK_HANDLER_MAP = {
    PATCH_DOM0:"exabox.infrapatching.handlers.mockTargetHandler.dom0mockhandler.Dom0MockHandler",
    PATCH_DOMU : "exabox.infrapatching.handlers.mockTargetHandler.domumockhandler.DomUMockHandler",
    PATCH_IBSWITCH : "exabox.infrapatching.handlers.mockTargetHandler.switchmockhandler.SwitchMockHandler",
    PATCH_CELL : "exabox.infrapatching.handlers.mockTargetHandler.cellmockhandler.CellMockHandler",
    PATCH_ROCESWITCH : "exabox.infrapatching.handlers.mockTargetHandler.roceswitchmockhandler.RoceSwitchMockHandler"
}

EXACOMPUTE_HANDLER_MAP = {
    TASK_PATCH : "exabox.infrapatching.exacompute.handlers.exacomputepatchhandler.ExaPatchHandler",
    TASK_ROLLBACK : "exabox.infrapatching.exacompute.handlers.exacomputerollbackhandler.ExaRollbackHandler",
    TASK_PREREQ_CHECK : "exabox.infrapatching.exacompute.handlers.exacomputeprecheckhandler.ExaPrecheckHandler",
    TASK_BACKUP_IMAGE : "exabox.infrapatching.exacompute.handlers.exacomputebackuphandler.ExaBackupHandler",
    TASK_POSTCHECK : "exabox.infrapatching.exacompute.handlers.exacomputepostcheckhandler.ExaPostcheckHandler"
}

PARALLEL_OPERATIONS_ALLOWED_MATRIX = [
    #runningTarget, ongoingOperation,ongoingPatchType,incomingTarget,incomingOperation,incomingPatchType
    # Incoming and ongoing target should not be same for infra (dom0 and cell), else there can be overlap of launch node and multiple
    # patchmgr session will try to run on launch node which we do not allow, except for extarenal launch node
    ["dom0", "patch_prereq_check", "quarterly","domu","patch_prereq_check","quarterly"],  #Allow domU quarterly precheck during dom0 quarterly precheck
    ["domu", "patch_prereq_check", "quarterly","dom0","patch_prereq_check","quarterly"],  #Allow dom0 quarterly precheck during domu quarterly precheck
    ["domu", "patch_prereq_check", "quarterly","cell","patch_prereq_check","quarterly"],  #Allow cell quarterly precheck during domu quarterly precheck
    ["cell", "patch_prereq_check", "quarterly","domu","patch_prereq_check","quarterly"],  #Allow domu quarterly precheck during cell quarterly precheck
    ["dom0", "patch", "monthly","domu","patch","quarterly"],  # Allow domU patching while dom0 monthly/exasplice patch is progressing.
    ["domu", "patch", "quarterly","dom0","patch","monthly"],  # Allow dom0 exasplice patching while domu quarterly patch is progressing.
    ["domu", "patch_prereq_check", "quarterly","dom0","patch","monthly"],  # Allow dom0 exasplice patching while domu quarterly precheck is progressing.
]

ANSI_ESCAPE = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
WAIT_LINES_ESCAPE = re.compile(r'(/|-|\||\\){5}')
PATCH_CONSOLE_LOG = "PatchmgrConsole.out"
PATCH_STDOUT = "patchmgr.stdout"
PATCH_STDERR = "patchmgr.stderr"
PATCH_TRC = "patchmgr.trc"
PATCH_LOG = "patchmgr.log"
IBSWITCH_LOG = "upgradeIBSwitch.log"
IBSWITCH_TRC = "upgradeIBSwitch.trc"
ROCESWITCH_LOG = "switch_admin.log"
ROCESWITCH_TRC = "switch_admin.trc"
EXADATA_BUNDLES_METADATA_FILE = "exadata_bundles_metadata.json"

'''
 Post Exadata 21.2.8, switchexa is the default user 
 used to patch roceswitches. Hence ssh connectivity 
 validations between dom0 and switch are performed
 using switchexa and not with ciscoexa as previously
 done.
'''
ROCESWITCH_USER = "switchexa"

CELL_ALERT_LOG = "$CELLTRACE/alert.log"
KVM_AUTO_START_DIR = "/etc/libvirt/qemu/autostart"
XEN_AUTO_START_DIR = "/etc/xen/auto"
SYSCTL_CONF = "/etc/sysctl.conf"
SYSCTL_99_CONF = "/etc/sysctl.d/99-sysctl.conf"
CPS_MASTER_NODE_FILE = "/etc/keepalived/MASTER"
DOM0_IPTABLES_SETUP_SCRIPT = "/opt/exacloud/network/dom0_iptables_setup.sh"
EXACLOUD_IPTABLES_SETUP_SCRIPT = "scripts/network/dom0_iptables_setup.sh"

PATCH_PENDING   = "pending"
PATCH_RUNNING   = "running"
PATCH_FAILED    = "failed"
PATCH_COMPLETED = "completed"
PATCH_SLEEP_START = "sleep_started"
PATCH_SLEEP_END = "sleep_ended"
PATCH_MGR = "patch_mgr"

PAYLOAD_RELEASE = 'exadata_release'
PAYLOAD_NON_RELEASE = 'one-offs'
ENV_PRODUCTION = 'production'
ENV_PREPRODUCTION = 'preproduction'
ENV_DEVELOPMENT = 'development'
ENV_TEST = 'test'
OP_STYLE_AUTO = 'auto'
OP_STYLE_ROLLING = 'rolling'
OP_STYLE_NON_ROLLING = 'non-rolling'
OP_BACKUPMODE_NO = 'no'
OP_BACKUPMODE_YES = 'yes'
OP_FEDRAMP_ENABLED = 'ENABLED'
OP_FEDRAMP_DISABLED = 'DISABLED'
PREPATCH_CRS_LOG = "/var/log/exadatatmp/prepatch_crs_stat.log"
POSTPATCH_CRS_LOG = "/var/log/exadatatmp/postpatch_crs_stat.log"
DUMMYDOMU = "dummydomu"

STEP_SELECT_LAUNCH_NODE = 'select_launch_node_and_copy_files'
STEP_FILTER_NODES = 'filter_nodes'
STEP_GATHER_NODE_DATA = 'gather_data'
STEP_PREP_ENV = 'prepare_environment'
STEP_RUN_PATCH_CELL = 'patch_cells'
STEP_RUN_PATCH_SWITCH = 'patch_switches'
STEP_RUN_PATCH_DOM0 = 'patch_dom0s'
STEP_RUN_PATCH_DOMU = 'patch_domus'
STEP_RUN_PATCH_SECOND_DOM0 = 'patch_init_dom0'
STEP_RUN_PATCH_SECOND_DOMU = 'patch_init_domu'
STEP_CLEAN_UP = 'clean_up_cells'
STEP_CLEAN_ENV = 'clean_environment'
STEP_POSTCHECKS = 'run_postchecks'
STEP_END = 'patch_done'
STEP_SHUTDOWN_VMS = 'shutdown_vms'
STEP_STOP_CELL_SERVICES = 'stop_cell_services'
STEP_START_VMS = 'start_vms'
STEP_START_CELL_SERVICES = 'start_cell_services'

PATCH_ONLY_CELL_STEP_LIST = [STEP_RUN_PATCH_CELL, STEP_CLEAN_UP]
PATCH_ONLY_SWITCH_STEP_LIST = [STEP_RUN_PATCH_SWITCH]

# patching input json keys
KEY_NAME_Dom0_YumRepository = 'Dom0YumRepository'
KEY_NAME_Domu_YumRepository = 'DomuYumRepository'
KEY_NAME_PatchFile = 'PatchFile'
KEY_NAME_DBPatchFile = 'DBPatchFile'
KEY_NAME_CellPatchFile = 'CellPatchFile'
KEY_NAME_SwitchPatchFile = 'SwitchPatchFile'

# CNS constants
CNS_DOM0_PATCHER = 'cns.dom0_patcher'
CNS_DOMU_PATCHER = 'cns.domu_patcher'

# Env types constants, it's used for future
ENV_ECS = 'ecs'

# KVM file substring
KVM_FILE_IDENTIFIER_LIST = ["ol7","ol8"]

# All handlers in the system
INFRA_PATCHING_HANDLERS = {}

# Constants that are rarely modified.
PARALLEL_OPERATION_TIMEOUT_IN_SECONDS = 180
SLEEP_CELL_PATCHMGR_CLEANUP_IN_SECONDS = 60
SLEEP_CELL_WAIT_BEFORE_POSTCHECK_IN_SECONDS = 300
PARALLEL_OPERATION_CRS_TIMEOUT_IN_SECONDS = 1200

# Constants used in clupatchhealthcheck while vm shutdown or startup. 
SHUTDOWN_STARTUP_SLEEP_INTERVAL_IN_SECONDS = 10 

INFRA_PATCHING_KNOWN_ALERTS_EXACC = "infra_patching_known_alerts_exacc"
INFRA_PATCHING_KNOWN_ALERTS_EXACS = "infra_patching_known_alerts_exacs"
INFRA_PATCHING_KNOWN_ALERTS_EXACOMPUTE = "infra_patching_known_alerts_exacompute"
PDB_DEGRADED_STATES_MATRIX_KEY = "pdb_degraded_states_matrix"
INFRA_PATCHING_CONF_FILE = "infrapatching.conf"
EXACOMPUTE_PATCH_CONF_FILE = "exacomputepatch.conf"
EXAVMIMAGES = "/EXAVMIMAGES/"
ROOT_PARTITION = "/"
REQUIRED_ROOT_PARTITION_SPACE = 1024
DBSERVER_BACKUP_EXIT_CODE_ERROR = 1
DBSERVER_BACKUP_EXIT_CODE_NO_ROLLBACK_AVAILABLE = 3

RETRY_PATCHMGR_PROCESS_COMPLETION_CHECK_MAX_COUNTER_VALUE = 12
WAIT_FOR_PATCHSUCCESSEXIT_IN_SECONDS = 5

# Constants specific to Patchmgr notifications.
RETRY_PATCH_NOTIFICATION_CHECK_MAX_COUNTER_VALUE = 30
WAIT_PATCH_NOTIFICATION_DIRECTORY_TIMEOUT_IN_SECONDS = 10

# Constants to indicate what service type we are in
EXACC_SRV = "exacc_srv"
EXACS_SRV = "exacs_srv"
EXACOMPUTE_SRV = "exacompute_srv"

RETRY_CRS_SERVICES_SLEEP_IN_SECONDS = 300
RETRY_CRS_STARTUP_CHECK_MAX_COUNTER_VALUE = 3
WAIT_FOR_CRSCTL_START_COMMAND_TO_COMPLETE_IN_SECONDS = 180
CRS_AUTO_START_CHECK_CODE = "CRS-4622"
CRS_AUTO_START_CHECK_STR = "Oracle High Availability Services autostart is enabled"

# Constants used for encryption
KEY_API = "/usr/lib/dracut/modules.d/99exacrypt/VGExaDbDisk.u02_extra_encrypted.img#LVDBDisk.key-api.sh"

# custom plugins
CUST_PLUGIN_DOM0 = '/opt/exacloud/customs/plugins/custom_dom0.sh'
CUST_PLUGIN_DOM0_DOMU = '/opt/exacloud/customs/plugins/custom_dom0_domu.sh'
CUST_PLUGIN_DOMU = '/opt/exacloud/customs/plugins/custom_domu.sh'
CPS_LAUNCH_NODE_PATCH_BASE = '/opt/oci/exacc/exacloud/InfraPatchBase/'
MANAGEMENT_HOST_LAUNCH_NODE_PATCH_BASE = '/var/odo/InfraPatchBase/'
DOMU_LAUNCH_NODE_PATCH_BASE = '/u02/'

# adbd infra domu patch log consumption location
ADBD_INFRA_DOMU_PATCH_LOG_CONSUMPTION_LOCATION = "/var/opt/oracle/log/infra_domu_patch_logs"

# One off v2 remote patch stage location
ONEOFF_REMOTE_STAGE_DIR = "/opt/exacloud/customs/plugins/oneoff_patches/"

# Plugin Metadata based Exacloud plugin remote patch stage location
EXACLOUD_PLUGIN_REMOTE_STAGE_DIR = "/opt/exacloud/customs/plugins/exacloud_plugins/"

# Plugin Metadata based Dbnu plugin remote patch stage location
DBNU_PLUGIN_REMOTE_STAGE_DIR = "/opt/exacloud/customs/plugins/dbnu_plugins/"

MINIMUM_NUMBER_OF_CELLS_REQUIRED_TO_REORDER = 7

# dbaasapi infra pre/post sanity check constants
INFRA_SANITY_CHECK_SCOPE_VM = "VM"
INFRA_SANITY_CHECK_OPERATION = "sanity_check"
INFRA_SANITY_POSTCHECK = "postcheck"
INFRA_SANITY_PRECHECK = "precheck"
INFRA_SANITY_CRS_RESOUCE_CHECK = "CRS_RESOURCE"
INFRA_SANITY_ERROR = "error"
DBAASAPI_COMMAND_PATH = "/var/opt/oracle/dbaasapi/dbaasapi"
DBAASCLI_COMMAND_PATH = "/usr/bin/dbaascli"
EXADATA_TMP_VAR_LOG_LOCATION = "/var/log/exadatatmp"
DBAASAPI_SANITY_CHECK_LOG_PATH = "/var/opt/oracle/log/sanity_check/"
DBAASAPI_SANITY_CHECK_LOG = "sanity_check.log"
EXACC_PLUGIN_STAGE_PATH = "/u01/downloads/exadata/exadataPrePostPlugins"
INFRA_SANITY_ERROR_MSG_SUGGESTION = ".... Please check /var/opt/oracle/log/sanity_check/sanity_check.log for more details."
ERROR_MSG_TRUNCATE_LENGTH = 4000

# sleep for MS services
MS_SERVICES_SLEEP = 10

# Exascale constants
ASM_CLUSTER_STORAGE_TYPE="ASM"
EXASCALE_CLUSTER_STORAGE_TYPE="XS"
ESCLI_WALLET_LOCATION="/opt/oracle/cell/cellsrv/deploy/config/security/admwallet"
ESCLI_CMD="/opt/oracle/cell/cellsrv/bin/escli"


# Lock file name for fcntl lock implementation
LOCK_FILE_NAME="/tmp/file_lock"

# ONEOFFV2
ONEOFFV2_SLEEP_TIMEOUT_IN_SECONDS = 20

DOM0_DOMU_ONLINE_STATUS_CHECK_SLEEP_IN_SECONDS = 2
HEARTBEAT_CHECK_INTERVAL_IN_SECONDS = 10
DBHEALTHCHECK_TIMEOUT_IN_SECONDS = 30

# Infrapatching custom mock patch json file capturing mock rack and response details. Its placed under exacloud/config/
CUSTOM_MOCK_PATCH_FILE_NAME = "custom_mock_patch.json"

# Default timeout value in secs for all infra patching cmds executed via Exacloud mExecute api
SHELL_CMD_DEFAULT_TIMEOUT_IN_SECONDS = 180

# Exacloud mExecute api exit code when cmd timeout
SHELL_CMD_TIMEOUT_EXIT_CODE = 124

# SSH keys
EXAPATCHING_KEY_TAG = "EXAPATCHING KEY"


LAUNCHNODE_TYPE_MANAGEMENT_HOST = 'MANAGEMENT_HOST'
LAUNCHNODE_TYPE_COMPUTE = 'COMPUTE'

# For ELU validations.
INVALID_REGISTERED_PATCH_VERSIONS = [ "0.0.0.0.0.0" ]
ELU_VERSION_STR ="Exadata Live Update Version"
ELU_TYPE_STR ="Exadata Live Update Type"
ELU_APPLIED_REBOOT_MESSAGE = "(Live Update applied. Reboot at any time to finalize outstanding items.)"
ELU_HAS_OUTSTANDING_WORK_STR = "Exadata Live Update Has Outstanding Work"
CURRENT_QMR_VERSION_STR = "Image version"
