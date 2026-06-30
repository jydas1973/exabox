#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/selinuxcontrols.py /main/1 2026/02/02 09:28:33 aypaul Exp $
#
# selinuxcontrols.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      selinuxcontrols.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      06/09/26 - Bug#39439673 Rectify set selinux logs when state
#                           change is not required.
#    aypaul      05/25/26 - Bug#39432939 Updated string domU to domu for
#                           selinux operations
#    aypaul      04/23/26 - Bug#39225305 Remove reboot from infra nodes for SELinux
#                           update
#    aypaul      03/16/26 - ER#38277507 Add selinux operation response to ec
#                           data.
#    aypaul      01/16/26 - Creation
#
import json
import os
import copy
from base64 import b64encode
from collections import defaultdict

from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogDebug, ebLogError, ebLogInfo, ebLogTrace, ebLogWarn
from exabox.utils.node import connect_to_host

SELINUX_UPDATE_SUCCESS = 0


class ebSelinuxControls(object):

    def __init__(self, aClucontrolObject):
        self.__ebCluObj = aClucontrolObject
        self.__operationStatus = list()

    def mGetSELinuxStatusForClusterOperations(self):
        return self.__operationStatus

    def mGetSELinuxMode(self, aNodeType):

        if self.__ebCluObj.mGetOptions() is not None and self.__ebCluObj.mGetOptions().jsonconf is not None and self.__ebCluObj.mGetOptions().jsonconf.get("se_linux", None) is not None:
            if type(self.__ebCluObj.mGetOptions().jsonconf["se_linux"]) is str:
                return None
            aNodeType = aNodeType.lower()
            listOfInfraComponents = self.__ebCluObj.mGetOptions().jsonconf["se_linux"]["infraComponent"]
            for infraComponent in listOfInfraComponents:
                if infraComponent["component"] == aNodeType:
                    return infraComponent["mode"]

        return None

    """
    Function used to update SELinux configuration during selinux update API call and add-compute/storage operation
    """
    def mProcessSELinuxUpdate(self, aOptions, isElastic=False):

        """Return status code meaning:
           0 : Successful.
           1 : mode update failure only.
           2 : policy update failure only.
           3 : mode and policy update failure."""

        _hasModeUpdateFailed = False
        _hasPolicyUpdateFailed = False
        if aOptions is not None and aOptions.jsonconf is not None and aOptions.jsonconf.get("se_linux", None) is not None:
            if type(aOptions.jsonconf["se_linux"]) is str:
                _error_str = "Incorrect SE Linux configuration in request payload."
                raise ExacloudRuntimeError(0x0121, 0xA, _error_str, aStackTrace=False)
            listOfInfrastructureComponents = aOptions.jsonconf.get("se_linux").get("infraComponent", [])
            statusOfComponents = list()
            ebLogInfo("Shared environment: {0}".format(self.__ebCluObj.mGetSharedEnv()))
            listOfAllHosts = self.__ebCluObj.mGetHostList()
            for component in listOfInfrastructureComponents:
                completeStatus = dict()

                newMode = component["mode"]
                componentType = component["component"]
                componentType = componentType.lower()
                if componentType == "domu" and not isElastic:
                    ebLogWarn("SE Linux update operations for domUs are supported only during provisioning and elastic scale compute.")
                    continue

                listOfNodes = component["targetComponentName"]
                preComputedList = True
                if type(listOfNodes) is str and listOfNodes == "all":
                    preComputedList = False
                    listOfNodes = list()
                    if componentType == "dom0":
                        listOfNodes = [dom0 for dom0, _ in self.__ebCluObj.mReturnDom0DomUPair()]
                    elif componentType == "cell":
                        listOfNodes = [cell for cell in self.__ebCluObj.mReturnCellNodes()]
                    elif componentType == "domu":
                        listOfNodes = [domU for _, domU in self.__ebCluObj.mReturnDom0DomUPair()]

                if type(listOfNodes) is not list:
                    ebLogError("Invalid value for list of nodes. Value = {0}".format(listOfNodes))
                    _hasModeUpdateFailed = True
                    _hasPolicyUpdateFailed = True
                    continue

                if preComputedList:
                    _ret = self.mUpdateListWithDomainNameIfRequired(listOfNodes, listOfAllHosts)
                    if not _ret:
                        _error_str = "Failed to obtain domain name for list of Nodes."
                        raise ExacloudRuntimeError(0x0123, 0xA, _error_str, aStackTrace=False)

                ebLogInfo("Processing SE Linux updates for {0}s: {1}".format(componentType, listOfNodes))

                completeStatus["componentType"] = componentType
                nodeStatusList = list()
                _reboot_set = set()
                for thisNode in listOfNodes:
                    with connect_to_host(thisNode, get_gcontext()) as _node:
                        operationStatus = dict()
                        operationStatus["modeUpdate"] = "Success"
                        operationStatus["policyUpdate"] = "Success"
                        if self.mSetSeLinux(_node, newMode, componentType, operationStatus):
                            ebLogInfo(f"SELinux configuration was successful on {thisNode}")
                            if componentType == "domu":
                                _reboot_set.add(thisNode)

                        if operationStatus["modeUpdate"] == "Failure":
                            _hasModeUpdateFailed = True
                        if operationStatus["policyUpdate"] == "Failure":
                            _hasPolicyUpdateFailed = True
                        thisNodeStatus = dict()
                        thisNodeStatus["hostname"] = str(thisNode)
                        thisNodeStatus["status"] = operationStatus
                        nodeStatusList.append(thisNodeStatus)
                
                if _reboot_set:
                    self.__ebCluObj.mRebootNodesIfNoVMExists(_reboot_set, componentType, True)

                completeStatus["nodeStatus"] = nodeStatusList
                policyFileKey = "{0}_policy".format(componentType)
                if policyFileKey in aOptions.jsonconf.get("se_linux").keys():
                    policyFileList = aOptions.jsonconf.get("se_linux").get(policyFileKey)
                    for policyFile in policyFileList:
                        if os.path.exists(policyFile):
                            os.remove(policyFile)

                statusOfComponents.append(completeStatus)

            _reqobj = self.__ebCluObj.mGetRequestObj()
            detailedStatusInfo = dict()
            detailedStatusInfo["sestatus"] = statusOfComponents
            _reqobj.mSetStatusInfo(json.dumps(detailedStatusInfo, indent = 4))
            ebLogDebug("Complete status of operation: {0}".format(json.dumps(detailedStatusInfo, indent = 4)))
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_reqobj)

            if _hasModeUpdateFailed and _hasPolicyUpdateFailed:
                _error_str = "Failed to update SE Linux mode and policies."
                raise ExacloudRuntimeError(0x0123, 0xA, _error_str, aStackTrace=False)
            elif _hasModeUpdateFailed:
                _error_str = "Failed to update SE Linux mode."
                raise ExacloudRuntimeError(0x0124, 0xA, _error_str, aStackTrace=False)
            elif _hasPolicyUpdateFailed:
                _error_str = "Failed to update SE Linux policies."
                raise ExacloudRuntimeError(0x0125, 0xA, _error_str, aStackTrace=False)
            else:
                return SELINUX_UPDATE_SUCCESS
        else:
            _error_str = "Missing SE Linux configuration in request payload."
            raise ExacloudRuntimeError(0x0121, 0xA, _error_str, aStackTrace=False)

    def mUpdateListWithDomainNameIfRequired(self, listOfNodes, listOfAllHosts):

        hostNameToFQDNHostName = defaultdict(lambda: None)
        for thisHost in listOfAllHosts:
            hostName = thisHost.split(".")[0]
            hostNameToFQDNHostName[hostName] = thisHost
        
        for thisIndex, thisNode in enumerate(listOfNodes):
            if thisNode.find(".") == -1:
                if hostNameToFQDNHostName[thisNode] != None:
                    listOfNodes[thisIndex] = hostNameToFQDNHostName[thisNode]
                else:
                    return False

        return True

    def mSetSeLinux(self, aNode, aStatus, anodeType = None, operationStatusDict = None):
        """
          aNode: node connected ready to execute commands
          aStatus: desired status of SELinux to have -> Enabled or Disabled
          Return type: boolean
              True: Reboot needed to achieve desired SELinux status (i.e. sed performed)
              False: No reboot needed because desired SELinux status was already present
        """

        if aNode is None:
            ebLogError("Node object cannot be None")
            return False
        aStatus = str(aStatus).lower()
        _permissible_vals = ["enforcing", "permissive", "disabled"]
        _ctx = get_gcontext()
        anodeType = anodeType.lower()
        if aStatus not in _permissible_vals:
            ebLogError("*** Invalid SE_LINUX mode. Value: {0}".format(aStatus))
            if operationStatusDict is None:
                operationStatusDict = dict()
            operationStatusDict["hostname"] = aNode.mGetHostname()
            if anodeType == "domu":
                if _ctx.mCheckRegEntry('_natHN_' + aNode.mGetHostname()):
                    operationStatusDict["hostname"] = _ctx.mGetRegEntry('_natHN_' + aNode.mGetHostname())
            operationStatusDict["componentType"] = anodeType
            operationStatusDict["modeUpdate"] = "Failure"
            operationStatusDict["selinuxStatus"] = aStatus
            self.__operationStatus.append(copy.deepcopy(operationStatusDict))
            return False

        _modeUpdateStatus = "Success"
        _policyUpdateStatus = "Success"
        _node = aNode
        _cmdstr = "/bin/grep -i \"^\\s*SELINUX\" /etc/selinux/config"
        _f, _o, _e = _node.mExecuteCmd(_cmdstr)
        _rc = _node.mGetCmdExitStatus()
        _needs_change = False
        _current_status = "disabled"
        _lines = _o.readlines()

        if _rc == 0:
            for _line in _lines:
                _line = _line.replace(" ", "") 
                _line = _line.replace(os.linesep, "") 
                _vals = _line.split("=") #SELINUX=disabled/permissive/enforcing

                if len(_vals) == 2 and _vals[0] == "SELINUX":
                    if _vals[1] in _permissible_vals and _vals[1] != aStatus:
                        _current_status = _vals[1]
                        _needs_change = True
                        break

        _rv = False

        if _needs_change:
            _updateSELinuxMode = True
            if aStatus == "enforcing":
                _node.mExecuteCmdLog("/bin/touch /.autorelabel")
                _thisReturnCode = _node.mGetCmdExitStatus()
                if _thisReturnCode != 0:
                    ebLogError("Failed to create autorelabel file on the host. Will not update SELinux mode. Exception policies will be loaded if present.")
                    _updateSELinuxMode = False
                    _modeUpdateStatus = "Failure"
                else:
                    ebLogInfo("Successfully created the autorelabel file.")

            if _updateSELinuxMode:
                _cmdstr = "/bin/sed -i --follow-symlinks s/SELINUX={0}/SELINUX={1}/ /etc/selinux/config".format(_current_status, aStatus)
                _node.mExecuteCmdLog(_cmdstr)
                _thisReturnCode = _node.mGetCmdExitStatus()
                if _thisReturnCode != 0:
                    ebLogError("Failed to update mode to {0}".format(aStatus))
                    _modeUpdateStatus = "Failure"
                else:
                    _rv = True
                    ebLogInfo("SELinux will be {0}".format(aStatus))
        else:
            ebLogInfo("*** SE Linux value already at: {0}".format(aStatus))

        #Update policies on the node in case se linux status is set to enforcing.
        if aStatus == "enforcing" or aStatus == "permissive":
            if anodeType is None:
                ebLogWarn("*** Unable to update security policies for node type None.")
                _policyUpdateStatus = "Failure"
            else:
                anodeType = anodeType.lower()
                _keyName = "{0}_policy".format(anodeType)
                policyFileList = list()
                if type(self.__ebCluObj.mGetOptions().jsonconf.get("se_linux")) is str:
                    policyFileList = None
                else:
                    policyFileList = self.__ebCluObj.mGetOptions().jsonconf.get("se_linux").get(_keyName, None)

                if policyFileList is None:
                    ebLogWarn("*** Policy file details absent in payload. ***")
                else:
                    for _policy_file in policyFileList:
                        if not os.path.exists(_policy_file):
                            ebLogWarn("*** Unable to locate policy file: {0}".format(_policy_file))
                            _policyUpdateStatus = "Failure"
                        else:
                            simpleFileName = _policy_file.split("/")[-1]
                            currentUUID = simpleFileName.split(".")[0]
                            _dst_file = "/tmp/{0}_policies_{1}.pp".format(anodeType, currentUUID)
                            _node.mCopyFile(_policy_file, _dst_file)
                            _cmdstr = "/usr/sbin/semodule -i {0}".format(_dst_file)
                            _f, _o, _e = _node.mExecuteCmd(_cmdstr)
                            _rc = _node.mGetCmdExitStatus()
                            if _rc == 0:
                                ebLogInfo("{0} Security policies successfully loaded.".format(anodeType))
                            else:
                                ebLogError("Failed to load security policies for {0}.".format(anodeType))
                                _policyUpdateStatus = "Failure"

        if operationStatusDict is None:
            operationStatusDict = dict()
        operationStatusDict["hostname"] = aNode.mGetHostname()
        if anodeType == "domu":
            if _ctx.mCheckRegEntry('_natHN_' + aNode.mGetHostname()):
                operationStatusDict["hostname"] = _ctx.mGetRegEntry('_natHN_' + aNode.mGetHostname())
        operationStatusDict["componentType"] = anodeType
        operationStatusDict["modeUpdate"] = _modeUpdateStatus
        operationStatusDict["selinuxStatus"] = aStatus
        self.__operationStatus.append(copy.deepcopy(operationStatusDict))

        return _rv

    def mGetGeneratedSELinuxPolicies(self, aOptions):
        if aOptions is not None and aOptions.jsonconf is not None and aOptions.jsonconf.get("se_linux", None) is not None:
            if type(aOptions.jsonconf["se_linux"]) is str:
                _error_str = "Incorrect SE Linux configuration in request payload."
                raise ExacloudRuntimeError(0x0121, 0xA, _error_str, aStackTrace=False)

            _db = ebGetDefaultDB()
            dictHostToGeneratedPolicies = dict()
            listOfInfrastructureComponents = aOptions.jsonconf.get("se_linux").get("infraComponent", [])
            sendAll = aOptions.jsonconf.get("sendall", False)
            if sendAll:
                ebLogInfo("Exacloud will send back all generated policies irrespective of previous sync operation.")
            for component in listOfInfrastructureComponents:
                listOfNodes = component.get("targetComponentName", [])
                ebLogInfo("List of hosts to sync generated policy files: {}.".format(listOfNodes))
                for thisNode in listOfNodes:
                    targetHost = str(thisNode)
                    listOfPolicies = list()
                    if sendAll:
                        listOfPolicies = _db.mGetAllSELinuxPolicy(targetHost)
                    else:
                        listOfPolicies = _db.mGetUnsyncedSELinuxPolicy(targetHost)
                    if listOfPolicies is None or len(listOfPolicies) == 0:
                        dictHostToGeneratedPolicies[targetHost] = []
                    else:
                        finalListOfPolicies = list()
                        for thisRow in listOfPolicies:
                            finalListOfPolicies.append(thisRow[0])
                        dictHostToGeneratedPolicies[targetHost] = finalListOfPolicies
            _reqobj = self.__ebCluObj.mGetRequestObj()
            _reqobj.mSetStatusInfo(json.dumps(dictHostToGeneratedPolicies))
            ebLogTrace("Complete statusinfo of operation: {}".format(json.dumps(dictHostToGeneratedPolicies, indent = 4)))
            _db.mUpdateRequest(_reqobj)

            #Marking policies of all hosts currently synced with ECRA
            for component in listOfInfrastructureComponents:
                listOfNodes = component.get("targetComponentName", [])
                for thisNode in listOfNodes:
                    targetHost = str(thisNode)
                    _db.mUpdateAllPoliciesOfHostAsSynced(targetHost)

            return SELINUX_UPDATE_SUCCESS
        else:
            _error_str = "Missing required information in exacloud payload."
            raise ExacloudRuntimeError(0x0121, 0xA, _error_str, aStackTrace=False)

    def mGenerateCustomPolicyFileForThisRequest(self):
        reqObj = self.__ebCluObj.mGetRequestObj()
        if reqObj is not None:
            startTime = reqObj.mGetTimeStampStart()
            ebLogTrace("Request start time was: {}".format(startTime))
            dom0s = [dom0 for dom0, _ in self.__ebCluObj.mReturnDom0DomUPair()]
            generatedPolicyFileMap = dict()
            for dom0 in dom0s:
                checkNode = exaBoxNode(get_gcontext())
                checkNode.mSetUser("root")
                # The mIsConnectable have no retry hence this check makse sense here.
                if checkNode.mIsConnectable(aHost=dom0):
                    with connect_to_host(dom0, get_gcontext()) as dom0Node:

                        ebLogTrace("Checking if python3 exists on {}".format(dom0))
                        python3Executable = None
                        if dom0Node.mFileExists("/usr/bin/python3"):
                            python3Executable = "/usr/bin/python3"
                        if python3Executable is None and dom0Node.mFileExists("/bin/python3"):
                            python3Executable = "/bin/python3"

                        if python3Executable is None:
                            ebLogWarn("Python3 does not exist on node {}. Skipping custom SE Linux policy generation".format(dom0))
                            continue
                        customPolicyScriptPath = os.path.join(self.__ebCluObj.mGetBasePath(),"scripts/selinux/createCustomAuditLog.py")
                        remoteScriptPath = os.path.join("/root", "createCustomAuditLog.py")
                        try:
                            dom0Node.mCopyFile(customPolicyScriptPath, remoteScriptPath)
                        except:
                            continue
                        cmdToExecute = "{0} {1} -st \"{2}\"".format(python3Executable, remoteScriptPath, startTime)
                        ebLogTrace("Executing command: {}".format(cmdToExecute))
                        fin, fout, ferr = dom0Node.mExecuteCmd(cmdToExecute)

                        returnCode = dom0Node.mGetCmdExitStatus()
                        if returnCode != 0:
                            ebLogWarn("Failed to generate custom policies on {}".format(dom0))
                            err = ferr.readlines()
                            if err:
                                for e in err:
                                    ebLogWarn(e[:-1].encode('utf-8'))
                        else:
                            ebLogTrace("Command execution successful.")
                            out = fout.readlines()
                            if out:
                                for e in out:
                                    outputLine = e[:-1]
                                    ebLogTrace(outputLine)
                                    remoteFileLocation = None
                                    if outputLine.startswith("Custom policy file created:"):
                                        remoteFileLocation = outputLine.split(":")[1]
                                        baseName = os.path.basename(remoteFileLocation)
                                        strFileContent = dom0Node.mReadFile(remoteFileLocation)
                                        enc64Data = b64encode(strFileContent)
                                        strEncodedData = enc64Data.decode('utf-8')
                                        generatedPolicyFileMap[str(dom0)] = strEncodedData
                                        cmdToExecute = "/bin/rm {0}".format(remoteFileLocation)
                                        dom0Node.mExecuteCmd(cmdToExecute)
                        
                        cmdToExecute = "/bin/rm {0}".format(remoteScriptPath)
                        dom0Node.mExecuteCmd(cmdToExecute)

            if len(generatedPolicyFileMap.keys()) > 0:
                _db = ebGetDefaultDB()
                hostList = list(generatedPolicyFileMap.keys())
                for thisHost in hostList:
                    _db.mInsertGeneratedSELinuxPolicy(reqObj.mGetUUID(), thisHost,generatedPolicyFileMap.get(thisHost))
