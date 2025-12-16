"""
 Copyright (c) 2014, 2021, Oracle and/or its affiliates. 

NAME:
    bmcutil - Some common utilities for bmc

FUNCTION:
    Provides some common utilities for bmc

NOTE:
    None

"""
import os
import json
import sys
import traceback
from inspect import getframeinfo, stack
from exabox.log.LogMgr import ebLogBMCInfo, ebLogBMCError, ebLogBMCWarn 
from exabox.log.LogMgr import ebLogBMCCritical, ebLogBMCDebug

def add_debug_info(log_func):
    caller = getframeinfo(stack()[1][0])
    debug_str = os.path.basename(caller.filename) + " :" + \
           caller.function + '@' + \
           str(caller.lineno) + ': '
    def new_log_func(aString):
        return log_func(debug_str + str(aString))
    return new_log_func

def debug_info():
    caller = getframeinfo(stack()[2][0])
    return os.path.basename(caller.filename) + " :" + \
           caller.function + '@' + \
           str(caller.lineno) + ': '
 
def logDebug(aString):
    aString = debug_info() + aString
    ebLogBMCDebug(aString)

def logError(aString):
    aString = debug_info() + aString
    ebLogBMCError(aString)

def logWarn(aString):
    aString = debug_info() + aString
    ebLogBMCWarn(aString)

def logInfo(aString):
    aString = debug_info() + aString
    ebLogBMCInfo(aString)

def logCritical(aString):
    aString = debug_info() + aString
    ebLogBMCCritical(aString)

class BmcUtil:
    def __init__(self, logger):
        self.logger = logger

    def readFile(self, fn):
        """
        Returns the content of the file name fn as string.
        """
        content = ''
        try:
            with open(fn) as f:
                content = f.read()
        except Exception as e:
            self.logger.error('Could not read file: %s [%s]' % (fn, e))
        return content

    def writeFile(self, content, fn, ignoreError=True):
        try:
            with open(fn, 'w') as f:
                f.write(content)
        except Exception as e:
            self.logger.error('Could not write:%s [%s]' % (fn, e)) 
            if not ignoreError:
                raise
            return False
        return True

    def getParsedJson(self, fn, ignoreError=False):
        pj = {}
        try:
            with open(fn) as f:
                pj = json.load(f)
        except Exception as e:
            self.logger.error('Could not parse json file: %s [%s]' % (fn, e))
            if not ignoreError:
                raise
        return pj

    def logFileContent(self, prefixMsg, fn):
        if not fn:
            self.logger.info(str(prefixMsg) + ': <empty filename>')
            return
        self.logger.info(str(prefixMsg) + ': path   :\n%s' % fn)
        self.logger.info(str(prefixMsg) + ': content:\n%s' % (self.readFile(fn),))

class BmcConfig(object):
    def __init__(self, logger, fn='vcncloud/bmcconfig.json'):
        self.logger = logger
        self.util = BmcUtil(self.logger)
        self.__configJson = self.util.getParsedJson(fn, ignoreError=True)

    def getValue(self, keyPath, default):
        cur = self.__configJson
        try:
            for key in keyPath:
                cur = cur[key]
        except Exception as e:
            self.logger.warning('Could not find config key: %s' % (keyPath,))
            cur = default
            self.logger.warning('Using default: %s' % (cur,))
        return cur


