"""
 Copyright (c) 2014, 2024, Oracle and/or its affiliates.

NAME:
    Context - Basic functionality

FUNCTION:
    Provide basic/core API for managing Core Context

NOTE:
    None

History:
    ririgoye    11/06/2024 - Bug 37229020 - EXACS EXACLOUD - OEDA_BUILD IS 
                             UPDATED ONLY WHEN EXACLOUD IS RESTARTED
    joserran    04/27/2021 - Bug 32394314 - Propagate options to agent
    gsundara    11/30/2018 - ER 28864094 (KMS)
    mirivier    08/21/2014 - Create file
"""

__version__ = '1.0.0'
__revision__ = "$Id: Context.py /main/26 2024/11/08 21:39:18 ririgoye Exp $"

version_info = (1, 0, 0, 'beta', 0)

__all__ = ['exaBoxContext', 'get_gcontext', 'set_gcontext']


import copy
import sys
import time
import os
import re

try:
    from collections import Mapping
except ImportError:
    from collections.abc import Mapping

from typing import List

from exabox.log.LogMgr import ebLogError, ebLogDebug, ebLogInfo, ebLogWarn

#
# Globals and Constants
#
ebCtxStateNone        = 0
ebCtxStateInitialized = 1
ebCtxStateFinalized   = 1 << 1

GlobalContext = None


class ReadOnlyDict(Mapping):
    '''This class take a normal dict and convert all the subdicts to
    ReadOnlyDict and all the lists to tuple type

    The objective of this class is to ensure that a given configuration is not
    changed in runtime, but explictly copyed before modification
    '''

    def __init__(self, data):
        assert(isinstance(data, dict))
        for k, v in list(data.items()):
            if isinstance(v, dict):
                data[k] = ReadOnlyDict(v)
            elif isinstance(v, list):
                data[k] = tuple(v)
        self._data = data

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __copy__(self):
        return self._data.copy()

    def __deepcopy__(self, other):
        for k, v in list(self._data.items()):
            if isinstance(v, tuple):
                self._data[k] = list(v)
        return copy.deepcopy(self._data)

    def __repr__(self):
        return repr(self._data)


class exaBoxContext(object):

    def __init__(self, aOptions, aConfig, aPersistKv=None, aBasePath=None):

        # Initialize Context
        self.__options = aOptions
        self.__config  = ReadOnlyDict(aConfig)
        self.__config_orig  = aConfig
        self.__state   = ebCtxStateInitialized
        self.__dict    = {}
        self.__persist_kv = {}
        self.__sshkeys = {}
        self.__exakmsSingleton = None
        self.__starttime = time.time()
        self.__oedaversion = None
        self.__oedahost = None
        self.__exacloud_version = None
        self.__exachk_path = None
        self.__cps_sync = False
        self.__oeda_build_version = None

        # Compute base path
        if aBasePath is None:
            bp  = os.path.abspath(sys.argv[0])
            idx = bp.rfind('/exabox')
            if idx == -1:
                ebLogError('Could not build base path : {0}'.format(bp))
                sys.exit(-1)
            self.__basepath = bp[:idx+1]
        else:
            self.__basepath = aBasePath

        # Compute OEDA path
        config = self.__config
        if 'oeda_dir' in list(config.keys()):
            _dir = config['oeda_dir']
            if _dir[0] == '/':
                self.__oedapath = config['oeda_dir']
            else:
                self.__oedapath = self.__basepath +'/'+_dir
        else:
            self.__oedapath = None

        # Compute OEDA Build Branch
        self.__oeda_build_version = self.mComputeOEDALabel()

        # Compute Log path
        if self.__basepath[-1] == '/':
            self.__logpath = self.__basepath + 'log'
        else:
            self.__logpath = self.__basepath + '/log'

        _version_file = ""
        if self.__basepath[-1] == "/":
            _version_file = self.__basepath + "config/version.conf"
        else:
            _version_file = self.__basepath + "/config/version.conf"

        if os.path.isfile(_version_file) and os.access(_version_file, os.R_OK):
            with open(_version_file, "r") as _vf:
                _lines = _vf.readlines()
                self.__exacloud_version = _lines[0].split("=")[1].strip()

        # Compute Exachk path
        if self.__basepath[-1] == '/':
            self.__exachk_path = self.__basepath
        else:
            self.__exachk_path = self.__basepath + '/'

        # Restore persist kv
        if aPersistKv is not None:
            self.__persist_kv = aPersistKv

        for _k, _v in self.__persist_kv.items():
            self.mSetConfigOption(_k, _v, aAddPersist=False)


    def mGetExacloudVersion(self):
        return self.__exacloud_version

    def mGetExaKmsSingleton(self):
        return self.__exakmsSingleton

    def mSetExaKmsSingleton(self, aExaKmsSingleton):
        self.__exakmsSingleton = aExaKmsSingleton

    def mGetExaKms(self):
        return self.__exakmsSingleton.mGetExaKms()

    def mGetStartTime(self):
        return self.__starttime

    def mGetBasePath(self):
        return self.__basepath

    def mGetOEDAHostname(self):
        return self.__oedahost

    def mSetOEDAHostname(self,aHost):
        self.__oedahost = aHost

    def mGetOEDAPath(self):
        return self.__oedapath

    def mSetOEDAVersion(self,aVersion):
        self.__oedaversion = aVersion

    def mGetOEDAVersion(self):
        return self.__oedaversion

    def mGetLogPath(self):
        return self.__logpath

    def mGetVersion(self):
        return version_info[:3]

    def mGetOptions(self):
        return self.__options

    def mSetOption(self, aKey, aValue):
        self.__options[aKey] = aValue

    # Helpers to help access processed sys args
    def mSetArgsOptions(self, aOptions):
        self.__options['optArgs'] = aOptions

    def mGetArgsOptions(self):
        return self.__options['optArgs']

    # Options set via exabox.conf file
    def mGetConfigOptions(self):
        return self.__config

    def mSetConfigOptions(self, aConfig):
        self.__config = aConfig

        # Restore persist kv
        for _k, _v in self.__persist_kv.items():
            self.mSetConfigOption(_k, _v, aAddPersist=False)

    def mSetConfigOption(self, aOption, aValue, aAddPersist=True):
        _copy = dict(self.__config)
        _copy[aOption] = aValue
        self.__config = ReadOnlyDict(_copy)

        if aAddPersist:
            self.mSetPersistEntry(aOption, aValue)

    def mCheckConfigOption(self, aOption, aValue=None):
        """
        This function is really two in one. See below overall behavior according to parameters passed.
            1 - Check if parameter aOption is present in the exabox.conf and return it's value.
            2 - Test if parameter aOption is present in exabox.conf and compare it's value to one provided
        :param aOption: Option name
        :param aValue: Value to compare with the current Option name value
        :return:
            if aValue is specified (e.g not None) then return True if aValue == Option.value False otherwise
            return None if aValue is not provided and aOption name does not exist
            return cValue or current value if aValue is not provided and aOption name exist
        """

        if aValue is None:
            if aOption in list(self.__config.keys()):
                return self.__config[ aOption ]
            else:
                return None

        if aOption in list(self.__config.keys()):
            if self.__config[ aOption ] == aValue:
                return True
            else:
                return False
        else:
            return False
    #
    # TODO: Build a persistent/file registry (cleanup ?) to allow concurrent process access
    #
    def mSetRegEntry(self, aKey, aValue):
        self.__dict[aKey]=aValue

    def mGetRegEntry(self, aKey):
        return self.__dict[aKey]

    def mDelRegEntry(self,aKey):
        if aKey in list(self.__dict.keys()): del self.__dict[aKey]

    def mCheckRegEntry(self,aKey):
        return aKey in list(self.__dict.keys())

    def mDumpRegEntry(self):
        ebLogInfo('*** DUMP REGISTRY ***')
        for _key in list(self.__dict.keys()):
            ebLogInfo('*** REG: '+str(_key)+' - '+str(self.__dict[_key]))

    def mGetPersistKV(self):
        return self.__persist_kv

    def mSetPersistEntry(self, aKey, aValue):
        self.__persist_kv[aKey]=aValue

    def mGetPersistEntry(self, aKey):
        return self.__persist_kv[aKey]

    def mDelPersistEntry(self,aKey):
        if aKey in self.__persist_kv.keys(): del self.__persist_kv[aKey]

    def mCheckPersistEntry(self,aKey):
        return aKey in self.__persist_kv.keys()

    def mSetAllSSHKeys(self, aDict):
        self.__sshkeys = aDict

    def mGetAllSSHKeys(self):
        return self.__sshkeys

    def mSetExachkpath(self,aExachkPath):
        self.__exachk_path = aExachkPath

    def mGetExachkPath(self):
        return self.__exachk_path

    def mGetOEDALabel(self):
        return self.__oeda_build_version

    def mRefreshOEDALabel(self):
        self.__oeda_build_version = self.mComputeOEDALabel()

    def mComputeOEDALabel(self):
        """
        Method to get the OEDA label from OEDA es.properties file.
        The OEDA label can be fetched from the property BUILDBRANCH
        """

        _oeda_build = "UNKNOWN"
        _properties_file = os.path.join(self.__oedapath, "properties",
                "es.properties")

        if os.path.isfile(_properties_file):

            with open(_properties_file, "r") as _file:
                _properties = _file.read()

            _build_branch = re.search(r'BUILDBRANCH.*', _properties)
            if _build_branch:
                try:
                    _oeda_label = _build_branch.group().strip()
                    _oeda_build = _oeda_label.split("=")[-1]
                except:
                    ebLogWarn("Unable to get OEDA BUILDBRANCH")

        return _oeda_build

    def mGetPropagateProcOptions(self) -> List[str]:
        """
        Retuns a list of argument strings to propagate on process spawning
        Currently --debug, --verbose and --loglevel are supported.
        """
        _propagate_options = []
        # Adding option-cli arguments
        if self.__options["optArgs"].debug:
            _propagate_options.append("--debug")
        if self.__options["optArgs"].verbose:
            _propagate_options.append("--verbose")
        if self.__options["optArgs"].log_level:
            _log_level = self.__options["optArgs"].log_level
            _propagate_options.append("--loglevel")
            _propagate_options.append(_log_level)

        return _propagate_options

def set_gcontext(aContext):
    global GlobalContext
    GlobalContext = aContext

def get_gcontext():
    return GlobalContext


