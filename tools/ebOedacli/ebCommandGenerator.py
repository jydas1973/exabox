"""
$Header: 

 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    ebCommandGenerator - Basic functionality

FUNCTION:
    This class takes the OEDA XML, EXACLOUD XML, PATCH XML and the EXATEMPLATE,
    the class is goint to call ebTree and generate the Tricolor Tree between the EXACLOUD XML and PATCH XML,
    the red nodes are nodes deleted from EXACLOUD XML and the green nodes area nodes new found on PATCH XML
    when a Red/Green node of the Tricolor Tree match with the Exatemplate and does have a 'cmdfx' tag is going to run the callback  callbacks otherwise, apply Manual Patching to the OEDA XML
    'examigrate' is a callback to migrate the OEDA xml to Exacloud XML, for example, on the VmSizes requirements


NOTE:
   Project Documentation: https://confluence.oraclecorp.com/confluence/pages/viewpage.action?pageId=1063643852

History:

    MODIFIED   (MM/DD/YY)
       aararora 10/31/25 - Bug 38595677: Get base path of exacloud independent
                           of sys.path
       aararora 05/10/22 - Bug 34004578: Bandit issue fix
        ndesanto    12/02/2020 - Fixing missing append
        jesandov    16/04/2020 - Bug31187942: Add sort of ALTER DATABASEHOME by DBVERSION subtag
        jesandov    17/12/2018 - File Creation

"""

import os
import sys
import uuid
from exabox.tools.ebTree.ebTree import ebTree
from exabox.core.Error import ExacloudRuntimeError
from exabox.tools.ebTree.ebTreeNode import ebTreeNode

class ebPatchStructure(object):

    def __init__(self, aType="", aNode=None, aReferenceNode=None):
        self.__type = aType
        self.__node = aNode
        self.__referenceNode = aReferenceNode
        self.__includeText = True

    def mGetType(self):
        return self.__type

    def mSetType(self, aStr):
        self.__type = aStr

    def mGetNode(self):
        return self.__node

    def mSetNode(self, aEbTreeNode):
        self.__node = aEbTreeNode

    def mGetReferenceNode(self):
        return self.__referenceNode

    def mSetReferenceNode(self, aEbTreeNode):
        self.__referenceNode = aEbTreeNode

    def mGetIncludeText(self):
        return self.__includeText

    def mSetIncludeText(self, aValue):
        self.__includeText = aValue

class ebCommandGenerator(object):

    def __init__(self, aExacloudFile, aPatchFile, aOedaFile, aOedacliObj):

        self.__exacloudFile = aExacloudFile
        self.__exacloudTree = ebTree(self.__exacloudFile)

        self.__patchFile    = aPatchFile
        self.__patchTree    = ebTree(self.__patchFile)

        self.__oedaFile     = aOedaFile
        self.__oedaTree     = ebTree(self.__oedaFile)

        self.__oedaFinalTree = None

        self.__deleteNodes     = []
        self.__appendNodes     = []
        self.__patchStructures = []

        self.__oedacli      = aOedacliObj

        self.__tricolorTree  = self.__exacloudTree.mTricolorTree(self.__patchTree)

        _current_script_dir = os.path.dirname(os.path.abspath(__file__))
        _template_path = os.path.join(_current_script_dir, "exatemplateV1.tpl")
        self.__template     = ebTree(_template_path)
        self.__commandList  = []
        self.__extraCommands = []
        self.__preExtraCommands = []

        self.__callbackShareData = {}

        self.__bannedCmds = [
            "DELETE MACHINE"
        ]

    def mGetOedaOriginalTree(self):
        return self.__oedaTree

    def mGetOedaFinalTree(self):
        return self.__oedaFinalTree

    def mGetPreExtraCommands(self):
        return self.__extraPreCommands

    def mSetPreExtraCommands(self, aCommands):
        self.__extraPreCommands = aCommands

    def mGetExtraCommands(self):
        return self.__extraCommands

    def mSetExtraCommands(self, aCommands):
        self.__extraCommands = aCommands

    def mPatchOriginalOeda(self):
        _oedaTmpLocation1 = "{0}/{1}.xml".format(self.__oedacli.mGetLogDir(), uuid.uuid1())
        _oedaTmpLocation2 = "{0}/{1}.xml".format(self.__oedacli.mGetLogDir(), uuid.uuid1())

        # Save tricolor tree
        _tricolorFile = os.path.join(self.__oedacli.mGetLogDir(), "tricolor.xml")
        self.__tricolorTree.mExportXml(_tricolorFile, aExportType=True)

        #Generate the commands
        _oedacliCommands = self.mGenerateCommands()

        #Apply Manual Pre-Patching to nodes
        self.__oedacli.mLog("Info", "Calculate differences", aFilename="ebCommandGenerator")
        _preNodes = [x for x in self.__patchStructures if x.mGetType() == "pre"]
        _posNodes = [x for x in self.__patchStructures if x.mGetType() == "post"]

        _preNodes.sort(key=lambda x: x.mGetNode().mGetType(), reverse=True)
        _posNodes.sort(key=lambda x: x.mGetNode().mGetType(), reverse=True)

        self.__oedaTree.mExportXml(_oedaTmpLocation1)

        #Apply Commands
        self.__oedacli.mLog("Info", "Apply OEDACLI Commands", aFilename="ebCommandGenerator")

        # Extra commands for new XML patching
        if self.mGetPreExtraCommands():
            for _command in self.mGetPreExtraCommands():
                self.__oedacli.mAppendCommand(_command[0], _command[1], _command[2])

        for _command in _oedacliCommands:

            # Validate Where
            if _command[0].startswith("ALTER") or _command[0].startswith("DELETE"):
                if not _command[2]:
                    continue

            # Validate Args
            if _command[0].startswith("ALTER") or _command[0].startswith("ADD"):
                if not _command[1]:
                    continue

            self.__oedacli.mAppendCommand(_command[0], _command[1], _command[2])

        # Extra commands for new XML patching
        if self.mGetExtraCommands():
            for _command in self.mGetExtraCommands():
                self.__oedacli.mAppendCommand(_command[0], _command[1], _command[2])

        if len(_oedacliCommands) != 0:
            self.__oedacli.mRun(_oedaTmpLocation1, _oedaTmpLocation2)
            self.__oedaFinalTree = ebTree(_oedaTmpLocation2)
            if os.path.exists(_oedaTmpLocation1):
                os.remove(_oedaTmpLocation1)
            if os.path.exists(_oedaTmpLocation2):
                os.remove(_oedaTmpLocation2)
        else:
            self.__oedaFinalTree = self.__oedaTree.mCopy()
            if os.path.exists(_oedaTmpLocation1):
                os.remove(_oedaTmpLocation1)

        #Apply Manual Post-Patching to nodes
        self.__oedacli.mLog("Info", "Do Post-Patching", aFilename="ebCommandGenerator")

        for _pendingNodes in _preNodes:

            self.mManualPatching(
                _pendingNodes.mGetNode(), 
                _pendingNodes.mGetReferenceNode(), 
                self.__oedaFinalTree, 
                aIncludeText=_pendingNodes.mGetIncludeText()
            )

        for _pendingNodes in _posNodes:

            self.mManualPatching(
                _pendingNodes.mGetNode(), 
                _pendingNodes.mGetReferenceNode(), 
                self.__oedaFinalTree, 
                aIncludeText=_pendingNodes.mGetIncludeText()
            )


    def mCompareName(self, aNextNode, aPathNode):
        return aNextNode.mGetElement()['tag'] == aPathNode.mGetElement()['tag']

    def mGenerateCommands(self):

        _notcmdfx   = []
        _templateCp = self.__template.mCopy()

        self.__commandList  = []
        self.__deleteNodes  = []
        self.__appendNodes  = []
        self.__patchStructures = []

        def mStuff(aTricolorNode, aArgsList):

            if aTricolorNode.mGetType() != "White":

                #Search the tricolor node in template
                _nodeFound = self.__template.mSearchByPath(aTricolorNode.mGetPathNode(), aCompareCallback=self.mCompareName)
                if _nodeFound is not None:

                    #Find the callback on the node and parents
                    _iterationNode = _nodeFound
                    _callbackFound = False

                    while _iterationNode is not None and not _callbackFound:

                        if "cmdfx" in list(_iterationNode.mGetElement().keys()):
                            self.mCallbackHadle(_iterationNode.mGetElement()['cmdfx'], aTricolorNode)
                            _callbackFound = True

                        _iterationNode = _iterationNode.mGetParent()

                    if not _callbackFound:

                        #Apply Manual Patching
                        self.mColorpatchingCallback(aTricolorNode)

                        _path = "/".join(aTricolorNode.mGetPath())
                        if _path not in _notcmdfx:
                            _notcmdfx.append(_path)

                else:

                    #Append node structure to the exatemplate to preservate consistency on template
                    _parent = aTricolorNode.mGetParent()
                    _nodeFound = _templateCp.mSearchByPath(aTricolorNode.mGetPathNode(), aCompareCallback=self.mCompareName)

                    if _nodeFound is None:
                        _nodeFound = _templateCp.mSearchByPath(_parent.mGetPathNode(), aCompareCallback=self.mCompareName)
                        _node = ebTreeNode()
                        _node.mSetElement({"tag": aTricolorNode.mGetElement()["tag"]})
                        _nodeFound.mAppendChild(_node)

        #Fetch Tree and callbacks and generate the commands
        self.__tricolorTree.mBFS(aStuffCallback=mStuff)
        self.mEndCallbackHadle()

        _newTagsTree = self.__template.mTricolorTree(_templateCp)

        #Show new template with tags not found
        if _newTagsTree.mGetNodesByType("Red") != [] or _newTagsTree.mGetNodesByType("Green"):

            _current_script_dir = os.path.dirname(os.path.abspath(__file__))
            _pathTree = os.path.join(_current_script_dir, "exatemplateV1.tpl.2")
            _newTagsTree.mSortTree()
            _newTagsTree.mExportXml(_pathTree)

            self.__oedacli.mLog("Info", "There is tags not declared on template while are on Patch Exacloud", aFilename="ebCommandGenerator")
            self.__oedacli.mLog("Info", "Generate new template file on: {0}".format(_pathTree), aFilename="ebCommandGenerator")

        #Showt the tags that apply manual patching
        if _notcmdfx:
            _notcmdfx.sort()
            self.__oedacli.mLog("Warn", "List cmdfx not implemented, do Manual Patching:", aFilename="ebCommandGenerator")

            for _tag in _notcmdfx:
                self.__oedacli.mLog("Warn", _tag, aFilename="ebCommandGenerator")

        self.mSortCommands()
        
        self.__oedacli.mLog("Info", "Generated commands", aFilename="ebCommandGenerator")
        self.__oedacli.mLog("Info", "\n".join([str(x) for x in self.__commandList]), aFilename="ebCommandGenerator")

        return self.__commandList

    def mSortCommands(self):
        """
        Sort the command to execute in oedacli by importance of execution
        """

        def mSorter(aElement):
            """
            Decide the sort value by the type of command that recive

            :param aElement: a list element with three object
            :param aElement[0]: the global name of the command
            :param aElement[1]: the data that would change by the command
            :param aElement[2]: the location of where the command will be affected
            :type aElement: list
            :type aElement[0]: str
            :type aElement[1]: dict or None
            :type aElement[1]: dict or None

            :return: return the value of the command to apply a sort
            :rtype: int
            """

            if aElement[0] == "DELETE DISKGROUP":
                return 0
            elif aElement[0] == "DELETE DATABASE":
                return 1
            elif aElement[0] == "DELETE DATABASEHOME":
                return 2
            elif aElement[0] == "ALTER MACHINE":
                return 2
            elif aElement[0] == "ALTER NETWORK":
                return 3
            elif aElement[0] == "ALTER CLUSTER":
                return 4
            elif aElement[0] == "ALTER VIP":
                return 5
            elif aElement[0] == "ALTER SCAN":
                return 6

            elif aElement[0] == "ALTER DATABASEHOME":

                # The default value of this operation will be 7
                _value = 7

                # In case that the value will have the dbversion will be parse as:
                # 10.<dbversion>, e.g. 7.(10000-1900) = 7.810
                try:
                    if aElement[1] and "DBVERSION" in aElement[1].keys():
                        _dbver = int(aElement[1]['DBVERSION'].replace(".", "")[0:4])
                        _diffv = str(10000 - _dbver)
                        _value = float("{0}.{1}".format(_value, _diffv.zfill(6))) # desc order
                except Exception as e:
                    self.__oedacli.mLog("Warn", "Could not parse DBVERSION", aFilename="ebCommandGenerator")
                    self.__oedacli.mLog("Warn", str(e), aFilename="ebCommandGenerator")

                return _value

            elif aElement[0] == "ADD DATABASEHOME":
                return 8
            elif aElement[0] == "ADD DATABASE":
                return 9
            elif aElement[0] == "ALTER DATABASE":
                return 10
            else:
                return 1000

        self.__commandList.sort(key=mSorter)

    def mManualPatching(self, aAppendNode, aFindNode=None, aTree=None, aIncludeText=True):

        def mComparePatch(aNextNode, aPathNode):
            _n = aNextNode.mGetElement()
            _p = aPathNode.mGetElement()

            if not _n or not _p:
                return False

            _res = True
            _res = _res and (_n["tag"]  == _p["tag"])

            if 'id' in list(_n.keys()) and 'id' in list(_n.keys()):
                _res = _res and (_n["id"] == _p["id"])

            if aIncludeText:
                if 'text' in list(_n.keys()) and 'text' in list(_n.keys()):
                    _res = _res and (_n["text"] == _p["text"])

            return _res

        def mAppendDelete(aNode, aArgs):
            self.__deleteNodes.append(aNode)

        #Restore ids from the "original" node
        if aFindNode is not None:
            for child in aFindNode.mGetChildren():
                if child.mGetSortElement() == "original":
                    aFindNode.mGetElement()['id'] = child.mGetElement()['text']
                    break

        #Find the node to apply the command
        _findNode = aFindNode
        if _findNode is None:
            _findNode = aAppendNode.mGetParent()

        _treeToPatch = aTree
        if _treeToPatch is None:
            _treeToPatch = self.__oedaFinalTree

        _nodeFound = _treeToPatch.mSearchByPath(_findNode.mGetPathNode(), aCompareCallback=mComparePatch)
        _nodeSelf  = _treeToPatch.mSearchByPath(aAppendNode.mGetPathNode(), aCompareCallback=mComparePatch)

        if aAppendNode.mGetType() == "Green":

            if _nodeSelf is not None:

                if not aIncludeText:
                    _nodeSelf.mSetElement(aAppendNode.mGetElement())

                #Check if the node is on the new nodes
                if _nodeSelf not in self.__appendNodes:
                    self.__oedacli.mLog("Warn", "Node Green already in XML", aFilename="ebCommandGenerator")
                    self.__oedacli.mLog("Warn", self.__tricolorTree.mStrNodesPath([aAppendNode]), aFilename="ebCommandGenerator")
            else:

                #Append node to the Tree
                if _nodeFound is not None:
                    _cp = aAppendNode.mCopy()

                    #Delete posible nodes with same parent than himself
                    _foundRelate = False
                    _childs = _nodeFound.mGetChildren()
                    for _childNode in _childs:
                        if _childNode.mGetSortElement() ==  _cp.mGetSortElement():

                            relateFlag = True
                            if "id" in _childNode.mGetElement() and \
                               "id" in _cp.mGetElement():
                                relateFlag = False
                                if _childNode.mGetElement()["id"] == _cp.mGetElement()["id"]:
                                    relateFlag = True

                            if relateFlag:

                                self.__oedacli.mLog("Warn", "Delete Node {0} Relate to {1}".format(_childNode, _cp), aFilename="ebCommandGenerator")
                                _foundRelate = True
                                _childNode.mSetElement(_cp.mGetElement())
                                self.__appendNodes.append(_childNode)
                                break

                    #Append the node
                    if not _foundRelate:
                        _nodeFound.mAppfrontChild(_cp)
                        self.__appendNodes.append(_cp)
                        self.__oedacli.mLog("Warn", "Patched Green Node in XML", aFilename="ebCommandGenerator")
                        self.__oedacli.mLog("Warn", self.__tricolorTree.mStrNodesPath([_cp]), aFilename="ebCommandGenerator")
                else:
                    self.__oedacli.mLog("Warn", "Node to Find of Green Nodes not found on XML", aFilename="ebCommandGenerator")
                    self.__oedacli.mLog("Warn", self.__tricolorTree.mStrNodesPath([_findNode, aAppendNode]), aFilename="ebCommandGenerator")

        elif aAppendNode.mGetType() == "Red":

            #Delete node from Tree
            if _nodeSelf is not None and _nodeFound is not None:

                _tmpTree = ebTree()
                _tmpTree.mSetRoot(_nodeSelf)
                _tmpTree.mBFS(aStuffCallback=mAppendDelete)
                _nodeSelf.mRemove()

                self.__oedacli.mLog("Warn", "Patched Red Node in XML", aFilename="ebCommandGenerator")
                self.__oedacli.mLog("Warn", self.__tricolorTree.mStrNodesPath([_nodeSelf]), aFilename="ebCommandGenerator")
            else:
                #Check nodes already deleted by parents
                _foundInDelete = False
                for _nodeDelete in self.__deleteNodes:
                    _child = [x for x in _nodeDelete.mGetChildren() if x.mGetElement() == aAppendNode.mGetElement()]
                    if len(_child) >= 1:
                        self.__deleteNodes.append(_child[0])
                        _foundInDelete = True
                        break

                if not _foundInDelete:
                    self.__oedacli.mLog("Warn", "Red Node not found on XML", aFilename="ebCommandGenerator")
                    self.__oedacli.mLog("Warn", self.__tricolorTree.mStrNodesPath([_findNode, aAppendNode]), aFilename="ebCommandGenerator")

    def mEndCallbackHadle(self):
        #Register callbacks of end
        self.mVmSizeCallbackEnd()
        self.mMachineCallbackEnd()
        self.mNetworkCallbackEnd()
        self.mClusterCallbackEnd()
        self.mVipCallbackEnd()
        self.mScanCallbackEnd()
        self.mDiskGroupCallbackEnd()
        self.mDatabaseHomeCallbackEnd()
        self.mDatabaseCallbackEnd()

    def mCallbackHadle(self, aCallbackName, aTricolorNode):
        if aCallbackName == "vmSizeFx":
            self.mVmSizeCallback(aTricolorNode)
        elif aCallbackName == "databaseHomeFx":
            self.mDatabaseHomeCallback(aTricolorNode)
        elif aCallbackName == "databaseFx":
            self.mDatabaseCallback(aTricolorNode)
        elif aCallbackName == "machineFx":
            self.mMachineCallback(aTricolorNode)
        elif aCallbackName == "networkFx":
            self.mNetworkCallback(aTricolorNode)
        elif aCallbackName == "clusterFx":
            self.mClusterCallback(aTricolorNode)
        elif aCallbackName == "vipFx":
            self.mVipCallback(aTricolorNode)
        elif aCallbackName == "scanFx":
            self.mScanCallback(aTricolorNode)
        elif aCallbackName == "diskGroupFx":
            self.mDiskGroupCallback(aTricolorNode)
        elif aCallbackName == "postpatching":
            self.mPostpatchingCallback(aTricolorNode)
        elif aCallbackName == "colorpatching":
            self.mColorpatchingCallback(aTricolorNode)
        elif aCallbackName == "prepatching":
            self.mPrepatchingCallback(aTricolorNode)
        elif aCallbackName == "nothing":
            pass

    def mPostpatchingCallback(self, aTricolorNode):
        _structure = ebPatchStructure("post", aTricolorNode)
        self.__patchStructures.append(_structure)

    def mPrepatchingCallback(self, aTricolorNode):
        _structure = ebPatchStructure("pre", aTricolorNode)
        self.__patchStructures.append(_structure)

    def mColorpatchingCallback(self, aTricolorNode, aReference=None):
        _structure = ebPatchStructure(aNode=aTricolorNode, aReferenceNode=aReference)

        if aTricolorNode.mGetType() == "Red":
            _structure.mSetType("pre")
        elif aTricolorNode.mGetType() == "Green":
            _structure.mSetType("post")

        self.__patchStructures.append(_structure)

    def mColorpatchingFromCmd(self, aSharedName, aCmd, aObjectToDelete, aNodeToPatch):

        if aSharedName in list(self.__callbackShareData.keys()):
            for _id in list(self.__callbackShareData[aSharedName].keys()):
                _newobj = self.__callbackShareData[aSharedName][_id]

                if _newobj == aObjectToDelete and _newobj["cmd"] == aCmd:
                    self.__callbackShareData[aSharedName].pop(_id)
                    self.mColorpatchingCallback(aNodeToPatch)


    def mClusterCallback(self, aTricolorNode):
        _obj = self.mDefaultCommandCallback(aTricolorNode, "cluster")
        self.mColorpatchingFromCmd("clusterFx", "DELETE CLUSTER", _obj, aTricolorNode)

    def mClusterCallbackEnd(self):
        self.mDefaultCommandCallbackEnd("cluster")

    def mVipCallback(self, aTricolorNode):
        _obj = self.mDefaultCommandCallback(aTricolorNode, "clusterVip")
        self.mColorpatchingFromCmd("clusterVipFx", "DELETE VIP", _obj, aTricolorNode)

    def mVipCallbackEnd(self):
        self.mDefaultCommandCallbackEnd("clusterVip")

    def mScanCallback(self, aTricolorNode):
        self.mDefaultCommandCallback(aTricolorNode, "clusterScan")

    def mScanCallbackEnd(self):
        if "clusterScanFx" in list(self.__callbackShareData.keys()):
            for _id in list(self.__callbackShareData["clusterScanFx"].keys()):
                _obj = self.__callbackShareData["clusterScanFx"][_id]

                if "ID" in list(_obj.keys()):
                    _obj["forcepk"] = "CLUSTERID"
                    _obj["CLUSTERID"] = _obj.pop("ID").replace("Scan_client", "Home")
                    _obj["CLUSTERID"] = _obj["CLUSTERID"].replace("_scan_client", "")

        self.mDefaultCommandCallbackEnd("clusterScan")

    def mDiskGroupCallback(self, aTricolorNode):
        _obj = self.mDefaultCommandCallback(aTricolorNode, "diskGroup")

        #In case we have one ID from V2
        if "ORIGINAL" not in list(_obj.keys()):

            _parent = aTricolorNode
            while _parent.mGetSortElement() != "diskGroup":
                _parent = _parent.mGetParent()

            _obj['ORIGINAL'] = _parent.mGetElement()['id']
            for _child in _parent.mGetChildren():

                if _child.mGetSortElement() == "original":
                    _obj['ORIGINAL'] = _child.mGetElement()['text']
                    break

        #Delete the key of SliceSize since DiskGroupSize already in
        if "SLICESIZE" in list(_obj.keys()) and "DISKGROUPSIZE" in list(_obj.keys()):
            _obj.pop("SLICESIZE")

        #Delete the command of delete since OEDACLI does not support delete with empty cluster
        if _obj["cmd"] == "DELETE DISKGROUP":
            self.mColorpatchingCallback(aTricolorNode)

            if "diskGroupFx" in list(self.__callbackShareData.keys()):
                for _id in list(self.__callbackShareData["diskGroupFx"].keys()):
                    _newobj = self.__callbackShareData["diskGroupFx"][_id]

                    if _obj == _newobj:
                        self.__callbackShareData["diskGroupFx"].pop(_id)
                        break

    def mDiskGroupCallbackEnd(self):

        def mFindMachinesByType(aTreeNode, aConditionDict):
            if aTreeNode.mGetSortElement() == "machineType"  and \
               aTreeNode.mGetElement()["text"].lower() == aConditionDict["type"]:
                for _silbing in aTreeNode.mGetParent().mGetChildren():
                    if _silbing.mGetSortElement() == "hostName":
                        aConditionDict["result"].append(_silbing.mGetElement()["text"])

        def mFindClusterDiskGroup(aTreeNode, aDiskGroupId):
            return aTreeNode.mGetSortElement() == "diskGroup" and \
                   aTreeNode.mGetParent().mGetParent().mGetSortElement() == "cluster" and \
                   aTreeNode.mGetElement()['id'] == aDiskGroupId

        def mFindMachineById(aTreeNode, aMachineId):
            return aTreeNode.mGetSortElement() == "machine" and \
                   aTreeNode.mGetParent().mGetParent().mGetSortElement() == "engineeredSystem" and \
                   aTreeNode.mGetElement()['id'] == aMachineId

        if "diskGroupFx" in list(self.__callbackShareData.keys()):

            for _id in list(self.__callbackShareData["diskGroupFx"].keys()):
                _obj = self.__callbackShareData["diskGroupFx"][_id]

                _conditionDict = {"type": "storage", "result": []}
                self.__tricolorTree.mBFS(aStuffCallback=mFindMachinesByType, aStuffArgs=_conditionDict)

                if ("ALTER" in _obj["cmd"] or "ADD" in _obj["cmd"]) and _conditionDict["result"]:
                    _obj["CELLLIST"] = ",".join(list(set(_conditionDict["result"])))

                else:

                    # Transform cell list from ids to hostnames
                    if "CELLLIST" in _obj and _obj['CELLLIST']:

                        _newCellList = []
                        for _cellId in  _obj['CELLLIST'].split(","):
                            _node = self.__tricolorTree.mBFS(aElement=_cellId, aCompareCallback=mFindMachineById)

                            if _node is not None:

                                for _child in _node.mGetChildren():
                                    if _child.mGetSortElement() == "hostName":
                                        _newCellList.append(_child.mGetElement()['text'])
                                        break

                        if _newCellList:
                            _obj['CELLLIST'] = ",".join(_newCellList)
                        else:
                            del _obj["CELLLIST"]

                # Remove SPARSE not supported tags
                if "TYPE" in _obj and _obj['TYPE']:
                    if _obj['TYPE'].upper() == "SPARSE":
                        del _obj['TYPE']

                if "SPARSE" in _obj and _obj['SPARSE'].upper() == "TRUE":
                    _unsuported = ['ACFSNAME', 'ACFSPATH', 'ACFSSIZE']
                    for _unsuport in _unsuported:
                        if _unsuport in _obj:
                            del _obj[_unsuport]

                # Fetch the clustername in ADD DISKGROUP
                if _obj['cmd'].find("ADD") != -1:
                    _node = self.__tricolorTree.mBFS(aElement=_obj['ID'], aCompareCallback=mFindClusterDiskGroup)
                    if _node is not None:
                        _obj['CLUSTERID'] = _node.mGetParent().mGetParent().mGetElement()['id']
                        _obj['pk'] = "CLUSTERID"

                # Replace the original ID
                if "ORIGINAL" in list(_obj.keys()):
                    _obj["ID"] = _obj.pop("ORIGINAL")

        self.mDefaultCommandCallbackEnd("diskGroup")

    def mNetworkCallback(self, aTricolorNode):
        self.mDefaultCommandCallback(aTricolorNode, "network")

    def mNetworkCallbackEnd(self):
        self.mDefaultCommandCallbackEnd("network")

    def mMachineCallback(self, aTricolorNode):
        self.mDefaultCommandCallback(aTricolorNode, "machine")

    def mMachineCallbackEnd(self):
        self.mDefaultCommandCallbackEnd("machine")

    def mDatabaseHomeCallback(self, aTricolorNode):

        if aTricolorNode.mGetSortElement() == "patches" or aTricolorNode.mGetSortElement() == "patch":
            return None

        def mFindClusterId(aTreeNode, aClusterId):
            _nodePath = aTreeNode.mGetPathNode()
            _path = "/".join([x.mGetSortElement() for x in _nodePath])
            return _path == "engineeredSystem/software/clusters/cluster" and aTreeNode.mGetElement()["id"] == aClusterId

        _obj = self.mDefaultCommandCallback(aTricolorNode, "databaseHome")

        #Search the cluster Element on the Tree
        _clusterId   = None
        for _child in _obj["cmdFxNode"].mGetChildren():
            if _child.mGetSortElement() == "cluster":
                _clusterId = _child.mGetElement()["id"]
                break

        if _clusterId is not None:

            if "clusterNodes" not in list(self.__callbackShareData.keys()):
                self.__callbackShareData["clusterNodes"] = {}

            _shared = self.__callbackShareData["clusterNodes"]

            if _clusterId not in _shared.keys():
                _shared[_clusterId] = self.__tricolorTree.mBFS(aElement=_clusterId, aCompareCallback=mFindClusterId)

            #Remove cluster node since None
            if _shared[_clusterId] is None:
                if "databaseHomeFx" in list(self.__callbackShareData.keys()):
                    for _id in list(self.__callbackShareData["databaseHomeFx"].keys()):
                        _object = self.__callbackShareData["databaseHomeFx"][_id]
                        if _obj == _object:
                            self.__callbackShareData["databaseHomeFx"].pop(_id)

    def mDatabaseHomeCallbackEnd(self):

        if "databaseHomeFx" in list(self.__callbackShareData.keys()):
            _clusterIdCounters = {}
            for _id in list(self.__callbackShareData["databaseHomeFx"].keys()):
                _obj = self.__callbackShareData["databaseHomeFx"][_id]

                if _obj["cmd"] == "DELETE DATABASEHOME":
                    continue

                #Update the Cluster Id to OEDA Cluster ID
                if "CLUSTERID" in list(_obj.keys()):
                    _clusterId = _obj["CLUSTERID"]

                    if _clusterId not in _clusterIdCounters:
                        _clusterIdCounters[_clusterId] = 1

                    if "ID" in list(_obj.keys()):

                        _oldId = _obj["ID"]
                        _newId = _obj["CLUSTERID"].replace("cluster", "database")
                        _newId = _newId.replace("_id", "_databaseHome") + str(_clusterIdCounters[_clusterId])

                        _clusterIdCounters[_clusterId] += 1
                        _obj["ID"] = _newId
                        _obj["oldId"] = _oldId

                        #Update the Manual Patching Nodes with new cluster id
                        for _patchStructure in self.__patchStructures:
                            _node = _patchStructure.mGetNode()

                            while _node is not None and _node.mGetSortElement() != "databaseHome":
                                _node = _node.mGetParent()

                            if _node is not None:
                                if _node.mGetElement()["id"] == _oldId:
                                    _node.mGetElement()["id"] = _newId


        self.mDefaultCommandCallbackEnd("databaseHome")

    def mDatabaseCallback(self, aTricolorNode):
        self.mDefaultCommandCallback(aTricolorNode, "database")

    def mDatabaseCallbackEnd(self):

        #Change the DATADG by a fetch
        def mFindDgName(aTreeNode, aDiskId):
            return aTreeNode.mGetSortElement() == "diskGroupName" and aTreeNode.mGetParent().mGetElement()['id'] == aDiskId

        if "databaseFx" in list(self.__callbackShareData.keys()):
            for _id in list(self.__callbackShareData["databaseFx"].keys()):
                _obj = self.__callbackShareData["databaseFx"][_id]

                if "DBHOMEID" in list(_obj.keys()) and "databaseHomeFx" in list(self.__callbackShareData.keys()):
                    for _idDbHome in list(self.__callbackShareData["databaseHomeFx"].keys()):
                        _objDbHome = self.__callbackShareData["databaseHomeFx"][_idDbHome]

                        if "oldId" in list(_objDbHome.keys()) and _obj["DBHOMEID"] == _objDbHome["oldId"]:
                            _obj["DBHOMEID"] = _objDbHome["ID"]
                            break

                if "DG" in  list(_obj.keys()):
                    _iterDg = _obj.pop("DG").split(",")
                    for _datadg in _iterDg:
                        _node = self.__tricolorTree.mBFS(aElement=_datadg, aCompareCallback=mFindDgName)
                        if _node is not None:
                            _text = _node.mGetElement()['text']
                            if _text.find("RECO") != -1:
                                _obj["RECODG"] = _text
                            else:
                                _obj["DATADG"] = _text

        #Generate the commands
        self.mDefaultCommandCallbackEnd("database")

    def mDefaultCommandCallback(self, aTricolorNode, aUpperName):

        #Generate the Shared memory section
        _sharedName = "{0}Fx".format(aUpperName)

        if _sharedName not in list(self.__callbackShareData.keys()):
            self.__callbackShareData[_sharedName] = {}

        #Get the template and callbacks nodes
        _tplNode   = self.__template.mSearchByPath(aTricolorNode.mGetPathNode(), aCompareCallback=self.mCompareName)
        _tplFxNode = self.__template.mSearchByPath(aTricolorNode.mGetPathNode(), aCompareCallback=self.mCompareName)

        _cmdFxNode = aTricolorNode
        _parentCount  = 0

        while _cmdFxNode.mGetSortElement() != aUpperName:
            _cmdFxNode = _cmdFxNode.mGetParent()
            _tplFxNode = _tplFxNode.mGetParent()
            _parentCount += 1

        #Validate the cname
        if "cname" not in list(_tplFxNode.mGetElement().keys()):
            self.__oedacli.mLog("Warn", "Element actually without a cname:\n{0}".format(_tplFxNode), aFilename="ebCommandGenerator")
            return None

        #Generete the main object
        _id = _cmdFxNode.mGetElement()['id']
        _obj  = {}

        if _id not in self.__callbackShareData[_sharedName]:
            self.__callbackShareData[_sharedName][_id] = _obj
        else:
            _obj = self.__callbackShareData[_sharedName][_id]

        #Get the command to apply
        if _cmdFxNode.mGetType() == "Red":
            _obj["cmd"] = "DELETE"
        elif _cmdFxNode.mGetType() == "Green":
            _obj["cmd"] = "ADD"
        else:
            _obj["cmd"] = "ALTER"

        _obj["cmd"] = "{0} {1}".format(_obj["cmd"], _tplFxNode.mGetElement()["cname"])
        _obj["ID"]  = _id
        _obj["cmdFxNode"] = _cmdFxNode

        if "pk" in list(_tplNode.mGetElement().keys()):
            _obj["pk"] = _tplNode.mGetElement()["cname"]

        _banned = False
        if _obj["cmd"] in self.__bannedCmds:
            _banned = True
            _obj["banned"] = True

        #Generate the strucutre of the args in base of template name
        if "cname" in list(_tplNode.mGetElement().keys()) and not _banned:
            _cname =  _tplNode.mGetElement()["cname"]

            if _parentCount == 1:

                if aTricolorNode.mGetType() in ["Green", "White"]:
                    try:
                        if _cname.find("ID") != -1:
                            _obj[_cname] = aTricolorNode.mGetElement()["id"]
                        else:
                            _obj[_cname] = aTricolorNode.mGetElement()["text"]
                    except KeyError:
                        _obj[_cname] = aTricolorNode.mGetElement()["text"]

            elif _parentCount >= 2:

                if aTricolorNode.mGetType() in ["Green", "White"]:

                    _value = ""

                    try:
                        if _cname.find("ID") != -1:
                            _value = aTricolorNode.mGetElement()["id"]
                        else:
                            _value = aTricolorNode.mGetElement()["text"]
                    except KeyError:
                        _value = aTricolorNode.mGetElement()["text"]

                    if _cname in _obj:
                        _obj[_cname] = ",".join( _obj[_cname].split(",") + [_value] )

                    else:
                        _obj[_cname] = _value

        else:
            self.mColorpatchingCallback(aTricolorNode, _cmdFxNode)

        return _obj

    def mDefaultCommandCallbackEnd(self, aUpperName):

        _sharedName = "{0}Fx".format(aUpperName)

        if _sharedName in list(self.__callbackShareData.keys()):
            for _id in list(self.__callbackShareData[_sharedName].keys()):

                _object = self.__callbackShareData[_sharedName][_id]

                if "banned" in _object:
                    self.__oedacli.mLog("Info", f"Skip banned command {_object}", aFilename="ebCommandGenerator")
                    continue

                if _object["cmd"].find("DELETE") != -1:
                    self.__commandList.append([_object["cmd"], None, {"ID": _id}])
                else:
                    _cmd = _object["cmd"]
                    _args = {}
                    _where = {}

                    _passKeys = ["pk", "cmd", 'forcepk', "cmdFxNode", "oldId"]

                    if _cmd.find("ADD") == -1:
                        _object["pk"] = "ID"
                    else:
                        _passKeys.append("ID")

                    if "forcepk" in list(_object.keys()):
                        _object['pk'] = _object["forcepk"]

                    for _key in _object:
                        if _key not in _passKeys:
                            if "pk" in _object and _key == _object["pk"]:
                                _where[_key] = _object[_key]
                            else:
                                _args[_key] = _object[_key]

                    self.__commandList.append([_cmd, _args, _where])

    def mVmSizeCallback(self, aTricolorNode):

        if 'vmSizeFx' not in list(self.__callbackShareData.keys()):
            self.__callbackShareData['vmSizeFx'] = {}

        # OEDACLI vmsizes commands only are generated with White and Green nodes
        if aTricolorNode.mGetType() == "Red":
            return


        _vmSizeId = aTricolorNode.mGetParent().mGetElement()["id"]

        _object = {}
        if _vmSizeId not in list(self.__callbackShareData['vmSizeFx'].keys()):
            self.__callbackShareData['vmSizeFx'][_vmSizeId] = _object

            #Initializate the Node
            _machines = []

            def mStuff(aNode, aArgs):

                _machineList = aArgs[0]
                _vmSizeId    = aArgs[1]

                _elem = aNode.mGetElement()
                if 'vmSizeName' in _elem['tag'] and _elem["id"] == _vmSizeId:
                    if 'machine' in aNode.mGetParent().mGetElement()["tag"]:
                        _machineList.append(aNode.mGetParent())

            _args = [_machines, _vmSizeId]
            self.__tricolorTree.mBFS(aStuffCallback=mStuff, aStuffArgs=_args)

            _object["machines"] = _machines
        else:
            _object = self.__callbackShareData['vmSizeFx'][_vmSizeId]

        if aTricolorNode.mGetParent().mGetSortElement() == "machine":

            if aTricolorNode.mGetParent() not in _object['machines']:
                _object['machines'].append(aTricolorNode.mGetParent())

            if aTricolorNode.mGetSortElement() == "guestMemory":
                _object['VMEM'] = aTricolorNode.mGetElement()['text']
            elif aTricolorNode.mGetSortElement() == "guestCores":
                _object['VCPU'] = aTricolorNode.mGetElement()['text']
            elif aTricolorNode.mGetSortElement() == "guestLocalDiskSize":
                _object['guestLocalDiskSize'] = aTricolorNode.mGetElement()['text']

        else:

            _structure = ebPatchStructure("post", aTricolorNode)
            _structure.mSetIncludeText(False)
            self.__patchStructures.append(_structure)

            if 'MemSize' in aTricolorNode.mGetElement()['id']:
                _object['VMEM'] = aTricolorNode.mGetElement()['text']
            elif 'cpuCount' in aTricolorNode.mGetElement()['id']:
                _object['VCPU'] = aTricolorNode.mGetElement()['text']
            elif 'DiskSize' in aTricolorNode.mGetElement()['id']:
                _object['guestLocalDiskSize'] = aTricolorNode.mGetElement()['text']

    def mVmSizeCallbackEnd(self):

        if 'vmSizeFx' in list(self.__callbackShareData.keys()):

            for _vmSizeName in list(self.__callbackShareData['vmSizeFx'].keys()):
                _object = self.__callbackShareData['vmSizeFx'][_vmSizeName]

                for _machine in _object['machines']:
                    _cmdWhere = {"ID": _machine.mGetElement()['id']}
                    _cmdBase  = "ALTER MACHINE"

                    for _child in _machine.mGetChildren():
                        if _child.mGetElement()['tag'] == "vmSizeName":
                            _child.mSetType("Red")
                            self.__patchStructures.append(ebPatchStructure("post", _child, _machine))

                    if 'guestLocalDiskSize' in list(_object.keys()):
                        _node = ebTreeNode()
                        _dict = {"tag": "guestLocalDiskSize", "text": _object["guestLocalDiskSize"]}
                        self.__patchStructures.append(ebPatchStructure("post", _node, _machine))

                    if 'VMEM' in list(_object.keys()):
                        _cmdArgs  = {}
                        _cmdArgs['VMEM'] = _object["VMEM"]
                        _cmdArgs['ACTION'] = "SETVMEM"
                        self.__commandList.append([_cmdBase, _cmdArgs, _cmdWhere])

                    if 'VCPU' in list(_object.keys()):
                        _cmdArgs  = {}
                        _cmdArgs['VCPU'] = _object["VCPU"]
                        _cmdArgs['ACTION'] = "SETVCPU"
                        self.__commandList.append([_cmdBase, _cmdArgs, _cmdWhere])

# end of file
