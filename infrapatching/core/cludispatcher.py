#
# $Header: ecs/exacloud/exabox/infrapatching/core/cludispatcher.py /main/66 2025/09/02 17:58:33 ajayasin Exp $
#
# cludispatcher.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cludispatcher.py - Dispatcher methods for infra patching
#
#    DESCRIPTION
#      This module has the method to run infra patching dispatcher functionalities
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jyotdas     02/11/26 - Enh - Skip path validation for DOM0 exasplice
#                           LATEST - handlers will resolve it
#    jyotdas     02/08/26 - Refactor to use mIsLatestTargetVersionAllowed
#                           utility function
#    jyotdas     02/06/26 - Enh - Allow LATEST targetVersion for DOM0
#                           exasplice patching
#    ajayasin    08/05/25 - moving command handler functions from clucontrol.py
#                           to clucommandhandler.py
#    apotluri    07/31/25 - Bug 38096654 - PRECHECK OF SMR FAILED WITH
#                           'DIRECTORY FOR EXADATA_RELEASE HAS MORE THAN ONE
#                           PATCH'
#    jyotdas     07/18/25 - ER 38056425 - Handle elu in racks with node qmr at
#                           different versions on ecra
#    jyotdas     06/11/25 - Enh 37912226 - Identify proper targetversion for
#                           elu in exacs infrapatching
#    araghave    04/02/25 - Enh 37515129 - EXACS | INFRAPATCHING NEED TO USE
#                           LATEST DBNU
#    apotluri    02/20/25 - Bug 37612704 - FIX INCORRECT VARIABLE DECLARATION
#                           IN MCHECKEXACLOUDMNT CAUSING
#                           EXACLOUD_PATCH_WORKING_SPACE_MB TO BE IGNORED
#    avimonda    09/26/24 - Bug 36943471 - DBAAS.EXACSOSPATCH : :FAILED TO
#                           COMPLETE GUEST VM OS UPDATE PRECHECK. ONE ORE
#                           MORE INDIVIDUAL PATCH REQUESTS FAILED
#    avimonda    09/16/24 - Enhancement Request 36775120 - EXACLOUD TIMEOUT
#                           MUST BE CALCULATED BASED ON THE PATCH OPERATION
#                           AND TARGET TYPE
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    emekala     08/05/24 - BUG 36878940 - UPDATE CHILD REQUEST UUID IN ECRA
#                           STATUS RESPONSE WHEN CHILD UUID CREATED BUT
#                           EXACLOUD FAILED WITH ERROR BEFORE INFRAPATCHING
#                           GETS THE HANDLE
#    araghave    07/15/24 - Enh 36830077 - CLEANUP KSPLICE CODE FROM
#                           INFRAPATCHING FILES
#    sdevasek    07/10/24 - ENH 36752768 - PROVIDE SPECIFIC ERROR CODE WHEN
#                           BUNDLE IS MISSING ON THE CPS NODE INSTEAD OF 
#                           GENERIC DISPATCHER EXCEPTION ERROR CODE
#    diguma      06/06/24 - Enh 36691192 - IN CASE OF ADBS, DURING DOM0/KVM
#                           HOST INFRA PATCHING RETRY EXECUTE DOM0DOMU PLUGIN
#    araghave    06/25/24 - Enh 36748435 - CLEANUP FABRIC ENTRIES IN CASE OF
#                           INFRA PATCHING ISSUES ENCOUNTERED DUE TO SWITCH
#                           REPLACEMENT
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    diguma      06/06/24 - Enh 36691192 - IN CASE OF ADBS, DURING DOM0/KVM
#                           HOST INFRA PATCHING RETRY EXECUTE DOM0DOMU PLUGIN
#    emekala     06/07/24 - ENH 36596516 - Optimize code in step 1-3 of
#                           cludispatcher to run only mPopulatePatchTables
#                           inside the lock
#    sdevasek    05/29/24 - ENH 36659116 - ECRA WR FOR DOMU OS PATCHING STATE
#                           IS NOT CHANGED FROM 202 TO 500 DUE TO ERROR_MESSAGE
#                           STRING OVERFLOW FOR TABLES ECS_REQUESTS_TABLE,
#                           ECS_EXA_APPLIED_PATCHES_TABLE
#    avimonda    05/15/24 - ENH 36569957: Stop gathering incident logs for
#                           HTTPS 503 error during child process creation. 
#    diguma      04/09/24 - Bug 36497510: EXACS:23.4.1.2.1:EXACLOUD:PATCHING:
#                           DOM0 PRECHECK DELETES
#                           '/OPT/EXACLOUD/CLUSTERS/SHARED_ENV_ENABLED' FILE
#    diguma      03/06/24 - Bug 36373059: EXACS | SMR PATCHING FAILED AT
#                           PRECHECK WITH ERROR | ERROR_DETAIL:
#                           MSTARTPATCHREQUESTEXECUTION ERROR: FLOAT OBJECT
#                           CANNOT BE INTERPRETED AS AN INTEGER
#    araghave    02/28/24 - Enh 36295801 - IMPLEMENT ONEOFFV2 PLUGIN EXACLOUD
#                           CHANGES
#    diguma      02/05/24 - Bug 36253736: NEED TO ADD STORAGE TYPE ATTRIBUTE
#                           IN INFRAPATCHING WORKFLOW
#    avimonda    01/03/24 - Bug 36148893: When the cluster details are missing
#                           from the local cluster list, the initiation of the
#                           monitoring request should be avoided. 
#    avimonda    12/14/23 - Bug 36111120: Adjusting cell patching timeout
#    sdevasek    12/11/23 - ENH 35976285 - COMMENT OUT UNUSED CODE TO INCREASE
#                           INFRAPATCHING CODE COVERAGE
#    diguma      12/08/23 - Bug 36085361: INCIDENT FILE CREATION FOR SUCCESS
#                           CASE SHOULD BE CONFIGURABLE THROUGH EXABOX.CONF
#    diguma      11/15/23 - bug 36006901: MULTIPLE CLUSTER PATCHING FAILURE
#                           WITH ERROR :ERROR_DETAIL: SYSTEM IS BUSY. PLEASE
#                           RETRY THE OPERATION AFTER SOME TIME
#    araghave    11/07/23 - FORTIFY: INSECURE RANDOMNESS REPORTED IN FILE
#                           /ECS/EXACLOUD/EXABOX/INFRAPATCHING/CORE/CLUDISPATCHER.PY
#    avimonda    10/07/23 - Bug 35869328 - EXACS| CELL PATCHING FAILED WITH
#                           ERROR MSTARTPATCHREQUESTEXECUTION MONITOR ERROR:
#                           (1205, 'LOCK WAIT TIMEOUT EXCEEDED; TRY
#                           RESTARTING TRANSACTION')
#    araghave    10/19/23 - Bug 35747726 - PATCHING FAILING WITH | ERROR -
#                           ERROR MESSAGE IN A SHARED IBFABRIC ENVIRONMENT,
#                           COMBINATION OF AN IBSWITCH/NON-IBSWITCH TARGET
#                           PATCH CANNOT BE RUN IN PARALLEL
#    jyotdas     08/08/23 - ENH 35614504 - Define erroraction for infrapatching
#                           at errorcode level instead of targettype level
#    avimonda    07/25/23 - Bug 34986894 - Adjust the patchmgr timeout to
#                           prevent CELLs patching timeout in rolling mode.
#    jyotdas     06/30/23 - BUG 35460949 - Infra prechecks blocked by domu
#                           prechecks
#    jyotdas     05/15/23 - ENH 35382596 - Store idempotency metadata in ecra
#                           db for active-active upgrade during infrapatching
#    sdevasek    08/03/22 - ENH 35127995 - USE DBSERVER.PATCH.ZIP FROM
#                           PATCHPAYLOADS/DBPATCHFILE IF EXISTS
#    araghave    11/25/22 - Bug 34828301 - EXACC:INFRA-PATCH:DOM0 PRECHECK
#                           EXPECT INCORRECT SPACE REQUIREMENT - SPACE IN / -
#                           NEEDED 5120 GB, GOT 2207 GB
#    sdevasek    10/19/22 - BUG 34685460 - CONCURRENT PATCHING REQUESTS FAILED
#    jyotdas     10/11/22 - BUG 34681939 - Infrapatching compute nodes should
#                           be sorted by dbserver name from ecra
#    araghave    07/22/22 - Enh 33043148 - EXADATA VM OS UPDATE DOES NOT USE
#                           LATEST PATCHMGR/DBNODEUPDATE
#    jyotdas     07/07/22 - ENH 34316717 - Pass dom0 list and cell list as part
#                           of infrapatching payload
#    sdevasek    06/27/22 - Bug 33213137 - INTRODUCE A SPECIFIC ERROR IF ROCE
#                           SWITCHES EMPTY FROM XML FILE
#    araghave    11/24/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES
#                           FROM ERROR.PY TO INFRAPATCHERROR.PY
#    araghave    10/20/21 - Enh 33486853 - MOVE TIMEOUT AND OTHER CONSTANTS OUT
#                           OF CODE INTO CONFIG/CONSTANT FILES
#    araghave    07/08/21 - BUG 33081173 - Remove older error codes from Infra
#                           patching core files
#    jyotdas     07/26/21 - Bug 33113180 - Infrastructure Patching issue with
#                           ibfabric
#    nmallego    07/12/21 - ER 32925372 - Allow domU patching when exasplice 
#                           patching is progressing and vice-versa. 
#    jyotdas     06/18/21 - Bug 32997721 - Patch wf failure does not report as
#                           failure
#    jyotdas     05/12/21 - ENH 32803507 - populate error message from exacloud
#                           outside patchlist attribute
#    araghave    03/23/21 - Enh 31423563 - PROVIDE A MECHANISM TO MONITOR INFRA
#                           PATCHING PROGRESS
#    jyotdas     03/22/21 - Enh 32415195 - error handling: return infra
#                           patching dispatcher errors to caller
#    araghave    02/01/21 - Bug 32120772 - EXASPLICE AND PYTHON 3 FIXES
#    araghave    01/20/21 - Bug 32395969 - MONTHLY PATCHING: FOUND FEW ISSUES
#                           WHILE TESTING AND NEED TO FIX
#    araghave    01/12/21 - Enh 31446326 - SUPPORT OF SWITCH OPTION AS TARGET
#                           TYPE THAT TAKES CARE OF BOTH IB AND ROCESWITCH
#    araghave    01/05/21 - Bug 32343803 - INFRAPATCHING: INVALID REQUEST ADDED
#                           WHEN PATCHING ATTEMPTED VIA CURL
#    araghave    12/09/20 - Enh 31984849 - RETURN ERROR CODES TO DBCP FROM DOMU
#                           AND PLUGINS
#    sringran    11/23/20 - Bug32025441 - INFRA PATCH TIMEDOUT EVEN THOUGH 
#                           PATCHMGR SUCEEDED
#    nmallego    11/06/20 - Fixing typo: ebLogInfo
#    araghave    10/28/20 - Enh 31925002 - Error code handling implementation 
#                           for Monthly Patching
#    nmallego    11/04/20 - Bug32109585 - override latest conversion for exacc
#    nmallego    10/27/20 - Enh 31540038 - INFRA PATCHING TO APPLY/ROLLBACK
#                           EXASPLICE/MONTHLY BUNDLE
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#

import copy
import re
import json
import threading
import traceback
import secrets
import glob
from base64 import b64decode
from time import sleep
from uuid import uuid4
import os
from datetime import datetime
import random
from pathlib import Path
from exabox.agent.Client import ebExaClient
from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.infrapatching.handlers.loghandler import LogHandler
from ast import literal_eval

from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *
from exabox.infrapatching.core.ibclusterpatch import IBClusterPatch
from exabox.infrapatching.core.ibfabricpatch import IBFabricPatch
from exabox.ovm.clumisc import OracleVersion
from defusedxml import ElementTree as ET
from exabox.infrapatching.utils.utility import mGetInfraPatchingConfigParam, mTruncateErrorMessageDescription, isInfrapatchErrorCode, runInfraPatchCommandsLocally, mQuarterlyVersionPatternMatch, mIsLatestTargetVersionAllowed
from exabox.infrapatching.utils.infrapatchexecutionvalidator import InfrapatchExecutionValidator

class ebCluPatchDispatcher(LogHandler):
    """
    It parses an input file and sends recursive calls to exacloud. Monitors the requests.

    Handles the patch orchestration:
        * One patch per cluster allowed at a given time
        * One ibswitch patch per fabric allowed at a given time.
        * If an ibswitch patch is running, then any cluster inside of the fabric should be running
          a patch.

    """

    LOG_DIRECTORY = 'log/patch/'
    LATEST_VER_FROM_FILESYSTEM = 'fileSystem'

    REGISTRY_ENTRY = 'patch_monitor_cmd'
    SLEEP_TIME = 30
    RETRY_TIME = 10
    EXACLOUD_PATCH_WORKING_SPACE_MB = 0
    CHECK_FOLDER_EXISTS_RETRY_TIME_IN_SECONDS = 3

    STEP_PARSE_JSON = 'parse_json_file'
    STEP_DOWNLOAD = 'download_patch_files'
    STEP_POPULATE_TABLES = 'populate_tables'
    STEP_MONITOR = 'patch_monitor'
    OCIEXACC_LOC = ''

    DISPATCH_STEP_LIST = [STEP_PARSE_JSON, STEP_DOWNLOAD, STEP_POPULATE_TABLES, STEP_MONITOR]

    MAX_RANDOM_TIME_VALUE = 60
    MIN_RANDOM_TIME_VALUE = 10

    def __init__(self, aJob=None):
        super(ebCluPatchDispatcher, self).__init__()

        from exabox.ovm.clucontrol import exaBoxCluCtrl

        self.__exacloud_calls = []
        self.__ibFabrics = []
        self.__expected_requests = 0
        self.__done_requests = []
        self.__pending_requests = []
        self.__reqObj = None
        self.__agent = True
        self.__node = None
        self.__hostname = None
        self.__logDir = None
        self.__zipFilesDir = None
        self.__object_store = {}
        self.__oss_patch_key = None
        self.__json_status = None
        self.__latest_verion_source_loc = self.LATEST_VER_FROM_FILESYSTEM
        self.__acquire_lock = False
        self.__cluster_key = None
        self.__child_request_uuid = None

        _get_context = get_gcontext()

        # Create exaBoxCluCtrl object for its usage inside
        # ebCluPatchDispatcher class.
        self.__node = exaBoxNode(_get_context, aLocal=True)
        self.__node.mConnect(aHost="localhost")
        self.__cluctrl = exaBoxCluCtrl(_get_context, self.__node)

        # Get Patchpayload location.
        if not self.mGetPatchPayLoad():
            self.mPatchLogError("Patch Stage location for ociexacc environment not specified in exabox.conf")
        self.PATCH_PAYLOADS_DIRECTORY = self.mGetPatchPayLoad()

        # Set request object. If not aJob
        self.mSetRequestObj(aJob)

    def mSetRequestObj(self, aJob=None):
        """
        Sets patch request object (Job).
        """

        class _SimpleJob(object):
            def __init__(self):
                self.__uuid = str(uuid4())
                self.__statusInfo = ""

            def mGetUUID(self):
                return self.__uuid

            def mGetWorker(self):
                return 0

            def mGetStatusInfo(self):
                return self.__statusInfo

            def mSetStatusInfo(self, aStatus):
                self.__statusInfo = aStatus

        # If not aJob is provided, then it creates a 'fake' job.
        # This help us to have a specific guid to handle the master
        # patch request lock. One patch request must run at a tim

        if not aJob:
            self.__reqObj = _SimpleJob()
            self.__agent = False
        else:
            self.__reqObj = aJob

    def mGetPatchPayLoad(self):
        """
        In case of OCI EXACC environemnts, PatchPayload details are fetched
        from ociexacc_exadata_patch_download_loc parameter as per details from
        the exabox.conf file.
        """

        patch_payloads_directory = 'PatchPayloads/'
        self.OCIEXACC = self.__cluctrl.mCheckConfigOption('ociexacc')
        if self.OCIEXACC == "True":
            self.OCIEXACC_LOC = self.__cluctrl.mCheckConfigOption('ociexacc_exadata_patch_download_loc').strip()
            if (self.OCIEXACC_LOC == '' or self.OCIEXACC_LOC == None or not self.OCIEXACC_LOC):
                patch_payloads_directory = False
            else:
                patch_payloads_directory = self.OCIEXACC_LOC + 'PatchPayloads/'
        else:
            self.mPatchLogInfo('*** ociexacc parameter is set to False. Retaining the patch path to default exacloud location.')
        return patch_payloads_directory

    def mGetRequestObj(self):
        """
        Gets patch request object (Job).
        """

        return self.__reqObj

    def mUpdateStatusFromList(self, aStatus, aStep, aComment=''):
        """
        Updates the patch request status for the initial (and common to all patches) steps.
        """

        if not self.__agent:
            return

        _reqobj = self.mGetRequestObj()

        if _reqobj:
            _db = ebGetDefaultDB()
            # First steps are set to be the 15% of all the patching operation
            # The other 85% is divided in the number of requests sent to exacloud
            _pos = str(int((15.0 / len(self.DISPATCH_STEP_LIST)) * (self.DISPATCH_STEP_LIST.index(aStep) + 1)))
            if aComment:
                aStep += '-' + aComment

            _reqobj.mSetStatusInfo(str(aStatus) + ':' + _pos + ':' + aStep)
            _db.mUpdateStatusRequest(_reqobj)

    def mUpdateStatusFromRequests(self):
        """
        Updates the patch request status in order of the number of exacloud
        recursive requests completed.
        """

        if not self.__agent:
            return

        _reqobj = self.mGetRequestObj()

        if _reqobj:
            _db = ebGetDefaultDB()

            # Create statusinfo comment
            _comment = f"pending[{len(self.__pending_requests)}/{self.__expected_requests}]_done[{len(self.__done_requests)}/{self.__expected_requests}]"
            # Get current status from db
            _status = _reqobj.mGetStatusInfo()
            if _status:
                # There is always a 15% done for the initial steps. Other 85% is from requests being executed.
                _pos = str(15 + int((85.0 / self.__expected_requests) * (len(self.__done_requests))))
                # We change only the comment and percentage instead of all the status
                _s = _status.split('-')[0].split(':')
                _reqobj.mSetStatusInfo(_s[0] + ':' + _pos + ':' + _s[2] + '-' + _comment)
            _db.mUpdateStatusRequestWithLock(_reqobj)

    def mLockPatchCmd(self):
        """
        Acquires patch lock. Only one master patch request must be executed at a time.
        """

        _db = ebGetDefaultDB()
        _range_of_random_numbers = []

        # Get the request
        _job = self.mGetRequestObj()
        if not _job:
            self.mPatchLogError("Patch job object is empty. Nothing to be done")
            return False

        # for the initial 10 attempts, _factor can be 2, which means that the range of random values would
        # be from 10..30. However, if we go beyond 10, it is possible that the system is busy and with more
        # processes competing for the lock, increase the range to be 10..60 to give more time
        # Typically, once acquired, the process holds the lock for about 1 minute if no issues 
        _factor = 2
        _max_retries = int(mGetInfraPatchingConfigParam('max_retries_to_acquire_lock'))
        _retry = _max_retries
        # Try multiple times to get the lock for the reason that user can submit
        # multiple cluster requests at the same time.
        while _retry > 0:
            # Check if there is another patch-cluster request running. We use registry table here.
            if _db.mCheckRegEntry(self.REGISTRY_ENTRY):
                self.mPatchLogWarn("mLockPatchCmd: Currently another master patch request is in progress, waiting until lock is released.")

                # Getting a list of integers between 10 and 30 to be used as an input for the
                # secrets.SystemRandom().choice module below.
                _range_of_random_numbers = [_number_random for _number_random in range(self.MIN_RANDOM_TIME_VALUE,
                                            int(self.MAX_RANDOM_TIME_VALUE/_factor))]

                # Pick random integer between 10 and 30 using secrets module
                # from the _range_of_random_numbers list.
                sleep(secrets.SystemRandom().choice(_range_of_random_numbers))
                _retry -= 1
                if _retry < (_max_retries - 10):
                    _factor = 1
            else:
                break
        else:
            self.mPatchLogError("mLockPatchCmd: In-spite of multiple attempts, could not get the master lock")
            return False

        # Acquire lock
        _db.mSetRegEntry(self.REGISTRY_ENTRY, 'True', str(_job.mGetUUID()), str(_job.mGetWorker()))

        self.mPatchLogInfo(
            f"mLockPatchCmd - Set registry entry: UUID = {str(_job.mGetUUID())}, Worker Id = {str(_job.mGetWorker())}")
        return True

    def mReleasePatchCmd(self):
        """
        Releases the patch lock. It deletes the entry in registry table.
        """

        # Get the request
        _job = self.mGetRequestObj()
        if not _job:
            self.mPatchLogError("mReleasePatchCmd: Patch job object is empty. Nothing to be done")
            return False

        _db = ebGetDefaultDB()
        # Delete row from registry to release patch-cluster cmd
        _db.mDelRegEntry(self.REGISTRY_ENTRY)

        self.mPatchLogInfo(
            f"mReleasePatchCmd - Delete registry entry: UUID = {str(_job.mGetUUID())}, Worker Id = {str(_job.mGetWorker())}")

    def mCheckLocalIBFabric(self, aSha512):
        """
        Checks the existance of an ibfabric with same sha512sum.
        It return the local list index for that ibfabric.
        """

        for _index, _fabric in enumerate(self.__ibFabrics):
            if _fabric.mGetSha512() == aSha512:
                return _index
        return -1

    def mAreClustersRepeated(self, aJson):
        """
        Checks if a xml cluster was already mentioned in the JSON file.
        """

        ### TBD - Change the way we do this check:
        # Right now we only compare the oeda xml path. However, we should
        # open each file just to be sure that the cluster is not the same
        _xmls = []

        # Iterate in JSON entries
        for _entry in aJson['Params']:
            if 'Clusters' in _entry:
                for _cluster in _entry['Clusters']:
                    if 'xml_oeda' in _cluster:
                        # Bug30014992: Decode cluster xml using Base64 format
                        # and then compare the cluster name.
                        _xml_oeda_data = b64decode(_cluster['xml_oeda']).decode('utf8')

                        # Read cluster/customer name from oeda xml
                        _cluster_name = self.mReadClusterNameFromOedaXml(_xml_oeda_data)

                        if _cluster_name in _xmls:
                            self.mPatchLogError(
                                f"Cluster oeda xml for rack {_cluster_name} is used in more than one entry in JSON file.")
                            return True
                        _xmls.append(_cluster_name)
        return False

    def mCheckPatchFileExistInFileSystem(self):
        """
        Check the existance of required exadata patch files in local file system.
        """
        _rc = PATCH_SUCCESS_EXIT_CODE
        _version_common_directory = None
        for _version in self.__object_store.keys():
            # Skip validation for LATEST - it's for DOM0 exasplice and will be resolved by handlers
            if _version and _version.upper() == 'LATEST':
                self.mPatchLogInfo(f"Skipping filesystem validation for version '{_version}' - will be resolved by handlers")
                continue

            for _file in set(self.__object_store[_version]['files']):
                _version_directory = os.path.join(self.PATCH_PAYLOADS_DIRECTORY, _version, _file)

                """
                If dbserver.patch.zip from PatchPayloads/DBPatchFile exists, use this for patching 
                otherwise check for dbserver.patch.zip from PatchPayloads/version/DBPatchFile directory
                """
                if _file == KEY_NAME_DBPatchFile:
                    _version_directory = os.path.join(_version_directory, "dbserver.patch.zip")
                    if os.path.exists(_version_directory):
                        _version_common_directory = os.path.join(self.PATCH_PAYLOADS_DIRECTORY, _file, "dbserver.patch.zip")
                        if _version_common_directory and os.path.exists(_version_common_directory) is True:
                            self.mPatchLogInfo(f"Checking for the latest dbserver.patch.zip between {str(_version_common_directory)} and {str(_version_directory)}")
                            _version_directory = self.mCompareDbserverPatchFiles(_version_directory, _version_common_directory)
                    self.mPatchLogInfo(f"dbserver.patch.zip from {_version_directory} is used for patching")
                    _version_directory = os.path.dirname(_version_directory)

                if _version_directory and os.path.isdir(_version_directory) is True:
                    _version_directory = os.path.abspath(_version_directory)
                    _listfile = os.listdir(_version_directory)

                    if len(_listfile) <= 0:
                        self.mPatchLogError(f"Patch file not found in '{_version_directory}'")
                        _suggestion_msg = f"Patch file not found in '{_version_directory}'"
                        _rc = MISSING_PATCH_FILES
                        self.mAddDispatcherError(_rc, _suggestion_msg)
                        return _rc
                else:
                    self.mPatchLogError(f"Patch directory '{_version_directory}' not found")
                    _suggestion_msg = f"Patch directory '{_version_directory}' not found"
                    _rc = MISSING_PATCH_DIRECTORY
                    self.mAddDispatcherError(_rc, _suggestion_msg)
                    return _rc
        return _rc

    def mGetDbserverPatchVersionDetails(self, aDbPatchFileDir):
        """
         This method returns the db patch file along with version based 
         on the input DB patch file path provided.

         -bash-4.4$ /bin/unzip -l /scratch/araghave/ecra_installs/abhi/mw_home/user_projects/
         domains/exacloud/PatchPayloads/DBPatchFile/dbserver.patch.zip | /bin/grep dbserver_ | 
         /bin/head -1 | /bin/awk '{print $4}' | /bin/tr -d "/"
         dbserver_patch_250119
         -bash-4.4$
        """
        _version = None
        _db_patch_file = None
        try:
            _cmd_list = []
            _out = []
            # Get Dbserver patch version details.
            _db_patch_file = os.path.join(aDbPatchFileDir)
            _cmd_list.append(["/bin/unzip", "-l", _db_patch_file])
            _cmd_list.append(["/bin/grep", "dbserver_"])
            _cmd_list.append(["/bin/head", "-1"])
            _cmd_list.append(["/bin/awk", '{print $4}'])
            _cmd_list.append(["/bin/tr", "-d", '/'])
            _cmd_list.append(["/bin/cut", "-d.", "-f1"])
            _rc, _o = runInfraPatchCommandsLocally(_cmd_list)
            if _o:
                _version = ((_o.split("\n"))[0]).split("_")[2]
        except Exception as e:
            self.mPatchLogWarn("Error in generating dbserver patch version. Error: %s" % str(e))
            self.mPatchLogTrace(traceback.format_exc())
        return _version

    def mCompareDbserverPatchFiles(self, aOldDbPatchFile, aNewDbPatchFile):
        """
         This method checks for the dbserver patch files staged at common
         and the exadata version stage locations and return the LATEST
         based on the date format details in the file naming convention.

         In the below example, 2 dbserver patch zip locations are provided
         as input for comparison to return the LATEST patch.

          [ araghave_dbserver ] bash-4.2$  unzip -l
          PatchPayloads/DBPatchFile/dbserver.patch.zip | grep 'dbserver_patch_' | head -1
            0  10-18-2023 00:09   dbserver_patch_231017/
          [ araghave_dbserver ] bash-4.2$

          [ araghave_dbserver ] bash-4.2$ unzip -l
          PatchPayloads/23.1.24.0.0.250306.1/DBPatchFile/dbserver.patch.zip | grep
          'dbserver_patch_' | head -1
            0  03-14-2025 00:00   dbserver_patch_250313/
          [ araghave_dbserver ] bash-4.2$

          -bash-4.2$ unzip -l PatchPayloads/DBPatchFile/dbserver.patch.zip | head -4
          Archive:  PatchPayloads/DBPatchFile/dbserver.patch.zip
           Length      Date    Time    Name
          ---------  ---------- -----   ----
                0  09-18-2024 23:46   dbserver_patch_240915.1/
          -bash-4.2$

          Here dbserver_patch_250313 is LATEST compared to dbserver_patch_231017 and
          will be consumed for patching.
        """
        _old_db_patch_file_date_format = None
        _new_db_patch_file_date_format = None
        try:
            _old_db_patch_file_date_format = self.mGetDbserverPatchVersionDetails(aOldDbPatchFile)
            _new_db_patch_file_date_format = self.mGetDbserverPatchVersionDetails(aNewDbPatchFile)

            if _old_db_patch_file_date_format and _new_db_patch_file_date_format:
                if int(_old_db_patch_file_date_format) > int(_new_db_patch_file_date_format):
                    self.mPatchLogInfo(f"{aOldDbPatchFile} is the LATEST dbserver patch file available based on the date.")
                    return aOldDbPatchFile
                elif int(_old_db_patch_file_date_format) < int(_new_db_patch_file_date_format):
                    self.mPatchLogInfo(f"{aNewDbPatchFile} is the LATEST dbserver patch file available based on the date.")
                    return aNewDbPatchFile
                else:
                    self.mPatchLogInfo(f"Both the dbserver patch files have the same date: {_new_db_patch_file_date_format} and either of them can be used for patching.")
                    return aNewDbPatchFile
            else:
                self.mPatchLogInfo("DBPatch file not found in either of the Patch Stage locations.")
                return None
        except Exception as e:
            self.mPatchLogWarn("Error in generating dbserver patch version file for patching. Error: %s" % str(e))
            self.mPatchLogTrace(traceback.format_exc())
            return None

    def mParsePatchJson(self, aOptions):
        """
        Parse json input file. It fills a dictionary with each call that
        should be done to exacloud.
        Returns a tuple containing two values: the first indicates the error code and the second is 
        the error suggestion message for error scenarios
        """
        _invalid_json_sug_msg = "Failed to validate the input configuration file."
        # Valid target types
        _valid_plugin_types = ['domu', 'dom0', 'dom0domu', 'dom0+dom0domu', 'dom0domu+dom0']

        _jconf = aOptions.jsonconf

        # For each entry in aParams, we can have multiple clusters.
        # This means that for each entry, we will iterate on each on each cluster:
        #       One worker per cluster (even it the cluster has multiple target_types)
        #
        # for entry in json_entries:
        #   for cluster in entry['Clusters']:
        #       Append a new call to exacloud_calls list
        #
        # XML files can't be called in different entries. Each xml must be
        # mentioned only once per JSON

        if _jconf and 'Params' in _jconf.keys():
            # Check xml files are not repeated
            if self.mAreClustersRepeated(_jconf):
                return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

            def mParseLatestVersion(aPatchFile, aVersion, aOperation, aTargetType=None, aIsExasplice=False):
                """
                This function replaces the 'LATEST' with actual latest
                value in patch path and also construct correct path for the
                patching file.
                Returns a tuple containing three values: the first indicate the error code, the second is the patch file name,
                and the third is the error suggestion message for error scenarios
                """
                _msg = ""
                _dom0YumRepo = False
                _DBPatchFileDir = False
                _domuYumRepo = False
                _cellPatchFileDir = False
                _switchPatchFileDir = False
                if aPatchFile.find(KEY_NAME_Dom0_YumRepository) > -1:
                    _dom0YumRepo = True

                if aPatchFile.find(KEY_NAME_DBPatchFile) > -1:
                    _DBPatchFileDir = True

                if aPatchFile.find(KEY_NAME_Domu_YumRepository) > -1:
                    _domuYumRepo = True

                if aPatchFile.find(KEY_NAME_CellPatchFile) > -1:
                    _cellPatchFileDir = True

                if aPatchFile.find(KEY_NAME_SwitchPatchFile) > -1:
                    _switchPatchFileDir = True

                # No bundle comparison or validation required in
                # case of oneoff, oneoffv2 patching.
                if aOperation in [ TASK_ONEOFF, TASK_ONEOFFV2 ]:
                    self.mPatchLogInfo(f"Patch file version validations are skipped during oneoff and oneoffv2 operations.")
                    return PATCH_SUCCESS_EXIT_CODE, aPatchFile, _msg

                # Skip path validation for DOM0 exasplice with LATEST - handlers will resolve it later
                if (aVersion and aVersion.upper() == 'LATEST' and
                    aTargetType and aTargetType.lower() == PATCH_DOM0 and
                    aIsExasplice):
                    self.mPatchLogInfo("Skipping path validation for DOM0 exasplice LATEST - will be resolved by handlers")
                    return PATCH_SUCCESS_EXIT_CODE, aPatchFile, _msg

                # If directory path is not having 'LATEST' string and it's not exacc, then
                # no job here; simply return (aPatchFile) as it is.
                if not _DBPatchFileDir and ((not aPatchFile or aPatchFile.find('LATEST') == -1) and self.OCIEXACC != 'True'):
                    self.mPatchLogInfo(f"mParseLatestVersion: PatchFile = '{aPatchFile}' ")
                    return PATCH_SUCCESS_EXIT_CODE, aPatchFile, _msg

                if not aVersion:
                    self.mPatchLogError(f"Invalid input version: {aVersion} ")
                    return INCORRECT_INPUT_JSON, "", _invalid_json_sug_msg

                aPatchFile = aPatchFile.replace('LATEST', aVersion)
                if self.OCIEXACC == "True":
                    aPatchFile = os.path.join(self.PATCH_PAYLOADS_DIRECTORY, aVersion, \
                                              aPatchFile.rstrip('/').split('/')[-1])

                # If PatchPayloads/DBPatchFile/ is found then use dbserver.patch.zip from PatchPayloads/DBPatchFile/
                # otherwise use from PatchPayloads/version/DBPatchFile/
                if _DBPatchFileDir:
                    if self.OCIEXACC == "True":
                        aPatchFile = os.path.join(aPatchFile, "dbserver.patch.zip")
                    if os.path.exists(aPatchFile):
                        _version_common_directory = os.path.join((Path(os.path.dirname(aPatchFile))).parent.parent, "DBPatchFile/dbserver.patch.zip")
                        if _version_common_directory and os.path.exists(_version_common_directory) is True:
                            self.mPatchLogInfo(f"Checking for the latest dbserver.patch.zip between {str(_version_common_directory)} and {str(aPatchFile)}")
                            aPatchFile = self.mCompareDbserverPatchFiles(aPatchFile, _version_common_directory)
                    self.mPatchLogInfo("dbserver.patch.zip from %s is used for patching" % aPatchFile)
                    aPatchFile = os.path.dirname(aPatchFile)

                if os.path.isdir(aPatchFile) is True:
                    aPatchFile = os.path.abspath(aPatchFile)
                    _listfile = os.listdir(aPatchFile)

                    # Sample Path for dom0YumRepo for 19.3.6 version
                    # ol7 is for KVM
                    # aPatchFile =
                    # exacloud/PatchPayloads/19.3.6.0.0.200317/Dom0YumRepository/exadata_ol7_19.3.6.0.0.200317_Linux-x86-64.zip,
                    # exacloud/PatchPayloads/19.3.6.0.0.200317/Dom0YumRepository/exadata_ovs_19.3.6.0.0.200317_Linux-x86-64.zip
                    # if there are multiple files are PatchPayloads/19.3.5.0.0.200228/Dom0YumRepository/
                    _dom0files = []
                    if _dom0YumRepo is True and len(_listfile) > 1:
                        for f in (_listfile):
                            _dom0files.append(os.path.join(aPatchFile, f))
                        aPatchFile = ','.join(_dom0files)
                        self.mPatchLogInfo(f"Dom0Repository file for LATEST Version is {aPatchFile} ")
                    elif _domuYumRepo is True:
                        files = glob.glob(os.path.join(aPatchFile, f'exadata_*_{aVersion}_Linux-x86-64.zip'))
                        if files:
                            aPatchFile = files[0]
                            self.mPatchLogInfo(f"DomuYumRepository file for LATEST Version is {aPatchFile} ")
                        else:
                            _msg = f"No matching file found in {aPatchFile} for version {aVersion}"
                            self.mPatchLogError(_msg)
                            return MISSING_PATCH_FILES, "", _msg
                    elif _cellPatchFileDir is True:
                        aPatchFile = os.path.join(aPatchFile, aVersion + ".patch.zip")
                    elif _switchPatchFileDir is True:
                        aPatchFile = os.path.join(aPatchFile, aVersion + ".switch.patch.zip")
                    elif _DBPatchFileDir is True:
                        aPatchFile = os.path.join(aPatchFile, "dbserver.patch.zip")
                    elif len(_listfile) == 1:
                        # if there is a single file under PatchPayloads/19.3.5.0.0.200228/<any directory> , proceed as before
                        aPatchFile = os.path.join(aPatchFile, _listfile[0])
                    else:
                        _msg = f"Patch file is not found in {aPatchFile} "
                        self.mPatchLogError(_msg)
                        return MISSING_PATCH_FILES, "", _msg
                else:
                    _msg= f"Patch directory path does not exist: {aPatchFile} "
                    self.mPatchLogError(_msg)
                    return MISSING_PATCH_DIRECTORY, "", _msg
                return PATCH_SUCCESS_EXIT_CODE, aPatchFile, _msg

            # end of method mParseLatestVersion()

            # Iterate on each entry in Params
            for _entry in _jconf['Params']:
                _operation = ''
                _payload = ''
                _style = ''
                _backupmode = ''
                _enableplugins = ''
                _plugintypes = ''
                _fedramp = ''
                _patch_retry_flag = ''
                _patch_master_request_id = ''
                _isMVM = ''
                _shared_env = ''
                _storageType = ''
                _additionaloption = {}
                _version = ''
                _target = []
                _download_files = []
                _computeNodeList = {}
                _storageNodeList = {}
                _dom0domuDetails = {}
                _eluTargetVersionToNodeMappings = {}
                _computeNodeListByAlias = {}
                _idemPotencyData = {}
                _infra_patch_plugin_metadata = {}
                _oneoff_script_alias = ''
                _isADBS = ''

                # Get patch operation
                if 'Operation' not in _entry:
                    self.mPatchLogError("'Operation' not provided in json entry")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg
                elif _entry['Operation'].lower() not in [TASK_BACKUP_IMAGE,
                                                         TASK_PREREQ_CHECK,
                                                         TASK_PATCH,
                                                         TASK_ROLLBACK_PREREQ_CHECK,
                                                         TASK_ROLLBACK,
                                                         TASK_POSTCHECK,
                                                         TASK_ONEOFF,
                                                         TASK_ONEOFFV2
                                                         ]:
                    self.mPatchLogError(f"Invalid 'Operation' value({_entry['Operation']}) in json entry.")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg
                else:
                    _operation = _entry['Operation']

                # Get payload type. Default: release
                if 'PayloadType' in _entry and _entry['PayloadType'].lower() in [PAYLOAD_RELEASE, \
                                                                                 PAYLOAD_NON_RELEASE]:
                    _payload = _entry['PayloadType']
                else:
                    self.mPatchLogError("PayloadType not defined in json entry.")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                # Get operation style. Default: rolling
                if 'OperationStyle' in _entry and _entry['OperationStyle'].lower() in [
                    OP_STYLE_ROLLING,
                    OP_STYLE_AUTO,
                    OP_STYLE_NON_ROLLING]:
                    _style = _entry['OperationStyle']
                else:
                    self.mPatchLogError("OperationStyle not provided in json entry.")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                # Get backup mode. Default: no
                if 'BackupMode' in _entry and _entry['BackupMode'].lower() in ['', OP_BACKUPMODE_NO,
                                                                               OP_BACKUPMODE_YES]:
                    _backupmode = _entry['BackupMode']
                else:
                    self.mPatchLogError("BackupMode either not provided or invalid entry in json entry.")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                # Get additional options if any
                if 'AdditionalOptions' in _entry:
                    _additionaloption = _entry['AdditionalOptions']

                # Get StorageNodeList options if any
                if 'StorageNodeList' in _entry:
                    _storageNodeList = _entry['StorageNodeList']

                # Get Dom0domUDetails options if any
                if 'Dom0domUDetails' in _entry:
                    _dom0domuDetails = _entry['Dom0domUDetails']

                # Get ComputeNodeList options if any
                if 'ComputeNodeList' in _entry:
                    _computeNodeList = _entry['ComputeNodeList']

                # Get ComputeNodeList Sorted by Alias options if any
                if 'ComputeNodeListByAlias' in _entry:
                    _computeNodeListByAlias = _entry['ComputeNodeListByAlias']

                # Get IdemPotencyData in case of a retry
                if 'Idempotency' in _entry:
                    _idemPotencyData = _entry['Idempotency']

                # Get InfraPatchPluginMetaData in case of a oneoffv2 patch operation
                if 'InfraPatchPluginMetaData' in _entry:
                    _infra_patch_plugin_metadata = _entry['InfraPatchPluginMetaData']

                # Get OneoffScriptAlias in case of a oneoffv2 patch operation
                if 'OneoffScriptAlias' in _entry:
                    _oneoff_script_alias = _entry['OneoffScriptAlias']

                # Get MultiVM enables or not for EXACS
                if 'isMVM' in _entry:
                    _isMVM = _entry['isMVM']
                    # check for shared env
                    if _isMVM.upper() == 'YES':
                        _shared_env = 'True'

                # Indicator of exascale env
                if 'storageType' in _entry:
                    _storageType = _entry['storageType']

                # If it is ADBS
                if 'adb_s' in _entry:
                    _isADBS = _entry['adb_s']

                _is_exasplice = False
                if _additionaloption and 'exasplice' in _additionaloption[0] \
                    and _additionaloption[0]['exasplice']:
                    if _additionaloption[0]['exasplice'].lower() == 'yes':
                        _is_exasplice = True

                # Get FedrampEnabled value
                if 'FedrampEnabled' in _entry:
                    _fedramp = _entry['FedrampEnabled']
                    self.mPatchLogInfo(f"Current FedrampEnabled value in EcsProperty Table : {_fedramp}")
                else:
                    self.mPatchLogInfo("FedrampEnabled value is not configured or used in EcsProperty Table")

                # Get target version
                if 'TargetVersion' in _entry:
                    # Bug-26830429 - Evaluate the available latest version
                    if _entry['TargetVersion'].upper() == 'LATEST':
                        # Check if LATEST is allowed as literal for dom0 + exasplice=yes
                        _target_types = _entry.get('TargetType', [])
                        _target_type = _target_types[0] if len(_target_types) == 1 else None
                        _exasplice_value = 'yes' if _is_exasplice else 'no'

                        if mIsLatestTargetVersionAllowed(_entry['TargetVersion'], _target_type, _exasplice_value):
                            # Allow LATEST as literal string for dom0 exasplice patching
                            self.mPatchLogInfo(f"Allowing LATEST as literal targetVersion for DOM0 exasplice patching")
                            _version = _entry['TargetVersion']
                        else:
                            self.mPatchLogInfo("Finding the LATEST target version.")
                            _version = self.mGetLatestPatchVersion()
                    else:
                        _version = _entry['TargetVersion']
                        self.mPatchLogInfo(f"The TargetVersion selected: {_version} ")

                    if _version not in self.__object_store:
                        self.__object_store[_version] = {'files': _download_files,
                                                         'dir': None}
                else:
                    self.mPatchLogError("TargetVersion not defined in json entry.")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                # Get target type: dom0, domu, cell, ibswitch
                if 'TargetType' in _entry:
                    for _ttype in _entry['TargetType']:
                        if _ttype.lower() in [PATCH_DOM0, PATCH_CELL, PATCH_SWITCH,
                                              PATCH_IBSWITCH, PATCH_DOMU]:
                            _target.append(_ttype.lower())
                        else:
                            self.mPatchLogWarn(f"TargetType '{_ttype}' not valid. Input will be ignored")
                else:
                    self.mPatchLogError("'TargetType' not provided in json entry")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                # Get Run Plugin value. Default: no
                if 'EnablePlugins' in _entry:
                    if _entry['EnablePlugins'].lower() in ['yes', 'no']:
                        _enableplugins = _entry['EnablePlugins'].lower()
                    else:
                        self.mPatchLogError(f"Invalid plugins option is specified: '{_entry['EnablePlugins']}'")
                        return INCORRECT_INPUT_JSON, _invalid_json_sug_msg
                else:
                    self.mPatchLogError("EnablePlugins param either not provided or invalid entry in json entry.")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                # Get the param value which indicate whether we need to run
                # plugins on dom0/domu/dom0's domu. Default: none
                if 'PluginTypes' in _entry:
                    if _entry['PluginTypes']:
                        _tmp_plugin_types = _entry['PluginTypes'].strip()
                        _tmp_plugin_types = _tmp_plugin_types.replace(" ", "")
                        _tmp_plugin_types = _entry['PluginTypes'].lower()

                        # Validate plugins types
                        if _enableplugins == 'yes' and _tmp_plugin_types in ["", " ", "none"]:
                            self.mPatchLogError(f"Invalid plugin types specified: '{_tmp_plugin_types}'.")
                            return INCORRECT_INPUT_JSON, _invalid_json_sug_msg
                        elif _enableplugins == 'yes' and PATCH_DOM0 in _target:
                            if not _tmp_plugin_types in ['dom0', 'dom0domu', 'dom0+dom0domu', 'dom0domu+dom0']:
                                self.mPatchLogError(f"Invalid plugin types specified for dom0: '{_tmp_plugin_types}'.")
                                return INCORRECT_INPUT_JSON, _invalid_json_sug_msg
                        elif _enableplugins == 'yes' and PATCH_DOMU in _target:
                            if not _tmp_plugin_types in ['domu']:
                                self.mPatchLogError(f"Invalid plugin types specified for domU: '{_tmp_plugin_types}'.")
                                return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                        # Just copy as it's if no plugin enable specified.
                        _plugintypes = _tmp_plugin_types
                else:
                    self.mPatchLogError("PluginTypes param either not provided or invalid entry in json entry.")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                # Get patching request retry flag. Default: no
                if 'Retry' in _entry:
                    if _entry['Retry'].lower() in ['yes', 'no']:
                        _patch_retry_flag = _entry['Retry'].lower()
                    else:
                        self.mPatchLogError(f"Invalid Retry option is specified: '{_entry['Retry']}'")
                        return INCORRECT_INPUT_JSON, _invalid_json_sug_msg
                else:
                    self.mPatchLogError("Retry param either not provided or invalid entry in json entry.")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

                # Get patching master request id. Default: none
                if 'RequestId' in _entry:
                    _patch_master_request_id = _entry['RequestId'].lower()
                else:
                    self.mPatchLogError("RequestId param either not provided or invalid entry in json entry.")
                    return INCORRECT_INPUT_JSON, _invalid_json_sug_msg
                
                # Get ELU to Node Mappings
                if _is_exasplice and (PATCH_DOM0 in _target or PATCH_DOMU in _target) and 'ELUTargetVersiontoNodeMappings' in _entry:
                    _eluTargetVersionToNodeMappings = _entry['ELUTargetVersiontoNodeMappings']

                # If not clusters specified for this entry, then ignore
                if 'Clusters' not in _entry:
                    self.mPatchLogWarn("'Clusters' not provided in json entry. This entry will be ignored")
                    continue

                # Get patch files
                if _payload == PAYLOAD_RELEASE:
                    if PATCH_CELL in _target:
                        _download_files.append('CellPatchFile')

                    if _target in [ PATCH_IBSWITCH, PATCH_SWITCH ]:
                        if 'CellPatchFile' in _entry:
                            self.mPatchLogWarn("'SwitchPatchFile' not specified in json. 'CellPatchfile' will be used instead.")
                            _entry['SwitchPatchFile'] = _entry['CellPatchFile']
                        else:
                            ### ATENTION: CellPatchFile is added here because it is the same for cells and ibswitches
                            _download_files.append('SwitchPatchFile')

                    # Refer Exasplice repository in case of exasplice patching on dom0.
                    if PATCH_DOM0 in _target and _is_exasplice:
                        _download_files.append('DBPatchFile')
                        if not mQuarterlyVersionPatternMatch(_version):
                            _download_files.append('ExaspliceRepository')
                    elif PATCH_DOM0 in _target:
                        for _input in ['DBPatchFile', 'Dom0YumRepository']:
                            _download_files.append(_input)

                    if PATCH_DOMU in _target:
                        for _input in ['DBPatchFile', 'DomuYumRepository']:
                            _download_files.append(_input)
                else:
                    if 'PatchFile' not in _entry:
                        self.mPatchLogWarn("'PatchFile' not provided in json entry.")
                        _download_files.append('PatchFile')
                        _entry['PatchFile'] = None

                    # Call common paramters for this entry
                _call = {
                    'Operation': _operation,
                    'PayloadType': _payload,
                    'OperationStyle': _style,
                    'TargetType': _target,
                    'TargetVersion': _version,
                    'BackupMode': _backupmode,
                    'EnablePlugins': _enableplugins,
                    'PluginTypes': _plugintypes,
                    'Fedramp': _fedramp,
                    'Retry': _patch_retry_flag,
                    'RequestId': _patch_master_request_id,
                    'AdditionalOptions': _additionaloption,
                    "ComputeNodeList": _computeNodeList,
                    "ComputeNodeListByAlias": _computeNodeListByAlias,
                    "isMVM":_isMVM,
                    "shared_env":_shared_env,
                    "storageType":_storageType,
                    "StorageNodeList": _storageNodeList,
                    "Dom0domUDetails": _dom0domuDetails,
                    "ELUTargetVersiontoNodeMappings": _eluTargetVersionToNodeMappings,
                    "Idempotency": _idemPotencyData,
                    "InfraPatchPluginMetaData": _infra_patch_plugin_metadata,
                    "OneoffScriptAlias": _oneoff_script_alias,
                    "adb_s": _isADBS
                }

                # Save patch file or files necessary to run the patch.
                if _payload == PAYLOAD_RELEASE:

                    # Bug-26830429 - Construct the actual path for the target
                    # patch file if dir path has the 'LATEST' value.
                    for _ttype in _target:
                        if _ttype == PATCH_CELL:
                            _call['CellPatchFile'] = _entry['CellPatchFile']
                            # Construct path with latest version for patch file
                            _ret, _patch_file, _msg = mParseLatestVersion(_call['CellPatchFile'], _version, _call['Operation'])
                            if _ret == PATCH_SUCCESS_EXIT_CODE:
                                _call['CellPatchFile'] = _patch_file
                            if _ret != PATCH_SUCCESS_EXIT_CODE:
                                return _ret, _msg

                        elif _ttype in [ PATCH_IBSWITCH, PATCH_SWITCH ]:
                            _call['SwitchPatchFile'] = _entry['SwitchPatchFile']
                            # Construct path with latest version for patch file
                            _ret, _patch_file, _msg  = mParseLatestVersion(_call['SwitchPatchFile'], _version, _call['Operation'])
                            if _ret == PATCH_SUCCESS_EXIT_CODE:
                                _call['SwitchPatchFile'] = _patch_file
                            if _ret != PATCH_SUCCESS_EXIT_CODE:
                                return _ret, _msg


                        elif _ttype == PATCH_DOM0:
                            _call['DBPatchFile'] = _entry['DBPatchFile']
                            # Construct path with latest version for patch file
                            _ret, _patch_file, _msg  = mParseLatestVersion(_call['DBPatchFile'], _version, _call['Operation'], _ttype, _is_exasplice)
                            if _ret == PATCH_SUCCESS_EXIT_CODE:
                                _call['DBPatchFile'] = _patch_file
                            if _ret != PATCH_SUCCESS_EXIT_CODE:
                                return _ret, _msg

                            _call['Dom0YumRepository'] = _entry['Dom0YumRepository']
                            # Construct path with latest version for patch file
                            _ret, _patch_file, _msg  = mParseLatestVersion(_call['Dom0YumRepository'], _version, _call['Operation'], _ttype, _is_exasplice)
                            if _ret == PATCH_SUCCESS_EXIT_CODE:
                                _call['Dom0YumRepository'] = _patch_file
                            if _ret != PATCH_SUCCESS_EXIT_CODE:
                                return _ret, _msg

                        elif _ttype == PATCH_DOMU:
                            _call['DBPatchFile'] = _entry['DBPatchFile']
                            # Construct path with latest version for patch file
                            _ret, _patch_file, _msg  = mParseLatestVersion(_call['DBPatchFile'], _version, _call['Operation'])
                            if _ret == PATCH_SUCCESS_EXIT_CODE:
                                _call['DBPatchFile'] = _patch_file
                            if _ret != PATCH_SUCCESS_EXIT_CODE:
                                return _ret, _msg

                            _call['DomuYumRepository'] = _entry['DomuYumRepository']
                            _ret, _patch_file, _msg  = mParseLatestVersion(_call['DomuYumRepository'], _version, _call['Operation'])
                            if _ret == PATCH_SUCCESS_EXIT_CODE:
                                _call['DomuYumRepository'] = _patch_file
                            if _ret != PATCH_SUCCESS_EXIT_CODE:
                                return _ret, _msg
                else:
                    _call['PatchFile'] = _entry['PatchFile']
                    for _ttype in _target:
                        if _ttype == PATCH_DOM0:
                            if 'Dom0YumRepository' in _entry:
                                _call['Dom0YumRepository'] = \
                                    _entry['Dom0YumRepository']
                            break
                        if _ttype == PATCH_DOMU:
                            if 'DomuYumRepository' in _entry:
                                _call['DomuYumRepository'] = \
                                    _entry['DomuYumRepository']
                            break

                # Iterate on each cluster specified in this entry
                for _cluster in _entry['Clusters']:
                    if 'xml_oeda' in _cluster:
                        # Bug30014992: Decode cluster xml using Base64 and
                        # write into a file and give same reference to
                        # xml oeda
                        _xml_oeda_data = b64decode(_cluster['xml_oeda']).decode('utf8')

                        # Read cluster/customer name from oeda xml
                        _cluster_name = self.mReadClusterNameFromOedaXml(_xml_oeda_data)

                        _cluster_xml_path = os.path.join(self.__logDir,
                                                         "exadata_patching_oedaxml_" + _cluster_name + ".xml")

                        '''
                        Bug 32700880 and Bug 33113180 
                        Failed to write cluster oeda xml because log directory does not exists .
                        Happens only for EXACC. Hence, loop though, sleep and check for existence
                        '''
                        _retry_check_for_folder_counter = 10
                        while _retry_check_for_folder_counter > 0:
                            if os.path.exists(self.__logDir) is True:
                                self.mPatchLogInfo(f"Patch log location on exacloud: {self.__logDir}")
                                break
                            else:
                                self.mPatchLogWarn(
                                    f"Patch log location '{self.__logDir}' is not existing. Checking again after {self.CHECK_FOLDER_EXISTS_RETRY_TIME_IN_SECONDS} seconds")
                                sleep(self.CHECK_FOLDER_EXISTS_RETRY_TIME_IN_SECONDS)
                                _retry_check_for_folder_counter -= 1


                        try:
                            with open(_cluster_xml_path, "w") as cluserxmldata:
                                cluserxmldata.write(_xml_oeda_data)

                            self.mPatchLogInfo(f"Cluster oeda xml written to a file on exacloud: {_cluster_xml_path}")
                            _call['XmlOeda'] = _cluster_xml_path
                        except Exception as e:
                            self.mPatchLogError(
                                f"Fail to write the cluster oeda xml '{_cluster_xml_path}'. Error: {str(e)}")
                            self.mPatchLogError(f"The cluster {_cluster_name} will be ignored")
                            self.mPatchLogTrace(traceback.format_exc())
                            continue

                        if 'target_env' in _cluster and _cluster['target_env'] in [ENV_PRODUCTION, \
                                                                                   ENV_PREPRODUCTION,
                                                                                   ENV_DEVELOPMENT, \
                                                                                   ENV_TEST]:
                            _call['TargetEnv'] = _cluster['target_env']
                            _call['RackName'] = _cluster['rack_name']
                            # Add to object store only if necessary
                            if _download_files:
                                for _f in _download_files:
                                    if _f not in self.__object_store[_version]['files']:
                                        self.__object_store[_version]['files'].append(_f)
                        else:
                            self.mPatchLogError(
                                f"target_env not provided for xml '{_cluster_xml_path}'. This cluster will be ignored")
                            continue
                        # Append a new call to the list of exacloud calls to be done
                        self.__exacloud_calls.append(copy.deepcopy(_call))
                    else:
                        self.mPatchLogWarn("'xml_oeda' not found in cluster entry. Input will be ignored")
                self.ClusterCount = len(_entry['Clusters'])
            return PATCH_SUCCESS_EXIT_CODE, ""
        return INCORRECT_INPUT_JSON, _invalid_json_sug_msg

    def mCheckExacloudMnt(self):
        """
        Validates the disk space usage of thread and requests log location to
        accomdate newer logs once patching is complete. In the current case, if
        there is no space available on the logs location. Patching task would
        fail in the end due to unable to copy the logs from the patched nodes
        although upgrade was successful.
        """
        # Read exacloud patch working space size
        _rc = True
        self.EXACLOUD_PATCH_WORKING_SPACE_MB = self.__cluctrl.mCheckConfigOption('exacloud_patch_working_space_mb').strip()
        if (not self.EXACLOUD_PATCH_WORKING_SPACE_MB) or self.EXACLOUD_PATCH_WORKING_SPACE_MB == '' or (
                int(self.EXACLOUD_PATCH_WORKING_SPACE_MB) == 0):
            self.mPatchLogError(
                f"Invalid exacloud disk space configured to store exacloud thread and request logs : {self.EXACLOUD_PATCH_WORKING_SPACE_MB} , please validate the parameter 'exacloud_patch_working_space_mb' in exabox.conf and re-run patching.")
            _rc = False
        else:
            _df_cmd = "/bin/df -mP ."
            _in, _out, _err = self.__cluctrl.mExecuteCmd(_df_cmd)

            _df_cmd = "/bin/awk '{print $4}'"
            _in, _out, _err = self.__cluctrl.mExecuteCmd(_df_cmd, aStdIn=_out)

            _df_cmd = "/bin/grep -vi Avail"
            _in, _out, _err = self.__cluctrl.mExecuteCmd(_df_cmd, aStdIn=_out)
            _cluTotal = int(self.EXACLOUD_PATCH_WORKING_SPACE_MB) * int(self.ClusterCount)
            _output = _out.readlines()
            _out = _output[0].strip()
            if int(_out) < int(_cluTotal):
                self.mPatchLogInfo("\nDisk statistics on exacloud area before patch operation: ")
                self.mPatchLogInfo(f"   - Free disk space on exacloud area : {int(_out)} MB")
                self.mPatchLogInfo(
                    f"   - Disk space expected on exacloud area for thread and request logs: {(int(self.EXACLOUD_PATCH_WORKING_SPACE_MB) / 1024)}GB(Disk space required to store logs per cluster) * {(int(self.ClusterCount) / 1024)}(Number of clusters requested to patch) = {(int(_cluTotal) / 1024)}GB \n")
                _rc = False
        return _rc

    def mPopulatePatchTables(self, aOptions):
        """
        Populates the db tables with all the ibfabric, clusters and ibswitches
        information. It is possible that information is already in the db.
        """
        _rc = PATCH_SUCCESS_EXIT_CODE

        _fabricObj = None
        _fabricID = None
        _fabricIndex = None
        _cluName = None
        _clusterIndex = None

        _db = ebGetDefaultDB()

        # Iterate on each exacloud dictionary call
        for index, _call in enumerate(self.__exacloud_calls):
            # Create Cluster object
            _clu = IBClusterPatch(aOptions, _call, aCluDispatcher=self)
            _rc = _clu.mInitializeCluster()
            if _rc != PATCH_SUCCESS_EXIT_CODE:
                return _rc

            # Get sha512 and switch list that we got from ibswitches command/ It is necessary
            # to check wether the fabric it belongs to already exists or not
            _tmpSha512 = _clu.mGetIBFabricSha512()
            _tmpIBSwitches = _clu.mGetIBSwitchList()
            _cluName = _clu.mGetClusterName()

            # Check if the fabric is already in the local object list
            _fabricIndex = self.mCheckLocalIBFabric(_tmpSha512)
            _fabricID = -1
            # If fabric is not listed, then check in DB
            if _fabricIndex == -1:
                _row = _db.mCheckIBFabricEntry(aSha512=_tmpSha512)
                # If the sha512 was not found, the fabric doesn't exist or ibswitches in the fabric changed
                if not _row or len(_row) <= 5:
                    self.mPatchLogInfo(f"Fabric '{_tmpSha512}' not found in DB or data is incomplete")
                    self.mPatchLogInfo(f"Fabric {_tmpSha512} data: {_row}")
                    # Check if at least one of the switches are already in the table
                    _sw_row = _db.mCheckIBFabricIBSwitchesTable([_sw['hostname'] for _sw in _tmpIBSwitches])

                    # If found, then the fabric was already there but sha512 changed.
                    if _sw_row and len(_sw_row) > 1:
                        self.mPatchLogInfo("At least one switch was found in IBFabricIBSwitches table")
                        _row = _db.mCheckIBFabricEntry(aFabricID=_sw_row[1])
                        if _row and len(_row) > 5:
                            # Check if the fabric found is already in the local list
                            _fabricIndex = self.mCheckLocalIBFabric(_row[1])
                            if _fabricIndex == -1:
                                _fabricObj = IBFabricPatch(_row[0], _row[1], _row[2], _row[3], [], _row[4], _row[5])
                                self.__ibFabrics.append(_fabricObj)
                                _fabricIndex = len(self.__ibFabrics) - 1
                            else:
                                _fabricObj = self.__ibFabrics[_fabricIndex]
                        else:
                            self.mPatchLogError("IBFabric not found in DB or data is incomplete. Cluster xml entry will be ignored.")
                            self.mPatchLogError(f"IBFabric data: {_row}")
                            continue
                    # If there are no switches in the table, then we must add the new fabric
                    else:
                        self.mPatchLogInfo("No valid one switches were found in IBFabricIBSwitches table")
                        self.mPatchLogInfo(f"Switch found: {_sw_row}")
                        self.mPatchLogInfo(f"Adding IBFabric '{_tmpSha512}' to DB")
                        _db.mSetIBFabricEntry(_tmpSha512)
                        _row = _db.mCheckIBFabricEntry(aSha512=_tmpSha512)
                        if _row and len(_row) > 5:
                            _fabricObj = IBFabricPatch(_row[0], _row[1], _row[2], _row[3], [], _row[4], _row[5])
                            self.__ibFabrics.append(_fabricObj)
                            _fabricIndex = len(self.__ibFabrics) - 1
                        else:
                            self.mPatchLogError("IBFabric not found in DB or data is incomplete. Cluster xml entry will be ignored.")
                            self.mPatchLogError(f"IBFabric data: {_row}")
                            continue

                # If fabric was already registred in DB
                else:
                    self.mPatchLogInfo(f"IBFabric with id={_row[0]} already registered in DB")
                    _fabricObj = IBFabricPatch(_row[0], _row[1], _row[2], _row[3], [], _row[4], _row[5])
                    self.__ibFabrics.append(_fabricObj)
                    _fabricIndex = len(self.__ibFabrics) - 1

                if not _fabricObj:
                    self.mPatchLogError("IBFabric Object empty. Cluster xml entry will be ignored")
                    continue
            else:
                _fabricObj = self.__ibFabrics[_fabricIndex]
                self.mPatchLogInfo(
                    f"IBFabric '{_fabricObj.mGetSha512()}' with id={_fabricObj.mGetIBFabricID():d} found IBFabric local list")

            _fabricObj.mRefreshData()
            _fabricID = _fabricObj.mGetIBFabricID()
            # _fabric_busy_clu = eval(fabricObj.mGetBusyClustersList())

            ########### CLuster Check ###########

            # Set FabricID in cluster object
            _clu.mSetIBFabricID(_fabricID)

            # Check if cluster exists in fabric object
            _clusterIndex = _fabricObj.mCheckCluster(_cluName)

            # If cluster is not listed in the fabric, then check if it already exists in DB
            if _clusterIndex == -1:
                _row = _db.mCheckIBFabricClusterTable(aClusterName=_cluName)
                # If cluster not in DB, add a new entry
                if not _row:
                    self.mPatchLogInfo(f"Adding cluster '{_cluName}' to IBFabricCluster")
                    _db.mSetIBFabricClusterEntry(_clu)
                # Check one more time to get the Cluster ID
                _row = _db.mCheckIBFabricClusterTable(aClusterName=_cluName)
                # If cluster exists in DB
                if _row:
                    if int(_row[1]) == _fabricID:
                        _clu.mSetIBClusterID(int(_row[0]))
                        _clusterIndex = _fabricObj.mAddCluster(_clu)
                        self.mPatchLogInfo(
                            f"Cluster '{_row[2]}' clu_id={_row[0]} fabric_id={_row[1]} added to fabric's cluster local list")
                    else:
                        # TBD: We should check if there is anything running in that cluster. If not,
                        #      Then we should remove the entry and add it again.
                        self.mPatchLogInfo("Cluster not attached to the correct Fabric. Cluster xml entry will be ignored")
                        continue
                # Cluster not found in DB. Add a new entry
                else:
                    self.mPatchLogError(f"Cluster {_cluName} not found in DB. Cluster xml entry will be ignored")
                    continue
            # Cluster is already in the IBFabric Cluster List
            else:
                _clu = _fabricObj.mGetCluster(_clusterIndex)

            ##### IBSwitches Check ######

            # Get domain. We must get the domain from the switches lsited in the xml file.
            # ibswitches command list the hostname with no domain
            _xml_switches = _clu.mGetXMLIBSwitchList()
            _domain = ".".join(_xml_switches[0].split('.')[1:])
            # List of switches. We update the list of switches at the end
            _updatedList = []
            # List of ibswitch hostnames (from ibswitches command) with domain
            _ibswitches_output = [_sw['hostname'] + '.' + _domain for _sw in _tmpIBSwitches]

            # Iterate in all the ibswitches
            for _switch in _ibswitches_output:
                _add = True
                # Check if the ibswitch is already in DB
                _list = _db.mGetListOfIBFabricIBSwitches(_fabricID)
                for _row in _list:
                    if _switch.strip() == str(_row[2]).strip():
                        _add = False
                        break
                # If not, then add a new entry with the ibswitch
                if _add:
                    _db.mSetIBFabricIBSwitchesEntry(_fabricID, _switch)
                    self.mPatchLogInfo(f"Switch '{_switch}' added to IBFabric with id={_fabricID:d}")
                _updatedList.append(_switch)
            # Update the local list of switches for this fabric
            _fabricObj.mSetIBSwitches(_updatedList)

            # Set do_switches flag only if we are actuall doingany task in ibswitches
            _fabric_do_switches = str(_fabricObj.mGetDoSwitch()).lower()
            if _fabric_do_switches == 'no' and ( PATCH_IBSWITCH in _call['TargetType'] or PATCH_SWITCH in _call['TargetType']):
                self.mPatchLogInfo(f"Set do_switch to 'yes' in fabric with id={_fabricID:d}")
                _fabricObj.mSetDoSwitch('yes')
                _fabricObj.mUpdateDoSwitchDB()
        return _rc

    def mGetCountOfRequests(self):
        """
        Calculates the number of expected exacloud requests:
        One request per cluster + one request per ibfabric (ibswitch task)

        TODO: The following for loop assumes that, one dispatcher thread support one
              cluster patching request. But, it's better to support multiple cluster upgrade
              with single dispatcher thread.
        """

        _requests = 0

        # Skip the below validation in case of not required to
        # acquire  lock
        if not InfrapatchExecutionValidator.isSwitchFabricLockingMechanismEnabled():
            self.mPatchLogInfo("Validation to check for Switch/non-switch target patching to be run in parallel is skipped.")
            _requests += 1
            return _requests

        for _f in self.__ibFabrics:
            for _c in (_f.mGetCluObjects()):
                _call = _c.mGetCall()
                '''
                 Case 1 : when the cluster list is none or empty and the value of doswitch is yes 
                          and locking acquired for target is ibswitch, we need to set the request count 
                          to 0 and return as we do not want to proceed when an ongoing patch operation 
                          is related to ibswitch.

                          Concurrent requests to other racks that involve a shared ib fabric and an ibswitch-any 
                          other target scenario is not allowed.

                          -> Valid values for mGetBusyClustersList() are : integer values separated by spaces.
                          -> Valid values for mGetLockedFor() are : ibswitch/non_ibswitch/none
                          -> Valid values for mGetDoSwitch() are : yes/no
                '''
                if _f.mGetBusyClustersList() not in [ None, '' ] and ((_f.mGetDoSwitch().lower() == 'yes' and _f.mGetLockedFor().lower() in [ 'ibswitch' ]) or (_f.mGetLockedFor().lower() in [ 'non_ibswitch' ] and (PATCH_IBSWITCH in _call['TargetType'] or PATCH_SWITCH in _call['TargetType']))):
                    self.mPatchLogError("*** IBSwitch/Non-IBSwitch target patching cannot run at the same time in a shared IB fabric environment, unable to process this request.")
                    return _requests

                '''
                 Case 2 : Just increment the request count, if given target type is ibswitch.
                '''
                if _f.mGetDoSwitch().lower() == 'yes' and (PATCH_IBSWITCH in _call['TargetType'] or PATCH_SWITCH in _call['TargetType']):
                    _requests += 1
                    self.mPatchLogInfo(f"Expected number of requests in case of a Switch operation : {_requests}")
                    return _requests

                '''
                 Case 3 : When the target type is something other than IBSwitch, increment the _requests counter by 1.
                '''
                for _target in  _call['TargetType']:
                    if _target in [PATCH_CELL, PATCH_DOM0, PATCH_DOMU]:
                        _requests+=1
                        self.mPatchLogInfo(
                            f"Expected number of requests in case of a Non-IBSwitch operation : {_requests}")
                        break

        return _requests

    def mDispatchCall(self, aFabric, aCluster, aNonIBSwitch):
        """
        Sends a patch request to exacloud.
        """

        _default_error_json = {'status': 'Done',
                               'uuid': '00000000-0000-0000-0000-000000000000',
                               'error': '-1',
                               'error_str': 'Unable to send request.',
                               'non_ibswitch': aNonIBSwitch,
                               'cluster_id': None,
                               'fabric_ptr': None}

        # Get Options
        _options = aCluster.mGetOptions()
        # The patch information (files, version, etc...) are in this dictionary.
        # We will put in the jsonconf option
        _call = copy.deepcopy(aCluster.mGetCall())
        # We must add the cluster_id so we can keep track of the cluster and ibfabric lock
        _call['ClusterID'] = str(aCluster.mGetIBClusterID())
        # If this cluster wants to do a non_ibswitch patching but in the list of targets ibswitch is included,
        # then we must take it out.
        if aNonIBSwitch:
            _found = False
            for _index, _ttype in enumerate(_call['TargetType']):
                if _ttype in [ PATCH_IBSWITCH, PATCH_SWITCH ]:
                    _found = True
                    break
            if _found:
                _call['TargetType'].pop(_index)

        else:
            # If doing an ibswitch operation, then no other operation should pass in here.
            for _index, _ttype in enumerate(_call['TargetType']):
                if _ttype in PATCH_IBSWITCH or _ttype in PATCH_SWITCH:
                    _call['TargetType'] = [PATCH_IBSWITCH]
                else:
                    _call['TargetType'] = [PATCH_ROCESWITCH]

        if len(_call['TargetType']) == 0:
            return None

        _options.configpath = _call['XmlOeda']
        _options.jsonconf = _call
        _options.clusterctrl = _call['Operation']

        if InfrapatchExecutionValidator.isSwitchFabricLockingMechanismEnabled():
            self.__acquire_lock = True

        self.__cluster_key = str(aCluster.mGetClusterName())
        self.mPatchLogInfo(f"Cluster Key = {self.__cluster_key}")


        # Set string for exasplice patching.
        _patch_type = None
        if self.__dispatcher_exasplice == 'yes':
            _patch_type = PATCH_TYPE_MONTHLY
        elif self.__dispatcher_exasplice == 'no':
            _patch_type = PATCH_TYPE_QUARTERLY

        _db = ebGetDefaultDB()
        # Mark to update for not to acquire lock for domu ptaching in case of
        # dom0 exasplice patch is progressing and vice-versa.
        if (any(_x in [PATCH_DOMU, PATCH_DOM0, PATCH_CELL] for _x in _call['TargetType'])) and InfrapatchExecutionValidator.isSwitchFabricLockingMechanismEnabled():
            _rows = _db.mCheckClusterPatchOperationsTable(aClusterName=self.__cluster_key)
            self.mPatchLogInfo(f"Currently running patch operation records: {str(_rows)}")
            if len(_rows) == 1:
                # Check whether we required to acquire the lock or not.
                self.__acquire_lock = self.mLockToBeAcquired(self.__cluster_key, self.__dispatcher_target[0],
                                                             self.__dispatcher_operation, _patch_type, aClusterPatchOperationDbRows = _rows)
            # Currently, we allow a maximum of two patch operations to run simultaneously
            elif len(_rows) >= 1:
                self.mPatchLogError(f"Can not run multiple patch operations on cluster {self.__cluster_key}")
                _default_error_json['cluster_id'] = _call['ClusterID']
                _default_error_json['fabric_ptr'] = aFabric
                _default_error_json['error_str'] = 'Can not run multiple patch operations on same cluster'
                return _default_error_json
        else:
            # Reset all stale entries in the ibfabriclocks table.
            aFabric.mResetSwitchFabricdata()

        if self.__acquire_lock:
            self.mPatchLogInfo("Trying to acquire the lock.")
            # Acquire lock. We need to acquire the lock even beofre launching the request.
            if not aFabric.mLock(_call['ClusterID'], aNonIBSwitch):
                self.mPatchLogWarn("Unable to acquire lock. The request will be ignored")
                _default_error_json['cluster_id'] = _call['ClusterID']
                _default_error_json['fabric_ptr'] = aFabric
                return _default_error_json

        # Update with currently running operation
        self.mPatchLogInfo("Adding patch operation to cluster operation table:")
        self.mPatchLogInfo(f" --> Cluster Key = {self.__cluster_key}")
        self.mPatchLogInfo(f" --> Master Req UUID = {self.mGetRequestObj().mGetUUID()}")
        self.mPatchLogInfo(f" --> Target Type = {self.__dispatcher_target[0]}")
        self.mPatchLogInfo(f" --> Patch Type = {_patch_type}")
        self.mPatchLogInfo(f" --> Task Type = {self.__dispatcher_task_type}")
        self.mPatchLogInfo(f" --> Operation Style = {self.__dispatcher_style}")
        _db.mSetClusterPatchOperationsEntry (self.__cluster_key, self.mGetRequestObj().mGetUUID(), self.__dispatcher_target[0],
                                             _patch_type, self.__dispatcher_task_type, self.__dispatcher_style)

        # Create client that will send the request
        _client = ebExaClient()
        # Send request
        _client.mIssueRequest(aOptions=_options)
        # Get JSON response to track the uuid for that request
        _json_response = _client.mGetJsonResponse()

        if 'error' not in _json_response:
            _json_response['error'] = 'Undef'
            _json_response['error_str'] = 'Undef'
            self.mLinkRequestDirectory(_json_response['uuid'])
        else:
            if _json_response['error'] != 'Undef' or _json_response['error'] == '':
                if _json_response['error'] == '' :
                    self.mPatchLogWarn('Error detected in request. Releasing cluster lock') 
                else:
                    self.mPatchLogWarn(f"Error {_json_response['error']} detected in request. Releasing cluster lock")

                if not aNonIBSwitch:
                    aFabric.mSetDoSwitch('no')
                    aFabric.mUpdateDoSwitchDB()

                if self.__acquire_lock:
                    aFabric.mRelease(_call['ClusterID'])
                else:
                    self.mPatchLogWarn('mDispatchCall: Not releasing the lock since this patch request did not acquire the lock')

                # Drop patching operation entry if failed to acquire the lock.
                self.mPatchLogInfo(
                    f"mDispatchCall: Deleting patch operation entry for {self.__dispatcher_target[0]} on {self.__cluster_key}")
                _db.mDeleteClusterPatchOperationsEntry(self.__cluster_key, self.__dispatcher_target[0])

        _db.mInsertChildRequestToPatchList(self.mGetRequestObj().mGetUUID(),
                                           _json_response['uuid'],
                                           'Undef')

        return {'status': _json_response['status'],
                'uuid': _json_response['uuid'],
                'error': _json_response['error'],
                'error_str': _json_response['error_str'],
                'non_ibswitch': aNonIBSwitch,
                'cluster_id': _call['ClusterID'],
                'fabric_ptr': aFabric}

    def mLockToBeAcquired(self, aClusterName, aIncomingTargetType, aIncomingTask, aIncomingPatchType, aClusterPatchOperationDbRows = None):
        '''
        This function validated whether it requires lock to be acquired or not.
        Return values:
            True  : Required
            False : Not required.
            aClusterPatchOperationDbRows contains the row from this table
            mysql> desc clusterpatchoperations;
            +-----------------+--------------+------+-----+---------+----------------+
            | Field           | Type         | Null | Key | Default | Extra          |
            +-----------------+--------------+------+-----+---------+----------------+
            | id              | int          | NO   | PRI | NULL    | auto_increment |
            | clustername     | varchar(760) | YES  | MUL | NULL    |                |
            | master_req_uuid | varchar(255) | YES  | UNI | NULL    |                |
            | target_type     | varchar(100) | YES  |     | NULL    |                |
            | patch_type      | varchar(100) | YES  |     | NULL    |                |
            | operation_type  | varchar(100) | YES  |     | NULL    |                |
            | operation_style | varchar(100) | YES  |     | NULL    |                |
            +-----------------+--------------+------+-----+---------+----------------+

        '''
        if PARALLEL_OPERATIONS_ALLOWED_MATRIX and len(PARALLEL_OPERATIONS_ALLOWED_MATRIX) > 0:
            for row in range(len(PARALLEL_OPERATIONS_ALLOWED_MATRIX)):
                _running_target = PARALLEL_OPERATIONS_ALLOWED_MATRIX[row][0]
                _ongoing_operation = PARALLEL_OPERATIONS_ALLOWED_MATRIX[row][1]
                _ongoing_patch_type = PARALLEL_OPERATIONS_ALLOWED_MATRIX[row][2]
                _incoming_target = PARALLEL_OPERATIONS_ALLOWED_MATRIX[row][3]
                _incoming_operation = PARALLEL_OPERATIONS_ALLOWED_MATRIX[row][4]
                _incoming_patch_type = PARALLEL_OPERATIONS_ALLOWED_MATRIX[row][5]
                for _dbrow in aClusterPatchOperationDbRows:
                    _target_in_db = _dbrow[3]
                    _patch_type_in_db = _dbrow[4]
                    _operation_in_db = _dbrow[5]
                    if _running_target == _target_in_db and _ongoing_patch_type == _patch_type_in_db and _ongoing_operation == _operation_in_db \
                        and aIncomingTargetType == _incoming_target and aIncomingPatchType == _incoming_patch_type and aIncomingTask == _incoming_operation:
                        self.mPatchLogWarn(
                            f"Not required to acquire lock for incoming target {aIncomingTargetType} and incoming operation {aIncomingTask} and incoming patchtype {aIncomingPatchType} while ongoing operation {_operation_in_db} of patchtype {_patch_type_in_db} is going on target {_target_in_db} ")
                        return False

        return True

    def mUpdatePendingCalls(self):
        """
        Updates all the exacloud requests information by reading the db requests table.
        """

        _done = []
        _master_patch_list = {}
        _updated_patch_list = {}
        _db = ebGetDefaultDB()
        _master_uuid = self.mGetRequestObj().mGetUUID()

        # See if the request was done through the agent
        # if _master_req and _master_req.__class__.__name__ != '_SimpleJob':
        #    _master_patch_list = {}
        # Refresh master request data
        # _master_req.mLoadRequestFromDB(_master_req.mGetUUID())
        # Get patch_list from the master request
        # _patch_col = _master_req.mGetPatchList()
        # if _patch_col and _patch_col.startswith('Undef') is False:
        #    try:
        #        _master_patch_list = literal_eval(_patch_col.strip())
        #    except:
        #        _master_patch_list = {}

        # Get patch list
        _rows = _db.mGetChildRequestsList(_master_uuid)
        if _rows:
            for _row in _rows:
                _master_patch_list[_row[0]] = _row[1]

        # Update individual requests
        for _index, _request in enumerate(self.__pending_requests):

            if not _request:
                _done.append(_index)
                continue

            _row = _db.mGetRequest(_request['uuid'])
            if _row:
                self.__pending_requests[_index]['status'] = _row[1]
                self.__pending_requests[_index]['error'] = _row[6]
                self.__pending_requests[_index]['error_str'] = _row[7]

            # If request finished, then we must delete it from pending list
            if self.__pending_requests[_index]['status'].startswith('Done'):
                _done.append(_index)
                # Check there is no lock stuck in there
                _non_ib_switch = self.__pending_requests[_index]['non_ibswitch']
                _cluid = self.__pending_requests[_index]['cluster_id']
                _fabric = self.__pending_requests[_index]['fabric_ptr']
                _fabric.mRefreshData()
                _list = _fabric.mGetBusyClustersList().strip().split()
                for _id in _list:
                    if int(_id.strip()) == int(_cluid):
                        self.mPatchLogWarn('Lock stuck in db. Cleaning lock.')
                        if not _non_ib_switch:
                            _fabric.mSetDoSwitch('no')
                            _fabric.mUpdateDoSwitchDB()

                        if self.__acquire_lock:
                            _fabric.mRelease(_cluid)
                        else:
                            self.mPatchLogWarn('mUpdatePendingCalls: Not releasing the lock since this patch request did not acquire the lock.')

                        # Drop patching operation entry when releasing the lock.
                        self.mPatchLogInfo(
                            f"mUpdatePendingCalls: Deleting patch operation entry for {self.__dispatcher_target[0]} on {self.__cluster_key}")
                        _db.mDeleteClusterPatchOperationsEntry(self.__cluster_key, self.__dispatcher_target[0])

            # Update request information in the patch list
            _uuid = self.__pending_requests[_index]['uuid']
            _status = self.__pending_requests[_index]['status']
            if self.__pending_requests[_index]['error'] != 'Undef' and \
                    self.__pending_requests[_index]['error'] != '0':
                if self.__pending_requests[_index]['error'].strip() == '701-614':
                    _status = 'No_action_required'
                    self.mPatchLogInfo('No action required')
                else:
                    _status = 'Failed'
            if _uuid in _master_patch_list and _master_patch_list[_uuid] != _status:
                _updated_patch_list[_uuid] = _status
        # Update patch list in the db
        for _key in _updated_patch_list.keys():
            _db.mUpdateChildRequestStatus(_master_uuid, _key, _updated_patch_list[_key])

        # Delete request from pending list and add it to done requests list
        for _index in reversed(_done):
            self.__done_requests.append(self.__pending_requests.pop(_index))

        # Update progress bar
        self.mUpdateStatusFromRequests()
        return (len(self.__done_requests) + len(self.__pending_requests))

    def mGetFabricIDsFromPendingRequests(self):
        """
        Returns the IDs from the fabrics that have pending requests
        """

        return [int(_req['fabric_ptr'].mGetIBFabricID()) for _req in self.__pending_requests]

    def mDumpCallInformation(self):
        """
        Prints all the exacloud requests information
        """
        _error_code = None
        _error_desc = None
        def mGetError(aChildUUID):
            _db = None
            _json_report = {}
            _error = ""
            _error_str = ""
            _json_patch_report_data = {}
            _db = ebGetDefaultDB()
            # Retrieve the json_report from patch list table
            _row = _db.mGetPatchChildRequest(aChildUUID)
            if _row and _row[1]:
                try:
                    #_json_report_str = str(_row[1])
                    #self.mPatchLogInfo('json_report %s' % json.dumps(_json_report_str))

                    _json_report = json.loads(_row[1])
                except Exception as e:
                    self.mPatchLogInfo('JSON patch report is not yet generated from patchmgr notification xml.')
            else:
                self.mPatchLogError("Error in fetching json report from Patch List Details from DB")

            try:
                if _json_report:
                    _json_patch_report_data = _json_report["data"]
                    if _json_patch_report_data:
                        _error = _json_patch_report_data["error_code"]
                        _error_str = _json_patch_report_data["error_message"]
            except KeyError as k:
                self.mPatchLogInfo(
                    f'KeyError: Not an error - _json_patch_report_data error code is not populated in DumpCallInformation: KeyError = {str(k)}')
            except Exception as e:
                self.mPatchLogInfo(f'In DumpCallInformation Exception for fetching json report. Error = {str(e)}')

            return _error, _error_str

        for _req in self.__done_requests:
            self.mPatchLogInfo("***** Patch Requests - Done*****")
            _error_code , _error_desc = mGetError(_req['uuid'])
            self.mPatchLogInfo(
                f'child_patch_uuid: {_req["uuid"]:<40}  status:{_req["status"]:<10} ret_code:{_error_code:<10} error_str:{_error_desc}')

            self.mPatchLogInfo(
                f"mDumpCallInformation: Final call to delete of patch operation entry if in case exist for {self.__dispatcher_target[0]} on {self.__cluster_key} and for master req id = {self.mGetRequestObj().mGetUUID()}")

            _db = ebGetDefaultDB()
            _db.mDeleteClusterPatchOperationsEntryByUuid(self.mGetRequestObj().mGetUUID())

            _status_succ = False
            if _error_code == PATCH_SUCCESS_EXIT_CODE:
                _status_succ  = True

            if (_req['uuid'] != "00000000-0000-0000-0000-000000000000" or (_req['error_str'] != "Unable to send request" and _req['error'] != '503')):
                # Incident logs collection as per ENH 30006991
                # for easier analysis and debugging.
                self.__cluctrl.mGetCommandHandler().mHandlerGenIncidentFile('patching', _req['uuid'], _status_succ)

        for _req in self.__pending_requests:
            self.mPatchLogInfo("***** Patch Requests - Pending *****")
            self.mPatchLogInfo(
                f'child_patch_uuid: {_req["uuid"]:<40}  status:{_req["status"]:<10} ret_code:{_req["error"]:<10} error_str:{_req["error_str"]}')

    def mCalculatePatchOperationTimeout(self, aPayloadOptions):
        """
        Calculate patch operation timeout
        """ 

        _patch_operation_timeout_in_sec = 0

        # Exacloud patch operation timeout should be a little higher than exadata patchmgr completion.
        # Hence, we are adding additional 1 hour.

        _exacloud_additional_patch_operation_timeout_in_seconds = 3600
        _patch_operation_timeout_in_sec = int(mGetInfraPatchingConfigParam('exacloud_patch_operation_timeout_in_seconds'))
        _patch_operation_timeout_in_sec += _exacloud_additional_patch_operation_timeout_in_seconds

        if PATCH_CELL in self.__dispatcher_target and self.__dispatcher_style in [OP_STYLE_ROLLING, OP_STYLE_AUTO] and self.__dispatcher_operation in [TASK_PATCH, TASK_ROLLBACK]:
            _storageNodeList = {}
            _jconf = aPayloadOptions.jsonconf
            if _jconf and 'StorageNodeList' in _jconf.keys():
                _storageNodeList = _jconf['StorageNodeList']

            _patchable_cells_count = len(_storageNodeList)
            if  _patchable_cells_count > 5 and _patchable_cells_count < 10 :
                _patch_operation_timeout_in_sec = (int(mGetInfraPatchingConfigParam('exacloud_patch_operation_timeout_in_seconds')) * int(mGetInfraPatchingConfigParam('exacloud_patchmgr_6_to_9_cell_nodes_timeout_multiplier')))
                _patch_operation_timeout_in_sec += _exacloud_additional_patch_operation_timeout_in_seconds
            elif _patchable_cells_count >= 10:
                _patch_operation_timeout_in_sec = (int(mGetInfraPatchingConfigParam('exacloud_patch_operation_timeout_in_seconds')) * int(mGetInfraPatchingConfigParam('exacloud_patchmgr_10_or_more_cell_nodes_timeout_multiplier')))
                _patch_operation_timeout_in_sec += _exacloud_additional_patch_operation_timeout_in_seconds

            self.mPatchLogInfo(
                f"The number of patchable cells is: {_patchable_cells_count:d}, and the exacloud final patch operation timeout is: {str(_patch_operation_timeout_in_sec)} seconds")
        else:
            self.mPatchLogInfo(
                f"The exacloud final patch operation timeout is: {str(_patch_operation_timeout_in_sec)} seconds")

        return _patch_operation_timeout_in_sec

    def mMonitorPatchRequest(self, aPayloadOptions = None):
        """
        Monitor the exacloud patch requests. I takes care of orchestration:
        1.- It sends all the non_ibswitch requests.
        2.- It sends ibswitch requests only when non_ibswitch requests are running in the fabric
        3.- It waits until all the requests are done.
        """

        _db = ebGetDefaultDB()

        self.mPatchLogInfo(
            f"\n*** Starting Patch Request Monitor. Expected_requests = {self.__expected_requests:d} ***")

        # Start by sending the non_ibswitch requests
        # for _fabric in self.__ibFabrics:
        #    _clusterObjs = _fabric.mGetCluObjects()
        #    for _clu in _clusterObjs:
        #        _res = self.mDispatchCall(_fabric, _clu, True)
        #        if _res:
        #            self.__pending_requests.append(_res)

        _elapsed_time = 0
        _sent_requests = 0
        _patch_operation_timeout_in_sec = self.mCalculatePatchOperationTimeout(aPayloadOptions)

        try:

            while True:

                if _sent_requests < self.__expected_requests:

                    # Get fabric ids from pending requests
                    _pending_fabric_ids = self.mGetFabricIDsFromPendingRequests()

                    # Iterate in all fabrics
                    for _fabric in self.__ibFabrics:
                        # Refresh object data (read db info)
                        _fabric.mRefreshData()

                        # If pending requests in fabric ignore
                        if int(_fabric.mGetIBFabricID()) in _pending_fabric_ids:
                            continue

                        # If clusters are locked, then go to next fabric
                        if int(_fabric.mGetFabricLock()) != 0:
                            continue

                        # If fabric must do an ibswitch task and no cluster is locked, we can run the task
                        if str(_fabric.mGetDoSwitch()).lower() == 'yes':
                            # Get first cluster that has 'ibswitch' included in TargetType
                            _clusterObjs = _fabric.mGetCluObjects()
                            for _clu in _clusterObjs:
                                if PATCH_IBSWITCH in _clu.mGetCall()['TargetType'] or PATCH_SWITCH in _clu.mGetCall()['TargetType']:
                                    _retry = 3
                                    # We must be careful here. It is possible patch locks are already released but
                                    # registry table is not cleaned yet. In this case the exacloud call will be sent
                                    # but it will fail.
                                    while _retry > 0:
                                        if _db.mCheckRegEntry(_clu.mGetClusterName()):
                                            self.mPatchLogInfo(
                                                f"Cluster with key '{_clu.mGetClusterName()}' is busy. Retry in 10 secs")
                                            _retry -= 1
                                        else:
                                            break
                                        sleep(self.RETRY_TIME)

                                    # Dispatch ibswitch requests
                                    _res = self.mDispatchCall(_fabric, _clu, False)
                                    if _res:
                                        self.__pending_requests.append(_res)
                                    break

                _sent_requests = self.mUpdatePendingCalls()

                #Helpful debug info printed once at the beginning only for all pending requests
                if _elapsed_time == 0:
                    for _req in self.__pending_requests:
                        self.__child_request_uuid = _req['uuid']
                        self.mPatchLogInfo(
                            f'In Progress Patching Request Info ---> master_patch_uuid: {self.mGetRequestObj().mGetUUID()}  child_patch_uuid: {self.__child_request_uuid} ')
                        self.mPatchLogInfo(f'Dispatcher Log: {self.mGetRequestObj().mGetUUID() + "_patch.patchclu_apply.log"} ')

                if (_elapsed_time % (self.SLEEP_TIME * 5)) == 0:
                    self.mPatchLogInfo(
                        f"\t\tmonitor_status: ---> Done=[{len(self.__done_requests):d}], Pending=[{len(self.__pending_requests):d}], Expected[{self.__expected_requests:d}]")

                # If all requests are done, then finish monitor
                if len(self.__done_requests) == self.__expected_requests:
                    self.mDumpCallInformation()
                    break

                # Sleep monitor
                sleep(self.SLEEP_TIME)
                _elapsed_time += self.SLEEP_TIME

                if _elapsed_time >= _patch_operation_timeout_in_sec:
                    self.mPatchLogError("Patch request monitor timed out. Admin should check for individual requests status:")
                    _suggestion_msg = "Patch request monitor timed out. Admin should check for individual requests status."
                    _rc = PATCH_REQUEST_TIMEOUT
                    self.mAddDispatcherError(_rc, _suggestion_msg)
                    self.mDumpCallInformation()
                    return _rc

        except Exception as e:
            self.mPatchLogTrace(traceback.format_exc())
            raise e

        # Get return code based on the sent requests
        _stat = None
        _req_uuid = self.mGetRequestObj().mGetUUID()
        _patch_rows = _db.mGetChildRequestsList(_req_uuid)

        _rc = PATCH_SUCCESS_EXIT_CODE
        if _patch_rows:

            for _row in _patch_rows:

                _error_str = None
                _error_code = None
                _error_message = None
                _child_req_uuid = None
                try:
                    if _row[2]:
                        _json_patch_report = json.loads(_row[2])
                        if _json_patch_report and _json_patch_report["data"]:
                            _error_code = _json_patch_report["data"]["error_code"]
                            _error_message = _json_patch_report["data"]["error_message"]
                            _child_req_uuid = _row[0]
                        else:
                            self.mPatchLogInfo("Json Report Data field is empty in Dispatcher")
                    else:
                        self.mPatchLogInfo("PatchList Json Report is empty")
                except Exception as e:
                    self.mPatchLogWarn(f'Exception: {str(e)}')
                    self.mPatchLogTrace(traceback.format_exc())
                    _json_patch_report = {}
                    

                if _error_code and _error_code != PATCH_SUCCESS_EXIT_CODE:
                    self.mPatchLogInfo(f"Returning Error Code : {_error_code} from dispatcher.")
                    #Update child request uuid data in requests table with error_code and error_str
                    if _child_req_uuid:
                        self.mPatchLogInfo(
                            f"Updating error code {_error_code} for _child_req_uuid uuid {_child_req_uuid} ")
                        _db.mUpdateChildRequestError(_child_req_uuid, _error_code, _error_message)
                    return _error_code

                if _row[1] == 'Failed' or _row[1] == 'Pending':
                    _err_row = () 
                    if _row[1] == 'Failed':
                        _err_row = _db.mGetChildRequestError(self.__child_request_uuid)

                    if _err_row and _err_row[0] and isInfrapatchErrorCode(_err_row[0]) and _err_row[1]:
                      _rc = _err_row[0]
                      _suggestion_msg = _err_row[1]
                    else:
                      _suggestion_msg = "Dispatcher - One or more individual patch requests failed."
                      _rc = INFRA_PATCHING_ONE_OR_MORE_PATCH_REQUEST_EXCEPTION
                    self.mAddDispatcherError(_rc, _suggestion_msg)
                    return _rc
                if _row[1] == 'No_action_required' and _stat is None:
                    _stat = _row[1]
                if _row[1] == 'Done':
                    _stat = _row[1]

        for _req in self.__done_requests:
            if _req['uuid'] == '00000000-0000-0000-0000-000000000000':
                _suggestion_msg = "Dispatcher - Patch operation did not start"
                _rc = PATCH_OPERATION_DID_NOT_START
                self.mAddDispatcherError(_rc, _suggestion_msg)
                return _rc

        if _stat and _stat == 'No_action_required':
            _suggestion_msg = "Dispatcher - No Action Required."
            _rc = PATCH_SUCCESS_EXIT_CODE
            self.mAddDispatcherError(_rc, _suggestion_msg)
            return _rc

        return _rc

    def mStartPatchRequestExecution(self, aOptions):
        """
        Initial master patch function:
        1.- Acquire master patch lock
        2.- Parses JSON file
        3.- Populates tables
        4.- Releases master patch lock
        5.- Starts monitor
        """

        _rc = PATCH_SUCCESS_EXIT_CODE
        _concurrent = False

        if 'hostname' in aOptions:
            self.__hostname = aOptions.hostname

            self.__node = exaBoxNode(get_gcontext(), aLocal=True)
            self.__node.mConnect(aHost=aOptions.hostname)

        # Better variables are currently required for error codes handling
        # at various places in the code.
        _jconf = aOptions.jsonconf
        if _jconf and 'Params' in _jconf.keys():
            for _entry in _jconf['Params']:
                self.__dispatcher_operation = _entry['Operation']
                self.__dispatcher_target_version = _entry['TargetVersion']
                self.__dispatcher_style = _entry['OperationStyle']
                self.__dispatcher_target = _entry['TargetType']
                self.__dispatcher_task_type = _entry['Operation']
                self.__dispatcher_RequestId = _entry['RequestId'].lower()

                if _entry['AdditionalOptions'] and 'exasplice' in _entry['AdditionalOptions'][0]:
                    self.__dispatcher_exasplice = _entry['AdditionalOptions'][0]['exasplice'].lower()
                else:
                    self.__dispatcher_exasplice = None

                for _cluster in _entry['Clusters']:
                    if 'xml_oeda' in _cluster:
                        _xml_oeda_data = b64decode(_cluster['xml_oeda']).decode('utf8')
                        self.__dispatcher_cluster_name = self.mReadClusterNameFromOedaXml(_xml_oeda_data)

        try:

            self.mPatchLogInfo("Step 1 of 5: Creating log directory")
            # Create log directory
            self.__logDir = self.mCreateLogDirectory()

            # Parse JSON input file
            self.mPatchLogInfo("Step 2 of 5: Parse JSON file")
            self.mUpdateStatusFromList(True, self.STEP_PARSE_JSON)
            _rc, _sug_msg = self.mParsePatchJson(aOptions)
            if _rc != PATCH_SUCCESS_EXIT_CODE:
                self.mAddDispatcherError(_rc, _sug_msg)
                return _rc
            self.mPatchLogInfo("Parsed JSON file")

            # Space usage check on exacloud mount point to ensure thread and
            # request logs are stored and patching completes without any issues.
            if not self.mCheckExacloudMnt():
                self.mPatchLogError("Insufficient disk space to store exacloud requests and thread logs.")
                _suggestion_msg = "Insufficient disk space to store exacloud requests and thread logs."
                _rc = INSUFFICIENT_SPACE_AT_EXACLOUD_THREAD_LOCATION
                self.mAddDispatcherError(_rc, _suggestion_msg)
                return _rc
            else:
                self.mPatchLogInfo("Sufficient free disk space found for exacloud threads and request logs.")

            # Check if we should skip filesystem validation for DOM0 exasplice LATEST
            _skip_filesystem_validation = False
            if self.__dispatcher_target_version and self.__dispatcher_target_version.upper() == 'LATEST' and \
               len(self.__dispatcher_target) == 1 and self.__dispatcher_target[0].lower() == PATCH_DOM0 and \
               self.__dispatcher_exasplice and self.__dispatcher_exasplice == 'yes':
                _skip_filesystem_validation = True
                self.mPatchLogInfo("Skipping filesystem validation for DOM0 exasplice LATEST - will be resolved by handlers")

            if not _skip_filesystem_validation and self.__latest_verion_source_loc == self.LATEST_VER_FROM_FILESYSTEM:
                self.mPatchLogInfo("Using file system to read patch files.")
                _rc = self.mCheckPatchFileExistInFileSystem()
                if _rc != PATCH_SUCCESS_EXIT_CODE:
                    return _rc

            # Populate IBFabric Table
            self.mPatchLogInfo("Step 3 of 5: Populate IBFabric Table")
            self.mUpdateStatusFromList(True, self.STEP_POPULATE_TABLES)

            self.mPatchLogInfo("Acquiring master patch lock to populate IBFabric Table...")
            if self.mLockPatchCmd() is False:
                self.mPatchLogError("*** Another patch-cluster request is in process."
                           " Try later.")
                _concurrent = True
                _suggestion_msg = "System is busy. Please retry the operation after some time."
                _rc = INFRA_PATCHING_SYSTEM_BUSY_LOCK_NOT_ACQUIRED
                self.mAddDispatcherError(_rc, _suggestion_msg)
                return _rc
            self.mPatchLogInfo("Acquired master patch lock. Populating IBFabric Table")

            _rc = self.mPopulatePatchTables(aOptions)
            if _rc != PATCH_SUCCESS_EXIT_CODE:
                return _rc

            self.mPatchLogInfo("Populated IBFabric Table")

            # Get total number of expected requests
            self.__expected_requests = self.mGetCountOfRequests()
            if self.__expected_requests == 0:
                _suggestion_msg = "Parallel patching on an IBSwitch and a non-IBSwitch target not allowed."
                _rc = PARALLEL_PATCHING_IB_NON_IB_TARGET_NOT_ALLOWED
                self.mAddDispatcherError(_rc, _suggestion_msg)
                return _rc 

            self.mPatchLogInfo(f"Total number of expected requests = {self.__expected_requests:d}")

            # Start by sending the non_ibswitch requests
            self.mPatchLogInfo("Start sending non_ibswitch requests")
            _cluCount = 0
            for _fabric in self.__ibFabrics:
                _clusterObjs = _fabric.mGetCluObjects()
                for _clu in _clusterObjs:
                    _res = self.mDispatchCall(_fabric, _clu, True)
                    if _res:
                        self.__pending_requests.append(_res)
                    _cluCount += 1
            if _cluCount < 1:
                '''
                 In case of stale entries found on the exacloud DB
                 or there is a mismatch in entries on the exacloud DB 
                 and cluster XML. All entries in the tables will be 
                 cleaned up and we will do a second retry to have the 
                 operation go though without failure.
                
                 There is no harm in cleaning up entries during an 
                 ongoing patch operation and are cleaned up as part of
                 the below method. At the start of patch execution, if 
                 the switch fabric entries are missing, they are created
                 back, but it is once validated at this point and created
                 if they are still missing.
                '''
                _db = ebGetDefaultDB()
                _db.mCleanupSwitchFabricTables()
                for _fabric in self.__ibFabrics:
                    _clusterObjs = _fabric.mGetCluObjects()
                    for _clu in _clusterObjs:
                        _res = self.mDispatchCall(_fabric, _clu, True)
                        if _res:
                            self.__pending_requests.append(_res)
                        _cluCount += 1
            if _cluCount < 1 :
                _suggestion_msg = "Patching child request to Exacloud is not created due to the absence of cluster details introduced by some fabric changes"
                self.mPatchLogError(f"{_suggestion_msg}")
                _rc = EXACLOUD_CHILD_REQUEST_CREATION_FAILED                    
                self.mAddDispatcherError(_rc, _suggestion_msg)
                return _rc
            self.mPatchLogInfo("Done sending non_ibswitch requests")

        except ExacloudRuntimeError as ecre:
            self.mPatchLogError("mStartPatchRequestExecution: ExacloudRuntimeError detected. " +
                                f"Error Code, Error Type, Error Message: {ecre.mGetErrorCode()}, {ecre.mGetErrorType()}, {ecre.mGetErrorMsg()}")
            self.mPatchLogTrace(traceback.format_exc())
            _suggestion_msg = f"mStartPatchRequestExecution: ExacloudRuntimeError detected. Error Code, Error Type, Error Message: {ecre.mGetErrorCode()}, {ecre.mGetErrorType()}, {ecre.mGetErrorMsg()}"
            _rc = MASTER_PATCH_REQUEST_ERROR
            self.mAddDispatcherError(_rc, _suggestion_msg)
        except Exception as e:
            self.mPatchLogError(f"mStartPatchRequestExecution error: {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _suggestion_msg = f"mStartPatchRequestExecution error: {str(e)}"
            _rc = MASTER_PATCH_REQUEST_EXCEPTION
            self.mAddDispatcherError(_rc, _suggestion_msg)

        finally:
            # Release patch-cluster cmd lock
            if not _concurrent:
                self.mReleasePatchCmd()
                self.mPatchLogInfo("Step 4 of 5: Released master patch lock")

        # Check if patch execution already failed
        if _rc == MASTER_PATCH_REQUEST_EXCEPTION:
            self.mPatchLogError("Patch Execution already failed. "
                       "Not running Patch Monitor")
            return _rc

        try:
            # Start Monitor. It will dispatch every single call
            self.mPatchLogInfo("Step 5 of 5: Start Monitoring requests")
            self.mUpdateStatusFromList(True, self.STEP_MONITOR)
            _rc = self.mMonitorPatchRequest(aOptions)
        except Exception as e:
            self.mPatchLogError(f"mStartPatchRequestExecution Monitor Error: {str(e)}")
            self.mPatchLogTrace(traceback.format_exc())
            _suggestion_msg = f"mStartPatchRequestExecution Monitor Error: {str(e)}"
            _rc = MONITOR_EXCEPTION
            self.mAddDispatcherError(_rc, _suggestion_msg)

        return _rc

    def mCreateLogDirectory(self):
        """
        Creates a log directory for the master request. This will have symlinks to
        individual worker log directories for all the patch workers.
        Example: exacloud/log/patch/<master_request_UUID>
        """

        try:
            _req = self.mGetRequestObj()
            if _req:
                _dir = self.LOG_DIRECTORY + _req.mGetUUID()
                self.__node.mExecuteCmd(f'mkdir -p {_dir}')
                return _dir
            else:
                raise Exception
        except:
            self.mPatchLogWarn("No log directory will be created.")
            self.mPatchLogTrace(traceback.format_exc())

        return None

    '''
    def mCreatePatchZipFilesDirs(self, aInternalDirectory):
        """
        Creates a directory for the master request to save
        the patch zip files.
        """

        _dir = ""

        try:

            if aInternalDirectory:
                _dir = self.PATCH_PAYLOADS_DIRECTORY + aInternalDirectory
                self.__node.mExecuteCmd(f'mkdir -p {_dir}')
                self.mPatchLogInfo(f"Directory '{_dir}' successfully created")

        except:
            self.mPatchLogWarn(f"Directory '{_dir}' not created.")
            self.mPatchLogTrace(traceback.format_exc())

        return None
    '''

    def mLinkRequestDirectory(self, aRequestUUID):
        """
        Creates a symbolic link from the master request log directory to
        a certain individual request log directory.
        Example:
            exacloud/log/patch/<master_request_UUID>/<worker_request_UUID> ->
            ../../../oeda/requests/<worker_request_UUID>/log
        """

        _oeda_path = ''
        try:
            for _dir in self.__logDir.split('/'):
                if _dir:
                    _oeda_path += '../'
            _oeda_path += 'oeda/requests/' + aRequestUUID + '/log'
            self.__node.mExecuteCmd(f'cd {self.__logDir}; ln -s {_oeda_path} {aRequestUUID}')

        except:
            self.mPatchLogWarn("No symlink created to request log directory.")
            self.mPatchLogTrace(traceback.format_exc())

    def mGetLatestPatchVersion(self):
        """
        Get the latest patch version by looking at the file system.
        """

        _valid_versions_fs = []
        _latest_ver_from_fs = None

        # instantiate the class oracle version
        _verobj = OracleVersion()

        # List the available patches from the file system PatchPayloads
        # -------------------------------------------------------------
        if os.path.isdir(self.PATCH_PAYLOADS_DIRECTORY) is True:
            _ldir = os.listdir(self.PATCH_PAYLOADS_DIRECTORY)
            # Go through the file system to get the latest patch version
            for _entry in _ldir:
                _patch_dir_path = ''
                _patch_dir_path = self.PATCH_PAYLOADS_DIRECTORY + _entry
                # validate the patch version is dir or not
                if os.path.isdir(_patch_dir_path) is True:
                    # Expect version in form a.b.c.d.e.f[.g] where f is 6 digits
                    # and g is an optional. Example: 12.2.1.1.1.170620,
                    # 18.1.4.0.0.180125.3, 18.1.10.0.0.181031.1.
                    _re_out = re.match('^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\.[0-9]{6,6}(|\.[0-9]+)$', _entry)
                    if _re_out:
                        _valid_versions_fs.append(_entry)
                    else:
                        self.mPatchLogWarn(f"Invalid version found in file system: {_entry} ")

            self.mPatchLogInfo("Following versions are found in file system:")
            for _ver in _valid_versions_fs:
                self.mPatchLogInfo(f"{_ver}")

        # get the latest/highest version from file system
        _latest_ver_from_fs = _verobj.mGetHighestVer(_valid_versions_fs)
        self.mPatchLogInfo(f"Latest version from file system: {_latest_ver_from_fs}")
        return _latest_ver_from_fs

    def mReadClusterNameFromOedaXml(self, _xml_oeda_data):
        """
        Read cluster/customer name from oeda xml. Return cluster name
        """

        # Read cluster/customer name from oeda xml
        _root = ET.fromstring(_xml_oeda_data)
        if re.search("xmlns=", _xml_oeda_data):
            # xmlns found in xml, use name space tag to read
            # customer name
            self.mPatchLogInfo("Found xml name space in oeda xml file")
            _cluster_name = _root.find("{model}customerName").text
        else:
            # no xmlns found in xml, normal read of customer name
            self.mPatchLogInfo("Not found xml name space in oeda xml file")
            _cluster_name = _root.find("customerName").text

        return _cluster_name

    def mAddDispatcherError(self, aError, aSuggestion=None, aComment=None):
        """
        Generate the patch error report.
        """

        self.__json_status = {}
        _suggestion_msg = aSuggestion
        if aSuggestion and len(aSuggestion) > ERROR_MSG_TRUNCATE_LENGTH:
            _suggestion_msg = mTruncateErrorMessageDescription(aSuggestion)
        
        _code, _msg, _description, _error_action = ebPatchFormatBuildErrorWithErrorAction(aError, _suggestion_msg, aComment)

        self.__json_status["data"] = self.mAddPatchreport()
        self.__json_status["data"]["error_code"] = _code
        self.__json_status["data"]["error_message"] = _msg
        self.__json_status["data"]["error_detail"] = _description
        if _error_action:
            self.__json_status["data"]["error_action"] = _error_action
        else:
            self.mPatchLogInfo(f"Error action is empty for Error Code {_code}")

        #Keep track of the exacloud master uuid as part of ecra status call 
        if self.mGetRequestObj():
            self.__json_status["data"]["master_request_uuid"] = self.mGetRequestObj().mGetUUID()
        if self.__child_request_uuid:
            self.__json_status["data"]["child_request_uuid"] = self.__child_request_uuid
        #Do not remove . Helpful for debugging purposes
        self.mPatchLogTrace(f"Dispatcher Error json details are as follows {json.dumps(self.__json_status)} :\n")

    def mGetPatchJsonStatus(self):
        return self.__json_status

    def mSetPatchJsonStatus(self,aJsonStatus):
        self.__json_status = aJsonStatus

    def mAddPatchreport(self):
        """
        Return patch report with more detail. We try to maintain the same
        format of patching CNS payload so that it can be read uniformly
        in ecra side.
        """

        # fill up the payload json for notificaiton
        _patch_report_json = {}
        _patch_report_json['httpRequestId'] = self.__dispatcher_RequestId

        _patch_report_json['recipients'] = []
        _channel_info = {}
        _channel_info['channelType'] = "topics"
        _patch_report_json['recipients'].append(_channel_info)

        _patch_report_json['notificationType'] = {}
        _patch_report_json['notificationType']['componentId'] = "Patch_Exadata_Infra_SM"
        _patch_report_json['notificationType']['id'] = "Patch_Exadata_Infra_SMnotification_v1"

        _patch_report_json['service'] = "EXADATA Patch"
        _patch_report_json['component'] = "Patch Exadata Infrastructure"
        _patch_report_json['subject'] = "Patch Exadata Infrastructure Service Update"
        # _patch_report_json['event_post_time'] = time.strftime("%Y-%m-%d:%H.%M.%S %Z")
        _patch_report_json['event_post_time'] = datetime.now().strftime("%Y-%m-%d:%H.%M.%S %Z")

        # Exacloud log thread location
        _patch_report_json['log_dir'] = self.__logDir

        # Fetch cluster name
        _patch_report_json['cluster_name'] = self.__dispatcher_cluster_name

        # This is required for mandatory CNS check in CNSOperation.java
        _patch_report_json['exadata_rack'] = self.__dispatcher_cluster_name

        # target type, such as cell, dom0, etc
        _patch_report_json['target_type'] = self.__dispatcher_target

        # task type such as, prereq, patch, rollback, etc
        _patch_report_json['operation_type'] = self.__dispatcher_task_type

        # operation style, rolling and / or non-rolling.
        _patch_report_json['operation_style'] = self.__dispatcher_style

        # These are required in ecra Patcher.java for updating the image version
        # and cabinet status
        _patch_report_json['target_version'] = self.__dispatcher_target_version

        _patch_report_json['topic'] = ''

        return _patch_report_json

#########################################################################################################################
