"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates. 

NAME:
    checkexecutor.py - Added for hc v2 

FUNCTION:
    execute checks from healthcheck infra

NOTE:
    None

History:
    bhpati      07/31/2025 - Bug 38102552 - Log as error instead of warning for healthcheck failure 
    joysjose    06/25/2024 - Bug 36727956 - Regression fix for printing result json correctly
    aypaul      05/30/2024 - Issue#36640253 Replace default multiprocess with asyncprocessing module.
    bhuvnkum    02/19/2018 - Creation

"""

import six
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogTrace, ebLogVerbose, ebLogWarn
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
from multiprocessing import Process, Manager
import threading
from copy import deepcopy

from exabox.healthcheck.hcutil import Singleton 
from exabox.healthcheck.hcconstants import HcConstants, gCheckNameFunctionMap, CHK_RESULT, LOG_TYPE
from exabox.healthcheck.clucheck import REGISTERED_CLASSES, get_all_registered_classes
from exabox.healthcheck.check_parser import CheckParser
from exabox.healthcheck.clumisc import ebCluPreChecks 
from exabox.healthcheck.healthcheck import HealthCheck
from exabox.healthcheck.hclogger import get_logger
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure

#if debug make it false 
#TBD: read this from config file
gRunNodeTaskParallel    = True
gRunCustomTaskParallel  = True
gRunExecutorParallel    = True
gCount  = 0

class ObjectStore(object):
    #__metaclass__ = Singleton

    def __init__(self, aCluHealth):
        self._hc = aCluHealth
        self._ebox = self._hc.mGetEbox()
        self._clsDict = {}
        
        self.mCreateInstance()

    def mCreateInstance(self):
        for _cls in REGISTERED_CLASSES:
            self._clsDict[_cls.__name__] = _cls(self._ebox, self._hc)

    def mGetInstance(self,_clsname):
        return self._clsDict[_clsname]

    def mDeleteInstance(self):
        #
        while self._clsDict:
            _cls, _inst = self._clsDict.popitem()
            if self._hc.mGetEbox().mGetVerbose():
                ebLogVerbose("remove class instance %s %s" %(_cls, _inst))
            ret = getattr(_inst, "mCleanUp")()
            del _inst


 #class for execution of checks build from profileParser 
class CheckExecutor(object):

    #class instance vars
    _checkIdToFuncMap = {}
    _funcToCheckIdMap = {}

    def _getMethods(self):
        
        def _methods(cls):
            _method_names = [x for x in dir(cls) if x.startswith("mCheck")]
            return _method_names
    
        get_all_registered_classes()
        _hc_methods = {}
        for _cls in REGISTERED_CLASSES:
            for _method in _methods(_cls):
                if(_method not in _hc_methods.keys()):
                    _hc_methods[_method] = _cls.__name__
                else:
                    #there should be only one check function wrt checkname, 
                    #it will call first check function if found more check function in other module wrt to same checkname
                    ebLogError("duplicate check definition found: %s, it will call method in module %s" %(_method, _hc_methods[_method]))

        return _hc_methods

    def __init__(self, aCluHealth):
        
        self._hc                =   aCluHealth
        self._objCheckParser    =   aCluHealth.mGetCheckParser()
        self._objProfileParser  =   aCluHealth.mGetProfileParser()
        self.resdict =  Manager().dict()
        

        self._CheckList = aCluHealth.mGetCheckList()
        _hc_methods = self._getMethods()
        
        for _checkId in self._CheckList:
            _checkName = self._objCheckParser.mGetCheckList()[_checkId][HcConstants.CHK_NAME]
            _funcName = None
            if _checkName in gCheckNameFunctionMap.keys():
                _funcName = gCheckNameFunctionMap[_checkName]
            else:
                if ("mCheck"+_checkName) in _hc_methods.keys():
                    _funcName = _hc_methods["mCheck"+_checkName] + ".mCheck"+_checkName
                else:
                    ebLogVerbose ("Function corresponding to check %s, %s not found" %(_checkId, _checkName))
            
            if _funcName is not None:
                CheckExecutor._funcToCheckIdMap[_funcName] = _checkId
                CheckExecutor._checkIdToFuncMap[_checkId] = _funcName
        

    # Entry point to execute all of the assembled tasks.
    def execute_checklist(self):
        _targetList = self._objCheckParser.mGetTargetList()
        _targetChkList = dict((_target, []) for _target in _targetList)
        object = ObjectStore(self._hc)
        _process_manager = ProcessManager()
        
        for _chkid in sorted(CheckExecutor._checkIdToFuncMap):
            
            _chkTargetList      =   self._objCheckParser.mGetCheckTargetList(_chkid)
            _profileTargetList  =   self._objProfileParser.mGetProfileTargetList()
            
            if HcConstants.ALL in _profileTargetList:
                _profileTargetList = self._objCheckParser.mGetTargetList()
                 
            _targetList = list(set(_chkTargetList) & set(_profileTargetList))
            for _target in _targetList:

                mod_name, func_name = CheckExecutor._checkIdToFuncMap[_chkid].rsplit('.',1)
                mod = object.mGetInstance(mod_name)

                #fill template 
                _task = {}
                try:
                    _task["fp"]                                   =     getattr(mod, func_name)
                    _task["result"]                               =     get_logger().mGetResultTemplate()
                    _task["result"][HcConstants.RES_HCID]         =     _chkid
                    _task["result"][HcConstants.RES_CHKNAME]      =     self._objCheckParser.mGetCheckName(_chkid)
                    _task["result"][HcConstants.RES_PROFILE]      =     self._objProfileParser.mGetProfileName()
                    _task["result"][HcConstants.RES_ALERTTYPE]    =     self._objCheckParser.mGetCheckAlertLevel(_chkid)
                    _task["result"][HcConstants.RES_NODETYPE]     =     _target
                    _task["result"][HcConstants.RES_NODENAME]     =     _target
                    #TBD: can take default param from master json
                    _task["result"][HcConstants.RES_CHECKPARAM]   =  self._objProfileParser.mGetCheckParamForId(_chkid)
                    #append funcpointer and template 
                    _targetChkList[_target].append(_task)
                except Exception as e:
                    ebLogError("Failed to add check in tasklist, exception: %s"  %(str(e)))

        _tasklist = []
        for _targettype, _chklist in six.iteritems(_targetChkList):
            if _chklist:
                _tasklist.append(HCTask.taskfactory(self._hc, _targettype, _chklist))

        _pidList  = []
        _currentPid = str(os.getpid())
        self.resdict[_currentPid +"pid_list"] = _pidList
        self.resdict["pids"]=[""]
        if not gRunExecutorParallel:
            for _task in _tasklist:
                _task.execute(self.resdict)

        else:
            _hc_timeout = 900
            _hc_timeout_config = self._hc.mGetEbox().mCheckConfigOption('healthcheck_task_timeout')
            if _hc_timeout_config is not None:
                _hc_timeout = int(_hc_timeout_config)
            for _task in _tasklist:
                _proc_struct = ProcessStructure(_task.execute, [self.resdict,])
                _proc_struct.mSetMaxExecutionTime(_hc_timeout)
                _proc_struct.mSetJoinTimeout(5)
                _proc_struct.mSetLogTimeoutFx(ebLogWarn)
                _process_manager.mStartAppend(_proc_struct)
                if self._hc.mGetEbox().mGetVerbose():
                    ebLogVerbose(f'Parallel process execution initiated for {_task}')
                ebLogTrace(f'Parallel process execution initiated for {_task}')

            _process_manager.mJoinProcess()
            if self._hc.mGetEbox().mGetVerbose():
                ebLogVerbose('All tasks execution completed')
            ebLogTrace('All tasks execution completed')

        self.resdict[_currentPid + "pid_list"] = list(set(self.resdict["pids"]))
        _pidList  =  self.getOrderPid(_currentPid)
        _result = Finalize(self.resdict)
        _result.execute(_pidList)
        #remove check infra class's object and release node connection 
        object.mDeleteInstance()

    def getOrderPid(self, aParentPid):
        _parentPid = aParentPid
        _finalpidlist = []
        _pidList  = self.resdict[_parentPid + "pid_list"]
        for _pid in _pidList :
            if (_pid + "pid_list") in self.resdict :
                for _childpid in self.resdict [_pid + "pid_list"] :
                    _finalpidlist.append(_childpid)
            _finalpidlist.append(_pid)
        _finalpidlist.append(_parentPid)
        return  _finalpidlist


class HCTask(object):
    
    @staticmethod
    def taskfactory(aCluHealth, aType, aTaskList):
        if aType in [HcConstants.DOM0, HcConstants.DOMU, HcConstants.CELL, HcConstants.SWITCH]: 
            return NodeTask(aCluHealth, aType, aTaskList)
        elif aType in [HcConstants.CUSTOMCHECK]:
            return CustomTask(aCluHealth, aType, aTaskList)
        else:
            return OtherTask(aCluHealth, aType, aTaskList)

    def __init__(self, aCluHealth, aTaskList):
        self._hc              = aCluHealth
        self._name            = self.__class__.__name__
        self._subtasks        = aTaskList
        self._res_fields      = [HcConstants.RES_RESULT, HcConstants.RES_LOG, HcConstants.RES_MSGDETAIL, HcConstants.RES_CHECKPARAM]

    def mGetHc(self):
        return self._hc
    
    def cleanupSubtaskResult(self, aSubtaskResult):
        aSubtaskResult[HcConstants.RES_RESULT]       = "" 
        aSubtaskResult[HcConstants.RES_STARTTIME]    = ""
        aSubtaskResult[HcConstants.RES_ENDTIME]      = ""
        aSubtaskResult[HcConstants.RES_NODENAME]     = ""
        aSubtaskResult[HcConstants.RES_LOG]          = []
        aSubtaskResult[HcConstants.RES_MSGDETAIL]    = {}
        
    def execute(self, aResult, aOptions = None):
        _resdict = aResult
        _currentPid = str(os.getpid())
        global  gCount
        logs = []
        gCount = 0

        for _subtask in self._subtasks:
            gCount += 1
            _fp         = _subtask["fp"]
            _result     = deepcopy(_subtask["result"])
            self.cleanupSubtaskResult(_result)

            try:
                if self._hc.mGetEbox().mGetVerbose():
                    ebLogVerbose("executing subtask: %s" %(_result[HcConstants.RES_CHKNAME]))
                starttime = datetime.now().replace(microsecond=0)
                if aOptions is None:
                    if not bool(_result[HcConstants.RES_CHECKPARAM]):
                        ret = _fp()
                    else:
                        ret = _fp(_result[HcConstants.RES_CHECKPARAM])
                elif "host" in aOptions.keys():
                    _result[HcConstants.RES_NODENAME] = aOptions["host"]
                    if not bool(_result[HcConstants.RES_CHECKPARAM]):
                        ret = _fp(aOptions["host"])
                    else:
                        ret = _fp(aOptions["host"], _result[HcConstants.RES_CHECKPARAM])

                elif "checkname" in aOptions.keys() and "cmdstr" in aOptions.keys():
                    _result[HcConstants.RES_CHKNAME] = aOptions["checkname"]
                    if not bool(_result[HcConstants.RES_CHECKPARAM]):
                        ret = _fp(aOptions["cmdstr"])
                    else:
                        ret = _fp(aOptions["cmdstr"], _result[HcConstants.RES_CHECKPARAM])
                else:
                    ebLogError("Invalid options to Healthcheck Executor")

                if self._hc.mGetEbox().mGetVerbose():
                    ebLogVerbose("execution completed for subtask: %s" %(_result[HcConstants.RES_CHKNAME]))
                if isinstance(ret,dict):
                    if all(key in ret.keys() for key in self._res_fields):
                        _result[HcConstants.RES_RESULT]       = CHK_RESULT.reverse_mapping(ret[HcConstants.RES_RESULT]).upper() 
                        _result[HcConstants.RES_LOG]          = ret[HcConstants.RES_LOG]
                        _result[HcConstants.RES_MSGDETAIL]    = ret[HcConstants.RES_MSGDETAIL]
                        #updating again if changed inside function
                        #_result[HcConstants.RES_CHECKPARAM]   = ret[HcConstants.RES_CHECKPARAM]
                    else:
                        ebLogError('result (%s) must contain (%s) for check %s' %(_result[HcConstants.RES_CHKNAME], self._res_fields, ret))
                        continue

                elif isinstance(ret,(int, bool)):
                    _result[HcConstants.RES_RESULT]       = CHK_RESULT.reverse_mapping(ret).upper()

                else:
                    ebLogError('No return value from check %s, it must return result in specified format' %(_result[HcConstants.RES_CHKNAME]))
                    _result[HcConstants.RES_RESULT]       = CHK_RESULT.reverse_mapping(CHK_RESULT.FAIL).upper()

            except Exception as e:
                err_message     = "Check %s, could not complete execution, exception: %s"  %(_result[HcConstants.RES_CHKNAME], str(e))
                logs.append(err_message)

                _resdict[_currentPid + "_log" + str(gCount)] = logs
                _result[HcConstants.RES_RESULT]       = CHK_RESULT.reverse_mapping(CHK_RESULT.FAIL).upper()
                _result[HcConstants.RES_LOG]          = err_message

            endtime = datetime.now().replace(microsecond=0)
            _result[HcConstants.RES_STARTTIME]    = str(starttime)
            _result[HcConstants.RES_ENDTIME]      = str(endtime)
            _resdict[_currentPid + "_results" + str(gCount)] = _result
            _resdict["pids"].append(_currentPid)
        _recommend  =  get_logger().mGetRecommend()
        _resdict[str(_currentPid) + "_recommend" + str(gCount)] = _recommend
        


class NodeTask(HCTask):

    def __init__(self, aCluHealth, aType, aTaskList):
        HCTask.__init__(self, aCluHealth, aTaskList)
        self._type      = aType

    def mGetHostList(self):
        _hostList = None

        if self._type == HcConstants.DOM0:
            _hostList = self.mGetHc().mGetDom0s()
        elif self._type == HcConstants.DOMU:
            _hostList = self.mGetHc().mGetDomUs()
        elif self._type == HcConstants.CELL:
            _hostList = self.mGetHc().mGetCells()
        elif self._type == HcConstants.SWITCH:
            _hostList = self.mGetHc().mGetSwitches()
        else:
            pass

        return _hostList
        
    def execute(self, aResult):
        _resdict = aResult
        _hostList = self.mGetHostList()
        _options = {}
        _process_manager = ProcessManager()
         
        if not gRunNodeTaskParallel:
            for _host in _hostList:
                _options["host"] = _host
                super(NodeTask, self).execute(_resdict, _options) 

        else:
            #enable it for multithreading
            _hostProcessMap = {}
            _pidList = []
            _currentPid  = str(os.getpid())
            _hc_timeout = 900
            _hc_timeout_config = self._hc.mGetEbox().mCheckConfigOption('healthcheck_task_timeout')
            if _hc_timeout_config is not None:
                _hc_timeout = int(_hc_timeout_config)
            for _host in _hostList:
                _options["host"] = _host
                _proc_struct = ProcessStructure(super(NodeTask, self).execute, [_resdict, deepcopy(_options),])
                _proc_struct.mSetMaxExecutionTime(_hc_timeout)
                _proc_struct.mSetJoinTimeout(5)
                _proc_struct.mSetLogTimeoutFx(ebLogWarn)
                _process_manager.mStartAppend(_proc_struct)
                if self._hc.mGetEbox().mGetVerbose():
                    ebLogVerbose(f'Process started for host {_host}')
                ebLogTrace(f'Process started for host {_host}')

            _process_manager.mJoinProcess()
            if self._hc.mGetEbox().mGetVerbose():
                ebLogVerbose('All processes completed execution.')   
            ebLogTrace('All processes completed execution.')

            _resdict[_currentPid + "pid_list"] = _pidList


class OtherTask(HCTask):
    
    def __init__(self, aCluHealth, aType, aTaskList):
        HCTask.__init__(self, aCluHealth, aTaskList)
        
    def execute(self, aResult):
        super(OtherTask, self).execute(aResult) 


class CustomTask(HCTask):
    
    def __init__(self, aCluHealth, aType, aTaskList):
        HCTask.__init__(self, aCluHealth, aTaskList)
        
    def mGetCustomCheckList(self):
        return self.mGetHc().mGetCustomCheckList()
        
    def execute(self, aResult):
        _resdict = aResult
        _chkList = self.mGetCustomCheckList()
        if _chkList is None:
            return
        _options = {}
        _process_manager = ProcessManager()
        if not gRunCustomTaskParallel:
            for _chk, _cmd_str in six.iteritems(_chkList):
                _options["checkname"] =  _chk
                _options["cmdstr"] =  _cmd_str
                super(CustomTask, self).execute(_options) 
        else:
            #enable it for multithreading
            _processMap = {}
            _pidList = []
            _currentPid = str(os.getpid())
            _hc_timeout = 900
            _hc_timeout_config = self._hc.mGetEbox().mCheckConfigOption('healthcheck_task_timeout')
            if _hc_timeout_config is not None:
                _hc_timeout = int(_hc_timeout_config)
            for _chk, _cmd_str in six.iteritems(_chkList):
                _options["checkname"] =  _chk
                _options["cmdstr"] =  _cmd_str
                _proc_struct = ProcessStructure(super(CustomTask, self).execute, [_resdict, deepcopy(_options),])
                _proc_struct.mSetMaxExecutionTime(_hc_timeout)
                _proc_struct.mSetJoinTimeout(5)
                _proc_struct.mSetLogTimeoutFx(ebLogWarn)
                _process_manager.mStartAppend(_proc_struct)
                if self._hc.mGetEbox().mGetVerbose():
                    ebLogVerbose(f'Process stated for {_chk}')
                ebLogTrace(f'Process stated for {_chk}')

            _process_manager.mJoinProcess()

            _resdict[_currentPid + "pid_list"] = _pidList

class Finalize:
    def __init__(self, aResult) :
        self.resdict = aResult

    def execute(self, aPidList):
        _pidList = aPidList
        _final_recommended_list = []
        for _pid in _pidList:
            _currentlist = self.finalize_results(_pid)
            _final_recommended_list += _currentlist
        _final_recommended_list = list(set(_final_recommended_list))
        get_logger().mSetRecommend(_final_recommended_list)

    def finalize_results(self, aPid):
        _pid = aPid
        _filtered_dict = self.getfilteredict(_pid, "_results")
        self.update_results(_filtered_dict)
        _filtered_dict = self.getfilteredict(_pid, "_log")
        self.update_results(_filtered_dict)
        _filtered_dict = self.getfilteredict(_pid, "_recommend")
        return  self.extract_list(_filtered_dict)

    def extract_list(self, aResult) :
        _resdict = aResult
        _current_list =  []
        for _key, _value in _resdict.items():
            _current_list +=  _value
        return _current_list

    def getfilteredict(self, aPid, aFilter):
        _pid = aPid
        _filter = aFilter
        _filtered_dict = {k: v for k, v in self.resdict.items() if (_pid in k) and _filter in k}
        return _filtered_dict

    def update_results(self, aResult):
        _resdict = aResult
        for _key, _value in _resdict.items():
            if not isinstance(_value, dict):
                ebLogError(f"*** Healthcheck - update_results: Skipping {_key} because {_value} is not a dict.")
                continue
            get_logger().mUpdateJsonMap(_value)

