"""
$Header:

 Copyright (c) 2014, 2021, Oracle and/or its affiliates. 

NAME:
    HVMgr - HyperVisorManager abstract functionality

FUNCTION:
    Xen - xenvmmgr
    KVM - kvmvmmgr

NOTE:
   Abstract class for VM operations as each VM type will deviate from each
   other in terms of underlying commands to manage.
   Caller gets the corresponding HVInstance and the corresponding methods 
   will be executed.

History:

    MODIFIED   (MM/DD/YY)
       pbellary 02/06/20 - ENH 30804242 DEVELOP ABSTRACT LAYER FOR HANDLING XEN AND KVM CODE PATHS
       pbellary 02/06/20 - ENH 30804272 DEVELOP VM OPERATIONS SUPPORT FOR KVM USING VIRSH
       siyarlag 01/22/20 - support vm operations on x8m
       nelchan  05/07/19 - creation
"""
# -*- coding: utf-8 -*-
# @Author: nelchan
# @email:   nelson.c.chan@oracle.com
# @Date:   2019-05-07 15:22:09
# @Last Modified by:   nelchan
# @Last Modified time: 2019-06-18 14:37:26

import sys
import json
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogDebug, ebLogWarn
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
import abc


class HVMgr(object):

    def __init__(self, *initial_data, **kwargs):
        super(HVMgr, self).__init__()
        self.hostname = None
        self.eboxObject = None
        """
            ## Flexible init attribute list. We can add new attributes without modifying the __init__ method.
            keys:
            hostname
            nr_mem
            nr_vcpu
            nr_phy_nic
        """
        self.node = None
        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])
        if self.hostname == None:
            raise Exception("Hostname is None")
        self.__destroyOnStart = False

    def mGetDestroyOnStart(self):
        return self.__destroyOnStart

    def mSetDestroyOnStart(self, aValue):
        self.__destroyOnStart = aValue

    def mGetHostname(self):
        return self.hostname

    def mLogInfo(self, msg):
        ebLogInfo("*** %s *** %s" % (self.__class__.__name__, msg))

    def mLogDebug(self, msg):
        ebLogDebug("*** %s *** %s" % (self.__class__.__name__, msg))

    def mLogError(self, msg):
        ebLogError("*** %s *** %s" % (self.__class__.__name__, msg))

    def mLogWarn(self, msg):
        ebLogWarn("*** %s *** %s" % (self.__class__.__name__, msg))

    @abc.abstractmethod
    def pingDomU(self, domU):
        pass

    @abc.abstractmethod
    def startDomU(self, domU):
        pass

    @abc.abstractmethod
    def stopDomU(self, domU):
        pass

    @abc.abstractmethod
    def restartDomU(self, domU):
        pass

    @abc.abstractmethod
    def addCPU(self, domU):
        pass

    @abc.abstractmethod
    def setCPU(self, domU):
        pass

    @abc.abstractmethod
    def getDom0FreeMem(self):
        pass

    # Close connection when instance is destroyed
    def mShutdown(self):

        if self.node is not None:
            # should use getter for node conection
            # if self.node.__connection is not None:
            self.node.mDisconnect()
            self.node = None

    def getExaboxNode(self, user='root'):
        # If self.node is None, get one, otherwise, return self.node
        # Should use getter for node user
        #if self.node == None or user != self.node.mGetUser():
        if self.node == None or user != self.node.__user:
            _ctx = get_gcontext()
            # self.mLogDebug(_ctx)
            _node = exaBoxNode(get_gcontext())
            _node.mSetUser(user)
            _node.mConnect(aHost=self.hostname)
            if _node:
                self.node = _node
            else:
                self.mLogError("Cannot obtain ExaboxNode instance %s" % self.__class__.__name__)
        return self.node

    def mExecuteCmdLog(self, command, user='root'):

        rtnlog = None
        if self.node == None:
            self.getExaboxNode(user=user)
        rtnlog = self.node.mExecuteCmdLog(command)
        return rtnlog

    def mExecuteCmd(self, command, user='root'):

        rtnlog = None
        if self.node == None:
            self.getExaboxNode(user=user)
        rtnlog = self.node.mExecuteCmd(command)
        return rtnlog

    def mGetCmdExitStatus(self, user='root'):

        rtnlog = None
        if self.node == None:
            self.getExaboxNode(user=user)
        rtnlog = self.node.mGetCmdExitStatus()
        return rtnlog

    def mFileExists(self, aRemoteFile, user='root'):

        rtnlog = None
        if self.node == None:
            self.getExaboxNode(user=user)

        rtnlog = self.node.mFileExists(aRemoteFile)
        return rtnlog

    def mCopyFile(self, aLocalFile, aRemoteFile, user='root'):

        rtnlog = None
        if self.node == None:
            self.getExaboxNode(user=user)

        rtnlog = self.node.mCopyFile(aLocalFile, aRemoteFile)
        return rtnlog
