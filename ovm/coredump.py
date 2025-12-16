"""
$Header:

 Copyright (c) 2014, 2023, Oracle and/or its affiliates. 

NAME:

FUNCTION:

NOTE:
   Abstract class for VM operations as each VM type will deviate from each
   other in terms of underlying commands to manage.
   Caller gets the corresponding HVInstance and the corresponding methods 
   will be executed.

History:

    MODIFIED   (MM/DD/YY)
       ririgoye 08/30/23 - Fix redundant/deprecated mConnect calls
       alsepulv 01/25/22 - Enh 33734668: Code coverage improvements
       nelchan  05/16/20 - creation
"""

import sys
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogDebug, ebLogWarn
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.AtpUtils import ebAtpUtils
from exabox.utils.node import connect_to_host

def validatePayload(payload):
    ALLOWED_ACTION = ['setup', 'detach', 'getimagefile', 'dumpcore']
    _action = None
    _coredumpPath = "local"
    _rc = 0
    if not "coredump" in payload.keys(): # pragma: no cover
        ebLogError('Missing action parameter')
        _rc = 0x0119
        return _rc, _action, _coredumpPath
    _action = payload["coredump"]["action"]
    if "coredumppath" in payload["coredump"].keys():
        _coredumpPath = payload["coredump"]["coredumppath"]
        ebLogInfo("Coredump path specified: {0}".format(_coredumpPath))
    if _action not in ALLOWED_ACTION: # pragma: no cover
        ebLogError("Invalid action parameter value: %s " % ALLOWED_ACTION)
        _rc = 0x0119
    return _rc, _action, _coredumpPath

class ebCoredumpUtil(object):

    def __init__(self, doms, payload):
        self.doms = doms
        self.node = None
        self.coredump = ebAtpUtils.mCheckExaboxConfigOption('coredump')
        self.isCoredumpEnabled = False
        if self.coredump != None and self.coredump == "True":
            self.isCoredumpEnabled = True
        rc, self.action, self.mountTarget = validatePayload(payload)
        if rc != 0: # pragma: no cover
            raise ExacloudRuntimeError(rc, 0xA, "Error while trying to validate payload JSON.")

    def mIsCoredumpEnabled(self):
        return self.isCoredumpEnabled

    def mLogInfo(self, msg):
        ebLogInfo("*** %s *** %s" % (self.__class__.__name__, msg))

    def mLogDebug(self, msg):
        ebLogDebug("*** %s *** %s" % (self.__class__.__name__, msg))

    def mLogError(self, msg):
        ebLogError("*** %s *** %s" % (self.__class__.__name__, msg))

    def mLogWarn(self, msg):
        ebLogWarn("*** %s *** %s" % (self.__class__.__name__, msg))

    def mRunCoredumpUtil(self):
        if not self.mIsCoredumpEnabled(): # pragma: no cover
            self.mLogInfo("*** DomU Coredump feature is not enabled ***")
            self.mLogInfo('*** Please set "coredump" : "True" in exabox.conf to enable the feature.')
            return
        _script_path='/opt/exacloud/bin/domU_coredump_util.py'
        _action = self.action
        if self.doms is not None:
            for _dom0, _domU in self.doms:
                self.mLogInfo("*** Setup: imagefile for domU core dumps for %s" % _domU)
                with connect_to_host(_dom0, get_gcontext()) as _node:
                    ## Added mkdir just to make sure this dir exists    
                    _node.mExecuteCmd("/bin/mkdir -p /opt/exacloud/bin")
                    ## Since this is a very small script, it's ok to update it everytime
                    _node.mCopyFile('scripts/domU_coredump_util.py', _script_path)
                    coredump_cmd="/usr/bin/python %s -a %s -hn %s " % (_script_path, _action, _domU)
                    if self.mountTarget != "local":
                        coredump_cmd = coredump_cmd + "-mt {0}".format(self.mountTarget)
                    self.mLogInfo("Executing: %s " % coredump_cmd)
                    _,_o,_ = _node.mExecuteCmd(coredump_cmd)
                    if not _o: # pragma: no cover
                        raise ExacloudRuntimeError(0x0657, 0xA, "No output from domU_coredump_util.py commands.")
                    self.mLogDebug(_o.read())
                
                ## disable domU kdump
                if _action == 'setup':
                    self.mLogInfo("Disabling kdump on %s" % _domU)
                    with connect_to_host(_domU, get_gcontext()) as _node:
                        _node.mExecuteCmd("/bin/systemctl stop kdump.service; /bin/systemctl disable kdump.service")


def setKvmOnCrash(doms, value):

    ALLOWED_ON_CRASH = ['destroy', 'restart', 'preserve', 
                        'rename-restart', 'coredump-destroy', 'coredump-restart']
    if value not in ALLOWED_ON_CRASH: # pragma: no cover
        raise ExacloudRuntimeError(0x0119, 0xA, "Invalid on_crash parameter value: {0} ".format(value))
    if doms is not None:
        for _dom0, _domU in doms:
            ebLogInfo("on_crash value specified: {0} on {1}".format(value, _domU))
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(_dom0)
            _node.mExecuteCmd("/usr/bin/virt-xml {0} --edit --event on_crash={1}".format(_domU, value))
            _rc =  _node.mGetCmdExitStatus()
            _node.mDisconnect()
            if _rc != 0: # pragma: no cover
                raise ExacloudRuntimeError(_rc, 0xA, 'Set virt-xml set on_crash value failed')
