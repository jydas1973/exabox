"""
$Header:

 Copyright (c) 2015, 2025, Oracle and/or its affiliates.

NAME:
    Worker - Worker process handling Agent client request

FUNCTION:
    Worker Core functionalities

NOTE:
    None

History:
   MODIFIED (MM/DD/YY)
   ririgoye  11/26/25 - Bug 38636333 - EXACLOUD PYTHON:ADD INSTANTCLIENT TO
                        LD_LIBRARY_PATH
   ririgoye  11/20/25 - Bug 38667586 - EXACS: MAIN: PYTHON3.11: SUPRASS ALL
                        PYTHON WARNINGS
   aypaul    10/22/25 - Bug#38503013 Resolve worker shutdown issue due to
                        listener not starting up.
   rajsag    09/17/25 - enh 38389132 - exacloud: autoencryption support for
                        exascale configuration
   aypaul    05/15/25 - Bug#37948804 Address worker consistency performance
                        issues.
   naps      04/15/25 - Bug 37680025 - Cleanup request table when worker has a
                        stale uuid.
   araghave  03/17/25 - Enh 37713042 - CONSUME ERROR HANDLING DETAILS FROM
                        INFRAPATCHERROR.PY DURING EXACOMPUTE PATCHING
   jesandov  06/21/24 - Bug 36759526: Add support of secondary exacloud
   jyotdas   11/26/24 - ENH 37267666 - Register separate operations for patch
                        precheck and rollback for single threaded operations
   jfsaldan  10/30/24 - Bug 37202899 - EXACS:24.4.1:VMBACKUP TO OSS : DOWNLOAD
                        GOLD BACKUP RETURN COMPLETED/SUCCESS POST GOLD BACKUP
                        FAILED TO OSS
   pverma    10/23/24 - Support for infra_vm_states commmand
   jyotdas   10/01/24 - ER 37089701 - ECRA Exacloud integration to enhance
                        infrapatching operation to run on a single thread
   avimonda  09/26/24 - Bug 36943471: DBAAS.EXACSOSPATCH : :FAILED TO COMPLETE
                        GUEST VM OS UPDATE PRECHECK. ONE ORE MORE INDIVIDUAL
                        PATCH REQUESTS FAILED
   jesandov  09/02/24 - 36883563: Add Hostname and Exacloud path to startup logs
   akkar     08/22/24 - Bug 36731374: Remove .trc file from mysql
   joysjose  08/13/24 - Bug 36601769 Archive OEDA request directory as soon as
                        the request finishes
   naps      08/06/24 - Bug 36629391 - During exacloud stop, handle dispatcher
                        and workermanager as special workers
   araghave  07/15/24 - Enh 36830077 - CLEANUP KSPLICE CODE FROM INFRAPATCHING
                        FILES
   naps      06/19/24 - Bug 36727077 - Check open fd limits for worker process.
   rajsag    06/13/24 - 36603931 - EXACLOUD : EXASCALE DB VAULT CREATION
                        SUPPORT36534554 - EXACLOUD : EXACLOUD CHANGES TO
                        SUPPORT EXASCALE VAULT LCM OPERATIONS
   araghave  06/12/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK LOGS
                        AND CLEAN-UP
   aypaul    04/29/24 - Issue#36532482 Add support to terminate worker when
                        threads pile up in process context.
   prsshukl  04/18/24 - Bug 36527975 - IMPLEMENT FEATURE TO MOCK INFRAPATCH
                        FROM EXACLOUD
   aararora  04/18/24 - Bug 36524930: Add None check for vmhandle
   akkar     03/08/24 - Bug 36250866: Set error in requests table
   araghave  02/28/24 - Enh 36295801 - IMPLEMENT ONEOFFV2 PLUGIN EXACLOUD
                        CHANGES
   aararora  01/10/24 - Bug 35863722: Remove cluster folder after operation is
                        completed to save space.
   aypaul    01/08/24 - Bug#36150269 Worker validation update.Bug#36150269
                        Worker validation update.
   naps      01/05/24 - Bug 36157324 - partial revert of 35896839.
   aypaul    01/04/24 - Forward porting changes of bug 36087830 to ECS MAIN.
   aypaul    12/21/23 - Bug#36120429 Add exception handling during response
                        write.
   naps      11/23/23 - Bug 35896839 - Improve the logic for port availability and cleanup port during shutdown.
   jesandov  09/28/23 - 35141262: Profiler enhancement to use DB tables
   ririgoye  08/23/23 - Bug 35616435 - Fix redundant/multiple instances of
                        mConnect
   naps      08/03/23 - Bug 35013360 - optimize worker count logic.
   ririgoye  07/10/23 - Enh 35580256 - Added exceptions for some invalid
                        format/values in some operations' payloads
   scoral    06/20/23 - Enh 35454589 - Add a API for EDV volumes prechecks.
   jyotdas   06/13/23 - BUG 35488103 - Domu os patch fails with page_oncall
                        error instead of fail_and_show for dispatcher errors
   gparada   06/22/23 - 35213979 Override workers
   aararora  05/22/23 - Bug 35391543: Set default log level for components not
                        using default logger
   naps      04/05/23 - Bug 35259960 - Reuse existing db object.
   ndesanto  03/02/23 - Bug 35072620 - Fix for port already in use.
   naps      02/24/23 - Bug 35104776 - Handle 0 microsecond case while
                        populating worker lastactivetime.
   naps      02/07/23 - 34931403 - Increase default worker threads for
                        production mode.
   aypaul    01/12/23 - Enh#34971851 SOP scripts execution support.
   aypaul    12/04/22 - Issue#34607716 Handle multiprocessing issue by shutting
                        down base manager instance explicitly.
   aararora  10/10/22 - Initialize with default_log_level if not passed in
                        options
   aypaul    09/05/22 - Enh#34411005 API implementation for active network
                        information.
   aararora  08/16/22 - Add step during incident file creation.
   naps      08/05/22 - Bug 34312132 - Check vmcmd name before generating log
                        file names.
   jyotdas   07/27/22 - ENH 34350151 - Exacompute Infrapatching
   aypaul    07/05/22 - Bug#34347508 Worker allocation optimisation logic
                        correction.
   naps      04/06/22 - Bug 33952513 - include vm cmd in log file names.
   alsepulv  02/16/22 - Enh 33691491: Create json_dispatch exacloud endpoint
   aypaul    01/25/22 - Enh#33611377 Worker limit and resource
                              utilisation optimisation.
   araghave  11/23/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES FROM
                        ERROR.PY TO INFRAPATCHERROR.PY
   naps      07/24/21 - move diagnostic messages to trace file.
   jyotdas   06/28/21 - Bug 33050209 - Dom0 monthly patch fails with
                        error-unsupported operand type for str and int
   araghave  06/09/21 - BUG 32959024 - INFRA PATCH TO RETURN APPROPRIATE ERROR
                        CODES DURING PARALLEL OPERATIONS
   joserran  04/27/21 - Bug 32394314 - Propagate options to agent
   naps      04/12/21 - Handle absence of .err and .trc files.
   naps      03/31/21 - have cluster specific logs.
   jyotdas   03/22/21 - Enh 32415195 - error handling: return infra patching
                        dispatcher errors to caller
   alsepulv  03/05/21 - Bug 32592473: replace get_stack_trace() with
                        traceback.format_exc()
   joserran  02/22/21 - Bug 32498502: Including loglevel in formatter
   naps      01/11/21 - Enhance error handling.
   jlombera  12/18/20 - Bug 32283440: handle exceptions occurred during
                        collection of diag info
   araghave  12/07/20 - Enh 31604386 - RETURN ERROR CODES TO DBCP TO CELLS
                        AND SWITCHES
   jejegonz  11/11/20 - 32047521 - Use ebLogAddDestinationToLoggers from LogMgr.
   araghave  10/21/20 - Enh 31925002 - Error code handling implementation
                        for Monthly Patching
   nmallego  08/28/20 - ER 31817570 - Update refactor infra patching call
   ajayasin  07/13/20 - fortify issue fixing 31525324
   jfsaldan  06/25/20 - Enh 31311814: Add time and date stamp to exacloud cluctrl log files
   devbabu   05/04/20 - exacloud returning wrong error code for all
                        ExacloudRuntimeError "
   dekuckre  03/09/20 - 30817349: Add capability to block operations
   ndesanto  10/02/19 - 30374491 - EXACC PYTHON 3 MIGRATION BATCH 01
   gurkasin  06/05/19 - Enh 29472639: Changed exacloud log file name
   oespinos  07/09/18 - Bug 28299175: return original dbException instead of raising new one
   seha      03/06/18 - Bug 27642280: remove a diagnostic worker handler
   seha      01/25/18 - Enh 27427661: move agent logs of diagnostic
                        module in threads/ to diagnostic/
   dekuckre  08/09/17 - Bug 26003275: Set log level in ExaCloud
   nmallego  07/17/17 - bug26387175 - In mShowStatus(), mark success for
                        the error codes '701-614 and 703-614', since it's
                        not handle today
   sdeekshi  08/25/17 - Bug 26571290: restructure mock code to use existing
                        dispatcher framework
   mirivier  06/15/15 - Create file
"""

from six.moves.urllib.parse import urlparse
from socket import error as socket_error
from time import strftime
from ast import literal_eval
import errno
import subprocess
import socket
import threading
import os
import re
import sys
import signal
import traceback
import time
import base64
import json
from six.moves import _thread
import uuid
from six.moves import urllib
import logging
import datetime
import psutil
import shutil
import glob
import shlex

from exabox.core.Context import get_gcontext
from exabox.config.Config import ebCluCmdCheckOptions
from exabox.log.LogMgr import (ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogTrace,
                                ebThreadLocalLog, ebLogVerbose, ebSetLogLvl,
                                ebLogInit, ebLogFinalize, ebLogCrit,
                                ebLogAddDestinationToLoggers, ebLogDeleteLoggerDestination,
                                ebGetDefaultLoggerName, ebGetDefaultLogLevel, ebFormattersEnum)
from exabox.core.Node import exaBoxNode
from exabox.ovm.vmcontrol import ebVgLifeCycle
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.ovm.bmc import ebBMCControl
from exabox.jsondispatch.jsondispatch import ebJsonDispatcher
from exabox.core.DBStore import ebGetDefaultDB
from exabox.core.Core import ebExit
from exabox.core.Error import build_error_string, gSubError, gBMCErrorCodeLookUp
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.core.Core import exaBoxCoreInit, exaBoxCoreShutdown
from exabox.core.DBStore import ebInitDBLayer, ebShutdownDBLayer, ebGetDefaultDB
import exabox.agent.Agent
from exabox.agent.AgentSignal import AgentSignal, AgentSignalEnum
from exabox.agent.AuthenticationStorage import ebGetHTTPAuthStorage
from exabox.agent.Client import ebExaClient
from exabox.agent.WClient import ebWorkerCmd
from exabox.agent.Mock import MockDispatcher, MockStatus
from exabox.infrapatching.core.cludispatcher import ebCluPatchDispatcher
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.cludiag import exaBoxDiagCtrl, ebDownloadLog
from exabox.agent.ebJobRequest import ebJobRequest, nsOpt
from exabox.proxy.Client import ebHttpClient
from exabox.proxy.ebJobResponse import ebJobResponse
from exabox.proxy.router import Router
from exabox.proxy.ebProxyJobRequest import ebProxyJobRequest
from exabox.tools.ebXmlGen.ebFacadeXmlGen import ebFacadeXmlGen
from exabox.infrapatching.core.infrapatcherror import PATCH_SUCCESS_EXIT_CODE, INCORRECT_INPUT_JSON, ebPatchFormatBuildError
from exabox.network.ExaHTTPSServer import ExaHTTPSServer, ExaHTTPRequestHandler
from exabox.exakms.ExaKmsEndpoint import ExaKmsEndpoint
from exabox.exakms.ExaKmsSingleton import ExaKmsSingleton
from exabox.ovm.clunetworkdetect import getActiveNetworkInformation
from exabox.sop.soputils import process_sop_request
import exabox.exadbxs.edv as edv
from exabox.utils.node import connect_to_host, kill_proc_tree
from exabox.utils.common import exception_handler_decorator
import subprocess as sp
import zlib

gWorkerPort = 0
gDaemonHandle = None
DEFAULT_MAX_RETRIES = 3
SOCKET_CONNECT_TIMEOUT = 15
FD_LIMIT_THRESHOLD = 80 #80%
FD_LIMIT_MAXLIMIT = 16384 #16k

# WorkerStatus = [ Idle, Running, Exited, Zombie ]
#

ebStandaloneWorkerSet = ('supervisor','dispatcher','workermanager','scheduler','heartbeat')

class SecondaryExacloudClient:

    def __init__(self, aExacloudHost="localhost", aExacloudPath=""):

        self.__exacloudHost = socket.getfqdn(aExacloudHost)
        self.__exacloudPort = None
        self.__exacloudPath = ""

        if aExacloudHost == "localhost":
            self.__exacloudPath = aExacloudPath
        else:
            _exacloudPath = os.path.abspath(__file__)
            _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]
            self.__exacloudPath = _exacloudPath

        self.__exaboxConf = ""

    def mGetExacloudPort(self):
        return self.__exacloudPort

    def mSetExacloudPort(self, aValue):
        self.__exacloudPort = aValue

    def mGetExacloudHost(self):
        return self.__exacloudHost

    def mSetExacloudHost(self, aValue):
        self.__exacloudHost = aValue

    def mGetExacloudPath(self):
        return self.__exacloudPath

    def mSetExacloudPath(self, aStr):
        self.__exacloudPath = aStr

    def mGetExaboxConf(self):
        return self.__exaboxConf

    def mSetExaboxConf(self, aStr):
        self.__exaboxConf = aStr

    def mExecuteLocal(self, aCmd, aCurrDir=None, aStdIn=sp.PIPE, aStdOut=sp.PIPE, aStdErr=sp.PIPE, aDebug=False):

        _args = aCmd
        if isinstance(aCmd, str):
            _args = shlex.split(aCmd)

        # Add timeot hook of 10m
        _current_dir = aCurrDir
        _stdin = aStdIn
        _stdout = aStdOut
        _stderr = aStdErr

        if aDebug:
            ebLogInfo(aCmd)
            ebLogInfo(_args)

        _proc = sp.Popen(_args, stdin=_stdin, stdout=_stdout, stderr=_stderr, cwd=_current_dir)
        _stdoutP, _stderrP = _proc.communicate()
        _rc = _proc.returncode

        if _stdoutP:
            _stdoutP = _stdoutP.decode("UTF-8").strip()
        else:
            _stdoutP = ""

        if _stderrP:
            _stderrP = _stderrP.decode("UTF-8").strip()
        else:
            _stderrP = ""

        if aDebug:
            ebLogInfo(_rc)
            ebLogInfo(_stderrP)
            ebLogInfo(_stdoutP)

        return _rc, _stdoutP, _stderrP


    def mReadConfig(self):

        _exaboxConfPath = os.path.join(self.mGetExacloudPath(), "config", "exabox.conf")

        with open(_exaboxConfPath, "r") as _remoteConfF:
            self.mSetExaboxConf(json.loads(_remoteConfF.read()))


    def mMakeJsonDispatchRequest(self, aEndpoint, aPayloadPath, aExaunitId="", aWorkflowId=""):

        if not self.mGetExacloudPort():
            self.mSetExacloudPort(self.mGetExaboxConf()["agent_port"])

        _agentPort = self.mGetExacloudPort()
        _agentAuth = self.mGetExaboxConf()["agent_auth"]
        _agentUser = base64.b64decode(_agentAuth[0]).decode("utf-8")
        _agentPass = base64.b64decode(_agentAuth[1]).decode("utf-8")

        _exa = self.mGetExacloudPath()

        # Create Cmd
        _cmd = f"{_exa}/bin/exacloud -jd {aEndpoint} -jc {aPayloadPath}"

        if aExaunitId:
            _cmd = f"{_cmd} -ei {aExaunitId}"

        if aWorkflowId:
            _cmd = f"{_cmd} -wi {aWorkflowId}"

        _cmd = f"{_cmd} -al {self.mGetExacloudHost()} -ap {_agentPort}"

        _rc, _stdout, _err = self.mExecuteLocal(_cmd, aDebug=True)

        # Call request
        try:
            _id = re.search("for request: (.*)", _stdout).group(1)
        except:
            _exc = traceback.format_exc()
            ebLogError(f"Something went wrong while calling exacloud.")
            ebLogError(f"Please check latest exacloud log that belong to the request: {_cmd}")
            ebLogError(_exc)
            raise

        # Do status tracking
        _cmd = f"/bin/curl"
        if self.mGetExaboxConf()["https_enabled"] == "True":
            _cmd = f"{_exa}/bin/curl_exa"

        _cmd = f"{_cmd} -u {_agentUser}:{_agentPass}"

        if self.mGetExaboxConf()["https_enabled"] == "True":
            _cmd = f"{_cmd} https://{self.mGetExacloudHost()}:{_agentPort}/Status/{_id}"
        else:
            _cmd = f"{_cmd} http://{self.mGetExacloudHost()}:{_agentPort}/Status/{_id}"

        _rc, _stdout, _ = self.mExecuteLocal(_cmd)

        _status_resp = json.loads(_stdout)
        return _status_resp


    def mMakeCluctrlRequest(self, aEndpoint, aXmlPath, aPayloadPath, aStepName="", aUndo=False, aExaunitId="", aWorkflowId=""):

        if not self.mGetExacloudPort():
            self.mSetExacloudPort(self.mGetExaboxConf()["agent_port"])

        _agentPort = self.mGetExacloudPort()
        _agentAuth = self.mGetExaboxConf()["agent_auth"]
        _agentUser = base64.b64decode(_agentAuth[0]).decode("utf-8")
        _agentPass = base64.b64decode(_agentAuth[1]).decode("utf-8")

        _exa = self.mGetExacloudPath()

        # Create Cmd
        _cmd = f"{_exa}/bin/exacloud -clu {aEndpoint} -cf {aXmlPath} -jc {aPayloadPath}"

        if aStepName and str(aStepName).strip() != "":
            _cmd = f"{_cmd} -rs {aStepName} -sl {aStepName}"

        if str(aUndo).upper() == "TRUE":
            _cmd = f"{_cmd} -un True"
        else:
            _cmd = f"{_cmd} -un False"

        if aExaunitId:
            _cmd = f"{_cmd} -ei {aExaunitId}"

        if aWorkflowId:
            _cmd = f"{_cmd} -wi {aWorkflowId}"

        _cmd = f"{_cmd} -al {self.mGetExacloudHost()} -ap {_agentPort}"

        _rc, _stdout, _err = self.mExecuteLocal(_cmd, aDebug=True)

        # Call request
        try:
            _id = re.search("for request: (.*)", _stdout).group(1)
        except:
            _exc = traceback.format_exc()
            ebLogError(f"Something went wrong while calling exacloud.")
            ebLogError(f"Please check latest exacloud log that belong to the request: {_cmd}")
            ebLogError(_exc)
            raise

        # Do status tracking
        _cmd = f"/bin/curl"
        if self.mGetExaboxConf()["https_enabled"] == "True":
            _cmd = f"{_exa}/bin/curl_exa"

        _cmd = f"{_cmd} -u {_agentUser}:{_agentPass}"

        if self.mGetExaboxConf()["https_enabled"] == "True":
            _cmd = f"{_cmd} https://{self.mGetExacloudHost()}:{_agentPort}/Status/{_id}"
        else:
            _cmd = f"{_cmd} http://{self.mGetExacloudHost()}:{_agentPort}/Status/{_id}"

        _rc, _stdout, _ = self.mExecuteLocal(_cmd)

        _status_resp = json.loads(_stdout)
        return _status_resp


class ebWorker(object):

    def __init__(self, aParams=None, aDB=None):
        self.__uuid    = '00000000-0000-0000-0000-000000000000'
        self.__status  = 'Idle'
        self.__statusinfo = {"status": "000:: No status info available"}
        self.__starttime = time.strftime("%c")
        self.__endtime = 'Undef'
        self.__params  = aParams
        self.__error   = 'Undef'
        self.__error_str = 'Undef'

        if not aDB:
            self.__db  = ebGetDefaultDB()
        else:
            self.__db  = aDB

        self.__port    = 0
        self.__pid     = os.getpid()
        self.__type    = 'worker'
        self.__sync_lock = 'Undef'
        #Using this timesepc will ensure miscroseconds is always set, even for 0 microseconds !
        self.__last_active_time = datetime.datetime.now().isoformat(sep=' ', timespec='microseconds')
        self.__state = 'NORMAL' #Values can be NORMAL/CORRUPTED
        if get_gcontext().mGetArgsOptions().proxy:
            self.__type    = 'proxy'

    def mSetState(self, aValue="NORMAL"):
        self.__state = aValue

    def mGetState(self):
        return self.__state

    def mSetSyncLock(self, aValue="Undef"):
        self.__sync_lock = aValue

    def mSetLastActiveTime(self, aValue=None):
        if aValue is None:
            #Using this timesepc will ensure miscroseconds is always set, even for 0 microseconds !
            aValue = datetime.datetime.now().isoformat(sep=' ', timespec='microseconds')
        self.__last_active_time = aValue

    def mGetSyncLock(self):
        return self.__sync_lock

    def mGetLastActiveTime(self):
        return self.__last_active_time

    #Returns True if lock was successfully accquired
    def mAcquireSyncLock(self, acquiringProcess=None):
        if acquiringProcess == None:
            return False

        if self.__db.mAcquireWorkerSyncLock(self.__port, acquiringProcess):
            self.__sync_lock = acquiringProcess
            return True
        return False

    #Returns True if lock was successfully released
    def mReleaseSyncLock(self, releaseProcess=None):
        if releaseProcess == None:
            return False

        if self.__db.mReleaseWorkerSyncLock(self.__port, releaseProcess):
            self.__sync_lock = 'Undef'
            return True
        return False

    def mGetPort(self):
        return self.__port

    def mSetPort(self,aPort):
        self.__port = aPort

    def mGetPid(self):
        return self.__pid

    def mSetPid(self,aPid):
        self.__pid = aPid

    def mGetStatus(self):
        return self.__status

    def mGetStatusInfo(self):
        return self.__statusinfo

    def mSetStatus(self, aStatus):
        self.__status = aStatus

    def mSetStatusInfo(self, aStastusInfo):
        self.__statusinfo = aStastusInfo

    def mResetUUID(self):
        self.__uuid    = '00000000-0000-0000-0000-000000000000'

    def mGetUUID(self):
        return self.__uuid

    def mSetUUID(self,aUUID):
        self.__uuid = aUUID

    def mGetTimeStampStart(self):
        return self.__starttime

    def mSetTimeStampStart(self,aTime):
        self.__starttime = aTime

    def mGetTimeStampEnd(self):
        return self.__endtime

    def mSetTimeStampEnd(self,aTime=None):
        if aTime:
            self.__endtime = aTime
        else:
            self.__endtime = time.strftime("%c")

    def mGetParams(self):
        return self.__params

    def mSetParams(self,aParams):
        self.__params = aParams

    def mGetError(self):
        return self.__error

    def mSetError(self, aError):
        self.__error = aError

    def mGetErrorStr(self):
        return self.__error_str

    def mSetErrorStr(self, aErrorStr):
        self.__error_str = aErrorStr

    def mGetType(self):
        return self.__type

    def mSetType(self, aType):
        self.__type = aType

    def mRegister(self):
        assert(self.__port)
        if self.__db.mGetWorker(self.__port):
            self.mUpdateDB()
        else:
            self.__db.mInsertNewWorker(self)

    def mDeregister(self):
        self.mSetSyncLock()
        self.mSetLastActiveTime()
        self.mSetTimeStampEnd()
        self.mSetStatus('Exited')
        self.mGetStatusInfo()["status"] = "Worker thread exited normally"
        self.mSetError('0')
        self.mSetErrorStr('No Errors')
        self.mSetPid(0)
        self.mSetState()
        self.mUpdateDB()
        if self.mGetUUID() != '00000000-0000-0000-0000-000000000000':
            ebLogError('*** Worker Exited with request UUID (%s) not NULL' % (self.mGetUUID()))
            _reqobj = exabox.agent.Agent.ebGetRequestObj(self.mGetUUID())
            _cur_status = _reqobj.mGetStatus()
            if _cur_status == 'Pending':
                #Set error state for this stale/dangling entry.
                ebLogInfo('*** Cleaning up the uuid in request table')
                _reqobj.mSetStatus('Done')
                _reqobj.mSetError('709')
                _reqobj.mSetErrorStr(f'Request with uuid {self.mGetUUID()} was terminated')
                self.__db.mUpdateRequest(_reqobj)
                self.__db.mDelRegByUUID(self.mGetUUID())

    def mDelete(self):
        self.__db.mDelWorkerEntry(self)

    def mUpdateDB(self):
        self.__db.mUpdateWorker(self)

    def mLoadWorkerUsingPID(self, aPID):
        _worker = self.__db.mGetWorkerByPid(aPID)
        if _worker:
            self.mPopulate(_worker)
            return True
        else:
            return False

    def mLoadWorkerFromDB(self,aPort):
        _worker = self.__db.mGetWorker(aPort)
        if _worker:
            self.mPopulate(_worker)
            return True
        else:
            return False

    def mPopulate(self, aWorker):

        _worker = aWorker
        self.mSetUUID(_worker[0])
        self.mSetStatus(_worker[1])
        self.mSetTimeStampStart(_worker[2])
        self.mSetTimeStampEnd(_worker[3])
        self.mSetParams(_worker[4])
        self.mSetError(_worker[5])
        self.mSetErrorStr(_worker[6])
        try:
            self.mSetStatusInfo(json.loads(_worker[7]))
        except ValueError:
            _tmpjson = {"status": _worker[7]}
            self.mSetStatusInfo(_tmpjson)
        self.mSetPid(_worker[8])
        self.mSetPort(_worker[9])
        self.mSetType(_worker[10])
        self.mSetSyncLock(_worker[11])
        try:
            self.mSetLastActiveTime(datetime.datetime.strptime(_worker[12], '%Y-%m-%d %H:%M:%S.%f'))
        except ValueError as e:
            #This is just a fallback safety mechanism
            #Ideally we will be not be getting in here.. Since we dont populate db back with this value.
            #We always populate db only with value from datetime.datetime.now value ( With isoformat set with timespec='microseconds' which will always have microseconds ) !
            ebLogWarn(f'mPopulate: error while parsing worker thread lastactivetime : {str(e)}')
            if '.' not in _worker[12]:
                ebLogInfo(f'mPopulate: microsecond field not populated !')
                self.mSetLastActiveTime(datetime.datetime.strptime(_worker[12], '%Y-%m-%d %H:%M:%S'))
            else:
                raise ValueError(f'Raising exception: {str(e)}')

        self.mSetState(_worker[13])

    def mSetLogLevel(self, log_level, isDefault=False):

        if not log_level in ['VERBOSE', 'DEBUG', 'INFO', 'ERROR', 'WARNING', 'CRITICAL', 'DIAGNOSTIC']:
            ebLogError("Invalid log level %s" % log_level)
            return

        _logger = logging.getLogger(ebGetDefaultLoggerName())
        ebSetLogLvl(_logger, log_level)

        _logger = logging.getLogger('agent')
        ebSetLogLvl(_logger, log_level)

        _logger = logging.getLogger('database')
        ebSetLogLvl(_logger, log_level)

        # For 'healthcheck' logger, if log_level is not passed in the payload,
        # the default log_level needs to be VERBOSE and not DIAGNOSTIC.
        _logger = logging.getLogger('healthcheck')
        if not isDefault:
            ebSetLogLvl(_logger, log_level)
        else:
            ebSetLogLvl(_logger, 'VERBOSE')

        try:
            # Default log levels for nw_reconfig and new_bonding need to be VERBOSE
            # and are not configurable according to payload.
            _logger = logging.getLogger('nw_reconfig')
            ebSetLogLvl(_logger, 'VERBOSE')

            _logger = logging.getLogger('nw_bonding')
            ebSetLogLvl(_logger, 'VERBOSE')
        except Exception as ex:
            ebLogError('mSetLogLevel: There was an error while setting default log level'\
                       'for nw_bonding and nw_reconfig loggers. Exception:: %s - %s' % (ex.__class__, ex))

    def mIsMySQLRunning(self):
        return self.__db.mIsMySQLRunning()


#
# Worker Daemon Class
#
class ebWorkerRestHttpListener(ExaHTTPRequestHandler):

    def __init__(self, aConfig, *args, initBaseHTTPHandler=True):

        self.__context = get_gcontext()
        self.__options = self.__context.mGetArgsOptions()
        self.__config = aConfig
        self.__authkey = aConfig['auth_key']
        self.__callbacks = {
            "/status" : self.mShowStatus,
            "/wctrl" : self.mWorkerRequest
        }
        self.__shutdown = False
        if initBaseHTTPHandler:
            super().__init__(*args)

        self.__mock_mode = False
        self.__mock_mode_patch = False
        self.mRefreshMock(aConfig)

    def mRefreshMock(self, aParams):

        _coptions = get_gcontext().mGetConfigOptions()

        if 'mock_mode' in _coptions:
            if str(_coptions['mock_mode']).upper() == 'TRUE':
                self.__mock_mode = True
            else:
                self.__mock_mode = False

        if 'mock_mode' in aParams:
            if str(aParams['mock_mode']).upper() == 'TRUE':
                self.__mock_mode = True
            else:
                self.__mock_mode = False

        if 'mock_mode_patch' in _coptions:
            if str(_coptions['mock_mode_patch']).upper() == 'TRUE':
                self.__mock_mode_patch = True
            else:
                self.__mock_mode_patch = False

        if 'mock_mode_patch' in aParams:
            if str(aParams['mock_mode_patch']).upper() == 'TRUE':
                self.__mock_mode_patch = True
            else:
                self.__mock_mode_patch = False

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"ExaCloud Agent\"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_JSON(self, aJReponse):
        _response = json.dumps(aJReponse, indent=4, separators=(',',': '))
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(_response.encode('utf8'))
        self.wfile.write(b'\n\n')

    def do_HTML(self, aHResponse):

        _response = aHResponse['output']
        if 'ctype' in aHResponse.keys():
            self.send_header('Content-type', aHResponse['ctype'])
        else:
            self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(_response.encode('utf8'))
        self.wfile.write(b'\n\n')

    def mInShutdown(self):

        _response = {}
        _response['status'] = 'Done'
        _response['error']  = '503'
        _response['error_str'] = 'Rest Listener not available'
        _response['success'] = 'False'
        self.send_response(503)
        self.do_JSON(_response)
        return

    def do_GET(self):

        if self.__shutdown:
            self.mInShutdown()

        _url_parsed = urlparse(self.path)

        if self.headers.get('Authorization') == None:
            self.do_AUTHHEAD()
            self.wfile.write(b'Authentication required to access this service')
            return
        elif self.headers.get('Authorization') == 'Basic '+self.__authkey:

            _response = {}
            _func = _url_parsed[2]
            if not _func in self.__callbacks.keys():
                _response['status'] = 'Done'
                _response['error']  = '404'
                _response['error_str'] = 'Service '+_func +' not valid'
                _response['success'] = 'False'
                self.send_response(404)
                self.do_JSON(_response)
                return
            else:
                # Parse the query part of the URL (e.g. the parameters sent by the Client)
                if len(_url_parsed[4]):
                    _param = dict(elt.split('=') for elt in _url_parsed[4].replace('"','').split('?'))
                    for k in _param.keys():
                        v = _param[k]
                        # Unmunch the Value (e.g. unquote) and eval the result to get the right Value
                        # e.g. 'True','None','{}' will be stored as native type and not string in the
                        # parameter array.
                        v = urllib.parse.unquote(v)
                        _param[k] = v
                else:
                    _param = []
                self.__callbacks[_func](_param, _response)
                self.send_response(200)
                self.do_JSON(_response)
                #
                # if Daemon exited/stopped commit suicide
                #
                if not gDaemonHandle:
                    self.__shutdown = True
        else:
            self.do_AUTHHEAD()
            self.wfile.write(self.headers.get('Authorization').encode('utf8'))
            self.wfile.write(b'Authentication failed not authorized to access this service')
            return

    def mShowStatus(self, aParams, aResponse):
        # mock mode
        self.mRefreshMock(aParams)
        if self.__mock_mode:
            MockStatus(self,aParams, aResponse)
            return

        _db = ebGetDefaultDB()
        _response = aResponse
        if not aParams or not len(aParams.keys()) or not 'uuid' in aParams.keys():
            _body = _db.mDumpRequests()
            _response['body'] = _body
            _response['success'] = False
            _response['error'] = '503'
            _response['error_str'] = 'Missing parameters or UUID'
        else:
            _body = _db.mGetRequest(aParams['uuid'])
            _response['body'] = str(_body)
            if not _body:
                _response['success'] = False
                _response['error'] = '504'
                _response['error_str'] = 'Unknown UUID request'
            else:
                # Bug-26387175: For exadata image patching today the status of
                # 'No action required' (error codes 701-614 and 703-614) is
                # treated as failure and eventually PSM read it as fail. So,
                # we need to trap the error code '701-614 and 703-614' and
                # mark as success.
                if _body[6] in ['0', 'Undef', '701-614', '703-614']:
                    _response['success'] = 'True'
                else:
                    _response['success'] = 'False'
        _response['status'] = 'Done'

    def mWorkerRequest(self, aParams, aResponse):

        _response = aResponse
        _cmd = None
        #
        # Fetch Worker entry from the DB
        #
        _db = ebGetDefaultDB()
        _worker = _db.mGetWorker(gWorkerPort)
        #
        # Worker Object not found return an error
        #
        if not _worker:
            _response['success'] = 'False'
            _response['status']  = 'Unavailable'
            _response['error']   = '800'
            _response['error_str'] = 'Worker entry not found in Worker DB'
            return
        #
        # Default initialization
        #
        _response['statusinfo'] = 'Request processed successfully'
        _response['error']      = '0'
        _response['error_str']  = 'No Errors'
        _response['success']    = 'True'
        _response['uuid']       = _worker[0]
        _response['status']     = _worker[1]
        _response['start_time'] = _worker[2]
        _response['end_time']   = _worker[3]
        #
        # Retrieve request command to perform
        #
        try:
            _cmd = aParams['cmd']
        except:
            _response['success'] = 'False'
            _response['error']   = '801'
            _response['error_str'] = 'Invalid worker cmd supplied (%s)' % (str(_cmd))
            return
        #
        # cmd::Status
        #
        if _cmd == 'status':
            # status cmd returns the default
            return
        #
        # cmd::Shutdown
        #
        if _cmd == 'shutdown':
            global gDaemonHandle
            if gDaemonHandle:
                gDaemonHandle.mWorker_Shutdown()
                return
        #
        # Default reply (e.g Default initialization)
        #
        return

def handlerhook(aArgs):
    return lambda *args: ebWorkerRestHttpListener(aArgs, *args)

class ebWorkerRestListener(object):

    def __init__(self, aConfig):

        self.__config = aConfig
        _coptions = get_gcontext().mGetConfigOptions()
        # Inherit agent default host (this allow monitoring of Workers outside of localhost)
        if 'agent_local' in _coptions.keys() and _coptions['agent_local'] == 'True':
            _host = 'localhost'
        else:
            _host = '0.0.0.0'
        self.__server_addr = (_host,self.__config['worker_port'])
        self.__server_class = ExaHTTPSServer
        self.__handler_class = handlerhook(self.__config)
        try:
            self.httpd = self.__server_class(self.__server_addr, self.__handler_class)
        except Exception as e:
            ebLogError('ebRestListener: Exception:: %s - %s' % (e.__class__, e))
            ebLogError('ebRestListener: Can not start Worker Listener on port: '+str(self.__config['worker_port']))
            sys.exit(-1)

    def mStartRestListener(self):

        try:
            self.httpd.serve_forever()
        except socket_error as e:
            if e.errno == errno.EADDRINUSE:
                ebLogError('ERROR: Worker can not start listening address already in use.')
                sys.exit(-1)
        except:
            ebLogError('*** Worker RestListener caught exception')

    def mStopRestListener(self):

        ebLogInfo('*** Worker Listener stopped...')
        self.httpd.shutdown()
        #self.httpd.socket.close()

def daemonize_process():
   """Detach a process from the controlling terminal and run it in the
   background as a daemon.
   """
   try:
      pid = os.fork()
   except OSError as e:
      raise Exception("%s [%d]" % (e.strerror, e.errno))

   if (pid == 0):   # The first child.
      # To become the session leader of this new session and the process group
      # leader of the new process group, we call os.setsid().  The process is
      # also guaranteed not to have a controlling terminal.
      os.setsid()

      # import signal           # Set handlers for asynchronous events.
      # signal.signal(signal.SIGHUP, signal.SIG_IGN)

      try:
         pid = os.fork()    # Fork a second child.
      except OSError as e:
         raise Exception("%s [%d]" % (e.strerror, e.errno))

      if pid:
        os._exit(0)     # Exit parent (the first child) of the second child.
   else:
      os._exit(0)       # Exit parent of the first child.

def redirect_std_descriptors():

    _rin_file = _rout_file = _rerr_file = '/dev/null'
    sys.stdout.flush()
    sys.stderr.flush()
    _sin  = open(_rin_file,'r')
    _sout = open(_rout_file, 'a+')
    _serr = open(_rerr_file, 'a+')
    os.dup2(_sin.fileno(),  sys.stdin.fileno())
    os.dup2(_sout.fileno(), sys.stdout.fileno())
    os.dup2(_serr.fileno(), sys.stderr.fileno())

def is_port_free(aPort):
    """Check if a network port in localhost is already being used

    :param aPort: network port to check
    :returns: True if port is free or False if taken.
    """

    _port = aPort
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as _sock:
        _rc = _sock.connect_ex(('localhost', int(_port)))
        if _rc == 0:
            ebLogInfo(f"Port {aPort} is free.")
            return False

    ebLogInfo(f"Port {aPort} is in use.")
    return True

class ebWorkerDaemon(object):

    def __init__(self, aPort=0, aLiteCreate=False):

        self.__restlistener = None
        self.__port = aPort
        self.__pid  = os.getpid()
        self.__config = {}
        self.__config_opts = get_gcontext().mGetConfigOptions()
        self.__abort_worker     = False
        self.__exit_main_loop   = False
        self.__main_loop_exited = False
        self.__worker  = None
        self.__detach  = False
        self.__logfilename_no_extension    = None
        self.__worker_destination_handlers= None
        self.__args_opt = get_gcontext().mGetArgsOptions()
        self.__ecs_version = "UNKNOWN"
        self.__thread_log_path = None
        self.__thread_xml_path = None

        try:
            if os.path.exists("config/label.dat"):
                with open("config/label.dat") as _f:
                    self.__ecs_version = _f.read().strip()
        except:
            pass

        self.__signal_db_map = {
            AgentSignalEnum.RELOAD: self.mReloadConfig
        }

        if aLiteCreate:
            return

        if self.__args_opt.worker_port:
            self.__port = int(self.__args_opt.worker_port)

        global gWorkerPort
        gWorkerPort = self.__port
        #
        # Check if Worker is already started at this port
        #
        _pid = 0
        _db = ebGetDefaultDB()
        _worker = _db.mGetWorker(self.__port)
        if _worker and _worker[1] != 'Exited':
            _pid = _worker[8]
        #
        # Check if process(_pid) still alive
        #
        if _pid:
            try:
                os.kill(int(_pid),0)
                self.__abort_worker = True
            except:
                ebLogWarn('*** Worker DB inconsistency detected. Worker set as alive but process (%d) not existing' % (int(_pid)))
                _pid = 0
        if not is_port_free(self.__port):
            self.__abort_worker = True
        if self.__abort_worker:
            return
        #
        # Daemonize process if requested
        #
        if self.__args_opt.worker_detach:
            self.__detach = True
            daemonize_process()
            redirect_std_descriptors()
            self.__pid = os.getpid()
        #
        # Redirect default log to worker log file
        #
        self.mMkdirWithPoption('log/workers')
        self.__logfilename_no_extension = os.path.join('log','workers',
                                "dflt_worker_{}".format(str(self.__port)))

        self.__worker_destination_handlers = ebLogAddDestinationToLoggers([ebGetDefaultLoggerName()],
            self.__logfilename_no_extension, ebFormattersEnum.WORKER)
        #
        # Build config object for Listener
        #
        self.__config['worker_port'] = self.__port

        #
        # Fall back agent_auth if agent_authkey is not available
        #

        self.__config["auth_key"] = ebGetHTTPAuthStorage().mGetAdminCredentialForRequest()

        self.__mock_mode = False
        self.mRefreshMock(self.__config_opts)
        #
        # Set DaemonHandle (required for listener interaction)
        #
        global gDaemonHandle
        gDaemonHandle = self


    def mRefreshMock(self, aParams):

        _coptions = get_gcontext().mGetConfigOptions()

        if 'mock_mode' in _coptions:
            if str(_coptions['mock_mode']).upper() == 'TRUE':
                self.__mock_mode = True
            else:
                self.__mock_mode = False

        if 'mock_mode' in aParams:
            if str(aParams['mock_mode']).upper() == 'TRUE':
                self.__mock_mode = True
            else:
                self.__mock_mode = False

        if 'mock_mode_patch' in _coptions:
            if str(_coptions['mock_mode_patch']).upper() == 'TRUE':
                self.__mock_mode_patch = True
            else:
                self.__mock_mode_patch = False

        if 'mock_mode_patch' in aParams:
            if str(aParams['mock_mode_patch']).upper() == 'TRUE':
                self.__mock_mode_patch = True
            else:
                self.__mock_mode_patch = False

    def mGetPid(self):
        return self.__pid

    def mSetPid(self, aPid):
        self.__pid = aPid

    def mGetSignalDBMap(self):
        return self.__signal_db_map

    def mSetSignalDBMap(self, aMap):
        self.__signal_db_map = aMap

    def mMkdirWithPoption(self,path):  #mkdir -p "path"
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                _err_str = "Make directory failed Operation failed with error: {0}".format(str(exc))
                ebLogError(_err_str)
                raise ExacloudRuntimeError(0x0795, 0xA, _err_str)

    def get_worker_exit_loop(self):
        return self.__exit_main_loop

    def validate_uuid(self, uuid_str):
        return re.match(r"^[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}$", uuid_str) is not None

    def mRedirectRequestSecondaryExacloud(self, aJob, aCallback):

        # Validate secondary exacloud
        _result = None
        _secondaries = get_gcontext().mCheckConfigOption("secondary_exacloud_config")
        if _secondaries:
            for _secondary in _secondaries:

                if "payload_regex" not in _secondary:
                    ebLogWarn(f"Invalid secondary exacloud config: {_secondary}")
                    continue

                if not aJob or not aJob.mGetOptions() or not aJob.mGetOptions().jsonconf:
                    ebLogWarn("Missing jsonconf in request")
                    continue

                if "exacloud_path" not in _secondary:
                    _exacloudPath = os.path.abspath(__file__)
                    _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]
                    _secondary["exacloud_path"] = _exacloudPath

                if "exacloud_host" not in _secondary:
                    _secondary["exacloud_host"] = "localhost"

                if re.search(_secondary["payload_regex"], str(aJob.mGetOptions().jsonconf)):

                    # Found secondary
                    _client = SecondaryExacloudClient(_secondary["exacloud_host"], _secondary["exacloud_path"])

                    if "exacloud_port" in _secondary:
                        _client.mSetExacloudPort(_secondary["exacloud_port"])

                    try:
                        _client.mReadConfig()
                    except:
                        ebLogWarn(f"Invalid exabox.conf in exacloud config: {_secondary}")
                        continue

                    _result = aCallback(_client, aJob)
                    _rc = 0
                    break

        return _result

    def mWorker_Start(self):

        if self.__abort_worker:
            ebLogInfo(f'*** Worker on port ({self.__port}) is already started')
            return 1

        if not self.__restlistener:
            self.__restlistener = ebWorkerRestListener(self.__config)
            ebLogInfo(f'Worker started on port ({self.__port}) pid ({self.__pid})')
            _thread.start_new_thread(self.__restlistener.mStartRestListener,())

        # Register Worker
        self.__worker = ebWorker()
        self.__worker.mSetPort(self.__port)
        self.__worker.mRegister()

        _db = ebGetDefaultDB()

        # Double check no other monitor are running
        _worker = ebWorker(aDB=_db)
        _worker.mLoadWorkerFromDB(self.__port)
        if _worker.mGetType() == 'monitor':
            _db = ebGetDefaultDB()
            _rqlist = literal_eval(_db.mDumpWorkers())
            for _worker in _rqlist:
                if _worker[10] == 'monitor':
                    if _worker[9] == self.__port:
                        pass
                    else:
                        ebLogError('*** Monitor already running. Abort launching 2nd monitor process')
                        self.__exit_main_loop
                        break

        # MAIN_LOOP
        _timer = 600
        _err   = None

        while not self.get_worker_exit_loop():

            # Delay of 1s between DB checks
            time.sleep(1)

            # Load Worker DB Entry
            _worker = ebWorker(aDB=_db)
            _worker.mLoadWorkerFromDB(self.__port)

            # Process signals
            self.mProcessSignalsDB(_worker, aDB=_db)

            # MONITOR ACTION
            if _worker.mGetType() == 'monitor':
                try:
                    if _timer >= 600 or _worker.mGetStatus() == 'Refreshing':

                        if _worker.mGetStatus() != 'Refreshing':
                            _worker.mSetStatus('Refreshing')
                            _worker.mUpdateDB()

                        _cluster_dir = []
                        for _entry in os.listdir('clusters/'):
                            if _entry[:len('cluster-')] == 'cluster-':
                                _cluster_dir.append(_entry)
                        _cluster_dir = ['clusters/' + _cluster + '/config/' for _cluster in _cluster_dir]
                        _cluster_config = []
                        for _dir in _cluster_dir:
                            if not os.path.isdir(_dir):
                                ebLogWarn(f'*** Invalid Entry found in cluster directory: {_dir}')
                                continue
                            for _file in os.listdir(_dir):
                                if _file.endswith('.xml'):
                                    _cluster_config.append(_dir + _file)
                                    break
                        for _config_file in _cluster_config:
                            if self.__exit_main_loop:
                                break
                            _cmd_list = ['bin/exacloud', '-dc', '-cf', _config_file, '-clu', 'monitor_cluster']

                            # Add args that need to be propagated (e.g. --debug/--verbose)
                            _cmd_list.extend(get_gcontext().mGetPropagateProcOptions())

                            _child = subprocess.run(_cmd_list, stdout=subprocess.PIPE,
                                                               stderr=subprocess.PIPE)

                            if _child.returncode:
                                _stderr = _child.stderr.decode("UTF-8")
                                _stdout = _child.stdout.decode("UTF-8")
                                ebLogError(f'*** Starting Monitor command: {_cmd_list} failed '\
                                           f'stderr:{_stderr} stdout:{_stdout}')
                                raise Exception(_stderr)
                        _timer = 0
                        _worker.mSetStatus('Running')
                        _worker.mUpdateDB()
                    else:
                        _timer += 1
                except:
                    ebLogError('*** FATAL_ERROR WHILE PROCESSING MONITOR REFRESH ***')
                    ebLogError(traceback.format_exc())
                continue

            if _worker.mGetType() == 'proxy':
                if _worker.mGetUUID() == '00000000-0000-0000-0000-000000000000':
                    continue
                _worker.mSetStatus('Running')
                _worker.mUpdateDB()
                _start_time = time.asctime()
                _err     = None
                _err_str = None

                _job = ebProxyJobRequest(None,{}, _db)
                _job.mLoadRequestFromDB(_worker.mGetUUID())

                _params = _job.mGetParams()
                if 'log_level' in _job.mGetOptions():
                    _level = _job.mGetOptions().log_level
                    ebLogInfo("*** mWorker_Start: Setting log level to %s" % _level)
                    _worker.mSetLogLevel(_level)
                else:
                    _level = ebGetDefaultLogLevel()
                    ebLogInfo("*** mWorker_Start: Setting log level to default level - %s" % _level)
                    _worker.mSetLogLevel(_level, isDefault=True)

                _requestID = None
                if "request_id" in _params.keys() and _params["request_id"] is not None:
                    if not self.validate_uuid(_params["request_id"]):
                        raise ExacloudRuntimeError(0x0810, 0xA, f"Invalid value for request_id: {_params['request_id']}")
                    _requestID = str(_params["request_id"])
                elif "exaunitid" in _params.keys() and _params["exaunitid"]:
                    if not re.match(r"^[1-9][0-9]*$", str(_params["exaunitid"])):
                        raise ExacloudRuntimeError(0x0810, 0xA, f"Invalid value for exaunitid: {_params['exaunitid']}")
                    _requestID = f"exaunit_{str(_params['exaunitid']).zfill(11)}"
                else:
                    _requestID = "0000-0000-0000-0000"

                    if "wf_uuid" in _params.keys() and _params["wf_uuid"]:
                        if not self.validate_uuid(_params["wf_uuid"]):
                            raise ExacloudRuntimeError(0x0810, 0xA, "Invalid value for wf_uuid: {_params['wf_uuid']}")
                        _requestID = f"{_requestID}/{_params['wf_uuid']}"
                    else:
                        _requestID = f"{_requestID}/00000000-0000-0000-0000-000000000000"

                _reqType = _job.mGetReqType()
                _endpoint = _reqType.split('.')[0]
                _method = _reqType.split('.')[1]
                os.makedirs(os.path.join('log/threads',_requestID), exist_ok=True)
                _logfilename_no_extension = os.path.join('log/threads', _requestID ,
                                "{}_{}.{}".format(_job.mGetUUID(), _reqType, _job.mGetCmd()))
                _worker_destination_handlers = ebLogAddDestinationToLoggers(
                    [ebGetDefaultLoggerName()], _logfilename_no_extension, ebFormattersEnum.WORKER)
                self.__thread_log_path = _logfilename_no_extension
                _critical_requests = self.__config_opts['proxy_critical_requests']
                _sleep_critical_requests = int(self.__config_opts['proxy_critical_requests_time'])

                #Currently there are 3 types of response possible from exacloud.
                #1. JSONResponse. While parsing response headers search for Content-Type = application/json
                #2. FileResponse. While parsing response headers search for Content-Type = application/octet-stream
                #3. HTMLResponse. While parsing response headers search for Content-Type = text/html. This content type may vary, need to add logic accordingly.
                #from exabox.agent.AuthenticationStorage import ebGetHTTPAuthStorage
                #_authkey = ebGetHTTPAuthStorage().mGetAdminCredentialForRequest()
                _ecInstanceID = _db.mSelectECInstanceIDFromUUIDToECInstance(str(_job.mGetUUID()))
                _echost = _ecport = _ecauthkey = None

                _echost, _ecport, _ecauthkey = _db.mSelectRoutingInfoFromECInstances(_ecInstanceID)

                ebLogInfo('[Worker] EC Instance details for {3}: {0},{1},{2}.'.format(_echost, _ecport, _ecauthkey, _endpoint))
                if _endpoint == "Status":
                    _start_time = time.time()

                    while True:
                        _uuid = _job.mGetUUID()
                        _path = _job.mGetUrlFullPath()
                        _headers = literal_eval(_job.mGetUrlHeaders())
                        if _headers is None:
                            ebLogInfo("Headers are None for Status request in worker.")

                        _options = nsOpt({  'host': str(_echost),
                                        'port': str(_ecport), 'authKey': str(_ecauthkey),
                                        'path': _path, 'headers': _headers, 'data': None})

                        _httpCLient = ebHttpClient()
                        _httpCLient.mSetCmd('request_status')
                        _response = _httpCLient.mIssueRequest(aOptions=_options)

                        _status = _response.mGetStatus()
                        _err = _response.mGetError()
                        _err_str = _response.mGetErrorStr()
                        _status_code = int(_response.mGetStatusCode())
                        #_resp_body = _response.mToJson()
                        _resp_body = _httpCLient.mGetRawJSONResponse()
                        _resp_headers = _httpCLient.mGetResponseHeaders()
                        #ebLogInfo("Status: {0}. Response headers: {1}. Status code: {2}. Response body: {3}".format(_status, _resp_headers, _status_code, _resp_body))
                        if _status == 'Pending':
                            #To be configurable in exabox.conf
                            _db.mUpdateStatusForReqUUID(_uuid, 'Pending')
                            _job.mSetRespCode(_status_code)
                            _job.mSetRespBody(_resp_body)
                            #No need to setting the response headers in the ebjobrequest object. Value will be taken from DB.
                            #Moreover setting this here will result in failure of building the next status request headers as its built from the existing ebjobrequest object.
                            _db.mUpdateResponseDetailsInProxyRequest(_uuid, _status_code, _resp_body, _resp_headers)
                            _cmd_type = str(_job.mGetCmd())
                            if _cmd_type in _critical_requests:
                                 time.sleep(_sleep_critical_requests)
                            else:
                                 time.sleep(60)
                            continue
                        else:
                            _db.mUpdateStatusForReqUUID(_uuid, 'Done')
                            _job.mSetRespCode(_status_code)
                            _job.mSetRespBody(_resp_body)
                            _job.mSetUrlHeaders(_resp_headers)
                            _db.mUpdateResponseDetailsInProxyRequest(_uuid, _status_code, _resp_body, _resp_headers)
                            break
                else:
                    #Generate the exacloud request and get the response by passing reqtype.
                    #Use _err and _err_str to indicate errors.
                    #Update the uuid to ecinstance table.
                    ebLogInfo("*** Worker for other requests.")
                    _form_data = None
                    _path = _job.mGetUrlFullPath()
                    _body = literal_eval(_job.mGetReqBody())

                    _headers = literal_eval(_job.mGetUrlHeaders())
                    _options = nsOpt({  'host': str(_echost),
                                        'port': str(_ecport), 'authKey': str(_ecauthkey),
                                        'path': _path, 'headers': _headers, 'data': _body})

                    _httpCLient = ebHttpClient()
                    _httpCLient.mSetCmd(_job.mGetCmd())
                    _response = _httpCLient.mIssueRequest(aOptions=_options)

                    _uuid = _job.mGetUUID()
                    _status = _response.mGetStatus()
                    _status_code = _response.mGetStatusCode()
                    _resp_body = _httpCLient.mGetRawJSONResponse()
                    _err = _response.mGetError()
                    _err_str = _response.mGetErrorStr()
                    _timestamp = time.strftime("%c")
                    _resp_headers = _httpCLient.mGetResponseHeaders()
                    _job.mSetRespCode(_status_code)
                    _job.mSetRespBody(_resp_body)
                    _job.mSetUrlHeaders(_resp_headers)
                    _db.mUpdateResponseDetailsInProxyRequest(_uuid, _status_code, _resp_body, _resp_headers)
                    if _err is not None:
                        _db.mUpdateStatusForReqUUID(_uuid, 'Done')
                    else:
                        _db.mUpdateStatusForReqUUID(_uuid, 'InitialReqDone')

                ebLogDeleteLoggerDestination(ebGetDefaultLoggerName(), _worker_destination_handlers)
                _db.mUpdateProxyRequest(_job)

                _worker.mSetStatus('Idle')
                _worker.mResetUUID()
                _worker.mSetLastActiveTime()
                _worker.mUpdateDB()
                continue
            #
            # Check if a Job Request UUID was assigned
            #
            if _worker.mGetUUID() != '00000000-0000-0000-0000-000000000000':

                _start_time = time.asctime()
                _err_str = None
                _node    = None
                _xml     = None
                _step    = None
                #
                # Fetch request from DB
                #
                _job = ebJobRequest(None,{}, aDB=_db)
                _job.mLoadRequestFromDB(_worker.mGetUUID())

                _params = _job.mGetParams()
                if 'log_level' in _job.mGetOptions():
                    _level = _job.mGetOptions().log_level
                    ebLogInfo("*** mWorker_Start: Setting log level to %s" % _level)
                    _worker.mSetLogLevel(_level)
                else:
                    _level = ebGetDefaultLogLevel()
                    ebLogInfo("*** mWorker_Start: Setting log level to default level - %s" % _level)
                    _worker.mSetLogLevel(_level, isDefault=True)
                _job.mSetWorker(self.__port)

                #
                # Capture all Logs (Info/Warn/Debug/Error) in memory
                #
                get_gcontext().mSetRegEntry("exaunit_id", "")
                get_gcontext().mSetRegEntry("operation_id", "")
                get_gcontext().mSetRegEntry("workflow_id", "")
                get_gcontext().mSetRegEntry("undo", "")

                if _job.mGetCmd() == 'collect_log':
                    self.mMkdirWithPoption(os.getcwd() + '/log/diagnostic')
                    _logfilename_no_extension = os.getcwd() + '/log/diagnostic/'+_job.mGetUUID()+'_'+ \
                                   _job.mGetType()+'.'+_job.mGetCmd()
                    _worker_destination_handlers =  ebLogAddDestinationToLoggers([ebGetDefaultLoggerName(),'diagnostic'],
                        _logfilename_no_extension, ebFormattersEnum.WORKER)
                    _logfilename = _logfilename_no_extension + ".trc"
                else:
                    _requestID = None
                    _undo = False
                    _params = _job.mGetParams()
                    if "request_id" in _params.keys() and _params["request_id"] is not None:
                        if not self.validate_uuid(_params["request_id"]):
                            raise ExacloudRuntimeError(0x0810, 0xA, f"Invalid value for request_id: {_params['request_id']}")
                        _requestID = str(_params["request_id"])
                    else:
                        if "exaunitid" in _params.keys() and _params["exaunitid"]:
                            if "ignore_uuid_check" not in _params or str(_params["ignore_uuid_check"]).lower().strip() != "true":
                                if not re.match(r"^[1-9][0-9]*$", str(_params["exaunitid"])):
                                    raise ExacloudRuntimeError(0x0810, 0xA, f"Invalid value for exaunitid: {_params['exaunitid']}")
                                _requestID = f"exaunit_{str(_params['exaunitid']).zfill(11)}"
                            else:
                                _requestID = _params['exaunitid']
                            get_gcontext().mSetRegEntry("exaunit_id", str(_params['exaunitid']))
                        else:
                            _requestID = "0000-0000-0000-0000"
                            get_gcontext().mSetRegEntry("exaunit_id", "0000-0000-0000-0000")

                        if "wf_uuid" in _params.keys() and _params["wf_uuid"]:
                            if not "ignore_uuid_check" in _params or str(_params["ignore_uuid_check"]).lower().strip() != "true":
                                if not self.validate_uuid(_params["wf_uuid"]):
                                    raise ExacloudRuntimeError(0x0810, 0xA, f"Invalid value for wf_uuid: {_params['wf_uuid']}")
                            _requestID = f"{_requestID}/{_params['wf_uuid']}"
                            get_gcontext().mSetRegEntry("workflow_id", _params['wf_uuid'])
                        else:
                            _requestID = f"{_requestID}/00000000-0000-0000-0000-000000000000"
                            get_gcontext().mSetRegEntry("workflow_id", "00000000-0000-0000-0000-000000000000")

                    if "steplist" in _params.keys() and _params["steplist"] is not None:
                        _str_steps = str(_params["steplist"])
                        if len(_str_steps) > 63:
                            #IF step list is too large, File too long error occurs
                            _str_steps = _str_steps.replace("ESTP_","")
                            if len(_str_steps) > 63:
                            #IF Still above 63, truncate middle
                                _str_steps = _str_steps[:30]+"..."+_str_steps[-30:]

                        _step = "." + _str_steps
                    else:
                        _step = ""

                    if "undo" in _params.keys():
                        _undo = _params["undo"]
                        if _undo == "True":
                            _undo = ".undo"
                        else:
                            _undo = ""
                    else:
                        _undo = ""

                    get_gcontext().mSetRegEntry("undo", _undo)

                    _cmd = _job.mGetCmd()
                    if 'vmcmd' in _job.mGetOptions():
                        _vmcmd = _job.mGetOptions().vmcmd
                        if _vmcmd is not None and _vmcmd.lower() != "none":
                            _cmd = _cmd + '.' + _vmcmd

                    self.mMkdirWithPoption(os.getcwd() + '/log/threads/' + _requestID)
                    _logfilename_no_extension = os.getcwd() + '/log/threads/' + _requestID + '/'+_job.mGetUUID()+'_'+ \
                                   _job.mGetType() + '.' + _cmd + _step + _undo

                    # In case of Infra patching, append the target
                    # type to the log filename.
                    _target_type = None
                    if _params and _job.mGetCmd() in ["patch_prereq_check", "postcheck", "patch",
                                                 "rollback", "backup_image", "rollback_prereq_check",
                                                 "oneoff", "oneoffv2"]:
                        #This is for single worker patching request
                        if 'singleworkerpatching' in _params and _params['singleworkerpatching'] == "enabled":
                            _jsonconf = _params['jsonconf']['Params'][0]
                        else:
                            _jsonconf = _params['jsonconf']
                        _target_type = (_jsonconf['TargetType'][0]).strip()
                        if _target_type:
                            _logfilename_no_extension = os.getcwd() + '/log/threads/' + _requestID + '/'+_job.mGetUUID()+'_'+ \
                                   _job.mGetType() + '.' + _cmd + '_' + _target_type + _step + _undo

                    _worker_destination_handlers =  ebLogAddDestinationToLoggers(
                        [ebGetDefaultLoggerName()], _logfilename_no_extension, ebFormattersEnum.WORKER)
                    self.__thread_log_path = _logfilename_no_extension
                    _logfilename = _logfilename_no_extension + ".trc"
                #
                # Change Worker Status
                #

                if _job.mGetType() == 'monitor' and _job.mGetCmd() == 'start':
                    ebLogInfo('assign worker %s to monitor' % _worker.mGetPort())
                    _worker.mSetStatus('Running')
                    _worker.mSetType('monitor')
                    _worker.mUpdateDB()
                    ebLogInfo('monitor process registered')
                    continue

                _worker.mSetStatus('Running')
                _worker.mUpdateDB()

                vmhandle = None

                #
                # Execute Job Request
                #
                try:
                    _uuid = _worker.mGetUUID()
                    ebLogInfo("ECS Version: {0}".format(self.__ecs_version))
                    ebLogInfo("Exacloud Path: {0}".format(get_gcontext().mGetBasePath()))
                    ebLogInfo("Exacloud Hostname: {0}".format(socket.getfqdn()))
                    ebLogInfo("Dispatching UUID: {0}".format(_uuid))
                    ebLogInfo('Assign worker Port: {0} PID: {1}'.format(_worker.mGetPort(), _worker.mGetPid()))
                    ebLogInfo("Using ExaKms of type: {0}".format(get_gcontext().mGetExaKms()))

                    # Store last options
                    get_gcontext().mSetRegEntry("operation_id", _uuid)

                    _hostname = _params.get('hostname', 'localhost')

                    with connect_to_host(_hostname, get_gcontext(), local=True) as _node:
                        if _db.mCheckRegEntry('exacloud_block_state') and _job.mGetCmd() not in ["op_cleanup", "block_operations"]:
                            _err_str = "Operations are blocked to be executed in Exacloud"
                            ebLogError(_err_str)
                            raise ExacloudRuntimeError(0x0787, 0xA, _err_str)

                        # mock mode
                        self.mRefreshMock(_params)
                        if self.__mock_mode:
                            ebLogInfo('Worker in MOCK mode')
                            _mock = MockDispatcher(_job)
                            _mock.mDispatchMock()

                        elif _job.mGetType() == "exakms":

                            ebLogInfo("Dispatching ExaKms endpoint")

                            _payload = _job.mGetOptions().__dict__
                            _endpoint = ExaKmsEndpoint(_payload)
                            _result = _endpoint.mExecute()

                            ebLogInfo(f"ExaKms result: {_result}")
                            _job.mSetData(_result)

                        elif _job.mGetType() == "elastic_shape":

                            # Run the endpoind command
                            os.makedirs("log/xmlgen", exist_ok=True)
                            os.makedirs("log/xmlgen/{0}".format(_uuid))
                            _savedir = "log/xmlgen/{0}/".format(_uuid)

                            _payload = _job.mGetOptions().jsonconf

                            ebLogInfo("Executing Callback Generator")

                            _facade = ebFacadeXmlGen(_uuid, _payload, _savedir)
                            _xml = _facade.mGenerateXml()
                            _job.mSetXml(_xml)
                            _job.mSetData(_xml)

                            ebLogInfo("Final XML at: {0}".format(_xml))

                        elif _job.mGetType() == "edv":
                            ebLogInfo("*** EDV: Dispatching EDV management endpoint... ***")
                            _action = edv.EDVAction(_job.mGetCmd())
                            _result = edv.perform_edv_action(_action, _job.mGetOptions())
                            _job.mSetData(json.dumps(_result))
                            ebLogInfo("*** EDV: Finished EDV management operation succesfully ***")

                        elif _job.mGetType() == 'cluctrl':

                            _xml = ""
                            _rc = 0

                            def mCluctrlCallbackFx(aClient, aJob):

                                _xml = aJob.mGetOptions().configpath
                                _payload = aJob.mGetOptions().jsonconf
                                _uuid = aJob.mGetUUID()

                                _inputXmlPath = f"/tmp/exacloud_input_{_uuid}.xml"
                                _inputPayloadPath = f"/tmp/exacloud_input_{_uuid}.json"
                                _outputXmlPath = f"/tmp/exacloud_output_{_uuid}.xml"
                                _outputPayloadStatus = f"/tmp/exacloud_output_{_uuid}.json"

                                ebLogInfo(f"Input XML: {_inputXmlPath}")
                                ebLogInfo(f"Input ECRA Payload: {_inputPayloadPath}")
                                ebLogInfo(f"Output XML: {_outputXmlPath}")
                                ebLogInfo(f"Output Status: {_outputPayloadStatus}")

                                shutil.copyfile(_xml, _inputXmlPath)

                                with open(_inputPayloadPath, "w") as _f:
                                    _f.write(json.dumps(aJob.mGetOptions().jsonconf))

                                _wf = ""
                                if get_gcontext().mCheckRegEntry("workflow_id"):
                                    _wf = get_gcontext().mGetRegEntry("workflow_id")

                                _exaunit = ""
                                if get_gcontext().mCheckRegEntry("workflow_id"):
                                    _exaunit = get_gcontext().mGetRegEntry("exaunit_id")

                                _status = aClient.mMakeCluctrlRequest(
                                    aJob.mGetOptions().cmd,
                                    _inputXmlPath,
                                    _inputPayloadPath,
                                    aJob.mGetOptions().steplist,
                                    aJob.mGetOptions().undo,
                                    _wf,
                                    _exaunit
                                )

                                # Save job status from other exacloud
                                _data = base64.b64decode(_status.pop("xml"))
                                _data = zlib.decompress(_data)

                                with open(_outputXmlPath,'w') as f:
                                    f.write(_data.decode('utf8'))

                                with open(_outputPayloadStatus,'w') as f:
                                    f.write(json.dumps(_status))

                                return _outputXmlPath

                            _xml = self.mRedirectRequestSecondaryExacloud(_job, mCluctrlCallbackFx)

                            if not _xml:

                                vmhandle = exaBoxCluCtrl(aCtx=get_gcontext(), aNode=_node,aOptions=_job.mGetOptions())
                                vmhandle.mSetRequestObj(_job)
                                if _job.mGetCmd() in ['validate_elastic_shapes', 'xsvault', 'infra_vm_states', 'xsput', 'xsget']:
                                    _rc  = vmhandle.mDispatchNonXMLCluster(_job.mGetCmd(), _job.mGetOptions(), aJob=_job)
                                else:
                                    _rc  = vmhandle.mDispatchCluster(_job.mGetCmd(), _job.mGetOptions(), aJob=_job)
                                    _xml = vmhandle.mGetPatchConfig()

                            '''
                            Error Handling :

                            Infra patching error code comes in a newer hex format in _rc and exacloud
                            specific errors are in different format. So below code addresses both the scenarios.

                            Sample Exacloud Error value: _rc = -65383
                            Sample InfraPatching Error value: _rc = 0x030100000

                            '''
                            _infra_patch_status_code = False
                            if _job.mGetCmd() in ["patch_prereq_check", "postcheck", "patch",
                                                "rollback", "backup_image", "rollback_prereq_check",
                                                "patchclu_apply", "oneoff", "exacompute_patch_nodes", "oneoffv2", "infra_patch_operation"]:
                                # Sample return code for infrapatching is 0x03010004 (length is 10)
                                if isinstance(_rc, str) and _rc.startswith("0x") and len(_rc) == 10:
                                    ebLogInfo("Status code from infra patching: {0}".format(_rc))
                                    _infra_patch_status_code = True
                                    if _rc != PATCH_SUCCESS_EXIT_CODE:
                                        _err = _rc
                                        _code, _error_msg, _ = ebPatchFormatBuildError(_err)
                                        if _err and _error_msg and len(_error_msg) > 0:
                                            _err_str = _error_msg
                                            ebLogInfo("Infra Patching error is %s and error_str is %s " % (_err, _err_str))

                            if not _infra_patch_status_code:
                                ebLogInfo("Exacloud Status code: {0}".format(str(_rc)))
                                if (_rc >> 16) == -1:
                                    _cmt = 'request: '+_job.mGetCmd()
                                    _sub_error = str(hex(_rc&0xFFFF))[2:].upper()
                                    _err = '701-'+_sub_error
                                    if _sub_error == '614':
                                        _err_str = "\n".join(gSubError[_sub_error])
                                        ebLogWarn(_err_str)
                                    else:
                                        _err_str = build_error_string(0x701, (_rc&0xFFFF),_cmt)
                                        ebLogError(_err_str)

                        elif _job.mGetType() == "jsondispatch":

                            _rc = 0

                            def mJsonDispatchCallbackFx(aClient, aJob):

                                _payload = aJob.mGetOptions().jsonconf
                                _uuid = aJob.mGetUUID()

                                _inputPayloadPath = f"/tmp/exacloud_input_{_uuid}.json"
                                _outputPayloadStatus = f"/tmp/exacloud_output_{_uuid}.json"

                                ebLogInfo(f"Input ECRA Payload: {_inputPayloadPath}")
                                ebLogInfo(f"Output Status: {_outputPayloadStatus}")

                                with open(_inputPayloadPath, "w") as _f:
                                    _f.write(json.dumps(aJob.mGetOptions().jsonconf))

                                _wf = ""
                                if get_gcontext().mCheckRegEntry("workflow_id"):
                                    _wf = get_gcontext().mGetRegEntry("workflow_id")

                                _exaunit = ""
                                if get_gcontext().mCheckRegEntry("workflow_id"):
                                    _exaunit = get_gcontext().mGetRegEntry("exaunit_id")

                                _status = aClient.mMakeJsonDispatchRequest(
                                    aJob.mGetCmd(),
                                    _inputPayloadPath,
                                    _wf,
                                    _exaunit
                                )

                                with open(_outputPayloadStatus,'w') as f:
                                    f.write(json.dumps(_status))

                                return _status

                            _res = self.mRedirectRequestSecondaryExacloud(_job, mJsonDispatchCallbackFx)

                            if not _res:

                                dispatcher = ebJsonDispatcher(aCtx=get_gcontext(),
                                                        aOptions=_job.mGetOptions())
                                dispatcher.mSetRequestObj(_job)
                                dispatcher.mSetDB(_db)
                                _rc = dispatcher.mDispatch(_job.mGetCmd(),
                                                        _job.mGetOptions())

                            if _job.mGetCmd() == 'imageConfig':
                                ebLogInfo(f"Exacloud Status code: {_rc}")
                                if (_rc >> 16) == -1:
                                    _err = '702'
                                    _err_code = 0x702
                                    _cmt = f"request: {_job.mGetCmd()}"
                                    _err_str = build_error_string(_err_code, (_rc&0x338), _cmt)
                                    ebLogError(_err_str)

                            elif _job.mGetCmd() == 'vmbackup':
                                ebLogInfo(f"Exacloud Status code: {_rc}")
                                if _rc:
                                    _err = '823'
                                    _err_code = 0x823
                                    _cmt = f"request: {_job.mGetCmd()}"
                                    _err_str = f"Error while executing jsondispatch {_job.mGetCmd()}"
                                    ebLogError(_err_str)
                            else:
                                ebLogInfo(f"Exacloud Status code: {_rc}")
                                if (_rc >> 16) == -1:
                                    _cmt = f"request: {_job.mGetCmd()}"
                                    _err_str = build_error_string(0x702, (_rc&0xFFFF), _cmt)
                                    ebLogError(_err_str)

                        elif _job.mGetType() == 'vmctrl':

                            # This commands are only be executed on the ssh_post_fix flow
                            get_gcontext().mSetRegEntry('ssh_post_fix', 'True')

                            # TODO: Return Patched XML
                            ovmhandle = ebVgLifeCycle()
                            ovmhandle.mSetOVMCtrl(aCtx=get_gcontext(), aNode=_node)
                            _rc = ovmhandle.mDispatchEvent(_job.mGetCmd(), _job.mGetOptions())
                            if (_rc >> 16) == -1:
                                _err = '702-'+str(hex(_rc&0xFFFF))[2:]
                                _err_str = 'Error while processing mDispatchEvent: '+_job.mGetCmd()
                                ebLogError(_err_str)

                        elif _job.mGetType() == 'bmcctrl':
                            bmhandle = ebBMCControl(aCtx=get_gcontext(), aJob=_job)
                            _rc = bmhandle.executeCmd(_job.mGetCmd(), _job.mGetOptions())
                            # TBDBM Return proper error code for BM
                            if (_rc >> 16) == -1:
                                _err_code = str(_rc & 0xFFFF)
                                _err = '702-' + _err_code
                                _err_reason = gBMCErrorCodeLookUp.get(_err_code,
                                                                    '')
                                _err_str = 'Error while processing : '+_job.mGetCmd()
                                _err_str += '[' + _err_reason + ']'
                                ebLogError(_err_str)

                        elif _job.mGetType() == 'patch':
                            _rc = 0
                            _options = _job.mGetOptions()
                            if not _options.jsonconf:
                                ebLogError("JSON file not provided. Nothing to be done.")
                                _err = INCORRECT_INPUT_JSON
                            else:
                                _patch_dispatcher = ebCluPatchDispatcher(aJob=_job)
                                _err = _patch_dispatcher.mStartPatchRequestExecution(_options)
                                if _err and _err != PATCH_SUCCESS_EXIT_CODE and _err != 0 :
                                    ebLogError("Found Error Code from Dispatcher during Patching. Value is " + _err)
                                    _patch_json_status = _patch_dispatcher.mGetPatchJsonStatus()
                                    if _patch_json_status:
                                        ebLogInfo("Patch JSON report with error code and error message is\n %s " % _patch_json_status)
                                        _job.mSetData(json.dumps(_patch_json_status))
                                        _error_msg = _patch_json_status["data"]["error_message"]
                                        ebLogError("Error Message %s " % _error_msg)
                                        if _error_msg and len(_error_msg) > 0:
                                            _err_str = _error_msg

                        elif _job.mGetType() == 'network_info':
                            _json_response = getActiveNetworkInformation(_params['jsonconf'])
                            _job.mSetStatusInfo(json.dumps(_json_response, indent = 4))
                            ebLogInfo(f"Network information response: {json.dumps(_json_response, indent = 4)}")

                        elif _job.mGetType() == 'sop':
                            _json_response = process_sop_request(_params['jsonconf'], _uuid)
                            _job.mSetData(json.dumps(_json_response))
                            ebLogInfo(f"SOP execution response: {json.dumps(_json_response, indent = 4)}")

                        else:
                            _err = '700'
                            _err_str = 'Invalid JobRequest type submitted: '+_job.mGetType()
                            ebLogError(_err_str)

                except ExacloudRuntimeError as ere:
                    # bug 29472670: Incident File ER
                    tgt = None
                    if vmhandle and not vmhandle.mIsOciEXACC():
                        try:
                            tgt = exabox.agent.Agent.incident_file_process(
                                ere, _job, vmhandle, step=_step)
                        except Exception:
                            ebLogError('Exception occurred while collecting '
                                       f'diag info:\n{traceback.format_exc()}')

                    _stack_trace = ere.mGetStackTraceMode()

                    # Use ebLogError to get the stack trace back to the Client
                    if _stack_trace:
                        ebLogError(traceback.format_exc())
                    _sub_error = ere.mGetSubErrorCode()
                    _err = '709-' + _sub_error
                    _err_str = '%s' % (ere.mGetErrorMsg())
                    if tgt != None:
                        _err_str = _err_str + "\nIncident file path: " + tgt
                    ebLogError(_err_str)

                    try:
                        ebLogInfo("Downloading logs")
                        _response = {}
                        _params['uuid'] = _worker.mGetUUID()
                        ebDownloadLog(_params, _response, os.getcwd()+'/log')
                        ebLogInfo("logs downloaded at %s" %(_response['file']))
                    except Exception as e:
                        ebLogError("Exception caught while downloading logs %s " % str(e))

                except Exception as oops:
                    # bug 29472670: Incident File ER
                    tgt = None
                    if vmhandle:
                        try:
                            tgt = exabox.agent.Agent.incident_file_process(
                                oops, _job, vmhandle, step=_step)
                        except Exception:
                            ebLogError('Exception occurred while collecting '
                                       f'diag info:\n{traceback.format_exc()}')

                    _stack_trace = True

                    # Use ebLogError to get the stack trace back to the Client
                    if _stack_trace:
                        ebLogError(traceback.format_exc())
                    _err = '709'
                    _err_str = 'Critical Exception caught aborting request [%s]' % (oops,)
                    if tgt != None:
                        _err_str = _err_str + "\nIncident file path: " + tgt
                    ebLogError(_err_str)

                    try:
                        ebLogInfo("Downloading logs")
                        _response = {}
                        _params['uuid'] = _worker.mGetUUID()
                        ebDownloadLog(_params, _response, os.getcwd()+'/log')
                        ebLogInfo("logs downloaded at %s" %(_response['file']))
                    except Exception as e:
                        ebLogError("Exception caught while downloading logs %s " % str(e))

                # Cleanup of cluster folder if feature is enabled in exabox.conf AND
                # in case thread log path is not None and it is cluctrl job and job command is not 'validate_elastic_shapes'
                if self.__config_opts.get("clean_cluster_folder") and self.__config_opts.get("clean_cluster_folder") == "True"\
                    and self.__thread_log_path and _job.mGetType() == 'cluctrl' and _job.mGetCmd() != 'validate_elastic_shapes' and vmhandle\
                    and not vmhandle.mIsOciEXACC():
                    ebLogTrace("*** Cleanup cluster folder operation")
                    self.mCleanupClusterFolder(_xml, vmhandle)
                    # Update _xml to the final xml path under thread logs folder
                    if self.__thread_xml_path:
                        _xml = self.__thread_xml_path

                #
                # Update Job Entry
                #
                _job.mSetStatus('Done')
                # Skip overwriting the already set xml for bmcctrl
                if _job.mGetType() != 'bmcctrl':
                    if _xml:
                        _job.mSetXml(_xml)
                if _err and _err_str:
                    _job.mSetError(_err)
                    _job.mSetErrorStr(_err_str)
                else:
                    _job.mSetError('0')
                    _job.mSetErrorStr('No Errors')

                #OEDA request directory Archiving if it is enabled in exabox.conf.
                if self.__config_opts.get("oeda_archive_requests") and self.__config_opts.get("oeda_archive_requests") == "True":
                    ebLogTrace("*** Proceeding with Archive OEDA request directory operation")
                    self.mArchiveOEDARequests(vmhandle, _job)

                #
                # Remove Worker log handler
                #
                ebLogDeleteLoggerDestination(ebGetDefaultLoggerName(), _worker_destination_handlers)
                if _job.mGetCmd() == 'collect_log':
                    ebLogDeleteLoggerDestination('diagnostic', _worker_destination_handlers)
                _job.mSetTimeStampEnd()
                #
                # Update DB entry
                #
                _db.mUpdateRequest(_job)

                _jconf = _params['jsonconf'] if 'jsonconf' in _params else None
                if _jconf is not None and 'scheduler_job' in _jconf.keys():
                    _db.mUpdateScheduleArchiveByType(_worker.mGetUUID())

                self.CreateClusterLogs(_job.mGetClusterName(), None, _logfilename_no_extension)

                _defunct_pids = kill_proc_tree(int(_worker.mGetPid()))
                if len(_defunct_pids) > 0:
                    ebLogWarn(f"Unable to kill all child processes for worker PID: {_worker.mGetPid()}. Will mark as corrupted for deletion in sometime.")
                    _worker.mSetState("CORRUPTED")

                _current_thread_count = int(threading.active_count())
                ebLogInfo(f"Current active thread count: {_current_thread_count}")
                if self.__config_opts.get("worker_thread_limit"):
                    _worker_thread_limit = int(self.__config_opts.get("worker_thread_limit"))
                    if _worker_thread_limit > 0 and _current_thread_count >= _worker_thread_limit:
                        _worker.mSetState("CORRUPTED")
                        ebLogWarn(f"Marking worker as corrupted since it exceeded worker thread limit of {_worker_thread_limit}, Current thread count: {_current_thread_count}")

                if self.mCheckFDLimitBreach() == True:
                    _worker.mSetState("CORRUPTED")
                    ebLogWarn(f"Marking worker as corrupted since it exceeded worker fd limit!")
                #
                # Reset Worker to Idle
                #
                _worker.mSetStatus('Idle')
                _worker.mResetUUID()
                _worker.mSetLastActiveTime()
                _reg_entry_to_check = f"{_worker.mGetPid()}_WORKER_CORRUPTED"
                if _db.mCheckRegEntry(_reg_entry_to_check):
                    _worker.mSetState("CORRUPTED")
                    _db.mDelRegEntry(_reg_entry_to_check)
                _worker.mUpdateDB()

        self.__main_loop_exited = True

        self.mWorker_Stop()

        if _err:
            return 1

        return 0


    def mCheckFDLimitBreach(self):
        try:
            _fd_limits_enabled = get_gcontext().mCheckConfigOption('fd_limits_enabled')
            if _fd_limits_enabled == 'True':
                _fd_limits = FD_LIMIT_MAXLIMIT
                _threshold = FD_LIMIT_THRESHOLD
                eboxNodeObject = exaBoxNode(get_gcontext())
                _fd_limits_custom_threshold = get_gcontext().mCheckConfigOption("fd_limits_custom_threshold")
                if _fd_limits_custom_threshold != "0":
                    _threshold = int(_fd_limits_custom_threshold)

                _fd_limits_custom_maxvalue = get_gcontext().mCheckConfigOption("fd_limits_custom_maxvalue")
                if _fd_limits_custom_maxvalue != "0":
                    _fd_limits = int(_fd_limits_custom_maxvalue)
                else:
                    _cmd = f"/bin/grep 'Max open files' /proc/{os.getpid()}/limits"
                    _rc, _, _o, _ = eboxNodeObject.mExecuteLocal(_cmd)
                    if _rc == 0:
                        _ulimit_val = int(_o.strip().split()[3])
                        ebLogTrace(f'*** mCheckFDLimitBreach: process fd limit is: {_ulimit_val}')
                        _fd_limits = int(_ulimit_val*_threshold/100)
                ebLogTrace(f'*** mCheckFDLimitBreach: Max allowed fds is: {_fd_limits}')

                p = psutil.Process(os.getpid())
                open_fd_count = p.num_fds()
                ebLogTrace(f'*** mCheckFDLimitBreach: open fd count: {open_fd_count}')
                if open_fd_count > _fd_limits:
                    ebLogError('*** mCheckFDLimitBreach: FD Limit breached. Decomissioning this worker!')
                    _cmd = f"/usr/bin/ls -lt --time-style=full-iso /proc/{os.getpid()}/fd"
                    _rc, _, _o, _ = eboxNodeObject.mExecuteLocal(_cmd)
                    if _rc == 0:
                        ebLogInfo(f'*** mCheckFDLimitBreach: fd dump:')
                        _lines = _o.split('\n')
                        for _line in _lines:
                            ebLogInfo(f'*** {_line}')
                    return True
        except Exception as ex:
            ebLogWarn(f'*** mCheckFDLimitBreach: Got Exception: {ex}.')

        return False

    def mArchiveOEDARequests(self, aVMHandle, aJob):
        try:
            _job = aJob
            if _job.mGetType() != 'cluctrl':
                ebLogTrace(f"Not cluctrl Job. Skipping mArchiveOEDARequests")
                return
            if 'ociexacc' in self.__config_opts.keys() and self.__config_opts['ociexacc'] == "True":
                ebLogTrace(f"ExaCC Env detected. Skipping mArchiveOEDARequests")
                return
            _vmhandle = aVMHandle
            _oeda_request_path = _vmhandle.mGetOEDARequestsPath()
            ebLogTrace(f"*** OEDA Request_path = {_oeda_request_path}")
            ebLogTrace(f"*** Basepath: {get_gcontext().mGetBasePath()}")

            if _oeda_request_path == None:
                ebLogTrace(f"OEDA Request Path is Not Present. Skipping the Archiving Operation..")
                return
            if not os.path.exists(_oeda_request_path):
                ebLogTrace(f"OEDA Request Path is Not Valid. Skipping the Archiving Operation..")
                return

            _oeda_req_archive_path = os.path.join(get_gcontext().mGetBasePath(), 'oeda/requests.bak/')
            if 'oeda_archive_requests_path' in self.__config_opts.keys() and self.__config_opts['oeda_archive_requests_path'] != "":
                _oeda_req_archive_path = os.path.join(get_gcontext().mGetBasePath(), self.__config_opts['oeda_archive_requests_path'])
            ebLogTrace(f"*** _oeda_req_archive_path = {_oeda_req_archive_path}")

            if os.path.exists(os.path.dirname(_oeda_request_path)):
                os.makedirs(_oeda_req_archive_path, exist_ok=True)
                if not os.path.exists(_oeda_req_archive_path):
                    ebLogTrace(f"{_oeda_req_archive_path} path could not be created successfully! Skipping the Archive Operation")
                    return
                _request_id = os.path.basename(_oeda_request_path)
                ebLogTrace(f"*** _request_id = {_request_id}")
                _req_archive_path = os.path.join(_oeda_req_archive_path, _request_id)
                ebLogTrace(f"*** _req_archive_path = {_req_archive_path}")
                try:
                    shutil.move(_oeda_request_path, _oeda_req_archive_path)
                    if os.path.exists(_req_archive_path):
                        ebLogInfo(f"*** Moving OEDA requests directory to archive path succeeded. Request {_oeda_request_path} moved to {_req_archive_path}.")

                except Exception as e:
                    ebLogError(f"*** Moving OEDA requests directory to archive path failed with exception: {str(e)}")
                    raise

            ebLogInfo(f"*** mArchiveOEDARequests completed Successfully!")

        except Exception as e:
            ebLogTrace(f"*** mArchiveOEDARequests failed with Exception: {str(e)}")

    def mCleanupClusterFolder(self, aXML, aVMHandle):
        try:
            _xml = aXML
            vmhandle = aVMHandle
            if not _xml:
                _xml = vmhandle.mGetPatchConfig()
            if os.path.exists(os.path.dirname(self.__thread_log_path)) and _xml:
                _dest_xml_file = self.__thread_log_path + ".xml"
                ebLogTrace(f"Copying the final patched xml for the operation to {_dest_xml_file}.")
                shutil.copy2(_xml, _dest_xml_file)
                # Updated self.__thread_xml_path path to _dest_xml_file needed for updating in db later when request is done
                # And the original _xml path under clusters folder will be removed below
                # This xml under thread logs path will be cleaned up by the scheduler every 7 days.
                self.__thread_xml_path = _dest_xml_file
                vmhandle.mSetPatchConfig(self.__thread_xml_path)
                _cluster_paths = []
                _cluster_lock_files = vmhandle.mGetClusterLockFiles()
                if _cluster_lock_files:
                    try:
                        for _cluster_lock_file in _cluster_lock_files:
                            _cluster_paths.append(os.path.dirname(_cluster_lock_file))
                            ebLogTrace(f"Removing cluster lock file : {_cluster_lock_file}.")
                            os.remove(_cluster_lock_file)
                    except Exception as ex:
                        ebLogTrace(f"Could not remove {_cluster_lock_file}. Lock file list: {_cluster_lock_files}. Error: {ex}.")
                _cluster_paths = list(set(_cluster_paths))
                for _cluster_path in _cluster_paths:
                    _short_cluster_path = vmhandle.mGetShortClusterPath(os.path.basename(_cluster_path))
                    _number_lock_files = len(list(glob.glob(os.path.join(_cluster_path, "cluster_lock_*"))))
                    if _number_lock_files > 0:
                        ebLogTrace(f"Not removing the cluster directory: {_cluster_path}. Another operation is using it. Number of lock files: {_number_lock_files}.")
                    else:
                        try:
                            if _short_cluster_path:
                                ebLogTrace(f"Unlinking {_short_cluster_path} since it is not needed after operation is completed.")
                                os.unlink(_short_cluster_path)
                        except Exception as ex:
                            ebLogTrace(f"Could not unlink {_short_cluster_path}. Error: {ex}.")
                        try:
                            ebLogTrace(f"Removing {_cluster_path} since it is not needed after operation is completed.")
                            shutil.rmtree(_cluster_path)
                        except Exception as ex:
                            ebLogTrace(f"Could not remove {_cluster_path}. Error: {ex}.")
        except Exception as ex:
            ebLogTrace(f"Error in cleanup of cluster folder. Error: {ex}.")


    def CreateClusterLogs(self, aCluName, aLogFile=None, aLogFileNoExt=None):
        _cluname = aCluName
        _logfilename_no_extension = aLogFileNoExt
        _logfilename = aLogFile

        if _cluname:
            _cludir = os.getcwd() + '/log/clusters/' + _cluname
            self.mMkdirWithPoption(_cludir)
            _logfnames = []
            if _logfilename_no_extension:
                _logfnames.append("{}.log".format(_logfilename_no_extension))
                _logfnames.append("{}.trc".format(_logfilename_no_extension))
                _logfnames.append("{}.err".format(_logfilename_no_extension))
            elif _logfilename:
                _logfnames.append(_logfilename)

            for _logfilename in _logfnames:
                if os.path.exists(_logfilename):
                    _fname = _logfilename.split("/")[-1]
                    _flink = _cludir + "/" + _fname
                    os.symlink(_logfilename, _flink)

    @exception_handler_decorator
    def mProcessSignalsDB(self, aWorker, aDB):

        _db = aDB

        if aWorker:

            _pid = aWorker.mGetPid()
            _port = aWorker.mGetPort()

            _criteria = {"pid": _pid}
            _signals = _db.mFilterAgentSignal(_criteria)

            # Process the signals
            for _signal in _signals:

                _signalName = _signal.mGetName()
                ebLogInfo(f"Processing Signal {_signalName} on Worker {_pid}:{_port}")

                # Remove the signals from the DB
                _db.mDeleteAgentSignal(_signal)

                # Execute the callback that receive only one worker
                for _signalMapName, _callback in self.mGetSignalDBMap().items():
                    if _signalMapName.value == _signalName:
                        _callback(aWorker)

    def mReloadConfig(self, aWorker):

        if aWorker:

            exaBoxCoreInit(aOptions={}, aReload=True)

            if not get_gcontext().mGetExaKmsSingleton():
                get_gcontext().mSetExaKmsSingleton(ExaKmsSingleton())

            ebLogInfo("Perform Reload of worker: {0}/{1}".format(aWorker.mGetPid(), aWorker.mGetPort()))

    def mWorker_Shutdown(self):

        self.__exit_main_loop = True

        global gDaemonHandle
        gDaemonHandle = None

    def mWorker_Stop(self):

        if self.__abort_worker:
            return

        _worker = ebWorker()
        _worker.mLoadWorkerFromDB(self.__port)
        if _worker.mGetType() == 'monitor':
            _job = ebJobRequest(None,{}, aDB=ebGetDefaultDB())
            _job.mLoadRequestFromDB(_worker.mGetUUID())
            _job.mSetStatus('Done')
            _job.mSetTimeStampEnd()
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_job)

        ebLogInfo('Worker stopped on port (%d)...' % (self.__port))
        #
        # Shutdown RestListener
        #
        if self.__restlistener is not None:
            self.__restlistener.mStopRestListener()
        #
        # Deregister Worker
        #
        if self.__worker is not None:
            self.__worker.mDeregister()
            ebLogInfo('*** Worker Deregistered...')
        else:
            ebLogInfo('*** Skip worker deregistration due to issues in startup.')
        #
        # Remove logger handler (not really required)
        #
        if self.__worker_destination_handlers:
            ebLogInfo(80*'-'+' : '+time.asctime())
            ebLogDeleteLoggerDestination(ebGetDefaultLoggerName(), self.__worker_destination_handlers)

        #
        # Gate any additional calls to mWorkerStop
        #
        self.__abort_worker = True

    def mWorker_Status(self):
        pass

    def mWorker_SigHandler(self, signum, frame):
        self.mWorker_Shutdown()

gWorkerFactory = None

def gGetDefaultWorkerFactory():
    global gWorkerFactory
    return gWorkerFactory

class ebWorkerFactory(object):

    def __init__(self):

        self.__config_opts = get_gcontext().mGetConfigOptions()

        if 'worker_port' in self.__config_opts.keys():
            self.__port_range = int(self.__config_opts['worker_port'])
        else:
            self.__port_range = 9000

        self.__port_index = self.__port_range
        self.__port_list  = []

        self.mResetWorkersList()
        self.__nb_workers = self.mGetWorkerCount()

        self.__use_different_port_validator = True
        if 'use_different_portvalidator' in self.__config_opts.keys():
            _current_value = self.__config_opts['use_different_portvalidator']
            if _current_value == "False":
                self.__use_different_port_validator = False

        self.__socket_connect_timeout = SOCKET_CONNECT_TIMEOUT
        if 'socket_connect_timeout_sec' in self.__config_opts.keys():
            _current_value = self.__config_opts['socket_connect_timeout_sec']
            self.__socket_connect_timeout = int(_current_value)

        self.__worker_port_extravalidation = True
        if 'worker_port_extravalidation' in self.__config_opts.keys():
            if self.__config_opts['worker_port_extravalidation'] == "False":
                self.__worker_port_extravalidation = False

        #
        # Only one Worker Factory currently supported
        #
        global gWorkerFactory
        assert(gWorkerFactory is None)
        gWorkerFactory = self

    def mGetWorkerCount(self):
        _workers = 0
        #exacc type env
        if 'ociexacc' in self.__config_opts.keys():
            if self.__config_opts['ociexacc'] == "True":
                ebLogInfo(f'Deployed environment is exacc type')
                if 'worker_count_nonexacs' in self.__config_opts.keys():
                    _workers = int(self.__config_opts['worker_count_nonexacs'])

        #exacs type env
        if _workers == 0 and 'deployment_target_type' in self.__config_opts.keys():
            if self.__config_opts['deployment_target_type'] == "prod":
                ebLogInfo(f'Deployed environment is production type')
                if 'worker_count' in self.__config_opts.keys():
                    _workers = int(self.__config_opts['worker_count'])
            else:
                ebLogInfo(f'Deployed environment is dev type')

        #dev type env
        if _workers == 0:
            if 'worker_count_nonexacs' in self.__config_opts.keys():
                _workers = int(self.__config_opts['worker_count_nonexacs'])
            else:
                _workers = 8

        # if agent is started with -workernum N argument, this value will take
        # precedence over other config values
        self.__args_opt = get_gcontext().mGetArgsOptions()
        if self.__args_opt.worker_num:
            _workers = int(self.__args_opt.worker_num)

        ebLogInfo(f'ebWorkerFactory: worker thread count is : {_workers}')
        return _workers

    def mGetWorkersList(self, aDB=None):

        _db = aDB or ebGetDefaultDB()
        try:
            _rqlist = literal_eval(_db.mDumpWorkers())
        except:
            ebLogError('*** DB access critical error please review DB integrity')
            raise

        return _rqlist

    def mResetWorkersList(self, aDB=None):
        """Remove any Exited worker from the Workers BD"""

        _rqlist = self.mGetWorkersList(aDB)

        for _req in _rqlist:
            if _req[1] == 'Exited':
                _worker = ebWorker(aDB=aDB)
                _worker.mLoadWorkerFromDB(_req[9])
                _worker.mDelete()

    def mCheckFactory(self, aDB=None):
        """
        Read Workers DB and check for all worker not Exited (e.g. Idle, Running,...) that they can be pinged
        """
        _rqlist = self.mGetWorkersList(aDB)

        for _req in _rqlist:
            if _req[1] != 'Exited' and (_req[10] not in ebStandaloneWorkerSet):
                ebLogTrace('*** [WF] Worker BD_REQ: %s STATE: %s PID: %s PORT: %s' % ( _req[0], _req[1], _req[8], _req[9] ))
                if _req[1] in ['Running', 'Idle']:
                    #
                    # Check if Worker process/PID is still running
                    #
                    _pid = _req[8]
                    if _pid:
                        try:
                            os.kill(int(_pid),0)
                        except:
                            ebLogWarn('*** [WF] Worker DB inconsistency detected. Worker PID (%d) but no corresponding process is running' % (int(_pid)))
                            _pid = 0
                    #
                    # Check if there is a listening socket on the Worker's port
                    #
                    _port = _req[9]
                    if _port:
                        #
                        # Check if network port is already in used
                        #
                        if self.__use_different_port_validator:
                            _port = self.mCheckPortForValidation(_port)
                        else:
                            _port = self.mCheckPort(_port)

                        if not _port and (_req[10] not in ebStandaloneWorkerSet):
                            ebLogWarn('*** [WF] Worker port detection for (%d) failed' % (int(_req[9])))

                        _update = False
                        if (_port and not _pid):
                            ebLogError('*** [WF] Worker listening port active but related Worker/PID is not running')
                            #
                            # Try to shutdown unknown worker
                            #
                            _workercmd = ebWorkerCmd(aCmd='shutdown',aPort=_req[9])
                            _workercmd.mIssueRequest()
                            _json = _workercmd.mWaitForCompletion()
                            if not _json:
                                ebLogError('>>> Worker is not accessible at port (%s)' % (_req[9]))
                            _update = True

                        if (not _port and _pid and int(_pid) != os.getpid()):
                            ebLogError('*** [WF] Worker/PID running but not listening port active')
                            _process = psutil.Process(int(_pid))
                            ebLogInfo(f"Worker process {_pid} status: {_process.status()}")

                            #
                            # Kill zombie worker
                            #
                            _killed = False
                            #Lets attempt a clean shutdown first.
                            try:
                                os.kill(int(_req[8]),signal.SIGTERM)
                            except Exception as e:
                                ebLogError(f"*** Exception caught while trying to kill process {_pid} with SIGTERM. Exception: {str(e)}")

                            time.sleep(10)
                            try:
                                #Checking if the process got killed.
                                os.kill(int(_req[8]),0)
                            except:
                                ebLogInfo(f"*** Worker process with pid {_pid} successfully terminated!")
                                _killed = True
                            if _killed is False:
                                #Kill using SIGKILL. This is a fallback option, which will kill the process immediately.
                                ebLogWarn(f"*** Sending SIGKILL for worker process with pid {_pid}!")
                                try:
                                    kill_proc_tree(int(_req[8]))
                                    os.kill(int(_req[8]),signal.SIGKILL)
                                except Exception as e:
                                    ebLogError(f"*** Exception caught while trying to kill process {_pid} with SIGKILL. Exception: {str(e)}")

                            #SIGTERM handler deregisters the worker. Hence no need to update db again.
                            _update = False

                        if (not _port and not _pid):
                            _update = True
                        #
                        # Update Worker DB Entry
                        #
                        if _update:
                                _worker = ebWorker(aDB)
                                _worker.mLoadWorkerFromDB(_req[9])
                                _worker.mDeregister()
                                ebLogWarn('*** [WF] De-Register Worker for PID/Port (%s/%s)' % (_req[8], _req[9]))
                    else:
                        ebLogWarn('*** [WF] Worker DB entry does have a port set')
            elif _req[10] in  ebStandaloneWorkerSet:
                # UUID is irrelevant for supervisor/scheduler
                ebLogTrace('*** [WF] Worker STATE: %s PID: %s PORT: %s' % ( _req[1], _req[8], _req[9] ))
            else:
                ebLogWarn('*** [WF] Exited Worker BD_REQ: %s STATE: %s PID: %s PORT: %s' % ( _req[0], _req[1], _req[8], _req[9] ))


    """For future implementation, this function needs to decorated with a timeoue using the below python library. Unable to do this now since BA approval takes time.
    https://pypi.org/project/wrapt-timeout-decorator/
    This will help ensure that the mCheckPortForValidation function doesn't get stuck. This fucntion should get over within 30 seconds maximum."""
    def mCheckPortForValidation(self, aPort):
        """Returns port number if the port is reachable and is connectable.
        Returns zero if port is unreachable."""

        _retries = DEFAULT_MAX_RETRIES
        if 'socket_check_retry' in self.__config_opts.keys():
            _retries = int(self.__config_opts['socket_check_retry'])
        if _retries > DEFAULT_MAX_RETRIES:
            _retries = DEFAULT_MAX_RETRIES
        _port = aPort

        for _retry_idx in range(_retries):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as _sock:
                _sock.settimeout(self.__socket_connect_timeout)
                _sock_rc = _sock.connect_ex(('localhost', int(_port)))
                if _sock_rc == 0:
                    ebLogTrace(f"Connection to {_port} is successful.")
                    return _port
                elif _retry_idx == (_retries - 1):
                    ebLogError(f"Socket connection validation failed for port {_port}. Unix error code: {_sock_rc}, Error details: {os.strerror(_sock_rc)}")

        _inet_infos = psutil.net_connections()
        ebLogTrace(f"Validating port activity using net_connections. Current opened inet ports in the system: {len(_inet_infos)}")
        for _current_inet_info in _inet_infos:
            _local_addr_info = "%s:%s" % (_current_inet_info.laddr)
            _current_pid = _current_inet_info.pid
            _current_port = _local_addr_info.split(':')[-1]
            _current_port_status = _current_inet_info.status
            if _current_port == str(_port):
                ebLogWarn(f"Port {_port} is owned by the PID {_current_pid}. Status: {_current_port_status}.")
                if _current_pid is not None and psutil.pid_exists(_current_pid):
                    _process_struct = psutil.Process(_current_pid)
                    _owned_process_details = _process_struct.as_dict(attrs=['pid', 'name', 'cmdline', 'status', 'create_time'])
                    ebLogTrace(f"Owned process details: {_owned_process_details}")
                return _port

        ebLogTrace(f"Port {_port} is not owned by any PID and is not connectable.")
        return 0


    def mCheckPort(self, aPort, aNeedExtraValidation=False):
        """Check if a network port in localhost is already being used

        :param aPort: network port to check
        :returns: aPort if port is already in use or 0 if port is available for grab
        """

        _port = aPort
        _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _rc = _sock.connect_ex(('localhost', int(_port)))
        if _rc == 0:
            pass
        else:
            ebLogTrace(f"*** Connect to port failed via socket_connect: {_port}, return code: {_rc}")
            if self.__worker_port_extravalidation and aNeedExtraValidation:
                for _current_inet_info in psutil.net_connections():
                    _local_addr_info = "%s:%s" % (_current_inet_info.laddr)
                    _current_pid = _current_inet_info.pid
                    _current_port = _local_addr_info.split(':')[-1]
                    if _current_port == str(_port):
                        ebLogWarn(f"Port {_port} has failed validation because of existing connections to the same port. PID {_current_pid} is currently occupying the same port.")
                        _sock.close()
                        return _port

            #If there are no matches in any of the existing local processes for the current port, it is safe to use.
            ebLogTrace(f"Port {_port} is free to be used as worker port at the moment.")
            _port = 0
        _sock.close()

        return _port

    def mGetPort(self, aBPort, aPortList):
        _port = 0
        _bport = aBPort
        while not _port:
            # Check if port is already in used by another worker
            while _bport in aPortList:
                _bport = _bport + 1

            # Check if port is already
            _port = self.mCheckPort(_bport, aNeedExtraValidation=True)

            # Increment port if already taken
            if _port:
                _bport = _bport + 1
                _port  = 0
            else:
                _port  = _bport
            ebLogInfo(f'*** Acquired port ({_port}/{_bport})')

        return _port

    def mStartWorkers(self, aWorkerCount=0):

        _rc = 0

        _wcount = self.__nb_workers
        if aWorkerCount:
            _wcount = aWorkerCount

        _rqlist = self.mGetWorkersList()
        _bport  = self.__port_index

        # Build list of port already used by existing/running workers.
        _port_list = []
        for _worker in _rqlist:
            _port_list.append(_worker[9])

        # Start workers
        # for _idx in range(0,_wcount):
        _wc = _wcount
        while _wc > 0:
            _port = self.mGetPort(_bport, _port_list)

            _port_list.append(_port)
            _ctx = get_gcontext()
            _opt = _ctx.mGetArgsOptions()

            # Start a new worker using the port we found
            _cmd_list = ['bin/exacloud', '-dc', '-wp', str(_port), '-w', '-wd']
            if _opt.proxy:
                _cmd_list = ['bin/exaproxy', '--proxy', 'asproxy', '-dc', '-wp', str(_bport), '-w', '-wd']

            # Check if run as a exatest
            if not isinstance(_opt, dict):
                _opt = vars(_opt)

            if 'exatest' in _opt and _opt['exatest']:
                _cmd_list.append('--exatest')
                ebLogInfo(f'Executing command: {_cmd_list}')

            # Add args that need to be propagated (e.g. --debug/--verbose)
            _cmd_list.extend(get_gcontext().mGetPropagateProcOptions())
            _child = None
            try:
                ebLogInfo(f'*** Starting Worker on port ({_port})')
                _child = subprocess.run(_cmd_list, stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE,
                                                check=True)

                # Wait for Worker to be started (e.g. check for status on given port)
                _timeout = 5
                while _timeout:
                    #The wait time has been increased from 2 to 8 seconds after the introduction on MYSQL connections which take more time to initialise.
                    time.sleep(8)
                    _workercmd = ebWorkerCmd(aCmd='status', aPort=_port)
                    _workercmd.mIssueRequest()
                    _json = _workercmd.mWaitForCompletion()
                    if not _json:
                        ebLogWarn(f'>>> Worker is not accessible at port ({_port})')
                    else:
                        break
                    _timeout = _timeout -1

                if _timeout == 0:
                    ebLogError(f'>>> Worker did not start on port ({_port})')
                    _rc = -1
                    break

                _wc -= 1

            except subprocess.CalledProcessError as cpe:
                _stderr = _child.stderr.decode("UTF-8")
                _stdout = _child.stdout.decode("UTF-8")
                ebLogError(f'*** Starting Worker command: {_cmd_list} failed '\
                           f'on port: {_bport} \nstderr: {_stderr} \nstdout: {_stdout}\n\n')

            _bport = _port + 1

        self.__port_list  = _port_list
        self.__port_index = _bport

        return _rc


    def mInitFactory(self):

        self.mCheckFactory()

        self.mResetWorkersList()

        ebLogInfo('*** Start Workers ...')

        self.mStartWorkers()

    def mShutdownFactory(self):

        _rqlist = self.mGetWorkersList()

        for _req in _rqlist:
            if _req[1] != 'Exited' and (_req[10] not in ebStandaloneWorkerSet):
                ebLogWarn('*** Worker BD_REQ: '+_req[0]+' STATE: '+_req[1])
                if _req[1] in ['Running', 'Idle', 'Refreshing']:
                    ebLogInfo('*** Shutdown Worker on port: (%s)...' % (_req[9]) )
                    _workercmd = ebWorkerCmd(aCmd='shutdown',aPort=_req[9])
                    _workercmd.mIssueRequest()
                    _workercmd.mWaitForCompletion()

        # Wait until workers are done
        _killed = False
        while not _killed:
            _killed = True
            _rqlist = self.mGetWorkersList()
            for _req in _rqlist:
                if _req[1] != 'Exited' and (_req[10] not in ebStandaloneWorkerSet):
                    _killed = False
            time.sleep(1)

    def mFactoryStatus(self):
        pass

    def mFactoryWorkerStatus(self,aWorker):
        pass

# end of file
