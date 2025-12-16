""" 
 Copyright (c) 2014, 2024, Oracle and/or its affiliates.

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

History:
    MODIFIED (MM/DD/YY)
    avimonda    10/15/24 - Bug 37156068 - EXCEPTION IN
                           MREADPATCHSTATESOBJECTFROMFILE() IS MISLEADING
    nmallego    04/14/20 - ER 30995812 - Make pre and post plugins idempotent
    nmallego    03/25/20 - ER 30995919 - Store json metadata for the patch operation
"""

import json
from json import JSONEncoder
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext

try:
    from types import SimpleNamespace as Namespace
except ImportError:
    from argparse import Namespace

class ebCluPatchSateInfo:
    def __init__(self, patchStates, afilePath=None, aTargetNode=None):
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

                return ebCluPatchSateInfo(_tempPatchStates)
            except:
                pass

    @staticmethod
    def mReadPatchStatesObjectFromFile(aFilePath, aTargetNode):
        """
        Reads the json and forms the ebCluPatchSateInfoObject.
         aFilePath     --> File to read patch states
         aTargetNode   --> Target node where the file is read from (typically the launch node)
        """
        try:
            ebLogDebug("Reading patch state JSON file: %s" % aFilePath)
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=aTargetNode)
            _i, _o, _e = _node.mExecuteCmd('cat %s' % aFilePath)
            _node_list = _o.readlines()
            output = []
            if _node_list:
                for ln in _node_list:
                    output.append(ln.replace("\n", "").strip())
                if len(output) < 1 :
                    raise RuntimeError('Error while reading Patch States from nodes . Node = %s, input file = %s. ' % (aTargetNode, aFilePath))
                _patchStateJsonData = ''.join(output)
                ebLogDebug("Patch State output json : %s" % _patchStateJsonData)
            else:
                ebLogError("Warning: No nodes found in the input file . Please check the filePath %s exists on TargetNode %s " % (aTargetNode, aFilePath))
                raise RuntimeError('Error while reading Patch States from nodes . Node = %s, input file = %s. ' % (aTargetNode, aFilePath))
        except Exception as e:
            raise Exception('Error: {str(e)} occurred while trying to read the patch states JSON file: {aFilePath} from the target node: {aTargetNode}.')
        finally:
            _node.mDisconnect()

        _patchStatesObj = json.loads(_patchStateJsonData, object_hook=lambda d: Namespace(**d))
        pss = ebCluPatchSateInfo.mBuildObjFromJson(_patchStatesObj)
        pss.filePath = aFilePath
        pss.targetNode = aTargetNode
        return pss

    def mWritePatchStatesToFile(self):
        """
        Writes the patchmetadata states json to the file
        """
        patchStateJsonData = json.dumps(self, indent=4, cls=ebCluPatchStatesEncoder)
        try:
            ebLogDebug("Writing patch states JSON to file : %s" % self.filePath)
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=self.targetNode)
            _node.mExecuteCmdLog("printf '%s' > %s" % (patchStateJsonData, self.filePath))

        except Exception as e:
            ebLogError("Error in Writing patch states to file : %s" % self.filePath)
            raise Exception(
                'Error in Writing patch states to file in launchNode. LaunchNode = %s, file = %s. Error: %s' % (
                    self.targetNode, self.filePath, str(e)))
        finally:
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
            ebLogInfo("Patch State Dictionary fetched : %s" % str(states_dict))
        return states_dict

    def getAllPatchStates(self):
        """
        Reads the json and forms the ebCluPatchSateInfoObject.
        """
        return self.patchStates

    def mPrintPatchStatesToConsole(self):
        """
         Prints the PatchMetata States to console for debugging purposes.
        """
        _patchStateJsonData = json.dumps(self, indent=4, cls=ebCluPatchStatesEncoder)
        ebLogInfo("Patch states to Console : %s" % _patchStateJsonData)

    def mUpdatePatchStates(self, targetType, nodeName, stateName, stateValue):
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
            self.mWritePatchStatesToFile()
        else:
            ebLogDebug("STATUS JSON NOT WRITTEN TO FILE AS NOTHING TO UPDATE")

    def mUpdateAllPatchStatesforNode(self, nodeName, stateValue):
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
            self.mWritePatchStatesToFile()
        else:
            ebLogError("Patch states not updated for Node %s " %(nodeName))

    def mUpdateLaunchNode(self, targetType, launchnodeName):
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
            self.mWritePatchStatesToFile()
        else:
            ebLogDebug("STATUS JSON NOT WRITTEN TO FILE AS NOTHING TO UPDATE")

    def mGetLaunchNodeForTargetType(self, targetType):
        """
        Returns the value of the launchNode for a targetType (dom0 or domu)
        targetType    --> Target type (dom0 or domu)
       """
        for ps in self.patchStates:
            if (ps.targetType == targetType):
                return ps.launchNode

    def mAppendPatchStates(self, PatchState):
        """
        Updates the value of the launchNode in case the launch Node value changes
        targetType         --> Target type (dom0 or domu)
        launchnodeName           --> Name of the launch Node
      """
        self.patchStates.append(PatchState)
        self.mWritePatchStatesToFile()


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

def mWritePatchInitialStatesToLaunchNodes(aNodeType, aNodeList, aMetadataNodesList, aMetadatafile):
    """
    Method to create intial layout of the nodes which are expected to upgrade.
    Param list:
      aNoodeType         --> Target type for which, metadata for patching progress 
                             should be created 
      aNodeList          --> List of nodes to which are expected undergo patching
      aMetadataNodesList --> Nodes (launch nodes) where metadata can store in json format 
      aMetadatafile      --> Location of the metadata json
    """

    ebLogInfo("Write initial metadata with file location '%s' on all launch nodes = '%s'" % 
               (aMetadatafile, aMetadataNodesList))
    _nodes = []

    for _n in aNodeList:
        _node = ebCluPsNode(_n, "pending", "pending", "pending")
        _nodes.append(_node)

    _patchSates = []

    _patchSates.append(ebCluPatchState(aNodeType, "", _nodes))
    for _launchNode in aMetadataNodesList: 
        _pstates = ebCluPatchSateInfo(_patchSates, aMetadatafile, _launchNode)
        _pstates.mWritePatchStatesToFile()


def mGetPatchStatesForNode(aMetadataNodesList, aMetadatafile, aNode, aStage):
    """
    Method to fetch a value from the metadata json for a given
    stage (prePatch, patchmgr, post_path).
    Param list:
      aMetadataNodesList  --> Nodes (launch nodes) where metadata store in json format 
      aMetadatafile       --> Location of the metadata json
      aNode               --> Get status of patching stage from the node. 
      aStage              --> Need to value for the stage (prePatch, patchmgr, post_path).  
    """
    for _metadata_node in aMetadataNodesList:
        _pss = ebCluPatchSateInfo.mReadPatchStatesObjectFromFile(aMetadatafile, _metadata_node)
        if _pss:
            break

    ebLogDebug("mGetPatchStatesForNode: Getting patch states dictionary")

    _patch_state_dict = _pss.mGetPatchStatesAsDictforNode(aNode)
    ebLogInfo("mGetPatchStatesForNode: Fetching status for %s on %s" % (aStage, aNode))
    if _patch_state_dict:
        if aStage.lower() == "patch_mgr".lower():
            return _patch_state_dict["patchmgrRun"]
        elif aStage.lower() == "pre_patch".lower():
            return _patch_state_dict["prePatch"]
        elif aStage.lower() == "post_patch".lower():
            return _patch_state_dict["postPatch"]
        else:
            ebLogError("No value found for patch stage = %s" % aStage)
            return None

def mUpdatePatchMetadata(aNodeType, aMetadataNodesList, aNode, 
                         aMetadatafile, aStage, aToUpdateStatus):
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
    for _metadata_node in aMetadataNodesList:
        _pss = ebCluPatchSateInfo.mReadPatchStatesObjectFromFile(aMetadatafile, _metadata_node)
        if _pss:
            _pss.mUpdatePatchStates(aNodeType, aNode, aStage, aToUpdateStatus)

def mUpdateAllPatchStatesForNode(aMetadataNodesList, aNode, aMetadatafile, aToUpdateStatus):
    """
    Method to update all patch states to a particular status for a node (pre_patch, patchmgr, post_patch).
    Param list:
      aMetadataNodesList  --> Nodes (mostly launch nodes) where metadata should be updated.
      aNode               --> Node for which patch state should be updated.
      aMetadatafile       --> Location of the metadata json
      aToUpdateStatus     --> Update stage with state value.
    """
    for _metadata_node in aMetadataNodesList:
        _pss = ebCluPatchSateInfo.mReadPatchStatesObjectFromFile(aMetadatafile, _metadata_node)
        if _pss:
            _pss.mUpdateAllPatchStatesforNode(aNode, aToUpdateStatus)

def mUpdateMetadataLaunchNode(aMetadataNodesList, aMetadatafile, aNodeType, aLaunchNode):
    """
    Method to update patch state for a given stage (prePatch, patchmgr, postPatch).
    Param list:
      aMetadataNodesList  --> Nodes (mostly launch nodes) where metadata should be updated.
      aMetadatafile       --> Location of the metadata json
      aNodeType           --> This is node type (dom0 or domu).
      aLaunchNode         --> LaunchNode to Update
    """
    for _metadata_node in aMetadataNodesList:
        _pss = ebCluPatchSateInfo.mReadPatchStatesObjectFromFile(aMetadatafile, _metadata_node)
        if _pss:
            _pss.mUpdateLaunchNode(aNodeType, aLaunchNode)

def mGetLaunchNodeForTargetType(aMetadataNodesList, aMetadatafile, aTargetType):
    """
    Method to fetch the launch node for a target type
    Param list:
      aMetadataNodesList  --> Nodes (launch nodes) where metadata store in json format
      aMetadatafile       --> Location of the metadata json
      aTargetType         --> dom0 or domu
    """
    ebLogDebug("mGetLaunchNodeForTargetType: Reading patch states")
    for _metadata_node in aMetadataNodesList:
        _pss = ebCluPatchSateInfo.mReadPatchStatesObjectFromFile(aMetadatafile, _metadata_node)
        if _pss:
            break

    return _pss.mGetLaunchNodeForTargetType(aTargetType)
