#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/common/ebRemoteManagmentInstaller.py /main/1 2021/04/16 12:46:05 jesandov Exp $
#
# ebRemoteManagmentInstaller.py
#
# Copyright (c) 2021, Oracle and/or its affiliates. 
#
#    NAME
#      ebRemoteManagmentInstaller.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    04/05/21 - Creation
#

import os

from exabox.exatest.common.ebGeneralInstaller import ebGeneralInstaller

from exabox.BaseServer.BaseConfig import BaseConfig
from exabox.BaseServer.BaseLogMgnt import BaseLogMgnt
from exabox.BaseServer.AsyncProcessing import ProcessManager

class ebRemoteManagmentInstaller(ebGeneralInstaller):

    def __init__(self, aExacloudPath, aExaboxConf, aVerbose=False):

        super().__init__(aExacloudPath, aExaboxConf, aVerbose)
        self.__shared = None
        self.__basicConfig = None

    def mGetBasicConfig(self):
        return self.__basicConfig

    #######################
    # GETTERS AND SETTERS #
    #######################

    def mGetShared(self):
        return self.__shared

    def mGetBasicConfigValue(self, aKey):
        return self.__basicConfig.mGetConfigValue(aKey)

    def mSetBasicConfigValue(self, aKey, aValue):
        self.__basicConfig.mGetConfig()[aKey] = aValue

    #################
    # CLASS METHODS #
    #################

    def mInstall(self, aExacloudUtil):

        _config = BaseConfig(os.path.join(self.mGetExacloudPath(), "exabox/managment"))
        _async = ProcessManager()

        _shared = {
            'config': _config,
            'log': BaseLogMgnt(_config),
            'util': aExacloudUtil,
            'exatest': False,
            'async': _async
        }

        self.__basicConfig = _config
        self.__shared = _shared

# end of file
