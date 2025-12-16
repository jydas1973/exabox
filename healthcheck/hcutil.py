"""
 Copyright (c) 2014, 2020, Oracle and/or its affiliates. 

NAME:
    hcutil.py - added for hc v2 

FUNCTION:
    define util functions, class for healthcheck infra.

NOTE:
    None

History:
    bhuvnkum    02/19/2018 - Creation

"""


import json
import os, sys

from exabox.log.LogMgr import ebLogError



class Singleton(type):
    """Metaclass for creating any class as Singleton
    just add below line in any class to make it Singleton. e.g. 
    __metaclass = Singleton
     ."""
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
        

class HcUtil(object):
    """
    Class method used in common for healthcheck. 
    """

########utility functions 


# Common method to log error code and error message
#
# Read configurarion file 
#
def mReadConfigFile(aConfigFilePath):
    _cf = None
    try:
        _f  = open(aConfigFilePath)
        _cf = json.loads(_f.read())
        _f.close()
    except:
        ebLogError('*** Could not access/read %s file' %(aConfigFilePath))
        return {}
    return _cf

# # for current func name, specify 0 or no argument.
# # for name of caller of current func, specify 1.
# # for name of caller of caller of current func, specify 2. etc.
def mGetCurFuncName(parent = 0):
    currentFuncName = lambda n=0: sys._getframe(n + 1).f_code.co_name
    return currentFuncName(parent)






