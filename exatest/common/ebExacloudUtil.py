"""

 $Header:

 Copyright (c) 2018, 2024, Oracle and/or its affiliates.

 NAME:
    ebExacloudUtil.py - Base Class for Agent and Enviroment testing

 DESCRIPTION:
    Use this class when is necessary to test the Agent or the Enviroment

 NOTES:
    None

 History:

    MODIFIED   (MM/DD/YY)
    ririgoye    06/18/24 - Bug 36746656 - PYTHON 3.11 - EXACLOUD NEEDS TO
                           UPDATE DEPRECATED/OLDER IMPORTS DYNAMICALLY
    gparada     06/22/23 - 35213979 Override workers, adding typing
    aypaul      12/05/21 - Enh33638849 Support elastic cases with Unit testing.
    aypaul      08/19/21 - Bug#33250436 Pass basepath from exatest execution to
                           create files in the local FS.
    jejegonz    11/19/20 - 32047521 - Delete gLogMgrConsole import, don't used anymore.
    ndesanto    06/09/20 - Enable MySQL
    rajsag      05/13/20 - THE CCA EXACLOUD CHANGES FOR THE TWO API SUPPORT
                           CREATE USER AND DELETE USER
    ndesanto    09/19/19 - 30294648 - IMPLEMENT PYTHON 3 MIGRATION WHITELIST ON EXATEST
    ndesanto    05/27/19 - Added isOracleDB method that retuerns the type of DB used
    ndesanto    05/07/19 - Added support for request backup to request_archive
    jesandov    08/15/18 - Creation of the file
"""

import os
import sys
import time
import json
import copy
import socket
import logging

try:
    from collections import OrderedDict
except ImportError:
    from collections.abc import OrderedDict

try:
    from collections import Mapping
except ImportError:
    from collections.abc import Mapping

from exabox.core.Node import exaBoxNode
from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogInit
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.core.Context import exaBoxContext, set_gcontext
from exabox.config.Config import exaBoxConfigFileReader, exaBoxProcessArgs
from exabox.tools.ebTree.ebTree import ebTree
from exabox.network.Local import exaBoxLocal
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.core.DBStore import ebGetDefaultDB
from exabox.exakms.ExaKmsSingleton import ExaKmsSingleton

from exabox.exatest.common.ebOedaInstaller import ebOedaInstaller
from exabox.exatest.common.ebAgentInstaller import ebAgentInstaller
from exabox.exatest.common.ebDatabaseInstaller import ebDatabaseInstaller
from exabox.exatest.common.ebRemoteManagmentInstaller import ebRemoteManagmentInstaller

class ebJsonObject(dict):

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __deepcopy__(self, memo=None):
        return ebJsonObject(copy.deepcopy(dict(self), memo=memo))


class ebExacloudUtil:

    def __init__(self, aResourcesPath=None, aGenerateDatabase=False, \
                 aExatestAgent=False, aUseOeda=False, aDeploy=False, \
                 aGenerateRemoteEC=False, isElasticOperation=None):

        # Calculate Exacloud path
        _exacloudPath = os.getcwd()
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]
        os.chdir(_exacloudPath)
        self.__exacloudPath = _exacloudPath

        # Validate basepath
        _path = 'exabox/exatest/common/resources'
        self.__resourcesPath = os.path.abspath(_path)
        if aResourcesPath and os.path.isdir(str(aResourcesPath)):
            self.__resourcesPath = os.path.abspath(str(aResourcesPath))

        # The other variables
        self.__deploy = aDeploy

        self.__installerDB = None
        self.__installerAgent = None
        self.__installerOeda = None
        self.__remoteec = None

        self.__lastctx = None

        self.__config = None
        self.__exaboxCfg = None
        self.__extraCfg = None

        self.mBootstrap(aGenerateDatabase, aExatestAgent, aUseOeda, aGenerateRemoteEC, isElasticOperation)

    #######################
    # GETTERS AND SETTERS #
    #######################

    def mIsDeploy(self):
        return self.__deploy

    def mSetDeploy(self, aValue):
        self.__deploy = aValue

    def mGetRemoteEC(self):
        return self.__remoteec

    def mSetRemoteEC(self, aValue):
        self.__remoteec = aValue

    def mGetExacloudPath(self):
        return self.__exacloudPath

    def mSetExacloudPath(self, aValue):
        self.__exacloudPath = aValue

    def mGetResourcesPath(self):
        return self.__resourcesPath

    def mSetResourcesPath(self, aPath):
        self.__resourcesPath = aPath

    def mGetInstallerDB(self):
        return self.__installerDB

    def mSetInstallerDB(self, aValue):
        self.__installerDB = aValue

    def mGetInstallerAgent(self) -> ebAgentInstaller:
        return self.__installerAgent

    def mSetInstallerAgent(self, aValue:ebAgentInstaller):
        self.__installerAgent = aValue

    def mGetInstallerOeda(self):
        return self.__installerOeda

    def mSetInstallerOeda(self,  aValue):
        self.__installerOeda = aValue

    def mGetLastContext(self):
        return self.__lastctx

    def mSetLastContext(self, aValue):
        self.__lastctx = aValue

    def mGetConfig(self):
        return self.__config

    def mSetConfig(self, aValue):
        self.__config = aValue

    def mGetExtraCfg(self):
        return self.__extraCfg

    def mSetExtraCfg(self, aValue):
        self.__extraCfg = aValue

    def mGetExaboxCfg(self):
        return self.__exaboxCfg

    def mSetExaboxConf(self, aValue):
        self.__exaboxCfg = aValue

    #################
    # CLASS METHODS #
    #################

    @staticmethod
    def mReadJson(aPath):

        def mCheckDuplicated(aJson):
            _newDict = {}

            for _key, _value in aJson:
                if _key in list(_newDict.keys()):
                    raise ValueError("Duplicated key: {0}".format(_key))
                else:
                    _newDict[_key] = _value
            return _newDict

        with open(aPath) as _file:
            _data = _file.read()
            _dictobj = json.loads(_data, object_pairs_hook=mCheckDuplicated)
            return ebJsonObject(_dictobj)

    @staticmethod
    def mDeepUpdate(aDict1, aDict2):
        """
        Copy json content of Dict2 into Dict1

        :param:aDict1:target json where to apply the changes
        :param:aDict2:src json where to apply the changes

        :return:json with both tags the one ones of aDict1 and aDict2
        """
        result = copy.deepcopy(dict(aDict1))

        for key, value in aDict2.items():
            if isinstance(value, Mapping):
                result[key] = ebExacloudUtil.mDeepUpdate(result.get(key, {}), value)
            else:
                result[key] = copy.deepcopy(aDict2[key])

        return ebJsonObject(result)


    def mBootstrap(self, aGenerateDatabase, aExatestAgent, aUseOeda, aGenerateRemoteEC, isElasticOperation):

        # Read resources config
        self.mReadResourcesConfig(isElasticOperation)

        # Create addons installation path
        _installPath = os.path.join(self.mGetExacloudPath(), "opt")

        # Verbose
        try:
            _verbose = self.mGetExtraCfg()['exatest']['log_level'] < logging.DEBUG
        except KeyError:
            _verbose = False

        if aGenerateDatabase or aExatestAgent or \
           aGenerateRemoteEC or self.mIsDeploy():

            # Database
            try:
                _port = self.mGetExtraCfg()['exatest']['mysql_port']
            except KeyError:
                _port = 21000

            _db = ebDatabaseInstaller(self.mGetExacloudPath(), self.mGetExaboxCfg(), self.mIsDeploy(), _port, _verbose)

            _mysqlPath = os.path.join(_installPath, "mysql")
            _db.mExecuteLocal("mkdir -p {0}".format(_mysqlPath))
            _db.mInstall(_mysqlPath)

            self.mSetInstallerDB(_db)

        # OEDA
        if aUseOeda:

            _oeda = ebOedaInstaller(self.mGetExacloudPath(), self.mGetExaboxCfg(), _verbose)

            if "r1" in self.mGetExaboxCfg() and self.mGetExaboxCfg()['r1']:
                _oeda.mSetOedaDir(self.mGetExaboxCfg()['oeda_dir'])

            else:
                _oedaPath = os.path.join(_installPath, "oeda")
                _oeda.mExecuteLocal("mkdir -p {0}".format(_oedaPath))
                _oeda.mInstall(_oedaPath)

            self.mSetInstallerOeda(_oeda)

        # Agent
        if aExatestAgent:

            _agent = ebAgentInstaller(self.mGetExacloudPath(), self.mGetExaboxCfg(), \
                                      self.mGetConfig(), _verbose)

            _agentPath = os.path.join(_installPath, "agent")
            _agent.mExecuteLocal("mkdir -p {0}".format(_agentPath))
            _agent.mInstall(_agentPath)

            self.mSetInstallerAgent(_agent)

        # Remote EC
        if aGenerateRemoteEC:

            _remoteec = ebRemoteManagmentInstaller(self.mGetExacloudPath(), \
                                                   self.mGetExaboxCfg(), _verbose)

            _remoteec.mInstall(self)
            self.mSetRemoteEC(_remoteec)


    def mReadResourcesConfig(self, isElasticOperation):

        #Read the Configuration Files
        _path = self.mGetResourcesPath()
        _config = ebExacloudUtil.mReadJson(os.path.join(_path, 'config.json'))

        #config the parameter of the exabox.conf
        if self.mIsDeploy():
            _exabox = os.path.join(self.mGetExacloudPath(), "config/exabox.conf")
            _exaboxCfg = ebExacloudUtil.mReadJson(_exabox)

        else:

            _exaboxCfg = exaBoxConfigFileReader(_config)
            _exaboxCfg['log_dir'] = os.path.abspath(self.mGetOutputDir())

        # Load extra args
        _extraCfg = {}

        if os.path.exists("config/exatest_extra_config.conf"):

            _extraCfg = ebExacloudUtil.mReadJson("config/exatest_extra_config.conf")

            # Deep update with extra args
            _exaboxCfg = ebExacloudUtil.mDeepUpdate(_exaboxCfg, _extraCfg['exacloud'])
            _config = ebExacloudUtil.mDeepUpdate(_config, _extraCfg['args'])

        _config['optArgs'] = ebJsonObject(_config)

        # Correctness of the basepath
        if not os.path.exists(_config["configpath"]):
            if isElasticOperation is not None:
                _config['configpath'] = os.path.join(_path, "elastic_sample.xml")
            else:
                _config['configpath'] = os.path.join(_path, "sample.xml")

        # Update in object
        self.mSetExaboxConf(_exaboxCfg)
        self.mSetExtraCfg(_extraCfg)
        self.mSetConfig(_config)

    def mPrepareEnviroment(self):

        #Prepare the Context
        _ctx = exaBoxContext(OrderedDict(self.mGetConfig()), OrderedDict(self.mGetExaboxCfg()), aBasePath=self.mGetExacloudPath())
        self.mGetConfig().dis_console = True
        ebLogInit(_ctx, self.mGetConfig())
        set_gcontext(_ctx)

        _ctx.mSetArgsOptions(self.mGetConfig()['optArgs'])

        #Init CluControl
        _node = exaBoxNode(_ctx, aLocal=True)
        _node.mConnect()
        _clubox = exaBoxCluCtrl(aCtx=_ctx, aNode=_node, aOptions=self.mGetConfig())
        _clubox.mSetConfigPath(self.mGetConfig().configpath)

        #Init DB
        if self.mGetInstallerDB():
            self.mGetInstallerDB().mInitDB(_ctx, self.mGetExaboxCfg())

        if self.mGetRemoteEC():
            self.mGetRemoteEC().mGetShared()['db'] = ebGetDefaultDB()

        _singleton = ExaKmsSingleton()
        _singleton.mInitExaKmsFileSystem()

        _ctx.mSetExaKmsSingleton(_singleton)
        self.mSetLastContext(_ctx)
        return _clubox

    def mGetOedaDir(self):
        return self.mGetInstallerOeda().mGetOedaDir()

    def mGetOutputDir(self):
        _sf = 'log/exatest'
        _d = os.listdir(_sf)
        _d = [x for x in _d if x != "oeda"]
        _d.sort(key=lambda x: os.path.getmtime(os.path.join(_sf, x)))
        return os.path.join(_sf, _d.pop())

# end of file
