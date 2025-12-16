#
# $Header: ecs/exacloud/exabox/infrapatching/core/clupatchmetadata.py /main/12 2025/03/25 10:03:33 araghave Exp $
#
# clupatchmetadata.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      clupatchmetadata.py - This module contains updating idempotent patch states
#
#    DESCRIPTION
#      Patch Metadata - Store and operate patching states via json object.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    araghave    03/04/25 - Bug 37417431 - EXACS | DOMU | UNWANTED SSH
#                           CONNECTION FROM 169.254.200.1 LOCKING OPC USER
#    avimonda    10/15/24 - Bug 37156068 - EXCEPTION IN
#                           MREADPATCHSTATESOBJECTFROMFILE() IS MISLEADING
#    araghave    08/27/24 - Enh 36829406 - PERFORM STRING INTERPOLATION USING
#                           F-STRINGS FOR ALL THE CORE, PLUGIN AND TASKHANDLER
#                           FILES
#    antamil     06/20/24 - Bug 36742410 - Fix for addressing the file creation
#                           issue for mgmt host as launch node
#    araghave    06/13/24 - Enh 36522596 - REVIEW PRE-CHECK/PATCHING/ROLLBACK
#                           LOGS AND CLEAN-UP
#    antamil     03/11/24 - Enh 36372221 - Code changes for single VM EXACS
#                           patching support
#    antamil     02/02/23 - 36109360 - Codes changes for Cps as launch node
#    araghave    07/08/21 - BUG 33081173 - Remove older error codes from Infra
#                           patching core files
#    nmallego    10/27/20 - Enh 31540038 - Fixing Typo ebCluPatchStateInfo
#    nmallego    08/28/20 - Refactor infra patching code
#    nmallego    08/28/20 - Creation
#

"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    Patch Metadata - Store and operate patching states via json object.

FUNCTION:
    Provide basic/core API for managing the Exadata patching states in the cluster.

    Sample json for patchstates Object:
          {
           "patchStates":[
              "_filePath":"filepath",
              "_targetNode":"targetNode"
              {
                 "nodes":[
                    {
                       "patchmgrRun":"running",
                       "postPatch":"running",
                       "prePatch":"running",
                       "nodeName":"nodeName_1"
                    },
                    {
                       "patchmgrRun":"running",
                       "postPatch":"running",
                       "prePatch":"running",
                       "nodeName":"nodeName_2"
                    }
                 ],
                 "launchNode":"dom0_launchNode",
                 "targetType":"dom0"
              },
              {
                 "nodes":[
                    {
                       "patchmgrRun":"completed",
                       "postPatch":"running",
                       "prePatch":"running",
                       "nodeName":"domu_nodeName_1"
                    },
                    {
                       "patchmgrRun":"running",
                       "postPatch":"running",
                       "prePatch":"running",
                       "nodeName":"domu_nodeName_2"
                    }
                 ],
                 "launchNode":"domu_launchNode_changed",
                 "targetType":"domu"
              }
           ],
          }
"""

import json
from exabox.infrapatching.utils.utility import runInfraPatchCommandsLocally, mGetInfraPatchingConfigParam
from json import JSONEncoder

from exabox.infrapatching.handlers.loghandler import LogHandler
from exabox.log.LogMgr import ebLogDebug, ebLogInfo, ebLogError
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext

try:
    from types import SimpleNamespace as Namespace
except ImportError:
    from argparse import Namespace

class ebCluPatchStateInfo(LogHandler):
    def __init__(self, patchStates, afilePath=None, aTargetNode=None):
        super(ebCluPatchStateInfo, self).__init__()
        self.patchStates = patchStates
        self.filePath = afilePath
        self.targetNode = aTargetNode

    def mSetFilePath(self, aFilePath):
        self.filePath = aFilePath

    def mSetTargetNode(self, aTargetNode):
        self.targetNode = aTargetNode

    @staticmethod
    def mBuildObjFromJson(json_object):
        _tempPatchStates = []
        if json_object is not None:
            try:
                for ps in json_object.patchStates:
                    _tempNodes = []
                    for n in ps.nodes:
                        _tempNodes.append(ebCluPsNode(n.nodeName, n.prePatch, n.patchmgrRun, n.postPatch))
                    _tempPatchStates.append(ebCluPatchState(ps.targetType, ps.launchNode, _tempNodes))

                return ebCluPatchStateInfo(_tempPatchStates)
            except:
                return None
        else:
            return None

    @staticmethod
    def mReadPatchStatesObjectFromFile(aFilePath, aTargetNode, aUser = 'root'):
        """
        Reads the json and forms the mReadPatchStatesObjectFromFile.
         aFilePath     --> File to read patch states
         aTargetNode   --> Target node where the file is read from (typically the launch node)
        """
        _node = None
        _node_list = []
        try:
            ebLogInfo(f"Reading patch state JSON file: {aFilePath}")
            if aTargetNode == 'localhost':
                _cmd_list = [['cat', aFilePath]]
                _rc, _o = runInfraPatchCommandsLocally(_cmd_list)
                if _o:
                    _node_list = _o.split("\n")
                else:
                    _node_list = []
            else:
                _node = exaBoxNode(get_gcontext())
                _node.mSetUser(aUser)
                _max_number_of_ssh_retries = mGetInfraPatchingConfigParam('max_number_of_ssh_retries')
                _node.mSetMaxRetries(int(_max_number_of_ssh_retries))
                _node.mConnect(aHost=aTargetNode)
                _i, _o, _e = _node.mExecuteCmd(f'cat {aFilePath}')
                _node_list = _o.readlines()

            output = []
            if _node_list:
                for ln in _node_list:
                    output.append(ln.replace("\n", "").strip())
                if len(output) < 1 :
                    raise RuntimeError(
                        f'Error while reading Patch States from nodes . Node = {aTargetNode}, input file = {aFilePath}. ')
                _patchStateJsonData = ''.join(output)
                ebLogInfo(f"Patch State output json : {json.dumps(_patchStateJsonData, indent=4)}")
            else:
                ebLogError(
                    f"Error: No nodes found in the input file . Please check the filePath {aFilePath} exists on TargetNode {aTargetNode} ")
                return None
        except Exception as e:
            raise Exception(
                f'Error: {str(e)} occurred while trying to read the patch states JSON file: {aFilePath} from the target node: {aTargetNode}.')
        finally:
            if _node != None:
                _node.mDisconnect()
        _patchStatesObj = json.loads(_patchStateJsonData, object_hook=lambda d: Namespace(**d))
        pss = ebCluPatchStateInfo.mBuildObjFromJson(_patchStatesObj)
        if pss is None:
            return None
        pss.filePath = aFilePath
        pss.targetNode = aTargetNode
        return pss

    def mWritePatchStatesToFile(self, aUser = 'root'):
        """
        Writes the patchmetadata states json to the file
        """
        _node = None
        patchStateJsonData = json.dumps(self, indent=4, cls=ebCluPatchStatesEncoder)
        try:
            self.mPatchLogInfo(f"Writing patch states JSON to file : {self.filePath}")
            if self.targetNode == 'localhost':
                _cmd_list = []
                _cmd_list.append(['printf', patchStateJsonData])
                _cmd_list.append(['tee', self.filePath])
                runInfraPatchCommandsLocally(_cmd_list)
            else:
                _node = exaBoxNode(get_gcontext())
                _node.mSetUser(aUser)
                _max_number_of_ssh_retries = mGetInfraPatchingConfigParam('max_number_of_ssh_retries')
                _node.mSetMaxRetries(int(_max_number_of_ssh_retries))
                _node.mConnect(aHost=self.targetNode)
                _cmd = None
                if aUser == 'root':
                    _cmd = f"printf '{patchStateJsonData}' > {self.filePath}"
                else:
                    _cmd = f"printf '{patchStateJsonData}' | sudo tee {self.filePath}"
                _node.mExecuteCmdLog(_cmd)
        except Exception as e:
            self.mPatchLogError(f"Error in Writing patch states to file : {self.filePath}")
            raise Exception(
                f'Error in Writing patch states to file in launchNode. LaunchNode = {self.targetNode}, file = {self.filePath}. Error: {str(e)}')
        finally:
            if _node and _node.mIsConnected():
                _node.mDisconnect()


    def mGetPatchStatesAsDictforNode(self, nodeName):
        """
        Returns the states as a dictionary for a node Name
        nodeName         --> Node Name for which the path status is required
        """
        states_dict = {}
        for ps in self.patchStates:
            for n in ps.nodes:
                if (n.nodeName == nodeName):
                    states_dict["launchNode"] = ps.launchNode
                    states_dict["targetType"] = ps.targetType
                    states_dict["nodeName"] = n.nodeName
                    states_dict["patchmgrRun"] = n.patchmgrRun
                    states_dict["postPatch"] = n.postPatch
                    states_dict["prePatch"] = n.prePatch
                    break

        if states_dict:
            self.mPatchLogInfo(f"Patch State for node {nodeName} is  {str(states_dict)}")
        return states_dict

    def getAllPatchStates(self):
        """
        Reads the json and forms the mReadPatchStatesObjectFromFile.
        """
        return self.patchStates

    def mPrintPatchStatesToConsole(self):
        """
         Prints the PatchMetata States to console for debugging purposes.
        """
        _patchStateJsonData = json.dumps(self, indent=4, cls=ebCluPatchStatesEncoder)
        self.mPatchLogInfo(f"Patch states to Console : {_patchStateJsonData}")

    def mUpdatePatchStates(self, targetType, nodeName, stateName, stateValue, aUser='root'):
        """
        Update the patch state for a given node to a specific value
        targetType         --> Target type (dom0 or domu)
        nodeName           --> Name of the node for which the patch state is updated
        stateName         --> Different patch states like prePatch,postPatch,patchmgrRun
        stateValue        --> pending , running , completed , failed
       """
        updated = False
        for ps in self.patchStates:
            if (ps.targetType == targetType and updated == False):
                for n in ps.nodes:
                    if (n.nodeName == nodeName and stateName == 'patch_mgr'):
                        n.patchmgrRun = stateValue
                        updated = True
                        break
                    elif (n.nodeName == nodeName and stateName == 'post_patch'):
                        n.postPatch = stateValue
                        updated = True
                        break
                    elif (n.nodeName == nodeName and stateName == 'pre_patch'):
                        n.prePatch = stateValue
                        updated = True
                        break
                    else:
                        updated = False

        if updated == True:
            self.mWritePatchStatesToFile(aUser)
        else:
            self.mPatchLogInfo("STATUS JSON NOT WRITTEN TO FILE AS NOTHING TO UPDATE")

    def mUpdateAllPatchStatesforNode(self, nodeName, stateValue, aUser='root'):
        """
        Update All the patch states to the specified stateValue for a given node.
        nodeName           --> Name of the node for which the patch state is updated
        stateValue         --> pending , running , completed , failed
       """
        updated = False
        for ps in self.patchStates:
            if updated == True:
                break
            for n in ps.nodes:
                if (n.nodeName == nodeName):
                    n.patchmgrRun = stateValue
                    n.postPatch = stateValue
                    n.prePatch = stateValue
                    updated = True
                    break
                else:
                    updated = False

        if updated == True:
            self.mWritePatchStatesToFile(aUser)
        else:
            self.mPatchLogError(f"Patch states not updated for Node {nodeName} ")

    def mUpdateLaunchNode(self, targetType, launchnodeName, aUser='root'):
        """
        Updates the value of the launchNode in case the launch Node value changes
        targetType         --> Target type (dom0 or domu)
        launchnodeName           --> Name of the launch Node
       """
        updated = False
        for ps in self.patchStates:
            if (ps.targetType == targetType and updated == False):
                ps.launchNode = launchnodeName
                updated = True
                break
        if updated == True:
            self.mWritePatchStatesToFile(aUser)
        else:
            self.mPatchLogInfo("STATUS JSON NOT WRITTEN TO FILE AS NOTHING TO UPDATE")

    def mGetLaunchNodeForTargetType(self, targetType):
        """
        Returns the value of the launchNode for a targetType (dom0 or domu)
        targetType    --> Target type (dom0 or domu)
       """
        for ps in self.patchStates:
            if (ps.targetType == targetType):
                return ps.launchNode

    def mAppendPatchStates(self, PatchState, aUser='root'):
        """
        Updates the value of the launchNode in case the launch Node value changes
        targetType         --> Target type (dom0 or domu)
        launchnodeName           --> Name of the launch Node
      """
        self.patchStates.append(PatchState)
        self.mWritePatchStatesToFile(aUser)

class ebCluPatchState:
    def __init__(self, targetType, launchNode, nodes):
        self.targetType = targetType
        self.launchNode = launchNode
        self.nodes = nodes


class ebCluPsNode:
    def __init__(self, nodeName, prePatch, patchmgrRun, postPatch):
        self.nodeName = nodeName
        self.prePatch = prePatch
        self.patchmgrRun = patchmgrRun
        self.postPatch = postPatch


class ebCluPatchStatesEncoder(JSONEncoder):
    def default(self, o):   # pylint: disable=E0202
        return o.__dict__

def mWritePatchInitialStatesToLaunchNodes(aNodeType, aNodeList, aMetadataNodesList, aMetadatafile, aUser = 'root'):
    """
    Method to create intial layout of the nodes which are expected to upgrade.
    Param list:
      aNoodeType         --> Target type for which, metadata for patching progress
                             should be created
      aNodeList          --> List of nodes to which are expected undergo patching
      aMetadataNodesList --> Nodes (launch nodes) where metadata can store in json format
      aMetadatafile      --> Location of the metadata json
    """

    ebLogInfo(
        f"Write initial metadata with file location '{aMetadatafile}' on all launch nodes = '{aMetadataNodesList}'")
    _nodes = []

    for _n in aNodeList:
        _node = ebCluPsNode(_n, "pending", "pending", "pending")
        _nodes.append(_node)

    _patchSates = []

    _patchSates.append(ebCluPatchState(aNodeType, "", _nodes))
    for _launchNode in aMetadataNodesList:
        _pstates = ebCluPatchStateInfo(_patchSates, aMetadatafile, _launchNode)
        _pstates.mWritePatchStatesToFile(aUser)


def mGetPatchStatesForNode(aMetadataNodesList, aMetadatafile, aNode, aStage, aUser = 'root'):
    """
    Method to fetch a value from the metadata json for a given
    stage (prePatch, patchmgr, post_path).
    Param list:
      aMetadataNodesList  --> Nodes (launch nodes) where metadata store in json format
      aMetadatafile       --> Location of the metadata json
      aNode               --> Get status of patching stage from the node.
      aStage              --> Need to value for the stage (prePatch, patchmgr, post_path).
    """
    _pss = None
    for _metadata_node in aMetadataNodesList:
        _pss = ebCluPatchStateInfo.mReadPatchStatesObjectFromFile(aMetadatafile, _metadata_node, aUser)
        if _pss:
            break

    if _pss is None:
        return None

    ebLogDebug("mGetPatchStatesForNode: Getting patch states dictionary")

    _patch_state_dict = _pss.mGetPatchStatesAsDictforNode(aNode)
    ebLogInfo(f"mGetPatchStatesForNode: Fetching status for {aStage} on {aNode}")
    if _patch_state_dict:
        if aStage.lower() == "patch_mgr".lower():
            return _patch_state_dict["patchmgrRun"]
        elif aStage.lower() == "pre_patch".lower():
            return _patch_state_dict["prePatch"]
        elif aStage.lower() == "post_patch".lower():
            return _patch_state_dict["postPatch"]
        else:
            ebLogError(f"No value found for patch stage = {aStage}")
            return None

def mUpdatePatchMetadata(aNodeType, aMetadataNodesList, aNode, aMetadatafile, aStage, aToUpdateStatus, aLaunchNode=None, aUser='root'):
    """
    Method to update patch state for a given stage (prePatch, patchmgr, postPatch).
    Param list:
      aNodeType           --> Update patch progress status for a given node type
      aMetadataNodesList  --> Nodes (mostly launch nodes) where metadata should be updated.
      aNode               --> Node for which patch state should be updated.
      aMetadatafile       --> Location of the metadata json
      aStage              --> Update operation state for a given stage.
      aToUpdateStatus     --> Update stage with state value.
    """
    if aLaunchNode:
        _pss = ebCluPatchStateInfo.mReadPatchStatesObjectFromFile(aMetadatafile, aLaunchNode, aUser)
        _pss.mUpdatePatchStates(aNodeType, aNode, aStage, aToUpdateStatus, aUser)
        for _metadata_node in aMetadataNodesList:
            if _metadata_node != aLaunchNode:
                ebLogInfo("Creating and Updating Patch States Metadata using Launch Node Data")
                _pss.mSetTargetNode(_metadata_node)
                _pss.mUpdatePatchStates(aNodeType, aNode, aStage, aToUpdateStatus, aUser)
    else:
        for _metadata_node in aMetadataNodesList:
            _pss = ebCluPatchStateInfo.mReadPatchStatesObjectFromFile(aMetadatafile, _metadata_node, aUser)
            if _pss:
                _pss.mUpdatePatchStates(aNodeType, aNode, aStage, aToUpdateStatus, aUser)

def mUpdateAllPatchStatesForNode(aMetadataNodesList, aNode, aMetadatafile, aToUpdateStatus, aUser='root'):
    """
    Method to update all patch states to a particular status for a node (pre_patch, patchmgr, post_patch).
    Param list:
      aMetadataNodesList  --> Nodes (mostly launch nodes) where metadata should be updated.
      aNode               --> Node for which patch state should be updated.
      aMetadatafile       --> Location of the metadata json
      aToUpdateStatus     --> Update stage with state value.
    """
    for _metadata_node in aMetadataNodesList:
        _pss = ebCluPatchStateInfo.mReadPatchStatesObjectFromFile(aMetadatafile, _metadata_node, aUser)
        if _pss:
            _pss.mUpdateAllPatchStatesforNode(aNode, aToUpdateStatus, aUser)
        else:
            ebLogError("ebCluPatchStateInfoObject Object is None in mUpdateAllPatchStatesForNode")

def mUpdateMetadataLaunchNode(aMetadataNodesList, aMetadatafile, aNodeType, aLaunchNode, aUser='root'):
    """
    Method to update patch state for a given stage (prePatch, patchmgr, postPatch).
    Param list:
      aMetadataNodesList  --> Nodes (mostly launch nodes) where metadata should be updated.
      aMetadatafile       --> Location of the metadata json
      aNodeType           --> This is node type (dom0 or domu).
      aLaunchNode         --> LaunchNode to Update
    """
    for _metadata_node in aMetadataNodesList:
        _pss = ebCluPatchStateInfo.mReadPatchStatesObjectFromFile(aMetadatafile, _metadata_node, aUser)
        if _pss:
            _pss.mUpdateLaunchNode(aNodeType, aLaunchNode, aUser)
        else:
            ebLogError(f"ebCluPatchSateInfo Object is None on node {_metadata_node} . So cannot update Metadata.")


def mGetLaunchNodeForTargetType(aMetadataNodesList, aMetadatafile, aTargetType, aUser='root'):
    """
    Method to fetch the launch node for a target type
    Param list:
      aMetadataNodesList  --> Nodes (launch nodes) where metadata store in json format
      aMetadatafile       --> Location of the metadata json
      aTargetType         --> dom0 or domu
    """
    ebLogDebug("mGetLaunchNodeForTargetType: Reading patch states")
    for _metadata_node in aMetadataNodesList:
        _pss = ebCluPatchStateInfo.mReadPatchStatesObjectFromFile(aMetadatafile, _metadata_node, aUser)
        if _pss:
            break

    return _pss.mGetLaunchNodeForTargetType(aTargetType)
