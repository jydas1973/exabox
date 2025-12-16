"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    Error - Basic Error Mgmt Facility

FUNCTION:
    Provide Error management - error mapping and processing

NOTE:
    None

History:
    mpedapro   11/14/25    - Enh::38235082 error codes addition for sriov
    scoral      05/06/2025 - Bug 37665235: Added BROKEN_GCV to gExaDbXSError
    aypaul      04/23/2025 - Bug#37535214 Utility function to backup a file.
    aararora    02/25/2025 - Bug 37513962: Raise exception if there is an issue during storage resize
    dekuckre    10/22/2024 - Add gExaDbXSError
    pbellary    10/09/2024 - Bug 37145972 - EXASCALE: CREATE-SERVICE DID NOT CATCH INCORRECT STATUS IN DBAASCLI ADMIN INITIALIZECLUSTER 
    joysjose    10/01/2024 - Bug 37113297 Add new error code for pmemcache enabling check
    joysjose    09/02/2024 - Bug 36731935 Add Error code for NFTable addition
    gparada     08/15/2024 - Bug 36931417 Error e variable not assigned
    rajsag      08/07/2024 - enh 36894620 - exacc:24.3.2.0.0:exascale: define
                             and create proper error codes mapping for exacloud
                             exascale flow 
    akkar       07/18/2024 - Bug 36521357: Add Error code for 23ai precheck
    joysjose    04/17/2024 - 36406874 - ER for enhanced support of IORM clusterplan, dbplan and pmemcachesize
    akkar       05/26/23   - Bug 35388002: Add Error 816
    mirivier    05/21/2015 - Create file
    mirivier    10/01/2015 - Add new error messages
    mrajm       22/03/2017 - Modify error message for 729
    hgaldame    03/29/2017 - Error 512 added
    sdeekshi    15/05/2017 - Error 743 added
    hgaldame    05/26/2017 - Error 514 Added
    pverma      04/07/2017 - Add error codes for sparse
    hgaldame    10/12/2017 - Error 107,108 Added
    dekuckre    11/29/2017 - Error 109 to 118 added
    dekuckre    12/02/2018 - Error 4036, 4037 added
    hcheon      03/07/2018 - Error 760 added
    dekuckre    03/23/2018 - 27703837: Error 761 and 762 added
    dekuckre    04/19/2018 - 27873458: Error 441 and 442 added
    dekuckre    05/25/2018 - 28060479: Add 822, 823, 824
    gsundara    07/02/2018 - Add a generic errmsg for ER 28096631
    hhhernan    06/25/2018 - 27765340 Add 310
    dekuckre    01/25/2018 - 28429399: Error 774 & 775 added
    araghave    03/21/2019 - 28584487: Add 777
    araghave    10/12/2019 - 30208083: Error 778
    nmallego    29/12/2019 - Bug29997448 - Error detail for no action required 
    araghave    01/02/2020 - ER Bug 30687229 - Add 1018
    nmallego    07/02/2020 - Bug30687255 - The error 1018 is not necessary 
    araghave    02/24/2020 - ER 30908782 - Add 1019
    dekuckre    02/20/2020 - 30817349: Add 917
    seha        04/09/2020 - 31127549: Add 950
    nmallego    04/14/2020 - 30995812: Add 2022 suggestion
    araghave    04/17/2020 - Bug 30536095: Add 620, suggestion 2023
    rajsag      07/02/2020 - Bug 31563524 - EXACC RESHAPE MEMSET ON DOMU FAILURE WITH INCORRECT HUGEPAGES
    devbabu     07/18/2020 - Bug  EXACLOUD ERROR TRANSLATION ISSUE IN EBERROR
    araghave    07/15/2020 - Bug 31465889 - Add 659
    araghave    10/28/2020 - Enh 31925002 - Error code handling implementation 
                             for Monthly Patching
    araghave    12/09/2020 - Enh 31984849 - RETURN ERROR CODES TO DBCP FROM 
                             DOMU AND PLUGINS 
    nmallego    12/08/2020 - Bug31982131 - Error for hardware alert
    dekuckre    12/07/2020 - 32290350: Add PrecheckFailed error
    araghave    11/30/2020 - ER 31604386 - Error code handling for Cells and 
                             Switches
    araghave    01/05/2021 - Bug 32343803 - INFRAPATCHING: INVALID REQUEST 
                             ADDED WHEN PATCHING ATTEMPTED VIA CURL
    rajsag      02/15/2021 - Bug 32299319 - CELL validation error code added
    nmallego    03/25/2021 - Bug32581076 - Error for domu availability check
    araghave    03/23/2021 - Enh 32415170 - Introduce specific Error Codes for 
                             Dom0 and DomU Exacloud Plugins
    alsepulv    03/22/2021 - Enh 32619413: remove any code related to Higgs
    jlombera    03/19/2021 - Bug 32652512: add 'Remote operation error'
    josedelg    04/15/2021 - Bug 32711562 - Patch failed/stuck due to corrupted
                             rpm database
    araghave    04/14/2021 - Enh 31423563 - PROVIDE A MECHANISM TO MONITOR INFRA
                             PATCHING PROGRESS
    aypaul      05/04/2021 - Bug#32677651 Exacloud to update policies on provisioned clusters.
    araghave    04/20/2021 - Bug 32397257 - Get granular error handling details
                             for Dom0 and DomU targets
    araghave    05/19/2021 - Bug 32888765 - Get Granular Error Handling details
                             for Cells and Switches
    araghave    09/07/2021 - Enh 32626119 - Infra patching to notify end user
                             regarding Grid Disks in Unused/Syncing status
    rajsag      08/24/2021 - Bug 31985002 - ensure asm reshape flows update point 
                             in time status for every step in request table
    joserran    08/06/2021 - Bug 32614102: Adding Remote Lock heartbeat mechanism
    araghave    07/20/2021 - Bug 33099120 - INTRODUCE A SPECIFIC ERROR CODE FOR 
                             PATCHMGR CONSOLE READ TIME OUT
    araghave    07/07/2021 - BUG 33081173 - Remove older error codes from Infra 
                             patching core files
    araghave    07/20/2021 - Bug 33099120 - INTRODUCE A SPECIFIC ERROR CODE FOR 
                             PATCHMGR CONSOLE READ TIME OUT
    nmallego    09/13/2021   Bug33249608 - Support non-rolling upgrade
    jyotdas     09/22/2021 - Enh 33290086 - stale mount check before patching for all nodes
    rajsag      10/19/2021 - Enh 33477686 - adding error code handling for the elastic cell in exacloud
    josedelg    10/04/2021 - Bug 33285054 - VIF-BRIDGE symlinks validation in
                             the post check operation
    araghave    11/24/2021 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES FROM ERROR.PY TO 
                                            INFRAPATCHERROR.PY
    aararora    10/06/2023 - Enh 35824846 - Add error messages for reclaiming space for grid mountpoint
    aararora    04/16/2024 - ER 36485120: Support IPv6 in exacloud
    scoral      04/16/2023 - Enh 36283110 - Add VM move prechecks errors.
"""

import six
import time
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogDebug, ebLogWarn

G_SUB_ERROR_RANGE_START = 1
G_SUB_ERROR_RANGE_END = 799
G_RES_ERROR_RANGE_START = 800
G_RES_ERROR_RANGE_END = 849
G_SPARSE_ERROR_RANGE_START = 850
G_SPARSE_ERROR_RANGE_END = 899
G_DBASS_ERROR_RANGE_START = 900
G_DBASS_ERROR_RANGE_END = 999
G_PATCH_ERROR_RANGE_START = 1000
G_PATCH_ERROR_RANGE_END = 1999
G_PATCH_SUGGESTION_RANGE_START = 2000
G_PATCH_SUGGESTION_RANGE_END = 2999
G_BDCS_ERROR_RANGE_START = 3000
G_BDCS_ERROR_RANGE_END = 3999
G_DISKGROUP_ERROR_RANGE_START = 4000
G_DISKGROUP_ERROR_RANGE_END = 4999
G_BMC_ERROR_RANGE_START = 5000
G_BMC_ERROR_RANGE_END = 5999
G_PARTITION_ERROR_RANGE_START = 6000
G_PARTITION_RANGE_END = 6999
G_CELLUPDATE_ERROR_RANGE_START = 7000
G_CELLUPDATE_ERROR_RANGE_END = 7999
G_RECONFIGE_ERROR_RANGE_START = 8000
G_RECONFIGE_ERROR_RANGE_END = 8499
G_EXASCALE_ERROR_RANGE_START = 8500
G_EXASCALE_ERROR_RANGE_END = 8999
G_OCI_ERROR_RANGE_START = 9000
G_OCI_ERROR_RANGE_END = 9999


# Error address space

gMainError = {
    '0'  : ['No error'],
    '701': ['Error while processing mDispatchCluster in Agent'],
    '702': ['Error while processing jsondispatch request'],
    '703': ['Error while processing patch request in Agent'],
    '709' : ['ExacloudRuntimeError occurred']
}

gSubError = {
    '0'   : ['No sub-error available'],
    '10' : ['Remote operation error'],
    '95' : ['Failure during Golden VM Backup step'],
    '96' : ['Failure during FileSystem Encryption'],
    '97' : ['Failed to add ecra nat ip in domU'],
    '98' : ['Agent wallet creation in domU failed'],
    '99' : ['Concurrent requests for the same cluster not supported - retry later'],
    '100' : ['OEDA environment/install location not found'],
    '101' : ['Could not execute OEDA installer'],
    '102' : ['Could not fetch OEDA version'],
    '103' : ['OEDA incorrect version'],
    '104' : ['Missing OEDA version in Exacloud configuration'],
    '105' : ['OEDA version in XML does not match OEDA installed'],
    '106' : ['Cluster XML has not been generated in PAAS mode and can not be processed'],
    '107' : ['SSH key validation failed. SSH key does not exist or invalid'],
    '108' : ['OEDA SSH key create failed. SSH Key invalid or mandatory host not available'],
    '109' : ['Network gateway not provided'],
    '110' : ['Firewall agent not running'],
    '111' : ['Failed to compute md5sum'],
    '112' : ['Database already defined'],
    '113' : ['Invalid parameters passed to restart VM'],
    '114' : ['OEDA error while applying security fixes'],
    '115' : ['Exacloud Operation Failed : Create ASM Diskgroups failed during Create Service'],
    '116' : ['OCDE Step: NID configuration error'],
    '117' : ['Timeout Exception'],
    '118' : ['OEDA error during installation of starter DB'],
    '119' : ['Missing or invalid parameter'],
    '120' : ['Failure during Infiniband Switch setup'],
    '121' : ['Missing SE Linux configuration in request payload.'],
    '123' : ['Failed to update SE Linux mode and policies.'],
    '124' : ['Failed to update SE Linux mode'],
    '125' : ['Failed to update SE Linux policies'],
    '126' : ['ethernet link not detected'],
    '127' : ['Rebalance operation is stuck'],
    '128' : ['Speed of ethernet interface not correctly set'],
    '129' : ['Failure during AHF installation setup'],
    '130' : ['RPM Not found'],
    '131' : ['OS Version mismatch between source domU and new dom0'],
    '132' : ['Reconfiguring grid failed'],
    '133' : ['Execution of root script failed'],
    '150' : ['Error occurred during storage resize operation. Please check exacloud logs for more details.'],
    '200' : ['XML Cluster configuration not available'],
    '201' : ['DYNDEP Update failed to compute md5sum of dependency file'],
    '202' : ['DYNDEP Failed to access dependency file (missing or wrong permission)'],
    '203' : ['DYNDEP Failed to save checksum file for dyndep components'],
    '204' : ['VDISK Creation failed'],
    '205' : ['VDISK Plumbing failed'],
    '206' : ['Extending logical volume failed'],
    '207' : ['Valid json payload is not provided'],
    '208' : ['Path is currently in use'],
    '209' : ['Device name could not be obtained for the provided mountpoint'],
    '210' : ['Could not detach device'],
    '211' : ['Filesystem path could not be obtained for the provided mountpoint'],
    '212' : ['Filesystem could not be unmounted'],
    '213' : ['Device template file could not be copied to DOM0'],
    '214' : ['Could not modify device xml parameter on DOM0'],
    '300' : ['OEDA Translation table not available'],
    '310' : ['Cells services are not running'],
    '390' : ['Basic Prechecks failed during create service'],
    '391' : ['CreateVM Precheck Failed due to RPM database corruption'],
    '400' : ['VM_CMD Error'],
    '401' : ['VM_ID required but not provided during VM_CMD dispatch'],
    '402' : ['VM_ID is not valid VM_CMD dispatch not successful'],
    '403' : ['VM_CMD request was processed but not successful'],
    '405' : ['VM OPC user not found. SSH Key reset not successful'],
    '406' : ['VM_CMD SSH Key operation failed. SSH Key not provided or incorrect'],
    '410' : ['VM already running VM_CMD request not successful'],
    '411' : ['VM is not running VM_CMD request not successful'],
    '412' : ['VM_ID is invalid or corresponding VM not created'],
    '413' : ['GD Grid Disks for current cluster already exists'],
    '414' : ['GD Grid Disks for current cluster does not exist'],
    '415' : ['GD Grid Disks for current cluster cannot be shrunk'],
    '416' : ['GD Grid Disks for current cluster cannot be extended'],
    '417' : ['GD Grid Disks for current cluster cannot be deleted'],
    '418' : ['Grid Disks count mismatch across diskgroups'],
    '420' : ['VM_ID is not valid VM_CMD request not successful'],
    '421' : ['DOM0 is not connectable VM_CMD request not successful'],
    '430' : ['VM_CPUCOUNT dynamic resize failed'],
    '431' : ['VM_CPUCOUNT dynamic resize failed : oversubscription detected'],
    '432' : ['VM_CPUCOUNT dynamic resize failed : undersubscription detected'],
    '433' : ['VM_CPUCOUNT dynamic resize failed : missing json payload'],
    '434' : ['VM_CPUCOUNT dynamic resize failed : maxvpcpus lower than cores requested'],
    '435' : ['VM_CPUCOUNT dynamic resize failed : maxvpcpus cfg not applied to vm - reboot required'],
    '436' : ['VM_CPUCOUNT dynamic resize failed to update all nodes : all the Dom0s were not pingable'],
    '437' : ['VM Image Resize failed: Volume Group Error'],
    '438' : ['Oedacli: clone guest failed'],
    '440' : ['VM did not destroy properly'],
    '441' : ['Failed to get the value of sysctl parameter.'],
    '442' : ['Failed to set the value of sysctl parameter.'],
    '450' : ['Requested memory is not enough'],
    '451' : ['Failed to shutdown VM'],
    '452' : ['Failed to start the VM'],
    '453' : ['Failed to remove Stale Dummy Bridge,it may cause CS failure.Manual cleanup required'],
    '454' : ['Failed to change the autostart parameter status'],
    '501' : ['Post DB install failure. OCDE execution returned an error'],
    '502' : ['Dataguard operation failure. OCDE execution returned an error'],
    '503' : ["DBAAS layer error please check dbaas logs"],
    '504' : ['Database operation failure. OCDE execution returned an error'],
    '505' : ['Create Starter DB NID operation failure. OCDE execution returned an error'],
    '506' : ['NFS mount point validation failure.'],
    '507' : ['Create Starter DB NID missing input parameter for DB Creation'],
    '508' : ['Create Starter DB NID apply security fixes error, cannot parse dbhome from oratab'],
    '509' : ['Create Starter DB NID apply ocde fixes error'],
    '510' : ['Backward starterDB compatibility mode cannot upgrade DB NID images'],
    '511' : ['Backward compatibility mode cannot get the dependency file list'],
    '512' : ['Create Additional DB failure. Invalid value in parameter "nodelist"'],
    '513' : ['Cannot create/delete an additional database 12.2 with GI 12.1'],
    '514' : ['Delete Database failure. Database is not present'],
    '601' : ['Concurrent patch requests not supported - retry later'],
    '602' : ['Could not parse DBCS json input correctly. Please verify your input json'],
    '603' : ['Patch request timed-out - Check individual requests'],
    '604' : ['Master patch request exception detected'],
    '605' : ['One ore more individual patch requests failed'],
    '610' : ['Individual patch request exception detected'],
    '611' : ['Basic patch postchecks failed - See output commands'],
    '612' : ['Patchmgr execution failed - See patchmgr logs'],
    '613' : ['Concurrent patchmgr tasks in same cluster not supported - try later'],
    '614' : ['No action required. Nodes are already at the intended version'],
    '615' : ['Patch monitor exception detected'],
    '616' : ['Unable to download files from object store'],
    '618' : ['Unable to rollback dom0 since a domU vm.cfg was modified after a dom0 patch'],
    '619' : ['Patch prechecks failed - See output commands'],
    '620' : ['Failed to copy patch file to target nodes.'],
    '621' : ['No OCI-EXACC location details found in exabox.conf'],
    '623' : ['DomU XML Patching with DNS and NTP server info failed'],
    '650' : ['Dataguard operation failed'],
    '651':  ['Cannot add static routing rule to domU'],
    '652':  ['Adding iptables rules to dom0 failed'],
    '653':  ['Adding backup IP to sshd_conf failed'],
    '654' : ['Invalid JSON Payload for add_atpbackup_route endpoint'],
    '655' : ['Error inside VM during execution of add_atpbackup_route'],
    '656' : ['Invalid JSON Payload for dom0_atpiptables_change endpoint'],
    '657' : ['No output from dom0 iptables commands'],
    '658' : ['iptables validation error'],
    '659' : ['Unable to set system attributes, specific to ATP Exacc environments during DomU Patch operation'],
    '660' : ['Failed to patch XML with add volume for u01'],
    '661' : ['Incorrect VIP configuration in the cluster'],
    '662' : ['Failed to post validate DNS/Ip Route after VM creation'],
    '719' : ['Prechecks for ExaDBXS env failed'],
    '720' : ['Exadata image does not support minimum Grid version required for the Database requested'],
    '721' : ['DB Version requested is 12.2 but support for 12.2 DB is disabled'],
    '722' : ['Image info version error please check cells image and try again'],
    '723' : ['GI Mount point in VM not found or invalid GI klone image'],
    '724' : ['DB Mount point in VM not found or invalid DB klone image'],
    '725' : ['DB Version corresponding klone image not found in VM'],
    '726' : ['DB Version requested is 12.2 but no GI 12.2 klone image not found in VM'],
    '727' : ['DB Version not supported with GI 12.2 for starter DB'],
    '728' : ['Invalid number of DB Homes found in XML. DB Version requested incompatible with current environment'],
    '729' : ['DB Version requested is either 12.1 or 11.2 but GI 12.1 klone image not found in VM, GI 12.2 with starter DB 11.2 or 12.1 is not yet a configuration supported'],
    '730' : ['First-boot system image version error or system image not found. Please check local system image availability and try again'],
    '731' : ['Not enough memory available on dom0 to complete create service'],
    '732' : ['Not enough storage available on dom0 to complete create service'],
    '733' : ['Cluster limit reached. New cluster cannot be created'],
    '734' : ['Cmd not supported for the env'],
    '735' : ['Neither of IPv4 or IPv6 IPs present in the payload'],
    '740' : ['Invalid CS Customer Network JSON format or content'],
    '741' : ['Invalid XML TMPL format or content'],
    '742' : ['Invalid clustername specified in JSON length greater that 11 characters'],
    '743' : ['Cell not in normal state'],
    '746' : ['Invalid Input'],
    '747' : ['Unable to fetch information from domU'],
    '750' : ['Failing to apply iptables rule during PREVM CS step'],
    '751' : ['Failed to add ebtables rule'],
    '752' : ['Error during Higgs Installation'],
    '753' : ['Error in elastic info flow'],
    '754' : ['Error while multiprocessing(Parallel Copy Error)'],
    '755' : ['Error while multiprocessing(Non-zero exitcode returned)'],
    '756' : ['Error while multiprocessing(Processes timedout)'],
    '757' : ['No active node in the cluster'],
    '758' : ['DomU not found'],
    '759' : ["Invalid invocation or unsupported DNS entry type"],
    '760' : ['Failed to execute security hardening command at POST GI step'],
    '761' : ['Failed to compute minimum total storage in /EXAVMIMAGES partition in dom0s'],
    '762' : ['Failed to compute minimum available storage in /EXAVMIMAGES partition in dom0s'],
    '763' : ['Failed to access/read vmbackup configuration file'],
    '764' : ['Failed to patch XML for node subset'],
    '765' : ['Invalid Json Payload for node subset'],
    '766' : ['Invalid hostname or node type'],
    '767' : ['Required patch files not found'],
    '768' : ['Invalid Json Payload for reshape operation, Add and Remove node not allowed in single operation'],
    '769' : ['Invalid Json Payload for reshape operation, Multiple Add(/Remove) node not allowed in single operation'],
    '770' : ['Invalid Json Payload for Reshape Operation'],
    '771' : ['Error running dbaascli on target domU'],
    '772' : ['Failed to remove node on target domU'],
    '773' : ['Failed to delete quorum disk'],
    '774' : ['Failed to read Job ID from domU'],
    '775' : ['DBAASAPI action failed on DomU'],
    '776' : ['Failed to add quorum disk'],
    '777' : ['Insufficient disk space to store thread logs, disk space needs to be cleared before infra patching is started'],
    '778' : ['The node is on requested version, but critical services are not running'],
    '779' : ['Post plugins failed on upgraded node'],
    '780' : ['Error while modifying CPU oversubscription factor'],
    '781' : ['Invalid steplist for Create Service Step Wise execution'],
    '782' : ['Cluster verification Failed'],
    '783' : ['Ksplice plugin failed, validate input and re-run patch'],
    '784' : ['One-off patch failed, validate input and re-run patch'],
    '785' : ['Failed to get network interfaces details during Jumbo Frames configuration'],
    '786' : ['Error while changing network interface MTU during Jumbo Frames configuraton'],
    '787' : ['Operations are blocked to be executed in Exacloud'],
    '788' : ['Invalid block state'],
    '789' : ['Target env is BM and should be converted to OVM'],
    '790' : ['Null response '],
    '791' : ['Failed to run diagnosis. Please look into diagnostic.log'],
    '792' : ['Error in fetching grid.ini'],
    '793' : ['Invalid user'],
    '794' : ['Error while syncing DB homes'],
    '795' : ['Log directory creation failed'],
    '796' : ['mFetchSshKeys error'],
    '797' : ['DB details for EM fetch failed'],
    '798' : ['Exception during asm, db snmp password command execution'],
    '799' : ['EM cluster details execution failed'],
    '801' : ['Failed to delete VMs'],
    '802' : ['Cell Operation Failed'],
    '803' : ['Scan Name not provided in the XML'],
    '804' : ['Bonding operation failed'],
    '805' : ['network_update failed'],
    '806' : ['Remote lock failed'],
    '807' : ['SSH test failed'],
    '808' : ['Reshape precheck failed'],
    '809' : ['Node subset precheck failed'],
    '810' : ['Keys copy to VM failed'],
    '811' : ['Error on ExaScale'],
    '812' : ['Invalid system version'],
    '813' : ['EXAVMIMAGES not loaded on dom0'],
    '814' : ['Failed to compute free space on /EXAVMIMAGES partition'],
    '815' : ['SOP operation failure'],
    '816' : ['NAT VIP resolution failed'],
    '817' : ['Exacloud Error on ExaScale/EDV/Exacompute Configuration'],
    '818' : ['Failed to Upload object to the object storage'],
    '819' : ['DBCS agent File Copy Failed'],
    '820' : ['Certificate copy to domU failed'],
    '821' : ['Certificate copy to dom0 failed'],
    '822' : ['VMBackup utility is not installed'],
    '823' : ['No available backups for VMBackup restore'],
    '824' : ['GI Image configuration failed'],
    '825' : ['GPG Keys copy failed'],
    '826' : ['DomU version not compatible with 23ai'],
    '827' : ['Backup of file failed.']
}

gResError = {
    '0'   : ['Command successful'],
    '800' : ['Failed to ping target node/cell'],
    '801' : ['Failed to connect to target node/cell'],
    '802' : ['Error running cellcli command on target cell'],
    '803' : ['List of database instances varies across cells'],
    '804' : ['Error reading list of database instances from cells'],
    '805' : ['Failed to parse flash cache size from cellcli output'],
    '806' : ['Size of flash cache varies across cells'],
    '807' : ['Error reading flash cache size from cells'],
    '808' : ['Missing input JSON object'],
    '809' : ['objective key not found in input JSON object'],
    '810' : ['Invalid value specified for objective in input JSON object'],
    '811' : ['IORM objective varies across cells'],
    '812' : ['Error reading IORM objective from cells'],
    '813' : ['Failed to parse IORM objective from cellcli output'],
    '814' : ['DBPlan not found in input JSON object'],
    '815' : ['Key:dbname not found in DBPlan list'],
    '816' : ['Key:share not found in DBPlan list'],
    '817' : ['DB instance not found on the cells'],
    '818' : ['DB share not a valid number'],
    '819' : ['DB share not within valid range'],
    '820' : ['Failed to parse IORM Db Plan from cellcli output'],
    '821' : ['Failed to restart cell services'],
    '822' : ['user key not found in input JSON'],
    '823' : ['password key not found in input JSON'],
    '824' : ['role key not found in input JSON'],
    '825' : ['Could not retrieve cell disks info'],
    '826' : ['Cell status warning'],
    '827' : ['IORM DB Plan varies across cells'],
    '828' : ['IORM Cluster Plan varies across cells'],
    '829' : ['Failed to parse pmem cache size from cellcli output'],
    '830' : ['clusterPlan not found in input JSON object'],
    '831' : ['Key:name not found in ClusterPlan list'],
    '832' : ['Key:share not found in ClusterPlan list'],
    '833' : ['Cluster share not a valid number'],
    '834' : ['Cluster share not within valid range'],
    '835' : ['Size of pmem cache varies across cells'],
    '836' : ['Error reading pmem cache size from cells'],
    '837' : ['Exception during view or updation of exabox.conf'],
    '838' : ['Exception during NFTable Addition'],
    '839' : ['Pmemcache not configured or enabled on cell'],
    '847' : ['Cell validation Node test failed'],
    '848' : ['Cellcli alert(Unresolved)'],
    '849' : ['Cellsrv no response: failed to query Cellcli alert'],
    '850' : ['Cell disk error'],
    '851' : ['Unsupported IORM option'],
    '852' : ['Unsupported User config option']
}

gSparseError = {
    '0'  : ['No error'],
    '851': ['Missing input JSON object'],
    '852': ['Source DB name missing in input'],
    '853': ['Testmaster DB name missing in input JSON object'],
    '854': ['Error reading Source DB name from cells'],
    '855': ['Source DB name not found among installed DBs on cells'],
    '856': ['DB with same name already exists. Testmaster cannot be created'],
    '857': ['Failed to ping domU'],
    '858': ['Failed to connect to domU'],
    '859': ['Error running dbaasapi on target domU'],
    '860': ['Source DB password missing in input JSON object'],
    '861': ['Testmaster creation job could not be launched'],
    '862': ['Jobid not specified or invalid jobid'],
    '863': ['Unable to fetch status of job'],
    '864': ['Prepare step for testmaster failed'],
    '865': ['Create step for testmaster failed'],
    '866': ['Finalize step for testmaster failed'],
    '867': ['Snapshot clone name missing in input'],
    '868': ['Testmaster DB name not found among installed DBs on cells'],
    '869': ['DB with same name already exists. Snapclone cannot be created'],
    '870': ['Delete operation for testmaster/snapclone failed'],
    '871': ['Database Info Fetch operation failed'],
    '872': ["Invalid invocation or unsupported Sparse Clone option"],
    '873': ['Could not update ASM local_listener']
}

gDbaasError = {
    '0'  : ['No error'],
    '901': ['Missing input JSON object'],
    '902': ['Failed to ping domU'],
    '903': ['Failed to connect to domU'],
    '904': ['Error running dbaasapi on target domU'],
    '911': ['Database Info Fetch operation failed']
}

gPatchError = {
    '1000': {'error': 'Unable to select a dom0 to run the patchmgr',
             'suggestion': ['2001','2002','2003', '2004']},
    '1001': {'error': 'Patchmgr execution error. Exit code is not 0',
             'suggestion': ['2000']},
    '1002': {'error': 'Not all the DomUs are up',
             'suggestion': ['2005']},
    '1003': {'error': 'DB services are not up',
             'suggestion': ['2006']},
    '1004': {'error': 'Not all the DomUs have a heartbeat to all the cells',
             'suggestion': ['2007']},
    '1005': {'error': 'Cell clean up execution failed',
             'suggestion': ['2008']},
    '1006': {'error': 'Unable to ping/ssh node',
             'suggestion': ['2004']},
    '1007': {'error': 'Unexpected target image version',
             'suggestion': ['2009']},
    '1008': {'error': 'Image status is not successful',
             'suggestion': ['2009', '2010']},
    '1009': {'error': 'Cell services are not up',
             'suggestion': ['2011']},
    '1010': {'error': 'Unexpected target firmware version',
             'suggestion': ['2012']},
    '1011': {'error': 'SM state is not as before the upgrade/downgrade',
             'suggestion': ['2013']},
    '1012': {'error': 'Changes detected done to the DOMU after last DOM0 upgrade. Rollback of DOM0 not allowed.',
             'suggestion': ['2014']},
    '1013': {'error': 'Output from commands changed after upgrade or rollback: (1) smnodes list (2) smpartition list active no-page',
             'suggestion': ['2015']},
    '1014': {'error': 'asmdeactivationoutcome is not Yes',
             'suggestion': ['2016']},
    '1015': {'error': 'Required services are not running on the upgraded node',
             'suggestion': ['2017']},
    '1016': {'error': 'Post exacloud plugins failed for upgraded node',
             'suggestion': ['2022']},
    '1017': {'error': 'The Rack node images are up to date',
             'suggestion': ['2018']},
    '1018': {'error': 'Patchmgr session is already active on this cluster',
             'suggestion': ['2019']},
    '1019': {'error': 'Ksplice plugin failed to apply.',
             'suggestion': ['2020']},
    '1020': {'error': 'One-off patch failed to apply.',
             'suggestion': ['2021']},
    '1021': {'error': 'Unable to locate patch stage location in OCI EXACC environment.',
             'suggestion': ['2023']},
    '1999': {'error': 'Error not available',
             'suggestion': ['2999']}
}

gPatchSuggestion = {
    '2000': 'Look at patchmgr.stdout|stderr as well as the screen output to find the error',
    '2001': 'At least 10GB free space is needed in /EXAVMIMAGES on DOM0. You may need to delete some '\
            'files in the target environment',
    '2002': 'Unable to copy/unzip file. Manually unzip the file in the target node',
    '2003': 'Patchmgr not found. Trye same operation with a different patch zip file',
    '2004': 'Node is not pingable. Request support to address the network problem',
    '2005': 'Attempt to start the DomUs \'vm create /EXAVMIMAGES/GuestImages/<domu_name>\'. '\
             'Check the console output for the DomU to try to find the problem',
    '2006': 'Examine the Database, ASM and Grid Infrastructure alert log to try to identify the problem',
    '2007': 'Check if the DomUs that do not have heartbeat to the cell are up and the ASM instances in each are up',
    '2008': 'Retry the original patch operation. If the issue persists, then expect the issue to be addressed in '\
             'the next patch operation',
    '2009': 'Examine /var/log/cellos/validations.log and /var/log/cellos/vldrun* files and then any '\
            '/var/log/cellos/validations/* files for failures. After resolving the problems, reboot the node and then '\
            'check the status using imageinfo command. If the status continues to be failure, then request help '\
            'from support',
    '2010': 'A failed validation seen in valdations.log and vldrun.log will indicate the cause for image'\
            ' status failure',
    '2011': 'Examine $CELLTRACE and $LOG_HOME log and trc files to identify the problem. '\
             'Look at $CELLTRACE/ms-odl.log|trc files as starting point',
    '2012': 'Contact support for help',
    '2013': 'If SM was enabled before the patch, then try to enable it.',
    '2014': 'Retry after delete service.',
    '2015': 'If this change is expected, then retry the upgrade or rollback.',
    '2016': 'Check offline ASM disks and bring them online',
    '2017': 'Check critical services are running on the upgraded node',
    '2018': 'No patching action required',
    '2019': 'Monitor and wait for the patchmgr session to complete',
    '2020': 'Validate the input and for presence of all input files and re-run ksplice plugin.',
    '2021': 'Validate the input and for presence of all input files and re-run one-off patch.',
    '2022': 'Verify user post exacloud plugin log for the failure.',
    '2023': 'Specify the actual patch stage location in exabox.conf and retry patch.',
    '2999': 'No suggestion available'
}

gBDCSError = {
    '3001': 'Parameter "dbsid" is mandatory',
    '3002': 'Parameter "vmid" is mandatory',
    '3003': 'Parameter "save-spec" is mandatory',
    '3004': 'BDCS installation tool is not available',
    '3005': 'BDCS installation failed',
    '2999': 'Error not available'
}

gDiskgroupError = {
    'InvalidOp'           : ('4001', "Invalid diskgroup operation command"),
    'UnsupportedOption'   : ('4002', "Unsupported option for the given diskgroup operation command"),
    'MissingArgs'         : ('4003', "Mandatory arg(s) for diskgroup operation missing"),
    'MissingInputPayload' : ('4004', "Input payload JSON is not available or readable"),
    'MissingDiskgroupType': ('4005', "Input payload JSON does not have value for diskgroup_type parameter"),
    'MissingDiskgroupName': ('4006', "Input payload JSON does not have value for diskgroup_name parameter"),
    'MissingDiskgroupSize': ('4007', "Input payload JSON does not have value for new_size parameter"),
    'DgAlreadyExists'     : ('4008', "A Diskgroup with specified name already exists for this cluster; Cannot create another"),
    'DgDoesNotExist'      : ('4009', "Specified Diskgroup does not exist on this cluster"),
    'NullOutputPayload'   : ('4010', "The output payload body is NULL"),
    'MissingPropDict'     : ('4011', "The output payload did not have details of the specified diskgroup"),
    'MissingStorPropDict' : ('4012', "The output payload did not have details of the specified diskgroup"),
    'MissingReblPropDict' : ('4013', "The output payload did not have details of the specified diskgroup"),
    'MissingFgrpPropDict' : ('4014', "The output payload did not have details of the specified diskgroup"),
    'MissingStorProp'     : ('4015', "The output payload did not have details of the specified diskgroup"),
    'MissingReblProp'     : ('4016', "The output payload did not have details of the specified diskgroup"),
    'MissingFgrpProp'     : ('4017', "The output payload did not have details of the specified diskgroup"),
    'NonModifiable'       : ('4018', "Entity in question cannot be modified"),
    'ErrorFetchingDetails': ('4019', "There was an error in fetching details of the given entity"),
    'InvalidPropValue'    : ('4020', "Invalid value for queried property"),
    'ErrorReadingPayload' : ('4021', "Error handling or reading the output payload from a previous operation"),
    'GDResizeFailed'      : ('4022', "Error resizing specified griddisk on given cell"),
    'GDCreateFailed'      : ('4023', "Error creating specified griddisk on given cell"),
    'GDDropFailed'        : ('4024', "Error dropping specified griddisk on given cell"),
    'GDCountMismatch'     : ('4025', "Griddisk count mismatch across diskgroups"),
    'NullPropertyValue'   : ('4031', "No value for the specified property found"),
    'InvalidArgs'         : ('4032', "Incorrect functions arguments"),
    'UpdateError'         : ('4033', "Could not update/modify object in question"),
    'DgOperationError'    : ('4034', "Diskgroup action failed"),
    'InvalidState'        : ('4035', "Invalid object state"),
    'MissingStorageOldSize': ('4036', "Input payload JSON does not have value for old size storage parameter"),
    'MissingStorageNewSize': ('4037', "Input payload JSON does not have value for new size storage parameter"),
    'DgSizeChangeNotPermitted': ('4038', "Disk Groups Size Change Not Permitted"),
    'DbaasApiFail': ('4039', "Dbaas API failed with internal error. Operation failed"),
    'DiskGroupLCMInvocationError': ('4040', "Invalid invocation or unsupported DiskGroup LCM option"),
    'DbaasObjJobIDReadFail': ('4041', "Dbaas obj Failed to read Job ID from domU"),
    'InvalidResize': ('4042', "Resize will lead to loss of DATA/RECO (or SPARSE) diskgroup")
}

gBMCError = {
    'NO_ERROR' : ('0', 'No Errors'),
    'MISMATCHED_JSONS' : ('5001', 'Mismatched Token and Input Jsons'),
    'INCOMPATIBLE_OEDA' : ('5002', 'Incompatible OEDA version'),
    'INVALID_CMD' : ('5003', 'Invalid Command'),
    'UNSUPPORTED_ALTER_METHOD' : ('5004', 'XML Alter Method not supported'),
    'INVALID_OEDA_PATH' : ('5005', 'Invalid OEDACLI path'),
    'XML_PROCESSING_ERROR' : ('5006', 'Error in processing XML by OEDA'),
    'MISSING_TOKEN_JSON' : ('5007', 'Token JSON not found'),
    'MISSING_TEMPLATE_XML' : ('5008', 'Template XML not found'),
    'XML_LOADING_ERROR' : ('5009', 'Error while loading template XML'),
    'OEDACLI_LOG_CONTAINS_ERRORS': ('5010', 'OEDACLI log has errors'),
    'DOMU_LOOKUP_FAILED': ('5011', 'DomU not found for given Dom0'),
    'INVALID_JSON_CONTENT' : ('5012', 'Invalid JSON Content'),
    'EXCEPTION' : ('5098', 'Caught Exception, check bmcctrl log'),
    'UNKNOWN_ERROR' : ('5099', 'Unknown Error')
}

gPartitionError = {
    'InvalidOp'              : ('6001', "Invalid partition operation command"),
    'UnsupportedOption'      : ('6002', "Unsupported option for the given partition operation command"),
    'MissingArgs'            : ('6003', "Mandatory arg(s) for partition operation missing"),
    'MissingInputPayload'    : ('6004', "Input payload JSON is not available or readable"),
    'MissingPartitionSize'   : ('6007', "Input payload JSON does not have value for new_size parameter"),
    'PartitionDoesNotExist'  : ('6009', "Specified partition does not exist on this cluster"),
    'ErrorRunningRemoteCmd'  : ('6017', "Error running specified command on given host"),
    'NonModifiable'          : ('6018', "Entity in question cannot be modified"),
    'ErrorFetchingDetails'   : ('6019', "There was an error in fetching details of the given entity"),
    'PartitionResizeFailed'  : ('6022', "Error resizing specified partition on given node"),
    'ImageResizeFailed'      : ('6023', "Error resizing specified block device image on given node"),
    'LoopDeviceErr'          : ('6024', "Error modifying specified loop device on given node"),
    'InvalidArgs'            : ('6032', "Incorrect functions arguments"),
    'UpdateError'            : ('6033', "Could not update/modify object in question"),
    'PartitionOperationError': ('6034', "Partition action failed"),
    'InvalidState'           : ('6035', "Invalid object state")

}

gCellUpdateError = {
    'MissingArgs'            : ('7001', "Mandatory arg(s) for cell update operation missing"),
    'InsufficientArgs'       : ('7002', "Insufficient arg(s) for cell update operation"),
    'BadInputCombination'    : ('7003', "Wrong combination of input arguments"),
    'InvalidInput'           : ('7004', "Invalid input arguments"),
    'PrecheckFailed'         : ('7005', "Precheck Failed"),
    'DiskgroupInfoFailed'    : ('7006', "Fetching Info failed"),
    'CellOperationFailed'    : ('7007', "Cell operation failed"),
    'OperationFailed'        : ('7008', 'Operation failed'),
    'OedaError'              : ('7011', "Exception running oedacli operation")
}

gReconfigError = {
    'InvalidPayload'                    : ('8001', "Invalid reconfig payload. Payload or preprov network missing"),
    'VmShutdownError'                   : ('8002', "Error on Restart the VM on Reconfig"),
    'SoftFailure:'                      : ('8003', "Error on Non SoftFailure execution"),
    'DiferentNetwork'                   : ('8004', "Backup and Client network must be the same network"),
    'InvalidOperation'                  : ('8005', "Operation is not supported"),
    'NetworkReconfigFailed'             : ('8006', "Network reconfiguration operation failed"),
    'RevertNetworkReconfigFailed'       : ('8007', "Revert Network reconfiguration operation failed"),
    'NetworkBondingModificationFailed'  : ('8008', "Network bonding mode change operation failed"),
    'NetworkBondingValidationFailed'    : ('8009', "Network bonding mode validate operation failed")
}
#
#Exacloud Provision Errors
#
gProvError = {
    'ERROR_AHF_INSTALL_FAIL'           : ('0x02000001', 'Failed to install AHF', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_RPM_NOT_FOUND'              : ('0x02000002', 'RPM not found at the given location', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_GDCOUNT_MISMATCH'           : ('0x02000003', 'Griddisk count mismatch across diskgroups', 'RETRYABLE_ERR', 3)
}

gOCIError = {
    'NoOCIConnector'                : ('9001',       "Failed to instantiate an OCI connector.")
}

#
#Exacloud Reshape Error Codes.
#
gReshapeError = {
    'INVALID_INPUT_PARAMETER'         : ('0x02010000', 'Failed due to input arguments missing or not proper', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_FETCHING_DETAILS_DG'       : ('0x02010004', 'Failed to fetch information for diskgroups', 'CRITICAL_NORETRY_ERR', 0),
    'INVALID_SIZE_PROVIDED_DG'        : ('0x02010005', 'Failed with invalid size of diskgroup', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_FETCHING_GRIDDISK_COUNT'   : ('0x02010006', 'Failed to count number of grid disks', 'RETRYABLE_ERR', 3),
    'ERROR_UPDATING_DG'               : ('0x02010007', 'Failed to update diskgroups', 'RETRYABLE_ERR', 3),
    'ERROR_RESIZE_CHECK_FAILED'       : ('0x02010008', 'Failed to perform resizable check for diskgroups', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_FETCHING_NEW_SIZES_DG'     : ('0x02010009', 'Failed to get new sizes of DATA, RECO (and SPARSE) diskgroups', 'RETRYABLE_ERR', 3),
    'ERROR_FETCHING_PARTITION_INFO'   : ('0x0201000A', 'Failed to fetch fdisk information for partition', 'RETRYABLE_ERR', 3),
    'ERROR_READING_DISKSIZE'          : ('0x0201000B', 'Failed to read the disk size in bytes for partition', 'RETRYABLE_ERR', 3),
    'ERROR_READING_DEVICE_INFO'       : ('0x0201000C', 'Failed to read device information for partition', 'RETRYABLE_ERR', 3),
    'ERROR_FETCHING_DEVICE_SIZE'      : ('0x0201000D', 'Failed to retrieve device size for partition', 'RETRYABLE_ERR', 3),
    'ERROR_INCONSISTENT_DOM0_SIZE'    : ('0x0201000E', 'Failed with inconsistent size on VM Host', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_USAGE_SIZE_MORE'           : ('0x0201000F', 'Failed to resize as available space is smaller than current utilisation', 'PAYLOAD_ERR', 0),
    'ERROR_LESS_FREE_SPACE'           : ('0x02010010', 'Failed to modify as minimum free space requirement is not met', 'PAYLOAD_ERR', 0),
    'ERROR_IMG_FILE_CHECK_FAILED'     : ('0x02010011', 'Failed to perform ImageFile check', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_RESIZE_NOT_PROPER'         : ('0x02010012', 'Failed to properly resized image on VM', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_FILE_SYS_CHECK_FAILED'     : ('0x02010013', 'Failed to perform filesystem check', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_MOUNTING_FILE_SYS'         : ('0x02010014', 'Failed to mount filesystem', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_UNMOUNTING_FILE_SYS'       : ('0x02010015', 'Failed to unmount filesystem', 'RETRYABLE_ERR', 3),
    'ERROR_FETCHING_CRS_PATH'         : ('0x02010016', 'Failed to fetch cluster control binary path', 'RETRYABLE_ERR', 3),
    'ERROR_TFA_STOP'                  : ('0x02010017', 'Failed to stop TFA services on VM', 'RETRYABLE_ERR', 3),
    'ERROR_CRS_STOP'                  : ('0x02010018', 'Failed to stop cluster services on VM', 'RETRYABLE_ERR', 3),
    'ERROR_LVRESIZE_FAIL'             : ('0x02010019', 'Failed lvresize command in VM', 'RETRYABLE_ERR', 3),
    'ERROR_PVRESIZE_FAIL'             : ('0x0201001A', 'Failed pvresize command in VM', 'RETRYABLE_ERR', 3),
    'ERROR_PARTED_CMD_FAIL'           : ('0x0201001B', 'Failed to execute Parted command in VM', 'RETRYABLE_ERR', 3),
    'ERROR_IMAGE_CFG_MISSING'         : ('0x0201001C', 'Failed due to image configuration file missing for VM', 'CRITICAL_NORETRY_ERR', 0),
    'INVALID_SIZE_PROVIDED'           : ('0x0201001D', 'Failed as new size is not enough for hypervisor to perform the operation', 'PAYLOAD_ERR', 0),
    'ERROR_VM_MEMORY_RESIZE_MISMATCH' : ('0x0201001E', 'Failed to perform memory update', 'RETRYABLE_ERR', 3),
    'ERROR_VCPU_NOT_APPLIED'          : ('0x0201001F', 'Failed to apply VCPU to running VM', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_MAX_CPU_LESS'              : ('0x02010020', 'Failed as Max VCPU is lower than new number of cores requested', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_FETCHING_VCPUS_ALLOC'      : ('0x02010021', 'Failed to retrieve VCPUS allocation for VM', 'RETRYABLE_ERR', 3),
    'INVALID_ALLOC_SIZE'              : ('0x02010022', 'Failed as number of cores is more than the maximum allowed value for VM', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_VM_RESIZE_UPDATE_FAIL'     : ('0x02010023', 'Failed to update VM cores', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_STORAGE_RESIZE_FAIL'       : ('0x02010024', 'Failed to resize storage', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_REBALANCE_FAILED'          : ('0x02010025', 'Failed to complete rebalance', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_POST_ASM_RESIZE'           : ('0x02010026', 'Failed to validate the size of a Diskgroup post resize', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_RESIZE_GRIDDISK'           : ('0x02010027', 'Failed to resize grid disks', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_SHUTDOWN_FAILED'           : ('0x02010028', 'Failed to shutdown VM', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_REBOOT_FAILED'             : ('0x02010029', 'Failed to reboot VM', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_DB_START'                  : ('0x0201002A', 'Failed to start database on VM', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_CRS_START'                 : ('0x0201002B', 'Failed to start cluster services on VM', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_IMAGE_RESIZE'              : ('0x0201002C', 'Failed to resize image on host', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_VCPU_OVERSUBSCRIBED'       : ('0x0201002D', 'Failed due to vCPUs over subscribed', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_VCPU_INSUFFICIENT'         : ('0x0201002E', 'Failed as domain cores are insufficient for allocation', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_VCPU_RESIZE_FAILED'        : ('0x0201002F', 'Failed to resize vcpu due to vm_maker failure', 'RETRYABLE_ERR', 0),
    'ERROR_VM_NOT_RUNNING'            : ('0x02010030', 'Failed as VM is expected to be running', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_VMID_NOT_VALID'            : ('0x02010031', 'Failed as vmid is not valid', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_PING_FAILURE'              : ('0x02010032', 'Failed as unable to ping the node', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_VMID_MISSING'              : ('0x02010033', 'Failed due to missing vmid', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_VM_IS_RUNNING'             : ('0x02010034', 'Failed as VM is already in running state', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_VM_OP_FAILURE'             : ('0x02010035', 'Failed due to VM operation failure', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_SSH_FAILURE'               : ('0x02010036', 'Failed as no SSH connection to server', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_RESHAPE_PRECHECK'          : ('0x02010037', 'Failed in reshape precheck', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_VM_CPU_RESIZE_PINGABLE'    : ('0x02010038', 'Failed to resize CPU as none of the Dom0s are pingable', 'CRITICAL_NORETRY_ERR', 3),
    'ERROR_DBS_NOT_RUNNING'           : ('0x0201003A', 'Failed to resize as not all earlier running DB instances are running on the VM after reboot. Continuing to resize can lead to service outage', 'RETRYABLE_ERR', 3),
    'ERROR_AUTOSTART_PARAM_SETTING'   : ('0x0201003B', 'Failed to change autostart parameter state', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_VM_NOT_CONNECTABLE'        : ('0x0201003C', 'Failed to SSH to VM', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_KEYAPI_FAIL'               : ('0x0201003D', 'Failed to run keyapi command in VM', 'RETRYABLE_ERR', 3),
    'ERROR_FSRESIZE_FAIL'             : ('0x0201003D', 'Failed fs resize command in VM', 'RETRYABLE_ERR', 3),
    'ERROR_LUKSRESIZE_FAIL'           : ('0x0201003E', 'Failed cryptsetup resize command in VM', 'RETRYABLE_ERR', 3),
    'ERROR_HUGEPAGE_UPDATE_FAIL'      : ('0x0201003F', 'Failed to update hugepage setting in VM', 'RETRYABLE_ERR', 3)
}

gPartialError = {
    'ERROR_VM_CPU_RESIZE_PARTIAL'     : ('0x02FF0000', 'Failed to resize CPU on all VMs. VM CPU core count will be partially updated', 'RETRYABLE_ERR', 3)
}
#
#Exacloud Elastic Error Codes.
#
gElasticError = {

    'INVALID_INPUT_PARAMETER'         : ('0x02020000', 'Failed due to input arguments missing or not proper', 'CRITICAL_NORETRY_ERR', 0),
    'CELL_PRECHECK_FAILED'            : ('0x02020001', 'Failed as grid disks already created before cloning cell', 'CRITICAL_NORETRY_ERR', 0),
    'CELL_DG_REBALANCE_INFO_FAILED'   : ('0x02020002', 'Failed to fetch rebalance status of the Diskgroup(s)', 'RETRYABLE_ERR', 3),
    'CELL_DG_METADATA_FETCH_FAILED'   : ('0x02020003', 'Failed to fetch and save Diskgroup metadata', 'RETRYABLE_ERR', 3),
    'CELL_CLONING_FAILED'             : ('0x02020004', 'Failed to perform cloning operation on the cell', 'RETRYABLE_ERR', 3),
    'CELL_DG_RESIZE_CALC_FAILED'      : ('0x02020005', 'Failed to calculate the resize values for diskgroup(s)', 'RETRYABLE_ERR', 3),
    'CELL_DG_SHRINK_FAILED'           : ('0x02020006', 'Failed to shrink the diskgroup(s)', 'RETRYABLE_ERR', 3),
    'CELL_OEDA_DEL_CMD_FAILED'        : ('0x02020007', 'Failed to delete cell using Oedacli', 'RETRYABLE_ERR', 3),
    'CELL_OEDA_ADD_CMD_FAILED'        : ('0x02020008', 'Failed to add cell using Oedacli', 'RETRYABLE_ERR', 3),
    'CELL_DG_INFO_FETCH_FAILED'       : ('0x02020009', 'Failed to fetch info for diskgroup', 'RETRYABLE_ERR', 3),
    'CELL_DG_RESIZE_OPS_FAILED'       : ('0x0202000A', 'Failed to complete resize operation for diskgroup', 'RETRYABLE_ERR', 3),
    'CELL_DG_REBAL_POWER_SET_FAILED'  : ('0x0202000B', 'Failed to set new rebalance power for diskgroup', 'RETRYABLE_ERR', 3),
    'CELL_BAD_INPUT_COMBINATION'      : ('0x0202000C', 'Failed to reshape as add and remove cell not allowed in single operation', 'CRITICAL_NORETRY_ERR', 0),
    'CELL_STATUS_NOT_NORMAL'          : ('0x0202000D', 'Failed as Cell services are not up', 'CRITICAL_NORETRY_ERR', 0),
    'CELL_GD_SHRINK_FAILED'           : ('0x0202000E', 'Failed to shrinkg the griddisks', 'RETRYABLE_ERR', 3)
    
}

#
#Exacloud Node Elastic/Subset Error Codes.
#
gNodeElasticError = {
    
    'INVALID_INPUT_PARAMETER'          : ('0x02030000', 'Failed due to input arguments missing or not proper', 'CRITICAL_NORETRY_ERR', 0),
    'COMPUTE_NODE_SRC_DOM0_MISSING'    : ('0x02030001', 'Failed to find src Dom0 for added_computes', 'CRITICAL_NORETRY_ERR', 0),
    'COMPUTE_NODE_MISSING_FRM_PAYLOAD' : ('0x02030002', 'Failed to find DomU/DomUs??for the removed_computes node in json payload', 'CRITICAL_NORETRY_ERR', 0),
    'RESHAPE_CONFIG_MISSING'           : ('0x02030003', 'Failed as??Reshape config is None', 'CRITICAL_NORETRY_ERR', 0),
    'ELASTIC_INFO_CMD_FAILED'          : ('0x02030004', 'Failed in elastic info flow', 'CRITICAL_NORETRY_ERR', 0),
    'NO_ACTIVE_NODE'                   : ('0x02030005', 'Failed due to no active node in the cluster', 'RETRYABLE_ERR', 3),
    'RESHAPE_FAILED_SINGLE_OPERATION'  : ('0x02030006', 'Failed to reshape service json payload as add and remove node not allowed in single operation', 'RETRYABLE_ERR', 3),
    'COMP_NODE_CNT_ZERO'               : ('0x02030007', 'Failed as participating computes nodes count should be greater than zero', 'CRITICAL_NORETRY_ERR', 0),
    'RESHAPE_VALIDATION_FAILED'        : ('0x02030008', 'Failed to validate??reshape service json payload', 'CRITICAL_NORETRY_ERR', 0),
    'NO_SUITABLE_FIRST_BOOT_IMG'       : ('0x02030009', 'Failed to find suitable System first boot Image. Aborting', 'CRITICAL_NORETRY_ERR', 0),
    'FETCH_TIMEZONE_FAILED'            : ('0x0203000A', 'Failed to fetch timezone from domU', 'RETRYABLE_ERR', 3),
    'STALE_ENTRY_EXIST'                : ('0x0203000B', 'Failed to cleanup stale entries of VM from clusterware', 'RETRYABLE_ERR', 3),
    'DB_INSTANCE_RUNNING_FAILURE'      : ('0x0203000C', 'Failed as DB Instance is running on single node, retry with force option enabled', 'RETRYABLE_ERR', 3),
    'DB_INST_NOT_REMOVED'              : ('0x0203000D', 'Failed to remove DB instances', 'RETRYABLE_ERR', 3),
    'NODE_SET_WRONG'                   : ('0x0203000E', 'Failed as cluster does not contain the correct set of nodes', 'CRITICAL_NORETRY_ERR', 0),
    'DB_INFO_FAILED'                   : ('0x0203000F', 'Failed to get dbinfo', 'RETRYABLE_ERR', 3),
    'DEL_VM_FAILED'                    : ('0x02030010', 'Failed to delete VM', 'RETRYABLE_ERR', 3),
    'DEL_CLUSTER_NODE_FAILED'          : ('0x02030011', 'Failed to execute oedacli: delete cluster nodes', 'RETRYABLE_ERR', 3),
    'INVALID_RESHAPE_ACTION'           : ('0x02030012', 'Failed due to invalid reshape service action', 'CRITICAL_NORETRY_ERR', 0),
    'FAILED_NO_OP_PARAMS'              : ('0x02030013', 'Failed as operation with sent parameters is a No-OP', 'CRITICAL_NORETRY_ERR', 0),
    'LISTENER_SERVICE_NOT_RUNNING'     : ('0x02030014', 'Failed as listener service for ASM in VMs are not running', 'RETRYABLE_ERR', 3),
    'FAILED_REMOVE_DBHOME'             : ('0x02030015', 'Failed during running of oedacli step to remove DBHomes', 'RETRYABLE_ERR', 3),
    'FAILED_REMOVE_CLUSTER_NODE'       : ('0x02030016', 'Failed during Running of oedacli step to remove cluster node', 'RETRYABLE_ERR', 3),
    'FAILED_REMOVE_DSK_IMG'            : ('0x02030017', 'Failed to force remove of the vm disk image failed', 'RETRYABLE_ERR', 3),
    'FAILED_REMOVE_VM_FRM_DIR'         : ('0x02030018', 'Failed to delete VM files from the VM directory in /EXAVMIMAGES/GuestImages/', 'RETRYABLE_ERR', 3),
    'INCORRECT_VIP_CONFIGURATION'      : ('0x02030019', 'Incorrect VIP configuration in the cluster', 'RETRYABLE_ERR', 3),
    'OEDAADDKEY_HOST_CMD_FAILED'       : ('0x0203001A', 'Failed to generate ssh keys', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_NODE_SUBSET_PRECHECK'       : ('0x0203001B', 'Failed in node subset precheck', 'CRITICAL_NORETRY_ERR', 0),
    'ADD_NODE_FAILED'                  : ('0x0203001C', 'Failed to execute oedacli: clone guest', 'RETRYABLE_ERR', 3),
    'ERROR_KEYS_COPY'                  : ('0x0203001D', 'Failed to copy keys to VM', 'RETRYABLE_ERR', 3),
    'FAILED_DOMU_XML_PATCHING'         : ('0x0203001E', 'Failed to Patch source DomU XML with DNS and NTP server info', 'CRITICAL_NORETRY_ERR', 0),
}

#
# Exacloud Network Error Codes.
#
gNetworkError = {
    'OPERATION_SUCCESSFUL'                  : ('0x00000000', 'Operation successful', '', 0),
    'INVALID_INPUT_PARAMETER'               : ('0x02040000', 'Failed due to input payload missing or not proper', 'CRITICAL_NORETRY_ERR', 0),
    'INVALID_OPERATION'                     : ('0x02040001', 'This action is supported only for OCI EXACC environment', 'CRITICAL_NORETRY_ERR', 0),
    'INVALID_RECONFIG_OPERATION'            : ('0x02040002', 'Invalid network reconfiguration operation', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_RECONFIGURATION_FAILED'          : ('0x02040003', 'Network reconfiguration operation failed', 'RETRYABLE_ERR', 3),
    'ERROR_REBOOT_FAILED'                   : ('0x02040004', 'Failed to reboot the Guest VM', 'RETRYABLE_ERR', 3),
    'ERROR_STALE_BRIDGE_DELETE_FAILED'      : ('0x02040005', 'Failed to delete stale bridge', 'RETRYABLE_ERR', 3),
    'ERROR_RECONFIGURATION_REVERT_FAILED'   : ('0x02040006', 'Network reconfiguration revert operation failed', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_BONDING_MODIFICATION_FAILED'     : ('0x02040007', 'Network bonding mode change operation failed', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_BONDING_VALIDATION_FAILED'       : ('0x02040008', 'Network bonding mode validate operation failed', 'RETRYABLE_ERR', 3),
    'ERROR_UPLOAD_FAILED'                   : ('0x02040009', 'Failed to upload to object storage', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_ACCELERATEDNETWORK_INCAPABLE_DOM0' : ('0x02040010', 'Dom0 is not capable of supporting accelaratedNetwork feature', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_FEATURE_NOT_ENABLED'             : ('0x02040011', 'Feature is not enabled', 'CRITICAL_NORETRY_ERR', 0)
}

#
# Exacloud Network Error Codes.
#
gExascaleError = {
    'OPERATION_SUCCESSFUL'                  : ('0x00000000', 'Operation successful', '', 0),
    'INVALID_INPUT_PARAMETER'               : ('0x02060000', 'Failed due to input payload missing or not proper', 'CRITICAL_NORETRY_ERR', 0),
    'ERROR_XS_DISABLED'                     : ('0x02060001', 'Failed as Exascale Service is disabled', 'CRITICAL_NORETRY_ERR', 0),
    'INVALID_EXASCALE_OPERATION'            : ('0x02060002', 'Failed due to invalid Exascale operation', 'CRITICAL_NORETRY_ERR', 0),
    'VAULT_CREATION_FAILED'                 : ('0x02060003', 'DB Vault creation operation failed', 'CRITICAL_NORETRY_ERR', 0),
    'VAULT_DELETION_FAILED'                 : ('0x02060004', 'DB Vault deletion operation failed', 'CRITICAL_NORETRY_ERR', 0),
    'VAULT_GET_SIZE_FAILED'                 : ('0x02060005', 'DB Vault size retrieve operation failed', 'CRITICAL_NORETRY_ERR', 0),
    'VAULT_UPDATE_SIZE_FAILED'              : ('0x02060006', 'DB Vault size update operation failed', 'CRITICAL_NORETRY_ERR', 0),
    'ESCLI_PATH_FAILURE'                    : ('0x02060007', 'ESCLI path does not exist', 'CRITICAL_NORETRY_ERR', 0),
    'CONFIG_STRE_FAILED'                    : ('0x02060008', 'Failed to configure the STRE interface', 'CRITICAL_NORETRY_ERR', 0),
    'STORAGEPOOL_RESIZE_FAILED'             : ('0x02060009', 'Storage pool size update operation failed', 'CRITICAL_NORETRY_ERR', 0),
    'GET_CLUSTER_DETAILS_FAILED'            : ('0x0206000A', 'Failed to retrieve Cluster details', 'CRITICAL_NORETRY_ERR', 0),
    'GET_VOLUME_DETAILS_FAILED'             : ('0x0206000B', 'Failed to retrieve Volume details', 'CRITICAL_NORETRY_ERR', 0),
    'ATTACH_ACFS_VOLUME_FAILED'             : ('0x0206000C', 'Failed to attach ACFS volume', 'CRITICAL_NORETRY_ERR', 0),
    'OCDE_INIT_FAILED'                      : ('0x0206000D', 'Failed to initialize cluster using dbaascli', 'CRITICAL_NORETRY_ERR', 0),
    'STORAGEPOOL_GET_DETAILS_FAILED'        : ('0x0206000E', 'Get Storage pool details failed', 'CRITICAL_NORETRY_ERR', 0),
    'SET_VLANID_FAILED'                     : ('0x0206000F', 'Failed to set the VLANID on the elastic cell', 'CRITICAL_NORETRY_ERR', 0)
}

#
# VM move prechecks dictionary
# "ERROR_CODE": ('Error num', 'Error cause', 'Suggestion')
#
gExaDbXSError = {
    "INVALID_PAYLOAD": (
        0x08500,    
        'Missing "{missing_field}" field in ExaScale Payload',
        'Verify the following fields are included in input payload: '
        '{required_fields}'
    ),
    "TARGET_HOST_NOT_REACHABLE": (
        0x08501,
        'Target Dom0 {host} is not connectable.',
        'Verify Exacloud is able to reach the Dom0 with the command '
        '"$EC_HOME/bin/exassh {host}". In case it is not, verify the SSH keys '
        'with "$EC_HOME/bin/exassh {host} -s". Also connect through the ILOM '
        'console and check for any hardware issue with '
        '"dbmcli -e list alerthistory".'
    ),
    "INVALID_IMAGE": (
        0x08502,
        'Could not obtain node type in target Dom0 {host}',
        'Verify the Exadata image is not corrupted. It is possible that you '
        'will need to reimage this host.'
    ),
    "INVALID_NODE_TYPE": (
        0x08503,
        'Bad host type "{type}" in target Dom0 {host}',
        'Verify secure fabric (QinQ) is properly configured in the Dom0 with '
        '"/opt/oracle.SupportTools/switch_to_ovm.sh --qinq", '
        'then restart the host and verify the node type is one of '
        '{valid_types}'
    ),
    "INVALID_HYPERVISOR": (
        0x08504,    
        'Could not obtain the VMs registered in {host}',
        'Verify libvirt services are running, Exadata image is not corrupted '
        'and that there are no critical alerts in the host with: '
        '"dbmcli -e list alerthistory". It is possible that you will need to '
        'reimage this host.'
    ),
    "VM_ALREADY_MOVED": (
        0x08505,
        'VM {vm} is already registered in target Dom0 {host}',
        'Abort immediately this move operation.'
    ),
    "EDV_SERVICES_OFFLINE": (
        0x08506,
        'EDV services are not online on {host}',
        'Verify the RoCE IPs for stre0 & stre1 interfaces are configured in '
        'the host and are correct. If not, you might need to run this command '
        'in the host: "/opt/exadata_ovm/vm_maker --set --storage-vlan <VLAN> '
        '--ip <IP> --netmask <NETMASK IP>"'
    ),
    "STALE_VM_FILES": (
        0x08507,
        'Target Dom0 {host} has residual VM files for {stale_vm_files}',
        'Verify /EXAVMIMAGES/GuestImages directory contains only one '
        'directory corresponding to each VM registered in the host shown in '
        '"virsh list --all" If that is not the case, verify that these files '
        'are not stale EDVs or stale mountpoints. Make sure these are removed '
        'from /etc/fstab. If you still need these files, please move them '
        'away from GuestImages directory, otherwise simply remove them before '
        'proceeding.'
    ),
    "BROKEN_EDV": (
        0x08508,
        'Could not get bridge files for VM {vm} in target Dom0 {host}',
        'In target Dom0 run "virsh domblklist {vm}" and verify the health '
        'status of all the shown EDVs with the help from Exacompute team. '
        'If the VM corresponds to a cluster that is already terminated, then '
        'simply undefine it with "virsh undefine {vm}" and remove the GCV EDV '
        'mountpoint from the host and /etc/fstab file in the host.'
    ),
    "INVALID_XML": (
        0x08509,
        'Could not get GCV EDV name for VM {vm} in cluster XML',
        'Review the Exacloud cluster XML received from ECRA and validate '
        'the EDVs names are correct for each VM. You might need to manually '
        'fix the XML and ingest it back to ECRA DB before retrying.'
    ),
    "STALE_EDV": (
        0x08510,
        'EDV {edv} is already present in target Dom0 {host}',
        'Contact Oracle Support and Exacompute team to check if the workflow '
        'might break by this. Once the {edv} descriptor is removed from the '
        'host, retry the workflow.'
    ),
    "STALE_BRIDGES": (
        0x08511,
        'Found stale bridges {stale_bridges} on target Dom0 {host}',
        'Remove the stale bridges with: "vm_maker --remove-bridge <BRIDGE>" '
        'before proceeding.'
    ),
    "DUPLICATE_NAT_VLAN": (
        0x08512,
        'NAT VLAN {vlan} is already used by other guest in target Dom0 {host}',
        'Verify the IP address of {bridge}, get the cluster which corresponds '
        'to that DomU IP and verify with ECRA why the same VLAN was picked. '
        'It is recommended to abort this VM move until the ECRA metada issue '
        'is resolved.'
    ),
    "BONDING_NOT_SETUP": (
        0x08513,
        'Bonding is not setup in target Dom0 {host}',
        'If the host was reimaged, please setup bonding again for it.'
    ),
    "BROKEN_GCV": (
        0x08514,
        'VM {vm} GCV EDV has missing files in source host {host}',
        'Verify the EDV is mounted in the source Dom0 {host} with '
        '"df /EXAVMIMAGES/GuestImages/{vm}", if it is not mounted, try '
        'manually mounting it and retry. If the EDV is already mounted, try '
        'restoring a backup of the GCV for this VM before moving this VM.'
    ),
    "LIVE_PRECHECK": (
        0x08515,
        'Live migration pre-checks failed using vm_maker --precheck-live-migrate-domain.',
        'Details error message is included in Exacloud trace file.'
    )
}


def get_dictkey(_error_code) :

    if _error_code >= G_SUB_ERROR_RANGE_START  and  _error_code <= G_SUB_ERROR_RANGE_END :
        return  "gSubError"
    if _error_code >= G_RES_ERROR_RANGE_START and  _error_code <= G_RES_ERROR_RANGE_END :
        return  "gResError"
    if _error_code >= G_SPARSE_ERROR_RANGE_START and  _error_code <= G_SPARSE_ERROR_RANGE_END :
        return  "gSparseError"
    if _error_code >= G_DBASS_ERROR_RANGE_START and  _error_code <= G_DBASS_ERROR_RANGE_END :
        return  "gDbaasError"
    if _error_code >= G_PATCH_ERROR_RANGE_START and  _error_code <= G_PATCH_ERROR_RANGE_END :
        return  "gPatchError"
    if _error_code >= G_PATCH_SUGGESTION_RANGE_START and  _error_code <= G_PATCH_SUGGESTION_RANGE_END :
        return  "gPatchSuggestion"
    if _error_code >= G_BDCS_ERROR_RANGE_START and  _error_code <= G_BDCS_ERROR_RANGE_END :
        return  "gBDCSError"
    if _error_code >= G_DISKGROUP_ERROR_RANGE_START and  _error_code <= G_DISKGROUP_ERROR_RANGE_END :
        return  "gDiskgroupError"
    if _error_code >= G_BMC_ERROR_RANGE_START  and  _error_code <= G_BMC_ERROR_RANGE_END :
        return  "gBMCError"
    if _error_code >= G_PARTITION_ERROR_RANGE_START and  _error_code <= G_PARTITION_RANGE_END :
        return  "gPartitionError"
    if _error_code >= G_CELLUPDATE_ERROR_RANGE_START and  _error_code <= G_CELLUPDATE_ERROR_RANGE_END :
        return  "gCellUpdateError"
    if _error_code >= G_RECONFIGE_ERROR_RANGE_START and  _error_code <= G_RECONFIGE_ERROR_RANGE_END :
        return  "gReconfigError"
    if _error_code >= G_EXASCALE_ERROR_RANGE_START and  _error_code <= G_EXASCALE_ERROR_RANGE_END :
        return  "gExascaleError"
    if _error_code >= G_OCI_ERROR_RANGE_START and  _error_code <= G_OCI_ERROR_RANGE_END :
        return  "gOCIError"

gErrorDict = {
        "gSubError": [gSubError,"errorCodeInKey"],
        "gResError"  :[gResError,"errorCodeInKey"],
        "gSparseError": [gSparseError, "errorCodeInKey"],
        "gDbaasError": [gDbaasError,"errorCodeInKey"],
        "gPatchError": [gPatchError,"errorCodeInKey"],
        "gPatchSuggestion": [gPatchSuggestion,"errorCodeInKey"],
        "gBDCSError": [gBDCSError,"errorCodeInKey"],
        "gDiskgroupError": [gDiskgroupError,"errorCodeInEmbeddedValue"],
        "gBMCError": [gBMCError,"errorCodeInEmbeddedValue"],
        "gPartitionError": [gPartitionError,"errorCodeInEmbeddedValue"],
        "gCellUpdateError": [gCellUpdateError,"errorCodeInEmbeddedValue"],
        "gReconfigError": [gReconfigError,"errorCodeInEmbeddedValue"],
        "gExascaleError": [gExascaleError, "errorCodeInEmbeddedValue"],
        "gOCIError": [gOCIError,"errorCodeInEmbeddedValue"]
    }

hw_validate_error_messages = {
    90000: {
        "message": "dom0:{hw_name} test failed to execute",
        "category": "config",
        "hw_type": "dom0"
    },
    91000: {
        "message": "cell:{hw_name} test failed to execute",
        "category": "config",
        "hw_type": "cell"
    },
    92000: {
        "message": "ibswitch:{hw_name} test failed to execute",
        "category": "config",
        "hw_type": "ibswitch"
    },
    90001: {
        "message": "dom0:{hw_name} not pingable",
        "category": "config",
        "hw_type": "dom0"
    },
    91001: {
        "message": "cell:{hw_name} not pingable",
        "category": "config",
        "hw_type": "cell"
    },
    92001: {
        "message": "ibswitch:{hw_name} not pingable",
        "category": "config",
        "hw_type": "ibswitch"
    },
    90002: {
        "message": "ssh connection failed on dom0:{hw_name}",
        "category": "config",
        "hw_type": "dom0"
    },
    91002: {
        "message": "ssh connection failed on cell:{hw_name}",
        "category": "config",
        "hw_type": "cell"
    },
    92002: {
        "message": "ssh connection failed on ibswitch:{hw_name}",
        "category": "config",
        "hw_type": "ibswitch"
    },
    90003: {
        "message": "hypervisor test failed on dom0:{hw_name}",
        "category": "config",
        "hw_type": "dom0"
    },
    91003: {
        "message": "cellsrvStatus test failed on cell:{hw_name}",
        "category": "config",
        "hw_type": "cell"
    },
    92003: {
        "message": "onboard ibdevice test returned failure",
        "category": "config",
        "hw_type": "ibswitch"
    },
    90004: {
        "message": "fan status on dom0:{hw_name} is abnormal",
        "category": "hw",
        "hw_type": "dom0"
    },
    91004: {
        "message": "fanStatus test failed on cell:{hw_name}",
        "category": "hw",
        "hw_type": "cell"
    },
    92004: {
        "message": "fan test returned failure",
        "category": "hw",
        "hw_type": "ibswitch"
    },
    90005: {
        "message": "power status on dom0:{hw_name} is abnormal",
        "category": "hw",
        "hw_type": "dom0"
    },
    91005: {
        "message": "powerStatus test failed on cell:{hw_name}",
        "category": "hw",
        "hw_type": "cell"
    },
    92005: {
        "message": "psu test returned failure",
        "category": "hw",
        "hw_type": "ibswitch"
    },
    90006: {
        "message": "temperature status on dom0:{hw_name} is abnormal",
        "category": "hw",
        "hw_type": "dom0"
    },
    91006: {
        "message": "temperatureStatus test failed on cell:{hw_name}",
        "category": "hw",
        "hw_type": "cell"
    },
    92006: {
        "message": "temperature test returned failure",
        "category": "hw",
        "hw_type": "ibswitch"
    },
    90007: {
        "message": "space used in root partition is more than threshold(95) on dom0:{hw_name}",
        "category": "hw",
        "hw_type": "dom0"
    },
    91007: {
        "message": "storage_test on root partition failed on cell:{hw_name}",
        "category": "hw",
        "hw_type": "cell"
    },
    90008: {
        "message": "Free space available on /EXAVMIMAGES partition on dom0 {hw_name} is insufficient",
        "category": "hw",
        "hw_type": "dom0"
    },
    90009: {
        "message": "PHYSICALDISK status on compute:{hw_name} is abnormal",
        "category": "hw",
        "hw_type": "dom0"
    },
    91009: {
        "message": "PHYSICALDISK status on cell:{hw_name} is abnormal",
        "category": "hw",
        "hw_type": "cell"
    },
    90010: {
        "message": "memory_check failed on dom0:{hw_name}",
        "category": "hw",
        "hw_type": "dom0"
    },
    90011: {
        "message": "cell.conf not found in /opt/oracle.cellos on dom0:{hw_name}",
        "category": "config",
        "hw_type": "dom0"
    },
    90012: {
        "message": "ilom_admin_consistency test failed on dom0:{hw_name}",
        "category": "config",
        "hw_type": "dom0"
    },
    90013: {
        "message": "bridge_check test failed on dom0:{hw_name}",
        "category": "config",
        "hw_type": "dom0"
    },
    90014: {
        "message": "stale_domu_check test failed on dom0:{hw_name}",
        "category": "config",
        "hw_type": "dom0"
    },
    90015: {
        "message": "image info check failed, wrong node type on dom0:{hw_name}",
        "category": "config",
        "hw_type": "dom0"
    },
    91016: {
        "message": "LUN status on cell:{hw_name} is abnormal",
        "category": "hw",
        "hw_type": "cell"
    },
    91017: {
        "message": "GRIDDISK status on cell:{hw_name} is abnormal",
        "category": "config",
        "hw_type": "cell"
    },
    91018: {
        "message": "Could not retrieve GRIDDISK output, griddisks could have been deleted",
        "category": "config",
        "hw_type": "cell"
    },
    91019: {
        "message": "GRIDDISK entries present on cell:{hw_name}",
        "category": "config",
        "hw_type": "cell"
    },
    91020: {
        "message": "CELLDISK status on cell:{hw_name} is abnormal",
        "category": "config",
        "hw_type": "cell"
    },
    91021: {
        "message": "Cell Secure Erase cannot proceed in case of MVM",
        "category": "config",
        "hw_type": "cell"
    },
    91022: {
        "message": "Cell Secure Erase cannot proceed with active Grid Disks present (In case of SVM)",
        "category": "config",
        "hw_type": "cell"
    },
    91023: {
        "message": "Cell Secure Erase failed (In case of SVM)",
        "category": "config",
        "hw_type": "cell"
    },
    91024: {
        "message": "Unable to locate cellinit.ora file on Cell:{hw_name}",
        "category": "config",
        "hw_type": "cell"
    },
    91025: {
        "message": "ip_match_test between cellinit.ora and ifconfig on cell:{hw_name} failed",
        "category": "config",
        "hw_type": "cell"
    },
    91026: {
        "message": "Interfaces are not properly configured on cell:{hw_name}",
        "category": "config",
        "hw_type": "cell"
    },
    91027: {
        "message": "PMEMCACHE status on cell:{hw_name} is abnormal",
        "category": "hw",
        "hw_type": "cell"
    },
    91028: {
        "message": "FLASHCACHE status on cell:{hw_name} is abnormal",
        "category": "hw",
        "hw_type": "cell"
    },
    91029: {
        "message": "msStatus test failed on cell:{hw_name}",
        "category": "config",
        "hw_type": "cell"
    },
    91030: {
        "message": "rsStatus test failed on cell:{hw_name}",
        "category": "config",
        "hw_type": "cell"
    },
    91031: {
        "message": "hw alerts test unknown failure",
        "category": "config",
        "hw_type": "cell"
    },
    92032: {
        "message": "env_test failed on the switch",
        "category": "config",
        "hw_type": "ibswitch"
    },
    90033: {
        "message": "2TB Memory test failed on Dom0:{hw_name}",
        "category": "config",
        "hw_type": "dom0"
    },
    90034: {
        "message": "2TB Memory test not supported on Dom0:{hw_name}",
        "category": "config",
        "hw_type": "dom0"
    },
    91035: {
        "message": "hw alerts failed on cell:{hw_name}",
        "category": "config",
        "hw_type": "cell"
    }
}

def get_hw_validate_error(error_code, error_type, hw_name="unknown", additional_error_message=None):
    entry = hw_validate_error_messages.get(error_code)
    if entry:
        err_msg = entry.get("message", "unknown")
        if '{hw_name}' in err_msg:
            err_msg = err_msg.format(hw_name=hw_name)
        # Append additional_error_message if provided
        if additional_error_message:
            err_msg = f"{err_msg} {additional_error_message}"
        return {
            "error-type": error_type,
            "error-category": entry.get("category", "unknown"),
            "error-message": err_msg,
            "error-code": error_code
        }
    else:
        err_msg = "Unknown error code"
        if additional_error_message:
            err_msg = f"{err_msg} {additional_error_message}"
        return {
            "error-type": error_type,
            "error-category": "unknown",
            "error-message": err_msg,
            "error-code": error_code
        }


gBMCErrorCodeLookUp = {v[0] : v[1] for v in six.itervalues(gBMCError)}

def map_suberror_dict(_error_code):
    error_code = int(_error_code)
    key = get_dictkey(error_code)
    if key in gErrorDict :
        return gErrorDict[key]
    raise KeyError(_error_code)

def get_suberror_str(_subError_dict,_skey) :
    try:
        return  _subError_dict[_skey][0]
    except:
        return gSubError['0'][0]

def get_embedded_suberror_str(_subError_dict,_skey) :
    for key in _subError_dict :
        value = _subError_dict[key][0]
        if _skey == value:
            return  _subError_dict[key][1]
    return gSubError['0'][0]

def get_suberror(_subErrorVals,_skey):
    if _subErrorVals[1] == "errorCodeInKey" :
        return get_suberror_str(_subErrorVals[0],_skey)
    if _subErrorVals[1] == "errorCodeInEmbeddedValue" :
        return get_embedded_suberror_str(_subErrorVals[0],_skey)

def build_error_string(aError, aSubError, aCmt):

    _mkey = str(hex(aError))[2:].upper()
    _skey = str(hex(aSubError))[2:].upper()
    try:
        _subErrorVals = map_suberror_dict(_skey)
        _subError = get_suberror(_subErrorVals, _skey)
        _str = gMainError[_mkey][0] + '[' + aCmt + ']' + '(' +  _subError + ')'

    except:
        _str = gMainError[_mkey][0] + '[' + aCmt + ']' + '(' + "Invalid SubError Range" ')'
    return _str

def ebError(aCode, aInfo=None):

    _rc = (-1<<16) | aCode
    return _rc

class ExacloudRuntimeError(Exception):

    def __init__(self, aErrorCode=0, aErrorType=0, aErrorMsg='No Error Message Defined',aStackTrace=True,
                 aStep=None, aDo=False, Cluctrl = None):
        self.__ec = aErrorCode
        self.__et = aErrorType
        self.__em = None

        if Cluctrl:
            _f_comp = Cluctrl.mGetProvErr()
            if _f_comp:
                ebLogInfo('ExacloudRuntimeError: ProvErr : %s' %_f_comp)
                self.__em = _f_comp + " : " + aErrorMsg
        if not self.__em:
            if self.mCheckFailedComponent(aErrorMsg):
                self.__em = aErrorMsg
            else:
                #Lets have the default failed component as 'Exacloud' if none was set !
                self.__em = "EXACLOUD : " + aErrorMsg

        self.__sm = aStackTrace
        self.__step = aStep
        self.__do = aDo

    def mCheckFailedComponent(self, aErrorMsg):
        _f_comp_list = ['EXACLOUD :', 'OEDA :', 'DBAAS :', 'CELLCLI :']
        if aErrorMsg.startswith(tuple(_f_comp_list)):
            return True
        else:
            return False

    def __str__(self):
        _header_msg_begin = "************************************************EXACLOUD FATAL EXCEPTION BEGIN************************************************"
        _header_msg_end = "************************************************EXACLOUD FATAL EXCEPTION END**************************************************"
        _return_str = f"\n{_header_msg_begin}\n\nExacloud error code: {self.__ec}\nExacloud error message: {self.__em}\n\n{_header_msg_end}\n"
        return _return_str

    def mGetErrorCode(self):
        return self.__ec

    def mGetSubErrorCode(self) :
        return str(hex(self.__ec))[2:].upper()

    def mGetErrorType(self):
        return self.__et

    def mGetErrorMsg(self):
        return self.__em

    def mGetStackTraceMode(self):
        return self.__sm

    def mGetContext(self):
        return (self.__step, self.__do)

def retryOnException(max_times: int = 5, sleep_interval: int = 5):
    """
    Retries the function/method 'max_times' times if it raises an exception

    :param max_times: The max number of times to repeat the wrapped function
    :param sleep_interval: The amount of seconds to wait between retries, in
        case an Exception is raised
    """
    def decorator(decorated_function):
        def helper_function(*args, **kwargs):
            attempt = 0
            while attempt < max_times:
                try:
                    return decorated_function(*args, **kwargs)

                except Exception as e:
                    ebLogWarn("Exception raised when running: "
                        f"'{decorated_function}', attempt '{(attempt+1)}' "
                        f"of max '{max_times}'.\nException: {e}")
                    attempt += 1
                    time.sleep(sleep_interval)

            _msg = f"Maximum retries '{max_times} exceeded for " \
                f"'{decorated_function}'"
            ebLogError(_msg)
            raise ExacloudRuntimeError(aErrorMsg=_msg)
        return helper_function
    return decorator


