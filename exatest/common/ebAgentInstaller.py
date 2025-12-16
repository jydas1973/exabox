#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/common/ebAgentInstaller.py /main/7 2024/04/01 07:33:59 naps Exp $
#
# ebAgentInstaller.py
#
# Copyright (c) 2021, 2023, Oracle and/or its affiliates.
#
#    NAME
#      ebAgentInstaller.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    naps        08/02/23 - Bug 35013360 - UT updation.
#    gparada     06/22/23 - 35213979 Override workers, adding typing
#    ndesanto    11/23/21 - Fix for Unit Test cases haging
#    ndesanto    06/17/21 - Added HTTPSHelper code
#    jesandov    02/23/21 - Creation
#

import os
import time
import base64
import threading
import exabox.network.HTTPSHelper as HTTPSHelper

from multiprocessing import Process
from six.moves.urllib.parse import urlencode
from exabox.exatest.common.ebGeneralInstaller import ebGeneralInstaller
from exabox.agent.Agent import ebAgentDaemon, ebGetAgentInfo
from exabox.log.LogMgr import ebLogInfo

AGENT_INSTALL_ALTNAMES_MOCK_BASE64 = "eyJETlMiOiBbInBoeGRiZmJnNzIuZGV2M2Zhcm0xcGh4LmRhdGFiYXNlZGUzcGh4Lm9yYWNsZXZjbi5jb20iXSwgIklQIjogWyIxMDAuNzAuMTkuMTIzIl19"

class ebAgentInstaller(ebGeneralInstaller):

    def __init__(self, aExacloudPath, aExaboxConf, aConfig, aVerbose):
        super().__init__(aExacloudPath, aExaboxConf, aVerbose)

        self.__config = aConfig
        self.__installDir = None

        self.__agentRunning = False
        self.__stopFlag = False
        self.__threadAgentStop  = None
        self.__threadAgentStart = None
        self.__agentHandle:ebAgentDaemon = None

    #######################
    # Getters and Setters #
    #######################

    def mGetConfig(self):
        return self.__config

    def mSetConfig(self,  aValue):
        self.__config = aValue

    def mGetInstallDir(self):
        return self.__installDir

    def mSetInstallDir(self, aValue):
        self.__installDir = aValue

    def mGetAgentRunning(self):
        return self.__agentRunning

    def mSetAgentRunning(self,  aValue):
        self.__agentRunning = aValue

    def mGetStopFlag(self):
        return self.__stopFlag

    def mSetStopFlag(self, aValue):
        self.__stopFlag = aValue

    def mGetThreadAgentStop(self):
        return self.__threadAgentStop

    def mSetThreadAgentStop(self, aValue):
        self.__threadAgentStop = aValue

    def mGetThreadAgentStart(self):
        return self.__threadAgentStart

    def mSetThreadAgentStart(self, aValue):
        self.__threadAgentStat = aValue

    def mGetAgentHandle(self) -> ebAgentDaemon:
        return self.__agentHandle

    def mSetAgentHandle(self, aValue:ebAgentDaemon):
        self.__agentHandle = aValue

    #################
    # Class Methods #
    #################

    def mInternalStopAgent(self):

        _stop = False
        while not _stop:
            if self.__stopFlag:
                ebLogInfo('mInternalStopAgent: Begin')
                self.mGetAgentHandle().mAgent_Shutdown()
                _stop = True
                ebLogInfo('mInternalStopAgent: End')
            time.sleep(0.5)

    def mStopAgent(self):

        ebLogInfo('mStopAgent: Begin')
        #Stop the Thread and the Agent
        self.__stopFlag = True
        self.__agentRunning = False
        if self.__threadAgentStop:
            ebLogInfo('mStopAgent: waiting to join threadAgentStop')
            self.__threadAgentStop.join()
        if self.__threadAgentStart:
            ebLogInfo('mStopAgent: waiting to join threadAgentStart')
            self.__threadAgentStart.join()

        self.mGetAgentHandle().mAgent_Stop()
        ebLogInfo('mStopAgent: done')

        self.__threadAgentStart = None
        self.__threadAgentStop = None

        os.system('rm {}/lock.dat'.format(self.mGetInstallDir()))
        ebLogInfo('mStopAgent: End')

    def mAgentUrl(self):
        _contest = ''
        try:
            _agentFile = '{}/lock.dat'.format(self.mGetInstallDir())
            with open(_agentFile, 'r') as f:
                _contest = f.read()
        except:
            pass
        return _contest

    def mInstall(self, aInstallDir):

        self.mSetInstallDir(aInstallDir)

        if "optArgs" in self.mGetConfig():

            if  "agent_port" in self.mGetConfig()['optArgs']:
                self.mGetConfig()['optArgs']['agent_port'] = self.mNextPortEmpty(self.mGetConfig()['optArgs']['agent_port'])

            self.mGetConfig()['optArgs']['daemonize'] = False

        if "worker_port" in self.mGetExaboxCfg():
            self.mGetExaboxCfg()['worker_port'] = self.mNextPortEmpty(self.mGetExaboxCfg()['worker_port'])

        _exacloudPath = os.path.abspath(self.mGetExacloudPath())
        if not os.path.exists(os.path.join(_exacloudPath, "exabox/network/certificates")):

            _cmd = "{0}/bin/install_certs {1}".format(_exacloudPath, AGENT_INSTALL_ALTNAMES_MOCK_BASE64)

            _rc, _, _ = self.mExecuteLocal(_cmd)

            if _rc != 0:
                raise Exception("ERROR: Could not create certificates")


    def mStartAgent(self):

        ebLogInfo('Starting new Agent')
        #Prepare the Enviroment
        _agentHandle = ebAgentDaemon()
        self.mSetAgentHandle(_agentHandle)

        #Start the Thread and the Agent
        self._thread_agent_start = threading.Thread(target=_agentHandle.mAgent_Start)
        self._thread_agent_start.start()

        #Start the Thread and the Agent
        self._thread_agent_stop = threading.Thread(target=self.mInternalStopAgent)
        self._thread_agent_stop.start()

        print("Installing Agent", flush=True)
        _timeout = 60 * 10 + time.time()
        while not _agentHandle.mGetReacheable():
            time.sleep(0.5)
            if time.time() > _timeout:
                raise Exception("ERROR: Could not start the Exacloud agent")

        #Set the agent running
        self.__agentRunning = True

        _agentFile = '{}/lock.dat'.format(self.mGetInstallDir())
        with open(_agentFile, 'w') as f:
            if HTTPSHelper.is_https_enabled():
                f.write("https://127.0.0.1:{0}/".format(self.mGetConfig()['optArgs']['agent_port']))
            else:
                f.write("http://127.0.0.1:{0}/".format(self.mGetConfig()['optArgs']['agent_port']))
        print('New Agent Running: "{0}"'.format(self.mAgentUrl()), flush=True)


    def mRequest(self, aPage, aData=None, aMethod=None):
        _pass = self.mGetExaboxCfg()['agent_auth']
        _pass = b":".join([base64.b64decode(x) for x in _pass])
        _pass = base64.b64encode(_pass).decode('utf8')
        headers = {}
        headers["authorization"] = "Basic {}".format(_pass)
        _page = None
        if aData:
            _data = urlencode(aData).encode('utf8')
            _response = HTTPSHelper.build_opener(\
                "127.0.0.1", int(self.mGetConfig()['optArgs']['agent_port']),
                aPage, aMethod='POST',
                aData=_data, aHeaders=headers, aTimeout=60)
            _page = _response.read().strip()
        else:
            _response = HTTPSHelper.build_opener(\
                "127.0.0.1", int(self.mGetConfig()['optArgs']['agent_port']),
                aPage, aMethod='GET',
                aHeaders=headers, aTimeout=60)
            _page = _response.read().strip()
        return _page

# end of file
