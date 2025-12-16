#
# $Header: ecs/exacloud/exabox/proxy/heartbeat.py /main/8 2022/11/09 12:51:49 jesandov Exp $
#
# heartbeat.py
#
# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
#
#    NAME
#      heartbeat.py
#
#    DESCRIPTION
#      Used by proxy to send heartbeat to exacloud instances to determine
#      if the instance is ALIVE/SUSPENDED/DEAD
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    alsepulv    02/23/21 - Bug 32513420: Fix pylint error 'Undefined variable
#                           'ebLogDebug''
#    jejegonz    12/01/20 - Use LogMgr API for adding handlers.
#    dekuckre    10/27/20 - 32072322: Fix DB connections
#    dekuckre    06/19/20 - Creation
#

import json
import datetime
import os
import time
import uuid
import signal
import logging
from exabox.core.DBStore import ebGetDefaultDB
from exabox.log.LogMgr import (ebLogError, ebLogInfo, ebLogWarn, ebLogDebug,
                                ebThreadLocalLog, ebLogAgent, ebLogAddDestinationToLoggers,
                                ebLogDeleteLoggerDestination, ebGetDefaultLoggerName, ebFormattersEnum)
from exabox.agent.Worker import ebWorkerFactory, ebWorker
from exabox.agent.Worker import daemonize_process, redirect_std_descriptors
from exabox.agent.RequestsBackupContext import RequestsBackupContext
from exabox.agent.ProxyClient import ProxyClient, ProxyOperation
from exabox.agent.Agent import ebAgentDaemon
from exabox.core.Context import get_gcontext

ALIVE = 'Alive'
DEAD = 'Dead'

class ProxyHeartbeat(object):  

    def __init__(self, timeout=10):
        self.__db = ebGetDefaultDB()
        self.__timeout = timeout
        self.__running = False
        self.__port = 44444
        self.__proxy_client = ProxyClient()

        signal.signal(signal.SIGINT, self.mSigHandler)
        signal.signal(signal.SIGTERM, self.mSigHandler)

    def mStart(self):
        #Daemonize heartbeat
        daemonize_process()
        redirect_std_descriptors()
        # Initialize after Fork
        pid = heartbeat_running()
        if pid:
            ebLogWarn('heartbeat process is already running with PID {0}'.format(pid))
            exit(1)
        else:
            worker = ebWorker()
            worker.mSetUUID(uuid.uuid4())
            worker.mSetStatus('Heartbeating')
            worker.mSetType('heartbeat')
            worker.mSetPort(self.__port)
            dbworker = self.__db.mGetWorkerByType('heartbeat')
            if dbworker:
                self.__db.mUpdateWorker(worker)
            else:
                self.__db.mInsertNewWorker(worker)

        _default_log_name = ebGetDefaultLoggerName()
        
        ebLogAddDestinationToLoggers([_default_log_name], 'log/workers/dflt_heartbeat', ebFormattersEnum.WORKER)
        ebLogInfo('Starting heartbeat to registered exacloud instances.')
        self.__running = True

        _config_opts = get_gcontext().mGetConfigOptions()
        if "agent_port" in list(_config_opts.keys()):
            _proxy_port = int(_config_opts["agent_port"])

        if "agent_host" in list(_config_opts.keys()):
            _proxy_host = str(_config_opts["agent_host"])

        _proxy_request = 'http://' + _proxy_host + ':' + str(_proxy_port)+"/ecinstmaintenance"

        # proxy to start heartbeat to registered exacloud instances.
        while self.__running:

            _entries = self.__db.mSelectAllFromExacloudInstance()    
            if len(_entries) == 0:
                time.sleep(self.__timeout)
                continue

            for _row in _entries:

                _data = {}

                _id = _row[0]
                _status = _row[4]
                _data['host'] = _row[1]
                _data['port'] = _row[2]

                # send heartbeat
                _request = "http://"+ _data['host'] + ":" + _data['port'] + "/heartbeat"
                _response = ebAgentDaemon.mPerformRequest(_request, _data['host'], _data['port'])

                if _response == None:
                    ebLogDebug("Heartbeat to exacloud agent {} failed.".format(_id))
                    if _status == ALIVE:
                        _data['op'] = 'update'
                        _data['key'] = 'status'
                        _data['value'] = DEAD
                        ebAgentDaemon.mPerformRequest(_proxy_request, \
                            _data['host'], _data['port'], 
                            json.dumps(_data).encode())
                else:
                    ebLogDebug("Heartbeat to exacloud agent {} was successful.".format(_id))
                    if _status == DEAD:
                        _data['op'] = 'update'
                        _data['key'] = 'status'
                        _data['value'] = ALIVE
                        ebAgentDaemon.mPerformRequest(_proxy_request, \
                            _data['host'], _data['port'], 
                            json.dumps(_data).encode())

            time.sleep(self.__timeout)
        ebLogInfo('Exiting heartbeat')

    def mStop(self):
        self.__running = False
        self.__timeout = 0
        worker = ebWorker()
        worker.mSetUUID(uuid.uuid4())
        worker.mSetType('heartbeat')
        worker.mSetPort(self.__port)
        worker.mSetStatus('Exited')
        self.__db.mUpdateWorker(worker)

    def mSigHandler(self, signum, frame):
        ebLogInfo('Handling signal {0}'.format(signum))
        self.mStop()


def heartbeat_running():
    db = ebGetDefaultDB()
    heartbeat = db.mGetWorkerByType('heartbeat')
    if heartbeat:
        pid = heartbeat[8]
        if os.path.exists('/proc/{0}'.format(pid)):
            with open('/proc/{0}/cmdline'.format(pid)) as fd:
                cmd = fd.read()
            if 'heartbeat' in cmd:
                return pid
    return ''

def stop():
    pid = heartbeat_running()
    if pid:
         os.kill(int(pid), signal.SIGTERM)
         os.kill(int(pid), signal.SIGKILL)
