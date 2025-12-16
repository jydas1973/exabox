"""
$Header:

 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    Agent - Configuration File Managemenet

FUNCTION:
    Agent Core functionalities

NOTE:
    None

History:
   MODIFIED (MM/DD/YY)
   ririgoye  11/26/25 - Bug 38636333 - EXACLOUD PYTHON:ADD INSTANTCLIENT TO
                        LD_LIBRARY_PATH
   aypaul    11/26/25 - ER#38653499 Add trace message for LD_LIBRARY_PATH
                        configuration.
   aypaul    11/17/25 - ER#37732654 Update oracle client home for use in AQ validation.
   aararora  10/27/25 - Bug 38348881: Reject invalid requests before parsing
                        parameters
   rajsag    09/17/25 - enh 38389132 - exacloud: autoencryption support for
                        exascale configuration
   aypaul    08/07/25 - Enh# 37732728 Support for storing AQ name from each
                        requests.
   nisrikan  06/23/24 - Bug 38053933 - FIX THE ISSUES FOR OPCTL SUPPORT FOR EXACS
   aararora  05/21/25 - ER 37732745: Send response to ecra using AQ
   rajsag    05/21/25 - Enh 37526315 - support additional response fields in
                        exacloud status response for stepwise status update
   aypaul    05/21/25 - Bug#37948804 Randomise the idle worker selection
                        process to distribute the load evenly.
   jbrigido  05/06/25 - Bug 37911519 Enableing Restrcited Apis in all regions
   aypaul    04/23/25 - Bug#37535214 Save a backup of exabox.conf post successful startup..
   aypaul    03/25/25 - Bug#37666465 Deprecate mServeUI endpoint.
   jyotdas   03/12/25 - Bug 37662723 - Dispatcher error is empty for single
                        thread patch operation
   aararora  02/05/25 - ER 37541321: Update percentage progress of rebalance
                        operation
   aararora  12/20/24 - ER 37402747: Send updated xml in the response
   pverma    12/12/24 - Add infra_vm_states to xml_less list of commands
   jbrigido  12/12/24 - Bug 37383325 Moving block of code inside of if
                        statement
   jbrigido  12/03/24 - Bug 37352141 EXACLOUD RESTARTING WITH NO OCIREGION IN
                        OCPS_JSON
   aypaul    12/02/24 - ER-37026034 Update status compilation for new request
                        data.
   jyotdas   11/26/24 - ENH 37267666 - Register separate operations for patch
                        precheck and rollback for single threaded operations
   jbrigido  11/20/24 - Bug 37298937 Adding verification when ocps json file
                        does not exist in local exacloud
   jbrigido  11/15/24 - Bug 37259548 Enabling Restricted Apis to only certain
                        regions
   aararora  11/14/24 - ER 36253480: Return ASM rebalance status during
                        rebalance step
   oespinos  11/07/24 - 37234027 Adding domain "oracle.local" to
                        ACCEPTED_DEVQA_DOMAINNAMES
   ririgoye  11/06/24 - Bug 37229020 - EXACS EXACLOUD - OEDA_BUILD IS UPDATED
                        ONLY WHEN EXACLOUD IS RESTARTED
   jyotdas   10/01/24 - ER 37089701 - ECRA Exacloud integration to enhance
                        infrapatching operation to run on a single thread
   nisrikan  09/30/24 - Bug 37109476 - INSTALL OPCTL RPM FAILING AT EXACLOUD
   aypaul    08/29/24 - Bug#37002424 Determine deployment type for exacloud.
   aypaul    08/13/24 - Enh#34242877 Add support for import data for backup for
                        mysql tables.
   aypaul    08/05/24 - Bug#36906041 rectify exacc check.
   aypaul    06/13/24 - Enh#36705805 Support exacloud api access control.
   rajsag    06/13/24 - 36603931 - EXACLOUD : EXASCALE DB VAULT CREATION
                        SUPPORT36534554 - EXACLOUD : EXACLOUD CHANGES TO
                        SUPPORT EXASCALE VAULT LCM OPERATIONS
   prsshukl  04/18/24 - Bug 36527975 - IMPLEMENT FEATURE TO MOCK INFRAPATCH
                        FROM EXACLOUD
   nisrikan  01/22/24 - ER 36211263 - ER for OPCTL support for ExaCS in ECRA and Exacloud
   naps      01/05/24 - Bug 36157324 - partial revert of 35896839.
   naps      12/01/23 - Bug 35896839 - Handle broken pipe exception in agent
                        error handling.
   jyotdas   11/29/23 - 35955958 - Ecra status call in pending status
   joysjose  10/17/23 - Bug 35906617 - correction of oeda requests path
   aypaul    09/20/23 - Enh#35813639 Forceshutdown(-fsd) to make sure that
                        crontab entry to be removed if it exists.
   pbellary  08/16/23 - Bug 35702302 - CLEAR TEXT PASSWORDS IN EXACLOUD AGENT LOG
   naps      07/21/23 - Bug 35013360 - Dispatcher and WorkerManager
                        implementation.
   ririgoye  07/11/23 - Bug 35581074 - Added support for mock mode requests
   ririgoye  07/10/23 - Enh 35580256 - Added exception for invalid operation
                        UUID
   scoral    06/20/23 - Enh 35454589 - Add a API for EDV volumes prechecks.
   jyotdas   06/13/23 - BUG 35488103 - Domu os patch fails with page_oncall
                        error instead of fail_and_show for dispatcher errors
   aypaul    03/31/23 - Enh#35221396 Read special worker PIDs from DB instead
                        of the agent context.
   naps      01/31/23 - Bug 34958798 - Make cpu and mem threshold values
                        configurable.
   aypaul    01/12/23 - Enh#34971851 SOP scripts execution support.
   aypaul    01/02/23 - Enh#34822394 Add free workers information in system
                        metrics endpoint.
   aypaul    12/11/22 - ENH#34822394 Endpoint to return system resources
                        statistics.
   aypaul    12/04/22 - Issue#34607716 Handle multiprocessing issue by shutting
                        down base manager instance explicitly.
   jfsaldan  09/06/22 - Enh 34567492 - Exacloud to include OEDA BUILDBRANCH in
                        Version Endpoint
   aypaul    09/05/22 - Enh#34411005 API implementation for active network
                        information.
   aararora  08/16/22 - Add step during incident file creation.
   aypaul    07/05/22 - Bug#34347508 Worker allocation optimisation logic
                        correction.
   jfsaldan  06/01/22 - Bug 34185829 - Enable debug mode for dispatchWorker
                        function
   ndesanto  04/29/22 - Removed no longer needed import.
   ndesanto  04/13/22 - Retrieve region directly from cavium. Dummy endpoint.
   aypaul    04/04/22 - Bug#34031174 Replace mdumpRequests with fetch pending
                        requests.
   alsepulv  02/24/22 - Enh 33691491: Add http api for jsondispatch
   jyotdas   02/22/22 - Bug 33798374 - dispatcher error should display only
                        patching messages for infrapatching operations
   aypaul    02/21/22 - 33855012 Updating agent code for unit tests.
   aypaul    01/25/22 - Enh#33611377 Worker limit and resource
                              utilisation optimisation.
   ndesanto  01/12/22 - ECRA endpoint to update OCI region.
   araghave  12/08/21 - Enh 33598784 - MOVE ALL INFRA PATCHING ERROR CODES FROM
                        ERROR.PY TO INFRAPATCHERROR.PY
   aypaul    11/29/21 - Mock mode for perform request.
   rajsag    08/13/21 - 31985002 - ensure asm reshape flows update point in
                        time status for every step in request table
   aypaul    07/29/21 - Bug#33150016 Implement get custom policies API to send
                        back generated se linux exception policies.
   aypaul    06/17/21 - Bug#32677660 Generate exception policies on
                        create_service/vmgi_reshape failure.
   ndesanto  06/17/21 - Bug 32989307: Fix for HTTPS txn
   jyotdas   05/12/21 - Enh 32803507:populate patching error message from exacloud 
   ndesanto  05/13/21 - Bug 32884378: Fixing mssing import due to auto merge removal.
   ndesanto  04/12/21 - Bug 32041800: HTTPS and Certificate Rotation
   aypaul    04/24/21 - Bug#32677651 Exacloud to update policies on provisioned clusters.
   joserran  04/27/21 - Bug 32394314 - Propagate options to agent
   araghave  04/14/21 - Enh 31423563 - PROVIDE A MECHANISM TO MONITOR INFRA
                        PATCHING PROGRESS
   jyotdas   03/22/21 - Enh 32415195 - error handling: return infra patching
                        dispatcher errors to caller
   alsepulv  03/05/21 - Bug 32592473: replace get_stack_trace() with
                        traceback.format_exc()
   araghave  10/21/20 - Enh 31925002 - Error code handling implementation 
                        for Monthly Patching
   dekuckre  10/07/20 - 31465951: Enhancements to proxy feature
   ndesanto  09/08/20 - Added None check on DB return value
   seha      04/22/20 - bug 31197624 split log transmitted from cps to ecra
   dekuckre  26/02/20 - 30697759: Add ebGetRequestObj
   araghave  20/02/20 - Enh 30908782 - ksplice configuration on dom0 and cells
   ndesanto  10/02/19 - 30374491 - EXACC PYTHON 3 MIGRATION BATCH 01 
   araghave  07/02/19 - ENH 29911293 - POSTCHECK OPTION FOR ALL PATCH OPERATION.
   seha      06/25/19 - bug 29947189 provide exaccocid to fetch log request
   seha      05/27/19 - Bug 29679165 log collection for OCI-ExaCC
   ndesanto  05/10/19 - added code to support the request backup
   ndesanto  04/09/19 - Bug 29624735: Fixing re-raising of exceptions to keep exception context
   oespinos  07/09/18 - Bug 28299175: return original dbException instead of raising new one
   oespinos  07/09/18 - 28314445 - Allow /AgentCtrl results to be paged
   oespinos  06/27/18 - Bug 28250045: add AgentCtrl url params (refresh, cmdtype, clustername)
   sachikuk  03/29/18 - Bug 27776337: Exacloud should reuse request uuid sent by ECRA
   hgaldame  02/07/18 - XbranchMerge hgaldame_bug-27071543_exacm from
                        st_ecs_17.3.6.0.0exacm
   seha      01/25/18 - Enh 27427661: Add diagnostic module log path to
                        mAgentLogDownload()
   jreyesm   10/06/17 - Bug 26025164. Checksum for one-off files.
   sdeekshi  08/25/17 - Bug 26571290: restructure mock code to use existing dispatcher framework
   hcheon    07/27/17 - Add CLUDiags command
   sdeekshi  07/07/17 - Bug 26409889: mock exaunit_info, start_vm, stop_vm, restart_vm endpoints
   nmallego  07/17/17 - bug26387175 - in mShowStatus(), mark success for
                        the error codes '701-614 and 703-614', since it's
                        not handle today
   gsundara  05/17/17 - Fix for bug 26002454
   mrajm     05/31/17 - Bug 26171208: Add logs download page
   pverma    04/07/17 - Support for sparse for existing customers
   mirivier  10/24/15 - BUG 21564916: Sanitize agent log to remove sensitive information + agent_debug option
   mirivier  10/15/15 - Add TimeZone and Cache-Control
   mirivier  01/21/15 - Create file
"""

from six.moves.urllib.parse import urlparse
from socket import error as socket_error
from socket import gethostname, getfqdn
from ast import literal_eval
from time import strftime
from datetime import datetime
import errno
import subprocess
import socket
import os, inspect
import sys
import re
import traceback
import base64
import json
from six.moves import _thread
import uuid
from six.moves import urllib
import time
import logging
from six.moves import socketserver
import signal
import threading
import hashlib
import six
import glob
import random

from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.core.Mask import maskSensitiveData
from exabox.core.Core import ebCoreContext
from exabox.core.Context import get_gcontext, ReadOnlyDict
from exabox.log.LogMgr import (ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogTrace,
                                ebThreadLocalLog, ebLogAgent, ebLogAddDestinationToLoggers,
                                ebLogDeleteLoggerDestination, ebGetDefaultLoggerName, ebFormattersEnum)
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.ovm.cludiag import ebDownloadLog
from exabox.ovm.cluincident import ebIncidentNode
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.DBStore import ebGetDefaultDB
from exabox.core.Core import ebExit
from exabox.agent.Worker import ebWorkerFactory, ebWorker, gGetDefaultWorkerFactory
from exabox.agent.Worker import daemonize_process, redirect_std_descriptors
from exabox.agent.Client import ebExaClient, ebGetClientConfig
from exabox.agent.Mock import MockStatus, MockDispatcher
from exabox.agent.ebJobRequest import ebJobRequest, nsOpt
from exabox.agent.HTTPResponses import JSONResponse, HttpCb, HTMLResponse, FileResponse, ErrorBuilder
from exabox.agent.HTTPRequest import HttpRequest
from exabox.agent.HTTPProcessors import (MethodWrapper, ConvertPathToParam,
                                         DecodeBase64, EncodeBase64, GetPathForIndex,
                                         ConvertHttpHeaderToParam, DecodeBase64Policy)
from exabox.agent.Supervisor import ebSupervisor
from exabox.elastic.HardwareInfo import ebHardwareInfo
import exabox.ovm.monitor as monitor
from multiprocessing import Process, Lock
from multiprocessing.managers import BaseManager
from exabox.core.CrashDump import CrashDump
from exabox.ovm.cluexaccatp import ebExaCCAtpSimulatePayload
from exabox.agent.Supervisor import supervisor_running
from exabox.agent.Dispatcher import dispatcher_running
from exabox.agent.WorkerManager import workermanager_running

from exabox.proxy.router import Router
from exabox.proxy.ebProxyJobRequest import ebProxyJobRequest
from exabox.agent.AuthenticationStorage import ebGetHTTPAuthStorage
from six.moves.urllib.parse import urlencode
from exabox.config.Config import ebCluCmdCheckOptions
from exabox.agent.ProxyClient import ProxyClient, ProxyOperation
from exabox.infrapatching.core.infrapatcherror import PATCH_SUCCESS_EXIT_CODE
import exabox.network.HTTPSHelper as HTTPSHelper
from exabox.network.ExaHTTPSServer import ExaHTTPSServer, ExaHTTPRequestHandler
from exabox.infrapatching.utils.utility import mPopulateDispatcherErrorForInfraPatch, isInfrapatchErrorCode, mCheckInfraPatchConfigOptionExists, mCheckDispatcherErrorCode
from exabox.ovm.opctlMgr import ExaCloudWrapper
from exabox.agent.HTTPSignatureVerification import insertRestrictedEndpointsInformation
from exabox.tools.Utils import mBackupFile
from exabox.utils.common import get_ecradb_details

ACCEPTED_DEVQA_DOMAINNAMES = ["us.oracle.com", "usdv1.oraclecloud.com", "oracle.local"]
API_ACL_ENABLED_REGIONS = ["ap-sydney-1", "sa-vinhedo-1", "mx-monterrey-1", "r1"]

gDefaultAgent   = None
gGlobalShutdown = False
gAgentConfig    = None
gAgentInfo      = None
gServerClass    = 'Undefined'
gHttpdServer    = None

GENERIC = "Generic"

class RouterManager(BaseManager):
    pass

RouterManager.register('routerObject', Router)


def ebGetDefaultAgent():
    global gDefaultAgent
    return gDefaultAgent

def ebSetDefaultAgent(aAgent):
    global gDefaultAgent
    gDefaultAgent = aAgent

def ebGetAgentConfig():
    global gAgentConfig
    return gAgentConfig

def ebGetAgentInfo():
    global gAgentInfo
    return gAgentInfo

def ebSetAgentInfo(aAgentInfo):
    global gAgentInfo
    gAgentInfo = aAgentInfo

def ebGetServerClass():
    global gServerClass
    return gServerClass

def ebSetServerClass(aValue):
    global gServerClass
    gServerClass = aValue

def ebGetHttpdServer():
    global gHttpdServer
    return gHttpdServer

def ebSetHttpdServer(aValue):
    global gHttpdServer
    gHttpdServer = aValue

def ebGetRequestObj(aUUID):
    global _reqobj
    _uuid = aUUID
    _db = ebGetDefaultDB()

    _reqobj = ebJobRequest(None, {}, aDB=_db)
    _reqobj.mLoadRequestFromDB(_uuid)
    return _reqobj
"""
JSON Response format and fields:

uuid      : Request Unique Identifier
status    : Done | Pending | Cancelled
success   : True | False
error     : int Code | 0 No Error
error_str : str Explanation string about the error | None No Error
output    : Body containing information about the execution of the request.
"""

class ebScheduleInfo(object):

    def __init__(self, aUUID, aDB=None):

        self.__uuid    = aUUID if aUUID else str(uuid.uuid1())
        self.__command = ''
        self.__mode = 'default'
        self.__operation = 'schedule'
        self.__event = ''
        self.__timertype = ''
        self.__schedTimestamp  = ''
        self.__interval = ''
        self.__repeatCount = '0'
        self.__lastrepeatCount = -1
        self.__monitorUUID = ''
        self.__monitorJobs = ''
        self.__status = 'Idle'
        self.__db      = aDB

    def mGetUUID(self):
        return self.__uuid

    def mSetUUID(self,aUUID=0):
        self.__uuid = aUUID

    def mGetScheduleCommand(self):
        return self.__command

    def mSetScheduleCommand(self, aCommand):
        self.__command = aCommand

    def mGetScheduleMode(self):
        return self.__mode

    def mSetScheduleMode(self, aMode):
        self.__mode = aMode

    def mGetScheduleOperation(self):
        return self.__operation

    def mSetScheduleOperation(self, aOperation):
        self.__operation = aOperation

    def mGetScheduleEvent(self):
        return self.__event

    def mSetScheduleEvent(self, aEvent):
        self.__event = aEvent

    def mGetScheduleTimerType(self):
        return self.__timertype

    def mSetScheduleTimerType(self, aType):
        self.__timertype = aType

    def mGetScheduleTimestamp(self):
        return self.__schedTimestamp

    def mSetScheduleTimestamp(self, aTime):
        self.__schedTimestamp = aTime

    def mGetScheduleInterval(self):
        return self.__interval

    def mSetScheduleInterval(self, aInterval):
        self.__interval = aInterval

    def mGetScheduleRepeatCount(self):
        return self.__repeatCount

    def mSetScheduleRepeatCount(self, aCount):
        self.__repeatCount = aCount

    def mGetScheduleLastRepeatCount(self):
        return self.__lastrepeatCount

    def mSetScheduleLastRepeatCount(self, aCount):
        self.__lastrepeatCount = aCount

    def mGetScheduleMonitorUUID(self):
        return self.__monitorUUID

    def mSetScheduleMonitorUUID(self, aUUID):
        self.__monitorUUID = aUUID

    def mGetScheduleMonitorWorkerJobs(self):
        return self.__monitorJobs

    def mSetScheduleMonitorWorkerJobs(self, aJobType):
        self.__monitorJobs = aJobType

    def mGetScheduleStatus(self):
        return self.__status

    def mSetScheduleStatus(self, aStatus):
        self.__status = aStatus

    def mLoadScheduleTaskFromDB(self, aUUID=0):

        _req = self.__db.mGetScheduleByType(aUUID)
        self.mPopulate(_req)

    def mRegister(self):
        # Register the Request with the DB
        self.__db.mInsertNewSchedule(self)

    def mPopulate(self, aReq):

        _req = aReq
        if _req:
            self.mSetUUID(_req[0])
            self.mSetScheduleCommand(_req[1])
            self.mSetScheduleMode(_req[2])
            self.mSetScheduleOperation(_req[3])
            self.mSetScheduleEvent(_req[4])
            self.mSetScheduleTimerType(_req[5])
            self.mSetScheduleTimestamp(_req[6])
            self.mSetScheduleInterval(_req[7])
            self.mSetScheduleRepeatCount(_req[8])
            self.mSetScheduleLastRepeatCount(_req[9])
            self.mSetScheduleMonitorUUID(_req[10])
            self.mSetScheduleMonitorWorkerJobs(_req[11])
            self.mSetScheduleStatus(_req[12])

def agent_status(aReqCtx, *args, **kwargs):
    pass

def agent_test(aParams, aResponse): #--/Test JSONResponse

    _response = aResponse
    _response['status'] = 'Done'
    _response['success'] = 'True'
    _response['output'] = str(aParams)

class ebAgentInfo(object):

    def __init__(self,aUUID=0):

        self.__uuid     = aUUID
        self.__status   = 'stopped'
        self.__pid      = os.getpid()
        self.__hostname = socket.getfqdn()
        self.__port     = 0
        self.__ttstart  = time.strftime("%c")
        self.__ttstop   = None
        self.__misc     = "{}"
        self.__db       = ebGetDefaultDB()

    def mGetStatus(self):
        return self.__status

    def mGetUUID(self):
        return self.__uuid

    def mGetPid(self):
        return self.__pid

    def mGetPort(self):
        return self.__port

    def mGetHostname(self):
        return self.__hostname

    def mGetStartTime(self):
        return self.__ttstart

    def mGetEndTime(self):
        return self.__ttstop

    def mGetMisc(self):
        return self.__misc

    def mSetStatus(self,aStatus):
        self.__status =  aStatus

    def mSetUUID(self,aUUID=0):
        self.__uuid = aUUID

    def mSetPid(self,aPid):
        self.__pid = aPid

    def mSetPort(self,aPort):
        self.__port = aPort

    def mSetHostname(self,aHostname):
        self.__hostname = aHostname

    def mSetStartTime(self,aStartTime):
        self.__ttstart = aStartTime

    def mSetEndTime(self,aEndTime):
        self.__ttstop = aEndTime

    def mSetMisc(self,aMisc):
        self.__misc = aMisc

    def mLoadAgentFromDB(self, aUUID=0):

        _req = self.__db.mAgentStatus(aUUID)
        self.mPopulate(_req)

    def mPopulate(self, aReq):

        _req = aReq
        if _req:
            self.mSetUUID(_req[0])
            self.mSetPid(_req[1])
            self.mSetStatus(_req[2])
            self.mSetStartTime(_req[3])
            self.mSetEndTime(_req[4])
            self.mSetHostname(_req[5])
            self.mSetPort(_req[6])
            self.mSetMisc(_req[7])

def incident_file_process(ex, aJobRequest, aCluCtrl, step=None):

    if type(ex) == type(ExacloudRuntimeError()) and ebCluCmdCheckOptions(aJobRequest.mGetCmd(), ['incident_cmds']):

        destdir = get_gcontext().mGetOEDAPath() +'/requests/'+ aCluCtrl.mGetExaunitID() + '_' + aJobRequest.mGetUUID()
        _ecopt = get_gcontext().mGetConfigOptions()
        _options = get_gcontext().mGetArgsOptions()
        if 'diag_level' in list(_ecopt.keys()) and (_ecopt['diag_level'] in ["Verbose", "Normal", "None"]) :
            lvl = _ecopt['diag_level']
        else:
            lvl = "None"

        dgStep, dgDo = ex.mGetContext()
        if not dgStep and step:
            dgStep = step.strip(".")
        dgOp = aJobRequest.mGetCmd()
        dgNode = ebIncidentNode(lvl, destdir, aJobRequest.mGetUUID(), aCluCtrl, _options, dgStep, dgDo, dgOp)

        return dgNode.process()

    return None

def lockseg_handler(signum, frame):
    try:
        ebRestHttpListener.plock.release()
    except ValueError:
        ebLogWarn('Log already released')
    sys.exit(1)

def obfuscate_passwd_entries(d):
    return maskSensitiveData(d, use_mask=False)

#Deep clones an ordered ReadOnlyDict into a regular dict (internal tuples are converted into lists).
#ReadOnlyDicts cannot be serialized. This function is useful for serializing them into JSON.
def unorderDict(d):

    ud = {}
    for key in list(d.keys()):
        if isinstance(d[key], ReadOnlyDict):
            ud[key] = unorderDict(d[key]) #ordered dict becomes regular dict
        elif isinstance(d[key], tuple):
            ud[key] = list(d[key]) #tuple becomes list
        else:
            ud[key] = d[key] #strings stay strings

    return ud

def isAdditionalWorkerAllowed(_disable_cpu_mem_threshold, _cpu_threshold, _mem_threshold):
    if _disable_cpu_mem_threshold:
        return True

    _db = ebGetDefaultDB()
    _cpu_percent, _mem_percent, _last_update_time = _db.mSelectAllFromEnvironmentResourceDetails()
    ebLogInfo(f"Environment resource statistics, CPU: {_cpu_percent}, Memory: {_mem_percent}.")
    if _cpu_percent == None or _mem_percent == None:
        ebLogWarn(f"Invalid resource statistics.")
        return True
    else:
        if float(_cpu_percent) > _cpu_threshold or float(_mem_percent) > _mem_threshold:
            ebLogWarn(f"Environment utilisation threshold exceeded. No additional worker will be created if all workers are busy.")
            return False
        else:
            return True

def buildErrorResponseForRequest(aRequestHandler, aResponseObj):
    _str = "Failed to allocate exacloud worker for the current operation."
    JSONResponse().WriteResponse(aRequestHandler, ErrorBuilder.response(503,_str,aResponseObj))

def dispatchJobToWorker(aReq, _workerLock=None):
    #
    # Worker invocation WIP
    #

    _coptions = get_gcontext().mGetConfigOptions()
    if 'agent_debug' in list(_coptions.keys()) and _coptions['agent_debug'].upper() == 'TRUE':
        _debug = True
    else:
        _debug = False

    _disable_cpu_mem_threshold = False
    _cpu_threshold = 80.0
    _mem_threshold = 80.0

    if 'disable_cpumem_threshold' in list(_coptions.keys()) and _coptions['disable_cpumem_threshold'].upper() == 'TRUE':
        _disable_cpu_mem_threshold = True

    if 'cpu_threshold' in list(_coptions.keys()):
        _cpu_threshold = float(_coptions['cpu_threshold'])

    if 'mem_threshold' in list(_coptions.keys()):
        _mem_threshold = float(_coptions['mem_threshold'])

    _create_new_worker = isAdditionalWorkerAllowed(_disable_cpu_mem_threshold, _cpu_threshold, _mem_threshold)
    _worker_assigned = False
    _assigned_worker_obj = None
    _db = ebGetDefaultDB()

    if 'agent_delegation_enabled' in list(_coptions.keys()) and _coptions['agent_delegation_enabled'].upper() == 'TRUE':
        _uuid = '00000000-0000-0000-0000-000000000000'
        _idle_worker = 0
        _rqlist = literal_eval(_db.mDumpWorkers())
        for _worker in _rqlist:
            if _worker[0] == _uuid and _worker[1] == 'Idle' and _worker[13] == "NORMAL":
                _idle_worker = _idle_worker + 1

        if _idle_worker == 0 and _create_new_worker is False:
            if 'accept_req_during_cpumem_threshold_breach' in list(_coptions.keys()) and _coptions['accept_req_during_cpumem_threshold_breach'].upper() == 'TRUE':
                #Lets queue the requests within exacloud, instead of returning back with http 503 error.
                #exacloud will dispatch the job, when an idle worker is available.
                ebLogInfo(f'Cpu/Mem threshold breached. But, will accept request {aReq.mGetUUID()}. Req will be served when system utilization comes back to normal ! ')
                return True
            else:
                #Unable to serve the request due to resource constraints. http 503 error will be returned.
                #This will prompt ecra to keep polling exacloud with system_metrics endpoint.
                #Ecra will then do a retry when system gets better.
                ebLogError(f'*** dispatchJobToWorker: Unable to serve uuid {aReq.mGetUUID()} due to resource constraints. http 503 error will be returned.')
                return False

        #Job dispatching will be done by dispatcher process.
        return True


    try:
        signal.signal(signal.SIGSEGV, lockseg_handler)
    except ValueError:
        if _debug:
            ebLogDebug('signal.SIGSEGV' + str(os.getpid()) + str(threading.current_thread().ident))

    ebLogInfo("UUID {0} on process {1} trying for a lock.".format(aReq.mGetUUID(), os.getpid()))
    _workerLock.acquire()
    ebLogInfo("UUID {0} on process {1} acquired the lock on: {2}.".format(aReq.mGetUUID(), os.getpid(), _workerLock))

    try:
        while _worker_assigned is False:
            _uuid = '00000000-0000-0000-0000-000000000000'
            _port = 0
            _pid = 0
            _idleworkers = literal_eval(_db.mDumpWorkers())
            _random_idle_workers = random.sample(_idleworkers, k = len(_idleworkers))
            for _worker in _random_idle_workers:
                if _worker[0] == _uuid and _worker[1] == 'Idle' and _worker[13] == "NORMAL":
                    _thisWorker = ebWorker()
                    _thisWorker.mLoadWorkerFromDB(int(_worker[9]))
                    if _thisWorker.mAcquireSyncLock("Agent"):
                        _port = _worker[9]
                        _pid = _worker[8]
                        break
            # Check if process is alive. Else, we start a new worker
            if _pid:
                try:
                    os.kill(int(_pid),0)
                except OSError as err:
                    if err.errno == 3:
                        ebLogWarn('*** Worker DB inconsistency detected. Worker PID (%d) but no corresponding process is running' % (int(_pid)))
                        # We cleanup DB entry but don't bother about port clean-up here.
                        _worker = ebWorker()
                        _worker.mLoadWorkerFromDB(_port)
                        _worker.mDeregister()
                        ebLogWarn('*** [WF] De-Register Worker for PID/Port (%s/%s)' % (_pid, _port))
                        _pid = 0
                    elif err.errno == 1:
                        ebLogWarn('*** Worker permission issue. Worker PID (%d) exists but is running as a different process/user' % (int(_pid)))

            if (_port == 0 or _pid == 0) and _create_new_worker is False:
                ebLogWarn(f"Request dispatch to worker failed due to system resource utlisation threshold exceeded.")
                break

            if (_port == 0 or _pid == 0):
                ebLogError('*** No available worker found - starting additional worker(s)')
                # TODO: Pass workerFactory from AgentDaemon as parameter to ebRestHttpListener
                _wf = gGetDefaultWorkerFactory()
                _wf.mStartWorkers(aWorkerCount=1)
            else:
                _worker = ebWorker()
                ebLogInfo('*** LOADING WORKER: %s' % (str(_worker.mLoadWorkerFromDB(int(_port)))))
                _worker.mSetUUID(aReq.mGetUUID())
                _worker.mUpdateDB()
                ebLogInfo(f"Request with UUID: {aReq.mGetUUID()} is allocated to worker with port {_db.mGetWorkerPortByUUID(aReq.mGetUUID())}.")
                _worker_assigned = True
                _assigned_worker_obj = _worker
    except:
        ebLogError("*** Exception occured while dispatching request {0} to a worker.".format(aReq.mGetUUID()))
    finally:
        if _worker_assigned is True and _assigned_worker_obj is not None:
            _assigned_worker_obj.mReleaseSyncLock("Agent")
        _workerLock.release()
        ebLogInfo("UUID {0} on process {1} released the lock on: {2}.".format(aReq.mGetUUID(), os.getpid(), _workerLock))

    if _worker_assigned is False:
        return False
    return True


class ebRestHttpListener(ExaHTTPRequestHandler):

    plock = Lock()

    def __init__(self, aConfig, aRouterInstance=None, aLock=None, *args):

        self.__cache   = {}
        self.__context = get_gcontext()
        self.__options = self.__context.mGetArgsOptions()
        self.__config = aConfig
        self.__shutdown = False
        self.__routerInstance = aRouterInstance
        self.__workerlock = aLock
        self.__db = ebGetDefaultDB()

        # Define more complex callbacks with pre/post process
        if self.__routerInstance is not None:
            ebLogAgent('NFO', 'Router Instance being used: %s ' % (str(self.__routerInstance)))

        _clu_ociUpdateRegion_cb = HttpCb(
            {
                "GET"  : self.mOCIRegionUpdater,
                "POST" : MethodWrapper(
                    self.mOCIRegionUpdater,
                    preprocess=[ConvertHttpHeaderToParam('StatusQueue', 'aq_name')]
                )
            },
            JSONResponse
        )

        _clu_xmlgen_cb = HttpCb(
            {
                "GET"  : self.mXmlGeneration,
                "POST" : MethodWrapper(
                    self.mXmlGeneration,
                    preprocess=[ConvertHttpHeaderToParam('StatusQueue', 'aq_name')]
                )
            },
            JSONResponse
        )

        _clu_request_cb = HttpCb(
            {
                "GET"  : self.mCLURequest,
                "POST" : MethodWrapper(
                    self.mCLURequest,
                    preprocess = [
                        ConvertPathToParam("cmd"),
                        DecodeBase64("configpath", deflate=True),
                        DecodeBase64Policy(),
                        ConvertHttpHeaderToParam('StatusQueue', 'aq_name')
                    ]
                )
            },
            JSONResponse
        )

        _json_dispatch_cb = HttpCb(
            {
                "GET": self.mJsonDispatchRequest,
                "POST": MethodWrapper(
                    self.mJsonDispatchRequest,
                    preprocess = [
                        ConvertPathToParam("cmd"),
                        ConvertHttpHeaderToParam('StatusQueue', 'aq_name')
                    ]
                )
            },
            JSONResponse
        )

        _sc_generic_request_cb = HttpCb(
            {
                "GET"  : self.mScheduleGenericRequest,
                "POST" : MethodWrapper(
                    self.mScheduleGenericRequest,
                    preprocess = [
                        ConvertPathToParam("cmd"),
                        ConvertHttpHeaderToParam('StatusQueue', 'aq_name')
                    ]
                )
            },
            JSONResponse
        )

        _status_request_cb = self.mGetStatusCallback()

        _ui_serve_cb = HttpCb(
            {
                "GET" : MethodWrapper(
                    self.mServeUI,
                    preprocess = [GetPathForIndex("path")]
                )
            },
            HTMLResponse,
            aAuthenticated = False #no Auth for UI serving function (/ , /css, /js)
        )

        _ociexacc_log_cb = HttpCb(
            {
                "GET" : MethodWrapper(
                    self.mAgentFetchLog,
                    preprocess=[ConvertPathToParam("jobid")]
                )
            },
            FileResponse
        )

        _worker_status_cb = HttpCb(
            {
                "GET" : MethodWrapper(
                    self.mWorkerStatus,
                    preprocess=[ConvertHttpHeaderToParam('Authorization', 'req_auth_header')]
                )
            },
            JSONResponse
        )

        _edv_request_cb = HttpCb(
            {
                "GET": self.mEDVManagement,
                "POST": MethodWrapper(
                    self.mEDVManagement,
                    preprocess=[
                        ConvertPathToParam("cmd"),
                        ConvertHttpHeaderToParam('StatusQueue', 'aq_name')
                    ]
                )
            },
            JSONResponse
        )

        _sop_request_cb = HttpCb(
            {
                "POST": MethodWrapper(
                    self.mProcessSOPRequest,
                    preprocess=[ConvertHttpHeaderToParam('StatusQueue', 'aq_name')]
                )
            },
            JSONResponse
        )

        _nwfetch_request_cb = HttpCb(
            {
                "POST": MethodWrapper(
                    self.mFetchNetworkInfoRequest,
                    preprocess=[ConvertHttpHeaderToParam('StatusQueue', 'aq_name')]
                )
            },
            JSONResponse
        )

        _exakms_request_cb = HttpCb(
            {
                "POST": MethodWrapper(
                    self.mExaKmsRequest,
                    preprocess=[ConvertHttpHeaderToParam('StatusQueue', 'aq_name')]
                )
            },
            JSONResponse
        )

        _bmc_request_cb = HttpCb(
            {
                "POST": MethodWrapper(
                    self.mBMRequest,
                    preprocess=[ConvertHttpHeaderToParam('StatusQueue', 'aq_name')]
                )
            },
            JSONResponse
        )

        # Define a callback function for every endpoint

        self.__callbacks = {
            "/sop"          : _sop_request_cb,
            "/network_info" : _nwfetch_request_cb,
            "/OCIExaCCLog"  : _ociexacc_log_cb,       #GET,      self.mAgentFetchLog,          FileResponse
            "/WorkerStatus" : _worker_status_cb,      #GET,      self.mWorkerStatus,           JSONResponse
            "/Status"       : _status_request_cb,     #GET,      self.mShowStatus,             JSONResponse
            "/CLUCtrl"      : _clu_request_cb,        #GET+POST, self.mCLURequest,             JSONResponse
            "/CLUDiags"     : _clu_request_cb,        #GET+POST, self.mCLURequest,             JSONResponse
            "/Patch"        : _clu_request_cb,        #GET+POST, self.mCLURequest,             JSONResponse
            "/SCGENCtrl"    : _sc_generic_request_cb, #GET+POST, self.mScheduleGenericRequest, JSONResponse
            "/"             : _ui_serve_cb,           #GET,      self.mServeUI,                HTMLResponse #outputs HTML / CSS / JS / JSON / TXT / IMG / FONT, NO AUTH
            "/css"          : _ui_serve_cb,           #GET,      self.mServeUI,                HTMLResponse #outputs HTML / CSS / JS / JSON / TXT / IMG / FONT, NO AUTH
            "/js"           : _ui_serve_cb,           #GET,      self.mServeUI,                HTMLResponse #outputs HTML / CSS / JS / JSON / TXT / IMG / FONT, NO AUTH
            "/elastic_shapes" : _clu_xmlgen_cb,       #GET+POST, self.mXmlGeneration,          JSONResponse
            "/update_region": _clu_ociUpdateRegion_cb,#POST,     self.mOCIRegionUpdater,       JSONResponse
            "/jsondispatch" : _json_dispatch_cb,      #GET+POST, self.mJsonDispatchRequest,    JSONResponse
            "/exakms"       : _exakms_request_cb,
            "/BMCCtrl"      : _bmc_request_cb,
            "/Test"         : HttpCb({"GET"  : agent_test             }, JSONResponse),
            "/BMCCtrlLogs"  : HttpCb({"GET"  : self.mAgentOedaLogs    }, JSONResponse),
            "/OedaLogs"     : HttpCb({"GET"  : self.mAgentOedaLogs    }, JSONResponse),
            "/PatchLogs"    : HttpCb({"GET"  : self.mAgentOedaLogs    }, JSONResponse),
            "/AgentCluster" : HttpCb({"GET"  : self.mAgentCluster     }, JSONResponse),
            "/AgentCmd"     : HttpCb({"GET"  : self.mAgentCmdRequest  }, JSONResponse),
            "/AgentHome"    : HttpCb({"GET"  : self.mAgentHome        }, JSONResponse),
            "/AgentPortal"  : HttpCb({"GET"  : self.mAgentPortal      }, JSONResponse),
            "/AgentTest"    : HttpCb({"GET"  : self.mAgentTestPage    }, JSONResponse),
            "/AgentWorkers" : HttpCb({"GET"  : self.mAgentWorkers     }, JSONResponse),
            "/BDCSCmd"      : HttpCb({"GET"  : self.mBDSCmd           }, JSONResponse),
            "/BDCSInstall"  : HttpCb({"GET"  : self.mBDSInstall       }, JSONResponse),
            "/HardwareInfo" : HttpCb({"GET"  : self.mHardwareInfo     }, JSONResponse),
            "/Monitor"      : HttpCb({"GET"  : self.mMonitor          }, JSONResponse),
            "/OedaDiags"    : HttpCb({"GET"  : self.mAgentOedaDiags   }, JSONResponse),
            "/Version"      : HttpCb({"GET"  : self.mAgentVersion     }, JSONResponse),
            "/VMCtrl"       : HttpCb({"GET"  : self.mVMRequest        }, JSONResponse),
            "/AgentCtrl"    : HttpCb({"GET"  : self.mAgentRequest     }, HTMLResponse), #outputs JSON / XML / TXT
            "/AtpGetFile"   : HttpCb({"GET"  : self.mAtpGetFile       }, HTMLResponse), #outputs HTML / JSON / TXT / BIN
            "/WWW"          : HttpCb({"GET"  : self.mAgentWWWContent  }, HTMLResponse), #outputs HTML / CSS / JS / JSON / XML / TXT / JPG
            "/logDownload"  : HttpCb({"GET"  : self.mAgentLogDownload }, FileResponse),
            "/ecinstmaintenance" : HttpCb({"POST"  : self.mHandleECInstance     }, JSONResponse), # ecinst to proxy
            "/heartbeat"         : HttpCb({"GET"  : self.mHeartbeatECInstance     }, JSONResponse), # proxy to ecinst
            "/system_metrics"    : HttpCb({"GET"  : self.mReturnSystemResourceUsage     }, JSONResponse),
            "/EDV"          : _edv_request_cb
        }

        _coptions = get_gcontext().mGetConfigOptions()
        if 'disable_mserveui_endpoint' in list(_coptions.keys()) and _coptions['disable_mserveui_endpoint'].upper() == 'TRUE':
            ebLogAgent('DBG', 'Disabling support for UI retreival endpoint.')
            del self.__callbacks["/"]
            del self.__callbacks["/css"]
            del self.__callbacks["/js"]

        self.__validproxy_endpoints = [ "/ecinstmaintenance",
                                        "/WorkerStatus",
                                        "/AgentCmd",
                                        "/AgentHome",
                                        "/AgentTest",
                                        "/AgentWorkers",
                                        "/AgentCtrl",
                                        "/Version",
                                      ]

        if 'agent_debug' in list(_coptions.keys()) and _coptions['agent_debug'].upper() == 'TRUE':
            self.__debug = True
        else:
            self.__debug = False

        self.__mock_mode = False
        self.mRefreshMock(_coptions)

        if aConfig is not None:
            super().__init__(*args)

    def mGetStatusCallback(self, aAuthenticated=True):
        """
        Method to get the callback object for /Status call
        aAuthenticated - argument to enable authentication or not.
        For Http calls, aAuthenticated should always be True.
        For internal calls i.e. non http calls that do not require authentication,
        aAuthenticated can be set to False.
        """
        _status_request_cb = HttpCb(
            {
                "GET" : MethodWrapper(
                    self.mShowStatus,
                    preprocess  = [ConvertPathToParam("uuid")],
                    postprocess = [EncodeBase64("xml", deflate=True)]
                )
            },
            JSONResponse,
            aAuthenticated
        )
        return _status_request_cb

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

    def mGetMockMode(self):
        return self.__mock_mode

    def log_message(self, format, *args ):
        if self.__debug:
            ebLogAgent('NFO', format % args)
        else:
            _str = format % args
            _str = re.sub(r"jsonconf=.*?\?","jsonconf=sanitized?", _str)
            # agent.log should only contains this log AND DEBUG logs for
            # instant access
            ebLogAgent('NFO', _str)

    def do_JSON(self, aJResponse):

        _response = json.dumps(aJResponse, indent=4, separators=(',',': '))

        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Content-type',                 'application/json')

        self.end_headers()
        self.wfile.write(_response.encode('utf8'))
        self.wfile.write(b'\n\n')

    def mInShutdown(self):

        JSONResponse().WriteResponse(self,\
                      ErrorBuilder.response(503,'Rest Listener not available'))
        return

    def mValidateUUID(self, str_uuid):
        return re.match(r"[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}", str_uuid) is not None

    def mHandleRequest(self):

        if self.__shutdown:
            self.mInShutdown()
            return

        _url_parsed = urlparse(self.path)
        _fullpath   = _url_parsed[2]
        _endpoint   = '/' + _fullpath[1:].split('/')[0] # First level
        _response   = {}
        _method     = self.command
        _uuid_req_params = None

        # Reject invalid endpoints before parsing their params
        if not _endpoint in self.__callbacks:
            ErrorBuilder.response(404, 'Service {} not found'.format(_endpoint), _response)
            JSONResponse().WriteResponse(self, _response)
            return

        if self.__debug:
            ebLogAgent('NFO', 'PID: %s URL_P: %s' % (str(os.getpid()), str(_url_parsed)))

        # In forked mode close the child socket corresponding to the http listener socket
        # This is required to avoid race where the child could accept a connection when the http server is shutting down
        if ebGetServerClass() == 'forked':
            ebGetHttpdServer().socket.close()

        _httpreq = HttpRequest(_fullpath, _method, self.headers, self.requestline)    
        _httpreq.extractParams(self, _url_parsed[4])

        if self.__options.proxy and _endpoint not in self.__validproxy_endpoints:#When instance is proxy
            _req_uuid = None
            _endpoint = _endpoint[1:]
            if _endpoint == "Status":
                _split = _fullpath[1:].split('/')
                if len(_split) == 2:
                    _httpreq.setParam('uuid',_split[1])
            elif _endpoint == "CLUCtrl" or _endpoint == "CLUDiags" or _endpoint == "Patch" or _endpoint == "SCGENCtrl":
                _split = _fullpath[1:].split('/')
                if len(_split) == 2:
                    _httpreq.setParam('cmd',_split[1])

            if 'uuid' in _httpreq.getParams():
                _uuid_req_params = True
                _req_uuid = _httpreq.getParam('uuid')
            else:

                if 'operation_uuid' in _httpreq.getParams():
                    _p_uuid = _httpreq.getParam('operation_uuid')
                    if _p_uuid:
                        if not self.mValidateUUID(_p_uuid):
                            raise ExacloudRuntimeError(0x0810, 0xA, f"Invalid value for operation UUID: {_p_uuid}")
                        _db = ebGetDefaultDB()
                        if _db.mGetRequest(_p_uuid):
                            _req_uuid = str(uuid.uuid1())
                            ebLogInfo(f"Request already created: {_p_uuid} using {_req_uuid}")
                        else:
                            _uuid_req_params = True
                            _req_uuid = _p_uuid

                    else:
                        _req_uuid = str(uuid.uuid1())
                else:
                    _req_uuid = str(uuid.uuid1())

            _contentType = self.headers.get('content-type')
            _body = {}
            if _contentType == 'application/json':
                _bytesBody = _httpreq.getBody()
                _strBody = _bytesBody.decode('utf-8')
                _jsonBody = json.loads(_strBody)
                _body = _jsonBody
                if not _uuid_req_params:
                    _body["uuid"] = _req_uuid

            ebLogAgent('NFO', 'UUID: %s Endpoint: %s' % (str(_req_uuid), str(_endpoint)))

            if self.command == "POST":
                self.dispatchHTTPPostReqToWorker(_endpoint, self.path, _httpreq.getParams(), self.headers.items(), _body, _req_uuid)
            elif self.command == "GET":
                self.getResponseFromExacloud(_endpoint, self.path, _httpreq.getParams(), self.headers.items(), _req_uuid)
            else:
                self.sendInvalidCommandResponse()
            if gGlobalShutdown:
                self.__shutdown = True
            return

        if self.headers.get('StatusQueue', None) is None:
            self.headers['StatusQueue'] = "Undef"

        _callback = self.__callbacks[_endpoint]
        # Authentication is handled inside the callback Execution
        _response = _callback.executeRequest(_httpreq) #the method HTTPResponses.HttpCb.executeRequest is run here
        _callback.returnResponse(self, _response) #the method HTTPResponses.HttpCb.returnResponse is run here

        # if Daemon exited/stopped commit suicide
        if gGlobalShutdown:
            self.__shutdown = True

    def dispatchHTTPPostReqToWorker(self, aEndPoint, aUrlFullPath, aParams, aHeaders, aBody, aReqUUID):
        _endpoint = aEndPoint
        _urlFullPath = aUrlFullPath
        _headers = aHeaders
        _body = aBody
        _req_uuid = aReqUUID

        _db = ebGetDefaultDB()
        _cmd = "None"
        try:
            _cmd = aParams['cmd']
        except:
            _cmd = "None"
        _req = ebProxyJobRequest(str(_endpoint).lower()+"."+_cmd, aParams, _db)
        _req.mSetUrlFullPath(_urlFullPath)
        _req.mSetUrlHeaders(_headers)
        _req.mSetReqBody(_body)
        _req.mSetReqType(_endpoint + '.POST')
        _req.mSetUUID(_req_uuid)
        _req.mRegister()
        ebLogInfo('POST request has been dispatched to the worker.')
        _echost, _ecport, _ecauthkey = self.__routerInstance.mGetECInstance(aRequestType= _endpoint)
        _ecInstanceID = str(_echost) + ":" + str(_ecport)
        self.__routerInstance.mUpdateUUIDToECInstance(_req_uuid, _ecinstid=_ecInstanceID)
        ebLogInfo('Request with UUID: {0} to be handled by exacloud instance: {1}.'.format(_req_uuid, _ecInstanceID))

        dispatchJobToWorker(_req, self.__workerlock)
        #
        # Prepare response
        #
        _response = {}
        _response['uuid'] = _req.mGetUUID()
        _response['status']  = 'Pending'
        _response['success'] = 'True'
        _response['body'] = [_req.mGetUUID(), 'Pending']
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
        self.end_headers()
        self.wfile.write(six.ensure_binary(json.dumps(_response)))

    def getResponseFromExacloud(self, aEndPoint, aUrlFullPath, aParams, aHeaders, aReqUUID):
        _endpoint = aEndPoint
        _urlFullPath = aUrlFullPath
        _headers = aHeaders
        _req_uuid = aReqUUID
        #Pass request to request analyzer and get the request type
        #Generate the exacloud request and get the response/ register-deregister the exacloud instance.
        #Send the response back to ECRA
        _cmd = "None"
        try:
            _cmd = aParams['cmd']
        except:
            _cmd = "None"

        if _endpoint == "Status":
            #Manage the status request. For Status calls there is no need to encode the uuid to params.
            #Load the request from the DB with the given uuid.
            #Modify the cmdtype and set it to Status.GET. Update the headers.
            _db = ebGetDefaultDB()
            _current_status = _db.mSelectStatusFromUUIDToECInstance(_req_uuid)
            if _current_status == "InitialReqPending":
                self.exaproxyWriteResponse(_req_uuid, sendMockPendingResponse=True, _cmdType=str(_endpoint).lower()+"."+_cmd, _params=aParams)
                return

            if _current_status == "InitialReqDone":#This means no worker has been assigned to poll for the status from exacloud.
                _worker_for_uuid = _db.mDumpWorkers(_req_uuid)
                if _worker_for_uuid != '()':
                    ebLogInfo("Worker has already been assigned for {0} status request. Sending mock pending response.".format(_req_uuid))
                    self.exaproxyWriteResponse(_req_uuid, sendMockPendingResponse=True, _cmdType=str(_endpoint).lower()+"."+_cmd, _params=aParams)
                    return
                _job = ebProxyJobRequest(None,{}, aDB=ebGetDefaultDB())
                _job.mLoadRequestFromDB(_req_uuid)
                _job.mSetUrlFullPath(_urlFullPath)
                _job.mSetReqType(_endpoint + '.GET') 
                _job.mSetUrlHeaders(_headers)
                _job.mSetRespCode(9999)
                _job.mSetRespBody('Undef')
                _db.mUpdateProxyRequest(_job)

                dispatchJobToWorker(_job, self.__workerlock)
                ebLogInfo('GET Status request has been dispatched to the worker.')
                self.exaproxyWriteResponse(_req_uuid, sendMockPendingResponse=True, _cmdType=str(_endpoint).lower()+"."+_cmd, _params=aParams)
            else:#When status is Done/Pending
                self.exaproxyWriteResponse(_req_uuid)
        else:
            ebLogWarn('Error: Request not accepted')
            ebLogError(traceback.format_exc())
            _response = ErrorBuilder.response(800,'Internal Server Error: Request not accepted')
            JSONResponse().WriteResponse(self, _response)

    def exaproxyWriteResponse(self, _reqUUID, sendMockPendingResponse=False, _cmdType=None, _params=None):

        if sendMockPendingResponse:
            _req = ebJobRequest(_cmdType, _params)
            _req.mSetUUID(_reqUUID)
            _response = {}
            _response['uuid'] = _req.mGetUUID()
            _response['status']  = 'Pending'
            _response['success'] = 'True'
            _response['body'] = _req.mUnpopulate()
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.send_header('Access-Control-Allow-Origin','*')
            self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS')
            self.end_headers()
            self.wfile.write(six.ensure_binary(json.dumps(_response)))
        else:
            _db = ebGetDefaultDB()
            _respData = _db.mSelectResponseDetailsFromProxyRequests(_reqUUID)
            _returnCode = int(_respData[0])
            _responseBody = _respData[1]
            _responseHeaders = str(_respData[2])

            self.send_response(_returnCode)
            _headers_dict = eval(_responseHeaders)
            for _hName, _hValue in _headers_dict.items():
                self.send_header(_hName,_hValue)
            self.end_headers()
            if _responseBody != 'Undef':
                self.wfile.write(six.ensure_binary(_responseBody))
                self.wfile.write(b'\n\n')




    def sendInvalidCommandResponse(self):
        self.send_response(404)
        self.end_headers()
        self.wfile.write(six.ensure_binary(self.command+" command type is currently not supported by exaproxy."))

    def mHandleRequestWrapper(self):
        try:
            self.mHandleRequest()
        except Exception as e:
            # This is to help in debugging unforeseen issues.
            ebLogWarn('Exception in handling request[%s]' % (e,))
            ebLogError(traceback.format_exc())
            _response = ErrorBuilder.response(500, f'Internal Server Error:\n\n\n\n{traceback.format_exc()}\n\n\n\n{e}')
            JSONResponse().WriteResponse(self, _response)

    def do_GET(self):
        self.mHandleRequestWrapper()
        return

    def do_POST(self):
        self.mHandleRequestWrapper()
        return

    def do_OPTIONS(self):
        self.mHandleRequestWrapper()
        return


    def mProcessSOPRequest(self, aParams, aResponse):#--------/sop/request JSONResponse
        ebLogInfo("Processing sop request.")
        _response = aResponse
        _err = False
        _str = None
        _valid_cmds = ["start", "delete", "scriptslist"]

        if not aParams or not len(list(aParams.keys())):
            _str = 'No Parameters provided'
            _err = True
        if not _err:
            if 'jsonconf' not in list(aParams.keys()):
                ErrorBuilder.response(800,'JSON input file not specified',_response)
                return
            _json_conf = aParams.get('jsonconf')
            if type(_json_conf) is not dict:
                ErrorBuilder.response(800,'Input payload file is not of type dictionary',_response)
                return
            _list_of_keys = _json_conf.keys()
            if "cmd" not in _list_of_keys or "scriptname" not in _list_of_keys:
                ErrorBuilder.response(800,'Input payload does not contain all(cmd,scriptname) mandatory information.',_response)
                return
            _cmd = _json_conf["cmd"]
            if _cmd not in _valid_cmds:
                ErrorBuilder.response(800,f"Command type {_cmd} is not supported for /sop endpoint.",_response)
                return
        else:
            ErrorBuilder.response(800,"No params provided. Please include the json payload required for processing.",_response)
            return

        # Create Job and New DB entry
        _req = ebJobRequest(f"sop.{_cmd}", aParams, aDB=ebGetDefaultDB())
        _req.mRegister()
        ebLogInfo('Posted the job for worker to pickup')

        if not dispatchJobToWorker(_req, self.__workerlock):
            buildErrorResponseForRequest(self, _response)
            return

        _response['uuid'] = _req.mGetUUID()
        _response['status']  = 'Pending'
        _response['success'] = 'True'
        return

    def mReturnSystemResourceUsage(self, aParams, aResponse): #--------/system_metrics JSONResponse
        _db = ebGetDefaultDB()
        _cpu_utilisation, _mem_utilisation, _ = _db.mSelectAllFromEnvironmentResourceDetails()
        if _cpu_utilisation is None:
            _cpu_utilisation = 0
        if _mem_utilisation is None:
            _mem_utilisation = 0
        _idle_workers = _db.mGetNumberOfIdleWorkers()

        _return_json = {"CPU Usage": _cpu_utilisation, "Memory Usage": _mem_utilisation, "Free Workers": _idle_workers}
        _response = aResponse
        _response['system_metrics'] = json.dumps(_return_json)

    def mShowStatus(self, aParams, aResponse): #--------/Status JSONResponse
        self.mRefreshMock(aParams)
        if self.__mock_mode:
            MockStatus(self, aParams, aResponse)
            return

        _db = ebGetDefaultDB()
        _response = aResponse
        error_code = ""
        error_message = ""
        _patch_child_error_detail = False
        _step_progress_details = None
        _step_status = {"stepProgressDetails": {}}
        _step_status["stepProgressDetails"] = {"message": "Step is in progress",
                                               "completedNodes": [],
                                               "stepSpecificDetails": {},
                                               "percent_complete": 0,
                                               "status": "InProgress"}

        if not aParams or not len(list(aParams.keys())) or not 'uuid' in list(aParams.keys()):
            _body = _db.mDumpRequests()
            _response['body'] = _body
            ErrorBuilder.response(400,'Missing parameters or UUID',_response)
        else:
            _body = _db.mGetRequest(aParams['uuid'])
            if _body is None:
                ebLogWarn('*** Invalid UUID: %s' %(aParams['uuid']))
                _response['uuid']      = aParams['uuid']
                ErrorBuilder.response(404,'Unknown UUID request', _response)
            else:
                if len(_body) >= 5:
                    cmd_type = _body[4]
                    if cmd_type and "opctl_cmd" in cmd_type and not get_gcontext().mCheckConfigOption('ociexacc', True):
                        _response = self.mCheckOpctlStatus(_body, aParams, _db, _response)

                _response["stepProgressDetails"] = _step_status["stepProgressDetails"]
                _current_job = ebJobRequest(None, {}, aDB=_db)
                _current_job.mLoadRequestFromDB(aParams['uuid'])
                is_patching_operation = False

                # Get PatchData
                _patch_list = {}
                _dispatcher_error_found = False
                
                #Check if dispatcher has an error code . Then throw this error
                error_code = _body[6]
                error_message = _body[7]
                error_detail = None
                _cmdType = _body[4]
                # For single thread operation with cmdtype = cluctrl.infra_patch_operation , no concept of dispatcher error since there is only one thread
                if (mCheckInfraPatchConfigOptionExists('patching_commands', _cmdType)):
                    is_patching_operation = True
                    #Typical Example: 2023-11-25 08:53:52+0000:LOG:Dispatcher Error found . Error Code  : 709 Error Message : Critical Exception caught aborting request.
                    #No need to populate infrapatching dispatcher error in the above case
                    if error_code and error_code not in ['0', 'Undef', '709', '701-614', '703-614', PATCH_SUCCESS_EXIT_CODE ] and len(error_message) > 0 and error_message not in ['Undef','No Errors'] :
                        #For Dispatcher Error , error is populated in the requests table . So no need to query patchlist table
                        _json_patch_report = None
                        #This marks response as Failure below for status to show as failed. _body[13] is the data field in the Exacloud requests table
                        _request_data = _body[13]
                        if _request_data and _request_data != 'Undef' and isInfrapatchErrorCode(error_code) and mCheckDispatcherErrorCode(_request_data, error_code):
                            ebLogInfo("Dispatcher Error found . Error Code  : %s Error Message : %s." % (error_code, error_message))
                            _dispatcher_error_found = True
                            _json_patch_report = mPopulateDispatcherErrorForInfraPatch(_body[4], aParams['uuid'], error_code, error_message, aRequestDataJson= _request_data)
                        if _json_patch_report:
                            _patch_list[aParams['uuid']] = {'status': 'Done', 'report': _json_patch_report}
                    #End of dispatcher error code check

                _request_data = _body[13]
                if "stepProgressDetails" in _request_data:
                    _step_progress_details = json.loads(_request_data)
                    _response["stepProgressDetails"] = _step_progress_details["stepProgressDetails"]

                if _dispatcher_error_found is False:
                    _patch_rows = _db.mGetChildRequestsList(aParams['uuid'])
                    _master_found = False

                    for _row in _patch_rows:
                        _master_found = True

                        '''
                         Enh 31925002 : This code takes care of integrating 
                         exacloud error with ECRA error for infrapatching with 
                         respect to the new error code project
                        '''
                        try:
                            '''
                              Any eblogInfo message in Agent will be printed in
                              "exacloud/log/workers/agent_<number>.log" like
                              exacloud/log/workers/agent_7260_139723829024576.log
                            '''
                            _json_patch_report = json.loads(_row[2])
                            ebLogInfo('AGENT json_report %s' % _json_patch_report)
                            if _json_patch_report:
                                _json_patch_report_data = _json_patch_report["data"]
                                if _json_patch_report_data:
                                    ebLogInfo('AGENT json_report_data %s' % _json_patch_report_data)
                                    #Handle the case in case error_code and error_message is not present in patch report
                                    error_code = _json_patch_report_data["error_code"]
                                    error_message = _json_patch_report_data["error_message"]
                                    error_detail = _json_patch_report_data["error_detail"]
                                    if error_code:
                                        ebLogInfo("Agent - Infra Patching Status Code is : %s " % (error_code))
                                    if error_message:
                                        ebLogInfo("Agent - Infra Patching Status Message is : %s " % (error_message))
                                    #Populate Error detail only if there is an error
                                    if error_detail and error_code not in ['0', 'Undef', '701-614', '703-614', PATCH_SUCCESS_EXIT_CODE]:
                                        _patch_child_error_detail = True
                                        ebLogInfo("Agent - Infra Patching Error Detail is : %s " % (error_detail))
                                else:
                                    ebLogInfo('AGENT patch json_report_data is not present yet in the patch list output')

                        except KeyError as k:
                            ebLogInfo('in KeyError: AGENT json_report error code is not populated')
                        except Exception as e:
                            ebLogInfo('in Exception: AGENT json_report fetch exception %s ' % str(e))
                            _json_patch_report = {}

                        _patch_list[str(_row[0])] = {'status': str(_row[1]),
                                                 'report': _json_patch_report}

                    if not _master_found:
                        _row  = _db.mGetPatchChildRequest(aParams['uuid'])
                        if _row:
                            try:
                                _json_patch_report = literal_eval(_row[1])
                            except:
                                _json_patch_report = {}
                            _patch_list = {'status': str(_row[0]),
                                       'report': _json_patch_report}

                #
                # Process outgoing json
                #
                _new_protocol = aParams.get('frompath_uuid',False)

                _nbody = list(_body)
                _nbody.append(_patch_list)
                if _patch_child_error_detail:
                    #Set error detail for patch requests in error case only
                    ebLogInfo('AGENT Set patch error detail for infra patch in error_str')
                    _nbody[7] = error_detail

                if _new_protocol:
                    _nbody[8] = "" # Do not return full log anymore
                    _xml = _nbody[9]
                    _nbody[9] = ""
                    if (_nbody[1] == "Done"):
                        _response['xml'] = _xml # Will be base64encoded
                if _body[1] == "Done" and _cmdType == "cluctrl.update_ntp_dns":
                    _response['xml'] = _body[9]
                _params = literal_eval(_nbody[5])
                if isinstance(_params,dict):
                    if _new_protocol and 'configpath' in _params:
                        del _params['configpath']
                    _params = json.dumps(_params)
                    _nbody[5] = _params
                _error_list = {}
                _errcode = list(_db.mGetErrCodeByUUID(aParams['uuid']))
                if len(_errcode) >= 6:
                    _error_list['errorCode'] = _errcode[1]
                    _error_list['errorMsg'] = _errcode[2]
                    _error_list['errorType'] = _errcode[3]
                    _error_list['retryCount'] = int(_errcode[4])
                    _error_list['detailErr'] = _errcode[5]
                    _response['errorObject'] = _error_list

                    _response_json = json.dumps(_response, indent=4, separators=(',',': '))
                    ebLogDebug('Response structure after adding errcode:%s'%(_response_json))

                #Checking for SE Linux violation for this request.
                if _db.mGetSELinuxViolationStatusForRequest(aParams['uuid']):
                    _current_error_message = _nbody[7]
                    _nbody[7] = "{} - SE Linux violations has also occured.".format(_current_error_message)
                _response['body'] = _nbody

                # Bug-26387175: For exadata image patching today the status of
                # 'No action required' (error codes 701-614 and 703-614) is
                # treated as failure and eventually PSM read it as fail. So,
                # we need to trap the error code '701-614 and 703-614' and
                # mark as success.
                
                if error_code and error_code not in ['0', 'Undef', '701-614', '703-614', PATCH_SUCCESS_EXIT_CODE]:
                    _response['success'] = 'False'
                else:
                    if _body[6] in ['0', 'Undef', '701-614', '703-614', PATCH_SUCCESS_EXIT_CODE ]:
                        _response['success'] = 'True'
                    else:
                        _response['success'] = 'False'

                _response["command"] = _cmdType
                if _body[1] == 'Done' and "step is in progress" in _response["stepProgressDetails"]["message"].lower():
                    _response["stepProgressDetails"]["message"] = "Step is completed"
                    _response["stepProgressDetails"]["status"] = "Completed"
                    _response["stepProgressDetails"]["percent_complete"] = 100
                # Removing sensitive customer data
                if _body[1] == 'Done' and not get_gcontext().mCheckConfigOption('keep_customer_data'):
                    _db.mClearCustomerData(aParams['uuid'])

                if not is_patching_operation:
                    _response['body_details'] = _current_job.mToDictForECRA()
 
        _response['status'] = 'Done'

    def mValidateNetworkInfoPayload(self, payload: dict) -> str:

        _required_information_list = ["interface", "information", "nodes"]
        for _required_information in _required_information_list:
            if _required_information not in list(payload.keys()):
                return f"Key: {_required_information} is missing from payload."

        #Additional validations of the values passed in the paylaod.
        _interface_value = payload['interface']
        if type(_interface_value) is not str:
            return f"Interface value is expected of type string but passed {type(_interface_value)}"

        _information_value = payload['information']
        if type(_information_value) is not list or len(_information_value) == 0:
            return f"Information value is either not of type list or empty list is passed in payload."

        _nodes_value = payload['nodes']
        if type(_nodes_value) is not list or len(_nodes_value) == 0:
            return f"Nodes value is either not of type list or empty list is passed in payload."

        return ""

    def mFetchNetworkInfoRequest(self, aParams, aResponse): #---------/network_info JSONResponse

        _response = aResponse
        if not aParams or len(list(aParams.keys())) == 0 or not 'jsonconf' in list(aParams.keys()):
            ErrorBuilder.response(801, "Network information payload missing.", _response)
            return

        _jconf = aParams['jsonconf']
        _validation_response = self.mValidateNetworkInfoPayload(_jconf)
        if _validation_response != "":
            ErrorBuilder.response(801, _validation_response, _response)
            return

        _information_value = _jconf['information']
        _str_information = '_'.join([str(_info) for _info in _information_value])
        _req = ebJobRequest('network_info.'+_str_information, aParams, aDB=ebGetDefaultDB())
        _req.mRegister()

        if not dispatchJobToWorker(_req, self.__workerlock):
            buildErrorResponseForRequest(self, _response)
            return
        #
        # Prepare response
        #
        _response = aResponse
        _response['uuid']    = _req.mGetUUID()
        _response['status']  = _req.mGetStatus()
        _response['success'] = 'True'


    def mBMRequest(self, aParams, aResponse): #---------/BMCCtrl JSONResponse
        ebLogInfo("in mBMRequest params are: %s" % (str(aParams),))
        _response = aResponse
        _err = False
        _str = None
        _valid_cmds = ['compose_cluster', 'add_customer_info']


        # Check if all Parameters are available
        if not aParams or not len(list(aParams.keys())):
            _str = 'No Parameters provided'
            _err = True
        if not _err:
            # Check if cmd is specified
            try:
                _cmd = aParams.get('cmd')
            except:
                _cmd = None
            if not _cmd:
                _str = 'Invalid request BMCCtrl command provided :'+str(_cmd)
                ErrorBuilder.response(801,_str,_response)
                return

            if _cmd not in _valid_cmds:
                _str = 'invalid BMCCTRL cmd specified: %s' % (_cmd,)
                _err = True

            if not 'jsonconf' in list(aParams.keys()):
                _str = 'JSON input file not specified'
                _err = True

            if _cmd == 'add_customer_info':
                if not 'xmlconfig' in list(aParams.keys()):
                    _str = 'Config XML file not specified'
                    _err = True
        if _err:
            ErrorBuilder.response(800,_str,_response)
            return
        # Create Job and New DB entry
        _req = ebJobRequest('bmcctrl.'+_cmd, aParams, aDB=ebGetDefaultDB())
        _req.mRegister()
        ebLogInfo('posted the job for worker to pickup')

        if not dispatchJobToWorker(_req, self.__workerlock):
            buildErrorResponseForRequest(self, _response)
            return

        #
        # Prepare response
        #
        _response['uuid'] = _req.mGetUUID()
        _response['status']  = 'Pending'
        _response['success'] = 'True'
        return

    def mUpdateScheduleInfo(self, aScheduleInfo, aStatus, aParams):

        _jconf = aParams['jsonconf']
        _reqobj = _jconf['scheduler_job']
        _sched_event = _reqobj['sc_events']
        _event_type = list(_sched_event.keys())[0]
        _ret = _sched_event[_event_type]

        _status = aStatus
        _sched_info = aScheduleInfo

        _sched_info.mSetScheduleCommand(_reqobj['command'])
        _sched_info.mSetScheduleOperation(_reqobj['operation'])

        if 'mode' in _reqobj:
            _sched_info.mSetScheduleMode(_reqobj['mode'])
        else:
             _sched_info.mSetScheduleMode('default')

        if _event_type == 'timer_job':
            _sched_info.mSetScheduleTimerType(_ret['timer_type'])
            _sched_info.mSetScheduleTimestamp(_ret['timestamp'])
            _sched_info.mSetScheduleInterval(_ret['interval'])
            if 'repeat_count' in _ret:
                _sched_info.mSetScheduleRepeatCount(_ret['repeat_count'])
        elif _event_type == 'follow_up_job':
            _sched_info.mSetScheduleMonitorUUID(_ret['monitor_uuid'])
        elif _event_type == 'no_active_jobs':
            _sched_info.mSetScheduleMonitorWorkerJobs(_ret['monitor_worker_jobs'])

        _sched_info.mSetScheduleEvent(_event_type)
        _sched_info.mSetScheduleStatus(_status)

        return _sched_info

    def mScheduleRequest(self, aReq, aParams):
        from exabox.agent.Scheduler  import scheduler_running

        _jconf = aParams['jsonconf']
        _ret = _jconf['scheduler_job']
        _req = aReq
        _db = ebGetDefaultDB()

        if _ret['operation'].lower() in ('schedule'):
            _sched_info = ebScheduleInfo(_req.mGetUUID(), aDB=ebGetDefaultDB())
            _sched_info = self.mUpdateScheduleInfo(_sched_info, 'Idle', aParams)
            _sched_info.mRegister()
        elif _ret['operation'].lower() in ('cancel', 'modify'):
            _sched_info = ebScheduleInfo(_ret['uuid'], aDB=ebGetDefaultDB())
            _sched_info = self.mUpdateScheduleInfo(_sched_info, 'Pending', aParams)
            _db.mUpdateSchedule(_sched_info)

            _pid = scheduler_running()
            os.kill(int(_pid), signal.SIGUSR1)

        return

    def mScheduleGenericRequest(self, aParams, aResponse): #--------/SCGENCtrl JSONResponse

        _response = aResponse
        _err = False

        _jconf = aParams['jsonconf'] if 'jsonconf' in aParams else None

        # Check if all Parameters are available
        if not aParams or not len(list(aParams.keys())):
            _str = 'No Parameters provided'
            _err = True

        if not _err:
            # Check if cmd is specified
            try:
                _cmd = aParams['cmd']
            except:
                _cmd = None
            if not _cmd:
                _str = 'Invalid request Schedule Generic Ctrl command provided :'+str(_cmd)
                ErrorBuilder.response(801,_str,_response)
                return

            if _jconf is not None and not ('scheduler_job' in list(_jconf.keys())):
                _str = 'scheduler_job not specified in json payload'
                _err = True

        if _err:
            ErrorBuilder.response(800,_str,_response)
            return

        # Create Job and New DB entry
        _req = ebJobRequest('genericctrl.'+_cmd, aParams, aDB=ebGetDefaultDB())
        _req.mRegister()

        if _jconf is not None and 'scheduler_job' in list(_jconf.keys()):
            self.mScheduleRequest(_req, aParams)
            #
            # Prepare response
            #
            _response = aResponse
            _response['uuid']    = _req.mGetUUID()

            if _jconf['scheduler_job']['operation'] in ('cancel', 'modify'):
                _db = ebGetDefaultDB()
                _req.mSetStatus('Done')
                _db.mUpdateRequest(_req)

                _response['status'] = 'Done'
            else:
                _response['status']  = _req.mGetStatus()
            _response['success'] = 'True'

            return

    def mCLURequest(self, aParams, aResponse): #--------/CLUCtrl /CLUDiags /Patch JSONResponse

        _response = aResponse
        _err = False
        _str = None
        _db = ebGetDefaultDB()
        _patchmgr_cmds = ['patchclu_apply']
        _single_worker_patchmgr_cmds = ['infra_patch_operation']
        _exempt_cmds = ['checkcluster', 'host_state']
        _diskgroup_cmds = ['diskgroup']
        _non_xml_cmds = ['validate_elastic_shapes','xsvault','infra_vm_states','xsput','xsget']

        # Check if all Parameters are available
        if not aParams or not len(list(aParams.keys())):
            _str = 'No Parameters provided'
            _err = True

        # Hostname where OEDA is supposed to be installed.
        # TODO: Check if it is installed locally
        if not _err and not 'hostname' in list(aParams.keys()):
            _str = 'Hostname required (e.g. dom0 or VM hostname)'
            _err = True

        if not _err:
            # Check if cmd is specified
            try:
                _cmd = aParams['cmd']
            except:
                _cmd = None
            if not _cmd:
                _str = 'Invalid request CluCtrl command provided :'+str(_cmd)
                ErrorBuilder.response(801,_str,_response)
                return


            if _cmd in _patchmgr_cmds:
                if not 'jsonconf' in list(aParams.keys()):
                    _str = 'JSON input file not specified'
                    _err = True
            elif _cmd in _single_worker_patchmgr_cmds:
                if not 'jsonconf' in list(aParams.keys()):
                    _str = 'JSON input file not specified'
                    _err = True
            elif _cmd in _diskgroup_cmds:
                if not 'jsonconf' in list(aParams.keys()):
                    _str = 'JSON input file not specified'
                    _err = True
                if not 'configpath' in list(aParams.keys()):
                    _str = 'Cluster XML config file not specified'
                    _err = True
            elif _cmd in _non_xml_cmds:
                if not 'jsonconf' in list(aParams.keys()):
                    _str = 'JSON input file not specified'
                    _err = True
            else:
                if (not 'configpath' in list(aParams.keys())) and not (_cmd in _exempt_cmds):
                    _str = 'Cluster XML config file not specified'
                    _err = True

        if _err:
            ErrorBuilder.response(800,_str,_response)
            return
        # Check if there is a pending request that can interfere with the current one
        # cmd such as create or delete vm, gi or db for a cluster can only be done in
        # serial fashion (e.g. one at a time). Use the exaunit id as key in the pending
        # operation/request table.

        # TODO: Implement this check !

        if self.__debug:
            ebLogAgent('NFO', f'* Request parameters (full):{(repr(aParams))}')
        else:
            _aparams_str = aParams
            _mask_params = maskSensitiveData((_aparams_str), use_mask=False)
            ebLogAgent('NFO', f'* Request parameters (sanitized): {_mask_params}')

        # TEMPORARY ATP FORCE MODE until ECRA changes are there
        _atp_force_from_agent = ebExaCCAtpSimulatePayload(aParams, _cmd)
        if _atp_force_from_agent.mIsATPSimulateEnabled():
            ebLogInfo('ATP Payload Injection enabled for cmd:{}'.format(_cmd))
            # ATP flag Y is injected if 'atp_force':'True' is set in exabox.conf
            _atp_force_from_agent.mInjectATPfromAgentWorkaround()

        # Create Job and New DB entry
        if _cmd in _patchmgr_cmds:
            _req = ebJobRequest('patch.'+_cmd, aParams, aDB=ebGetDefaultDB())

        #This case handles execution of infra patch operation in a single worker thread without spawning a  child worker thread
        elif _cmd in _single_worker_patchmgr_cmds:
            _jsonconf = aParams['jsonconf'] if 'jsonconf' in aParams else None
            if _jsonconf and 'Params' in _jsonconf.keys():
                for _params in _jsonconf['Params']:
                    if 'Operation' in _params:
                        _operation = (_params['Operation']).strip()
                        ebLogAgent('NFO', f'cmdtype persisted in Exacloud requests table for single worker incoming infrapatching operation {_cmd} is cluctrl.{_operation}')
                        _req = ebJobRequest('cluctrl.'+_operation, aParams, aDB=ebGetDefaultDB())
                        break
        else:
            _req = ebJobRequest('cluctrl.'+_cmd, aParams, aDB=ebGetDefaultDB())

        if "operation_uuid" in aParams:
            _req_uuid = aParams["operation_uuid"]
            if not self.mValidateUUID(_req_uuid):
                raise ExacloudRuntimeError(0x0810, 0xA, f"Invalid value for operation UUID: {_req_uuid}")
            if _db.mGetRequest(_req_uuid):
                ebLogInfo(f"Request already created: {_req_uuid} using {_req.mGetUUID()}")
            else:
                _req.mSetUUID(_req_uuid) 
        if self.__mock_mode:
            ebLogInfo("Request in MOCK mode")
            _mock = MockDispatcher(_req)
            _mock.mDispatchMock()

        _req.mRegister()

        _jconf = aParams['jsonconf'] if 'jsonconf' in aParams else None
        if _jconf is not None and 'scheduler_job' in list(_jconf.keys()):
            self.mScheduleRequest(_req, aParams)
            #
            # Prepare response
            #
            _response = aResponse
            _response['uuid']    = _req.mGetUUID()

            if _jconf['scheduler_job']['operation'] in ('cancel', 'modify'):
                _req.mSetStatus('Done')
                _db.mUpdateRequest(_req)

                _response['status'] = 'Done'
            else:
                _response['status']  = _req.mGetStatus()
            _response['success'] = 'True'

            return

        if not dispatchJobToWorker(_req, self.__workerlock):
            buildErrorResponseForRequest(self, _response)
            return
        #
        # Prepare response
        #
        _response = aResponse
        _response['uuid']    = _req.mGetUUID()
        _response['status']  = _req.mGetStatus()
        _response['success'] = 'True'

    def mJsonDispatchRequest(self, aParams, aResponse): #---------/jsondispatch JSONResponse
        _response = aResponse

        if not aParams:
            _str = 'No Parameters provided'
            ErrorBuilder.response(800, _str, _response)
            return

        if not 'cmd' in aParams:
            _str = 'No Cmd provided'
            ErrorBuilder.response(801, _str ,_response)
            return

        _cmd = aParams['cmd']

        if not 'jsonconf' in aParams:
            _str = "JSON configuration required"
            ErrorBuilder.response(800, _str, _response)
            return

        if "action" in aParams["jsonconf"]:
            _cmd = f"{_cmd}_{aParams['jsonconf']['action']}"

        # Create Job and New DB entry
        _req = ebJobRequest(f'jsondispatch.{_cmd}', aParams,
                            aDB=ebGetDefaultDB())
        _req.mRegister()

        dispatchJobToWorker(_req, self.__workerlock)

        _response['uuid']    = _req.mGetUUID()
        _response['status']  = _req.mGetStatus()
        _response['success'] = 'True'

    def mExaKmsRequest(self, aParams, aResponse): #---------/ExaKms JSONResponse

        _response = aResponse

        if not aParams or not len(list(aParams.keys())) or not 'cmd' in list(aParams.keys()):
            _str = 'Cmd required for this operation'
            ErrorBuilder.response(900,_str,_response)
            return

        _cmd = aParams['cmd']

        # Create Job and New DB entry
        _req = ebJobRequest(f'exakms.{_cmd}', aParams, aDB=ebGetDefaultDB())
        _req.mRegister()

        if not dispatchJobToWorker(_req, self.__workerlock):
            buildErrorResponseForRequest(self, _response)
            return

        ebLogInfo(_req.mToDict())

        _response = aResponse
        _response['uuid']    = _req.mGetUUID()
        _response['status']  = _req.mGetStatus()
        _response['success'] = 'True'

    def mOCIRegionUpdater(self, aParams, aResponse):
        '''
        Expected payload from ECRA
        {
            "urlmapping": [{
                    "realm": "R1_ENVIRONMENT",
                    "realmdomain": "oracleiaas.com",
                    "regionkey": "SEA",
                    "regionidentifier": "us-seattle-1"

                }
            ]
        }
        '''
        _response = aResponse
        _response['success'] = 'True'

    def mXmlGeneration(self, aParams, aResponse):

        _response = aResponse

        # Create Job and New DB entry
        _req = ebJobRequest('elastic_shape.xmlgen', aParams, aDB=ebGetDefaultDB())
        _req.mRegister()

        if not dispatchJobToWorker(_req, self.__workerlock):
            buildErrorResponseForRequest(self, _response)
            return

        ebLogInfo(_req.mToDict())

        _response = aResponse
        _response['uuid']    = _req.mGetUUID()
        _response['status']  = _req.mGetStatus()
        _response['success'] = 'True'

    def mEDVManagement(self, aParams, aResponse): #---------/EDV JSONResponse

        _response = aResponse
        if not aParams or not len(list(aParams.keys())) or not 'cmd' in list(aParams.keys()):
            _str = 'Cmd required for this operation'
            ErrorBuilder.response(900,_str,_response)
            return

        _cmd = aParams['cmd']

        # Create Job and New DB entry
        _req = ebJobRequest(f'edv.{_cmd}', aParams, aDB=ebGetDefaultDB())
        _req.mRegister()

        if not dispatchJobToWorker(_req, self.__workerlock):
            buildErrorResponseForRequest(self, _response)
            return

        ebLogInfo(_req.mToDict())

        _response['uuid']    = _req.mGetUUID()
        _response['status']  = _req.mGetStatus()
        _response['success'] = 'True'

    def mVMRequest(self, aParams, aResponse): #---------/VMCtrl JSONResponse

        _response = aResponse

        # Check if all Parameters are available
        if not aParams or not len(list(aParams.keys())) or not 'hostname' in list(aParams.keys()):
            _str = 'Hostname required (e.g. dom0 or VM hostname)'
            ErrorBuilder.response(900,_str,_response)
            return

        # Check if cmd is specified
        try:
            _cmd = aParams['cmd']
        except:
            _cmd = None
        if not _cmd:
            _str = 'Invalid request VMCtrl command provided :'+str(_cmd)
            ErrorBuilder.response(901,_str,_response)
            return

        if self.__debug:
            ebLogAgent('NFO', '* Request parameters (full): %s' % (repr(aParams)))
        else:
            _aparams_str = repr(aParams)
            _aparams_str = re.sub(r"jsonconf=.*?\?","jsonconf=sanitized?", _aparams_str)
            ebLogInfo('* Request parameters (sanitized): %s' % (_aparams_str))

        # Create Job and New DB entry
        _req = ebJobRequest('vmctrl.'+_cmd, aParams, aDB=ebGetDefaultDB())
        _req.mRegister()

        if not dispatchJobToWorker(_req, self.__workerlock):
            buildErrorResponseForRequest(self, _response)
            return

        _response = aResponse
        _response['uuid']    = _req.mGetUUID()
        _response['status']  = _req.mGetStatus()
        _response['success'] = 'True'

    def mMonitor(self, aParams, aResponse): #-----------/Monitor JSONResponse
        _response = aResponse
        _err = False
        _str = None
        _req = None

        # Check if cmd is specified
        try:
            _cmd = aParams['cmd']
        except:
            _cmd = None
        if not _cmd:
            _str = 'Invalid request Monitor command provided :'+str(_cmd)
            ErrorBuilder.response(801,_str,_response)
            return

        if _cmd == 'refresh':
            _db = ebGetDefaultDB()
            try:
                _wklist = literal_eval(_db.mDumpWorkers())
            except:
                ebLogError('*** DB access critical error please review DB integrity')
                raise

            for _entry in _wklist:
                if _entry[10] == 'monitor':
                    _worker = ebWorker()
                    _worker.mPopulate(_entry)
                    if _worker.mGetStatus() != 'Refreshing':
                        _worker.mSetStatus('Refreshing')
                        _worker.mUpdateDB()
                    break
        # Fallback is start monitor worker
        else:
            # Create Job and New DB entry
            _req = ebJobRequest('monitor.'+_cmd, aParams, aDB=ebGetDefaultDB())
            _req.mRegister()
            #
            # Worker invocation WIP - assume worker_pool is default and only available option
            #
            _worker_assigned = False
            while _worker_assigned is False:
                _uuid = '00000000-0000-0000-0000-000000000000'
                _port = 0
                _db = ebGetDefaultDB()
                _rqlist = literal_eval(_db.mDumpWorkers())
                for _worker in _rqlist:
                    if _worker[0] == _uuid and _worker[1] == 'Idle':
                        _port = _worker[9]
                        break
                if _port == 0:
                    ebLogError('*** A::Monitor::No available worker found - starting additional worker(s)')
                    # TODO: Pass workerFactory from AgentDaemon as parameter to ebRestHttpListener
                    _wf = gGetDefaultWorkerFactory()
                    _wf.mStartWorkers(aWorkerCount=1)
                    time.sleep(5)
                else:
                    _worker = ebWorker()
                    ebLogInfo('*** A::Monitor::LOADING WORKER: %s' % (str(_worker.mLoadWorkerFromDB(int(_port)))))
                    _worker.mSetUUID(_req.mGetUUID())
                    _worker.mUpdateDB()
                    ebLogInfo('*** A::Monitor::WORKER PORT (%d) UUID: %s' % (int(_worker.mGetPort()), _worker.mGetUUID()))
                    _worker_assigned = True
        #
        # Prepare response
        #
        if _req:
            _response['uuid']    = _req.mGetUUID()
            _response['status']  = _req.mGetStatus()
        _response['success'] = 'True'

    def mValidatePath(self, aPath):
        if '..' in aPath or '//' in aPath:
            return False
        return True

    def mAgentHome(self, aParams, aResponse): #---------/AgentHome JSONResponse

        _paramdict = {}

        _core = ebCoreContext()
        _ctx  = get_gcontext()

        _agentcfg = ebGetDefaultAgent().mAgent_Config()
        _key   = "Agent Hostname"
        _value = "%s:%d" % (_agentcfg[0],int(_agentcfg[1]))
        _paramdict[_key] = _value

        global gAgentInfo
        _key   = "Agent PID"
        _value = "%s" % (gAgentInfo.mGetPid())
        _paramdict[_key] = _value

        _key   = "Core Version"
        _value = "%s (%s)" % (_core.mGetVersion())
        _paramdict[_key] = _value

        _key   = "Start Time"
        _value = "%s (%s)" % (time.ctime(_ctx.mGetStartTime()),time.strftime("%Z"))
        _paramdict[_key] = _value

        _key   = "Base Path"
        _value = "%s" % (_ctx.mGetBasePath())
        _paramdict[_key] = _value

        _key   = "OEDA Path"
        _value = "%s" % (_ctx.mGetOEDAPath())
        _paramdict[_key] = _value

        if get_gcontext().mGetOEDAHostname():
            _key   = "OEDA Hostname"
            _value = get_gcontext().mGetOEDAHostname()
            _paramdict[_key] = _value

        if get_gcontext().mGetOEDAVersion():
            _key   = "OEDA Version"
            _value = get_gcontext().mGetOEDAVersion().replace("\n","")
            _paramdict[_key] = _value

        _key   = "Log Path"
        _value = "%s" % (_ctx.mGetLogPath())
        _paramdict[_key] = _value

        _key   = "RestListener Log Path"
        _value = _ctx.mGetLogPath()+"/agent.log" #what the link should say
        _paramdict[_key] = _value

        _key   = "RestListener Log Link"
        _value = "/AgentCtrl?file=log/agent.log" #where the link should point to
        _paramdict[_key] = _value

        _key = "ExaCloud Agent Log Path"
        _value = _ctx.mGetLogPath()+"/exacloud.log" #what the link should say
        _paramdict[_key] = _value

        _key = "ExaCloud Agent Log Link"
        _value = "/AgentCtrl?file=log/exacloud.log" #where the link should point to
        _paramdict[_key] = _value

        _response = aResponse
        _response["status"]  = "Done"
        _response["success"] = "True"
        _response["ctype"]   = "application/json"
        _response["output"]  = _paramdict
        return

    def mAgentOedaDiags(self, aParams, aResponse): #----/OedaDiags JSONResponse

        _response = aResponse
        _response["status"]  = "Done"
        _response["success"] = "True"
        _response["ctype"]   = "application/json"
        _response["output"]  = {"status":"DIAG OK"}
        return

    def mAgentOedaLogs(self, aParams, aResponse): #-----/BMCCtrlLogs /OedaLogs /PatchLogs JSONResponse

        # This function creates a collapse div to show files inside a directory. It is called recursively until no more directories are found.
        def _build_log_table_dir(aParentDirPath, aChildDirName, aUUID):

            _curr_dir = {
                "dirname": aChildDirName,
                "logfiles": [] #list of files for THIS directory
            }

            _dir_path = aParentDirPath + aChildDirName + "/"
            _inner_mtime = lambda f: os.stat(os.path.join(_dir_path, f)).st_mtime
            _list_of_files = list(sorted(os.listdir(_dir_path), key=_inner_mtime))

            for _log_file in _list_of_files:
                if os.path.isfile(_dir_path+_log_file):
                    _log_entry_s = "/AgentCtrl?file="+_dir_path+_log_file
                    _curr_dir["logfiles"].append(_log_entry_s)
                else:
                    _curr_dir["logfiles"].append(_build_log_table_dir(_dir_path, _log_file, aUUID))

            return _curr_dir #return a dictionary in the form of a filesystem tree

        if aParams and "uuid" in list(aParams.keys()):

            _uripath = urlparse(self.path)[2]

            #determine the log path according to querystring or URI path

            _err_str = "OEDA"
            _parent_log_dir = os.getcwd() + "/oeda/requests/"+aParams["uuid"]+"/log/"

            if "patch" in list(aParams.keys()):
                _err_str = "PATCH"
                _parent_log_dir = os.getcwd() + "/log/patch/"+aParams["uuid"]+"/"
            elif "bmcctrl" in list(aParams.keys()):
                _err_str = "BMCCTRL"
                _parent_log_dir = os.getcwd() + "/log/bmcctrl/"+aParams["uuid"]+"/"
            elif _uripath=="/PatchLogs":
                _err_str = "PATCH"
                _parent_log_dir = os.getcwd() + "/log/patch/"+aParams["uuid"]+"/"
            elif _uripath=="/BMCCtrlLogs":
                _err_str = "BMCCTRL"
                _parent_log_dir = os.getcwd() + "/log/bmcctrl/"+aParams["uuid"]+"/"
            else:
                _err_str = "OEDA"
                _parent_log_dir = os.getcwd() + "/oeda/requests/"+aParams["uuid"]+"/log/"

            #form filetree dictionary

            _log_filetree = {
                "dirname": _parent_log_dir,
                "logfiles": [] #list of files for THIS directory
            }

            try:
                _mtime = lambda f: os.stat(os.path.join(_parent_log_dir, f)).st_mtime
                _logs_list = list(sorted(os.listdir(_parent_log_dir), key=_mtime))

                for _log in _logs_list:
                    if os.path.isfile(_parent_log_dir+_log):
                        _log_entry_s = "/AgentCtrl?file="+_parent_log_dir+_log
                    else:
                        _log_entry_s = _build_log_table_dir(_parent_log_dir, _log, aParams["uuid"])

                    _log_filetree["logfiles"].append(_log_entry_s)

            except Exception as e:
                ebLogError(str(e))
                _log_filetree = {
                    "err_msg": "Error while accessing %s Logs: %s" % (_err_str, _parent_log_dir)
                }

            _response = aResponse
            _response["status"]  = "Done"
            _response["success"] = "True"
            _response["ctype"]   = "application/json"
            _response["output"]  = _log_filetree
            return

        _response = aResponse
        _response["status"]  = "Done"
        _response["success"] = "False"
        _response["error"]   = "400"
        _response["ctype"]   = "application/json"
        _response["output"]  = {"err_msg":"Invalid Request. UUID not provided."}
        return

    def mAgentVersion(self, aParams, aResponse): #------/Version JSONResponse

        # Make sure to update OEDA build branch first
        get_gcontext().mRefreshOEDALabel()

        # Get OEDA Build Branch from context
        _oeda_build_version = get_gcontext().mGetOEDALabel()

        if self.__options.proxy:
            _nexthost, _nextport, _nextauthkey = self.__routerInstance.mGetECInstance()
            _id = str(_nexthost) + ":" + str(_nextport)
            _agent_vers, _oeda_vers = self.__routerInstance.mGetECInstVersionInfo(_id)

            _versions = {
                "agent" : _agent_vers,
                "oeda"  : _oeda_vers,
                "oeda_build"  : _oeda_build_version
            }
        else:

            params = [get_gcontext().mGetOEDAPath() + "/oedacli", "-v"]

            sp = subprocess
            p = sp.Popen(params, stdout=sp.PIPE, stderr=sp.PIPE)
            stdout, stderr = wrapStrBytesFunctions(p).communicate()

            oeda_version = stdout.strip()

            _versions = {
                "agent" : "{0}({1})".format(*ebCoreContext().mGetVersion()),
                "oeda"  : oeda_version,
                "oeda_build"  : _oeda_build_version
            }


        _response = aResponse
        _response["status"]  = "Done"
        _response["success"] = "True"
        _response["ctype"]   = "application/json"
        _response["output"]  = _versions          #needed in this form for Web UI
        _response["oeda"]    = _versions["oeda"]  #needed in this form for ECRACLI
        _response["oeda_build"]    = _versions["oeda_build"]  #needed in this form for ECRACLI
        _response["agent"]   = _versions["agent"] #needed in this form for ECRACLI
        return

    def mAgentCluster(self, aParams, aResponse): #------/AgentCluster JSONResponse

        #GET NODES----------------------

        _db = ebGetDefaultDB()

        try:
            _cluster_list = literal_eval(_db.mDumpClusterStatus())
        except:
            _cluster_list = []
            ebLogWarn("*** No Cluster defined in DB")

        _node_dict = {}

        for _entry in _cluster_list:
            _node = monitor.ebClusterNode()
            _node.mPopulate(_entry)
            _node_dict[_node.mGetHostname()] = _node

        #GET CLUSTERS-------------------

        _db = ebGetDefaultDB()

        try:
            _rqlist = literal_eval(_db.mDumpRequests())
        except:
            ebLogError("Requests DB access failure in mAgentCluster")
            _rqlist = []

        _cluster_dir = {}
        for _entry in _rqlist:
            _request = ebJobRequest(None, {}, aDB=ebGetDefaultDB())
            _request.mPopulate(_entry)

            if ("configpath" not in list(_request.mGetParams().keys())) or (_request.mGetXml()=="Undef") or (_request.mGetError()!="0"):
                continue

            _config = _request.mGetParams()["configpath"]

            # For now just use the first XML configuration
            if not _config in list(_cluster_dir.keys()):
                _cluster_dir[_config] = {}
                _cluster_dir[_config]["request"] = vars(_request)

        for _entry in list(_cluster_dir.keys()):

            _cluctrl = exaBoxCluCtrl(get_gcontext())

            _eb_request_params = _cluster_dir[_entry]["request"]["_ebJobRequest__params"]
            _eb_request_params = nsOpt(_eb_request_params)
            _cluctrl.mParseXMLConfig(_eb_request_params)

            _ddp = _cluctrl.mReturnDom0DomUPair()
            _cells = _cluctrl.mReturnCellNodes()

            # Dom0/U

            _cluster_dir[_entry]["dom0domupairs"] = []

            for _dom0, _domU in _ddp:
                _cluster_dir[_entry]["dom0domupairs"].append({
                    "dom0": _dom0,
                    "domu": _domU
                })

            # Cells

            _cluster_dir[_entry]["cells"] = []

            for _cell in _cells:
                _cluster_dir[_entry]["cells"].append(_cell)

        #ASSEMBLE RESPONSE-------------------

        #prepare dictionary for JSON conversion
        for cluster in list(_cluster_dir.keys()):

            #remove non-serializable objects
            _cluster_dir[cluster]["request"].pop("_ebJobRequest__db",None)
            _cluster_dir[cluster]["request"].pop("_ebJobRequest__nsOpt",None)

            #if data node already is JSON string, make it a dict
            jsondata = _cluster_dir[cluster]["request"]["_ebJobRequest__data"]
            if jsondata!="Undef":
                _cluster_dir[cluster]["request"]["_ebJobRequest__data"] = json.loads(jsondata)

        _response = aResponse
        _response["status"]  = "Done"
        _response["success"] = "True"
        _response["ctype"]   = "application/json"
        _response["output"]  = {
            "nodes":    _node_dict,
            "clusters": _cluster_dir
        }

        return

    def mAgentTestPage(self, aParams, aResponse): #-----/AgentTest JSONResponse

        _response = aResponse
        _response["status"]  = "Done"
        _response["success"] = "True"
        _response["ctype"]   = "application/json"
        _response["output"]  = {"status":"TEST OK"}
        return

    def mAgentWorkers(self, aParams, aResponse): #------/AgentWorkers JSONResponse

        _paramdict = {}
        _paramdict["workers"] = []

        _db = ebGetDefaultDB()

        try:
            _rqlist = literal_eval(_db.mDumpWorkers())
        except:
            ebLogError("Workers DB access failure in mAgentWorkers")
            _rqlist = []

        for _entry in _rqlist:
            _worker = ebWorker()
            _worker.mPopulate(_entry)

            _log_path = "dflt_worker_"+_worker.mGetPort()+".log" #where the link should point to
            _link_s = "/AgentCtrl?file=log/workers/"+_log_path #what the link should say

            _paramdict["workers"].append({
                "uuid"      : _worker.mGetUUID(),
                "status"    : _worker.mGetStatus(),
                "startTime" : _worker.mGetTimeStampStart(),
                "endTime"   : _worker.mGetTimeStampEnd(),
                "port"      : str(_worker.mGetPort()),
                "pid"       : str(_worker.mGetPid()),
                "type"      : _worker.mGetType(),
                "logPath"   : _log_path,
                "logLink"   : _link_s
            })

        _response = aResponse
        _response["status"]  = "Done"
        _response["success"] = "True"
        _response["ctype"]   = "application/json"
        _response["output"]  = _paramdict

        return

    def mAgentWWWContent(self, aParams, aResponse): #---/WWW HTMLResponse (outputs HTML / CSS / JS / JSON / XML / TXT / JPG)

        # Default ContentType
        _ctype = "text/html"
        _notfound = False

        if aParams and "file" in list(aParams.keys()):

            _pfx = "www/"
            _filename = _pfx + aParams["file"]
            _body = None

            if not self.mValidatePath(_filename):
                _body = "Error. www/content file not found: "+_filename+"."
                ebLogError("*** "+_body)
                _notfound = True
            else:
                try:
                    _f = open(os.getcwd() + "/" + _filename)
                    _body = _f.read()
                    _f.close()
                except:
                    _body = "Error while accessing www/content file: "+_filename+"."
                    ebLogError("*** "+_body)
                    _notfound = True
                #try/except
            #if/else

            if _body is None:
                _body = "File not found."

            _ctype_lookup = {
                "html" : "text/html",
                "css"  : "text/css",
                "js"   : "text/javascript",
                "txt"  : "text/plain",
                "xml"  : "application/xml",
                "json" : "application/json",
                "jpg"  : "image/jpeg"
            }

            _response = aResponse
            _ext = _filename.split(".")[-1]
            if _ext in list(_ctype_lookup.keys()):
                _ctype = _ctype_lookup[_ext]

            if "/" in _filename:
                _cname = _filename.split("/")[-1]
            else:
                _cname = _filename

            _response["status"]  = "Done"
            _response["success"] = "True"
            _response["ctype"]   = _ctype
            _response["cname"]   = _cname
            _response["output"]  = _body

            # Use cache-control for static content
            if not _notfound:
                _response['cache_control'] = True

            return

        else: #to avoid crashes when no querystring is supplied
            _response = aResponse
            _response["status"]  = "Done"
            _response["success"] = "False"
            _response["error"]   = "400"
            _response["ctype"]   = "application/json"
            _response["output"]  = {"err_msg":"No parameters supplied."}
            return _response

    def mBuildChecksums(self):

        _checksumlist = []

        _checksumbase = "./config/checksumfiles.dat"
        if os.path.exists(_checksumbase):
            with open(_checksumbase) as _fd:
                _files = _fd.readlines()
                for _line in _files:
                    _file = None
                    _tarball_checksum = None
                    try:
                        _file = _line.split()[1].strip()
                        _tarball_checksum = _line.split()[0].strip()

                        with open(_file) as _c:
                            _sha256 = str(hashlib.sha256(_c.read().encode('utf8')).hexdigest())
                            _checksumlist.append({
                                "file": _file,
                                "tarballCS": _tarball_checksum,
                                "deployedCS": _sha256
                            })
                    except:
                        ebLogError("*** mBuildChecksums: File {0} not found, failed to build checksum".format(_file))
                        _checksumlist.append({
                            "file": _file,
                            "tarballCS": _tarball_checksum,
                            "deployedCS": "undefined"
                        })

        return _checksumlist

    def mAgentPortal(self, aParams, aResponse): #-------/AgentPortal JSONResponse

        _checksums = self.mBuildChecksums()

        #context dictionary is ordered, readonly, has tuples instead of lists and has passwords in plain text
        #several pre-processings are needed before JSON-stringifying it.
        _thisctx   = get_gcontext().mGetConfigOptions()
        _unordered = unorderDict(_thisctx)
        _coptions  = obfuscate_passwd_entries(_unordered)

        _portaldict = {
            "checksums" : _checksums,
            "config"    : _coptions
        }

        _response = aResponse
        _response["status"]  = "Done"
        _response["success"] = "True"
        _response["ctype"]   = "application/json"
        _response["output"]  = _portaldict

        return

    def mAgentCmdRequest(self, aParams, aResponse): #---/AgentCmd JSONResponse

        if aParams and 'cmd' in list(aParams.keys()):
            _cmd = aParams['cmd']
            ebLogInfo('**** mAgentRequest CMD: %s...' % (_cmd))

            if _cmd == 'stop':
                _agent = ebGetDefaultAgent()
                _agent.mAgent_Shutdown()
                _response = aResponse
                _response['status']     = 'Done'
                _response['success']    = 'True'
                _response['statusinfo'] = 'Agent shutdown in progress'
                return

            if _cmd == 'status':
                _response = aResponse
                _response['status']     = 'Done'
                _response['success']    = 'True'
                _response['statusinfo'] = 'Agent is running and reachable'
                if self.__options.proxy:
                    self.__routerInstance.mReportECInstances()
                return

    def mAgentRequest(self, aParams, aResponse): #------/AgentCtrl HTMLResponse (outputs JSON / XML / TXT)

        _cmd_aliases = {
            "create_service" : "vmgi_install",
            "delete_service" : "vmgi_delete",
            "create_db"      : "db_install",
            "delete_db"      : "db_delete"
        }

        _db = self.__db

        if aParams: #if GET request has a querystring
            _cmdtype = aParams.get("cmdtype")
            if _cmdtype in _cmd_aliases:
                aParams["cmdtype"] = _cmd_aliases[_cmdtype]

        #alternate responses if GET request has a querystring

        if aParams and ("ccluster" in list(aParams.keys())): #Cluster Configuration, outputs XML or JSON

            _uuid = aParams["ccluster"]
            _data = _db.mDumpRequests(aUUID=_uuid)

            if str(_data)=="()":
                _dict = {}
            else:
                _dict = literal_eval(_data)[0][9] # only 1 row and fetch column 9 params data

            _ctype = "application/xml"
            if (not _dict) or (str(_dict) in ["None", "Undef"]):
                _responsebody = {"Error" : "XML Cluster Configuration not available for uuid: "+_uuid}
                _ctype = "application/json"
            else:
                try:
                    with open(str(_dict)) as _f:
                        _responsebody = _f.read()
                except:
                    _responsebody = {"Error" : "XML Cluster Configuration not readable for uuid: "+_uuid}
                    _ctype = "application/json"

            _response = aResponse
            _response["status"]  = "Done"
            _response["success"] = "True"
            _response["ctype"]   = _ctype
            _response["output"]  = _responsebody

            return

        if aParams and ("cparams" in list(aParams.keys())): #Request Type, outputs JSON

            _uuid = aParams["cparams"]
            _data = _db.mDumpRequests(aUUID=_uuid)

            if str(_data)=="()":
                _dict = {"Error" : "Request Type info not available for uuid: "+_uuid}
            else:
                _dict = literal_eval(_data)[0][5] # only 1 row and fetch column 5 params data

            #Fix for bug 26002454
            obfuscate_passwd_entries(_dict)

            _response = aResponse
            _response["status"]  = "Done"
            _response["success"] = "True"
            _response["ctype"]   = "application/json"
            _response["output"]  = _dict

            return

        if aParams and ("file" in list(aParams.keys())): #outputs TXT

            _filename = os.path.realpath(aParams["file"])
            _current = os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())+"/../../"))
            _body = None
            _error = False

            try:
                if _filename.startswith(_current):
                    with open(_filename) as _f:
                        _body = _f.read()
                else:
                    ebLogError("*** File error: "+aParams["file"])
                    _body = "Invalid filename. Incident reported."
            except:
                ebLogError("*** File error: "+aParams["file"])
                _body = "Error while handling external file. Incident reported."
                _error = True

            if _body is None:
                _body = "File not found."
                _error = True

            #Set preformatted timestamps
            if not _error:

                _coptions = get_gcontext().mGetConfigOptions()
                if 'threads_formatter' in list(_coptions.keys()) and _coptions['threads_formatter'] is not None:

                    _newbody = ""
                    _formatter = _coptions['threads_formatter']
                    _delimiters = set([x for x in re.split("%\([a-zA-Z0-9]{1,}\)s", _formatter) if x!=""])

                    if len(_delimiters)!=0:

                        _newdelimiter = " - "
                        for _delimiter in _delimiters:
                            _formatter = _formatter.replace(_delimiter, _newdelimiter)
                        #for

                        try:
                            _asctimepos = _formatter.split(_newdelimiter).index("%(asctime)s")
                            _hidetime   = aParams and 'hidetime' in list(aParams.keys()) and aParams['hidetime'].lower() == "true"

                            if _hidetime:

                                for _row in _body.split("\n"):

                                    _newrow = _row
                                    for _delimiter in _delimiters:
                                        _newrow = _newrow.replace(_delimiter, _newdelimiter)
                                    #for

                                    _newrowsplit = _newrow.split(_newdelimiter)
                                    _formattersp = _formatter.split(_newdelimiter)

                                    if len(_newrowsplit)==len(_formattersp):
                                        if _asctimepos==0 and _newrowsplit[0].startswith("<pre>"):
                                            _newrowsplit.pop(_asctimepos)
                                            _newrowsplit[0] = "<pre>"+_newrowsplit[0]
                                        else:
                                            _newrowsplit.pop(_asctimepos)
                                        #else
                                    #if

                                    _newbody += _newdelimiter.join(_newrowsplit)+"\n"
                                #for

                                _newbody = _newbody.strip()
                            else:
                                _newbody = _body
                            #else
                        except ValueError:
                            ebLogWarn("%(asctime)s not found on the format option")
                            _newbody = _body
                        #except
                    else:
                        _newbody = _body
                    #else

                    _body = _newbody
                #if
            #if

            _response = aResponse
            _response["status"]  = "Done"
            _response["success"] = "True"
            _response["ctype"]   = "text/plain"
            _response["output"]  = _body

            return

        # Request V3 (Oracle JET & JSON. V2 was HTML & Bootstrap) #outputs JSON

        _content = monitor.build_requests_html_page(aParams) #returns a json showing every request made (content of /AgentCtrl)

        _response = aResponse
        _response["status"]  = "Done"
        _response["success"] = "True"
        _response["ctype"]   = "application/json"
        _response["output"]  = _content

        return # _response is returned to HTTPResponses.HttpCb.executeRequest

    def mHardwareInfo(self, aParams, aResponse): #------/HardwareInfo JSONResponse
        # Prepare the request
        _start_time = time.asctime()
        _err = None
        _err_str = None
        _req = None

        # pylint: disable=no-member
        # Execute the Cell Info command
        try:
            _options = lambda: None
            _options.uuid = aParams['uuid'] if 'uuid' in aParams else str(uuid.uuid1())
            _options.hostname = aParams['hostname']
            _options.hw_type = aParams['hw_type']
            if 'debug' in list(aParams.keys()):
                _options.debug = aParams['debug']
            else:
                _options.debug = False
            _hwInfoObj = ebHardwareInfo( _options.hw_type, _options.hostname)
            _hwInfo = _hwInfoObj.mGetInfo()
        except Exception as e:
            _hwInfo = {}
            _hwInfo['exit_code'] = -1
            _hwInfo['stderr'] = f'{e}\n{traceback.format_exc()}'
            _hwInfo['stdout'] = ''
            ebLogError(traceback.format_exc())
            ebLogError(str(e))

        _end_time = time.asctime()

        # Make a HTTP response
        _response = aResponse
        _response['status']     = 'Done'
        _response['success']    = 'True'
        _response['uuid']       = _options.uuid
        _response['ec_details'] = _hwInfo
        _response['time']       = "{} to {}".format(_start_time, _end_time)

    def mAtpGetFile(self, aParams, aResponse): #--------/AtpGetFile HTMLResponse (outputs HTML / JSON / TXT / BIN)

        _response = aResponse
        _coptions = get_gcontext().mGetConfigOptions()
        _errstr   = ""

        if aParams==[]: #to avoid crashes when no querystring is supplied
            _response["status"]  = "Done"
            _response["success"] = "False"
            _response["error"]   = "400"
            _response["ctype"]   = "application/json"
            _response["output"]  = {"err_msg":"No parameters supplied."}
            return _response

        #Get the response type
        _typeResponse = "text"

        if "type" in list(aParams.keys()) and aParams["type"] in ("text", "data", "html"):
            _typeResponse = aParams["type"]

        #Get the file to log
        _file = ""
        _basepath = ""

        if "file" not in list(aParams.keys()) or aParams["file"]=="":
            _errstr = "No found param 'file' on mAtpGetFile"
        else:
            if "atpgetfile_base_path" not in list(_coptions.keys()) or _coptions["atpgetfile_base_path"]=="":
                _errstr = "No found param 'atpgetfile_base_path' on exabox.conf used by mAtpGetFile"
            else:
                _file = urllib.parse.unquote(aParams["file"])
                _basepath = _coptions["atpgetfile_base_path"].strip()

                if _basepath=="/" or _basepath=="":
                    _errstr = "AtpGetFile endpoint has not been configured, please set base path in exacloud configuration."
                else:
                    if _basepath[-1]!="/":
                        _basepath = _basepath+"/"

                    _file = os.path.realpath("{0}{1}".format(_basepath, _file))

                    # Disallow backward navigation ../../
                    if not _file.startswith(_basepath):
                        _errstr = "Invalid path on 'file' param in mAtpGetFile: '{}'".format(urllib.parse.unquote(aParams["file"]))
                    else:
                        if not os.path.isfile(_file):
                            _errstr = "File not found mAtpGetFile: '{}'".format(_file)

        #Read the file
        _body = "This is an empty file"

        try:
            if _errstr=="":
                with open(_file, "r") as _f:
                    _body = _f.read()
        except Exception as _excp:
            _errstr = "Error on 'mAtpGetFile': {}".format(_excp)

        #Error response
        if _errstr!="":
            ebLogError("*** {}".format(_errstr))
            _response["ctype"]  = "application/json"
            _response["output"] = {"err_msg":_errstr+".\nFor more information, consult the exacloud.log."}
            ErrorBuilder.response(777, _errstr, _response)
            return _response

        _response["status"]  = "Done"
        _response["success"] = "True"

        #parse the result
        if _typeResponse=="html":
            _response["ctype"]  = "text/html"
            _response["output"] = monitor.build_html_page_header()+'<div class="container" style="width: 100%;">'+_body+"</div>"+monitor.build_html_page_footer()
        elif _typeResponse=="data":
            _response["cname"]  = os.path.basename(_file)
            _response["ctype"]  = "application/octet-stream"
            _response["output"] = _body
        else:
            _response["ctype"]  = "text/plain"
            _response["output"] = _body

        return _response

    def mBDSCmd(self, aParams, aResponse): #------------/BDCSCmd JSONResponse
        return self.mBDS(aParams, aResponse, 'cluctrl.bds_cmd')

    def mBDSInstall(self, aParams, aResponse): #--------/BDCSInstall JSONResponse
        return self.mBDS(aParams, aResponse, 'cluctrl.bds_install')

    def mBDS(self, aParams, aResponse, aTargetCMD):

        _response = aResponse
        _err = False
        _errstr = None

        # Check if all Parameters are available
        if not aParams or not len(list(aParams.keys())):
            _errstr = 'No Parameters provided'
            _err = True

        requiredp = set(('jsonconf', 'configpath',))
        providedp = set(aParams.keys())
        missingp = requiredp - providedp
        if missingp:
            paramsstr = ', '.join(missingp)
            _errstr = 'Parameters ({0}) are required'.format(paramsstr)
            _err = True

        if _err:
            ErrorBuilder.response(800,_errstr,_response)
            return

        # Create Job and New DB entry
        _req = ebJobRequest(aTargetCMD, aParams, aDB=ebGetDefaultDB())
        _req.mRegister()

        if not dispatchJobToWorker(_req, self.__workerlock):
            buildErrorResponseForRequest(self, _response)
            return

        #
        # Prepare response
        #
        _response = aResponse
        _response['uuid']    = _req.mGetUUID()
        _response['status']  = _req.mGetStatus()
        _response['success'] = 'True'

    def mAgentLogDownload(self, aParams, aResponse): #--/logDownload FileResponse

        #Support 2 options, regular uuid logs and full vm logs using rack xml
        try:
            ebLogInfo("Downloading logs")
            _response = aResponse

            #check if log dump directory is set in context, if not use default (/tmp)
            _log_dir = '/tmp'
            _coptions = get_gcontext().mGetConfigOptions()
            if 'default_logdir' in _coptions:
                if _coptions['default_logdir'][0]=='/': #if path is absolute, leave it as such
                    _log_dir = _coptions['default_logdir']
                else:
                    _log_dir = get_gcontext().mGetBasePath() + _coptions['default_logdir'] #if path is relative, make it point to a subdirectory of exacloud

            if not 'configpath' in aParams :
                ebDownloadLog(aParams, _response, _log_dir)

            #want the logs directly from the vms
            else:
                _db= aParams['dbName'] if 'dbName' in aParams else None
                _vm= aParams['vmName'] if 'vmName' in aParams else None
                _params={'dbName':_db,'vmName':_vm}
                _rack_path=aParams['configpath']
                _options=lambda:None
                _options.configpath=_rack_path
                _options.jsonconf=None

                _cluctrl = exaBoxCluCtrl(get_gcontext())
                _cluctrl.mParseXMLConfig(_options)
                _log_folder=_cluctrl.mCopyDBLogFiles(_params)
                _tar_file=_cluctrl.mGetClusterName()+ '.tgz'

                _dir_path = _cluctrl.mGetBasePath() + '/' + _log_folder
                _file_list = glob.glob('{0}/*.*'.format(_dir_path))
                _file_str = ' '.join([str(_file) for _file in _file_list])
                _cmd = "/bin/rm -rf {0}".format(_file_str)
                _cluctrl.mExecuteLocal(_cmd, aCurrDir=_dir_path)

                _destVM = _vm if _vm != None else ' '
                _file_list = glob.glob('{0}*'.format(_destVM))
                _file_str = ' '.join([str(_file) for _file in _file_list])
                _cmd = '/bin/tar cvfz ' + _tar_file + ' ' + _file_str
                _cluctrl.mExecuteLocal(_cmd, aCurrDir=_dir_path)

                _response['file'] = _log_folder+'/'+_tar_file

                ebLogInfo("logs downloaded at %s" %(_response['file']))
        except Exception as e:
            ebLogError("Exception caught while downloading logs %s " % str(e))

        return

    def mAgentFetchLog(self, aParams, aResponse): #-----/OCIExaCCLog FileResponse

        _base_path = get_gcontext().mGetBasePath()
        _hcconfigpath = _base_path + '/config/healthcheck.conf'

        try:
            _hcconfig = json.load(open(_hcconfigpath))
            _root_dir = _hcconfig['diag_root']
        except Exception as e:
            ebLogWarn('Could not get diag_root from healthcheck.conf : %s' % e)
            ebLogWarn('Fetch logs from exacloud root instead of diag root')
            _root_dir = _base_path

        _results_dir = '%s/diagnostic/results' % _root_dir

        try:
            _response = aResponse
            _uuid, _chunkid = aParams['jobid'].split('--')
            _response['file'] = '%s/%s.tar.gz.%s' % (_results_dir, _uuid,
                    str(_chunkid).zfill(2))
            _response['delete_temp'] = True
            ebLogInfo("Fetching diag logs for the job uuid: %s" % _uuid)
        except Exception as e:
            ebLogError("Exception caught while fetching logs: %s" % str(e))

        return

    def mWorkerStatus(self, aParams, aResponse): #------/WorkerStatus JSONResponse

        _url = "http://localhost:"
        _url_parameters = "/wctrl?cmd=status"
        _response = aResponse
        _response['status'] = "Done"
        _response['success'] = "True"

        _db = ebGetDefaultDB()
        _rc = _db.mGetWorkerStatus()
        _result = []
        for _iter in range(0,len(_rc)):
            _temp = {}
            try:
                _temp['port'] = _rc[_iter][0]
                _temp['uuid'] = _rc[_iter][1]
                _temp['status'] = _rc[_iter][2]
                if _rc[_iter][3]:
                    _temp['clustername'] = _rc[_iter][3]
                if _rc[_iter][4]:
                    _temp['command'] = _rc[_iter][4]
            except:
                _result.append(_temp)
                continue
            try:
                #Authentication is forwarded, Request Authorization header
                #was injected by a preprocessor into a parameter
                headers = {}
                headers["authorization"] = aParams['req_auth_header']
                _url_response = HTTPSHelper.build_opener(\
                    "localhost", _temp['port'], 
                    _url + str(_temp['port']) + _url_parameters, 
                    aHeaders=headers)
                _check_status = _url_response.read()
                _check_status = literal_eval(_check_status)
                if _check_status['success']==False:
                    _temp['status'] = "Invalid"
            except Exception as e:
                ebLogError("Cannot reach workers error " + str(len(str(e))))
                _temp['status'] = "Unreachable"
            _result.append(_temp)
        _response['response'] = _result
        return


    def mHandleECInstance(self, aParams, aResponse): # ----- /ecinstmaintenance

        # Check if all Parameters are available
        _response = aResponse
        if not aParams or not len(list(aParams.keys())):
            _str = 'No Parameters provided'
            _err = True
            _response['success'] = 'False'
            _response['status']  = 'Done'
            return

        ebLogInfo("aParams: {}".format(aParams))
        _op = None
        _host = None
        _port = None
        _vers = None
        _reqtype = None
        _auth_key = None
        _oeda_vers = None
        _key = None
        _value = None
        _paramslist = list(aParams.keys())
        _response = aResponse

        if 'op' in _paramslist:
            _op = aParams['op']
        if 'host' in _paramslist:
            _host = aParams['host']
        if 'port' in _paramslist:
            _port = aParams['port']
        if 'version' in _paramslist:
            _vers = aParams['version']
        if 'request_type' in _paramslist:
            _reqtype = aParams['request_type']
        if 'auth_key' in _paramslist:
            _auth_key = aParams['auth_key']
        if 'oeda_version' in _paramslist:
            _oeda_vers = aParams['oeda_version']
        if 'key' in _paramslist:
            _key = aParams['key']
        if 'value' in _paramslist:
            _value = aParams['value']

        if _op == 'register' and _host and _port and _vers and _reqtype and _auth_key and _oeda_vers:

            self.__routerInstance.mRegisterECInstance(_host, _port, _vers, _auth_key, _reqtype, _oeda_vers)
            _response['success'] = 'True'

        elif _op == 'deregister' and _host and _port and _reqtype:

            self.__routerInstance.mDeregisterECInstance(_host, _port, _reqtype)
            _response['success'] = 'True'

        elif _op == 'update' and _host and _port and _key and _value:

            self.__routerInstance.mUpdateECInstance(_host, _port, _key, _value)
            _response['success'] = 'True'

        else:
            ebLogError("Invalid operation/ Insufficient parameters")
            _response['success'] = 'False'

        _response['status']  = 'Done'
        return

    def mHeartbeatECInstance(self, aParams, aResponse): #--- /heartbeat

       #
       # Prepare response
       #
       _response = aResponse
       _response['status']  = 'Done'
       _response['success'] = 'True'
       return 

    def mServeUI(self, aParams, aResponse): #-----------/ /css /js HTMLResponse (outputs HTML / CSS / JS / JSON / TXT / IMG / FONT)

        #possible content-types this method can return (every type of file in www/ecwebui)
        _ctypes = {
            "html" : ("text/html"                , "r"),
            "css"  : ("text/css"                 , "r"),
            "js"   : ("text/javascript"          , "r"),
            "json" : ("application/json"         , "r"),
            "map"  : ("application/json"         , "r"),
            "txt"  : ("text/plain"               , "r"),
            "svg"  : ("image/svg+xml"            , "r"),
            "gif"  : ("image/gif"                , "rb"),
            "png"  : ("image/png"                , "rb"),
            "ico"  : ("image/x-icon"             , "rb"),
            "woff" : ("application/font-woff"    , "rb"),
            "cur"  : ("application/octet-stream" , "rb")
        }

        #get content-type and read mode from file extension

        _filepath = aParams["path"]

        _filename = _filepath
        if "/" in _filepath:
            _filename = _filepath.split("/")[-1]

        _ext = "txt"
        if "." in _filename:
            _ext = _filename.split(".")[-1]

        _ctype = "text/plain"
        _rmode = "r"
        if _ext in list(_ctypes.keys()):
            _ctype, _rmode = _ctypes[_ext]

        #Generate absolute filepath

        _coptions = get_gcontext().mGetConfigOptions()
        _ecpath   = _coptions["oeda_dir"][:-4] #path to OEDA minus 4 trailing characters is path to exacloud
        _uipath   = os.path.join(_ecpath, "www/ecwebui/")
        if _filepath[0]=="/":
            _filepath = _filepath[1:]
        #if
        _targetpath = _uipath+_filepath

        #Read the file and store it

        _found = False
        _body  = ""

        try:
            if self.mValidatePath(_targetpath):
                try:
                    with open(_targetpath, _rmode) as _f:
                        _body = _f.read()
                    _found = True
                    if _ext=="woff":
                        _clength = os.path.getsize(_targetpath) #calculate size of woff files (not size of content), must be 5104 and 4896
                    #if
                except:
                    _body = "mServeUI error while reading file: {}".format(_targetpath)
                    ebLogError("*** "+_body)
                #try/except
            else:
                _body = "mServeUI provided file path is invalid: {}".format(_targetpath)
                ebLogError("*** "+_body)
            #if
        except:
            _body = "mServeUI error while accessing file: {}".format(_targetpath)
            ebLogError("*** "+_body)
        #try/except

        _response = aResponse

        if _found:
            _response['cache_control'] = True # Use cache-control for static content
            _cerr  = "200"
            _succ  = "True"
        else:
            _cerr  = "400"
            _succ  = "False"
            _ctype = "text/plain"
        #if

        #Assemble response
        _response["status"]  = "Done"
        _response["success"] = _succ
        _response["error"]   = _cerr
        _response["ctype"]   = _ctype
        _response["output"]  = _body

        if _ext=="woff":
            _response["clength"] = _clength #calculate size of woff files (not size of content), must be 5104 and 4896
        #if

        return _response
    #mServeUI

    def mCheckOpctlStatus(self, body, aParams, db, response):
        status_info = body[10]
        opctl_payload = body[5]
        opctl_data = body[-1]

        try:
            # status is already updated from DB
            if '"status": "200"' in opctl_data:
                response["status"] = "Done"
                response["body"] = []
                response["body"].append(opctl_data) 
                response["success"] = "True"
                return response 
             
            # check if opctl has indeed failed or in progress, otherwise update the status
            # get the ecra idemtoken, as opctl status is stored based on this idemtoken
            idemtoken_str = "'idemtoken': '"
            idemtoken_len = 36 # idemtoken is generally in form ff7452f7-e91b-4de6-8382-f4a803b62694
            opctl_idemtoken_index = opctl_payload.find(idemtoken_str)
            opctl_idemtoken = \
                    opctl_payload[opctl_idemtoken_index + len(idemtoken_str):opctl_idemtoken_index + len(idemtoken_str) + idemtoken_len]
            ebLogInfo(f"opctl_idemtoken {opctl_idemtoken}")

            # check the idemtoken file and update the status in DB. Once updated fetch the response from DB
            opctl_obj = ExaCloudWrapper.set_infra_type()
            new_body = opctl_obj.check_status_for_idemtoken(aParams, opctl_idemtoken)
            if not new_body:
                 response["status"] = "Done"
                 response["body"] = []
                 response["success"] = "False"
                 return response

            ebLogInfo(f"opctl new status feteched from DB {new_body.mToDict()}")
 
            response["status"] = new_body.mGetStatus()
            if new_body.mGetBody() != "Undef":
                response["success"] = "True"
                response["body"] = json.dumps(new_body.mGetBody()) 

            if new_body.mGetError() != "Undef":
                response["status"] = "Done"
                response["success"] = "False"
                response["body"] = json.dumps(new_body.mGetBody())
            return response

        except Exception as err:
            ebLogWarn(f"Exception for UUID {aParams.get('uuid')} backtrace {err}")
            ebLogError(traceback.format_exc())
            response = None

        return response

def handlerhook(aArgs1, aArgs2=None, aArgs3=None):

    def _init_handler(*args):
        try:
            ebRestHttpListener(aArgs1, aArgs2, aArgs3, *args)
        except Exception as error:
            with CrashDump() as crash:
                crash.ProcessException()
            ebLogError("*** ebRestHttpListener: Exception caught {0}".format(error))
        #try/except
    #_init_handler

    return _init_handler

class ebThreadingSimpleServer(socketserver.ThreadingMixIn, ExaHTTPSServer):
    pass

class ebForkingSimpleServer(socketserver.ForkingMixIn, ExaHTTPSServer):
    pass

class ebRestListener(object):

    def __init__(self, aConfig):

        self.__main_agent_pid = os.getpid()
        self.__config = aConfig
        _coptions = get_gcontext().mGetConfigOptions()
        self.__args_options = get_gcontext().mGetArgsOptions()
        if 'agent_local' in list(_coptions.keys()) and _coptions['agent_local'] == 'True':
            _host = 'localhost'
        else:
            _host = '0.0.0.0'
        self.__server_addr = (_host,self.__config['agent_port'])
        ebLogInfo("Starting agent at: {0}".format(self.__server_addr))
        #
        # Select default HTTP server mode: serial, threaded, forkmode
        #
        if not 'http_server_mode' in list(_coptions.keys()):
            self.__server_class = ExaHTTPSServer
            ebLogInfo('*** ebRestListner started in default mode')
            ebSetServerClass('default')
        elif _coptions['http_server_mode'] == 'threaded':
            ebLogInfo('*** ebRestListener started in threaded mode')
            self.__server_class = ebThreadingSimpleServer
            ebSetServerClass('threaded')
        elif _coptions['http_server_mode'] == 'forked':
            ebLogInfo('*** ebRestListener started in forked mode')
            self.__server_class = ebForkingSimpleServer
            ebSetServerClass('forked')
        else:
            self.__server_class = ExaHTTPSServer
            ebLogInfo('*** ebRestListener unknown mode using default')
        _parentlock = Lock()
        if self.__args_options.proxy:
            _iRouterManagerPort = int(_coptions['routermanager_port'])
            __routerManager = RouterManager(address=('', _iRouterManagerPort), authkey=b'exacloud')
            __routerManager.start()
            # pylint: disable=no-member
            aRouterInst = __routerManager.routerObject()
            # pylint: enable=no-member
            self.__handler_class = handlerhook(self.__config, aRouterInst, _parentlock)
        else:
            self.__handler_class = handlerhook(self.__config, None, _parentlock)
        try:
            self.__server_class.request_queue_size = _coptions.get('http_queue', 1000)
            self.httpd = self.__server_class(self.__server_addr, self.__handler_class)
            ebSetHttpdServer(self.httpd)
        except Exception as e:
            ebLogError('ebRestListener: Exception:: %s - %s' % (e.__class__, e))
            ebLogError('ebRestListener: Can not start Agent Listener on port: '+str(self.__config['agent_port']))
            ebExit(-1)


    def serve_forever(self):
        try:
            # IF Different PID than Main agent, use Thread-Safe logger
            if (os.getpid() != self.__main_agent_pid):
                _ob = getattr(ebThreadLocalLog(),'activated_by', None)
                if _ob is not None:
                    ebLogError('Not Expecting ThreadLocal Log to be initialized.')
                    ebExit(-1)
                else:
                    ebThreadLocalLog().activated_by='agent'
                # Disable existing default loggers
                _dflt_logger = logging.getLogger(ebGetDefaultLoggerName())
                if _dflt_logger:
                    #iterate over copy as we remove handlers in same array
                    for handler in _dflt_logger.handlers[:]:
                        _dflt_logger.removeHandler(handler)

            self.httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        except Exception as ex:
            with CrashDump() as c:
                c.ProcessException()

    def mStartRestListener(self):

        try:
            config_options = get_gcontext().mGetConfigOptions()
            self.preforks = []
            if config_options['http_server_mode'] == 'preforked':
                for i in range(int(config_options.get('http_workers', '8'))):
                    process = Process(target=self.serve_forever)
                    process.start()
                    self.preforks.append(process)
                    ebLogInfo('Starting Prefork at pid: {0}'.format(process.pid))
            else:
                # VGE Equivalent code for non preforked where this function was in a thread
                _thread.start_new_thread(self.httpd.serve_forever())

        except socket_error as e:
            if e.errno == errno.EADDRINUSE:
                ebLogError('ERROR: Agent can not start listening address already in use.')
                sys.exit(-1)
        except Exception as ex:
            ebLogError('*** Worker RestListener caught exception')
            with CrashDump() as c:
                c.ProcessException()

    def mStopRestListener(self):

        #bug 28124842: Change of shutdown to server_close for prevent hang
        self.httpd.server_close()
        for p in self.preforks:
            p.terminate()
            p.join(2)
            if p.is_alive():
                os.kill(p.pid,signal.SIGKILL)
                os.waitpid(p.pid,0)
        #self.httpd.socket.close()

def compute_agent_port(aConfigOptions, aArgsOptions) -> int:
    """
    Common static function to compute agent port
    """
    _agent_port = 7080
    if aArgsOptions.agent_port:
        _agent_port = int(aArgsOptions.agent_port)
    elif "agent_port" in aConfigOptions:
        _agent_port = int(aConfigOptions["agent_port"])

    return _agent_port


class ebAgentDaemon(object):

    def __init__(self):

        self.__restlistener = None
        self.__config_opts = get_gcontext().mGetConfigOptions()
        self.__config = {}
        self.__workerFactory = ebWorkerFactory()
        self.__logfilename_no_extension = None
        self.__agent_destination_handlers = None
        self.__main_loop_exited = False
        self.__disable_monitor  = False
        self.__reacheable = False
        self.__specialWorkersPids = []
        self.__stopped = False
        self.__args_options = get_gcontext().mGetArgsOptions()

        _args_opt    = self.__args_options
        _config_keys = list(self.__config_opts.keys())
        self.__config["agent_port"] = compute_agent_port(self.__config_opts,
                                                         _args_opt)

        self.__agent_port = str(self.__config["agent_port"])
        self.__authkey = ebGetHTTPAuthStorage().mGetAdminCredentialForRequest()

        self.__agent_reqtype = GENERIC 

        if "agent_reqtype" in _config_keys:
            self.__agent_reqtype = self.__config_opts["agent_reqtype"]

        #proxy_client will only be defined if Agent is behind proxy
        self.__proxy_client     = None
        if 'proxy_port' in _config_keys and 'proxy_host' in _config_keys:
            self.__proxy_client = ProxyClient()

        if 'agent_id' in _config_keys:
            self.__agent_id = self.__config_opts['agent_id']
        else:
            self.__agent_id = 0

        if not _args_opt.proxy and 'exatest' in _config_keys and self.__config_opts['exatest']:
            self.__exatest = True
        else:
            self.__exatest = False

        if "disable_monitor" in list(self.__config_opts.keys()):
            if self.__config_opts['disable_monitor'] == 'True':
                self.__disable_monitor = True

        ebSetDefaultAgent(self)
        #
        # Set gGlobalShutdown (required for listener interaction)
        #
        global gGlobalShutdown
        gGlobalShutdown = False

    def mGetReacheable(self):
        return self.__reacheable

    def mSetReacheable(self, aBool):
        self.__reacheable = aBool

    def mAgent_Config(self):
        return [gethostname(), self.__config_opts['agent_port']]

    def _mDaemonizedSubProcesses_mStart(self, aProcessAgentOption, aCheckPidFn):
        """
            This function will start a new "special" daemonized process
            Typically Scheduler and Supervisor. That will be tracked
            Interface for special process are an agent option (first arg)
            and that graceful STOP must be handled through a SIGINT

            :param str aProcessAgentOption: '--supervisor','--scheduler'
            :param fn aCheckPidFn: Function handle to fetch Pid if started and
                                   a False truth value if failed/starting
        """
        _cmd_list = ['bin/exacloud', '-dc', aProcessAgentOption]
        if self.__exatest:
            _cmd_list.append('--exatest')
            ebLogInfo(f'Executing command: {_cmd_list}')

        # Add args that need to be propagated (e.g. --debug/--verbose)
        _cmd_list.extend(get_gcontext().mGetPropagateProcOptions())

        # Do not need piped std nor inherited FDs
        ebLogTrace(f"Running command: {_cmd_list}")
        rc = subprocess.run(_cmd_list)
        if rc.returncode != 0:
            raise Exception('Cannot start daemonized process (1): {} RC:{}'\
                            .format(_cmd_list, rc.returncode))

        # 20s timeout is plenty in that case.
        # we cannot get the PID from Popen as the daemonize function
        # creates a new PID
        _timeout = 20
        _start_time = time.time()
        _pid = None
        while (time.time() - _start_time < _timeout):
            _pid = aCheckPidFn()
            time.sleep(2)
            if _pid:
                self.__specialWorkersPids.append(int(_pid))
                break
        if not _pid:
            raise Exception('Cannot start daemonized process (2): {}'\
                            .format(aProcessAgentOption))


    def mAgent_Start(self):

        global gGlobalShutdown
        _oraconn = None
        #Check AQ configuration
        if not get_gcontext().mCheckConfigOption('ociexacc', 'True') and \
               get_gcontext().mCheckConfigOption('enable_pushstatus_support', 'True'):

            ebLogInfo("Advanced queue push status support is enabled. Verifying mandatory configurations required for the feature.")
            if "LD_LIBRARY_PATH" not in os.environ:
                ebLogError("LD_LIBRARY_PATH not configured. Please check $EC_HOME/bin/header file for configuration details. \
                            This environment variable needs to have a path configured where libclntsh.so exists.")
                return
            else:
                ebLogTrace(f"LD_LIBRARY_PATH set to {os.environ['LD_LIBRARY_PATH']}")

            _connected_successfully = True
            try:
                import oracledb
                oracledb.init_oracle_client()
                _ecradb_details = get_ecradb_details()
                _mandatory_conn_params = ['user', 'password', 'host', 'port', 'service_name']
                _all_conn_params_available = True
                for _conn_param in _mandatory_conn_params:
                    if _conn_param not in _ecradb_details:
                        ebLogError(f"Mandatory connection parameter {_conn_param} is missing from configured ECRA database details.")
                        _all_conn_params_available = False
                        break

                if not _all_conn_params_available:
                    ebLogError(f"Mandatory connection parameters unavailable from configured ECRA database details, terminating agent startup")
                    return

                _oraconn = oracledb.connect(user =         _ecradb_details.get('user'), \
                                            password =     _ecradb_details.get('password'),\
                                            host =         _ecradb_details.get('host'), \
                                            port =         _ecradb_details.get('port'), \
                                            service_name = _ecradb_details.get('service_name'))
            except ImportError as ie:
                ebLogWarn(f"Failed to import python library: {ie}")
            except Exception as ex:
                ebLogError(f"Encountered generic exception during connection setup. Details: {ex}, terminating agent startup")
                _connected_successfully = False
            finally:
                if 'connection' in locals() and _oraconn:
                    _oraconn.close()

            if not _connected_successfully:
                ebLogError("Unable to connect to the ECRA database. Oracle AQ push status support pre-check fail.")
                return
            else:
                ebLogInfo("Successfully connected to the ECRA database. Oracle AQ push status support pre-check succeeded.")

        # Check Status of DB
        self.mCheckAgentState()

        # Check Status of WorkerFactory
        self.__workerFactory.mInitFactory()

        # Start Dispatcher, Workermanager and Supervisor
        if not self.__args_options.proxy:
            if "agent_delegation_enabled" in list(self.__config_opts.keys()) and self.__config_opts['agent_delegation_enabled'].upper() == 'TRUE':
                ebLogInfo('Dispatcher is enabled')
                self._mDaemonizedSubProcesses_mStart('--dispatcher',
                                                    dispatcher_running)

                ebLogInfo('Worker manager is enabled')
                self._mDaemonizedSubProcesses_mStart('--workermanager',
                                                    workermanager_running)
            else:
                ebLogInfo('Agent delegation feature is disabled!')

            supervisor = self.__config_opts.get('supervisor', 'True')
            if supervisor == 'True' and not self.__args_options.nosupervisor:
                ebLogInfo('Supervisor is enabled')
                self._mDaemonizedSubProcesses_mStart('--supervisor', 
                                                    supervisor_running)
            else:
                ebLogInfo('Supervisor is disabled')

        # Start proxy heartbeat process.
        if self.__args_options.proxy:
            ebLogInfo("Starting proxy hearbeat process")
            _cmd_list = ['bin/exaproxy', '--proxy', 'asproxy', '-dc', '--heartbeat']

            # Add args that need to be propagated (e.g. --debug/--verbose)
            _cmd_list.extend(get_gcontext().mGetPropagateProcOptions())

            subprocess.run(_cmd_list, stdout=None, stderr=None)

        # Start scheduler
        if not self.__args_options.proxy:
            scheduler = self.__config_opts.get('scheduler', 'True')
            if scheduler == 'True':
                ebLogInfo('Scheduler is enabled')
                from exabox.agent.Scheduler  import scheduler_running
                self._mDaemonizedSubProcesses_mStart('--scheduler',
                                                    scheduler_running)
            else:
                ebLogInfo('Scheduler is disabled')

        # Reset Workers List (e.g. worker with status set to Exited)
        # xxx/MR: BUG - Race condition with start workers
        # self.__workerFactory.mResetWorkersList()

        # Daemonize the agent if requested
        if self.__args_options.daemonize:
            ebLogInfo('Daemonize Agent...')
            daemonize_process()

            if not self.__exatest:
                redirect_std_descriptors()

            # Redirect default log to Agent log file
            self.__logfilename_no_extension = 'log/dflt_agent'
            _default_logger_name = ebGetDefaultLoggerName()
            self.__agent_destination_handlers = ebLogAddDestinationToLoggers([_default_logger_name],
                self.__logfilename_no_extension, ebFormattersEnum.DEFAULT)

        #In case of exatest, redict the log
        if not self.__args_options.proxy and self.__exatest:

            #Calculate the workdir
            _sf = 'log/exatest'
            _d = os.listdir(_sf)
            _d.sort(key=lambda x: os.path.getmtime(os.path.join(_sf, x)))
            _workdir = os.path.join(_sf, _d.pop())

            #Apply the workdir to files
            ebLogInfo("  Exatest OutputF: %s " % (_workdir))
            self.__logfilename_no_extension = os.path.join(_workdir , 'exacloud')
            _default_logger_name = ebGetDefaultLoggerName()
            self.__agent_destination_handlers = ebLogAddDestinationToLoggers([_default_logger_name],
                self.__logfilename_no_extension, ebFormattersEnum.DEFAULT)

        # Update AgentInfo DB
        _db = ebGetDefaultDB()
        _db.mCreateAgentTable()
        _agent_id = self.__agent_id
        _rc = _db.mAgentStatus(_agent_id)
        if _rc is not None and _rc[2] != 'stopped':
            ebLogWarn('*** DB Agent Info entry out of sync (%s:%s:%s) resyncing' % (_rc[0],_rc[1],_rc[2]))
            _db.mDeleteAgent(_agent_id)
            _rc = None

        # Create ebAgentInfo and update DB entry
        global gAgentInfo
        gAgentInfo = ebAgentInfo(_agent_id)
        gAgentInfo.mSetPort(self.__config["agent_port"])
        if _rc is None:
            _db.mInsertAgent(gAgentInfo)
        _db.mStartAgent(aAgentId=_agent_id, aPid=str(os.getpid()))

        # Start Rest/HTTP Listener
        if not self.__restlistener:
            self.__restlistener = ebRestListener(self.__config)
            ebLogInfo('Agent (%s) started...' % (_agent_id))
            self.__restlistener.mStartRestListener()

        if get_gcontext().mCheckConfigOption('ociexacc', 'True'):
            insertRestrictedEndpointsInformation()
            _cps_fqdn = socket.getfqdn()
            ebLogInfo(f"Current CPS hostname: {_cps_fqdn}")
            _input_reg_key = "ociexacc_deploymenttype_dev"
            _db.mDelRegEntry(_input_reg_key)
            for _domain_name in ACCEPTED_DEVQA_DOMAINNAMES:
                if _domain_name in _cps_fqdn:
                    _db.mSetRegEntry(_input_reg_key)
                    ebLogInfo(f"Current CPS: {_cps_fqdn} is running on a dev/qa setup.")
                    break
            ocps_json_path = ""
            if get_gcontext().mGetConfigOptions().get('ocps_jsonpath') is not None:
                ocps_json_path = get_gcontext().mGetConfigOptions().get('ocps_jsonpath')
                exacc_json_path = os.path.join(os.path.dirname(ocps_json_path), "exacc.json")
                region = None
                if os.path.exists(exacc_json_path):
                    exacc_json = json.load(open(exacc_json_path))
                    monConfig = exacc_json.get("monitoringConfig", None)
                    if "region" in monConfig:
                        region = monConfig.get("region", None)
                    ebLogInfo(f"API Access Control is enabled in the region: {region}")

        if not  self.__disable_monitor:
            ebLogInfo('*** Starting Monitor')
            _cmd_list = ['bin/exacloud', '-al', 'localhost', '--monitor', 'start', '-as']

            # Add args that need to be propagated (e.g. --debug/--verbose)
            _cmd_list.extend(get_gcontext().mGetPropagateProcOptions())

            subprocess.run(_cmd_list, stdout=None, stderr=None)
            ebLogInfo('*** Done assigning Monitor')
        else:
            ebLogWarn('*** Monitor process is disabled by configuration')

        self.mSetReacheable(True)

        if get_gcontext().mCheckConfigOption('import_tabledata', 'True'):
            ebLogInfo("Attempting to import data from backup into MYSQL db.")
            _tables = []
            _tables = get_gcontext().mCheckConfigOption('import_tabledata_tables')
            ebLogInfo(f"List of tables to backup: {_tables}")

            for _table in _tables:
                ebLogInfo(f"Attempting to import data for {_table} table from backup.")
                _ret = _db.mImportDataIntoTable(_table)
                if _ret:
                    ebLogInfo(f"Successfully imported data for {_table} table.")
                else:
                    ebLogError(f"Failed to import data for {_table} table.")

        # Register itself(exacloud instance) with proxy.
        if self.__proxy_client:
            self.__proxy_client.mSendOperation(ProxyOperation.REGISTER)

        if self.__args_options.proxy:
            #Update requestuuidtoexacloud table. Set all entries with status as Pending to InitialReqDone so that new workers could be started
            #to poll for the status request from exacloud agents.
            ebLogInfo("Updating requestuuidtoexacloud table, resetting reqstatus option for Pending requests.")
            _db.mUpdateUUIDtoexacloudForAgentStart()

            #For Agent startup if any entries in requestuuidtoexacloud table is in InitialReqPending state, a worker needs to be assgined to work on that request.
            _entries = _db.mSelectAllFromRequestuuidtoExacloud(aReqStatus="InitialReqPending")
            _lock = Lock()
            if len(_entries) != 0:
                for _entry in _entries:
                    ebLogInfo('Request with UUID: {0} is being dispatched to a new worker.'.format(_entry[0]))
                    _req = ebProxyJobRequest("DUMMY.COMMAND", {'uuid':_entry[0]}, _db)
                    _req.mLoadRequestFromDB(_entry[0])
                    dispatchJobToWorker(_req, _lock)

        if get_gcontext().mCheckConfigOption('backup_configuration_during_start', 'True') and not mBackupFile(os.path.join(get_gcontext().mGetBasePath(), 'config/exabox.conf')):
            ebLogAgent('CRT','Shutting down exacloud agent services due to error in backing up exabox configuration file.')
            gGlobalShutdown = True

        while not gGlobalShutdown:

            # Check Agent DB
            _rc = _db.mAgentStatus(_agent_id)
            if _rc is None or _rc[2] == 'stopped':
                gGlobalShutdown = True
            else: # Sleep (only if not stopped for responsiveness)
                time.sleep(5)

        ebLogAgent('NFO','*** Agent Main Loop exited ***')

        self.__main_loop_exited = True

        # Agent STOP MUST be called from MAIN agent
        # as it have the worker factory and the subprocesses
        self.mAgent_Stop()

        # Agent Cleanup/Stop will called in shutdown_all() from main exabox

    def mAgentDBShutdown(self):

        _db = ebGetDefaultDB()
        _rc = _db.mAgentStatus(self.__agent_id)
        if _rc is not None and _rc[2] == 'stopped':
            ebLogAgent('NFO', '*** Agent shutdown already requested')
        else:
            _db.mStopAgent(self.__agent_id)

    def mAgent_Shutdown(self):

        self.mAgentDBShutdown()

        global gGlobalShutdown
        gGlobalShutdown = True

    def mAgent_Stop(self):

        if self.__stopped:  # idempotency
            return

        _db = ebGetDefaultDB()
        # Deregister itself(exacloud instance) with proxy.
        if self.__proxy_client:
            ebLogInfo("Deregister itself(exacloud instance) with proxy")
            self.__proxy_client.mSendOperation(ProxyOperation.DEREGISTER)

        ebLogInfo('Stopping special workers.')
        _process_pid_mapping = _db.mGetSpecialWorkerPIDs()
        _processes = _process_pid_mapping.keys()
        if len(_processes) == 0:
            ebLogWarn("No special workers are registered with this exacloud agent.")
        else:
            for _process in _processes:
                _pid = _process_pid_mapping[_process]
                ebLogInfo(f"Sending signal {signal.SIGINT} to pid {_pid} for {_process} process.")
                try:
                    os.kill(_pid,signal.SIGINT) #SIGINT for graceful stop
                except Exception as e:
                    ebLogError(f"Failed to message {_process} process. Exception detail: {e}")
        #TODO: this can be further enhanced to check the supervisor worker entry in the workers table.
        ebLogInfo('Waiting for 20 seconds for supervisor process to stop.')
        time.sleep(20)

        # Stop agent rest listener (can ONLY be done on MAIN agent)
        ebLogInfo('Stopping REST listener on subprocesses')

        # Stop agent rest listener
        ebLogInfo('Agent stopped...')
        if self.__restlistener:
            self.__restlistener.mStopRestListener()

        # Stop worker factory
        ebLogInfo('Worker Factory stopping...')
        if self.__workerFactory:
            self.__workerFactory.mShutdownFactory()
        ebLogInfo('Worker Factory stopped...')

        # Stop proxy heartbeat to exacloud instances.
        # TODO check that stop correctly, not tested in START/STOP REFACTORING
        if self.__args_options.proxy:
            from exabox.proxy.heartbeat import stop
            stop()

        # Detach the logger
        if self.__agent_destination_handlers:
            ebLogDeleteLoggerDestination(ebGetDefaultLoggerName(), self.__agent_destination_handlers)

        self.__stopped = True
    
    def mAgentIsStopped(self):
        return self.__stopped

    @staticmethod
    def mPerformRequest(aUrl, aHost, aPort, form_data=None, isMock=False, mockReturn=None):

        if isMock:
            ebLogInfo("*** mPerformRequest mock response data: {}".format(mockReturn))
            return mockReturn

        _data = None
        _error = None
        _error_str = None

        # Issue Request
        try:
            _headers = {}
            _headers["Authorization"] = "Basic %s" % ebGetHTTPAuthStorage().mGetAdminCredentialForRequest()
            _headers["content-type"] = "application/json"
            if form_data:
                _data = HTTPSHelper.build_opener(\
                    aHost, aPort, 
                    aUrl, aData=form_data, aHeaders=_headers, aTimeout=60)
            else:
                _data = HTTPSHelper.build_opener(\
                    aHost, aPort, 
                    aUrl, aHeaders=_headers, aTimeout=60)


        except urllib.error.HTTPError as e:
            _error = '120'
            _error_str = str(e)
        except urllib.error.URLError as e:
            _error = '121'
            _error_str = str(e)
        except socket.error as e:
            ebLogWarn(str(e))
        except Exception as e:
            ebLogAgent('NFO', '*** urlopen error:{0} {1} {2}'.format(str(e), aUrl, _data))

        # Process Reply
        if not _error:
            _json = json.load(_data)
            ebLogAgent('NFO', '*** Response obtained: {}'.format(_json))
            return _json
        else:
            ebLogError("*** mPerformRequest Error code: {0}".format(_error))
            ebLogError("*** mPerformRequest Error details: {0}".format(_error_str))
            return None

    @staticmethod
    def mAgentForceKill(aOptions, aWorkersOnly=False, aSchedulerOnly=False, aSupervisorOnly=False, aDispatcherOnly=False, aWrkmanagerOnly=False):

        _extra_filter = None
        if aWorkersOnly:
            _extra_filter = 'wp'
        elif aSchedulerOnly:
            _extra_filter = 'scheduler'
        elif aSupervisorOnly:
            _extra_filter = 'supervisor'
        elif aDispatcherOnly:
            _extra_filter = 'dispatcher'
        elif aWrkmanagerOnly:
            _extra_filter = 'workermanager'

        _argOptions = aOptions
        _exacloudPath = sys.path[0]
        if not _argOptions.proxy:
            _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]
        else:
            _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exaproxy.primary")+16]

        _cmd_list = []
        _cmd_list.append(['/bin/ps', '-ax'])             #List all process
        _cmd_list.append(['/bin/grep', _exacloudPath])   #Filter the actual path
        _cmd_list.append(['/bin/grep', '-F' , '../exabox'])  #Match only exabox entries
        if _extra_filter:
            _cmd_list.append(['/bin/grep', _extra_filter])   #Extra filter
        _cmd_list.append(['/bin/awk', '{print $1}'])       #Get only the PID
        _cmd_list.append(['/bin/grep', '-v', str(os.getpid())]) #Remove self script

        try:
            for i in range(len(_cmd_list)):
                if i == 0:
                    _cmd_exec_first = subprocess.Popen(_cmd_list[i], stdout=subprocess.PIPE)
                else:
                    _cmd_exec_first = subprocess.Popen(_cmd_list[i], stdin=_cmd_exec_prev.stdout, stdout=subprocess.PIPE)
                _cmd_exec_prev = _cmd_exec_first
            if _cmd_exec_prev:
                _out, _err = wrapStrBytesFunctions(_cmd_exec_prev).communicate()
                if _cmd_exec_prev.returncode != 0:
                    # Last command is a grep, it will return not 0 if there is no process
                    ebLogInfo('*** All process are stopped, nothing to kill. filter:{}'.format(
                              _extra_filter or 'all'))
                else:
                    ebLogInfo('*** Apply Kill of Exacloud Processes: {}'.format(
                               _extra_filter or 'all'))
                    for _pid in _out.split('\n'):
                        try:
                            if _pid:
                                os.kill(int(_pid), signal.SIGKILL)
                                ebLogInfo('Killed pid: {}'.format(_pid))
                        except ProcessLookupError:
                            ebLogWarn(f'Process with pid: {_pid} does not exists anymore')
                        except PermissionError as e:
                            ebLogWarn(f'Signalling process with pid: {_pid} returned a PermissionError: {e}')
                        except ValueError as e:
                            ebLogError('Unexpected output of kill commands {}\n Output:{}'\
                                       .format(_cmd_list,_out))
                            raise

                if _extra_filter is None or _extra_filter == "supervisor":
                    ebLogInfo("Attempting to clean up supervisor recovery cron setup.")
                    _removal_status = ebSupervisor.mDeleteCrontab()
                    if _removal_status:
                        ebLogInfo("Successfully removed supervisor recovery crontab setup.")
                    else:
                        ebLogWarn("Failed to removed supervisor recovery crontab setup or crontab setup doesn't exist.")

        except Exception as e:
            ebLogError("*** exception while Apply Kill of Exacloud Processes: {}\nStack: {}".format(
                       e, traceback.format_exc()))

    @staticmethod
    def mAgentGracefulStop(aOptions=None):

        _argOptions = aOptions
        # Issue stop agent
        _options = nsOpt({'agent': 'stop'})
        _client = ebExaClient()
        _client.mIssueRequest(aOptions=_options)
        _client.mWaitForCompletion()
        _response = _client.mGetJsonResponse()
        _agentcfg = ebGetClientConfig()
        if _response['success'] == 'False': #agent doesn't respond
            ebLogInfo('*** Could not contact Agent (%s, %d)- either not running or not reachable' % (_agentcfg[0], int(_agentcfg[1])))

        else:
            ebLogInfo('*** Agent shutdown is in progress (stop)')

            # Wait for agent to shutdown
            _loop = True
            _client.mSetQuietMode() # skip errors triggered by urlopen

            _count = 0
            _wait = 5
            while _loop:

                _options = nsOpt({'agent': 'status'})
                _client.mIssueRequest(aOptions=_options)
                _response = _client.mGetJsonResponse()
                _agentcfg = ebGetClientConfig()

                if _response['success'] == 'False': #agent doesn't respond
                    ebLogInfo('*** Agent (%s, %d) has shutdown' % (_agentcfg[0], int(_agentcfg[1])))
                    _loop = False

                else:
                    time.sleep(_wait)
                    ebLogInfo('*** Agent shutdown is in progress (status)')

                _count += 1

                if _count >= (60/_wait) * 3: #3 minutes
                    _loop = False
                    ebLogInfo("*** Agent timeout on shutdown")
                    ebAgentDaemon.mAgentForceKill(_argOptions)


    def mAgent_Status(self):
        pass

    def mCheckAgentState(self):

        _db = ebGetDefaultDB()
        try:
            _orphan_req_list = _db.mOrphanRequests()
            for _req in _orphan_req_list:
                ebLogWarn(f"Orphaned request: {_req[0]} STATE: Pending.")
        except:
            ebLogError('*** DB access critical error please review DB integrity')
            raise

#EOF
