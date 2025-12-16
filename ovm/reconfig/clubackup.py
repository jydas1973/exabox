#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/reconfig/clubackup.py /main/2 2021/12/15 20:59:58 ndesanto Exp $
#
# clubackup.py
#
# Copyright (c) 2020, 2021, Oracle and/or its affiliates.
#
#    NAME
#      clubackup.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ndesanto    12/14/21 - Increase coverage for ndesanto files.
#    jesandov    05/18/20 - Creation
#

import time

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure


class ebCluBackup:

    ###############
    # Constructor #
    ###############

    def __init__(self, aClubox):
        self.__clubox = aClubox
        self.__connections = {}

        self.__backupFolder = None
        self.__vmsFolder = None

    #######################
    # Getters and Setters #
    #######################

    def mGetClubox(self):
        return self.__clubox

    def mSetClubox(self, aClubox):
        self.__clubox = aClubox

    def mGetBackupFolder(self):
        return self.__backupFolder

    def mSetBackupFolder(self, aBackupFolder):
        self.__backupFolder = aBackupFolder

    def mGetVmsFolder(self):
        return self.__vmsFolder

    def mSetVmsFolder(self, aVmsFolder):
        self.__vmsFolder = aVmsFolder

    ##################
    # Backup methods #
    ##################

    def mGetConnection(self, aHostname):

        if aHostname in self.__connections:
            return self.__connections[aHostname]

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aHostname)

        self.__connections[aHostname] = _node

        return _node

    def mCleanConnections(self):

        for _, _node in self.__connections.items():
            _node.mDisconnect()

        self.__connections = {}

    def mBackupAll(self):

        _processes = ProcessManager()

        for _dom0, _domu in self.mGetClubox().mReturnDom0DomUPair():

            _p = ProcessStructure(self.mCreateBackup, [_dom0, _domu])
            _p.mSetMaxExecutionTime(60*60)
            _p.mSetJoinTimeout(10)
            _processes.mStartAppend(_p)

        _processes.mJoinProcess()

        if _processes.mGetStatus() == "killed":
            ebLogError('Timeout while executing Backup in Reconfig.')
            raise ExacloudRuntimeError(0x0821, 0xA, 'Timeout while executing Backup.', aStackTrace=False)

        self.mCleanConnections()

    def mDeleteAll(self):
        for _dom0, _domu in self.mGetClubox().mReturnDom0DomUPair():
            self.mDeleteBackup(_dom0, _domu)
        self.mCleanConnections()

    def mCreateBackup(self, aDom0Name, aVmName):
        raise NotImplementedError

    def mDeleteBackup(self, aDom0Name, aVmName):
        raise NotImplementedError

    def mRestoreBackup(self, aDom0Name, aVmName):
        raise NotImplementedError

    def mFetchBackup(self, aDom0Name, aVmName):
        raise NotImplementedError

# end of file
