# -*- coding: utf-8 -*-
"""

The :program:`exabox` umbrella command.

.. program:: exabox

"""

import os
import sys
import uuid
import time
import socket
import signal
import traceback
import threading
import json
import subprocess
from  subprocess import PIPE
import shlex
from enum import Enum
from typing import Any,Iterator
import psutil

from exabox.agent.DBService import ExaMySQL, is_mysql_running
from exabox.core.Node import exaBoxNode
from exabox.core.Core import exaBoxCoreInit, exaBoxCoreShutdown
from exabox.ovm.vmcontrol import ebVgLifeCycle
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogError, ebLogDebug, ebLogInfo, ebLogWarn, ebLogInit, ebLogFinalize, ebLogCrit
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.ovm.clumisc import AgentWorkerPIDListing
from exabox.core.Threads import ebThreadStartHangMonitoring
from exabox.publish.Publish import exaBoxPackage
from exabox.agent.Agent import ebAgentDaemon
from exabox.agent.AgentSignal import AgentSignal, AgentSignalEnum
from exabox.agent.AuthenticationStorage import ebBasicAuthStorage
from exabox.core.DBStore import get_db_version, ebInitDBLayer, ebShutdownDBLayer, ebGetDefaultDB
from exabox.agent.Client import ebExaClient, ebGetClientConfig
from exabox.tools.scripts import ebScriptsEngineInit
from exabox.config.Config import ebJsonConfigFileReader
from exabox.agent.Worker import ebWorkerDaemon, ebWorkerFactory, ebWorker
from exabox.agent.WClient import ebWorkerCmd
from exabox.agent.Supervisor import ebSupervisor, supervisor_running
from exabox.agent.Dispatcher import ebDispatcher, dispatcher_running
from exabox.agent.WorkerManager import ebWorkermanager, workermanager_running
from exabox.agent.Scheduler  import ebScheduler, scheduler_running
from exabox.agent.ScheduleRegistry  import register_schedule_jobs
from exabox.ovm.rackcontrol import ebRackControl
from exabox.agent.ebJobRequest import nsOpt
from exabox.infrapatching.core.cludispatcher import ebCluPatchDispatcher
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.CrashDump import CrashDump
from exabox.network.dns.DNSConfig import ebDNSConfig
from exabox.agent.AuthenticationStorage import ebConvertToWalletStorage,ebConfigAuthStorage
from exabox.core.DBLockTableUtils import sDBLockCleanAllLeftoverLocks
from exabox.proxy.ECAgentOperationUpdate import fetch_update_ecregistrationinfo
from exabox.proxy.router import Router
from exabox.proxy.heartbeat import ProxyHeartbeat
from exabox.agent.ProxyClient import ProxyClient, ProxyOperation
from exabox.tools.ebXmlGen.ebFacadeXmlGen import ebFacadeXmlGen
from exabox.exakms.ExaKmsSingleton import ExaKmsSingleton
from exabox.exakms.ExaKmsEndpoint import ExaKmsEndpoint
from exabox.jsondispatch.jsondispatch import ebJsonDispatcher
from exabox.utils.oci_region import load_oci_region_config, parse_region_info, update_oci_config
from exabox.sop.soputils import process_sop_request
import exabox.exadbxs.edv as edv

__all__ = ['main']


class ebRState(Enum):
    ''' List of ResourceState'''
    STARTED = 'Started'
    STOPPED = 'Stopped'
    STARTING = 'Starting'
    STOPPING = 'Stopping'
    UNKNOWN  = 'Unknown'

class ebRType(Enum):
    ''' List of ResourceType '''
    # In the future, if DB orchestration is needed it can be
    # tracked as a resource
    WORKER   = 'worker'
    AGENT    = 'agent'
    SUPERVISOR = 'supervisor'
    DISPATCHER = 'dispatcher'
    WRKMANAGER = 'workermanager'
    SCHEDULER  = 'scheduler'

class ebResource():
    """ 
      Resource Instance, used to track the startup/stop flow
      Every resources started have to be tracked, that allow for
      cleanup for both Ctrl-C during startup/unexpected failures.
      And also cover regular resources startup/shutdown as
      Agent and Worker process will go back to the agent once they exit their
      main loop.
    """
    def __init__(self, aType : ebRType,
                 aState : ebRState = ebRState.UNKNOWN,
                 aHandle : Any = None):#An interface for handle could be created
        self.__type = aType
        self.__state = aState
        self.__handle = aHandle

    def mUpdateState(self, aState :ebRState, aHandle : Any) -> None:
        self.__state = aState
        if aHandle:
            self.__handle = aHandle

    def mGetHandle(self) -> Any:
        return self.__handle

    def mGetType(self) -> ebRType:
        return self.__type

    def __str__(self) -> str:
        return 'Resource Type: {}, Resource State:{}, Handler:{}'.format(
                self.__type, self.__state, self.__handle)

    def mIsNotStopped(self) -> bool:
        return self.__state != ebRState.STOPPED


class ebExaboxState():
    """  
        Class to keep track of any cleanup / state management.
        Stateless commands will not put any State here.
        But any operation like Starting Agent/Worker/DB should be tracked
    """
    def __init__(self):
        self.__resources_touched = {}
        self.__skip_cleanup = False

    def mSkipCleanup(self) -> bool:
        return self.__skip_cleanup

    def mSetSkipCleanup(self) -> None:
        self.__skip_cleanup = True
    
    def mUpdateResourceState(self, aRType : ebRType,
                             aRState :ebRState,
			     aRHandler : Any = None) -> None:
        if aRType in self.__resources_touched:
            self.__resources_touched[aRType].mUpdateState(aRState,aRHandler)
        else:
            self.__resources_touched[aRType] = ebResource(aRType, aRState, aRHandler)
    
    def mGetResourcesToBeStopped(self) -> Iterator[ebResource]:
        return filter(ebResource.mIsNotStopped, self.__resources_touched.values())

    def __str__(self) -> str:
        return 'noCleanup:{}, resources:{}'.format(self.__skip_cleanup,
                {k:str(v) for (k,v) in self.__resources_touched.items()})


def clean_environment():
    #
    # Make sure TMPDIR env variable is valid in case some utility attempts to use it, e.g. mktemp
    #
    _tmpdir = os.getenv("TMPDIR")
    if _tmpdir:
        if os.path.isdir(_tmpdir):
            print("* INFO * *** Using TMPDIR value: {0}".format(_tmpdir))
        else:
            del os.environ['TMPDIR']
            print("* WARN * *** Unsetting TMPDIR environment varible. Directory {0} is invalid".format(_tmpdir))

def validate_user() -> None:
    """Terminate program if not running as the correct user."""

    uid = os.geteuid()

    if uid == 0: # pragma: no cover
        print('Exacloud / Exabox cannot be run as root.  Exiting.')
        sys.exit(1)

    # Check that current user is the owner of <exacloud_home>/exabox.
    #
    # Assume __file__ will always be <exacloud_home>/exabox/bin/exabox.py
    exabox_dir = os.path.abspath(f"{__file__}/../../../exabox")
    exabox_owner_uid = os.stat(exabox_dir).st_uid

    if uid != exabox_owner_uid: # pragma: no cover
        print(f"Exacloud / Exabox can only be run as user '{exabox_owner_uid}' "
              f"but we are running as user '{uid}'.  Exiting.")
        sys.exit(1)


def shutdown_all(aExaboxState):
    ebContext = get_gcontext()
    if not ebContext: # pragma: no cover
        return # Failed in argument parsing, nothing to clean
    options = ebContext.mGetArgsOptions()
    _debug = False

    # Mysql-db calls (start, status & stop) do not create
    if options.mysql_db:
        return

    if options.debug:
        print('shutdown_all: Debugging mode enabled')
        print('shutdown_all: aExaboxState: {}'.format(aExaboxState))
        _debug = True

    if aExaboxState.mSkipCleanup():
        return 

    _running_resources = aExaboxState.mGetResourcesToBeStopped()

    # Define subworker (scheduler/supervisor) timeout
    _coptions = get_gcontext().mGetConfigOptions()
    _timeout_subworkers = int(_coptions.get('timeout_subworkers', 20))

    for _r in _running_resources:
        _handle = _r.mGetHandle()
        _type   = _r.mGetType()
        if _type == ebRType.AGENT:
            if _handle and not _handle.mAgentIsStopped():
                _handle.mAgent_Stop()                
            else:
                _uuid = str(_coptions["agent_id"])
                _db = ebGetDefaultDB()
                _db.mStopAgent(aAgentId=_uuid)
                
        elif _type == ebRType.SCHEDULER:
            if _handle and _handle.mIsRunning():
                _handle.mStop()
            else:
                # Give time for clean stop
                _start_time = time.time()
                _scheduler_found = False
                while (time.time() - _start_time < _timeout_subworkers):
                    pid_scheduler = scheduler_running()
                    if not pid_scheduler:
                        break
                    elif not _scheduler_found:
                        _scheduler_found = True
                    time.sleep(1)
                if pid_scheduler:
                    os.kill(int(pid_scheduler), signal.SIGKILL)
                elif not _scheduler_found: #if DB Pid not match/found 
                    ebAgentDaemon.mAgentForceKill(options, aSchedulerOnly=True)

        elif _type == ebRType.DISPATCHER:
            print('ebRType.DISPATCHER')
            if _handle and _handle.mIsRunning():
                print('Stopping dispatcher')
                _handle.mStop()
            else:
                # Give time for clean stop (To be factorized)
                _dispatcher_found = False
                _start_time = time.time()
                while (time.time() - _start_time < _timeout_subworkers):
                    pid_dispatcher = dispatcher_running()
                    if not pid_dispatcher:
                        break
                    elif not _dispatcher_found:
                        _dispatcher_found = True
                    time.sleep(1)
                if pid_dispatcher:
                    print('killing dispatcher')
                    os.kill(int(pid_dispatcher), signal.SIGKILL)
                elif not _dispatcher_found:
                    print('force kill')
                    ebAgentDaemon.mAgentForceKill(options, aDispatcherOnly=True)

        elif _type == ebRType.WRKMANAGER:
            print('ebRType.WRKMANAGER')
            if _handle and _handle.mIsRunning():
                print('Stopping workermanager')
                _handle.mStop()
            else:
                # Give time for clean stop (To be factorized)
                _workermanager_found = False
                _start_time = time.time()
                while (time.time() - _start_time < _timeout_subworkers):
                    pid_workermanager = workermanager_running()
                    if not pid_workermanager:
                        break
                    elif not _workermanager_found:
                        _workermanager_found = True
                    time.sleep(1)
                if pid_workermanager:
                    print('killing workermanager')
                    os.kill(int(pid_workermanager), signal.SIGKILL)
                elif not _workermanager_found:
                    print('force kill')
                    ebAgentDaemon.mAgentForceKill(options, aWrkmanagerOnly=True)

        elif _type == ebRType.SUPERVISOR:
            if _handle and _handle.mIsRunning():
                _handle.mStop()
            else:
                # Give time for clean stop (To be factorized)
                _supervisor_found = False
                _start_time = time.time()
                while (time.time() - _start_time < _timeout_subworkers):
                    pid_supervisor = supervisor_running()
                    if not pid_supervisor:
                        break
                    elif not _supervisor_found:
                        _supervisor_found = True
                    time.sleep(1)
                if pid_supervisor:
                    os.kill(int(pid_supervisor), signal.SIGKILL)
                elif not _supervisor_found:
                    ebAgentDaemon.mAgentForceKill(options, aSupervisorOnly=True)

        elif _type == ebRType.WORKER:
            # Try first graceful shutdown with handles
            if _handle:
                _handle.mWorker_Stop()
            else:
            # If we get there, it means Worker Start not completed or shutdown failed. => KILL
                sDBLockCleanAllLeftoverLocks()
                ebAgentDaemon.mAgentForceKill(options, aWorkersOnly=True)
                _db = ebGetDefaultDB()
                _db.mClearWorkers()
                _db.mClearRegistry()
                _db.mDeleteAllLocks()

        # Cleanup resource state
        aExaboxState.mUpdateResourceState(_type, ebRState.STOPPED)
        
    if (get_db_version() != 3) and ebGetDefaultDB():
        ebShutdownDBLayer() # pragma: no cover

    if options.debug:
        ebLogInfo('$ Shutdown all completed')


def display_version_banner(aCoreContext, isProxy=False):
    if isProxy:
        print('$ ExaProxy') # pragma: no cover
    else:
        print('$ ExaCloud')
    print('  Core Version   : %s (%s)' % aCoreContext.mGetVersion())
    print('  Hostname       : %s' % socket.getfqdn())
    print('  ECS Label      : %s' % aCoreContext.mGetLabel())
    print('  Base Path      : %s' % aCoreContext.mGetContext().mGetBasePath())
    if not isProxy:
        print('  OEDA Path      : %s' % aCoreContext.mGetContext().mGetOEDAPath())
    print('  Log  Path      : %s' % aCoreContext.mGetContext().mGetLogPath())


def execute_from_commandline(aArgv, aExaboxState):

    ebCore = exaBoxCoreInit(aOptions={'argv': aArgv})

    ebContext = get_gcontext()
    options = ebContext.mGetArgsOptions()

    # Initialize Loging Facility/Mgr
    ebLogInit(ebContext, options)

    if options.proxy and get_db_version() != 3: # pragma: no cover
        ebLogError('Proxy needs to be enabled with MySQL.')
        sys.exit(0)

    # Prevents for stop and status calls from starting MySQL
    if get_db_version() == 3 and not is_mysql_running():
        if options.agent and options.agent in ['stop', 'status'] :
            ebLogInfo("*** MySQL is STOPPED, please start it with './bin/exacloud --mysql-db start' and reissue command")
            ebLogInfo("*** ExaCloud agent is STOPPED")
            return
    
    # Start MySQL at the start
    if options.agent and options.agent == 'start':
        ebInitDBLayer(ebContext, options)
        if get_db_version() == 3:
            _exabox_conf = ebContext.mGetConfigOptions()
            ExaMySQL(_exabox_conf).mInit()

    # Display version and exit (if requested) - Skip DB initialization
    if options.version:
        display_version_banner(ebCore, options.proxy)
        return

    if options.shortversion:
        print(('%s (%s)' % ebCore.mGetVersion()))
        return

    if options.mysql_db:
        _return = 0
        _exabox_conf = ebContext.mGetConfigOptions()
        _driver = ExaMySQL(_exabox_conf)
        if options.mysql_db == 'start':
            ebLogInfo("*** ExaCloud MySQL service will be STARTED")
            _driver.mInit()
        elif options.mysql_db == 'stop':
            ebLogInfo("*** ExaCloud MySQL service will be STOPPED")
            if _driver.mManualStop():
                ebLogInfo("*** ExaCloud MySQL service was STOPPED")
            else:
                ebLogError("*** ExaCloud MySQL service is still RUNNING, " + \
                    "please check no exacloud process are still running, " + 
                    "then try stop again")
                _return = 1
        elif options.mysql_db == 'status':
            if _driver.mIsRunning():
                ebLogInfo("*** ExaCloud MySQL service is RUNNING")
            else:
                ebLogInfo("*** ExaCloud MySQL service is STOPPED")
                _return = 1

        elif options.mysql_db == 'prechecks':
            ebLogInfo("*** Performing ExaCloud MySQL prechecks")
            _rc = _driver.mPrechecks()
            ebLogInfo(f"MySQL prechecks returned with exit code {_rc}")

        return _return

    # Initialize DB only in agent mode
    if options.agent or options.worker:
        ebInitDBLayer(ebContext, options)
        _db = ebGetDefaultDB()

        _db.mCreateAgentTable()
        _db.mCreateAgentSignalTable()
        _db.mCreateRequestsTable()
        _db.mCreateRequestsArchiveTable()
        _db.mCreateWorkersTable()
        if options.agent in ["start", "stop"]:
            _db.mReleaseWorkerSyncLockForAllWorkersDuringStart()
        _db.mCreateClusterStatusTable()
        _db.mCreatePatchListTable()
        _db.mCreateIBFabricLocksTable()
        _db.mCreateIBFabricClusterTable()
        _db.mCreateIBFabricIBSwitchesTable()
        _db.mCreateClusterPatchOperationsTable()
        _db.mCreateInfraPatchingTimeStatsTable()
        _db.mCreateFilesTable('ecra_files')
        _db.mCreateFilesTable('exacloud_files')
        _db.mCreateMockCallTable()
        _db.mCreateScheduleTable()
        _db.mCreateScheduleArchiveTable()
        _db.mCreateExawatcherTable()
        _db.mCreateCCATable()
        _db.mCreateLocksTable()
        _db.mCreateSELinuxPolicyTable()
        _db.mCreateErrCodeTable()
        _db.mCreateEnvironmentResourceDetails()
        _db.mCreateRunningDBsList()
        _db.mCreateAsyncProcessTable()
        _db.mCreateDataCacheTable()
        _db.mCreateExaKmsHistoryTable()
        _db.mCreateProfilerTable()
        if options.agent:
            _db.mDelDataCache("region")


    if options.proxy:
        _db = ebGetDefaultDB()
        _db.mCreateProxyRequestsTable()
        _db.mCreateExacloudInstanceTable()
        _db.mCreateUUIDToExacloudInstanceTable()
        if options.migrateproxydb:
            if not _db.mMigrateProxyDB(options.migrateproxydb):
                return 1

    # Banner
    if not options.jsonmode:
        display_version_banner(ebCore, options.proxy)

    # exaBoxTimeout( aTimeOut=30 ).mStart()
    _config_file = get_gcontext().mGetConfigOptions()

    # If hostname is not supplied check if there is a default hostname in the
    # exabox conf.
    if not options.proxy and not options.hostname and 'oeda_host' in _config_file.keys():
        options.hostname = _config_file['oeda_host']

    # Initialize script Engine
    if not options.proxy and options.scripts or ('enable_scripts' in _config_file.keys()):
        if options.scripts:
            ebScriptsEngineInit(options.scripts)
        else:
            ebScriptsEngineInit(_config_file['enable_scripts'])
        if options.debug:
            ebLogInfo('ebScriptEngine Initialization done.')

    # --region-info -ri
    #
    # Init OCI region db cache, from base64 argument or directly from Cavium
    #
    #{"realmDomainComponent": "oracleiaas.com", "realmKey": "R1_ENVIRONMENT", "regionIdentifier": "r1", "regionKey": "SEA"}
    #base64 encoded
    #eyJyZWFsbURvbWFpbkNvbXBvbmVudCI6ICJvcmFjbGVpYWFzLmNvbSIsICJyZWFsbUtleSI6ICJSMV9FTlZJUk9OTUVOVCIsICJyZWdpb25JZGVudGlmaWVyIjogInIxIiwgInJlZ2lvbktleSI6ICJTRUEifQ==
    is_oci_exacc = _config_file.get('ociexacc', False)
    is_ocps_json = _config_file.get('ocps_jsonpath', None)
    if is_oci_exacc and is_ocps_json and is_ocps_json.strip():
        ebLogInfo('Skip OCI region check for ExaCC-CPS.')
    else:
        if (options.agent or options.proxy) and options.agent == 'start':
            if options.region_info:
                _region_info = parse_region_info(options.region_info)
                update_oci_config(_region_info)
            else:
                load_oci_region_config()

    # Init ExaKMS
    get_gcontext().mSetExaKmsSingleton(ExaKmsSingleton())

    # --rack
    if not options.proxy and options.rackcmd:
        ebInitDBLayer(ebContext, options)
        _rackControl = ebRackControl(options)
        _rackControl.mExecute()
        return

    #--eccontrol
    if options.eccontrol:
        options.proxy = True
        ebInitDBLayer(ebContext, options)
        fetch_update_ecregistrationinfo(options)
        return

    # -id and -cf
    if not options.proxy and options.id is not None and options.configpath is None:
        _cfpath = None
        _cfid   = options.id
        if os.path.exists('clusters/cluster-'+_cfid):
            _cfpath = 'clusters/cluster-'+_cfid+'/config/'+_cfid+'.xml'
            if os.path.exists(_cfpath):
                options.configpath = _cfpath
                options.id = None
            else:
                _cfpath = None
        if _cfpath is None:
            ebLogWarn('XML configpath conversion from id failed')
            return -1
        else:
            ebLogInfo('*** CF/ID: %s' % (_cfpath))

    # --tm
    if not options.proxy and options.threadmonitor:
        ebThreadStartHangMonitoring(int(options.threadmonitor))
        ebLogInfo('*** Threads hang detection has been activated...')

    # --json
    if not options.proxy and options.jsonmode:
        # Force redirect to log file instead of console
        pass

    # -jc
    if not options.proxy and options.jsonconf:
        options.jsonconf = ebJsonConfigFileReader(options.jsonconf)

    # -al/-agentloc
    # implicit entry point for -m/-monitor
    if options.agenthostname:
        _status = options.status
        _client = ebExaClient()
        _client.mIssueRequest()
        time.sleep(3)
        if not getattr(options, "async"):
            _client.mWaitForCompletion()
        if _status:
            _client.mDumpJson()
        return

    # --status
    # Fallback if no -al/-agentloc provided : default to conf.agent_host
    if options.status:
        _client = ebExaClient()
        _client.mIssueRequest()
        if not getattr(options, "async"):
            _client.mWaitForCompletion()
        _client.mDumpJson()
        return

    # --workercmd
    if options.worker_cmd:
        if not options.worker_port: # pragma: no cover
            ebLogError('Worker port is required to issue worker request')
            return
        _workercmd = ebWorkerCmd()
        _workercmd.mIssueRequest()
        _json = _workercmd.mWaitForCompletion()
        print(_json)
        return

    # --worker
    if options.worker:
        if not options.worker_port: # pragma: no cover
            ebLogError('Worker port is required to start a background worker')
            return 1
        
        _workerHandle = ebWorkerDaemon()
        aExaboxState.mUpdateResourceState(ebRType.WORKER,ebRState.STARTING,_workerHandle)
        signal.signal(signal.SIGINT, _workerHandle.mWorker_SigHandler)
        signal.signal(signal.SIGTERM, _workerHandle.mWorker_SigHandler)
        _rc = _workerHandle.mWorker_Start()
        aExaboxState.mUpdateResourceState(ebRType.WORKER,ebRState.STARTED,_workerHandle)
        return _rc
    
    if options.proxy and options.heartbeat:
        _proxy_hb = ProxyHeartbeat()
        _proxy_hb.mStart()
        return

    if not options.proxy and options.dispatcher:
        dispatcher = ebDispatcher()
        aExaboxState.mUpdateResourceState(ebRType.DISPATCHER,ebRState.STARTING,dispatcher)
        dispatcher.mStart()
        aExaboxState.mUpdateResourceState(ebRType.DISPATCHER,ebRState.STARTED,dispatcher)
        return

    if not options.proxy and options.workermanager:
        workermanager = ebWorkermanager()
        aExaboxState.mUpdateResourceState(ebRType.WRKMANAGER,ebRState.STARTING,workermanager)
        workermanager.mStart()
        aExaboxState.mUpdateResourceState(ebRType.WRKMANAGER,ebRState.STARTED,workermanager)
        return

    # --supervisor
    if not options.proxy and options.supervisor:
        supervisor = ebSupervisor()
        aExaboxState.mUpdateResourceState(ebRType.SUPERVISOR,ebRState.STARTING,supervisor)
        supervisor.mStart()
        aExaboxState.mUpdateResourceState(ebRType.SUPERVISOR,ebRState.STARTED,supervisor)
        return

    # --scheduler
    if not options.proxy and options.scheduler:
        # Register jobs to scheduler
        register_schedule_jobs()
        scheduler = ebScheduler()
        aExaboxState.mUpdateResourceState(ebRType.SCHEDULER,ebRState.STARTING, scheduler)
        scheduler.mStart()
        aExaboxState.mUpdateResourceState(ebRType.SCHEDULER,ebRState.STARTED, scheduler)
        return

    # --agent
    if options.agent:
        # In agent mode many options are not valid any more.
        # scripts/status/async/ kvl/pvc/pk/pwl/ssk/clh/
        if not options.proxy and options.scripts or getattr(options, "async") or options.clusterctrl or options.vmctrl or \
                options.installpkg or options.setupssh or options.pwdless: # pragma: no cover
            ebLogError('Invalid combination of command line options in --agent mode.')
            return

        def agentStartInternal():
            #
            # Check if Agent is already running
            #
            _options = nsOpt({'agent': 'start'})
            _client = ebExaClient()
            _response = {}
            try:
                _client.mIssueRequest(aOptions=_options)
                _client.mWaitForCompletion()
                _response = _client.mGetJsonResponse()
            except: # pragma: no cover
                _response['success'] = 'False'
                ebLogWarn("Agent verification call failed.")
            _agentcfg = ebGetClientConfig()
            if not options.proxy:
                #
                # Pre-Check OEDA (connect to OEDA hosting server and invoke OEDA/version
                #
                node = exaBoxNode(ebContext, aLocal=True)
                try:
                    node.mConnect(aHost=options.hostname)
                except Exception as e: # pragma: no cover
                    ebLogCrit('Connection to OEDA host failed. Agent can not start')
                    return
                cluhandle = exaBoxCluCtrl(aCtx=ebContext, aNode=node)
                cluhandle.mDispatchCluster('version', options)
                node.mDisconnect()
            #
            # Start Agent
            #
            if _response['success'] == 'True':
                ebLogWarn('*** Agent ({}, {}) is already running ***'.format(_agentcfg[0], int(_agentcfg[1])))
            else:
                _agentHandle = ebAgentDaemon()
                aExaboxState.mUpdateResourceState(ebRType.AGENT,ebRState.STARTING,_agentHandle)
                _agentHandle.mAgent_Start()
                aExaboxState.mUpdateResourceState(ebRType.AGENT,ebRState.STARTED,_agentHandle)

        def agentReloadInternal():

            all_workers_str = _db.mDumpWorkers()
            all_workers_list = AgentWorkerPIDListing.getWorkerPIDs(all_workers_str)

            for workerPid in all_workers_list:
                _signal = AgentSignal(str(uuid.uuid1()), AgentSignalEnum.RELOAD.value, workerPid)
                _db.mInsertAgentSignal(_signal)

                ebLogInfo("Set Reload Tag to worker PID: {0}".format(workerPid))


        def agentStopInternal():
            #
            # Fetch current host/pid for the agent
            #
            _host = None
            _pid = None
            _options = nsOpt({'agent': 'status'})
            _client = ebExaClient()
            _db = ebGetDefaultDB()
            try:
                # REGISTER INTENT TO STOP ALL PROCESSES
                for _res in (ebRType.AGENT,     ebRType.WORKER,
                             ebRType.SUPERVISOR,ebRType.SCHEDULER, ebRType.DISPATCHER, ebRType.WRKMANAGER):
                    aExaboxState.mUpdateResourceState(_res,ebRState.STOPPING)

                _client.mIssueRequest(aOptions=_options)
            except Exception as e: # pragma: no cover
                ebLogWarn('Agent Stop: Request to query agent status failed: Exception:({})'.format(e))
                ebLogWarn('Taking crashdump and force kill exacloud stack')
                # Log exception context/Stack trace to log/crash directory
                with CrashDump(logFx=ebLogError) as c:
                    c.ProcessException()
                if options.killworkers:
                    ebAgentDaemon.mAgentForceKill(aOptions=options) # this will kill all exacloud process
                return

            _response = _client.mGetJsonResponse()
            _agentcfg = ebGetClientConfig()

            if _response['success'] == 'False':
                ebLogInfo('*** Could not contact Agent (%s, %d)- either not running or not reachable' %(_agentcfg[0], int(_agentcfg[1])))
                if options.killworkers:
                    ebAgentDaemon.mAgentForceKill(aOptions=options)
                return
            else:
                _host, _pid = _agentcfg[0], int(_agentcfg[1]) #_pid is actually port number...
                aExaboxState.mUpdateResourceState(ebRType.AGENT,ebRState.STOPPED)

            # Check for available workers (active and idle), kill them if -kw flag is set
            active_workers_str = _db.mDumpActiveWorkers() #get workers that are NOT in an idle state
            active_workers_list = AgentWorkerPIDListing.getWorkerPIDs(active_workers_str) #get PIDs of active 'worker/supervisor' processes in this instance
            active_workers_str = active_workers_str.replace("),(","\n").replace("u'","").replace("'","")[2:-3] #format for readability

            all_workers_str = _db.mDumpWorkers() #get all current workers regardless of state
            all_workers_list = AgentWorkerPIDListing.getWorkerPIDs(all_workers_str) #get PIDs of all 'worker/supervisor' processes in this instance
            all_workers_str = all_workers_str.replace("),(","\n").replace("u'","").replace("'","")[2:-3] #format for readability

            #
            # Branch agent stop procedure according to flags
            #
            graceful_stop = False

            def mStopWorkers(all_workers_list, all_workers_str, active_workers_list, active_workers_str, force_kill=False):

                if len(all_workers_list)>0:

                    if len(active_workers_list)>0:
                        if options.proxy:
                            ebLogInfo('There are workers in progress, shutting down the proxy agent at this time could result in unexpected failures reported .\nList of Workers in progress:\n'+active_workers_str)
                        else:
                            ebLogInfo('There are workers in progress, shutting down the exacloud agent at this time could result in provisioning failures reported from SM / SDI / ECRA.\nList of Workers in progress:\n'+active_workers_str)

                    if options.killworkers or force_kill:

                        #Release all dom0 lock if they exists
                        if not options.proxy:
                            sDBLockCleanAllLeftoverLocks()
                        
                        #kill all workers regardless of state
                        ebLogInfo('Workers forcekill is in progress...')
                        # Sanitizing process ids
                        all_workers_list_str = map(str, all_workers_list)
                        _tmp_all_workers_list = [_worker for _worker in all_workers_list_str if _worker.isdigit()]
                        executeLocal('kill -9 '+' '.join(_tmp_all_workers_list))
                        
                        # Ensure there is no Workers remaining 
                        ebAgentDaemon.mAgentForceKill(options, aWorkersOnly=True)
                        aExaboxState.mUpdateResourceState(ebRType.WORKER,ebRState.STOPPED)
                                                
                        _db.mClearRegistry() # Clear Registry if forcekill is used

                        #reset lists to empty
                        all_workers_list = list()
                        active_workers_list = list()
                        all_workers_str = ""
                        active_workers_str = ""

            def mForceShutdown(active_workers_list):
                if len(active_workers_list)>0:
                    ebLogInfo('Agent shutdown is in progress. Workers in progress will be ignored...\nTo forcekill workers, use -kw flag.')
                    # Since fsd flag is used, we must leave old workers running (forcekill (kw) flag must be used to kill them)
                    aExaboxState.mUpdateResourceState(ebRType.WORKER,ebRState.STOPPED)
                else:
                    ebLogInfo('Agent shutdown is in progress...')

            def mNormalShutdown(active_workers_list):
                if len(active_workers_list)>0:
                    ebLogInfo('Agent can\'t shutdown while there are workers in progress. Waiting for workers to finish...\nTo force agent immediate shutdown, use -fsd flag.')

                    _ctx = get_gcontext()

                    #--wait for workers to stop or timeout
                    timeout_counter = 0
                    while timeout_counter<20: #increase if timeout should be longer. 20 seconds is default.

                        time.sleep(1)
                        active_workers = []
                        active_workers_str = ""
                        try:
                            for pid in active_workers_list:
                                if psutil.pid_exists(int(pid)):
                                    cmdline_opts = psutil.Process(int(pid)).cmdline()
                                    cmdline_opts_str = " ".join(cmdline_opts)
                                    if '-w' in cmdline_opts and _ctx.mGetBasePath() in cmdline_opts_str:
                                        active_workers += [cmdline_opts_str]
                            active_workers_str = ",".join(active_workers) #check for active workers of this instance of EC
                        except Exception as ex:
                            ebLogError('Error while checking active workers list %s' % ex)
                            # This is the only case where the stop is deep into the code and we must not cleanup
                            aExaboxState.mSetSkipCleanup()
                            return False
                        if len(active_workers_str)==0:
                            break
                        timeout_counter+=1

                    if len(active_workers_str)==0:
                        return True
                    else: # pragma: no cover
                        ebLogInfo('Operation timed out. There are workers in progress. Agent can\'t be shut down.\nTo force agent immediate shutdown, use -fsd flag.')
                        # This is the only case where the stop is deep into the code and we must not cleanup
                        aExaboxState.mSetSkipCleanup()
                        return False
                else:
                    ebLogInfo('Agent shutdown is in progress.')
                    return True

            def startSwitchoverProxy(_primary_mysql_file_location):
                _standbyProxyLocation = options.standbyloc
                _primary_agent_port = _config_file['agent_port']
                _primary_worker_port = _config_file['worker_port']
                _primary_ec_agent_port = _config_file['ec_agent_port']
                _standbyProxyExaboxConfiguration = os.path.join(_standbyProxyLocation,"config/exabox.conf")
                _config_json = json.load(open(_standbyProxyExaboxConfiguration))
                _config_json['agent_port'] = _primary_agent_port
                _config_json['worker_port'] = _primary_worker_port
                _config_json['ec_agent_port'] = _primary_ec_agent_port
                with open(_standbyProxyExaboxConfiguration, "w") as outfile: 
                    json.dump(_config_json, outfile)

                _standbyproxystartcmd = os.path.join(_standbyProxyLocation,"bin/exaproxy") + " --proxy start -migrateproxydb " + _primary_mysql_file_location +" -da"
                _standbyproxystartcmd_list = shlex.split(_standbyproxystartcmd)
                proc = subprocess.Popen(_standbyproxystartcmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = proc.communicate()
                _status = proc.returncode
                if _status == 0:
                    print("Switchover proxy successfully started at base location: "+_standbyProxyLocation)
                else:
                    print("Switchover proxy could not be started due to errors.")

            #Main Shutdown Part
            mStopWorkers(all_workers_list, all_workers_str, active_workers_list, active_workers_str)

            _primary_mysql_file_location = None
            if options.agent == 'switchover':
                _db = ebGetDefaultDB()
                _primary_mysql_file_location = _db.mExportProxyMigrationTables()
            
            # wait for workers to stop or timeout, if workers stop then
            # gracefully stop agent, or else keep agent up
            if not options.forcekill and not options.forceshutdown: 
                graceful_stop = mNormalShutdown(active_workers_list)

            if options.forceshutdown: #gracefully stop agent, disregard workers
                mForceShutdown(active_workers_list)
                graceful_stop = True

            if options.forcekill: #forcefully kill agent
                ebAgentDaemon.mAgentForceKill(options)
                aExaboxState.mUpdateResourceState(ebRType.AGENT, ebRState.STOPPED)
                graceful_stop = False

            if graceful_stop:
                ebAgentDaemon.mAgentGracefulStop(aOptions=options)
                #Successfull call will also stop workers/scheduler/supervisor
                for _res in (ebRType.AGENT,     ebRType.WORKER,
                             ebRType.SUPERVISOR,ebRType.SCHEDULER,ebRType.DISPATCHER,ebRType.WRKMANAGER):
                    aExaboxState.mUpdateResourceState(_res,ebRState.STOPPED)

            if options.agent == 'switchover':
                _exabox_conf = ebContext.mGetConfigOptions()
                _driver = ExaMySQL(_exabox_conf)
                ebLogInfo("*** ExaCloud MySQL service will be STOPPED")
                _driver.mManualStop()
                startSwitchoverProxy(_primary_mysql_file_location)

        def getMySQLMessage():
            if options.proxy:
                return "\n{0}\n{1}\n{1}\n{2}\n{1}\n{3}\n{4}\n{1}\n{5}\n{1}\n{1}\n{6}\n{1}\n{7}\n{1}\n{1}\n{0}".format(\
                      "*"*102, 
                      "{0}{1}{0}".format("***", " "*96),
                      "{0}{1}Exaproxy Agent stopped.{2}{0}".format("***", " "*4, " "*69), 
                      "{0}{1}MySQL server will be kept running in the background until stack is either uninstalled or{1}{0}".format("***", " "*4), 
                      "{0}{1}manually stopped by command:{2}{0}".format("***", " "*4, " "*64), 
                      "{0}{1}bin/exaproxy --mysql-db stop{2}{0}".format("***", " "*8, " "*60), 
                      "{0}{1}To check MySQL server status, please run:{2}{0}".format("***", " "*4, " "*51), 
                      "{0}{1}bin/exaproxy --mysql-db status{2}{0}".format("***", " "*8, " "*58))

            return "\n{0}\n{1}\n{1}\n{2}\n{1}\n{3}\n{4}\n{1}\n{5}\n{1}\n{1}\n{6}\n{1}\n{7}\n{1}\n{1}\n{0}".format(\
                      "*"*102, 
                      "{0}{1}{0}".format("***", " "*96),
                      "{0}{1}ExaCloud Agent stopped.{2}{0}".format("***", " "*4, " "*69), 
                      "{0}{1}MySQL server will be kept running in the background until stack is either uninstalled or{1}{0}".format("***", " "*4), 
                      "{0}{1}manually stopped by command:{2}{0}".format("***", " "*4, " "*64), 
                      "{0}{1}bin/exacloud --mysql-db stop{2}{0}".format("***", " "*8, " "*60), 
                      "{0}{1}To check MySQL server status, please run:{2}{0}".format("***", " "*4, " "*51), 
                      "{0}{1}bin/exacloud --mysql-db status{2}{0}".format("***", " "*8, " "*58))

        if options.agent == 'start':
            agentStartInternal()
        elif options.agent == 'restart':
            agentStopInternal()
            agentStartInternal()
        elif options.agent == 'reload':
            agentReloadInternal()
        elif options.agent == 'stop':
            agentStopInternal()
            ebLogInfo(getMySQLMessage())
        elif options.agent == 'switchover':
            options.forcekill = True
            options.killworkers = True
            agentStopInternal()
        elif options.agent == "suspend":
            # Send proxy command only
            ProxyClient().mSendOperation(ProxyOperation.UPDATE_STATUS_SUSPEND)
        elif options.agent == 'activate':
            ProxyClient().mSendOperation(ProxyOperation.UPDATE_STATUS_ACTIVE)       
        elif options.agent == 'register':
            ProxyClient().mSendOperation(ProxyOperation.REGISTER)
        elif options.agent == 'deregister':
            ProxyClient().mSendOperation(ProxyOperation.DEREGISTER)

        elif options.proxy == "import":
            # Import data from file to tables
            Router().mImportDBData(options.importfilepath)
            ebLogInfo("Contents of file successfully imported to database.")

        elif options.proxy == "export":
            # Export tables into a file
            _file = Router().mExportDBData()
            ebLogInfo("Location of Database exported data: {}".format(_file))
            
        elif options.agent == 'status':
            _client = ebExaClient()
            if options.debug:
                ebLogDebug('*** IssueRequest start.')
            _client.mIssueRequest()
            if options.debug:
                ebLogDebug('*** IssueRequest done.')
            _client.mWaitForCompletion()
            _response = _client.mGetJsonResponse()
            _agentcfg = ebGetClientConfig()
            if _response['success'] == 'False':
                ebLogInfo('*** Could not contact Agent (%s, %d)- either not running or not reachable' %
                          (_agentcfg[0], int(_agentcfg[1])))
                # Fail the execution, this will be used to check if Exacloud is running on ECRA
                return 1
            else:
                ebLogInfo('*** Agent (%s, %d) is running and reachable' % (_agentcfg[0], int(_agentcfg[1])))
                _wfactory = ebWorkerFactory()
                _wfactory.mCheckFactory()
        return

    if not options.proxy and options.installpkg:
        # Check prereq
        if not options.hostname: # pragma: no cover
            ebLogError('Hostname required to install package')
            sys.exit(-1)
        node = exaBoxNode(ebContext, aLocal=True)
        node.mConnect(aHost=options.hostname)
        pkg = exaBoxPackage(ebContext, options.installpkg, node)
        ebLogInfo('Installing pkg: ' + pkg.mGetPackageName())
        pkg.mInstallSetup()
        pkg.mPublish()
        pkg.mInstallPkg()
        node.mDisconnect()
        return

    if not options.proxy and options.vmctrl:
        ebInitDBLayer(ebContext, options)
        if not options.hostname: # pragma: no cover
            ebLogError('Hostname required (dom0 or VM name)')
            sys.exit(-1)
        node = exaBoxNode(ebContext)
        try:
            node.mConnect(aHost=options.hostname)
        except Exception as e: # pragma: no cover
            ebLogCrit('Connection failure aborting operation: '+options.vmctrl)
            sys.exit(-1)

        vmhandle = ebVgLifeCycle()
        vmhandle.mSetOVMCtrl(aCtx=ebContext, aNode=node)
        vmhandle.mDispatchEvent(options.vmctrl, options)
        node.mDisconnect()
        return

    if not options.proxy and options.clusterctrl:
        ebInitDBLayer(ebContext, options)
        if not options.hostname: # pragma: no cover
            options.hostname = socket.gethostname()
            ebLogWarn('Hostname not provided defaulting to: ' + options.hostname)
        # Default now to local OEDA
        node = exaBoxNode(ebContext, aLocal=True)
        try:
            node.mConnect(aHost=options.hostname)
        except Exception as e: # pragma: no cover
            ebLogCrit('Connection failure aborting operation: ' + options.clusterctrl)
            ebLogCrit(str(e))
            sys.exit(-1)
        ebLogInfo('::ClusterCtrl Command: '+options.clusterctrl)
        cluhandle = exaBoxCluCtrl(aCtx=ebContext, aNode=node, aOptions=options)
        if options.clusterctrl in ["validate_elastic_shapes", "xsvault", "infra_vm_states", "xsput", "xsget"]: # pragma: no cover
             _rc = cluhandle.mDispatchNonXMLCluster(options.clusterctrl, options)
        else:
            _rc = cluhandle.mDispatchCluster(options.clusterctrl, options)
        node.mDisconnect()
        return _rc

    if not options.proxy and options.pwdless:
        if not options.hostname: # pragma: no cover
            ebLogError('Hostname required to setup pwdless connection')
            sys.exit(0)
        node = exaBoxNode(ebContext)
        node.mConnect(aHost=options.hostname)
        node.mSetupPwdLess()
        node.mDisconnect()
        return

    if not options.proxy and options.setupssh:
        if not options.hostname: # pragma: no cover
            ebLogError('Hostname required to setup ssh key')
            sys.exit(0)
        node = exaBoxNode(ebContext)
        node.mConnect(aHost=options.hostname)
        node.mSetupSSHKey()
        node.mDisconnect()
        return

    if not options.proxy and options.setupdns:
        ebLogInfo("Configuring DNS entries for type: {0}".format(options.setupdns))
        ebDNSConfig(options, options.configpath).mConfigureDNS(options.setupdns)
        return

    if not options.proxy and options.healthcheckmetrics:
        ebLogInfo("Configuring Networking for Health Check Metrics : {0}".format(options.healthcheckmetrics))
        return_code = ebDNSConfig(options, options.configpath).mConfigureHealthCheckMetrics(options.healthcheckmetrics)
        return return_code

    # --patch-cluster
    if not options.proxy and options.patchclu:
        ebLogInfo("Patch Cluster Request Started")

        # Check if we have a JSON to parse
        if not options.jsonconf:
            ebLogError("A valid configuration file with patch or rollback operation directives is required.")
            return

        _patch_dispatcher = ebCluPatchDispatcher()
        _patch_dispatcher.mStartPatchRequestExecution(options)
        return

    if not options.proxy and options.sop:
        _json_response = process_sop_request(options.jsonconf, str(uuid.uuid1()))
        ebLogInfo(f"SOP execution response: {json.dumps(_json_response, indent = 4)}")
        return

    # Exakms options
    if not options.proxy and options.exakms:

        ebLogInfo("Dispatching ExaKms endpoint")

        # Get options
        _exakmsOpt = vars(options)
        _payload = options.jsonconf

        if _payload:
            _exakmsOpt.update(options.jsonconf)

        _exakmsOpt['cmd'] = _exakmsOpt['exakms']

        _endpoint = ExaKmsEndpoint(_exakmsOpt)
        _result = _endpoint.mExecute()

        ebLogInfo(f"ExaKms result: {_result}")
        return

    # --json-dispatch
    if not options.proxy and options.jsondispatch:
        if options.jsonconf is None:
            ebLogError("A valid json configuration file is required.")
            return

        if not options.hostname: # pragma: no cover
            options.hostname = socket.gethostname()
            ebLogWarn(("Hostname not provided defaulting to: "
                      f"{options.hostname}"))

        ebLogInfo(f"::JsonDispatch Command: {options.jsondispatch}")

        _dispatcher = ebJsonDispatcher(aCtx=ebContext, aOptions=options)
        _dispatcher.mSetDB(ebGetDefaultDB())
        _rc = _dispatcher.mDispatch(options.jsondispatch, options)

        return _rc

    # Elastic Shapes
    if not options.proxy and options.elastic_shapes:

        # Run the endpoind command
        _uuid = str(uuid.uuid1())
        _payload = options.jsonconf

        if not _payload:
            ebLogError("Payload is Required")
            return

        os.makedirs("log/xmlgen", exist_ok=True)
        os.makedirs("log/xmlgen/{0}".format(_uuid))
        _savedir = "log/xmlgen/{0}/".format(_uuid)

        ebLogInfo("Executing Callback Generator")

        _facade = ebFacadeXmlGen(_uuid, _payload, _savedir)
        _xml = _facade.mGenerateXml()

        ebLogInfo("Final XML at: {0}".format(_xml))
        return
    
    # EDV volumes
    if not options.proxy and options.edv:
        ebLogInfo("*** EDV: Performing EDV management action... ***")
        _action = edv.EDVAction(options.edv)
        _response = edv.perform_edv_action(_action, options)
        ebLogInfo("*** EDV: Finished EDV management operation succesfully ***")
        ebLogInfo(f"EDV action response: {json.dumps(_response, indent=4)}")
        return

    if not options.proxy and options.createwallet:
        # Exabox.conf conversion, default options
        _converter = ebConvertToWalletStorage(ebConfigAuthStorage())
        if _converter.mCheckPrereq():
            _converter.mDoConversion()

        #Remote management conversion
        try:
            _recconf = os.path.join(get_gcontext().mGetBasePath(),
                                    'exabox','managment','config','basic.conf')
            with open(_recconf,'r') as _c:
                _remote_ec_config = json.load(_c)
            _cred = ebBasicAuthStorage(_remote_ec_config["auth"])
            _converter_remoteec = ebConvertToWalletStorage(_cred,_recconf,('auth',),'remoteec_')
            _converter_remoteec.mDoConversion()
        except Exception:
            _converter.mRollback() # If second conversion fails, rollback the first
            raise
        #If we get there, both conversions are successful, delete backups
        _converter.mDeleteBackupConfiguration()
        _converter_remoteec.mDeleteBackupConfiguration()
        return

    ebLogError('*** Please provide an action / request to perform - none provided ***') # pragma: no cover

def executeLocal(aCmd, aCurrDir=None, aStdIn=PIPE, aStdOut=PIPE, aStdErr=PIPE):
    ebLogDebug("executeLocal " + aCmd)
    _args = shlex.split(aCmd)
    _current_dir = aCurrDir
    _stdin = aStdIn
    _std_out = aStdOut
    _stderr = aStdErr
    _proc = subprocess.Popen(_args, stdin=_stdin, stdout=_std_out, stderr=_stderr, cwd=_current_dir)
    _std_out, _std_err = _proc.communicate()
    _rc = _proc.returncode
    return _rc, None, _std_out, _std_err

def main(argv=None):
    _rc = None
    _exabox_state = ebExaboxState()
    try:
        if __name__ != '__main__':  # pragma: no cover
            sys.modules['__main__'] = sys.modules[__name__]

        validate_user()
        clean_environment()
        _rc = execute_from_commandline(argv, _exabox_state)
        # shutdown_all called in finally: block
    except ExacloudRuntimeError as ere:
        _rc = 1
        _stack_trace_mode = ere.mGetStackTraceMode()

        if _stack_trace_mode is True:
            print(ere)
            print('*** Catched exception aborting ***')
            print("Exception in user code:")
            print(('-'*60))
            traceback.print_exc(file=sys.stdout)
            print(('-'*60))
            with CrashDump(logFx=ebLogError) as c:
                c.ProcessException()
    except Exception as ex:
        _rc = 1
        print(ex)
        print('*** Catched exception aborting ***')
        print("Exception in user code:")
        print(('-'*60))
        traceback.print_exc(file=sys.stdout)
        print(('-'*60))
        with CrashDump(logFx=ebLogError) as c:
            c.ProcessException()
    except KeyboardInterrupt:
        print('KeyboardInterrupt exception catched')
        raise
    except SystemExit:
        print('SystemExit exception catched')
        _rc = 1
    finally:
        shutdown_all(_exabox_state)

    if _rc is not None and _rc != 0:
        sys.exit(_rc)


if __name__ == '__main__': # pragma: no cover
    main()
    sys.exit(0)
