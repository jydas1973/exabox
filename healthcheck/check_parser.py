"""
 Copyright (c) 2014, 2022, Oracle and/or its affiliates. 

NAME:
    check_parser.py - added for hc v2 

FUNCTION:
    define functions for loading and parsing master checklist 

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
from multiprocessing import Process

from exabox.healthcheck.hcutil import mReadConfigFile
from exabox.healthcheck.hcconstants import HcConstants #, gCheckNameFunctionMap
from exabox.healthcheck.hclogger import get_logger, mRecordError


class CheckParser(object):
    """
    class respponsible for parsing master checklist and maintaining 
    a tag-based list. 
    TODO:
        1) Add methods to get parse default CheckParams
    """
    def __init__(self, aJsonFilePath):
        self.__masterJson       = None
        self.__dictTagCheckList = None
        self.__dictCheckNameId  = {}
        self.__masterJsonPath = aJsonFilePath

    
    def mInitCheckParser(self):
        _ret = False
        try:
            self.__masterJson = self.loadMasterChecklist(self.__masterJsonPath)
            if (self.validateChecklist(self.__masterJson)) == True:
                ebLogDebug("*** healthcheck master checklist validation successful")
                self.__dictTagCheckList = self.parseChecklist(self.__masterJson)
                _ret = True
            else:
                ebLogError("*** healthcheck master checklist validation failed") 
        except:
             ebLogError("*** Profile parser initialization failed ")
        return _ret
            
    
    def mGetMasterCheckConfig(self):
        return copy.copy(self.__masterJson)

    def mGetTagCheckList(self):
        return self.__dictTagCheckList

    def mGetTargetList(self):
        return self.__masterJson[HcConstants.TARGET_LIST]
    
    def mGetTagList(self):
        return self.__masterJson[HcConstants.TAG_LIST]
    
    
    def mGetCheckList(self):
        return self.__masterJson[HcConstants.CHECK_LIST]
    
    def mGetAlertLevelList(self):
        return self.__masterJson[HcConstants.ALERT_LEVEL]

    def mGetCheckTagList(self, aChkId):
        return self.__masterJson[HcConstants.CHECK_LIST][aChkId][HcConstants.CHK_TAGS]

    def mGetCheckTargetList(self, aChkId):
        return self.__masterJson[HcConstants.CHECK_LIST][aChkId][HcConstants.CHK_TARGET]
    
    def mGetCheckNameIdList(self):
        return self.__dictCheckNameId
    
    def mGetCheckId(self, aCheckName):
        if aCheckName in self.__dictCheckNameId.keys():
            return self.__dictCheckNameId[aCheckName]
        else:
            ebLogDebug("check id wrt %s not found" %(aCheckName))
            return None
        
    def mGetCheckName(self, aChkId):
        return self.__masterJson[HcConstants.CHECK_LIST][aChkId][HcConstants.CHK_NAME]

    def mGetCustomerDisplayTag(self, aChkId):
        if HcConstants.RES_CUSTOMERTAG in self.__masterJson[HcConstants.CHECK_LIST][aChkId].keys():
            return self.__masterJson[HcConstants.CHECK_LIST][aChkId][HcConstants.RES_CUSTOMERTAG]
        else:
            return self.__masterJson[HcConstants.CHECK_LIST][aChkId][HcConstants.CHK_NAME]
    
    def mGetCheckAlertLevel(self, aChkId):
        return self.__masterJson[HcConstants.CHECK_LIST][aChkId][HcConstants.CHK_ALERT_LEVEL]

    def loadMasterChecklist(self, aPath):
        checklist_filepath = aPath
        return mReadConfigFile(checklist_filepath)

    def validateChecklist(self, aJsonChecklist):

        _jconf = aJsonChecklist
        
        #valid key-names for checklist
        _valid_key_names = [HcConstants.VERSION, HcConstants.TARGET_LIST, HcConstants.TAG_LIST, HcConstants.CHECK_LIST, HcConstants.ALERT_LEVEL, HcConstants.REFERENCE, HcConstants.CHECK_PARAM, HcConstants.COMMENTS]
        _must_key_names      = (_valid_key_names[0], _valid_key_names[1], _valid_key_names[2],  _valid_key_names[3], _valid_key_names[4])

        #valid key-names for check details of each individual check
        _valid_chk_fields = [HcConstants.CHK_NAME, HcConstants.CHK_DESC, HcConstants.CHK_TARGET, HcConstants.CHK_TAGS, HcConstants.CHK_REF, HcConstants.CHK_ALERT_LEVEL]
        _must_chk_fields = [_valid_chk_fields[0], _valid_chk_fields[1], _valid_chk_fields[2], _valid_chk_fields[3], _valid_chk_fields[4]]

        if not all(key in _jconf.keys() for key in _must_key_names):
            return mRecordError("911", "All required keys %s not found in checklist" % str(_must_key_names))

        for _chk_id, _chk_details in _jconf[HcConstants.CHECK_LIST].items():

            if not all(key in _chk_details for key in _must_chk_fields):
                _err = True
                return mRecordError("911", "All required fields %s not found in check_details" % str(_must_chk_fields))

            for k, v in _chk_details.items():
                if(k == HcConstants.CHK_TARGET):
                    if not all(key in _jconf[HcConstants.TARGET_LIST] for key in v):
                        return mRecordError("911", "target (%s) in check_fields is not valid, allowed targets %s" % (v, str(_jconf[HcConstants.TARGET_LIST])))

                if(k == HcConstants.CHK_TAGS):
                    if not all(key in _jconf[HcConstants.TAG_LIST] for key in v):
                        return mRecordError("911", "tags (%s) in check_fields is not valid tag, allowed tags %s" % (v, str(_jconf[HcConstants.TAG_LIST])))
                
                if(k == HcConstants.CHK_ALERT_LEVEL):
                    if v not in _jconf[HcConstants.ALERT_LEVEL]:
                        return mRecordError("911", "alert level (%s) in check_fields is not valid alert level, allowed alertlevels %s" % (v, str(_jconf[HcConstants.ALERT_LEVEL])))
                        
                    #TBD: validate each of alterlevel defined in levels, target, tags 
                    
        #TODO: add more validation for ref
        return True

      
    def parseChecklist(self , aMasterJson):
        """
        this function parse master checklist to create tag based 
        checklist associated with each of the tag
        """
        _jconf = aMasterJson
        _jconfKeys = list(_jconf.keys())
        _dictTag = {}
        
        if HcConstants.VERSION in _jconfKeys: 
            _dictTag[HcConstants.VERSION] =  _jconf[HcConstants.VERSION]
        
        _dictTag[HcConstants.ALL] = []
        if HcConstants.TAG_LIST in _jconfKeys:
            for _tag in _jconf[HcConstants.TAG_LIST]:
                _dictTag[_tag] = []
        
        if HcConstants.TARGET_LIST in _jconfKeys:
            for _target in _jconf[HcConstants.TARGET_LIST]:
                _dictTag[_target] = []
                
        if HcConstants.ALERT_LEVEL in _jconfKeys:
            for _alertlevel in _jconf[HcConstants.ALERT_LEVEL]:
                _dictTag[_alertlevel] = []
                
        if HcConstants.CHECK_LIST in _jconfKeys:
            for _chkid, v in _jconf[HcConstants.CHECK_LIST].items():
                self.__dictCheckNameId[v[HcConstants.CHK_NAME]] = _chkid
                for _tag in v[HcConstants.CHK_TAGS]:
                    if _tag in _dictTag.keys():
                        _dictTag[_tag].append(_chkid)
                        _dictTag[HcConstants.ALL].append(_chkid)

                for _target in v[HcConstants.CHK_TARGET]:
                    if _target in _dictTag.keys():
                        _dictTag[_target].append(_chkid)
                        _dictTag[HcConstants.ALL].append(_chkid)
                
                _alertlevel  = v[HcConstants.CHK_ALERT_LEVEL]
                if _alertlevel in _dictTag.keys():
                    _dictTag[_alertlevel].append(_chkid)
                    _dictTag[HcConstants.ALL].append(_chkid)
                        
                
                
        #TBD: store this in pickle/json for future use
        return _dictTag

   
