#
# $Header: ecs/exacloud/exabox/infrapatching/handlers/targetHandler/cellhandler.py /main/86 2025/11/17 18:10:28 jyotdas Exp $
#
# cellhandler.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cellhandler.py - Patch - Cell Basic Functionality
#
#    DESCRIPTION
#      Provide basic/core cell patching API (prereq, patch,
#      rollback_prereq, and rollback) for managing the Exadata patching in
#      the cluster implementation.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jyotdas     10/31/25 - Bug 38575316 - Parallelise the dom0 shutdown across
#                           all nodes while non-rolling qmr patching.
#    mirrodri    10/28/25 - Bug 38513100 - CHECK EDV AND ESNP STATUS BEFORE
#                           SHUTDOWN OF EDV AND ESNP SERVICE ON DOM0 DURING
#                           CELL NON-ROLLING UPGRADE.
#    mirrodri    10/14/25 - Bug 38264211 - INFRA-PATCH:NON-ROLLING CELL PATCHING
#                           PROCEEDS WHEN ESNP SERVICE WAS NOT SHUTDOWN. AFTER 
#                           PATCHING SERVICES ARE NOT BROUGHT BACK UP.
#    avimonda    09/12/25 - Bug 38293914 - OCI: MISLEADING ERROR IN THE ECACLI
#                           STATUS FOR EXACLOUD
#    diguma      06/02/25 - bug 38020509: fix variable incorrectly initialized
#    diguma      05/22/25 - Bug37984512: FOR NON-ROLLING CELL PATCHING, EDV AND
#                           ESNP SERVICES NEED TO BE SHUTDOWN ON DOM0
#    sdevasek    04/23/25 - Enh 37041773 - PERFORM SPACE CHECK ONLY ON
#                           APPLICABLE NODES BASED ON GRANULAR PATCHING AND
#                           ALREADY UPGRADED NODES
#    nelango     02/12/25 - Bug 37328906: ipmi servicestate checks for
#    araghave    02/04/25 - Enh 34479463 - PROVIDE EXACLOUD REGISTRATION AND
#                           PLUGIN SUPPORT FOR CELLS
#    antamil     01/31/25 - Enh 37300427 - Enable clusterless cell patching
#                           using management host
#    avimonda    01/11/25 - Bug 37232903 - AIM4ECS:0X03010010 - TASK HANDLER
#                           PATCH REQUEST EXCEPTION DETECTED.
#    diguma      12/06/24 - bug 37365122 - EXACS:24.4.2.1:X11M: ROLLING DOM0
#                           PATCHING FAILS WITH SSH CONNECTIVITY CHECK FAILED
#                           DURING PATCHING EVEN THOUGH EXASSH TO DOMUS WORK
#    sdevasek    11/29/24 - bug 37335358 - NODE_PROGRESS_DATA SHOULD HAVE THE
#                           DATA FOR REQUESTED CELL COUNT ONLY AND SHOULD NOT
#                           HAVE DATA FOR ALREADY UPGRADED CELLS
#    araghave    11/26/24 - Bug 37247140 - ALLOW DOMU ONEOFF PATCH TO COPY AND
#                           EXECUTE PLUGINS BASED ON AVAILABLE KEYS
#    diguma      11/08/24 - bug 37264841: ENABLING LISTENER INTERFACE ON CELL
#    araghave    10/08/24 - Enh 36505637 - IMPROVE POLLING MECHANISM IN CASE
#                           OF INFRA PATCHING OPERATIONS
#    jyotdas     10/07/24 - ER 37089701 - ECRA Exacloud integration to enhance
#                           infrapatching operation to run on a single thread
#    diguma      09/27/24 - bug 37112385 - REMOVING FIX FOR 36640349 FROM 
#                           CODELINE UNTIL 37036798 HAS A SOLUTION 
#    avimonda    09/16/24 - Enhancement Request 36775120 - EXACLOUD TIMEOUT
#                           MUST BE CALCULATED BASED ON THE PATCH OPERATION
#                           AND TARGET TYPE
#    araghave    09/16/24 - Enh 36971721 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE TARGET HANDLER FILES
#    araghave    08/14/24 - Enh 36923844 - INFRA PATCHING CHANGES TO SUPPORT
#                           PATCHING ADMIN SWITCH
#    emekala     08/13/24 - ENH 36679949 - REMOVE OVERHEAD OF INDEPENDENT
#                           MONITORING PROCESS FROM INFRAPATCHING
#    jesandov    08/12/24 - bug36937497: Add ssh key rotation
#    avimonda    07/24/24 - Bug 36563684 - AIM4EXACLOUD:0X03040001 - VM PRECHECK
#                           EXCEPTION DETECTED. (23.4.1.2.1-DOMU)
#    diguma      07/22/24 - bug36870253: ERROR CHECKING THE INTERFACE TYPE
#    emekala     07/19/24 - ENH 36794217 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE EXACOMPUTE AND DOMU PATCHMGR CMDS
#    araghave    07/15/24 - Enh 36830077 - CLEANUP KSPLICE CODE FROM
#                           INFRAPATCHING FILES
#    diguma      07/10/24 - bug 36727709: CONFIGURE LISTENINGINTERFACE ON CELL
#                           NODES AFTER 24.1 PATCHING
#    josedelg    07/03/24 - Bug 36801471 - VMS must be started up during
#                           non-rolling cell patch when cell count is passed
#    emekala     06/25/24 - ENH 36748433 - PATCH MANAGER SPECIFIC CHANGES TO
#                           HANDLE DOM0, CELL, IBSWITCH AND ROCESWITCH PATCHMGR
#                           CMDS
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    araghave    05/09/24 - Bug 36599891 - EXACC|GEN2|INFRA PATCHING|PRECEHCK
#                           MARKED SUCCESS THOUGH THERE WAS FAILURE
#    araghave    04/19/24 - ER 36452945 - TERMINATE INFRA PATCHING THREAD EARLY
#                           IN CASE OF PATCHMGR COMMAND DID NOT RUN
#    araghave    02/28/24 - Enh 36295801 - IMPLEMENT ONEOFFV2 PLUGIN EXACLOUD
#                           CHANGES
#    araghave    02/08/24 - Enh 36234905 - ENABLE SERVICESTATE OF INFRA ILOM
#                           DURING UPGRADE & DISABLE THEM AFTER UPGRADE
#    josedelg    01/26/24 - Bug 36060863 - Get cell count from CP
#    josedelg    12/18/23 - Enh 36073825 - Create static ordered cell list
#    avimonda    11/29/23 - Bug 35972504 - If any cell fails to come online
#                           after patching, lowering the number of cleanup
#                           retries.
#    antamil     11/29/23 - Bug 36033909 - Recreate node_list file for cell cleanup
#    antamil     09/29/23 - Bug 35851548 - Append request Id to dbnodes file name
#                           to be unique
#    antamil     18/08/23 - ENH 35577433 - ADD VALIDATIONS ON EXTERNAL LAUNCH NODE
#                           PASSED
#    sdevasek    08/30/23 - BUG 35662405 - FAILED TO SHUTDOWN VMS DURING CELL
#                           NON-ROLLING UPGRADE FAILED
#    avimonda    07/30/23 - Bug 35443002 - Set the current target type to cell
#                           before establishing the launch node.
#    avimonda    07/25/23 - Bug 34986894 - Adjust the patchmgr timeout to
#                           prevent CELLs patching timeout in rolling mode.
#    araghave    12/19/22 - Enh 34339397 - REMOVE RESTRICTION FOR MULTIPLE
#                           PATCHMGR ON SINGLE LAUNCH NODE
#    araghave    09/29/22 - Enh 34623863 - PERFORM SPACE CHECK VALIDATIONS
#                           BEFORE PATCH OPERATIONS ON TARGET NODES
#    araghave    09/14/22 - Enh 34480945 - MVM IMPLEMENTATION ON INFRA PATCHING
#                           CORE FILES
#    araghave    06/24/22 - Enh 34258082 - COPY PATCHMGR DIAG LOGS FROM LAUNCH
#                           NODES POST PATCHING ONLY IF THE EXIT STATUS IS A
#                           FAILURE
#    araghave    06/03/22 - Bug 34241012 - CELL ROLLBACK VALIDATION ARE
#                           REQUIRED TO BE RUN ONLY ON FILTERED NODE LIST
#    araghave    05/24/22 - Enh 33951360 - CHECK ROLLBACK VALIDATION FOR CELL
#                           UPGRADE
#    sdevasek    05/22/22 - ENH 33859232 - TRACK TIME PROFILE INFORMATION FOR
#                           INFRAPATCH OPERATIONS
#    araghave    04/19/22 - Enh 33516791 - EXACLOUD: DO NOT OVER WRITE THE
#                           ERROR SET BY RAISE EXCEPTION
#    araghave    04/12/22 - Enh 34048154 - ONEOFF PATCH OPERATION TO SUPPORT A
#                           PLUGIN FRAMEWORK WITH GENERIC OPTIONS
#    josedelg    04/11/22 - BUG 34052030 - Remove griddisk in UNUSED state
#                           validation
#    araghave    03/08/22 - ER33689675 - Move MOS NOTE 2829056.1 messages to
#                           ecra_error_catalog.json
#    araghave    02/20/22 - Bug 33847682 - DELAYED PATCHMGR PROCESS EXIT CAUSES
#                           SUBSEQUENT PATCHMGR CLEANUP TO FAIL
#    sdevasek    01/18/22 - Enh 32509673 - Require ability to specify Cell
#                           nodes to include as part of Patching process
#    araghave    01/18/22 - Enh 30646084 - Require ability to specify compute
#                           nodes to include as part of Patching process
#    nmallego    01/12/22 - Bug33689655 - UPDATE DOMU FAIL AND SHOW ERROR
#                           MESSAGE WITH MOS NOTE 2829056.1
#    araghave    11/23/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES
#                           FROM ERROR.PY TO INFRAPATCHERROR.PY
#    nmallego    11/19/21 - Bug33584494 - correct log message
#    nmallego    11/10/21 - Bug33521580 - Update ASM mode status message
#    araghave    10/20/21 - Enh 33486853 - MOVE TIMEOUT AND OTHER CONSTANTS OUT
#                           OF CODE INTO CONFIG/CONSTANT FILES
#    nmallego    10/18/21 - Bug32945969 - Non-rolling: Optimize the
#                           shutdown/startup
#    araghave    09/23/21 - Enh 33366173 - INFRA PATCHING TO NOTIFY END USER
#                           REGARDING GRID DISKS IN OFFLINE STATE
#    araghave    09/03/21 - Enh 32626119 - Infra patching to notify end user
#                           regarding Grid Disks in Unused/Syncing status
#    nmallego    08/31/21 - Bug33249608 - Support non-rolling option
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
#    araghave    03/08/21 - Bug32593118 - Collect the actual patchmgr status
#                           only when patchmgr is success
#    araghave    02/16/21 - ENH 31423563 - PROVIDE A MECHANISM TO MONITOR
#                           INFRA PATCHING PROGRESS
#    nmallego    01/28/21 - Bug31963499-Instrumented code to track return
#                           payload
#    araghave    01/19/21 - Bug 32395969 - MONTHLY PATCHING: FOUND FEW ISSUES
#                           WHILE TESTING AND NEED TO FIX
#    araghave    12/24/20 - Bug 32319703 - Precheck error handling fix
#    josedelg    01/04/21 - Bug 32319928 - Error handling format issue
#    nmallego    12/07/20 - Bug31982131 - Do not ignore critical h/w alert
#    araghave    11/27/20 - Enh 31604386 - RETURN ERROR CODES TO DBCP FOR CELLS
#                           AND SWITCHES
#    araghave    09/16/20 - Enh 31870258 - Include additional option
#                           ignore_date_validation for cells.
#    araghave    08/12/20 - ER 31395456 - Display the cell and switchnumber during
#                           patching and rollback.
#    araghave    08/12/20 - Enh 30829107 - Patchmgr log detailed output and log
#                           collection fix
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#

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
import copy
import os, sys
import traceback
from multiprocessing import Process
from time import sleep
from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB
from exabox.core.Node import exaBoxNode
from exabox.infrapatching.handlers.targetHandler.targethandler import TargetHandler
from exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler import InfraPatchManager
from exabox.infrapatching.utils.utility import mRegisterInfraPatchingHandlers, mReadCallback, mErrorCallback, mGetSshTimeout, checkPluginEnabledFromInfraPatchMetadata
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.exakms.ExaKmsEndpoint import ExaKmsEndpoint

sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))

class CellHandler(TargetHandler):

    def __init__(self, *initial_data, **kwargs):

        super(CellHandler, self).__init__(*initial_data, **kwargs)
        self.mPatchLogInfo("CellHandler")
        mRegisterInfraPatchingHandlers(INFRA_PATCHING_HANDLERS, [PATCH_CELL], self)
        self.__dom0s_list = {}
        self.__patchable_cells = []
        self.__cell_patchmgr_timeout_in_sec = 0
        self.mPrintEnvRelatedDebugStatements()

    def mSetEnvironment(self):

        # Adjust the patchmgr timeout to prevent CELL patching timeout in rolling mode.
        self.__cell_patchmgr_timeout_in_sec = self.mGetCellPatchingTimoutInSec()

        # Set patch environment
        self.mSetcellSwitchesBaseEnvironment()

        # set target type
        self.mSetCurrentTargetType(PATCH_CELL)

        # Set launch node
        _ret = PATCH_SUCCESS_EXIT_CODE
        _ret, _launch_node = self.mSetDom0ToPatchcellSwitches()

        # Add to executed targets
        self.mGetExecutedTargets().append(PATCH_CELL)
        self.mSetCallBacks([mReadCallback, None, mErrorCallback, None])

        # Set collect time stats flag
        self.mSetCollectTimeStatsFlag(self.mGetCollectTimeStatsParam(PATCH_CELL))
        return _ret

    def mGetCellPatchingTimoutInSec(self):

        # Adjust the patchmgr timeout to prevent CELL patching timeout in rolling mode.
        _cell_patchmgr_timeout_in_sec = self.mGetExadataPatchmgrConsoleReadTimeoutSec()

        _op_style = self.mGetOpStyle()
        _task = self.mGetTask()
        if _op_style in [OP_STYLE_AUTO, OP_STYLE_ROLLING] and _task in [ TASK_PATCH, TASK_ROLLBACK ]:
            _node_list = self.mGetCustomizedCellList()
            _patchable_cells_count = len(_node_list)
            if  _patchable_cells_count > 5 and _patchable_cells_count < 10 :
                _cell_patchmgr_timeout_in_sec = (self.mGetExadataPatchmgrConsoleReadTimeoutSec() * self.mGetExacloudPatchmgr6To9CellNodesTimeoutMultiplier())
            elif _patchable_cells_count >= 10:
                _cell_patchmgr_timeout_in_sec = (self.mGetExadataPatchmgrConsoleReadTimeoutSec() * self.mGetExacloudPatchmgr10OrMoreCellNodesTimeoutMultiplier())

        if _cell_patchmgr_timeout_in_sec:
            self.mPatchLogInfo(f"Exadata patchmgr console read timeout is {_cell_patchmgr_timeout_in_sec} seconds.")
        else:
            self.mPatchLogError("Invalid exadata patchmgr console read timeout is configured.")

        return _cell_patchmgr_timeout_in_sec

    def mUpdateTaskFile(self):
        """
        It looks for cell_states.txt to get the current status of cell patching.
        This also to keep statusinfo updated with the currentcell being patched.
        This function runs in a different process while patch is running.
        """
        _new_reqobj = None
        _uuid = None
        _output_file = None
        _dom0 = None
        _cell = None
        _template_header = 'patchmgr task: %s\n'
        _read_cell_cmd = f"cat {self.mGetCellSwitchesPatchBaseAfterUnzip()}cell_states.txt 2>/dev/null"
        # Get list of all cells specified for patching(i.e custom node list)
        _cells = self.mGetCustomizedCellList()
        _done_cells = []
        _db = ebGetDefaultDB()
        _template_node = '''\n* %s:\n%-20s\n'''

        try:
            _new_reqobj = copy.copy(self.mGetCluControl().mGetRequestObj())
            _uuid = _new_reqobj.mGetUUID()
        except Exception as e:
            self.mPatchLogError(f"Error while fetching request object in extra process: {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            return

        # Get file path
        _output_file = self.__log_path
        if _output_file[-1] != '/':
            _output_file += '/'
        _output_file += 'patchmgr.cellinfo'

        while True:
            _text = ''
            _row = None

            # Reload request information
            _row = _db.mGetRequest(_uuid)

            if not _row:
                break

            # Get status information
            _stat, _percentage, _step = _row[10].split(':')

            if _step.startswith(TASK_PATCH) or _step.startswith(TASK_ROLLBACK):
                # Check if patchmgr is running in cells
                if _step.find('_' + PATCH_CELL) >= 0:
                    _text += _template_header % _step

                    _dom0 = exaBoxNode(get_gcontext())
                    _dom0.mConnect(aHost=self.mGetDom0ToPatchcellSwitches())
                    _i, _o, _e = _dom0.mExecuteCmd(_read_cell_cmd)

                    _output = _o.readlines()
                    _dom0.mDisconnect()

                    if _output:
                        self.mPatchLogInfo("************")
                        self.mPatchLogInfo(_output)
                        for _line in _output:
                            _cell = None
                            for _c in _cells:
                                if _line.find(_c) >= 0:
                                    _cell = _c
                                    break

                            if _cell:
                                _text += _template_node % (_cell, _line.replace(_cell + ":", "").strip())

                    # Update statusinfo if necessary
                    if _new_reqobj:
                        if _cell and len(_output) == 1:
                            if _cell not in _done_cells:
                                _done_cells.append(_cell)
                            if _row[10].find(_cell) == -1:
                                _new_reqobj.mSetStatusInfo(_row[10].split('-')[0] + f'-[{len(_done_cells):d}/{len(_cells):d}]_{_cell}')
                                _db.mUpdateStatusRequest(_new_reqobj)
                        if len(_output) > 1:
                            if _row[10].find('parallel_task_in_all_cells') == -1:
                                _new_reqobj.mSetStatusInfo(_row[10].split('-')[0]+'-'+'parallel_task_in_all_cells')
                                _db.mUpdateStatusRequest(_new_reqobj)

                    # Open file and write status information
                    with open(_output_file, 'w') as fd:
                        fd.write(_text)
                else:
                    self.mPatchLogInfo('Extra process ending because no cell patch is running anymore')
                    break

            # If the request is already done, then exit thread
            if _row[1].startswith('Done'):
                break

            # Wait for 3 secs before collecting information again
            sleep(3)

    def mCheckIdemPotency(self):
        """
        This method checks for the existence of patchmgr session and read the
        output if running and return the exit status.
        Return/Exit code:
           PATCH_SUCCESS_EXIT_CODE   for success
           Any other error code other than PATCH_SUCCESS_EXIT_CODE for indicating 
           that patchmgr console log is not present.
          Non-zero for failure
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        _patchMgrObj = None

        '''
         Get list of domUs and it's required for bring up the domUs at the end.
         All of the Dom0s need to be considered for idempotency validations.
        '''
        for _dom0 in self.mGetCustomizedDom0List():
            '''
             All of the DomUs need to be considered for idempotency validations.
            '''
            self.__dom0s_list[_dom0] = self.mGetDomUListFromXml(_dom0, aFromXmList=True)

        self.mPatchLogInfo(f'Launch Node = {self.mGetDom0ToPatchcellSwitches()}')

        _dom0_to_patch_cell = self.mGetDom0ToPatchcellSwitches()

        # create patchmgr object with bare minimum arguments
        _patchMgrObj = InfraPatchManager(aTarget=PATCH_CELL, aOperation=self.mGetTask(), aPatchBaseAfterUnzip=self.mGetCellSwitchesPatchBaseAfterUnzip(),
                                   aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

        # Read patchmgr console output if that file is only present, otherwise, we should let regular patch run
        if _patchMgrObj.mIsPatchMgrConsoleOutputFileExists(aLaunchNode=_dom0_to_patch_cell):
            _patchMgrObj.mSetLaunchNode(aLaunchNode=_dom0_to_patch_cell)
            _patchMgrObj.mSetTimeoutInSeconds(aTimeoutInSeconds=self.__cell_patchmgr_timeout_in_sec)

            _patchMgrObj.mWaitForPatchMgrCmdExecutionToComplete()

            self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")
            _ret = _patchMgrObj.mGetStatusCode()
        else:
            # Indicate that no patchmgr run was attempted with this request id. In that case,
            # we should have regular patch run in the caller of this function.
            _ret = PATCHMGR_CONSOLE_LOG_MISSING
            self.mPatchLogWarn(
                f'Not found patchmgr console output file: {_patchMgrObj.mGetPatchMgrConsoleOutputFile()}')
            return _ret

        #Recreate the node_list file for cell cleanup for retry
        _input_file_retry_case = _patchMgrObj.mCreateNodesToBePatchedFile(aLaunchNode=_dom0_to_patch_cell,
            aHostList=self.mGetCustomizedCellList())

        _list_of_cells_retry_case = _patchMgrObj.mGetNodeListFromNodesToBePatchedFile(aHost=_dom0_to_patch_cell)

        # Run cleanup to get diagnosis files.

        """
         If patch failed, and cleanup failed then mark patch failed with PATCH error
         code.
         If patch success and cleanup failed then mark patch as failure with CLEANUP
         error code.
         If patch failed, but cleanup success, then mark patch failed with PATCH error
         code.
        """
        if _ret != PATCH_SUCCESS_EXIT_CODE: #Patch Failed
            _suggestion_msg = f"Patch exited with non-zero status on launch node : {str(_dom0_to_patch_cell)}"
            _ret = CELL_PATCH_FAILED
            # Not bothered about return condition , since Patch failure error code has higher priority
            self.mCellsCleanUp(_input_file_retry_case, self.mGetCallBacks())
            self.mAddError(_ret, _suggestion_msg)
        else: #Patch success
            _ret = self.mCellsCleanUp(_input_file_retry_case, self.mGetCallBacks())
            if _ret == PATCH_CELL_CLEANUP_FAILED:
                _suggestion_msg = f"Cell cleanup failed even after retry on list of cells : {str(_list_of_cells_retry_case)}."
                self.mAddError(_ret, _suggestion_msg)

        # Clean the environment: Delete passwordless, delete input file
        self.mCleanEnvironment(self.mGetDom0ToPatchcellSwitches(), _list_of_cells_retry_case,
                                _input_file_retry_case, self.mGetCellSwitchesPatchBaseAfterUnzip(),
                                self.mGetPatchmgrLogPathOnLaunchNode(), PATCH_CELL, _ret)
        # Turn on vms
        if self.mGetShutDownServices():
            if not self.mVMOperation('start'):
                self.mPatchLogError("mCheckIdemPotency: Start VMs during cell non-rolling upgrade failed.")

        return _ret

    def mGatherCellPreCheckData(self, aCellsList):
        """
        Get/Return the cells data before running any patch task. This data will be used in the postcheck.
        """
        _data = {}

        for _cell in aCellsList:
            _data[_cell] = {'version':          None,
                            'cell_services':    {}}

            # Update status
            self.mUpdatePatchStatus(True, STEP_GATHER_NODE_DATA,_cell)

            self.mPatchLogInfo(f'Starting  basic data check in cell {_cell}')

            _data[_cell]['version'] = self.mGetCluPatchCheck().mCheckTargetVersion(_cell, PATCH_CELL)
            _data[_cell]['cell_services'] = self.mGetCluPatchCheck().mCheckCellServices(_cell)

        return _data

    def mCellsCleanUp(self, aListFilePath, aCallbacks):
        """
        Runs the cell clean up to generate the diagnosis files.
        Return/Exit code:
          Zero for success
          Non-zero for failure
        """
        # Update status
        self.mUpdatePatchStatus(True, STEP_CLEAN_UP)
        _exit_code = 0
        _rc = PATCH_SUCCESS_EXIT_CODE
        _patchMgrObj = None

        _patchMgrObj = InfraPatchManager(aTarget=PATCH_CELL, aOperation=STEP_CLEAN_UP, aPatchBaseAfterUnzip=self.mGetCellSwitchesPatchBaseAfterUnzip(),
                                   aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

        # set the  patchmgr node list file
        _patchMgrObj.mSetNodesToBePatchedFile(aNodesToBePatchedFile=aListFilePath)

        # prepare the patchmgr command for execution using the InfraPatchManager object
        _cell_cleanup_cmd = _patchMgrObj.mGetPatchMgrCmd()

        # Connect to Dom0
        _dom0 = exaBoxNode(get_gcontext())
        self.mSetConnectionUser(_dom0)
        try:
            _dom0.mConnect(aHost=self.mGetDom0ToPatchcellSwitches())
            # Execute cleanup
            _dom0.mExecuteCmdAsync(_cell_cleanup_cmd, aCallbacks)
            _exit_code = int(_dom0.mGetCmdExitStatus())
            if _exit_code != 0:
                _max_retry_check_for_folder_counter = self.mGetExacloudPatchmgrRetryCleanupCheckMaxCounterValue()
                _retry_check_for_folder_counter = _max_retry_check_for_folder_counter
                _counter_to_display_iteration_count = 0
                while _retry_check_for_folder_counter > 0:
                    # Execute cleanup again
                    _dom0.mExecuteCmdAsync(_cell_cleanup_cmd, aCallbacks)
                    _exit_code = int(_dom0.mGetCmdExitStatus())
                    _counter_to_display_iteration_count += 1
                    self.mPatchLogInfo(
                        f"Performing Patchmgr cleanup for {_counter_to_display_iteration_count:d} iteration(s), maximum number of retries = {_max_retry_check_for_folder_counter:d}")
                    if _exit_code != 0:
                        # Retry cleanup. See bug 23341346
                        self.mPatchLogError(
                            f"Cleanup failed with exit_code={_exit_code:d}. Waiting for {SLEEP_CELL_PATCHMGR_CLEANUP_IN_SECONDS:d} seconds before retry.")
                        sleep(SLEEP_CELL_PATCHMGR_CLEANUP_IN_SECONDS)
                        _retry_check_for_folder_counter -= 1
                    else:
                        self.mPatchLogInfo(
                            f"Patchmgr cleanup succeeded after {_counter_to_display_iteration_count:d} retries")
                        break

                if _retry_check_for_folder_counter == 0 and _exit_code != 0:
                    self.mPatchLogWarn(f"Cleanup failed with exit_code={_exit_code:d} during retry.")
                    _rc = PATCH_CELL_CLEANUP_FAILED

        except Exception as e:
            self.mPatchLogError(f"Error while executing patchmgr cleanup commands. \n\n {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())

        finally:
            if _dom0.mIsConnected():
                _dom0.mDisconnect()

            return _rc

    def mVMOperation(self, aAction):
        '''
        This function try to shutdown and startup baased on the action.
        Also, it perform VM operation on all dom0 in parallel.
        Return
           True  -->  if VM operation is succesful.
           False -->  if it's failed to do the VM start/shutdown.
        '''

        _rc_all = True
        _rc = PATCH_SUCCESS_EXIT_CODE
        if aAction == 'shutdown':

            _dom0domU = []
            _dom0domuListMap = {}
            for _dom0 in self.mGetCustomizedDom0List():
                _domUs_within_dom0 = self.mGetDomUListFromXml(_dom0, aFromXmList=True)
                _dom0domuListMap[_dom0] = _domUs_within_dom0
                for _domu in _domUs_within_dom0:
                    _dom0domU.append([_dom0,_domu])

            if self.isParallelShutdownofAllVMAcrossAllDom0Enabled():
                self.mPatchLogInfo("Parallely shutting dom0 all domu across all dom0.")
                _rc = self.mParallelDomUShutdownAcrossAllDom0(_dom0domU)
            else:
                self.mPatchLogInfo("Parallely shutting down domu only for a specific dom0.")
                # _dom0domuListMap is a mapping of all dom0 to a list of domus within the dom0
                _rc = self.mParallelShutdownAllDomUinDom0(self.mGetCustomizedDom0List(), _dom0domuListMap)
            if _rc != PATCH_SUCCESS_EXIT_CODE:
                _rc_all = False
                return _rc_all

        if aAction == 'start':
            _processes = ProcessManager()
            _rc_status = _processes.mGetManager().list()
            _process = None
            for _dom0 in self.mGetCustomizedDom0List():
                self.mUpdatePatchStatus(True, STEP_START_VMS, _dom0)
                self.__dom0s_list[_dom0] = self.mGetDomUListFromXml(_dom0, aFromXmList=True)
                self.mPatchLogInfo(f"Dom0 = {_dom0}, DomUs within dom0 = {self.__dom0s_list[_dom0]}")
                _process = ProcessStructure(self.mGetCluPatchCheck().mManageVMs,
                                            [_dom0, self.__dom0s_list[_dom0], aAction, _rc_status], _dom0)

                _process.mSetMaxExecutionTime(self.mGetVmExecutionTimeoutInSeconds())
                _process.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
                _process.mSetLogTimeoutFx(self.mPatchLogWarn)
                _processes.mStartAppend(_process)

            _processes.mJoinProcess()

            # Validate the return codes of stop.
            for _node_status in _rc_status:
                if _node_status['status'] == 'failed':
                    _rc_all &= False
                    self.mPatchLogError(f"Shutdown of VM '{_node_status['domu']}' is not successfull.")

        return _rc_all

    def mPatchCellsRollingNonRolling(self, aPatchMgrObj):
        """
        Runs the cells patch operations in Rolling or Non-rolling mode.
        Return code:
          Zero for success
          Non-zero for failure
        """

        _task_type = self.mGetTask()
        _node_type = PATCH_CELL
        _patchMgrObj = aPatchMgrObj

        if not self.mGetDom0ToPatchcellSwitches():
            _suggestion_msg = f"Launch node is either down or patches are not staged, unable to proceed with {PATCH_CELL} operation on {_task_type} target."
            _ret = CELL_PATCH_FILES_MISSING
            self.mAddError(_ret, _suggestion_msg)
            return _ret

        _exit_code = 0
        _patchmgr_cmd = ""

        # Update status
        self.mUpdatePatchStatus(True, STEP_RUN_PATCH_CELL)

        # prepare the patchmgr command for execution using the InfraPatchManager object
        _patchmgr_cmd = _patchMgrObj.mGetPatchMgrCmd()

        # run patchmgr
        _patchMgrObj.mSetLaunchNode(aLaunchNode=self.mGetDom0ToPatchcellSwitches())

        _node = exaBoxNode(get_gcontext())
        # in case of cell non-rolling patching, we need to shutdown edv and esnp in all dom0's
        # it is a best effort, if it fails, it will caught in patchmgr
        # Even if it is not setup, cmd returns success
        '''
        [root@sea201323exdd007 ~]# dbmcli -e 'alter dbserver shutdown services edv'
        Stopping EDV services...
        The SHUTDOWN of EDV services was successful.
        [root@sea201323exdd007 ~]# dbmcli -e 'alter dbserver shutdown services esnp'
        Stopping ESNP services...
        The SHUTDOWN of ESNP services was successful.

        chcluster --shutdown is called in prepareEsOfflineUpgrade.sh, called by patchmgr
        '''
        if self.mIsKvmEnv() and self.mGetShutDownServices() and _task_type in [ TASK_PATCH ]:
            _list_done = []
            for _dom0 in self.mGetCustomizedDom0List():
                try:
                    if _dom0 in _list_done:
                        continue
                    _list_done.append(_dom0)
                    _node.mConnect(aHost=_dom0)
 
                    _edv_status_cmd = "dbmcli -e 'list dbserver attributes edvStatus' | grep running"
                    _esnp_status_cmd = "dbmcli -e 'list dbserver attributes esnpStatus' | grep running"

                    _i,_o,_e = _node.mExecuteCmd(_edv_status_cmd)
                    
                    if _o:
                        _outEdv = _o.read()
                    
                    _i,_o,_e =_node.mExecuteCmd(_esnp_status_cmd)
              
                    if _o:
                        _outEsnp = _o.read()

                    if _outEdv and ("running" in _outEdv):
                        _node.mExecuteCmdLog("dbmcli -e 'alter dbserver shutdown services edv'")
                        if _node.mGetCmdExitStatus() != 0:
                            _suggestion_msg = "Error occurred in dbmcli during EDV service startup for non-rolling cell patching."
                            _ret = DBMCLI_COMMAND_EXECUTION_FAILED
                            self.mAddError(_ret, _suggestion_msg)
                            return _ret
                    if _outEsnp and ("running" in _outEsnp):
                        _node.mExecuteCmdLog("dbmcli -e 'alter dbserver shutdown services esnp'")
                        if _node.mGetCmdExitStatus() != 0:
                            _suggestion_msg = "Error occurred in dbmcli during ESNP service startup for non-rolling cell patching"
                            _ret = DBMCLI_COMMAND_EXECUTION_FAILED
                            self.mAddError(_ret, _suggestion_msg)
                            return _ret
                    
                except Exception as e:
                    _suggestion_msg = f"Exception in dbmcli while shutting down EDV or ESNP services for non-rolling cell patching {str(e)}"
                    self.mPatchLogError(_suggestion_msg)
                    _ret = DBMCLI_COMMAND_EXECUTION_FAILED
                    self.mAddError(_ret, _suggestion_msg)
                    return _ret
                finally:
                    if _node.mIsConnected():
                        _node.mDisconnect()

        _exit_code = _patchMgrObj.mExecutePatchMgrCmd(aPatchMgrCmd=_patchmgr_cmd)
        if _exit_code != PATCH_SUCCESS_EXIT_CODE:
            return _exit_code   

        # Capture time profile details
        self.mPopulateInfrapatchingTimeStatsEntries(aNewStage="PATCH_MGR", aNewSubStage="", aNewStageNodes=str(self.__patchable_cells),aCompletedStage="PRE_PATCH", aCompletedSubStage="")

        # Monitor console log
        _patchMgrObj.mSetTimeoutInSeconds(aTimeoutInSeconds=self.__cell_patchmgr_timeout_in_sec)
        if _task_type in [ TASK_PATCH, TASK_ROLLBACK ]:
            _patchMgrObj.mWaitForPatchMgrCmdExecutionToComplete(aInputListFile=_patchMgrObj.mGetNodesToBePatchedFile(), aPatchStates=STEP_RUN_PATCH_CELL)
        else:
            _patchMgrObj.mWaitForPatchMgrCmdExecutionToComplete()

        self.mPatchLogInfo("Finished waiting for Patch Manager command execution. Starting to handle exit code from Patch Manager")
        _exit_code = _patchMgrObj.mGetStatusCode()

        self.mPopulateInfrapatchingTimeStatsEntries(aNewStage="POST_PATCH", aNewSubStage="",
                                                    aNewStageNodes=str(self.__patchable_cells),
                                                    aCompletedStage="PATCH_MGR", aCompletedSubStage="")
     
        self.mPatchLogInfo(f'Infra Patching exit_code = {_exit_code}')

        return _exit_code

    def mOrderCells(self, aNodesList):
        """
        This function orders the cells in the rack according the partnership between them
        Return lists:
           1) if cells total is lower than 7 (MINIMUM_CELLS_TO_REORDER) then the same list not ordered.
           2) otherwise the cells are reordered
        Example:
            Cells order by name
              index
                0.  scaqae01celadm01.us.oracle.com (Iteration 1)
                1.  scaqae01celadm02.us.oracle.com (Iteration 6)
                2.  scaqae01celadm03.us.oracle.com (Iteration 4)
                3.  scaqae01celadm04.us.oracle.com (Iteration 2)
                4.  scaqae01celadm05.us.oracle.com (Iteration 7)
                5.  scaqae01celadm06.us.oracle.com (Iteration 5)
                6.  scaqae01celadm07.us.oracle.com (Iteration 3)

            - Iteration 1 (index 0)
                1. scaqae01celadm01.us.oracle.com
            - Iteration 2 (index 3)
                1. scaqae01celadm01.us.oracle.com
                2. scaqae01celadm04.us.oracle.com
            - Iteration 3 (index 6)
                1. scaqae01celadm01.us.oracle.com
                2. scaqae01celadm04.us.oracle.com
                3. scaqae01celadm07.us.oracle.com
            - Iteration 4 (index 9 [Out of bounds 9 - 7 = 2])
                1. scaqae01celadm01.us.oracle.com
                2. scaqae01celadm04.us.oracle.com
                3. scaqae01celadm07.us.oracle.com
                4. scaqae01celadm03.us.oracle.com
            - Iteration 5 (index 5)
                1. scaqae01celadm01.us.oracle.com
                2. scaqae01celadm04.us.oracle.com
                3. scaqae01celadm07.us.oracle.com
                4. scaqae01celadm03.us.oracle.com
                5. scaqae01celadm06.us.oracle.com
            - Iteration 6 (index 8 [Out of bounds 8 - 7 = 1])
                1. scaqae01celadm01.us.oracle.com
                2. scaqae01celadm04.us.oracle.com
                3. scaqae01celadm07.us.oracle.com
                4. scaqae01celadm03.us.oracle.com
                5. scaqae01celadm06.us.oracle.com
                6. scaqae01celadm02.us.oracle.com
            - Iteration 7 (index 4)
                1. scaqae01celadm01.us.oracle.com
                2. scaqae01celadm04.us.oracle.com
                3. scaqae01celadm07.us.oracle.com
                4. scaqae01celadm03.us.oracle.com
                5. scaqae01celadm06.us.oracle.com
                6. scaqae01celadm02.us.oracle.com
                7. scaqae01celadm05.us.oracle.com
        """
        _nodes_ordered = []
        _nodes_to_patch = []
        if aNodesList:
            _nodes_to_patch = aNodesList
            _nodes_to_patch.sort()
            _total_cells = len(_nodes_to_patch)
            _index = 0
            while True:
                # Finish the loop
                if len(_nodes_ordered) == _total_cells:
                    break
                # Iteration 1
                elif _index == 0:
                    _nodes_ordered.append(_nodes_to_patch[_index])
                else:
                    # If _index is out of bounds
                    if _index >= _total_cells:
                        _index = _index - _total_cells
                    # If cell is already added, go next _index
                    if _nodes_to_patch[_index] in _nodes_ordered:
                        _index = _index + 1
                        continue
                    else:
                        _nodes_ordered.append(_nodes_to_patch[_index])
                _index = _index + 3
            self.mPatchLogInfo(f"Cells reordered: {_nodes_ordered}")
        return _nodes_ordered

    def mRegularPatchRun(self):
        """
        This function is to run the patchmgr with regular flow and take
         appropriate action
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
        _precheck_data   = {}
        _task_type = self.mGetTask()
        _discarded = []
        _patchMgrObj = None
        # Get list of all the cells in the cluster for regular patch flow (but not in patch retry)
        # After subset(IncludeNodeList) node patching feature implementation, get only custom node 
        # list for patch operations.
        _cell_count = self.mGetCellCount()
        if not _cell_count:
            _cell_count = 0
        _cell_to_patch = []
        _total_of_cells = self.mGetCellList()
        if len(_total_of_cells) < MINIMUM_NUMBER_OF_CELLS_REQUIRED_TO_REORDER and _task_type not in [TASK_PATCH]:
            _cell_to_patch = self.mGetCustomizedCellList()
        else:
            _ordered_cells = self.mOrderCells(_total_of_cells)
            _cell_to_patch = _ordered_cells
            if len(self.mGetIncludeNodeList()) > 0 and _cell_count == 0:
                _include_node_list = self.mGetIncludeNodeList()
                _cell_to_patch = [i for i in _ordered_cells if i in _include_node_list]
        _ret, _suggestion_msg, _list_of_cells, _discarded = self.mFilterNodesToPatch(_cell_to_patch, PATCH_CELL, _task_type)
        if _ret != PATCH_SUCCESS_EXIT_CODE:
            self.mAddError(_ret, _suggestion_msg)
            return _ret, _no_action_taken

        if self.mGetTask() in [TASK_ROLLBACK, TASK_ROLLBACK_PREREQ_CHECK] and len(_list_of_cells) > 0:
            '''
             Check if rollback is possible on filtered 
             list of cells.
            '''
            self.mvalidateCellEligibilityForRollback(_list_of_cells)

        # Update the list of list that are going to be patched
        self.__patchable_cells = _list_of_cells[:]

        if _task_type in [TASK_PATCH] and _cell_count > 0:
            _list_of_cells = _list_of_cells[:_cell_count]
            self.__patchable_cells = _list_of_cells[:]
            self.mPatchLogInfo(
                f'List of Nodes to be patched based on Cell Count {str(_cell_count)} is {str(_list_of_cells)} ')

        # Rotate SSH Keys
        _exakmsEndpoint = ExaKmsEndpoint(None)
        for _node in self.__patchable_cells:
            if _node:
                _exakmsEndpoint.mSingleRotateKey(_node)

        # Set initial Patch Status Json.
        if _cell_count > 0:
            """
            When CellCountFromCP is passed in the payload, the node progress data should contain only cells being patched..
            Note: If more no of cells (say 64+ cells) need to be patched using gmr, since only one node data(currently CellCountFromCP is 1)
            is sent in the node_progress_data and no data for already up to date nodes, storing node_progress_data(patch_list) in db
            will not cause any issue 
            """
            self.mUpdatePatchProgressStatus(aNodeList=_list_of_cells)
        else:
            self.mUpdatePatchProgressStatus(aNodeList=_list_of_cells, aDiscardedNodeList=_discarded)

        if len(_discarded) > 0 and _task_type not in [TASK_PREREQ_CHECK, TASK_ROLLBACK_PREREQ_CHECK]:
            _ret = self.mCustomCheck(_discarded)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                _suggestion_msg = f"Although cell nodes '{_discarded}' are on requested version, required services are not running."
                _ret = CELL_SERVICES_NOT_RUNNING
                self.mAddError(_ret, _suggestion_msg)
                _no_action_taken += 1
                return _ret, _no_action_taken

        if len(_list_of_cells) > 0:
            # Init extra process that will look for cell information to keep status updated
            self.__process = Process(target=self.mUpdateTaskFile)
            self.__process.start()

            '''
             Collect the precheck data before the upgrade/rollback and 
             same would be compare against the result after the 
             patching.
            '''

            # Gather precheck data
            if _task_type not in [TASK_PREREQ_CHECK, TASK_ROLLBACK_PREREQ_CHECK]:
                _precheck_data = self.mGatherCellPreCheckData(_list_of_cells)

            # Check cell services for the below cellcli commands to work
            for _cell in _list_of_cells:
                if not self.mGetCluPatchCheck().mCheckCellServices(_cell, aCheckRunning=True):
                    _suggestion_msg = f"Cell services seems to be not up on cell {_cell}. Please verify the cell service functionality."
                    _ret = CELL_SERVICES_NOT_RUNNING
                    self.mAddError(_ret, _suggestion_msg)
                    _no_action_taken += 1
                    return _ret, _no_action_taken
                self.mPatchLogDebug(f"Cell services on {_cell} are up and running.")

            #Validate readability of ipmiservice state during precheck
            #Not enabling it during precheck even if its disabled.
            #Only checking the readability.
            if _task_type in [TASK_PREREQ_CHECK, TASK_ROLLBACK_PREREQ_CHECK]:
                _ret , _val_failed_nodes  = self.mValidateServiceStateOnIlom(_list_of_cells)
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    _suggestion_msg = f"Error in reading ipmi service state value of ilom on nodes : {_val_failed_nodes}"
                    self.mAddError(_ret, _suggestion_msg)
                    _no_action_taken += 1
                    return _ret, _no_action_taken
            
            # Prepare environment: passwordless between dom0 and cells
            _key = self.mPrepareEnvironment(self.mGetDom0ToPatchcellSwitches(), _list_of_cells,
                                                           self.mGetCellSwitchesPatchBaseAfterUnzip())

            '''
             Perform space validations on root partition
             on Cell targets
            '''
            _ret = self.mValidateRootFsSpaceUsage(_list_of_cells)
            if _ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since Return code from mValidateRootFsSpaceUsage is {_ret} ")
                return _ret , _no_action_taken

            # create patchmgr object with bare minimum arguments
            _patchMgrObj = InfraPatchManager(aTarget=PATCH_CELL, aOperation=_task_type, aPatchBaseAfterUnzip=self.mGetCellSwitchesPatchBaseAfterUnzip(),
                                       aLogPathOnLaunchNode=self.mGetPatchmgrLogPathOnLaunchNode(), aHandler=self)

            # now set the component's operation specific arguments
            _patchMgrObj.mSetOperationStyle(aOperationStyle=self.mGetOpStyle())

            # create patchmgr nodes file
            _input_file = _patchMgrObj.mCreateNodesToBePatchedFile(aLaunchNode=self.mGetDom0ToPatchcellSwitches(), aHostList=_list_of_cells)

            # Skip patchmgr existence check during clusterless patching.
            if self.mPerformPatchmgrExistenceCheck():
                # check for patchmgr session existence
                _patchMgrObj.mSetLaunchNode(aLaunchNode=self.mGetDom0ToPatchcellSwitches())

                _ret, _patchmgr_active_node = _patchMgrObj.mCheckForPatchMgrSessionExistence()
                if _ret == PATCHMGR_SESSION_ALREADY_EXIST:
                    return _ret, _no_action_taken

            # if rolling upgrade, check asmdeactivationoutcome
            if not self.mGetShutDownServices():
                self.mPatchLogInfo("Verifying ASM deactivationoutcome for cells to be patched in Rolling mode.")
                if not self.mGetCluPatchCheck().mVerifyGriddiskDeactivationOutcome(_list_of_cells, self.mGetOpStyle()):
                    _suggestion_msg = f"Pre-patch check: ASM deactivationoutcome status is not 'Yes' in some of the cells : {str(_list_of_cells)} and the outcome is not successful."
                    _ret = CELL_ASMDEACTIVATION_OUTCOME_ERROR
                    self.mAddError(_ret, _suggestion_msg)
                    _no_action_taken += 1
                    return _ret, _no_action_taken

                self.mPatchLogInfo("ASM deactivationoutcome successful on all cells")

            # If non-rolling check for asmmodestatus, then shutdown vms and cell services
            if self.mGetShutDownServices():
                # Shutdown vms
                if not self.mVMOperation('shutdown'):
                    _suggestion_msg = "Shutdown VMs during cell non-rolling upgrade failed. Failure reason for shutdown of VM's needs to be investigated."
                    _ret = CELL_FAILED_TO_SHUTDOWN_VMS
                    self.mAddError(_ret, _suggestion_msg)
                    _no_action_taken += 1
                    return _ret, _no_action_taken

                self.mPatchLogInfo("Verifying ASM asmmodestatus for cells to be patched in non-rolling mode.")
                if not self.mGetCluPatchCheck().mVerifyGriddiskDeactivationOutcome(_list_of_cells, self.mGetOpStyle()):
                    _suggestion_msg = f"Pre-patch check: ASM asmmodestatus is still 'ONLINE' in some of the cells : {str(_list_of_cells)}."
                    _ret = CELL_ASM_MODE_STATUS_STILL_ONLINE_ERROR
                    self.mAddError(_ret, _suggestion_msg)
                    _no_action_taken += 1
                    return _ret, _no_action_taken

                self.mPatchLogInfo("ASM asmmodestatus successful on all cells")

            '''
             Enable service state on ilom prior to upgrade.
            '''
            if _task_type in [TASK_PATCH, TASK_ROLLBACK]:
                _ret , _val_failed_nodes  = self.mUpdateServiceStateOnIlom(_list_of_cells, "prepatch")
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    _suggestion_msg = f"Error in setting ipmi service state value of ilom on nodes : {_val_failed_nodes}"
                    self.mAddError(_ret, _suggestion_msg)
                    _no_action_taken += 1
                    return _ret, _no_action_taken

            # Run plugin metadata based exacloud plugins before patchmgr cmd
            if self.mGetTask() in [ TASK_PATCH ] and len(self.mGetPluginMetadata()) > 0:
                _plugin_metadata_based_exacloud_plugin_enabled, _ = checkPluginEnabledFromInfraPatchMetadata(self.mGetPluginMetadata())
                if _plugin_metadata_based_exacloud_plugin_enabled:
                    # Execute plugin metadata based exacloud plugins
                    self.mPatchLogInfo(
                        f"Executing Exacloud Plugins implicitly based on the infra patch plugin metadata during Pre-Patch stage and as part of {self.mGetOpStyle()} patching.")
                    _ret = self.mGetPluginHandler().mExacloudPluginMetadataExecutor(_list_of_cells, "pre")
                    if _ret != PATCH_SUCCESS_EXIT_CODE:
                        return _ret, _no_action_taken

            # Run patchmgr command
            _ret = self.mPatchCellsRollingNonRolling(_patchMgrObj)
            """
              If patch failed, and cleanup failed then mark patch failed with PATCH error
              code.
              If patch success and cleanup failed then mark patch as failure with CLEANUP
              error code.
              If patch failed, but cleanup success, then mark patch failed with PATCH error
              code.
            """
            if _ret != PATCH_SUCCESS_EXIT_CODE: #Patch Failed
                # In cases where a patch operation is unsuccessful due to cells not coming online after a reboot,
                # the subsequent cleanup operation may also fail due to these inactive cells. This process will
                # attempt retries up to 60 times before giving up. Therefore, it's important to verify the status
                # of the cells and update the cell input list appropriately before initiating the cleanup operation.
                _input_file = ""
                _reachableCellList = self.mCheckAndUpdateNodeList(_list_of_cells)
                if _reachableCellList:
                    _input_file = _patchMgrObj.mCreateNodesToBePatchedFile(aLaunchNode=self.mGetDom0ToPatchcellSwitches(), aHostList=_reachableCellList)

                # Not bothered about return condition , since Patch failure error code has higher priority
                if _input_file:
                    self.mCellsCleanUp(_input_file, self.mGetCallBacks())
            else: #Patch success
                _ret = self.mCellsCleanUp(_input_file, self.mGetCallBacks())
                if _ret == PATCH_CELL_CLEANUP_FAILED:
                    _suggestion_msg = f"Cell cleanup failed even after retry on the list of cells : {_list_of_cells}."
                    self.mAddError(_ret, _suggestion_msg)

            # Run plugin metadata based exacloud plugins before patchmgr cmd
            if self.mGetTask() in [ TASK_PATCH ] and len(self.mGetPluginMetadata()) > 0 and _ret == PATCH_SUCCESS_EXIT_CODE:
                _plugin_metadata_based_exacloud_plugin_enabled, _ = checkPluginEnabledFromInfraPatchMetadata(self.mGetPluginMetadata())
                if _plugin_metadata_based_exacloud_plugin_enabled:
                    # Execute plugin metadata based exacloud plugins
                    self.mPatchLogInfo(
                        f"Executing Exacloud Plugins implicitly based on the infra patch plugin metadata during Post-Patch stage and as part of {self.mGetOpStyle()} patching.")
                    _ret = self.mGetPluginHandler().mExacloudPluginMetadataExecutor(_list_of_cells, "post")
                    if _ret != PATCH_SUCCESS_EXIT_CODE:
                        return _ret, _no_action_taken

            # Clean the environment: Delete passwordless, delete input file
            self.mCleanEnvironment(self.mGetDom0ToPatchcellSwitches(), _list_of_cells, _input_file,
                                    self.mGetCellSwitchesPatchBaseAfterUnzip(), self.mGetPatchmgrLogPathOnLaunchNode(),
                                    PATCH_CELL, _ret)

            # Non-rolling: Bring up VMs if cell upgrade is failed so that computes/DB will be available for user.
            # Non-rolling: Bring up VMs if cell count greater than 0, MW is divided in a different actions.
            # If cell upgrade is successful, then we don't need to bring up VMs since dom0 non-rolling upgrade
            # will take care of bring up the VMs, subsequently. Otherwise, we would end up in starting/shutdown 
            # twice which is not affordable for dom0 and cell upgrade.
            # _cell_count variable is there only in case of granular maintenance and will be greater than 0
            if self.mGetShutDownServices() and (_cell_count > 0 or _ret != PATCH_SUCCESS_EXIT_CODE or _ret == PATCH_CELL_CLEANUP_FAILED):
                # start edv and esnp services on all dom0's in case of failure for non-rolling cell patching
                # if exascale is not configured, it will fail. It will be hard to address here any other failure so leaving analysis for 
                # upper layer
                _node = exaBoxNode(get_gcontext())
                if self.mIsKvmEnv() and self.mGetShutDownServices() and _task_type in [ TASK_PATCH ]:
                    _list_done = []
                    for _dom0 in self.mGetCustomizedDom0List():
                        try:
                            if _dom0 in _list_done:
                                continue
                            _list_done.append(_dom0)
                            _node.mConnect(aHost=_dom0)
                            _node.mExecuteCmdLog("dbmcli -e 'alter dbserver startup services esnp'")
                            if _node.mGetCmdExitStatus() != 0:
                                self.mPatchLogWarn("Error occurred in dbmcli during ESNP service startup for non-rolling cell patching.")
                            _node.mExecuteCmdLog("dbmcli -e 'alter dbserver startup services edv'")
                            if _node.mGetCmdExitStatus() != 0:
                                self.mPatchLogWarn("Error occurred in dbmcli during EDV service startup for non-rolling cell patching.")
                        except Exception as e:
                            self.mPatchLogWarn(f"Exception in dbmcli while starting up EDV or ESNP services for non-rolling cell patching {e}")
                        finally:
                            if _node.mIsConnected():
                                _node.mDisconnect()
                # TODO: Add config param to bring up the VMs in case of cell upgrade.
                #  e, we are trying to shutodwn or bring twice.
                if not self.mVMOperation('start'):
                    _suggestion_msg = "Start VMs during cell non-rolling upgrade failed. Check why starting of VMs has failed."
                    _ret = CELL_FAILED_TO_BRINGUP_VMS
                    self.mAddError(_ret, _suggestion_msg)
                    _no_action_taken += 1
                else:
                    self.mPatchLogInfo("Start VMs during cell non-rolling upgrade successfully.")
            elif _task_type not in [TASK_PREREQ_CHECK, TASK_ROLLBACK_PREREQ_CHECK]:
                self.mPatchLogInfo("Cell upgrade is success. No need to bring up the VMs, because dom0 upgrade will bringup the VMs.")

            # Do postchecks
            _wait_before_post_check = False
            if _task_type in [TASK_PATCH, TASK_ROLLBACK]:
                _wait_before_post_check = True

            '''
             After the cell upgrade/rollback, do the postcheck and 
             compare the result against the precheck data collected 
             before patching/rollback.
            '''
            if _task_type not in [TASK_PREREQ_CHECK, TASK_ROLLBACK_PREREQ_CHECK] and _ret == PATCH_SUCCESS_EXIT_CODE:
                _ret = self.mDoCellPostCheck(_precheck_data, _task_type, aWait=_wait_before_post_check)

        else:
            _no_action_taken += 1
            # We need to populate more info about the patching operation when
            # no action is required and it requires to update ecra rack
            # status to previous
            _suggestion_msg = "No available cell nodes to run the patchmgr. Nothing to do here."
            self.mAddError(_ret, _suggestion_msg)

        return _ret, _no_action_taken

    def mDoCellPostCheck(self, aCellsData, aTaskType, aWait=True):
        """
        Runs a basic postcheck in the cells. It compares the data taken before running the patchmgr.
        Return
           PATCH_SUCCESS_EXIT_CODE  --> If everything is success
           Any other code other than PATCH_SUCCESS_EXIT_CODE --> if post check is 
           failed in any of the cells.
        """

        # Sleep for 5 minutes before checking. Image status check may fail if we don't wait
        if aWait:
            # Update status
            self.mUpdatePatchStatus(True, STEP_POSTCHECKS, "waiting for 5 min to start")
            self.mPatchLogInfo('Waiting for 5 minutes before running the postcheck')
            sleep(SLEEP_CELL_WAIT_BEFORE_POSTCHECK_IN_SECONDS)

        def _check_cell(aCell, aData):
            # Ping host
            if not self.mGetCluPatchCheck().mPingNode(aCell):
                _suggestion_msg = f"Cell ping failure : {aCell}"
                _ret = CELL_PING_FAILED
                self.mAddError(_ret, _suggestion_msg)
                return False, _ret

            # Check target version
            _rc = self.mGetCluPatchCheck().mCheckTargetVersion(aCell, PATCH_CELL, aData['version'])

            if aTaskType == TASK_PATCH:
                if _rc <= 0:
                    _suggestion_msg = f"Current version on the cell is expected to be higher than original version for cell : {aCell}"
                    _ret = CELL_CURRENT_VERSION_EXPECTED_HIGHER_THAN_ORIGINAL_VERSION
                    self.mAddError(_ret, _suggestion_msg)
                    return False, _ret

            elif aTaskType == TASK_ROLLBACK:
                if _rc >= 0:
                    _suggestion_msg = f"Current version on the cell is expected to be lower than original version : {aCell}"
                    _ret = CELL_CURRENT_VERSION_EXPECTED_LOWER_THAN_ORIGINAL_VERSION
                    self.mAddError(_ret, _suggestion_msg)
                    return False, _ret

            else:
                if _rc != 0:
                    _suggestion_msg = f"Current version on the cell is expected to be equal to original version : {aCell}"
                    _ret = CELL_CURRENT_VERSION_EXPECTED_EQUAL_TO_ORIGINAL_VERSION
                    self.mAddError(_ret, _suggestion_msg)
                    return False, _ret

            # Check image status
            if not self.mGetCluPatchCheck().mCheckImageSuccess(aCell):

                # Get error messages from /var/log/cellos/validations.log /var/log/cellos/vldrun.*.log
                _errors = 'validations.log/vldrun.*.log output:\n'

                _cell = exaBoxNode(get_gcontext())
                _cell.mConnect(aHost=aCell)
                _i, _o, _e = _cell.mExecuteCmd("grep -as '\[ERROR\|\[FAIL' /var/log/cellos/validations.log" \
                                               " /var/log/cellos/vldrun.*.log")
                _output = _o.readlines()
                if _output:
                    _errors += str("".join(_output))
                _cell.mDisconnect()
                _suggestion_msg = f"Image status not successful in cell : {_errors}"
                _ret = CELL_IMAGE_STATUS_NOT_SUCCESSFUL
                self.mAddError(_ret, _suggestion_msg)
                return False, _ret

            # Check for Fedramp configurtion and restore relevant files
            if self.mGetFedRamp() == 'ENABLED' and aTaskType in [TASK_PATCH, TASK_ROLLBACK]:
                self.mFedrampRestoreConfig("cells")

            # Check cell services"
            if not self.mGetCluPatchCheck().mCheckCellServices(aCell, aData['cell_services']):
                if not self.mGetCluPatchCheck().mCheckCellServices(aCell, aData['cell_services'], aCheckRunning=True):
                    _suggestion_msg = f"Cell services are not up in {aCell}"
                    _ret = CELL_SERVICES_NOT_RUNNING
                    self.mAddError(_ret, _suggestion_msg)
                    return False, _ret

            # check for ListeningInterface
            if aTaskType in [TASK_PATCH]:
                # Check for listeningInterface
                _ret = self.mCheckListeningInterface(aCell, aData['cell_services'])
                if _ret != PATCH_SUCCESS_EXIT_CODE:
                    return False, _ret

            return True, PATCH_SUCCESS_EXIT_CODE

        _rc = PATCH_SUCCESS_EXIT_CODE
        _ret = True
        _failure_history_code = PATCH_SUCCESS_EXIT_CODE

        for _cell in aCellsData.keys():
            # Update status
            self.mUpdatePatchStatus(True, STEP_POSTCHECKS, _cell)
            # Start check
            self.mPatchLogInfo(f'Starting basic postcheck in cell {_cell}')
            _out, _error_code = _check_cell(_cell, aCellsData[_cell])
            if _out:
                self.mPatchLogInfo(f"Successful postcheck in cell {_cell}")
            
            _ret &= _out
            if _error_code != PATCH_SUCCESS_EXIT_CODE:
                _failure_history_code = _error_code

        # Consolidate and return Error code for all cells.
        if not _ret:
            _rc = _failure_history_code

        return _rc

    def mPreCheck(self):
        """
        Does the custom check, setup, idempotency check and then run the patch
        precheck of cell upgrade.
        Return codes:
           1) ret -->
               0 for success
               non-zero for failure
           2)  _no_action_taken -->
               0 indicate some action is taken care.
               non-zero indicate no action is taken care.
        """
        ret = PATCH_SUCCESS_EXIT_CODE
        _rc = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0
        _task_type = self.mGetTask()

        try:
            self.mPatchLogInfo(
                f"\n\n---------------> Starting {_task_type} in {PATCH_CELL} <---------------\n\n")

            # Run independent postcheck method before proceeding with Prereq.
            ret = self.mCustomCheck()
            if ret != PATCH_SUCCESS_EXIT_CODE:
                return ret, _no_action_taken

            # 1. Set up environment
            ret = self.mSetEnvironment()
            if ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since return code from mSetEnvironment is {ret} ")
                return ret, _no_action_taken

            # 2. Check for idempotency
            if self.mPatchRequestRetried():
                ret = self.mCheckIdemPotency()
                if ret != PATCH_SUCCESS_EXIT_CODE:
                    # 3. Check for Regular patch run
                    self.mPatchLogWarn("Initiating regular patch prereq operation")
                    ret, _no_action_taken = self.mRegularPatchRun()
            else:
                # 3. Check for Regular patch run
                ret, _no_action_taken = self.mRegularPatchRun()

            self.mPatchLogInfo(f"Task: {_task_type} - Type: {PATCH_CELL}\t\t[ ret_code = {ret} ]")
            if ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"{PATCH_CELL} '{_task_type}' failed. Patch execution stopped.")

            if ret == PATCH_SUCCESS_EXIT_CODE:
                self.mSetCellUpgradePassThroughFlag(True)

        except Exception as e:
            self.mPatchLogError(f"Exception in Running Cell PreCheck {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()
            
            if _child_request_error_already_exists_in_db:
                ret = _rc
            else:
                _suggestion_msg = f"Exception in Running Cell PreCheck {str(e)}"
                ret = CELL_PRECHECK_EXCEPTION
                self.mAddError(ret, _suggestion_msg)
                self.mPatchLogTrace(traceback.format_exc())

        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_CELL}s <---------------\n\n")
            return ret, _no_action_taken

    def mRollBackPreCheck(self):
        """
        Does the custom check, setup, idempotency check and then run the rollback
        precheck of cell upgrade.
        Return codes:
           1) ret -->
               0 for success
               non-zero for failure
           2)  _no_action_taken -->
               0 indicate some action is taken care.
               non-zero indicate no action is taken care.
        """
        ret = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0
        _task_type = self.mGetTask()

        try:
            self.mPatchLogInfo(
                f"\n\n---------------> Starting {_task_type} in {PATCH_CELL} <---------------\n\n")

            # Run independent postcheck method before proceeding with Prereq.
            _rc = self.mCustomCheck()
            if _rc != PATCH_SUCCESS_EXIT_CODE:
                return _rc, _no_action_taken

            # 1. Set up environment
            self.mSetEnvironment()

            # 2. Check for idempotency
            if self.mPatchRequestRetried():
                ret  = self.mCheckIdemPotency()
                # If patchmgr console output not found, then run regular patch
                if ret != PATCH_SUCCESS_EXIT_CODE:
                    # 3. Check for Regular patch run
                    self.mPatchLogWarn("Initiating regular rollback prereq operation")
                    ret, _no_action_taken = self.mRegularPatchRun()
            else:
                # 3. Check for Regular patch run
                ret, _no_action_taken = self.mRegularPatchRun()

            self.mPatchLogInfo(f"Task: {_task_type} - Type: {PATCH_CELL}\t\t[ ret_code = {ret} ]")
            if ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"{PATCH_CELL} '{_task_type}' failed. Patch execution stopped.")

            if ret == PATCH_SUCCESS_EXIT_CODE:
                self.mSetCellUpgradePassThroughFlag(True)

        except Exception as e:
            self.mPatchLogError(f"Exception in RollBack PreCheck: {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                ret = _rc
            else:
                _suggestion_msg = f"{PATCH_CELL} '{_task_type}' failed. Rollback Precheck execution stopped."
                ret = CELL_ROLLBACK_PRECHECK_EXCEPTION
                self.mAddError(ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_CELL}s <---------------\n\n")
            return ret, _no_action_taken

    def mPatch(self):
        """
        Does the setup, idempotency check and then run the patch.
        Return codes:
           1) ret -->
               0 for success
               non-zero for failure
           2)  _no_action_taken -->
               0 indicate some action is taken care.
               non-zero indicate no action is taken care.
        """
        ret = PATCH_SUCCESS_EXIT_CODE
        _rc = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0
        _task_type = self.mGetTask()

        try:
            self.mPatchLogInfo(
                f"\n\n---------------> Starting {_task_type} in {PATCH_CELL} <---------------\n\n")

            # 1. Set up environment
            ret = self.mSetEnvironment()
            if ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since return code from mSetEnvironment is {ret} ")
                return ret, _no_action_taken

            # 2. Check for idempotency
            if self.mPatchRequestRetried():
                ret  = self.mCheckIdemPotency()
                # If patchmgr console output not found, then run regular patch
                if ret != PATCH_SUCCESS_EXIT_CODE:
                    # 3. Check for Regular patch run
                    self.mPatchLogWarn("Initiating regular patch operation")
                    ret, _no_action_taken = self.mRegularPatchRun()
            else:
                # 3. Check for Regular patch run
                ret, _no_action_taken = self.mRegularPatchRun()

            self.mPatchLogInfo(f"Task: {_task_type} - Type: {PATCH_CELL}\t\t[ ret_code = {ret} ]")
            if ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"{PATCH_CELL} '{_task_type}' failed. Patch execution stopped.")

            if ret == PATCH_SUCCESS_EXIT_CODE:
                self.mSetCellUpgradePassThroughFlag(True)

        except Exception as e:
            self.mPatchLogError(f"Exception in Patch operation: {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                ret = _rc
            else:
                _suggestion_msg = f"{PATCH_CELL} '{_task_type}' failed. Patch execution stopped."
                ret = CELL_PATCH_EXCEPTION
                self.mAddError(ret, _suggestion_msg)

        finally:
            # Disable ServiceState on ilom post upgrade.
            if _task_type in [TASK_PATCH, TASK_ROLLBACK]:
                self.mUpdateServiceStateOnIlom(self.__patchable_cells, "postpatch")
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_CELL}s <---------------\n\n")
            return ret, _no_action_taken

    def mRollBack(self):
        """
        Does the setup, idempotency check and then run the rollback.
        Return codes:
           1) ret -->
               0 for success
               non-zero for failure
           2)  _no_action_taken -->
               0 indicate some action is taken care.
               non-zero indicate no action is taken care.
        """
        ret = PATCH_SUCCESS_EXIT_CODE
        _rc = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0
        _task_type = self.mGetTask()

        try:
            self.mPatchLogInfo(
                f"\n\n---------------> Starting {_task_type} in {PATCH_CELL} <---------------\n\n")

            # 1. Set up environment
            ret = self.mSetEnvironment()
            if ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"Exiting since return code from mSetEnvironment is {ret} ")
                return ret, _no_action_taken

            # 2. Check for idempotency
            if self.mPatchRequestRetried():
                ret  = self.mCheckIdemPotency()
                # If patchmgr console output not found, then run regular patch
                if ret != PATCH_SUCCESS_EXIT_CODE:
                    # 3. Check for Regular patch run
                    self.mPatchLogWarn("Initiating regular rollback operation")
                    ret, _no_action_taken = self.mRegularPatchRun()
            else:
                # 3. Check for Regular patch run
                ret, _no_action_taken = self.mRegularPatchRun()

            self.mPatchLogInfo(f"Task: {_task_type} - Type: {PATCH_CELL}\t\t[ ret_code = {ret} ]")
            if ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"{PATCH_CELL} '{_task_type}' failed. Patch execution stopped.")

            if ret == PATCH_SUCCESS_EXIT_CODE:
                self.mSetCellUpgradePassThroughFlag(True)

        except Exception as e:
            self.mPatchLogError(f"Exception in Rollback operation: {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                ret = _rc
            else:
                _suggestion_msg = f"{PATCH_CELL} '{_task_type}' failed. Rollback execution stopped."
                ret = CELL_ROLLBACK_EXCEPTION
                self.mAddError(ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_CELL}s <---------------\n\n")
            return ret, _no_action_taken

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
        ret = PATCH_SUCCESS_EXIT_CODE
        _rc = PATCH_SUCCESS_EXIT_CODE
        _no_action_taken = 0
        _task_type = self.mGetTask()

        try:
            self.mPatchLogInfo(
                f"\n\n---------------> Starting {_task_type} in {PATCH_CELL} <---------------\n\n")

            # Run independent postcheck method before proceeding with Prereq.
            ret = self.mCustomCheck()
            self.mPatchLogInfo(f"Task: {_task_type} - Type: {PATCH_CELL}\t\t[ ret_code = {ret} ]")
            if ret != PATCH_SUCCESS_EXIT_CODE:
                self.mPatchLogError(f"{PATCH_CELL} '{_task_type}' failed. Patch execution stopped.")

        except Exception as e:
            self.mPatchLogError(f"Exception in RollBack PreCheck: {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                ret = _rc
            else:
                _suggestion_msg = f"{PATCH_CELL} '{_task_type}' failed. Postcheck execution stopped."
                ret = CELL_POSTCHECK_EXCEPTION
                self.mAddError(ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_CELL}s <---------------\n\n")
            return ret, _no_action_taken

    def mOneOff(self):
        """
        This method suppose to run any user script staged by user on plugin area.
        Return code:
          PATCH_SUCCESS_EXIT_CODE for success
          Any other error code other than PATCH_SUCCESS_EXIT_CODE
          for failure.
        """

        _ret = PATCH_SUCCESS_EXIT_CODE

        self.mPatchLogInfo(f"\n\n---------------> Starting {TASK_ONEOFF} in {PATCH_CELL}s <---------------\n\n")
        try:
            # Check if oneoff is enabled by the framework
            # Get custom node list for oneoff operation
            if self.mGetPluginHandler() and self.mIsOneOffPluginEnabled():
                _node_list = self.mGetCustomizedCellList()
                self.mGetPluginHandler().mSetNodeList(_node_list)
                self.mGetPluginHandler().mSetPluginTarget(PATCH_CELL)

                #Execute oneoff plugin
                _ret = self.mGetPluginHandler().mApply()
                return _ret
            else:
                _ret = ONEOFF_APPLY_FAILED
                _suggestion_msg = TASK_ONEOFF.upper() + " plugin is unavailable for " + PATCH_CELL.upper()
                self.mAddError(_ret, _suggestion_msg)
                raise self.mPatchLogError(TASK_ONEOFF.upper() +
                                          " plugin is unavailable for " + PATCH_CELL.upper())
        except Exception as e:
            self.mPatchLogWarn(f"Exception in Running Cell OneOff Plugin {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())

            _rc, _child_request_error_already_exists_in_db = self.mGetErrorCodeFromChildRequest()

            if _child_request_error_already_exists_in_db:
                _ret = _rc
            else:
                _suggestion_msg = f"Exception in Running Cell OneOff Plugin {str(e)}"
                _ret = INDIVIDUAL_PATCH_REQUEST_EXCEPTION_ERROR
                self.mAddError(_ret, _suggestion_msg)

        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_CELL}s <---------------\n\n")
            return _ret

    def mOneOffv2(self):
        """
        This method suppose to run any user script staged by user on plugin area
        using the oneoff v2 implementation.
        
        Return code:

           PATCH_SUCCESS_EXIT_CODE for success.
           Any other error code other than PATCH_SUCCESS_EXIT_CODE for failure.
        """
        _ret = PATCH_SUCCESS_EXIT_CODE
        self.mPatchLogInfo(f"\n\n---------------> Starting {TASK_ONEOFFV2} on {PATCH_CELL}s <---------------\n\n")
        try:
            # Check if oneoff plugin is enabled by the framework
            if self.mGetPluginHandler() and self.mIsOneOffV2PluginEnabled():
                # Execute oneoff plugin
                _ret = self.mGetPluginHandler().mApply()
        except Exception as e:
            _suggestion_msg = f"Exception in Running Cell Oneoff V2 Plugin : {str(e)}"
            _ret = ONEOFFV2_EXCEPTION_ENCOUNTERED
            self.mAddError(_ret, _suggestion_msg)
            self.mPatchLogTrace(traceback.format_exc()) 
        finally:
            self.mPatchLogInfo(f"Log files are in {self.mGetLogPath()}")
            self.mPatchLogInfo(f"Final return code from task : {self.mGetTask()} is {_ret} ")
            self.mPatchLogInfo(
                f"\n\n---------------> Completed {self.mGetTask()} on {PATCH_CELL}s <---------------\n\n")
            return _ret

    def mPrePostCellCheck(self, aCellList):
        """
         This method performs basic sanity checks on all Cells in the
         clusters during Cell prereq and postcheck operartions. These
         checks are independent of previous checks.
             - return PATCH_SUCCESS_EXIT_CODE if success
             - return any other code other than PATCH_SUCCESS_EXIT_CODE if failure
        """

        _rc = PATCH_SUCCESS_EXIT_CODE
        '''
          Check cell services and ping check only during postcheck 
          stage they are checked at early stages of prereq while
          filtering the list of nodes and is a duplication
          of checks.
        '''
        for _cell in aCellList:

            if self.mGetTask() in [TASK_POSTCHECK]:
                # Ping status check
                if not self.mGetCluPatchCheck().mPingNode(_cell):
                    _suggestion_msg = f"Cell ping failure : {_cell}"
                    _rc = CELL_PING_FAILED
                    self.mAddError(_rc, _suggestion_msg)
                    return _rc

                # Cell Services validation check
                if not self.mGetCluPatchCheck().mCheckCellServices(_cell):
                    _suggestion_msg = f"Cell services are not up in {_cell}"
                    _rc = CELL_SERVICES_NOT_RUNNING
                    self.mAddError(_rc, _suggestion_msg)
                    return _rc

            # Check image status
            if not self.mGetCluPatchCheck().mCheckImageSuccess(_cell):
                _suggestion_msg = f"Image status not successful in cell : {_cell}"
                _rc = CELL_IMAGE_STATUS_NOT_SUCCESSFUL
                self.mAddError(_rc, _suggestion_msg)

                # Get error messages from /var/log/cellos/validations.log /var/log/cellos/vldrun.*.log
                _errors = 'validations.log/vldrun.*.log output:\n'

                _cel = exaBoxNode(get_gcontext())
                _cel.mConnect(aHost=_cell)
                _i, _o, _e = _cel.mExecuteCmd("grep -as '\[ERROR\|\[FAIL' /var/log/cellos/validations.log" \
                                               " /var/log/cellos/vldrun.*.log")
                _output = _o.readlines()
                if _output:
                    _errors += str("".join(_output))
                    self.mPatchLogError(f"Image status not successful in cell : {_cell}, {str(_errors)}")

                if _cel.mIsConnected():
                    _cel.mDisconnect()
                return _rc

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
          Otherwise, pre-defined non zero error code
        """

        # Enh 30208083 - Disallow patching if required/critical services
        # are not running on the upgraded node(s).
        _ret = PATCH_SUCCESS_EXIT_CODE
        if aNodes:
            _final_Cell_list = aNodes
        else:
            # Get list of all cells specified for patching(i.e custom node list)
            _final_Cell_list = self.mGetCustomizedCellList()

        # Below checks performed as part of independent
        # postcheck and on the upgraded cells.
        _ret = self.mPrePostCellCheck(_final_Cell_list)

        return _ret

    def mvalidateCellEligibilityForRollback(self, aListOfCellsToValidate):
        """
        This method parses the imageinfo command output prior to rollback
        to confirm if rollback can be performed on a given cell node.

         return
            - PATCH_SUCCESS_EXIT_CODE - if cells are eligible for rollback
            - CELL_NOT_ELIGIBLE_FOR_ROLLBACK in case of Rollback to the
              inactive partitions: Impossible error encountered.
        """
        def _validate_cell_possibility_of_rollback(aCell, aStatus):

            '''
             In case of a rollback not possible, imageinfo output 
             would indicate error as below.

             Inactive marker for the rollback: not found
             Inactive grub config for the rollback: not found
             Inactive usb grub config for the rollback: not found
             Inactive kernel version for the rollback: undefined
             Rollback to the inactive partitions: Impossible

             In case of a cell rollback possible.

             Inactive marker for the rollback: /boot/I_am_hd_boot.inactive
             Inactive grub config for the rollback: /boot/efi/EFI/redhat/grub.cfg.inactive
             Inactive usb grub config for the rollback:
             /boot/efi/EFI/redhat/grub.cfg.usb.inactive
             Inactive kernel version for the rollback: 4.14.35-2047.508.3.3.el7uek.x86_64
             Rollback to the inactive partitions: Possible
            '''
            try:
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=aCell)
                _cmd_get_rollback_possibility_status = "/usr/local/bin/imageinfo | grep 'Rollback to the inactive partitions: Impossible'"
                _i, _o, _e = _node.mExecuteCmd(_cmd_get_rollback_possibility_status)
                _exit_code = int(_node.mGetCmdExitStatus())
                if int(_exit_code) == 0:
                    _suggestion_msg = f"Rollback is not possible on cell : {aCell}"
                    aStatus.append({'node': aCell, 'status': 'failed', 'errorcode': CELL_NOT_ELIGIBLE_FOR_ROLLBACK})
                    self.mAddError(CELL_NOT_ELIGIBLE_FOR_ROLLBACK, _suggestion_msg)

            except Exception as e:
                 self.mPatchLogWarn(f"Error while performing rollback possibility validation. \n\n {str(e)}")
                 self.mPatchLogTrace(traceback.format_exc())

            finally:
                if _node.mIsConnected():
                    _node.mDisconnect()

        # End of _validate_cell_possibility_of_rollback method

        """
         Validate possibility of rollback on all 
         cells in parallel.
        """
        _plist = ProcessManager()
        _rc_status = _plist.mGetManager().list()

        for _remote_node in aListOfCellsToValidate:
            _p = ProcessStructure(_validate_cell_possibility_of_rollback, [_remote_node, _rc_status], _remote_node)

            '''
             Timeout parameter configurable in Infrapatching.conf
             Currently it is set to 10 minutes
            '''
            _p.mSetMaxExecutionTime(self.mGetExadataPatchPurgeExecutionTimeoutInSeconds())

            _p.mSetJoinTimeout(PARALLEL_OPERATION_TIMEOUT_IN_SECONDS)
            _p.mSetLogTimeoutFx(self.mPatchLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()

        if _plist.mGetStatus() == "killed":
            _suggestion_msg = f"Timeout while validating possibility of rollback on the list of cells : {str(aListOfCellsToValidate)}."
            self.mAddError(CELL_NOT_ELIGIBLE_FOR_ROLLBACK, _suggestion_msg)
            raise Exception(_suggestion_msg)

        # validate the return codes
        for _rc_details in _rc_status:
            if _rc_details['status'] == "failed":
                raise Exception("Rollback validation on cells failed.")

    def mCheckListeningInterface(self, aCellName, aList):
        _ret = PATCH_SUCCESS_EXIT_CODE
        # not required for ExaCC and not to be executed if SMR
        if self.mIsExaCC() or self.mIsExaSplice():
            self.mPatchLogInfo("ExaCC or ExaSplice, no need to set interface")
            return _ret
        try:
            _cell = exaBoxNode(get_gcontext())
            _cell.mConnect(aHost=aCellName)
            # if cellcli supports listening interface, it indicates that is 24.1 or higher
            '''
            [root@sea201416exdcl04 ~]# cellcli -e list cell attributes listeningInterface 
            ALL
            for 23.*
            CELL-01504: Invalid command syntax.
            [root@sea201309exdcl01 ~]# echo $?
            1
            '''
            _cmd = "cellcli -e list cell attributes listeningInterface"
            _i, _o, _e = _cell.mExecuteCmd(_cmd)
            _exit_code = int(_cell.mGetCmdExitStatus())
            if int(_exit_code) != 0:
                self.mPatchLogInfo("Exadata version is not 24.1 or higher, nothing to do")
            # setup listening endpoint
            elif self.mCheckCurrentInterfaceOpen(_cell):
                _ret = self.mSetIpListeningInterface(aCellName, _cell, aList)
        except Exception as e:
             self.mPatchLogError(f"Error while setting up listeningInterface \n {str(e)}")
        finally:
            if _cell.mIsConnected():
                _cell.mDisconnect()
        return _ret

    def mCheckCurrentInterfaceOpen(self, aCellConn):
        # check if the listening endpoint is open
        _cmd = "netstat -anp | grep 443 | grep LISTEN |egrep ':::443|0.0.0.0:443'"
        _i, _o, _e = aCellConn.mExecuteCmd(_cmd)
        _exit_code = int(aCellConn.mGetCmdExitStatus())
        # if it listening edpoint is open, need to set the IP's
        if int(_exit_code) != 0:
            self.mPatchLogInfo("IP's already set for listening interface")
            return False
        else:
            self.mPatchLogInfo("Listening interface not set")
        return True

    def mSetIpListeningInterface(self, aCellName, aCellConn, aList):
        _rc = PATCH_SUCCESS_EXIT_CODE
        try:
            # check if it is IB or Roce
            '''
            [root@sea201309exdcl02 ~]# /opt/oracle.cellos/exadata.img.hw --get is-roce-or-ib
            roce
            '''
            _cmd = "/opt/oracle.cellos/exadata.img.hw --get is-roce-or-ib"
            _i, _o, _e = aCellConn.mExecuteCmd(_cmd)
            _exit_code = int(aCellConn.mGetCmdExitStatus())
            if int(_exit_code) == 0:
                '''
                [root@sea201416exdcl04 ~]# cellcli -e "alter cell listeningInterface='stre0,stre1' force"

                Stopping MS services...
                The SHUTDOWN of MS services was successful.

                Updating attribute "listeningInterface" before redeploying MS.

                Starting MS services...
                The STARTUP of MS services was successful.

                Cell sea201416exdcl04 successfully altered
                '''
                _type = _o.read()
                # for roce
                if _type and "roce" in _type.lower():
                    _cmd = "cellcli -e \"alter cell listeningInterface='stre0,stre1' force\""
                # for ib
                else:
                    _cmd = "cellcli -e \"alter cell listeningInterface='stib0,stib1' force\""
                _i, _o, _e = aCellConn.mExecuteCmd(_cmd)
                _exit_code = int(aCellConn.mGetCmdExitStatus())
                self.mPatchLogWarn(f"alter cell listeningInterface cmd returned : {str(_exit_code)}")
            else:
                self.mPatchLogWarn(f"Error running exadata.img.hw --get :{str(_exit_code)}")
        except Exception as e:
            self.mPatchLogWarn(f"cellcli to alter interface failed : {str(e)}")

        # if the "cellcli alter" cmd succeded, need to check if services are up
        # OR if the previous "cellcli alter" command failed but services are restarted ok, we should
        # be able to proceed.
        # if the services are not up for any reason, we need to stop patching.
        _count = 0
        _ret = False
        # Max sleep time is 60 seconds
        while _count < 6:
            # wait for the service to come up
            _ret = self.mGetCluPatchCheck().mCheckCellServices(aCellName, aList, aCheckRunning=True)
            if not _ret:
                self.mPatchLogInfo("Cell services are not up yet")
                _count += 1
                sleep(MS_SERVICES_SLEEP)
                self.mPatchLogInfo(f"**** Iteration : [{_count:d}/6] - Cell services online status check is executed again in {MS_SERVICES_SLEEP} seconds.")
            else:
                break
    
        if not _ret:
            _suggestion_msg = f"Cell services are not up in {aCellName}"
            _rc = CELL_SERVICES_NOT_RUNNING 
            self.mAddError(_rc, _suggestion_msg) 
            self.mPatchLogWarn("During setup of Listening Interface MS services did not come up")

        self.mPatchLogInfo("Listening Interface complete")
        return _rc

