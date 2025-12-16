#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/mockTargetHandler/dom0mockhandler.py /main/5 2025/12/02 17:57:52 ririgoye Exp $#
#
# dom0mockhandler.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      dom0mockhandler.py - Patch - Dom0 Basic Functionality
#    DESCRIPTION
#      Provide basic/core dom0 patching API (prereq, patch, backup,
#      rollback) for managing the Exadata patch operation in the cluster
#      implementation.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#       ririgoye 11/26/25 - Bug 38699725 - EXACLOUD - FIX PYLINT ERRORS FOR
#                           MIGRATE TO OL8 IN ECS
#       emekala  10/25/24 - ENH 37070223 - SYNC MOCK HANLDERS WITH LATEST CODE
#                           FROM CORE INFRAPATCHING HANDLERS AND ADD SUPPORT
#                           FOR CUSTOM RESPONSE AND RACK DETAILS
#    araghave    10/08/24 - Enh 36505637 - IMPROVE POLLING MECHANISM IN CASE
#                           OF INFRA PATCHING OPERATIONS
#    diguma      10/08/24   bug 37130040 - EXACC:BB:EXASCALE:DOM0 PATCHING 
#                           FAILS WITH ERROR "EXCEPTION IN RUNNING DOM0 PATCH 
#                           TIME DATA '2024-10' DOES NOT MATCH FORMAT 
#                           '%Y-%M-%DT%H:%M:%S'"
#    sdevasek    09/23/24 - ENH 36654974 - ADD CDB HEALTH CHECKS DURING DOM0
#                           INFRA PATCHIN
#    araghave    09/16/24 - Enh 36971721 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE TARGET HANDLER FILES
#    antamil     09/11/24 - bug 37028789 Fix for all discarded nodes to be 
#                           skipped for precheck
#    araghave    09/11/24 - Bug 37030766 - WHEN CRS IS DOWN IN ONE OF THE DOMU,
#                           SAME DOMU NAME IS BEING PRINTED TWICE IN LIST
#    araghave    08/30/24 - ER 36977545 - REMOVE SYSTEM FIRST BOOT IMAGE
#                           SPECIFIC CODE FROM INFRA PATCHING FILES
#    diguma      08/26/24 - bug 36975348: NEED A NEW INDICATOR OF GI STACK
#                           TO BE STARTED IN EXASCALE BASED CLUSTERS
#    emekala     08/28/24 - BUG 36978473 - WHEN CRS DISABLED IS EXPECTED ON ONE
#                           OR MORE NODES DOM0 POST PATCHING SHOULD NOT RETURN
#                           FAILURE RETURN CODE
#    diguma      08/21/24 - bug 36871736:REPLACE EXASPLICE WITH ELU(EXADATA
#                           LIVE UPDATE) FOR EXADATA 24.X
#    emekala     08/13/24 - ENH 36679949 - REMOVE OVERHEAD OF INDEPENDENT
#                           MONITORING PROCESS FROM INFRAPATCHING
#    diguma      07/31/24 - Bug 36908409: NEED INDICATOR OF CLUSTER STORAGE
#                           TYPE IN THE EXACLOUD PAYLOAD
#    araghave    08/06/24 - Bug 36896213 - MULTIPLE PATCHING FAILURE FOR OTM
#                           TENANCY |UNABLE TO ESTABLISH HEARTBEAT ON THE CELLS
#    bhpati      08/02/24 - Bug 36802587 - AIM4ECS:0X03110003 - PATCHMGR
#                           SESSION IS ACTIVE ON THE PRIMARY CPS NODE.
#    araghave    08/02/24 - Bug 36907132 - EXACC:BB:GRANULAR: DOM0 PRECHECK
#                           FAILS WITH ERROR IN CASE OF NO NODES AVAILABLE TO
#                           RUN PRECHECK
#    avimonda    07/24/24 - Bug 36563684 - AIM4EXACLOUD:0X03040001 - VM PRECHECK
#                           EXCEPTION DETECTED. (23.4.1.2.1-DOMU)
#    emekala     07/19/24 - ENH 36794217 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE EXACOMPUTE AND DOMU PATCHMGR CMDS
#    araghave    07/15/24 - Enh 36830077 - CLEANUP KSPLICE CODE FROM
#                           INFRAPATCHING FILES
#    emekala     06/24/24 - ENH 36748433 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE DOM0, CELL, IBSWITCH AND ROCESWITCH PATCHMGR
#                           CMDS
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    emekala     06/06/24 - ENH 36619025 - BUILD PATCHMGR AS AN OBJECT
#    diguma      06/04/24 - Bug 36691192: IN CASE OF ADBS, DURING DOM0/KVM HOST
#                           INFRA PATCHING RETRY EXECUTE DOM0DOMU PLUGIN
#    araghave    05/23/24 - Bug 36640067 - EXACS | EXASPLICE PRECHECK IS
#                           FAILING WHERE EXASPLICE IS NOT APPLICABLE
#    araghave    05/07/24 - Bug 36543876 - ERROR OUT WHEN GRID HOME PATH BINARY
#                           DOES NOT EXISTS FOR CRS AUTOSTART ENABLED CHECK
#    araghave    04/19/24 - ER 36452945 - TERMINATE INFRA PATCHING THREAD EARLY
#                           IN CASE OF PATCHMGR COMMAND DID NOT RUN
#    araghave    03/13/24 - Enh 36270822 - EXECUTION OF EXACLOUD PLUGINS USING
#                           INFRA PATCHING PLUGIN METADATA
#    emekala     03/12/24 - ENH 35494282 - ENABLE AND LOG CRS AND HA CHECK
#                           ERRORS DURING DOM0 PATCH PRECHECK AS WARNINGS
#    araghave    03/08/24 - Enh 35410482 - APPLY EXASPLICE ON ELIGIBLE DOM0
#                           NODES AND PROCEED TO APPLY CELL MONTHLY PATCH
#    araghave    02/28/24 - Enh 36295801 - IMPLEMENT ONEOFFV2 PLUGIN EXACLOUD
#                           CHANGES
#    araghave    02/08/24 - Enh 36234905 - ENABLE SERVICESTATE OF INFRA ILOM
#                           DURING UPGRADE & DISABLE THEM AFTER UPGRADE
#    araghave    01/24/24 - Enh 36219869 - SKIP INACTIVE VERSION CHECK DURING
#                           PATCH CLEANUP IN CASE OF NEWLY PROVISIONED
#                           ENVIRONMENTS
#    araghave    01/18/24 - Enh 34708925 - AVOID COPYING SYSTEM.IMG DURING
#                           PATCHING
#    araghave    12/11/23 - Bug 36030818 - PATCHMGR LOGS NOT AVAILABLE ON
#                           DRIVING NODES
#    araghave    12/06/23 - Enh 36069257 - EXACC GEN 2 | MODIFY THE TIME SPENT
#                           IN CHECKING CRS AVAILABILITY ON GUEST VM NODES THAT
#                           ARE NOT ACCESSIBLE
#    araghave    28/11/23 - Bug 36011741 - EXACC GEN 2 | INFRA PATCHING | QMR
#                           FAILING FOR HA CHECK EVEN THOUGH CUSTOMER VMS ARE
#                           SHUTDOWN WITH ZERO CPU CORES
#    apotluri    11/21/23 - Bug 35975084 - DOM0 PRECHECK FAILS AT STALEMOUNT
#                           CHECK AND LOG SHOWS OCI ERROR DURING INSTANCE
#                           PRINCIPALS CREATION.
#                           OCICONNECTIONPOOL(HOST='AUTH.SEA.ORACLECLOUD.COM',
#                           PORT=443): MAX RETRIES EXCEEDED WITH URL: /V1/X509
#    sdevasek    11/20/23 - Bug 36015891 - SVM:DOM0 PRECHECK FAILS:INSUFFICIENT
#                           LAUNCH NODE(S) FOUND ON THE ENVIRONMENT TO PATCH   
#    sdevasek    11/15/23 - ENH 36011846 - RUN RDS_PING TO VALIDATE VM TO VM
#                           AND VM TO CELL CONNECTIVITY AFTER HEARTBEAT CHECK
#                           FAILURE IN DOM0 PATCHING
#    araghave    10/25/23 - Bug 35902513 - EXACC | ERROR HANDLING TESTING - QMR
#                           DOM0 PRECHECK ENABLED DOMU AUTORESTART THEN FAILED
#                           IN EXACLOUD BUT PRECHECK CONTINUED WITH CELL
#    antamil     20/09/23 - BUG 35752885 - ALLOW LAUNCH NODE TO BE PASSED WITH
#                           INCLUDE NODE LIST
#    sdevasek    10/27/23 - BUG 35949486 - RESTORING INFRA PATCHING CHANGES
#                           DONE AS PART OF 35825510
#    antamil     10/17/23 - Bug 35835537 - Implement support for multiple external
#                                          launch node
#    antamil     09/20/23 - BUG 35752885 - ALLOW LAUNCH NODE TO BE PASSED WITH
#                           INCLUDE NODE LIST
#                           INCLUDE NODE LIST
#    sdevasek    09/20/23 - BUG 35820002 - DOM0 ROLLING PATCHING FAILS: USER
#                           SPECIFIED NODE DOES NOT EXIST IN THE ORIGINAL
#                           LAUNCH NODE CANDIDATES
#    sdevasek    09/19/23 - BUG 35692709 - DOM0 ROLLBACK IS EXECUTED ON 
#                           DISCARDED NODE AND INFRAPATCHING OPERATION FAILS
#    diguma      09/15/23 - Bug 35797999 - use current version to check 
#                           exasplice
#    sdevasek    08/30/23 - BUG 35662405 - FAILED TO SHUTDOWN VMS DURING CELL
#                           NON-ROLLING UPGRADE FAILED
#    antamil     18/08/23 - ENH 35577433 - ADD VALIDATIONS ON EXTERNAL LAUNCH
#                           NODE PASSED
#    araghave    08/14/23 - Enh 35244586 - DISABLE PRE AND POST CHECKS NOT
#                           APPLICABLE DURING MONTHLY PATCHING
#    avimonda    07/30/23 - Bug 35443002 - Set the current target type to dom0
#                           before establishing the launch node.
#    jyotdas     07/26/23 - ENH 35641075 - Develop a generic framework for
#                           infrapatching api validation execution
#    sdevasek    07/19/23 - BUG 35619289 - ACTIVE/ACTIVE UPGRADE: SECURITY
#                           MAINTENANCE RUN GOT STUCK DURING ROLLING UPGRADE
#    sdevasek    07/08/23 - BUG 35555704 - EXACS:BB:INFRAPATCHING:DOM0 PATCH
#                           FAILED AS VM IS NOT ACCESSIBLE
#    antamil     06/21/23   ENH 35026503 - SUPPORT TO LAUNCH MULTIPLE PATCHMGR
#                           SESSIONS  ON THE GIVEN EXTERNAL LAUNCH NODE
#    sdevasek    06/26/23 - BUG 35509499 - AIM4EXA2.0 - BUG NOT CREATED FOR
#                           INCIDENT IN BUG 35481344
#    araghave    06/13/23 - Bug 35489234 - DOM0 POSTCHECK OPERATION FAILS FOR
#                           HEARTBEAT CHECK AND UNABLE TO START CRS EVEN WHEN
#                           KEYS ARE AVAILABLE
#    araghave    06/07/23 - ENH 35277247 - OCI EXACS: INFRA PATCHING PRECHECK
#                           SHOULD NOT CHECK DOMU RUNNING STATUS AND HEARTBEAT
#    pkandhas    06/01/23 - Enh 35371653, Remove Obsolete SSH keys
#    josedelg    05/23/23 - Bug 35395723 - Remove dom0_iptables_setup.sh
#                           exists validation for clusterless upgrade
#    antamil     05/17/23 - Enh 35361661 - Enable external launch node support
#                           for precheck operation
#    sdevasek    05/12/23 - BUG 35264894 - INFRAPATCHING EXACLOUD IS WAITING 
#                           FOR CRS HB ON EACH CELL FOR MORE THAN 30 MINUTES
#    araghave    04/24/23 - Enh 35317523 - MAKE INFRA PATCHING HIGH
#                           AVAILABILITY CHECKS CONFIGURABLE IN
#                           INFRAPATCHING.CONF
#    diguma      04/18/23 - bug 34392890 - check connectivity of domu if 
#                           dom0domu is enabled in precheck
#    araghave    04/13/23 - Bug 35287744 - DISABLING HEARTBEAT CHECK PRIOR TO
#                           PATCHING
#    araghave    04/13/23 - Enh 35113451 - SSH CONNECTIVITY TEST FOR
#                           INFRAPATCHING NOT WORKING
#    sdevasek    04/12/23 - BUG 35272253 - PERFORM HEARTBEAT VALIDATIONS POST
#                           ADDING RELEVANT DISKMON MESSAGES IN ALERT LOG
#    araghave    03/23/23 - Enh 35098710 - FOR MVM CLUSTER PRE-CHECK FAILED
#                           WHEN ONE VM - CPU SCALE DOWN TO 0 SO VM IS SHUTDOWN
#                           FOR THAT CLUSTER
#    araghave    03/20/23 - Enh 35062878 - VALIDATE CRS AUTO STARTUP SETTINGS
#                           DURING DOM0 PATCHING
#    sdevasek    03/20/23 - ENH 35199689 - REMOVAL OF EXTRA SLEEP TIME IN DOM0
#                           POST CHECK EXECUTION
#    antamil     03/07/23 - Bug 35054815 -LAUNCH NODE SUPPORT FOR PROVIDIONED
#                           CLUSTER AND CLUSTERLESS DOM0 PATCHING
#    araghave    01/13/22 - Enh 34859379 - PERFORM CRS BOUNCE BEFORE HEARTBEAT
#                           CHECK TIMEOUT, IF DOMUs ARE UNABLE TO ESTABLISH
#                           A HEART BEAT TO THE CELLS
#    araghave    01/06/23 - Bug 34953949 - DOMU HEARTBEAT VALIDATIONS NEED TO
#                           BE PERFORMED USING CUSTOMER HOSTNAME
#    josedelg    01/03/23 - Bug 34905057 - Identify properly OL8 kvm file
#    araghave    01/01/23 - Enh 34899467 - Perform heartbeat validations during
#                           dom0 non-rolling patching
#    araghave    12/16/22 - Enh 34339397 - REMOVE RESTRICTION FOR MULTIPLE
#                           PATCHMGR ON SINGLE LAUNCH NODE
#    araghave    12/05/22 - 34846923 - Startup VMs on the discarded dom0 list
#                           if they are down
#    sdevasek    12/02/22 - BUG 34842139 - DOM0 PATCHING FAILED AT CUSTOMCHECK
#                           AS NODE IMAGE VERSION IS HIGHER THAN TARGET VERSION
#    araghave    11/23/22 - Bug 34592207 - INFRA PATCHING SHOULD FAIL WHEN ONE
#                           OF VM IS DOWN
#    talagusu    11/17/22 - Bug 34808547 - INFRA LOGGING IMPROVEMENTS ON TOP OF
#                           BUG 34644538
#    diguma      11/14/22 - Enh 34015624 - if an error exists, dont overwrite
#    araghave    09/28/22 - Enh 34645910 - RUN HEARTBEAT VALIDATIONS PRIOR TO
#                           PATCHING ON REQUIRED SET OF DOMUS
#    josedelg    11/03/22 - Bug 34760850 - Recreate auto startup symlinks
#    jyotdas     10/16/22 - BUG 34681939 - Infrapatching compute nodes should
#                           be sorted by dbserver name from ecra
#    sdevasek    10/13/22 - BUG 34632765 - IPTABLES SVC IS NOT STARTED IN POST
#                           PATCHING WHEN ANY OF THE POSTCHECK FAILS
#    jyotdas     10/10/22 - Bug 34681437 - Infrapatch nodes are getting patched
#                           in random order
#    araghave    09/29/22 - Enh 34623863 - PERFORM SPACE CHECK VALIDATIONS
#                           BEFORE PATCH OPERATIONS ON TARGET NODES
#    araghave    09/29/22 - Bug 34546422 - INFRAPATCHING V2 : RETRY OF FAILED
#                           MR MAY CAUSE OUTAGE TO CUSTOMER
#    araghave    09/23/22 - Bug 34629293 - DOMU PRECHECK OPERATION FAILING AT
#                           EXACLOUD LAYER DUE TO CHECKSUM ISSUE
#    araghave    09/22/22 - Enh 33944615 - IMPLEMENT HEARTBEAT VALIDATION 
#                           WITHOUT CELL MARKER DETAILS
#    sdevasek    09/22/22 - Bug 34627697 - HANDLING OF ERROR WHEN EXECUTING
#                           EXACLOUD PLUGIN DURING IDEMPOTENCY CHECK
#    araghave    09/14/22 - Enh 34480945 - MVM IMPLEMENTATION ON INFRA PATCHING
#                           CORE FILES
#    josedelg    07/04/22 - Bug 34277307 - Skip autostart soft link validation
#                           for patch operation
#    araghave    06/24/22 - Enh 34258082 - COPY PATCHMGR DIAG LOGS FROM LAUNCH
#                           NODES POST PATCHING ONLY IF THE EXIT STATUS IS A
#                           FAILURE
#    sdevasek    06/07/22 - Bug 34246727 - EXACS: DOMU EXACSOSPATCH PRECHECK
#                           FAILS WITH ERROR STALE MOUNT(S) DETECTED ON DOMU
#    araghave    05/30/22 - Enh 34225663 - SKIP BACKUP IN CASE OF A SYSTEM
#                           CONSISTENCY CHECK FAILURE AND PROCEED WITH UPGRADE
#    araghave    05/23/22 - Enh 34179923 - WHEN PATCH RETRY IS TRIGGERED FROM
#                           CP PASS NOBACKUP TO PATCHMGR BY CHECKING SYSTEM
#                           CONSISTENCY STATE
#    sdevasek    05/22/22 - ENH 33859232 - TRACK TIME PROFILE INFORMATION FOR
#                           INFRAPATCH OPERATIONS
#    sdevasek    05/11/22 - ENH 34053202 - INFRAPATCHING PRECHECK TO VALIDATE
#                           THE PRESENCE OF DOM0_IPTABLES_SETUP.SH SCRIPT
#    araghave    04/28/22 - Bug 34094559 - REVERTING THE CHANGES FOR ENH
#                           33729129
#    araghave    04/19/22 - Enh 33516791 - EXACLOUD: DO NOT OVER WRITE THE
#                           ERROR SET BY RAISE EXCEPTION
#    araghave    04/12/22 - Enh 34048154 - ONEOFF PATCH OPERATION TO SUPPORT A
#                           PLUGIN FRAMEWORK WITH GENERIC OPTIONS
#    jyotdas     04/04/22 - BUG 34010538 - Apply monthly patch on dom0 fails if
#                           reshape to zero cores is run in parallel
#    jyotdas     03/14/22 - ENH 33933635 - Avoid cleanup the ssh equivalence at
#                           the end of patching
#    nmallego    02/17/22 - Bug33811252 - Stop looking for notifications if no
#                           action required
#    josedelg    02/16/22 - Bug 33828825 - Retry copy of patch artifacts during
#                           precheck and patch
#    araghave    01/06/22 - Enh 33729129 - Provide both .zip and .bz2 file
#                           extension support on System image files.
#    nmallego    01/19/22 - Bug33763732-Disable mCheckDomuAvailability on ExaCC
#    araghave    01/18/22 - Enh 30646084 - Require ability to specify compute
#                           nodes to include as part of Patching process
#    jyotdas     01/17/22 - ENH 33748218 - optimize to call mhasstalemounts for
#                           single node upgrade
#    nmallego    01/04/22 - ER 33453352 - Validate root file system before
#                           taking backup
#    araghave    12/20/21 - ENH 33689675 - ADD NEW ERROR FOR DOMU PATCHMGR
#                           FAILURE AND MARK FAIL AND SHOW
#    araghave    12/06/21 - Enh 33052410 - Purge System first boot image file
#                           for Dom0 space management
#    araghave    11/23/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES
#                           FROM ERROR.PY TO INFRAPATCHERROR.PY
#    nmallego    11/19/21 - Bug33584494 - correct log message
#    araghave    10/28/21 - Bug 33520303 - COMPARE WITH APPROPRIATE ERROR CODE
#                           DURING IDEMPOTENT PATCHMGR EXISTENCE CHECK
#    araghave    10/25/21 - Enh 33387834 - THROW APPROPRIATE ERROR MSG WHEN
#                           ONLY ONE NODE IS AVAILABLE
#    araghave    10/20/21 - Enh 33486853 - MOVE TIMEOUT AND OTHER CONSTANTS OUT
#                           OF CODE INTO CONFIG/CONSTANT FILES
#    nmallego    10/18/21 - Bug32945969 - Non-rolling: Optimize the
#                           shutdown/startup
#    araghave    10/05/21 - Enh 33378051 - VALIDATE FOR DOMU AUTO STARTUP
#                           DETAILS DURING PRE/POST DOM0 PATCH OPERATIONS
#    josedelg    10/04/21 - Bug 33285054 - VIF-BRIDGE symlinks validation in
#                           the post check operation
#    araghave    09/22/21 - Bug 33300892 - Enh 33382919 - CLEANUP EBERROR AND 
#                           EXACLOUD ERROR CODE DETAILS FROM 
#                           MVALIDATEIMAGECHECKSUM()
#    jyotdas     09/20/21 - Enh 33290086 - stale mount check before starting
#                           dbserver patching for all nodes
#    nmallego    09/03/21 - Bug33249608 - Support non-rolling option
#    araghave    08/02/21 - Enh 33182904 - Move all configurable parameters
#                           from constants.py to Infrapatching.conf
#    nmallego    08/12/21 - Bug33218205 - Push sleep code to inner for loop
#    nmallego    08/04/21 - Bug33188998 - Do not run DomU Aavil check for
#                           clusterless rack
#    araghave    07/11/21 - ENH 33099120 - INTRODUCE A SPECIFIC ERROR CODE FOR
#                           PATCHMGR CONSOLE READ TIME OUT
#    araghave    07/08/21 - BUG 33081173 - Remove older error codes from Infra
#                           patching core files
#    jyotdas     06/30/21 - Bug 32813015 - non-rolling patching should not run
#                           dom0domu plugin
#    nmallego    05/21/21 - Bug32507046 - Pick appropriate launch node
#    sringran    05/14/21 - Bug32878905 - PATCHING FAILS WITH NO ATTRIBUTE 
#                           '_DOM0HANDLER__FEDRAMP'
#    pkandhas    05/11/21 - Bug32864782 - use dbmcli instead of dbserverd
#    nmallego    04/23/21 - Bug32788094 - Fix exasplice activated option
#    araghave    04/20/21 - Bug 32397257 - Get granular error handling details
#                           for Dom0 and DomU targets
#    araghave    04/11/21 - Multiple occurances of MGETPATCHMGRXML failed with
#                           diff -w command errors
#    nmallego    03/18/21 - ER 32581076: Check domU availability on each dom0
#    alsepulv    03/16/21 - Enh 32619413: remove any code related to Higgs
#    araghave    02/15/21 - ENH 31423563 - PROVIDE A MECHANISM TO MONITOR
#                           INFRA PATCHING PROGRESS
#    nmallego    02/08/21 - Bug32433614 - Add sleep b/w compute nodes in
#                           rolling upgrade
#    araghave    02/01/21 - Bug 32120772 - EXASPLICE AND PYTHON 3 FIXES
#    nmallego    01/28/21 - Bug31963499-Instrumented code to track return
#                           payload
#    araghave    01/19/21 - Bug 32395969 - MONTHLY PATCHING: FOUND FEW ISSUES
#                           WHILE TESTING AND NEED TO FIX
#    araghave    12/24/20 - Bug 32319703 - Precheck error handling fix
#    nmallego    12/23/20 - ER 32284276 - Restrict non-rolling for exasplice on
#                           dom0
#    araghave    12/08/20 - Enh 31984849 - RETURN ERROR CODES TO DBCP FROM DOM0
#                           AND PLUGINS
#    nmallego    12/07/20 - Bug31982131 - Do not ignore critical h/w alert
#    nmallego    10/27/20 - Enh 32134826 - Stop patching in-case patchmgr
#                           session exist without retry/idempotent case.
#    araghave    10/21/20 - Enh 31925002 - Error code handling implementation for
#                           Monthly Patching
#    nmallego    10/27/20 - Enh 31540038 - INFRA PATCHING TO APPLY/ROLLBACK
#                           EXASPLICE/MONTHLY BUNDLE
#    araghave    08/12/20 - Enh 30829107 - Patchmgr log detailed output and log
#                           collection fix
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#

# pylint: disable=raising-bad-type,no-member

"""
History:
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
    nmallego 03/16/20 - Bug 30922125 - fix concurrent issue
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
    nmallego 08/07/19 - Bug 30115824: Read customer name based on xmlns tag
                        in oeda xml
    nmallego 08/01/19 - Bug 30125729 - Use common plugin directory path
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
import datetime
import os, sys
import re
import time
import json
import traceback
from time import sleep
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.infrapatching.handlers.mockTargetHandler.targetmockhandler import TargetMockHandler
from exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler import InfraPatchManager
from exabox.infrapatching.utils.utility import mGetFirstDirInZip, PATCH_BASE, mFormatOut, \
    EXACLOUD_DO_DOM0_ROLLBACK_EVEN_IF_DOMU_MODIFIED_POST_PATCH, mRegisterInfraPatchingHandlers, \
    mFilterRequestsForThisRack, mIsFSEncryptedNode, checkPluginEnabledFromInfraPatchMetadata, \
    mConvertTimeEscli, mValidateTime
from exabox.infrapatching.core.clupatchmetadata import mWritePatchInitialStatesToLaunchNodes, \
    mUpdateAllPatchStatesForNode, mGetPatchStatesForNode, mGetLaunchNodeForTargetType, mUpdatePatchMetadata, \
    mUpdateMetadataLaunchNode
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.ovm.clumisc import ebCluSshSetup
from exabox.core.DBStore import ebGetDefaultDB
from exabox.utils.common import version_compare
from exabox.exakms.ExaKmsEndpoint import ExaKmsEndpoint
sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

class Dom0MockHandler(TargetMockHandler):

    def __init__(self, *initial_data, **kwargs):

        super(Dom0MockHandler, self).__init__(*initial_data, **kwargs)
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [PATCH_DOM0], self)
        self.mPatchLogInfo("Dom0MockHandler")

        # Only Dom0 related variables
        self.__dom0_local_patch_zip = self.mGetDom0DomUPatchZipFile()[0]
        self.__dom0_local_patch_zip2 = self.mGetDom0DomUPatchZipFile()[1]
        self.__dom0_patch_zip_name = None
        self.__dom0_patch_zip2_name = None
        self.__dom0_patch_base = None
        self.__dom0_patch_zip = None
        self.__dom0_patch_base_after_unzip = None
        self.__dom0_patchmgr = None
        self.__dom0_patch_zip_size_mb = None
        self.__dom0_patch_zip2_size_mb = None
        self.__dom0_patch_necessary_space_mb = None
        self.__dom0_to_patch_dom0s = None
        self.__dom0_patchmgr_input_file = None
        self.__dom0s_to_patch = []
        self.__dom0_patch_base_dir = PATCH_BASE
        self.__dom0_hb_info = {}
        # Contains all the vms on which crs auto start is enabled and crs is running 
        self.__crs_autostart_enabled_vm_set = set()
        self.mPrintEnvRelatedDebugStatements()

    def mGetDom0PatchBaseDir(self):
        return self.__dom0_patch_base_dir

    def mGetDom0LocalPatchZip(self):
        return self.__dom0_local_patch_zip

    def mGetDom0LocalPatchZip2(self):
        return self.__dom0_local_patch_zip2

    def mGetDom0PatchZipName(self):
        return self.__dom0_patch_zip_name

    def mGetDom0PatchZip2Name(self):
        return self.__dom0_patch_zip2_name

    def mGetDom0PatchBase(self):
        return self.__dom0_patch_base

    def mGetDom0PatchZip(self):
        return self.__dom0_patch_zip

    def mGetDom0PatchBaseAfterUnzip(self):
        return self.__dom0_patch_base_after_unzip

    def mGetDom0PatchMgr(self):
        return self.__dom0_patchmgr

    def mGetDom0PatchZipSizeMB(self):
        return self.__dom0_patch_zip_size_mb

    def mGetDom0PatchZip2SizeMB(self):
        return self.__dom0_patch_zip2_size_mb

    def mGetDom0PatchNecessarySpaceMB(self):
        return self.__dom0_patch_necessary_space_mb

    def mGetDom0ToPatchDom0(self):
        return self.__dom0_to_patch_dom0s

    def mGetDom0PatchMgrInputFile(self):
        return self.__dom0_patchmgr_input_file

    def mGetDom0sToPatch(self):
        return self.__dom0s_to_patch

    def mPreCheck(self):
        """
        Does the setup, filter the nodes to perform pre-check,
        idempotency check , custom check and then run the pre-check
        of dom0's
        Return codes:
           1) ret -->
               0 for success
               non-zero for failure
           2)  _no_action_taken -->
               0 indicate some action is taken care.
               non-zero indicate no action is taken care.
           3) Precheck operation always run as non-rolling to save the
              time. Also, since patchmgr notification has some issue
              with rolling, it's always recommended to run precheck as
              non-rolling.
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0

        try:
            self.mPatchLogInfo(
                f"\n\n---------------> Starting {TASK_PREREQ_CHECK} on {PATCH_DOM0}s <---------------\n\n")

            # check if artifacts are present
            if self.mIsExaSplice() and (not self.mGetDom0LocalPatchZip() or not self.mGetDom0LocalPatchZip2()):
                self.mPatchLogError("Exiting. Patch files missing")
                return MISSING_PATCH_FILES, _no_action_taken

            # 1. Set up environment
            _ret = self.mSetEnvironment()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since return code from mSetEnvironment is {_ret} ")
                return _ret, _no_action_taken

            # Perform crs checks but ignore the ret value
            self.mPerformDomuCrsCheckForAllClusters()

            _launch_nodes = [self.__dom0_to_patch_dom0s, self.mGetDom0ToPatchInitialDom0()]

            '''
             Perform space validations on root partition
             on Dom0 targets
            '''
            _ret = self.mValidateRootFsSpaceUsage()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mValidateRootFsSpaceUsage is {_ret} ")
                return _ret , _no_action_taken

            # Perform HA checks but ignore the ret value
            if self.mGetInfrapatchExecutionValidator().mCheckCondition('checkHAChecksOnDom0') \
                    and self.mGetOpStyle() == OP_STYLE_ROLLING:
                self.mCheckDomuAvailability() 

            # Get customized list of nodes
            _ret, _suggestion_msg, _list_of_nodes, _discarded = self.mFilterNodesToPatch(
                self.mGetCustomizedDom0List(), PATCH_DOM0, TASK_PREREQ_CHECK)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            # Validate for exasplice patch to be applied on list of dom0s.
            if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsExaspliceNot24'):
                _list_of_nodes = self.mGetListOfDom0sWhereExasplicePatchCanBeApplied(_launch_nodes, _list_of_nodes)

            # Set initial Patch Status Json.
            self.mUpdatePatchProgressStatus(aNodeList=_list_of_nodes, aDiscardedNodeList=_discarded)

            # 2. Check for idempotency
            _ret, _no_action_taken = self.mCheckIdemPotency(_discarded)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mSetPatchEnvironment in domU is {_ret} ")
                return _ret , _no_action_taken

            # 3. Perform customcheck
            if len(_discarded) > 0:
                _ret = self.mCustomCheck(aNodes=_discarded)
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    return _ret, _no_action_taken

            if len(_list_of_nodes) <= 0:

                # We need to populate more info about the patching operation when
                # no action is required and it requires to update ecra rack status
                # to previous status.
                _suggestion_msg = f"No available {PATCH_DOM0.upper()}s to run the patchmgr. Nothing to do here."
                _ret = PATCH_SUCCESS_EXIT_CODE
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            _check_plugin_connectivity = False
            # check if exacloud plugin is enabled for dom0domU 
            if not self.mIsExaCC() and self.mIsExacloudPluginEnabled() and self.mGetPluginHandler().mGetRunUserPluginsonDom0sdomuNode():
                _check_plugin_connectivity = True

            '''
             Performing Auto start validations of DomU currently
             up and running on the current Dom0 during Dom0 precheck.
            '''
            if self.mIsMockEnv():
                # in mock setup, skip rack specific operations
                return _ret , _no_action_taken

            for _dom0 in _list_of_nodes:
                _domU_listed_by_xm_list = self.mGetCluPatchCheck().mCheckVMsUp(_dom0)
                self.mPatchLogInfo(f"List of domUs : {str(_domU_listed_by_xm_list)} running on dom0 :{_dom0} ")
                if len(_domU_listed_by_xm_list) > 0:
                    _ret = self.mGetCluPatchCheck().mValidateAndEnableDomuAutoStartup(_dom0,_domU_listed_by_xm_list)
                    if _ret != PATCH_SUCCESS_EXIT_CODE:
                        return _ret, _no_action_taken
                    
                    # check if node is accessible with key. Check only for the VM's that are up
                    if _check_plugin_connectivity:
                        for _domu in _domU_listed_by_xm_list:
                            _ret = self.mGetPluginHandler().mCheckConnectivityPluginScript(
                                       self.mGetDomUNatHostNameforDomuCustomerHostName(_domu),
                                       _domu, "dom0domu", True)
                            if _ret != PATCH_SUCCESS_EXIT_CODE:
                                return _ret, _no_action_taken

            #Perform stale mounts check
            if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsStaleMountCheckEnabled'):
                _ret, _stale_mount_check_node_list = self.mGetStaleMountNodeList(_list_of_nodes)
                if _ret == SINGLE_NODE_NAME_MISSING:
                    _suggestion_msg = "Single Node Name not specified"
                    _ret = SINGLE_NODE_NAME_MISSING
                    self.mAddError(_ret, _suggestion_msg)
                    return _ret, _no_action_taken

                _has_stale_mounts, _suggestion_msg = self.mHasStaleMounts(_stale_mount_check_node_list)
                if _has_stale_mounts:
                    _ret = DOM0_STALE_MOUNT_CHECK_FAILED
                    self.mAddError(_ret, _suggestion_msg)
                    return _ret, _no_action_taken
            else:
                self.mPatchLogInfo(
                    f'enable_stale_mount_check is disabled in conf file {INFRA_PATCHING_CONF_FILE}. Hence stale mount check is skipped.')

            # Perform system consistency check
            _is_system_valid_state, _suggestion_msg = self.mCheckSystemConsitency(_list_of_nodes)
            if not _is_system_valid_state:
                _ret = DOM0_SYSTEM_CONSISTENCY_CHECK_FAILED
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            # Check for presence of dom0_iptables_setup.sh in exacs envs
            if not self.mIsExaCC():
                # dom0_iptables_setup.sh is not present in a clusterless patching.
                # The provisioning flow has to execute dom0_iptables_setup.sh if it is not already executing it.
                if not self.mIsClusterLessUpgrade():
                    _result, _nodes_missing_file = self.mCheckFileExistsOnRemoteNodes(_list_of_nodes, DOM0_IPTABLES_SETUP_SCRIPT)
                    if not _result:
                        _suggestion_msg = f"Unable to locate {DOM0_IPTABLES_SETUP_SCRIPT} file on dom0 nodes "
                        if len(_nodes_missing_file) > 0 :
                            _suggestion_msg += str(_nodes_missing_file)
                        _ret = DOM0_UNABLE_TO_LOCATE_IPTABLES_SETUP_SCRIPT
                        self.mAddError(_ret, _suggestion_msg)
                        return _ret, _no_action_taken
            
            """
            Runs the dom[0U]s prerequisite check in rolling or non-rolling  mode.

            Returns  NO_ACTION_REQUIRED if no nodes requiere patching
            Returns 0 if patchmgr ran without issues and the dom[0U]s should be
            patched.
            Returns != 0 if patchmgr found problems on the nodes
            """
            _node_to_patch_nodes = self.__dom0_to_patch_dom0s
            _node_to_patch_initial_node = self.mGetDom0ToPatchInitialDom0()
            '''
             _nodes_to_patch_except_initial can only be the customised
             list of nodes as patch operations are required to be performed
             only on the input node provided.
            '''
            _nodes_to_patch_except_initial = list(set(_list_of_nodes) -
                                                  set([self.__dom0_to_patch_dom0s]))
            _initial_node_list = list(set(_list_of_nodes) - set(_nodes_to_patch_except_initial))	
            _cns_string = CNS_DOM0_PATCHER

            if not _node_to_patch_nodes and _node_to_patch_initial_node:
                raise self.mPatchLogError(PATCH_DOM0.upper() +
                                          " patching is unavailable, " + PATCH_DOM0.upper() +
                                          " patch files" +
                                          " were not provided at initialization")

            _callbacks = self.mGetCallBacks()

            self.mPatchLogInfo(
                f'_node_to_patch_nodes = {str(_node_to_patch_nodes)}, _node_to_patch_initial_node = {str(_node_to_patch_initial_node)}')
            self.mPatchLogInfo(
                f'_nodes_to_patch_except_initial = {str(_nodes_to_patch_except_initial)}, _initial_node_list= {str(_initial_node_list)}')

            _ec_node_precheck = PATCH_SUCCESS_EXIT_CODE
            _ec_initial_node_precheck = PATCH_SUCCESS_EXIT_CODE

            def _patch_precheck_node(aNode, aTargetType, aListOfNodesToPatch,
                                     aDiscardedNodeList, aPatchInitNode=False):
                _dom0Us_count = len(aListOfNodesToPatch)

                # Initial launch node is what it has passed, but it can change if
                # patchmgr session already exist in case of patch retry.
                _node_patcher = aNode
                _exit_code = PATCH_SUCCESS_EXIT_CODE
                _patchMgrObj = None

                self.mPatchLogInfo(f'Launch node = {aNode}, List of Nodes to work on = {str(aListOfNodesToPatch)}')

                # Update status
                if not aPatchInitNode:
                    self.mUpdatePatchStatus(True,
                                            STEP_FILTER_NODES + '_' + PATCH_DOM0 + '_1')
                else:
                    self.mUpdatePatchStatus(True,
                                            STEP_FILTER_NODES + '_' + PATCH_DOM0 + '_2')

                ##### TBD: check if all vms are in the cluster (heartbeat).
                for _dom0u_to_patch in aListOfNodesToPatch[:]:
                    # check if all dom[0u]s are healthy/pingable first
                    if not self.mGetCluPatchCheck().mPingNode(_dom0u_to_patch):
                        self.mPatchLogWarn(
                            f"{aTargetType.upper()} {_dom0u_to_patch} is not pingable. Discarding for precheck")
                        aListOfNodesToPatch.remove(_dom0u_to_patch)
                        continue

                if (aListOfNodesToPatch and
                        ((_dom0Us_count - len(aListOfNodesToPatch)) !=
                         len(aDiscardedNodeList))):
                    self.mPatchLogWarn(
                        f"Cluster is not coherent. Expected {str(_dom0Us_count)} {aTargetType.upper()}s, but got {str(len(aListOfNodesToPatch))}")

                self.mPatchLogInfo(
                    f"ebCluPatchControl._mPatchDom0UsPreChecks: _dom0Us_count = {_dom0Us_count}, aListOfNodesToPatch = {len(aListOfNodesToPatch)}, doums_count_on_same_target_version = {len(aDiscardedNodeList)}")

                # if we removed all of the nodes to run pre-check, because they were
                # already at the requested version just return success
                if (not aListOfNodesToPatch and
                        _dom0Us_count == len(aDiscardedNodeList)):
                    self.mPatchLogInfo("All the DOMUs are in the requested version. "
                                       "No action required")
                    return NO_ACTION_REQUIRED

                # Return NO_ACTION_REQUIRED if no dom0Us to precheck
                # No need to check CNS at the end of cluster since no precheck is done
                if not aListOfNodesToPatch and len(aDiscardedNodeList) > 0:
                    self.mPatchLogInfo(f"List of nodes already upgraded and not considered for precheck using launch node {aNode} is {str(aDiscardedNodeList)} ")
                    return NO_ACTION_REQUIRED

                if not aPatchInitNode:
                    self.mUpdatePatchStatus(True, STEP_RUN_PATCH_DOM0)
                    _update_msg = STEP_CLEAN_ENV + '_' + PATCH_DOM0 + '_1'
                else:
                    self.mUpdatePatchStatus(True, STEP_RUN_PATCH_SECOND_DOM0)
                    _update_msg = STEP_CLEAN_ENV + '_' + PATCH_DOM0 + '_2'


                # create patchmgr object with bare minimum arguments local to this inner function for fresh InfraPatchManager obj ref
                # everytime inner function is called to avoid using old InfraPatchManager obj attribute ref, if any
                _patchMgrObj = InfraPatchManager(aTarget=PATCH_DOM0, aOperation=TASK_PREREQ_CHECK, aPatchBaseAfterUnzip=self.__dom0_patch_base_after_unzip,
                                           aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

                # now set the component's operation specific arguments
                _patchMgrObj.mSetIsoRepo(aIsoRepo=self.__dom0_patch_zip2_name)
                _patchMgrObj.mSetIsExaSpliceEnabled(aIsExaSpliceEnabled=self.mIsExaSplice())
                _patchMgrObj.mSetTargetVersion(aTargetVersion=self.mGetTargetVersion())

                # create patchmgr nodes file
                _input_file = _patchMgrObj.mCreateNodesToBePatchedFile(aLaunchNode=aNode, aHostList=aListOfNodesToPatch)
                self.__dom0_patchmgr_input_file = _input_file

                # prepare the patchmgr command for execution using the InfraPatchManager object
                _patch_precheck_cmd = _patchMgrObj.mGetPatchMgrCmd()
                
                # 1.- Run pre_check
                # If there are no patchmgr sessions running, then run patchmgr command
                # In this context, PATCH_SUCCESS_EXIT_CODE infers NO_PATCHMGR Session is running.
                # Skip patchmgr existence check during clusterless patching.

                _patchmgr_session_exit = PATCH_SUCCESS_EXIT_CODE
                _patchmgr_active_node = None

                if self.mPerformPatchmgrExistenceCheck():
                    # check for patchmgr session existence
                    _patchMgrObj.mSetLaunchNode(aLaunchNode=None)
                    _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=self.mGetCustomizedDom0List())

                    _patchmgr_session_exit, _patchmgr_active_node = _patchMgrObj.mCheckForPatchMgrSessionExistence()

                if _patchmgr_session_exit == PATCH_SUCCESS_EXIT_CODE:  # No patchmgr session found in any of the nodes, so re-execute
                    # set the launch node and execute patchmgr cmd
                    _patchMgrObj.mSetLaunchNode(aLaunchNode=_node_patcher)

                    _exit_code = _patchMgrObj.mExecutePatchMgrCmd(aPatchMgrCmd=_patch_precheck_cmd)
                    if _exit_code != PATCH_SUCCESS_EXIT_CODE:
                        return _exit_code

                    # Capture time profile details
                    self.mUpdateInfrapatchingTimeStatsForUnfilledStages()
                    self.mCreateInfrapatchingTimeStatsEntry(str(aListOfNodesToPatch), "PATCH_MGR")
                else:
                    # TODO: We need to handle patch non-retry in future. Time being we are forcibly stopping.
                    if not self.mPatchRequestRetried():
                        self.mPatchLogError('Found older patchmgr session. Forcibly terminating patching request')
                        return _patchmgr_session_exit

                    # Already patchmgr is running, just monitor patchmgr console on the node.
                    _patchMgrObj.mSetLaunchNode(aLaunchNode=_patchmgr_active_node)
                    _node_patcher = _patchmgr_active_node

                # reset the node list to make sure patchmgr cmd execution 
                # only looked at the launch node
                _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=None)
                
                # Following InfraPatchManager api sets the patchmgr execution status into mStatusCode method
                # hence not required to return/read a value from this api
                # this will help to use the patchMgr status apis 
                # (mIsSuccess/mIsFailed/mIsTimedOut/mIsCompleted) wherever required
                _patchMgrObj.mWaitForPatchMgrCmdExecutionToComplete()

                self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")

                _exit_code = _patchMgrObj.mGetStatusCode()

                # Capture time profile details
                self.mPopulateInfrapatchingTimeStatsEntries(aNewStage="POST_PATCH", aNewSubStage="",
                                                            aNewStageNodes=str(aListOfNodesToPatch),
                                                            aCompletedStage="PATCH_MGR", aCompletedSubStage="",
                                                            aCompletedStageNodeDetails=str(aListOfNodesToPatch))

                if len(aListOfNodesToPatch) > 0:
                    # 2 .- Update status
                    self.mUpdatePatchStatus(True, _update_msg)

                    # 3.- Get patchmgr pre-check logs
                    _precheck_log = str(self.mGetDom0FileCode(_node_patcher, self.mGetPatchmgrLogPathOnLaunchNode()))
                    self.mGetPatchMgrOutFiles(_node_patcher,
                                              self.mGetPatchmgrLogPathOnLaunchNode(),
                                              _precheck_log)
                    '''
                     Collect patchmgr diag logs for debugging only
                     when the final exit code from patch operation 
                     is not PATCH_SUCCESS_EXIT_CODE.
                    '''
                    if _exit_code != PATCH_SUCCESS_EXIT_CODE:
                        self.mGetPatchMgrDiagFiles(_node_patcher,
                                                   aTargetType,
                                                   aListOfNodesToPatch,
                                                   self.mGetPatchmgrLogPathOnLaunchNode())
                    else:
                        self.mPatchLogInfo("Patchmgr diag logs are not collected in case of a successful infra patch operation.")

                    self.mGetPatchMgrMiscLogFiles(_node_patcher,
                                                  self.mGetPatchmgrLogPathOnLaunchNode(),
                                                  TASK_PREREQ_CHECK,
                                                  aListOfNodesToPatch)

                # Print all the log details at the end of log files copy.
                self.mPrintPatchmgrLogFormattedDetails()

                self.mPreCheckFilesCleanup(_node_patcher, _input_file, _cns_string)

                return _exit_code
                # end of _patch_precheck_node

            # Initialize actual patchmgr location before it is renamed.
            _actual_patchmgr_log_on_launch_node = self.mGetPatchmgrLogPathOnLaunchNode()

            # update current node being used to upgrade i.e., __dom0_to_patch_dom0
            _node_patch_progress = os.path.join(self.mGetLogPath(), _cns_string)
            try:
                with open(_node_patch_progress, "w") as write_nodestat:
                    write_nodestat.write(f"{_node_to_patch_nodes}:{self.mGetPatchmgrLogPathOnLaunchNode()}")
            except Exception as e:
                self.mPatchLogWarn(f'Failed to write {_node_patch_progress}: {str(e)}')
                self.mPatchLogTrace(traceback.format_exc())

            # Run the pre_check in all the dom[0U]s except one
            _ec_node_precheck = _patch_precheck_node(
                aNode=_node_to_patch_nodes,
                aTargetType=PATCH_DOM0,
                aListOfNodesToPatch=_nodes_to_patch_except_initial,
                aDiscardedNodeList=_discarded, 
                aPatchInitNode=False)

            if _ec_node_precheck == EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR:
                self.mPatchLogInfo(f"Infra patching failed due to Exacloud timeout - Return code - {_ec_node_precheck}")
                _ret = _ec_node_precheck
                return _ret , _no_action_taken

            self.mPatchLogInfo("*** Finished running pre-check in all the dom0s except initial dom0 node")

            # Log location was renamed for supporting idempotency. Resetting -log_dir to
            # actual path for collecting notifications.
            self.mSetPatchmgrLogPathOnLaunchNode(_actual_patchmgr_log_on_launch_node)

            # update current node being used to upgrade i.e., to
            # __dom0_to_patch_initial_dom0 (self.mGetDom0ToPatchInitialDom0())
            try:
                with open(_node_patch_progress, "w") as write_nodestat:
                    write_nodestat.write(f"{_node_to_patch_initial_node}:{self.mGetPatchmgrLogPathOnLaunchNode()}")
            except Exception as e:
                self.mPatchLogWarn(f'Failed to write {_node_patch_progress}: {str(e)}')
                self.mPatchLogTrace(traceback.format_exc())

            '''
            In case of single external launch node there is no 2nd iteration of 
            precheck to be run. Precheck would have been run on all nodes in 
            the 1st iteration itself . Hence the below iteration has to be run only
            when external launch node is not passed
            '''
            if len(self.mGetExternalLaunchNode()) == 0 and len(_initial_node_list) > 0:
                _ec_initial_node_precheck = _patch_precheck_node(
                    aNode=_node_to_patch_initial_node,
                    aTargetType=PATCH_DOM0,
                    aListOfNodesToPatch=_initial_node_list,
                    aDiscardedNodeList=_discarded,
                    aPatchInitNode=True)

                # Need to capture exadata error json details 
                if _ec_node_precheck == PATCHMGR_COMMAND_FAILED and _ec_initial_node_precheck != PATCHMGR_COMMAND_FAILED:
                    _cur_launch_node_list = self.mGetCurrentLaunchNodeList()
                    if _cur_launch_node_list:
                        # This is to have launch node where patch_mgr has failed as the last element to read patch_mgr error json details
                        _cur_launch_node_list.reverse()
                        self.mSetCurrentLaunchNodeList(_cur_launch_node_list)
                        self.mUpdateCurrentLaunchNodeDetailsInCorrespondingTaskHandlerInstance()

                if _ec_initial_node_precheck == EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR:
                    self.mPatchLogInfo(
                        f"Infra patching failed due to Exacloud timeout - Return code - {_ec_initial_node_precheck}")
                    _ret = _ec_initial_node_precheck
                    self.mPatchLogInfo("Finished running pre-check on initial dom0 Node .")
                    return _ret , _no_action_taken
            else:
                _ec_initial_node_precheck = NO_ACTION_REQUIRED
            self.mPatchLogInfo("Pre-check run finished")

            # Updates POST_PATCH time for last post_patch entry
            self.mUpdateInfrapatchingTimeStatsForUnfilledStages()
            # Capture time profile details for post_patch activity done on all nodes
            self.mCreateInfrapatchingTimeStatsEntry(str(self.mGetDom0List()), "POST_PATCH")

            if (_ec_node_precheck == NO_ACTION_REQUIRED or
                     _ec_initial_node_precheck == NO_ACTION_REQUIRED):
                 self.mPatchLogInfo("In scenario where NO ACTION REQUIRED on one node")
                 if (_ec_node_precheck == NO_ACTION_REQUIRED and
                         _ec_initial_node_precheck == NO_ACTION_REQUIRED):
                     self.mPatchLogInfo("No action required on multiple nodes.")
                     _no_action_taken += 1
                     # We need to populate more info about the patching
                     # operation when no action is required
                     _suggestion_msg = "No Action required."
                     _ret = PATCH_SUCCESS_EXIT_CODE
                     self.mAddError(_ret, _suggestion_msg)
                 elif _ec_node_precheck == NO_ACTION_REQUIRED:
                     self.mPatchLogInfo("No action required on _ec_node_precheck.")
                     _ret = _ec_initial_node_precheck
                 else:
                     self.mPatchLogInfo("No action required on _ec_initial_node_precheck.")
                     _ret = _ec_node_precheck

            # Node Failure Case
            elif (_ec_node_precheck != PATCH_SUCCESS_EXIT_CODE or _ec_initial_node_precheck != PATCH_SUCCESS_EXIT_CODE):
                self.mPatchLogInfo("In scenario where one of the precheck failed")
                # Both node failure
                if (_ec_initial_node_precheck != PATCH_SUCCESS_EXIT_CODE and _ec_node_precheck != PATCH_SUCCESS_EXIT_CODE):
                    _ret = DOM0_PRECHECK_EXECUTION_FAILED_ERROR
                    _suggestion_msg = "Patch Prereq check failed on multiple dom0 nodes"
                    self.mAddError(_ret, _suggestion_msg)
                elif (_ec_node_precheck != PATCH_SUCCESS_EXIT_CODE):
                    self.mPatchLogError("_ec_node_precheck failed")
                    _ret = _ec_node_precheck
                elif (_ec_initial_node_precheck != PATCH_SUCCESS_EXIT_CODE):
                    self.mPatchLogError("_ec_initial_node_precheck failed")
                    _ret = _ec_initial_node_precheck
            else:
                self.mPatchLogInfo("PreCheck Operation is Success")
                _ret = PATCH_SUCCESS_EXIT_CODE

        except Exception as e:
            self.mPatchLogError(f"Exception in Running DOM0 PreCheck  {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _suggestion_msg = f"Exception in Running DOM0 Precheck  {str(e)}"
                _ret = INDIVIDUAL_PATCH_REQUEST_EXCEPTION_ERROR 
                self.mAddError(_ret, _suggestion_msg)

        finally:
            #Cleanup keys only for EXACS
            if not self.mIsExaCC():
                self.mPatchLogInfo("Cleanup Environment")
                self.mCleanSSHEnvSetUp()

            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_DOM0}s <---------------\n\n")
            return _ret , _no_action_taken

    def mPreCheckFilesCleanup(self, aNode, aInputFile, aCnsString):
        '''
         Remove temporary patchmgr log files
        '''
        self.mPatchLogInfo("Remove temporary patchmgr log files")
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aNode)
        if _node.mFileExists(aInputFile):
            _node.mExecuteCmdLog(f"rm -f {aInputFile}")

        if _node.mFileExists(self.mGetPatchmgrLogPathOnLaunchNode()):
            # Moving log_dir to log_dir_<launch_node>, before starting another one
            _node.mExecuteCmdLog(
                f"mv -f {self.mGetPatchmgrLogPathOnLaunchNode()} {self.mGetPatchmgrLogPathOnLaunchNode()}_{aNode.split('.')[0]}")

        if _node.mIsConnected():
            _node.mDisconnect()

        # Log location is updated in mUpdateNodePatcherLogDir for proper collection of final CNS notification
        self.mUpdateNodePatcherLogDir(aNode, aCnsString)

    def mPatch(self):

        """
       Does the setup, filter the nodes to patch, idempotency check
       does customcheck and then runs the patch.
       Return codes:
          1) ret -->
              0 for success
              non-zero for failure
          2)  _no_action_taken -->
              0 indicate some action is taken care.
              non-zero indicate no action is taken care.
       """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0
        _list_of_nodes = []

        try:
            self.mPatchLogInfo(f"\n\n---------------> Starting {TASK_PATCH} on {PATCH_DOM0}s <---------------\n\n")

            # check if artifacts are present
            if self.mIsExaSplice() and (not self.mGetDom0LocalPatchZip() or not self.mGetDom0LocalPatchZip2()):
                self.mPatchLogError("Exiting. Patch files missing")
                return MISSING_PATCH_FILES, _no_action_taken

            # 1. Set up environment
            _ret = self.mSetEnvironment()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since return code from mSetEnvironment is {_ret} ")
                return _ret, _no_action_taken

            _launch_nodes = [self.__dom0_to_patch_dom0s, self.mGetDom0ToPatchInitialDom0() ]

            # Perform heartbeat checks before infra patch operations.
            _ret = self.mPerformDomuCrsCheckForAllClusters()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                return _ret , _no_action_taken

            '''
             Perform space validations on root partition
             on Dom0 targets
            '''
            _ret = self.mValidateRootFsSpaceUsage()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mValidateRootFsSpaceUsage is {_ret} ")
                return _ret, _no_action_taken

            # Get customized list of nodes
            _ret, _suggestion_msg, _list_of_nodes, _discarded = self.mFilterNodesToPatch(
                self.mGetCustomizedDom0List(), PATCH_DOM0, TASK_PATCH)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            # Validate for exasplice patch to be applied on list of dom0s.
            if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsExaspliceNot24'):
                _list_of_nodes = self.mGetListOfDom0sWhereExasplicePatchCanBeApplied(_launch_nodes, _list_of_nodes)

            # Set initial Patch Status Json.
            self.mUpdatePatchProgressStatus(aNodeList=_list_of_nodes, aDiscardedNodeList=_discarded)

            # In case of ADBS, the node list would be just one node and if it is already upgraded,
            # check if needs to run dom0domu plugin
            if len(_list_of_nodes) == 0 and len(_discarded) == 1 and self.mIsExacloudPluginEnabled():
                _ret = self.mGetPluginHandler().mExecuteDom0DomuPlugininADBSforCompletedNodes(_discarded[0],
                            self.mGetPluginHandler().mGetRunUserPluginsonDom0sdomuNode())
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    self.mPatchLogError("Error executing ADBS plugins")
                    return _ret, _no_action_taken

            '''
             Enable service state on ilom prior to upgrade.
            '''
            self.mUpdateServiceStateOnIlom(_list_of_nodes, "prepatch")

            # 2. Check for idempotency
            _ret, _no_action_taken = self.mCheckIdemPotency(_discarded)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mSetPatchEnvironment in domU is {_ret} ")
                return _ret , _no_action_taken

            # 3. Perform customcheck
            if len(_discarded) > 0:
                if not self.mIsExaSplice(): 
                    _ret = self.mCustomCheck(aNodes=_discarded, aTaskType=TASK_PATCH)
                    if _ret != PATCH_SUCCESS_EXIT_CODE:
                        return _ret, _no_action_taken

            if len(_list_of_nodes) <= 0:

                # We need to populate more info about the patching operation when
                # no action is required and it requires to update ecra rack status
                # to previous status.
                _suggestion_msg = f"No available {PATCH_DOM0.upper()}s to run the patchmgr. Nothing to do here."
                _ret = PATCH_SUCCESS_EXIT_CODE
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            # Perform stale mounts check
            if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsStaleMountCheckEnabled'):
                _ret, _stale_mount_check_node_list = self.mGetStaleMountNodeList(_list_of_nodes)
                if _ret == SINGLE_NODE_NAME_MISSING:
                    _suggestion_msg = "Single Node Name not specified"
                    _ret = SINGLE_NODE_NAME_MISSING
                    self.mAddError(_ret, _suggestion_msg)
                    return _ret, _no_action_taken

                _has_stale_mounts, _suggestion_msg = self.mHasStaleMounts(_stale_mount_check_node_list)
                if _has_stale_mounts:
                    _ret = DOM0_STALE_MOUNT_CHECK_FAILED
                    self.mAddError(_ret, _suggestion_msg)
                    return _ret, _no_action_taken
            else:
                self.mPatchLogInfo(
                    f'enable_stale_mount_check is disabled in conf file {INFRA_PATCHING_CONF_FILE}. Hence stale mount check is skipped.')

            # 4. Perform the actual operation
            # Runs the dom[0U]s patch(upgrade)/rollback(downgrade) operation in
            #   rolling or non-rolling mode.
            # Returns 0 if the pre-checks, patch, and post-checks run fine.
            # Returns the patchmgr exit code (usualy 1) if there were any errors
            #   running patchmgr.
            # Returns DOM[0U]_POSTCHECKS_FAILED if there were problems running
            #   post-checks.
            # Returns NO_ACTION_REQUIRED if no dom0s were patched or rolled back
            #
            # NOTE : ExaData expects one to install user RPMs only after
            #        exadata-sun-vm-computenode-exact RPM was removed. Else, patching
            #        may fail. At present following RPMs are user installed ones.
            #           krb5-workstation.x86_64
            #           libxenstore.x86_64
            #           dbaastools_exa.x86_64
            #           perl-JSON.noarch
            #           dnsmasq.x86_64
            #           cx_Oracle.x86_64
            #
            # TODO : In order to handle user installed RPMs and what not
            #        It will be better to create a configuration parameter to
            #        control those and just pass those.
            #        It may be something in its own conf file or in exabox.conf:
            #        "exadata_patch_domu_options", "exadata_patch_cell_options" etc..

            _node_to_patch_nodes = self.__dom0_to_patch_dom0s
            _node_to_patch_initial_node = self.mGetDom0ToPatchInitialDom0()
            '''
             _nodes_to_patch_except_initial can only be the customised
             list of nodes as patch operations are required to be performed
             only on the input node provided.
            '''
            _nodes_to_patch_except_initial = list(set(_list_of_nodes) -
                                                  set([self.__dom0_to_patch_dom0s]))
            _initial_node_list = [self.__dom0_to_patch_dom0s]

            if not _node_to_patch_nodes and _node_to_patch_initial_node:
                raise self.mPatchLogError(TASK_PATCH.upper +
                                          " patching is unavailable, " + TASK_PATCH.upper +
                                          " patch files" +
                                          " were not provided at initialization")

            self.mPatchLogInfo(
                f'_node_to_patch_nodes = {str(_node_to_patch_nodes)}, _node_to_patch_initial_node = {str(_node_to_patch_initial_node)}')
            self.mPatchLogInfo(
                f'_nodes_to_patch_except_initial = {str(_nodes_to_patch_except_initial)}, _initial_node_list= {str(_initial_node_list)}')

            # Update status
            self.mUpdatePatchStatus(True, STEP_FILTER_NODES + '_' + PATCH_DOM0)

            _dont_rollback = False
            # get the list of the dom0s that actually require patching
            _nodes_that_require_patching = _list_of_nodes[:]
            self.mPatchLogInfo("_nodes_that_require_patching" +str(_nodes_that_require_patching))
            if len(_nodes_that_require_patching) == 0:
                _no_action_taken += 1
                return NO_ACTION_REQUIRED, _no_action_taken
            else:
                #  contains tuples of the form [(patcher_node, [nodes_to_patch]), .. ]
                _node_patcher_and_node_patch_list = []
                _external_launch_nodes = self.mGetExternalLaunchNode()
                #Currently supporting single launch node only
                if len(_external_launch_nodes) > 0:
                    _node_patcher_and_node_patch_list.append((_external_launch_nodes[0], _nodes_that_require_patching))
                else:
                    # if the dom[0U] that patches all other dom[0U]s (except itself) requieres
                    # patching, then add it and add the node that will patch it to the list
                    if _node_to_patch_nodes in _nodes_that_require_patching:
                        _node_patcher_and_node_patch_list.append(
                            (_node_to_patch_initial_node, [_node_to_patch_nodes]))
                        _nodes_that_require_patching.remove(_node_to_patch_nodes)

                    # if any more dom[0U]s require patching, use the dom[0U] designated to
                    # patch all other dom[0U]
                    if _nodes_that_require_patching:
                        _node_patcher_and_node_patch_list.append(
                            (_node_to_patch_nodes, _nodes_that_require_patching))
                self.mPatchLogInfo(f"_node_patcher_and_node_patch_list: {str(_node_patcher_and_node_patch_list)}")
                _operationStyle = self.mGetOpStyle()
                if _operationStyle == OP_STYLE_ROLLING:
                    _ret = self.mPatchRollbackDom0sRolling(
                        self.mGetBackUpMode(),
                        aNodePatcherAndPatchList=_node_patcher_and_node_patch_list, aListOfNodesToBePatched=_list_of_nodes, aRollback=False)
                elif _operationStyle == OP_STYLE_NON_ROLLING:
                    _ret = self.mPatchRollbackDom0sNonRolling(
                        self.mGetBackUpMode(),
                        aNodePatcherAndPatchList=_node_patcher_and_node_patch_list, aListOfNodesToBePatched=_list_of_nodes, aRollback=False)
                else:
                    _msg = f"{PATCH_DOM0.upper()} patching operation style [{_operationStyle}] not recognized or unsupported"
                    self.mPatchLogError(_msg)
                    raise Exception(_msg)


            if _ret == NO_ACTION_REQUIRED:
                _no_action_taken += 1
                # We need to populate more info about the patching
                # operation when no action is required and need to
                # update ecra rack status to previous status.
                _suggestion_msg = "No action required."
                _ret = PATCH_SUCCESS_EXIT_CODE
                self.mAddError(_ret, _suggestion_msg)

            # Updates time for last post patch stage
            self.mUpdateInfrapatchingTimeStatsForUnfilledStages()
            # Capture time profile details for post_patch activity done on all nodes
            self.mCreateInfrapatchingTimeStatsEntry(str(self.mGetDom0List()), "POST_PATCH")

        except Exception as e:
            self.mPatchLogError(f"Exception in Running Dom0 Patch {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _suggestion_msg = f"Exception in Running DOM0 Patch {str(e)}"
                _ret = INDIVIDUAL_PATCH_REQUEST_EXCEPTION_ERROR
                self.mAddError(_ret, _suggestion_msg)

        finally:
            # Disable ServiceState on ilom post upgrade.
            self.mUpdateServiceStateOnIlom(_list_of_nodes, "postpatch")

            #Cleanup keys only for EXACS
            if not self.mIsExaCC():
                self.mPatchLogInfo("Cleanup Environment")
                self.mCleanSSHEnvSetUp()

            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_DOM0}s <---------------\n\n")
            return _ret, _no_action_taken

    def mOneOff(self):
        """
        This method suppose to run any user script staged by user on plugin area.
        Return code:

           PATCH_SUCCESS_EXIT_CODE for success.
           Any other error code other than PATCH_SUCCESS_EXIT_CODE for failure.
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        self.mPatchLogInfo(f"\n\n---------------> Starting {TASK_ONEOFF} on {PATCH_DOM0}s <---------------\n\n")
        try:
            # Check if oneoff plugin is enabled by the framework
            if self.mGetPluginHandler() and self.mIsOneOffPluginEnabled():
                '''
                 One off is applied only on the custom 
                 node list.
                '''
                _node_list = self.mGetCustomizedDom0List()
                self.mGetPluginHandler().mSetNodeList(_node_list)
                self.mGetPluginHandler().mSetPluginTarget(PATCH_DOM0)

                # Execute oneoff plugin
                _ret = self.mGetPluginHandler().mApply()
                return _ret
            else:
                _ret = ONEOFF_APPLY_FAILED
                _suggestion_msg = TASK_ONEOFF.upper() + " plugin is unavailable for " + PATCH_DOM0.upper()
                self.mAddError(_ret, _suggestion_msg)
                raise self.mPatchLogError(TASK_ONEOFF.upper() +
                                          " plugin is unavailable for " + PATCH_DOM0.upper())
        except Exception as e:
            self.mPatchLogError("Exception in Running Dom0 OneOff Plugin  " + str(e))
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_DOM0}s <---------------\n\n")
            pass

    def mOneOffv2(self):
        """
        This method suppose to run any user script staged by user on plugin area
        using the oneoff v2 implementation.
        
        Return code:

           PATCH_SUCCESS_EXIT_CODE for success.
           Any other error code other than PATCH_SUCCESS_EXIT_CODE for failure.
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        self.mPatchLogInfo(f"\n\n---------------> Starting {TASK_ONEOFFV2} on {PATCH_DOM0}s <---------------\n\n")
        try:
            # Check if oneoff plugin is enabled by the framework
            if self.mGetPluginHandler() and self.mIsOneOffV2PluginEnabled():
                # Execute oneoff plugin
                _ret = self.mGetPluginHandler().mApply()
        except Exception as e:
            _suggestion_msg = f"Exception in Running Dom0 Oneoff V2 Plugin : {str(e)}"
            _ret = ONEOFFV2_EXCEPTION_ENCOUNTERED
            self.mAddError(_ret, _suggestion_msg)
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_DOM0}s <---------------\n\n")
            return _ret

    def mRollBack(self):

        """
        Does the setup, filter the nodes to rollback ,
        idempotency check, custom check and then run the rollback.
        Return codes:
           1) ret -->
               0 for success
               non-zero for failure
           2)  _no_action_taken -->
               0 indicate some action is taken care.
               non-zero indicate no action is taken care.
        """

        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0
        _err_msg_template = "%s %s failed. Errors printed to screen and logs"
        try:
            self.mPatchLogInfo(f"\n\n---------------> Starting {TASK_ROLLBACK} on {PATCH_DOM0}s <---------------\n\n")
            # 1. Set up environment
            _ret = self.mSetEnvironment()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since return code from mSetEnvironment is {_ret} ")
                return _ret, _no_action_taken

            _launch_nodes = [self.__dom0_to_patch_dom0s, self.mGetDom0ToPatchInitialDom0()]

            # Perform heartbeat checks before infra patch operations.
            _ret = self.mPerformDomuCrsCheckForAllClusters()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                return _ret , _no_action_taken

            '''
             Perform space validations on root partition
             on Dom0 targets
            '''
            _ret = self.mValidateRootFsSpaceUsage()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mValidateRootFsSpaceUsage is {_ret} ")
                return _ret, _no_action_taken

            # Get customized list of nodes
            _ret, _suggestion_msg, _list_of_nodes, _discarded = self.mFilterNodesToPatch(
                self.mGetCustomizedDom0List(), PATCH_DOM0, TASK_ROLLBACK)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            # Set initial Patch Status Json.
            self.mUpdatePatchProgressStatus(aNodeList=_list_of_nodes, aDiscardedNodeList=_discarded)

            # 2. Check for idempotency
            _ret, _no_action_taken = self.mCheckIdemPotency(_discarded)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mSetPatchEnvironment in domU is {_ret} ")
                return _ret , _no_action_taken

            # 3. Perform customcheck
            if len(_discarded) > 0:
                _ret = self.mCustomCheck(aNodes=_discarded)
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    _ret = INFRA_PATCHING_DOM0_SERVICES_NOT_RUNNING
                    return _ret, _no_action_taken

            if len(_list_of_nodes) <= 0:

                # We need to populate more info about the patching operation when
                # no action is required and it requires to update ecra rack status
                # to previous status.
                _suggestion_msg = f"No available {PATCH_DOM0.upper()}s to run the patchmgr. Nothing to do here."
                _rc = PATCH_SUCCESS_EXIT_CODE
                self.mAddError(_rc, _suggestion_msg)
                return _rc, _no_action_taken

            # 4. Perform the actual rollback operation
            # Runs the dom[0U]s patch(upgrade)/rollback(downgrade) operation in
            #   rolling or non-rolling mode.
            # Returns 0 if the pre-checks, patch, and post-checks run fine.
            # Returns the patchmgr exit code (usualy 1) if there were any errors
            #   running patchmgr.
            # Returns DOM[0U]_POSTCHECKS_FAILED if there were problems running
            #   post-checks.
            # Returns NO_ACTION_REQUIRED if no dom0s were patched or rolled back
            #
            # NOTE : ExaData expects one to install user RPMs only after
            #        exadata-sun-vm-computenode-exact RPM was removed. Else, patching
            #        may fail. At present following RPMs are user installed ones.
            #           krb5-workstation.x86_64
            #           libxenstore.x86_64
            #           dbaastools_exa.x86_64
            #           perl-JSON.noarch
            #           dnsmasq.x86_64
            #           cx_Oracle.x86_64
            #
            # TODO : In order to handle user installed RPMs and what not
            #        It will be better to create a configuration parameter to
            #        control those and just pass those.
            #        It may be something in its own conf file or in exabox.conf:
            #        "exadata_patch_domu_options", "exadata_patch_cell_options" etc..

            _node_to_patch_nodes = self.__dom0_to_patch_dom0s
            _node_to_patch_initial_node = self.mGetDom0ToPatchInitialDom0()
            '''
             _nodes_to_patch_except_initial can only be the customised
             list of nodes as patch operations are required to be performed
             only on the input node provided.
            '''
            _nodes_to_patch_except_initial = list(set(_list_of_nodes) -
                                                  set([self.__dom0_to_patch_dom0s]))
            _initial_node_list = [self.__dom0_to_patch_dom0s]

            if not _node_to_patch_nodes and _node_to_patch_initial_node:
                raise self.mPatchLogError(PATCH_DOM0.upper +
                                          " patching is unavailable, " + PATCH_DOM0.upper +
                                          " patch files" +
                                          " were not provided at initialization")

            self.mPatchLogInfo(
                f'_node_to_patch_nodes = {str(_node_to_patch_nodes)}, _node_to_patch_initial_node = {str(_node_to_patch_initial_node)}')
            self.mPatchLogInfo(
                f'_nodes_to_patch_except_initial = {str(_nodes_to_patch_except_initial)}, _initial_node_list= {str(_initial_node_list)}')

            # Update status
            self.mUpdatePatchStatus(True, STEP_FILTER_NODES + '_' + PATCH_DOM0)

            _dont_rollback = False
            # get the list of the dom0s that actually requiere patching
            _nodes_that_require_patching = []

            for _node in _list_of_nodes:
                if not self.mIsMockEnv() and self.mRollbackIsAvailable(_node):
                    # if the dbnode is at a lower version than the requested
                    # version, dont attempt to rollback.
                    # This is to stop doing a rollback after a rollback
                    # (ie: you can/should only rollback once)
                    # after a sucessfull upgrade
                    if (self.mGetCluPatchCheck().mCheckTargetVersion(_node,
                                                                     PATCH_DOM0, self.mGetTargetVersion(), aIsexasplice= self.mIsExaSplice()) < 0):
                        self.mPatchLogInfo(
                            f"{PATCH_DOM0.upper()} [{_node}] cannot be rolled back, its version is lower than the target version")
                        continue

                    # Compare rollback version and target version to see if rollback is really required
                    if self.mIsInActiveVersionGreaterThanTargetVersion(_node,PATCH_DOM0,self.mIsExaSplice()):
                        continue

                    '''
                     Bug:23499655 Block Dom0 rollback if fresh service created after patch

                     Do not perform this validation on a kvm environment as the KVM env 
                     has a different naming convention for the VM configuration files unlike
                     vm.cfg in case of xen environment.

                     KVM specific validations will be performed as part of the below ER

                     Enh 34600712 - EXACS:22.2.1.1:220909, KVM/MULTI-VM, ERROR OUT ON A 
                                    ROLLBACK ON DOM0 IF THERE IS A PROVISIONING
                    '''
                    if EXACLOUD_DO_DOM0_ROLLBACK_EVEN_IF_DOMU_MODIFIED_POST_PATCH or self.mIsKvmEnv():
                        self.mPatchLogInfo(f"Skipping creation/modification time check on for domU's on {_node}")
                    # check to make sure no new domU were created or modified after a previous dom0 patch
                    else:
                        _dom0_node = exaBoxNode(get_gcontext())
                        _dom0_node.mConnect(aHost=_node)

                        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsExaspliceNot24'):
                            _i, _o, _e = _dom0_node.mExecuteCmd("date '+%s' -d \"`imageinfo -activatedexasplice`\"")
                        else:
                            _i, _o, _e = _dom0_node.mExecuteCmd("date '+%s' -d \"`imageinfo -activated`\"")

                        _dom0_activation_date = mFormatOut(_o).strip()

                        _i, _o, _e = _dom0_node.mExecuteCmd(
                            r"stat -c '%Y' /EXAVMIMAGES/GuestImages/*/vm.cfg | sort -n | tail -n 1")
                        _oldest_domU_modification_date = mFormatOut(_o).strip()

                        _dom0_node.mDisconnect()

                        self.mPatchLogInfo(
                            f"Dom0 activation date: '{_dom0_activation_date}' latest domU vm.cfg modification date: '{_oldest_domU_modification_date}'")
                        try:
                            _oldest_domU_modification_date = int(_oldest_domU_modification_date)
                            _dom0_activation_date = int(_dom0_activation_date)
                        except (ValueError, TypeError) as e:
                            self.mPatchLogInfo(
                                f"No vm.cfg were detected or errors parsing vm.cfg modification time to int for domU on dom0: '{_node}'. This check will be skipped for this dom0. Exception: {str(e)}")
                            _oldest_domU_modification_date, _dom0_activation_date = 0, 0

                        if _oldest_domU_modification_date > _dom0_activation_date:
                            _suggestion_msg = f"one or more domUs were created (or had vm.cfg settings modified) after {_node} has been patched. Unable to rollback any dom0."
                            _rc = DOM0_ROLLBACK_NOT_ALLOWED_ERROR
                            self.mAddError(_rc, _suggestion_msg)
                            # even though we can just return here and stop the rollback action, lets check the next dom0
                            #  for a more complete error report
                            _dont_rollback = True
                            continue

                else:  # rollback is not available, just skip it
                    if not self.mIsMockEnv():
                        self.mPatchLogInfo(f"{PATCH_DOM0} [{_node}] cannot be rolled back, rollback is not available")
                        continue
                _nodes_that_require_patching.append(_node)

            if _dont_rollback:
                _ret = DOM0_ROLLBACK_FAILED_INCONSISTENT_DOM0_DOMU_VERSION
                _suggestion_msg = _err_msg_template % (PATCH_DOM0.upper(),
                                                       "rollback unavailable because it would cause inconsistencies with versions on Dom0 and its DomU")
                self.mAddError(_ret, _suggestion_msg)
                return _ret , _no_action_taken

            if len(_nodes_that_require_patching) == 0:
                _no_action_taken += 1
                return NO_ACTION_REQUIRED, _no_action_taken
            _node_patcher_and_node_patch_list = []
            _external_launch_nodes = self.mGetExternalLaunchNode()
            # Currently supporting single launch node only
            if len(_external_launch_nodes) > 0:
                _node_patcher_and_node_patch_list.append((_external_launch_nodes[0], _nodes_that_require_patching))
            else:
                # if the dom[0U] that patches all other dom[0U]s (except itself) requieres
                # patching, then add it and add the node that will patch it to the list
                if _node_to_patch_nodes in _nodes_that_require_patching:
                    _node_patcher_and_node_patch_list.append(
                        (_node_to_patch_initial_node, [_node_to_patch_nodes]))
                    _nodes_that_require_patching.remove(_node_to_patch_nodes)

                # if any more dom[0U]s require patching, use the dom[0U] designated to
                # patch all other dom[0U]
                if _nodes_that_require_patching:
                    _node_patcher_and_node_patch_list.append(
                        (_node_to_patch_nodes, _nodes_that_require_patching))
            self.mPatchLogInfo(f"_node_patcher_and_node_patch_list:\n {str(_node_patcher_and_node_patch_list)}")

            _operationStyle = self.mGetOpStyle()
            if _operationStyle == OP_STYLE_ROLLING:
                _ret = self.mPatchRollbackDom0sRolling(
                    self.mGetBackUpMode(),
                    aNodePatcherAndPatchList=_node_patcher_and_node_patch_list,
                    aListOfNodesToBePatched=_list_of_nodes,
                    aRollback=True)
            elif _operationStyle == OP_STYLE_NON_ROLLING:
                _ret = self.mPatchRollbackDom0sNonRolling(
                    self.mGetBackUpMode(),
                    aNodePatcherAndPatchList=_node_patcher_and_node_patch_list,
                    aListOfNodesToBePatched=_list_of_nodes,
                    aRollback=True)
            else:
                _msg = f"{PATCH_DOM0.upper()} patching operation style [{_operationStyle}] not recognized or unsupported"
                self.mPatchLogError(_msg)
                raise Exception(_msg)

            if _ret == NO_ACTION_REQUIRED:
                _no_action_taken += 1
                # We need to populate more info about the patching
                # operation when no action is required and need to
                # update ecra rack status to previous status.
                _suggestion_msg = "Nodes are upto date, no further action required."
                _ret = PATCH_SUCCESS_EXIT_CODE
                self.mAddError(_ret, _suggestion_msg)

            # Updates time for last post patch stage
            self.mUpdateInfrapatchingTimeStatsForUnfilledStages()
            # Capture time profile details for post_patch activity done on all nodes
            self.mCreateInfrapatchingTimeStatsEntry(str(self.mGetDom0List()), "POST_PATCH")

        except Exception as e:
            self.mPatchLogError(f"Exception in Running DOM0 Rollback {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _suggestion_msg = f"Exception in Running DOM0 Rollback {str(e)}"
                _ret = INDIVIDUAL_PATCH_REQUEST_EXCEPTION_ERROR
                self.mAddError(_ret, _suggestion_msg)

        finally:
            #Cleanup keys only for EXACS
            if not self.mIsExaCC():
                self.mPatchLogInfo("Cleanup Environment")
                self.mCleanSSHEnvSetUp()
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_DOM0}s <---------------\n\n")
            return _ret, _no_action_taken

    def mImageBackup(self):
        """
         Does the setup, filter the nodes to patch, idempotency check
         does customcheck and then performs the image rollback.
         Return codes:
           1) ret -->
               0 for success
               non-zero for failure
           2)  _no_action_taken -->
               0 indicate some action is taken care.
               non-zero indicate no action is taken care.
           3) Backup operation always run as non-rolling to save the
              time. Also, since patchmgr notification has some issue
              with rolling, it's always recommended to run backup as
              non-rolling.
        """

        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0
        try:
            self.mPatchLogInfo(
                f"\n\n---------------> Starting {TASK_BACKUP_IMAGE} on {PATCH_DOM0}s <---------------\n\n")

            # 1. Set up environment
            self.mSetEnvironment()
            _launch_nodes = [self.__dom0_to_patch_dom0s, self.mGetDom0ToPatchInitialDom0()]

            '''
             Perform space validations on root partition
             on Dom0 targets
            '''
            _ret = self.mValidateRootFsSpaceUsage()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mValidateRootFsSpaceUsage is {_ret} ")
                return _ret , _no_action_taken

            # Get customized list of nodes
            _ret, _suggestion_msg, _list_of_nodes, _discarded = self.mFilterNodesToPatch(
                self.mGetCustomizedDom0List(), PATCH_DOM0, TASK_BACKUP_IMAGE)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            # Set initial Patch Status Json.
            self.mUpdatePatchProgressStatus(aNodeList=_list_of_nodes, aDiscardedNodeList=_discarded)

            # 2. Check for idempotency
            _ret, _no_action_taken = self.mCheckIdemPotency(_discarded)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mSetPatchEnvironment in domU is {_ret} ")
                return _ret , _no_action_taken

            # 3. Perform customcheck
            if len(_discarded) > 0:
                _ret = self.mCustomCheck(aNodes=_discarded)
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    return _ret, _no_action_taken

            if len(_list_of_nodes) <= 0:

                # We need to populate more info about the patching operation when
                # no action is required and it requires to update ecra rack status
                # to previous status.
                _suggestion_msg = f"No available {PATCH_DOM0.upper()}s to run the patchmgr. Nothing to do here."
                _rc = PATCH_SUCCESS_EXIT_CODE
                self.mAddError(_rc, _suggestion_msg)
                return _rc, _no_action_taken

            # Perform system consistency check
            _is_system_valid_state, _suggestion_msg = self.mCheckSystemConsitency(_list_of_nodes)
            if not _is_system_valid_state:
                _ret = DOM0_SYSTEM_CONSISTENCY_CHECK_FAILED
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            '''
             Performing Auto start validations of DomU currently
             up and running on the current Dom0 during Dom0 precheck.
            '''
            for _dom0 in _list_of_nodes:
                _domU_listed_by_xm_list = self.mGetCluPatchCheck().mCheckVMsUp(_dom0)
                self.mPatchLogInfo(f"List of domUs : {str(_domU_listed_by_xm_list)} running on dom0 :{_dom0} ")
                if len(_domU_listed_by_xm_list) > 0:
                    _ret = self.mGetCluPatchCheck().mValidateAndEnableDomuAutoStartup(_dom0,_domU_listed_by_xm_list)
                    if _ret != PATCH_SUCCESS_EXIT_CODE:
                        return _ret, _no_action_taken

            # Bug27643008 - Enhance to support image backup
            _node_to_patch_nodes = self.__dom0_to_patch_dom0s
            _node_to_patch_initial_node = self.mGetDom0ToPatchInitialDom0()
            '''
             _nodes_to_patch_except_initial can only be the customised
             list of nodes as patch operations are required to be performed
             only on the input node provided.
            '''
            _nodes_to_patch_except_initial = list(set(_list_of_nodes) -
                                                  set([self.__dom0_to_patch_dom0s]))
            _initial_node_list = [self.__dom0_to_patch_dom0s]
            _cns_string = CNS_DOM0_PATCHER
            _callbacks = self.mGetCallBacks()
            self.mPatchLogInfo(
                f'_node_to_patch_nodes = {str(_node_to_patch_nodes)}, _node_to_patch_initial_node = {str(_node_to_patch_initial_node)}')
            self.mPatchLogInfo(
                f'_nodes_to_patch_except_initial = {str(_nodes_to_patch_except_initial)}, _initial_node_list= {str(_initial_node_list)}')

            _ec_node_backup = PATCH_SUCCESS_EXIT_CODE
            _ec_initial_node_backup = PATCH_SUCCESS_EXIT_CODE

            # Initialize actual patchmgr location before it is renamed.
            _actual_patchmgr_log_on_launch_node = self.mGetPatchmgrLogPathOnLaunchNode()

            # update current node being used to upgrade i.e., __dom0_to_patch_dom0
            _node_patch_progress = os.path.join(self.mGetLogPath(), _cns_string)
            try:
                with open(_node_patch_progress, "w") as write_nodestat:
                    write_nodestat.write(f"{_node_to_patch_nodes}:{self.mGetPatchmgrLogPathOnLaunchNode()}")
            except Exception as e:
                self.mPatchLogWarn(f'Failed to write {_node_patch_progress}: {str(e)}')
                self.mPatchLogTrace(traceback.format_exc())

            # Run the image backup in all the dom[0U]s except one
            _ec_node_backup = self.mPatchImageBackupDom0Node(aNode=_node_to_patch_nodes,
                                                             aListOfNodesToPatch=_nodes_to_patch_except_initial,
                                                             aCnsString=_cns_string,
                                                             aPatchInitNode=False)

            if _ec_node_backup == EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR:
                self.mPatchLogInfo(f"Infra patching failed due to Exacloud timeout - Return code - {_ec_node_backup}")
                return _ec_node_backup, _no_action_taken

            # Log location was renamed for supporting idempotency. Resetting -log_dir to
            # actual path for collecting notifications.
            self.mSetPatchmgrLogPathOnLaunchNode(_actual_patchmgr_log_on_launch_node)

            # update current node being used to upgrade i.e., to
            # __dom0_to_patch_initial_dom0 (self.mGetDom0ToPatchInitialDom0())
            try:
                with open(_node_patch_progress, "w") as write_nodestat:
                    write_nodestat.write(f"{_node_to_patch_initial_node}:{self.mGetPatchmgrLogPathOnLaunchNode()}")
            except Exception as e:
                self.mPatchLogWarn(f'Failed to write {_node_patch_progress}: {str(e)}')
                self.mPatchLogTrace(traceback.format_exc())

            # Run the image backup in the inital dom[0U]s
            _ec_initial_node_backup = self.mPatchImageBackupDom0Node(aNode=_node_to_patch_initial_node,
                                                                     aListOfNodesToPatch=_initial_node_list,
                                                                     aCnsString=_cns_string,
                                                                     aPatchInitNode=True)

            if _ec_initial_node_backup == EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR:
                self.mPatchLogInfo(
                    f"Infra patching failed due to Exacloud timeout - Return code - {_ec_initial_node_backup}")
                return _ec_initial_node_backup, _no_action_taken

            if (_ec_node_backup == NO_ACTION_REQUIRED or
                     _ec_initial_node_backup == NO_ACTION_REQUIRED):
                 self.mPatchLogInfo("In scenario where NO ACTION REQUIRED on one node")
                 if (_ec_node_backup == NO_ACTION_REQUIRED and
                         _ec_initial_node_backup == NO_ACTION_REQUIRED):
                     self.mPatchLogInfo("No action required on multiple nodes.")
                     _no_action_taken += 1
                     # We need to populate more info about the patching
                     # operation when no action is required
                     _suggestion_msg = "No Action required."
                     _ret = PATCH_SUCCESS_EXIT_CODE
                     self.mAddError(_ret, _suggestion_msg)
                 elif _ec_node_backup == NO_ACTION_REQUIRED:
                     self.mPatchLogInfo("No action required on _ec_node_backup.")
                     _ret = _ec_initial_node_backup
                 else:
                     self.mPatchLogInfo("No action required on _ec_initial_node_backup.")
                     _ret = _ec_node_backup
            # Node Failure Case
            elif (_ec_node_backup != PATCH_SUCCESS_EXIT_CODE or _ec_initial_node_backup != PATCH_SUCCESS_EXIT_CODE):
                self.mPatchLogInfo("In scenario where one of the precheck failed")
                # Both node failure
                if (_ec_initial_node_backup != PATCH_SUCCESS_EXIT_CODE and _ec_node_backup != PATCH_SUCCESS_EXIT_CODE):
                    _ret = DOM0_BACKUP_EXECUTION_FAILED_ERROR
                    _suggestion_msg = "Patch Backup check failed on multiple dom0 nodes"
                    self.mAddError(_ret, _suggestion_msg)
                elif (_ec_node_backup != PATCH_SUCCESS_EXIT_CODE):
                    self.mPatchLogError("_ec_node_backup failed")
                    _ret = _ec_node_backup
                elif (_ec_initial_node_backup != PATCH_SUCCESS_EXIT_CODE):
                    self.mPatchLogError("_ec_initial_node_backup failed")
                    _ret = _ec_initial_node_backup
            else:
                self.mPatchLogInfo("Backup Operation is Success")
                _ret = PATCH_SUCCESS_EXIT_CODE

        except Exception as e:
            self.mPatchLogError(f"Exception in Running DOM0 ImageBackup {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _suggestion_msg = f"Exception in Running DOM0 ImageBackup {str(e)}"
                _ret = PATCH_DOM0_IMAGE_BACKUP_ERROR_EXCEPTION
                self.mAddError(_ret, _suggestion_msg)

        finally:
            #Cleanup keys only for EXACS
            if not self.mIsExaCC():
                self.mPatchLogInfo("Cleanup Environment")
                self.mCleanSSHEnvSetUp()
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_DOM0}s <---------------\n\n")
        return _ret, _no_action_taken

    def mPostCheck(self):

        """
        Does only customcheck which takes care of basic validations.
        Return codes:
           1) ret -->
               0 for success
               non-zero for failure
           2)  _no_action_taken -->
               0 indicate some action is taken care.
               non-zero indicate no action is taken care.
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0
        try:
            self.mPatchLogInfo(
                f"\n\n---------------> Starting {TASK_POSTCHECK} on {PATCH_DOM0}s <---------------\n\n")
            # 1. Set up environment
            self.mSetEnvironment()
            _launch_nodes = [self.__dom0_to_patch_dom0s, self.mGetDom0ToPatchInitialDom0()]

            # Perform heartbeat checks before infra patch operations.
            _ret = self.mPerformDomuCrsCheckForAllClusters()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                return _ret , _no_action_taken

            # Get customized list of nodes
            _ret, _suggestion_msg, _list_of_nodes, _discarded = self.mFilterNodesToPatch(
                self.mGetCustomizedDom0List(), PATCH_DOM0, TASK_POSTCHECK)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            # 2. Check for idempotency
            _ret, _no_action_taken = self.mCheckIdemPotency(_discarded)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mSetPatchEnvironment in domU is {_ret} ")
                return _ret , _no_action_taken

            if len(_list_of_nodes) <= 0:

                # We need to populate more info about the patching operation when
                # no action is required and it requires to update ecra rack status
                # to previous status.
                _suggestion_msg = f"No available {PATCH_DOM0.upper()}s to run the patchmgr. Nothing to do here."
                _ret = PATCH_SUCCESS_EXIT_CODE
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            # Dom0 Independent Postchecks
            _ret = self.mCustomCheck(aNodes=self.mGetCustomizedDom0List())

        except:
            self.mPatchLogError("Failed to Perform PostCheck for Dom0")
            self.mPatchLogTrace(traceback.format_exc())
            _suggestion_msg = f"Failed to Perform PostCheck for Dom0 List : {str(self.mGetCustomizedDom0List())}"
            _ret = PATCH_OPERATION_FAILED
            self.mAddError(_ret, _suggestion_msg)

        finally:
            #Cleanup keys only for EXACS
            if not self.mIsExaCC():
                self.mPatchLogInfo("Cleanup Environment")
                self.mCleanSSHEnvSetUp()
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_DOM0}s <---------------\n\n")
            return _ret, _no_action_taken

    def mPatchImageBackupDom0Node(self, aNode, aListOfNodesToPatch,
                                  aCnsString, aPatchInitNode=False):
        """
        Returns 0, if patchmgr takes backup.
        Returns non-zero, if backup is not taken or failed.
        """
        _node_patcher = aNode
        _exit_code = PATCH_SUCCESS_EXIT_CODE
        _patchMgrObj = None

        self.mPatchLogInfo(f'Launch node = {aNode}, List of Nodes to work on = {aListOfNodesToPatch}')

        ##### TBD: check if all vms are in the cluster (heartbeat).
        for _dom0u_to_patch in aListOfNodesToPatch[:]:
            # check if all dom[0u]s are healthy/pingable first
            if not self.mGetCluPatchCheck().mPingNode(_dom0u_to_patch):
                aListOfNodesToPatch.remove(_dom0u_to_patch)
                self.mPatchLogWarn(f"{PATCH_DOM0.upper()} {_dom0u_to_patch} is not pingable.")

        if not aListOfNodesToPatch:
            # No need to check CNS at the end of cluster since no image
            # backup is taken on nodes
            _exit_code = PATCH_DOM0_IMAGE_BACKUP_ERROR_EXCEPTION
            _suggestion_msg = f"No {PATCH_DOM0.upper()}s to take image backup."
            self.mAddError(_exit_code, _suggestion_msg)
            return _exit_code

        # Update status
        if not aPatchInitNode:
            self.mUpdatePatchStatus(True,
                                    STEP_FILTER_NODES + '_' + PATCH_DOM0 + '_1')
        else:
            self.mUpdatePatchStatus(True,
                                    STEP_FILTER_NODES + '_' + PATCH_DOM0 + '_2')

        if not aPatchInitNode:
            self.mUpdatePatchStatus(True, STEP_RUN_PATCH_DOM0)
            _update_msg = STEP_CLEAN_ENV + '_' + PATCH_DOM0 + '_1'
        else:
            self.mUpdatePatchStatus(True, STEP_RUN_PATCH_SECOND_DOM0)
            _update_msg = STEP_CLEAN_ENV + '_' + PATCH_DOM0 + '_2'

        # create patchmgr object with bare minimum arguments local to this function for fresh InfraPatchManager obj ref
        # everytime the function executes to avoid using old InfraPatchManager obj attribute ref, if any
        _patchMgrObj = InfraPatchManager(aTarget=PATCH_DOM0, aOperation=TASK_BACKUP_IMAGE, aPatchBaseAfterUnzip=self.__dom0_patch_base_after_unzip,
                                   aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

        # create patchmgr nodes file
        _input_file = _patchMgrObj.mCreateNodesToBePatchedFile(aLaunchNode=_node_patcher, aHostList=aListOfNodesToPatch)
        self.__dom0_patchmgr_input_file = _input_file

        # prepare the patchmgr command for execution using the InfraPatchManager object
        _patch_backup_cmd = _patchMgrObj.mGetPatchMgrCmd()

        # If there are no patchmgr sessions running, then run patchmgr command
        # In this context, PATCH_SUCCESS_EXIT_CODE infers NO_PATCHMGR Session is running.

        _patchmgr_session_exit = PATCH_SUCCESS_EXIT_CODE
        _patchmgr_active_node = None

        # Skip patchmgr existence check during clusterless patching.
        if self.mPerformPatchmgrExistenceCheck():
            # check for patchmgr session existence
            _patchMgrObj.mSetLaunchNode(aLaunchNode=None)
            _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=self.mGetCustomizedDom0List())

            _patchmgr_session_exit, _patchmgr_active_node = _patchMgrObj.mCheckForPatchMgrSessionExistence()

        # 1.- Run patchmgr backup
        if _patchmgr_session_exit == PATCH_SUCCESS_EXIT_CODE:  # No patchmgr session found in any of the nodes, so re-execute
            # set the launch node and execute patchmgr cmd
            _patchMgrObj.mSetLaunchNode(aLaunchNode=_node_patcher)

            _exit_code = _patchMgrObj.mExecutePatchMgrCmd(aPatchMgrCmd=_patch_backup_cmd)
            if _exit_code != PATCH_SUCCESS_EXIT_CODE:
                return _exit_code
        else:
            # TODO: We need to handle patch non-retry in future. Time being we are forcibly stopping.
            if not self.mPatchRequestRetried():
                self.mPatchLogError('Found older patchmgr session. Forcibly terminating patching request')
                return _patchmgr_session_exit

            # Already patchmgr is running, just monitor patchmgr console on the node.
            _patchMgrObj.mSetLaunchNode(aLaunchNode=_patchmgr_active_node)
            _node_patcher = _patchmgr_active_node

        # reset the node list to make sure patchmgr cmd execution 
        # only looked at the launch node
        _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=None)

        # Following InfraPatchManager api sets the patchmgr execution status into mStatusCode method
        # hence not required to return/read a value from this api
        # this will help to use the patchMgr status apis 
        # (mIsSuccess/mIsFailed/mIsTimedOut/mIsCompleted) wherever required
        _patchMgrObj.mWaitForPatchMgrCmdExecutionToComplete()

        self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")

        _exit_code = _patchMgrObj.mGetStatusCode()

        if len(aListOfNodesToPatch) > 0:
            # 2 .- Update status
            self.mUpdatePatchStatus(True, _update_msg)

            # 3.- Get patchmgr backup logs
            _precheck_log = str(
                self.mGetDom0FileCode(_node_patcher,
                                      self.mGetPatchmgrLogPathOnLaunchNode()))
            self.mGetPatchMgrOutFiles(_node_patcher,
                                      self.mGetPatchmgrLogPathOnLaunchNode(),
                                      _precheck_log)

            '''
             Collect patchmgr diag logs for debugging only
             when the final exit code from patch operation 
             is not PATCH_SUCCESS_EXIT_CODE.
            '''
            if _exit_code != PATCH_SUCCESS_EXIT_CODE:
                self.mGetPatchMgrDiagFiles(_node_patcher,
                                           PATCH_DOM0,
                                           aListOfNodesToPatch,
                                           self.mGetPatchmgrLogPathOnLaunchNode())
            else:
                self.mPatchLogInfo("Patchmgr diag logs are not collected in case of a successful infra patch operation.")

        # Print all the log details at the end of log files copy.
        self.mPrintPatchmgrLogFormattedDetails()

        # 4. Remove temporary patchmgr log files
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_node_patcher)
        _node.mExecuteCmdLog(f"rm -f {_input_file}")

        # Moving log_dir to log_dir_<launch_node>, before starting another one
        _node.mExecuteCmdLog(
            f"mv -f {self.mGetPatchmgrLogPathOnLaunchNode()} {self.mGetPatchmgrLogPathOnLaunchNode()}_{_node_patcher.split('.')[0]}")

        _node.mDisconnect()

        # Log location is updated in mUpdateNodePatcherLogDir for proper collection of final CNS notification
        self.mUpdateNodePatcherLogDir(_node_patcher, aCnsString)

        return _exit_code


    # Remove obsolete ssh keys from authorized_keys file.
    # From Exadata image 23.x, the target OS will be upgraded to OL8
    # where dsa keys become obsolete. This block checks presence of any
    # obsolete keys and remove from dom0.
    def mRemoveObsoleteSshKeysfromAuthKeysFile(self, aNode, aRemoteNodesList, aSshEnv=None):

        _ssh_env_setup = None

        if aSshEnv is not None:
            _ssh_env_setup = aSshEnv
        else:
            _ssh_env_setup = ebCluSshSetup(self.mGetCluControl())

        _ssh_keys_remove_config = self.mGetSshKeysRemoveConfig()

        if ( version_compare(self.mGetTargetVersion() , "23.1.0.0.0", ) >= 0 and
            PATCH_DOM0 in _ssh_keys_remove_config and
            'auth_keys_remove_patterns' in _ssh_keys_remove_config[PATCH_DOM0] ):

                self.mPatchLogInfo(f'Starting obsolete SSH keys check on host(s) {aRemoteNodesList}')
                _auth_keys_remove_patterns = _ssh_keys_remove_config[PATCH_DOM0]['auth_keys_remove_patterns']

                if _ssh_env_setup and _auth_keys_remove_patterns:
                    self.mPatchLogInfo(f'SSH key patterns to be removed: {_auth_keys_remove_patterns}')
                    _ssh_env_setup.mRemoveSshKeysAndFilesFromHosts(aNode,
                                                                   aRemoteNodesList,
                                                                   _auth_keys_remove_patterns)
    
    # Sets the common envrionment for all tasks in dom0
    def mSetEnvironment(self):

        # self.__dom0_patch_zip2_name: is of the format shown below
        # domains/exacloud/PatchPayloads/19.3.6.0.0.200317/Dom0YumRepository/exadata_ol7_19.3.6.0.0.200317_Linux-x86-64.zip,
        # domains/exacloud/PatchPayloads/19.3.6.0.0.200317/Dom0YumRepository/exadata_ovs_19.3.6.0.0.200317_Linux-x86-64.zip
        # if _target in [PATCH_ALL, PATCH_DOM0] and self.__dom0_local_patch_zip and self.__dom0_local_patch_zip2:
        if self.__dom0_local_patch_zip and self.__dom0_local_patch_zip2:
            # Select the appropriate zip file based on KVM (e.g exadata_ol7_19.3.6.0.0.200317_Linux-x86-64.zip ) or  OVM (e.g exadata_ovs_19.3.6.0.0.200317_Linux-x86-64.zip)
            dom0zip2File = self.__dom0_local_patch_zip2
            if dom0zip2File.find(',') > -1:
                patchFiles = dom0zip2File.strip().split(',')
                for _file in (patchFiles):
                    if self.mIsKvmEnv() and (any(substring in _file for substring in KVM_FILE_IDENTIFIER_LIST)):
                        self.mPatchLogInfo(f"Dom0Repository KVM file is {_file} ")
                        self.__dom0_local_patch_zip2 = _file
                        break
                    elif not self.mIsKvmEnv() and ((any(substring in _file for substring in KVM_FILE_IDENTIFIER_LIST)) == False):
                        self.mPatchLogInfo(f"Dom0Repository NON KVM file is {_file} ")
                        self.__dom0_local_patch_zip2 = _file
                        break

            # Set collect time stats flag
            self.mSetCollectTimeStatsFlag(self.mGetCollectTimeStatsParam(PATCH_DOM0))

            self.mPatchLogInfo(f"Dom0 local patch zip file name {self.__dom0_local_patch_zip}")
            self.mPatchLogInfo(f"Dom0 local patch zip-2 file name {self.__dom0_local_patch_zip2}")

            if not self.__dom0_local_patch_zip2:
                self.mPatchLogError("Dom0 Patch Zip file not found")
                raise Exception("Dom0 Patch Zip file not found")

            _no_action_taken = 0

            _ret = PATCH_SUCCESS_EXIT_CODE
            # Dom0 patching needs 2 zip files. first one has the patchmgr, second one is the actual patch
            self.__dom0_patch_zip_name = self.__dom0_local_patch_zip.split("/")[-1]
            self.__dom0_patch_zip2_name = self.__dom0_local_patch_zip2.split("/")[-1]
            # self.__dom0_patch_base = PATCH_BASE + self.__dom0_patch_zip_name + "_" + self.__dom0_patch_zip2_name + "/"
            self.__dom0_patch_base = self.__dom0_patch_base_dir + self.__dom0_patch_zip_name + "_" + self.__dom0_patch_zip2_name + "/"
            self.__dom0_patch_zip = self.__dom0_patch_base + self.__dom0_patch_zip_name
            self.__dom0_patch_base_after_unzip = (self.__dom0_patch_base +
                                                  mGetFirstDirInZip(self.__dom0_local_patch_zip))
            self.__dom0_patchmgr = self.__dom0_patch_base_after_unzip + "patchmgr"
            self.__dom0_patch_zip_size_mb = int(os.path.getsize(self.__dom0_local_patch_zip)) >> 20
            self.__dom0_patch_zip2_size_mb = int(os.path.getsize(self.__dom0_local_patch_zip2.strip())) >> 20
            self.__dom0_patch_necessary_space_mb = (
                        self.__dom0_patch_zip_size_mb + self.__dom0_patch_zip2_size_mb + int(self.mGetExadataPatchWorkingSpaceMB()))
            # Set current patch. Information necessary to update status in db
            self.mSetCurrentTargetType(PATCH_DOM0)

            _ret, _launchNodes = self.mSetLaunchNodeToPatchOtherDom0Nodes()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                return _ret
            try:
                self.__dom0_to_patch_dom0s = _launchNodes[0]
                self.mSetDom0ToPatchInitialDom0(_launchNodes[1])
            except IndexError:
                pass

            self.mSetPatchmgrLogPathOnLaunchNode(
                self.__dom0_patch_base_after_unzip + "patchmgr_log_" + self.mGetMasterReqId())
            self.mPatchLogInfo(f"Patch manager Log Path on Launch Node is {self.mGetPatchmgrLogPathOnLaunchNode()}")

            # def mPatchDom0sOrDomus(self, aTargetType, aTaskType):
            # List of launch nodes to update patch state metadata
            _launch_nodes = []

            '''
            # Set target version based on the patch tar file version name.
            Quarterly:
                ./PatchPayloads/19.3.2.0.0.191119/Dom0YumRepository/exadata_ovs_19.3.2.0.0.191119_Linux-x86-64.zip
            Monthly:
                ./PatchPayloads/201015/ExaspliceRepository/exadata_exasplice_update_201015_Linux-x86-64.zip
            '''
            if "ExaspliceRepository" in self.mGetDom0LocalPatchZip2():
                self.mSetTargetVersion(self.mGetDom0LocalPatchZip2().split("/")[-1].split("_")[3])
            else: 
                self.mSetTargetVersion(self.mGetDom0LocalPatchZip2().split("/")[-1].split("_")[2])

            # Add to executed targets
            self.mGetExecutedTargets().append(PATCH_DOM0)

            # Update status
            self.mUpdatePatchStatus(True, STEP_PREP_ENV)

            '''
             In this case, for _nodes_to_patch_except_initial All nodes from
             xml need to be considered as passwdless ssh is required to be setup 
             on all nodes and are used during ssh validation, patchmgr existence 
             check and for performing a few config changes during CNS monitor start.
            '''
            _nodes_to_patch_except_initial = list(set(self.mGetCustomizedDom0List()) - set([self.__dom0_to_patch_dom0s]))
            _initial_node_list = [self.__dom0_to_patch_dom0s]
            _initial_node = self.__dom0_to_patch_dom0s
            _next_node = self.mGetDom0ToPatchInitialDom0()
            _launch_nodes = [self.__dom0_to_patch_dom0s, _next_node]

            # These variables are defined , but files are created during operation only
            self.mSetPatchStatesBaseDir(os.path.join(self.__dom0_patch_base_after_unzip, "patch_states_data"))
            self.mSetMetadataJsonFile(os.path.join(self.mGetPatchStatesBaseDir(),
                                                   self.mGetMasterReqId() + "_patch_progress_report.json"))
            self.mPatchLogInfo(f"Patch metadata file = {self.mGetMetadataJsonFile()}")

            # Exacloud Plugin already initialized at this stage
            if self.mIsExacloudPluginEnabled():
                self.mGetPluginHandler().mSetPluginsLogPathOnLaunchNode(
                    self.__dom0_patch_base_after_unzip + "plugins_log_" + self.mGetMasterReqId())
                self.mPatchLogInfo("Exacloud Plugin Enabled to run")
            
            if self.mIsMockEnv():
                # in mock setup, skip rack specific operations
                return _ret

            # Rotate SSH Keys
            _all_nodes = _initial_node_list + _nodes_to_patch_except_initial
            _exakmsEndpoint = ExaKmsEndpoint(None)
            for _node in _all_nodes:
                if _node:
                    _exakmsEndpoint.mSingleRotateKey(_node)

            # In case of single launch node, _next_node will be None, because only one launch node
            # has been passed
            # set ssh keys from node patchers to the nodes they will be patching
            _ssh_env_setup = ebCluSshSetup(self.mGetCluControl())
            _ssh_env_setup.mSetSSHPasswordlessForInfraPatching(_initial_node, _nodes_to_patch_except_initial)

            # Remove Obsolete ssh keys emrtires from authorised_keys file
            self.mRemoveObsoleteSshKeysfromAuthKeysFile(_initial_node,
                                                        _nodes_to_patch_except_initial,
                                                        _ssh_env_setup)
                  

            # Store these in memory for clearing after each operation

            _src_node_list = [_initial_node]
            _remote_node_list = [_nodes_to_patch_except_initial]
            #
            # Configure ssh only if the second launch node is being selected or passed
            #
            if _next_node:
                _ssh_env_setup.mSetSSHPasswordlessForInfraPatching(_next_node, _initial_node_list)
                self.mRemoveObsoleteSshKeysfromAuthKeysFile(_next_node,
                                                            _initial_node_list,
                                                            _ssh_env_setup)
                _src_node_list.append(_next_node)
                _remote_node_list.append(_initial_node_list)
            _sshEnvDict = {
                "sshEnv": _ssh_env_setup,
                "fromHost": _src_node_list,
                "remoteHostLists": _remote_node_list
            }
            self.mSetSSHEnvSetUp(_sshEnvDict)

            # Fetch user specified exadata env type (like, ecs (is default), adw, atp, fa, higgs, etc).
            if self.mGetAdditionalOptions() and 'EnvType' in self.mGetAdditionalOptions()[0]:
                self.mSetExadataEnvType(self.mGetAdditionalOptions()[0]['EnvType'].lower())

        self.mPatchLogInfo("Finished Setting up Environment for Dom0")
        return _ret

    def mCheckIdemPotency(self, aDiscarded):

        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0
        _launch_nodes = [self.__dom0_to_patch_dom0s]
        _patchMgrObj = None
        if self.mGetDom0ToPatchInitialDom0():
            _launch_nodes.append(self.mGetDom0ToPatchInitialDom0())
        try:
            if not self.mIsMockEnv() and not self.mPatchRequestRetried():
                self.mCreateDirOnNodes(_launch_nodes, self.mGetPatchStatesBaseDir())
                mWritePatchInitialStatesToLaunchNodes(PATCH_DOM0, self.mGetCustomizedDom0List(),
                                                      _launch_nodes, self.mGetMetadataJsonFile())
        except Exception as e:
            self.mPatchLogWarn(f"Create Dir Error {str(e)} ")
            self.mPatchLogTrace(traceback.format_exc())

        # create a local patchmgr object with bare minimum arguments to make sure the _patchMgrObj attributes are local for this check only
        _patchMgrObj = InfraPatchManager(aTarget=PATCH_DOM0, aOperation=self.mGetTask(), aPatchBaseAfterUnzip=self.__dom0_patch_base_after_unzip,
                                   aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

        # check if any patchmgr session running arround in the patch retry and
        # if so, let's wait for it.
        if self.mPatchRequestRetried():
            _p_ses_exist = PATCH_SUCCESS_EXIT_CODE
            _p_active_node = None
            # Skip patchmgr existence check during clusterless patching.
            if self.mPerformPatchmgrExistenceCheck():
                # check for patchmgr session existence
                _patchMgrObj.mSetLaunchNode(aLaunchNode=None)
                _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=self.mGetCustomizedDom0List())

                _p_ses_exist, _p_active_node = _patchMgrObj.mCheckForPatchMgrSessionExistence()

                # Wait for patchmgr to complete
                if _p_ses_exist == PATCHMGR_SESSION_ALREADY_EXIST:
                    # reset the node list to make sure patchmgr cmd execution 
                    # only looked at the launch node
                    _patchMgrObj.mSetLaunchNode(aLaunchNode=_p_active_node)
                    _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=None)

                    _patchMgrObj.mWaitForPatchMgrCmdExecutionToComplete()

                    self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")
                    
                    _ret = _patchMgrObj.mGetStatusCode()
                    if _ret == PATCH_SUCCESS_EXIT_CODE:
                        self.mPatchLogInfo("Patch manager session found and completed successfully in patch retry")
                    else:
                        _suggestion_msg = f"Patch manager failed during patch retry on Dom0 : {_ret}. Exit code = {_p_active_node}"
                        _ret = PATCHMGR_RETRY_EXECUTION_FAILED_ERROR
                        self.mAddError(_ret, _suggestion_msg)
                        return _ret, _no_action_taken

        if self.mGetTask() not in [TASK_ROLLBACK, TASK_PATCH]:
            return _ret, _no_action_taken

        # Below checks for idempotency are done only for patch ot rollback operations
        if self.mGetTask() == TASK_ROLLBACK:
            _taskType = TASK_ROLLBACK
        else:
            _taskType = TASK_PATCH

        # Run post plugins if needed on already completed nodes
        if len(aDiscarded) > 0:
            self.mPatchLogInfo("Run patch manager and plugins for already upgraded nodes if required")
            # If new patch req, then mark completed for upgraded nodes.
            if not self.mPatchRequestRetried():
                self.mPatchLogInfo("Set completed for already upgraded nodes")
                for _n in aDiscarded:
                    mUpdateAllPatchStatesForNode(_launch_nodes, _n, self.mGetMetadataJsonFile(), PATCH_COMPLETED)
            elif self.mPatchRequestRetried():
                # Verify last attempted patchmgr and resume if required.
                for _n in aDiscarded:
                    _read_patch_state = mGetPatchStatesForNode(_launch_nodes, self.mGetMetadataJsonFile(), _n,
                                                               PATCH_MGR)
                    if _read_patch_state == PATCH_RUNNING:
                        _active_launch_node = mGetLaunchNodeForTargetType(_launch_nodes,
                                                                          self.mGetMetadataJsonFile(),
                                                                          PATCH_DOM0)
                        self.mPatchLogInfo(
                            f"Launch node where last patchmgr was run = {_active_launch_node} and log path = {self.mGetPatchmgrLogPathOnLaunchNode()}")

                        """
                        Here PatchmgrConsole.out file presence checked in two directories
                        1.  patchmgr_log_path_on_launch_node
                        2.  patchmgr_log_path_on_launch_node_launch_node_name(At the end of patching patchmgr log directory gets renamed by appending launch_node_name
                        It has to be in one of the directory because before patch retry, patch state was PATCH_RUNNING
                        
                        """
                        _patchmgr_log_directory_to_check = self.mGetPatchmgrLogPathOnLaunchNode()
                        _patchmgr_console_file_before_patchmgr_completion_found = False
                        _patchmgr_console_file_after_patchmgr_completion_found = False

                        # Check for the PatchmgrConsole.out presence in patchmgr_log_before_completion
                        # ( /EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_22.1.10.0.0.230422_Linux-x86-64.zip/dbserver_patch_221130/patchmgr_log_b75f885d-74c0-4979-8219-506d909aff6a)
                        _patchmgr_console_file_before_patchmgr_completion = _patchMgrObj.mGetPatchMgrConsoleOutputFile()
                        _patchmgr_console_file_before_patchmgr_completion_found, _ = self.mCheckFileExistsOnRemoteNodes([_active_launch_node], _patchmgr_console_file_before_patchmgr_completion)

                        if _patchmgr_console_file_before_patchmgr_completion_found:
                            _patchmgr_log_directory_to_check = self.mGetPatchmgrLogPathOnLaunchNode()
                        else:
                            # Check for PatchmgrConsole.out presence in patcmgr_log_after_completion
                            # ( /EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_22.1.10.0.0.230422_Linux-x86-64.zip/dbserver_patch_221130/patchmgr_log_b75f885d-74c0-4979-8219-506d909aff6a_slcs27dv0405m)
                            if _active_launch_node:
                                _patchmgr_console_file_after_patchmgr_completion = f"{self.mGetPatchmgrLogPathOnLaunchNode()}_{_active_launch_node.split('.')[0]}/{'PatchmgrConsole.out'}"
                                _patchmgr_console_file_after_patchmgr_completion_found, _ = self.mCheckFileExistsOnRemoteNodes([_active_launch_node], _patchmgr_console_file_after_patchmgr_completion)
                                if _patchmgr_console_file_after_patchmgr_completion_found:
                                    _patchmgr_log_directory_to_check = f"{self.mGetPatchmgrLogPathOnLaunchNode()}_{_active_launch_node.split('.')[0]}"

                        # If PatchmgrConsole.out does not exists in either of the patch log directories, marking the state as completed since the node is already upgraded
                        # This scenario might not occur at all
                        if not _patchmgr_console_file_before_patchmgr_completion_found and not _patchmgr_console_file_after_patchmgr_completion_found:
                            self.mPatchLogInfo(
                                f"Updating PATCH_MGR patchmetadata as completed for the node {_n} during CheckIdemPotency as node is up to date")
                            mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _n,
                                                 self.mGetMetadataJsonFile(), PATCH_MGR, PATCH_COMPLETED,aLaunchNode=_active_launch_node)
                        else:
                            # reset the node list to make sure patchmgr cmd execution 
                            # only looked at the launch node
                            _patchMgrObj.mSetLaunchNode(aLaunchNode=_active_launch_node)
                            _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=None)
                            _patchMgrObj.mSetLogPathOnLaunchNode(aLogPathOnLaunchNode=_patchmgr_log_directory_to_check)

                            _patchMgrObj.mWaitForPatchMgrCmdExecutionToComplete()

                            self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")
                    
                            _ret = _patchMgrObj.mGetStatusCode()
                            if _ret == PATCH_SUCCESS_EXIT_CODE:
                                self.mPatchLogInfo("Patch manager success during patch retry")
                                mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _n,
                                                     self.mGetMetadataJsonFile(), PATCH_MGR, PATCH_COMPLETED)
                            else:
                                mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _n,
                                                     self.mGetMetadataJsonFile(), PATCH_MGR, PATCH_FAILED)
                                _suggestion_msg = f"Patch manager failed during patch retry. Exit code = {_ret} on {_n}"
                                ret = PATCHMGR_RETRY_EXECUTION_FAILED_ERROR
                                self.mAddError(ret, _suggestion_msg)
                                return ret, _no_action_taken

                # Verify last attempted post plugins and resume if required.
                _read_patch_state = ""
                if self.mIsExacloudPluginEnabled():
                    self.mPatchLogInfo(f"ExaCloud Plugin Enabled . Launch nodes = {_launch_nodes}")
                    for _n in aDiscarded:
                        self.mPatchLogInfo(f"Getting post patch status on node {_n}.")
                        try:
                            _read_patch_state = ""
                            _read_patch_state = mGetPatchStatesForNode(_launch_nodes, self.mGetMetadataJsonFile(),
                                                                       _n, POST_PATCH)
                            self.mPatchLogInfo(f"Post plugin patch status: {_read_patch_state}")
                        except Exception as e:
                            self.mPatchLogWarn(f'Failed to get the post patch state : {str(e)}')
                            self.mPatchLogTrace(traceback.format_exc())

                        if not _read_patch_state:
                            _suggestion_msg = f"Invalid patch state found during patch = {_read_patch_state} on Dom0 : {_n}"
                            ret = POSTCHECKS_FAILED
                            self.mAddError(ret, _suggestion_msg) 
                            return ret, _no_action_taken

                        if _read_patch_state in [PATCH_PENDING, PATCH_RUNNING]:

                            # Run plugin metadata based exacloud plugins after patchmgr cmd
                            if self.mGetTask() in [ TASK_PATCH ] and not self.mIsExaSplice() and len(self.mGetPluginMetadata()) > 0:
                                _plugin_metadata_based_exacloud_plugin_enabled, _ = checkPluginEnabledFromInfraPatchMetadata(self.mGetPluginMetadata())
                                if _plugin_metadata_based_exacloud_plugin_enabled:
                                    # Execute plugin metadata based exacloud plugins
                                    self.mPatchLogInfo(
                                        f"Executing Exacloud Plugins implicitly based on the infra patch plugin metadata during PostPatch stage and as part of {self.mGetOpStyle()} patching retry.")
                                    _rc = self.mGetPluginHandler().mExacloudPluginMetadataExecutor([_n], "post")
                                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                                        return _rc

                            _rollback_operation = False
                            if _taskType == TASK_ROLLBACK:
                                _rollback_operation = True
                            _ret = self.mGetPluginHandler().mApply(_n, PATCH_DOM0, POST_PATCH,
                                                                   aRollback=_rollback_operation)
                            if _ret != PATCH_SUCCESS_EXIT_CODE:
                                mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _n,
                                                     self.mGetMetadataJsonFile(), POST_PATCH, PATCH_FAILED)
                                _suggestion_msg = f"Exacloud plugin failed on an upgraded node during retry : {_n}"
                                # do not overwrite error coming from plugin mApply
                                _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
                                if _child_request_error_already_exists_in_db:
                                    self.mPatchLogError(_suggestion_msg)
                                else:
                                    _ret = DOM0_POST_EXACLOUD_PLUGINS_FAILED
                                    self.mAddError(_ret, _suggestion_msg)
                                return _ret, _no_action_taken

                            mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _n,
                                                 self.mGetMetadataJsonFile(), POST_PATCH, PATCH_COMPLETED)

        self.mPatchLogInfo("Finished Check for IdemPotency in Patch Manager session")
        return _ret, _no_action_taken

    def mSetLaunchNodeToPatchOtherDom0Nodes(self):
        """
        Selects and sets 2 bases for dom0 or domU patching.
        use one to patch all other dom0s or domUs
        and the other to patch initial dom0 or domU
        """

        _launch_node_initial_candidates = []
        self.mPatchLogInfo("Set Launch Node for Dom0 to patch other nodes.")
        _external_launch_nodes = self.mGetExternalLaunchNode()
        if len(_external_launch_nodes) > 0:
            self.mPatchLogInfo(f"Getting  external Launch Nodes for patching {str(_external_launch_nodes)}")
            for _launch_node in _external_launch_nodes:
                if _launch_node in self.mGetCustomizedDom0List():
                    _exit_code = LAUNCH_NODE_PASSED_FOR_PATCH_OPERATION_SHOULD_NOT_BE_TARGET
                    _suggestion_msg = f"Launch node {_launch_node} passed should not be part of the list of the nodes to be patched. "
                    self.mAddError(_exit_code, _suggestion_msg)
                    self.mPatchLogError(_suggestion_msg)
                    return LAUNCH_NODE_PASSED_FOR_PATCH_OPERATION_SHOULD_NOT_BE_TARGET, _external_launch_nodes

                if _launch_node in self.mGetCustomizedCellList():
                    _exit_code = LAUNCH_NODE_PASSED_FOR_PATCH_OPERATION_SHOULD_NOT_BE_CELL
                    _suggestion_msg = f"Launch node {_launch_node} passed cannot be a cell node. "
                    self.mAddError(_exit_code, _suggestion_msg)
                    self.mPatchLogError(_suggestion_msg)
                    return LAUNCH_NODE_PASSED_FOR_PATCH_OPERATION_SHOULD_NOT_BE_CELL, _external_launch_nodes
                _launch_node_initial_candidates.append(_launch_node)
        elif len(_external_launch_nodes) == 0 \
                and self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsExternalLaunchNodePassed'):
            _exit_code = UNABLE_TO_PING_CONNECT_TO_EXTERNAL_LAUNCH_NODE 
            _suggestion_msg = "Launch nodes passed are not valid since they are not pingable or not connectible"
            self.mAddError(_exit_code, _suggestion_msg)
            self.mPatchLogError(_suggestion_msg)
            return UNABLE_TO_PING_CONNECT_TO_EXTERNAL_LAUNCH_NODE, _external_launch_nodes
        elif len(self.mGetIncludeNodeList()) > 0:
            self.mPatchLogInfo("Getting  Launch Nodes for Patching IncludeNodeList.")
            for _dom0 in self.mGetComputeNodeListFromPayload():
                _launch_node_initial_candidates.append(_dom0)
        else:
            # Launch Nodes are fetched in order of customerHostname or db server alias for MVM
            self.mPatchLogInfo("Getting  Launch Nodes for Patching.")

            """
            To get the launchnode candidates,first use mGetComputeNodeListSortedByAlias.
            If this list is empty use mGetComputeNodeListFromPayload.
           
            For infrapatching, dom0 launchnodes should not be fetched from dom0domudetails of
            ECRA payload, since this creates issues during single node vm cluster      
            """
            _compute_node_list = self.mGetComputeNodeListSortedByAlias()

            if _compute_node_list and len(_compute_node_list) > 0:
                self.mPatchLogInfo(
                    f"Launch Node candidates are fetched from ComputeNodeListSortedByAlias from ECRA payload : {json.dumps(_compute_node_list, indent=4)}.")
            else:
                _compute_node_list = self.mGetComputeNodeListFromPayload()
                self.mPatchLogInfo(
                    f"Launch Node candidates are fetched from ComputeNodeListFromPayload from ECRA payload {json.dumps(_compute_node_list, indent=4)}.")

            for _dom0 in _compute_node_list:
                _launch_node_initial_candidates.append(_dom0)

        if _launch_node_initial_candidates:
            self.mPatchLogInfo(
                f"Launch Node Initial candidates from mSetLaunchNodeToPatchOtherDom0Nodes is {str(_launch_node_initial_candidates)} ")

        _local_patch_zip = self.__dom0_local_patch_zip
        _patch_zip_name = self.__dom0_patch_zip_name
        _patch_zip_size_mb = self.__dom0_patch_zip_size_mb
        _patch_base = self.__dom0_patch_base
        _patch_zip = self.__dom0_patch_zip
        _patchmgr = self.__dom0_patchmgr
        _patch_necessary_space_mb = self.__dom0_patch_necessary_space_mb
        _local_patch_zip2 = self.__dom0_local_patch_zip2
        _patch_base_after_unzip = self.__dom0_patch_base_after_unzip
        if len(_external_launch_nodes) > 0:
            _launch_node_candidates = _external_launch_nodes
        else:
            _launch_node_candidates = self.mGetListOfLaunchNodeCandidates(list(_launch_node_initial_candidates))

        _selected_launch_nodes = []
        _errmsg_template = "Unable to set a %s to act as a patch manager for "
        _msgs = ["other %s",  # msg for lauch node to patch other nodes
                 "the initial %s patcher"]  # msg for launch_node to patch initial launch node

        '''
         First condition takes care of a quarter rack and Single node upgrade combination.
         The second condition means that for a cluster where
         external launch nodes are not specified, there should be at least two launch
         nodes taken from the cluster
        '''
        _insufficient_launch_node = False
        self.mPatchLogInfo(f"Launch node candidates: {str(_launch_node_candidates)}")
        if (len(self.mGetIncludeNodeList()) >= 1 and len(_launch_node_candidates) < 1) or \
            (len(self.mGetExternalLaunchNode()) == 0 and len(_launch_node_candidates) < 2):
                _insufficient_launch_node = True

        if _insufficient_launch_node == True:
            _exit_code = INSUFFICIENT_LAUNCH_NODES_AVAILABLE_TO_PATCH
            _suggestion_msg = "Insufficient launch node(s) found on the environment to patch. There must be atlest one launch node apart from the target node for patching to operate."
            self.mAddError(_exit_code, _suggestion_msg)
            self.mPatchLogError(_suggestion_msg)
            return _exit_code, _launch_node_candidates

        # loop twice since we need to set 2 dom[0U]s as dom[0U] patchers

        for _msg in _msgs:
            if len(_launch_node_candidates) > 0:
                _selected_launch_node = self.mSetLaunchNodeAsPatchBase(
                    aLaunchNodeCandidates=_launch_node_candidates,
                    aLocalPatchZipFile=_local_patch_zip,
                    aPatchZipName=_patch_zip_name,
                    aPatchZipSizeMb=_patch_zip_size_mb,
                    aRemotePatchBase=_patch_base,
                    aRemotePatchZipFile=_patch_zip,
                    aRemotePatchmgr=_patchmgr,
                    aRemoteNecessarySpaceMb=_patch_necessary_space_mb,
                    aPatchBaseDir=self.__dom0_patch_base_dir,
                    aSuccessMsg=(_msg % (PATCH_DOM0.upper())),
                    aMoreFilesToCopy=[(_local_patch_zip2,
                                       _patch_base_after_unzip)])

                if not _selected_launch_node:
                    _errmsg = ((_errmsg_template % (_selected_launch_node))
                               + (_msg % (PATCH_DOM0)))
                    self.mPatchLogError(_errmsg)
                    return PATCH_OPERATION_FAILED, _selected_launch_nodes
                else:
                    for _launch_node in _launch_node_candidates:
                        if (_launch_node in self.mGetJsonStatus() and
                                'error-1000' in _launch_node):
                            del self.mGetJsonStatus()[_launch_node]['error-1000']

                _selected_launch_nodes.append(_selected_launch_node)
                _launch_node_candidates.remove(_selected_launch_node)

        self.mPatchLogInfo(f"Selected launch nodes {str(_selected_launch_nodes)}")
        return PATCH_SUCCESS_EXIT_CODE, _selected_launch_nodes

    def mCustomCheck(self, aNodes=None, aTaskType=TASK_POSTCHECK):
        """
         This method performs a post checks independently on
         all of the Exadata targets like Dom0, DomU,IbSwitches
         and cells.

         Return value :
          0 -> if post check is success
          1 -> if post check fails
          Otherwise, pre-defined non zero error code
        """

        _post_patch_failed_nodes = []
        _node_prepatch_version = {}
        _err_msg_template = "%s !%s failed. Errors printed to screen and logs"
        _ret_code = PATCH_SUCCESS_EXIT_CODE

        if self.mIsMockEnv():
            # in mock setup, skip rack specific operations
            return _ret_code        

        '''
         Dom0 Independent Postchecks.
         aPrePatchVersion and aPostPatchTargetVersion are the image versions 
         before and after patches respectively. They do not have any 
         significance in case of running an independent post check, but they
         are only passed as they are mandatory arguments.
        '''

        _domU_listed_by_xm_list = []
        for _dom0_to_patch in aNodes:
            _node_prepatch_version[_dom0_to_patch] = self.mGetCluPatchCheck().mCheckTargetVersion(_dom0_to_patch,
                                                                                                  PATCH_DOM0,
                                                                                                  aIsexasplice= self.mIsExaSplice())
            _domU_listed_by_xm_list = self.mGetCluPatchCheck().mCheckVMsUp(_dom0_to_patch)
            self.mPatchLogInfo(f"Dom0 : {_dom0_to_patch} contains DomU : {_domU_listed_by_xm_list}")
            # aRollback is set to False as this is not a rollback operation.
            # But in case of postcheck we dont know what task was performed.
            # Hence version check will be skipped.

            _ret_code = self.mPostDom0PatchCheck(aDom0=_dom0_to_patch,
                                            aDomUList=_domU_listed_by_xm_list,
                                            aPrePatchVersion=_node_prepatch_version[_dom0_to_patch],
                                            aPostPatchTargetVersion=self.mGetTargetVersion(),
                                            aRollback=False,
                                            aTaskType=aTaskType,
                                            aIsDiscardedNodeListCheck = True)

            if _ret_code != PATCH_SUCCESS_EXIT_CODE:    
                _post_patch_failed_nodes.append(_dom0_to_patch)
                self.mPatchLogError(_err_msg_template % (PATCH_DOM0.upper(), "upgrade postchecks"))
                return _ret_code

        return _ret_code

    def mStartIptablesService(self, aDom0):
        """
        This method is going to copy dom0_iptables_setup.sh to dom0 if it does not exists and also executes
        dom0_iptables_setup.sh on the dom0 node

        return True upon executing the script otherwise False
        """
        '''
         This check can be skipped in case of
          - exasplice patching
          - clusterless upgrade
          - Patch percheck operation
          - EXACC environment
        '''
        _ret = PATCH_SUCCESS_EXIT_CODE
        if not self.mGetInfrapatchExecutionValidator().mCheckCondition('checkStartIptablesService'):
            return _ret

        _dom0 = exaBoxNode(get_gcontext())
        try:
            # Script path variables
            _local_iptables_script = "{0}/{1}".format(get_gcontext().mGetBasePath(),EXACLOUD_IPTABLES_SETUP_SCRIPT)
            _remote_iptables_script = DOM0_IPTABLES_SETUP_SCRIPT
            _dom0.mConnect(aHost=aDom0)

            # Check if iptables script is present, copy it otherwise
            if not _dom0.mFileExists(_remote_iptables_script):
                self.mPatchLogInfo(
                    f"Copy dom0_iptables_setup.sh : Source file = {_local_iptables_script}, Destination file = {_remote_iptables_script} , Remote node ={aDom0} ")
                # Make sure directory /opt/exacloud/network/ exists
                _mkdir_cmd = f"/bin/mkdir -p {os.path.dirname(_remote_iptables_script)} "
                _dom0.mExecuteCmdLog(_mkdir_cmd)
                if os.path.exists(_local_iptables_script):
                    _dom0.mCopyFile(_local_iptables_script, _remote_iptables_script)

            # Execute script to start iptables service and restore dynamic rules
            self.mPatchLogInfo(f"Running 'dom0_iptables_setup' script on {aDom0}")
            _exec_cmd = f"/bin/sh {_remote_iptables_script} "
            _dom0.mExecuteCmdLog(_exec_cmd)

        except Exception as e:
            self.mPatchLogError(f"Exception {str(e)} occurred while executing iptables setup script")
            _ret = DOM0_EXECUTE_IPTABLES_SETUP_SCRIPT_FAILED
            _suggestion_msg = f"Error occurred when executing iptables_setup script on {aDom0}."
            self.mAddError(_ret, _suggestion_msg)
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            if _dom0.mIsConnected():
                _dom0.mDisconnect()

        return _ret

    def mPostDom0PatchCheck(self, aDom0, aDomUList,
                            aPrePatchVersion, aPostPatchTargetVersion,
                            aRollback, aTaskType=None, aIsDiscardedNodeListCheck=False): 
        """
        Returns PATCH_SUCCESS_EXIT_CODE if all checks pass, otherwise error code specific to failure of the postcheck.
        checks currently done:
        *ping/ssh into the dom0
        *verify the image is listed as sucess
        *verify new version is what we expected for upgrade or rollback
        *check that all domUs are up
        *execute dom0_iptables_setup.sh
        *check db services up on dom0
        *check that db has started on domUs (currently just a sleep)
        *Startup VMs in case they are down on the discarded dom0 nodes for non-rolling patching.
        *check VIF-BRIDGE symlinks creation
        Note:
            Please make sure to execute any domu related postchecks that require network connectivity to domu after
            executing dom0_iptables_setup.sh
        """

        self.mPatchLogInfo(f"Starting post patch checks for {aDom0}")

        '''
         Check that we can ping and ssh into dom0
         Check that all the domU that were up before patching have come up
        '''
        _check_dom0_up_for_secs = 0
        _check_domU_up_for_secs = 0
        ret = PATCH_SUCCESS_EXIT_CODE
        if not aIsDiscardedNodeListCheck:
            _timeout_for_dom0_domU_up = self.mGetTimeoutForDom0DomuStartupInSeconds()
        else:
            _timeout_for_dom0_domU_up = 10

        '''
         In case of a non-rolling dom0+cell patching, VMs are 
         shutdown prior to cell patching. Once the cell patching
         completes, dom0 patching is started. To validate CRS on the 
         VMs running on the Dom0s, running VM list needs to be fetched 
         again after dom0 patching (VM should come up automatically 
         after dom0 patching is completed). In this case,
         since VMs were already shutdown prior to cell patching
         DomU list during Dom0 patching will be empty and heartbeat
         validations are skipped as a result. The below snippet
         of code fetches the list of VMs on the current Dom0 from Ecra 
         metadata and validates for presence of soft link. If there is 
         a soft link detected, it indicates, VMs are expected to be up 
         and running and heartbeat validations are performed on the previously 
         computed list of VMs else skipped.
        '''
        try:
            if self.mGetInfrapatchExecutionValidator().mCheckCondition('checkValidationsToPerformAutoStartupRequired', dom0sdomulist=aDomUList, discardedNodeListCheck=aIsDiscardedNodeListCheck):
                _domu_list_with_auto_startup_enabled = self.mListOfDomusWithAutoStartEnabled(aDom0)
                if len(_domu_list_with_auto_startup_enabled) > 0:
                    _domU_listed_by_xm_list = self.mGetCluPatchCheck().mCheckVMsUp(aDom0)
                    for _domu in _domu_list_with_auto_startup_enabled:
                        _domu = _domu.strip()
                        if _domu in _domU_listed_by_xm_list:
                            aDomUList.append(_domu)
                    if len(aDomUList) > 0:
                        self.mPatchLogInfo(
                            f"VMs up and running in Dom0 : {aDom0} after non-rolling {self.mGetTask()} are {str(aDomUList)}.")
                    else:
                        self.mPatchLogWarn(
                            f"No VMs up and running in Dom0 : {aDom0} after non-rolling {self.mGetTask()}.")
        except Exception as e:
            self.mPatchLogWarn(
                f"Unable to get DomU list during Dom0 non-rolling patching. Some of the Dom0 postcheck validations will be skipped. Error details : {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
                
        while _check_dom0_up_for_secs < _timeout_for_dom0_domU_up:
            if self.mGetCluPatchCheck().mPingNode(aDom0):
                break
            sleep(DOM0_DOMU_ONLINE_STATUS_CHECK_SLEEP_IN_SECONDS)
            _check_dom0_up_for_secs += DOM0_DOMU_ONLINE_STATUS_CHECK_SLEEP_IN_SECONDS
            self.mPatchLogInfo(f"**** Dom0 online check is polled for another {DOM0_DOMU_ONLINE_STATUS_CHECK_SLEEP_IN_SECONDS} seconds and re-validated.")
        else:
            ret = DOM0_NOT_PINGABLE
            _suggestion_msg = f"Dom0 : {aDom0} did not come back online (not ping-able or ssh-able) post patch"
            self.mAddError(ret, _suggestion_msg) 
            return ret

        # check that the image is seen as success
        if not self.mGetCluPatchCheck().mCheckImageSuccess(aDom0):
            ret = DOM0_IMAGE_NOT_SUCCESS
            _suggestion_msg = f"post-patch check on dom0 : {aDom0} image is not seen as success via imageinfo command"
            self.mAddError(ret, _suggestion_msg)
            return ret

        '''
         check if the environment is a fresh installation and 
         skip heartbeat related checks if True.
        '''
        if self.mIsExaSplice():
            self.mPatchLogInfo("Newly provisionsed environment check will be skipped in case of exasplice patching.")
        else:
            if self.mCheckFreshInstall(aDom0):
                ret = PATCH_SUCCESS_EXIT_CODE
                _suggestion_msg = f"Hearbeat checks cannot be performed on a newly provisoned clusters due to missing heartbeat enties : {aDom0}."
                self.mAddError(ret, _suggestion_msg)
                return ret

        '''
         Image version checks are not performed as during
         independent postcheck option as we are not aware 
         whether upgrade or rollback was performed.
        '''
        if aTaskType not in [TASK_POSTCHECK]:
            # Check that the dom0 is at the requested version. if it was a rollback we just
            # check for the version to be lower than what it previously was.
            _current_dom0_version = self.mGetCluPatchCheck().mCheckTargetVersion(aDom0, PATCH_DOM0,
                                                                                 aIsexasplice= self.mIsExaSplice())
            if aRollback:
                if self.mGetCluPatchCheck().mCheckTargetVersion(aDom0, PATCH_DOM0, aPrePatchVersion, aIsexasplice= self.mIsExaSplice()) >= 0:
                    ret = VERSION_MISMATCH_DURING_ROLLBACK
                    _suggestion_msg = f"Dom0 : {aDom0} rollback was requested but the version seems to be unchanged, found version {aPrePatchVersion}, expected to be lower than {_current_dom0_version}"
                    self.mAddError(ret, _suggestion_msg)
                    return ret
            elif self.mGetCluPatchCheck().mCheckTargetVersion(aDom0, PATCH_DOM0, aPostPatchTargetVersion, aIsexasplice= self.mIsExaSplice()) < 0:
                """
                We proceed with patching only if the target version is higher than the current version.
                In all other cases, when currentVersion = targetVersion or currentVersion > TargetVersion (as seen in
                elastic node addition case, a node with higher version can be added), the node is skipped.            
                After successful patch completion, node would be at target version.
                """
                ret = DOM0_NOT_AT_REQUESTED_VERSION
                _suggestion_msg = f"Dom0 : {aDom0} is not at the requested upgrade version {aPostPatchTargetVersion}, found version {_current_dom0_version}"
                self.mAddError(ret, _suggestion_msg)
                return ret

        if self.mIsExaSplice():
            # Check if any parallel vm_cmd operations are running during dom0 exasplice
            # if yes, log the operation details for easy debugging purpose
            try:
                _ongoing_vm_cmd_requests = mFilterRequestsForThisRack(ebGetDefaultDB(), self.mGetRackName(),
                                                                              "Pending", aCmd="cluctrl.vm_cmd",
                                                                              aRowsLimit=1)
                if _ongoing_vm_cmd_requests:
                    for r in _ongoing_vm_cmd_requests:
                        _op_uuid = r["uuid"]
                        _start_time = r["starttime"]
                        if _op_uuid and _start_time:
                            self.mPatchLogInfo(
                                f"Parallel exacloud operation is in progress on rack {self.mGetRackName()} with UUID {_op_uuid} and start time '{_start_time}' ")
            except:
                # Should be info , not error as this is just an informative message
                self.mPatchLogInfo("Not able to fetch any parallel exacloud operation during Dom0 monthly infrapatching")

        # Validate if Auto startup is enabled for the DomUs
        # which were previously up and running prior to Upgrade
        # and Rollback operations.
        # Skip these checks for dom0 exasplice since
        # reshape operations restarts domu and these checks fail
        if not self.mIsExaSplice():
            if len(aDomUList) > 0:
                ret = self.mGetCluPatchCheck().mValidateAndEnableDomuAutoStartup(aDom0,aDomUList)
                if ret != PATCH_SUCCESS_EXIT_CODE:
                    return ret

            # Check if DomUs are up.
            while _check_domU_up_for_secs < _timeout_for_dom0_domU_up:
                if self.mGetCluPatchCheck().mCheckVMsUp(aDom0, aDomUList):
                    break
                sleep(DOM0_DOMU_ONLINE_STATUS_CHECK_SLEEP_IN_SECONDS)
                _check_domU_up_for_secs += DOM0_DOMU_ONLINE_STATUS_CHECK_SLEEP_IN_SECONDS
                self.mPatchLogInfo(f"**** Dom0 online check is polled for another {DOM0_DOMU_ONLINE_STATUS_CHECK_SLEEP_IN_SECONDS} seconds and re-validated.")
            else:
                ret = DOMU_DOWN_ERROR
                _suggestion_msg = f"Expected all of the following domus {str(aDomUList)} to be up on {aDom0}, but only {str(self.mGetDomUList(aDom0, aFromXmList=True))} were up"
                self.mAddError(ret, _suggestion_msg)
                return ret
        else:
           self.mPatchLogInfo(
                "VM AutoStart Enabled Checks and VM Up related checks will not be performed during Dom0 monthly patching")

        # Start iptables service only in exacs envs
        # dom0_iptables_setup.sh is not present in a clusterless patching.
        # The provisioning flow has to execute dom0_iptables_setup.sh if it is not already executing it.
        ret = self.mStartIptablesService(aDom0)
        if ret != PATCH_SUCCESS_EXIT_CODE:
            return ret

        # check that db services are up
        if not self.mGetCluPatchCheck().mCheckDBServices(aDBNode=aDom0, aCheckRunning=True):
            ret = DB_SERVER_SERVICE_DOWN
            _suggestion_msg = f"dbserverd service was not up on dom0 {aDom0} "
            self.mAddError(ret, _suggestion_msg)
            return ret

        '''
         Check for VMs to be online and startup VMs
         in case they are down in case of already
         upgraded dom0 and non-rolling patching.
        '''
        if aIsDiscardedNodeListCheck and self.mGetOpStyle() == OP_STYLE_NON_ROLLING:
            ret = self.mStartupVMsIfAutoStartEnabled(aDom0)
            if ret != PATCH_SUCCESS_EXIT_CODE:
                return ret

        # Heartbeat validations in this case will be performed during regular patching.
        ret, _domu_heartbeat_failure_list, _domus_accessible_from_exacloud_node = self.mValidateDomUHeartbeat(aDomUList, aIsDiscardedNodeListCheck)
        if ret != PATCH_SUCCESS_EXIT_CODE and self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsRDSPingCheckEnabled'):
            # Heartbeat validation failed so check for rds_ping validation to determine network connectivity is causing Heartbeat failure
            _ret_rds_ping_validation = self.mValidateRDSPingOnDomuNodes(_domu_heartbeat_failure_list, _domus_accessible_from_exacloud_node)

            # When rds_ping succeeds return existing HB error
            if _ret_rds_ping_validation != PATCH_SUCCESS_EXIT_CODE:
                ret = _ret_rds_ping_validation
            return ret 
          

        """
        Execute DB healthchecks on the vms where crs auto start is enabled.        
        """
        if ret == PATCH_SUCCESS_EXIT_CODE:
            """
            self.__crs_autostart_enabled_vm_set has all the vms where crs auto start is enabled
            aDomUList contains vms running on current dom0
            So updating _crs_running_vm_list to have vm list of current dom0 on which crs auto start is enabled    
            """
            _crs_running_vm_list = []
            _crs_running_vm_list.extend(
                item for item in aDomUList if item in self.__crs_autostart_enabled_vm_set)

            ret = self.mDetectCDBDegradationDuringDom0Patching(aDom0, _crs_running_vm_list)
            if ret != PATCH_SUCCESS_EXIT_CODE:
                return ret

            ret = self.mDetectPDBDegradationDuringDom0Patching(aDom0, _crs_running_vm_list,
                                                               aIsRetry=self.mPatchRequestRetried())
            if ret != PATCH_SUCCESS_EXIT_CODE:
                return ret
 
        # Fedramp configuration check to restore fedramp configuration
        if self.mGetFedRamp() == 'ENABLED':
            self.mPatchLogInfo(
                f"Executing fedramp file restore operations as the value of Fedamp Enable is set to {self.mGetFedRamp()}")
            _Pre_Aud = "/etc/audit/audit.rules_FED"
            _Post_Aud = "/etc/audit/audit.rules"
            '''
             Fedramp related backup is performed and restored 
             only on the customized list.
            '''
            _aNodesList = self.mGetCustomizedDom0List()
            self.mFedrampDom0RestoreConfig(_aNodesList, _Pre_Aud, _Post_Aud)

        # Validate VIF bridge symlinks creation only for ExaCS / Xen env
        ret = self.mValidateVIFBridgeInDom0(aDom0, aDomUList)

        return ret

    def mListOfDomusWithAutoStartEnabled(self, aDom0):
        """
         This method gets the list of VMs for which auto startup
         is enabled for the current Dom0. Since soft link validations
         are performed prior to this and links are created if missing on Dom0.
         This method validates only for the rebot specific parameter on Xen and
         KVM VM config files. If the config file indicate auto startup is enabled
         for the VM under validation. It is added to the final list.

         return - empty list if auto startup is disabled for all VMs on the Dom0.
                - else list of DomUs where auto startup is enabled.
        """

        _list_of_vm_with_auto_startup_enabled = []
        _node = exaBoxNode(get_gcontext())
        try:
            _node.mConnect(aHost=aDom0)
            # mGetDom0DomUCustomerNameMapWithNoZeroVcpu contains customer hostname DomU List
            for _dom0, _domu_list in self.mGetDom0DomUCustomerNameMapWithNoZeroVcpu():

                if _dom0 == aDom0 and len(_domu_list) > 0:
                    for _domu_customer_hostname in _domu_list:
                        if self.mIsKvmEnv():
                            _auto_start_file = f"{KVM_AUTO_START_DIR}/{_domu_customer_hostname}.xml"
                        else:
                            _auto_start_file = f"{XEN_AUTO_START_DIR}/{_domu_customer_hostname}.cfg"

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
                        if _node.mFileExists(_auto_start_file):
                            _cmd = f"grep on_reboot {_auto_start_file} | grep -i 'restart'"
                            _node.mExecuteCmd(_cmd)
                            if int(_node.mGetCmdExitStatus()) == 0:
                                _list_of_vm_with_auto_startup_enabled.append(_domu_customer_hostname)
                        else:
                            self.mPatchLogInfo(f"Soft link details missing for VM : {_domu_customer_hostname}")

        except Exception as e:
            self.mPatchLogWarn(
                f'Unable to fetch DomU host details with auto startup settings enabled on {aDom0}. Error : {str(e)}')
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            if _node.mIsConnected():
                _node.mDisconnect()
            return _list_of_vm_with_auto_startup_enabled

    def mStartupVMsIfAutoStartEnabled(self, aDom0):
        """
         This method starts up VMs in case they are down
         post dom0 reboot.

         return:
            - PATCH_SUCCESS_EXIT_CODE in case of all VMs
              on the current Dom0 or were able to startup
              VMs successfully.

            - UNABLE_TO_STARTUP_VM in case of VMs down and
              unable to startup
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _domus_down_on_dom0 = []

        '''
         This check can be skipped in case of
         exasplice patching.
        '''
        if self.mIsExaSplice():
            self.mPatchLogInfo("Validation to perform auto startup of VMs post patching will be skipped in case of Exasplice patching.")
            return _ret

        try:
            '''
             Check for VMs to be up and running only if 
             there are VMs with auto startup settings 
             enabled.
            '''
            _domu_list_with_auto_startup_enabled = self.mListOfDomusWithAutoStartEnabled(aDom0)
            if len(_domu_list_with_auto_startup_enabled) > 0:
                _domU_listed_by_xm_list = self.mGetCluPatchCheck().mCheckVMsUp(aDom0)
                for _domu in _domu_list_with_auto_startup_enabled:
                    _domu = _domu.strip()
                    if _domu not in _domU_listed_by_xm_list:
                        _domus_down_on_dom0.append(_domu)
                    else:
                        self.mPatchLogInfo(f"DomU : {_domu} is up and running post Dom0 : {aDom0}'s reboot.")

            if len(_domus_down_on_dom0) > 0:
                _processes = ProcessManager()
                _rc_status = _processes.mGetManager().list()
                for _dom0 in [ aDom0 ]:
                    _p = ProcessStructure(self.mGetCluPatchCheck().mManageVMs, [aDom0, _domus_down_on_dom0, 'start', _rc_status], aDom0)
                    '''
                     Timeout parameter configurable in Infrapatching.conf
                     Currently it is set to 60 minutes
                    '''
                    _p.mSetMaxExecutionTime(self.mGetVmExecutionTimeoutInSeconds())
                    _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
                    _p.mSetLogTimeoutFx(self.mPatchLogWarn)
                    _processes.mStartAppend(_p)

                _processes.mJoinProcess()

                # Validate the return codes of vm start.
                _rc_all = True
                for _node_status in _rc_status:
                    if _node_status['status'] == 'failed':
                        _rc_all &= False
                        self.mPatchLogError(f"Startup of VM '{str(_node_status['domu'])}' was not successful.")
                    else:
                        self.mPatchLogInfo(
                            f"Startup of DomU : {str(_node_status['domu'])} on Dom0 : {aDom0} was successful.")

                if not _rc_all:
                    _suggestion_msg = f"Unable to startup VMs on Dom0 : {aDom0}"
                    _ret = UNABLE_TO_STARTUP_VM_ON_DOM0
                    self.mAddError(_ret, _suggestion_msg)

        except Exception as e:
            _suggestion_msg = f'Exception encountered while starting up VMs on Dom0 : {aDom0}. Error : {str(e)}'
            _ret = UNABLE_TO_STARTUP_VM_ON_DOM0
            self.mAddError(_ret, _suggestion_msg)
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            return _ret

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
        _heartbeat_timeout_in_seconds = self.mGetExadataPatchGridHeartBeatTimeoutSec()

        '''
         This validation is performed based on checkValidateHeartbeatRequired 
         returns True or False. Skipped during exasplice where checkValidateHeartbeatRequired  
         returns false
        '''
        if not self.mGetInfrapatchExecutionValidator().mCheckCondition('checkValidateHeartbeatRequired', isDiscardedNodeListCheck=aIsDiscardedNodeListCheck):
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
                _list_domus_Exascale_storage = self.mGetDomuListByClusterStorageType(EXASCALE_CLUSTER_STORAGE_TYPE)
                # for each domU, check if it has started clusterware heartbeat with all the cells
                for _domU_name in aDomUList:
                    # Heartbeat validations are performed using
                    # customer hostname.
                    _cust_hostname = _domU_name
                    _domU_name = (self.mGetDomUCustomerNameforDomuNatHostName(_domU_name)).strip()
                    # bug 26678535: heart beat message in the cell 'alert.log' only
                    # contains the DOMU hostnames without the FQDN. So strip off
                    # the FQDN from the DOMU hostname before doing anything.
                    _domu_hostname_no_fqdn = _domU_name.split('.')[0]

                    # host names are cut to 32 chars on the cell alert logs
                    _32_char_domU_name = _domu_hostname_no_fqdn[:32]

                    # if domU belongs to an exascale cluster based, check EDV info
                    if _cust_hostname in _list_domus_Exascale_storage:
                        _ret = self.mCheckEDVInfoForHB(_domu_hostname_no_fqdn, self.mGetCellList(),
                                                  _heartbeat_timeout_in_seconds)
                        if not _ret:
                            _failed_heartbeat_domu_list.append(_domU_name)
                            self.mPatchLogError(f'Heartbeat validation failed for DomU (on Exascale): {_domU_name}')
                        continue

                    # if domU belongs to an ASM cluster based
                    _cell_list_to_validate_for_crs = self.mGetCluPatchCheck().mVerifyCellsInUseByASM(
                        self.mGetCellList())
                    if _cell_list_to_validate_for_crs is None or len(_cell_list_to_validate_for_crs) < 1:
                        self.mPatchLogInfo(
                            "Cell List to validate CRS is empty. So no CRS validation will happen for Dom0 postcheck")
                    else:
                        self.mPatchLogInfo(
                            f"Cell List to validate CRS for Dom0 postcheck is {json.dumps(_cell_list_to_validate_for_crs, indent=4)} ")

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
                            _cell.mExecuteCmd(_cmd_get_heartbeat_alert_log_file)
                            _exit_status = _cell.mGetCmdExitStatus()
                            if int(_exit_status) != 0:
                                for _alert_log_extension_counter_value in range(0, 5):
                                    _cmd_get_heartbeat_alert_log_file_extension = f'grep -ai "Heartbeat with diskmon" {CELL_ALERT_LOG}.{_alert_log_extension_counter_value} | egrep -ai "started on|stopped on" | grep "{_32_char_domU_name}"'
                                    _cell.mExecuteCmd(_cmd_get_heartbeat_alert_log_file_extension)
                                    _exit_status_alert_log_file = _cell.mGetCmdExitStatus()
                                    if int(_exit_status_alert_log_file) == 0:
                                        _alert_log_file = _alert_log_file + "." + str(_alert_log_extension_counter_value)
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
                                _checked_for_secs += 10
                            else:
                                # Heartbeat check failed so for the next iteration combination of cell/domu,
                                # no need to wait until self.mGetExadataPatchGridHeartBeatTimeoutSec()
                                _heartbeat_timeout_in_seconds = 1
                                _failed_heartbeat_domu_list.append(_domU_name)
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
                    _failed_heartbeat_domu_list = self.mGetDomUNatHostNamesforDomuCustomerHostNames(_failed_heartbeat_domu_list)
                    _domus_accessible_from_exacloud_node, _domus_not_accessible_from_exacloud_node = self.mGetReachableDomuList(_failed_heartbeat_domu_list)

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
                    _ret, _list_of_vms_crs_auto_startup_enabled = self.mGetCluPatchCheck().mReturnListofVMsWithCRSAutoStartupEnabled(_domus_accessible_from_exacloud_node)
                    if _ret in [DOMU_INVALID_CRS_HOME, CRS_COMMAND_EXCEPTION_ENCOUNTERED]:
                        return _ret, _failed_heartbeat_domu_list, _domus_accessible_from_exacloud_node

                    '''
                     Perform CRS validations only on VMs where CRS
                     Auto startup is enabled. Validations are performed
                     using NAT hostnames.
                    '''
                    if len(_list_of_vms_crs_auto_startup_enabled) > 0:
                        _ret_crs_validate, _failed_crs_domu_list = self.mGetCluPatchCheck().mCheckAndStartupCRSDuringDom0Patching(_list_of_vms_crs_auto_startup_enabled)
                        if len(_failed_crs_domu_list) > 0:
                            for _domu_crs_down in _failed_crs_domu_list:
                                _failed_heartbeat_domu_list.append(_domu_crs_down)
                    else:
                        _set_of_vms_crs_auto_startup_enabled = set(_list_of_vms_crs_auto_startup_enabled)
                        _vms_where_crs_is_disabled = [_vm_list for _vm_list in _domus_accessible_from_exacloud_node if _vm_list not in _set_of_vms_crs_auto_startup_enabled]

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
                    _failed_heartbeat_domu_list_customer_nat_hostnames = self.mReturnBothDomUNATCustomerHostNames(_failed_heartbeat_domu_list)
                    ret = DOMU_HEARTBEAT_NOT_RECEIVED
                    _suggestion_msg = f"CRS did not startup even after timeout of {str(_heartbeat_timeout_in_seconds)} secs. CRS is down on the list : {str(_failed_heartbeat_domu_list_customer_nat_hostnames)}"
                    '''
                     CRS error details takes higher precendence than 
                     that of the heartbeat error details. 

                     _failed_heartbeat_domu_list contains failed VM list both based on 
                     CRS check as well as heartbeat validations.
                    '''
                    if len(_failed_crs_domu_list) > 0:
                        ret = _ret_crs_validate
                        _suggestion_msg = f"Unable to startup CRS on the DomU list : {str(_failed_heartbeat_domu_list_customer_nat_hostnames)}"
                    self.mAddError(ret, _suggestion_msg)

                if _cell.mIsConnected():
                    _cell.mDisconnect()

        return ret, _failed_heartbeat_domu_list, _domus_accessible_from_exacloud_node
                        
    def mCheckEDVInfoForHB(self, aDomuName, aCellList, aTimeoutInSec):
        '''
        This method is called in post patch. It will use the snapshot obtained prior
        to patching to compare with current output
        Collection phase: it stores the hostname, if up/down, and last EDV heartbeat.
        Comparison phase: when the node is rebooted, EDV, when it comes up in the node
        it will have to register in all cells. So the time has to be post last hb seen
        in the cell
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
            _cmd = f"{ESCLI_CMD} --wallet {ESCLI_WALLET_LOCATION} lsinitiator -l | grep ' {aDomuName} ' "
        else:
            _cmd = f"{ESCLI_CMD} --wallet {ESCLI_WALLET_LOCATION} lsinitiator -l | grep ' {aDomuName} ' |grep {_guid}"
        '''
        Output of lsinitiator
        [root@scaqar01celadm01 ~]# /opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet lsinitiator -l
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
                        if _reg_time <=  _init_reg_time:
                            self.mPatchLogInfo(f'Still waiting for stack on {aDomuName} to be up - registration time {str(_reg_time)}')
                        else:    
                            self.mPatchLogInfo(f'CRS stack on {aDomuName} is up - registration time {str(_reg_time)}')
                            _crs_is_up = True
                            break

                if _cell.mIsConnected():
                    _cell.mDisconnect()
                sleep(9)
                _checked_for_secs += 10

        if _cell.mIsConnected():
            _cell.mDisconnect()
        return _crs_is_up

    def mCollectEDVCellInfo(self, aDomUList):
        _rc = PATCH_SUCCESS_EXIT_CODE
        _domu_list_no_fqdn = []

        if len(aDomUList) == 0:
            self.mPatchLogInfo('DomU list is empty.')
            return _rc

        _list_domus_Exascale_storage = self.mGetDomuListByClusterStorageType(EXASCALE_CLUSTER_STORAGE_TYPE)

        for _domu in aDomUList:
            if _domu in _list_domus_Exascale_storage:
                _domu_list_no_fqdn.append( _domu.split('.')[0])
            else:
                self.mPatchLogInfo(f'Domu {_domu} not on exascale cluster')

        _idx_guid = 3
        _idx_hostname = 1
        _cell = exaBoxNode(get_gcontext())
        _cmd = f"{ESCLI_CMD} --wallet {ESCLI_WALLET_LOCATION} lsinitiator -l"
        '''
        [root@scaqar01celadm01 ~]# /opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet lsinitiator -l
        id                                   hostName       giClusterName   giClusterId                          version           lastHeartbeat             registerTime
        60b679ac-bafa-c910-60b6-79acbafac910 scaqar01dv0207 iad1376clu070a1 11a8f48a-da35-5f3c-ff7c-b37096bdf813 24.1.2.0.0.240711 2024-08-22T15:32:43-07:00 2024-08-06T05:26:09-07:00
        a0f6ad56-a639-c085-a0f6-ad56a639c085 scaqar01dv0107 iad1376clu070a1 11a8f48a-da35-5f3c-ff7c-b37096bdf813 24.1.2.0.0.240711 2024-08-22T15:32:43-07:00 2024-08-06T05:26:10-07:00

        If CRS stack is down, the line would be like:
        a0f6ad56-a639-c085-a0f6-ad56a639c085 scaqar01dv0107                                                      24.1.2.0.0.240711 2024-08-22T15:32:43-07:00 2024-08-06T05:26:10-07:00

        In case the node is down, because EDV will not be present, no line will be present in the output
        '''
        # info should be the same in all cells, but due to some connectivity issues, it coudl be behind, so connect to the majority
        # of cells. Not that some customers may have 50+ cells.
        _number_majority_cells = int(len(self.mGetCellList())/2) + 1
        _count_cell = 1
        _good_cells = 0
        _localDict = {}
        for _cellName in self.mGetCellList():
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
                       #a0f6ad56-a639-c085-a0f6-ad56a639c085 scaqar01dv0107 11a8f48a-da35-5f3c-ff7c-b37096bdf813 24.1.2.0.0.240711 2024-08-22T15:32:43-07:00 2024-08-06T05:26:10-07:00
                       # 5 columns, no info from EDV
                       #a0f6ad56-a639-c085-a0f6-ad56a639c085 24.1.2.0.0.240711 2024-08-22T15:32:43-07:00 2024-08-06T05:26:10-07:00

                       if len(_line) == 7:
                           _state = "up"
                           _hb_time = _line[-2]
                           _reg_time = _line[-1]
                           _guid = _line[_idx_guid]
                       elif len(_line) == 6:
                           # for the case where EDV hit this bug, providing either clusterId or clustername
                           # 0d72d0ef-2b28-b02c-0d72-d0ef2b28b02c scaqau05dv0207                 6ed854f2-0d12-4fcd-ffec-19496f550f6f 24.1.2.0.0.240727 
                           #2024-10-08T18:21:23+00:00 2024-10-08T16:09:04+00:00
                           _state = "up"
                           _hb_time = _line[-2]
                           _reg_time = _line[-1]
                           # note that we get either clustername or clusterid here, whatever is present
                           _guid = _line[_idx_guid-1]
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
                           _info_already_added =  _localDict[_hostname]
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
            self.__dom0_hb_info[_hostname] = [_localDict[_hostname][0], _localDict[_hostname][1], _localDict[_hostname][2]]
        self.mPatchLogInfo(f'HB info collected: {self.__dom0_hb_info}')


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

        if not self.mGetInfrapatchExecutionValidator().mCheckCondition('checkHeartbeatValidationPriorToPatchmgrRun'):
            self.mPatchLogInfo("Cluster wide CRS checks will be skipped.")
            return _ret
   
        self.mPatchLogInfo("\n ***Performing CRS checks on clusters. Checks are performed only in case of keys injected to DomUs during Dom0 patching.***\n")
        try:
            if not self.mIsMockEnv() and len(self.mGetClusterToVmMapWithNonZeroVcpu()) > 0 and self.mGetOpStyle() != OP_STYLE_NON_ROLLING:
                '''
                 Get domu details from Ecra metadata and perform
                 heartbeat validations for each cluster.
                '''
                for _clustername, _domu_list in self.mGetClusterToVmMapWithNonZeroVcpu():
                    _domu_crs_failure_list = []

                    '''
                     SSH connectivity between exacloud &
                     DomU to be performed using NAT Hostname.
                     Input _domu_list has customer Hostnames.
                    '''
                    _domu_list = self.mGetDomUNatHostNamesforDomuCustomerHostNames(_domu_list)

                    '''
                     In case of a quarter rack and CRS auto start is enabled
                     only on one of the VM, no heartbeat checks are performed.

                     Expectation is customer is aware that the CRS autostart is
                     disabled on one of the VMs in a given 2 VM list and the
                     downtime is expected.
                    '''
                    _domus_accessible_from_exacloud_node, _domus_not_accessible_from_exacloud_node = self.mGetReachableDomuList(_domu_list)
                    if len(_domus_accessible_from_exacloud_node) > 0:
                        _ret, _list_of_vms_crs_auto_startup_enabled = self.mGetCluPatchCheck().mReturnListofVMsWithCRSAutoStartupEnabled(_domus_accessible_from_exacloud_node)
                        if _ret == DOMU_INVALID_CRS_HOME:
                            break

                        self.mPatchLogInfo(
                            f"List of VMs where CRS auto startup is currently enabled : {json.dumps(_list_of_vms_crs_auto_startup_enabled, indent=4)}.")
                        if len(_list_of_vms_crs_auto_startup_enabled) < 2:
                            self.mPatchLogInfo("CRS auto startup must be enabled on atleast 2 VMs for the CRS validations to be performed.")
                            continue

                        '''
                         CRS is validated and started up in case of CRS services down on 
                         a given DomU and cluster. If we are unable to startup CRS even 
                         after 3 iterations, CRS validation and inturn infra patching operation 
                         is marked as failure.
                        '''
                        _, _domu_crs_failure_list = self.mGetCluPatchCheck().mCheckAndStartupCRSDuringDom0Patching(_list_of_vms_crs_auto_startup_enabled)
                        """
                        Updating self.__crs_autostart_enabled_vm_set to have vms where crs auto start is enabled and crs is running 
                        """
                        self.__crs_autostart_enabled_vm_set.update(
                            set(self.mGetDomUCustomerHostNamesforDomuNatHostNames(
                                _list_of_vms_crs_auto_startup_enabled)) - set(_domu_crs_failure_list))

                        if ((int(len(_list_of_vms_crs_auto_startup_enabled)) - int(len(_domu_crs_failure_list))) < 2):
                            _domu_crs_failure_list_with_nat_and_customer_hostname = self.mReturnBothDomUNATCustomerHostNames(_domu_crs_failure_list)
                            _suggestion_msg = f"CRS services were supposed to be running on at least 2 VMs.It is currently down on {str(_domu_crs_failure_list_with_nat_and_customer_hostname)} for the cluster : {str(_clustername)}."
                            if self.mGetTask() == TASK_PREREQ_CHECK:
                                self.mPatchLogWarn(f"{_suggestion_msg}")
                            else:
                                self.mPatchLogError(f"{_suggestion_msg}")
                            _clusters_with_crs_down_and_no_high_availability[_clustername] = _domu_crs_failure_list
                        elif len(_domu_crs_failure_list) > 0:
                            _domu_crs_failure_list_with_nat_and_customer_hostname = self.mReturnBothDomUNATCustomerHostNames(_domu_crs_failure_list)
                            self.mPatchLogInfo(
                                f"Although CRS is down on few VMs :{str(_domu_crs_failure_list_with_nat_and_customer_hostname)} belonging to the cluster : {str(_clustername)}, high availability is not impacted as CRS is running on at least 2 VMs.")
                    else:
                        _domus_not_accessible_from_exacloud_node_nat_customer_hostname = self.mReturnBothDomUNATCustomerHostNames(_domus_not_accessible_from_exacloud_node)
                        _suggestion_msg = f"CRS validations are skipped as one or more VMs are not accessible : {str(_domus_not_accessible_from_exacloud_node_nat_customer_hostname)}."
                        if self.mGetTask() == TASK_PREREQ_CHECK:
                            self.mPatchLogWarn(f"{_suggestion_msg}")
                        else:
                            self.mPatchLogError(f"{_suggestion_msg}")

                if len(_clusters_with_crs_down_and_no_high_availability) > 0:
                    _suggestion_msg = f"CRS services are supposed to be running on atleast 2 VMs. It is currently down on the given list of clusters and VMs : {str(_clusters_with_crs_down_and_no_high_availability)}. Please startup CRS services on required VMs and retry patch operations."
                    if self.mGetTask() == TASK_PREREQ_CHECK:
                        self.mPatchLogWarn(f"{_suggestion_msg}")
                    else:
                        _ret = DOMU_HEARTBEAT_NOT_RECEIVED
                        self.mAddError(_ret, _suggestion_msg)
            else:
                self.mPatchLogInfo("DomU heartbeat checks on cells will be skipped in case of non-rolling patch operation or in case of CRS up and running only on one VM on a given cluster.")

        except Exception as e:
            _suggestion_msg = "Exception in fetching DomU list and cluster details for heartbeat validations."
            if self.mGetTask() == TASK_PREREQ_CHECK:
                self.mPatchLogWarn(f"{_suggestion_msg}")
            else:
                self.mPatchLogError("Exception in fetching DomU list for heartbeat validations."+str(e))
                self.mPatchLogTrace(traceback.format_exc()) 
                _ret = INDIVIDUAL_PATCH_REQUEST_EXCEPTION
                self.mAddError(_ret, _suggestion_msg)
            
        finally:
            self.mPatchLogInfo("***Cluster wide CRS checks on clusters Completed.***")
            return _ret

    def mPreDom0UPatchCheck(self, aTargetList):
        """
        Takes a backup of the Audit file to preserve
        fedramp setting post upgrade and Rollback tasks.
        """

        if self.mGetFedRamp() == 'ENABLED':
            _Pre_Aud = "/etc/audit/audit.rules"
            _Post_Aud = "/etc/audit/audit.rules_FED"
            self.mPatchLogInfo(
                f"Executing fedramp file backup operation as the value of Fedamp Enable is set to {self.mGetFedRamp()}")
            self.mFedrampDom0RestoreConfig(aTargetList, _Pre_Aud, _Post_Aud)

    # Caters to both Patch or Rollback based on the aRolBack parameter
    def mPatchRollbackDom0sRolling(self, aBackupMode, aNodePatcherAndPatchList, aListOfNodesToBePatched, aRollback):
        """
        Patch/rollback rolling is handled by us
        (ie: we dont rely on  patchmgr with rolling option) since we need to
        to some checks before and after each patch/rollback on every dom[0U].

        If patching any dom0 fails the rest of the (not yet patched) dom[0U]s
        will not be attempted to be patched.
        """
        _callbacks = self.mGetCallBacks()
        _patchMgrObj = None

        # List of launch nodes to update patch state metadata
        _launch_nodes = []

        _task = ""
        if aRollback:
            _task = TASK_ROLLBACK
        else:
            _task = TASK_PATCH

        _nodes_successfuly_patched = []
        _node_patch_failed = None
        _patch_failed_message = ""
        _rc = PATCH_SUCCESS_EXIT_CODE
        _node_stat_index = 0
        _round = 0
        _count_nodes = 0
        _num_nodes_to_patch = 0
        _no_action_required = True

        _node_to_patch_nodes = self.__dom0_to_patch_dom0s
        _node_to_patch_initial_node = self.mGetDom0ToPatchInitialDom0()
        '''
         _nodes_to_patch_except_initial can only be the customised
         list of nodes as patch operations are required to be performed
         only on the input node provided.
        '''
        _nodes_to_patch_except_initial = list(set(aListOfNodesToBePatched) -
                                              set([self.__dom0_to_patch_dom0s]))
        _initial_node_list = [self.__dom0_to_patch_dom0s]
        _cns_string = CNS_DOM0_PATCHER
        _node_patch_base_after_unzip = self.__dom0_patch_base_after_unzip
        _node_patch_zip2_name = self.__dom0_patch_zip2_name
        _nodes_not_patched = list(aListOfNodesToBePatched)
        self.mPreDom0UPatchCheck(aListOfNodesToBePatched)

        _launch_nodes = [self.__dom0_to_patch_dom0s]
        if self.mGetDom0ToPatchInitialDom0():
            _launch_nodes.append(self.mGetDom0ToPatchInitialDom0())
        self.mPatchLogInfo(f"LaunchNodes = {str(_launch_nodes)}")

        _single_node_upgrade = False

        if (len(aNodePatcherAndPatchList) == 1 and
                aNodePatcherAndPatchList[0][0] == _node_to_patch_nodes):
            _node_stat_index = 1
            _round = 1
            _single_node_upgrade = True

        for _, _l in aNodePatcherAndPatchList:
            _num_nodes_to_patch += len(_l)

        self.mPatchLogInfo(f"Number of nodes available to update = {_num_nodes_to_patch}")

        if self.mIsMockEnv():
            # in mock setup, skip rack specific operations
            return _rc

        # Before patching started, fail if there are no domUs available on dom0.
        # However, this check can be ignored if caller specified forcibly.
        if (self.mGetAdditionalOptions() and 'SkipDomuCheck' in self.mGetAdditionalOptions()[0] \
                and self.mGetAdditionalOptions()[0]['SkipDomuCheck'].lower() == 'yes'):
            self.mPatchLogWarn("Before Patch Started: User opted to skip DomU validation check on dom0s")
        elif self.mGetInfrapatchExecutionValidator().mCheckCondition('checkHAChecksOnDom0'):
            self.mPatchLogWarn("DomU Availability Check: Before Patching Started.")
            _rc = self.mCheckDomuAvailability()
            if _rc != PATCH_SUCCESS_EXIT_CODE:
                return  _rc

        for _node_patcher, _node_patch_list in aNodePatcherAndPatchList:
            _round += 1

            # We are not suppose to continue further node upgrade if we found
            # any failure
            if _rc and _rc != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Failure detected in the node upgrade. Return code = {_rc}")
                break

            self.mPatchLogInfo(
                f"{PATCH_DOM0.upper()} {_node_patcher} will be used to patch {str(_node_patch_list)} rolling")

            # Set log dir with master request id tagged. Once upgrade is completed,
            # we would move and append with node name.
            self.mSetPatchmgrLogPathOnLaunchNode(_node_patch_base_after_unzip + "patchmgr_log_" +
                                                 self.mGetMasterReqId())

            '''
             The below __crs_config_enable_stat captures the status of CRS on 
             all DomU passed as per the iteration.
            '''
            self.__crs_config_enable_stat = {}

            # Update with launch node in the patch metadata json
            mUpdateMetadataLaunchNode(_launch_nodes, self.mGetMetadataJsonFile(), PATCH_DOM0, _node_patcher)

            for _node_to_patch in _node_patch_list:
                _is_system_valid_state = True
                _count_nodes += 1
                _node_stat_index += 1
                _comment = f"[{_count_nodes}/{_num_nodes_to_patch}]_{_node_to_patch}"

                self.mPatchLogInfo(
                    f"Node {_count_nodes} out of {_num_nodes_to_patch} node(s) is progressing at the moment.")

                # stop rollback if it found to be a fresh install
                if aRollback and self.mCheckFreshInstall(_node_to_patch):
                    _node_patch_failed =  _node_to_patch
                    _suggestion_msg = f"The node {_node_to_patch} seems to be fresh install and we cannot perform rollback operation. Current operation style is Rolling"
                    _rc = DOM0_ROLLBACK_FAILED_FOR_FRESH_INSTALL
                    self.mAddError(_rc, _suggestion_msg)
                    break

                # Update status
                self.mUpdatePatchStatus(True,
                                        (STEP_GATHER_NODE_DATA + '_' + PATCH_DOM0 + f'_[{_node_stat_index:d}]'), _comment)

                # Perform system consistency check only during patch operation.
                if not aRollback:
                    _is_system_valid_state, _suggestion_msg = self.mCheckSystemConsitency([_node_to_patch])

                _domU_listed_by_xm_list = []
                # we get domus from 'xm list' command to check heartbeat
                # betweeen domU -> cell after patch operation
                _domU_listed_by_xm_list = self.mGetCluPatchCheck().mCheckVMsUp(
                    _node_to_patch)
                self.mPatchLogInfo(f"List of domUs : {str(_domU_listed_by_xm_list)} running on dom0 :{_node_to_patch} ")

                self.mCollectEDVCellInfo(_domU_listed_by_xm_list)
                _pre_patch_version = self.mGetCluPatchCheck().mCheckTargetVersion(
                    _node_to_patch, PATCH_DOM0, aIsexasplice= self.mIsExaSplice())

                # update with current dom[0u] patcher which will be used in
                # CNS monitor
                _node_patch_progress = os.path.join(self.mGetLogPath(), _cns_string)
                with open(_node_patch_progress, "w") as write_nodestat:
                    write_nodestat.write(f"{_node_patcher}:{self.mGetPatchmgrLogPathOnLaunchNode()}")

                # create patchmgr object with bare minimum arguments local to this for loop for fresh InfraPatchManager obj ref
                # everytime the loop executes to avoid using old InfraPatchManager obj attribute ref, if any
                _patchMgrObj = InfraPatchManager(aTarget=PATCH_DOM0, aOperation=_task, aPatchBaseAfterUnzip=_node_patch_base_after_unzip,
                                           aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

                # now set the component's operation specific arguments
                _patchMgrObj.mSetIsoRepo(aIsoRepo=_node_patch_zip2_name)
                _patchMgrObj.mSetIsExaSpliceEnabled(aIsExaSpliceEnabled=self.mIsExaSplice())
                _patchMgrObj.mSetTargetVersion(aTargetVersion=self.mGetTargetVersion())
                _patchMgrObj.mSetSystemConsistencyState(aSystemConsistencyState=_is_system_valid_state)
                _patchMgrObj.mSetOperationStyle(aOperationStyle=self.mGetOpStyle())

                # create patchmgr nodes file
                _input_file = _patchMgrObj.mCreateNodesToBePatchedFile(aLaunchNode=_node_patcher, aHostList=[_node_to_patch])

                # prepare the patchmgr command for execution using the InfraPatchManager object
                _patch_cmd = _patchMgrObj.mGetPatchMgrCmd()

                # Update status
                if _round == 1:
                    self.mUpdatePatchStatus(True,
                                            (STEP_RUN_PATCH_SECOND_DOM0 + f'_[{_node_stat_index:d}]'), _comment)
                else:
                    self.mUpdatePatchStatus(True,
                                            (STEP_RUN_PATCH_DOM0 + f'_[{_node_stat_index:d}]'), _comment)

                # Run dbnu plugin on each Node before patchmgr command
                _dbnu_plugin_handler = self.mGetDbnuPluginHandler()
                if _dbnu_plugin_handler:
                    _rc = _dbnu_plugin_handler.mApply(_node_to_patch,
                                                       PATCH_DOM0)

                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                        _patch_failed_message = f"Error running Dbnu plugins validation. Return code was {str(_rc)}. Errors on screen and in logs"
                        self.mPatchLogError(_patch_failed_message)
                        break

                # Run Pre Post Plugins
                if self.mIsExacloudPluginEnabled():

                    _read_patch_state = mGetPatchStatesForNode(_launch_nodes, self.mGetMetadataJsonFile(),
                                                               _node_to_patch, PRE_PATCH)

                    self.mPatchLogInfo(f"Dom0 pre plugin patch status: {_read_patch_state}")
                    if not _read_patch_state:
                        _rc = DOM0_PRECHECK_EXECUTION_FAILED_ERROR
                        _suggestion_msg = f"Invalid patch state found during rolling patch = {_read_patch_state}"
                        self.mAddError(_rc, _suggestion_msg)
                        break

                    # If anything left at last run of pre plugin and patchmgr is still
                    # running, then re-run plugin too.
                    if _read_patch_state in [PATCH_PENDING, PATCH_RUNNING]:
                        if _read_patch_state == PATCH_PENDING:
                            # Update patch metadata status progress for pre plugins
                            mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _node_to_patch,
                                                 self.mGetMetadataJsonFile(), PRE_PATCH, PATCH_RUNNING)
                        _rc = self.mGetPluginHandler().mApply(_node_to_patch,
                                                               PATCH_DOM0, PRE_PATCH,
                                                               aRollback=aRollback)
                        if _rc != PATCH_SUCCESS_EXIT_CODE:
                            mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _node_to_patch,
                                                 self.mGetMetadataJsonFile(), PRE_PATCH, PATCH_FAILED)
                            break

                        mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _node_to_patch,
                                             self.mGetMetadataJsonFile(), PRE_PATCH, PATCH_COMPLETED)
                    elif _read_patch_state == PATCH_FAILED:
                        _suggestion_msg = f"Patch read state : FAILED on : {_node_to_patch}"
                        _rc = DOM0_PRECHECK_EXECUTION_FAILED_ERROR
                        self.mAddError(_rc, _suggestion_msg)
                        break

                # Run plugin metadata based exacloud plugins before patchmgr cmd
                if self.mGetTask() in [ TASK_PATCH ] and not self.mIsExaSplice() and len(self.mGetPluginMetadata()) > 0:
                    _plugin_metadata_based_exacloud_plugin_enabled, _ = checkPluginEnabledFromInfraPatchMetadata(self.mGetPluginMetadata())
                    if _plugin_metadata_based_exacloud_plugin_enabled:
                        # Execute plugin metadata based exacloud plugins
                        self.mPatchLogInfo(
                            f"Executing Exacloud Plugins implicitly based on the infra patch plugin metadata during PrePatch stage and as part of {self.mGetOpStyle()} patching.")
                        _rc = self.mGetPluginHandler().mExacloudPluginMetadataExecutor([_node_to_patch], "pre")
                        if _rc != PATCH_SUCCESS_EXIT_CODE:
                            break

                """
                Run DB healtchecks on vms where crs auto_start is enabled and crs is running
                """
                _crs_running_vm_list = []
                _crs_running_vm_list.extend(
                    item for item in _domU_listed_by_xm_list if item in self.__crs_autostart_enabled_vm_set)

                _rc = self.mDetectCDBDowntimeDuringDom0Patching(_node_to_patch, _crs_running_vm_list)
                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    break

                _rc = self.mDetectPDBDowntimeDuringDom0Patching(_node_to_patch, _crs_running_vm_list)
                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    break

                # Run patch command
                # If there are no patchmgr sessions running, then run patchmgr command
                # In this context, PATCH_SUCCESS_EXIT_CODE infers NO_PATCHMGR Session is running.
                # Skip patchmgr existence check during clusterless patching.

                _patchmgr_session_exit = PATCH_SUCCESS_EXIT_CODE
                _patchmgr_active_node = None

                if self.mPerformPatchmgrExistenceCheck():
                    # check for patchmgr session existence
                    _patchMgrObj.mSetLaunchNode(aLaunchNode=None)
                    _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=self.mGetCustomizedDom0List())

                    _patchmgr_session_exit, _patchmgr_active_node = _patchMgrObj.mCheckForPatchMgrSessionExistence()

                if _patchmgr_session_exit == PATCH_SUCCESS_EXIT_CODE:  # No patchmgr session found in any of the nodes,
                    # so re-execute with same launch/_node_patcher
                    # Update patch metadata status progress for patchmgr
                    mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _node_to_patch,
                                         self.mGetMetadataJsonFile(), PATCH_MGR, PATCH_RUNNING)

                    '''
                      Write crs stop message into cell alert logs.
                      It is skipped during exasplice patch.
                    '''
                    if not self.mIsExaSplice():
                        _rc = self.mWriteCRSMessagesToCellTraceLogs(_node_to_patch)
                        if _rc != PATCH_SUCCESS_EXIT_CODE:
                            break

                    _patchMgrObj.mSetLaunchNode(aLaunchNode=_node_patcher)

                    _rc = _patchMgrObj.mExecutePatchMgrCmd(aPatchMgrCmd=_patch_cmd)
                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                        break

                    # Let upper layer look for notification detail to be evaluated.
                    _no_action_required = False

                    # Capture time profile details
                    if _round == 1 or _single_node_upgrade:
                        self.mPopulateInfrapatchingTimeStatsEntries(aNewStage="PATCH_MGR", aNewSubStage="",
                                                                    aNewStageNodes=str([_node_to_patch]),
                                                                    aCompletedStage="PRE_PATCH", aCompletedSubStage="")
                    else:
                        self.mPopulateInfrapatchingTimeStatsEntries(aNewStage="PATCH_MGR", aNewSubStage="",
                                                                    aNewStageNodes=str([_node_to_patch]),
                                                                    aCompletedStage="POST_PATCH", aCompletedSubStage="",
                                                                    aCompletedStageNodeDetails=str(
                                                                        [_nodes_successfuly_patched[-1]]))

                else:
                    # TODO: We need to handle patch non-retry in future. Time being we are forcibly stopping.
                    if not self.mPatchRequestRetried():
                        self.mPatchLogError('Found older patchmgr session. Forcibly terminating patching request')
                        return _patchmgr_session_exit

                    # Already patchmgr is running, just monitor patchmgr console on the node.
                    self.mPatchLogInfo(
                        f"Patchmanager session exists and return code = {_patchmgr_session_exit}, Patchmgr session active node = {_patchmgr_active_node}")
                    _patchMgrObj.mSetLaunchNode(aLaunchNode=_patchmgr_active_node)
                    _node_patcher = _patchmgr_active_node

                # reset the node list to make sure patchmgr cmd execution 
                # only looked at the launch node
                _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=None)

                # Following InfraPatchManager api sets the patchmgr execution status into mStatusCode method
                # hence not required to return/read a value from this api
                # this will help to use the patchMgr status apis 
                # (mIsSuccess/mIsFailed/mIsTimedOut/mIsCompleted) wherever required

                _patchMgrObj.mWaitForPatchMgrCmdExecutionToComplete()

                self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")

                _rc = _patchMgrObj.mGetStatusCode()

                self.mPopulateInfrapatchingTimeStatsEntries(aNewStage="POST_PATCH", aNewSubStage="",
                                                            aNewStageNodes=str([_node_to_patch]),
                                                            aCompletedStage="PATCH_MGR", aCompletedSubStage="",
                                                            aCompletedStageNodeDetails=str([_node_to_patch]))

                # The error is mostly populated from patchmgr side.
                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    # Update patch metadata status progress for patchmgr
                    mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _node_to_patch,
                                         self.mGetMetadataJsonFile(), PATCH_MGR, PATCH_FAILED)
                else:
                    # Update patch metadata status progress for patchmgr
                    mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _node_to_patch,
                                         self.mGetMetadataJsonFile(), PATCH_MGR, PATCH_COMPLETED)

                self.mUpdatePatchStatus(True,
                                        (STEP_CLEAN_ENV + '_' + PATCH_DOM0 + f'_[{_node_stat_index:d}]'), _comment)

                # Get the logs, diags and so on
                _patch_log = str(
                    self.mGetDom0FileCode(_node_patcher,
                                          self.mGetPatchmgrLogPathOnLaunchNode()))
                self.mGetPatchMgrOutFiles(_node_patcher,
                                          self.mGetPatchmgrLogPathOnLaunchNode(),
                                          _patch_log)

                '''
                 Collect patchmgr diag logs for debugging only
                 when the final exit code from patch operation 
                 is not PATCH_SUCCESS_EXIT_CODE.
                '''
                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    self.mGetPatchMgrDiagFiles(_node_patcher,
                                               PATCH_DOM0,
                                               [_node_to_patch],
                                               self.mGetPatchmgrLogPathOnLaunchNode())
                else:
                    self.mPatchLogInfo("Patchmgr diag logs are not collected in case of a successful infra patch operation.")

                self.mGetPatchMgrMiscLogFiles(_node_patcher,
                                              self.mGetPatchmgrLogPathOnLaunchNode())


                # Print all the log details at the end of log files copy.
                self.mPrintPatchmgrLogFormattedDetails()   

                _dom0 = exaBoxNode(get_gcontext())
                _dom0.mConnect(aHost=_node_patcher)
                _dom0.mExecuteCmdLog(f"rm -f {_input_file}")

                # Moving log_dir to log_dir_<node_patched>, before starting another one
                _dom0.mExecuteCmdLog(
                    f"mv -f {self.mGetPatchmgrLogPathOnLaunchNode()} {self.mGetPatchmgrLogPathOnLaunchNode()}_{_node_patcher.split('.')[0]}")
                _dom0.mDisconnect()

                # Log location is updated in mUpdateNodePatcherLogDir for proper collection of final CNS notification
                self.mUpdateNodePatcherLogDir(_node_patcher, _cns_string)

                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    _node_patch_failed = _node_to_patch
                    _patch_failed_message = f"Error patching {_node_patch_failed} using {_node_patcher} to patch it. return code was {str(_rc)}. Errors on screen and in logs"
                    break

                _nodes_successfuly_patched.append(_node_to_patch)
                _nodes_not_patched.remove(_node_to_patch)

                # We need this data for the plugins
                if self.mIsExacloudPluginEnabled():
                    self.mGetPluginHandler().mSetLastNodePatched(_node_to_patch)

                self.mUpdatePatchStatus(True,
                                        (STEP_POSTCHECKS + '_' + PATCH_DOM0 + f'_[{_node_stat_index:d}]'), _comment)

                _rc = self.mPostDom0PatchCheck(aDom0=_node_to_patch,
                                                aDomUList=_domU_listed_by_xm_list,
                                                aPrePatchVersion=_pre_patch_version,
                                                aPostPatchTargetVersion=self.mGetTargetVersion(),
                                                aRollback=aRollback)
                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    _node_patch_failed = _node_to_patch
                    _patch_failed_message = (
                        f"dom0 [{_node_to_patch}] patching succeeded, but post-patch checks failed")
                    break

                if self.mIsExacloudPluginEnabled():

                    # Update patch metadata status progress for post plugins
                    mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _node_to_patch,
                                         self.mGetMetadataJsonFile(), POST_PATCH, PATCH_RUNNING)
                    _ret = self.mGetPluginHandler().mApply(_node_to_patch,
                                                           PATCH_DOM0, POST_PATCH,
                                                           aRollback=aRollback)
                    if _ret != PATCH_SUCCESS_EXIT_CODE:
                        mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _node_to_patch,
                                             self.mGetMetadataJsonFile(), POST_PATCH, PATCH_FAILED)
                        # do not overwrite the error code from mApply
                        _suggestion_msg = f"Exacloud plugin failed during post patch : {_node_to_patch}"
                        _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
                        if _child_request_error_already_exists_in_db:
                            self.mPatchLogError(_suggestion_msg)
                        else:
                            _rc = DOM0_POST_EXACLOUD_PLUGINS_FAILED
                            self.mAddError(_ret, _suggestion_msg)
                        break

                    mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _node_to_patch,
                                         self.mGetMetadataJsonFile(), POST_PATCH, PATCH_COMPLETED)

                # Run plugin metadata based exacloud plugins after patchmgr cmd
                if self.mGetTask() in [ TASK_PATCH ] and not self.mIsExaSplice() and len(self.mGetPluginMetadata()) > 0:
                    _plugin_metadata_based_exacloud_plugin_enabled, _ = checkPluginEnabledFromInfraPatchMetadata(self.mGetPluginMetadata())
                    if _plugin_metadata_based_exacloud_plugin_enabled:
                        # Execute plugin metadata based exacloud plugins
                        self.mPatchLogInfo(
                            f"Executing Exacloud Plugins implicitly based on the infra patch plugin metadata during PostPatch stage and as part of {self.mGetOpStyle()} patching.")
                        _rc = self.mGetPluginHandler().mExacloudPluginMetadataExecutor([_node_to_patch], "post")
                        if _rc != PATCH_SUCCESS_EXIT_CODE:
                            break

                #Cleanup dbnu plugins
                if self.mIsDbnuPluginEnabled():
                    self.mGetDbnuPluginHandler().mCleanupDbnuPluginsFromNode(_node_to_patch, PATCH_DOM0)

                # if any dom[0U] patch or post-patch failed, we cant risk patching
                # another node and it having issues also
                if _node_patch_failed:
                    break

            # Invoke sleep method only when:
            #   -> if user time specified is more than 1 seconds and
            #   -> if its not single node upgrade and then
            #   -> if upgrading node is not last node in the list.
            # Also, update the patch metadata file with sleeping mode.
            if (len(self.mGetIncludeNodeList()) >= 2) and \
                    self.mGetSleepbetweenComputeTimeInSec() > 0 and \
                    _num_nodes_to_patch > _count_nodes:
                mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _node_to_patch,
                                     self.mGetMetadataJsonFile(), POST_PATCH, PATCH_SLEEP_START)
                self.mSleepBtwNodes()
                mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _node_to_patch,
                                     self.mGetMetadataJsonFile(), POST_PATCH, PATCH_SLEEP_END)

        self.mPatchLogInfo(
            f"\n{PATCH_DOM0.upper()}s patched: {' '.join(_nodes_successfuly_patched)}\n{PATCH_DOM0.upper()}s not patched: {' '.join(_nodes_not_patched)}")
        if _node_patch_failed:
            self.mPatchLogError(_patch_failed_message)
            self.mPatchLogError(f"{PATCH_DOM0.upper()} patching or post-patching failed on: {str(_node_patch_failed)}")

        # To be extra careful, after the patch completed with all success, do the domUs available check on dom0 also.
        # However, this check can be ignored if caller specified forcibly.
        if _rc == PATCH_SUCCESS_EXIT_CODE and _no_action_required == False:
            if (self.mGetAdditionalOptions() and 'SkipDomuCheck' in self.mGetAdditionalOptions()[0] \
                    and self.mGetAdditionalOptions()[0]['SkipDomuCheck'].lower() == 'yes'):
                self.mPatchLogWarn("After Patch completed: User opted to skip DomU validation check on dom0s")
            elif self.mGetInfrapatchExecutionValidator().mCheckCondition('checkHAChecksOnDom0'):
                self.mPatchLogWarn("DomU Availability Check: After Patch Completed.")
                _rc = self.mCheckDomuAvailability()

        # If patchmgr not run and also no action needs to be taken, then our return code should
        # be essentially override by no action required code, otherwise, CNS code will keep on wait
        # for driver node to get the patchmgr xml report.
        if _rc == PATCH_SUCCESS_EXIT_CODE and _no_action_required == True:
            _rc = NO_ACTION_REQUIRED

        return _rc

    def mPatchRollbackDom0sNonRolling(self, aBackupMode,
                                      aNodePatcherAndPatchList, aListOfNodesToBePatched, aRollback):
        """
        patch dom[0U]s in non-rolling fashion
        """

        # List of launch nodes to update patch state metadata
        _launch_nodes = []
        _callbacks = self.mGetCallBacks()
        _rc = PATCH_SUCCESS_EXIT_CODE
        _task = ""
        _node_prepatch_version = {}
        _count_nodes = 0
        _node_stat_index = 0
        _num_nodes_to_patch = 0
        _no_action_required = True
        _patchMgrObj = None

        if aRollback:
            _task = TASK_ROLLBACK
        else:
            _task = TASK_PATCH

        _node_to_patch_nodes = self.__dom0_to_patch_dom0s
        _node_to_patch_initial_node = self.mGetDom0ToPatchInitialDom0()
        '''
         _nodes_to_patch_except_initial can only be the customised
         list of nodes as patch operations are required to be performed
         only on the input node provided.
        '''
        _nodes_to_patch_except_initial = list(set(aListOfNodesToBePatched) -
                                              set([self.__dom0_to_patch_dom0s]))
        _initial_node_list = [self.__dom0_to_patch_dom0s]
        _cns_string = CNS_DOM0_PATCHER
        _node_patch_base_after_unzip = self.__dom0_patch_base_after_unzip
        _node_patch_zip2_name = self.__dom0_patch_zip2_name
        self.mPreDom0UPatchCheck(aListOfNodesToBePatched)

        _launch_nodes = [self.__dom0_to_patch_dom0s]
        if self.mGetDom0ToPatchInitialDom0():
            _launch_nodes.append(self.mGetDom0ToPatchInitialDom0())

        _single_node_upgrade = False

        if (len(aNodePatcherAndPatchList) == 1 and
                aNodePatcherAndPatchList[0][0] == _node_to_patch_nodes):
            _node_stat_index = 1
            _single_node_upgrade = True

        # Set log dir with master request id tagged. Once upgrade is completed,
        # we would move and append with node name.
        self.mSetPatchmgrLogPathOnLaunchNode(_node_patch_base_after_unzip + "patchmgr_log_" +
                                             self.mGetMasterReqId())

        # Needed to capture time profile details
        _previous_iteration_patch_node_list = []

        if self.mIsMockEnv():
            # in mock setup, skip rack specific operations
            return _rc

        for _node_patcher, _node_patch_list in aNodePatcherAndPatchList:
            _is_system_valid_state = True
            _node_stat_index += 1

            # Perform system consistency check only during patch operation on list of nodes.
            if not aRollback:
                _is_system_valid_state, _suggestion_msg = self.mCheckSystemConsitency(_node_patch_list)

            _dom0 = exaBoxNode(get_gcontext())
            _dom0.mConnect(aHost=_node_patcher)

            self.mPatchLogInfo(
                f"{PATCH_DOM0.upper()} {_node_patcher} will be used to patch {str(_node_patch_list)} non-rolling")

            # update with current node patcher which will be used in CNS monitor
            _node_patch_progress = os.path.join(self.mGetLogPath(), _cns_string)
            with open(_node_patch_progress, "w") as write_nodestat:
                write_nodestat.write(f"{_node_patcher}:{self.mGetPatchmgrLogPathOnLaunchNode()}")

            # Update with launch node in the patch metadata json
            mUpdateMetadataLaunchNode(_launch_nodes, self.mGetMetadataJsonFile(), PATCH_DOM0, _node_patcher)

            # gather the data which we will need for the post patch checks
            _domU_up_per_dom0 = {}  # key is Dom0, value is list of DomU
            #  key is Dom[0U], value is version prior to patching

            for _node_to_patch in _node_patch_list:
                # Update status
                self.mUpdatePatchStatus(True,
                                        (STEP_GATHER_NODE_DATA + '_'
                                         + PATCH_DOM0 + f'_[{_node_stat_index:d}]'),
                                        _node_to_patch)

                # stop rollback if it found to be a fresh install
                if aRollback and self.mCheckFreshInstall(_node_to_patch):
                    _node_patch_failed =  _node_to_patch
                    _suggestion_msg = f"The node {_node_to_patch} seems to be fresh install and we cannot perform rollback operation. Current operation style is Non-Rolling"
                    _rc = DOM0_ROLLBACK_FAILED_FOR_FRESH_INSTALL
                    self.mAddError(_rc, _suggestion_msg)
                    break

                '''
                 Below code snippet validates if CRS is enabled or disabled.
                 if CRS is enabled it would validate if CRS is ONLINE before
                 the start of patch or rollback activity.
                '''
                _domU_listed_by_xm_list = \
                    self.mGetCluPatchCheck().mCheckVMsUp(_node_to_patch)
                _domU_up_per_dom0[_node_to_patch] = _domU_listed_by_xm_list
                self.mPatchLogInfo(f"Dom0 {_node_to_patch} has {str(_domU_listed_by_xm_list)} domU up")

                _pre_patch_version = self.mGetCluPatchCheck().mCheckTargetVersion(
                    _node_to_patch, PATCH_DOM0, aIsexasplice= self.mIsExaSplice())
                self.mCollectEDVCellInfo(_domU_listed_by_xm_list)
                _node_prepatch_version[_node_to_patch] = _pre_patch_version
                self.mPatchLogInfo(f"{PATCH_DOM0.upper()} {_node_to_patch} is at version {_pre_patch_version}")
            # end of for

            # create patchmgr object with bare minimum arguments local to this for loop for fresh InfraPatchManager obj ref
            # everytime the loop executes to avoid using old InfraPatchManager obj attribute ref, if any
            _patchMgrObj = InfraPatchManager(aTarget=PATCH_DOM0, aOperation=_task, aPatchBaseAfterUnzip=_node_patch_base_after_unzip,
                                       aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

            # now set the component's operation specific arguments
            _patchMgrObj.mSetIsoRepo(aIsoRepo=_node_patch_zip2_name)
            _patchMgrObj.mSetIsExaSpliceEnabled(aIsExaSpliceEnabled=self.mIsExaSplice())
            _patchMgrObj.mSetTargetVersion(aTargetVersion=self.mGetTargetVersion())
            _patchMgrObj.mSetSystemConsistencyState(aSystemConsistencyState=_is_system_valid_state)
            _patchMgrObj.mSetOperationStyle(aOperationStyle=self.mGetOpStyle())

            # create patchmgr nodes file
            _input_file = _patchMgrObj.mCreateNodesToBePatchedFile(aLaunchNode=_node_patcher, aHostList=_node_patch_list)

            # prepare the patchmgr command for execution using the InfraPatchManager object
            _patch_cmd = _patchMgrObj.mGetPatchMgrCmd()

            # Update status
            self.mUpdatePatchStatus(True,
                                    (STEP_SHUTDOWN_VMS + '_' + PATCH_DOM0 + f'_[{_node_stat_index:d}]'))

            # Shutdown all of the domUs on all the dom0 that will be patched
            # or else patchmgr will complain. Shutdown is not needed for
            # exasplice and if there are no VMs already running.
            #
            # DomU list is collected from the custom node list.
            #
            if not self.mIsExaSplice() and self.mGetDomUList(aFromXmList=True):
                _processes = ProcessManager()
                _rc_status = _processes.mGetManager().list()
                for _dom0_to_patch in _node_patch_list:
                    """
                    If the graceful shutdown of the VM does not happen,
                    xm destroy/virsh destroy would be called.                
                    """
                    _p = ProcessStructure(self.mGetCluPatchCheck().mShutDownVMs,
                                            [_dom0_to_patch, _domU_up_per_dom0[_dom0_to_patch], _rc_status],_dom0_to_patch)

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
                    # Stop patching if failure is occurred during shutdown.
                    break
            else:
                self.mPatchLogInfo("Not attempted to shutdown the VMs.")

            # Update patch status with the amount of dom0s we are patching
            if _node_stat_index == 1:
                self.mUpdatePatchStatus(True,
                                        STEP_RUN_PATCH_SECOND_DOM0 + '_[1]',
                                        _node_patcher)
            else:
                self.mUpdatePatchStatus(True,
                                        STEP_RUN_PATCH_DOM0 + f'_[{_node_stat_index:d}]')

            # Run dbnu plugin on each Node before patchmgr command
            _dbnu_plugin_handler = self.mGetDbnuPluginHandler()
            if _dbnu_plugin_handler:
                for _dom0_to_patch in _node_patch_list:
                    _rc = _dbnu_plugin_handler.mApply(_dom0_to_patch,
                                                       PATCH_DOM0)

                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                        _patch_failed_message = f"Error running Dbnu plugins validation. Return code was {str(_rc)}. Errors on screen and in logs"
                        self.mPatchLogError(_patch_failed_message)
                        _dom0.mDisconnect()
                        break

            # Run exacloud plugins on each node before patchmgr cmd
            if self.mIsExacloudPluginEnabled():

                self.mPatchLogInfo(f"Running dom0 pre exacloud plugins on : {json.dumps(_node_patch_list, indent=4)}")
                for _dom0_to_patch in _node_patch_list:
                    _read_patch_state = mGetPatchStatesForNode(_launch_nodes, self.mGetMetadataJsonFile(),
                                                               _dom0_to_patch, PRE_PATCH)
                    self.mPatchLogInfo(f"Dom0 pre plugin patch status: {_read_patch_state}")
                    if not _read_patch_state:
                        _rc = DOM0_PRECHECK_EXECUTION_FAILED_ERROR
                        _suggestion_msg = f"Invalid patch state found during non-rolling patch = {_read_patch_state} on Node : {_dom0_to_patch}"
                        self.mAddError(_rc, _suggestion_msg)
                        break

                    # If anything left at last run of pre plugin and patchmgr is still
                    # running, then re-run plugin too.
                    if _read_patch_state in [PATCH_PENDING, PATCH_RUNNING]:
                        if _read_patch_state == PATCH_PENDING:
                            # Update patch metadata status progress for pre plugins
                            mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _dom0_to_patch,
                                                 self.mGetMetadataJsonFile(), PRE_PATCH, PATCH_RUNNING)

                        _rc = self.mGetPluginHandler().mApply(_dom0_to_patch,
                                                               PATCH_DOM0, PRE_PATCH,
                                                               aRollback=aRollback)
                        if _rc != PATCH_SUCCESS_EXIT_CODE:
                            mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _dom0_to_patch,
                                                 self.mGetMetadataJsonFile(), PRE_PATCH, PATCH_FAILED)
                            break

                        mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _dom0_to_patch,
                                             self.mGetMetadataJsonFile(), PRE_PATCH, PATCH_COMPLETED)
                    elif _read_patch_state == PATCH_FAILED:
                        _suggestion_msg = f"_read_patch_state (rolling): {_read_patch_state} on Node : {_dom0_to_patch}"
                        _rc = DOM0_PRECHECK_EXECUTION_FAILED_ERROR
                        self.mAddError(_rc, _suggestion_msg)
                        break
                    elif _read_patch_state != PATCH_COMPLETED:
                        _suggestion_msg = f"_read_patch_state (rolling): {_read_patch_state} on Node : {_dom0_to_patch}"
                        _rc = DOM0_PRECHECK_EXECUTION_FAILED_ERROR
                        self.mAddError(_rc, _suggestion_msg)
                        break

            # Run plugin metadata based exacloud plugins before patchmgr cmd
            if self.mGetTask() in [ TASK_PATCH ] and not self.mIsExaSplice() and len(self.mGetPluginMetadata()) > 0:
                _plugin_metadata_based_exacloud_plugin_enabled, _ = checkPluginEnabledFromInfraPatchMetadata(self.mGetPluginMetadata())
                if _plugin_metadata_based_exacloud_plugin_enabled:
                    # Execute plugin metadata based exacloud plugins
                    self.mPatchLogInfo(
                        f"Executing Exacloud Plugins implicitly based on the infra patch plugin metadata during PrePatch stage and as part of {self.mGetOpStyle()} patching.")
                    _rc = self.mGetPluginHandler().mExacloudPluginMetadataExecutor(_node_patch_list, "pre")
                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                        break

            if _rc != PATCH_SUCCESS_EXIT_CODE:
                _patch_failed_message = f"Error running pre exacloud plugins. Return code was {str(_rc)}. Errors on screen and in logs"
                self.mPatchLogError(_patch_failed_message)
                _dom0.mDisconnect()
                break

            # Run patch command
            # If there are no patchmgr sessions running, then run patchmgr command
            # In this context, PATCH_SUCCESS_EXIT_CODE infers NO_PATCHMGR Session is running.
            # Skip patchmgr existence check during clusterless patching.

            _patchmgr_session_exit = PATCH_SUCCESS_EXIT_CODE
            _patchmgr_active_node = None
            
            if self.mPerformPatchmgrExistenceCheck():
                # check for patchmgr session existence
                _patchMgrObj.mSetLaunchNode(aLaunchNode=None)
                _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=self.mGetCustomizedDom0List())

                _patchmgr_session_exit, _patchmgr_active_node = _patchMgrObj.mCheckForPatchMgrSessionExistence()

            if _patchmgr_session_exit == PATCH_SUCCESS_EXIT_CODE:  # No patchmgr session found in any of the nodes, so re-execute
                # with same launch/_node_patcher
                # Update patch metadata status progress for patchmgr
                for _n in _node_patch_list:
                    mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _n,
                                         self.mGetMetadataJsonFile(), PATCH_MGR, PATCH_RUNNING)

                    '''
                      Write crs stop message into cell alert logs.
                      It is skipped during exasplice patch.
                    '''
                    if not self.mIsExaSplice():
                        _rc = self.mWriteCRSMessagesToCellTraceLogs(_n)
                        if _rc != PATCH_SUCCESS_EXIT_CODE:
                            break

                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    break

                # set the launch node and execute patchmgr cmd
                _patchMgrObj.mSetLaunchNode(aLaunchNode=_node_patcher)

                _rc = _patchMgrObj.mExecutePatchMgrCmd(aPatchMgrCmd=_patch_cmd)
                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    break

                # Let upper layer look for notification detail to be evaluated.
                _no_action_required = False

                # Capture time profile details
                if _node_stat_index == 1 or _single_node_upgrade:
                    self.mPopulateInfrapatchingTimeStatsEntries(aNewStage="PATCH_MGR", aNewSubStage="",
                                                                aNewStageNodes=str(_node_patch_list),
                                                                aCompletedStage="PRE_PATCH", aCompletedSubStage="")
                else:
                    self.mPopulateInfrapatchingTimeStatsEntries(aNewStage="PATCH_MGR", aNewSubStage="",
                                                                aNewStageNodes=str(_node_patch_list),
                                                                aCompletedStage="POST_PATCH", aCompletedSubStage="",
                                                                aCompletedStageNodeDetails=str(
                                                                    _previous_iteration_patch_node_list))

            else:
                # TODO: We need to handle patch non-retry in future. Time being we are forcibly stopping.
                if not self.mPatchRequestRetried():
                    self.mPatchLogError('Found older patchmgr session. Forcibly terminating patching request')
                    return _patchmgr_session_exit

                # Already patchmgr is running, just monitor patchmgr console on the node.
                self.mPatchLogInfo(
                    f"Patchmanager session exists . Monitoring Patchmgr session on active node = {_patchmgr_active_node}")
                _patchMgrObj.mSetLaunchNode(aLaunchNode=_patchmgr_active_node)
                _node_patcher = _patchmgr_active_node

            # reset the node list to make sure patchmgr cmd execution 
            # only looked at the launch node
            _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=None)

            # Following InfraPatchManager api sets the patchmgr execution status into mStatusCode method
            # hence not required to return/read a value from this api
            # this will help to use the patchMgr status apis 
            # (mIsSuccess/mIsFailed/mIsTimedOut/mIsCompleted) wherever required
            _patchMgrObj.mWaitForPatchMgrCmdExecutionToComplete()

            self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")

            _rc = _patchMgrObj.mGetStatusCode()

            # Capture time profile details
            self.mPopulateInfrapatchingTimeStatsEntries(aNewStage="POST_PATCH", aNewSubStage="",
                                                        aNewStageNodes=str(_node_patch_list),
                                                        aCompletedStage="PATCH_MGR", aCompletedSubStage="",
                                                        aCompletedStageNodeDetails=str(_node_patch_list))

            # Update patch metadata progress status for patchmgr status
            # The error (from _rc) is mostly populated from patchmgr side
            _patch_metadata_status = ""
            if _rc != PATCH_SUCCESS_EXIT_CODE:
                _patch_metadata_status = PATCH_FAILED
            else:
                _patch_metadata_status = PATCH_COMPLETED

            for _n in _node_patch_list:
                mUpdatePatchMetadata(_task, _launch_nodes, _n,
                                     self.mGetMetadataJsonFile(), PATCH_MGR, _patch_metadata_status)

            _dom0.mConnect(aHost=_node_patcher)
            self.mUpdatePatchStatus(True,
                                    (STEP_CLEAN_ENV + '_' + PATCH_DOM0 + f'_[{_node_stat_index:d}]'))

            # Get the logs, diags and so on
            _patch_log = str(
                self.mGetDom0FileCode(_node_patcher,
                                      self.mGetPatchmgrLogPathOnLaunchNode()))
            self.mGetPatchMgrOutFiles(_node_patcher,
                                      self.mGetPatchmgrLogPathOnLaunchNode(),
                                      _patch_log)

            '''
             Collect patchmgr diag logs for debugging only
             when the final exit code from patch operation 
             is not PATCH_SUCCESS_EXIT_CODE.
            '''
            if _rc != PATCH_SUCCESS_EXIT_CODE:
                self.mGetPatchMgrDiagFiles(_node_patcher,
                                           PATCH_DOM0,
                                           _node_patch_list,
                                           self.mGetPatchmgrLogPathOnLaunchNode())
            else:
                self.mPatchLogInfo("Patchmgr diag logs are not collected in case of a successful infra patch operation.")

            if aRollback:
                self.mGetPatchMgrMiscLogFiles(_node_patcher,
                                              self.mGetPatchmgrLogPathOnLaunchNode())
            else:
                self.mGetPatchMgrMiscLogFiles(_node_patcher,
                                              self.mGetPatchmgrLogPathOnLaunchNode(),
                                              TASK_PATCH,
                                              _node_patch_list)

            # Print all the log details at the end of log files copy.
            self.mPrintPatchmgrLogFormattedDetails()

            _dom0.mExecuteCmdLog(f"rm -f {_input_file}")

            # Moving log_dir to log_dir_<node_patched>, before starting another one
            _dom0.mExecuteCmdLog(
                f"mv -f {self.mGetPatchmgrLogPathOnLaunchNode()} {self.mGetPatchmgrLogPathOnLaunchNode()}_{_node_patcher.split('.')[0]}")

            # Log location is updated in mUpdateNodePatcherLogDir for proper collection of final CNS notification
            self.mUpdateNodePatcherLogDir(_node_patcher, _cns_string)

            if _rc != PATCH_SUCCESS_EXIT_CODE:
                _patch_failed_message = f"Error patching one of {str(_node_patch_list)} using {_node_patcher} to patch it. return code was {str(_rc)}. Errors. on screen and in logs"
                self.mPatchLogError(_patch_failed_message)
                _dom0.mDisconnect()
                break

            # post checks on each node
            _post_patch_failed_nodes = []
            # Update status
            self.mUpdatePatchStatus(True,
                                    (STEP_POSTCHECKS + '_' + PATCH_DOM0 + f'_[{_node_stat_index:d}]'))

            for _dom0_to_patch in _node_patch_list:
                _rc = self.mPostDom0PatchCheck(aDom0=_dom0_to_patch,
                                                aDomUList=_domU_up_per_dom0[_dom0_to_patch],
                                                aPrePatchVersion=_node_prepatch_version[_dom0_to_patch],
                                                aPostPatchTargetVersion=self.mGetTargetVersion(),
                                                aRollback=aRollback)

                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    _post_patch_failed_nodes.append(_dom0_to_patch)

            if _post_patch_failed_nodes:
                _patch_failed_message = f"{PATCH_DOM0.upper()} {str(_post_patch_failed_nodes)} patching succeded, but post-patch checks failed. Return code was = {str(_rc)} "
                self.mPatchLogError(_patch_failed_message)
                _dom0.mDisconnect()
                break

            # Run exacloud plugins on each node after patchmgr cmd
            if (self.mIsExacloudPluginEnabled()):

                self.mPatchLogInfo(f"Running dom0 post exacloud plugins on : {json.dumps(_node_patch_list, indent=4)}")
                for _dom0_to_patch in _node_patch_list:
                    # Update patch metadata status progress for pre plugins
                    mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _dom0_to_patch,
                                         self.mGetMetadataJsonFile(), POST_PATCH, PATCH_RUNNING)
                    _ret = self.mGetPluginHandler().mApply(_dom0_to_patch,
                                                           PATCH_DOM0, POST_PATCH,
                                                           aRollback=aRollback)
                    if _ret != PATCH_SUCCESS_EXIT_CODE:
                        mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _dom0_to_patch,
                                             self.mGetMetadataJsonFile(), POST_PATCH, PATCH_FAILED)
                        _suggestion_msg = f"Exacloud plugin failed during post patch : {_dom0_to_patch}"
                        # do not overwrite error coming from plugin mApply
                        _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
                        if _child_request_error_already_exists_in_db:
                            self.mPatchLogError(_suggestion_msg)
                        else:
                            self.mAddError(_ret, _suggestion_msg)
                        break

                    mUpdatePatchMetadata(PATCH_DOM0, _launch_nodes, _dom0_to_patch,
                                         self.mGetMetadataJsonFile(), POST_PATCH, PATCH_COMPLETED)

            # Run plugin metadata based exacloud plugins after patchmgr cmd
            if self.mGetTask() in [ TASK_PATCH ] and not self.mIsExaSplice() and len(self.mGetPluginMetadata()) > 0:
                _plugin_metadata_based_exacloud_plugin_enabled, _ = checkPluginEnabledFromInfraPatchMetadata(self.mGetPluginMetadata())
                if _plugin_metadata_based_exacloud_plugin_enabled:
                    # Execute plugin metadata based exacloud plugins
                    self.mPatchLogInfo(
                        f"Executing Exacloud Plugins implicitly based on the infra patch plugin metadata during PostPatch stage and as part of {self.mGetOpStyle()} patching.")
                    _rc = self.mGetPluginHandler().mExacloudPluginMetadataExecutor(_node_patch_list, "post")
                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                        break

            #Clean up dbnu plugin if dbnu plugin was run
            if self.mIsDbnuPluginEnabled():
                for _dom0_to_patch in _node_patch_list:
                    self.mGetDbnuPluginHandler().mCleanupDbnuPluginsFromNode(_dom0_to_patch,PATCH_DOM0)

            if _rc != PATCH_SUCCESS_EXIT_CODE:
                _patch_failed_message = f"Patching succeeded, but error running post exacloud plugins. Return code was {str(_rc)}. Errors on screen and in logs"
                self.mPatchLogError(_patch_failed_message)

            _dom0.mDisconnect()

            # if return code of previous patch operation is non-zero,
            # we had an issue so dont do any more patching
            if _rc != PATCH_SUCCESS_EXIT_CODE:
                break

            _previous_iteration_patch_node_list = _node_patch_list[:]
        # If patchmgr not run and also no action needs to be taken, then our return code should
        # be essentially override by no action required code, otherwise, CNS code will keep on wait
        # for driver node to get the patchmgr xml report.
        if _rc == PATCH_SUCCESS_EXIT_CODE and _no_action_required == True:
            _rc = NO_ACTION_REQUIRED

        return _rc

    def mCleanupSystemImages(self):
        """
        Purges all other System first boot image file other than
        the files with the active and inactive versions.

        Return "0x00000000" -> PATCH_SUCCESS_EXIT_CODE if success,
        otherwise return error code.
        """
        _inactive_image_version = None
        _active_image_version = None
        _sys_first_boot_active_image = None
        _sys_first_boot_inactive_image = None
        _image_file_to_be_retained = []
        _system_first_boot_image_file = os.path.join(EXAVMIMAGES,"System.first.boot")
        _list_of_files_to_be_purged_string = None

        if self.mIsMockEnv():
            # in mock setup, skip rack specific operations
            return 
        '''
         Cleanup of System first boot image is performed 
         on the custom node list.
        '''
        for _dom0 in self.mGetCustomizedDom0List():
            _node = exaBoxNode(get_gcontext())

            try:
                _node.mConnect(aHost=_dom0)
                self.mPatchLogInfo(f"Cleanup of system first boot image files on {str(_dom0)} in progress.")

                _cmd_get_active_image_version = "/usr/local/bin/imageinfo -ver"
                _i, _o, _e = _node.mExecuteCmd(_cmd_get_active_image_version)
                _exit_code = int(_node.mGetCmdExitStatus())
                if int(_exit_code) == 0:
                    _o = _o.readlines()
                    _active_image_version = _o[0].strip()
                    if _active_image_version:
                        _list_of_files_to_be_purged_string = _active_image_version
                '''
                 Since purge operation is performed post upgrade and assuming backup will
                 also be in place prior to starting actual upgrade, below command is used
                 to get the inactive LVM image version details.
                '''
                additional_dbserver_cmd = ""
                # need to check if we need to pass encrypt script
                if self.mCheckConditionsForEncryptPatching() and mIsFSEncryptedNode(_node, _dom0, self):
                    additional_dbserver_cmd = " --key-api {}".format(KEY_API)

                _cmd_get_inactive_image_version = "/opt/oracle.SupportTools/dbserver_backup.sh --ignore-nfs-smbfs-mounts --check-rollback --get-backup-version {}".format(additional_dbserver_cmd)
                _i, _o, _e = _node.mExecuteCmd(_cmd_get_inactive_image_version)
                _exit_code = int(_node.mGetCmdExitStatus())
                if int(_exit_code) == 0 or int(_exit_code) == 2:
                    _inactive_image_version = (_o.readlines()[-1]).strip()
                else:
                    self.mPatchLogWarn(
                        f"Unable to fetch inactive image version on {_dom0} and the exit status is {_exit_code}, No system image file will be purged.")

                if _inactive_image_version:
                    if (_inactive_image_version.find('exasplice') != -1):
                        _inactive_image_version = _inactive_image_version.split(".exasplice.", 1)[0]
                    _list_of_files_to_be_purged_string = _list_of_files_to_be_purged_string + "|" + _inactive_image_version

                '''
                If active image version is empty or None, patch purge will be skipped.
                '''
                if _list_of_files_to_be_purged_string:
                    _cmd_purge_files = f"ls -ld {_system_first_boot_image_file}* | egrep -v '{_list_of_files_to_be_purged_string}' | /usr/bin/awk '{{print $9}}' | xargs rm -rfv"
                    _node.mExecuteCmdLog(_cmd_purge_files)

            except Exception as e:
                self.mPatchLogWarn(f'Unable to purge System first boot image files on {_dom0}. Error : {str(e)}')
                self.mPatchLogTrace(traceback.format_exc())
            finally:
                self.mPatchLogInfo(f"Cleanup of system first boot image files on {str(_dom0)} completed.")
                if _node.mIsConnected():
                    _node.mDisconnect()

    def mGetListOfDom0sWhereExasplicePatchCanBeApplied(self, aLaunchNodeCandidates, aListOfDom0s):
        """
         This method validates if exasplice can be applied
         on the current dom0 and based on the QMR version installed
         on it.

         - return the list of Dom0s where exasplice patch
           can be applied.
        """
        _list_of_dom0s_where_exasplice_can_be_applied = []
        _image_version = None
        _file_output_list = set()
        _image_version_based_on_env_type = None
        _launch_node = None
        _exception_encountered = False

        '''
         Get the list of versions from the exasplice manifest file
         from one of the launch nodes.
        '''
        _node = exaBoxNode(get_gcontext())
        '''
         At times if exasplice manifest file is not found on the 
         first launch node, we will need to search for this file
         on other launch nodes before skipping this validation.
        '''
        try:
            for _launch_node in aLaunchNodeCandidates:
                _node.mConnect(aHost=_launch_node)
                _manifest_file_name = f"exadata_exasplice_update_repos_{self.mGetTargetVersion()}.lst"
                _patch_manifest_file = os.path.join(self.__dom0_patch_base_after_unzip, _manifest_file_name)
                if _node.mFileExists(_patch_manifest_file):
                    '''
                      Sample exasplice manifest file :

                      cat exadata_exasplice_update_repos_230508.lst
                      21.2.18.0.0 baremetal
                      21.2.18.0.0 dom0
                      21.2.18.0.0 domu
                      21.2.18.0.0 kvmguest
                      21.2.18.0.0 kvmhost
                    '''
                    _i, _o, _e = _node.mExecuteCmd(f"/bin/cat {_patch_manifest_file} | sed 's/ //g'")
                    if _node.mGetCmdExitStatus() == 0:
                        _output = _o.readlines()
                        self.mPatchLogInfo(
                            f"Exasplice manifest file found on launch node : {_launch_node} and will be used to check the eligibility of dom0s for applying exasplice patch.")
                        for _version_name in _output:
                            _file_output_list.add(_version_name.strip())
                        break
                else:
                    self.mPatchLogWarn(
                        f'Exasplice patch validation cannot be performed as the exasplice manifest file : {_patch_manifest_file} is missing on Launch node : {_launch_node}')

                if _node.mIsConnected():
                    _node.mDisconnect()

        except Exception as e:
            self.mPatchLogWarn(
                f'Error in fetching the list of QMR version from the exasplice manifest file on : {str(aLaunchNodeCandidates)} . Error : {str(e)}. All the input list of Dom0s passed will be returned.')
            self.mPatchLogTrace(traceback.format_exc())
            # In case of exception encountered, return original set of Dom0s - aListOfDom0s
            return aListOfDom0s

        _exception_encountered = False
        for _dom0 in aListOfDom0s:
            try:
                _node.mConnect(aHost=_dom0)

                '''
                 Get the imageinfo details from dom0. echo <image version> is mimicking
                 imageinfo -ver command in the below example.

                   [ araghave_smr ] [ araghave_smr ] bash-4.2$ echo "22.1.13.0.0.230712.exasplice.230814" | cut -d"." -f1,2,3,4,5
                   22.1.13.0.0
                   [ araghave_smr ] [ araghave_smr ] bash-4.2$

                   [ araghave_smr ] [ araghave_smr ] bash-4.2$ echo "22.1.13.0.0.230712" | cut -d"." -f1,2,3,4,5
                   22.1.13.0.0
                   [ araghave_smr ] [ araghave_smr ] bash-4.2$
                '''
                _in, _out, _err = _node.mExecuteCmd("imageinfo -ver | cut -d'.' -f1,2,3,4,5")
                _output = _out.readlines()
                if _output:
                    _image_version = (_output[0]).strip()
               
                if _file_output_list and len(_file_output_list) > 0:
                    if self.mIsKvmEnv():
                        _image_version_based_on_env_type = _image_version + "kvmhost" 
                    else:
                        _image_version_based_on_env_type = _image_version + "dom0"

                    if str(_image_version_based_on_env_type) in _file_output_list:
                        self.mPatchLogInfo(
                            f"Image version : {str(_image_version)} of Dom0 : {str(_dom0)} found in the exasplice manifest file : {str(self.__dom0_patch_base_after_unzip)} and is eligible for exasplice patching.")
                        _list_of_dom0s_where_exasplice_can_be_applied.append(_dom0)
                    else:
                        self.mPatchLogWarn(
                            f"Image version : {str(_image_version)} was not found in the exasplice manifest file : {str(self.__dom0_patch_base_after_unzip)} and exasplice patch cannot be applied on Dom0 : {_dom0}")
            except Exception as e:
                self.mPatchLogWarn(
                    f'Error in validating exasplice patch to be applied on dom0 : {_dom0} . Error : {str(e)}. All the input list of Dom0s passed will be returned.')
                self.mPatchLogTrace(traceback.format_exc())
                _exception_encountered = True
            finally:
                if _node.mIsConnected():
                    _node.mDisconnect()
                if _exception_encountered:
                    break

        if _exception_encountered:
            '''
             In case of exception encountered on atleast one dom0s, filtered dom0 list will not have 
             the appropriate set of Dom0s. Hence initialize _list_of_dom0s_where_exasplice_can_be_applied 
             with aListOfDom0s and return all input Dom0s.
            '''
            _list_of_dom0s_where_exasplice_can_be_applied = aListOfDom0s

        return _list_of_dom0s_where_exasplice_can_be_applied

    def mDetectCDBDowntimeDuringDom0Patching(self, aDom0, aDomUList):
        """
        :param aDom0: dom0 node on which patching happens
        :param aDomUList: VM node list - contains customerhostnames
        :return: PATCH_SUCCESS_EXIT_CODE on success otherwise DOM0_PATCHING_DB_HEALTHCHECKS_DBS_ARE_DOWN or DOMU_DBAASAPI_COMMAND_FAILED

        Note:
            1. mExecuteInfraPreSanityCheck in called parallely on all the vms here
            2. For EXACS, opc user and for EXACC root user keys are injected to connect to VM nodes
        """
        _cdb_downtime_detection_vm_list = []
        _ret = PATCH_SUCCESS_EXIT_CODE
        _suggestion_msg = ""

        _user = None

        _enable_health_checks_from_cp = self.mGetInfrapatchExecutionValidator().mCheckCondition('mEnableDBHealthChecks')
        _enable_cdb_downtime_check = self.mGetInfrapatchExecutionValidator().mCheckCondition(
            'mIsCDBDowntimeCheckEnabled')

        if not self.mIsExaCC():
            _user = "opc"
        if _enable_health_checks_from_cp and _enable_cdb_downtime_check:
            try:
                def _detect_cdbdowntime_during_dom0_patching(_domu_customer_hostname, aStatus):
                    _domu_node = self.mGetDomUNatHostNameforDomuCustomerHostName(_domu_customer_hostname)
                    _rc = self.mGetCluPatchCheck().mExecuteInfraPreSanityCheck(_domu_node, aUser=_user)
                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                        _sanity_check_log_on_remote_node = f"{DBAASAPI_SANITY_CHECK_LOG_PATH}/{DBAASAPI_SANITY_CHECK_LOG}"
                        _sanity_check_log_local_path = f"{self.mGetLogPath()}/{_domu_node}_{DBAASAPI_SANITY_CHECK_LOG}"
                        self.mPatchLogInfo(
                            f"Copying {_sanity_check_log_on_remote_node} from remote node {_domu_node} to {_sanity_check_log_local_path}")
                        self.mCopyFileFromRemote(_domu_node, _sanity_check_log_on_remote_node,
                                                 _sanity_check_log_local_path, aCopytoTmp=True, aUser=_user)
                        aStatus.append({'domu': _domu_customer_hostname, 'status': 'failed', 'errorcode': _rc})
                        self.mPatchLogError(f"cdb downtime detected on {_domu_customer_hostname}")

                # End of _detect_cdbdowntime_during_dom0_patching

                """
                 Parallelize execution on all target nodes.
                """
                _plist = ProcessManager()
                _rc_status = _plist.mGetManager().list()

                for _remote_node in aDomUList:
                    _p = ProcessStructure(_detect_cdbdowntime_during_dom0_patching, [_remote_node, _rc_status],
                                          _remote_node)

                    '''
                     Timeout parameter configurable in Infrapatching.conf
                     Currently it is set to 60 minutes
                    '''
                    _p.mSetMaxExecutionTime(self.mGetDBHealthChecksParallelExecutionWaitTimeInSeconds())

                    _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
                    _p.mSetLogTimeoutFx(self.mPatchLogWarn)
                    _plist.mStartAppend(_p)

                _plist.mJoinProcess()

                if _plist.mGetStatus() == "killed":
                    _suggestion_msg = f"Timeout occured while validating for cdb downtime on the VM nodes of the dom0 {aDom0} "
                    _ret = DB_HEALTCHECKS_DETECTION_TIMEOUT_ERROR
                    self.mAddError(_ret, _suggestion_msg)
                    return _ret

                # validate the return codes
                for _rc_details in _rc_status:
                    if _rc_details['status'] == "failed":
                        _cdb_downtime_detection_vm_list.append(_rc_details['domu'])
                        _ret = _rc_details['errorcode']

                if _cdb_downtime_detection_vm_list:
                    _suggestion_msg = f"Patching {aDom0} will reboot the vms, resulting in cdb downtime on this " \
                                      f"vm list : {str(_cdb_downtime_detection_vm_list)} "

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
            self.mAddError(_ret, _suggestion_msg)

        return _ret

    def mDetectCDBDegradationDuringDom0Patching(self, aDom0, aDomUList):
        """
        :param aDom0: dom0 node on which patching happened
        :param aDomUList: VM node list - contains customerhostnames
        :return: PATCH_SUCCESS_EXIT_CODE on success otherwise DOM0_PATCHING_DB_HEALTHCHECKS_DBS_ARE_DOWN or DOMU_DBAASAPI_COMMAND_FAILED

        Note:
            1. mExecuteInfraPostSanityCheck in called parallely on all the vms here
            2. For EXACS, opc user and for EXACC root user keys are injected to connect to VM nodes
        """
        _cdb_degradation_failed_vm_list = []
        _ret = PATCH_SUCCESS_EXIT_CODE
        _suggestion_msg = ""
        _user = None

        if not self.mIsExaCC():
            _user = "opc"

        _enable_health_checks_from_cp = self.mGetInfrapatchExecutionValidator().mCheckCondition('mEnableDBHealthChecks')
        _enable_cdb_degradation_check = self.mGetInfrapatchExecutionValidator().mCheckCondition(
            'mIsCDBDegradationCheckEnabled')

        if _enable_health_checks_from_cp and _enable_cdb_degradation_check:
            try:
                def _detect_cdb_degradation_during_dom0_patching(_domu_customer_hostname, aStatus):
                    _domu_node = self.mGetDomUNatHostNameforDomuCustomerHostName(_domu_customer_hostname)
                    _rc = PATCH_SUCCESS_EXIT_CODE
                    self.mPatchLogInfo(f"CDB degradation check started on {_domu_node}.")
                    _db_healthchecks_wait_time = self.mGetDBHealthChecksWaitTimeInSeconds()
                    _starttime = time.time()
                    _elapsed = 0
                    _iteration = 0
                    _sanity_chek_log_name = f"{self.mGetLogPath()}/{_domu_node}_{DBAASAPI_SANITY_CHECK_LOG}"
                    _sanity_check_log_on_remote_node = f"{DBAASAPI_SANITY_CHECK_LOG_PATH}/{DBAASAPI_SANITY_CHECK_LOG}"
                    while _elapsed < _db_healthchecks_wait_time:
                        _iteration = _iteration + 1
                        sleep(DBHEALTHCHECK_TIMEOUT_IN_SECONDS)
                        self.mPatchLogInfo(f"**** DomU healthchecks are polled for another {DBHEALTHCHECK_TIMEOUT_IN_SECONDS} seconds and re-validated.")
                        _rc = self.mGetCluPatchCheck().mExecuteInfraPostSanityCheck(_domu_node, aUser=_user)
                        _elapsed = time.time() - _starttime
                        if _rc == PATCH_SUCCESS_EXIT_CODE:
                            self.mPatchLogInfo(
                                f"mDetectCDBDegradationDuringDom0Patching: Completed CDB healtchecks of the VM: {_domu_node}, elapsed time: {str(_elapsed)}")
                            break

                        self.mCopyFileFromRemote(_domu_node, _sanity_check_log_on_remote_node,
                                                 f"{_sanity_chek_log_name}.{_iteration:d}", aCopytoTmp=True,
                                                 aUser=_user)
                        self.mPatchLogInfo(
                            'mDetectCDBDegradationDuringDom0Patching: Waiting for completion of CDB healtchecks of the VM: {'
                            '0}, iteration {1} time elapsed: {2}'.format(_domu_node, _iteration, _elapsed))

                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                        self.mPatchLogError("CDB healthcheck has returned non zero exit status")
                        self.mPatchLogInfo(
                            f"Copying {_sanity_check_log_on_remote_node} from remote node {_domu_node} to {_sanity_chek_log_name}.{_iteration:d}")
                        self.mCopyFileFromRemote(_domu_node, _sanity_check_log_on_remote_node,
                                                 f"{_sanity_chek_log_name}.{_iteration:d}", aCopytoTmp=True,
                                                 aUser=_user)
                        aStatus.append({'domu': _domu_customer_hostname, 'status': 'failed', 'errorcode': _rc})
                        self.mPatchLogError(f"cdb degradation detected on {_domu_customer_hostname}")

                    self.mPatchLogInfo(f"CDB degradation check completed on {_domu_node}.")

                # End of _detect_cdb_degradation_during_dom0_patching

                """
                 Parallelize execution on all target nodes.
                """
                _plist = ProcessManager()
                _rc_status = _plist.mGetManager().list()

                for _remote_node in aDomUList:
                    _p = ProcessStructure(_detect_cdb_degradation_during_dom0_patching, [_remote_node, _rc_status],
                                          _remote_node)

                    '''
                     Timeout parameter configurable in Infrapatching.conf
                     Currently it is set to 60 minutes
                    '''
                    _p.mSetMaxExecutionTime(self.mGetDBHealthChecksParallelExecutionWaitTimeInSeconds())

                    _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
                    _p.mSetLogTimeoutFx(self.mPatchLogWarn)
                    _plist.mStartAppend(_p)

                _plist.mJoinProcess()

                if _plist.mGetStatus() == "killed":
                    _suggestion_msg = f"Timeout occurred while validating for cdb downtime on the VM nodes of the dom0 {aDom0} "
                    _ret = DB_HEALTCHECKS_DETECTION_TIMEOUT_ERROR
                    self.mAddError(_ret, _suggestion_msg)
                    return _ret

                # validate the return codes
                for _rc_details in _rc_status:
                    if _rc_details['status'] == "failed":
                        _cdb_degradation_failed_vm_list.append(_rc_details['domu'])
                        _ret = _rc_details['errorcode']

                if _cdb_degradation_failed_vm_list:
                    _suggestion_msg = f"CDB degradation detected on the vm list : {str(_cdb_degradation_failed_vm_list)} during {aDom0} patching"

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
            self.mAddError(_ret, _suggestion_msg)

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
        if not self.mIsExaCC():
            _user = "opc"

        _enable_health_checks_from_cp = self.mGetInfrapatchExecutionValidator().mCheckCondition('mEnableDBHealthChecks')
        _enable_pdb_downtime_check = self.mGetInfrapatchExecutionValidator().mCheckCondition(
            'mIsPDBDowntimeCheckEnabled')
        _enable_pdb_degradation_check = self.mGetInfrapatchExecutionValidator().mCheckCondition(
            'mIsPDBDegradationCheckEnabled')
        if _enable_health_checks_from_cp and (_enable_pdb_downtime_check or _enable_pdb_degradation_check):
            try:
                def _detect_pdb_downtime_during_dom0_patching(_domu_customer_hostname, aStatus):
                    _domu_node = self.mGetDomUNatHostNameforDomuCustomerHostName(_domu_customer_hostname)

                    # Fetch dbsystem details json for post patch comparison to detect if pdb is in degraded state
                    _rc = self.mGetCluPatchCheck().mFetchAndStoreDBSystemDetailsToFile(_domu_node, "pre", aUser=_user)
                    if _rc == PATCH_SUCCESS_EXIT_CODE and _enable_pdb_downtime_check:
                        self.mPatchLogInfo("PDB downtime check started.")
                        _rc = self.mGetCluPatchCheck().mDetectPDBDowntime(_domu_node, aUser=_user)
                        self.mPatchLogInfo("PDB downtime check completed.")
                    else:
                        self.mPatchLogInfo("PDB downtime check is not run as enable_pdb_downtime_check is False.")

                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                        aStatus.append({'domu': _domu_customer_hostname, 'status': 'failed', 'errorcode': _rc})
                        self.mPatchLogError(f"pdb downtime detected on {_domu_customer_hostname}")

                # End of _detect_pdb_downtime_during_dom0_patching

                """
                 Parallelize execution on all target nodes.
                """
                _plist = ProcessManager()
                _rc_status = _plist.mGetManager().list()

                for _remote_node in aDomUList:
                    _p = ProcessStructure(_detect_pdb_downtime_during_dom0_patching, [_remote_node, _rc_status],
                                          _remote_node)

                    '''
                     Timeout parameter configurable in Infrapatching.conf
                     Currently it is set to 60 minutes
                    '''
                    _p.mSetMaxExecutionTime(self.mGetDBHealthChecksParallelExecutionWaitTimeInSeconds())

                    _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
                    _p.mSetLogTimeoutFx(self.mPatchLogWarn)
                    _plist.mStartAppend(_p)

                _plist.mJoinProcess()

                if _plist.mGetStatus() == "killed":
                    _suggestion_msg = f"Timeout occured while validating for cdb downtime on the VM nodes of the dom0 {aDom0}"
                    _ret = DB_HEALTCHECKS_DETECTION_TIMEOUT_ERROR
                    self.mAddError(_ret, _suggestion_msg)
                    return _ret

                # validate the return codes
                for _rc_details in _rc_status:
                    if _rc_details['status'] == "failed":
                        _pdb_downtime_detection_vm_list.append(_rc_details['domu'])
                        _ret = _rc_details['errorcode']

                if _pdb_downtime_detection_vm_list:
                    _suggestion_msg = f"Patching {aDom0} will reboot the vms, resulting in pdb downtime on this vm list : {str(_pdb_downtime_detection_vm_list)}"
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
            self.mAddError(_ret, _suggestion_msg)

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
        if not self.mIsExaCC() :
            _user = "opc"

        _enable_health_checks_from_cp = self.mGetInfrapatchExecutionValidator().mCheckCondition('mEnableDBHealthChecks')
        _enable_pdb_degradation_check = self.mGetInfrapatchExecutionValidator().mCheckCondition(
            'mIsPDBDegradationCheckEnabled')

        if _enable_health_checks_from_cp and _enable_pdb_degradation_check:
            try:
                def _detect_pdb_degrdation_during_dom0_patching(_domu_customer_hostname, aStatus):
                    _domu_node = self.mGetDomUNatHostNameforDomuCustomerHostName(_domu_customer_hostname)
                    self.mPatchLogInfo("PDB degradation check started.")
                    _rc = self.mGetCluPatchCheck().mValidateForPDBDegradation(_domu_node, aIsRetry, aUser=_user)
                    self.mPatchLogInfo("PDB degradation check completed.")
                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                        aStatus.append({'domu': _domu_customer_hostname, 'status': 'failed', 'errorcode': _rc})
                        self.mPatchLogError(f"pdb degradation detected on {_domu_customer_hostname}")

                # End of _detect_pdb_degrdation_during_dom0_patching

                """
                 Parallelize execution on all target nodes.
                """
                _plist = ProcessManager()
                _rc_status = _plist.mGetManager().list()

                for _remote_node in aDomUList:
                    _p = ProcessStructure(_detect_pdb_degrdation_during_dom0_patching, [_remote_node, _rc_status],
                                          _remote_node)

                    '''
                     Timeout parameter configurable in Infrapatching.conf
                     Currently it is set to 60 minutes
                    '''
                    _p.mSetMaxExecutionTime(self.mGetDBHealthChecksParallelExecutionWaitTimeInSeconds())

                    _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
                    _p.mSetLogTimeoutFx(self.mPatchLogWarn)
                    _plist.mStartAppend(_p)

                _plist.mJoinProcess()

                if _plist.mGetStatus() == "killed":
                    _suggestion_msg = f"Timeout occured while validating for cdb downtime on the VM nodes of the dom0 {aDom0} "
                    _ret = DB_HEALTCHECKS_DETECTION_TIMEOUT_ERROR
                    self.mAddError(_ret, _suggestion_msg)
                    return _ret

                # validate the return codes
                for _rc_details in _rc_status:
                    if _rc_details['status'] == "failed":
                        _pdb_degradation_failed_vm_list.append(_rc_details['domu'])
                        _ret = _rc_details['errorcode']

                if _pdb_degradation_failed_vm_list:
                    _suggestion_msg = f"PDB degradation detected on the vm list : {str(_pdb_degradation_failed_vm_list)} during {aDom0} patching"

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
            self.mAddError(_ret, _suggestion_msg)

        return _ret

