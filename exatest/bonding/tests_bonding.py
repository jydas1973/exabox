#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/bonding/tests_bonding.py /main/19 2025/12/01 04:43:08 mpedapro Exp $
#
# tests_bonding.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_bonding.py - Unit tests for Bonding modules.
#
#    DESCRIPTION
#      Unit tests for Bonding modules
#       - clubonding.py
#       - clubonding_config.py
#
#    NOTES
#      None.
#
#    MODIFIED   (MM/DD/YY)
#    mpedapro    11/24/25 - Enh::38602758 - Cover code changes of clubonding.py. 
#    kaggupta    09/29/25 - Enh 38335432 - SUPPORT FOR HANDLING THE STACK IDENTIFIER IN ECRA AND CONFIGURING IN KVM HOSTS
#    bhpati      09/15/25 - Bug 38381325 - ERROR FAILED TO CREATE STATIC BONDED
#                           BRIDGE VMBONDETH0.
#    abflores    04/03/25 - Bug 37604161: Fix unnecesary interfaces restart
#    bhpati      02/07/25 - Bug 37520825 - NJA1 | LAUNCHEXADBSYSTEM FAILED |
#                           ERROR FAILED TO CREATE STATIC BONDED BRIDGE
#                           VMBONDETH0
#    akkar       01/22/25 - Bug 37487880 - Make bonding operations in parallel.
#    naps        08/14/24 - Bug 36949876 - X11 ipconf path changes.
#    aararora    07/30/24 - Bug 36440760: Fix the link on the previous active
#                           interface after failover
#    aararora    10/20/22 - Adding unit test for smartNIC_action bonding_action.
#    ffrrodri    10/12/22 - Enh 34686167: Adding unnittesting for methods un
#                           clubonding.py
#    scoral      04/06/22 - Creation
#

import json
import os
import re
from ipaddress import IPv4Interface, IPv4Address
from typing import List, Mapping, Optional, Sequence, Tuple
import unittest
from unittest.mock import patch
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm import clubonding_config
import exabox.ovm.clubonding as clubonding
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.MockCommand import exaMockCommand

from unittest.mock import patch, MagicMock, call
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check)
from exabox.core.Context import get_gcontext
from exabox.ovm.clubonding_config import BondIfaceConf
from exabox.ovm.clubonding_config import (
    Payload
)

CUSTOM_VIPS_CORRECT_PAYLOAD: Payload = {
    "customvip": [
        {
            "interfacetype": "client",
            "ip": "10.0.0.5",
            "standby_vnic_mac": "00:09:A9:78:67"
        },
        {
            "interfacetype": "backup",
            "ip": "10.0.0.6",
            "standby_vnic_mac": "00:09:A9:78:68"
        }
    ]
}

CUSTOM_VIPS_CORRECT_ELASTIC_PAYLOAD: Payload = {
    "customvip": [
        {
            "interfacetype": "client",
            "ip": "10.0.0.7",
            "standby_vnic_mac": "00:09:A9:78:69"
        },
        {
            "interfacetype": "backup",
            "ip": "10.0.0.8",
            "standby_vnic_mac": "00:09:A9:78:6A"
        }
    ]
}

BONDMONITOR_CONFIG_SAMPLE: Payload = {
    "sea201605exddu0101": [
        {
            "type": "scan_ip",
            "ip": "10.0.4.14",
            "interface_type": "client",
            "mac": "00:00:17:01:4C:65",
            "standby_vnic_mac": "00:00:17:01:DC:4A",
            "vlantag": 1,
            "floating": True
        },
        {
            "type": "scan_ip",
            "ip": "10.0.2.94",
            "interface_type": "client",
            "mac": "00:00:17:01:4C:65",
            "standby_vnic_mac": "00:00:17:01:DC:4A",
            "vlantag": 1,
            "floating": True
        },
        {
            "type": "scan_ip",
            "ip": "10.0.13.241",
            "interface_type": "client",
            "mac": "00:00:17:01:4C:65",
            "standby_vnic_mac": "00:00:17:01:DC:4A",
            "vlantag": 1,
            "floating": True
        },
        {
            "type": "host_ip",
            "ip": "10.0.7.65",
            "interface_type": "client",
            "mac": "00:00:17:01:4C:65",
            "standby_vnic_mac": "00:00:17:01:DC:4A",
            "vlantag": 1,
            "floating": False
        },
        {
            "type": "host_ip",
            "ip": "10.0.30.94",
            "interface_type": "backup",
            "mac": "00:00:17:01:56:05",
            "standby_vnic_mac": "00:00:17:01:ED:1F",
            "vlantag": 2,
            "floating": False
        },
        {
            "type": "vip",
            "ip": "10.0.1.248",
            "interface_type": "client",
            "mac": "00:00:17:01:4C:65",
            "standby_vnic_mac": "00:00:17:01:DC:4A",
            "vlantag": 1,
            "floating": True
        }
    ]
}

STDOUT_TEST_STANDBY="""
Calling Test Standby for Bond interface bondeth0
Standby interface for bond bondeth0 are ['eth1']
remove_intf_from_bond(interface=eth1, bond=bondeth0)
ARPING 192.168.0.1 from 11.0.0.64 eth1
Unicast reply from 192.168.0.1 [00:00:17:BB:C9:76] 0.573ms
Unicast reply from 192.168.0.1 [00:00:17:BB:C9:76] 0.566ms
Unicast reply from 192.168.0.1 [00:00:17:BB:C9:76] 0.572ms
Unicast reply from 192.168.0.1 [00:00:17:BB:C9:76] 0.541ms
Unicast reply from 192.168.0.1 [00:00:17:BB:C9:76] 0.536ms
Sent 5 probes (1 broadcast(s))
Received 5 response(s)


arp link test successful for eth1
 Arping output - out: ARPING 192.168.0.1 from 11.0.0.64 eth1
Unicast reply from 192.168.0.1 [00:00:17:BB:C9:76] 0.573ms
Unicast reply from 192.168.0.1 [00:00:17:BB:C9:76] 0.566ms
Unicast reply from 192.168.0.1 [00:00:17:BB:C9:76] 0.572ms
Unicast reply from 192.168.0.1 [00:00:17:BB:C9:76] 0.541ms
Unicast reply from 192.168.0.1 [00:00:17:BB:C9:76] 0.536ms
Sent 5 probes (1 broadcast(s))
Received 5 response(s)
 , err: 
Adding eth1 as standby to bond interface bondeth0
"""

class Node:

    def mExecuteCmd(self, aCmd):
        return 0

    def mGetCmdExitStatus(self):
        return 0

    def mGetHostname(self):
        return "mockHost"

def extract_custom_vips_from_common_and_elastic_payload_tests(
        env: ebTestClucontrol,
        correct_payload: Payload):
    """Custom VIPs parsing from Create Service and Elastic compute payloads.

    :param env: A ebTestClucontrol object.
    :param correct_payload: The Payload that is expected after parsing.
    """
    cluctrl = env.mGetClubox()
    options = cluctrl.mGetArgsOptions()
    payload = options.jsonconf
    custom_vips_payload = {
        "customvip": payload.get("customer_network", {})
        .get("customvip", [])
    }

    env.assertEqual(custom_vips_payload, correct_payload)


TEST_GREP_PATH: exaMockCommand = exaMockCommand('/bin/test -e /bin/grep')
TEST_ECHO_PATH: exaMockCommand = exaMockCommand('/bin/test -e /bin/echo')
TEST_SED_PATH: exaMockCommand = exaMockCommand('/bin/test -e /bin/sed')


def dom0_supports_static_bridge_cmds(
        should_support: bool) -> List[exaMockCommand]:
    """Get the commands that should be run for dom0_supports_static_bridge.

    :param should_support: Whether the Dom0 should support static bridges.
    :returns: List of exaMockCommand.
    """
    cmds = []
    cmds.append(TEST_GREP_PATH)
    cmds.append(exaMockCommand(re.escape(
            f"{clubonding.REMOTE_IPCONF_CMD} -conf-add 2>&1 "
            f"| /bin/grep -q 'Unknown option: conf-add'"
        ), aRc = 1 if should_support else 0))

    return cmds


def is_static_monitoring_bridge_supported_cmds(
        cluctrl: exaBoxCluCtrl,
        payload: Payload,
        should_support_map: Mapping[str, bool]
        ) -> Tuple[bool, Mapping[str, List[List[str]]]]:
    """Get the commands that should be run for is_static_monitoring_bridge_supported.

    :param cluctrl: A clucontrol object.
    :param payload: Exacloud payload dictionary.
    :param should_support_map: Map from Dom0 FQDN to whether static bridges is
                               supported on it.
    :returns: Map of exaMockCommand for each connection of each node.
    """
    bonding_operation = clubonding.get_bonding_operation_from_payload(payload)
    if not bonding_operation:
        return {}

    nodes_bonding_confs = clubonding.extract_bonding_conf_from_payload(
        payload, bonding_operation, extract_monitor_conf=False, scan_ips=())
    if not nodes_bonding_confs:
        return {}

    nodes_cmds = {
        conf.dom0: [
            dom0_supports_static_bridge_cmds(should_support_map[conf.dom0])
        ] for conf in nodes_bonding_confs
    }
    result = all(should_support_map.values())

    return (result, nodes_cmds)


def node_create_bonding_dirs_cmds() -> List[exaMockCommand]:
    """ Get the commands that should be run for node_create_bonding_dirs.

    :returns: List of exaMockCommand.
    """
    return [
        exaMockCommand(f"/bin/mkdir -p {clubonding.REMOTE_BONDING_DIR}"),
        exaMockCommand(f"/bin/mkdir -p {clubonding.REMOTE_BACKUP_DIR}")
    ]

def delete_bonded_bridge_cmds(
        bond_iface_conf: BondIfaceConf,
        is_kvm: bool,
        will_fail: bool) -> List[exaMockCommand]:
    """Get the commands that should be run for delete_bonded_bridge.

    :param bond_iface_conf: net interface bonding configuration.
    :param is_kvm: whether it should a KVM system.
    :param will_fail: Whether we should simulate the function to fail.
    :returns: List of exaMockCommand.
    """
    bond_id = bond_iface_conf.bond_id
    bond_iface = clubonding.BOND_INTERFACE_FMT.format(bond_id)
    bridge_iface = clubonding.BRIDGE_INTERFACE_FMT.format(bond_id)

    cmds = []
    cmds.append(exaMockCommand("/bin/ls /EXAVMIMAGES/GuestImages"))

    stale_bridges = [f"{bridge_iface}.666", f"{bridge_iface}.777"]
    cmds.append(exaMockCommand(
        "/sbin/brctl show", aStdout="\n".join(stale_bridges)))
    if is_kvm:
        remove_bridge_fmt = "/opt/exadata_ovm/vm_maker --remove-bridge {}"
    else:
        remove_bridge_fmt = ("/opt/exadata_ovm/exadata.img.domu_maker "
                             "remove-bridge-dom0 {}")
    for bridge in stale_bridges:
        cmds.append(exaMockCommand(remove_bridge_fmt.format(bridge)))
    
    cmds.append(exaMockCommand(remove_bridge_fmt.format(bridge_iface)))
    cmds.append(exaMockCommand(re.escape(
        f"{clubonding.REMOTE_IPCONF_CMD} -int-delet {bond_iface}")))
    cmds.append(exaMockCommand('/bin/test -e /bin/grep', aRc = 0))
    cmds.append(exaMockCommand(re.escape("/bin/grep eth1 /opt/oracle.cellos/cell.conf")))
    cmds.append(exaMockCommand(re.escape("/bin/grep eth2 /opt/oracle.cellos/cell.conf")))
    cmds.append(exaMockCommand(re.escape(f"{clubonding.REMOTE_IPCONF_CMD} -int-delet eth1")))
    cmds.append(exaMockCommand(re.escape(f"{clubonding.REMOTE_IPCONF_CMD} -int-delet eth2")))
    cmds.append(exaMockCommand(re.escape(
        f"/bin/rm -f {clubonding.IFCFG_DIR}/ifcfg-*bondeth{bond_id}*")))

    cmds.append(exaMockCommand(re.escape(
            f"/bin/test -e {clubonding.BOND_IFCFG_PATH_FMT.format(bond_id)}"
        ), aRc = 1))
    cmds.append(exaMockCommand(re.escape(
            f"/bin/test -e /sys/class/net/{bond_iface}/operstate"
        ), aRc = 1))
    cmds.append(exaMockCommand(re.escape(
            f"/bin/test -e {clubonding.BRIDGE_IFCFG_PATH_FMT.format(bond_id)}"
        ), aRc = 1))
    cmds.append(exaMockCommand(re.escape(
            f"/bin/test -e /sys/class/net/{bridge_iface}/operstate"
        ), aRc = 0 if will_fail else 1))
    cmds.append(exaMockCommand(re.escape(
            f"ls -l {clubonding.BOND_IFCFG_PATH_FMT.format(bond_id)}* "
            f"{clubonding.BRIDGE_IFCFG_PATH_FMT.format(bond_id)}*"
        ), aRc = 1))

    return cmds


def cleanup_bond_bridges_cmds(
        bond_iface_confs: Sequence[BondIfaceConf],
        is_kvm: bool,
        static_bridge: bool,
        delete_will_fail: bool) -> List[exaMockCommand]:
    """Get the commands that should be run for cleanup_bond_bridges.

    :param bond_iface_confs: net interface bonding configurations.
    :param is_kvm: whether it should a KVM system.
    :param static_bridge: Whether we should simulate static bridges deletion.
    :param will_fail: Whether we should simulate the function to fail.
    :returns: List of exaMockCommand.
    """
    cmds = []
    for conf in bond_iface_confs:
        if static_bridge:
            cmds += delete_bonded_bridge_cmds(conf, is_kvm, delete_will_fail)
        else:
            # TODO: Implement patch_bond_bridge_ifcfg commands.
            pass

    return cmds


def save_bonding_config_state_cmds(
        is_cleanup: bool,
        bridge: bool = False,
        monitor_domu: str = "") -> List[exaMockCommand]:
    """Get the commands that should be run for save_bonding_config_state.

    :param is_cleanup: whether state should be update for cleanup operations
                       rather than setup.
    :param bridge: whether change state of monitoring bridge.
    :param monitor_domu: DomU to change monitor state for.
    :returns: List of exaMockCommand.
    """
    cmds = []
    bridge_value = 'bridge_configured'
    monitor_value = f'monitor_configured:{monitor_domu}'
    if is_cleanup:
        cmds.append(exaMockCommand(re.escape(
            f"/bin/test -e {clubonding.REMOTE_BONDING_STATE_FILE}")))
        cmds.append(TEST_SED_PATH)
        if bridge:
            cmds.append(exaMockCommand(re.escape(
                f"/bin/sed -i '/{bridge_value}/d' "
                f"{clubonding.REMOTE_BONDING_STATE_FILE}")))
        if monitor_domu:
            cmds.append(exaMockCommand(re.escape(
                f"/bin/sed -i '/{monitor_value}/d' "
                f"{clubonding.REMOTE_BONDING_STATE_FILE}")))
    else:
        cmds.append(TEST_ECHO_PATH)
        if bridge:
            cmds.append(exaMockCommand(re.escape(
                f'/bin/echo "{bridge_value}" >> '
                f"{clubonding.REMOTE_BONDING_STATE_FILE}")))
        if monitor_domu:
            cmds.append(exaMockCommand(re.escape(
                f'/bin/echo "{monitor_value}" >> '
                f"{clubonding.REMOTE_BONDING_STATE_FILE}")))

    return cmds


def remove_cavium_info_cmds() -> List[exaMockCommand]:
    """Get the commands that should be run for remove_cavium_info.

    :returns: List of exaMockCommand.
    """
    cmds = []
    cmds.append(exaMockCommand(re.escape(
        f"/bin/rm -f {clubonding.REMOTE_MONITOR_CAVIUM_INFO_FILE}")))
    return cmds


def start_bond_monitor_cmds() -> List[exaMockCommand]:
    """Get the commands that should be run for start_bond_monitor.

    :returns: List of exaMockCommand.
    """
    cmds: List[exaMockCommand] = []
    cmds.append(exaMockCommand('/bin/test -e /sbin/initctl', aRc = 1))
    cmds.append(exaMockCommand(
        f"/sbin/service {clubonding.MONITOR_SERVICE} start"))
    return cmds


def stop_bond_monitor_cmds() -> List[exaMockCommand]:
    """Get the commands that should be run for stop_bond_monitor.

    :returns: List of exaMockCommand.
    """
    cmds: List[exaMockCommand] = []
    cmds.append(exaMockCommand('/bin/test -e /sbin/initctl', aRc = 1))
    cmds.append(exaMockCommand(
        f"/sbin/service {clubonding.MONITOR_SERVICE} stop"))
    return cmds


def restart_bond_monitor_cmds() -> List[exaMockCommand]:
    """Get the commands that should be run for restart_bond_monitor.

    :returns: List of exaMockCommand.
    """
    return stop_bond_monitor_cmds() + start_bond_monitor_cmds()


def get_bond_monitor_installed_cmds(ver: str) -> List[exaMockCommand]:
    """Get the commands that should be run for get_bond_monitor_installed.

    :param ver: Version that we should simulate to be installed.
    :returns: List of exaMockCommand.
    """
    return [
        exaMockCommand(f"/bin/rpm -q {clubonding.MONITOR_RPM_PACKAGE_NAME}",
                       aStdout=ver, aRc=0 if ver else 1)
    ]


def install_bond_monitor_rpm_cmds(
        rpm_path: str,
        current_ver: str="",
        domu: Optional[str]=None,
        force_reinstall: bool=True,
        old_file_exists: bool=False,
        new_file_exists: bool=False) -> List[exaMockCommand]:
    """Get the commands that should be run for install_bond_monitor_rpm.

    :param current_ver: Monitor version to simulate to be already installed.
    :param domu: DomU NAT Hostname needed in case we want to migrate the
                 monitor configuration JSON file to the new path.
    :param force_reinstall: Simulate reinstall if already installed.
    :param old_file_exists: Simulate old monitor config file exists.
    :param new_file_exists: Simulate new monitor config file exists.
    :returns: List of exaMockCommand.
    """
    cmds = get_bond_monitor_installed_cmds(current_ver)
    if not force_reinstall:
        return cmds

    old_conf_file = clubonding.REMOTE_MONITOR_CONFIG_FILE_OLD
    if domu:
        cmds.append(exaMockCommand(
            f"/bin/test -e {old_conf_file}",
            aRc=0 if old_file_exists else 1
        ))
    if domu and old_file_exists:
        conf_file = clubonding.REMOTE_MONITOR_CONFIG_FILE_FMT.format(domu)
        cmds.append(exaMockCommand(
            f"/bin/test -e {conf_file}",
            aRc=0 if new_file_exists else 1
        ))
        if new_file_exists:
            cmds.append(exaMockCommand(f"/bin/rm -f {old_conf_file}"))
        else:
            cmds.append(exaMockCommand(f"/bin/mv {old_conf_file} {conf_file}"))

    rpm_basename = os.path.basename(rpm_path)
    remote_rpm_path = os.path.join(clubonding.REMOTE_BONDING_DIR, rpm_basename)
    cmds.append(exaMockCommand(f"/bin/scp {rpm_path} {remote_rpm_path}"))
    cmds.append(exaMockCommand(
        "/bin/rpm -U --nodigest --nofiledigest "
        f"--replacepkgs --oldpackage {remote_rpm_path}"
    ))

    return cmds


def uninstall_bond_monitor_rpm_cmds() -> List[exaMockCommand]:
    """Get the commands that should be run for uninstall_bond_monitor_rpm.

    :returns: List of exaMockCommand.
    """
    return [ exaMockCommand(re.escape(cmd)) for cmd in [
            '/bin/rpm -q bondmonitor',
            '/bin/rpm -e --allmatches bondmonitor',
            '/bin/rm -f /opt/exacloud/bonding/bondmonitor*.x86_64.rpm']]


def configure_custom_vips_cmds(
        cluctrl: exaBoxCluCtrl,
        payload: Payload,
        old_monitor_file: bool
        ) -> Mapping[str, List[List[exaMockCommand]]]:
    """Get the commands that should be run for configure_custom_vips.

    :param cluctrl: A clucontrol object.
    :param payload: Exacloud payload dictionary.
    :old_monitor_file: Simulate whether we should have the bondmonitor config
                       file in the old path.
    """
    nodes_cmds: Mapping[str, List[List[exaMockCommand]]] = {}
    for dom0, domu in cluctrl.mReturnDom0DomUPair():
        domu_net_configs = cluctrl.mGetVMNetConfigs(domu)
        domu = \
            domu_net_configs["client"].mGetNetNatHostName(aFallBack=False)

        node_cmds: List[exaMockCommand] = []
        remote_monitor_config = \
            clubonding.REMOTE_MONITOR_CONFIG_FILE_FMT.format(domu)
        node_cmds.append(exaMockCommand(
            f"/bin/test -e {remote_monitor_config}",
            aRc = int(old_monitor_file)))
        if old_monitor_file:
            remote_monitor_config = clubonding.REMOTE_MONITOR_CONFIG_FILE_OLD

        remote_monitor_config_contents = \
            json.dumps(BONDMONITOR_CONFIG_SAMPLE)
        node_cmds.append(exaMockCommand(
            f"/bin/cat {remote_monitor_config}",
            aStdout=remote_monitor_config_contents))

        node_cmds += restart_bond_monitor_cmds()
        nodes_cmds[dom0] = [node_cmds]

    return nodes_cmds



def cleanup_bonding_if_enabled_cmds(
        cluctrl: exaBoxCluCtrl,
        payload: Payload,
        cleanup_bridge: bool,
        cleanup_monitor: bool,
        static_bridges_nodes_support: Mapping[str, bool],
        will_fail_bridge_deletion: bool
        ) -> Mapping[str, List[List[str]]]:
    """Get the commands that should be run for cleanup_bonding_if_enabled.

    :param cluctrl: A clucontrol object.
    :param payload: Exacloud payload dictionary.
    :param cleanup_bridge: Whether we should simulate bridge deletion.
    :param cleanup_monitor: Whether we should simulate bondmonitor config
                            deletion.
    :param static_bridges_nodes_support: Map from Dom0 FQDN to whether static
                                         bridges is supported on it.
    :param will_fail_bridge_deletion: Whether we should simulate the static 
                                      deletion to fail.
    :returns: Map of exaMockCommand for each connection of each node.
    """
    if not clubonding.is_bonding_supported(cluctrl):
        return {}

    bonding_operation = clubonding.get_bonding_operation_from_payload(payload)
    if bonding_operation is None:
        return {}

    if (cleanup_monitor and
            bonding_operation in (
                clubonding_config.PayloadBondOp.CleanupBridge,
                clubonding_config.PayloadBondOp.SetupBridge)):
        cleanup_monitor = False

    if not (cleanup_bridge or cleanup_monitor):
        return {}

    extract_monitor_conf = cleanup_monitor and \
        bonding_operation != clubonding_config.PayloadBondOp.DeleteService
    nodes_bonding_confs = clubonding.extract_bonding_conf_from_payload(
        payload, bonding_operation, extract_monitor_conf=extract_monitor_conf,
        scan_ips=())

    if not nodes_bonding_confs:
        if not cleanup_monitor:
            return {}
        cleanup_bridge = False
        nodes_bonding_confs = tuple(
            clubonding_config.NodeBondingConf(dom0) for dom0, _ in 
            cluctrl.mReturnDom0DomUPair())

    if cleanup_monitor and not extract_monitor_conf:
        dom0_domu_map = dict(cluctrl.mReturnDom0DomUNATPair())
        nodes_bonding_confs = tuple(
            conf._replace(domu=dom0_domu_map[conf.dom0].split(".")[0])
            for conf in nodes_bonding_confs
            if conf.dom0 in dom0_domu_map
        )

    is_kvm = cluctrl.mIsKVM()
    static_bridge, nodes_cmds = is_static_monitoring_bridge_supported_cmds(
        cluctrl, payload, static_bridges_nodes_support)

    for conf in nodes_bonding_confs:
        node_cmds = []
        if cleanup_monitor:
            # TODO: Implement cleanup_custom_vips_config and
            # cleanup_bond_monitor_config commands.
            pass
        if cleanup_bridge:
            nodes_cmds[conf.dom0][0].extend([exaMockCommand(
                '/bin/test -e /etc/sysconfig/network-scripts/ifcfg-vmeth0')])
            node_cmds += cleanup_bond_bridges_cmds(conf.bond_iface_confs,
                is_kvm, static_bridge, will_fail_bridge_deletion)
            node_cmds += save_bonding_config_state_cmds(True, True)
            node_cmds += remove_cavium_info_cmds()
            node_cmds += uninstall_bond_monitor_rpm_cmds()

            nodes_cmds[conf.dom0].append(node_cmds)

    return nodes_cmds


class ebTestBonding(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestBonding, self).setUpClass()


    def setUp(self):
        ebox = self.mGetClubox()
        ctx = self.mGetContext()

        ebox.mSetExabm(True)
        ctx.mSetConfigOption("activate_oci_bonding", "exabm")


    def copy_file(self, overwrite=False):
        _commands = [
            exaMockCommand("/bin/mkdir*", aRc=0)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]

        with connect_to_host(dom0s[0], get_gcontext()) as dom0Node:
            clubonding.node_copy_file(dom0Node, "/scratch/", "/tmp/", overwrite)

    def node_interface_up(self, state, interface):

        if state == "DOWN":
            command = "/sbin/ifdown*"
        else:
            command = "/sbin/ifup*"

        _commands = [
            exaMockCommand(command, aRc=0)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]

        with connect_to_host(dom0s[0], get_gcontext()) as dom0Node:
            if state == "DOWN":
                clubonding.node_interface_down(dom0Node, interface)
            else:
                clubonding.node_interface_up(dom0Node, interface)

    def create_bonded_bridge(self, is_kvm):

        if is_kvm:
            command = "/opt/exadata_ovm/vm_maker*"
        else:
            command = "/opt/exadata_ovm/exadata.img.domu_maker*"

        _commands = [
            exaMockCommand(command, aRc=0),
            exaMockCommand(command, aRc=0)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]

        with connect_to_host(dom0s[0], get_gcontext()) as dom0Node:
            clubonding.create_bonded_bridge(dom0Node, BondIfaceConf, is_kvm)

    def create_static_bonded_bridge(self, is_kvm):

        bond_id =  BondIfaceConf.bond_id
        _commands = [
            exaMockCommand("/bin/ls /EXAVMIMAGES/GuestImages"),
            exaMockCommand("/sbin/brctl show"),
            exaMockCommand("/bin/rm*"),
            exaMockCommand("/usr/local/bin/ipconf*", aRc=0),
            exaMockCommand("/bin/grep eth1 /opt/oracle.cellos/cell.conf", aRc = 0),
            exaMockCommand("/bin/grep eth2 /opt/oracle.cellos/cell.conf", aRc = 0),
            exaMockCommand(re.escape(f"{clubonding.REMOTE_IPCONF_CMD} -int-delet eth1")),
            exaMockCommand(re.escape(f"{clubonding.REMOTE_IPCONF_CMD} -int-delet eth2")),
            exaMockCommand(re.escape(f"ls -l {clubonding.BOND_IFCFG_PATH_FMT.format(bond_id)}* {clubonding.BRIDGE_IFCFG_PATH_FMT.format(bond_id)}*"), aRc=1),
            exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker*", aRc=0),
            exaMockCommand("/usr/local/bin/ipconf*", aRc=0),
            exaMockCommand("/bin/test*", aRc=1),
            exaMockCommand("/bin/test*", aRc=1),
            exaMockCommand("/bin/test*", aRc=1),
            exaMockCommand("/bin/test*", aRc=1)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]

        with connect_to_host(dom0s[0], get_gcontext()) as dom0Node:
            clubonding.create_static_bonded_bridge(dom0Node, BondIfaceConf, is_kvm)

    def save_bonding_config_state(self, cleanup):
        _commands = [
            exaMockCommand("/bin/sed*", aRc=0),
            exaMockCommand("/bin/sed*", aRc=0),
            exaMockCommand("/bin/sed*", aRc=0),
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/bin/echo*", aRc=0),
            exaMockCommand("/bin/echo*", aRc=0)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]

        with connect_to_host(dom0s[0], get_gcontext()) as dom0Node:
            clubonding.save_bonding_config_state(dom0Node, cleanup, True, "monitor")

    def test_parse_custom_vips_payload(self):
        extract_custom_vips_from_common_and_elastic_payload_tests(
            self,
            CUSTOM_VIPS_CORRECT_PAYLOAD
        )

    def test_copy_no_overwrite(self):
        self.copy_file()

    def test_copy_overwrite(self):
        self.copy_file(True)

    def test_node_interface_up(self):
        self.node_interface_up("UP", "eth0")

    def test_node_interface_down(self):
        self.node_interface_up("DOWN", "eth0")

    def test_create_bonded_bridge_xen(self):
        self.create_bonded_bridge(False)

    def test_create_bonded_bridge_kvm(self):
        self.create_bonded_bridge(True)

    def test_create_static_bonded_bridge_xen(self):
        self.create_static_bonded_bridge(False)

    def test_dom0_has_static_bridge(self):
        _commands = [
            exaMockCommand("/bin/grep*", aRc=0),
            exaMockCommand("/bin/grep*", aRc=0)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]

        with connect_to_host(dom0s[0], get_gcontext()) as dom0Node:
            clubonding.dom0_has_static_bridge(dom0Node)

    def test_dom0_supports_static_bridge(self):

        should_support = True
        _cmds = {
            self.mGetRegexDom0(): [
                dom0_supports_static_bridge_cmds(should_support)
            ]
        }

        self.mPrepareMockCommands(_cmds)

        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]

        with connect_to_host(dom0s[0], get_gcontext()) as dom0Node:
            res = clubonding.dom0_supports_static_bridge(dom0Node)
            self.assertEqual(res, should_support)

    def test_is_static_monitoring_bridge_supported(self):

        ebox = self.mGetClubox()
        payload = self.mGetPayload()

        bonding_operation = \
            clubonding.get_bonding_operation_from_payload(payload)
        self.assertEqual(bonding_operation,
            clubonding_config.PayloadBondOp.CreateService)

        nodes_bonding_confs = clubonding.extract_bonding_conf_from_payload(
            payload, bonding_operation, extract_monitor_conf=False,
            scan_ips=())
        should_support_map = {
            conf.dom0: False for conf in nodes_bonding_confs
        }

        expected_result, cmds = is_static_monitoring_bridge_supported_cmds(
            ebox, payload, should_support_map)

        self.mPrepareMockCommands(cmds)
        result = \
            clubonding.is_static_monitoring_bridge_supported(ebox, payload)
        self.assertEqual(result, expected_result)


    def test_get_node_nics(self):
        _commands = [
            exaMockCommand("/sbin/ip*", aRc=0),
            exaMockCommand("/sbin/ip*", aRc=0)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]

        with connect_to_host(dom0s[0], get_gcontext()) as dom0Node:
            clubonding.get_node_nics(dom0Node)

    def test_node_create_bonding_dirs(self):
        _cmds = {
            self.mGetRegexDom0(): [
                node_create_bonding_dirs_cmds()
            ]
        }

        self.mPrepareMockCommands(_cmds)

        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]

        with connect_to_host(dom0s[0], get_gcontext()) as dom0Node:
            clubonding.node_create_bonding_dirs(dom0Node)

    def test_save_bonding_config_state_cleanup(self):
        self.save_bonding_config_state(True)

    def test_save_bonding_config_state(self):
        self.save_bonding_config_state(False)

    def config_custom_vips_tests(self, old_monitor_file):
        ebox = self.mGetClubox()
        payload = self.mGetPayload()
        ctx = self.mGetContext()

        payload['customvip'] = CUSTOM_VIPS_CORRECT_PAYLOAD['customvip']

        cmds = configure_custom_vips_cmds(ebox, payload, old_monitor_file)
        self.mPrepareMockCommands(cmds)
        clubonding.configure_custom_vips(ebox, payload)

    def test_config_custom_vips_old_config(self):
        self.config_custom_vips_tests(True)

    def test_config_custom_vips_new_config(self):
        self.config_custom_vips_tests(False)

    def test_read_bond_interface_atr(self):
        test_bond_vals = {
            "MTU": "9000",
            "mode": "active-backup",
            "fail_over_mac": "1",
            "num_grat_arp": "8",
            "arp_interval": "1000",
            "primary_reselect": "failure",
            "arp_allslaves": "1",
        }
        test_interface = "bondeth0"
        
        _cmds = self.mock_bonding_values(test_bond_vals, test_interface)
        self.mPrepareMockCommands(_cmds)
        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():
            with connect_to_host(_dom0, get_gcontext()) as _node:
                for key, bondValue in test_bond_vals.items():
                    self.assertEqual(bondValue, clubonding.read_bond_interface_atr(_node, test_interface, key))
    
    def test_validate_different_bond_values(self):
        test_bond_vals = {
            "MTU": "9000",
            "mode": "active-backup",
            "fail_over_mac": "active 1",
            "num_grat_arp": "8",
            "arp_interval": "1000",
            "primary_reselect": "failure",
            "arp_allslaves": "active 1",
        }
        test_interface = "bondeth0"
        
        _cmds = self.mock_bonding_values(test_bond_vals, test_interface)
        self.mPrepareMockCommands(_cmds)

        #Change expected value
        test_bond_vals["arp_interval"] = "9000"
        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():
            with connect_to_host(_dom0, get_gcontext()) as _node:
                validActualConfig = clubonding.validate_bonding_config(_node, test_interface, test_bond_vals)
                self.assertEqual(False, validActualConfig)

    def test_read_bridge_values(self):
        ip_test = IPv4Interface("192.168.0.0/28")
        bridge_key_test_vals = {
            "MTU": "9000",
            "IPADDR": str(ip_test.ip),
            "NETMASK": str(ip_test.netmask),
            "ARPCHECK": "no"
        }

        test_interface = "vmbondeth0"
        
        _cmds = self.mock_bridge_values(bridge_key_test_vals, test_interface, ip_test)
        self.mPrepareMockCommands(_cmds)
        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():
            with connect_to_host(_dom0, get_gcontext()) as _node:
                valuesFound = clubonding.read_bridge_interface_attrs(_node, test_interface)
                for key, valueFound in valuesFound.items():
                    self.assertEqual(bridge_key_test_vals[key], str(valueFound))

    def test_validate_different_bridge_values(self):
        ip_test = IPv4Interface("192.168.0.0/28")
        bridge_key_test_vals = {
            "MTU": "9000",
            "IPADDR": str(ip_test.ip),
            "NETMASK": str(ip_test.netmask),
            "ARPCHECK": "no"
        }

        test_interface = "vmbondeth0"
        
        _cmds = self.mock_bridge_values(bridge_key_test_vals, test_interface, ip_test)
        self.mPrepareMockCommands(_cmds)

        #Change expected value
        bridge_key_test_vals["ARPCHECK"] = "yes"

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():
            with connect_to_host(_dom0, get_gcontext()) as _node:
                validActualConfig = clubonding.validate_bridge_config(_node, test_interface, bridge_key_test_vals)
                self.assertEqual(False, validActualConfig)

    def mock_bridge_values(self, test_bridge_vals, test_interface, ip_test):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/bin/test -e /sbin/ip", aRc=0, aPersist=True, aStdout="1"),
                    exaMockCommand(f"/bin/test -e /bin/awk", aRc=0, aPersist=True, aStdout="1"),
                    exaMockCommand(f"/sbin/ip -o -4 addr show {test_interface} | /bin/awk '/scope global/ {{print $4}}'", aRc=0, aPersist=True, aStdout=str(ip_test)),
                    exaMockCommand(f"/bin/test -e /bin/grep", aRc=0, aPersist=True, aStdout="1"),
                    exaMockCommand(f"/bin/grep ARPCHECK /etc/sysconfig/network-scripts/ifcfg-{test_interface}", aRc=0, aPersist=True, aStdout=f"ARPCHECK={test_bridge_vals['ARPCHECK']}"),
                    exaMockCommand(f"/bin/test -e /bin/cat", aRc=0, aPersist=True, aStdout="1"),
                    exaMockCommand(f"/bin/cat /sys/class/net/{test_interface}/mtu", aRc=0, aPersist=True, aStdout=test_bridge_vals["MTU"]),
                ],
            ],
        }
        return _cmds        

    def mock_bonding_values(self, test_bond_vals, test_interface):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/bin/test -e /bin/cat", aRc=0, aPersist=True, aStdout="1"),
                    exaMockCommand(f"/bin/cat /sys/class/net/{test_interface}/mtu", aRc=0, aPersist=True, aStdout=test_bond_vals["MTU"]),
                    exaMockCommand(f"/bin/cat /sys/class/net/{test_interface}/bonding/mode",aRc=0, aPersist=True, aStdout=test_bond_vals["mode"]),
                    exaMockCommand(f"/bin/cat /sys/class/net/{test_interface}/bonding/fail_over_mac",aRc=0, aPersist=True, aStdout=test_bond_vals["fail_over_mac"]),
                    exaMockCommand(f"/bin/cat /sys/class/net/{test_interface}/bonding/num_grat_arp",aRc=0, aPersist=True, aStdout=test_bond_vals["num_grat_arp"]),
                    exaMockCommand(f"/bin/cat /sys/class/net/{test_interface}/bonding/arp_interval",aRc=0, aPersist=True, aStdout=test_bond_vals["arp_interval"]),
                    exaMockCommand(f"/bin/cat /sys/class/net/{test_interface}/bonding/primary_reselect",aRc=0, aPersist=True, aStdout=test_bond_vals["primary_reselect"]),
                    exaMockCommand(f"/bin/cat /sys/class/net/{test_interface}/bonding/arp_allslaves",aRc=0, aPersist=True, aStdout=test_bond_vals["arp_allslaves"]),
                ],
            ],
        }
        return _cmds

    def cleanup_bonding_if_enabled_tests(
            self,
            cleanup_bridge,
            cleanup_monitor,
            static_bridge,
            try_fail_bridge_deletion,
            strict_bridge_deletion):

        ebox = self.mGetClubox()
        payload = self.mGetPayload()
        ctx = self.mGetContext()

        payload['bonding_operation'] = 'delete-bonding'
        ctx.mSetConfigOption("bonding",
            { 'strict_bridge_removal': 
                'True' if strict_bridge_deletion else 'False' })

        bonding_operation = \
            clubonding.get_bonding_operation_from_payload(payload)
        nodes_bonding_confs = clubonding.extract_bonding_conf_from_payload(
            payload, bonding_operation, extract_monitor_conf=False,
            scan_ips=())
        should_support_map = {
            conf.dom0: static_bridge for conf in nodes_bonding_confs
        }

        cmds = cleanup_bonding_if_enabled_cmds(ebox, payload, cleanup_bridge,
            cleanup_monitor, should_support_map, try_fail_bridge_deletion)
        self.mPrepareMockCommands(cmds)

        if try_fail_bridge_deletion and strict_bridge_deletion:
            self.assertRaises(ExacloudRuntimeError,
                clubonding.cleanup_bonding_if_enabled, ebox, payload,
                cleanup_bridge, cleanup_monitor)
        else:
            clubonding.cleanup_bonding_if_enabled(ebox, payload,
                cleanup_bridge, cleanup_monitor)

    def test_del_bond_bridge_staticbridge(self):
        self.cleanup_bonding_if_enabled_tests(True, False, True, False, True)

    def test_del_bond_bridge_staticbridge_failcase(self):
        self.cleanup_bonding_if_enabled_tests(True, False, True, True, True)


    def test_cleanup_custom_vips_config(self):
        _commands = [
            exaMockCommand("/bin/rm*", aRc=0)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]

        with connect_to_host(dom0s[0], get_gcontext()) as dom0Node:
            clubonding.cleanup_custom_vips_config(dom0Node, "")

    def test_send_bond_monitor_garps(self):
        _commands = [
            exaMockCommand("/bin/test*", aRc=0),
            exaMockCommand("/opt/exacloud/bondmonitor/monitor_link*", aRc=0),
            exaMockCommand("/sbin/initctl*", aRc=0)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]

        with connect_to_host(dom0s[0], get_gcontext()) as dom0Node:
            clubonding.send_bond_monitor_garps(dom0Node, "")

    def test_restart_bond_monitor(self):
        _cmds = {
            self.mGetRegexDom0(): [
                restart_bond_monitor_cmds()
            ]
        }

        self.mPrepareMockCommands(_cmds)

        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]

        with connect_to_host(dom0s[0], get_gcontext()) as dom0Node:
            clubonding.restart_bond_monitor(dom0Node)

    def test_smartNIC_action(self):
        """Testing successful execution of test_standby operation"""
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/exacloud/bondmonitor/bond_utils.py", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/opt/exacloud/bondmonitor/bond_utils.py test_standby", aRc=0, aStdout=STDOUT_TEST_STANDBY)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        for dom0 in dom0s:
            with connect_to_host(dom0, self.mGetContext()) as node:
                clubonding.run_operation_with_bond_utils_script(
                    node, "test_standby")

    def test_smartNIC_action_failure(self):
        """Testing failure of test_standby operation"""
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/exacloud/bondmonitor/bond_utils.py", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/opt/exacloud/bondmonitor/bond_utils.py test_standby", aRc=1, aStdout=STDOUT_TEST_STANDBY)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        for dom0 in dom0s:
            with connect_to_host(dom0, self.mGetContext()) as node:
                with self.assertRaises(Exception):
                    clubonding.run_operation_with_bond_utils_script(
                        node, "test_standby")

    def test_bring_up_interface_DOM0(self):
        """
        Testing bring up the interface on DOM0
        """
        node = Node()
        data = {'interface': 'bondeth0', 'information': ['active_slave'],
                'nodes': node.mGetHostname()}
        with patch("exabox.ovm.clubonding.node_exec_cmd", return_value=(0, "out", "stderr")),\
             patch("exabox.ovm.clubonding.getActiveNetworkInformation", return_value=(0, "out", "stderr")):
            clubonding.bring_up_interface_DOM0("eth1", node, data, "mockHost")

    def test_persist_stack_identifier_with_value(self):
        """
        When payload contains 'stack_identifier', ensure we mkdir the monitor dir
        and write the identifier file with the expected contents.
        """
        payload = {"stack_identifier": "STACK-123"}
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/bin/mkdir -p {clubonding.REMOTE_MONITOR_DIR}", aRc=0)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        with connect_to_host(dom0s[0], get_gcontext()) as dom0Node, \
             patch("exabox.ovm.clubonding.node_write_text_file") as mock_write:
            clubonding.persist_stack_identifier(dom0Node, payload, dom0s[0])
            mock_write.assert_called_once_with(
                dom0Node,
                clubonding.REMOTE_STACK_IDENTIFIER_CONFIG,
                "STACK-123\n"
            )

    def test_persist_stack_identifier_without_value(self):
        """
        When payload does not contain 'stack_identifier', nothing should be executed.
        """
        payload = {}
        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        with connect_to_host(dom0s[0], get_gcontext()) as dom0Node, \
             patch("exabox.ovm.clubonding.node_exec_cmd_check") as mock_exec, \
             patch("exabox.ovm.clubonding.node_write_text_file") as mock_write:
            clubonding.persist_stack_identifier(dom0Node, payload, dom0s[0])
            mock_exec.assert_not_called()
            mock_write.assert_not_called()

    def test_persist_stack_identifier_handles_exception(self):
        """
        If mkdir fails (raises), persist_stack_identifier should not raise.
        """
        payload = {"stack_identifier": "STACK-123"}
        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        with connect_to_host(dom0s[0], get_gcontext()) as dom0Node, \
             patch("exabox.ovm.clubonding.node_exec_cmd_check", side_effect=Exception("boom")), \
             patch("exabox.ovm.clubonding.node_write_text_file") as mock_write:
            # Should not raise
            clubonding.persist_stack_identifier(dom0Node, payload, dom0s[0])
            # Since mkdir raised, we should not attempt to write the file
            mock_write.assert_not_called()


    def test_configure_bond_monitor_customer(self):
        """Test configure_bond_monitor for customer monitor config"""
        _cluctrl = self.mGetClubox()
        _cluctrl.mGetClusterName = MagicMock(return_value="test_cluster")
        _bond_conf = clubonding_config.NodeBondingConf(
            dom0="test_dom0",
            domu="test_domu",
            domu_client="test_domu_client",
            domu_admin_ip="192.168.1.1",
            domu_admin_vlan=1,
            monitor_conf_type=clubonding_config.MonitorConfType.CUSTOMER,
            monitor_conf='{"test": "config"}',
            bond_iface_confs=[],
            bond_cavium_info=None
        )

        _commands = [
            exaMockCommand("/bin/test -e /sbin/initctl", aRc=1),
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]

        with connect_to_host(dom0s[0], get_gcontext()) as node:
            with patch('exabox.ovm.clubonding.add_remove_entry_monitor_admin_conf') as mock_add_remove, \
                    patch('exabox.ovm.clubonding.node_write_text_file') as mock_write_text, \
                    patch('exabox.ovm.clubonding.ebCluAcceleratedNetwork.isClusterEnabledWithAcceleratedNetwork',
                          return_value=False) as mock_accelerated_check:
                # Should not raise exception
                clubonding.configure_bond_monitor(_cluctrl, node, _bond_conf)

                # Verify the methods were called with expected arguments
                mock_add_remove.assert_called_once_with(node, _bond_conf.domu_admin_ip, _bond_conf.domu_admin_vlan,
                                                        add=True)
                mock_write_text.assert_has_calls([
                    call(node, clubonding.REMOTE_MONITOR_CONFIG_FILE_FMT.format(_bond_conf.domu),
                         _bond_conf.monitor_conf),
                    call(node, clubonding.REMOTE_MONITOR_CONFIG_BK_FILE_FMT.format(_bond_conf.domu),
                         _bond_conf.monitor_conf)
                ])
                mock_accelerated_check.assert_called_once_with(_cluctrl)
    def test_get_slave_name_switchdev_enabled(self):
        """Test get_slave_name when switchdev mode is enabled"""
        node = MagicMock()
        bond_interface_name = "bondeth0"
        interface_name = "eth1"
        expected_vf_slave = "eth1vf1"

        with patch('exabox.ovm.clubonding.ebCluAcceleratedNetwork.isDom0InterfaceEnabledWithSwitchDevMode',
                   return_value=True) as mock_switchdev, \
                patch('exabox.ovm.clubonding.ebCluAcceleratedNetwork.getVirtualFnSlaveForPhysicalFnSlave',
                      return_value=expected_vf_slave) as mock_get_vf:
            result = clubonding.get_slave_name(node, bond_interface_name, interface_name)

            self.assertEqual(result, expected_vf_slave)
            mock_switchdev.assert_called_once_with(node, interface_name)
            mock_get_vf.assert_called_once_with(node, bond_interface_name, interface_name)

    def test_get_slave_name_switchdev_disabled(self):
        """Test get_slave_name when switchdev mode is disabled"""
        node = MagicMock()
        bond_interface_name = "bondeth0"
        interface_name = "eth1"

        with patch('exabox.ovm.clubonding.ebCluAcceleratedNetwork.isDom0InterfaceEnabledWithSwitchDevMode',
                   return_value=False) as mock_switchdev:
            result = clubonding.get_slave_name(node, bond_interface_name, interface_name)

            self.assertEqual(result, interface_name)
            mock_switchdev.assert_called_once_with(node, interface_name)

    def test_get_slave_name_switchdev_enabled_vf_none(self):
        """Test get_slave_name when switchdev is enabled but VF slave is None"""
        node = MagicMock()
        bond_interface_name = "bondeth0"
        interface_name = "eth1"

        with patch('exabox.ovm.clubonding.ebCluAcceleratedNetwork.isDom0InterfaceEnabledWithSwitchDevMode',
                   return_value=True) as mock_switchdev, \
                patch('exabox.ovm.clubonding.ebCluAcceleratedNetwork.getVirtualFnSlaveForPhysicalFnSlave',
                      return_value=None) as mock_get_vf:
            with self.assertRaises(ExacloudRuntimeError):
                clubonding.get_slave_name(node, bond_interface_name, interface_name)

            mock_switchdev.assert_called_once_with(node, interface_name)
            mock_get_vf.assert_called_once_with(node, bond_interface_name, interface_name)

    def test_patch_bond_bridge_ifcfg_setup(self):
        """Test patch_bond_bridge_ifcfg for setup operation"""
        node = MagicMock()
        bond_iface_conf = BondIfaceConf(
            bond_id=0,
            primary_interface="eth1",
            secondary_interface="eth2",
            ip_addr=IPv4Interface("192.168.1.100/24").ip,
            netmask=IPv4Interface("192.168.1.100/24").netmask,
            gateway=IPv4Address("192.168.1.1")
        )

        # Mock file existence checks
        node.mFileExists.side_effect = lambda path: "ifcfg-" in path

        # Mock validation functions to return True (config is already correct)
        with patch('exabox.ovm.clubonding.validate_bonding_config', return_value=True) as mock_validate_bond, \
                patch('exabox.ovm.clubonding.validate_bridge_config', return_value=True) as mock_validate_bridge, \
                patch('exabox.ovm.clubonding.get_slave_name') as mock_get_slave, \
                patch('exabox.ovm.clubonding.node_update_key_val_file') as mock_update_file, \
                patch('exabox.ovm.clubonding.node_interface_down') as mock_if_down, \
                patch('exabox.ovm.clubonding.node_interface_up') as mock_if_up, \
                patch('exabox.utils.node.node_exec_cmd_check') as mock_exec_check:
            mock_get_slave.side_effect = lambda node, bond, iface: iface  # Return interface name unchanged

            # Call the method
            clubonding.patch_bond_bridge_ifcfg(node, bond_iface_conf, is_cleanup=False)

            # Verify slave name lookups
            self.assertEqual(mock_get_slave.call_count, 2)
            mock_get_slave.assert_any_call(node, 'bondeth0', 'eth1')
            mock_get_slave.assert_any_call(node, 'bondeth0', 'eth2')

            # Since validation returns True, files should not be updated and interfaces should not be restarted
            mock_update_file.assert_not_called()

    def test_patch_bond_bridge_ifcfg_cleanup(self):
        """Test patch_bond_bridge_ifcfg for cleanup operation"""
        node = MagicMock()
        bond_iface_conf = BondIfaceConf(
            bond_id=0,
            primary_interface="eth1",
            secondary_interface="eth2",
            ip_addr=IPv4Interface("192.168.1.100/24").ip,
            netmask=IPv4Interface("192.168.1.100/24").netmask,
            gateway=IPv4Address("192.168.1.1")
        )

        # Mock file existence checks - bridge file exists, bond file doesn't
        node.mFileExists.side_effect = lambda path: "ifcfg-vmbondeth0" in path

        with patch('exabox.ovm.clubonding.validate_bonding_config', return_value=False) as mock_validate_bond, \
                patch('exabox.ovm.clubonding.validate_bridge_config', return_value=False) as mock_validate_bridge, \
                patch('exabox.ovm.clubonding.get_slave_name') as mock_get_slave, \
                patch('exabox.ovm.clubonding.node_update_key_val_file') as mock_update_file, \
                patch('exabox.ovm.clubonding.node_interface_down') as mock_if_down, \
                patch('exabox.ovm.clubonding.node_interface_up') as mock_if_up:
            mock_get_slave.side_effect = lambda node, bond, iface: iface

            # Call the method for cleanup
            clubonding.patch_bond_bridge_ifcfg(node, bond_iface_conf, is_cleanup=True)

            # Verify files are updated (since validation failed)
            self.assertEqual(mock_update_file.call_count, 1)  # Only bridge file since bond file doesn't exist

            # Verify interface operations for cleanup
            mock_if_down.assert_called_once_with(node, 'vmbondeth0')
            mock_if_up.assert_called_once_with(node, 'vmbondeth0')

class ebTestBondingElastic(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestBondingElastic, self).setUpClass(
            isElasticOperation='add_compute'
        )

    def test_parse_custom_vips_payload(self):
        extract_custom_vips_from_common_and_elastic_payload_tests(
            self,
            CUSTOM_VIPS_CORRECT_ELASTIC_PAYLOAD
        )


if __name__ == '__main__':
    unittest.main()
