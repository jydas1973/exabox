"""
 Copyright (c) 2014, 2023, Oracle and/or its affiliates.

NAME:
    hclogger.py - Refactored from cluhealth to provide common logging support

FUNCTION:
    define HCConstants and enum for common usage.

NOTE:
    None

History:
    bhuvnkum    02/19/2018 - Creation

"""

import os
import json
import sys
import traceback
from inspect import getframeinfo, stack
from copy import deepcopy

from exabox.log.LogMgr import (ebLogError, ebLogInfo, ebLogWarn, ebLogDebug,
                                ebLogVerbose, ebLogHealth,  ebLogCrit)
from exabox.healthcheck.hcconstants import HcConstants, gHealthcheckError, CHK_RESULT, LOG_TYPE
from exabox.healthcheck.hcconstants import FAIL_CODE


g_logger = None
def init_logging(aCluCtrlObject, aCluHealthObject = None):
    # Rudimentary singleton
    # - thread, serialization etc is not handled
    global g_logger
    if (g_logger is None):
        g_logger = HcLogger(aCluCtrlObject, aCluHealthObject)
    return g_logger

def get_logger():
    global g_logger
    if (g_logger is None):
        errors = ["Attempt to access logger before initialization"]
        sys.exit(FAIL_CODE)
    return g_logger

#can be part of logger class itself
# Common method to log error code and error message
def mRecordError(aErrorCode, aString=None):
    """
    TBD: to be used later 
    """
    _hcResult = {}

    _hcResult["Status"] = "Fail"
    _hcResult["ErrorCode"] = aErrorCode
    if aString is None:
        _hcResult["Log"] = gHealthcheckError[_hcResult["ErrorCode"]][0]
    else:
        _hcResult["Log"] = gHealthcheckError[_hcResult["ErrorCode"]][0] + aString

    ebLogError("%s" % (_hcResult["Log"]))

    if int(aErrorCode) != 0:
        return False
    return True


class HcLogger(object):
    """
    Class contains wrapper around exacloud logging to customize healthcheck logging based on loglevel/warninglevel. 
    Also it will also facilitate adding error summary based on resultlevel. 
    """
    
    def __init__(self, aCluCtrlObject, aCluHealthObject = None):
      
        self.__ecc = aCluCtrlObject
        self.__hc = aCluHealthObject
        self.__recommend   = []
        self._jsonMap     = {}
        self.__resultLevel = LOG_TYPE.__dict__["INFO"]
        self.__debuginfo    = False
        
    def UpdateHcLogger(self, aCluHealthObject):
        self.__hc = aCluHealthObject
        self.__recommend   = aCluHealthObject.mGetRecommend()
        self._jsonMap      = aCluHealthObject.mGetJsonMap() 

    def mGetRecommend(self):
        return self.__recommend

    def mSetRecommend(self, aNewlist):
        self.__recommend = aNewlist

    def mGetResultLevel(self):
        return self.__resultLevel
        
    def mSetResultLevel(self, aResultLevel):
        self.__resultLevel = LOG_TYPE.__dict__[aResultLevel.upper()]

    def mGetStackTrace(self):
        _tb_list = traceback.format_exc()
        return ''.join(_tb_list)

    def mDebugInfo(self):
        caller = getframeinfo(stack()[3][0])
        return os.path.basename(caller.filename) + " :" + \
               caller.function + '@' + \
               str(caller.lineno) + ': '
           
           
    def mAppendLog(self, aType, aString, aJsonMap = None):
        
        if self.__debuginfo:
            aString = self.mDebugInfo() + aString
        if(self.__hc == None):
            if aType == LOG_TYPE.INFO:
                ebLogDebug(aString)
            elif aType == LOG_TYPE.VERBOSE:
                ebLogVerbose(aString)
            elif aType == LOG_TYPE.RECOMMEND:
                ebLogInfo(aString)
            elif aType == LOG_TYPE.DEBUG:
                ebLogDebug(aString)
            elif aType == LOG_TYPE.WARNING:
                ebLogWarn(aString)
            elif aType == LOG_TYPE.ERROR:
                ebLogError(aString)
            elif aType == LOG_TYPE.CRITICAL:
                ebLogCrit(aString)
            else:
                ebLogError('Health log type not set:')
                ebLogInfo(aString)
    
        else:
            ebLogHealth(LOG_TYPE.reverse_mapping(aType).upper(), aString)
            if (aType >= LOG_TYPE.RECOMMEND):
                if(self.mGetResultLevel() <= aType):
                #TBD: lock _recommend if required
                    self.__recommend.append('* %s * %s' %(LOG_TYPE.reverse_mapping(aType).upper(), aString))
                   
                if aJsonMap: 
                    if(HcConstants.RES_LOG not in list(aJsonMap.keys())):
                        aJsonMap[HcConstants.RES_LOG] = []
                    #will add in json even if it has been ignored from recommend
                    aJsonMap[HcConstants.RES_LOG].append('* %s * %s' %(LOG_TYPE.reverse_mapping(aType).upper(), aString))
                 #TBD   
#                else:
#                     ebLogHealth(LOG_TYPE.reverse_mapping[LOG_TYPE.WARNING].upper(), 'JsonMap should be passed with healthcheck loglevel >= LOG_TYPE.RECOMMEND')
            
        
    def mUpdateResult(self, aResult , aMsgDetail = {}, aCheckParam = {}):
        
        if(self.__hc == None):
            return aResult
        else:
            _resultDict  = {}
            _resultDict[HcConstants.RES_RESULT]         = aResult
            
            if HcConstants.RES_LOG in list(aMsgDetail.keys()):
                _resultDict[HcConstants.RES_LOG]            = aMsgDetail[HcConstants.RES_LOG]  
                del aMsgDetail[HcConstants.RES_LOG]
            else:
                _resultDict[HcConstants.RES_LOG] = []
                
            _resultDict[HcConstants.RES_MSGDETAIL]      = aMsgDetail
            _resultDict[HcConstants.RES_CHECKPARAM]     = aCheckParam
            return _resultDict
    
    def mGetResultTemplate(self):
        _template  = {
                    HcConstants.RES_STARTTIME  :   "",
                    HcConstants.RES_ENDTIME    :   "",
                    HcConstants.RES_HCID       :   "",
                    HcConstants.RES_PROFILE    :   "",
                    HcConstants.RES_CHKNAME    :   "",
                    HcConstants.RES_NODETYPE   :   "",
                    HcConstants.RES_NODENAME   :   "",
                    HcConstants.RES_ALERTTYPE  :   "",      # (0 - INFO, RECOMMEND, WARNING, ERROR, 4 - CRITICAL)
                    HcConstants.RES_RESULT     :   "",      # (0 - PASS, 1 - FAIL)
                    HcConstants.RES_LOG        :   [],
                    HcConstants.RES_MSGDETAIL  :   {},
                    HcConstants.RES_CHECKPARAM :   {}
                }
        return _template

    def mUpdateJsonMap(self, aResult):
        # adding local vars to make code more readable
        nodeName = HcConstants.RES_NODENAME
        hcDispStr = HcConstants.RES_DISPLAYSTRING
        hcMsgDetail = HcConstants.RES_MSGDETAIL
        testResult = HcConstants.RES_RESULT
        testName = HcConstants.RES_CHKNAME
        nodeSummary = HcConstants.RES_NODESUMMARY

        if aResult[testName] not in list(self._jsonMap.keys()):
            self._jsonMap[aResult[testName]] = {}
        self._jsonMap[aResult[testName]][aResult[nodeName]] = deepcopy(aResult)
        if hcDispStr not in self._jsonMap:
            self._jsonMap[hcDispStr] = {}

        # Customer Tag is only added for network validation specific tests in hc_master_checklist
        # If customerDisplayTag is not defined, chkName is returned
        custDisplayTag = self.__hc.mGetCheckParser().mGetCustomerDisplayTag(aResult[HcConstants.RES_HCID])

        if not custDisplayTag in self._jsonMap[hcDispStr]:
            self._jsonMap[hcDispStr][custDisplayTag] = []

        if hcMsgDetail in list(aResult.keys()) and hcDispStr in list(aResult[hcMsgDetail].keys()):
            myDisplaylist = aResult[hcMsgDetail][hcDispStr]
            for errmsg in myDisplaylist:
                if errmsg not in self._jsonMap[hcDispStr][custDisplayTag]:
                    self._jsonMap[hcDispStr][custDisplayTag].append(errmsg)

        # build dom0 wise validation summary for elastic use case
        if nodeSummary not in self._jsonMap:
            self._jsonMap[nodeSummary] = {}

        if aResult[nodeName] not in self._jsonMap[nodeSummary]:
            self._jsonMap[nodeSummary][aResult[nodeName]] = {}
            # set default values for nodeSummary
            nodeDict = {
                "testsPassed": [],
                "testsFailed": [],
                "nodeStatus": CHK_RESULT.reverse_mapping(0)
            }
            self._jsonMap[nodeSummary][aResult[nodeName]].update(nodeDict)

        if testResult in list(aResult.keys()):
            if aResult[testResult] == CHK_RESULT.reverse_mapping(1):
                self._jsonMap[nodeSummary][aResult[nodeName]]["nodeStatus"] = aResult[testResult]
                self._jsonMap[nodeSummary][aResult[nodeName]]["testsFailed"].append(custDisplayTag)
            else:
                self._jsonMap[nodeSummary][aResult[nodeName]]["testsPassed"].append(custDisplayTag)

