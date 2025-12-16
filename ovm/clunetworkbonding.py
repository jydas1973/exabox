#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/clunetworkbonding.py /main/8 2025/03/05 16:36:07 rkhemcha Exp $
#
# clunetworkbonding.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      clunetworkbonding.py - ExaCC network bonding operations
#
#    DESCRIPTION
#      ebCluNetworkBonding: Wrapper class to modify and validate bonding mode on the dom0s
#      NetworkBondingUtils: Helper class for node and network specific entities
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    rkhemcha    02/26/25 - 37628410 - Bump bonded bridge during LACP validate
#                           bonding mode
#    ririgoye    06/18/24 - Bug 36746656 - PYTHON 3.11 - EXACLOUD NEEDS TO
#                           UPDATE DEPRECATED/OLDER IMPORTS DYNAMICALLY
#    rkhemcha    01/10/24 - 35903105 - Handle empty participating_computes in
#                           payload
#    rkhemcha    09/22/23 - 35720047 - Add MII Status check to ensure physical
#                           interfaces up for bonding mode validation
#    rkhemcha    06/15/23 - 35500787 - Manually bring up base bridge, since it goes
#                           down after ifdown of bonded interface
#    rkhemcha    06/12/23 - 35489020 - Manually set DR net enabled to true, for
#                           DR net discovery
#    rkhemcha    12/07/22 - 34841682 - Add input validation for shared
#                           interfaces flow
#    rkhemcha    09/24/22 - Creation
#

import ast
import copy
from contextlib import contextmanager
import json
import os
from time import sleep
import xml.etree.ElementTree as ET

from exabox.log.LogMgr import ebLog
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.utils.node import connect_to_host
from exabox.core.Error import ExacloudRuntimeError, gNetworkError
from exabox.core.DBStore import ebGetDefaultDB

try:
    from collections import Counter
except ImportError:
    from collections.abc import Counter

ACTIVE_BACKUP = "active-backup"
LACP = "lacp"


class ebCluNetworkBonding:

    def __init__(self, aExaBoxCluCtrl, aOptions, operation) -> None:
        self.__ebox = aExaBoxCluCtrl
        self.operation = operation
        self.inputData = aOptions.jsonconf
        self.outputData = copy.deepcopy(self.inputData)
        self.__jsonmode = aOptions.jsonmode
        self._mValidateEnv()
        self._sharedClientBackup = {}
        self.intfInfoDom0s = {}
        self._mLogPayload()
        self._mValidatePayload(self.inputData)
        self._mSetEmptyResult()

    def _mGetEbox(self):
        return self.__ebox

    def _mLogPayload(self):
        # log header
        ebLog(
            "nw_bonding",
            "INFO",
            "{}{:->80}{}{:-<80}".format(
                "\n", "\n", f"Starting network bonding {self.operation}", "\n"
            ),
        )
        ebLog("nw_bonding", "DEBUG", json.dumps(self.inputData, indent=4))

    def _mValidateEnv(self):
        """
        Checks if env is OCI EXACC setup.
        Raises: ExacloudRuntimeError if not ociexacc
        """
        ebox = self._mGetEbox()
        if not ebox.mIsOciEXACC():
            msg = "Detected non-OCIEXACC environment. Network Bonding change is not supported"
            ebLog("nw_bonding", "ERROR", msg)
            ebox.mUpdateErrorObject(gNetworkError["INVALID_OPERATION"], msg)
            raise ExacloudRuntimeError(0x8005, 0xA, msg)

    def _mValidatePayload(self, payload):
        """
        Validates the input payload for required information.

        Raises:
            ExacloudRuntimeError: If payload has missing information
        """

        validPayload = True
        requiredKeys = ["network_types", "participating_computes"]
        bondingStates = ["current", "new"]

        for key in requiredKeys:
            if key not in payload.keys():
                validPayload = False
                _msg = f"Missing required info {key} in the input payload."
                ebLog("nw_bonding", "ERROR", _msg)
            else:
                if key == "network_types":
                    # validate bonding modes
                    for network, networkInfo in payload["network_types"].items():
                        if not networkInfo.get("bonding_mode"):
                            validPayload = False
                            _msg = f"Missing required bonding_mode info for {network} network in the input payload."
                            ebLog("nw_bonding", "ERROR", _msg)
                        else:
                            for state in bondingStates:
                                if not networkInfo["bonding_mode"].get(state):
                                    validPayload = False
                                    _msg = f"Missing required {state} state for {network} network bonding in the input payload."
                                    ebLog("nw_bonding", "ERROR", _msg)

                elif key == "participating_computes":
                    compute_list = payload.get("participating_computes")

                    # validate empty participating computes
                    if compute_list is None or len(compute_list) == 0:
                        validPayload = False
                        _msg = f"Empty participating_computes received in the input payload."
                        ebLog("nw_bonding", "ERROR", _msg)

                    # validate participating computes
                    for node in payload.get("participating_computes"):
                        if not node.get("compute_node_hostname"):
                            validPayload = False
                            _msg = f"Missing required dom0 FQDN for node {node} in the input payload."
                            ebLog("nw_bonding", "ERROR", _msg)

        # If payload is not missing any required info, continue
        # Check if dom0's share client/backup networks, and validate payload accordingly
        if validPayload:
            validPayload = self.validateSharedIntfPayload(payload)

        if not validPayload:
            _msg = f"Invalid input payload received. Please check the payload and retry."
            self._mGetEbox().mUpdateErrorObject(gNetworkError["INVALID_INPUT_PARAMETER"], _msg)
            raise ExacloudRuntimeError(0x8001, 0xA, _msg)

    def validateSharedIntfPayload(self, payload):
        """
        :param payload:
        :return: Bool, if payload is correct in case client/backup interfaces are shared
        """
        _target_bond_client = payload["network_types"]["client"]["bonding_mode"]["new"]
        _target_bond_backup = payload["network_types"]["backup"]["bonding_mode"]["new"]
        # for every dom0, check if client/backup networks share the same interface
        for _dom0Payload in payload["participating_computes"]:
            _dom0 = _dom0Payload["compute_node_hostname"]
            self._sharedClientBackup[_dom0] = False
            if payload.get("network_types").get("dr") is not None:
                self.__ebox.mSetDRNetPresent(True)
            _dom0_network = self.__ebox.mGetNetworkSetupInformation("all", _dom0)
            # store dom0 network info for use in later flows
            if not self.intfInfoDom0s.get(_dom0):
                self.intfInfoDom0s[_dom0] = _dom0_network
            _client_intfs = set(_dom0_network["client"]["bond_slaves"].split())
            _backup_intfs = set(_dom0_network["backup"]["bond_slaves"].split())

            # store shared info metadata to optimise other flows
            if _client_intfs == _backup_intfs:
                ebLog("nw_bonding", "INFO", f"Shared Client and Backup interfaces identified on node {_dom0}.")
                self._sharedClientBackup[_dom0] = True

            if (self._sharedClientBackup[_dom0] and
                    _target_bond_client != _target_bond_backup):
                _msg = f"Shared client and backup interfaces identified on node {_dom0}, " \
                       f"but target bonding for both interfaces received different."
                ebLog("nw_bonding", "ERROR", _msg)
                return False

        return True

    def _mUpdateRequestData(self, aData):  # pragma: no cover
        """
        Updates request object with the response payload
        """
        _reqobj = self._mGetEbox().mGetRequestObj()
        if _reqobj is not None:
            _db = ebGetDefaultDB()
            _reqobj.mSetData(json.dumps(aData, sort_keys=True))
            _db.mUpdateRequest(_reqobj)
        elif self.__jsonmode:
            print(json.dumps(aData, indent=4, sort_keys=True))

    def _mSetEmptyResult(self):
        """
        Creates return payload with dummy values
        """

        self.outputData["overallStatus"] = "FAILURE"
        self.outputData["msg"] = ""

        for node in self.outputData["participating_computes"]:
            # add network_types section for every participating_compute
            netTypes = copy.deepcopy(self.outputData["network_types"])
            _bondingInfo = {"network_types": netTypes}
            for _, _netDetails in _bondingInfo["network_types"].items():
                _netDetails.update({"status": "FAILURE", "msg": ""})

            node.update(_bondingInfo)

        del self.outputData["network_types"]
        self._mUpdateRequestData(self.outputData)

    def mApply(self, operation):
        """
        Applies network bonding modification/validation
        Initialises NetworkUpdatePayload and iterate over all nodes and network in sequence
        Sets final success/error messages and updates status to db.
        """

        __eBox = self._mGetEbox()
        overallFailure = False

        for node in self.outputData.get("participating_computes"):
            dom0 = node.get("compute_node_hostname")

            for network, networkInfo in node["network_types"].items():

                if operation == "modification":
                    opHandler = NetworkBondingModifier(
                        __eBox, network, dom0, networkInfo, self.intfInfoDom0s
                    )
                elif operation == "validation":
                    opHandler = NetworkBondingValidator(
                        __eBox, network, dom0, networkInfo, self.intfInfoDom0s
                    )
                else:
                    _msg = f"Wrong operation {operation} identified. Exiting."
                    ebLog("nw_bonding", "ERROR", _msg)
                    raise ExacloudRuntimeError(0x8005, 0xA, _msg)

                try:
                    opHandler.mPerformOp()
                    result = opHandler.mGetResult()
                    node["network_types"][network] = result

                except ExacloudRuntimeError as err:
                    overallFailure = True
                    result = opHandler.mGetResult()
                    node["network_types"][network] = result
                    error = gNetworkError[opHandler.mGetResultErrorcode()]
                    __eBox.mUpdateErrorObject(error, err.mGetErrorMsg())
                    overallResult = {
                        "overallStatus": "FAILURE",
                        "msg": err.mGetErrorMsg(),
                        "errorcode": error[0],
                    }
                    self.outputData.update(overallResult)

                    # break if any exception encountered during modification operation
                    # in case of validation operation, check all nodes before exiting
                    if operation == "modification":
                        self._mUpdateRequestData(self.outputData)
                        # log footer
                        ebLog("nw_bonding", "INFO", "{}{:->80}".format("\n", "\n"))
                        return

        if operation == "validation" and overallFailure:
            self.outputData["msg"] = "Network bonding validation unsuccessful on one or more nodes. " \
                                     "Please check the report for details."

        if not overallFailure:
            result = {"overallStatus": "SUCCESS", "msg": "", "errorcode": "0x00000000"}
            self.outputData.update(result)
            error = gNetworkError["OPERATION_SUCCESSFUL"]
            self._mGetEbox().mUpdateErrorObject(error, error[1])

        self._mUpdateRequestData(self.outputData)
        # log footer
        ebLog("nw_bonding", "INFO", "{}{:->80}".format("\n", "\n"))


class NetworkBondingUtils(object):
    """
    Base class which acts on the ExaCC dom0 to modify/validate network bonding

    Raises:
        ExacloudRuntimeError: If any operation fails

    Returns:
        json: Saves JSON object in DB for ECRA to read
    """

    BACKUP_PATH = "/opt/exacloud/nw_bonding/"

    def __init__(self, eBox, network, dom0, nodeNetInfo, intfInfoDom0s):
        """
        Init for NetworkBondingUtils. This object corresponds to a specific network of a dom0

        Args:
            eBox: aExaBoxCluCtrl object
            network: (str) Any of ["backup", "client"]
            dom0: dom0 FQDN
            nodeNetInfo: {
                "bonding_mode": {'current': 'active-backup', 'new': 'lacp'},
            }
            intfInfoDom0s :{
                "scaqan17adm01.us.oracle.com": {
                    "client": {
                        "bridge": "vmbondeth0",
                        "bond_master": "bondeth0",
                        "bond_slaves": "eth1 eth2"
                    },
                    "backup": {
                        "bridge": "vmbondeth1",
                        "bond_master": "bondeth1",
                        "bond_slaves": "eth3 eth4"
                    }
                }
                [..]
            }
        Returns: None

        Raises: ExacloudRuntimeError
        """
        self.__ebox = eBox
        self.ctx = self.__ebox.mGetCtx()
        self.dom0 = dom0
        self.message = ""
        self.network = network
        self.interfaceInfo = intfInfoDom0s
        self.payloadResult = nodeNetInfo
        self.currentBonding = nodeNetInfo["bonding_mode"]["current"]
        self.newBonding = nodeNetInfo["bonding_mode"]["new"]

        if self.currentBonding != self.newBonding:
            # Get network info for the dom0 for all network types
            if dom0 not in self.interfaceInfo.keys():
                if network == "dr":
                    self.__ebox.mSetDRNetPresent(True)
                self.interfaceInfo[dom0] = self.__ebox.mGetNetworkSetupInformation("all", dom0)

    def _mGetBackupDir(self):
        """
        Returns path of backup directory.
        Config files will be backed up here for debugging support.

        Returns: str
        """
        return os.path.join(self.BACKUP_PATH, self.mGetUUID())

    def _mGetEbox(self):
        return self.__ebox

    def mGetUUID(self):
        return self._mGetEbox().mGetUUID()

    def _mGetDom0(self):
        return self.dom0

    def _mGetMasterInterface(self):
        """
        Get bonding master interface name

        Returns: (str) bondeth1
        """
        return self.interfaceInfo[self.dom0][self.network]["bond_master"]

    def _mGetBridgeInterface(self):
        """
        Get base bridge interface name for network

        Returns: (str) vmbondeth1
        """
        return self.interfaceInfo[self.dom0][self.network]["bridge"]

    def _mGetSlaveInterfaces(self):
        """
        Get slaves interface list for specific network type

        Returns: (list) ["eth1", "eth2"]
        """
        slaves = self.interfaceInfo[self.dom0][self.network]["bond_slaves"]
        return slaves.split()

    def mSetResult(self, status, message):
        """
        Sets status and msg keys in the return payload

        Args:
            status: (str)
            message: (str)

        Returns: None
        """
        result = {"status": status, "msg": message}
        self.payloadResult.update(result)
        self.mSetResultMessage(message)

    def mSetResultErrorcode(self, errorcode):
        self.errorcode = errorcode

    def mGetResultErrorcode(self):
        return self.errorcode

    def mSetResultMessage(self, msg):
        self.message = msg

    def mGetResultMessage(self):
        return self.message

    def mGetResult(self):
        return self.payloadResult

    def mPerformOp(self):  # pragma: no cover
        """
        Executes specified operation on the dom0
        """
        raise NotImplementedError
    
    def mOnErrorException(self, msg, errorcode):
        ebLog("nw_bonding", "ERROR", msg)
        self.mSetResult("FAILURE", msg)
        raise ExacloudRuntimeError(errorcode, 0xA, msg)

    def mBumpBondedInterface(self, errorcode):
        """
        Bump bonded interface (bondethX) for the particular network
        :return: None
        """
        dom0 = self._mGetDom0()
        bondedInterface = self._mGetMasterInterface()
        with connect_to_host(dom0, self.ctx, "root") as node:
            ebLog("nw_bonding", "INFO", f"Bumping bonded interface for {bondedInterface} network on host {dom0}.")
            _rc, _, _ = self.mExecuteCmd(node, f"ifdown {bondedInterface}")
            if _rc != 0:
                _msg = f"Failed to bring down the interface {bondedInterface} on host {dom0}."
                self.mOnErrorException(_msg, errorcode)
            sleep(5)

            _rc, _, _ = self.mExecuteCmd(node, f"ifup {bondedInterface}")
            if _rc != 0:
                _msg = f"Failed to bring up the interface {bondedInterface} on host {dom0}."
                self.mOnErrorException(_msg, errorcode)
            sleep(5)

    @staticmethod
    def mExecuteCmd(node, cmd):  # pragma: no cover
        """
        Wrapper command for Node.mExecuteCmd() with logging
        """
        _, _out, _err = node.mExecuteCmd(cmd, aTimeout=180)
        _rc = node.mGetCmdExitStatus()
        _out = _out.readlines()
        _err = _err.readlines()
        _msg = f"CMD: {cmd} | RC: {_rc} | OUT: {_out} | ERR: {_err} HOST: {node.mGetHostname()}"
        ebLog("nw_bonding", "INFO", _msg)
        return _rc, _out, _err


class NetworkBondingValidator(NetworkBondingUtils):
    """
    Network Bonding Validator class

    Raises:
        ExacloudRuntimeError: If any operation fails
    """

    def __init__(self, eBox, network, dom0, nodeNetInfo, intfInfoDom0s):
        self.errorcode = "ERROR_BONDING_VALIDATION_FAILED"
        super().__init__(eBox, network, dom0, nodeNetInfo, intfInfoDom0s)

    def mPerformOp(self):
        if self.currentBonding == self.newBonding:
            ebLog("nw_bonding", "INFO", f"Current and new bonding modes are same ({self.newBonding}) "
                                        f"for the {self.network} network. "
                                        f"Skipping validation for {self.network} network bonding on {self.dom0}.")
            self.mSetResult("SUCCESS",
                            "Current and new bonding modes are same. No validation needed.")
        else:
            self.mValidateIntfsUp()
            if self.newBonding == LACP:
                self.mValidateLacp()
            elif self.newBonding == ACTIVE_BACKUP:
                self.mValidateActiveBackup()

    def mValidateIntfsUp(self):
        """
        Validate if the physical interfaces for a network on the host are up
        :return: None
        """
        miiStatus = "MII Status: up"
        bondingConfig = f"/proc/net/bonding/{self._mGetMasterInterface()}"

        with connect_to_host(self.dom0, self.ctx, "root") as node:
            _rc, _out, _ = self.mExecuteCmd(node, f"/bin/grep -B 1 -ie 'MII Status' {bondingConfig}")
            # strip new lines
            output = [line.strip() for line in _out]

            if _rc == 0:
                # count the MII Status: up occurrences
                counts = Counter(output)
                if counts[miiStatus] == 3:
                    ebLog("nw_bonding", "INFO", f"Both physical interfaces up for {self.network} network "
                                                f"on the host {self.dom0}")
                else:
                    ebLog("nw_bonding", "INFO", f"Both physical interfaces not yet up for {self.network} network "
                                                f"on the host {self.dom0}")
                    ebLog("nw_bonding", "DEBUG", f"Current interfaces' state: {output}")

                    _msg = f"Waiting for physical interfaces of {self.network} network to be up " \
                           f"on the host {self.dom0}."
                    self.mOnErrorException(_msg, 0x8009)
            else:
                _msg = f"Failed to check state of physical interface's on {self.dom0}."
                self.mOnErrorException(_msg, 0x8009)

    def mValidateLacp(self):
        """
        Validate if the specific network on the host is configured for LACP bonding
        :return: None
        """
        actorStr = "Actor Churn State: none"
        partnerStr = "Partner Churn State: none"
        monitoringState = False
        churnedState = False
        bondingConfig = f"/proc/net/bonding/{self._mGetMasterInterface()}"

        self.mValidateConfig(LACP)

        with connect_to_host(self.dom0, self.ctx, "root") as node:
            _rc, _out, _ = self.mExecuteCmd(node, f"/bin/grep -ie 'Churn State' {bondingConfig}")
            # strip new lines
            output = [line.strip() for line in _out]

            if _rc == 0:
                # count the Actor and Partner Churn States
                counts = Counter(output)
                if counts[actorStr] == 2 and counts[partnerStr] == 2:
                    ebLog("nw_bonding", "INFO", f"LACP negotiations complete for {self.network} network "
                                                f"on the host {self.dom0}")
                    self.mSetResult("SUCCESS", "Network bonding mode validation successful.")
                else:
                    for line in output:
                        line = line.strip()
                        if 'monitoring' in line:
                            monitoringState = True
                        if 'churned' in line:
                            churnedState = True

                    ebLog("nw_bonding", "INFO", f"LACP negotiations not yet complete for {self.network} network "
                                                f"on the host {self.dom0}")
                    ebLog("nw_bonding", "DEBUG", f"Current LACP bond status: {counts}")

                    _msg = ""
                    if monitoringState:
                        _msg = "LACP bonds currently in negotiation state. Please retry after some time."
                    elif churnedState:
                        # bump the bonded interface in case interfaces have churned
                        self.mBumpBondedInterface(errorcode=0x8009)
                        _msg = f"LACP bonds in churned state. Please check the switch configuration " \
                               f"for {self.network} network ports for {self.dom0} and retry."

                    self.mOnErrorException(_msg, 0x8009)
            else:
                _msg = f"Failed to validate bonding mode on {self.dom0}."
                self.mOnErrorException(_msg, 0x8009)

    def mValidateActiveBackup(self):
        """
        Validate if the specific network on the host is configured for active-backup bonding
        :return: None
        """
        self.mValidateConfig(ACTIVE_BACKUP)

        if self.mCheckInLacpduPackets():
            _msg = f"LACPDU packets seen on one or more interfaces of the {self.network} network on host {self.dom0}. " \
                   f"Please check the switch configuration and try again."
            self.mOnErrorException(_msg, 0x8009)
        else:
            self.mSetResult("SUCCESS", "Network bonding mode validation successful.")

    def mValidateConfig(self, type):
        """
        Function to cross check if bonding config for the specific network is correct

        :return: bool
        """
        bondingModeStr = None
        dom0 = self._mGetDom0()
        bondingConfig = f"/proc/net/bonding/{self._mGetMasterInterface()}"

        if type == LACP:
            bondingModeStr = "802.3ad Dynamic link aggregation"
        elif type == ACTIVE_BACKUP:
            bondingModeStr = ACTIVE_BACKUP

        with connect_to_host(dom0, self.ctx, "root") as node:
            _rc, _, _ = self.mExecuteCmd(node, f"/bin/grep -ie '{bondingModeStr}' {bondingConfig}")
            if _rc != 0:
                _msg = f"Bonding config is incorrect for {self.network} network on {dom0}. " \
                       f"Please check the file {bondingConfig} on the host and retry."
                self.mOnErrorException(_msg, 0x8009)

            ebLog("nw_bonding", "INFO", f"Bonding config checked successfully "
                                        f"for {self.network} network on host {dom0}.")

    def mCheckInLacpduPackets(self):
        dom0 = self._mGetDom0()
        result = False

        with connect_to_host(dom0, self.ctx, "root") as node:
            for interface in self._mGetSlaveInterfaces():
                _rc, _, _ = self.mExecuteCmd(node, f"timeout 35 tcpdump --direction=in "
                                                   f"-nn -xx -i {interface} -s 0 -c 1 ether proto 0x8809 2>/dev/null")
                if _rc == 0:
                    ebLog("nw_bonding", "DEBUG", f"LACPDU packets seen on interface {interface} of the "
                                                 f"{self.network} network on host {dom0}.")
                    result = True

        return result


class NetworkBondingModifier(NetworkBondingUtils):
    """
    Network Bonding Modifier class

    Raises:
        ExacloudRuntimeError: If any operation fails
    """

    def __init__(self, eBox, network, dom0, networkInfo, intfInfoDom0s):
        self.errorcode = "ERROR_BONDING_MODIFICATION_FAILED"
        self.BRIDGE_METADATA = "/etc/exadata/ovm/bridge.conf.d"
        super().__init__(eBox, network, dom0, networkInfo, intfInfoDom0s)

    def mPerformOp(self):

        if self.currentBonding == self.newBonding:
            ebLog("nw_bonding", "INFO", f"Current and new bonding modes are same ({self.newBonding}) "
                                        f"for the {self.network} network. "
                                        f"No changes needed for {self.network} network bonding on {self._mGetDom0()}.")
            self.mSetResult("SUCCESS",
                            "Current and new bonding modes are same. No changes needed.")
        else:
            self.mCreateBackupDir()
            self.mBackupBondingConfig()
            self.mBackupGuestMetadata()
            self.mModifyBondingConfig()
            self.mUpdateBridgeMetadata()
            self.mBringBridgeUp()

            self.mSetResult("SUCCESS",
                            "Network bonding mode change successful.")

    def mCreateBackupDir(self):
        """
        Creates new empty backup directory /opt/exacloud/nw_bonding/<uuid> in dom0

        Raises:
            ExacloudRuntimeError: if directory creation fails
        """

        if not os.path.isdir(self._mGetBackupDir()):
            dom0 = self._mGetDom0()
            ebLog("nw_bonding", "DEBUG", f"Creating backup directory on {dom0}")

            with connect_to_host(dom0, self.ctx, "root") as node:
                _rc, _, _ = self.mExecuteCmd(
                    node, "/bin/mkdir -p {0}".format(self._mGetBackupDir())
                )
                if _rc != 0:
                    _msg = f"Failed to create backup dir {self._mGetBackupDir()} on {dom0}"
                    self.mOnErrorException(_msg, 0x8008)

    def mBackupBondingConfig(self):
        """
        Back up ifcfg-bondethX to backup directory

        Raises: ExacloudRuntimeError if copy command returns non-zero status
        """
        dom0 = self._mGetDom0()
        masterIntf = self._mGetMasterInterface()
        BONDING_CONF = "/etc/sysconfig/network-scripts/ifcfg-{}".format(masterIntf)
        ebLog("nw_bonding", "DEBUG", f"Backing up {BONDING_CONF} on {dom0}")

        with connect_to_host(dom0, self.ctx, "root") as node:
            _cmd = "/bin/cp {0} {1}".format(BONDING_CONF, self._mGetBackupDir())
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Failed to take backup of {BONDING_CONF} on {dom0}"
                self.mOnErrorException(_msg, 0x8008)

    def mBackupGuestMetadata(self):
        """
        Back up guest bridge metadata from bridge.conf.d to backup directory

        Raises: ExacloudRuntimeError if copy command returns non-zero status
        """
        dom0 = self._mGetDom0()
        ebLog("nw_bonding", "DEBUG", f"Backing up {self.network} bridge metadata from {self.BRIDGE_METADATA} on {dom0}")

        with connect_to_host(dom0, self.ctx, "root") as node:
            _cmd = "/bin/cp {0}/*{1}* {2}".format(self.BRIDGE_METADATA,
                                                  self._mGetMasterInterface(), self._mGetBackupDir())
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Failed to take backup of {self.BRIDGE_METADATA} on {dom0}"
                self.mOnErrorException(_msg, 0x8008)

    def mUpdateBridgeMetadata(self):

        def patchBridgeConf(bridgeConf):
            """
            Patches the VM bridge XML with new bonding mode

            Returns:
                (str) Updated XML as string
            """
            root = ET.fromstring(bridgeConf)
            intf = root.find("./Interfaces/[Name='{}']".format(self._mGetMasterInterface()))
            intf.find("Bondeth_mode").text = self.newBonding

            conf = ET.tostring(root)
            conf = "<?xml version='1.0' standalone='yes'?>\n".encode("utf-8") + conf + b'\n'
            return conf

        dom0 = self._mGetDom0()

        ebLog("nw_bonding", "INFO", f"Fetching the list of {self.network} bridge files on dom0 {dom0}")

        # Get all the files for the corresponding network
        with connect_to_host(dom0, self.ctx, "root") as node:
            _cmd = "ls {0}/*{1}*".format(self.BRIDGE_METADATA, self._mGetMasterInterface())
            _rc, _out, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Failed to retrieve {self.network} bridge files on {dom0}"
                self.mOnErrorException(_msg, 0x8008)

        ebLog("nw_bonding", "DEBUG", f"List of files retrieved for {self.network} bridges: {_out}")
        ebLog("nw_bonding", "INFO", f"Updating {self.network} bridge files on dom0 {dom0}")

        try:
            # Update all bridge metadata files corresponding to the network
            with connect_to_host(dom0, self.ctx, "root") as node:
                for conf in _out:
                    # strip newline characters from file path
                    conf = conf.strip()
                    bridgeConf = node.mReadFile(conf)
                    newConf = patchBridgeConf(bridgeConf)
                    node.mWriteFile(conf, newConf, aAppend=False)

        except Exception as e:  # pragma: no cover
            _msg = f"Couldn't update {self.network} bridge metadata files on {dom0}. Exception: {e}"
            self.mOnErrorException(_msg, 0x8008)

    def mModifyBondingConfig(self):
        """
        Updates ifcfg-bondethX with new bonding mode

        Args:
            address: (str) e.g. "0000:ff:00.0"
        """
        BOND_OPS_LACP = 'BONDING_OPTS="mode=802.3ad miimon=100 downdelay=200 updelay=200 lacp_rate=1 xmit_hash_policy=layer3+4"'
        BOND_OPS_ACTIVE_BACKUP = 'BONDING_OPTS="mode=active-backup miimon=100 downdelay=2000 updelay=5000 num_grat_arp=100"'
        bondingFile = f"/etc/sysconfig/network-scripts/ifcfg-{self._mGetMasterInterface()}"

        ebLog("nw_bonding", "DEBUG", "Updating file {}".format(bondingFile))

        try:
            with connect_to_host(self.dom0, self.ctx, "root") as node:
                bondConf = node.mReadFile(bondingFile)
                bondConf = bondConf.split(b"\n")
                for itr, line in enumerate(bondConf):
                    if "BONDING_OPTS" in line.decode():
                        if self.newBonding == LACP:
                            bondConf[itr] = BOND_OPS_LACP.encode()
                        elif self.newBonding == ACTIVE_BACKUP:
                            bondConf[itr] = BOND_OPS_ACTIVE_BACKUP.encode()
                bondConf = b"\n".join(bondConf)
                node.mWriteFile(bondingFile, bondConf)

        except Exception as e:  # pragma: no cover
            _msg = f"Couldn't update {bondingFile} on {self._mGetDom0()}. Exception: {e}"
            self.mOnErrorException(_msg, 0x8008)

    def mBringBridgeUp(self):
        intf = self._mGetMasterInterface()
        bridge = self._mGetBridgeInterface()
        dom0 = self._mGetDom0()
        ebLog("nw_bonding", "INFO", f"Bouncing the interface {intf} on dom0 {dom0}")

        # Bump bonded interface
        self.mBumpBondedInterface(errorcode=0x8008)

        # Bring up VM Bridge
        with connect_to_host(dom0, self.ctx, "root") as node:
            _cmd = "ifup {}".format(bridge)
            _rc, _o, _e = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Failed to bring up the interface {bridge} on {dom0}"
                self.mOnErrorException(_msg, 0x8008)
            sleep(5)
