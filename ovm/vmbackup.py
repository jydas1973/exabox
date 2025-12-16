"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    vmbackup.py - Basic functionality

FUNCTION:
    Provide basic/core API for VM backups

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
       ririgoye 11/20/25 - Bug 38667586 - EXACS: MAIN: PYTHON3.11: SUPRASS ALL
                           PYTHON WARNINGS
       enrivera 11/04/25 - Bug 38614602 - EXACC:VMBACKUP: BACKUP OPERATION DOING 
                           INSTALLATION AND REPLACING EDITED CONFIG FILE
       enrivera 11/03/25 - Bug 38608075 - Create nodes.conf during install/patch for ExaCC
       gsundara 11/03/25 - Bug 38606770 - FATAL PYTHON ERROR: INIT_FS_ENCODING
       prsshukl 10/31/25 - Bug 38601485 - ECS_MAIN -> TESTS_VMBACKUP_PY.DIF IS
                           FAILING IN ECS_MAIN_LINUX.X64_251030.0900
       enrivera 10/21/25 - Bug 38284338 - Adding support for forceapply flag in exacloud
       oespinos 10/17/25 - Bug 38523938 - EXACC: ADD OPTIONS 'CLEANALL', 'UPDATE_NODESCONF'
                           AND 'UPDATE_PASSWORDLESS'
       jfsaldan 09/30/25 - Bug 38485986 - EXACS: VMBOSS: USE 'VMBACKUP VERSION'
                           FROM DOM0 TO COMPARE THE VERSION AGAINST
                           $EC_HOME/IMAGES/<VMBACKUP TGZ>
       arturjim 08/13/25 - Enh 38301649 - EXACC:VMBACKUP: ADD SUPPORT FOR SSH 
                           KEYS IN VMBACKUP 
       jfsaldan 08/01/25 - Enh 38250708 - ECRACLI VMBACKUP INSTALL CHANGES
                           CRONTAB ENTRIES ON DOM0
       akkar    07/24/25 - Bug 38222695 - Raise exception if backup sequence not available
       pbellary 07/15/25 - Enh 37980305 - EXACLOUD TO SUPPORT CHANGE OF VM BACKUP STORAGE 
                           FROM LOCAL TO EXASCALE STORAGE (EXISTING CLUSTERS)
       jfsaldan 06/11/25 - Bug 38058481 - EXACS:25.2.1, RC4:VMBACKUP TO OSS:ONE
                           COMPUTE FAILED VMBACKUP TO OSS ON MVM EXASCLE
       abflores 05/19/25 - Bug 37916975: UPDATE VMBACKUP PACKAGE DURING
                           ON-DEMAND VMBACKUP TOO
       jfsaldan 05/02/25 - VMBackup Install untar with verbose option causes
                           stuck mExecuteCmd
       aypaul   12/23/24 - Bug#37418797 Update exacloud to handle new vmbackup
                           version naming convention.
       gsundara 12/19/24 - Bug 37400164 - EXACS:24.4.2.1:VMBACKUP TO OSS: MVM
                           SCHEDULE VMBACKUP SEE PARTIAL VMBACKUP COMPLETED ON
                           ECRA DB QUERY, BUT ECRA OSSLIST DID NOT SEE UPLOAD
                           TO OSS
       jfsaldan 12/12/24 - Bug 37358454 - VMBACKUP TO OSS FAILURE | AD-HOC
                           BACKUP TAKEN BUT NOT BEING PUSHED TO OSS
       jfsaldan 10/30/24 - Bug 37202899 - EXACS:24.4.1:VMBACKUP TO OSS :
                           DOWNLOAD GOLD BACKUP RETURN COMPLETED/SUCCESS POST
                           GOLD BACKUP FAILED TO OSS
       jfsaldan 10/28/24 - Bug 37178530 - 2.4.1.2.7 | OSS_BACKUP VMBACKUP
                           OSSLIST SHOW ALL MVM CLUSTER BACKUP LIST
       jfsaldan 10/09/24 - Bug 37137506 - EXACLOUD VMBACKUP TO OSS: EXACLOUD
                           SHOULD DISABLE OSS BACKUP FROM VMBACKUP.CONF AFTER
                           THE ECRA SCHEDULED BACKUP FINISH
       jfsaldan 09/26/24 - Bug 37107371 - EXACS X11M - DELETE SERVICE TAKING
                           EXTRA 1HR AND HANGING DURING PREVMSETUP STEP
       gsundara 09/25/24 - Bug 36741285 - EXADB-XS: DISABLING VM BACKUP WHILE
                           INGESTION FROM EXACS TO EXACOMPUTE
       jfsaldan 09/11/24 - Bug 37048143 - EXACS:24.4.1:DELETE CLUSTER
                           FAILING:ERROR - 32488 - EXACLOUD : EXACLOUD REQUIRES
                           THE VMBACKUP TOOL TO BE INSTALLED SO THAT WE CAN
                           TAKE MODIFY THE VMBACKUP OSS PARAMETERS
       jfsaldan 09/05/24 - Bug 37020132 - EXACLOUD VMBACKUP : GOLDEN VMBACKUP
                           FAILS IF ANOTHER BACKUP IS CURRENTLY RUNNING IN THE
                           DOM0
       jfsaldan 08/21/24 - Bug 36899424 - EXACLOUD VMBACKUP TO OSS: EXACLOUD
                           SHOULD ENABLE THE OSSBACKUP FLAG IN VMBACKUP.CONF
                           BEFORE ANY OSS OPERATION, AND DISABLE AFTER IS DONE
       ririgoye 08/05/24 - Bug 36899055 - EXACLOUD VMBACKUP - PARALLEL BACKUP
                           OPERATION DOESN'T DISPLAY/RECORD ERRORS PROPERLY
       jfsaldan 07/22/24 - Bug 36860756 - VMBACKUP TO OBJECTSTORE ON EXADB-D -
                           FAILURE | LOCAL VARIABLE '_MSG' REFERENCED BEFORE
                           ASSIGNMENT
       jfsaldan 06/25/24 - Bug 36726315 - EXACLOUD VMBACKUP: EXACLOUD SHOULD
                           SET THE KMS OCIDS IN THE PAYLOAD PASSED TO THE
                           VMBACKUP TOOL ON THE DOM0S, INSTEAD OF SETTING THEM
                           IN EXABOX.CONF
       jfsaldan 06/24/24 - Enh 36755943 - EXACLOUD VMBACKUP: EXACLOUD SHOULD
                           HAVE A FEATURE FLAG SO THAT WE CAN ENABLE/DISABLE
                           THE CRONTAB ENTRY FOR VMBACKUP IN THE DOM0S
       pbellary 06/06/24 - Bug 36698695 - NODE RECOVERY : VM BACKUP FAILED DUE TO TIMEOUT WHILE WAITING FOR SSH PORT
       jfsaldan 06/04/24 - Bug 36696343 - ECS MAIN:VMBACKUP: VMBACKUP BACKUP
                           WORKFLOW DID NOT SHOW VMBACKUP ERROR VMBOSS WHILE
                           SUFFICENT SPACE IS UNAVAILABLE
       abyayada 05/29/24 - ER 36428455 - Ecracli to enhance VMbackup listing
                           using exaocid
       jfsaldan 05/24/24 - Enh 36474098 - EXACLOUD TO SUPPORT VM RESTORE ON
                           INDIVIDUAL FILESYSTEMS
       enrivera 05/22/24 - Bug 36605888 - VMBACKUP PATCH IN ECRA BREAKS THE PASSWORDLESS
                           SSH TO REMOTE NODE IN THE DOM0S
       jfsaldan 05/14/24 - Enh 36474795 - STATUS TRACKING FOR VMBACKUP RESTORE
                           OPERATIONS.
       jfsaldan 03/19/24 - Bug 36409419 - EXACS:23.4.1.2.1: VMBACKUP GOLD IMAGE
                           : DID NOT REMOVE PREVIOUS TERMINATED PROVISION GOLD
                           BACKUP IMAGE (ONLY IN CACHE FILE)
       enrivera 03/07/24 - Bug 36059011 - LATEST VM BACKUP UPGRADE IS NOT
                           UPDATING THE VMBACKUP.CONF WITH RIGHT VALUES
       pbellary 02/20/24 - Bug 36384090 - NODE RECOVERY : VMBACKUP RESTORE FAILED WITH ERROR 
                           "HOOK SCRIPT EXECUTION FAILED"
       jfsaldan 02/09/24 - Bug 36282190 - EXACS:23.4.1.2: VMBACKUP GOLD IMAGE
                           BACKUP TIME OUT
       jfsaldan 02/09/24 - Bug 36278260 - EXACS:23.4.1.2: VMBACKUP DOWNLOAD
                           EXAUNITID DID NOT FIND THE DOWNLOAD BACKUP
       pbellary 01/26/24 - Bug 36089062 - NODE RECOVERY: IMPLEMENT CHANGES IN EXACLOUD 
                           TO SUPPORT ADDITIONAL ATTRIBUTES FOR VMBACKUP RESTORE CMD
       jfsaldan 01/17/24 - Bug 36197480 - EXACS - EXACLOUD FAILS TO SET
                           VMBACKUP.CONF VALUES TO ENABLED VMBACKUP TO OSS
       aypaul   12/19/23 - Enh#35866197 Support reload option using osslist.
       ririgoye 11/17/23 - Parallelize backup of dom0s
       pbellary 11/10/23 - Bug 35939171 - NODE RECOVERY: POST VM BACKUP RESTORE OPERATION UNABLE TO CONNECT TO DOMU USING ROOT KEYS
       jfsaldan 11/01/23 - Bug 35969085 - ECS:EXACLOUD:23.4.1.2:ADD KMS KEY
                           OCID AND CRYPTO ENDPOINT IN ALREADY PROVISIONED
                           CLUSTERS IF PARAMETER IS MISSING FROM VMBACKUP.CONF
       jfsaldan 10/20/23 - Bug 35857923 - ECS:23.4.1.2:EXACLOUD SHOULD NOT
                           EXPECT THE DEST_DIR VALUE ON VMBACKUP RESTORE_OSS
                           CALL
       pbellary 10/18/23 - Bug SYSTEM FIRST BOOT IMAGE FILE GETS REMOVED DURING IN-PLACE REPLACEMENT 
                           PROCESS CAUSING FAILURE OF "EXAUNIT-ATTACH-COMPUTE" OPERATION
       pbellary 10/06/23 - Enh 35784380 - NODE RECOVERY: VM SHOULD BE REGISTERED BEFORE INVOKING VMBACKUP RECOVERY
       enrivera 10/05/23 - Bug 35857483 - VMBACKUP: EXACLOUD INSTALL ENDPOINT IS NOT SETTING ALL CUSTOM PARAMETERS CORRECTLY
       jfsaldan 09/27/23 - Enh 35791811 - VMBACKUP TO OSS:EXACLOUD: REDUCE TIME
                           WHILE TAKING GOLD IMAGE DURING PROVISIONING
       ririgoye 09/06/23 - Enh 35688081 - EXACLOUD SHOULD UPDATE THE VMBACKUP
                           TOOL DURING VMBACKUP_BACKUP_HOST CALL
       jfsaldan 08/16/23 - Enh 35692408 - EXACLOUD - VMBOSS - CREATE A FLAG IN
                           EXABOX.CONF THAT TOGGLES BETWEEN INSTANCE PRINCIPALS
                           AND USERS PRINCIPALS FOR VMBACKUP TO OSS MODULE
       pbellary 08/11/23   Bug 35702520 - NODE RECOVERY: VM BACKUP RECOVERY API GETTING WRONG SEQUENCE NUMBER
       pbellary 07/19/23 - Enh 35434971 - NODE RECOVERY: EXACLOUD API TO RECOVER A NODE USING VM BACKUP
       jfsaldan 06/22/23 - Enh 35399269 - EXACLOUD TO SUPPORT RETRIEVAL OF
                           METADATA FILES FROM DOM0 FOR BACKUP OPERATION
       vikasras 06/21/23 - 35276663 - VMBACKUP UTILITY INSTALL IS ADDING WRONG ENTRY IN CRONTAB
       jfsaldan 06/13/23 - Enh 35399269 - EXACLOUD TO UPLOAD METADATA FILES
                           FROM DOM0 FOR BACKUP OPERATION.
       jfsaldan 03/16/23 - Enh 35135691 - EXACLOUD - ADD SUPPORT FOR VMBACKUP
                           ECRA SCHEDULER
       jfsaldan 02/09/23 - Bug 35054534 - EXACS:22.2.1:DROP2:FILE SYSTEM
                           ENCRYPTION TEST: VMBACKUP INSTALL FAILED AT
                           IMAGES/PYTHON-FOR-VMBACKUP-OL6.TGZ: NO SUCH FILE OR
                           DIRECTORY
       jfsaldan 01/10/23 - Enh 34965441 - EXACLOUD TO SUPPORT NEW TASK FOR GOLD
                           IMAGE BACKUP
       aypaul   12/12/22 - Bug#34881713 Delete vmbackups on vm cluster
                           termination.
       dekuckre 07/06/22 - 34054166: Add MATERIALIZED_LOCAL_COPY to default param list
       enrivera 05/26/22 - 32594252 - EXACC GEN2: MAKE VMBACKUP PART OF CPS SW OR EXACLOUD PATCHING
       siyarlag 04/20/21 - 32690067: remove dir contents before extraction
       dekuckre 03/02/21 - 32568369: Validate params added to vmbackup.conf
       dekuckre 11/16/20 - XbranchMerge dekuckre_bug-32041302 from
                           st_ecs_20.2.1.0.0rel
       dekuckre 11/13/20 - 31990802: Update mInstallVMbackup
       hgaldame 10/06/20 - enh 31980918 - extending the integration of exacloud
                           and the vm backup tool for oci/exacc
       dekuckre 10/21/20 - 32041302: Remove optional parameters related to backup.
       dekuckre 08/04/20 - 31708798: Fix mInstallVMbackup
       agarrido 05/09/18 - 27560658: Add install, backup, restore, list and patch operations
       dekuckre 03/21/18 - 27703864: Create file
"""

from exabox.ovm.vmboci import ebVMBackupOCI
from exabox.core.Error import ExacloudRuntimeError, gResError
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB
from exabox.exaoci.ExaOCIFactory import ExaOCIFactory
from exabox.exaoci.connectors.ExaboxConfConnector import ExaboxConfConnector
from exabox.exaoci.connectors.R1Connector import R1Connector
from exabox.exaoci.connectors.RegionConnector import RegionConnector
from exabox.exaoci.connectors.R1Connector import R1Connector
from exabox.ovm.hypervisorutils import getHVInstance
from exabox.log.LogMgr import ebLogError, ebLogDebug, ebLogInfo, ebLogWarn, ebLogVerbose, ebLogTrace
from exabox.ovm.vmconfig import exaBoxVMConfig, exaBoxClusterConfig, ebVMCfg
from exabox.ovm.clumisc import ebCluSshSetup
from exabox.ovm.vmcontrol import ebVgLifeCycle
from exabox.ovm.cluvmrecoveryutils import NodeRecovery
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from multiprocessing import Manager, Process
from tempfile import NamedTemporaryFile
from exabox.utils.ExaRegion import get_r1_certificate_path
from exabox.utils.node import (connect_to_host, node_exec_cmd,
        node_exec_cmd_check, node_cmd_abs_path_check)

import socket
import time
import os
import json
import fileinput
import uuid
import sys
import re
import glob
import re
import ast
import datetime
import copy
import shutil
import tarfile
from concurrent import futures

class ebCluManageVMBackup(object):

    # Constants defined for this class

    # vmbackup configuration file stored in dom0s
    VMBACKUPCONF_FILE = "/opt/oracle/vmbackup/conf/vmbackup.conf"
    VMBACKUPOFF_FILE = "/opt/oracle/vmbackup/conf/vmbackup.conf.off"
    VMBACKUPENV_FILE = "/opt/python-vmbackup/bin/set-vmbackup-env.sh"
    VMBACKUP_STATUS_FILE = "/EXAVMIMAGES/Backup/OSSMetadata/ossbackup_status.json"
    VMBACKUP_OSS_DOWNLOAD_STATUS = "/EXAVMIMAGES/Restore/{0}/ossrestore_status.dat"
    VMBACKUPINT_BITS = "images/python-for-vmbackup"
    VMBACKUPPKG_BITS = "images/release-vmbackup"
    VMBACKUP_PARAMS = ['ST_AUTH', 'ST_USER', 'ST_KEY', 'ST_CONTAINER', 'ST_AUTH_VERSION', 'ST_SEGMENT_SIZE', 'ST_THREADS_PER_SEGMENT', 'ST_OSS_AGEOUT_IN_DAYS', 'DELETE_LOCAL_BACKUP', 'REMOTE_BACKUP', 'OSS_BACKUP', 'MAX_REMOTE_BACKUPS', 'BACKUP_ONLY_VM', 'SKIP_IMG', 'SKIP_CHECKSUM', 'SERVER_ALIVE_INTERVAL', 'SERVER_ALIVE_COUNTMAX', 'MATERIALIZED_LOCAL_COPY', 'ACTIVE_BLOCKCOMMIT']
    FAIL = "Fail"
    PASS = "Pass"

    CONFIG_CRYPTO_EP = "kms_dp_endpoint"
    CONFIG_MASTER_KEY_OCID = "kms_key_id"
    SET_PARAM_OSS_BACKUP = "OSS_BACKUP"
    SET_PARAM_CRYPTO_EP = "OSS_KMS_ENDPOINT"
    SET_PARAM_MASTER_KEY_OCID = "OSS_KMS_KEY_ID"
    SET_PARAM_R1_CERT = "OSS_R1_CERT"
    SET_PARAM_OCI_CERT = "OSS_OCI_CERT_PATH"
    CERTIFICATE_R1_REMOTE_PATH = \
        "/opt/oracle/vmbackup/ociconf/combined_r1.crt"
    CERTIFICATE_CUSTOM = \
        '/opt/oracle/vmbackup/ociconf/certificate.crt'

    def __init__(self, aExaBoxCluCtrl):

        self.__ebox = aExaBoxCluCtrl
        self.__sshsetup = ebCluSshSetup(self.__ebox)
        self._vmbackupdata = {}
        self._is_exacc_rack = self.__ebox.mIsOciEXACC()

    def mGetVMBackupData(self):
        return self._vmbackupdata

    def mSetVMBackupData(self, aVMBackupData):
        self._vmbackupdata = aVMBackupData

    def mExecuteOperation(self, aOptions):

        _options = aOptions
        _vmbackupdata = self.mGetVMBackupData()
        _rc = 0

        _vmbackupdata["Exacloud Cmd Status"] = self.PASS

        if _options.vmbackup_operation is None:
            ebLogInfo("Invalid invocation or unsupported vmbackup option")
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL

        elif _options.vmbackup_operation == "enable":
            _vmbackupdata["Command"] = "enable"
            ebLogInfo("Running vmbackup operation: enable")
            _rc = self.mSetVMBackup(True)

        elif _options.vmbackup_operation == "disable":
            _vmbackupdata["Command"] = "disable"
            ebLogInfo("Running vmbackup operation: disable")
            _rc = self.mSetVMBackup(False)

        elif _options.vmbackup_operation == "setparam":
            _vmbackupdata["Command"] = "setparam"
            ebLogInfo("Running vmbackup operation: setparam")
            _rc = self.mSetVMBackupParameter(_options)

        elif _options.vmbackup_operation == "getparam":
            _vmbackupdata["Command"] = "getparam"
            ebLogInfo("Running vmbackup operation: getparam")
            _rc = self.mGetVMBackupParameter(_options)

        elif _options.vmbackup_operation == "install":
            _vmbackupdata["Command"] = "install"
            ebLogInfo("Running vmbackup operation: install")
            _rc = self.mInstallVMbackup(_options)

        # ECRAcli ondemand backup
        elif _options.vmbackup_operation == "backup":
            _vmbackupdata["Command"] = "backup"
            ebLogInfo("Running vmbackup operation: backup")
            _rc = self.mVMbackupAll(_options)

        # Scheduler backup
        elif _options.vmbackup_operation == "backup_host":
            _vmbackupdata["Command"] = "backup_host"
            ebLogInfo("Running vmbackup operation: backup_host")
            _rc = self.mTriggerBackgrounBackupHost(_options)

        elif _options.vmbackup_operation == "golden_backup":
            _vmbackupdata["Command"] = "golden_backup"
            ebLogInfo("Running vmbackup operation: golden_backup")
            _rc = self.mTriggerGoldenBackup(_options)

        elif _options.vmbackup_operation == "restore":
            _vmbackupdata["Command"] = "restore"
            ebLogInfo("Running vmbackup operation: restore")
            _rc = self.mRestoreVMbackup(_options)

        elif _options.vmbackup_operation == "restore_oss":
            _vmbackupdata["Command"] = "restore_oss"
            ebLogInfo("Running vmbackup operation: restore_oss")
            _rc = self.mRestoreOSSVMbackup(_options)

        elif _options.vmbackup_operation == "restore_local":
            _vmbackupdata["Command"] = "restore_local"
            ebLogInfo("Running vmbackup operation: restore_local")
            _rc = self.mRestoreLocalVMbackup(_options)

        elif _options.vmbackup_operation == "patch":
            _vmbackupdata["Command"] = "patch"
            ebLogInfo("Running vmbackup operation: patch")
            _rc = self.mInstallVMbackup(_options, aPatching=True)

        elif _options.vmbackup_operation == "list":
            _vmbackupdata["Command"] = "list"
            ebLogInfo("Running vmbackup operation: list")
            _rc = self.mListVMbackup()

        elif _options.vmbackup_operation == "list_oss":
            _vmbackupdata["Command"] = "list_oss"
            ebLogInfo("Running vmbackup operation: list_oss")
            _rc = self.mListOSSVMbackup(_options)

        elif _options.vmbackup_operation == "get_host_status":
            _vmbackupdata["Command"] = "get_host_status"
            ebLogInfo("Running vmbackup operation: get_host_status")
            _rc = self.mGetDom0BackupStatus(_options)

        elif _options.vmbackup_operation == "export_keys_dom0":
            _vmbackupdata["Command"] = "export_keys_dom0"
            ebLogInfo("Running vmbackup operation: export_keys_dom0")
            _rc = self.mCopyVMBackupUserCredentialsToDom0s(_options)

        elif _options.vmbackup_operation == "setcron":
            _vmbackupdata["Command"] = "setcron"
            ebLogInfo("Running vmbackup operation: setcron")
            _rc = self.mSetCrontabEntry(_options)

        elif _options.vmbackup_operation == "exascale_edv_backup":
            _vmbackupdata["Command"] = "exascale_edv_backup"
            ebLogInfo("Running vmbackup operation: exascale_edv_backup")
            _rc = self.mExascaleEDVbackup(_options)

        elif _options.vmbackup_operation == "cleanall":
            _vmbackupdata["Command"] = "cleanall"
            ebLogInfo("Running vmbackup operation: cleanall")
            _rc = self.mCleanAllVMbackup()

        elif _options.vmbackup_operation == "update_nodesconf":
            _vmbackupdata["Command"] = "update_nodesconf"
            ebLogInfo("Running vmbackup operation: update_nodesconf")
            _rc = self.mUpdateNodesConf(_options)

        elif _options.vmbackup_operation == "update_passwordless":
            _vmbackupdata["Command"] = "update_passwordless"
            ebLogInfo("Running vmbackup operation: update_passwordless")
            _rc = self.mUpdatePasswordlessChain(_options)

        ebLogTrace("JSON returned from Exacloud: %s" % _vmbackupdata)

        _reqobj = self.__ebox.mGetRequestObj()
        if _reqobj:
            _db = ebGetDefaultDB()
            _reqobj.mSetData(json.dumps(_vmbackupdata, sort_keys=True))
            _db.mUpdateRequest(_reqobj)

        return _rc

    # mSetVMBackup:
    # Turns VMbackup on the dom0's ON/OFF based on aFlag is passed as True/False.
    # This is achieved by keeping/removing the configuration file.
    # Note:
    # To disable vmbackup, move VMBACKUPCONF_FILE to VMBACKUPOFF_FILE.
    # To enable vmbackup, move VMBACKUPOFF_FILE to VMBACKUPCONF_FILE.
    def mSetVMBackup(self, aFlag):

        _flag = aFlag
        _rc = 0
        _vmbackupdata = self.mGetVMBackupData()
        _vmbackupdata["Log"] = []

        if _flag:
            _cmdstr = "mv -f " + self.VMBACKUPOFF_FILE + " " + self.VMBACKUPCONF_FILE
        else:
            _cmdstr = "mv -f " + self.VMBACKUPCONF_FILE + " " + self.VMBACKUPOFF_FILE

        _dpairs = self.__ebox.mReturnDom0DomUPair()
        for _dom0, _ in _dpairs:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)
            _vmbackupdata[_dom0] = {}

            _node.mExecuteCmdLog("cp " + self.VMBACKUPCONF_FILE + " " + self.VMBACKUPOFF_FILE)

            _, _o, _e = _node.mExecuteCmd(_cmdstr)
            _out = _o.readlines()
            if not _out or len(_out) == 0:
                if _flag:
                    _log = "Turned VM backup ON on Dom0 %s" % (_dom0)
                else:
                    _log = "Turned VM backup OFF on Dom0 %s" % (_dom0)

                ebLogInfo(_log)
                _vmbackupdata[_dom0]["Exacloud Cmd Status"] = self.PASS
                _vmbackupdata[_dom0]["Log"] = _log
                _vmbackupdata["Log"].append(_log)
                _rc = 0
            else:
                _log = "Failed to set VM backup to %s on Dom0(%s)" % (_flag, _dom0)
                ebLogError(_log)
                _vmbackupdata[_dom0]["Exacloud Cmd Status"] = self.FAIL
                _vmbackupdata[_dom0]["Log"] = _log
                _vmbackupdata["Log"].append(_log)
                _rc = 1

        return _rc

    def mRecordError(self, aErrorCode, aString=None):

        _iormdata = {}
        _iormdata["Status"] = "Fail"
        _iormdata["ErrorCode"] = aErrorCode

        if aString is None:
            _iormdata["Log"] = gResError[_iormdata["ErrorCode"]][0]
        else:
            _iormdata["Log"] = gResError[_iormdata["ErrorCode"]][0] + aString

        ebLogInfo("%s" % (_iormdata["Log"]))

    # mSetVMBackupParameter:
    # Sets the vmbackup parameter (in the configuration file) to a value
    # obtained from the json passed through aOptions.
    def mSetVMBackupParameter(self, aOptions, aDom0DomUPair=None):

        _options = aOptions
        _rc = 0

        # Create a unique tmp file to path with new params and copy
        os.makedirs("tmp", exist_ok=True)

        with NamedTemporaryFile(dir="tmp",
                delete=True,
                suffix=f"_vmbackup.conf_{uuid.uuid1()}") as _fd_localfile:
            _localfile = _fd_localfile.name
            ebLogTrace(f"Using vmbackup.conf {_localfile}")

            _vmbackupdata = self.mGetVMBackupData()
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL

            # Keep a local copy of the configuration file
            # for processing below.
            if aDom0DomUPair:
                _dpairs = aDom0DomUPair
            else:
                _dpairs = self.__ebox.mReturnDom0DomUPair()

            # If vmbackup is not enabled (configuraiton file is not present), then
            # return.
            if self.mCheckVMbackupEnabled(aDom0DomUPair) is False:
                _log = "VM backup is not enabled. Please enable vmbackup before proceeding to setting vmbackup parameter."
                _vmbackupdata["Log"] = _log
                ebLogError(_log)
                _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                return 0

            if not _options.jsonconf:
                return self.mRecordError("808")

            # Obtain the parameter and its value form the json
            _key = list(_options.jsonconf.keys())[0]
            _value = list(_options.jsonconf.values())[0]

            for _dom0, _ in _dpairs:
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_dom0)
                if _node.mFileExists(self.VMBACKUPCONF_FILE):
                    _node.mCopy2Local(self.VMBACKUPCONF_FILE, _localfile)
                _node.mDisconnect()

                # Legacy code: we always assumed all dom0s from an infra will have
                # the same vmbackup.conf
                break

            # Iterate through the lines in the file and search for the parameter
            # in the line and replace the value corresponding to the parameter.
            for _line in fileinput.FileInput(_localfile, inplace=1):
                if not _line.startswith('#'):
                    _pair = _line.split('=')
                    if (_key == _pair[0].rstrip()):
                        if (_value != _pair[1].rstrip()):
                            _line = _line.replace(_pair[1].rstrip(), _value)
                            _log = "Setting " + _key + " to " + _value + " in vmbackup configuration."
                            _vmbackupdata["Log"] = _log
                            _vmbackupdata["Exacloud Cmd Status"] = self.PASS
                            _rc = 0
                        else:
                            _vmbackupdata["Log"] = _key + " is already set to " + _value + " in vmbackup configuration."
                            _rc = 1
                sys.stdout.write(_line)

            # Copy the updated local configuration file back to the dom0s.
            for _dom0, _ in _dpairs:
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_dom0)
                _rc, _in, _out, _err = self.__ebox.mExecuteLocal("/bin/ls " + _localfile)
                if _node.mFileExists(self.VMBACKUPCONF_FILE):
                    _node.mCopyFile(_localfile, self.VMBACKUPCONF_FILE)

                _node.mDisconnect()


        return _rc

    # mGetVMBackupParameter:
    # Gets the value of the vmbackup parameter from the vmbackup configuration
    # file.
    def mGetVMBackupParameter(self, aOptions):

        _options = aOptions
        _value = None
        os.makedirs("tmp", exist_ok=True)

        with NamedTemporaryFile(dir="tmp",
                delete=True,
                suffix=f"_vmbackup.conf_{uuid.uuid1()}") as _fd_localfile:
            _localfile = _fd_localfile.name
            ebLogTrace(f"Using vmbackup.conf {_localfile}")

            _vmbackupdata = self.mGetVMBackupData()
            _rc = 0

            # If vmbackup is not enabled (configuraiton file is not present), then
            # return.
            if self.mCheckVMbackupEnabled() is False:
                _log = "VM backup is not enabled. Please enable vmbackup before proceeding to getting vmbackup parameter."
                _vmbackupdata["Log"] = _log
                ebLogError(_log)
                _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                return 0

            # Obtain the vmbackup parameter form the json
            _key = _options.jsonconf["param"]

            # Keep a local copy of the configuration file
            # for processing below.
            _dpairs = self.__ebox.mReturnDom0DomUPair()
            for _dom0, _ in _dpairs:
                _node = exaBoxNode(get_gcontext())
                _node.mConnect(aHost=_dom0)
                if _node.mFileExists(self.VMBACKUPCONF_FILE):
                    _node.mCopy2Local(self.VMBACKUPCONF_FILE, _localfile)
                _node.mDisconnect()
                break

            try:
                _file = open(_localfile)

            except:
                _log = 'Failed to access/read vmbackup configuration file %s'
                _vmbackupdata["Log"] = _log
                ebLogError(_log)
                _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                raise ExacloudRuntimeError(0x0763, 0xA, "Failed to access/read vmbackup configuration file")

            # Iterate through the lines in the file and search for the parameter
            # in the line and report the value corresponding to the parameter.
            for _line in _file:
                if not _line.startswith('#'):
                    _pair = _line.split('=')
                    if (_key == _pair[0]):
                        _value = _pair[1].rstrip()
                        _log = "Value of vmbackup parameter(%s) obtained from configuration file is %s" % (_key, _value)
                        ebLogInfo(_log)
                        _vmbackupdata["Log"] = _log
                        _vmbackupdata["Exacloud Cmd Status"] = self.PASS
                        _vmbackupdata[_key] = _value
                        _rc = 0
                        break

            _file.close()

            if _value is None:
                _log = "Failed to get the value of vmbackup parameter(%s)" % (_key)
                _vmbackupdata["Log"] = _log
                ebLogError(_log)
                _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                _rc = 1

        return _rc

    def mCheckVMbackupEnabled(self, aDom0DomUPair=None):

        if aDom0DomUPair:
            _dpairs = aDom0DomUPair
        else:
            _dpairs = self.__ebox.mReturnDom0DomUPair()
        for _dom0, _ in _dpairs:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)
            if _node.mFileExists(self.VMBACKUPCONF_FILE):
                _node.mDisconnect()
                return True
            _node.mDisconnect()

        return False

    # mgetOLVersion:
    # Return the OL version based on the kernel (e.g el6uek.x86_64)
    def mGetOLVersion(self, aNode):

        _cmd_str = "uname -a  | awk '{print $3}'"
        _, _o, _e = aNode.mExecuteCmd(_cmd_str)
        _out = _o.readlines()[0]
        _version = '-OL6' if '6' in _out.split('.')[-2] else ''
        return _version

    # mConfigureVMBackup:
    # Fill the vmbackup configuration file with the payload parameters
    # Use aCustom for custom configuration without a payload
    def mConfigureVMBackup(self, aOptions, aNode, aCustom=False):

        _options = aOptions
        # Obtain the parameters and their values form the json
        if aCustom and isinstance(aCustom, dict):
            _items = list(aCustom.items())
        else:
            _items = list(_options.jsonconf.items())
        ebLogTrace('Items passed to configure: {0}'.format(_items))
        _cmd_str = ''
        _rc = 0
        # Apply configuration update
        for _key, _value in _items:
                _, _o, _e = aNode.mExecuteCmd("grep {0} {1}".format(_key, self.VMBACKUPCONF_FILE))
                _out = _o.readlines()
                _key = _key.upper()
                if _key not in self.VMBACKUP_PARAMS:
                    continue
                ebLogInfo(f'Updating/adding {_key} to vmbackup confirguration')
                if _out:
                    _cmd_str += r'sed -i -e "s#{0}\s*=.*#{0}={1}#" {2};'.format(_key, _value, self.VMBACKUPCONF_FILE)
                else:
                    _cmd_str += 'echo "{0}={1}" >> {2};'.format(_key, _value, self.VMBACKUPCONF_FILE)
                ebLogInfo(f"Current command string: {_cmd_str}")
        if _cmd_str:
            _, _o, _e = aNode.mExecuteCmd(_cmd_str)
            _rc = aNode.mGetCmdExitStatus()
        if _rc == 0:
            ebLogInfo("*** Successful vmbackup configuration.")
        else:
            ebLogError('*** Error configuring vmbackup: {0} '.format(_e.readlines()))

    # mCheckAvailableVMbackups:
    # Check if there are available backups of a vm
    def mCheckAvailableVMbackups(self, aNode, aVmName):
        _cmd_str = f"source {self.VMBACKUPENV_FILE}; vmbackup list | grep {aVmName} | grep success | sed 's/\s\s*/ /g' | cut -d' ' -f2"
        _, _o, _ = aNode.mExecuteCmd(_cmd_str)
        _out = _o.readlines()
        if _out:
            _out = list(map(str,list(map(str.strip,_out))))
            return _out
        else:
            return False

    # mCheckVMbackupInstalled:
    # Check if the utility is installed, sourcing the shiped environment
    # then search for the vmbackup package
    def mCheckVMbackupInstalled(self, aNode):

        if not aNode.mFileExists(self.VMBACKUPENV_FILE):
            return False
        _cmd_str = 'source ' + self.VMBACKUPENV_FILE
        #_cmd_str = 'source ' + self.VMBACKUPENV_FILE + '&& pip list | grep vmbackup'
        _, _o, _ = aNode.mExecuteCmd(_cmd_str)
        if aNode.mGetCmdExitStatus():
            return False
        #_out = _o.readlines()[0]
        #ebLogDebug('*** VMBackup version: {0}'.format(_out.split()[1]))
        return True

    # mInstallVMbackupOnDom0:
    # Install VMbackup utility on single dom0, for local backups
    def mInstallVMbackupOnDom0(self, aOptions, aNode, aPatching=False):

        _options = aOptions
        _vmbackupdata = self.mGetVMBackupData()
        _node = aNode
        _dest_dir = '/opt/exacloud/vmbackup/'
        _install_path = '/opt/python-vmbackup'

        # Regardless of OL6 or OL7, we use the same python bits
        # Bug 35054534
        _interpreter_bits = self.VMBACKUPINT_BITS + '.tgz'
        _package_bits = glob.glob(self.VMBACKUPPKG_BITS + '*[0-9].tgz').pop()
        _node.mExecuteCmd('mkdir -p ' + _dest_dir + 'release-vmbackup/')
        _node.mExecuteCmd('rm -f ' + _dest_dir + 'release-vmbackup/*')
        _node.mCopyFile(_interpreter_bits, _dest_dir + 'python-for-vmbackup.tgz')
        _node.mCopyFile(_package_bits, _dest_dir +  'release-vmbackup.tgz')

        # Check if dom0 on-disk has Python 3.6
        _i, _o, _e = _node.mExecuteCmd('test -f {0}/bin/python3.6 && echo "exists" || echo "notfound"'.format(_install_path))
        _disk_36 = "exists" in _o.read().strip()

        # Check if tar.gz has Python 3.8
        _tar_38 = False  # Initialize
        try:
            with tarfile.open(_interpreter_bits, 'r:gz') as tar:
                members = tar.getnames()
                _tar_38 = any('python3.8' in m and 'python-vmbackup/bin' in m for m in members)
        except Exception as e:
            ebLogError("Error reading tar file {0}: {1}".format(_interpreter_bits, str(e)))

        # Delete /opt/python-vmbackup ONLY if upgrading from 3.6 to 3.8
        # this is to avoid mangling of 3.6 & 3.8 libs, leading to runtime errors.
        if _disk_36 and _tar_38:
            ebLogInfo("Upgrading Python 3.6 → 3.8: Deleting old python 3.6 installation")
            _node.mExecuteCmd('rm -rf {0}'.format(_install_path))

        _node.mExecuteCmd('tar -xzf {0}python-for-vmbackup.tgz -C /'.format(_dest_dir))
        _node.mExecuteCmd('tar -xzf {0}release-vmbackup.tgz --strip-components=1 -C {0}release-vmbackup'.format(_dest_dir))
        _cmd_str = 'cd {0}release-vmbackup && ./install.sh'.format(_dest_dir)
        _i,_o,_e = _node.mExecuteCmd(_cmd_str)
        if self.mCheckVMbackupInstalled(_node):
            # Proceed to configuration
            if not aPatching:
                self.mConfigureVMBackup(_options,_node,aPatching)
                _log = '*** Vmbackup is installed and configured on dom0: {0}'.format(_node.mGetHostname())
            else:
                _log = '*** Vmbackup is patched on dom0: {0}'.format(_node.mGetHostname())
            ebLogInfo(_log)
            _vmbackupdata["Log"] = _log
            _vmbackupdata["Exacloud Cmd Status"] = self.PASS
            _rc = 0
        else:
            _log = '*** Error during Vmbackup installation: cmd {0} returned {1}, error {2}'.format(_cmd_str, str(_o.readlines()), str(_e.readlines()))
            ebLogError(_log)
            _vmbackupdata["Log"] = _log
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
            _rc = 1
        return _rc

    # mInstallVMbackup:
    # Install VMbackup utility on all the dom0s and dependencies
    # Depending on the OL version install the corresponding python package
    def mInstallVMbackup(self, aOptions, aPatching=False):

        _options = aOptions
        _vmbackupdata = self.mGetVMBackupData()
        _rc = 0

        if not aPatching:
            if aOptions.jsonconf is None:
                _log = '*** VMBackup Install payload required'
                _vmbackupdata["Log"] = _log
                ebLogError(_log)
                _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                raise ExacloudRuntimeError(0x0763, 0xA, "Failed to get vmbackup payload")

        _dpairs = self.__ebox.mGetOrigDom0sDomUs()
        _dom0s = [pair[0] for pair in _dpairs]
        if self.__ebox.mIsOciEXACC():
            _dom0s = self.mSortDom0List(_dom0s)

        # ER 36755943. In ExaCS Exacloud must check exabox.conf on the
        # 'vmbackup' section for 'crontab_force_disable'.
        # Default value is 'false'
        _disable_crontrab =  get_gcontext().mGetConfigOptions().get(
            "vmbackup", {}).get("crontab_force_disable", "false")
        ebLogTrace(f"Crontab disable/enable flag: {_disable_crontrab}")

        for _inx, _dom0 in enumerate(_dom0s):
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)
            if self.mCheckVMbackupInstalled(_node) and not aPatching:
                ebLogWarn('*** Vmbackup already installed on {0}'.format(_dom0))

            _inst_rc = self.mInstallVMbackupOnDom0(aOptions, _node, aPatching)

            if _inst_rc != 0:
                _log = '*** Could not install vmbackup in dom0: ' + _dom0
                ebLogError(_log)
                _vmbackupdata["Log"] += _log
                _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                _rc = 1
                break

            if self.__ebox.mIsOciEXACC():
                ebLogInfo('*** Configuring ssh passwordless for {0}'.format(_dom0))
                _next_dom0 = _dom0s[0] if _inx == len(_dom0s)-1 else _dom0s[_inx+1]
                self.__sshsetup.mSetSSHPasswordlessForVMBackup(_dom0, [_next_dom0])
                ebLogInfo("*** Configuring sshd options for oci/exacc")
                _ssh_rc = self.mSetSSHDOptions(aOptions, _node)
                if _ssh_rc != 0:
                    _log = '*** Could not configure sshd options'
                    ebLogError(_log)
                    _vmbackupdata["Log"] += _log
                    _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                    _rc = 1
                    break
                ebLogInfo("*** Configuring Vmbackup cronjob for oci/exacc")
                _cron_rc = self.mSetVMBackupCronJob(aOptions, _node)
                if _cron_rc != 0:
                    _log = '*** Could not setup cronjob in ' + _dom0
                    ebLogError(_log)
                    _vmbackupdata["Log"] += _log
                    _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                    _rc = 1
                    break
            else:

                # ER 38250708
                # Exacloud should not add/modify the vmbackup crontab
                # entry if any existing commented/non commented entry
                # exists for vmbackup
                if not self.mGetVMBackupCronTabEntries(_node):
                    self.mSetVMBackupCronJob(_options, _node)
                else:
                    ebLogInfo(f"Skipping crontrab modification since "
                        f"crontrab entries are detected in {_dom0}")

            _node.mDisconnect()

        if self._is_exacc_rack:
            ebLogInfo("*** Configuring VMBackup nodes.conf in dom0s for oci/exacc")
            _nodes_conf_rc = self.mUpdateNodesConf(aOptions=_options, aDom0DomUList=_dpairs)
            if _nodes_conf_rc != 0:
                _log = '*** Could not create nodes.conf in dom0s'
                ebLogError(_log)
                _vmbackupdata["Log"] += _log
                _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                _rc = 1

        ebLogInfo('*** Vmbackup Installation ended')
        return _rc

    # mSortDom0List
    # Sort dom0 list based on the hostname number,
    # needed for ExaCC's case of remote backups.
    # Handles both prod-like hostnames and internal hostnames.
    def mSortDom0List(self, aDom0s):
        def sort_key(dom0):
            hostname = dom0.split(".")[0]
            if hostname[-3] in '0123456789':
                return int(hostname[-3:])
            elif hostname[-2] in '0123456789':
                return int(hostname[-2:])
        return sorted(aDom0s, key=sort_key)

    # mListVMbackup:
    # List available local and remote backups the dom
    def mListVMbackup(self):

        _vmbackupdata = self.mGetVMBackupData()
        _dpairs = self.__ebox.mReturnDom0DomUPair()
        _cmd_str = 'source ' + self.VMBACKUPENV_FILE + '; vmbackup list'
        _vmbackupdata["Log"] = ''
        _rc = 0
        for _dom0, _ in _dpairs:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)
            if not self.mCheckVMbackupInstalled(_node):
                _log =  '*** VMBackup utility is not installed on the dom0: {0}\n'.format(_dom0)
                ebLogError(_log)
                _vmbackupdata["Log"] += _log
                _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                _rc = 1
            else:
                _, _o, _e = _node.mExecuteCmd(_cmd_str)
                _out = _o.read()
                if _out:
                    _log = '*** Available Backups on: {0} \n {1}'.format(_dom0, _out)
                    ebLogInfo(_log)
                    _vmbackupdata["Log"] += _log
                    _vmbackupdata["Exacloud Cmd Status"] = self.PASS
                else:
                    _log = '*** VMBackup error: {0}\n'.format(str(_e.readlines()))
                    ebLogError(_log)
                    _vmbackupdata["Log"] += _log
                    _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                    _rc = 1
        return _rc

    # mListOSSVMbackup:
    # List the available backups from OSS from the DomUs provisioned in the
    # Dom0s part of the cluster of the XML passed as input
    def mListOSSVMbackup(self, aOptions, aReload=None):

        _options = aOptions
        _target_dom0 = None
        _reload = False
        if aOptions.jsonconf is not None:
            _target_dom0 = aOptions.jsonconf.get("dom0", "")
            _reload = aOptions.jsonconf.get("reload", False)
        if aReload:
            ebLogTrace(f"Running reload={aReload} as per argument")
            _reload = aReload

        _vmbackupdata = self.mGetVMBackupData()

        # ECRA may request us to OSSLIST for a given dom0, or
        # for multiple dom0s from a cluster/rack. We need to
        # calculate this. If we receive a cluster we must list
        # for those VMs only
        _dpairs = list()
        if _target_dom0:
            ebLogTrace(f"Fetchng list of ossbackups only for {_target_dom0}")
            _dpairs = [(_target_dom0, None)]
        else:
            _vmbackup_oci_mgr = ebVMBackupOCI(aOptions)
            _dpairs = _vmbackup_oci_mgr.mReturnDom0DomUPair()

        # Enable OSS_BACKUP in vmbackup.conf
        self.mEnableOssVMBackupConfig(aOptions, _dpairs)
        _cmd_str = "source {0} ; vmbackup osslist {1} "
        if _reload:
            _cmd_str += " --reload"
            if ebVMBackupOCI.mIsVMBOSSEnabled(aOptions):
                ebLogInfo(f"Copying user credentials to dom0: {_target_dom0}")
                _vmbackup_oci_mgr = ebVMBackupOCI(aOptions)
                _vmbackup_oci_mgr.mSetupVMBackupDom0Cache()
                if ebVMBackupOCI.mIsForceUsersPrincipalsSet():
                    _vmbackup_oci_mgr.mUploadCustomerUserCredentialsToDom0()
                _vmbackup_oci_mgr.mUploadCertificatesToDom0()
            else:
                ebLogWarn(f"Exacloud did not receive OSS details, yet "
                    f"vmbackup osslis RELOAD is requested")

        _vmbackupdata["Log"] = ''
        _rc = 0
        _results_str = ''
        for _dom0, _domU in _dpairs:

            # If reload is requested, check if the dom0 can reach OCI.
            # If not, skip it
            if _reload and not self.mCheckNodeCanReachOci(_dom0):
                ebLogWarn(f"We detected that {_dom0} can't reach OCI. We will "
                    "not run the OSSLIST reload on it")
                continue

            with connect_to_host(_dom0, get_gcontext()) as _node:
                if not self.mCheckVMbackupInstalled(_node):
                    _log =  '*** VMBackup utility is not installed on the dom0: {0}'.format(_dom0)
                    ebLogError(_log)
                    _results_str += _log
                    _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                    _rc = 1
                    break
                else:
                    # If we have a domU in here, we should list backups
                    # for that VM only
                    if _domU:
                        ebLogInfo(f"Listing backups for {_domU} in {_dom0}")
                        _, _o, _e = _node.mExecuteCmd(
                            _cmd_str.format(self.VMBACKUPENV_FILE, f"--vm {_domU}"))
                    else:
                        ebLogInfo(f"Listing backups for all VMs in {_dom0}")
                        _, _o, _e = _node.mExecuteCmd(
                            _cmd_str.format(self.VMBACKUPENV_FILE, ""))
                    _out = _o.read()
                    if _out:
                        _log = '*** Available Backups on: {0} \n {1}'.format(_dom0, _out)
                        _results_str += _log
                        ebLogInfo(_log)
                        _vmbackupdata["Exacloud Cmd Status"] = self.PASS
                        _rc = 0
                    else:
                        _log = '*** VMBackup error: {0}'.format(str(_e.readlines()))
                        _results_str += _log
                        ebLogError(_log)
                        _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                        _rc = 1
                        break

        self.mDisableOSSVMBackupConfig(aOptions, _dpairs)

        # Restore Log field that ECRA reads
        _vmbackupdata["Log"] = _results_str
        return _rc

    # mGetDom0BackupStatus:
    # Gets the status of the backup operations in a given Dom0
    # by reading the file /EXAVMIMAGES/Backup/OSSMetadata/ossbackup_status.json
    # and returning it to ECRA as-is
    # Returns:
    #   0 - success
    #   1- Error reading file
    #   2 - Payload missing a Dom0 name
    #   3 - Could not connect to the Dom0 provided
    def mGetDom0BackupStatus(self, aOptions):
        _vmbackupdata = self.mGetVMBackupData()

        _dom0 = aOptions.jsonconf.get("dom0", "")
        _rc = 0
        ebLogInfo(f"Exacloud will try to read: '{self.VMBACKUP_STATUS_FILE}' in: '{_dom0}'")

        # Error out if dom0 is None, should not happen since the jsondispatch
        # uses a JSON Schema to validate the payload, but we can have this
        # simple check in here in case we are not being called from the
        # jsondispatch endpoint
        if _dom0 == "":
            _log = f"The payload received doesn't contain any dom0 entry/field"
            ebLogError(_log)
            _vmbackupdata["Log"] = _log
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
            return 2


        # Make sure the dom0 is connectable
        _node = exaBoxNode(get_gcontext())
        if not _node.mIsConnectable(aHost=_dom0, aTimeout=5):
            _log = f"Could not connect to the Dom0: '{_dom0}'"
            ebLogError(_log)
            _vmbackupdata["Log"] = _log
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
            _vmbackupdata["status"] = ""
            return 3

        with connect_to_host(_dom0, get_gcontext()) as _node:

            _cmd = f"/bin/cat {self.VMBACKUP_STATUS_FILE}"
            _out_cat_status = node_exec_cmd(_node, _cmd)

            # Try to read remote status file
            if _out_cat_status.exit_code != 0:
                _log = f'Error reading status file in {_dom0}, output: {_out_cat_status}'
                ebLogError(_log)
                _vmbackupdata["Log"] = _log
                _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                _vmbackupdata["status"] = ""
                _rc = 1
            else:
                _log = f'Success reading status file in {_dom0}, output: {_out_cat_status}'
                ebLogInfo(_log)
                _vmbackupdata["Log"] = _log
                _vmbackupdata["Exacloud Cmd Status"] = self.PASS
                _vmbackupdata["status"] = _out_cat_status.stdout.strip()
                _rc = 0

            # If there is no ongoing process, we assume there is
            # no backup ongoing so we can disable OSS_BACKUP
            # safely. Ideally, OSS_BACKUP in vmbackup.conf should be
            # enabled only when there is an OSS backup in progress
            _tmp_vmbackupdata = copy.deepcopy(_vmbackupdata)
            self.mDisableOSSVMBackupConfig(aOptions, [[_dom0, ""]])
            self.mSetVMBackupData(_tmp_vmbackupdata)


        return _rc


    # mCopyVMBackupUserCredentialsToDom0s
    # Copies the User Principals credentials stored in SiV, to the Dom0s
    # coming in the payload
    def mCopyVMBackupUserCredentialsToDom0s(self, aOptions):

        _vmbackupdata = self.mGetVMBackupData()

        # If the payload has a non-empty vmboss section, we proceeed with
        # copying the VMBackup OCI cache file, and credentials
        if ebVMBackupOCI.mIsVMBOSSEnabled(aOptions):
            _vmbackup_oci_mgr = ebVMBackupOCI(aOptions)
            _vmbackup_oci_mgr.mSetupVMBackupDom0Cache()
            if ebVMBackupOCI.mIsForceUsersPrincipalsSet():
                _vmbackup_oci_mgr.mUploadCustomerUserCredentialsToDom0()
            _vmbackup_oci_mgr.mUploadCertificatesToDom0()
            self.mEnableOssVMBackupConfig(aOptions)
            _log = '*** VMBackup Credentials copy to dom0 succeded'
            _vmbackupdata["Log"] = _log
            ebLogInfo(_log)
            _vmbackupdata["Exacloud Cmd Status"] = self.PASS
            return 0

        # Return error if payload doesn't have OSS fields, as we expect those for this
        # operation
        else:
            _log = ('*** VMBackup Credentials copy to dom0 failed, payload '
                'missing vmbackup information ')
            _vmbackupdata["Log"] = _log
            ebLogError(_log)
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
            return 1

    # mCreateVMbackup:
    # Perform a backup of the existing VMs on the dom0
    def mCreateVMbackup(self, aNode):
        _node = aNode
        _vmbackupdata = self.mGetVMBackupData()
        _rc = 0
        if not self.mCheckVMbackupInstalled(_node):
            _log = '*** VMBackup utility is not installed on the dom0: {0}'.format(_node.mGetHostname())
            ebLogError(_log)
            _vmbackupdata["Log"] = _log
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
            _rc = 1
            raise ExacloudRuntimeError(0x095, 0xA, _log)

        _cmd_str = 'source ' + self.VMBACKUPENV_FILE + '; vmbackup backup'
        ebLogInfo(f"{_node.mGetHostname()} - Triggering backup command, "
            f"this operation may take a while:\n{_cmd_str}")
        _, _o, _e = _node.mExecuteCmd(_cmd_str)
        _out = _o.read()
        _err = _e.read()
        _rc_backup = _node.mGetCmdExitStatus()
        if _rc_backup:
            _log = '*** VMBackup error: {0}'.format(str(_e.readlines()))
            ebLogError(_log)
            _vmbackupdata["Log"] = _log
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
            _rc = 1
            raise ExacloudRuntimeError(0x095, 0xA, _log)

        ebLogInfo("VMBackup tool returned with success, checking status file")
        _log = '*** Backup Created: \n' + str(_out)
        ebLogInfo(_log)

        _cmd = f"/bin/cat {self.VMBACKUP_STATUS_FILE}"
        _out_cat_status = node_exec_cmd(_node, _cmd)

        # If OSS is enabled, ignore failures from VMs not belonging
        # to the current cluster
        _domUs_requested = []
        _options = self.__ebox.mGetArgsOptions()
        if ebVMBackupOCI.mIsVMBOSSEnabled(_options):
            _vmbackup_oci_mgr = ebVMBackupOCI(_options)
            _domUs_requested = [_domU for _, _domU in
                _vmbackup_oci_mgr.mReturnDom0DomUPair() ]
            ebLogInfo(f"VMBackup to OSS enabled in payload, will search "
                f"successful backup entries for {_domUs_requested}")

        # Try to read status file
        try:
            _json_content = {}
            _json_content = json.loads(_out_cat_status.stdout.strip())
        except Exception as e:
            _msg = ("Failed to parse Status file after backup finished "
                f"with success, error \n{e}")
            ebLogError(_msg)
            if ebVMBackupOCI.mIsVMBOSSEnabled(_options):
                raise ExacloudRuntimeError(0x095, 0xA, _msg)

        # Search in the contents for the VM name, a backup with NO
        # sequence number
        try:
            _domU_backups_list = _json_content.get("GuestVMs", {})
            for _domU_name, _entry in _domU_backups_list.items():
                ebLogTrace(f"Backup entry in {_node.mGetHostname()} for {_domU_name} "
                    f"{_entry}")
                _status = _entry.get("CurrentStatus", "UNKOWN")
                if str(_status).lower() != "Succeeded".lower():
                    ebLogTrace(f"Error found on {_entry} for {_domU_name} "
                        "in status file")

                    # Ignore errors from other VMs in case OSS is enabled
                    # This is because the payload will have the info for
                    # the specific VMs to backup
                    if _domUs_requested:
                        if _domU_name not in _domUs_requested:
                            ebLogWarn(f"Ignoring the entry for {_domU_name} "
                                "as not requested in payload")
                        else:
                            _rc = 1
                            ebLogError(f"Error detected on {_entry} for "
                                f"{_domU_name}")

                    # If there are no domUs_requested, it means
                    # the backup is local so we ignore this OSS
                    # status file
                    else:
                        ebLogInfo("No domUs requested to check")
                else:
                    ebLogInfo(f"Success found on {_entry} for {_domU_name}")
        except Exception as e:
            ebLogError(f"General error while parsing the Status File for "
                    f"the backup operation. Error: {e}")
            _rc = 1

        if _rc and ebVMBackupOCI.mIsVMBOSSEnabled(_options):
            _msg = (f"Error detected on {_node.mGetHostname()}, "
                "raising exception")
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x095, 0xA, _msg)

        return _rc

    # Actual execution of the VM backup operation 
    def mRunVMBackup(self, aDom0, aProcessDict):
        # Initalize result dictionary
        _proxy_dict = {
            "start_time": datetime.datetime.now(),
            "end_time": None,
            "elapsed_time": None,
            "return_code": -1,
            "vmbackupdata": self.mGetVMBackupData()
        }
        _proxy_dict["vmbackupdata"]["Log"] = ''
        # Attempt connection to host
        with connect_to_host(aDom0, get_gcontext()) as _node:
            # Run VM backup on host
            _rc = 1
            try:
                _rc = self.mCreateVMbackup(_node)
            except ExacloudRuntimeError as e:
                # If error is raised, mCreateVMbackup will return _rc = 0 anyways, so we need to handle this use case
                _rc = 1
                _msg = f"Detected error while attempting to do VM backup: {e.mGetErrorMsg()}"
                ebLogError(_msg)
                _proxy_dict["vmbackupdata"]["Log"] += _msg + '\n'

            # Calculate execution time
            _end_time = datetime.datetime.now()
            _proxy_dict["end_time"] = _end_time
            _proxy_dict["elapsed_time"] = _end_time - _proxy_dict["start_time"]
            # Set ExaCloud command status
            _proxy_dict["vmbackupdata"]["Exacloud Cmd Status"] = self.FAIL if _rc != 0 else self.PASS
            # Log execution result
            _log = ''
            if _rc != 0:
                _log = f'Error on Dom0: {aDom0}, could not create VM backup'
                ebLogError(_log)
                _rc = 1
            else:
                # Log success
                _log = f'VM backup created for: {aDom0} '
                ebLogInfo(_log)
                _rc = 0
            _proxy_dict["vmbackupdata"]["Log"] += _log
            # Set return code
            _proxy_dict["return_code"] = _rc
            aProcessDict[aDom0] = _proxy_dict

    # mVMbackupAll:
    # Perform a backup of the existing VMs on all dom0s, secuentially
    def mVMbackupAll(self, aOptions):
        _dpairs = self.__ebox.mReturnDom0DomUPair()

        # If the payload has a non-empty vmboss section, we proceeed with the VMBackup
        # OCI cache file update, and credentials population
        if ebVMBackupOCI.mIsVMBOSSEnabled(aOptions):

            # We need to make sure there is no ongoing vmbackup process
            # before we go past this point, otherwise the ongoing
            # vmbackup process in the dom0s might finish and
            # delete the Dom0 Cache file which will make
            # the subsequent backup to OSS fail
            for _dom0, _ in _dpairs:
                with connect_to_host(_dom0, get_gcontext()) as _node:

                    # Wait for any ongoing processes
                    _timeout_max_seconds = get_gcontext().mGetConfigOptions().get(
                        "vmbackup", {}).get("max_timeout", 28800)
                    self.mCheckRemoteProcessOngoing(
                        _node, int(_timeout_max_seconds))

            _vmbackup_oci_mgr = ebVMBackupOCI(aOptions)
            _vmbackup_oci_mgr.mSetupVMBackupDom0Cache()
            if ebVMBackupOCI.mIsForceUsersPrincipalsSet():
                _vmbackup_oci_mgr.mUploadCustomerUserCredentialsToDom0()
            _vmbackup_oci_mgr.mUploadCertificatesToDom0()
            _vmbackup_oci_mgr.mSetupVMBackupClusterBucket()
            self.mEnableOssVMBackupConfig(aOptions)

        #Update BackupTool if needed
        if not self._is_exacc_rack:
            try:
                for _dom0, _ in _dpairs:
                    _rc = self.mInstallNewestVMBackupTool(_dom0, aOptions)
                    ebLogInfo(f"VM backup tool installed newest for {_dom0} ended with code: {_rc}")
            except Exception as e:
                _warn = "Error found while trying to update VM backup tool"
                ebLogWarn(_warn)
        
        # Set process manager, process dictionary and init variables
        ebLogInfo("Adding VM backup processes to be ran in parallel.")
        _procManager = ProcessManager()
        _procDict = _procManager.mGetManager().dict()
        _defaultMaxTime = get_gcontext().mGetConfigOptions().get("vmbackup", {}).get("default_timeout", 18000) # Set timeout to 5 hours per backup as default value
        _maxTime = get_gcontext().mGetConfigOptions().get("vmbackup", {}).get("max_timeout", _defaultMaxTime)

        # Add tasks to parallel processing manager
        for _dom0, _ in _dpairs:
            _task = ProcessStructure(self.mRunVMBackup, aArgs=[_dom0, _procDict], aId=_dom0)
            _task.mSetMaxExecutionTime(int(_maxTime))
            _task.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_task)
            ebLogInfo(f"VM backup process for dom0: {_dom0} created.")

        # Wait for processes to end
        ebLogInfo("Waiting for VM backup processes to end. This might take a while.")
        _procManager.mJoinProcess()

        # Once all processes finish, check for dom0s with errors
        _error_dom0s = []
        for _key, _val in _procDict.items():
            # Skip if return code is 0
            if _val['return_code'] != 0:
                _error_dom0s.append(_key)

        if ebVMBackupOCI.mIsVMBOSSEnabled(aOptions):
            self.mDisableOSSVMBackupConfig(aOptions)

        # Raise error in case of failure in any VM backup operation.
        # This is needed because an Exception raised by a Process won't be immediately reflected.
        if len(_error_dom0s) > 0:
            _msg = f"VM backup ended with errors in the following dom0s: {_error_dom0s}."
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x095, 0xA, _msg)

        # If we reach this point this means we didn't get any errors while running VMBOSS
        ebLogInfo("VM backup operation completed successfully on all dom0s.")
        return 0

    def mInstallNewestVMBackupTool(self, aHostname, aOptions):

        # Get timeout
        _timeout_max_seconds = get_gcontext().mGetConfigOptions().get(
            "vmbackup", {}).get("max_timeout", 28800)

        with connect_to_host(aHostname, get_gcontext()) as _node:
            _options = aOptions
            # Check if vmbackup is already installed
            _vmbackup_installed = self.mCheckVMbackupInstalled(_node)
            ebLogTrace(f"Log from vmbackup operation: {self.mGetVMBackupData()}")
            
            # Try to install tool if it's not installed yet
            if not _vmbackup_installed:
                ebLogInfo(f"VMBackup tool was not detected in {aHostname}, "
                    "attempting to install it")
                _rc = self.mInstallVMbackupOnDom0(_options, _node)
                if _rc:
                    _msg = ("An error happened while trying to install the "
                        f"vmbackup tool in {aHostname}")
                    ebLogError(_msg)
                return _rc

            # If it is, check the version it has to compare it against
            # the version present currently in Exacloud images/ directory, 
            # which is expected to be in the format:
            # images/release-vmbackup-25.2.2.1.5+250905.0159.tgz

            # We need to compare the pattern that represents
            # the series and the date of the tool tarball.
            # If the version is an empty string, we assume an error
            # happened so we attempt to install the tool anyways
            _node_vmbackup_series, _node_vmbackup_date = \
                    self.mGetVMBackupVersion(_node)

            if _node_vmbackup_series == "":
                ebLogInfo("Unable to determine the version of the tool "
                    f"currently installed in {aHostname}, attempting to "
                    "check if there's any ongoing process before installing it.")

                # Wait for any ongoing processes
                if self.mCheckRemoteProcessOngoing(_node, int(_timeout_max_seconds)):
                    _msg = ("Exacloud detected an ongoing vmbackup "
                            f"process is running the remote node {aHostname}. We can't"
                            "attempt to install the vmbackup tool while a vmbackup "
                            "process is ongoing. You have two options:\n"
                            "1) You retry this operation once the vmbackup process "
                            "on this node has finished; you can review if on ongoing "
                            "vmbackup process is running in the node with the "
                            "command: '$pgrep vmbackup -a'.\n"
                            "2) You can set to 'False' the field "
                            "'enable_vmbackup_install' in "
                            "'$EC_ROOT/config/exabox.conf',and retry this step. "
                            "Please be aware that to for Exacloud to detect the new "
                            "change in exabox.conf, you need to reload the Exacloud "
                            "workers, you can use '$EC_ROOT/bin/exacloud --agent "
                            "reload' . This reload operation WILL NOT interfere with "
                            "any Exacloud ongoing operation. Disabling this option "
                            "will cause Exacloud to NOT install the vmbackup tool")
                    ebLogError(_msg)
                    return 1

                # If no process is running, install it
                ebLogInfo("No ongoing vmbackup process was detected in "
                    f"{aHostname}, attempting to install it")
                _rc = self.mInstallVMbackupOnDom0(_options, _node)
                ebLogTrace("Log from vmbackup operation: "
                    f"{self.mGetVMBackupData()}")
                if  _rc != 0:
                    _msg = ("An error happened while trying to install the "
                        f"vmbackup tool in {aHostname}")
                    ebLogError(_msg)
                return _rc

            # Get version we have currently of the tool, by using
            # the name of the tool file, example is:
            # exacloud/images/release-vmbackup-MAIN_230109.0900.tgz
            _local_vmbackup_series, _local_vmbackup_date = \
                    self.mGetLocalVMBackupVersion()

            # If version is different, check if a vmbackup process is running
            if (_local_vmbackup_series != _node_vmbackup_series or
                    _local_vmbackup_date != _node_vmbackup_date):

                ebLogInfo("Exacloud detected the current installed vmbackup "
                    f"tool version ({_node_vmbackup_series}-"
                    f"{_node_vmbackup_date}) in {aHostname} is "
                    "different than the local version of the tool: "
                    f"{_local_vmbackup_series}-{_local_vmbackup_date}. We'll "
                    "check if an ongoing process is ongoing, if there is "
                    "Exacloud will raise an Exception, wait for the current "
                    "vmbackup process and "
                    "retry the operation. If we don't detect an ongoing "
                    "process we'll attempt to install the new vmbackup tool")

                if self.mCheckRemoteProcessOngoing(_node, int(_timeout_max_seconds)):
                    _msg = ("Exacloud detected an ongoing vmbackup "
                            f"process is running the remote node {aHostname}. We can't"
                            "attempt to install the vmbackup tool while a vmbackup "
                            "process is ongoing. You have two options:\n"
                            "1) You retry this operation once the vmbackup process "
                            "on this node has finished; you can review if on ongoing "
                            "vmbackup process is running in the node with the "
                            "command: '$pgrep vmbackup -a'.\n"
                            "2) You can set to 'False' the field "
                            "'enable_vmbackup_install' in "
                            "'$EC_ROOT/config/exabox.conf',and retry this step. "
                            "Please be aware that to for Exacloud to detect the new "
                            "change in exabox.conf, you need to reload the Exacloud "
                            "workers, you can use '$EC_ROOT/bin/exacloud --agent "
                            "reload' . This reload operation WILL NOT interfere with "
                            "any Exacloud ongoing operation. Disabling this option "
                            "will cause Exacloud to NOT install the vmbackup tool")
                    ebLogError(_msg)
                    return 1

                # If no process is running, install it
                ebLogInfo(f"No ongoing vmbackup process was detected in "
                    f"{aHostname}, attempting to install it")
                _rc = self.mInstallVMbackupOnDom0(_options, _node)
                ebLogTrace("Log from vmbackup operation: "
                    f"{self.mGetVMBackupData()}")
                if _rc:
                    _msg = ("An error happened while trying to install the "
                        f"vmbackup tool in {aHostname}")
                    ebLogError(_msg)
                return _rc

            ebLogInfo("Exacloud detected the current installed vmbackup "
                f"tool version ({_node_vmbackup_series}-"
                f"{_node_vmbackup_date}) in {aHostname} is "
                "same as the local version of the tool: "
                f"{_local_vmbackup_series}-{_local_vmbackup_date}."
                "No need to install new tool")
        return 0

    # mTakeBackgrounBackupHost
    # Trigger a backup of the existing VMs on a given dom0,
    # which we'll read from the payload.
    # Depending on the parameter 'ondemand' (True) we may trigger the backup in
    # background and return as soon as possible, or (False) wait for the
    # backup completion
    def mTriggerBackgrounBackupHost(self, aOptions):

        _vmbackupdata = self.mGetVMBackupData()
        _vmbackupdata["Log"] = ''

        # Parse the payload to get Dom0
        _dom0 = aOptions.jsonconf.get("dom0", "")

        # Error out if dom0 is None, should not happen since the jsondispatch
        # uses a JSON Schema to validate the payload, but we can have this
        # simple check in here in case we are not being called from the
        # jsondispatch endpoint
        if _dom0 == "":
            _log = f"The payload received doesn't contain any dom0 entry/field"
            ebLogError(_log)
            _vmbackupdata["Log"] += _log
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
            return 1

        # Make sure the Dom0 is connectable
        _node = exaBoxNode(get_gcontext())
        if not _node.mIsConnectable(aHost=_dom0, aTimeout=5):
            _log = f"Could not connect to the Dom0: '{_dom0}'"
            ebLogError(_log)
            _vmbackupdata["Log"] = _log
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
            return 3

        # If the payload has a non-empty vmboss section, we proceeed with the VMBackup
        # OCI cache file update, and credentials population
        if ebVMBackupOCI.mIsVMBOSSEnabled(aOptions):

            # We need to make sure there is no ongoing vmbackup process
            # before we go past this point, otherwise the ongoing
            # vmbackup process in the dom0s might finish and
            # delete the Dom0 Cache file which will make
            # the subsequent backup to OSS fail
            with connect_to_host(_dom0, get_gcontext()) as _node:

                # Wait for any ongoing processes
                _timeout_max_seconds = get_gcontext().mGetConfigOptions().get(
                    "vmbackup", {}).get("max_timeout", 28800)
                self.mCheckRemoteProcessOngoing(
                        _node, int(_timeout_max_seconds))

            _vmbackup_oci_mgr = ebVMBackupOCI(aOptions)
            _vmbackup_oci_mgr.mSetupVMBackupDom0Cache()
            if ebVMBackupOCI.mIsForceUsersPrincipalsSet():
                _vmbackup_oci_mgr.mUploadCustomerUserCredentialsToDom0()
            _vmbackup_oci_mgr.mUploadCertificatesToDom0()
            _vmbackup_oci_mgr.mSetupVMBackupClusterBucket()
            self.mEnableOssVMBackupConfig(aOptions)
        
        # Try to install/upgrade VM backup tool
        _rc = self.mInstallNewestVMBackupTool(_dom0, aOptions)
        ebLogInfo(f"VM backup tool install ended with code: {_rc}")

        # Connect to aDom0
        with connect_to_host(_dom0, get_gcontext()) as _node:

            # Error out if tool is still not installed even after attempt
            if not self.mCheckVMbackupInstalled(_node):
                _log =  ("*** VMBackup utility is not installed on the dom0: "
                    "{0}".format(_dom0))
                ebLogError(_log)
                _vmbackupdata["Log"] += _log
                _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                return 1


            # The 'ondemand' flag comes from aOptions.ondemand
            # If ondemand is 'false', use nohup, and spawn the process in such a
            # way that it ignores signals/detaches and has 1 as PPID
            # If ondemad is 'true', wait for the process completion,
            # If ondemand is missing, the default value is 'false', so if
            # missing we'll trigger in background and return ASAP
            _bin_nohup = node_cmd_abs_path_check(_node, "nohup", sbin=True)
            _background_enable = "&"

            _ondemand = aOptions.ondemand
            if _ondemand and str(_ondemand).lower() == "true":
                _bin_nohup = ""
                _background_enable = ""

            ebLogTrace(f"Ondemand flag for backup is: {_ondemand}")

            _cmd_backup_str = (f'{_bin_nohup} /bin/sh -c '
                f'"source {self.VMBACKUPENV_FILE} && '
                f'vmbackup backup --localtooci 2> /dev/null " {_background_enable}')
            ebLogTrace(_cmd_backup_str)

            # NOTE: don't use node_exec_cmd in here if using 'nohup' and '&'
            # since 'node_exec_cmd' will force a 'read()' on the stream obj
            # and we saw issues when doing a 'read()' when using 'nohup' and
            # '&'. Suspicious is that the process gets spawned without
            # a tty and that is something that causes issues with the 'read()'
            # If we need the stdout of this at some point we would need do it
            # without using read() on the paramiko channel more than likely
            _node.mExecuteCmd(_cmd_backup_str)

            # The exit code we check in here is from 'nohup', not from
            # the backup itself (assuming nohup was used)
            _rc = _node.mGetCmdExitStatus()

            _result_str = ""
            if _rc == 0:
                _log = (f"*** Successfully triggered the backup of all the "
                    f"VMs from {_dom0}")
                ebLogInfo(_log)
                _result_str = _log
                _vmbackupdata["Exacloud Cmd Status"] = self.PASS
                _rc = 0
            else:
                _log = (f"*** Error on {_dom0}, failed to trigger the "
                    f"backup of the VMs from {_dom0}")
                ebLogError(_log)
                _result_str = _log
                _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                _rc = 1

            if ebVMBackupOCI.mIsVMBOSSEnabled(aOptions):
                ebLogWarn(f"Will not disable '{self.SET_PARAM_OSS_BACKUP}' "
                    "to let the backup continue")

            # Restore vmbackup Log result
            _vmbackupdata["Log"] = _result_str

            return _rc

    # mTriggerGoldenBackup
    # Reads the payload to get a list of Dom0s and DomUs.
    # It populates the VMBackup Dom0 Cache file and
    # then triggers the Completion steps for the Golden
    # Backup
    def mTriggerGoldenBackup(self, aOptions):
        _vmbackupdata = self.mGetVMBackupData()
        _vmbackupdata["Log"] = ''

        # Make sure payload has OCI values
        if not ebVMBackupOCI.mIsVMBOSSEnabled(aOptions):
            _log = (f"We expect the vmbackup to OSS details to be present in "
                "the payload to complete the Golden Backup steps. Please "
                "retry sending 'vmboss_map' field in the payload ")
            ebLogError(_log)
            _vmbackupdata["Log"] += _log
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
            return 1

        # Get max timeout for taking the golden backup, if not set
        # we use 3600 seconds as default
        _timeout_default = "3600"
        _timeout_max_seconds =  get_gcontext().mGetConfigOptions().get(
                "vmbackup", {}).get("max_gold_backup_timeout", _timeout_default)
        try:
            _timeout_max_seconds = int(_timeout_max_seconds)
        except Exception as e:
            _warn = ("Detected invalid value for "
                f"'max_timeout_backup': '{_timeout_max_seconds}'"
                f". Using default value: '{_timeout_default}'."
                f"Error: '{e}'")
            ebLogWarn(_warn)
            _timeout_max_seconds = int(_timeout_default)

        ebLogInfo("Setting max timeout for golden backup to: "
            f"'{_timeout_max_seconds}'")

        # Check if all nodes have the tool installed
        _vmbackup_oci_mgr = ebVMBackupOCI(aOptions)
        _nodes = _vmbackup_oci_mgr.mReturnDom0DomUPair()
        for _dom0, _domU in _nodes:

            with connect_to_host(_dom0, get_gcontext()) as _node:
                if not self.mCheckVMbackupInstalled(_node):
                    _log =  ("*** VMBackup utility is not installed on the dom0: "
                        "{0}".format(_dom0))
                    ebLogError(_log)
                    _vmbackupdata["Log"] += _log
                    _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                    return 1

                # Wait for any other vmbackup processes that may be
                # running
                # Wait for other backup operations ongoing at most aTimeout
                self.mCheckRemoteProcessOngoing(_node, int(_timeout_max_seconds))

        # Populate the JSON file with OCI values in the Dom0s
        _vmbackup_oci_mgr = ebVMBackupOCI(aOptions)
        _vmbackup_oci_mgr.mSetupVMBackupDom0Cache()
        if ebVMBackupOCI.mIsForceUsersPrincipalsSet():
            _vmbackup_oci_mgr.mUploadCustomerUserCredentialsToDom0()
        _vmbackup_oci_mgr.mUploadCertificatesToDom0()
        self.mEnableOssVMBackupConfig(aOptions)


        # Trigger in parallel
        ebLogTrace("Will spawn workers to complete Golden Backup of: "
            f"'{_nodes}'")

        # Create a pool of processes Executor
        _results_map = {}
        with futures.ProcessPoolExecutor() as _executor:

            # Submit process callback and store them in _list_processes_spawned
            _list_processes_spawned = []
            for _dom0, _domU in _nodes:

                _list_processes_spawned.append((_executor.submit(
                    self.mCompleteGoldenBackupCallback,
                        _dom0, _domU, _timeout_max_seconds),
                    _dom0, _domU))

            _time_start = datetime.datetime.now()

            # Wait response from each process at most _timeout_max_seconds
            # after _time_start
            _list_results = []
            _list_processes_failed = []
            for _process, *_args in _list_processes_spawned:
                try:

                    _dom0, _domU = _args
                    _result = _process.result(timeout=_timeout_max_seconds)

                except futures._base.TimeoutError as e:
                    ebLogError(f"Timeout happened while taking the Golden VM Backup. "
                        f"Process args: '{_args}'. We'll terminate all ongoing subprocess.")
                    _list_processes_failed.append(_args)

                    # During a timeout, if the tool receives a SIGKILL it will not
                    # cleanup the ociconf directory, we will remote it in here
                    # If we change which args are hold on *args above, we must change below
                    # line as well
                    _cmd_str = "/bin/rm -rf /opt/oracle/vmbackup/ociconf"
                    with connect_to_host(_dom0, get_gcontext()) as _node:
                        ebLogInfo(f"Cleaning up 'ociconf' dir in {_dom0}")
                        _output_vmbackup = node_exec_cmd(_node, _cmd_str)
                    _time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    _results_map[_domU] = {
                            "goldenbackup": "False",
                            "date": _time
                            }

                # If a process fails for non-timeout reason, we let the rest
                # of the processes to keep going, since we did not trigger a SIGKILL
                # it's the tool responsibility to clean ociconf
                except Exception as e:
                    ebLogError(f"An Error happened while taking up the "
                        f"Golden VM Backup image. Process args: '{_args}'."
                        f"Exception is: '{e}'")
                    _list_processes_failed.append(_args)
                    _time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    _results_map[_domU] = {
                            "goldenbackup": "False",
                            "date": _time
                            }

                else:
                    ebLogInfo("Exacloud completed the Golden VM Backup "
                        f"image with process args: '{_args}'")
                    _time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    _results_map[_domU] = {
                            "goldenbackup": "True",
                            "date": _time
                            }

        if ebVMBackupOCI.mIsVMBOSSEnabled(aOptions):
            self.mDisableOSSVMBackupConfig(aOptions, _nodes)

        _vmbackupdata["Log"]  = _results_map
        if _list_processes_failed:
            _msg = ("An error happened while one or more Golden "
                f"VMBackup's happened, errors: {_list_processes_failed}")
            ebLogError(_msg)
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
            return 1

        else:
            _msg = ("Completed the Golden Backup")
            ebLogInfo(_msg)
            _vmbackupdata["Exacloud Cmd Status"] = self.PASS
            return 0


    @staticmethod
    def mCompleteGoldenBackupCallback(aDom0, aDomU, aTimeout):
        """
        This method executes the callback to trigger the Completion steps
        of the Golden Backup, in other words we will complete the
            - Tarring
            - Encryption
            - Push to Object Storage

        :param aDom0: a string representing the Dom0 where to trigger the backup
        :param aDomU: a string representing the DomU of which to take the
            golden vm backup
        :param aTimeout: an integer representing how much seconds to set as
            timeout for the callback execution

        :raises ExacloudRuntimeError: If the golden backup tool was not
            generated ok. This is a combination of:
                -- The vmbackup tool having exit-code 0 when running the Golden
                    Backup
                -- If the tool is successful, we verify that a backup entry
                    exists in the Dom0 OSS cache file. The Golden backup entry
                    is expected to NOT have any Sequence number, e.g.

             "luks-patching-test-nglua1.client.exaclouddev.oraclevcn.com": [
                 [
                     "luks-patching-test-nglua1.client.exaclouddev.oraclevcn.com.tar",
                     "2023-09-28-07-10-50"
                 ],
                 [
                     "luks-patching-test-nglua1.client.exaclouddev.oraclevcn.com_SEQ1.tar",
                     "2023-09-28-21-12-34"
                 ]
             ]

        """

        ebLogInfo("Triggering golden vmbackup completiong steps of: "
            f"'{aDomU}' from: '{aDom0}'")

        _cmd_str = (f"source {ebCluManageVMBackup.VMBACKUPENV_FILE}; "
            f"timeout {aTimeout} vmbackup backup --localtooci --vm {aDomU} "
            "--gold")
        ebLogTrace(f"Golden Backup Completion in: '{aDom0}', this operation "
            f"may take some time. Timeout set for '{aTimeout}' seconds...")

        with connect_to_host(aDom0, get_gcontext()) as _node:

            _output_vmbackup = node_exec_cmd(_node, _cmd_str)
            ebLogTrace(f"VMBackup output in: '{aDom0}': '{_output_vmbackup}'")

            if _output_vmbackup.exit_code != 0:
                ebLogWarn("Failed to complete the Golden VMBackup "
                    f"process in: '{aDom0}' for: '{aDomU}'. We will try to "
                    "check the OSS cache file in the dom0 to verify")

            else:
                ebLogInfo("Exacloud completed the Golden VMBackup process "
                    f"in: '{aDom0}' for: '{aDomU}' with success. We will try "
                    "to check the OSS cache file in the dom0 to verify")

            # The tool finished, but we need to confirm
            # by looking at the oss cache file in the Dom0s
            # This file read is very quick, no need to make
            # parallel for now
            _cache_file = "/opt/python-vmbackup/oss/backupdetails.dat"
            _output_oss_cache = node_exec_cmd(_node, f"/bin/cat {_cache_file}")

            # This file should be in JSON, try to parse
            try:
                _json_content = json.loads(_output_oss_cache.stdout.strip())
            except Exception as e:
                _msg = ("Failed to parse OSS Cache file, error \n{e}")
                ebLogError(_msg)
                raise ExacloudRuntimeError(0x095, 0xA, _msg)

            # Search in the contents for the VM name, a backup with NO
            # sequence number
            _domU_backups_list = _json_content.get(aDomU)
            _expected_backup = f"{aDomU}.tar"
            ebLogInfo(f"Looking for entry: '{_expected_backup}' in: "
                f"'{_cache_file}' of '{aDom0}'")
            for _domU_backup_entry in _domU_backups_list:

                if _expected_backup in _domU_backup_entry:
                    ebLogInfo(f"Found entry: '{_expected_backup}' in: "
                        f"'{_cache_file}' of '{aDom0}'")
                    return 0

            _msg = ("We did not detect any Golden Backup entry in the "
                f"cache file: '{_cache_file}' of the '{aDom0}'")
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x095, 0xA, _msg)


    # mDisableVMBackupCronJob:
    # Will read the crontab file from aNode and will try to check if an entry
    # for 'vmbackup' exists. If there is such entry and is NOT commented (i.e.
    # starts with '#') we'll try to comment it out
    # Returns True on success, i.e. no entry is present on the crontab
    #   or False if we where unable to remove an entry
    def mDisableVMBackupCronJob(self, aNode):
        _vmbackupdata = self.mGetVMBackupData()
        _vmbackupdata["Log"] = ''

        # We'll review directly the 'root' spool crontab file
        # in the same way the method 'mSetVMBackupCronJob' does it
        _cron_file_loc = "/var/spool/cron/root"

        # If the file doesn't exist we can exit right away
        if not aNode.mFileExists(_cron_file_loc):
            _log = (f"The file: '{_cron_file_loc}' doesn't exist on: "
                f"{aNode.mGetHostname()}'. No cronjob to delete")
            ebLogInfo(_log)
            _vmbackupdata["Log"] += _log
            _vmbackupdata["Exacloud Cmd Status"] = self.PASS
            return True

        # The entry looks like this:
        # 0 4 * * sun /opt/oracle/vmbackup/sched_vmb.sh
        _cron_entry_identifier = "sched_vmb.sh"

        # Match:
        # ^[^#] .*sched_vmb.sh
        # Starts with anything but a comment, and has the pattern 'sched_vmb.sh'
        #
        # Replace with:
        # #&
        # A character '#' and the rest of the matched line
        _cmd = f'/bin/sed -Ei "s/^[^#].*sched_vmb.sh/#&/" {_cron_file_loc}'
        _out_sed = node_exec_cmd(aNode, _cmd)
        ebLogTrace(_out_sed)

        # Since the exit code of 'sed' will not tell us if a replace happened
        # we use 'grep' to verify using the same regex
        _cmd = f'/bin/grep -E "^[^#].*sched" {_cron_file_loc}'
        _out_grep = node_exec_cmd(aNode, _cmd)
        ebLogTrace(_out_grep)

        if _out_grep.exit_code == 0:
            _log = (f"Exacloud detected an entry in: '{_cron_file_loc}' which "
                f"we were unable to comment: {_out_grep}. As WA please make "
                f"sure tha there is no entry on the '{_cron_file_loc}' with "
                f"the entry: '{_cron_entry_identifier}' and retry the "
                "operation")
            ebLogError(_log)
            _vmbackupdata["Log"] += _log
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
            return False

        _log = (f"Exacloud detected 0 entries on: '{_cron_file_loc}' related "
            f"to vmbackup, as expected")
        ebLogInfo(_log)
        _vmbackupdata["Log"] += _log
        _vmbackupdata["Exacloud Cmd Status"] = self.PASS
        return True

    # mCleanAllVMbackup:
    # Delete all available local and remote backups on the dom0
    # If aCleanGoldBackup is True, we must populate the Dom0s with
    # the OCI values needed by the tool to clean the golden backup
    # in the Object Storage, i.e. Golden Backup requires
    # OSS info to be on the payload
    def mCleanVMbackup(self, aOptions, aListOfDom0DomUPairs, aCleanGoldBackup):

        ebLogTrace(f"Running Clean VMBackup, cleaning goldn backups flag: '{aCleanGoldBackup}'")

        _vmbackupdata = self.mGetVMBackupData()
        _vmbackupdata["Log"] = ''
        if aListOfDom0DomUPairs is None or type(aListOfDom0DomUPairs) != list or len(aListOfDom0DomUPairs) == 0:
            _log = "List of dom0_domU pair cannot be None or empty."
            ebLogError(_log)
            _vmbackupdata["Log"] += _log
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
            return

        # If the payload has a non-empty vmboss section, we proceeed with the VMBackup
        # OCI cache file update, and credentials population
        if ebVMBackupOCI.mIsVMBOSSEnabled(aOptions):

            # Bug 37048143
            # If VMBackup OSS is enabled and the tool is missing,
            # we will install it to make sure we cleanup
            # any possible stale backups
            for _dom0, _domU in aListOfDom0DomUPairs:
                with connect_to_host(_dom0, get_gcontext()) as _node:
                    if not self.mCheckVMbackupInstalled(_node):
                        ebLogWarn(f"Trying to cleanup OSS backups in {_dom0} for "
                            f"{_domU} we detected the tool is not installed, "
                            "we'll install it")
                        self.mInstallVMbackupOnDom0(aOptions, _node)
                    else:
                        ebLogTrace(f"VMbackup tool already installed in {_dom0}")

            _vmbackup_oci_mgr = ebVMBackupOCI(aOptions)
            _vmbackup_oci_mgr.mSetupVMBackupDom0Cache()
            if ebVMBackupOCI.mIsForceUsersPrincipalsSet():
                _vmbackup_oci_mgr.mUploadCustomerUserCredentialsToDom0()
            _vmbackup_oci_mgr.mUploadCertificatesToDom0()
            self.mEnableOssVMBackupConfig(aOptions)

        # If the payload does not have vmboss section and we want to clean Golden backups,
        # we must error out as cleaning Golden backups requires the OCI info
        elif aCleanGoldBackup is True:
            _log = ("Cleaning golden Backup requires OSS info on the payload, "
                f"and we detected no info")
            ebLogError(_log)
            _vmbackupdata["Log"] += _log
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
            return

        # Check if we should trigger the clean with the --gold flag
        if aCleanGoldBackup is True:
            _gold_flag = "--gold"
        else:
            _gold_flag = ""

        # Trigger of the cleanup operation with the tool on the dom0s
        _dpairs = aListOfDom0DomUPairs
        for _dom0, _domU in _dpairs:
            _cmd_str = f"source {self.VMBACKUPENV_FILE}; vmbackup cleanall {_gold_flag} --vm {_domU}"
            with connect_to_host(_dom0, get_gcontext()) as _node:
                if not self.mCheckVMbackupInstalled(_node):
                    _log =  '*** VMBackup utility is not installed on the dom0: {0}'.format(_dom0)
                    ebLogError(_log)
                    _vmbackupdata["Log"] += _log
                    _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                else:
                    _, _o, _e = _node.mExecuteCmd(_cmd_str)
                    _out = _o.read()
                    if _node.mGetCmdExitStatus() == 0:
                        _log = f"*** Successfully cleaned all backups on {_dom0} for the VM {_domU}"
                        ebLogInfo(_log)
                        _vmbackupdata["Log"] += _log
                        _vmbackupdata["Exacloud Cmd Status"] = self.PASS
                    else:
                        _log = f"*** Error on {_dom0}, cannot clean Backups for VM: {_domU}, error {str(_e.readlines())}"
                        ebLogError(_log)
                        _vmbackupdata["Log"] += _log
                        _vmbackupdata["Exacloud Cmd Status"] = self.FAIL

        if ebVMBackupOCI.mIsVMBOSSEnabled(aOptions):
            self.mDisableOSSVMBackupConfig(aOptions, _dpairs)

    # mCleanAllVMbackup:
    # Delete all available local and remote backups on the dom0
    def mCleanAllVMbackup(self):

        _vmbackupdata = self.mGetVMBackupData()
        _dpairs = self.__ebox.mReturnDom0DomUPair()
        _cmd_str = 'source ' + self.VMBACKUPENV_FILE + '; vmbackup cleanall'
        _vmbackupdata["Log"] = ''
        _rc = 0
        for _dom0, _ in _dpairs:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)
            if not self.mCheckVMbackupInstalled(_node):
                _log =  '*** VMBackup utility is not installed on the dom0: {0}'.format(_dom0)
                ebLogError(_log)
                _vmbackupdata["Log"] += _log
                _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                _node.mDisconnect()
                _rc = 1
                return _rc
            else:
                _, _o, _e = _node.mExecuteCmd(_cmd_str)
                _out = _o.read()
                if _node.mGetCmdExitStatus() == 0:
                    _log = '*** Successfully clean all backups on the dom0: {0}'.format(_dom0)
                    ebLogInfo(_log)
                    _vmbackupdata["Log"] += _log
                    _vmbackupdata["Exacloud Cmd Status"] = self.PASS
                    _node.mDisconnect()
                    _rc = 0
                else:
                    _log = '*** Error on {0}, cannot clean Backups, error {1}'.format(_dom0, str(_e.readlines()))
                    ebLogError(_log)
                    _vmbackupdata["Log"] += _log
                    _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                    _node.mDisconnect()
                    _rc = 1
        return _rc


    # mRestoreVMbackup:
    # Restore available local or remote backups the dom0
    def mRestoreVMbackup(self, aOptions, aNode=None, aVmName=None):

        _options = aOptions
        _vmbackupdata = self.mGetVMBackupData()
        _rc = 0
        _node_recovery = False
        _recoveryObj = None

        if aNode is None or aVmName is None:
            if aOptions.jsonconf is None:
                _log = '*** VMBackup Restore payload required'
                _vmbackupdata["Log"] = _log
                ebLogError(_log)
                _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                raise ExacloudRuntimeError(0x0763, 0xA, "Failed to access/read vmbackup configuration file")

            _json = aOptions.jsonconf

            try:
                _dom0 = _json["dom0"]
                _vm_name = _json["vm_name"]
                _local = _json["local"]
                _dest = ""
                _jconf_keys = list(_json.keys())
                _forceapply = False
                if _jconf_keys is not None and "forceapply" in _jconf_keys:
                    _forceapply = _json["forceapply"]

                if _jconf_keys is not None and 'node_recovery_flow' in _jconf_keys and _json['node_recovery_flow'] == True:

                    #Create NodeRecovery object
                    _recoveryObj = NodeRecovery(self.__ebox, aOptions)

                    _node_recovery = True
                    _node = exaBoxNode(get_gcontext())
                    _node.mConnect(aHost=_dom0)

                    if not self.mCheckVMbackupInstalled(_node):
                        _log = '*** VMBackup utility is not installed on the dom0: {0}'.format(_dom0)
                        ebLogError(_log)
                        _vmbackupdata["Log"] = _log
                        _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                        _node.mDisconnect()
                        raise ExacloudRuntimeError(0x0822, 0xA, 'VMBackup utility is not installed')

                    _available_bkp = self.mCheckAvailableVMbackups(_node, _vm_name)
                    if _available_bkp is False:
                        _log = '*** Error, not available backups for restore'
                        ebLogError(_log)
                        _vmbackupdata["Log"] = _log
                        _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                        raise ExacloudRuntimeError(0x0823, 0xA, 'No available backups for VMBackup restore')

                    _seq_list = [ ast.literal_eval(_seq) for _seq in _available_bkp ]
                    _backup_seq = str(max(_seq_list))
                    ebLogInfo(f"*** VM backup is available with sequence:{_backup_seq}")
                    _node.mDisconnect()
                    _dest  = '/EXAVMIMAGES/GuestImages/{0}'.format(_vm_name)
                    aVmName = _vm_name

                    #Fetch client/backup information from XML
                    _dom0_bonding = aOptions.jsonconf.get('dom0_bonding', False)
                    _payload = _recoveryObj.mFetchNetworkInfo(_dom0, _vm_name, _dom0_bonding)
                    _recoveryObj.mExecutePreVMStep(_dom0, _vm_name, _payload)

                    #VM should be registered & in shutdown state before invoking VMBackup Restore
                    _rc = _recoveryObj.mRegisterVM(_dom0, _vm_name)
                    if _rc:
                        _recoveryObj.mDeleteVM(_dom0, _vm_name, aNodeRecovery=True)
                        ebLogError(f"*** Failed to create VM:{_vm_name} on dom0:{_dom0}")
                        raise ExacloudRuntimeError(0x0411, 0xA, 'VM was not able to start')

                    # Configure bonding
                    _recoveryObj.mExecutePostVMStep(_dom0, _vm_name, _payload)

                    #Fetch DomU Admin Network Details
                    _recoveryObj.mFetchAdminNWDetails(_dom0, _vm_name)

                    _rc = _recoveryObj.mShutdownVM(_dom0, _vm_name)
                    if _rc not in [0, 0x0411, 0x0454]:
                        _recoveryObj.mDeleteVM(_dom0, _vm_name, aNodeRecovery=True)
                        ebLogError(f"*** Failed to shutdown VM:{_vm_name} on dom0:{_dom0}")
                        raise ExacloudRuntimeError(0x0441, 0xA, 'Failed to perform vm shutdown')
                else:
                    _backup_seq = _json["backup_seq"]
                    _dest  = _json["dest"]
                    aVmName = _vm_name
            except KeyError as e:
                ebLogError('*** Vmbackup JSON invalid, missing {0} entry'.format(e))
                _rc = 1
                return _rc
        else:
            _backup_seq = "0"
            _dom0 = aNode
            _vm_name = aVmName
            _local = 'local'  # Fixed for local vmbackups
            _dest  = '/EXAVMIMAGES/GuestImages/{0}'.format(_vm_name)
            _forceapply = False

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_dom0)
        if not self.mCheckVMbackupInstalled(_node):
            _log = '*** VMBackup utility is not installed on the dom0: {0}'.format(_dom0)
            ebLogError(_log)
            _vmbackupdata["Log"] = _log
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
            _node.mDisconnect()
            raise ExacloudRuntimeError(0x0822, 0xA, 'VMBackup utility is not installed')
        else:
            _available_bkp = self.mCheckAvailableVMbackups(_node, aVmName)
            if _available_bkp is False:
                _log = '*** Error, not available backups for restore'
                ebLogError(_log)
                _vmbackupdata["Log"] = _log
                _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                raise ExacloudRuntimeError(0x0823, 0xA, 'No available backups for VMBackup restore')
            else:
                if self._is_exacc_rack:
                    #If exacc, do not calculate seq n. just pass the one in the arguments
                    _exec_time = 1600 * 12

                else:
                    _exec_time = 60 * 60
                    _location = self.mGetVmBackupLocalFolder(_dom0, aVmName)
                    _backup_seq = _location.split("/")[5]

                if _backup_seq not in _available_bkp:
                    ebLogError('*** Available backup seq is lower than requested: {0} '.format(_backup_seq))
                    ebLogError('*** Valid backup seq numbers: {0} '.format(_available_bkp))
                    raise ExacloudRuntimeError(0x0823, 0xA, ' Valid backup seq number not available')

                _uuid = str(uuid.uuid1())
                #Multiprorcess of check an copy file
                _processes = ProcessManager()
                _rc = _processes.mGetManager().list()
                _pr1 = ProcessStructure(self.mExecuteRestore, [_dom0, _vm_name, _backup_seq, _local, _dest, _uuid, _rc, _node_recovery, _forceapply])
                _pr1.mSetMaxExecutionTime(_exec_time)
                _pr1.mSetJoinTimeout(1)
                _processes.mStartAppend(_pr1)

                _processes.mJoinProcess()

                _json = aOptions.jsonconf
                _jconf_keys = list(_json.keys())
                if _jconf_keys is not None and 'node_recovery_flow' in _jconf_keys and _json['node_recovery_flow'] == True:
                    try:
                        _recoveryObj.mRestoreVM(_dom0, _vm_name)
                    except Exception as e:
                        _error_str = '*** VMBackup Restore failed'
                        _vmbackupdata["Log"] = _error_str
                        ebLogError(_error_str)
                        _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                        raise ExacloudRuntimeError(0x0441, 0xA, _error_str)

                    #Validate VM Post Restore Operation
                    _recoveryObj.mPostRestoreValidation(_dom0, _vm_name)
                    # Remove access to the domUs.
                    if "delete_domu_keys" in aOptions.jsonconf and aOptions.jsonconf['delete_domu_keys'].lower() == "true":
                        self.__ebox.mRemoveSshKeys(['opc', 'grid', 'oracle'])
                return _rc.pop()

    # mRestoreOSSVMbackup:
    # Restore available oss backup of a given DomU on a given Dom0
    def mRestoreOSSVMbackup(self, aOptions):

        _options = aOptions
        _vmbackupdata = self.mGetVMBackupData()
        _vmbackupdata["Log"] = ''
        _rc = 0
        ebLogInfo("Restore Backup from OSS")

        # If payload does not have the OSS values, we error out
        if not ebVMBackupOCI.mIsVMBOSSEnabled(aOptions):
            _log = ('*** VMBackup Restore payload or config is invalid, '
                 'check if any fields are missing')
            _vmbackupdata["Log"] = _log
            ebLogError(_log)
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
            raise ExacloudRuntimeError(0x0763, 0xA, _log)

        # If the payload has a non-empty vmboss section, we proceeed with the VMBackup
        # OCI cache file update, and credentials population
        _vmbackup_oci_mgr = ebVMBackupOCI(aOptions)
        _vmbackup_oci_mgr.mSetupVMBackupDom0Cache()
        if ebVMBackupOCI.mIsForceUsersPrincipalsSet():
            _vmbackup_oci_mgr.mUploadCustomerUserCredentialsToDom0()
        _vmbackup_oci_mgr.mUploadCertificatesToDom0()
        self.mEnableOssVMBackupConfig(aOptions)

        _domU_to_restore = aOptions.jsonconf.get("vmboss", {}).get("domU", None)
        _seq = aOptions.jsonconf.get("vmboss", {}).get("seq", None)

        # Parse payload, since this is expected to be called from json dispatch
        # we know aOptions.jsonconf must exist
        for _node_details in _vmbackup_oci_mgr.mGetNodeDetails():

            _dom0 = _node_details.dom0
            _domU = _node_details.domU

            if _domU != _domU_to_restore:
                ebLogWarn(f"Ignoring payload pair: {_dom0} : {_domU}")
                continue

            ebLogTrace(f"Restore payload fields: "
                f"dom0 = {_dom0}, "
                f"domU = {_domU}, "
                f"seq = {_seq}")

            # Fail is no sequence number is given
            if _seq is None:
                _log = ('*** VMBackup Restore payload is invalid, check if any '
                    'fields are missing')
                _vmbackupdata["Log"] = _log
                ebLogError(_log)
                _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                raise ExacloudRuntimeError(0x0763, 0xA, _log)

            _uuid = str(uuid.uuid1())
            _cmd_restore  = f"vmbackup restore --vm {_domU}  --loc oss --seq {_seq} --uuid {_uuid}"
            _cmd_str = f"source {self.VMBACKUPENV_FILE} ; {_cmd_restore}"

            with connect_to_host(_dom0, get_gcontext()) as _node:

                # Make sure the vmbackup tool is installed
                if not self.mCheckVMbackupInstalled(_node):
                    _log =  '*** VMBackup utility is not installed on the dom0: {0}'.format(_dom0)
                    ebLogError(_log)
                    _vmbackupdata["Log"] += _log
                    _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                    _rc = 1

               # Trigger the restore command on the Dom0 for the given DomU
                else:
                    ebLogInfo(f"Triggering restore command, this operation may take a while:\n{_cmd_str}")
                    _, _o, _e = _node.mExecuteCmd(_cmd_str)
                    _restore_rc = _node.mGetCmdExitStatus()
                    _out = _o.read()
                    _err = _e.read()
                    ebLogTrace(f"Stdout: {_out}. Stderr: {_err}")

                    _results_file = self.VMBACKUP_OSS_DOWNLOAD_STATUS.format(_uuid)
                    _result = ""

                    if _node.mFileExists(_results_file):
                        ebLogInfo(f"OSS Restore status file is available")
                        _out_cat = node_exec_cmd_check(_node, f"/bin/cat {_results_file}")
                        _result = _out_cat.stdout.strip()
                        ebLogTrace(f"Result from status file is: {_out_cat}")

                    if _restore_rc == 0:
                        _msg = f'*** Backup Restore exit with success on: {_dom0}, will check status file'
                        ebLogInfo(_msg)

                        # Validate results file on uuid directory
                        if "COMPLETEDSUCCESSFULLY" in _result:
                            ebLogInfo(f"Status file result is {_result}")
                            _vmbackupdata["Log"] = os.path.dirname(_results_file)
                            _vmbackupdata["Exacloud Cmd Status"] = self.PASS
                            _rc = 0
                        else:
                            _log = f"Status file result is {_result}"
                            ebLogError(_log)
                            _vmbackupdata["Log"] = _log
                            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                            _rc = 1

                    else:
                        _log = f'*** Backup Restore error on: {_dom0}'
                        ebLogError(_log)
                        _vmbackupdata["Log"] = _log
                        _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                        _rc = 1

        _log_restore = _vmbackupdata["Log"]
        _status_restore = _vmbackupdata["Exacloud Cmd Status"]

        if ebVMBackupOCI.mIsVMBOSSEnabled(aOptions):
            self.mDisableOSSVMBackupConfig(aOptions, _vmbackup_oci_mgr.mReturnDom0DomUPair())

        if _rc:
            _msg = "An error is detected during the restore operation"
            ebLogError(_msg)

        # Populate log results for ECRA to read
        # if operations was successful
        _vmbackupdata["Log"] = _log_restore
        _vmbackupdata["Exacloud Cmd Status"] = _status_restore

        return _rc

    # Restore available local backup of a given DomU on a given Dom0
    def mRestoreLocalVMbackup(self, aOptions):

        _options = aOptions
        _vmbackupdata = self.mGetVMBackupData()
        _vmbackupdata["Log"] = ''
        _rc = 0
        ebLogInfo("Restore Backup from Local")

        # Parse payload
        _domU = aOptions.jsonconf.get("vmboss", {}).get("domu", None)
        _dom0 = aOptions.jsonconf.get("vmboss", {}).get("dom0", None)
        _seq = aOptions.jsonconf.get("vmboss", {}).get("seq", None)
        _image = aOptions.jsonconf.get("vmboss", {}).get("image", None)
        _restart_vm = aOptions.jsonconf.get("vmboss", {}).get("restart_vm", None)

        _mandatory = {_domU, _dom0, _seq}

        ebLogTrace(f"Restore payload fields: "
            f"dom0 = {_dom0}, "
            f"domu = {_domU}, "
            f"seq = {_seq}, "
            f"image = {_image}, "
            f"restart_vm = {_restart_vm}")

        # Fail is any mandatory field is missing
        if None in _mandatory:
            _log = ('*** VMBackup Restore payload is invalid, check if any '
                'fields are missing.')
            _vmbackupdata["Log"] = _log
            ebLogError(_log)
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
            raise ExacloudRuntimeError(0x0763, 0xA, _log)

        # Check if specific image is requested
        if not _image:
            ebLogInfo(f"No specific image detected on payload to be restored")
            _cmd_img = ""
        else:
            ebLogInfo(f"Image requested in payload: {_image}")
            _cmd_img = f"--restoreimage {_image}"

        # Check if specific sequence number is requested
        if _seq in ["", None]:
            ebLogInfo(f"No specific sequence number detected on payload to "
                "be restored")
            _cmd_seq = ""
        else:
            ebLogInfo(f"Sequence number requested in payload: {_seq}")
            _cmd_seq = f"--seq {_seq}"

        # Check if restart vm is requested
        if str(_restart_vm).lower() == "true":
            ebLogInfo("Will restart the VM as requested in payload")
            _cmd_restart = "--restart-vm"
        else:
            ebLogInfo("Will not restart VM")
            _cmd_restart = ""

        # For now location is always local with no intention to make this
        # optional for the operator
        _uuid = str(uuid.uuid1())
        _cmd_restore  = (f"vmbackup restore --vm {_domU} --loc local "
            f"{_cmd_seq} {_cmd_img} {_cmd_restart} --uuid {_uuid}")
        _cmd_str = f"source {self.VMBACKUPENV_FILE} ; {_cmd_restore}"

        with connect_to_host(_dom0, get_gcontext()) as _node:

            # Make sure the vmbackup tool is installed
            if not self.mCheckVMbackupInstalled(_node):
                _log =  '*** VMBackup utility is not installed on the dom0: {0}'.format(_dom0)
                ebLogError(_log)
                _vmbackupdata["Log"] += _log
                _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                _rc = 1

           # Trigger the restore command on the Dom0 for the given DomU
            else:
                _, _o, _e = _node.mExecuteCmd(_cmd_str)
                _restore_rc = _node.mGetCmdExitStatus()
                _out = _o.read()
                _err = _e.read()
                ebLogTrace(f"Stdout: {_out}. Stderr: {_err}")

                _results_file = self.VMBACKUP_OSS_DOWNLOAD_STATUS.format(_uuid)
                _result = ""

                if _node.mFileExists(_results_file):
                    ebLogInfo(f"OSS Restore status file is available")
                    _out_cat = node_exec_cmd_check(_node, f"/bin/cat {_results_file}")
                    _result = _out_cat.stdout.strip()
                    ebLogTrace(f"Result from status file is: {_out_cat}")

                if _restore_rc == 0:
                    _log = os.path.dirname(_results_file)
                    _msg = f'*** Backup Restore exit with success on: {_dom0}'
                    ebLogInfo(_msg)

                    # Validate results file on uuid directory
                    if "COMPLETEDSUCCESSFULLY" in _result:
                        ebLogInfo(f"Status file result is {_result}")
                        _vmbackupdata["Log"] += _log
                        _vmbackupdata["Exacloud Cmd Status"] = self.PASS
                        _rc = 0
                    else:
                        ebLogError(f"Status file result is {_result}")
                        _vmbackupdata["Log"] += _log
                        _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                        _rc = 1

                else:
                    _log = f'*** Backup Restore error on: {_dom0}'
                    ebLogError(_log)
                    _vmbackupdata["Log"] += _log
                    _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                    _rc = 1
        if _rc:
            _msg = "An error is detected during the restore operations"
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x0763, 0xA, _msg)

        return _rc


    def mGetVmBackupLocalFolder(self, aDom0Name, aVmName, aBackupType="Local"):
        _backup_type = aBackupType

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDom0Name)

        _cmd = "find /EXAVMIMAGES/Backup/{0} | grep '{1}$' | tail -1".format(_backup_type, aVmName)
        _node.mExecuteCmd(_cmd)
        if _node.mGetCmdExitStatus() == 0:
            _location = _node.mSingleLineOutput(_cmd)
            _node.mDisconnect()
            return _location

        _node.mDisconnect()
        return None


    def mCheckRestore(self, aDom0Name, aVmName, aLocalFolder, aDestFolder):

        time.sleep(1)

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDom0Name)

        _totalSize = float(_node.mSingleLineOutput("ls -lA %s | awk 'BEGIN{sum=0} {sum+=$5} END{print sum}'" % (aLocalFolder)))
        _starttime = time.time()

        _actualSize = 0
        while (_actualSize < _totalSize):
            _actualSize = float(_node.mSingleLineOutput("ls -lA %s | awk 'BEGIN{sum=0} {sum+=$5} END{print sum}'" % (aDestFolder)))
            ebLogInfo("Restore of {0} at: {1:.2f}%".format(aVmName, _actualSize/_totalSize*100))

            time.sleep(3)

        _endtime = time.time()

        ebLogInfo("Restore of {0} Complete in: {1:.2f} minutes".format(aVmName, (_endtime-_starttime)/60))
        _node.mDisconnect()

    def mExecuteRestore(self, aDom0Name, aVmName, aBackupSeq, aLocalFolder, aDestFolder, aUUID, aRc, aNodeRecovery=False, aForceApply=False):
        """
        Run 'vmbackup restore' in the specified dom0.
        Expected behavior on ExaCC is as follows:
            If --forceapply is given, vmbackup will try to use the fetched backup to boot the VM.
            Otherwise, restore will act as a simple fetch and bring the selected backup
            to /EXAVMIMAGES/Restore/<uuid> directory.
        """

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDom0Name)
        _vmbackupdata = self.mGetVMBackupData()

        _cmd_str = 'source ' + self.VMBACKUPENV_FILE + '; vmbackup restore '
        _cmd_str += '--vm {0} --seq {1} --loc {2} --uuid {3}'.format(aVmName, aBackupSeq, aLocalFolder, aUUID)
        if aForceApply:
            ebLogWarn("Force Apply detected, VM will be shut down (if not already down) "
                      "and VM files will be replaced with the fetched backup.")
            _cmd_str += " --forceapply"

        ebLogWarn('Executing: ' + _cmd_str)
        _, _o, _e = _node.mExecuteCmd(_cmd_str)
        _rv = _node.mGetCmdExitStatus()
        _err = _e.read()
        if (self._is_exacc_rack and _rv != 0) or 'error' in _err.lower():
            _log = '*** Failed to restore VM backup, {0}'.format(str(_err.rstrip()))
            ebLogError(_log)
            _vmbackupdata["Log"] = _log
            _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
            aRc.append(1)
            _node.mDisconnect()
            return

        if aForceApply:
            _log = f"Restored VM {aVmName} with {aLocalFolder} backup number: {aBackupSeq}."
            _log += " Please check VM status."
        else:
            # ExaCC does not support NodeRecovery so restore without --forceapply
            # would behave like a simple backup fetch to /EXAVMIMAGES/Restore
            _srcDir = f"/EXAVMIMAGES/Restore/{aUUID}"
            if not self._is_exacc_rack:
                if aNodeRecovery:
                    _cmd_str = f"/bin/mv -f {_srcDir}/*.img {aDestFolder}"
                else:
                    _cmd_str = f"/bin/mv -f {_srcDir}/* {aDestFolder}"
                _, _o, _e = _node.mExecuteCmd(_cmd_str)
                _rv = _node.mGetCmdExitStatus()
                _err = _e.read()
                _out = _o.read().rstrip()
                _node.mExecuteCmdLog(f"/bin/rm -rf {_srcDir}/")
                if _rv != 0 or 'error' in _err.lower():
                    _log = '*** Failed to restore VM backup, {0}'.format(str(_err.rstrip()))
                    ebLogError(_log)
                    _vmbackupdata["Log"] = _log
                    _vmbackupdata["Exacloud Cmd Status"] = self.FAIL
                    aRc.append(1)
                    return
                else:
                    _node.mExecuteCmdLog(f"/bin/mkdir -p {aDestFolder}/console")
                    _node.mExecuteCmdLog(f"/bin/mkdir -p {aDestFolder}/console/write-qemu")
            else:
                _out = _srcDir

            _log = '*** Restoring Backup: \n' + str(_out)

        ebLogInfo(_log)
        _vmbackupdata["Log"] = _log
        _vmbackupdata["Exacloud Cmd Status"] = self.PASS
        aRc.append(0)
        _node.mDisconnect()

    def mSetSSHDOptions(self, aOptions, aNode):
        _options = aOptions
        _cmd_list = list()
        _rc = 0
        _cmd_list.append("/bin/sed 's/^ClientAliveCountMax.*/ClientAliveCountMax 24/' -i /etc/ssh/sshd_config")
        _cmd_list.append("/bin/sed 's/^ClientAliveInterval.*/ClientAliveInterval 600/' -i /etc/ssh/sshd_config")
        _cmd_list.append("/sbin/service sshd restart")
        for _cmd in _cmd_list:
            _, _o, _e = aNode.mExecuteCmd(_cmd)
            _rc = aNode.mGetCmdExitStatus() 
            if aNode.mGetCmdExitStatus() != 0:
                _err = _e.read()
                _log = "*** Failed to execute command : '{0}', Node: '{1}' Error:[{2}]".format(_cmd,\
                    aNode.mGetHostname(), str(_err.rstrip()))
                ebLogError(_log)
                return _rc 
        return _rc


    def mSetCrontabEntry(self, aOptions):
        # This method is used during capacity move from exadb-d to exadb-xs & vice-versa
        _rc = 0
        _dom0 = aOptions.jsonconf.get("dom0_name")
        _mode = aOptions.jsonconf.get("setcronaction")
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_dom0)
        if _mode == 'enable':
            _rc = self.mSetVMBackupCronJob (aOptions, _node)
        else:
            _rc = self.mDisableVMBackupCronJob (_node)
        _node.mDisconnect()
        return _rc


    def mGetVMBackupCronTabEntries(self, aNode)->list:
        """
        Returns a list where every element is a
        'vmbackup' related crontab entry
        """

        _cron_file_loc = "/var/spool/cron/root"
        _cron_string = "/opt/oracle/vmbackup/sched_vmb.sh"
        _out_grep = node_exec_cmd(aNode, f"/bin/grep '{_cron_string}' -i {_cron_file_loc}")
        _cron_entries = []
        if _out_grep.stdout:
            _cron_entries = _out_grep.stdout.strip().splitlines()
        ebLogTrace(f"Crontrab contents from {aNode.mGetHostname()}:\n "
            f"{_cron_entries}")
        return _cron_entries

    def mSetVMBackupCronJob(self, aOptions, aNode):
        _options = aOptions
        _cmd_list = list()
        _rc = 0
        _cron_file_loc = "/var/spool/cron/root"
        _cron_string = "/opt/oracle/vmbackup/sched_vmb.sh"
        # cron-file does not exist at the very first time.
        _cmd_ensure_cron_file = "! /bin/test -e {0} && /bin/touch {0} && /bin/chmod 0600 {0}".format(_cron_file_loc)
        aNode.mExecuteCmdLog(_cmd_ensure_cron_file)
        _cron_entry = "00 23 * * 6 /opt/oracle/vmbackup/sched_vmb.sh"

        # Remove all earlier commented entries of sched_vmb.sh using sed
        _cmd = f'/bin/sed -i "/^[[:space:]]*#.*sched_vmb\.sh/d" {_cron_file_loc}'
        _out_sed = node_exec_cmd(aNode, _cmd)
        ebLogTrace(_out_sed)

        # We filter out any lines starting with a comment '#', so that we
        # make sure the crontab entry present is valid/triggered. At most
        # we'll end up with 2 entries, where one of them is commented ('#')
        _cmd_check_entry = '/bin/grep "^[^#].*{0}" {1}'.format(_cron_string, _cron_file_loc)
        _, _o, _e = aNode.mExecuteCmd(_cmd_check_entry)
        _rc = aNode.mGetCmdExitStatus()
        if _rc == 0:
            ebLogInfo("Cron entry {0} already exists on node {1}. Skipping configuration".format(_cron_string, aNode.mGetHostname()))
            return _rc

        # Add the default entry
        _cmd_add_entry = "/bin/sh -c 'echo \"{0}\"' >> {1}".format(_cron_entry, _cron_file_loc)
        _, _o, _e = aNode.mExecuteCmd(_cmd_add_entry)
        ebLogInfo("Added crontab entry {0} on node {1}".format(_cron_entry, aNode.mGetHostname()))
        _rc = aNode.mGetCmdExitStatus()
        if _rc == 0:
            ebLogInfo("No errors while adding crontab entry {0} on node {1}".format(_cron_entry, aNode.mGetHostname()))
        else:
            _err = _e.read()
            _log = "*** Failed to execute command : [{0}] on Node '{1}'  Error: '{2}'".format(\
                _cmd_add_entry, aNode.mGetHostname(), str(_err.rstrip()))
            ebLogError(_log)
            return _rc
        return _rc

    def mGetVMBackupVersion(self, aNode)->tuple:
        """
        This method will get the version of the vmbackup tool from a given Node
        by running 'vmbackup version'

        :param aNode: an already connected node to a Dom0

        :returns: a tuple of 2 strings representing the major version (series)
            and the date

            If unable to determine version, two empty strings are returned
        """

        # Use vmbackup version
        _cmd_version = 'vmbackup version '
        _cmd_str = f'source {self.VMBACKUPENV_FILE}; {_cmd_version}'
        ebLogInfo("Attempting to check version of vmbackup in "
            f"'{aNode.mGetHostname()}'")
        ebLogTrace(f"Running: '{_cmd_str}'")
        _series = ""
        _date = ""

        _out_version = node_exec_cmd(aNode, _cmd_str)

        _version = _out_version.stdout.strip()
        ebLogTrace(f"Version output is: '{_out_version}'")

        # We expect an output in the form of:
        # [root@sea201605exdd001 ~]# vmbackup version
        # ECS_25.2.2.1.5_LINUX.X64_250905.159
        # [root@sea201605exdd001 ~]# 

        # Regular expression pattern to extract the required parts
        pattern = r"ECS_(.*)_LINUX\.X64_(\d+)\.\d+"

        # Use regular expression to extract the required parts
        _version_portion_match = re.match(pattern, _version)

        if (not _version_portion_match or
                len(_version_portion_match.groups()) != 2):
            _msg = ("Unable to locate vmbackup version, version output: "
                f"{_out_version}")
            ebLogWarn(_msg)

        else:
            _series = _version_portion_match.group(1)
            _date = _version_portion_match.group(2)
            ebLogInfo(f"Exacloud detected the series: '{_series}', "
                f"and date '{_date}' from: "
                f"{_version}', in '{aNode.mGetHostname()}'")

        return _series, _date

    def mGetLocalVMBackupVersion(self)->tuple():
        """
        This method will try to calculate the version of the vmbackup tool currently
        present in the file under 'exacloud/images', examples:

        images/release-vmbackup-MAIN+251001.0901.tgz
        images/release-vmbackup-25.2.2.1.5+250905.0159.tgz

        From the above example, this method will return a tuple with
        two strings:
            ("MAIN", "251001")
            ("25.2.2.1.5", "250905")

        :raises ExacloudRuntimeError: if unable to locate the local release package
            for the vmbackup tool
        """

        # Search for files with the following pattern, we expect something like:
        # ['images/release-vmbackup-1.0.1_221215.0901.tgz']
        # Then we try to get the version, which is 221215.0901 from the above example
        # This is the same paterrn version we can get from the vmbackup tool on the
        # remote doms with 'pip show'
        _vmbackup_file = glob.glob(self.VMBACKUPPKG_BITS + '*[0-9].tgz').pop()
        if _vmbackup_file:
            ebLogTrace(f"Exacloud detected the vmbackup package path: '{_vmbackup_file}'")
            _vmbackup_file = os.path.basename(_vmbackup_file)
            ebLogInfo(f"Exacloud detected the vmbackup package: '{_vmbackup_file}'")

            # We'll try to get the series and date portion using regex,
            # e.g. from ['images/release-vmbackup-25.2.2.1.5+250905.0159.tgz']
            # we would get: 25.2.2.1.5 and 250905
            # Regular expression pattern to extract the required parts
            #_pattern = r"release-vmbackup-(.+?)\+(\d+)\.\d+\.tgz"
            _pattern = r"release-vmbackup-([^+]+)\+(\d+)\.\d+\.tgz"

            # Use regular expression to extract the required parts
            _version_portion_match = re.match(_pattern, _vmbackup_file)

            if (not _version_portion_match or
                len(_version_portion_match.groups()) != 2):
                _msg = ("Exacloud couldn't detect the version from the file: "
                    f"{_vmbackup_file}. We'll raise an exception, please fix the "
                    "naming convention to match the supported convention, e.g. "
                    "'images/release-vmbackup-25.2.2.1.5+250905.0159.tgz'")
                ebLogError(_msg)
                raise ExacloudRuntimeError(0x0763, 0xA, _msg)

            else:
                _series = _version_portion_match.group(1)
                _date = _version_portion_match.group(2)
                ebLogInfo(f"Exacloud detected the series: '{_series}', "
                    f"and date '{_date}' from: {_vmbackup_file}' locally.")
                return (_series, _date)

        else:
            raise ExacloudRuntimeError(0x0763, 0xA, "Failed to identify local vmbackup file under $EC_HOME/images")


    def mCheckRemoteProcessOngoing(self, aNode, aTimeout:int=0)-> bool:
        """
        This method will check in the host to which aNode is connected, if there is
        any ongoing vmbackup process running, it will log it and return True.
        If we detect no ongoig process we'll return False

        :param aTimeout: an optional integer that specifies how many seconds
            to wait for any vmbackup process to finish (if any)

        :returns:
            True: If a vmbackup process still exists
            False: If no vmbackup processes exists
        """

        _start_time = datetime.datetime.now()

        _timeout_reached = False
        _process_still_exists = True
        _wait_seconds = 10

        while not _timeout_reached and _process_still_exists:

            _cmd_pgrep = "/usr/bin/ps -fe| /bin/grep 'python-vmbackup' | /bin/grep -v grep"
            ebLogInfo(f"Looking for a vmbackup process running in '{aNode.mGetHostname()}'")

            _pgrep_output = node_exec_cmd(aNode, _cmd_pgrep)
            ebLogTrace(_pgrep_output)

            if _pgrep_output.exit_code == 0:
                ebLogInfo("Exacloud found a vmbackup process running in: "
                    f"'{aNode.mGetHostname()}', process info is: '{_pgrep_output.stdout}")
                _process_still_exists = True

            else:
                ebLogInfo("Exacloud found no vmbackup process running in: "
                    f"'{aNode.mGetHostname()}', cmd out is: '{_pgrep_output}")
                _process_still_exists = False

            _current_time = datetime.datetime.now()
            if _process_still_exists and (_current_time - _start_time).total_seconds() >= aTimeout:
                ebLogInfo(f"After {aTimeout} seconds, a vmbackup process "
                    f"still exists: {_pgrep_output.stdout}")
                _timeout_reached = True

            elif _process_still_exists and (_current_time - _start_time).total_seconds() < aTimeout:
                ebLogInfo(f"A vmbackup process is detected to be running, will check again in "
                    f"{_wait_seconds} seconds, and we will wait at most {aTimeout} seconds for "
                    f"it to finish, process info:\n{_pgrep_output.stdout}")
                time.sleep(_wait_seconds)


        return _process_still_exists

    def mDisableOSSVMBackupConfig(self, aOptions, aDom0DomUPair=[]):
        """
        This method will attempt to update the necessary OSS parameters
        in the vmbackup.conf file, to DISABLE the tool to push 'vmbackup file' to
        OSS.

        :param aOptions: a context aOptions object

        :returns: 0 on success

        :raises: ExacloudnRuntimeError on error
        """

        _options = copy.deepcopy(aOptions)

        #
        # Disable oss backup
        ebLogInfo(f"Exacloud setting param: '{self.SET_PARAM_OSS_BACKUP}' to 'disabled'")

        if aDom0DomUPair:
            _ddpair = aDom0DomUPair
        else:
            _vmbackup_oci_mgr = ebVMBackupOCI(_options)
            _ddpair = _vmbackup_oci_mgr.mReturnDom0DomUPair()

        # If there is no ongoing process, we assume there is
        # no backup ongoing so we can disable OSS_BACKUP
        # safely. Ideally, OSS_BACKUP in vmbackup.conf should be
        # enabled only when there is an OSS backup in progress
        for _dom0, _ in _ddpair:
            with connect_to_host(_dom0, get_gcontext()) as _node:
                if self.mCheckRemoteProcessOngoing(_node):
                    ebLogInfo("Skipping mDisableOSSVMBackupConfig since at "
                            "least one vmbackup process is detected in "
                            f"{_dom0}")
                    return

        # Since the set_param operation accepts one parameter at once, we set it
        # in here and continue with other parameters
        _set_param_dict = {self.SET_PARAM_OSS_BACKUP: "disabled"}
        _options.jsonconf = _set_param_dict
        _rc = self.mSetVMBackupParameter(_options, _ddpair)
        ebLogTrace(f"Log from vmbackup operation: {self.mGetVMBackupData()}")
        if _rc:
            _msg = ("Exacloud failed to set the parameter with data: "
                f"'{_set_param_dict}'")
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x095, 0xA, _msg)
        ebLogInfo(f"Exacloud set the parameter with data: '{_set_param_dict}'")

        return 0

    def mEnableOssVMBackupConfig(self, aOptions, aDom0DomUPair=[]):
        """
        This method will attempt to update the necessary OSS parameters
        in the vmbackup.conf file, to enable the tool to push 'vmbackup file' to
        OSS.

        :param aOptions: a context aOptions object

        :returns: 0 on success

        :raises: ExacloudnRuntimeError on error

        """

        _options = copy.deepcopy(aOptions)

        # Make sure the vmbackup tool is present
        # Since the installation may be gated in exabox.conf, we need to can do a quick
        # check in here
        _list_dom0s_missing_tool = set()
        if aDom0DomUPair:
            _nodes = aDom0DomUPair
        else:
            _vmbackup_oci_mgr = ebVMBackupOCI(_options)
            _nodes = _vmbackup_oci_mgr.mReturnDom0DomUPair()
        for _dom0, _ in _nodes:
            with connect_to_host(_dom0, get_gcontext()) as _node:
                _vmbackup_installed = self.mCheckVMbackupInstalled(_node)
                ebLogTrace(f"Log from vmbackup operation: {self.mGetVMBackupData()}")

            # Store all the dom0s missing the tool for better logging
            if _vmbackup_installed is False:
                _list_dom0s_missing_tool.add(_dom0)

        if _list_dom0s_missing_tool:
            _msg = (f"Exacloud requires the VMBackup tool to be installed so that we "
                "can take modify the vmbackup OSS parameters If you want to install "
                "the vmbackup tool when retrying this step, you can set to 'True' the "
                "field 'enable_vmbackup_install' in exabox.conf, reload the "
                "Exacloud agent/workers with: '$EC_ROOT/bin/agent --reload' and retry "
                "this step (this will not interrupt any other exacloud ongoing process "
                "List of dom0s without the tool installed: "
                f"'{_list_dom0s_missing_tool}'")
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x095, 0xA, _msg)

        #
        # Enable oss backup
        ebLogInfo(f"Exacloud setting param: '{self.SET_PARAM_OSS_BACKUP}' to 'enabled'")

        # Since the set_param operation accepts one parameter at once, we set it
        # in here and continue with other parameters
        _set_param_dict = {self.SET_PARAM_OSS_BACKUP: "enabled"}
        _options.jsonconf = _set_param_dict
        _rc = self.mSetVMBackupParameter(_options, _nodes)
        ebLogTrace(f"Log from vmbackup operation: {self.mGetVMBackupData()}")
        if _rc:
            _msg = ("Exacloud failed to set the parameter with data: "
                f"'{_set_param_dict}'")
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x095, 0xA, _msg)
        ebLogInfo(f"Exacloud set the parameter with data: '{_set_param_dict}'")

        return 0

    def mCheckNodeCanReachOci(self, aDom0):
        """
        Checks if the dom0 given can reach a common OCI endpoint (we use
        object storage endpoint). This endpoint is different per
        region but will always follow the same conventions for commercial
        and non-commercial regions, with the single exception of R1

        :param aDom0: The dom0 to check

        """

        _reaches_oci = False

        _oci_factory = ExaOCIFactory()
        _connector = _oci_factory.get_oci_connector()

        _oci_url = ""
        if isinstance(_connector, R1Connector):
            _oci_url = "https://objectstorage.r1.oracleiaas.com"

        elif (isinstance(_connector, ExaboxConfConnector) or
            isinstance(_connector, RegionConnector)):
            _oci_region = _connector.get_region()
            _oci_domain = _connector.get_domain()
            _oci_url = f'https://objectstorage.{_oci_region}.{_oci_domain}'
        else:
            ebLogError("We detected no valid region, will assume this is "
                "non OCI")
            return False

        ebLogInfo(f"Checking if {aDom0} can reach {_oci_url}")

        # This is easier with netcat but right now
        # it's unkown to me if all dom0s will always have 'nc'
        _curl_cmd = ('{0} --local-port 49152-65535 {1}:443/tmp '
            '-vvv 2>&1 --max-time 10 | {2} -E "^\* Connected to"')

        _tries, _delay, _backoff = 3,2,2

        with connect_to_host(aDom0, get_gcontext()) as _node:

            _bin_curl = node_cmd_abs_path_check(
                _node, "curl", sbin=True)
            _bin_grep = node_cmd_abs_path_check(
                _node, "grep")


            for _ in range(_tries):
                _out_curl = node_exec_cmd(_node, _curl_cmd.format(
                    _bin_curl, _oci_url, _bin_grep))
                ebLogTrace(f"Output from {aDom0} is {_out_curl}")

                if _out_curl.exit_code == 0:
                    _reaches_oci = True
                    ebLogInfo(f"Detected a succesful connection from {aDom0} to "
                        f"{_oci_url}")
                    break
                else:
                    ebLogWarn(f"Detected a failure while trying to establish a "
                        f"connection from {aDom0} to {_oci_url}")

                ebLogWarn(f'*** Retrying...Unable to reach {_oci_url} from {aDom0}')
                time.sleep(_delay)
                _delay *= _backoff

            else:
                ebLogError(f"After {_tries} attempts, we could not establish "
                    f"a connection from {aDom0} to {_oci_url}")

        return _reaches_oci

    # This method converts local storage to exascale storage
    def mExascaleEDVbackup(self, aOptions):
        _options = aOptions
        _ebox = self.__ebox
        _rc = 0
        ebLogInfo("Convert Local VMbackup to exascale VMbackup")

        _utils = _ebox.mGetExascaleUtils()
        _utils.mMigrateVMbackupJson(_options)

        return _rc

    def mUpdateNodesConf(self, aOptions, aDom0DomUList=None):
        _ebox = self.__ebox
        _nodes_conf = "nodes.conf"
        _nodes = {}
        _rc = 0

        if aDom0DomUList:
            _dom0UList = aDom0DomUList
        else:
            _dom0UList = _ebox.mReturnDom0DomUPair()

        _remote_path = get_gcontext().mGetConfigOptions().get("vmbackup", {}).get(
            "vmbackup_conf_dir", "/opt/oracle/vmbackup/conf/")
        if not _remote_path:
            _remote_path = "/opt/oracle/vmbackup/conf/"

        _remoteNodesFile = os.path.join(_remote_path, _nodes_conf)
        _dom0_list = [_dom0.split('.')[0] for _dom0, _ in _dom0UList]
        _nodes["dbnodes"] = _dom0_list
        _dbnode_object = json.dumps(_nodes, indent=4)
        with NamedTemporaryFile(mode='w', delete=True) as _tmp_file:
            _tmp_file.write(_dbnode_object)
            _tmp_file.flush()
            for _dom0, _ in _dom0UList:
                try:
                    _node = exaBoxNode(get_gcontext())
                    _node.mConnect(aHost=_dom0)
                    #check if vmbackup conf dir exists
                    if _node.mFileExists(_remote_path) is False:
                        _node.mExecuteCmdLog(f"/bin/mkdir -p {_remote_path}")
                    if _node.mFileExists(_remoteNodesFile):
                        _node.mExecuteCmdLog(f"/bin/rm -rf {_remoteNodesFile}")
                    ebLogInfo(f"Creating VMBackup nodes.conf on {_dom0}")
                    _node.mCopyFile(_tmp_file.name, _remoteNodesFile)
                finally:
                    _node.mDisconnect()

        return _rc

    def mUpdatePasswordlessChain(self, aOptions, aDom0DomUList=None):
        _ebox = self.__ebox
        _rc = 0

        if aDom0DomUList:
            _dom0UList = aDom0DomUList
        else:
            _dom0UList = _ebox.mReturnDom0DomUPair()

        _dom0s = [pair[0] for pair in _dom0UList]
        _dom0s = self.mSortDom0List(_dom0s)

        for _inx, _dom0 in enumerate(_dom0s):
            ebLogInfo('*** Configuring ssh passwordless for {0}'.format(_dom0))
            _next_dom0 = _dom0s[(_inx + 1) % len(_dom0s)]
            self.__sshsetup.mSetSSHPasswordlessForVMBackup(_dom0, [_next_dom0])

        return _rc
