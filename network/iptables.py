"""$Header:

 Copyright (c) 2014, 2023, Oracle and/or its affiliates. 

NAME:
    iptables classes

FUNCTION:
    exabox base execution class

NOTE:
    None

History:

        MODIFIED   (MM/DD/YY)
        ririgoye    08/30/23 - Fix redundant/deprecated mConnect calls
        nelchan     08/28/19 - create file
"""
"""
   Base class for exabox related steps
"""

import abc
import os
import json
import re
from tempfile import NamedTemporaryFile
from exabox.core.Node import exaBoxNode
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogDebug, ebLogWarn
from exabox.ovm.AtpUtils import ebAtpUtils
from exabox.utils.node import connect_to_host

EB_FEATUREKEY_CLASSNAME_MAP = {
    "ebValidateDom0Iptables": "validate_dom0_iptables",
}

EB_LOG_TAG = "[EB STEP]"
DOM0_EXACLOUD_NETWORK_SCRIPT_LOC = "/opt/exacloud/network/"


class ebStep(metaclass=abc.ABCMeta):

    def __init__(self, aDomPairs, aParameters, aErrHex=0x0658):
        super(ebStep, self).__init__()
        self.__domPairs = aDomPairs
        self.__stepname = self.__class__.__name__
        self.__featureKey = EB_FEATUREKEY_CLASSNAME_MAP[self.__stepname]
        self.__parameters = aParameters
        self.__errHex = aErrHex
        self.__LOG_TAG = EB_LOG_TAG

    @abc.abstractmethod
    def _mExecute(self):
        raise NotImplementedError

    @abc.abstractmethod
    def mSetup(self):
        raise NotImplementedError

    @abc.abstractmethod
    def mDestroy(self):
        raise NotImplementedError

    def mExecute(self):
        if ebAtpUtils.isFeatureEnabled(self.__featureKey):
            self.mLogInfo("Executing %s" % self.__stepname)
            self._mExecute()

    def mGetStepName(self):
        return self.__stepname

    def mGetDomPairs(self):
        return self.__domPairs

    def mGetErrHex(self):
        return self.__errHex

    def mGetParameters(self):
        return self.__parameters

    def mLogInfo(self, msg):
        ebLogInfo("***  %s [%s] %s" % (EB_LOG_TAG, self.__stepname.upper(), msg))

    def mLogDebug(self, msg):
        ebLogDebug("***  %s [%s] %s" % (EB_LOG_TAG, self.__stepname.upper(), msg))

    def mLogError(self, msg):
        ebLogError("***  %s [%s] %s" % (EB_LOG_TAG, self.__stepname.upper(), msg))

    def mLogWarn(self, msg):
        ebLogWarn("***  %s [%s] %s" % (EB_LOG_TAG, self.__stepname.upper(), msg))

    @staticmethod
    def runOnCluster(host, cmd, user="root"):
        with connect_to_host(host, get_gcontext()) as _node:
            (_, _o, _e) = _node.mExecuteCmd(cmd)
            if _node.mGetCmdExitStatus():  # need to improve error handling
                raise ExacloudRuntimeError(0x0658, 0x0A, "%s error. e:%s  o:%s" % (
                    cmd, _e.readlines(), _o.readlines()))
            return _o


class ebValidateDom0Iptables(ebStep):

    def _mExecute(self):
        if self.mGetParameters()["template_type"] is None:
            raise ExacloudRuntimeError(self.mGetErrHex(), 0x0A, "template_type is not set in parameters for ebstep")
        templatefile = "iptables.%s.template" % self.mGetParameters()["template_type"]
        for _dom0, _domU in self.mGetDomPairs():
            _cmd = "python {0}validateIptables.py -hn {1} -tp {0}{2}".format(DOM0_EXACLOUD_NETWORK_SCRIPT_LOC, _domU, templatefile)
            self.mLogInfo("Running: " + _cmd)
            _out = ebStep.runOnCluster(_dom0, _cmd)
            _stdout = _out.read()
            if "FAILED" in _stdout:
                self.mLogError("Verification failed: " + _stdout)
                raise ExacloudRuntimeError(self.mGetErrHex(), 0x0A, "iptables validation failed on dom0")
            self.mLogInfo(_stdout)

    def mSetup(self):
        for _dom0, _domU in self.mGetDomPairs():
            with connect_to_host(_dom0, get_gcontext()) as _node:
                self.mLogInfo('*** Copying iptables validation tool to Dom0: %s' % _dom0)
                _node.mCopyFile('scripts/network/validateIptables.py', '/opt/exacloud/network/validateIptables.py')
                _node.mCopyFile('scripts/network/iptables.atp.template', '/opt/exacloud/network/iptables.atp.template')
                _node.mCopyFile('scripts/network/iptables.exacs.template', '/opt/exacloud/network/iptables.exacs.template')

    def mDestroy(self):
        for _dom0, _domU in self.mGetDomPairs():
            with connect_to_host(_dom0, get_gcontext()) as _node:
                ebLogInfo('*** Removing iptables validation tool from Dom0: %s' % _dom0)
                _node.mExecuteCmdLog('rm -rf /opt/exacloud/network/validateIptables.py 2>/dev/null')
                _node.mExecuteCmdLog('rm -rf /opt/exacloud/network/iptables.atp.template 2>/dev/null')
                _node.mExecuteCmdLog('rm -rf /opt/exacloud/network/iptables.exacs.template 2>/dev/null')
