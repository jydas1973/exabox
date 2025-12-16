"""
 Copyright (c) 2014, 2024, Oracle and/or its affiliates.

NAME:
    DBStore - Basic DB functionality

FUNCTION:
    Provide basic/core APIs

NOTE:
    None

History:
    MODIFIED   (MM/DD/YY)
       ririgoye 02/13/24 - Bug 36215212 - Added memory diagnostics to crash
                           dump exception logging
    hnvenkat    07/30/2020 - Mask sensitive ENV variables
    vgerard     02/25/19 - Create file
    ndesanto    10/02/19 - 30374491 - EXACC PYTHON 3 MIGRATION BATCH 01 
"""

import sys
import os
import traceback
import platform
import subprocess
from datetime import datetime
import six
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.tools.Utils import mGetUsageMetrics
from exabox.core.Mask import maskSensitiveData

class CrashDump(object):

    def __init__(self, inExceptBlock=False, logFx=None):
        self.__pid  = os.getpid()
        self.__uid  = os.getuid()
        self.__euid = os.geteuid()
        # Directory name, minute granularity'
        self.__str_time = datetime.now().strftime("%Y_%m_%d_%Hh%M")
        self.__str_exception = None
        self.__str_currstack = None
        self.__extra_infos   = []
        self.__written       = False
        self.__logFx = logFx

    def __enter__(self):
        return self

    def __exit__(self, etype, value, tb):
        if etype:
            self.AddExtraInfo('Exception occured inside CrashDump: {}'.format(etype))
            self.AddExtraInfo("\n".join(traceback.format_tb(tb)))
        if not self.__written:
            self.WriteCrashDump()

    def ProcessException(self):
        etype, value,tb = sys.exc_info()
        if etype:
            # Stack of original exception
            self.__str_exception  = traceback.format_tb(tb)
            # Current stack
            self.__str__currstack = traceback.format_stack()
            self.AddExtraInfo('Exception class:{}, value: {}'.format(etype,value))
            # Retrieve memory diagnostics
            _return_json = mGetUsageMetrics()
            self.AddExtraInfo(f"Environment usage per resource: {_return_json}")

    def AddExtraInfo(self,aExtraInfo):
        if aExtraInfo:
            self.__extra_infos.append(aExtraInfo)

    def WriteCrashDump(self):
        # CWD agnostic way to get exacloud path from this file path
        _paths = os.path.split(os.path.dirname(os.path.abspath(__file__)))
        # go up until exacloud base directory (child dir is exabox)
        while (_paths[1] != 'exabox'):
            _paths = os.path.split(_paths[0]) 

        #Create a directory per crash, like: log/crashes/2019_02_26_10h35/
        _logdir = os.path.join(_paths[0],'log','crashes',self.__str_time)
        if not os.path.exists(_logdir):
            try:
                os.makedirs(_logdir, 0o755)
            except OSError:
                #Seen race condition under high load where directory was
                #Created by other Agent at the same exact time
                pass

        _filename = 'crashdump_{}.log'.format(self.__pid)
        with open(os.path.join(_logdir,_filename),'a') as fd:
            self.crashDumpOutput(fd)

        if self.__logFx:
            with open(os.path.join(_logdir,_filename),'r') as fd:
                self.__logFx(fd.read())

        self.__written = True

    def crashDumpOutput(self, aFd):
        aFd.write(datetime.now().strftime("%c"))
        try:
            # Write current process and Cmdline argument
            psout = subprocess.check_output(["ps", "-xwq", str(self.__pid)]).decode('utf8')
            aFd.write("\n{}\n".format(psout))
        except:
            pass
        aFd.write("PID: {}, UID: {}, EUID: {}\n".format(self.__pid,self.__uid,self.__euid))
        aFd.write("Linux Kernel: {}, Distribution:{}\n".format(\
                   platform.release(), platform.uname()))
        aFd.write("Python version: {}\n\n".format(sys.version))
        _environ = maskSensitiveData(os.environ)
        aFd.write("Environment:\n{}\nExtra Info:\n".format(str(_environ)))
        aFd.writelines("\n".join(self.__extra_infos))
        if isinstance(self.__str_currstack,list):
            aFd.write("\nStack to crashdump:\n")
            aFd.writelines(self.__str_currstack)
        if isinstance(self.__str_exception,list):
            aFd.write("\nRoot cause Stack:\n")
            aFd.writelines(self.__str_exception)




