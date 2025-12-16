#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/tools/ebXmlGen/ebJsonCallbackGenerator.py /main/6 2024/10/17 09:54:47 jesandov Exp $
#
# ebJsonCallbackGenerator.py
#
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
#
#    NAME
#      ebJsonCallbackGenerator.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      JSON Callback Generator
#
#    NOTES
#      Confluence: https://confluence.oraclecorp.com/confluence/x/D_xSq
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    06/18/24 - Bug 36746656 - PYTHON 3.11 - EXACLOUD NEEDS TO
#                           UPDATE DEPRECATED/OLDER IMPORTS DYNAMICALLY
#    jesandov    11/18/20 - Creation
#

import os
import re
import json
import copy
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn

class ebJsonCallbackGenerator:

    def __init__(self, aUUID, aOptions, aSaveDir="log/xmlgen"):
        """
        Constructor

        :param:aUUID: Uuid of the operation
        :param:aOptions: Jsonconf passed of the ECRA Payload
        :param:aSaveDir: Directory where to record the callback_name of every step
        """

        # Output variable
        self.__uuid = aUUID
        self.__callbackInfo = []
        self.__saveDir = aSaveDir

        # Read configuration file of default values
        _dv = {}
        with open("exabox/tools/ebXmlGen/default_values.json") as _dvf:
            _dv = json.load(_dvf)

        # Every subtag is a private attribute
        self.__pureCallbacks = _dv['callbacks']
        self.__structure = _dv['structure']
        self.__payload = aOptions
        self.__envType = "undefined"

        if "clusterless" in self.__payload and str(self.__payload["clusterless"]).lower() == "true":
            self.mSetPreprocesor(_dv['preprocessor_clusterless'])
        else:
            self.mSetPreprocesor(_dv['preprocessor'])

    #######################
    # GETTERS AND SETTERS #
    #######################

    def mGetUUID(self):
        return self.__uuid

    def mSetUUID(self, aValue):
        self.__uuid = aValue

    def mGetCallbackInfo(self):
        return self.__callbackInfo

    def mSetCallbackInfo(self, aValue):
        self.__callbackInfo = aValue

    def mGetPureCallbacks(self):
        return self.__pureCallbacks

    def mSetPureCallbacks(self, aValue):
        self.__pureCallbacks = aValue

    def mGetStructure(self):
        return self.__structure

    def mSetStructure(self, aValue):
        self.__structure = aValue

    def mGetPayload(self):
        return self.__payload

    def mSetPayload(self, aValue):
        self.__payload = aValue

    def mGetPreprocesor(self):
        return self.__preprocesor

    def mSetPreprocesor(self, aValue):
        self.__preprocesor = aValue

    def mGetEnvType(self):
        return self.__envType

    def mSetEnvType(self, aTypeEnv):
        self.__envType = aTypeEnv

    def mGetSaveDir(self):
        return self.__saveDir

    def mSetSaveDir(self, aValue):
        self.__saveDir = aValue

    #################
    # Class Methods #
    #################

    def mInitCallbackInfo(self):
        self.mSetCallbackInfo([])

    def mExecute(self):
        """
        Entry point of ebJsonCallbackGenerator

        This method calls one subset of substeps to generate the callback-generator.json
        """

        self.mInitCallbackInfo()

        # Process Preprocesor
        _path = []
        _pathNodes = []
        _currentNode = self.mGetPayload()
        self.mProcessPreprocesor(_path, _pathNodes, _currentNode)

        # Initial Entry point
        os.makedirs(self.mGetSaveDir(), exist_ok=True)
        with open("{0}/{1}_p1-0-DeepUpdate.json".format(self.mGetSaveDir(), self.mGetUUID()), "w") as _f:
            _f.write(json.dumps(self.mGetPayload(), indent=4, sort_keys=True))

        # Process All Callbacks
        _path = []
        _pathNodes = []
        _currentNode = self.mGetPayload()

        self.mProcessPayload(_path, _pathNodes, _currentNode)
        self.mSaveCallbackInfo("p1-1-CreatePayload")

        # Process XML Relations
        self.mProcessRelationsXML()
        self.mSaveCallbackInfo("p1-2-ProcessRelations")

    def mSaveCallbackInfo(self, aTag):
        """
        Save the current step of the callbackinfo.json

        :param:aTag:sufix of filename of the callbackinfo.json
        """

        os.makedirs(self.mGetSaveDir(), exist_ok=True)

        with open("{0}/{1}_{2}_callbackinfo.json".format(self.mGetSaveDir(), self.mGetUUID(), aTag), "w") as _f:
            _f.write(json.dumps(self.mGetCallbackInfo(), indent=4, sort_keys=True))

    def mFindCallbacks(self, aPath):
        """
        Find the callbacks in the structure givin a certein path

        :param:aPath: path inside the structure
        :return: list of string with the callbacks names found in the structure
        """

        _callbacks = []
        _curr = self.mGetStructure()
        _remains = copy.deepcopy(aPath)

        while _remains:

            _step = _remains.pop(0)

            if _step not in _curr:
                _callbacks = []
                _curr = None
                break

            _curr = _curr[_step]

        if _curr and "callbacks" in _curr:
            _callbacks = _curr["callbacks"]

        return _callbacks


    def mReplaceValue(self, aValue, aCurrentNode, aPathNodes):
        """
        Replace the 'aValue' with the information of the aCurrentNodes

        Lets review the followin example:

            aValue = "<parent/name>_id"
            aCurrentNode = {"name": "3"}
            aPathNode = [{"name": "1"}, {"name": "2"}]

        will return:

            return "2_id"

        Starting with find the <> and fetch the content of the string start
        will replace the value with the aCurrentNode or will change with 
        aPathNode path.


        :aValue: string to change
        :aCurrentNode: Current information of the callback info
        :aPathNode: Get the history nodes from the start to the current node
        :return: formatted aValue with the replace
        """

        _selfTag = ""
        _value = aValue

        # Remove all logic before the token ":"
        if re.match(".*:.*", aValue):
            _withSelf = aValue.split(":") 
            _value = _withSelf.pop()
            _selfTag = "{0}:".format(":".join(_withSelf))

        _match = re.search("\<(.*?)\>", _value)

        while _match:

            _current = aCurrentNode
            _pathNode = copy.deepcopy(aPathNodes)
            _replaceValue = ""

            # Iterate to find the path
            _fetchedPath = _match.group(1).split("/")

            for _route in _fetchedPath:

                _replaceValue = ""

                if _route == "parent":
                    _current = _pathNode.pop()
                    continue

                elif _route == "root":
                    _current = _pathNode[0]
                    _pathNode = []
                    continue

                # Fetch the subtag
                if _route in _current:

                    _pathNode.append(_current)
                    _current = _current[_route]

                    if isinstance(_current, str):
                        _replaceValue = _current

                else:

                    for _subkey in _current:

                        if re.match(_route, _subkey):

                            _pathNode.append(_current)
                            _current = _current[_subkey]

                            if isinstance(_current, str):
                                _replaceValue = _current

                            break

            # Update value and math
            _value = "{0}{1}{2}".format(
                    _value[:_match.start()], \
                    _replaceValue, \
                    _value[_match.end():] \
            )

            _match = re.search("\<(.*?)\>", _value)

        # Replace cases when there are extra default values
        # taking the example "<master>|eth0" with empty master -> "|eth0"
        # The returning value needs to be "eth0"
        _finalValue = _value
        _valueSplit = _value.split("|")
        for _split in _valueSplit:
            if _split:
                _finalValue = _split
                break

        return "{0}{1}".format(_selfTag, _finalValue)


    def mExecuteCallback(self, aCallbackHandler, aCurrentNode, aPathNodes):
        """
        Execute one callback info given one aCallbackHandler givin one aCurrentNode
        the execition will add one new entry to the callbackInfo final json

        Giving one aCallbackHandler that could be am array or one string will
        find the pure callback that is behind the "callbacks" tag in the default_values.json

        After find the pure callback, will do the replace of every value in the pure callback
        depends of the environment and the type of callbacks

        There are three types of callbaks:
            * XML Callbacks: This callbacks will replace values in the Vanilla XML
            * Relation Callbacks: This callbacks create relations between XML Callbacks
            * Code Callback: Additional callbacks that execute code checks and cleanups

        :param:aCallbackHandler: str or dict with the name of the callbacks
        :param:aCurrentNode: Current callbackinfo where to replace values
        :param:aPathNods: history of the nodes from the beginning to the current node
        """

        # In case of range callback execute the callback by range
        if isinstance(aCallbackHandler, dict):

            _cb = aCallbackHandler["cb"]
            _range = aCallbackHandler["range"].split(",")

            for i in range(int(_range[0]), int(_range[1])):
                _curr = copy.deepcopy(aCurrentNode)

                if "extra" in aCallbackHandler:
                    _curr.update(aCallbackHandler['extra'])

                _curr['idx'] = str(i)
                _curr['idx1'] = str(i+1)
                self.mExecuteCallback(_cb, _curr, aPathNodes)

            return

        # Check if the callback exist
        if aCallbackHandler not in self.mGetPureCallbacks():
            _msg = "invalid callback: {0}".format(aCallbackHandler)
            raise ValueError(_msg)

        _callback = copy.deepcopy(self.mGetPureCallbacks()[aCallbackHandler])

        _values = {}

        # If the callback is an Code Change
        if _callback['type'] == "code_callback":
            self.mExecuteCodeCallback(_callback, aCurrentNode)
            return 

        # If the callback is a XML Change
        elif _callback["type"] == "xml_callback":

            # Get the default values 
            _defaultValues = _callback.pop('default_values')
            _values = _defaultValues.pop("all")

            # Apply patch of values for enviroment type
            if self.mGetEnvType() in _defaultValues:
                _values.update(_defaultValues.pop(self.mGetEnvType()))

        # If the callback is an relation change
        elif _callback["type"] == "relation_callback":
            _values = _callback.pop("relation")

        # Do the replace of every value in the callback
        for _key, _value in copy.deepcopy(_values).items():

            _newValue = None

            # In case of list, do the replace of every subelement

            if isinstance(_value, list):

                _newValue = []

                for _element in _value:
                    _nv = self.mReplaceValue(_element, aCurrentNode, aPathNodes)
                    _newValue.append(_nv)

            else:
                _newValue = self.mReplaceValue(_value, aCurrentNode, aPathNodes)

            # Store the new value
            _values[_key] = _newValue

        _callback['values'] = _values


        # Save the result callback
        _callback['name'] = aCallbackHandler

        self.mGetCallbackInfo().append(_callback)


    def mExecuteCodeCallback(self, aCallback, aCurrentNode):
        """
        Execute code callbacks

        :param:aCallback: Callbackinfo with the information to parse
        :param::aCurrentNode: Node with the information to change
        """

        if aCallback['name'] == "detect_domain":

            if "fqdn" in aCurrentNode:

                _fqdn = aCurrentNode['fqdn'].split(".")
                aCurrentNode['host'] = _fqdn.pop(0)
                aCurrentNode['domain'] = ".".join(_fqdn)

        elif aCallback['name'] == "change_env":

            if "ostype" in aCurrentNode:

                ostype = aCurrentNode['ostype']

                if ostype in ["xen", "ib", "xen/ib", "ib/xen"]:
                    self.mSetEnvType("xen")
                elif ostype in ["kvm", "roce"]:
                    self.mSetEnvType("kvm")

    def mProcessPreprocesor(self, aPath, aPathNodes, aCurrentNode):
        """
        Start the parse of the ECRA Payload doing BFS tree iteration
        After detect preprocesor node will update the missing arguments

        :param:aPath: Str Path from the given json node
        :param:aPathNodes: Node path from the given json node
        :param:aCurrentNode: Node in the current position
        """

        if isinstance(aCurrentNode, dict):

            # Iterate
            for _key, _value in aCurrentNode.items():

                _path = aPath + [_key]
                _pathNodes = aPathNodes + [aCurrentNode]
                _currentNode = _value

                self.mProcessPreprocesor(_path, _pathNodes, _currentNode)

            # Add missing tags from preprocesor
            _preprocessorTag = self.mGetPreprocesor()

            for _route in aPath:
                if _preprocessorTag:

                    if _route in _preprocessorTag:
                        _preprocessorTag = _preprocessorTag[_route]
                    else:
                        _preprocessorTag = None

            # Do the update of the current node
            if _preprocessorTag:
                for _key, _value in _preprocessorTag.items():
                    if _key not in aCurrentNode:
                        aCurrentNode[_key] = _value

        elif isinstance(aCurrentNode, list):
            for _value in aCurrentNode:
                _currentNode = _value
                self.mProcessPreprocesor(aPath, aPathNodes, _currentNode)

    def mProcessPayload(self, aPath, aPathNodes, aCurrentNode):
        """
        Start the parse of the ECRA Payload doing BFS tree iteration

        After detect callbacks in that given position in the Structure
        will execute in order to generate the callback info structure

        :param:aPath: Str Path from the given json node
        :param:aPathNodes: Node path from the given json node
        :param:aCurrentNode: Node in the current position
        """

        if isinstance(aCurrentNode, dict):

            _callbacks = self.mFindCallbacks(aPath)
            for _callback in _callbacks:
                self.mExecuteCallback(_callback, aCurrentNode, aPathNodes)

            for _key, _value in aCurrentNode.items():

                _path = aPath + [_key]
                _pathNodes = aPathNodes + [aCurrentNode]
                _currentNode = _value

                self.mProcessPayload(_path, _pathNodes, _currentNode)

        elif isinstance(aCurrentNode, list):

            _idx = 0
            for _value in aCurrentNode:
                _currentNode = _value

                if isinstance(_currentNode, dict):
                    _currentNode['idx'] = str(_idx)
                    _currentNode['idx1'] = str(_idx+1)

                self.mProcessPayload(aPath, aPathNodes, _currentNode)
                _idx += 1

    def mFetchCallbackInfo(self, aRelValues):
        """
        Fetch XML Callback assosiate with one Relation Callback

        :param:aRelValues:Relation callback where to find the XML Callback
        :return: XML Callback found or None
        """

        for _callback in self.mGetCallbackInfo():

            if _callback['type'] == "xml_callback":

                try:
                    _cond1 = _callback['values']['id'] == aRelValues['callback_id']
                    _cond2 = _callback['xml_callback'] == aRelValues['callback_name']
                    _cond3 = _callback['name']  == aRelValues['callback_name']

                except Exception as e:
                    #import pdb; pdb.set_trace()
                    raise

                if _cond1 and (_cond2 or _cond3):
                    return _callback

        return None


    def mProcessRelationsXML(self):
        """
        Process Relation XML

        The final callback_info.json will not contain any Relation Callback
        The relation callback will insert information to the corresponding XML Callback
        """

        # Process the relation callbacks
        _callbacks = copy.deepcopy(self.mGetCallbackInfo())

        for _relCallback in _callbacks:

            if _relCallback['type'] == "relation_callback":

                _xmlCallback = self.mFetchCallbackInfo(_relCallback["values"])

                if _xmlCallback:
                    _key = _relCallback['values']['insert_key']
                    _value = _relCallback['values']['insert_values']

                    if isinstance(_value, list):
                        _xmlCallback['values'][_key] = _xmlCallback['values'][_key] + _value
                    else:
                        _xmlCallback['values'][_key] = _value

                else:
                    #import pdb; pdb.set_trace()
                    ebLogWarn("Invalid aRelCallback: {0}".format(_relCallback))

                self.mGetCallbackInfo().remove(_relCallback)

        # Process the self callbacks
        for _callback in self.mGetCallbackInfo():

            for _key, _value in _callback['values'].items():

                if isinstance(_value, list):

                    _newValues = []
                    for _element in _value:

                        if _element.startswith("self:"):

                            _rel = {"callback_id": _element.split(":")[2],
                                    "callback_name": _element.split(":")[1]}

                            _xmlCallback = self.mFetchCallbackInfo(_rel)

                            if _xmlCallback:
                                _newValues.append(_xmlCallback['values'])
                                _xmlCallback['xml_callback'] = "deleted"

                        else:
                            _newValues.append(_element)

                    _callback['values'][_key] = _newValues


# end of file
