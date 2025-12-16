"""
$Header:

 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    OVM - Basic functionality

FUNCTION:
    Provide basic/core API for managing OVM Cluster (Cluster Lifecycle,...)

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    jfsaldan    11/28/25 - Bug 38693893 - EXACS:BUTTERFLY:OC39:ADD VM FAILING
                           AT RUN ROOTSCRIPT STEP:ERROR:OEDA-1200: ROOT.SH
                           INITIALIZATION FOR CLUSTER CL-K3YQCYTA FAILED ON
                           HOST
    pbellary    11/24/25 - Enh 38685113 - EXASCALE: POST CONFIGURE EXASCALE EXACLOUD SHOULD FETCH STRE0/STE1 FROM DOM0
    prsshukl    11/20/25 - Bug 38675257 - EXADBXS PROVISIONING FAILING IN
                           FETCHUPDATEDXMLFROMEXACLOUD
    prsshukl    11/19/25 - Bug 38037088 - BASE DB -> REFACTOR CODE FOR BASEDB
    scoral      10/30/25 - Bug 38599517 - Added a call to mPatchEDVVolumes
                           before mAddDomU for Exascale with EDV volumes.
    pbellary    10/30/25 - Enh 38596691 - ASM/EXASCALE TO SUPPORT ADD NODE WITH EDV IMAGE
    scoral      10/28/25 - Enh 38452359: Support separate "admin" network
                           section in payload.
    rajsag      10/23/25 - bug 38484985 - exascale- exacloud: add vm to
                           exascale cluster with exascale images failed
    naps        10/15/25 - Buf 38092408 - zdlra change newnode permission for
                           u01 diag folder.
    ririgoye    09/25/25 - Bug 38341730 - ADD IPCONF PRECHECKS DURING
                           PREVMSETUP TO CATCH STALE BRIDGES BEFOREHAND
    aararora    09/10/25 - 38391988: Regression fix for 38025087
    akkar       30/06/25 - Bug 38025087: dbaastool rpm for multi cloud
    gparada     07/29/25 - 38253002 allow add db instance for GPC and AWS
    rajsag      07/29/25 - bug 38249275 - exacc:24.3.2.4.0:delete node:
                           clunoderemovegideletetask step is failing due to
                           stale entries not getting cleaned up 
    ririgoye    07/21/25 - Enh 38219932 - CPG: RAISE EXACLOUD ERROR IF THE
                           LOCATION ATTRIBUTE HAS INVALID OR EMPTY INFO IN ECRA
                           PAYLOAD
    ririgoye    06/27/25 - Enh 38086929 - CREATE /OPT/ORACLE/SG.JSON DURING
                           PROVISIONING OF ADBS CLUSTERS
    bhpati      06/23/25 - Bug 38027097 - NEW LAUNCH STUCK AS THE OLD DELETE
                           NODE HAD NOT DELETED VM
    oespinos    06/10/25 - Bug 38051133 - Keep nats dns entries even after node deletion
    abflores    06/09/25 - Bug 37508725 - IMPROVE PORT SCAN
    pbellary    06/02/25 - Bug 37976663 - DB INSTANCES ARE NOT GETTING DELETED DURING DELETE NODE
    abflores    06/01/25 - Add ACFS validation before adding node
    rajsag      05/30/25 - 37542341 - support additional response fields in
                           exacloud status response for add compute steps
    prsshukl    04/24/25 - Bug 37861890 - EXADB-XS: EXACLOUD: ADD COMPUTE IS
                           FAILING IN OEDA
    prsshukl    04/23/25 - Bug 37857887 - REMOVE CELLINIT.ORA FILE FOR EXADBXS
                           (BLOCK STORAGE)
    jfsaldan    04/21/25 - Bug 37856850 - EXACLOUD ENCRYPTION AT REST | ENSURE
                           CLEANUP OF RESIDUAL FILES IN EXACLOUD IF PREVIOUS
                           ATTEMPT FAILED
    prsshukl    04/16/25 - Enh 37827765 - EXADB-XS 19C : ADDITIONAL CHANGES IN
                           CS AND ADD COMPUTE WORKFLOW -> REMOVAL OF INTERFACE
                           STREX / CLREX AND CREATE USER STEP
    prsshukl    04/11/25 - Enh 37807155 - EXADB-XS 19C :CS AND ADD COMPUTE ENDPOINT UPDATE -> 
                           USE OEDACLI CMD TO ATTACH DBVOLUME VOLUMES TO GUEST VMS
    gparada     04/10/25 - 37793138 enable rpms for multicloud aws and azure
                           Also, skip db extension in mAddDBHomes for multicloud
    jesandov    04/10/25 - Bug 37603273 - Install libkms as part of add compute
    pbellary    04/04/25 - Bug 37671564 - DB INSTANCES ARE GETTING DELETED ONLY IF STATUS IS OPEN
    aypaul      04/03/25 - Bug#37509007 Run container activites in parallel for
    prsshukl    04/03/25 - Enh 37740750 - EXADB-XS 19C :CS AND ADD COMPUTE
                           ENDPOINT UPDATE-> ATTACH DBVOLUME VOLUMES TO GUEST
                           VMS
    jfsaldan    04/02/25 - Store luks passphrase in new node
    pbellary    03/12/25 - Bug 37691254 - ADD ELASTIC VM:DB SOURCE FILE GETTING COPIED FROM BASE VM 
                                          TO THE ELASTIC VMS WITH WRONG ORACLE_SID AND ORACLE_HOSTNAME
    dekuckre    03/06/25 - 37363507: Cleanup vmbackup logs for the vm
    jfsaldan    02/28/25 - Bug 37651494 - EXACLOUD ADD NODE FAILS POSTGINID ||
                           OCDE INIT RUNS AFTER SRVCTL SETUP DUE TO 37459561
    aararora    02/26/25 - Bug 37542922: Raise exception during unconfig of
                           clusterware if there is an exception in oeda
    jfsaldan    01/30/25 - Bug 37459561 - REVIEW ECRA STEP OCDE NID
                           CONFIGURATION SCRIPT FOR PARALLEL PROCESSING
    akkar       01/29/25 - Bug 37005705: Delete ssh keys of deleted node from
                           know_hosts file of other nodes
    dekuckre    01/27/25 - 37488508: Remove snapshots of vol as part of delete node
    akkar       01/24/25 - Bug 37515096 Add back db.env code 
    aararora    01/24/25 - Bug 37510360: Fix to read ntp and dns info from
                           ppayload correctly
    pbellary    01/23/25 - Bug 37506231 - EXACALE:CLUSTER PROVISIONING FAILING DUE TO EDV SERVICES STARTUP FAILURE
    ririgoye    01/22/25 - Bug 37265371 - Check that 'fs_encryption' is in payload when base domU is
                           encrypted
    aararora    01/03/25 - ER 37402747: Add NTP and DNS entries in xml
    pbellary    01/10/24 - Bug 37456054 - NODE RECOVERY : DB ON VM RECOVERED BY EXTERNAL 
                           NODE RECOVERY IS OFFLINE DUE TO DB ENVIRONMENT FILE IS MISSING IN SOURCE NODE 
    aypaul      12/24/24 - Bug#37415603 FORWARD PORT CHANGES OF 37405644 TO
    akkar       12/13/24 - Bug 37384268  Handle dbaascli faulty output
    bhpati      12/09/24 - Bug 37097036 - EXACS | REMOVEVMCLOUDVMCLUSTER IS NOT
                           SUCCEEDING | EXACLOUD : NO ACTIVE NODE IN THE
                           CLUSTER
    joysjose    12/04/24 - 37123857: ER to propogate /etc/resolv.conf file from
                           source VM to New Added VMs in Add Node flow to allow
                           custom nameservers
    prsshukl    11/28/24 - Bug 37240032 - Add ntp and dns value pre and post
                           OEDA create vm to the new compute
    jfsaldan    11/27/24 - Enh 37327500 - EXADB-XS: EXACLOUD - OPEN HOST ACCESS
                           CONTROL FOR ROCE NETWORK IN TARGET HOST DURING
                           CREATE SERVICE AND ADD COMPUTE FLOWS
    gparada     11/27/24 - Bug 37331103 Elastic flow should not patch System Img
    anudatta    11/22/24 -  Enh 36553996 - clufy report before add node root.script
    joysjose    11/19/24 - Bug 37277064 Skip mRemoveNodeFromCRS for EXADB-XS
    naps        10/24/24 - Bug 37192649 - Handle eth0 removal per node instead
                           of cluster wide.
    jfsaldan    10/15/24 - Create clustersjson file with all node names for FS
                           Encryption in ExaCC CPSAgent socket setup
    joysjose    10/11/24 - Bug 37111990: Include mRemoveNodeFromCRS function in
                           delete node install_cluster step
    aararora    09/26/24 - Bug 37105761: Oedacli command is failing for
                           elastic_info call in ipv6
    prsshukl    09/26/24 - Bug 37103101 - ADBS: Create /opt/exacloud directory
                           and populate it with exacli wallet files at the end
                           of CREATE_GUEST
    prsshukl    09/23/24 - ER 36981808 - EXACS | ADBS | ELASTIC COMPUTE AND
                           CELL OPERATION ENHANCEMENTS -> IMPLEMENT PHASE 2
    prsshukl    09/22/24 - Bug 37082702 - EXACS: ADBS: ELASTIC COMPUTE FAILURE
                           IN PREVMINSTALL
    prsshukl    09/04/24 - ER 36553793 - EXACS | ADBS | ELASTIC CELL AND
                           COMPUTE OPERATION ENHANCEMENTS -> IMPLEMENT PHASE 1
    jfsaldan    08/23/24 - Bug 36974914 - EXACLOUD - ADD COMPUTE U01 ENCRYPTION
                           FAILS IF AHF IS RUNNING IN U01 FS
    naps        08/09/24 - Bug 36908342 - X11M support.
    pbellary    09/04/24 - Enh 36976333 - EXASCALE:ADD NODE CHANGES FOR EXASCALE CLUSTERS 
    prsshukl    08/06/24 - Bug 36910001 - Add Dom0 lock for System Image
                           transfer
    pbellary    07/25/24 - Bug 36550491 - Exacloud should skip UNDO of ROOT_SCRIPT for 23ai
    prsshukl    07/24/24 - Bug 34014317 - Delete Storage pool as part of delete
                           compute
    prsshukl    07/19/24 - Bug 36860623 - mWhitelistCidr() method needs to be
                           called for Fedramp enabled Exacc env
    jfsaldan    07/17/24 - Bug 36711025: Add u01 encryption support with
                           oeda/exadata tooling
    jesandov    07/17/24 - Bug 36836361 - Single Node Backfill
    akkar       07/10/24 - Bug 36825918: Minor fix for dbaascli
    aararora    07/09/24 - Bug 36813479: Exclude asm password precheck for
                           zdlra environment and add exabox config for the
                           check
    scoral      06/27/24 - Bug 36781764 - Fix DomUImageName XML field for RTG
                           images after clone DomU.
    jfsaldan    06/14/24 - Bug 36730803 - EXACS:23.4.1.2.5: OL8 FS ENCRYPTION:
                           ADD VM FAILING AT PREVM INSTALL: EXACLOUD TRIES TO
                           ENCRYPT FIRST.BOOT IMAGE FOR FULL GUEST ENCRYPTION
    akkar       05/29/24 - Bug 36397179: Replace dbaasapi with dbaascli
    gparada     05/14/24 - 36603685 Handle *.rtg.img files for >=24.1
                           RTG = Ready To Go
    pbellary    05/03/24 - Bug 36577256 - NODE RECOVERY - DB INSTANCE ON RECOVERED 
                           VM IS IN OFFLINE STATE AFTER NODE RECOVERY COMPLETED
    aararora    04/30/24 - ER 36485120: IPv6 support in exacloud
    pbellary    04/19/24 - Bug 36525280 - OEDACLI: CLONE GUEST FAILED: FAILED TO ESTABLISH CONNECTION TO SYSASM
    akkar       04/17/24 - Bug 36509496: Patchserver ip change for fedramp
    jfsaldan    04/15/24 - Bug 36494276 - EXACS EXACSDBOPS-6953: GUEST FIRST
                           BOOT IMAGE FILE DOES NOT EXIST ON HOST FOR ELASTIC
                           COMPUTE FLOW
    akkar       04/09/24 - Bug 36437394 - Copy gpg keys to new node 
    dekuckre    04/03/24 - 36503657: Remove gcv volume mount for deleted vm.
    aararora    03/29/24 - Bug 36400840: Give enough time to check for crs to
                           be up and also to restart the cluster
    dekuckre    03/29/24 - 36458423: xs - update cswlib_oss_url in env file
    jesandov    03/25/24 - 36437219: Add Compute with custom version in ECRA
                           payload
    dekuckre    03/21/24 - 36427129: For exascale generate id_rsa keys for opc user in the new VM.
    dekuckre    03/20/24 - 36422145: Skip removal of VM access at end of add node (exascale)
    jesandov    03/11/24 - 36390486: Move Exascale validation for secure_vm
    ririgoye    03/06/24 - Bug 36364832 - NEED DETECTION/PRECHECK FOR
                           EXACSDBOPS-6663 WHERE ASM PASSWORD IS CHANGED BY
                           CUSTOMER CAUSING VM-ADDITION FAILURE
    dekuckre    03/01/24 - 36339845: patch private network
    dekuckre    02/28/24 - XbranchMerge dekuckre_bug-36313994 from
                           st_ecs_23.4.1.2.0
    jesandov    02/23/24 - 36326706: Skip mRemoveNodeFromCRS in ExaScale
    dekuckre    02/28/24 - 36313994: Use scp to copy dbhome from src domU
    aararora    02/21/24 - Bug 36298520: Generate ssh keys for oracle and grid user for add compute
                           flow in exascale.
    jesandov    02/13/24 - 36294300: Add parameter to force lookup of system
                           version
    jfsaldan    02/07/24 - Bug 35471024 - EXACS:22.2.1:DROP4:FS ENCRYPTION
                           VALIDATION FOR OL8
    jesandov    01/25/24 - 36207260: Add function to read/write sysctl
                           parameters
    ririgoye    01/19/24 - Bug 36165727 - Added check to verify that failure is
                           silent when in a ExaCC environment and ExaCLI
                           password is invalid
    scoral      01/04/23 - Bug 36152786: Move parsing of grid home of mCallBack
                           to its respective step to avoid ExaDB-XS failure.
                           Bug 36155980: Fixed invocation arguments of
                           csExaScaleComplete.doExecute
                           Bug 36160581: Skip VIP setup during
                           mPostReshapeValidation for ExaDB-XS.
    rajsag      12/20/23 - Bug 36125280: exacs:23.4.1:tc2:post provisioning the
                           hugepages_total:0 is set on the vm
    akkar       12/15/23 - Bug 36040644 - Add patchserver ip in /etc/hosts
    ririgoye    11/24/23 - Bug 35965709 - ECS : EXACLOUD SHOULD FAIL DURING
                           PROVISIONING OR ADD NODE IF IT FAILS TO SET UP THE
                           EXACLI CLOUD USER PASSWORD
    pbellary    11/03/23 - Bug 35448716 - EXACC:22.3.1:X8:ADD NODE FAILED AT CREATE VM STEP AFTER RENAMING CLUSTER NAME ON DOMUS
    prsshukl    10/29/23 - Bug 35887541 - OCI-EXACC: Exacloud to copy correct
                           dbcsagent p12 file to domU during Create Service and
                           Add Node
    pbellary    10/18/23 - Bug 35916007 - SYSTEM FIRST BOOT IMAGE FILE GETS REMOVED DURING 
                           IN-PLACE REPLACEMENT PROCESS CAUSING FAILURE OF "EXAUNIT-ATTACH-COMPUTE" OPERATION
    jesandov    10/16/23 - 35729701: Support of OL7 + OL8
    scoral      10/10/23 - Enh 35779476 - Do not update the bonding
                           configuration if eth0 is removed.
    dekuckre    10/03/23 - 35868006: Update copy of patchconfig xml for oedacli calls.
    jfsaldan    09/29/23 - Bug 35834771 - NODE RECOVERY: BONDETH0 OF NEWLY
                           CREATED VM WAS NOT BROUGHT UP RESULTING IN CLIENT
                           NETWORK ISSUE
    rajsag      09/25/23 - 35834771 - node recovery: bondeth0 of newly created
                           vm was not brought up resulting in client network
                           issue
    jesandov    09/23/23 - 35832789: Create new step called ExaScale Complete
    aypaul      09/01/23 - Bug#35759743 Updating call to process selinux update
                           to postvm_install step.
    asrigiri    08/25/23 - Bug 35619286 - DURING NODE SCLAEUP OPERATION AT RDBMS ADDITION THE SCP IS BEING USED AND COPYING IN SERIAL.
    pbellary    08/25/23 - Bug 35737837 - EXACS:23.4.1:X9M:MULTI-VM:ADBD PROVISIONING FAILING AT CREATE VM
                           STEP:ERROR - 6153 - UNABLE TO REMOVE STALE DUMMY BRIDGE VMETH200
    jfsaldan    08/24/23 - Enh 35692408 - EXACLOUD - VMBOSS - CREATE A FLAG IN
    ririgoye    08/23/23 - Bug 35616435 - Fix redundant/multiple instances of
                           mConnect
    pbellary    08/22/23 - Enh 35728221 - ADD SUPPORT FOR 2TB MEMORY IN X10M
    jfsaldan    08/18/23 - Bug 35719818 - PLEASE PROVIDE A WAY TO IDENTIFY FROM
                           A XEN DOM0 IF THE GUESTVM HAS LUKS ENABLED OR NOT
    jesandov    08/08/23 - 35688512: Move logic of check CRS after update of
                           nodes
    scoral      07/14/23 - 35605560: Added call of mDeleteStaleDummyBridge
                           during add compute flow before Create Guest step.
    jfsaldan    07/12/23 - Bug 35571756 - EXACLOUD - DELETE COMPUTE DOESN'T
                           UPDATE NODE_LIST IN GRID.INI FOR ALL THE NODES TO
                           KEEP
    pbellary    06/28/23 - 35543679 - ADD VM (ON NON 2TB SYSTEM) FAILING AT PRECHECK:"ERROR-MESSAGE": "2TB MEMORY NOT SUPPORTED ON DOM0 
    pbellary    06/20/23 - ENH 35434953: NODE RECOVERY: DELETE NODE SHOULD SKIP DELETION OF VM BACKUP IF EXISTS
    dekuckre    06/19/23 - 35513067: call mRotateVmKeys() in POST VM INSTALL step
    jfsaldan    06/14/23 - Enh 35500796 - EXACLOUD TO SUPPORT GOLDEN VMBACKUP
                           STEP IN ELASTIC ADD COMPUTE
    pbellary    06/06/23 - ENH 35445802: EXACS X9M - ADD SUPPORT FOR 2TB MEMORY IN X9M
    naps        06/04/23 - Bug 35095608 - mvm support for zdlra.
    aararora    05/29/23 - Bug 35437879: Delete multiple entries of VIP if present during
                           delete compute.
    jfsaldan    05/24/23 - Bug 35394466 - ADD VM FAILS AT TASK RUNROOTSCRIPT
                           SINCE WIDE OPEN TMP RULES ARE MISSING
    scoral      05/24/23 - Bug 35285863: Update bonding interface during Add
                           node for bonding environments to increase
                           arp_interval from 100 to 1000 if needed.
    akkar       04/27/23 - Bug 35305090: Add Grid user keys during add compute
    joysjose    04/26/23 - Bug 35236850 - Patch source XML with DNS and NTP
                           info from Source DomU before Add Node
    jfsaldan    04/19/23 - Bug 35304980 - EXACC:ELASTIC NODE IS NOT PROPERLY
                           CONFIGURING COMMON_NAT_FILESERVER AT CPROPS.INI
    scoral      04/14/23 - Bug 35177571 - Use bridge family instead of ip
                           family for VM NFTables rules in OL8 envs.
    rajsag      04/12/23 - 35281887 - exacc:22.3.1:x10m:multirack:add nodes
                           does not replicate db instances to new nodes
    pbellary    03/29/23 - 35094869: EXACC SERIAL CONSOLE ADD THE CALL TO EXACLOUD SERIAL CONSOLE INSTALL
                           COMMAND IN ELASTIC COMPUTE FLOW
    aararora    03/14/23 - Add DR VIPs during elastic compute addition.
    aararora    03/09/23 - Need to add DR info from payload to xml during
                           vmgi_reshape
    jfsaldan    03/03/23 - Bug 35144841 -MULTI-VM:STEPWISE ADD
                           COMPUTE FAILING AT CREATE_GUEST - FSENCRYPTION
    pbellary    03/03/23 - 35142856: ADD NODE FAILS AT FETCHUPDATEDXMLFROMECFORNODELISTUPDATE WITH ERROR: INVALID RACK NUMBER : 2
    dekuckre    02/16/23 - 35081567: Call mCheckOracleLinuxVersion
    dekuckre    02/02/23 - 35033217: Raise error incase xml patching fails in delete node flow.
    naps        01/06/23 - Bug 34884577 - Move HT for zdlra to prevmsetup step.
    prsshukl    01/04/23 - 34912293: Improve the error message for VM
                           connectivity failure and suggest running of temporal
                           keys addition workflow for existing VMs
    siyarlag    11/23/22 - 34278230: try copying kms rpms from images repo
    hgaldame    11/08/22 - 34778659 - ociexacc: exacloud cli command for health
                           metrics network configuration on cps host
    aypaul      11/03/22 - ENH#34250801 Connectivity check to existing VMs
                           prior to elastic add operations.
    pbellary    10/17/22 - Bug 34686909 - FOR HETERO ENV, PATCH THE XML WITH CORRECT INTERFACES 
    rajsag      10/14/22 - 34701585 - ADD COMPUTE FAILING TO FETCH SOURCE DOMU
    dekuckre    30/09/22 - 34653200: Reset actions(True) when patching the xml with new node
    dekuckre    09/23/22 - 34629253: Skip decode of password already in string
    rajsag      09/14/22 - 34591580 - EXACC: mSetSrcDom0DomU not setting the
                           pingable node as src node
    pbellary    08/25/22 - 34520909: HUGEPAGES ON ADDED NODE NOT CONFIGURED TO MATCH 
                           EXISTING NODES IN THE CLUSTER
    scoral      08/02/22 - Bug 34482855 - Migrate to bonding static bridges
                           while PreVM Checks.
    dekuckre    29/07/22 - 34429138: Remove key access to new domU.
    akkar       08/04/22 - Bug:3439496 Raiise exception if keys sync fails
    akkar       07/14/22 - Bug 34372638 - EXACS:22.2.1:IAD SRG:NEW DOMU NOT
                           ACCESSIBLE VIA USER KEY AFTER ELASTIC COMPUTE ADD
    dekuckre    06/10/22 - 34252376: Include more oedacli substeps
    dekuckre    06/17/22 - 34276586: Move UpdateListenerPort outside post GI NID Step
    rajsag      06/15/22 - 33897329 - ensure that the ahf trace files are
                           readable by the grid user before you add vms to a vm cluster
    alsepulv    06/15/22 - Bug 34236957: Run hostnames' length precheck before
                           add node
    dekuckre    06/14/22 - 34267393: Update grid.ini in ZDLRA env
    scoral      06/08/22 - Bug 34261110: Remove stale bridges after VM deletion
    dekuckre    06/01/22 - 34200603: Install dbaastool rpm prior to ocde -init
    alsepulv    05/26/22 - Enh 33590245: Enable FS encryption during
                           add_compute
    ajayasin    05/24/22 - 34202215: variable referenced before assignment -
                           code issue fix
    jfsaldan    05/20/22 - XbranchMerge jfsaldan_bug-34195692 from
                           st_ecs_22.2.1.0.0
    jfsaldan    05/20/22 - Bug 34195692 - Grab lock before delete VM during
                           delete node to support parallel ops
    aypaul      04/25/22 - Enh#33667718 Add profile based cluster check
                           operations for delete node operations.
    dekuckre    04/05/22 - 33931831: Ensure CRS and ASM related pre-checks only on src domU
    dekuckre    04/04/22 - 34022578: Update InMemory config objects
    jlombera    03/28/22 - Bug 34000208: pass JSON payload to
                           clubonding.is_static_monitoring_bridge_supported()
    jlombera    03/18/22 - Bug 33244220: add support for bonding static
                           monitoring bridge
    jlombera    03/08/22 - Bug 33891346: configure bondmonitor at CreateVM
                           instead of PostGINID
    naps        03/06/22 - remove virsh dependency layer.
    dekuckre    02/23/22 - 33678788: Correct /etc/hosts in existing domUs
    dekuckre    02/17/22 - 31549427: Add more post validation checks 
    siyarlag    02/07/22 - 33383208: Install KMS rpms on the new node
    dekuckre    01/17/22 - 33757532: Correct condition to fetch src domU
    ajayasin    12/09/21 - ahf install for new node
    dekuckre    12/08/21 - 33647944: Fix mDeleteNode 
    aypaul      12/07/21 - Bug#32967023 Copy cprops.ini file from source domU
                           to new domU.
    ajayasin    12/03/21 - 33633800 cmd exit status check
    jlombera    12/01/21 - ENH 33304767: honor _skip_jumbo_frames_config
                           exabox.conf param
    rajsag      12/01/21 - 33594977 :adding error code handling for the node
                           subsetting in exacloud
    siyarlag    11/22/21 - 33588278: scp needs destination directory
    siyarlag    11/15/21 - 33556605: use scp instead of rsync for remote copy
    scoral      11/04/21 - 33539248 - Fix u02 size.
    siyarlag    11/04/21 - 33536097: use ssh keepAlive to retain the connection
    dekuckre    10/27/21 - 33416778:Remove entry from /etc/hosts* (delete node)
    dekuckre    03/11/21 - 33533544: select connectable domU to parse oratab
    siyarlag    10/21/21 - 33484723: pass date string to imageversion command
    naps        10/18/21 - remove opc key dependency during addnode
    dekuckre    10/06/21 - 32886306: Optimize copy of u02 from src to new domU
    rajsag      10/05/21 - 33436451 - exacc: cluster xml not updating due to
                           exception in exacloud for unsupported operand
                           type(s) for set
    pbellary    10/04/21 - ENH 33056017 - EXACS EXACLOUD. ADD COMPUTE SUPPORT FOR MULTI VM
    pbellary  09/30/21 - 33412194 - OEDACLI XMLS NEEDS TO BE UPDATED TO DESIRED GRIDHOME DURING NODESUBSET ADDNODE.
    dekuckre    09/29/21 - 33405400: Remove oracle,grid,opc access to existing ndoes
    naps        09/23/21 - patch vm.cfg only once.
    dekuckre    09/15/21 - 33349996: Select first node from olsnodes as srcdomU
                           33355282: Call post validation in end step of delete node
                           33375478: Add prechecks in OSTP_PREDB_DELETE
    pbellary    09/20/21 - 33349674 - DB Instance are not removed when db is in preferred state
    ajayasin    09/13/21 - delete Node flow log addition
    rajsag      09/12/21 - 33333194 - exacc:bb:cpu offline: scaling failed -
                           critical exception caught aborting request [invalid
                           literal for int() with base 10: ] after ecra/cps
                           upgrade
    dekuckre    09/09/21 - 33322272: Update DNS config  with priv networks for
                           OCIExaCC
    dekuckre    31/08/21 - 33276912: Update u02 size before creating new VM
    siyarlag    07/08/21 - 32914532: manual removal of vmbridges
    naps        07/07/21 - Disable HT for elastic nodes.
    dekuckre    09/05/21 - 32982101: Add elastic support for ZDLRA systems
    dekuckre    09/05/21 - 32962521: Update pswd in es.properties before oedacli - delete guest
    siyarlag    06/10/21 - 32971743: move ahf data dir from gi home for addNode
    dekuckre    06/05/21 - 32205492: Convert elastic flow to workflow based.
    gsundara    05/21/21 - bug 32908741: addviptovcn.sh to be copied on added compute node
    dekuckre    06/05/21 - Update mRemoveNodeFromCRS
    dekuckre    04/20/21 - 32790503: Add mUpgradeSystemImage
    dekuckre    03/31/21 - 32563027: Include parallel multiple compute flow
    dekuckre    03/30/21 - 32603029: update mUpdateRPM
    dekuckre    03/17/21 - 32636490: Use latest patched config for Add Node.
    jlombera    03/23/21 - Bug 32620666: use new clujumboframes API
    siyarlag    03/22/21 - 32214702: multiple image version support
    jvaldovi    03/22/21 - Enh 32621312 - Marker Script To Disable Vnuma
    dekuckre    03/12/21 - 32621244: Send correct xml to patch image version
                           and timezone
    dekuckre    03/02/21 - 32481040: Add mUpdateRPM 
    dekuckre    03/02/21 - 32566609: Use correct domU to update CRS resource
    jlombera    02/17/21 - Bug 31525380: setup/cleanup bonding during Elastic
                           add/remove compute
    dekuckre    02/16/21 - 32502419: Add mRemoveNodeFromCRS
    dekuckre    02/09/21 - 32467974: Patch xml with source domU's timezone.
    naps        02/02/21 - rootfs should be at default size of 15G.
    dekuckre    01/22/21 - 32404771: Update mPostReshapeValidation
    ffrrodri    01/20/21 - Bug 32387381: Correction of local variable dbname
                           referenced before assignment error
    dekuckre    01/15/21 - 32383839: Call new Dom0, DomU for mAddNodeCallBack
    dekuckre    01/06/21 - 32300564: Add operation validation check
                           32299593: Add delete node precheck
    sdeekshi    12/04/20 - 32224810: clean up dbnid folder during add node
    dekuckre    11/24/20 - 32103730: Store exacli password in new domU
    rajsag      11/03/20 - place and copy the script for downloading latest
                           compute updates and patchmgr from exacc to domu in
                           exacloud
    jlombera    09/22/20 - XbranchMerge jlombera_bug-31921823 from
                           st_ecs_20.2.1.0.0rel
    dekuckre    09/21/20 - 31908302: Syncup DBs with shared oracle home (addnode)
    dekuckre    09/15/20 - XbranchMerge dekuckre_bug-31879505 from
                           st_ecs_20.2.1.0.0rel
    dekuckre    09/13/20 - XbranchMerge dekuckre_bug-31873592 from main
    jlombera    09/22/20 - Bug 31921823: do not access None values
    dekuckre    09/11/20 - Fix 31873592
    dekuckre    09/02/20 - XbranchMerge dekuckre_bug-31822036 from
                           st_ecs_20.2.1.0.0rel
    dekuckre    09/15/20 - Fix 31879505
    dekuckre    09/13/20 - XbranchMerge dekuckre_bug-31873592 from main
    dekuckre    09/11/20 - Fix 31873592
    dekuckre    09/02/20 - XbranchMerge dekuckre_bug-31822036 from
    dekuckre    09/02/20 - Backport dekuckre_bug-31800460 from main
    dekuckre    09/02/20 - Fix 31822036
    dekuckre    08/28/20 - XbranchMerge dekuckre_bug-31799929 from
                           st_ecs_20.2.1.0.0rel
    dekuckre    08/28/20 - 31799929: Use virsh undefine as part of delete node.
    dekuckre    08/26/20 - Fix 31800460
    dekuckre    08/04/20 - 31708798: Configure vmbackup in elastic 
                           compute flow.
    dekuckre    07/21/20 - Fix 31645831
    jlombera    07/20/20 - Bug 31607257: handle KVM images
    dekuckre    07/16/20 - Fix 31627599 and 31622498
    dekuckre    07/13/20 - Fix 31598817 
    ajayasin    07/08/20 - bug 31548326 fix
    dekuckre    06/25/20 - Bug 31521017 and 31537710 
    dekuckre    06/25/20 - Bug 31521017 and 31537710
    gurkasin    06/18/20 - Added mPostReshapeValidation
    dekuckre    06/17/20 - 31494643: Add try-except clause for delete node steps.
    siyarlag    06/08/20 - bug 31375127 support kvm for vmbackup
    dekuckre    05/22/20 - 31389081: Make Add Dom0 KVM compatible
    dekuckre    05/07/20 - 30858257: Make elastic compute KVM compatible
    aypaul      03/16/20 - 31030998 EXACC GEN1: DELETE NODE FAILS WHEN NODE IS
                           DOWN.
    siyarlag    01/23/20 - support x8m vm operations
    oespinos    08/12/19 - 30143231 - DISABLE OEDA CVU CHECKS FOR ADD NODE
    dekuckre    06/17/19 - 29859854: Call mStoreDomUInterconnectIps as part of
                           vmgi_reshape
    dekuckre    06/11/19 - XbranchMerge dekuckre_bug-29866040 from
                           st_ebm_19.1.1.1.0
    dekuckre    05/06/19 - XbranchMerge dekuckre_bug-29617988 from
                           st_ebm_19.1.1.1.0
    dekuckre    04/10/19 - 29617988: Remove stale entries from VM's known_hosts file
    dekuckre    07/07/19 - 29351099: Syncup keys for PSM usage.
    dekuckre    02/22/19 - 29394831: Invoke 'addInstance' dbaasapi on DB 
                           running node.
    dekuckre    02/14/19 - 29354634: Invoke change_spfile on the node running
                           DB instance.
    dekuckre    02/07/19 - 29285993: Wait for ASM to be up before proceeding 
                           to post GI step.
    dekuckre    01/30/19 - 29283735: Store the config xml (as part of add node)
                           in appropriate cluster directory.
    dekuckre    11/26/18 - 28429399: Include capability to add a node to the cluster.
    dekuckre    11/26/18 - Move delete node capability from clucontrol.py to here.


"""

from exabox.core.Error import ebError, ExacloudRuntimeError, gNodeElasticError, gReshapeError
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import (ebLogError, ebLogInfo, ebLogWarn, ebLogDebug,
    ebLogVerbose, ebLogJson, ebLogTrace, ebLogCritical)
from exabox.ovm.vmconfig import exaBoxClusterConfig
from exabox.ovm.clunetworkvalidations import ebNetworkValidations
from exabox.core.Context import get_gcontext
from base64 import b64decode
from .clustorage import ebCluQuorumManager
from .cludbaas import ebCluDbaas, getDatabaseHomes, getDatabases, cloneDbHome, addInstance, getDatabaseDetails, deleteInstance, mUpdateListenerPort
from exabox.core.Context import get_gcontext
from exabox.tools.oedacli import OedacliCmdMgr
from exabox.core.DBStore import ebGetDefaultDB
from exabox.ovm.vmbackup import ebCluManageVMBackup
from exabox.ovm.sysimghandler import (
        copyVMImageVersionToDom0IfMissing, formatVMImageBaseName, mIsRtgImg)
from exabox.ovm.clumisc import ebCluPreChecks, ebMiscFx, ebCopyDBCSAgentpfxFile, mPatchPrivNetworks, ebCluSshSetup, ebMigrateUsersUtil
import exabox.ovm.clubonding as clubonding
from exabox.ovm.cluiptablesroce import ebIpTablesRoCE
import exabox.ovm.clujumboframes as clujumboframes
from exabox.ovm.cluexaccsecrets import ebExaCCSecrets
from exabox.network.dns.DNSConfig import ebDNSConfig
from exabox.ovm.cludomufilesystems import get_dom0_disk_for_filesystem, GIB, ebDomUFilesystem, get_dom0_edvdisk_for_filesystem
import os, time, copy, hashlib, uuid, json, traceback
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.cluserialconsole import serialConsole
from exabox.ovm.cluvmconsole_deploy import VMConsoleDeploy
from exabox.ovm.cluencryption import (isEncryptionRequested, createAndPushRemotePassphraseSetup,
    deleteRemotePassphraseSetup, ensureSystemFirstBootEncryptedExistsParallelSetup,
    useLocalPassphrase, deleteOEDAKeyApiFromDom0, encryptionSetupDomU, patchXMLForEncryption,
    createEncryptionMarkerFileForVM, deleteEncryptionMarkerFileForVM,
    exacc_fsencryption_requested, mSetLuksChannelOnDom0Exacc, validateMinImgEncryptionSupport,
    setupU01EncryptedDiskParallel, getMountPointInfo, exacc_save_fsencryption_passphrase,
    exacc_del_fsencryption_passphrase, cleanupU02EncryptedDisk, luksCharchannelExistsInDom0)
from exabox.ovm.csstep.cs_golden_backup import csGoldenBackup
from exabox.ovm.csstep.cs_exascale_complete import csExaScaleComplete as exadbxsComplete
from exabox.ovm.csstep.exascale.cs_exascale_complete import csExaScaleComplete as xsComplete
from exabox.ovm.cluexascale import ebCluExaScale, mRemoveVMmount
from exabox.ovm.utils.clu_utils import ebCluUtils
from exabox.exakms.ExaKmsEntry import ExaKmsHostType
from exabox.ovm.cluvmrecoveryutils import NodeRecovery
from exabox.utils.common import version_compare
from exabox.utils.node import connect_to_host, node_cmd_abs_path_check, node_exec_cmd_check, node_exec_cmd
from exabox.ovm.cluelastic import getGridHome, getDiskGroupNames
from exabox.ovm.adbs_elastic_service import (mReturnSrcDom0DomUPair, mUpdateQuorumDiskConfig, 
                                             mAddExacliPasswdToNewDomUs, mGetorCreateDomUObj, mCreateADBSSiteGroupConfig)
from exabox.ovm.cluhostaccesscontrol import addRoceNetworkHostAccessControl
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure

OSTP_CREATE_VM    = 2
OSTP_INSTALL_CLUSTER = 7
OSTP_CREATE_DB    = 12

OSTP_PRE_INSTALL    = 127
OSTP_PREVM_INSTALL  = 128
OSTP_PREGI_INSTALL  = 129
OSTP_POSTVM_INSTALL = 130
OSTP_POSTGI_INSTALL = 131
OSTP_POST_INSTALL   = 132
OSTP_PREDB_INSTALL  = 133
OSTP_POSTDB_INSTALL = 134

OSTP_PREGI_DELETE   = 135
OSTP_POSTGI_DELETE  = 136
OSTP_PREVM_DELETE   = 137
OSTP_POSTVM_DELETE  = 138
OSTP_PREDB_DELETE   = 139
OSTP_POSTDB_DELETE  = 140

OSTP_POSTGI_NID     = 141
OSTP_DBNID_INSTALL  = 142
OSTP_APPLY_FIX_NID  = 143
OSTP_DG_CONFIG      = 144
OSTP_BACKUP_GOLDIMG = 145

OSTP_END_INSTALL    = 255

VM_MODE   = 1
GI_MODE   = 2
VMGI_MODE = 3

SELINUX_UPDATE_SUCCESS = 0
EXCEPTION_IN_CRS = False

#
# 
#
class ebCluReshapeCompute(object):

    def __init__(self, aExaBoxCluCtrlObj, aOptions):

        self.__oedacli_mgr = None
        self.__options = aOptions
        self.__eboxobj = aExaBoxCluCtrlObj
        self.__dbaasobj = ebCluDbaas(self.__eboxobj, aOptions)
        self.__patchconfig = self.__eboxobj.mGetPatchConfig()
        self.__origdom0domUList = copy.deepcopy(self.__eboxobj.mReturnDom0DomUPair())
        self.__origVMs = copy.deepcopy([domU for _, domU in self.__eboxobj.mReturnDom0DomUPair()])
        
        self.__reshape_conf = {}
        self.__reshape_conf['dom0'] = {}
        self.__reshape_conf['domU'] = {}

        #Node Recovery
        self.__node_recovery = False

        # initialize the json to be used for vmgi_reshape.
        self.initReshapeConf(aOptions)
        self.__srcdomU=''
        self.__srcdom0=''
        self.mSetSrcDom0DomU()
        self.__clu_utils = ebCluUtils(aExaBoxCluCtrlObj)
        

        ebLogInfo("init completed")

    def mGetReshapeConf(self):
        return self.__reshape_conf    
    
    def mGetCluUtils(self):
        return self.__clu_utils  

    def mSetSrcDom0DomU(self):

        _ebox = self.__eboxobj
        _connectableDomU = None
        _olsNodeList=[]
        _newNodeList = []
        for x in self.__reshape_conf['nodes']:
            _newNodeList.append(x['domU']['hostname'])
        for _, _domU in _ebox.mReturnDom0DomUPair():
            if _domU in _newNodeList:
                continue

            if _ebox.mIsExaScale():
                _connectableDomU = _domU.split('.')[0]
                ebLogInfo(f"ExaScale environment, setting src domU as: {_connectableDomU}")
                break

            _node = exaBoxNode(get_gcontext())
            if not _node.mIsConnectable(_domU):
                ebLogWarn(f"*** mSetSrcDom0DomU: DomU {_domU} is not connectable. Run the temporal keys addition workflow for existing VMs. Root ssh access is required for this operation.")
                continue

            _node.mConnect(aHost=_domU)
            if _ebox.mIsAdbs():
                _path = getGridHome(_domU)
                if _path is None:
                    _node.mDisconnect()
                    _detail_error = f"Customised -> GridHomePath:{_path} is empty"
                    raise ExacloudRuntimeError(0x0753, 0xA, _detail_error)
            else:
                _path, _, _ = _ebox.mGetOracleBaseDirectories(aDomU = _domU)

            _, _o, _e = _node.mExecuteCmd(_path + '/bin/crsctl check crs')
            if _node.mGetCmdExitStatus() != 0:
                _node.mDisconnect()
                continue
            # CRS is considered Online only if all the below are online.
            # CRS-4638: Oracle High Availability Services is online
            # CRS-4537: Cluster Ready Services is online
            # CRS-4529: Cluster Synchronization Services is online
            # CRS-4533: Event Manager is online

            if _o:
                _crs_down = False
                _output = _o.readlines()
                for _line in _output:
                    _line = _line.strip()
                    if "is online" not in _line:
                        ebLogWarn(f"*** crs is down on {_domU}. crs check cluster output: {_line}")
                        _crs_down = True
                        break
                if _crs_down:
                    _node.mDisconnect()
                    continue
            
            if not _olsNodeList:
                _, _o, _e = _node.mExecuteCmd(_path + '/bin/olsnodes -s -n|grep Active')
                _out = _o.readlines()
                ebLogInfo(f"olsnodes reported: {_out}")
                if _node.mGetCmdExitStatus() != 0:
                    _node.mDisconnect()
                    _detail_error = "No active node in the cluster"
                    _ebox.mUpdateErrorObject(gNodeElasticError['NO_ACTIVE_NODE'], _detail_error)
                    raise ExacloudRuntimeError(0x0757, 0xA, _detail_error)
                else:
                    for _entry in _out:
                        _olsNodeList.append(_entry.split("\t")[0].strip())

            _node.mDisconnect()
            if _domU.split('.')[0] in _olsNodeList:
                _connectableDomU = _domU.split('.')[0]
            else:
                continue
            ebLogInfo(f"Connectable DomU:{_connectableDomU} detected.")
            break
        if _connectableDomU is None:
            _detail_error = "No Pingable/Active node in the cluster"
            _ebox.mUpdateErrorObject(gNodeElasticError['NO_ACTIVE_NODE'], _detail_error)
            raise ExacloudRuntimeError(0x0757, 0xA, _detail_error )

        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            if _connectableDomU == _domU.split('.')[0]:
                self.__srcdomU = _domU
                self.__srcdom0 = _dom0
                break

        ebLogInfo(f"Selected source node - {self.__srcdom0} : {self.__srcdomU} for the operation.")

    def mGetSrcDomU(self):
        return self.__srcdomU

    def mGetSrcDom0(self):
        return self.__srcdom0

    def mSetSrcDomU(self, aHost):
        self.__srcdomU = aHost

    def mSetSrcDom0(self, aHost):
        self.__srcdom0 = aHost

    def mUpdateNetworkConfig(self, aHostType, aNetworks):
        _host_type = aHostType
        _networks = aNetworks
        _ebox = self.__eboxobj

        #private
        _dict = [_dict for _dict in _networks if 'private' in list(_dict.keys())]
        if _dict:
            _dict = _dict[0]
            if _host_type == 'domU' and (_ebox.isDBonVolumes() or _ebox.isBaseDB()):
                self.__reshape_conf[_host_type]['priv1'] = ""
                self.__reshape_conf[_host_type]['priv2'] = ""
            else:
                self.__reshape_conf[_host_type]['priv1'] = _dict['private'][0]
                self.__reshape_conf[_host_type]['priv2'] = _dict['private'][1]
        #admin
        _dict = [_dict for _dict in _networks if 'admin' in list(_dict.keys())]
        if _dict:
            _dict = _dict[0]
            if _dict['admin']:
                self.__reshape_conf[_host_type]['admin'] = _dict['admin'][0]
            else:
                self.__reshape_conf[_host_type]['admin'] = ""
        else:
            self.__reshape_conf[_host_type]['admin'] = ""
        #client
        _dict = [_dict for _dict in _networks if 'client' in list(_dict.keys())]
        if _dict:
            _dict = _dict[0]
            ebMiscFx.mReplaceDiscover(_dict['client'][0])
            self.__reshape_conf[_host_type]['client'] = _dict['client'][0]
        #backup
        _dict = [_dict for _dict in _networks if 'backup' in list(_dict.keys())]
        if _dict:
            _dict = _dict[0]
            ebMiscFx.mReplaceDiscover(_dict['backup'][0])
            self.__reshape_conf[_host_type]['backup'] = _dict['backup'][0]
        #dr
        _dict = [_dict for _dict in _networks if 'dr' in list(_dict.keys())]
        if _dict:
            _dict = _dict[0]
            self.__reshape_conf[_host_type]['dr'] = _dict['dr'][0]
        #drVip
        _dict = [_dict for _dict in _networks if 'drVip' in list(_dict.keys())]
        if _dict:
            _dict = _dict[0]
            self.__reshape_conf[_host_type]['drVip'] = _dict['drVip'][0]
        #interconnect
        _dict = [_dict for _dict in _networks if 'interconnect' in list(_dict.keys())]
        if _dict:
            _dict = _dict[0]
            if _host_type == 'domU' and _ebox.isBaseDB():
                self.__reshape_conf[_host_type]['interconnect1'] = ""
                self.__reshape_conf[_host_type]['interconnect2'] = ""
            else:
                self.__reshape_conf[_host_type]['interconnect1'] = _dict['interconnect'][0]
                self.__reshape_conf[_host_type]['interconnect2'] = _dict['interconnect'][1]
        #vip
        _dict = [_dict for _dict in _networks if 'vip' in list(_dict.keys())]
        if _dict:
            _dict = _dict[0]
            self.__reshape_conf[_host_type]['vip'] = _dict['vip'][0]
        #ilom
        _dict = [_dict for _dict in _networks if 'ilom' in list(_dict.keys())]
        if _dict:
            _dict = _dict[0]
            self.__reshape_conf[_host_type]['ilom'] = _dict['ilom'][0]
        #ntp
        _dict = [_dict for _dict in _networks if 'ntp' in list(_dict.keys())]
        if _dict:
            _dict = _dict[0]
            self.__reshape_conf[_host_type]['ntp'] = _dict['ntp']
        #dns
        _dict = [_dict for _dict in _networks if 'dns' in list(_dict.keys())]
        if _dict:
            _dict = _dict[0]
            self.__reshape_conf[_host_type]['dns'] = _dict['dns']

    def initReshapeConf(self, aOptions):
        _ebox = self.__eboxobj
        _debug = _ebox.mIsDebug()
        if _debug :
            ebLogDebug("*** aOptions.jsonconf = %s" % aOptions.jsonconf)
        _reshape_config = aOptions.jsonconf['reshaped_node_subset']

        self.mValidateReshapePayload(aOptions)

        #add all requested compute nodes
        self.__reshape_conf['nodes'] = []
        for _compute in _reshape_config['added_computes']:
            self.__reshape_conf['action'] = 'ADD_NODE'
            self.__reshape_conf['dom0'] = {}
            self.__reshape_conf['domU'] = {}
            self.__reshape_conf['dom0']['hostname'] = _compute['compute_node_hostname']
            #
            _networks = _compute['network_info']['computenetworks']
            self.mUpdateNetworkConfig('dom0', _networks)

            if 'racknum' in _compute['rack_info'].keys():
                _rack_num = _compute['rack_info']['racknum']
            else:
                _rack_num = "1"

            self.__reshape_conf['dom0']['rack_num'] = _rack_num
            self.__reshape_conf['dom0']['uloc'] = _compute['rack_info']['uloc']

            self.__reshape_conf['domU']['hostname'] = _compute['virtual_compute_info']['compute_node_hostname']
            _networks = _compute['virtual_compute_info']['network_info']['virtualcomputenetworks']

            # For X7 and X8 when admin network is not present skip the oedacli admin part 
            # and admin network is not copied into self.__reshape_conf dictionary
            self.mUpdateNetworkConfig('domU', _networks)

            # Store CDB info (to be synced on the new node)
            self.__reshape_conf['domU']['db_info'] = None
            if 'db_info' in _compute:
                self.__reshape_conf['domU']['db_info'] = ",".join(_dbinfo['dbname'] for _dbinfo in _compute['db_info'])

            self.__reshape_conf['nodes'].append({'dom0': self.__reshape_conf['dom0'], 'domU': self.__reshape_conf['domU']})

            del self.__reshape_conf['dom0']
            del self.__reshape_conf['domU']

        #remove all requested compute nodes
        for _compute in _reshape_config['removed_computes']:
            self.__reshape_conf['action'] = 'DELETE_NODE'
            self.__reshape_conf['dom0'] = {}
            self.__reshape_conf['domU'] = {}
            self.__reshape_conf['dom0']['hostname'] = _compute['compute_node_hostname']
            self.__reshape_conf['domU']['hostname'] = _compute['compute_node_virtual_hostname']
            self.__reshape_conf['keep_dyndep_cache'] = _compute.get('keep_dyndep_cache', 'False')

            self.__reshape_conf['nodes'].append({'dom0': self.__reshape_conf['dom0'], 'domU': self.__reshape_conf['domU']})

            del self.__reshape_conf['dom0']
            del self.__reshape_conf['domU']

        if self.__reshape_conf['action'] == 'DELETE_NODE':
            if 'node_recovery_flow' in _reshape_config.keys():
                self.__node_recovery = _reshape_config['node_recovery_flow']

        if self.__reshape_conf['action'] == 'ADD_NODE':
            self.__reshape_conf['full_compute_to_virtualcompute_list'] = _reshape_config['full_compute_to_virtualcompute_list']

        ebLogInfo("self.__reshape_conf = %s" % self.__reshape_conf)


    def mUpdateDom0DomUPair(self, aClusterId=None):

        _ebox = self.__eboxobj

        # If aClusterId is not defined return the first cluster
        # By default contains only entry corresponding to the cluster at hand
        if not aClusterId:
            clusterId = _ebox.mGetClusters().mGetCluster().mGetCluId()
        else:
            clusterId = aClusterId

        _ebox.mSetElasticOldDom0DomUPair(copy.deepcopy(_ebox.mReturnDom0DomUPair()))

        _list = [ [x['dom0']['hostname'], x['domU']['hostname']] for x in self.__reshape_conf['nodes'] ]

        _ebox.mSetDomUsDom0s(clusterId, _list)

    def mValidateReshapePayload(self, aOptions):

        _ebox = self.__eboxobj
        #parse json payload, to identify request is for add node or delete node
        if aOptions is not None and aOptions.jsonconf is not None and 'reshaped_node_subset' in list(aOptions.jsonconf.keys()):
            nsParams = aOptions.jsonconf['reshaped_node_subset']
            if len(nsParams['removed_computes']) > 0 and len(nsParams['added_computes']) > 0:
                _detail_error = "Reshape service json payload: Add and Remove node not allowed in single operation"
                _ebox.mUpdateErrorObject(gNodeElasticError['RESHAPE_FAILED_SINGLE_OPERATION'], _detail_error)
                raise ExacloudRuntimeError(0x0768, 0xA, _detail_error)

            if not len(nsParams['participating_computes']) > 0:
                _detail_error = "Reshape service json payload: participating_computes nodes should be greater than zero "
                _ebox.mUpdateErrorObject(gNodeElasticError['COMP_NODE_CNT_ZERO'], _detail_error)
                raise ExacloudRuntimeError(0x0770, 0xA, _detail_error)

            #TODO:
            #add more validation for participant nodes, retained nodes

        else:
            _detail_error = "Invalid reshape service json payload " 
            _ebox.mUpdateErrorObject(gNodeElasticError['RESHAPE_VALIDATION_FAILED'], _detail_error)
            raise ExacloudRuntimeError(0x0770, 0xA, _detail_error)


    # Temporary work around for bug 32971743
    #  if gi_home/oracle.ahf directory is present then
    #  - move gi_home/oracle.ahf directory to oracle_base before addNode
    #  - move oracle_base/oracle.ahf directory back to gi_home if we moved it before addNode
    def mMoveAhfDataDir(self, _srcdomU, _preAddNode=False, _movedToObase=False, _restartTFA=False):
        # if post addNode and we didn't move oracle.ahf before then nothing to do
        if _preAddNode is False and _movedToObase is False:
            return

        _ebox = self.__eboxobj

        # GET GI_HOME, ORACLE_BASE
        _gihome, _, _obase = _ebox.mGetOracleBaseDirectories(aDomU = _srcdomU)
        _tfaRunningStatus = False

        # connect to source domU
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_srcdomU)

        # before addNode and oracle.ahf is present under gi_home
        if _preAddNode:
            if _node.mFileExists(_gihome + '/oracle.ahf') is True:
                # stop if TFA is running
                _tfaRunningStatus = self.mToggleTFA(_gihome, _node)
                ebLogInfo('*** Moving oracle.ahf directory out of GI Home')
                _cmd = "/bin/mv {0}/oracle.ahf {1}/oracle.ahf.gihome".format(_gihome, _obase)
                _i, _o, _e = _node.mExecuteCmd(_cmd)
            else:
                _node.mDisconnect()
                # oracle.ahf is NOT present under gi_home
                # so nothing to move back post addNode
                return False
        else: # post addNode and oracle.ahf is present under oracle_base
            if _node.mFileExists(_obase + '/oracle.ahf.gihome') is True and _movedToObase is True:
                ebLogInfo('*** Moving oracle.ahf directory back to GI Home')
                _cmd = "/bin/mv {0}/oracle.ahf.gihome {1}/oracle.ahf".format(_obase, _gihome)
                _i, _o, _e = _node.mExecuteCmd(_cmd)
                if _restartTFA:
                    self.mToggleTFA(_gihome, _node, _restartTFA)
        _node.mDisconnect()
        return True 

    def mToggleTFA(self, aGiHomePath, aNode, aStart = False):
        _node = aNode
        _tfactl_path = aGiHomePath + "/bin/tfactl"
        if _node.mFileExists(_tfactl_path) is True:
            ebLogInfo("*** TFACTL path is %s"%(_tfactl_path))
        else:
            _tfactl_path = "/usr/bin/tfactl"
        if aStart:
            _cmdstr = _tfactl_path + " -check"
            ebLogDebug("Executing cmd : %s"%(_cmdstr))
            _i, _o, _e = _node.mExecuteCmd(_cmdstr) 
            _out = _o.readlines()
            ebLogInfo("*** Command %s executed with response %s"%(_cmdstr,_out))
            if _node.mGetCmdExitStatus() == 0:
                return False

            _cmdstr = _tfactl_path + " start"
            ebLogDebug("Executing cmd : %s"%(_cmdstr))
            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
            _out = _o.readlines()
            ebLogInfo("*** Command %s executed with response %s"%(_cmdstr,_out))
            _exitstatus = _node.mGetCmdExitStatus()
            if _exitstatus != 0:
                ebLogWarn("*** Could not start TFA services due to error: %s"%(_e))
                return False
            return True
        else:
            _cmdstr = _tfactl_path + " -check"
            ebLogDebug("Executing cmd : %s"%(_cmdstr))
            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
            _out = _o.readlines()
            ebLogInfo("*** Command %s executed with response %s"%(_cmdstr,_out))
            if _node.mGetCmdExitStatus() != 0:
                return False
            _cmdstr = _tfactl_path + " shutdown"
            ebLogDebug("Executing cmd : %s"%(_cmdstr))
            _i, _o, _e = _node.mExecuteCmd(_cmdstr)
            _out = _o.readlines()
            ebLogInfo("*** Command %s executed with response %s"%(_cmdstr,_out))
            if _node.mGetCmdExitStatus() != 0:
                ebLogWarn("*** Could not stop TFA services due to error: %s"%(_e))
                return False
            return True 

    def mSetOraBaseDirectories(self, aNewDomU, aGridHome, aOraBase):
        _newdomU = aNewDomU
        _gridhome = aGridHome
        _orabase = aOraBase

        # connect to New domU
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_newdomU)

        if _node.mFileExists(_orabase) is False:
            _cmd = f"/bin/mkdir -p {_orabase}"
            _node.mExecuteCmdLog(_cmd)
            _rc = _node.mGetCmdExitStatus()
            if _rc != 0:
                ebLogError(f'*** ORA BASE path {_orabase} creation failed ***')
                _node.mDisconnect()
                return
            ebLogInfo(f"*** ORA BASE path {_orabase} created successfully..")
        _cmd = f"/bin/chown -fR grid:oinstall {_orabase}"
        _node.mExecuteCmdLog(_cmd)

        _oracle_dir = _orabase.rsplit('/', 1)[0] + "/oracle"
        if _node.mFileExists(_oracle_dir) is False:
            _cmd = f"/bin/mkdir -p {_oracle_dir}"
            _node.mExecuteCmdLog(_cmd)
            _rc = _node.mGetCmdExitStatus()
            if _rc != 0:
                ebLogError(f'*** ORACLE path {_oracle_dir} creation failed ***')
                _node.mDisconnect()
                return
            ebLogInfo(f"*** ORACLE path {_oracle_dir} created successfully..")
        _cmd = f"/bin/chown -fR oracle:oinstall {_oracle_dir}"
        _node.mExecuteCmdLog(_cmd)

        if _node.mFileExists(_gridhome) is False:
            _cmd = f"/bin/mkdir -p {_gridhome}"
            _node.mExecuteCmd(_cmd)
            ebLogInfo(f"*** GRID HOME path {_gridhome} created successfully..")
        _cmd = f"/bin/chown -fR grid:oinstall {_gridhome}"
        _node.mExecuteCmd(_cmd)

        _grid_version = _gridhome.split('/')[-2]
        _cmd = f"/bin/chown -fR grid:oinstall /u02/app/{_grid_version}"
        _node.mExecuteCmdLog(_cmd)

        _ora_version = _orabase.split('/')[-2]
        _cmd = f"/bin/chown -fR grid:oinstall /u02/app/{_ora_version}"
        _node.mExecuteCmdLog(_cmd)

        _node.mDisconnect()

    def mSetGIHome(self, aGridHome):
        _gridhome = aGridHome
        _ebox = self.__eboxobj

        _oeda_path  = _ebox.mGetOedaPath()
        _oedacli_bin = _oeda_path + '/oedacli'
        _savexmlpath = _oeda_path + '/exacloud.conf'

        _oedacli_mgr = OedacliCmdMgr( _oedacli_bin, _savexmlpath)

        _uuid = _ebox.mGetUUID()
        _patchconfig = _ebox.mGetPatchConfig()
        _updatedxml = _oeda_path + '/exacloud.conf/patched_gihome_'  + _uuid + '.xml'
        _ebox.mExecuteLocal("/bin/cp {} {}".format(_patchconfig, _updatedxml))
                                                                                                                                                                                                                          
        _clusterName = _ebox.mGetClusters().mGetCluster().mGetCluName()
        _cluver = _ebox.mGetClusters().mGetCluster().mGetCluVersion()

        _oedacli_mgr.mUpdateGIHome(_clusterName, _cluver, _gridhome, _updatedxml, _updatedxml)
        ebLogInfo(f"Updating GI HOME PATH: {_gridhome}")
        _ebox.mSetPatchConfig(_updatedxml)
        _patchconfig = _ebox.mGetPatchConfig()
        _remoteconfig = _ebox.mGetRemoteConfig()
        _ebox.mCopyFile(_patchconfig, _remoteconfig)
        ebLogInfo('ebCluCtrl: Saved patched Cluster Config: ' + _updatedxml)

    def mUpgradeSystemImage(self, aImgVers, aNewDom0):
        """
        Upgrade/Copy system image in new dom0
        :param aImgVers : source domU image version
        :param aNewDom0 : New dom0
        """
        _ebox = self.__eboxobj
        _imgVersion = aImgVers
        _isKvm = _ebox.mIsKVM()

        _repo_download_location = ''
        if _ebox.mCheckConfigOption('ociexacc', 'True'):
            _repo_download_location = _ebox.mCheckConfigOption('ociexacc_exadata_patch_download_loc')

        # Taking a lock on the dom0 before copying System image
        _remote_lock = _ebox.mGetRemoteLock()
        with _remote_lock():
            _remoteImgFound, _localImgInfo, _imgCopied = copyVMImageVersionToDom0IfMissing(aNewDom0, _imgVersion, _isKvm, _repo_download_location)

        if _remoteImgFound or _imgCopied:
            ebLogInfo(f"System image {_imgVersion} synced accross the new dom0 {aNewDom0}")
        else:
            _detail_error = f"*** Could not sync system image {_imgVersion} to new dom0 {aNewDom0}" 
            ebLogError(_detail_error)
            _ebox.mUpdateErrorObject(gNodeElasticError['NO_SUITABLE_FIRST_BOOT_IMG'], _detail_error)
            raise ExacloudRuntimeError(0x0730, 0xA, "No suitable System first boot Image found. Aborting", aStackTrace=False)

        return _localImgInfo

    def mVerifyDomUSystemImage(self, aImgVersion):
        _ebox = self.__eboxobj
        _isRtg = mIsRtgImg(aImgVersion)
        _imgName = formatVMImageBaseName(aImgVersion, False, _isRtg)
        
        _dpairs = _ebox.mGetOrigDom0sDomUs()

        # Patch XML (mSetMacVMImgName & mSetMacVMImgVersion)
        for _, _domU in _dpairs:            
            _domU_mac = _ebox.mGetMachines().mGetMachineConfig(_domU)
            # _domUImageName = _domU_mac.mGetMacVMImgName()
            if _domU_mac:
                _domU_mac.mSetMacVMImgName(_imgName)
                _domU_mac.mSetMacVMImgVersion(aImgVersion)

        _ebox.mSaveXMLClusterConfiguration()
        ebLogInfo('mVerifyDomUSystemImage: Saved patched System Image Version: ' + _ebox.mGetPatchConfig())  

    def mDisplayDomUDnsNtpConfig(self, aSrcDomU):
        _ebox = self.__eboxobj
        _domU_mac = _ebox.mGetMachines().mGetMachineConfig(aSrcDomU)
        _domU_xml_dns_list = _domU_mac.mGetDnsServers()
        _domU_xml_ntp_list = _domU_mac.mGetNtpServers()
        ebLogInfo(f"DomU DNS list from Config: {_domU_xml_dns_list}")
        ebLogInfo(f"DomU NTP list from Config: {_domU_xml_ntp_list}")
        
    def mGetNtpConf(self, aSrcDomU):
        _ntp_config_file = ""
        with connect_to_host(aSrcDomU, get_gcontext(), username="root") as _node:
            if _node.mFileExists('/etc/chrony.conf') is True:
                ebLogInfo(f"chrony.conf file found on DomU {aSrcDomU}")
                _ntp_config_file = "/etc/chrony.conf"
            else:
                if _node.mFileExists('/etc/ntp.conf') is True:
                    ebLogInfo(f"ntp.conf file found on DomU {aSrcDomU}")
                    _ntp_config_file = "/etc/ntp.conf"
        return _ntp_config_file
        
    def mGetDomUDnsIP(self, aSrcDomU):
        _dns_list = []
        _dns_cmd = "/usr/bin/cat /etc/resolv.conf | /usr/bin/grep '^nameserver[[:space:]][0-9]' | /usr/bin/awk '{print $2}'"
        with connect_to_host(aSrcDomU, get_gcontext(), username="root") as _node:
            ebLogTrace(f"Executing cmd : {_dns_cmd}")
            _i,_o,_ = _node.mExecuteCmd(_dns_cmd)
            if not _node.mGetCmdExitStatus():
                _out = _o.readlines()
                for _line in _out:
                    _dns_list.append(_line.strip())
                ebLogInfo(f"*** Command {_dns_cmd} executed with response :{_dns_list}")
            else:
                raise Exception('mExecuteCmd Failed', _node.mGetHostname(), _dns_cmd)
        return _dns_list
    
    def mGetDomUNtpIP(self, aSrcDomU, _ntp_config_file):
        _ntp_list = []
        _ntp_cmd = "/usr/bin/cat %s | /usr/bin/grep '^server[[:space:]][0-9]' | /usr/bin/awk '{print $2}'"%(_ntp_config_file)
        with connect_to_host(aSrcDomU, get_gcontext(), username="root") as _node:
            ebLogTrace(f"Executing cmd : {_ntp_cmd}")
            _i,_o,_ = _node.mExecuteCmd(_ntp_cmd)
            if not _node.mGetCmdExitStatus():
                _out = _o.readlines()
                for _line in _out:
                    _ntp_list.append(_line.strip())
                ebLogInfo(f"*** Command {_ntp_cmd} executed with response :{_ntp_list}")
            else:
                raise Exception('mExecuteCmd Failed', _node.mGetHostname(), _ntp_cmd)
        return _ntp_list
        
    def mPatchXML(self, aSrcDomU):

        _ebox = self.__eboxobj

        # Patch xml with source domU's timezone.
        _domU_mac = _ebox.mGetMachines().mGetMachineConfig(aSrcDomU)
        _timeZone = _domU_mac.mGetMacTimeZone()
       
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost = aSrcDomU)
        _, _o, _e = _node.mExecuteCmd("/bin/timedatectl | grep 'Time zone:'")
        _out = _o.readlines()
        _node.mDisconnect()
        try:
            _tz = _out[0].split(':')[1].split('(')[0].strip()
        except Exception as e:
             _detail_error = f'Output of timedatectl: {_out}' 
             ebLogError(_detail_error)
             _ebox.mUpdateErrorObject(gNodeElasticError['FETCH_TIMEZONE_FAILED'], _detail_error)
             raise ExacloudRuntimeError(0x0747, 0xA, "Unable to fetch timezone from domU") from e

        if _tz != _timeZone:
            _ebox.mPatchClusterInfo(self.__options, {'TIMEZONE' : _tz})
           
        # Bug 35236850: Patch source node xml with source DomU's DNS and NTP servers
        _ntp_config_file = ""
        try:
            _ntp_config_file = self.mGetNtpConf(aSrcDomU)
            if not _ntp_config_file:
                raise Exception("chrony.conf and ntp.conf file not found in DomU {aSrcDomU}")
        except Exception as e:
            _detail_error = f"Cannot Proceed with Patching of XML..Could not retrieve ntp configuration file from DomU {aSrcDomU} : {str(e)}"
            ebLogError(_detail_error)
            _ebox.mUpdateErrorObject(gNodeElasticError['FAILED_DOMU_XML_PATCHING'], _detail_error)
            raise ExacloudRuntimeError(0x0623, 0xA, _detail_error)
        
        try:
            _dns_list = self.mGetDomUDnsIP(aSrcDomU)
        except Exception as e:
            _detail_error = f"Cannot Proceed with Patching of XML..Failed to retrieve DNS Server IPs from DomU {aSrcDomU} with error {str(e)}"
            ebLogError(_detail_error)
            _ebox.mUpdateErrorObject(gNodeElasticError['FAILED_DOMU_XML_PATCHING'], _detail_error)
            raise ExacloudRuntimeError(0x0623, 0xA, _detail_error)
            
        try:
            _ntp_list = self.mGetDomUNtpIP(aSrcDomU, _ntp_config_file)
        except Exception as e:
            _detail_error = f"Cannot Proceed with Patching of XML..Failed to retrieve NTP Server IPs from DomU {aSrcDomU} with error {str(e)}"
            ebLogError(_detail_error)
            _ebox.mUpdateErrorObject(gNodeElasticError['FAILED_DOMU_XML_PATCHING'], _detail_error)
            raise ExacloudRuntimeError(0x0623, 0xA, _detail_error)
        
        #patch XML with DNS and NTP server info from source DomU and save XML
        ebLogInfo("DNS and NTP server values before patching:")
        self.mDisplayDomUDnsNtpConfig(aSrcDomU)
        _domU_mac.mSetNtpServers(_ntp_list)
        _domU_mac.mSetDnsServers(_dns_list)

        _ebox.mSaveXMLClusterConfiguration()
        ebLogInfo("DNS and NTP server values after patching:")
        self.mDisplayDomUDnsNtpConfig(aSrcDomU)

    def mGetHugePages(self, aDomU):
        _domU= aDomU

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_domU)

        _cmd = "/usr/sbin/sysctl -n vm.nr_hugepages"
        _in, _out, _err = _node.mExecuteCmd(_cmd)
        if not _out:
            ebLogError("Failed to get the value of the sysctl parameter: vm.nr_hugepages")
            _node.mDisconnect()
            return -1
        
        _curr_paramval = _out.readlines()[0].strip()
        ebLogInfo(f"Current value of vm.nr_hugepages in domU:{_domU} is {_curr_paramval}")

        _node.mDisconnect()

        return _curr_paramval
    
    def mUpdateHugePages(self, aDomU):

        _ebox = self.__eboxobj
        _domU = aDomU

        #Fetch Hugepages from srcdomU
        _srcdomU = self.mGetSrcDomU()
        _paramval = self.mGetHugePages(_srcdomU)
        if _paramval == -1 or _paramval == '0':
            ebLogError(f'HugePage value not set in src domU:{_srcdomU}')
            return

        #Check if Hugepages in source domU matches with new domU. Then skip updating in new domU.
        _currval = self.mGetHugePages(_domU)
        if _paramval == _currval:
            ebLogInfo(f"Hugepages in source domU matches with new domU. Skip updating in new domU.")
            return

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_domU)

        _ebox.mSetSysCtlConfigValue(_node, "vm.nr_hugepages", _paramval, aRaiseException=False)

        self.mGetHugePages(_domU)

        _node.mDisconnect()


    # OC5: There is a special case where FS encryption is applied even
    # when the 'fs_encryption' flag is not present in the payload. For
    # this, we will need to check if the base domU is encrypted. If it 
    # is and the flag is missing, we must fail the flow gracefully.

    def mCheckMissingEncryptionFlag(self, aDomU, aFileSystem):
        # Connect to the base domU
        with connect_to_host(aDomU, get_gcontext()) as _vm_node:
            # Dismiss if domU does not have FS encryption enabled
            if not getMountPointInfo(_vm_node, aFileSystem).is_luks:
                ebLogInfo(f"{aFileSystem} is not encrypted in {aDomU}")
                return
            # At this point we can assume FS encryption is enabled, so if the
            # payload does not contain 'fs_encryption', we should fail the flow
            _options = self.__options
            _json = _options.jsonconf

            if "fs_encryption" not in list(_json.keys()):
                _err_msg = (f"Base domU has FS encryption enabled but the "
                            f"\'fs_encryption\' flag is missing in the payload.")
                _action_msg = ("Ensure the payload contains fs_encryption data, "
                            "then undo/retry.")
                ebLogCritical(_err_msg, _action_msg)
                raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)


    #
    # RESHAPE SERVICE
    #
    def mReshapeVMGI(self, aOptions=None):
        """
        Automata driving Reshape Service,
        :param aOptions: Options context
        :return:
        """
        _ebox = self.__eboxobj
        _action     = self.__reshape_conf['action']

        if _action == 'ADD_NODE':
            ebLogInfo("Invoking Add Node operation")
            self.mAddNode(aOptions)

        elif _action == 'DELETE_NODE':
            ebLogInfo("Invoking Delete Node operation")
            self.mDeleteNode(aOptions)

        else:
            _detail_error = "Invalid reshape service action %s " % _action 
            ebLogError(_detail_error)
            _ebox.mUpdateErrorObject(gNodeElasticError['INVALID_RESHAPE_ACTION'], _detail_error)


    def mCallBack(self, aStepName):

        _step_name = aStepName
        # Restore entries
        _ebox = self.__eboxobj
        _ebox.mSaveOEDASSHKeys()
        
        # Elastic flow
        _aoptions = self.__options
        _newdom0UList = []   
        for _node in self.__reshape_conf['nodes']:
            _newdom0 = _node['dom0']['hostname']  
            _newdom0UList.append([_node['dom0']['hostname'], _node['domU']['hostname']])
        _dom0UList = _newdom0UList
        _srcdomU = self.__srcdomU

        _gridhome, _, _ora_base = _ebox.mGetOracleBaseDirectories(aDomU = _srcdomU)

        if _step_name == 'CELL_CONNECTIVITY':
            # operations performed before Grid install 
            _ebox.mAcquireRemoteLock()
            _step_time = time.time()

            # If requested:
            # Create the u01 encrypted disk on the domUs
            self.mCheckMissingEncryptionFlag(_srcdomU, '/u01')

            if _ebox.mIsKVM() and (isEncryptionRequested(_aoptions, 'domU') or
                exacc_fsencryption_requested(_aoptions)):

                if not validateMinImgEncryptionSupport(
                    _ebox,  _newdom0UList):
                    _err_msg = (f"Some nodes failed the "
                        f"minimum image version requirements for Encryption. ")
                    _action_msg = ("Disable encryption on the input payload or upgrade "
                        "the nodes and undo/retry")
                    ebLogCritical(_err_msg, _action_msg)
                    raise ExacloudRuntimeError(0x96, 0x0A, _err_msg)

                # If we're in ExaCC, we must create a socket to use
                # for the fs encryption passphrase communication
                if _ebox.mIsOciEXACC():
                    for _dom0, _domU in _newdom0UList:
                        mSetLuksChannelOnDom0Exacc(_ebox, _dom0, _domU)

                    # In ExaCC, set the domU clustersjson list for FS Encryption
                    _ebox.mSaveClusterDomUList()

                # Run the u01 encryption entry point
                setupU01EncryptedDiskParallel(
                        _ebox, _aoptions, _newdom0UList)

            # U02 Creation
            _ebox.mPatchVMCfg(_aoptions, _gridhome)             # Customize VM.CFG (e.g. additional images, partitions,...)
            _ebox.mLogStepElapsedTime(_step_time, 'Patching VM Configuration')
            _ebox.mReleaseRemoteLock()

            # Perform Encryption on Fs Mounted on /u02 if requested
            # We need to call this right after /u02 is available, before other
            # processes start using the FS and interefere with the encryption
            self.mCheckMissingEncryptionFlag(_srcdomU, '/u02')

            if (isEncryptionRequested(_aoptions, 'domU') and not _ebox.mIsKVM()
                 and not _ebox.mIsOciEXACC()):
                ebLogInfo(('*** mCallBack: Before Grid Install '
                           'Encryption of /u02 for domUs'))
                for _dom0, _domU in _ebox.mReturnDom0DomUPair():
                    encryptionSetupDomU(_ebox, _dom0, _domU, '/u02')

            # Reference: bug 35834771
            # Make sure bondeth0/1 both have an IP assigned, else try to
            # force it in case ip is in standby vnic useful to fix
            # ip in wrong vnic issues during cluster replacement)
            if _ebox.mIsExabm() and not _ebox.isATP():
                _net_val_mgr = ebNetworkValidations(_ebox, _newdom0UList)
                _net_val_mgr.mCheckClientBackupIPSet()

        for _dom0, _domU in _dom0UList:

            if _step_name == "CREATE_USERS":
                ebLogInfo(f'*** mCallBack: Updating hostname of DomU: {_domU}')
                with connect_to_host(_domU,get_gcontext()) as _node:
                    _rc = 0
                    _i, _o, _e = _node.mExecuteCmd('/usr/bin/hostname')
                    _rc = _node.mGetCmdExitStatus()
                    if not _rc:
                        _out = _o.readlines()
                        _hostname = _out[0].split('.')[0]
                        _i, _o, _e = _node.mExecuteCmd(f'/usr/bin/hostnamectl set-hostname {_hostname}')
                        _rc = _node.mGetCmdExitStatus()
                    if _rc:
                        ebLogWarn(f"Hostname update failed for DomU: {_domU}")
            elif _step_name == "CONFIG_CLUSTERWARE":
                _dir = _gridhome.split('/', 2)[1]
                if _dir == "u02":
                    ebLogInfo(f'*** mCallBack: Creating Oracle Base Directories on DomU: {_domU}')
                    self.mSetOraBaseDirectories(_domU, _gridhome, _ora_base)
                    self.mSetGIHome(_gridhome)


    def mSetDRVip(self, aDomU):
        _domu = aDomU
        _dr_vips_ip_list = []
        for _json in self.__reshape_conf['nodes']:
            if 'drVip' in _json['domU']:
                _dr_vip = _json['domU']['drVip']
                _domu_hostname_short = _json['domU']['hostname'].split(".")[0]
                _dr_vips_ip_list.append(f"{_domu_hostname_short}:{_dr_vip['ipaddr']}")
        if _dr_vips_ip_list:
            with connect_to_host(_domu, get_gcontext(), username="root") as _node:
                _dbaascli_full_path = node_cmd_abs_path_check(_node, "dbaascli")
                _cmd_dr_vip = f"{_dbaascli_full_path} dataguard createDrConfig"
                _cmd_dr_vip += f" --drVipList {','.join(_dr_vips_ip_list)} "
                _node.mExecuteCmdLog(_cmd_dr_vip)
                if _node.mGetCmdExitStatus() != 0:
                    _err_msg = f"*** Error: dbaascli command '{_cmd_dr_vip}' failed to configure dr-vips on the DOMU {_domu} during elastic compute addition."
                    ebLogError(_err_msg)
                    raise ExacloudRuntimeError(0x0116, 0xA, _err_msg,
                                               aStackTrace=True, aDo=True)
                else:
                    ebLogInfo(f"The dbaascli command '{_cmd_dr_vip}' ran successfully on the DOMU {_domu} to configure dr-vips during elastic compute addition.")
        else:
            ebLogInfo(f"Not configuring DR VIPs on the DOMUs. DR VIPs were not found in the payload for elastic compute addition.")

    # Asssume a half rack with config and keys present in clusters/AA'BB'CC'DD'/
    # and existing cluster containing AA'BB' (clusters/AA'BB'/)
    # Where X - Dom0, X' - DomU
    # mAddNode() adds CC' to the existing cluster (AA'BB') 
    # As part of this, config and keys corresponding to this new cluster 
    # configuration will be stored in clusters/AA'BB'CC'/
    # ADD_NODE_FIX_MR
    def mAddNode(self, aOptions=None):

        _rc = 0
        _srcdom0 = self.mGetSrcDom0()
        _srcdomU = self.mGetSrcDomU()
        _newdomUList = [x['domU']['hostname'] for x in self.__reshape_conf['nodes']]
        _newdom0List = [x['dom0']['hostname'] for x in self.__reshape_conf['nodes']]
        _ebox = self.__eboxobj
        _utils = _ebox.mGetExascaleUtils()
        _pchecks = ebCluPreChecks(_ebox)
        _domUDict = {}

        # Construct grid home using the grid version in the existing node.
        _gridhome, _, _ = _ebox.mGetOracleBaseDirectories(aDomU = _srcdomU)

        _OrigDom0DomUList = _ebox.mGetOrigDom0sDomUs()
        for x in self.__reshape_conf['nodes']:
            _entry = [x['dom0']['hostname'], x['domU']['hostname']]
            if _entry not in _OrigDom0DomUList:
                _OrigDom0DomUList.append(_entry)
        _ebox.mSetOrigDom0sDomUs(_OrigDom0DomUList)

        _step_list = [
            "OSTP_PREVM_INSTALL",
            "CREATE_GUEST",
            "CREATE_USERS",
            "CELL_CONNECTIVITY",
            "CONFIG_CLUSTERWARE",
            "RUN_ROOTSCRIPT",
            "OSTP_POSTVM_INSTALL",
            "OSTP_POSTINSTALL_CLUSTER",
            "OSTP_POSTGI_INSTALL",
            "OSTP_POSTGI_NID",
            "OSTP_PREDB_INSTALL",
            "OSTP_END_INSTALL",
            "OSTP_BACKUP_GOLDIMG"
        ]

        if _ebox.mIsAdbs():
            _step_list.insert(0,"UPDATE_ADBS_VM")
            _step_list.append("REVERT_ADBS_CONFIG")

        if _ebox.mIsExaScale():

            _step_list = [
                "OSTP_PREVM_INSTALL",
                "CREATE_GUEST",
                "CREATE_USERS",
                "OSTP_POSTVM_INSTALL",
                "OSTP_EXASCALE_COMPLETE",
                "OSTP_END_INSTALL"
            ]

        if _ebox.mIsXS():
            _step_list = [
                "OSTP_PREVM_INSTALL",
                "CREATE_GUEST",
                "CREATE_USERS",
                "CELL_CONNECTIVITY",
                "CONFIG_CLUSTERWARE",
                "RUN_ROOTSCRIPT",
                "OSTP_POSTVM_INSTALL",
                "OSTP_POSTINSTALL_CLUSTER",
                "OSTP_POSTGI_INSTALL",
                "OSTP_EXASCALE_COMPLETE",
                "OSTP_PREDB_INSTALL",
                "OSTP_END_INSTALL",
                "OSTP_BACKUP_GOLDIMG"
            ]

        _ebox.mUpdateStatus('Add Node to existing cluster')
        _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic ADD Node in progress", "ADD_NODE")
        self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, "ADD_NODE", "In Progress", _stepSpecificDetails)

        if aOptions.steplist: 
            _step_list = str(aOptions.steplist).split(",") 

        if 'undo' not in aOptions:
            _undo = False   
        elif str(aOptions.undo).lower() == "true" or aOptions.undo == True:
            _undo = True
        else:
            _undo = False 
        
        _do = not _undo

        if "OSTP_CREATE_VM" in _step_list:
            if _do:
                _step_list = ["OSTP_PREVM_INSTALL", "CREATE_GUEST", "CREATE_USERS", "CELL_CONNECTIVITY", "CONFIG_CLUSTERWARE", "RUN_ROOTSCRIPT"]
            else:
                _step_list = ["RUN_ROOTSCRIPT", "CONFIG_CLUSTERWARE", "CELL_CONNECTIVITY", "CREATE_USERS", "CREATE_GUEST"]

        if _ebox.mHasNatAndCustomerNet():
            _ddp_nat = _ebox.mReturnDom0DomUNATPair()
            for x in self.__reshape_conf['nodes']:
                _domU_nathostname = (x['domU'].get('admin') or {}).get('hostname')
                if _domU_nathostname is None:
                    _domU_nathostname = x['domU']['client']['nathostname']
                _entry = [x['dom0']['hostname'], _domU_nathostname]
                if _entry not in _ddp_nat:
                    _ddp_nat.append(_entry)
            _cludir = self.mBuildClusterDir(sorted(_ddp_nat))
        else:
            #Copy the keys from OEDA staging area (WorkDir) to the new cluster directory & cluster/oeda
            _cludir = self.mBuildClusterDir(sorted(_ebox.mGetOrigDom0sDomUs()))
        _key = _ebox.mGetKey()
        _ebox.mSetKey(_cludir)
        _ebox.mSaveOEDASSHKeys()

        # Update OEDA properties
        _step_time = time.time()                  
        _ebox.mUpdateOEDAProperties(aOptions)     
        _ebox.mLogStepElapsedTime(_step_time, 'Updating OEDA environment')

        # Need network setup information from the existing cluster before it is set to None
        _net_info_dr = {}
        for _json in self.__reshape_conf['nodes']:

            _net_info = None
            if 'dr' in _json['domU'] and _ebox.mIsOciEXACC():
                _ebox.mSetDRNetPresent(True)
                _net_info = _ebox.mGetNetworkSetupInformation(aNetworkType="dr", aDom0=_json['dom0']['hostname'])
            _net_info_dr[_json['dom0']['hostname']] = _net_info

        # Hereon, the dom0-domU pair contain only the new node(dom0-domU) being added.
        self.mUpdateDom0DomUPair(None)
        _ebox.mSetSharedEnv(None)
        _ebox.mCheckSharedEnvironment()

        # sets the cluster path to clusters/CC'/
        _ebox.mSetClusterPath('clusters/' + _ebox.mGetKey())

        # Check ASM is up before Add Node (not needed for Adbs)
        if _ebox.mIsAdbs() is False:
            _ebox.mCheckCrsIsUp(self.mGetSrcDomU(), [self.mGetSrcDomU()],'root', int(_ebox.mCheckConfigOption('crs_timeout_add_node_minutes')))

            # Patch clusterName in XML before Add Node (not needed for Adbs)
            _ebox.mUpdateClusterName(self.mGetSrcDomU())

        # Patch EGS clusterName in XML, by fetching the EGS clustername from cells
        if _ebox.mIsXS():
           _utils.mPatchEGSClusterName(aOptions)

        # To reuse pre-post VM steps (from exaBoxCluCtrl) dom0-domU pair
        # is updated. Also, self.__key and self.__clusterpath (used in 
        # pre-post VM steps) is updated because it is coupled with 
        # dom0-domU pair).

        for step in _step_list:

            ebLogInfo(f"Executing do: {_do} / undo: {_undo} of step: {step}")
            if step == "UPDATE_ADBS_VM" and _do:
                for _, _domU in mReturnSrcDom0DomUPair(_ebox):
                    _domU_obj = mGetorCreateDomUObj(_domU, _domUDict)
                    _domU_obj.mUpdateGridHomePath()
            elif step == "OSTP_PREVM_INSTALL" and _do:
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Add Compute Prevm install in progress", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, step, "In Progress", _stepSpecificDetails)
                if _ebox.mIsKVM():
                    _pchecks.mAddMissingNtpDnsIps(_newdom0List)

                # Add pre-checks in case a failed VM move left stale bridges on dom0s
                ebLogInfo(f"Checking for stale bridges...")
                _pchecks.mNetworkDom0PreChecks()

                self.mExecutePreVMStep(aOptions, _newdomUList, aNetInfoDR=_net_info_dr)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Add Compute Prevm install Completed", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, step, "Done", _stepSpecificDetails)

            elif step in ["CREATE_GUEST", "CREATE_USERS", "CELL_CONNECTIVITY", "CONFIG_CLUSTERWARE", "RUN_ROOTSCRIPT"] and _do:
                if step == "RUN_ROOTSCRIPT":
                    if _ebox.mIsAdbs():
                        _pswd = _ebox.mGetAsmSysPasswordForAdbs('asmsys', _srcdomU)
                        _ebox.mUpdateOedaUserPswd(_ebox.mGetOedaPath(), "non-root", _pswd)
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Add Compute run rootscripts in progress", step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, step, "In Progress", _stepSpecificDetails) 
                    _val = _ebox.mCheckConfigOption("exacloud_health_install_cluster", "True")
                    if (_val):
                        _csu = csUtil()
                        _csu.mHealthCheckClufy(_ebox)
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Add Compute run rootscripts in progress", step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 25, step, "In Progress", _stepSpecificDetails)
                else:
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', f"Elastic Add Compute step {step} in progress", step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, step, "In Progress", _stepSpecificDetails) 

                if step == "CREATE_GUEST" and _ebox.mIsXS():
                    _utils.mEnableQinQIfNeeded(aOptions, aDom0List=_newdom0List)
                    _failedList = []
                    #perform check to deduce if QinQ is enabled
                    if not _utils.mCheckRoCEIPs(aOptions, _failedList, aDom0List=_newdom0List):
                        # execute command to enable QinQ
                        ebLogInfo(f" *** Enabling QinQ on the Host Nodes {_failedList}. Host node will be restarted serially to handle that")
                        _utils.mSetupRoCEIPs(aOptions, _failedList, aDom0List=_newdom0List)
                        _rc = _utils.mValidateGuest(aOptions, _failedList)# validate domU after rebooting of dom0s for QinQ enabling
                        if _rc != 0:
                            ebLogError("*** DomU Validation failed after enabling QinQ")
                            return _rc

                self.mExecuteOEDACLIDoStep(_newdomUList, step, aOptions)

                if (step == "CREATE_GUEST") and _ebox.mIsAdbs():
                    mAddExacliPasswdToNewDomUs(_ebox, _srcdomU, _newdomUList)
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Add Compute create guest completed", step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, step, "Done", _stepSpecificDetails)

                if (step == "CELL_CONNECTIVITY") and _ebox.mIsAdbs():
                    # quorumdisks needs to be configured as in Phase 1 CONFIG_CLUSTERWARE is not getting executed
                    try: 
                        mUpdateQuorumDiskConfig(_ebox)
                    except Exception as e:
                        _msg = f"Failure in updating the quorum disk on the domUs. Error:{str(e)}"
                        ebLogError(_msg)
                        raise ExacloudRuntimeError(aErrorMsg=_msg)

                    # add copy of cellkey.ora to the newdomU
                    self.mCopyCellkeyOra(_srcdomU,_newdomUList)

                    _ebox.mAddUserDomU("opc", "2000", aSudoAccess=True, aPasswordLess=True)
                    for _user in ["oracle", "grid"]:
                        _ebox.mConfigurePasswordLessDomU(_user)
                    for _newdomU in _newdomUList:

                        # Call mSyncPSMKeys to syncup the keys in the new domU                                                                                                                                                  
                        # which were inserted in the existing VM's (as part of starter DB)  
                        self.mSyncPSMKeys(_srcdomU, _newdomU)
                    
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Add Compute cell connectivity completed", step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, step, "Done", _stepSpecificDetails)

                if (step == "CREATE_GUEST") and _ebox.mIsKVM():
                    _pchecks.mAddMissingNtpDnsIps(_newdom0List)
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Add Compute create guest completed", step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, step, "Done", _stepSpecificDetails)

                if step == "CREATE_GUEST":
                    _exascale = ebCluExaScale(_ebox)
                    if _ebox.isDBonVolumes() and _ebox.mCheckConfigOption("exadbxs_19c_invoke_oedacli", "False"):
                        _exascale.mAttachDBVolumetoGuestVMs(aWhen="AddNode")
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Add Compute create guest completed", step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, step, "Done", _stepSpecificDetails)

            elif step == "CREATE_GUEST" and _undo:
                # remove new node from origdom0domUList for undo- CREATE_GUEST
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Add Compute undo create guest is in progress", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, step, "In Progress", _stepSpecificDetails)
                _OrigDom0DomUList = _ebox.mGetOrigDom0sDomUs()
                for x in self.__reshape_conf['nodes']:
                    _OrigDom0DomUList.remove([x['dom0']['hostname'], x['domU']['hostname']])
                _ebox.mSetOrigDom0sDomUs(_OrigDom0DomUList) 

                for x in self.__reshape_conf['nodes']:
                    try:
                        _ebox.mAcquireRemoteLock()
                        self.mRemoveComputeVMDelete(x['dom0']['hostname'], x['domU']['hostname'], [OSTP_CREATE_VM], aOptions)
                    except Exception as e:
                        _detail_error = f"Error while deleting the VM {x['domU']['hostname']}"
                        _ebox.mUpdateErrorObject(gNodeElasticError['DEL_VM_FAILED'], _detail_error)
                        ebLogError(_detail_error)
                        ebLogError(traceback.format_exc())
                    finally:
                        _ebox.mReleaseRemoteLock()
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Add Compute undo create guest completed", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, step, "Done", _stepSpecificDetails)

            elif step == "RUN_ROOTSCRIPT" and _undo:
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Add Compute undo run rootscripts in progress", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, step, "In Progress", _stepSpecificDetails) 
                self.mExecuteOEDACLIUndoStep(_newdomUList, step)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Add Compute undo run rootscripts completed", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, step, "Done", _stepSpecificDetails)

            elif step in ["CONFIG_CLUSTERWARE", "CELL_CONNECTIVITY", "CREATE_USERS"] and _undo:
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', f"Elastic Add Compute undo {step} in progress", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, step, "In Progress", _stepSpecificDetails)
                self.mExecuteOEDACLIUndoStep(_newdomUList, step)
                
                if step == "CELL_CONNECTIVITY" and _ebox.mIsKVM() and ( isEncryptionRequested(aOptions, 'domU') or
                        exacc_fsencryption_requested(aOptions)):

                    # Clean up encrypted u02 disk if applicable
                    _newdom0UList = []
                    for _node in self.__reshape_conf['nodes']:
                        _newdom0UList.append([_node['dom0']['hostname'],
                            _node['domU']['hostname']])
                    cleanupU02EncryptedDisk(_newdom0UList)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', f"Elastic Add Compute undo {step} completed", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, step, "DONE", _stepSpecificDetails)


            elif step == "OSTP_POSTVM_INSTALL" and _do:

                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Add Compute run post VM install in progress", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, step, "In Progress", _stepSpecificDetails) 
                # Executes the steps required post VM installation.
                _ebox.mAddPostVMInstallSteps([OSTP_POSTVM_INSTALL], aOptions)

                _setPasswordless = True
                if _ebox.mIsExaScale():
                    _setPasswordless = False

                _ebox.mAddUserDomU("opc", "2000", aSudoAccess=True, aPasswordLess=_setPasswordless)

                # For Exascale, only generate id_rsa keys for opc user in the new VM.
                # DBCS Agent will configure passwordless connectivity for opc user.
                if _ebox.mIsExaScale():
                    self.mGenerateUserKeys(_newdomUList, ["opc"])

                # Migrate keys for all the users.
                _ebox.mRotateVmKeys()
                ebLogInfo("OSTP_POSTVM_INSTALL")

                # Update images to install cluster
                _ebox.mUpdateDepFiles()

                _selinux_status = _ebox.mGetSELinuxMode("domu")
                if _selinux_status:
                    try:
                        _return_code = _ebox.mProcessSELinuxUpdate(aOptions, True)
                        if _return_code == SELINUX_UPDATE_SUCCESS:
                            ebLogInfo("SE Linux mode/policy update succeeded for elastic scale compute.")
                    except ExacloudRuntimeError as ere:
                        _exception_message = "{0}".format(ere.mGetErrorMsg())
                        ebLogError("SE Linux mode/policy update failed for elastic scale compute. Error details: {0}".format(_exception_message))
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Add Compute run post VM install completed", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, step, "Done", _stepSpecificDetails)

            elif step == "OSTP_POSTINSTALL_CLUSTER" and _do:

                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Add Compute run Post Install cluster in progress", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, step, "In Progress", _stepSpecificDetails)
                # As part of mPatchVMCfg(), the VM is rebooted.
                # Thus wait for ASM to be up.
                if not _ebox.mIsXS():
                    for _newdomU in _newdomUList:
                        self.mAddCheckClusterAsm(aOptions, _newdomU, _gridhome)

                if not _ebox.mCheckConfigOption('secure_ssh_all', 'False'):
                    _step_time = time.time()
                    _ebox.mSecureDom0SSH()
                    if _ebox.mIsExaScale() and not _ebox.mIsOciEXACC():
                        addRoceNetworkHostAccessControl(aOptions)
                    _ebox.mLogStepElapsedTime(_step_time, 'Secure DOM SSH')

                _step_time = time.time()
                _remapUtil = ebMigrateUsersUtil(_ebox)
                _remapUtil.mExecuteRemap()
                _ebox.mLogStepElapsedTime(_step_time, 'Remapping Users and Groups IDs')

                ebLogInfo("OSTP_POSTINSTALL_CLUSTER")
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Add Compute Post Install cluster completed", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, step, "Done", _stepSpecificDetails)


            elif step == "OSTP_POSTGI_INSTALL" and _do:
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Add Compute Post GI Install is in progress", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, step, "In Progress", _stepSpecificDetails)
                # Executes the steps required post GI install
                _ebox.mAddPostGIInstallSteps([OSTP_POSTGI_INSTALL], aOptions)
                ebLogInfo("OSTP_POSTGI_INSTALL")
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Add Compute Post GI Install completed", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, step, "Done", _stepSpecificDetails)

            elif step == "OSTP_EXASCALE_COMPLETE" and _do:

                if _ebox.mIsXS():
                    self.mExecuteExascaleComplete(aOptions)
                else:
                    if not _ebox.mCheckConfigOption('secure_ssh_all', 'False'):
                        _step_time = time.time()
                        _ebox.mSecureDom0SSH()
                        _ebox.mLogStepElapsedTime(_step_time, 'Secure DOM SSH')

                    _step_time = time.time()
                    _remapUtil = ebMigrateUsersUtil(_ebox)
                    _remapUtil.mExecuteRemap()
                    _ebox.mLogStepElapsedTime(_step_time, 'Remapping Users and Groups IDs')

                    # Execute ExaScale Complete
                    _esc = exadbxsComplete()
                    _esc.doExecute(_ebox, aOptions, ["ESTP_EXASCALE_COMPLETE"])

                    # Setting CSWLIB_OSS_URL environment variable in domU for Exascale clusters
                    csu = csUtil()
                    csu.mSetEnvVariableInDomU(_ebox)

                ebLogInfo("OSTP_EXASCALE_COMPLETE")

            elif step == "OSTP_POSTGI_NID" and _do:
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Add Compute Post GI NID in progress", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, step, "In Progress", _stepSpecificDetails)

                # Install dbaastools rpm prior to initializing ocde (in Post GI NID step)
                for _newdomU in _newdomUList:
                    if _ebox.mIsAdbs():
                        self.mUpdateKMSRPM(_newdomU)
                    else:
                        self.mUpdateRPM(_srcdomU, _newdomU, aOptions)

                if _ebox.mIsDRNetPresent() and _ebox.mIsOciEXACC():
                    self.mSetDRVip(_newdomUList[0])

                if _ebox.mIsOciEXACC():
                    if  _ebox.mIsFedramp():
                        _ebox.mSetupDomUsForSecurePatchServerCommunication()
                        _ebox.mAddEcraNatOnDomU()
                        _ebox.mHandlerCopyCSSHubKeys()
                    # for fedramp check is placed inside class
                    _obj = ebCopyDBCSAgentpfxFile(_ebox)
                    _obj.mCopyDbcsAgentpfxFiletoDomUsForFedramp()

                # Executes the steps required post GI NID installation.
                # Post GI NID also makes sure ACFS is loaded.
                _ebox.mAddPostGINIDSteps([OSTP_POSTGI_NID], aOptions, _gridhome)

                if not _ebox.mIsAdbs():
                    # Identify if this is Multicloud env
                    _isMulticloud = False
                    _multicloudProvider = ""
                    _isMulticloud, _multicloudProvider = \
                        self.mIsMulticloud(_srcdomU)

                    with connect_to_host(_srcdomU, get_gcontext()) as _node:
                        # Dbaascli need to verify dbaas_acfs contents
                        _dbaas_acfs = '/var/opt/oracle/dbaas_acfs'
                        _, _o, _e = _node.mExecuteCmd(f'/bin/ls -lrt {_dbaas_acfs}')
                        _rc = _node.mGetCmdExitStatus()
                        if not _rc:
                            _out = _o.readlines()
                            ebLogDebug(f'{_dbaas_acfs} contents: {_out}') 

                    # If multicloud, run dbaascli in SRC node after RPMs were installed.
                    if _isMulticloud:
                        for _newdomU in _newdomUList:
                            self.mInstallMulticloudRPMs(
                                _srcdomU, _newdomU, _multicloudProvider)

                with connect_to_host(_srcdomU, get_gcontext()) as _node:
                    for _newdomU in _newdomUList:
                        ebLogInfo(f"Copying cprops_wallet file from {_srcdomU} to {_newdomU}.")
                        ebLogTrace(f"Executing: /usr/bin/sudo -u oracle /bin/scp -r /u01/app/oracle/admin/cprops/cprops_wallet oracle@{_newdomU}:/u01/app/oracle/admin/cprops")
                        _node.mExecuteCmd(f"/usr/bin/sudo -u oracle /bin/scp -r /u01/app/oracle/admin/cprops/cprops_wallet oracle@{_newdomU}:/u01/app/oracle/admin/cprops")
                
                if not _ebox.mIsAdbs():
                    mUpdateListenerPort(_ebox, _newdomUList)

                # Adding Site Group configuration file to the domU (only if working with ABDS)
                # This can only be done if this is an ADBS flow AND if this is a multicloud instance, 
                # which is already checked by ECRA before sending the payload. If any of these conditions
                # is not met, the payload will NOT contain the 'location' block, therefore we can assume 
                # that, if we can find said attribute in the payload, this is a multicloud instance:
                if _ebox.mIsAdbs():
                    mCreateADBSSiteGroupConfig(_ebox)

                # Bug 35304980 - In ExaCC we build a specific cprops.ini for each DomU,
                # so we don't copy it from the source DomU to the new DomU(s) like
                # we do for ExaCS
                if not _ebox.mIsOciEXACC():
                    with connect_to_host(_srcdomU, get_gcontext()) as _node:
                        for _newdomU in _newdomUList:
                            ebLogInfo(f"Copying cprops.ini file from {_srcdomU} to {_newdomU}.")
                            ebLogTrace(f"Executing: /usr/bin/sudo -u oracle /bin/scp /var/opt/oracle/cprops/cprops.ini oracle@{_newdomU}:/var/opt/oracle/cprops/cprops.ini")
                            _node.mExecuteCmd(f"/usr/bin/sudo -u oracle /bin/scp /var/opt/oracle/cprops/cprops.ini oracle@{_newdomU}:/var/opt/oracle/cprops/cprops.ini")

                #Install AHF on new domUs. Dom0 AHF install will be taken care while running exachk
                if not _ebox.isATP():
                    csu = csUtil()
                    csu.mInstallAhfonDomU(_ebox)

                if _ebox.IsZdlraProv():
                    for _newdomU in _newdomUList:
                        _host = _newdomU.split('.')[0]
                        with connect_to_host(_newdomU, get_gcontext()) as _node:
                            _node.mExecuteCmd(f"/usr/bin/chmod -R 775 /u01/app/grid/diag/crs/{_host}/crs/*")

                ebLogInfo("OSTP_POSTGI_NID")
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Add Compute Post GI NID completed", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, step, "Done", _stepSpecificDetails)

            elif step == "OSTP_PREDB_INSTALL" and _do:

                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Add Compute Pre DB Install in progress", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, step, "In Progress", _stepSpecificDetails)
                if not _ebox.IsZdlraProv():
                    #zdlra has a different logic for updating hugepages in postginid step!
                    #Fetch the hugepages from srcdomU & Update it on new domU
                    for _newdomU in _newdomUList:
                        self.mUpdateHugePages(_newdomU)

                _ebox.mCheckCrsIsUp(_srcdomU, _newdomUList)
                _ebox.mCheckAsmIsUp(_srcdomU, _newdomUList)

                _ebox.mCopyCreateVIP()

                # Fetch the exacli password from src domU and store it in new domU
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_srcdomU)
                _, _o, _ = _node.mExecuteCmd('/opt/exacloud/get_cs_data.py --dataonly')
                _node.mDisconnect()
                _passwd = _o.read().strip()
                for _newdomU in _newdomUList:
                    try:
                        ebExaCCSecrets([_newdomU]).mPushExacliPasswdToDomUs(_passwd)
                    except Exception as e:
                        ebLogError(f"Failure during ExaCLI password push to domU: {_newdomU}")
                        ebLogError(f"Error caused by the following exception: {e}")
                        # We will not raise any errors regarding the ExaCLI password if we're in an ExaCC environment
                        if _ebox.mIsOciEXACC() or _ebox.mIsAdbs():
                            ebLogInfo("Not stopping step flow since we're in an ExaCC environment.")
                            continue
                        # If the corresponding flag is enabled, we will raise runtime error when invalid ExaCLI pwd is passed
                        if get_gcontext().mGetConfigOptions().get("enforce_exacli_password_update"):
                            raise ExacloudRuntimeError(0x0757, 0xA, f"Exception during ExaCLI password push to domU: {_newdomU}") from e

                # ZDLRA systems do not create databases using dbaas tooling
                # Do not syncup databases for ZDLRA systems
                if not _ebox.IsZdlraProv() and not _ebox.mIsAdbs():

                    # Sync DB Homes on the new domU with the already existing 
                    # domU (_srcdomU). Installation of DB instances will be 
                    # handled in separate call from PSM.
                    self.mAddDBHomes(aOptions, _srcdomU)
                
                ebLogInfo("OSTP_PREDB_INSTALL")
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Add Compute Pre DB Install completed", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, step, "Done", _stepSpecificDetails)

            elif step == "OSTP_END_INSTALL" and _do:
                
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Add Compute End Install in progress", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, step, "In Progress", _stepSpecificDetails)
                _csu = csUtil()
                if _ebox.mIsFedramp() and _ebox.mCheckConfigOption ('whitelist_admin_network_cidr', 'True'):
                    _step_time = time.time()
                    _remote_lock = _ebox.mGetRemoteLock()
                    with _remote_lock():
                        for _new_dom0 in _newdom0List:
                            with connect_to_host(_new_dom0, get_gcontext()) as _node:
                                _csu.mWhitelistCidr(_ebox, _node)
                    _ebox.mLogStepElapsedTime(_step_time, 'Whitelist Admin Network Cidr on Added Dom0')

                self.mExecuteEndStep(_newdomUList, aOptions)

                #Update System Vault Access to the new compute
                if not _ebox.isBaseDB() and not _ebox.mIsExaScale():
                    _utils.mUpdateSystemVaultAccess(aOptions)

                ebLogInfo('*** Exacloud Operation Successful : Add Node completed')
                _ebox.mUpdateStatusOEDA(True, OSTP_END_INSTALL, [OSTP_END_INSTALL], 'Add Node Completed')

                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Add Compute Compute End Install completed", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, step, "Done", _stepSpecificDetails)

            elif step == "OSTP_BACKUP_GOLDIMG" and _do:
                
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'ONGOING', "Elastic Add Compute golden vm backup in progress", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, step, "In Progress", _stepSpecificDetails)
                ebLogInfo(f"*** Exacloud will attempt to take a golden vm backup"
                           f"of the VMs: '{_newdomUList}'")
                _golden_backuo_mgr = csGoldenBackup("OSTP_BACKUP_GOLDIMG")
                _newdom0List = [x['dom0']['hostname'] for x in self.__reshape_conf['nodes']]
                _golden_backuo_mgr.doExecute(_ebox, aOptions, ["OSTP_BACKUP_GOLDIMG"], _newdom0List)
                ebLogInfo('*** Exacloud completed the golden vmbackup step ')
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Add Compute golden vm backup completed", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, step, "Done", _stepSpecificDetails)

            elif step == "REVERT_ADBS_CONFIG" and _do:
                # the updated value of oracle_home remains to make sync with customisation
                ebLogInfo("No-OP: Nothing to be performed as part of this operation for ADBS")

                if "delete_domu_keys" in aOptions.jsonconf and aOptions.jsonconf['delete_domu_keys'].lower() == "true":
                    # Remove access to the domUs for root, grid, opc, oracle
                    _ebox.mRemoveSshKeys()

            else:
                _detail_error = "Operation with sent parameters is a No-OP" 
                _ebox.mUpdateErrorObject(gNodeElasticError['FAILED_NO_OP_PARAMS'], _detail_error)
                ebLogError(_detail_error)

    def mExecuteExascaleComplete(self, aOptions):
        _rc = 0
        _srcdom0 = self.mGetSrcDom0()
        _srcdomU = self.mGetSrcDomU()
        _newdomUList = [x['domU']['hostname'] for x in self.__reshape_conf['nodes']]
        _newdom0List = [x['dom0']['hostname'] for x in self.__reshape_conf['nodes']]
        _ebox = self.__eboxobj

        if _ebox.mIsDRNetPresent() and _ebox.mIsOciEXACC():
            self.mSetDRVip(_newdomUList[0])

        # Execute ExaScale Complete
        _esc = xsComplete()
        _esc.doExecute(_ebox, aOptions, ["ESTP_EXASCALE_COMPLETE"])

        with connect_to_host(_srcdomU, get_gcontext()) as _node:
            for _newdomU in _newdomUList:
                ebLogInfo(f"Copying cprops_wallet file from {_srcdomU} to {_newdomU}.")
                ebLogTrace(f"Executing: /usr/bin/sudo -u oracle /bin/scp -r /u01/app/oracle/admin/cprops/cprops_wallet oracle@{_newdomU}:/u01/app/oracle/admin/cprops")
                _node.mExecuteCmd(f"/usr/bin/sudo -u oracle /bin/scp -r /u01/app/oracle/admin/cprops/cprops_wallet oracle@{_newdomU}:/u01/app/oracle/admin/cprops")

        mUpdateListenerPort(_ebox, _newdomUList)

        # Bug 35304980 - In ExaCC we build a specific cprops.ini for each DomU,
        # so we don't copy it from the source DomU to the new DomU(s) like
        # we do for ExaCS
        if not _ebox.mIsOciEXACC():
            with connect_to_host(_srcdomU, get_gcontext()) as _node:
                for _newdomU in _newdomUList:
                    ebLogInfo(f"Copying cprops.ini file from {_srcdomU} to {_newdomU}.")
                    ebLogTrace(f"Executing: /usr/bin/sudo -u oracle /bin/scp /var/opt/oracle/cprops/cprops.ini oracle@{_newdomU}:/var/opt/oracle/cprops/cprops.ini")
                    _node.mExecuteCmd(f"/usr/bin/sudo -u oracle /bin/scp /var/opt/oracle/cprops/cprops.ini oracle@{_newdomU}:/var/opt/oracle/cprops/cprops.ini")

        #Install AHF on new domUs. Dom0 AHF install will be taken care while running exachk
        if not _ebox.isATP():
            csu = csUtil()
            csu.mInstallAhfonDomU(_ebox)

    def mExecuteEndStep(self, aNewDomUList, aOptions):

        _ebox = self.__eboxobj
        _newdom0List = [x['dom0']['hostname'] for x in self.__reshape_conf['nodes']]
        _newdomUList = aNewDomUList
        _srcdomU = self.mGetSrcDomU()
        _srcdom0 = self.mGetSrcDom0()

        # Now that the node addition is complete. We should 
        # copy the config xml and the keys in the clusters/<cluster name>/.
        # Here <cluster name> is constructed using the new set of 
        # dom0-domU pair. 
        # The config xml and keys will now be stored in clusters/AA'BB'CC'/
        if _ebox.mHasNatAndCustomerNet():
            _ebox.mBuildClusterId()
        else:
            _cludir = self.mBuildClusterDir(sorted(_ebox.mGetOrigDom0sDomUs()))
            _ebox.mSetKey(_cludir) 

        _ebox.mSaveXMLClusterConfiguration()

        _ebox.mSaveOEDASSHKeys(aOptions)

        for _newdomU in _newdomUList:

            # Call mSyncPSMKeys to syncup the keys in the new domU
            # which were inserted in the existing VM's (as part of starter DB)  
            if not _ebox.mIsExaScale():
                self.mSyncPSMKeys(_srcdomU, _newdomU)

        _ebox.mCopyExaDataScript() # copy the exadata_updates script to DomUs
        # Update the list of the DomUs and the cluster Config Xml path to a json file for the CPS usage
        domu_list = [ _domu for _ , _domu in _ebox.mGetOrigDom0sDomUs()]
        _ebox.mDeleteClusterFileForDomUs(list(set(domu_list) - set(_newdomUList)))
        _ebox.mSaveClusterDomUList()
        # Stores the interconnect IP's of the VM's in cluster_interconnect.dat
        if not _ebox.mIsExaScale():
            _ebox.mStoreDomUInterconnectIps()
        
        # 34267393: Update grid.ini (nodelist, sid, dbname, oracle_home) in all domUs in ZDLRA env
        if _ebox.IsZdlraProv():
            _ebox.mUpdateGridINI(domu_list)

        # Save new cluster configuration in dom0 config files
        _ebox.mSaveClusterConfiguration()

        # Configure vm backups on the new dom0s
        self.mConfigureVMBackup(aOptions,_srcdom0, _newdom0List)

        # CONFIGURE EDV VMBACKUP/LOCAL VMBACKUP
        if not _ebox.isBaseDB() and not _ebox.mIsExaScale():
            _utils = _ebox.mGetExascaleUtils()
            _utils.mConfigureEDVbackup(aOptions)

            #Update System Vault Access to the new compute
            _utils.mUpdateSystemVaultAccess(aOptions)

        # Validation
        self.mPostReshapeValidation(aOptions,None, _newdomUList)

        if not _ebox.mIsExaScale() and "delete_domu_keys" in aOptions.jsonconf and aOptions.jsonconf['delete_domu_keys'].lower() == "true":
            # Remove access to the domUs.
            _ebox.mRemoveSshKeys(['opc', 'grid', 'oracle'])


    def mConfigureVMBackup(self, aOptions, aSrcDom0, aNewDom0List):
        """
        The function configures packages in new dom0s
        to take vm backups.
        :param aOptions
        :param aSrcDom0
        :param aNewDom0List
        """

        _srcdom0 = aSrcDom0
        _newdom0List = aNewDom0List
        _ebox = self.__eboxobj

        # If VM backup is enabled in existing dom0s, 
        # install vmbackup in the new node too.
        _vmbkup = False
        with connect_to_host(_srcdom0, get_gcontext()) as _node:
            _vmbkupobj = ebCluManageVMBackup(_ebox)
            _vmbkup = _vmbkupobj.mCheckVMbackupInstalled(_node)
            if _vmbkup:
                # Make local copy of vmbackup.conf from srcdom0
                _node.mCopy2Local('/opt/oracle/vmbackup/conf/vmbackup.conf')

        if _vmbkup:
            for _newdom0 in _newdom0List:
                with connect_to_host(_newdom0, get_gcontext()) as _node:
                    # Copy vmbackup.conf to the newdom0
                    _node.mExecuteCmd('/bin/mkdir -p /opt/oracle/vmbackup/conf/')
                    _node.mCopyFile('vmbackup.conf', '/opt/oracle/vmbackup/conf/')
           
            # Remove the local copy of vmbackup.conf
            _ebox.mExecuteLocal("/bin/rm vmbackup.conf")

            # Install vmbackup on the newly added node
            _vmbkupobj.mInstallVMbackup(aOptions, aPatching=True)
            
    def mCopyResolvConf(self, aSrcDomU, aNewDomUList):
        _ebox = self.__eboxobj
        _uuid = _ebox.mGetUUID()
        _localfile = f"/tmp/{_uuid}_resolv.conf"
        _backupfilepath = "/etc/resolv_bak.conf"
        try:
            _resolv_conf_path = '/etc/resolv.conf'
            with connect_to_host(aSrcDomU, get_gcontext(), username="root") as _node:
                if _node.mFileExists(_resolv_conf_path) is True:
                    ebLogInfo(f"/etc/resolv.conf file exists on {aSrcDomU}")
                    _node.mCopy2Local(_resolv_conf_path, _localfile)
            for aNewDomU in aNewDomUList:
                with connect_to_host(aNewDomU, get_gcontext(), username="root") as _node:
                    # Copy resolv.conf to the newdomU
                    if _node.mFileExists(_resolv_conf_path) is False:
                        node_exec_cmd_check(_node, '/bin/touch /etc/resolv.conf')
                    else:
                        #take a backup before modification
                        _node.mCopyFile(_resolv_conf_path, _backupfilepath)
                    _node.mCopyFile(_localfile, _resolv_conf_path)
                    _node.mChmodFile(f'{_resolv_conf_path}', 0o644)
                    node_exec_cmd_check(_node, f'/bin/chown -f root:root {_resolv_conf_path}')
            _ebox.mExecuteLocal(f"/bin/rm -f {_localfile}")
        except Exception as e:
            _msg = f"Unable to copy /etc/resolv.conf file to the new domUs. Error:{str(e)}"
            ebLogError(_msg)
            raise ExacloudRuntimeError(aErrorMsg=_msg)

    def mCopyCellkeyOra(self, aSrcDomU, aNewDomUList):
        _ebox = self.__eboxobj
        _uuid = _ebox.mGetUUID()
        _localfile = f"/tmp/{_uuid}_domU_cellkey"
        try:
            _cellkey_ora_path = '/etc/oracle/cell/network-config/cellkey.ora'
            with connect_to_host(aSrcDomU, get_gcontext(), username="root") as _node:
                if _node.mFileExists(_cellkey_ora_path) is True:
                    ebLogInfo(f"cellkey.ora file exists on {aSrcDomU}")
                    _node.mCopy2Local(_cellkey_ora_path, _localfile)
            for aNewDomU in aNewDomUList:
                with connect_to_host(aNewDomU, get_gcontext(), username="root") as _node:
                    # Copy cellkey.ora to the newdomU
                    if _node.mFileExists(_cellkey_ora_path) is False:
                        node_exec_cmd_check(_node, '/bin/mkdir -p /etc/oracle/cell/network-config')
                    _node.mCopyFile(_localfile, _cellkey_ora_path)
                    _node.mChmodFile(f'{_cellkey_ora_path}', 0o640)
                    node_exec_cmd_check(_node, f'/bin/chown -f grid:oinstall {_cellkey_ora_path}')
            _ebox.mExecuteLocal(f"/bin/rm {_localfile}")
        except Exception as e:
            _msg = f"Unable to copy the cellkey.ora to the new domUs Error:{str(e)}"
            ebLogError(_msg)
            raise ExacloudRuntimeError(aErrorMsg=_msg)

    def mPatchPrivNames(self, aReshapeConfig:dict):
        """
        This method will attempt to modify aReshapeConfig to override
        priv1 priv2 networks.

        Example of how an original json will come:

        "hostname": "scaqak03dv0108.us.oracle.com",
        "priv1": {
            "fqdn": "iad176585exddb01vm03str-priv1.oraclecloud.internal",
            "ipaddr": "192.168.0.41"
        },
        "priv2": {
            "fqdn": "iad176585exddb01vm03str-priv2.oraclecloud.internal",
            "ipaddr": "192.168.0.42"

        With this method result should be something like:

        "hostname": "scaqak03dv0108.us.oracle.com",
        "priv1": {
            "fqdn": "scaqak03dv0108-priv1.oraclecloud.internal",
            "ipaddr": "192.168.0.41"
        },
        "priv2": {
            "fqdn": "scaqak03dv0108-priv2.oraclecloud.internal",
            "ipaddr": "192.168.0.42"
        """

        ebLogInfo("ExaCC - Modfiying priv names on nodes")
        # Iterate over config json "nodes" list
        for _nodes in aReshapeConfig.get("nodes"):

            # Get domU hostname and strip domain name
            _hostname = _nodes.get("domU", {}).get("hostname")
            _hostname = _hostname.split(".")[0]

            # Get priv domain name
            _privdomain = _nodes.get("domU", {}).get("priv1", {}).get(
                    "fqdn", "")
            _privdomain = _privdomain.split(".", 1)[1]

            # Build hostname + priv1/priv2 and domain
            _priv1_fqdn = f"{_hostname}-priv1.{_privdomain}"
            _priv2_fqdn = f"{_hostname}-priv2.{_privdomain}"
            ebLogInfo(f"priv1 fqdn computed: {_priv1_fqdn} for host {_hostname}")
            ebLogInfo(f"priv2 fqdn computed: {_priv2_fqdn} for host {_hostname}")

            # Override aReshapeConfig priv1 fqdn and priv2 fqdn
            # with the one calculated above
            _nodes["domU"]["priv1"]["fqdn"] = _priv1_fqdn
            _nodes["domU"]["priv2"]["fqdn"] = _priv2_fqdn

        ebLogTrace(f"Diag, dumping reshape_conf: {aReshapeConfig}")


    def mExecutePreVMStep(self, aOptions, aNewDomUList, aNetInfoDR={}):

        _ebox = self.__eboxobj
        _utils = _ebox.mGetExascaleUtils()
        _srcdomU = self.mGetSrcDomU()
        _srcdom0 = self.mGetSrcDom0()
        _newdomUList = aNewDomUList
        _oeda_path  = _ebox.mGetOedaPath()
        _oedacli_bin = _oeda_path + '/oedacli'
        _ociexacc  = _ebox.mIsOciEXACC()
        #TODO: store intermediate xml files returned from oedacli to some location 
        _savexmlpath = _oeda_path + '/exacloud.conf'
        self.__oedacli_mgr = OedacliCmdMgr( _oedacli_bin, _savexmlpath)

        #
        # Update OEDA properties
        #
        _step_time = time.time()
        _ebox.mUpdateOEDAProperties(aOptions)
        _ebox.mLogStepElapsedTime(_step_time, 'PREVM INSTALL : Updating OEDA environment')

        _uuid = _ebox.mGetUUID()
        _oeda_path = _ebox.mGetOedaPath()
        _addnodexml = _oeda_path + '/exacloud.conf/addnode_' + _uuid + '.xml'

        _newdom0UList = []
        for _node in self.__reshape_conf['nodes']:
            _newdom0 = _node['dom0']['hostname']
            _newdom0UList.append([_node['dom0']['hostname'], _node['domU']['hostname']])

        # If we are in exacc and with fs encryption enabled, we store
        # the passphrase in the encrypted wallet. Keys will be synced
        # to STANDBY CPS at the end of the operatoin (as with all exakms keys)
        if _ebox.mIsKVM() and _ebox.mIsOciEXACC() and exacc_fsencryption_requested(aOptions):
            _new_guest_list = [ _domU for _, _domU in _newdom0UList ]
            ebLogInfo("Storing entry for exacc encrypted guests: "
                f"{_new_guest_list}")
            exacc_save_fsencryption_passphrase(aOptions, _new_guest_list)

        # Update u02 size for new domU
        if not _ebox.mIsExaScale():
            if _ebox.mGetOHSize() is not None:
                _ebox.mSetU02Size(_ebox.mGetOHSize())
            else:
                _ebox.mSetU02Size(self.mGetNodeU02Size(_srcdom0, _srcdomU))

            _imgVersion = _ebox.mGetImageVersion(_srcdomU, aUseCache=False)
            for _new_node, _ in _newdom0UList:
                _imgInfo = self.mUpgradeSystemImage(_imgVersion, _new_node)

            # Update OEDA properties file for image version to match with image version of source domU
            _ebox.mSetImageVersionProperty(_imgVersion)

            # Patch the XML with src domU's actual timezone and DNS/NTP server info
            self.mPatchXML(_srcdomU)

        else:

            if "domu_image_version" in aOptions.jsonconf:
                _imgVersion = aOptions.jsonconf["domu_image_version"]
                ebLogTrace(f"Taking domu image version from payload: {_imgVersion}")
            else:
                _imgVersion = _ebox.mGetImageVersion(_srcdom0, aUseCache=False)
                ebLogTrace(f"Taking domu image version from srcdom0: {_imgVersion}")

            for _new_node, _ in _newdom0UList:
                _imgInfo = self.mUpgradeSystemImage(_imgVersion, _new_node)
            _ebox.mSetImageVersionProperty(_imgVersion)

        #Patch XML with storage Interconnect Ips from compute nodes
        if _ebox.mIsKVM() and not _ebox.mIsAdbs() and not _ebox.mIsExaScale():
            _existing_dom0_domu_pairs = _ebox.mGetElasticOldDom0DomUPair()
            _utils = _ebox.mGetExascaleUtils()
            _utils.mPatchStorageInterconnctIps(aOptions, aDom0DomUList=_existing_dom0_domu_pairs)

        _patchconfig = _ebox.mGetPatchConfig()
        _ebox.mExecuteLocal("/bin/cp {} {}".format(_patchconfig, _addnodexml))

        # Patch priv1 and priv2 for all new domU's for ExaCC
        if _ebox.mGetOciExacc():
            self.mPatchPrivNames(self.__reshape_conf)

        # Execute oedacli steps to patch the xml '_addnodexml' 
        # (with new Dom0-DomU) to be used in mAddPreVMInstallSteps.
        for _json in self.__reshape_conf['nodes']:

            self.__oedacli_mgr.mAddDom0(_srcdom0, _addnodexml, _addnodexml, _json, _ebox.mIsKVM(), True)
            _dns_servers, _ntp_servers = self.mGetCluUtils().mExtractNtpDnsPayload(_json['dom0'])
            if _dns_servers or _ntp_servers:
                self.__oedacli_mgr.mUpdateDnsNtpServers(_json['dom0']['hostname'],
                                                        _addnodexml, _addnodexml,
                                                        _dns_servers, _ntp_servers,
                                                        aDeploy=True)
            _net_info = None
            if 'dr' in _json['domU'] and _ociexacc:
                _net_info = aNetInfoDR.get(_json['dom0']['hostname'])

            _imgfile = None
            if _imgInfo and "imgBaseName" in _imgInfo:
                _imgfile = _imgInfo["imgBaseName"].replace(".kvm", "")

            self.__oedacli_mgr.mAddDomU(_srcdomU, _json['domU']['hostname'], _addnodexml, _addnodexml, _json, _ebox, _ebox.mIsKVM(), _imgVersion, True, _ociexacc, aNetInfo=_net_info, aImgFile=_imgfile)

            if _utils.mIsEDVImageSupported(aOptions):
                _vault_name = _utils.mGetVaultName(aOptions, aVaultType="image")
                self.__oedacli_mgr.mUpdateEDVGuestVolumes(_addnodexml, _addnodexml, "celldisk", "edv", _vault_name, "guest", _json['domU']['hostname'])

        # self.mVerifyDomUSystemImage(_imgVersion)
        _ebox.mUpdateInMemoryXmlConfig(_addnodexml, aOptions)

        if _ebox.mIsExaScale():
            mPatchPrivNetworks(_ebox)
            _ebox.mSaveXMLClusterConfiguration()
            ebLogInfo(f"patched Private Network config: {_ebox.mGetPatchConfig()}")

            _exascale = ebCluExaScale(_ebox)
            _exascale.mUpdateVolumesOedacli(aWhen="AddNode")

        #ADD 2T MEMORY SUPPORT FOR X9M
        _exadata_model = _ebox.mGetExadataDom0Model(_srcdom0)
        _exadata_model_gt_x9 = False
        if _ebox.mCompareExadataModel(_exadata_model, 'X9') >= 0:
            _exadata_model_gt_x9 = True

        _model_subType: str = ""
        _inputjson = aOptions.jsonconf
        if _inputjson:
            if 'model_subtype' in _inputjson.keys() and _inputjson['model_subtype'].strip():
                _model_subType = _inputjson['model_subtype'].strip()

        _enable_2t_support = _ebox.mCheckConfigOption('enable_2t_memory_support')
        if _ebox.mIsKVM() and not _ebox.mIsOciEXACC() and  _enable_2t_support == "True" and _exadata_model_gt_x9 and _model_subType in ["ELASTIC_LARGE", "ELASTIC_EXTRA_LARGE"]:
            _is_supported = _ebox.mCheck2TMemoryRequirements(_srcdom0, _model_subType)
            if _is_supported:
                for _dom0, _domU in _newdom0UList:
                    _is_supported = _ebox.mCheck2TMemoryRequirements(_dom0, _model_subType)
                    if not _is_supported:
                        _detail_error = f'2T Memory not supported on dom0 {_dom0}' 
                        ebLogError("*** Error: " + _detail_error)
                if _is_supported:
                    for _dom0, _ in _newdom0UList:
                        _exadata_model = _ebox.mGetNodeModel(_dom0)
                        _ebox.mAdd2TMemorySupport(aOptions, _exadata_model, _model_subType)

        # If encryption is requested, reset XML and add encryption again.
        # This will make sure that the keyapi is added to the new nodes from
        # the cluster
        # Only do this if full guest encryption is enabled
        if (isEncryptionRequested(aOptions, 'domU') and
                _ebox.mIsKVM() and get_gcontext().mGetConfigOptions().get(
                    "force_full_guest_encryption", "false").lower() == "true"):
            patchXMLForEncryption(_ebox, _addnodexml)

        # Check hostnames' length
        _pchecks = ebCluPreChecks(_ebox)
        ebLogInfo(f"Checking connectivity for: {self.__origVMs}")
        _are_existing_vms_connectable = _pchecks.mConnectivityChecks(aHostList=self.__origVMs)
        if not _are_existing_vms_connectable:
            _detail_error = "Connectivity checks to existing VMs in the cluster has failed. \
            Make sure that temporal key for all existing VMs are added and are ssh enabled prior to elastic add operation."
            _ebox.mUpdateErrorObject(gReshapeError['ERROR_VM_NOT_CONNECTABLE'], _detail_error)
            raise ExacloudRuntimeError(0x0757, 0xA, _detail_error)
        _pchecks.mHostnamesLengthChecks()

        _newdom0list = []
        for _dom0, _ in _newdom0UList:
            _newdom0list.append(_dom0)

        _pchecks.mCheckOracleLinuxVersion(_srcdomU, _newdom0list)
        if not _ebox.mIsAdbs() and not _ebox.mIsExaScale() and not _ebox.mIsXS() and not _ebox.IsZdlraProv() and _ebox.mCheckConfigOption("check_asm_passwd", "True"):
            _pchecks.mCheckASMPassword(_srcdomU)

        if _ebox.mGetOciExacc():
            # Apply DNS config on CC
            ebDNSConfig(aOptions, _addnodexml).mConfigureDNS('guest')
            ebDNSConfig(aOptions, _addnodexml).mConfigureHealthCheckMetrics("all", aCriticalError=False)

        # Executes PreVM installtion steps
        _ebox.mAddPreVMInstallSteps([OSTP_PREVM_INSTALL], aOptions)

        if _ebox.IsZdlraHThread() is False:
            _ebox.mGetZDLRA().mEnableDisableHT("Disabled", aOptions)

        if _ebox.mIsExabm() and _ebox.mIsKVM():

            _nftDom0s = _ebox.mGetHostsByTypeAndOLVersion(ExaKmsHostType.DOM0, ["OL8"])
            _iptDom0s = _ebox.mGetHostsByTypeAndOLVersion(ExaKmsHostType.DOM0, ["OL7", "OL6"])

            if _nftDom0s:
                ebIpTablesRoCE.mSetupSecurityRulesExaBM(_ebox, aOptions.jsonconf, aDom0s=_nftDom0s)

            if _iptDom0s:
                ebIpTablesRoCE.mPrevmSetupIptables(_ebox, aDom0s=_iptDom0s)

        ebLogInfo("OSTP_PREVM_INSTALL")
        
        # Global Cache Update
        _ebox.mParallelFileLoad()

        _ebox.mAcquireRemoteLock()

        # Bonded-bridge configuration might cause OEDA CREATE_VM to
        # fail, thus cleanup bonding first.  Bonding will be configured
        # later after the VMs are created.
        #
        # This operation is only required if static bonded-bridge creation is
        # not supported in the cluster.
        # In case static bonded-bridges are supported for this cluster, we'll
        # try to make sure the bridges are configured as dynamic to avoid
        # cleanup during provisioning.
        clubonding.migrate_static_bridges(_ebox, aOptions.jsonconf)
        if not clubonding.is_static_monitoring_bridge_supported(
                _ebox, payload=aOptions.jsonconf):
            clubonding.cleanup_bonding_if_enabled(
                _ebox, payload=aOptions.jsonconf, cleanup_bridge=True,
                cleanup_monitor=False)

        #
        # Update bonding configuration only if static bridges are supported.
        #
        if clubonding.is_static_monitoring_bridge_supported(
                _ebox, payload=aOptions.jsonconf): 
            clubonding.update_bonded_bridges(_ebox, payload=aOptions.jsonconf)

        _ebox.mReleaseRemoteLock()

        # Ensure Encrypted First Boot exists and Create and push luks devices passphrase
        # if encryption is requested in ECRA payload
        if isEncryptionRequested(aOptions, 'domU') and not _ebox.mIsOciEXACC():

            # Don't create and push luks passphrase if property is we're using
            # local passphrase
            if not useLocalPassphrase():
                ebLogInfo('Create and push luks devices passphrase')

                _domu_list = []
                for _node in self.__reshape_conf['nodes']:
                    _domu_list.append( _node['domU']['hostname'])
                createAndPushRemotePassphraseSetup(aOptions, _domu_list)

            # Also, if Exadata is KVM and encryption is requested. Make sure the
            # encrypted First Boot image is present, else create it with vm_maker
            # only if full guest encryption is turned on in exabox.conf
            if _ebox.mIsKVM() and get_gcontext().mGetConfigOptions().get(
                    "force_full_guest_encryption", "false").lower() == "true":
                ebLogInfo('Ensure Encrypted First Boot image exists')

                _dom0_list = []
                for _node in self.__reshape_conf['nodes']:
                    _dom0_list.append(_node['dom0']['hostname'])
                ensureSystemFirstBootEncryptedExistsParallelSetup(_ebox, _dom0_list)

            # Create Marker file for Encryption
            ebLogInfo('Create crypto luks marker file')
            for _node in self.__reshape_conf['nodes']:
                createEncryptionMarkerFileForVM(
                        _node['dom0']['hostname'], _node['domU']['hostname'])


    def mExecuteOEDACLIUndoStep(self, aNewDomUList, aStep): 
        _srcdomU = self.mGetSrcDomU()                     
        _srcdom0 = self.mGetSrcDom0()                     
        _newdomUList = aNewDomUList                       
        _step = aStep 
        _ebox = self.__eboxobj                            
        _patchconfig = _ebox.mGetPatchConfig()            
        _uuid = _ebox.mGetUUID()                          
        _oeda_path = _ebox.mGetOedaPath()                 
        aOptions = self.__options

        _delnodexml = _oeda_path + '/exacloud.conf/delnode_' + _step + '_' + _uuid + '.xml'           
        _oeda_path  = _ebox.mGetOedaPath()                
        _oedacli_bin = _oeda_path + '/oedacli'
        #TODO: store intermediate xml files returned from oedacli to some location            
        _savexmlpath = _oeda_path + '/exacloud.conf'      
        self.__oedacli_mgr = OedacliCmdMgr( _oedacli_bin, _savexmlpath)                       
        _ebox.mExecuteLocal("/bin/cp {} {}".format(_patchconfig, _delnodexml))                
                      
        # oedacli steps (below) require grid sys password for                                 
        # node addition.                                  
        if not _ebox.mIsExaScale():
            # GET GI_HOME, ORACLE_BASE
            _gihome, _giversion, _obase = _ebox.mGetOracleBaseDirectories(aDomU = _srcdomU)
            if not _giversion:
                _giversion = _ebox.mGetClusters().mGetCluster().mGetCluVersion()
            _giver = _giversion[:2]

            if _step == "RUN_ROOTSCRIPT" and _giver == "23":
                for _domU in _newdomUList:
                    with connect_to_host(_domU, get_gcontext()) as _node:
                        _host = _domU.split('.')[0]
                        _cmd_str = f"{_gihome}/bin/srvctl stop listener -n {_host}"
                        _node.mExecuteCmdLog(_cmd_str)

                ebLogInfo(f"SKIPPING UNDO RUN_ROOTSCRIPT STEP FOR {_giver} GIVERSION.")
                return

            if _ebox.IsZdlraProv():                           
                 _pswd = _ebox.mGetZDLRA().mGetWalletViewEntry('passwd', _srcdomU)
            elif _ebox.mIsAdbs():
                _pswd = _ebox.mGetWalletViewEntry('passwd', _srcdomU)
            else:         
                 _pswd = _ebox.mGetSysPassword(_srcdomU)      
            _ebox.mUpdateOedaUserPswd(_oeda_path, "non-root", _pswd)                              
                      
        _ebox.mAcquireRemoteLock()                        
                      
        _step_time = time.time()                          
        self.__oedacli_mgr.mDeleteClusterNode(_newdomUList, _delnodexml, _delnodexml, _step)
        _ebox.mLogStepElapsedTime(_step_time, 'delete guest oedacli execution')              
        _ebox.mReleaseRemoteLock()                        
                      
        if _step == "CREATE_GUEST":
            # cleanup bondmonitor
            clubonding.cleanup_bonding_if_enabled(
                _ebox, payload=aOptions.jsonconf, cleanup_bridge=False,
                cleanup_monitor=True)
        _ebox.mSaveXMLClusterConfiguration()              
        ebLogInfo(_step)                                  

    def mExecuteOEDACLIDoStep(self, aNewDomUList, aStep, aOptions=None):

        _srcdomU = self.mGetSrcDomU()
        _srcdom0 = self.mGetSrcDom0()
        _newdomUList = aNewDomUList
        _step = aStep
        _ebox = self.__eboxobj
        

        #FOR EXACC-HETERO ENV PATCH THE XML WITH CLIENT/BACKUP SLAVES & ENABLE SKIPPASSPROPERTY FLAG
        _ebox.mOEDASkipPassProperty(aOptions)

        _uuid = _ebox.mGetUUID()
        aOptions = self.__options
        _oeda_path = _ebox.mGetOedaPath()
        _oedacli_bin = _oeda_path + '/oedacli'
        #TODO: store intermediate xml files returned from oedacli to some location 
        _savexmlpath = _oeda_path + '/exacloud.conf'
        self.__oedacli_mgr = OedacliCmdMgr( _oedacli_bin, _savexmlpath)

        # GET GI_HOME, ORACLE_BASE
        _gihome, _giversion, _obase = _ebox.mGetOracleBaseDirectories(aDomU = _srcdomU)
        if not _gihome:
            _gihome = _ebox.mGetClusters().mGetCluster().mGetCluHome()
        if not _giversion:
            _giversion = _ebox.mGetClusters().mGetCluster().mGetCluVersion()
        _giver = _giversion[:2]
        _obaseahf = False
        if not _ebox.mIsExaScale():

            # Update OEDA properties file for image version to match with image version of source domU 
            _imgVersion = _ebox.mGetImageVersion(_srcdomU, aUseCache=False)
            _ebox.mSetImageVersionProperty(_imgVersion)

            # connect to source domU
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_srcdomU)
            _gihomeahf = _node.mFileExists(_gihome + '/oracle.ahf')
            _obaseahf = _node.mFileExists(_obase + '/oracle.ahf.gihome')
            _node.mDisconnect()

            # before addNode, oracle.ahf is present under gi_home
            if _gihomeahf is True:
                # pre addNode: move ahf to obase
                self.mMoveAhfDataDir(_srcdomU, True)

        # oedacli steps (below) require grid sys password for 
        # node addition.
        if not _ebox.mIsExaScale():
            if _ebox.IsZdlraProv():
                _pswd = _ebox.mGetZDLRA().mGetWalletViewEntry('passwd', _srcdomU)
            elif _ebox.mIsAdbs():
                _pswd = _ebox.mGetWalletViewEntry('passwd', _srcdomU)
            else:
                _pswd = _ebox.mGetSysPassword(_srcdomU)
            _ebox.mUpdateOedaUserPswd(_oeda_path, "non-root", _pswd)

        if not _ebox.mIsExaScale():

            # Update u02 size for new domU            
            if _ebox.mGetOHSize() is not None:        
                _ebox.mSetU02Size(_ebox.mGetOHSize()) 
            else: 
                _ebox.mSetU02Size(self.mGetNodeU02Size(_srcdom0, _srcdomU))                    

        _newdom0UList = []
        _newdom0List = []
        for _node in self.__reshape_conf['nodes']:
            _newdom0 = _node['dom0']['hostname']
            _newdom0List.append(_node['dom0']['hostname'])
            _newdom0UList.append([_node['dom0']['hostname'], _node['domU']['hostname']])

        _ebox.mAcquireRemoteLock()

        _step_time = time.time()     
        
        if _step == "CONFIG_CLUSTERWARE":
            self.mCopyResolvConf(_srcdomU,_newdomUList)
            
            
        if _step in ["CREATE_USERS", "CELL_CONNECTIVITY", "CONFIG_CLUSTERWARE"]:
            self.mCallBack(_step)

        if _step in ["CREATE_GUEST"]:

            #Cleanup Stale serial console connection & directory if exists
            self.mRemoveConsoleSSH(aOptions)

            #Clear if any stale bridge exist, before VM Creation,applicable only for kvm
            _csu = csUtil()
            _ebox.mAcquireRemoteLock()
            try:
                _csu.mDeleteStaleDummyBridge(_ebox)
            except Exception as e:
                raise e
            finally:
                _ebox.mReleaseRemoteLock()

            #copy /opt/exacloud/config_info.json to dom0
            _ebox.mConfigureVMConsole(aOptions, _newdom0UList)

            _utils = _ebox.mGetExascaleUtils()
            if _utils.mIsEDVImageSupported(aOptions):
                _utils.mPatchEDVVolumes(aOptions)

        try:
            _patchconfig = _ebox.mGetPatchConfig()
            _addnodexml = _oeda_path + '/exacloud.conf/' + _step + '_' + _uuid + '.xml'
            _ebox.mExecuteLocal("/bin/cp {} {}".format(_patchconfig, _addnodexml))

            _utils = _ebox.mGetExascaleUtils()
            if _utils.mIsEDVImageSupported(aOptions):
                _vault_name = _utils.mGetVaultName(aOptions, aVaultType="image")
                for _domU in _newdomUList:
                    self.__oedacli_mgr.mUpdateEDVGuestVolumes(_addnodexml, _addnodexml, "celldisk", "edv", _vault_name, "guest", _domU)

            if _step == "RUN_ROOTSCRIPT" and _ebox.mIsAdbs():
                # Patch the xml temporarily with DATA as that is what is in the ASM DB, and then after the oeda step, patch is again to the original value
                _srcdomU = self.mGetSrcDomU()
                _newdiskgroupNames = getDiskGroupNames(_srcdomU)
                _diskGroupIds = _ebox.mGetClusters().mGetCluster().mGetCluDiskGroups()
                _olddiskgroupNames = []
                for _dgid in _diskGroupIds:
                    _dgName = _ebox.mGetStorage().mGetDiskGroupConfig(_dgid).mGetDgName()
                    _olddiskgroupNames.append(_dgName)
                _id_diskgroup_mapping = dict(zip(_diskGroupIds, _newdiskgroupNames))

                for _diskGroupId,_newdiskgroupName in _id_diskgroup_mapping.items():
                    ebLogInfo(f"The diskGroup id={_diskGroupId} and updated to new diskGroupName={_newdiskgroupName}")
                    self.__oedacli_mgr.mUpdateDiskGroupName(_newdiskgroupName, _diskGroupId, _addnodexml, _addnodexml)

                ebLogInfo('ebCluCtrl: Saved patched Cluster Config: ' + _addnodexml)

            #Bug 36531177 - NEED TO START THE LISTENER DURING PROVISION
            self.__oedacli_mgr.mBuildMultipleGuests(_newdomUList, _addnodexml, _addnodexml, _step)
        except Exception as e:
            _detail_error = 'OEDACLI: clone guest failed' 
            ebLogError(_detail_error)
            _ebox.mUpdateErrorObject(gNodeElasticError['ADD_NODE_FAILED'], _detail_error)
            # move ahf back to gihome
            if _obaseahf is True:
                self.mMoveAhfDataDir(_srcdomU, False, True, True)

            raise ExacloudRuntimeError(0x0738, 0xA, "Oedacli: Clone Guest failed") from e

        _ebox.mLogStepElapsedTime(_step_time, 'clone guest oedacli execution')                           

        if _step == "CREATE_GUEST":

            # Below we create the permanent xtable/security rules in the Dom0s (KVM)
            # for the VM's for client/backup interfaces. We try to create these
            # rules as soon as the VM is created, to avoid cases where the wide
            # open tmp rules get deleted by a parallel operation in the same
            # cluster, causing connectivity issues.
            # As of the time of writing this, only OL7 requires the creation of
            # this tmp rules and NOT OL8, that's why the below logic is gated
            # to NOT run on OL8.
            if _ebox.mIsExabm() and _ebox.mIsKVM():
                _iptDom0s = _ebox.mGetHostsByTypeAndOLVersion(ExaKmsHostType.DOM0, ["OL7", "OL6"])
                if _iptDom0s:
                    ebIpTablesRoCE.mSetupSecurityRulesExaBM(_ebox, aOptions.jsonconf, aDom0s=_iptDom0s)

            #INSTALL SERIAL CONSOLE BITS IN NEW DOM0
            _vmc_dpy = VMConsoleDeploy(_ebox, aOptions)
            _vmc_dpy.mInstall(_newdom0List)

            #Start Containers exa-hippo-serialmux|exa-hippo-sshd for serial Console
            _consoleobj = serialConsole(_ebox, aOptions)
            def _restartContainers(_dom0, _domU):
                _consoleobj.mRunContainer(_dom0, _domU)
                _consoleobj.mRestartContainer(_dom0, _domU, aMode="start")

                
            _plist = ProcessManager()
            for _dom0, _domU in _newdom0UList:
                _p = ProcessStructure(_restartContainers, [_dom0, _domU,])
                _p.mSetMaxExecutionTime(30*60) #30 minutes timeout
                _p.mSetJoinTimeout(5)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)

            _plist.mJoinProcess()

            _isHetero, _ = _ebox.IsHeteroConfig()
            _ociexacc = _ebox.mIsOciEXACC()
            if _isHetero and _ociexacc:
                ebLogInfo("HETERO ENVIRONMENT DETECTED...")
                ebLogInfo("CONFIGURING DEFAULT GATEWAY TO BONDETH0 ...")
                for _dom0, _domU in _ebox.mReturnDom0DomUPair():
                    _ebox.mConfigureDefaultGateway(_dom0, _domU, aOptions)

            # Configure bonding.
            # 
            # Configure bridge only if static monitoring bridge is not supported.
            conf_bridge = \
                not clubonding.is_static_monitoring_bridge_supported(
                    _ebox, payload=aOptions.jsonconf)
            clubonding.configure_bonding_if_enabled(
                _ebox, payload=aOptions.jsonconf,
                configure_bridge=conf_bridge, configure_monitor=True)
            _ebox.mSetupArpCheckFlag()

            ## Bug 38693893
            # Set up Cloud marker file in the new guests
            # GI installers use this to not test for some unnecesary
            # network paths (ICMP...)
            if _ebox.mIsKVM():
                _ebox.mUpdateVmetrics('vmexacs_kvm')
                _ebox.mStartVMExacsService(
                    aOptions, aDom0DomUPair=_newdom0UList, aCheckCrsAsm=False)

        if _step == "RUN_ROOTSCRIPT":
            # post addNode: move ahf back to gihome
            # before addNode and oracle.ahf is present under gi_home
            if _obaseahf is True:
                self.mMoveAhfDataDir(_srcdomU, False, True, True)

            if not _ebox.mCheckConfigOption("_skip_jumbo_frames_config", "True"):
                clujumboframes.configureJumboFrames(_ebox, aOptions.jsonconf)
            _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticAddDetails", 'DONE', "Elastic Add Compute run rootscripts completed", _step)
            self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, _step, "Done", _stepSpecificDetails)

        if _step == "CREATE_USERS":
            # We need to generate ssh keys for oracle and grid users on new DOMUs
            # for exascale
            if _ebox.mIsExaScale():
                self.mGenerateUserKeys(_newdomUList, ["oracle", "grid"])

        if _step == "RUN_ROOTSCRIPT" and _ebox.mIsAdbs():
            # Patch the xml again with original diskgroupname
            _diskGroupIds = _ebox.mGetClusters().mGetCluster().mGetCluDiskGroups()
            _id_diskgroup_mapping = dict(zip(_diskGroupIds, _olddiskgroupNames))

            for _diskGroupId,_olddiskgroupName in _id_diskgroup_mapping.items():
                ebLogInfo(f"The diskGroup id={_diskGroupId} and again updated to old diskGroupName={_olddiskgroupName}")
                self.__oedacli_mgr.mUpdateDiskGroupName(_olddiskgroupName, _diskGroupId, _addnodexml, _addnodexml)

            ebLogInfo('ebCluCtrl: Saved patched Cluster Config: ' + _addnodexml)

        _ebox.mReleaseRemoteLock()

        _ebox.mSaveOEDASSHKeys()
        _ebox.mSaveXMLClusterConfiguration()
        ebLogInfo(_step)

    def mGenerateUserKeys(self, aNewDomUList, aUserList):
        _domUs = aNewDomUList
        _userlist = aUserList
        _keyType = "rsa"
        _exakms = get_gcontext().mGetExaKms()
        if _exakms.mGetDefaultKeyAlgorithm() == "ECDSA":
            _keyType = "ecdsa"
        for aUser in _userlist:
            _home_dir = f'/home/{aUser}'
            for _domU in _domUs:
                #Creating ssh key on actual domu
                ebLogInfo(f'Creating ssh key for user: {aUser} on {_domU}')

                try:
                    with connect_to_host(_domU, get_gcontext()) as _node:
                        node_exec_cmd_check(_node, f'/bin/su - {aUser} -c "/bin/mkdir -p {_home_dir}/.ssh"')
                        node_exec_cmd_check(_node, f'/bin/su - {aUser} -c "/bin/chown `id -u {aUser}`:`id -g {aUser}` {_home_dir}/.ssh"')
                        node_exec_cmd_check(_node, f'/bin/su - {aUser} -c "/bin/chmod 700 {_home_dir}/.ssh"')

                        if not _node.mFileExists(f'{_home_dir}/.ssh/id_{_keyType}') and not _node.mFileExists(f'{_home_dir}/.ssh/id_{_keyType}.pub'):

                            if _keyType == "ecdsa":
                                _cmd = f'/bin/su - {aUser} -c "/bin/ssh-keygen -t ecdsa -b 384 -q -C \'USER_KEY\' -N \'\' -f {_home_dir}/.ssh/id_{_keyType}"'
                                node_exec_cmd_check(_node, _cmd)
                            else:
                                _cmd = f'/bin/su - {aUser} -c "/bin/ssh-keygen -q -C \'USER_KEY\' -N \'\' -f {_home_dir}/.ssh/id_{_keyType}"'
                                node_exec_cmd_check(_node, _cmd)

                        _cmd = f'/bin/su - {aUser} -c "/bin/chmod 600 {_home_dir}/.ssh/id_{_keyType}*"'
                        node_exec_cmd_check(_node, _cmd)
                        _cmd = f'/bin/su - {aUser} -c "/bin/chown `id -u {aUser}`:`id -g {aUser}` {_home_dir}/.ssh/id_{_keyType}*"'
                        node_exec_cmd_check(_node, _cmd)
                except Exception as exp:
                    _msg = f'::mGenerateUserKeys failed for user {aUser} on {_domU}: {exp}.'
                    ebLogError(_msg)
                    raise ExacloudRuntimeError(aErrorMsg=_msg) from exp

    def mGetNodeU02Size(self, aDom0, aDomU):
        _ebox = self.__eboxobj
        _utils = _ebox.mGetExascaleUtils()
        aOptions = self.__options
        with connect_to_host(aDom0, get_gcontext()) as _node:
            if _utils.mIsEDVImageSupported(aOptions):
                _disk_image = get_dom0_edvdisk_for_filesystem(_node, aDomU, ebDomUFilesystem.U02)
            else:
                _disk_image = get_dom0_disk_for_filesystem(_node, aDomU, ebDomUFilesystem.U02)
            return f"{_disk_image.size_bytes // GIB}G"

    def mBuildClusterDir(self, aDom0DomUPair=None):

        _ebox = self.__eboxobj
        _ddp = []

        if aDom0DomUPair:
            _ddp = aDom0DomUPair

        # Only do compressed ClusterID on KVM+OCI for now as ExaCC-OCI uses for
        # X8M the full clusterID in the keys.db
        if _ebox.mIsKVM() and _ebox.mIsExabm():
            #FirstDomULastDomU
            _dir = _ddp[0][1].split('.')[0] + _ddp[-1][1].split('.')[0]
        else:
            _dir  = ''
            _dir2 = ''
            for _dom0, _domU in _ddp:
                _dir = _dir + _dom0.split('.')[0] + _domU.split('.')[0]
                _dir2 = _dir2 + _domU.split('.')[0]
            if len(_dir) >= 255:
                # Fix for cluster id greater than 255 characters (e.g. SABRE)
                _dir  = _dir2[:255]

        return _dir

    # 
    # The function checks if asm is running on
    # the new node.
    #
    def mAddCheckClusterAsm(self, aOptions, aDomU, aGridHome):

        _domu = aDomU
        _ebox = self.__eboxobj
        _vmnode = exaBoxNode(get_gcontext())
        _grid_home = aGridHome
        _vmnode.mSetUser('grid')
        _vmnode.mConnect(_domu)
        _cmd = "export ORACLE_HOME={0}; {0}/bin/lsnrctl services | grep -m1 -oP '\+ASM\d'"
        _i, _o, _e = _vmnode.mExecuteCmd(_cmd.format(_grid_home))
        _count = 0
        while (_vmnode.mGetCmdExitStatus() and _count < 20):
            time.sleep(30)
            _count = _count + 1
            ebLogWarn(f"*** Waiting for listener to report ASM in {_domu} post patching vm configuration")
            _i, _o, _e = _vmnode.mExecuteCmd(_cmd.format(_grid_home))

        if _vmnode.mGetCmdExitStatus():
            _detail_error = f"Listener service for ASM in {_domu} are not running." 
            _ebox.mUpdateErrorObject(gNodeElasticError['FAILED_NO_OP_PARAMS'], _detail_error)
            ebLogError(_detail_error)
            ebLogError("*** Error: " + _detail_error)

        _vmnode.mDisconnect()

    def mAddDBHomes(self, aOptions, aSrcDomU):
        """
        The function attempts to sync DB Homes on the new domU with the already
        existing domU (_srcdomU). 
        :param aOptions
        :param aSrcDomU
        """
        _statusdata = {}
        _new_domushortnames = ""
        _data = {}
        _syncdblist = dict()
        for _entry in self.__reshape_conf['nodes']:
            _srcdomU = aSrcDomU
            _newdomU = _entry['domU']['hostname']
            _newdomU_shrtnm = _newdomU.split('.')[0]
            _new_domushortnames += f"{_newdomU_shrtnm},"
            _ebox = self.__eboxobj
            _db_info = _entry['domU']['db_info']

            ebLogInfo(f"List of databases requested by ECRA to be synced: {_db_info}")
            
            # Clean up /u02/opt/dbaas_images/* from newdomU
            ebLogInfo("Cleaning up /u02/opt/dbaas_images/dbnid before copying images in the VM: %s" % _newdomU)
            _username = "oracle"
            with connect_to_host(_newdomU, get_gcontext(), username=_username) as _node:
                _node.mExecuteCmdLog("/bin/rm -rf /u02/opt/dbaas_images/dbnid/*")

            # Update nodelist in grid.ini of all nodes (existing and new nodes) to contain
            # the correct set of nodes.
            _nodelist = " ".join([_domU.split('.')[0] for _, _domU in _ebox.mGetOrigDom0sDomUs()])

            _username = "root"
            for _, _domU in _ebox.mGetOrigDom0sDomUs():
                try:
                    with connect_to_host(_domU, get_gcontext(), username=_username) as _node:
                        _node.mExecuteCmdLog(f"/var/opt/oracle/ocde/rops set_creg_key grid nodelist '{_nodelist}'")
                except Exception as e:
                    ebLogError(f"Failed to set grid nodelist with error: {e}")
                    
                    
            try:
                with connect_to_host(_srcdomU, get_gcontext(), username=_username) as _node:
                    _out = node_exec_cmd(_node, f"/usr/bin/sudo -u oracle /bin/scp -r /u02/opt/dbaas_images oracle@{_newdomU}:/u02/opt/")
                    ebLogTrace(_out)
            except Exception as e:
                ebLogError(f'Error while copying /u02/opt/dbaas_images from {_srcdomU} to {_newdomU : }{e}')


            if _db_info:  # not None/empty
                _syncdblist[_newdomU] = _db_info.split(',')
            else:
                _syncdblist[_newdomU] = []
            _data[_newdomU] = { _db: "Fail" for _db in _syncdblist[_newdomU] }

        
        _dbhomes = getDatabaseHomes(_srcdomU)
        ebLogTrace(f'DBHomes list from {_srcdomU} : {_dbhomes}')
        if not _dbhomes: # empty output
            ebLogError('Could not retrieve Dbhomes for {_db_info}, skipping database sync')
            return

        if _new_domushortnames[-1] == ",":
            _new_domushortnames = _new_domushortnames[:-1]

        ebLogTrace(f"Attempting to clone db home for following VM(s): {_new_domushortnames}")
        
        try:
            for _dbhome in _dbhomes:
                _version = _dbhomes[_dbhome]["version"]
                _dbhome_path = _dbhomes[_dbhome]["homePath"]
                cloneDbHome(_srcdomU, _version, _dbhome_path, _new_domushortnames)
        except Exception as e:
            ebLogError(f'Error in cloning db home, skipping database sync : {str(e)}')
            return

        # Identify if this is Multicloud env
        _isMulticloud, _multicloudProvider = self.mIsMulticloud(_srcdomU)
        if _isMulticloud and _multicloudProvider == "AZURE":
            _msg = ( "IMPORTANT: In Multicloud Environment DB HOME is extended."
                f" But DB extension is skipped for {_multicloudProvider} ")
            ebLogInfo(_msg)
            return

        # addInstance is called below
        # Which adds a database instance to a new node.
        _databases = getDatabases(_srcdomU)
        ebLogTrace(f'List of Databases from {_srcdomU}: {_databases}')

        for _entry in self.__reshape_conf['nodes']:

            _newdomU = _entry['domU']['hostname']
            _newdomU_shrtnm = _newdomU.split('.')[0]
            _domainname = _newdomU.split('.',1)[1]

            for _dbname in _databases:
                _instance_added = False
                _data[_newdomU][_dbname] = "Fail"
                if not _ebox.mIsOciEXACC():
                    if not _syncdblist.get(_newdomU, None) or _dbname not in _syncdblist.get(_newdomU):
                        continue

                _username = "root"
                with connect_to_host(_srcdomU, get_gcontext(), username=_username) as _node:
                    _node.mExecuteCmdLog(f"/var/opt/oracle/ocde/rops add_creg {_dbname} {_newdomU_shrtnm}")

                if not _databases[_dbname].get('dbNodeLevelDetails', {}):
                    ebLogError(f'dbNodeLevelDetails value empty in {_databases[_dbname]}, skipping add instance for {_dbname}, please add manually.')
                    continue

                for _node in _databases[_dbname]['dbNodeLevelDetails']:
                    # add instance will work only on nodes instance is running
                    _node_status = None
                    _db_role = None
                    if _databases[_dbname]['dbNodeLevelDetails'].get(_node, {}):
                        _node_status = _databases[_dbname]['dbNodeLevelDetails'][_node].get('status')
                        _db_role = _databases[_dbname]['dbRole']
                    if _db_role in ["PRIMARY"] and _node_status in ["OPEN", "READ_ONLY"]\
                        or _db_role in ["PHYSICAL_STANDBY"] and _node_status in ["MOUNTED", "READ_ONLY"]:
                        _nodefqdn  = _node + "." + _domainname
                        ebLogTrace(f'Db {_dbname} is running on node {_nodefqdn} with DbRole:{_db_role} and Status:{_node_status}')
                        
                        addInstance(_nodefqdn, _dbname, _newdomU_shrtnm)
                        _instance_added = True
                        break # only one running node is required

                if not _instance_added:
                    continue

                _database_details = getDatabaseDetails(_srcdomU, _dbname)
                ebLogTrace(f'Details of db status {_database_details}')

                if 'dbNodeLevelDetails' in _database_details.keys() and not _database_details['dbNodeLevelDetails']:
                    ebLogError(f'dbNodeLevelDetails value empty for {_dbname}, skipping add instance for {_dbname}, please add manually.')
                    continue

                for _node in _database_details.get("dbNodeLevelDetails", {}):
                    if _node == _newdomU_shrtnm:
                        _node_status = None
                        if _database_details['dbNodeLevelDetails'].get(_node, {}):
                            _node_status = _database_details['dbNodeLevelDetails'][_node].get('status')
                        if _node_status in ["OPEN", "MOUNTED", "READ_ONLY"] and _data[_newdomU][_dbname] == 'Fail':
                            ebLogTrace(f'{_dbname} instance is added on node {_node}')
                            _data[_newdomU][_dbname] = "Pass"
                        else:
                            try:
                                _db_unique = _database_details["dbUniqueName"]
                                _location = _database_details["dbNodeLevelDetails"][_node]["homePath"]
                                _recoveryObj = NodeRecovery(_ebox, aOptions)
                                _rc = _recoveryObj.mStartDBInstanceIfOffline(_srcdomU, _newdomU, _dbname, _db_unique, _location)
                                if _rc == 0:
                                    _data[_newdomU][_dbname] = "Pass"
                            except Exception as e:
                                ebLogError(f"Failed to start the database {_dbname} with error: {e}")
                    if _data[_newdomU][_dbname] == "Pass":
                        _sid = ""
                        with connect_to_host(_srcdomU, get_gcontext(), username="root") as _node:
                            _node.mExecuteCmdLog(f"/usr/bin/sudo -u oracle /bin/scp -p /home/oracle/{_dbname}.env oracle@{_newdomU}:/home/oracle/")

                        _sid = self.mGetSid(_dbname, _newdomU)
                        self.mUpdateDBEnv(_dbname, _sid, _newdomU)

            ebLogInfo("Status of databases on the new node {}: {}".format(_newdomU, _data))
            _statusdata[_newdomU] = _data[_newdomU]

        self.mUpdateRequestData(aOptions, _statusdata)

    def mGetSid(self, aDBName, aDomU):
        _dbname = aDBName
        _domU = aDomU
        _sid = ""
        with connect_to_host(_domU, get_gcontext(), username="root") as _node:
            _cmd = f"/bin/cat /var/opt/oracle/creg/{_dbname}.ini | /bin/grep \"^sid\" "
            _, _o, _ = _node.mExecuteCmd(_cmd)
            _out = _o.readlines()
            if _out and len(_out):
                _sid = _out[0].split('=')[1].strip()
        return _sid

    def mUpdateDBEnv(self, aDBName, aSid, aDomU):
        _dbname = aDBName
        _sid = aSid
        _domU = aDomU
        _env_file = f"/home/oracle/{_dbname}.env"
        with connect_to_host(_domU, get_gcontext(), username="root") as _node:
            _cmd = "/bin/sed -i 's/^ORACLE_SID=.*;/ORACLE_SID={0};/g' {1}".format(_sid, _env_file)
            _node.mExecuteCmdLog(_cmd)

            _cmd = "/bin/sed -i 's/^ORACLE_HOSTNAME=.*;/ORACLE_HOSTNAME={0};/g' {1}".format(_domU, _env_file)
            _node.mExecuteCmdLog(_cmd)
            
    def mSyncDbaastoolRpmMultiCloud(self, aSrcDomU, aNewDomU, aRpm):
        _srcdomU = aSrcDomU
        _newdomU = aNewDomU
        _rpmpath = "/u02/opt/dbaas_images/"
        _rpm_to_sync = _rpmpath + aRpm  # Use a different variable name for clarity
        ebLogTrace(f'RPM default path on source node {aSrcDomU} is {_rpm_to_sync}')

        try:
            with connect_to_host(_srcdomU, get_gcontext()) as _src_node:
                # Fetch client fqdn hostname
                _, _o, _e = _src_node.mExecuteCmd("/bin/hostname --fqdn")
                if _src_node.mGetCmdExitStatus() != 0:
                    ebLogError(f"Error: Could not get hostname from source '{_srcdomU}'.")
                    return False
                _src_hostname = _o.readlines()[0].strip().split('.')[0]
                ebLogTrace(f'source node shortname for rsync {_src_hostname}')

                # --- Smart Sync Logic: Find the exact installed version ---
                # Fetch rpm release version from installed package
                _rpm_name = aRpm.split('.')[0]
                _, _o, _e = _src_node.mExecuteCmd(f'/bin/rpm -qi {_rpm_name} | grep Release')
                if _src_node.mGetCmdExitStatus() == 0:
                    _out = _o.readlines()
                    ebLogTrace(f'RPM details : {_out}')
                    _release = _out[0].split(':')[1].strip()
                    ebLogInfo(f"Info: Found installed release '{_release}' on source. Searching for matching RPM file.")

                    # Search for the rpm file with that specific release
                    _, _o, _e = _src_node.mExecuteCmd(f'/bin/ls {_rpmpath}{_rpm_name}*.rpm')
                    _rpm_files = _o.readlines()
                    if _rpm_files:
                        ebLogTrace(f'RPM files matching : {_rpm_files}')
                        for _entry in _rpm_files:
                            _rpmentry = _entry.strip()
                            _, _o, _e = _src_node.mExecuteCmd(f'/bin/rpm -qpi {_rpmentry} | grep Release')
                            _rel = _o.readlines()[0].split(':')[1].strip()
                            ebLogTrace(f'RPM release version: {_rel}')
                            if _rel == _release:
                                _rpm_to_sync = _rpmentry # Found it! Update the path.
                                ebLogInfo(f"Info: Found matching RPM file: {_rpm_to_sync}")
                                break
                else:
                    ebLogError(f"Could not determine installed RPM version on {_srcdomU},falling back to default path: {_rpm_to_sync}")


            # --- connect to the new VM to perform the sync and install ---
            with connect_to_host(_newdomU, get_gcontext()) as _new_node:
                # 1. RSYNC THE FILE
                ebLogInfo(f"Syncing {_rpm_to_sync} from {_src_hostname} to {_newdomU}...")
                _, _o, _e = _new_node.mExecuteCmd(f'sudo -u oracle rsync oracle@{_src_hostname}:{_rpm_to_sync} {_rpmpath}')
                if _new_node.mGetCmdExitStatus() != 0:
                    ebLogError(f"Error: rsync failed! Could not copy {_rpm_to_sync} from source.")
                    return False

                # 2. INSTALL THE RPM
                ebLogInfo(f"Info: Installing RPM {_rpm_to_sync} on {_newdomU}...")
                final_rpm_path = f"{_rpmpath}{_rpm_to_sync.split('/')[-1]}" # Use the filename part for install
                _, _o, _e = _new_node.mExecuteCmd(f'/bin/rpm --force -Uhv {final_rpm_path}')

                if _new_node.mGetCmdExitStatus() == 0:
                    ebLogInfo("Success: RPM sync and installation complete.")
                    return True
                else:
                    ebLogError(f"Error: RPM installation failed on {_newdomU}.")
                    return False

        except Exception as e:
            ebLogError(f"An unexpected error occurred: {e}")
            return False

    # Dump the JSON object
    def mUpdateRequestData(self, aOptions, aDataD):
        _ebox = self.__eboxobj
        _data_d = aDataD
        _reqobj = _ebox.mGetRequestObj()
        if _reqobj is not None:
            _reqobj.mSetData(json.dumps(_data_d, sort_keys = True))
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_reqobj)
        elif aOptions.jsonmode:
            ebLogJson(json.dumps(_data_d, indent = 4, sort_keys = True))

    def mUpdateKMSRPM(self, aNewDomU):
        _newdomU = aNewDomU
        _ebox = self.__eboxobj
        _rpmpath = "/u02/opt/dbaas_images/"
        _kmsrpms = ["kmstdecli.rpm", "libkmstdepkcs11.rpm"]

        # Install KMS RPMS
        with connect_to_host(_newdomU, get_gcontext()) as _node:
            for _rpm in _kmsrpms:
                _kmsrpm = _rpmpath + _rpm
                if _node.mFileExists(_kmsrpm) is False:
                    # TRY copying from images repo
                    _localfile = 'images/' + _rpm
                    if os.path.isfile(_localfile):
                        ebLogInfo('*** Copy %s to %s on %s' %(_localfile, _kmsrpm, _newdomU))
                        _node.mCopyFile(_localfile, _kmsrpm)
                        _cmd_str = 'chown -fR oracle.oinstall %s' %_kmsrpm
                        _node.mExecuteCmd(_cmd_str)
                if _node.mFileExists(_kmsrpm) is True:
                    _, _o, _e = _node.mExecuteCmd(f'/bin/rpm --force -Uhv {_kmsrpm}')
                    _rc = _node.mGetCmdExitStatus()
                    if not _rc:
                        ebLogInfo(f'Installed rpm: {_kmsrpm} on node: {_newdomU}') 
                    else:
                        _out = _o.readlines()
                        ebLogError(f'Failed to install rpm: {_kmsrpm} on node: {_newdomU} ') 
                        if _out:
                            ebLogInfo(f'OUT: {_out}')

    def mUpdateRPM(self, aSrcDomU, aNewDomU, aOptions=None):
        _srcdomU = aSrcDomU
        _newdomU = aNewDomU
        _ebox = self.__eboxobj
        _rpmpath = "/u02/opt/dbaas_images/"
        _dbaastools_rpm_default = "dbaastools_exa_main.rpm"
        _dbaastools_rpm_multicloud_sync = False 
        
        _csu = csUtil()
        _dbaastools_rpm_multicloud = _csu.mGetDbaastoolRpmName(aOptions, aLocalPath=None)
        ebLogTrace(f'DBAAS tools rpm selected : {_dbaastools_rpm_multicloud}')
        if _dbaastools_rpm_multicloud != _dbaastools_rpm_default:
            # if payload has a differnt rpm name than default
            ebLogTrace(f'DBAAS tools RPM selected from payload , sync the RPM from source node')
            _dbaastools_rpm_multicloud_sync = self.mSyncDbaastoolRpmMultiCloud(aSrcDomU, aNewDomU, _dbaastools_rpm_multicloud)
            ebLogTrace(f'{_dbaastools_rpm_multicloud} installation status {_dbaastools_rpm_multicloud_sync}')
        
        
        _rpm = _rpmpath + _dbaastools_rpm_default
        _kmsrpms = ["kmstdecli.rpm","libkmstdepkcs11.rpm"]

        _multicloudProvider = ""
        _isMulticloud = False

        _rc = 0
        _found = False

        # dbaastools rpm name from payload not found in source domU        
        if not _dbaastools_rpm_multicloud_sync:
            with connect_to_host(_srcdomU, get_gcontext()) as _node:
                # Fetch client fqdn hostname
                _, _o, _e = _node.mExecuteCmd("/bin/hostname --fqdn")
                _out = _o.readlines()
                _src_hostname = _out[0].strip().split('.')[0]

                # Fetch rpm release version
                _, _o, _e = _node.mExecuteCmd(f'/bin/rpm -qi dbaastools_exa | grep Release')
                _rc = _node.mGetCmdExitStatus()
                _out = _o.readlines()

                if not _rc and _out:
                    _release = _out[0].split(':')[1].strip()

                    # Search for the rpm with a specific release
                    _, _o, _e = _node.mExecuteCmd(f'/bin/ls {_rpmpath}dbaastools_exa*.rpm')
                    _out = _o.readlines()
                    if _out:
                        for _entry in _out:
                            _rpmentry = _entry.strip()
                            _, _o, _e = _node.mExecuteCmd(f'/bin/rpm -qpi {_rpmentry} | grep Release')
                            _out = _o.readlines()
                            _rel = _out[0].split(':')[1].strip()
                            if _rel == _release:
                                _found = True
                                _rpm = _rpmentry
                                break

            if _found:
                with connect_to_host(_newdomU, get_gcontext()) as _node:
                    _, _o, _e = _node.mExecuteCmd(f'sudo -u oracle rsync oracle@{_src_hostname}:{_rpm} {_rpmpath}')
                    _, _o, _e = _node.mExecuteCmd(f'/bin/rpm --force -Uhv {_rpm}')
                    _rc = _node.mGetCmdExitStatus()
                
            if _rc or not _out or not _found:
                # If failed to find dbaastools rpm in src domU or
                # failed to copy and install dbaastools rpm from src domU,
                # fetch the rpm from exacloud images and install it.
                _dbaastools_rpm = _csu.mGetDbaastoolRpmName(aOptions)
                # _dbaastools_rpm variable above will return the multicloud dbaastools name 
                # if that exist in images folder else it returns the default name
                # hence its safe to depend on mGetDbaastoolRpmName
                _ebox.mUpdateRpm(_dbaastools_rpm)

        # Identify if this is Multicloud env
        _isMulticloud, _ = self.mIsMulticloud(_srcdomU)

        # If MultiCloud, kmstdecli and libkmstdepkcs are not needed            
        if _isMulticloud:   
            ebLogInfo(f'Multicloud found. Skipping OCI KMS in: {_newdomU}')
            return

        # Install KMS RPMs
        with connect_to_host(_newdomU, get_gcontext()) as _node:
                            
            for _rpm in _kmsrpms:
                _rpmToInstall = _rpmpath + _rpm
                
                ebLogInfo(f'Search for RPMs in Target/New: {_newdomU}')
                # Verify if RPM's exist in New Node, if not, then will copy.
                if _node.mFileExists(_rpmToInstall) is False:
                    _msg=f'{_rpmToInstall} not found, try to do scp from src.'
                    ebLogInfo(_msg)
                    # Try to copy from source node
                    with connect_to_host(_srcdomU, get_gcontext()) as _srcnode:
                        if _srcnode.mFileExists(_rpmToInstall):
                            cmd = '/usr/bin/su - oracle -c ' \
                                f'"/bin/scp {_rpmToInstall} ' \
                                f'oracle@{_newdomU}:{_rpmToInstall}"'
                            node_exec_cmd(_srcnode, cmd, 
                                log_warning=True, log_stdout_on_error=True)
                            
                if _node.mFileExists(_rpmToInstall) is False:
                    _msg=f'{_rpmToInstall} still not found. So cp from /images'
                    ebLogInfo(_msg)
                    # TRY copying from images repo
                    _localfile = 'images/' + _rpm
                    if os.path.isfile(_localfile):
                        ebLogInfo('*** Copy %s to %s on %s' %(_localfile, 
                            _rpmToInstall, _newdomU))
                        _node.mCopyFile(_localfile, _rpmToInstall)
                        _cmd_str = 'chown -fR oracle.oinstall %s' %_rpmToInstall
                        _node.mExecuteCmd(_cmd_str)

                # Once RPM's exist in New Node, install it.
                if _node.mFileExists(_rpmToInstall) is True:
                    _, _o, _e = _node.mExecuteCmd(f'/bin/rpm --force -Uhv {_rpmToInstall}')
                    _rc = _node.mGetCmdExitStatus()
                    if not _rc:
                        ebLogInfo(f'Installed rpm: {_rpmToInstall} on node: {_newdomU}') 
                    else:
                        _out = _o.readlines()
                        ebLogError(f'Failed to install rpm: {_rpmToInstall} on node: {_newdomU} ') 
                        if _out:
                            ebLogInfo(f'OUT: {_out}') 
            
    def mIsMulticloud(self, aSrcDomU) -> (bool,str):
        """ 
        Connect to Source DomU and verify if
        1) dbmulticloud or 
        2) pkcs
        RPMs are installed in it.
        Depending on the rpm name installed, provider can be detected
        """

        _srcDomU = aSrcDomU

        _multicloudRpmPath = "/u02/app_acfs/"
        # pkcs-multicloud-driver will have suffix -maz -gcp -aws 
        # for MsAzure, GoogleCloud and AWS respectively
        _dbmulticloudRpm = "dbmulticloud-dataplane-integ"
        _pkcsMulticloudRpm = "pkcs-multicloud-driver"
        _multicloudDetails = {"installed": False, "found": False}
        _multicloudRpms = {
            _dbmulticloudRpm: _multicloudDetails,
            _pkcsMulticloudRpm: _multicloudDetails,
        }
        _multicloudProvider:str = ""
        _isMulticloud:bool = False

        def _getMulticloudProvider( aOutReadlines ) -> str:
            provider = ""
            _outputLines = aOutReadlines
            for _entry in _outputLines:
                if 'pkcs' in _entry:
                    # Check for -maz -gcp -aws 
                    if '-maz' in _entry:
                        provider = 'AZURE'
                    elif '-gcp' in _entry:
                        provider = 'GOOGLE'
                    elif '-aws' in _entry:
                        provider = 'AWS'
            return provider

        with connect_to_host(_srcDomU, get_gcontext()) as _node:
            # Search for the multicloud rpm
            ebLogInfo(f'Search for multicloud RPMs in src: {_srcDomU}')
            for multicloudRpm, mcDetails in _multicloudRpms.items():
                # Check if multicloud rpm are installed in src
                ebLogInfo(f'Check if RPM: {multicloudRpm} is installed.')
                cmd = f'/bin/rpm -qa | grep {multicloudRpm}'
                _, _o, _e = _node.mExecuteCmd(cmd)
                _rc = _node.mGetCmdExitStatus()
                if not _rc and _o:
                    _rpm_installed = _o.readlines()
                    if len(_rpm_installed):
                        mcDetails["installed"] = True
                        _isMulticloud = True
                        # Determine provider from installed RPM
                        _multicloudProvider = \
                            _getMulticloudProvider(_rpm_installed)
                        ebLogInfo(f'Multicloud provider: {_multicloudProvider}')

                ebLogInfo(f'Check if RPM: {multicloudRpm} file exists.')
                cmd = f'/bin/ls {_multicloudRpmPath}{multicloudRpm}*.rpm'
                _, _o, _e = _node.mExecuteCmd(cmd)
                _outMc = _o.readlines()
                if _outMc:
                    ebLogInfo(f'Multicloud File Found: {_outMc}') 
                    for _entry in _outMc:
                        if multicloudRpm in _entry:
                            mcDetails["found"] = True

                # If RPM was NOT found installed, then provider can be 
                # determined from the listed RPM files
                if not _multicloudProvider:
                    _multicloudProvider = _getMulticloudProvider(_outMc)
                    ebLogInfo(f'Multicloud provider: {_multicloudProvider}') 

                ebLogInfo(f'Status of Multicloud RPMS: {_multicloudRpms}')
        return _isMulticloud, _multicloudProvider

    def mInstallMulticloudRPMs(self, aSrcDomU, aNewDomU, aMulticloudProvider):
        """ 
        Exacloud will NOT install RPM's directly, actually exacloud should
        call 'dbascli admin' command to perform this task
        """
        _srcDomU = aSrcDomU
        _newDomU = aNewDomU
        _multicloudProvider = aMulticloudProvider

        ebLogInfo('In Multicloud environment, dbaascli admin installs RPMs')
        with connect_to_host(_srcDomU, get_gcontext()) as _node:                
            # Run updateMCKMS (this command includes CLOUD PROVIDER)
            _dbaascliCmd = "dbaascli admin updateMCKMS " \
                f"--nodelist {_newDomU} " \
                f"--keystoreProvider {_multicloudProvider} " \
                "--extendNodes"
            _, _o, _e = _node.mExecuteCmd(_dbaascliCmd)
            _rc = _node.mGetCmdExitStatus()
            _out = _o.readlines()
            ebLogInfo(f"Multicloud - dbaascli updateMCKMS. RC:{_rc} {_out}") 

            # Run updateMCDP
            _dbaascliCmd = "dbaascli admin updateMCDP " \
                f"--nodelist {_newDomU} " \
                "--extendNodes"
            _, _o, _e = _node.mExecuteCmd(_dbaascliCmd)
            _rc = _node.mGetCmdExitStatus()
            _out = _o.readlines()
            ebLogInfo(f"Multicloud - dbaascli updateMCDP. RC:{_rc} {_out}")         
        
    def mSyncPSMKeys(self, aSrcDomU, aNewDomU):

        _srcdomU = aSrcDomU
        _newdomU = aNewDomU

        # As part of starter DB creation on existing cluster (VMs), ssh public
        # keys gets pushed in authorized_keys for oracle, opc, root.
        # Thus, we need to push in that key to the new node. Thereby, allowing
        # PSM to connect to new node for additional DB install.

        # Now, inorder to push in that key, we have decided to syncup the 
        # authorized_keys for oracle, opc, root (in new VM) with existing VM. 
        for _userpath in ['/home/opc', '/home/oracle', '/root', '/home/grid']:

            _keyspath = _userpath + "/.ssh/authorized_keys"
            ebLogInfo(f'keypath : {_keyspath}')
            with connect_to_host(_srcdomU, get_gcontext()) as _node:
                # get keys from source domU
                _i, _o, _e = _node.mExecuteCmd("/bin/cat " + _keyspath)
                _src_keys = _o.readlines() if _o else []
                if not _src_keys:
                    ebLogInfo(f'Source key is empty, no sync required') 
                    return
            with connect_to_host(_newdomU, get_gcontext()) as _node:
                # get the keys from dest domU
                _i, _o, _e = _node.mExecuteCmd("/bin/cat " + _keyspath)
                _dest_keys = _o.readlines() if _o else []
                ebLogInfo(f'Reading {aNewDomU} keys')                                                                                                                                                                                                            
                for _src_key in _src_keys:
                    _add_key = True
                    _src_key_list = _src_key.split()
                    if len(_src_key_list)  < 2:
                        continue
                    for _dest_key in _dest_keys: # check all dest keys against source key
                        _dest_key_list = _dest_key.split()
                        if len(_dest_key_list) >= 2 and _dest_key_list[0] == _src_key_list[0] and _dest_key_list[1] == _src_key_list[1]:
                            _add_key = False
                            break
                    if _add_key:
                        _dest_keys.append(_src_key)
                #write keys to a local file
                _ebox = self.__eboxobj
                _uuid = _ebox.mGetUUID()
                _localfile = f"/tmp/{_uuid}new_domU_synced_keys"
                with open(_localfile, "w") as fd:
                    for key in _dest_keys:
                        if len(key) >2:
                            fd.write(key + '\n')
                #take backup and copy the new keys file
                try:
                    _node.mExecuteCmd("/bin/cp " + _keyspath + " " + _keyspath + ".bkup")
                    _node.mCopyFile(_localfile, _keyspath)
                    if _node.mGetCmdExitStatus() !=0:
                        raise Exception("Key copy failed: mCopyFile")
                except Exception as e:
                    _node.mExecuteCmd("/bin/cp " + _keyspath + ".bkup" + " " + _keyspath)
                    _detail_error = f'Failed to copy keys to node: {_newdomU}  due to {e}'
                    _ebox.mUpdateErrorObject(gNodeElasticError['ERROR_KEYS_COPY'], _detail_error)
                    raise ExacloudRuntimeError(0x0810, 0xA, _detail_error)
                finally:
                    os.remove(_localfile)

    def mDeleteNode(self, aOptions=None):

        _ebox = self.__eboxobj

        _reshape_dom0_list = [x['dom0']['hostname'] for x in self.__reshape_conf['nodes']]
        _reshape_domu_list = [x['domU']['hostname'] for x in self.__reshape_conf['nodes']]
        _reshape_dom0domU_list = []
        global EXCEPTION_IN_CRS
        for x in self.__reshape_conf['nodes']:
            _reshape_dom0domU_list.append([x['dom0']['hostname'], x['domU']['hostname']])

        _OrigDom0DomUList = _ebox.mGetOrigDom0sDomUs()
        for _dom0, _domU in _reshape_dom0domU_list:
            _OrigDom0DomUList.remove([_dom0, _domU])
        _ebox.mSetOrigDom0sDomUs(_OrigDom0DomUList)
        ebLogInfo(f"After removing node to be deleted, _OrigDom0DomUList: {_ebox.mGetOrigDom0sDomUs()}") 

        self.mUpdateDom0DomUPair(None)
        _ebox.mSetSharedEnv(None)
        _ebox.mCheckSharedEnvironment()

        #
        # RESHAPE CLUSTER WITH DELETE NON-PARTICIPANT Subset Node
        #
        _step_list = ["OSTP_PREDB_DELETE", "OSTP_CREATE_DB", "OSTP_POSTDB_DELETE", "OSTP_PREGI_DELETE", "OSTP_INSTALL_CLUSTER", "OSTP_POSTGI_DELETE", "OSTP_PREVM_DELETE", "OSTP_CREATE_VM", "OSTP_POSTVM_DELETE", "OSTP_END_INSTALL"]

        if aOptions.steplist:
            _step_list = str(aOptions.steplist).split(",")                                                                                      
        if 'undo' not in aOptions:
            _undo = False
        elif aOptions.undo == "True" or aOptions.undo == "true":
            _undo = True
        else:
            _undo = False

        _do = not _undo

        #
        # Update OEDA properties
        #
        _step_time = time.time()
        _ebox.mUpdateOEDAProperties(aOptions)
        _ebox.mLogStepElapsedTime(_step_time, 'PREVM VM/GI INSTALL : Updating OEDA environment')
    
        _uuid = _ebox.mGetUUID()
        _oeda_path = _ebox.mGetOedaPath()
        _deletenodexml = _oeda_path + '/exacloud.conf/deletenode_' + _uuid + '.xml'
        
        _patchconfig = _ebox.mGetPatchConfig()
        _ebox.mExecuteLocal("/bin/cp {} {}".format(_patchconfig, _deletenodexml))

        #
        # GI_DELETE
        #
        for step in _step_list:

            try:
                ebLogInfo("*** Running delete node step: %s" % step)
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'ONGOING', f"Elastic Delete Compute {step} in progress", step)
                self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, step, "In Progress", _stepSpecificDetails)

                if step == "OSTP_PREDB_DELETE":
                    #Verify ASM is up
                    _ebox.mCheckCrsIsUp(_reshape_domu_list[0], _reshape_domu_list)
                    _ebox.mCheckAsmIsUp(_reshape_domu_list[0], _reshape_domu_list)

                    self.mRemoveComputeDBDelete("OSTP_PREDB_DELETE", _reshape_domu_list, ["OSTP_PREDB_DELETE"], aOptions)
                elif step == "OSTP_CREATE_DB":
                    self.mRemoveComputeDBDelete("OSTP_CREATE_DB", _reshape_domu_list, ["OSTP_CREATE_DB"], aOptions)
                elif step == "OSTP_POSTDB_DELETE":
                    self.mRemoveComputeDBDelete("OSTP_POSTDB_DELETE", _reshape_domu_list, ["OSTP_POSTDB_DELETE"], aOptions)
                elif step == "OSTP_PREGI_DELETE":
                    self.mRemoveComputeGIDelete("OSTP_PREGI_DELETE", ["OSTP_PREGI_DELETE"], aOptions)
                elif step == "OSTP_INSTALL_CLUSTER":
                    self.mRemoveComputeInstallCluster(_reshape_domu_list, ["OSTP_INSTALL_CLUSTER"], aOptions)
                elif step == "OSTP_POSTGI_DELETE":
                    self.mRemoveComputeGIDelete("OSTP_POSTGI_DELETE", ["OSTP_POSTGI_DELETE"], aOptions)
                #
                # VM DELETE
                #
                elif step == "OSTP_PREVM_DELETE":
                    self.mRemoveComputePreVMDelete([step], aOptions)
                elif step == "OSTP_CREATE_VM":
                    _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'ONGOING', f"Elastic Delete Compute {step} in progress", step)
                    self.mGetCluUtils().mUpdateTaskProgressStatus([], 0, step, "In Progress", _stepSpecificDetails)
                    progress_percentage_step_size = 100.0/len(_reshape_dom0domU_list)
                    _percentage_increase = 0.0
                    for _reshape_dom0, _reshape_domu in _reshape_dom0domU_list:
                        try:
                            EXCEPTION_IN_CRS = False
                            _ebox.mAcquireRemoteLock()
                            _percentage_increase = _percentage_increase + progress_percentage_step_size
                            self.mRemoveComputeVMDelete(_reshape_dom0, _reshape_domu, _step_list, aOptions)
                            _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'ONGOING', f"Elastic Delete Compute {step} in progress", step)
                            self.mGetCluUtils().mUpdateTaskProgressStatus([_reshape_domu], _percentage_increase, step, "In Progress", _stepSpecificDetails)
                        except Exception as e:
                            _detail_error = f"Error while deleting the VM {_reshape_domu} : {str(e)}"           
                            _ebox.mUpdateErrorObject(gNodeElasticError['DEL_VM_FAILED'], _detail_error)
                            ebLogError(_detail_error)
                            ebLogError(traceback.format_exc())
                            if EXCEPTION_IN_CRS:
                                raise ExacloudRuntimeError(aErrorMsg=_detail_error) from e 
                        finally:
                            _ebox.mReleaseRemoteLock()

                    clubonding.cleanup_bonding_if_enabled(
                        _ebox, payload=aOptions.jsonconf, cleanup_bridge=False,
                        cleanup_monitor=True)
                    
                elif step == "OSTP_POSTVM_DELETE":
                    self.mRemoveComputePostVMDelete(["OSTP_POSTVM_DELETE"], aOptions)
                #
                # Update Final status
                #
                elif step == "OSTP_END_INSTALL":
                    self.mExecDelNodeEndStep(aOptions)
                    self.mRemoveConsoleSSH(aOptions)

            except Exception as e:
                _err_str = f"Exception in handling request: {str(e)}"
                ebLogError(traceback.format_exc())
                ebLogError(f"*** Error in running step: {step}. Detailed Error: {_err_str}" )
                if EXCEPTION_IN_CRS:
                    EXCEPTION_IN_CRS = False
                    raise ExacloudRuntimeError(aErrorMsg=_err_str) from e

            if step == "OSTP_END_INSTALL":
                # Patch the cluster xml
                _ebox.mSetPatchConfig(_deletenodexml)
                _ebox.mPatchXMLForNodeSubset(aOptions)
                _ebox.mSaveXMLClusterConfiguration()

                _patchconfig = _ebox.mGetPatchConfig()
                ebLogInfo('ebCluCtrl: Saved patched Cluster Config: ' + _patchconfig)
                _db = ebGetDefaultDB()
                _db.import_file(_patchconfig)

                self.mPostReshapeValidation(aOptions,None)
                _ebox.mUpdateStatusOEDA(True, OSTP_END_INSTALL, [OSTP_END_INSTALL], 'Delete Node Completed')
                ebLogInfo('*** Exacloud Operation Successful : Delete Node completed')
            _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'DONE', f"Elastic Delete Compute step {step} completed", step)
            self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, step, "DONE", _stepSpecificDetails)
                

    def mExecDelNodeEndStep(self, aOptions):

        _ebox = self.__eboxobj
        _reshape_dom0_list = [x['dom0']['hostname'] for x in self.__reshape_conf['nodes']]
        _reshape_domu_list = [x['domU']['hostname'] for x in self.__reshape_conf['nodes']]

        if not _ebox.mIsExaScale():
            for _reshape_domu in _reshape_domu_list:
                self.mRemoveNodeFromCRS(_reshape_domu)

        for _reshape_dom0 in _reshape_dom0_list:
            _ebox.mDeleteVnumaMarker(_reshape_dom0)

        # Remove DNS Entries corresponding to the deleted node.
        if _ebox.mIsOciEXACC():
            _dnsconfig = ebDNSConfig(aOptions, _ebox.mGetPatchConfig())
            for _domU in _reshape_domu_list:
                _dnsconfig.mRemoveHostEntries(_domU)
            _ebox.mRestartDnsmasq()

        # Update the list of the DomUs and the cluster Config Xml path to a json file for the CPS usage
        domu_list = [ _domu for _ , _domu in _ebox.mGetOrigDom0sDomUs()]
        _ebox.mDeleteClusterFileForDomUs(list(set(domu_list) | set(_reshape_domu_list))) 
        _ebox.mSaveClusterDomUList()
        # Stores the interconnect IP's of the VM's in cluster_interconnect.dat
        _ebox.mStoreDomUInterconnectIps()

        # 34267393: Update grid.ini (nodelist, sid, dbname, oracle_home) in all domUs in ZDLRA env
        if _ebox.IsZdlraProv():
            _ebox.mUpdateGridINI(domu_list)

        # Save new cluster configuration in dom0 config files
        _ebox.mSaveClusterConfiguration()

        # Delete remote luks devices passphrase and keyapi shell wrapper from the dom0s
        if isEncryptionRequested(aOptions, 'domU') and not _ebox.mIsOciEXACC():

            # Delete the Remote passphrase from SiV only if local passphrase is not
            # enabled. This is regardless of KVM or XEN
            if not useLocalPassphrase():
                ebLogInfo('Delete remote luks devices passphrase')
                _domu_list = []
                for _node in self.__reshape_conf['nodes']:
                    _domu_list.append( _node['domU']['hostname'])
                deleteRemotePassphraseSetup(aOptions, _domu_list)

            # On KVM we use OEDA to handle Filesystem Encryption. To accomplish
            # this Exacloud copies one shell wrapper to the Dom0s during the Create
            # service. This file is used by OEDA on Step2 to create the VMs.
            # This is to make sure we delete the keyapi corresponding to this cluster
            if _ebox.mIsKVM():
                ebLogInfo('Delete keyapi from Dom0s')
                _dom0_list = []
                for _node in self.__reshape_conf['nodes']:
                    _dom0_list.append(_node['dom0']['hostname'])
                deleteOEDAKeyApiFromDom0(_ebox, _dom0_list)

            # Delete Marker file for Encryption
            ebLogInfo('Delete crypto luks marker file')
            for _node in self.__reshape_conf['nodes']:
                deleteEncryptionMarkerFileForVM(
                        _node['dom0']['hostname'], _node['domU']['hostname'])

            if _ebox.mIsKVM() and _ebox.mIsOciEXACC():
                # If base nodes have encryption enabled, try to remove
                # the encrypted passphrase for deleted nodes
                if luksCharchannelExistsInDom0(self.mGetSrcDom0(), self.mGetSrcDomU()):
                    ebLogInfo(f"Encryption detected in base nodes, attempting to delete passphrase from CPS")
                    for  _domU in _reshape_domu_list:
                        exacc_del_fsencryption_passphrase(_domU)


    def mRemoveConsoleSSH(self, aOptions):
        _ebox = self.__eboxobj

        _consoleobj = serialConsole(_ebox, aOptions)
        for x in self.__reshape_conf['nodes']:
            _dom0 = x['dom0']['hostname']
            _domU = x['domU']['hostname']

            _consoleobj.mRemoveSSH(_dom0, _domU)

    def mRemoveComputeDBDelete(self, aStep, aDomUList, aStepList, aOptions):
        _ebox = self.__eboxobj
        _step_list = aStepList
        _oeda_path  = _ebox.mGetOedaPath()
        _reshape_domu_list = aDomUList
        _found = False
        _percentage_increase = 0.0

        if self.__node_recovery:
            ebLogInfo('Node Recovery: Skipping removal of DB instances...')
            return

        if aStep == "OSTP_PREDB_DELETE":

            if _ebox.mIsKVM():
                _prefix = "/usr/sbin/vm_maker --list"
            else:
                _prefix = "xm list "

            # precheck
            _node = exaBoxNode(get_gcontext())
            _percentageStepSize= 99.0/len(self.__reshape_conf['nodes'])
            _lastNode = []
            for x in self.__reshape_conf['nodes']:
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'ONGOING', f"Elastic Delete Compute {aStep} in progress", aStep)
                self.mGetCluUtils().mUpdateTaskProgressStatus(_lastNode, _percentage_increase, aStep, "In Progress", _stepSpecificDetails)
                _percentage_increase = _percentage_increase +_percentageStepSize
                _dom0 = x['dom0']['hostname']
                _domu = x['domU']['hostname']
                _lastNode.append(_domu)
                _node.mConnect(_dom0)
                _i, _o, _e = _node.mExecuteCmd(_prefix + " | grep " + _domu)
                if _node.mGetCmdExitStatus() == 0:
                    _found = True
                else:
                    _detail_error = f"Domu {_domu} not found wrt removed_computes node in json payload" 
                    _ebox.mUpdateErrorObject(gNodeElasticError['COMPUTE_NODE_MISSING_FRM_PAYLOAD'], _detail_error)
                    ebLogError(_detail_error)
                _node.mDisconnect()
                

            if not _found:
                ebLogWarn(f"None of the DOMUs available to delete, VM is unavailable.")
            #
            # Run External Scripts
            #
            _step_time = time.time()
            _ebox.mUpdateStatusOEDA(True, OSTP_PREDB_DELETE, [OSTP_PREDB_DELETE], 'Running External PREDB Scripts')
            #TBD: whether this step required or not
            #self.mRunScript(aType='*',aWhen='pre.db_delete')
            _ebox.mLogStepElapsedTime(_step_time, 'PREDB DELETE : Running External Scripts')
            _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'DONE', f"Elastic Delete Compute step {aStep} completed", aStep)
            self.mGetCluUtils().mUpdateTaskProgressStatus(_lastNode, 100, aStep, "DONE", _stepSpecificDetails)
        elif aStep == "OSTP_CREATE_DB":
            #
            # Remove DB using dbaascli
            #
            _srcDomU = self.mGetSrcDomU()
            _db_list = self.mGetDbList(_srcDomU)
            _percentageStepSize= 99.0/len(self.__reshape_conf['nodes'])
            _lastNode = []
            for _reshape_domu in _reshape_domu_list:
                _percentage_increase = _percentage_increase +_percentageStepSize
                _step_time = time.time()
                _ebox.mUpdateStatusOEDA(True, OSTP_CREATE_DB, [OSTP_CREATE_DB], 'Running dbaas API to remove DB instances')
                _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'ONGOING', f"Elastic Delete Compute {aStep} in progress", aStep)
                self.mGetCluUtils().mUpdateTaskProgressStatus(_lastNode, _percentage_increase, aStep, "In Progress", _stepSpecificDetails)
                _lastNode.append(_reshape_domu)
                if not _db_list:
                    _options = get_gcontext().mGetConfigOptions()
                    _pswd = _options["oeda_pwd"]
                    _ebox.mUpdateOedaDefaultDBPwd(_oeda_path, _pswd)
                else:
                    if _ebox.mIsAdbs():
                        _pswd = _ebox.mGetAsmSysPasswordForAdbs('asmsys', _srcDomU)
                    else:
                        _pswd = _ebox.mGetSysPassword(_srcDomU)
                    _ebox.mUpdateOedaDefaultDBPwd(_oeda_path, _pswd)
                    self.mUpdateDbInstance(_reshape_domu, _db_list)
                    self.mRemoveDBInstancesFromVMDbaascli(_reshape_domu, aOptions)
                    _ebox.mLogStepElapsedTime(_step_time, 'DB instances removed')
            _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'DONE', f"Elastic Delete Compute step {aStep} completed", aStep)
            self.mGetCluUtils().mUpdateTaskProgressStatus(_lastNode, 100, aStep, "DONE", _stepSpecificDetails)
        elif aStep == "OSTP_POSTDB_DELETE":
            _step_time = time.time()
            _ebox.mUpdateStatusOEDA(True, OSTP_POSTDB_DELETE, [OSTP_POSTDB_DELETE], 'Running External POSTDB Scripts')
            _ebox.mRunScript(aType='*',aWhen='post.db_delete')
            _ebox.mRollbackEncryption(aOptions.jsonconf)
            _ebox.mLogStepElapsedTime(_step_time, 'POSTDB DELETE: Running External Scripts')
            _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'DONE', f"Elastic Delete Compute step {aStep} completed", aStep)
            self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, aStep, "DONE", _stepSpecificDetails)

    def mRemoveNodeFromCRS(self, aNodeToDelete):

        _ebox = self.__eboxobj  
        _vip = "" 
        if _ebox.mIsExabm() or _ebox.mIsOciEXACC():
             _eBoxNetworks = _ebox.mGetNetworks()
             _domu_networks = _ebox.mGetMachines().mGetMachineConfig(aNodeToDelete).mGetMacNetworks()
             _id = [_net_id for _net_id in _domu_networks if _net_id.split('_')[-1] == "client"]
             _net_conf = _eBoxNetworks.mGetNetworkConfig(_id[0])
             _deletenode = _net_conf.mGetNetNatHostName()
        else:
             _deletenode = aNodeToDelete.split('.')[0]

        _srcdomU = self.mGetSrcDomU()
        with connect_to_host(_srcdomU, get_gcontext()) as _node:
            _path, _, _ = _ebox.mGetOracleBaseDirectories(_srcdomU)

            _delnode = aNodeToDelete.split('.')[0]
            ebLogInfo(f"Removing stale entries of VM {_delnode} in the node {_srcdomU}")                   

            _node.mExecuteCmdLog(f'{_path}/bin/crsctl unpin css -n {_delnode}')
            _node.mExecuteCmdLog(f'{_path}/bin/crsctl stop cluster -n {_delnode}')
            _node.mExecuteCmdLog(f'{_path}/bin/crsctl delete node -n {_delnode}')

            _i, _o, _e = _node.mExecuteCmd(f'{_path}/bin/srvctl config vip -n {_delnode} | grep "VIP IPv4 Address"')
            if _node.mGetCmdExitStatus() == 0:
                _out = _o.readlines()
                for _vip_out in _out:
                    _vip = _vip_out.split(":")[1].strip()
                    ebLogInfo(f'Cleanup stale entries of {_delnode}/{_vip} from clusterware')
                    _node.mExecuteCmdLog(f'{_path}/bin/srvctl stop vip -vip {_vip} -force') 
                    _node.mExecuteCmdLog(f'{_path}/bin/srvctl remove vip -vip {_vip} -force')

            _i, _o, _e = _node.mExecuteCmd(f'{_path}/bin/srvctl config vip -n {_delnode} | grep "VIP IPv6 Address"')
            if _node.mGetCmdExitStatus() == 0:
                _out = _o.readlines()
                for _vip_out in _out:
                    """
                    From https://confluence.oraclecorp.com/confluence/x/Oq308QE
                    [root@diagvmcl21-nxgt61 ~]# /u01/app/19.0.0.0/grid/bin/srvctl config vip -n diagvmcl21-nxgt62 | grep "VIP IPv6 Address"
                    VIP IPv6 Address: 2607:9b80:9a00:f521:b269:ebfd:53bb:83bc (inactive)
                    """
                    try:
                        _vip_list = _vip_out.split(" ")
                        if len(_vip_list) > 3:
                            _vip = _vip_out.split(" ")[3].strip()
                            ebLogInfo(f'Cleanup stale entries of {_delnode}/{_vip} from clusterware')
                            _node.mExecuteCmdLog(f'{_path}/bin/srvctl stop vip -vip {_vip} -force') 
                            _node.mExecuteCmdLog(f'{_path}/bin/srvctl remove vip -vip {_vip} -force')
                    except Exception as ex:
                        ebLogError(f"Could not remove entry for IPv6 vip {_delnode}/{_vip} from clusterware. Error: {ex}.")

            _node.mExecuteCmdLog(f'{_path}/bin/olsnodes -s -t | grep {_delnode}')

            if _node.mGetCmdExitStatus() == 0:  
                _node.mExecuteCmdLog(f'{_path}/bin/crsctl delete node -n {_delnode} -purge')
                _node.mExecuteCmdLog(f'{_path}/bin/olsnodes -s -t | grep {_delnode}')   
                if _node.mGetCmdExitStatus() == 0:  
                    _detail_error = f'Failed to cleanup stale entries of VM {_delnode} from clusterware' 
                    _ebox.mUpdateErrorObject(gNodeElasticError['STALE_ENTRY_EXIST'], _detail_error)
                    ebLogError(_detail_error)
                    raise ExacloudRuntimeError(0x0801, 0xA, _detail_error)

        for _, _domU in _ebox.mGetOrigDom0sDomUs():
            with connect_to_host(_domU, get_gcontext()) as _node:
                _node.mExecuteCmdLog(f'{_path}/bin/olsnodes -s -t | grep {_delnode}')
                if _node.mGetCmdExitStatus() == 0:
                    _node.mExecuteCmdLog(f'{_path}/bin/crsctl delete node -n {_delnode} -purge')
                    _node.mExecuteCmdLog(f'{_path}/bin/olsnodes -s -t | grep {_delnode}') 

                    if _node.mGetCmdExitStatus() == 0:
                        _detail_error = f'Failed to cleanup stale entry of VM {_delnode} in the node {_domU}' 
                        _ebox.mUpdateErrorObject(gNodeElasticError['STALE_ENTRY_EXIST'], _detail_error)
                        ebLogError(_detail_error)
                        raise ExacloudRuntimeError(0x0801, 0xA, _detail_error)

                # Remove the deleted node from /etc/hosts in existing domUs
                _node.mExecuteCmdLog(f"/bin/sed -i '/{_deletenode}/d' /etc/hosts")
                _node.mExecuteCmdLog(f"/bin/sed -i '/{_delnode}/d' /etc/hosts")

    def mGetDbList(self, aDomU):
        """
            Return list of databases for domU
        """
        _domU = aDomU
        _path, _, _ = self.__eboxobj.mGetOracleBaseDirectories(aDomU = _domU)
        _node = exaBoxNode(get_gcontext())
        _node.mSetUser('root')
        _node.mConnect(aHost=_domU)
        _cmd = f'{_path}/bin/srvctl config database'
        _i, _o, _e = _node.mExecuteCmd(_cmd)
        _out = _o.readlines()
        _node.mDisconnect()
        if not _out or len(_out) == 0:
            return []
        ebLogInfo('*** mGetDbList:  %s ' % (_out))
        return _out

    def mGetOracleHome(self, aDomU, aDbName):
        _node = exaBoxNode(get_gcontext())
        _node.mSetUser('root')
        _node.mConnect(aHost=aDomU)

        _cmd = "cat /etc/oratab | grep %s | awk -F : '{print $2}' "%(aDbName)
        _i, _o, _e = _node.mExecuteCmd(_cmd)
        _out = _o.readlines()
        if not _out or len(_out) == 0:
            return ""
        _path = _out[0].strip()

        _node.mDisconnect()

        ebLogInfo(f"*** oracle_home:{_path} for DB:{aDbName}")
        return _path

    def mUpdateDbInstance(self, aDomU, aDbList):
        """
            Change the state of the DB instance from preferred to available
        """
        _ebox = self.__eboxobj
        _domU = aDomU
        _srcDomU = self.mGetSrcDomU()
        _node = exaBoxNode(get_gcontext())
        _node.mSetUser('root')
        _node.mConnect(aHost=_srcDomU)

        for _dbName in aDbList:
            _dbName = _dbName.strip()
            _path, _, _  = _ebox.mGetOracleBaseDirectories(_srcDomU, _dbName)
            if not _path:
                continue
            _cmd_pfx = 'ORACLE_HOME=%s;export ORACLE_HOME;' % (_path)
            _cmd = _cmd_pfx + "$ORACLE_HOME/bin/srvctl status database -d %s " % (_dbName)
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            _out = _o.readlines()
            _db_status = {}
            for _item in _out:
                _instance = _item.split()
                _db_status[_instance[-1]] = {}
                _db_status[_instance[-1]]["instance_name"] =  _instance[1]
                _db_status[_instance[-1]]["instance_status"] = "down" if "not running" in _item else "up"
            ebLogInfo('*** DB status:  %s ' % (_db_status))

            _cmd = _cmd_pfx + "$ORACLE_HOME/bin/srvctl status service -d %s " % (_dbName)
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            _out = _o.readlines()
            _service_names = []
            if _out:
                for _line in _out:
                    _line = _line.strip()
                    _service_names.append(_line.split()[1])
            ebLogInfo('*** Service Names:  %s ' % (_service_names))

            for _service_name in _service_names:
                _cmd = _cmd_pfx + "$ORACLE_HOME/bin/srvctl config service -d %s -service %s | grep 'Preferred instances' " % (_dbName, _service_name)
                _i, _o, _e = _node.mExecuteCmd(_cmd)
                _out = _o.readlines()
                _preferred_instance = []
                if _out:
                    _preferred_instance = _out[0].split(':')[1].strip().split(',')
                ebLogInfo('*** Prefered Instances:  %s  on service: %s' % (_preferred_instance, _service_name))

                _inst_name = ""
                _hostname = _domU.split('.', 1)[0]
                if _hostname in _db_status.keys():
                    _inst_name = _db_status[_hostname]["instance_name"]
                if _preferred_instance and _inst_name in _preferred_instance:
                    ebLogInfo("*** Update DB Configuration from Preferred to Available.")
                    _preferred_instance.remove(_inst_name)
                    _preferred = ','.join(_preferred_instance)

                    _cmd = _cmd_pfx + "$ORACLE_HOME/bin/srvctl modify service -d %s -service %s -modifyconfig -preferred %s -available %s " % (_dbName, _service_name, _preferred, _inst_name)
                    _i, _o, _e = _node.mExecuteCmd(_cmd)
                    _out = _o.readlines()

                _cmd = _cmd_pfx + "$ORACLE_HOME/bin/srvctl config service -d %s -service %s | grep -E 'Preferred instances|Available instances' " % (_dbName, _service_name)
                _i, _o, _e = _node.mExecuteCmd(_cmd)
                _out = _o.readlines()
                for _ret in _out:
                    ebLogInfo('*** %s on database %s for service:%s' % (_ret.strip(), _dbName, _service_name))
    
        _node.mDisconnect()

    def mRemoveDBInstancesFromVMDbaascli(self, aDomu, aOptions=None):
        _domu = aDomu
        _domu_shrtnm = _domu.split('.')[0]
        _srcdomU = self.mGetSrcDomU()
        _srcdomU_shrtnm = _srcdomU.split('.')[0]
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_srcdomU)
        _db_instance_removed = False
        _db_instance_domu = False
        _ebox = self.__eboxobj

        _databases = getDatabases(_srcdomU)
        ebLogTrace(f'List of Databases from {_srcdomU}: {_databases}')
        _deleted_instances = set()

        for _dbname in _databases:
            if 'dbNodeLevelDetails' in _databases[_dbname].keys() and not _databases[_dbname]['dbNodeLevelDetails']:
                continue
            for _nodeName in _databases[_dbname]['dbNodeLevelDetails']:
                # delete instances on given domU only
                if _nodeName == _srcdomU_shrtnm:
                    if _databases[_dbname]["dbRole"] in ["PRIMARY"] and _databases[_dbname]["dbNodeLevelDetails"][_nodeName]["status"] in ["OPEN", "READ_ONLY"] \
                        or _databases[_dbname]["dbRole"] == "PHYSICAL_STANDBY" and _databases[_dbname]["dbNodeLevelDetails"][_nodeName]["status"] in ["MOUNTED", "READ_ONLY"]:
                        ebLogInfo(f'Database {_dbname} running on node {_srcdomU}')
                        ebLogInfo(f'Deleting database instance {_dbname} for {_domu} on source node {_srcdomU}')
                        _rc = deleteInstance(_srcdomU, _dbname, _domu)
                        if _rc == 0:
                            _deleted_instances.add(_dbname)

        # check the status of databases deleted
        _databases = getDatabases(_srcdomU)
        for _dbname in _databases:
            if _dbname not in _deleted_instances or ('dbNodeLevelDetails' in _databases[_dbname].keys() and not _databases[_dbname]['dbNodeLevelDetails']):
                continue
            if not _databases[_dbname].get('dbNodeLevelDetails'):
                continue
            for _node in _databases[_dbname]['dbNodeLevelDetails']:
                if _node == _domu_shrtnm: 
                    if _databases["dbNodeLevelDetails"][_node]["status"] in ["OPEN", "MOUNTED", "READ_ONLY"]:
                        _detail_error = f"Failed to remove DB instances {_dbname} using dbaascli on {_node}"
                        _ebox.mUpdateErrorObject(gNodeElasticError['DB_INST_NOT_REMOVED'], _detail_error)
                        raise ExacloudRuntimeError(0x0771, 0xA, _detail_error)
                    else:
                        ebLogInfo(f'Database {_dbname} successfully deleted on node {_node}')

    def mRemoveDBInstancesFromVM(self, aDomu, aOptions=None):

        #TBD: use dbaasapi instead of invoking dbascli directly
        _domu = aDomu
        _srcDomU = self.mGetSrcDomU()
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_srcDomU)
        _db_instance_removed = False
        _db_instance_domu = False
        _dbaasobj = self.__dbaasobj
        _ebox = self.__eboxobj
        _debug = _ebox.mIsDebug()

        ebLogInfo('*** Remove DB Instance on node %s' %(_domu)) 
        self.mCheckDBConfiguration(_srcDomU)
        #get db instances info using dbaas api
        #sending copy of options bcz dbaas api requires some additional params to be added 
        #which should not change the original aOptions
        _db_instances = self.mGetDbInfo(_srcDomU, copy.deepcopy(aOptions))

        for _db_instance in _db_instances:
            if (len(_db_instance["nodelist"]) == 1):
                _host = _db_instance["nodelist"].pop() + '.' + _db_instance["domain"]
                if aOptions.force and _host == aDomu:
                    _db_instance_domu = True
                    break
                elif aOptions.force is False and _host == aDomu:
                    _detail_error = 'DB instance running on single domu %s' % (_domu)
                    _ebox.mUpdateErrorObject(gNodeElasticError['DB_INST_NOT_REMOVED'], _detail_error)
                    ebLogError('*** ' +_detail_error)
                    raise ExacloudRuntimeError(0x0772, 0xA, _detail_error)
                else:
                    ebLogInfo('*** DB Instance not running on domu %s' %(_domu))
                    return
            elif aDomu.split('.')[0] in _db_instance["nodelist"]:
                _db_instance_domu = True
                break

        if _db_instance_domu is False:
            ebLogInfo('*** DB Instance not running on domu %s' %(_domu))
            return 

        _remove_domU = _domu
        for _db_instance in _db_instances:
            if _remove_domU.split('.')[0] in _db_instance["nodelist"]:
                _dbname = _db_instance['db_name']
                # Determine the node where the DB instance is running
                _params = {}
                _params["dbname"] = _dbname
                _params["infofile"] = "/var/opt/oracle/log/get_inst_status_" + _ebox.mGetUUID() + "_status.json"
                _dbaas_data = {}
                _dbaasobj.mExecuteDBaaSAPIAction("get", "inst_status", _dbaas_data, _srcDomU, _params, aOptions)
                _stjson = _dbaas_data["get"]
                _domU = None
                _domainname = _remove_domU.split('.',1)[1]
                _instance = "down"
                for _entry in list(_stjson.keys()):
                    if _stjson[_entry]["instance_status"] == "up" and _entry != _remove_domU.split('.')[0]:
                        _instance = "up"
                        _domU = _entry + "." + _domainname
                        break

                # Cleanup redo and undo tablespace of the DB.
                _params = {}
                _params["dbname"] = _dbname
                _params["nodename"] = _remove_domU.split('.')[0]

                if _instance == "down":
                    _params["connectable"] = "no"
                    _domU = _remove_domU.split('.')[0]
                else:
                    _params["connectable"] = "yes"

                ebLogInfo("Execute update_dbinst dbaasapi for %s in the VM: %s" % (_dbname, _domU))
                if _debug :
                    ebLogDebug("Json Payload for update_dbinst dbaasapi:%s" % (_params))
                _dbaas_data = {}
                _dbaasobj.mExecuteDBaaSAPIAction("clean", "update_dbinst", _dbaas_data, _domU, _params, aOptions, aRaiseError=False)
                _db_instance_removed = True

        if _db_instance_removed is True:
            #validate, thr shud not be any db instance with delete node included
            _db_instances = self.mGetDbInfo(_srcDomU, copy.deepcopy(aOptions))
            for _db_instance in _db_instances:
                if  _remove_domU in _db_instance["nodelist"]:
                    _detail_error = "Failed to remove DB instances %s using dbaasapi on %s" %(str(_db_instances), _remove_domU)
                    _ebox.mUpdateErrorObject(gNodeElasticError['DB_INST_NOT_REMOVED'], _detail_error)
                    raise ExacloudRuntimeError(0x0771, 0xA, _detail_error)

    def mCheckDBConfiguration(self, aDomu):
        """
        dbaasapi does not support DB instance removal in following cases:
        1. If DG setup on node to be deleted
        2. if DB running is testmaster instance
        3. if DB is clone 
        """
        def _checkTestMasterConfigured(aDomu):
            return False

        def _checkDGConfigured(aDomu):
            return False

        def _checkCloneNodeConfigured(aDomu):
            return False

        _ebox = self.__eboxobj
        _testmaster_enabled = _checkTestMasterConfigured(aDomu)
        _dg_enabled = _checkDGConfigured(aDomu)
        _clone_enabled = _checkCloneNodeConfigured(aDomu)

        if _testmaster_enabled:
            _detail_error = "Testmaster Enabled, DB instance can not be removed using dbaas api for %s" %(aDomu)
            _ebox.mUpdateErrorObject(gNodeElasticError['DB_INST_NOT_REMOVED'], _detail_error)
            raise ExacloudRuntimeError(0x0772, 0xA, _detail_error)
        if _dg_enabled:
            _detail_error = "DG Enabled, Failed to remove DB instances %s using dbaasapi on %s" %(aDomu)
            _ebox.mUpdateErrorObject(gNodeElasticError['DB_INST_NOT_REMOVED'], _detail_error)
            raise ExacloudRuntimeError(0x0772, 0xA, _detail_error)
        if _clone_enabled:
            _detail_error = "Clone node, Failed to remove DB instances %s using dbaasapi on %s" %(aDomu)
            _ebox.mUpdateErrorObject(gNodeElasticError['DB_INST_NOT_REMOVED'], _detail_error)
            raise ExacloudRuntimeError(0x0772, 0xA, _detail_error)

    def mPostReshapeValidation(self, aOptions, aReshapeConfig, aDomUList=None):
        #
        #validate if participant nodes are up and running after reshape operation
        #
        _action = self.__reshape_conf['action']
        _reshape_domu_list = [x['domU']['hostname'] for x in self.__reshape_conf['nodes']]
        ebLogInfo("Running Post Reshape Validation")
        _ebox = self.__eboxobj 
        _report_fatal_err = _ebox.mCheckConfigOption('report_fatal_err', 'True')
        if aDomUList:
            _domu_list = aDomUList
        else:
            _domu_list = [ _domu for _ , _domu in _ebox.mGetOrigDom0sDomUs()]

        # Checking cluster integrity
        if not _ebox.mIsExaScale():
            _pchecks = ebCluPreChecks(_ebox)
            _pchecks.mCheckClusterIntegrity(True, _report_fatal_err, _domu_list)

        # Add VIP will be executed by DBaaS agent for ExaDB-XS
        if _ebox.mIsExaScale():
            ebLogWarn("*** Skipping add VIP for ExaDB-XS clusters.")
        else:        
            # Check if cluster contains correct set of nodes (post add-delete node)
            _domu_list = [ _domu.split('.')[0] for _ , _domu in _ebox.mGetOrigDom0sDomUs()]
            _srcdomU = self.mGetSrcDomU()
            _path, _, _ = _ebox.mGetOracleBaseDirectories(aDomU = _srcdomU)
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(_srcdomU)

            for _domU in _reshape_domu_list:
                _, _, _ = _node.mExecuteCmd(f'{_path}/bin/srvctl config vip -node {_domU}')
                if _node.mGetCmdExitStatus() != 0 and _action == 'ADD_NODE':
                    _error = "Failed to add VIP of the new node"
                    _ebox.mUpdateErrorObject(gNodeElasticError['INCORRECT_VIP_CONFIGURATION'], _error)
                    ebLogError(_error)
                    raise ExacloudRuntimeError(0x0661, 0xA, _error)

                if _node.mGetCmdExitStatus() == 0 and _action == 'DELETE_NODE':
                    _error = "Failed to cleanup the VIP of the node"
                    _ebox.mUpdateErrorObject(gNodeElasticError['INCORRECT_VIP_CONFIGURATION'], _error)
                    ebLogError(_error)
                    raise ExacloudRuntimeError(0x0661, 0xA, _error)
            
            _, _o, _ = _node.mExecuteCmd(f'{_path}/bin/olsnodes')
            _node.mDisconnect()
            _list = _o.read().strip().split('\n')

            if sorted(_list) != sorted(_domu_list):
                _detail_error = f"Error, lists does not match: {sorted(_list)} / {sorted(_domu_list)}" 
                _ebox.mUpdateErrorObject(gNodeElasticError['NODE_SET_WRONG'], _detail_error)
                ebLogError(_detail_error)
                raise ExacloudRuntimeError(0x0782, 0xA, 'Cluster does not contain the correct set of nodes')

        _ebox.mExecuteProfileClusterCheck("hc_domU.prf")

    def mGetDbInfo(self, aDomu, aOptions=None):
        #TODO: pass json input required to run dbaas api
        ebLogInfo('Fetch DB instances info using DBaaS API operation')
        _db_instances   = []
        _dbaas_data     = {}
        _dbaas_data["DbInfo"] = None
        _domu = aDomu
        _ebox = self.__eboxobj

        #append params required to fetch db info using dbaasapi
        aOptions.jsonconf['dbname'] = "grid"
        aOptions.jsonconf['mode'] = "all"

        #invoke dbinfo using dbaasapi
        _dbaasobj = self.__dbaasobj 
        _rc = _dbaasobj.mClusterDbaas(aOptions, "db_info", _dbaas_data)
        if _rc:
           _detail_error = 'Failed to get dbinfo using dbaas api on: %s' % (_domu) 
           _ebox.mUpdateErrorObject(gNodeElasticError['NODE_SET_WRONG'], _detail_error)
           ebLogError("*** ERROR:" + _detail_error)
           raise ExacloudRuntimeError(0x0771, 0xA, _detail_error)

        if _dbaas_data["DbInfo"] is None:
            _detail_error = "DbInfo returned as null from using dbaas api on: %s" % (_domu)
            _ebox.mUpdateErrorObject(gNodeElasticError['DB_INFO_FAILED'], _detail_error)
            ebLogError("*** ERROR: " + _detail_error)
            raise ExacloudRuntimeError(0x0771, 0xA, _detail_error)

        for _db_inst, _db_details in _dbaas_data["DbInfo"].items():
            _dbinfo = {}
            _dbinfo["db_name"] = _db_details["db_name"]
            _dbinfo["domain"] = _db_details["domain"]
            _dbinfo["nodelist"] = [str(nodename) for nodename in _db_details["nodelist"].split()]
            _db_instances.append(_dbinfo)

        ebLogVerbose('DB instances running on nodelist %s' %str(_db_instances))
        return _db_instances


    def mRemoveComputeGIDelete(self, aStep, aStepList, aOptions):
        _ebox = self.__eboxobj
        _step_list = aStepList

        if aStep == "OSTP_PREGI_DELETE":
            # PRE-GI - Run External Scripts
            #
            _step_time = time.time()
            _ebox.mUpdateStatusOEDA(True, OSTP_PREGI_DELETE, [OSTP_PREGI_DELETE], 'Running External PREGI Scripts')
            _ebox.mRunScript(aType='*',aWhen='pre.gi_delete')
            _ebox.mLogStepElapsedTime(_step_time, 'Running External PREGI Scripts')
            _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'DONE', f"Elastic Delete Compute step {aStep} completed", aStep)
            self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, aStep, "DONE", _stepSpecificDetails)
        elif aStep == "OSTP_POSTGI_DELETE":
            #
            # POSTGI - Run External Scripts
            #
            _step_time = time.time()
            _ebox.mUpdateStatusOEDA(True, OSTP_POSTGI_DELETE, [OSTP_POSTGI_DELETE], 'Running External POSTGI Scripts')
            _ebox.mRunScript(aType='*',aWhen='post.gi_delete')
            _ebox.mLogStepElapsedTime(_step_time, 'Running External POSTGI Scripts')
            _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'DONE', f"Elastic Delete Compute step {aStep} completed", aStep)
            self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, aStep, "DONE", _stepSpecificDetails)

    def mRemoveComputeInstallCluster(self, aDomUList, aStepList, aOptions):
        #
        # Remove DBHomes
        #
        _ebox = self.__eboxobj
        _step_list = aStepList
        _oeda_path  = _ebox.mGetOedaPath()
        _oedacli_bin = _oeda_path + '/oedacli'
        #TODO: store intermediate xml files returned from oedacli to some location 
        _savexmlpath = _oeda_path + '/exacloud.conf'
        _reshape_domu_list = aDomUList
        _options = aOptions
        step = aStepList[0]


        # Update password in es.properties
        ebLogInfo("Updating non-root password in es.properties for oedacli delete cluster execution")
        _srcDomU = self.mGetSrcDomU()

        if not _ebox.mIsExaScale():
            if _ebox.IsZdlraProv():
                _pswd = _ebox.mGetZDLRA().mGetWalletViewEntry('passwd', _srcDomU)
            elif _ebox.mIsAdbs():
                _pswd = _ebox.mGetAsmSysPasswordForAdbs('asmsys', _srcDomU)                                                                
            else:                                                                                                                                  
                _pswd = _ebox.mGetSysPassword(_srcDomU)                                                                                           
            _ebox.mUpdateOedaUserPswd(_ebox.mGetOedaPath(), "non-root", _pswd)

        _uuid = str(uuid.uuid1())
        _oeda_path = _ebox.mGetOedaPath()
        _deletenodexml = _oeda_path + '/exacloud.conf/deletenode_' + _uuid + '.xml'
        _patchconfig = _ebox.mGetPatchConfig()
        _ebox.mExecuteLocal("/bin/cp {} {}".format(_patchconfig, _deletenodexml))

        try:
            _ebox.mAcquireRemoteLock()
            _step_time = time.time()
            _ebox.mUpdateStatusOEDA(True, OSTP_INSTALL_CLUSTER, [OSTP_INSTALL_CLUSTER], 'Running oedacli step to remove DBHomes')
            _oedacli_mgr = OedacliCmdMgr( _oedacli_bin, _savexmlpath)
            _oedacli_mgr.mDeleteDBHomes(_reshape_domu_list, _deletenodexml, _savexmlpath+'/deletedbhome.xml')
            _ebox.mLogStepElapsedTime(_step_time, 'Running oedacli step to remove DBHomes')

        except Exception as e:
            _detail_error = f"Error running oedacli step to remove DBHomes: {str(e)}" 
            _ebox.mUpdateErrorObject(gNodeElasticError['FAILED_REMOVE_DBHOME'], _detail_error)
            ebLogError("*** ERROR: " + _detail_error)
        finally:
            _ebox.mReleaseRemoteLock()
        
        _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'ONGOING', f"Elastic Delete Compute {step} task remove DBHomes in progress", step)
        self.mGetCluUtils().mUpdateTaskProgressStatus([], 50, step, "In Progress", _stepSpecificDetails)

        _remote_lock = _ebox.mGetRemoteLock()
        with _remote_lock():
            try:
                _step_time = time.time()
                _ebox.mUpdateStatusOEDA(True, OSTP_INSTALL_CLUSTER, [OSTP_INSTALL_CLUSTER], 'Running oedacli step to remove cluster node') 
                _oedacli_mgr = OedacliCmdMgr( _oedacli_bin, _savexmlpath)
                _oedacli_mgr.mDeleteClusterNode(_reshape_domu_list, _deletenodexml, _savexmlpath+'/rootscript.xml', 'RUN_ROOTSCRIPT')

                _oedacli_mgr = OedacliCmdMgr( _oedacli_bin, _savexmlpath)
                _oedacli_mgr.mDeleteClusterNode(_reshape_domu_list, _deletenodexml, _savexmlpath+'/deletecluster.xml', 'CONFIG_CLUSTERWARE')

                _ebox.mLogStepElapsedTime(_step_time, 'Running oedacli step to remove cluster node')
                # Cleanup entries from CRS. Bug 37111990: to include this function in install cluster step as well.
                for _reshape_domu in _reshape_domu_list:
                    self.mRemoveNodeFromCRS(_reshape_domu)
                    
            except:
                _detail_error = 'Error running oedacli step to remove cluster node'
                _ebox.mUpdateErrorObject(gNodeElasticError['FAILED_REMOVE_CLUSTER_NODE'], _detail_error)
                ebLogError("*** ERROR: " + _detail_error)
                if _ebox.mCheckConfigOption('raise_exception_delete_compute', 'True'):
                    global EXCEPTION_IN_CRS
                    EXCEPTION_IN_CRS = True
                    raise ExacloudRuntimeError(0x0801, 0xA, _detail_error)
        _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'DONE', f"Elastic Delete Compute step {step} completed", step)
        self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, step, "DONE", _stepSpecificDetails)

    def mRemoveComputePreVMDelete(self, aStepList, aOptions):
        #
        # PREVM - Run External Scripts
        #
        _ebox = self.__eboxobj
        _step_list = aStepList
        _step_time = time.time()
        _ebox.mUpdateStatusOEDA(True, OSTP_PREVM_DELETE, [OSTP_PREVM_DELETE], 'Running External PREVM Scripts')
        _ebox.mRunScript(aType='*',aWhen='pre.vm_delete')
        step = aStepList[0]
        _ebox.mLogStepElapsedTime(_step_time, 'Running External PREVM Scripts')

        if self.__reshape_conf['keep_dyndep_cache'] != 'True':

            #
            # PREVM - Shred VM Images (Sytem, User, DB/GI bits)
            #
            _step_time = time.time()
            _ebox.mUpdateStatusOEDA(True, OSTP_PREVM_DELETE, [OSTP_PREVM_DELETE],
                                                     'VM Image shredding in progress (this operation can take a long time')
            _ebox.mVMImagesShredding(aOptions)
            _ebox.mLogStepElapsedTime(_step_time, 'VM Image shredding')
        _stepSpecificDetails = self.mGetCluUtils().mStepSpecificDetails("elasticDeleteDetails", 'DONE', f"Elastic Delete Compute step {step} completed", step)
        self.mGetCluUtils().mUpdateTaskProgressStatus([], 100, step, "DONE", _stepSpecificDetails)

    def mRemoveComputeVMDelete(self, aDom0, aDomU, aStepList, aOptions):
        #
        # xxx/MR: OEDA Delete VM currently bypassed due to switch configuration being changed
        # TODO: Check if future version of OEDA remove this issue/constraints
        #
        _ebox = self.__eboxobj
        _debug = _ebox.mIsDebug()
        _oeda_path  = _ebox.mGetOedaPath()
        _oedacli_bin = _oeda_path + '/oedacli'                                                                                                 
        #TODO: store intermediate xml files returned from oedacli to some location                                                             
        _savexmlpath = _oeda_path + '/exacloud.conf'                                                                                           
        _oedacli_mgr = OedacliCmdMgr( _oedacli_bin, _savexmlpath)
        _csu = csUtil()
        _reshape_dom0 = aDom0
        _reshape_domu = aDomU
        _step_list = aStepList
        _step_time = time.time()
        _non_oeda_cleanup = True
        _ebox.mUpdateStatusOEDA(True, OSTP_CREATE_VM, [OSTP_CREATE_VM], 'Delete Virtual Machine')

        if _ebox.mIsExaScale():
            _exascale = ebCluExaScale(_ebox)     
            _json = {}
            for _dom0, _domU in _ebox.mReturnDom0DomUPair():        
                for _dev in ['u01', 'u02']:
                    ebLogInfo(f"Checking if any snapshots need to be unmounted as part of delete node")
                    _lvm, _snap_dev = _exascale.mGetLVDev(_dom0, _domU, _dev)
                    if not _snap_dev or not _lvm:
                        ebLogInfo(f"No {_dev} snapshot mounted for the VM {_domU}. Nothing to unmount")
                        continue
                    _json['snapshot_device_name'] = _snap_dev 
                    _json['lvm'] = _lvm
                    _json['dom0'] = _dom0
                    _json['vm'] = _domU
                    ebLogInfo(f"Performing unmount of snapshot for {_json}")
                    _exascale.mUnmountVolume(aOptions, _json)

        _bridges = _csu.mFetchBridges(_ebox, [(_reshape_dom0, _reshape_domu)])

        _uuid = str(uuid.uuid1())
        _oeda_path = _ebox.mGetOedaPath()
        _deletenodexml = _oeda_path + '/exacloud.conf/deletenode_' + _uuid + '.xml'
        _patchconfig = _ebox.mGetPatchConfig()
        _ebox.mExecuteLocal("/bin/cp {} {}".format(_patchconfig, _deletenodexml))

        #
        # Populate final config (new OEDA requirement)
        #
        _ebox.mCopyFinalVMConfig(_oeda_path)

        #
        # Try to clean up via OEDA first
        #
        if _ebox.mCheckConfigOption('oeda_vm_delete_step', 'True'):
            #remove vm using oedacli first
            _non_oeda_cleanup = False
            try:
                # Update es.properties with non-root password
                ebLogInfo("Updating non-root password in es.properties for oedacli delete guest execution")
                _srcDomU = self.mGetSrcDomU() 

                if not _ebox.mIsExaScale():
                    if _ebox.IsZdlraProv(): 
                        _pswd = _ebox.mGetZDLRA().mGetWalletViewEntry('passwd', _srcDomU)
                    elif _ebox.mIsAdbs():
                        _pswd = _ebox.mGetAsmSysPasswordForAdbs('asmsys', _srcDomU)
                    else:
                        _pswd = _ebox.mGetSysPassword(_srcDomU) 
                    _ebox.mUpdateOedaUserPswd(_ebox.mGetOedaPath(), "non-root", _pswd)
 
                _ebox.mAcquireRemoteLock()
                # OEDACLI: Delete Guest
                _oedacli_mgr.mVMOperation(_reshape_domu, _deletenodexml, _savexmlpath+'/deletedvm.xml', 'delete')
            except Exception as e:
                _non_oeda_cleanup = True
                ebLogInfo(f"Error while deleting the VM {_reshape_domu} using oedacli")
            finally:
                _ebox.mReleaseRemoteLock()

        if _ebox.mCheckConfigOption('min_vm_cycles_reboot') is None or _non_oeda_cleanup:

            #remove only reshaped domu
            if not _ebox.mIsKVM():
                _cmd_str  = '/opt/exadata_ovm/exadata.img.domu_maker remove-domain '+_reshape_domu+' -force'
                if _ebox.mIsExabm():
                    _cmd_str += ' ; /opt/exadata_ovm/exadata.img.domu_maker remove-bridge-dom0 vmeth100 -force'
                _cmd_str2 = 'xm destroy '+_reshape_domu
                _cmd_str3 = ''
                _chkvm_cmd = 'xm list | grep '+ _reshape_domu
            else:
                _cmd_str = '/opt/exadata_ovm/vm_maker --remove-domain '+_reshape_domu+' --force'
                _cmd_str2 = '/usr/sbin/vm_maker --force --stop-domain '+_reshape_domu
                _cmd_str3 = 'virsh undefine ' + _reshape_domu
                _chkvm_cmd = '/usr/sbin/vm_maker --list | grep '+ _reshape_domu
            _cmd_del_vmbkup = 'source /opt/python-vmbackup/bin/set-vmbackup-env.sh && vmbackup cleanall --vm '+_reshape_domu
            ebLogInfo('*** running vm delete using: '+_cmd_str)
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_reshape_dom0)
            _del_vmbkup = _ebox.mCheckConfigOption('delete_vmbackup')
            if _del_vmbkup is not None and _del_vmbkup == 'True' and not self.__node_recovery:
                _node.mExecuteCmdLog(_cmd_del_vmbkup)
            _node.mExecuteCmdLog(_cmd_str2)
            _rc = _node.mGetCmdExitStatus()
            if _debug :
                ebLogDebug("** [Debug] The command '{0}' returned with the code '{1}'".format(_cmd_str2 , str(_rc)) )
            _node.mExecuteCmdLog(_cmd_str)
            _rc = _node.mGetCmdExitStatus()
            if _debug :
                ebLogDebug("** [Debug] The command '{0}' returned with the code '{1}'".format(_cmd_str , str(_rc)) )

            if _ebox.mIsKVM():
                ebLogInfo('*** Running virsh undefine using : '+_cmd_str3)
                _node.mExecuteCmdLog(_cmd_str3)
                _rc = _node.mGetCmdExitStatus()
                ebLogInfo("** virsh undefine returned with the code '{0}'".format(str(_rc)) )

            _node.mExecuteCmdLog(_chkvm_cmd)
            # If VM is present, retry cmd to remove domain
            if not _node.mGetCmdExitStatus():

                _node.mExecuteCmdLog(_cmd_str)
                _node.mExecuteCmdLog(_chkvm_cmd)
                if not _node.mGetCmdExitStatus():
                    _detail_error = 'Failed to delete VM {}'.format(_reshape_domu)
                    _ebox.mUpdateErrorObject(gNodeElasticError['DEL_VM_FAILED'], _detail_error)
                    raise ExacloudRuntimeError(0x0801, 0xA, _detail_error)

            # Bug 34261110 - Remove stale bridges after VM deletion
            _csu.mDeleteBridges(_ebox, _bridges)

            # Bug 25506875 - ExaCM 16.4.2.1 ExaCM Instance Deletion and Re-creation Failed
            if _ebox.mCheckConfigOption ('force_delete_vm', 'True') :
                _cmd = "ls /EXAVMIMAGES/GuestImages/"+_reshape_domu
                _node.mExecuteCmdLog (_cmd)
                _rc = _node.mGetCmdExitStatus()

                if _rc == 0 :
                    ebLogInfo ("*** Command '{0}' return a non cero value, cheking if the DomU files still present in the Dom0.".format(_cmd_str))
                    _cmd = "losetup -a"
                    _, _o, _e = _node.mExecuteCmd (_cmd)
                    out = _o.readlines()
                    if out :
                        for o in out :
                            if _reshape_domu in o :
                                _cmd = "losetup -d " + o.split(":")[0]
                                ebLogInfo ("*** running: '{0}'".format(_cmd))
                                _node.mExecuteCmdLog (_cmd)
                                _rc = _node.mGetCmdExitStatus()
                                if _rc :
                                    _detail_error = 'Force removal of the vm disk image failed.'
                                    _ebox.mUpdateErrorObject(gNodeElasticError['FAILED_REMOVE_DSK_IMG'], _detail_error)
                                    ebLogError("*** ERROR: " + _detail_error)
                                    if _debug :
                                        ebLogDebug("** [Debug] The command '{0}' returned with the code '{1}'".format(_cmd , str(_rc)) )

                    _cmd = "rm -rf /EXAVMIMAGES/GuestImages/"+_reshape_domu
                    _node.mExecuteCmdLog (_cmd)
                    _cmd = "ls /EXAVMIMAGES/GuestImages/"+_reshape_domu
                    _node.mExecuteCmdLog (_cmd)
                    _rc = _node.mGetCmdExitStatus()
                    if _rc == 0 :
                        _detail_error = "Can't delete VM files from directory /EXAVMIMAGES/GuestImages/{0}".format(_reshape_domu)
                        _ebox.mUpdateErrorObject(gNodeElasticError['FAILED_REMOVE_VM_FRM_DIR'], _detail_error)
                        ebLogError("*** ERROR: " + _detail_error)

            else: # force_delete_vm is not set, try to delete GuestImages/<domU> dir if domu_maker failed (vm.cfg not present)
                ebLogInfo("Deleting potential leftover domU Images")
                _cmd = "rm -rf /EXAVMIMAGES/GuestImages/"+_reshape_domu
                _node.mExecuteCmd(_cmd)

            _node.mDisconnect()
        else:
            _ebox.mCheckVMCyclesAndReboot()

        if not _ebox.mIsExaScale():
            try:
                # Cleanup entries from CRS
                self.mRemoveNodeFromCRS(_reshape_domu)
            except Exception as e:
                _detail_error = f"Failed to Cleanup entries from CRS for {_reshape_domu} with the error {str(e)}"
                ebLogError(_detail_error)
                _ebox.mUpdateErrorObject(gNodeElasticError['DEL_VM_FAILED'], _detail_error)
                global EXCEPTION_IN_CRS
                EXCEPTION_IN_CRS = True
                raise ExacloudRuntimeError(0x0801, 0xA, _detail_error)
            
        if _ebox.IsZdlraHThread() is False:
            _ebox.mGetZDLRA().mEnableDisableHT("Enabled", aOptions)

        if _ebox.mIsExaScale():
            mRemoveVMmount(_ebox, _reshape_dom0, _reshape_domu)

        # For ASM & EXASCALE, Remove EDV Volumes for the GuestVM
        if not _ebox.isBaseDB() and not _ebox.mIsExaScale():
            try:
                _utils = _ebox.mGetExascaleUtils()
                _utils.mRemoveGuestEDVVolumes(aOptions)
            except Exception as e:
                ebLogWarn(f"*** mRemoveGuestEDVVolumes failed with Exception: {str(e)}")

        if not self.__node_recovery:
            #
            # Delete VMBackups of the VM for this cluster
            #
            _step_time = time.time()
            _vmbkupobj = ebCluManageVMBackup(_ebox)

            try:
                # Clean non-golden backups
                _vmbkupobj.mCleanVMbackup(aOptions, [[_reshape_dom0, _reshape_domu]], aCleanGoldBackup=False)
                _vmbackup_data = _vmbkupobj.mGetVMBackupData()
                if _vmbackup_data['Exacloud Cmd Status'] == _vmbkupobj.FAIL:
                    ebLogWarn(f"Failed to delete non-golden vmbackups for the current cluster. Reason: {_vmbackup_data['Log']}")
                else:
                    ebLogInfo("Successfully deleted all non-golden vmbackups for the current cluster")

                # Clean golden backups
                _vmbkupobj.mCleanVMbackup(aOptions, [[_reshape_dom0, _reshape_domu]], aCleanGoldBackup=True)
                _vmbackup_data = _vmbkupobj.mGetVMBackupData()
                if _vmbackup_data['Exacloud Cmd Status'] == _vmbkupobj.FAIL:
                    ebLogWarn(f"Failed to delete golden vmbackups for the current cluster. Reason: {_vmbackup_data['Log']}")
                else:
                    ebLogInfo("Successfully deleted all golden vmbackups for the current cluster")

                # Remove VMbackup Json
                _utils = _ebox.mGetExascaleUtils()
                _utils.mRemoveVMbackupJson(aOptions)
                _ebox.mLogStepElapsedTime(_step_time, 'Delete VMBackups from Dom0')

            except Exception as e:
                _detail_error = f"Failed to delete vmbackups for the current cluster. Reason: {str(e)}"
                ebLogError(_detail_error)
                if (get_gcontext().mGetConfigOptions().get("vmbackup", {}).get("force_error_on_cleanup", "").lower() == "true"):
                    raise ExacloudRuntimeError(0x0801, 0xA, _detail_error)

            for _dom0, _domU in _ebox.mReturnDom0DomUPair():
                with connect_to_host(_dom0, get_gcontext(), username="root") as _node:
                    ebLogInfo(f"Cleanup vmbackup logs for {_domU}")
                    _node.mExecuteCmdLog(f"rm -f /opt/oracle/vmbackup/log/vmbackup_{_domU.split('.')[0]}.log")

        # remove the references of deleted node from existing node
        _ssh_setup_obj = ebCluSshSetup(_ebox)
        _reshape_domu_list = [x['domU']['hostname'] for x in self.__reshape_conf['nodes']]
        for _, domU in _ebox.mGetOrigDom0sDomUs():
            for deleted_domU in _reshape_domu_list:
                for user in ['root', 'opc', 'oracle', 'grid']:
                    _ssh_setup_obj.mRemoveSSHPublicKeyFromVM(domU, deleted_domU, user)
                    hostname = deleted_domU.split('.')[0]
                    if hostname != deleted_domU:
                        _ssh_setup_obj.mRemoveSSHPublicKeyFromVM(domU, hostname, user)
    
        _ebox.mLogStepElapsedTime(_step_time, 'Delete Virtual Machine')

    def mRemoveComputePostVMDelete(self, aStepList, aOptions):
        
        #
        # Remove ClusterConfiguration from Dom0s
        #
        _ebox = self.__eboxobj
        _step_list = aStepList
        _csu = csUtil()

        # Add NAT egress IPS
        _ebox.mAddNatEgressIPs(aOptions)

        #
        # Removing libvirt network filters or NFTables in kvm
        #
        if _ebox.mIsExabm() and _ebox.mIsKVM():
            ebIpTablesRoCE.mRemoveSecurityRulesExaBM(_ebox) 

        _step_time = time.time()
        _ebox.mUpdateStatusOEDA(True, OSTP_POSTVM_DELETE, [OSTP_POSTVM_DELETE], 'Remove Cluster Configuration')
        _ebox.mRemoveClusterConfiguration()
        _ebox.mLogStepElapsedTime(_step_time, 'Remove Cluster Configuration')

        #
        # Update request status
        #

        _step_time = time.time()
        _ebox.mUpdateStatusOEDA(True, OSTP_POSTVM_DELETE, [OSTP_POSTVM_DELETE], 'Running External POSTVM Scripts')
        _ebox.mRunScript(aType='*',aWhen='post.vm_delete')
        _ebox.mLogStepElapsedTime(_step_time, 'Running External POSTVM Scripts')

        #
        # Remove ebtables whitelist if present
        #
        _step_time = time.time()
        _ebox.mUpdateStatusOEDA(True, OSTP_PREVM_DELETE, [OSTP_PREVM_DELETE], 'Remove and flush ebtables from Dom0')
        _ebox.mSetupEbtablesOnDom0(aMode=False)
        _ebox.mLogStepElapsedTime(_step_time, 'Remove and flush ebtables from Dom0')

        #
        # Update nodelist in grid.ini of existing node to contain correct set of nodes.
        #
        _nodelist = " ".join([_domU.split('.')[0] for _, _domU in _ebox.mGetOrigDom0sDomUs()])
        for _, _domU in _ebox.mGetOrigDom0sDomUs():
            with connect_to_host(_domU, get_gcontext(), username="root") as _node:
                _node.mExecuteCmdLog(
                    f"/var/opt/oracle/ocde/rops set_creg_key grid nodelist '{_nodelist}'")

        #
        # Remove nat-rules file to support NAT RULES recreation via dom0_iptables_setup.sh script
        #
        _ebox.mDeleteNatIptablesRulesFile()

        #
        # Remove Storage Pool from libvirt definition on the dom0s
        #
        if _ebox.mIsKVM() and _ebox.mCheckConfigOption('remove_storage_pool','True'):
            _step_time = time.time()
            _csu.mRemoveStoragePool(_ebox)
            _ebox.mLogStepElapsedTime(_step_time, 'Remove Storage Pool from libvirt definition on added dom0s')
