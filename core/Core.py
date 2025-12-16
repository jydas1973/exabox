"""
 Copyright (c) 2014, 2021, Oracle and/or its affiliates. 

NAME:
    Core - Basic functionality

FUNCTION:
    Provide basic/core APIs
    Initialize global Context

NOTE:
    None

History:
    mirivier    08/21/2014 - Create file
    ndesanto    10/02/2019 - 30374491 - EXACC PYTHON 3 MIGRATION BATCH 01 
"""
from __future__ import print_function

__version__ = '2.0.7'
__revision__ = "$Id: Core.py /main/18 2021/09/02 10:52:47 jesandov Exp $"

version_info = (2, 0, 7, 'Tequila', 0)

__all__ = ['exaBoxCoreInit', 'exaBoxCoreShutdown', 'ebExit', 'ebCoreContext']

from exabox.core.Context import exaBoxContext, set_gcontext, get_gcontext
from exabox.config.Config import exaBoxConfigFileReader, exaBoxProcessArgs
import sys, os, re

#
# Globals and Constants
#
ebCoreStateDefault     = 0
ebCoreStateInitialized = 1

gCoreState   = ebCoreStateDefault
gCoreOptions = None
gCoreObject  = None

def exaBoxCoreShutdown():

    global gCoreState
    if gCoreState != ebCoreStateInitialized:
        # TODO: Log Warning : State different what was expected
        return
    gCoreState = ebCoreStateDefault

def ebCoreContext():

    global gCoreState
    if gCoreState != ebCoreStateInitialized:
        return None
    return gCoreObject

def ebSetCoreObject(aCoreObject):
    global gCoreObject
    gCoreObject = aCoreObject

def ebGetCoreObject():
    global gCoreObject
    return gCoreObject

def exaBoxCoreInit(aOptions, aReload=False):

    global gCoreState
    if not aReload and gCoreState == ebCoreStateInitialized:
        return gCoreObject

    rOptions = aOptions

    # Keep the same options when reload command
    persist = None
    if aReload:
        rOptions = get_gcontext().mGetOptions()
        persist  = get_gcontext().mGetPersistKV()

    # Process sys args and configuration / file
    options = exaBoxProcessArgs(rOptions)
    config  = exaBoxConfigFileReader(options)

    global gCoreOptions
    gCoreOptions = rOptions

    global gCoreConfig
    gCoreConfig = config

    global gCoreContext
    gCoreContext = exaBoxContext(gCoreOptions, gCoreConfig, aPersistKv=persist)
    set_gcontext(gCoreContext)

    # Push config file parameters/options in Global Context
    gCoreContext.mSetConfigOptions(config)
    gCoreContext.mSetArgsOptions(options)

    gCoreState = ebCoreStateInitialized

    # set Global coreObject
    _coreObject = exaBoxCore(gCoreContext, gCoreOptions)
    ebSetCoreObject(_coreObject)

    return ebGetCoreObject()

def ebExit(aExitCode, aMsg=None):

    if aMsg:
        print('* EXIT *', aMsg)
    sys.exit(aExitCode)

class exaBoxCore(object):

    def __init__(self, aContext, aOptions):

        self.__options = aOptions
        self.__context = aContext

    def mGetContext(self):
        return self.__context

    def mGetLabel(self):

        label = "UNKNOWN"
        try:
            if os.path.exists("config/label.dat"):
                with open('config/label.dat') as f:
                    return f.read().strip()
        except:
            return label
            

    def mGetVersion(self):

        version = '.'.join([str(num) for num in version_info[:3]])
        release = version_info[3]
        try:
            if os.path.isfile('config/release.dat'):
                with open('config/release.dat') as f:
                    tokens = [match for match in re.findall('([a-zA-Z0-9\.]*)', f.read()) if match]
                return tokens[1], tokens[3]
            else:
                return version, release 
        except:
            return version, release
