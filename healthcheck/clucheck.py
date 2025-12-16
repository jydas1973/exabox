"""
 Copyright (c) 2014, 2023, Oracle and/or its affiliates. 

NAME:
    clucheck.py - added for hc v2 

FUNCTION:
    define base class and utility functions for healthcheck infra. 

NOTE:
    None

History:
    bhuvnkum    02/19/2018 - Creation

"""

import six
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogDebug, ebLogVerbose
from exabox.ovm.vmconfig import exaBoxClusterConfig
import os, sys, subprocess, uuid, time, os.path, traceback
from subprocess import Popen, PIPE
import xml.etree.cElementTree as etree
from exabox.core.Context import get_gcontext
from exabox.core.Core import exaBoxCoreInit
from exabox.ovm.vmcontrol import exaBoxOVMCtrl
from tempfile import NamedTemporaryFile
from time import sleep
from datetime import datetime
from base64 import b64decode
import hashlib
import re, random
import json, copy, socket
from exabox.tools.scripts import ebScriptsEngineFetch
from exabox.core.DBStore import ebGetDefaultDB
from multiprocessing import Process, Queue
from exabox.ovm.monitor import ebClusterNode
import threading
from os.path import basename, dirname, join
from glob import glob

from exabox.healthcheck.hcutil import Singleton
from exabox.healthcheck.hcconstants import HcConstants, CHK_RESULT, LOG_TYPE
from exabox.healthcheck.hcconstants import gCheckNameFunctionMap, gCheckList
from exabox.healthcheck.hclogger import get_logger, init_logging
from exabox.ovm.hypervisorutils import getHVInstance

REGISTERED_CLASSES = []


def register_class(cls):
    REGISTERED_CLASSES.append(cls)
    return cls


def get_all_registered_classes():
    # TBD: Looking for file in current dir,
    # can think of loading from ovm, if required
    pwd = dirname(__file__)
    for x in glob(join(pwd, '*.py')):
        # skip files like __init__.py to get imported
        if not x.startswith('__'):
            __import__('exabox.healthcheck.' + basename(x)[:-3], globals(), locals())


class Meta(type):
    """
    class to be used for registering classes with healthcheck 
    infra. 
    """

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)
        register_class(cls)
        return cls


# Use if required to hook all methods
class CheckFilter(object):
    """
    class to hook all calls of derived class i.e. ebCluHealth
    check for functions listed in master checklist 
    skip function based on profile
    """

    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        if hasattr(attr, '__call__'):
            def newfunc(*args, **kwargs):
                _func_name = attr.__name__
                if _func_name in gCheckNameFunctionMap.keys():
                    _chk_id = gCheckNameFunctionMap[attr.__name__]
                    if _chk_id not in gCheckList:
                        ebLogVerbose("skipping %s " % (_func_name))
                        return
                result = attr(*args, **kwargs)
                return result

            return newfunc
        else:
            return attr


class NodeConnection(object):
    #    __metaclass__ = Singleton

    def __init__(self, aCluCtrlObject, aCluHealthObject=None):
        self.__ecc = aCluCtrlObject
        self.__hc = aCluHealthObject
        self.__cluster_host_d = {}
        self.__ssh_connections = {}
        self.__not_reachable = set()  # ping or ssh failure
        self.__not_running_vms = []
        self.__allow_domu_ssh = True
        self.__initNode()
        self.__preprov = None
        self.__lock = threading.RLock()

    def __initNode(self):
        _dom0s, _domUs, _cells, _ = self.__ecc.mReturnAllClusterHosts(aRetDummyDomu=False)

        if self.__ecc.mIsOciEXACC() and self.__ecc.mIsKVM():
            _switches = self.__ecc.mReturnSwitches(aMode=True, aRoceQinQ=True)
        else:
            _switches = self.__ecc.mReturnSwitches(aMode=True)

        _cluhosts = _dom0s + _domUs + _cells + _switches

        for _host in _cluhosts:
            _clunode = ebClusterNode()
            self.__cluster_host_d[_host] = _clunode
            _eBoxKey = self.__ecc.mGetKey()
            _clunode.mSetClusterId(_eBoxKey)
            _clunode.mSetHostname(_host)
            _eBoxNetworks = self.__ecc.mGetNetworks()
            _neto = _eBoxNetworks.mGetNetworkConfigByName(_host)
            _clunode.mSetNetworkIp(_neto.mGetNetIpAddr())

            if _host in _dom0s:
                _clunode.mSetNodeType('dom0')
            elif _host in _domUs:
                _clunode.mSetNodeType('domu')
            elif _host in _cells:
                _clunode.mSetNodeType('cell')
            elif _host in _switches:
                _clunode.mSetNodeType('switch')

    def mGetClusterHostD(self):
        return self.__cluster_host_d

    def mIsDomuSshAllowed(self):
        return self.__allow_domu_ssh

    def mSetDomuSshAllowed(self, aAllowed):
        self.__allow_domu_ssh = aAllowed

    def mPingTest(self, aHost, aCount=2, aTimeout=4):
        _ret = False
        _verbose = self.__ecc.mGetVerbose()

        def _mSetPingstatusUtil(aHost, aCount, aTimeout, aQueue):
            _host = aHost
            _queue = aQueue
            _clunode = _clu_ping_host[_host]
            if not self.__ecc.mPingHost(aHost, aCount, aTimeout):
                _queue.put([_host, False])
            else:
                _queue.put([_host, True])

        _hostProcessMap = {}
        _queue = Queue()
        _clu_ping_host = self.mGetClusterHostD()

        _p = Process(target=_mSetPingstatusUtil, args=(aHost, aCount, aTimeout, _queue))
        _hostProcessMap[aHost] = _p
        _p.start()
        if _verbose:
            ebLogVerbose('*** %s : _mSetPingstatusUtil started for %s' % (_p.name, aHost))

        _hostProcessMap[aHost].join()
        if _verbose:
            ebLogVerbose('*** %s : _mSetPingstatusUtil joined for %s ' % (_hostProcessMap[aHost].name, aHost))

        while not _queue.empty():
            _entry = _queue.get()
            _host = _entry[0]
            _ret = _entry[1]
            _clunode = _clu_ping_host[_host]
            _clunode.mSetPingable(_ret)

        return _ret

    def mSshTest(self, aHost, aUser="root", aTimeout="10"):
        _ret = False
        _host = aHost
        _user = aUser
        _ssh_timeout = aTimeout
        _clunode = self.mGetClusterHostD()[_host]
        _node = None
        if not _clunode.mGetPingable():
            if not self.mPingTest(aHost):
                return None

        _node = exaBoxNode(get_gcontext())
        _node.mSetUser(_user)
        try:
            _node.mConnectTimed(aHost=_host, aTimeout=_ssh_timeout)
            _ret = True
        except Exception as e:
            ebLogError('*** SSH error: Failed to connect to: %s@%s (pingable though) with error %s' % (_user, _host, str(e)))
            return None

        # TBD: ssh connection status may vary for different users
        _clunode.mSetSSHConnection(_ret)
        return _node

    def mGetNode(self, aHost, aUser='root', aForceRetry=False):
        _host = aHost
        _user = aUser
        _node = None

        _clunode = self.mGetClusterHostD()[aHost]
        if _clunode.mGetNodeType() == 'domu':
            if not self.mIsDomuSshAllowed():
                return None

        _destination = '%s@%s' % (aUser, aHost)
        if _destination in self.__ssh_connections:
            return self.__ssh_connections[_destination]

        if (not aForceRetry and (aHost in self.__not_reachable or
                                 _destination in self.__not_reachable)):
            return None

        if not _clunode.mGetPingable():
            if not self.mPingTest(aHost):
                return None

        _node = self.mSshTest(_host, _user)
        if _node is None:
            self.__not_reachable.add(_destination)
        else:
            self.__ssh_connections[_destination] = _node

        # print self.__ssh_connections, self.__not_reachable
        return _node

    def mDisconnectNode(self, aNode):

        # expecting that healthcheck executor will cleanup
        # all connections in last with  mCleanUp call
        if self.__hc is None:
            return

        # In case of mGetNode called without healthcheck then
        # it should be disconnected individually
        _node = aNode
        for _host, _ssh in six.iteritems(self.__ssh_connections):
            if _ssh == _node:
                if self.__ecc.mGetVerbose():
                    ebLogVerbose("remove connection %s %s" % (_host, _ssh))
                _node.mDisconnect()
                del self.__ssh_connections[_host]
                break

    def mCleanUp(self):
        while self.__ssh_connections:
            _host, _ssh = self.__ssh_connections.popitem()
            if self.__ecc.mGetVerbose():
                ebLogVerbose("remove connection %s %s" % (_host, _ssh))
            _ssh.mDisconnect()

    def mGetVmStatus(self):
        ebLogVerbose('Check VM status')
        _ret = True

        def _is_vm_running(aNode, aDomuName, aVmHandle):
            _vm = aVmHandle
            _cmd_str, _domUList = _vm.mGetDomUList()
            for _line in _domUList:
                if aDomuName in _line:
                    return True
            return False

        def _is_vmconfig_exist(aNode, aDomuName, aVmHandle):
            _vm = aVmHandle
            _rc = _vm.mVmConfigExist(aNode, aDomuName)
            if _rc:
                ebLogDebug('*** VM config file exists for %s' % (aDomuName))
                return True
            else:
                ebLogDebug('*** VM config file not found for %s' % (aDomuName))
                return False

        for _dom0, _domu in self.__ecc.mReturnDom0DomUPair():
            _node = self.mGetNode(_dom0)
            if _node is None:
                ebLogDebug('%s not running' % _dom0)
                _ret = False
                continue

            _vm = getHVInstance(_node)

            if _is_vm_running(_node, _domu, _vm):
                ebLogDebug('%s is running' % _domu)
            else:
                ebLogError('VM check failed: %s is not running' % _domu)
                self.__not_running_vms.append(_domu)
                if _is_vmconfig_exist(_node, _domu, _vm):
                    ebLogDebug('%s is not running but already provisioined' % _domu)
                else:
                    ebLogDebug('%s not provisioined' % _domu)
                    _ret = False

            _node.mDisconnect()
        return _ret

    def mGetPreProv(self):

        if self.__preprov is None:
            self.__lock.acquire()
            if self.__preprov is None:
                self.__preprov = self.mGetVmStatus()
            self.__lock.release()

        return self.__preprov


class ebCluCheck(metaclass=Meta):
    """
    Base class for all checks to be included as part of healthcheck infra.
    """

    def __init__(self, aCluCtrlObject, aCluHealthObject=None):
        self.__ecc = aCluCtrlObject
        self.__hc = aCluHealthObject
        self.__sshnode = NodeConnection(self.__ecc, self.__hc)

        # initialize logging if not already
        init_logging(aCluCtrlObject, aCluHealthObject)
        self.logger = get_logger()

    def __del__(self):
        pass

    def mGetNodeConnection(self):
        return self.__sshnode

    def mGetNode(self, aHost, aUser='root', aForceRetry=False):
        _node = self.__sshnode.mGetNode(aHost, aUser, aForceRetry)
        if _node is not None:
            return _node
        else:
            raise Exception('GetNode failed to get Connection for %s@%s' % (aUser, aHost))

    def mDisconnectNode(self, aNode):
        return self.__sshnode.mDisconnectNode(aNode)

    def mCleanUp(self):
        self.__sshnode.mCleanUp()

    def mGetHc(self):
        return self.__hc

    def mGetEbox(self):
        return self.__ecc

    def mGetClusterNode(self, aHost):
        return self.__sshnode.mGetClusterHostD()[aHost]

    def mGetCluHealthNode(self, aHost):
        return self.__hc.mGetClusterHealthD()[aHost]

    def mGetPreProv(self):
        return self.__sshnode.mGetPreProv()

    def mGetCheckParam(self, aOption, aDefault, aCheckParam=None):
        """
        This function return healthcheck option in below order: 
        1. return if passed through profile using checkParam
        2. else look into global healthcheck.conf params
        3. if not found return default value supplied 
        
        """
        if aCheckParam is not None:
            if aOption in aCheckParam.keys():
                return aCheckParam[aOption]

        if self.__hc is not None:
            _hcConf = self.__hc.mGetHcConfig()
            if aOption in _hcConf.keys():
                return _hcConf[aOption]

        return aDefault
