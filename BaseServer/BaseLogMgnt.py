"""
 Copyright (c) 2014, 2020, Oracle and/or its affiliates. 

NAME:
    BaseLogMgnt - Basic functionality

FUNCTION:
    Simple class that log the information of the BaseServer

NOTE:
    None    

History:
    jesandov    26/03/2019 - File Creation
"""

from __future__ import print_function

import os
import time

class BaseLogMgnt(object):

    def __init__(self, aConfig, aServerLogName="server.log"):
        self.__serverFd      = None
        self.__requestsFd    = None
        self.__config        = aConfig
        self.__serverLogName = aServerLogName

    def mGetServerFd(self):
        return self.__serverFd

    def mGetRequestsFd(self):
        return self.__requestsFd

    def mGetConfig(self):
        return self.__config

    def mGetServerLogName(self):
        return self.__serverLogName

    def mOpenFd(self, aName):

        _directory = "{0}/log".format(self.__config.mGetPath())
        if not os.path.exists(_directory):
            os.mkdir(_directory)

        _file   = "{0}/{1}".format(_directory, aName)
        _fd     = open(_file, "a+")
        return _fd

    def mWrite(self, aFd, aLevel, aMsg):

        if aFd is not None:
            _str =  "{0} - ".format(time.strftime('%Y-%m-%d %H:%M:%S%z'))
            _str += "{0} - ".format(aLevel) 
            _str += "{0} - ".format(os.getpid()) 
            _str += "{0}\n".format(aMsg)
            aFd.write(_str)

    def mInit(self):

        if self.__serverFd is None:
            self.__serverFd = self.mOpenFd(self.__serverLogName)

        if self.__requestsFd is None:
            self.__requestsFd = self.mOpenFd("requests.log")

    def mClose(self):

        if self.__serverFd is not None:
            self.__serverFd.close()

        if self.__requestsFd is None:
            self.__requestsFd.close()


    def mCall(self, aString):
        self.mWrite(self.__requestsFd, "Call", aString)
        print("Call - {0}".format(aString))

    def mInfo(self, aString):
        self.mWrite(self.__serverFd, "Info", aString)
        print("Info - {0}".format(aString))

    def mDebug(self, aString):
        self.mWrite(self.__serverFd, "Debug", aString)
        print("Debug - {0}".format(aString))

    def mWarn(self, aString):
        self.mWrite(self.__serverFd, "Warn", aString)
        print("Warn - {0}".format(aString))

    def mCrit(self, aString):
        self.mWrite(self.__serverFd, "Crit", aString)
        print("Crit - {0}".format(aString))

    def mVerbose(self, aString):
        self.mWrite(self.__serverFd, "Verbose", aString)
        print("Verbose - {0}".format(aString))

    def mError(self, aString):
        self.mWrite(self.__serverFd, "Error", aString)
        print("Error - {0}".format(aString))

