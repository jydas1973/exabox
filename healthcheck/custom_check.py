"""
 Copyright (c) 2014, 2022, Oracle and/or its affiliates. 

NAME:
    custom_check.py - execute scripts or command directly giving through profile  

FUNCTION:
    define function to execute custom commands

NOTE:
    None

History:
    bhuvnkum    02/19/2018 - Creation

"""

from exabox.core.Node import exaBoxNode
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
from multiprocessing import Process
from exabox.ovm.monitor import ebClusterNode
import threading

from exabox.healthcheck.clucheck import ebCluCheck
from exabox.healthcheck.hcconstants import HcConstants, LOG_TYPE, CHK_RESULT


class CustomCheck(ebCluCheck):

    def __init__(self, aCluCtrlObj, aCluHealthObj=None):
        super(CustomCheck, self).__init__(aCluCtrlObj, aCluHealthObj)
        
    def mCheckCustomScript(self, aCmd):
        _cmd_str = aCmd
        _ebox = self.mGetEbox()
        
        if(os.path.splitext(_cmd_str.split()[0])[1] == '.py'):
            _python_bin_path = os.getcwd() + "/opt/bin/python2.7"
            _cmd_str = _python_bin_path + ' ' + _cmd_str
          
        _jsonMap = {}
        _testResult = CHK_RESULT.PASS
        _chkParam = {}
        
        _chkParam["cmd"] = aCmd
         
        try:
            _rc, _i, _o, _e = _ebox.mExecuteLocal(_cmd_str)
            if _rc == 0:
                _jsonMap["output"] = _o
                
            else:
                _testResult = CHK_RESULT.FAIL
                
                self.logger.mAppendLog(LOG_TYPE.ERROR, "Cmd (%s) failed with \n error: \n %s" %(aCmd, _e), _jsonMap)
                
        except Exception as e:
            _testResult = CHK_RESULT.FAIL
            self.logger.mAppendLog(LOG_TYPE.ERROR, "Cmd (%s) failed with return code %s \n output: \n %s  \n error: \n %s  " %(aCmd, _rc, _o, _e), _jsonMap)
            
        return self.logger.mUpdateResult(_testResult, _jsonMap, _chkParam)
    
