"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    OVM - Basic functionality

FUNCTION:
    Provide basic/core API for managing OVM Cluster (Cluster Lifecycle,...)

NOTE:
    None

History:    
    MODIFIED   (MM/DD/YY)
    scoral      11/20/25 - Bug 38673589 - Enhanced mIsEth0Removed to connect to
                           the actual node and check the interface.
    joysjose    11/15/25 - joysjose 10/22/25 - Bug 38417178 Refactoring cell
                           connections before Create VM
    jfsaldan    10/27/25 - Bug 38559314 - EXADBXS Y25W42 | CREATEVM FAILED | 2
                           DOM0S HAVE DIFFERENT IMAGE VERSION | PARALLEL CREATE
                           SERVICE 'B' WITH DIFFERENT FIRST.BOOT IMAGE SELECTED
                           DELETED FIRST.BOOT IMAGE OF OPERATIONS 'A'
    remamid     10/14/25 - Enable libvirtd during prevm check step bug 38481712
    kanmanic    10/10/25 - HW Sanity Test with Specific Error codes
    abysebas    10/07/25 - Enh 38299822 - PHASE 1: FREE NODE POWER SAVING -
                           EXACLOUD CHANGES
    nelango     09/24/25 - Bug 38261183: validating eth speed of -1 as
                           unknown/unresolved
    remamid     09/11/25 - Report precheck hardware failure as part of exacloud
                           error message 38325004
    bhpati      09/09/25 - Bug 38258245 - prevmchecks during create cluster is
                           trying to set the speed even if the speed is already
                           correct
    naps        09/09/25 - Bug 38347003 - For zdlra migrate users confirming to
                           accessUpdater.
    jfsaldan    09/03/25 - Bug 38244250 - EXACS: PROVISIONING FAILED WITH
                           EXACLOUD ERROR CODE: 1859 EXACLOUD : CELL
                           CONSISTENCY/SEMANTIC CHECKFAILED. | CELL CONSISTENCY
                           CHECK SHOULD NOT RAISE AN EXCEPTION IN CREATE
                           SERVICE
    nelango     08/29/25 - Bug 38299928: Postpone restore SSH keys after
                           cleanup and validation are complete
    jesandov    08/22/25 - 38172531: Add validation in case of clusterless XML.
    avimonda    08/15/25 - Bug 38215547 - EXACS: PROVISIONING FAILED WITH
                           EXACLOUD ERROR CODE: 1859 EXACLOUD : PHYSICAL DISK
                           NOT IN NORMAL STATE -- ARN100208EXDCL04
    arturjim    08/13/25 - Enh 38301649 - EXACC:VMBACKUP: ADD SUPPORT FOR SSH
                           KEYS IN VMBACKUP 
    aararora    08/08/25 - Bug 38290565: Do not set ntp/dns config on cells for
                           exacc and for provisioning if grid disks are present
    antamil     08/07/25 - 38268425: Validate the priv and public key for clusterless patching
    ajayasin    07/31/25 - 38169726: Enhance the logic to accurately identify the faulty
                           grid disk for the given cluster
                           identify the faulty grid disk for the given cluster
    oespinos    07/23/25 - Enh 37969515 - Add Spine/Admin switches to exassh
                           only adds first switch
    ririgoye    07/21/25 - Enh 38219932 - CPG: RAISE EXACLOUD ERROR IF THE
                           LOCATION ATTRIBUTE HAS INVALID OR EMPTY INFO IN ECRA
                           PAYLOAD
    hcheon      07/21/25 - 38196008 Cell force shutdown for fault injection
    ajayasin    07/11/25 - Bug 38169726: Enhance the logic to accurately
                           identify the faulty grid disk for the given cluster
    asrigiri    06/25/25 - Bug 37989091 - WRONG STATUS CODE IN EXACLOUD LOG
                           EVEN THOUGH THERE IS FAILURE.
    ririgoye    06/25/25 - Enh 38086929 - CREATE /OPT/ORACLE/SG.JSON DURING
                           PROVISIONING OF ADBS CLUSTERS
    anudatta    06/12/25 - Enh 37654312 : add version info in metadata sync api 
    aararora    05/26/25 - Bug 37981919: cellcli alerthistory command output is
                         now on multiple lines from 25.x onwards
    antamil     05/23/25  - Bug 37969822 Changes to make infrapatching key tag to be 
                            used for all patch operations  
    antamil     05/20/25 - 37954339: Cleanup EXAMISC KEY for clusterless patching
    jesandov    05/13/25 - 37938578: Ignore 'nobody(65534)' user in maximum id for migrate_ids.sh
    remamid     05/08/25 - Add HDD check for compute bug 37828585
    araghave    05/07/25 - Enh 37892080 - TO IMPLEMENT NEWER PATCHSWITCHTYPE
                           CHANGES APPLICABLE TO ALL SWITCH TARGET TYPES AND
                           PATCH COMBINATIONS
    akkar       04/25/25 - Bug 37833446: Check GI support in OEDA
    caborbon    04/08/25 - ENH 37518143 - Increasing size name in VIP domain
                           length in mHostnamesLengthChecks
    akkar       04/03/25 - 37784744 Improve response time for faultinjection
    gparada     03/31/25 - 37768492 Fix user in mRemoveSSHPublicKeyFromVM
    rothakk     03/28/25   - Bug 37760900: Add timeout to faultinjection
    gparada     03/24/25 - 37697720 Fix call to ssh-keygen to keep folder owner
    akkar       03/06/25   - Bug 37573195: Interface to inject network errors for stre0 and stre1 
    pbellary    27/02/25   - Bug 37644760 - EXACS:PRECHECK:'ERROR-MESSAGE': 'ERSSTATUS TEST FAILED ON CELL 
    enrivera    31/01/25   - Bug 37524625 - INFRA PATCH DELETING PUBLIC KEYS ON
    jesandov    02/17/25   - 37598599: Add extra validation in eth0_removed detect
    antamil     02/12/25   - 37567374: Multiple patchmgr session on launch node 
                             for clusterless patching
    jfsaldan    02/11/25   - Bug 37570873 - EXADB-D|XS -- EXACLOUD |
                             PROVISIONING | REVIEW AND ORGANIZE PREVM_CHECKS
                             AND PREVM_SETUP STEPS
    piyushsi    02/10/25   - BUG 37379443 FaultInjection API changes
    akkar       01/29/25 - Bug 37005705: Delete ssh keys of deleted node from
                           know_hosts file of other nodes
    joysjose    02/05/25   - 37353081: Ignore M2_SYS_0 or M2_SYS_1 errors in
                             provisioning and elastic flows
    antamil     01/31/25 -   Enh 37300427 - Enable clusterless cell patching
                             using management host
    aararora    01/28/25   - Bug 37521880: UT failing for _rc_status not
                             defined
    joysjose    01/13/25   - Bug 37348776 provisioning should not fail due to a
                             single power supply failure to cell
    araghave    12/12/24   - Enh 37228878 - GENERATE KEYSCAN ENTRIES ON THE
                             IBSWITCH TARGET IN CASE OF SSH VERSION MISMATCH
    zpallare    12/10/24   - Enh 37144837 - EXACS ECRA - Create an api to do
                             re-bonding of existing node and update
                             admin_monitor.json
    prsshukl    11/28/24   - Bug 37240032 - Add ntp and dns value pre and post
                             OEDA create vm
    antamil     11/27/24   - Bug 37236994 - Changes on cleanup of passwordless ssh
                             for single vm patching
    ririgoye    11/26/24   - Bug 37315472 - EXACC: ADD NODE TO ASM VM CLUSTER
                             FAILS WITH EXACLOUD ERROR MESSAGE: EXACLOUD :
                             REMOTE COMMAND EXECUTION FAILED
    araghave    11/22/24   - Enh 37106126 - PROVIDE A MECHANISM TO PATCH SPINE
                             SWITCHES
    jfsaldan    11/22/24   - Bug 37315192 - EXACS: 24.4.2.1: ADD STORAGE FLOW
                             FAILING WITH 'ASM RESHAPE PRECHECK FAILED. GRID
                             DISKS IN FOLLOWING CELLS ARE IN 'DROPPED',
                             'OFFLINE' OR 'UNKNOWN ''
    asrigiri    11/20/24   - Bug 37208063 - UPDATE EXADATA STORAGE WORKFLOW
                             FAILS AT PRE-CHECK - FIX RELEASED THROUGH BUG
                             37000514 IS APPLIED VIA CPS TUNER 86 IS NOT
                             WORKING
    prsshukl    11/19/24   - Bug 37288941 - MRESTARTVMEXACSSERVICE SHOULD CHECK
                             IF VMEXACS_KVM SERVICE IS UP PRIOR TO RESTART
    antamil     11/15/24   - Bug 37259695 - Fix for multiple patching operation
                             on management host
    prsshukl    11/13/24   - Bug 37274900 - Update mCorrectTimeDifinNode to
                             include other nodes also
    prsshukl    11/11/24   - Bug 37262418 - Adding GMT to the precheck for time
                             dif
    antamil     11/06/24   - Bug 37181004 Add timeout for ssh-keyscan command
    ririgoye    11/05/24   - 36994764 - VM CLUSTER PROVISION FAIL AT PREVMCHECKS
                             WHEN FLASHCACHE STATUS ON CELL IS ABNORMAL
    ririgoye    11/04/24   - Bug 37137239 - EXACLOUD NOT RELEASING LOCKS WHEN
                             FAILING THREADED PROCESS
    jfsaldan    10/30/24   - Bug 37207274 -
                             EXACS:24.4.1:241021.0914:MULTI-VM:PARALLEL VM
                             CLUSTER PROVISIONING FAILING AT PREVM SETUP
                             STEP:EXACLOUD : COULD NOT UPDATE CELL DISK SIZE
    pbellary    10/29/24   - 37224927 - SRG:PROVISIONING FAILED AT PREVMSETUP WITH ERROR:CRITICAL EXCEPTION CAUGHT ABORTING REQUEST ['FQDN'] 
    naps        10/24/24   - Bug 37192649 - Handle eth0 removal per node
                             instead of cluster wide.
    araghave    10/11/24   - Enh 37156971 - USE ENCRYPTED NON-DEFAULT PASSWORD
                             TO SETUP KEYS DURING ADMIN SWITCH PATCHING
    naps        10/09/24   - Bug 37147521 - Replace x11m-2 with x11m as per
                             oeda requirement.
    prsshukl    10/04/24   - Bug 37136123 - RESIZEDGSIZES FAILING IN ADD CELL
                             BECAUSE OF CELL-01504: INVALID COMMAND SYNTAX
    jesandov    10/02/24   - Bug 37021727 - Change logic on scanning keys
    bhpati      09/27/24   - DOMU PRECHECK IS REMOVING EXISTING ROOT
                             SSH-EQUIVALENCE FROM NODE1 TO NODE2
    akkar       09/25/24   - Bug 36923764: Return admin switches for patching
    vikasras    09/19/24   - Bug 37057958 - FAILED TO COMPLETE GUEST VM OS UPDATE PRECHECK. 
                             TASK HANDLER PATCH REQUEST EXCEPTION DETECTED. 
    asrigiri    09/11/24   - Bug 37000514 - UPDATEEXADATASTORAGE FAILS AT
                             AWAIT_EXA_STRG_PRECHECK WHEN ASMMODESTATUS WHEN
                             DOMUS FOR OTHER VM CLUSTERS ARE NOT RUNNING AND
                             ASMMODESTATUS EXPECTEDLY SHOWS AS UNKNOWN SINCE
                             CUSTOMER DOES NOT HAVE DOMUS RUNNING.
    antamil     08/28/24   - Bug 36977261 - Cleanup know_host file based on nat ip
    naps        08/14/24   - Bug 36949876 - X11 ipconf path changes.
    prsshukl    08/13/24   - Bug 36927902 -Precheck to sync time between node
                             and ecra host
    prsshukl    08/12/24   - Enh 36557797 - Function to restart vmexacs_kvm
                             service once libvirtd service is up
    ririgoye    08/09/24   - Bug 36931626 - Adding logs for grid disks in bad
                             state
    naps        08/09/24   - Bug 36908342 - X11M support.
    antamil     08/01/24   - Bug 36881089 - Configure passwordless ssh using
                             ssh config file on management host
    ririgoye    07/30/24   - Bug 36869934 - EXACLOUD NEEDS TO CHANGE ASM
                             PASSWORD CHECK COMMAND
    joysjose    07/30/24   - BUG 36563704 disable dom0 host image check for
                             ExaCC ADD NODE flow in node_subset_precheck flow
    antamil     07/24/24   - Bug 36829942 - Missing fixes for single VM patching on MAIN
    joysjose    07/23/24   - ER 36618415 Stop and Start Host via Ilom
    pbellary    07/22/24   - Bug 36641413 - EXACC:BB:23.3.1.3.0:ACTIVATE COMPUTE:FAILING WITH GENERIC ERROR AND 500 RESPONSE 
    akkar       07/15/24   - Bug 36838959: Update the comment
    gparada     07/11/24   - Bug 36564670 Replace Queue by ProcessManager.List
    bhpati      07/10/24  - Bug 36672855 - EXACS : ALREADY CONFIGURED ROOT USER
                            SSH KEY EQUIVALENCY IS NOT PRESERVED POST PATCHING
    antamil     07/10/24 - Bug 36807420 - Cleanup known host during cleanup of
                           keys
    antamil     07/10/24   - Bug 36807420 - Cleanup known host during cleanup of
    pbellary    07/02/24  - ENH 36690772 - EXACLOUD: IMPLEMENT PRE-VM STEPS FOR EXASCALE SERVICE
    pbellary    07/02/24   - ENH 36690772 - EXACLOUD: IMPLEMENT PRE-VM STEPS FOR EXASCALE SERVICE
    joysjose    06/28/24   - ER-36120286 - EXACS: EXACLOUD TO DISPLAY A SUMMARY
                             REPORT OF ISSUES FOUND DURING SCALE PRECHECK
    akkar       06/05/24   - Bug 36184231: Copy dbcsagent files for oc1 region
    gojoseph    06/04/24   - Bug 36672995 Fix for asmdisksize='UNKNOWN'
    antamil     03/07/24   - Bug 36796372 - Fix for multiple patch request for
                             single VM clusters
    antamil     05/21/24   - Bug 36635964 - Address connection errors message 
                             on logfile
    remamid     05/14/24   - Bug 36554329 - IMPROVE DBAAS.UPDATEEXADATASTORAGE
                             WORKREQUEST FAILURE
    prsshukl    05/08/24   - Enh 36442918 - ADD A PRECHECK TO STOP PROVISIONING
                             IF VM NAME STARTS WITH "VM" AND AT LEAST ONE KVM
                             DOM0 HAS (< 23.1.90.0.0.231219) EXADATA IMAGE
    rajsag      05/07/24   - 36591979 - rack model name x10m-cc not parsed
                             properly by exacloud
    jfsaldan    05/02/24   - Bug 36573967 - EXACS:R1 SRG: CLUSTER TERMINATION
                             STUCK IN PREVMINSTALL STEP
    aararora    04/24/24   - ER 36485120: IPv6 support in exacloud
    akkar       04/21/24   - Bug 36509496: Change of certificate name format
    ririgoye    03/13/24   - Bug 36401221 - REMOVING ADDITIONAL INFO FROM ERROR
    antamil     03/11/24  -  Enh 36372221 - Code changes for single VM EXACS
                             patching support
    akkar       03/07/24   - Bug 36377723: Fedramp ttruststore path change
    rajsag      03/07/24   - 36368657 exacc23.3:bb:elastic: activate node
    rajsag      03/07/24   - 36368657 exacc23.3:bb:elastic: activate node
    ririgoye    03/06/24   - Bug 36364832 - NEED DETECTION/PRECHECK FOR
                             EXACSDBOPS-6663 WHERE ASM PASSWORD IS CHANGED BY
                             CUSTOMER CAUSING VM-ADDITION FAILURE
    dekuckre    03/04/24   - 36339845: Add mPatchPrivNetworks
    pbellary    02/15/24   - Bug 36054723 - EXACS - PREVENT EARLY DBAASOPS-269375; PHYSICAL DISK PMEM_0_3 
                             FAILURE SHOULD BE CAUGHT BEFORE PROVISIONING
    pkandhas    02/20/2024 - 36154049 Remove right SSH keys from authorized_keys
    pbellary    12/09/23   - Enh 35586531: SUPPORT FOR 100GBE CARD FOR BACKUP NETWORK IN PCI SLOT 2 
    antamil     12/05/23   - Fix for bug 36095866, generate keys on launch node
    jfsaldan    12/01/23   - Bug 36063747 - EXADBXS:23.4.1.1.1:231115,X9M,
                             CREATE-SERVICE, PROVISIONING FAILS AT TASK
                             PREVMCHECKS, CONCURRENT IPCONF EXECUTION CAUSES
                             CONSISTEN CHECK ERROR
    akkar       12/01/23   - Bug 36019407: pfx files copy to domU
    pkandhas    11/25/23   - 36037591 - Add any key to known_hosts if RSA Not
                             available
    jesandov    11/22/23   - 36037011: Remove mSaveOperatingSystems
    antamil     11/17/23   - BUG 36000710 - FIX FOR CPS AS LAUNCH NODE TO USE NAT
                             HOSTNAME
    prsshukl    10/31/23   - Bug 35887541:Copy dbcsagent p12 file to domU
    jfsaldan    10/09/23   - Bug 35889169 - EXACS:23.4.1:SSH_TEST DURING
                             PREVM_CHECKS SUCCEEDS EVEN IF KEY DOESN'T WORK BUT
                             USERNAME/PASSWORD WORK OK
    rajsag      10/04/23   - 35847165 - exacc:23.3.1:x8m-x9m:bb:activate cell
                             failed with error: dbaasapi: failed to read job id
                             from domu
    rajsag      09/20/23   - ENH 35779694 - EXACC GEN2 ADD IN PRECHECK SIZE
                             MUST BE SAME FOR GRIDDISK AND ASMDISKSIZE
    hcheon      08/30/23   - 35197827 Use OCI instance metadata v2
    ririgoye    08/23/23   - Bug 35616435 - Fix redundant/multiple instances of
    ririgoye    09/01/23   - Bug 35769896 - PROTECT YIELD KEYWORDS WITH
                             TRY-EXCEPT BLOCKS
    pbellary    08/22/23   - Enh 35728221 - ADD SUPPORT FOR 2TB MEMORY IN X10M
    jesandov    08/08/23   - 35309586: Add save of id_rsa key before
                             passworless setup
    gparada     07/10/23   - 35529689 Refactor cluctl.mGetMinSystemImageVersion 
                             and moved here to mGetDom0sImagesListSorted 
    jfsaldan    07/03/23   - Bug 35339516 - EXACS:22.2.1:DROP3:EXACLOUD DIDN'T
                             CATCH FLASHDISK ISSUE DURING PROVISIONING, WHICH
                             RESULTED IN FLASHCACHE BEING DIFFERENT IN 1 CELL
                             OF THE CLUSTER WITH NO ERRORS REPORTED
    pbellary    06/28/23   - 35543679 - ADD VM (ON NON 2TB SYSTEM) FAILING AT PRECHECK:"ERROR-MESSAGE": "2TB MEMORY NOT SUPPORTED ON DOM0 
    rajsag      06/19/23   - 35498967-exacc:22.3.1.0.0: exacloud to send memory
                             for add compute validate node call
    avimonda    06/14/23   - 35412261 Fix hostname-based SSH key removal method
                             to correctly delete the SSH keys from the
                             authorized_keys file
    gparada     06/13/23   - 35495548 Fix version used to compare in validation
    pkandhas    06/01/23   - Enh 35371653, Remove Obsolete SSH keys
    gparada     05/26/23   - 34556452 Add validation for KVM and MVM
    jesandov    05/26/23   - 35426500: Add support of ECDSA passwordless
    gparada     05/11/23   - 35370215 Added getInitialIngestion, consumed by ECRA
    agoulet     05/08/23   - BUG 35320371 Create VM Precheck fails with griddisk suffix C1
    rajsag      04/24/23   - 35303436 - list capacity returns invalid model in
                             cellnodedetails
    dekuckre    04/20/23   - 35081567: update mCheckOracleLinuxVersion
    oespinos    02/16/23   - 35079264 - CELL MODEL RETURNED BY EXACLOUD IS
                             "X10M" INSTEAD OF "X10M-2"
    dekuckre    02/16/23   - 35081567: Add mCheckOracleLinuxVersion
    joysjose    02/02/23   - Enh 34926987 Improve error log in temperature test
                             for better debug
    rajsag      01/15/23   - ol8 support
    rajsag      01/09/23   - x10m support
    pkandhas    12/19/22   - Bug 34482941 - Fix known_hosts file errors
    prsshukl    11/23/22   - Bug 34809190 - Dead code removal in
                             mRunAllPreChecks
    rajsag      11/16/22   - 34804621 - exacc:22.3.1.2.0:multirack:after
                             activating x9m compute ecra still shows rack model
                             as x8m
    egalaviz    11/11/22   - Enh 34783912- XbranchMerge egalaviz_bug-34753192 from
                             st_ecs_21.3.1.0.0
    rajsag      11/08/22   - enh 34552843 - exacc gen2: add node precheck for
                             space on source domu
    aypaul      11/02/22   - ENH#34250801 Connectivity check to existing VMs
                             prior to elastic add operations.
    rajsag      09/18/22   - 34611549 - exacc:x7:x8:elastic_cell:attach x8 cell
                             gets stuck at sync_storage_ecra because of
                             rack-model mismatch
    naps        09/02/22   - Bug 34559797 - remove cluster suffix check for
                             zdlra env.
    ajayasin    08/22/22   - Bug 34508899: Fetchkey NAT FQDN to be used
    pbellary    08/18/22   - Bug 34506450: EXACS:22.2.1:MULTI-VM, E2E, 220812, CREATE-SERVICE, CS FLOW FAILED AT
                             TASK PREVMCHECKS
    alsepulv    08/11/22   - Bug 34489419: Remove 63 character length check for
                             VIPs
    rajsag      08/03/22   - bug 34460196 - exacc:wrong model number given for
                             the cell server
    alsepulv    07/05/22   - Bug 34353705: Prechecks - Fix for incorrect FQDN
                             length check
    alsepulv    06/07/22   - Bug 34236957: Add hostnames length prechecks
    araghave    04/28/22   - Bug 34094559 - REVERTING THE CHANGES FOR ENH
                             33729129
    akkar       04/07/22   - Bug 34004535: Bandit fixes
    jyotdas     03/14/22   - ENH 33933635 - Avoid cleanup the ssh equivalence
                             at the end of patching
    rajsag      02/04/22   - Enh 33777831 - post compute activate validation
                             support from exacloud
    araghave    02/02/22   - Enh 33813626 - Add switchexa user access during
                             Roce Switch
    araghave    01/06/22   - Enh 33729129 - Provide both .zip and .bz2 file
                             extension support on System image files.
    siyarlag    12/20/21   - 33689277: skip KVM HOST re0, re1 checks
    araghave    12/09/21   - Bug 33574929 - ROCE SWITCH PRECHECKS FAILS DUE TO
                             CLUMISC.PY COMMAND FORMAT MODIFICATION CHANGES
    ashisban    12/08/21   - Exacloud API for cell disk precheck of exadata
                             storage reshape
    dekuckre    11/09/21   - XbranchMerge alsepulv_bug-33513659 from
                             st_ecs_21.4.1.0.0
    dekuckre    10/25/21   - 33498594: Remove dependency on non-root user
    alsepulv    08/11/21   - Bug 33212009: Make sure pmem is set to disabled
                             instead of failing
    rajsag      06/22/21   - 33027911 - elastic cell add: add domu connectivity
                             test to the existing cell validation flow
    alsepulv    05/24/21   - Kms Refactoring: Use new ExaKms
    araghave    05/20/21   - Enh 32905414 - ROCE SWITCH KNOWN HOSTS ENTRY
                             CHANGES IN CLUMISC.PY
    rajsag      04/21/21   - Bug 32771363 - need to add a precheck in elastic expansion to detect authconfig installation 
    rajsag      04/19/21   - 32778978 - elastic cell add: exacloud change to
                             validate cell api incase the dbaasapi is missing
    rajsag      03/21/2021 - Enh 32566227 - domu based validation for elastic cell expansion
    rajsag      04/14/21   - 32765071 - exacc gen2: ecra error in activate cell
                             server call
    alsepulv    03/16/21   - Enh 32619413: remove any code related to Higgs
    vikasras    03/17/2021 - Bug 32285465 - BETTER HANDLING OF SSH-KEYGEN
    josedelg    03/08/2021 - Bug 32522779 - Add confirmation when executing
    alsepulv    03/05/21   - Bug 32592473: replace get_stack_trace() with
                             traceback.format_exc()
    josedelg    08/03/2021 - Bug 32522779 - Add confirmation when executing
                             ssh-keygen
    rajsag      02/16/2021 - Enh 32299319 - IMPLEMENT CELL SERVER ACCESSIBILITY TEST MODULE IN EXACLOUD
    araghave    01/07/2021 - Bug 32320030 - ROCE SWITCH REFACTOR CODE CHANGES
    sringran    10/03/2020 - Bug31722894 - DOMU PRE-CHECK FAILURE DUE TO SSH
                             VERIFY SSH EQUIVALENCE
    dekuckre    09/08/2020 - 31854421: Fix fetchkeys cmd flow
    nmallego    08/18/2020 - Bug31765351 - python3 compatible for sorted method
    jricoir     08/04/2020 - Bug 31600342: include role in EM DB details
    dekuckre    06/12/2020 - Add fix for 31476866
    pnkrishn    03/18/2020 - 31021422: mRemoveFromKnownHosts to remove 
                             short hostname 
    dekuckre    03/02/2020 - 30892256: Verify presence of ssh key file
    dekuckre    11/29/2019 - 30590874: Add mCheckVMTimeDrift.
    nmallego    01/13/2020 - Bug30327503 - fixing fortify error
    jricoir     09/25/2019 - Bug 30345314: EM is showing wrong tenant OCID
    jricoir     05/25/2019 - Bug 30134829: Get ASM/APX instance nodes for EM
    jricoir     05/25/2019 - Bug 29855713: Properly update logical AD code and
                             tenant ID for EM properties
    ajadams     04/04/2019 - bug-29604305: use correct SID for 
                             registering DB instances to EM
    ananyban    03/03/2019 - Bug 29412175: Handling namespace changes for 
                                 cluster reg with EM
    nmallego    02/16/2018 - Bug27556005 - add comments for the public key
                             creation with ssh-keygen 
    nmallego    11/16/2017 - Bug26830429 - Add class OracleVersion for oracle
                             version to compare and sort
    dekuckre    05/30/2017 - Use debug flag in class:ebCluPreChecks
    dekuckre    05/23/2017 - Bug 25902691: Add mVMPreChecks()
    dekuckre    05/23/2017 - Bug 26035758: Add mCheckDom0Mem()
    mirivier    02/09/2016 - File Creation
"""

from typing import Set, List
import six
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.core.Error import ebError, gSubError, ExacloudRuntimeError, gReshapeError, gNodeElasticError, get_hw_validate_error
from exabox.core.Node import exaBoxNode
from exabox.utils.node import (connect_to_host, node_exec_cmd,
        node_cmd_abs_path_check, node_list_process)
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogVerbose, ebLogDebug, ebLogJson, ebLogTrace
from exabox.ovm.vmconfig import exaBoxClusterConfig
from exabox.utils.common import check_string_base64, version_compare
from exabox.utils.node import connect_to_host, node_exec_cmd_check, node_cmd_abs_path_check, node_exec_cmd
from exabox.utils.common import mCompareModel
from exabox.config.Config import ebCluCmdCheckOptions
import getpass
import os, sys, subprocess, uuid, time, os.path, shlex
from subprocess import Popen, PIPE
import xml.etree.cElementTree as etree
from exabox.core.Context import get_gcontext
from tempfile import NamedTemporaryFile
from time import sleep
from base64 import b64decode, b64encode
import hashlib
import random
import string
import re
import ast
import glob
import base64
import json, copy, socket
from datetime import datetime
from exabox.tools.scripts import ebScriptsEngineFetch
from exabox.core.Error import retryOnException
from exabox.core.DBStore import ebGetDefaultDB
from exabox.ovm.monitor import ebClusterNode
from exabox.ovm.cludbaas import ebCluDbaas
from exabox.ovm.remotelock import RemoteLock
# Note: Queue objects are not used for multiprocessing in this file.
# If needed in future, consider using _list = _plist.mGetManager().list()
from multiprocessing import Process, Manager, Queue, Event
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.ovm.hypervisorutils import getHVInstance
import socket
from functools import cmp_to_key
from exabox.core.Mask import umask
import traceback
import psutil
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure, TimeoutBehavior, ExitCodeBehavior
from exabox.infrapatching.utils.constants import EXAPATCHING_KEY_TAG


STOP_SLEEP_TIME_FROM_ILOM = 330
START_SLEEP_TIME_FROM_ILOM = 330
MAX_RETRY = 3
RETRY_WAIT_TIME = 30
SSH_KEYSCAN_TIMEOUT = 30

FAULT_INJECTION_STOP_SLEEP_TIME_FROM_ILOM = 120
FAULT_INJECTION_PING_CHECK_INTERVAL = 10
FAULT_INJECTION_INIT_CHECK_DELAY_AFTER_START = 30

def mGetAlertHistoryOptions(aCluctrl, aHost):
    _cluctrl = aCluctrl
    _host = aHost
    _cellcli_alerthistory_options = ""
    _cellcli_alerthistory_options_config = _cluctrl.mCheckConfigOption('cellcli_alerthistory_options')
    # If the exabox option is set, _cellcli_alerthistory_options will be taken as the config option
    # if the image version of host is >= 25.1.
    if version_compare(_cluctrl.mGetImageVersion(_host), "25.1.0") >= 0:
        if _cellcli_alerthistory_options_config:
            _cellcli_alerthistory_options = _cellcli_alerthistory_options_config
        else:
            # If the exadata version for the cell is greater than or equal to 25.1.0
            # and exabox option is not set - set it by default to '--inline' - exacc case, since
            # during tuner update, exacc does not update exabox conf.
            _cellcli_alerthistory_options = "--inline"
    return _cellcli_alerthistory_options

class ebCluPreChecks(object):

    def __init__(self, aCluCtrlObj):

        self.__cluctrl = aCluCtrlObj
        self.__verbose = False
        self.__cluster_host_d = {}

    def mGetEbox(self):
        return self.__cluctrl

    def mCheckOracleLinuxVersion(self, aSrcDomU, aDom0List):

        if self.__cluctrl.mCheckConfigOption("os_precheck") == "False":
            return

        _srcos = self.__cluctrl.mGetOracleLinuxVersion(aSrcDomU)

        for _dom0 in aDom0List:
            _dom0os = self.__cluctrl.mGetOracleLinuxVersion(_dom0)
            if _dom0os < _srcos:
                _err = "OS Version does not match"
                ebLogError(_err)
                raise ExacloudRuntimeError(0x0131, 0xA, _err)

    def mNetworkDom0PreChecks(self):

        @retryOnException(max_times=3, sleep_interval=5)
        def _dom0_network_validation(_dom0, rc_status):

            _rc = False
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)
            #
            # KVM Specifics checks (and temp w/a)
            # 
            # Check invalid bridges configuration and remove them if present
            #
            if self.__cluctrl.mIsKVM():
                ebLogWarn('*** TEMP W/A FOR KVM ROCE UNTIL NETWORK PRECHECKS IS DONE')
                _cmd = 'ls /etc/exadata/ovm/bridge.conf.d/*.xml'
                _,_o,_ = _node.mExecuteCmd(_cmd)
                _out = _o.readlines()
                if not self.mGetEbox().mIsOciEXACC() and not self.mGetEbox().mIsIntelX9MDom0(_dom0):
                    if _out:
                        for _entry in _out:
                            if 'eth5' in _entry or 'eth6' in _entry:
                                ebLogWarn('*** Invalid bridge configuration detected for KVM gen. Dom0')
                                _cmd = 'rm {0}'.format(_entry)
                                _node.mExecuteCmdLog(_cmd)
            #
            # Check ifcfg config files for invalid BOND mapping and not required config (e.g eth5|6).
            #
                    _cmd = 'rm /etc/sysconfig/network-scripts/ifcfg-eth5 ; rm /etc/sysconfig/network-scripts/ifcfg-eth6 '
                    _node.mExecuteCmdLog(_cmd)
                _cmd = "sed 's/^MASTER=bondeth1/MASTER=bondeth0/' -i /etc/sysconfig/network-scripts/ifcfg-eth1"
                _node.mExecuteCmd(_cmd)
                _cmd = "sed 's/^MASTER=bondeth1/MASTER=bondeth0/' -i /etc/sysconfig/network-scripts/ifcfg-eth2"
                _node.mExecuteCmd(_cmd)
                _cmd = "sed 's/^MASTER=bondeth0/MASTER=bondeth1/' -i /etc/sysconfig/network-scripts/ifcfg-eth3"
                _node.mExecuteCmd(_cmd)
                _cmd = "sed 's/^MASTER=bondeth0/MASTER=bondeth1/' -i /etc/sysconfig/network-scripts/ifcfg-eth4"
                _node.mExecuteCmd(_cmd)
            #
            # Check critical configuration files
            #
            if not _node.mFileExists('/opt/oracle.cellos/cell.conf'):
                ebLogError('ebPC Dom0 Network critical error. cell.conf not found in /opt/oracle.cellos')
                rc_status[_dom0] = _rc
                return
            #
            # Main network validation on Dom0
            #
            _fin, _fout, _ferr = _node.mExecuteCmd('/usr/local/bin/ipconf -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime')
            _out = _fout.readlines()
            if _out:
                _rc = False
                for _line in _out:
                    if (_line.find('Consistency check PASSED') != -1):
                        ebLogInfo('Network Consistency checks PASSED on {0}'.format(_dom0))
                        _rc = True
                        break

                if not _rc:
                    ebLogError(_out)
                    if self.__cluctrl.mIsKVM():
                        ebLogError('*** IP Conf. checks should pass - this is mandatory for KVM. Please fix issues in KVM OS System and try again.')
                        raise ExacloudRuntimeError(0x0131, 0xA, 'ipconf check consistency semantic at runtime fatal error')
            _node.mDisconnect()

            rc_status[_dom0] = _rc
            return
        #
        # Parallel Dom0 pre-checks
        #

        _plist = ProcessManager()
        _rc_d = _plist.mGetManager().dict()

        for _dom0, _ in self.__cluctrl.mReturnDom0DomUPair():
            _p = ProcessStructure(_dom0_network_validation, [_dom0, _rc_d], _dom0)
            _p.mSetMaxExecutionTime(60*60) # 30 minutes
            _p.mSetJoinTimeout(5)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()

        if False in _rc_d.values():
            return False

    def mDom0SystemPreChecks(self):
        _rc = True
        for _dom0, _ in self.__cluctrl.mReturnDom0DomUPair():
            #assuming 85percent as threshold
            _threshold_root_space = '95'
            if not self.mCheckUsedSpace(_dom0,'/',_threshold_root_space):
                ebLogError("space used in root partition is more than threshold(%s%%) for dom0 - %s" %(_threshold_root_space, _dom0))
                _rc = False

             #TBD: Check need to revisit to decide whether to abort provisioning flow
             #if not self.mCheckDom0Mem(_dom0):
             #    _rc = False

        return _rc

    def mNetworkBasicChecks(self,aVerbose=False):

        _network_ip_list = {}
        _dom0s, _, _, _ = self.__cluctrl.mReturnAllClusterHosts()
        _machinesConfigDict = self.__cluctrl.mGetMachines().mGetMachineConfigList()
        for _machine in _machinesConfigDict.keys():
            _machineConfig = _machinesConfigDict[_machine]
            _hostname = _machineConfig.mGetMacHostName()
            _networks = _machineConfig.mGetMacNetworks()
            if aVerbose:
                ebLogInfo('*** Hostname: %s' % (_hostname))
            for _network in _networks:
                # 33689277: skip checking private IPs on KVM HOSTs
                net_type = self.__cluctrl.mGetNetworks().mGetNetworkConfig(_network).mGetNetType()
                if self.__cluctrl.mIsKVM():
                    if _hostname in _dom0s and net_type == "private":
                        continue

                _ip = self.__cluctrl.mGetNetworks().mGetNetworkConfig(_network).mGetNetIpAddr()
                if aVerbose:
                    ebLogInfo('    _network: %s %s' % (_network,_ip))
                if _ip not in _network_ip_list.keys():
                    _network_ip_list[_ip] = _network
                else:
                    ebLogError('*** duplicate IP detected ***: %s clashes with: %s / %s' % (_network,_ip,_network_ip_list[_ip]))

    def mConnectivityChecks(self,aCheckDomU=True,aHostList=None):

        _rc = True

        _dom0s, _domUs, _cells, _switches = self.__cluctrl.mReturnAllClusterHosts()
        _cluhosts = list()
        if aHostList is not None:
            _cluhosts = aHostList
        else:
            _cluhosts = _dom0s + _domUs + _cells + _switches

        _cluster_host_d = {}
        #
        # Collect info on all hosts
        #
        for _host in _cluhosts:
            _neto = self.__cluctrl.mGetNetworks().mGetNetworkConfigByName(_host)
            _clunode = ebClusterNode()
            _cluster_host_d[_host] = _clunode
            _clunode.mSetClusterId(self.__cluctrl.mGetKey())
            _clunode.mSetHostname(_host)
            _clunode.mSetNetworkIp(_neto.mGetNetIpAddr())
            if _host in _dom0s:
                _clunode.mSetNodeType('dom0')
            elif _host in _domUs:
                _clunode.mSetNodeType('domu')
            elif _host in _cells:
                _clunode.mSetNodeType('cell')
            elif _host in _switches:
                _clunode.mSetNodeType('switch')
        #
        # Check HOST connectivity
        #
        for _host in _cluster_host_d.keys():

            _clunode = _cluster_host_d[_host]
            #
            # Check if HOST is pingable
            #
            if not self.__cluctrl.mPingHost(_host):
                _clunode.mSetPingable(False)
                _clunode.mSetSSHConnection(None)
                _clunode.mSetRootSSHDMode(None)
                _clunode.mSetPwdAuthentication(None)
                _clunode.mSetWeakPassword(None)
            else:
                _clunode.mSetPingable(True)
            #
            # Check if SSH connectivity
            #
            if _clunode.mGetPingable():

                _node = exaBoxNode(get_gcontext())
                try:
                    _node.mConnect(aHost=_host)
                except:
                    _clunode.mSetSSHConnection(False)
                    continue
                _clunode.mSetSSHConnection(True)
                #
                # Node specific checks/info
                #
                if _clunode.mGetNodeType() == 'switch':
                    _cmd4_str = 'smpartition list active no-page | head -10'
                    _i, _o, _e = _node.mExecuteCmd(_cmd4_str)
                    _out = _o.readlines()
                    if _out:
                        for _line in _out:
                            if _line.find('Default=') != -1:
                                _default = _line[len('Default='):-2]
                                _clunode.mSetSwitchDefault(_default)
                            elif _line.find('ALL_CAS=') != -1:
                                _all_cas = _line[len('ALL_CAS='):-2]
                                _clunode.mSetSwitchAllCas(_all_cas)

                _node.mDisconnect()
            #
            # Short report
            #
            if _clunode.mGetSSHConnection():
                ebLogTrace('Connectivity check to {1} host: {0} PASS'.format(_host,_clunode.mGetNodeType()))
            elif _clunode.mGetNodeType() == 'domu' and aCheckDomU is False:
                ebLogWarn('Connectivity check to domu: {0} FAILED (non critical)'.format(_host))
            elif _clunode.mGetPingable():
                ebLogError('Connectivity check to {1} host: {0} FAILED (ping: OK ssh: FAIL)'.format(_host, _clunode.mGetNodeType()))
                _rc = False
            else:
                ebLogError('Connectivity check to {1} host: {0} FAILED'.format(_host,_clunode.mGetNodeType()))
                _rc = False

        self.__cluster_host_d = _cluster_host_d

        return _rc

    def mResetNetwork(self,aCheckMode=None):

        for _dom0, _  in self.__cluctrl.mReturnDom0DomUPair():
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)

            # Reset interface to
            _cmd  = 'ifconfig ib0 0.0.0.0 ; ifconfig ib1 0.0.0.0 ; ifconfig vmbondeth0 0.0.0.0 ; ifconfig vmbondeth1 0.0.0.0'
            _cmd += ' ; ifconfig eth1 0.0.0.0 ; ifconfig eth2 0.0.0.0 ; ifconfig eth3 0.0.0.0 ; ifconfig eth4 0.0.0.0 ; ifconfig eth5 0.0.0.0'
            _node.mExecuteCmdLog(_cmd)

            _node.mDisconnect()

        return True

    def mResetIBNetwork(self,aCheckMode=None):

        for _dom0, _  in self.__cluctrl.mReturnDom0DomUPair():
            ebLogInfo('*** Running ResetIBNetwork on dom0 *** {0}'.format(_dom0))
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)
            _node.mExecuteCmdLog("cat /opt/oracle.cellos/ORACLE_CELL_OS_IS_SETUP | grep ovs")
            _rc = _node.mGetCmdExitStatus()
            if _rc != 0:
                ebLogInfo('*** Non-OVM mode,Skipping ResetIBNetwork ***')
                _node.mDisconnect()
                return

            # Reset interface of ibs
            _ib_ifaces = ['ib0','ib1']
            for _ib_iface in _ib_ifaces:
                _node.mExecuteCmdLog("sed '/^IPADDR=/d' -i /etc/sysconfig/network-scripts/ifcfg-{0}".format(_ib_iface))
                _node.mExecuteCmdLog("sed '/^NETMASK=/d' -i /etc/sysconfig/network-scripts/ifcfg-{0}".format(_ib_iface))
                _node.mExecuteCmdLog("ip addr flush dev {0}".format(_ib_iface))

            _node.mDisconnect()

    def mGetCoreAndMemInfo(self):
        ebLogInfo("mGetCoreAndMemInfo: get Cores and Memory iformation ")
        _dpairs = self.__cluctrl.mReturnDom0DomUPair()
        _dom0 = _dpairs[0][0]
        _domU = _dpairs[0][1]
        _memory_in_gb = 0
        _currvmem = 0
        _cpu = 0
        _currcpu = 0
        cluster_detail = {}
        domu_info = []
        _ratio = 2

        if self.__cluctrl.IsZdlraProv():
            if self.__cluctrl.mCheckConfigOption('zdlra_core_to_vcpu_ratio') is not None:
                _ratio = int(self.__cluctrl.mCheckConfigOption('zdlra_core_to_vcpu_ratio'))
            else:
                _ratio = 1
            ebLogDebug('*** mGetCoreAndMemInfo: _ratio is : %d' % (_ratio))


        for _dom0, _domU in _dpairs:
            ebLogInfo(f"getting details from dom0 {_dom0}")
            _hv = getHVInstance(_dom0)

            # get current VM memory  and CPU from Dom0
            _currvmem = _hv.mGetVMMemory(_domU, "CUR_MEM")
            _currcpu = _hv.mGetVMCpu(_domU, "CUR_CPU", True)
            ebLogTrace(f"CPU: {_currcpu} MEMORY: {_currvmem}")

            if _currvmem:
                _memory_in_gb = int(_currvmem) // 1024
            else:
                raise ExacloudRuntimeError("Could not retrieve memory info from cluster")
            if _currcpu:
                _cpu = int(_currcpu)
            else:
                raise ExacloudRuntimeError("Could not retrieve cpu info from  cluster")
          
            _cores = int(_cpu / _ratio)

            domu_info.append({"domu": _domU, "cpu": _cores, "memory_in_gb": _memory_in_gb, "dom0": _dom0})

        #get version info
        _data_d = {
            "dom0": {},
            "cell": {}
        }
        for _dom0, _domU in _dpairs:
            _imagever = self.__cluctrl.mGetImageVersion(_dom0)
            _data_d["dom0"][_dom0] = _imagever

        ebLogTrace(f"*** Imageinfo of all dom0s: {_data_d['dom0']}")
        _cells = list(self.__cluctrl.mReturnCellNodes(aIsClusterLessXML=self.__cluctrl.mIsClusterLessXML()).keys())

        for _cell in _cells:
            _imagever = self.__cluctrl.mGetImageVersion(_cell)
            _data_d["cell"][_cell] = _imagever
        ebLogTrace(f"*** Imageinfo of all cells: {_data_d['cell']}")

        cluster_detail["cpu_memory_info"] = domu_info
        cluster_detail["image_version"] = _data_d
        ebLogInfo(f"cluster detail json obtained : {json.dumps(cluster_detail, indent=4)}")
        _reqobj = self.__cluctrl.mGetRequestObj()
        if _reqobj is not None:
            _reqobj.mSetData(json.dumps(cluster_detail, sort_keys=True))
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_reqobj)
        else:
            raise ExacloudRuntimeError("Request Object cannot be null")

    def mGetAsmDbSnmpPasswords(self, _aOptions=None):
        aJsonKeyData = {}
        _err = None
        _rc = -1
        
        try:
            for _ , _domu  in self.__cluctrl.mReturnDom0DomUPair():
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_domu)

                # Reset interface to
                _cmd  = '/var/opt/oracle/ocde/rops get_creg_key grid asmsnmp'           
                _i, _o, _e = _node.mExecuteCmd(_cmd)
                if _node.mGetCmdExitStatus():
                    ebLogInfo('Asmsnmp password cmd %s returned %s, error %s' % (_cmd, str(_o.readlines()), str(_e.readlines())))
                    _err = _e.readlines()
                    continue
            
                _out = _o.readlines()
                _asmsnmppasswd = _out[0].strip()
                _aDbName = _aOptions.dbsid
                ebLogInfo("_aDbName = " + _aDbName)
                _dbsnmppasswd = ""
                if (_aDbName  != ""):
                    _cmd = '/var/opt/oracle/ocde/rops get_creg_key ' + _aDbName + ' dbsnmp_passwd'
                    _i, _o, _e = _node.mExecuteCmd(_cmd)
                    if _node.mGetCmdExitStatus():
                        ebLogInfo('Dbsnmp password cmd %s returned %s, error %s' % (_cmd, str(_o.readlines()), str(_e.readlines())))
                        _err = _e.readlines()
                        continue
            
                    _out = _o.readlines()
                    _dbsnmppasswd = _out[0].strip()
                _rc = 0
                _err = None
            
                aJsonKeyData['asmsnmppassword'] = _asmsnmppasswd
                aJsonKeyData['dbsnmppassword'] = _dbsnmppasswd            
                _node.mDisconnect()            
                break
        except Exception as e:
            _rc = -1
            _err = 'Exception during asm, db snmp password command execution: '+ str(e)
            ebLogError('*** ' + str(_err))
        self.mUpdateRequestData(_aOptions, _rc, aJsonKeyData, _err)
        if _rc != 0 :
            raise ExacloudRuntimeError(0x0798, 0xA, _err)
        return _rc

    def mEMDBDetails(self, _aOptions=None):
        aJsonKeyData = {}
        _rc = -1
        _err = None
        _dbsid = _aOptions.dbsid

        try:
            for _ , _domu  in self.__cluctrl.mReturnDom0DomUPair():
                _node = exaBoxNode(get_gcontext())
                _node.mSetUser('grid')
                _node.mConnect(aHost=_domu)

                # Get the service name (service_name) using rops.
                _cmd = "/var/opt/oracle/ocde/rops get_creg_key " \
                     + _dbsid + " service_name"
                _i, _o, _e = _node.mExecuteCmd(_cmd)
                if _node.mGetCmdExitStatus():
                    ebLogInfo('DB SERVICE NAME cmd %s returned %s, error %s' % (_cmd, str(_o.readlines()), str(_e.readlines())))
                    _err = _e.readlines()
                    continue

                _out = _o.readlines()
                _dbservicename = _out[0].strip()

                # Get the database home (db_home) using rops.
                _cmd = "/var/opt/oracle/ocde/rops get_creg_key " \
                     + _dbsid + " db_home"
                _i, _o, _e = _node.mExecuteCmd(_cmd)
                if _node.mGetCmdExitStatus():
                    ebLogInfo('DB HOME cmd %s returned %s, error %s' % (_cmd, str(_o.readlines()), str(_e.readlines())))
                    _err = _e.readlines()
                    continue

                _out = _o.readlines()
                _dbhome = _out[0].strip()

                # Get the database name (dbname) using rops.
                _cmd = "/var/opt/oracle/ocde/rops get_creg_key " \
                     + _dbsid + " dbname"
                _i, _o, _e = _node.mExecuteCmd(_cmd)
                if _node.mGetCmdExitStatus():
                    ebLogInfo('DB NAME cmd %s returned %s, error %s' % (_cmd, str(_o.readlines()), str(_e.readlines())))
                    _err = _e.readlines()
                    continue

                _out = _o.readlines()
                _dbname = _out[0].strip()

                # Get the database instances using srvctl.
                _dbUniqNameCmd = "/var/opt/oracle/ocde/rops get_creg_key " \
                     + _dbsid + " db_unique_name"
                _cmd = "srvctl status database -db `" \
                     + _dbUniqNameCmd + "` | cut -d ' ' --output-delimiter ',' -f 2,7 | tr '\n' ' '"
                _i, _o, _e = _node.mExecuteCmd(_cmd)
                if _node.mGetCmdExitStatus():
                    ebLogInfo('DB INSTANCES cmd %s returned %s, error %s' % (_cmd, str(_o.readlines()), str(_e.readlines())))
                    _err = _e.readlines()
                    continue

                _out = _o.readlines()
                _dbInstances = _out[0].strip()

                # Get the database role using srvctl.
                _cmd = "srvctl config database -db `" + _dbUniqNameCmd + "` " \
                     + "| grep 'Database role:' | cut -d ' ' -f 3"
                _i, _o, _e = _node.mExecuteCmd(_cmd)
                if _node.mGetCmdExitStatus():
                    ebLogInfo('DB ROLE cmd %s returned %s, error %s' % (_cmd, str(_o.readlines()), str(_e.readlines())))
                    _err = _e.readlines()
                    continue

                _out = _o.readlines()
                _dbRole = _out[0].strip()

                _rc = 0
                _err = None

                aJsonKeyData['DB_SERVICE_NAME'] = _dbservicename
                aJsonKeyData['DB_HOME'] = _dbhome
                aJsonKeyData['DB_NAME'] = _dbname
                aJsonKeyData['DB_INSTANCES'] = _dbInstances
                aJsonKeyData['DB_ROLE'] = _dbRole

                ebLogInfo('aJsonKeyData is  ' + str(aJsonKeyData))
                _node.mDisconnect()
                break
        except Exception as e:
            _rc = -1
            _err = 'Exception during retrieving DB details for EM : '+ str(e)
            ebLogError('*** ' + str(_err))
        self.mUpdateRequestData(_aOptions, _rc, aJsonKeyData, _err)
        if _rc != 0:
            raise ExacloudRuntimeError(0x0797, 0xA, _err)
        return _rc

    def mEMClusterDetails(self, _aOptions=None):
        aJsonKeyData = {}
        _rc = -1
        _err = None
        _firstNode = True
        _isOCI = self.__cluctrl.mIsExabm()
        _allNodeCommands = self.mGetEMClusterAllNodeKeyCommandDict(_isOCI)
        _currentNodeNum = 1

        try:
            for _ , _domu  in self.__cluctrl.mReturnDom0DomUPair():
                _node = exaBoxNode(get_gcontext())
                _node.mSetUser('grid')
                _node.mConnect(aHost=_domu)
                _isNamespaceEnabled = self.mGetNamespaceStatus(_node)
                aJsonKeyData["IS_NAMESPACE_ENABLED"] = _isNamespaceEnabled
                
                if _firstNode:
                    _firstNodeCommands = self.mGetEMClusterKeyCommandDict(_isOCI, 
                                                                              _isNamespaceEnabled)
                    for _key, _cmd in six.iteritems(_firstNodeCommands):
                        ebLogInfo('key is ' + _key)
                        ebLogInfo('cmd is ' + _cmd)
                        _i, _o, _e = _node.mExecuteCmd(_cmd)
                        if _node.mGetCmdExitStatus():
                            ebLogInfo('EM cluster details cmd %s returned %s, error %s' % (_cmd, str(_o.readlines()), str(_e.readlines())))
                            _err = _e.readlines()
                            continue

                        _out = _o.readlines()
                        aJsonKeyData[_key] = _out[0].strip()
                _firstNode = False

                for _key, _cmd in six.iteritems(_allNodeCommands):
                    ebLogInfo('key is ' + _key)
                    ebLogInfo('cmd is ' + _cmd)
                    _i, _o, _e = _node.mExecuteCmd(_cmd)
                    if _node.mGetCmdExitStatus():
                        ebLogInfo('EM cluster details cmd %s returned %s, error %s' % (_cmd, str(_o.readlines()), str(_e.readlines())))
                        _err = _e.readlines()
                        continue
                    _out = _o.readlines()
                    aJsonKeyData[_key + str(_currentNodeNum)] = _out[0].strip()

                _perNodeCommands = self.mGetEMClusterPerNodeCommands(_isOCI, 
                                                                     _currentNodeNum,
                                                                     _domu)

                for _key, _cmd in six.iteritems(_perNodeCommands):
                    ebLogInfo('key is ' + _key)
                    ebLogInfo('cmd is ' + _cmd)
                    _i, _o, _e = _node.mExecuteCmd(_cmd)
                    if _node.mGetCmdExitStatus():
                        ebLogInfo('EM cluster details cmd %s returned %s, error %s' % (_cmd, str(_o.readlines()), str(_e.readlines())))
                        _err = _e.readlines()
                        continue
                    _out = _o.readlines()
                    aJsonKeyData[_key] = _out[0].strip()

                _currentNodeNum = _currentNodeNum + 1
            ebLogInfo(aJsonKeyData)
            _rc = 0
            _err = None

        except Exception as e:
            _rc = -1
            _err = 'Exception occured during EM cluster details: '+ str(e)
            ebLogError('*** ' + str(_err))
        self.mUpdateRequestData(_aOptions, _rc, aJsonKeyData, _err)
        if _rc != 0:
            raise ExacloudRuntimeError(0x0799, 0xA, _err)
        return _rc

    def mGetEMClusterPerNodeCommands(self, isOCI, nodeIndex, nodeName):
        _dict = {}
        _dict["NET1_HOST" 
            + str(nodeIndex) 
            + "_VIP_NAME"] = "srvctl config vip -node " + nodeName \
                           + " | grep \"VIP Name:\" " \
                           + "| cut -d \" \" -f 3"
       
        if isOCI :                                                  
            _dict["NET2_HOST" 
                + str(nodeIndex) 
                + "_VIP_NAME"] = "srvctl config vip -node " + nodeName \
                               + " | grep -A1 \"network number 2\" " \
                               + "| grep \"VIP IPv4\" " \
                               + "| cut -d \" \" -f 4"
        else:
            _dict["NET2_HOST" 
                + str(nodeIndex) 
                + "_VIP_NAME"] = "srvctl config vip -node " + nodeName \
                               + " | grep \"VIP Name:\" " \
                               + "| cut -d \" \" -f 3"

        _dict["HOST"
            + str(nodeIndex)
            + "_ASM_INSTANCE"] = "/var/opt/oracle/ocde/rops get_creg_key grid sid"

        return _dict

    def mGetEMClusterKeyCommandDict(self, isOCI, isNamespaceEnabled):
        _dict = {}

        _dict["GRID_HOME"] = "cat /var/opt/oracle/creg/grid/grid.ini " \
                           + "| grep \"^oracle_home\" " \
                           + "| cut -d \"=\" -f 2"
        _dict["ORA_CLUSTER_NAME"] = "cemutlo -n"
        _dict["MACHINE_SCAN1"] = "srvctl config scan " \
                               + "| grep \"SCAN.*1.*IPv4 VIP:\" " \
                               + "| cut -d \" \" -f 5"
                               
        _dict["MACHINE_SCAN2"] = "srvctl config scan " \
                               + "| grep \"SCAN.*2.*IPv4 VIP:\" " \
                               + "| cut -d \" \" -f 5"
                               
        _dict["MACHINE_SCAN3"] = "srvctl config scan " \
                               + "| grep \"SCAN.*3.*IPv4 VIP:\" " \
                               + "| cut -d \" \" -f 5"

        _dict["SCAN_HOST1"] = "crsctl stat res ora.LISTENER_SCAN1.lsnr " \
                            + "| grep \"STATE=ONLINE\" " \
                            + "| cut -d \" \" -f 3"
                            
        _dict["SCAN_HOST2"] = "crsctl stat res ora.LISTENER_SCAN2.lsnr " \
                            + "| grep \"STATE=ONLINE\" " \
                            + "| cut -d \" \" -f 3"
                            
        _dict["SCAN_HOST3"] = "crsctl stat res ora.LISTENER_SCAN3.lsnr " \
                            + "| grep \"STATE=ONLINE\" " \
                            + "| cut -d \" \" -f 3"
                            
        _dict["ASMNET1LSNR_PORT"] = "lsnrctl status ASMNET1LSNR_ASM " \
                                  + "| grep \"PROTOCOL=tcp\" " \
                                  + "| head -n 1 " \
                                  + "| cut -d \"=\" -f 6 " \
                                  + "| cut -d \")\" -f 1"

        _dict["LOGICAL_AD_CODE"] = "echo \"`curl -s -H 'Authorization: Bearer Oracle' -m 5 http://169.254.169.254/opc/v2/instance/ " \
                                 + "| grep \"availabilityDomain\" " \
                                 + "| cut -d '\"' -f 4`\""

        if isOCI:

            _dict["NET1_SCAN_NAME"] = "srvctl config scan -netnum 1 " \
                                    + "| grep \"SCAN name:\" " \
                                    + "| cut -d \" \" -f 3 " \
                                    + "| cut -d \",\" -f 1"

            _dict["NET1_SCAN_PORT"] = "srvctl config scan_listener -netnum 1 " \
                                    + "| grep \"Endpoints: TCP:\" " \
                                    + "| cut -d \":\" -f 3 " \
                                    + "| cut -d \"/\" -f 1"
        else:
           _dict["NET1_SCAN_NAME"] = "srvctl config scan " \
                                   + "| grep \"SCAN name:\" " \
                                   + "| cut -d \" \" -f 3 " \
                                   + "| cut -d \",\" -f 1"
                                   
           _dict["NET1_SCAN_PORT"] = "srvctl config scan_listener " \
                                   + "| grep \"Endpoints: TCP:\" " \
                                   + "| cut -d \":\" -f 3 " \
                                   + "| cut -d \"/\" -f 1"

        """
        NET2 SCAN is not present in the namespace env
        """
        if not isNamespaceEnabled :
            if isOCI :
                _dict["NET2_SCAN_NAME"] = "srvctl config scan -netnum 2  " \
                                        + "| grep \"SCAN name:\" " \
                                        + "| cut -d \" \" -f 3 " \
                                        + "| cut -d \",\" -f 1"
                                        
                _dict["NET2_SCAN_PORT"] = "srvctl config scan_listener -netnum 2 " \
                                        + "| grep \"Endpoints: TCP:\" " \
                                        + "| cut -d \":\" -f 3 " \
                                        + "| cut -d \"/\" -f 1"
                                        
                _dict["LISTENER_BKUP_SCAN_NAME"] = "echo LISTENER_BKUP_SCAN1_NET2"
                
                _dict["NET2_SCAN_HOST"] = "crsctl stat res ora.LISTENER_BKUP_SCAN1_NET2.lsnr " \
                                        + "| grep \"STATE=ONLINE\" " \
                                        + "|  cut -d \" \" -f 3"
                                        
                _dict["MACHINE_NET2_SCAN"] = "srvctl config scan -netnum 2 " \
                                           + "| grep \"SCAN.*1.*IPv4 VIP:\" " \
                                           + "| cut -d \" \" -f 5"
                                           
            else:
                _dict["NET2_SCAN_NAME"] = "srvctl config scan " \
                                        + "| grep \"SCAN name:\" " \
                                        + "| cut -d \" \" -f 3 " \
                                        + "| cut -d \",\" -f 1"
                                        
                _dict["NET2_SCAN_PORT"] = "srvctl config scan_listener " \
                                        + "| grep \"Endpoints: TCP:\" " \
                                        + "| cut -d \":\" -f 3 " \
                                        + "| cut -d \"/\" -f 1"
                                        
                _dict["LISTENER_BKUP_SCAN_NAME"] = "echo LISTENER_SCAN1"
                _dict["NET2_SCAN_HOST"] = "crsctl stat res ora.LISTENER_SCAN1.lsnr " \
                                        + "| grep \"STATE=ONLINE\" " \
                                        + "| cut -d \" \" -f 3"
                                        
                _dict["MACHINE_NET2_SCAN"] = "srvctl config scan " \
                                           + "| grep \"SCAN.*1.*IPv4 VIP:\" " \
                                           + "| cut -d \" \" -f 5"

        
        return _dict

    def mGetEMClusterAllNodeKeyCommandDict(self, isOCI):
        _dict = {}
        _dict["ASMNET1LSNR_HOST"] = "lsnrctl status ASMNET1LSNR_ASM " \
                                  + "| grep \"PROTOCOL=tcp\" " \
                                  + "| head -n 1 " \
                                  + "| cut -d \"=\" -f 5 " \
                                  + "| cut -d \")\" -f 1 "
        return _dict

    def mGetNamespaceStatus(self,aNode):
        """
        Determines if Namespace is enabled.
        Not enabled if ip netns returns empty string.
        """
        _namespacecmd = "ip netns"
        _retVal = True
        _i, _o, _e = aNode.mExecuteCmd(_namespacecmd)
        if aNode.mGetCmdExitStatus():
            ebLogInfo('cmd %s returned %s, error %s' % (_namespacecmd, 
                                                            str(_o.readlines()), 
                                                            str(_e.readlines())))
        _out = _o.readlines()
        
        if not _out:
            _retVal = False
            
        return _retVal

    def mUpdateRequestData(self, aOptions, rc, aData, err):
        """
        Updates request object with the response payload
        """
        _reqobj = self.__cluctrl.mGetRequestObj()
        _response = {}
        _response["success"] = "True" if (rc == 0) else "False"
        _response["error"] = err
        _response["output"] = aData
        if _reqobj is not None:
            _db = ebGetDefaultDB()
            _reqobj.mSetData(json.dumps(_response, sort_keys = True))
            _db.mUpdateRequest(_reqobj)

        ebLogJson(json.dumps(_response, indent=4, sort_keys = True))

    def mVMPreChecks(self, aHost=None):

        #
        # Checks if VM/s already exist/s
        #
        _exists = False
        _node = exaBoxNode(get_gcontext())
        for _dom0, _domU in self.__cluctrl.mReturnDom0DomUPair():
            # if aHost is provided then do pre-checks for only that aHost(dom0)
            # otherwise do pre-checks for all the dom0's.
            if ((aHost and _dom0 == aHost) or not aHost):
                _node.mConnect(aHost=_dom0)
                _vm_image='/EXAVMIMAGES/GuestImages/%s/System.img' % (_domU)
                _rc = _node.mFileExists(_vm_image)
                if _rc:
                    ebLogWarn('*** VM %s already exists' % (_domU))
                    _exists = True
                else:
                    if self.__cluctrl.mIsDebug():
                        ebLogInfo('*** VM %s is not present' % (_domU))
                _node.mDisconnect()

        return _exists

    # Dom0 test:
    # Check for available free memory in dom0.
    # The memsize in XML should not be greater than the avaiable free memory
    # in dom0 during pre-provisioning.

    def mCheckDom0Mem(self, aHost):

        _host = aHost
        _ebox = self.__cluctrl

        _dom0List = [_dom0 for _dom0, _ in _ebox.mReturnDom0DomUPair()]
        if _host not in _dom0List:
            ebLogError('ERROR: Node type for which available free memory is checked is not dom0.')
            return False

        _vm = getHVInstance(_host)
        _memfree = _vm.getDom0FreeMem()
        _memint = int(_memfree) / 1024

        # All MemSize in XML are same
        _memXML = _ebox.mGetVMSizesConfig().mGetVMSize('Large').mGetVMSizeAttr('MemSize')
        ebLogInfo('*** Memory size requirement in XML is %s' %(_memXML))
        ebLogInfo('*** Memory available on %s is %dGb' %(_host, _memint))

        if _memint < (int(_memXML[:-2])):
            ebLogError('*** Not enough memory available on dom0 %s' %(_host))
            _domUs = _vm.mRefreshDomUs()
            ebLogError("***List of created VMs:")
            for _line in _domUs:
                ebLogError(_line)
            return False
        else:
            if _ebox.mIsDebug():
                ebLogInfo('*** Enough memory available on dom0 %s' %(_host))
            return True
    # end

    # Check for available free space on given parition.
    #return True: if used space less than threshold value
    def mCheckUsedSpace(self, aHost, aPartition, aThreshold):

        _host       = aHost
        _partition  = aPartition
        _threshold  = aThreshold
        _ebox       = self.__cluctrl

        _cmdstr = 'df -P ' + _partition + ' | tail -1 | awk \'0+$5 >= ' + _threshold + ' {print}\''
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_host)
        _, _o, _ = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        _node.mDisconnect()
        if len(_out):
            ebLogDebug('%s partition space used more than threshold value for host - %s' %(_partition,_host))
            return False
        return True
    # end

    def mHostnamesLengthChecks(self):
        _max_hostname_len = 63
        _max_domain_name_len = 199
        #Bug 37747007 - Per VM maker limitations, FQDN max should be 240
        #As Vm Maker concatenate 15 characters by itself for a 255 total 
        _max_FQDN_len = 240

        _vips = self.__cluctrl.mGetClusters().mGetCluster().mGetCluVips()
        _hostnames = self.__cluctrl.mGetMachines().mGetMachineConfigList()
        _scans = self.__cluctrl.mGetScans()
        _networks = self.__cluctrl.mGetNetworks()

        for _, _vip in _vips.items():
            _vip_name = _vip.mGetCVIPName()
            _vip_domain = _vip.mGetCVIPDomainName()

            if len(_vip_name) > _max_hostname_len:
                _err_msg = (f"Invalid VIP hostname length ({len(_vip_name)}"
                            f" characters) for {_vip_name}. The maximum length "
                            "is 63 characters")
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)

            if len(_vip_domain) > _max_domain_name_len:
                _err_msg = ("Invalid VIP domain name length "
                            f"({len(_vip_domain)} characters) for {_vip_domain}"
                            ". The maximum length is 199 characters")
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)

        for _, _hostname in _hostnames.items():
            _mac_hostname = _hostname.mGetMacHostName()
            if len(_mac_hostname) > _max_FQDN_len:
                _err_msg = (f"Invalid machine hostname FQDN length "
                            f"({len(_mac_hostname)} characters) for "
                            f"{_mac_hostname}. The maximum length is 240 "
                             "characters")
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)

        for _scan_id in _scans.mGetScans():
            _scan = _scans.mGetScan(_scan_id)
            if len(_scan.mGetScanName()) > _max_FQDN_len:
                _err_msg = (f"Invalid Scan FQDN length ({len(_scan)} "
                            f"characters) for {_scan}. The maximum length is "
                             "240 characters")
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)

        for _network_id in _networks.mGetNetworkIdList():
            _network = _networks.mGetNetworkConfig(_network_id)

            _hostname = _network.mGetNetHostName()
            _domain = _network.mGetNetDomainName()
            _nat_hostname = _network.mGetNetNatHostName()
            _nat_domain = _network.mGetNetNatDomainName()

            if len(_hostname) > _max_hostname_len:
                _max_len = _max_hostname_len
                _label = "hostname"
                _name = _network.mGetNetHostName()

            elif len(_domain) > _max_domain_name_len:
                _max_len = _max_domain_name_len
                _label = "domain name"
                _name = _network.mGetNetDomainName()

            elif len(_nat_hostname) > _max_hostname_len:
                _max_len = _max_hostname_len
                _label = "NAT hostname"
                _name = _network.mGetNetNatHostName()

            elif len(_nat_domain) > _max_domain_name_len:
                _max_len = _max_domain_name_len
                _label = "NAT domain name"
                _name = _network.mGetNetNatDomainName()

            else:
                continue

            _err_msg = (f"Invalid network {_label} length ({len(_name)} "
                        f"characters) for {_name}. The maximum length is "
                        f"{_max_len} characters")
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorMsg=_err_msg)

    def mCheckASMPassword(self, aDomU):
        # Retrieve active port by using cluster scans
        ebLogInfo("Checking that ASM password is valid.")
        _ebox = self.__cluctrl
        _cluster_scans = self.__cluctrl.mGetClusters().mGetCluster().mGetCluScans()
        if not _cluster_scans:
            _err_msg = ("Cluster scans not found in XML.")
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(_err_msg)
        _scan_name = _cluster_scans[0]
        if not _scan_name:
            _err_msg = ("Scan name not found in XML.")
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(_err_msg)
        _scans = self.__cluctrl.mGetScans()
        _scan_conf = _scans.mGetScan(_scan_name)
        _scan_port = _scan_conf.mGetScanPort()

        # Retrieve current password using rops
        _file_loc = "/var/opt/oracle/ocde/rops"
        _pwd_cmd = f"{_file_loc} get_cprops_key sys"
        ebLogInfo(f"Checking ASM connection in domU: {aDomU}")
        with connect_to_host(aDomU, get_gcontext()) as _node:
            _pwd_out = node_exec_cmd_check(_node, _pwd_cmd).stdout.strip('\n')

            # Fail check if we can't retrieve password
            if not _pwd_out:
                _err_msg = ("Could not get ASM password using rops.")
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)

            # Use given key to log in to SQL
            _gihome, _, _obase = _ebox.mGetOracleBaseDirectories(aDomU = aDomU)
            _orahome_set_cmd = f"true pass && ORACLE_HOME={_gihome};"
            _path_export_cmd = f"export ORACLE_HOME;PATH=$PATH:{_gihome}/bin:{_gihome};export PATH;"
            _sqlplus_cmd = f"{_gihome}/bin/sqlplus -s sys/\"{_pwd_out}\"@{aDomU}:{_scan_port}/+ASM as sysasm"

            # Confirm that the login was able to complete
            try:
                _sqlplus_out = node_exec_cmd_check(_node, f"{_orahome_set_cmd}{_path_export_cmd}{_sqlplus_cmd} <<_EOF\n_EOF")
            except ExacloudRuntimeError as e:
                _err_msg = (f"Could not log in successfully to ASM. Password might have been changed without using dbaascli.")
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)

            ebLogInfo(f"ASM password is valid in domU: {aDomU}")

    @retryOnException(max_times=3, sleep_interval=5)
    def mRunAllPreChecks(self, aVerboseMode=False,aMode=None,aIbTarget=True):

        self.__verbose = aVerboseMode

        self.mNetworkBasicChecks(aVerbose=aVerboseMode)

        self.mHostnamesLengthChecks()

        # Dom0 ipconf check
        # This will raise an exception on error in kvm
        _rc_d = self.mNetworkDom0PreChecks()
        if _rc_d is False and aIbTarget:
            self.mResetIBNetwork(aCheckMode=aMode)
        #
        # Dom0 root partition space and mem check
        #
        _rc = self.mDom0SystemPreChecks()

        return _rc

    ######################################################################
    # mDigTest
    # 
    #        Perform dig test to check if the ip provided is resolvable. 
    # 
    # Parameters:
    #         aIp        - IP address to test
    #         node        - [OPTIONAL] Object which is connected to a machine on which
    #                              the test is to be run. This can be passed in if
    #                              the DigTest is to be run on a specific node dom0
    #                              or domU.
    #
    # Returns:
    #         True        - If IP is resolvable 
    #        False        - Otherwise.
    # 
    # History:
    #        Nov, 2018        nkattige        Moved out from cluhealth.py
    # 
    def mDigTest(self, aIp, node = None):

        try:
            # If the node details are passed in use the node to run the 
            # command. 
            if (node is not None) :
                _cmd = "dig @" + aIp + " www.oracle.com +short"
                _i, _out, _e = node.mExecuteCmd(_cmd)
                _o = _out.readlines()
            else:
            # We need to run it on the current machine.
                _out = subprocess.check_output(['dig', "@"+aIp, \
                                                "www.oracle.com", "+short"]).decode('utf8')
                if _out:
                    _o = _out.split('\n')
                else : 
                    ebLogWarn("*** Error: Did not get output from DIG test.")
                    return False
            
            _digstr = "no servers could be reached"
            for _line in _o:
                if _digstr in _line:
                    return False
        except:
            _msg = "*** Error: Exception occured during DIG test for ip = " \
                + aIp
            ebLogWarn(_msg);
            return False

        return True

    def mResetSwitches(self):
        """
        This function fetches master switch node and enables it
        """
        try:

            _host_name = []

            _list = self.__cluctrl.mGetSwitches().mGetSwitchesNetworkId(True)
            for _h in _list:
                _neto = self.__cluctrl.mGetNetworks().mGetNetworkConfig(_h)
                _host_name.append(_neto.mGetNetHostName())

            _cmdstr = 'getmaster'
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_host_name[0])
            _fin, _fout, _ferr = _node.mExecuteCmd(_cmdstr)
            _out = _fout.readlines()
            _node.mDisconnect()

            if _out and len(_out):
                _master = ''.join(_out)

                match = re.search(r'\w+sw-\w+', _master).group()
                if match:
                    ebLogInfo("Master Switch hostname %s" %match)

                    if not match in _host_name:
                        ebLogWarn("Master switch not present in XML configuration file")

                    _node = exaBoxNode(get_gcontext())
                    _node.mConnect(aHost=match)

                    _cmdstr = 'disablesm'
                    _, _fout, _ =  _node.mExecuteCmd(_cmdstr)

                    _cmdstr = 'enablesm'
                    _, _fout, _ = _node.mExecuteCmd(_cmdstr)

                    _node.mDisconnect()
                else:
                    ebLogError('*** Failed to retrieve master switch node from node {}'.format(_host_name[0]))
            else:
                ebLogError('*** Failed to retrieve master switch node from node {}'.format(_host_name[0]))
        except Exception as e:
            ebLogError('*** Fatal ERROR - Reset Switch failed')

    def mGeneratePassword(self, aClusterID, aClusterName, aHostName):
        """
         This method generates strong password
         Password  will be generated with the combnination of clusterId, clusterName, Hostname 
         Sample Input params: clusterId: "c0_clusterHome", clusterName: "paas-cluste-634", Hostname: "slcs16adm03vm05-v303.us.oracle.com"
         Sample output: C~0:_+c[P@a#A]s&S(l%C)s
        """
        def capitalize_first_nth(aInput, aIndex):
            s = aInput.title()
            return s[:1].upper() + s[1:aIndex].lower() + s[aIndex:].capitalize()

        def add_special_characters(aInput):
            special_chars = ['~', '~', ':', '+', '[', '@', '#', ']', '&', '(', '%', ')', '*', '-', '^']
            def generate():
                for sp_char, elem in zip(special_chars, aInput) :
                    try:
                        yield sp_char
                        yield elem
                    except StopIteration:
                        return
            ret = generate()
            next(ret)
            return ret

        aClusterID = capitalize_first_nth(aClusterID[:4], 2)
        aClusterName = capitalize_first_nth(aClusterName[:4], 2)
        aHostName = capitalize_first_nth(aHostName[:4], 2)
        result = list(add_special_characters(aClusterID + aClusterName + aHostName))
        new_pass = ''.join(random.sample(result,len(result)))
        new_pass = new_pass.encode("utf-8")
        return b64encode(new_pass)

    def mCheckScanName(self):

        _cluScans = self.__cluctrl.mGetClusters().mGetCluster().mGetCluScans()
        _cluScans = _cluScans[0]
        _scans = self.__cluctrl.mGetScans().mGetScans()
        for _scan_id in _scans:
            _o = self.__cluctrl.mGetScans().mGetScan(_scan_id)
            if _o.mGetCluId() == _cluScans:
                _scanName = _o.mGetScanName()
                ebLogInfo(f"scan name:{_scanName}")
                if _scanName:
                    _scan_name = _scanName.split('.')[0]
                    if _scan_name in ["", "null"]:
                        raise ExacloudRuntimeError(0x0803, 0xA, "Scan Name Check Failed")

    def mCheckClusterIntegrity(self, aScanIPEnabled, aRaiseError=True, aDomUList= None):

        _scan_ip_enabled = aScanIPEnabled
        def _mExecute(aNode, aCmd, aOperation):
            _node = aNode

            ebLogInfo(f'Executing cmd : su - oracle -c \'{aCmd}\'')
            _i, _o, _e = _node.mExecuteCmd(f'su - oracle -c \'{aCmd}\'')
            _rc = _node.mGetCmdExitStatus()
            
            if _rc:
                _errLines = _o.readlines()
                ebLogError("*** {}".format(''.join(_errLines).strip()))
            else:
                ebLogInfo("*** Verification of {} was successful.".format(aOperation))

            return _rc

        if aDomUList is None:
            _domu_list = [ _domu for _ , _domu in self.__cluctrl.mReturnDom0DomUPair()]
        else:
            _domu_list = aDomUList
        _domu_str = ','.join(_domu_list)

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_domu_list[0])

        _cmd_pfx, _, _ = self.mGetEbox().mGetOracleBaseDirectories(aDomU = _domu_list[0])
        _cmd_pfx += '/bin/cluvfy comp '

        #Check reachability between nodes
        _cmd_str = _cmd_pfx + 'nodereach  -n {}'.format(_domu_str)
        _rc = _mExecute(_node, _cmd_str, "Node reachability")
        if _rc:
            ebLogError('*** Reachability between nodes failed...')
            if aRaiseError:
                _node.mDisconnect()
                raise ExacloudRuntimeError(0x0782, 0xA, "Reachability between nodes Failed")

        #Check cluster manager integrity
        _cmd_str = _cmd_pfx + 'clumgr -n {}'.format(_domu_str)
        _rc = _mExecute(_node, _cmd_str, "Cluster manager")
        if _rc:
            ebLogError('*** Cluster manager integrity check failed...')
            if aRaiseError:
                _node.mDisconnect()
                raise ExacloudRuntimeError(0x0782, 0xA, "Cluster manager integrity check Failed")

        #Check Voting Disk Udev settings
        _cmd_str = _cmd_pfx + 'vdisk -n {}'.format(_domu_str)
        _rc = _mExecute(_node, _cmd_str, "Voting disk")
        if _rc:
            ebLogError('*** vdisk component verification failed...')
            if aRaiseError:
                _node.mDisconnect()
                raise ExacloudRuntimeError(0x0782, 0xA, "vdisk component verification Failed")

        #Check CRS integrity
        _cmd_str = _cmd_pfx + 'crs -n {}'.format(_domu_str)
        _rc = _mExecute(_node, _cmd_str, "CRS")
        if _rc:
            ebLogError('*** CRS integrity check failed...')
            if aRaiseError:
                _node.mDisconnect()
                raise ExacloudRuntimeError(0x0782, 0xA, "CRS Integrity Check Failed")

        #Check ASM integrity
        if not self.mGetEbox().mIsXS():
            _cmd_str = _cmd_pfx + 'asm -n {}'.format(_domu_str)
            _rc = _mExecute(_node, _cmd_str, "ASM")
            if _rc:
                ebLogError('*** ASM integrity check failed...')
                if aRaiseError:
                    _node.mDisconnect()
                    raise ExacloudRuntimeError(0x0782, 0xA, "ASM Integrity Check Failed")

        #Check SCAN integrity
        if _scan_ip_enabled == True:
            _cmd_str = _cmd_pfx + 'scan'
            _rc = _mExecute(_node, _cmd_str, "IP SCAN")
            if _rc:
                ebLogError('*** SCAN integrity check failed...')
                if aRaiseError:
                    _node.mDisconnect()
                    raise ExacloudRuntimeError(0x0782, 0xA, "SCAN Integrity Check Failed")

        _node.mDisconnect()

    # 
    # mCheckVMTimeDrift: Detects if there is any time difference 
    # between the VMs or between VMs and NTP server. 
    # A threshold of 3 seconds is used to declare that the time difference is
    # erroneous. 
    # Output of chronyc tracking:
    #
    #    [root@slcs08adm05vm06-v263 ~]# chronyc tracking
    #    ....
    #    ....
    #    Reference ID    : 0AF60001 (ucf-mdf1-rtr-9.ucf.oracle.com)
    #    Stratum         : 4
    #    Ref time (UTC)  : Fri Nov 29 11:44:57 2019
    #    System time     : 0.000007713 seconds slow of NTP time
    #    Last offset     : -0.000002363 seconds
    #    RMS offset      : 0.000015207 seconds
    #    .......
    # chronyc -c tracking is used to extract 'System time' and is used 
    # to detect the above mentioned time differences.
    #
    def mCheckVMTimeDrift(self):
        _diff = 0
        _threshold = 3 
        _arr = []
        
        for _, _domU in self.__cluctrl.mReturnDom0DomUPair():
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_domU)

            _, _o, _ = _node.mExecuteCmd("chronyc -c tracking")

            # Fetch the system time from the chronyc tracking cmd
            _output = float(_o.read().split(',')[4])
            if _output > _threshold:
                ebLogError("The VM (%s) and the NTP server have considerable system time difference (%d seconds)" % (_domU, _output))

            _arr.append(_output)
            for x in _arr:
                _diff = abs(x - _output)
                if _diff > _threshold:
                    ebLogError("The VM's have considerable time difference (%d seconds) amongst them." % _diff)

            _node.mDisconnect()
        return 0

    def validate_hw_results(self, aStep, aHWResult):
        _step = aStep
        _hw_result = aHWResult
        _output = {}

        if _step == "ESTP_PREVM_CHECKS":
            _output = { "healthy_nodes": [], "unhealthy_nodes": [] }
            for _node_data in _hw_result["nodes"]:
                _rc = True
                _host = _node_data.get("hostname") + '.' + _node_data.get("domainname")
                _node_data['host'] = _host
                for _key, _value in list(_node_data.items()):
                    if _key not in  ["hostname", "domainname", "hw_type"] and _value == 'abnormal':
                        ebLogWarn('*** {0} validatation failed...'.format(_host))
                        _rc = False
                if _rc == True:
                    _node_data.pop("error_list",None)
                    _output['healthy_nodes'].append(_node_data)
                else:
                    _output['unhealthy_nodes'].append(_node_data)
                    _rc = False
        elif _step == "ELASTIC_SHAPES_VALIDATION":
            _output = { "quarter-rack-healthy-servers" : [], "quarter-rack-faulty-servers":[],
                        "elastic-healthy-servers": [], "elastic-faulty-servers":[] }
            for _host, _result in list(_hw_result.items()):
                _nodeInfo = _result.get('node_info', {})
                if _nodeInfo:
                    _nodeInfo = _nodeInfo[0]
                    _nodeType = _nodeInfo.get("node_type", "")
                    _error_list = _nodeInfo.get('error_list', [])
                    _nodeInfo.pop("node_type",None)
                    if _error_list:
                        if self.__cluctrl.mCheckConfigOption('ignore_m2_sys_error'):
                            _only_m2_sys_err = all("m2_sys" in str(error.get("error-message", "")).lower() for error in _error_list)
                            if _error_list and _only_m2_sys_err:
                                continue
                        if _nodeType == "quarter-rack-servers":
                            _output["quarter-rack-faulty-servers"].append(_nodeInfo)
                        elif _nodeType == "elastic-servers":
                            _output["elastic-faulty-servers"].append(_nodeInfo)
                    else:
                        _nodeInfo.pop("error_list",None)
                        if _nodeType == "quarter-rack-servers":
                            _output["quarter-rack-healthy-servers"].append(_nodeInfo)
                        elif _nodeType == "elastic-servers":
                            _output["elastic-healthy-servers"].append(_nodeInfo)

        ebLogTrace(f"VALIDATE HW RESULTS: {_output}")
        return _output

    def mRunPreVMChecks(self, aNodeInfo, aConfig, aTimeout=300):
        # Set init variables
        _nodeInfo, _config = aNodeInfo, aConfig
        _event_timeout = aTimeout
        _step = "ESTP_PREVM_CHECKS"

        # Get HW lists
        _dom0_list = _nodeInfo["dom0s"] if "dom0s" in _nodeInfo else []
        _cell_list = _nodeInfo["cells"] if "cells" in _nodeInfo else []
        _switch_list = _nodeInfo["switches"] if "switches" in _nodeInfo else []

        # Set process manager and processes dictionary
        ebLogInfo(f"Adding {_step} processes to be ran in parallel.")
        _procManager = ProcessManager()
        _hw_health_table = _procManager.mGetManager().dict()
        _hw_health_table["nodes"] = []

        # Append all processes
        for _dom0 in _dom0_list:
            _sanityTestHandler = ebCluDom0SanityTests(self, _dom0, 'prevm-checks', _step, None, False, None, _config['dom0_prechecks'], None)
            _process = ProcessStructure(_sanityTestHandler.run, aArgs=[_hw_health_table], aId=_dom0)
            _process.mSetMaxExecutionTime(_event_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)

        for _cell in _cell_list:
            _sanityTestHandler = ebCluCellSanityTests(self, _cell, 'prevm-checks', _step, False, _config['cell_prechecks'])
            _process = ProcessStructure(_sanityTestHandler.run, aArgs=[_hw_health_table], aId=_cell)
            _process.mSetMaxExecutionTime(_event_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)

        for _switch in _switch_list:
            _sanityTestHandler = ebCluIbSwitchSanityTests(self, _switch, 'prevm-checks', _step, _config['ibswitch_prechecks'])
            _process = ProcessStructure(_sanityTestHandler.run, aArgs=[_hw_health_table], aId=_switch)
            _process.mSetMaxExecutionTime(_event_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)
        
        # Wait for processes to end
        ebLogInfo(f"Waiting for {_step} processes to end. This might take a while.")
        _procManager.mJoinProcess()

        # Make serializable dict
        result = dict(_hw_health_table)
        ebLogTrace(f"VALIDATE RESULT: {result}")
        return result

    def mRunElasticShapesValidation(self, aNodeInfo, aConfig, aTimeout=300):
        # Set init variables
        _nodeInfo, _config = aNodeInfo, aConfig
        _event_timeout = aTimeout
        _step = "ELASTIC_SHAPES_VALIDATION"

        # Get node info and HW lists
        _osType = _nodeInfo["ostype"]
        _model_subType = _nodeInfo["model_subtype"]
        _multivm = _nodeInfo["shared_env"]
        _operationType = _nodeInfo["operationtype"]
        _quarter_rack_dom0s = _nodeInfo["quarter_rack_dom0s"] if "quarter_rack_dom0s" in _nodeInfo else []
        _quarter_rack_cells = _nodeInfo["quarter_rack_cells"] if "quarter_rack_cells" in _nodeInfo else []
        _quarter_rack_switches = _nodeInfo["quarter_rack_switches"] if "quarter_rack_switches" in _nodeInfo else []
        _elastic_dom0s = _nodeInfo["elastic_dom0s"] if "elastic_dom0s" in _nodeInfo else []
        _elastic_cells = _nodeInfo["elastic_cells"] if "elastic_cells" in _nodeInfo else []
        _elastic_switches = _nodeInfo["elastic_switches"] if "elastic_switches" in _nodeInfo else []

        # Set process manager and processes dictionary
        ebLogInfo(f"Adding {_step} processes to be ran in parallel.")
        _procManager = ProcessManager()
        _hw_health_table = _procManager.mGetManager().dict()

        # Append all processes
        for _quarter_rack_dom0 in _quarter_rack_dom0s:
            _sanityTestHandler = ebCluDom0SanityTests(self, _quarter_rack_dom0, 'quarter-rack-servers', _step, _osType, _multivm, _operationType, _config['dom0_prechecks'], _model_subType)
            _process = ProcessStructure(_sanityTestHandler.run, aArgs=[_hw_health_table], aId=_quarter_rack_dom0)
            _process.mSetMaxExecutionTime(_event_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)

        for _quarter_rack_cell in _quarter_rack_cells:
            _sanityTestHandler = ebCluCellSanityTests(self, _quarter_rack_cell, 'quarter-rack-servers', _step, _multivm, _config['cell_prechecks'])
            _process = ProcessStructure(_sanityTestHandler.run, aArgs=[_hw_health_table], aId=_quarter_rack_cell)
            _process.mSetMaxExecutionTime(_event_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)

        for _quarter_rack_switch in _quarter_rack_switches:
            _sanityTestHandler = ebCluIbSwitchSanityTests(self, _quarter_rack_switch, 'quarter-rack-servers', _step, _config['ibswitch_prechecks'])
            _process = ProcessStructure(_sanityTestHandler.run, aArgs=[_hw_health_table], aId=_quarter_rack_switch)
            _process.mSetMaxExecutionTime(_event_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)

        for _elastic_dom0 in _elastic_dom0s:
            _sanityTestHandler = ebCluDom0SanityTests(self, _elastic_dom0, 'elastic-servers', _step, _osType, _multivm, _operationType, _config['dom0_prechecks'], _model_subType)
            _process = ProcessStructure(_sanityTestHandler.run, aArgs=[_hw_health_table], aId=_elastic_dom0)
            _process.mSetMaxExecutionTime(_event_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)

        for _elastic_cell in _elastic_cells:
            _sanityTestHandler = ebCluCellSanityTests(self, _elastic_cell, 'elastic-servers', _step, _multivm, _config['cell_prechecks'])
            _process = ProcessStructure(_sanityTestHandler.run, aArgs=[_hw_health_table], aId=_elastic_cell)
            _process.mSetMaxExecutionTime(_event_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)

        for _elastic_switch in _elastic_switches:
            _sanityTestHandler = ebCluIbSwitchSanityTests(self, _elastic_switch, 'elastic-servers', _step, _config['ibswitch_prechecks'])
            _process = ProcessStructure(_sanityTestHandler.run, aArgs=[_hw_health_table], aId=_elastic_switch)
            _process.mSetMaxExecutionTime(_event_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)

        # Wait for processes to end
        ebLogInfo(f"Waiting for {_step} processes to end. This might take a while.")
        _procManager.mJoinProcess()

        # Make serializable dict
        result = dict(_hw_health_table)
        ebLogTrace(f"VALIDATION RESULT: {result}")
        return result

    def mRunHWSanityTest(self, aStep="", aNodeInfo=None, aConfig=None):
        _step = aStep
        _nodeInfo = aNodeInfo
        _config = aConfig

        # Set timeout
        _timeout = self.__cluctrl.mCheckConfigOption('precheck_event_timeout')
        _event_timeout = 300

        if _timeout is not None:
            _event_timeout = int(_timeout)

        # Run checks according to the given step
        if _step in ["ESTP_PREVM_CHECKS"]:
            return self.mRunPreVMChecks(_nodeInfo, _config, aTimeout=_event_timeout)
        
        if _step in ["ELASTIC_SHAPES_VALIDATION"]:
            return self.mRunElasticShapesValidation(_nodeInfo, _config, aTimeout=_event_timeout)

    def mParseHWAlertPayload(self, aOptions):
        _options = aOptions
        _nodeInfo = {}

        # Parse the json and read the attributes
        _inputjson = _options.jsonconf
        if _inputjson:
            _operationType = ""
            _precheck_mode = ""
            _osType = ""
            _model_subType = ""
            _multivm = False
            _quarter_rack_dom0s = []
            _quarter_rack_cells = []
            _quarter_rack_switches = []
            _elastic_dom0s = []
            _elastic_cells = []
            _elastic_switches = []
            if 'operationtype' in _inputjson.keys() and _inputjson['operationtype'].strip():
                _operationType = _inputjson['operationtype'].strip()
            if 'precheckmode' in _inputjson.keys() and _inputjson['precheckmode'].strip():
                _precheck_mode = _inputjson['precheckmode'].strip()
            if 'ostype' in _inputjson.keys() and _inputjson['ostype'].strip():
                _osType = _inputjson['ostype'].strip().lower()
            if 'model_subtype' in _inputjson.keys() and _inputjson['model_subtype'].strip():
                _model_subType = _inputjson['model_subtype'].strip()
            if 'shared_env' in _inputjson.keys() and _inputjson['shared_env']:
                _multivm = _inputjson['shared_env']
            if 'quarter-rack-servers' in _inputjson.keys() and _inputjson['quarter-rack-servers']:
                _quarter_rack_dom0s = list(filter(lambda x: x['hw_type'] == 'COMPUTE', _inputjson['quarter-rack-servers']))
                _quarter_rack_cells = list(filter(lambda x: x['hw_type'] == 'CELL', _inputjson['quarter-rack-servers']))
                _quarter_rack_switches = list(filter(lambda x: x['hw_type'] == 'IBSWITCH', _inputjson['quarter-rack-servers']))
            if 'elastic-servers' in _inputjson.keys() and _inputjson['elastic-servers']:
                _elastic_dom0s = list(filter(lambda x: x['hw_type'] == 'COMPUTE', _inputjson['elastic-servers']))
                _elastic_cells = list(filter(lambda x: x['hw_type'] == 'CELL', _inputjson['elastic-servers']))
                _elastic_switches = list(filter(lambda x: x['hw_type'] == 'IBSWITCH', _inputjson['elastic-servers']))

            if self.__cluctrl.mIsXS():
                ebLogWarn('Skipping Hardware prechecks for cells')
                _elastic_cells = []
                _quarter_rack_cells = []

            _nodeInfo["ostype"] = _osType
            _nodeInfo["model_subtype"] = _model_subType
            _nodeInfo["shared_env"] = _multivm
            _nodeInfo["operationtype"] = _operationType
            _nodeInfo["quarter_rack_dom0s"] = _quarter_rack_dom0s
            _nodeInfo["quarter_rack_cells"] = _quarter_rack_cells
            _nodeInfo["quarter_rack_switches"] = _quarter_rack_switches
            _nodeInfo["elastic_dom0s"] = _elastic_dom0s
            _nodeInfo["elastic_cells"] = _elastic_cells
            _nodeInfo["elastic_switches"] = _elastic_switches

        return _nodeInfo

    def mStoreResultsJson(self, aStep, aOutput):
        _step = aStep
        _hw_health_table = aOutput

        _cmd = self.__cluctrl.mGetCmd()
        _uuid = self.__cluctrl.mGetUUID()
        _cluster_name = self.__cluctrl.mGetClusterName()

        _path = 'log/hardware_alerts/'
        _log_dir = _path + '{}'.format(_cluster_name)
        self.__cluctrl.mExecuteLocal("/bin/mkdir -p {0}".format(_path), aCurrDir=self.__cluctrl.mGetBasePath())
        self.__cluctrl.mExecuteLocal("/bin/mkdir -p {0}".format(_log_dir), aCurrDir=self.__cluctrl.mGetBasePath())

        _output = self.validate_hw_results(_step, _hw_health_table)
        _time = time.strftime("%Y%m%d%H%M%S")
        _logfilename = _log_dir + '/{}_cluctrl.{}.{}.json'.format(_uuid, _cmd, _time)
        
        _err_dict = {}
        if _step == "ELASTIC_SHAPES_VALIDATION":
            for key,value in _hw_health_table.items():
                if isinstance(value, dict):
                    errors = {}
                    for _key, _val in value.items():
                        if _val in ["abnormal","stopped"]:
                            errors[_key] = _val
                    if "node_info" in value:
                        if isinstance(value["node_info"],list):
                            for _node in value["node_info"]:
                                if "error_list" in _node:
                                    if _node["error_list"]:
                                        errors["error_list"] = _node["error_list"]
                    if errors:
                        _err_dict[key] = errors
            
        elif _step == "ESTP_PREVM_CHECKS":
            for node in _hw_health_table.get("nodes", []):
                hostname = node.get("hostname")
                errors = {}
                for key, value in node.items():
                    if value in ["abnormal","stopped"]:
                        errors[key] = value
                    
                if errors:
                    _err_dict[hostname] = errors
        
        if _err_dict:      
            _error_msg = f"Errors identified from hardware health check: {_err_dict}"
            if _step == "ESTP_PREVM_CHECKS":
                self.__cluctrl.mSetProvErr(_error_msg)
            ebLogError(f"{_error_msg}")
        else:
            ebLogInfo(f"No Errors found from hardware health check")

        with open(_logfilename, 'w') as json_file:
            json.dump(_hw_health_table, json_file)
            
        ebLogInfo('Detailed status is available at <exacloud>/%s' % (_logfilename))
        return _output

    def mExecuteHWAlertChecks(self, aOptions, aStep, aConfig):
        _options = aOptions
        _step = aStep
        _precheck_config = aConfig
        _rc = 0

        _hw_health_table = {}
        _output, _err = {}, ""
        _nodeInfo = {}

        # Parse the json and read the attributes
        _inputjson = _options.jsonconf
        if _inputjson:
            _step = "ELASTIC_SHAPES_VALIDATION"
            _nodeInfo = self.mParseHWAlertPayload(_options)
        else:
            _step = "ESTP_PREVM_CHECKS"
            _dpairs = self.__cluctrl.mReturnDom0DomUPair()
            _dom0_list = [ _dom0 for _dom0 , _ in _dpairs ]

            if self.__cluctrl.mIsXS():
                ebLogWarn('Skipping Hardware prechecks for cells')
                _cell_list = []
            else:
                _cell_list = self.__cluctrl.mReturnCellNodes().keys()

            _nodeInfo["dom0s"] = _dom0_list
            _nodeInfo["cells"] = _cell_list

            if not self.__cluctrl.mIsKVM():
                _switch_list = self.__cluctrl.mReturnSwitches(True)
                _nodeInfo["switches"] = _switch_list

        _hw_health_table = self.mRunHWSanityTest(_step, _nodeInfo, _precheck_config)
        _output = self.mStoreResultsJson(_step, _hw_health_table)

        self.mUpdateRequestData(_options, 0, _output, _err)

        return _rc

    def mValidateElasticShapes(self, aOptions, aStep, aConfig):
        _options = aOptions
        _step = aStep
        _precheck_config = aConfig
        _rc = 0

        _output, _err = {}, ""
        _nodeInfo = {}

        _nodeInfo = self.mParseHWAlertPayload(_options)
        _hw_health_table = self.mRunHWSanityTest(_step, _nodeInfo, _precheck_config)
        _output = self.validate_hw_results(_step, _hw_health_table)

        self.mUpdateRequestData(_options, _rc, _output, _err)

        return _rc

    def mPreVMHardwareChecks(self, aOptions, aStep, aConfig):
        _options = aOptions
        _step = aStep
        _precheck_config = aConfig
        _rc = True

        _hw_health_table = {}
        _output, _err = {}, ""
        _nodeInfo = {}

        _dpairs = self.__cluctrl.mReturnDom0DomUPair()
        _dom0_list = [ _dom0 for _dom0 , _ in _dpairs ]

        if self.__cluctrl.mIsXS():
            ebLogWarn('Skipping Hardware prechecks for cells')
            _cell_list = []
        else:
            _cell_list = self.__cluctrl.mReturnCellNodes().keys()

        _nodeInfo["dom0s"] = _dom0_list
        _nodeInfo["cells"] = _cell_list

        if not self.__cluctrl.mIsKVM():
            _switch_list = self.__cluctrl.mReturnSwitches(True)
            _nodeInfo["switches"] = _switch_list

        _hw_health_table = self.mRunHWSanityTest(_step, _nodeInfo, _precheck_config)
        _output = self.mStoreResultsJson(_step, _hw_health_table)

        if _output['unhealthy_nodes']:
            _rc = False

        self.mUpdateRequestData(_options, 0 if _rc else 1 , _output, _err)

        return _rc

    def mFetchHardwareAlerts(self, aOptions, aStep=''):

        _rc = 0
        _options = aOptions
        _step = aStep

        _cmd = self.__cluctrl.mGetCmd()

        _configpath = self.__cluctrl.mGetBasePath()+ "/config/hardware_prechecks.conf"

        if not os.path.exists(_configpath):
            ebLogWarn('Hardware prechecks Config file not found: ' + _configpath)
            return _rc

        with open(_configpath) as fd:
            _precheck_config = json.load(fd)

        try:
            if _cmd == "hardware_alerts":
                _rc = self.mExecuteHWAlertChecks(_options, _step, _precheck_config)
            elif _cmd == "validate_elastic_shapes":
                _rc = self.mValidateElasticShapes(_options, _step, _precheck_config)
            elif _cmd in ["createservice", "vmgi_install", "vmgi_preprov"] and _step == "ESTP_PREVM_CHECKS":
                _rc = self.mPreVMHardwareChecks(_options, _step, _precheck_config)
            else:
                ebLogWarn("Invalid cmd '{0}' in mFetchHardwareAlerts".format(_cmd))

            ebLogInfo('*** Exadata Hardware Alert activity is completed ...')
        except Exception as e:
            ebLogWarn('Exception in handling request[%s]' % (e,))
            ebLogError(traceback.format_exc())

        return _rc

    def mCheckVmNamePrefix(self):
        """
        Check if the vm name has "vm" prefix and atleast one dom0 version is < 23.1.13, if so fail provisioning
        """
        _rc = False
        _vm_prefix_dom0_version_cutoff = self.__cluctrl.mCheckConfigOption('vm_prefix_dom0_version_cutoff')

        for _dom0, _domU in self.__cluctrl.mReturnDom0DomUPair():
            _dom0_version = self.__cluctrl.mGetExadataImageFromMap(_dom0)
            if _domU.startswith("vm") and (version_compare(_dom0_version, _vm_prefix_dom0_version_cutoff) < 0):
                ebLogError(f"Precheck Failed. The vm name {_domU} has prefix vm and and since Dom0 = {_dom0} has Exadata Image {_dom0_version} which is older than {_vm_prefix_dom0_version_cutoff}. "
                f"Kindly either upgrade the dom0s to an Exadata image newer than {_vm_prefix_dom0_version_cutoff} or else recreate this cluster with a different name that does not start with 'vm'")
                _rc = True
                break

        return _rc

    def mSetDiskScrubbingWindow(self, aOptions):
        """
        Set Disk Scrubbing window on cells
        """
        _user = ''
        _passwd = ''
        _role = ''

        _out, _err = {}, ""
        _options = aOptions
        # Parse the json and read the attributes
        _inputjson = _options.jsonconf
        if _inputjson:

            if 'user' in _inputjson.keys() and _inputjson['user'].strip():
                _user = _inputjson['user'].strip()

            if 'passwd' in _inputjson.keys() and _inputjson['passwd'].strip():
                _passwd = b64decode(_inputjson['passwd']).decode('utf8')

            if 'role' in _inputjson.keys() and _inputjson['role'].strip():
                _role = _inputjson['role'].strip()

        _cell_list = sorted(self.__cluctrl.mReturnCellNodes().keys())

        for _cell_name in _cell_list:
            with connect_to_host(_cell_name, get_gcontext()) as _node:
                _cmd = f"cellcli -e create user {_user} password={_passwd}"
                _ret = node_exec_cmd(_node, _cmd)
                if _ret.exit_code:
                    _err_msg = ("An error occured while attempting to run cmd: {0}, stdout: {1.stdout}, stderr: {1.stderr}, exit-code: {1.exit_code}")
                    ebLogError(_err_msg.format(_cmd, _ret))
                    raise ExacloudRuntimeError(0x802, 0xA,_err_msg.format(_cmd, _ret))

                _cmd = f"cellcli -e create role {_role}"
                _ret = node_exec_cmd(_node, _cmd)
                if _ret.exit_code:
                    _err_msg = ("An error occured while attempting to run cmd: {0}, stdout: {1.stdout}, stderr: {1.stderr}, exit-code: {1.exit_code}")
                    ebLogError(_err_msg.format(_cmd, _ret))
                    raise ExacloudRuntimeError(0x802, 0xA,_err_msg.format(_cmd, _ret))

                _cmd = f"cellcli -e grant privilege list on cell attributes hardDiskScrubStartTime,hardDiskScrubInterval with all options to role {_role}"
                _ret = node_exec_cmd(_node, _cmd)
                if _ret.exit_code:
                    _err_msg = ("An error occured while attempting to run cmd: {0}, stdout: {1.stdout}, stderr: {1.stderr}, exit-code: {1.exit_code}")
                    ebLogError(_err_msg.format(_cmd, _ret))
                    raise ExacloudRuntimeError(0x802, 0xA,_err_msg.format(_cmd, _ret))

                _cmd = f"cellcli -e grant privilege alter on cell attributes hardDiskScrubStartTime,hardDiskScrubInterval with all options to role {_role}"
                _ret = node_exec_cmd(_node, _cmd)
                if _ret.exit_code:
                    _err_msg = ("An error occured while attempting to run cmd: {0}, stdout: {1.stdout}, stderr: {1.stderr}, exit-code: {1.exit_code}")
                    ebLogError(_err_msg.format(_cmd, _ret))
                    raise ExacloudRuntimeError(0x802, 0xA,_err_msg.format(_cmd, _ret))

                _cmd = f"cellcli -e grant role {_role} to user {_user}"
                _ret = node_exec_cmd(_node, _cmd)
                if _ret.exit_code:
                    _err_msg = ("An error occured while attempting to run cmd: {0}, stdout: {1.stdout}, stderr: {1.stderr}, exit-code: {1.exit_code}")
                    ebLogError(_err_msg.format(_cmd, _ret))
                    raise ExacloudRuntimeError(0x802, 0xA,_err_msg.format(_cmd, _ret))

        self.mUpdateRequestData(_options, _ret, _ret.stdout, _ret.stderr)
        return 0

    def cleanup_old_system_boot_files(self, aDom0:str, aImgVers:Set):
        """
        This helper function will read all the first.boot images
        from aDom0 and will delete the ones that do NOT match
        aImgVers and only if the file is older than 1 week
        """

        _dom0 = aDom0
        _imgvers = aImgVers
        _customImgVer = self.__cluctrl.mCheckConfigOption('exadata_custom_domu_version')

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost = _dom0)
        _bin_find = node_cmd_abs_path_check(_node, "find", sbin=True)
        _, _o, _e = _node.mExecuteCmd(f'{_bin_find} /EXAVMIMAGES/ -maxdepth 1 -iname "System.first.boot.*.img" -mtime +7')
        _output = _o.readlines()
        if _output and len(_output):

            _imgver_list = set(map(lambda x: re.search("boot\.([0-9\.]{1,})", x).group(1), _output))
            _imgver_list = set(map(lambda x: x.strip("."), _imgver_list))
            _imgver_list = _imgver_list - _imgvers
            if _customImgVer:
                ebLogTrace("The flag exadata_custom_domu_version is set, skipping cleanup of image {}".format(_imgver_list))
                _imgver_list = set(filter(_customImgVer.__ne__, _imgver_list))

            for _version in _imgver_list:
                ebLogInfo(f"Removing System.first.boot.{_version} from {_dom0}")
                _node.mExecuteCmdLog('/bin/rm -rf /EXAVMIMAGES/System.first.boot.{0}*.img'.format(_version))
                _node.mExecuteCmdLog('/bin/rm -rf /EXAVMIMAGES/System.first.boot.{0}*.bz2'.format(_version))
        _node.mDisconnect()

    def mValidateVersionForMVM(self, aOptions):
        # relax OEDA image version validation for create service
        _skip_sysimage_version_check = False
        if aOptions and aOptions.jsonconf and \
           "skip_sysimage_version_check" in aOptions.jsonconf and \
           str(aOptions.jsonconf['skip_sysimage_version_check']).lower() == "true":
            _skip_sysimage_version_check = True

        _cutOffVersionMig = "21.2.16"        
        if _skip_sysimage_version_check and ebCluCmdCheckOptions(
            self.__cluctrl.mGetCmd(), ['relax_oeda_image_version_check']):
            # min exacloud version for mvm migration is 21.2.17
            _minVersion = mGetDom0sImagesListSorted(self.__cluctrl)[0]
            if version_compare(_cutOffVersionMig,_minVersion) > 0 and ebCluCmdCheckOptions(self.__cluctrl.mGetCmd(), ['mvm_migrate_check']):
                ebLogError(f"System Image version({_minVersion}) is be same or older than minimum cut off version({_cutOffVersionMig}) required for migration")
                raise ExacloudRuntimeError(0x0812, 0xA, "System version invalid for migration", aStackTrace=False)
            self.__cluctrl.mSetDomUImageVer(_minVersion)

        _cutOffVersionMVM = "21.2.14"
        if self.__cluctrl.mGetSharedEnv() and self.__cluctrl.mIsKVM() and \
            ebCluCmdCheckOptions(self.__cluctrl.mGetCmd(), ['validate_mvm_version']):      
            # min exacloud version for mvm is 21.2.14
            _minVersion = mGetDom0sImagesListSorted(self.__cluctrl)[0]
            if version_compare(_cutOffVersionMVM,_minVersion) > 0:
                ebLogError(f"System Image version({_minVersion}) is be same or older than minimum cut off version({_cutOffVersionMVM}) required for MVM")
                raise ExacloudRuntimeError(0x0812, 0xA, f"System Image version({_minVersion}) must be same or older than minimum cut off version({_cutOffVersionMVM}) required for MVM", aStackTrace=False)


    def mAddMissingNtpDnsIps(self, aHostList=[], aChronyRestart=True):
        """
        Check if ntp/dns value and chrony sources are configured if not,
        it will update it using ipconf command.

        :params:
                aHostList -> a list of nodes for which ntp/dns need to checked and updated
                aChronyRestart -> Default -> True -> chronyd service will be restarted

        :returns: 
                0  -> if the ntp/dns is already updated or its update was successful for all the nodes
                -1 -> if the ntp/dns update was not successful (for any of the nodes)
        """

        def mServerPrecheck(aNode, _default_server_ip):

            _node = aNode
            _update_required = False
            _grep_cmd = node_cmd_abs_path_check(_node, "grep")

            if _node.mFileExists("/etc/chrony.conf"):
                _cmd = f"{_grep_cmd} 'server {_default_server_ip}' /etc/chrony.conf"
                _ret, _out, _err = node_exec_cmd(_node, _cmd)
                if _ret != 0:
                    _update_required = True

            if _node.mFileExists("/opt/oracle.cellos/cell.conf"):
                _cmd = f"{_grep_cmd} 'Ntp_servers' /opt/oracle.cellos/cell.conf"
                _ret, _out, _err = node_exec_cmd(_node, _cmd)
                if _ret != 0:
                    _update_required = True

                _cmd = f"{_grep_cmd} 'Nameservers' /opt/oracle.cellos/cell.conf"
                _ret, _out, _err = node_exec_cmd(_node, _cmd)
                if _ret != 0:
                    _update_required = True

            if _node.mFileExists("/etc/resolv.conf"):
                _cmd = f"{_grep_cmd} 'nameserver {_default_server_ip}' /etc/resolv.conf"
                _ret, _out, _err = node_exec_cmd(_node, _cmd)
                if _ret != 0:
                    _update_required = True

            return _update_required

        def mUpdateNtpIp(aNode, _default_server_ip):
            _node = aNode
            _cmd = f"/usr/local/bin/ipconf -update -ntp {_default_server_ip} -ilom-ntp {_default_server_ip} -force"
            _i,_o,_e = _node.mExecuteCmd(_cmd)
            _output = _o.readlines()
            if _output:
                for _line in _output:
                    if (_line.find('Update cell configuration file /opt/oracle.cellos/cell.conf OK') != -1):
                        ebLogInfo(f"ntp and ntp ilom server {_default_server_ip} updated in /opt/oracle.cellos/cell.conf")
                        return 0
                        
            ebLogWarn(f"Failure in updating ntp server on {_node}")
            return -1

        def mUpdateDnsIp(aNode, _default_server_ip):
            _node = aNode
            _cmd = f"/usr/local/bin/ipconf -update -dns {_default_server_ip} -ilom-dns {_default_server_ip} -force"
            _i,_o,_e = _node.mExecuteCmd(_cmd)
            _output = _o.readlines()
            if _output:
                for _line in _output:
                    if (_line.find('Update cell configuration file /opt/oracle.cellos/cell.conf OK') != -1):
                        ebLogInfo(f"dns and dns ilom nameserver server {_default_server_ip} updated in /opt/oracle.cellos/cell.conf")
                        return 0

            ebLogWarn(f"Failure in updating dns nameserver on {_node}")
            return -1
        
        def mUpdateNtpDnsIp(_host, _chrony_restart, _rc_status):
            _rc_status[_host] = 0
            _default_server_ip = self.__cluctrl.mCheckConfigOption('ntp_dns_ilom_ip')
            _succ = True
            with connect_to_host(_host, get_gcontext()) as _node:
                try:
                    _update_req = mServerPrecheck(_node, _default_server_ip)
                    if _update_req:
                        #update ntp
                        ebLogInfo(f"Updating the ntp server ip in cell.conf and chrony.conf on node: {_host}")
                        _return_code = mUpdateNtpIp(_node, _default_server_ip)
                        if _return_code == -1:
                            _succ = False
                        #update dns
                        ebLogInfo(f"Updating the dns server ip in cell.conf and resolv.conf on node: {_host}")
                        _return_code = mUpdateDnsIp(_node, _default_server_ip)
                        if _return_code == -1:
                            _succ = False
                        #restart chronyd service
                        if _chrony_restart:
                            _systemctl_cmd = node_cmd_abs_path_check(_node, "systemctl")                        
                            _cmd = f"{_systemctl_cmd} restart chronyd"
                            _node.mExecuteCmdLog(_cmd)
                            if _node.mGetCmdExitStatus() != 0:
                                _msg = f"Could not succesfully run the command {_cmd} on node: {_host}"
                                ebLogWarn(f"*** {_msg} ***")
                                _succ = False
                    else:
                        ebLogInfo(f"ntp and dns servers are already set on the node: {_host}")
                        _succ = True

                except Exception as e:
                    ebLogWarn(f"**** Unable to update ntp and dns server value on:{_host} Exception: {str(e)}")
                    _succ = False

                finally:
                    if _succ is False:
                        _rc_status[_host] = -1

        def mGetGriddisksCell(_cell, _dict_grid_disks, _storage_obj):
            ebLogInfo(f"Fetching GridDisks info from: {_cell}")
            with connect_to_host(_cell, get_gcontext()) as _node:
                _dict_grid_disks[_cell] = _storage_obj.mListCellDG(_node)

        if self.__cluctrl.mIsOciEXACC():
            ebLogInfo(f"Ntp and Dns server IPs are expected to be already set for exacc envs. Skipping update.")
            return 0

        _enable_ntp_dns_update = self.__cluctrl.mCheckConfigOption('enable_ntp_dns_update', 'True')
        _rc_status = {}
        if _enable_ntp_dns_update:
            try:
                if self.__cluctrl.mGetCmd() in ['createservice', 'elastic_cell_info', 'elastic_cell_update']:

                    _cell_list = self.__cluctrl.mReturnCellNodes()
                    if self.__cluctrl.mGetCmd() in ['elastic_cell_info', 'elastic_cell_update'] and aHostList:
                        _cell_list = aHostList
                    #Create the multiprocess structure
                    _plist = ProcessManager()
                    _dict_grid_disks = _plist.mGetManager().dict()
                    _storage_obj = self.__cluctrl.mGetStorage()
                    for _cell in _cell_list:
                        _p = ProcessStructure(mGetGriddisksCell, (_cell, _dict_grid_disks, _storage_obj))
                        _p.mSetMaxExecutionTime(15*60) # 15 minutes
                        _p.mSetJoinTimeout(5)
                        _p.mSetLogTimeoutFx(ebLogWarn)
                        _plist.mStartAppend(_p)
                    _plist.mJoinProcess()

                    for _cell in _cell_list:
                        if len(_dict_grid_disks[_cell]) > 0:
                            ebLogInfo(f"Grid disks found on cell - {_cell} : {_dict_grid_disks[_cell]}. Skipping update of ntp/dns values.")
                            return 0
                with self.__cluctrl.remote_lock():
                    _plist = ProcessManager()
                    _rc_status = _plist.mGetManager().dict()

                    for aHost in aHostList:
                        _p = ProcessStructure(mUpdateNtpDnsIp, [aHost, aChronyRestart, _rc_status])
                        _p.mSetMaxExecutionTime(30 * 60)  # 30 minutes timeout
                        _p.mSetJoinTimeout(10)  #10 seconds
                        _p.mSetLogTimeoutFx(ebLogInfo)
                        _plist.mStartAppend(_p)

                    _plist.mJoinProcess()
            except Exception as e:
                ebLogWarn(f"**** Unable to update ntp and dns server value {str(e)}. Moving Ahead")

            finally:
                #validate the return code from the hostlist
                _rc_all = 0

                for aHost in aHostList:
                    if _rc_status.get(aHost) == -1:
                        _rc_all = -1
                return _rc_all
        else:
            return 0


#class added for listing the PIDs of agent/worker processes.
class AgentWorkerPIDListing(object):

    @staticmethod
    def getWorkerPIDs(wlist_str): #get PIDs of '-w and --supervisor' processes in this instance of EC

        #wlist_str is return value of exabox.core.DBStore.ebGetDefaultDB.mDumpWorkers()

        pidlist = [] #declare empty list to store the PID's

        if wlist_str == "()": #check if worker list is empty
            return pidlist

        wlist = ast.literal_eval(wlist_str) #convert wlist_str to matrix
        for w in wlist: #iterate through rows (workers)
            if w[1]!='Exited': #check if active worker
                pidlist.append(int(w[8])) #insert PID of every row into list
        
        worker_types = ['-w', '--supervisor']
        for pid in pidlist:
            if pid and psutil.pid_exists(pid):
                _process = psutil.Process(pid).cmdline()
                if not any(worker in _process for worker in worker_types): #check if PID is NOT an open worker
                    pidlist.remove(pid)
            else:
                pidlist.remove(pid)

        return pidlist
   
#class added for ssh setup
class ebCluSshSetup(object):

    def __init__(self, aCluCtrlObj):

        self.__cluctrl = aCluCtrlObj
        self.__verbose = False
        # Hold the ssh key comment
        self.__hostkey = None

        self.__priv_hostkey_files = []
        self.__pub_hostkey_files = []


    def get_priv_hostkey_files(self):
        return self.__priv_hostkey_files


    def get_pub_hostkey_files(self):
        return self.__pub_hostkey_files

    # Functions that handle ssh passwordless connetion between hosts.

    def mGetSSHPublicKeyFromHost(self, aHost, aKeyComment = "EXACMISC KEY"):
        """
        Returns aHost's public ssh key value. If the key doesn't exist, then it is created with ssh-keygen command.
        """

        _exakms = get_gcontext().mGetExaKms()

        _is_rsa = True
        if _exakms.mGetDefaultKeyAlgorithm() == "ECDSA":
            _is_rsa = False


        _ssh_key = ''
        _cmd = ""

        if _is_rsa:

            _cmd = "if [[ ! `find /root/.ssh -maxdepth 1 -name 'id_rsa'` || ! `find /root/.ssh -maxdepth 1" \
                   f" -name 'id_rsa.pub'` ]]; then ssh-keygen -C '{aKeyComment}' -q -t rsa -N \"\" -f "\
                   '/root/.ssh/id_rsa <<<y > /dev/null 2>&1; fi; '\
                   'cat /root/.ssh/id_rsa.pub'

        else:

            _cmd = "if [[ ! `find /root/.ssh -maxdepth 1 -name 'id_ecdsa'` || ! `find /root/.ssh -maxdepth 1" \
                   f" -name 'id_ecdsa.pub'` ]]; then ssh-keygen -C '{aKeyComment}' -q -t ecdsa -b 384 -m PEM -N \"\" -f "\
                   '/root/.ssh/id_ecdsa <<<y > /dev/null 2>&1; fi; '\
                   'cat /root/.ssh/id_ecdsa.pub'

        with connect_to_host(aHost, get_gcontext()) as _node:

            # Backup key
            _keypair_files = ['/root/.ssh/id_ecdsa','/root/.ssh/id_ecdsa.pub']
            if _is_rsa:
                _keypair_files = ['/root/.ssh/id_rsa','/root/.ssh/id_rsa.pub']

            for _filename in _keypair_files:
                if _node.mFileExists(_filename):
                    _, _o, _e = _node.mExecuteCmd(f"/bin/mv -f {_filename} {_filename}_keybackup")

                    if _node.mGetCmdExitStatus() != 0:
                        ebLogWarn(f"Backup not created: {_o.read()}, {_e.read()}")
           
           
            # Create new SSH Key
            _in, _out, _err = _node.mExecuteCmd(_cmd)
            if _node.mGetCmdExitStatus():
                ebLogError(f'Failed to get public key for host {aHost}: mExecuteCmd Failed: with error: {_err.readlines()}')
            else:
                _output = _out.readlines()
                if _output:
                    _ssh_key  = _output[0].strip()
                    ebLogInfo(f'Obtained SSH public key for host {aHost}')
                    # Retain the key comment which can be used when cleanup
                    self.__hostkey = aKeyComment

        return _ssh_key
    
    def mRemoveSSHPublicKeyFromVM(self, aSrcDomU, aDeletedDomU, aUser, aUseInputUserForSSH=False):
        """  
        Removes references of a deleted node from a target node.
        aSrcDomU : Existing node from which keys to be removed
        aDeletedDomU : node which has been removed 
        aUser : user for which keys have to be removed
        aUseInputUserForSSH : decide if root user or custom user 
        to be used to login to the aSrcDomU
        """
        # Validate inputs
        if not ebCluCmdCheckOptions(self.__cluctrl.mGetCmd(), ['remove_ssh_publickey']):
            ebLogTrace(f'CMD: {self.__cluctrl.mGetCmd()} not allowed for removing ssh keys.')
            return
        
        if not isinstance(aSrcDomU, str) or not aSrcDomU.strip():
            ebLogError("Invalid input: DomU must be a non-empty string.")
            return
        
        if not isinstance(aDeletedDomU, str) or not aDeletedDomU.strip():
            ebLogError("Invalid input: deleted node must be a non-empty string.")
            return 
        
        if not isinstance(aUser, str) or not aUser.strip():
            ebLogError("Invalid input: user must be a non-empty string.")
            return 
        
        if not isinstance(aUseInputUserForSSH, bool):
            ebLogError("Invalid input: {aUseInputUserForSSH} must be a boolean value.")
            return
        
        if aUseInputUserForSSH:
            username = aUser
        else:
            username = 'root'
        try:
            with connect_to_host(aSrcDomU, get_gcontext(), username=username) as _node_conn:
                # Determine the path to the known_hosts file for the user
                if aUser == "root":  
                    known_hosts_path = "/root/.ssh/known_hosts"
                else:
                    known_hosts_path = f"/home/{aUser}/.ssh/known_hosts"
                command = f'/bin/su - {aUser} -c "/usr/bin/ssh-keygen -R {aDeletedDomU} -f {known_hosts_path}"'
                _node_conn.mExecuteCmdLog(command)
                ebLogTrace(f"Executed command to remove references of {aDeletedDomU} from {aSrcDomU} for {aUser}")
        except Exception as e:
            ebLogError(f"Error removing references from {aSrcDomU}: {e}")


    def mGetSSHPublicKeyFromHostForClusterless(self, aHost, aKeyComment = EXAPATCHING_KEY_TAG):
        """
        Returns aHost's public ssh key value. If the key doesn't exist, then it is created with ssh-keygen command.
        """

        _exakms = get_gcontext().mGetExaKms()

        _is_rsa = True
        if _exakms.mGetDefaultKeyAlgorithm() == "ECDSA":
            _is_rsa = False
        _ssh_key = ''
        _cmd = ""
        if _is_rsa:
            _cmd = "if [[ ! `find /root/.ssh -maxdepth 1 -name 'id_rsa'` || ! `find /root/.ssh -maxdepth 1" \
                   f" -name 'id_rsa.pub'` ]]; then ssh-keygen -C '{aKeyComment}' -q -t rsa -N \"\" -f "\
                   '/root/.ssh/id_rsa <<<y > /dev/null 2>&1; fi; '\
                   'cat /root/.ssh/id_rsa.pub'
        else:
            _cmd = "if [[ ! `find /root/.ssh -maxdepth 1 -name 'id_ecdsa'` || ! `find /root/.ssh -maxdepth 1" \
                   f" -name 'id_ecdsa.pub'` ]]; then ssh-keygen -C '{aKeyComment}' -q -t ecdsa -b 384 -m PEM -N \"\" -f "\
                   '/root/.ssh/id_ecdsa <<<y > /dev/null 2>&1; fi; '\
                   'cat /root/.ssh/id_ecdsa.pub'
        with connect_to_host(aHost, get_gcontext()) as _node:
            # diff -s <(ssh-keygen -y -f /root/.ssh/id_rsa | cut -d' ' -f2) <(cat /root/.ssh/id_rsa.pub | cut -d' ' -f2)
            # will return 1 if the private key doesnt match with public key, those keys will be deleted and fresh pair of 
            # keys will be generated
            if _is_rsa:
                if _node.mFileExists("/root/.ssh/id_rsa.pub") and  _node.mFileExists("/root/.ssh/id_rsa"):
                    _node.mExecuteCmd("diff -s <(ssh-keygen -y -f /root/.ssh/id_rsa | cut -d' ' -f2) <(cat /root/.ssh/id_rsa.pub | cut -d' ' -f2)")
                    if _node.mGetCmdExitStatus():
                        ebLogInfo(f'Cleaning up invalid keys on {aHost}')
                        _node.mExecuteCmd("/bin/rm -f /root/.ssh/id_rsa")
                        _node.mExecuteCmd("/bin/rm -f /root/.ssh/id_rsa.pub")
            else:
                if _node.mFileExists("/root/.ssh/id_ecdsa.pub") and _node.mFileExists("/root/.ssh/id_ecdsa"):
                    _node.mExecuteCmd("diff -s <(ssh-keygen -y -f /root/.ssh/id_ecdsa | cut -d' ' -f2) <(cat /root/.ssh/id_ecdsa.pub | cut -d' ' -f2)")
                    if _node.mGetCmdExitStatus():
                        ebLogInfo(f'Cleaning up invalid keys on {aHost}')
                        _node.mExecuteCmd("/bin/rm -f /root/.ssh/id_ecdsa")
                        _node.mExecuteCmd("/bin/rm -f /root/.ssh/id_ecdsa.pub")

            # Create new SSH Key
            _in, _out, _err = _node.mExecuteCmd(_cmd)
            if _node.mGetCmdExitStatus():
                ebLogError(f'Failed to get public key for host {aHost}: mExecuteCmd Failed: with error: {_err.readlines()}')
            else:
                _output = _out.readlines()
                if _output:
                    _ssh_key  = _output[0].strip()
                    ebLogInfo(f'Obtained SSH public key for host {aHost}')
                    # Retain the key comment which can be used when cleanup
                    self.__hostkey = aKeyComment
        return _ssh_key



    def mAddKeyToHosts(self, aHostKey, aRemoteHostList):
        """
        Adds the ssh public key (aHostKey) to the nodes listed in aRemoteHostList.
        """

        if not aHostKey:
            ebLogError("Host's SSH public key not found. Nothing to do.")
            return -1

        _cmd = f'echo {aHostKey} >> /root/.ssh/authorized_keys'
        for _h in aRemoteHostList:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_h)
            _node.mExecuteCmdLog(f"sh -c '{_cmd}'")
            _node.mDisconnect()

    def mAddKeyToHostsIfKeyDoesNotExist(self, aHost, aHostKey, aRemoteHostList):
        """
        Checks if the key already exists. If not , then add the ssh public key (aHostKey) to the nodes listed in aRemoteHostList.
        """

        def add_key_if_not_exists(_host, _remoteHost, _hostKey, aStatus):

            _check_key = f'/bin/grep -i "{_hostKey}" /root/.ssh/authorized_keys'
            _cmd_addkey = f'/bin/echo {_hostKey} >> /root/.ssh/authorized_keys'
            _node = exaBoxNode(get_gcontext())
            try:
                _node.mConnect(aHost=_remoteHost)
                _i, _o, _e = _node.mExecuteCmd(_check_key)
                _key_exists_output = _o.readlines()
                if _key_exists_output:
                    _status_msg = '*** SSH equivalence is already set up between  node %s and remote node %s ****  ' % (_host, _remoteHost)
                    aStatus.append({'message':_status_msg})
                else:
                    _status_msg = '*** Setting up SSH equivalence between  node %s and remote node %s ****  ' % (_host, _remoteHost)
                    _node.mExecuteCmdLog(f"sh -c '{_cmd_addkey}'")
                    aStatus.append({'message':_status_msg})
            except:
                _status_msg = '*** Exception in setting up SSH equivalence between node %s and remote node %s **** ' % (_host, _remoteHost)
                ebLogError(_status_msg)
                aStatus.append({'message':_status_msg})
            _node.mDisconnect()

        if not aHostKey:
            ebLogError("Host's SSH public key not found. Nothing to do.")
            return -1

        #
        # Parallel Execution of check and addition of keys
        #
        _plist = ProcessManager()
        _rc_status = _plist.mGetManager().list()

        for _h in aRemoteHostList:
            _p = ProcessStructure(add_key_if_not_exists, [aHost, _h, aHostKey, _rc_status])
            _p.mSetMaxExecutionTime(30 * 60)  # 30 minutes timeout
            _p.mSetJoinTimeout(30)  #30 seconds
            _p.mSetLogTimeoutFx(ebLogInfo)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()

        if _plist.mGetStatus() == "killed":
            ebLogError('Timeout while adding Host Key for SSH equivalence')
            return -1

        # Display the output
        _rcs = list([x for x in _rc_status])
        _ret = 0
        if _rcs == []:
            ebLogInfo('*** Empty status from SSH equivalence ***')
        else:
            for _rc in _rcs:
                if _rc and _rc['message']:
                    ebLogTrace( _rc['message'])

    def mRemoveKeyFromHosts(self, aHostKey, aRemoteHostList, aExcludePatternsRegEx=None):
        """
        Removes all aHost's ssh public keys found in the authorized_keys file on each node listed in aRemoteHostList.
        """
        ebLogInfo(f'mRemoveKeyFromHosts: Pattern to be matched for deletting line: {aHostKey}')
        if not str(aHostKey).strip():
          # If aHostKey is empty sed command could delete whole file
          raise Exception('mRemoveKeyFromHosts: called with Empty aHostKey')

        # remove entry using "aHostKey" - public key os driver node's short hostname
        # Using # as a sed separator in order for the code not to worry about existing slaesh in the key (if any)
        _msg_match_found = 'mRemoveKeyFromHosts: Lines to be removed from /root/.ssh/authorized_keys on host %s:\n%s'
        _msg_no_match = 'mRemoveKeyFromHosts: No matching lines to be removed from /root/.ssh/authorized_keys on host: %s'
        _cmd_match_lines = f'sed --follow-symlinks -n "\#\<{aHostKey}\>#p" /root/.ssh/authorized_keys'
        _cmd_delete_line = f'sed --follow-symlinks -i "\#\<{aHostKey}\>#d" /root/.ssh/authorized_keys'

        # This is to prevent other lines from deleting if any substring matches with pattern to be deleted.
        if aExcludePatternsRegEx:
            ebLogInfo( f'mRemoveKeyFromHosts: aExcludePatternsRegEx: {aExcludePatternsRegEx}' )
            _cmd_match_lines = "sed --follow-symlinks -n -r '/%s/!{\#\<%s\>#p}' /root/.ssh/authorized_keys" % (aExcludePatternsRegEx, aHostKey)
            _cmd_delete_line = "sed --follow-symlinks -i -r '/%s/!{\#\<%s\>#d}' /root/.ssh/authorized_keys" % (aExcludePatternsRegEx, aHostKey)
        
        _domu_list = [ _domu for _ , _domu in self.__cluctrl.mReturnDom0DomUPair()]
        _domu_shlist = [fqdn.split('.')[0] for fqdn in _domu_list]
        for _h in aRemoteHostList:
            #skipping delete of aHostKey in authorized_keys if aHost/aHostKey is Domu         
            if _h in _domu_list and aHostKey in _domu_shlist:                            
                ebLogInfo(f"Skipping aHostkey: {aHostKey} removal from Domu: {_h} authorized_keys")
                continue
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_h)
            _in, _out, _err = _node.mExecuteCmd(_cmd_match_lines)

            _output = []
            try:
                _lines = [ _line for _line in _out.readlines() if _line.strip() ]
                if _lines:
                   _output = _lines
            except:
                _output = []
            
            if _output:
                ebLogInfo(_msg_match_found % ( _h, '\n'.join(_output)))
            else:
                ebLogWarn(_msg_no_match % _h)
                _node.mDisconnect()
                continue
            
            _in, _out, _err = _node.mExecuteCmd(_cmd_delete_line)

            _rc = _node.mGetCmdExitStatus()

            if _rc != 0:
                _messages = '\n'.join(_out.readlines())+'\n'.join(_err.readlines())
                _node.mDisconnect()
                raise ExacloudRuntimeError(0x0114, 0xA, f'Error while removing ssh key from authorized_keys file in node:{_h}\n{_messages}')
            _node.mDisconnect()

    def mRemoveKeyFromHostsByComment(self, aHostKeyComment, aRemoteHostList):
        """
        Removes all aHost's ssh public keys found in the authorized_keys file on each node listed in aRemoteHostList.
        ssh public key removes based on key comment.
        """

        #remove entry using public key
        _cmd = f'sed --follow-symlinks -i "s#^.*{aHostKeyComment}.*\\$##g" /root/.ssh/authorized_keys'

        for _h in aRemoteHostList:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_h)
            _in, _out, _err = _node.mExecuteCmd(_cmd)

            _rc = _node.mGetCmdExitStatus()

            if _rc != 0:
                _messages = '\n'.join(_out.readlines())+'\n'.join(_err.readlines())
                _node.mDisconnect()
                raise ExacloudRuntimeError(0x0114, 0xA, f'Error while removing ssh key from authorized_keys based on comment file in node:{_h}\n{_messages}')

            _node.mDisconnect()


    def mRemoveSshKeysAndFilesFromHosts(self, 
                                        aHost,
                                        aRemoteHostList,
                                        aAuthKeyPatternsListToRemove=[],
                                        aSshUser='root',
                                        aAuthKeyFile='~/.ssh/authorized_keys'):
      
        # Do nothing if none of the required params given
        if not aAuthKeyPatternsListToRemove:
            return

        _auth_keys_patterns = '|'.join(aAuthKeyPatternsListToRemove)
        _obs_keys_found = False

        if _auth_keys_patterns:
            _cmd_grep_keys = f'/bin/grep -Pa "{_auth_keys_patterns}" {aAuthKeyFile}'

            for _aNode in aRemoteHostList:
                with connect_to_host(_aNode, get_gcontext(), username=aSshUser) as _node:

                    _in, _out, _err = _node.mExecuteCmd(_cmd_grep_keys)

                    if _node.mGetCmdExitStatus() == 0:
                        _obs_keys_found = True
                        ebLogInfo(f'Found obsolete SSH keys to be removed from {aAuthKeyFile} on host {_aNode}')
    
                        _cmd_sed = f"/bin/sed -i -r --follow-symlinks '/{_auth_keys_patterns}/d' {aAuthKeyFile}"
                        _in, _out, _err = _node.mExecuteCmd(_cmd_sed)

                        if _node.mGetCmdExitStatus() == 0:
                            ebLogInfo(f'Removed obsolete SSH keys from {aAuthKeyFile} on host {_aNode}')
                        else:
                            ebLogError(f'Obsolete keys {_auth_keys_patterns} should be removed from {aAuthKeyFile} on Host {_aNode}') 

        if not _obs_keys_found:
            ebLogInfo('SSH Obsolete keys not found on any Hosts')


    def mAddToKnownHosts(self, aHost, aRemoteHostList, aUser=None):
        """
        Adds all nodes listed in aRemoteHostList to the known_hosts file in aHost.
        """
        _cmd_scan_ssh_keys= "ssh-keyscan -T %s %s"
        _completed_nodes_list = []


        ebLogInfo(f'{aHost}: Start updating known_hosts file for target nodes: {aRemoteHostList}')

        _node = exaBoxNode(get_gcontext())

        if aUser:
            _node.mSetUser(aUser)
            _cmd_add_ecdsa_keys = 'ssh-keyscan -T %s -t ecdsa %s | sudo tee -a /root/.ssh/known_hosts;'
            _cmd_add_rsa_keys = 'ssh-keyscan -T %s -t rsa %s | sudo tee -a /root/.ssh/known_hosts;'
            _cmd_add_available_keys = 'ssh-keyscan -T %s %s | sudo tee -a /root/.ssh/known_hosts;'
        else:
            _cmd_add_ecdsa_keys = 'ssh-keyscan -T %s -t ecdsa %s >> /root/.ssh/known_hosts 2> /dev/null;'
            _cmd_add_rsa_keys = 'ssh-keyscan -T %s -t rsa %s >> /root/.ssh/known_hosts 2> /dev/null;'
            _cmd_add_available_keys = 'ssh-keyscan -T %s %s >> /root/.ssh/known_hosts 2> /dev/null;'
        _node.mConnect(aHost=aHost)

        for _h in aRemoteHostList:
            #Here _h is FQDN of host and _sh is shortname of host without domain name.
            _sh = _h.split(".")[0]
            _in, _out, _err = _node.mExecuteCmd(_cmd_scan_ssh_keys %(SSH_KEYSCAN_TIMEOUT, _h))
            '''_output is list of lines like below.
               [ 
                 'nodename ssh-rsa AAAAB3NzaC1yXXXXXXXXX',
                 'nodename ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYXXXXXX'
               ]
            '''
            _output = _out.readlines()
            try:
                # Sample _scanned_keys = ['ecdsa-sha2-nistp256', 'ssh-rsa']
                _scanned_keys = [ _line.split()[1] for _line in _output ]
                ebLogInfo(f"{aHost}: scanned keys from node {_h} : {_scanned_keys}")

                if 'ecdsa' in " ".join(_scanned_keys):
                    ebLogInfo(f'{aHost}: Adding ECDSA key for {_h}')
                    _, _, _ = _node.mExecuteCmd(_cmd_add_ecdsa_keys %(SSH_KEYSCAN_TIMEOUT, _h))
                    if _h != _sh:
                        _, _, _ = _node.mExecuteCmd(_cmd_add_ecdsa_keys %(SSH_KEYSCAN_TIMEOUT,_sh))
                if 'rsa' in " ".join(_scanned_keys):
                    ebLogInfo(f'{aHost}: Adding RSA key for {_h}')
                    _, _, _ = _node.mExecuteCmd(_cmd_add_rsa_keys %(SSH_KEYSCAN_TIMEOUT, _h))
                    if _h != _sh:
                        _, _, _ = _node.mExecuteCmd(_cmd_add_rsa_keys %(SSH_KEYSCAN_TIMEOUT, _sh))
                if not 'ecdsa' in " ".join(_scanned_keys) and not 'rsa' in " ".join(_scanned_keys):
                    ebLogWarn(f'{aHost}: Neither ECDSA nor RSA key found for {_h}')
                    ebLogWarn(f'{aHost}: Trying to add default available keys for {_h}')
                    _, _, _ = _node.mExecuteCmd(_cmd_add_available_keys %(SSH_KEYSCAN_TIMEOUT, _h))
                    if _h != _sh:
                        _, _, _ = _node.mExecuteCmd(_cmd_add_available_keys %(SSH_KEYSCAN_TIMEOUT, _sh))
                else:
                    _completed_nodes_list.append(_h)

            except:
                ebLogError(f"{aHost}: ssh-keyscan could not get list of keys scanned from node {_h}")

        if _node.mIsConnected():
            _node.mDisconnect()
        if len(aRemoteHostList) == len(_completed_nodes_list):
            ebLogInfo(f'{aHost}: Completed updating known_hosts file for target nodes: {aRemoteHostList}')
        else:
            _pending_nodes = [ _n for _n in aRemoteHostList if not _n in _completed_nodes_list ]
            ebLogError(f'{aHost}: known_hosts not updated for some nodes {_pending_nodes}')

    def mAddToKnownHostsForOlVersionMismatchConfigs(self, aHost, aRemoteHostList, aTargetType, aUser=None):
        """
         Adds all nodes listed in aRemoteHostList to the known_hosts file in aHost.
         This module is currently applicable in ibswitch and the target details can
         be updated in 'exec_keyscan_on_target_node' in infrapatching.conf

         This method is applicable in environments where different versions on ssh
         binaries are installed and ssh keyscan commands are not returning required
         output.
        """
        _cmd_scan_ssh_keys= "ssh-keyscan -T %s %s"
        _completed_nodes_list = []
        _consolidated_key_list_from_target_host = []
        _pending_nodes = []
        _output = []

        ebLogInfo(f'Start generating known_hosts entries on the target nodes : {aRemoteHostList} to be added to launch node {aHost} known hosts file')

        _node = exaBoxNode(get_gcontext())
        _user = 'root'
        if aTargetType.lower() == "domu" and aUser:
            _user = aUser

        '''
          Connect to the target node to get ssh-keyscan output and
          append to known hosts file of the launch node.
          In case of environments with different openssh versions on
          launch and target nodes, ssh-keyscan does not return the
          required results and scan need to run on the target node.
        '''
        for _remote_host in aRemoteHostList:
            with connect_to_host(_remote_host, get_gcontext(), username=_user) as _node:
                _in, _out, _err = _node.mExecuteCmd(_cmd_scan_ssh_keys % (SSH_KEYSCAN_TIMEOUT, _remote_host))
                '''_output is list of lines like below.
                   [
                     'nodename ssh-rsa AAAAB3NzaC1yXXXXXXXXX',
                     'nodename ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYXXXXXX'
                   ]
                '''
                if _out:
                    _output = _out.readlines()

                if len(_output) > 0:
                    _consolidated_key_list_from_target_host += _output

        with connect_to_host(aHost, get_gcontext(), username=_user) as _node:
            if len(_consolidated_key_list_from_target_host) > 0:
                for _entries in _consolidated_key_list_from_target_host:
                    _keys = _entries.strip()
                    try:
                        if aUser:
                            _cmd_add_consolidated_keys = f'echo {_keys} | sudo tee -a /root/.ssh/known_hosts;'
                        else:
                            _cmd_add_consolidated_keys = f'echo {_keys} >> /root/.ssh/known_hosts;'
                        _node.mExecuteCmdLog(_cmd_add_consolidated_keys)
                        ebLogInfo(f'Updation of known_hosts file entries on the launch node - {aHost} completed.')
                    except:
                        ebLogError(f"{aHost}: ssh-keyscan could not get list of keys scanned from the remote hosts")

    def mAddKeyToRoceSwitches(self, aHostKey, aRemoteHostList):
        """
          Adds the ssh public key (aHostKey) of Dom0 to the Roce switches listed in
          aRemoteHostList. In case of roce-switches keys will be injected through admin
          console.

          Return code : None
        """

        _user_roceswitch = 'admin'
        for _switch in aRemoteHostList:
            try:

                '''
                 In case of Roce or Admin Switches, passwdless ssh is
                 configured via Configure terminal and below steps are
                 performed.

                 -> Add the Dom0 user ciscokey key with root privileges onto Switches.
                 -> Add Relevant roles to the patch user ciscoexa.
                 -> Save the configuration for it to be persistent even after reboot.
                 -> Exit from configure terminal and switch.

                 Do not modify the passwdless command as per python 3 format. It was 
                 modified as below and passwdless ssh setup dint work as expected resulting 
                 in roceswitch patch failures.

                   _cmds.append(['#', f'username ciscoexa sshkey {aHostKey}'])

                 It has to be be in the below format for the passwdless ssh to work.

                   _cmds.append(['#', 'username ciscoexa sshkey {0}'.format(aHostKey)])

                  From Exadata 21.2.8, ciscoexa user will be replaced with switchexa user.
                  At this time, there is a possibility of using a version higher than
                  or lower than 21.2.8, hence setting up passwdless ssh will be performed with
                  both ciscoexa and switchexa user. Once all environments are moved to 21.2.8 
                  and above, ciscoexa details will be removed from here.
                '''

                _cmds = []
                _cmds.append(['#', 'configure terminal'])
                _cmds.append(['#', 'username ciscoexa role network-admin'])
                _cmds.append(['#', 'username ciscoexa sshkey {0}'.format(aHostKey)])
                _cmds.append(['#', 'username switchexa role network-admin'])
                _cmds.append(['#', 'username switchexa sshkey {0}'.format(aHostKey)])
                _cmds.append(['#', 'copy running-config startup-config'])
                _cmds.append(['#', 'exit']) # exit configure terminal
                _cmds.append(['#', 'exit']) # exit ssh connection

                _node = exaBoxNode(get_gcontext())
                _node.mSetUser(_user_roceswitch)
                _node.mConnect(aHost=_switch)

                ebLogInfo(f'Try authentication: {_switch}')
                _node.mConnectAuthInteractive(aHost=_switch)

                ebLogInfo(f'Execute command on switch: {_switch}')
                _node.mExecuteCmdsAuthInteractive(_cmds)

                if self.__cluctrl.mIsDebug():
                    ebLogDebug(f'Read from socket: [{_node.mGetConsoleRawOutput()}]')

                ebLogInfo(f'Successfully pushed the key to Roce Switch : {_switch}')
                _node.mDisconnect()

            except Exception as e:
                ebLogError(f'Could not inject keys in {_switch}: ')
                ebLogError(e)

    """
       This function is currently used only by infrapatching module to set up ssh equivalence 
       so that vm backup can also happen without any issues 
    """
    def mSetSSHPasswordlessForInfraPatching(self,
                                            aHost,
                                            aRemoteHostList,
                                            aRoceSwitch=False,
                                            aKeyComment=EXAPATCHING_KEY_TAG):
        """
        Set ssh passwordless between the host and a list of remote hosts.
        """

        #Fall back to our original method for setting up passwordless SSH for EXACS.
        #This is because vm backup happens in the same local node for EXACS. for EXACC , this is on remote node
        if not self.__cluctrl.mIsOciEXACC():
            return self.mSetSSHPasswordless(aHost, aRemoteHostList, aRoceSwitch, aKeyComment)

        #Get ssh public key from the host
        _key = self.mGetSSHPublicKeyFromHost(aHost, aKeyComment)

        self.mRemoveFromKnownHosts(aHost, aRemoteHostList, aRoceSwitch)
        self.mAddToKnownHosts(aHost, aRemoteHostList)

        #RoceSwitch equivalence set up is completely different business logic 
        #than other components, hence the if check
        if not aRoceSwitch:
            self.mAddKeyToHostsIfKeyDoesNotExist(aHost, _key, aRemoteHostList)
        else:
            self.mAddKeyToRoceSwitches(_key, aRemoteHostList)

        return _key

    def mValidateKnownHostsFile(self, aHost, aFixHostsFileIfInvalid=True, aUser=None):
        """ known_hosts file is expected to have 3 fileds in every line like,
           -> [hostname]  [ssh-algorithm]  [host hash key]
                             (or)
           -> [hostname,ip]  [ssh-algorithm]  [host hash key]

            If this file is corrupted for any reason and one or more filed missing,
            "ssh-keygen -R <hostname>" will fail on mRemoveFromKnownHosts()

            This method does follwing.
            1) Looks for inavlid lines (with less than 3 fiels, except Commented lines)
            2) If not found return success. else,
            3.1) if aFixHostsFileIfInvalid=False report error and fails. else,
            3.2) else run "mv -f /root/.ssh/known_hosts /root/.ssh/known_hosts_backup_by_Exacloud"
                 and makes new known_hosts files by filtering only valid lines of above file.
        """

        _ret = True
        _known_hosts = '/root/.ssh/known_hosts'
        _known_hosts_bkp = str(_known_hosts) + '_backup_by_Exacloud'

        _line_numbers = []
        _msg = ''

        ebLogInfo(f'mValidateKnownHostsFile: Starting known_hosts file validation on {aHost}')

        # awk command to get lines with less than 3 fields
        _cmd = "awk '$0 !~ /^[[:space:]]*#/ &&  NF < 3 {print NR, $0}' %s" % _known_hosts

        _node = exaBoxNode(get_gcontext())
        if aUser:
            _node.mSetUser(aUser)
        _node.mConnect(aHost=aHost)

        _in, _out, _err = _node.mExecuteCmd(_cmd)
        _output = _out.readlines()
        #_rc = _node.mGetCmdExitStatus()

        # Remove empty line if any
        _output = [ _i for _i in _output if _i.strip() ]

        if not _output:
            ebLogInfo(f'mValidateKnownHostsFile: known_hosts file validation success on {aHost}')
        else:
            _line_numbers = [ _i.split()[0] for _i in _output if _i ]
            _msg = 'Found invalid lines from file {} on host {}:\nLine number(s): {}'.format(_known_hosts, aHost, ', '.join(_line_numbers))
            if aFixHostsFileIfInvalid:
                ebLogWarn(_msg)
                ebLogInfo('Removing invalid line(s) from {} on host {}'.format(_known_hosts, aHost))
                ebLogInfo('Old {} file will be backed up to {}'.format(_known_hosts, _known_hosts_bkp))
                _mv_cmd = 'mv -f {} {}'.format(_known_hosts, _known_hosts_bkp)
                _node.mExecuteCmd(_mv_cmd)


                # Filter lines with only 3 or more fields
                _cmd_awk_filter = 'awk "NF && NF > 2" {} > {}'.format(_known_hosts_bkp, _known_hosts)
                _in, _out, _err = _node.mExecuteCmd(_cmd_awk_filter)
                _rc = _node.mGetCmdExitStatus()
                if _rc:
                    ebLogError('Command \"{}\" failed on host {}'.format(_cmd_awk_filter, aHost))
                    _ret = False
                else:
                    ebLogInfo(f'mValidateKnownHostsFile: known_hosts file validation success on {aHost}')
            else:
                ebLogError(_msg)
                _ret = False

        _node.mDisconnect()
        if not _ret:
            ebLogError(f'mValidateKnownHostsFile: known_hosts file validation failed on {aHost}')
        return _ret


    def mRemoveFromKnownHosts(self, aHost, aRemoteHostList, aRoceSwitch=False, aUser=None):
        """
        Removes all nodes listed in aRemoteHostList from the known_hosts file in aHost.
        """

        #fetch IPs  of all remote nodes
        _remoteHostIPList=[]
        if aUser:
            _username = aUser
        else:
            _username = 'root'

        if not aRoceSwitch:
            for _h in aRemoteHostList:
                try:
                    with connect_to_host(_h, get_gcontext()) as _remoteNode:
                        # Get ip of the node.
                        _i, _o, _e = _remoteNode.mExecuteCmd("/bin/hostname -i")
                        _ip = _o.readlines()[0].strip()
                        _remoteHostIPList.append(_ip)
                except Exception as e:
                    ebLogWarn("Exception caught while fetching IP of remote node %s for cleaning known_hosts file. %s" % (_h,str(e)) )
        if aRoceSwitch or _username == 'opc':
            '''
              The _username will be 'opc' when it is invoked for management host.  
              In case of RoceSwitches or management host entries are cleaned up
              based on the IP returned by nslookup
    
              
              Example of an nslookup output for Roceswitches.
              
              [root@scaqar05adm03 ~]# nslookup scaqar05sw-rocea0.us.oracle.com
              Server:         10.31.138.25
              Address:        10.31.138.25#53
              
              Name:   scaqar05sw-rocea0.us.oracle.com
              Address: 10.32.231.61
              
              [root@scaqar05adm03 ~]#
            
            '''
            with connect_to_host(aHost, get_gcontext(), username=_username) as _node:
                _cmd = "/usr/bin/nslookup %s | /usr/bin/grep Address | /usr/bin/grep -v '#' | /usr/bin/awk '{print $2}'"
                for _h in aRemoteHostList:
                    try:
                        # Get ip of Roce or admin switches.
                        _i, _o, _e = _node.mExecuteCmd(_cmd % _h)
                        _ip = _o.readlines()[0].strip()
                        _remoteHostIPList.append(_ip)
                    except Exception as e:
                        ebLogWarn("Exception caught while fetching IP of a remote Roceswitch : %s for cleaning known_hosts file. %s" % (_h,str(e)))

        #remove known_hosts file entries
        with connect_to_host(aHost, get_gcontext(), username=_username) as _node:  
            _cmd = 'ssh-keygen -R %s > /dev/null 2>&1'

            for _h in aRemoteHostList:
                _sh = _h.split(".")[0]
                ebLogTrace("Removing IP/Hostname : %s entries from known_hosts file." % _h)
                _node.mExecuteCmdLog(_cmd % _h)
                if _h != _sh:
                    _node.mExecuteCmdLog(_cmd % _sh)

            #remove ip based entries
            for _remoteIP in _remoteHostIPList:
                _node.mExecuteCmdLog(_cmd % _remoteIP)
    
    def mConnectandExecuteonCiscoSwitches(self, aNode, aUser, aSwitch, aCmds):
        _user = aUser
        _switch = aSwitch
        _cmds = aCmds
        _node = aNode
        _node.mSetUser(_user)
        _tries = 0
        _pwds = self.__cluctrl.mCheckConfigOption("admin_switchkeys")

        # We are trying to connect using the available
        # passwords in exabox.conf and will break from
        # loop as soon as the password works.
        for _pwd in _pwds:
            try:
                _pwd = base64.b64decode(_pwd).decode('utf8')
                if _pwd:
                    _node.mSetPassword(_pwd)
                    ebLogInfo(f'Try authentication: {_switch}')
                    _node.mConnectAuthInteractive(aHost=_switch)
                    ebLogInfo(f"mConnectandExecuteonCiscoSwitches: Execute commands {_cmds} on switch: {_switch}")
                    _node.mExecuteCmdsAuthInteractive(_cmds)
                    ebLogInfo(f"mConnectandExecuteonCiscoSwitches: Read from socket: [{_node.mGetConsoleRawOutput()}]")
            except Exception as e:
                ebLogInfo(f"Execution of cisco switch : {_switch} key setup command failed with exception: {str(e)} for the user {_user}")
                _tries += 1

            if _tries == len(_pwds):
                ebLogError(f"Unable to connect to {_switch} using any of the available passwords. Keys based access will not be setup.")
                break

            if _node.mIsConnectable(aHost=_switch, aTimeout=50, aKeyOnly=True):
                ebLogInfo(f"Key based ssh access between exacloud and {_switch} for {_user} user was setup successfully.")
                break
                
    def mSetCiscoSwitchSSHPasswordless(self, aGenerateSpineSwitchKeys=False, aGenerateAdminSwitchKeys=False):
        """
         Set SSH Passwordless from Exacloud to admin switch in EXACC
        """
        _exakms = get_gcontext().mGetExaKms()
        _adminswitches = []
        _spineswitches = []
        _adminandspineswitches = []
        _node = exaBoxNode(get_gcontext())

        # Create the keys for the switches
        _configured_admin_switches = set()
        _configured_spine_switches = set()

        _list = self.__cluctrl.mGetSwitches().mGetSwitchesDict()
        for _s in _list:
            if aGenerateAdminSwitchKeys:
                if 'Admin' in _s['swdesc']:  # 'swdesc': 'Exadata Admin Switch'
                    _neto = self.__cluctrl.mGetNetworks().mGetNetworkConfig(_s["swnetid"])
                    _adminswitches.append(_neto.mGetNetHostName()+'.'+_neto.mGetNetDomainName())
                    ebLogTrace(f"Admin Switch List: {_adminswitches}")

            # Get Spine switch details and setup passwdless
            # ssh between exacloud and Roce spine switch.
            # Collect Spine switch details and setup keys only
            # if aGenerateSpineSwitchKeys is set to True
            if aGenerateSpineSwitchKeys:
                if "spine" in _s["swdesc"].lower():
                    _neto = self.__cluctrl.mGetNetworks().mGetNetworkConfig(_s["swnetid"])
                    _spineswitches.append(_neto.mGetNetHostName()+'.'+_neto.mGetNetDomainName())

        _adminandspineswitches = _adminswitches[:]
        if len(_spineswitches) > 0:
            ebLogTrace(f"Spine Switch List required to patch: {_spineswitches}")
            _adminandspineswitches += _spineswitches

        ebLogInfo(f"Admin and Spine switches to be consumed for patching - {_adminandspineswitches}")

        # For admin switches, the requirement from ER 36969653 is to add admin and switchexa user keys to ExaKMS
        # and setup passwordless ssh from Exacloud for both the users.
        _user = "admin"
        for _switch in list(set(_adminandspineswitches)):
            try:
                # At times, keys could be rotated or new set of keys could
                # be generated and in such cases, ssh connectivity using
                # the existing keys must be deleted and new keys must
                # be added on KMS.
                _node.mSetUser(_user)
                if not _node.mIsConnectable(aHost=_switch, aTimeout=50, aKeyOnly=True):
                    ebLogInfo(f"Deleting the stale entries from KMS as the cisco switch - {_switch} is not accessible from exacloud host for user - {_user}")
                    _cparam = {"FQDN": _switch, "user": _user}
                    _entry = _exakms.mGetExaKmsEntry(_cparam)
                    if _entry:
                        _exakms.mDeleteExaKmsEntry(_entry)
                else:
                    if _switch in _adminswitches:
                        _configured_admin_switches.add(_switch)
                    if _switch in _spineswitches:
                        _configured_spine_switches.add(_switch)
                    ebLogInfo(f"Switch - {_switch} is accessible from exacloud host using {_user} user credentials.")
                    continue

                # Pregenerate kms entry
                _cparam = {"FQDN": _switch, "user": _user}
                _entry = _exakms.mGetExaKmsEntry(_cparam)
                if not _entry:
                    ebLogInfo(f"Kms entry not exists for: {_user}@{_switch}, Generating")

                    _entry = _exakms.mBuildExaKmsEntry(
                            _switch,
                            _user,
                            _exakms.mGetEntryClass().mGeneratePrivateKey(),
                            ExaKmsHostType.SWITCH
                    )
                    _exakms.mInsertExaKmsEntry(_entry)
                else:
                    ebLogInfo(f"Kms entry already exists for: {_user}@{_switch}")

                _pubKeyContent = _entry.mGetPublicKey("EXACLOUD KEY")

                _user_cmds = []
                _user_cmds.append(['#', 'configure terminal'])
                _user_cmds.append(['#', 'username admin sshkey {0}'.format(_pubKeyContent)])
                _user_cmds.append(['#', 'exit']) # exit configure terminal
                _user_cmds.append(['#', 'exit']) # exit ssh connection

                self.mConnectandExecuteonCiscoSwitches(_node, "admin", _switch, _user_cmds)
                if _node.mIsConnectable(aHost=_switch, aTimeout=50, aKeyOnly=True):
                    ebLogInfo(f"Key based ssh access between exacloud and {_switch} for {_user} user was setup successfully.")
                    # Add only the admin switch to the configured switch list
                    if _switch in _adminswitches and _switch not in _configured_admin_switches:
                        _configured_admin_switches.add(_switch)
                    if _switch in _spineswitches and _switch not in _configured_spine_switches:
                        _configured_spine_switches.add(_switch)

            except Exception as e:
                ebLogError(f"mHandlerAdminSwitchConnect: Could not inject {_user} user key in {_switch}: ")
                ebLogError(e)
            finally:
                if _node.mIsConnected():
                    _node.mDisconnect()
        return list(set(_configured_admin_switches)), list(set(_configured_spine_switches))

    def mSetSSHPasswordless(self, aHost, aRemoteHostList, 
                            aRoceSwitch=False, aKeyComment="EXACMISC KEY"):
        """
        Set ssh passwordless between the host and a list of remote hosts.
        """
        _key = self.mGetSSHPublicKeyFromHost(aHost, aKeyComment)

        # Integrity check of known_hosts file
        if not self.mValidateKnownHostsFile(aHost, True):
            raise Exception(f'known_hosts file error on host {aHost}')

        ##### TBD: check if all cells are healthy/pingable first
        # Add cells to known_hosts in host
        self.mRemoveFromKnownHosts(aHost, aRemoteHostList, aRoceSwitch)
        self.mAddToKnownHosts(aHost, aRemoteHostList)

        if not aRoceSwitch:
            # Add host's ssh public key to the cells
            self.mRemoveKeyFromHosts(aHost.split('.')[0], aRemoteHostList, aExcludePatternsRegEx="EXACLOUD KEY|ExaKms")
            # Removes the ssh key based on both host name and key comment if found
            # before adding new key.
            self.mRemoveKeyFromHostsByComment(self.__hostkey, aRemoteHostList)
            self.mAddKeyToHosts(_key, aRemoteHostList)
        else:
            self.mAddKeyToRoceSwitches(_key, aRemoteHostList)
        return _key

    def mSetSSHPasswordlessForClusterless(self, aHost, aRemoteHostList):
        """
        Set ssh passwordless between the host and a list of remote hosts.
        """
        _key = self.mGetSSHPublicKeyFromHostForClusterless(aHost)

        # Integrity check of known_hosts file
        if not self.mValidateKnownHostsFile(aHost, True):
            raise Exception(f'known_hosts file error on host {aHost}')

        ##### TBD: check if all cells are healthy/pingable first
        # Add cells to known_hosts in host
        self.mRemoveFromKnownHosts(aHost, aRemoteHostList)
        self.mAddToKnownHosts(aHost, aRemoteHostList)

        # Add host's ssh public key to the cells
        self.mRemoveKeyFromHosts(aHost.split('.')[0], aRemoteHostList, aExcludePatternsRegEx="EXACLOUD KEY|ExaKms")
        # Removes the ssh key based on both host name and key comment if found
        # before adding new key.
        self.mRemoveKeyFromHostsByComment(self.__hostkey, aRemoteHostList)
        self.mAddKeyToHosts(_key, aRemoteHostList)
        return _key


    def mSetSSHPasswordlessForOlVersionMismatch(self, aHost, aRemoteHostList, aTargetType, aRoceSwitch=False):
        """
        Set ssh passwordless between the host and a list of remote hosts.
        """
        _key = self.mGetSSHPublicKeyFromHost(aHost, EXAPATCHING_KEY_TAG)

        # Integrity check of known_hosts file
        if not self.mValidateKnownHostsFile(aHost, True):
            raise Exception(f'known_hosts file error on host {aHost}')

        ##### TBD: check if all cells are healthy/pingable first
        # Add cells to known_hosts in host
        self.mRemoveFromKnownHosts(aHost, aRemoteHostList, aRoceSwitch)

        if not aRoceSwitch:
            self.mAddToKnownHostsForOlVersionMismatchConfigs(aHost, aRemoteHostList, aTargetType)
            # Add host's ssh public key to the cells
            self.mRemoveKeyFromHosts(aHost.split('.')[0], aRemoteHostList, aExcludePatternsRegEx="EXACLOUD KEY|ExaKms")
            # Removes the ssh key based on both host name and key comment if found
            # before adding new key.
            self.mRemoveKeyFromHostsByComment(self.__hostkey, aRemoteHostList)
            self.mAddKeyToHosts(_key, aRemoteHostList)
        else:
            self.mAddKeyToRoceSwitches(_key, aRemoteHostList)
        return _key

    def mSetSSHPasswordlessForVMBackup(self, aHost, aRemoteHostList, aKeyComment="EXAVMBACKUP_KEY_TAG"):
        """
        Set ssh passwordless between the host and a list of remote hosts.
        """
        _key = self.mGetSSHPublicKeyFromHostForVMBackup(aHost, aKeyComment)

        # Integrity check of known_hosts file
        if not self.mValidateKnownHostsFile(aHost, True):
            raise Exception(f'known_hosts file error on host {aHost}')

        # Add host to known_hosts
        self.mRemoveFromKnownHosts(aHost, aRemoteHostList)
        self.mAddToKnownHosts(aHost, aRemoteHostList)

        # Add host's ssh public key to remote 
        self.mRemoveKeyFromHosts(aHost.split('.')[0], aRemoteHostList, aExcludePatternsRegEx="EXACLOUD KEY|ExaKms")
        self.mRemoveKeyFromHostsByComment(self.__hostkey, aRemoteHostList)
        self.mAddKeyToHosts(_key, aRemoteHostList)

        return _key

    def mGetSSHPublicKeyFromHostForVMBackup(self, aHost, aKeyComment = "EXAVMBACKUP_KEY_TAG"):
        """
        Returns aHost's public ssh key value. If the key doesn't exist, then it is created with ssh-keygen command.
        """

        _exakms = get_gcontext().mGetExaKms()

        _is_rsa = True
        if _exakms.mGetDefaultKeyAlgorithm() == "ECDSA":
            _is_rsa = False


        _ssh_key = ''
        _cmd = ""

        if _is_rsa:

            _cmd = "if [[ ! -f /root/.ssh/id_rsa_vmbackup || ! -f /root/.ssh/id_rsa_vmbackup.pub ]] ; " \
                "then if [[ ! -d /root/.ssh ]] ; then mkdir /root/.ssh ; chmod 0700 /root/.ssh ; fi ; " \
                "rm -f /root/.ssh/id_rsa_vmbackup /root/.ssh/id_rsa_vmbackup.pub ; " \
                f"ssh-keygen -C \"{aKeyComment}\" -q -t rsa -N \"\" -f /root/.ssh/id_rsa_vmbackup > /dev/null 2>&1; fi ; " \
                "cat /root/.ssh/id_rsa_vmbackup.pub"

        else:

            _cmd = "if [[ ! -f /root/.ssh/id_ecdsa_vmbackup || ! -f /root/.ssh/id_ecdsa_vmbackup.pub ]] ; " \
                "then if [[ ! -d /root/.ssh ]] ; then mkdir /root/.ssh ; chmod 0700 /root/.ssh ; fi ; " \
                "rm -f /root/.ssh/id_ecdsa_vmbackup /root/.ssh/id_ecdsa_vmbackup.pub ; " \
                f"ssh-keygen -C \"{aKeyComment}\" -q -t ecdsa -b 384 -m PEM -N \"\" -f /root/.ssh/id_ecdsa_vmbackup > /dev/null 2>&1; fi ; " \
                "cat /root/.ssh/id_ecdsa_vmbackup.pub"

        with connect_to_host(aHost, get_gcontext()) as _node:

            # Create new SSH Key
            _in, _out, _err = _node.mExecuteCmd(_cmd)
            if _node.mGetCmdExitStatus():
                ebLogError(f'Failed to get public key for host {aHost}: mExecuteCmd Failed: with error: {_err.readlines()}')
            else:
                _output = _out.readlines()
                if _output:
                    _ssh_key  = _output[0].strip()
                    ebLogInfo(f'Obtained SSH public key for host {aHost}')
                    # Retain the key comment which can be used when cleanup
                    self.__hostkey = aKeyComment

        return _ssh_key

    def mRestoreSSHKey(self, aHost, aUser=None):
        if aUser:
            _username = aUser
        else:
            _username = 'root'

        with connect_to_host(aHost, get_gcontext(), username=_username) as _node:
            _exakms = get_gcontext().mGetExaKms()
            # Backup key
            _keypair_files = ['/root/.ssh/id_rsa','/root/.ssh/id_rsa.pub']
            if _exakms.mGetDefaultKeyAlgorithm() == "ECDSA":
               _keypair_files = ['/root/.ssh/id_ecdsa','/root/.ssh/id_ecdsa.pub']
            for _filename in _keypair_files:
                _file_exists = False
                if _username == 'root':
                    _file_exists = _node.mFileExists(f"{_filename}_keybackup")
                else:
                    _node.mExecuteCmd(f"ls {_filename}_keybackup")
                    if _node.mGetCmdExitStatus() == 0:
                        _file_exists = True
                if _file_exists:
                    _, _o, _e = _node.mExecuteCmd(f"/bin/mv -f {_filename}_keybackup {_filename}")
                    if _node.mGetCmdExitStatus() != 0:
                        ebLogWarn(f"Backup not avaliable: {_o.read()}, {_e.read()}")

 
    def mCleanSSHPasswordless(self, aHost, aRemoteHostList, aUser=None, aSkipRestore=False):

        """
        Cleans the ssh passwordless configuration.
        """

        # Removes the ssh key based on both host name and key comment if found.
        # Infact, removes the ssh key based on the comment would be
        # sufficient in future.
        _hosts = aHost.split('.')
        self.mRemoveKeyFromHosts(_hosts[0], aRemoteHostList, aExcludePatternsRegEx="EXACLOUD KEY|ExaKms")
        self.mRemoveKeyFromHostsByComment(self.__hostkey, aRemoteHostList)
        if not aSkipRestore:
            self.mRestoreSSHKey(aHost, aUser)

    def mCleanSSHPasswordlessForClusterless(self, aHost, aRemoteHostList, aUser=None):

        """
        Cleans the ssh passwordless configuration.
        """

        # Removes the ssh key based on both host name and key comment if found.
        # Infact, removes the ssh key based on the comment would be
        # sufficient in future.
        _hosts = aHost.split('.')
        self.mRemoveKeyFromHosts(_hosts[0], aRemoteHostList, aExcludePatternsRegEx="EXACLOUD KEY|ExaKms")
        self.mRemoveKeyFromHostsByComment(self.__hostkey, aRemoteHostList)


        # Cleanup examisc key, if old key exists on the launch node
        if self.__hostkey != 'EXACMISC KEY':
            self.mRemoveKeyFromHostsByComment("EXACMISC KEY", aRemoteHostList)



    def mConfigureSshForMgmtHost(self, aLaunchNode, aRemoteHostList, aKeyComment, aInfraPatchBase):
        """
        This method is called for configuring passwordless ssh for management host
        """
        keys_dir = aInfraPatchBase + "keys/"
        _exakms = get_gcontext().mGetExaKms()
        _is_rsa = True
        if _exakms.mGetDefaultKeyAlgorithm() == "ECDSA":
            _is_rsa = False
        _ssh_key = ''
        _cmd = ""
        _priv = ""
        _pub = ""
        _gen_key = ""
        _get_key = ""
        _priv_key_file_name = None
        _pub_key_file_name = None


        with connect_to_host(aLaunchNode, get_gcontext(), username='opc') as _node:
            ls_path = node_cmd_abs_path_check(_node, "ls")
            cat_path = node_cmd_abs_path_check(_node, "cat")
            mv_path = node_cmd_abs_path_check(_node, "mv")
            ssh_keygen_path = node_cmd_abs_path_check(_node, "ssh-keygen")
            mkdir_path = node_cmd_abs_path_check(_node, "mkdir")

            #Create keys folder if it does not exists
            _keys_dir_check = f"{ls_path} {keys_dir}"
            _, _o, _e = _node.mExecuteCmd(_keys_dir_check)
            _keys_dir_result = _node.mGetCmdExitStatus()
            if _keys_dir_result != 0:
                _cmd = f"{mkdir_path} {keys_dir}"
                _, _o, _e = _node.mExecuteCmd(_cmd)
                if _node.mGetCmdExitStatus() != 0:
                    ebLogError(f"Keys directory creation failed")

            for aRemoteHost in aRemoteHostList:
                #Generate the keys
                if _is_rsa:
                    _priv_key_file_name = f"{keys_dir}{aRemoteHost}_id_rsa"
                    _pub_key_file_name = f"{keys_dir}{aRemoteHost}_id_rsa.pub"
                    _gen_key = f"{ssh_keygen_path} -C '{aKeyComment}' -q -t rsa -N \"\" -f \"{_priv_key_file_name}\"<<<y"
                else:
                    _priv_key_file_name = f"{keys_dir}{aRemoteHost}_id_ecdsa"
                    _pub_key_file_name = f"{keys_dir}{aRemoteHost}_id_ecdsa.pub"
                    _gen_key = f"{ssh_keygen_path} -C '{aKeyComment}' -q -t ecdsa -N \"\" -f \"{_priv_key_file_name}\"<<<y"

                _get_key = f"{cat_path} {_pub_key_file_name}"
                self.__priv_hostkey_files.append(_priv_key_file_name)
                self.__pub_hostkey_files.append(_pub_key_file_name)

                _, _o, _e = _node.mExecuteCmd(_gen_key)
                if _node.mGetCmdExitStatus() != 0:
                    ebLogWarn(f"Key generation failed")
                else:
                    ebLogWarn(f"Key generation successfull")
                _in, _out, _err = _node.mExecuteCmd(_get_key)
                if _node.mGetCmdExitStatus():
                    ebLogError(
                        f'Failed to get public key for host {aLaunchNode}: mExecuteCmd Failed: with error: {_err.readlines()}')
                else:
                    _output = _out.readlines()
                    if _output:
                        _ssh_key = _output[0].strip()
                        ebLogInfo(f'Obtained SSH public key for host {aLaunchNode}')
                        # Retain the key comment which can be used when cleanup
                        self.__hostkey = aKeyComment
                #
                #Update /root/.ssh/config file
                #Sample entry on the config file is given below:
                #Host sea201415exddu0907.sea2mvm01roce.adminsea2.oraclevcn.com
                #    HostName sea201415exddu0907.sea2mvm01roce.adminsea2.oraclevcn.com
                #    User root
                #    IdentityFile /var/odo/InfraPatchBase/keys/sea201415exddu0907.sea2mvm01roce.adminsea2.oraclevcn.com_id_rsa
                #
                echo_path = node_cmd_abs_path_check(_node, "echo")
                sed_path = node_cmd_abs_path_check(_node, "sed")
                sudo_path = node_cmd_abs_path_check(_node, "sudo")
                tee_path = node_cmd_abs_path_check(_node, "tee")
                _config_entry = "Host "+ aRemoteHost + "\n    HostName "+ aRemoteHost + "\n    User root\n    IdentityFile "+ _priv_key_file_name + "\n"
                _cmd = f'{echo_path} "{_config_entry}" | {sudo_path} {tee_path} -a /root/.ssh/config'
                _node.mExecuteCmd(_cmd)

                if _node.mGetCmdExitStatus() != 0:
                        ebLogError(f"Ssh config file addition failed")
                else:
                    ebLogInfo(f"Ssh config file addition successful")

                # Add host's ssh public key to domu, before adding remove based on comment and by hostname
                self.mRemoveKeyFromHosts(aLaunchNode.split('.')[0], [aRemoteHost], aExcludePatternsRegEx="EXACLOUD KEY|ExaKms")
                self.mRemoveKeyFromHostsByComment(self.__hostkey, [aRemoteHost])
                self.mAddKeyToHosts(_ssh_key, [aRemoteHost])

        # Integrity check of known_hosts file
        if not self.mValidateKnownHostsFile(aLaunchNode, True, 'opc'):
            raise Exception(f'known_hosts file error on host {aLaunchNode}')
        # Update known host file
        self.mRemoveFromKnownHosts(aLaunchNode, aRemoteHostList, False, 'opc')
        self.mAddToKnownHosts(aLaunchNode, aRemoteHostList, 'opc')

    def mCleanupSSHConfigForMgmtHost(self, aLaunchNode, aNodeList):
        """
        This method is called to cleanup passwordless ssh configuration
        on management host
        """

        _hosts = aLaunchNode.split('.')
        # Remove key by hostname and by comment on domu
        self.mRemoveKeyFromHosts(_hosts[0], aNodeList, aExcludePatternsRegEx="EXACLOUD KEY|ExaKms")
        self.mRemoveKeyFromHostsByComment(self.__hostkey, aNodeList)

        self.mRemoveFromKnownHosts(aLaunchNode, aNodeList, False, 'opc')
        with connect_to_host(aLaunchNode, get_gcontext(), username='opc') as _node:
            # Delete the keys
            rm_path = node_cmd_abs_path_check(_node, "rm")
            for _priv_key_file in self.get_priv_hostkey_files():
                _node.mExecuteCmd(f"{rm_path} {_priv_key_file}")
                if _node.mGetCmdExitStatus() != 0:
                    ebLogError(f"Deletion of {_priv_key_file} failed")

            for _pub_key_file in self.get_pub_hostkey_files():
                _node.mExecuteCmd(f"{rm_path} {_pub_key_file}")
                if _node.mGetCmdExitStatus() != 0:
                    ebLogError(f"Deletion of {_pub_key_file} failed")


    def mCleanupSSHConfigFileOnMgmtHost(self, aLaunchNode, aNodeList):
        with connect_to_host(aLaunchNode, get_gcontext(), username='opc') as _node:
            # Remove the entry from root ssh config file
            sed_path = node_cmd_abs_path_check(_node, "sed")
            for aNode in aNodeList:
                _remove_entry = f"{sed_path} -i -e '/Host {aNode}/,+4d' /root/.ssh/config"
                _node.mExecuteCmd(_remove_entry)
                if _node.mGetCmdExitStatus() != 0:
                    ebLogError(f"Ssh config file entry removal failed")

###############################################################################

class OracleVersion(object):
    """
    Handle operations on oracle version like compare, sort and
    get latest/highest oracle versions.
    """

    def mCompareVersions(self, aCurrentVersion = None, aTargetVersion = None):
        """
        Compare current and target version and return based on the comparison.
        Return 0, if aCurrentVersion and aTargetVersion are equal,
        return -1, if aCurrentVersion is lesser than aTargetVersion,
        return 1, if aCurrentVersion is greater than aTargetVersion.
        This function is expected to work for oracle version format and
        also for any two given strings.

        """
        if not aCurrentVersion or not aTargetVersion:
            ebLogError ("Invalid inputs: Provide valid compare versions")
            return None

        # if the given input versions are numbers, do the number camparision
        if type(aCurrentVersion) == int and type(aTargetVersion) == int:
            if aCurrentVersion == aTargetVersion:
                return 0
            elif aCurrentVersion > aTargetVersion:
                return 1
            else:
                return -1

        _ver1, _ver2 = aCurrentVersion, aTargetVersion
        try:
            # IBSWITCH version can have fomrat like 2.1.8-1 and needs to be
            # taken care
            _ver1 = (re.sub('[-]', '.', _ver1))
            _ver2 = (re.sub('[-]', '.', _ver2))

            _ver1 = _ver1.split(".")
            _ver2 = _ver2.split(".")

            _comp_count_to_cmp = min(len(_ver1), len(_ver2))

            for i in range (_comp_count_to_cmp):
                # Do the numeric comparison
                if _ver1[i].isdigit() and _ver2[i].isdigit():
                     if int(_ver1[i]) == int(_ver2[i]):
                        continue
                     elif int(_ver1[i]) > int(_ver2[i]):
                        return 1
                     else:
                        return -1
                # Do the alphanumeric comparison
                elif _ver1[i].isalnum() or _ver2[i].isalnum():
                     if _ver1[i] == _ver2[i]:
                        continue
                     elif _ver1[i] > _ver2[i]:
                        return 1
                     else:
                        return -1

            if ((i + 1) == _comp_count_to_cmp):
                if (len(_ver1) == len(_ver2)):
                    return 0
                elif (len(_ver1) > len(_ver2)):
                    return 1
                else:
                    return -1
        except Exception as err:
            ebLogWarn("Version error: " + str(err))
            return None

    def mSortVersion(self, aListVersions):
        """
        Sort the exadata oracle version in ascending order.
        """
        # if no elements in the list, just return
        if not aListVersions or len(aListVersions) == 0:
            return None
        # if only one element in the list, nothing to be sort.
        elif len(aListVersions) == 1:
            return aListVersions

        _sortlist = sorted(aListVersions, key=cmp_to_key(self.mCompareVersions))
        return _sortlist

    def mGetHighestVer(self, aListVersions):
        """
        This function sort and get the highest version from the given list
        """
        # if no elements in the list, just return
        if not aListVersions or len(aListVersions) == 0:
            return None
        # if only one element in the list, nothing to be compare, return as is.
        elif len(aListVersions) == 1:
            return aListVersions[0]

        _sortlist = sorted(aListVersions, key=cmp_to_key(self.mCompareVersions))
        return _sortlist[-1]

class ebFortifyIssues(object):
    """
    Test and validate the errors reprorted by fortify tool on python code.
    """

    def mPathManipulationError(self, aFilePath = None):
        """ 
        This function search for a char or word which has security concerns.
        Return True, if file path has security related strings or chars and
                     it's not valid path
               False, if file path is good and doesn't have any vulnerable
                     word or chars. 
        """ 

        _vulnerable_word = ['..', '.\\.', 'etc', 'system', 'password', 'boot', 'device']
        _vulnerable_char = ['$', '#', '?', '^', '%', '@', '!', '&', '*']

        # If vulnerable word is found, then return
        for _security_word in _vulnerable_word: 
            if (aFilePath.find(_security_word) != -1): 
                ebLogError("Invalid word in file path: " + _security_word)
                return True

        # If vulnerable character is found, then return
        for _security_char in _vulnerable_char: 
            if (aFilePath.find(_security_word) != -1): 
                ebLogError("Invalid character in file path: " + _security_word)
                return True

        return False

#class added for fault injection
class ebCluFaultInjection(object):
    def __init__(self, aCluCtrlObj, aOptions):
        self.__cluctrl = aCluCtrlObj
        self.__aOptions = aOptions
        self.__hostname = aOptions.jsonconf['hostname']
        self.__optype = aOptions.jsonconf['optype']
        self.__nodetype = aOptions.jsonconf['nodetype']
        self.timeout = 10
        get_gcontext().mSetConfigOption('ssh_connect_max_retries', '1')

    def mHandleRequest(self):
        if self.__optype == 'instancehealth':
            return self.mHandleInstanceHealth()
        elif self.__optype == 'lifecycle':
            action = self.__aOptions.jsonconf.get('action', None)
            if action == None:
                _err = "Fault Injection rejected as action parameter is not provided"
                ebLogError(_err)
                raise ExacloudRuntimeError(0x0750, 0xA, _err)
            return self.mHandleHostLifeCycleUsingIlom(action)
        elif self.__optype == 'network-partition':
            action = self.__aOptions.jsonconf.get('action', None)
            if action == None:
                _err = "Fault Injection rejected as action parameter is not provided"
                ebLogError(_err)
                raise ExacloudRuntimeError(0x0750, 0xA, _err)
            return self.mHandleNetworkPartition(action)
        else:
            _err = "Fault Injection rejected for invalid optype"
            ebLogError(_err)
            raise ExacloudRuntimeError(0x0750, 0xA, _err)
            

    def mHandleInstanceHealth(self):
        with connect_to_host(self.__hostname, get_gcontext(), timeout=self.timeout) as _node:
            ebLogInfo(f"Host is connectable:{self.__hostname}")
            if self.__nodetype == "cell" and self.__cluctrl.mCheckCellsServicesUp(aRestart=False, aCellList=[self.__hostname]):
                ebLogInfo(f"cell services up for hostname: {self.__hostname}")
        return True

    def mHandleHostLifeCycleUsingIlom(self, action):
        _mac = self.__cluctrl.mGetMachines().mGetMachineConfig(self.__hostname)
        _iloms = _mac.mGetMacIlomNetworks()
        for _ilom in _iloms:
            _ilomCfg = self.__cluctrl.mGetIloms().mGetIlomConfig(_ilom)
            _ilomNet = self.__cluctrl.mGetNetworks().mGetNetworkConfig(_ilomCfg.mGetIlomNetworkId())
            _ilomName = "{0}.{1}".format(_ilomNet.mGetNetHostName(), _ilomNet.mGetNetDomainName())
            ebLogTrace(f"ILOM HOSTNAME:{_ilomName}")
        if action == "stop":
            ebLogInfo(f"Stopping HOSTNAME:{self.__hostname}")
            ilomObj = ebCluStartStopHostFromIlom(self.__cluctrl)
            ebLogInfo(f"Operation stop to be performed on host {self.__hostname} via ilom {_ilomName}")
            ilomObj.mStopHostfromIlom(_ilomName)
            _is_trying_graceful_shutdown = True
            _timeout = FAULT_INJECTION_STOP_SLEEP_TIME_FROM_ILOM
            _initial_time = time.time()
            ebLogTrace(f"Waiting for the host {self.__hostname} to be shutdown..")
            while True:
                _elapsed_time = time.time() - _initial_time
                if not self.__cluctrl.mPingHost(self.__hostname):
                    ebLogInfo(f"Host {self.__hostname} not pingeable after stop from ilom and {_elapsed_time} seconds wait time")
                    break

                if _timeout < _elapsed_time:
                    if _is_trying_graceful_shutdown:
                        ebLogInfo(f"Host {self.__hostname} is still pingable after {_elapsed_time} seconds. Force shutdown will be triggered.")
                        ilomObj.mStopHostfromIlom(_ilomName, False)
                        _is_trying_graceful_shutdown = False
                        _initial_time = time.time()
                    else:
                        raise ExacloudRuntimeError(0x0114, 0xA, f"Timeout while waiting for host {self.__hostname} to be stopped.")

                ebLogTrace(f"Waiting for host {self.__hostname} to be stopped : {_elapsed_time}")
                time.sleep(FAULT_INJECTION_PING_CHECK_INTERVAL)
                
        if action == "start":
            ebLogInfo(f"Starting HOSTNAME:{self.__hostname}")
            ilomObj = ebCluStartStopHostFromIlom(self.__cluctrl)
            ebLogInfo(f"Operation start to be performed on host {self.__hostname} via ilom {_ilomName}")
            ilomObj.mStartHostfromIlom(_ilomName)
            _timeout = START_SLEEP_TIME_FROM_ILOM
            _initial_time = time.time()
            ebLogInfo(f"Waiting for the host {self.__hostname} to start up..")
            ebLogTrace("Waiting for 30 seconds first for the host to start up.")
            time.sleep(FAULT_INJECTION_INIT_CHECK_DELAY_AFTER_START)
            while True:
                _elapsed_time = time.time() - _initial_time
                if self.__cluctrl.mPingHost(self.__hostname):
                    ebLogInfo(f"Host {self.__hostname} pingeable after start from ilom and {_elapsed_time} seconds wait time")
                    break
                
                if _timeout < _elapsed_time:
                    raise ExacloudRuntimeError(0x0114, 0xA, f"Timeout while waiting for host {self.__hostname} to be started.")

                ebLogTrace(f"Waiting for host {self.__hostname} to be started : {_elapsed_time}")
                time.sleep(FAULT_INJECTION_PING_CHECK_INTERVAL)
                
        return True

    def mHandleNetworkPartition(self, action):
        """Up/Down cell network interface
        """
        interfaces = ["stre0", "stre1"]
        for interface in interfaces: 
            ebLogInfo(f"Checking state of {interface} on {self.__hostname}.")
            interface_state = self.mGetInterfaceState(interface)
            if interface_state and action == 'down':
                # if interface is up and we need to bring it down
                self.mToggleCellInterface(interface, action)
            if not interface_state and action == 'up':
                # if interface is down and we need to bring it up
                self.mToggleCellInterface(interface, action)
        return True
    
    def mGetInterfaceState(self, iface):
        """  
        Get the state of a network interface using the `ip` command.  
        Returns True if the interface is UP, otherwise False.
        """  
        try: 
            with connect_to_host(self.__hostname, get_gcontext(), timeout=self.timeout) as _node:
                # sample output
                #[root@sea201507exdcl06 ~]# /usr/sbin/ip a s stre0
                #7: stre0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 2300 qdisc mq state UP group default qlen 1000
                    #link/ether 66:d4:3e:aa:33:05 brd ff:ff:ff:ff:ff:ff
                    #altname enp177s0f0v0
                    #altname ens3f0v0
                    #inet 100.106.33.100/16 brd 100.106.255.255 scope global stre0
                    #valid_lft forever preferred_lft forever
                _cmd = f'/usr/sbin/ip a s {iface} | /bin/grep state'
                _, _o, _ = _node.mExecuteCmd(_cmd)
            _out = _o.readlines()
            output_string = ''.join(_out)
            output_string = output_string.strip()
            # sample output: 
            # '7: stre0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 2300 qdisc mq state UP group default qlen 1000'
            # '7: stre0: <BROADCAST,MULTICAST> mtu 2300 qdisc mq state DOWN group default qlen 1000
            if "state UP" in output_string:
                ebLogInfo(f'Interface ; {iface} is UP on {self.__hostname}')
                return True
            if "state DOWN" in output_string or "<NO-CARRIER>" in output_string:
                ebLogInfo(f'Interface ; {iface} is DOWN on {self.__hostname}')
            return False
        except Exception as e:
            ebLogError(f"Error checking state of {iface}: {e}")
            return False
    
    def mToggleCellInterface(self, iface, state):
        with connect_to_host(self.__hostname, get_gcontext(), timeout=self.timeout) as _node:
            _cmd = f'/usr/sbin/ip link set {iface} {state}'
            _node.mExecuteCmdLog(_cmd)

#class added to fetch ssh keys
class ebCluFetchSshKeys(object):

    def __init__(self, aCluCtrlObj, aLocalHost):
        self.__cluctrl = aCluCtrlObj
        self.__host = aLocalHost
        self.__mapping_table = { 'dom0':{}, 'domu':{}, 'cell':{}, 'ibswitch':{} }
        self.__kms = get_gcontext().mGetExaKms()

        for _dom0, _domU in self.__cluctrl.mReturnDom0DomUPair():
            self.__mapping_table['dom0'][_dom0.strip()] = {}
            self.__mapping_table['domu'][_domU.strip()] = {}
            self.__mapping_table['domu'][_domU]['NAT'] = {}

            if self.__cluctrl.mIsExabm():
                _domu_conf = self.__cluctrl.mGetMachines().mGetMachineConfig(_domU)
                _domu_conf_net = _domu_conf.mGetMacNetworks()
                for _net_id in _domu_conf_net:
                    _net_conf = self.__cluctrl.mGetNetworks().mGetNetworkConfig(_net_id)
                    _fall_back = False if _net_conf.mGetNetType() == 'client' else True
                    _nat_ip = _net_conf.mGetNetNatAddr(_fall_back)
                    _nat_ip_v6 = _net_conf.mGetNetNatAddr(_fall_back, ip_version='6')
                    _nat_host = _net_conf.mGetNetNatHostName(_fall_back)
                    _nat_domain = _net_conf.mGetNetNatDomainName()
                    self.mUpdateNetworkConf(_domU, _nat_ip, _nat_ip_v6, _nat_host, _nat_domain, _net_conf.mGetNetType())
            else:
                self.__mapping_table['domu'][_domU]['NAT']['ip'] = ''
                self.__mapping_table['domu'][_domU]['NAT']['host'] = ''
                self.__mapping_table['domu'][_domU]['NAT']['domain'] = ''
                self.__mapping_table['domu'][_domU]['BACKUP'] = {}
                self.__mapping_table['domu'][_domU]['BACKUP']['ip'] = ''
                self.__mapping_table['domu'][_domU]['BACKUP']['ipv6'] = ''
                self.__mapping_table['domu'][_domU]['BACKUP']['host'] = ''
                self.__mapping_table['domu'][_domU]['BACKUP']['domain'] = ''

        for _cell in self.__cluctrl.mReturnCellNodes():
             self.__mapping_table['cell'][_cell.strip()] = {}

        for _switch in self.__cluctrl.mReturnSwitches(True):
            self.__mapping_table['ibswitch'][_switch.strip()] = {}

    def mUpdateNetworkConf(self, anodeType, aNatIp, aNatIpv6, aNatHost, aNatDomain, aNetType):
        _nat_ip = aNatIp
        _nat_ip_v6 = aNatIpv6
        _nat_host = aNatHost
        _nat_domain = aNatDomain
        if aNetType in ['client', 'backup']:
            _net_type = 'NAT' if aNetType == 'client' else aNetType
            self.__mapping_table['domu'][anodeType][_net_type] = {}
            if _nat_ip and _nat_host:
                self.__mapping_table['domu'][anodeType][_net_type]['ip'] = _nat_ip
                self.__mapping_table['domu'][anodeType][_net_type]['host'] = _nat_host
                self.__mapping_table['domu'][anodeType][_net_type]['domain'] = _nat_domain
            if _nat_ip_v6 and _nat_host:
                self.__mapping_table['domu'][anodeType][_net_type]['ipv6'] = _nat_ip_v6
                self.__mapping_table['domu'][anodeType][_net_type]['host'] = _nat_host
                self.__mapping_table['domu'][anodeType][_net_type]['domain'] = _nat_domain

    def mGetSingleSSHKey(self, aJsonKeyData, aHost, aUser,aDomainName=None):
        """
        Internal Function
        Returns SSH Key File based on the input nodetype and user
        """
        if len(aHost.split('.')) == 1 and aDomainName:
            aHost = f"{aHost}.{aDomainName}"
        _params = {"FQDN": aHost,  "user": aUser}
        _kmsEntry = self.__kms.mGetExaKmsEntry(_params)
        if _kmsEntry:
            aJsonKeyData['key'] = _kmsEntry.mGetPrivateKey()
        else:
            aJsonKeyData['key'] = ''
            ebLogWarn(f"KEY NOT FOUND for host {aHost} as  {aUser} user!")

        return aJsonKeyData

    def mGetSSHkeys(self, aJsonKeyData, anodeType='all_nodes', aHost='all', aUser='root', aNode=None):
        """
        Internal Function
        Returns SSH Keys based on node type and user
        """

        _rc = 0
        if anodeType == 'dom0':
            aJsonKeyData[anodeType] = {}
            if aHost == 'all':
                for _dom0 in self.__mapping_table['dom0'].keys():
                    aJsonKeyData[anodeType][_dom0] = {}
                    aJsonKeyData[anodeType][_dom0] = self.mGetSingleSSHKey(aJsonKeyData[anodeType][_dom0], _dom0, aUser)
            else:
                if aHost in self.__mapping_table['dom0']:
                    aJsonKeyData[anodeType][aHost] = {}
                    aJsonKeyData[anodeType][aHost] = self.mGetSingleSSHKey(aJsonKeyData[anodeType][aHost], aHost, aUser)
                else:
                    ebLogError(f'*** Invalid hostname {aHost}')
                    return ebError(0x766), {}
        elif anodeType == 'domu':
            aJsonKeyData[anodeType] = {}
            if aHost == 'all':
                for _domU in self.__mapping_table['domu'].keys():
                    aJsonKeyData[anodeType][_domU] = {}
                    aJsonKeyData[anodeType][_domU]['key'] = ''
                    aJsonKeyData[anodeType][_domU]['NAT'] = self.__mapping_table['domu'][_domU]['NAT']
                    aJsonKeyData[anodeType][_domU]['NAT']['key'] = ''
                    _nat = self.__mapping_table['domu'][_domU]['NAT']['host']

                    
                    if _nat:
                        aDomainName = self.__mapping_table['domu'][_domU]['NAT']['domain']
                        aJsonKeyData[anodeType][_domU]['NAT'] = self.mGetSingleSSHKey(aJsonKeyData[anodeType][_domU]['NAT'], _nat, aUser,aDomainName)

                        if aJsonKeyData[anodeType][_domU]['NAT']['key'] != '':
                            aJsonKeyData[anodeType][_domU]['key'] = aJsonKeyData[anodeType][_domU]['NAT']['key']
                    else:
                        aJsonKeyData[anodeType][_domU] = self.mGetSingleSSHKey(aJsonKeyData[anodeType][_domU], _domU, aUser)
                    #root key not found. Trying for opc key    
                    if aJsonKeyData[anodeType][_domU]['key'] == '':
                        ebLogWarn("*** 'root' key not found, trying with 'opc' user")
                        if aUser == 'root':
                            _opcUser = 'opc'
                            if _nat:
                                aJsonKeyData[anodeType][_domU]['NAT'] = self.mGetSingleSSHKey(aJsonKeyData[anodeType][_domU]['NAT'], _nat, _opcUser)

                                if aJsonKeyData[anodeType][_domU]['NAT']['key'] != '':
                                    aJsonKeyData[anodeType][_domU]['key'] = aJsonKeyData[anodeType][_domU]['NAT']['key']
                            else:
                                aJsonKeyData[anodeType][_domU] = self.mGetSingleSSHKey(aJsonKeyData[anodeType][_domU], _domU, _opcUser)

                    if 'backup' in self.__mapping_table['domu'][_domU].keys():
                        aJsonKeyData[anodeType][_domU]['BACKUP'] = self.__mapping_table['domu'][_domU]['backup']
            else:
                if aHost in self.__mapping_table['domu']:
                    aJsonKeyData[anodeType][aHost] = {}
                    aJsonKeyData[anodeType][aHost]['key'] = ''
                    aJsonKeyData[anodeType][aHost]['NAT'] = self.__mapping_table['domu'][aHost]['NAT']
                    aJsonKeyData[anodeType][aHost]['NAT']['key'] = ''
                    _nat = self.__mapping_table['domu'][aHost]['NAT']['host']
                    if _nat:
                        aJsonKeyData[anodeType][aHost]['NAT'] = self.mGetSingleSSHKey(aJsonKeyData[anodeType][aHost]['NAT'], _nat, aUser)

                        if aJsonKeyData[anodeType][aHost]['NAT']['key'] != "":
                            aJsonKeyData[anodeType][aHost]['key'] = aJsonKeyData[anodeType][aHost]['NAT']['key']
                    else:
                        aJsonKeyData[anodeType][aHost] = self.mGetSingleSSHKey(aJsonKeyData[anodeType][aHost], aHost, aUser)

                    if 'backup' in self.__mapping_table['domu'][aHost].keys():
                        aJsonKeyData[anodeType][aHost]['BACKUP'] = self.__mapping_table['domu'][aHost]['backup']
                else:
                    ebLogError(f'*** Invalid hostname {aHost}')
                    return ebError(0x766), {}
        elif anodeType == 'cell':
            aJsonKeyData[anodeType] = {}
            if aHost == 'all':
                for _cell in self.__mapping_table['cell'].keys():
                    aJsonKeyData[anodeType][_cell] = {}
                    aJsonKeyData[anodeType][_cell] = self.mGetSingleSSHKey(aJsonKeyData[anodeType][_cell], _cell, aUser)
            else:
                if aHost in self.__mapping_table['cell']:
                    aJsonKeyData[anodeType][aHost] = {}
                    aJsonKeyData[anodeType][aHost] = self.mGetSingleSSHKey(aJsonKeyData[anodeType][aHost], aHost, aUser)
                else:
                    ebLogError(f'*** Invalid hostname {aHost}')
                    return ebError(0x766), {}
        elif anodeType == 'ibswitch':
            if not self.__cluctrl.mIsKVM():
                aJsonKeyData[anodeType] = {}
                if aHost == 'all':
                    for _switch in self.__mapping_table['ibswitch'].keys():
                        aJsonKeyData[anodeType][_switch] = {}
                        aJsonKeyData[anodeType][_switch] = self.mGetSingleSSHKey(aJsonKeyData[anodeType][_switch], _switch, aUser)
                else:
                    if aHost in self.__mapping_table['ibswitch']:
                        aJsonKeyData[anodeType][aHost] = {}
                        aJsonKeyData[anodeType][aHost] = self.mGetSingleSSHKey(aJsonKeyData[anodeType][aHost], aHost, aUser)
                    else:
                        ebLogError(f'*** Invalid hostname {aHost}')
                        return ebError(0x766), {}
        elif anodeType == 'all_nodes':
            _rc, aJsonKeyData = self.mGetSSHkeys(aJsonKeyData, 'dom0', aHost, aUser, aNode)
            _rc, aJsonKeyData = self.mGetSSHkeys(aJsonKeyData, 'domu', aHost, aUser, aNode)
            _rc, aJsonKeyData = self.mGetSSHkeys(aJsonKeyData, 'cell', aHost, aUser, aNode)
            _rc, aJsonKeyData = self.mGetSSHkeys(aJsonKeyData, 'ibswitch', aHost, aUser, aNode)
        else:
            ebLogError(f'Invalid Node Type {anodeType}')
            return ebError(0x766), {}
        return _rc, aJsonKeyData

    def mUpdateRequestData(self, aOptions, rc, aData, err):
        """
        Updates request object with the response payload
        """
        _reqobj = self.__cluctrl.mGetRequestObj()
        _response = {}
        _response["success"] = "True" if (rc == 0) else "False"
        _response["error"] = err
        _response["output"] = aData
        if _reqobj is not None:
            _db = ebGetDefaultDB()
            _reqobj.mSetData(json.dumps(_response, sort_keys = True))
            _db.mUpdateRequest(_reqobj)

        ebLogJson(json.dumps(_response, indent=4, sort_keys = True))

    def mFetchSshKeys(self, aOptions):
        """
        Returns SSH Keys based on nodeType
        """
        _nodeType = 'all_nodes'
        _user = 'root'
        _host = 'all'

        _rc = 0
        _out, _err = {}, ""
        _options = aOptions
        try:
            # Parse the json and read the attributes
            _inputjson = _options.jsonconf
            if _inputjson:
                if 'node_type' in _inputjson.keys() and _inputjson['node_type'].strip():
                    _nodeType = _inputjson['node_type'].strip().lower()

                if 'user' in _inputjson.keys() and _inputjson['user'].strip():
                    _user = _inputjson['user'].strip().lower()

                if 'host' in _inputjson.keys() and _inputjson['host'].strip():
                    _host = _inputjson['host'].strip().lower()

            _data = {}
            _node = exaBoxNode(get_gcontext(), aLocal=True)
            _node.mConnect(aHost=self.__host)
            _rc, _out = self.mGetSSHkeys(_data, _nodeType, _host, _user, _node)
            _node.mDisconnect()
            if _rc:
                _err = gSubError[str(hex(_rc&0xFFFF))[2:].upper()][0]
        except Exception as e:
            _rc = -1
            _err = 'Exception during fetchkeys command execution: '+ str(e)
            ebLogError('*** ' + str(_err))
        self.mUpdateRequestData(_options, _rc, _out, _err)
        if _rc != 0:
            raise ExacloudRuntimeError(0x0796, 0xA, _err)
        return _rc

class ebMiscFx:

    @staticmethod
    def mExecuteLocal(aCmd, aCurrDir=None, aStdIn=PIPE, aStdOut=PIPE, aStdErr=PIPE, aTimeOut=None):

        _args = shlex.split(aCmd)
        _current_dir = aCurrDir
        _stdin = aStdIn
        _std_out = aStdOut
        _stderr = aStdErr
        _proc = subprocess.Popen(_args, stdin=_stdin, stdout=_std_out, stderr=_stderr, cwd=_current_dir)
        _std_out, _std_err = wrapStrBytesFunctions(_proc).communicate(timeout=aTimeOut)
        _rc = _proc.returncode
        return _rc, None, _std_out, _std_err

    @staticmethod
    def mReplaceDiscover(aDict):

        if "natip" in aDict and aDict['natip'] == "discover":

            _nathost = "{0}.{1}".format(aDict['nathostname'], aDict['natdomain'])

            _cmd = f"/usr/bin/dig +short {_nathost}"
            _rc, _, _o, _e = ebMiscFx.mExecuteLocal(_cmd)

            if _rc == 0:

                _hostname = _o.strip()

                if _hostname:
                    aDict['natip'] = _hostname
                    return

            _msg = f"Could not reverse lookup of {_nathost}"
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x0740, 0xA, _msg)

    @staticmethod
    def getInitialIngestion(aHost) -> str:
        """
            Executes /usr/sbin/edvutil, available on OL8  
        """
        _initid = ""
        with connect_to_host(aHost, get_gcontext()) as dom0Node:                    
            _cmd = '/usr/sbin/edvutil lsedvnode'
            _, _o, _ = dom0Node.mExecuteCmd(_cmd)
            if dom0Node.mGetCmdExitStatus() != 0:
                return _initid
            _lines = _o.readlines()
            if len(_lines) != 0:
                _initid = _lines[0]
                if _initid.startswith('id:'):
                    _initid = _initid.split(":")[1].strip()
        return _initid   

    @staticmethod
    def mIsEth0Removed(aJson, aDom0):
        _json = aJson
        _dom0 = aDom0
        if 'customer_network' in _json and 'nodes' in _json['customer_network']:
            _nodes = _json['customer_network']['nodes']
            for _node in _nodes:
                if "fqdn" in list(_node.keys()) and _node["fqdn"] == _dom0:
                    if "eth0_removed" in _node:
                        ebLogTrace(f"*** mIsEth0Removed createservice: {_dom0}: eth0_removed: {_node['eth0_removed']}")
                        if _node['eth0_removed'].lower() == "true":
                            return True

        if 'reshaped_node_subset' in _json and 'added_computes' in _json['reshaped_node_subset']:

            for _added_compute in _json['reshaped_node_subset']['added_computes']:
                if _added_compute['compute_node_hostname'] == _dom0:
                    if "eth0_removed" in _added_compute:
                        ebLogTrace(f"*** mIsEth0Removed reshape: {_dom0}: eth0_removed: _added_compute['eth0_removed']")
                        if _added_compute['eth0_removed'].lower() == "true":
                            return True

        if 'reshaped_node_subset' in _json and 'participating_computes' in _json['reshaped_node_subset']:

            for _participating_compute in _json['reshaped_node_subset']['participating_computes']:
                if _participating_compute['compute_node_hostname'] == _dom0:
                    if "eth0_removed" in _participating_compute:
                        ebLogTrace(f"*** mIsEth0Removed reshape: {_dom0}: eth0_removed: _participating_compute['eth0_removed']")
                        if _participating_compute['eth0_removed'].lower() == "true":
                            return True

        with connect_to_host(_dom0, get_gcontext()) as _node:
            return not _node.mFileExists('/etc/sysconfig/network-scripts/ifcfg-vmeth0')

    @staticmethod
    def mIsSkipBondingBridge(aJson, aDom0):
        _json = aJson
        _dom0 = aDom0
        if 'customer_network' in _json and 'nodes' in _json['customer_network']:
            _nodes = _json['customer_network']['nodes']
            for _node in _nodes:
                if "fqdn" in list(_node.keys()) and _node["fqdn"] == _dom0:
                    if "skip_bonding" in _node:
                        ebLogTrace(f"*** mIsSkipBondingBridge : {_dom0}: skip_bonding: {_node['skip_bonding']}")
                        if _node['skip_bonding'].lower() == "true":
                            return True
                        
        return False

class ebSubnetIp(object):
    """
    Manage IP/Subnet strings and conversion
    Args:
        aIpStr (str): IPv4 String with following formats:
                      '10.0.0.1'                 (Single IP)
                      '10.0.0.0/24'              (IP/<0-32>)
                      '10.0.0.1/255.255.255.255' (IP/<0-255>.<0-255>...)
    """
    def __init__(self, aIpStr='127.0.0.1/32'):

        #Validation of none
        _ipStr = aIpStr
        if _ipStr is None:
            _ipStr = ''

        #Validate the existence of / on IP
        if _ipStr.find('/') != -1: 
            _base = _ipStr.split('/')
            _ip   = _base[0]
            _seg  = _base[1] 
        else:
            _ip  = _ipStr
            _seg = '32'

        #Validate the IP
        self.__ip = self.mIpToInt(_ip)
        if self.__ip is None:
            raise ValueError('*** SubnetIp: Invalid value for aIpStr: {}'.format(aIpStr))

        #Validate the Segment
        if _seg.find('.') == -1: 
            self.__segment = int(_seg)
        else:
            self.__segment = self.mMaskToSegment(_seg)

        if self.__segment > 32:
            self.__segment = 32

        #Reduce the segment for reading purposes
        self.__ip = self.mGetIntFirstIp()

    def mLimitSegment(self, aInt):
        if int(aInt) > 255 or int(aInt) < 0:
            raise ValueError('*** SubnetIp: Invalid value for segment: {}'.format(aInt))
        else:
            return int(aInt)

    def mIpToInt(self, aIpStr):
        #Divide the IP into Segments and Validate the Grammar
        try:
            _ipStr = aIpStr.replace(' ', '')
            
            if re.match('-{0,1}\d{1,3}\.-{0,1}\d{1,3}\.-{0,1}\d{1,3}\.-{0,1}\d{1,3}', _ipStr) is None:
                _segments = socket.gethostbyname(aIpStr)
                _segments = _segments.split('.')
            else:
                _segments = _ipStr.split('.')
        except:
            ebLogError("*** SubnetIp: Error on mIpToInt, aIpStr:'{}'".format(aIpStr))
            return None

        #Calculate the Binary Integer
        _number =  (self.mLimitSegment(_segments[0])) << 24
        _number += (self.mLimitSegment(_segments[1])) << 16
        _number += (self.mLimitSegment(_segments[2])) << 8
        _number += self.mLimitSegment(_segments[3])
        return _number

    def mIntToIp(self, aIpInt):
        if aIpInt is None:
            ebLogError("*** SubnetIp: Error on mIntToIp, aIpInt:'{}'".format(aIpInt))
            return None
        _segments =  str((aIpInt & 0xFF000000) >> 24) + '.'
        _segments += str((aIpInt & 0x00FF0000) >> 16) + '.'
        _segments += str((aIpInt & 0x0000FF00) >> 8)  + '.'
        _segments += str((aIpInt & 0x000000FF))
        return _segments

    def mSegmentToMask(self, aSegment):
        _fill = ''.zfill(int(aSegment)).replace('0', '1') + ''.zfill(32-int(aSegment))
        _numb = int(_fill, 2)
        return self.mIntToIp(_numb)

    def mMaskToSegment(self, aMask):
        _numb = self.mIpToInt(str(aMask))
        _numb = str(bin(_numb))[2:]
        return _numb.count('1')

    def mGetIntFirstIp(self):
        if self.__segment == 32:
            return self.__ip
        else:
            return (self.__ip & ((1 << self.__segment) - 1) << (32 - self.__segment))

    def mGetIntLastIp(self):
        if self.__segment == 32:
             return self.__ip
        else:
            return (self.__ip | ((1 << (32 - self.__segment)) -1))

    def mIsSubset(self, aIp):
        return self.mGetIntFirstIp() >= aIp.mGetIntFirstIp() and self.mGetIntLastIp() <= aIp.mGetIntLastIp()

    def mGetAllIPs(self):
        if self.__segment == 32:
            return [self.mIntToIp(self.__ip)]
        elif self.__segment == 31:
            return []
        else:
            return list(map(self.mIntToIp, list(range(self.mGetIntFirstIp(), self.mGetIntLastIp()+1))))

    def mGetSubnet(self):
        return self.mIntToIp(self.__ip) + '/' + self.mSegmentToMask(self.__segment)

    def mGetCIDR(self):
        return self.mIntToIp(self.__ip) + '/' + str(self.__segment)

class ebSubnetSet(object):
    """
    Manage ebSubnetIp class as a Set
    """
    def __init__(self):
        self.__ipSet = []

    def mAddSubnet(self, aIp):
        if aIp is not None:
            #Cast the object in case of String
            _ipSubnet = aIp
            if isinstance(aIp, six.string_types[0]):
                _ipSubnet = ebSubnetIp(aIp)
    
            #Get the current state of the Subset
            _conflicts = self.mIpInSet(_ipSubnet)
            if _conflicts == []:
                self.__ipSet.append(_ipSubnet)
            else:
                #Remove all the subnet duplications
                _conflicts = [x for x in _conflicts if x < 0]
                _conflicts = [-x for x in _conflicts]
                if len(_conflicts) > 0:
                    while len(_conflicts) > 0:
                        _pos = _conflicts.pop(0)-1
                        self.__ipSet.pop(_pos)
                        _conflicts = [x-1 for x in _conflicts]
                    self.__ipSet.append(_ipSubnet)

    """
    This method return a list
    a empty list is not conflict
    a list of i positive if aIp is a subset of x[abs(i)-1]
    a list of i negative if x[abs(i)-1] is a subset of aIp
    """
    def mIpInSet(self, aIp):
        #Cast to object in case of String
        _ipSubnet = aIp
        if isinstance(aIp, six.string_types[0]):
            _ipSubnet = ebSubnetIp(aIp)
        #If not element return []
        _conflicts = []
        if len(self.__ipSet) == 0:
            return _conflicts
        else:
            #Compare if there are a Subset
            c = 1
            for _ip in self.__ipSet:
                if _ipSubnet.mIsSubset(_ip):
                    _conflicts.append(c)
                if _ip.mIsSubset(_ipSubnet):
                    _conflicts.append(-1 * c)
                c+=1
            return _conflicts
        
    def mGetAllIPs(self):
        _ips = []
        for _ip in self.__ipSet:
            _ips += _ip.mGetAllIPs() 
        _ips.sort()
        return _ips

    def mAppendList(self, aList):
        if aList is not None and len(aList) != 0:
            for _ip in aList:
                self.mAddSubnet(_ip)

    def mGetSubnetList(self):
        _list = [x.mGetSubnet() for x in self.__ipSet] 
        _list.sort()
        return _list

    def mGetCIDRList(self):
        _list = [x.mGetCIDR() for x in self.__ipSet]
        _list.sort()
        return _list

#Check if given input is either in a valid hostname or ipv4/ipv6 address format.
def validateIpOrHostname(aHostOrIP):
    try:
        socket.inet_pton(socket.AF_INET, aHostOrIP)
        return True
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET6, aHostOrIP)
            return True
        except socket.error:
            #doing simple checks for hostnames, instead of rigorous checking in terms of length and starting character restrictions.
            if not re.match("^[0-9A-Za-z\-\.]+$", aHostOrIP):
                return False
            return True

def mPatchPrivNetworks(aCluCtrlObj):

    _obj = aCluCtrlObj
    for _, domu in _obj.mReturnDom0DomUPair(aForce=True):
        domu_conf = _obj.mGetMachines().mGetMachineConfig(domu)
        domu_conf_net = domu_conf.mGetMacNetworks()

        priv1_net = None
        priv2_net = None
        client_net = None
        clusterpriv1_net = None
        clusterpriv2_net = None

        for net_id in domu_conf_net:
            net_conf = _obj.mGetNetworks().mGetNetworkConfig(net_id)
            net_type = net_conf.mGetNetType()
            ebLogInfo('*** network name: %s' % (net_conf.mGetNetName()))

            if net_type == "client":
                client_net = net_conf

            elif net_type == "private":
                pkey_name = net_conf.mGetPkeyName()
                _int_name = net_conf.mGetInterfaceName()
                ebLogInfo('*** Interface name: %s' % (_int_name))

                if _obj.mIsKVM():
                    
                    _master = net_conf.mGetNetMaster()
                    if _int_name == f"stre0":
                        priv1_net = net_conf
                    elif _int_name == f"stre1":
                        priv2_net = net_conf
                    elif _int_name == f"clre0":
                        clusterpriv1_net = net_conf
                    elif _int_name == f"clre1":
                        clusterpriv2_net = net_conf
                else:
                    if pkey_name == "stib0":
                        priv1_net = net_conf
                    elif pkey_name == "stib1":
                        priv2_net = net_conf
                    elif _int_name == f"clib0":
                        clusterpriv1_net = net_conf
                    elif _int_name == f"clib1":
                        clusterpriv2_net = net_conf
        if priv1_net is None or priv2_net is None or clusterpriv1_net is None or clusterpriv2_net is None :
            ebLogWarn(f'*** !!!! Private interface not found in cluster xml ***')
            return

        client_hostname = client_net.mGetNetHostName()
        priv1_net.mSetNetHostName(client_hostname + "-stre0")
        priv2_net.mSetNetHostName(client_hostname + "-stre1")
        clusterpriv1_net.mSetNetHostName(client_hostname + "-clre0")
        clusterpriv2_net.mSetNetHostName(client_hostname + "-clre1")
        ebLogInfo(f"Patched xml with {priv1_net.mGetNetHostName()}, {priv2_net.mGetNetHostName()}, {clusterpriv1_net.mGetNetHostName()}, {clusterpriv2_net.mGetNetHostName()}")

def mChangeOpCtlAudit(aCluCtrlObj, tryReboot):
    '''
    for each of dom0,domU,cell check if opctl audit rules are present. if not add them to audit rules file
    reboot the nodes in case of production environment for the rules to start working
    reboot is done in parallel and this code gets hooked as part of postginid
    '''
    _grepCmd = "/bin/grep 'auid>=2100 -F auid<=2999' /etc/audit/rules.d/01-exadata_audit.rules"
    _auditText = "#### OPCTL - Start. DO NOT MODIFY #### \n-a exit,always -F arch=b64 -F auid>=2100 -F auid<=2999 -S execve\n\
    -a exit,always -F arch=b32 -F auid>=2100 -F auid<=2999 -S execve\n#### OPCTL - End. DO NOT MODIFY ####\n"

    # need to add opctl rules before last 3 lines
    _auditCmd = "/usr/bin/head -n -3 /etc/audit/rules.d/01-exadata_audit.rules > /tmp/auditd.temp.txt;/bin/echo $'" + _auditText + "' >> /tmp/auditd.temp.txt;" \
                + "/usr/bin/tail -3 /etc/audit/rules.d/01-exadata_audit.rules >> /tmp/auditd.temp.txt;" \
                + "/bin/mv /tmp/auditd.temp.txt /etc/audit/rules.d/01-exadata_audit.rules"

    # get the requisite nodes
    _dom0s, _, _cells, _ = aCluCtrlObj.mReturnAllClusterHosts()
    _allAuditNodes = []
    _allAuditNodes.extend(_dom0s)
    _allAuditNodes.extend(_cells)
    _nodesToReboot = []

    for _auditNode in _allAuditNodes:
        _node = exaBoxNode(get_gcontext(), aLocal=False)
        # check for the presence of audit rules for opctl
        _node.mConnect(aHost=_auditNode)
        _, _o, _e = _node.mExecuteCmd(_grepCmd)
        _out = _o.readlines()
        if _out:
            ebLogInfo("opctl audit config is already present in " + _auditNode)
            _node.mDisconnect()
            continue

        # add opctl audit rules
        ebLogInfo("adding opctl audit config in " + _auditNode)
        _node.mExecuteCmd(_auditCmd)
        _node.mDisconnect()

        # add dom0 as part of reboot, domU gets rebooted as part of dom0, it is unlikely that domU has audit rules
        # and dom0 does not. cells are always rebooted. before rebooting check for shared environment, if shared is
        # false reboot, if shared reboot only if no other VMs are running
        if _auditNode in _dom0s:
            if aCluCtrlObj.mCheckSharedEnvironment() is False:
                _nodesToReboot.extend(_auditNode)
            else:
                _vm = getHVInstance(_auditNode)
                _vm_count = _vm.getTotalVMs()
                # since current VM is in preVM step, it will not be added to the count
                if _vm_count == 0:
                    _nodesToReboot.extend(_auditNode)

    # cannot add cells to the reboot list as they could be part of already existing VMs.
    # to ensure this check if all dom0 are part of _nodesToReboot, if yes, it means no domUs are running and it is
    # safe to add cells to the reboot list
    _nodesToReboot.sort()
    _dom0s.sort()
    if _dom0s == _nodesToReboot:
        _nodesToReboot.extend(_cells)

    # reboot the nodes to rebooted in parallel only on production environment. dom0 reboot takes care of domU
    if tryReboot == True:
        _plist = ProcessManager()
        for _nodeToReboot in _nodesToReboot:
            ebLogInfo("Rebooting nodes %s." % _nodeToReboot)
            _p = ProcessStructure(aCluCtrlObj.mRebootNode, (_nodeToReboot,), _nodeToReboot)
            _p.mSetMaxExecutionTime(60 * 60)
            _p.mSetJoinTimeout(30)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()


class ebCluScheduleManager(object):

    def __init__(self, aExaBoxCluCtrl):
        self.__ebox = aExaBoxCluCtrl
        self.__data = {}

    def mGetData(self):
        return self.__data

    # Main worker method for Scheduler
    def mHandleRequest(self, aOptions):
        _options = aOptions
        _rc = 0

        _eBox = self.__ebox
        _data = self.mGetData()

        # Dump the JSON object
        def _mUpdateRequestData(aDataD):
            _data_d = aDataD
            _reqobj = _eBox.mGetRequestObj()
            if _reqobj is not None:
                _reqobj.mSetData(json.dumps(_data_d, sort_keys = True))
                _db = ebGetDefaultDB()
                _db.mUpdateRequest(_reqobj)
            elif aOptions.jsonmode:
                ebLogJson(json.dumps(_data_d, indent = 4, sort_keys = True))

        if (_options.sccmd is None):
            ebLogInfo("Invalid invocation or unsupported option")
            _rc = -1
            _data["Log"] = "Invalid invocation or unsupported option"
            _data["Status"] = "Fail"
            _mUpdateRequestData(_data)
            return _rc

        # Invoke right worker method
        if (_options.sccmd == "list"):
            ebLogInfo("Running Step: Read Scheduled Job List")
            _data["Command"] = "list"
            self.mListScheduledJobs(_options)

        _mUpdateRequestData(_data)
        return _rc
    # end

    def mListScheduledJobs(self, aOptions=None):
        _db = ebGetDefaultDB()
        _rc = _db.mGetSchedule()

        _data = self.mGetData()
        _data["Status"] = "Pass"
        _data["uuid"] = {}
        _data["ErrorCode"] = "0"

        for _iter in range(0, len(_rc)):
            _uuid = _rc[_iter][0]
            _mode = _rc[_iter][2]
            _operation = _rc[_iter][3]
            _event = _rc[_iter][4]
            _timer_type = _rc[_iter][5]
            _timestamp = _rc[_iter][6]
            _interval = _rc[_iter][7]
            _repeat_count = _rc[_iter][8]
            _last_repeat_count = _rc[_iter][9]
            _monitor_uuid = _rc[_iter][10]
            _monitor_worker_jobs = _rc[_iter][11]
            _status = _rc[_iter][12]

            _data["uuid"][_uuid] = {  "mode" : _mode, "operation": _operation, 
                                            "event": _event, "timer_type": _timer_type,
                                            "timestamp": _timestamp,  "interval": _interval, 
                                            "repeat_count": _repeat_count, "last_repeat_count": _last_repeat_count,
                                            "monitor_uuid": _monitor_uuid, "monitor_worker_jobs" : _monitor_worker_jobs,
                                            "status": _status 
                                        }
        return 0

class ebCluCellValidate(object):

        def __init__(self, aExaBoxCluCtrl, aOptions):
            self.__cluctrl = aExaBoxCluCtrl
            self.__ociexacc = self.__cluctrl.mCheckConfigOption('ociexacc','True')

        def mValidateCell(self,aOptions):
            _data_d = {}
            _errString = None
            _rc = -1
            _valid_cell_list = []

            def _mUpdateRequestData(rc, aData, err):
                """
                Updates request object with the response payload
                """
                _reqobj = self.__cluctrl.mGetRequestObj()
                _response = {}
                _response["success"] = "True" if (rc == 0) else "False"
                _response["error"] = err
                _response["output"] = aData
                if _reqobj is not None:
                    _db = ebGetDefaultDB()
                    _reqobj.mSetData(json.dumps(_response, sort_keys = True))
                    _db.mUpdateRequest(_reqobj)
                elif aOptions.jsonmode:
                    ebLogJson(json.dumps(_response, indent=4, sort_keys = True))

            if aOptions is not None and aOptions.jsonconf is not None and \
               'cell_list' in list(aOptions.jsonconf.keys()):
                _valid_cell_list = aOptions.jsonconf.get('cell_list')
            else:
                _rc = 0
                _mUpdateRequestData(_rc,_data_d,'invalid params')
                return _rc
            _result = []
            
            if _valid_cell_list and self.__ociexacc:
                for _target in _valid_cell_list:
                    _res = {}
                    _res = self.mValidateCellStat(aOptions, _target)
                    _result.append(_res)

            _data_d['output']= _result
            _rc = 0
            ebLogInfo("*** mValidateCell is : %s" % (json.dumps(_data_d)))
            _mUpdateRequestData(_rc,_data_d,_errString)
            return _rc

        def mValidateCellStat(self, aOptions, aCell):
            _cell = aCell
            _options = aOptions
            _stat_dict = {}
            _stat_dict['server'] = _cell
            _stat_dict['status'] = None

            if not self.__cluctrl.mPingHost(_cell):
                ebLogInfo("Failed to ping %s" %(_cell))
                _o = "Failed to ping " + _cell
                _e = '0x0800'
                _stat_dict['status'] = _o
                _stat_dict['error_code'] = _e
                return _stat_dict

            # Connect to the cell
            _node = exaBoxNode(get_gcontext())
            try:
                _node.mConnect(aHost=_cell)
            except:
                ebLogWarn('*** Failed to connect to: %s' %(_cell))
                _o = "Failed to connect to " + _cell
                _e = '0x0801'
                _stat_dict['status'] = _o
                _stat_dict['error_code'] = _e
                return _stat_dict

            ebLogInfo('*** Getting Cell Exadata model')
            # Sample output: [root@scaqak02celadm07 ~]# dmidecode | grep Exadata | tail -1
            # Exadata X8M-2 
            # Sample output: [root@scaqan02celadm02 ~]# dmidecode | grep Exadata | tail -1
            # Exadata X8M-2-CC

            _cmd = 'dmidecode | grep Exadata | tail -1'
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            _out = _o.readlines()[0]
            if _out:
                _model_name= str(_out).strip().split(' ')
                _model_name[1] = re.sub("[^a-zA-Z0-9-]","", _model_name[1])
                ebLogInfo("*** The model name is %s"%(_model_name))
                _model_split = _model_name[1].split('-')
                if len(_model_split)>=2:
                    _stat_dict['model'] = f"{_model_split[0]}-{_model_split[1]}"   # remove anything after second '-' from the string if it comes in the response
                else:
                    _stat_dict['model'] = _model_name[1]
            else:                                                      # if dmidecode command returns nothing, we can fall back to the existing way of getting model detail
                _stat_dict['model'] = self.__cluctrl.mGetNodeModel(aHostName=_cell)

            ebLogInfo(f"*** mValidateCellStat: Model name is {_stat_dict['model']}") 
            if _stat_dict['model'] in ['X10M','X10M-CC']: # dmidecode output for X10M is missing the trailing -2, we want to add it to keep it consistent
                _stat_dict['model'] = 'X10M-2'
            elif _stat_dict['model'] in ['X11M','X11M-CC']:
                _stat_dict['model'] = 'X11M'
            ebLogInfo("*** The final model name is :%s"%(_stat_dict['model']))
            _cellcli_alerthistory_options = mGetAlertHistoryOptions(self.__cluctrl, _cell)
            #print cell alerthistory
            _i, _o, _e = _node.mExecuteCmd(f"/opt/oracle/cell/cellsrv/bin/cellcli {_cellcli_alerthistory_options} -e 'list alerthistory where endTime=null AND alertType=stateful'")
            for _line in _o.readlines():
                # Ignore AIDE warning in non-dev env
                # e.g.
                #   <date>    warning         "Advanced Intrusion Detection Environment (AIDE) detected potential changes to software on this system. The changes are in /var/log/aide/aide.log "
                # Set exact filter string to exclude only that warning
                if 'Advanced Intrusion Detection Environment (AIDE) detected potential changes to software on this system' in _line:
                    continue
                _err_msg = "Cellcli alert(Unresolved): Host:{0} - {1}".format(_cell, _line.strip())
                ebLogWarn(_err_msg)
                _stat_dict['status'] = _err_msg
                _stat_dict['error_code'] = '0x0848'

            _i, _o, _e = _node.mExecuteCmd('/opt/oracle/cell/cellsrv/bin/cellcli -e list cell detail')
            for _line in _o.read().strip().split('\n'):
                try:
                    _slice = _line.split(':')
                    if len(_slice) < 2:
                        #no parse for multiline
                        continue
                    _stat_dict[_slice[0].strip()] = _slice[1].strip()
                except:
                    ebLogWarn('\'cellcli list cell detail\' failed: ' + _line)

            if 'cellsrvStatus' not in _stat_dict:
                _err_msg = "Cellsrv no response. {0}: failed to query Cellcli alert".format(_cell)
                ebLogError(_err_msg)
                _stat_dict['status'] = _err_msg
                _stat_dict['error_code'] = '0x849'
                return _stat_dict

            for _status in ['cellsrv', 'ms', 'rs']:
                _cur_status_key = _status + 'Status'
                _cur_status_val = _stat_dict.get(_cur_status_key)
                if _cur_status_val != 'running':
                    _err_msg = "Cell status: {0}: {1} is {2}".format(_cell, _cur_status_key, _cur_status_val)
                    ebLogWarn(_err_msg)
                    _stat_dict['status'] = _err_msg
                    _stat_dict['error_code'] = '0x0826'

                else:
                    _msg = '*** {0} : {1} is {2}'.format(_cell, _cur_status_key, _cur_status_val)
                    ebLogInfo(_msg)
                    _stat_dict['status'] = _msg
                    _stat_dict['error_code'] = '0x00'

            # if cell server stat was not goot in the check above, no need to check name
            if 'name' not in _stat_dict:
                return _stat_dict


            #check physical disk status
            _cellcli_cmd = "list physicaldisk attributes name,status " +\
                    "where diskType like '.*Disk' and status!=normal"
            _i, _o, _e = _node.mExecuteCmd('/opt/oracle/cell/cellsrv/bin/cellcli -e "%s"' % _cellcli_cmd)
            _abnormal_disks = [_line.split(None, 1) for _line in _o.readlines()]
            if _abnormal_disks:
                for _name, _status in _abnormal_disks:
                    _err_msg = "Cell disk error {0}: Status of physical disk {1} is {2}".format(_cell, _name, _status)
                    ebLogWarn(_err_msg)
                    _stat_dict['status'] = _err_msg
                    _stat_dict['error_code'] = '0x0850'

            else:
                _msg = "*** No abnormal physical disk in {0}".format(_cell)
                ebLogInfo(_msg)
                _stat_dict['status'] = _msg
                _stat_dict['error_code'] = '0x00'

            
            _cellcli_cmd = "list celldisk attributes name,size where disktype=HardDisk"
            _i, _o, _e = _node.mExecuteCmd('/opt/oracle/cell/cellsrv/bin/cellcli -e "%s"' % _cellcli_cmd)
            _output = _o.readlines()
            if not _output:
                _cellcli_cmd1 = "drop celldisk all"
                _cellcli_cmd2 = "create celldisk all"
                _i, _o, _e = _node.mExecuteCmd('/opt/oracle/cell/cellsrv/bin/cellcli -e "%s"' % _cellcli_cmd1)
                _i, _o, _e = _node.mExecuteCmd('/opt/oracle/cell/cellsrv/bin/cellcli -e "%s"' % _cellcli_cmd2)
                
            return _stat_dict

        def mValidateAuthConfig(self, aNodeList):
            _cmdstr = "/bin/rpm -qa | /bin/grep authconfig"
            for _domU in aNodeList:
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_domU)
                _i, _o, _e = _node.mExecuteCmd(_cmdstr)
                _out = _o.readlines()
                _node.mDisconnect()
                if _out:
                   return 'FAIL'
            return 'PASS'
        
        def mValidateAllNodeSSHConnect(self, aNodeList):
            for _domU in aNodeList:
                _node = exaBoxNode(get_gcontext())
                try:
                    _node.mConnect(aHost=_domU)
                except:
                    ebLogWarn('*** Failed to connect to: %s' %(_domU)) 
                    return 'FAIL'
            return 'PASS'
        
        def mZDLRAChecks(self):
            if ebCluCmdCheckOptions(self.__cluctrl.mGetCmd(), ['skip_zdlra_detection']):
                ebLogInfo(f"Skipping Zdlra detection for {self.__cluctrl.mGetCmd()} command!")
            else:
                if not self.__cluctrl.mIsExaScale() and not self.__cluctrl.mIsXS():
                    if not self.__cluctrl.IsZdlraProv():  
                        zdlra_obj = self.__cluctrl.mGetZDLRA()  
                        if zdlra_obj is not None:
                            zdlra_check_result = zdlra_obj.mCheckZdlraInEnv()
                            self.__cluctrl.mSetZdlraProv(zdlra_check_result) 
                            if self.__cluctrl.IsZdlraProv(): 
                                self.__cluctrl.mSetZdlraHThread(False)
                        else:
                            ebLogError(f" ZDLRA object is not initialized in exaBoxCluCtrl.")
            return self.__cluctrl.IsZdlraProv()  

        def mMaxStartupChecks(self, aOptions):
            #Check if MaxStartups set to 100 in cell nodes. Else patch cells SSHD
            if self.__cluctrl.mIsClusterLessXML():
                ebLogInfo(f"Skipping mPatchCellsSSHDConfig for special command : {aOptions.clusterctrl}")
            else:
                # Condition to avoid patching cells SSHD if command has no_check_sw_cell
                if ebCluCmdCheckOptions(self.__cluctrl.mGetCmd(), ['no_check_sw_cell']):
                    ebLogInfo(f'*** Skip patching cells SSHD for {self.__cluctrl.__cmd} command')
                else:
                    self.__cluctrl.mPatchCellsSSHDConfig()
                
        def mCellTasks(self, aOptions):
            self.__cluctrl.mSetCellInfo({})
            _steplist = ["ESTP_PREVM_CHECKS", "ESTP_PREVM_SETUP"]
            _cell_info = self.__cluctrl.mGetCellInfo()
            def _perform_checks():
                try:
                    _cell_info['zdlra_enabled'] = self.mZDLRAChecks()
                    _cell_info['exadata_model'] = self.__cluctrl.mGetExadataCellModel()
                    self.mMaxStartupChecks(aOptions)
                    self.__cluctrl.mSetCellInfo(_cell_info)
                except Exception as e:
                    ebLogError(f"mCellTasks failed with Exception: {str(e)}")
            
            if 'steplist' in aOptions and aOptions.steplist is not None and aOptions.steplist in _steplist:
                with self.__cluctrl.remote_lock():
                    _perform_checks()
            else:
                _perform_checks()
            _cell_info = self.__cluctrl.mGetCellInfo()
            ebLogTrace(f"ZDLRA Enabled : {_cell_info.get('zdlra_enabled','None')} ")
            ebLogTrace(f"Exadata Model : {_cell_info.get('exadata_model','None')} ")

class ebCluPostComputeValidate(object):

        def __init__(self, aExaBoxCluCtrl, aOptions):
            self.__cluctrl = aExaBoxCluCtrl
            self.__ociexacc = self.__cluctrl.mCheckConfigOption('ociexacc','True')

        def mPostComputeValidate(self,aOptions):
            _rc = -1
            _validate_dom0_list = []
            _result = []

            def _mUpdateRequestData(rc, aData):
                """
                Updates request object with the response payload
                """
                _reqobj = self.__cluctrl.mGetRequestObj()
                _response = {}
                _response["overallStatus"] = "True" if (rc == 0) else "False"
                _response["ValidationStatus"] = aData
                if _reqobj is not None:
                    _db = ebGetDefaultDB()
                    _reqobj.mSetData(json.dumps(_response, sort_keys = True))
                    _db.mUpdateRequest(_reqobj)
                elif aOptions.jsonmode:
                    ebLogJson(json.dumps(_response, indent=4, sort_keys = True))

            if aOptions is not None and aOptions.jsonconf is not None and \
               'newdom0_list' in list(aOptions.jsonconf.keys()):
                _validate_dom0_list = aOptions.jsonconf.get('newdom0_list')
                _rc = 0
            else:
                _mUpdateRequestData(_rc, _result)
                return _rc

            for _dom0 in _validate_dom0_list:
                _data = {}
                _data["node_name"] = _dom0
                _data["testsPassed"] = []
                _data["testsFailed"] = []
                _data["nodeStatus"] =  "PASS"
                _data["server"] = _dom0
                _data["model"] = self.mGetModelName(aOptions,_dom0)
                _data["TotOnlineMem"] = self.mGetTotalOnlineMemory(aOptions,_dom0)
                _result.append(_data)
            # returning success for the time being as its a dummy implementation
            _mUpdateRequestData(_rc,_result)
            return _rc

        def mGetModelName(self,aOptions,aDom0):
            ebLogInfo('*** Getting Exadata model')
            _model_name= ''
            # Sample output: [root@scaqak02dv07 ~]# dmidecode | grep Exadata | tail -1
            # Exadata X8M-2
            # Sample output: [root@scaqan02dv02 ~]# dmidecode | grep Exadata | tail -1
            # Exadata X8M-2-CC
            _node = exaBoxNode(get_gcontext())
            _cmd = 'dmidecode | grep Exadata | tail -1'
            try:
                _node.mConnect(aHost=aDom0)
                _i, _o, _e = _node.mExecuteCmd(_cmd)
                _out = _o.readlines()[0]
                if _out:
                    _model_name_list = str(_out).strip().split(' ')
                    _model_name_list[1] = re.sub("[^a-zA-Z0-9-]","", _model_name_list[1])
                    ebLogInfo("*** The model name is %s"%(_model_name_list))
                    _model_split = _model_name_list[1].split('-')
                    if len(_model_split)>=2:
                        _model_name = f"{_model_split[0]}-{_model_split[1]}"   # remove anything after second '-' from the string if it comes in the response
                    else:
                        _model_name = _model_name_list[1]  # use the string which comes in the response
                else:                                                      # if dmidecode command returns nothing, we can fall back to the existing way of getting model detail
                    _model_name = self.__cluctrl.mGetNodeModel(aHostName=aDom0)

                ebLogInfo(f"*** mGetModelName: Model name is {_model_name}")

                if _model_name in ['X10M','X10M-CC']: # dmidecode output for X10M is missing the trailing -2, we want to add it to keep it consistent
                    _model_name = 'X10M-2'
                elif _model_name in ['X11M','X11M-CC']:
                    _model_name = 'X11M'

                ebLogInfo("*** The final model name is :%s"%(_model_name))
            except Exception as e:
                ebLogWarn("Exception caught while fetching Model Name for server : %s error details : %s" % (aDom0,str(e)))
            finally:
                _node.mDisconnect()
            return _model_name            

        def mGetTotalOnlineMemory(self,aOptions,aDom0):
            ebLogInfo('*** Getting Total online memory')
            _totalOnlineMem = ''
            _node = exaBoxNode(get_gcontext())
            _cmd = "/usr/bin/lsmem |/usr/bin/grep 'Total online memory' |  /usr/bin/awk '{ print $4 }'" 
            try:
                _node.mConnect(aHost=aDom0)
                _i, _o, _e = _node.mExecuteCmd(_cmd)
                _out = _o.readlines()[0]
            
                if _out:
                    ebLogInfo("*** The Total online memory is:" + _out)
                    _totalOnlineMem = _out.strip()
                else:
                    ebLogWarn('*** Failed Getting Total online memory value')
            except Exception as e:
                ebLogWarn("Exception caught while fetching Total online memory value for server : %s error details : %s" % (aDom0,str(e)))
            finally:
                _node.mDisconnect()
            return _totalOnlineMem

gPreCheckFunctionMap = {
    "fan_test"                 :   "mRunFanTest",
    "power_test"               :   "mRunPowerTest",
    "temperature_test"         :   "mRunTemperatureTest",
    "hypervisor_test"          :   "mRunHypervisorTest",
    "root_storage_test"        :   "mRunRootStorageTest",
    "exavmimages_storage_test" :   "mRunExavmImagesStorageTest",
    "memory_test"              :   "mRunMemoryTest",
    "ilom_consistency_test"    :   "mRunIlomConsistencyTest",
    "hw_test"                  :   "mRunHWTest",
    "lun_test"                 :   "mRunLunTest",
    "physicaldisk_test"        :   "mRunPhysicalDiskTest",
    "griddisk_test"            :   "mRunGridDiskTest",
    "celldisk_test"            :   "mRunCellDiskTest",
    "flashcache_test"          :   "mRunFlashCacheTest",
    "pmemcache_test"           :   "mRunPmemCacheTest",
    "ip_match_test"            :   "mRunIPConflictTest",
    "env_test"                 :   "mRunHWTest",
    "hw_alerts"                :   "mRunListAlertHistory",
    "computephysicaldisk_test" :   "mRunComputePhysicalDiskTest"
}

class ebCluDom0SanityTests:
    def __init__(self, aCluPreCheck, aNodeInfo=None, aNodeType=None, aStep="", aOsType=None, aMultivm=False, aOperationType=None, aPrecheckConfig=None, aModelSubType=None):
        self.__precheck = aCluPreCheck
        self.__nodeInfo = aNodeInfo
        self.__nodeType = aNodeType
        self.__step = aStep
        self.__precheckConfig = aPrecheckConfig

        self.__cluctrl = self.__precheck.mGetEbox()
        self.__verbose = self.__cluctrl.mGetVerbose()

        self.__res = {}
        self.__osType = ""
        self.__modelsubType = ""
        self.__multiVM = False
        self.__operationType = ""
        self.__error_list = []
        self.__precheck_list = []

        for _key, _value in self.__precheckConfig.items():
            if _value == "True":
                if _key not in ["bridge_test", "stale_domU_test", "image_info_test"]:
                    self.__precheck_list.append(_key)

        if self.__step == "ESTP_PREVM_CHECKS":
            self.__hostname, self.__domain = aNodeInfo.split('.', 1)
            self.__res.update( { "hostname" : self.__hostname, "domainname" : self.__domain, "hw_type" : "COMPUTE", 'error_list' : []} )
            self.__host = self.__hostname +  '.' + self.__domain
            self.__alert_log = "ESTP_PREVM_CHECKS"
        elif self.__step == "ELASTIC_SHAPES_VALIDATION":
            self.__osType = aOsType
            self.__modelsubType: str = aModelSubType
            self.__multiVM = aMultivm
            self.__operationType = aOperationType
            self.__nodeInfo.update( {'error_list' : []} )
            self.__nodeInfo.update( {'node_type' : self.__nodeType} )
            self.__host = self.__nodeInfo['hostname'] + '.' + self.__nodeInfo['domainname']
            self.preprov = self.__nodeInfo['preprov']

            self.__alert_log = 'ELASTIC_SHAPES_VALIDATION'

            self.__precheck_list.remove("memory_test")
            self.__precheck_list.remove("exavmimages_storage_test")

        self.__node = exaBoxNode(get_gcontext())

    def run(self, aHwChecksTable={}):
        self.mPingTest()
        _status = self.__res.get("ping_test", "")
        if _status == "abnormal":
            if self.__step == "ELASTIC_SHAPES_VALIDATION":
                if self.__error_list:
                    self.__nodeInfo.update( {'error_list' : self.__error_list } )
                self.__res.update( {'node_info' : [self.__nodeInfo]} )
                # Fill multiprocess dictionary
                aHwChecksTable[self.__host] = self.__res
                # Log context for exacloud thread
                ebLogError(f"*** ERROR: host={self.__host}, step={self.__step}, result={json.dumps(self.__res)}")
                return

            if self.__step == "ESTP_PREVM_CHECKS":
                if self.__error_list:
                    self.__res.update({'error_list': self.__error_list})

            # Fill multiprocess dictionary
            _proxy_list = aHwChecksTable.get("nodes", [])
            _proxy_list.append(self.__res)
            aHwChecksTable["nodes"] = _proxy_list
            return

        self.mRunSshTest()
        _status = self.__res.get("ssh_test", "")
        if _status == "normal":
            self.__node.mConnect(aHost=self.__host)

            for _name in self.__precheck_list:
                _func_name = gPreCheckFunctionMap[_name]
                try:
                    getattr(self, _func_name)()
                except Exception as e:
                    self.__res.update({_name: 'failed'})
                    self.__error_list.append(get_hw_validate_error(90000, _name, self.__host))
                    ebLogError('*** Exception in testing  %s[%s]' % (_name, e,))
                    ebLogError(traceback.format_exc())

            if self.__step == "ELASTIC_SHAPES_VALIDATION":
                if ((self.__nodeType in ["elastic-servers"] and self.__operationType in ["ADD_COMPUTE", "ADD_CELL"]) or 
                        (self.__nodeType in ["quarter-rack-servers", "elastic-servers"] and self.__operationType in ["CEI_RESERVE"]) ):

                    _shared_env = self.__cluctrl.mGetSharedEnv()
                    if self.preprov ==  False and (self.__multiVM == False or _shared_env == False):
                        _bridge_test = self.mPrecheckConfigOption("bridge_test", "True")
                        if _bridge_test:
                            self.mRunBridgeTest()
                        _stale_domU_test = self.mPrecheckConfigOption("stale_domU_test", "True")
                        if _stale_domU_test:
                            self.mRunStaleDomUTest()

                self.mRun2TMemoryTest()

                if self.__osType:
                    _image_info_test = self.mPrecheckConfigOption("image_info_test", "True")
                    if _image_info_test:
                        self.mRunImageInfoTest(self.__osType)

            self.__node.mDisconnect()
        else:
            ebLogError("*** {0}: dom0 {1} is not connectable by SSH".format(self.__alert_log, self.__host))

        if self.__step == "ELASTIC_SHAPES_VALIDATION":
            if self.__error_list:
                self.__nodeInfo.update( {'error_list' : self.__error_list } )
            self.__res.update( {'node_info' : [self.__nodeInfo]} )
            # Fill multiprocess dictionary
            aHwChecksTable[self.__host] = self.__res
            return

        if self.__step == "ESTP_PREVM_CHECKS":
            if self.__error_list:
                self.__res.update({'error_list': self.__error_list})

        # Fill multiprocess dictionary
        _proxy_list = aHwChecksTable.get("nodes", [])
        _proxy_list.append(self.__res)
        aHwChecksTable["nodes"] = _proxy_list
        return

    def mPrecheckConfigOption(self, aOption, aValue=None):

        if aValue is None:
            if aOption in list(self.__precheckConfig.keys()):
                return self.__precheckConfig[ aOption ]
            else:
                return None

        if aOption in list(self.__precheckConfig.keys()):
            if self.__precheckConfig[ aOption ] == aValue:
                return True
            else:
                return False
        else:
            return False

    def mRemoteExecute(self, aCmd):
        _cmd_str = aCmd
        _i, _o, _e = self.__node.mExecuteCmd(_cmd_str)
        _out = [_line.strip() for _line in _o.readlines()]
        return _out

    def mPingTest(self):
        if not self.__cluctrl.mPingHost(self.__host):
            ebLogError('*** {0}: Host {1} is not pingable.'.format(self.__alert_log, self.__host))
            self.__res.update( {'ping_test' : 'abnormal'} )
            self.__error_list.append(get_hw_validate_error(90001, "ping_test", self.__host))
        else:
            self.__res.update( {'ping_test' : 'normal'} )
            ebLogInfo("*** {0}: PING_TEST on dom0:{1} is normal".format(self.__alert_log, self.__host))

    def mRunSshTest(self):
        if self.__cluctrl.mIsOciEXACC():
            _key_only = False
        else:
            _key_only = True

        if self.__node.mIsConnectable(aHost=self.__host, aKeyOnly=_key_only):
            self.__res.update( {'ssh_test' : 'normal'} )
            ebLogInfo("*** {0}: SSH_TEST on dom0:{1} is normal".format(self.__alert_log, self.__host))
        else:
            ebLogError("*** {0}: SSH_TEST on dom0:{1} is abnormal".format(self.__alert_log, self.__host))
            self.__res.update( {'ssh_test' : 'abnormal'} )
            self.__error_list.append(get_hw_validate_error(90002, "ssh_test", self.__host))

    def mRunHypervisorTest(self):
        if self.__cluctrl.mIsKVM():
            self.__cluctrl.mEnableDom0Service('libvirtd', self.__node, self.__host)
        _hv = getHVInstance(self.__host)
        _status = _hv.mGetHVStatus()
        if _status == "running":
            self.__res.update( {'hypervisor' : 'running'} )
            ebLogInfo("*** {0}: HYPERVISOR {1} on dom0:{2}".format(self.__alert_log, _status, self.__host))
        else:
            self.__res.update( {'hypervisor' : 'stopped'} )
            ebLogError("*** {0}: HYPERVISOR {1} on dom0:{2}".format(self.__alert_log, _status, self.__host))
            self.__error_list.append(get_hw_validate_error(90003, "hypervisor", self.__host))
    
    def mRunFanTest(self):
        _cmd_str = "ipmitool sdr type fan  |  awk '{ print $5 }'"
        _output = self.mRemoteExecute(_cmd_str)
        if _output or len(_output):
            _ret =  all(ele == 'ok' for ele in _output)
            _value = 'normal' if _ret else 'abnormal'
            if _value == 'abnormal':
                ebLogError(f"*** {self.__alert_log}: FAN status on dom0:{self.__host} is abnormal")
                self.__res.update( {'fan' : _value} )
                self.__error_list.append(get_hw_validate_error(90004, "fan", self.__host))
            else:
                ebLogInfo(f"*** {self.__alert_log}: FAN status on dom0:{self.__host} is normal")
                self.__res.update( {'fan' : _value} )

    def mRunPowerTest(self):
        _cmd_str = "ipmitool chassis status | grep 'System Power'"
        _output = self.mRemoteExecute(_cmd_str)
        if _output or len(_output):
            _ret = _output[0].split(':')[1].strip()
            _value = 'normal' if _ret == 'on' else 'abnormal'
            if _value == 'abnormal':
                self.__res.update( {'power' : _value} )
                ebLogError(f"*** {self.__alert_log}: CHASSIS status on dom0:{self.__host} is abnormal")
                self.__error_list.append(get_hw_validate_error(90005, "power", self.__host))
            else:
                ebLogInfo(f"*** {self.__alert_log}: CHASSIS status on dom0:{self.__host} is normal")
                self.__res.update( {'power' : _value} )
    
    def mRunTemperatureTest(self):
        _cmd_str = "/opt/oracle.cellos/exadata.img.hw --get model"
        _model, *_ = self.mRemoteExecute(_cmd_str)
        _cmd_str = "ipmitool sdr type temperature  |  awk '{ print $1, $5 }'"
        _output = [ sensor.split() for sensor in self.mRemoteExecute(_cmd_str) ]
        _sensors = [
            state for name, state in _output
            # E4-c2 X9M envs lack of these PS2 and PS3 sensors, so we'll just ignore them.
            # TBD check the _model name for x10 and see if it supports these sensors.
            if not ((_model.endswith('E4-2c') or _model.endswith('E5-2L') or _model.endswith('E6-2L')) and (name.startswith('PS2') or name.startswith('PS3')))
        ]
        if _output or len(_output):
            if any(ele == 'ns' for ele in _sensors):
                ebLogWarn(f"*** {self.__alert_log}: There are missing temperature sensors in Dom0: {self.__host}")
            _ret =  all(ele == 'ok' for ele in _sensors)
            _value = 'normal' if _ret else 'abnormal'
            if _value == 'normal':
                ebLogInfo(f"*** {self.__alert_log}: TEMPERATURE on dom0:{self.__host} is normal")
            else:
                ebLogError(f"*** {self.__alert_log}: TEMPERATURE on dom0:{self.__host} is abnormal")
                ebLogError(f"*** {self.__alert_log}:TEMPERATURE test on dom0 model {_model} produced result: {_output}")

            _ignore_error = get_gcontext().mCheckConfigOption("exacloud_prevm_checks").get("ignore_temperature_errors")
            if _value == 'normal' or _ignore_error == 'True':
                self.__res.update( {'temperature' : 'normal'} )
            else:
                self.__res.update( {'temperature' : _value} )
                self.__error_list.append(get_hw_validate_error(90006, "temperature", self.__host))

    def mRunRootStorageTest(self):
        _partition = '/'
        _threshold_root_space = '95'
        if not self.__precheck.mCheckUsedSpace(self.__host,  _partition, _threshold_root_space):
            ebLogError("*** space used in root partition is more than threshold(%s%%) for host - %s" %(_threshold_root_space, self.__host))
            ebLogError("*** {0}: STORAGE_CHECK on / partition for dom0:{1} is abnormal".format(self.__alert_log, self.__host))
            self.__res.update( {'root_storage_test' : 'abnormal'} )
            self.__error_list.append(get_hw_validate_error(90007, "root_storage_test", self.__host))
        else:
            if self.__verbose:
                ebLogVerbose('*** %s partition space used is less than threshold value(%s%%) for host - %s' %(_partition, _threshold_root_space, self.__host))
            ebLogInfo("*** {0}: STORAGE_CHECK on / partition is normal on dom0:{1}".format(self.__alert_log, self.__host))
            self.__res.update( {'root_storage_test' : 'normal'} )

    def mRunExavmImagesStorageTest(self):

        if self.__cluctrl.mIsExaScale():
            return

        # store check on /EXAVMIMAGES
        if not self.__cluctrl.mCheckConfigOption('skip_storage_checks','True'):
            # Fetch u02 disk size
            _disk_u02_size = self.__cluctrl.mGetu02Size()

            # Images take up about 40G. Buffer of 60 to ensure we don't empty storage
            if self.__cluctrl.mCheckConfigOption('disk_images_size') is not None:
                _disk_images_size = self.__cluctrl.mCheckConfigOption('disk_images_size')
            else:
                _disk_images_size = '100G'

            _cmd_str = "df -h -B G |grep EXAVMIMAGES"
            _i, _o, _e = self.__node.mExecuteCmd(_cmd_str)
            _fspace = _o.readlines()[0].strip()
            _fspace = " ".join(_fspace.split())
            _fspace = _fspace.split(" ")[-3].lstrip().rstrip()[:-1]

            if self.__verbose:
                ebLogVerbose('*** Free space required for images: %s' %(_disk_images_size))
                ebLogVerbose('*** Free space required for u02 partition: %s' %(_disk_u02_size))
                ebLogVerbose('*** Free space available on /EXAVMIMAGES partition on %s is %sG' %(self.__host, _fspace))

            # At least twice the amount of required u02 size should be available
            if int(_fspace) < (int(_disk_images_size[:-1]) + int(_disk_u02_size[:-1])):
                self.__res.update( {'exavmimages_storage_check' : 'abnormal'} )
                ebLogError('*** %s: Free space available on /EXAVMIMAGES partition on dom0 %s is insufficient' %(self.__alert_log, self.__host))
                self.__error_list.append(get_hw_validate_error(90008, "exavmimages_storage_check", self.__host))
            else:
                self.__res.update( {'storage_check_exavmimages' : 'normal'} )
                ebLogInfo("*** {0}: STORAGE_CHECK on /EXAVMIMAGES is normal on dom0:{1}".format(self.__alert_log, self.__host))

    def mParseDBNodeResult(self, aOutput):
        _output = aOutput
        _error_details = {}
        for _line in _output:
            _disk_split = _line.split()
            if _disk_split:
                _error = ' '.join( str(_ret) for _ret in _disk_split[1:] )
                ebLogError(_error)
                _error_details.update( { _disk_split[0] : _error } )
        return _error_details

    #Dom0 physical disk check
    def mRunComputePhysicalDiskTest(self):
        _status = "normal"
        _cmd_str = (f"dbmcli -e list physicaldisk attributes name,status  where status!=\\'normal\\';")
        _output = self.mRemoteExecute(_cmd_str)
        if _output or len(_output):
            for _line in _output:
                if "predictive" in _line.lower() or "failed" in _line.lower() or "not present" in _line.lower():
                    _status = "abnormal"
            if _status == "normal":
                self.__res.update( {'physicaldisk' : 'normal'} )
                ebLogInfo("*** {0}: PHYSICALDISK status on compute:{1} is normal".format(self.__alert_log, self.__host))
            else:
                ebLogError("*** {0}: PHYSICALDISK status on compute:{1} is abnormal".format(self.__alert_log, self.__host))
                _err = self.mParseDBNodeResult(_output)
                self.__res.update( {'physicaldisk' : 'abnormal'} )
                self.__error_list.append(get_hw_validate_error(90009, "physicaldisk", self.__host, _err))
        else:
            self.__res.update( {'physicaldisk' : 'normal'} )
            ebLogInfo("*** {0}: PHYSICALDISK status on compute:{1} is normal".format(self.__alert_log, self.__host))

    def mRunMemoryTest(self):
        if not self.__precheck.mCheckDom0Mem(self.__host):
            self.__res.update( {'memory_check' : 'abnormal'} )
            self.__error_list.append(get_hw_validate_error(90010, "memory_check", self.__host))
        else:
            self.__res.update( {'memory_check' : 'normal'} )
            ebLogInfo("*** {0}: MEMORY_CHECK is normal on dom0:{1}".format(self.__alert_log, self.__host))
    
    def mRunIlomConsistencyTest(self):
        #Dom0 Network Validation
        if not self.__node.mFileExists('/opt/oracle.cellos/cell.conf'):
            ebLogError("*** {0}: cell.conf not found in /opt/oracle.cellos on dom0:{1}".format(self.__alert_log, self.__host))
            ebLogInfo("*** {0}: ILOM_ADMIN_CONSISTENCY is abnormal on dom0:{1}".format(self.__alert_log, self.__host))
            self.__res.update( {'ilom_admin_consistency' : 'abnormal'} )
            self.__error_list.append(get_hw_validate_error(90011, "ilom_admin_consistency", self.__host))
        else:
            _check_passed = False
            _sub_str = 'consistency check passed'
            _cmd_str = "/usr/local/bin/ipconf -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime"
            _output = self.mRemoteExecute(_cmd_str)
            if _output or len(_output):
                for _line in _output:
                    if _sub_str in _line.lower():
                        self.__res.update( {'ilom_admin_consistency' : 'normal'} )
                        ebLogInfo("*** {0}: ILOM_ADMIN_CONSISTENCY is normal on dom0:{1}".format(self.__alert_log, self.__host))
                        _check_passed = True
                        break

            if not _check_passed:
                self.__res.update( {'ilom_admin_consistency' : 'abnormal'} )
                ebLogInfo("*** {0}: ILOM_ADMIN_CONSISTENCY is abnormal on dom0:{1}".format(self.__alert_log, self.__host))
                self.__error_list.append(get_hw_validate_error(90012, "ilom_admin_consistency", self.__host))
    
    def mRunBridgeTest(self):
        if self.__cluctrl.mIsKVM():
            _vif = "vnet"
        else:
            _vif = "vif"

        _cmd_str = """brctl show | tr -s '\n\t\ ' ' ' | sed -e 's/vm/\\nvm/g' | grep "%s" | awk '{print $1}' """ % (_vif)
        _output = self.mRemoteExecute(_cmd_str)
        ebLogInfo('*** bridge output: %s' %(_output))
        if _output or len(_output):
            ebLogError('*** %s: stale bridges are present on dom0 %s' %(self.__alert_log, self.__host))
            self.__res.update( {'bridge_check' : 'abnormal'} )
            self.__error_list.append(get_hw_validate_error(90013, "bridge_check", self.__host))
        else:
            self.__res.update( {'bridge_check' : 'normal'} )
            ebLogInfo("*** {0}: BRIDGE_CHECK is normal on dom0:{1}".format(self.__alert_log, self.__host))

    def mRun2TMemoryTest(self):
        try:
            _enable_2t_support = self.__cluctrl.mCheckConfigOption('enable_2t_memory_support')
            _exadata_model = self.__cluctrl.mGetNodeModel(aHostName=self.__host)
            if (self.__cluctrl.mIsKVM() and _enable_2t_support == "True" and self.__cluctrl.mCompareExadataModel(
                    _exadata_model, 'X9') >= 0 and self.__modelsubType in ["ELASTIC_LARGE", "ELASTIC_EXTRA_LARGE"] and (
                    self.__nodeType in ["elastic-servers"] and self.__operationType in ["ADD_COMPUTE", "CEI_RESERVE"])):
                _is_supported = self.__cluctrl.mCheck2TMemoryRequirements(self.__host, self.__modelsubType)
                if _is_supported:
                    self.__res.update({'2tb_memory': 'supported'})
                else:
                    self.__res.update({'2tb_memory': 'not_supported'})
                    self.__error_list.append(get_hw_validate_error(90034, "2tb_memory", self.__host))
        except Exception as e:
            self.__res.update({'2tb_memory': 'failed'})
            self.__error_list.append(get_hw_validate_error(90033, "2tb_memory", self.__host))
            ebLogError('*** Exception in testing  2tb_memory[%s]' % (e,))
            ebLogError(traceback.format_exc())

    def mRunStaleDomUTest(self):
        #Stale DomU Check
        _hv = getHVInstance(self.__host)
        _output = _hv.mGetDomains()
        ebLogInfo('*** stale DomUs: %s' %(_output))
        if _output or len(_output):
            ebLogError('*** %s: stale domUs are present on dom0 %s' %(self.__alert_log, self.__host))
            self.__res.update( {'stale_domu_check' : 'abnormal'} )
            self.__error_list.append(get_hw_validate_error(90014, "stale_domu_check", self.__host))
        else:
            self.__res.update( {'stale_domu_check' : 'normal'} )
            ebLogInfo("*** {0}: STALE_DOMU_CHECK is normal on dom0:{1}".format(self.__alert_log, self.__host))

    def mRunImageInfoTest(self, aOsType):
        _aOsType = aOsType
        _cmd_str = "imageinfo | grep 'Node type:'"
        _output = self.mRemoteExecute(_cmd_str)
        if _output or len(_output):
            _hviType = _output[0].split()[2].strip()
            if _hviType == "KVMHOST" and _aOsType == "kvm":
                self.__res.update( {'image_info_check' : 'normal'} )
            elif _hviType == "DOM0" and _aOsType == "ib":
                self.__res.update( {'image_info_check' : 'normal'} )
            else:
                self.__res.update( {'image_info_check' : 'abnormal'} )
                self.__error_list.append(get_hw_validate_error(90015, "image_info_check", self.__host))


class ebCluCellSanityTests:
    def __init__(self, aCluPreCheck, aNodeInfo=None, aNodeType=None, aStep="", aMultivm=False, aPrecheckConfig=None):
        self.__precheck = aCluPreCheck
        self.__nodeInfo = aNodeInfo
        self.__nodeType = aNodeType
        self.__step = aStep
        self.__multiVM = False
        self.__precheckConfig = aPrecheckConfig

        self.__cluctrl = self.__precheck.mGetEbox()
        self.__verbose = self.__cluctrl.mGetVerbose()

        self.__res = {}
        self.__res['Details'] = {}
        self.__error_list = []
        self.__precheck_list = []

        for _key, _value in self.__precheckConfig.items():
            if _value == "True":
                self.__precheck_list.append(_key)

        if self.__step == "ESTP_PREVM_CHECKS":
            self.__hostname, self.__domain = aNodeInfo.split('.', 1)
            self.__res.update( { "hostname" : self.__hostname, "domainname" : self.__domain, "hw_type" : "CELL", 'error_list' : []} )
            self.__host = self.__hostname +  '.' + self.__domain
            self.__alert_log = "ESTP_PREVM_CHECKS"
        elif self.__step == "ELASTIC_SHAPES_VALIDATION":
            self.__multiVM = aMultivm
            self.__nodeInfo.update( {'error_list' : []} )
            self.__nodeInfo.update( {'node_type' : self.__nodeType} )
            self.__host = self.__nodeInfo['hostname'] + '.' + self.__nodeInfo['domainname']
            self.preprov = self.__nodeInfo['preprov']

            self.__alert_log = 'ELASTIC_SHAPES_VALIDATION'

        self.__node = exaBoxNode(get_gcontext())

    def run(self, aHwChecksTable={}):

        self.mPingTest()
        _status = self.__res.get("ping_test", "")
        if _status == "abnormal":
            if self.__step == "ELASTIC_SHAPES_VALIDATION":
                if self.__error_list:
                    self.__nodeInfo.update( {'error_list' : self.__error_list } )
                self.__res.update( {'node_info' : [self.__nodeInfo]} )
                # Fill multiprocess dictionary in format {node: result}
                aHwChecksTable[self.__host] = self.__res
                # Log context for exacloud thread
                ebLogError(f"*** ERROR: host={self.__host}, step={self.__step}, result={json.dumps(self.__res)}")
                return

            if self.__step == "ESTP_PREVM_CHECKS":
                if self.__error_list:
                    self.__res.update({'error_list': self.__error_list})

            # Fill multiprocess dictionary in format [{result}, ...]
            _proxy_list = aHwChecksTable.get("nodes", [])
            _proxy_list.append(self.__res)
            aHwChecksTable["nodes"] = _proxy_list
            return

        self.mRunSshTest()
        _status = self.__res.get("ssh_test", "")
        if _status == "normal":
            self.__node.mConnect(aHost=self.__host)

            for _name in self.__precheck_list:
                _func_name = gPreCheckFunctionMap[_name]
                try:
                    getattr(self, _func_name)()
                except Exception as e:
                    self.__res.update({_name: 'failed'})
                    self.__error_list.append(get_hw_validate_error(91000, _name, self.__host))
                    ebLogError('*** Exception in testing  %s[%s]' % (_name, e,))
                    ebLogError(traceback.format_exc())

            self.__node.mDisconnect()
        else:
            ebLogError("*** {0}: cell {1} is not connectable by SSH".format(self.__alert_log, self.__host))

        if self.__step == "ELASTIC_SHAPES_VALIDATION":
            if self.__error_list:
                self.__nodeInfo.update( {'error_list' : self.__error_list } )
            self.__res.update( {'node_info' : [self.__nodeInfo]} )
            # Fill multiprocess dictionary in format {node: result}
            aHwChecksTable[self.__host] = self.__res
            return

        if self.__step == "ESTP_PREVM_CHECKS":
            if self.__error_list:
                self.__res.update({'error_list': self.__error_list})

        # Fill multiprocess dictionary in format [{result}, ...]
        _proxy_list = aHwChecksTable.get("nodes", [])
        _proxy_list.append(self.__res)
        aHwChecksTable["nodes"] = _proxy_list
        return

    def mRemoteExecute(self, aCmd):
        _cmd_str = aCmd
        _i, _o, _e = self.__node.mExecuteCmd(_cmd_str)
        _out = [_line.strip() for _line in _o.readlines()]
        return _out

    def mParseNodeResult(self, aOutput):
        _output = aOutput
        _error_details = {}
        for _line in _output:
            _disk_split = _line.split()
            if _disk_split:
                _error = ' '.join( str(_ret) for _ret in _disk_split[1:] )
                ebLogError(_error)
                _error_details.update( { _disk_split[0] : _error } )
        return _error_details

    def mGetIfaceAdress(self, aInt):
        _iface = aInt
        _ip_addr = ""

        _cmd_str = "ip addr show dev %s | grep 'inet' | cut -d: -f2 | awk '{print $2}' " %(_iface)
        _output = self.mRemoteExecute(_cmd_str)
        if _output:
            _ip_addr = _output[0].split('/')[0]

        return _ip_addr

    def mGetIfaceList(self):
        _ifaceList = []
        if self.__cluctrl.mIsKVM():
            _includes = ('stre0', 'stre1', 're0', 're1')
        else:
            _includes = ('stib0', 'stib1')

        _cmd_str = "cd /etc/sysconfig/network-scripts/; ls ifcfg-*"
        _output = self.mRemoteExecute(_cmd_str)
        if _output:
            for _intf in _output:
                if _intf.endswith(_includes):
                    _ifaceList.append(_intf.split('-')[1])
        return _ifaceList

    def mPingTest(self):
        if not self.__cluctrl.mPingHost(self.__host):
            ebLogError('*** {0}: Host {1} is not pingable.'.format(self.__alert_log, self.__host))
            self.__res.update( {'ping_test' : 'abnormal'} )
            self.__error_list.append(get_hw_validate_error(91001, "ping_test", self.__host))
        else:
            self.__res.update( {'ping_test' : 'normal'} )
            ebLogInfo("*** {0}: PING_TEST on cell:{1} is normal".format(self.__alert_log, self.__host))

    def mRunSshTest(self):
        if self.__cluctrl.mIsOciEXACC():
            _key_only = False
        else:
            _key_only = True

        if self.__node.mIsConnectable(aHost=self.__host, aKeyOnly=_key_only):
            self.__res.update( {'ssh_test' : 'normal'} )
            ebLogInfo("*** {0}: SSH_TEST on cell:{1} is normal".format(self.__alert_log, self.__host))
        else:
            ebLogError("*** {0}: SSH_TEST on cell:{1} is abnormal".format(self.__alert_log, self.__host))
            self.__res.update( {'ssh_test' : 'abnormal'} )
            self.__error_list.append(get_hw_validate_error(91002, "ssh_test", self.__host))

    def mRunListAlertHistory(self):
        """
        Method to check alert history in cells.
        For now, we check for non-cleared alerts (endTime=null) and for
        stateful alerts only which are also critical:

        Reference:
        Stateful alerts represent observable cell states that can be
            subsequently retested to detect whether the state has changed,
            indicating that a previously observed alert condition is no longer
            a problem.
        Stateless alerts represent point-in-time events that do not represent
        a persistent condition; they simply show that something has occurred.

        """
        _cellcli_alerthistory_options = mGetAlertHistoryOptions(self.__cluctrl, self.__host)
        _cmd_str = (f"/opt/oracle/cell/cellsrv/bin/cellcli {_cellcli_alerthistory_options} -e "
            f"'list alerthistory where endTime=null AND alertType=stateful AND severity=critical'")
        _output = self.mRemoteExecute(_cmd_str)
        _alerts = []
        if _output or len(_output):
            for _line in _output:
                if "critical" in _line:
                    _err_msg = (f"Cellcli critical alert(Unresolved): "
                        f"Host: {self.__host} - {_line.strip()}")
                    ebLogWarn(_err_msg)
                    _alerts.append(_alerts)

        if _alerts:
            ebLogError("*** {0}: HW_ALERTS on cell:{1} is abnormal".format(
                self.__alert_log, self.__host))
            self.__res.update( {'hw_alerts' : 'abnormal'} )
            self.__error_list.append(get_hw_validate_error(91035, "hw_alerts", self.__host))
            ebLogError("Please fix and clear the following Critical Alerts: "
                f"{_alerts} before retrying the step. To disable "
                "this checks please disable the flag 'hw_alerts' in "
                "'config/hardware_prechecks.conf' then retry the operation")

        else:
            ebLogInfo("*** {0}: HW_ALERTS on cell:{1} is normal".format(
                self.__alert_log, self.__host))
            self.__res.update( {'hw_alerts' : 'normal'} )


    def mRunHWTest(self):
        _cmd_str = "cellcli -e list cell detail | grep -Ew 'fanStatus|powerStatus|temperatureStatus|cellsrvStatus|msStatus|rsStatus'"
        _output = self.mRemoteExecute(_cmd_str)
        _error_code = {
            'fanStatus': 91004,
            'temperatureStatus': 91006,
            'powerStatus': 91005,
            'cellsrvStatus': 91003,
            'msStatus': 91029,
            'rsStatus': 91030
        }
        if _output or len(_output):
            for _iter in _output:
                _key = _iter.split(':')[0].strip()
                _ret = _iter.split(':')[1].strip()
                _value = 'normal' if _ret in ['normal', 'online', 'running' ] else 'abnormal'
                if _value == 'abnormal':
                    ebLogError("*** {0}: {1} status on cell:{2} is abnormal".format(self.__alert_log, _key.split('S')[0].upper(), self.__host))
                    self.__error_list.append(get_hw_validate_error(_error_code.get(_key, 91031), _key, self.__host))
                else:
                    ebLogInfo("*** {0}: {1} status on cell:{2} is normal".format(self.__alert_log, _key.split('S')[0].upper(), self.__host))
                if _key == 'fanStatus':
                    self.__res.update( {'fan' : _value} )
                elif _key == 'temperatureStatus':
                    self.__res.update( {'temperature' : _value} )
                elif _key == 'cellsrvStatus':
                    self.__res.update( {'cellsrvStatus' : 'running'} )
                elif _key == 'msStatus':
                    self.__res.update( {'msStatus' : 'running'} )
                elif _key == 'rsStatus':
                    self.__res.update( {'rsStatus' : 'running'} )
    
    def mRunLunTest(self):
        _cmd_str = "cellcli -e list lun attributes name, status  where diskType like \\'.*Disk\\' and status!=\\'normal\\';"
        _output = self.mRemoteExecute(_cmd_str)
        if _output or len(_output):
            ebLogError("*** {0}: LUN status on cell:{1} is abnormal".format(self.__alert_log, self.__host))
            _err = self.mParseNodeResult(_output)
            self.__res.update( {'lun' : 'abnormal'} )
            self.__res['Details']['lun'] = _err
            self.__error_list.append(get_hw_validate_error(91016, "lun", self.__host, _err))
        else:
            self.__res.update( {'lun' : 'normal'} )
            ebLogInfo("*** {0}: LUN status on cell:{1} is normal".format(self.__alert_log, self.__host))

    def mRunPhysicalDiskTest(self):
        _status = "normal"
        _cmd_str = "cellcli -e list physicaldisk attributes name,status  where diskType like \\'.*Disk\\' and status!=\\'normal\\';"
        _output = self.mRemoteExecute(_cmd_str)
        if _output or len(_output):
            for _line in _output:
                if "predictive" in _line.lower():
                    if self.__cluctrl.mCheckConfigOption('ignore_m2_sys_error'):
                        if "m2_sys" in _line.lower():
                            continue
                _status = "abnormal"
            if _status == "normal":
                self.__res.update( {'physicaldisk' : 'normal'} )
                ebLogInfo("*** {0}: PHYSICALDISK status on cell:{1} is normal".format(self.__alert_log, self.__host))
            else:
                ebLogError("*** {0}: PHYSICALDISK status on cell:{1} is abnormal".format(self.__alert_log, self.__host))
                _err = self.mParseNodeResult(_output)
                self.__res.update( {'physicaldisk' : 'abnormal'} )
                self.__res['Details']['physicaldisk'] = _err
                self.__error_list.append(get_hw_validate_error(91009, "physicaldisk", self.__host, _err))
        else:
            self.__res.update( {'physicaldisk' : 'normal'} )
            ebLogInfo("*** {0}: PHYSICALDISK status on cell:{1} is normal".format(self.__alert_log, self.__host))

    def mListGridDisk(self):
        _cmd_str = "cellcli -e LIST GRIDDISK ATTRIBUTES NAME;"
        _griddisks = self.mRemoteExecute(_cmd_str)
        return _griddisks

    def mGridDiskStatus(self):

        try:
            _suffix = self.__cluctrl.mGetClusterSuffix()
        except:
            _cmd_str = "cellcli -e list griddisk attributes name,status;"
            _output = self.mRemoteExecute(_cmd_str)
            return _output

        _suffix = self.__cluctrl.mGetClusterSuffix()

        if self.__cluctrl.IsZdlraProv():
            _cmd_str = "cellcli -e list griddisk attributes name,status  where diskType like \\'.*Disk\\' | grep 'CATALOG\|DELTA'"
            _output = self.mRemoteExecute(_cmd_str)
        elif _suffix:
            _cmd_str = "cellcli -e list griddisk attributes name,status  where name like \\'.*%s_.*\\' and diskType like \\'.*Disk\\';" %(_suffix)
            _output = self.mRemoteExecute(_cmd_str)
        else:
            _output = ["Failed to get cluster suffix from the cluster XML"]
        return _output

    def mRunGridDiskTest(self):
        _err_str = "Failed to get cluster suffix from the cluster XML"
        if self.__step == "ELASTIC_SHAPES_VALIDATION":
            if self.__nodeType == "quarter-rack-servers":
                _output = self.mGridDiskStatus()
                if _output:
                    _status = "normal"
                    for _line in _output:
                        _disk = _line.strip()
                        if _disk:
                            _pattern = re.compile(r"\bactive\b")
                            _isExist = _pattern.search(_disk)
                            if not _isExist:
                                ebLogInfo(f"{_disk}")
                                _status = "abnormal"
                                ebLogError("*** {0}: GRIDDISK status on cell:{1} is abnormal".format(self.__alert_log, self.__host))
                                if _err_str in _output:
                                    _err = _err_str
                                else:
                                    _err = _disk
                                self.__res.update( {'griddisk' : 'abnormal'} )
                                self.__res['Details']['griddisk'] = _err
                                self.__error_list.append(get_hw_validate_error(91017, "griddisk", self.__host, _err))
                        else:
                            _status = "abnormal"
                            _err = "Could not retrieve GRIDDISK output, griddisks could have been deleted."
                            ebLogError("*** {0}: GRIDDISK status on cell:{1} is abnormal".format(self.__alert_log, self.__host))
                            self.__res.update( {'griddisk' : 'abnormal'} )
                            self.__res['Details']['griddisk'] = _err
                            self.__error_list.append(get_hw_validate_error(91018, "griddisk", self.__host, _err))
                    if _status == "normal":
                        self.__res.update( {'griddisk' : 'normal'} )
                        ebLogInfo("*** {0}: GRIDDISK status on cell:{1} is normal".format(self.__alert_log, self.__host))
                else:
                    _err = "Could not retrieve GRIDDISK output, griddisks could have been deleted."
                    ebLogError("*** {0}: GRIDDISK status on cell:{1} is abnormal".format(self.__alert_log, self.__host))
                    #self.__res.update( {'griddisk' : 'abnormal'} )
                    #self.__res['Details']['griddisk'] = _err
                    #self.__error_list.append( { "error-type": "griddisk", "error-message" : _err} )
            if self.__nodeType == "elastic-servers":
                if self.__multiVM:
                    _output = self.mGridDiskStatus()
                    if _output or len(_output):
                        ebLogError("*** {0}: GRIDDISK status on cell:{1} is abnormal".format(self.__alert_log, self.__host))
                        if _err_str in _output:
                            _err = _err_str
                        else:
                            _err = self.mParseNodeResult(_output)
                        self.__res.update( {'griddisk' : 'abnormal'} )
                        self.__res['Details']['griddisk'] = _err
                        self.__error_list.append(get_hw_validate_error( 91017, "griddisk", self.__host, _err))
                    else:
                        self.__res.update( {'griddisk' : 'normal'} )
                        ebLogInfo("*** {0}: GRIDDISK status on cell:{1} is normal".format(self.__alert_log, self.__host))
                else:
                    _output = self.mListGridDisk()
                    if _output or len(_output):
                        _err =  f"GRIDDISK entries present on cell:{self.__host}"
                        ebLogError("*** {0}: GRIDDISK entries present on cell:{1} ".format(self.__alert_log, self.__host))
                        self.__res.update( {'griddisk' : 'abnormal'} )
                        self.__res['Details']['griddisk'] = _err
                        self.__error_list.append(get_hw_validate_error(91019, "griddisk", self.__host, _err))
                    else:
                        self.__res.update( {'griddisk' : 'normal'} )
                        ebLogInfo("*** {0}: NO GRIDDISK present on the cell:{1} status is normal".format(self.__alert_log, self.__host))
        elif self.__step == "ESTP_PREVM_CHECKS":
            _output = self.mGridDiskStatus()
            if _output or len(_output):
                ebLogError("*** {0}: GRIDDISK status on cell:{1} is abnormal".format(self.__alert_log, self.__host))
                if _err_str in _output:
                    _err = _err_str
                else:
                    _err = self.mParseNodeResult(_output)
                self.__res.update( {'griddisk' : 'abnormal'} )
                self.__res['Details']['griddisk'] = _err
                self.__error_list.append(get_hw_validate_error(91017, "griddisk", self.__host))
            else:
                self.__res.update( {'griddisk' : 'normal'} )
                ebLogInfo("*** {0}: GRIDDISK status on cell:{1} is normal".format(self.__alert_log, self.__host))
    
    def mRunCellDiskTest(self):
        _error_code = 91020
        _cmd_status = "cellcli -e list celldisk attributes name,status  where diskType like \\'.*Disk\\' and status!=\\'normal\\';"
        _output = self.mRemoteExecute(_cmd_status)
        if _output or len(_output):
            # Dont drop cells in case of mvm
            if self.__cluctrl.mGetSharedEnv():
                ebLogWarn('*** Cell Secure Erase cannot proceed in case of MVM')
                _error_code = 91021
                _err = self.mParseNodeResult(_output)
            else:
                # Drop corrupt cells
                ebLogInfo(f"*** {self.__alert_log}: CELLDISK status on cell:{self.__host} is abnormal, trying to drop the cells")
                _err = None
                _cmdstr = "cellcli -e LIST GRIDDISK ATTRIBUTES NAME;"
                _griddisks = self.mRemoteExecute(_cmdstr)
                if len(_griddisks):
                    ebLogWarn('*** Cell Secure Erase cannot proceed with active Grid Disks present: %s' % (str(_griddisks)))
                    _error_code = 91022
                    _err = self.mParseNodeResult(_griddisks)
                else:            
                    _cmd_drop = 'cellcli -e drop celldisk all'
                    self.mRemoteExecute(_cmd_drop)
                    time.sleep(100)
                    _output = self.mRemoteExecute(_cmd_status)
                    if _output:
                        _err = self.mParseNodeResult(_output)
                        _error_code = 91023
            if _err:
                self.__res.update( {'celldisk' : 'abnormal'} )
                self.__res['Details']['celldisk'] = _err
                self.__error_list.append(get_hw_validate_error(_error_code, "celldisk", self.__host, _err))
        else:
            self.__res.update( {'celldisk' : 'normal'} )
            ebLogInfo("*** {0}: CELLDISK status on cell:{1} is normal".format(self.__alert_log, self.__host))
    
    def mRunFlashCacheTest(self):
        _cmd_str = 'cellcli -e list flashcache attributes name,size'
        _output = self.mRemoteExecute(_cmd_str)
        if _output is None or not len(_output):
            ebLogWarn('*** FLASHCACHE is not enabled on the Cell: %s' % (self.__host))
        else:
            ebLogInfo('*** FLASHCACHE enabled on cell: %s' % (self.__host))

            self.mUpdateNormalFlushedCellDisks()

            _cmd_str = "cellcli -e list flashcache attributes name,status where status!=\\'normal\\';"
            _output = self.mRemoteExecute(_cmd_str)
            if _output or len(_output):
                ebLogError("*** {0}: FLASHCACHE status on cell:{1} is abnormal".format(self.__alert_log, self.__host))
                _err = self.mParseNodeResult(_output)
                self.__res.update( {'flashcache' : 'abnormal'} )
                self.__res['Details']['flashcache'] = _err
                self.__error_list.append(get_hw_validate_error(91028, "flashcache", self.__host, _err))
            else:
                self.__res.update( {'flashcache' : 'normal'} )
                ebLogInfo("*** {0}: FLASHCACHE status on cell:{1} is normal".format(self.__alert_log, self.__host))
    
    def mRunPmemCacheTest(self):
        if self.mGetCellOLVersion()=='OL8':
            ebLogInfo('*** PMEMCACHE check skipped for OL8 on cell: %s' % (self.__host))
            return
        _cmd_str = 'cellcli -e list pmemcache attributes name,size'
        _output = self.mRemoteExecute(_cmd_str)
        if (_output is None or not len(_output) or 'CELL-01504' in _output[0]
                    or 'Invalid command syntax' in _output[0]):
            ebLogWarn('*** PMEMCACHE is not enabled or available on the Cell: %s' % (self.__host))
        else:
            ebLogInfo('*** PMEMCACHE enabled on cell: %s' % (self.__host))

            _cmd_str = "cellcli -e list pmemcache attributes name,status  where  status!=\\'normal\\';"
            _output = self.mRemoteExecute(_cmd_str)
            if _output or len(_output):
                ebLogError("*** {0}: PMEMCACHE status on cell:{1} is abnormal".format(self.__alert_log, self.__host))
                _err = self.mParseNodeResult(_output)
                self.__res.update( {'pmemcache' : 'abnormal'} )
                self.__res['Details']['pmemcache'] = _err
                self.__error_list.append(get_hw_validate_error(91027, "pmemcache", self.__host, _err))
            else:
                self.__res.update( {'pmemcache' : 'normal'} )
                ebLogInfo("*** {0}: PMEMCACHE status on cell:{1} is normal".format(self.__alert_log, self.__host))
    
    def mRunRootStorageTest(self):
        #Memory test on cells: assuming 95 percent as threshold
        _partition = '/'
        _threshold_root_space = '95'
        if not self.__precheck.mCheckUsedSpace(self.__host,  _partition, _threshold_root_space):
            ebLogError("*** space used in root partition is more than threshold(%s%%) for host - %s" %(_threshold_root_space, self.__host))
            ebLogError("*** {0}: ROOT_STORAGE_TEST on cell:{1} is abnormal".format(self.__alert_log, self.__host))
            self.__res.update( {'root_storage_test' : 'abnormal'} )
            self.__error_list.append(get_hw_validate_error(91007, "root_storage_test", self.__host))
        else:
            if self.__verbose:
                ebLogVerbose('*** %s partition space used is less than threshold value(%s%%) for host - %s' %(_partition, _threshold_root_space, self.__host))
            ebLogInfo("*** {0}: ROOT_STORAGE_TEST on / partition is normal on cell:{1}".format(self.__alert_log, self.__host))
            self.__res.update( {'root_storage_test' : 'normal'} )
    
    def mRunIPConflictTest(self):
        #
        # IP address match between cellinit.ora and ifconfig addresses
        #
        _cmd_str = 'locate cellinit.ora'
        _output = self.mRemoteExecute(_cmd_str)
        if _output is None or not len(_output):
            ebLogWarn('*** Unable to locate cellinit.ora file on Cell: %s' % (self.__host))
            self.__res.update( {'ip_match_test' : 'abnormal'} )
            self.__error_list.append(get_hw_validate_error(91024, "ip_match_test", self.__host))
        else:
            _cell_init = _output[0]

            _cmd_str = "cat %s | grep -E 'ipaddress1|ipaddress2' " %(_cell_init)
            _output = self.mRemoteExecute(_cmd_str)

            _cell_init_ip = []
            for _line in _output:
                _name, _addr = _line.split('=') 
                _cell_init_ip.append(_addr.split('/')[0])

            _ifaceList = self.mGetIfaceList()
            if len(_ifaceList) == 2:
                _ip_addr1 = self.mGetIfaceAdress("%s" %(_ifaceList[0]))
                _ip_addr2 = self.mGetIfaceAdress("%s" %(_ifaceList[1]))
            else:
                self.__res.update( {'ip_match_test' : 'abnormal'} )
                self.__error_list.append(get_hw_validate_error(91026, "ip_match_test", self.__host))
                return

            if _ip_addr1 in _cell_init_ip and _ip_addr2 in _cell_init_ip:
                ebLogInfo("*** {0}: IPAddress of cellinit.ora matches with ifconfig on cell:{1}".format(self.__alert_log, self.__host))
                self.__res.update( {'ip_match_test' : 'normal'} )
            else:
                ebLogError("*** {0}: IPAddress mismatch between cellinit.ora and ifconfig on cell:{1} ".format(self.__alert_log, self.__host))
                ebLogError("*** {0}: ip_match_test on cell:{1} is abnormal".format(self.__alert_log, self.__host))
                self.__res.update( {'ip_match_test' : 'abnormal'} )
                self.__error_list.append(get_hw_validate_error(91025, "ip_match_test", self.__host))

    def mGetCellOLVersion(self):
        _cmd_str = "/bin/uname -r"
        _OLVersion = ''
        _output = self.mRemoteExecute(_cmd_str)
        if _output:
            _uekStr = _output[0].strip().split('.')[-2]
            _OLVersion = "OL" + _uekStr[2]
        return _OLVersion

    def mUpdateNormalFlushedCellDisks(self):
        # Get all cells in normal - flushed status
        _cmd_str = "cellcli -e list flashcache attributes name,status where status=\\'normal - flushed\\'"
        _output = self.mRemoteExecute(_cmd_str)
        if not _output or len(_output) == 0:
            return
        # Log cells with normal - flushed status
        for _line in _output:
            ebLogInfo(f"*** Found: {_line}")
        # Try to cancel all flush operations
        ebLogInfo("*** Found cells with \'normal - flushed\' FLASHCACHE status. Cancelling all flush operations.")
        _cmd_str = "cellcli -e alter flashcache all cancel flush"
        _output = self.mRemoteExecute(_cmd_str)
        # Check if cancellation was successful
        for _line in _output:
            if "altered successfully" not in _line:
                ebLogError("*** Could not cancel all flush operations successfully.")
                return
        ebLogInfo("*** All flush operations cancelled successfully.")

class ebCluReshapePrecheck(object):

    def __init__(self, aExaBoxCluCtrl):
        self.__ebox = aExaBoxCluCtrl
        self._optype_key = "opType"

    def mRunReshapePrecheck(self, aOptions):
        _options = aOptions
        _inputjson = _options.jsonconf

        if _inputjson:
            if self._optype_key not in _inputjson.keys() or not _inputjson[self._optype_key]:
                _detail_error = "\'opType\' parameter is not provided. Please provide the parameter to proceed"
                self.__ebox.mUpdateErrorObject(gReshapeError['INVALID_INPUT_PARAMETER'], _detail_error)
                return 1
        else:
            _detail_error = "Missing input payload"
            self.__ebox.mUpdateErrorObject(gReshapeError['INVALID_INPUT_PARAMETER'], _detail_error)
            return 1
        _optype = _inputjson[self._optype_key]
        
        _rc = 0
        if _optype == "ASM":
            cluPrecheckReshapeStorage = ebCluStorageReshapePrecheck(self.__ebox)
            _rc = cluPrecheckReshapeStorage.mStorageReshapePrecheck(_options)
        elif _optype == "MEMORY":
            cluPrecheckReshapeMemory = ebCluMemoryReshapePrecheck(self.__ebox)
            _rc = cluPrecheckReshapeMemory.mMemoryReshapePrecheck(_options)
        elif _optype != "OHOME":
            _detail_error = "Operation " + _optype + " is not supported. Please input a valid operation"
            self.__ebox.mUpdateErrorObject(gReshapeError['INVALID_INPUT_PARAMETER'], _detail_error)
            _rc = 1

        return _rc

class ebCluMemoryReshapePrecheck(object):

    def __init__(self, aExaBoxCluCtrl):
        self.__ebox = aExaBoxCluCtrl
        self.__error_list = []
        self.__node = exaBoxNode(get_gcontext())

    def mMemoryReshapePrecheck(self, aOptions):
        ebLogInfo('*** Running Memory reshape precheck ***')
        _rc = self.mCheckMemoryDimmFailure()
        _error = ""
        _data = []
        _storage_precheck_object = ebCluStorageReshapePrecheck(self.__ebox)
        if _rc == 0:
            _storage_precheck_object.mUpdateRequestData(_rc, _data, _error, aOptions)
            ebLogInfo('*** mMemoryReshapePrecheck: Success - Memory reshape precheck passed')
        else:
            _error = ", ".join(self.__error_list)
            _detail_error = "Memory reshape precheck failed. Memory DIMM failure in following dom0s: " + _error
            ebLogError('*** mMemoryReshapePrecheck: The dom0s with memory DIMM failure are: %s' % (_error))
            _storage_precheck_object.mUpdateRequestData(_rc, _data, _detail_error, aOptions)
            self.__ebox.mUpdateErrorObject(gReshapeError['ERROR_RESHAPE_PRECHECK'], _detail_error)
            raise ExacloudRuntimeError(0x0808, 0xA, _detail_error)

        return _rc
    
    def mCheckMemoryDimmFailure(self):
        ebLogInfo('*** mCheckMemoryDimmFailure >>>')
        _ebox = self.__ebox
        _rc = 0
        _dom0s, _, _, _ = _ebox.mReturnAllClusterHosts()
        IPMITOOL = '/usr/sbin/ipmitool'

        _dimm_failure_check = IPMITOOL + " sunoem cli \"show /System/memory\"| grep -i 'health ='| awk '{print $3}'"

        for _dom0 in sorted(_dom0s):
            self.__node.mConnect(aHost=_dom0)
            ebLogInfo("*** Executing the command in dom0 %s - %s" % (_dom0, _dimm_failure_check))
            _, _o, _e = self.__node.mExecuteCmd(_dimm_failure_check)
            if _o:
                _output = _o.readlines()
                _out = _output[0].strip()
                ebLogDebug("*** Output from command %s is: %s" % (_dimm_failure_check, _out))
                if(_out != "OK"):
                    self.__error_list.append(_dom0)
                    _rc = 1
            self.__node.mDisconnect()

        ebLogInfo('*** mCheckMemoryDimmFailure <<< ***')
        return _rc
        

class ebCluStorageReshapePrecheck(object):

    def __init__(self, aExaBoxCluCtrl):
        self.__ebox = aExaBoxCluCtrl
        self.__error_list = []
        self.__node = exaBoxNode(get_gcontext())

    def mStorageReshapePrecheck(self, aOptions,aReshapeProgress=False):
        ebLogInfo('*** Running Exadata storage reshape precheck ***')

        # Bug 37315192: We need to retry the griddisk precheck
        # to avoid failling for transcient issues (same as in
        # asm reshape)
        _rc = self.mGetOfflineCellDisks()
        _error = ""
        _count = 0
        _max_tries = int(self.__ebox.mCheckConfigOption('disk_online_timeout'))
        while _rc != 0 and _count < _max_tries:
            ebLogInfo('*** Waiting for all griddisks to be online')
            time.sleep(60)
            _rc = self.mGetOfflineCellDisks()
            _count = _count + 1

        if _rc != 0:
            _error = ", ".join(self.__error_list)
            _detail_error = "ASM reshape precheck failed: " + "\n" + _error
            ebLogError('*** mStorageReshapePrecheck: The error is: %s' % (_error))
            self.mUpdateRequestData(_rc, [], _detail_error, aOptions)
            self.__ebox.mUpdateErrorObject(gReshapeError['ERROR_RESHAPE_PRECHECK'], _detail_error)
            raise ExacloudRuntimeError(0x0808, 0xA, _detail_error)

        self.mUpdateRequestData(_rc, [], _error, aOptions)
        ebLogInfo('*** mStorageReshapePrecheck: Success - ASM storage reshape precheck passed')
        return _rc


    def mUpdateRequestData(self, rc, aData, err, aOptions):
        """
        Updates request object with the response payload
        """
        _reqobj = self.__ebox.mGetRequestObj()
        _response = {}
        _response["success"] = "True" if (rc == 0) else "False"
        _response["error"] = err
        _response["output"] = aData
        if _reqobj is not None:
            _db = ebGetDefaultDB()
            _reqobj.mSetData(json.dumps(_response, sort_keys = True))
            _db.mUpdateRequest(_reqobj)
            ebLogInfo(json.dumps(_response, indent=4, sort_keys=True))

        ebLogJson(json.dumps(_response, indent=4, sort_keys = True))

    def mGetOfflineCellDisks(self):
        ebLogInfo('*** mGetOfflineCellDisks >>> ***')
        GRID_DISK_FAULTY = 1
        GRID_DISK_GOOD = 0
        MAX_EXEC_TIME = 600
        MAX_JOIN_TIMEOUT = 5
        _rc = GRID_DISK_GOOD

        def _griddisk_asmmodestatus_validation(_cell,_dg_suffix, rc_status):
            _rc = False
            _invalid_griddisk_status = ['DROPPED','OFFLINE','UNKNOWN']
            _cellcli_path = "/opt/oracle/cell/cellsrv/bin/cellcli"
            _cellcli_celldisk_check = f"{_cellcli_path} -e \"list griddisk attributes name,asmmodestatus where name like \'.*{_dg_suffix}_.*\'\""
            ebLogInfo(f"*** Executing the command in cell {_cell} {_cellcli_celldisk_check}")
            with connect_to_host(_cell, get_gcontext(),username='root') as cellnode:
                _, _o, _e = cellnode.mExecuteCmd(_cellcli_celldisk_check)
                if not cellnode.mGetCmdExitStatus() and _o:
                    _output = _o.readlines()
                    if(len(_output) > 0):
                        _output = ' '.join(_output)
                        if (any(map(_output.__contains__, _invalid_griddisk_status))):
                            _griddisk_invalid_state = f"One of the grid disks in DROPPED/OFFLINE/UNKNOWN state.Check the command output :\n {_output}"
                            ebLogError(f"*** {_griddisk_invalid_state}")
                            _rc = True
                        else:
                            _rc = False
            rc_status[_cell] = _rc
               
        _plist = ProcessManager()
        _rc_d = _plist.mGetManager().dict()
        _ebox = self.__ebox
        _dg_suffix = _ebox.mGetStorage().mClusterDiskGroupSuffix()
        ebLogInfo(f"*** the Cluster postfix retrived is : {_dg_suffix}")

        _dom0s, _domUs, _cells, _switches = _ebox.mReturnAllClusterHosts()
        for _cell in sorted(_cells):
            _p = ProcessStructure(_griddisk_asmmodestatus_validation, [_cell,_dg_suffix,_rc_d], _cell)
            _p.mSetMaxExecutionTime(MAX_EXEC_TIME) # 10 minutes
            _p.mSetJoinTimeout(MAX_JOIN_TIMEOUT)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()
        for _cell in sorted(_cells):
            if _rc_d[_cell]:
                _error_msg = f"{_cell} : One of the grid disks in DROPPED/OFFLINE/UNKNOWN state"
                self.__error_list.append(_error_msg)
                _rc = GRID_DISK_FAULTY
        return _rc


    def mCheckDiskSizeMatch(self, aOptions):
        ebLogInfo('*** mCheckDiskSizeMatch >>> ***')
        _ebox = self.__ebox
        _rc = 0
        _suffix = _ebox.mGetClusterSuffix()
        _cellcli_path = "/opt/oracle/cell/cellsrv/bin/cellcli"
        _, _, _cells, _ = _ebox.mReturnAllClusterHosts()
        _cellcli_gdsize_check = _cellcli_path + " -e list griddisk attributes name,size,asmdisksize | grep " + _suffix
        for _cell in sorted(_cells):
            self.__node.mConnect(aHost=_cell)
            ebLogInfo("*** Executing the command in cell %s - %s" % (_cell, _cellcli_gdsize_check))
            _, _o, _e = self.__node.mExecuteCmd(_cellcli_gdsize_check)
            if _o:
                _output = _o.readlines()
                _rcode, _mismatch_string = self.mCheckGridSizeForEachDisk(_output)
                if not _rcode:
                    _rc = -1
                    self.__error_list.append(" Size Mismatch for " + _mismatch_string)
            self.__node.mDisconnect()
        ebLogInfo('*** mCheckDiskSizeMatch <<< ***')
        return _rc


    def mCheckGridSizeForEachDisk(self, aCmdOutput, aSparseVsizeFactor = 10):
        _output = aCmdOutput
        _rc = True
        _oLine_display = ""
        for _oline in _output:
            _oline = _oline.strip()
            _olineList = _oline.split()
            if len(_olineList) < 3:
                return False, _oline
            _asmSize = float(_olineList[2].strip().rstrip()[:-1]) # in MB
            _totalSize = _olineList[1].strip()
            if 'T' in _totalSize:
                _totalSize = float(_olineList[1].strip().rstrip()[:-1]) * 1024 * 1024
            elif 'G' in _totalSize:
                _totalSize = float(_olineList[1].strip().rstrip()[:-1]) * 1024
            else:
                _totalSize = float(_olineList[1].strip().rstrip()[:-1])
            if 'SPRC' in _olineList[0].strip():
                _totalSize = _totalSize * aSparseVsizeFactor
            if _asmSize != _totalSize:
                _percentage_diff = int((abs(_asmSize - _totalSize)*100)/_totalSize)
                if _percentage_diff > 2:
                    _rc = False
                    ebLogInfo("*** Percentage Difference is %s"%(str(_percentage_diff)))
                    _oLine_display = _oline
                    break
        return _rc, _oLine_display
    
class ebCluNodeSubsetPrecheck(object):

    def __init__(self, aExaBoxCluCtrl):
        self.__ebox = aExaBoxCluCtrl
        self.__error = ""
        self._optype_key = "opType"

    def mUpdateRequestData(self, rc, aData, err, aOptions):
        """
        Updates request object with the response payload
        """
        _reqobj = self.__ebox.mGetRequestObj()
        _response = {}
        _response["success"] = "True" if (rc == 0) else "False"
        _response["error"] = err
        _response["output"] = aData
        if _reqobj is not None:
            _db = ebGetDefaultDB()
            _reqobj.mSetData(json.dumps(_response, sort_keys = True))
            _db.mUpdateRequest(_reqobj)
            ebLogError(json.dumps(_response, indent=4, sort_keys=True))

        ebLogJson(json.dumps(_response, indent=4, sort_keys = True))

    def mRunNodeSubsetPrecheck(self, aOptions):
        _options = aOptions
        _inputjson = _options.jsonconf

        if _inputjson:
            if self._optype_key not in _inputjson.keys() or not _inputjson[self._optype_key]:
                _detail_error = "\'opType\' parameter is not provided. Please provide the parameter to proceed"
                self.__ebox.mUpdateErrorObject(gReshapeError['INVALID_INPUT_PARAMETER'], _detail_error)
                return 1
        else:
            _detail_error = "Missing input payload"
            self.__ebox.mUpdateErrorObject(gReshapeError['INVALID_INPUT_PARAMETER'], _detail_error)
            return 1
        _optype = _inputjson[self._optype_key]
        
        _rc = 0
        if _optype == "ADD_NODE":
            _rc = self.mAddNodePrecheck(_options)
        else:
            _detail_error = "Operation " + _optype + " is not supported. Please input a valid operation"
            self.__ebox.mUpdateErrorObject(gReshapeError['INVALID_INPUT_PARAMETER'], _detail_error)
            _rc = 1

        return _rc

    def mAddNodePrecheck(self, aOptions):
        ebLogInfo('*** Running Add Node precheck ***')
        #bug36563704 removed the call to mCheckHostImage() function from mAddNodePrecheck because the check for host image
        #on the any random dom0 was causing regression. The check for image is handled in mExecutePreVMStep function in cluelasticcompute.py 
        _rc = self.mCheckSrcNodeSpace()
        _error = self.__error
        _data = []
        if _rc == 0:
            self.mUpdateRequestData(_rc, _data, _error, aOptions)
            ebLogInfo('*** mAddNodePrecheck: Success - Add Node precheck passed')
        else:
            ebLogError('*** mAddNodePrecheck: ERROR - Add Node precheck failed')
            self.mUpdateRequestData(_rc, _data, _error, aOptions)
            self.__ebox.mUpdateErrorObject(gNodeElasticError['ERROR_NODE_SUBSET_PRECHECK'], _error)
            raise ExacloudRuntimeError(0x0809, 0xA, _error)

        return _rc

    def mCheckSrcNodeSpace(self):
        ebLogInfo('*** mCheckSrcNodeSpace>>>')
        _ebox = self.__ebox
        _rc = 0
        _,_domUs, _, _ = _ebox.mReturnAllClusterHosts()
        ebLogInfo("Checking free Space on the Source VMs to be more then a 1GB")
        for _domU in _domUs:
            _rc = self.mCheckMinDiskSpace(_domU)
            if _rc != 0:
                return _rc
        ebLogInfo('*** mCheckSrcNodeSpace <<< ***')
        return _rc    

    def mCheckMinDiskSpace(self, SrcDomU):
        ebLogInfo('*** mCheckMinDiskSpace>>>')
        _rc = 0
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=SrcDomU)
        _cmdstr = 'df /|tail -1|awk \'{print $4}\''
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if int(_out[0]) < 1000000:
            ebLogError('***** Free disk space less then 1 GB on %s' % (SrcDomU) )
            ebLogError('*** Free disk space: %d KB' % int(_out[0]))
            _rc = -1
        else:
            ebLogInfo('*** Reasonable free diskspace of %d KB on %s' % (int(_out[0]), SrcDomU) )
        _node.mDisconnect()
        ebLogInfo('*** mCheckMinDiskSpace <<< ***')
        return _rc
            

class ebCluServerSshConnectionCheck(object):

    def __init__(self, aExaBoxCluCtrl):
        self.__ebox = aExaBoxCluCtrl
        self.__error_list = []
        self.__node = exaBoxNode(get_gcontext())

    def mUpdateRequestData(self, rc, aData, err, aOptions):
        """
        Updates request object with the response payload
        """
        _reqobj = self.__ebox.mGetRequestObj()
        _response = {}
        _response["success"] = "True" if (rc == 0) else "False"
        _response["error"] = err
        _response["output"] = aData
        if _reqobj is not None:
            _db = ebGetDefaultDB()
            _reqobj.mSetData(json.dumps(_response, sort_keys = True))
            _db.mUpdateRequest(_reqobj)

        ebLogJson(json.dumps(_response, indent=4, sort_keys = True))

    def mServerSshConnectionCheck(self, aOptions, aDomUs=[], aDom0s=[], aCells=[]):
        ebLogInfo('*** mServerSshConnectionCheck >>> ***')
        _servers = aDomUs + aDom0s + aCells
        _rc = 0

        if self.__ebox.mIsOciEXACC():
            _key_only = False
        else:
            _key_only = True

        for _server in _servers:
            ebLogInfo('*** Running ssh test for server: %s ***' % (_server))
            if self.__node.mIsConnectable(aHost=_server, aKeyOnly=_key_only):
                ebLogInfo('*** Success: server %s is connectable ***' % (_server))
            else:
                ebLogError('*** Failure: server %s is not connectable ***' % (_server))
                self.__error_list.append(_server)
                _rc = 1

        _data = []
        _error = ""

        if _rc == 0:
            self.mUpdateRequestData(_rc, _data, _error, aOptions)
            ebLogInfo('*** Success: All servers passed the ssh connection test ***')
        else:
            _error = ", ".join(self.__error_list)
            _detail_error = "Following servers failed the ssh connection test: " + _error
            self.mUpdateRequestData(_rc, _data, _detail_error, aOptions)
            self.__ebox.mUpdateErrorObject(gReshapeError['ERROR_SSH_FAILURE'], _detail_error)
            raise ExacloudRuntimeError(0x0807, 0xA, _detail_error)
        
        ebLogInfo('*** mServerSshConnectionCheck <<< ***')
        return _rc


class ebCluIbSwitchSanityTests:
    def __init__(self, aCluPreCheck, aNodeInfo=None, aNodeType=None, aStep="", aPrecheckConfig=None):
        self.__precheck = aCluPreCheck
        self.__nodeInfo = aNodeInfo
        self.__nodeType = aNodeType
        self.__step = aStep
        self.__precheckConfig = aPrecheckConfig

        self.__precheck_list = []

        self.__cluctrl = self.__precheck.mGetEbox()
        self.__verbose = self.__cluctrl.mGetVerbose()

        for _key, _value in self.__precheckConfig.items():
            if _value == "True":
                self.__precheck_list.append(_key)

        self.__res = {}
        self.__error_list = []

        if self.__step == "ESTP_PREVM_CHECKS":
            self.__hostname, self.__domain = aNodeInfo.split('.', 1)
            self.__res.update( { "hostname" : self.__hostname, "domainname" : self.__domain, "hw_type" : "IBSWITCH", 'error_list' : []} )
            self.__host = self.__hostname +  '.' + self.__domain
            self.__alert_log = "ESTP_PREVM_CHECKS"
        elif self.__step == "ELASTIC_SHAPES_VALIDATION":
            self.__nodeInfo.update( {'error_list' : []} )
            self.__nodeInfo.update( {'node_type' : self.__nodeType} )
            self.__host = self.__nodeInfo['hostname'] + '.' + self.__nodeInfo['domainname']
            self.preprov = self.__nodeInfo['preprov']

            self.__alert_log = 'ELASTIC_SHAPES_VALIDATION'

        self.__node = exaBoxNode(get_gcontext())

    def run(self, aHwChecksTable={}):

        self.mPingTest()
        _status = self.__res.get("ping_test", "")
        if _status == "abnormal":
            if self.__step == "ELASTIC_SHAPES_VALIDATION":
                if self.__error_list:
                    self.__nodeInfo.update( {'error_list' : self.__error_list } )
                self.__res.update( {'node_info' : [self.__nodeInfo]} )
                # Fill multiprocess dictionary
                aHwChecksTable[self.__host] = self.__res
                # Log context for exacloud thread
                ebLogError(f"*** ERROR: host={self.__host}, step={self.__step}, result={json.dumps(self.__res)}")
                return

            if self.__step == "ESTP_PREVM_CHECKS":
                if self.__error_list:
                    self.__res.update({'error_list': self.__error_list})

            # Fill multiprocess dictionary
            _proxy_list = aHwChecksTable.get("nodes", [])
            _proxy_list.append(self.__res)
            aHwChecksTable["nodes"] = _proxy_list
            return

        self.mRunSshTest()
        _status = self.__res.get("ssh_test", "")
        if _status == "normal":
            self.__node.mConnect(aHost=self.__host)

            for _name in self.__precheck_list:
                _func_name = gPreCheckFunctionMap[_name]
                try:
                    getattr(self, _func_name)()
                except Exception as e:
                    self.__res.update({_name: 'failed'})
                    self.__error_list.append(get_hw_validate_error(92000, _name, self.__host))
                    ebLogError('*** Exception in testing  %s[%s]' % (_name, e,))
                    ebLogError(traceback.format_exc())

            self.__node.mDisconnect()
        else:
            ebLogError("*** {0}: ibswitch {1} is not connectable by SSH".format(self.__alert_log, self.__host))

        if self.__step == "ELASTIC_SHAPES_VALIDATION":
            if self.__error_list:
                self.__nodeInfo.update( {'error_list' : self.__error_list } )
            self.__res.update( {'node_info' : [self.__nodeInfo]} )
            # Fill multiprocess dictionary
            aHwChecksTable[self.__host] = self.__res
            return

        if self.__step == "ESTP_PREVM_CHECKS":
            if self.__error_list:
                self.__res.update({'error_list': self.__error_list})

        # Fill multiprocess dictionary
        _proxy_list = aHwChecksTable.get("nodes", [])
        _proxy_list.append(self.__res)
        aHwChecksTable["nodes"] = _proxy_list
        return

    def mRemoteExecute(self, aCmd):
        _cmd_str = aCmd
        _i, _o, _e = self.__node.mExecuteCmd(_cmd_str)
        _out = [_line.strip() for _line in _o.readlines()]
        return _out

    def mPingTest(self):
        if not self.__cluctrl.mPingHost(self.__host):
            ebLogError('*** {0}: Host {1} is not pingable.'.format(self.__alert_log, self.__host))
            self.__res.update( {'ping_test' : 'abnormal'} )
            self.__error_list.append(get_hw_validate_error(92001, "ping_test", self.__host))
        else:
            self.__res.update( {'ping_test' : 'normal'} )
            ebLogInfo("*** {0}: PING_TEST on ibswitch:{1} is normal".format(self.__alert_log, self.__host))

    def mRunSshTest(self):
        if self.__cluctrl.mIsOciEXACC():
            _key_only = False
        else:
            _key_only = True

        if self.__node.mIsConnectable(aHost=self.__host, aKeyOnly=_key_only):
            self.__res.update( {'ssh_test' : 'normal'} )
            ebLogInfo("*** {0}: SSH_TEST on ibswitch:{1} is normal".format(self.__alert_log, self.__host))
        else:
            ebLogError("*** {0}: SSH_TEST on ibswitch:{1} is abnormal".format(self.__alert_log, self.__host))
            self.__res.update( {'ssh_test' : 'abnormal'} )
            self.__error_list.append(get_hw_validate_error(92002, "ssh_test", self.__host))

    def mRunHWTest(self):
        _cmd_str = "env_test | grep -E 'Voltage test returned|PSU test returned|Temperature test returned|FAN test returned|Connector test returned|Onboard ibdevice test returned|SSD test returned|Auto-link-disable test returned'"
        _output = self.mRemoteExecute(_cmd_str)
        _error_code = {
            'psu': 92005,
            'temperature':92006,
            'fan': 92004,
            'onboard ibdevice': 92003
        }
        if _output or len(_output):
            for _line in _output:
                _key = _line.split('test returned')[0].strip().lower()
                _ret = _line.split('test returned')[-1].strip()
                _value = 'normal' if _ret in ['OK'] else 'abnormal'
                if _value == 'normal':
                    ebLogInfo("*** {0}: {1} test on ibswitch {2} returned success".format(self.__alert_log, _key.upper(), self.__host))
                else:
                    if "auto-link-disable" in _line.lower():
                        ebLogWarn('*** %s: %s on switch %s' % (self.__alert_log, _line, self.__host))
                        continue
                    else:
                        ebLogError("*** {0}: {1} test on ibswitch {2} returned failure".format(self.__alert_log, _key.upper(), self.__host))
                        self.__error_list.append(get_hw_validate_error( _error_code.get(_key, 92032), _key, self.__host))
                self.__res.update( {_key : _value} )

def mGetDom0sImagesListSorted(aExaBoxCluCtrlObj) -> List[str]:
    """
    Returns a sorted list of strings identifying the image versions in asc order
    """
    _ebox = aExaBoxCluCtrlObj
    # Get Minimal Version
    _minV = sorted(
        [_ebox.mGetImageVersion(_dom0) for _dom0, _ in _ebox.mReturnDom0DomUPair()], 
        key=cmp_to_key(version_compare))
    ebLogDebug(f'mGetDom0sImagesListSorted returns {_minV}')
    return _minV

def mWaitForSystemBoot(aNode: exaBoxNode) -> None:
    """
    This function will wait until the system boot finishes.
    We rely on systemd for this


    :param aNode: an exaBoxNode already connected

    :returns None:
    """

    _bin_systemd_analyze = node_cmd_abs_path_check(aNode, "systemd-analyze", sbin=True)
    _cmd = f"{_bin_systemd_analyze} time"
    _rc = 1

    ebLogInfo(f"Checking if system is not booting up: {aNode.mGetHostname()}")
    while _rc:
        ebLogTrace(f"Retrying in 5 seconds...: {aNode.mGetHostname()}")
        time.sleep(5)
        _out_boot = node_exec_cmd(aNode, _cmd)
        _rc = _out_boot.exit_code

        # If systemd-analyze doesn't signal any ongoing reboot, we also
        # check for elasticConfig processes that may be running.
        # If any we assume a reboot is ongoing and we wait
        if not _rc:
            _list_proc = node_list_process(aNode, "firstconf/elasticConfig.sh")
            if _list_proc:
                ebLogWarn(f"We detected an elasticConfig process ongoing:\n "
                    f"{_list_proc} in {aNode.mGetHostname()}, we'll wait "
                    "for those processes to finish")
                _rc = 1
            else:
                ebLogInfo(f"No elasticConfig process found in "
                    f"{aNode.mGetHostname()}")


    ebLogInfo(f"System boot up has completed on {aNode.mGetHostname()}")


class ebCopyDBCSAgentpfxFile:
    """Copy the corresponding domU dbcsagent p12 certificate during Create Service and Add Node 
    """

    def __init__(self, aExaBoxCluCtrlObj):
        self._ebox = aExaBoxCluCtrlObj
        self._cert_destination_dir = '/opt/oracle/dcs/auth'
        self._dbcs_agent_user = 'opc'
        self._dbcs_agent_group = 'opc'
        self._cluster_name = self._ebox.mGetClusterName()
        self._dbcs_files = self.get_dbcs_files()
            
    def get_dbcs_files(self):
        """
        For OC1 region two new files will be generated
        dbcsagent_keystore.pfx and
        dbcsagent_truststore.pfx

        Exacloud needs to copy both these files to /opt/oracle/dcs/auth folder.
        To maintain backward compatibility if these 2 files aren't present then 
        copy dbcsagent.pfx to dom-u 
        """
        if self._ebox.mIsFedramp():
            return {f'/opt/oci/exacc/certs/dbcsagent/dbcsagent_keystore_{self._cluster_name}.p12' : f'{self._cert_destination_dir}/dbcsagent_keystore.pfx', 
                    '/etc/pki/ociexacc/cacert.pfx' : f'{self._cert_destination_dir}/dbcsagent_truststore.pfx'}
            
        else:
            # check if dbcsagent_keystore.pfx and dbcsagent_truststore.pfx files exist
            _files = {f'/opt/oci/exacc/certs/dbcsagent/dbcsagent_keystore.pfx' : f'{self._cert_destination_dir}/dbcsagent_keystore.pfx', 
                    '/opt/oci/exacc/certs/dbcsagent/dbcsagent_truststore.pfx' : f'{self._cert_destination_dir}/dbcsagent_truststore.pfx'}
            _keystore_truststore_file_exists = True
            for _file in _files:
                if not os.path.isfile(_file):
                    ebLogError(f'*** Source dbcsagent pfx file {_file} does not exist ! ')
                    _keystore_truststore_file_exists = False
            if _keystore_truststore_file_exists:
                return _files
            # fallback on default
            return {'/opt/oci/exacc/websocket/wsclient/certs/client/dbcsagent.pfx': f'{self._cert_destination_dir}/dbcsagent.pfx'}                

    def execute_command(self, nodeU, command):
        nodeU.mExecuteCmdLog(command)
        return nodeU.mGetCmdExitStatus()

    def setup_directory(self, nodeU):
        commands = [
            f'/bin/mkdir -p {self._cert_destination_dir}',
            f'/bin/chmod 700 {self._cert_destination_dir}',
            f'/bin/chown {self._dbcs_agent_user}:{self._dbcs_agent_group} {self._cert_destination_dir}'
        ]

        for command in commands:
            exit_status = self.execute_command(nodeU, command)
            if exit_status:
                return exit_status
        return 0

    def setup_pfx_directory(self, nodeU, domU):
        exit_status = self.setup_directory(nodeU)
        if exit_status:
            ebLogError(f'*** Failed to setup pfx directory {self._cert_destination_dir} on {domU}')
            raise ExacloudRuntimeError(0x0819, 0xA, 'Directory setup failed on domU')
        ebLogInfo(f'*** pfx directory {self._cert_destination_dir} properly setup on {domU}')

    def copy_file(self, nodeU, domU, aSourceFile, aDestinationFile):
        _source_file = aSourceFile
        _destination_file = aDestinationFile
        ebLogInfo(f'*** Copying {_source_file} to {_destination_file} on {domU}')
        nodeU.mCopyFile(_source_file, _destination_file)
        if not nodeU.mFileExists(_destination_file):
            ebLogError(f'*** Copying {_source_file} to {_destination_file} on {domU} failed')
            raise ExacloudRuntimeError(0x0819, 0xA, 'Certificate copy failed to domU')
        ebLogInfo(f'*** Copying {_source_file} to {_destination_file} on {domU} successful')

    def setup_file_permissions(self, nodeU, domU, aDestinationFile):
        _destination_file = aDestinationFile
        commands = [
            f'/bin/chmod 600 {_destination_file}',
            f'/bin/chown {self._dbcs_agent_user}:{self._dbcs_agent_group} {_destination_file}'
        ]

        for command in commands:
            exit_status = self.execute_command(nodeU, command)
            if exit_status:
                ebLogError(f'*** Failed to assign permission/ownership for pfx files {_destination_file} on {domU}')
                ebLogTrace(f'*** Removing pfx file {_destination_file} on {domU} to avoid security breaches.')
                nodeU.mExecuteCmdLog(f'/bin/rm -f {_destination_file}')
                raise ExacloudRuntimeError(0x0819, 0xA, 'Failed to assign permission to certificate')

        ebLogInfo(f'*** Permission assigned successfully to {_destination_file}')

    def setup_pfx_files(self):
        for _, domU in self._ebox.mReturnDom0DomUPair():
            with connect_to_host(domU, get_gcontext(), username='root') as nodeU:
                self.setup_pfx_directory(nodeU, domU)
                for _source_file, _destination_file in self._dbcs_files.items():
                    if not os.path.isfile(_source_file):
                        ebLogError(f'*** source dbcsagent pfx file {_source_file} does not exist.')
                        raise ExacloudRuntimeError(0x0819, 0xA, 'Certificate Missing!')
                    self.copy_file(nodeU, domU, _source_file, _destination_file)
                    self.setup_file_permissions(nodeU, domU, _destination_file)
    
    def mCopyDbcsAgentpfxFiletoDomUsForFedramp(self):
        try:
            self.setup_pfx_files()
        except Exception as e:
            ebLogError(f'*** Fatal Error *** : Error while copying the dbcsagent pfx file to respective domU, {e}')
            raise ExacloudRuntimeError(0x0819, 0xA, 'Certificate Copy Failed')


class ebCluEthernetConfig:
    """ 
    """
    def __init__(self, aCluCtrlObj, aOptions):
        self.__cluctrl = aCluCtrlObj
        self.__options = aOptions

    def mSplitLinkMode(self, aModes):
        _modes = aModes
        _speeds = []

        #Supported link modes/Advertised link modes will be in Format '100000baseLR2_ER2_FR2/Full', '100000baseDR2/Full'
        for _mode_str in _modes:
            if 'base' in _mode_str.lower():
                _speed, _mode = _mode_str.split('base')
            else:
                _speed = 0
            _speeds.append(int(_speed))
        return _speeds

    def mGetSupportedSpeeds(self, aData):
        _data = aData
        _advertise_modes = []
        _supported_modes = []
        for _index, _output in enumerate(_data):
            if 'Supported link modes:' in _output:
                _supported_modes.append(_output.split(':')[1].strip())
                _flag = False
                _idx = _index
                while not _flag:
                    _idx = _idx + 1
                    _flag = ':' in _data[_idx]
                    if _data[_idx] and not _flag:
                        _supported_modes.append(_data[_idx].strip())
            elif 'Advertised link modes:' in _output:
                _advertise_modes.append(_output.split(':')[1].strip())
                _flag = False
                _idx = _index
                while not _flag:
                    _idx = _idx + 1
                    _flag = ':' in _data[_idx]
                    if _data[_idx] and not _flag:
                        _advertise_modes.append(_data[_idx].strip())
        ebLogTrace(f"Advertised Modes:{_advertise_modes} Supported Modes:{_supported_modes}")
        return _advertise_modes, _supported_modes

    def mSetCustomSpeed(self, aNode, aEthx, aCurrSpeed, aOptSpeed, aExadataModel=None):
        _rc = 0
        _node: exaBoxNode = aNode
        _ethx: str = aEthx
        _dom0: str = _node.mGetHostname()
        _curr_speed = aCurrSpeed
        _opt_speed = aOptSpeed
        _exadata_model = aExadataModel

        ebLogInfo(f"{_dom0}: Setting Custom link speed {_opt_speed} in interface {_ethx} ")
        if mCompareModel(_exadata_model, "X9") >= 0:
            _cmd_str = f"/usr/sbin/ethtool -s {_ethx} speed {_opt_speed} autoneg on"
            _node.mExecuteCmd(_cmd_str)
        else:
            _cmd_str = f"/usr/sbin/ethtool -s {_ethx} speed {_opt_speed} autoneg off"
            _node.mExecuteCmd(_cmd_str)
        time.sleep(30)

        _rc = _node.mGetCmdExitStatus()
        if _rc != 0:
            _node.mDisconnect()
            raise ExacloudRuntimeError(f"Error while executing command: {_cmd_str}")
        
        #Retrieve the current link speed after applying the custom link speed.
        _curr_speed = self.mGetCurrentSpeed(_node, _ethx)
        _count = 0
        while _curr_speed != _opt_speed and _count < 5:
            _count = _count + 1
            time.sleep(60)
            _curr_speed = self.mGetCurrentSpeed(_node, _ethx)
            ebLogTrace(f"{_dom0}: Attempt {_count} : expected={_opt_speed}, current={_curr_speed}")
            if _curr_speed == -1:
                if _count < 5:
                    ebLogTrace(f"{_dom0}: {_ethx} speed is still -1, reporting as unknown/unresolved, retrying...")

        ebLogInfo(f"{_dom0}: Custom link speed {_curr_speed} updated in {_ethx} interface")
        _rc = 0 if _curr_speed == _opt_speed else -1
        return _rc

    def mGetCurrentSpeed(self, aNode, aEthx):
        _node: exaBoxNode = aNode
        _ethx: str = aEthx
        _, _o, _ = _node.mExecuteCmd(f"/bin/cat /sys/class/net/{_ethx}/speed")
        _out = _o.readlines()
        _current_speed = int(_out[0].strip())
        ebLogTrace(f"/bin/cat /sys/class/net/%s/speed output is %s {_current_speed}")       
        return _current_speed

    def mValidateInterface(self, aNode, aEthx, aOptSpeed=None):
        _node: exaBoxNode = aNode
        _ethx: str = aEthx
        _dom0: str = _node.mGetHostname()
        _opt_speed = aOptSpeed

        # If bonding is not enabled for this node, then we can ignore the
        # interfaces which id parity do not match with the node's id parity.
        if self.__cluctrl.mIssueSoftWarningOnLinkfailure(_dom0, _ethx):
            return True

        # Validate if interface is up
        _, _o_operstate, _ = _node.mExecuteCmd(f"/bin/cat /sys/class/net/{_ethx}/operstate")
        _out_operstate = _o_operstate.read()
        if "down" in _out_operstate:
            # if interface is down, trying to bring it up
            _node.mExecuteCmdLog(f"/sbin/ip link set {_ethx} up")
            # Obtaining again tha status of the interface
            _, _o_operstate, _ = _node.mExecuteCmd(f"/bin/cat /sys/class/net/{_ethx}/operstate")
            _out_operstate = _o_operstate.read()

        if "up" in _out_operstate:
            ebLogInfo(f"{_ethx} link is up in {_dom0}")

            _rc = True
            if _opt_speed:
                _, _o, _ = _node.mExecuteCmd(f"/bin/cat /sys/class/net/{_ethx}/speed")
                _out = _o.readlines()
                ebLogTrace("/bin/cat /sys/class/net/%s/speed output is %s"%(_ethx,str(_out)))
                _curr_speed = int(_out[0].strip())
                ebLogInfo(f"{_dom0}: {_ethx} interface has link speed {_curr_speed}")

                _rc = True if _curr_speed == _opt_speed else False

            return _rc
        else:
            _msg = f"Interface {_ethx} is down in {_dom0} and it was not possible to bring it up"
            ebLogWarn(_msg)

    def mUpdateCustomEthernetSpeed(self, aNode, aDom0, aEthx, aCurrSpeed, aExadataModel=None):
        _node = aNode
        _dom0 = aDom0
        _ethx = aEthx
        _current_speed = aCurrSpeed
        _exadata_model = aExadataModel

        self.mValidateInterface(_node, _ethx)
        if self.__cluctrl.mCompareExadataModel(_exadata_model, 'X10') >= 0:
            _optimum_speed = 100000
        elif _exadata_model == "X9":
            _optimum_speed = 50000
        else:
            _optimum_speed = 25000

        _, _o, _ = _node.mExecuteCmd(f"/usr/sbin/ethtool {_ethx} ")
        _out = _o.readlines()

        _link_modes = []
        _advertise_modes, _supported_modes = self.mGetSupportedSpeeds(_out)
        if 'Not reported' in _advertise_modes:
            _link_modes.extend(_supported_modes)
            ebLogTrace(f"Supported link modes {_link_modes}")
        else:
            _link_modes.extend(_advertise_modes)
            ebLogTrace(f"Advertised link modes:{_link_modes}")

        #Check advertise mode present in supported modes, if present set the value
        _rc = -1
        if _link_modes and _supported_modes:
            _link = list(set(self.mSplitLinkMode(_link_modes)))
            _link_speeds = sorted(_link, reverse=True)
            ebLogInfo(f"Advertised link speeds:{_link_speeds}")

            _supported = list(set(self.mSplitLinkMode(_supported_modes)))
            _supported_speeds = sorted(_supported, reverse=True)
            ebLogInfo(f"Supported link speeds {_supported_speeds}")

            for _speed in _link_speeds:
                if _speed in _supported_speeds:
                    _optimum_speed = _speed
                    _rc = self.mSetCustomSpeed(_node, _ethx, _current_speed, _optimum_speed, _exadata_model)
                    if _rc == 0:
                        break
        #Set default custom speed
        if _rc == -1:
            if self.__cluctrl.mCompareExadataModel(_exadata_model, 'X10') >= 0:
                _optimum_speed = 100000
            elif _exadata_model == "X9":
                _optimum_speed = 50000
            else:
                _optimum_speed = 25000
            _rc = self.mSetCustomSpeed(_node, _ethx, _current_speed, _optimum_speed, _exadata_model)
        _, _o, _ = _node.mExecuteCmd(f"cat /sys/class/net/{_ethx}/speed")
        _out = _o.readlines()
        ebLogTrace("cat /sys/class/net/%s/speed output is %s"%(_ethx,str(_out)))
        _current_speed = int(_out[0].strip())
        ebLogInfo(f"{_dom0}: updated link speed to {_current_speed} in interface {_ethx} ")

        if _current_speed != _optimum_speed:
            _err = f"Speed of ethernet interface {_ethx} not correctly set"
            ebLogError(f"{_dom0}: {_err}")
            # In production env, if speed is not correctly speed,
            # raise an exception.
            if self.__cluctrl.mEnvTarget() == True:
                _node.mDisconnect()
                raise ExacloudRuntimeError(0x0128, 0x0A, _err)

class ebCluStartStopHostFromIlom(object):
    def __init__(self, aExaBoxCluCtrl):
        self.__ebox = aExaBoxCluCtrl
        
    def mExecuteIlomCmd(self, _cmds, IlomName):
        """
        This function executes the commands formulated on the iloms 
        and prints the console raw output.
        """
        _lastpwd = self.__ebox.mGetIlomPass()
        _ilomName = IlomName
        _maxTries = 3
        _tries    = 0
 
        while _tries < _maxTries:
    
            if _tries != 0:
                _lastpwd = getpass.getpass("Password for {0}: ".format(_ilomName))
    
            try:
                _node = exaBoxNode(get_gcontext())
                _node.mSetUser("root")
                _node.mSetPassword(_lastpwd)
    
                ebLogInfo("Try authentication: {0}".format(_ilomName))
                _node.mConnectAuthInteractive(aHost=_ilomName)
    
                _node.mExecuteCmdsAuthInteractive(_cmds)
                ebLogInfo("Read from socket: [{0}]".format(_node.mGetConsoleRawOutput()))
    
                _node.mDisconnect()
                break
    
            except Exception as e:
                ebLogInfo(f"Execution of Ilom command failed with exception: {str(e)}")
                _tries += 1
                    
    def mStopHostfromIlom(self, IlomName, aGracefulShutdown=True):
        _cmds = []
        if aGracefulShutdown:
            _cmds.append(['->', 'stop /System'])
        else:
            _cmds.append(['->', 'stop -f /System'])
        _cmds.append(['->', 'show /System'])
        self.mExecuteIlomCmd(_cmds, IlomName)
    
    def mStartHostfromIlom(self, IlomName):
        _cmds = []
        _cmds.append(['->', 'start /System'])
        _cmds.append(['->', 'show /System'])
        self.mExecuteIlomCmd(_cmds, IlomName)
        
    def mProcessHostLifecycle(self, ctx: dict):
        """
        Handles host lifecycle via ILOM for both 'start' and 'stop'.
        Accepts a dictionary with keys: host, ilom, operation, sleep_time, results_dict.
        """
        _host = ctx.get("host")
        _ilom = ctx.get("ilom")
        _operation = ctx.get("operation")
        _timeout = ctx.get("sleep_time")
        _results_dict = ctx.get("results_dict")

        if not all([_host, _ilom, _operation, _timeout is not None, _results_dict is not None]):
            msg = (f"Invalid lifecycle context: missing required keys or values. "
                   f"Context = {{'host': {_host}, 'ilom': {_ilom}, "
                   f"'operation': {_operation}, 'sleep_time': {_timeout}, 'results_dict': {_results_dict}}}")
            ebLogError(msg)
            raise ExacloudRuntimeError(0x0208, 0xA, msg)

        if _operation not in ("start", "stop"):
            msg = f"Failed: Invalid operation '{_operation}' for host {_host}"
            _results_dict[_host] = msg
            ebLogError(msg)
            raise ExacloudRuntimeError(0x0208, 0xA, msg)

        ebLogInfo(f"Operation {_operation} to be performed on host {_host} via ilom {_ilom}")

        # Trigger the appropriate ILOM action
        if _operation == "stop":
            self.mStopHostfromIlom(_ilom)
        else:
            self.mStartHostfromIlom(_ilom)

        # For start, give the host a short grace period to POST/boot before ping checks
        if _operation == "start":
            ebLogInfo(f"Waiting for the host {_host} to start up..")
            ebLogTrace("Waiting for 30 seconds first for the host to start up.")
            time.sleep(10)
        else:
            ebLogInfo(f"Waiting for the host {_host} to be shutdown..")

        _start_ts = time.time()

        # Desired ping state:
        #   stop  -> expect ping to be False (down)
        #   start -> expect ping to be True  (up)
        def _is_desired_state() -> bool:
            ping = self.__ebox.mPingHost(_host)
            return (not ping) if _operation == "stop" else ping

        while True:
            _elapsed = time.time() - _start_ts

            if _is_desired_state():
                _results_dict[_host] = "Success"
                if _operation == "stop":
                    ebLogInfo(
                        f"Host {_host} not pingeable after {_operation} from ilom and {_elapsed} seconds wait time")
                else:
                    ebLogInfo(f"Host {_host} pingeable after {_operation} from ilom and {_elapsed} seconds wait time")
                break

            if _elapsed > _timeout:
                msg = (f"Failed: Timeout while waiting for host {_host} to be "
                       f"{'stopped' if _operation == 'stop' else 'started'}.")
                _results_dict[_host] = msg
                ebLogError(msg)
                break

            ebLogTrace(f"Waiting for host {_host} to be "
                       f"{'stopped' if _operation == 'stop' else 'started'} : {_elapsed}")
            time.sleep(10)

    def mStopStartHostViaIlom(self, aOptions):
        if not aOptions or not aOptions.jsonconf:
            _err_str = "Please provide valid json input."
            ebLogError(_err_str)
            raise ExacloudRuntimeError(0x0207, 0xA, _err_str)

        _json = aOptions.jsonconf
        _operation = _json.get("operation")
        _parallelprocess = bool(_json.get("parallel_process", False))
        _host_ilom_pair = _json.get("host_ilom_pair")

        if _operation not in ("start", "stop"):
            _err_str = "Invalid operation provided in the payload."
            ebLogError(_err_str)
            raise ExacloudRuntimeError(0x0207, 0xA, _err_str)

        if not _host_ilom_pair:
            _err_str = "Host and Ilom information not present in input payload."
            ebLogError(_err_str)
            raise ExacloudRuntimeError(0x0207, 0xA, _err_str)

        _sleep_time = STOP_SLEEP_TIME_FROM_ILOM if _operation == "stop" else START_SLEEP_TIME_FROM_ILOM
        _rc_final_result = {}

        if _parallelprocess:
            _items = list(_host_ilom_pair.items())
            for i in range(0, len(_items), 5):
                _batch_pairs = dict(_items[i:i + 5])
                _plist = ProcessManager()
                _rc_result = _plist.mGetManager().dict()

                for _host, _ilom in _batch_pairs.items():
                    ctx = {
                        "host": _host,
                        "ilom": _ilom,
                        "operation": _operation,
                        "sleep_time": _sleep_time,
                        "results_dict": _rc_result
                    }
                    _p = ProcessStructure(self.mProcessHostLifecycle, [ctx], _host)
                    _p.mSetMaxExecutionTime(10 * 60)
                    _p.mSetJoinTimeout(5)
                    _p.mSetLogTimeoutFx(ebLogWarn)
                    _plist.mStartAppend(_p)

                _plist.mJoinProcess()
                _rc_result = dict(_rc_result)

                for _host, _rcs in _rc_result.items():
                    ebLogInfo(f"{_operation.capitalize()} status for {_host} : {_rcs}")
                _rc_final_result.update(_rc_result)

        else:
            _rc_result = {}
            for _host, _ilom in _host_ilom_pair.items():
                ctx = {
                    "host": _host,
                    "ilom": _ilom,
                    "operation": _operation,
                    "sleep_time": _sleep_time,
                    "results_dict": _rc_result
                }
                self.mProcessHostLifecycle(ctx)

            for _host, _rcs in _rc_result.items():
                ebLogInfo(f"{_operation.capitalize()} status for {_host} : {_rcs}")
            _rc_final_result.update(_rc_result)

        return _rc_final_result


class ebCluRestartVmExacsService:
    """
    To restart vmexacs_kvm service at the end of patching if libvirtd service is up
    """
    def __init__(self, aExaBoxCluCtrlObj):
        self.__ebox = aExaBoxCluCtrlObj

    def mGetPropertyVal(self, output):
        """
        parameter -> ActiveState=active
        returns active
        """
        output = output.strip()
        return output.split("=", 1)[1]

    def mRestartVmExacsService(self, aDom0, _max_retry):
        _retry_count = 1
        with connect_to_host(aDom0, get_gcontext()) as _node:
            while _retry_count <= _max_retry:
                _cmd = "systemctl is-active libvirtd.service"
                _libvirtd_state = _node.mSingleLineOutput(_cmd)
                _cmd = "systemctl show vmexacs_kvm --property=ActiveState"
                _vmexacs_kvm_state = self.mGetPropertyVal(_node.mSingleLineOutput(_cmd))
                _cmd = "systemctl show vmexacs_kvm --property=SubState"
                _vmexacs_kvm_substate = self.mGetPropertyVal(_node.mSingleLineOutput(_cmd))

                # restart vmexacs_kvm service when libvirt is "active" and vmexacs_kvm service not in "active (running) state"
                if _libvirtd_state == "active":
                    if not (_vmexacs_kvm_state == "active" and _vmexacs_kvm_substate == "running"):
                        ebLogInfo(f"libvirtd service is active and running, and vmexacs_kvm is: {_vmexacs_kvm_state} ({_vmexacs_kvm_substate}) , restarting vmexacs_kvm service on {aDom0}")
                        _cmd = "systemctl restart vmexacs_kvm"
                        _node.mExecuteCmdLog(_cmd)
                        _rc = _node.mGetCmdExitStatus()
                        if _rc == 0:
                            ebLogInfo(f"vmexacs_kvm services successfully restarted on DOM0:{aDom0}")
                        else:
                            ebLogWarn(f"vmexacs_kvm services didn't restart on DOM0:{aDom0}")
                        
                        return
                    else:
                        ebLogInfo(f"libvirtd service is active and running, and vmexacs_kvm is: {_vmexacs_kvm_state} ({_vmexacs_kvm_substate}) state, on {aDom0}")
                        return
                else:
                    ebLogWarn(f"libvirt service is in {_libvirtd_state} state on DOM0:{aDom0}. Waiting for libvirt service to be active. Retry No. {_retry_count}")
                    _retry_count += 1
                    time.sleep(RETRY_WAIT_TIME)
        return

    def mPostPatchingRestartVmExacsService(self):

        with self.__ebox.remote_lock():
            for _dom0, _ in self.__ebox.mReturnDom0DomUPair():
                if self.__ebox.mIsKVM() and self.__ebox.mIsHostOL8(_dom0):
                    self.mRestartVmExacsService(_dom0, MAX_RETRY)


class ebMigrateUsersUtil:

    def __init__(self, aClubox):
        self.__clubox = aClubox

    def _is_dbmcli_running(self, aNode):
        _node = aNode
        #dbmcli -e
        # The service returns an output similar to below.
        # This output is checked via grep and that's why a process count of 2
        # means that the service is running
        # msStatus:               running
        # rsStatus:               running

        ebLogInfo("*** Checking status of dbmcli services ***")
        _cmd = "/usr/bin/dbmcli -e list dbserver detail"
        _, _o, _e = _node.mExecuteCmd(_cmd)
        _rc = _node.mGetCmdExitStatus()

        _dbmcli_output = "".join(_o.readlines())

        # dbmcli status return code is 1 when services are not running
        _not_running_pattern = ":\s+Connect Error"
        # The output when services are running looks like:
        # DBM-01514: Connect Error. Verify that Management Server is listening at the specified HTTP port: 7878.
        # msStatus:               unknown
        # rsStatus:               stopped

        if _rc != 0 and not re.findall(_not_running_pattern,_dbmcli_output):
            _msg = "Could not verify if dbmcli services are running. Command:{0}:\n{1}".format(_cmd,"\n".join(_o.readlines()))
            ebLogError(f"*** {_msg} ***")
            raise ExacloudRuntimeError(0x0760, 0xA, _msg)

        _ms_pattern = "msStatus:\s+running"
        _rs_pattern = "rsStatus:\s+running"

        if re.search(_ms_pattern,_dbmcli_output) and re.search(_rs_pattern,_dbmcli_output):
            return True

        return False

    def _is_esnp_running(self, aNode):

        ebLogInfo("*** Checking status of ESNP service ***")

        _cmd = "/usr/bin/dbmcli -e list dbserver detail"
        _, _o, _ = aNode.mExecuteCmd(_cmd)

        _dbmcli_output = _o.read()
        ebLogInfo(_dbmcli_output)

        _esnp_pattern = "esnpStatus:\s+running"

        if re.search(_esnp_pattern,_dbmcli_output): 
            return True

        return False


    def mGetUidFromFile(self, aNode, aFile):

        _ids = {}
        _, _o, _e = aNode.mExecuteCmd(f"/bin/cat {aFile}")

        if aNode.mGetCmdExitStatus() != 0:
            ebLogError(f"Error while read file {aFile}")
            ebLogError(_e.read())
            raise OSError

        for _record in _o.readlines():
            _ids[_record.split(":")[0]] = int(_record.split(":")[2])

        return _ids

    def mGetCustomUserGroupsConfigFile(self):

        # Get User Info file
        _userConfigFile = os.path.abspath(str(self.__clubox.mCheckConfigOption("user_config_file")))
        _usrConfig = {}

        if os.path.exists(_userConfigFile):
            with open(_userConfigFile, "r") as _f:
                _usrConfig = json.load(_f)

        return _usrConfig

    def mGetCustomUserGroupsPayload(self):

        CUSTOMUSERS = 'users_with_custom_id'
        CUSTOMGROUPS = 'groups_with_custom_id'

        _usrConfig = {}
        _users = None
        _groups = None

        _override = self.__clubox.mCheckConfigOption("override_userconfig_from_payload")
        if _override == "True":

            _jconf = {}
            if self.__clubox.mGetOptions():
                _jconf = self.__clubox.mGetOptions().jsonconf

            if _jconf and CUSTOMUSERS in list(_jconf.keys()):
                #Check in main section
                _users = _jconf[CUSTOMUSERS]
            if _jconf and CUSTOMGROUPS in list(_jconf.keys()):
                _groups = _jconf[CUSTOMGROUPS]

            if _jconf and 'vm' in list(_jconf.keys()):
            #Check in vm section
                if CUSTOMUSERS in list(_jconf['vm'].keys()):
                    _users = _jconf['vm'][CUSTOMUSERS]
                if CUSTOMGROUPS in list(_jconf['vm'].keys()):
                    _groups = _jconf['vm'][CUSTOMGROUPS]

            if _users is not None:
                for _user in _users:
                    ebLogInfo(f"*** mUpdateUserConfiguration: user: {_user['user']}, uid:{_user['uid']}")
                    _usrConfig[_user['user']] = {}
                    _usrConfig[_user['user']]['uid'] = _user['uid']

            if _groups is not None:
                for _group in _groups:
                    ebLogInfo(f"*** mUpdateUserConfiguration: group: {_group['group']}, gid:{_group['gid']}")
                    _usrConfig[_group['group']] = {}
                    _usrConfig[_group['group']]['gid'] = _group['gid']

        return _usrConfig

    def mGetUsersGroupsToRemap(self, aNode):
        """
        https://confluence.oraclecorp.com/confluence/display/SSOCI/Access+Updater
        """

        _toRemap = {}

        if not self.__clubox.mIsAdbs() and not self.__clubox.isATP() and not self.__clubox.IsZdlraProv():
            ebLogInfo("Users and Groups outside range is only supported in ADB-S, ADB-D and Zdlra")
            return _toRemap

        # Get users to remap
        _ids = self.mGetUidFromFile(aNode, "/etc/passwd")

        _maxId = 0
        for _name, _id in _ids.items():
            if (_id >= 3000 and _id <= 65533) or (_id >= 65535 and _id <= 120000):
                if _name not in _toRemap:
                    _toRemap[_name] = {"uid": _id}
                else:
                    _toRemap[_name]["uid"] = _id
            else:
                if not (_id >= 3000 and _id <= 120000):
                    _maxId = max(_maxId, _id)
        _maxId += 1

        for _name in _toRemap.keys():
            if "uid" in _toRemap[_name]:
                ebLogInfo(f"mGetUsersGroupsToRemap: User: {_name}, original: {_toRemap[_name]['uid']}, suggested: {_maxId}")
                _toRemap[_name]["uid"] = _maxId
                _maxId += 1

        # Get groups to remap
        _ids = self.mGetUidFromFile(aNode, "/etc/group")

        _maxId = 0
        for _name, _id in _ids.items():
            if (_id >= 4000000 and _id <= 2147483647):
                if _name not in _toRemap:
                    _toRemap[_name] = {"gid": _id}
                else:
                    _toRemap[_name]["gid"] = _id
            else:
                _maxId = max(_maxId, _id)
        _maxId += 1

        for _name in _toRemap.keys():
            if "gid" in _toRemap[_name]:
                ebLogInfo(f"mGetUsersGroupsToRemap: Group: {_name}, original: {_toRemap[_name]['gid']}, suggested: {_maxId}")
                _toRemap[_name]["gid"] = _maxId
                _maxId += 1

        return _toRemap

    def mMergeUsersGroupsConfigPayload(self):

        _toRemap = {}
        _configMap = self.mGetCustomUserGroupsConfigFile()
        _payloadMap = self.mGetCustomUserGroupsPayload()

        ebLogInfo(f"Config UserGroups: {_configMap}")
        ebLogInfo(f"Payload UserGroups: {_payloadMap}")

        for _name in _configMap:
            if _name not in _toRemap:
                _toRemap[_name] = {}
            if "uid" in _configMap[_name]:
                _toRemap[_name]["uid"] = _configMap[_name]["uid"]
            if "gid" in _configMap[_name]:
                _toRemap[_name]["gid"] = _configMap[_name]["gid"]

        for _name in _payloadMap:
            if _name not in _toRemap:
                _toRemap[_name] = {}
            if "uid" in _payloadMap[_name]:
                _toRemap[_name]["uid"] = _payloadMap[_name]["uid"]
            if "gid" in _payloadMap[_name]:
                _toRemap[_name]["gid"] = _payloadMap[_name]["gid"]

        ebLogInfo(f"UserGroups from Config and Payload: {_toRemap}")
        return _toRemap


    def mMergeUsersGroupsToRemap(self, aNode):

        _toRemap = self.mGetUsersGroupsToRemap(aNode)
        _configMap = self.mMergeUsersGroupsConfigPayload()

        for _name in _configMap:
            if _name not in _toRemap:
                _toRemap[_name] = {}
            if "uid" in _configMap[_name]:
                _toRemap[_name]["uid"] = _configMap[_name]["uid"]
            if "gid" in _configMap[_name]:
                _toRemap[_name]["gid"] = _configMap[_name]["gid"]

        ebLogInfo(f"Final UserGroups: {_toRemap}")
        return _toRemap


    def mCreateMissingUsersGroups(self, aNode, aToRemap):

        for _name, _configU in aToRemap.items():

            if "gid" in _configU:
                aNode.mExecuteCmd(f"/bin/cat /etc/group | /bin/grep {_name}")
                if aNode.mGetCmdExitStatus() != 0:
                    ebLogInfo(f"Creating missing group: {_configU['gid']} {_name}")
                    _cmd = f"/usr/sbin/groupadd -g {_configU['gid']} {_name}"
                    aNode.mExecuteCmd(_cmd)

            if "uid" in _configU:
                aNode.mExecuteCmd(f"/bin/cat /etc/shadow | /bin/grep {_name}")
                if aNode.mGetCmdExitStatus() != 0:
                    ebLogInfo(f"Creating missing user: {_configU['uid']} {_name}")
                    _cmd = f"/usr/sbin/useradd -u {_configU['uid']} -g {_name} -d /home/{_name} -s /bin/bash {_name}"
                    aNode.mExecuteCmd(_cmd)

    def mValidateUsersRange(self, aNode):

        _toRemap = self.mGetUsersGroupsToRemap(aNode)

        if _toRemap:
            _msg = f"The following users/groups are outside the range: {_toRemap.keys()}"
            return False, _msg

        return True, ""

    def mRemapUsers(self, aNode, aToRemap, aForceManual):

        # Remove the already configured
        _ids = self.mGetUidFromFile(aNode, "/etc/passwd")
        _newRemap = {}

        for _name, _info in aToRemap.items():
            if "uid" in _info:
                if str(_info["uid"]) == str(_ids[_name]):
                    ebLogInfo(f"Skip remap of {_name} with id {_info['uid']}")
                else:
                    _newRemap[_name] = int(_info["uid"])
                    ebLogInfo(f"Add remap of {_name} to id {_info['uid']}")

        # Remap the users
        _exadataImage = self.__clubox.mGetExadataImageFromMap(aNode.mGetHostname())

        if version_compare(_exadataImage, "24.1.0") >= 0:

            # Create content of new file
            _filename = f"/tmp/{str(uuid.uuid1())}.txt"
            for _name, _id in _newRemap.items():
                ebLogInfo(f"*** Alter user {_name} to ({_id}) with migrate_ids.sh on file {_filename}")

                _cmd = f"/bin/echo '{_name} {_id}' >> {_filename}"
                aNode.mExecuteCmd(_cmd)

            # Execute remap
            _cmd = f"/opt/oracle.SupportTools/migrate_ids.sh --uid-file {_filename}"
            aNode.mExecuteCmdLog(_cmd)

            # Remove file
            _cmd = f"/bin/rm {_filename}"
            aNode.mExecuteCmdLog(_cmd)

        else:

            for _name, _id in _newRemap.items():

                _originalId = _ids[_name]

                if aForceManual:

                    ebLogInfo(f"*** Alter user {_name} ({_originalId} to {_id}) with manual process")
                    _cmd = f"/usr/bin/usermod -u {_id} {_name}"
                    aNode.mExecuteCmd(_cmd)

                    _cmd = "/bin/find / -uid %s -exec chown -h %s {} \;" % (str(_originalId), str(_id))
                    aNode.mExecuteCmd(_cmd)

                else:
                    ebLogInfo("*** Alter user %s (%s to %s) with migrate_ids.sh" % (_name, _originalId, _id))
                    _cmd = f"/opt/oracle.SupportTools/migrate_ids.sh -uid {_name} {_id}"
                    aNode.mExecuteCmd(_cmd)


    def mRemapGroups(self, aNode, aToRemap, aForceManual):

        _ids = self.mGetUidFromFile(aNode, "/etc/group")
        _newRemap = {}

        # Remove the already configured
        for _name, _info in aToRemap.items():
            if "gid" in _info:
                if str(_info["gid"]) == str(_ids[_name]):
                    ebLogInfo(f"Skip remap of {_name} with id {_info['gid']}")
                else:
                    _newRemap[_name] = int(_info["gid"])
                    ebLogInfo(f"Add remap of {_name} to id {_info['gid']}")

        # Remap the groups
        _exadataImage = self.__clubox.mGetExadataImageFromMap(aNode.mGetHostname())

        if version_compare(_exadataImage, "24.1.0") >= 0:

            # Create content of new file
            _filename = f"/tmp/{str(uuid.uuid1())}.txt"
            for _name, _id in _newRemap.items():
                ebLogInfo(f"*** Alter group {_name} to ({_id}) with migrate_ids.sh on file {_filename}")

                _cmd = f"/bin/echo '{_name} {_id}' >> {_filename}"
                aNode.mExecuteCmd(_cmd)

            # Execute remap
            _cmd = f"/opt/oracle.SupportTools/migrate_ids.sh --gid-file {_filename}"
            aNode.mExecuteCmdLog(_cmd)

            # Remove file
            _cmd = f"/bin/rm {_filename}"
            aNode.mExecuteCmdLog(_cmd)

        else:

            # Remap the groups
            for _name, _id in _newRemap.items():

                _originalId = _ids[_name]

                if aForceManual:

                    ebLogInfo(f"*** Alter group {_name} ({_originalId} to {_id}) with manual process")
                    _cmd = f"/usr/bin/groupmod -g {_id} {_name}"
                    aNode.mExecuteCmd(_cmd)

                    _cmd = "/bin/find / -gid %s -exec chgrp -h %s {} \;" % (str(_originalId), str(_id))
                    aNode.mExecuteCmd(_cmd)

                else:

                    ebLogInfo(f"*** Alter group {_name} ({_originalId} to {_id}) with migrate_ids.sh")
                    _cmd = f"/opt/oracle.SupportTools/migrate_ids.sh -gid {_name} {_id}"
                    aNode.mExecuteCmd(_cmd)


    def mGetRequiredRemapping(self, aHost, aNode):
        _node = aNode

        # Check ENSP
        if self._is_esnp_running(_node):
            ebLogInfo(f"Skip node: {aHost} since ENSP is running")
            return None

        # Check DBMCLI
        if not self._is_dbmcli_running(_node):
            _msg = ("dbmcli services are down and must be up "
                    "and running before remapping users/groups.")
            ebLogError(f"*** {_msg} ***")
            raise ExacloudRuntimeError(0x0760, 0xA, _msg)

        # Calculate users to remap
        return self.mMergeUsersGroupsToRemap(_node)


    def mExecuteNodeRemap(self, aNode, aRequiredRemapping):
        _node = aNode
        _toRemap = aRequiredRemapping

        # Create missing users
        self.mCreateMissingUsersGroups(_node, _toRemap)

        # Detect migrate_ids.sh
        _force_manual_uidmove = True

        if not self.__clubox.mCheckConfigOption('force_manual_uidmove','True'):
            ebLogInfo("*** Checking if compute image is above 19.2")
            _minversion = "192000"
            _rc = self.__clubox.mCheckMinSystemImage([_node.mGetHostname()],_minversion)
            if _rc:
                ebLogInfo('*** Host:{} has a System Image above version:{}'.format(_node.mGetHostname(),_minversion))
                ebLogInfo('*** Looking for /opt/oracle.SupportTools/migrate_ids.sh script')

                if _node.mFileExists("/opt/oracle.SupportTools/migrate_ids.sh"):
                    _force_manual_uidmove = False
                else:
                    ebLogInfo('*** /opt/oracle.SupportTools/migrate_ids.sh script not found')
                    ebLogWarn('*** Warning *** : Falling back to the manual change uid/gid process')
            else:
                ebLogInfo('*** Host:{} does not have a System Image above version:{}'.format(_node.mGetHostname(),_minversion))
                ebLogWarn('*** Warning *** : Falling back to the manual change uid/gid process')

        # Triggering remap
        self.mRemapGroups(_node, _toRemap, _force_manual_uidmove)
        self.mRemapUsers(_node, _toRemap, _force_manual_uidmove)


    def mExecuteRemapSingle(self, aHost, aGrabLock=False):

        with connect_to_host(aHost, get_gcontext()) as _node:
            # Check without locks first if we need to remap
            _toRemap = self.mGetRequiredRemapping(aHost, _node)

            # If we don't need to remap, end execution early
            if not _toRemap:
                ebLogInfo("Remap not needed. Skipping execution.")
                return

            # If we need to map, grab locks only if specified
            if aGrabLock:
                ebLogTrace(f"Execution of this step will grab a lock for node: {aHost}")
                _lock = RemoteLock(self.__clubox, force_host_list=[aHost])
                _lock.acquire()
                try:
                    # Check again if a change is required, now with the lock acquired
                    _toRemap = self.mGetRequiredRemapping(aHost, _node)
                    # End execution early if we don't need to remap anymore
                    if not _toRemap:
                        ebLogInfo("Remap not needed after checking with acquired lock. Skipping execution.")
                        return
                    # Remap with lock already acquired, return to avoid execution of below lines
                    self.mExecuteNodeRemap(_node, _toRemap)
                    return
                finally:
                    _lock.release()
            
            # If we don't need to lock to remap, no need to double-check.
            self.mExecuteNodeRemap(_node, _toRemap)


    def mExecuteRemap(self):

        # Process dom0s

        _ite = 0
        while _ite < 2:
            _plist = ProcessManager(aTimeoutBehavior=TimeoutBehavior.IGNORE, aExitCodeBehavior=ExitCodeBehavior.IGNORE)
            for _dom0, _ in self.__clubox.mReturnDom0DomUPair():
                _p = ProcessStructure(self.mExecuteRemapSingle, [_dom0, True], _dom0)
                _p.mSetMaxExecutionTime(30*60) # 30 minutes timeout
                _p.mSetJoinTimeout(10)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)

            _plist.mJoinProcess()
            if _plist.mGetStatus() != 'killed':
                break

            _ite += 1

       # Process domUs

        _ite = 0
        while _ite < 2:
            _plist = ProcessManager(aTimeoutBehavior=TimeoutBehavior.IGNORE, aExitCodeBehavior=ExitCodeBehavior.IGNORE)
            for _, _domU in self.__clubox.mReturnDom0DomUPair():
                _p = ProcessStructure(self.mExecuteRemapSingle, [_domU], _domU)
                _p.mSetMaxExecutionTime(30*60) # 30 minutes timeout
                _p.mSetJoinTimeout(10)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)

            _plist.mJoinProcess()
            if _plist.mGetStatus() != 'killed':
                break

            _ite += 1

        ebLogInfo("mExecuteRemap Complete")

class ebADBSUtil:
    def __init__(self, aOptions):
        self.__options = aOptions
        self.__site_group_path = '/var/opt/oracle/location.json'

    def mGetSiteGroupInfoFromPayload(self):
        # Check if payload exists
        if not self.__options.jsonconf:
            raise ExacloudRuntimeError(0x0207, 0xA, f"Options does not contain the 'jsonconf' attribute.")
        # Skip if location block is not present, as this means that ECRA determined that this is not a 
        # multicloud instance. We need to explicitly check if this is a NoneType object because Python
        # will return False for either None or empty dictionary instances, which are different scenarios
        # in this case:
        _site_group_config = self.__options.jsonconf.get("location")
        if _site_group_config is None:
            ebLogWarn("Skipping the creation of the 'location.json' file as this is not a multicloud instance.")
            return None
        if len(_site_group_config) == 0:
            _msg = f"Failed to create location.json file. Location info in ECRA payload is empty."
            raise ExacloudRuntimeError(_msg, aStackTrace=True)
        ebLogInfo("Successfully retrieved site group info from the payload.")
        return _site_group_config

    def mCreateSiteGroupConfigFile(self, aNode):
        # Retrieve the location info
        _site_group_config = self.mGetSiteGroupInfoFromPayload()
        if not _site_group_config:
            ebLogInfo("Did not retrieve location info from ECRA payload.")
            return 0
        # Check if the domUs are able to be connected to
        ebLogInfo(f"Checking if domUs are up before creating {self.__site_group_path}")
        _node = exaBoxNode(get_gcontext())
        if not _node.mIsConnectable(aHost=aNode, aTimeout=5):
            raise ExacloudRuntimeError(0x0114, 0xA, f"Cannot connnect to {aNode}. Cannot create {self.__site_group_path}")
        # Write the location info to the site group file
        _exit_status = 0
        _bytes = six.ensure_binary(json.dumps(_site_group_config))
        ebLogInfo(f"Writing site group configuration file at {aNode}")
        with connect_to_host(aNode, get_gcontext(), username="root") as _node:
            # Write the file as bytes
            _node.mWriteFile(self.__site_group_path, _bytes)
            # Verify that the file was written properly, the .trc file will already contain the error message
            if _exit_status != 0 or not _node.mFileExists(self.__site_group_path):
                raise ExacloudRuntimeError(0x0114, 0xA, f"Failed to create {self.__site_group_path} in {aNode}.")
            # Give oracle user permissions for the site group JSON file
            ebLogInfo(f"Changing ownership to oracle user for file: {self.__site_group_path}")
            _cmd = f"/usr/bin/chown -fR oracle:oinstall {self.__site_group_path}"
            _node.mExecuteCmdLog(_cmd)
            _exit_status = _node.mGetCmdExitStatus()
            # Set read-only permissions to the file only for oracle user
            _cmd = f"/usr/bin/chmod 400 {self.__site_group_path}"
            _node.mExecuteCmdLog(_cmd)
            _exit_status = _node.mGetCmdExitStatus()
        return _exit_status


def mGetGridListSupportedByOeda(aExaBoxCluCtrlObj, aGridVersion):
    """
    Check if given grid image is supported by OEDA
    """
    try:
        # Get oeda opath
        _ebox = aExaBoxCluCtrlObj
        _oeda_path = _ebox.mGetOedaPath()
        _oedacli_bin = os.path.join(_oeda_path, 'oedacli')
        _get_grid_list_cmd = f'{_oedacli_bin} -e "list softwareversions grid"'
        # Get the output from oedacli  
        _, _, _o, _ = _ebox.mExecuteLocal(_get_grid_list_cmd)
        _output = _o.strip()
        
        _supported_major_minor_versions = set()  
        
        for line in _output.split(os.linesep):
            line = line.strip()
            if not line:
                continue

            potential_versions = line.split(',')
            
            first_part = potential_versions[0].strip()
            if not first_part or not all(c.isdigit() or c == '.' for c in first_part):
                # Skip lines that don't start with something looking like a version
                continue
                
            for part in potential_versions:
                version = part.strip()
                if version:
                    major_minor = '.'.join(version.split('.')[:2])
                    # Ensure it looks like major.minor (e.g. "19.25", not "GI") before adding
                    if '.' in major_minor and all(p.isdigit() for p in major_minor.split('.')):
                        _supported_major_minor_versions.add(major_minor)

        # Extract major.minor from the input grid version
        input_major_minor = '.'.join(aGridVersion.split('.')[:2])
        
        if input_major_minor in _supported_major_minor_versions:
            ebLogInfo(f'Grid version {aGridVersion} supported by OEDA')
            return True
        
        ebLogWarn(f'Grid version {aGridVersion} NOT supported by OEDA !')
        return False
    
    except Exception as e:
        ebLogError(f'Exception during checking Grid list support in OEDA : {str(e)}')
        return False
        
# end of file
