#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/generichandler.py /main/197 2025/11/28 06:57:28 araghave Exp $
#
# generichandler.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      generichandler.py - This module contains methods to support all the inheriting handlers.
#
#    DESCRIPTION
#      This module contains methods to support all the inheriting handlers, patch payload from the exacloud
#      is received in this file.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    11/13/25 - Bug 38651311 - REPLACE FULLCVSS ELU OPTION WITH
#                           FULL IN DOMU ELU INFRA PATCHING CODE
#    jyotdas     10/31/25 - Bug 38575316 - Parallelise the dom0 shutdown across
#                           all nodes while non-rolling qmr patching.
#    sdevasek    10/10/25 - ENH 38437135 - IMPLEMENT ADDITION OF SCRIPTNAME
#                           SCRIPTBUNLDENAME AND SCRIPTBUNDLEHASH ATTRIBUTES
#                           TO ECRA REGISTERED PLUGINS METADATA REGISTRATION
#    avimonda    09/19/25 - Bug 38324744 - EXACC GEN 2 | PATCHING | SSHD
#                           TIMEOUT ERRORS MISINTERPRETED AS SSHD NOT RUNNING
#    araghave    09/11/25 - Bug 38404851 - PROVIDE A WARNNG MESSAGE AND RETURN
#                           SUCCESS IN CASE OF ALL NODES REGISTERED ARE WITH
#                           THE INVALID VERSION
#    araghave    09/11/25 - Enhancement Request 38173247 - EXACLOUD CHANGES TO
#                           SUPPORT DOMU ELU INFRA PATCH OPERATIONS
#    sdevasek    08/28/25 - Enh 38282910 - CLUSTER-WIDE CRS CHECK SHOULD BE
#                           PERFORMED ONLY ON VM CLUSTERS BELONG TO THE DOM0S
#                           WITHIN THE MAINTENANCE WINDOW  
#    apotluri    08/19/25 - Enhancement Request 38195215 - ECRA INFRA PATCHING
#                           FAILURE ERROR MESSAGE TO CONTAIN FAILED NODE AND
#                           CLUSTER INFORMATION
#    sdevasek    08/19/25 - Bug 38298923 - GMR: CELL NON-ROLLING PATCHING
#                           FAILING AT VMS STARTUP STAGE POST PATCHMGR RUN
#    araghave    08/13/25 - Enh 38228272 - EXACC GEN2 | PATCHING | SWITCH BACK
#                           TO OPC USER FOR ALL INFRA PATCH USE CASES IN CASE
#                           OF ROOT KEY INJECTION FAILS
#    rbhandar    08/07/25 - Bug 37625365 - AIM4ECS:0X03030024 - INVALID CRS
#                           HOME ON DOMU
#    araghave    07/28/25 - Enh 38228977 - EXACC GEN2 | INFRAPATCHING - MODIFY
#                           HIGH AVAILABILITY CHECK TO SKIP WHEN ALL VMS IN
#                           CLUSTER ARE SHUTOFF
#    sdevasek    07/24/25 - Enh 38120913 - TIMEOUT RUNNING OF CUSTOM_DOMU.SH
#                           IF IT EXCEEDS 60 MINS
#    araghave    07/16/25 - Bug 38192106 - EXACC GEN2 | INFRA PATCHING | SSHD
#                           CHECKS TO BE FIXED FOR AUTONOMOUS VMS
#    avimonda    07/12/25 - Bug 37934568 - AIM4ECS:0X0301000A - INDIVIDUAL
#                           PATCH REQUEST EXCEPTION DETECTED
#    sdevasek    06/27/25 - Bug 38121983 - INCORRECT DOMU INFORMATION DISPLAYED
#                           FOR VMC CLUSTER IN EXACLOUD THREAD LOGS FOR HA
#                           CHECK FAILURE 
#    araghave    06/24/25 - Enhancement Request 38082882 - HANDLING EXACLOUD
#                           ELU CHANGES FOR DOM0 PATCHING
#    josedelg    06/24/25 - Enh 37520273 - Select launch node from the rack
#                           when include node list is filled
#    araghave    06/05/25 - Enh 38039225 - RE-RUN PATCHMGR VERIFY CONFIG IN
#                           CASE OF A FAILURE DUE TO SWITCH MISCONFIGURATION
#                           DURING PROVISIONING
#    araghave    05/27/25 - Enh 37923422 - EXACC|GEN2|INFRAPATCHING|ENH|
#                           DETERMINE RUNTIME STATUS OF VM DURING INFRA
#                           PATCHING
#    avimonda    05/23/25 - Bug 37833454 - EXACC GEN2 - INFRA PATCHING - DOM0
#                           POST HEARTBEAT VALIDATION HUNG IF OUTPUT SIZE MORE
#                           THAN 1 MB
#    sdevasek    05/16/25 - Enh 37839098 - ECRA changes to track patching
#                           sessions on the launch node
#    diguma      05/14/25 - bug37947555: EXACC GEN2 || EXADATA LIVE UPDATE ||
#                           SMR LIVE UPDATE TESTING FAILED DUE TO INCORRECT
#                           BASE DIRECTORY SETUP
#    araghave    05/07/25 - Enh 37892080 - TO IMPLEMENT NEWER PATCHSWITCHTYPE
#                           CHANGES APPLICABLE TO ALL SWITCH TARGET TYPES AND
#                           PATCH COMBINATIONS
#    avimonda    04/24/25 - Bug 37795564 - AIM4ECS:0X030B0010 - EXCEPTION
#                           ENCOUNTERED WHILE READING PLUGIN CONSOLE LOGS ON
#                           DOMU. REFER MOS NOTE 2829056.1 FOR MORE DETAILS.
#    sdevasek    04/15/25 - Bug 37819772 - PATCHING IS FAILING WITH INCORRECT
#                           ERROR THAT DOMU ARE NOT UP EVEN THOUGH DOMU ARE UP
#                           AND RUNNING FOR ADBD VMS
#    jyotdas     04/09/25 - Enh 37500460 - free node from qfab as a launch node
#                           for clusterless patching
#    araghave    03/24/25 - Enh 37164753 - USE ROOT USER TO CONNECT TO DOMU TO
#                           PERFORM CRS CHECKS ON EXACC ENVIRONMENTS DURING
#                           DOM0 PATCHING
#    sdevasek    03/24/25 - Enh 36496178 - HA CHECK INCORRECTLY REPORTS THE VM
#                           AS RUNNING DESPITE IT BEING STUCK IN BOOTING
#                           CAUSING WRONG CALCULATION IN HA VM RUNNING CHECKS
#    araghave    03/04/25 - Enh 37541740 - UPDATE ALL MISCONNECTABLE API INFRA
#                           PATCHING REFERENCES TO TAKE AKEY AS TRUE
#    araghave    03/04/25 - Bug 37417431 - EXACS | DOMU | UNWANTED SSH
#                           CONNECTION FROM 169.254.200.1 LOCKING OPC USER
#    diguma      02/27/25 - Bug 36668666: PRINT MANUALLY SHUTDOWN VMS IN CASE
#                           OF HA CHECK FAILURE
#    jyotdas     02/25/25 - Enh 37567184 - EXACC Discard patching of cells
#                           found in pre-activation state
#    sdevasek    02/14/25 - ENH 37496197 - INFRAPATCHING TEST AUTOMATION -
#                           REVIEW AND ADD METHODS INTO METHODS_TO_EXCLUDE_
#                           COVERAGE_REPORT
#    antamil     01/31/25 - Enh 37300427 - Enable clusterless cell patching
#                           using management host
#    araghave    01/27/25 - Enh 37132175 - EXACOMPUTE MUST REUSE INFRA PATCHING
#                           MODULES FOR VALIDATION AND PATCH OPERATIONS
#    araghave    01/23/25 - Enh 37106126 - PROVIDE A MECHANISM TO PATCH SPINE
#                           SWITCHES
#    sdevasek    01/16/25 - Enh 36513535 - PASS OEDA_PATH IN STATUS OUTPUT TO
#                           BE CONSUMED BY ECRA
#    araghave    12/12/24 - Enh 37228878 - GENERATE KEYSCAN ENTRIES ON THE
#                           IBSWITCH TARGET IN CASE OF SSH VERSION MISMATCH
#    araghave    12/12/24 - Enh 37156971 - USE ENCRYPTED NON-DEFAULT PASSWORD
#                           TO SETUP KEYS DURING ADMIN SWITCH PATCHING
#    avimonda    12/10/24 - Enh 37378866 - INCLUDE THE TARGET TYPE IN THE CHILD
#                           THREAD LOG FILE NAME WITHIN THE PATCH FAILURE
#                           JSON FILE
#    diguma      12/06/24 - bug 37365122 - EXACS:24.4.2.1:X11M: ROLLING DOM0
#                           PATCHING FAILS WITH SSH CONNECTIVITY CHECK FAILED
#                           DURING PATCHING EVEN THOUGH EXASSH TO DOMUS WORK
#    avimonda    12/02/24 - Enh 37327136 - INCLUDE A WORK REQUEST ID INTO
#                           PATCH FAILURE JSON FILE
#    antamil     11/27/24 - Bug 37236994 - Changes on cleanup of passwordless ssh
#                           for single vm patching
#    sdevasek    11/15/24 - Enh 37172948 - ISOLATE CRS/HEARTBEAT/DB HEALTH
#                           CHECKS TO A SEPARATE API BASED MODULE
#    araghave    11/05/24 - Enh 37115530 - ADD NEW SWITCH TARGET REFERENCE IN
#                           INFRA PATCHING CODE
#    sdevasek    10/28/24 - ENH 37180312 - DO NOT RUN DBHEALTHCHECKS ON
#                           AUTONOMOUS VMS IF HETEROGENEOUS CLUSTERS ARE
#                           PRESENT ON COMPUTE NODES
#    diguma      10/22/24 - bug 37198496: LIVE UPDATE PROTECTED UNDER FEATURE
#                           FLAG (addl jiras EXACS-141925 and EXACS-141638)
#    diguma      10/11/24 - Bug 37163375 - EXACS:24.4.1:CELL CLUSTERLESS
#                           PRECHECK IS FAILS BUT DOM0 PATCH IS WORKING
#    araghave    10/08/24 - Enh 36505637 - IMPROVE POLLING MECHANISM IN CASE
#                           OF INFRA PATCHING OPERATIONS
#    jyotdas     10/01/24 - ER 37089701 - ECRA Exacloud integration to enhance
#                           infrapatching operation to run on a single thread
#    sdevasek    09/23/24 - ENH 36654974 - ADD CDB HEALTH CHECKS DURING DOM0
#                           INFRA PATCHING
#    araghave    08/14/24 - Enh 36923844 - INFRA PATCHING CHANGES TO SUPPORT
#                           PATCHING ADMIN SWITCH
#    araghave    09/16/24 - Enh 36971721 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE TARGET HANDLER FILES
#    araghave    09/11/24 - Bug 37030766 - WHEN CRS IS DOWN IN ONE OF THE DOMU,
#                           SAME DOMU NAME IS BEING PRINTED TWICE IN LIST
#    araghave    08/30/24 - ER 36977545 - REMOVE SYSTEM FIRST BOOT IMAGE
#                           SPECIFIC CODE FROM INFRA PATCHING FILES
#    emekala     08/30/24 - BUG 37008344 - WHEN PATCH REPORT DETAILS NOT YET
#                           POPULATED DO NOT PRINT ERROR STACKTRACE
#    diguma      08/26/24 - bug 36975348: NEED A NEW INDICATOR OF GI STACK
#                           TO BE STARTED IN EXASCALE BASED CLUSTERS
#    diguma      08/21/24 - bug 36871736:REPLACE EXASPLICE WITH ELU(EXADATA
#                           LIVE UPDATE) FOR EXADATA 24.X
#    araghave    08/21/24 - Enh 36972288 - SUPPORT DOM0 NON-ROLLING GMR
#                           PATCHING WITH ALL RACK NODES IN INCLUDENODELSIT
#    diguma      07/31/24 - Bug 36908409: NEED INDICATOR OF CLUSTER STORAGE
#                           TYPE IN THE EXACLOUD PAYLOAD
#    araghave    07/18/24 - ER 34893466 - EXACS | EXACLOUD THREAD LOG FOR
#                           PATCHING NEEDS MORE INFORMATION - EASE OF USE
#    araghave    07/18/24 - ER 36641819 - EXACC GEN2 | TOOLING TO REPORT THE EXACT
#                           VM NAME WHICH FAILED TO START IN EXACLOUD THREAD
#                           LOGS
#    jyotdas     07/01/24 - Bug 36737760 - EXACC vmstate showing stopped in
#    diguma      06/25/24 - Bug 36727709: IMPLEMENT TFA BLACKOUT NOTIFICATION
#                           FOR DOMU VM OS PATCHING BY INFRAPATCHING TEAM
#    avimonda    06/17/24 - Bug 36586172: Dump JSON status in a file for
#                           automatic filing of exacloud bug.
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    sdevasek    06/07/24 - Bug 36630512 - ADD DEALY BEFORE VALIDATING CDB
#                           SERVICE DEGRADATION DETECTION IN INFRAPATCHING
#                           DOMU OS POSTCHECK
#    sdevasek    06/07/24 - ENH 36639315 - COPY SANITY_CHECK.LOG TO EXACLOUD
#                           LOCATION FOR CDB HEALTH CHECKS FAILURE SCENARIO
#    diguma      06/06/24 - Enh 36691192 - IN CASE OF ADBS, DURING DOM0/KVM
#                           HOST INFRA PATCHING RETRY EXECUTE DOM0DOMU PLUGIN
#    sdevasek    06/05/24 - ENH 36296976 - VALIDATE FOR PDBS RUNNING STATE AND
#                           FOR PDBS IN RESTRICTED MODE DURING DOMU PATCHING 
#    antamil     05/31/24 - Bug 36659206 - Changes to report precheck failure
#                           message to CP
#    sdevasek    05/29/24 - ENH 36659116 - ECRA WR FOR DOMU OS PATCHING STATE
#                           IS NOT CHANGED FROM 202 TO 500 DUE TO ERROR_MESSAGE
#                           STRING OVERFLOW FOR TABLES ECS_REQUESTS_TABLE,
#                           ECS_EXA_APPLIED_PATCHES_TABLE
#    araghave    05/17/24 - Enh 36293209 - USE PLUGIN FILES FROM THE NEW
#                           EXADATA VERSION PLUGIN LOCATION
#    araghave    05/06/24 - Bug 36543876 - ERROR OUT WHEN GRID HOME PATH BINARY
#                           DOES NOT EXISTS FOR CRS AUTOSTART ENABLED CHECK
#    apotluri    04/10/24 - Enhancement Request 36492251 - INFRAPATCHING :
#                           OPTIMISE CODE AROUND PATCHMGR START AND END PHASE
#                           FOR BETTER CPU UTILISATION
#    sdevasek    04/08/24 - Bug 36486779 - PATCHMGR RELATED ERROR MESSAGES  
#    jyotdas     03/25/24 - Bug 36425641 - exacc gen2 -high availability check
#    antamil     03/11/24 - Enh 36372221 - Code changes for single VM EXACS
#                           patching support
#    diguma      03/24/24 - Bug 36442733 - MORE ROBUST METHOD TO OBTAIN
#                           CRS HOME
#    araghave    03/24/24 - Enh 36270822 - EXECUTION OF EXACLOUD PLUGINS USING
#                           INFRA PATCHING PLUGIN METADATA
#    emekala     03/12/24 - ENH 35494282 - ENABLE AND LOG CRS AND HA CHECK
#                           ERRORS DURING DOM0 PATCH PRECHECK AS WARNINGS
#    jyotdas     02/28/24 - Enh 35474573 - Validate and certify exacloud plugin
#                           support on adbd exacc
#    avimonda    02/21/24 - Bug 36294457 - EXACLOUD ERROR_JSON IN PRETTY FORMAT
#                           IN THE TRACES
#    antamil     03/06/23 - Bug 36371934 - Powered off VM should not be 
#                           considered for single VM clusters
#    jyotdas     02/06/24 - Bug 36264934 - Dom0 Patch is failing with error
#    jyotdas     02/05/24 - ER 36108549 - adbd dom0domu plugins should be
#                           enabled in case user specified dom0 plugin type
#    josedelg    01/26/24 - Bug 36060863 - Get cell count from CP
#    jyotdas     01/22/24 - Bug 36024518 - QMR failing for HA check when vm
#                           cluster was stopped by customer before patching
#    jyotdas     01/19/24 - 36157656 - enhance infrapatch domu details payload
#                           to pass vms shutdown by customer
#    araghave    01/18/24 - Enh 34708925 - AVOID COPYING SYSTEM.IMG DURING 
#                           PATCHING
#    avimonda    01/18/24 - Get Exacloud patchmgr retry cleanup check max
#                           counter value
#    antamil     02/02/23 - 36109360 - Codes changes for Cps as launch node
#    apotluri    12/15/23 - Bug 36107235 - ECRA REQUEST STATUS FOR EXACOMPUTE
#                           OPS SHOWS INVALID LOCATION IN EXACLOUD_THREAD_LOG
#    araghave    12/06/23 - Enh 36069257 - EXACC GEN 2 | MODIFY THE TIME SPENT 
#                           IN CHECKING CRS AVAILABILITY ON GUEST VM NODES THAT 
#                           ARE NOT ACCESSIBLE
#    apotluri    12/04/23 - Bug 35871652 - PATCH FAILURE JSON IS MISSING
#                           REQUEST_START_TIME FIELD
#    sdevasek    11/22/23 - Bug 36025803 - EXACC:HEARTBEAT NOT ESTABLISHED BUT
#                           PATCHING MOVED TO NEXT DOM0 NODE   
#    sdevasek    11/20/23 - Bug 36015891 - SVM:DOM0 PRECHECK FAILS:INSUFFICIENT
#                           LAUNCH NODE(S) FOUND ON THE ENVIRONMENT TO PATCH
#    sdevasek    11/15/23 - ENH 36011846 - RUN RDS_PING TO VALIDATE VM TO VM
#                           AND VM TO CELL CONNECTIVITY AFTER HEARTBEAT CHECK
#                           FAILURE IN DOM0 PATCHING
#    jyotdas     11/08/23 - Bug 35947965 - domu os patching errors should be
#                           fail_and_show
#    araghave    28/11/23 - Bug 36011741 - EXACC GEN 2 | INFRA PATCHING | QMR
#                           FAILING FOR HA CHECK EVEN THOUGH CUSTOMER VMS ARE
#                           SHUTDOWN WITH ZERO CPU CORES
#    antamil     10/17/23 - Bug 35835537 - Implement support for multiple external
#                                          launch node
#    antamil     09/29/23 - Bug 35851548 - Append request Id to dbnodes file name
#                           to be unique
#    sdevasek    09/20/23 - BUG 35820002 - DOM0 ROLLING PATCHING FAILS : USER
#                           SPECIFIED NODE DOES NOT EXIST IN THE ORIGINAL
#                           LAUNCH NODE CANDIDATES 
#    avimonda    09/18/23 - Bug 35659081 - Get max retries value for validate
#                           image checksum
#    antamil     18/08/23 - ENH 35577433 - ADD VALIDATIONS ON EXTERNAL LAUNCH NODE
#    emekala     09/01/23 - Bug 35288637 - ADD DBNUVERSION TO PATCHMGR FAILURE
#                           JSON
#    araghave    08/30/23 - Enh 35686722 - EXACC:PATCH_PREREQ_CHECK:FAILURE ON
#                           DOMU DOES NOT PROVIDE SEPARATE ERROR INFO FOR
#                           DIFFERENT NODES
#    araghave    08/14/23 - Enh 35244586 - DISABLE PRE AND POST CHECKS NOT
#                           APPLICABLE DURING MONTHLY PATCHING
#    araghave    08/12/23 - Bug 35703803 - EXACC GEN 2 | QMR IS GOT FAILED
#                           BECAUSE ITS CHECKING HIGH AVAILABILITY AT VM SIDE
#                           WHERE CUSTOMER BRING IT DOWN INTENTIONALLY
#    sdevasek    08/09/23 - ENH 35687013 - CREATE AND DELETE MARKER FILE DURING
#                           PATCHING WHEN CPS IS USED AS LAUNCHNODE
#    jyotdas     08/08/23 - ENH 35614504 - Define erroraction for infrapatching
#                           at errorcode level instead of targettype level
#    antamil     08/03/23 - ENH 35621978 - ENABLE CPS AS LAUNCHNODE FOR
#                           DOMU PATCH OPERATION
#    jyotdas     07/26/23 - ENH 35641075 - Develop a generic framework for
#                           infrapatching api validation execution
#    avimonda    07/25/23 - Bug 34986894 - Adjust the patchmgr timeout to
#                           prevent CELLs patching timeout in rolling mode.
#    sdevasek    07/08/23 - BUG 35555704 - EXACS:BB:INFRAPATCHING:DOM0 PATCH
#                           FAILED AS VM IS NOT ACCESSIBLE
#    pkandhas    07/05/23 - Enh 35371653, Remove Obsolete SSH keys
#    araghave    07/03/23 - Bug 35489234 - DOM0 POSTCHECK OPERATION FAILS FOR
#                           HEARTBEAT CHECK AND UNABLE TO START CRS EVEN WHEN
#                           KEYS ARE AVAILABLE
#    vikasras    06/27/23 - Bug 35456901 - MOVE RPM LIST TO INFRAPATCHING.CONF
#                           FOR SYSTEM CONSISTIENCY DUPLICATE RPM CHECK 
#    sdevasek    06/26/23 - BUG 35509499 - AIM4EXA2.0 - BUG NOT CREATED FOR 
#                           INCIDENT IN BUG 35481344
#    antamil     06/21/23   ENH 35026503 - SUPPORT TO LAUNCH MULTIPLE PATCHMGR 
#                           SESSIONS ON THE GIVEN EXTERNAL LAUNCH NODE
#    araghave    06/09/23 - Enh 35479785 - PARAMETERISE TO ENABLE PERFORMING
#                           SPACE VALIDATIONS ON INDIVIDUAL TARGETS
#    antamil     05/26/23 - Enh 35340706 - Infrapatch support for decomposed
#                           rack
#    jyotdas     05/15/23 - ENH 35382596 - Store idempotency metadata in ecra
#                           db for active-active upgrade during infrapatching
#    sdevasek    05/01/23 - BUG 35335917 - ACTIVE ACTIVE UPGRADE: ERROR OCCURS
#                           WITH _JSON_PATCH_REPORT_DATA DOES NOT HAVE
#                          'NODE_PROGRESSING_STATUS' KEY AFTER THE SWITCHOVER
#    araghave    04/24/23 - Enh 35317523 - MAKE INFRA PATCHING HIGH
#                           AVAILABILITY CHECKS CONFIGURABLE IN
#                           INFRAPATCHING.CONF
#    araghave    04/20/23 - bug-35281111 - exacs| exacloud patch and prepatch
#    jyotdas     04/17/23 - ENH 35106082 - By default run dom0domu plugin on
#                           autonomous vms
#    araghave    03/23/23 - Enh 35098710 - FOR MVM CLUSTER PRE-CHECK FAILED
#                           WHEN ONE VM - CPU SCALE DOWN TO 0 SO VM IS SHUTDOWN
#                           FOR THAT CLUSTER
#    antamil     03/07/23 - Bug 35054815 -LAUNCH NODE SUPPORT FOR PROVIDIONED
#                           CLUSTER AND CLUSTERLESS DOM0 PATCHING
#    araghave    02/22/23 - ENH 35105936 - ADD FWVERIFY VALIDATIONS DURING
#                           IBSWITCH PRECHECK
#    jyotdas     02/14/23 - ENH 35029839 - Enhance exacloud to create json file
#                           with patch failure details
#    sdevasek    02/02/23   BUG 35019632 - JSONDecodeError is coming while
#                           loading target json file from launchnode
#    antamil     13/01/23   BUG 34959522 = FIX FOR PATCHMGR ERROR DETAILS
#                           MISSING IN PRECHECK
#    araghave    01/13/22 - Enh 34859379 - PERFORM CRS BOUNCE BEFORE HEARTBEAT
#                           CHECK TIMEOUT, IF DOMUs ARE UNABLE TO ESTABLISH
#                           A HEART BEAT TO THE CELLS
#    araghave    01/06/23 - Bug 34953949 - DOMU HEARTBEAT VALIDATIONS NEED TO
#                           BE PERFORMED USING CUSTOMER HOSTNAME
#    araghave    12/19/22 - Enh 34339397 - REMOVE RESTRICTION FOR MULTIPLE
#                           PATCHMGR ON SINGLE LAUNCH NODE
#    pkandhas    12/07/22 - BUG 34862200 - Set timeout for dbmcli/cellcli
#    jyotdas     11/29/22 - BUG 34777710 - Plugin failures no longer report the
#                           customer domu name in error
#    araghave    11/25/22 - Bug 34828301 - EXACC:INFRA-PATCH:DOM0 PRECHECK
#                           EXPECT INCORRECT SPACE REQUIREMENT - SPACE IN / -
#                           NEEDED 5120 GB, GOT 2207 GB
#    talagusu    11/17/22 - Bug 34808547 - INFRA LOGGING ENH ON TOP OF BUG 34644538
#    araghave    11/23/22 - Bug 34592207 - INFRA PATCHING SHOULD FAIL WHEN ONE
#                           OF VM IS DOWN
#    jyotdas     11/08/22 - BUG 34726052 - Return cluster information from ecra
#                           for all vm
#    asrigiri    11/07/22 - Bug 34644538 - Diagnostic enhancement to log DomU list from ECRA and Dom0
#    araghave    10/17/22 - Enh 34683285 - INFRA PATCHING CHANGES FOR EXADATA
#                           PATCHMGR ERROR HANDLING
#    jyotdas     10/11/22 - BUG 34681939 - Infrapatching compute nodes should
#                           be sorted by dbserver name from ecra
#    jyotdas     10/10/22 - Bug 34681437 - Infrapatch nodes are getting patched
#                           in random order
#    araghave    09/29/22 - Enh 34623863 - PERFORM SPACE CHECK VALIDATIONS
#                           BEFORE PATCH OPERATIONS ON TARGET NODES
#    araghave    09/23/22 - Bug 34629293 - DOMU PRECHECK OPERATION FAILING AT
#                           EXACLOUD LAYER DUE TO CHECKSUM ISSUE
#    araghave    09/14/22 - Enh 34480945 - MVM IMPLEMENTATION ON INFRA PATCHING
#                           CORE FILES
#    sdevasek    09/01/22 - ENH 34510052 - EXACLOUD CHANGES TO GET IMAGEINFO
#                           DETAILS AS PART OF NODE_PROGRESS_STATUS
#    sdevasek    07/18/22 - ENH 34384737 - CAPTURE EXACLOUD START_TIME,
#                           EXACLOUD_END_TIME AND PATCHING TIME TAKEN BY NODES
#    jyotdas     07/07/22 - ENH 34316717 - Pass dom0 list and cell list as part
#                           of infrapatching payload
#    araghave    06/16/22 - Enh 34138779 - RUN EXACLOUD PLUGIN ON ALL DOMUS
#                           WHICH ARE PROVISIONED AS PART OF MVM ENV
#    sdevasek    06/07/22 - Bug 34246727 - EXACS: DOMU EXACSOSPATCH PRECHECK
#                           FAILS WITH ERROR STALE MOUNT(S) DETECTED ON DOMU
#    sdevasek    05/22/22 - ENH 33859232 - TRACK TIME PROFILE INFORMATION FOR 
#                           INFRAPATCH OPERATIONS
#    sdevasek    05/11/22 - ENH 34053202 - INFRAPATCHING PRECHECK TO VALIDATE
#                           THE PRESENCE OF DOM0_IPTABLES_SETUP.SH SCRIPT
#    araghave    04/12/22 - Enh 33833262 - DOM0 AND DOMU LAUNCH NODES SPACE
#                           MANAGEMENT
#    araghave    04/19/22 - Enh 33516791 - EXACLOUD: DO NOT OVER WRITE THE
#                           ERROR SET BY RAISE EXCEPTION
#    nmallego    04/17/22 - Bug33689792 - Skip dummy vm for domu availability
#    araghave    02/15/22 - Enh 33808723 - Make Roceswitch unkey option
#                           configurable in infrapatching.conf
#    sdevasek    01/18/22 - Enh 32509673 - Require ability to specify Cell
#                           nodes to include as part of Patching process
#    araghave    01/18/22 - Enh 30646084 - Require ability to specify compute
#                           nodes to include as part of Patching process
#    araghave    11/23/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES
#                           FROM ERROR.PY TO INFRAPATCHERROR.PY
#    jyotdas     11/22/21 - ENH 33415996 - Check for stale mounts parallely
#    nmallego    11/22/21 - Bug33584494 - Change the position of setenv call
#    jyotdas     11/19/21 - ENH 33577777 - Handle dbnu plugin script location
#                           in infrapatching to support exacc
#    nmallego    11/10/21 - Bug33521580 - Change operation style to auto for
#                           prechecks
#    araghave    10/20/21 - Enh 33486853 - MOVE TIMEOUT AND OTHER CONSTANTS OUT
#                           OF CODE INTO CONFIG/CONSTANT FILES
#    josedelg    10/04/21 - Bug 33285054 - VIF-BRIDGE symlinks validation in
#                           the post check operation
#    jyotdas     09/22/21 - Enh 33290086 - stale mount check before starting
#                           dbserver patching for all nodes
#    araghave    09/03/21 - Enh 32626119 - Infra patching to notify end user
#                           regarding Grid Disks in Unused/Syncing status
#    nmallego    08/31/21 - Bug33249608 - Support non-rolling option
#    araghave    08/02/21 - Enh 33182904 - Move all configurable parameters
#                           from constants.py to Infrapatching.conf
#    araghave    07/20/21 - ENH 33099120 - INTRODUCE A SPECIFIC ERROR CODE FOR
#                           PATCHMGR CONSOLE READ TIME OUT
#    araghave    07/09/21 - BUG 33081173 - Remove older error codes from Infra
#                           patching core files
#    jyotdas     06/30/21 - Bug 32813015 - non-rolling patching should not run
#                           dom0domu plugin
#    jyotdas     06/22/21 - Bug 32991692 - cell monthly patching should always
#                           operate in rolling style
#    araghave    05/19/21 - Bug 32888564 - Roceswitch patching uses Root user
#                           instead of Admin user
#    araghave    03/23/21 - Enh 31423563 - PROVIDE A MECHANISM TO MONITOR INFRA
#                           PATCHING PROGRESS
#    jyotdas     03/22/21 - Enh 32415195 - error handling: return infra
#                           patching dispatcher errors to caller
#    nmallego    03/18/21 - ER 32581076: Check domU availability on each dom0
#    araghave    03/08/21 - Bug32593118 - Collect the actual patchmgr status
#                           only when patchmgr is success
#    nmallego    01/28/21 - Bug31963499-Instrumented code to track return
#                           payload
#    josedelg    01/20/21 - Bug 32387832 -  Refactored bug 31919030
#    araghave    01/12/21 - Enh 31446326 - SUPPORT OF SWITCH OPTION AS TARGET
#                           TYPE THAT TAKES CARE OF BOTH IB AND ROCESWITCH
#    araghave    01/07/21 - Bug 32320030 - ROCE SWITCH REFACTOR CODE CHANGES
#    nmallego    12/23/20 - Bug32284276 - Restrict non-rolling for exasplice on
#                           dom0
#    araghave    10/21/20 - Enh 31925002 - Enh 31925002 - Error code handling 
#                           implementation for Monthly Patching
#    nmallego    10/27/20 - Enh 31540038 - INFRA PATCHING TO APPLY/ROLLBACK
#                           EXASPLICE/MONTHLY BUNDLE
#    nmallego    10/23/20 - ER 31684959 - Add exaunitId, exaOcid, and exasplice
#                           as part of exacloud result payload
#    nmallego    10/09/20 - Bug31987132 - Return [] instead of None in
#                           mGetExcludedList()
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#

import traceback
import time
import datetime
import json
import random
import glob
from uuid import uuid4
from time import sleep

from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB
from exabox.core.Node import exaBoxNode
from exabox.infrapatching.core.infrapatcherror import *
from exabox.infrapatching.core.clupatchhealthcheck import ebCluPatchHealthCheck
from exabox.infrapatching.core.infrapatchtimestats import InfrapatchingTimeStatsRecord
from exabox.infrapatching.handlers.loghandler import LogHandler
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.ibfabricpatch import IBFabricPatch
from exabox.infrapatching.utils.utility import mGetInfraPatchingConfigParam,runInfraPatchCommandsLocally, \
        mTruncateErrorMessageDescription, mCheckFileExists, mGetSshTimeout, mGetInfraPatchingHandler, \
        mExaspliceVersionPatternMatch, mQuarterlyVersionPatternMatch, mCheckAndFailOnCmdTimeout
from exabox.infrapatching.utils.infrapatchexecutionvalidator import InfrapatchExecutionValidator
from exabox.ovm.clumisc import OracleVersion
from exabox.infrapatching.helpers.crshelper import CrsHelper
from exabox.ovm.vmcontrol import exaBoxOVMCtrl
from exabox.utils.node import connect_to_host

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

class GenericHandler(LogHandler):

    def __init__(self, *initial_data, **kwargs):
        super(GenericHandler, self).__init__()
        self.mPatchLogInfo("GenericHandler")

        self.__isSingleWorkerRequest = None
        self.__is_exacompute_patching = None
        self.__elu_target_version_to_node_mappings = None
        for dictionary in initial_data:
            for key in dictionary:
                if key == "CluControl":
                    self.__cluctrl = dictionary[key]
                elif key == "LocalLogFile":
                    self.__log_path = dictionary[key]
                elif key == "TargetType":
                    self.__target_type = dictionary[key]
                elif key == "Operation":
                    self.__task = dictionary[key]
                elif key == "OperationStyle":
                    self.__op_style = dictionary[key]
                elif key == "PayloadType":
                    self.__payload = dictionary[key]
                elif key == "TargetEnv":
                    self.__target_env = dictionary[key]
                elif key == "TargetVersion":
                    self.__target_version = dictionary[key]
                elif key == "BackupMode":
                    self.__backup_mode = dictionary[key]
                elif key == "Fedramp":
                    self.__fedramp = dictionary[key]
                elif key == "Retry":
                    self.__patch_req_retry = dictionary[key]
                elif key == "RequestId":
                    self.__master_request_id = dictionary[key]
                elif key == "AdditionalOptions":
                    self.__additional_options = dictionary[key]
                elif key == "ClusterID":
                    self.__cluster_id = dictionary[key]
                elif key == "Dom0DomuPatchZipFile":
                    self.__dom0domUPatchZipFiles = dictionary[key]
                elif key == "CellIBSwitchesPatchZipFile":
                    self.__CellSwitchesZipFile = dictionary[key]
                elif key == "RackName":
                    self.__rack_name = dictionary[key]
                elif key == "ComputeNodeList":
                    self.__computeNodeList = dictionary[key]
                elif key == "ComputeNodeListByAlias":
                    self.__computeNodeListByAlias = dictionary[key]
                elif key == "isMVM":
                    self.__isMVM = dictionary[key]
                elif key == "StorageNodeList":
                    self.__storageNodeList = dictionary[key]
                elif key == "Dom0domUDetails":
                    self.__dom0domuDetails = dictionary[key]
                elif key == "Idempotency":
                    self.__idemPotencyData = dictionary[key]
                elif key == "InfraPatchPluginMetaData":
                    self.__pluginsMetadata = dictionary[key]
                elif key == "adb_s":
                    self.__isADBS = dictionary[key]
                elif key == "ExacloudChildReqUUID":
                    self.__exacloud_child_request = dictionary[key]
                elif key == "ExacloudMasterReqUUID":
                    self.__exacloud_master_request = dictionary[key]
                elif key == "isSingleWorkerRequest":
                    self.__isSingleWorkerRequest = dictionary[key]
                elif key == "isExaComputePatching":
                    self.__is_exacompute_patching = dictionary[key]
                elif key == "ELUTargetVersiontoNodeMappings":
                    self.__elu_target_version_to_node_mappings = dictionary[key]

            self.__allArgs = dictionary

        # These are used by locking  and then for release locking. So should be defined here and taskhandler,targetHandler can access them through getters and setters . Has getters and setters
        self.__fabric = None
        self.__fabric_id = None
        self.__process = None
        self.__admin_switches_list = []
        self.__process_cns_monitor = None
        self.__admin_switch_patch_apply = ""
        self.__executed_targets = []
        self.__current_target_type = ""
        self.__json_status = {}
        self.__domuNatHostNameToCustomerHostName = {}
        self.__domuCustomerHostNameToNatHostName = {}
        self.__include_node_list = []
        self.__exadata_env_type = ENV_ECS
        self.__patching_dom0_and_domu_list_from_ecra = []
        self.__dom0_and_domu_customer_hostname_list_from_ecra_with_non_zero_vcpu = []
        self.__ClusterToVmMappingWithNonZeroVcpu = []
        self.__ClustersWithSingleVM = set()
        self.__user_to_node_mapping_to_run_crs_cmds = {}
        self.__user_to_node_mapping_to_run_plugins = {}
        # Below one is used to track cell upgrade completed when both
        # cell+dom0 is given in the request.
        self.__cell_upgrade_passthrough = False

        self.__mListOfStatementsToPrint=[]

        # Include node list
        self.__all_dom0s = []
        self.__dom0_customized_list = []
        self.__all_domus = []
        self.__domu_customized_list = []
        self.__computeNodeListSortedByAlias = []
        self.__dom0ToClusterList = []
        self.__clusterToGuestVMList = []
        self.__collect_time_stats = False
        # KVM environment variable
        self.__kvm_env = False
        self.__step_list = None
        self.__crs_helper = None

        #InfraPatch Execution Validator
        self.__infrapatch_execution_validator = InfrapatchExecutionValidator(self.__target_type)

        # To use crshelper methods
        self.__crs_helper = CrsHelper(aHandler=self)

        # ExaCC environment variable
        self.__exacc = False

        # Needed here since used by mAddError in pluginhandler as well
        self.__patchmgr_log_path_on_launch_node = ""

        # To store launchnode used during patching, needed to read exadata error json details
        self.__cur_launch_node_list = []

        self.__external_launch_node = None

        self.__shutdown_services = \
            (self.__op_style == OP_STYLE_NON_ROLLING and
             self.__task in [TASK_PATCH, TASK_ROLLBACK])

        if self.__shutdown_services:
            self.__mListOfStatementsToPrint.append(("WARN", "Requested VMs shutdown."))
        else:
            self.__mListOfStatementsToPrint.append(("WARN", "No VMs shutdown requested."))

        # Generic functions used by all
        self.mSetStepList(self.mCreateStepList())
        self.__clupatchcheck = ebCluPatchHealthCheck(self.__cluctrl, aGenericHandler=self)

        if self.mIsExacomputePatching():
            self.mPatchLogInfo(f"Exacompute patch is performed. Exiting from infrapatching generichandler init method.")
            return

        # Bug27263414: Read grid heartbeat timeout to check the cell
        #              heartbeat from domu.
        if self.mGetExadataPatchGridHeartBeatTimeoutSec():
            self.mPatchLogDebug(
                f"Exadata patch grid heartbeat timeout is {self.mGetExadataPatchGridHeartBeatTimeoutSec()} seconds.")
        else:
            self.mPatchLogError("Invalid exadata patch grid heartbeat timeout is configured.")

        # Read exacloud patch working space size
        if self.mGetExadataPatchWorkingSpaceMB():
            self.mPatchLogDebug(f"Exacloud patch working size is {self.mGetExadataPatchWorkingSpaceMB()} MB.")
        else:
            self.mPatchLogError("Invalid exadata patch working space is configured.")

        # Set KVM environment value - True or False
        self.mSetKvmEnv()

        # Set ExaCC environment value - True or False
        self.mSetExaCC()

        #Set the patch Operation style
        self.mSetPatchOperationStyle()

        # To filter out nodes to run patch operations in
        # case of include node list.
        self.mSetIncludeNodeList(self.mInitializeIncludeListNodes())

        if self.__target_type[0] not in [ PATCH_CELL, PATCH_IBSWITCH, PATCH_SWITCH ]:
            # Set Dom0 List Sorted by Alias
            self.mSetComputeNodeListSortedByAlias()

            # Set DomoDomU list from ecra details
            self.mSetPatchingDom0DomUListFromEcra()

            # Set Dom0ToClusterMapping
            self.mSetDom0ToClusterMapping()
            self.mPatchLogInfo(f"Dom0ToClusterMapping is {self.mGetDom0ToClusterMapping()}")

            # Set ClusterToDomuMapping
            self.mSetClusterToGuestVMMapping()

            # Set Cluster to VM mapping with customer Hostnames and Zero Vcpu
            self.mSetClusterToGuestVMMappingWithNonZeroCPU()

        if self.mIsSingleWorkerRequest():
            self.mPatchLogInfo("No Fabric configuration since this is a single worker request")
        else:
            self.mBuildIBFabric()

        # Include Node list
        self.__all_dom0s = self.mGetDom0ListFromXml()
        self.__dom0_customized_list = self.mGetDom0List()

        self.__autonomousVMList = []
        self.__autonomousVMListWithCustomerHostnames = []
        if self.__target_type[0] not in [ PATCH_CELL, PATCH_IBSWITCH, PATCH_SWITCH ]:
            #Fetch dbnu Plugin Handler base dir prefix
            # For EXACC /u01/downloads/exadata/exadataPrePostPlugins/dbnu_plugins/ or /u01/downloads/exadata/<Exadata version>/exadataPrePostPlugins/dbnu_plugins/
            # for EXACS <EXACLOUD_HOME>//exadataPrePostPlugins/dbnu_plugins/ or <EXACLOUD_HOME>/<Exadata version>/exadataPrePostPlugins/dbnu_plugins/
            self.__dbnu_plugins_base_dir_prefix = self.mGetPluginPathForExaCcCS()

            # Include Node list
            self.__all_domus = self.mGetDomUListFromXml()
            self.__domu_customized_list = self.mGetDomUList()

            #Create AutonomousVM list , if any
            #This value contains the AutonomousVM list on which dom0domu plugins are fired implicitly, only if EnablePlugins is not yes
            #If EnablePlugins = yes , plugin will run on all VM
            self.mSetAutonomousVMList()

        self.mConvertExasplice()

    def mGetCluCtrlInstance(self):
        return self.__cluctrl

    ### Code to be removed ###
    def mConvertExasplice(self):
        # in case of exasplice, dom0 and target host is on 24+, need to get the target version from disk and rebuild all the values

        # check to see if live update is disabled
        _disable_live_update = mGetInfraPatchingConfigParam('disable_live_update')
        if _disable_live_update and _disable_live_update.lower() in ['true']:
            self.mPatchLogInfo('Live update disabled')
            return

        _original_version = self.__target_version
        _isExaplice = False
        _new_target_version = None
        if self.__additional_options[0]['exasplice'].lower() == 'yes':
            _isExaplice = True
        _dom0_to_check = self.mGetDom0ToCheck()
        if PATCH_DOM0 in self.__target_type and _isExaplice and _dom0_to_check and len(self.__target_version) == 6:
            # check for the host
            # 6 digits version convention is compared here.
            _is_of_exaImage_type, _node_version = self.mIsOfexaImageType(_dom0_to_check)
            if _is_of_exaImage_type:
                _new_target_version = self.mGetLatestPatchVersionFromDisk(_node_version)
                if _new_target_version:
                    self.__target_version = _new_target_version
                    _orig_dbpatchfile = self.mGetDom0DomUPatchZipFile()[0]
                    _orig_dom0yum = self.mGetDom0DomUPatchZipFile()[1]
                    _dbpatchfile = _orig_dbpatchfile.replace(_original_version, _new_target_version)
                    _dom0Yum = self.mGetYumRepo24(_new_target_version)
                    self.__dom0domUPatchZipFiles.remove(_orig_dbpatchfile)
                    self.__dom0domUPatchZipFiles.remove(_orig_dom0yum)
                    self.mPatchLogInfo(f'New files {_dbpatchfile} - {_dom0Yum}')
                    if not self.mCheckLocalFileExists(_dbpatchfile):
                        _suggestion_msg = f'File {_dbpatchfile} does not exist. Please check before retrying'
                        self.mPatchLogInfo(_suggestion_msg)
                        self.mAddError(MISSING_PATCH_FILES, _suggestion_msg)
                    elif not self.mCheckLocalFileExists(_dom0Yum):
                        _suggestion_msg = f'File {_dom0Yum} does not exist. Please check before retrying'
                        self.mPatchLogInfo(_suggestion_msg)
                        self.mAddError(MISSING_PATCH_FILES, _suggestion_msg)
                    else:
                        self.__dom0domUPatchZipFiles.insert(0, _dbpatchfile)
                        self.__dom0domUPatchZipFiles.insert(1, _dom0Yum)
                        self.mPatchLogInfo(f'New files in list {self.__dom0domUPatchZipFiles}')

    def mGetPatchPayloadsBasePath(self):
        if self.mIsExaCC():
            # ociexacc_exadata_patch_download_loc: /u01/downloads/exadata/ in exabox.conf
            _base_path = self.mGetCluControl().mCheckConfigOption('ociexacc_exadata_patch_download_loc')
            if _base_path is None:
                _base_path = '/u01/downloads/exadata/'
        else:
            _base_path = get_gcontext().mGetBasePath()
        return _base_path

    # build Dom0YumRepository files
    def mGetYumRepo24(self, aVersion):
        _exacloud_base_path = self.mGetPatchPayloadsBasePath()
        _base_dir = f"{os.path.join(_exacloud_base_path, 'PatchPayloads/')}"
        self.mPatchLogInfo(f'_base_dir {_base_dir}')
        # in case of KVM, the file would be like
        # /u01/2221d4/admin/exacloud/PatchPayloads/24.1.1.0.0.240605/Dom0YumRepository/
        # exadata_ol8_24.1.1.0.0.240605_Linux-x86-64.zip
        if self.mIsKvmEnv():
            _pattern = f'{_base_dir}{aVersion}/Dom0YumRepository/exadata_ol*{aVersion}_Linux-x86-64.zip'
        # Xen - /u01/2221d4/admin/exacloud/PatchPayloads/24.1.1.0.0.240605/Dom0YumRepository/
        #       exadata_ovs_24.1.1.0.0.240605_Linux-x86-64.zip
        else:
            _pattern = f'{_base_dir}{aVersion}/Dom0YumRepository/exadata_ovs*{aVersion}_Linux-x86-64.zip'

        self.mPatchLogInfo(f'pattern {_pattern}')
        _first_file = True
        _files = None
        for _f in glob.glob(_pattern):
            if _first_file:
                _files = _f
                _first_file = False
            else:
                _files = _files + "," + _f
        self.mPatchLogInfo(f'New Dom0YumRepository - {_files}')
        return _files

    # this method considers that all the nodes passed are on the same version, so just pick the first one
    def mGetDom0ToCheck(self):
        _dom0_to_check = None
        if self.mGetIncludeNodeList() and len(self.mGetIncludeNodeList()) > 0:
            _dom0_to_check = self.mGetIncludeNodeList()[0]

        elif self.mGetDom0List() and len(self.mGetDom0List()) > 0:
            _dom0_to_check = self.mGetDom0List()[0]

        return _dom0_to_check

    # check if target host has exadata image 24+
    def mIsOfexaImageType(self, aNode):
        _IsExaImage = True
        _version = None
        # check if target node is of Exadata image version naming convention.
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aNode)
        _i, _o, _e = _node.mExecuteCmd("/usr/local/bin/imageinfo -ver")
        if _o:
            _version = _o.readlines()
            _version = _version[0].strip()
            _IsExaImage = mQuarterlyVersionPatternMatch(_version)

        if _node.mIsConnected():
            _node.mDisconnect()

        return _IsExaImage, _version

    def mIsSingleWorkerRequest(self):
        return (self.__isSingleWorkerRequest is not None) and (self.__isSingleWorkerRequest == 'yes')

    def mGetLatestPatchVersionFromDisk(self, aVersion):
        """
        Get the latest patch version by looking at the file system.
        """
        # version are like 24.1.2.0.0.240727. The prefix of poissible versions
        # on disk should match "xx.xx.". In this case, "24.1."
        _exacloud_base_path = self.mGetPatchPayloadsBasePath()
        _base_dir = f"{os.path.join(_exacloud_base_path, 'PatchPayloads/')}"

        # version are like 24.1.2.0.0.240727. The prefix of poissible versions
        # on disk should match "xx.xx.". In this case, "24.1."
        _prefix_version = f"{aVersion.split('.')[0]}.{aVersion.split('.')[1]}."
        self.mPatchLogInfo(f'prefix {_prefix_version} - base_dir {_base_dir}')

        # get the base of PatchPayloads
        _valid_versions_fs = []
        _latest_ver_from_fs = None

        # instantiate the class oracle version
        _verobj = OracleVersion()

        # List the available patches from the file system PatchPayloads
        # -------------------------------------------------------------
        if os.path.isdir(_base_dir) is True:
            _ldir = os.listdir(_base_dir)
            # Go through the file system to get the latest patch version
            for _entry in _ldir:
                _patch_dir_path = ''
                _patch_dir_path = f'{_base_dir}{_entry}'
                # validate the patch version is dir or not
                if os.path.isdir(_patch_dir_path) is True:
                    # Expect version in form a.b.c.d.e.f[.g] where f is 6 digits
                    # and g is an optional. Example: 12.2.1.1.1.170620,
                    # 18.1.4.0.0.180125.3, 18.1.10.0.0.181031.1.
                    _re_out = re.match('^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\.[0-9]{6,6}(|\.[0-9]+)$', _entry)
                    self.mPatchLogInfo(f're_out {_re_out}')
                    if _re_out:
                        if mQuarterlyVersionPatternMatch(_entry) and _entry.startswith(_prefix_version):
                            _valid_versions_fs.append(_entry)
                    else:
                        self.mPatchLogInfo(f'Skipping: {_entry}')

            self.mPatchLogInfo("Following versions are found in file system:")
            for _ver in _valid_versions_fs:
                self.mPatchLogInfo(f'{_ver}')

        # get the latest/highest version from file system
        #_latest_ver_from_fs = self.mGetHighestVer(_valid_versions_fs, _IsExaImage24)
        _latest_ver_from_fs = _verobj.mGetHighestVer(_valid_versions_fs)
        self.mPatchLogInfo(f'Latest version from file system: {_latest_ver_from_fs}')
        return _latest_ver_from_fs

    def mGetPluginPathForExaCcCS(self):
        '''
          This method determines the plugin stage location and return 
          the path details for plugin execution.
        '''
        _dbnu_plugins_base_dir_prefix = None
        if self.mIsExaCC():
            # ociexacc_exadata_patch_download_loc: /u01/downloads/exadata/ in exabox.conf
            _exadata_bundle_base_dir = self.mGetCluControl().mCheckConfigOption(
                'ociexacc_exadata_patch_download_loc')
            if _exadata_bundle_base_dir is None:
                _exadata_bundle_base_dir = '/u01/downloads/exadata'

            _plugin_exadata_version_stage_path = os.path.join(os.path.join("/u01/downloads/exadata/PatchPayloads/" + self.__target_version), "/exadataPrePostPlugins")
            if os.path.exists(_plugin_exadata_version_stage_path) and len(os.listdir(_plugin_exadata_version_stage_path)) != 0:
                self.mPatchLogInfo(
                    f"Plugin new path found with all the plugins staged and will be used to run plugins : {_plugin_exadata_version_stage_path}.")
                _dbnu_plugins_base_dir_prefix = os.path.join("/u01/downloads/exadata/PatchPayloads/", self.__target_version)
            elif os.path.exists(EXACC_PLUGIN_STAGE_PATH) and len(os.listdir(EXACC_PLUGIN_STAGE_PATH)) != 0:
                self.mPatchLogInfo(
                    f"Plugin files found on the common stage location and will be used to run plugins : {EXACC_PLUGIN_STAGE_PATH}.")
                _dbnu_plugins_base_dir_prefix = _exadata_bundle_base_dir

            self.mPatchLogInfo(f"\nEXACC DBNU plugins base dir prefix '{_dbnu_plugins_base_dir_prefix}'")
        else:
            # Exacloud Home Path
            _dbnu_plugins_base_dir_prefix = get_gcontext().mGetBasePath()
            _plugin_exadata_version_stage_path = get_gcontext().mGetBasePath() + "/" +  "PatchPayloads" + "/" + self.__target_version + "/" + "/exadataPrePostPlugins"
            if os.path.exists(_plugin_exadata_version_stage_path) and len(os.listdir(_plugin_exadata_version_stage_path)) != 0:
                self.mPatchLogInfo(
                    f"Plugin new path found with all the plugins staged and will be used to run plugins : {_plugin_exadata_version_stage_path}.")
                _dbnu_plugins_base_dir_prefix = os.path.join(get_gcontext().mGetBasePath() + "/" +  "PatchPayloads" + "/" + self.__target_version)
            self.mPatchLogInfo(f"\nEXACS DBNU plugins base dir prefix '{_dbnu_plugins_base_dir_prefix}'")
        return _dbnu_plugins_base_dir_prefix

    def mGetPluginMetadata(self):
        return self.__pluginsMetadata

    def mSetPluginMetadata(self, aPluginMetadata):
        self.__pluginsMetadata = aPluginMetadata

    def mIsExacomputePatching(self):
        if self.__is_exacompute_patching is not None:
            return self.__is_exacompute_patching
        else:
            return None

    def mGetCRSHelper(self):
        return self.__crs_helper

    def mGetEluTargetVersiontoNodeMappings(self):
        '''
         In case of ELU patching, below target version list
         with Dom0/DomU will passed as input.

         - Prechecks are performed for all nodes at once.
         - Patch is performed one node at a time.
         - For Dom0 Elu version to node mapping would look like -
             "ELUTargetVersiontoNodeMappings": {
              "24.1.13.0.0.250621": "sea201323exdd011.sea2xx2xx0061qf.adminsea2.oraclevcn.com, sea201323exdd008.sea2xx2xx0061qf.adminsea2.oraclevcn.com,
               sea201323exdd007.sea2xx2xx0061qf.adminsea2.oraclevcn.com, sea201323exdd006.sea2xx2xx0061qf.adminsea2.oraclevcn.com"
              },

         - For DomU Elu version to node mapping would look like -
             "ELUTargetVersiontoNodeMappings": {
                "24.1.15.0.0.250805": "eagles-2fdyd1.client.infrapatchdev.oraclevcn.com,eagles-2fdyd2.client.infrapatchdev.oraclevcn.com"
             },

         - Please note that the ELU upgrade to 22.x and 23.x is not valid and SRE shouldn't
           be registering this in the imageseries registration.
        '''
        _elu_node_list = {}
        if self.__elu_target_version_to_node_mappings is not None:
            _elu_node_list = {
                       _elu_versions: [node.strip() for node in re.split(r',\s*', _list_of_elu_nodes)]
                       for _elu_versions, _list_of_elu_nodes in self.__elu_target_version_to_node_mappings.items()
            }
            return _elu_node_list
        else:
            return None

    def mGetEluOptions(self):
        '''
         Applicable only to DomU patching for now and
         valid values of ELUOptions are
         "highcvss, allcvss, full, apply pending"
        '''
        if self.__additional_options and 'ELUOptions' in self.__additional_options[0]:
            return self.__additional_options[0]['ELUOptions']
        else:
            return None

    def mIsElu(self):
        '''
         This method determines whether the current infra patching
         operation is ELU or not and execution flow is run only in 
         case of ELUTargetVersiontoNodeMappings is passed in the input
         payload. 
        '''
        _ret = False
        if self.mIsExaSplice() and self.__elu_target_version_to_node_mappings and len(self.__elu_target_version_to_node_mappings) > 0:
            _ret = True
        return _ret

    def mGetExadataLiveUpdateDetails(self, aDomU):
        '''
         Checks if ELU (Exadata Live Update) outstanding work can be applied on a list of DomU nodes.
         Args:
             aDomU (string): A DomU hostname to check for ELU outstanding work.
             Only 1 domu will be patched at a time during elu apply.
         Returns:
             _ret - PATCH_SUCCESS_EXIT_CODE - if imageinfo -all command can return required details, error code otherwise.
             _current_qmr_image_version - Current QMR version on the node.
             _elu_info - dictionary that contains
                 _live_update_version - Elu image version applied.
                 _applied_elu_type_on_domu - Elu image type applied on Domu.
                 _outstanding_work_msg - Imageinfo output string - imageinfo output string used to determine if
                                        ELU is already applied and a reboot is required.
             _is_elu_outstanding_work_applicable - Can outstanding work items be applied - True/False
        '''
        _ret = PATCH_SUCCESS_EXIT_CODE
        _current_live_update_version_msg = None
        _applied_elu_type_on_domu = None
        _outstanding_work_msg = None
        _elu_info = {
            'elu_version': '',
            'elu_type': '',
            'elu_has_outstanding_work': 'no exadata live update active',
        }
        _allowed_migrations = {
            "highcvss": ["allcvss", "full", "applypending"],
            "allcvss": ["full", "applypending"],
            "full": ["applypending"],
            "applypending": []
        }
        _is_elu_outstanding_work_applicable = False
        _live_update_version = None
        _current_qmr_image_version = None

        # Helper for regex extraction to keep logic simple
        def _extract_image_version_regex(aPattern, aImageDetails, group=1):
            _desired_output = re.search(aPattern, aImageDetails)
            return _desired_output.group(group).strip() if _desired_output else None

        _domu = exaBoxNode(get_gcontext())

        try:
            _domu.mConnect(aHost=aDomU)
            _cmd_get_image_output = "/usr/local/bin/imageinfo -all"
            _i, _o, _e = _domu.mExecuteCmd(_cmd_get_image_output)
            mCheckAndFailOnCmdTimeout(aCmd=_cmd_get_image_output, aNode=_domu, aHandler=self)

            if _domu.mGetCmdExitStatus() != 0:
                self.mPatchLogError('Unable to fetch imageinfo outstanding work items apply status.')
                _ret = IMAGE_VERSION_EMPTY_OR_INVALID
                _elu_info['elu_version'] = _live_update_version
                _elu_info['elu_type'] = _applied_elu_type_on_domu
                _elu_info['elu_has_outstanding_work'] = 'no exadata live update active'
                return _ret, _current_qmr_image_version, _elu_info, _is_elu_outstanding_work_applicable

            _output = _o.readlines()
            for _image_details in _output:
                if ELU_VERSION_STR in _image_details:
                    # Exadata Live Update Version can be:
                    #   Exadata Live Update Version: 24.1.15.0.0.250805
                    #   Exadata Live Update Version: 24.1.15.0.0.250805 (Live Update applied. Reboot at any time to finalize outstanding items.)
                    _current_live_update_version_msg = _extract_image_version_regex(
                        re.escape(ELU_VERSION_STR) + r':\s*(.*)', _image_details
                    )
                    _live_update_version = _extract_image_version_regex(
                        re.escape(ELU_VERSION_STR) + r':\s*([\d\.]+)', _image_details
                    )
                elif ELU_TYPE_STR in _image_details:
                    _applied_elu_type_on_domu = _extract_image_version_regex(
                        re.escape(ELU_TYPE_STR) + r':\s*([^\s\(]+)', _image_details
                    )
                elif ELU_HAS_OUTSTANDING_WORK_STR in _image_details:
                    _outstanding_work_msg = _extract_image_version_regex(
                        re.escape(ELU_HAS_OUTSTANDING_WORK_STR) + r':\s*(.*)', _image_details
                    )
                elif CURRENT_QMR_VERSION_STR in _image_details:
                    _current_qmr_image_version = _extract_image_version_regex(
                        re.escape(CURRENT_QMR_VERSION_STR) + r':\s*([\d\.]+)', _image_details
                    )

            if _live_update_version:
                self.mPatchLogInfo(f"Exadata live update version - {_live_update_version}")
            if _applied_elu_type_on_domu:
                if _applied_elu_type_on_domu in [ "all", "high" ]:
                    _applied_elu_type_on_domu = _applied_elu_type_on_domu + "cvss"
                self.mPatchLogInfo(f"Exadata live update applied - {_applied_elu_type_on_domu}")
            if _outstanding_work_msg:
                self.mPatchLogInfo(f"Exadata Live Update Has Outstanding Work - {_outstanding_work_msg}")

            '''
              - In case ELU was never applied, apply the elu based on elu options passed.
              - In case target version passed is not equal to the current elu version applied,
                 apply the elu based on elu options passed.
              - Target version cannot be less than live update version. If it is the case of
                lower target version passed, ELU patch may not exhibit the right behavior.
            '''
            if not _live_update_version or (str(self.mGetTargetVersion()) != str(_live_update_version)):
                self.mPatchLogInfo(f"Elu upgrade version - {self.mGetTargetVersion()} will be aplicable for patching - Domu - {aDomU}")
                _is_elu_outstanding_work_applicable = True # Migration to a different version is always allowed
            elif _applied_elu_type_on_domu and self.mGetEluOptions() in _allowed_migrations.get(_applied_elu_type_on_domu, []):
                self.mPatchLogInfo(f"Elu patch will be applied on DomU - {aDomU} based on the current elu type - {_applied_elu_type_on_domu} and the elu type passed for upgrade as part of payload is {self.mGetEluOptions()}.")
                _is_elu_outstanding_work_applicable = True
            else:
                self.mPatchLogInfo(f"Elu patch will be skipped on DomU - {aDomU} due to the unsupported ELU Target version and ELU option combination specified.")
                _is_elu_outstanding_work_applicable = False

            '''
             In case of domu upgraded using "full" elu option, live upgrade details will not be present post applypending
             and rollback operation must not depend on the elu outstanding work items details or live update version.

              [root@auto-hbzvr2 ~]# imageinfo

              Kernel version: 5.4.17-2136.343.5.5.el8uek.x86_64 #3 SMP Sat Jul 26 16:34:30 PDT 2025 x86_64
              Uptrack kernel version: 5.4.17-2136.345.5.3.el8uek.x86_64 #3 SMP Wed Jul 9 10:52:40 PDT 2025 x86_64
              Image kernel version: 5.4.17-2136.343.5.5.el8uek.x86_64
              Image version: 24.1.15.0.0.250805
              Image activated: 2025-11-17 09:31:01 +0000
              Image status: success
              Exadata software version: 24.1.15.0.0.250805
              Node type: GUEST
              System partition on device: /dev/mapper/VGExaDb-LVDbSys1

              [root@auto-hbzvr2 ~]#
            '''
            if not _live_update_version and self.mGetTask() == TASK_ROLLBACK:
                self.mPatchLogInfo(f"This domu, {aDomU}, is eligible for rollback in ELU context in the current scenario and will proceed.")
                _elu_info['elu_version'] = ''
                _elu_info['elu_type'] = ''
                _elu_info['elu_has_outstanding_work'] = 'yes'
                return _ret, _current_qmr_image_version, _elu_info, _is_elu_outstanding_work_applicable

            '''
             Imageinfo output will contain "Exadata Live Update Has Outstanding Work" message
             in newer Exadata images and below output could be observed.

             [root@auto-hbzvr2 ~]# /tmp/imageinfo_main_251007 -all
             Exadata Live Update Type: high (CVSS 7-10)
             Exadata Live Update Version: 24.1.15.0.0.250805
             Exadata Live Update Has Outstanding Work: Yes

             In other versions of Exadata, imageinfo will not contain "Exadata Live Update Has Outstanding Work"
             and below output could be observed.

             [root@auto-hbzvr2 ~]# imageinfo
             Exadata Live Update Type: all (CVSS 1-10)
             Exadata Live Update Version: 24.1.15.0.0.250805 (Live Update applied. Reboot at any time to finalize outstanding items.)
            '''
            if _outstanding_work_msg:
                _out_msg_lower = _outstanding_work_msg.lower()
                if 'yes' in _out_msg_lower:
                    '''
                      Cases where ELU outstanding items will be applied.
                      Domu will reboot after the outstanding work items are applied.
                    '''
                    self.mPatchLogInfo(
                        f"Elu outstanding work apply will be applied on {aDomU} as the imageinfo exadata-live-update-has-outstanding-work is - {_outstanding_work_msg}.")
                    _elu_info['elu_version'] = _live_update_version
                    _elu_info['elu_type'] = _applied_elu_type_on_domu
                    _elu_info['elu_has_outstanding_work'] = 'yes'
                    return _ret, _current_qmr_image_version, _elu_info, _is_elu_outstanding_work_applicable
                elif any(_no_msg in _out_msg_lower for _no_msg in ['no', 'no exadata live update active']):
                    # Cases where ELU outstanding items will not be applied.
                    self.mPatchLogInfo(
                        f"Elu outstanding work apply will be skipped on {aDomU} as the imageinfo exadata-live-update-has-outstanding-work is - {_outstanding_work_msg}.")
                    _elu_info['elu_version'] = _live_update_version
                    _elu_info['elu_type'] = _applied_elu_type_on_domu
                    _elu_info['elu_has_outstanding_work'] = _outstanding_work_msg
                    _is_elu_outstanding_work_applicable = False
                    return _ret, _current_qmr_image_version, _elu_info, _is_elu_outstanding_work_applicable

            elif _current_live_update_version_msg:
                if ELU_APPLIED_REBOOT_MESSAGE in _current_live_update_version_msg:
                    '''
                      Cases where ELU outstanding items will be applied.
                      Domu will reboot after the outstanding work items are applied.
                    '''
                    self.mPatchLogInfo(
                            f"Elu outstanding work apply will be applied on {aDomU} as the imageinfo output has the message - 'Live Update applied. Reboot at any time to finalize outstanding items.'")
                    _outstanding_work_msg = 'yes'
                else:
                    """
                     Elu is already applied on the current node and outstanding work items output must be returned as - 'no'.
                     Although imageinfo contain live update version in this case, 'Live Update applied. Reboot at any time to finalize outstanding items'
                     message is not observed in the output. This means applypending was already performed and Domu is already rebooted, no further ELU action
                     will be required.
                    """
                    self.mPatchLogInfo(
                         f"Elu outstanding work apply will be skipped on {aDomU} as the imageinfo exadata-live-update-has-outstanding-work is - 'no'")
                    _outstanding_work_msg = 'no'
                    _is_elu_outstanding_work_applicable = False
                _elu_info['elu_version'] = _live_update_version
                _elu_info['elu_type'] = _applied_elu_type_on_domu
                _elu_info['elu_has_outstanding_work'] = _outstanding_work_msg
                return _ret, _current_qmr_image_version, _elu_info, _is_elu_outstanding_work_applicable

            else:
                # ELU not applied on this current node yet and outstanding work items output must be returned 'no exadata live update active'.
                self.mPatchLogInfo(
                     f"Elu outstanding work apply will be skipped on {aDomU} as the imageinfo exadata-live-update-has-outstanding-work is - 'no exadata live update active'")
                _elu_info['elu_version'] = _live_update_version
                _elu_info['elu_type'] = _applied_elu_type_on_domu
                _elu_info['elu_has_outstanding_work'] = 'no exadata live update active'
                return _ret, _current_qmr_image_version, _elu_info, _is_elu_outstanding_work_applicable

        except Exception:
            self.mPatchLogTrace(traceback.format_exc())
            _ret = IMAGE_VERSION_EMPTY_OR_INVALID
            _suggestion_msg = f'mGetExadataLiveUpdateDetails - Exception occured while fetching imageinfo command details on - {aDomU}.'
            self.mAddError(_ret, _suggestion_msg)
        finally:
            if _domu.mIsConnected():
                _domu.mDisconnect()
            self.mPatchLogInfo(f"mGetExadataLiveUpdateDetails - Apply Exadata live update outstanding work items - {_is_elu_outstanding_work_applicable}")

        return _ret, _current_qmr_image_version, _elu_info, _is_elu_outstanding_work_applicable

    def mGetInfrapatchExecutionValidator(self):
        return self.__infrapatch_execution_validator

    def mGetComputeNodeListSortedByAlias(self):
        return self.__computeNodeListSortedByAlias

    def mGetIdemPotencydata(self):
        return self.__idemPotencyData

    def mGetCellCount(self):
        if self.__additional_options and 'CellCountFromCP' in self.__additional_options[0]:
            return self.__additional_options[0]['CellCountFromCP']
        else:
            return 0


    def mGetComputeNodeListFromPayload(self):
        """
        Get the list of compute nodes from ecra metadata.
        If ecra metadata is empty get compute nodes from xml.
        Note: In Prod envs, ecra metadata is not empty
        """      
        _final_node_list = []
        _dom0_list_from_ecra = self.__computeNodeList
        if _dom0_list_from_ecra and len(_dom0_list_from_ecra) > 0:
            _final_node_list = _dom0_list_from_ecra
            self.mPatchLogInfo(f"Fetched computenodelist from ECRA : {json.dumps(_final_node_list, indent=4)}.")
        else:
            _final_node_list = [_dom0 for _dom0, _ in self.__cluctrl.mReturnDom0DomUPair()]
            self.mPatchLogInfo(f"Fetched computenodelist from xml : {json.dumps(_final_node_list, indent=4)}.")
        return _final_node_list

    '''
    List the VM for which AutonomousDb flag is Y
    '''
    def mSetAutonomousVMList(self):
         if self.__dom0domuDetails:
             _dom0_and_autonomous_domu_list = []
             _dom0_and_autonomous_domu_list_with_customer_hostnames = []
             _domu_list = []
             _domu_list_with_customer_hostnames = []

             for dom0HostnamefromEcra, domuHostListFromEcra in self.__dom0domuDetails.items():
                 for _, domUHostnameList in domuHostListFromEcra.items():
                     _domu_list = []
                     _domu_list_with_customer_hostnames = []
                     for _domuDetails in domUHostnameList:
                         if "AutonomousDb" in _domuDetails.keys():
                             _autonomous_db_flag = _domuDetails['AutonomousDb']
                             if _autonomous_db_flag and _autonomous_db_flag.lower() == 'y':
                                 if "domuNatHostname" in _domuDetails.keys():
                                     _domU = _domuDetails["domuNatHostname"]
                                     _domu_list.append(_domU)

                                 if "customerHostname" in _domuDetails.keys():
                                     _domu_customer_hostname = _domuDetails["customerHostname"]
                                     _domu_list_with_customer_hostnames.append(_domu_customer_hostname)

                 if _domu_list and len(_domu_list) > 0:
                     _dom0_and_autonomous_domu_list.append((dom0HostnamefromEcra, _domu_list))

                 if _domu_list_with_customer_hostnames and len(_domu_list_with_customer_hostnames) > 0:
                     _dom0_and_autonomous_domu_list_with_customer_hostnames.append((dom0HostnamefromEcra, _domu_list_with_customer_hostnames))

             if _dom0_and_autonomous_domu_list and len(_dom0_and_autonomous_domu_list) > 0:
                 self.__autonomousVMList = _dom0_and_autonomous_domu_list
                 self.mPatchLogInfo(
                     f"Final VM list with AutonomousDb flag enabled is {json.dumps(self.__autonomousVMList, indent=4)} ")
             else:
                  self.mPatchLogTrace("No VM found with AutonomousDb flag set to Y")

             if _dom0_and_autonomous_domu_list_with_customer_hostnames and len(_dom0_and_autonomous_domu_list_with_customer_hostnames) > 0:
                 self.__autonomousVMListWithCustomerHostnames = _dom0_and_autonomous_domu_list_with_customer_hostnames
                 self.mPatchLogInfo(
                     f"Final VM(CustomerHostname) list  with AutonomousDb flag enabled is {json.dumps(self.__autonomousVMListWithCustomerHostnames, indent=4)} ")

         else:
             self.mPatchLogInfo("No DomuDetails found from Payload")

    def mGetAutonomousVMList(self):
        return self.__autonomousVMList

    def mGetAutonomousVMListWithCustomerHostnames(self):
        return self.__autonomousVMListWithCustomerHostnames

    def isADBDImplicitPluginEnabled(self):
        _run_adbd_implicit_plugin = False
        if (PATCH_DOM0 in self.__target_type) and (self.mGetTask() in [TASK_PATCH, TASK_ROLLBACK]) and self.mGetOpStyle() == OP_STYLE_ROLLING:
            _autonomous_vm_list = self.mGetAutonomousVMList()
            if self.mGetAdditionalOptions() and 'isADBDHybridEnv' in self.mGetAdditionalOptions()[0] \
                and self.mGetAdditionalOptions()[0]['isADBDHybridEnv'].upper() == "YES":
                if _autonomous_vm_list and len(_autonomous_vm_list) < 1:
                    self.mPatchLogInfo("No Autonomous VM detected. ADBD Implicit Plugin will not run.")
                    _run_adbd_implicit_plugin =  False
                elif self.mGetAllArgs() and 'EnablePlugins' in self.mGetAllArgs().keys():
                    _enable_plugin_param = self.mGetAllArgs().get('EnablePlugins')
                    if _enable_plugin_param and _enable_plugin_param.lower() == 'yes':
                        self.mPatchLogInfo("ADBD Hybrid Env detected with Plugin Enabled. ADBD Implicit Plugin will run.")
                        _run_adbd_implicit_plugin =  True

        return _run_adbd_implicit_plugin

    def mGetClusterListForDom0(self, aDom0):
        """
        Retrieves the cluster list associated with the given dom0.

        Args:
            aDom0 (str): The name of the dom0.

        Returns:
            list: A list of cluster names associated with the dom0. If no association is found, an empty list is returned.
        """
        if self.mGetDom0ToClusterMapping():
            for _dom0, _cluster_list in self.mGetDom0ToClusterMapping():
                if _dom0 == aDom0:
                    return _cluster_list
        return []

    def mSetDom0ToClusterMapping(self):
        if self.__dom0domuDetails:
            _cluster_list_across_all_dom0 = []
            for dom0HostnamefromEcra, domuHostListFromEcra in self.__dom0domuDetails.items():
                _cluster_list = []
                for dom0HostnameFromEcraDict, domUHostnameList in domuHostListFromEcra.items():
                    for _domuDetails in domUHostnameList:
                        if "clusterName" in _domuDetails.keys():
                            _cluster_list.append(_domuDetails["clusterName"])
                _cluster_list_across_all_dom0.append((dom0HostnamefromEcra, _cluster_list))

            if _cluster_list_across_all_dom0 and len(_cluster_list_across_all_dom0) > 0:
                self.__dom0ToClusterList = _cluster_list_across_all_dom0

    '''
     mGetDom0ToClusterMapping output:
     [('sea201610exdd004.sea2xx2xx0051qf.adminsea2.oraclevcn.com',['cluster1', 'cluster2']),
        ('sea201610exdd005.sea2xx2xx0051qf.adminsea2.oraclevcn.com', ['cluster1','cluster3', 'cluster2']),
        ('sea201610exdd007.sea2xx2xx0051qf.adminsea2.oraclevcn.com', ['cluster3'])]

     Usage:
     _cluster_list_across_all_dom0 = self.mGetDom0ToClusterMapping()
     for _dom0,_cluster_list_for_one_dom0 in _cluster_list_across_all_dom0:
         print(_dom0)
         for _cluster in _cluster_list_for_one_dom0:
             print(_cluster)
    '''
    def mGetDom0ToClusterMapping(self):
        return self.__dom0ToClusterList

    def mSetClusterToGuestVMMapping(self):
        if self.__dom0domuDetails:
            _domu_list_across_all_clusters = []
            _cluster_list = []

            for dom0HostnamefromEcra, domuHostListFromEcra in self.__dom0domuDetails.items():
                for dom0HostnameFromEcraDict, domUHostnameList in domuHostListFromEcra.items():
                    _clusterName = None
                    _domU = None
                    _domUCustomerName = None
                    for _domuDetails in domUHostnameList:
                        if "clusterName" in _domuDetails.keys():
                            _clusterName = _domuDetails["clusterName"]
                        if "domuNatHostname" in _domuDetails.keys():
                            _domU = _domuDetails["domuNatHostname"]
                        if "customerHostname" in _domuDetails.keys():
                            _domUCustomerName = _domuDetails["customerHostname"]
                        #Store a mapping between domuNatHostname and domuCustomerHostName and vice versa to be used in plugin code or any other place
                        if _domU and _domUCustomerName:
                            self.__domuNatHostNameToCustomerHostName[_domU] = _domUCustomerName
                            self.__domuCustomerHostNameToNatHostName[_domUCustomerName] = _domU
                        if (_clusterName and _clusterName not in _cluster_list):
                            _domu_list_for_cluster = []
                            _cluster_list.append(_clusterName)
                            if _domU:
                                _domu_list_for_cluster.append(_domU)
                                _domu_list_across_all_clusters.append((_clusterName, _domu_list_for_cluster))
                        else:
                            for _clu, _domu_list in _domu_list_across_all_clusters:
                                if (_clu and _domU and (_clu == _clusterName)):
                                    _domu_list.append(_domU)


            if _domu_list_across_all_clusters and len(_domu_list_across_all_clusters) > 0:
                self.__clusterToGuestVMList = _domu_list_across_all_clusters

    def mSetClusterToGuestVMMappingWithNonZeroCPU(self):
        """
         This method sets cluster to vm mapping and are
         populated with customer hostnames that have VCPU
         set to non-zero
         This API also removes the VM which are non zero CPU but stopped by the customer from CP portal

         Sample Data for dom0domuDetails
         "scaqag01adm05.us.oracle.com": {
              "domuDetails": [
                  {
                     "customerHostname": "scaqag01dv0501m.us.oracle.com",
                     "domuNatHostname": "scaqag01dv0501m.us.oracle.com",
                     "clusterName": "scaqag01adm0506clu1",
                     "isSingleNodeVMCluster": "yes", ==> if SingleNodeCluster
                     "meterocpus": "4",
                     "AutonomousDb": "N",
                     "exaunitId": "41",
                     "vmState": "running",
                     "vmStateUpdateTime": "2024-01-19 11:12:36.958"
                  }
                ]
        """
        if self.__dom0domuDetails:
            _domu_list_across_all_clusters = []
            _cluster_list = []
            _domu_list_with_zero_vcpu_across_clusters = []
            _domu_list_with_non_zero_vcpu_per_cluster = []
            _clusters_with_single_vm = set()
            _clusters_with_vm_stopped = set()

            for dom0HostnamefromEcra, domuHostListFromEcra in self.__dom0domuDetails.items():
                for dom0HostnameFromEcraDict, domUHostnameList in domuHostListFromEcra.items():
                    _domuVcpuCount = None
                    _clusterName = None
                    _domUCustomerName = None
                    _isSingleNodeVMCluster = "no"
                    for _domuDetails in domUHostnameList:
                        _domuState = None
                        if "clusterName" in _domuDetails.keys():
                            _clusterName = _domuDetails["clusterName"]
                        if "customerHostname" in _domuDetails.keys():
                            _domUCustomerName = _domuDetails["customerHostname"]
                        if "meterocpus" in _domuDetails.keys():
                            _domuVcpuCount = _domuDetails["meterocpus"]
                        if "isSingleNodeVMCluster" in _domuDetails.keys():
                            _isSingleNodeVMCluster = _domuDetails["isSingleNodeVMCluster"]
                            if _isSingleNodeVMCluster == "yes":
                                self.mPatchLogInfo(
                                    f"Cluster {_clusterName} has a single VM {_domUCustomerName}. Adding it to single cluster set ")
                                _clusters_with_single_vm.add(_clusterName)
                        if _domuVcpuCount and int(_domuVcpuCount) < 1:
                            _domu_list_with_zero_vcpu_across_clusters.append(_domUCustomerName)
                        if (_clusterName and _clusterName not in _cluster_list):
                            _domu_list_for_cluster = []
                            _cluster_list.append(_clusterName)
                            if _domUCustomerName:
                                _domu_list_for_cluster.append(_domUCustomerName)
                                _domu_list_across_all_clusters.append((_clusterName, _domu_list_for_cluster))
                        else:
                            for _clu, _domu_list in _domu_list_across_all_clusters:
                                if (_clu and _domUCustomerName and (_clu == _clusterName)):
                                    _domu_list.append(_domUCustomerName)

            # This variable is populated only if ECRA metadata for singleNodeVM is not available
            _clusters_with_single_vm_from_exacloud = set()
            for _cluster_name, _domu_list in _domu_list_across_all_clusters:
                domu_customer_hostname_list_with_non_zero_vcpu_per_cluster = [_domu_natHostName for _domu_natHostName in
                                                                              _domu_list if
                                                                              _domu_natHostName not in _domu_list_with_zero_vcpu_across_clusters]
                #In case of zero vcpu clusters , vms are also shutdown so we want to aviud the cluster with vm list as empty as it creates issues in HA check
                # Sample : [('iad107422exd-dbaas-scaqan02XXX-clu01', ['scaqan02dv0501.us.oracle.com', 'scaqan02dv0601.us.oracle.com']), ('iad107422exd-dbaas-scaqan02XXX-clu02', [])]
                # The last cluster entry should not be there
                if domu_customer_hostname_list_with_non_zero_vcpu_per_cluster and len(domu_customer_hostname_list_with_non_zero_vcpu_per_cluster) > 0:
                    _domu_list_with_non_zero_vcpu_per_cluster.append(
                        (_cluster_name, domu_customer_hostname_list_with_non_zero_vcpu_per_cluster))

                #If VM's are stopped in a cluster , those clusters should not be treated as single VM clusters
                if len(_clusters_with_single_vm) < 1 and (_cluster_name not in _clusters_with_vm_stopped) and _domu_list and len(_domu_list) < 2 :
                    _clusters_with_single_vm_from_exacloud.add(_cluster_name)

            if _domu_list_with_non_zero_vcpu_per_cluster and len(_domu_list_with_non_zero_vcpu_per_cluster) > 0:
                self.__ClusterToVmMappingWithNonZeroVcpu = _domu_list_with_non_zero_vcpu_per_cluster
                self.mPatchLogInfo(
                    f"List of VMs with customer hostname and non-zero VCPU and not shut down from CP explicitly: {json.dumps(self.__ClusterToVmMappingWithNonZeroVcpu, indent=4)}")

            if _clusters_with_single_vm and len(_clusters_with_single_vm) > 0:
                self.mPatchLogInfo("Single VM Cluster populated from ECRA metadata")
                self.__ClustersWithSingleVM = _clusters_with_single_vm
            elif _clusters_with_single_vm_from_exacloud and len(_clusters_with_single_vm_from_exacloud) > 0:
                self.mPatchLogInfo("Single VM Cluster populated from Exacloud metadata")
                self.__ClustersWithSingleVM = _clusters_with_single_vm_from_exacloud


    '''
    mGetClusterToGuestVMMapping output:
    [('cluster1', ['sea201610exddu0404.sea2mvm01roce.adminsea2.oraclevcn.com','sea201610exddu0504.sea2mvm01roce.adminsea2.oraclevcn.com']),
    ('cluster2',['sea201610exddu0401.sea2xx2xx0051qf.adminsea2.oraclevcn.com','sea201610exddu0503.sea2xx2xx0051qf.adminsea2.oraclevcn.com']),
    ('cluster3',['sea201610exddu0501.sea2xx2xx0051qf.adminsea2.oraclevcn.com','sea201610exddu0703.sea2mvm01roce.adminsea2.oraclevcn.com'])]

    Usage:
    _clusterToVMList = self.mGetClusterToGuestVMMapping()
    for _cluster, _domu_list_for_one_cluster in _clusterToVMList:
        print(str(_cluster))
        for _domU in _domu_list_for_one_cluster:
            print(_domU)

    '''
    def mGetClusterToGuestVMMapping(self):
        return self.__clusterToGuestVMList

    def mGetClusterToVmMapWithNonZeroVcpu(self):
        return self.__ClusterToVmMappingWithNonZeroVcpu

    def mGetClustersWithSingleVM(self):
        return self.__ClustersWithSingleVM

    # Get DomuCustomerName to DomuNatHostName mapping
    def mGetDomUCustomerNameforDomuNatHostName(self, aDomuNatHostName):
        _domUCustomerName = None
        if aDomuNatHostName and self.__domuNatHostNameToCustomerHostName and (aDomuNatHostName in self.__domuNatHostNameToCustomerHostName.keys()):
            _domUCustomerName = self.__domuNatHostNameToCustomerHostName[aDomuNatHostName]
        if _domUCustomerName:
            return _domUCustomerName
        else:
            return aDomuNatHostName

    # Get DomuNatHostName to DomuCustomerName mapping
    def mGetDomUNatHostNameforDomuCustomerHostName(self, aDomuCustomerHostName):
        _domUNatHostName = None
        if aDomuCustomerHostName and self.__domuCustomerHostNameToNatHostName and (aDomuCustomerHostName in self.__domuCustomerHostNameToNatHostName.keys()):
            _domUNatHostName = self.__domuCustomerHostNameToNatHostName[aDomuCustomerHostName]
        if _domUNatHostName:
            return _domUNatHostName
        else:
            return aDomuCustomerHostName

    # Get list of DomuCustomerNames from a list of DomuNatHostNames
    def mGetDomUCustomerHostNamesforDomuNatHostNames(self, aDomuNatHostNameList):
        _domu_customer_hostname_list = []
        for _domu in aDomuNatHostNameList:
            _domu_customer_hostname = None
            _domu_customer_hostname = self.mGetDomUCustomerNameforDomuNatHostName(_domu)
            if _domu_customer_hostname:
                _domu_customer_hostname_list.append(_domu_customer_hostname)
        return _domu_customer_hostname_list

    # Get list of DomuNatHostNames from a list of DomuCustomerNames
    def mGetDomUNatHostNamesforDomuCustomerHostNames(self, aDomuCustomerHostNameList):
        _domu_nat_hostname_list = []
        for _domu in aDomuCustomerHostNameList:
            _domu_nat_hostname = None
            _domu_nat_hostname = self.mGetDomUNatHostNameforDomuCustomerHostName(_domu)
            if _domu_nat_hostname:
                _domu_nat_hostname_list.append(_domu_nat_hostname)
        return _domu_nat_hostname_list

    # Return both DomU customer and NAT hostname based on
    # the input dom0 customer or NAT hostname passed.
    def mReturnBothDomUNATCustomerHostNames(self, aDomuList):
        _domu_nat_and_customer_hostname_list = []
        for _domu in aDomuList:
            _domu_nat_hostname = None
            _domu_customer_hostname = None
            _domu_nat_hostname = self.mGetDomUNatHostNameforDomuCustomerHostName(_domu)
            _domu_customer_hostname = self.mGetDomUCustomerNameforDomuNatHostName(_domu)
            _domu_nat_and_customer_hostname_list.append(("Nat Hostname :" + str(_domu_nat_hostname), "Customer Hostname :" + str(_domu_customer_hostname)))
        return _domu_nat_and_customer_hostname_list

    # "ComputeNodeListByAlias":[{"slcs27adm01.us.oracle.com":"db-server1","slcs27adm02.us.oracle.com":"db-server2",}]
    # This list comes sorted from ECRA by dbserver alias , so no sorting logic here now in Exacloud
    def mSetComputeNodeListSortedByAlias(self):
        if self.__computeNodeListByAlias:
            for elem in self.__computeNodeListByAlias:
                for hostname, _ in elem.items():
                    self.__computeNodeListSortedByAlias.append(hostname)

    def mGetMVM(self):
        return self.__isMVM


    def mGetADBS(self):
        return self.__isADBS

    def mGetCustomizedDomUList(self):
        '''
         Getter method for mGetAllDomU()
        '''
        return self.__domu_customized_list

    def mSetCustomizedDomUList(self, aCustomizedDomUList):
        self.__domu_customized_list = aCustomizedDomUList
 
    def mGetCustomizedDom0List(self):
        '''
         Getter method for mGetAllDom0()
        '''
        return self.__dom0_customized_list

    def mSetKvmEnv(self):
        """
         Set kvm env type
        """
        if self.mGetCluControl().mIsKVM():
            self.__mListOfStatementsToPrint.append(("INFO","The environment is KVM"))
            self.__kvm_env = True
        else:
            self.__mListOfStatementsToPrint.append(("INFO", "OVM environment type"))
            self.__kvm_env = False

    def mIsKvmEnv(self):
        """
        Check for KVM or OVM.
        Return
          True  --> if kvm env,
          False --> otherwise
        """
        return self.__kvm_env

    def mSetExaCC(self):
        """
         Set ExaCC env type
        """
        if self.mGetCluControl().mIsOciEXACC():
            self.__mListOfStatementsToPrint.append(("INFO", "The environment is ExaCC"))
            self.__exacc = True
        else:
            self.__mListOfStatementsToPrint.append(("INFO", "The environment is not ExaCC"))
            self.__exacc = False

    def mIsExaCC(self):
        """
        Check for ExaCC.
        Return
          True  --> if ExaCC env,
          False --> otherwise
        """
        return self.__exacc

    def mGetIncludeNodeList(self):
        return self.__include_node_list

    def mSetIncludeNodeList(self, aList):
        self.__include_node_list = aList

    def mGetUserToNodeMappingToRunCrsCmds(self):
        '''
         Sample user to node json - 

         self.__user_to_node_mapping_to_run_crs_cmds = {
           "slcs27dv0301m.us.oracle.com": ['root'],
           "slcs27dv0401m.us.oracle.com": ['root', 'opc']
         }
        '''
        return self.__user_to_node_mapping_to_run_crs_cmds

    def mSetUserToNodeMappingToRunCrsCmds(self, aUserDict):
        self.__user_to_node_mapping_to_run_crs_cmds = aUserDict

    def mGetUserToNodeMappingToRunPlugins(self):
        '''
         Sample user to node json -

         self.__user_to_node_mapping_to_run_plugins = {
           "slcs27dv0301m.us.oracle.com": ['root'],
           "slcs27dv0401m.us.oracle.com": ['root', 'opc']
         }
        '''
        return self.__user_to_node_mapping_to_run_plugins

    def mSetUserToNodeMappingToRunPlugins(self, aUserDict):
        self.__user_to_node_mapping_to_run_plugins = aUserDict

    def mGetDbnuPluginBaseDirPrefix(self):
        return self.__dbnu_plugins_base_dir_prefix

    def mGetPatchmgrLogPathOnLaunchNode(self):
        return self.__patchmgr_log_path_on_launch_node

    def mSetPatchmgrLogPathOnLaunchNode(self, aPatchmgrLogPathOnLaunchNode):
        self.__patchmgr_log_path_on_launch_node = aPatchmgrLogPathOnLaunchNode

    def mGetUserDetailsBasedOnDomUhostname(self, aDomUHostname):
        """
         Given a hostname, this method returns the user which 
         is able to access this host. In case of Domu accesible
         both through root and opc user, root user is considered
         for performing validations.
        """
        _accessible_user = None
        _user_node_accessible_dict = self.mGetUserToNodeMappingToRunCrsCmds()
        if aDomUHostname in _user_node_accessible_dict:
            _users = _user_node_accessible_dict[aDomUHostname]
            if "root" in _users:
                _accessible_user = "root"
            elif "opc" in _users:
                _accessible_user = "opc"
        return _accessible_user

    def mGetUserDetailsBasedOnDomUhostnameToRunPlugins(self, aDomUHostname):
        """
         Given a hostname, this method returns the user which
         is able to access this host. In case of Domu accesible
         both through root and opc user, root user is considered
         to execute plugins.
        """
        _accessible_user = None
        _user_node_accessible_dict = self.mGetUserToNodeMappingToRunPlugins()
        if aDomUHostname in _user_node_accessible_dict:
            _users = _user_node_accessible_dict[aDomUHostname]
            if "root" in _users:
                _accessible_user = "root"
            elif "opc" in _users:
                _accessible_user = "opc"
        return _accessible_user

    def mGetCurrentLaunchNodeList(self):
        return self.__cur_launch_node_list

    def mSetCurrentLaunchNodeList(self, aCurLaunchNodeList):
        self.__cur_launch_node_list= aCurLaunchNodeList

    def mGetRackName(self):
        return self.__rack_name

    def mSetCellUpgradePassThroughFlag(self, aFlagValue):
        self.__cell_upgrade_passthrough = aFlagValue

    def mGetCurrentTargetType(self):
        return self.__current_target_type

    def mSetCurrentTargetType(self, aCurrentTargetType):
        self.__current_target_type = aCurrentTargetType

    def mGetJsonStatus(self):
        return self.__json_status

    def mGetFabric(self):
        return self.__fabric

    def mGetFabricId(self):
        return self.__fabric_id

    def mGetShutDownServices(self):
        return self.__shutdown_services

    def mGetStepList(self):
        return self.__step_list

    def mSetStepList(self, aStepList):
        self.__step_list = aStepList
    
    def mGetCluPatchCheck(self):
        return self.__clupatchcheck

    def mGetAllArgs(self):
        return self.__allArgs

    def mGetCluControl(self):
        return self.__cluctrl

    def mGetLogPath(self):
        return self.__log_path

    def mGetTargetTypes(self):
        if self.__target_type[0] in [ PATCH_SWITCH, PATCH_IBSWITCH ]:
            if self.mIsKvmEnv():
                self.__target_type = [PATCH_ROCESWITCH]
            else:
                self.__target_type = [PATCH_IBSWITCH]

        return self.__target_type

    def mGetTask(self):
        return self.__task

    def mGetOpStyle(self):
        return self.__op_style

    def mGetPayload(self):
        return self.__payload

    def mGetTargetEnv(self):
        return self.__target_env

    def mGetTargetVersion(self):
        return self.__target_version

    def mSetTargetVersion(self, aTargetVersion):
        self.__target_version = aTargetVersion

    def mGetBackUpMode(self):
        return self.__backup_mode

    def mGetFedRamp(self):
        return self.__fedramp

    def mGetPatchRequestRetried(self):
        return self.__patch_req_retry

    def mGetMasterReqId(self):
        """
        Method to return master request id. We are using this to tag in
        log_dir path for reading the patchmgr console in case of patch retry.
        """
        return self.__master_request_id

    def mGetAdditionalOptions(self):
        return self.__additional_options

    def mGetClusterId(self):
        return self.__cluster_id

    def mGetCellSwitchesZipFile(self):
        return self.__CellSwitchesZipFile

    def mGetDom0DomUPatchZipFile(self):
        return self.__dom0domUPatchZipFiles

    def mSetExadataEnvType(self, aExaDataEnvType):
        self.__exadata_env_type = aExaDataEnvType

    def mGetProcess(self):
        return self.__process

    def mGetListOfAdminSwitches(self):
        return self.__admin_switches_list

    def mSetListOfAdminSwitches(self, aListOfAdminSwitches):
        self.__admin_switches_list = aListOfAdminSwitches

    def mGetProcessCnsMonitor(self):
        return self.__process_cns_monitor

    def mGetExecutedTargets(self):
        return self.__executed_targets

    def isParallelShutdownofAllVMAcrossAllDom0Enabled(self):
        _enable_parallel_shutdown_of_all_vm_across_all_dom0 = mGetInfraPatchingConfigParam('enable_parallel_shutdown_of_all_vm_across_all_dom0')
        if _enable_parallel_shutdown_of_all_vm_across_all_dom0 and _enable_parallel_shutdown_of_all_vm_across_all_dom0.lower() in ['true']:
            ebLogInfo("Parallel shutdown of all VM across all dom0 is enabled.")
            return True
        else:
            ebLogInfo("Parallel shutdown of all VM across all dom0 is not enabled.")
            return False

    def mGetNodeSleepIntervalInSeconds(self):
        return int(mGetInfraPatchingConfigParam('node_sleep_interval_in_seconds'))
    
    def mGetNodeSleepMaxLimitInSeconds(self):
        return int(mGetInfraPatchingConfigParam('node_sleep_max_limit_in_seconds'))
    
    def mGetExadataPatchWorkingSpaceMB(self):
        return int(mGetInfraPatchingConfigParam('exadata_patch_working_space_mb'))
    
    def mGetExadataPatchGridHeartBeatTimeoutSec(self):
        return int(mGetInfraPatchingConfigParam('exadata_patch_grid_heartbeat_timeout_sec'))

    def mGetHeartBeatDetailsInCellAlertLogExecutionTimeoutSec(self):
        return int(mGetInfraPatchingConfigParam('heartbeat_details_in_cell_alert_log_execution_timeout_in_seconds'))
    
    def mGetSleepbetweenComputeTimeInSec(self):
        return int(mGetInfraPatchingConfigParam('exadata_sleep_between_computes_time_in_sec'))

    def mGetPluginConsoleReadCustomTimeoutSec(self):
        return int(mGetInfraPatchingConfigParam('plugin_console_read_custom_timeout_sec'))

    def mGetExacloudPatchmgr6To9CellNodesTimeoutMultiplier(self):
        return int(mGetInfraPatchingConfigParam('exacloud_patchmgr_6_to_9_cell_nodes_timeout_multiplier'))

    def mGetExacloudPatchmgr10OrMoreCellNodesTimeoutMultiplier(self):
        return int(mGetInfraPatchingConfigParam('exacloud_patchmgr_10_or_more_cell_nodes_timeout_multiplier'))

    def mGetExacloudPatchmgrRetryCleanupCheckMaxCounterValue(self):
        return int(mGetInfraPatchingConfigParam('exacloud_patchmgr_retry_cleanup_check_max_counter_value'))

    def mGetExadataPatchmgrConsoleReadTimeoutSec(self):
        return int(mGetInfraPatchingConfigParam('exadata_patchmgr_console_read_timeout_sec'))

    def mGetMaxRetriesForValidateImageChecksum(self):
        return int(mGetInfraPatchingConfigParam('max_retries_for_validate_image_checksum'))

    def mGetStaleMountCheckTimeoutSeconds(self):
        return int(mGetInfraPatchingConfigParam('stale_mount_check_timeout_in_seconds'))

    def mGetStaleMountThreadJoinTimeoutSeconds(self):
        return int(mGetInfraPatchingConfigParam('stale_mount_check_thread_join_timeout_in_seconds'))

    def mGetStaleMountMaxThreadExecutionTimeoutSeconds(self):
        return int(mGetInfraPatchingConfigParam('stale_mount_check_max_thread_execution_time_in_seconds'))

    def mCheckFileExistsOnRemoteNodesThreadJoinTimeoutSeconds(self):
        return int(mGetInfraPatchingConfigParam('remote_nodes_file_check_thread_join_timeout_in_seconds'))

    def mCheckFileExistsOnRemoteNodesMaxThreadExecutionTimeoutSeconds(self):
        return int(mGetInfraPatchingConfigParam('remote_nodes_file_check_max_thread_execution_time_in_seconds'))

    def mGetValidateRDSPingTimeoutInSeconds(self):
        return int(mGetInfraPatchingConfigParam('validate_rds_ping_timeout_in_seconds'))

    def mGetVmExecutionTimeoutInSeconds(self):
        return int(mGetInfraPatchingConfigParam('vm_execution_timeout_in_seconds'))

    def mGetValidateChecksumExecutionTimeoutInSeconds(self):
        return int(mGetInfraPatchingConfigParam('validate_checksum_execution_timeout_in_seconds'))

    def mGetValidateSshConnectivityExecutionTimeoutInSeconds(self):
        return int(mGetInfraPatchingConfigParam('ssh_connectivity_check_execution_timeout_in_seconds'))
    
    def mGetTimeoutForDom0DomuStartupInSeconds(self):
        return int(mGetInfraPatchingConfigParam('dom0_domu_startup_timeout_in_seconds'))
    
    def mGetTimeoutForDomuStartupInSeconds(self):
        return int(mGetInfraPatchingConfigParam('domu_startup_timeout_in_seconds'))

    def mGetDomUShutdownWaitTimeoutInSeconds(self):
        return int(mGetInfraPatchingConfigParam('domu_shutdown_wait_timeout_in_seconds'))

    def mGetVMStartUpMaxTimeoutInSeconds(self):
        return int(mGetInfraPatchingConfigParam('max_vm_startup_wait_time_in_seconds'))
 
    def mGetExadataPatchPurgeExecutionTimeoutInSeconds(self):
        return int(mGetInfraPatchingConfigParam('exadata_patch_purge_execution_timeout_in_seconds'))

    def mGetStartupCrsonDomUExecutionTimeoutInSeconds(self):
        return int(mGetInfraPatchingConfigParam('crs_startup_on_domu_execution_timeout_in_seconds'))

    def mGetValidateRootPartitionFreeSpaceCheckTimeoutInSeconds(self):
        return int(mGetInfraPatchingConfigParam('root_partition_free_space_check_timeout_in_seconds'))

    def mGetPatchmgrConsoleReadIntervalInSeconds(self):
        return int(mGetInfraPatchingConfigParam('patchmgr_console_read_interval_in_seconds'))

    def mGetDBHealthChecksWaitTimeInSeconds(self):
        return int(mGetInfraPatchingConfigParam('db_healthchecks_wait_time_in_seconds'))

    def mGetDbaascliTimeOutInSeconds(self):
        return int(mGetInfraPatchingConfigParam('dbaascli_timeout_in_seconds'))

    def mGetDBHealthChecksParallelExecutionWaitTimeInSeconds(self):
        return int(mGetInfraPatchingConfigParam('db_healthchecks_parallel_execution_wait_time_in_seconds'))

    def mGetMaxNumberofSshRetries(self):
        return int(mGetInfraPatchingConfigParam('max_number_of_ssh_retries'))

    def mGetRpmExcludeList(self):
        try:
            return mGetInfraPatchingConfigParam('system_consistiency_check_exclude_rpm_list')
        except:
            return {}

    def mGetTimeoutForDbmcliCellCliInSeconds(self):
        aTimeout = int(mGetInfraPatchingConfigParam('exadata_dbmcli_cellcli_timeout_in_seconds'))
        return aTimeout if aTimeout else 60

    def mIsMultiRackEnv(self):
        '''
         In case of spine switches present, environment
         is a multirack.
        '''
        _is_multirack_env = False
        _list = self.__cluctrl.mGetSwitches().mGetSwitchesDict()
        for _s in _list:
            if 'swdesc' in _s and 'spine' in _s['swdesc']:  # 'swdesc': 'Exadata spine Switch'
                self.mPatchLogInfo("Environment is multirack.")
                _is_multirack_env = True
                break
        return _is_multirack_env

    def mGetRevokeRoceswitchPasswdlessSshSettings(self):
        _revoke_roceswitch_passwdless_ssh = mGetInfraPatchingConfigParam('revoke_roceswitch_passwdless_ssh_settings')
        if _revoke_roceswitch_passwdless_ssh.lower() in ['false']:
            return False
        else:
            return True

    def mCheckIfAdminSwitchCanBePatched(self):
        """
         This method validates the additional options to check
         if switch patching flag is enabled or not.

         Patch the admin, spine, leaf, roce or IB switch patching
         based on the PatchSwitchType flag specified.
        """
        _patch_admin_switches = ""
        if (self.mGetAdditionalOptions() and 'PatchSwitchType' in (self.mGetAdditionalOptions()[0])):
            _patch_admin_switches = self.mGetAdditionalOptions()[0]['PatchSwitchType'].lower()

        # Since EXACS does not support Admin and Roce Switch patching,
        # PatchSwitchType option must be passed as "roce" so that the 
        # ibswitches can be patched.
        if not self.mIsExaCC():
            _patch_admin_switches = "roce"

        if _patch_admin_switches:
            ebLogInfo(f"_patch_admin_switches value from _patch_admin_switches is {str(_patch_admin_switches)}")
        return _patch_admin_switches

    def mGetPatchSwitchType(self):
        return self.__admin_switch_patch_apply

    def mSetPatchSwitchType(self, aPatchAdminSwitch):
        self.__admin_switch_patch_apply = aPatchAdminSwitch

    #This method is replaced by if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsStaleMountCheckEnabled')
    def mIsStaleMountCheckEnabled(self):
        """
        Default value for enable_stale_mount_check is True in infrapatching.conf and parameter stored in the below format.
        
        "enable_stale_mount_check": "True"
         
        True/False values are stored as string so string comparison is done to get whether stale_mount_check is 
        enabled or not.       
        """
        _enable_stale_mount_check = mGetInfraPatchingConfigParam('enable_stale_mount_check')
        if _enable_stale_mount_check:
            return _enable_stale_mount_check.lower() in ['true']
        else:
            return False

    # This flag is specific to current target type
    def mIsTimeStatsEnabled(self):
        return self.__collect_time_stats

    def mSetCollectTimeStatsFlag(self, aEnable = False):
        self.__collect_time_stats = aEnable

    def mMinRequiredDom0RootFsFreeSpaceinMB(self):
        return int(mGetInfraPatchingConfigParam('min_required_dom0_root_fs_free_space_in_mb'))

    def mMinRequiredDomURootFsFreeSpaceinMB(self):
        return int(mGetInfraPatchingConfigParam('min_required_domu_root_fs_free_space_in_mb'))
 
    def mMinRequiredCellRootFsFreeSpaceinMB(self):
        return int(mGetInfraPatchingConfigParam('min_required_cell_root_fs_free_space_in_mb'))

    def mGetSshKeysRemoveConfig(self):
        try:
            return mGetInfraPatchingConfigParam('remove_ssh_keys_from_hosts')
        except:
            return {}

    def mGetKeyScanFromTargetTypeNodeList(self):
        """
          This API returns the targetType for which keyscan
          command will be executed on the target node rather than the source node . This
          is because keyscan on  the source node was not returning data and hence known
          hosts file was not getting updated . Currently this is applicable only from
          switches
        """
        try:
            return mGetInfraPatchingConfigParam('keyscan_node_type_list')
        except:
            return []

    def mPerformPatchmgrExistenceCheck(self):
        _perform_patch_mgr_existence_check = True
        if self.mIsClusterLessUpgrade() or len(self.mGetExternalLaunchNode()) > 0:
            self.mPatchLogInfo("Patchmgr existence check will be skipped in case of clusterless patching or when \
                                external launch node is passed.")
            _perform_patch_mgr_existence_check = False
        return _perform_patch_mgr_existence_check

    def mGetCollectTimeStatsParam(self, aCurrentTargetType):
        """
        This method reads collect_current_targettype_time_stats parameter from infrapatching.conf
        Eg: For dom0 it is like  "collect_dom0_time_stats"
        By default it is True. Parameter for other targets is of the below format

            "collect_domu_time_stats": "True",
            "collect_dom0_time_stats": "True",
            "collect_cell_time_stats": "True",
            "collect_ibswitch_time_stats": "False",
            "collect_roceswitch_time_stats": "True"

        """
        _ret = False
        try:
            _collect_time_stats_str = f"collect_{aCurrentTargetType}_time_stats"
            self.mPatchLogInfo(f"Reading {_collect_time_stats_str} parameter from infrapatching.conf.")
            _enable_collect_time_stats = mGetInfraPatchingConfigParam(_collect_time_stats_str)
            if _enable_collect_time_stats:
                _ret =  _enable_collect_time_stats.lower() in ['true']

        except Exception as e:
            self.mPatchLogWarn(f"Exception {str(e)} occurred while reading collect_time_stats parameter.")
            self.mPatchLogTrace(traceback.format_exc())

        return _ret

    def mUpdatePatchStatus(self, aStatus, aStep, aComment=""):
        """
        Updates db to see changes in the progress bar.
        """

        if not self.mGetStepList():
            return False

        if aStep not in self.mGetStepList():
            if aStep+'_'+self.__current_target_type not in self.mGetStepList():
                self.mPatchLogWarn(f"Step {aStep} not in list")
                return False
            else:
                aStep = aStep+'_'+self.__current_target_type

        _reqobj = self.mGetCluControl().mGetRequestObj()
        if _reqobj:
            _db = ebGetDefaultDB()
            _pos = str(int((100.0 / len(self.mGetStepList()) * (self.mGetStepList().index(aStep)+1))))

            if aStep.startswith('patch_'):
                aStep = aStep.replace('patch_', self.__task+'_')
            if aComment == "":
                _reqobj.mSetStatusInfo(str(aStatus)+':'+_pos+':'+aStep)
            else:
                _reqobj.mSetStatusInfo(str(aStatus)+':'+_pos+':'+aStep+'-'+str(aComment))
            _db.mUpdateStatusRequest(_reqobj)
        return True

    # IBFabric/cluster Lock management
    def mBuildIBFabric(self):
        """
        Set an IBFabric object based on the information located in the db. We must have the
        db cluster_id in order to retrieve the information.
        """

        # If not cluster_id is provided, there is no way to know which fabric this cluster belongs to.
        # In this case, no locking will be used. This should never happen if using JSON input file
        # when doing a request for patching.

        if not self.__cluster_id:
            self.mPatchLogWarn("No cluster ID provided. Locking will not be managed during patch operation.")
            return False

        _db = ebGetDefaultDB()

        # Get cluster information located in db
        _row = _db.mCheckIBFabricClusterTable(aClusterID=self.__cluster_id)
        if not _row or len(_row) <= 1:
            self.mPatchLogWarn("Cluster ID not found or data is incomplete. Locking will not be managed during patch operation.")
            self.mPatchLogWarn(f"Cluster ID data: {_row}")
            return False

        # Based on fabric_id, get all the information related to that fabric
        _row = _db.mCheckIBFabricEntry(_row[1])

        if not _row or len(_row) <= 5:
            self.mPatchLogWarn("Fabric ID not found or data is incomplete. Locking will not be managed during patch operation.")
            self.mPatchLogWarn(f"Fabric ID data: {_row}")
            return False

        self.__fabric = IBFabricPatch(_row[0], _row[1], _row[2], _row[3], [], _row[4], _row[5])
        self.__fabric_id = self.__fabric.mGetIBFabricID()

        return True

    def mCreateStepList(self):
        """
        Creates the steps list that will allow to update the status request in
        the database.
        """

        _list = [STEP_SELECT_LAUNCH_NODE]
        _cell_switch_common_pre_steps = [STEP_FILTER_NODES, STEP_GATHER_NODE_DATA, STEP_PREP_ENV]
        _cell_switch_common_post_steps = [STEP_CLEAN_ENV, STEP_POSTCHECKS]
        _cell_dom0_shutdown_steps = [STEP_SHUTDOWN_VMS, STEP_STOP_CELL_SERVICES]

        if PATCH_CELL in self.__target_type or PATCH_ALL in self.__target_type:
            _list += [_step + '_' + PATCH_CELL for _step in _cell_switch_common_pre_steps]
            if self.__shutdown_services:
                _list += [_step + '_' + PATCH_CELL for _step in _cell_dom0_shutdown_steps]
            _list += PATCH_ONLY_CELL_STEP_LIST
            if self.__shutdown_services:
                _list += [STEP_START_VMS + '_' + PATCH_CELL]
            _list += [_step + '_' + PATCH_CELL for _step in _cell_switch_common_post_steps]

        if PATCH_DOM0 in self.__target_type or PATCH_ALL in self.__target_type:
            _list += [STEP_PREP_ENV + '_' + PATCH_DOM0]
            _list.append(STEP_FILTER_NODES)

            if (self.__task == TASK_PREREQ_CHECK or
                    self.__task == TASK_ROLLBACK_PREREQ_CHECK or
                    self.__task == TASK_BACKUP_IMAGE):
                _list.append(STEP_FILTER_NODES + '_' + PATCH_DOM0 + '_1')
                _list.append(STEP_RUN_PATCH_DOM0)
                _list.append(STEP_CLEAN_ENV + '_' + PATCH_DOM0 + '_1')

                _list.append(STEP_FILTER_NODES + '_' + PATCH_DOM0 + '_2')
                _list.append(STEP_RUN_PATCH_SECOND_DOM0)
                _list.append(STEP_CLEAN_ENV + '_' + PATCH_DOM0 + '_2')

            if self.__task == TASK_PATCH or self.__task == TASK_ROLLBACK:
                _list.append(STEP_FILTER_NODES + '_' + PATCH_DOM0)

                if not self.__shutdown_services:
                    # Need to shutdown the VMs from the includes dom0s list.
                    for _index in range(len(self.mGetCustomizedDom0List())):
                        if _index == 0:
                            _list.append(STEP_GATHER_NODE_DATA + '_' + PATCH_DOM0 + f'_[{_index + 1:d}]')
                            _list.append(STEP_RUN_PATCH_SECOND_DOM0 + f'_[{_index + 1:d}]')
                            _list.append(STEP_CLEAN_ENV + '_' + PATCH_DOM0 + f'_[{_index + 1:d}]')
                            _list.append(STEP_POSTCHECKS + '_' + PATCH_DOM0 + f'_[{_index + 1:d}]')
                        else:
                            _list.append(STEP_GATHER_NODE_DATA + '_' + PATCH_DOM0 + f'_[{_index + 1:d}]')
                            _list.append(STEP_RUN_PATCH_DOM0 + f'_[{_index + 1:d}]')
                            _list.append(STEP_CLEAN_ENV + '_' + PATCH_DOM0 + f'_[{_index + 1:d}]')
                            _list.append(STEP_POSTCHECKS + '_' + PATCH_DOM0 + f'_[{_index + 1:d}]')

                else:
                    _list.append(STEP_GATHER_NODE_DATA + '_' + PATCH_DOM0 + '_[1]')
                    _list.append(STEP_SHUTDOWN_VMS + '_' + PATCH_DOM0 + '_[1]')
                    _list.append(STEP_RUN_PATCH_SECOND_DOM0 + '_[1]')
                    _list.append(STEP_CLEAN_ENV + '_' + PATCH_DOM0 + '_[1]')
                    _list.append(STEP_POSTCHECKS + '_' + PATCH_DOM0 + '_[1]')

                    _list.append(STEP_GATHER_NODE_DATA + '_' + PATCH_DOM0 + '_[2]')
                    _list.append(STEP_SHUTDOWN_VMS + '_' + PATCH_DOM0 + '_[2]')
                    _list.append(STEP_RUN_PATCH_DOM0 + '_[2]')
                    _list.append(STEP_CLEAN_ENV + '_' + PATCH_DOM0 + '_[2]')
                    _list.append(STEP_POSTCHECKS + '_' + PATCH_DOM0 + '_[2]')

        if (PATCH_DOMU in self.__target_type or
                PATCH_ALL in self.__target_type):
            _list += [STEP_PREP_ENV + '_' + PATCH_DOMU]
            _list.append(STEP_FILTER_NODES)

            if (self.__task == TASK_PREREQ_CHECK or
                    self.__task == TASK_ROLLBACK_PREREQ_CHECK or
                    self.__task == TASK_BACKUP_IMAGE):
                _list.append(STEP_FILTER_NODES + '_' + PATCH_DOMU + '_1')
                _list.append(STEP_RUN_PATCH_DOMU)
                _list.append(STEP_CLEAN_ENV + '_' + PATCH_DOMU + '_1')

                _list.append(STEP_FILTER_NODES + '_' + PATCH_DOMU + '_2')
                _list.append(STEP_RUN_PATCH_SECOND_DOMU)
                _list.append(STEP_CLEAN_ENV + '_' + PATCH_DOMU + '_2')

            if (self.__task == TASK_PATCH or
                    self.__task == TASK_ROLLBACK):
                _list.append(STEP_FILTER_NODES + '_' + PATCH_DOMU)

                if not self.__shutdown_services:
                    # Need to shutdown the VMs from the includes dom0s list.
                    for _index in range(len(self.mGetCustomizedDomUList())):
                        if _index == 0:
                            _list.append(STEP_GATHER_NODE_DATA + '_' + PATCH_DOMU + f'_[{_index + 1:d}]')
                            _list.append(STEP_RUN_PATCH_SECOND_DOMU + f'_[{_index + 1:d}]')
                            _list.append(STEP_CLEAN_ENV + '_' + PATCH_DOMU + f'_[{_index + 1:d}]')
                            _list.append(STEP_POSTCHECKS + '_' + PATCH_DOMU + f'_[{_index + 1:d}]')
                        else:
                            _list.append(STEP_GATHER_NODE_DATA + '_' + PATCH_DOMU + f'_[{_index + 1:d}]')
                            _list.append(STEP_RUN_PATCH_DOMU + f'_[{_index + 1:d}]')
                            _list.append(STEP_CLEAN_ENV + '_' + PATCH_DOMU + f'_[{_index + 1:d}]')
                            _list.append(STEP_POSTCHECKS + '_' + PATCH_DOMU + f'_[{_index + 1:d}]')

                else:
                    _list.append(STEP_GATHER_NODE_DATA + '_' + PATCH_DOMU + '_[1]')
                    _list.append(STEP_SHUTDOWN_VMS + '_' + PATCH_DOMU + '_[1]')
                    _list.append(STEP_RUN_PATCH_SECOND_DOMU + '_[1]')
                    _list.append(STEP_CLEAN_ENV + '_' + PATCH_DOMU + '_[1]')
                    _list.append(STEP_POSTCHECKS + '_' + PATCH_DOMU + '_[1]')

                    _list.append(STEP_GATHER_NODE_DATA + '_' + PATCH_DOMU + '_[2]')
                    _list.append(STEP_SHUTDOWN_VMS + '_' + PATCH_DOMU + '_[2]')
                    _list.append(STEP_RUN_PATCH_DOMU + '_[2]')
                    _list.append(STEP_CLEAN_ENV + '_' + PATCH_DOMU + '_[2]')
                    _list.append(STEP_POSTCHECKS + '_' + PATCH_DOMU + '_[2]')

        for _target in [ PATCH_IBSWITCH, PATCH_SWITCH ]:
            if _target in self.__target_type or PATCH_ALL in self.__target_type:
                _list += [_step + '_' + _target for _step in _cell_switch_common_pre_steps]
                _list += PATCH_ONLY_SWITCH_STEP_LIST
                _list += [_step + '_' + _target for _step in _cell_switch_common_post_steps]

        _list.append(STEP_END)

        return _list

    def mGetCellList(self):
        """
        Returns the list of cell nodes in the cluster. In case of clusterless
        cabinet, we need to remove the nodes which are specified in the
        excluded list.
        """
        _final_node_list = []
        _final_node_list = self.mGetCellListFromEcra()
        if _final_node_list is None or len(_final_node_list) < 1:
            _final_node_list = list(self.__cluctrl.mReturnCellNodes().keys())
            self.mPatchLogInfo(f"ECRA StorageNodeList is Empty. Returning {_final_node_list} from cluster XML for Cell from mGetCellList.")
        else:
            self.mPatchLogInfo(f"ECRA StorageNodeList from ECRA metadata is {_final_node_list} from mGetCellList.")

        return _final_node_list

    def mGetCustomizedCellList(self):
        """
        If includeNodeList has nodes specified in AdditionalOptions of payload,
        returns the nodes from includeNodeList
        otherwise returns all the cells from cluster xml(same as mGetCellList)

        """
        _final_node_list = []
        if len(self.mGetIncludeNodeList()) > 0 and PATCH_CELL in self.__target_type:
            _final_node_list = self.mGetIncludeNodeList()
            self.mPatchLogInfo(f"Returning IncludeNodelist {_final_node_list} for Cell from mGetCustomizedCellList .")
            return _final_node_list

        # Both Clusterless and Normal Patching for cell is done with respect to the nodes from ECRA metadata and not from XML

        _final_node_list = self.mGetCellListFromEcra()
        if _final_node_list is None or len(_final_node_list) < 1:
            _final_node_list = list(self.__cluctrl.mReturnCellNodes().keys())
            self.mPatchLogInfo(f"ECRA StorageNodeList is Empty. Returning {_final_node_list} from cluster XML for Cell from mGetCustomizedCellList.")
        else:
            self.mPatchLogInfo(f"ECRA StorageNodeList from ECRA metadata is  {_final_node_list}  from mGetCustomizedCellList.")

        return _final_node_list

    def mIsClusterLessUpgrade(self):
        """
        Check whether user requested for upgrading nodes from compute or cell
        cabinet. It returns:
          True: if user requested to upgrade nodes from cabinet
          False: Otherwise
        """
        if self.__additional_options and 'ClusterLess' in self.__additional_options[0] \
           and self.__additional_options[0]['ClusterLess'].upper() == "YES":
            return True
        else:
            return False

    def mGetControlPlaneRequestID(self):
        """
        Return Control Plane Request Id
        """
        if self.__additional_options and 'FpCrId' in self.__additional_options[0]:
            return self.__additional_options[0]['FpCrId']
        else:
            return None

    def mGetCabinetLaunchNode(self):
        """
        Get launch node which is passed by ecra input paylaod.
        Return value:
            Raise Exception --> If launch node not specified in the exacloud payload
            Return Launch Node, it could be string or List.
        """
        if self.__additional_options and 'LaunchNode' in self.__additional_options[0] \
           and not self.__additional_options[0]['LaunchNode']:
            _errmsg = "Unable to set launch node for clusterless upgrade"
            raise Exception(_errmsg)
        else:
            return self.__additional_options[0]['LaunchNode']

    def mGetLaunchNodeType(self):
        _launch_node_type=None
        if self.__additional_options and 'LaunchNodeType' in self.__additional_options[0] \
                and self.__additional_options[0]['LaunchNodeType']:
            _launch_node_type = self.__additional_options[0]['LaunchNodeType']
        return _launch_node_type


    def mGetExternalLaunchNode(self):
        """
        Returns CPS as the launchnode for EXACC when enable_cps_as_launch_node_for_domu
        is set to true on infrapatch conf file. In EXACC , CPS will be the only external
        launch node (or) we fallback to option of reading launch node from exacloud payload

        Get launch node which is passed by ecra input paylaod.
        Return value:
             In case of EXACC, if enable_cps_as_launch_node_for_domu is set to true on
             infrapatch conf file and only for domu patch operation it returns localhost
             as the launchnode

             (or) it will choose an accessible launchnode from the list of launch node(s) in
             exacloud payload

             (or) if launch node is not there in the exacloud payload or if the launch node(s)
             passed is not accessible it will return empty list
        """
        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
            return ['localhost']
        '''
        Launch node will be chosen only in the first invocation of this method,
        in subsequesnt invocation it will return the launch node which was chosen
        in the first invocation.
        '''
        if self.__external_launch_node:
            self.mPatchLogInfo(f"launch node returned: {str(self.__external_launch_node)}")
            return [ self.__external_launch_node ]

        if self.__additional_options and 'LaunchNode' in self.__additional_options[0] \
                and self.__additional_options[0]['LaunchNode']:
            if self.__additional_options[0]['LaunchNode'] == 'none':
                return []
            else:
                launchNodes = self.__additional_options[0]['LaunchNode']
                launchNodesList = launchNodes.split(",")
                '''
                Launch node will be passed in the additional options section
                Example:
                LaunchNode: "ecra-exacsdev9,ecra-exacsdev7"
                '''
                validNodes = []
                '''
                Randomly choose an accessible launch node  from the 
                list of launch node(s) passed, so that we have some distribution of 
                patchmgr operations 
                '''
                _launchNodeHealth = False
                while len(launchNodesList) > 0:
                    if len(launchNodesList) == 1:
                        _node = launchNodesList[0]
                    else:
                        _node = random.SystemRandom().choice(launchNodesList)
                    if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomuOrClusterless'):
                        _launchNodeHealth =  self.__clupatchcheck.mPingNode(_node, aSshUser='opc')
                    else:
                        _launchNodeHealth =  self.__clupatchcheck.mPingNode(_node)

                    if _launchNodeHealth:
                        validNodes.append(_node)
                        self.__external_launch_node = _node
                        break
                    else:
                        launchNodesList.remove(_node)
                if len(validNodes) > 0:
                    self.mPatchLogInfo(f"Chosen launch node: {str(validNodes)}")
                else:
                    self.mPatchLogWarn("No valid external launch nodes passed")
                return validNodes
        else:
            return []

    def mGetExaunitId(self):
        """
        Get Exaunit id from input payload.
        Return value:
            Return None --> If Exaunit id not specified in the exacloud payload
            Return Exaunit Id if specified
        """
        if self.__additional_options and 'exaunitId' in self.__additional_options[0] \
           and self.__additional_options[0]['exaunitId']:
            return self.__additional_options[0]['exaunitId']
        else:
            return None

    def mGetExaOcid(self):
        """
        Get ExaOcid from input payload.
        Return value:
            Return None --> --> If exaOcid not specified in the exacloud payload
            Return exaOcid if specified
        """
        if self.__additional_options and 'exaOcid' in self.__additional_options[0] \
           and self.__additional_options[0]['exaOcid']:
            return self.__additional_options[0]['exaOcid']
        else:
            return None

    def mIsExaSplice(self):
        """
        Check exasplice upgrade indicated or not.
        Return value:
            True  --> If exasplice or monthly upgrade is specified.
            False --> If exasplice is not specified.
        """
        if self.__additional_options and 'exasplice' in self.__additional_options[0] \
           and self.__additional_options[0]['exasplice']:
            if self.__additional_options[0]['exasplice'].lower() == 'yes':
                return True
        else:
            return False

    def mGetExcludedList(self):
        """
        Get the list of nodes which are passed by ecra input paylaod.
        Return value:
            [] --> If exclude list is empty
            Return ExcludeList if specified in the payload.
        """
        if self.__additional_options and 'ExcludedNodeList' in self.__additional_options[0] \
           and not self.__additional_options[0]['ExcludedNodeList']:
            self.mPatchLogWarn("Exclude list is empty in exacloud payload")
            return []
        else:
            return self.__additional_options[0]['ExcludedNodeList']

    def mReturnPatchingDom0DomUList(self):
        """
        Returns a list of dom0,DomU tuples. In case of clusterless cabinet, we need to
        remove the nodes which are specified in the excluded list.
        """
        if self.mIsClusterLessUpgrade():
            # Remove excluded nodes from the actual node list
            _orig_node_list = self.__cluctrl.mReturnDom0DomUPair(aIsClusterLessXML=True)
            _excluded_node_list = list(self.mGetExcludedList())
            return list(filter(lambda x: x[0] not in _excluded_node_list,_orig_node_list))
        else:
            return self.__cluctrl.mReturnDom0DomUPair()

    def mSetPatchingDom0DomUListFromEcra(self):
            """
             This method sets
               - Dom0 Domu pair from ecra, domu list are
                 populated using NAT hostnames.
               - Dom0 DomU pair with zero CPU cores and domu 
                 list are populated using customer hostnames.
            """
            _dom0_and_domu_list = []
            _domu_list_across_all_dom0 = []
            _domu_list = []
            _dom0_and_domu_list_customer_hostname_with_non_zero_vcpu = []
            _domu_list_customer_hostname = []

            if self.__dom0domuDetails and not self.mIsClusterLessUpgrade():
                for dom0HostnamefromEcra, domuHostListFromEcra in self.__dom0domuDetails.items():
                    for dom0HostnameFromEcraDict, domUHostnameList in domuHostListFromEcra.items():
                        _domu_list = []
                        _domu_list_customer_hostname = []
                        for domUHostnamingConvention in domUHostnameList:
                            if "domuNatHostname" in domUHostnamingConvention.keys():
                                _domu_list.append(domUHostnamingConvention["domuNatHostname"])
                                _domu_list_across_all_dom0.append(domUHostnamingConvention["domuNatHostname"])

                            # Get the list of VMs with customer hostnames zero Vcpu cores set
                            if "customerHostname" in domUHostnamingConvention.keys():
                                if "meterocpus" in domUHostnamingConvention.keys() and int(domUHostnamingConvention["meterocpus"]) > 0:
                                    _domu_list_customer_hostname.append(domUHostnamingConvention["customerHostname"])

                    # dom0 to domu list with Nat hostbname map.
                    _dom0_and_domu_list.append((dom0HostnamefromEcra, _domu_list))

                    # Dom0 to domu list customer hostname map with non-zero VCPU
                    _dom0_and_domu_list_customer_hostname_with_non_zero_vcpu.append((dom0HostnamefromEcra, _domu_list_customer_hostname))

            if _domu_list_across_all_dom0 and len(_domu_list_across_all_dom0) > 0:
                self.mPatchLogInfo("Fetched Dom0 and Domu pair from ECRA.")
            else:
                self.mPatchLogInfo("Fetching Dom0 and Domu pair from Cluster XML.")
                '''
                 mReturnPatchingDom0DomUList method return example -
                  ['slcs27adm03.us.oracle.com', 'slcs27dv0305m.us.oracle.com'], 
                   ['slcs27adm04.us.oracle.com', 'slcs27dv0405m.us.oracle.com']
                '''
                for _dom0, _domu in self.mReturnPatchingDom0DomUList():
                    _domu_list = []
                    _domu_list.append(_domu)
                    _dom0_and_domu_list.append((_dom0, _domu_list))
    
            self.__patching_dom0_and_domu_list_from_ecra = _dom0_and_domu_list
            # _dom0_and_domu_list_customer_hostname_with_non_zero_vcpu will be empty if fetched from
            # cluster xml
            self.__dom0_and_domu_customer_hostname_list_from_ecra_with_non_zero_vcpu = _dom0_and_domu_list_customer_hostname_with_non_zero_vcpu

    def mReturnPatchingDom0DomUListFromEcra(self):
        """
         This method refers ecra metadata information to populate list of all VMs running
         on the Dom0s in case of a multi VM environment.

         Example of the input json details that contains dom0 DomU details.

         initialDom0DomUJson = {
             "sea201610exdd004.sea2xx2xx0051qf.adminsea2.oraclevcn.com": {
                 "domuDetails": [
                     {
                         "customerHostname": "clu04-gljjf3.clientmvm02.vcnmvmx9m.oraclevcn.com",
                         "domuNatHostname": "sea201610exddu0404.sea2mvm01roce.adminsea2.oraclevcn.com"
                     },
                     {
                         "customerHostname": "clu01-nid7s1.clientmvmx9m.vcnmvmx9m.oraclevcn.com",
                         "domuNatHostname": "sea201610exddu0401.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
                     }
                 ]
             },
             "sea201610exdd007.sea2xx2xx0051qf.adminsea2.oraclevcn.com": {
                 "domuDetails": [
                     {
                         "customerHostname": "clu04-gljjf1.clientmvm02.vcnmvmx9m.oraclevcn.com",
                         "domuNatHostname": "sea201610exddu0704.sea2mvm01roce.adminsea2.oraclevcn.com"
                     }
                 ]
             }
         }

         Skip CLusterless for ECRA data.
         Clusterless is handled from the existing mReturnPatchingDom0DomUList in the else loop.

         Example of a final Dom0 DomU pair obtained :

         {
            "sea201610exdd004.sea2xx2xx0051qf.adminsea2.oraclevcn.com":[
               "sea201610exddu0404.sea2mvm01roce.adminsea2.oraclevcn.com",
               "sea201610exddu0401.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
            ],
            "sea201610exdd007.sea2xx2xx0051qf.adminsea2.oraclevcn.com":[
              "sea201610exddu0704.sea2mvm01roce.adminsea2.oraclevcn.com"
            ]
         }
        """
        if  self.__patching_dom0_and_domu_list_from_ecra and len(self.__patching_dom0_and_domu_list_from_ecra) > 0:
            return self.__patching_dom0_and_domu_list_from_ecra
        else:
            self.mSetPatchingDom0DomUListFromEcra()
            return self.__patching_dom0_and_domu_list_from_ecra

    def mGetDom0DomUCustomerNameMapWithNoZeroVcpu(self):
        """
         This method refers ecra metadata information to populate list of all VMs running
         on the Dom0s in case of a multi VM environment and return the list of 0 VCPU core
         VMs with customer hostname.
        """
        return self.__dom0_and_domu_customer_hostname_list_from_ecra_with_non_zero_vcpu

    '''
    Currently this function sorts Dom0 names by Domu customer Name
    '''
    def mSortDom0ByDomuCustomerHostName(self):
        _dom0_and_domu_list = []
        _domu_customerName_list_across_all_dom0 = []
        # This list of dom0s contains dom0 sorted by domu customerHostName
        _dom0s = []

        for dom0HostnamefromEcra, domuHostListFromEcra in self.__dom0domuDetails.items():
            for dom0HostnameFromEcraDict, domUHostnameList in domuHostListFromEcra.items():
                _domu_customerName_list = []
                for domUHostnamingConvention in domUHostnameList:
                    if "customerHostname" in domUHostnamingConvention.keys():
                        _domu_customerName_list.append(domUHostnamingConvention["customerHostname"])
                        _domu_customerName_list_across_all_dom0.append(domUHostnamingConvention["customerHostname"])
            _dom0_and_domu_list.append((dom0HostnamefromEcra, _domu_customerName_list))

        # Step2: Sort domUs based on length and then lexical/ascending order.
        _domu_customerName_list_across_all_dom0.sort(key=lambda item: (len(item), item))
        if _domu_customerName_list_across_all_dom0:
            self.mPatchLogInfo(
                f"Entire DomU List sorted by customer Name {str(_domu_customerName_list_across_all_dom0)}")

        # Step3: Create dom0 and domU pair based on domU sorting.
        for _domu in _domu_customerName_list_across_all_dom0:
            for _dom0_hostname, _dom0s_domU in _dom0_and_domu_list:
                if _domu in _dom0s_domU and _dom0_hostname not in _dom0s:
                    _dom0s.append(_dom0_hostname)
                    break

        return _dom0s

    def mGetDom0ListFromEcra(self):
        """
         This method fetches dom0 list details based on the sorting order for the domu.
         Should be supported for both single VM and multiVM
         [
          "sea201610exdd004.sea2xx2xx0051qf.adminsea2.oraclevcn.com",
          "sea201610exdd005.sea2xx2xx0051qf.adminsea2.oraclevcn.com",
          "sea201610exdd007.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
         ],
        """
        _dom0List = []
        if self.__dom0domuDetails:
            _dom0List = self.mSortDom0ByDomuCustomerHostName()
            if _dom0List:
                self.mPatchLogInfo(
                    f"Final Dom0 List after sorting by Domu CustomerHostName {json.dumps(_dom0List, indent=4)} ")
        if _dom0List and len(_dom0List) < 1 and self.__computeNodeList and len(self.__computeNodeList) > 0:
            self.mPatchLogInfo(f"Final Dom0 List from  self.__computeNodeList {json.dumps(_dom0List, indent=4)} ")
            _dom0List = self.__computeNodeList

        """
        In single vm cluster scenario when one of the dom0 does not have any vms in it, reading dom0 details from Dom0domUDetails would not list all the dom0s
        So will be adding dom0 details from __computeNodeList
        
            "ComputeNodeList": [
                "sea201832exdd001.sea2xx2xx0071qf.adminsea2.oraclevcn.com",
                "sea201832exdd002.sea2xx2xx0071qf.adminsea2.oraclevcn.com"
            ],
            "ComputeNodeListByAlias": [
            {
              "sea201832exdd001.sea2xx2xx0071qf.adminsea2.oraclevcn.com": "dbserver-1",
              "sea201832exdd002.sea2xx2xx0071qf.adminsea2.oraclevcn.com": "dbserver-2"
            }
            ],
            "isMVM": "no",
            "StorageNodeList": [
                "sea201831exdcl02.sea2xx2xx0071qf.adminsea2.oraclevcn.com",
                "sea201831exdcl03.sea2xx2xx0071qf.adminsea2.oraclevcn.com",
                "sea201831exdcl01.sea2xx2xx0071qf.adminsea2.oraclevcn.com"
                ],
            "Dom0domUDetails": {
                "sea201832exdd001.sea2xx2xx0071qf.adminsea2.oraclevcn.com": {
                  "domuDetails": [
                    {
                      "customerHostname": "x10msn-nyoh11.dbqadataad2s1.dbqavcn.oraclevcn.com",
                      "domuNatHostname": "sea201832exddu0104.sea2mvm01roce.adminsea2.oraclevcn.com",
                      "clusterName": "sea2-d2-cl3-acac77f5-ceec-48ae-9483-52e6d2805999-clu04",
                      "AutonomousDb": "N"
                    }
                  ]
                }
            }
        """
        if self.__computeNodeList and len(self.__computeNodeList) > 0 and len(_dom0List) < len(self.__computeNodeList):
            _dom0List = _dom0List + [x for x in self.__computeNodeList if x not in _dom0List]
            self.mPatchLogInfo(
                f"Final Dom0 List from mGetDom0ListFromEcra after adding nodes from self.__computeNodeList {json.dumps(_dom0List, indent=4)} ")
        return _dom0List

    def mGetCellListFromEcra(self):
        """
         This method fetches dom0 list details 
         from ecra metadata in the below format.
         
         [
          "sea201606exdcl06.sea2xx2xx0051qf.adminsea2.oraclevcn.com", 
          "sea201606exdcl04.sea2xx2xx0051qf.adminsea2.oraclevcn.com", 
          "sea201606exdcl05.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
         ]
        """
        return self.__storageNodeList

    def mGetDom0List(self):
        """
          Returns the list of dom0s nodes. In case of clusterless cabinet, we need to
          remove the nodes which are specified in the excluded list.

          In case of Include node list, input list passed are the list of dom0s to be
          patched.
        """
        _final_node_list = []

        # The MVM variable will not be set for EXACC
        if self.mGetMVM() and self.mGetMVM() == "yes":
            self.mPatchLogTrace("Fetched Dom0 List for Multi VM Sorted By Alias")
            _dom0_list_from_ecra = self.mGetComputeNodeListSortedByAlias()
        else:
            _dom0_list_from_ecra = self.mGetDom0ListFromEcra()

        if len(self.mGetIncludeNodeList()) > 0 and PATCH_DOM0 in self.__target_type:
            _final_node_list = self.mGetIncludeNodeList()
        elif self.mIsClusterLessUpgrade():
            _final_node_list = self.__computeNodeList
        elif _dom0_list_from_ecra and len(_dom0_list_from_ecra) > 0:
            _final_node_list = _dom0_list_from_ecra
            self.mPatchLogInfo(f"Fetched Dom0 list from ECRA : {json.dumps(_final_node_list, indent=4)}.")
        else:
            _final_node_list = list({_dom0 for _dom0, _ in self.__cluctrl.mReturnDom0DomUPair()})
            self.mPatchLogInfo(f"Fetched Dom0 list from XML : {json.dumps(_final_node_list, indent=4)}.")
        return _final_node_list

    def mGetDom0ListFromXml(self):
        """
        Returns the list of dom0s nodes. In case of clusterless cabinet, we need to
        remove the nodes which are specified in the excluded list.
        """
        if self.mIsClusterLessUpgrade():
            _final_node_list = []
            # Remove excluded nodes from the actual node list
            _orig_node_list = [_dom0 for _dom0, _ in self.__cluctrl.mReturnDom0DomUPair(aIsClusterLessXML=True)]
            _excluded_node_list = list(self.mGetExcludedList())
            _final_node_list = [_node for _node in _orig_node_list if _node not in _excluded_node_list]
            return _final_node_list
        else:
            return [_dom0 for _dom0, _ in self.__cluctrl.mReturnDom0DomUPair()]

    def mGetDomUList(self, aDom0=None, aFromXmList=False):
        """
          Returns the list of domUs. if aDom0 is provided, only return the domUs on that dom0

          In case of Include node list, input list passed are the list of dom0s to be
          patched.
        """
        _domUs = []
        _cmd = ""

        if self.mIsKvmEnv():
            '''
            sed added at the end to remove empty line
            Example:
              # virsh list|tail -n+3|awk '{print $2}' | sed '/^$/d'
                scaqan03dv0208.us.oracle.com
                scaqan03dv0204.us.oracle.com
                scaqan03dv0201.us.oracle.com
                scaqan03dv0202.us.oracle.com
                scaqan03dv0203.us.oracle.com
            '''
            _cmd = "virsh list| grep -i 'running' | awk '{print $2}' | sed '/^$/d'"
        else:
            _cmd = "xm list|tail -n+3|awk '{print $1}'"

        if aDom0:
            if not aFromXmList:
                for _dom0, _domU in self.mReturnPatchingDom0DomUList():
                    if _dom0 == aDom0:
                        _domUs = _domU
                        if type(_domUs) not in (list,set,tuple):
                            _domUs = [_domUs]
                        break
            else:
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=aDom0)
                _in, _out, _err = _node.mExecuteCmd(_cmd)
                _output = _out.readlines()
                if _output:
                    for _line in _output:
                        _domUs.append(_line.strip())
                _node.mDisconnect()
        else:
            if not aFromXmList:
                _domUs = [_domU for _, _domU in self.mReturnPatchingDom0DomUList()]
            else:
                for _dom0, _ in self.mReturnPatchingDom0DomUList():
                    _node = exaBoxNode(get_gcontext())
                    _node.mConnect(aHost=_dom0)
                    _in, _out, _err = _node.mExecuteCmd(_cmd)
                    _output = _out.readlines()
                    if _output:
                        for _line in _output:

                            _domUs.append(_line.strip())
                    _node.mDisconnect()

        if len(self.mGetIncludeNodeList()) > 0 and PATCH_DOMU in self.__target_type:
            _domUs = self.mGetIncludeNodeList()

        return _domUs

    def mGetDomUListFromXml(self, aDom0=None, aFromXmList=False):
        """
        Returns the list of domUs. if aDom0 is provided, only return the domUs on that dom0
        """
        _domUs = []
        _cmd = ""

        # if clusterless patching, no domUs should be running
        if self.mIsClusterLessUpgrade():
            return _domUs

        if self.mIsKvmEnv():
            '''
            sed added at the end to remove empty line
            Example:
              # virsh list|tail -n+3|awk '{print $2}' | sed '/^$/d'
                scaqan03dv0208.us.oracle.com
                scaqan03dv0204.us.oracle.com
                scaqan03dv0201.us.oracle.com
                scaqan03dv0202.us.oracle.com
                scaqan03dv0203.us.oracle.com
            '''
            _cmd = "virsh list| grep -i 'running' | awk '{print $2}' | sed '/^$/d'"
        else:
            _cmd = "xm list|tail -n+3|awk '{print $1}'"

        if aDom0:
            if not aFromXmList:
                for _dom0, _domU in self.mReturnPatchingDom0DomUList():
                    if _dom0 == aDom0:
                        _domUs = _domU
                        if type(_domUs) not in (list,set,tuple):
                            _domUs = [_domUs]
                        break
            else:
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=aDom0)
                _in, _out, _err = _node.mExecuteCmd(_cmd)
                _output = _out.readlines()
                if _output:
                    for _line in _output:
                        _domUs.append(_line.strip())
                _node.mDisconnect()
        else:
            if not aFromXmList:
                _domUs = [_domU for _, _domU in self.mReturnPatchingDom0DomUList()]
            else:
                for _dom0, _ in self.mReturnPatchingDom0DomUList():
                    _node = exaBoxNode(get_gcontext())
                    _node.mConnect(aHost=_dom0)
                    _in, _out, _err = _node.mExecuteCmd(_cmd)
                    _output = _out.readlines()
                    if _output:
                        for _line in _output:
                            _domUs.append(_line.strip())
                    _node.mDisconnect()
        return _domUs

    def mGetSwitchList(self):
        """
        Returns the list of all the ibswitches.
        """
        # Connect to exacloud DB and fetch the list of switches 
        # only in case of a non Roce Environment.
        if self.__fabric and not self.mIsKvmEnv():
            _db = ebGetDefaultDB()
            _list = _db.mGetListOfIBFabricIBSwitches(self.mGetFabricId())
            if _list:
                return [str(_row[2]) for _row in _list]

        if self.mIsKvmEnv():
            if self.mGetPatchSwitchType().lower() in [ "rocespine", "all" ]:
                # The following call will get the ROCE switches detail
                # and also set 'admin' user to login to ROCE switches.
                return list(set(self.mGetCluControl().mReturnSwitches(True, True, aEnableSpineSwitchPatching=True)))
            elif self.mGetPatchSwitchType().lower() in [ "roce" ]:
                return list(set(self.mGetCluControl().mReturnSwitches(True, True)))
            elif self.mGetPatchSwitchType().lower() in [ "spine" ]:
                return list(set(self.mGetCluControl().mReturnandConnectRoceSpineSwitches()))
        else:
            return list(set(self.mGetCluControl().mReturnSwitches(True)))

    def mSetPatchOperationStyle(self):
        """
        Decides which type of operation style will be used: rolling/non-rolling
        """

        # Patchmgr support only non-rolling style in case of exasplice on dom0 
        # nodes. So, change to non-rolling if auto or rolling specified by user.

        # Cells should be patched in rolling always in case of monthly patching
        # because customer might try VM start/stop operations and those
        # operations would fail if cell goes in non-rolling (because VMs
        # are brought down).
        # TODO :This can be relaxed to use non-rolling once we get the rebootless cell monthly patching

        if self.mIsExaSplice():
            if PATCH_DOM0 in self.__target_type:
                self.__op_style = OP_STYLE_NON_ROLLING
            elif  PATCH_CELL in self.__target_type:
                self.__op_style = OP_STYLE_ROLLING
            self.mPatchLogInfo(
                f"Monthly Patching operation style set to {self.__op_style} for target {self.__target_type} ")
            return

        # Change style to auto in case of prechecks and let it evaluate based on the VMs availabality, later.
        if self.__task in [TASK_PREREQ_CHECK, TASK_ROLLBACK_PREREQ_CHECK] and self.__op_style == OP_STYLE_NON_ROLLING:
            self.mPatchLogWarn("Changing operation style to auto for precheck operation.")
            self.__op_style = OP_STYLE_AUTO

        if (self.__op_style == OP_STYLE_AUTO and self.__target_env == ENV_PRODUCTION):

            if self.mGetDomUListFromXml(aFromXmList=True):
                self.__mListOfStatementsToPrint.append(("INFO", "VMs up found in cluster. Operation style will be set to Rolling."))
                self.__op_style = OP_STYLE_ROLLING
            else:
                self.__mListOfStatementsToPrint.append(("INFO", "VMs not found in cluster. Operation style will be set to Non-Rolling"))
                self.__op_style = OP_STYLE_NON_ROLLING

        _ops_style_message_to_be_printed = f"Operation style set to {self.__op_style}"
        self.__mListOfStatementsToPrint.append(("INFO", _ops_style_message_to_be_printed))

    def mCheckDomuAvailability(self):
        """
        This method checks the availability of the domU on each dom0.
        Return two factors:
            1) DomU availability
               True : Each dom0s has at-least one domU running
               False: One/many of the dom0s do not have domUs running.
            2) List of dom0s which don't have domUs running on it.

        """
        _rc = PATCH_SUCCESS_EXIT_CODE
        _cmd = ""
        _list_of_running_domUs_across_all_dom0 = []
        _suggestion_msg = None
        _clusters_with_no_high_availability = {}
        _cluster_details_with_domU_not_running = {}
        _non_adbd_vm_list = []
        _nat_node_list = []
        _cust_node_list = []
        _vm_list_with_nat_hostname = []
        _sshd_not_running_nodes = []
        _customer_hostname_vms_down = []

        '''
          - Environments can have a mixture of ADBD and non ADBD VMs.
          - Vm online status for both ADBD and Non-ABDB VMs are performed using sshd/socket based exacloud API.
        '''

        if len(self.mGetDom0DomUCustomerNameMapWithNoZeroVcpu()) > 0:
            for _, _cust_node_list in self.mGetDom0DomUCustomerNameMapWithNoZeroVcpu():
                _nat_node_list.extend(self.mGetDomUNatHostNamesforDomuCustomerHostNames(_cust_node_list))
            # Nat hostname is used here since the checks are performed from Exacloud.
            _ret_sshd_validation, _sshd_not_running_nodes = self.mGetSshdNotRunningNodeList(_nat_node_list)

            # HA validations are performed even if one
            # VM in a cluster is up and running. There
            # can be scenarios where 2 out of 3 nodes have
            # ssh service up and HA requirement is met.
            for _, _vm_list in self.mGetDom0DomUCustomerNameMapWithNoZeroVcpu():
                _vm_list = self.mGetDomUNatHostNamesforDomuCustomerHostNames(_vm_list)
                _vm_list_with_nat_hostname.extend(_vm_list)

        '''
         Nat hostname is used here since the checks are performed from Exacloud.
         Get the list of VMs running and not running based on Exacloud ssh validations 
         and xm/virsh based validations.    
        '''
        _customer_hostname_vms_down, _list_of_running_domUs_across_all_dom0 = self.mGetListOfRunningDomuAcrossAllDom0(_sshd_not_running_nodes, _vm_list_with_nat_hostname)

        '''
         _list_of_running_domUs_across_all_dom0 can contain the list of VMs down as per sshd validations,
         but up as per virsh/xm validations.
        '''
        if len(_list_of_running_domUs_across_all_dom0) > 0:
            self.mPatchLogInfo(
                f"List of DomUs that are currently up and running : {json.dumps(_list_of_running_domUs_across_all_dom0, indent=4)}.")
            _list_of_running_domUs_across_all_dom0 = self.mGetDomUCustomerHostNamesforDomuNatHostNames(_list_of_running_domUs_across_all_dom0)
            '''
             The below function mGetClusterDetailsWithoutHA performs a metadata 
             check and so the VM NAT hostnames is again changed to customerhostnames
             since Ops wants to view the customer hostname in log messages

             All the VMs down as per sshd and virsh/xm validations are removed from _list_of_running_domUs_across_all_dom0 list.
            '''
            _clusters_with_no_high_availability = self.mGetClusterDetailsWithoutHA(_list_of_running_domUs_across_all_dom0, _customer_hostname_vms_down)
            if _clusters_with_no_high_availability and len(_clusters_with_no_high_availability) > 0:
                if self.mGetExaunitId():
                    _suggestion_msg = f"DomUs are not available on dom0s. Corresponding Cluster with exaunit id : {self.mGetExaunitId()}, VMs details that are currently down are as follows : {str(_clusters_with_no_high_availability)}. At least 2 Guest VMs are expected to be up and running for high availability."
                else:
                    _suggestion_msg = f"DomUs are not available on dom0s. Corresponding Cluster with VMs details that are currently down are as follows : {str(_clusters_with_no_high_availability)}. At least 2 Guest VMs are expected to be up and running for high availability."

                if self.mGetTask() == TASK_PATCH:
                    _rc = DOM0_PATCH_FAILED_DONOT_HAVE_DOMU
                elif self.mGetTask() == TASK_ROLLBACK:
                    _rc = DOM0_ROLLBACK_FAILED_DONOT_HAVE_DOMU

                if self.mGetCurrentTargetType() == PATCH_DOM0 and self.mGetTask() == TASK_PREREQ_CHECK:
                    self.mPatchLogWarn(f"{_suggestion_msg}")
                else:
                    self.mAddError(_rc, _suggestion_msg)

        self.mPatchLogInfo("***Finished checking the availability of domUs on dom0s***\n")
        return _rc

    def mGetListOfRunningDomuAcrossAllDom0(self, aSshdNotRunningNodes, aVmListWithNatHostname):
        '''
         This method performs virsh/xm checks based on the list of nodes where sshd
         service is down and returns the final list of VMs which are down. In addition,
         it also returns the list of all VM's which are up and running across all dom0
        '''
        _vms_up_as_per_virsh_xm_output, _vms_down_as_per_virsh_xm_output = [], []
        _list_of_running_domUs_across_all_dom0 = []
        _sshd_not_running_customer_hostname_nodes = []
        _customer_hostname_vms_up_as_per_virsh_xm_output, _customer_hostname_vms_down = [], []

        if len(aSshdNotRunningNodes) > 0:
            _sshd_not_running_customer_hostname_nodes = self.mGetDomUCustomerHostNamesforDomuNatHostNames(aSshdNotRunningNodes)
            # Since virsh validations are done on the Dom0, customer hostnames
            # need to be passed in this case.
            _customer_hostname_vms_up_as_per_virsh_xm_output, _customer_hostname_vms_down = self.mCheckVmOnlineStatusBasedonXmVirshCmds(_sshd_not_running_customer_hostname_nodes)

            '''
             This sections compares the virsh/xm output with the sshd down nodes and
             determines whether the vm is down. If the output of both indicates that the vm
             is down , then the vm is considered to be down , else the vm is considered to be
             up and running
            '''
            if len(_customer_hostname_vms_down) > 0:
                _vms_down_as_per_virsh_xm_output = self.mGetDomUNatHostNamesforDomuCustomerHostNames(
                    _customer_hostname_vms_down)
                if len(aVmListWithNatHostname) > 0:
                    _vm_list_with_nat_hostname = [vm for vm in aVmListWithNatHostname if
                                                  vm not in _vms_down_as_per_virsh_xm_output]

            # Nat hostname is used here since the checks are performed from Exacloud.
            _list_of_running_domUs_across_all_dom0.extend(
                [_node_name for _node_name in aVmListWithNatHostname if _node_name not in aSshdNotRunningNodes])

            if len(_customer_hostname_vms_up_as_per_virsh_xm_output) > 0:
                _vms_up_as_per_virsh_xm_output = self.mGetDomUNatHostNamesforDomuCustomerHostNames(
                    _customer_hostname_vms_up_as_per_virsh_xm_output)
                for _vm in _vms_up_as_per_virsh_xm_output:
                    if _vm not in _list_of_running_domUs_across_all_dom0:
                        _list_of_running_domUs_across_all_dom0.append(_vm)
        return _customer_hostname_vms_down, _list_of_running_domUs_across_all_dom0


    def mGetClusterDetailsWithoutHA(self, aDomuRunningList, aCustomerHostnameVmsDown):
        '''
         In case of a multi vm environment, this method provides a list 
         of VMs that are currently down and might result in outage scenarios 
         due to required number of VMs not up.

         Return cluster with domu down list
                - List can be empty if none of the VMs in the
                  rack are down
                - Else otherwise.

         For a quarter rack, it is expected for the VMs to be up and
         running on both Dom0s.
        '''
        _cluster_details_with_domU_not_running = {}
        _list_of_running_domUs_across_dom0s = []

        # VMs confirmed to be shutdown to be removed from metadata details as well.
        # Remove the Vm's which are down from mGetDom0DomUCustomerNameMapWithNoZeroVcpu 
        # so that the new list _list_of_running_domUs_across_dom0s created from 
        # mGetDom0DomUCustomerNameMapWithNoZeroVcpu will only contain DomUs up and running.
        _list_of_running_domUs_across_dom0s.extend([(_dom0, [_vm for _vm in _vms if _vm not in aCustomerHostnameVmsDown]) for _dom0, _vms in self.mGetDom0DomUCustomerNameMapWithNoZeroVcpu()])

        # mGetClusterToVmMapWithNonZeroVcpu contains customer hostnames
        if len(self.mGetClusterToVmMapWithNonZeroVcpu()) > 0 and len(aDomuRunningList) > 0:
            _list_of_domu_not_running_in_cluster = []
            for _cluster_name, _domu_list in self.mGetClusterToVmMapWithNonZeroVcpu():

                '''
                 Domu availability check is skipped in case of a single node cluster
                 setup due to inadequate number of VMs to maintain high availability.

                 Ignore if the cluster in a single Node VMcluster
                '''
                if self.mGetClustersWithSingleVM() and _cluster_name in self.mGetClustersWithSingleVM():
                    self.mPatchLogInfo(
                        f"DomU availability check will be skipped on the cluster : {_cluster_name}, since this is a single node cluster.")
                    continue
                _domus_up_in_cluster_count = 0
                _list_of_domu_not_running_in_cluster = []
                for _domu_customer_name in _domu_list:
                    if _domu_customer_name in aDomuRunningList:
                        _domus_up_in_cluster_count += 1
                    else:
                        _suggestion_msg = f"DomU : {str(_domu_customer_name)} for the cluster : {str(_cluster_name)} is currently down."
                        if self.mGetCurrentTargetType() == PATCH_DOM0 and self.mGetTask() == TASK_PREREQ_CHECK:
                            self.mPatchLogWarn(f"{_suggestion_msg}")
                        else:
                            self.mPatchLogError(f"{_suggestion_msg}")
                        _list_of_domu_not_running_in_cluster.append(_domu_customer_name)
                        '''
                         _list_of_running_domUs_across_dom0s is used to get the corresponding Dom0
                         details for the DomU that is currently down.
                        '''
                        for _dom0_host, _domu_host_list in _list_of_running_domUs_across_dom0s:
                            if _domu_customer_name in _domu_host_list:
                                self.mPatchLogError(
                                    f"DomU : {_domu_customer_name} under Dom0 : {_dom0_host} is down and is expected to be up for the cluster : {_cluster_name}.")

                '''
                 HA checks are skipped in case of all VMs
                 of a cluster is down.
                '''
                if int(_domus_up_in_cluster_count) == 0:
                    self.mPatchLogInfo(f"DomU availability check will be skipped on the cluster : {_cluster_name} as all the VMs of this cluster are down.")

                '''
                 For high availability atleast 2 VMs must be
                 up and running.
                '''
                if int(_domus_up_in_cluster_count) != 0 and int(_domus_up_in_cluster_count) < 2:
                    _cluster_details_with_domU_not_running[_cluster_name] = list(set(_list_of_domu_not_running_in_cluster))

        return _cluster_details_with_domU_not_running

    def mGetSshdNotRunningNodeList(self, aNodeList):
        """
        This method is going to check if sshd is running on the remote node list
        returns PATCH_SUCCESS_EXIT_CODE and list of nodes where sshd is not runnning upon success
        and returns SSHD_VALIDATION_ERROR upon exception
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _sshd_not_running_nodes = []

        def _mCheckSshdRunningOnRemoteNode(aNode, aStatus):
            """
             This sub method checks whether sshd is running on the remote node
             It adds node details to aStatus where file check presence is failed.
            """
            if self.mGetCluControl().mCheckSshd(aNode, 180, 10):
                self.mPatchLogInfo(f"SSH port is reachable on {aNode}.")
            else:
                self.mPatchLogInfo(f"SSH port is not reachable on {aNode}.")
                aStatus.append({'node': aNode, 'status': 'failed'})
            # end of _mCheckSshdRunningOnRemoteNode

        try:
            """
             Parallelize checking of sshd is running or not on remote nodes.
            """
            _plist = ProcessManager()
            _rc_status = _plist.mGetManager().list()
            for _node_to_check in aNodeList:
                _p = ProcessStructure(_mCheckSshdRunningOnRemoteNode, [_node_to_check, _rc_status], _node_to_check)
                _p.mSetMaxExecutionTime(self.mGetValidateSshConnectivityExecutionTimeoutInSeconds())
                _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
                _p.mSetLogTimeoutFx(self.mPatchLogWarn)
                _plist.mStartAppend(_p)

            _plist.mJoinProcess()

            if _plist.mGetStatus() == "killed":
                _ret = SSHD_VALIDATION_ERROR
                self.mPatchLogError(
                    f"Timeout occurred while checking whether sshd is running on remote node list : {json.dumps(aNodeList, indent=4)}.")
                _sshd_not_running_nodes = aNodeList

            # Check for the nodes where file is missing
            for _rc_details in _rc_status:
                if _rc_details['status'] == "failed":
                    _sshd_not_running_nodes.append(_rc_details['node'])

            if _sshd_not_running_nodes:
                self.mPatchLogInfo(f"Node List where sshd is not running is: {str(_sshd_not_running_nodes)}")
        except Exception as e:
            _ret = SSHD_VALIDATION_ERROR
            self.mPatchLogWarn(f"Exception : {str(e)} occurred while validating whether sshd is running or not.")
            self.mPatchLogTrace(traceback.format_exc())
            _sshd_not_running_nodes = aNodeList

        return _ret, _sshd_not_running_nodes

    def mCheckVmOnlineStatusBasedonXmVirshCmds(self, aCustomVmList):
        """
        This method is going to check if Custom VMs are up based on xm/virsh list output.
        returns the VM running list. VMs not up as per virsh/xm list are removed.
        """
        _list_of_running_domUs_across_all_dom0 = []
        _list_of_running_domUs_up = []
        _list_of_running_domUs_down = []
        _dom0_list_from_ecra = []

        if self.mIsKvmEnv():
            '''
            sed added at the end to remove empty line
            Example:
              # virsh list|tail -n+3|awk '{print $2}' | sed '/^$/d'
                scaqan03dv0208.us.oracle.com
                scaqan03dv0204.us.oracle.com
                scaqan03dv0201.us.oracle.com
                scaqan03dv0202.us.oracle.com
                scaqan03dv0203.us.oracle.com
            '''
            _cmd = "virsh list| grep -i 'running' | awk '{print $2}' | sed '/^$/d'"
        else:
            _cmd = "xm list|tail -n+3|awk '{print $1}'"

        '''
         virsh and xm list commands to be execute on all Dom0 to get the 
         desired output. self.mGetCustomizedDom0List() only runs the 
         virsh and xm list commands only the list of nodes passed as part 
         of IncludeNodeList.
        '''
        for _dom0 in self.mGetDom0ListFromEcra():
            _node = exaBoxNode(get_gcontext())
            try:
                _node.mConnect(aHost=_dom0)
                _in, _out, _err = _node.mExecuteCmd(_cmd, aTimeout=SHELL_CMD_DEFAULT_TIMEOUT_IN_SECONDS)
                mCheckAndFailOnCmdTimeout(aCmd=_cmd, aNode=_node, aHandler=self)
                _output = _out.readlines()
                _list_of_running_domUs_across_all_dom0.extend(_domu_hostname.strip() for _domu_hostname in _output)

                if len(_list_of_running_domUs_across_all_dom0) == 0:
                    self.mPatchLogInfo(f"No Domus are up and running on dom0s = {str(_dom0)}")

            except Exception as e:
                self.mPatchLogWarn(f"Exception encountered while fetching the list of Domu that are currently up and running on Dom0 : {_dom0}.")
                self.mPatchLogTrace(traceback.format_exc())

            if _node.mIsConnected():
                _node.mDisconnect()

        if len(_list_of_running_domUs_across_all_dom0) > 0:
            self.mPatchLogInfo(f"List of VMs up and running as per virsh/xm output - {str(_list_of_running_domUs_across_all_dom0)}")
            for _vm in aCustomVmList:
                if _vm in _list_of_running_domUs_across_all_dom0:
                    '''
                     Get only the VMs from the list of all VMs up as per virsh/xm output,
                     but are down as per sshd validations.
                    '''
                    _list_of_running_domUs_up.append(_vm)
                else:
                    '''
                     Get only the VMs from the list of all VMs down
                     both as part of virsh/xm validations and as per
                     sshd validations.
                   '''
                    _list_of_running_domUs_down.append(_vm)

        if len(_list_of_running_domUs_up) > 0:
            self.mPatchLogInfo(f"List of VMs currently up - {str(_list_of_running_domUs_up)} as per virsh/xm list output, but were not accessible through sshd validations.")
        if len(_list_of_running_domUs_down) > 0:
            self.mPatchLogInfo(f"List of VMs currently down - {str(_list_of_running_domUs_down)} both as part of virsh/xm list and sshd validations.")

        return _list_of_running_domUs_up, _list_of_running_domUs_down

    def mAddPatchreport(self):
            """
            Return patch report with more detail. We try to maintain the same
            format of patching CNS payload so that it can be read uniformly
            in ecra side.
            """

            # fill up the payload json for notificaiton
            _patch_report_json = {}
            _myuuid = uuid4().hex
            _patch_report_json['httpRequestId'] = _myuuid

            _patch_report_json['recipients'] = []
            _channel_info = {}
            _channel_info['channelType'] = "topics"
            _patch_report_json['recipients'].append(_channel_info)

            _patch_report_json['notificationType'] = {}
            _patch_report_json['notificationType']['componentId'] = "Patch_ExadataInfra_SM"
            _patch_report_json['notificationType']['id'] = "Patch_ExadataInfra_SMnotification_v1"

            _patch_report_json['service'] = "ExadataPatch"
            _patch_report_json['component'] = "Patch Exadata Infrastructure"
            _patch_report_json['subject'] = "Patch Exadata Infrastructure Service Update"
            _patch_report_json['event_post_time'] = datetime.datetime.now().strftime("%Y-%m-%d:%H.%M.%S %Z")
            _patch_report_json['log_dir'] = self.__patchmgr_log_path_on_launch_node

            _oeda_request_log_path = self.mGetLogPath()
            if _oeda_request_log_path is None:
                _oeda_request_log_path = ""
            _patch_report_json["oeda_requests_log_path"] = _oeda_request_log_path

            # Fetch cluster name
            _patch_report_json['cluster_name'] = self.mGetRackName()

            # This is required for mandatory CNS check in CNSOperation.java
            _patch_report_json['exadata_rack'] = self.mGetRackName()

            # target type, such as cell, dom0, etc
            _patch_report_json['target_type'] = self.mGetTargetTypes()

            # task type such as, prereq, patch, rollback, etc
            _patch_report_json['operation_type'] = self.mGetTask()

            # operation style, rolling and / or non-rolling.
            _patch_report_json['operation_style'] = self.mGetOpStyle()

            # These are required in ecra Patcher.java for updating the image version
            # and cabinet status
            _patch_report_json['target_version'] = self.mGetTargetVersion()
            if self.mIsClusterLessUpgrade():
                _patch_report_json['cluster_less'] = 'yes'
            else:
                _patch_report_json['cluster_less'] = 'no'

            #Update launchnode name to be used to manipulate data in ecs_external_launch_node_patching_operations_table
            #in ecra after operation completion
            if self.mGetAdditionalOptions() and ('LaunchNode' in self.mGetAdditionalOptions()[0]):
                _patch_report_json["LaunchNode"] = self.mGetAdditionalOptions()[0]['LaunchNode']

            # update with exaunit id
            _patch_report_json['exaunit_id'] = self.mGetExaunitId()
            # update with exaocid
            _patch_report_json['exa_ocid'] = self.mGetExaOcid()
            # update with exasplice
            if self.mIsExaSplice():
                _patch_report_json['exa_splice'] = 'yes'
            else:
                _patch_report_json['exa_splice'] = 'no'

            _patch_report_json['topic'] = ''

            return _patch_report_json

    def mGetAllPatchListDetails(self):
        _master_request_uuid = None
        _child_request_uuid = None
        _req_status = None
        _json_report = None
        _reqobj = self.__cluctrl.mGetRequestObj()
        if _reqobj:
            _child_request_uuid = _reqobj.mGetUUID()
            self.mPatchLogTrace(f"Fetching Patch List Details using child request uuid {_child_request_uuid} ")
            _db = ebGetDefaultDB()
            _row = _db.mGetPatchChildRequest(_child_request_uuid)
            if _row:
                try:
                    _req_status = _row[0]
                    _json_report = _row[1]
                    _master_request_uuid = str(_row[2])
                except:
                    self.mPatchLogTrace("Error is fetching Patch List Details:\n")

        return _master_request_uuid, _child_request_uuid, _req_status , _json_report

    def mGetExistingErrorDetailsFromExacloudDB(self):
        """
        This method looks for existing exadata error 
        details in patch list table on the exacloud DB.
        """
        _db = None
        _json_report = {}
        _child_request_uuid = None
        _json_patch_report_data = {}
        _exadata_error_handling_list = []
        _reqobj = self.mGetCluControl().mGetRequestObj()
        if _reqobj:
            _child_request_uuid = _reqobj.mGetUUID()
            _db = ebGetDefaultDB()
            # Retrieve the json_report from patch list table
            _row = _db.mGetPatchChildRequest(_child_request_uuid)
            if _row:
                try:
                    _json_report = json.loads(_row[1])
                except Exception as e:
                    self.mPatchLogInfo('Exadata error handling details could not be found in exacloud DB.')
                    self.mPatchLogTrace(traceback.format_exc())

        if _json_report:
            _json_patch_report_data  = _json_report["data"]

            if _json_patch_report_data:
                for _json_patch_report_data_key, _json_patch_report_data_value in _json_patch_report_data.items():
                    if _json_patch_report_data_key == "patch_mgr_error":
                        _exadata_error_handling_list = _json_patch_report_data_value["patch_mgr_error_details"]

                '''
                  Below list only will be returned in case of Exadata error 
                  handling details already present in patch list table of 
                  exacloud DB.

                    [
                       {
                          "nodeName":"slcs27adm04.us.oracle.com",
                          "nodeType":"Driver-Node",
                          "Unhandled_Checks":[
                             {
                                "Description":"Checks that are not handled by the error code framework.",
                                "Starttime":"2023-09-08 08:10:49 UTC",
                                "Endtime":"2023-09-08 08:10:49 UTC",
                                "Status":"Failed",
                                "ErrorCode":"EXAUPG-99999",
                                "ErrorMessage":"Unhandled error[s] found. Potential sources include: 1)main:dbnodeupdate.sh precheck failed on one or more nodes 2)patchmgr_set_failed_status_for_the_node:DONE: dbnodeupdate.sh precheck on slcs27adm03.us.oracle.com;;;;slcs27adm03.us.oracle.com has state: FAILED 3)postamble:DONE: Initiate precheck on node(s). 4)patchmgr_print_exit:FAILED run of command:./patchmgr -dbnodes node_list -precheck -iso_repo exadata_ovs_22.1.14.0.0.230818_Linux-x86-64.zip -target_version 22.1.14.0.0.230818 -log_dir /EXAVMIMAGES/dbserver.patch.zip_exadata_ovs_22.1.14.0.0.230818_Linux-x86-64.zip/dbserver_patch_230822/patchmgr_log_248651d7-2ac6-46fc-a6ac-539b31f707d0 -allow_active_network_mounts .",
                                "Cause":"Unhandled error[s].",
                                "Action":"Examine the patchmgr and dbnodeupdate logs to determine the failure cause.",
                                "MOSUrl":"https://support.oracle.com/msg/EXAUPG-99999"
                             }
                          ]
                       },
                       {
                          "nodeName":"slcs27adm03.us.oracle.com",
                          "nodeType":"Target-Node",
                          "CheckFreeSpace":[
                             {
                                "Description":"Verify ability to obtain diskspace usage for /  file system.",
                                "Starttime":"2023-09-08 08:10:31 UTC",
                                "Endtime":"2023-09-08 08:10:31 UTC",
                                "Status":"Passed"
                             },
                             {
                                "Description":"Check to verify 1500  MB free space in /  file system.",
                                "Starttime":"2023-09-08 08:10:31 UTC",
                                "Endtime":"2023-09-08 08:10:32 UTC",
                                "Status":"Failed",
                                "ErrorCode":"EXAUPG-00605",
                                "ErrorMessage":"Insufficient free space found in / file system. 1500  MB is required, but only 801  MB is available.",
                                "Cause":"Free space in /  file system is less than 1500  MB.",
                                "Action":"Cleanup /  file system and restart the update.",
                                "MOSUrl":"https://support.oracle.com/msg/EXAUPG-00605"
                             }
                          ]
                       }
                    ]
                '''
                if _exadata_error_handling_list and len(_exadata_error_handling_list) > 0:
                    self.mPatchLogInfo(
                        f"Found Exadata error handling details on the exacloud DB : {json.dumps(_exadata_error_handling_list, indent=4)}")

        return _exadata_error_handling_list

    def mAddError(self, aError, aSuggestion):
        """
        Generate the patch error report.
        """

        _master_request_uuid = None
        _child_request_uuid = None
        _exadata_patch_err_json = {}
        _existing_exadata_error_details_list = []

        _suggestion_msg = aSuggestion
        if aSuggestion and len(aSuggestion) > ERROR_MSG_TRUNCATE_LENGTH:
            _suggestion_msg = mTruncateErrorMessageDescription(aSuggestion)

        self.__json_status["data"] = self.mAddPatchreport()

        _code, _msg, _description, _error_action = ebPatchFormatBuildErrorWithErrorAction(aError, _suggestion_msg, aTargetTypes = self.__target_type)
        self.__json_status["data"]["error_code"] = _code
        self.__json_status["data"]["error_message"] = _msg
        self.__json_status["data"]["error_detail"] = _description
        if _error_action:
            self.__json_status["data"]["error_action"] = _error_action
        else:
            self.mPatchLogInfo(f"Error action is empty for Error Code {_code} in mAddError")
        self.__json_status["data"]['node_progressing_status'] = self.mGetPatchProgressStatus()

        # Add launchNodes for clusterless patching
        if self.mIsClusterLessUpgrade():
            self.__json_status["data"]["cluster_less"] = "yes"
            if self.mGetAdditionalOptions() and ('LaunchNode' in self.mGetAdditionalOptions()[0]):
                self.__json_status["data"]["LaunchNode"] = self.mGetAdditionalOptions()[0]['LaunchNode']
            if self.mGetAdditionalOptions() and ('LaunchNodeCabinet' in self.mGetAdditionalOptions()[0]):
                self.__json_status["data"]["LaunchNodeCabinet"] = self.mGetAdditionalOptions()[0]['LaunchNodeCabinet']
            if self.mGetAdditionalOptions() and ('CabinetFabricName' in self.mGetAdditionalOptions()[0]):
                self.__json_status["data"]["CabinetFabricName"] = self.mGetAdditionalOptions()[0]['CabinetFabricName']
            if self.mGetAdditionalOptions() and ('LaunchNodeState' in self.mGetAdditionalOptions()[0]):
                self.__json_status["data"]["LaunchNodeState"] = self.mGetAdditionalOptions()[0]['LaunchNodeState']

        '''
         Add Exadata error handling details to final status call output
         in case of a patchmgr failure.

         Exadata error handling support is not yet available in case of 
         switch patching and below validation in case of switch patching 
         must be skipped.
        '''
        if self.__target_type[0] not in [ PATCH_ROCESWITCH, PATCH_IBSWITCH, PATCH_SWITCH ]:
            _cur_launch_node_list = self.mGetCurrentLaunchNodeList()
            for _launch_node in _cur_launch_node_list:
                _exadata_patch_err_json = self.mGetPatchMgrErrorHandlingDetails(_launch_node)
                if _exadata_patch_err_json and ("patch_mgr_error_details" in _exadata_patch_err_json):
                    _error_list = _exadata_patch_err_json["patch_mgr_error_details"]
                    if _error_list and len(_error_list) > 0:
                        _existing_exadata_error_details_list = self.mGetExistingErrorDetailsFromExacloudDB()
                        if _existing_exadata_error_details_list and len(_existing_exadata_error_details_list) > 0:
                            for _existing_exadata_error in _existing_exadata_error_details_list:
                                if _existing_exadata_error not in _exadata_patch_err_json["patch_mgr_error_details"]:
                                    _exadata_patch_err_json["patch_mgr_error_details"].append(_existing_exadata_error)
                            self.__json_status["data"]['patch_mgr_error'] = _exadata_patch_err_json
                        else:
                            self.__json_status["data"]['patch_mgr_error'] = _exadata_patch_err_json

        _master_request_uuid, _child_request_uuid , _ , _ = self.mGetAllPatchListDetails()
        # Save json error in db
        _reqobj = self.__cluctrl.mGetRequestObj()
        if _reqobj:
           self.__json_status["data"]["child_request_uuid"] = _child_request_uuid
           if _master_request_uuid:
               self.mPatchLogInfo(f"Master request uuid for error status {_master_request_uuid}")
               self.__json_status["data"]["master_request_uuid"] = _master_request_uuid

           self.mPatchLogInfo('Updating patch status JSON report to Exacloud DB.')
           _db = ebGetDefaultDB()
           _db.mUpdateJsonPatchReport(_reqobj.mGetUUID(), json.dumps(self.mGetJsonStatus(), indent=4))
           self.mPatchLogInfo('mAddError - Output')

        _ret = self.mGetJsonStatus()
        self.mPatchLogInfo("Patch status details.\n"+json.dumps(_ret, indent=4))
        self.mPatchLogInfo(f"\n\n*******Execute : 'ecracli>patch getDebugInfo ecraRequestId={self.mGetMasterReqId()}' to locate the logs and other details for further analysis.********** \n\n")
        return _ret

    def mGetECSLabelInformation(self):

        _ecs_version = None
        try:
            # Get ECS Label information
            # should not fail if version is not there
            if os.path.exists("config/label.dat"):
                with open("config/label.dat") as _f:
                    _ecs_version = _f.read().strip()
        except:
            self.mPatchLogInfo("Unable to obtain ecs version")
            pass

        return _ecs_version

    def mGetExacloudThreadLogsPath(self, aMasterRequestUUID, aChildRequestUUID):

        _master_request_uuid = aMasterRequestUUID
        _child_request_uuid = aChildRequestUUID
        _exacloud_thread_log_path = None
        _dispatcher_log_path = None

        # Assume __file__ will always be $EC_HOME/exabox/infrapatching/handlers/generichandler.py
        # Need to navigate to $EC_HOME/log/threads/0000-0000-0000-0000/00000000-0000-0000-0000-000000000000
        _threads_log_directory = os.path.abspath(f"{__file__}/../../../../log/threads/0000-0000-0000-0000/00000000-0000-0000-0000-000000000000")
        # Get the Exaclod thread logs path
        if _threads_log_directory and os.path.isdir(_threads_log_directory) is True:
            # Include the target type in the child thread log file name within
            # the patch failure JSON file. This is required to integrate the
            # AIM bug into the oneview.
            _exacloud_thread_log_path = f"{_threads_log_directory}/{_child_request_uuid}_cluctrl.{self.mGetTask()}_{self.mGetTargetTypes()[0]}.log"
            _dispatcher_log_path = f"{_threads_log_directory}/{_master_request_uuid}_patch.patchclu_apply.log"
        else:
            self.mPatchLogInfo("Exacloud Thread Logs Directory is not Present")

        return _exacloud_thread_log_path, _dispatcher_log_path

    def mGetExternalWorkRequestID(self):
        """
        This method will obtain the Work Request ID
        """
        _external_work_request_id = ""
        if (self.mGetAdditionalOptions() and 'external-work-request-id' in (self.mGetAdditionalOptions()[0])):
            _external_work_request_id = self.mGetAdditionalOptions()[0]['external-work-request-id']
        return _external_work_request_id

    def mDumpFailureJsonFileforNonPatchmgrFailures(self, aMasterRequestUUID, aChildRequestUUID, aJSONPatchData):
        _exacloud_patch_error_dict = {}
        _simple_pairs = {}
        _nested_dicts = {}
        _ec_home_log_dir = None
        _master_request_uuid = aMasterRequestUUID
        _child_request_uuid = aChildRequestUUID
        _json_patch_data = aJSONPatchData

        if self.mGetLogPath() and os.path.isdir(self.mGetLogPath()) is True:
            # self.mGetLogPath() = $EC_HOME/oeda/requests/96c8c3f2-26fa-11ef-bb06-0200170667b1/log/patchmgr_logs
            # Get rid of the patchmgr_logs. Final path e.g /u02/2011drop/admin/exacloud/oeda/requests/96c8c3f2-26fa-11ef-bb06-0200170667b1/log/
            _ec_home_log_dir = '/'.join((self.mGetLogPath()).split("/")[:-1])

            if _ec_home_log_dir:
                _ecs_version = self.mGetECSLabelInformation()
                if _ecs_version:
                    _exacloud_patch_error_dict["ecs_label"] = _ecs_version

                if self.mGetExternalWorkRequestID():
                    _exacloud_patch_error_dict["work_request_id"] = self.mGetExternalWorkRequestID()

                if self.mGetControlPlaneRequestID():
                    _exacloud_patch_error_dict["control_plane_request_id"] = self.mGetControlPlaneRequestID()

                if self.mGetMasterReqId():
                    # self.mGetMasterReqId() is the ECRA Request Id
                    _exacloud_patch_error_dict["ecra_request_id"] = self.mGetMasterReqId()

                if _json_patch_data and _json_patch_data["data"]:
                    _exacloud_patch_error_dict.update(_json_patch_data['data'])

                _exacloud_thread_log_path, _dispatcher_log_path = self.mGetExacloudThreadLogsPath(_master_request_uuid, _child_request_uuid)
                if _exacloud_thread_log_path:
                    _exacloud_patch_error_dict["exacloud_thread_log_path"] = _exacloud_thread_log_path
                if _dispatcher_log_path:
                    _exacloud_patch_error_dict["exacloud_dispatcher_log_path"] = _dispatcher_log_path

                # Separate simple key-value pairs and nested dictionaries for rearrangement
                for _key, _value in _exacloud_patch_error_dict.items():
                    if isinstance(_value, dict):
                        _nested_dicts[_key] = _value
                    else:
                        _simple_pairs[_key] = _value

                # Combine simple pairs and nested dictionaries, preserving their order
                combined_data = {**_simple_pairs, **_nested_dicts}

                _exacloud_patch_error_json_file = f"{_ec_home_log_dir}/{_child_request_uuid}_exacloud_patch_error.json"
                self.mPatchLogInfo(
                    f"Generating a JSON file for the exacloud patch failure at {_exacloud_patch_error_json_file} ")
                with open(_exacloud_patch_error_json_file, 'w') as _ec_patch_error_fd:
                    json.dump(combined_data, _ec_patch_error_fd, indent=4)
        else:
            self.mPatchLogInfo("Output directory for generating exacloud patch failure json is not present")

    #Helper function to debug the details from Patch List
    def mDisplayPatchListDetails(self):
        """
        Display the details from the patchlist entity at any point
        """
        _master_request_uuid, _child_request_uuid, _req_status, _json_report = self.mGetAllPatchListDetails()
        if _master_request_uuid:
            self.mPatchLogInfo(f"_master_request_uuid {_master_request_uuid} ")
        if _child_request_uuid:
            self.mPatchLogInfo(f"_child_request_uuid {_child_request_uuid} ")
        if _req_status:
            self.mPatchLogInfo(f"_req_status {_req_status} ")
        if _json_report:
            self.mPatchLogInfo(f"_json_report : {json.dumps(_json_report, indent=4)} ")

    def mGetPatchProgressStatus(self):
        _db = None
        _json_report = {}
        _child_request_uuid = None
        _json_patch_report_data = {}
        _node_progress_status_json = {}
        _reqobj = self.mGetCluControl().mGetRequestObj()
        if _reqobj:
            _child_request_uuid = _reqobj.mGetUUID()
            _db = ebGetDefaultDB()
            # Retrieve the json_report from patch list table
            _row = _db.mGetPatchChildRequest(_child_request_uuid)
            if _row:
                try:
                    _json_report = json.loads(_row[1])
                except TypeError as te:
                    # when patch report not yet generated _row[1] will have None
                    self.mPatchLogTrace('JSON patch report not yet generated. This is expected when patchmgr session not yet started or patchmgr session not required for certain operations!')
                except Exception as e:
                    self.mPatchLogWarn('Exception while loading JSON patch report')
                    self.mPatchLogTrace(traceback.format_exc())
            else:
                self.mPatchLogError("Error in fetching json report from Patch List Details from DB")
        if _json_report:
            _json_patch_report_data  = _json_report["data"]

            if _json_patch_report_data:
                self.mPatchLogInfo("Found Json patch report data.")
                if "node_progressing_status" in _json_patch_report_data:
                    _node_progress_status_json = _json_patch_report_data["node_progressing_status"]
                # self.mPatchLogInfo('_node_progress_status_json %s' % _node_progress_status_json)

        return _node_progress_status_json

    def mUpdatePatchReportJsonToDB(self, aJsonPatchReport):
        if aJsonPatchReport:
            _reqobj = self.mGetCluControl().mGetRequestObj()
            if _reqobj:
                self.mPatchLogInfo("Updating patch status JSON into Exacloud DB.")
                _db = ebGetDefaultDB()
                _db.mUpdateJsonPatchReport(_reqobj.mGetUUID(), json.dumps(aJsonPatchReport, indent=4))
        else:
            self.mPatchLogInfo("mUpdatePatchReportJsonToDB : Json Patch Report is empty.")

    def mGetErrorCodeFromChildRequest(self):
        """
          This method parses the data json obtained from Exacloud DB and checks for presence of error code details.
           - If there is an error code in the error_code field other than PATCH_SUCCESS_EXIT_CODE - True is returned
           - If the error_code Field has PATCH_SUCCESS_EXIT_CODE - False is returned
        """
        _json_patch_report_data = {}
        _ret = False
        _error_code = PATCH_SUCCESS_EXIT_CODE
        try:
            _, _, _, _json_patch_report = self.mGetAllPatchListDetails()
            _json_patch_report_data = json.loads(_json_patch_report)
            if _json_patch_report_data and "data" in _json_patch_report_data and "error_code" in _json_patch_report_data["data"]:
                _error_code = str(_json_patch_report_data["data"]["error_code"])
                if _error_code is not None and _error_code != str(PATCH_SUCCESS_EXIT_CODE):
                    self.mPatchLogDebug(f"Found error code : {_error_code} on the Exacloud DB.")
                    _ret = True
        except Exception as e:
            self.mPatchLogTrace(
                f"Exception encountered when error handling details were fetched from Exacloud DB {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            return _error_code, _ret

    def mInitializeIncludeListNodes(self):
        """
        This function gets the node name if specified in the rest api or in
        the additional parameter list.
        It returns:
           Node List, if user specified in the additional parameter
                      i.e., in IncludeNodeList param
           None, otherwise
        """

        _include_node_list = []
        if self.mGetAdditionalOptions() and ('IncludeNodeList' in self.mGetAdditionalOptions()[0]) \
            and (self.mGetAdditionalOptions()[0]['IncludeNodeList']) \
            and (self.mGetAdditionalOptions()[0]['IncludeNodeList']) != "none" \
            and len(self.mGetAdditionalOptions()[0]['IncludeNodeList']) > 0:
            for _include_node in self.mGetAdditionalOptions()[0]['IncludeNodeList'].split(','):
                _include_node_list.append(_include_node)
            self.mPatchLogInfo(f"Include node list hosts are : {json.dumps(_include_node_list, indent=4)}")

        return _include_node_list

    def mGetlaunchNodeForIncludeNodeList(self, aSingleNodeName, aLaunchNodeCandidates):
        """
         This method is common method used between dom0 and domu
         and are used to return launch node candidates during
         include node list patch operations.
        """

        self.mPatchLogInfo(f"User specified node '{aSingleNodeName}' for patch.")
        _launch_node_candidates_for_single_node_upgrade = []
        _valid_node_provided = False
        if self.mGetCluPatchCheck().mPingNode(aSingleNodeName):
            if aSingleNodeName in aLaunchNodeCandidates:
                _launch_node_candidates_for_single_node_upgrade.append(aSingleNodeName)
                aLaunchNodeCandidates.remove(aSingleNodeName)
                _valid_node_provided = True
            else:
                _errmsg = (
                    f"User specified node '{aSingleNodeName}' does not exist in the original launch node candidates: '{aLaunchNodeCandidates}'.")
                self.mPatchLogError(_errmsg)
                raise Exception(_errmsg)
        else:
            _errmsg = (f"User requested node {aSingleNodeName} for upgrade is not pingable.")
            self.mPatchLogError(_errmsg)
            raise Exception(_errmsg)

        if _valid_node_provided:
            for _launch_node in aLaunchNodeCandidates:
                if self.mGetCluPatchCheck().mPingNode(_launch_node):
                    _launch_node_candidates_for_single_node_upgrade.append(_launch_node)
                    aLaunchNodeCandidates = _launch_node_candidates_for_single_node_upgrade
                    return aLaunchNodeCandidates

    def mGetListOfLaunchNodeCandidates(self, aLaunchNodeCandidates):
        """
        This method prepares the list of launch node candidates.
         
          - In case of Include list specified and is greater than 
            2, then launch node would be potential launch node 
            candidates.
          - In regular patch flow, _launch_node_candidates obtained 
            from _dom0U_list are considered.
        """
        _launch_node_candidates = list(aLaunchNodeCandidates)

        if self.mGetCurrentTargetType() in [ PATCH_DOM0, PATCH_DOMU ]: 
            if len(self.mGetIncludeNodeList()) >= 2:
                # if Include nodes total is less than the list of dom0
                if self.mGetCurrentTargetType() == PATCH_DOM0:
                    if len(self.mGetIncludeNodeList()) < len(_launch_node_candidates):
                        _launch_node_candidates = list(set(_launch_node_candidates) - set(self.mGetIncludeNodeList()))
                    else:
                        _launch_node_candidates = self.mGetIncludeNodeList()[:]
                else:
                    _launch_node_candidates = self.mGetIncludeNodeList()[:]
                self.mPatchLogInfo(f"Include node list upgrade is opted and the launch node candidates are {json.dumps(_launch_node_candidates, indent=4)}.")
            elif len(self.mGetIncludeNodeList()) == 1:
                self.mPatchLogInfo(f"Single node upgrade is opted and the hostname is {self.mGetIncludeNodeList()[0]}.")
                _launch_node_candidates = self.mGetlaunchNodeForIncludeNodeList(self.mGetIncludeNodeList()[0], aLaunchNodeCandidates)
                self.mPatchLogInfo(
                    f"Single node upgrade is opted and the launch node candidates are {str(_launch_node_candidates)}.")
        
        return _launch_node_candidates

    def mCreateInfrapatchingTimeStatsEntry(self, aNodes, aStage, aSubStage=''):
        if self.mIsTimeStatsEnabled():
            """
            Sets patching time stat record object
            """
            try:
                #Get master_uuid and child_uuid details
                _master_request_uuid, _child_request_uuid, _, _ = self.mGetAllPatchListDetails()
                _patch_type = PATCH_TYPE_QUARTERLY
                if self.mIsExaSplice():
                    _patch_type = PATCH_TYPE_MONTHLY

                _patching_timestats_record = InfrapatchingTimeStatsRecord(_master_request_uuid,_child_request_uuid,
                                                                      self.mGetTargetTypes(), self.mGetTask(),
                                                                      self.mGetRackName(), _patch_type, self.mGetOpStyle())
                _patching_timestats_record.mSetPatchingStage(aStage)
                _patching_timestats_record.mSetNodeNames(aNodes)
                _patching_timestats_record.mSetPatchingSubStage(aSubStage)

                self.mPatchLogInfo(
                    f"mCreateInfrapatchingTimeStatsEntry : Updating timestat details for {aStage} and nodes {str(aNodes)}")
                _db = ebGetDefaultDB()
                _db.mCreateInfrapatchingTimeStatsEntry(_patching_timestats_record)

            except Exception as e:
                self.mPatchLogWarn(
                    f"mCreateInfrapatchingTimeStatsEntry : Exception {str(e)} occurred while creating time stat entry.")
                self.mPatchLogTrace(traceback.format_exc())

    def mUpdateInfraPatchingTimeStatEntry(self, aStage, aSubStage='', aNodes=None):
        if self.mIsTimeStatsEnabled():
            try:
                _log_message = f"mUpdateInfraPatchingTimeStatEntry : Updating timestat details for {aStage} "
                if aNodes:
                    _log_message += f" and nodes {aNodes}"
                self.mPatchLogInfo(_log_message)
                _db = ebGetDefaultDB()
                _child_request_uuid = None
                _reqobj = self.__cluctrl.mGetRequestObj()
                if _reqobj:
                    _child_request_uuid = _reqobj.mGetUUID()
                    _db.mUpdateInfrapatchingTimeStatEntry(_child_request_uuid, aStage, aSubStage, aNodes)
                else:
                    self.mPatchLogWarn("mUpdateInfraPatchingTimeStatEntry : Could not fetch child_request_uuid to update time stat entry.")

            except Exception as e:
                self.mPatchLogWarn(
                    f"mUpdateInfraPatchingTimeStatEntry : Exception {str(e)} occurred while updating time stat entry.")
                self.mPatchLogTrace(traceback.format_exc())

    def mPopulateInfrapatchingTimeStatsEntries(self, aNewStage, aNewSubStage, aNewStageNodes, aCompletedStage, aCompletedSubStage, aCompletedStageNodeDetails=None):
        if self.mIsTimeStatsEnabled():
            try:
                # For completed stage, update endtime
                if aCompletedStageNodeDetails:
                    self.mUpdateInfraPatchingTimeStatEntry(aCompletedStage, aCompletedSubStage, aCompletedStageNodeDetails)
                else:
                    self.mUpdateInfraPatchingTimeStatEntry(aCompletedStage, aCompletedSubStage)

                # For new stage, create the timestat entry
                self.mCreateInfrapatchingTimeStatsEntry(aNewStageNodes, aNewStage, aNewSubStage)
            except Exception as e:
                self.mPatchLogWarn(
                    f"mPopulateInfrapatchingTimeStatsEntries : Exception {str(e)} occurred while populating time stat entries.")
                self.mPatchLogTrace(traceback.format_exc())

    def mDumpCurrentInfrapactchOperationTimeStatsToFile(self, aPatching_time_stats=None):
        if self.mIsTimeStatsEnabled():
            try:
                if aPatching_time_stats:
                    if "node_patching_time_stats" in aPatching_time_stats.keys() and len(aPatching_time_stats["node_patching_time_stats"]) > 0:
                        _patching_time_stats_list = aPatching_time_stats["node_patching_time_stats"]
                        _child_request_uuid = aPatching_time_stats["child_uuid"]
                        _operation = aPatching_time_stats["operation"]

                        _threads_log_directory = os.path.join(THREADS_LOG_DIRECTORY)
                        # Dump time stats details into child_uuid_infrapatch_patch_time_stats.log in thread logs directory
                        if _threads_log_directory and os.path.isdir(_threads_log_directory) is True:
                            _path_for_time_profile_json_for_patching_operation = f"{_threads_log_directory}/{_child_request_uuid}_infrapatch_{_operation}_time_stats.log"
                            with open(_path_for_time_profile_json_for_patching_operation, "w") as _time_profile_file_fd:
                                json.dump(aPatching_time_stats, _time_profile_file_fd)
                        else:
                            self.mPatchLogWarn(
                                "mDumpCurrentInfrapactchOperationTimeStatsToFile : Could not fetch threads log directory to dump time stat details.")
                    else:
                        self.mPatchLogInfo("mDumpCurrentInfrapactchOperationTimeStatsToFile : node_patching_time_stats not found in time_stats details.")
                else:
                    self.mPatchLogInfo("mDumpCurrentInfrapactchOperationTimeStatsToFile : time_profiel data not found.")
            except Exception as e:
                self.mPatchLogWarn(
                    f"mDumpCurrentInfrapactchOperationTimeStatsToFile : Exception {str(e)} occurred while dumping timestat details.")
                self.mPatchLogTrace(traceback.format_exc())

    def mUpdateInfrapatchingTimeStatsForUnfilledStages(self):
        """
        This method updates end_time for the stage where end_time is not updated. This could happen because of exception
        and failure scenarios. In happy path scenarios(infrapatch operation success cases) start_time and end_time are
        captured correctly in the sequence for all the stages, if execution occurs or failure returns, end_time is updated
        with this method.
        """ 
        if self.mIsTimeStatsEnabled():
            try:
                _db = ebGetDefaultDB()
                _child_request_uuid = None
                _reqobj = self.__cluctrl.mGetRequestObj()
                if _reqobj:
                    _child_request_uuid = _reqobj.mGetUUID()
                    self.mPatchLogInfo(
                        f"mUpdateInfrapatchingTimeStatsForUnfilledStages : Updating timestat details for the child_uuid {_child_request_uuid} ")
                    _db.mUpdateInfrapatchingTimeStatsForUnfilledStages( _child_request_uuid)
                else:
                    self.mPatchLogWarn("mUpdateInfrapatchingTimeStatsForUnfilledStages : Could not fetch child_request_uuid to update end_time for unfilled stages.")
            except Exception as e:
                self.mPatchLogWarn(
                    f"mUpdateInfrapatchingTimeStatsForUnfilledStages : Exception {str(e)} occurred while updating time stat entries for unfilled stages.")
                self.mPatchLogTrace(traceback.format_exc())

    def mReadInfrapactchOperationTimeStatsFromDB(self):
        """
        This method reads infrapatching timestats into a dictionary from exacloud db
        """
        _patching_time_stats_dict = {}
        if self.mIsTimeStatsEnabled():
            try:
                _child_request_uuid = None
                _reqobj = self.__cluctrl.mGetRequestObj()
                if _reqobj:
                    _child_request_uuid = _reqobj.mGetUUID()
                    _db = ebGetDefaultDB()
                    # Fetch the timestat details from DB
                    _list = _db.mGetInfapatchingTimeStats(_child_request_uuid)


                    _common_data_updated = False
                    _overall_time_profile_data = []
                    _post_patch_time_profile_data = []
                    # Needed to form the file name child_uuid_infrapatch_patch_time_stats.log
                    _operation = ""
                    _nodes_specified_for_patching = []

                    # read record by record
                    for _entry in _list:
                        # Capture common data for the time stat details for the patch operation
                        if not _common_data_updated:
                            _patching_time_stats_dict["master_uuid"] = _entry[0]
                            _patching_time_stats_dict["child_uuid"] = _entry[1]
                            _patching_time_stats_dict["rack_name"] = _entry[5]
                            _patching_time_stats_dict["target_type"] = _entry[2]
                            _patching_time_stats_dict["operation"] = _entry[4]
                            _operation = _patching_time_stats_dict["operation"]
                            _patching_time_stats_dict["patch_type"] = _entry[6]
                            _patching_time_stats_dict["operation_style"] = _entry[7]
                            _common_data_updated = True

                        _stage = _entry[8]
                        _patching_time_stat_dict_for_each_step = {"node_names": _entry[3], "stage": _entry[8],
                                                                  "sub_stage": _entry[9],
                                                                  "start_time": f"{_entry[10].strftime('%Y-%m-%d %H:%M:%S%z')}{time.strftime('%z')}",
                                                                  "end_time": f"{_entry[11].strftime('%Y-%m-%d %H:%M:%S%z')}{time.strftime('%z')}",
                                                                  "duration_in_seconds": _entry[12]}

                        if _stage == "PRE_PATCH":
                            _nodes_specified_for_patching = _patching_time_stat_dict_for_each_step["node_names"]

                        # Capture post_patch stage time stats separately so that all the post_patch stage entries
                        # can be consolidated into a single entry
                        if _stage == "POST_PATCH":
                            _post_patch_time_profile_data.append(_patching_time_stat_dict_for_each_step)
                        else:
                            _overall_time_profile_data.append(_patching_time_stat_dict_for_each_step)

                    """
                    Consolidate post_patch stage entries into a single entry such that
                    start_time for the consolidated record is start_time of first occurred record,
                    end_time for the consolidated record is end_time of last occurred record,
                    node_names for the consolidated record is the string containing all the nodes specified for infra patch operation and 
                    duration_in_seconds is summation of duration for all the occurrences of post_patch stage
                    """
                    _consolidated_post_patch_start_time = None
                    _consolidated_post_patch_end_time = None
                    _consolidated_post_patch_duration = 0
                    for _post_patch_time_stats_record in _post_patch_time_profile_data:
                        # If None, update as initial value
                        if not _consolidated_post_patch_start_time:
                            _consolidated_post_patch_start_time = _post_patch_time_stats_record["start_time"]

                        if _post_patch_time_stats_record["start_time"] < _consolidated_post_patch_start_time:
                            _consolidated_post_patch_start_time = _post_patch_time_stats_record["start_time"]

                        # If None, update as initial value
                        if not _consolidated_post_patch_end_time:
                            _consolidated_post_patch_end_time = _post_patch_time_stats_record["end_time"]

                        if _post_patch_time_stats_record["end_time"] > _consolidated_post_patch_end_time:
                            _consolidated_post_patch_end_time = _post_patch_time_stats_record["end_time"]

                        _consolidated_post_patch_duration += _post_patch_time_stats_record["duration_in_seconds"]

                    if _consolidated_post_patch_duration > 0:
                        _overall_time_profile_data.append({"node_names": _nodes_specified_for_patching, "stage": "POST_PATCH",
                                                           "sub_stage": "", "start_time": _consolidated_post_patch_start_time,
                                                           "end_time": _consolidated_post_patch_end_time,
                                                           "duration_in_seconds": _consolidated_post_patch_duration})

                    # Dictionary contains time stat details.
                    _patching_time_stats_dict["node_patching_time_stats"] = _overall_time_profile_data

                    self.mPatchLogInfo(
                        f"mGetInfrapactchOperationTimeStats : final time_stats are {json.dumps(_patching_time_stats_dict, indent=4)} ")
                else:
                    self.mPatchLogWarn("mGetInfrapactchOperationTimeStats : Could not fetch child_request_uuid to dump time stat details.")
            except Exception as e:
                _patching_time_stats_dict = {}
                self.mPatchLogWarn(
                    f"mGetInfrapactchOperationTimeStats : Exception {str(e)} occurred while dumping timestat details.")
                self.mPatchLogTrace(traceback.format_exc())

        return _patching_time_stats_dict

    def mGetPatchmgrTimestatsWithNodeProgressData(self, aCurPatchingTimestatsDict, aNodeProgressDataJson):
        """
         This method does the following
          1. If time_stats from infrapatching code are present, separates them into patch_mgr time_stats and non_patch_mgr time_stats(PRE_PATCH and POST_PATCH)
          2. Updates patch_mgr time_stats with timing details of node_progress_data if available
          3. If node_progress_data is only present, patch_mgr time_stats collected form node_progresss_data alone are returned
        """

        # This is needed because non_rolling happens in two iteration so time_stats are collected in two iterations from infrapcthing instrumentation code
        #  where as node_progres_data has consolidated list.
        # So if node_progress_data has timing details, new patch_mgr time_stats are collected in single iteration
        _non_rolling_new_patch_mgr_timestats_updated_already = False

        _patch_mgr_time_stats_list = []
        _non_patch_mgr_time_stats_list = []

        """
        Example for node_progressing_status structure

        "node_progressing_status": {
            "sleep_infra_patch": "no",
            "infra_patch_start_time": "2022-07-12 03:04:30-0700",
            "node_patching_progress_data": [
                {
                    "node_name": "scaqag01adm05.us.oracle.com",
                    "target_type": "dom0",
                    "patchmgr_start_time": "2022-07-12 03:05:22-0700",
                    "last_updated_time": "2022-07-12 03:42:37-0700",
                    "status": "Completed",
                    "status_details": "Succeeded"
                },
                {
                    "node_name": "scaqag01adm06.us.oracle.com",
                    "target_type": "dom0",
                    "patchmgr_start_time": "2022-07-12 03:45:57-0700",
                    "last_updated_time": "2022-07-12 04:24:39-0700",
                    "status": "Completed",
                    "status_details": "Succeeded"
                }
            ]
        }
        """

        #  Form a dictionary with node_name as key with patch_mgr time stats of node_progress_data as value
        _node_progress_data_dict = {}
        if aNodeProgressDataJson and 'node_patching_progress_data' in aNodeProgressDataJson.keys():
            for _node_progress_data_elem in aNodeProgressDataJson['node_patching_progress_data']:
                _patch_mgr_timestat_entry = {}
                if "node_name" in _node_progress_data_elem.keys():
                    _patch_mgr_timestat_entry["node_names"] = "%s%s%s" % (
                        "['", _node_progress_data_elem["node_name"], "']")
                    if "patchmgr_start_time" in _node_progress_data_elem.keys():
                        _patch_mgr_timestat_entry["patchmgr_start_time"] = _node_progress_data_elem[
                            "patchmgr_start_time"]
                    if "last_updated_time" in _node_progress_data_elem.keys():
                        _patch_mgr_timestat_entry["patchmgr_end_time"] = _node_progress_data_elem[
                            "last_updated_time"]
                    if "status" in _node_progress_data_elem.keys():
                        _patch_mgr_timestat_entry["status"] = _node_progress_data_elem["status"]
                    if "status_details" in _node_progress_data_elem.keys():
                        _patch_mgr_timestat_entry["status_details"] = _node_progress_data_elem["status_details"]

                # Both patchmgr_start_time and patchmgr_end_time are equal for the case of discarded_node_list
                # so ignoring it(as patch_mgr is not run)
                if _patch_mgr_timestat_entry["patchmgr_start_time"] != _patch_mgr_timestat_entry[
                    "patchmgr_end_time"]:
                    _node_progress_data_dict[_node_progress_data_elem["node_name"]] = _patch_mgr_timestat_entry


        def _mGetPatchTimeStatFromNodeProgressData(aNodeProgressDataElem):
            _new_patching_time_stats_record = {}
            _new_patching_time_stats_record["node_names"] = aNodeProgressDataElem[
                "node_names"]
            _new_patching_time_stats_record["stage"] = "PATCH_MGR"
            _new_patching_time_stats_record["sub_stage"] = ""
            _new_patching_time_stats_record["start_time"] = aNodeProgressDataElem[
                "patchmgr_start_time"]
            _new_patching_time_stats_record["end_time"] = aNodeProgressDataElem[
                "patchmgr_end_time"]
            # When node_progress_data status shows TimeOut, do not update duration
            if "status" in aNodeProgressDataElem and aNodeProgressDataElem[
                "status"] != "TimeOut":
                _new_patching_time_stats_record["duration_in_seconds"] = (
                        datetime.datetime.strptime(
                            _new_patching_time_stats_record["end_time"],
                            '%Y-%m-%d %H:%M:%S%z') - datetime.datetime.strptime(
                    _new_patching_time_stats_record["start_time"],
                    '%Y-%m-%d %H:%M:%S%z')).total_seconds()
            else:
                _new_patching_time_stats_record["duration_in_seconds"] = 0

            return _new_patching_time_stats_record
        # end of _mGetPatchTimeStatFromNodeProgressData

        try:
            if aCurPatchingTimestatsDict and "node_patching_time_stats" in aCurPatchingTimestatsDict.keys():
                _cur_patching_time_stats_list = aCurPatchingTimestatsDict["node_patching_time_stats"]

                for _cur_patching_time_stats_record in _cur_patching_time_stats_list:
                    if _cur_patching_time_stats_record["stage"] == "PATCH_MGR":
                        """
                         For cell,ibswitch and roceswitch cases , time_stats from infrapatching instrumented code would 
                         have single PATCH_MGR entry having node_names with all the patched nodes
                         So here updating time_stats for individual node
                        """
                        _cur_target_type = aCurPatchingTimestatsDict["target_type"]
                        _cur_target_type = _cur_target_type[2:-2]
                        _operation_style = aCurPatchingTimestatsDict["operation_style"]
                        self.mPatchLogInfo(
                            f"Updating patch_mgr time_stats for {_cur_target_type} {_operation_style} infra operation")
                        if ((_cur_target_type in [ PATCH_CELL, PATCH_IBSWITCH, PATCH_SWITCH ]) or (
                                _cur_target_type in [PATCH_DOM0,
                                                     PATCH_DOMU] and _operation_style == OP_STYLE_NON_ROLLING)):
                            if len(_node_progress_data_dict) > 0:
                                if not _non_rolling_new_patch_mgr_timestats_updated_already:
                                    for _node_progress_data_elem in _node_progress_data_dict.values():
                                        _new_patching_time_stats_record = _mGetPatchTimeStatFromNodeProgressData(_node_progress_data_elem)
                                        _patch_mgr_time_stats_list.append(_new_patching_time_stats_record)
                                    _non_rolling_new_patch_mgr_timestats_updated_already = True

                            else:
                                # If node_progress_data does not have data continue with time_stats collected from infrapatching instrumentation code
                                _patch_mgr_time_stats_list.append(_cur_patching_time_stats_record)

                        if _cur_target_type in [PATCH_DOM0, PATCH_DOMU] and _operation_style == OP_STYLE_ROLLING:
                            if len(_node_progress_data_dict) > 0:
                                # if node_name is present in node_progress_data then add patch_mgr time_stats from node_progress_data
                                # otherwise continue with time_stats from infrapatching instrumentation code
                                #
                                # Note: Node name will be of the format ['slcs27adm03.us.oracle.com'] so removing first
                                # and last two characters for node_name comparison
                                _cur_patching_time_stats_node_name = _cur_patching_time_stats_record["node_names"]

                                if _cur_patching_time_stats_node_name[2:-2] in _node_progress_data_dict:
                                    _node_progress_data_elem = _node_progress_data_dict[_cur_patching_time_stats_node_name[2:-2]]
                                    _new_patching_time_stats_record = _mGetPatchTimeStatFromNodeProgressData(_node_progress_data_elem)
                                    _patch_mgr_time_stats_list.append(_new_patching_time_stats_record)
                                else:
                                    _patch_mgr_time_stats_list.append(_cur_patching_time_stats_record)
                            else:
                                # There are no entries in node_progress_data so adding time_stats data from
                                # infrapatching instrumentation code
                                _patch_mgr_time_stats_list.append(_cur_patching_time_stats_record)

                    else:
                        # For PRE_PATCH and POST_PATCH stages
                        _non_patch_mgr_time_stats_list.append(_cur_patching_time_stats_record)
            else:
                self.mPatchLogInfo("node_patching_time_stats not found in time_stats data collected from exacloud DB")
                if _node_progress_data_dict:
                    for _node_progress_data_elem in _node_progress_data_dict.values():
                        _new_patching_time_stats_record = _mGetPatchTimeStatFromNodeProgressData(
                            _node_progress_data_elem)
                        _patch_mgr_time_stats_list.append(_new_patching_time_stats_record)

        except Exception as e:
            self.mPatchLogWarn(
                f"Exception {str(e)} occurred in mGetPatchmgrTimestatsWithNodeProgressData")
            self.mPatchLogTrace(traceback.format_exc())

        return _patch_mgr_time_stats_list, _non_patch_mgr_time_stats_list

    def mDumpPatchFailureJsonFile(self):

        try:
            _master_request_uuid, _child_request_uuid,  _, _json_patch_report = self.mGetAllPatchListDetails()
            if _json_patch_report:
                _json_patch_temp_data = json.loads(_json_patch_report)
                self.mPatchLogInfo("Exacloud patch operation failed and an error json will be generated.")
                self.mDumpFailureJsonFileforNonPatchmgrFailures(_master_request_uuid, _child_request_uuid, _json_patch_temp_data)
                if self.mIsExaCC() and self.mGetTask() in [ TASK_PATCH ]:
                    self.mPatchLogInfo("EXACC system detected and patchmgr error json will be dumped in case of patchmgr errors only.")
                    self.mDumpPatchMgrError(_master_request_uuid, _child_request_uuid, _json_patch_temp_data)
        except Exception as e:
            self.mPatchLogWarn(f"Exception {str(e)} occurred in mDumpPatchFailureJsonFile")
            self.mPatchLogWarn(traceback.format_exc())

    def mDumpPatchMgrError(self, aMasterRequestUUID, aChildRequestUUID, aJSONPatchData):

        _master_request_uuid = aMasterRequestUUID
        _child_request_uuid = aChildRequestUUID
        _json_patch_temp_data = aJSONPatchData
        _final_patchmgr_error_dict = {}

        if _json_patch_temp_data and _json_patch_temp_data["data"] and "patch_mgr_error" in _json_patch_temp_data["data"]:
            _json_patch_report_data_dict = _json_patch_temp_data["data"]
            _patch_mgr_error_dict = _json_patch_temp_data["data"]["patch_mgr_error"]
            if "patch_mgr_error_detected" in _patch_mgr_error_dict:
                _patch_mgr_error_flag = _patch_mgr_error_dict["patch_mgr_error_detected"]
                if 'yes' == _patch_mgr_error_flag:
                    self.mPatchLogInfo("Patch Mgr error detected. Writing output to file")
                    # Get DBNUVersion
                    if "dbnu_version" in _patch_mgr_error_dict:
                        _dbnu_version = _patch_mgr_error_dict["dbnu_version"]
                        if _dbnu_version:
                            _final_patchmgr_error_dict["dbnuVersion"] = _dbnu_version
                        else:
                            _final_patchmgr_error_dict["dbnuVersion"] = "DBNUVersion not populated in ExaCloud db"
                    else:
                        self.mPatchLogInfo("DBNUVersion not populated in ExaCloud db")
                    # Dump patchmgr error json in file
                    if "patch_mgr_error_details" in _patch_mgr_error_dict:
                        _patch_mgr_error_details_dict = _patch_mgr_error_dict["patch_mgr_error_details"]
                        if _patch_mgr_error_details_dict:
                            _final_patchmgr_error_dict["patch_mgr_error_details"] = _patch_mgr_error_details_dict

                    #Dump Failed Node Name to jason file
                    if _json_patch_temp_data["data"]["node_progressing_status"] and "node_patching_progress_data" in _json_patch_temp_data["data"]["node_progressing_status"]:
                        _cur_patch_progressing_data = _json_patch_temp_data["data"]["node_progressing_status"]["node_patching_progress_data"]
                        for _item in _cur_patch_progressing_data:
                            if "status_details" in _item.keys():
                                _status_detail = _item["status_details"]
                                if _status_detail == 'Failed':
                                    if "node_name" in _item.keys():
                                        _failed_node_name = _item["node_name"]
                                        if _failed_node_name:
                                            _final_patchmgr_error_dict["failedNodeName"] = _failed_node_name
                                        else:
                                            _final_patchmgr_error_dict["failedNodeName"] = "node_name not populated in ExaCloud db" 

                                    if "image_version" in _item.keys():
                                        _current_version = _item["image_version"]
                                        if _current_version:
                                            _final_patchmgr_error_dict["currentVersion"] = _current_version
                                        else:
                                            _final_patchmgr_error_dict["currentVersion"] = "image_version not populated in ExaCloud db"
                                    break

                    _final_patchmgr_error_dict["exacloudDispatcherUUID"] = _master_request_uuid
                    _final_patchmgr_error_dict["exacloudThreadUUID"] = _child_request_uuid
                    _final_patchmgr_error_dict["TargetType"] = self.mGetTargetTypes()[0]
                    _final_patchmgr_error_dict["operationType"] = self.mGetTask()
                    _final_patchmgr_error_dict["clusterName"] = self.mGetRackName()
                    if self.mGetExaOcid():
                        _final_patchmgr_error_dict["exaOcid"] = self.mGetExaOcid()
                    if self.mGetControlPlaneRequestID():
                        _final_patchmgr_error_dict["Control_Plane_Request_ID"] = self.mGetControlPlaneRequestID()
                    if self.mGetMasterReqId():
                        _final_patchmgr_error_dict["statusPollingUUID_for_ecracli_status_uuid"] = self.mGetMasterReqId()

                    if _json_patch_report_data_dict:
                        # Handle the case in case error_code and error_message is present in patch report
                        if "error_code" in _json_patch_report_data_dict:
                            _error_code = _json_patch_report_data_dict["error_code"]
                            _final_patchmgr_error_dict["exacloudStatusCode"] = _error_code
                        if "error_message" in _json_patch_report_data_dict:
                            _error_message = _json_patch_report_data_dict["error_message"]
                            _final_patchmgr_error_dict["exacloudStatusMessage"] = _error_message

                    if "time_profile_data" in _json_patch_report_data_dict:
                        _time_profile_data = _json_patch_report_data_dict["time_profile_data"]
                        if "exacloud_start_time" in _time_profile_data:
                            _final_patchmgr_error_dict["request_start_time"] = _time_profile_data["exacloud_start_time"]
                        if "exacloud_end_time" in _time_profile_data:
                            _final_patchmgr_error_dict["request_end_time"] = _time_profile_data["exacloud_end_time"]

                    _ecs_version = self.mGetECSLabelInformation()
                    if _ecs_version:
                        _final_patchmgr_error_dict["ecs_label"] = _ecs_version

                    #Get targetVersion
                    _final_patchmgr_error_dict["target_version"] = self.mGetTargetVersion()

                    _exacloud_thread_log_path, _dispatcher_log_path = self.mGetExacloudThreadLogsPath(_master_request_uuid, _child_request_uuid)
                    if _exacloud_thread_log_path:
                        _final_patchmgr_error_dict["exacloudThreadLog"] = _exacloud_thread_log_path
                    if _dispatcher_log_path:
                        _final_patchmgr_error_dict["exacloudDispatcherLog"] = _dispatcher_log_path

                    #<EC_HOME>>oeda/requests/3c421000-a816-11ed-b38a-0200170158bc/log/patchmgr_logs
                    #Sample : /u02/2011drop/admin/exacloud/oeda/requests/3c421000-a816-11ed-b38a-0200170158bc/log/
                    _output_directory = None
                    if self.mGetLogPath() and os.path.isdir(self.mGetLogPath()) is True:
                        _final_patchmgr_error_dict["Patch_Mgr_log_path_on_Exacloud"] = self.mGetLogPath()
                        # self.mGetLogPath() = <EC_HOME>oeda/requests/3c421000-a816-11ed-b38a-0200170158bc/log/patchmgr_logs
                        # Get rid of the patchmgr_logs. Final path e.g /u02/2011drop/admin/exacloud/oeda/requests/3c421000-a816-11ed-b38a-0200170158bc/log/
                        _output_directory = '/'.join((self.mGetLogPath()).split("/")[:-1])
                        if _output_directory:
                            # self.mGetMasterReqId() is the ECRA Request Id
                            _exadata_patch_mgr_error_json_file = f"{_output_directory}/{self.mGetMasterReqId()}_patchmgr_error.json"
                            self.mPatchLogInfo(
                                f"Output directory for writing exadata patch mgr error json {_exadata_patch_mgr_error_json_file} ")
                            with open(_exadata_patch_mgr_error_json_file,"w") as _patch_mgr_error_fd:
                                json.dump(_final_patchmgr_error_dict, _patch_mgr_error_fd)
                        else:
                            self.mPatchLogInfo(
                                "Output directory for writing exadata patch mgr error json is not present")
                    else:
                        self.mPatchLogInfo("Patch Mgr log path on Exacloud is not Present")
                else:
                    self.mPatchLogInfo("No Patch Mgr Error detected to dump Patch mgr error file")
        else:
            self.mPatchLogInfo("JSON patch report data is not present to dump Patch mgr error file")

    def mDeleteMarkerFileFromPatchBase(self,aPatchBaseAfterUnzip, aNode=None):
        """
        This method is going to delete current infrapatching marker file that got created in patch base
        """
        try:
            if aPatchBaseAfterUnzip:
                _ecra_request_id_progress_txt_marker = os.path.join(aPatchBaseAfterUnzip,
                                                                    f"{self.mGetMasterReqId()}_progress.txt")
                if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
                    if aNode:
                        _node = exaBoxNode(get_gcontext())
                        _node.mSetUser('opc')
                        _node.mSetMaxRetries(self.mGetMaxNumberofSshRetries())
                        _node.mConnect(aHost=aNode)
                        _cmd = f'ls {_ecra_request_id_progress_txt_marker}'
                        _in, _out, _err = _node.mExecuteCmd(_cmd)
                        if _node.mGetCmdExitStatus() == 0:
                            self.mPatchLogInfo(
                                f"Deleting current infrapatch operation request marker {_ecra_request_id_progress_txt_marker} ")
                            _marker_remove_cmd = f"rm -f {_ecra_request_id_progress_txt_marker}"
                            _node.mExecuteCmd(_marker_remove_cmd)
                        if _node.mIsConnected():
                            _node.mDisconnect()
                else:
                    if self.mCheckLocalFileExists(_ecra_request_id_progress_txt_marker, aCheckWithSudo=True):
                        self.mPatchLogInfo(
                            f"Deleting current infrapatch operation request marker {_ecra_request_id_progress_txt_marker} ")
                        _marker_remove_cmd = f"/usr/bin/sudo rm -f {_ecra_request_id_progress_txt_marker}"
                        self.mGetCluControl().mExecuteCmdLog(_marker_remove_cmd)
        except Exception as e:
            self.mPatchLogWarn(f"Exception {str(e)} occurred in mDeleteMarkerFileFromPatchBase")
            self.mPatchLogTrace(traceback.format_exc())

    def mCreateMarkerFileInPatchBase(self,aPatchBaseAfterUnzip, aNode=None):
        """
        This method is going to create marker file based on current ecra request id in patch base.

        When cps node is used as launchnode, marker file need to be created in patchbase location to avoid purging of
        this directory when there is an on going infrapatch operation with the exadata version.
        Example for the marker file: /opt/oci/exacc/exacloud/InfraPatchBase/dbserver.patch.zip_exadata_ol8_23.1.3.0.0.230613_Linux-x86-64.zip/dbserver_patch_230626/7c8842b2-c907-4334-9640-9fbcd32526d8_progress.txt
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _ecra_request_id_progress_txt_marker =""
        _check = True
        try:
            if aPatchBaseAfterUnzip:
                _ecra_request_id_progress_txt_marker = os.path.join(aPatchBaseAfterUnzip,
                                                                    f"{self.mGetMasterReqId()}_progress.txt")
                if aNode:
                    _launch_node = exaBoxNode(get_gcontext())
                    _launch_node.mSetUser('opc')
                    _launch_node.mSetMaxRetries(self.mGetMaxNumberofSshRetries())
                    _launch_node.mConnect(aHost=aNode)
                    _cmd = f'printf "patching_in_progress" | sudo tee  {_ecra_request_id_progress_txt_marker}'
                    _launch_node.mExecuteCmd(_cmd)
                    _check_cmd = f'ls {_ecra_request_id_progress_txt_marker}'
                    _i, _o, _e = _launch_node.mExecuteCmd(_check_cmd)
                    _out = _o.readlines()
                    self.mPatchLogInfo(str(_out))
                    if _out:
                        self.mPatchLogInfo("\n Marker file found")
                    else:
                        self.mPatchLogInfo("\n Marker file not found")
                        _check = False
                else:
                    _marker_creation_cmd = f"/usr/bin/sudo touch {_ecra_request_id_progress_txt_marker}"
                    self.mGetCluControl().mExecuteCmdLog(_marker_creation_cmd)
                    _check = self.mCheckLocalFileExists(_ecra_request_id_progress_txt_marker, aCheckWithSudo=True)

                if not _check:
                    _ret = CURRENT_REQUEST_MARKER_NOT_FOUND_IN_PATCH_BASE
                    _suggestion_msg = f"Current infrapatch operation request marker {_ecra_request_id_progress_txt_marker} is not found."
                    self.mAddError(_ret, _suggestion_msg)
        except Exception as e:
            self.mPatchLogWarn(f"Exception {str(e)} occurred in mCreateMarkerFileInPatchBase")
            self.mPatchLogTrace(traceback.format_exc())
            _ret = CURRENT_REQUEST_MARKER_NOT_FOUND_IN_PATCH_BASE
            _suggestion_msg = f"Current infrapatch operation request marker {_ecra_request_id_progress_txt_marker} could not be located."
            self.mAddError(_ret, _suggestion_msg)
        return _ret

    def mCheckLocalFileExists(self, aFile, aCheckWithSudo=False):
        _ret = False
        if aFile:
            _ls_cmd_str = f"/usr/bin/ls {aFile}"
            _ls_cmd = _ls_cmd_str
            if aCheckWithSudo:
                _ls_cmd = f"/usr/bin/sudo {_ls_cmd_str}"
            _rc, _in, _out, _err = self.mGetCluControl().mExecuteLocal(_ls_cmd)
            if _rc == 0:
                self.mPatchLogInfo(f"File {_out} exists so returning True")
                _ret = True
        return _ret

    def mUpdateCurrentInfrapactchOperationTimeStatsToDB(self, aExacloudStartTime=None, aExacloudEndTime=None):
        """
        This method does the following
        1. Reads time stats from exacloud db which are captured with infrapatching instrumentation code.
        2. Update patch_mgr time stats with values of node_progress_data(Node_progress_data reads from patch_mgr.xml)
        3. Update patchlist table with below time_profile data for rolling scenarios

            "time_profile_data": {
                "node_patching_time_stats": [
                      {
                        "node_names": "['slcs27celadm04.us.oracle.com']",
                        "stage": "PATCH_MGR",
                        "sub_stage": "",
                        "start_time": "2022-07-21 01:55:47+0000",
                        "end_time": "2022-07-21 02:34:12+0000",
                        "duration_in_seconds": 2305
                      },
                      {
                        "node_names": "['slcs27celadm05.us.oracle.com']",
                        "stage": "PATCH_MGR",
                        "sub_stage": "",
                        "start_time": "2022-07-21 01:55:47+0000",
                        "end_time": "2022-07-21 03:03:23+0000",
                        "duration_in_seconds": 4056
                      },
                      {
                        "node_names": "['slcs27celadm06.us.oracle.com']",
                        "stage": "PATCH_MGR",
                        "sub_stage": "",
                        "start_time": "2022-07-21 01:55:47+0000",
                        "end_time": "2022-07-21 03:35:00+0000",
                        "duration_in_seconds": 5953
                      }
                     ],
                "exacloud_start_time": "2022-07-20 18:53:37-0700",
                "exacloud_end_time": "2022-07-20 20:46:53-0700"
          }
        """
        _json_patch_temp_data = None
        try:
            # 1. Read time stats from exacloud db which are captured with infrapatching instrumentation code.
            _cur_patching_time_stats_dict = {}
            _cur_patching_time_stats_dict = self.mReadInfrapactchOperationTimeStatsFromDB()

            # 1.b.  Read node_progress_data and form a dictionary with node_name as key and time_stats as value
            _cur_patch_progressing_status_json = None
            _operation_style = None
            _, _, _, _json_patch_report = self.mGetAllPatchListDetails()
            if _json_patch_report:
                _json_patch_temp_data = json.loads(_json_patch_report)
                if _json_patch_temp_data and _json_patch_temp_data["data"] :
                    if _json_patch_temp_data["data"]["node_progressing_status"]:
                        _cur_patch_progressing_status_json = _json_patch_temp_data["data"]["node_progressing_status"]
                        self.mPatchLogInfo(
                            f"mUpdateCurrentInfrapactchOperationTimeStatsToDB : node_progress_data is - {json.dumps(_cur_patch_progressing_status_json, indent=4)}")

                    if _json_patch_temp_data["data"]["operation_style"]:
                        _operation_style = _json_patch_temp_data["data"]["operation_style"]

            # _patching_time_stats_for_debug_info contains time_stats collected to display in Debuginfo
            #  This is dumpled in patchlist table
            _patching_time_stats_for_debug_info = {}

            # time_profile_data with patch_mgr time stats is required only for rolling case
            # So in case of rolling, all these time stats are calculated and for non_rolling jus dumping already calcuated time_stats into file
            if _operation_style  and _operation_style == OP_STYLE_ROLLING :
                # 2. Update patch_mgr time stats with values of node_progress_data
                _patch_mgr_time_stats_list, _non_patch_mgr_time_stats_list = self.mGetPatchmgrTimestatsWithNodeProgressData(
                    _cur_patching_time_stats_dict, _cur_patch_progressing_status_json)

                # _new_patching_time_stats_dict is used to dump time_stats into file
                _new_patching_time_stats_dict = {}

                # If time_stats are collected properly(patch_mgr timestats are updated with node_progress_data details),
                # use new time_stats otherwise use time_stats collected from exacloud DB
                #
                if _patch_mgr_time_stats_list and _non_patch_mgr_time_stats_list and len(_patch_mgr_time_stats_list) > 0:
                    for key in _cur_patching_time_stats_dict:
                        if key != "node_patching_time_stats":
                            _new_patching_time_stats_dict[key] = _cur_patching_time_stats_dict[key]

                    # Update patch_mgr stage time stats with time_stats collected with node_progress_data
                    _new_patching_time_stats_dict[
                        "node_patching_time_stats"] = _patch_mgr_time_stats_list + _non_patch_mgr_time_stats_list

                    self.mDumpCurrentInfrapactchOperationTimeStatsToFile(_new_patching_time_stats_dict)
                else:
                    self.mDumpCurrentInfrapactchOperationTimeStatsToFile(_cur_patching_time_stats_dict)


                #  3. Update patchlist table with below time_profile data for rolling scenarios for patch Debuginfo display

                if _patch_mgr_time_stats_list and len(_patch_mgr_time_stats_list) > 0:
                    _patching_time_stats_for_debug_info["node_patching_time_stats"] = _patch_mgr_time_stats_list

            else:
                # Dump time_stats to file
                self.mDumpCurrentInfrapactchOperationTimeStatsToFile(_cur_patching_time_stats_dict)

            # Update exacloud_start_time and exacloud_end_time in time_profile_date
            if aExacloudStartTime:
                _patching_time_stats_for_debug_info["exacloud_start_time"] = aExacloudStartTime
            if aExacloudEndTime:
                _patching_time_stats_for_debug_info["exacloud_end_time"] = aExacloudEndTime

            if _json_patch_temp_data and _json_patch_temp_data["data"] and _json_patch_temp_data["data"][
                "node_progressing_status"]:
                _json_patch_temp_data["data"]["time_profile_data"] = _patching_time_stats_for_debug_info
                self.mUpdatePatchReportJsonToDB(_json_patch_temp_data)
        except Exception as e:
            self.mPatchLogWarn(
                f"Exception {str(e)} occurred in mUpdateCurrentInfrapactchOperationTimeStatsToDB")
            self.mPatchLogTrace(traceback.format_exc())

    def mUpdatePatchProgressStatusForTimedOutNodes(self):
        """
        This method updates node_progress_data staus as Timeout for pending nodes when exacloud timeout error occurs.
        """
        _json_patch_temp_data = None
        try:
            # Get updated patch Report Json from Exacloud DB and update Node Progressing status
            _, _, _, _json_patch_report = self.mGetAllPatchListDetails()
            if _json_patch_report:
                _json_patch_temp_data = json.loads(_json_patch_report)
                if _json_patch_temp_data and _json_patch_temp_data["data"] and _json_patch_temp_data ["data"]["error_code"] and _json_patch_temp_data ["data"]["error_code"] == EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR :
                    if _json_patch_temp_data["data"]["node_progressing_status"]:
                        _cur_patch_progressing_status_json = _json_patch_temp_data["data"]["node_progressing_status"]
                        self.mPatchLogInfo(
                            f"Node_progress_data before updating Timeout status - {json.dumps(_json_patch_temp_data, indent=4)}")
                        if 'node_patching_progress_data' in _cur_patch_progressing_status_json.keys():
                            for _patch_progress_elem in _cur_patch_progressing_status_json['node_patching_progress_data']:
                                if "status" in _patch_progress_elem.keys() and _patch_progress_elem["status"] == "Pending":
                                    _patch_progress_elem["status"] = "TimeOut"
                        _json_patch_temp_data["data"]["node_progressing_status"] = _cur_patch_progressing_status_json
                        self.mPatchLogInfo(
                            f"Node_progress_data after updating Timeout status - {json.dumps(_cur_patch_progressing_status_json, indent=4)}")
                        self.mUpdatePatchReportJsonToDB(_json_patch_temp_data)
                    else:
                        self.mPatchLogInfo('Json Patch Report with node_progressing_status details not found.')

        except Exception as e:
            self.mPatchLogWarn(f"Exception {str(e)} occurred in mUpdatePatchProgressStatusForTimedOutNodes.")
            self.mPatchLogTrace(traceback.format_exc())

    def mUpdateImageVersionInfoDetailsInNodeProgressData(self):
        """
        This method updates node_progress_data with image version details.
        Eg data for node_patching_progress_data :
             "node_patching_progress_data": [
              {
                "node_name": "slcs27celadm04.us.oracle.com",
                "target_type": "cell",
                "patchmgr_start_time": "2022-08-29 09:47:00+0000",
                "last_updated_time": "2022-08-29 09:49:58+0000",
                "status": "Completed",
                "status_details": "Succeeded",
                "image_version": "21.2.11.0.0.220414.1",
                "image_activation_date": "2022-07-21 02:32:04 +0000",
                "image_status": "success"
              },
              {
                "node_name": "slcs27celadm05.us.oracle.com",
                "target_type": "cell",
                "patchmgr_start_time": "2022-08-29 09:47:00+0000",
                "last_updated_time": "2022-08-29 09:49:58+0000",
                "status": "Completed",
                "status_details": "Succeeded",
                "image_version": "21.2.11.0.0.220414.1",
                "image_activation_date": "2022-07-21 03:01:21 +0000",
                "image_status": "success"
              },
              {
                "node_name": "slcs27celadm06.us.oracle.com",
                "target_type": "cell",
                "patchmgr_start_time": "2022-08-29 09:47:00+0000",
                "last_updated_time": "2022-08-29 09:49:58+0000",
                "status": "Completed",
                "status_details": "Succeeded",
                "image_version": "21.2.11.0.0.220414.1",
                "image_activation_date": "2022-07-21 03:32:49 +0000",
                "image_status": "success"
              }
            ]
          }

        It does the following
        1. Get node_progress_data from exacloud db
        2. Parse each node data to get nodename and target type and get image version details
        3. Update the node_progress_data with image info details obtained in above step
        4. Update the exacloud db with updated node_progress_data
        """
        try:
            # 1. Get node_progress_data from exacloud db
            _cur_patch_progressing_status_json = None
            _json_patch_temp_data = None
            _, _, _, _json_patch_report = self.mGetAllPatchListDetails()
            if _json_patch_report:
                _json_patch_temp_data = json.loads(_json_patch_report)
                if _json_patch_temp_data and _json_patch_temp_data["data"]:
                    if _json_patch_temp_data["data"]["node_progressing_status"]:
                        _cur_patch_progressing_status_json = _json_patch_temp_data["data"]["node_progressing_status"]

            # 2. Parse each node data to get nodename and target type and get image version details
            if _cur_patch_progressing_status_json and 'node_patching_progress_data' in _cur_patch_progressing_status_json.keys():
                self.mPatchLogInfo(
                    f"mUpdateImageVersionInfoDetailsInNodeProgressData - node_progress_data is - {json.dumps(_cur_patch_progressing_status_json, indent=4)}")
                for _node_progress_data_elem in _cur_patch_progressing_status_json['node_patching_progress_data']:
                    _node_name = None
                    _target_tye = None
                    if "target_type" in _node_progress_data_elem.keys():
                        _target_tye=_node_progress_data_elem["target_type"]

                    if "node_name" in _node_progress_data_elem.keys():
                        _node_name = _node_progress_data_elem["node_name"]

                    _image_info_details = self.mGetCluPatchCheck().mGetImageVersionInfoDetails(_node_name, _target_tye)

                    # 3. Update the node_progress_data with image info details obtained in above step
                    for _image_info_key in _image_info_details.keys():
                        _node_progress_data_elem[_image_info_key] = _image_info_details[_image_info_key]


                    """
                    It could so happen that status and status_details could be set to Pending during active-active 
                    switch over of ecra rolling upgrade in mPopulateNodeProgressDataIfMissing so setting status as Completed 
                    if current version and target version are same.
                    """
                    if "image_version" in _image_info_details:
                        _target_version_from_input_payload = self.mGetTargetVersion()
                        if _target_version_from_input_payload:
                            if _image_info_details["image_version"] == _target_version_from_input_payload and "status" in _node_progress_data_elem.keys() \
                                    and _node_progress_data_elem["status"] == "Pending" and "status_details" in _node_progress_data_elem.keys() and _node_progress_data_elem["status_details"] == "Pending":
                                self.mPatchLogInfo("Updating status as completed in node progress data for nodes which are at target version and status was Pending")
                                _node_progress_data_elem["status"]="Completed"
                                _node_progress_data_elem["status_details"] =  "Succeeded"

                _json_patch_temp_data["data"]["node_progressing_status"] = _cur_patch_progressing_status_json
                self.mPatchLogInfo(
                    f"Node_progress_data after updating imageinfo details- {json.dumps(_cur_patch_progressing_status_json, indent=4)}")

                # 4. Update the exacloud db with updated node_progress_data
                self.mUpdatePatchReportJsonToDB(_json_patch_temp_data)

        except Exception as e:
            self.mPatchLogWarn(f"Exception {str(e)} occurred in mUpdateImageVersionInfoDetailsInNodeProgressData.")
            self.mPatchLogTrace(traceback.format_exc())

    def mGetPatchMgrErrorHandlingDetails(self, aNode):
        """
         This method contains changes related to Exadata error
         handling changes from Infra patching
         in case patchmgr command failure cases

         - Returns None in case patchmgr error handling json
           details are not found in the patchmgr log location.

         - Return Exadata error handling json details in case of
           patchmgr command failure and patchmgr error handling json
           details were found in the patchmgr log location.

         Example of an Exadata Error handling json file :
         {
            "Metadata": [
                {
                    "Operation": "Precheck",
                    "TargetNode[s]": "slcs27dv0305m",
                    "StartTime": "2022-09-29 11:54:06 UTC",
                    "EndTime": "2022-09-29 11:54:59 UTC",
                    "FinalStatus": "Failed",
                    "RunID": "290922115311",
                    "CommandRun": "./dbnodeupdate.sh -g -P 290922115311 -v -a -u -l exadata_ol7_21.2.14.0.0.220830_Linux-x86-64.zip -t 21.2.14.0.0.220830"
                }
            ],
            "Modules": [
                {
                    "slcs27dv0305m": {
                        "Node_type": "Target-Node",
                        "CheckAndRepairRpmdb": [
                            {
                                "Description": "Check to verify that the rpm database (RPMDB) is healthy and accessible.",
                                "Starttime": "2022-09-29 11:54:06 UTC",
                                "Endtime": "2022-09-29 11:54:06 UTC",
                                "Status": "Passed"
                            }
                        ],
                        "checkSSHTimeout": [
                            {
                                "Description": "Check to verify that the SSH server inactivity timeout is 600 seconds or greater.",
                                "Starttime": "2022-09-29 11:54:59 UTC",
                                "Endtime": "2022-09-29 11:54:59 UTC",
                                "Status": "Failed",
                                "ErrorCode": "EXAUPG-00002",
                                "ErrorMessage": "SSH server inactivity timeout is less than 600 seconds.",
                                "Cause": "The following SSH server attributes contain non-default values: ClientAliveInterval, ClientAliveCountMax.",
                                "Action": "Configure the SSH server to use the recommended values for Exadata: ClientAliveInterval=600, ClientAliveCountMax=0.",
                                "MOSUrl": "https://support.oracle.com/msg/EXAUPG-00002"
                            }
                        ]
                    }
                }
            ]
         }
        """
        _node = exaBoxNode(get_gcontext())
        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomuOrClusterless'):
            _node.mSetUser('opc')
            _node.mSetMaxRetries(self.mGetMaxNumberofSshRetries())

        try:
            _patchmgr_error_json = {}
            _patchmgr_error_json["patch_mgr_error_details"] = []
            _found_exadata_json_error = False
            _exadata_error_json_files = []
            if not self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                _node.mConnect(aHost=aNode)

            def _mget_target_json(_json_file, _node):
                '''
                 Sub function to get the required
                 Exadata patchmgr json.
                '''
                _target_json = {}
                _target_json_list = []
                _target_json_str = None
                try:
                    if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                        _cmd_list = []
                        _cmd_list.append(['sudo', 'cat', _json_file])
                        _rc, _target_json_str = runInfraPatchCommandsLocally(_cmd_list)
                    elif self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomuOrClusterless'):
                         _cmd = "cat "+_json_file
                         _i, _o, _e = _node.mExecuteCmd(_cmd)
                         _list = _o.readlines()
                         _target_json_str = ''.join([str(elem) for elem in _list])
                    else:
                        _target_json_str = _node.mReadFile(_json_file)

                    if _target_json_str:
                        _patch_mgr_error_detected = False
                        _patchmgr_error_json["patch_mgr_error_detected"] = "no"
                        _target_json = json.loads(_target_json_str)
                        for _exadata_error_json_name, _exadata_error_json_value in _target_json.items():
                            if _exadata_error_json_name and _exadata_error_json_name == "Modules":
                                for _patchmgr_error_host_list in _exadata_error_json_value:
                                    for _patchmgr_error_host, _patchmgr_error_details in _patchmgr_error_host_list.items():
                                        _patchmgr_error_status_json = {}
                                        _patchmgr_error_status_json["nodeName"] = {}
                                        _patchmgr_error_status_json["nodeType"] = {}
                                        for _patchmgr_error_code_name, _patchmgr_error_handling_details in _patchmgr_error_details.items():
                                            if _patchmgr_error_code_name:
                                                _patchmgr_error_status_json["nodeName"] = _patchmgr_error_host
                                                if _patchmgr_error_code_name == "Node_type":
                                                    _patchmgr_error_status_json["nodeType"] = _patchmgr_error_handling_details
                                                else:
                                                    for _patch_status in _patchmgr_error_handling_details:
                                                        for _error_param_name, _error_param_value in _patch_status.items():
                                                            if _error_param_name == "Status" and _error_param_value == "Failed":
                                                                _patchmgr_error_status_json[_patchmgr_error_code_name] = _patchmgr_error_handling_details
                                                                _patchmgr_error_json["patch_mgr_error_details"].append(_patchmgr_error_status_json)
                                                                _patch_mgr_error_detected = True
                            elif _exadata_error_json_name and _exadata_error_json_name == "Metadata":
                                for _item in _exadata_error_json_value:
                                    if "DBNUVersion" in _item.keys():
                                        _patchmgr_error_json["dbnu_version"] = _item["DBNUVersion"]
                                        break

                        if _patch_mgr_error_detected:
                            _patchmgr_error_json["patch_mgr_error_detected"] = "yes"

                except Exception as e:
                    self.mPatchLogWarn(
                        f"Unable to get exadata patchmgr json details from json file : {str(exadata_error_json_file)}. Error : {str(e)}")
                    self.mPatchLogTrace(traceback.format_exc())
                finally:
                    if len(_patchmgr_error_json) > 0 and _patchmgr_error_json["patch_mgr_error_detected"] == "yes":
                        self.mPatchLogInfo(
                            f"Exadata patchmgr error json details : {json.dumps(_patchmgr_error_json, indent=4)}")
                    else:
                        self.mPatchLogTrace("No Exadata error json generated on the launch node patchmgr log location. No Exadata error handling details will be forwarded to status call output.")
                    return _patchmgr_error_json

                # End of _mget_target_json method

            '''
             Fetch error details from Exadata error handling json files

              [root@slcs27adm03 ~]# ls /EXAVMIMAGES/dbserver.patch.zip_exadata_ovs_22.1.3.0.0.220914_Linux-x86-64.zip/
              dbserver_patch_220928/patchmgr_log_f272ca90-a456-4ed9-98ec-f340cc2b3136_slcs27adm03/drivernode_*.json 
              /EXAVMIMAGES/dbserver.patch.zip_exadata_ovs_22.1.3.0.0.220914_Linux-x86-64.zip/dbserver_patch_220928/
              patchmgr_log_f272ca90-a456-4ed9-98ec-f340cc2b3136_slcs27adm03/targetnode_*.json
              /EXAVMIMAGES/dbserver.patch.zip_exadata_ovs_22.1.3.0.0.220914_Linux-x86-64.zip/dbserver_patch_220928/
              patchmgr_log_f272ca90-a456-4ed9-98ec-f340cc2b3136_slcs27adm03/drivernode_slcs27adm03_Precheck_details_081122055207.json
              /EXAVMIMAGES/dbserver.patch.zip_exadata_ovs_22.1.3.0.0.220914_Linux-x86-64.zip/dbserver_patch_220928/
              patchmgr_log_f272ca90-a456-4ed9-98ec-f340cc2b3136_slcs27adm03/targetnode_slcs27adm04_Precheck_details_081122055207.json
              [root@slcs27adm03 ~]#
            '''
            _exadata_error_json_files = None
            _get_list_of_exadata_error_json_files_cmd = f"ls {self.mGetPatchmgrLogPathOnLaunchNode()}*/drivernode_*.json {self.mGetPatchmgrLogPathOnLaunchNode()}*/targetnode_*.json"
            _list_of_exadata_error_json_files_cmd1_glob = self.mGetPatchmgrLogPathOnLaunchNode() + "*/drivernode_*.json "
            _list_of_exadata_error_json_files_cmd2_glob = self.mGetPatchmgrLogPathOnLaunchNode() + "*/targetnode_*.json"
            if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                _exadata_error_json_files = \
                    glob.glob(_list_of_exadata_error_json_files_cmd1_glob) + glob.glob(_list_of_exadata_error_json_files_cmd2_glob)
                if not _exadata_error_json_files:
                    _sleep_monitor_iteration_count = 0
                    # Max sleep time is 20 seconds
                    while _sleep_monitor_iteration_count < 4:
                        _exadata_error_json_files = \
                            glob.glob(_list_of_exadata_error_json_files_cmd1_glob) + glob.glob(
                                _list_of_exadata_error_json_files_cmd2_glob)
                        if _exadata_error_json_files:
                            break
                        else:
                            _sleep = 5
                            time.sleep(_sleep)
                            _sleep_monitor_iteration_count += 1
                            self.mPatchLogInfo(f"**** Iteration : [{_sleep_monitor_iteration_count:d}/4] - Patchmgr error json check is executed again in {_sleep} seconds.")
            else:
                _in, _out, _err = _node.mExecuteCmd(_get_list_of_exadata_error_json_files_cmd)
                if _out:
                    _exadata_error_json_files = _out.readlines()
                else:
                    _sleep_monitor_iteration_count = 0
                    # Max sleep time is 20 seconds.
                    while _sleep_monitor_iteration_count < 4:
                        _in, _out, _err = _node.mExecuteCmd(_get_list_of_exadata_error_json_files_cmd)
                        if _out:
                            _exadata_error_json_files = _out.readlines()
                            break
                        else:
                            _sleep = 5
                            time.sleep(_sleep)
                            _sleep_monitor_iteration_count += 1
                            self.mPatchLogInfo(f"Patchmgr error json check is polled for another {_sleep} seconds with iteration : [{_sleep_monitor_iteration_count:d}/4]")

            if  not _exadata_error_json_files:
                self.mPatchLogError("No Exadata error json on the launch or target json generated even after waiting for 20 seconds. Error logs for patchmgr error will not be collected.")
                return _patchmgr_error_json

            if len(_exadata_error_json_files) > 0:
                for exadata_error_json_file in _exadata_error_json_files:
                    _file_exists = False
                    exadata_error_json_file = exadata_error_json_file.strip()
                    _is_cps = self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU')
                    _file_exists = mCheckFileExists(exadata_error_json_file, _is_cps, _node)
                    if _file_exists:
                        _patchmgr_error_json = _mget_target_json(exadata_error_json_file, _node)
                        if _patchmgr_error_json and len(_patchmgr_error_json) != 0:
                            _found_exadata_json_error = True

                    '''
                     Due to infra patching idempotency feature, there are possible cases 
                     in which patchmgr log directory could be renamed at the end of patching.
                     To handle that scenario, we are checking for exadata error json in the 
                     new location if not found in the initial patchmgr log location.
                    '''
                    exadata_error_json_file_idempotent_location = exadata_error_json_file.strip() + '_' + aNode
                    _file_exists = mCheckFileExists(exadata_error_json_file_idempotent_location, _is_cps, _node)
                    if _file_exists and not _found_exadata_json_error:
                        _patchmgr_error_json = _mget_target_json(exadata_error_json_file_idempotent_location, _node)

        except Exception as e:
            self.mPatchLogWarn("\nException in writing Exadata Error handing details to Exacloud DB")
            self.mPatchLogTrace(traceback.format_exc())

        finally:
            if _node.mIsConnected():
                _node.mDisconnect()
            return _patchmgr_error_json

    def mGetReachableDomuList(self, aDomUList):
        """
         Note: This is used to get connectible vm list during dom0 patching

         This method returns a list of VMs accessible
         from exacloud node. Keys will be injected to VMs
         during patching in this case.

        """
        
        _domu_accessible_using_keys = []
        _domu_not_accessible_using_keys = []
        _timeout_ssh_connection = mGetSshTimeout()
        _use_root, _use_opc = False, False
        _user_to_vm_accessibility_mapping = {}

        if len(aDomUList) == 0:
            return _domu_accessible_using_keys, _domu_not_accessible_using_keys

        self.mPatchLogInfo(
            f"List of VMs validated to be accessible from Exacloud node : {json.dumps(aDomUList, indent=4)}")

        _node = exaBoxNode(get_gcontext())
        for _domu in aDomUList:
            _user_to_vm_accessibility_mapping[_domu] = []
            try:
                '''
                 Below assumption is made based on a fact that only
                 opc keys are available on EXACS environments and
                 both opc/root keys are available on EXACC.
                '''
                if self.mIsExaCC():
                    _use_root, _use_opc = self.mExecuteCrsCommandUsingRootOrOpcUser(_domu, _node)
                else:
                    _use_root, _use_opc = self.mExecuteCrsCommandUsingRootOrOpcUser(_domu, _node, aCheckRoot=False)
                 
                if _use_root or _use_opc:
                    _domu_accessible_using_keys.append(_domu)
                    '''
                     VM may or may not be accessible using both root or opc keys.
                     In case of VM already accessible with root keys, opc user accessibility
                     details are not included to _user_to_vm_accessibility_mapping.
                    '''
                    if _use_root:
                        _user_to_vm_accessibility_mapping[_domu].append("root")
                    if _use_opc:
                        _user_to_vm_accessibility_mapping[_domu].append("opc")

                '''
                 In case of DomU not accessible neither through opc nor
                 root, append to below list. CRS based validation both 
                 during pre and post patching will be skipped on the 
                 below list of DomUs.
                '''
                if not _use_root and not _use_opc:
                    _domu_not_accessible_using_keys.append(_domu)                

                '''
                 mGetUserToNodeMappingToRunCrsCmds can be used to get user to DomU accessibility mapping details.
                '''
                if len(_user_to_vm_accessibility_mapping) > 0:
                    self.mSetUserToNodeMappingToRunCrsCmds(_user_to_vm_accessibility_mapping)

            except Exception as e:
                self.mPatchLogWarn(
                    f"Unable to access DomU : {str(_domu)} from Exacloud host within Timeout : {str(_timeout_ssh_connection)} seconds. \n\n")
                self.mPatchLogTrace(traceback.format_exc())

        if len(_domu_accessible_using_keys) > 0:
            self.mPatchLogInfo(
                f"List of VMs accessible using keys : {json.dumps(_domu_accessible_using_keys, indent=4)}")

        if len(_domu_not_accessible_using_keys) > 0:
            self.mPatchLogInfo(
                f"List of VMs not accessible using keys : {json.dumps(_domu_not_accessible_using_keys, indent=4)}")

        return _domu_accessible_using_keys, _domu_not_accessible_using_keys

    def mExecuteCrsCommandUsingRootOrOpcUser(self, aDomUHostName, aNodeContext, aCheckRoot=True, aCheckOpc=True):
        """
         This function checks if a command on DomU could be executed either using 'root/opc' 
         user. It returns _use_root and _use_opc to True or False
         depending on whether the SSH connection works.
         - Connectivity to the nodes are checked using crsctl config crs command
         - aNodeContext in the exabox getContext here.
        """
        _use_root = False
        _use_opc = False
        _domU = aNodeContext
        _user_to_vm_accessibility_mapping = {}
        _cmd = None
        try:
            def _execute_crs_cmds_using_root_or_opc_user(_node, aDomU):
                '''
                 Please note that in case of CRS binaries are corrupted,
                 crsctl config crs can return non zero exit status and 
                 the return would be a False.

                 Advantage in validating crsctl command run is to ensure
                 that crsctl binaries are intact and also indicate if the
                 command execution is successful based on access control
                 set to users by customer.
                '''
                _cmd = None
                try:
                    _node.mConnect(aHost=aDomU)
                    '''
                     In case of CRS home not available or unable to run crsctl commands.
                     return would be False and the current node would be discarded.
                    '''
                    _ret, _cmd = self.mGetCRSHelper().mGenCrsctlCmd(_node, "config crs", aDomU)
                    if _ret == DOMU_INVALID_CRS_HOME:
                        self.mPatchLogWarn(f"mExecuteCrsCommandUsingRootOrOpcUser - Error encountered while validating crs command path on DomU - {str(aDomU)}.")
                        return False

                    if _cmd:
                        _in, _out, _err = _node.mExecuteCmd(_cmd)
                        _output = _out.readlines()
                        _error = _err.readlines()
                        if _output:
                            self.mPatchLogInfo(f"mExecuteCrsCommandUsingRootOrOpcUser - crsctl command output details run using {_node.mGetUser()} user on DomU - {aDomU} - {str(_output)}.")
                        if _error:
                            self.mPatchLogInfo(f"mExecuteCrsCommandUsingRootOrOpcUser - crsctl command error details user - {str(_error)}. crsctl command was run using {_node.mGetUser()} user on DomU - {aDomU}.")

                        _exit_code = int(_node.mGetCmdExitStatus())
                        if int(_exit_code) == 0:
                            return True
                        else:
                            return False
                    else:
                        self.mPatchLogWarn(f'mExecuteCrsCommandUsingRootOrOpcUser - Unable to generate crsctl test commands using {_node.mGetUser()} on VM - {aDomU}')
                    
                except Exception as e:
                    if _cmd is not None:
                        self.mPatchLogWarn(f'mExecuteCrsCommandUsingRootOrOpcUser - Unable to run {_cmd} command using {_node.mGetUser()} user on VM - {aDomU}')
                    else:
                        self.mPatchLogWarn(f'mExecuteCrsCommandUsingRootOrOpcUser - Unable to generate crsctl test commands using {_node.mGetUser()} on VM - {aDomU}')
                    self.mPatchLogTrace(traceback.format_exc())
                    return False
                finally: 
                    if _node.mIsConnected():
                         _node.mDisconnect()
             
            '''
             Try running commands on DomU using root user only when aCheckRoot
             flag is enabled.
            '''
            if aCheckRoot:
                # Unless reset, mGetUser will have the previously set user details.
                _domU.mSetUser('root')
                if _execute_crs_cmds_using_root_or_opc_user(_domU, aDomUHostName):
                    self.mPatchLogInfo(f"VM - {aDomUHostName} is accessible using root keys.")
                    _use_root = True
                else:
                    _suggestion_msg = f"Unable to access VM {aDomUHostName} using root keys"
                    if self.mGetCurrentTargetType() == PATCH_DOM0 and self.mGetTask() == TASK_PREREQ_CHECK:
                        self.mPatchLogWarn(f"mExecuteCrsCommandUsingRootOrOpcUser: {_suggestion_msg}")
                    else:
                        self.mPatchLogError(f"mExecuteCrsCommandUsingRootOrOpcUser: {_suggestion_msg}")

            # Try running commands on DomU with opc user in case of root user fails.
            if aCheckOpc:
                # Unless reset, mGetUser will have the previously set user details.
                _domU.mSetUser('opc')
                _domU.mSetMaxRetries(self.mGetMaxNumberofSshRetries())
                if _execute_crs_cmds_using_root_or_opc_user(_domU, aDomUHostName):
                    self.mPatchLogInfo(f"VM - {aDomUHostName} is accessible using opc keys.")
                    _use_opc = True
                else:
                    _suggestion_msg = f"Unable to access VM {aDomUHostName} using opc keys"
                    if self.mGetCurrentTargetType() == PATCH_DOM0 and self.mGetTask() == TASK_PREREQ_CHECK:
                        self.mPatchLogWarn(f"mExecuteCrsCommandUsingRootOrOpcUser: {_suggestion_msg}")
                    else:
                        self.mPatchLogError(f"mExecuteCrsCommandUsingRootOrOpcUser: {_suggestion_msg}")

        except Exception as e:
            self.mPatchLogWarn(
                f"mExecuteCrsCommandUsingRootOrOpcUser: Failed to execute commands as root or opc user on DomU : {str(aDomUHostName)}. Error {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            return _use_root, _use_opc

    def mGetUsertoConnectWith(self, aDomU, aNode):
        """
         This method verifies for both root/opc user
         access on EXACC environments and opc user access
         on EXACS environments. 

         It returns:
            <username>: if user 'root/opc' exist and able to connect.
            None: if user 'root/opc' exist and not able to connect.
        """
        _user_to_vm_accessibility_mapping = {}
        _user_to_vm_accessibility_mapping[aDomU] = []
        if self.mIsExaCC():
            # Validate for both root and opc user access on EXACC environments.
            _use_root, _use_opc = self.mIsRootOrOpcUserExists(aDomU, aNode)
        else:
            # Validate for only opc user access on EXACS environments.
            _use_root, _use_opc = self.mIsRootOrOpcUserExists(aDomU, aNode, aCheckRoot=False)

        if _use_root or _use_opc:
            '''
             VM may or may not be accessible using both root or opc keys.
             In case of VM already accessible with root keys, opc user accessibility
             details are not included to _user_to_vm_accessibility_mapping.
            '''
            if _use_root:
                _user_to_vm_accessibility_mapping[aDomU].append("root")
            if _use_opc:
                _user_to_vm_accessibility_mapping[aDomU].append("opc")

        '''
         mGetUserToNodeMappingToRunPlugins can be used to get user to DomU accessibility mapping details.
        '''
        if len(_user_to_vm_accessibility_mapping) > 0:
            self.mSetUserToNodeMappingToRunPlugins(_user_to_vm_accessibility_mapping)
    
        if _use_root:
            return 'root'
        elif _use_opc:
            return 'opc'
        else:
            if self.mIsExaCC():
                self.mPatchLogError(f"VM - {aDomU} is not accessible neither using root nor opc keys.")
            else:
                self.mPatchLogError(f"VM - {aDomU} is not accessible using opc keys.")
            return None

    def mIsRootOrOpcUserExists(self, aDomUHostName, aNode, aCheckRoot=True, aCheckOpc=True):
        """
         This function checks if a DomU is accessible either using 'root/opc' user.
         It returns _use_root and _use_opc to True or False 
         depending on whether the SSH connection works.
        """
        _use_root = False
        _use_opc = False
        _domU = aNode
        try:
            '''
             Try connecting using root user only when aCheckRoot
             flag is enabled.
            '''
            if aCheckRoot:
                # Unless reset, mGetUser will have the previously set user details.
                _domU.mSetUser('root')
                if _domU.mIsConnectable(aHost=aDomUHostName, aTimeout=20, aKeyOnly=True):
                    self.mPatchLogInfo(f"VM - {aDomUHostName} is accessible using root keys.")
                    _use_root = True
                else:
                    _suggestion_msg = f"Unable to access VM {aDomUHostName} using root keys"
                    if self.mGetCurrentTargetType() == PATCH_DOM0 and self.mGetTask() == TASK_PREREQ_CHECK:
                        self.mPatchLogWarn(f"mIsRootOrOpcUserExists: {_suggestion_msg}")
                    else:
                        self.mPatchLogError(f"mIsRootOrOpcUserExists: {_suggestion_msg}")

            # Try connecting with opc user in case of root user access fails.
            if aCheckOpc:
                # Unless reset, mGetUser will have the previously set user details.
                _domU.mSetUser('opc')
                _domU.mSetMaxRetries(self.mGetMaxNumberofSshRetries())
                if _domU.mIsConnectable(aHost=aDomUHostName, aTimeout=20, aKeyOnly=True):
                    self.mPatchLogInfo(f"VM - {aDomUHostName} is accessible using opc keys.")
                    _use_opc = True
                else:
                    _suggestion_msg = f"Unable to access VM {aDomUHostName} using opc keys"
                    if self.mGetCurrentTargetType() == PATCH_DOM0 and self.mGetTask() == TASK_PREREQ_CHECK:
                        self.mPatchLogWarn(f"mIsRootOrOpcUserExists: {_suggestion_msg}")
                    else:
                        self.mPatchLogError(f"mIsRootOrOpcUserExists: {_suggestion_msg}")

        except Exception as e:
            self.mPatchLogWarn(
                f"mIsRootOrOpcUserExists: Failed to connect as root or opc user on DomU : {str(aDomUHostName)}. Error {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            return _use_root, _use_opc

    def mIsOpcUserExists(self, aNode):
        """
        This function checks whether we can connect as 'opc' or not to a node
        It returns:
           True: if user 'opc' exist and able to connect
           False: if user 'opc' does not exist and not able to connect.
        """

        _domU = exaBoxNode(get_gcontext())
        _domU.mSetUser('opc')
        _domU.mSetMaxRetries(self.mGetMaxNumberofSshRetries())

        ret = True
        try:
            if not _domU.mIsConnectable(aHost=aNode, aTimeout=20, aKeyOnly=True):
                _suggestion_msg = f"Unable to access VM {aNode} using opc keys"
                if self.mGetCurrentTargetType() == PATCH_DOM0 and self.mGetTask() == TASK_PREREQ_CHECK:
                    self.mPatchLogWarn(f"{_suggestion_msg}")
                else:
                    self.mPatchLogError(f"{_suggestion_msg}")
                ret = False
        except Exception as e:
            self.mPatchLogWarn(
                f"mIsOpcUserExists: Failed to connect as opc user on DomU : {str(aNode)}. Error {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            ret = False
        finally:
            return ret

    def mGetDbNodesFileName(self):
        """
        This function returns the dbnodes file name which gets passed to patchmgr
        """
        return "node_list_" + self.mGetMasterReqId()

    def mReturnExecOutput(self, aCmd, aConnNode):
        output = ""
        _i, _o, _e = aConnNode.mExecuteCmd(aCmd)
        if aConnNode.mGetCmdExitStatus() == 0:
            _out = _o.readlines()
            if _out:
                output = _out[0].strip()
        else:
            ebLogInfo(f"*** Failed to execute the command : {aCmd} \n The error found : {_e}")
        return output          

    def mPrintEnvRelatedDebugStatements(self):
        if len(self.__mListOfStatementsToPrint) > 0:
            for _messagetype, _message in self.__mListOfStatementsToPrint:
                if _messagetype == "INFO":
                    self.mPatchLogInfo(f"{str(_message)}")
                elif _messagetype == "WARN":
                    self.mPatchLogWarn(f"{str(_message)}")
                elif _messagetype == "DEBUG":
                    self.mPatchLogDebug(f"{str(_message)}")
                elif _messagetype == "ERROR":
                    self.mPatchLogError(f"{str(_message)}")
                elif _messagetype == "TRACE":
                    self.mPatchLogTrace(f"{str(_message)}")

    def mCopyFileFromRemote(self, aNode, aRemotePath, aLocalPath, aCopytoTmp=False, aUser=None):
        """
        This method copies the file from remote node to exacloud location
        aUser is used to specify teh opc user to set mSetUser
        If aCopytoTmp is set to True, first it copies the file to /tmp location and then copies back to exacloud location
        """
        _remote_path = aRemotePath
        _node = exaBoxNode(get_gcontext())
        if aUser:
            _node.mSetUser(aUser)
            _node.mSetMaxRetries(self.mGetMaxNumberofSshRetries())
            
        try:
            _node.mConnect(aHost=aNode)
            if aCopytoTmp:
                _file_name = os.path.basename(aRemotePath)
                _remote_path = f"/tmp/{aNode}_{_file_name}"
                _node.mExecuteCmd(f"cat  {aRemotePath} > {_remote_path}")
            if _node.mFileExists(_remote_path):
                _node.mCopy2Local(_remote_path, aLocalPath)
            else:
                self.mPatchLogWarn(f"{_remote_path} does not exist on the node {aNode}")
        except Exception as e:
            self.mPatchLogWarn(f"mCopyFileFromRemote: Exception {str(e)} occurred while copying the file {_remote_path}"
                               f" on node {str(aNode)} to {aLocalPath}")

        finally:
            if _node.mIsConnected():
                _node.mDisconnect()

    def mGetDomuListByClusterStorageType(self, aClusterStorageType):
        _domu_list = []
        if self.__dom0domuDetails:
            for dom0HostnamefromEcra, domuHostListFromEcra in self.__dom0domuDetails.items():
                for dom0HostnameFromEcraDict, domUHostnameList in domuHostListFromEcra.items():
                    for _domuDetails in domUHostnameList:
                        if "clusterStorageType" in _domuDetails.keys():
                            _storageType = _domuDetails["clusterStorageType"]
                            if _storageType and aClusterStorageType == _storageType:
                                _domu_name = _domuDetails["customerHostname"]
                                _domu_list.append(_domu_name)
                                self.mPatchLogInfo(f"{_domu_name} is {_storageType}-cluster based")
        return _domu_list

    def mUpdatePatchListRequestStatus(self, aReturnCodefromPatch):
        #Master and child request are same for single thread patching
        _master_request_uuid = self.__cluctrl.mGetRequestObj().mGetUUID()
        _child_request_uuid = _master_request_uuid
        _db = ebGetDefaultDB()
        if (aReturnCodefromPatch is None) or (aReturnCodefromPatch != PATCH_SUCCESS_EXIT_CODE):
            _db.mUpdateChildRequestStatus(_master_request_uuid, _child_request_uuid, 'Failed')
        else:
            _db.mUpdateChildRequestStatus(_master_request_uuid, _child_request_uuid, 'Done')

    def mComputeSha256Checksum(self, aFile):
        """
        Compute the SHA256 checksum of a given local file.

        Args:
            aFile (str): Path to the local file.

        Returns:
            str: SHA256 checksum of the local file, or None if computation fails.
        """
        _local_file_checksum = None
        # Define possible paths for sha256sum command
        _sha256sum_cmd_paths = ['/bin/sha256sum', '/usr/bin/sha256sum']
        _awk_cmd = "/bin/awk '{print $1}'"

        # Find the available sha256sum command path
        _sha256sum_cmd = next((_path for _path in _sha256sum_cmd_paths if os.path.isfile(_path)), None)
        if _sha256sum_cmd is None:
            # Handle the case when sha256sum command is not found
            self.mPatchLogError(f"sha256sum command is not found")
            return _local_file_checksum

        _cmd = f"{_sha256sum_cmd} {aFile}"
        _in, _out, _err = self.mGetCluControl().mExecuteCmd(_cmd)
        if _out:
            # Extract the SHA256 checksum from the command output using AWK
            _in, _out, _err = self.mGetCluControl().mExecuteCmd(_awk_cmd, aStdIn=_out)
            if _out:
                _local_file_checksum = _out.read().strip()
            else:
                # Log an error message if the AWK command output is empty
                self.mPatchLogError("Failed to extract SHA256 checksum from command output")
        else:
            self.mPatchLogError(f"sha256sum command output is empty")
        return _local_file_checksum
   
    def mParallelDomUShutdownAcrossAllDom0(self, aDom0DomUPair):

        """
        This function shuts down all the dom0 and their corresponding domu in parallel
        """
        _rc = PATCH_SUCCESS_EXIT_CODE
        _plist = ProcessManager()
        _rc_status = _plist.mGetManager().list()
        if aDom0DomUPair:
            _dpairs = aDom0DomUPair
            self.mPatchLogInfo("Dom0 DomU Pair considered for shutdown operation:\n")
            for _dom0, _domU in aDom0DomUPair:
                self.mPatchLogInfo(f"Dom0: {_dom0}, DomU: {_domU} ; ")
        else:
            self.mPatchLogError(f"No VM List specified for non rolling shutdown.")
            return _rc

        def mShutDownDomU(aDom0Name, aDomU, aRcStatus):
            # Do VM Reboot
            with connect_to_host(aDom0Name, get_gcontext()) as _node0:
                _vm_ctl_handle = exaBoxOVMCtrl(aCtx=get_gcontext(), aNode=_node0)
                self.mPatchLogInfo(f"Shutdown vm '{aDomU}' on dom0 '{aDom0Name}'")
                _ret = _vm_ctl_handle.mShutdownVM(aDomU)

                if _ret != 0:
                    # If shutdown return non-zero
                    _shutdown_successful = False
                    self.mPatchLogError(f'*** mShutDownVMs: Shutdown operation failed on {aDomU}')
                    aRcStatus.append({'domu': aDomU, 'status': 'failed'})

                _vm_ctl_handle.mRefreshDomUs()
                if not aDomU in _vm_ctl_handle.mGetDomUs():
                    self.mPatchLogInfo(f'*** mShutDownVMs: Completed Shutdown of VM: {aDomU}')
                else:
                    _shutdown_successful = False
                    self.mPatchLogError(f'*** mShutDownVMs: Shutdown not completed in-time on {aDomU}')
                    aRcStatus.append({'domu': aDomU, 'status': 'failed'})

        # Parallelize execution on dom0s
        for _dom0, _domU in _dpairs:
            _p = ProcessStructure(mShutDownDomU,[_dom0, _domU, _rc_status], f"{_dom0}-{_domU}")
            '''
                Timeout parameter configurable in Infrapatching.conf
                Currently it is set to 60 minutes
            '''

            _p.mSetMaxExecutionTime(self.mGetDomUShutdownWaitTimeoutInSeconds()) # 60 minutes
            _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
            _p.mSetLogTimeoutFx(self.mPatchLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()

        # Validate the return codes of shutdown.
        _rc_all = True

        for _node_status in _rc_status:
            if _node_status['status'] == 'failed':
                _rc_all &= False
                self.mPatchLogError(f"Shutdown of VM '{_node_status['domu']}' is not successful.")

        if _rc_all:
            self.mPatchLogInfo("Shutdown of VMs during dom0 non-rolling upgrade is successful.")
        else:
            self.mPatchLogError("Shutdown of VMs during dom0 non-rolling upgrade failed.")
            _rc = DOM0_FAILED_TO_SHUTDOWN_VMS
            return _rc

        return _rc

    def mParallelShutdownAllDomUinDom0(self, aDom0List, aDom0DomUList):

        """
        This function shuts down all the domus within a dom0 in parallel
        """
        _processes = ProcessManager()
        _rc_status = _processes.mGetManager().list()
        _rc = PATCH_SUCCESS_EXIT_CODE
        for _dom0 in aDom0List:
            """
            If the graceful shutdown of the VM does not happen,
            xm destroy/virsh destroy would be called.
            """
            _p = ProcessStructure(self.mGetCluPatchCheck().mShutDownVMs,
                                  [_dom0, aDom0DomUList[_dom0], _rc_status], _dom0)

            '''
                Timeout parameter configurable in Infrapatching.conf
                Currently it is set to 60 minutes
            '''
            _p.mSetMaxExecutionTime(self.mGetDomUShutdownWaitTimeoutInSeconds())

            _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
            _p.mSetLogTimeoutFx(self.mPatchLogWarn)
            _processes.mStartAppend(_p)

        _processes.mJoinProcess()

        # Validate the return codes of shutdown.
        _rc_all = True

        for _node_status in _rc_status:
            if _node_status['status'] == 'failed':
                _rc_all &= False
                self.mPatchLogError(f"Shutdown of VM '{_node_status['domu']}' is not successfull.")

        if not _rc_all:
            _suggestion_msg = "Shutdown VMs during dom0 non-rolling upgrade failed. Failure reason for shutdown of VM's needs to be investigated."
            _rc = DOM0_FAILED_TO_SHUTDOWN_VMS
            self.mAddError(_rc, _suggestion_msg)
            _dom0.mDisconnect()

        return _rc
