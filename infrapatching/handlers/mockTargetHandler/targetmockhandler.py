#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/mockTargetHandler/targetmockhandler.py /main/8 2025/01/17 05:22:26 emekala Exp $
#
# targetmockhandler.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      targetmockhandler.py - Place holder for common functionalities among all
#      targets.
#
#    DESCRIPTION
#      This module contains common methods which are shared between one or more
#      targets (Storage Cell, Dom0, domU and Switches).
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    emekala     12/13/24 - ENH 37374442 - SUPPORT INFRA PATCH MOCK FWK TO
#                           ACCEPT MOCK RESPONSE IN JSON FORMAT VIA REST API
#    diguma      12/06/24 - bug 37365122 - EXACS:24.4.2.1:X11M: ROLLING DOM0
#                           PATCHING FAILS WITH SSH CONNECTIVITY CHECK FAILED
#                           DURING PATCHING EVEN THOUGH EXASSH TO DOMUS WORK
#    emekala     11/29/24 - ENH 37328901 - Add support to initialize infra
#                           patch mock setup when payload has mock request
#                           attribute
#    emekala     11/20/24 - BUG 37293033 - INFAPATCHING MOCK OPERATIONS ARE
#                           FAILING IN BM ENV
#    emekala     10/25/24 - ENH 37070223 - SYNC MOCK HANLDERS WITH LATEST CODE
#                           FROM CORE INFRAPATCHING HANDLERS AND ADD SUPPORT
#                           FOR CUSTOM RESPONSE AND RACK DETAILS
#    sdevasek    10/22/24 - Bug 37175058 - DOMU PATCHING FAILED WITH MISLEADING
#                           ERROR MESSAGE
#    antamil     10/11/24 - Bug 37161723 - Fix for patchmgr script existence 
#                           check
#    antamil     10/11/24 - Bug 37161723 - Fix for patchmgr script existence 
#    araghave    10/08/24 - Enh 37034564 - PRINT SPACE UTILISATION DETAILS BOTH 
#                           IN MB AND GB FORMAT 
#    araghave    10/08/24 - Enh 36505637 - IMPROVE POLLING MECHANISM IN CASE
#                           OF INFRA PATCHING OPERATIONS
#    jyotdas     10/07/24 - ER 37089701 - ECRA Exacloud integration to enhance
#                           infrapatching operation to run on a single thread
#    antamil     10/04/24 - Enh 37027134 - Modularize single vm patching code
#    sdevasek    09/25/24 - Enh 37036765 - CODE COVERAGE IMPROVEMENT -
#                           MAKE METHOD NAME INTO SINGLE LINE
#    sdevasek    09/23/24 - ENH 36654974 - ADD CDB HEALTH CHECKS DURING DOM0
#                           INFRA PATCHING
#    antamil     09/20/24 - bug 37057639 - cleanup known_host file based on Ip
#    jyotdas     09/19/24 - Bug 37028368 - Dom0 patching with ECRA switchover
#                           exited with error before the patchmgr run completed
#    araghave    09/16/24 - Enh 36971721 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE TARGET HANDLER FILES
#    antamil     09/12/24 - bug 37048223 - Fix for patchmgr script missing failure
#                           seen on single vm patching
#    gparada     09/11/24 - 37042976 Fix call to mAddSecscanSshdSingle
#    bhpati      09/04/24 - Enh 36902510 - ALREADY CONFIGURED ROOT SSH
#                           EQUIVALENCY BETWEEN DOMU'S REPORTS 0X03010040 AT
#                           POST PATCHING STAGE.
#    emekala     08/27/24 - ENH 36748344 - USE PATCHMANAGER OBJECT IN ALL DOMU
#                           OPERATIONS
#    diguma      08/21/24 - bug 36871736:REPLACE EXASPLICE WITH ELU(EXADATA
#                           LIVE UPDATE) FOR EXADATA 24.X
#    emekala     08/13/24 - ENH 36679949 - REMOVE OVERHEAD OF INDEPENDENT
#                           MONITORING PROCESS FROM INFRAPATCHING
#    antamil     08/12/24 - Bug 36798372 - Change the owner of patchmgr files
#                           to opc when management host is used as launchnode
#    antamil     08/01/24 - Bug 36881089 - Configure passwordless ssh using
#                           ssh config file on management host
#    antamil     07/24/24 - Bug 36829942 - Missing fixes for single VM patching
#                           on MAIN
#    avimonda    07/23/24 - Bug 36563684 - AIM4EXACLOUD:0X03040001 - VM PRECHECK
#                           EXCEPTION DETECTED. (23.4.1.2.1-DOMU)
#    asrigiri    07/23/24 - Bug 36811005 - MAKE THE INFO TO ERROR WHEN PATCHMGR
#                           ALREADY EXIST.
#    araghave    07/18/24 - ER 34893466 - EXACS | EXACLOUD THREAD LOG FOR
#                           PATCHING NEEDS MORE INFORMATION - EASE OF USE
#    araghave    07/18/24 - ER 36641819 - EXACC GEN2 | TOOLING TO REPORT THE EXACT
#                           VM NAME WHICH FAILED TO START IN EXACLOUD THREAD
#                           LOGS
#    avimonda    07/17/24 - AIM4EXACLOUD:0X03010032 - DETECTED CRITICAL HARDWARE
#                           ALERT ON SPECIFIED TARGET. (23.4.1.2.1-DOM0)
#    araghave    07/15/24 - Enh 36830077 - CLEANUP KSPLICE CODE FROM
#                           INFRAPATCHING FILES
#    antamil     07/10/24 - Bug 36807420 - Cleanup known host during cleanup of 
#                           keys
#    emekala     06/26/24 - ENH 36748433 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE DOM0, CELL, IBSWITCH AND ROCESWITCH PATCHMGR
#                           CMDS
#    diguma      06/25/24 - Bug 36727709: IMPLEMENT TFA BLACKOUT NOTIFICATION
#                           FOR DOMU VM OS PATCHING BY INFRAPATCHING TEAM
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    araghave    06/06/24 - Enh 36628557 - DOMU OS PATCHING CHECKS TO PREVENT 
#                           OUTAGE
#    antamil     05/31/24 - Bug 36659206 - Changes to report precheck failure
#                           message to CP
#    antamil     05/30/24 - Bug 36542578 - Fix the return status on 
#                           mReadLocalNodePatchmgrConsoleOut
#    antamil     05/22/24 - Bug 36635964 - Fix mExecutePatchmgrCmd for single
#                           VM patching
#    antamil     05/22/24 - Bug 36635964 - Fix mExecutePatchmgrCmd for single 
#                           VM patching
#    josedelg    05/14/24 - Bug 36581470 - Break iteration when patchmgr
#                           process is found in any dom0 in cluster.
#    araghave    05/07/24 - Bug 36543876 - ERROR OUT WHEN GRID HOME PATH BINARY
#                           DOES NOT EXISTS FOR CRS AUTOSTART ENABLED CHECK
#    avimonda    04/26/24 - Bug 36555012 - Removing HW alerthistory checks for
#                           DomU, since it does not interact directly with
#                           the hardware.
#    araghave    04/19/24 - ER 36452945 - TERMINATE INFRA PATCHING THREAD EARLY
#                           IN CASE OF PATCHMGR COMMAND DID NOT RUN
#    apotluri    04/10/24 - Enhancement Request 36492251 - INFRAPATCHING :
#                           OPTIMISE CODE AROUND PATCHMGR START AND END PHASE
#                           FOR BETTER CPU UTILISATION
#    emekala     03/26/24 - ENH 36445542 - /BIN/SHA256SUM NOT PRESENT ON FEW
#                           PRODUCTION RACKS CAUSING INFRAPATCHING ARTIFACT
#                           STAGING FAILURES
#    diguma      03/24/24 - Bug 36442733: small fix to check 
#                           mCheckandRestartCRSonDomU
#    antamil     03/12/24 - Bug 36383353: Fix for diff command failure log message
#    antamil     03/11/24 - Enh 36372221 - Code changes for single VM EXACS
#                           patching support
#    emekala     03/08/24 - ENH 36351481 - DISABLE COPYING OF DBNU PLUGINS
#                           DURING DOMU PATCHING
#    araghave    03/08/24 - Bug 36382885 - DOM0 PATCH POST VALIDATION FAILED
#                           WHILE CHECKING FOR /ETC/XEN/SCRIPTS/VIF-BRIDGE.EBT
#                           ON X9M
#    araghave    02/28/24 - Enh 36295801 - IMPLEMENT ONEOFFV2 PLUGIN EXACLOUD
#                           CHANGES
#    avimonda    02/12/24 - Bug 36238752: If there are directories in the remote
#                           patch base that do not contain the patchmgr file,
#                           the remote patch base dir must be removed.
#    araghave    02/07/24 - Enh 36234905 - ENABLE SERVICESTATE OF INFRA ILOM
#                           DURING UPGRADE & DISABLE THEM AFTER UPGRADE
#    sdevasek    01/30/24 - ENH 35306246 - ADD DB HEALTH CHECKS
#                           DURING DOMU OS PATCHING
#    araghave    01/24/24 - Enh 36219869 - SKIP INACTIVE VERSION CHECK DURING
#                           PATCH CLEANUP IN CASE OF NEWLY PROVISIONED
#                           ENVIRONMENTS
#    antamil     02/02/23 - 36109360 - Codes changes for Cps as launch node
#    araghave    02/02/23 - 35634510 - INTRODUCE LOCAL METHODS FOR THE CPS NODE TO
#                           WORK AS EXTERNAL PATCH LAUNCH NODE
#    araghave    02/02/23 - 36195067 - SETUP AND REVOKE PASSWDLESS SSH IN CASE OF
#                           CPS AS A LAUNCH NODE
#    sdevasek    12/18/23 - Bug 36116662 - WHEN FREE_SPACE_CHECK_VALIDATION_
#                           ENABLED_ON_CELL IS TRUE, INFRAPATCHING SHOULD TAKE
#                           THRESHOLD SIZE OF 3126MB 
#    araghave    12/11/23 - Bug 36030818 - PATCHMGR LOGS NOT AVAILABLE ON
#                           DRIVING NODES
#    antamil     12/05/23 - Fix for bug 36095866, generate keys on launch node
#    emekala     11/28/23 - ENH 36020428 - COPY PATCH TO LAUNCH NODES BASED ON
#                           THE CHECKSUM GENERATED ON TARGET
#    antamil     11/17/23 - BUG 36000710 - FIX FOR CPS AS LAUNCH NODE TO USE NAT
#    sdevasek    11/15/23 - ENH 36011846 - RUN RDS_PING TO VALIDATE VM TO VM 
#                           AND VM TO CELL CONNECTIVITY AFTER HEARTBEAT CHECK
#                           FAILURE IN DOM0 PATCHING
#    asrigiri    11/13/23 - Bug 35815597 - DOMU 22.1.14 PATCH FAIL WITH -
#                           ERROR: REPOSITORY FILE SPECIFIED
#                           (EXADATA_OL7_22.1.14.0.0.230818_LINUX-X86-64.ZIP)
#                           UNKNOWN.USE (ORACLE LINUX 6 OR 7) REPOSITORY FOR
#                           PHYSICAL EXADATA OR USER DOMAIN (DOMU).
#    diguma      10/30/23 - ENH 35656193 - EXADATA CLOUD DOMU OS PATCHING
#                           PRECHECK CLOUD UI SHOWING INCORRECT MESSAGE 
#                           // "DETECTED CRITICAL HARDWARE ALERT ON
#                           SPECIFIED TARGET."
#    sdevasek    10/27/23 - BUG 35949486 - RESTORING INFRA PATCHING CHANGES
#                           DONE AS PART OF 35825510
#    apotluri    10/11/23 - BUG 35892332 - EXACC | ERROR HANDLING TESTING -
#                           PRECHECK FAILURE DETAILS ON ONEVIEW HAS INCOMPLETE
#                           DETAILS
#    avimonda    10/03/23 - Bug 35659081 - Fixing the retry mechanism to
#                           validate image checksum.
#    antamil     09/29/23 - Bug 35851548 - Append request Id to dbnodes file name
#                           to be unique
#    sdevasek    09/19/23 - BUG 35692709 - DOM0 ROLLBACK IS EXECUTED ON
#                           DISCARDED NODE AND INFRAPATCHING OPERATION FAILS
#    diguma      09/15/23 - Bug 35797999 - use current version to check 
#                           exasplice
#    antamil     18/08/23 - ENH 35577433 - ADD VALIDATIONS ON EXTERNAL LAUNCH NODE
#                           PASSED
#    ririgoye    08/30/23 - Bug 35616435 - Fix redundant/multiple/deprecated
#                           instances of mConnect
#    sdevasek    08/24/23 - ENH 35476464 - UPDATE CNS NOTIFICATION JSON WITH
#                           NODE_PROGRESS_DATA IF IT EXISTS EVEN WHEN 
#                           ERROR_CODE AND ERROR_MESSAGE ARE NOT PRESENT IN DB
#    araghave    08/14/23 - Enh 35244586 - DISABLE PRE AND POST CHECKS NOT
#                           APPLICABLE DURING MONTHLY PATCHING
#    vikasras    08/03/23 - Bug 35671592 - AFTER REFRESHING TO THE RECENT LABEL
#                           TEST FILES ARE REPORTING COMPILATION ERROR
#    pkandhas    08/10/23 - 35657107 - IB patch fails due to version issue
#    jyotdas     08/08/23 - ENH 35614504 - Define erroraction for infrapatching
#                           at errorcode level instead of targettype level
#    antamil     08/03/23 - ENH 35621978 - ENABLE CPS AS LAUNCHNODE FOR
#                           DOMU PATCH OPERATION
#    jyotdas     07/26/23 - ENH 35641075 - Develop a generic framework for
#                           infrapatching api validation execution
#    avimonda    07/25/23 - Bug 34986894 - Adjust the patchmgr timeout to
#                           prevent CELLs patching timeout in rolling mode.
#    avimonda    07/20/23 - Bug 35443002 - Modify the patterns to effectively
#                           remove the ExaData patches.
#    vikasras    06/27/23 - Bug 35456901 - MOVE RPM LIST TO INFRAPATCHING.CONF
#                           FOR SYSTEM CONSISTIENCY DUPLICATE RPM CHECK
#    antamil     06/21/23   ENH 35026503 - SUPPORT TO LAUNCH MULTIPLE PATCHMGR
#                           SESSIONS  ON THE GIVEN EXTERNAL LAUNCH NODE
#    sdevasek    06/26/23 - BUG 35509499 - AIM4EXA2.0 - BUG NOT CREATED FOR
#                           INCIDENT IN BUG 35481344
#    araghave    06/13/23 - Bug 35489234 - DOM0 POSTCHECK OPERATION FAILS FOR
#                           HEARTBEAT CHECK AND UNABLE TO START CRS EVEN WHEN
#                           KEYS ARE AVAILABLE
#    araghave    06/09/23 - Enh 35479785 - PARAMETERISE TO ENABLE PERFORMING
#                           SPACE VALIDATIONS ON INDIVIDUAL TARGETS
#    pkandhas    06/01/23 - Enh 35371653, Remove Obsolete SSH keys
#    sdevasek    05/30/23 - ENH 35362646 - READ NODE PROGRESSING DATA FROM 
#                           IDEMPOTENCY PAYLOAD AS A PART OF RETRY REQUEST
#    jyotdas     05/23/23 - ENH 35401192 - Handling patchmgr reboot scenario
#                           during ecra active active upgrade
#    araghave    05/11/23 - Enh 35353733 - REFACTOR AND USE NEW SSH CONNECTIVITY
#                           VALIDATION METHODS FROM CLUAPATCHHEALTHCHECK.PY
#    sdevasek    05/04/23 - BUG 35355975 - DOM0 PATCHING CONTINUED TO THE NEXT
#                           NODE WHILE VM IS STILL DOWN ON LAST PATCHED NODE
#    sdevsek     05/01/23 - BUG 35335917 - ACTIVE ACTIVE UPGRADE: ERROR OCCURS
#                           WITH _JSON_PATCH_REPORT_DATA DOES NOT HAVE
#                          'NODE_PROGRESSING_STATUS' KEY AFTER THE SWITCHOVER
#    sdevasek    04/24/23 - BUG 35088859 - PATCHMGR FAILURE LOGS NOT COPIED
#                           ON EXACLOUD OEDA LOCATION
#    araghave    04/19/23 - Bug 35281111 - EXACS| EXACLOUD PATCH AND PREPATCH
#                           FAILS DUE TO SPACE
#    jyotdas     04/17/23 - ENH 35106082 - By default run dom0domu plugin on
#                           autonomous vms
#    sdevasek    04/12/23 - BUG 35272253 - PERFORM HEARTBEAT VALIDATIONS POST
#                           ADDING RELEVANT DISKMON MESSAGES IN ALERT LOG
#    araghave    04/03/23 - Bug 35227491 - DOMUHANDLER AUTHENTICATION FAILURE 
#                           BUT ECRA WF DIDN'T FAILED 
#    josedelg    03/29/23 - 35232371 - Save ebCluSshSetup instance for using
#                           in the cleanup step
#    talagusu    03/27/23 - Bug 34881003 - EXACS | EXACLOUD FAILED PATCHING DUE TO FAILURE IN COPYING PATCHMGR LOGS
#    antamil     03/21/23 - Enh 35026476 - external launch node support
#                           for cell and switch
#    diguma      02/16/23 - Bug 35080646 - in case of FS encryption, pass
#                           key_api.sh location to patchmgr
#    araghave    02/09/23 - Enh 34859379 - PERFORM CRS BOUNCE BEFORE HEARTBEAT
#                           CHECK TIMEOUT, IF DOMU'S ARE UNABLE TO ESTABLISH A
#                           HEART BEAT TO THE CELLS
#    sdevasek    30/01/23 - BUG 34622357 - STATUS CALL OUTPUT IS NOT SHOWING
#                           NODE_PROGRESS_DATA EVEN THOUGH DOMU PRECHECK 
#                           COMPLETED SUCCESSFULLY
#    antamil     02/02/23 - ENH 34893583 - ENABLE PLUGIN SUPPORT FOR
#                           MONTHLY PATCHING
#    diguma      01/23/23 - Bug 34961991 - adding check to add flag
#                           --allow_selinux_enforcing
#    jyotdas     01/16/23 - BUG 34979995 - patching failed due to checksum json
#                           encoder issue
#    pkandhas    12/07/22 - BUG 34862200 - Set timeout for dbmcli/cellcli
#    diguma      12/01/22 - Enh 34840180 - addition of specific alerts for
#                           ExaCC
#    araghave    11/25/22 - Bug 34828301 - EXACC:INFRA-PATCH:DOM0 PRECHECK
#                           EXPECT INCORRECT SPACE REQUIREMENT - SPACE IN / -
#                           NEEDED 5120 GB, GOT 2207 GB
#    diguma      11/13/22 - ER 34444560 - adding parameter
#                           --skip_gi_db_validation for patchmgr
#    araghave    10/27/22 - Enh 34683285 - INFRA PATCHING CHANGES FOR EXADATA
#                           PATCHMGR ERROR HANDLING
#    bchapman    10/18/22 - Bug 34655355 - WE NEED TO GENERATE MORE PRECISE
#                           MESSAGES FOR MVALIDATEIMAGECHECKSUM FAILURES
#    araghave    10/03/22 - BUG 34665176 - HANDLING TIMEOUT ERRORS DURING
#                           CLEANUP OF EXADATA PATCHES
#    araghave    09/29/22 - Enh 34623863 - PERFORM SPACE CHECK VALIDATIONS
#                           BEFORE PATCH OPERATIONS ON TARGET NODES
#    araghave    09/19/22 - ENH 34480945 - EXACS:22.2.1:MVM IMPLEMENTATION ON
#                           INFRA PATCHING CORE FILES
#    sdevasek    07/18/21 - ENH 34384737 - CAPTURE EXACLOUD START_TIME,
#                           EXACLOUD_END_TIME AND PATCHING TIME TAKEN BY NODES
#    araghave    06/10/22 - Enh 34157603 - CREATING DUMMY PATCHMGR NOTIFICATION
#                           XML IN CASE IT IS DELETED
#    araghave    06/09/22 - Enh 34258082 - COPY PATCHMGR AND OTHER LOGS FROM
#                           LAUNCH NODES POST PATCHING ONLY IF THE EXIT STATUS
#                           IS A FAILURE
#    sdevasek    06/07/22 - Bug 34246727 - EXACS: DOMU EXACSOSPATCH PRECHECK
#                           FAILS WITH ERROR STALE MOUNT(S) DETECTED ON DOMU
#    araghave    06/06/22 - Enh 34247908 - GET FILTERED NODE LIST ONCE FOR
#                           MCHECKKNOWNALERTHISTORY AND MCHECKHWCRITICALALERT
#                           METHOD
#    araghave    05/25/22 - ENH 34179923 - WHEN PATCH RETRY IS TRIGGERED FROM
#                           CP PASS NOBACKUP TO PATCHMGR BY CHECKING SYSTEM
#                           CONSISTENCY STATE
#    jyotdas     05/24/22 - ENH 34161120 - expose nodeprogressingstatus field
#                           from fleetpatchingresponse to cp
#    sdevasek    05/18/22 - ENH 34053202 - INFRAPATCHING PRECHECK TO VALIDATE
#                           THE PRESENCE OF DOM0_IPTABLES_SETUP.SH SCRIPT
#    araghave    04/28/22 - Bug 34094559 - REVERTING THE CHANGES FOR ENH
#                           33729129
#    araghave    04/12/22 - Enh 33833262 - DOM0 AND DOMU LAUNCH NODES SPACE
#                           MANAGEMENT
#    araghave    04/12/22 - Bug 34050416 - COULD NOT PARSE /EXAVMIMAGES/ FOR
#                           FREE SPACE ON DOMU TO COPY EXADATA UPGRADE BITS
#    araghave    03/30/22 - Enh 34000386 - PATCH NOTIFICATION SUPPORT FOR ROCE
#                           SWITCHES
#    sdevasek    03/29/22 - ENH 33453366 CAPTURE PATCHMGR LOG LOCATION WHEN 
#                           PATCHMGR IS FAILED
#    jyotdas     03/24/22 - ENH 33909170 - post patch check on domu failed due
#                           to crs services are down
#    araghave    03/23/22 - Enh 34010822 - Validate both patchmgr base dir and
#                           patchmgr log dir location for switch upgrade files
#    jesandov    03/14/22 - Solve typo
#    araghave    03/06/22 - Enh 33925371 - DISABLE SSH CONNECTIVITY CHECK
#                           DURING POSTCHECK IF UNKEY IS DISABLED DURING
#                           ROCESWITCH PATCH
#    araghave    02/20/22 - ENH 33689675 - ADD NEW ERROR FOR DOMU PATCHMGR
#                           FAILURE AND MARK FAIL AND SHOW
#    araghave    02/20/22 - Bug 33847682 - DELAYED PATCHMGR PROCESS EXIT CAUSES
#                           SUBSEQUENT PATCHMGR CLEANUP TO FAIL
#    josedelg    02/16/22 - Bug 33828825 - Retry copy of patch artifacts during
#                           precheck and patch
#    araghave    02/09/22 - Bug 33686503 - Populate status reporting details for
#                           all the nodes in the list.
#    jyotdas     02/06/22 - Bug 33829094 - exacc gen2- failing with error in
#                           multiprocessing(non-zero exitcode due to checksum
#                           file jsondecoder issue
#    nmallego    01/19/22 - Bug33763732 - Change log from error to info level
#    sdevasek    01/18/22 - Enh 32509673 - Require ability to specify Cell
#                           nodes to include as part of Patching process
#    araghave    01/18/22 - Enh 30646084 - Require ability to specify compute
#                           nodes to include as part of Patching process
#    jyotdas     01/17/22 - ENH 33748218 - optimize to call mhasstalemounts for
#                           single node upgrade
#    josedelg    01/17/22 - Bug33758128 - Clusterless patching mImportKeys
#                           was renamed to mHandlerImportKeys
#    nmallego    01/12/22 - Bug33689655 - UPDATE DOMU FAIL AND SHOW ERROR
#                           MESSAGE WITH MOS NOTE 2829056.1
#    araghave    01/06/22 - Enh 33729129 - Provide both .zip and .bz2 file
#                           extension support on System image files.
#    nmallego    01/04/22 - ER 33453352 - Validate root file system before
#                           taking backup
#    araghave    12/06/21 - Enh 33052410 - Purge System first boot image file
#                           for Dom0 space management
#    pkandhas    12/16/21 - BUG 33677531 - Fix Err msg for missing patchmgr
#    pkandhas    12/01/21 - BUG 33558732 - Handle Patches checksum json error
#    araghave    11/23/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES
#                           FROM ERROR.PY TO INFRAPATCHERROR.PY
#    jyotdas     11/19/21 - ENH 33577777 - Handle dbnu plugin script location
#                           in infrapatching to support exacc
#    jyotdas     11/17/21 - ENH 33415996 - Check for stale mounts parallelly
#    sdevasek    10/28/21 - Bug 33495944 - ECRA STATUS REPORTS IT AS SUCCESS
#                           EVEN THOUGH DOM0 ROLLBACK FAILED AT PATCHMGRSIDE 
#    araghave    10/20/21 - Enh 33486853 - MOVE TIMEOUT AND OTHER CONSTANTS OUT
#                           OF CODE INTO CONFIG/CONSTANT FILES
#    jyotdas     10/05/21 - Bug 33418843 - Patch Progress status not updated
#    josedelg    10/04/21 - Bug 33285054 - VIF-BRIDGE symlinks validation in
#                           the post check operation
#    sdevasek    09/30/21 - ENH 33400429 - CLEAN UP OF MODIFY AT PREREQ FROM
#                           ADDITIONAL OPTIONS
#    araghave    09/22/21 - Bug 33300892 - Enh 33382919 - CLEANUP EBERROR AND
#                           EXACLOUD ERROR CODE DETAILS FROM
#                           MVALIDATEIMAGECHECKSUM()
#    sdevasek    09/22/21 - Bug 32799615 - EXADATA VM CLUSTER OS IMAGE UPDATE
#                           MISSING FLAG ALLOW_ACTIVE_NETWORK_MOUNTS
#    jyotdas     09/20/21 - Enh 33290086 - stale mount check before starting
#                           dbserver patching for all nodes
#    araghave    09/17/21 - Enh 33345801 - ADD SSH PRE-CHECKS AS PART OF INFRA
#                           PATCHING PRECHECKS
#    nmallego    08/31/21 - Bug33249608 - Support non-rolling option
#    josedelg    08/19/21 - ENH 33147238 - Exacc copy patchmgr logs to CPS
#    araghave    08/16/21 - Bug 33216836 - Collect upgradeIBSwitch logs from
#                           Infra patching log location
#    araghave    08/09/21 - Bug 33197682 - COMPUTE NODE PATCHING FAILED AFTER
#                           SLEEP DELAY SETUP
#    josedelg    08/03/21 - ENH 33040391 Add precheck operation in exaversion
#                           patchreport
#    araghave    08/02/21 - Enh 33182904 - Move all configurable parameters
#                           from constants.py to Infrapatching.conf
#    nmallego    08/02/21 - Bug33114129 Pass ignore_alert for exasplice always
#    araghave    07/26/21 - BUG 32888598 - ISSUE WITH ASYNC CALLS DURING INFRA
#                           PATCHING
#    araghave    07/11/21 - ENH 33099120 - INTRODUCE A SPECIFIC ERROR CODE FOR
#                           PATCHMGR CONSOLE READ TIME OUT
#    araghave    07/09/21 - BUG 33081173 - Remove older error codes from Infra
#                           patching core files
#    nmallego    07/08/21 - Bug33092752 - Picking dom0 list always
#    jyotdas     06/30/21 - Bug 32813015 - non-rolling patching should not run
#                           dom0domu plugin
#    araghave    06/28/21 - Enh 32996951 - ENABLE IGNORE_DATE_VALIDATIONS
#                           OPTION FOR CELL UPGRADE BY DEFAULT
#    josedelg    06/23/21 - Bug 32978881 - Pre-check failed with alert
#                           alert.chassis.fw.fpga-upgrade-blocked
#    nmallego    06/04/21 - Bug32962679 - Validate ntp offset value  
#    araghave    05/19/21 - Bug 32888765 - Get Granular Error Handling details
#                           for Cells and Switches
#    araghave    05/12/21 - 32363866 - mValidateImageCheckSum fixes to
#                           represent patch files and checksum in new format.
#    josedelg    05/08/21 - ENH 32586428 - Configure known alerts in
#                           infrapatching.conf
#    araghave    04/20/21 - Bug 32397257 - Get granular error handling details
#                           for Dom0 and DomU targets
#    jyotdas     04/19/21 - ENH 32786829 - exacs : disable dom0domu plugin for
#                           monthly security patching (exasplice)
#    araghave    04/11/21 - Multiple occurances of MGETPATCHMGRXML failed with
#                           diff -w command errors
#    araghave    03/23/21 - Enh 31423563 - PROVIDE A MECHANISM TO MONITOR INFRA
#                           PATCHING PROGRESS
#    jyotdas     03/22/21 - Enh 32415195 - error handling: return infra
#                           patching dispatcher errors to caller
#    nmallego    02/08/21 - Bug32433614 - sleep between nodes
#    araghave    02/01/21 - Bug 32120772 - EXASPLICE AND PYTHON 3 FIXES
#    nmallego    01/28/21 - Bug31963499- Enable verbose logs
#    vmallu      01/22/21 - Bug 32412646 - 20.4.1: clusterless patching is
#    josedelg    01/20/21 - Bug 32387832 -  Refactored bug 31945775, 32078800
#    araghave    01/19/21 - Bug 32395969 - MONTHLY PATCHING: FOUND FEW ISSUES
#                           WHILE TESTING AND NEED TO FIX
#    araghave    01/07/21 - Bug 32320030 - ROCE SWITCH REFACTOR CODE CHANGES
#    vmallu      12/23/20 - Bug 32322988 - operation type is not set for
#                           cell 
#    nmallego    12/07/20 - Bug31982131 - Do not ignore critical h/w alert
#    nmallego    10/27/20 - Enh 31540038 - Change debug level
#    nmallego    11/08/20 - Bug32115347 - Change print mode
#    araghave    10/21/20 - Enh 31925002 - Error code handling implementation for
#                           Monthly Patching
#    nmallego    10/27/20 - Enh 31540038 - INFRA PATCHING TO APPLY/ROLLBACK
#                           EXASPLICE/MONTHLY BUNDLE
#    nmallego   10/23/20 - ER 31684959 - Add exaunitId, exaOcid, and exasplice as
#                          part of exacloud result payload
#    araghave   10/13/20 - Bug 32004388 - Reset System First boot image file
#                          naming convention
#    araghave   08/12/20 - ER 31395456 - Display the cell number during cell
#                          patching.
#    araghave   08/12/20 - Enh 30829107 - Patchmgr log detailed output and log 
#                          collection fix
#    nmallego   08/28/20 - Refactor infra patching code
#    nmallego   08/28/20 - Creation
#

import abc
import copy
import json
import time
import datetime
import traceback
import types
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from multiprocessing import Process
from uuid import uuid4
from defusedxml import ElementTree as ET
from exabox.core.Context import get_gcontext
from exabox.ovm.userutils import ebUserUtils
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.core.DBStore import ebGetDefaultDB
from time import sleep
from exabox.core.Node import exaBoxNode
from exabox.infrapatching.handlers.mockTargetHandler.genericmockhandler import GenericMockHandler
from exabox.infrapatching.handlers.pluginHandler.dbnupluginhandler import DbnuPluginHandler
from exabox.infrapatching.handlers.pluginHandler.exacloudpluginhandler import ExacloudPluginHandler
from exabox.infrapatching.handlers.pluginHandler.oneoffpluginhandler import OneOffPluginHandler
from exabox.infrapatching.handlers.pluginHandler.oneoffv2pluginhandler import OneOffV2PluginHandler
from exabox.infrapatching.handlers.pluginHandler.pluginhandlertypes import mGetPluginHandlerType
from exabox.infrapatching.utils.utility import PATCH_BASE, mFormatOut, mReadPatcherInfo, mGetFirstDirInZip,\
  mReadCallback, mErrorCallback, mGetInfraPatchingKnownAlert, mIsFSEncryptedList, mIsFSEncryptedNode, mGetInfraPatchingHandler,\
  DOMU_PATCH_BASE, runInfraPatchCommandsLocally, flocked, mGetSshTimeout
from exabox.ovm.clumisc import ebCluSshSetup
from exabox.utils.common import version_compare


sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))
import subprocess
import glob
import traceback



class TargetMockHandler(GenericMockHandler):

    def __init__(self, *initial_data, **kwargs):
        __metaclass__ = abc.ABCMeta
        super(TargetMockHandler, self).__init__(*initial_data, **kwargs)
        self.mPatchLogInfo("TargetMockHandler")

        self.__ibswitch_upgrade_version = None
        self.__ibswitch_rollback_version = None

        self.__plugins_log_path_on_launch_node = ""
        self.__callbacks = [mReadCallback, None, mErrorCallback, None]
        self._last_node_patched = ""
        self._cells_switches_remote_base = PATCH_BASE
        self.__json_status = {}

        # old patchmgr xml location for checking the pathing status change
        self.__patchmgr_old_xml_loc = None

        # Bug27556005 - Get ssh setup class object and use the same for both
        # ssh key generate and cleanup. It's used only for cell and ibswitch
        # patch operation. Dom0/Domu already having single object.
        self.__ssh_env_setup = None

        # Absolute path of metadata path and json which contains patch progress states
        self.__metadata_json_file = ""
        self.__patch_states_base_dir = ""

        # This is to handle keys for connecting to hosts . Initialized in setPatchEnvironment and cleared after every operation
        self.__ssh_env_setup = {}

        # Cell and Switch Related  Variables , since they are common for both
        self.__cells_switches_local_patch_zip = self.mGetCellSwitchesZipFile()
        self.__cells_switches_patch_zip_name = None
        self.__cells_switches_patch_base = None
        self.__cells_switches_patch_zip = None
        self.__cells_switches_patch_base_after_unzip = None
        self.__cells_switches_patch_zip_size_mb = None
        self.__cells_switches_patch_necessary_space_mb = None
        self.__dom0_to_patch_cells_switches = None
        self.__cells_switches_patchmgr = None

        # Ideally , __domu_to_patch_initial_domu should be in domuHandler
        # But is is being used in by mGetPatchmgrXml -> mGetDomUToPatchInitialDomU  in targetHandler and  mGetPatchmgrXml
        # is shared by all handlers . So exatest gives an error "Instance of 'TargetHandler' has no 'mGetDomUToPatchInitialDomU' member (no-member)
        # Hence variables moved to targetHandler and used getters and setterrs for __domu_to_patch_initial_domu are defined here
        # Same reason applicable for __dom0_to_patch_initial_dom0 as well
        self.__domu_to_patch_initial_domu = None
        self.__dom0_to_patch_initial_dom0 = None

        # List of logs copied to exacloud post patching.
        self.__list_of_logs_copied_to_exacloud_host = []

        #Initialize PluginHandler . Exacloud, oneoff - all plugins will be automatically enabled
        if self.isADBDImplicitPluginEnabled() == True:
            self.mPatchLogInfo("ADBD Implicit Plugin will run")
            _domU_autonomous_list = self.mGetAutonomousVMList()
            self.__pluginHandler = mGetPluginHandlerType(*initial_data, autonomousVMList=_domU_autonomous_list)
        else:
            self.mPatchLogInfo("ADBD Implicit Plugin will not run")
            self.__pluginHandler = mGetPluginHandlerType(*initial_data, **kwargs)

        if self.mIsMockEnv():
            # In mock setup, no need to run plugins
            self.__pluginHandler = None

        #Initialize NODE_SLEEP_MAX_LIMIT_IN_SECONDS timeout parameter.
        NODE_SLEEP_MAX_LIMIT_IN_SECONDS = self.mGetNodeSleepMaxLimitInSeconds()

        #Check for dbnu plugin handler . Valid for compute nodes currently , dom0 and ADBD domu
        self.__dbnu_plugin_handler = None
        if DbnuPluginHandler.mIsRunDbnuPlugin(self.mGetTargetTypes(),self.mGetTask(),self.mGetDbnuPluginBaseDirPrefix()):
            if not self.mIsMockEnv():
                # disable dbnu plugins for non ADBD domu
                if PATCH_DOMU in self.mGetTargetTypes() and len(self.mGetAutonomousVMList()) <= 0:
                    self.__dbnu_plugin_handler = None
                    self.mPatchLogInfo("Autonomous VMs not found. Dbnu plugin execution will be skipped on non-adbd vms!")
                else:
                    self.mPatchLogInfo("DbNu Plugin will Run")
                    self.__dbnu_plugin_handler = DbnuPluginHandler(*initial_data, **kwargs)

        # Read and update sleep time for compute nodes and raise exception if it exeeded the max limit.
        self.EXADATA_SLEEP_BETWEEN_COMPUTES_TIME_IN_SEC = self.mGetSleepbetweenComputeTimeInSec()
        if self.EXADATA_SLEEP_BETWEEN_COMPUTES_TIME_IN_SEC:
            self.mPatchLogInfo(
                f"Value set for sleep between compute nodes {self.EXADATA_SLEEP_BETWEEN_COMPUTES_TIME_IN_SEC} seconds.")
            if self.EXADATA_SLEEP_BETWEEN_COMPUTES_TIME_IN_SEC > NODE_SLEEP_MAX_LIMIT_IN_SECONDS or \
                    self.EXADATA_SLEEP_BETWEEN_COMPUTES_TIME_IN_SEC < 0:
                _error_msg = f"Sleep time between node upgrade should not be negative or exceed maximum limit of {NODE_SLEEP_MAX_LIMIT_IN_SECONDS} seconds. User specified value {self.EXADATA_SLEEP_BETWEEN_COMPUTES_TIME_IN_SEC}"
                _rc = EXADATA_INVALID_SLEEP_TIME_FOR_COMPUTES_IN_EXABOX_CONF
                self.mAddError(_rc, _error_msg)
                raise Exception(_error_msg)
        elif self.EXADATA_SLEEP_BETWEEN_COMPUTES_TIME_IN_SEC != 0:
            self.mPatchLogError(
                f"Invalid value set for sleep between compute nodes = {self.EXADATA_SLEEP_BETWEEN_COMPUTES_TIME_IN_SEC}.")
        #This is to handle keys for connecting to hosts . Initialized in setPatchEnvironment and cleared after every operation
        self.__ssh_env_setup_switches_cell = ebCluSshSetup(self.mGetCluControl())


    # Abstract method definitions -- needed to be implemented by the child class
    # Can be left completely blank, or a base implementation can be provided
    # Note that ordinarily a blank interpretation implicitly returns `None`,
    # but by registering, this behaviour is no longer enforced.
    @abc.abstractmethod
    def mPreCheck(self):
        pass

    @abc.abstractmethod
    def mPatch(self):
        pass

    @abc.abstractmethod
    def mRollBack(self):
        pass

    @abc.abstractmethod
    def mRollBackPreCheck(self):
        pass

    @abc.abstractmethod
    def mImageBackup(self):
        pass

    @abc.abstractmethod
    def mPostCheck(self):
        pass

    @abc.abstractmethod
    def mOneOff(self):
        pass

    def mGetDbnuPluginHandler(self):
        return self.__dbnu_plugin_handler

    def mGetPluginHandler(self):
        return self.__pluginHandler

    def mSetPluginHandler(self, aPluginHandler):
        self.__pluginHandler = aPluginHandler

    def mGetCallBacks(self):
        return self.__callbacks

    def mSetCallBacks(self, aCallBacks):
        self.__callbacks = aCallBacks

    def mGetSSHEnvSetUp(self):
        return self.__ssh_env_setup

    def mSetSSHEnvSetUp(self, aSSHEnvSetUp):
        if aSSHEnvSetUp:
            '''
             Below checks are applicable to Dom0 and Domu targets 
             and are used for validating ssh connectivity post passwordless 
             ssh is complete.
            '''
            _ssh_env = aSSHEnvSetUp["sshEnv"]
            for _node_name in range(len(aSSHEnvSetUp["fromHost"])):
                self.mPatchLogInfo(
                    f"Passwordless ssh validation performed between {str(aSSHEnvSetUp['remoteHostLists'][_node_name])} and {str(aSSHEnvSetUp['fromHost'][_node_name])}")
                if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
                    self.mGetCluPatchCheck().mVerifyPatchmgrSshConnectivityBetweenExadataHosts(aSSHEnvSetUp["remoteHostLists"][_node_name],
                                                                            aSSHEnvSetUp["fromHost"][_node_name], aSshUser='opc')
                else:
                    self.mGetCluPatchCheck().mVerifyPatchmgrSshConnectivityBetweenExadataHosts(aSSHEnvSetUp["remoteHostLists"][_node_name],
                                                                            aSSHEnvSetUp["fromHost"][_node_name])
        self.__ssh_env_setup = aSSHEnvSetUp

    def mGetDomUToPatchInitialDomU(self):
        return self.__domu_to_patch_initial_domu

    def mSetDomUToPatchInitialDomU(self,aDomuToPatchInitialDomu):
        self.__domu_to_patch_initial_domu = aDomuToPatchInitialDomu

    def mGetDom0ToPatchInitialDom0(self):
        return self.__dom0_to_patch_initial_dom0

    def mSetDom0ToPatchInitialDom0(self,aDom0ToPatchInitialDom0):
        self.__dom0_to_patch_initial_dom0 = aDom0ToPatchInitialDom0

    def mGetPatchStatesBaseDir(self):
        return self.__patch_states_base_dir

    def mSetPatchStatesBaseDir(self, aPatchStatesBaseDir):
        self.__patch_states_base_dir = aPatchStatesBaseDir

    # Getters for cell and switch related variables
    def mGetCellSwitchesLocalPatchZip(self):
        return self.__cells_switches_local_patch_zip

    def mGetCellSwitchesPatchZipName(self):
        return self.__cells_switches_patch_zip_name

    def mGetCellSwitchesPatchBase(self):
        return self.__cells_switches_patch_base

    def mSetCellSwitchesPatchBase(self, acellSwitchespatchBase):
        self.__cells_switches_patch_base = acellSwitchespatchBase

    def mGetCellSwitchesPatchZip(self):
        return self.__cells_switches_patch_zip

    def mSetCellSwitchesPatchZip(self, aCellSwitchesPatchZip):
        self.__cells_switches_patch_zip = aCellSwitchesPatchZip

    def mGetListOfLogsCopiedToExacloudHost(self):
        return self.__list_of_logs_copied_to_exacloud_host

    def mSetListOfLogsCopiedToExacloudHost(self, aListOfLogsCopiedToExacloudHost):
        self.__list_of_logs_copied_to_exacloud_host.append(aListOfLogsCopiedToExacloudHost)

    def mGetCellSwitchesPatchBaseAfterUnzip(self):
        return self.__cells_switches_patch_base_after_unzip

    def mSetCellSwitchesPatchBaseAfterUnzip(self,aCellSwitchesPatchBaseAfterPatchUnZip):
        self.__cells_switches_patch_base_after_unzip = aCellSwitchesPatchBaseAfterPatchUnZip

    def mGetCellSwitchesPatchZipSizeMb(self):
        return self.__cells_switches_patch_zip_size_mb

    def mGetCellSwitchesPatchNecessarySpaceMB(self):
        return self.__cells_switches_patch_necessary_space_mb

    def mGetDom0ToPatchcellSwitches(self):
        return self.__dom0_to_patch_cells_switches

    # Checks for amy plugin is enabled like Exacloud plugin or oneoff plugin
    def mIsPluginEnabled(self):
        if self.mIsMockEnv():
            # In mock setup, no need to run plugins
            return False

        if self.__pluginHandler is not None:
            return True
        else:
            return False

    def mIsExacloudPluginEnabled(self):
        return (self.__pluginHandler is not None) and (isinstance(self.__pluginHandler, ExacloudPluginHandler))

    def mIsDbnuPluginEnabled(self):
        return (self.__dbnu_plugin_handler is not None) and (isinstance(self.__dbnu_plugin_handler, DbnuPluginHandler))

    def mIsOneOffPluginEnabled(self):
        return (self.__pluginHandler is not None) and (isinstance(self.__pluginHandler, OneOffPluginHandler))

    def mIsOneOffV2PluginEnabled(self):
        return (self.__pluginHandler is not None) and (isinstance(self.__pluginHandler, OneOffV2PluginHandler))
    
    def mCheckConditionsForEncryptPatching(self):
        if self.mGetCurrentTargetType() == PATCH_DOMU and not self.mIsExaCC() and \
           self.mGetCluControl().mIsKVM(): 
            return True
        else:
            return False

    def mCleanSSHEnvSetUp(self, aSingleVmHandler=None):
        # _sshEnvDict = {
        #     "sshEnv": ebCluSshSetup(self.mGetCluControl()),
        #     "fromHost": ["a", "b"],
        #     "remoteHostLists": [["1", "2"], ["3", "4"]]
        # }
        _sshEnvDict = self.mGetSSHEnvSetUp()
        if _sshEnvDict:
            _ssh_env = _sshEnvDict["sshEnv"]
            for host in range(len(_sshEnvDict["fromHost"])):

                # Add secsacan key
                ebUserUtils.mAddSecscanSshdSingle(self.mGetCluControl(),_sshEnvDict["fromHost"][host])
                if aSingleVmHandler:
                    aSingleVmHandler.mCleanupSSHForSingleVM(_sshEnvDict["fromHost"][host], _sshEnvDict["remoteHostLists"][host], \
                                           _ssh_env, self)
                else:
                    _ssh_env.mCleanSSHPasswordless(_sshEnvDict["fromHost"][host],
                                               _sshEnvDict["remoteHostLists"][host])
                    _ssh_env.mRemoveFromKnownHosts(_sshEnvDict["fromHost"][host], _sshEnvDict["remoteHostLists"][host],False)
                    _ssh_env.mAddToKnownHosts(_sshEnvDict["fromHost"][host], _sshEnvDict["remoteHostLists"][host])
                '''
                 Below checks are applicable to Dom0 and Domu targets 
                 and are used for validating ssh connectivity post patching
                 activity is complete during the passwdless ssh cleanup stage.
                '''
                self.mPatchLogInfo(
                    f"Passwordless ssh validation performed between {str(_sshEnvDict['remoteHostLists'][host])} and {str(_sshEnvDict['fromHost'][host])}")
                if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
                    self.mGetCluPatchCheck().mVerifyPatchmgrSshConnectivityBetweenExadataHosts(_sshEnvDict["remoteHostLists"][host], _sshEnvDict["fromHost"][host], aStage="PostPatch", aSshUser='opc') 
                else:
                    self.mGetCluPatchCheck().mVerifyPatchmgrSshConnectivityBetweenExadataHosts(_sshEnvDict["remoteHostLists"][host], _sshEnvDict["fromHost"][host], aStage="PostPatch")

    def mGetMetadataJsonFile(self):
        return self.__metadata_json_file

    def mSetMetadataJsonFile(self, aMetaDataJsonFile):
        self.__metadata_json_file = aMetaDataJsonFile

    def mGetPatchmgrOldXmlLoc(self):
        return self.__patchmgr_old_xml_loc

    def mSetPatchmgrOldXmlLoc(self, aPatchmgrOldXmlLoc):
        self.__patchmgr_old_xml_loc = aPatchmgrOldXmlLoc

    def mGetCellIBPatchMgr(self):
        return self.__cells_switches_patchmgr

    def mSetCellIBPatchMgr(self, acellSwitchesPatchmgr):
        self.__cells_switches_patchmgr = acellSwitchesPatchmgr

    def mGetCellIBPatchZipName(self):
        return self.__cells_switches_patch_zip_name

    def mSetCellIBPatchZipName(self, acellSwitchesPatchZipName):
        self.__cells_switches_patch_zip_name = acellSwitchesPatchZipName

    def mSetDom0ToPatchcellSwitches(self):
        """
        Selects and sets the necessary files on a dom0 in order to patch cells and ibswitches.
        mGetLaunchNode call here returns a list of launchnode, even if it a single launch node
        """
        if self.mIsMockEnv():
            # in mock setup, skip rack specific operations
            return PATCH_SUCCESS_EXIT_CODE, []

        _exit_code = PATCH_SUCCESS_EXIT_CODE
        _external_launch_node = self.mGetExternalLaunchNode()
        if self.mGetCurrentTargetType() not in [ PATCH_IBSWITCH, PATCH_ROCESWITCH ] \
                and len(_external_launch_node) > 0:
            if _external_launch_node[0] in self.mGetCustomizedCellList():
                _exit_code = LAUNCH_NODE_PASSED_FOR_PATCH_OPERATION_SHOULD_NOT_BE_CELL
                _suggestion_msg = f"Launch node {_external_launch_node[0]} passed cannot be a cell node. "
                self.mAddError(_exit_code, _suggestion_msg)
                self.mPatchLogError(_suggestion_msg)
                return _exit_code, _external_launch_node
            _dom0s = _external_launch_node
        else:
            '''
             Launch node for cells and switches should always 
             be all node list and not custom node list.
            '''
            _dom0s = self.mGetCustomizedDom0List()
        self.mPatchLogInfo(f"Launch node to be used {str(_dom0s)}")


        self.__dom0_to_patch_cells_switches = self.mSetLaunchNodeAsPatchBase(
                aLaunchNodeCandidates=_dom0s,
                aLocalPatchZipFile=self.mGetCellSwitchesLocalPatchZip(),
                aPatchZipName=self.mGetCellIBPatchZipName(),
                aPatchZipSizeMb=self.__cells_switches_patch_zip_size_mb,
                aRemotePatchBase=self.mGetCellSwitchesPatchBase(),
                aRemotePatchZipFile=self.mGetCellSwitchesPatchZip(),
                aRemotePatchmgr=self.mGetCellIBPatchMgr(),
                aRemoteNecessarySpaceMb=self.__cells_switches_patch_necessary_space_mb,
                aPatchBaseDir=self._cells_switches_remote_base,
                aSuccessMsg="cells and ibswitches")

        if not self.__dom0_to_patch_cells_switches:
            _errmsg = "Unable to set a dom0 to act as patch manager for cells/ibswitches"
            self.mPatchLogError(_errmsg)
            _exit_code = PATCH_OPERATION_FAILED
            return _exit_code, _external_launch_node
        else:
            for _dom0 in _dom0s:
                if _dom0 in self.__json_status:
                    if 'error-1000' in _dom0:
                        del self.__json_status[_dom0]['error-1000']
        return _exit_code, _dom0s

    def mGetMountList(self, aHostList):

        self.mPatchLogInfo('Check for Stale Mounts and get the Mount List.')
        def mLoadMountonHost(aNodeName, aMountList):
            _cmd_load_mounts = "awk '{print $2}'  /etc/mtab  | sort -u"
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=aNodeName)
            try:
                _in, _out, _err = _node.mExecuteCmd(_cmd_load_mounts)
                _output = _out.readlines()
                self.mPatchLogInfo(f'Mount List on host {aNodeName} is {str(_output)} ')
                if _output:
                    for _line in _output:
                        _mount_point = _line.rstrip("\n")
                        _result = {}
                        _mount_cmd = f"/usr/bin/df -h {_mount_point} >/dev/null & echo PID=$!"
                        # bash - 4.2$ df - h / dev > / dev / null & echo PID =$!
                        # [1] 14509
                        # PID = 14509 <== grab this value using the command below
                        _node.mMultipleLineOutputWithSeparator(_mount_cmd, "=", _result)
                        aMountList.append({'host': aNodeName, 'mount': _mount_point, 'pid': _result['PID']})
                else:
                    self.mPatchLogError(f'\nNot able to load mounts for host: ({aNodeName})')

            except Exception as e:
                self.mPatchLogWarn(
                    f'Error occurred while checking for stale mounts on host {aNodeName}. Error : {str(e)}.')
                self.mPatchLogTrace(traceback.format_exc())
            finally:
                if _node.mIsConnected():
                    _node.mDisconnect()
            return

        _plist = ProcessManager()
        _mount_list = _plist.mGetManager().list()
        _connected_nodes = []
        try:
            for _host in aHostList:
                _p = ProcessStructure(mLoadMountonHost, [_host, _mount_list], _host)
                _p.mSetMaxExecutionTime(self.mGetStaleMountMaxThreadExecutionTimeoutSeconds())  # 30 min timeout
                _p.mSetJoinTimeout(self.mGetStaleMountThreadJoinTimeoutSeconds())
                _p.mSetLogTimeoutFx(self.mPatchLogInfo)
                _plist.mStartAppend(_p)

            _plist.mJoinProcess()

            if _plist.mGetStatus() == "killed":
                self.mPatchLogError('Timeout while executing check for Stale Mounts')

        except Exception as e:
            self.mPatchLogWarn(
                f'Error occurred while loading stale mounts. Error : {str(e)}.')
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            self.mPatchLogInfo("Fetched all mounts")

        return _mount_list

    def mHasStaleMounts(self, aHostList):

        if self.mIsMockEnv():
            return False, ""

        def mValidateMount(aNodeName, aMountPoint, aProcessId, aStaleMountList):
            _result = {}
            _cmd_validate_mounts = f"ps -o pid,ppid,lstart,etime,cmd {aProcessId};echo STATUS=$?"
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=aNodeName)
            try:

                # bash-4.2$ ps -o pid,ppid,lstart,etime,cmd 31707;echo STATUS=$?
                # PID  PPID                  STARTED     ELAPSED CMD
                # 31707 31702 Fri Oct  1 04:54:54 2021 18-23:43:03 bash
                # STATUS=0 <== stale Mount Point
                #
                # bash-4.2$ ps -o pid,ppid,lstart,etime,cmd 31708;echo STATUS=$?
                # PID  PPID                  STARTED     ELAPSED CMD
                # STATUS=1

                _node.mMultipleLineOutputWithSeparator(_cmd_validate_mounts, "=", _result)
                #if 0 , then retry and validate if the stale mount still exists for 2 minutes
                if int(_result['STATUS']) == 0:
                    self.mPatchLogInfo(
                        f" Possible Stale Mount for mountPoint {aMountPoint} since status is {_result['STATUS']} ")
                    _starttime = time.time()
                    _elapsed = 0
                    _timeout = self.mGetStaleMountCheckTimeoutSeconds()  # 2 minutes
                    _stale_mount_found = True
                    _iterations = 0
                    while _elapsed < _timeout:
                        time.sleep(3)  # Sleep for 3 seconds
                        _result = {}
                        _node.mMultipleLineOutputWithSeparator(_cmd_validate_mounts, "=", _result)
                        if int(_result['STATUS']) == 0:
                            if _iterations % 10 == 0:
                                self.mPatchLogInfo(
                                    f"Checking for stale mountpoint {aMountPoint} on host {aNodeName} in a loop")
                            _elapsed = time.time() - _starttime
                        else:
                            self.mPatchLogInfo(f"Mount point {aMountPoint}  is not stale after checking in loop ")
                            _stale_mount_found = False
                            break
                        _iterations += 1

                    if _stale_mount_found:
                        self.mPatchLogError(f"Stale Mount Point Detected for mount {aMountPoint} on host {aNodeName} ")
                        aStaleMountList.append({'host': aNodeName, 'StaleMount': aMountPoint})
                        _kill_mount_process_cmd = f"kill -9 {aProcessId}"
                        _in, _out, _err = _node.mExecuteCmd(_kill_mount_process_cmd)
                        _process_kill_err = _err.read().strip('\n')
                        if _process_kill_err:
                            self.mPatchLogError(f"Unable to kill the process id {str(aProcessId)} ")
                        else:
                            self.mPatchLogInfo(f"Killed Process id  {str(aProcessId)}")

            except Exception as e:
                self.mPatchLogWarn(
                    f'Error occurred while checking for stale mounts on host {aNodeName}. Error : {str(e)}.')
                self.mPatchLogTrace(traceback.format_exc())

            finally:
                 if _node.mIsConnected():
                     _node.mDisconnect()
            return

        _starttime = time.time()
        _processes = ProcessManager()
        _stale_mount_list = _processes.mGetManager().list()
        _mount_list = self.mGetMountList(aHostList)
        try:
            for _m in _mount_list:
                _host = _m['host']
                _pid = _m['pid']
                _mnt = _m['mount']

                _p = ProcessStructure(mValidateMount, [_host, _mnt, _pid, _stale_mount_list], f'{_host}-{_mnt}')
                _p.mSetMaxExecutionTime(self.mGetStaleMountMaxThreadExecutionTimeoutSeconds())  # 30 min timeout
                _p.mSetJoinTimeout(self.mGetStaleMountThreadJoinTimeoutSeconds())
                _p.mSetLogTimeoutFx(self.mPatchLogInfo)
                _processes.mStartAppend(_p)

            _processes.mJoinProcess()

            if _processes.mGetStatus() == "killed":
                # Proceed with patching and do not return an error in case of application timeout error for checking stale mounts
                _time_out_return_msg = "Timeout while executing check for stale mounts on hosts"
                self.mPatchLogWarn(_time_out_return_msg)
                return False, _time_out_return_msg

        except Exception as e:
            self.mPatchLogWarn(f'Error occurred while loading stale mounts. Error : {str(e)}.')
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            self.mPatchLogInfo("Checked all stale mounts")

        _return_msg = ""
        _stale_mount_list = list([x for x in _stale_mount_list if x['host']])
        if _stale_mount_list == []:
            self.mPatchLogInfo('*** No Stale Mounts Detected ***')
            return False, _return_msg
        else:
            for _js in _stale_mount_list:
                if _js["host"]:
                    _return_msg += "host:" + _js["host"]
                if _js["StaleMount"]:
                    _return_msg += ",StaleMount:" + _js["StaleMount"]+"; "

        _return_msg = _return_msg + ". Refer MOS Note 2829056.1 for more details." 
        self.mPatchLogInfo(f'*** Final return msg {_return_msg} ***')
        self.mPatchLogInfo(f"Total time taken to determine Stale Mounts in seconds : {str(time.time() - _starttime)} ")
        return True, _return_msg

    def mGetStaleMountNodeList(self, aListOfNodesToPatch):
        self.mPatchLogInfo("Preparing Node List to Check for Stale Mounts")
        _ret = PATCH_SUCCESS_EXIT_CODE
        _single_node_name = None
        _stale_mount_check_node_list = aListOfNodesToPatch[:]
        # In case of a single node upgrade, override with the single node
        if self.mGetIncludeNodeList() and len(self.mGetIncludeNodeList()) == 1:
            _single_node_name = self.mGetIncludeNodeList()[0]
            if _single_node_name is None:
                _ret = SINGLE_NODE_NAME_MISSING
                return _ret, []

            self.mPatchLogInfo(f"Single Node to be checked for Stale Mounts is  {_single_node_name} ")
            if _single_node_name in aListOfNodesToPatch:
                # Modify _stale_mount_check_node_list to have the single node only
                _stale_mount_check_node_list = [_single_node_name]

        self.mPatchLogInfo(
            f'*** Final _stale_mount_check_node_list {str(_stale_mount_check_node_list)} ***')
        return _ret, _stale_mount_check_node_list

    def mCheckSystemConsitency(self, aNodeList):
        '''
        Check whether system is in partially updated or not. If system is in
        bad state, then stop the patching so that we avoid taking bad backup.
        Return:
            Return value _system_is_in_valid_state:
                True : The system is in good condition.
                False: The system rpms are in invalid state.
            Return value _node_error_msg:
                Send error message for each nodes.
        '''

        _is_system_valid_state = True
        _node_error_msg = {}

        self.mPatchLogInfo("\n\n***System consistency check started.***\n")

        if self.mIsMockEnv():
            # in mock setup, skip rack specific operations
            return _is_system_valid_state, _node_error_msg

        additional_dbserver_cmd = ""
        # need to check if we need to pass encrypt script
        if self.mCheckConditionsForEncryptPatching() and mIsFSEncryptedList(aNodeList, self):
            additional_dbserver_cmd = f" --key-api {KEY_API}"

        for _node_name in aNodeList:
            _duplicate_rpm_found = False
            _incomplete_yum_txn_found = False

            self.mPatchLogInfo(f"System consistency check started on node = {_node_name}")

            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_node_name)

            # Read the infrapatching.conf to fetch the list of rpms to be excluded from duplicate rpm check
            _rpm_list="";
            exclude_dup_rpmchk_list = self.mGetRpmExcludeList()
            if self.mGetCurrentTargetType() == PATCH_DOM0:
                _rpm_list = exclude_dup_rpmchk_list['dom0']
            elif self.mGetCurrentTargetType() == PATCH_DOMU:
                _rpm_list = exclude_dup_rpmchk_list['domu']
            elif self.mGetCurrentTargetType() == PATCH_CELL:
                _rpm_list = exclude_dup_rpmchk_list['cell']
            _dup_rpmchk_list = '|'.join (_rpm_list)

            # Command for duplicate rpm validation.
            _cmd_1 = "rpm -qa --queryformat '%{ARCH} %{NAME}\n' | sort | uniq -c | sed -e 's/^ *//g'"
            _cmd_2 = f'| egrep -v "^1|{_dup_rpmchk_list}"'

            _cmd_dup_rpm = _cmd_1 + _cmd_2
            self.mPatchLogInfo(f"Command for duplicate rpm validation = {_cmd_dup_rpm}")
            '''
             Example of above command output:
                [root@slcs16adm04 ~]# rpm -qa --queryformat '%{ARCH} %{NAME}\n' | sort | uniq -c | sed -e 's/^ *//g'| egrep -v "^1 | kernel-uek|uptrack-updates|gpg-pubkey"
                2 x86_64 kernel-ueknano
            '''
            _i, _o, _e = _node.mExecuteCmd(_cmd_dup_rpm)
            _out = _o.readlines()
            if _out:
                self.mPatchLogError(f"Following duplicate RPMs found on {_node_name}:")
                self.mPatchLogError(f"{_out}")
                _duplicate_rpm_found = True

            # Command to find incomplete yum transactions
            _cmd_pending_yum_trans = "find /var/lib/yum -maxdepth 1 -type f -name 'transaction-all*' -not -name '*disabled'"
            self.mPatchLogInfo(f"Command for incomplete yum transaction = {_cmd_pending_yum_trans}")
            _i, _o, _e = _node.mExecuteCmd(_cmd_pending_yum_trans)
            _out = _o.readlines()
            if _out:
                self.mPatchLogError(f"\nFollowing incomplete yum transactions found on node {_node_name}:")
                self.mPatchLogError(f"{_out}")
                _incomplete_yum_txn_found = True

             # initialize _msg1 and _ms2 for each node validation.
            _msg1 = _msg2 = ""

            # If system is in bad state, stop the patching with appropriate error for the user to take action.
            if _duplicate_rpm_found and _incomplete_yum_txn_found:
                _msg1 = f"System is in partially updated state on node {_node_name}. Cannot take backup and hence not proceeding with patching."
                self.mPatchLogError(_msg1)
                _is_system_valid_state = False

                '''
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

                _cmd_exit_code_checker = f"/opt/oracle.SupportTools/dbserver_backup.sh --ignore-nfs-smbfs-mounts --check-rollback --get-backup-version {additional_dbserver_cmd}"
                   
                _i, _o, _e = _node.mExecuteCmd(_cmd_exit_code_checker)
                _exit_code = int(_node.mGetCmdExitStatus())

                if int(_exit_code) == 0:
                    _msg2 = " Contact Oracle Support and rollback to a previous good backup."
                elif int(_exit_code) == 1:
                    _msg2 = " Failed to get the rollback detail. Fix the active system image rpms and retry patching."
                elif int(_exit_code) == 2:
                    _msg2 = " Rollback version is same as the active partition. Fix the active system image rpms."
                elif int(_exit_code) == 3:
                    _msg2 = " Rollback is not available. Fix the active system images rpm and retry patching."
                else:
                    _msg2 = " Received invalid error code from get-backup-version command."

                self.mPatchLogError(_msg2)

            if _node.mIsConnected():
                _node.mDisconnect()

            _error_msg = _msg1 + _msg2
            # Update error message only when both duplicate and incosistency check failed.
            if _error_msg:
                _node_error_msg [_node_name] = _error_msg

            self.mPatchLogInfo(f"System consistency check completed on node = {_node_name}")

        # Update MOS Doc also if any issues found on any of the domUs.
        if _node_error_msg:
            _node_error_msg ["MOS_NOTE"] = "Refer MOS Note 2829056.1 for more details."

        self.mPatchLogInfo("***System consistency check completed.***\n")
        return _is_system_valid_state, _node_error_msg

    def mGetSwitchTargetVersion(self, aTargetType):
        """
        Gets the ibswitch,roceswitch firmware target version. EXADATA_IMAGE_IBSWITCH_UPGRADE_VERSION,
        EXADATA_IMAGE_ROCESWITCH_UPGRADE_VERSION and EXADATA_IMAGE_IBSWITCH_DOWNGRADE_VERSION,
        EXADATA_IMAGE_ROCESWITCH_ROLLBACK_VERSION  are env variables used in the patchmgr to set the
        ibswitch version.

        This function looks for these variables using printenv. If not found, then it takes the default
        value being used in patchmgr script.
        """

        self.mSetDom0ToPatchcellSwitches()
        if self.mIsMockEnv():
            # in mock setup, return empty list
            return ['', '']

        _upgrade_version = None
        _rollback_version = None
        _cmd1 = 'printenv|grep -a %s'
        _cmd2 = "grep -P 'export\s*%s\s*=' " + self.mGetCellIBPatchMgr()

        _dom0 = exaBoxNode(get_gcontext())
        _dom0.mConnect(aHost=self.mGetDom0ToPatchcellSwitches())

        self.mPatchLogInfo("\n\n**** Performing Switch target version validations. ****\n")
        def _parse_patchmgr(aVariable):
            _version = None

            try:
                _in, _out, _err = _dom0.mExecuteCmd(_cmd1 % aVariable)
                _output = _out.readlines()

                if _output:
                    if _output[0].strip() != '':
                        _re_out = re.match('.*%s=(.*)', _output[0].strip())
                        if _re_out:
                            _version = _re_out.groups()[0]
                else:
                    _in, _out, _err = _dom0.mExecuteCmd(_cmd2 % aVariable)
                    _output = _out.readlines()
                    if _output:
                        if _output[0].strip() != '':
                            _re_out = re.match('.*=(.*)', _output[0].strip())
                            if _re_out:
                                _version = _re_out.groups()[0]
            except Exception as e:
                self.mPatchLogWarn(f"Error while fetching ibswitch target version: {str(e)}")
                self.mPatchLogTrace(traceback.format_exc())

            return _version

        if aTargetType in [PATCH_IBSWITCH]:
            _upgrade_version = _parse_patchmgr('EXADATA_IMAGE_IBSWITCH_UPGRADE_VERSION')
            _rollback_version = _parse_patchmgr('EXADATA_IMAGE_IBSWITCH_DOWNGRADE_VERSION')
        elif aTargetType in [ PATCH_ROCESWITCH ]:
            _upgrade_version = _parse_patchmgr('EXADATA_IMAGE_ROCESWITCH_UPGRADE_VERSION')
            _rollback_version = _parse_patchmgr('EXADATA_IMAGE_ROCESWITCH_DOWNGRADE_VERSION')
        else:
            self.mPatchLogError(
                f"Invalid Target Type : {aTargetType}, Target can either be IBSwitches or RoceSwitches.")

        if _dom0.mIsConnected():
            _dom0.mDisconnect()
        self.mPatchLogInfo("**** Switch target version validations completed ****\n")
        return [_upgrade_version, _rollback_version]

    def mSetcellSwitchesBaseEnvironment(self):
        if self.mIsMockEnv():
            # in mock setup, skip rack specific operations
            return None

        #Sets all the variables used to select the dom0 that will run the patchmgr.
        if self.mGetCellSwitchesLocalPatchZip():
            # Name of the patch zip file (without the path)
            self.mSetCellIBPatchZipName(self.mGetCellSwitchesLocalPatchZip().split("/")[-1])
            # Base dir to copy the patch onto the remote dom0
            self.mSetCellSwitchesPatchBase(PATCH_BASE + self.mGetCellIBPatchZipName() + "/")
            # Full path to the zip patch on the remote dom0
            self.mSetCellSwitchesPatchZip(self.mGetCellSwitchesPatchBase() + \
                                                self.mGetCellIBPatchZipName())
            # Full path to the unziped patch folder on the remote dom0
            self.mSetCellSwitchesPatchBaseAfterUnzip(self.mGetCellSwitchesPatchBase() +
                                                              mGetFirstDirInZip(self.mGetCellSwitchesLocalPatchZip()))
            # Full path to the patchmgr script on the remote dom0
            self.mSetCellIBPatchMgr(self.mGetCellSwitchesPatchBaseAfterUnzip() + "patchmgr")
            self.__cells_switches_patch_zip_size_mb = int(os.path.getsize(self.mGetCellSwitchesLocalPatchZip())) >> 20
            # NOTE size is *2 of the zip file because we need to copy the zip, and unzip +
            # EXADATA_PATCH_WORKING_SPACE_MB for any logs generated?
            self.__cells_switches_patch_necessary_space_mb = int((self.__cells_switches_patch_zip_size_mb * 2 +
                                                                self.mGetExadataPatchWorkingSpaceMB()))
            self.mSetPatchmgrLogPathOnLaunchNode(self.mGetCellSwitchesPatchBaseAfterUnzip() + "patchmgr_log_" + self.mGetMasterReqId())
            self.mSetTargetVersion((self.mGetCellSwitchesLocalPatchZip()[::-1].split("/")[0])[::-1].replace(".patch","").replace(".zip",""))

    def mParsePatchmgrXml(self, patchmgrxml, aFinalLastCns):
        """
        Parse the patchmgr xml file which has the current status of the sofwate
        upgrade, running on DOM0. Also, create the json output for sending the
        CNS (Cloud Notification Service).
        """

        # flag to indicate final status of the target
        _target_succ_flag = True
        _target_na_flag = True

        # fill up the payload json for notificaiton
        _cnsjson = {}
        _cnsjson["data"] = {}
        _myuuid = uuid4().hex
        _cnsjson["httpRequestId"] = _myuuid

        _channel_info = {}
        _cnsjson["recipients"] = []
        _channel_info["channelType"] = "topics"

        _cnsjson["notificationType"] = {}
        _cnsjson["notificationType"]["componentId"] = "Patch_ExadataInfra_SM"
        _cnsjson["notificationType"]["id"] = "Patch_ExadataInfra_SMnotification_v1"

        _cnsjson["data"]["service"] = "ExadataPatch"
        _cnsjson["data"]["component"] = "Patch Exadata Infrastructure"
        _cnsjson["data"]["subject"] = "Patch Exadata Infrastructure Service Update"
        _cnsjson["data"]["event_post_time"] = time.strftime("%Y-%m-%d:%H.%M.%S %Z")
        _cnsjson["data"]["log_dir"] = self.mGetPatchmgrLogPathOnLaunchNode()
        _cnsjson["data"]["target_type"] = self.mGetTargetTypes()

        #Incorporate the master uuid and child uuid for the patching request
        _master_request_uuid, _child_request_uuid , _ , _json_patch_report= self.mGetAllPatchListDetails()
        if _master_request_uuid:
            self.mPatchLogInfo(f"mParsePatchmgrXml: Master request uuid for cnsjson in success case {_master_request_uuid}")
            _cnsjson["data"]["master_request_uuid"] = _master_request_uuid
        _cnsjson["data"]["child_request_uuid"] = _child_request_uuid
        try:
            if _json_patch_report:
                _json_patch_temp_data = json.loads(_json_patch_report)
                _json_patch_report_data = _json_patch_temp_data["data"]
                if _json_patch_report_data:
                    # Handle the case in case error_code, error_message, error_detail and error_action are  present in patch report
                    if "error_detail" in _json_patch_report_data:
                        error_detail = _json_patch_report_data["error_detail"]
                        if error_detail:
                            _cnsjson["data"]["error_detail"] = error_detail

                    if "error_code" in _json_patch_report_data:
                        error_code = _json_patch_report_data["error_code"]
                        if error_code:
                            _cnsjson["data"]["error_code"] = error_code

                    if "error_message" in _json_patch_report_data:
                        error_message = _json_patch_report_data["error_message"]
                        if error_message:
                            _cnsjson["data"]["error_message"] = error_message

                    if "error_action" in _json_patch_report_data:
                        error_action = _json_patch_report_data["error_action"]
                        if error_action:
                            _cnsjson["data"]["error_action"] = error_action
                            self.mPatchLogInfo(
                                f"mParsePatchmgrXml: Error action {error_action} is populated for Error Code {error_code} in mParsePatchmgrXml")

                    if "patch_mgr_error" in _json_patch_report_data:
                        patch_mgr_error = _json_patch_report_data["patch_mgr_error"]
                        if patch_mgr_error:
                            _cnsjson["data"]["patch_mgr_error"] = patch_mgr_error

                    if "time_profile_data" in _json_patch_report_data:
                        _time_profile_data = _json_patch_report_data["time_profile_data"]
                        if _time_profile_data:
                            _cnsjson["data"]["time_profile_data"] = _time_profile_data

                    if "node_progressing_status" in _json_patch_report_data:
                        _existing_node_progressing_status = _json_patch_report_data["node_progressing_status"]
                        if _existing_node_progressing_status:
                            _cnsjson["data"]["node_progressing_status"] = _existing_node_progressing_status
                else:
                    self.mPatchLogInfo('mParsePatchmgrXml: _json_patch_report_data is not present in mParsePatchmgrXml')
        except KeyError as k:
            self.mPatchLogWarn('mParsePatchmgrXml: json_report error code is not populated in mParsePatchmgrXml')
            self.mPatchLogTrace(traceback.format_exc())
        except Exception as e:
            self.mPatchLogWarn(f'mParsePatchmgrXml: In Exception: json_report fetch exception in mParsePatchmgrXml {str(e)} ')
            self.mPatchLogTrace(traceback.format_exc())

        # Fetch Global info
        _cnsjson["data"]["operation_type"] = self.mGetTask()
        _cnsjson["data"]["operation_style"] = self.mGetOpStyle()

        # Fetch cluster name
        _cnsjson["data"]["cluster_name"] = self.mGetRackName()
        # this is required for mandatory CNS check in CNSOperation.java
        _cnsjson["data"]["exadata_rack"] = self.mGetRackName()

        # These are required in ecra Patcher.java for updating the image version
        # and cabinet status
        _cnsjson["data"]["target_version"] = self.mGetTargetVersion()

        if self.mIsClusterLessUpgrade():
            _cnsjson["data"]["cluster_less"] = "yes"
        else:
            _cnsjson["data"]["cluster_less"] = "no"

        # update with exaunit id
        _cnsjson["data"]["exaunit_id"] = self.mGetExaunitId()
        # update with exaocid
        _cnsjson["data"]["exa_ocid"] = self.mGetExaOcid()
        # update with exasplice
        if self.mIsExaSplice():
            _cnsjson["data"]["exa_splice"] = 'yes'
        else:
            _cnsjson["data"]["exa_splice"] = 'no'

        # For cells, doms, dom0s, ibswitches
        _cnsjson["data"][self.mGetCurrentTargetType() + 's'] = []

        # To parse node target type within ptachmgr xml and also update
        # topic/id appropriately for each target so that subscriber can also
        # opt CNS for any target(s), individually, while they can also opt
        # parent one 'critical.patch_of_exadata_infrastructure' to get all CNS.
        _node_type = ""
        if self.mGetCurrentTargetType() == PATCH_CELL:
            _node_type = 'Cell'
            _channel_info["topicId"] = "critical.patch_of_exadata_infrastructure.patch_Exadata_cell"
            _cnsjson["data"]["topic"] = "critical.patch_of_exadata_infrastructure.patch_Exadata_cell"
        elif self.mGetCurrentTargetType() == PATCH_DOMU:
            _node_type = 'Compute_Node'
            _channel_info["topicId"] = "critical.patch_of_exadata_infrastructure.patch_Exadata_domu"
            _cnsjson["data"]["topic"] = "critical.patch_of_exadata_infrastructure.patch_Exadata_domu"
        elif self.mGetCurrentTargetType() == PATCH_DOM0:
            _node_type = 'Compute_Node'
            _channel_info["topicId"] = "critical.patch_of_exadata_infrastructure.patch_Exadata_dom0"
            _cnsjson["data"]["topic"] = "critical.patch_of_exadata_infrastructure.patch_Exadata_dom0"
        elif self.mGetCurrentTargetType() == PATCH_IBSWITCH:
            _node_type = 'IBSwitch'
            _channel_info["topicId"] = "critical.patch_of_exadata_infrastructure.patch_Exadata_ibswitch"
            _cnsjson["data"]["topic"] = "critical.patch_of_exadata_infrastructure.patch_Exadata_ibswitch"
        elif self.mGetCurrentTargetType() == PATCH_ROCESWITCH:
            _node_type = 'ROCESwitch'
            _channel_info["topicId"] = "critical.patch_of_exadata_infrastructure.patch_Exadata_roceswitch"
            _cnsjson["data"]["topic"] = "critical.patch_of_exadata_infrastructure.patch_Exadata_roceswitch"

        # Patch Status Json parse and get the
        # json payload Manipulate node_progress_status_json
        _node_progressing_status = self.mUpdatePatchProgressStatus(aPatchmgrXmlData=patchmgrxml, aNodeType=_node_type)
        if _node_progressing_status:
            _cnsjson["data"]["node_progressing_status"]  = _node_progressing_status

        # Get into the root of patchmgr xml notification and read launch node.
        try:
            _root = ET.fromstring(patchmgrxml)
            _launch_node = _root.findall('./Global_info/Launch_Node/Transition')
            if _launch_node:
                _cnsjson["data"]["launch_node"] = _launch_node[0].attrib['VALUE']

            '''
              Below code parses the patchmgr xml file and gets _node_type 
              details. It might require extensive testing for all patch 
              targets and not suggested to merge changes as part of 
              34000386 and can be taken care as part of future transactions.

                for _tmp_node in _root.findall('.//From_Version/..'):
                    _switch_node_type = _tmp_node.tag
                    if _switch_node_type:
                        self.mPatchLogInfo("Node type tag for Switch from notification xml is %s." % _switch_node_type)
                        _node_type = _switch_node_type
                    else:
                        self.mPatchLogInfo("Node type tag by definition is %s." % _node_type)
                    break
            '''

            for _each_node_type in _root.findall('./' + _node_type):
                _node = {}
                _node["operation_target"] = _each_node_type.attrib['NAME']

                _from_ver = _each_node_type.findall('./From_Version/Transition')
                if _from_ver:
                    _node["from_version"] = _from_ver[0].attrib['VALUE']

                _to_ver = _each_node_type.findall('./To_Version/Transition')
                if _to_ver:
                    _node["to_version"] = _to_ver[0].attrib['VALUE']

                # Goto last patch transition state
                _cur_pstate_tran = None
                for _each_pstate_tran in _each_node_type.findall('./Patch_State/Transition'):
                    _cur_pstate_tran = _each_pstate_tran

                if _cur_pstate_tran:
                    _node["operation_status"] = _cur_pstate_tran.attrib['VALUE']
                    _node["timestamp"] = _cur_pstate_tran.attrib['LAST_UPDATE_TIMESTAMP']
                    _cnsjson["data"][self.mGetCurrentTargetType() + 's'].append(_node)

                    # Check over all status (as Success or 'Not Attempted' or Failed)
                    # of the node target, which will be used for final notification
                    if aFinalLastCns:
                        _target_succ_flag = _target_succ_flag and (_cur_pstate_tran.attrib['VALUE'] == 'Succeeded')
                        _target_na_flag = _target_na_flag and (_cur_pstate_tran.attrib['VALUE'] == 'Not Attempted')
                else:
                    self.mPatchLogWarn('mParsePatchmgrXml: Current state of patch notification is not available as of now. Displaying last updated status.')
        except Exception as e:
            self.mPatchLogWarn(f'mParsePatchmgrXml: Error in parsing Patch Manager Notification XML. Error is : {str(e)}\n')
            self.mPatchLogTrace(traceback.format_exc())

        # Set the topic preference for the final notification of the cluster
        if aFinalLastCns:
            self.mSetTopicForCns(_channel_info, _cnsjson, _target_succ_flag, _target_na_flag)

        # Append channel info to recipients[]
        _cnsjson["recipients"].append(_channel_info)

        return _cnsjson

    def mSetTopicForCns(self, channel_info, cnsjson, target_succ_flag, target_na_flag):
        """
        Set the topic preference for the final notification
        """

        # verify and set Success status
        if target_succ_flag and self.mGetCurrentTargetType() == PATCH_DOMU:
            channel_info['topicId'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_domu.SUCCESS"
            cnsjson['data']['topic'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_domu.SUCCESS"
        elif target_succ_flag and self.mGetCurrentTargetType() == PATCH_DOM0:
            channel_info['topicId'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_dom0.SUCCESS"
            cnsjson['data']['topic'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_dom0.SUCCESS"
        elif target_succ_flag and self.mGetCurrentTargetType() == PATCH_CELL:
            channel_info['topicId'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_cell.SUCCESS"
            cnsjson['data']['topic'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_cell.SUCCESS"
        elif target_succ_flag and self.mGetCurrentTargetType() == PATCH_IBSWITCH:
            channel_info['topicId'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_ibswitch.SUCCESS"
            cnsjson['data']['topic'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_ibswitch.SUCCESS"
        elif target_succ_flag and self.mGetCurrentTargetType() == PATCH_ROCESWITCH:
            channel_info['topicId'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_roceswitch.SUCCESS"
            cnsjson['data']['topic'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_roceswitch.SUCCESS"

        # verify and set Not Attempted status
        elif target_na_flag and self.mGetCurrentTargetType() == PATCH_DOMU:
            channel_info['topicId'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_domu.NOTAPPLICABLE"
            cnsjson['data']['topic'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_domu.NOTAPPLICABLE"
        elif target_na_flag and self.mGetCurrentTargetType() == PATCH_DOM0:
            channel_info['topicId'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_dom0.NOTAPPLICABLE"
            cnsjson['data']['topic'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_dom0.NOTAPPLICABLE"
        elif target_na_flag and self.mGetCurrentTargetType() == PATCH_CELL:
            channel_info['topicId'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_cell.NOTAPPLICABLE"
            cnsjson['data']['topic'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_cell.NOTAPPLICABLE"
        elif target_na_flag and self.mGetCurrentTargetType() == PATCH_IBSWITCH:
            channel_info['topicId'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_ibswitch.NOTAPPLICABLE"
            cnsjson['data']['topic'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_ibswitch.NOTAPPLICABLE"
        elif target_na_flag and self.mGetCurrentTargetType() == PATCH_ROCESWITCH:
            channel_info['topicId'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_roceswitch.NOTAPPLICABLE"
            cnsjson['data']['topic'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_roceswitch.NOTAPPLICABLE"

        # verify and set Fail status
        elif self.mGetCurrentTargetType() == PATCH_DOMU:
            channel_info['topicId'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_domu.FAIL"
            cnsjson['data']['topic'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_domu.FAIL"
        elif self.mGetCurrentTargetType() == PATCH_DOM0:
            channel_info['topicId'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_dom0.FAIL"
            cnsjson['data']['topic'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_dom0.FAIL"
        elif self.mGetCurrentTargetType() == PATCH_CELL:
            channel_info['topicId'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_cell.FAIL"
            cnsjson['data']['topic'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_cell.FAIL"
        elif self.mGetCurrentTargetType() == PATCH_IBSWITCH:
            channel_info['topicId'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_ibswitch.FAIL"
            cnsjson['data']['topic'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_ibswitch.FAIL"
        elif self.mGetCurrentTargetType() == PATCH_ROCESWITCH:
            channel_info['topicId'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_roceswitch.FAIL"
            cnsjson['data']['topic'] = "critical.patch_of_exadata_infrastructure.patch_Exadata_roceswitch.FAIL"

    def mGetPatchMgrDiagFiles(self, aDom0, aNodeType, aNodeList, aRemotePath):
        """
        Copies the last patchmgr_files found for various node types to /log.
        Presently handles the CELLs and DOMUs
        For CELLS, it copies the files from DOM0 to ExaCloud logs
        For DOMUs, along with the files from DOM0 where patchmrg ran it also
        gets the files from DOMUs.
        """

        # First get the files from the DOM0 which ran the patchmgr
        if aNodeType == PATCH_CELL:

            _cmd_list_diag_files = f'find {aRemotePath} -name "patchmgr_diag_*"'
            _cell_diag_files = {}

            for _cell in aNodeList:
                _cell_diag_files[_cell] = {'path': '',
                                           'group': []}

            ### IMPORTANT ###
            # This implementation always will copy the most recent patmgr file
            # found for a given cell. Is there a certain way to know which files
            # were created during a cleanup task?
            ### -------- ###

            _node = exaBoxNode(get_gcontext())
            self.mSetConnectionUser(_node)
            _node.mConnect(aHost=aDom0)

            try:

                # Find all the patchmgr_diag* files availables. It is possible
                # that this patchmgr was used before so it is important to get
                # the last files generated
                _in, _out, _err = _node.mExecuteCmd(_cmd_list_diag_files)
                _output = _out.readlines()

                if _output:
                    # For each files, we parse its name (which has the date of
                    # creation).
                    for _o in _output:
                        _file = _o.strip().split("/")[-1]
                        _re_out = re.match("patchmgr_diag_(.+)_([0-9]{4})-" \
                                           "([0-9]{2})-([0-9]{2})_([0-9]{2})_" \
                                           "([0-9]{2})_([0-9]{2})\.tar\.bz2", _file)
                        if _re_out:
                            _group = _re_out.groups()
                            _current = ''
                            for _cell in aNodeList:
                                if _cell.startswith(_group[0]):
                                    _current = _cell
                                    break

                            # For each cell, we get only the most recent
                            # patchmgr_diag file created
                            if _current:
                                _update = True
                                if _cell_diag_files[_current]['group']:
                                    for _ind in range(1, 7):
                                        if _group[_ind] != _cell_diag_files[_current]['group'][_ind]:
                                            if _group[_ind] < _cell_diag_files[_current]['group'][_ind]:
                                                _update = False
                                            break

                                if _update:
                                    _cell_diag_files[_current]['path'] = _file
                                    _cell_diag_files[_current]['group'] = _group

                # Each patchmgr file is copied from the dom0 to the localhost.
                self.mPatchLogInfo(f"Collecting diagnostics logs from: {aRemotePath} to: {self.mGetLogPath()}")
                for _cell in _cell_diag_files:
                    if _cell_diag_files[_cell]['path'] != '':
                        if _node.mFileExists(os.path.join(aRemotePath, _cell_diag_files[_cell]['path'])):
                            self.mSetListOfLogsCopiedToExacloudHost(os.path.join(aRemotePath, _cell_diag_files[_cell]['path']))
                            _node.mCopy2Local(os.path.join(aRemotePath, _cell_diag_files[_cell]['path']) ,
                                              os.path.join(self.mGetLogPath(), _cell_diag_files[_cell]['path']))
                    else:
                        self.mPatchLogInfo(f"No diagnosis files found for cell {_cell}")

            except Exception as e:
                self.mPatchLogWarn(f'Error while copying cell diagnosis files: {str(e)}')
                self.mPatchLogTrace(traceback.format_exc())
            if _node.mIsConnected():
                _node.mDisconnect()

        if aNodeType == PATCH_DOMU or aNodeType == PATCH_DOM0:
            _node = exaBoxNode(get_gcontext())
            self.mSetConnectionUser(_node)
            _node.mConnect(aHost=aDom0)
            aRemotePath = self.mGetPatchmgrLogPathOnLaunchNode()
            _patchmgr_diag_tar = aRemotePath.split('/')[-1] + ".tar"

            self.mPatchLogInfo(
                f"aRemotePath = {aRemotePath}\n_patchmgr_diag_tar = {_patchmgr_diag_tar}\n dirname = {os.path.dirname(aRemotePath)}\n basename = {os.path.basename(aRemotePath)}\n")

            # tar the diagnostic files
            tar_cmd = f"cd {os.path.dirname(aRemotePath)}; tar cvf {_patchmgr_diag_tar} {os.path.basename(aRemotePath)};"
            try:
                self.mPatchLogInfo(f"Taring patch manager diagnosis files from DOM0 {aDom0}\n cmd={tar_cmd}")

                _in, _out, _err = _node.mExecuteCmd(tar_cmd)
            except Exception as e:
                self.mPatchLogWarn(f"Error while taring the diagnosis files({tar_cmd}) from DOM0 {str(e)}")
                self.mPatchLogTrace(traceback.format_exc())

            # copy the tar to local
            try:
                if _node.mFileExists(os.path.dirname(aRemotePath) + '/' + _patchmgr_diag_tar):
                    self.mSetListOfLogsCopiedToExacloudHost(os.path.join(aRemotePath, _patchmgr_diag_tar))
                    _node.mCopy2Local(os.path.dirname(aRemotePath) + '/' + _patchmgr_diag_tar,
                                      os.path.join(self.mGetLogPath(), _patchmgr_diag_tar))
                else:
                    self.mPatchLogWarn(
                        f'{os.path.dirname(aRemotePath) + "/" + _patchmgr_diag_tar} not found on the launch node : {aDom0}')
            except Exception as e:
                self.mPatchLogWarn(
                    f"Error while copying the diagnosis files from DOM0 error={str(e)}\n rfile={os.path.dirname(aRemotePath) + '/' + _patchmgr_diag_tar}\n lfile={os.path.join(self.mGetLogPath(), _patchmgr_diag_tar)} to exacloud location - {self.mGetLogPath()}")
                self.mPatchLogTrace(traceback.format_exc())
                ls_cmd = f"ls {os.path.dirname(aRemotePath)}"
                _in, _out, _err = _node.mExecuteCmd(ls_cmd)
                self.mPatchLogInfo(
                    f"We have following files in dir ({_out.readlines()}) in node ({aDom0}) that dont have the exected {_patchmgr_diag_tar} ")
                                      
            # remove the tar file
            try:
                _in, _out, _err = _node.mExecuteCmd(f"cd {os.path.dirname(aRemotePath)}; rm -f {_patchmgr_diag_tar};")
            except Exception as e:
                self.mPatchLogWarn(f"Error while removing the diagnosis files from DOM0 {str(e)}")
                self.mPatchLogTrace(traceback.format_exc())

        # secondly get the files from the individual DOMUs
        if aNodeType == PATCH_DOMU:
            for _domu in aNodeList:
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_domu)
                _cmd_list_diag_files = (
                    f'find {"/var/log/cellos"} -type f -name "*package*"|grep -v tmp')
                self.mPatchLogInfo(
                    f"Copying patch manager diagnosis files from DOMU {_domu} to exacloud location - {self.mGetLogPath()}")
                try:
                    _in, _out, _err = _node.mExecuteCmd(_cmd_list_diag_files)
                    _output = _out.readlines()

                    if _output:
                        for _o in _output:
                            _file = _o.strip().split("/")[-1]
                            if _node.mFileExists(os.path.join('/var/log/cellos/' ,_file)):
                                self.mSetListOfLogsCopiedToExacloudHost(os.path.join('/var/log/cellos/' ,_file))
                                _node.mCopy2Local(os.path.join('/var/log/cellos/' ,_file) , os.path.join(self.mGetLogPath() , _domu + '.' + _file))
                            else:
                               self.mPatchLogWarn(
                                   f'{os.path.join("/var/log/cellos/", _file)} not found on the launch node : {_domu}')
                except Exception as e:
                    self.mPatchLogWarn(
                        f'Error while copying DOMU diagnosis files: {str(e)} from {_domu} node to exacloud location - {self.mGetLogPath()}.')
                    self.mPatchLogTrace(traceback.format_exc())

                if _node.mIsConnected():
                    _node.mDisconnect()

        return

    # Clean environment after any operation
    def mCleanEnvironment(self, aDom0, aNodesList, aListFilePath, aBaseDir, aLogDir, aNodeType, aPatchExitStatus):
        """
        Deletes input files and passwordless ssh between nodes. It will also
        copy the log files from the remote dom0 to the local log directory.
        """

        self.mPatchLogInfo(f"Copying diagnostic logs to exacloud: {self.mGetLogPath()}")

        # Update status
        self.mUpdatePatchStatus(True, STEP_CLEAN_ENV + '_' + aNodeType)

        _std_code = ''
        if aNodeType == PATCH_DOM0:
            _std_code = str(self.mGetDom0FileCode(aDom0, aBaseDir))

        # Get .stdout and .stderr log files. Patchmgr logs present in -log_dir
        # in case of ibswitch upgrade (aLogDir), otherwise, those present in
        # base directory which has latest content
        if aNodeType in [ PATCH_IBSWITCH, PATCH_ROCESWITCH, PATCH_CELL]:
            self.mGetPatchMgrOutFiles(aDom0, aLogDir, _std_code)
        else:
            self.mGetPatchMgrOutFiles(aDom0, aBaseDir, _std_code)

        '''
         Collect patchmgr diag logs for debugging only
         when the final exit code from patch operation 
         is not PATCH_SUCCESS_EXIT_CODE.
        '''
        if aPatchExitStatus != PATCH_SUCCESS_EXIT_CODE:
            self.mGetPatchMgrDiagFiles(aDom0, aNodeType, aNodesList, aLogDir)
        else:
            self.mPatchLogInfo("Patchmgr diag logs are not collected in case of a successful infra patch operation.")

        # Get patchmgr console that we generate using nohup
        self.mGetPatchMgrMiscLogFiles(aDom0, aLogDir)

        # Get <cellname>.log files from the patchmgr_log_<date> location
        if aNodeType == PATCH_CELL:
            self.mGetCellLogs(aDom0, aNodesList, aLogDir)

        '''
         Example snippet of aBaseDir and aLogDir.

         aBaseDir : /EXAVMIMAGES/21.1.0.0.0.210319.switch.patch.zip/patch_switch_21.1.0.0.0.210319/ 
         aLogDir : /EXAVMIMAGES/21.1.0.0.0.210319.switch.patch.zip/patch_switch_21.1.0.0.0.210319/patchmgr_log_db9dd643-cffa-4448-95f0-c530835da603

         When appropriate logs are generate under the above locations, logs are copied onto exacloud 
         log location as below.

         aBaseDir :
         
            2021-07-26 07:46:37-0700 - RoceSwitchHandler - INFO - Copying switch_admin.log
            file from node - scaqan17adm01.us.oracle.com , location -
            /EXAVMIMAGES/21.2.2.0.0.210709.switch.patch.zip/patch_switch_21.2.2.0.0.210709/
         
         aLogDir :

            2021-08-16 01:34:06-0700 - INFO - SwitchHandler - INFO - Copying
            upgradeIBSwitch.log file from node - slcs27adm03.us.oracle.com , location -
            /EXAVMIMAGES/21.1.0.0.0.210319.switch.patch.zip/patch_switch_21.1.0.0.0.210319/
            patchmgr_log_db9dd643-cffa-4448-95f0-c530835da603

        '''

        # Get RoceSwitch specific logs
        if aNodeType == PATCH_ROCESWITCH:
            self.mGetUpgradeROCESwitchOutFiles(aDom0, aLogDir, aBaseDir)

        # Get ibswitch specific logs
        if aNodeType == PATCH_IBSWITCH:
            self.mGetUpgradeIBSwitchOutFiles(aDom0, aLogDir)

        # Print all the log details at the end of log files copy.
        self.mPrintPatchmgrLogFormattedDetails()  

        '''
         Clean ssh configuration

         Note : Currently passwordless ssh cleanup is not done for the
                Roceswitches by default.
        '''
        if aNodeType != PATCH_ROCESWITCH and self.__ssh_env_setup_switches_cell:
            self.__ssh_env_setup_switches_cell.mCleanSSHPasswordless(aDom0, aNodesList)

        '''
         Below checks are applicable to Cell and Switch targets 
         and are used for validating ssh connectivity post patching
         activity is complete during the passwdless ssh cleanup stage.

         ssh validation on a roceswitch during postcheck 
         are run only if revoke_roceswitch_passwdless_ssh_settings 
         is set to True in infrapatching.conf
        '''
        if self.mGetCurrentTargetType() == PATCH_ROCESWITCH and not self.mGetRevokeRoceswitchPasswdlessSshSettings():
            self.mPatchLogInfo("Ssh validations are not performed post roceswitch patching when revoke_roceswitch_passwdless_ssh_settings parameter in infrapathcing.conf is set to False.")
        else:
            self.mPatchLogInfo(f"Passwordless ssh validation performed between {str(aNodesList)} and {aDom0}")
            self.mGetCluPatchCheck().mVerifyPatchmgrSshConnectivityBetweenExadataHosts(aNodesList, aDom0,
                                                                        aStage="PostPatch")

        # Delete input file
        self.mDeleteNodesFile(aListFilePath, aDom0)

    def mGetUpgradeROCESwitchOutFiles(self, aDom0, aLogDir, aBaseDir):
        """
        Copies switch_admin.trc and switch_admin.log files
        """

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDom0)

        '''
         In some of the Exadata versions, switch admin logs
         are stored under patchmgr log location and in other
         exadata versions, it is stored under patchmgr base
         directory. Below code looks for the logs in both the
         locations and copies it to Exacloud log location.
        '''
        try:
            _switch_upgrade_log_logdir = os.path.join(aLogDir, ROCESWITCH_LOG)
            _switch_upgrade_trc_logdir = os.path.join(aLogDir, ROCESWITCH_TRC)
            _switch_upgrade_log_basedir = os.path.join(aBaseDir, ROCESWITCH_LOG)
            _switch_upgrade_trc_basedir = os.path.join(aBaseDir, ROCESWITCH_TRC)
            _switch_upgrade_log_local = os.path.join(self.mGetLogPath(), ROCESWITCH_LOG)
            _switch_upgrade_trc_local = os.path.join(self.mGetLogPath(), ROCESWITCH_TRC)

            if _node.mFileExists(_switch_upgrade_log_logdir):
                self.mSetListOfLogsCopiedToExacloudHost(_switch_upgrade_log_logdir)
                _node.mCopy2Local(_switch_upgrade_log_logdir, _switch_upgrade_log_local)
            elif _node.mFileExists(_switch_upgrade_log_basedir):
                self.mSetListOfLogsCopiedToExacloudHost(_switch_upgrade_log_basedir)
                _node.mCopy2Local(_switch_upgrade_log_basedir, _switch_upgrade_log_local)
            else:
                self.mPatchLogWarn(f"Unable to locate : {ROCESWITCH_LOG} on Launch node : {aDom0}")

            if _node.mFileExists(_switch_upgrade_trc_logdir):
                self.mSetListOfLogsCopiedToExacloudHost(_switch_upgrade_trc_logdir)
                _node.mCopy2Local(_switch_upgrade_trc_logdir, _switch_upgrade_trc_local)
            elif _node.mFileExists(_switch_upgrade_trc_basedir):
                self.mSetListOfLogsCopiedToExacloudHost(_switch_upgrade_trc_basedir)
                _node.mCopy2Local(_switch_upgrade_trc_basedir, _switch_upgrade_trc_local)
            else:
                self.mPatchLogWarn(f"Unable to locate : {ROCESWITCH_TRC} on Launch node : {aDom0}")

        except Exception as e:
            self.mPatchLogWarn(f'Error while copying {ROCESWITCH_LOG} and {ROCESWITCH_TRC}: {str(e)}')
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()

    def mGetNodeList(self, aFilePath, aDom0):
        """
        Read the list of nodes which are eligible for patching
        """
        _list_of_nodes = []

        try:
            self.mPatchLogInfo(f"Reading patch input file: {aFilePath}")
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=aDom0)
            _i, _o, _e = _node.mExecuteCmd(f'cat {aFilePath}')

            _node_list = _o.readlines()

            if _node_list:
                for _cell_node in _node_list:
                    _list_of_nodes.append(_cell_node.replace("\n", "").strip())
            else:
                self.mPatchLogWarn("Warning: No nodes found in the input file")

            if _node.mIsConnected(): 
                _node.mDisconnect()

        except Exception as e:
            raise Exception(
                f'Error while reading list of cell nodes. Node = {aDom0}, input file = {aFilePath}. Error: {str(e)}')
            self.mPatchLogTrace(traceback.format_exc())
        return _list_of_nodes

    def mGetUpgradeIBSwitchOutFiles(self, aDom0, aRemotePath):
        """
        Copies upgradeIBSwitch.trc and upgradeIBSwitch.log files
        """

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDom0)

        try:
            if _node.mFileExists(os.path.join(aRemotePath, IBSWITCH_LOG)):
                self.mSetListOfLogsCopiedToExacloudHost(os.path.join(aRemotePath, IBSWITCH_LOG))
                _node.mCopy2Local(os.path.join(aRemotePath, IBSWITCH_LOG), os.path.join(self.mGetLogPath(), IBSWITCH_LOG))
            else:
                self.mPatchLogWarn(f'{os.path.join(aRemotePath, IBSWITCH_LOG)} not found on the launch node : {aDom0}')

            if _node.mFileExists(os.path.join(aRemotePath, IBSWITCH_TRC)):
                self.mSetListOfLogsCopiedToExacloudHost(os.path.join(aRemotePath, IBSWITCH_TRC))
                _node.mCopy2Local(os.path.join(aRemotePath, IBSWITCH_TRC), os.path.join(self.mGetLogPath(),IBSWITCH_TRC))
            else:
                self.mPatchLogWarn(f'{os.path.join(aRemotePath, IBSWITCH_TRC)} not found on the launch node : {aDom0}')

        except Exception as e:
            self.mPatchLogWarn(
                f'Error while copying {IBSWITCH_LOG} and {IBSWITCH_TRC}: {str(e)} to exacloud location - {self.mGetLogPath()}')
            self.mPatchLogTrace(traceback.format_exc())

        if _node.mIsConnected():
            _node.mDisconnect()

    def mGetCellLogs(self, aDom0, aNodesList, aLogDir):
        """
        Copy cell patching diagnostic files with naming convention as
        <cellhostname>.log and these logs would be generated during cell upgrade
        and same needs to be copied toi ECRA from launch node.
        """

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDom0)

        try:
            # Copy <cellnmae>.log files from patchmgr stage location on Dom0 to local node.
            for _cell in aNodesList:
                if _node.mFileExists(os.path.join(aLogDir, _cell + '.' + 'log')):
                    self.mSetListOfLogsCopiedToExacloudHost(os.path.join(aLogDir, _cell + ".log"))
                    _node.mCopy2Local(os.path.join(aLogDir, _cell + '.' + 'log'),
                                      os.path.join(self.mGetLogPath(), _cell + '.' + 'log'))
                else:
                    self.mPatchLogWarn(
                        f'{os.path.join(aLogDir, _cell + "." + "log")} not found on the launch node : {aDom0}')
        except Exception as e:
            self.mPatchLogWarn(
                f'Error while copying {_cell}.log file from node - {aLogDir} , location - {str(e)} to exacloud location - {self.mGetLogPath()}')
            self.mPatchLogTrace(traceback.format_exc())

        # Disconnect Dom0
        if _node.mIsConnected():
            _node.mDisconnect()

        return


    def mGetPatchMgrMiscLogFiles(self, aDom0, aRemotePath, aTaskType=None,aNodesList=[]):
        """
        Copies PatchmgrConsole.out to /log
        """

        _misc_files = [PATCH_CONSOLE_LOG]

        _context = get_gcontext()
        _oeda_path_logs = os.path.join(_context.mGetOEDAPath(), "log")

        _node = exaBoxNode(_context)
        self.mSetConnectionUser(_node)
        _node.mConnect(aHost=aDom0)

        '''
         If the applied patch is exaplice, collect exaplice
         specific diagnostic information.

         2021-01-19 13:31:08+0000 - Dom0Handler - INFO - - <dbnode_name>_exasplice_driver.log
         2021-01-19 13:31:08+0000 - Dom0Handler - INFO - - <dbnode_name>_exasplice_driver.trc
         2021-01-19 13:31:08+0000 - Dom0Handler - INFO - - <dbnode_name>_dbnodeupdate.log
         2021-01-19 13:31:08+0000 - Dom0Handler - INFO - - patchmgr.log
        '''
        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsExaspliceNot24') and \
                aTaskType in [ TASK_PATCH, TASK_PREREQ_CHECK ]: 

            for aNode in aNodesList:

                EXASPLICE_DRIVE_LOG = f"{aNode}_exasplice_driver.log"
                EXASPLICE_DRIVE_TRC = f"{aNode}_exasplice_driver.trc"

                for _exasplice_logs in [ EXASPLICE_DRIVE_LOG, EXASPLICE_DRIVE_TRC ]:
                    try:
                        if _node.mFileExists(os.path.join(aRemotePath , _exasplice_logs)):
                            self.mSetListOfLogsCopiedToExacloudHost(os.path.join(aRemotePath, _exasplice_logs))
                            _node.mCopy2Local(os.path.join(aRemotePath , _exasplice_logs),
                                            os.path.join(self.mGetLogPath() , _exasplice_logs + '.' + \
                                              self.mGetCurrentTargetType()))
                            # symlinks used for chainsaw2/lumberjack
                            #  ln -s <file> <symlink>
                            # example:
                            #   ln -s /opt/oci/exacc/exacloud/oeda/requests/f829406a-15cb-11ec-8770-0010e0efc742/log/patchmgr_logs/nodename_exasplice_driver.log
                            #         /opt/oci/exacc/exacloud/oeda/log/1ef39fbd-9be8-450c-8512-1e633cdf89b5_nodename_exasplice_driver.log
                            #
                            _in, _out, _err = self.mGetCluControl().mExecuteCmd(
                                f"ln -s {os.path.join(self.mGetLogPath(), _exasplice_logs + '.' + self.mGetCurrentTargetType())} {os.path.join(_oeda_path_logs, self.mGetMasterReqId() + '_' + _exasplice_logs + '.' + self.mGetCurrentTargetType())}")
                        else:
                            self.mPatchLogWarn(
                                f'{os.path.join(self.mGetLogPath(), _exasplice_logs + "." + self.mGetCurrentTargetType())} not found on the launch node : {aDom0}')
                    except Exception as e:
                        self.mPatchLogWarn(
                            f'Error while copying exasplice log  {_exasplice_logs}: {str(e)} from node - {aDom0} , location - {aRemotePath} to exacloud location - {self.mGetLogPath()}')
                        self.mPatchLogTrace(traceback.format_exc())

        for _misc_file in _misc_files:
            try:
                if _node.mFileExists(os.path.join(aRemotePath ,_misc_file)):
                    self.mSetListOfLogsCopiedToExacloudHost(os.path.join(aRemotePath, _misc_file))
                    _node.mCopy2Local(os.path.join(aRemotePath ,_misc_file),
                                      os.path.join(self.mGetLogPath() , _misc_file + '.' + \
                                      self.mGetCurrentTargetType()))
                    # symlinks used for chainsaw2/lumberjack
                    #  ln -s <file> <symlink>
                    # example:
                    #   ln -s /opt/oci/exacc/exacloud/oeda/requests/f829406a-15cb-11ec-8770-0010e0efc742/log/patchmgr_logs/patchmgr.log
                    #         /opt/oci/exacc/exacloud/oeda/log/1ef39fbd-9be8-450c-8512-1e633cdf89b5_patchmgr.log
                    #
                    _in, _out, _err = self.mGetCluControl().mExecuteCmd(
                        f"ln -s {os.path.join(self.mGetLogPath(), _misc_file + '.' + self.mGetCurrentTargetType())} {os.path.join(_oeda_path_logs, self.mGetMasterReqId() + '_' + _misc_file + '.' + self.mGetCurrentTargetType())}")
                else:
                    self.mPatchLogWarn(
                        f'{os.path.join(self.mGetLogPath(), _misc_file + "." + self.mGetCurrentTargetType())} not found on the launch node : {aDom0}')
            except Exception as e:
                self.mPatchLogWarn(
                    f'Error while copying miscellaneous file console log {_misc_file}: {str(e)} from node - {aDom0} , location - {aRemotePath} to exacloud location - {self.mGetLogPath()}')
                self.mPatchLogTrace(traceback.format_exc())
        if _node.mIsConnected(): 
            _node.mDisconnect()

    def mGetDom0FileCode(self, aDom0, aRemotePath):
        """
        Gets the most recent code. File name is patchmgr.stdout.<code>
        """
        _code = ''
        _output = []
        _node = None
        if aRemotePath[-1] != '/':
            aRemotePath += '/'
        if  self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
            _cmd = os.path.join(aRemotePath, PATCH_STDOUT)+"*"
            _out = glob.glob(_cmd)
            if len(_out) > 0:
                _output = [_out[0]]
        else:
            _cmd_list_files = f'ls -t {os.path.join(aRemotePath, PATCH_STDOUT)}*|head -1'
            _node = exaBoxNode(get_gcontext())
            self.mSetConnectionUser(_node)
            _node.mConnect(aHost=aDom0)
            _in, _out, _err = _node.mExecuteCmd(_cmd_list_files)
            _output = _out.readlines()

        if _output:
            _file = _output[0].strip().split("/")[-1]
            self.mPatchLogInfo(f"Log file from output {_file} ")
            # return patchmgr.stdout , else if patchmgr.stdout.<code> , then return the proper code
            if _file is not None and _file.find("stdout.") < 0:
                if _node and _node.mIsConnected():
                    _node.mDisconnect()
                return _code
            _re_out = re.match(".*stdout([.0-9a-zA-Z]+)", _file)
            if _re_out:
                _code = int(_re_out.groups()[0])
        if _node and _node.mIsConnected():
            _node.mDisconnect()
        return _code

    def mGetPatchMgrOutFiles(self, aDom0, aRemotePath, aCode=''):
        """
        Copies patchmgr.stdout/stderr/trc/log to /log
        """

        patchmgr_files = [PATCH_STDOUT, PATCH_STDERR,
                          PATCH_TRC, PATCH_LOG]
        if aCode != '':
            for i, patchmgr_file in enumerate(patchmgr_files):
                patchmgr_files[i] = patchmgr_file + '.' + aCode

        _context = get_gcontext()
        _oeda_path_logs = os.path.join(_context.mGetOEDAPath(), "log")

        _node = exaBoxNode(_context)
        self.mSetConnectionUser(_node)
        _node.mConnect(aHost=aDom0)

        for patchmgr_file in patchmgr_files:
            try:
                if _node.mFileExists(os.path.join(aRemotePath , patchmgr_file)):
                    self.mSetListOfLogsCopiedToExacloudHost(os.path.join(aRemotePath, patchmgr_file))
                    _node.mCopy2Local(os.path.join(aRemotePath , patchmgr_file),
                                      os.path.join(self.mGetLogPath() , patchmgr_file + '.' + \
                                          self.mGetCurrentTargetType()))
                    # symlinks used for chainsaw2/lumberjack
                    #  ln -s <file> <symlink>
                    # example:
                    #   ln -s /opt/oci/exacc/exacloud/oeda/requests/f829406a-15cb-11ec-8770-0010e0efc742/log/patchmgr_logs/patchmgr.stderr.cell
                    #         /opt/oci/exacc/exacloud/oeda/log/1ef39fbd-9be8-450c-8512-1e633cdf89b5_patchmgr.stderr.cell
                    #
                    _in, _out, _err = self.mGetCluControl().mExecuteCmd(
                        f"ln -s {os.path.join(self.mGetLogPath(), patchmgr_file + '.' + self.mGetCurrentTargetType())} {os.path.join(_oeda_path_logs, self.mGetMasterReqId() + '_' + patchmgr_file + '.' + self.mGetCurrentTargetType())}")
                else:
                    self.mPatchLogWarn(
                        f'{os.path.join(self.mGetLogPath(), patchmgr_file + "." + self.mGetCurrentTargetType())} not found on the launch node : {aDom0}')
            except Exception as e:
                self.mPatchLogWarn(
                    f'Error while copying {patchmgr_file}: {str(e)} from node - {aDom0} , location - {aRemotePath} to exacloud location - {self.mGetLogPath()}')
                self.mPatchLogTrace(traceback.format_exc())
        if _node.mIsConnected():
            _node.mDisconnect()

    # Functions that handle the input file necessary to run the patchmgr
    def mCreateNodesFile(self, aPath, aDom0, aHostList, aExclude=""):
        """
        Creates the input file with the list of nodes to be patched.
        """

        _input_nodes_file = os.path.join(aPath, self.mGetDbNodesFileName())
        self.mPatchLogInfo(f"Creating patch input file: {_input_nodes_file}")
        aHostList.sort()

        self.mPatchLogInfo(f"Create node list: {json.dumps(aHostList, indent=4)}")

        _h_list = [_h for _h in aHostList if _h != aExclude]
        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
            _cmd_list = (["echo", "\\n".join(_h_list)], ["tee", _input_nodes_file])
            runInfraPatchCommandsLocally(_cmd_list)
        else:
            _cmd = ''
            _node = exaBoxNode(get_gcontext())
            if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
                _node.mSetUser('opc')
                _cmd = 'printf "%s" | sudo tee %s' % ("\\n".join(_h_list), _input_nodes_file)
            else:
                _cmd = 'printf "%s" > %s' % ("\\n".join(_h_list), _input_nodes_file)

            _node.mConnect(aHost=aDom0)
            _node.mExecuteCmdLog(_cmd)
            if _node.mIsConnected():
                _node.mDisconnect()
        return _input_nodes_file


    def mCheckFreshInstall(self, aDom0):
        """
         In case of fresh installation and no upgrade or rollback performed on this environment in the
         past, this method will return True in case the
         TARGET VERSION and the image value on the Dom0 are
         same and will skip the remaining post checks like
         heartbeat etc.
        """

        _cmd_imagehistory_cmd = 'imagehistory | grep "Imaging mode" | wc -l'
        _cmd_get_fresh_image_version = "imagehistory | head -1 | awk '{print $3}'"

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDom0)
        _i, _o, _e = _node.mExecuteCmd(_cmd_imagehistory_cmd)
        _out = _o.readlines()
        if _out[0] == 1:
            _i, _o, _e = _node.mExecuteCmd(_cmd_get_fresh_image_version)
            _output = _o.readlines()
            if self.mGetTargetVersion() == _output[0]:
                self.mPatchLogInfo(
                    f"Current environment seems like a fresh install. Current Dom0 version : {_output[0]} , Target Version : {self.mGetTargetVersion()}.")
                if _node.mIsConnected():
                    _node.mDisconnect()
                return True
        if _node.mIsConnected():
            _node.mDisconnect()
        return False

    # Prepare environment before any operation
    def mPrepareEnvironment(self, aDom0, aNodesList, aBaseDir, aNodeType):
        """
        Creates the input files and sets passwordless ssh between the dom0
        and the nodes that will be patched.
        """
        _key = None

        # Update status
        self.mUpdatePatchStatus(True, STEP_PREP_ENV + '_' + aNodeType)

        # Set passwordless connection between dom0 and cells/ibswitches
        if self.__ssh_env_setup_switches_cell:
            # Setting up passwdless ssh is different in case of RoceSwitches.
            if aNodeType == PATCH_ROCESWITCH:
                _key = self.__ssh_env_setup_switches_cell.mSetSSHPasswordless(aDom0, aNodesList, True)
            else:
                _key = self.__ssh_env_setup_switches_cell.mSetSSHPasswordless(aDom0, aNodesList)


        # From Exadata image 23.x, the target OS will be upgraded to OL8 where 
        # dsa keys become obsolete. This block checks presence of any obsolete
        # keys and remove from cells
        
        _ssh_keys_remove_config = self.mGetSshKeysRemoveConfig()

        if aNodeType == PATCH_CELL:
            if ( version_compare(self.mGetTargetVersion(), "23.1.0.0.0") >= 0 and
                 PATCH_CELL in _ssh_keys_remove_config and
                'auth_keys_remove_patterns' in _ssh_keys_remove_config[PATCH_CELL] ):

                self.mPatchLogInfo(f'Starting obsolete SSH keys check on Cells : {json.dumps(aNodesList, indent=4)}')
                _auth_keys_remove_patterns = _ssh_keys_remove_config[PATCH_CELL]['auth_keys_remove_patterns']
                if _auth_keys_remove_patterns:
                    self.mPatchLogInfo(f'SSH Key Patterns to be removed : {_auth_keys_remove_patterns}')
                    self.__ssh_env_setup_switches_cell.mRemoveSshKeysAndFilesFromHosts(aDom0,
                                                                                       aNodesList,
                                                                                       _auth_keys_remove_patterns)


        '''
         Validate ssh connectivity is working fine before
         starting patch operation. Below checks are performed
         for cells and switches in this case
        '''
        self.mPatchLogInfo(f"Passwordless ssh validation performed between {str(aNodesList)} and {aDom0}")
        self.mGetCluPatchCheck().mVerifyPatchmgrSshConnectivityBetweenExadataHosts(aNodesList, aDom0)

        return _key

    def mDeleteNodesFile(self, aFilePath, aDom0):
        """
        Deletes the input file with the list of nodes to be patched.
        """
        self.mPatchLogInfo(f"Removing patch input file: {aFilePath}")
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDom0)
        _node.mExecuteCmdLog(f'rm -f {aFilePath}')
        if _node.mIsConnected():
            _node.mDisconnect()

    def mFedrampRestoreConfig(self, aTargetType):
        """
        Restores all the FEDRAMP configuration files
        and settings as patch upgrade removes all the
        fedramp settings.
        """

        # Set the Fedramp settings post upgrade.
        self.mGetCluControl().mFedrampConfig(aTargetType)

    def mFedrampDom0RestoreConfig(self, aNodesList, _Pre_Aud, _Post_Aud):
        """
        Backup the audit config file /etc/audit/audit.rules to
        preserve audit configuration for pre and post configuration.
        """

        _aDom0 = exaBoxNode(get_gcontext())
        try:
            for _node in aNodesList:
                _aDom0.mConnect(aHost=_node)
                self.mPatchLogInfo(
                    f"Audit rules file copy. Source file : {_Pre_Aud} - Destination file : {_Post_Aud} - Node : {_node}.")
                _aDom0.mExecuteCmdLog(f"\cp -rp {_Pre_Aud} {_Post_Aud}")
        except Exception as e:
            self.mPatchLogError(f"Error while taking backup of audit config file /etc/audit/audit.rules. \n\n {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            if _aDom0.mIsConnected():
                _aDom0.mDisconnect()

    def mValidateVIFBridgeInDom0(self, aDom0, aDomUList=[]):
        """
        Compare /etc/xen/scripts/vif-bridge and /etc/xen/scripts/vif-common.sh
        with the EBT files
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _log_message = None

        '''
         This check can be skipped in case of
         exasplice patching.
        '''
        _enable_vif_bridge_symlink_postcheck = self.mGetInfrapatchExecutionValidator().mCheckCondition('enableValidationOfVifBridge')
        if not _enable_vif_bridge_symlink_postcheck:
            self.mPatchLogInfo("Vif bridge symlink postcheck is disabled in infrapatching.conf and will not be performed.")
            return _ret

        _perform_vif_bridge_symlink_postcheck = self.mGetInfrapatchExecutionValidator().mCheckCondition('checkValidationOfVifBridge', dom0sdomulist=aDomUList)
        if not _perform_vif_bridge_symlink_postcheck:
            return _ret 

        _aDom0 = exaBoxNode(get_gcontext())
        try:
            _aDom0.mConnect(aHost=aDom0)

            _cmd_ls_bridge_ebt = "/bin/ls /etc/xen/scripts/vif-bridge.EBT"
            _in, _out, _err = _aDom0.mExecuteCmd(_cmd_ls_bridge_ebt)
            _output = _out.readlines()
            if not _output:
                _ret = DOM0_VIF_BRIDGE_RECREATION_FAILED
                _log_message = "Vif-bridge.EBT file doesn't exist"
                if _perform_vif_bridge_symlink_postcheck:
                    self.mPatchLogError(_log_message)
                else:
                    self.mPatchLogWarn(_log_message)
                _suggestion_msg = f"VIF Bridge validation failed in dom0 {aDom0}"
                self.mAddError(_ret, _suggestion_msg)
                return _ret

            _cmd_diff_bridge = "/usr/bin/diff -q /etc/xen/scripts/vif-bridge /etc/xen/scripts/vif-bridge.EBT"
            _i, _o, _e = _aDom0.mExecuteCmd(_cmd_diff_bridge)
            _diffs = _o.readlines()
            if _diffs:
                _ret = DOM0_VIF_BRIDGE_RECREATION_FAILED
                _log_message = f"Re-creating vif-bridge file: {_diffs}"
                if _perform_vif_bridge_symlink_postcheck:
                    self.mPatchLogError(_log_message)
                else:
                    self.mPatchLogWarn(_log_message)
                _suggestion_msg = f"VIF Bridge validation failed in dom0 {aDom0}"
                self.mAddError(_ret, _suggestion_msg)
                return _ret

            _cmd_ls_vif_common_ebt = "/bin/ls /etc/xen/scripts/vif-common.sh.EBT"
            _in, _out, _err = _aDom0.mExecuteCmd(_cmd_ls_vif_common_ebt)
            _output = _out.readlines()
            if not _output:
                _ret = DOM0_VIF_BRIDGE_RECREATION_FAILED
                _log_message = "Vif-common.sh.EBT file doesn't exist"
                if _perform_vif_bridge_symlink_postcheck:
                    self.mPatchLogError(_log_message)
                else:
                    self.mPatchLogWarn(_log_message)
                _suggestion_msg = f"VIF Bridge validation failed in dom0 {aDom0}"
                self.mAddError(_ret, _suggestion_msg)
                return _ret

            _cmd_diff_common = "/usr/bin/diff -q /etc/xen/scripts/vif-common.sh /etc/xen/scripts/vif-common.sh.EBT"
            _i, _o, _e = _aDom0.mExecuteCmd(_cmd_diff_common)
            _diffs = _o.readlines()
            if _diffs:
                _ret = DOM0_VIF_BRIDGE_RECREATION_FAILED
                _log_message = f"Re-creating vif-common.sh file: {_diffs}"
                if _perform_vif_bridge_symlink_postcheck:
                    self.mPatchLogError(_log_message)
                else:
                    self.mPatchLogWarn(_log_message)
                _suggestion_msg = f"VIF Bridge validation failed in dom0 {aDom0}"
                self.mAddError(_ret, _suggestion_msg)
                return _ret
        except Exception as e:
            self.mPatchLogError(f"Error while checking vif bridge symlinks. \n\n {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _ret = DOM0_VIF_BRIDGE_RECREATION_FAILED
            _suggestion_msg = f"Error while checking vif bridge symlinks : {str(e)}"
            self.mAddError(_ret, _suggestion_msg)
        finally:
            if _aDom0.mIsConnected():
                _aDom0.mDisconnect()
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

                _hbcheck_failed_nathostname_vm_list = self.mGetDomUNatHostNamesforDomuCustomerHostNames(aHBCheckFailedDomUList)
                _hbcheck_failed_connectible_domu_list = [x for x in _hbcheck_failed_nathostname_vm_list if x in aConnectibleDomUList]

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
                            if self.mGetCurrentTargetType() == PATCH_DOM0:
                                if self.mIsOpcUserExists(aNode):
                                    _node.mSetUser('opc')

                            _node.mConnect(aHost=aNode)
                            _netchk_file = "/opt/oracle/dcs/exacd_netchk/netchk"

                            # If the netchk file does not exist, dont fail the validation
                            if not  _node.mFileExists(_netchk_file):
                                self.mPatchLogWarn(f"{_netchk_file} does not exist on {aNode}.")
                            else:
                                _netchk_cmd_filter_json_str = json.dumps(_netchk_cmd_filter_json, indent=4)
                                _exacd_netchk_json =  "/tmp/exacd_netchk.json"
                                _node.mConnect(aHost=aNode)
                                # create exacd_netchk.json file
                                _node.mExecuteCmdLog(f"printf '{_netchk_cmd_filter_json_str}' > {_exacd_netchk_json}")
                                if not _node.mFileExists(_exacd_netchk_json):
                                    self.mPatchLogWarn(f"{_exacd_netchk_json} could not be created on {aNode}.")
                                else:
                                    _netchk_cmd= f" {_netchk_file}  --configfile={_exacd_netchk_json} | grep 'Validate VM to VM and cell connectivity over RDS' | grep PASSED "
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
                        _p.mSetMaxExecutionTime(self.mGetValidateRDSPingTimeoutInSeconds())
                        _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
                        _p.mSetLogTimeoutFx(self.mPatchLogWarn)
                        _plist.mStartAppend(_p)

                    _plist.mJoinProcess()

                    if _plist.mGetStatus() == "killed":
                        _suggestion_msg = f"Timeout occurred while validating RDSPing on the list of Nodes : {str(_hbcheck_failed_connectible_domu_list)}."
                        self.mAddError(DOMU_RDS_PING_FAILED, _suggestion_msg)
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
            self.mAddError(_ret, _suggestion_msg)

        self.mPatchLogInfo("**** RDS ping validations completed ****\n")
        return _ret

    def mUpdateCurrentLaunchNodeDetailsInCorrespondingTaskHandlerInstance(self, aNode=None, aPatchmgrLogPathLaunchNode=None):
        """
          This method is used to update instance variables(self.__cur_launch_node_list and self.__patchmgr_log_path_on_launch_node)
          of taskhandler instance by reading from targethandler instance
        """
        try:
            _cur_launch_node_list = self.mGetCurrentLaunchNodeList()
            if aNode:
                _cur_launch_node_list.append(aNode)
                self.mSetCurrentLaunchNodeList(_cur_launch_node_list)


            _patch_mgr_log_patch_on_launch_node = None
            if aPatchmgrLogPathLaunchNode:
                _patch_mgr_log_patch_on_launch_node = aPatchmgrLogPathLaunchNode
            else:
                _patch_mgr_log_patch_on_launch_node = self.mGetPatchmgrLogPathOnLaunchNode()


            _context_task_handler = mGetInfraPatchingHandler(INFRA_PATCHING_HANDLERS, self.mGetTask())

            if _context_task_handler:
                _context_task_handler.mSetCurrentLaunchNodeList(_cur_launch_node_list)
                _context_task_handler.mSetPatchmgrLogPathOnLaunchNode(_patch_mgr_log_patch_on_launch_node)
                self.mPatchLogInfo(
                    f"Updated launchnode details in taskhandler instance as {str(_cur_launch_node_list)} and patch_mgr log path as {_patch_mgr_log_patch_on_launch_node}")
            else:
                self.mPatchLogError("mUpdateCurrentLaunchNodeDetailsInCorrespondingTaskHandlerInstance - Could not get taskhandler instance to update")

        except Exception as e:
            self.mPatchLogError(
                f"Exception {str(e)} occurred in mUpdateCurrentLaunchNodeDetailsInCorrespondingTaskHandlerInstance")
            self.mPatchLogTrace(traceback.format_exc())

    def mValidateIbSwitchNTPdata(self, aListOfNodes):
        """
           Validate NTP synchronisation detail for all the
           NTP hosts added in ntp.conf file on all of the
           Ibswitches in the Exadata rack.
        """

        _ret = PATCH_SUCCESS_EXIT_CODE
        for _ibswitch in aListOfNodes:
            # Get the NTP server entries on the node.

            _cmd = 'grep ^server /etc/ntp.conf | cut -d" " -f2'

            _ibsw = exaBoxNode(get_gcontext())
            _ibsw.mConnect(aHost=_ibswitch)
            _in, _out, _err = _ibsw.mExecuteCmd(_cmd)
            _ibntp_nodes = _out.readlines()

            if not _ibntp_nodes:
                _ret = SWITCH_NTP_CHECK_FAILED
                _suggestion_msg = f"No NTP server details found in ntp.conf on {_ibswitch}"
                self.mAddError(_ret, _suggestion_msg)
                if _ibsw.mIsConnected():
                    _ibsw.mDisconnect()
                break

            # The below command tried to check the synchronization between the NTP servers and Ibswitches for success.
            # Note:
            #   o If offset is less than 0.5 seconds, 'adjust time server' is returned.
            #   o If offset is greater than 0.5 seconds, 'step time server' is returned.
            # However, in both cases, if offset is more than 1 seconds, we need to mark failure.

            _cmd = 'for aNtp in `grep ^server /etc/ntp.conf | cut -d" " -f2`; do ntpdate -d $aNtp | egrep "adjust time server|step time server"; done'

            _ibs = exaBoxNode(get_gcontext())
            _ibs.mConnect(aHost=_ibswitch)
            _in, _out, _err = _ibs.mExecuteCmd(_cmd)
            _ibntp_List = _out.readlines()
            if _ibs.mIsConnected():
                _ibs.mDisconnect()

            # Parse below offset value (above var _ibntp_List contains the same)
            # and return error if abs(offset) > 1
            # -------------------
            #  adjust time server 10.31.138.20 offset -0.000106 sec
            #  step time server 169.254.169.254 offset -22.686504 sec
            # -------------------
            for _ibnode in _ibntp_nodes:
                _ibnode = _ibnode.strip()

                if _ibnode in str(_ibntp_List):
                    self.mPatchLogInfo (
                        f"Found Time synchronization between NTP Server. Checking NTP offset value for NTP Server: [{_ibnode}] on IBSwitch: [{_ibswitch}]")
                    for _time_server in _ibntp_List:
                        if _ibnode in str(_time_server):
                            _offset_value = _time_server.split(" ")[-2]
                            _offset_value = float(_offset_value)
                            if abs(_offset_value) > 1:
                                _ret = SWITCH_NTP_CHECK_FAILED
                                _suggestion_msg = f"NTP offset is more than one second, which is not acceptable: NTP Server: [{_ibnode}] on IBSwitch: [{_ibswitch}]. NTP offset value: {abs(_offset_value)}"
                                self.mAddError(_ret, _suggestion_msg)
                            else:
                                self.mPatchLogInfo (
                                    f"Time synchronization between NTP Server: [{_ibnode}] and IBSwitch: [{_ibswitch}] is good. NTP offset value: {abs(_offset_value)}")
                else:
                    _ret = SWITCH_NTP_CHECK_FAILED
                    _suggestion_msg = f"No NTP synchronization found for NTP Server: [{_ibnode}] on IBSwitch: [{_ibswitch}]"
                    self.mAddError(_ret, _suggestion_msg)

        return _ret

    def mPatchRequestRetried(self):
        """
        This method would return whether the patching request is re-attempted by
        ecra, perhaps, after ecra/exacloud is upgraded or rebooted.
        Return value:
          True  --> Same patch request is tried with master request id
          False --> If patch request is fresh and new one
        """
        if self.mGetPatchRequestRetried().upper() == "YES":
            return True
        else:
            return False

    def mFilterNodesToPatch(self, aNodesList, aNodeType, aTaskType):
        """
        Filters the nodes that must be patched based on the active/inactive
        version and the target version. It returns two lists: one for available
        nodes and one for discarded nodes:
        [nodes_to_patch, discarded_nodes]
        """

        _ret = PATCH_SUCCESS_EXIT_CODE 
        _suggestion_msg = ""
        _nodes_to_patch = []
        _discarded_nodes = []

        if self.mIsMockEnv():
            # in mock setup, first read the hw nodes from the mock config file. 
            # If the list is empty then user running with a valid cluster...use the hw nodes from it
            if aNodeType == PATCH_CELL:
                _nodes_to_patch = self.mGetMockRackDetailsForTargetType(aTargetType=aNodeType)
            elif aNodeType == PATCH_DOM0:
                _nodes_to_patch = self.mGetMockRackDetailsForTargetType(aTargetType=aNodeType)
            elif aNodeType == PATCH_DOMU:
                # for mock testing of domus, always use the first dom0's domus
                _mock_dom0domu_mapping_list = self.mGetMockRackDetailsForTargetType(aTargetType="dom0domu_mapping")
                if len(_mock_dom0domu_mapping_list) > 0:
                    _nodes_to_patch = _mock_dom0domu_mapping_list[f"{list(_mock_dom0domu_mapping_list.keys())[0]}"]
            if _nodes_to_patch:
                return [_ret, _suggestion_msg, _nodes_to_patch, _discarded_nodes]
            else:
                return [_ret, _suggestion_msg, aNodesList, _discarded_nodes]

        # Update status
        self.mUpdatePatchStatus(True, STEP_FILTER_NODES + '_' + aNodeType)

        for _node in aNodesList:
            _active_version = self.mGetCluPatchCheck().mCheckTargetVersion(_node,
                                                                           aNodeType, aIsexasplice= self.mIsExaSplice())
            self.mPatchLogInfo(f"Current Image version on Node {_node} is {_active_version} ")
            _active_compare = self.mGetCluPatchCheck().mCheckTargetVersion(_node,
                                                                           aNodeType, self.mGetTargetVersion(),
                                                                           aIsexasplice= self.mIsExaSplice())
            if not _active_version or _active_compare is None:
                self.mPatchLogInfo(f'No version available to compare in {_node}. Node will be discarded.')
                _discarded_nodes.append(_node)
                continue

            if (self.mIsExaSplice() and aNodeType == PATCH_DOM0 and aTaskType in [TASK_PREREQ_CHECK, TASK_PATCH]):
                if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsNodeAlreadyAtOrHigherExaspliceVersion',
                                                                   node=_node,version=self.mGetTargetVersion(),nodeType=PATCH_DOM0):
                    self.mPatchLogInfo(f'Node {_node} is already at the same or higher requested version.')
                    _discarded_nodes.append(_node)
                    continue

            if (aTaskType in [TASK_ROLLBACK, TASK_ROLLBACK_PREREQ_CHECK]):
                if _active_compare < 0:
                    self.mPatchLogInfo(f'Node {_node} is already at a lower version. Node will be discarded')
                    _discarded_nodes.append(_node)
                    continue

                _inactive_version = \
                    self.mGetCluPatchCheck().mCheckTargetVersion(_node, aNodeType,
                                                                 aInactiveImage=True, aIsexasplice= self.mIsExaSplice())

                if not _inactive_version:
                    self.mPatchLogInfo(f'No rollback image available in {_node}. Node will be discarded')
                    _discarded_nodes.append(_node)
                    continue

                _inactive_compare = \
                    self.mGetCluPatchCheck().mCheckTargetVersion(_node, aNodeType,
                                                                 _inactive_version, aIsexasplice= self.mIsExaSplice())

                if _inactive_compare is None or _inactive_compare <= 0:
                    self.mPatchLogInfo(
                        f'Rollback image version is higher than active version in {_node}.Node will be discarded')
                    _discarded_nodes.append(_node)
                    continue
                else:
                    self.mPatchLogInfo(f"Node {_node} will be rolled back to Image Version  {_inactive_version} ")
            elif (aTaskType in [TASK_POSTCHECK]):
                pass
            else:
                # Bug28126586 - Need to ensure current image status is success,
                # otherwise, no point in continuing further
                _cmd = 'imageinfo -status'
                _node_tmp = exaBoxNode(get_gcontext())
                _node_tmp.mConnect(aHost=_node)
                _i, _o, _e = _node_tmp.mExecuteCmd(_cmd)
                if _node_tmp.mIsConnected():
                    _node_tmp.mDisconnect()

                _image_status = _o.readline()
                if _image_status:
                    if not _image_status.strip().lower() == 'success':
                        _suggestion_msg = f"Current image state on {_node} is invalid. It should be success, but got: {_image_status.strip()}. Please fix the image status and proceed."
                        _ret = IMAGE_INFO_STATUS_EMPTY_OR_INVALID
                        return [_ret, _suggestion_msg, _nodes_to_patch, _discarded_nodes]

                if _active_compare >= 0:
                    self.mPatchLogInfo(f'Node {_node} is already up to date. Node will be discarded ')
                    _discarded_nodes.append(_node)
                    continue
                else:
                    self.mPatchLogInfo(
                        f"Node {_node} will be upgraded/patched to Image Version {self.mGetTargetVersion()} ")

            self.mPatchLogInfo(f'Adding {_node} to available nodes list')
            _nodes_to_patch.append(_node)

        self.mPatchLogInfo(f'List of nodes to be patched : {json.dumps(_nodes_to_patch, indent=4)}')
        self.mPatchLogInfo(f'Discarded node list : {json.dumps(_discarded_nodes, indent=4)}')
        return [_ret, _suggestion_msg, _nodes_to_patch, _discarded_nodes]

    def mCheckAdditionalOptions(self, aPatchmgrCmd, aTaskType, aTargetType):
        """
        Check to see if any additional option passed to add to
        patchmgr. Basically, we might need to have some workaround to
        over-come the error or warning situation.
        """

        # Bug31982131 - Do not ignore real hardware alert if user not intended to ignore.
        _real_hw_alert_found = False
        _multiple_hw_alert_found_nodes = []
        _multiple_hw_alert_found = False
        if self.mIsMockEnv():
            # in mock setup, skip rack specific operations
            return aPatchmgrCmd

        
        if aTargetType not in [PATCH_IBSWITCH, PATCH_ROCESWITCH]:
            
            '''
             AlertHistory and Hardware alert checks are
             required to be performed only on custom 
             node list.
            '''
            if aTargetType == PATCH_DOM0:
                _node_list = self.mGetCustomizedDom0List()
            elif aTargetType == PATCH_DOMU:
                _node_list = self.mGetCustomizedDomUList()
            elif aTargetType == PATCH_CELL:
                _node_list = self.mGetCustomizedCellList()

            # list of nodes which are participating in the patch operations.
            _ret, _suggestion_msg, _list_of_nodes, _discarded = self.mFilterNodesToPatch(_node_list, aTargetType, aTaskType)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mAddError(_ret, _suggestion_msg)
                raise Exception(_suggestion_msg)
            
            if (self.mGetAdditionalOptions() and 'IgnoreAlerts' in self.mGetAdditionalOptions()[0]\
                and self.mGetAdditionalOptions()[0]['IgnoreAlerts'] == 'yes'):
                    self.mPatchLogWarn("User specified to ignore hardware alert. Proceeding with patch operation.")
            # Run H/W critical alert check for all targets, but not for exasplice dom0 patch/precheck.
            elif not (self.mIsExaSplice() and aTargetType in [PATCH_DOM0] and aTaskType in [TASK_PATCH, TASK_PREREQ_CHECK]):
                _real_hw_alert_found, _hw_alert_details, _MS_down_nodes = self.mCheckHwCriticalAlert(aTargetType, _list_of_nodes)
                _suggestion_msg = ""
                if len(_MS_down_nodes) > 0:
                    _suggestion_msg = f"Management Server is down on target {aTargetType} and task {aTaskType} for {_MS_down_nodes}. "
                    _ret = MANAGEMENT_SERVER_DOWN_DETECTED 

                if _real_hw_alert_found:
                    for _node, _log_buffer in _hw_alert_details.items():
                        if len(_log_buffer) > 1 or len (_hw_alert_details) > 1:
                            _multiple_hw_alert_found_nodes.append(_node)
                            _multiple_hw_alert_found = True
                        elif len(_log_buffer) == 1:
                            _alert_output = ''.join(_log_buffer)
                            _substr = "Critical hardware alert [%s] detected on %s for target %s and task %s"
                            if len (_alert_output) <= (ERROR_MSG_TRUNCATE_LENGTH - len(_suggestion_msg) - len(_substr) - len(_node) - len (aTargetType) - len(aTaskType)):
                                _suggestion_msg = _suggestion_msg + _substr \
                                    % (_alert_output, _node, aTargetType, aTaskType)
                            else:
                                _suggestion_msg = _suggestion_msg + f"Critical hardware alert detected on {_node} for target {aTargetType} and task {aTaskType}"

                    if _multiple_hw_alert_found:
                        _suggestion_msg = _suggestion_msg + f"Multiple critical hardware alerts detected on {_multiple_hw_alert_found_nodes} for target {aTargetType} and task {aTaskType}"

                    _ret = CRITICAL_HARDWARE_ALERT_DETECTED
                    self.mAddError(_ret, _suggestion_msg)
                elif len(_MS_down_nodes) > 0:
                    self.mAddError(_ret, _suggestion_msg)
                if len(_MS_down_nodes) > 0 or _real_hw_alert_found:
                    raise Exception(f"{_suggestion_msg}. Fix the issue and proceed.")

            _ignore_alert_flag = False
            # Check for h/w known alerts for all targets, other than dom0 exasplice precheck/patch.
            if not (self.mIsExaSplice() and aTargetType in [PATCH_DOM0] and aTaskType in [TASK_PATCH, TASK_PREREQ_CHECK]):
                _ignore_alert_flag = self.mCheckKnownAlertHistory(aTargetType, _list_of_nodes)
            else:
                # This is the case where exasplice patch / prereq check requested
                # on dom0 and in which case we simply pass ignore_alert option to
                # patchmgr, because we don't need stop patching if any h/w alerts
                # found
                _ignore_alert_flag = True

        # Bug30208068 - To automatically select additional
        # options in case additional options are to be used.

        # By default -allow_active_network_mounts is passed to patchmgr for dom0[u] except
        # when AllowActiveNfsMounts has no in AdditionalOptions being passed in payload
        if aTargetType in [PATCH_DOM0, PATCH_DOMU]:
            if (self.mGetAdditionalOptions() and 'AllowActiveNfsMounts' in self.mGetAdditionalOptions()[0]\
                and self.mGetAdditionalOptions()[0]['AllowActiveNfsMounts'] == 'no'):
                    self.mPatchLogInfo("Allow active networks mounts option is not passed to patchmgr command.")
            else:
                aPatchmgrCmd += " -allow_active_network_mounts"
                self.mPatchLogInfo("Allow active networks mounts option is passed to patchmgr command.")

        if (self.mGetAdditionalOptions() and 'IgnoreAlerts' in self.mGetAdditionalOptions()[0]\
            and (aTargetType in [PATCH_DOM0, PATCH_DOMU, PATCH_CELL])\
            and self.mGetAdditionalOptions()[0]['IgnoreAlerts'] == 'yes') or _ignore_alert_flag:
                self.mPatchLogWarn(f"Warning: ignoring all the hardware alerts on Target Type : {aTargetType}.")
                aPatchmgrCmd += " -ignore_alerts"

        if aTargetType == PATCH_CELL:
            if (self.mGetAdditionalOptions() and 'IgnoreDateValidation' in self.mGetAdditionalOptions()[0]\
              and (self.mGetAdditionalOptions()[0]['IgnoreDateValidation']).lower() != 'yes'):
                self.mPatchLogWarn(
                    f"Patchmgr option '-ignore_date_validations' is not passed to patchmgr for Target : {aTargetType} and Task Type : {self.mGetTask()}.")
            else:
                self.mPatchLogWarn(
                    f"Ignoring all the date validations in the patch naming convention on Task Type : {self.mGetTask()}.")
                aPatchmgrCmd += " -ignore_date_validations"

        if self.mGetAdditionalOptions() and 'ForceRemoveCustomRpms' in self.mGetAdditionalOptions()[0]\
            and (aTargetType in [PATCH_DOM0, PATCH_DOMU])\
            and self.mGetAdditionalOptions()[0]['ForceRemoveCustomRpms'] == 'yes':
                self.mPatchLogWarn(f"Warning: Removing all the custom RPMs on Target Type : {aTargetType}.")
                aPatchmgrCmd += " -force_remove_custom_rpms"

        if self.mGetAdditionalOptions() and 'SkipGiDbValidation' in self.mGetAdditionalOptions()[0]\
            and (aTargetType == PATCH_DOMU)\
            and self.mGetAdditionalOptions()[0]['SkipGiDbValidation'] == 'yes':
                self.mPatchLogWarn("Skipping validation of GI/DB versions")
                aPatchmgrCmd += " --skip_gi_db_validation"

        # connect to the nodes on the list and see if enforcing is set on SELinux
        if aTargetType in [PATCH_DOM0, PATCH_DOMU]:
            if (self.mIsSELinuxEnforcing(_list_of_nodes)):
                aPatchmgrCmd += " --allow_selinux_enforcing"

        # connect to the nodes on the list and check for FS encryption
        if self.mCheckConditionsForEncryptPatching() and mIsFSEncryptedList(_list_of_nodes, self):
            aPatchmgrCmd += f" --key_api {KEY_API}"

        return aPatchmgrCmd

    def mCheckKnownAlertHistory(self, aTargetType, aListOfNodes):

        """
         This method checks for alerts in the alerthistory to
         see if it could be ignored or needs attention, List of
         alerts would be updated in a list based on analysis peformed.

         Although for now ignore_alerts option is of prime focus, More
         actions would be taken for other options as well in future
         releases.
        """

        self.mPatchLogInfo("\n\n***Performing known alerthistory validations ****\n")
        _srvType = EXACC_SRV if self.mIsExaCC() else EXACS_SRV
           
        if aTargetType in [ PATCH_DOM0 ]:
            _dom0_filter_list = mGetInfraPatchingKnownAlert(PATCH_DOM0, _srvType)
            _dbmcli_cmd = "dbmcli -e 'LIST ALERTHISTORY WHERE endtime=null AND alerttype=stateful'"
            _dom0_filter = '|'.join(_dom0_filter for _dom0_filter in _dom0_filter_list)
            _filter_cmd = f" | egrep -i '{_dom0_filter}'"
            _cmd = _dbmcli_cmd + _filter_cmd
        elif aTargetType in [ PATCH_DOMU ]:
            _domu_filter_list = mGetInfraPatchingKnownAlert(PATCH_DOMU, _srvType)
            _dbmcli_cmd = "dbmcli -e 'LIST ALERTHISTORY WHERE endtime=null AND alerttype=stateful'"
            _domu_filter = '|'.join(_domu_filter for _domu_filter in _domu_filter_list)
            _filter_cmd = f" | egrep -i '{_domu_filter}'"
            _cmd = _dbmcli_cmd + _filter_cmd
        elif aTargetType in [ PATCH_CELL ]:
            _cell_filter_list = mGetInfraPatchingKnownAlert(PATCH_CELL, _srvType)
            _cellcli_cmd = "cellcli -e 'LIST ALERTHISTORY WHERE endtime=null AND alerttype=stateful'"
            _cell_filter = '|'.join(_cell_filter for _cell_filter in _cell_filter_list)
            _filter_cmd = f" | egrep -i '{_cell_filter}'"
            _cmd = _cellcli_cmd + _filter_cmd

        _ignore_alert_flag = False

        _aTimeout = self.mGetTimeoutForDbmcliCellCliInSeconds()

        for aNode in aListOfNodes:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=aNode)
            _i, _o, _e = _node.mExecuteCmd(_cmd, aTimeout=_aTimeout)
            _out = _o.readlines()
            if _node.mIsConnected():
                _node.mDisconnect()

            if _out:
                self.mPatchLogWarn(f"Error observed in alerthistory output on {aTargetType} {aNode}.")
                self.mPatchLogWarn(f"{_out}")
                self.mPatchLogWarn("-ignore_alerts will be appended to the patchmgr command.")
                # when applied to a boolean variable "|=" will set it to TRUE the first time it encounters a truth expression on the right side and will HOLD its TRUE value
                # for all |= subsequent calls. Like a latch.
                _ignore_alert_flag |= True

        self.mPatchLogInfo("\n***Known alerthistory checks completed***\n")
        return _ignore_alert_flag

    def mCheckHwCriticalAlert(self, aTargetType, aListOfNodes):
        """
         This method checks for the existence of real hardware alert on all
         filter nodes of the specified target, and other than known and
         specified alerts.
         Return:
            True  --> if genuine hardware alerts found
            False --> if no genuine hardware alerts found
            []    --> list of dom0/cell node names having hardware alerts if found
        """
        _cmd = ""
        _hw_alert_flag = False
        _MS_down_nodes = []
        _hw_alert_details = {}
 
        self.mPatchLogInfo("Critical hardware alerts verification started.")

        _srvType = EXACC_SRV if self.mIsExaCC() else EXACS_SRV

        if aTargetType in [ PATCH_DOM0 ]:
            _dom0_filter_list = mGetInfraPatchingKnownAlert(PATCH_DOM0, _srvType)
            _dbmcli_cmd = "dbmcli -e 'LIST ALERTHISTORY WHERE endtime=null AND alerttype=stateful and alertShortName=Hardware and severity=Critical'"
            _dom0_filter = '|'.join(_dom0_filter for _dom0_filter in _dom0_filter_list)
            _filter_cmd = f" | grep -vE '{_dom0_filter}'"
            _cmd = _dbmcli_cmd + _filter_cmd
        elif aTargetType in [ PATCH_DOMU ]:
            self.mPatchLogInfo("DomU does not interact directly with the hardware, therefore it skips the check for critical hardware alerts.")
            return _hw_alert_flag, _hw_alert_details, _MS_down_nodes
        elif aTargetType in [ PATCH_CELL ]:
            _cell_filter_list = mGetInfraPatchingKnownAlert(PATCH_CELL, _srvType)
            _cellcli_cmd = "cellcli -e 'LIST ALERTHISTORY WHERE endtime=null AND alerttype=stateful and alertShortName=Hardware and severity=Critical'"
            _cell_filter = '|'.join(_cell_filter for _cell_filter in _cell_filter_list)
            _filter_cmd = f" | grep -vE '{_cell_filter}'"
            _cmd = _cellcli_cmd + _filter_cmd

        _aTimeout = self.mGetTimeoutForDbmcliCellCliInSeconds()

        # Detect H/W alert on all nodes.
        for aNode in aListOfNodes:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=aNode)
            _i, _o, _e = _node.mExecuteCmd(_cmd, aTimeout=_aTimeout)
            _out = _o.readlines()
            if _node.mIsConnected():
                _node.mDisconnect()

            '''
            If the Server Management is down, dbmcli will return:
            dbmcli -e 'list alerthistory'
            DBM-01514: Connect Error. Verify that Management Server is running on the server.
            '''
            # Genuine H/W alert found.
            if _out:
                _log_buffer = []
                _MS_down = False
                # check if Managerment Server is running first
                for _output in _out:
                    if "DBM-01514" in _output:
                        _MS_down = True
                        _MS_down_nodes.append(aNode)
                        self.mPatchLogWarn(f"Found Management Server down on {aTargetType} {aNode}")
                        break;
                    _log_buffer.append(_output.strip().split('\t')[-1].strip())

                if not _MS_down:
                    self.mPatchLogWarn(f"Found HardWare alert on {aTargetType} {aNode}:")
                    self.mPatchLogWarn(f"{str(_out)}")
                    _hw_alert_details.update({aNode: _log_buffer})
                    _hw_alert_flag |= True

        self.mPatchLogInfo("Critical hardware alerts verification completed.")

        return _hw_alert_flag, _hw_alert_details, _MS_down_nodes

    def getExistingPatchMgrSessionLogPath(self, aNode):

        _patchmgr_log_path = None
        _node = exaBoxNode(get_gcontext())

        '''
        root@scaqag01dv0601m dbserver_patch_240824]# ps -ef | egrep -i 'patchmgr -' | egrep -vi 'grep|tail' |awk -F'log_dir ' '{print $2}' | awk '{print $1}' |head -1
        output (for domu): /u02/dbserver.patch.zip_exadata_ol8_23.1.13.0.0.240727_Linux-x86-64.zip/dbserver_patch_240824/patchmgr_log_80abf0aa-55f3-4b47-b4fc-0de1766cffa7
        
        output (for domu): /EXAVMIMAGES/dbserver.patch.zip_exadata_ovs_23.1.13.0.0.240727_Linux-x86-64.zip/dbserver_patch_240824/patchmgr_log_df0f4362-aa76-49b1-b1e8-818053a363f9
        '''
        _cmd = "ps -ef | egrep -i 'patchmgr -' | egrep -vi 'grep|tail' |awk -F'log_dir ' '{print $2}' | awk '{print $1}' | head -1"

        _node.mConnect(aNode)
        _patchmgr_log_path = self.mReturnExecOutput(_cmd, _node)
        if _patchmgr_log_path and len(_patchmgr_log_path) > 0:
            self.mPatchLogInfo(f"PatchMgr Log path from existing patchmgr session is {_patchmgr_log_path}")
        _node.mDisconnect()
        return _patchmgr_log_path

    def mCheckPatchmgrSessionExistence(self, aPatchmgLogPathLaunchNode, aLaunchNode=None, aNodeList=None, aUpdateExacloudDB=True):
        """
         This method checks for existing of patchmgr session.

         Return two values:
          1) Non-zero (EB ERROR - 613) : One or more patchmgr sessions
              OR
             Zero: No patchmgr session are running
          2) Node name which is running pacthmgr
          3) In case of aUpdateExacloudDB set to False patchmgr
             existence check is only required to be performed and not
             update the exacloud DB as in such cases, there is an 
             existing error code on the Exacloud DB and do not want 
             error code from mCheckPatchmgrSessionExistence to overwite 
             the previous Error code.
             
        """

        def _patchmgr_session_hint(aNode):
            """
             Return:
               PATCHMGR_SESSION_ALREADY_EXIST : One or more patchmgr sessions are running or had patchmgr ran
               PATCH_SUCCESS_EXIT_CODE        : No patchmgr sessions are running.
            """

            _node = exaBoxNode(get_gcontext())
            self.mSetConnectionUser(_node)
            _node.mConnect(aHost=aNode)

            # Search of 'patchmgr -' in the grep command.

            # TODO: Below code can be used for future requirement:-
            # # See if there any remote console log found
            # if not aPatchmgLogPathLaunchNode:
            # self.mPatchLogInfo("The patchmgr console log found. Active Launch Node = '%s'." % aNode)
            #
            # _patchmgr_console_log_find = 'find %s/PatchmgrConsole.out' % (aPatchmgLogPathLaunchNode)
            # _i, _o, _e = _node.mExecuteCmd(_patchmgr_console_log_find)
            # if int(_node.mGetCmdExitStatus()) == 0:
            # self.mPatchLogInfo("The patchmgr console log found. Active Launch Node = '%s'." % aNode)
            #     _node.mDisconnect()
            # return True

            _cmd = "ps -ef | egrep -i 'patchmgr -' | egrep -vi 'grep|tail'" 
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            _out = _o.readlines()
            if _out:
                self.mPatchLogInfo(f"Existing patchmgr session details are as follows :\n {str(_out)}")

            if int(_node.mGetCmdExitStatus()) == 0:
                self.mPatchLogInfo(
                    f"The patchmgr session is active on this cluster. Patchmgr Active Node = '{aNode}'.")
                if _node.mIsConnected():
                    _node.mDisconnect()
                return PATCHMGR_SESSION_ALREADY_EXIST

            if _node.mIsConnected():
                _node.mDisconnect()
            return PATCH_SUCCESS_EXIT_CODE

        # end of _patchmgr_session_hint

        ret = PATCH_SUCCESS_EXIT_CODE
        _patchmgr_session_active_node = None
        self.mPatchLogInfo("\nPerforming Patchmgr existence check.")

        if aLaunchNode:
            self.mPatchLogInfo(
                f"*** Checking for existence of patchmgr/dbnodeupdate.sh sessions in the cluster on Node {aLaunchNode} ")
        else:
             self.mPatchLogInfo("*** Checking for existence of patchmgr/dbnodeupdate.sh sessions in the cluster.")

        # Find patchmgr session in the given list of nodes
        if aNodeList:
            for _dom0domU in aNodeList:
                ret = _patchmgr_session_hint(aNode=_dom0domU)
                if ret != PATCH_SUCCESS_EXIT_CODE:
                    if aUpdateExacloudDB:
                        _suggestion_msg = f"Patchmgr session already exists on node : {_dom0domU}"
                        self.mAddError(ret, _suggestion_msg)
                    _patchmgr_session_active_node = _dom0domU
                    break
            # Find patchmgr session on the launch node
        elif aLaunchNode:
            ret = _patchmgr_session_hint(aNode=aLaunchNode)
            if ret != PATCH_SUCCESS_EXIT_CODE:
                if aUpdateExacloudDB:
                    _suggestion_msg = f"Patchmgr session already exists on launch node : {aLaunchNode}"
                    self.mAddError(ret, _suggestion_msg)
                _patchmgr_session_active_node = aLaunchNode

        if _patchmgr_session_active_node:
            self.mPatchLogError(f"*** Patchmgr session already exists found on {_patchmgr_session_active_node}")

        self.mPatchLogInfo("Patchmgr existence check completed.\n")
        return ret, _patchmgr_session_active_node

    def mGetNodeCount(self, aNode, aInputListFile):

        """
         To get the count of Cells/ IBSwitches to be patched.
         The list of nodes might vary depending on the discarded
         node list and canont rely on the config xml list of cells.
        """

        _count_of_nodes = 0
        _count_of_nodes_cmd = (f"wc -l {aInputListFile} | awk '{{print $1}}'")
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aNode)
        _i, _o, _e = _node.mExecuteCmd(_count_of_nodes_cmd)
        _out = _o.readlines()
        for _output in _out:
            _count_of_nodes = int(_output.strip())

        '''

         Incrementing the count is necessary due to the 
         below issue. in the lat line both cell name and 
         prompt appear in the same line.

          bash-4.2$cat node_list
          cel01
          cel02
          cel03bash-4.2$ 

        '''
        _count_of_nodes += 1
        if _node.mIsConnected():
            _node.mDisconnect()
        return _count_of_nodes

    def mUpdateRequestStatusFromList(self, aStatus, aStep, aComment=''):
        """
        Updates the patch request status for the initial (and common to all patches) steps.
        """

        _reqobj = self.mGetCluControl().mGetRequestObj()

        if _reqobj:
            _db = ebGetDefaultDB()
            if aComment:
                aStep+='-'+aComment
                _reqobj.mSetStatusInfo(str(aStatus)+':'+aStep)
                _db.mUpdateStatusRequest(_reqobj)

    def mReadPatchmgrConsoleOut(self, aNode, aPatchmgLogPathLaunchNode, aInputListFile=None, aPatchStates=None, aPatchmgrTimeoutInSec=None):
        """
         Here we connect to the launch node and try to check for progress reading
          Patchmgr Console out file. It returns:

             zero     --> when patchmgr end with success
             non-zero --> when patchmgr end with failure

          Since the patchmgr is run in the background using nohup, the below section
           of code monitors the log file for completion and returns the exit status of the
          patchmgr command.
        """

        self.mPatchLogInfo(f"\nRead patchmgr console from node = {aNode} and log loc = {aPatchmgLogPathLaunchNode}")

        self.mPatchLogInfo("\n\n--------> Patchmgr output starts here <--------\n")
        _node = exaBoxNode(get_gcontext())
        self.mSetConnectionUser(_node)
        _node.mConnect(aHost=aNode)
        _patch_mgr_run = True
        _patchmgr_prev = None
        _elapsed_time_in_sec = 0
        _nodes_already_upgraded = []
        _exit_code = PATCHMGR_COMMAND_FAILED
        _count_of_nodes = 0
        _finished_d = 0
        _patchmgr_timeout_in_sec = 0

        if self.mGetCurrentTargetType() == PATCH_DOMU:
            _exit_code = DOMU_PATCHMGR_COMMAND_FAILED

        if aInputListFile is not None:
            _finished_nodes = 0
            _count_of_nodes = self.mGetNodeCount(aNode, aInputListFile)
            self.mPatchLogInfo(
                f"**** [ Nodes already upgraded / Total number of Nodes ] : [ {_finished_d:d} / {_count_of_nodes:d} ]")
            self.mUpdateRequestStatusFromList(True, aPatchStates, f"[0/{_count_of_nodes:d}]_{self.mGetRackName()}")

        _patchmgr_find = f"egrep -i 'Working|SUCCESS|INFO' {aPatchmgLogPathLaunchNode}/PatchmgrConsole.out | tail -1 | cut -d'[' -f3,4,5 | cut -d':' -f2,3,4,5 | sed -E 's/\]/->/g;/^$/d'"
        _patchmgr_seek = f'grep -i "Exit status" {aPatchmgLogPathLaunchNode}/PatchmgrConsole.out'
        _patchmgr_start_time = datetime.datetime.now()
        if aPatchmgrTimeoutInSec:
            _patchmgr_timeout_in_sec = aPatchmgrTimeoutInSec
        else:
            _patchmgr_timeout_in_sec = self.mGetExadataPatchmgrConsoleReadTimeoutSec()

        self.mPatchLogInfo(
            f"\nPatchmgr console logs can be found under {aNode}:{aPatchmgLogPathLaunchNode}/PatchmgrConsole.out\n")

        while _patch_mgr_run and _elapsed_time_in_sec < _patchmgr_timeout_in_sec:

            # Notification xml files are monitored every 5 minutes for change in status,
            # Change in status to Success or Failure for any of the cells and ibswitches
            # requests table will be updated and update details are written into thread
            # logs.
       
            # We dont want to poll the PatchmgrConsole.out continously as it increases 
            # cpu usage, hence sleeping for certain time
            time.sleep(self.mGetPatchmgrConsoleReadIntervalInSeconds())

            if aInputListFile is not None and ( _elapsed_time_in_sec % 300 ) == 0:
                _input_status_file = f'{aPatchmgLogPathLaunchNode}/notifications/notification_patchmgr_*_'
                _patch_filter_cmd = f"egrep -i 'NAME=' {_input_status_file} | cut -d'=' -f2 | tr -d '>'"
                _i, _o, _e = _node.mExecuteCmd(_patch_filter_cmd)
                _out_cellswitch_list = _o.readlines()
                for _out_celswitch_name in _out_cellswitch_list:
                    _out_celswitch_name = _out_celswitch_name.strip()
                    _patch_get_status = f"egrep -i -A 15 {_out_celswitch_name} {_input_status_file} | cut -d '\"' -f2,6 | sed 's/4\"//g; s/5\"//g' | egrep -i 'Succeeded|Failed' | tail -1 | awk '{{print $1}}'"
                    _i, _o, _e = _node.mExecuteCmd(_patch_get_status)
                    _out_get_status = _o.readlines()
                    for _output_get_status in _out_get_status:
                        _output_get_status = _output_get_status.strip()
                        if _out_celswitch_name not in _nodes_already_upgraded:
                            self.mPatchLogInfo(
                                f"**** Current status of Node : {_out_celswitch_name} -> {_output_get_status}")
                            _finished_d += 1
                            _nodes_already_upgraded.append(_out_celswitch_name)
                            self.mUpdateRequestStatusFromList(True, aPatchStates,
                                                              f"[{_finished_d:d}/{_count_of_nodes:d}]_{self.mGetRackName()}")
                            self.mPatchLogInfo(
                                f"**** [ Nodes already upgraded / Total number of Nodes ] : [ {_finished_d:d} / {_count_of_nodes:d} ]")

                '''
                 To print the elpased time and total timeout for end user 
                 to determine the time taken for patch operation to complete.
                 Polling is done evenry 1Hr and total exacloud timeout is 23Hrs.
                '''
                if ( _elapsed_time_in_sec % 3600 ) == 0:
                    _total_elapsed_time_in_hrs = abs(int(_elapsed_time_in_sec/3600))
                    _exadata_console_read_timeout_in_hrs = abs(int(self.mGetExadataPatchmgrConsoleReadTimeoutSec()/3600))
                    _total_time_left_to_reach_exacloud_timeout = _exadata_console_read_timeout_in_hrs - _total_elapsed_time_in_hrs
                    self.mPatchLogInfo(
                        f"\n\n****** Total time left to reach exacloud timeout : {_total_time_left_to_reach_exacloud_timeout}Hrs, Elapsed time : {_total_elapsed_time_in_hrs}Hrs, Total exacloud timeout : {_exadata_console_read_timeout_in_hrs}Hrs *****\n\n")

            _i, _o, _e = _node.mExecuteCmd(_patchmgr_find)
            _out = _o.readlines()
            for _output in _out:
                _output = _output.strip()
                if _patchmgr_prev != _output:
                    self.mPatchmgrLogInfo(f"{_output}")
                    _patchmgr_prev = _output

            _patch_progress_time = datetime.datetime.now()
            _elapsed_time_in_sec = int((_patch_progress_time - _patchmgr_start_time).total_seconds())

            _i, _o, _e = _node.mExecuteCmd(_patchmgr_seek)
            _exit_check = _node.mGetCmdExitStatus()
            _out = _o.readlines()

            if _exit_check == 0:
                _patch_mgr_run = False
                _cmd_get_summary = f"egrep -i 'ERROR|WARNING|For details, check the following files' -A 5 {aPatchmgLogPathLaunchNode}/PatchmgrConsole.out | egrep -vi 'Do not interrupt|Do not resize|Do not reboot|Do not open logfiles' | cut -d'[' -f3,4,5 | cut -d':' -f2,3,4,5 | sed -E 's/\]/->/g;/^$/d'"
                _i, _o, _e = _node.mExecuteCmd(_cmd_get_summary)
                _out_summary = _o.readlines()
                if _out_summary:
                    for _output_summary in _out_summary:
                        _output_summary = _output_summary.strip()
                        self.mPatchmgrLogInfo(_output_summary)

                for _output in _out:
                    self.mPatchmgrLogInfo(f"{_output}")
                    if "Exit status:0" in _output:
                        _exit_code = PATCH_SUCCESS_EXIT_CODE
                    else:
                        _suggestion_msg = f"Patchmgr command failed on Target : {str(self.mGetTargetTypes())} for Patch Operation : {self.mGetTask()}.Patchmgr logs are available on the node : {aNode} at location : {aPatchmgLogPathLaunchNode}."
                        self.mAddError(_exit_code, _suggestion_msg)

                    # Dump content of PatchmgrConsole.out at the end irrespective if success/failure
                    self.mPatchLogInfo(
                        f"\n\n ------> Start dumping entire patchmgr Console log at the end of patchMgr operation from {aNode}:{aPatchmgLogPathLaunchNode} <------\n\n")
                    _cmd_dump_console_log = f"cat {aPatchmgLogPathLaunchNode}/PatchmgrConsole.out"
                    _in, _op, _ex = _node.mExecuteCmd(_cmd_dump_console_log)
                    for _line in _op.readlines():
                        self.mPatchmgrLogInfo(_line.strip())
                    self.mPatchLogInfo(
                        f"\n\n ------> End dumping entire patchmgr Console log at the end of patchMgr operation from {aNode}:{aPatchmgLogPathLaunchNode} <------\n\n")

                    if _node.mIsConnected():
                        _node.mDisconnect()
                    self.mPatchLogInfo("\n\n--------> Patchmgr output ends here <--------\n")

                    # Wait for patchmgr commands to complete.
                    self.mWaitForPatchmgrCommandToComplete(aNode, aPatchmgLogPathLaunchNode)
                    return _exit_code

        '''
         In case of Exadata patchmgr timeout, Infra patching will terminate with
         exit code.

         EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR requires action to be taken
         exacloud side/Operation team, hence it is by default retained as 
         PAGE_ONCALL
        '''
        if _elapsed_time_in_sec >= _patchmgr_timeout_in_sec:
            _exit_code = EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR
            _suggestion_msg = f"Exadata Infra patching Timeout occurred after {_patchmgr_timeout_in_sec:d} seconds, Could not validate patch operation completion on launch node : {aNode}."
            self.mAddError(_exit_code, _suggestion_msg)

        if _node.mIsConnected():
            _node.mDisconnect()
        self.mPatchLogInfo(
            f"Reading patchmgr console from node = {aNode} and log loc = {aPatchmgLogPathLaunchNode} completed..\n")
        return _exit_code

    def mWaitForPatchmgrCommandToComplete(self, aNode, aPatchmgLogPathLaunchNode):
        """
         This method validates for any patchmgr sessions before proceeding
         with other patching tasks. If there are patchmgr sessions running,
         it waits for the patchmgr/dbnodeupdate session to complete.
        """
        # Check patchmgr session existence
        _ret, _patchmgr_active_node = self.mCheckPatchmgrSessionExistence(aPatchmgLogPathLaunchNode,aNode,aUpdateExacloudDB=False)
        if _ret == PATCHMGR_SESSION_ALREADY_EXIST:
            _retry_check_for_folder_counter = RETRY_PATCHMGR_PROCESS_COMPLETION_CHECK_MAX_COUNTER_VALUE
            _counter_to_display_iteration_count = 0
            while _retry_check_for_folder_counter > 0:
                sleep(WAIT_FOR_PATCHSUCCESSEXIT_IN_SECONDS)
                # Retry checking for patchmgr process existence.
                _ret, _patchmgr_active_node = self.mCheckPatchmgrSessionExistence(aPatchmgLogPathLaunchNode,aNode,aUpdateExacloudDB=False)
                _retry_check_for_folder_counter -= 1
                _counter_to_display_iteration_count += 1
                self.mPatchLogError(
                    f"Patchmgr session is still running. Polling for {_counter_to_display_iteration_count:d} iteration(s) of 10 seconds each for 60 seconds for the patchmgr command to complete.")
                if _ret == PATCH_SUCCESS_EXIT_CODE or _retry_check_for_folder_counter == 0:
                    break

    def mCreateDirOnNodes(self, aNodeList, aDirPath):
        """
          Create directory 'aDirPath' on given list of aNodeList.
        """
        _cmd_mkdir = f'mkdir -p {aDirPath}'
        for _node in aNodeList:
            _node_ctx = exaBoxNode(get_gcontext())
            self.mSetConnectionUser(_node_ctx)
            _node_ctx.mConnect(aHost=_node)
            _node_ctx.mExecuteCmd(_cmd_mkdir)
            if _node_ctx.mIsConnected():
                _node_ctx.mDisconnect()

    def mVerifyAndCleanupMissingPatchmgrRemotePatchBase(self, aRemotePatchBase, aLaunchNodeCandidates):

        if self.mIsMockEnv():
            # in mock setup, skip rack specific operations
            return

        for _launch_node in aLaunchNodeCandidates:
            _node = exaBoxNode(get_gcontext())
            self.mSetConnectionUser(_node)
            _node.mConnect(aHost=_launch_node)

            if _node.mFileExists(aRemotePatchBase):
                _parent_dir = aRemotePatchBase
                _cmd_find_dir = f"find {_parent_dir} -mindepth 1 -maxdepth 1 -type d"
                _in, _out, _err = _node.mExecuteCmd(_cmd_find_dir)
                _exit_code = int(_node.mGetCmdExitStatus())
                _outputList = _out.readlines()
                if int(_exit_code) == 0:
                    # In some cases, the patch base directory may not have any
                    # subdirectories yet contains a file like dbserver.patch.zip
                    # In these scenarios, dbserver.patch.zip will not be
                    # transferred and unzipped to the patch base directory.
                    # Therefore, we're completely removing the patch base
                    # directory to ensure all content is transferred and updated.
                    if len(_outputList) == 0:
                        self.mPatchLogWarn(f"The patch base directory doesn't contain any subdirectories, resulting in the deletion of the patch base directory {_parent_dir}")
                        _cmd_rm_dir = f"rm -rf {_parent_dir}"
                        _node.mExecuteCmd(_cmd_rm_dir)

                    for _output in _outputList:
                        _dir_path = _output.strip()
                        _patchmgr_path = _dir_path + "/patchmgr"
                        _cmd_test = f"test -f {_patchmgr_path}"
                        _in, _out, _err = _node.mExecuteCmd(_cmd_test)
                        _exit_code = int(_node.mGetCmdExitStatus())
                        _output = _out.readlines()
                        if int(_exit_code) != 0:
                            self.mPatchLogWarn(f'The patchmgr file cannot be found in {_dir_path}, leading to the removal of the patch base directory {_parent_dir}')
                            _cmd_rm_dir = f"rm -rf {_parent_dir}"
                            _node.mExecuteCmd(_cmd_rm_dir)
                            break

            if _node.mIsConnected():
                _node.mDisconnect()

    def mSetLaunchNodeAsPatchBase(self,
                                   aLaunchNodeCandidates,
                                   aLocalPatchZipFile,
                                   aPatchZipName, aPatchZipSizeMb,
                                   aRemotePatchBase, aRemotePatchZipFile,
                                   aRemotePatchmgr, aRemoteNecessarySpaceMb, aPatchBaseDir,
                                   aSuccessMsg="", aMoreFilesToCopy=None):
        """
        Makes sure the patchmgr is installed alog with any other files for
        its correct use. Generic method to install patchmgr on a given node to
        patch cells/ibswitches, dom0s or domus
        """

        # Update db status
        self.mUpdatePatchStatus(True, STEP_SELECT_LAUNCH_NODE)

        # Cleanup old patches before validating for space requirements
        # and copying patches.
        try:
            self.mCleanupExadataPatches(aLaunchNodeCandidates)
        except Exception as e:
            self.mPatchLogWarn(
                f'Exadata patches not cleaned properly on launch nodes {str(aLaunchNodeCandidates)}. Message: {str(e)}')
            self.mPatchLogTrace(traceback.format_exc())

        # If there are directories in the remote patch base that do not
        # contain the patchmgr file, the remote patch base dir must be removed.
        if not self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
            self.mVerifyAndCleanupMissingPatchmgrRemotePatchBase(aRemotePatchBase, aLaunchNodeCandidates)

        # In case of Postcheck and oneoff operations, we need not
        # to copy any of the patchmgr related files or images.
        if self.mGetTask() in [ TASK_ONEOFF, TASK_POSTCHECK, TASK_ONEOFFV2 ]:
            self.mPatchLogInfo(f"Ignoring file copy of exadata patches for task : {self.mGetTask()} is performed.")
            _launch_node = aLaunchNodeCandidates[0].strip()
            return _launch_node

        if self.mIsMockEnv():
            # in mock setup, skip rack specific operations
            _launch_node = aLaunchNodeCandidates[0].strip()
            return _launch_node

        _local_patch_path = os.path.dirname(aLocalPatchZipFile)
        _ret, _errmsg = self.mValidateImageCheckSumWithRetry(aPatchZipName, _local_patch_path, aRemotePatchBase ,aLaunchNodeCandidates , aRemoteNecessarySpaceMb)
        if _ret != PATCH_SUCCESS_EXIT_CODE:
            raise Exception(_errmsg)

        if aMoreFilesToCopy:
            for _file, _copy_to in aMoreFilesToCopy:
                _file_name = _file.split("/")[-1]
                _local_patch_path = os.path.dirname(_file)
                _ret, _errmsg = self.mValidateImageCheckSumWithRetry(_file_name, _local_patch_path, _copy_to ,aLaunchNodeCandidates, aRemoteNecessarySpaceMb)
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    raise Exception(_errmsg)

        for _launch_node in aLaunchNodeCandidates:

            #TODO: fix all the disconnect calls. Can maybe connect/disconnect
            # during each cmd? whats the best way?
            _node = exaBoxNode(get_gcontext())
            self.mSetConnectionUser(_node)
            _node.mConnect(aHost=_launch_node)
            _node.mExecuteCmd("ls -l %s" % (aRemotePatchmgr))
            _exit_code = _node.mGetCmdExitStatus()

            #make sure we can get the patch to the directory that came out of unziping the patch
            if int(_exit_code) != 0:
                if _node.mIsConnected():
                    _node.mDisconnect()
                _suggestion_msg = f"Expected patchmgr script {_launch_node}:{aRemotePatchmgr} but it was not found.Patch zip structure may have changed"
                _ret = PATCHMGR_SCRIPT_MISSING_ON_LAUNCH_NODE
                self.mAddError(_ret, _suggestion_msg)
                #TODO give it another shot on a different  dom0 (continue), or just error out (return None)
                continue

            self.mPatchLogInfo(
                f"Selecting {str(_launch_node)} as a patch base for {aSuccessMsg}. patchmgr is at {aRemotePatchmgr}")
            if _node.mIsConnected():
                _node.mDisconnect()
            return _launch_node
        else:
            self.mPatchLogError(f"None of {str(aLaunchNodeCandidates)} were eligible bases for the patch manager")
            return None


    def mGetImageLocation(self,aPatchLoc=None):
        """
        In case of OCI EXACC environemnts, PatchPayload details are fetched
        from ociexacc_exadata_patch_download_loc parameter as per details from
        the exabox.conf file.
        """

        _imgrev = aPatchLoc
        self.OCIEXACC = self.mGetCluControl().mCheckConfigOption('ociexacc')
        if self.OCIEXACC == "True":
            self.OCIEXACC_LOC = self.mGetCluControl().mCheckConfigOption('ociexacc_exadata_patch_download_loc').strip()
            if(not self.OCIEXACC_LOC or self.OCIEXACC_LOC == '' or self.OCIEXACC_LOC == None):
                _imgrev = False
            else:
                _imgrev = self.OCIEXACC_LOC + aPatchLoc
        else:
            self.mPatchLogInfo('*** ociexacc parameter is set to False. Retaining the patch path to default exacloud location.')
            _imgrev = os.path.join(os.getcwd(), aPatchLoc)
        return _imgrev

    def mValidateImageCheckSumWithRetry(self,  aPatchFile, aPatchRepo, aRemotePatchBase, aNodeList, aRemoteNecessarySpaceMb):
        """
         This method calls mValidateImageCheckSum with 2 retries
         if there is any issue in any iteration
         Return:-
          PATCH_SUCCESS_EXIT_CODE                 --> if checksum evaluation and files copy are successful.
          Non PATCH_SUCCESS_EXIT_CODE error codes --> If there any failures
        """
        _rc = PATCH_SUCCESS_EXIT_CODE
        _errmsg = ""
        _max_retries = self.mGetMaxRetriesForValidateImageChecksum()
        _retries = 0
        while _retries < _max_retries:
            try:
                if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                    _rc, _errmsg = self.mValidateImageCheckSumForLocalNode(aPatchFile, aPatchRepo, aRemotePatchBase, aNodeList, aRemoteNecessarySpaceMb)
                else:
                    _rc, _errmsg = self.mValidateImageCheckSum(aPatchFile, aPatchRepo, aRemotePatchBase, aNodeList, aRemoteNecessarySpaceMb)
                if _rc == PATCH_SUCCESS_EXIT_CODE:
                    break
                else:
                    self.mPatchLogWarn(
                        f"Retry ({(_retries + 1):d}/{_max_retries:d}) to copy {aPatchFile} file due to error {str(_errmsg)}.")
            except Exception as e:
                _rc = PATCH_COPY_AND_IMAGE_CHECKSUM_VALIDATION_EXCEPTION  
                _errmsg = e
                self.mPatchLogError(
                    f'Exception encountered while retrying ({(_retries + 1):d}/{_max_retries:d}) to copy {aPatchFile} file to the destination node. Error : {str(_errmsg)}')
                self.mPatchLogTrace(traceback.format_exc())

            _retries += 1
        else:
            self.mPatchLogError(
                f'Max {_max_retries:d} retries reached. File {aPatchFile} copying still failed and the error details are {str(_errmsg)}.')
        return _rc, _errmsg


    def mValidateImageCheckSum(self, aPatchFile, aPatchRepo, aRemotePatchBase, aNodeList, aRemoteNecessarySpaceMb):
        """
         This method checks for existence of patch file on remote node and if the
         file is available, it validates the checksum of the file with the local
         file's checksum and if there is any mismatch then remote file get replaced
         with the local file.

         Return:-
          PATCH_SUCCESS_EXIT_CODE                 --> if checksum evaluation and files copy are successful.
          Non PATCH_SUCCESS_EXIT_CODE error codes --> If there any failures
        """

        # Validate ssh connectivity between Exacloud/CPS nodes to launch nodes 
        # to ensure passwdless ssh connectivity exists.
        self.mPatchLogInfo("Passwdless ssh connectivity is validated between Exacloud/CPS nodes to target launch nodes.")
        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
            self.mGetCluPatchCheck().mVerifyExacloudExadataHostSshConnectivity(aNodeList, aSshUser='opc')
        else:
            self.mGetCluPatchCheck().mVerifyExacloudExadataHostSshConnectivity(aNodeList)
 

        def _mValidateRemotePatchFileChecksum(_remote_node):
            '''
             Common method to perform remote patch file checksum
            '''
            _ret = False
            _remote_patch_file_checksum = None
            _cmd = (f"{_checksum_cmd} {_remote_patch_file} | {_awk_cmd}")
            if not _remote_node.mFileExists(_checksum_cmd):
                _cmd = (f"{_checksum_cmd_in_usr_bin} {_remote_patch_file} | {_awk_cmd}")
            _in, _out, _err  = _remote_node.mExecuteCmd(_cmd)
            if _out:
                for _output in _out.readlines():
                   _remote_patch_file_checksum = _output.strip()

            self.mPatchLogInfo(f"Local Patch file : {_local_patch_file}  checksum : {_local_patch_file_checksum}")
            self.mPatchLogInfo(f"Remote Patch file : {_remote_patch_file}  checksum : {_remote_patch_file_checksum}")
            if _remote_patch_file_checksum and _local_patch_file_checksum == _remote_patch_file_checksum:
                _ret = True
            return _ret

        def _mCopyFile(aStatus):
            '''
             Common method to perform mCopyFile based on the conditions
             in _mExecute_FileCopy method.
            '''
            _node = exaBoxNode(get_gcontext())
            self.mSetConnectionUser(_node)
            
            try:
                _node.mConnect(aHost=_remote_node)
                if os.path.exists(_local_patch_file):
                    _node.mCopyFile(_local_patch_file, _remote_patch_file)
                self.mPatchLogInfo(
                    f'Patch file : {_remote_patch_file} copied to node : {_remote_node}. Re-validating copied patch file checksum before extracting...')
                _checksum_status = _mValidateRemotePatchFileChecksum(_node)
                if not _checksum_status:
                    _node.mExecuteCmdLog(f"ls -l {_remote_patch_file}")
                    _patch_copy_end_time = datetime.datetime.now()
                    self.mGetPatchRunningTime(_task_type, _patch_copy_start_time, _patch_copy_end_time)
                    _suggestion_msg = f"Patch file : {_remote_patch_file} corrupted on node : {_remote_node} as checksum of patch files different. Skipping patch file extraction on this node!"
                    _ret = PATCH_COPY_ERROR
                    self.mAddError(_ret, _suggestion_msg)
                    aStatus.append({'node': _remote_node, 'status': 'failed', 'errorcode':_ret, 'errormessage':_suggestion_msg})
                else:
                    self.mPatchLogInfo(
                        f'Patch file: {_remote_patch_file} correctly copied to node: {_remote_node}. Proceeding with patch file extraction...')
                    _i, _o, _e = _node.mExecuteCmd(_patch_unzip_cmd)
                    _exit_code = _node.mGetCmdExitStatus()
                    if int(_exit_code) != 0:
                        _node.mExecuteCmdLog(f"ls -l {_remote_patch_file}")
                        _patch_copy_end_time = datetime.datetime.now()
                        self.mGetPatchRunningTime(_task_type, _patch_copy_start_time, _patch_copy_end_time)
                        _suggestion_msg = f"Error while unziping the patch : {_remote_patch_file} on {str(_remote_node)}, skipping this Node. Error : {_e}"
                        _ret = PATCH_UNZIP_ERROR
                        self.mAddError(_ret, _suggestion_msg)
                        aStatus.append({'node': _remote_node, 'status': 'failed', 'errorcode':_ret, 'errormessage':_suggestion_msg})
                    else:
                        #
                        # When management host is used as launch node, the permission
                        # on dbserver patch dir should be 775
                        #
                        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
                            _remote_dbserver_patchdir = mGetFirstDirInZip(_remote_patch_file).split("/")[-1]
                            _node.mExecuteCmdLog(f"/usr/bin/chmod 775 {aRemotePatchBase}/{_remote_dbserver_patchdir}")
                        self.mPatchLogInfo(
                            f'*** Patch file : {_local_patch_file} >>>> {_remote_patch_file} transferred to Node : {_remote_node}')
            except Exception as e:
                if _node.mIsConnected():
                    _suggestion_msg = f"Copy operation failed with errors on Node : {_remote_node} Error : {str(e)}."
                    _ret = PATCH_COPY_ERROR
                else: # mConnect() failed
                    _suggestion_msg = f"Connect to Node : {_remote_node} failed with {str(e)}"
                    _ret = PATCHING_CONNECT_FAILED
                self.mAddError(_ret, _suggestion_msg)
                aStatus.append({'node': _remote_node, 'status': 'failed', 'errorcode':_ret, 'errormessage':_suggestion_msg})
                self.mPatchLogTrace(traceback.format_exc())

            finally:
                if _node.mIsConnected():
                    _node.mDisconnect()

            # End of _mCopyFile sub function.

        def _mExecute_FileCopy(_remote_node, aStatus):
            '''
             Sub function to copy patches parallely
             to multiple target nodes.
            '''

            _node = exaBoxNode(get_gcontext())
            self.mSetConnectionUser(_node)

            try:
                _node.mConnect(aHost = _remote_node)

                # Create Patch and Images directory if missing.
                _exec_code = f"mkdir -p {aRemotePatchBase}"
                
               

                _node.mExecuteCmdLog(_exec_code)

                # Calculating the free disk space on remote node.
                _patch_base_df_cmd = (f"df -mP {aRemotePatchBase} | tail -n1 | awk '{{print $(NF - 2); }}'")
                _exec_code = f"ExecuteCmd {_patch_base_df_cmd}"

                #
                # When management host is used as launch node, the permission
                # on aRemotePatchBase should be 775
                #
                if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
                     _node.mExecuteCmdLog(f"/usr/bin/chmod 775 {aRemotePatchBase}")

                _i, _o, _e  = _node.mExecuteCmd(_patch_base_df_cmd)
                _patch_base_space_available = int(mFormatOut(_o))

                # If the space to copy patch is not available on the target node
                # this node will be skipped.
                if _patch_base_space_available < (aRemoteNecessarySpaceMb*3):
                    if _node.mIsConnected():
                        _node.mDisconnect()
                    _suggestion_msg = f"{_remote_node} does not have enough space in {aRemotePatchBase} to be used as the patching base. Needed {((aRemoteNecessarySpaceMb * 3) / 1024):.2f} GB({(aRemoteNecessarySpaceMb * 3):.2f} MB), got {(_patch_base_space_available / 1024):.2f} GB({(_patch_base_space_available):.2f} MB)."
                    _ret = INSUFFICIENT_SPACE_ON_PATCH_BASE
                    self.mAddError(_ret, _suggestion_msg)
                    aStatus.append({'node': _remote_node, 'status': 'failed', 'errorcode':_ret, 'errormessage':_suggestion_msg})
                else:
                    self.mPatchLogInfo(
                        f"Sufficient space available to stage patches on Node : {_remote_node}, Location : {aRemotePatchBase}, Required : {(aRemoteNecessarySpaceMb / 1024):.2f} GB({(aRemoteNecessarySpaceMb):.2f} MB), Available Space : {(_patch_base_space_available / 1024):.2f} GB({(_patch_base_space_available):.2f} MB)")

                    if not _node.mFileExists(_remote_patch_file):
                        '''
                         Patch file not yet staged. Go ahead and copy 
                        '''
                        self.mPatchLogInfo(
                            f'*** Patch file : {aPatchFile} missing on node : {_remote_node} . Copying in progress...')
                        if _node.mIsConnected():
                            _node.mDisconnect()
                        _mCopyFile(aStatus)

                    else:
                        '''
                         Patch file already present. 
                         Get the remote file checksum and compare with local file checksum.
                         On checksum mismatch, copy local file to remote node.
                        '''
                        _checksum_status = _mValidateRemotePatchFileChecksum(_node)
                        if not _checksum_status:
                            self.mPatchLogInfo(
                                f'*** Deleting remote patch file : {_remote_patch_file} on node : {_remote_node} as checksum of patch files different.')
                            _node.mExecuteCmdLog(f"rm -f {_remote_patch_file}")
                            self.mPatchLogInfo(
                                f'*** Copying patch file : {aPatchFile}  to node : {_remote_node} in progress...')
                            if _node.mIsConnected():
                                _node.mDisconnect()
                            _mCopyFile(aStatus)
                        else:
                            self.mPatchLogInfo(
                                f"Patch file : {_remote_patch_file} already staged on node : {_remote_node} and matches with source file checksum.")

            except ValueError as e:
                _suggestion_msg = f"Could not parse {aRemotePatchBase} for free space on {str(_remote_node)}. Expected a number, got {str(e)}. Trying a different node"
                _ret = PATCH_COPY_ERROR
                aStatus.append({'node': _remote_node, 'status': 'failed', 'errorcode':_ret, 'errormessage':_suggestion_msg})
                if _node.mIsConnected():
                    _node.mDisconnect()

            except Exception as e:
                if _node.mIsConnected():
                    # disambiguate dir creation or df execution
                    _suggestion_msg = f"Prior to copy, {_exec_code} execution on Node : {str(_remote_node)} failed with {str(e)}"
                    _ret = PATCH_COPY_ERROR
                    _node.mDisconnect()
                else: # mConnect() failed
                    _suggestion_msg = f"Connect to Node : {_remote_node} failed with {str(e)}"
                    _ret = PATCHING_CONNECT_FAILED
                self.mAddError(_ret, _suggestion_msg)
                aStatus.append({'node': _remote_node, 'status': 'failed', 'errorcode':_ret, 'errormessage':_suggestion_msg})
                self.mPatchLogTrace(traceback.format_exc())

        # End of _mExecute_FileCopy sub function.

        _patch_copy_start_time = datetime.datetime.now()
        _ret = PATCH_SUCCESS_EXIT_CODE

        _local_patch_file = os.path.join(aPatchRepo, aPatchFile)
        _remote_patch_file = os.path.join(aRemotePatchBase, aPatchFile)
        _task_type = "Patch_copy"

        # If patch file does not exist at source, Patch copy exits with error.
        self.mPatchLogInfo(f"*** Generating checksum for the patch file : {_local_patch_file} ***")
 
        _checksum_cmd = '/bin/sha256sum'
        _checksum_cmd_in_usr_bin = '/usr/bin/sha256sum'
        _awk_cmd = "/bin/awk '{print $1}'"

        _local_patch_file_checksum = None
        _cmd = f'{_checksum_cmd} {_local_patch_file}'
        if os.path.isfile(_checksum_cmd) is False:
            _cmd = f'{_checksum_cmd_in_usr_bin} {_local_patch_file}'
        _in, _out, _err = self.mGetCluControl().mExecuteCmd(_cmd)
        if _out:
           _in, _out, _err = self.mGetCluControl().mExecuteCmd(_awk_cmd, aStdIn=_out)
           if _out:
              for _output in _out.readlines():
                 _local_patch_file_checksum = _output.strip()

        if _local_patch_file_checksum is None:
           _suggestion_msg = f"Local Patch file : {_local_patch_file} not found, unable to transfer file. Aborting."
           _ret = PATCH_COPY_ERROR
           self.mAddError(_ret, _suggestion_msg)
           return _ret

        _cmd = f"/bin/du -sh {_local_patch_file} "
        _in, _out, _err = self.mGetCluControl().mExecuteCmd(_cmd)

        _cmd_size = "/bin/awk '{print $1}'"
        _in, _out, _err = self.mGetCluControl().mExecuteCmd(_cmd_size, aStdIn=_out)
        _file_size = ""
        for _output in _out.readlines():
            _file_size = _output.strip()

        # Patch unzip command is prepared based on patch file extension.
        if _remote_patch_file.endswith('.zip'):
            _patch_unzip_cmd = f"unzip -d {aRemotePatchBase} -o {_remote_patch_file}"

        """
         Parallelize execution on all target nodes. In case
         of Dom0/DomU patching, patches are copied to multiple
         nodes. In case of Cell and IBSwitches patching, patches
         are copied to one launch node. For more details regarding
         parallel file copy, please refer mParallelFileLoad and
         mCheckSystemImage methods in clucontrol file.
        """
        _plist = ProcessManager()
        _rc_status = _plist.mGetManager().list()

        for _remote_node in aNodeList:
            if self.mIsClusterLessUpgrade() and _remote_node not in self.mGetCluControl().mGetHostList():
                # Only in clusterless CELL, the launch node will not be part of HostList
                self.mGetCluControl().mAppendToHostList(_remote_node)
                self.mGetCluControl().mHandlerImportKeys()
            _p = ProcessStructure(_mExecute_FileCopy, [_remote_node, _rc_status], _remote_node)

            '''
             Timeout parameter configurable in Infrapatching.conf
             Currently it is set to 30 minutes
            '''
            _p.mSetMaxExecutionTime(self.mGetValidateChecksumExecutionTimeoutInSeconds())

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
            _suggestion_msg = f'Timeout while copying patches to launch nodes : {str(aNodeList)}.'
            self.mAddError(PATCH_COPY_ERROR, _suggestion_msg)
            raise Exception(_suggestion_msg)

        # validate the return codes
        for _rc_details in _rc_status:
            if _rc_details['status'] == "failed":
                _err_msg = f"Patch copy method encountered error. {_rc_details['errormessage']}"
                self.mPatchLogError(_err_msg)
                return _rc_details['errorcode'], _err_msg

        return PATCH_SUCCESS_EXIT_CODE, None

    def mGetPatchRunningTime(self, aTaskType, aPatchStartTime=None, aPatchEndTime=None):
        """
        This method computes the time taken for a patch operation to
        complete.
        """

        if aPatchStartTime is None or aPatchEndTime is None:
            self.mPatchLogWarn(
                f"Task Type : {aTaskType} execution time could not be computed as the Start or end time is None.")
        else:
            _execution_time = aPatchEndTime - aPatchStartTime
            self.mPatchLogInfo(f"Task Type : {aTaskType} execution time : {str(_execution_time)}")

    def mUpdateCnsJsonPayload(self, cnsjson):
        """
        Post CNS payload for patch state change.
        """

        # Save cns json in db
        _reqobj = self.mGetCluControl().mGetRequestObj()
        if _reqobj:
            self.mPatchLogInfo('mUpdateCnsJsonPayload - Save the patch notification JSON to database')
            _db = ebGetDefaultDB()
            _db.mUpdateJsonPatchReport(_reqobj.mGetUUID(), json.dumps(cnsjson))
            self.mPatchLogInfo('mUpdateCnsJsonPayload - Completed saving the patch notification JSON to database')

    def mSleepBtwNodes(self):
        """
        Sleep user designated number of seconds with proper dialogue message.
        Generally, it suppose to sleep if node upgrade in rolling manner.
        Return: Simply return if sleep time got over.
        """
        _elapsed_time = 0
        NODE_SLEEP_INTERVAL_IN_SECONDS = self.mGetNodeSleepIntervalInSeconds()
        self.mPatchLogInfo("Sleeping between nodes started")
        self.mUpdatePatchProgressStatus(aSleepStatus="yes")
        while _elapsed_time < self.mGetSleepbetweenComputeTimeInSec():
            self.mPatchLogInfo(f"Elaspsed sleep time = {_elapsed_time}")

            # Sleep regularly for every NODE_SLEEP_INTERVAL_IN_SECONDS. But, if
            # user specified lesser than NODE_SLEEP_INTERVAL_IN_SECONDS then, we
            # need to sleep those many seconds only.
            _remaining_time_in_sec = self.mGetSleepbetweenComputeTimeInSec() - _elapsed_time
            self.mPatchLogInfo(f"Sleep ended in {_remaining_time_in_sec} seconds")
            if _remaining_time_in_sec >= NODE_SLEEP_INTERVAL_IN_SECONDS:
                time.sleep(NODE_SLEEP_INTERVAL_IN_SECONDS)
                _elapsed_time += NODE_SLEEP_INTERVAL_IN_SECONDS
            else:
                time.sleep(_remaining_time_in_sec)
                _elapsed_time += _remaining_time_in_sec
        else:
            self.mPatchLogInfo("Sleeping between nodes ended")
            self.mUpdatePatchProgressStatus(aSleepStatus="no")

    def mUpdatePatchProgressStatus(self, aNodeList=[], aDiscardedNodeList=[], aPatchmgrXmlData=None, aSleepStatus=None, aNodeType=None):
        """
           Following operation will be performed :-

               1. Update initial nodes status for discarded node
               2. Update initial nodes status for nodes which requires upgrade.

           Param list:
             aNodeList          --> List of nodes to which are expected undergo patching
             aDiscardedNodeList --> If the node is already upto date, default values
                                    are set
             aSleepStatus       --> Contains sleep parameter details to be updated in
                                    node progress json.
             aPatchmgrXmlData   --> contains the patchmgr xml data.

             Sample json:
             "node_progressing_status": {
                    "infra_patch_start_time": "2022-05-10 09:31:43+0000",
                    "node_patching_progress_data": [{
                            "node_name": "ecc201vm01.tawn.com",
                            "last_updated_time": "2022-02-09 10:20:33+0000",
                            "patchmgr_start_time": "2022-02-09 10:17:25+0000",
                            "status": "Pending",
                            "status_details": "Precheck",
                            "target_type": "domu"
                        },
                        {
                            "node_name": "ecc201vm02.tawn.com",
                            "last_updated_time": "2022-02-09 10:16:54+0000",
                            "patchmgr_start_time": "2022-02-09 10:10:44+0000",
                            "status": "Completed",
                            "status_details": "Succeeded",
                            "target_type": "domu"
                        }
                    ]
                },
        """
        patch_progressing_status_json = {}
        _json_patch_report = {}
        _data = {}
        _json_patch_report["data"] = _data
        _patch_start_time = time.strftime("%Y-%m-%d %H:%M:%S%z")
        _patch_start_time_patch_transition_state_map = {
            "dom0-rolling-patch":"Started",
            "dom0-rolling-rollback": "Started",
            "dom0-rolling-patch_prereq_check": "Started",
            "dom0-non-rolling-patch": "Started",
            "dom0-non-rolling-rollback": "Downgrading",
            "dom0-non-rolling-patch_prereq_check": "Started",
            "domu-rolling-patch": "Started",
            "domu-rolling-rollback": "Started",
            "domu-rolling-patch_prereq_check": "Started",
            "domu-non-rolling-patch": "Started",
            "domu-non-rolling-rollback": "Started",
            "domu-non-rolling-patch_prereq_check": "Started",
            "cell-rolling-patch": "Updating",
            "cell-rolling-rollback": "Downgrading",
            "cell-rolling-patch_prereq_check": "Started",
            "cell-rolling-rollback_prereq_check": "Started",
            "cell-non-rolling-patch": "Updating",
            "cell-non-rolling-rollback": "Downgrading",
            "cell-non-rolling-patch_prereq_check": "Started",
            "cell-non-rolling-rollback_prereq_check": "Started",
            "ibswitch-rolling-patch": "Updating",
            "ibswitch-rolling-rollback": "Downgrading",
            "ibswitch-rolling-patch_prereq_check": "Started",
            "ibswitch-rolling-rollback_prereq_check": "Started",
            "ibswitch-non-rolling-patch": "Updating",
            "ibswitch-non-rolling-rollback": "Downgrading",
            "ibswitch-non-rolling-patch_prereq_check": "Started",
            "ibswitch-non-rolling-rollback_prereq_check": "Started",
            "roceswitch-rolling-patch": "Updating",
            "roceswitch-rolling-rollback": "Downgrading",
            "roceswitch-rolling-patch_prereq_check": "Started",
            "roceswitch-rolling-rollback_prereq_check": "Started",
            "roceswitch-non-rolling-patch": "Updating",
            "roceswitch-non-rolling-rollback": "Downgrading",
            "roceswitch-non-rolling-patch_prereq_check": "Started",
            "roceswitch-non-rolling-rollback_prereq_check": "Started"
        }

        def _patch_update_json_to_db(aJsonPatchReport):
            if aJsonPatchReport:
                _reqobj = self.mGetCluControl().mGetRequestObj()
                if _reqobj:
                    self.mPatchLogInfo('Updating patch status JSON with Node Progressing status to Exacloud DB.')
                    _db = ebGetDefaultDB()
                    _db.mUpdateJsonPatchReport(_reqobj.mGetUUID(), json.dumps(aJsonPatchReport))
            else:
                self.mPatchLogInfo('mUpdatePatchProgressStatus : Json Patch Report is empty. Node Progressing status Json is not updated to Exacloud DB')

        if aSleepStatus is not None:
            # Get updated patch Report Json from Exacloud DB and update Node Progressing status
            _, _, _, _json_patch_report = self.mGetAllPatchListDetails()
            if _json_patch_report:
                _json_patch_temp_data = json.loads(_json_patch_report)
                if _json_patch_temp_data and _json_patch_temp_data["data"] and _json_patch_temp_data["data"]["node_progressing_status"]:
                    self.mPatchLogInfo('Updating sleep_infra_patch in node_progressing_status.')
                    _json_patch_temp_data["data"]["node_progressing_status"]['sleep_infra_patch'] = aSleepStatus
                    _patch_update_json_to_db(_json_patch_temp_data)
                else:
                    self.mPatchLogInfo('Json Patch Report with node_progressing_status details not found.')

        if aNodeList or aDiscardedNodeList:
            patch_progressing_status_json['sleep_infra_patch'] = "no"
            patch_progressing_status_json['infra_patch_start_time'] = _patch_start_time
            _node_progress_list = []
            if len(aDiscardedNodeList) > 0:
                for _node_name in aDiscardedNodeList:
                    _node_progress_list.append({'node_name': _node_name, 'target_type': self.mGetCurrentTargetType(),
                                         'patchmgr_start_time': _patch_start_time, 'last_updated_time': _patch_start_time,
                                         'status': "Completed", 'status_details': "Succeeded"})

            if len(aNodeList) > 0:
                for _node_name in aNodeList:
                    _node_progress_list.append({'node_name': _node_name, 'target_type': self.mGetCurrentTargetType(),
                                                'patchmgr_start_time': _patch_start_time,
                                                'last_updated_time': _patch_start_time,
                                                'status': "NotStarted", 'status_details': "Not Attempted"})

            patch_progressing_status_json['node_patching_progress_data'] = _node_progress_list
            _json_patch_report['data']['node_progressing_status'] = patch_progressing_status_json
            _patch_update_json_to_db(_json_patch_report)

        else: #Update Case

            if aPatchmgrXmlData:
                try:
                    # Get into root of patchmgr.xml
                    _root = ET.fromstring(aPatchmgrXmlData)

                    # Get updated patch status Json from Exacloud DB
                    patch_progressing_status_json = self.mGetPatchProgressStatus()

                    _launch_node = _root.findall('./Global_info/Launch_Node/Transition')
                    if _launch_node is not None:
                        _patch_start_time = _launch_node[0].attrib['LAST_UPDATE_TIMESTAMP']

                    _infra_patch_status = "Pending"

                    if not patch_progressing_status_json:
                        # populate node_progress_data if exacloud db does not have the data, eg: there are scenarios like active-active rolling upgrade
                        # and patch retry scenario can lead into this situation
                        # Here when ecra switch over happens exacloud db data is not synched
                        self.mPatchLogInfo("Node progress data is empty so trying to update explicitly.")
                        patch_progressing_status_json = self.mPopulateNodeProgressDataIfMissing()

                    for _eachpatch_progressing_status_type in _root.findall('./' + aNodeType):

                        _node_name = _eachpatch_progressing_status_type.attrib['NAME']

                        # Goto last patch transition state
                        _cur_pstate_tran = None
                        for _each_pstate_tran in _eachpatch_progressing_status_type.findall('./Patch_State/Transition'):
                            _cur_pstate_tran = _each_pstate_tran
                            if _cur_pstate_tran is not None and _cur_pstate_tran.attrib['VALUE'] in [ "Succeeded", "Failed" ]:
                                _infra_patch_status = "Completed"

                            _patch_transition_map_key = f"{self.mGetCurrentTargetType()}-{self.mGetOpStyle()}-{self.mGetTask()}"
                            _patch_transition_map_value = "Started"
                            if _patch_transition_map_key in _patch_start_time_patch_transition_state_map:
                                _patch_transition_map_value = _patch_start_time_patch_transition_state_map[_patch_transition_map_key]

                            if _cur_pstate_tran is not None and _cur_pstate_tran.attrib['VALUE'] == _patch_transition_map_value:
                                _patch_start_time = _cur_pstate_tran.attrib['LAST_UPDATE_TIMESTAMP']

                        if _cur_pstate_tran is not None and 'node_patching_progress_data' in patch_progressing_status_json.keys():
                            # for _list in list(patch_progressing_status_json.keys()):
                            for _patch_progress_elem in patch_progressing_status_json['node_patching_progress_data']:
                                if "node_name" in _patch_progress_elem.keys() and _patch_progress_elem["node_name"].upper() == _node_name.upper():
                                    if _patch_start_time is not None:
                                        _patch_progress_elem["patchmgr_start_time"] = _patch_start_time

                                    _patch_progress_elem["last_updated_time"] = _cur_pstate_tran.attrib['LAST_UPDATE_TIMESTAMP']
                                    _patch_progress_elem["status"] = _infra_patch_status
                                    _patch_progress_elem["status_details"] = _cur_pstate_tran.attrib['VALUE']
                        else:
                            self.mPatchLogInfo("mUpdatePatchProgressStatus - '_cur_pstate_tran' is None, hence 'last_updated_time', 'patchmgr_start_time' and 'status_details' are not populated yet.")
                except Exception as e:
                    self.mPatchLogWarn("mUpdatePatchProgressStatus - aPatchmgrXmlData is not formed yet or is not populated with all the expected fields.")
                    self.mPatchLogTrace(traceback.format_exc())
            else:
                self.mPatchLogInfo("mUpdatePatchProgressStatus - aPatchmgrXmlData is yet to be populated.")
        return patch_progressing_status_json

    def mPopulateNodeProgressDataIfMissing(self):
        """
        This method does the following
        If ecra payload contains node_progress_data in idempotency attribute, prepare node_progress_data from ecra idempotency payload data
        otherwise prepare the node_progress_data for all the nodes with pending state
        """
        _patch_progressing_status_json = {}
        _node_progress_data_list_from_ecra_idempotency_payload = []
        if self.mPatchRequestRetried() and self.mGetIdemPotencydata() and "node_progressing_status" in self.mGetIdemPotencydata() \
                and "node_patching_progress_data" in self.mGetIdemPotencydata()["node_progressing_status"] :
            _node_progress_data_list_from_ecra_idempotency_payload = self.mGetIdemPotencydata()["node_progressing_status"]["node_patching_progress_data"]
            if _node_progress_data_list_from_ecra_idempotency_payload and len(_node_progress_data_list_from_ecra_idempotency_payload) > 0:
                self.mPatchLogInfo("Updating node_progress_data status from ecra idempotency payload data")
                _patch_progressing_status_json['node_patching_progress_data'] = _node_progress_data_list_from_ecra_idempotency_payload

        #  Prepare node_progress_data for all nodes with pending state
        if "node_patching_progress_data" not in _patch_progressing_status_json:
            _node_list = []
            _target_type = self.mGetCurrentTargetType()
            if _target_type == PATCH_DOMU:
                _node_list = self.mGetCustomizedDomUList()
            elif _target_type == PATCH_DOM0:
                _node_list = self.mGetCustomizedDom0List()
            elif _target_type == PATCH_CELL:
                _node_list = self.mGetCustomizedCellList()
            elif _target_type in [ PATCH_IBSWITCH, PATCH_ROCESWITCH ] :
                _node_list = self.mGetSwitchList()

            _patch_start_time = time.strftime("%Y-%m-%d %H:%M:%S%z")
            _node_progress_list = []
            if _node_list and len(_node_list) > 0:
                self.mPatchLogInfo(
                    f"Updating {_target_type} node_progress_data status as Pending for : {json.dumps(_node_list, indent=4)}.")
                for _node_name in _node_list:
                    _node_progress_list.append({'node_name': _node_name, 'target_type': _target_type,
                                                'patchmgr_start_time': _patch_start_time,
                                                'last_updated_time': _patch_start_time,
                                                'status': "Pending", 'status_details': "Pending"})
                _patch_progressing_status_json['node_patching_progress_data'] = _node_progress_list

        self.mPatchLogInfo(
            f"mPopulateNodeProgressDataIfMissing - final node_progress_data status is - {json.dumps(_patch_progressing_status_json, indent=4)}")
        return _patch_progressing_status_json

    def mUpdateNodePatcherLogDir(self, aNodePatcher, aCnsString):
        """
         This method :

            1) As part of Infra patch idempotent changes, patchmgr log directory were renamed and
            appended with the hostname details and hence when CNS details were collected at the
            end of patch operation, it would fail due to missing patchmgr log directory as it is
            already renamed.

            2) update  the right log location until the CNS collection is complete.
        """
        
        _cns_append_log_path = ""
        _node_name_to_be_appended = aNodePatcher.split(".")[0]
        if self.mGetPatchmgrLogPathOnLaunchNode().find(_node_name_to_be_appended) == -1:
            _cns_append_log_path = self.mGetPatchmgrLogPathOnLaunchNode() + "_" + _node_name_to_be_appended

        self.mPatchLogInfo(
            f"Updating Patchmgr log location for collecting notifications : {self.mGetPatchmgrLogPathOnLaunchNode()}.")
        self.mPatchLogInfo(f"Log path updated to metadata file : {_cns_append_log_path}.")
        _node_patch_progress = os.path.join(self.mGetLogPath(), aCnsString)
        try:
            with open(_node_patch_progress, "w") as write_nodestat:
                write_nodestat.write(f"{aNodePatcher}:{_cns_append_log_path}")
        except Exception as e:
            self.mPatchLogWarn(f'Failed to write {_node_patch_progress}: {str(e)}')
            self.mPatchLogTrace(traceback.format_exc())

    def mCleanupExadataPatches(self, aLaunchNodeCandidates):
        """
        This method Purges all the exadata patch files with versions
        other than that of the current target version passed, active
        and inactive exadata versions. Patches are purged on the launch
        nodes like Dom0(In case of Dom0, cell and Switch targets) and
        DomU.

        Return "0x00000000" -> PATCH_SUCCESS_EXIT_CODE if success,
        otherwise return error code.
        """

        if self.mIsMockEnv():
            # in mock setup, skip rack specific operations
            return

        def _purge_exadata_patches(aNode, aStatus):
            '''
             Cleanup of Exadata patches are performed
             on the custom node list.
            '''
            _node = exaBoxNode(get_gcontext())
            self.mSetConnectionUser(_node)
            _active_image_version = None
            _inactive_image_version = None
            _list_of_files_to_be_purged_string = None
            _purge_patches = True
            try:
                _node.mConnect(aHost=aNode)
                '''
                  Fetching Exadata active exadata version using imageinfo command and inactive 
                  exadata version details using dbserver_backup.sh script output. Exadata patches 
                  from the current Exadata version, previous exadata and current target version
                  (It may be same as the active version at times if the patch is applied and upgrade 
                  fails.) will be preserved,all other Exadata patch files will be purged.
                  
                    Example of an "ls -ltr" command output from the launch nodes.
                
                     drwxr-xr-x 3 root root        3896 May  6 05:55
                     dbserver.patch.zip_exadata_ovs_21.2.11.0.0.220414.1_Linux-x86-64.zip
                     drwxr-xr-x 2 root root        3896 May  6 06:24 crashfiles
                     drwxr-xr-x 2 root root        3896 May  6 09:43 13.2.9.0.0.220216.patch.zip
                     drwxr-xr-x 2 root root        3896 May  6 09:43 14.2.9.0.0.220216.patch.zip
                     drwxr-xr-x 2 root root        3896 May  6 09:43 13.2.7.0.0.211221.switch.patch.zip
                     drwxr-xr-x 2 root root        3896 May  6 09:43 14.2.7.0.0.211221.switch.patch.zip
                     drwxr-xr-x 2 root root        3896 May  6 09:43 15.2.7.0.0.211221.switch.patch.zip
                     drwxr-xr-x 2 root root        3896 May  6 09:43 16.2.7.0.0.211221.switch.patch.zip
                     drwxr-xr-x 2 root root        3896 May  6 09:43 dbserver.patch.zip_exadata_ovs_13.2.11.0.0.220414.1_Linux-x86-64.zip
                     drwxr-xr-x 2 root root        3896 May  6 09:43 dbserver.patch.zip_exadata_ovs_14.2.11.0.0.220414.1_Linux-x86-64.zip
                     drwxr-xr-x 2 root root        3896 May  6 09:43 dbserver.patch.zip_exadata_ovs_15.2.11.0.0.220414.1_Linux-x86-64.zip
                     drwxr-xr-x 8 root root        3896 May  6 09:44 dbnodeupdate.patchmgr
                     [root@slcs27adm03 EXAVMIMAGES]#
                '''
                _cmd_get_active_image_version = "/usr/local/bin/imageinfo -ver"
                _i, _o, _e = _node.mExecuteCmd(_cmd_get_active_image_version)
                _exit_code = int(_node.mGetCmdExitStatus())
                if int(_exit_code) == 0:
                    _o = _o.readlines()
                    _active_image_version = _o[0].strip()
                    self.mPatchLogInfo(f"Active image version fetched to purge patches : {_active_image_version}")
                else:
                    self.mPatchLogWarn(f"Unable to get image version on the launch node : {aNode}")
                    aStatus.append({'node': aNode, 'status': 'failed'})
                    _purge_patches = False

                additional_dbserver_cmd = ""
                # need to check if we need to pass encrypt script
                if self.mCheckConditionsForEncryptPatching() and mIsFSEncryptedNode(_node, aNode, self):
                    additional_dbserver_cmd = f" --key-api {KEY_API}"

                _cmd_get_inactive_image_version = f"/opt/oracle.SupportTools/dbserver_backup.sh --ignore-nfs-smbfs-mounts --check-rollback --get-backup-version {additional_dbserver_cmd}"
                _i, _o, _e = _node.mExecuteCmd(_cmd_get_inactive_image_version)
                _exit_code = int(_node.mGetCmdExitStatus())
                if int(_exit_code) == 0 or int(_exit_code) == 2:
                    _inactive_image_version = (_o.readlines()[-1]).strip()

                '''
                 Example of an inactive version with exasplice patch installed.

                  70230588-a9cc-11ee-86fc-00001701a08b_cluctrl.backup_image.log:2024-01-03 00:10:36,019 
                  - dfltlog - INFO - 17212 - Dom0Handler - INFO - Inactive image version fetched to purge 
                  patches : 22.1.13.0.0.230712.exasplice.230814

                  >>> active_version = "22.1.13.0.0.230712.exasplice.230814"
                  >>> active_version.split(".exasplice.", 1)[0]
                  '22.1.13.0.0.230712'
                  >>>
                '''
                if _inactive_image_version and (_inactive_image_version.find('exasplice') != -1):
                    _inactive_image_version = _inactive_image_version.split(".exasplice.", 1)[0]

                if _active_image_version and (_active_image_version.find('exasplice') != -1):
                    _active_image_version = _active_image_version.split(".exasplice.", 1)[0]

                if (_inactive_image_version is not None and _inactive_image_version == _active_image_version) or (_active_image_version and _active_image_version == self.mGetTargetVersion()):
                    _purge_patches = False

                '''
                 If active image version is empty or None, patch purge will be skipped.
                '''
                if _purge_patches:
                    '''
                     Remote patch base is /EXAVIMAGES for dom0, cells and switches
                     and /u02 in case of DomU.
                    '''
                    if PATCH_DOMU in self.mGetTargetTypes():
                        _remote_patch_base = DOMU_PATCH_BASE
                    else:
                        _remote_patch_base = PATCH_BASE

                    if _active_image_version:
                        _list_of_files_to_be_purged_string = _active_image_version

                    if _active_image_version and _active_image_version != self.mGetTargetVersion():
                        self.mPatchLogInfo("Target version patches will be preserved on launch nodes only in case current active version and target version are different.")
                        self.mPatchLogInfo(
                            f"Active Exadata version : {str(_active_image_version)}, Target Exadata version : {str(self.mGetTargetVersion())}")
                        _list_of_files_to_be_purged_string = _list_of_files_to_be_purged_string + "|" + self.mGetTargetVersion()

                    '''
                      In case of a newly provisioned environment, backup version 
                      will not be available.
                    '''
                    if _inactive_image_version:
                        self.mPatchLogInfo(
                            f"Inactive image version fetched to purge patches : {_inactive_image_version}")
                        _list_of_files_to_be_purged_string = _list_of_files_to_be_purged_string + "|" + _inactive_image_version

                    if _list_of_files_to_be_purged_string:
                        _cmd_list_files_patch_to_be_purged = f"ls -ld {_remote_patch_base}/*patch.zip* | egrep -v '{_list_of_files_to_be_purged_string}' | /usr/bin/awk '{{print $9}}' | xargs rm -rfv"
                        _node.mExecuteCmdLog(_cmd_list_files_patch_to_be_purged)

            except Exception as e:
                self.mPatchLogWarn(f"Unable to purge exadata patches on {aNode}. Error : {str(e)}")
                self.mPatchLogTrace(traceback.format_exc())

            finally:
                self.mPatchLogInfo("Purging of Exadata patches task completed.")
                if _node.mIsConnected():
                    _node.mDisconnect()
        # End of _purge_exadata_patches method

        # Exadata patch cleanup is skipped if launch node is localhost or mgmt host
        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsLocalHostLaunchNode') or self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
            self.mPatchLogInfo("Skipping cleanup of exadata patches on launch node")
            return

        """
         Purge Exadata patches on all target
         types and nodes in parallel. 
        """
        _plist = ProcessManager()
        _rc_status = _plist.mGetManager().list()

        self.mPatchLogInfo("Purging of Exadata patches(if any) will be performed.")
        for _remote_node in aLaunchNodeCandidates:
            _p = ProcessStructure(_purge_exadata_patches, [_remote_node, _rc_status], _remote_node)

            '''
             Timeout parameter configurable in Infrapatching.conf
             Currently it is set to 10 minutes
            '''
            self.mPatchLogInfo(
                f"Configurable parameter for parallel execution timeout in Infrapatching.conf currently set to {str(self.mGetExadataPatchPurgeExecutionTimeoutInSeconds())} seconds")
            _p.mSetMaxExecutionTime(self.mGetExadataPatchPurgeExecutionTimeoutInSeconds())

            _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
            _p.mSetLogTimeoutFx(self.mPatchLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()

        if _plist.mGetStatus() == "killed":
            self.mPatchLogWarn("Timeout while purging Exadata patches.")

        # validate the return codes
        for _rc_details in _rc_status:
            if _rc_details['status'] == "failed":
                self.mPatchLogWarn("Purging Exadata patches failed.")

    def mCheckFileExistsOnRemoteNodes(self, aNodeList, aFile):
        """
        This method is going to check for the presence of the file on the remote node list and
        return True if it exists on all the nodes otherwise False
        """
        _ret = False
        _nodes_missing_file = []

        def _mCheckFileExistsOnRemoteNode(aNode, aFileToCheck, aStatus):
            """
             This sub method checks for the presence of the file.
             It adds node details to aStatus where file check presence is failed.
            """
            if self.mGetCluPatchCheck().mCheckFileExists(aNode, aFileToCheck):
                self.mPatchLogInfo(f"{aFileToCheck} is present on {aNode}.")
            else:
                aStatus.append({'node': aNode, 'status': 'failed'})
            # end of _mCheckFileExistsOnRemoteNode
        
        """
         Parallelize checking for the presence of the file on remote nodes.
        """
        _plist = ProcessManager()
        _rc_status = _plist.mGetManager().list()
        for _node_to_check in aNodeList:
            _p = ProcessStructure(_mCheckFileExistsOnRemoteNode, [_node_to_check, aFile, _rc_status], _node_to_check)

            """
             Timeout parameter remote_nodes_file_check_max_thread_execution_time_in_seconds
             configurable in Infrapatching.conf. Currently it is set to 30 minutes

             remote_nodes_file_check_thread_join_timeout_in_seconds is configurable and is set
             to 30 seconds in infrapatching.conf.
             """
            _p.mSetMaxExecutionTime(self.mCheckFileExistsOnRemoteNodesMaxThreadExecutionTimeoutSeconds())
            _p.mSetJoinTimeout(self.mCheckFileExistsOnRemoteNodesThreadJoinTimeoutSeconds())
            _p.mSetLogTimeoutFx(self.mPatchLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()

        if _plist.mGetStatus() == "killed":
            self.mPatchLogError(
                f"Timeout occurred while checking for the presence of the file {aFile} on remote node list : {json.dumps(aNodeList, indent=4)}.")
            return _ret, _nodes_missing_file

        # Check for the nodes where file is missing
        for _rc_details in _rc_status:
            if _rc_details['status'] == "failed":
                _nodes_missing_file.append(_rc_details['node'])

        # All nodes have the file
        if len(_nodes_missing_file) == 0:
            _ret = True

        return _ret, _nodes_missing_file


    def mRollbackIsAvailable(self, aNode):
        # Looks for an available image to rollback in aNode.
        def _mRunCheckRollbackCmd(aNode):
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=aNode)

            additional_dbserver_cmd = ''
            # need to check if we need to pass encrypt script
            if self.mCheckConditionsForEncryptPatching() and mIsFSEncryptedNode(_node, aNode, self):
                additional_dbserver_cmd = f' --key-api {KEY_API}'

            check_rollback_cmd = (f'/opt/oracle.SupportTools/dbserver_backup.sh --ignore-nfs-smbfs-mounts -check-rollback {additional_dbserver_cmd} | grep -i "rollback is available"')
            _i, _o, _e = _node.mExecuteCmd(check_rollback_cmd)
            if _node.mIsConnected():
                _node.mDisconnect()
            if _o:
                return True
            else:
                return False

        '''
         Rollback availablility is performed only 
         on the custom node list.
        '''
        if self.mGetCurrentTargetType() == PATCH_DOM0:
            _node_list = self.mGetCustomizedDom0List()
        elif self.mGetCurrentTargetType() == PATCH_DOMU:
            _node_list = self.mGetCustomizedDomUList()

        if aNode in _node_list:
            return _mRunCheckRollbackCmd(aNode)

    def mValidateRootFsSpaceUsage(self):
        """
         This method validates for adequate space on root
         partition for the patch operation to work
         efficiently.

         return PATCH_SUCCESS_EXIT_CODE if adequate space is
                available on the root partition.

         return INSUFFICIENT_SPACE_ON_ROOT_PARTITION otherwise.
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _node = exaBoxNode(get_gcontext())
        _required_space_to_patch_root_fs = 0
        _space_check_failed_on_nodes_list = []
        _node_list = []
      
        def _perform_root_space_check(_remote_node, aStatus):
            _ret = PATCH_SUCCESS_EXIT_CODE
            try:
                _node.mConnect(aHost = _remote_node)

                '''
                 Calculating the free disk space on remote node for root FS.

                 [root@slcs27adm03 ~]# /bin/df -mP / | /usr/bin/tail -n1 | /bin/awk '{print $(NF - 2); }' | /usr/bin/tr -d 'M'
                 13239
                 [root@slcs27adm03 ~]#
                '''
                _patch_base_df_cmd = f"/bin/df -mP {ROOT_PARTITION} | /usr/bin/tail -n1 | /bin/awk '{{print $(NF - 2); }}' | /usr/bin/tr -d 'M'"
                _sufficient_space_available = True
                _i, _o, _e  = _node.mExecuteCmd(_patch_base_df_cmd)
                _patch_base_space_available = int(mFormatOut(_o))

                # If the space on root partition is not sufficient
                # Infra patching will be stopped as it is eventually fails
                # during patchmgr run if there is no sufficient space.
                if _patch_base_space_available < (_required_space_to_patch_root_fs):
                    if _node.mIsConnected():
                        _node.mDisconnect()
                    _suggestion_msg = f"{_remote_node} does not have enough space in {ROOT_PARTITION} for performing patch. Needed {(_required_space_to_patch_root_fs / 1024):.2f} GB({(_required_space_to_patch_root_fs):.2f} MB), got {(_patch_base_space_available / 1024):.2f} GB({(_patch_base_space_available):.2f} MB)."
                    self.mAddError(INSUFFICIENT_SPACE_ON_ROOT_PARTITION, _suggestion_msg)
                    aStatus.append({'node': _remote_node, 'status': 'failed'})
                else:
                    self.mPatchLogInfo(
                        f"Sufficient space available on the root partition on Node : {_remote_node}, Location : {ROOT_PARTITION}, Required : {(_required_space_to_patch_root_fs / 1024):.2f} GB({(_required_space_to_patch_root_fs):.2f} MB), Available Space : {(_patch_base_space_available / 1024):.2f} GB({(_patch_base_space_available):.2f} MB) for performing patch.")

            except ValueError as e:
                _suggestion_msg = f"Could not parse {ROOT_PARTITION} for free space on {str(_remote_node)}. Patching will fail with space issues."
                self.mAddError(INSUFFICIENT_SPACE_ON_ROOT_PARTITION, _suggestion_msg)
                aStatus.append({'node': _remote_node, 'status': 'failed'})
                self.mPatchLogTrace(traceback.format_exc())

            finally:
                if _node.mIsConnected():
                    _node.mDisconnect()

        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsSpaceValidationEnabledForTarget'):
            if self.mGetCurrentTargetType() == PATCH_DOM0:
                _node_list = self.mGetCustomizedDom0List()
                _required_space_to_patch_root_fs = self.mMinRequiredDom0RootFsFreeSpaceinMB()
            elif self.mGetCurrentTargetType() == PATCH_DOMU:
                _node_list = self.mGetCustomizedDomUList()
                _required_space_to_patch_root_fs = self.mMinRequiredDomURootFsFreeSpaceinMB()
            elif self.mGetCurrentTargetType() == PATCH_CELL:
                _node_list = self.mGetCustomizedCellList()
                _required_space_to_patch_root_fs = self.mMinRequiredCellRootFsFreeSpaceinMB()
            self.mPatchLogInfo(
                f"Root partition space validations in infrapatching.conf during {str(self.mGetCurrentTargetType())} patching are enabled and are currently performed.")

        else:
            self.mPatchLogInfo(
                f"Root partition space validations in infrapatching.conf during {str(self.mGetCurrentTargetType())} patching are disabled on this environment and will be skipped.")
            return _ret

        if self.mIsMockEnv():
            # in mock setup, skip rack specific operations
            return _ret
        """
         Parallelize performing root partition space 
         check validation execution on all target nodes.
        """
        _plist = ProcessManager()
        _rc_status = _plist.mGetManager().list()

        for _remote_node in _node_list:
            _p = ProcessStructure(_perform_root_space_check, [_remote_node, _rc_status], _remote_node)

            '''
             Timeout parameter configurable in Infrapatching.conf
             Currently it is set to 60 minutes
            '''
            _p.mSetMaxExecutionTime(self.mGetValidateRootPartitionFreeSpaceCheckTimeoutInSeconds())
            _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
            _p.mSetLogTimeoutFx(self.mPatchLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()

        if _plist.mGetStatus() == "killed":
            _suggestion_msg = f'Timeout while validating Root partition free space usage on the list of Nodes : {str(_node_list)}.'
            self.mAddError(INSUFFICIENT_SPACE_ON_ROOT_PARTITION, _suggestion_msg)
            raise Exception(_suggestion_msg)

        # validate the return codes
        for _rc_details in _rc_status:
            if _rc_details['status'] == "failed":
                self.mPatchLogError(
                    f"Root partition usage failed on {str(_rc_details['node'])}. Cleanup root partition before retrying patch.")
                _space_check_failed_on_nodes_list.append(_rc_details['node'])

        if len(_space_check_failed_on_nodes_list) > 0:
            _ret = INSUFFICIENT_SPACE_ON_ROOT_PARTITION

        return _ret

    def mIsSELinuxEnforcing (self, aNodeList):
        """
         This method checks if one of the nodes on the list
         has SELinux with enforcing mode. 

         Output of /usr/sbin/getenforce
         Disabled
         Permissive
         Enforcing

         return True if one of the nodes on the list has enforcing mode set
         return False if none of the nodes on the list has enforcing mode set
        """
        # once ExaCC needs support for SELinux enforcing, we can remove these
        # lines 
        if self.mIsExaCC():
            return False

        _enforcing = False
        _run_mode_cmd = ('/usr/sbin/getenforce') 
        _node = exaBoxNode(get_gcontext())
        for _node_name in aNodeList:
            try:
                _node.mConnect(aHost=_node_name)
                _i, _o, _e = _node.mExecuteCmd(_run_mode_cmd)
                _exit_check = int(_node.mGetCmdExitStatus())
                if int(_exit_check) == 0 and _o:
                    _out = (_o.readlines()[-1]).strip()
                    if "enforcing" in _out.lower():
                        _enforcing = True
                        self.mPatchLogInfo("SELinux mode is set to enforcing")
                        break;
            except Exception as e:
                self.mPatchLogWarn(f'Failed to obtain SELinux mode from {_node_name}')
                self.mPatchLogTrace(traceback.format_exc())
            finally:
                if _node.mIsConnected():
                    _node.mDisconnect()
        return _enforcing

    def mIsInActiveVersionGreaterThanTargetVersion(self, aNode, aTargetType, aIsExasplicePatching=False):
        """
        This method is to find whether inactive version is greater than or equal to targetversion passed in the payload
        """
        _result = False
        if aTargetType in [PATCH_DOM0, PATCH_DOMU, PATCH_CELL]:
            # Fetch Inactive version from backup partition
            _inactive_version = self.mGetCluPatchCheck().mCheckTargetVersion(aNode, aTargetType,
                                                                             aInactiveImage=True,
                                                                             aIsexasplice=aIsExasplicePatching)
            if _inactive_version:
                _inactive_compare = self.mGetCluPatchCheck().mCheckTargetVersion(aNode, aTargetType, _inactive_version,
                                                                                 aIsexasplice=aIsExasplicePatching)
                # Compare rollback version and target version
                if _inactive_compare is None or _inactive_compare <= 0:
                    self.mPatchLogInfo(
                        f'Rollback image version is higher than active version in {aNode}. Node will be discarded')
                    _result = True

        return _result

    def mWriteCRSMessagesToCellTraceLogs(self, aDom0):
        """
         Since CRS stop services suddenly stopped writing diskmon
         stop messages in the cell trace alert log , this API writes the
         CRS stop messages forcefully in the cell alert logs before dom0
         patching , so that CRS validation works properly for dom0 from infrapatching
         perspective. CRS stop messages are written for the current domUs running on
         the dom0 to be patched.
        """
        _rc = PATCH_SUCCESS_EXIT_CODE
        _node = None
        _domu_list_for_a_specific_dom0_to_write_crs = []
        self.mPatchLogInfo("\n\n **** Writing CRS messages into alert log on each cell. ****\n")
        try:
            for _dom0, _domUs in self.mReturnPatchingDom0DomUListFromEcra():
                if _dom0 == aDom0:
                    _domu_list_for_a_specific_dom0_to_write_crs = _domUs.copy()
                    break

            if len(_domu_list_for_a_specific_dom0_to_write_crs) == 0:
                self.mPatchLogInfo('DomU list is empty and no stopped diskmon message will be written into the alert log.')
                return _rc

            _heartbeat_str_to_be_appended = ""
            for _domu in _domu_list_for_a_specific_dom0_to_write_crs:
                # Heartbeat validations are performed using customer hostname.
                _domU_name = (self.mGetDomUCustomerNameforDomuNatHostName(_domu)).strip()
                # bug 26678535: heart beat message in the cell 'alert.log' only
                # contains the DOMU hostnames without the FQDN. So strip off
                # the FQDN from the DOMU hostname before doing anything.
                _domu_hostname_no_fqdn = _domU_name.split('.')[0]

                # host names are cut to 32 chars on the cell alert logs
                _32_char_domU_name = _domu_hostname_no_fqdn[:32]
                _cell_alert_log_mark_tz = "%+4.4d" % (time.timezone / -(60 * 60) * 100)
                _current_time_in_iso_format = datetime.datetime.now().isoformat()
                _heartbeat_str_to_be_appended += _current_time_in_iso_format+_cell_alert_log_mark_tz+" Heartbeat with diskmon (pid 000000) stopped on " + _32_char_domU_name +"\n"

            """
            _heartbeat_str_to_be_appended contains the below format of the string
                2023-04-11T09:48:22.807401+0000 Heartbeat with diskmon (pid 000000) stopped on abcipat-77xcq1
                2023-04-11T09:48:22.807420+0000 Heartbeat with diskmon (pid 000000) stopped on abcipat-77xcq2
                2023-04-11T09:48:22.807431+0000 Heartbeat with diskmon (pid 000000) stopped on abcipat-77xcq3
                2023-04-11T09:48:22.807437+0000 Heartbeat with diskmon (pid 000000) stopped on bbcnew-l9hkd1
                2023-04-11T09:48:22.807442+0000 Heartbeat with diskmon (pid 000000) stopped on bbcnew-l9hkd2
                2023-04-11T09:48:22.807449+0000 Heartbeat with diskmon (pid 000000) stopped on bbcnew-l9hkd3
                2023-04-11T09:48:22.807458+0000 Heartbeat with diskmon (pid 000000) stopped on eagles-2fdyd1
                2023-04-11T09:48:22.807468+0000 Heartbeat with diskmon (pid 000000) stopped on eagles-2fdyd2
            """

            if _heartbeat_str_to_be_appended:
                self.mPatchLogInfo(
                    f"Message : {_heartbeat_str_to_be_appended} will be written to alert.log on the cells ")
                for _cell in self.mGetCellList():
                    _node = exaBoxNode(get_gcontext())
                    _node.mConnect(aHost=_cell)
                    '''
                     writing a marker to understand that these
                     messages are written by infrapatching tool and 
                     not from CRS (since the stop messages are same 
                     in both cases)
                    '''
                    _node.mExecuteCmd(
                        f"echo -e \"{'Exadata cloud service diskmon stop message.'}\" >> {CELL_ALERT_LOG}")
                    _node.mExecuteCmd(f"echo -e \"{_heartbeat_str_to_be_appended}\" >> {CELL_ALERT_LOG}")
                    _exit_status = _node.mGetCmdExitStatus()
                    if int(_exit_status) != 0:
                        _suggestion_msg = f"Unable to write crs message into cell alert log : {CELL_ALERT_LOG} on Cell : {_cell}."
                        _rc = CELL_MARKER_MISSING_ERROR
                        self.mAddError(_rc, _suggestion_msg)
                        break
                    if _node.mIsConnected():
                        _node.mDisconnect()

        except Exception as e:
            _suggestion_msg = f'Exception encountered when crs message was written into cell alert log. Error : {str(e)}'
            _rc = CELL_MARKER_MISSING_ERROR
            self.mAddError(_rc, _suggestion_msg)
            self.mPatchLogTrace(traceback.format_exc())

        finally:
            if _node and _node.mIsConnected():
                _node.mDisconnect()
        self.mPatchLogInfo("\n **** Writing CRS messages into alert log on each cell completed. ****\n")
        return _rc

    '''
    This function checks for any existing patchmgr sessions and updates status post switchover (workflows retry command)
    '''
    def mHandleExistingPatchMgrSessionsOnRetry(self):

        _ret = PATCH_SUCCESS_EXIT_CODE
        _p_ses_exist = PATCH_SUCCESS_EXIT_CODE
        _patch_mgr_log_dir = None
        _node_fqdn = None
        _launch_node = None
        _launch_node_list = []
        _node_progressing_status = {}

        if not self.mPatchRequestRetried():
            return _ret

        self.mPatchLogInfo("Checking for Existence of PatchMgr Session during SwitchOver/Retry and waiting for patchmgr session to complete")

    # "Idempotency": {
    #     "errorCode": "0x03020001",
    #     "errorMessage": "Patchmgr precheck command failed with errors.",
    #     "patchmgrLogDir": "/EXAVMIMAGES/dbserver.patch.zip_exadata_ovs_22.1.8.0.0.230211_Linux-x86-64.zip/dbserver_patch_221130/patchmgr_log_5c4b860e-2632-4188-9ab3-75eedfdc9cde_slcs27adm02",
    #     "launchNode": "slcs27adm02",
    #     "node_progressing_status": {
    #       "sleep_infra_patch": "no",
    #       "infra_patch_start_time": "2023-05-17 16:21:25+0000",
    #       "node_patching_progress_data": [
    #         {
    #           "node_name": "slcs27adm01.us.oracle.com",
    #           "target_type": "dom0",
    #           "patchmgr_start_time": "2023-05-17 16:08:24+0000",
    #           "last_updated_time": "2023-05-17 16:11:28+0000",
    #           "status": "Completed",
    #           "status_details": "Failed",
    #           "image_version": "21.1.0.0.0.210319",
    #           "image_status": "success",
    #           "image_activation_date": "2021-07-26 10:18:36 +0000"
    #         },
    #         {
    #           "node_name": "slcs27adm02.us.oracle.com",
    #           "target_type": "dom0",
    #           "patchmgr_start_time": "2023-05-17 16:08:58+0000",
    #           "last_updated_time": "2023-05-17 16:13:36+0000",
    #           "status": "Completed",
    #           "status_details": "Failed",
    #           "image_version": "21.1.0.0.0.210319",
    #           "image_status": "success",
    #           "image_activation_date": "2021-04-13 15:10:12 +0000"
    #         }
    #       ]
    #         },
    #         "nodeFQDN": "us.oracle.com"
    #     }

        _idempotency_data = self.mGetIdemPotencydata()
        if _idempotency_data is None:
            self.mPatchLogInfo("No IdemPotency Data Detected")
            return _ret

        if _idempotency_data and 'node_progressing_status' in _idempotency_data.keys():
            _node_progressing_status = _idempotency_data["node_progressing_status"]

        if _idempotency_data and 'patchmgrLogDir' in _idempotency_data.keys():
            _patch_mgr_log_dir = _idempotency_data['patchmgrLogDir']
        if _idempotency_data and 'launchNode' in _idempotency_data.keys():
            _launch_node = _idempotency_data['launchNode']
        if _idempotency_data and 'nodeFQDN' in _idempotency_data.keys():
            _node_fqdn = _idempotency_data['nodeFQDN']

        #Modify patchmgr dir to remove any hostname at the end , if present
        #"patchmgrLogDir": "/EXAVMIMAGES/dbserver.patch.zip_exadata_ovs_22.1.8.0.0.230211_Linux-x86-64.zip/dbserver_patch_221130/patchmgr_log_5c4b860e-2632-4188-9ab3-75eedfdc9cde_slcs27adm02",
        #Should be /EXAVMIMAGES/dbserver.patch.zip_exadata_ovs_22.1.8.0.0.230211_Linux-x86-64.zip/dbserver_patch_221130/patchmgr_log_<ecra_request_id>

        if _patch_mgr_log_dir and _launch_node:
            _temp_dir = _patch_mgr_log_dir.split("patchmgr_log_")[0]
            _patch_mgr_log_dir = _temp_dir + "patchmgr_log_"+ self.mGetMasterReqId()

            if "." not in _launch_node:
                _launch_node = _launch_node + "." + _node_fqdn
            self.mPatchLogInfo(f"PatchMgr Log Dir from Idempotecy Data is {_patch_mgr_log_dir} and launch Node is {_launch_node}")
            #Check for patchmgrSession Existence in the Launch Node
            _p_ses_exist, _p_active_node = self.mCheckPatchmgrSessionExistence(_patch_mgr_log_dir,aLaunchNode=_launch_node,aNodeList=None)

            # Wait for patchmgr to complete
            if _p_ses_exist == PATCHMGR_SESSION_ALREADY_EXIST:
                self.mPatchLogInfo(f"PatchMgr session found on launch node {_launch_node} in patch retry")
                _ret = self.mReadPatchmgrConsoleOut(_p_active_node, _patch_mgr_log_dir)
                if _ret == PATCH_SUCCESS_EXIT_CODE:
                    self.mPatchLogInfo("PatchMgr session found and completed successfully in patch retry")
                    return _ret
                else:
                    self.mPatchLogInfo("PatchMgr session Failed in patch retry on launch node ")
                    _ret = PATCHMGR_RETRY_EXECUTION_FAILED_ERROR
                    _suggestion_msg = f"Patch manager failed during patch retry. Exit code = {_ret}"
                    self.mPopulatePatchListPostPatchMgrCompletion(_patch_mgr_log_dir, aLaunchNode=_launch_node, aNodeProgressStatus=_node_progressing_status, aErrCode= _ret, aSuggestionMsg = _suggestion_msg)
                    return _ret

        ##If patchmgr is not found based on the above logic , do further hardening checks to find any existing patchmgr session
        # Determine both launch Node and patchmgr Log directory and proceed
        if _p_ses_exist != PATCHMGR_SESSION_ALREADY_EXIST:
            self.mPatchLogInfo("PatchMgr session not found on Launch Node from Idempotency Payload Data during retry. Looping through probable launch Node candidates to check for patchmgr session")
            if PATCH_DOMU in self.mGetTargetTypes():
                _launch_node_list = self.mGetCustomizedDomUList()
            elif PATCH_DOM0 in self.mGetTargetTypes():
                _launch_node_list = self.mGetCustomizedDom0List()
            elif PATCH_CELL in self.mGetTargetTypes():
                _launch_node_list = self.mGetCustomizedDom0List()
            elif PATCH_IBSWITCH in self.mGetTargetTypes():
                _launch_node_list = self.mGetCustomizedDom0List()
            elif PATCH_ROCESWITCH in self.mGetTargetTypes():
                _launch_node_list = self.mGetCustomizedDom0List()

            self.mPatchLogInfo(f"Launch Node List to check for patchmgr session existence {str(_launch_node_list)}")
            _actual_launch_node = None
            for _ln in _launch_node_list:
                _node = exaBoxNode(get_gcontext())
                #Do not fail in mConnect for the  the node which is rebooting
                if not _node.mIsConnectable(_ln, aTimeout=mGetSshTimeout()):
                    self.mPatchLogInfo(f"Node {_ln} is not connectable to check for patchmgr session during patch retry. Moving to next node")
                    continue

                 #Check for PatchMgr Session existence
                _patch_mgr_log_dir = self.getExistingPatchMgrSessionLogPath(_ln)
                if _patch_mgr_log_dir and len(_patch_mgr_log_dir) > 0:
                    _actual_launch_node = _ln
                    self.mPatchLogInfo(f"Patch Manager Log directory {_patch_mgr_log_dir} is detected on Launch Node {_actual_launch_node}")
                    break

            # Wait for patchmgr to complete
            if _patch_mgr_log_dir and _actual_launch_node:
                self.mPatchLogInfo(f"Waiting for PatchMgr session to be completed on launch node {_actual_launch_node}")
                _ret = self.mReadPatchmgrConsoleOut(_actual_launch_node, _patch_mgr_log_dir)
                if _ret == PATCH_SUCCESS_EXIT_CODE:
                    self.mPatchLogInfo(f"PatchMgr session found and completed successfully in patch retry on launch node {_actual_launch_node}")
                    return _ret
                else:
                    self.mPatchLogInfo(f"PatchMgr session Failed in patch retry on launch node {_actual_launch_node}")
                    _ret = PATCHMGR_RETRY_EXECUTION_FAILED_ERROR
                    _suggestion_msg = f"Patch manager failed during patch retry. Exit code = {_ret}"
                    self.mPopulatePatchListPostPatchMgrCompletion(_patch_mgr_log_dir, aLaunchNode = _actual_launch_node, aNodeProgressStatus=_node_progressing_status, aErrCode= _ret, aSuggestionMsg = _suggestion_msg)
                    return _ret
            else:
                self.mPatchLogInfo(f"No Existing PatchMgr Session Found on the Probable Launch Node Candidates {str(_launch_node_list)}")

        return _ret

    def mPopulatePatchListPostPatchMgrCompletion(self, aPatchMgrLogPath, aLaunchNode = None, aNodeProgressStatus=None, aErrCode= None, aSuggestionMsg = None):
        try:
            _master_request_uuid = None
            _child_request_uuid = None
            self.__json_status["data"] = self.mAddPatchreport()
            if aErrCode and aSuggestionMsg:
                _code, _msg, _description, _error_action = ebPatchFormatBuildErrorWithErrorAction(aErrCode, aSuggestionMsg, None)
                self.__json_status["data"]["error_code"] = _code
                self.__json_status["data"]["error_message"] = _msg
                self.__json_status["data"]["error_detail"] = _description
                if _error_action:
                    self.__json_status["data"]["error_action"] = _error_action
                else:
                    self.mPatchLogInfo(
                        f"Error action is empty for Error Code {_code} in mPopulatePatchListPostPatchMgrCompletion")
            if aNodeProgressStatus:
                self.__json_status["data"]['node_progressing_status']  = aNodeProgressStatus
            if aPatchMgrLogPath:
                self.__json_status["data"]["log_dir"] = aPatchMgrLogPath
            if aLaunchNode:
                self.__json_status["data"]["launch_node"] = aLaunchNode

            _master_request_uuid, _child_request_uuid , _ , _ = self.mGetAllPatchListDetails()
            # Save json error in db
            _reqobj = self.mGetCluControl().mGetRequestObj()
            if _reqobj:
                if _child_request_uuid:
                    self.__json_status["data"]["child_request_uuid"] = _child_request_uuid
                if _master_request_uuid:
                    self.mPatchLogInfo(f"Master request uuid for error status {_master_request_uuid}")
                    self.__json_status["data"]["master_request_uuid"] = _master_request_uuid

                self.mPatchLogInfo('Updating patch list to Exacloud DB from mPopulatePatchListPostPatchMgrCompletion.')
                _db = ebGetDefaultDB()
                _db.mUpdateJsonPatchReport(_reqobj.mGetUUID(), json.dumps(self.__json_status))

            self.mPatchLogInfo("Patch status JSON report from mPopulatePatchListPostPatchMgrCompletion.\n")
            self.mPatchLogInfo(json.dumps(self.__json_status, indent=4))
        except Exception as e:
            self.mPatchLogError(f'Exception in creating patch list while PatchMgr Drain  {str(e)} ')
            self.mPatchLogTrace(traceback.format_exc())

    def mUpdateServiceStateOnIlom(self, aNodeList, aPhase):
        """
         This method takes care of enabling the
         servicestate prior to patching and disabling
         the same post patching. It is applicable to
         dom0 and cells and is currently applicable
         to EXACC environments. Irrespective of the
         impact of patch results, values are reset at
         the end of patching.

         ipmitool servicestate commands sample snippets :

         [root@slcs27adm03 ~]# ipmitool sunoem getval /SP/services/ipmi/servicestate
         Target Value: disabled
         [root@slcs27adm03 ~]#

         [root@slcs27adm03 ~]# ipmitool sunoem setval /SP/services/ipmi/servicestate enabled
         Sun OEM setval command successful.
         [root@slcs27adm03 ~]#

         [root@slcs27adm03 ~]# ipmitool sunoem setval /SP/services/ipmi/servicestate disabled
         Sun OEM setval command successful.
         [root@slcs27adm03 ~]#
        """
        if not self.mGetInfrapatchExecutionValidator().mCheckCondition('enableServiceStateOnIlomsPriorToDom0CellPatchingEnabled'):
            return

        _node = exaBoxNode(get_gcontext())
        _cmd_ipmi_geteval = "ipmitool sunoem getval /SP/services/ipmi/servicestate"
        for _node_name in aNodeList:
            try:
                _node.mConnect(aHost=_node_name, aTimeout=20)
                if aPhase == "prepatch":
                    _in, _out, _err = _node.mExecuteCmd(_cmd_ipmi_geteval)
                    _o = _out.readlines()
                    if _o:
                        self.mPatchLogInfo(
                            f"Service State of ilom on node : {_node_name} prior to patching, output : {str(_o)}.")
                    if _o[0].find("disabled") != -1:
                        _cmd = "ipmitool sunoem setval /SP/services/ipmi/servicestate enabled"
                        _in, _out, _err = _node.mExecuteCmd(_cmd)
                        if _node.mGetCmdExitStatus() == 0:
                            _in, _out, _err = _node.mExecuteCmd(_cmd_ipmi_geteval)
                            _output = _out.readlines()
                            self.mPatchLogInfo(
                                f"Service State of ilom on node : {_node_name} is enabled. Output : {str(_output)}")
                        else:
                            self.mPatchLogWarn(
                                f"Error in enabling service state value of iloms on node : {_node_name} during patching.")

                elif aPhase == "postpatch":
                    _in, _out, _err = _node.mExecuteCmd(_cmd_ipmi_geteval)
                    _o = _out.readlines()
                    if _o[0].find("enabled") != -1:
                        _cmd = "ipmitool sunoem setval /SP/services/ipmi/servicestate disabled"
                        _in, _out, _err = _node.mExecuteCmd(_cmd)
                        if _node.mGetCmdExitStatus() == 0:
                            _in, _out, _err = _node.mExecuteCmd(_cmd_ipmi_geteval)
                            _output = _out.readlines()
                            self.mPatchLogInfo(
                                f"Service State of ilom on node : {_node_name} is disabled. Output : {str(_output)}")
                        else:
                            self.mPatchLogWarn(
                                f"Error in disabling service state value of iloms on node : {_node_name} during patching.")

            except Exception as e:
                self.mPatchLogWarn(
                    f'Exception in setting servicestate value on ilom of node : {_node_name} Error : {str(e)}')
                self.mPatchLogTrace(traceback.format_exc())
            finally:
                if _node.mIsConnected():
                    _node.mDisconnect()

    def mVerifyAndCleanupMissingPatchmgrPatchBaseForLocalNode(self, aRemotePatchBase):

        if os.path.exists(aRemotePatchBase):
            _parent_dir = aRemotePatchBase
            _cmd_list_find_dir = []
            _cmd_list_find_dir.append(['find', _parent_dir, '-mindepth', '1', '-maxdepth', '1', '-type', 'd'])
            _rc, _out = runInfraPatchCommandsLocally(_cmd_list_find_dir)
            _output_list = _out.split("\n")
            if int(_rc) == 0:
                # In some cases, the patch base directory may not have any
                # subdirectories yet contains a file like dbserver.patch.zip
                # In these scenarios, dbserver.patch.zip will not be
                # transferred and unzipped to the patch base directory.
                # Therefore, we're completely removing the patch base
                # directory to ensure all content is transferred and updated.
                if len(_output_list) == 0: 
                    self.mPatchLogWarn(f"The patch base directory doesn't contain any subdirectories, resulting in the deletion of the patch base directory {_parent_dir}")
                    _cmd_list_rm_dir = []
                    _cmd_list_rm_dir.append(['rm', '-rf', _parent_dir])
                    runInfraPatchCommandsLocally(_cmd_list_rm_dir)

                for _output in _output_list:
                    _dir_path = _output.strip() 
                    _patchmgr_path = _dir_path + "/patchmgr"
                    if not os.path.exists(_patchmgr_path):
                        self.mPatchLogWarn(f'The patchmgr file cannot be found in {_dir_path}, leading to the removal of the patch base directory {_parent_dir}')
                        _cmd_list_rm_dir = []
                        _cmd_list_rm_dir.append(['rm', '-rf', _parent_dir])
                        runInfraPatchCommandsLocally(_cmd_list_rm_dir)
                        break

    def mSetLaunchNodeAsPatchBaseForLocalNode(self,
                                              aLaunchNodeCandidates,
                                              aLocalPatchZipFile,
                                              aPatchZipName, aPatchZipSizeMb,
                                              aRemotePatchBase, aRemotePatchZipFile,
                                              aRemotePatchmgr, aRemoteNecessarySpaceMb, aPatchBaseDir,
                                              aSuccessMsg="", aMoreFilesToCopy=None):
        """
        Makes sure the patchmgr is installed alog with any other files for
        its correct use. Generic method to install patchmgr on a given node to
        patch cells/ibswitches, dom0s or domus
        """
        # Update db status
        self.mUpdatePatchStatus(True, STEP_SELECT_LAUNCH_NODE)

        # If there are directories in the patch base that do not
        # contain the patchmgr file, the patch base dir must be removed.
        self.mVerifyAndCleanupMissingPatchmgrPatchBaseForLocalNode(aRemotePatchBase)

        # In case of Postcheck and oneoff operations, we need not
        # to copy any of the patchmgr related files or images.
        if self.mGetTask() in [ TASK_ONEOFF, TASK_POSTCHECK, TASK_ONEOFFV2 ]:
            self.mPatchLogInfo(f"Ignoring file copy of exadata patches for task : {self.mGetTask()} is performed.")
            _launch_node = aLaunchNodeCandidates[0].strip()
            return _launch_node

        _local_patch_path = os.path.dirname(aLocalPatchZipFile)
        _ret, _errmsg = self.mValidateImageCheckSumWithRetry(aPatchZipName, _local_patch_path, aRemotePatchBase,
                                                             aLaunchNodeCandidates, aRemoteNecessarySpaceMb)
        if _ret != PATCH_SUCCESS_EXIT_CODE:
            raise Exception(_errmsg)

        if aMoreFilesToCopy:
            for _file, _copy_to in aMoreFilesToCopy:
                _file_name = _file.split("/")[-1]
                _local_patch_path = os.path.dirname(_file)
                _ret, _errmsg = self.mValidateImageCheckSumWithRetry(_file_name, _local_patch_path, _copy_to,
                                                                         aLaunchNodeCandidates, aRemoteNecessarySpaceMb)
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                   raise Exception(_errmsg)

        for _launch_node in aLaunchNodeCandidates:

            # make sure we can get the patch to the directory that came out of unziping the patch
            if not os.path.exists(aRemotePatchmgr):
                _suggestion_msg = f"Expected patchmgr script {_launch_node}:{aRemotePatchmgr} but it was not found.Patch zip structure may have changed"
                _ret = PATCHMGR_SCRIPT_MISSING_ON_LAUNCH_NODE
                self.mAddError(_ret, _suggestion_msg)
                # TODO give it another shot on a different  dom0 (continue), or just error out (return None)
                continue

            self.mPatchLogInfo(
                f"Selecting {str(_launch_node)} as a patch base for {aSuccessMsg}. patchmgr is at {aRemotePatchmgr}")

            return _launch_node
        else:
            self.mPatchLogError(f"None of {str(aLaunchNodeCandidates)} were eligible bases for the patch manager")
            return None

    def mValidateImageCheckSumForLocalNode(self, aPatchFile, aPatchRepo, aRemotePatchBase, aNodeList, aRemoteNecessarySpaceMb):
        """
           Return:-
          PATCH_SUCCESS_EXIT_CODE                 --> if files copy are successful.
          Non PATCH_SUCCESS_EXIT_CODE error codes --> If there any failures
        """

        """
        No need to validate ssh connectivity as it is  the local node
        self.mPatchLogInfo(
            "Passwdless ssh connectivity is validated between Exacloud/CPS nodes to target launch nodes.")
        self.mGetCluPatchCheck().mVerifyExacloudExadataHostSshConnectivity(aNodeList)
        
        """
        def _mCopyFile(_remote_node):
            '''
             Common method to perform mCopyFile based on the conditions
             in _mExecute_FileCopy method.
            '''
            _ret = PATCH_SUCCESS_EXIT_CODE

            try:
                _cmd_list = []
                _cmd_list.append(['cp', _local_patch_file, _remote_patch_file])
                _exit_code, _o = runInfraPatchCommandsLocally(_cmd_list)

                _cmd_list = []
                _cmd_list.append(_patch_unzip_cmd.split())
                _exit_code, _o = runInfraPatchCommandsLocally(_cmd_list)

                if int(_exit_code) != 0:
                    _cmd_list = []
                    _cmd_list.append(['rm', '-f', _remote_patch_file])
                    runInfraPatchCommandsLocally(_cmd_list)
                    _patch_copy_end_time = datetime.datetime.now()
                    self.mGetPatchRunningTime("Patch_copy", _patch_copy_start_time, _patch_copy_end_time)
                    _suggestion_msg = f"Error while unziping the patch : {_remote_patch_file} on {str(_remote_node)}, skipping this Node."
                    _ret = PATCH_UNZIP_ERROR
                    self.mAddError(_ret, _suggestion_msg)
                else:
                    self.mPatchLogInfo(
                        f'*** Patch file :{_local_patch_file} >>>> {_remote_patch_file} transferred to Node : {_remote_node}')

            except Exception as e:
                _suggestion_msg = f"Copy operation failed with errors on Node : {_remote_node} Error : {str(e)}."
                _ret = PATCH_COPY_ERROR
                self.mAddError(_ret, _suggestion_msg)
                self.mPatchLogTrace(traceback.format_exc())
            finally:
                return _ret


            # End of _mCopyFile sub function.

        def _mExecute_FileCopy(_remote_node):
            '''
             Sub function to copy patches parallely
             to multiple target nodes.
            '''
            _ret = PATCH_SUCCESS_EXIT_CODE

            try:
                _sufficient_space_available = False

                # Create Patch and Images directory if missing.
                #_exec_code = "mkdir -p %s" % aRemotePatchBase
                _cmd_list = []
                _cmd_list.append(["mkdir", "-p", aRemotePatchBase])
                runInfraPatchCommandsLocally(_cmd_list)                
                _cmd_list = []
                _cmd_list.append(["df", "-mP", aRemotePatchBase])             
                _cmd_list.append(["tail", "-n1"])   
                _cmd_list.append(["awk", '{print $(NF - 2); }'])  
                _rc, _o = runInfraPatchCommandsLocally(_cmd_list)                
                _patch_base_space_available = int(_o)


                # If the space to copy patch is not available on the target node
                # this node will be skipped.
                if _patch_base_space_available < (aRemoteNecessarySpaceMb * 3):
                    _suggestion_msg = f"{_remote_node} does not have enough space in {aRemotePatchBase} to be used as the patching base. Needed {((aRemoteNecessarySpaceMb * 3) / 1024):.2f}GB, got {(_patch_base_space_available / 1024):.2f}GB."
                    _ret = INSUFFICIENT_SPACE_ON_PATCH_BASE
                    self.mAddError(_ret, _suggestion_msg)
                else:
                    _sufficient_space_available = True
                    self.mPatchLogInfo(
                        f"Sufficient space available to stage patches on Node : {_remote_node}, Location : {aRemotePatchBase}, Required : {(aRemoteNecessarySpaceMb / 1024):.2f}GB, Available Space : {(_patch_base_space_available / 1024):.2f}GB")

            except ValueError as e:
                _suggestion_msg = f"Could not parse {aRemotePatchBase} for free space on {str(_remote_node)}. Expected a number, got {str(e)}. Trying a different node"
                _ret = PATCH_COPY_ERROR

            except Exception as e:
                # disambiguate dir creation or df execution
                _suggestion_msg = f"Prior to copy  patches on Node : {str(_remote_node)} failed with {str(e)}"
                _ret = PATCH_COPY_ERROR
                self.mAddError(_ret, _suggestion_msg)
                self.mPatchLogTrace(traceback.format_exc())

            if _ret != PATCH_SUCCESS_EXIT_CODE:
                return  _ret

            if _sufficient_space_available:
                # Delete the patch zip file if found on the node.
                if os.path.exists(_remote_patch_file):
                    self.mPatchLogInfo(
                        f"Patch zip file found in {_remote_node} at {_remote_patch_file}. It will be removed.")
                    _cmd_list = []
                    _cmd_list.append(['rm', '-f', _remote_patch_file])
                    runInfraPatchCommandsLocally(_cmd_list)
                self.mPatchLogInfo(
                    f'*** Copying Patch :{aPatchFile} to Node : {_remote_node} in progress...')
                _ret = _mCopyFile(_remote_node)
            return _ret


        # End of _mExecute_FileCopy sub function.

        _patch_copy_start_time = datetime.datetime.now()

        _ret = PATCH_SUCCESS_EXIT_CODE

        _local_patch_file = os.path.join(aPatchRepo, aPatchFile)
        _remote_patch_file = os.path.join(aRemotePatchBase, aPatchFile)

        # Patch unzip command is prepared based on patch file extension.
        if _remote_patch_file.endswith('.zip'):
            #_patch_unzip_cmd = "unzip -o %s -d %s;" % ( _remote_patch_file,aRemotePatchBase)
            _patch_unzip_cmd = f"unzip -d {aRemotePatchBase} -o {_remote_patch_file}"


        _ret = PATCH_SUCCESS_EXIT_CODE
        _ret = _mExecute_FileCopy("localhost")

        return _ret, None

    def mUpdateCurrentLaunchNodeDetailsInCorrespondingLocalNodeTaskHandlerInstance(self, aPatchmgrLogPathLaunchNode=None):
        """
          This method is used to update instance variables(self.__cur_launch_node_list and self.__patchmgr_log_path_on_launch_node)
          of taskhandler instance by reading from targethandler instance
        """
        try:
            _cur_launch_node_list = self.mGetExternalLaunchNode()
            _patch_mgr_log_patch_on_launch_node = None
            if aPatchmgrLogPathLaunchNode:
                _patch_mgr_log_patch_on_launch_node = aPatchmgrLogPathLaunchNode
            else:
                _patch_mgr_log_patch_on_launch_node = self.mGetPatchmgrLogPathOnLaunchNode()

            self.mSetCurrentLaunchNodeList(_cur_launch_node_list)

            _context_task_handler = mGetInfraPatchingHandler(INFRA_PATCHING_HANDLERS, self.mGetTask())

            if _context_task_handler:
                _context_task_handler.mSetCurrentLaunchNodeList(_cur_launch_node_list)
                _context_task_handler.mSetPatchmgrLogPathOnLaunchNode(_patch_mgr_log_patch_on_launch_node)
                self.mPatchLogInfo(
                    f"Updated launchnode details in taskhandler instance as {str(_cur_launch_node_list)} and patch_mgr log path as {_patch_mgr_log_patch_on_launch_node}")
            else:
                self.mPatchLogError(
                    "mUpdateCurrentLaunchNodeDetailsInCorrespondingTaskHandlerInstance - Could not get taskhandler instance to update")
        except Exception as e:
            self.mPatchLogWarn(
                f"Exception {str(e)} occurred in mUpdateCurrentLaunchNodeDetailsInCorrespondingTaskHandlerInstance")
            self.mPatchLogTrace(traceback.format_exc())

    def mGetLocalNodePatchMgrMiscLogFiles(self, aRemotePath, aTaskType=None, aNodesList=[]):
        """
        Copies PatchmgrConsole.out to /log
        """

        _misc_files = [PATCH_CONSOLE_LOG]

        _context = get_gcontext()
        _oeda_path_logs = os.path.join(_context.mGetOEDAPath(), "log")

        '''
         If the applied patch is exaplice, collect exaplice
         specific diagnostic information.

         2021-01-19 13:31:08+0000 - Dom0Handler - INFO - - <dbnode_name>_exasplice_driver.log
         2021-01-19 13:31:08+0000 - Dom0Handler - INFO - - <dbnode_name>_exasplice_driver.trc
         2021-01-19 13:31:08+0000 - Dom0Handler - INFO - - <dbnode_name>_dbnodeupdate.log
         2021-01-19 13:31:08+0000 - Dom0Handler - INFO - - patchmgr.log
        '''
        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsExaspliceNot24') and \
                aTaskType in [ TASK_PATCH, TASK_PREREQ_CHECK ]: 

            for aNode in aNodesList:

                EXASPLICE_DRIVE_LOG = f"{aNode}_exasplice_driver.log"
                EXASPLICE_DRIVE_TRC = f"{aNode}_exasplice_driver.trc"

                for _exasplice_logs in [EXASPLICE_DRIVE_LOG, EXASPLICE_DRIVE_TRC]:
                    try:
                        self.mPatchLogInfo(
                            f"Copying Exasplice log : {_exasplice_logs} from node - {str(self.mGetExternalLaunchNode())} , location - {aRemotePath} to exacloud location - {self.mGetLogPath()}")
                        _cmd_list = []
                        _cmd_list.append(['cp', '-rf', os.path.join(aRemotePath, _exasplice_logs),
				os.path.join(self.mGetLogPath(),_exasplice_logs + '.' + self.mGetCurrentTargetType()) ])
                        runInfraPatchCommandsLocally(_cmd_list)

                        # symlinks used for chainsaw2/lumberjack
                        #  ln -s <file> <symlink>
                        # example:
                        #   ln -s /opt/oci/exacc/exacloud/oeda/requests/f829406a-15cb-11ec-8770-0010e0efc742/log/patchmgr_logs/nodename_exasplice_driver.log
                        #         /opt/oci/exacc/exacloud/oeda/log/1ef39fbd-9be8-450c-8512-1e633cdf89b5_nodename_exasplice_driver.log
                        #
                        _cmd_list = []
                        _cmd_list.append(['ln', '-s', os.path.join(self.mGetLogPath(), _exasplice_logs + '.' + self.mGetCurrentTargetType()),
					os.path.join(_oeda_path_logs, self.mGetMasterReqId() + "_" + _exasplice_logs + '.' + self.mGetCurrentTargetType())])
                        runInfraPatchCommandsLocally(_cmd_list) 
                    except Exception as e:
                        self.mPatchLogWarn(
                            f'Error while copying exasplice log  {_exasplice_logs}: {str(e)} from node - {str(self.mGetExternalLaunchNode())} , location - {aRemotePath} to exacloud location - {self.mGetLogPath()}')
                        self.mPatchLogTrace(traceback.format_exc())

        for _misc_file in _misc_files:
            try:
                self.mPatchLogInfo(
                    f"Copying {_misc_file} file from node - {str(self.mGetExternalLaunchNode())} , location - {aRemotePath} to exacloud location - {self.mGetLogPath()}")
                _source_patchmgr_log_loc = os.path.join(aRemotePath, _misc_file)
                _dest_patchmgr_log_loc = os.path.join(self.mGetLogPath(),
                                                      _misc_file + '.' + self.mGetCurrentTargetType())
                _cmd_list = []
                _cmd_list.append(['cp', '-rf', _source_patchmgr_log_loc, _dest_patchmgr_log_loc])
                runInfraPatchCommandsLocally(_cmd_list)
                # symlinks used for chainsaw2/lumberjack
                #  ln -s <file> <symlink>
                # example:
                #   ln -s /opt/oci/exacc/exacloud/oeda/requests/f829406a-15cb-11ec-8770-0010e0efc742/log/patchmgr_logs/patchmgr.log
                #         /opt/oci/exacc/exacloud/oeda/log/1ef39fbd-9be8-450c-8512-1e633cdf89b5_patchmgr.log
                #
                _cmd_list = []
                _cmd_list.append(['ln', '-s', os.path.join(self.mGetLogPath(), _misc_file + '.' + self.mGetCurrentTargetType()),
				os.path.join(_oeda_path_logs,self.mGetMasterReqId() + "_" + _misc_file + '.' + self.mGetCurrentTargetType())])
                runInfraPatchCommandsLocally(_cmd_list)

            except Exception as e:
                self.mPatchLogWarn(
                    f'Error while copying miscellaneous file console log {_misc_file}: {str(e)} from node - {str(self.mGetExternalLaunchNode())} , location - {aRemotePath} to exacloud location - {self.mGetLogPath()}')
                self.mPatchLogTrace(traceback.format_exc())


    def mGetLocalNodeCount(self, aInputListFile):

        """
         To get the count of Cells/ IBSwitches to be patched.
         The list of nodes might vary depending on the discarded
         node list and count rely on the config xml list of cells.
        """

        _count_of_nodes = 0
        _cmd_list = []
        _cmd_list.append(['wc', '-l', aInputListFile])
        _cmd_list.append(['awk', '{print $1}'])
        _rc, _o = runInfraPatchCommandsLocally(_cmd_list)
        _out = _o.split("\n")
        for _output in _out:
            _count_of_nodes = int(_output.strip())

        '''

         Incrementing the count is necessary due to the 
         below issue. in the last line both cell name and 
         prompt appear in the same line.

          bash-4.2$cat node_list
          cel01
          cel02
          cel03bash-4.2$ 

        '''
        _count_of_nodes += 1
        return _count_of_nodes


    def mGetLocalNodePatchMgrOutFiles(self, aRemotePath, aCode=''):
        """
        Copies patchmgr.stdout/stderr/trc/log to /log
        """

        patchmgr_files = [PATCH_STDOUT, PATCH_STDERR,
                          PATCH_TRC, PATCH_LOG]
        if aCode != '':
            for i, patchmgr_file in enumerate(patchmgr_files):
                patchmgr_files[i] = patchmgr_file + '.' + aCode

        _context = get_gcontext()
        _oeda_path_logs = os.path.join(_context.mGetOEDAPath(), "log")

        for patchmgr_file in patchmgr_files:
            try:
                self.mPatchLogInfo(
                    f"Copying {patchmgr_file} file from node - {self.mGetExternalLaunchNode()} , location - {aRemotePath} to exacloud location - {self.mGetLogPath()}")
                _cmd_list_cp =[]
                _cmd_list_cp.append(['cp', '-rf', os.path.join(aRemotePath, patchmgr_file), os.path.join(self.mGetLogPath(), patchmgr_file + '.' + self.mGetCurrentTargetType())])
                runInfraPatchCommandsLocally(_cmd_list_cp)

                # symlinks used for chainsaw2/lumberjack
                #  ln -s <file> <symlink>
                # example:
                #   ln -s /opt/oci/exacc/exacloud/oeda/requests/f829406a-15cb-11ec-8770-0010e0efc742/log/patchmgr_logs/patchmgr.stderr.cell
                #         /opt/oci/exacc/exacloud/oeda/log/1ef39fbd-9be8-450c-8512-1e633cdf89b5_patchmgr.stderr.cell
                #
                _cmd = f"ln -s {os.path.join(self.mGetLogPath(), patchmgr_file + '.' + self.mGetCurrentTargetType())} {os.path.join(_oeda_path_logs, self.mGetMasterReqId() + '_' + patchmgr_file + '.' + self.mGetCurrentTargetType())}"
                _cmd_list_ln =[['ln', '-s', os.path.join(self.mGetLogPath(), patchmgr_file + '.' + self.mGetCurrentTargetType()), os.path.join(_oeda_path_logs, self.mGetMasterReqId() + "_" + patchmgr_file + '.' + self.mGetCurrentTargetType())]]
                runInfraPatchCommandsLocally(_cmd_list_ln)

            except Exception as e:
                self.mPatchLogWarn(
                    f'Error while copying {patchmgr_file}: {str(e)} from node - {self.mGetExternalLaunchNode()} , location - {aRemotePath} to exacloud location - {self.mGetLogPath()}')
                self.mPatchLogTrace(traceback.format_exc())



    def mSetConnectionUser(self, _node):
        _user = 'root'
        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
            _user = 'opc'
            if _node.mIsConnected():
                self.mPatchLogError(f'Unable to change the user to {_user} because connection is already established')
            else:
                _node.mSetUser(_user)
        return _user

    # if aEnable is true, it enables blackout, otherwise, removes
    def mSetUnsetBlackout(self, aNode, aEnable):
        # Blackout only for ExaCS
        if self.mIsExaCC():
            return
        if self.mIsMockEnv():
            return

        _node = exaBoxNode(get_gcontext())
        try:
            _node.mConnect(aHost=aNode)

            # get tfa location
            _tfa_home = self.mReturnExecOutput("cat /etc/oracle.ahf.loc", _node)
            _tfa_bin = f"{_tfa_home}/bin/tfactl"

            # check if tfactl is present
            if _node.mFileExists(_tfa_bin):
                if aEnable:
                    _reason = "DomU VM OS Patching " + aNode
                    _node.mExecuteCmdLog(f"{_tfa_bin} blackout add -targettype host -timeout 2h -reason '{_reason}'")
                    _node.mExecuteCmdLog(f"{_tfa_bin} blackout print")
                else:
                    _node.mExecuteCmdLog(f"{_tfa_bin} blackout remove -targettype host")
                    _node.mExecuteCmdLog(f"{_tfa_bin} blackout print")
        except Exception as e:
            self.mPatchLogWarn(f"Exception {str(e)} caught while calling tfactl blackout")
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()

    def mPrintPatchmgrLogFormattedDetails(self):
        """
          This method prints the patchmgr log location
          and host details in a readable manner.
        """
        self.mPatchLogInfo(f"***** \n------------\n Copying below patchmgr logs from Launch Node to Exacloud/CPS Target Log Location -- {self.mGetLogPath()} \n Patchmgr Log Name -- {json.dumps(self.mGetListOfLogsCopiedToExacloudHost(), indent=4)}\n------------\n")
