#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/clunetworkreconfig.py /main/12 2025/05/21 05:57:34 rkhemcha Exp $
#
# clunetworkreconfig.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      clunetworkreconfig.py - ExaCC cluster network reconfiguration
#
#    DESCRIPTION
#      ebCluNetworkReconfig: Wrapper class to validate env and apply reconfiguration operations
#      NetworkUpdatePayload: Class to parse and validate payload and
#                            provide methods to iterate and fetch values
#
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    rkhemcha    02/14/25 - 35594100 - Changes for DNS/NTP reconfiguration
#    rkhemcha    02/12/25 - 37581181 - Remove check for num_part_computes to
#                           nodes in network section, for payloads with free
#                           nodes
#    rkhemcha    10/28/24 - 37202048 - Check operstate of bridge before
#                           allocate
#    rkhemcha    09/05/24 - 36805220 - Use node-alias, and mGetNetworkSetupInfo
#                           calls instead of es.properties
#    rkhemcha    07/04/24 - 36805457 - Skip result updation based on nodeId,
#                           since results already upgraded during operation
#    ririgoye    09/01/23 - Bug 35769896 - PROTECT YIELD KEYWORDS WITH
#                           TRY-EXCEPT BLOCKS
#    pvachhan    10/02/22 - BUG 34657901 - EXACC:22.3.1.1:X8M:BACKUP NETWORK
#                           RECONFIGURATION OF AN ALLOCATED NODES FAILS WITH
#                           INDEX OUT OF RANGE ERROR
#    rkhemcha    09/28/22 - 34642088 - add bonding mode while creating bonding
#    pvachhan    06/24/22 - BUG 34316266 - ADD VLAN FAILS TO TAKE BACKUP OF
#                           VMBONDETH4.NULL.XML
#    pvachhan    06/22/22 - ENH 34303483 - EXACLOUD SUPPORT OF BACKUP NW RECONFIG
#                           IN NODE SUBSET SETUP
#    pvachhan    06/06/22 - BUG 34230694 - RECONFIGURING A BACKUP N/W OF A
#                           CLUSTER WITH SHARED BRIDGES FAILS TO DELETE STALE
#                           COMMON BRIDGE
#    rkhemcha    04/23/22 - BUG 34006060 - Add XEN flow for reconfiguration
#    pvachhan    03/28/22 - BUG 33928340 - Cluster network reconfiguration API
#    pvachhan    03/28/22 - Creation
#

import os
import ast
import copy
from time import sleep
from contextlib import contextmanager
import xml.etree.ElementTree as elementTree

from exabox.log.LogMgr import ebLog
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.network.dns.DNSConfig import ebDNSConfig
from exabox.core.Error import ExacloudRuntimeError, gNetworkError
from exabox.ovm.hypervisorutils import getTargetHVIType, HVIT_XEN, HVIT_KVM
from exabox.ovm.clunetworkreconfigcommons import (ebCluNetworkReconfigHandler,
                                                  NodeUtils, SUPPORTED_NETWORKS, EXACC_HOSTS)

class ebCluNetworkReconfig(ebCluNetworkReconfigHandler):

    def __init__(self, aExaBoxCluCtrl, aOptions):
        self.ebDNSHandler = ebDNSConfig(aOptions)
        ebCluNetworkReconfigHandler.__init__(self, aExaBoxCluCtrl, aOptions)
        self.mSetEmptyResult()
        self.workingPayload = self.mConsolidateOperations(
            copy.deepcopy(self.payload["updateNetwork"]["nodes"]),
            self.payload["updateNetwork"]["networkServices"],
            copy.deepcopy(self.payload["node_subset"]["participating_computes"])
        )
        self.mSetEmptyResultWorkingPayload()
        ebLog("nw_reconfig", "DEBUG", f"Working payload: {self.workingPayload}")

    def mSetEmptyResult(self):
        """
        Sets all operation status to "NOOP". Added uuid key to payload.
        Raises: ExacloudRuntimeError if not ociexacc
        """
        self.payload["updateNetwork"]["status"] = "NOOP"
        self.payload["updateNetwork"]["msg"] = ""
        self.payload["uuid"] = self.mGetUUID()
        for node in self.payload["updateNetwork"]["nodes"]:
            for net, operations in node.items():
                if net in ["updateProperties"]:
                    continue
                for operation in operations:
                    operation.update({"status": "NOOP", "msg": ""})

        # Create network service operation copy per participating compute
        serviceOps = copy.deepcopy(self.payload["updateNetwork"]["networkServices"])
        self.payload["updateNetwork"]["networkServices"] = []
        for op in serviceOps:
            for compute in self.payload["node_subset"]["participating_computes"]:
                operation = copy.deepcopy(op)
                operation["payload"]["compute_node_alias"] = compute["compute_node_alias"]
                operation.update({"status": "NOOP", "msg": ""})
                self.payload["updateNetwork"]["networkServices"].append(operation)
        self.mUpdateRequestData(self.payload)

    def mSetEmptyResultWorkingPayload(self):
        """
            Sets all operation status to "NOOP".
            Raises: ExacloudRuntimeError if not ociexacc
        """
        for nodeAlias, operations in self.workingPayload.items():
            for op in operations:
                operations[op].update({"status": "NOOP", "msg": ""})

    def apply(self):
        """
        Applies network reconfiguration
        Sets final success/error messages and updates status to db.
        """

        if self.mUpdateDnsRecord():
            # backup /etc/hosts.exacc_domu on the CPS
            self.mCreateBackupDirCps()
            self.mBackupConfCps(EXACC_HOSTS)

        __eBox = self.mGetEbox()
        for computeInfo in self.payload.get("node_subset").get("participating_computes"):
            dom0 = computeInfo["compute_node_hostname"]
            nodeAlias = computeInfo["compute_node_alias"]
            dom0domUpair = self.mGetDom0DomuPairForNode(dom0)
            hypervisor = getTargetHVIType(dom0)
            if hypervisor == HVIT_KVM:
                nwComposer = KvmNodeNetworkComposer(
                    __eBox, self.ebDNSHandler, dom0domUpair, self.workingPayload[nodeAlias]
                )
            elif hypervisor == HVIT_XEN:
                nwComposer = XenNodeNetworkComposer(
                    __eBox, self.ebDNSHandler, dom0domUpair, self.workingPayload[nodeAlias]
                )
            else:
                _msg = f"Unsupported hypervisor {hypervisor} identified. Exiting."
                ebLog("nw_reconfig", "ERROR", _msg)
                raise ExacloudRuntimeError(0x8005, 0xA, _msg)

            try:
                nwComposer.mReconfigure()

                if self.mUpdateDnsRecord():
                    # Update /etc/hosts.exacc_domu
                    nwComposer.mUpdateExaccHostsDomU()

                self.mSetResultOrgPayload(nodeAlias, nwComposer.mGetResult())
            except ExacloudRuntimeError as err:
                # update the result of operations from working payload to original payload
                self.mSetResultOrgPayload(nodeAlias, nwComposer.mGetResult())

                error = gNetworkError[nwComposer.mGetResultErrorcode()]
                __eBox.mUpdateErrorObject(error, err.mGetErrorMsg())
                result = {
                    "status": "FAILURE",
                    "msg": err.mGetErrorMsg(),
                    "errorcode": error[0],
                }
                self.payload["updateNetwork"].update(result)
                self.mUpdateRequestData(self.payload)
                self.mPrintLogFooter()
                return

        result = {"status": "SUCCESS", "msg": "", "errorcode": "0x00000000"}
        self.payload["updateNetwork"].update(result)
        error = gNetworkError["OPERATION_SUCCESSFUL"]
        self.mGetEbox().mUpdateErrorObject(error, error[1])
        self.mUpdateRequestData(self.payload)

        if self.mUpdateDnsRecord():
            # Rsync and Reload dnsmasq due to changes in /etc/hosts_exacc.domU
            self.ebDNSHandler.mUpdateRemoteNode()
            self.ebDNSHandler.mRestartDnsmasq(self.mGetEbox().mCheckConfigOption("remote_cps_host"))

        self.mPrintLogFooter()


class NodeNetworkComposer(NodeUtils):

    def __init__(self, eBox, ebDNSHandler, dom0domUpair, updates):
        super(NodeNetworkComposer, self).__init__(eBox, dom0domUpair, updates)
        self.ebDNSHandler = ebDNSHandler
        self.HYPERVISOR = None

    def mReconfigure(self):
        """
        Executes all operations defined in self.operations
        """
        if self.operations:
            self._mRunPreOperations()
            self._mRunApplyConfiguration()
            self._mRunPostOperations()
        else:
            ebLog("nw_reconfig", "INFO", f"No updates found for node {self.mGetDom0()}")

    def _mRunPreOperations(self):
        """
        Creates backup directory and runs required pre-operations

        Returns: None
        """
        ebLog("nw_reconfig", "DEBUG", f"Starting pre operations on {self.mGetDomU()}")
        self.mCreateBackupDir()

        if "ipconf_updates" in self.operations:
            self._mBackupConfDomu(self.CELLCONF_PATH)

            if "dns" in self.operations["ipconf_updates"]["entities"]:
                self._mBackupConfDomu(self.DNSCONF_PATH)

            if "ntp" in self.operations["ipconf_updates"]["entities"]:
                self._mBackupConfDomu(self.NTPCONF_PATH)

        if any("vlan" in op for op in self.operations):
            self.mBackupPersistentNetRules()

        for op, details in self.operations.items():
            if "vlan_delete" in op:
                network = op.split("_")[-1]
                self.mBackupGuestXmls(network, details["payload"].get("vlantag"))

    def _mRunApplyConfiguration(self):
        """
        Modifies the configuration files with new values.

        Returns: None
        """
        ebLog(
            "nw_reconfig", "DEBUG", f"Starting apply operations on {self.mGetDomU()}"
        )
        if "ipconf_updates" in self.operations:
            self._mRunApplyIpConfUpdate(self.operations["ipconf_updates"].get("entities"))
        for op, details in self.operations.items():
            if "vlan_add" in op:
                network = op.split("_")[-1]
                self._mRunApplyVlanAdd(network)
            elif "vlan_delete" in op:
                network = op.split("_")[-1]
                self._mRunApplyVlanDelete(network, details["payload"].get("vlantag"))

    def _mRunPostOperations(self):
        """
        New configuration should get reflected after this method is completed

        Returns: None
        """
        ebLog("nw_reconfig", "DEBUG", f"Starting post operations on {self.mGetDomU()}")
        domU = self.mGetDomU()
        if any("vlan" in op for op in self.operations):
            self.mRestartDomain(self.HYPERVISOR)

        for op, details in self.operations.items():
            if "vlan_delete" in op:
                network = op.split("_")[-1]
                self.mDeleteStaleBridge(network, details["payload"].get("vlantag"))

        if "ipconf_updates" in self.operations:
            self.mRunIpConf()
            self.mSetResult(
                "ipconf_updates",
                "SUCCESS",
                f"IP Conf updates operation successful on {domU}"
            )

    def _mRunApplyIpConfUpdate(self, entities):
        """
        Updates cell.conf with new values from XML on domU

        Raises:
            ExacloudRuntimeError: if it cannot read/write cell.conf
        """
        ebLog(
            "nw_reconfig",
            "DEBUG",
            f"Starting IP conf update operations on {self.mGetDomU()}",
        )
        self.mSetResult("ipconf_updates", "FAILURE", "Operation started")

        def patchCellConfNetwork(conf, network):
            """
            Patches the cellConf XML string with new values

            Args:
                conf: (str) current cell.conf
                network: (str)client/backup

            Returns:
                (str) Updated XML as string
            """
            patchedCluConfig = self.mGetCluConfig(network)
            root = elementTree.fromstring(conf)
            intf = root.find(
                "./Interfaces/[Name='{}']".format(self.mGetMasterInterface(network))
            )
            intf.find("IP_address").text = patchedCluConfig.mGetNetIpAddr()
            intf.find("Gateway").text = patchedCluConfig.mGetNetGateWay()
            intf.find("Netmask").text = patchedCluConfig.mGetNetMask()
            intf.find("Hostname").text = (
                    patchedCluConfig.mGetNetNatHostName()
                    + "."
                    + patchedCluConfig.mGetNetNatDomainName()
            )

            return elementTree.tostring(root)

        def patchCellConfServers(conf, serviceTag):
            """
            Patches the cellConf XML string with new values

            Args:
                conf: (str) current cell.conf
                serviceTag: (str)Element tag for appropriate server element

            Returns:
                (str) Updated XML as string
            """

            root = elementTree.fromstring(conf)
            servers = root.findall(f"./{serviceTag}")
            # remove all old entries
            for server in servers:
                root.remove(server)

            newServers = []
            if serviceTag == "Nameservers":
                newServers = self.mGetServers("dns")
            elif serviceTag == "Ntp_servers":
                newServers = self.mGetServers("ntp")

            for ip in newServers:
                entry = elementTree.Element(serviceTag)
                entry.text = ip
                root.append(entry)

            # TODO: Current exacloud python 3.6 does not have indent
            # Uncomment in future once exacloud uses >= python 3.9
            # In its absence cell.conf.nw_reconfig is not pretty printed
            # elementTree.indent(root, space="  ", level=0)
            return elementTree.tostring(root)

        domU = self.mGetDomU()
        try:
            with self.mGetNode("root", domU) as node:
                cellConf = node.mReadFile(self.CELLCONF_PATH)

                for entity in entities:
                    # Patch network entities
                    if entity in SUPPORTED_NETWORKS:
                        cellConf = patchCellConfNetwork(cellConf, entity)
                    # Patch server entities
                    else:
                        if entity == "dns":
                            cellConf = patchCellConfServers(cellConf, "Nameservers")
                        elif entity == "ntp":
                            cellConf = patchCellConfServers(cellConf, "Ntp_servers")

                newCellConf = "<?xml version='1.0' standalone='yes'?>\n".encode("utf-8") + cellConf

                node.mWriteFile(
                    "{}.nw_reconfig".format(self.CELLCONF_PATH),
                    newCellConf,
                    aAppend=False,
                )
        except Exception as e:
            _msg = f"Couldn't update {self.CELLCONF_PATH} on {domU}. Exception: {e}"
            ebLog("nw_reconfig", "ERROR", _msg)
            self.mSetResult("ipconf_updates", "FAILURE", _msg)
            raise ExacloudRuntimeError(0x8006, 0xA, _msg) from e

    def _mBackupConfDomu(self, file):
        """
        Copy cell.conf to backup directory

        Raises:
            ExacloudRuntimeError: if cp return non-zero status
        """
        domU = self.mGetDomU()
        ebLog("nw_reconfig", "DEBUG", f"Backing up {file} on {domU}")
        with self.mGetNode("root", domU) as node:
            _rc, _, _ = self.mExecuteCmd(
                node,
                "/bin/cp {0} {1}".format(file, self.mGetBackupDir()),
            )
            if _rc != 0:
                _msg = f"Failed to take backup of {file} on {domU}"
                ebLog("nw_reconfig", "ERROR", _msg)
                raise ExacloudRuntimeError(0x8006, 0xA, _msg)

    def mBackupPersistentNetRules(self):
        """
        Copy /etc/udev/rules.d/70-persistent-net.rules to backup directory

        Raises:
            ExacloudRuntimeError: if cp return non-zero status
        """
        domU = self.mGetDomU()
        ebLog("nw_reconfig", "DEBUG", f"Backing up {self.NETRULES_PATH} on {domU}")
        with self.mGetNode("root", domU) as node:
            _cmd = "/bin/cp {0} {1}".format(self.NETRULES_PATH, self.mGetBackupDir())
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Failed to take backup of {self.NETRULES_PATH} on {domU}"
                ebLog("nw_reconfig", "ERROR", _msg)
                raise ExacloudRuntimeError(0x8006, 0xA, _msg)

    def mUpdatePersistentRules(self, updatedRule, masterInterface):
        """
        Updates /etc/udev/rules.d/70-persistent-net.rules with new address

        Args:
            :param updatedRule: (str) e.g. updated rule with new kernel address
            :param masterInterface: (str) bondethX
        """
        domU = self.mGetDomU()
        ebLog("nw_reconfig", "DEBUG", "Updating file {} on {}".format(self.NETRULES_PATH, domU))
        with self.mGetNode("root", domU) as node:
            rules = node.mReadFile(self.NETRULES_PATH)
            rules = rules.split(b"\n")
            for itr, rule in enumerate(rules):
                if masterInterface in rule.decode():
                    rules[itr] = updatedRule.encode()
            rules = b"\n".join(rules)
            node.mWriteFile(self.NETRULES_PATH, rules)

    def isBridgeUp(self, bridge):
        """
        Check status of bridge and try to bring up if not already up
        :param bridge: Bonded/VLAN tagged bridge name to be associated to the VM
        :return: Boolean, True if bridge is up, otherwise False
        """
        dom0 = self.mGetDom0()
        with self.mGetNode("root", dom0) as node:
            retryCount = 0
            while retryCount<3:
                retryCount += 1
                ebLog("nw_reconfig", "DEBUG", f"Checking if bridge {bridge} is up on {dom0}")
                _cmd = f"/bin/cat /sys/class/net/{bridge}/operstate"
                _rc, _out, _ = self.mExecuteCmd(node, _cmd)
                if _rc == 0 and 'up' in _out[0].strip():
                    return True
                else:
                    _msg = f"Bridge {bridge} is not yet up on {dom0}, current state: {_out[0].strip()}"
                    ebLog("nw_reconfig", "DEBUG", _msg)
                    ebLog("nw_reconfig", "DEBUG", f"Trying to bring up {bridge} on {dom0}")
                    _cmd = f"/usr/sbin/ifup {bridge}"
                    _rc, _, _ = self.mExecuteCmd(node, _cmd)
                sleep(5)
        return False

    def mEntriesToAddDelete(self):
        entries_to_delete = set()
        entries_to_add = []

        for op, details in self.operations.items():
            # Delete entries for old hostname/ip if available,
            if "vlan_delete" in op:
                entries_to_delete.add(details["payload"]["ip"])
                entries_to_delete.add(details["payload"]["hostname"])
            if "ipconf_updates" in op:
                for network in details["entities"]:
                    if network in SUPPORTED_NETWORKS:
                        # Fetch new hostname and IP address
                        cluConfig = self.mGetCluConfig(network)
                        newHostFqdn = f"{cluConfig.mGetNetHostName()}.{cluConfig.mGetNetDomainName()}"
                        newIp = cluConfig.mGetNetIpAddr()
                        entries_to_add.append((newHostFqdn, newIp))

        return entries_to_add, entries_to_delete

    def mUpdateExaccHostsDomU(self):
        entries_to_add, entries_to_delete  = self.mEntriesToAddDelete()

        # Remove entries marked for removal
        ebLog("nw_reconfig", "INFO", f"Entries to be removed from '{EXACC_HOSTS}': {entries_to_delete}")
        for entry in entries_to_delete:
            _rc, _out, _err = self.ebDNSHandler.mDeleteDNSEntry(aHostname=entry, aHostFile=EXACC_HOSTS)
            if _rc != 0:
                _msg = f"Failed to delete entry for {entry} from {EXACC_HOSTS} on {self.mGetMasterCps()}"
                ebLog("nw_reconfig", "ERROR", _msg)
                raise ExacloudRuntimeError(self.exacloudErrorCode, 0xA, _msg)

        # Add the new entries
        ebLog("nw_reconfig", "INFO", f"Entries to be added to '{EXACC_HOSTS}': {entries_to_add}")
        for entry in entries_to_add:
            _rc, _out, _err = self.ebDNSHandler.mAddServiceEntry(aHostname=entry[0], aAddress=entry[1])
            if _rc != 0:
                _msg = f"Failed to add entry {entry} to {EXACC_HOSTS} on {self.mGetMasterCps()}"
                ebLog("nw_reconfig", "ERROR", _msg)
                raise ExacloudRuntimeError(self.exacloudErrorCode, 0xA, _msg)

    def mDeleteStaleBridge(self, network, old_vlantag):
        """
        Remove stale bridge as part of vlan_delete operation
        :param network: client/backup
        :param old_vlantag: vlantag whose bridge is to be removed
        :return: None
        """
        vlanBridge = self.mGetBondedBridgeName(network, old_vlantag)
        if self.mDetectSharedBridge(vlanBridge, self.HYPERVISOR):
            ebLog("nw_reconfig", "INFO", f"Skipping removal of bridge {vlanBridge}.")
            return

        self.mDeleteBondedBridge(network, vlanBridge, self.HYPERVISOR)

    def _mRunApplyVlanAdd(self, network) -> None:  # pragma: no cover
        raise NotImplementedError

    def _mRunApplyVlanDelete(self, network, old_vlantag):  # pragma: no cover
        raise NotImplementedError

    def mBackupGuestXmls(self, network, old_vlantag):  # pragma: no cover
        raise NotImplementedError

    def getUpdatedBridgeAddress(self, network):  # pragma: no cover
        raise NotImplementedError


class KvmNodeNetworkComposer(NodeNetworkComposer):
    """
    NodeNetworkComposer for KVM based hypervisor

    Raises:
        ExacloudRuntimeError: If any operation fails
    """

    def __init__(self, eBox, ebDNSHandler, dom0domUpair, updates):
        super(KvmNodeNetworkComposer, self).__init__(eBox, ebDNSHandler, dom0domUpair, updates)
        self.HYPERVISOR = HVIT_KVM
        self.XMLDIR_PATH = "/etc/libvirt/qemu"

    def _mRunApplyVlanAdd(self, network) -> None:
        """
        Runs vlan add operation. Subtasks:
        1. Add bonded-bridge if not found.
        2. Allocate bonded-bridge
        3. Get new bridge address and update /etc/udev/rules.d/70-persistent-net.rules

        This method assumes a valid vlan is present in the payload.
        Raises: ExacloudRuntimeError if any command returns non-zero status
        """
        domU = self.mGetDomU()
        dom0 = self.mGetDom0()
        VLAN_ADD = self.mGetVlanOpKey("add", network)
        self.mSetResult(VLAN_ADD, "FAILURE", "Operation started")
        ebLog("nw_reconfig", "DEBUG", f"Starting Vlan Add operation on {dom0}")
        bondedBridge = self.mGetBondedBridgeName(network)
        vlanId = self.mGetNetVlanId(network)

        with self.mGetNode("root", dom0) as node:

            self.mAddBondedBridge(network, vlanId, self.HYPERVISOR)

            if not self.isBridgeUp(f"{bondedBridge}.{vlanId}"):
                _msg = f"Failed to bring up {bondedBridge}.{vlanId} on {dom0}"
                ebLog("nw_reconfig", "ERROR", _msg)
                raise ExacloudRuntimeError(0x8006, 0xA, _msg)

            _cmd = "/opt/exadata_ovm/vm_maker --allocate-bridge {0} --vlan {1} --domain {2}"
            _cmd = _cmd.format(bondedBridge, vlanId, domU)
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Couldn't allocate bridge {bondedBridge}.{vlanId} to domain {domU}"
                ebLog("nw_reconfig", "ERROR", _msg)
                raise ExacloudRuntimeError(0x8006, 0xA, _msg)

        try:
            kernel = self.getUpdatedBridgeAddress(network)
            self._mUpdatePersistentRules(kernel, network)
        except Exception as e:
            _msg = f"Couldn't update rules in {self.NETRULES_PATH} on {domU}"
            ebLog("nw_reconfig", "ERROR", _msg)
            self.mSetResult(VLAN_ADD, "FAILED", _msg)
            raise ExacloudRuntimeError(0x8006, 0xA, _msg) from e

        self.mSetResult(VLAN_ADD, "SUCCESS", f"Vlan Add operation successful on {dom0}")

    def _mRunApplyVlanDelete(self, network, old_vlantag):
        """
        Runs vlan delete operation. Subtasks:
        1. Remove bridge configuration using virt-xml <domain> --network source=<bridge> --remove-device
        2. Remove bridge xml from /EXAVMIMAGES/GuestImages/<domain> (We have backup)

        Raises: ExacloudRuntimeError if any command returns non-zero status
        """
        VLAN_DELETE = self.mGetVlanOpKey("delete", network)
        self.mSetResult(VLAN_DELETE, "FAILURE", "Operation started")
        ebLog(
            "nw_reconfig",
            "DEBUG",
            f"Starting Vlan Delete operation on {self.mGetDomU()}",
        )

        dom0 = self.mGetDom0()
        domU = self.mGetDomU()
        bondedBridge = self.mGetBondedBridgeName(network, old_vlantag)
        _cmd = "/bin/virt-xml {0} --network source={1} --remove-device".format(
            domU, bondedBridge
        )
        with self.mGetNode("root", dom0) as node:
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Failed to update Guest XML for {domU} on {dom0}"
                ebLog("nw_reconfig", "ERROR", _msg)
                self.mSetResult(
                    VLAN_DELETE,
                    "FAILED",
                    f"Failed to update Guest XML for {domU} on {dom0}",
                )
                raise ExacloudRuntimeError(0x8006, 0xA, _msg)

        # Remove bridge XML only if it is vlan tagged bridge
        if old_vlantag:
            bridgeXmlPath = "/EXAVMIMAGES/GuestImages/{0}/{1}.xml".format(
                domU, self.mGetBondedBridgeName(network, old_vlantag)
            )

            with self.mGetNode("root", dom0) as node:
                _cmd = "/bin/rm -f {0}".format(bridgeXmlPath)
                _rc, _, _ = self.mExecuteCmd(node, _cmd)
                if _rc != 0:
                    _msg = f"Failed to remove {bridgeXmlPath} on {dom0}"
                    ebLog("nw_reconfig", "ERROR", _msg)
                    self.mSetResult(
                        VLAN_DELETE,
                        "FAILED",
                        f"Failed to remove {bridgeXmlPath} on {dom0}",
                    )
                    raise ExacloudRuntimeError(0x8006, 0xA, _msg)
        else:
            ebLog(
                "nw_reconfig",
                "INFO",
                "Old vlan is null. Skipping removal of bridge XML.",
            )

        self.mSetResult(
            VLAN_DELETE, "SUCCESS", f"Vlan Delete operation successful on {dom0}"
        )

    def mBackupGuestXmls(self, network, old_vlantag):
        """
        Backup /etc/libvirt/qemu directory and /EXAVMIMAGES/GuestImages/<domain>/vmbondethX.YYY.xml

        Raises: ExacloudRuntimeError if any command returns non-zero status
        """
        dom0 = self.mGetDom0()
        domU = self.mGetDomU()
        ebLog("nw_reconfig", "DEBUG", f"Backing up {self.XMLDIR_PATH} on {dom0}")

        with self.mGetNode("root", dom0) as node:
            _cmd = "/bin/cp -r {0} {1}".format(self.XMLDIR_PATH, self.mGetBackupDir())
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Failed to take backup of {self.XMLDIR_PATH} on {dom0}"
                ebLog("nw_reconfig", "ERROR", _msg)
                raise ExacloudRuntimeError(0x8006, 0xA, _msg)

            bridgeXmlPath = "/EXAVMIMAGES/GuestImages/{0}/{1}.xml".format(
                domU,
                self.mGetBondedBridgeName(network, old_vlantag),
            )
            ebLog("nw_reconfig", "DEBUG", f"Backing up {bridgeXmlPath} on {dom0}")
            _cmd = "/bin/cp {0} {1}".format(bridgeXmlPath, self.mGetBackupDir())
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Failed to take backup of {bridgeXmlPath} on {dom0}"
                ebLog("nw_reconfig", "ERROR", _msg)
                raise ExacloudRuntimeError(0x8006, 0xA, _msg)

    def getUpdatedBridgeAddress(self, network):
        """
        Parses /EXAVMIMAGES/GuestImages/<domain>/vmbondethX.YYY.xml to find new address
        """
        bridgeName = self.mGetBondedBridgeName(
            network, self.mGetNetVlanId(network)
        )
        bridgeXmlPath = "/EXAVMIMAGES/GuestImages/{0}/{1}.xml".format(
            self.mGetDomU(),
            bridgeName,
        )

        with self.mGetNode("root", self.mGetDom0()) as node:
            bridgeIntfXml = node.mReadFile(bridgeXmlPath)
            intf = elementTree.fromstring(bridgeIntfXml)
            kernel = (
                    intf.find("address").get("domain")[2:]
                    + ":"
                    + intf.find("address").get("bus")[2:]
                    + ":"
                    + intf.find("address").get("slot")[2:]
                    + "."
                    + intf.find("address").get("function")[2:]
            )
            return kernel

    def _mUpdatePersistentRules(self, address, network):
        """
        Updates /etc/udev/rules.d/70-persistent-net.rules with new address

        Args:
            :param address: (str) e.g. "0000:ff:00.0"
            :param network: (str) client/backup
        """

        masterInterface = self.mGetMasterInterface(network)
        updatedRule = (
            f'SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", KERNELS=="{address}", '
            f'ATTR{{type}}=="1", NAME="{masterInterface}"'
        )
        self.mUpdatePersistentRules(updatedRule, masterInterface)


class XenNodeNetworkComposer(NodeNetworkComposer):
    """
    NodeNetworkComposer for XEN based hypervisor

    Raises:
        ExacloudRuntimeError: If any operation fails
    """

    def __init__(self, eBox, ebDNSHandler, dom0domUpair, updates):
        super(XenNodeNetworkComposer, self).__init__(eBox, ebDNSHandler, dom0domUpair, updates)
        self.HYPERVISOR = HVIT_XEN
        self.XMLDIR_PATH = "/etc/libvirt/qemu"

    def _mRunApplyVlanAdd(self, network) -> None:
        """
        Runs vlan add operation. Subtasks:
        1. Add bonded-bridge if not found.
        2. Allocate bonded-bridge cmd: /opt/exadata_ovm/exadata.img.domu_maker allocate-bridge-domu vmbondeth1.129 scaqab10client01vm08.us.oracle.com
        3. Get new bridge address and update /etc/udev/rules.d/70-persistent-net.rules

        Raises: ExacloudRuntimeError if any command returns non-zero status
        """
        VLAN_ADD = self.mGetVlanOpKey("add", network)
        self.mSetResult(VLAN_ADD, "FAILURE", "Operation started")
        ebLog(
            "nw_reconfig",
            "DEBUG",
            f"Starting Vlan Add operation for {self.mGetDomU()}",
        )
        domU = self.mGetDomU()
        dom0 = self.mGetDom0()
        vlanId = self.mGetNetVlanId(network)
        bondedBridge = self.mGetBondedBridgeName(network, vlanId)

        with self.mGetNode("root", dom0) as node:

            self.mAddBondedBridge(network, vlanId, self.HYPERVISOR)

            if not self.isBridgeUp(bondedBridge):
                _msg = f"Failed to bring up {bondedBridge} on {dom0}"
                ebLog("nw_reconfig", "ERROR", _msg)
                raise ExacloudRuntimeError(0x8006, 0xA, _msg)

            # /opt/exadata_ovm/exadata.img.domu_maker allocate-bridge-domu vmbondeth1.129 scaqab10client01vm08.us.oracle.com
            _cmd = "{0} allocate-bridge-domu {1} {2}"
            _cmd = _cmd.format(
                self.DOMU_MAKER_PATH,
                bondedBridge,
                domU,
            )
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Couldn't allocate bridge {bondedBridge} to domain {domU}"
                ebLog("nw_reconfig", "ERROR", _msg)
                raise ExacloudRuntimeError(0x8006, 0xA, _msg)

        try:
            newBridgeMac = self.getUpdatedBridgeAddress(network)
            self._mUpdatePersistentRules(newBridgeMac, network)
        except Exception as e:
            _msg = f"Couldn't update rules in {self.NETRULES_PATH} on {domU}"
            ebLog("nw_reconfig", "ERROR", _msg)
            self.mSetResult(VLAN_ADD, "FAILED", _msg)
            raise ExacloudRuntimeError(0x8006, 0xA, _msg) from e

        self.mSetResult(VLAN_ADD, "SUCCESS", f"Vlan Add operation successful on {dom0}")

    def _mRunApplyVlanDelete(self, network, old_vlantag):
        """
        Runs vlan delete operation. Subtasks:
        1. Remove old bridge configuration from vm.cfg

        Raises: ExacloudRuntimeError if read/write to vm.cfg fails
        """
        VLAN_DELETE = self.mGetVlanOpKey("delete", network)
        self.mSetResult(VLAN_DELETE, "FAILURE", "Operation started")
        ebLog(
            "nw_reconfig",
            "DEBUG",
            f"Starting Vlan Delete operation for {self.mGetDomU()}",
        )
        dom0 = self.mGetDom0()
        oldBridgeName = self.mGetBondedBridgeName(network, old_vlantag)
        XMLDIR_PATH = "/EXAVMIMAGES/GuestImages/{}/vm.cfg".format(self.mGetDomU())

        try:
            with self.mGetNode("root", dom0) as node:
                newVmCfgFile = []
                oldVmCfgFile = node.mReadFile(XMLDIR_PATH)
                oldVmCfgFile = oldVmCfgFile.decode("utf-8").split("\n")

                for line in oldVmCfgFile:
                    if "vif" in line:
                        vifOP = line
                        # extract the vif output list, sample O/P
                        # vif = ['type=netfront,mac=<macAddr>,bridge=vmbondeth0.318',
                        #        'type=netfront,mac=<macAddr>,bridge=vmbondeth1.310',
                        #        'type=netfront,mac=<macAddr>,bridge=vmeth103'
                        #       ])
                        oldBridgeList = ast.literal_eval(vifOP[vifOP.find("["):])
                        newBridgeList = []
                        for bridgeInfo in oldBridgeList:
                            if oldBridgeName not in bridgeInfo:
                                newBridgeList.append(bridgeInfo)
                        newVmCfgFile.append(f"vif = {newBridgeList}")
                    else:
                        newVmCfgFile.append(line)

                newVmCfgFile_bytes = bytes("\n".join(newVmCfgFile), "utf-8")
                node.mWriteFile(XMLDIR_PATH, newVmCfgFile_bytes)

                self.mSetResult(
                    VLAN_DELETE, "SUCCESS", "Vlan Delete operation successful"
                )
        except Exception as e:
            _msg = f"Failed to update the file {XMLDIR_PATH} on {dom0}"
            ebLog("nw_reconfig", "ERROR", _msg)
            self.mSetResult(
                VLAN_DELETE,
                "FAILED",
                f"Failed to update the file {XMLDIR_PATH} on {dom0}",
            )
            raise ExacloudRuntimeError(0x8006, 0xA, _msg) from e

    def mBackupGuestXmls(self, network, old_vlantag):
        """
        Back up vm.cfg to backup directory

        Raises: ExacloudRuntimeError if cp command returns non-zero status
        """
        dom0 = self.mGetDom0()
        domU = self.mGetDomU()
        XMLDIR_PATH = "/EXAVMIMAGES/GuestImages/{}/vm.cfg".format(domU)
        ebLog("nw_reconfig", "DEBUG", f"Backing up {XMLDIR_PATH} on {domU}")

        with self.mGetNode("root", dom0) as node:
            _cmd = "/bin/cp {0} {1}".format(XMLDIR_PATH, self.mGetBackupDir())
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Failed to take backup of {XMLDIR_PATH} on {dom0}"
                ebLog("nw_reconfig", "ERROR", _msg)
                raise ExacloudRuntimeError(0x8006, 0xA, _msg)

    def getUpdatedBridgeAddress(self, network):
        """
        Parses vm.cfg to find new bridge address
        Raises: ExacloudRuntimeError if read/parse fails
        """
        XMLDIR_PATH = "/EXAVMIMAGES/GuestImages/{}/vm.cfg".format(self.mGetDomU())
        vlanBridgeName = self.mGetBondedBridgeName(
            network, self.mGetNetVlanId(network)
        )

        with self.mGetNode("root", self.mGetDom0()) as node:
            vmCfgFile = node.mReadFile(XMLDIR_PATH)
            vmCfgFile = vmCfgFile.decode("utf-8").split("\n")

            for line in vmCfgFile:
                if "vif" in line:
                    vifOP = line

            # Extract the vif output list, sample O/P
            # vif = ['type=netfront,mac=<macAddr>,bridge=vmbondeth0.318',
            #        'type=netfront,mac=<macAddr>,bridge=vmbondeth1.310',
            #        'type=netfront,mac=<macAddr>,bridge=vmeth103'
            #       ]
            if vifOP:
                bridgeList = ast.literal_eval(vifOP[vifOP.find("["):])
                for bridgeInfo in bridgeList:
                    if vlanBridgeName in bridgeInfo:
                        for info in bridgeInfo.split(","):
                            if "mac" in info:
                                macAddr = info.split("=")[-1]
                                return macAddr

        _msg = f"Failed to determine the mac address for new bridge {vlanBridgeName} from {XMLDIR_PATH}"
        ebLog("nw_reconfig", "ERROR", _msg)
        raise Exception(_msg)

    def _mUpdatePersistentRules(self, address, network):
        """
        Updates /etc/udev/rules.d/70-persistent-net.rules with new address

        Args:
            :param address: (str) e.g. "0000:ff:00.0"
            :param network: (str) client/backup
        """

        masterInterface = self.mGetMasterInterface(network)
        updatedRule = (
            f'SUBSYSTEM=="net", ACTION=="add", ATTR{{address}}=="{address}", '
            f'KERNEL=="e*", NAME="{masterInterface}"'
        )
        self.mUpdatePersistentRules(updatedRule, masterInterface)
