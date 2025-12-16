#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/clurevertnetworkreconfig.py /main/12 2025/05/21 05:57:34 rkhemcha Exp $
#
# clurevertnetworkreconfig.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      clurevertnetworkreconfig.py - Revert network reconfig operation
#
#    DESCRIPTION
#      ebCluRevertNetworkReconfig: Wrapper class to validate env and revert reconfiguration operations
#      NetworkUpdatePayload: Class to parse and validate payload and
#                            provide methods to iterate and fetch values#
#
#    MODIFIED   (MM/DD/YY)
#    rkhemcha    09/10/24 - 35594111 - Changes for revert DNS/NTP
#                           reconfiguration
#    rkhemcha    02/12/25 - 37581181 - Remove check for num_part_computes to
#                           nodes in network section, for payloads with free
#                           nodes
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
#    pvachhan    04/04/22 - ENH 34030639 - IMPLEMENT NETWORK RECONFIGURATION REVERT API
#    pvachhan    04/04/22 - Creation
#
import os
import copy
from time import sleep
from contextlib import contextmanager

from exabox.log.LogMgr import ebLog
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB
from exabox.core.Error import ExacloudRuntimeError, gNetworkError
from exabox.ovm.hypervisorutils import HVIT_KVM, HVIT_XEN, getTargetHVIType
from exabox.ovm.clunetworkreconfigcommons import (ebCluNetworkReconfigHandler,
                                                  NodeUtils, SUPPORTED_NETWORKS, EXACC_HOSTS)

class ebCluRevertNetworkReconfig(ebCluNetworkReconfigHandler):
    def __init__(self, aExaBoxCluCtrl, aOptions):
        ebCluNetworkReconfigHandler.__init__(self, aExaBoxCluCtrl, aOptions)
        self.mValidateRevertPayload(self.payload)
        self.workingPayload = self.mConsolidateOperations(
            copy.deepcopy(self.payload["updateNetwork"]["nodes"]),
            self.payload["updateNetwork"]["networkServices"],
            copy.deepcopy(self.payload["node_subset"]["participating_computes"])
        )
        ebLog("nw_reconfig", "DEBUG", f"Working payload: {self.workingPayload}")

    def mValidateRevertPayload(self, payload):
        """
            Validates rollback specific entities from revert reconfig payload.
        """
        if not "uuid" in payload:
            _msg = "UUID missing in payload"
            self.mGetEbox().mUpdateErrorObject(gNetworkError["INVALID_INPUT_PARAMETER"], _msg)
            raise ExacloudRuntimeError(0x8001, 0xA, _msg)

        for node in payload["updateNetwork"]["nodes"]:
            for network, nwOps in node.items():
                if network in ["updateProperties"]:
                    continue
                for operation in nwOps:
                    if not "status" in operation or not operation["status"]:
                        _msg = f"Status missing for the operation {operation}"
                        self.mGetEbox().mUpdateErrorObject(
                            gNetworkError["INVALID_INPUT_PARAMETER"], _msg
                        )
                        raise ExacloudRuntimeError(0x8001, 0xA, _msg)

        for operation in payload["updateNetwork"]["networkServices"]:
            if not "status" in operation or not operation["status"]:
                _msg = f"Status missing for the operation {operation}"
                self.mGetEbox().mUpdateErrorObject(
                    gNetworkError["INVALID_INPUT_PARAMETER"], _msg
                )
                raise ExacloudRuntimeError(0x8001, 0xA, _msg)

    def mRevertExaccHosts(self):
        """
        Revert /etc/hosts.exacc_domu from backup dir

        Raises:
            ExacloudRuntimeError: if cp returns non-zero status
        """
        self.mBackupConfCps(EXACC_HOSTS)

        exaccHostsBackup = os.path.join(self.mGetBackupDirCps(), EXACC_HOSTS)
        ebLog(
            "nw_reconfig",
            "DEBUG",
            f"Reverting {exaccHostsBackup} to {EXACC_HOSTS}",
        )
        _rc, _ = NodeUtils.mExecuteCmdLocal(
            "/usr/bin/sudo /bin/cp {0} {1}".format(exaccHostsBackup, EXACC_HOSTS),
            self.masterCps
        )
        if _rc != 0:
            _msg = f"Failed to revert {exaccHostsBackup} on {self.masterCps}"
            ebLog("nw_reconfig", "ERROR", _msg)
            raise ExacloudRuntimeError(0x8007, 0xA, _msg)

    def apply(self):
        """
        Reverts changes done using network reconfiguration
        Sets final reverted/error messages and updates status to db.
        """

        # Exits if overall operation was NOOP
        if self.payload["updateNetwork"].get("status") == "NOOP":
            self.mUpdateRequestData(self.payload)
            return

        if self.mUpdateDnsRecord():
            self.mCreateBackupDirCps()
            # Revert the /etc/hosts.exacc_domu on the CPS
            self.mRevertExaccHosts()

        _eBox = self.mGetEbox()
        revertUUID = self.payload["uuid"]
        self.payload["updateNetwork"]["status"] = "NOOP"
        self.payload["updateNetwork"]["msg"] = ""
        self.mUpdateRequestData(self.payload)

        for computeInfo in self.payload.get("node_subset").get("participating_computes"):
            dom0 = computeInfo["compute_node_hostname"]
            nodeAlias = computeInfo["compute_node_alias"]
            dom0domUpair = self.mGetDom0DomuPairForNode(dom0)
            hypervisor = getTargetHVIType(dom0)
            if hypervisor == HVIT_KVM:
                revertor = KvmNodeRevertor(
                    _eBox, revertUUID, dom0domUpair, self.workingPayload[nodeAlias]
                )
            elif hypervisor == HVIT_XEN:
                revertor = XenNodeRevertor(
                    _eBox, revertUUID, dom0domUpair, self.workingPayload[nodeAlias]
                )
            else:
                _msg = f"Unsupported hypervisor {hypervisor} identified. Exiting."
                ebLog("nw_reconfig", "ERROR", _msg)
                raise ExacloudRuntimeError(0x8005, 0xA, _msg)

            try:
                revertor.mRevertConfiguration()
                self.mSetResultOrgPayload(nodeAlias, revertor.mGetResult())
            except ExacloudRuntimeError as err:
                self.mSetResultOrgPayload(nodeAlias, revertor.mGetResult())

                error = gNetworkError[revertor.mGetResultErrorcode()]
                _eBox.mUpdateErrorObject(error, err.mGetErrorMsg())
                result = {
                    "status": "FAILURE",
                    "msg": err.mGetErrorMsg(),
                    "errorcode": error[0],
                }
                self.payload["updateNetwork"].update(result)
                self.mUpdateRequestData(self.payload)
                self.mPrintLogFooter()
                return

        # Operation successful. Set overall status and save to db.
        result = {"status": "SUCCESS", "msg": "", "errorcode": "0x00000000"}
        self.payload["updateNetwork"].update(result)
        error = gNetworkError["OPERATION_SUCCESSFUL"]
        self.mGetEbox().mUpdateErrorObject(error, error[1])
        self.mUpdateRequestData(self.payload)

        if self.mUpdateDnsRecord():
            # Reload dnsmasq due to revert of /etc/hosts_exacc.domU
            self.ebDNSHandler.mUpdateRemoteNode()
            self.ebDNSHandler.mRestartDnsmasq(self.mGetEbox().mCheckConfigOption("remote_cps_host"))

        self.mPrintLogFooter()


class NodeRevertor(NodeUtils):

    HYPERVISOR = None

    def __init__(self, eBox, revertUUID, dom0domUpair, updates):
        super(NodeRevertor, self).__init__(eBox, dom0domUpair, updates, isRevert=True)
        self.revertUUID = revertUUID

    def mGetRevertUUID(self):
        return self.revertUUID

    def _mGetRevertDir(self):
        """
        Returns path of revert directory.
        XMLs and other config files will be used to replace current ones.

        Returns: str
        """
        return str(os.path.join(self.BACKUP_PATH, self.mGetRevertUUID()))

    def mRevertConfiguration(self):
        if self.operations:
            self.mCreateBackupDir()
            self.mRunRevertConfiguration()
            self.mRunPostOperations()

    def mRunPostOperations(self):
        domU = self.mGetDomU()
        ebLog("nw_reconfig", "DEBUG", f"Starting post operations on {domU}")
        if any("vlan" in op for op in self.operations):
            self.mRestartDomain(self.HYPERVISOR)

        for op in self.operations.keys():
            if "vlan_add" in op:
                network = op.split("_")[-1]
                VLAN_ADD = self.mGetVlanOpKey("add", network)
                if self.operations[op].get("status") not in ["NOOP", "REVERTED"]:
                    self.mDeleteStaleBridge(network)
                    ebLog("nw_reconfig", "INFO", "Marking vlan_add operation as reverted")
                    self.mSetResult(
                        VLAN_ADD,
                        "REVERTED",
                        f"VLAN add operation reverted successfully on {self.mGetDom0()}",
                    )
                else:
                    ebLog("nw_reconfig", "INFO", f"No action required for {op} on {self.mGetDom0()}.")

        if "ipconf_updates" in self.operations:
            if self.operations["ipconf_updates"].get("status") not in ["NOOP", "REVERTED"]:
                self.mRunIpConf()
                self.mSetResult(
                    "ipconf_updates",
                    "REVERTED",
                    f"IP Conf updates reverted successfully on {domU}"
                )
            else:
                ebLog("nw_reconfig", "INFO", f"No action required for ipconf_updates on {self.mGetDomU()}.")


    def mRunRevertConfiguration(self):
        # Operations with status SUCCESS or FAILURE are only reverted.
        # NOOP and REVERTED are ignored. This allows retrying of revert WF.
        if ("ipconf_updates" in self.operations and
            self.operations["ipconf_updates"].get("status") not in ["NOOP", "REVERTED"]):
            self.mRevertCellConf()

        for op, details in self.operations.items():
            if "vlan_add" in op:
                network = op.split("_")[-1]
                VLAN_DELETE = self.mGetVlanOpKey("delete", network)
                if details["status"] in ["NOOP", "REVERTED"]:
                    ebLog(
                        "nw_reconfig",
                        "INFO",
                        f"No action required for VLAN operation(s) for '{network}' network on {self.mGetDom0()}.",
                    )
                    continue

                # identify old VLAN
                old_vlan = None
                if VLAN_DELETE in self.operations:
                    old_vlan = self.operations[VLAN_DELETE].get("payload").get("vlantag")
                self.mRunRevertBridges(network, old_vlan)
                self.mRevertGuestXmls(network, old_vlan)
                self.mRevertPersistentNetRules(network)

                # Mark VLAN delete operation as successful for the network
                if VLAN_DELETE in self.operations:
                    ebLog("nw_reconfig", "INFO", "Marking vlan_delete operation as reverted")
                    self.mSetResult(
                        VLAN_DELETE,
                        "REVERTED",
                        f"VLAN delete operation reverted successfully on {self.mGetDom0()}",
                    )

    def mRevertCellConf(self):
        """
        Backup current cell.conf and copy from revert dir to /opt/oracle.cellos/cell.conf.nw_reconfig

        Raises:
            ExacloudRuntimeError: if cp returns non-zero status
        """
        ebLog("nw_reconfig", "DEBUG", f"Starting to revert cell.conf on {self.mGetDomU()}")
        domU = self.mGetDomU()
        with self.mGetNode("root", domU) as node:
            ebLog("nw_reconfig", "DEBUG", f"Backing up {self.CELLCONF_PATH}")
            _rc, _, _ = self.mExecuteCmd(
                node,
                "/bin/cp {0} {1}".format(self.CELLCONF_PATH, self.mGetBackupDir()),
            )
            if _rc != 0:
                _msg = f"Failed to take backup of {self.CELLCONF_PATH} on {domU}"
                ebLog("nw_reconfig", "ERROR", _msg)
                self.mSetResult("ipconf_updates", "FAILURE", _msg)
                raise ExacloudRuntimeError(0x8007, 0xA, _msg)

            cellConfBackup = os.path.join(self._mGetRevertDir(), "cell.conf")
            ebLog(
                "nw_reconfig",
                "DEBUG",
                f"Reverting {cellConfBackup} to {self.CELLCONF_PATH}.nw_reconfig",
            )
            _rc, _, _ = self.mExecuteCmd(
                node,
                "/bin/cp {0} {1}.nw_reconfig".format(
                    cellConfBackup, self.CELLCONF_PATH
                ),
            )
            if _rc != 0:
                _msg = f"Failed to revert {cellConfBackup} on {domU}"
                ebLog("nw_reconfig", "ERROR", _msg)
                self.mSetResult("ipconf_updates", "FAILURE", _msg)
                raise ExacloudRuntimeError(0x8007, 0xA, _msg)

    def mRevertPersistentNetRules(self, network):
        """
        Backup current 70-persistent-net.rules and replace from revert dir

        Raises:
            ExacloudRuntimeError: if cp return non-zero status
        """
        VLAN_ADD = self.mGetVlanOpKey("add", network)
        VLAN_DELETE = self.mGetVlanOpKey("delete", network)

        def setOpResult(msg):
            if VLAN_ADD in self.operations:
                self.mSetResult(VLAN_ADD, "FAILURE", msg)
            if VLAN_DELETE in self.operations:
                self.mSetResult(VLAN_DELETE, "FAILURE", msg)

        domU = self.mGetDomU()
        ebLog("nw_reconfig", "DEBUG", f"Backing up {self.NETRULES_PATH} on {domU}")
        with self.mGetNode("root", domU) as node:
            _cmd = "/bin/cp {0} {1}".format(self.NETRULES_PATH, self.mGetBackupDir())
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Failed to take backup of {self.NETRULES_PATH} on {domU}"
                ebLog("nw_reconfig", "ERROR", _msg)
                setOpResult(_msg)
                raise ExacloudRuntimeError(0x8007, 0xA, _msg)

            netRulesBackup = os.path.join(
                self._mGetRevertDir(), os.path.basename(self.NETRULES_PATH)
            )
            _cmd = "/bin/cp {0} {1}".format(netRulesBackup, self.NETRULES_PATH)
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Failed to revert {netRulesBackup} to {self.NETRULES_PATH} on {domU}"
                ebLog("nw_reconfig", "ERROR", _msg)
                setOpResult(_msg)
                raise ExacloudRuntimeError(0x8007, 0xA, _msg)

    def mRunRevertBridges(self, network, old_vlantag):
        """
        Try to revert the state of bridges with steps:
        1. Add missing bridge. (Not allocated here.)

        Returns: None
        """
        ebLog("nw_reconfig", "DEBUG", f"Starting to revert Vlan operation on {self.mGetDomU()}")

        if old_vlantag in self.NO_VLAN_LIST:
            ebLog("nw_reconfig", "INFO", "No vlantag found. Skipping add bridge.")
        else:
            self.mAddBondedBridge(network, old_vlantag, self.HYPERVISOR)

    def mDeleteStaleBridge(self, network):
        """
        Remove stale bridge which is added as part of apply and needs revert

        Raises: ExacloudRuntimeError if any command returns non-zero status
        """
        dom0 = self.mGetDom0()
        bridge = self.mGetBondedBridgeName(network, self.mGetNetVlanId(network))
        with self.mGetNode("root", dom0) as node:
            _cmd = "/usr/sbin/brctl show | grep {0}".format(bridge)
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc == 0:
                _msg = f"Bonded bridge {bridge} exists on {dom0}"
                ebLog("nw_reconfig", "INFO", _msg)

                if self.mDetectSharedBridge(bridge, self.HYPERVISOR):
                    ebLog("nw_reconfig", "INFO", f"Skipping remove from bridge {bridge}.")
                    return

                self.mDeleteBondedBridge(network, bridge, self.HYPERVISOR)
            else:
                _msg = f"Bonded bridge {bridge} doesn't exist on {dom0}"
                ebLog("nw_reconfig", "INFO", _msg)

    def mRevertGuestXmls(self, network, old_vlantag):  # pragma: no cover
        raise NotImplementedError


class KvmNodeRevertor(NodeRevertor):
    """
    NodeRevertor for KVM based hypervisor

    Raises:
        ExacloudRuntimeError: If any operation fails
    """

    def __init__(self, eBox, revertUUID, dom0domUpair, updates):
        super(KvmNodeRevertor, self).__init__(eBox, revertUUID, dom0domUpair, updates)
        NodeRevertor.HYPERVISOR = HVIT_KVM
        self.XMLDIR_PATH = "/etc/libvirt/qemu"

    def mRevertGuestXmls(self, network, old_vlantag):
        """
        Replace /etc/libvirt/qemu with data from revert dir.
        Move current bridge xml if existing, copy old bridge xml from revert dir

        Raises: ExacloudRuntimeError if any command returns non-zero status
        """
        dom0 = self.mGetDom0()
        domU = self.mGetDomU()
        VLAN_ADD = self.mGetVlanOpKey("add", network)
        VLAN_DELETE = self.mGetVlanOpKey("delete", network)

        def setOpResult(msg):
            if VLAN_ADD in self.operations:
                self.mSetResult(VLAN_ADD, "FAILURE", msg)
            if VLAN_DELETE in self.operations:
                self.mSetResult(VLAN_DELETE, "FAILURE", msg)

        with self.mGetNode("root", dom0) as node:
            ebLog("nw_reconfig", "DEBUG", f"Backing up {self.XMLDIR_PATH} on {dom0}")
            _cmd = "/bin/cp -r {0} {1}".format(self.XMLDIR_PATH, self.mGetBackupDir())
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Failed to take backup of {self.XMLDIR_PATH} on {dom0}"
                ebLog("nw_reconfig", "ERROR", _msg)
                setOpResult(_msg)
                raise ExacloudRuntimeError(0x8007, 0xA, _msg)

            XmlDirBackup = os.path.join(self._mGetRevertDir(), "qemu")
            ebLog("nw_reconfig", "DEBUG", f"Reverting {XmlDirBackup} on {dom0}")

            _cmd = "/bin/cp -Tfr {0} {1}".format(XmlDirBackup, self.XMLDIR_PATH)
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Failed to revert {XmlDirBackup} on {dom0}"
                ebLog("nw_reconfig", "ERROR", _msg)
                setOpResult(_msg)
                raise ExacloudRuntimeError(0x8007, 0xA, _msg)

            bridgeXmlPath = "/EXAVMIMAGES/GuestImages/{0}/{1}.xml".format(
                domU,
                self.mGetBondedBridgeName(network, self.mGetNetVlanId(network)),
            )

            ebLog(
                "nw_reconfig",
                "DEBUG",
                f"Backup {bridgeXmlPath} to {self.mGetBackupDir()} on {dom0}",
            )
            _cmd = "/usr/bin/test -f {0} && /bin/mv {0} {1}".format(
                bridgeXmlPath, self.mGetBackupDir()
            )
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Failed to copy {bridgeXmlPath} to {self.mGetBackupDir()} on {dom0}"
                ebLog("nw_reconfig", "WARNING", _msg)

            revertBridgeXmlPath = os.path.join(
                self._mGetRevertDir(),
                "{0}.xml".format(
                    self.mGetBondedBridgeName(network, old_vlantag),
                ),
            )
            bridgeXmlPath = "/EXAVMIMAGES/GuestImages/{0}/{1}.xml".format(
                domU,
                self.mGetBondedBridgeName(network, old_vlantag),
            )
            ebLog(
                "nw_reconfig",
                "DEBUG",
                f"Reverting {revertBridgeXmlPath} to {bridgeXmlPath} on {dom0}",
            )
            _cmd = "/bin/cp {0} {1}".format(revertBridgeXmlPath, bridgeXmlPath)
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Failed to revert {revertBridgeXmlPath} to {bridgeXmlPath} on {dom0}"
                ebLog("nw_reconfig", "ERROR", _msg)
                setOpResult(_msg)
                raise ExacloudRuntimeError(0x8007, 0xA, _msg)

            domainXml = f"{self.XMLDIR_PATH}/{domU}.xml"
            ebLog("nw_reconfig", "DEBUG", f"Defining {domainXml} on {dom0}")
            _cmd = "/usr/bin/virsh define {0}".format(domainXml)
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Failed to define {domainXml} on {dom0}"
                ebLog("nw_reconfig", "ERROR", _msg)
                setOpResult(_msg)
                raise ExacloudRuntimeError(0x8007, 0xA, _msg)


class XenNodeRevertor(NodeRevertor):
    """
    NodeRevertor for XEN based hypervisor

    Raises:
        ExacloudRuntimeError: If any operation fails
    """

    def __init__(self, eBox, revertUUID, dom0domUpair, updates):
        super(XenNodeRevertor, self).__init__(eBox, revertUUID, dom0domUpair, updates)
        NodeRevertor.HYPERVISOR = HVIT_XEN

    def mRevertGuestXmls(self, network, old_vlantag):
        """
        Replace vm.cfg from revert dir.

        Raises: ExacloudRuntimeError if any command returns non-zero status
        """
        dom0 = self.mGetDom0()
        domU = self.mGetDomU()
        VLAN_ADD = self.mGetVlanOpKey("add", network)
        VLAN_DELETE = self.mGetVlanOpKey("delete", network)

        XMLDIR_PATH = "/EXAVMIMAGES/GuestImages/{}/vm.cfg".format(domU)
        XmlRevertPath = os.path.join(self._mGetRevertDir(), "vm.cfg")
        ebLog(
            "nw_reconfig",
            "DEBUG",
            f"Reverting {XmlRevertPath} to {XMLDIR_PATH} on {dom0}",
        )

        with self.mGetNode("root", dom0) as node:
            _cmd = "/bin/cp {0} {1}".format(XmlRevertPath, XMLDIR_PATH)
            _rc, _, _ = self.mExecuteCmd(node, _cmd)
            if _rc != 0:
                _msg = f"Failed to revert {XmlRevertPath} to {XMLDIR_PATH} on {dom0}"
                ebLog("nw_reconfig", "ERROR", _msg)
                if VLAN_ADD in self.operations:
                    self.mSetResult(VLAN_ADD, "FAILURE", _msg)
                if VLAN_DELETE in self.operations:
                    self.mSetResult(VLAN_DELETE, "FAILURE", _msg)

                raise ExacloudRuntimeError(0x8007, 0xA, _msg)
