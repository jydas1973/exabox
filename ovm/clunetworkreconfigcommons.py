#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/clunetworkreconfigcommons.py /main/1 2025/05/21 05:57:34 rkhemcha Exp $
#
# clunetworkreconfigcommons.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      clunetworkreconfigcommons.py - Common classes/methods for reconfig/revert reconfig network flows
#
#    DESCRIPTION
#      Houses common methods needed for clunetworkreconfig.py and clurevertnetworkreconfig.py
#
#    MODIFIED   (MM/DD/YY)
#    rkhemcha    02/14/25 - Creation
#

import os
import copy
import json
import shlex
import subprocess
from time import sleep


from contextlib import contextmanager
from exabox.log.LogMgr import ebLog
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB
from exabox.network.dns.DNSConfig import ebDNSConfig
from exabox.core.Error import ExacloudRuntimeError, gNetworkError
from exabox.ovm.hypervisorutils import HVIT_XEN, HVIT_KVM

SUPPORTED_NETWORKS = ["backup"]
EXACC_HOSTS = "/etc/hosts.exacc_domu"

class ebCluNetworkReconfigHandler(object):

    VALID_OPERATIONS = {
        "cidr_update": [],
        "vlan_add": [],
        "vlan_delete": ["vlantag"],
        "dns_update": [],
        "ntp_update": []
    }
    NO_VLAN_LIST = ["UNDEFINED", "", "1"]

    def __init__(self, aExaBoxCluCtrl, aOptions):
        self.ebox = aExaBoxCluCtrl
        self.payload = aOptions.jsonconf
        self.jsonmode = aOptions.jsonmode
        self.ebDNSHandler = ebDNSConfig(aOptions)

        # Set error code for reconfig v/s revert flow
        self.isRevert = False
        if self.payload.get('uuid'):
            self.isRevert = True
        self.errorCode = 0x8007 if self.isRevert else 0x8006

        self.masterCps = self.mGetEbox().mCheckConfigOption("oeda_host").split('.')[0]
        self.remoteCps = self.mGetEbox().mCheckConfigOption("remote_cps_host").split('.')[0]

        self.mPrintLogHeader()
        self.mValidateEnv()
        self.mValidatePayload(self.payload)

    def mGetEbox(self):
        return self.ebox

    def mGetUUID(self):
        return self.mGetEbox().mGetUUID()

    def mGetMasterCps(self):
        return self.masterCps

    def mGetRemoteCps(self):
        return self.remoteCps

    def mPrintLogHeader(self):
        OP = "REVERT Network Reconfiguration" if self.isRevert \
            else "Network Reconfiguration"
        ebLog(
            "nw_reconfig",
            "INFO",
            "{}{:->80}{}{}{:-<80}".format(
                "\n", "\n", f"Starting {OP}\n", f"Operation UUID - {self.mGetUUID()}", "\n"
            ),
        )

    def mPrintLogFooter(self):
        # log JSON report into the log file
        ebLog("nw_reconfig", "DEBUG", json.dumps(self.payload, indent=4))
        # log footer
        ebLog("nw_reconfig", "INFO", "{}{:->80}".format("\n", "\n"))

    def mGetDom0DomuPairForNode(self, dom0):
        """
        Get dom0,domU pair for a given dom0
        :param dom0:
        :return: (dom0, domU)
        """
        __dom0domUpairs = self.mGetEbox().mReturnDom0DomUPair()
        for pair in __dom0domUpairs:
            if pair[0] == dom0:
                return pair

    def mValidateEnv(self):
        """
        Checks if env is OCI EXACC setup.
        Raises: ExacloudRuntimeError if not ociexacc
        """
        ebox = self.mGetEbox()
        if not ebox.mIsOciEXACC():
            msg = "Detected non-OCIEXACC environment. Network reconfiguration is not supported"
            ebLog("nw_reconfig", "ERROR", msg)
            ebox.mUpdateErrorObject(gNetworkError["INVALID_OPERATION"], msg)
            raise ExacloudRuntimeError(0x8005, 0xA, msg)

    def mValidatePayload(self, payload):
        """
            1. Checks if no of nodes defined in updateNetwork is same as in XML
            2. Checks if operations are valid
            3. Checks if payload for each operation has required keys

        Raises:
            AssertionError: If number of nodes in participating computes is different from updateNetwork payload
            ExacloudRuntimeError: If operation is unknown or payload has missing information
        """
        nodes = payload["updateNetwork"]["nodes"]
        if not (payload.get("node_subset").get("num_participating_computes") ==
                len(payload["updateNetwork"]["nodes"])):
            _msg = "Node count mismatch in updateNetwork section of payload with num_participating_computes"
            self.mGetEbox().mUpdateErrorObject(gNetworkError["INVALID_INPUT_PARAMETER"], _msg)
            raise ExacloudRuntimeError(0x8001, 0xA, _msg)

        for node in nodes:
            for network, nwOps in node.items():
                if network in ["updateProperties"]:
                    continue
                # raise Error if operations identified in unsupported network
                if network not in SUPPORTED_NETWORKS:
                    if nwOps:
                        _msg = f"Changes in unsupported network {network} identified. Exiting."
                        ebLog("nw_reconfig", "ERROR", _msg)
                        raise ExacloudRuntimeError(0x8005, 0xA, _msg)

                for operation in nwOps:
                    opName = operation["op"]
                    opPayload = operation["payload"]

                    if not opName in self.VALID_OPERATIONS.keys():
                        _msg = f"Invalid network reconfiguration operation {opName}"
                        self.mGetEbox().mUpdateErrorObject(gNetworkError["INVALID_RECONFIG_OPERATION"], _msg)
                        raise ExacloudRuntimeError(0x8005, 0xA, _msg)

                    if not set(self.VALID_OPERATIONS[opName]).issubset(opPayload.keys()):
                        _msg = f"Missing data in payload {opPayload} to perform operation {opName}"
                        self.mGetEbox().mUpdateErrorObject(gNetworkError["INVALID_INPUT_PARAMETER"], _msg)
                        raise ExacloudRuntimeError(0x8005, 0xA, _msg)

                    if opPayload.get("vlantag") in self.NO_VLAN_LIST:
                        opPayload["vlantag"] = None

        for networkServiceOp in payload["updateNetwork"]["networkServices"]:
            if not networkServiceOp["op"] in self.VALID_OPERATIONS.keys():
                _msg = f"Invalid network service reconfiguration operation {networkServiceOp['op']}"
                raise ExacloudRuntimeError(0x8005, 0xA, _msg)

    def mUpdateRequestData(self, aData):  # pragma: no cover
        """
        Updates request object with the response payload.
        """
        _reqobj = self.mGetEbox().mGetRequestObj()
        if _reqobj is not None:
            _db = ebGetDefaultDB()
            _reqobj.mSetData(json.dumps(aData, sort_keys=True))
            _db.mUpdateRequest(_reqobj)
        elif self.jsonmode:
            print(json.dumps(aData, indent=4, sort_keys=True))

    def mSetResultOrgPayload(self, nodeAlias, result):
        nodeUpdates = self.payload["updateNetwork"]["nodes"]
        for node in nodeUpdates:
            for net, operations in node.items():
                if net in ["updateProperties"]:
                    continue
                for operation in operations:
                    if operation["payload"]["compute_node_alias"] != nodeAlias:
                        continue

                    op = operation["op"]
                    if op in ["cidr_update"]:
                        operation["status"] = result['ipconf_updates']["status"]
                        operation["msg"] = result['ipconf_updates']["msg"]
                    elif op in ["vlan_add", "vlan_delete"]:
                        operation["status"] = result[f"{op}_{net}"]["status"]
                        operation["msg"] = result[f"{op}_{net}"]["msg"]

        serviceUpdates = self.payload["updateNetwork"]["networkServices"]
        for service in serviceUpdates:
            if service["payload"]["compute_node_alias"] == nodeAlias:
                service["status"] = result['ipconf_updates']["status"]
                service["msg"] = result['ipconf_updates']["msg"]

    def mGetBackupDirCps(self):
        """
        Returns path of backup directory on CPS
        /etc/hosts.exacc_domu will be backed up here for rollback support.

        Returns: str
        """
        return os.path.join(NodeUtils.BACKUP_PATH_CPS, self.mGetUUID())

    def mCreateBackupDirCps(self):
        """
        Creates backup directory on CPS
        /etc/hosts.exacc_domu will be backed up here for rollback support.
        :return: None
        Raises: ExacloudRuntimeError if unable to create backup directory
        """
        cps = self.mGetMasterCps()
        ebLog("nw_reconfig", "DEBUG", f"Creating backup directory on {cps}")
        cmd = f"/bin/mkdir -p {self.mGetBackupDirCps()}"
        _rc, _ = NodeUtils.mExecuteCmdLocal(cmd, cps)
        if _rc != 0:
            _msg = f"Failed to create backup dir {self.mGetBackupDirCps()} on {cps}"
            ebLog("nw_reconfig", "ERROR", _msg)
            raise ExacloudRuntimeError(self.errorCode, 0xA, _msg)

    def mUpdateDnsRecord(self):
        """
        Utility which checks whether hostname/IP is changing for any/(passed) node
        :param alias: compute node alias
        :return: Boolean
        """
        for node in self.payload["updateNetwork"]["nodes"]:
            for key, operations in node.items():
                if key in ["updateProperties"]:
                    for net, entities in operations.items():
                        if any(x in entities for x in ["hostname", "ip"]):
                            return True

        return False

    def mBackupConfCps(self, file):
        """
        Copy 'file' to back-up directory

        Raises:
            ExacloudRuntimeError: if cp returns non-zero status
        """
        cps = self.mGetMasterCps()
        ebLog("nw_reconfig", "DEBUG", f"Backing up {file} on {cps}")

        _rc, _ = NodeUtils.mExecuteCmdLocal(
            "/bin/cp {0} {1}".format(file, self.mGetBackupDirCps()),
            cps
        )
        if _rc != 0:
            _msg = f"Failed to take backup of {file} on {cps}"
            ebLog("nw_reconfig", "ERROR", _msg)
            raise ExacloudRuntimeError(self.errorCode, 0xA, _msg)

    def mConsolidateOperations(self, nodeUpdates, serviceUpdates, computes):
        """
        Modifies the received input payload to consolidate operations per node
        :param serviceUpdates: List of operations on DNS/NTP servers
        :param computes: dom0 and corresponding alias names for participating computes
        :param nodeUpdates: List of updates across nodes
        :return: consolidated dictionary of operations, node wise
        {
            "node-1": {
                "ipconf_updates":{
                   "entities":["backup", "dns", "ntp"],
                   "status":"NOOP",
                   "msg":""
                },
                "vlan_add_backup":{
                   "payload":{..},
                   "status":"NOOP",
                   "msg":""
                },
                "vlan_delete_backup":{
                   "payload":{..},
                   "status":"NOOP",
                   "msg":""
                }
            }
        }
        """
        transformedNodeUpdates = {}
        for compute in computes:
            transformedNodeUpdates[compute["compute_node_alias"]] = {}

        # first update operations on nodes which have some update in client/backup network
        for nodeUpdate in nodeUpdates:
            nodeAlias = None
            for cls, operations in nodeUpdate.items():
                if cls in "updateProperties":
                    continue
                for op in operations:
                    if not nodeAlias:
                        nodeAlias = op.get("payload").get("compute_node_alias")

                    if op["op"] in "cidr_update":
                        if not transformedNodeUpdates[nodeAlias].get("ipconf_updates"):
                            transformedNodeUpdates[nodeAlias]["ipconf_updates"] = {
                                "entities": [cls]
                            } if not self.isRevert else {
                                "entities": [cls],
                                "status": op["status"],
                                "msg": op["msg"]
                            }
                        else:
                            transformedNodeUpdates[nodeAlias]["ipconf_updates"]["entities"].append(cls)
                    else:
                        transformedNodeUpdates[nodeAlias][f"{op['op']}_{cls}"] = {
                            "payload": op.get("payload")
                        } if not self.isRevert else {
                            "payload": op.get("payload"),
                            "status": op["status"],
                            "msg": op["msg"]
                        }

        # check and add operations for network service updates, in all nodes
        for service in serviceUpdates:
            for node, nodeUpdate in transformedNodeUpdates.items():
                serviceKey = service['op'][:3]
                if not nodeUpdate.get("ipconf_updates"):
                    nodeUpdate["ipconf_updates"] = {
                        "entities": [serviceKey]
                    } if not self.isRevert else {
                        "entities": [serviceKey],
                        "status": service["status"],
                        "msg": service["msg"]
                    }
                else:
                    if serviceKey not in nodeUpdate["ipconf_updates"]["entities"]:
                        nodeUpdate["ipconf_updates"]["entities"].append(serviceKey)

        return transformedNodeUpdates

    def apply(self):    # pragma: no cover
        raise NotImplementedError


class NodeUtils(object):
    """
    Base class which acts on the ExaCC host/VM to modify network parameters

    Raises:
        ExacloudRuntimeError: If any operation fails

    Returns:
        json: Saves JSON object in DB for ECRA to read
    """

    # pylint: disable=too-many-instance-attributes
    CELLCONF_PATH = "/opt/oracle.cellos/cell.conf"
    NETRULES_PATH = "/etc/udev/rules.d/70-persistent-net.rules"
    BACKUP_PATH = "/opt/exacloud/nw_reconfig/"
    BACKUP_PATH_CPS = "/opt/oci/exacc/exacloud/scratch/nw_reconfig/"
    NO_VLAN_LIST = ["UNDEFINED", "", "1"]
    DNSCONF_PATH = "/etc/resolv.conf"
    NTPCONF_PATH = "/etc/chrony.conf"
    VMMAKER_PATH = "/opt/exadata_ovm/vm_maker"
    DOMU_MAKER_PATH = "/opt/exadata_ovm/exadata.img.domu_maker"

    def __init__(self, eBox, dom0domUpair, updates, isRevert=False):
        """
        Init for NodeComposer. This object corresponds to a specific network of a dom0domUpair.

        Args:
            eBox: aExaBoxCluCtrl object
            dom0domUpair: (tuple) (dom0, domU)
            updates: (dict) dictionary of operations with payload
            {
                "ipconf_updates":{
                   "entities":[
                      "backup",
                      "dns",
                      "ntp"
                   ],
                   "status":"NOOP",
                   "msg":""
                },
                "vlan_add":{
                   "payload":{…},
                   "status":"NOOP",
                   "msg":""
                }
            }
        Returns: None

        Raises: ExacloudRuntimeError
        """
        self.ebox = eBox
        self.dom0 = dom0domUpair[0]
        self.domU = dom0domUpair[1]
        self.operations = updates
        self.result = updates
        self.isRevert = isRevert
        self.errorcode = "ERROR_RECONFIGURATION_REVERT_FAILED" if isRevert \
            else "ERROR_RECONFIGURATION_FAILED"
        self.exacloudErrorCode = 0x8007 if isRevert \
            else 0x8006

        # Read local and remote CPS names from exabox.conf
        self.masterCps = eBox.mCheckConfigOption("oeda_host").split('.')[0]
        self.remoteCps = eBox.mCheckConfigOption("remote_cps_host").split('.')[0]

        # Fetch network information
        self.interfaceInfo = self.mGetInterfaceInfo()

    def mGetEbox(self):
        return self.ebox

    def mGetDom0(self):
        return self.dom0

    def mGetDomU(self):
        return self.domU

    def mGetMasterCps(self):
        return self.masterCps

    def mGetUUID(self):
        return self.mGetEbox().mGetUUID()

    def mGetVlanOpKey(self, op, network):
        if op == "delete":
            return "vlan_delete_" + network
        elif op == "add":
            return "vlan_add_" + network

    def mGetInterfaceInfo(self):
        """
        Discover interface info from mGetNetworkSetupInformation function

        Returns: (dict) {"bridge": "vmbondeth1", "bond_slaves": "eth3 eth4", "bond_master": "bondeth1"}
        Raises: ExacloudRuntimeError: When cannot find info from function call
        """
        try:
            networkInfo = self.mGetEbox().mGetNetworkSetupInformation("all", self.mGetDom0())
            for network in SUPPORTED_NETWORKS:
                if network not in networkInfo:
                    raise Exception
            return networkInfo
        except Exception:
            _msg = f"Cannot find network info from exacloud for node {self.mGetDom0()}."
            ebLog("nw_reconfig", "ERROR", _msg)
            raise ExacloudRuntimeError(self.exacloudErrorCode, 0xA, _msg)

    def mGetBondedBridgeName(self, network, vlan=None):
        """
        Get bonded bridge name in format vmbondeth<0/1>.<vlan>

        Returns: (str) vmbondeth1.111 or vmbondeth1
        """
        bridge = self.interfaceInfo[network]["bridge"]
        if vlan:
            return f"{bridge}.{vlan}"
        else:
            return bridge

    def mGetBackupDir(self):
        """
        Returns path of backup directory.
        XMLs and other config files will be backed up here for rollback support.

        Returns: str
        """
        return os.path.join(self.BACKUP_PATH, self.mGetUUID())

    def mGetSlaveInterfaces(self, network):
        """
        Returns: (list) ['eth3', 'eth4']
        Raises: ExacloudRuntimeError: If slaves info unavailable
        """
        slaves = self.interfaceInfo[network]["bond_slaves"].split(" ")
        if len(slaves) == 2:
            return slaves

        VLAN_ADD = self.mGetVlanOpKey("add", network)
        VLAN_DELETE = self.mGetVlanOpKey("delete", network)
        _msg = f"Incorrect slave interfaces {slaves} returned from exacloud for {network} network."
        ebLog("nw_reconfig", "ERROR", _msg)
        resultKey = VLAN_DELETE if self.isRevert else VLAN_ADD
        self.mSetResult(resultKey, "FAILED", _msg)
        raise ExacloudRuntimeError(self.exacloudErrorCode, 0xA, _msg)

    def mGetMasterInterface(self, network):
        """
        Get bonding master interface name

        Returns: (str) bondethX
        """
        return self.interfaceInfo[network]["bond_master"]

    def mCreateBackupDir(self):
        """
        Creates new empty backup directory /opt/exacloud/nw_reconfig/<uuid> in dom0 and domU

        Raises:
            ExacloudRuntimeError: if it cannot create the directory
        """
        domu = self.mGetDomU()
        ebLog("nw_reconfig", "DEBUG", f"Creating backup directory on {domu}")
        with self.mGetNode("root", domu) as node:
            _rc, _, _ = self.mExecuteCmd(
                node, "/bin/mkdir -p {0}".format(self.mGetBackupDir())
            )
            if _rc != 0:
                _msg = f"Failed to create backup dir {self.mGetBackupDir()} on {domu}"
                ebLog("nw_reconfig", "ERROR", _msg)
                raise ExacloudRuntimeError(self.exacloudErrorCode, 0xA, _msg)

        dom0 = self.mGetDom0()
        ebLog("nw_reconfig", "DEBUG", f"Creating backup directory on {dom0}")
        with self.mGetNode("root", dom0) as node:
            _rc, _, _ = self.mExecuteCmd(
                node, "/bin/mkdir -p {0}".format(self.mGetBackupDir())
            )
            if _rc != 0:
                _msg = f"Failed to create backup dir {self.mGetBackupDir()} on {dom0}"
                ebLog("nw_reconfig", "ERROR", _msg)
                raise ExacloudRuntimeError(self.exacloudErrorCode, 0xA, _msg)

    def mSetResult(self, operation, status, message):
        """
        Sets status and msg keys for given operation in the return payload

        Args:
            operation: (str)
            status: (str)
            message: (str)

        Returns: None
        """
        result = {"status": status, "msg": message}
        self.result[operation].update(result)

    def mSetResultErrorcode(self, errorcode):
        self.errorcode = errorcode

    def mGetResultErrorcode(self):
        return self.errorcode

    def mGetResult(self):
        return self.result

    def mGetCluConfig(self, network):
        """
        Returns cluconfig for the WIP cluster and network.
        cluconfig helps to retrieve ip, netmask etc. for the cluster from XML

        Returns: ebCluNetworkConfig object
        """
        _eBox = self.mGetEbox()
        vm_machine_config = _eBox.mGetMachines().mGetMachineConfig(self.mGetDomU())
        vm_net_ids = vm_machine_config.mGetMacNetworks()
        networks = _eBox.mGetNetworks()
        vm_nets = (networks.mGetNetworkConfig(nid) for nid in vm_net_ids)
        return {config.mGetNetType(): config for config in vm_nets}.get(network)

    def mGetNetVlanId(self, network):
        """
        Function to return vlantag for the particular network
        :param network:
        :return: (str)/None
        """
        cluConfig = self.mGetCluConfig(network)
        vlanId = cluConfig.mGetNetVlanId()
        if vlanId in self.NO_VLAN_LIST:
            return None
        else:
            return vlanId

    def mGetNetLacp(self, network):
        """
        Function to check if LACP is enabled for the particular network on the node
        :return: bool
        """
        cluConfig = self.mGetCluConfig(network)
        isLacpEnabled = cluConfig.mGetNetLacp()
        return isLacpEnabled

    def mGetServers(self, service):
        """
        Function to return DNS/NTP servers for a given VM
        :return: bool
        """
        _eBox = self.mGetEbox()
        vm_machine_config = _eBox.mGetMachines().mGetMachineConfig(self.mGetDomU())
        if service == "dns":
            return vm_machine_config.mGetDnsServers()
        elif service == "ntp":
            return vm_machine_config.mGetNtpServers()

    def mRunIpConf(self):
        """
        Runs ipconf on domU with new config cell.conf.nw_reconfig filename
        Updates the in case of FAILURE and set errorcode
        /usr/local/bin/ipconf -newconf <new_config_path> -force

        Returns: None
        Raises: ExacloudRuntimeError if command returns non-zero status
        """
        domU = self.mGetDomU()
        new_config_path = "{}.nw_reconfig".format(self.CELLCONF_PATH)
        _cmd = "/usr/local/bin/ipconf -newconf {} -force".format(new_config_path)
        with self.mGetNode("root", domU) as node:
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Failed to run ipconf on {domU}"
                ebLog("nw_reconfig", "ERROR", _msg)
                self.mSetResult("ipconf_updates", "FAILURE", _msg)
                raise ExacloudRuntimeError(self.exacloudErrorCode, 0xA, _msg)

    def mAddBondedBridge(self, network, vlanId, hypervisor):
        """
        Function to add vlan-tagged bridge in the dom0
        :param network: client/backup
        :param vlanId: vlantag for the VM for the particular network
        :param hypervisor: Hypervisor type (KVM/XEN)
        :return:
        """
        dom0 = self.mGetDom0()
        slaves = self.mGetSlaveInterfaces(network)
        baseBridge = self.mGetBondedBridgeName(network)
        vlanBridge = f"{baseBridge}.{vlanId}"
        VLAN_ADD = self.mGetVlanOpKey("add", network)
        VLAN_DELETE = self.mGetVlanOpKey("delete", network)

        add_cmd = None
        if hypervisor == HVIT_KVM:
            if self.mGetNetLacp(network):
                add_cmd = "{0} --add-bonded-bridge {1} --first-slave {2} --second-slave {3} --vlan {4} --bond-mode lacp"
            else:
                add_cmd = "{0} --add-bonded-bridge {1} --first-slave {2} --second-slave {3} --vlan {4}"
            add_cmd = add_cmd.format(
                self.VMMAKER_PATH, baseBridge, slaves[0], slaves[1], vlanId
            )
        elif hypervisor == HVIT_XEN:
            if self.mGetNetLacp(network):
                add_cmd = "{0} add-bonded-bridge-dom0 {1} {2} {3} {4} lacp"
            else:
                add_cmd = "{0} add-bonded-bridge-dom0 {1} {2} {3} {4}"
            add_cmd = add_cmd.format(
                self.DOMU_MAKER_PATH, baseBridge, slaves[0], slaves[1], vlanId,
            )

        with self.mGetNode("root", dom0) as node:
            _cmd = "/usr/sbin/brctl show | grep {0}".format(f"{vlanBridge}")
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Bonded bridge {vlanBridge} doesn't exist on {dom0}. Trying to add"
                ebLog("nw_reconfig", "INFO", _msg)
                _rc, _, _ = self.mExecuteCmd(node, add_cmd)
                if _rc != 0:
                    _msg = f"Couldn't add bonded bridge {vlanBridge} on {dom0}"
                    ebLog("nw_reconfig", "ERROR", _msg)
                    resultKey = VLAN_DELETE if self.isRevert else VLAN_ADD
                    self.mSetResult(resultKey, "FAILED", _msg)
                    raise ExacloudRuntimeError(self.exacloudErrorCode, 0xA, _msg)
            else:
                _msg = f"Bonded bridge {vlanBridge} already existing on {dom0}."
                ebLog("nw_reconfig", "INFO", _msg)

    def mDeleteBondedBridge(self, network, bridge, hypervisor):
        """
        Function to delete vlan-tagged bridge from the dom0
        :param network: client/backup
        :param bridge: vlan-tagged bridge name (vmbondethX.X)
        :param hypervisor: Hypervisor type (KVM/XEN)
        :return:
        """
        dom0 = self.mGetDom0()
        ebLog("nw_reconfig", "INFO", f"Trying to delete bonded bridge {bridge} on {dom0}.")
        VLAN_ADD = self.mGetVlanOpKey("add", network)
        VLAN_DELETE = self.mGetVlanOpKey("delete", network)

        _cmd = None
        if hypervisor == HVIT_KVM:
            _cmd = f"{self.VMMAKER_PATH} --remove-bridge {bridge} --force"
        elif hypervisor == HVIT_XEN:
            _cmd = f"{self.DOMU_MAKER_PATH} remove-bridge-dom0 {bridge} -force"

        with self.mGetNode("root", dom0) as node:
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Couldn't delete bonded bridge {bridge} on {dom0}"
                ebLog("nw_reconfig", "ERROR", _msg)
                resultKey = VLAN_ADD if self.isRevert else VLAN_DELETE
                self.mSetResult(resultKey, "FAILED", _msg)
                self.mSetResultErrorcode("ERROR_STALE_BRIDGE_DELETE_FAILED")
                raise ExacloudRuntimeError(self.exacloudErrorCode, 0xA, _msg)
            else:
                ebLog("nw_reconfig", "DEBUG", f"Removed stale bridge {bridge}")

    def mRestartDomain(self, hypervisor):
        """
        Stop and start domain. Waits for domain to be available for ssh again.
        Retry mechanism to keep trying after few intervals

        Raises:
            ExacloudRuntimeError: if reboot fails.
            Set the corresponding error code and overall message as failure.
        """
        dom0 = self.mGetDom0()
        domU = self.mGetDomU()

        start_cmd, stop_cmd = None, None
        if hypervisor == HVIT_KVM:
            stop_cmd = "{} --stop-domain {}".format(self.VMMAKER_PATH, domU)
            start_cmd = "{} --start-domain {}".format(self.VMMAKER_PATH, domU)
        elif hypervisor == HVIT_XEN:
            XMLDIR_PATH = "/EXAVMIMAGES/GuestImages/{}/vm.cfg".format(domU)
            stop_cmd = "xm shutdown {} -w".format(domU)
            start_cmd = "xm create {}".format(XMLDIR_PATH)

        with self.mGetNode("root", dom0) as node:
            _rc = self.mExecuteCmdAsync(node, stop_cmd)
            if _rc != 0:
                _msg = f"Failed to stop domain {domU} while attempting to restart"
                ebLog("nw_reconfig", "ERROR", _msg)
                self.mSetResultErrorcode("ERROR_REBOOT_FAILED")
                raise ExacloudRuntimeError(0x8002, 0xA, _msg)

        with self.mGetNode("root", dom0) as node:
            _rc = self.mExecuteCmdAsync(node, start_cmd)
            if _rc != 0:
                _msg = f"Failed to start domain {domU} while attempting to restart"
                ebLog("nw_reconfig", "ERROR", _msg)
                self.mSetResultErrorcode("ERROR_REBOOT_FAILED")
                raise ExacloudRuntimeError(0x8002, 0xA, _msg)

        ebLog("nw_reconfig", "INFO", "Waiting for domain to be available.")
        _timeout = 600
        _timeout_decrement = 10
        _wait_timeout = _timeout
        _node = exaBoxNode(get_gcontext())
        _node.mSetUser("root")
        while _wait_timeout > 0:  # pragma: no cover
            sleep(_timeout // 10)
            try:
                _node.mConnect(aHost=domU)
                ebLog(
                    "nw_reconfig",
                    "INFO",
                    "Successfully restarted domain %s" % domU,
                )
                _node.mDisconnect()
                return
            except:
                ebLog(
                    "nw_reconfig",
                    "INFO",
                    "Waiting for host:{0} to be pingable".format(domU),
                )
            _wait_timeout = _wait_timeout - _timeout_decrement

        ebLog(  # pragma: no cover
            "nw_reconfig",
            "ERROR",
            "Host:{0} didn't reboot after {1} seconds.".format(domU, _timeout),
        )
        _msg = f"Failed to connect to domain {self.mGetDomU()} after restart"
        self.mSetResultErrorcode("ERROR_REBOOT_FAILED")
        raise ExacloudRuntimeError(0x8002, 0xA, _msg)

    def mDetectSharedBridge(self, bridge, hypervisor):  # pragma: no cover
        if hypervisor == HVIT_KVM:
            return self.mDetectSharedBridgeKVM(bridge)
        if hypervisor == HVIT_XEN:
            return self.mDetectSharedBridgeXEN(bridge)

    def mDetectSharedBridgeKVM(self, bridge):
        """
        Detect if any other cluster in same rack is sharing same bridge.
        We don't delete the bridge if it is shared.

        Commands:
        1. /usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'
        Lists all VMs irrespective of the state and prints the names.
        2. /usr/bin/virsh domiflist {domU} | /bin/tail -n+3 | /bin/awk '{{print $3}}'
        Print list of all interfaces defined for that domU.

        Returns:
            0: If bridge is not shared by other domains
            1. If bridge is shared by other domains
        Raises: ExacloudRuntimeError if any command returns non-zero status
        """
        dom0 = self.mGetDom0()
        domU = self.mGetDomU()
        _domains = []
        # Get list of all domains in any state
        _cmd = "/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'"
        with self.mGetNode("root", dom0) as node:
            _rc, _out, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Couldn't list all domains on {dom0}"
                ebLog("nw_reconfig", "ERROR", _msg)
                self.mSetResultErrorcode("ERROR_STALE_BRIDGE_DELETE_FAILED")
                raise ExacloudRuntimeError(self.exacloudErrorCode, 0xA, _msg)
            elif _out:
                for _domain in _out:
                    if not _domain.isspace():
                        _domains.append(_domain.strip())

        # Remove current domU from the list
        try:
            _domains.remove(domU)
        except ValueError as e:
            _msg = (f"Couldn't remove domain {domU} from the list. "
                    f"Please check if {domU} exists using 'virsh list --all'.")
            ebLog("nw_reconfig", "ERROR", _msg)
            self.mSetResultErrorcode("ERROR_STALE_BRIDGE_DELETE_FAILED")
            raise ExacloudRuntimeError(self.exacloudErrorCode, 0xA, _msg) from e

        # For remaining domains, check bondedBridge is being used.
        for _domain in _domains:
            _cmd = f"/usr/bin/virsh domiflist {_domain} | /bin/tail -n+3 | /bin/awk '{{print $3}}'"
            with self.mGetNode("root", dom0) as node:
                _rc, _out, _ = self.mExecuteCmd(node, _cmd)
                if _rc != 0:
                    _msg = f"Couldn't list all interfaces for domain {_domain} on {dom0} using 'virsh domiflist'."
                    ebLog("nw_reconfig", "ERROR", _msg)
                    self.mSetResultErrorcode("ERROR_STALE_BRIDGE_DELETE_FAILED")
                    raise ExacloudRuntimeError(self.exacloudErrorCode, 0xA, _msg)
                elif _out:
                    for _intf in _out:
                        if not _intf.isspace() and bridge == _intf.strip():
                            ebLog(
                                "nw_reconfig",
                                "INFO",
                                f"Bridge {bridge} is shared by domain {_domain}",
                            )
                            return 1

        ebLog(
            "nw_reconfig",
            "INFO",
            f"Bridge {bridge} is not shared by other cluster",
        )
        return 0

    def mDetectSharedBridgeXEN(self, bridge):
        """
        Detect if any other cluster in same rack is sharing same bridge.
        We don't delete the bridge if it is shared.

        Actions:
        We try to list all domains using xm list.
        For each domain except the current cluster,
        we print all details with xm list <domain> --long
        and grep for bridge.
        If rc != 0 and no stderr, bridge is not shared.
        If rc != 0 and stderr is present, it can be error in xm command
        If rc == 0, bridge is shared.

        Commands:
        1. xm list | tail -n+3 | awk '{print $1}'
        Lists all VMs irrespective of the state and print the names.
        2. xm list {domU} --long | grep {bridge}
        Print parsed detailed info for given VM and check bridge is present

        Returns:
            0: If bridge is not shared by other domains
            1. If bridge is shared by other domains
        Raises: ExacloudRuntimeError if any command returns non-zero status
        """
        _domains = []
        _cmd = "xm list | tail -n+3 | awk '{print $1}'"
        with self.mGetNode("root", self.mGetDom0()) as node:
            _rc, _out, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Couldn't list all domains on {self.mGetDom0()} to detect shared bridges."
                ebLog("nw_reconfig", "ERROR", _msg)
                self.mSetResultErrorcode("ERROR_STALE_BRIDGE_DELETE_FAILED")
                raise ExacloudRuntimeError(self.exacloudErrorCode, 0xA, _msg)
            elif _out:
                for _domain in _out:
                    if not _domain.isspace():
                        _domains.append(_domain.strip())

        # Remove current domU from xm list output.
        try:
            _domains.remove(self.mGetDomU())
        except ValueError as e:
            _msg = f"Couldn't remove domain {self.mGetDomU()} from the list."
            _msg = _msg + f" Please check if {self.mGetDomU()} exists in xm list."
            ebLog("nw_reconfig", "ERROR", _msg)
            self.mSetResultErrorcode("ERROR_STALE_BRIDGE_DELETE_FAILED")
            raise ExacloudRuntimeError(self.exacloudErrorCode, 0xA, _msg) from e

        # For all domains except the current cluster, check if bridge is in use.
        for _domain in _domains:
            _cmd = f"xm list {_domain} --long | grep {bridge}"
            with self.mGetNode("root", self.mGetDom0()) as node:
                _rc, _out, _err = self.mExecuteCmd(node, _cmd)
                if _rc != 0 and _err:
                    _msg = f"Couldn't list details for domain {_domain} on {self.mGetDom0()}"
                    ebLog("nw_reconfig", "ERROR", _msg)
                    self.mSetResultErrorcode("ERROR_STALE_BRIDGE_DELETE_FAILED")
                    raise ExacloudRuntimeError(self.exacloudErrorCode, 0xA, _msg)
                elif _rc == 0:
                    ebLog(
                        "nw_reconfig",
                        "INFO",
                        f"Bridge {bridge} is shared by domain {_domain}",
                    )
                    return 1

        ebLog(
            "nw_reconfig",
            "INFO",
            f"Bridge {bridge} is not shared by other cluster",
        )
        return 0

    @contextmanager
    def mGetNode(self, user, domU):
        """
        Yields connected node object with can be used with mExecuteCmd()
        Ensures disconnect after block ends

        Args:
            user: (str) username to connect e.g. "root"
            domU: (str) hostname e.g. "scaqan04adm03"

        Returns: exaBoxNode object
        """
        _node = exaBoxNode(get_gcontext())
        _node.mSetUser(user)
        _node.mConnect(aHost=domU)
        try:
            yield _node
        except StopIteration:
            _node.mDisconnect()
            return
        finally:
            _node.mDisconnect()

    @staticmethod
    def mExecuteCmdAsync(node, cmd):  # pragma: no cover
        """
        Wrapper command for Node.mExecuteCmdAsync() with logging
        """
        ebLog("nw_reconfig", "INFO", f"{cmd} on node {node.mGetHostname()}")

        def _read_cb(aData):
            ebLog("nw_reconfig", "INFO", aData)

        def _error_cb(aData):
            ebLog("nw_reconfig", "ERROR", aData)

        def _status_cb(aStatus):
            ebLog(
                "nw_reconfig",
                "INFO",
                f"*** Async command {cmd} status returned: {str(aStatus)}",
            )

        _callbacks = [_read_cb, None, _error_cb, _status_cb]
        node.mExecuteCmdAsync(cmd, _callbacks)
        _rc = node.mGetCmdExitStatus()
        return _rc

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
        ebLog("nw_reconfig", "INFO", _msg)
        return _rc, _out, _err

    @staticmethod
    def mExecuteCmdLocal(aCmd, aHost):  # pragma: no cover
        """ Execute a command in the local (master) CPS """
        try:
            output = subprocess.check_output(shlex.split(aCmd), stderr=subprocess.STDOUT).decode('utf-8')
            _msg = f"CMD: {aCmd} | RC: {0} | OUT: {output} | HOST: {aHost}"
            ebLog("nw_reconfig", "DEBUG", _msg)
            return 0, output
        except subprocess.CalledProcessError as ex:
            _msg = f"CMD: {aCmd} | RC: {ex.returncode} | OUT: {ex.output} | HOST: {aHost}"
            ebLog("nw_reconfig", "DEBUG", _msg)
            return ex.returncode, ex.output
