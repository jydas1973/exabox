"""
 Copyright (c) 2014, 2021, Oracle and/or its affiliates. 

NAME:
    BaseConfig - Basic functionality

FUNCTION:
    Simple class that read the information of the BaseServer configuration file

NOTE:
    None    

History:
    jesandov    26/03/2019 - File Creation
"""



import os
import sys
import json
import copy
import time
import traceback

from importlib import import_module

from exabox.agent.AuthenticationStorage import ebBasicAuthStorage,ebGetHTTPAuthStorage

class BaseConfig(object):

    def __init__(self, aPrefix):

        self.__prefix     = aPrefix
        self.__endpoints  = {}
        self.__config     = {}
        self.__path       = ""
        self.__exapath    = ""
        self.__exaboxconf = {}

        self.mRefreshConfig()

    def mGetPrefix(self):
        return self.__prefix

    def mRefreshConfig(self):

        if os.path.exists(self.__prefix):
            self.__path = os.path.abspath(self.__prefix) + "/"

        if self.__path == "":
            _path = sys.argv[0]
            _path = _path[0: _path.find("{0}/".format(self.__prefix))+len(self.__prefix)+1]
            self.__path = _path

        _exapath = self.mGetPath()
        self.__exapath = os.path.abspath(_exapath[0: _exapath.find("exabox")] )

        with open(self.__path + "config/basic.conf") as _f:
            self.__config = json.loads(_f.read())

        with open(self.__path + "config/endpoints.conf") as _f:
            self.__endpoints = json.loads(_f.read())

        with open(self.__exapath + "/config/exabox.conf") as _f:
            self.__exaboxconf = json.loads(_f.read())

        #HTTP Authentication either from config or from Wallet
        _basic_auth = None
        if "auth" in list(self.__config.keys()):
            _basic_auth = ebBasicAuthStorage(self.__config["auth"])

        self.__config["auth"] = ebGetHTTPAuthStorage('remoteec_',_basic_auth, self.__exaboxconf)

    def mGetClientEndpoints(self):
        _cp = copy.deepcopy(self.__endpoints)
        list(map(lambda x: _cp[x].pop("class"), _cp))
        list(map(lambda x: _cp[x].pop("package"), _cp))
        return _cp

    def mGetEndpointClasses(self):

        _classTemplate = {}
        for _key in list(self.__endpoints.keys()):
            _class   = self.__endpoints[_key]['class']
            _package = self.__endpoints[_key]['package'] 

            try:
                _module = import_module(_package)
                _classTemplate[_key] = getattr(_module, _class)
            except ImportError:
                raise
            except Exception as e:
                self.mGetStacktrace()

        return _classTemplate

    def mGetStacktrace(self):
        sys.stderr.write("[Error Date: {0}]\n".format(time.strftime('%Y-%m-%d %H:%M:%S%z')))
        traceback.print_exc(file=sys.stderr)
        sys.stderr.write(("-"*60) + "\n")

    def mGetPath(self):
        return self.__path

    def mGetConfig(self):
        return self.__config

    def mGetConfigValue(self, aKey):
        if aKey in list(self.__config.keys()):
            return self.__config[aKey]
        else:
            return None

    def mGetExacloudPath(self):
        return self.__exapath

    def mGetExacloudConfig(self):
        return self.__exaboxconf

    def mGetExacloudConfigValue(self, aKey):
        if aKey in list(self.__exaboxconf.keys()):
            return self.__exaboxconf[aKey]
        else:
            return None

