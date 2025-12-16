# $Header: ecs/exacloud/exabox/infrapatching/core/infrapatcherror.py /main/78 2025/12/03 05:30:07 sdevasek Exp $
#
# infrapatcherror.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      infrapatcherror.py - Contains methods and error code details
#                           specific to Infra patching.
#
#    DESCRIPTION
#      Contains methods and error code details specific to Infra patching.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    remamid     11/18/25 - Add new error code for singlenode patch failure due
#                           to base node space issue bug 38667536
#    mirrodri    10/14/25 - Bug 38264211 INFRA-PATCH:NON-ROLLING CELL PATCHING 
#                           PROCEEDS WHEN ESNP SERVICE WAS NOT SHUTDOWN. AFTER 
#                           PATCHING SERVICES ARE NOT BROUGHT BACK UP.
#    sdevasek    10/10/25 - ENH 38437135 - IMPLEMENT ADDITION OF SCRIPTNAME
#                           SCRIPTBUNLDENAME AND SCRIPTBUNDLEHASH ATTRIBUTES
#                           TO ECRA REGISTERED PLUGINS METADATA REGISTRATION
#    avimonda    10/07/25 - Bug 38475354 - AIM4ECS:0X03050015 - PATCHMGR
#                           SESSION ON VM ALREADY EXISTS. REFER MOS NOTE
#                           2829056.1 FOR MORE DETAILS.
#    araghave    09/11/25 - Enh 38173247 - EXACLOUD CHANGES TO SUPPORT DOMU ELU
#                           INFRA PATCH OPERATIONS
#    sdevasek    09/12/25 - Bug 38366221 SMR FAILED - 'EXCEPTION IN SETTING
#                           SERVICESTATE VALUE ON ILOM - ERROR : LIST INDEX
#                           OUT OF RANGE'
#    remamid     08/18/25 - Modify Error message for 0x03070006 bug 38224059
#    sdevasek    07/24/25 - Enh 38120913 - TIMEOUT RUNNING OF CUSTOM_DOMU.SH
#                           IF IT EXCEEDS 60 MINS
#    araghave    06/24/25 - Enhancement Request 38082882 - HANDLING EXACLOUD
#                           ELU CHANGES FOR DOM0 PATCHING
#    sdevasek    06/16/25 - Enh 38059285 - ENHANCE ERROR STRING MESSAGE
#                           "INDIVIDUAL PATCH REQUEST DURING PRECHECK EXCEPTION
#                           DETECTED ON VM"
#    avimonda    05/14/25 - Bug 37877715 - EXACS: DOMU OS PATCHING FAILED WITH
#                           NO ERROR MESSAGES OR LOGS AT VM END
#    sdevasek    03/24/25 - Enh 36496178 - HA CHECK INCORRECTLY REPORTS THE VM
#                           AS RUNNING DESPITE IT BEING STUCK IN BOOTING
#                           CAUSING WRONG CALCULATION IN HA VM RUNNING CHECKS
#    araghave    03/17/25 - Enh 37713042 - CONSUME ERROR HANDLING DETAILS FROM
#                           INFRAPATCHERROR.PY DURING EXACOMPUTE PATCHING
#    avimonda    03/03/25 - Bug 37541893 - EXACS |DOM0 ROLLBACK | FAILED (NOT
#                           SUPPORTED)
#    araghave    02/13/25 - Enh 34479463 - PROVIDE EXACLOUD REGISTRATION AND
#                           PLUGIN SUPPORT FOR CELLS
#    nelango     01/23/25 - Bug 37328906: ipmi servicestate checks
#    araghave    12/18/24 - Bug 37247140 - ALLOW DOMU ONEOFF PATCH TO COPY AND
#                           EXECUTE PLUGINS BASED ON AVAILABLE KEYS
#    sdevasek    01/07/24 - Bug 37442949 - DB HEALTH CHECKS - INCORRECT ERROR
#                           MESSAGE FOR LISTENER RESOURCE
#    avimonda    11/25/24 - Enhancement Request 37232972 - ADD
#                           EXADATA_PATCHES_CLEANUP_FAILED
#    emekala     10/22/24 - ENH 36657637 - COMMANDS EXECUTED IN PRE AND POST
#                           CHECKS SHOULD HAVE TIMEOUT
#    sdevasek    09/23/24 - ENH 36654974 - ADD CDB HEALTH CHECKS DURING DOM0
#                           INFRA PATCHING
#    araghave    08/31/24 - ER 36977545 - REMOVE SYSTEM FIRST BOOT IMAGE
#                           SPECIFIC CODE FROM INFRA PATCHING FILES
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    avimonda    07/23/24 - Add IMAGE_INFO_STATUS_EMPTY_OR_INVALID
#    araghave    07/15/24 - Enh 36830077 - CLEANUP KSPLICE CODE FROM
#                           INFRAPATCHING FILES
#    sdevasek    07/03/24 - ENH 36542989  -  VERIFY PDB HELATH CHECK ACROSS
#                           CLUSTER OF THE NODES DURING DOMU PATCH TO DETECT
#                           DOWNTIME   
#    jyotdas     06/26/24 - Bug 36730609 - Exacc Gen2 - domo qmr apply failure
#                           due to crs down - error action should be
#                           FAIL_DONTSHOW_PAGE_ONCALL
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    jyotdas     06/04/24 - Enh 36652413 - Change PAGE_ONCALL ERRORACTION to
#                           FAIL_DONTSHOW_PAGE_ONCALL
#    remamid     06/13/24 - Bug 36518641 - add error code for ssh failure due
#                           to host valdation error.
#    sdevasek    05/15/24 - ENH 36296976 - VALIDATE FOR PDBS RUNNING STATE AND
#                           FOR PDBS IN RESTRICTED MODE DURING DOMU PATCHING
#    araghave    04/25/24 - Bug 36543876 - ERROR OUT WHEN GRID HOME PATH BINARY
#                           DOES NOT EXISTS FOR CRS AUTOSTART ENABLED CHECK
#    araghave    04/19/24 - ER 36452945 - TERMINATE INFRA PATCHING THREAD EARLY
#                           IN CASE OF PATCHMGR COMMAND DID NOT RUN
#    diguma      03/24/24 - Bug 36442733 - MORE ROBUST METHOD TO OBTAIN
#                           CRS HOME
#    araghave    02/28/24 - Enh 36295801 - IMPLEMENT ONEOFFV2 PLUGIN EXACLOUD
#                           CHANGES
#    sdevasek    01/30/24 - ENH 35306246 - ADD DB HEALTH CHECKS 
#                           DURING DOMU OS PATCHING
#    avimonda    01/03/24 - Bug 36148893 - add 
#                           MASTER_PATCH_REQUEST_TO_EXACLOUD_FAIL
#    vikasras    12/12/23 - Bug 35972774 - OS PATCH PRECHECK WORKFLOW STUCK AT
#                           PAGE_ONCALL ERROR
#    jyotdas     11/29/23 - 35955958 - Ecra status call in pending status
#    sdevasek    11/15/23 - ENH 36011846 - RUN RDS_PING TO VALIDATE VM TO VM
#                           AND VM TO CELL CONNECTIVITY AFTER HEARTBEAT CHECK
#                           FAILURE IN DOM0 PATCHING
#    jyotdas     11/08/23 - Bug 35947965 - domu os patching errors should be
#                           fail_and_show
#    diguma      10/30/23 - ENH 35656193 - EXADATA CLOUD DOMU OS PATCHING
#                           PRECHECK CLOUD UI SHOWING INCORRECT MESSAGE
#                           // "DETECTED CRITICAL HARDWARE ALERT ON
#                           SPECIFIED TARGET."
#    antamil     10/17/23 - Bug 35835537 - Implement support for multiple external
#                                          launch node
#    sdevasek    10/04/23 - ENH 35853718 - CHECK FOR EXISTING VMS BEFORE
#                           PATCHING NODES FOR EXACOMPUTE
#    antamil     18/08/23 - ENH 35577433 - ADD VALIDATIONS ON EXTERNAL LAUNCH NODE
#                           PASSED
#    avimonda    09/15/23 - Bug 35659081 - Add
#                           PATCH_COPY_AND_IMAGE_CHECKSUM_VALIDATION_EXCEPTION
#    sdevasek    08/09/23 - ENH 35687013 - CREATE AND DELETE MARKER FILE DURING
#                           PATCHING WHEN CPS IS USED AS LAUNCHNODE
#    jyotdas     08/08/23 - ENH 35614504 - Define erroraction for infrapatching
#                           at errorcode level instead of targettype level
#    araghave    07/24/23 - Enh 35629517 - RENAME ERROR CODE SPECIFIC TO CUSTOM
#                           PLUGINS
#    araghave    05/29/23 - Bug 35424783 - CREATE SWITCH LIST FILE UNDER
#                           EXACLOUD CONF LOCATION
#    josedelg    04/26/23 - Bug 34989435: Copy 87-podman-bridge.conflist file
#                           used by podman in ol7 to ol8 migration
#    diguma      04/18/23 - Bug 34582467 - new errors for plugins
#    vikasras    21/02/23 - Bug 34882321  - Updated the message incase there
#                           is an active patchmgr session inorder to avoid 
#                           confusion.
#    diguma      02/27/23 - bug 35080646: failed to obtain key api script
#    araghave    02/22/23 - ENH 35105936 - ADD FWVERIFY VALIDATIONS DURING
#                           IBSWITCH PRECHECK
#    araghave    12/05/22 - 34846923 - Startup VMs on the discarded dom0 list
#                           if they are down
#    araghave    12/02/22 - Bug 34709138 - PROVIDE APPROPRIATE ERROR HANDLING
#                           DETAILS IN CASE OF IMAGE VERSION IS NONE
#    bchapman    10/20/22 - Bug 34655355 - GENERATE MORE PRECISE MESSAGES FOR
#                           MVALIDATEIMAGECHECKSUM FAILURES
#    sdevasek    10/19/22 - BUG 34685460 - CONCURRENT PATCHING REQUESTS FAILED
#    sdevasek    10/13/22 - BUG 34632765 - IPTABLES SVC IS NOT STARTED IN POST
#                           PATCHING WHEN ANY OF THE POSTCHECK FAILS
#    araghave    09/29/22 - Enh 34623863 - PERFORM SPACE CHECK VALIDATIONS
#                           BEFORE PATCH OPERATIONS ON TARGET NODES
#    araghave    09/20/22 - Enh 33944615 - IMPLEMENT HEARTBEAT VALIDATION
#                           WITHOUT CELL MARKER DETAILS
#    araghave    06/16/22 - Enh 34138779 - RUN EXACLOUD PLUGIN ON ALL DOMUS
#                           WHICH ARE PROVISIONED AS PART OF MVM ENV
#    sdevasek    06/27/22 - Bug 33213137 - INTRODUCE A SPECIFIC ERROR IF ROCE
#                           SWITCHES EMPTY FROM XML FILE
#    araghave    06/13/22 - Enh 34239188 - ADD ADDITIONAL, GRANULAR ERROR CODES
#                           FOR PLUG-IN FAILURES
#    araghave    05/26/22 - Enh 33951360 - CHECK ROLLBACK VALIDATION FOR CELL 
#                           UPGRADE
#    sdevasek    05/11/22 - ENH 34053202 - INFRAPATCHING PRECHECK TO VALIDATE
#                           THE PRESENCE OF DOM0_IPTABLES_SETUP.SH SCRIPT
#    araghave    04/18/22 - Enh 34053344 - MOVE MOS NOTE DETAILS TO
#                           INFRAPATCHERROR.PY TO APPEAR IN STATUS REPORTING
#                           OUTPUT
#    araghave    04/12/22 - Enh 34048154 - ONEOFF PATCH OPERATION TO SUPPORT A
#                           PLUGIN FRAMEWORK WITH GENERIC OPTIONS
#    sdevasek    03/29/22 - ENH 33453366 CAPTURE PATCHMGR LOG LOCATION WHEN
#                           PATCHMGR IS FAILED
#    araghave    03/02/22 - Enh 33911950 - ADD SMPARTITION VALIDATION BEFORE
#                           AND AFTER IB SWITCH PATCHING IN INFRAPATCH TOOLING
#    nmallego   01/04/22 - ER 33453352 - Add ERROR for system consistency
#    araghave   12/20/21 - ENH 33689675 - ADD NEW ERROR FOR DOMU PATCHMGR
#                          FAILURE AND MARK FAIL AND SHOW
#    araghave   11/24/21 - Enh 33598784 - Move all Infra patching error
#                          codes from error.py to infrapatcherror.py
#    araghave   11/24/21 - Creation
#

from exabox.log.LogMgr import ebLogInfo
from exabox.infrapatching.utils.constants import *

#Error Code Constants

# Dispatcher and Exacloud errors
PATCH_SUCCESS_EXIT_CODE                                     = "0x00000000"
PATCH_OPERATION_FAILED                                      = "0x03010000"
MISSING_PATCH_FILES                                         = "0x03010001"
UNABLE_TO_DOWNLOAD_FROM_OBJECT_STORE                        = "0x03010002"
INFRA_PATCHING_SYSTEM_BUSY_LOCK_NOT_ACQUIRED                = "0x03010003"
INCORRECT_INPUT_JSON                                        = "0x03010004"
PATCH_REQUEST_TIMEOUT                                       = "0x03010005"
MASTER_PATCH_REQUEST_EXCEPTION                              = "0x03010006"
INFRA_PATCHING_ONE_OR_MORE_PATCH_REQUEST_EXCEPTION          = "0x03010007"
MONITOR_EXCEPTION                                           = "0x03010008"
INSUFFICIENT_SPACE_AT_EXACLOUD_THREAD_LOCATION              = "0x03010009"
INDIVIDUAL_PATCH_REQUEST_EXCEPTION                          = "0x0301000A"
MISSING_PATCH_DIRECTORY                                     = "0x0301000B"
INVALID_PATCH_FILES_UNDER_PATCH_STAGE                       = "0x0301000C"
ERROR_DOWNLOAD_FROM_OBJECT_STORE_EXCEPTION                  = "0x0301000D"
MASTER_PATCH_REQUEST_ERROR                                  = "0x0301000E"
PATCH_OPERATION_DID_NOT_START                               = "0x0301000F"
INFRA_PATCHING_TASK_HANDLER_PATCH_REQUEST_EXCEPTION         = "0x03010010"
CRITICAL_HARDWARE_ALERT_DETECTED                            = "0x03010032"
PARALLEL_PATCHING_IB_NON_IB_TARGET_NOT_ALLOWED              = "0x03010033"
EXADATA_INVALID_SLEEP_TIME_FOR_COMPUTES_IN_EXABOX_CONF      = "0x03010034"
INSUFFICIENT_SPACE_ON_PATCH_BASE                            = "0x03010035"
PATCH_UNZIP_ERROR                                           = "0x03010036"
PATCHMGR_SCRIPT_MISSING_ON_LAUNCH_NODE                      = "0x0301003A"
PATCHMGR_SESSION_ALREADY_EXIST                              = "0x0301003B"
PATCH_COPY_ERROR                                            = "0x0301003C"
NO_ACTION_REQUIRED                                          = "0x0301003D"
NO_NODES_AVAILABLE_FOR_PRECHECK                             = "0x0301003E"
PATCHING_NODE_SSH_CHECK_FAILED                              = "0x0301003F"
PASSWDLESS_SSH_CLEANUP_FAILED                               = "0x03010040"
INVALID_DATA_FROM_SHA512SUM_COMMAND                         = "0x03010041"
DOM0_DETAILS_NOT_AVAILABLE                                  = "0x03010042"
SWITCH_PATCH_FILES_MISSING                                  = "0x03010043"
EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR                 = "0x03010044"
PATCHMGR_COMMAND_FAILED                                     = "0x03010045"
INSUFFICIENT_LAUNCH_NODES_AVAILABLE_TO_PATCH                = "0x03010046"
NO_SUITABLE_SYSTEM_IMAGE_FOUND                              = "0x03010047"
INVALID_DATA_FROM_IBSWITCHES_COMMAND                        = "0x03010048"
ROCESWITCH_LIST_FROM_CLUSTER_XML_IS_EMPTY                   = "0x0301004E"
PATCHING_PING_CHECK_FAILED                                  = "0x0301004F"
INSUFFICIENT_SPACE_ON_ROOT_PARTITION                        = "0x03010054"
PATCHING_CONNECT_FAILED                                     = "0x03010055"
UNABLE_TO_GET_INACTIVE_PARTITION_IMAGE_VERSION              = "0x03010056"
EXACLOUD_CONFIG_PATH_MISSING                                = "0x03010058"
SWITCH_LIST_FILE_EMPTY                                      = "0x03010059"
CURRENT_REQUEST_MARKER_NOT_FOUND_IN_PATCH_BASE              = "0x0301005A"
LAUNCH_NODE_PASSED_FOR_PATCH_OPERATION_SHOULD_NOT_BE_TARGET = "0x0301005B"
LAUNCH_NODE_PASSED_FOR_PATCH_OPERATION_SHOULD_NOT_BE_CELL   = "0x0301005C"
PATCH_COPY_AND_IMAGE_CHECKSUM_VALIDATION_EXCEPTION          = "0x0301005D"
PRECHECK_OPERATION_FAILED_ON_COMPUTE_NODES                  = "0x0301005E"
UNABLE_TO_PING_CONNECT_TO_EXTERNAL_LAUNCH_NODE              = "0x0301005F"
MANAGEMENT_SERVER_DOWN_DETECTED                             = "0x03010060"
EXACLOUD_CHILD_REQUEST_CREATION_FAILED                      = "0x03010061"
DOMU_DBAASAPI_COMMAND_FAILED                                = "0x03010062"
PATCH_ZIP_FILE_NOT_FOUND                                    = "0x03010063"
UNABLE_TO_FIND_ELIGIBLE_LAUNCH_NODE                         = "0x03010064"
LAUNCH_NODE_SSH_CHECK_FAILED_KNOWNHOSTS                     = "0x03010065"
IMAGE_INFO_STATUS_EMPTY_OR_INVALID                          = "0x03010066"
SHELL_CMD_EXECUTION_TIMEOUT_ERROR                           = "0x03010067"
EXADATA_PATCHES_CLEANUP_FAILED                              = "0x03010068"
INFRA_PATCHING_IPMI_SERVICESTATE_READ_FAILED                = "0x03010069"
INFRA_PATCHING_IPMI_SERVICESTATE_NOT_ENABLED                = "0x0301006A"
ROLLBACK_PRECHECK_NOT_SUPPORTED                             = "0x0301006B"
SSHD_VALIDATION_ERROR                                       = "0x0301006C"
MISSING_REMOTE_PATCH_BASE_CLEANUP_FAILED                    = "0x0301006D"
INFRA_PATCHING_ELU_IMAGE_VERSION_NOT_FOUND                  = "0x0301006F"
INVALID_TARGET_VERSION                                      = "0x03010071"
ELU_OUTSTANDING_WORK_APPLY_FAILURE                          = "0x03010072"
INSUFFICIENT_SPACE_ON_PATCH_BASE_FOR_SINGLENODE             = "0x03010073"

# Dom0
HEARTBEAT_FAILURE_ERROR                                     = "0x03020000"
DOM0_PRECHECK_EXECUTION_FAILED_ERROR                        = "0x03020001"
DOM0_UNABLE_TO_LOCATE_IPTABLES_SETUP_SCRIPT                 = "0x03020002"

SINGLE_NODE_NAME_MISSING                                    = "0x03030000"
DOM0_NOT_PINGABLE                                           = "0x03030001"
DOM0_IMAGE_NOT_SUCCESS                                      = "0x03030002"
VERSION_MISMATCH_DURING_ROLLBACK                            = "0x03030003"
DOM0_NOT_AT_REQUESTED_VERSION                               = "0x03030004"
DOMU_DOWN_ERROR                                             = "0x03030005"
DB_SERVER_SERVICE_DOWN                                      = "0x03030006"
DOM0_ROLLBACK_FAILED_DONOT_HAVE_DOMU                        = "0x03030007"
DOMU_HEARTBEAT_NOT_RECEIVED                                 = "0x03030008"
DOM0_ROLLBACK_NOT_ALLOWED_ERROR                             = "0x03030009"
CELL_MARKER_MISSING_ERROR                                   = "0x0303000A"
INFRA_PATCHING_DOM0_SERVICES_NOT_RUNNING                    = "0x0303000B"
MISSING_PATCHES                                             = "0x0303000C"
DOM0_ROLLBACK_FAILED_INCONSISTENT_DOM0_DOMU_VERSION         = "0x0303000E"
PATCHMGR_RETRY_EXECUTION_FAILED_ERROR                       = "0x0303000D"
DOM0_PATCHING_FAILED_ERROR                                  = "0x0303000F"
PATCHMGR_EXECUTION_FAILED_ERROR                             = "0x03030010"
POSTCHECKS_FAILED                                           = "0x03030011"
INDIVIDUAL_PATCH_REQUEST_EXCEPTION_ERROR                    = "0x03030012"
PATCH_DOM0_IMAGE_BACKUP_ERROR_EXCEPTION                     = "0x03030013"
DOM0_POST_EXACLOUD_PLUGINS_FAILED                           = "0x03030014"
DOM0_ROLLBACK_FAILED_FOR_FRESH_INSTALL                      = "0x03030015"
DOM0_BACKUP_EXECUTION_FAILED_ERROR                          = "0x03030016"
DOM0_PRECHECK_FAILED_DONOT_HAVE_DOMU                        = "0x03030017"
DOM0_PATCH_FAILED_DONOT_HAVE_DOMU                           = "0x03030018"
DOM0_FAILED_TO_SHUTDOWN_VMS                                 = "0x03030019"
DOM0_STALE_MOUNT_CHECK_FAILED                               = "0x0303001A"
DOMU_AUTO_STARTUP_FILE_MISSING_ERROR                        = "0x0303001B"
DOMU_AUTO_STARTUP_ONREBOOT_PARAMETER_SET_INCORRECT          = "0x0303001C"
DOM0_VIF_BRIDGE_RECREATION_FAILED                           = "0x0303001D"
DOM0_SYSTEM_CONSISTENCY_CHECK_FAILED                        = "0x0303001E"
PATCHMGR_PRECHECK_EXECUTION_FAILED_ERROR                    = "0x0303001F"
DOM0_EXECUTE_IPTABLES_SETUP_SCRIPT_FAILED                   = "0x03030020"
UNABLE_TO_STARTUP_VM_ON_DOM0                                = "0x03030021"
DOMU_CRS_VALIDATION_EXCEPTION_ENCOUNTERED                   = "0x03030022"
DOMU_RDS_PING_FAILED                                        = "0x03030023"
DOMU_INVALID_CRS_HOME                                       = "0x03030024"
NO_PATCHMGR_RESPONSE_DETECTED                               = "0x03030025"
NO_PATCHMGR_RESPONSE_DETECTED_ON_DOMU                       = "0x03030026"
CRS_IS_DISABLED                                             = "0x03030027"
CRS_COMMAND_EXCEPTION_ENCOUNTERED                           = "0x03030028"
DB_HEALTCHECKS_DETECTION_TIMEOUT_ERROR                      = "0x03030029"
DB_HEALTCHECKS_DETECTION_EXCEPTION_ENCOUNTERED              = "0x0303002A"
DOM0_PATCHING_DB_HEALTHCHECKS_CRS_RESOURCES_ARE_DOWN        = "0x0303002B"
DOM0_PATCHING_DB_HEALTHCHECKS_PDB_IN_DEGRADED_STATE         = "0x0303002C"
DOM0_PATCHING_DB_HEALTHCHECKS_VM_OS_REBOOT_WILL_CAUSE_DOWNTIME  = "0x0303002D"
DOM0_PATCHING_DB_HEALTHCHECKS_CRS_SERVICES_DOWN             = "0x0303002E"
DOM0_PATCHING_DB_HEALTHCHECKS_PDB_FETCH_DETAILS_ERROR       = "0x0303002F"
NODE_LIST_NOT_SPECIFIED                                     = "0x03030030"
OPERATION_NOT_SPECIFIED                                     = "0x03030031"
TARGET_VERSION_NOT_SPECIFIED                                = "0x03030032"
JSON_CONF_FILE_NOT_SPECIFIED                                = "0x03030033"
PATCH_ZIP_FILE_NOT_FOUND                                    = "0x03030034"
UNABLE_TO_FIND_ELIGIBLE_LAUNCH_NODE                         = "0x03030035"

# Cells

CELL_POSTCHECK_EXCEPTION                                    = "0x03060000"
CELL_PRECHECK_EXCEPTION                                     = "0x03060001"
CELL_ROLLBACK_PRECHECK_EXCEPTION                            = "0x03060002"

PATCH_CELL_CLEANUP_FAILED                                   = "0x03070000"
CELL_ROLLBACK_EXECUTION_STOPPED                             = "0x03070001"
CELL_ROLLBACK_EXCEPTION                                     = "0x03070002"
PATCHMGR_CONSOLE_LOG_MISSING                                = "0x03070003"
CELL_PATCH_EXCEPTION                                        = "0x03070004"
CELL_PATCH_FAILED                                           = "0x03070005"
CELL_PING_FAILED                                            = "0x03070006"
CELL_PATCH_FILES_MISSING                                    = "0x03070007"
CELL_SERVICES_NOT_RUNNING                                   = "0x03070008"
CELL_CURRENT_VERSION_EXPECTED_HIGHER_THAN_ORIGINAL_VERSION  = "0x03070009"
CELL_CURRENT_VERSION_EXPECTED_LOWER_THAN_ORIGINAL_VERSION   = "0x0307000A"
CELL_CURRENT_VERSION_EXPECTED_EQUAL_TO_ORIGINAL_VERSION     = "0x0307000B"
CELL_IMAGE_STATUS_NOT_SUCCESSFUL                            = "0x0307000C"
CELL_ASM_MODE_STATUS_SYNCING_ERROR                          = "0x0307000D"
CELL_ASM_MODE_STATUS_UNUSED_ERROR                           = "0x0307000E"
CELL_FAILED_TO_SHUTDOWN_VMS                                 = "0x0307000F"
CELL_FAILED_TO_BRINGUP_VMS                                  = "0x03070010"
CELL_ASM_MODE_STATUS_OFFLINE_ERROR                          = "0x03070011"
CELL_ASM_MODE_STATUS_STILL_ONLINE_ERROR                     = "0x03070012"
CELL_NOT_ELIGIBLE_FOR_ROLLBACK                              = "0x03070013"
DBMCLI_COMMAND_EXECUTION_FAILED                             = "0x03070014"

# Switch

SWITCH_POSTCHECK_FAILED                                     = "0x03080000"
SWITCH_ROLLBACK_PRECHECK_FAILED                             = "0x03080001"
SWITCH_PATCH_PRECHECK_FAILED                                = "0x03080002"
SWITCH_PING_CHECK_FAILED                                    = "0x03080003"
SWITCH_SM_STATE_MISMATCH_ERROR                              = "0x03080004"
SWITCH_IBSWITCH_PARTITIONS_MISMTACH_ERROR                   = "0x03080005"
SWITCH_NTP_CHECK_FAILED                                     = "0x03080006"
SWITCH_SM_PARTITION_CONFIGURATION_ERROR                     = "0x03080007"
FWVERIFY_COMMAND_FAILED_ON_IBSWITCHES                       = "0x03080008"

SWITCH_CURRENT_VERSION_SHOULD_BE_LOWER_THAN_ORIGINAL_VER    = "0x03090000"
SWITCH_PATCH_FAILED                                         = "0x03090001"
SWITCH_ROLLBACK_FAILED                                      = "0x03090002"
SWITCH_PATCH_OPERATION_FAILED                               = "0x03090003"
SWITCH_CURRENT_VERSION_EXPECTED_HIGHER_THAN_ORIGINAL_VER    = "0x03090004"

# ASM and DB

CELL_ASMDEACTIVATION_OUTCOME_ERROR                          = "0x030C0000"

# ONEOFF and ONEOFFV2

ONEOFF_APPLY_FAILED                                         = "0x030D0000"
ONEOFF_PATCHES_MISSING                                      = "0x030D0001"
PARENT_PLUGINS_MISSING                                      = "0x030D0002"
ONEOFF_PATCH_COPY_FAILED                                    = "0x030D0008"
ONEOFF_PATCH_CLEANUP_FAILED                                 = "0x030D0009"
NODE_DID_NOT_STARTUP_POST_ONEOFF_PLUGINS                    = "0x030D000F"
ONEOFFV2_APPLY_FAILED                                       = "0x030D0010"   
ONEOFFV2_PATCH_COPY_FAILED                                  = "0x030D0011"
ONEOFFV2_PATCHES_MISSING                                    = "0x030D0012"
ONEOFFV2_EXCEPTION_ENCOUNTERED                              = "0x030D0013"
ONEOFF_PATCH_CLEANUP_DOMU_FAILED                            = "0x030D0014"
ONEOFF_DOMU_APPLY_FAILED                                    = "0x030D0015"
ONEOFF_DOMU_PATCH_COPY_FAILED                               = "0x030D0016"
ONEOFF_DOMU_PATCHES_MISSING                                 = "0x030D0017"
ONEOFFV2_PLUGIN_SCRIPT_BUNDLE_MISSING                       = "0x030D0018"
ONEOFFV2_PLUGIN_SCRIPT_BUNDLE_HASH_MISMATCH                 = "0x030D0019"
ONEOFFV2_PLUGIN_SCRIPT_VALIDATION_EXCEPTION                 = "0x030D001A"

# DomU

DOMU_PRECHECK_EXECUTION_FAILED                              = "0x03040000"
DOMU_PRECHECK_REQUEST_EXCEPTION                             = "0x03040001"
DOMU_POSTCHECK_REQUEST_EXCEPTION                            = "0x03040002"
DOMU_BACKUP_EXECUTION_FAILED_ERROR                          = "0x03040003"

EXACLOUD_PLUGIN_RUN_FAILED_DOMU                             = "0x03050000"
DOMU_CRITICAL_SERVICES_NOT_RUNNING                          = "0x03050001"
DOMU_PATCHMGR_UPGRADE_EXECUTION_FAILED                      = "0x03050002"
DOMU_PATCH_REQUEST_EXCEPTION                                = "0x03050003"
DOMU_PATCHMGR_ROLLBACK_EXECUTION_FAILED                     = "0x03050004"
DOMU_ROLLBACK_FAILED_FOR_FRESH_INSTALL                      = "0x03050005"
DOMU_PATCHMGR_BACKUP_EXECUTION_FAILED                       = "0x03050006"
DOMU_BACKUP_REQUEST_EXCEPTION                               = "0x03050007"
UNABLE_TO_SET_SYSTEM_ATTRIBUTES_ATP_ENV                     = "0x03050008"
PATCH_DOMU_RETRY_FAILED                                     = "0x03050009"
POST_PLUGIN_FAILED_DOMU                                     = "0x0305000A"
DOMU_DID_NOT_STARTUP_POST_PATCH                             = "0x0305000B"
DOMU_IMAGE_STATUS_FAILED                                    = "0x0305000C"
DOMU_VERSION_LOWER_THAN_EXPECTED_VERSION                    = "0x0305000D"
DOMU_VERSION_NOT_AT_EXPECTED_VERSION                        = "0x0305000E"
DOMU_CRS_SERVICES_DOWN                                      = "0x0305000F"
PRE_PLUGIN_FAILED_DOMU                                      = "0x03050010"
DOMU_STALE_MOUNT_CHECK_FAILED                               = "0x03050011"
DOMU_SYSTEM_CONSISTENCY_CHECK_FAILED                        = "0x03050012"
DOMU_PRECHECK_EXECUTION_FAILED_ERROR                        = "0x03050013"
PATCH_DOMU_IMAGE_BACKUP_ERROR_EXCEPTION                     = "0x03050014"
PATCHMGR_DOMU_SESSION_ALREADY_EXIST                         = "0x03050015"
INSUFFICIENT_LAUNCH_NODES_AVAILABLE_TO_PATCH_ON_DOMU        = "0x03050016"
DOMU_PATCHMGR_COMMAND_FAILED                                = "0x03050017"
FAILURE_IN_READING_PRE_PLUGIN_STATE                         = "0x03050018"
DOMU_HEARTBEAT_VALIDATION_EXCEPTION_ENCOUNTERED             = "0x03050019"
DOMU_ENCRYPT_KEY_API_FAILED                                 = "0x0305001A"
DOMU_CRS_RESOURCES_ARE_DOWN                                 = "0x0305001B"
PDB_FETCH_DETAILS_ERROR                                     = "0x0305001C"
PDB_IN_DEGRADED_STATE                                       = "0x0305001D"
VM_OS_PATCH_WILL_CAUSE_DOWNTIME                             = "0x0305001E"

DBNUPLUGIN_COPY_ERROR                                       = "0x030A0000"
EXACLOUD_DOM0_PLUGIN_EXECUTION_FAILED                       = "0x030A0001"
EXACLOUD_PLUGIN_SCRIPT_BUNDLE_MISSING                       = "0x030A0002"
EXACLOUD_PLUGIN_SCRIPT_BUNDLE_HASH_MISMATCH                 = "0x030A0003"
EXACLOUD_PLUGIN_SCRIPT_VALIDATION_EXCEPTION                 = "0x030A0004"
						            
EXACLOUD_PLUGINS_DIRECTORY_MISSING                          = "0x030B0000"
EXACLOUD_PARENT_PLUGINS_MISSING                             = "0x030B0001"
EXACLOUD_PLUGIN_GENERIC_DOM0_EXCEPTION_ERROR                = "0x030B0002"
EXACLOUD_CUSTOM_PLUGIN_SCRIPT_EXECUTION_FAILED              = "0x030B0003"
EXACLOUD_PARENT_PLUGIN_FILES_MISSING_ON_DOM0                = "0x030B0004"
EXACLOUD_PARENT_PLUGIN_FILES_MISSING_ON_DOMU                = "0x030B0005"
EXACLOUD_PLUGIN_GENERIC_DOMU_EXCEPTION_ERROR                = "0x030B0006"
EXACLOUD_PLUGIN_COPY_DOM0_EXCEPTION_ERROR                   = "0x030B0007"
EXACLOUD_PLUGIN_COPY_DOMU_EXCEPTION_ERROR                   = "0x030B0008"
EXACLOUD_PLUGIN_EXECUTION_DOM0_EXCEPTION_ERROR              = "0x030B0009"
EXACLOUD_PLUGIN_EXECUTION_DOMU_EXCEPTION_ERROR              = "0x030B000A"
EXACLOUD_PLUGIN_MISSING_DOM0_EXCEPTION_ERROR                = "0x030B000B"
EXACLOUD_PLUGIN_MISSING_DOMU_EXCEPTION_ERROR                = "0x030B000C"
EXACLOUD_PLUGIN_APPLY_DOM0_EXCEPTION_ERROR                  = "0x030B000D"
EXACLOUD_PLUGIN_APPLY_DOMU_EXCEPTION_ERROR                  = "0x030B000E"
EXACLOUD_PLUGIN_CONSOLE_LOG_READ_DOM0_EXCEPTION_ERROR       = "0x030B000F"
EXACLOUD_PLUGIN_CONSOLE_LOG_READ_DOMU_EXCEPTION_ERROR       = "0x030B0010"	
EXACLOUD_PLUGIN_MISSING_CUSTOM_PLUGIN_SCRIPT                = "0x030B0011"
DOM0_EXACLOUD_METADATA_BASED_PLUGIN_EXECUTION_FAILED        = "0x030B0012"
DOMU_EXACLOUD_METADATA_BASED_PLUGIN_EXECUTION_FAILED        = "0x030B0013"
CELL_EXACLOUD_METADATA_BASED_PLUGIN_EXECUTION_FAILED        = "0x030B0014"
EXACLOUD_PLUGIN_COPY_CELL_EXCEPTION_ERROR                   = "0x030B0015"
EXACLOUD_PLUGIN_MISSING_CELL_EXCEPTION_ERROR                = "0x030B0016"
EXACLOUD_PLUGIN_APPLY_CELL_EXCEPTION_ERROR                  = "0x030B0017"
EXACLOUD_CUSTOM_PLUGIN_CONSOLE_READ_TIMEOUT_DOM0_ERROR      = "0x030B0018"
EXACLOUD_CUSTOM_PLUGIN_CONSOLE_READ_TIMEOUT_DOMU_ERROR      = "0x030B0019"

#CPS OS PATCHING                                            
						            
STANDBY_NODE_EMPTY                                          = "0x030F0000"
INVALID_ADDITIONAL_OPTION                                   = "0x030F0001"
INVALID_PATCH_OPTION                                        = "0x030F0002"
INVALID_MASTER_NODE_DETAILS                                 = "0x030F0003"
CPS_TASK_FAILED                                             = "0x030F0004"
PATCHMGR_READ_CONSOLE_ERROR                                 = "0x030F0005"
CPS_PATCH_EXCEPTION                                         = "0x030F0006"
TARGET_VERSION_SAME_NO_ACTION_REQUIRED                      = "0x030F0007"
INSUFFICIENT_SPACE_ON_PRIMARY_NODE                          = "0x03100000"
INSUFFICIENT_SPACE_TO_STAGE_PATCHES                         = "0x03100001"
CPS_PATCH_PREREQ_CHECK_FAILED                               = "0x03100002"
CPS_HARDWARE_ALERT_DETECTED                                 = "0x03110000"
TARGET_VERSION_EMPTY                                        = "0x03110001"
INVALID_NODE_TO_RUN_DBMCLI                                  = "0x03110002"
PATCHMGR_SESSION_ACTIVE                                     = "0x03110003"
DBSERVERD_SERVICE_DOWN                                      = "0x03110004"
TARGET_INPUT_VERSION_MATCH                                  = "0x03110005"
CPS_PATCH_OPERATION_FAILED                                  = "0x03110006"
UNABLE_TO_PARSE_PATCH_VERSION                               = "0x03110007"
CPS_RPM_DATABASE_CORRUPTED                                  = "0x03110008"
CPS_SYSTEM_CONSISTENCY_CHECK_FAILED                         = "0x03110009"
CPS_ROLLBACK_FAILED                                         = "0x03120000"
ROLLBACK_CANNOT_BE_PERFORMED                                = "0x03120001"
IMAGE_VERSION_EMPTY_OR_INVALID                              = "0x03120002"
ACTIVE_INACTIVE_PARTITION_VERSION_MATCH                     = "0x03120003"
CPS_SWITCHOVER_FAILED                                       = "0x03130000"
CPS_SWITCHOVER_STATUS_FAILED                                = "0x03130001"
CPS_POSTCHECK_FAILED                                        = "0x03140000"
CPS_OS_PODMAN_CONFIG_FAILED                                 = "0x03140002"
CPS_BACKUP_FAILED                                           = "0x03150000"

#Error Actions as defined in ECRA. Please define the exact same way here as well so that it matches ECRA one to one
#FAIL_AND_SHOW, FAIL_DONTSHOW_PAGE_ONCALL, RETRY_WITH_SAME_TOKEN,RETRY_WITH_DIFFERENT_TOKEN,RETRY_WF_TASK,UNDO_AND_RETRY_WF_TASK
# Error code ranges 

gPatchGenericError = {
    "0x00000000" : ('Patch operation Status successful, no further action required.', ''),
    "0x03010000" : ('Patch operation Status failed', 'FAIL_DONTSHOW_PAGE_ONCALL'),
    "0x03010001" : ("Required patch files not found",'FAIL_DONTSHOW_PAGE_ONCALL'),
    "0x03010002" : ("Unable to download files from object store",'FAIL_DONTSHOW_PAGE_ONCALL'),
    "0x03010003" : ("System is busy. Please retry the operation after some time.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010004" : ("Could not parse DBCS json input correctly. Please verify your input json","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010005" : ("Patch request timed-out - Check individual requests","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010006" : ("Master patch request exception detected","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010007" : ("One ore more individual patch requests failed","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010008" : ("Patch monitor exception detected","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010009" : ("Insufficient disk space to store thread logs, disk space needs to be cleared before infra patching is started","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301000A" : ("Individual patch request exception detected","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301000B" : ("Missing patch directory on staging node.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301000C" : ("Invalid number of files staged under patch stage location.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301000D" : ("Error downloading patch from stage location.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301000E" : ("Master request patch error detected.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301000F" : ("Patch operation did not start","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010010" : ("Task handler patch request exception detected.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010032" : ("Detected Critical Hardware alert on specified Target.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010033" : ("In a shared IBFabric environment, combination of an IBSwitch/Non-IBSwitch target patch cannot be run in parallel","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010034" : ("Invalid sleep time specified which is less than zero or more than the maximum limit.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010035" : ("Insufficient space on the target node patch base location.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010036" : ("Unable to unzip patches on the launch node, patching will be skipped.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301003A" : ("Unable to locate patchmgr script on the launch node.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301003B" : ("Patchmgr session already exists.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301003C" : ("Unable to copy patches on to target nodes.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301003E" : ("No nodes available to run precheck","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301003F" : ("Ssh connectivity check failed during patching.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010040" : ("Passwdless ssh cleanup failed, cleanup passwdless ssh for security compliance.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010041" : ("Command : (sha512sum returned invalid data on dom0 launch node.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010042" : ("Unable to fetch dom0 details.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010043" : ("Patch files were not provided at initialization for patch operations.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010044" : ("Exadata Infra patching Timeout occurred, Could not validate patch operation completion on launch node.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010045" : ("patchmgr command failed with non-zero status.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010046" : ("At least one launch node is required to perform patch operation.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010048" : ("Command : (ibswitches returned invalid data on dom0 launch node.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301004E" : ("RocE Switch list from cluster XML is empty.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301004F" : ("Node is not pingable. Validate connectivity before retrying infra patch operations.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010054" : ("Insufficient space available on root partition during patch operation.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010055" : ("Node connect failed. Validate connectivity and authentication before retrying infra patch operations.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010056" : ("Unable to get image version details during target version validation for inactive partition.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010058" : ("Exacloud home config location does not exist.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010059" : ("Switch List file is empty and hence unable to acquire lock to proceed with patching.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301005A" : ("Current infrapatching operation marker is not found in patch base directory.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301005B" : ("Launch node passed should not be one of the target nodes to be patched.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301005C" : ("Launch node passed should not be a cell node.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301005D" : ("Patch copy and image checksum validation exception detected.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301005E" : ("Precheck operation failed on compute nodes.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301005F" : ("Unable to ping or connect to external launch nodes", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010060" : ("Management Server down.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010061" : ("Patching child request to Exacloud is not created due to the absence of cluster details introduced by some fabric changes.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010062" : ("Execution of DBAASAPI command to fetch infra sanity check details failed.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010063" : ("Unable to find zip file on ecra host, patching will be skipped.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010064" : ("Unable to find eligible launchnode for patching.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010065" : ("ssh connectivity check failed due to host validation failure","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010066" : ("Image information status is either empty or invalid. The patch operation is not possible.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010067" : ("Command timed out before it completed.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010068" : ("Exadata patches cleanup failed","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010069" : ("Unable to read ipmi servicestate in ilom.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301006A" : ("Unable to set the ipmi servicestate in ilom to enabled state.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301006B" : ("Rollback precheck is not supported for Dom0 and/or DomU.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301006C" : ("Error occurred while validating sshd is running or not on remote nodes.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301006D" : ("Unable to verify and cleanup missing patchmgr remote patch base.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0301006F" : ("Exadata Live Update Image version not found for the DOM0.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010071" : ("Target version passed is invalid and infra patch operations will be marked failure for the current node.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03010072" : ("Apply outstanding work items not applied after an elu upgrade with applypending was performed.", "FAIL_AND_SHOW"),
    "0x03010073" : ("Insufficient space on the Remote node patch base location for single node patching.", "FAIL_DONTSHOW_PAGE_ONCALL")
}

#All Generic Errors are FAIL_DONTSHOW_PAGE_ONCALL for infra targets. However, for Domu , some generic errors are FAIL_AND_SHOW as defined in the list below
#Based on Ops dicussion on Nov 7 2023 and email reference with
#Subject "MOM - RE: Exacs - DomU OS Prechecks getting stuck in Production - errorAction List for Domu Generic Errors"
gDomUGenericErrorAsFailAndShow = ["0x03010005", "0x03010032", "0x03010035", "0x03010036", "0x0301003A", "0x03010040", "0x03010041", "0x03010045", "0x03010046", "0x0301004F", "0x03010054", "0x03010055", "0x03010056"]

gPrecheckDom0Error = {
    "0x03020000" : ("Unable to establish Heartbeat on the cells. Not all CRS/DB services are up on DomU.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03020001" : ("Patchmgr precheck command failed with errors.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03020002" : ("Unable to locate dom0_iptables_setup.sh file on the dom0 node.","FAIL_DONTSHOW_PAGE_ONCALL")
}

gPatchDom0Error = {
    "0x03030000"  : ("Node name missing to perform single node upgrade. Provide appropriate inputs and re-run patch.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030001"  : ("Dom0 did not come back online (not ping-able or ssh-able) post patch","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030002"  : ("Post-patch check: Dom0 image is not seen as success via imageinfo command","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030003"  : ("Dom0 rollback was requested but the version seems to be unchanged","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030004"  : ("Dom0 is not at the requested upgrade, cannot proceed further.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030005"  : ("Expected all of the following domus to be up. But one or more DomU are still down.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030006"  : ("DB services were not up on dom0","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030007"  : ("DomUs are not running on dom0 while dom0 rollback requested","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030008"  : ("Unable to establish Heartbeat on the cells. Not all CRS/DB services are up on DomU.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030009"  : ("Changes detected done to the DOMU after last DOM0 upgrade. Rollback of DOM0 not allowed.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0303000A"  : ("No Cell marker found in alert log to validate heartbeat checks","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0303000B"  : ("Required services are not running on the upgraded node","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0303000C"  : ("Unable to locate patch stage location in OCI EXACC environment.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0303000D"  : ("Patchmgr retry operation failed with errors.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0303000E"  : ("Dom0 Rollback not allowed in this scenario due to inconsistency in Dom0/DomU version.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0303000F"  : ("Dom0 Patching failed due to errors.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030010"  : ("Patchmgr execution failed - See patchmgr logs","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030011"  : ("Basic patch postchecks failed - See output commands","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030012"  : ("Individual patch request exception detected","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030013"  : ("Patchmgr image backup exception.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030014"  : ("Exacloud plugins failed post Infra patch operation.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030015"  : ("Rollback cannot be performed on a newly provisioned Dom0.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030016"  : ("Patchmgr backup command failed with errors.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030017"  : ("DomUs are not running on dom0 while dom0 precheck requested","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030018"  : ("DomUs are not running on dom0 while dom0 patch requested","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030019"  : ("Failed to shutdown VMs during dom0 upgrade.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0303001A"  : ("Stale mount(s) detected on Dom0","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0303001B"  : ("Auto startup soft link missing for the DomU running on the current Dom0. Re-create soft link, verify if on-reboot in vm.cfg is set to restart and retry patch.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0303001C"  : ("The properties 'on_reboot' in vm.cfg on particular domU is not set to 'restart' and due to which domU will not startup after dom0 reboot.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0303001D"  : ("VIF bridge symlinks re-creation failed","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0303001E"  : ("System is in partially updated state on Dom0. Image backup cannot be performed.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0303001F"  : ("Infra patching image backup command on Dom0 failed with errors.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030020"  : ("Error occurred when executing dom0_iptables_setup.sh on the dom0 node.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030021"  : ("Unable to startup Guest VMs as part of upgrade/rollback operation.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030022"  : ("Exception encountered while validating and starting up CRS services on DomU.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030023"  : ("Unable to establish Heartbeat with the cells since rds-ping to validate VM to VM and VM to cell connectivity failed on DomU.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030024"  : ("Invalid CRS HOME on DomU.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030025"  : ("No patchmgr response detected on the current target.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030026"  : ("No patchmgr response detected on DomU.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030027"  : ("CRS is disabled on DomU and further crs validations will be skipped.", "FAIL_AND_SHOW"),
    "0x03030028"  : ("Exception encountered while running crs commands.", "FAIL_AND_SHOW"),
    "0x03030029": ("Timeout occurred while executing DB healthcheck commands.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0303002A": ("Exception occurred while executing DB healthcheck commands.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0303002B": ("DB healthchecks have detected that one or more Clusterware resources (like database, service or listener) are down on VM(s).", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0303002C": ("DB healthchecks have detected degraded state in the PDB(s).", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0303002D": ("DB healthchecks have detected that patching will lead to outage for one or more pdbs due to the reboot of VMs.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0303002E": ("DB healthchecks have detected that CRS services down on VM(s).", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0303002F": ("Error occurred while reading and validating PDB metadata to detect if PDBs are in a degraded state.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030030": ("Node List Not Specified for ExaCompute Patching.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030031": ("ExaCompute Operation not specified.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030032": ("ExaCompute Target Version not specified.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030033": ("ExaCompute Json Configuration File not specified.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030034": ("Exacompute patch zip file not found.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03030035": ("Unable to find eligible launch node on the Exacompute environment.", "FAIL_DONTSHOW_PAGE_ONCALL")
}

gPrecheckDomuError = {
    "0x03040000" : ("Patchmgr precheck on VM failed.","FAIL_AND_SHOW"),
    "0x03040001" : ("Exception detected during VM OS precheck operation.","FAIL_AND_SHOW"),
    "0x03040002" : ("Exception detected during VM OS postcheck operation.","FAIL_AND_SHOW"),
    "0x03040003" : ("Infra patching image backup command on VM failed with errors. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW")
}

gPatchDomuError = {
    "0x03050000" : ("Exacloud plugin run on VM failed.","FAIL_AND_SHOW"),
    "0x03050001" : ("Critical services on VM down. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x03050002" : ("Infra patching upgrade command on VM failed with errors.","FAIL_AND_SHOW"),
    "0x03050003" : ("Exception detected during VM OS patch operation.","FAIL_AND_SHOW"),
    "0x03050004" : ("VM rollback exception detected.","FAIL_AND_SHOW"),
    "0x03050005" : ("Rollback cannot be performed on a newly provisioned VM. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x03050006" : ("Infra patching image backup command on VM failed with errors.","FAIL_AND_SHOW"),
    "0x03050007" : ("VM backup request exception detected.","FAIL_AND_SHOW"),
    "0x03050008" : ("Unable to set system attributes, specific to ADB-CC environments during VM Patch operation. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x03050009" : ("VM patch retry failed. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x0305000A" : ("Plugin run post patch operation on VM failed. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x0305000B" : ("VM startup failed post patching activity. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x0305000C" : ("VM image status failed. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x0305000D" : ("VM current version lower than expected version.","FAIL_AND_SHOW"),
    "0x0305000E" : ("VM version not at the expected version.","FAIL_AND_SHOW"),
    "0x0305000F" : ("CRS services down on VM. Refer MOS Note 2829056.1 for more details.","FAIL_DONTSHOW_PAGE_ONCALL"), #CRS check failed on domu during dom0 patching hence FAIL_DONTSHOW_PAGE_ONCALL
    "0x03050010" : ("Plugin run during pre patch operation on VM failed. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x03050011" : ("Stale mount(s) detected on VM. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x03050012" : ("System is in partially updated state on VM. Image backup cannot be performed. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x03050013" : ("VM OS patching precheck command failed. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x03050014" : ("VM OS patching image backup command exception encountered. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x03050015" : ("Patchmgr session on VM already exists. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x03050016" : ("Insufficient launch nodes(VM) found on the environment to patch. There must be one launch node apart from the target node for patching to operate. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x03050017" : ("Patchmgr command on VM failed. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x03050018" : ("Invalid patch state found during non-rolling patch on launch Node VM.","FAIL_AND_SHOW"),
    "0x03050019" : ("Exception encountered while validating DomU heartbeat on cells.","FAIL_DONTSHOW_PAGE_ONCALL"), #HB check failed on domu during dom0 patching hence FAIL_DONTSHOW_PAGE_ONCALL
    "0x0305001A" : ("Error locating the encryption key api script.","FAIL_AND_SHOW"),
    "0x0305001B" : ("One or more Clusterware resources (like database, service or listener) are down on VM.", "FAIL_AND_SHOW"),
    "0x0305001C" : ("Error occurred while reading and validating PDB metadata to detect if PDB is in a degraded state.", "FAIL_AND_SHOW"),
    "0x0305001D" : ("PDB is in a degraded state.", "FAIL_AND_SHOW"),
    "0x0305001E": ("VM OS patch will lead to outage for PDB.", "FAIL_AND_SHOW")
}

gPrecheckCellError = {
    "0x03060000"  : ("Individual Cell patch postcheck request exception detected.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03060001"  : ("Individual Cell patch prereq check request exception detected.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03060002"  : ("Individual Cell patch rollback precheck request exception detected.","FAIL_DONTSHOW_PAGE_ONCALL")
}

# Error codes for cell patch, rollback
gPatchCellError = {
    "0x03070000"  : ("Patchmgr cleanup on cells failed.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03070001"  : ("Cell Rollback execution stopped.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03070002"  : ("Individual Cell rollback request exception detected.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03070003"  : ("Patchmgr console output log missing, unable to read patch status.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03070004"  : ("Individual Cell patch request exception detected.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03070005"  : ("Cell patch execution failed.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03070006"  : ("Ping to cell nodes from exacloud host failed.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03070007"  : ("Cell patch files missing.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03070008"  : ("Critical cell services not running.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03070009"  : ("Current version on the cell is expected to be higher than that of Patch target version.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0307000A"  : ("Current version on the cell is expected to be lower than that of Patch target version.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0307000B"  : ("Current version on the cell is expected to be equal to original version.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0307000C"  : ("Cell Image Status not successful.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0307000D"  : ("ASM mode status of griddisks on cell servers are in Syncing state. Refer MOS Note 2829056.1 for more details.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0307000E"  : ("ASM mode status of griddisks on cell servers are in Unused state. Refer MOS Note 2829056.1 for more details.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x0307000F"  : ("Failed to shutdown VMs during cell upgrade.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03070010"  : ("Failed to bring up VMs during cell upgrade.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03070011"  : ("ASM mode status of griddisks on cell servers are in Offline state. Refer MOS Note 2829056.1 for more details.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03070012"  : ("ASM mode status of griddisks on cell servers are in Online state. Cannot do non-rolling upgrade with this state. Refer MOS Note 2829056.1 for more details.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03070013"  : ("Rollback is not possible on cell due to error encountered : Rollback to the inactive partitions: Impossible.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03070014"  : ("Error executing DBMCLI command on the Dom0 node, resulting in services not starting or stopping correctly during the patching process.","FAIL_DONTSHOW_PAGE_ONCALL")
}

gPrecheckSwitchError = {
    "0x03080000"  : ("Basic switch postchecks failed.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03080001"  : ("Switch Rollback precheck failed.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03080002"  : ("Switch Patch precheck failed.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03080003"  : ("ping check on Switches failed.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03080004"  : ("SM state for the switch is not same as before the upgrade/downgrade.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03080005"  : ("Output from commands changed after upgrade or rollback: (1) smnodes list (2) smpartition list active no-page.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03080006"  : ("No NTP synchronization found for NTP Servers on the IBSwitches","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03080007"  : ("IBSwitch smpartitioning is not configured appropriately.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03080008"  : ("Fwverify command validation on IBSwitches failed.","FAIL_DONTSHOW_PAGE_ONCALL")
}

# Error codes for switch patch, rollback
gPatchSwitchError = {
    "0x03090000"  : ("Current version on the switch is expected to be lower than that of Patch target version.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03090001"  : ("Switch patchmgr command failed.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03090002"  : ("Switch Rollback failed","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03090003"  : ("Switch patch operation failed.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x03090004"  : ("Current version on the switch is expected to be higher than that of Patch target version.","FAIL_DONTSHOW_PAGE_ONCALL")
}

# Plugin Specific Error codes.
gDom0PatchPluginError = {
    "0x030A0000" : ("Failed to copy dbnu plugins to target nodes.","FAIL_AND_SHOW"),
    "0x030A0001" : ("Execution of plugin script for Dom0 target failed.","FAIL_AND_SHOW"),
    "0x030A0002":  ("Exacloud plugin script bundle is missing.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030A0003":  ("SHA256 sum mismatch for Exacloud plugin script bundle.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030A0004":  ("An error occurred while validating the Exacloud plugin script bundle.", "FAIL_DONTSHOW_PAGE_ONCALL")
}

# Error code for DomU plugin errors
gDomUPatchPluginError = {
    "0x030B0000" : ("Exacloud plugin directory missing.","FAIL_AND_SHOW"),
    "0x030B0001" : ("Exacloud parent plugin files missing.","FAIL_AND_SHOW"),
    "0x030B0002" : ("Exacloud plugin exception error encountered on Dom0.","FAIL_AND_SHOW"),
    "0x030B0003" : ("Execution of custom plugin script for Guest VM failed. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x030B0004" : ("Exacloud parent plugin files on Dom0 target stage location are missing.","FAIL_AND_SHOW"),
    "0x030B0005" : ("Exacloud parent plugin files on Guest VM stage location are missing. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x030B0006" : ("Exacloud plugin exception error encountered on DomU. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x030B0007" : ("Exacloud plugin file copy error exception encountered on Dom0.","FAIL_AND_SHOW"),
    "0x030B0008" : ("Exacloud plugin file copy error exception encountered on DomU. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x030B0009" : ("Exacloud plugin execution error exception encountered on Dom0.","FAIL_AND_SHOW"),
    "0x030B000A" : ("Exacloud plugin execution error exception encountered on DomU. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x030B000B" : ("Exacloud plugin file missing error exception encountered on Dom0.","FAIL_AND_SHOW"),
    "0x030B000C" : ("Exacloud plugin file missing error exception encountered on DomU. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x030B000D" : ("Exacloud plugin Apply error exception encountered on Dom0.","FAIL_AND_SHOW"),
    "0x030B000E" : ("Exacloud plugin Apply error exception encountered on DomU. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x030B000F" : ("Exception encountered while reading plugin console logs on Dom0.","FAIL_AND_SHOW"),
    "0x030B0010" : ("Exception encountered while reading plugin console logs on DomU. Refer MOS Note 2829056.1 for more details.","FAIL_AND_SHOW"),
    "0x030B0011" : ("Custom plugin script missing.","FAIL_AND_SHOW"),
    "0x030B0012" : ("Plugin metadata based exacloud plugin execution failed on dom0 target.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030B0013" : ("Plugin metadata based exacloud plugin execution failed on domu target.","FAIL_AND_SHOW"),
    "0x030B0014" : ("Plugin metadata based exacloud plugin execution failed on cell target.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030B0015" : ("Exacloud plugin file copy error exception encountered on cell target.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030B0016" : ("Exacloud plugin file missing error exception encountered on cell target.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030B0017" : ("Exacloud plugin Apply error exception encountered on Cell target.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030B0018" : ("Timeout occurred while reading plugin console log on dom0 target.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030B0019" : ("Timeout occurred while reading plugin console log on domu target.", "FAIL_AND_SHOW")
}

# ASM/DB Specific Error codes
gAsmError = {
    "0x030C0000" : ("ASM Deactivation outcome is not set to yes on cells. Please refer MOS Note 2829056.1 for more details or contact Oracle support for assistance.","FAIL_DONTSHOW_PAGE_ONCALL")
}

# Oneoff Specific Error codes
gOneoff = {
    "0x030D0000" : ("One off patch apply failed.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030D0001" : ("One off patches missing. stage and re-run one off patch","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030D0002" : ("Parent plugins not available.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030D0008" : ("Unable to copy oneoff patches to target nodes.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030D0009" : ("Oneoff patch operation exception encountered.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030D000F" : ("Node not started up post oneoff V2 plugin execution and node reboot.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030D0010" : ("One off V2 patch apply failed.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030D0011" : ("Unable to copy oneoff v2 patches to target nodes.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030D0012" : ("One off V2 patches missing. stage and re-run one off patch.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030D0013" : ("Exception in Running Oneoff V2 plugins on patch targets.","FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030D0014" : ("Cleanup of oneoff patch and logs failed on the domu target node.","FAIL_AND_SHOW"),
    "0x030D0015" : ("One off patch apply failed on the DomU target.","FAIL_AND_SHOW"),
    "0x030D0016" : ("Unable to copy oneoff patches to DomU nodes.","FAIL_AND_SHOW"),
    "0x030D0017" : ("Oneoff patches on the DomU target nodes are missing.","FAIL_AND_SHOW"),
    "0x030D0018": ("Oneoff V2 plugin script bundle is missing.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030D0019": ("SHA256 sum mismatch for Oneoff V2 plugin script bundle.", "FAIL_DONTSHOW_PAGE_ONCALL"),
    "0x030D001A": ("An error occurred while validating the Oneoff V2 plugin script bundle.", "FAIL_DONTSHOW_PAGE_ONCALL")
}

gCpsGenericError = {
    "0x00000000"  : "CPS Remoteec Task completed successfully. No further action required",
    "0x030F0000"  : "Standby CPS node details empty",
    "0x030F0001"  : "Not a valid additional option parameter for patchmgr.",
    "0x030F0002"  : "Invalid patch option, options can be patch or rollback or patch_prereq_check or backup or postcheck",
    "0x030F0003"  : "Error in confirming Master CPS Node",
    "0x030F0004"  : "CPS operation Status failed.",
    "0x030F0005"  : "Patchmgr console read output was not successful",
    "0x030F0006"  : "CPS patch exception detected.",
    "0x030F0007"  : "CPS node is already at intended version."
}

gCpsPrecheckError = {
    "0x03100000"  : "Insufficient space on Primary CPS launch node and unable to extract patch.",
    "0x03100001"  : "Insufficient space available under patch stage location.",
    "0x03100002"  : "Patch precheck failed on CPS node."
}

gCpsPatchError = {
    "0x03110000"  : "Hardware alert detected on CPS node.",
    "0x03110001"  : "Input Target version empty.",
    "0x03110002"  : "Node type is not compute, dbmcli utility cannot be used.",
    "0x03110003"  : "patchmgr session is active on the primary CPS node. Before you perform cleanup and re-try, please verify if there is an ongoing patchmgr session as cleaning-up an ongoing patchmgr session can leave the system in unusable state.",
    "0x03110004"  : "dbserverd services are down on CPS node being patched.",
    "0x03110005"  : "Target version on the CPS node and the target version are not the same.",
    "0x03110006"  : "Patch operation failed with errors. Check thread log for more details.",
    "0x03110007"  : "Unable to obtain or parse image version for CPS node being patched.",
    "0x03110008"  : "RPM database is corrupted. Please perform rebuild manually and re-try patch.",
    "0x03110009"  : "System is in partially updated state on CPS node. Image backup cannot be performed."
}

gCpsRollbackError = {
    "0x03120000"  : "Rollback operation failed with errors. Check thread log for more details.",
    "0x03120001"  : "Rollback cannot be performed as the target version is lower than the current version.",
    "0x03120002"  : "Image version is either empty or undefined. Rollback is not possible.",
    "0x03120003"  : "Both Active image version and Inactive image version are of the same version."
}

gCpsSwitchoverError = {
    "0x03130000"  : "Switchover operation failed with errors. Check thread log for more details.",
    "0x03130001"  : "Switchover Status operation failed with errors. Check thread log for more details."
}

gCpsPostcheckError = {
    "0x03140000"  : "post-patch check failed, Image status is not success.",
    "0x03140002"  : "Post-patch check failed, Podman bridge configuration failed."
}

gCpsBackupkError = {
    "0x03150000"  : "Backup operation failed with errors. Check thread log for more details."
}

# -- Error Range constants
G_SUCCESS_PATCH_GENERIC        = "0000"
G_ERROR_RANGE_PATCH_GENERIC    = "0301"
G_ERROR_RANGE_PRECHECK_DOM0    = "0302"
G_ERROR_RANGE_PATCH_DOM0       = "0303"
G_ERROR_RANGE_PRECHECK_DOMU    = "0304"
G_ERROR_RANGE_PATCH_DOMU       = "0305"
G_ERROR_RANGE_PRECHECK_CELL    = "0306"
G_ERROR_RANGE_PATCH_CELL       = "0307"
G_ERROR_RANGE_PRECHECK_SWITCH  = "0308"
G_ERROR_RANGE_PATCH_SWITCH     = "0309"
G_ERROR_RANGE_PLUGINS_DOM0     = "030A"
G_ERROR_RANGE_PLUGINS_DOMU     = "030B"
G_ERROR_RANGE_ASM              = "030C"
G_ERROR_RANGE_ONEOFF           = "030D"
G_CPS_ERROR_RANGE_GENERIC      = "030F"
G_CPS_ERROR_RANGE_PRECHECK     = "0310"
G_CPS_ERROR_RANGE_PATCH        = "0311"
G_CPS_ERROR_RANGE_ROLLBACK     = "0312"
G_CPS_ERROR_RANGE_SWITCHOVER   = "0313"
G_CPS_ERROR_RANGE_POSTCHECK    = "0314"
G_CPS_ERROR_RANGE_BACKUP       = "0315"

def mGetPatchkey(_error_code_range_key):
    """
     This method returns the dictionary in which the
     error code was found based on the above Error
     constants range.
    """

    if _error_code_range_key in [ G_ERROR_RANGE_PATCH_GENERIC, G_SUCCESS_PATCH_GENERIC ]:
        return gPatchGenericError

    if _error_code_range_key == G_ERROR_RANGE_PATCH_DOM0:
        return gPatchDom0Error

    if _error_code_range_key == G_ERROR_RANGE_PATCH_CELL:
        return gPatchCellError

    if _error_code_range_key == G_ERROR_RANGE_PATCH_SWITCH:
        return gPatchSwitchError

    if _error_code_range_key == G_ERROR_RANGE_PATCH_DOMU:
        return gPatchDomuError

    if _error_code_range_key == G_ERROR_RANGE_PLUGINS_DOM0:
        return gDom0PatchPluginError

    if _error_code_range_key == G_ERROR_RANGE_PLUGINS_DOMU:
        return gDomUPatchPluginError

    if _error_code_range_key == G_ERROR_RANGE_ASM:
        return gAsmError

    if _error_code_range_key == G_ERROR_RANGE_ONEOFF:
        return gOneoff

    if _error_code_range_key == G_ERROR_RANGE_PRECHECK_DOM0:
        return gPrecheckDom0Error

    if _error_code_range_key == G_ERROR_RANGE_PRECHECK_CELL:
        return gPrecheckCellError

    if _error_code_range_key == G_ERROR_RANGE_PRECHECK_SWITCH:
        return gPrecheckSwitchError

    if _error_code_range_key == G_ERROR_RANGE_PRECHECK_DOMU:
        return gPrecheckDomuError

    if _error_code_range_key == G_CPS_ERROR_RANGE_PRECHECK:
        return gCpsPrecheckError

    if _error_code_range_key == G_CPS_ERROR_RANGE_GENERIC:
        return gCpsGenericError

    if _error_code_range_key == G_CPS_ERROR_RANGE_PATCH:
        return gCpsPatchError

    if _error_code_range_key == G_CPS_ERROR_RANGE_ROLLBACK:
        return gCpsRollbackError

    if _error_code_range_key == G_CPS_ERROR_RANGE_SWITCHOVER:
        return gCpsSwitchoverError

    if _error_code_range_key == G_CPS_ERROR_RANGE_POSTCHECK:
        return gCpsPostcheckError

    if _error_code_range_key == G_CPS_ERROR_RANGE_BACKUP:
        return gCpsBackupkError

#This function is made backward compatible whether the error json schema is defined in old or new format
def ebPatchFormatBuildError(aErrorCode, aSuggestionCode=None, aComment=None):
    """
     This method returns a formatted
     Error code - Error message - Comment
     output.
    """
    '''
     For Ex : If aErrorCode is 0x003000000,
              _error_range is 0300
    '''
    _error_description = None
    _error_range = str(aErrorCode[2:6])
    gPatchError = dict(mGetPatchkey(_error_range))

    if aErrorCode not in gPatchError:
        return ("0x03010000", str(gPatchGenericError[('0x03010000')]), aSuggestionCode)

    _error = gPatchError[str(aErrorCode)]
    if _error and isinstance(_error, tuple):
        _error_description = _error[0]
        _error_action = _error[1]
        ebLogInfo(f"Error Action is {_error_action} for Error Code {aErrorCode} ")
    else:
        _error_description = _error

    if _error_description:
        ebLogInfo(f"Error description is {str(_error_description)}")
    else:
        ebLogInfo("Error Description is Empty")

    return (str(aErrorCode), str(_error_description), str(aSuggestionCode))

#The caller has to ignore the extra return parameter error_action with _ if not required
#_code, _error_msg, _, _ = ebPatchFormatBuildErrorWithErrorAction(aError, aSuggestion)
def ebPatchFormatBuildErrorWithErrorAction(aErrorCode, aSuggestionCode=None, aTargetTypes = None):
    """
     This method returns a formatted
     Error code - Error message - Comment - ErrorAction
     output.
    """

    '''
     For Ex : If aErrorCode is 0x003000000,
              _error_range is 0300
    '''
    _error_description = None
    #Default value for error Action
    _error_action = "FAIL_DONTSHOW_PAGE_ONCALL"

    _error_range = str(aErrorCode[2:6])
    gPatchError = dict(mGetPatchkey(_error_range))

    if aErrorCode not in gPatchError:
        ebLogInfo("Error Code is Empty for Infrapatching. Returning Generic error code 0x03010000")
        return ("0x03010000", str(gPatchGenericError[('0x03010000')]), aSuggestionCode, _error_action)

    _error = gPatchError[str(aErrorCode)]
    if _error and isinstance(_error, tuple):
        _error_description = _error[0]
        #if target is domu , for specific generic errorcodes make the errorAction FAIL_AND_SHOW
        if aTargetTypes and (PATCH_DOMU in aTargetTypes) and aErrorCode in gDomUGenericErrorAsFailAndShow:
            _error_action = "FAIL_AND_SHOW"
            ebLogInfo(f"Marking Error Action as FAIL_AND_SHOW for Generic Error Code {aErrorCode} for domu")
        else:
             _error_action = _error[1]
        ebLogInfo(f"Error Action is {_error_action} for Error Code {aErrorCode} ")
    else:
        _error_description = _error

    if _error_description:
        ebLogInfo(f"Error description is {str(_error_description)}")
    else:
        ebLogInfo("Error Description is Empty")

    return (str(aErrorCode), str(_error_description), str(aSuggestionCode), _error_action)

def mUpdateErrorObjectToDB(aCluCtrl,aErrorObj):
    '''
      Updates Error Object to DB
    '''
    _errMsg = ''
    _errCode = ''
    _errorAction = ''

    ebLogInfo("Updating ErrorObject with error message to DB")
    _errCode = aErrorObj[0]
    if _errCode:
        _errCode, _errMsg, _, _errorAction = ebPatchFormatBuildErrorWithErrorAction(_errCode)
        ebLogInfo(f"Error Message for _errCode {_errCode} is {_errMsg} and Error action is {_errorAction}")
    _err_obj = [ _errCode, _errMsg, _errorAction, "0" ]
    '''
     This is for updating retrycount to 0 in errorresponse Exacloud table, this was removed
     and patching was tried and below error was observed.

      File "/u02/ecra_preprov/oracle/ecra_installs/exascaleinteg/mw_home/user_projects/domains/exacloud/exabox/ovm/clucontrol.py", line 15797, in mUpdateErrorObject
      _sqldata = (self.mGetUUID(),aErrorObject[0],aErrorObject[1],aErrorObject[2],aErrorObject[3],aDetailError, aNodeData)
      IndexError: tuple index out of range
    '''
    _final_err_obj = tuple(_err_obj)
    aCluCtrl.mUpdateErrorObject(_final_err_obj, _errMsg)
