"""
 Copyright (c) 2014, 2022, Oracle and/or its affiliates. 

NAME:
    profile_parser.py - added for hc v2 

FUNCTION:
    define functions for loading and parsing profile.

NOTE:
    None

History:
    bhuvnkum    02/19/2018 - Creation

"""

import six
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogDebug
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
from exabox.healthcheck.hcconstants import HcConstants, gCheckNameFunctionMap, LOG_TYPE


class ProfileParser(object):
    """
    class respponsible for parsing profile and creating checklist based on
    input params.
    TODO:
        1) Add methods to get profile CheckParams
        Class contains methods to read, parse, validate custom profile 
    """

    def __init__(self, aCheckParser, aJsonProfile):
        self.__jsonProfile  = aJsonProfile
        self.__dictProfile   = {}
        self.__chkParam     = {}
        self.__hcconf       = {}
        self.__oCheckParser = aCheckParser

    def mInitProfileParser(self):
        _ret = False
        try:
            if self.validateProfile(self.__jsonProfile) == True:
                ebLogDebug("*** healthcheck profile validation successful")
                self.__dictProfile = self.parseProfile(self.__jsonProfile)
                _ret = True
            else:
                ebLogError("*** profile validation failed")
        except:
            ebLogError("*** Profile parser initialization failed")
        return _ret
    
    def mGetJsonProfile(self):
        return self.__jsonProfile

    def mGetProfileTargetList(self):
        return self.__dictProfile.get(HcConstants.PROFILE_TARGET)

    def mGetProfileTagList(self):
        return self.__dictProfile.get(HcConstants.PROFILE_TAGS)

    def mGetResultLevel(self):
        return self.__dictProfile.get(HcConstants.RESULT_LEVEL)
    
    def mGetCustomCheckList(self):
        return self.__dictProfile.get(HcConstants.PROFILE_CUSTOM_CHK)
    
    def mGetProfileName(self):
        return self.__dictProfile.get(HcConstants.PROFILE_NAME)
    
    def mGetCheckParam(self):
        return self.__chkParam
    
    def mGetCheckParamForId(self, aChkId):
        if aChkId in self.__chkParam.keys():
            return self.__chkParam[aChkId]
        else:
            return {}

    def mGetHcConf(self):
        return self.__hcconf

    def mDumpProfile(self):
        _jconf = self.mGetJsonProfile()
        
        ebLogDebug("dump profile: \n %s" %(_jconf))

    def validateProfile(self, aJsonChecklist):
        _ret = True
        _jconf = aJsonChecklist
        _valid_key_names = [HcConstants.PROFILE_NAME, HcConstants.CHECK_LIST, HcConstants.RESULT_LEVEL, HcConstants.CHECK_PARAM]
        _must_key_names      = (_valid_key_names[0], _valid_key_names[1], _valid_key_names[2])

        #TODO: validate preprov/postprov tag mutual exclusive
        #TODO: add more validation for checkparams
        if (not _jconf) or (not all(key in _jconf for key in _must_key_names)):
            ebLogError("*** profile: %s does not contain all must key names(%s)" %(_jconf, _must_key_names))
            return False
        
        
        for k, v in _jconf[HcConstants.CHECK_LIST].items():
            
                if(k == HcConstants.PROFILE_TARGET):
                    _targetList = self.__oCheckParser.mGetTargetList()
                    if (HcConstants.ALL not in v)  and not all(key in _targetList for key in v):
                        ebLogError("target (%s) in profile is not valid target, allowed targets %s" % (v, str(_targetList)))
                        _ret = False

                if(k == HcConstants.PROFILE_TAGS):
                    _tagList = self.__oCheckParser.mGetTagList()
                    if (HcConstants.ALL not in v) and not all(key in _tagList for key in v):
                        ebLogError("tags (%s) in profile is not valid, allowed tags %s" % (v, str(_tagList)))
                        _ret = False
                
                if(k == HcConstants.PROFILE_ALERT_LEVEL):
                    _alertLevelList = self.__oCheckParser.mGetAlertLevelList()
                    if (HcConstants.ALL not in v) and v not in _alertLevelList:
                        ebLogError("alert level (%s) in profile is not valid, allowed alert levels %s" % (v, str(_alertLevelList)))
                        _ret = False
        
        return _ret
     
                 
    def parseProfile(self, aJsonChecklist):
        _json_profile  = {}

        _jconf = aJsonChecklist
        _json_profile[HcConstants.PROFILE_NAME] =  _jconf[HcConstants.PROFILE_NAME]
        oCheckParser = self.__oCheckParser
        _master_chklist = oCheckParser.mGetTagCheckList()
        
        #parse profile to fetch check list
        for k, v in _jconf[HcConstants.CHECK_LIST].items():
            _json_profile[k] = v
        
        _json_profile[HcConstants.RESULT_LEVEL] = _jconf[HcConstants.RESULT_LEVEL]
        
        if HcConstants.PROFILE_CUSTOM_CHK in _jconf.keys():
            _json_profile[HcConstants.PROFILE_CUSTOM_CHK] = _jconf[HcConstants.PROFILE_CUSTOM_CHK]
        
        if HcConstants.CHECK_PARAM in _jconf.keys():
            for _chk, v in _jconf[HcConstants.CHECK_PARAM].items():
                if _chk.isdigit():
                    if _chk in _master_chklist[HcConstants.ALL]:
                        self.__chkParam[_chk] = v
                    else:
                        ebLogError("*** Parsing CheckParams, check %s not found in master check list" %(_chk))
                else:
                    _chkId = self.__oCheckParser.mGetCheckId(_chk)
                    if _chkId is not None:
                        self.__chkParam[_chkId] = v
                    else:
                        ebLogError("*** Parsing CheckParams, check %s not found in master check list" %(_chk))
            
        if HcConstants.HCCONF in _jconf.keys():
            self.__hcconf = _jconf[HcConstants.HCCONF]
        
        return _json_profile

    def buildChecklist(self):
        oCheckParser = self.__oCheckParser
        _profile_dict = self.__dictProfile
        _master_chklist = oCheckParser.mGetTagCheckList()
        _checklist = []

        if _profile_dict is None:
            return _checklist

        def _intersect(a, b, c):
            return list(set(a) & set(b) & set(c))

        def _getList(aCheckList):
            _list = []
            for _chk in aCheckList:
                if _chk.isdigit():
                    if _chk in _master_chklist[HcConstants.ALL]:
                        _list.append(_chk)
                    else:
                        ebLogError("*** check %s not found in master check list" %(_chk))
                else:
                    _chkId = oCheckParser.mGetCheckId(_chk)
                    if _chkId is not None:
                        _list.append(_chkId)
                    else:
                        ebLogError("*** check %s not found in master check list" %(_chk))
            return _list

        if HcConstants.PROFILE_TAGS in _profile_dict.keys():
            _targetCheckList = []
            if HcConstants.PROFILE_TARGET in _profile_dict.keys():
                for _target in _profile_dict[HcConstants.PROFILE_TARGET]:
                    _targetCheckList += _master_chklist[_target]

            _tagCheckList = []
            for _tag in _profile_dict[HcConstants.PROFILE_TAGS]:
                _tagCheckList += _master_chklist[_tag]

            _alertCheckList = []
            if HcConstants.PROFILE_ALERT_LEVEL in _profile_dict.keys():
                _alertList = oCheckParser.mGetAlertLevelList()
                
                #start from alert level index and add all above that level
                if _profile_dict[HcConstants.PROFILE_ALERT_LEVEL] == HcConstants.ALL:
                    _startIndex = 0 
                else:
                    _startIndex = _alertList.index(_profile_dict[HcConstants.PROFILE_ALERT_LEVEL])
                 
                for i in six.moves.range(_startIndex,len(_alertList)):
                    _alertCheckList += _master_chklist[_alertList[i]]
            
            #get intersect of target , tag and alert checklists            
            _checklist = _intersect(_targetCheckList, _tagCheckList, _alertCheckList)

            #include checks included exclusively
            if HcConstants.PROFILE_INCLUDE in _profile_dict.keys():
                _includeList = _getList(_profile_dict[HcConstants.PROFILE_INCLUDE])
                _checklist += _includeList
                
            #exclude checks included exclusively
            if HcConstants.PROFILE_EXCLUDE in _profile_dict.keys():
                _excludeList = _getList(_profile_dict[HcConstants.PROFILE_EXCLUDE])
                _checklist = list(set(_checklist) - set(_excludeList))

        if HcConstants.PROFILE_CUSTOM_CHK in _profile_dict.keys():
            _checklist += _master_chklist[HcConstants.CUSTOMCHECK]
            
        _checklist = list(set(_checklist))   
         
        return _checklist
