"""

$Header: 

 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    ebExportExacloud - Basic functionality

FUNCTION:
   This class takes the OEDA XML, and after do a run on the XML, is going to match the tags with the EXATEMPLATE to generate the Exacloud XML,
   Additional, if exist a node on the EXATEMPLATE that match with the OEDA XML and does have a tag called 'examigrate'
   'examigrate' is a callback to migrate the OEDA xml to Exacloud XML, for example, on the VmSizes requirements

NOTE:
   Project Documentation: https://confluence.oraclecorp.com/confluence/pages/viewpage.action?pageId=1063643852

History:

    MODIFIED   (MM/DD/YY)
       aararora 10/31/25 - Bug 38595677: Get base path of exacloud independent
                           of sys.path
       scoral   20/03/24 - Bug 36427145: Change DiskSize from 60G to 20G.
       ndesanto 10/27/21 - Add default values for local guest
       naps     12/11/20 - zdlra provisioning support.
       naps     10/12/20 - zdlra provisioning support.
       naps     05/29/20 - set vm params for kvm.
       jesandov 16/04/20 - Bug31187942: Change DFS to BFS in tree execution
       naps     02/12/20 - merge kvm changes from pt to main.
       jesandov 17/12/18 - File Creation

"""

import os
import sys
import re

from exabox.tools.ebTree.ebTree import ebTree
from exabox.core.Error import ExacloudRuntimeError
from exabox.tools.ebTree.ebTreeNode import ebTreeNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose

class ebExportExacloud(object):

    def __init__(self, aOedaFile, aDebug=False):
        self.__exacloudTree = None

        self.__oedaFile     = aOedaFile
        self.__oedaTree     = ebTree(self.__oedaFile)
        _current_script_dir = os.path.dirname(os.path.abspath(__file__))
        _template_path = os.path.join(_current_script_dir, "exatemplateV1.tpl")
        self.__template     = ebTree(_template_path)

        self.__callbackShareData = {}

        self.__debug = aDebug

    def mOedaToExacloud(self):

        self.__exacloudTree = ebTree()
        _waitTags     = []

        def mCompareName(aNextNode, aPathNode):
            return aNextNode.mGetElement()['tag'] == aPathNode.mGetElement()['tag']

        def mStuff(aOedaNode, aArgsList):

            #Get the trees
            _tplTree = self.__template
            _exaTree = self.__exacloudTree
            _waitTag = _waitTags

            #Search the oeda node in template
            _nodeFound = _tplTree.mSearchByPath(aOedaNode.mGetPathNode(), aCompareCallback=mCompareName)
            if _nodeFound is not None:

                #Copy the oeda node in exacloud tree using the callbacks
                if _exaTree.mGetRoot() is None:
                    _exaTree.mSetRoot(aOedaNode.mCopy())
                else:
                    if "examigrate" in _nodeFound.mGetElement().keys():
                        self.mCallbackHadle(_nodeFound.mGetElement()['examigrate'], aOedaNode)
                    else:
                        self.mCallbackHadle("default", aOedaNode)

            else:
                _path = "/".join(aOedaNode.mGetPath())
                if _path not in _waitTag:
                    _waitTag.append(_path)

        self.__oedaTree.mBFS(aStuffCallback=mStuff)

        self.mEndCallbackHadle()

        if _waitTags:
            _waitTags.sort()
            if self.__debug:
                ebLogWarn("Nodes/Paths not found in template:")
            
            for _tag in _waitTags:
                if self.__debug:
                    ebLogWarn(_tag)

        return self.__exacloudTree

    def mEndCallbackHadle(self):
        #Register callbacks of end
        self.mDiskgroupCallbackEnd()
        self.mVmSizeCallbackEnd()

    def mCallbackHadle(self, aCallbackName, aOedaNode):
        if aCallbackName == "vmSizeFx":
            vmparams = ['guestCores', 'guestMemory', 'guestLocalDiskSize']
            if any(param in aOedaNode.mGetElement()['tag'] for param in vmparams):
                #Lets add these params in both places
                self.mDefaulCallback(aOedaNode)
                self.mVmSizeCallback(aOedaNode)
            else:
                self.mVmSizeCallback(aOedaNode)
        elif aCallbackName == "nothing":
            pass
        elif aCallbackName == "diskgroupFx":
            self.mDiskgroupCallback(aOedaNode)
        elif aCallbackName == "overrideParentFx":
            self.mOverrideParentCallback(aOedaNode)
        else:
            self.mDefaulCallback(aOedaNode)

    def mDefaulCallback(self, aOedaNode):

        _oedaParent = aOedaNode.mGetParent()
        if _oedaParent is not None:
            _exaParent  = self.__exacloudTree.mSearchByPath(_oedaParent.mGetPathNode())
            if _exaParent is not None:
                _exaParent.mAppendChild(aOedaNode.mCopy())

    def mOverrideParentCallback(self, aOedaNode):

        _oedaGrandParent = aOedaNode.mGetParent().mGetParent()
        _exaGrandParent = self.__exacloudTree.mSearchByPath(_oedaGrandParent.mGetPathNode())

        _oedaParent = aOedaNode.mGetParent().mGetParent()
        _exaParent = self.__exacloudTree.mSearchByPath(_oedaParent.mGetPathNode())

        _newParent = _exaParent.mCopy()

        if _newParent.mGetElement()["tag"].endswith("es"):
            _newParent.mGetElement()["tag"] = _newParent.mGetElement()["tag"][:-2]
        else:
            _newParent.mGetElement()["tag"] = _newParent.mGetElement()["tag"][:-1]

        _newParent.mAppendChild(aOedaNode.mCopy())

        _exaGrandParent.mAppendChild(_newParent)
        _exaGrandParent.mGetChildren().pop(0)

    def mDiskgroupCallback(self, aOedaNode):

        if 'diskgroupFx' not in self.__callbackShareData.keys():
            self.__callbackShareData['diskgroupFx'] = []

        _prevId = aOedaNode.mGetParent().mGetElement()['id']

        _newId   = aOedaNode.mGetElement()['text']
        _pattern = re.search("([a-zA-Z]{1,})([0-9]{1,})", _newId)

        if _pattern is not None:

            _clusterN = int(_pattern.group(2))-1
            _dgType   = _pattern.group(1).lower()

            if _dgType[-2:] == "dg":
                _dgType = _dgType[:-2]

            if _dgType[-1:] == "c":
                _dgType = _dgType[:-1]

            _newId = "c{0}_{1}dg".format(_clusterN, _dgType)
            _newId = _newId.replace("sprdg", "sparsedg")
        else:
            _newId = "{0}dg".format(_newId.lower())
           
        self.__callbackShareData['diskgroupFx'].append({"prev": _prevId, "new": _newId})
        self.mDefaulCallback(aOedaNode)


    def mDiskgroupCallbackEnd(self):

        def mChangeId(aNode, aSharedFx):
            for _obj in aSharedFx:
                if "id" in aNode.mGetElement().keys() and aNode.mGetElement()['id'] == _obj['prev']:
                    aNode.mGetElement()['id'] = _obj['new']
                    ebTreeNode(aElement={"tag": "original", "text": _obj['prev']}, aParent=aNode)
                    break

        if "diskgroupFx" in self.__callbackShareData:
            self.__exacloudTree.mBFS(aStuffCallback=mChangeId, aStuffArgs=self.__callbackShareData['diskgroupFx'])


    def mVmSizeCallback(self, aOedaNode):

        _machineOedaNode = aOedaNode.mGetParent()
        _machineExaNode  = self.__exacloudTree.mSearchByPath(_machineOedaNode.mGetPathNode())
        _machineExaNode.mSetPrintMemory(True)

        if 'vmSizeFx' not in self.__callbackShareData.keys():
            self.__callbackShareData['vmSizeFx'] = []

        _listInfo = self.__callbackShareData['vmSizeFx']

        _object = None
        for _info in _listInfo:
            if _info['machine'] == _machineExaNode:
                _object = _info
                break

        if _object is None:
            _object = {"machine": _machineExaNode}
            self.__callbackShareData['vmSizeFx'].append(_object)

        if 'guestCores' in aOedaNode.mGetElement()['tag']:
            _object['cpuCount'] = aOedaNode.mGetElement()['text']
        elif 'guestLocalDiskSize' in aOedaNode.mGetElement()['tag']:
            _object['DiskSize'] = aOedaNode.mGetElement()['text']
        elif 'guestMemory' in aOedaNode.mGetElement()['tag']:
            _object['MemSize'] = aOedaNode.mGetElement()['text']

    def mVmSizeCallbackEnd(self):

        def mLambda(aDict):
            _cp = aDict.copy()
            _cp.pop("machine")
            return set(_cp.items())

        def mCompare(aNode, aElement):
            return aElement in aNode.mGetElement()['tag']

        def mSizeInInfo(aSize, aInfo):
            for _key in aSize.keys():
                if _key not in aInfo.keys() or aSize[_key] != aInfo[_key]:
                    return False
            return True

        def mCreateVmSizeName(aVmSizeNode, aConfig):
            _vmSizeNameNode = ebTreeNode({"tag": "vmSizeName", "id": aConfig['id']}, aVmSizeNode)
            if 'MemSize' in aConfig:
                ebTreeNode({"tag": "vmAttribute", "id": "MemSize" , "text": aConfig['MemSize']},  _vmSizeNameNode)
            else:
                ebTreeNode({"tag": "vmAttribute", "id": "MemSize" , "text": "30Gb"},  _vmSizeNameNode)
            if 'cpuCount' in aConfig:
                ebTreeNode({"tag": "vmAttribute", "id": "cpuCount", "text": aConfig['cpuCount']}, _vmSizeNameNode)
            else:
                ebTreeNode({"tag": "vmAttribute", "id": "cpuCount", "text": "4"}, _vmSizeNameNode)
            if 'DiskSize' in aConfig:
                ebTreeNode({"tag": "vmAttribute", "id": "DiskSize", "text": aConfig['DiskSize']}, _vmSizeNameNode)
            else:
                ebTreeNode({"tag": "vmAttribute", "id": "DiskSize", "text": "20Gb"}, _vmSizeNameNode)

        _vmSizesNode = self.__exacloudTree.mBFS("vmSizes", aCompareCallback=mCompare)
        if 'vmSizeFx' in self.__callbackShareData.keys() and _vmSizesNode is None:

            _listInfo = self.__callbackShareData['vmSizeFx']

            #Calculate the different VM Sizes
            _sizes = list(map(mLambda, _listInfo))
            _sizes.sort()
            _sizes = [ dict(x) for x in _sizes ]

            _vmSizeNode = ebTreeNode({"tag": "vmSizes"}, self.__exacloudTree.mGetRoot())

            _sizeNames = ["Small", "Medium", "Large"]
            _counter = 3

            if len(_sizes) == 2:
                _sizes.append(_sizes[0])

            if len(_sizes) == 1:
                _sizes.append(_sizes[0])
                _sizes.append(_sizes[0])

            for _size in _sizes:

                #Get the tag name
                _config = _size.copy()
                if _counter <= 0:
                    _config['id'] = "misc" + str(abs(_counter))
                else:
                    _config['id'] = _sizeNames[_counter-1]

                #Append to every machine
                for _info in _listInfo:

                    if mSizeInInfo(_size, _info):
                        _machineNode = _info['machine']
                        _alreadyTag  = False

                        for _child in _machineNode.mGetChildren():
                            if _child.mGetElement()['tag'] == "vmSizeName":
                                _alreadyTag = True


                        if not _alreadyTag:
                            _vmSizeName = ebTreeNode({"tag": "vmSizeName", "id": _config['id']})
                            _machineNode.mAppendChild(_vmSizeName)

                mCreateVmSizeName(_vmSizeNode, _config)
                _counter -= 1


