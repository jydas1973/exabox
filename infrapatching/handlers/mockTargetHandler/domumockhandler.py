#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/mockTargetHandler/domumockhandler.py /main/3 2025/12/02 17:57:52 ririgoye Exp $
#
# domumockhandler.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      domumockhandler.py - Patch - DomU Basic Functionality
#    DESCRIPTION
#      Provide basic/core domU patching API (prereq, patch, backup,
#      rollback) for managing the Exadata patching in the exadata cluster
#      implementation.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    11/26/25 - Bug 38699725 - EXACLOUD - FIX PYLINT ERRORS FOR
#                           MIGRATE TO OL8 IN ECS
#    emekala     10/25/24 - ENH 37070223 - SYNC MOCK HANLDERS WITH LATEST CODE
#                           FROM CORE INFRAPATCHING HANDLERS AND ADD SUPPORT
#                           FOR CUSTOM RESPONSE AND RACK DETAILS
#    araghave    10/08/24 - Enh 36505637 - IMPROVE POLLING MECHANISM IN CASE
#                           OF INFRA PATCHING OPERATIONS
#    antamil     10/04/24 - Enh 37027134 - Modularize single vm patching code
#    sdevasek    09/25/24 - Enh 37036765 - CODE COVERAGE IMPROVEMENT - 
#                           MAKE METHOD NAME INTO SINGLE LINE
#    antamil     09/17/24 - bug 37068006: Additional fixes for single VM patching
#    araghave    09/16/24 - Enh 36971721 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE TARGET HANDLER FILES
#    emekala     08/27/24 - ENH 36748344 - USE PATCHMANAGER OBJECT IN ALL DOMU
#                           OPERATIONS
#    bhpati      08/15/24 - Bug 36881218 - AIM4ECS:0X03050003 - VM PATCH
#                           EXCEPTION DETECTED
#    emekala     08/13/24 - ENH 36679949 - REMOVE OVERHEAD OF INDEPENDENT
#                           MONITORING PROCESS FROM INFRAPATCHING
#    antamil     08/12/24 - Bug 36798372 - Change the owner of patchmgr files
#                           to opc when management host is used as launchnode
#    araghave    08/02/24 - Bug 36907132 - EXACC:BB:GRANULAR: DOM0 PRECHECK
#    antamil     08/01/24 - Bug 36881089 - Configure passwordless ssh using
#                            ssh config file on management host
#    avimonda    07/24/24 - Bug 36563684 - AIM4EXACLOUD:0X03040001 - VM PRECHECK
#                           EXCEPTION DETECTED. (23.4.1.2.1-DOMU)
#    sdevasek    07/16/24 - ENH  36820129 - IGNORE PDB DOWNTIME LOGIC ON
#                           STANDBY NODES IN DG ENV DURING DOMU PATCHING
#    sdevasek    07/03/24 - ENH 36542989  -  VERIFY PDB HELATH CHECK ACROSS
#                           CLUSTER OF THE NODES DURING DOMU PATCH TO DETECT
#                           DOWNTIME
#    diguma      06/25/24 - Bug 36727709: IMPLEMENT TFA BLACKOUT NOTIFICATION
#                           FOR DOMU VM OS PATCHING BY INFRAPATCHING TEAM
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    antamil     06/13/24 - Bug 36666801 - Replace the calls of 
#                           mGetCustomizedDomUList with filtered node list
#    araghave    06/06/24 - Enh 36628557 - DOMU OS PATCHING CHECKS TO PREVENT
#                           OUTAGE
#    sdevasek    05/15/24 - ENH 36296976 - VALIDATE FOR PDBS RUNNING STATE AND
#                           FOR PDBS IN RESTRICTED MODE DURING DOMU PATCHING
#    araghave    05/07/24 - Bug 36543876 - ERROR OUT WHEN GRID HOME PATH BINARY
#                           DOES NOT EXISTS FOR CRS AUTOSTART ENABLED CHECK
#    araghave    04/19/24 - ER 36452945 - TERMINATE INFRA PATCHING THREAD EARLY
#                           IN CASE OF PATCHMGR COMMAND DID NOT RUN
#    emekala     03/25/24 - ENH 36351481 - DISABLE COPYING OF DBNU PLUGINS
#                           DURING DOMU PATCHING
#    antamil     03/11/24 - Enh 36372221 - Code changes for single VM EXACS
#                           patching support
#    sdevasek    01/30/24 - ENH 35306246 - ADD DB HEALTH CHECKS
#                           DURING DOMU OS PATCHING
#    antamil     02/02/23 - 36109360 - Codes changes for Cps as launch node
#    antamil     12/15/23 - Bug 36111686 - Update IsCpsLaunchNodeForDomU
#                           to mIsCpsLaunchNodeForDomU 
#    antamil     12/05/23 - Fix for bug 36095866, generate keys on launch node
#    apotluri    11/21/23 - Bug 35975084 - DOM0 PRECHECK FAILS AT STALEMOUNT
#                           CHECK AND LOG SHOWS OCI ERROR DURING INSTANCE
#                           PRINCIPALS CREATION.
#                           OCICONNECTIONPOOL(HOST='AUTH.SEA.ORACLECLOUD.COM',
#                           PORT=443): MAX RETRIES EXCEEDED WITH URL: /V1/X509
#    antamil     11/17/23 - BUG 36000710 - FIX FOR CPS AS LAUNCH NODE TO USE NAT
#                           HOSTNAME
#    sdevasek    10/27/23 - BUG 35949486 - RESTORING INFRA PATCHING CHANGES
#                           DONE AS PART OF 35825510
#    emekala     09/28/23 - ENH 35545568 - STASH GUEST VM EXADATA PATCHMGR LOGS
#                           TO ADBD LOGGER LOCATION
#    antamil     09/20/23 - BUG 35752885 - ALLOW LAUNCH NODE TO BE PASSED WITH
#                           INCLUDE NODE LIST
#    sdevasek    09/19/23 - BUG 35692709 - DOM0 ROLLBACK IS EXECUTED ON
#                           DISCARDED NODE AND INFRAPATCHING OPERATION FAILS
#    ririgoye    08/23/23 - Bug 35616435 - Fix redundant/multiple instances of
#                           mConnect
#    sdevasek    08/09/23 - ENH 35687013 - CREATE AND DELETE MARKER FILE DURING
#                           PATCHING WHEN CPS IS USED AS LAUNCHNODE
#    antamil     08/03/23 - ENH 35621978 - ENABLE CPS AS LAUNCHNODE FOR
#                           DOMU PATCH OPERATION
#    diguma      08/03/23 - BUG 35639615 - fix overwrite of return code
#    jyotdas     08/01/23 - ENH 35641075 - Develop a generic framework for
#                           infrapatching api validation execution
#    araghave    07/24/23 - Enh 35629517 - RENAME ERROR CODE SPECIFIC TO CUSTOM
#                           PLUGINS
#    avimonda    07/20/23 - Bug 35443002 - Set the current target type to domu
#                           before establishing the launch node to effectively
#                           cleanup old patches.
#    sdevasek    07/19/23 - BUG 35619289 - ACTIVE/ACTIVE UPGRADE: SECURITY
#                           MAINTENANCE RUN GOT STUCK DURING ROLLING UPGRADE
#    sdevasek    06/26/23 - BUG 35509499 - AIM4EXA2.0 - BUG NOT CREATED FOR
#                           INCIDENT IN BUG 35481344
#    antamil     06/21/23   ENH 35026503 - SUPPORT TO LAUNCH MULTIPLE PATCHMGR 
#                           SESSIONS  ON THE GIVEN EXTERNAL LAUNCH NODE
#    antamil     05/17/23 - Enh 35361661 - Enable external launch node support 
#                           for precheck operation
#    diguma      04/16/23 - bug 34392890 - check connectivity of domu and if 
#                           plugin is enabled, check for plugin custom script
#    vmallu      03/17/23 - Enh 32298104 - ENABLE DBNU PLUGIN SUPPORT FOR DOMU
#    antamil     16/01/23 - BUG 34959522 = FIX FOR PATCHMGR ERROR DETAILS
#                           MISSING IN PRECHECK
#    araghave    01/13/22 - Enh 34859379 - PERFORM CRS BOUNCE BEFORE HEARTBEAT
#                           CHECK TIMEOUT, IF DOMUs ARE UNABLE TO ESTABLISH
#                           A HEART BEAT TO THE CELLS
#    sdevasek    12/02/22 - BUG 34842139 - DOM0 PATCHING FAILED AT CUSTOMCHECK
#                           AS NODE IMAGE VERSION IS HIGHER THAN TARGET VERSION
#    diguma      10/21/22 - Enh34015624: add location of exacloud plugin logs
#    araghave    10/07/22 - Enh 34623863 - PERFORM SPACE CHECK VALIDATIONS
#                           BEFORE PATCH OPERATIONS ON TARGET NODES
#    araghave    09/23/22 - Bug 34629293 - DOMU PRECHECK OPERATION FAILING AT
#                           EXACLOUD LAYER DUE TO CHECKSUM ISSUE
#    araghave    09/14/22 - Enh 34480945 - MVM IMPLEMENTATION ON INFRA PATCHING
#                           CORE FILES
#    araghave    06/09/22 - Enh 34258082 - COPY PATCHMGR AND OTHER LOGS FROM
#                           LAUNCH NODES POST PATCHING ONLY IF THE EXIT STATUS
#                           IS A FAILURE
#    sdevasek    06/07/22 - Bug 34246727 - EXACS: DOMU EXACSOSPATCH PRECHECK
#                           FAILS WITH ERROR STALE MOUNT(S) DETECTED ON DOMU
#    araghave    06/02/22 - Bug 34224203 - MODIFY ERROR HANDLING MESSAGE
#                           DETAILS AS PER TEAM REVIEW
#    araghave    05/30/22 - Enh 34225663 - SKIP BACKUP IN CASE OF A SYSTEM
#                           CONSISTENCY CHECK FAILURE AND PROCEED WITH UPGRADE
#    araghave    05/23/22 - Enh 34179923 - WHEN PATCH RETRY IS TRIGGERED FROM
#                           CP PASS NOBACKUP TO PATCHMGR BY CHECKING SYSTEM
#                           CONSISTENCY STATE
#    sdevasek    05/22/22 - ENH 33859232 - TRACK TIME PROFILE INFORMATION FOR
#                           INFRAPATCH OPERATIONS
#    araghave    04/19/22 - Enh 33516791 - EXACLOUD: DO NOT OVER WRITE THE
#                           ERROR SET BY RAISE EXCEPTION
#    araghave    04/11/22 - Enh 34048154 - ONEOFF PATCH OPERATION TO SUPPORT A
#                           PLUGIN FRAMEWORK WITH GENERIC OPTIONS
#    jyotdas     03/24/22 - ENH 33909170 - post patch check on domu failed due
#                           to crs services are down
#    nmallego    03/07/22 - Bug33811252 - Stop looking for notifications if no
#                           action required
#    araghave    12/20/21 - ENH 33689675 - ADD NEW ERROR FOR DOMU PATCHMGR
#                           FAILURE AND MARK FAIL AND SHOW
#    araghave    01/18/22 - Enh 30646084 - Require ability to specify compute
#                           nodes to include as part of Patching process
#    jyotdas     01/17/22 - ENH 33748218 - optimize to call mhasstalemounts for
#                           single node upgrade
#    nmallego    01/04/22 - ER 33453352 - Validate root file system before
#                           taking backup
#    araghave    11/23/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES
#                           FROM ERROR.PY TO INFRAPATCHERROR.PY
#    araghave    10/28/21 - Bug 33520303 - COMPARE WITH APPROPRIATE ERROR CODE
#                           DURING IDEMPOTENT PATCHMGR EXISTENCE CHECK
#    araghave    10/25/21 - Enh 33387834 - THROW APPROPRIATE ERROR MSG WHEN
#                           ONLY ONE NODE IS AVAILABLE
#    araghave    10/20/21 - Enh 33486853 - MOVE TIMEOUT AND OTHER CONSTANTS OUT
#                           OF CODE INTO CONFIG/CONSTANT FILES
#    jyotdas     09/20/21 - Enh 33290086 - stale mount check before starting
#                           dbserver patching for all nodes
#    araghave    08/02/21 - Enh 33182904 - Move all configurable parameters
#                           from constants.py to Infrapatching.conf
#    nmallego    08/12/21 - Bug33218205 - Push sleep code to inner for loop
#    araghave    07/11/21 - ENH 33099120 - INTRODUCE A SPECIFIC ERROR CODE FOR
#                           PATCHMGR CONSOLE READ TIME OUT
#    jyotdas     06/30/21 - Bug 32813015 - non-rolling patching should not run
#                           dom0domu plugin
#    araghave    04/20/21 - Bug 32397257 - Get granular error handling details
#                           for Dom0 and DomU targets
#    araghave    04/11/21 - Multiple occurances of MGETPATCHMGRXML failed with
#                           diff -w command errors
#    nmallego    03/29/21 - Bug32581076 - Retain actual error from patchmgr
#    araghave    02/16/21 - ENH 31423563 - PROVIDE A MECHANISM TO MONITOR
#                           INFRA PATCHING PROGRESS
#    nmallego    02/08/21 - Bug32433614 - Add sleep b/w compute nodes in
#                           rolling upgrade
#    araghave    02/01/21 - Bug 32120772 - EXASPLICE AND PYTHON 3 FIXES
#    araghave    01/19/21 - Bug 32395969 - MONTHLY PATCHING: FOUND FEW ISSUES
#                           WHILE TESTING AND NEED TO FIX
#    araghave    12/24/20 - Bug 32319703 - Precheck error handling fix
#    araghave    12/08/20 - Enh 31984849 - RETURN ERROR CODES TO DBCP FROM DOMU
#                           AND PLUGINS
#    nmallego    12/07/20 - Bug31982131 - Do not ignore critical h/w alert
#    nmallego    10/27/20 - Enh 32134826 - Stop patching in-case patchmgr
#                           session exist without retry/idempotent case.
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
import os, sys,logging
import traceback
from datetime import time
from time import sleep
import json
from exabox.infrapatching.handlers.mockTargetHandler.targetmockhandler import TargetMockHandler
from exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler import InfraPatchManager
from exabox.infrapatching.utils.utility import mSetFromEnv, mGetFirstDirInZip, mReadCallback, mErrorCallback, \
    mManageRPMs, mRegisterInfraPatchingHandlers, DOMU_PATCH_BASE, flocked, mChangeOwnerofDir
from exabox.infrapatching.core.clupatchmetadata import mWritePatchInitialStatesToLaunchNodes, \
    mUpdateAllPatchStatesForNode, mUpdateMetadataLaunchNode, mGetPatchStatesForNode, mUpdatePatchMetadata, \
    mGetLaunchNodeForTargetType
from exabox.ovm.clumisc import ebCluSshSetup
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.exakms.ExaKmsEndpoint import ExaKmsEndpoint
from exabox.utils.node import connect_to_host
from exabox.infrapatching.utils.utility import runInfraPatchCommandsLocally
from exabox.infrapatching.helpers.singlevmhelper import SingleVMHandler



sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))
log = logging.getLogger(__name__)

class DomUMockHandler(TargetMockHandler):

    def __init__(self, *initial_data, **kwargs):
        # invoking the __init__ of the parent class
        super(DomUMockHandler, self).__init__(*initial_data, **kwargs)
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [PATCH_DOMU], self)

        self.__domu_local_patch_zip = self.mGetDom0DomUPatchZipFile()[0]
        self.__domu_local_patch_zip2 = self.mGetDom0DomUPatchZipFile()[1]
        self.__domu_patch_zip_name = None
        self.__domu_patch_zip2_name = None
        self.__domu_patch_base = None
        self.__domu_patch_zip = None
        self.__domu_patch_base_after_unzip = None
        self.__domu_patchmgr = None
        self.__domu_patch_zip_size_mb = None
        self.__domu_patch_zip2_size_mb = None
        self.__domu_patch_necessary_space_mb = None
        self.__domu_to_patch_domus = None
        self.__domu_patchmgr_input_file = None
        self.__domus_to_patch = []
        self.__single_vm_handler = None
        self.mPrintEnvRelatedDebugStatements()

        self.__domu_patch_base_dir = DOMU_PATCH_BASE

        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsLocalHostLaunchNode'):
            self.__domu_patch_base_dir = mSetFromEnv(default= CPS_LAUNCH_NODE_PATCH_BASE,
                                                     aEnvVariable="EXACLOUD_PATCH_PAYLOAD_BASE",
                                                     aErrorOn=["/tmp", "/tmp/"])
        elif self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
            self.__domu_patch_base_dir = mSetFromEnv(default=MANAGEMENT_HOST_LAUNCH_NODE_PATCH_BASE,
                                                     aEnvVariable="EXACLOUD_PATCH_PAYLOAD_BASE",
                                                     aErrorOn=["/tmp", "/tmp/"])
        else:
            self.__domu_patch_base_dir = mSetFromEnv(default=DOMU_LAUNCH_NODE_PATCH_BASE,
                                                     aEnvVariable="EXACLOUD_PATCH_PAYLOAD_BASE",
                                                     aErrorOn=["/tmp", "/tmp/"])

    def mGetDomUPatchBaseDir(self):
        return self.__domu_patch_base_dir

    def mGetDomULocalPatchZip(self):
        return self.__domu_local_patch_zip

    def mGetDomULocalPatchZip2(self):
        return self.__domu_local_patch_zip2

    def mGetDomUPatchZipName(self):
        return self.__domu_patch_zip_name

    def mGetDomUPatchZip2Name(self):
        return self.__domu_patch_zip2_name

    def mGetDomUPatchBase(self):
        return self.__domu_patch_base

    def mGetDomUPatchZip(self):
        return self.__domu_patch_zip

    def mGetDomUPatchBaseAfterUnzip(self):
        return self.__domu_patch_base_after_unzip

    def mGetDomUPatchMgr(self):
        return self.__domu_patchmgr

    def mGetDomUPatchZipSizeMB(self):
        return self.__domu_patch_zip_size_mb

    def mGetDomUPatchZip2SizeMB(self):
        return self.__domu_patch_zip2_size_mb

    def mGetDomUPatchNecessarySpaceMB(self):
        return self.__domu_patch_necessary_space_mb

    def mGetDomUToPatchDomU(self):
        return self.__domu_to_patch_domus

    def mGetDomUPatchMgrInputFile(self):
        return self.__domu_patchmgr_input_file

    def mGetDomUsToPatch(self):
        return self.__domus_to_patch

    def mGetSingleVMHandler(self):
        return self.__single_vm_handler

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
        _patchmgr_console_file = None

        try:
            self.mPatchLogInfo(
                f"\n\n---------------> Starting {TASK_PREREQ_CHECK} on {PATCH_DOMU}s <---------------\n\n")
            # 1. Set up environment
            self.mSetEnvironment()

            if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsPatchBaseMarkerFileApplicable'):
                if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
                    _ret = self.mCreateMarkerFileInPatchBase(self.mGetDomUPatchBaseAfterUnzip(), aNode=self.mGetDomUToPatchDomU())
                else:
                    _ret = self.mCreateMarkerFileInPatchBase(self.mGetDomUPatchBaseAfterUnzip())
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    return _ret, _no_action_taken


            '''
             Perform space validations on root partition
             on DomU targets
            '''
            _ret = self.mValidateRootFsSpaceUsage()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mValidateRootFsSpaceUsage is {_ret} ")
                return _ret , _no_action_taken
            # Get customized list of nodes
            _ret, _suggestion_msg, _list_of_nodes, _discarded = self.mFilterNodesToPatch(
                self.mGetCustomizedDomUList(), PATCH_DOMU, TASK_PATCH)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            # 2. Check for idempotency
            _ret, _no_action_taken = self.mCheckIdemPotency(_discarded)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mSetPatchEnvironment in domU is {_ret} ")
                return _ret , _no_action_taken

            # Set initial Patch Status Json.
            self.mUpdatePatchProgressStatus(aNodeList=_list_of_nodes, aDiscardedNodeList=_discarded)

            # 3. Perform customcheck
            if len(_discarded) > 0:  # and aTaskType not in [self.TASK_POSTCHECK]:
                _ret = self.mCustomCheck(_discarded)
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    return _ret, _no_action_taken

            if len(_list_of_nodes) <= 0:
                self.mPatchLogInfo(f"No available {PATCH_DOMU.upper()}s to run the patchmgr. Nothing to do here.")

                # We need to populate more info about the patching operation when
                # no action is required and it requires to update ecra rack status
                # to previous status.
                _suggestion_msg = "The Rack node images are up to date, no action taken."
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
                    _ret = DOMU_STALE_MOUNT_CHECK_FAILED
                    self.mAddError(_ret, _suggestion_msg)
                    return _ret, _no_action_taken
            else:
                self.mPatchLogInfo(
                    f'enable_stale_mount_check is disabled in conf file {INFRA_PATCHING_CONF_FILE}. Hence stale mount check is skipped.')

            if self.mIsMockEnv():
                # in mock setup, skip rack specific operations
                return _ret , _no_action_taken

            # Validate and print CRS error messages in case of CRS startup failures.
            self.mGetCluPatchCheck().mCheckandRestartCRSonAllDomUWithinCluster()

            # Perform system consistency check. Also, need to raise FAIL and SHOW
            # error for this case so that customer can be involved to take
            # appropriate action.
            _is_system_valid_state, _suggestion_msg = self.mCheckSystemConsitency(_list_of_nodes)
            if not _is_system_valid_state:
                _ret = DOMU_SYSTEM_CONSISTENCY_CHECK_FAILED
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            _target_type = PATCH_DOMU

            _node_to_patch_nodes = self.__domu_to_patch_domus
            _node_to_patch_initial_node = self.mGetDomUToPatchInitialDomU()
            '''
             _nodes_to_patch_except_initial can only be the customised
             list of nodes as patch operations are required to be performed
             only on the input node provided.
            '''
            _nodes_to_patch_except_initial = list(set(_list_of_nodes) -
                                                  set([self.__domu_to_patch_domus]))
            _initial_node_list = [self.__domu_to_patch_domus]
            _cns_string = CNS_DOMU_PATCHER

            if not _node_to_patch_nodes and _node_to_patch_initial_node:
                raise self.mPatchLogError(_target_type.upper +
                                 " patching is unavailable, " + _target_type.upper +
                                 " patch files" +
                                 " were not provided at initialization")

            _callbacks = [mReadCallback, None, mErrorCallback, None]

            self.mPatchLogInfo(
                f'_node_to_patch_nodes = {_node_to_patch_nodes}, _node_to_patch_initial_node = {_node_to_patch_initial_node}')
            self.mPatchLogInfo(
                f'_nodes_to_patch_except_initial = {str(_nodes_to_patch_except_initial)}, _initial_node_list= {str(_initial_node_list)}')

            _ec_node_precheck = PATCH_SUCCESS_EXIT_CODE
            _ec_initial_node_precheck = PATCH_SUCCESS_EXIT_CODE

            # For the patchmgr command to run in background

            def _patch_precheck_node(aNode, aTargetType, aListOfNodesToPatch,
                                     aDiscardedNodeList, aPatchInitNode=False):
                _dom0Us_count = len(aListOfNodesToPatch)
                _domOUs_count_on_same_target_version = 0
                _update_msg = None
                _patchMgrObj = None
               
                """
                 Return Zero if success.
                        Non-zero in case of failure.
                """
                _exit_code = PATCH_SUCCESS_EXIT_CODE
                # Initial launch node is what it has passed, but it can change if
                # patchmgr session already exist in case of patch retry.
                _node_patcher = aNode

                self.mPatchLogInfo(f'Launch node = {aNode}, List of Nodes to work on = {str(aListOfNodesToPatch)}')

                # Update status
                if not aPatchInitNode:
                    self.mUpdatePatchStatus(True,
                                        STEP_FILTER_NODES + '_' + aTargetType + '_1')
                else:
                    self.mUpdatePatchStatus(True,
                                        STEP_FILTER_NODES + '_' + aTargetType + '_2')

                ##### TBD: check if all vms are in the cluster (heartbeat).
                for _dom0u_to_patch in aListOfNodesToPatch[:]:
                    # check if all dom[0u]s are healthy/pingable first
                    if not self.mGetCluPatchCheck().mPingNode(_dom0u_to_patch):
                        self.mPatchLogWarn(
                            f"{aTargetType.upper()} {_dom0u_to_patch} is not pingable. Discarding for precheck")
                        aListOfNodesToPatch.remove(_dom0u_to_patch)
                        continue

                    # Bug 23149472 - PATCHMGR INTERNAL ERROR PREREQ CHECK IF A NODE
                    #               IS ALREADY AT TARGET VERSION
                    #  to work around this, we will manually check to see if the
                    #  requested precheck version is already the installed version
                    #  on every node to precheck
                    if (self.mGetCluPatchCheck().mCheckTargetVersion(_dom0u_to_patch,
                                                                 aTargetType, self.mGetTargetVersion()) >= 0):
                        self.mPatchLogInfo(
                            f"{_dom0u_to_patch} is already at the requested version {self.mGetTargetVersion()} (or higher)")
                        # Remove this node from the list that we will run pre-checks
                        # with patchmgr
                        aListOfNodesToPatch.remove(_dom0u_to_patch)
                        _domOUs_count_on_same_target_version += 1
                    # if node up, check for connectivity and plugin script
                    elif (not self.mIsExaCC()) and self.mIsExacloudPluginEnabled() and self.mGetPluginHandler().mGetRunUserPluginsonDomuNode():
                        _ret = self.mGetPluginHandler().mCheckConnectivityPluginScript(
                                    _dom0u_to_patch, 
                                    self.mGetDomUCustomerNameforDomuNatHostName(_dom0u_to_patch),
                                    "domu", True)
                        if _ret != PATCH_SUCCESS_EXIT_CODE:
                            return _ret

                if (aListOfNodesToPatch and
                        ((_dom0Us_count - len(aListOfNodesToPatch)) !=
                         _domOUs_count_on_same_target_version)):
                    self.mPatchLogWarn(
                        f"Cluster is not coherent. Expected {str(_dom0Us_count)} {aTargetType.upper()}s, but got {str(len(aListOfNodesToPatch))}")

                self.mPatchLogInfo(
                    f"ebCluPatchControl._mPatchDom0UsPreChecks: _dom0Us_count = {_dom0Us_count}, aListOfNodesToPatch = {len(aListOfNodesToPatch)}, doums_count_on_same_target_version = {_domOUs_count_on_same_target_version}")

                # if we removed all of the nodes to run pre-check, because they were
                # already at the requested version just return success
                if (not aListOfNodesToPatch and
                        _dom0Us_count == _domOUs_count_on_same_target_version):
                    self.mPatchLogInfo("All the DOMUs are in the requested version. "
                              "No action required")
                    return NO_ACTION_REQUIRED

                # Return NO_ACTION_REQUIRED if no dom0Us to precheck
                # No need to check CNS at the end of cluster since no precheck is done
                if not aListOfNodesToPatch and len(aDiscardedNodeList) > 0:
                    self.mPatchLogInfo(f"List of nodes already upgraded and not considered for precheck using launch node {aNode} is {str(aDiscardedNodeList)} ")
                    return NO_ACTION_REQUIRED

                if not aPatchInitNode:
                    self.mUpdatePatchStatus(True, STEP_RUN_PATCH_DOMU)
                    _update_msg = STEP_CLEAN_ENV + '_' + PATCH_DOMU + '_1'
                else:
                    self.mUpdatePatchStatus(True, STEP_RUN_PATCH_SECOND_DOMU)
                    _update_msg = STEP_CLEAN_ENV + '_' + PATCH_DOMU + '_2'

                # create patchmgr object with bare minimum arguments
                _patchMgrObj = InfraPatchManager(aTarget=PATCH_DOMU, aOperation=TASK_PREREQ_CHECK, aPatchBaseAfterUnzip=self.__domu_patch_base_after_unzip, 
                                                 aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

                # now set the component's operation specific arguments
                _patchMgrObj.mSetIsoRepo(aIsoRepo=self.__domu_patch_zip2_name)
                _patchMgrObj.mSetTargetVersion(aTargetVersion=self.mGetTargetVersion())

                # create patchmgr nodes file
                _input_file = _patchMgrObj.mCreateNodesToBePatchedFile(aLaunchNode=aNode, aHostList=aListOfNodesToPatch)
                self.__domu_patchmgr_input_file = _input_file

                # prepare the patchmgr command for execution using the PatchManager object
                _patch_precheck_cmd = _patchMgrObj.mGetPatchMgrCmd()


                # 1.- Run pre_check
                # If there are no patchmgr sessions running, then run patchmgr command
                # In this context, PATCH_SUCCESS_EXIT_CODE infers NO_PATCHMGR Session is running.
                _patchmgr_session_exit = PATCH_SUCCESS_EXIT_CODE
                _patchmgr_active_node = None
                if self.mPerformPatchmgrExistenceCheck():
                    _patchMgrObj.mSetLaunchNode(aLaunchNode=None)
                    _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=aListOfNodesToPatch)

                    _patchmgr_session_exit, _patchmgr_active_node = _patchMgrObj.mCheckForPatchMgrSessionExistence()

                if _patchmgr_session_exit == PATCH_SUCCESS_EXIT_CODE:  # No patchmgr session found in any of the nodes, so re-execute
                    # with same launch/_node_patcher
                    # Capture time profile details
                    self.mUpdateInfrapatchingTimeStatsForUnfilledStages()
                    self.mCreateInfrapatchingTimeStatsEntry(str(aListOfNodesToPatch), "PATCH_MGR")

                    if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                        _patchMgrObj.mExecutePatchMgrCmd(_patch_precheck_cmd)
                    else:
                        # set the launch node and execute patchmgr cmd
                        _patchMgrObj.mSetLaunchNode(aLaunchNode=_node_patcher)

                        _exit_code = _patchMgrObj.mExecutePatchMgrCmd(_patch_precheck_cmd)
                        if _exit_code != PATCH_SUCCESS_EXIT_CODE:
                            return _exit_code
                else:
                    # TODO: We need to handle patch non-retry in future. Time being we are forcibly stopping.
                    if not self.mPatchRequestRetried():
                        _suggestion_msg = f"VM OS Patch session running at the moment on {_patchmgr_active_node}. Executing multiple patchmgr sessions not supported for now. Terminating current Patch Request."
                        _exit_code = PATCHMGR_DOMU_SESSION_ALREADY_EXIST
                        self.mAddError(_exit_code, _suggestion_msg)
                        return _exit_code

                    _patchMgrObj.mSetLaunchNode(aLaunchNode=_patchmgr_active_node)
                    _node_patcher = _patchmgr_active_node

                # reset the node list to make sure patchmgr cmd execution 
                # only looked at the launch node
                _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=None)
                
                # Following PatchManager api sets the patchmgr execution status into mStatusCode method
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

                    if _exit_code != PATCH_SUCCESS_EXIT_CODE:
                        if self.mGetSingleVMHandler():
                            self.mGetSingleVMHandler().mGetPatchMgrDiagFilesForSingleVM(self, _node_patcher, aListOfNodesToPatch,
                                                                                    self.mGetPatchmgrLogPathOnLaunchNode())
                        else:
                            self.mGetPatchMgrDiagFiles(_node_patcher,
                                                PATCH_DOMU,
                                                aListOfNodesToPatch,
                                                self.mGetPatchmgrLogPathOnLaunchNode())
                    else:
                        self.mPatchLogInfo(
                            "Patchmgr diag logs are not collected in case of a successful infra patch operation.")


                    # 3.- Get patchmgr pre-check logs
                    _precheck_log = None
                    if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                        _precheck_log = str(self.mGetSingleVMHandler().mGetLocalDom0FileCode(self.mGetPatchmgrLogPathOnLaunchNode()))
                        self.mGetLocalNodePatchMgrOutFiles(self.mGetPatchmgrLogPathOnLaunchNode(),
                                               _precheck_log)
                        self.mGetLocalNodePatchMgrMiscLogFiles(
                                                   self.mGetPatchmgrLogPathOnLaunchNode())

                        _cmd_list = [['rm', '-f', _input_file]]
                        runInfraPatchCommandsLocally(_cmd_list)
                        _cmd_list = [['mv', '-f', self.mGetPatchmgrLogPathOnLaunchNode(),self.mGetPatchmgrLogPathOnLaunchNode()+'_'+_node_patcher.split(".")[0]]]
                        runInfraPatchCommandsLocally(_cmd_list)
                        self.mLocalCopyLogsForADBDConsumption()
                    else:
                        _precheck_log = str(self.mGetDom0FileCode(_node_patcher,
                                               self.mGetPatchmgrLogPathOnLaunchNode()))
                        # Change the owner of patchmgr folder incase of managment host as the launch node
                        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
                            mChangeOwnerofDir(_node_patcher, self.mGetPatchmgrLogPathOnLaunchNode(), 'opc', 'opc')
              
                        self.mGetPatchMgrOutFiles(_node_patcher,
                                               self.mGetPatchmgrLogPathOnLaunchNode(),
                                               _precheck_log)
                        self.mGetPatchMgrMiscLogFiles(_node_patcher, self.mGetPatchmgrLogPathOnLaunchNode())
                        _node = exaBoxNode(get_gcontext())
                        self.mSetConnectionUser(_node)
                        _node.mConnect(aHost=_node_patcher)
                        _node.mExecuteCmdLog(f"rm -f {_input_file}")

                        # Moving log_dir to log_dir_<launch_node>, before starting another one
                        _node.mExecuteCmdLog(
                            f"mv -f {self.mGetPatchmgrLogPathOnLaunchNode()} {self.mGetPatchmgrLogPathOnLaunchNode()}_{_node_patcher.split('.')[0]}")

                        self.mCopyLogsForADBDConsumption(_node)
                        _node.mDisconnect()


                # Print all the log details at the end of log files copy.
                self.mPrintPatchmgrLogFormattedDetails()    

                # Log location is updated in mUpdateNodePatcherLogDir for proper collection of final CNS notification
                self.mUpdateNodePatcherLogDir(_node_patcher, _cns_string)

                return _exit_code
                # end of _patch_precheck_node

            # Initialize actual patchmgr location before it is renamed.
            _actual_patchmgr_log_on_launch_node = self.mGetPatchmgrLogPathOnLaunchNode()

            # update current node being used to upgrade i.e., __dom0_to_patch_dom0
            # or domu_to_patch_domus
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
                aTargetType=_target_type,
                aListOfNodesToPatch=_nodes_to_patch_except_initial,
                aDiscardedNodeList=_discarded,
                aPatchInitNode=False)
            self.mPatchLogInfo("Finished running pre-check in all the domUs except one")

            if _ec_node_precheck == EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR:
                self.mPatchLogInfo(f"Infra patching failed due to Exacloud timeout - Return code - {_ec_node_precheck}")
                _ret = _ec_node_precheck
                return _ret, _no_action_taken

            # Log location was renamed for supporting idempotency. Resetting -log_dir to
            # actual path for collecting notifications.
            self.mSetPatchmgrLogPathOnLaunchNode(_actual_patchmgr_log_on_launch_node)

            # update current node being used to upgrade i.e., to
            # __dom0_to_patch_initial_dom0  or __domu_to_patch_initial_domu
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
            if len(self.mGetExternalLaunchNode()) == 0:
                _ec_initial_node_precheck = _patch_precheck_node(
                        aNode=_node_to_patch_initial_node,
                        aTargetType=_target_type,
                        aListOfNodesToPatch=_initial_node_list,
                        aDiscardedNodeList=_discarded,
                        aPatchInitNode=True)

                # Need to capture exadata error json details
                if _ec_node_precheck == DOMU_PATCHMGR_COMMAND_FAILED and _ec_initial_node_precheck != DOMU_PATCHMGR_COMMAND_FAILED:
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
                    return _ret, _no_action_taken
                self.mPatchLogInfo("Finished running pre-check on initial domU Node.")
            else:
                _ec_initial_node_precheck = NO_ACTION_REQUIRED
            self.mPatchLogInfo("Pre-check run finished")

            # Updates POST_PATCH time for last post_patch entry
            self.mUpdateInfrapatchingTimeStatsForUnfilledStages()
            self.mCreateInfrapatchingTimeStatsEntry(str(self.mGetDomUList()), "POST_PATCH")

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

                    '''
                     In case of a DOMU_PATCHMGR_COMMAND_FAILED return from
                     mWaitForPatchMgrCmdExecutionToComplete() method atleast from one of
                     the iterations, Error code need to be preserved as
                     DOMU_PATCHMGR_COMMAND_FAILED so that the Error is a
                     FAIL_AND_SHOW and customer could take action.
                    '''
                    _suggestion_msg = f"Patch Prereq check failed on multiple Guest VMs. Refer patchmgr logs : {self.mGetPatchmgrLogPathOnLaunchNode()} on the launch Node Guest VM Launch nodes : {_node_to_patch_nodes},{_node_to_patch_initial_node} for more details."
                    if _ec_initial_node_precheck == DOMU_PATCHMGR_COMMAND_FAILED or _ec_node_precheck == DOMU_PATCHMGR_COMMAND_FAILED:
                        _ret = DOMU_PATCHMGR_COMMAND_FAILED
                    else:
                        _ret, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
                        if _child_request_error_already_exists_in_db:
                            self.mPatchLogError(_suggestion_msg)
                        else:
                            _ret = DOMU_PRECHECK_EXECUTION_FAILED_ERROR
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
            self.mPatchLogError("Exception in Running Domu PreCheck  "+str(e))
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
             
            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _suggestion_msg = "Individual patch request during precheck exception detected on VM."
                _ret = DOMU_PRECHECK_REQUEST_EXCEPTION
                self.mAddError(_ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_DOMU}s <---------------\n\n")
            self.mCleanSSHEnvSetUp(aSingleVmHandler=self.mGetSingleVMHandler())
            return _ret, _no_action_taken

    def mOneOff(self):
        """
         This method suppose to run any user script staged by user on plugin area

         Return code:
            PATCH_SUCCESS_EXIT_CODE for success
            Any other error code other than PATCH_SUCCESS_EXIT_CODE
            for failure.
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        self.mPatchLogInfo(f"\n\n---------------> Starting {TASK_ONEOFF} on {PATCH_DOMU}s <---------------\n\n")
        try:
            #Check if oneoff is enabled by the framework
            if self.mGetPluginHandler() and self.mIsOneOffPluginEnabled():
                '''
                 One off is applied only on the custom
                 node list.
                '''
                _node_list = self.mGetCustomizedDomUList()
                self.mGetPluginHandler().mSetNodeList(_node_list)
                self.mGetPluginHandler().mSetPluginTarget(PATCH_DOMU)

                #Execute oneoff plugin
                _rc = self.mGetPluginHandler().mApply()
                return _rc
            else:
                _ret = ONEOFF_APPLY_FAILED
                _suggestion_msg = TASK_ONEOFF.upper() + " plugin is unavailable for " + PATCH_DOMU.upper()
                self.mAddError(_ret, _suggestion_msg)
                raise self.mPatchLogError(TASK_ONEOFF.upper() +
                                          " plugin is unavailable for " + PATCH_DOMU.upper())
        except Exception as e:
            self.mPatchLogWarn("Exception in Running DomU OneOff Plugin  " + str(e))
            self.mPatchLogTrace(traceback.format_exc())
        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_DOMU}s <---------------\n\n")

    def mPatch(self):

        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0
        try:
            self.mPatchLogInfo(f"\n\n---------------> Starting {TASK_PATCH} on {PATCH_DOMU}s <---------------\n\n")

            #1. Set up environment
            self.mSetEnvironment()

            if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsPatchBaseMarkerFileApplicable'):
                if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
                    _ret = self.mCreateMarkerFileInPatchBase(self.mGetDomUPatchBaseAfterUnzip(), aNode=self.mGetDomUToPatchDomU())
                else:
                    _ret = self.mCreateMarkerFileInPatchBase(self.mGetDomUPatchBaseAfterUnzip())
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    return _ret, _no_action_taken

            '''
             Perform space validations on root partition
             on DomU targets
            '''
            _ret = self.mValidateRootFsSpaceUsage()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mValidateRootFsSpaceUsage is {_ret} ")
                return _ret , _no_action_taken

            _launch_nodes = [self.__domu_to_patch_domus, self.mGetDomUToPatchInitialDomU()]
            # Get customized list of nodes
            _ret, _suggestion_msg, _list_of_nodes, _discarded = self.mFilterNodesToPatch(
                self.mGetCustomizedDomUList(), PATCH_DOMU, TASK_PATCH)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            #2. Check for idempotency
            _ret, _no_action_taken = self.mCheckIdemPotency(_discarded)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mSetPatchEnvironment in domU is {_ret} ")
                return _ret , _no_action_taken

            # Set initial Patch Status Json.
            self.mUpdatePatchProgressStatus(aNodeList=_list_of_nodes, aDiscardedNodeList=_discarded)

            #3. Perform customcheck
            if len(_discarded) > 0:
                _ret = self.mCustomCheck(_discarded)
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    return _ret, _no_action_taken

            if len(_list_of_nodes) <= 0:
                self.mPatchLogInfo(f"No available {PATCH_DOMU.upper()}s to run the patchmgr. Nothing to do here.")

                # We need to populate more info about the patching operation when
                # no action is required and it requires to update ecra rack status
                # to previous status.
                _suggestion_msg = "The Rack node images are up to date, no action taken."
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
                    _ret = DOMU_STALE_MOUNT_CHECK_FAILED
                    self.mAddError(_ret, _suggestion_msg)
                    return _ret, _no_action_taken
            else:
                self.mPatchLogInfo(
                    f'enable_stale_mount_check is disabled in conf file {INFRA_PATCHING_CONF_FILE}. Hence stale mount check is skipped.')

            # 4. Perform the actual patch operation

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
            # TODO  In order to handle user installed RPMs and what not
            #        It will be better to create a configuration parameter to
            #        control those and just pass those.
            #        It may be something in its own conf file or in exabox.conf:
            #        "exadata_patch_domu_options", "exadata_patch_cell_options" etc..

            _node_to_patch_nodes = self.__domu_to_patch_domus
            _node_to_patch_initial_node = self.mGetDomUToPatchInitialDomU()
            '''
             _nodes_to_patch_except_initial can only be the customised
             list of nodes as patch operations are required to be performed
             only on the input node provided.
            '''
            _nodes_to_patch_except_initial = list(set(_list_of_nodes) -
                                                  set([self.__domu_to_patch_domus]))
            _initial_node_list = [self.__domu_to_patch_domus]

            if not _node_to_patch_nodes and _node_to_patch_initial_node:
                raise self.mPatchLogError(PATCH_DOMU.upper() +
                                 " patching is unavailable, " + PATCH_DOMU.upper() +
                                 " patch files" +
                                 " were not provided at initialization")

            self.mPatchLogInfo(
                f'_node_to_patch_nodes = {_node_to_patch_nodes}, _node_to_patch_initial_node = {_node_to_patch_initial_node}')
            self.mPatchLogInfo(
                f'_nodes_to_patch_except_initial = {str(_nodes_to_patch_except_initial)}, _initial_node_list= {str(_initial_node_list)}')

            # Update status
            self.mUpdatePatchStatus(True, STEP_FILTER_NODES + '_' + PATCH_DOMU)


            if len(_list_of_nodes) == 0:
                _no_action_taken += 1
                return NO_ACTION_REQUIRED, _no_action_taken


            _node_patcher_and_node_patch_list = \
                self._mGetNodePatchPair(_list_of_nodes, _node_to_patch_initial_node, _node_to_patch_nodes)


            # TODO: This is a one time hack. When we implement the extensible
            #       patching infrastructure which allows one to run custom
            #       pre and post patching actions by means of placing the
            #       scripts in right dirs (pre or post) in lexically ordered
            #       manner. Till then we use this. ie. remove krb5-workstation
            _rpm_ret_val = True
            try:
                if not self.mIsMockEnv():
                    for _node_patcher, _node_patch_list in _node_patcher_and_node_patch_list:
                        for _domu in _node_patch_list:
                            _rpm_ret_val = mManageRPMs(aNode=_domu, aNodeConnection=None,
                                              aRPMList=['krb5-workstation.x86_64'],
                                              aAction='remove')
            except Exception as e:
                self.mPatchLogWarn(
                    f"Exception caught while removing  krb5-workstation.x86_64 from domu. Exception is {str(e)} ")
                self.mPatchLogTrace(traceback.format_exc())

            _operationStyle = self.mGetOpStyle()
            if _operationStyle == OP_STYLE_ROLLING:
                _ret = self.mPatchRollbackDomUsRolling(
                    self.mGetBackUpMode(),
                    aNodePatcherAndPatchList=_node_patcher_and_node_patch_list,aRollback=False)
            elif _operationStyle == OP_STYLE_NON_ROLLING:
                _ret = self.mPatchRollbackDomUsNonRolling(
                    self.mGetBackUpMode(),
                    aNodePatcherAndPatchList=_node_patcher_and_node_patch_list,aRollback=False)
            else:
                _msg = f"{PATCH_DOMU.upper()} patching operation style [{_operationStyle}] not recognized or unsupported"
                self.mPatchLogError(_msg)
                raise Exception(_msg)

            if _ret == NO_ACTION_REQUIRED:
                _no_action_taken += 1
                # We need to populate more info about the patching
                # operation when no action is required and need to
                # update ecra rack status to previous status.
                _suggestion_msg =  "The Rack node images are up to date, no action taken."
                _ret = PATCH_SUCCESS_EXIT_CODE
                self.mAddError(_ret, _suggestion_msg)

            # Updates time for last post patch stage
            self.mUpdateInfrapatchingTimeStatsForUnfilledStages()
            # Capture time profile common post_patch activity done on all nodes
            self.mCreateInfrapatchingTimeStatsEntry(str(self.mGetDomUList()), "POST_PATCH")

        except Exception as e:
            self.mPatchLogError("Exception in Running Domu Patch  "+str(e))
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _suggestion_msg = "Individual patch request exception detected on VM."
                _ret = DOMU_PATCH_REQUEST_EXCEPTION
                self.mAddError(_ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_DOMU}s <---------------\n\n")
            self.mCleanSSHEnvSetUp(aSingleVmHandler=self.mGetSingleVMHandler())
            return _ret, _no_action_taken

    def mRollBack(self):

        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0
        try:
            self.mPatchLogInfo(f"\n\n---------------> Starting {TASK_ROLLBACK} on {PATCH_DOMU}s <---------------\n\n")

            # 1. Set up environment
            self.mSetEnvironment()

            if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsPatchBaseMarkerFileApplicable'):
                if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
                    _ret = self.mCreateMarkerFileInPatchBase(self.mGetDomUPatchBaseAfterUnzip(), aNode=self.mGetDomUToPatchDomU())
                else:
                    _ret = self.mCreateMarkerFileInPatchBase(self.mGetDomUPatchBaseAfterUnzip())
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    return _ret, _no_action_taken

            '''
             Perform space validations on root partition
             on DomU targets
            '''
            _ret = self.mValidateRootFsSpaceUsage()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mValidateRootFsSpaceUsage is {_ret} ")
                return _ret , _no_action_taken

            # 2. Check for idempotency
            _launch_nodes = [self.__domu_to_patch_domus, self.mGetDomUToPatchInitialDomU()]

            # Get customized list of nodes
            _ret, _suggestion_msg, _list_of_nodes, _discarded = self.mFilterNodesToPatch(
                self.mGetCustomizedDomUList(), PATCH_DOMU, TASK_ROLLBACK)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            _ret, _no_action_taken = self.mCheckIdemPotency(_discarded)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mSetPatchEnvironment in domU is {_ret} ")
                return _ret , _no_action_taken

            # Set initial Patch Status Json.
            self.mUpdatePatchProgressStatus(aNodeList=_list_of_nodes, aDiscardedNodeList=_discarded)

            # 3. Perform customcheck
            if len(_discarded) > 0:
                _ret = self.mCustomCheck(_discarded)
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    return _ret, _no_action_taken

            if len(_list_of_nodes) <= 0:
                self.mPatchLogInfo(
                    f"No available {PATCH_DOMU.upper()}s to run the patchmgr. Nothing to do here.")

                # We need to populate more info about the patching operation when
                # no action is required and it requires to update ecra rack status
                # to previous status.
                _suggestion_msg = "The Rack node images are up to date, no action taken."
                _ret = PATCH_SUCCESS_EXIT_CODE
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            # def _mPatchDom0Us(self, aTaskType, aOperationStyle, aBackupMode, aRollback):
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

            _node_to_patch_nodes = self.__domu_to_patch_domus
            _node_to_patch_initial_node = self.mGetDomUToPatchInitialDomU()
            '''
             _nodes_to_patch_except_initial can only be the customised
             list of nodes as patch operations are required to be performed
             only on the input node provided.
            '''
            _nodes_to_patch_except_initial = list(set(_list_of_nodes) -
                                                  set([self.__domu_to_patch_domus]))
            _initial_node_list = [self.__domu_to_patch_domus]

            if not _node_to_patch_nodes and _node_to_patch_initial_node:
                raise self.mPatchLogError(PATCH_DOMU.upper +
                                 " patching is unavailable, " + PATCH_DOMU.upper +
                                 " patch files" +
                                 " were not provided at initialization")

            self.mPatchLogInfo(
                f'_node_to_patch_nodes = {_node_to_patch_nodes}, _node_to_patch_initial_node = {_node_to_patch_initial_node}')
            self.mPatchLogInfo(
                f'_nodes_to_patch_except_initial = {str(_nodes_to_patch_except_initial)}, _initial_node_list= {str(_initial_node_list)}')

            # Update status
            self.mUpdatePatchStatus(True, STEP_FILTER_NODES + '_' + PATCH_DOMU)

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
                                                                 PATCH_DOMU, self.mGetTargetVersion()) < 0):
                        self.mPatchLogInfo(
                            f"{PATCH_DOMU.upper()} [{_node}] cannot be rolled back, its version is lower than the target version")
                        _dont_rollback = True
                        continue

                    # Compare rollback version and target version to see if rollback is really required
                    if self.mIsInActiveVersionGreaterThanTargetVersion(_node,PATCH_DOMU,aIsExasplicePatching = False):
                        _dont_rollback = True
                        continue

                else:  # rollback is not available, just skip it
                    if not self.mIsMockEnv():
                        self.mPatchLogInfo(f"{PATCH_DOMU} [{_node}] cannot be rolled back, rollback is not available")
                        _dont_rollback = True
                        continue
                _nodes_that_require_patching.append(_node)

            if len(_nodes_that_require_patching) == 0:
                _no_action_taken += 1
                return NO_ACTION_REQUIRED, _no_action_taken

            _node_patcher_and_node_patch_list = \
                self._mGetNodePatchPair(_nodes_that_require_patching, _node_to_patch_initial_node, _node_to_patch_nodes)
            _operationStyle = self.mGetOpStyle()
            if _operationStyle == OP_STYLE_ROLLING:
                _ret = self.mPatchRollbackDomUsRolling(
                    self.mGetBackUpMode(),
                    aNodePatcherAndPatchList=_node_patcher_and_node_patch_list,
                    aRollback=True)
            elif _operationStyle == OP_STYLE_NON_ROLLING:
                _ret = self.mPatchRollbackDomUsNonRolling(
                    self.mGetBackUpMode(),
                    aNodePatcherAndPatchList=_node_patcher_and_node_patch_list,
                    aRollback=True)
            else:
                _msg = f"{PATCH_DOMU.upper()} patching operation style [{self.mGetOpStyle()}] not recognized or unsupported"
                self.mPatchLogError(_msg)
                raise Exception(_msg)

            if _ret == NO_ACTION_REQUIRED:
                _no_action_taken += 1
                # We need to populate more info about the patching
                # operation when no action is required and need to
                # update ecra rack status to previous status.
                _suggestion_msg = "The Rack node images are up to date, no action taken."
                _ret = PATCH_SUCCESS_EXIT_CODE
                self.mAddError(_ret, _suggestion_msg)

            # Updates time for last post patch stage
            self.mUpdateInfrapatchingTimeStatsForUnfilledStages()
            # Capture time profile common post_patch activity done on all nodes
            self.mCreateInfrapatchingTimeStatsEntry(str(self.mGetDomUList()), "POST_PATCH")

        except Exception as e:
            self.mPatchLogError(f"Exception in Running Domu Rollback {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _suggestion_msg = "Individual patch request exception detected on VM."
                _ret = DOMU_PATCH_REQUEST_EXCEPTION
                self.mAddError(_ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_DOMU}s <---------------\n\n")
            self.mCleanSSHEnvSetUp(aSingleVmHandler=self.mGetSingleVMHandler())
            return _ret, _no_action_taken

    def rollback_prereq_check(self):
        pass

    def mPatchImageBackupDomUNode(self, aNode, aListOfNodesToPatch,
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
                self.mPatchLogWarn(f"{PATCH_DOMU.upper()} {_dom0u_to_patch} is not pingable.")

        if not aListOfNodesToPatch:
            _exit_code = PATCH_DOMU_IMAGE_BACKUP_ERROR_EXCEPTION
            _suggestion_msg = f"No {PATCH_DOMU.upper()}s to take image backup."
            self.mAddError(_exit_code, _suggestion_msg)
            return _exit_code

        # Update status
        if not aPatchInitNode:
            self.mUpdatePatchStatus(True,
                                    STEP_FILTER_NODES + '_' + PATCH_DOMU + '_1')
        else:
            self.mUpdatePatchStatus(True,
                                    STEP_FILTER_NODES + '_' + PATCH_DOMU + '_2')

        if not aPatchInitNode:
            self.mUpdatePatchStatus(True, STEP_RUN_PATCH_DOMU)
            _update_msg = STEP_CLEAN_ENV + '_' + PATCH_DOMU + '_1'
        else:
            self.mUpdatePatchStatus(True, STEP_RUN_PATCH_SECOND_DOMU)
            _update_msg = STEP_CLEAN_ENV + '_' + PATCH_DOMU + '_2'


        # create patchmgr object with bare minimum arguments
        _patchMgrObj = InfraPatchManager(aTarget=PATCH_DOMU, aOperation=TASK_BACKUP_IMAGE, aPatchBaseAfterUnzip=self.__domu_patch_base_after_unzip, 
                                         aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

        # create patchmgr nodes file
        _input_file = _patchMgrObj.mCreateNodesToBePatchedFile(aLaunchNode=_node_patcher, aHostList=aListOfNodesToPatch)
        self.__domu_patchmgr_input_file = _input_file

        # prepare the patchmgr command for execution using the PatchManager object
        _patch_backup_cmd = _patchMgrObj.mGetPatchMgrCmd()

        # If there are no patchmgr sessions running, then run patchmgr command
        # In this context, PATCH_SUCCESS_EXIT_CODE infers NO_PATCHMGR Session is running.
        _patchmgr_session_exit = PATCH_SUCCESS_EXIT_CODE
        _patchmgr_active_node = None
        if self.mPerformPatchmgrExistenceCheck():
            _patchMgrObj.mSetLaunchNode(aLaunchNode=None)
            _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=self.mGetCustomizedDomUList())

            _patchmgr_session_exit, _patchmgr_active_node = _patchMgrObj.mCheckForPatchMgrSessionExistence()

        if _patchmgr_session_exit == PATCH_SUCCESS_EXIT_CODE:  # No patchmgr session found in any of the nodes, so re-execute
            # with same launch/_node_patcher
            # set the launch node and execute patchmgr cmd
            _patchMgrObj.mSetLaunchNode(aLaunchNode=_node_patcher)

            _exit_code = _patchMgrObj.mExecutePatchMgrCmd(_patch_backup_cmd)
            if _exit_code != PATCH_SUCCESS_EXIT_CODE:
                return _exit_code
        else:
            # TODO: We need to handle patch non-retry in future. Time being we are forcibly stopping.
            if not self.mPatchRequestRetried():
                _suggestion_msg = f"VM OS Patch session running at the moment on {_patchmgr_active_node}. Executing multiple patchmgr sessions not supported for now. Terminating current Patch Request."
                _exit_code = PATCHMGR_DOMU_SESSION_ALREADY_EXIST
                self.mAddError(_exit_code, _suggestion_msg)
                return _exit_code

            # Already patchmgr is running, just monitor patchmgr console on the node.
            _patchMgrObj.mSetLaunchNode(aLaunchNode=_patchmgr_active_node)
            _node_patcher = _patchmgr_active_node

        # reset the node list to make sure patchmgr cmd execution 
        # only looked at the launch node
        _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=None)
        
        # Following PatchManager api sets the patchmgr execution status into mStatusCode method
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
                                           PATCH_DOMU,
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
                f"\n\n---------------> Starting {TASK_BACKUP_IMAGE} on {PATCH_DOMU}s <---------------\n\n")
            # 1. Set up environment
            self.mSetEnvironment()

            '''
             Perform space validations on root partition
             on DomU targets
            '''
            _ret = self.mValidateRootFsSpaceUsage()
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mValidateRootFsSpaceUsage is {_ret} ")
                return _ret , _no_action_taken

            _launch_nodes = [self.__domu_to_patch_domus, self.mGetDomUToPatchInitialDomU()]
            # Get customized list of nodes
            _ret, _suggestion_msg, _list_of_nodes, _discarded = self.mFilterNodesToPatch(
                self.mGetCustomizedDomUList(), PATCH_DOMU, TASK_PATCH)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            # 2. Check for idempotency
            _ret, _no_action_taken = self.mCheckIdemPotency(_discarded)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mSetPatchEnvironment in domU is {_ret} ")
                return _ret , _no_action_taken

            # Set initial Patch Status Json.
            self.mUpdatePatchProgressStatus(aNodeList=_list_of_nodes, aDiscardedNodeList=_discarded)

            # 3. Perform customcheck
            if len(_discarded) > 0:
                _ret = self.mCustomCheck(_discarded)
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    return _ret, _no_action_taken

            if len(_list_of_nodes) <= 0:
                self.mPatchLogInfo(f"No available {PATCH_DOMU.upper()}s to run the patchmgr. Nothing to do here.")

                # We need to populate more info about the patching operation when
                # no action is required and it requires to update ecra rack status
                # to previous status.
                _suggestion_msg = "The Rack node images are up to date, no action taken."
                _ret = PATCH_SUCCESS_EXIT_CODE
                self.mAddError(_ret, _suggestion_msg) 
                return _ret, _no_action_taken

            # Perform system consistency check. Also, need to raise FAIL_AND_SHOW
            # error for this case so that customer can be involved to take
            # appropriate action.
            _is_system_valid_state, _suggestion_msg = self.mCheckSystemConsitency(_list_of_nodes)
            if not _is_system_valid_state:
                _ret = DOMU_SYSTEM_CONSISTENCY_CHECK_FAILED
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            # Bug27643008 - Enhance to support image backup
            _node_to_patch_nodes = self.__domu_to_patch_domus
            _node_to_patch_initial_node = self.mGetDomUToPatchInitialDomU()
            '''
             _nodes_to_patch_except_initial can only be the customised
             list of nodes as patch operations are required to be performed
             only on the input node provided.
            '''
            _nodes_to_patch_except_initial = list(set(self.mGetCustomizedDomUList()) -
                                                  set([self.__domu_to_patch_domus]))
            _initial_node_list = [self.__domu_to_patch_domus]
            _cns_string = CNS_DOMU_PATCHER
            self.mSetCallBacks([mReadCallback, None, mErrorCallback, None])

            self.mPatchLogInfo(
                f'_node_to_patch_nodes = {_node_to_patch_nodes}, _node_to_patch_initial_node = {_node_to_patch_initial_node}')
            self.mPatchLogInfo(
                f'_nodes_to_patch_except_initial = {str(_nodes_to_patch_except_initial)}, _initial_node_list= {str(_initial_node_list)}')

            _ec_node_backup = PATCH_SUCCESS_EXIT_CODE
            _ec_initial_node_backup = PATCH_SUCCESS_EXIT_CODE

            # Initialize actual patchmgr location before it is renamed.
            _actual_patchmgr_log_on_launch_node = self.mGetPatchmgrLogPathOnLaunchNode()

            # update current node being used to upgrade i.e., __dom0_to_patch_dom0
            # or domu_to_patch_domus
            _node_patch_progress = os.path.join(self.mGetLogPath(), _cns_string)
            try:
                with open(_node_patch_progress, "w") as write_nodestat:
                    write_nodestat.write(f"{_node_to_patch_nodes}:{self.mGetPatchmgrLogPathOnLaunchNode()}")
            except Exception as e:
                self.mPatchLogWarn(f'Failed to write {_node_patch_progress}: {str(e)}')
                self.mPatchLogTrace(traceback.format_exc())

            # Run the image backup in all the dom[0U]s except one
            _ec_node_backup = self.mPatchImageBackupDomUNode(
                aNode=_node_to_patch_nodes,
                aListOfNodesToPatch=_nodes_to_patch_except_initial,
                aCnsString=_cns_string,
                aPatchInitNode=False)

            if _ec_node_backup == EXADATA_PATCHMGR_CONSOLE_READ_TIMEOUT_ERROR:
                self.mPatchLogInfo(f"Infra patching failed due to Exacloud timeout - Return code - {_ec_node_backup}")
                return _ec_node_backup, _no_action_taken
   
            '''
             Extract and post notification (CNS), if anything left out on
             __domu_to_patch_domu, before it moves to __domu_to_patch_initial_domu
             __domu_to_patch_initial_domu (self.mGetDomUToPatchInitialDomU())

             In case of NO_ACTION_REQUIRED, patchmgr will not be run and inturn
             notification files will not be generated and collected.
            '''
            # Log location was renamed for supporting idempotency. Resetting -log_dir to
            # actual path for collecting notifications.
            self.mSetPatchmgrLogPathOnLaunchNode(_actual_patchmgr_log_on_launch_node)

            # update current node being used to upgrade i.e., to
            # __dom0_to_patch_initial_dom0  or __domu_to_patch_initial_domu
            try:
                with open(_node_patch_progress, "w") as write_nodestat:
                    write_nodestat.write(f"{_node_to_patch_initial_node}:{self.mGetPatchmgrLogPathOnLaunchNode()}")
            except Exception as e:
                self.mPatchLogWarn(f'Failed to write {_node_patch_progress}: {str(e)}')
                self.mPatchLogTrace(traceback.format_exc())

            # Run the image backup in the initial dom[0U]s
            _ec_initial_node_backup = self.mPatchImageBackupDomUNode(
                aNode=_node_to_patch_initial_node,
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
                self.mPatchLogInfo("In scenario where one of the Backup failed")
                if (_ec_initial_node_backup != PATCH_SUCCESS_EXIT_CODE and _ec_node_backup != PATCH_SUCCESS_EXIT_CODE):

                    '''
                     In case of a DOMU_PATCHMGR_COMMAND_FAILED return from
                     mWaitForPatchMgrCmdExecutionToComplete() method atleast from one of 
                     the iterations, Error code need to be preserved as 
                     DOMU_PATCHMGR_COMMAND_FAILED so that the Error is a 
                     FAIL_AND_SHOW and customer could take action.
                    '''
                    if _ec_initial_node_backup == DOMU_PATCHMGR_COMMAND_FAILED or _ec_node_backup == DOMU_PATCHMGR_COMMAND_FAILED:
                        _ret = DOMU_PATCHMGR_COMMAND_FAILED
                    else:
                        _ret = DOMU_BACKUP_EXECUTION_FAILED_ERROR

                    _suggestion_msg = f"Patch Backup check failed on multiple VMs. Refer patchmgr logs : {self.mGetPatchmgrLogPathOnLaunchNode()} on the Patch driving Guest VM Launch nodes : {_node_to_patch_nodes},{_node_to_patch_initial_node} for more details."
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
            self.mPatchLogError("Exception in Running Domu Image Backup  "+str(e))
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _suggestion_msg = "Individual patch request exception detected during backup on VM."
                _ret = DOMU_BACKUP_REQUEST_EXCEPTION
                self.mAddError(_ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_DOMU}s <---------------\n\n")
            self.mCleanSSHEnvSetUp(aSingleVmHandler=self.mGetSingleVMHandler())
            return _ret, _no_action_taken


    def mPostCheck(self):

        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0
        try:
            self.mPatchLogInfo(f"\n\n---------------> Starting {TASK_PATCH} on {PATCH_DOMU}s <---------------\n\n")
            # 1. Set up environment
            self.mSetEnvironment()
            _launch_nodes = [self.__domu_to_patch_domus, self.mGetDomUToPatchInitialDomU()]
            # Get customized list of nodes
            _ret, _suggestion_msg, _list_of_nodes, _discarded = self.mFilterNodesToPatch(
            self.mGetCustomizedDomUList(), PATCH_DOMU, TASK_PATCH)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            # 2. Check for idempotency
            _ret, _no_action_taken = self.mCheckIdemPotency(_discarded)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mSetPatchEnvironment in domU is {_ret} ")
                return _ret , _no_action_taken

            if len(_list_of_nodes) <= 0:
                self.mPatchLogInfo(f"No available {PATCH_DOMU.upper()}s to run the patchmgr. Nothing to do here.")

                # We need to populate more info about the patching operation when
                # no action is required and it requires to update ecra rack status
                # to previous status.
                _suggestion_msg =  "The Rack node images are up to date, no action taken."
                _ret = PATCH_SUCCESS_EXIT_CODE
                self.mAddError(_ret, _suggestion_msg)
                return _ret, _no_action_taken

            # DomU Independent Postchecks
            _ret = self.mCustomCheck(self.mGetCustomizedDomUList())

        except Exception as e:
            self.mPatchLogError("Exception in Running Domu PostCheck  "+str(e))
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _suggestion_msg = "Individual patch request exception detected during postcheck on VM."
                _ret = DOMU_POSTCHECK_REQUEST_EXCEPTION
                self.mAddError(_ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_DOMU}s <---------------\n\n")
            self.mCleanSSHEnvSetUp(aSingleVmHandler=self.mGetSingleVMHandler())
            return _ret, _no_action_taken


    # Sets the base envrionment for all tasks in domu
    def mSetEnvironment(self):
        #Sets all the variables used to select the domu that will run the patchmgr.

        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsSingleDomUVMCluster'):
            self.__single_vm_handler = SingleVMHandler(is_exacc = self.mIsExaCC())
        else:
            self.__single_vm_handler = None
          

        # Check for KVM or OVM
        if self.mIsKvmEnv():
            self.mPatchLogInfo("mSetEnvironment: KVM environment")
        else:
            self.mPatchLogInfo("mSetEnvironment: Not KVM environment")

        # Set target version based on the patch tar file version name.
        self.mSetTargetVersion(self.mGetDomULocalPatchZip2().split("/")[-1].split("_")[2])

        if self.__domu_local_patch_zip and self.__domu_local_patch_zip2:
            self.mPatchLogInfo(f"Domu local patch zip file name {self.__domu_local_patch_zip}")
            self.mPatchLogInfo(f"Domu local patch zip-2 file name {self.__domu_local_patch_zip2}")

            _no_action_taken = 0
            # Domu patching needs 2 zip files. first one has the patchmgr,
            # second one is the actual patch
            self.__domu_patch_zip_name = \
                self.__domu_local_patch_zip.split("/")[-1]
            self.__domu_patch_zip2_name = \
                self.__domu_local_patch_zip2.split("/")[-1]
            # self.__domu_patch_base = PATCH_BASE + \
            #                          self.__domu_patch_zip_name + "_" + \
            #                          self.__domu_patch_zip2_name + "/"
            self.__domu_patch_base = self.__domu_patch_base_dir + \
                                     self.__domu_patch_zip_name + "_" + \
                                     self.__domu_patch_zip2_name + "/"
            self.__domu_patch_zip = self.__domu_patch_base + \
                                    self.__domu_patch_zip_name
            self.__domu_patch_base_after_unzip = (self.__domu_patch_base +
                                                  mGetFirstDirInZip(self.__domu_local_patch_zip))
            self.__domu_patchmgr = self.__domu_patch_base_after_unzip + \
                                   "patchmgr"
            self.__domu_patch_zip_size_mb = \
                int(os.path.getsize(self.__domu_local_patch_zip)) >> 20
            self.__domu_patch_zip2_size_mb = \
                int(os.path.getsize(self.__domu_local_patch_zip2)) >> 20
            self.__domu_patch_necessary_space_mb = \
                (self.__domu_patch_zip_size_mb + \
                 self.__domu_patch_zip2_size_mb + \
                 self.mGetExadataPatchWorkingSpaceMB())

            # Set current patch. Information necessary to update status in db
            self.mSetCurrentTargetType(PATCH_DOMU)

            _launchNodes = self.mSetLaunchNodeToPatchOtherDomuNodes()

            try:
                self.__domu_to_patch_domus = _launchNodes[0]
                self.mSetDomUToPatchInitialDomU(_launchNodes[1])
            except IndexError:
                pass

            self.mSetPatchmgrLogPathOnLaunchNode(
                self.__domu_patch_base_after_unzip + "patchmgr_log_" + self.mGetMasterReqId())

            # List of launch nodes to update patch state metadata
            _launch_nodes = []

            # Add to executed targets
            self.mGetExecutedTargets().append(PATCH_DOMU)
            # Update status
            self.mUpdatePatchStatus(True, STEP_PREP_ENV)

            '''
             In this case, for _nodes_to_patch_except_initial All nodes from
             xml need to be considered as passwdless ssh is required to be setup
             on all nodes and are used during ssh validation, patchmgr existence
             check and for performing a few config changes during CNS monitor start.
            '''
            _nodes_to_patch_except_initial = list(
                set(self.mGetCustomizedDomUList()) - set([self.__domu_to_patch_domus]))
            _initial_node_list = [self.__domu_to_patch_domus]
            _initial_node = self.__domu_to_patch_domus
            _next_node = self.mGetDomUToPatchInitialDomU()
            '''
            When a single launch node is passed mGetDomUToPatchInitialDomU()
            will be None, we need to handle with the following code
            '''
            _launch_nodes = [self.__domu_to_patch_domus]
            if _next_node:
                _launch_nodes.append(_next_node)

            self.mSetPatchStatesBaseDir(os.path.join(self.__domu_patch_base_after_unzip, "patch_states_data"))
            self.mSetMetadataJsonFile(os.path.join(self.mGetPatchStatesBaseDir(),
                                                   self.mGetMasterReqId() + "_patch_progress_report.json"))
            self.mPatchLogInfo(f"Patch metadata file = {self.mGetMetadataJsonFile()}")

            # Exacloud Plugin already initialized at this stage and available in mGetPluginHandler
            # Plugins directory set below by pluginhandler if exacloud plugin is enabled
            if self.mIsExacloudPluginEnabled():
                self.mGetPluginHandler().mSetPluginsLogPathOnLaunchNode(
                    self.__domu_patch_base_after_unzip + "plugins_log_" + self.mGetMasterReqId())

            if self.mIsMockEnv():
                # in mock setup, skip rack specific operations
                return

            if  not self.mPatchRequestRetried():
                if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                    _cmd_list = []
                    _cmd_list.append(['mkdir', '-p', self.mGetPatchStatesBaseDir()])
                    runInfraPatchCommandsLocally(_cmd_list)
                else:
                    self.mCreateDirOnNodes(_launch_nodes, self.mGetPatchStatesBaseDir())
                if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
                    mWritePatchInitialStatesToLaunchNodes(PATCH_DOMU, self.mGetCustomizedDomUList(),
                                                        _launch_nodes, self.mGetMetadataJsonFile(), aUser='opc')
                else:
                    mWritePatchInitialStatesToLaunchNodes(PATCH_DOMU, self.mGetCustomizedDomUList(),
                                                        _launch_nodes, self.mGetMetadataJsonFile())


            # Rotate SSH Keys
            _all_node = []
            if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
                _all_nodes = _nodes_to_patch_except_initial
            else:
                _all_nodes = _initial_node_list + _nodes_to_patch_except_initial
            _exakmsEndpoint = ExaKmsEndpoint(None)

            for _node in _all_nodes:
                if _node:
                    self.mPatchLogInfo(f"Node name: {_node}")
                    _exakmsEndpoint.mSingleRotateKey(_node)


            # In case of single launch node, _next_node will be None, because only one launch node
            # has been passed
            # set ssh keys from node patchers to the nodes they will be patching
            _ssh_env_setup = ebCluSshSetup(self.mGetCluControl())
            _nat_domu_node_list = []
            _src_node_list = []
            _remote_node_list = []
            if self.mGetSingleVMHandler():
                self.mGetSingleVMHandler().mConfigureSSHForSingleVM(_initial_node, _nodes_to_patch_except_initial,
                                                                    _ssh_env_setup, self)
            else:
                _ssh_env_setup.mSetSSHPasswordless(_initial_node, _nodes_to_patch_except_initial)
            # Store these in memory for clearing after each operation

            _src_node_list = [_initial_node]
            _remote_node_list = [_nodes_to_patch_except_initial]
            #
            # Configure ssh only if the second launch node is being selected or passed
            #
            if _next_node:
                _ssh_env_setup.mSetSSHPasswordless(_next_node, _initial_node_list)
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

        # Set collect time stats flag
        self.mSetCollectTimeStatsFlag(self.mGetCollectTimeStatsParam(PATCH_DOMU))
        self.mPatchLogInfo("Finished Setting up Base Environment")

    def mCheckIdemPotency(self, aDiscarded):

        _ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0
        _patchMgrObj = None

        '''
         - Restore ATP setting prior to DomU operations.

         - ATP settings will be backed up and restored 
           only on the custom node list.
        '''
        _domu_list = self.mGetCustomizedDomUList()
        if not self.mSetExaccAtpSettingsOnDomU(_domu_list, "prepatch"):
            _suggestion_msg = f"Unable to set system attributes on the Guest VM List : {str(_domu_list)}, specific to ADB-C@C environments during Guest VM OS Patch operation. Verify ipv4.conf.eth0.rp_filter parameter in sysctl.conf before re-trying patch."
            _rc = UNABLE_TO_SET_SYSTEM_ATTRIBUTES_ATP_ENV
            self.mAddError(_rc, _suggestion_msg)
            return _rc
        '''
        When a single launch node is passed mGetDomUToPatchInitialDomU()
        will be None, we need to handle with the following code
        '''
        _launch_nodes = [self.__domu_to_patch_domus]
        if self.mGetDomUToPatchInitialDomU():
            _launch_nodes.append(self.mGetDomUToPatchInitialDomU())
        self.mPatchLogInfo(f"LaunchNodes = {str(_launch_nodes)}")

        # create a local patchmgr object with bare minimum arguments to make sure the _patchMgrObj attributes are local for this check only
        _patchMgrObj = InfraPatchManager(aTarget=PATCH_DOMU, aOperation=self.mGetTask(), aPatchBaseAfterUnzip=self.__domu_patch_base_after_unzip, 
                                         aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

        # check if any patchmgr session running around in the patch retry and
        # if so, let's wait for it.
        if self.mPatchRequestRetried():
            _p_ses_exist = PATCH_SUCCESS_EXIT_CODE
            _p_active_node = None
            if self.mPerformPatchmgrExistenceCheck():
                # check for patchmgr session existence
                _patchMgrObj.mSetLaunchNode(aLaunchNode=None)
                _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=self.mGetCustomizedDomUList())

                _p_ses_exist, _p_active_node = _patchMgrObj.mCheckForPatchMgrSessionExistence()

            # Wait for patchmgr to complete
            if _p_ses_exist == PATCHMGR_DOMU_SESSION_ALREADY_EXIST:
                # reset the node list to make sure patchmgr cmd execution 
                # only looked at the launch node
                _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=None)
                _patchMgrObj.mSetLaunchNode(aLaunchNode=_p_active_node)

                _patchMgrObj.mWaitForPatchMgrCmdExecutionToComplete()

                self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")
                
                _ret = _patchMgrObj.mGetStatusCode()
                if _ret == PATCH_SUCCESS_EXIT_CODE:
                    self.mPatchLogInfo("Patch manager session found and completed successfully in patch retry")
                else:
                    _suggestion_msg = f"Patch manager on {_p_active_node} failed during patch retry. Exit code = {_ret}. Refer patchmgr logs : {self.mGetPatchmgrLogPathOnLaunchNode()} on the Patch driving Guest VM : {_p_active_node} for more details."
                    _ret = PATCH_DOMU_RETRY_FAILED
                    self.mAddError(_ret, _suggestion_msg)
                    return _ret, _no_action_taken

        if self.mGetTask() not in [TASK_ROLLBACK,TASK_PATCH]:
            return _ret, _no_action_taken

        #Below checks for idempotency are done only for patch ot rollback operations
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
                    if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
                        mUpdateAllPatchStatesForNode(_launch_nodes, _n, self.mGetMetadataJsonFile(), PATCH_COMPLETED, \
                                                     aUser='opc')
                    else:
                        mUpdateAllPatchStatesForNode(_launch_nodes, _n, self.mGetMetadataJsonFile(), PATCH_COMPLETED)

            elif self.mPatchRequestRetried():
                # Verify last attempted patchmgr and resume if required.
                for _n in aDiscarded:
                    _read_patch_state = None
                    _read_patch_state = self.mGetDomUPatchStatesForNode(_launch_nodes, self.mGetMetadataJsonFile(), _n,
                                                                   PATCH_MGR)
                    if _read_patch_state == PATCH_RUNNING:
                        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
                            _active_launch_node = mGetLaunchNodeForTargetType(_launch_nodes,
                                                                              self.mGetMetadataJsonFile(),
                                                                              PATCH_DOMU,
                                                                              aUser ='opc')
                        else:
                            _active_launch_node = mGetLaunchNodeForTargetType(_launch_nodes, self.mGetMetadataJsonFile(),
                                                                              PATCH_DOMU)
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

                        # Check for the PatchmgrConsole.out presence in patcmgr_log_before_completion
                        # ( /u02/dbserver.patch.zip_exadata_ol7_22.1.10.0.0.230422_Linux-x86-64.zip/dbserver_patch_221130/patchmgr_log_b75f885d-74c0-4979-8219-506d909aff6a)
                        _patchmgr_console_file_before_patchmgr_completion = _patchMgrObj.mGetPatchMgrConsoleOutputFile()
                        _patchmgr_console_file_before_patchmgr_completion_found, _ = self.mCheckFileExistsOnRemoteNodes([_active_launch_node], _patchmgr_console_file_before_patchmgr_completion)

                        if _patchmgr_console_file_before_patchmgr_completion_found:
                            _patchmgr_log_directory_to_check = self.mGetPatchmgrLogPathOnLaunchNode()
                        else:
                            # Check for PatchmgrConsole.out presence in patchmgr_log_after_completion
                            # ( /u02/dbserver.patch.zip_exadata_ol7_22.1.10.0.0.230422_Linux-x86-64.zip/dbserver_patch_221130/patchmgr_log_b75f885d-74c0-4979-8219-506d909aff6a_slcs27dv0405m)
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
                            self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _n,
                                                 self.mGetMetadataJsonFile(), PATCH_MGR, PATCH_COMPLETED,aLaunchNode=_active_launch_node)
                        else:
                            # reset the node list to make sure patchmgr cmd execution 
                            # only looked at the launch node
                            _patchMgrObj.mSetLogPathOnLaunchNode(aLogPathOnLaunchNode=_patchmgr_log_directory_to_check)
                            _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=None)
                            _patchMgrObj.mSetLaunchNode(aLaunchNode=_active_launch_node)

                            _patchMgrObj.mWaitForPatchMgrCmdExecutionToComplete()

                            self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")
                    
                            _ret = _patchMgrObj.mGetStatusCode()
                            if _ret == PATCH_SUCCESS_EXIT_CODE:
                                self.mPatchLogInfo("Patch manager success during patch retry")
                                self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _n,
                                                     self.mGetMetadataJsonFile(), PATCH_MGR, PATCH_COMPLETED,aLaunchNode=_active_launch_node)
                            else:
                                self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _n,
                                                     self.mGetMetadataJsonFile(), PATCH_MGR, PATCH_FAILED,aLaunchNode=_active_launch_node)
                                _suggestion_msg = f"PatchMgr failed on {_n} during patch retry. Exit code = {_ret}. Refer patchmgr logs : {self.mGetPatchmgrLogPathOnLaunchNode()} on the Patch driving VMs : {str(_launch_nodes)} for more details."
                                _ret = PATCH_DOMU_RETRY_FAILED
                                self.mAddError(_ret, _suggestion_msg)
                                return _ret, _no_action_taken

                # Verify last attempted post plugins and resume if required.
                _read_patch_state = ""
                if self.mIsExacloudPluginEnabled():
                    self.mPatchLogInfo(f"Exacloud Plugin Enabled. Launch nodes = {_launch_nodes}")
                    for _n in aDiscarded:
                        self.mPatchLogInfo(f"Getting post patch status on node {_n}.")
                        try:
                            _read_patch_state = self.mGetDomUPatchStatesForNode(_launch_nodes, self.mGetMetadataJsonFile(),
                                                                   _n, POST_PATCH)
                            self.mPatchLogInfo(f"Post plugin patch status: {_read_patch_state}")
                        except Exception as e:
                            self.mPatchLogWarn(f'Failed to get the post patch state on {str(_launch_nodes)}: {str(e)}')
                            self.mPatchLogTrace(traceback.format_exc())

                        if not _read_patch_state:
                            _pluginLog = self.mGetPluginHandler().mGetPluginsLogPathOnLaunchNode()
                            _suggestion_msg = f"Invalid post plugin state found during patch = {_read_patch_state}. Refer plugin logs on launch Node VMs : {str(_launch_nodes)} for more details ({_pluginLog})."
                            # Do not overwrite the error code from mApply
                            ret, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
                            if _child_request_error_already_exists_in_db:
                                self.mPatchLogError(_suggestion_msg)
                            else:
                                ret = POST_PLUGIN_FAILED_DOMU
                                self.mAddError(ret, _suggestion_msg)

                            return ret, _no_action_taken

                        if _read_patch_state in [PATCH_PENDING, PATCH_RUNNING]:
                            _rollback_operation = False
                            if _taskType == TASK_ROLLBACK:
                                _rollback_operation = True

                            _ret = self.mGetPluginHandler().mApply(_n, PATCH_DOMU, POST_PATCH,
                                                                   _rollback_operation)
                            if _ret != PATCH_SUCCESS_EXIT_CODE:
                                self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _n,
                                                     self.mGetMetadataJsonFile(), POST_PATCH, PATCH_FAILED)
                                return _ret, _no_action_taken

                            self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _n,
                                                 self.mGetMetadataJsonFile(), POST_PATCH, PATCH_COMPLETED)

        self.mPatchLogInfo("Finished Check for IdemPotency in Patch Manager session")
        return _ret, _no_action_taken


    def mCustomCheck(self,aNodes=None):
        """
         This method performs a post checks independently on
         all of the Exadata targets like Dom0, DomU,IbSwitches
         and cells.

         Return value :
          PATCH_SUCCESS_EXIT_CODE -> if post check is success
          Hex error code other than PATCH_SUCCESS_EXIT_CODE -> if post check fails
        """

        _post_patch_failed_nodes = []
        _node_prepatch_version = {}
        _ret = PATCH_SUCCESS_EXIT_CODE

        if self.mIsMockEnv():
            # in mock setup, skip rack specific operations
            return _ret

        '''
         DomU Independent Postchecks.
         aPrePatchVersion and aPostPatchTargetVersion are the image versions 
         before and after patches respectively. They do not have any 
         significance in case of running an independent post check, but they
         are only passed as they are mandatory arguments.
        '''

        _domU_listed_by_xm_list = []
        for _domu_to_patch in aNodes:
            _node_prepatch_version[_domu_to_patch] = self.mGetCluPatchCheck().mCheckTargetVersion(_domu_to_patch,
                                                                                              PATCH_DOMU)
            _ret = self.mPostDomUPatchCheck(aDomU=_domu_to_patch,
                                             aPrePatchVersion=_node_prepatch_version[_domu_to_patch],
                                             aPostPatchTargetVersion=self.mGetTargetVersion(),
                                             aRollback=False,
                                             aTaskType=TASK_POSTCHECK)

            if _ret != PATCH_SUCCESS_EXIT_CODE:
                _post_patch_failed_nodes.append(_domu_to_patch)
                return _ret

        return _ret

    def mSetLaunchNodeToPatchOtherDomuNodes(self):
        """
        Selects and sets 2 bases for domU patching.
        use one to patch all other domUs
        and the other to patch initial dom0 or domU
        """

        self.mPatchLogInfo("Set Launch Node for DomU to patch other nodes.")
        _launch_node_initial_candidates = []
        _external_launch_nodes = self.mGetExternalLaunchNode()
        if len(_external_launch_nodes) > 0:
            self.mPatchLogInfo(f"Getting  external Launch Nodes for patching {str(_external_launch_nodes)}")
            _launch_node_initial_candidates = _external_launch_nodes
        else:
            _dom0U_list = self.mReturnPatchingDom0DomUList()
            _launch_node_initial_candidates = list(zip(*_dom0U_list))[1]
        _local_patch_zip = self.__domu_local_patch_zip
        _patch_zip_name = self.__domu_patch_zip_name
        _patch_zip_size_mb = self.__domu_patch_zip_size_mb
        _patch_base = self.__domu_patch_base
        _patch_zip = self.__domu_patch_zip
        _patchmgr = self.__domu_patchmgr
        _patch_necessary_space_mb = self.__domu_patch_necessary_space_mb
        _local_patch_zip2 = self.__domu_local_patch_zip2
        _patch_base_after_unzip = self.__domu_patch_base_after_unzip
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
            _suggestion_msg = "Insufficient launch node(s) found on the environment to patch. " \
                              "There must be atlest one launch node apart from the target node for patching to operate."
            self.mAddError(_exit_code, _suggestion_msg)
            raise Exception(_suggestion_msg)

        # loop twice since we need to set 2 dom[0U]s as dom[0U] patchers
        for _msg in _msgs:
            if len(_launch_node_candidates) > 0:
                if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                    self.mPatchLogInfo("*CPS as launch node *")
                    _selected_launch_node = self.mSetLaunchNodeAsPatchBaseForLocalNode(
                        aLaunchNodeCandidates=_launch_node_candidates,
                        aLocalPatchZipFile=_local_patch_zip,
                        aPatchZipName=_patch_zip_name,
                        aPatchZipSizeMb=_patch_zip_size_mb,
                        aRemotePatchBase=_patch_base,
                        aRemotePatchZipFile=_patch_zip,
                        aRemotePatchmgr=_patchmgr,
                        aRemoteNecessarySpaceMb=_patch_necessary_space_mb,
                        aPatchBaseDir=self.__domu_patch_base_dir,
                        aSuccessMsg=(_msg % (PATCH_DOMU.upper())),
                        aMoreFilesToCopy=[(_local_patch_zip2,
                                           _patch_base_after_unzip)])
                else:
                    _selected_launch_node = self.mSetLaunchNodeAsPatchBase(
                        aLaunchNodeCandidates=_launch_node_candidates,
                        aLocalPatchZipFile=_local_patch_zip,
                        aPatchZipName=_patch_zip_name,
                        aPatchZipSizeMb=_patch_zip_size_mb,
                        aRemotePatchBase=_patch_base,
                        aRemotePatchZipFile=_patch_zip,
                        aRemotePatchmgr=_patchmgr,
                        aRemoteNecessarySpaceMb=_patch_necessary_space_mb,
                        aPatchBaseDir = self.__domu_patch_base_dir,
                        aSuccessMsg=(_msg % (PATCH_DOMU.upper())),
                        aMoreFilesToCopy=[(_local_patch_zip2,
                                           _patch_base_after_unzip)])

                if not _selected_launch_node:
                    _errmsg = ((_errmsg_template % (_selected_launch_node))
                               + (_msg % (PATCH_DOMU)))
                    self.mPatchLogError(_errmsg)
                    raise Exception(_errmsg)
                else:
                    for _launch_node in _launch_node_candidates:
                        if (_launch_node in self.mGetJsonStatus() and
                                'error-1000' in _launch_node):
                            del self.mGetJsonStatus()[_launch_node]['error-1000']

                _selected_launch_nodes.append(_selected_launch_node)
                _launch_node_candidates.remove(_selected_launch_node)

        self.mPatchLogInfo(f"Selected launch nodes {str(_selected_launch_nodes)}")
        return _selected_launch_nodes

    def mPostDomUPatchCheck(self, aDomU, aPrePatchVersion,
                             aPostPatchTargetVersion, aRollback, aTaskType=None):
        """
        Returns True if all checks pass, False if any of the checks failed.
        checks currently done:
        *ping/ssh into the domu
        *verify the image is listed as sucess
        *verify new version is what we expected for upgrade or rollback
        *Restore ATP EXACC specific system settings.
        *check that db has started on domUs. Done by the patchmgr
        *check if the crs is up. Done by the patchmgr.
        """

        self.mPatchLogInfo(f"Starting post patch checks for the domu {aDomU}")

        '''
        Check that we can ping and ssh into domU
        In case of indepndent post check option, Its better
        to ping for 2secs before proceeding with other checks.
        '''
        _checked_domu_up_for_secs = 0
        _ret = PATCH_SUCCESS_EXIT_CODE
        if aTaskType in [TASK_POSTCHECK]:
            # In case of independent post check, we wait for
            # the minimum tim possible as most of the detils
            # in logs are already captured and waiting more
            # than 5 seconds would not be applicable in this case.
            _timeout_for_domu_up = 3
        else:
            _timeout_for_domu_up = self.mGetTimeoutForDomuStartupInSeconds()

        while _checked_domu_up_for_secs < _timeout_for_domu_up:
            if self.mGetCluPatchCheck().mPingNode(aDomU):
                break
            sleep(DOM0_DOMU_ONLINE_STATUS_CHECK_SLEEP_IN_SECONDS)
            _checked_domu_up_for_secs += DOM0_DOMU_ONLINE_STATUS_CHECK_SLEEP_IN_SECONDS
            self.mPatchLogInfo(f"**** DomU online check is polled for another {DOM0_DOMU_ONLINE_STATUS_CHECK_SLEEP_IN_SECONDS} seconds and re-validated.")
        else:
            _ret = DOMU_DID_NOT_STARTUP_POST_PATCH
            _suggestion_msg = f"VM {aDomU} did not come back online (not ping-able or ssh-able) post patch."
            self.mAddError(_ret, _suggestion_msg)

        # check that the image is seen as success
        if not self.mGetCluPatchCheck().mCheckImageSuccess(aDomU):
            _suggestion_msg = f"post-patch check: Guest VM {aDomU} image is not seen as success via imageinfo command. It could either be failed or is empty. Run imageinfo command on {aDomU} and Refer patchmgr logs : {self.mGetPatchmgrLogPathOnLaunchNode()} on VMs for more details."
            _ret = DOMU_IMAGE_STATUS_FAILED
            self.mAddError(_ret, _suggestion_msg)

        '''
         Restore ATP setting post DomU Upgrade/Rollback
        '''
        _domu_list = [ aDomU ]
        if not self.mSetExaccAtpSettingsOnDomU(_domu_list, "postpatch"):
            _suggestion_msg = f"Unable to set system attributes on the Guest VM List : {str(_domu_list)}, specific to ADB-C@C environments during Guest VM Patch operation. Verify ipv4.conf.eth0.rp_filter parameter in sysctl.conf before re-trying patch."
            _ret = UNABLE_TO_SET_SYSTEM_ATTRIBUTES_ATP_ENV
            self.mAddError(_ret, _suggestion_msg)

        _enable_health_checks_from_cp = self.mGetInfrapatchExecutionValidator().mCheckCondition('mEnableDBHealthChecks')

        '''
        Following code is run as part of regular upgrade
        and rollback flow. Independent post check option
        cant be used in this case.
        '''
        if aTaskType not in [TASK_POSTCHECK]:
            # Check that the domu is at the requested version. if it was a rollback
            # we just check for the version to be lower than what it previously was.
            _crs_enable = ""
            _current_domu_version = \
                self.mGetCluPatchCheck().mCheckTargetVersion(aDomU, PATCH_DOMU)
            if aRollback:
                if self.mGetCluPatchCheck().mCheckTargetVersion(
                        aDomU, PATCH_DOMU, aPrePatchVersion) >= 0:
                    _ret = DOMU_VERSION_LOWER_THAN_EXPECTED_VERSION
                    _suggestion_msg = f"VM rollback was requested but the version seems to be unchanged, found version {aPrePatchVersion}, expected to be lower than {_current_domu_version}."
                    self.mAddError(_ret, _suggestion_msg)
            elif self.mGetCluPatchCheck().mCheckTargetVersion(aDomU, PATCH_DOMU,
                                                          aPostPatchTargetVersion) < 0:
                """
                We proceed with patching only if the target version is higher than the current version.
                In all other cases, when currentVersion = targetVersion or currentVersion > TargetVersion (as seen in
                elastic node addition case, a node with higher version can be added), the node is skipped.            
                After successful patch completion, node would be at target version.
                """
                _ret = DOMU_VERSION_NOT_AT_EXPECTED_VERSION
                _suggestion_msg = f"VM is not at the requested upgrade version {aPrePatchVersion}, found version {_current_domu_version}."
                self.mAddError(_ret, _suggestion_msg)

            '''
             Perform CRS and Sanity checks post patching only in case 
             of crs checks are successful and autostartup is enabled.

             Fail Domu patching in case of below error codes
             are returned to avoid outage.
 
                    - DOMU_INVALID_CRS_HOME
                    - CRS_COMMAND_EXCEPTION_ENCOUNTERED 
                    - DOMU_CRS_SERVICES_DOWN
            '''
            _ret = self.mGetCluPatchCheck().mCheckandRestartCRSonDomU(aDomU)
            # If CRS is running, validate if all the dbs are back up or not
            if _ret == PATCH_SUCCESS_EXIT_CODE and _enable_health_checks_from_cp:
                _ret = self.mGetCluPatchCheck().mCheckCDBPDBHealthPostPatch(aDomU)
        else:
            _ret = self.mGetCluPatchCheck().mCheckandRestartCRSonDomU(aDomU)
            if _ret in [ DOMU_INVALID_CRS_HOME, CRS_COMMAND_EXCEPTION_ENCOUNTERED ]:
                return _ret
            elif _ret == PATCH_SUCCESS_EXIT_CODE:
                # only for retry request, trigger post stage calculation on the already upgraded node
                if self.mPatchRequestRetried() and _enable_health_checks_from_cp:
                    _ret = self.mGetCluPatchCheck().mCheckCDBPDBHealthPostPatch(aDomU, aIsRetry=True)
        return _ret

    def mSetExaccAtpSettingsOnDomU(self, aDomUList, aStage):
        """
         This methods restores the ATP specific system
         settings prior to and post DomU patch operations.
         These settings were recommnded by exacloud team.

         True -> Indicate values were restored successful.
         False -> Failed to restore system settings.
        """

        # Below settings are to be modified only if the environment is OCI EXACC.
        _oci_exacc = self.mGetCluControl().mCheckConfigOption('ociexacc', 'True')
        if not _oci_exacc:
            self.mPatchLogInfo("Environment is not ATP Exacc, no system settings will be restored. ")
            return True

        for _domU in aDomUList:

            _node = exaBoxNode(get_gcontext())
            try:
                _node.mConnect(aHost=_domU)

                # To set the value in memory.
                _cmd_sysctl_w = "sysctl -w net.ipv4.conf.eth0.rp_filter=0"
                self.mPatchLogInfo(f"System restore command will be run during {aStage} : {_cmd_sysctl_w}")
                _i, _o, _e = _node.mExecuteCmd(_cmd_sysctl_w)
                _rc = _node.mGetCmdExitStatus()
                if _rc != 0:
                    self.mPatchLogError(
                        f"Unable to set ipv4.conf.eth0.rp_filter values on DomU during {aStage} : {_domU}.")
                    _node.mDisconnect()
                    return False

                # To add settings in sysctl config files for the changes to takeeffect during next reboot.
                _cmd_set_sysctlconf = f"sed -i 's/^net.ipv4.conf.eth0.rp_filter.*/net.ipv4.conf.eth0.rp_filter = 0/' {SYSCTL_CONF}"
                _cmd_set_99sysctlconf = f"sed --follow-symlinks -i 's/^net.ipv4.conf.eth0.rp_filter.*/net.ipv4.conf.eth0.rp_filter = 0/' {SYSCTL_99_CONF}"

                for _file in [SYSCTL_CONF, SYSCTL_99_CONF]:
                    if _node.mFileExists(_file):

                        if _file in [SYSCTL_CONF]:
                            _cmd = _cmd_set_sysctlconf
                        else:
                            _cmd = _cmd_set_99sysctlconf

                        self.mPatchLogInfo(f"Running system file restore settings during {aStage} : {_cmd}")
                        _i, _o, _e = _node.mExecuteCmd(_cmd)
                        _rc = _node.mGetCmdExitStatus()
                        if _rc != 0:
                            self.mPatchLogError(
                                f"Unable to set ipv4.conf.eth0.rp_filter values on DomU during {aStage} : {_domU}.")
                            _node.mDisconnect()
                            return False
                    else:
                        self.mPatchLogError(f"Unable to locate {_file} file on {_domU} during {aStage}")
                        _node.mDisconnect()
                        return False

                _node.mDisconnect()

            except Exception as e:
                self.mPatchLogWarn(
                    f'Unable to set ipv4.conf.eth0.rp_filter values on DomU : {_domU} during {aStage}.\n {str(e)}')
                self.mPatchLogTrace(traceback.format_exc())
                _node.mDisconnect()
                return False

        return True

    def mRunDbnuPluginsOnAutonomousVMs(self, aDomuPatchList):
        """
        Restrict dbnu plugin execution to exacc adbd vms only
        """
        _dbnu_plugin_handler = self.mGetDbnuPluginHandler()
        if _dbnu_plugin_handler and self.mIsExaCC():
            _dbnu_plugin_execution_failed = False
            _dom0_and_autonomous_domu_list = self.mGetAutonomousVMList()
            __autonomous_domus_not_part_of_domu_patch_list = []
            for _dom0_hostname, _autonomous_domu_list in _dom0_and_autonomous_domu_list:
                for _autonomous_domu in _autonomous_domu_list:
                    # Make sure this adbd vm is the one that is getting patched as well.
                    if _autonomous_domu in aDomuPatchList:
                        _rc = _dbnu_plugin_handler.mApply(_autonomous_domu,
                                                       PATCH_DOMU)

                        if _rc != PATCH_SUCCESS_EXIT_CODE:
                            _patch_failed_message = f"Error running Dbnu plugins validation. Return code was {str(_rc)}. Errors on screen and in logs"
                            self.mPatchLogError(_patch_failed_message)
                            _dbnu_plugin_execution_failed = True
                            break
                    else:
                        __autonomous_domus_not_part_of_domu_patch_list.append(_autonomous_domu)
                if _dbnu_plugin_execution_failed:
                    break
            if len(__autonomous_domus_not_part_of_domu_patch_list) > 0:
                self.mPatchLogInfo(
                    f"List of autonomous VMs: {str(__autonomous_domus_not_part_of_domu_patch_list)} not part of the list of domus getting patched: {str(aDomuPatchList)}. Hence dbnu plugin execution skipped on these autonomous vms")
        else:
            self.mPatchLogInfo("Not an ExaCC ADBD env hence dbnu plugin execution skipped!")

    def mPatchRollbackDomUsRolling(self, aBackupMode, aNodePatcherAndPatchList, aRollback):
        """
        Patch/rollback rolling is handled by us
        (ie: we dont rely on  patchmgr with rolling option) since we need to
        to some checks before and after each patch/rollback on every dom[0U].

        If patching any domu fails the rest of the (not yet patched) dom[0U]s
        will not be attempted to be patched.
        """
        # List of launch nodes to update patch state metadata
        _launch_nodes = []
        _patchmgr_console_file = None
        _consolidated_patch_node_list = []
        _patchMgrObj = None

        for _patch, _node_list in aNodePatcherAndPatchList:
            _consolidated_patch_node_list += _node_list

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

        _node_to_patch_nodes = self.__domu_to_patch_domus
        _node_to_patch_initial_node = self.mGetDomUToPatchInitialDomU()
        '''
         _nodes_to_patch_except_initial can only be the customised
         list of nodes as patch operations are required to be performed
         only on the input node provided.
        '''
        _nodes_to_patch_except_initial = list(set(_consolidated_patch_node_list) -
                                              set([self.__domu_to_patch_domus]))
        _initial_node_list = [self.__domu_to_patch_domus]
        _cns_string = CNS_DOMU_PATCHER
        _node_patch_base_after_unzip = self.__domu_patch_base_after_unzip
        _node_patch_zip2_name = self.__domu_patch_zip2_name
        _nodes_not_patched = list(_consolidated_patch_node_list)
        '''
        When a single launch node is passed mGetDomUToPatchInitialDomU()
        will be None, we need to handle with the following code
        '''
        _launch_nodes = [self.__domu_to_patch_domus]
        if self.mGetDomUToPatchInitialDomU():
            _launch_nodes.append(self.mGetDomUToPatchInitialDomU())
        self.mPatchLogInfo(f"LaunchNodes = {str(_launch_nodes)}")
        _single_node_upgrade = False
        _node_stat_index = 0
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

        # initialize the list of nodes that get blacked out
        _blackout_nodes_list = []
        for _node_patcher, _node_patch_list in aNodePatcherAndPatchList:
            _round += 1

            # We are not suppose to continue further node upgrade if we found
            # any failure
            if _rc and _rc != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Failure detected in the earlier node upgrade. Return code = {_rc}")
                break

            self.mPatchLogInfo(
                f"{PATCH_DOMU.upper()} {_node_patcher} will be used to patch {str(_node_patch_list)} rolling")

            self.mSetPatchmgrLogPathOnLaunchNode( _node_patch_base_after_unzip + "patchmgr_log_" +
                    self.mGetMasterReqId())

            # Update with launch node in the patch metadata json
            self.mUpdateMetadataLaunchNodeForDomU(_launch_nodes,_node_patcher)

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
                    _suggestion_msg = f"The node {_node_to_patch} seems to be fresh install and we cannot perform rollback operation. Current operation style is {self.mGetOpStyle()}."
                    _rc = DOMU_ROLLBACK_FAILED_FOR_FRESH_INSTALL
                    self.mAddError(_rc, _suggestion_msg)
                    break

                '''
                 Perform cluster wide CRS checks on all DomUs in a given cluster
                 prior to patching.
                '''
                _rc = self.mGetCluPatchCheck().mCheckandRestartCRSonAllDomUWithinCluster()
                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    break

                _enable_health_checks_from_cp  = self.mGetInfrapatchExecutionValidator().mCheckCondition('mEnableDBHealthChecks')

                # Below code snippet validates if CRS is enabled or disabled.
                # if CRS is enabled it would validate if CRS is ONLINE before
                # the start of patch or rollback activity.
                _rc = self.mGetCluPatchCheck().mCheckCrsIsEnabled(_node_to_patch)
                if _rc in [ DOMU_INVALID_CRS_HOME, CRS_COMMAND_EXCEPTION_ENCOUNTERED ]:
                    break
                elif _rc == PATCH_SUCCESS_EXIT_CODE:

                    # Check crs and Validate for outage scenario
                    if _enable_health_checks_from_cp:
                        _enable_cdb_downtime_check = self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCDBDowntimeCheckEnabled')

                        if _enable_cdb_downtime_check:
                            # CDB healthchecks : Outage detection for DB/CRS service
                            _rc = self.mGetCluPatchCheck().mExecuteInfraPreSanityCheck(_node_to_patch)
                            if _rc != PATCH_SUCCESS_EXIT_CODE:
                                _sanity_check_log_on_remote_node = f"{DBAASAPI_SANITY_CHECK_LOG_PATH}/{DBAASAPI_SANITY_CHECK_LOG}"
                                _sanity_check_log_local_path = f"{self.mGetLogPath()}/{DBAASAPI_SANITY_CHECK_LOG}"
                                self.mPatchLogInfo(
                                    f"Copying {_sanity_check_log_on_remote_node} from remote node {_node_to_patch} to {_sanity_check_log_local_path} ")
                                self.mCopyFileFromRemote(_node_to_patch, _sanity_check_log_on_remote_node,
                                                         _sanity_check_log_local_path)
                                break
                        else:
                            self.mPatchLogInfo("enable_cdb_downtime_check is False so CDB downtime check is not run.")

                        _enable_pdb_downtime_check = self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsPDBDowntimeCheckEnabled')
                        _enable_pdb_degradation_check = self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsPDBDegradationCheckEnabled')

                        if _enable_pdb_downtime_check or _enable_pdb_degradation_check:
                            # Fetch dbsystem details json for post patch comparison to detect if pdb is in degraded state
                            _rc = self.mGetCluPatchCheck().mFetchAndStoreDBSystemDetailsToFile(_node_to_patch, "pre")
                            if _rc == PATCH_SUCCESS_EXIT_CODE and _enable_pdb_downtime_check:
                                self.mPatchLogInfo("PDB downtime check started.")
                                _rc = self.mGetCluPatchCheck().mDetectPDBDowntime(_node_to_patch)
                                self.mPatchLogInfo("PDB downtime check completed.")
                            else:
                               self.mPatchLogInfo("PDB downtime check is not run as enable_pdb_downtime_check is False.")
                            if _rc != PATCH_SUCCESS_EXIT_CODE:
                                break
                        else:
                            self.mPatchLogInfo("DB system details are not fetched during VM OS pre_patch as "
                                               "enable_pdb_downtime_check and enable_pdb_degradation_check are False.")


                # Update status
                self.mUpdatePatchStatus(True,
                                        (STEP_GATHER_NODE_DATA + '_' + PATCH_DOMU + f'_[{_node_stat_index:d}]'), _comment)

                # Perform system consistency check only during patch operation. Also, need to raise
                # FAIL_AND_SHOW error for this case so that customer can be involved to take
                # appropriate action.
                if not aRollback:
                    _is_system_valid_state, _suggestion_msg = self.mCheckSystemConsitency([_node_to_patch])

                _domU_listed_by_xm_list = []
                _pre_patch_version = self.mGetCluPatchCheck().mCheckTargetVersion(
                    _node_to_patch, PATCH_DOMU)

                # since we will do operations between dom[0U] upgrades,
                # create an input file per domu to patch
                _nat_host_to_patch = None
                _customer_host_to_patch = _node_to_patch
                # update with current dom[0u] patcher which will be used in
                # CNS monitor
                _node_patch_progress = os.path.join(self.mGetLogPath(), _cns_string)
                with open(_node_patch_progress, "w") as write_nodestat:
                    write_nodestat.write(f"{_node_patcher}:{self.mGetPatchmgrLogPathOnLaunchNode()}")

                # create patchmgr object with bare minimum arguments local to this for loop
                _patchMgrObj = InfraPatchManager(aTarget=PATCH_DOMU, aOperation=_task, aPatchBaseAfterUnzip=_node_patch_base_after_unzip, 
                                                 aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

                # now set the component's operation specific arguments
                _patchMgrObj.mSetIsoRepo(aIsoRepo=_node_patch_zip2_name)
                _patchMgrObj.mSetTargetVersion(aTargetVersion=self.mGetTargetVersion())
                _patchMgrObj.mSetSystemConsistencyState(aSystemConsistencyState=_is_system_valid_state)
                _patchMgrObj.mSetOperationStyle(aOperationStyle=self.mGetOpStyle())

                # create patchmgr nodes file
                _input_file = _patchMgrObj.mCreateNodesToBePatchedFile(aLaunchNode=_node_patcher, aHostList=[_node_to_patch])

                # prepare the patchmgr command for execution using the PatchManager object
                _patch_cmd = _patchMgrObj.mGetPatchMgrCmd()

                # Update status
                if _round == 1:
                    self.mUpdatePatchStatus(True,
                                            (STEP_RUN_PATCH_SECOND_DOMU + f'_[{_node_stat_index:d}]'), _comment)
                else:
                    self.mUpdatePatchStatus(True,
                                            (STEP_RUN_PATCH_DOMU + f'_[{_node_stat_index:d}]'), _comment)
                # Run dbnu plugin on ExaCC ADBD VMs before patchmgr command
                self.mRunDbnuPluginsOnAutonomousVMs(_node_patch_list)

                # enable blackout for the node that is going to be patched
                self.mSetUnsetBlackout(_node_to_patch, True)
                _blackout_nodes_list.append(_node_to_patch)

                # Run Pre Post Plugins
                if self.mIsExacloudPluginEnabled():
                    _read_patch_state = self.mGetDomUPatchStatesForNode(_launch_nodes, self.mGetMetadataJsonFile(),
                                                               _node_to_patch, PRE_PATCH)

                    self.mPatchLogInfo(f"DomU pre plugin patch status: {_read_patch_state}")
                    _pluginLog = self.mGetPluginHandler().mGetPluginsLogPathOnLaunchNode()
                    if not _read_patch_state:
                        _suggestion_msg = f"Invalid pre-Plugin state found during rolling patch = {_read_patch_state}. Refer plugin logs on the Patch driving Guest VM launch node(s) : {_launch_nodes} for more details ({_pluginLog})."
                        # Do not overwrite the error code from mApply
                        ret, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
                        if _child_request_error_already_exists_in_db:
                            self.mPatchLogError(_suggestion_msg)
                        else:
                            _rc = PRE_PLUGIN_FAILED_DOMU
                            self.mAddError(_rc, _suggestion_msg)
                        break

                    # If anything left at last run of pre plugin and patchmgr is still
                    # running, then re-run plugin too.
                    if _read_patch_state in [PATCH_PENDING, PATCH_RUNNING]:
                        if _read_patch_state == PATCH_PENDING:
                            # Update patch metadata status progress for pre plugins
                            self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _node_to_patch,
                                                 self.mGetMetadataJsonFile(), PRE_PATCH, PATCH_RUNNING)
                        _rc = self.mGetPluginHandler().mApply(_node_to_patch,
                                                       PATCH_DOMU, PRE_PATCH,
                                                       aRollback=aRollback)
                        if _rc != PATCH_SUCCESS_EXIT_CODE:
                            self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _node_to_patch,
                                                 self.mGetMetadataJsonFile(), PRE_PATCH, PATCH_FAILED)
                            break

                        self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _node_to_patch,
                                             self.mGetMetadataJsonFile(), PRE_PATCH, PATCH_COMPLETED)
                    elif _read_patch_state == PATCH_FAILED:
                        _suggestion_msg = f"Patch state found during rolling patch = {_read_patch_state}. Refer patchmgr logs : {self.mGetPatchmgrLogPathOnLaunchNode()} on the Patch driving Guest VM launch node(s) : {_launch_nodes} for more details ({_pluginLog})."
                        # Do not overwrite the error code from mApply
                        _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
                        if _child_request_error_already_exists_in_db:
                            self.mPatchLogError(_suggestion_msg)
                        else:
                            _rc = PRE_PLUGIN_FAILED_DOMU
                            self.mAddError(_rc, _suggestion_msg)
                        break

                # Run patch command
                # If there are no patchmgr sessions running, then run patchmgr command
                # In this context, PATCH_SUCCESS_EXIT_CODE infers NO_PATCHMGR Session is running.
                _patchmgr_session_exit = PATCH_SUCCESS_EXIT_CODE
                _patchmgr_active_node = None
                if self.mPerformPatchmgrExistenceCheck():
                    _patchMgrObj.mSetLaunchNode(aLaunchNode=None)
                    _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=_consolidated_patch_node_list)

                    _patchmgr_session_exit, _patchmgr_active_node = _patchMgrObj.mCheckForPatchMgrSessionExistence()

                if _patchmgr_session_exit == PATCH_SUCCESS_EXIT_CODE:  # No patchmgr session found in any of the nodes,
                    # so re-execute with same launch/_node_patcher
                    # Update patch metadata status progress for patchmgr
                    self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _node_to_patch,
                                         self.mGetMetadataJsonFile(), PATCH_MGR, PATCH_RUNNING)
                    if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                        _patchMgrObj.mExecutePatchMgrCmd(_patch_cmd)
                    else:
                        # set the launch node and execute patchmgr cmd
                        _patchMgrObj.mSetLaunchNode(aLaunchNode=_node_patcher)

                        _rc = _patchMgrObj.mExecutePatchMgrCmd(_patch_cmd)
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
                        # clear blackout for the node  - note that we are returning from here, so dont need to remove from list
                        self.mSetUnsetBlackout(_node_to_patch, False)
                        _suggestion_msg = f"VM OS Patch session running at the moment on {_patchmgr_active_node}. Executing multiple patchmgr sessions not supported for now. Terminating current Patch Request."
                        _rc = PATCHMGR_DOMU_SESSION_ALREADY_EXIST
                        self.mAddError(_rc, _suggestion_msg)
                        return _rc

                    # Already patchmgr is running, just monitor patchmgr console on the node.
                    self.mPatchLogInfo(
                        f"Patchmanager session exists and return code = {_patchmgr_session_exit}, Patchmgr session active node = {_patchmgr_active_node}")

                    _patchMgrObj.mSetLaunchNode(aLaunchNode=_patchmgr_active_node)
                    _node_patcher = _patchmgr_active_node

                # reset the node list to make sure patchmgr cmd execution 
                # only looked at the launch node
                _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=None)
                
                # Following PatchManager api sets the patchmgr execution status into mStatusCode method
                # hence not required to return/read a value from this api
                # this will help to use the patchMgr status apis 
                # (mIsSuccess/mIsFailed/mIsTimedOut/mIsCompleted) wherever required
                _patchMgrObj.mWaitForPatchMgrCmdExecutionToComplete()

                self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")

                _rc = _patchMgrObj.mGetStatusCode()

                # Capture time profile details
                self.mPopulateInfrapatchingTimeStatsEntries(aNewStage="POST_PATCH", aNewSubStage="",
                                                            aNewStageNodes=str([_node_to_patch]),
                                                            aCompletedStage="PATCH_MGR", aCompletedSubStage="",
                                                            aCompletedStageNodeDetails=str([_node_to_patch]))

                try:
                    # clear blackout for the node 
                    self.mSetUnsetBlackout(_node_to_patch, False)
                    _blackout_nodes_list.remove(_node_to_patch)

                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                        # Update patch metadata status progress for patchmgr
                        self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _node_to_patch,
                                             self.mGetMetadataJsonFile(), PATCH_MGR, PATCH_FAILED, aLaunchNode = _node_patcher)
                    else:
                        # Update patch metadata status progress for patchmgr
                        self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _node_to_patch,
                                             self.mGetMetadataJsonFile(), PATCH_MGR, PATCH_COMPLETED, aLaunchNode = _node_patcher)
                except:
                    self.mPatchLogError(
                        f"Error in updating PatchState Metadata after executing {_task} on node {_patchmgr_active_node} ")

                self.mUpdatePatchStatus(True,
                                        (STEP_CLEAN_ENV + '_' + PATCH_DOMU + f'_[{_node_stat_index:d}]'), _comment)

                # Get the logs, diags and so on
                _patch_log = str(
                    self.mGetDom0FileCode(_node_patcher,
                                           self.mGetPatchmgrLogPathOnLaunchNode()))
                if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                    self.mGetLocalNodePatchMgrOutFiles(
                                           self.mGetPatchmgrLogPathOnLaunchNode(),
                                           _patch_log)
                else:
                    # Change the owner of patchmgr folder incase of managment host as the launch node
                    if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
                        mChangeOwnerofDir(_node_patcher, _patch_log, 'opc', 'opc')
                    self.mGetPatchMgrOutFiles(_node_patcher,
                                           self.mGetPatchmgrLogPathOnLaunchNode(),
                                           _patch_log)
          
                '''
                 Collect patchmgr diag logs for debugging only
                 when the final exit code from patch operation 
                 is not PATCH_SUCCESS_EXIT_CODE.
                '''
                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    if self.mGetSingleVMHandler():
                        self.mGetSingleVMHandler().mGetPatchMgrDiagFilesForSingleVM(self, _node_patcher, [_node_to_patch],
                                                                                    self.mGetPatchmgrLogPathOnLaunchNode())
                    else:
                        self.mGetPatchMgrDiagFiles(_node_patcher,
                                                PATCH_DOMU,
                                                [_node_to_patch],
                                                self.mGetPatchmgrLogPathOnLaunchNode())
                else:
                    self.mPatchLogInfo("Patchmgr diag logs are not collected in case of a successful infra patch operation.")

                if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                    self.mGetLocalNodePatchMgrMiscLogFiles(self.mGetPatchmgrLogPathOnLaunchNode())
                    _cmd_list = [['rm', '-f', _input_file]]
                    runInfraPatchCommandsLocally(_cmd_list)
                    self.mLocalCopyLogsForADBDConsumption()
                    _cmd_list = [['mv', '-f', self.mGetPatchmgrLogPathOnLaunchNode(), self.mGetPatchmgrLogPathOnLaunchNode()+"_"+_node_patcher.split(".")[0] ]]
                    runInfraPatchCommandsLocally(_cmd_list)
                else:
                    self.mGetPatchMgrMiscLogFiles(_node_patcher,
                                               self.mGetPatchmgrLogPathOnLaunchNode())
                    _domu = exaBoxNode(get_gcontext())
                    self.mSetConnectionUser(_domu)
                    _domu.mConnect(aHost=_node_patcher)
                    _domu.mExecuteCmdLog(f"rm -f {_input_file}")

                    self.mCopyLogsForADBDConsumption(_domu)

                    # Moving log_dir to log_dir_<node_patched>, before starting another one
                    _domu.mExecuteCmdLog(
                        f"mv -f {self.mGetPatchmgrLogPathOnLaunchNode()} {self.mGetPatchmgrLogPathOnLaunchNode()}_{_node_patcher.split('.')[0]}")
                    _domu.mDisconnect()

                # Print all the log details at the end of log files copy.
                self.mPrintPatchmgrLogFormattedDetails()    

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
                                        (STEP_POSTCHECKS + '_' + PATCH_DOMU + f'_[{_node_stat_index:d}]'), _comment)

                _rc = self.mPostDomUPatchCheck(aDomU=_node_to_patch,
                                                 aPrePatchVersion=_pre_patch_version,
                                                 aPostPatchTargetVersion=self.mGetTargetVersion(),
                                                 aRollback=aRollback)
                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    _node_patch_failed = _node_to_patch
                    _patch_failed_message = f"domu [{_node_to_patch}] patching succeeded, but post-patch checks failed"
                    break

                if self.mIsExacloudPluginEnabled():
                    # Update patch metadata status progress for post plugins
                    self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _node_to_patch,
                                         self.mGetMetadataJsonFile(), POST_PATCH, PATCH_RUNNING)
                    _rc = self.mGetPluginHandler().mApply(_node_to_patch,
                                                   PATCH_DOMU, POST_PATCH,
                                                   aRollback=aRollback)
                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                        self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _node_to_patch,
                                             self.mGetMetadataJsonFile(), POST_PATCH, PATCH_FAILED)
                        break

                    self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _node_to_patch,
                                         self.mGetMetadataJsonFile(), POST_PATCH, PATCH_COMPLETED)


                # if any dom[0U] patch or post-patch failed, we cant risk patching
                # another node and it having issues also
                if _node_patch_failed:
                    break

            # Invoke sleep method only when:
            #   -> if user time specified is more than 1 seconds and
            #   -> if its not single node upgrade and then
            #   -> if upgrading node is not last node in the list.
            # Also, update the patch metadata file with sleeping mode.
            if (len(self.mGetIncludeNodeList()) >= 2) and\
                    self.mGetSleepbetweenComputeTimeInSec() > 0 and\
                    _num_nodes_to_patch > _count_nodes:
                self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _node_to_patch,
                                     self.mGetMetadataJsonFile(), POST_PATCH, PATCH_SLEEP_START)
                self.mSleepBtwNodes()
                self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _node_to_patch,
                                     self.mGetMetadataJsonFile(), POST_PATCH, PATCH_SLEEP_END)

        self.mPatchLogInfo(
            f"\n{PATCH_DOMU.upper()}s patched: {' '.join(_nodes_successfuly_patched)}\n{PATCH_DOMU.upper()}s not patched: {' '.join(_nodes_not_patched)}")
        if _node_patch_failed:
            self.mPatchLogError(_patch_failed_message)
            self.mPatchLogError(f"{PATCH_DOMU.upper()} patching or post-patching failed on: {str(_node_patch_failed)}")

        for _blackout_node in _blackout_nodes_list:
            self.mSetUnsetBlackout(_blackout_node, False)

        # If patchmgr not run and also no action needs to be taken, then our return code should
        # be essentially override by no action required code, otherwise, CNS code will keep on wait
        # for driver node to get the patchmgr xml report.
        if _rc == PATCH_SUCCESS_EXIT_CODE and _no_action_required == True:
            _rc = NO_ACTION_REQUIRED

        return _rc

    def mPatchRollbackDomUsNonRolling(self, aBackupMode, aNodePatcherAndPatchList, aRollback):
        """
        patch dom[0U]s in non-rolling fashion
        """

        # List of launch nodes to update patch state metadata
        _launch_nodes = []

        _rc = PATCH_SUCCESS_EXIT_CODE
        _no_action_required = True
        _patchmgr_console_file = None
        _consolidated_patch_node_list = []
        _patchMgrObj = None

        for _patch, _node_list in aNodePatcherAndPatchList:
            _consolidated_patch_node_list += _node_list
        _task = ""
        if aRollback:
            _task = TASK_ROLLBACK
        else:
            _task = TASK_PATCH

        _node_to_patch_nodes = self.__domu_to_patch_domus
        _node_to_patch_initial_node = self.mGetDomUToPatchInitialDomU()
        '''
         _nodes_to_patch_except_initial can only be the customised 
         list of nodes as patch operations are required to be performed 
         only on the input node provided.
        '''
        _nodes_to_patch_except_initial = list(set(_consolidated_patch_node_list) -
                                              set([self.__domu_to_patch_domus]))
        _initial_node_list = [self.__domu_to_patch_domus]
        _cns_string = CNS_DOMU_PATCHER
        _node_patch_base_after_unzip = self.__domu_patch_base_after_unzip
        _node_patch_zip2_name = self.__domu_patch_zip2_name
        _launch_nodes = [self.__domu_to_patch_domus]
        '''
        When a single launch node is passed mGetDomUToPatchInitialDomU()
        will be None, we need to handle with the following code
        '''
        if self.mGetDomUToPatchInitialDomU():
            _launch_nodes.append(self.mGetDomUToPatchInitialDomU())
        self.mPatchLogInfo(f"LaunchNodes = {str(_launch_nodes)}")
        _node_stat_index = 0
        _single_node_upgrade = False

        if (len(aNodePatcherAndPatchList) == 1 and
                aNodePatcherAndPatchList[0][0] == _node_to_patch_nodes):
            _node_stat_index = 1
            _single_node_upgrade = True

        # Set log dir with master request id tagged. Once upgrade is completed,
        # we would move and append with node name.
        self.mSetPatchmgrLogPathOnLaunchNode(_node_patch_base_after_unzip + "patchmgr_log_" +
                self.mGetMasterReqId())

        # mark node in blackout
        for _blackout_node in _consolidated_patch_node_list:
            self.mSetUnsetBlackout(_blackout_node, True)

        if self.mIsMockEnv():
            # in mock setup, skip rack specific operations
            return _rc

        _previous_iteration_patch_node_list = []
        for _node_patcher, _node_patch_list in aNodePatcherAndPatchList:
            _is_system_valid_state = True
            _node_stat_index += 1

            # Perform system consistency check only during patch operation on list of nodes.
            #  Also, need to raise FAIL_AND_SHOW error for this case so that customer can
            #  be involved to take appropriate action.
            if not aRollback:
                _is_system_valid_state, _suggestion_msg = self.mCheckSystemConsitency(_node_patch_list)

            with connect_to_host(_node_patcher, get_gcontext()) as _domu:
                # self.mPatchLogInfo("%s %s will be used to patch %s non-rolling" % (
                #     aTaskType.upper(), _node_patcher, str(_node_patch_list)))

                self.mPatchLogInfo(
                    f"{PATCH_DOMU.upper()} {_node_patcher} will be used to patch {str(_node_patch_list)} non-rolling")

                # update with current node patcher which will be used in CNS monitor
                _node_patch_progress = os.path.join(self.mGetLogPath(), _cns_string)
                with open(_node_patch_progress, "w") as write_nodestat:
                    write_nodestat.write(f"{_node_patcher}:{self.mGetPatchmgrLogPathOnLaunchNode()}")

                # Update with launch node in the patch metadata json
                self.mUpdateMetadataLaunchNodeForDomU(_launch_nodes, _node_patcher)

                # gather the data which we will need for the post patch checks
                _domU_up_per_dom0 = {}  # key is Dom0, value is list of DomU
                #  key is Dom[0U], value is version prior to patching
                _node_prepatch_version = {}
                for _node_to_patch in _node_patch_list:
                    # Update status
                    self.mUpdatePatchStatus(True,
                                            (STEP_GATHER_NODE_DATA + '_'
                                             + PATCH_DOMU + f'_[{_node_stat_index:d}]'),
                                            _node_to_patch)

                    # stop rollback if it found to be a fresh install
                    if aRollback and self.mCheckFreshInstall(_node_to_patch):
                        _node_patch_failed =  _node_to_patch
                        _suggestion_msg = f"The node {_node_to_patch} seems to be fresh install and we cannot perform rollback operation. Current operation style is {self.mGetOpStyle()}."
                        _rc = DOMU_ROLLBACK_FAILED_FOR_FRESH_INSTALL
                        self.mAddError(_rc, _suggestion_msg)
                        break 

                    '''
                      Perform cluster wide CRS checks on all DomUs in a given cluster
                      prior to patching.
                    '''
                    _rc = self.mGetCluPatchCheck().mCheckandRestartCRSonAllDomUWithinCluster()
                    if _rc in [ DOMU_INVALID_CRS_HOME, CRS_COMMAND_EXCEPTION_ENCOUNTERED, DOMU_CRS_SERVICES_DOWN ]:
                        break

                    _pre_patch_version = self.mGetCluPatchCheck().mCheckTargetVersion(
                        _node_to_patch, PATCH_DOMU)
                    _node_prepatch_version[_node_to_patch] = _pre_patch_version
                    self.mPatchLogInfo(f"{PATCH_DOMU.upper()} {_node_to_patch} is at version {_pre_patch_version}")
                # end of for

                '''
                 Fail Domu patching in case of below error codes
                 are returned to avoid outage.

                   - DOMU_INVALID_CRS_HOME
                   - CRS_COMMAND_EXCEPTION_ENCOUNTERED 
                   - DOMU_CRS_SERVICES_DOWN

                 Patching will still continue in case of CRS_IS_DISABLED
                 as CRS auto startup was disabled intentionally.
                '''
                if _rc in [ DOMU_INVALID_CRS_HOME, CRS_COMMAND_EXCEPTION_ENCOUNTERED, DOMU_CRS_SERVICES_DOWN ]:
                    # remove blackout
                    for _blackout_node in _consolidated_patch_node_list:
                        self.mSetUnsetBlackout(_blackout_node, False)
                    return _rc

                _list_with_nat_host_name = []

                # create patchmgr object with bare minimum arguments
                _patchMgrObj = InfraPatchManager(aTarget=PATCH_DOMU, aOperation=_task, aPatchBaseAfterUnzip=_node_patch_base_after_unzip, 
                                                 aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

                # now set the component's operation specific arguments
                _patchMgrObj.mSetTargetVersion(aTargetVersion=self.mGetTargetVersion())
                _patchMgrObj.mSetIsoRepo(aIsoRepo=_node_patch_zip2_name)
                _patchMgrObj.mSetSystemConsistencyState(aSystemConsistencyState=_is_system_valid_state)
                _patchMgrObj.mSetOperationStyle(aOperationStyle=self.mGetOpStyle())

                # create patchmgr nodes file
                _input_file = _patchMgrObj.mCreateNodesToBePatchedFile(aLaunchNode=_node_patcher, aHostList=_node_patch_list)

                # prepare the patchmgr command for execution using the PatchManager object
                _patch_cmd = _patchMgrObj.mGetPatchMgrCmd()


                if _node_stat_index == 1:
                    self.mUpdatePatchStatus(True,
                                            STEP_RUN_PATCH_SECOND_DOMU + '_[1]',
                                            _node_patcher)
                else:
                    self.mUpdatePatchStatus(True,
                                            STEP_RUN_PATCH_DOMU + f'_[{_node_stat_index:d}]')

                # Run dbnu plugin on ExaCC ADBD VMs before patchmgr command
                self.mRunDbnuPluginsOnAutonomousVMs(_node_patch_list)

                # Run exacloud plugins on each node before patchmgr cmd
                if self.mIsExacloudPluginEnabled():
                    self.mPatchLogInfo(f"Running domu pre exacloud plugins on {json.dumps(_node_patch_list, indent=4)}")
                    for _domu_to_patch in _node_patch_list:
                        _read_patch_state = self.mGetDomUPatchStatesForNode(_launch_nodes, self.mGetMetadataJsonFile(),
                                                            _domu_to_patch, PRE_PATCH)
                        self.mPatchLogInfo(f"DomU pre plugin patch status: {_read_patch_state}")
                        if not _read_patch_state:
                            _rc = FAILURE_IN_READING_PRE_PLUGIN_STATE
                            _suggestion_msg = f"Invalid patch state found during non-rolling patch = {_read_patch_state} on launch Node : {_launch_nodes}."
                            self.mAddError(_rc, _suggestion_msg)
                            break

                        # If anything left at last run of pre plugin and patchmgr is still
                        # running, then re-run plugin too.
                        if _read_patch_state in [PATCH_PENDING, PATCH_RUNNING]:
                            if _read_patch_state == PATCH_PENDING:
                                # Update patch metadata status progress for pre plugins
                                self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _domu_to_patch,
                                                    self.mGetMetadataJsonFile(), PRE_PATCH, PATCH_RUNNING)
                            _rc = self.mGetPluginHandler().mApply(_domu_to_patch,
                                                            PATCH_DOMU, PRE_PATCH,
                                                            aRollback=aRollback)
                            if _rc != PATCH_SUCCESS_EXIT_CODE:
                                self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _domu_to_patch,
                                                    self.mGetMetadataJsonFile(), PRE_PATCH, PATCH_FAILED)
                                break

                            self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _domu_to_patch,
                                                self.mGetMetadataJsonFile(), PRE_PATCH, PATCH_COMPLETED)
                        elif _read_patch_state == PATCH_FAILED:
                            _pluginLog = self.mGetPluginHandler().mGetPluginsLogPathOnLaunchNode()
                            _suggestion_msg = f"Patch state found during non-rolling patch = {_read_patch_state} on launch Node : {_launch_nodes}. Refer Patchmgr logs : {self.mGetPatchmgrLogPathOnLaunchNode()} on the Patch driving Guest VM node for more details ({_pluginLog})."
                            # Do not overwrite the error code from mApply
                            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
                            if _child_request_error_already_exists_in_db:
                                self.mPatchLogError(_suggestion_msg)
                            else:
                                _rc = PRE_PLUGIN_FAILED_DOMU
                                self.mAddError(_rc, _suggestion_msg)
                            break

                #Clean up dbnu plugin if dbnu plugin was run
                if self.mIsDbnuPluginEnabled():
                    for _domu_to_patch in _node_patch_list:
                        self.mGetDbnuPluginHandler().mCleanupDbnuPluginsFromNode(_domu_to_patch,PATCH_DOMU)

                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    _patch_failed_message = f"Error running pre exacloud plugins. Return code was {str(_rc)}. Errors on screen and in logs"
                    self.mPatchLogError(_patch_failed_message)
                    break

                # Run patch command
                # If there are no patchmgr sessions running, then run patchmgr command
                # In this context, PATCH_SUCCESS_EXIT_CODE infers NO_PATCHMGR Session is running.
                _patchmgr_session_exit = PATCH_SUCCESS_EXIT_CODE
                _patchmgr_active_node = None
                if self.mPerformPatchmgrExistenceCheck():
                    _patchMgrObj.mSetLaunchNode(aLaunchNode=None)
                    _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=_consolidated_patch_node_list)

                    _patchmgr_session_exit, _patchmgr_active_node = _patchMgrObj.mCheckForPatchMgrSessionExistence()

                if _patchmgr_session_exit == PATCH_SUCCESS_EXIT_CODE:  # No patchmgr session found in any of the nodes, so re-execute
                    # with same launch/_node_patcher
                    # Update patch metadata status progress for patchmgr
                    for _n in _node_patch_list:
                        self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _n,
                                            self.mGetMetadataJsonFile(), PATCH_MGR, PATCH_RUNNING)
                    if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                        _patchMgrObj.mExecutePatchMgrCmd(_patch_cmd)
                    else:
                        # set the launch node and execute patchmgr cmd
                        _patchMgrObj.mSetLaunchNode(aLaunchNode=_node_patcher)

                        _rc = _patchMgrObj.mExecutePatchMgrCmd(_patch_cmd)
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
                        _suggestion_msg = f"VM OS Patch session running at the moment on {_patchmgr_active_node}. Executing multiple patchmgr sessions not supported for now. Terminating current Patch Request."
                        _rc = PATCHMGR_DOMU_SESSION_ALREADY_EXIST
                        self.mAddError(_rc, _suggestion_msg)
                        # remove blackout
                        for _blackout_node in _consolidated_patch_node_list:
                            self.mSetUnsetBlackout(_blackout_node, False)
                        return _rc

                    # Already patchmgr is running, just monitor patchmgr console on the node.
                    self.mPatchLogInfo(
                        f"Patchmgr session exists and return code = {_patchmgr_session_exit}, Patchmgr session active node = {_patchmgr_active_node}")

                    _patchMgrObj.mSetLaunchNode(aLaunchNode=_patchmgr_active_node)

                    _node_patcher = _patchmgr_active_node

                # reset the node list to make sure patchmgr cmd execution 
                # only looked at the launch node
                _patchMgrObj.mSetCustomizedNodeList(aCustomizedNodeList=None)
                
                # Following PatchManager api sets the patchmgr execution status into mStatusCode method
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


                # Update patch error based on patchmgr return value and
                # Update patch metadata progress status for patchmgr status
                _patch_metadata_status = ""
                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    _patch_metadata_status = PATCH_FAILED
                else:
                    _patch_metadata_status = PATCH_COMPLETED

                for _n in _node_patch_list:
                    self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _n,
                                        self.mGetMetadataJsonFile(), PATCH_MGR, _patch_metadata_status)

                self.mUpdatePatchStatus(True,
                                        (STEP_CLEAN_ENV + '_' + PATCH_DOMU + f'_[{_node_stat_index:d}]'))

                # Get the logs, diags and so on
                _patch_log = str(
                    self.mGetDom0FileCode(_node_patcher,
                                        self.mGetPatchmgrLogPathOnLaunchNode()))

                if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                    self.mGetLocalNodePatchMgrOutFiles(self.mGetPatchmgrLogPathOnLaunchNode(),
                                            _patch_log)
                else:
                    self.mGetPatchMgrOutFiles(_node_patcher,
                                            self.mGetPatchmgrLogPathOnLaunchNode(),
                                            _patch_log)

                '''
                Collect patchmgr diag logs for debugging only
                when the final exit code from patch operation 
                is not PATCH_SUCCESS_EXIT_CODE.
                '''
                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    if self.mGetSingleVMHandler():
                        self.mGetSingleVMHandler().mGetPatchMgrDiagFilesForSingleVM(self, _node_patcher, _node_patch_list,
                                                                                    self.mGetPatchmgrLogPathOnLaunchNode())
                    else:
                        self.mGetPatchMgrDiagFiles(_node_patcher,
                                                PATCH_DOMU,
                                                _node_patch_list,
                                                self.mGetPatchmgrLogPathOnLaunchNode())
                else:
                    self.mPatchLogInfo("Patchmgr diag logs are not collected in case of a successful infra patch operation.")

                if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsCpsLaunchNodeForDomU'):
                    self.mGetLocalNodePatchMgrMiscLogFiles(self.mGetPatchmgrLogPathOnLaunchNode())
                    _cmd_list = [['rm', '-f', _input_file]]
                    runInfraPatchCommandsLocally(_cmd_list)

                    self.mLocalCopyLogsForADBDConsumption()

                    # Moving log_dir to log_dir_<node_patched>, before starting another one
                    _cmd_list =[['mv', '-f', self.mGetPatchmgrLogPathOnLaunchNode(),self.mGetPatchmgrLogPathOnLaunchNode()+"_"+_node_patcher.split(".")[0] ]]
                    runInfraPatchCommandsLocally(_cmd_list)
                else:
                    self.mGetPatchMgrMiscLogFiles(_node_patcher,
                                                self.mGetPatchmgrLogPathOnLaunchNode())
                    _domu.mExecuteCmdLog(f"rm -f {_input_file}")

                    self.mCopyLogsForADBDConsumption(_domu)

                    # Moving log_dir to log_dir_<node_patched>, before starting another one
                    _domu.mExecuteCmdLog(
                        f"mv -f {self.mGetPatchmgrLogPathOnLaunchNode()} {self.mGetPatchmgrLogPathOnLaunchNode()}_{_node_patcher.split('.')[0]}")

                # Print all the log details at the end of log files copy.
                self.mPrintPatchmgrLogFormattedDetails()

                # Log location is updated in mUpdateNodePatcherLogDir for proper collection of final CNS notification
                self.mUpdateNodePatcherLogDir(_node_patcher, _cns_string)
                
                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    _patch_failed_message = f"Error patching one of {str(_node_patch_list)} using {_node_patcher} to patch it. return code was {str(_rc)}. Errors on screen and in logs"
                    self.mPatchLogError(_patch_failed_message)
                    break

                # post checks on each node
                _post_patch_failed_nodes = []
                # Update status
                self.mUpdatePatchStatus(True,
                                        (STEP_POSTCHECKS + '_' + PATCH_DOMU + f'_[{_node_stat_index:d}]'))

                for _domu_to_patch in _node_patch_list:
                    _rc = self.mPostDomUPatchCheck(aDomU=_domu_to_patch,
                                                    aPrePatchVersion=_node_prepatch_version[_domu_to_patch],
                                                    aPostPatchTargetVersion=self.mGetTargetVersion(),
                                                    aRollback=aRollback)
                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                        _post_patch_failed_nodes.append(_domu_to_patch)

                if _post_patch_failed_nodes:
                    _patch_failed_message = f"{PATCH_DOMU.upper()} {str(_post_patch_failed_nodes)} patching succeded, but post-patch checks failed. Return code was = {str(_rc)}"
                    self.mPatchLogError(_patch_failed_message)
                    break

                # Run exacloud plugins on each node after patchmgr cmd
                if self.mIsExacloudPluginEnabled():
                    self.mPatchLogInfo(
                        f"Running domu post exacloud plugins on {json.dumps(_node_patch_list, indent=4)}")
                    for _domu_to_patch in _node_patch_list:
                        self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _domu_to_patch,
                                            self.mGetMetadataJsonFile(), POST_PATCH, PATCH_RUNNING)
                        _rc = self.mGetPluginHandler().mApply(_domu_to_patch, PATCH_DOMU, POST_PATCH, aRollback=aRollback)
                        if _rc != PATCH_SUCCESS_EXIT_CODE:
                            self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _domu_to_patch,
                                                self.mGetMetadataJsonFile(), POST_PATCH, PATCH_FAILED)
                            break

                        self.mUpdateDomUPatchMetadata(PATCH_DOMU, _launch_nodes, _domu_to_patch,
                                            self.mGetMetadataJsonFile(), POST_PATCH, PATCH_COMPLETED)

                #Clean up dbnu plugin if dbnu plugin was run
                if self.mIsDbnuPluginEnabled():
                    for _domu_to_patch in _node_patch_list:
                        self.mGetDbnuPluginHandler().mCleanupDbnuPluginsFromNode(_domu_to_patch,PATCH_DOMU)

                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    _patch_failed_message = f"Patching succeded, but error running post exacloud plugins. Return code was {str(_rc)}. Errors on screen and in logs"
                    self.mPatchLogError(_patch_failed_message)


                # if return code of previous patch operation is non-zero,
                # we had an issue so dont do any more patching
                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    break

                _previous_iteration_patch_node_list = _node_patch_list[:]

        # remove blackout
        for _blackout_node in _consolidated_patch_node_list:
            self.mSetUnsetBlackout(_blackout_node, False)

        # If patchmgr not run and also no action needs to be taken, then our return code should
        # be essentially override by no action required code, otherwise, CNS code will keep on wait
        # for driver node to get the patchmgr xml report.
        if _rc == PATCH_SUCCESS_EXIT_CODE and _no_action_required == True:
            _rc = NO_ACTION_REQUIRED

        return _rc

    def _mGetNodePatchPair(self, _nodes_that_require_patching, _node_to_patch_initial_node, _node_to_patch_nodes):
        #  contains tuples of the form [(patcher_node, [nodes_to_patch]), .. ]
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
        self.mPatchLogInfo(f"_node_patcher_and_node_patch_list: {str(_node_patcher_and_node_patch_list)}")
        return _node_patcher_and_node_patch_list



    '''
    Copy log_dir to ADBD_INFRA_DOMU_PATCH_LOG_CONSUMPTION_LOCATION for ADBD consumption
    Note that cleaning up of the logs on a regular basis to release space is the responsibility 
    of ADBD and infra patching won't clear that space.
    '''
    def mCopyLogsForADBDConsumption(self, domu):
        self.mPatchLogInfo("Check if its an ADBD env...")
        if self.mGetAutonomousVMList() and len(self.mGetAutonomousVMList()) > 0:
            self.mPatchLogInfo(f"ADBD env detected. Copying logs to {ADBD_INFRA_DOMU_PATCH_LOG_CONSUMPTION_LOCATION}")
            try:
                domu.mExecuteCmdLog(
                    f"/usr/bin/mkdir -p {ADBD_INFRA_DOMU_PATCH_LOG_CONSUMPTION_LOCATION}; /usr/bin/cp -rf {self.mGetPatchmgrLogPathOnLaunchNode()} {ADBD_INFRA_DOMU_PATCH_LOG_CONSUMPTION_LOCATION}")
                domu.mExecuteCmdLog(
                    f"/usr/bin/chown -R oracle:oinstall {ADBD_INFRA_DOMU_PATCH_LOG_CONSUMPTION_LOCATION}")
                domu.mExecuteCmdLog(f"/usr/bin/chmod -R 770 {ADBD_INFRA_DOMU_PATCH_LOG_CONSUMPTION_LOCATION}")
            except:
                self.mPatchLogInfo(f"Unable to copy logs to {ADBD_INFRA_DOMU_PATCH_LOG_CONSUMPTION_LOCATION}")
        else:
            self.mPatchLogInfo("Not an ADBD env, logs will not be copied")

    '''
    Copy log_dir to ADBD_INFRA_DOMU_PATCH_LOG_CONSUMPTION_LOCATION for ADBD consumption
    Note that cleaning up of the logs on a regular basis to release space is the responsibility
    of ADBD and infra patching won't clear that space.
    '''
    def mLocalCopyLogsForADBDConsumption(self):
        self.mPatchLogInfo("Check if its an ADBD env...")
        if self.mGetAutonomousVMList() and len(self.mGetAutonomousVMList()) > 0:
            self.mPatchLogInfo(f"ADBD env detected. Copying logs to {ADBD_INFRA_DOMU_PATCH_LOG_CONSUMPTION_LOCATION}")
            try:
                _cmd_list = [['/usr/bin/mkdir', '-p', ADBD_INFRA_DOMU_PATCH_LOG_CONSUMPTION_LOCATION]]
                runInfraPatchCommandsLocally(_cmd_list)
                _cmd_list = [['/usr/bin/cp', '-rf', self.mGetPatchmgrLogPathOnLaunchNode(), ADBD_INFRA_DOMU_PATCH_LOG_CONSUMPTION_LOCATION]]
                runInfraPatchCommandsLocally(_cmd_list)
                _cmd_list = [['/usr/bin/chown', '-R', 'oracle:oinstall', ADBD_INFRA_DOMU_PATCH_LOG_CONSUMPTION_LOCATION]]
                runInfraPatchCommandsLocally(_cmd_list)
                _cmd_list = [['/usr/bin/chmod', '-R', '770', ADBD_INFRA_DOMU_PATCH_LOG_CONSUMPTION_LOCATION]]
                runInfraPatchCommandsLocally(_cmd_list)
            except:
                self.mPatchLogInfo(f"Unable to copy logs to {ADBD_INFRA_DOMU_PATCH_LOG_CONSUMPTION_LOCATION}")
        else:
            self.mPatchLogInfo("Not an ADBD env, logs will not be copied")

    def mUpdateDomUPatchMetadata(self, aNodeType, aMetadataNodesList, aNode, aMetadatafile, aStage, aToUpdateStatus,
                             aLaunchNode=None):
        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
            mUpdatePatchMetadata(aNodeType, aMetadataNodesList, aNode, aMetadatafile, aStage, aToUpdateStatus,\
                                 aLaunchNode, aUser='opc')
        else:
            mUpdatePatchMetadata(aNodeType, aMetadataNodesList, aNode, aMetadatafile, aStage, aToUpdateStatus, \
                                 aLaunchNode)

    def mGetDomUPatchStatesForNode(self, aMetadataNodesList, aMetadatafile, aNode, aStage):
        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
            return mGetPatchStatesForNode(aMetadataNodesList, aMetadatafile, aNode, aStage, aUser='opc')
        else:
            return mGetPatchStatesForNode(aMetadataNodesList, aMetadatafile, aNode, aStage)

    def mUpdateMetadataLaunchNodeForDomU(self, _launch_nodes, _node_patcher):
        if self.mGetInfrapatchExecutionValidator().mCheckCondition('mIsManagementHostLaunchNodeForDomU'):
            mUpdateMetadataLaunchNode(_launch_nodes, self.mGetMetadataJsonFile(), PATCH_DOMU, _node_patcher,
                                      aUser='opc')
        else:
            mUpdateMetadataLaunchNode(_launch_nodes, self.mGetMetadataJsonFile(), PATCH_DOMU, _node_patcher)
