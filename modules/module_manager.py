"""

 $Header:

 Copyright (c) 2018, 2024, Oracle and/or its affiliates.

 NAME:
    Manager.py - Base Class for Module Manager

 DESCRIPTION:
    Use this class when you need to read the content of the modules of exacloud

 NOTES:
    None

 History:

    MODIFIED   (MM/DD/YY)
    ririgoye    06/18/24 - Bug 36746656 - PYTHON 3.11 - EXACLOUD NEEDS TO
                           UPDATE DEPRECATED/OLDER IMPORTS DYNAMICALLY
    jejegonz    12/21/20 - 32047521 - Delete gLogMgrConsole import, don't used
                           anymore.
    jesandov    12/02/19 - Creation of the file
"""

# pylint: disable=import-error

from __future__ import print_function

import json
import os
import sys
import time
import uuid
import subprocess
from subprocess import PIPE

try:
    from collections import namedtuple, OrderedDict
except ImportError:
    from collections.abc import namedtuple, OrderedDict

from jsonschema import validate as validate_schema

from exabox.core.Node import exaBoxNode
from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogInit, ebLogInfo
from exabox.core.Context import get_gcontext
from exabox.tools.ebGraph.ebGraph import ebGraph, ebGraphNode, ebGraphLink

DEVNULL = open(os.devnull, 'wb')

class ebJsonObject(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

class ModuleManager(object):

    @staticmethod
    def mReadJson(aPath):

        def mCheckDuplicated(aJson):
            _newDict = {}

            for _key, _value in aJson:
                if _key in _newDict.keys():
                    raise ValueError("Duplicated key: {0}".format(_key))
                else:
                    _newDict[_key] = _value
            return ebJsonObject(_newDict)

        with open(aPath) as _file:
            _data = _file.read()
            _dictobj = json.loads(_data, object_pairs_hook=mCheckDuplicated)
            return ebJsonObject(_dictobj)

    def __init__(self, aCluboxObj, aStagePath=None):

        self.__stage_path = aStagePath
        if not self.__stage_path:
            self.__stage_path = 'modules/'

        self.__stage_path = os.path.abspath(self.__stage_path)
        self.__internal_path = os.path.abspath('exabox/modules/')

        self.__schema = ModuleManager.mReadJson(self.__internal_path + '/module_schema.json')
        self.__cache = {}
        self.__clubox = aCluboxObj

        self.__undo = False

    def mExecuteLocal(self, aCmd, aCurrDir=None, aStdIn=PIPE, aStdOut=PIPE, aStdErr=PIPE):
        _current_dir = aCurrDir
        _stdin = aStdIn
        _std_out = aStdOut
        _stderr = aStdErr

        _node = exaBoxNode(get_gcontext(), aLocal=True)
        _node.mConnect()
        _i, _o, _e = _node.mExecuteCmd(aCmd, aCurrDir=_current_dir, aStdIn=_stdin, aStdOut=_std_out, aStdErr=_stderr)
        _rc = _node.mGetCmdExitStatus()
        _node.mDisconnect()
        return _rc, _i, _o, _e

    def mGetCache(self):
        return self.__cache

    def mGetSchema(self):
        return self.__schema

    def mGetStagePath(self):
        return self.__stage_path

    def mSetStagePath(self, aStagePath):
        self.__stage_path = aStagePath

    def mGetUndo(self):
        return self.__undo

    def mSetUndo(self, aUndo):
        self.__undo = aUndo

    def mLoadModule(self, aModuleName):
        muuid = str(uuid.uuid1())
        old_path = os.path.abspath(os.getcwd())

        try:
            # Extract only module.json on uniq folder
            os.chdir(self.__stage_path)
            self.mExecuteLocal("/bin/mkdir {0}".format(muuid))
            cmd = "/bin/tar xvf {0} -C {1}/ module.json".format(aModuleName, muuid)
            self.mExecuteLocal(cmd, aStdOut=DEVNULL, aStdErr=DEVNULL)

            # Read the information of the module.json
            module_json = ModuleManager.mReadJson("{0}/module.json".format(muuid))

            # Cleanup
            self.mExecuteLocal("/bin/rm -rf {0}".format(muuid))
            os.chdir(old_path)

            # Validation of the module
            validate_schema(instance=module_json, schema=self.__schema)
            return module_json

        except Exception as e:
            ebLogInfo(e)
            os.chdir(old_path)
            return None


    def mTriggerStep(self, aStep):
        ebLogInfo("Execute Trigger for aStep: {0}".format(aStep))
        pass

    def mListModules(self):
        modules = os.listdir(self.__stage_path)
        modules = list(filter(lambda x: x.endswith(".tar"), modules))
        return modules

    def mBuildCache(self):

        self.__cache = {}

        for module in self.mListModules():
            content = self.mLoadModule(module)
            if content:
                self.__cache[module] = content

    def mPrintDependencyGraph(self):
        self.__dependency.mPrint(aPrintfx=ebLogInfo)

    def mGetInstallationOrder(self):
        visit_order = self.__dependency.mVisitAll()
        return visit_order

    def mBuildDependencyGraph(self):

        def mDependencyParent(aGraphNodeElement, aReq):

            if aGraphNodeElement.version >= aReq.min_version and \
               aGraphNodeElement.name == aReq.module_name:
                    return True
            return False

        self.__dependency = ebGraph()

        # Add all elements to the graph
        for cache_key, cache_node in self.__cache.items():
            self.__dependency.mAddElement(cache_node)

        # Create the links
        for graph_node in self.__dependency.mGetNodes():

            cache_node = graph_node.mGetElement()

            if "requires" in cache_node.keys():

                # Fetch the nodes that have the dependency
                for req in cache_node.requires:

                    link_node = self.__dependency.mFindElement(req, mDependencyParent)

                    # Add faker dependency of env type
                    if link_node is None:
                        faker_dep = ebJsonObject({"name": req.module_name, \
                                                  "version": req.min_version, \
                                                  "module_type": "env_rpm"})
                        link_node = self.__dependency.mAddElement(faker_dep)

                    self.__dependency.mAddLink(link_node, graph_node)


