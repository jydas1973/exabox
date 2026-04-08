#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/bonding/tests_bonding.py /main/23 2026/02/21 03:56:44 mpedapro Exp $
#
# tests_bonding.py
#
# Copyright (c) 2022, 2026, Oracle and/or its affiliates.
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
#    mpedapro    02/18/26 - Enh::38914367 Update bonding test cases to reflect
#                           the removed method get_slave_name in clubonding.py
#    aararora    01/16/26 - Bug 38842120: Fix monitor_admin json - regression
#                           from 38452359
#    shapatna    12/23/25 - Bug 38791495: Modify Unit tests
#                           to include keys: growMB, shrinkMB
#    joysjose    12/15/25 - Codex UT enhancement
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
from ipaddress import IPv4Interface, IPv4Address, IPv6Address
from typing import Dict, List, Mapping, Optional, Sequence, Tuple
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, call, patch
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm import clubonding_config
import exabox.ovm.clubonding as clubonding
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.MockCommand import exaMockCommand

from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.utils.node import (CmdRet, connect_to_host, node_cmd_abs_path_check)
from exabox.core.Context import get_gcontext
from exabox.ovm.clubonding_config import (
    BondIfaceConf,
    NodeBondingConf,
    NodeNetworkConf,
    Payload,
    PayloadBondOp
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
    cmds.append(exaMockCommand('/bin/test -e /sbin/initctl', aRc=1))
    cmds.append(exaMockCommand(
        f"/sbin/service {clubonding.MONITOR_SERVICE} start"))
    return cmds


def start_bond_monitor_cmds_initctl(
        already_running: bool=False) -> List[exaMockCommand]:
    """Get commands run for start_bond_monitor when initctl is present.

    :param already_running: simulate service already running condition.
    :returns: List of exaMockCommand.
    """
    cmds: List[exaMockCommand] = []
    cmds.append(exaMockCommand('/bin/test -e /sbin/initctl', aRc=0))
    err = '' if not already_running else \
        f'Job is already running: {clubonding.MONITOR_SERVICE}'
    cmds.append(exaMockCommand(
        f"/sbin/initctl start {clubonding.MONITOR_SERVICE}",
        aRc=0 if not already_running else 1,
        aStdout='',
        aStderr=err
    ))
    return cmds


def start_bond_monitor_cmds_failure() -> List[exaMockCommand]:
    """Get commands for start_bond_monitor failure via service path.

    :returns: List of exaMockCommand.
    """
    return [
        exaMockCommand('/bin/test -e /sbin/initctl', aRc=1),
        exaMockCommand(
            f"/sbin/service {clubonding.MONITOR_SERVICE} start",
            aRc=1,
            aStdout='',
            aStderr='custom-error'
        )
    ]


def stop_bond_monitor_cmds_initctl() -> List[exaMockCommand]:
    """Get commands for stop_bond_monitor when initctl is present.

    :returns: List of exaMockCommand.
    """
    return [
        exaMockCommand('/bin/test -e /sbin/initctl', aRc=0),
        exaMockCommand(f"/sbin/initctl stop {clubonding.MONITOR_SERVICE}")
    ]


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


def _build_monitor_files_map(
        active_slave: str,
        inactive_slave: str,
        monitor_config: str,
        custom_vips_config: Optional[str] = None
) -> Dict[str, str]:
    files: Dict[str, str] = {
        "/sys/class/net/eth1/operstate": "up\n",
        "/sys/class/net/eth1/master/operstate": "up\n",
        "/sys/class/net/eth2/operstate": "up\n",
        "/sys/class/net/eth2/master/operstate": "up\n",
        "/sys/class/net/bondeth0/bonding/active_slave": f"{active_slave}\n",
        "/sys/class/net/bondeth0/bonding/slaves": f"{active_slave} {inactive_slave}\n",
    }
    files[monitor_config] = "{}"
    if custom_vips_config is not None:
        files[custom_vips_config] = "{}"
    files[clubonding.REMOTE_MONITOR_CONFIG_FILE_OLD] = "{}"
    return files


class ebTestBonding(ebTestClucontrol):

    def _build_bond_iface_conf(self, bond_id: int = 0,
                               primary: str = 'eth1',
                               secondary: str = 'eth2') -> BondIfaceConf:
        return BondIfaceConf(
            bond_id=bond_id,
            ip_addr=IPv4Address('10.0.0.10'),
            netmask=IPv4Address('255.255.255.0'),
            gateway=IPv4Address('10.0.0.1'),
            primary_interface=primary,
            secondary_interface=secondary
        )

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

    def test_cleanup_bonding_if_enabled_skips_when_not_supported(self):
        # Auto-generated test for cleanup_bonding_if_enabled
        ebox = self.mGetClubox()
        payload = self.mGetPayload()
        payload['bonding_operation'] = 'delete-bonding'

        with patch('exabox.ovm.clubonding.is_bonding_supported', return_value=False):
            result = clubonding.cleanup_bonding_if_enabled(
                ebox,
                payload,
                cleanup_bridge=True,
                cleanup_monitor=True
            )

        self.assertFalse(result)

    def test_cleanup_bonding_if_enabled_warns_without_operations(self):
        # Auto-generated test for cleanup_bonding_if_enabled
        ebox = self.mGetClubox()
        payload = self.mGetPayload()
        payload['bonding_operation'] = 'delete-bonding'

        with patch('exabox.ovm.clubonding.is_bonding_supported', return_value=True), \
             patch('exabox.ovm.clubonding.get_bonding_operation_from_payload', return_value=None):
            result = clubonding.cleanup_bonding_if_enabled(
                ebox,
                payload,
                cleanup_bridge=False,
                cleanup_monitor=False
            )

        self.assertFalse(result)

    def test_cleanup_bonding_if_enabled_handles_monitor_only_without_nodes(self):
        # Auto-generated test for cleanup_bonding_if_enabled
        ebox = self.mGetClubox()
        payload = self.mGetPayload()
        payload['bonding_operation'] = 'delete-service'

        dom0 = next(iter(ebox.mReturnDom0DomUPair()))[0]

        machines_mock = MagicMock()
        networks_mock = MagicMock()
        machine_cfg = MagicMock()
        machine_cfg.mGetMacNetworks.return_value = ['network1']
        machines_mock.mGetMachineConfig.return_value = machine_cfg
        network_cfg = MagicMock()
        network_cfg.mGetNetType.return_value = 'client'
        network_cfg.mGetNetNatAddr.return_value = '10.0.0.20'
        networks_mock.mGetNetworkConfig.return_value = network_cfg
        ctx_mock = MagicMock()

        with patch('exabox.ovm.clubonding.is_bonding_supported', return_value=True), \
             patch('exabox.ovm.clubonding.get_bonding_operation_from_payload', return_value=clubonding_config.PayloadBondOp.DeleteService), \
             patch('exabox.ovm.clubonding.extract_bonding_conf_from_payload', return_value=()), \
             patch('exabox.ovm.clubonding.filter_nodes_by_cluctrl', return_value=()), \
             patch.object(ebox, 'mReturnDom0DomUPair', return_value=[(dom0, 'domuA')]), \
             patch.object(ebox, 'mReturnDom0DomUNATPair', return_value=[(dom0, 'domuA.domains')]), \
             patch.object(ebox, 'mGetMachines', return_value=machines_mock), \
             patch.object(ebox, 'mGetNetworks', return_value=networks_mock), \
             patch.object(ebox, 'mGetCtx', return_value=ctx_mock), \
             patch.object(ebox, 'mIsKVM', return_value=False), \
             patch('exabox.ovm.clubonding.is_static_monitoring_bridge_supported', return_value=True), \
             patch('exabox.ovm.clubonding.cleanup_custom_vips_config') as mock_cleanup_custom, \
             patch('exabox.ovm.clubonding.cleanup_bond_monitor_config') as mock_cleanup_monitor, \
             patch('exabox.ovm.clubonding.save_bonding_config_state') as mock_save_state, \
             patch('exabox.ovm.clubonding.connect_to_host') as mock_connect:

            mock_node = MagicMock()
            mock_connect.return_value.__enter__.return_value = mock_node

            result = clubonding.cleanup_bonding_if_enabled(
                ebox,
                payload,
                cleanup_bridge=False,
                cleanup_monitor=True
            )

        self.assertTrue(result)
        mock_cleanup_custom.assert_called_once_with(mock_node, 'domuA')
        mock_cleanup_monitor.assert_called_once()
        mock_save_state.assert_called_with(
            mock_node,
            is_cleanup=True,
            monitor_domu='domuA'
        )


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

    # Auto-generated test for start_bond_monitor
    def test_start_bond_monitor_service(self):
        _cmds = {
            self.mGetRegexDom0(): [
                start_bond_monitor_cmds(),
                start_bond_monitor_cmds_initctl(already_running=True),
                start_bond_monitor_cmds_failure()
            ]
        }

        self.mPrepareMockCommands(_cmds)

        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        dom0 = dom0s[0]

        with connect_to_host(dom0, get_gcontext()) as dom0Node:
            clubonding.start_bond_monitor(dom0Node)

        with connect_to_host(dom0, get_gcontext()) as dom0Node:
            clubonding.start_bond_monitor(dom0Node)

        with self.assertRaises(ExacloudRuntimeError):
            with connect_to_host(dom0, get_gcontext()) as dom0Node:
                clubonding.start_bond_monitor(dom0Node)

    # Auto-generated test for get_bond_monitor_status
    def test_get_bond_monitor_status(self):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand('/bin/test -e /sbin/initctl', aRc=1),
                    exaMockCommand(
                        f"/sbin/service {clubonding.MONITOR_SERVICE} status",
                        aRc=0
                    )
                ],
                [
                    exaMockCommand('/bin/test -e /sbin/initctl', aRc=0),
                    exaMockCommand(
                        f"/sbin/initctl status {clubonding.MONITOR_SERVICE}",
                        aRc=1
                    )
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        dom0 = dom0s[0]

        with connect_to_host(dom0, get_gcontext()) as dom0Node:
            self.assertTrue(clubonding.get_bond_monitor_status(dom0Node))
        with connect_to_host(dom0, get_gcontext()) as dom0Node:
            self.assertFalse(clubonding.get_bond_monitor_status(dom0Node))

    # Auto-generated test for stop_bond_monitor
    def test_stop_bond_monitor(self):
        _cmds = {
            self.mGetRegexDom0(): [
                stop_bond_monitor_cmds(),
                stop_bond_monitor_cmds_initctl()
            ]
        }

        self.mPrepareMockCommands(_cmds)

        dom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        dom0 = dom0s[0]

        with connect_to_host(dom0, get_gcontext()) as dom0Node:
            clubonding.stop_bond_monitor(dom0Node)
        with connect_to_host(dom0, get_gcontext()) as dom0Node:
            clubonding.stop_bond_monitor(dom0Node)

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


    # Auto-generated test for is_bonding_supported_dom0
    def test_is_bonding_supported_dom0_cluster_not_supported(self):
        cluctrl = MagicMock()
        payload = {}

        with patch('exabox.ovm.clubonding.is_bonding_supported', return_value=False), \
             patch('exabox.ovm.clubonding.get_bonding_operation_from_payload') as mock_op:
            result = clubonding.is_bonding_supported_dom0(cluctrl, payload, 'dom0-1')
            self.assertFalse(result)
            mock_op.assert_not_called()

    # Auto-generated test for is_bonding_supported_dom0
    def test_is_bonding_supported_dom0_missing_operation(self):
        cluctrl = MagicMock()
        payload = {}

        with patch('exabox.ovm.clubonding.is_bonding_supported', return_value=True), \
             patch('exabox.ovm.clubonding.get_bonding_operation_from_payload', return_value=None):
            result = clubonding.is_bonding_supported_dom0(cluctrl, payload, 'dom0-1')
            self.assertFalse(result)

    # Auto-generated test for is_bonding_supported_dom0
    def test_is_bonding_supported_dom0_empty_filtered_nodes(self):
        cluctrl = MagicMock()
        payload = {}

        with patch('exabox.ovm.clubonding.is_bonding_supported', return_value=True), \
             patch('exabox.ovm.clubonding.get_bonding_operation_from_payload', return_value='setup'), \
             patch('exabox.ovm.clubonding.extract_bonding_conf_from_payload', return_value=[]), \
             patch('exabox.ovm.clubonding.filter_nodes_by_cluctrl', return_value=[]):
            result = clubonding.is_bonding_supported_dom0(cluctrl, payload, 'dom0-1')
            self.assertFalse(result)

    # Auto-generated test for is_bonding_supported_dom0
    def test_is_bonding_supported_dom0_returns_true_when_dom0_present(self):
        cluctrl = MagicMock()
        payload = {}
        conf = NodeBondingConf(dom0='dom0-1')

        with patch('exabox.ovm.clubonding.is_bonding_supported', return_value=True), \
             patch('exabox.ovm.clubonding.get_bonding_operation_from_payload', return_value='setup'), \
             patch('exabox.ovm.clubonding.extract_bonding_conf_from_payload', return_value=[conf]), \
             patch('exabox.ovm.clubonding.filter_nodes_by_cluctrl', return_value=[conf]):
            result = clubonding.is_bonding_supported_dom0(cluctrl, payload, 'dom0-1')
            self.assertTrue(result)

    def _make_bond_iface_conf(self, bond_id: int = 0) -> BondIfaceConf:
        return BondIfaceConf(
            bond_id=bond_id,
            ip_addr=IPv4Address('10.0.0.10'),
            netmask=IPv4Address('255.255.255.0'),
            gateway=IPv4Address('10.0.0.1'),
            primary_interface='eth1',
            secondary_interface='eth2'
        )

    # Auto-generated test for delete_bonded_bridge
    def test_delete_bonded_bridge_raises_when_guests_present(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-1'
        bond_conf = self._make_bond_iface_conf()
        guest_output = MagicMock(stdout='guest1\n')

        with patch('exabox.ovm.clubonding.node_exec_cmd_check', return_value=guest_output), \
             patch('exabox.ovm.clubonding.node_exec_cmd') as mock_cmd:
            with self.assertRaises(ExacloudRuntimeError):
                clubonding.delete_bonded_bridge(node, bond_conf, is_kvm=False)
            mock_cmd.assert_not_called()

    # Auto-generated test for delete_bonded_bridge
    def test_delete_bonded_bridge_removes_stale_bridges(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-2'
        node.mFileExists.return_value = False
        bond_conf = self._make_bond_iface_conf(1)

        def exec_cmd_check_side_effect(node_arg, cmd):
            if cmd == "/bin/ls /EXAVMIMAGES/GuestImages":
                return CmdRet(0, '', '')
            if cmd == "/sbin/brctl show":
                bridges = 'vmbondeth1.100   info\nvmbondeth1.200   info'
                return CmdRet(0, bridges, '')
            raise AssertionError(f"Unexpected command: {cmd}")

        def exec_cmd_side_effect(node_arg, cmd, **kwargs):
            if cmd.startswith('/opt/exadata_ovm/vm_maker --remove-bridge'):
                return CmdRet(0, '', '')
            if cmd.startswith(f"{clubonding.REMOTE_IPCONF_CMD} -int-delet"):
                return CmdRet(0, '', '')
            if cmd.startswith('/bin/grep'):
                return CmdRet(1, '', '')
            if cmd.startswith('/bin/rm -f'):
                return CmdRet(0, '', '')
            if cmd.startswith('ls -l '):
                return CmdRet(1, '', '')
            return CmdRet(0, '', '')

        with patch('exabox.ovm.clubonding.node_exec_cmd_check', side_effect=exec_cmd_check_side_effect), \
             patch('exabox.ovm.clubonding.node_exec_cmd', side_effect=exec_cmd_side_effect) as mock_exec:
            clubonding.delete_bonded_bridge(node, bond_conf, is_kvm=True)

            executed = [call.args[1] for call in mock_exec.call_args_list]
            self.assertTrue(any('--remove-bridge vmbondeth1.100' in cmd for cmd in executed))
            self.assertTrue(any('--remove-bridge vmbondeth1.200' in cmd for cmd in executed))
            self.assertTrue(any('--remove-bridge vmbondeth1' in cmd for cmd in executed))
            self.assertTrue(any('ipconf -int-delet bondeth1' in cmd for cmd in executed))
            expected_ls = (
                f"ls -l {clubonding.BOND_IFCFG_PATH_FMT.format(1)}* "
                f"{clubonding.BRIDGE_IFCFG_PATH_FMT.format(1)}* | grep -E "
                f"\"{clubonding.BOND_IFCFG_PATH_FMT.format(1)}.[0-9]*$|"
                f"{clubonding.BRIDGE_IFCFG_PATH_FMT.format(1)}.[0-9]*$\""
            )
            self.assertIn(expected_ls, executed)
            self.assertTrue(any(cmd.startswith('ls -l ') for cmd in executed))

    # Auto-generated test for delete_bonded_bridge
    def test_delete_bonded_bridge_strict_failure_on_residual_files(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-3'
        bond_conf = self._make_bond_iface_conf(2)

        node.mFileExists.side_effect = lambda path: True

        def exec_cmd_check_side_effect(node_arg, cmd):
            if cmd in ("/bin/ls /EXAVMIMAGES/GuestImages", "/sbin/brctl show"):
                return MagicMock(stdout='')
            if cmd.startswith(f'ls -l {clubonding.BOND_IFCFG_PATH_FMT.format(2)}'):
                return MagicMock(stdout='')
            return MagicMock(stdout='')

        with patch('exabox.ovm.clubonding.node_exec_cmd_check', side_effect=exec_cmd_check_side_effect), \
             patch('exabox.ovm.clubonding.node_exec_cmd', return_value=(1, '', '')):
            with self.assertRaises(ExacloudRuntimeError):
                clubonding.delete_bonded_bridge(node, bond_conf, is_kvm=False, strict=True)

    # Auto-generated test for delete_bonded_bridge
    def test_delete_bonded_bridge_non_strict_suppresses_exception(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-4'
        bond_conf = self._make_bond_iface_conf(3)

        node.mFileExists.side_effect = lambda path: True

        def exec_cmd_check_side_effect(node_arg, cmd):
            if cmd in ("/bin/ls /EXAVMIMAGES/GuestImages", "/sbin/brctl show"):
                return MagicMock(stdout='')
            if cmd.startswith(f'ls -l {clubonding.BOND_IFCFG_PATH_FMT.format(3)}'):
                return MagicMock(stdout='')
            return MagicMock(stdout='')

        with patch('exabox.ovm.clubonding.node_exec_cmd_check', side_effect=exec_cmd_check_side_effect), \
             patch('exabox.ovm.clubonding.node_exec_cmd', return_value=(1, '', '')):
            clubonding.delete_bonded_bridge(node, bond_conf, is_kvm=False, strict=False)

    # Auto-generated test for delete_bonded_bridge
    def test_delete_bonded_bridge_handles_residual_glob_entries(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-5'
        node.mFileExists.return_value = False

        bond_conf = BondIfaceConf(
            bond_id=3,
            ip_addr=IPv4Address('10.0.0.30'),
            netmask=IPv4Address('255.255.255.0'),
            gateway=IPv4Address('10.0.0.1'),
            primary_interface='eth1',
            secondary_interface='eth2'
        )

        def exec_cmd_check_side_effect(node_arg, cmd):
            if cmd == "/bin/ls /EXAVMIMAGES/GuestImages":
                return CmdRet(0, '', '')
            if cmd == "/sbin/brctl show":
                bridges = 'vmbondeth3.10 info\nvmbondeth3.20 info'
                return CmdRet(0, bridges, '')
            if cmd.startswith(f'ls -l {clubonding.BOND_IFCFG_PATH_FMT.format(3)}'):
                return CmdRet(0, '', '')
            raise AssertionError(f"Unexpected command: {cmd}")

        residual_listing = 'ifcfg-bondeth3.99\nifcfg-vmbondeth3.99'

        def exec_cmd_side_effect(node_arg, cmd, **kwargs):
            if cmd.startswith('/opt/exadata_ovm/vm_maker --remove-bridge'):
                return CmdRet(0, '', '')
            if cmd.startswith(f"{clubonding.REMOTE_IPCONF_CMD} -int-delet bondeth3"):
                return CmdRet(0, '', '')
            if cmd.startswith('/bin/grep'):
                return CmdRet(0, '', '')
            if cmd.startswith(f"{clubonding.REMOTE_IPCONF_CMD} -int-delet eth"):
                return CmdRet(0, '', '')
            if cmd.startswith('/bin/rm -f'):
                return CmdRet(0, '', '')
            if cmd.startswith('ls -l '):
                return CmdRet(0, residual_listing, '')
            return CmdRet(0, '', '')

        with patch('exabox.ovm.clubonding.node_exec_cmd_check', side_effect=exec_cmd_check_side_effect), \
             patch('exabox.ovm.clubonding.node_exec_cmd', side_effect=exec_cmd_side_effect) as mock_exec:
            with self.assertRaises(ExacloudRuntimeError):
                clubonding.delete_bonded_bridge(node, bond_conf, is_kvm=True, strict=True)

        expected_remove = "/opt/exadata_ovm/vm_maker --remove-bridge vmbondeth3"
        expected_ipconf = f"{clubonding.REMOTE_IPCONF_CMD} -int-delet bondeth3"
        executed_cmds = [call.args[1] for call in mock_exec.call_args_list]
        self.assertIn(expected_remove, executed_cmds)
        self.assertIn(expected_ipconf, executed_cmds)

    # Auto-generated test for get_bond_monitor_status
    def test_get_bond_monitor_status_down_logs_service_result(self):
        node = MagicMock()
        node.mFileExists.return_value = False

        service_cmd = f"/sbin/service {clubonding.MONITOR_SERVICE} status"
        failure_ret = CmdRet(1, 'stopped', '')

        with patch('exabox.ovm.clubonding.node_exec_cmd', return_value=failure_ret) as mock_exec:
            result = clubonding.get_bond_monitor_status(node)

        self.assertFalse(result)
        mock_exec.assert_called_once_with(node, service_cmd)

    # Auto-generated test for monitor_consistency_check
    def test_monitor_consistency_check_reports_missing_files_as_false(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-6'

        present_paths = {
            '/sys/class/net/eth1/operstate': 'up',
            '/sys/class/net/eth1/master/operstate': 'up',
            '/sys/class/net/bondeth0/bonding/active_slave': 'eth1',
            '/sys/class/net/bondeth0/bonding/slaves': 'eth1 eth2'
        }

        def file_exists(path):
            return path in present_paths

        def read_text(node_arg, path):
            if path in present_paths:
                return present_paths[path]
            raise AssertionError(f'Unexpected read: {path}')

        node.mFileExists.side_effect = file_exists

        with patch('exabox.ovm.clubonding.node_read_text_file', side_effect=read_text), \
             patch('exabox.ovm.clubonding.get_bond_monitor_status', return_value=False):
            result = clubonding.monitor_consistency_check(node, ['domu1.example.com'])

        self.assertTrue(result['eth1_link'])
        self.assertTrue(result['eth1_ifstatus'])
        self.assertFalse(result['eth2_link'])
        self.assertFalse(result['eth2_ifstatus'])
        self.assertFalse(result['bondmonitor'])
        self.assertFalse(result['bondmonitor_json'])

    # Auto-generated test for cleanup_bond_bridges
    def test_cleanup_bond_bridges_invokes_delete_for_static(self):
        node = MagicMock()
        conf = self._make_bond_iface_conf()

        with patch('exabox.ovm.clubonding.delete_bonded_bridge') as mock_delete, \
             patch('exabox.ovm.clubonding.patch_bond_bridge_ifcfg') as mock_patch:
            clubonding.cleanup_bond_bridges(
                node,
                (conf,),
                is_kvm=False,
                static_bridge=True,
                bonding_operation=PayloadBondOp.CleanupBridge,
                strict_removal=True,
                keep_bridge=False
            )

            mock_delete.assert_called_once_with(node, conf, False, strict=True)
            mock_patch.assert_not_called()

    # Auto-generated test for cleanup_bond_bridges
    def test_cleanup_bond_bridges_invokes_patch_when_not_static(self):
        node = MagicMock()
        conf = self._make_bond_iface_conf()

        with patch('exabox.ovm.clubonding.delete_bonded_bridge') as mock_delete, \
             patch('exabox.ovm.clubonding.patch_bond_bridge_ifcfg') as mock_patch:
            clubonding.cleanup_bond_bridges(
                node,
                (conf,),
                is_kvm=False,
                static_bridge=False,
                bonding_operation=PayloadBondOp.SetupBridge,
                strict_removal=True,
                keep_bridge=True
            )

            mock_delete.assert_not_called()
            mock_patch.assert_called_once_with(
                node,
                conf,
                is_cleanup=True,
                restart_network=True,
                remove_bridge_ip_on_cleanup=False
            )

    # Auto-generated test for cleanup_bond_monitor_config
    def test_cleanup_bond_monitor_config_invokes_monitor_teardown(self):
        node = MagicMock()
        bond_conf = NodeBondingConf(dom0='dom0-5', domu='domu1', domu_admin_ip='10.0.0.10')

        with patch('exabox.ovm.clubonding.add_remove_entry_monitor_admin_conf') as mock_admin, \
             patch('exabox.ovm.clubonding.node_exec_cmd') as mock_exec:
            clubonding.cleanup_bond_monitor_config(node, bond_conf)
            mock_admin.assert_called_once_with(node, bond_conf.domu_admin_ip, add=False)
            exec_args = mock_exec.call_args[0][1]
            self.assertIn('rm -f', exec_args)
            self.assertIn(bond_conf.domu, exec_args)

    # Auto-generated test for uninstall_bond_monitor_rpm
    def test_uninstall_bond_monitor_rpm_when_installed(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-6'

        with patch('exabox.ovm.clubonding.get_bond_monitor_installed', return_value='bondmonitor-1.0'), \
             patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_check, \
             patch('exabox.ovm.clubonding.node_exec_cmd') as mock_exec:
            clubonding.uninstall_bond_monitor_rpm(node)
            mock_check.assert_called_once()
            self.assertTrue(mock_exec.called)

    # Auto-generated test for uninstall_bond_monitor_rpm
    def test_uninstall_bond_monitor_rpm_when_not_installed(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-7'

        with patch('exabox.ovm.clubonding.get_bond_monitor_installed', return_value=None), \
             patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_check, \
             patch('exabox.ovm.clubonding.node_exec_cmd') as mock_exec:
            clubonding.uninstall_bond_monitor_rpm(node)
            mock_check.assert_not_called()
            self.assertTrue(mock_exec.called)

    # Auto-generated test for build_custom_vips_config
    def test_build_custom_vips_config_uses_monitor_network_details(self):
        domu = 'domu1'
        payload = {
            'customvip': [
                {
                    'interfacetype': 'client',
                    'ip': '10.0.0.5'
                }
            ]
        }

        domu_net_configs = {
            'client': MagicMock()
        }
        domu_net_configs['client'].mGetNetMacAddr.return_value = 'aa:bb:cc:dd:ee:ff'
        domu_net_configs['client'].mGetNetVlanId.return_value = 'UNDEFINED'

        monitor_conf = NodeNetworkConf(
            interface_type='client',
            mac='ff:ee:dd:cc:bb:aa',
            standby_vnic_mac='11:22:33:44:55:66',
            vlantag=10
        )

        with patch('exabox.ovm.clubonding.NetworkUtils') as mock_utils:
            instance = MagicMock()
            instance.mGetIPv4IPv6PayloadNotNoneValues.return_value = ('10.0.0.5', '2001::1')
            mock_utils.return_value = instance

            result = clubonding.build_custom_vips_config(
                domu,
                domu_net_configs,
                {'client': monitor_conf},
                payload
            )

        expected_entry = {
            'type': 'app_vip',
            'ip': '10.0.0.5',
            'ipv6': '2001::1',
            'interface_type': 'client',
            'mac': 'ff:ee:dd:cc:bb:aa',
            'standby_vnic_mac': '11:22:33:44:55:66',
            'vlantag': 10,
            'floating': True
        }

        parsed = json.loads(result)
        self.assertEqual([expected_entry], parsed[domu])


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

    # Auto-generated test for update_monitor_admin_conf
    def test_update_monitor_admin_conf_no_monitor_entries(self):
        node = MagicMock()
        bond_conf = clubonding_config.NodeBondingConf(
            dom0='dom0',
            bond_iface_confs=(),
            monitor_conf=json.dumps({'other': []})
        )

        result = clubonding.update_monitor_admin_conf(node, bond_conf)

        self.assertEqual(result, bond_conf)
        node.mGetHostname.assert_not_called()

    # Auto-generated test for update_monitor_admin_conf
    def test_update_monitor_admin_conf_populates_missing_mac(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0'
        bond_conf = clubonding_config.NodeBondingConf(
            dom0='dom0',
            bond_iface_confs=(
                BondIfaceConf(
                    bond_id=0,
                    ip_addr=IPv4Address('10.0.0.10'),
                    netmask=IPv4Address('255.255.255.0'),
                    gateway=IPv4Address('10.0.0.1'),
                    primary_interface='eth1',
                    secondary_interface='eth2'
                ),
            ),
            monitor_conf=json.dumps({
                'monitor_admin': [
                    {'ip': '10.0.0.1', 'mac': '', 'vlantag': '1'},
                    {'ip': '10.0.0.2', 'mac': 'aa:bb', 'vlantag': '2'}
                ]
            })
        )

        with patch('exabox.ovm.clubonding.get_interface_mac_address', return_value='ff:ee:dd:cc:bb:aa'):
            result = clubonding.update_monitor_admin_conf(node, bond_conf)

        updated_conf = json.loads(result.monitor_conf)
        self.assertEqual(
            updated_conf['monitor_admin'][0]['mac'],
            'ff:ee:dd:cc:bb:aa'
        )
        self.assertEqual(
            updated_conf['monitor_admin'][1]['mac'],
            'aa:bb'
        )

    # Auto-generated test for add_remove_entry_monitor_admin_conf
    def test_add_remove_entry_monitor_admin_conf_missing_file(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0'
        node.mFileExists.return_value = False

        with patch('exabox.ovm.clubonding.ebLogInfo') as mock_log, \
             patch('exabox.ovm.clubonding.node_read_text_file') as mock_read, \
             patch('exabox.ovm.clubonding.node_write_text_file') as mock_write, \
             patch('exabox.ovm.clubonding.get_interface_mac_address') as mock_mac:
            clubonding.add_remove_entry_monitor_admin_conf(node, '10.0.0.1')

            node.mFileExists.assert_called_once_with(clubonding.REMOTE_MONITOR_ADMIN_CONFIG_FILE)
            mock_read.assert_not_called()
            mock_write.assert_not_called()
            mock_mac.assert_not_called()
            self.assertIn('missing', mock_log.call_args[0][0])

    # Auto-generated test for add_remove_entry_monitor_admin_conf
    def test_add_remove_entry_monitor_admin_conf_skips_when_ip_missing(self):
        node = MagicMock()

        with patch('exabox.ovm.clubonding.ebLogInfo') as mock_log, \
             patch('exabox.ovm.clubonding.node_read_text_file') as mock_read, \
             patch('exabox.ovm.clubonding.node_write_text_file') as mock_write, \
             patch('exabox.ovm.clubonding.get_interface_mac_address') as mock_mac:
            clubonding.add_remove_entry_monitor_admin_conf(node, '')

            mock_log.assert_called_once()
            self.assertIn('Admin IP missing', mock_log.call_args[0][0])
            mock_read.assert_not_called()
            mock_write.assert_not_called()
            mock_mac.assert_not_called()
            node.mFileExists.assert_not_called()

    # Auto-generated test for add_remove_entry_monitor_admin_conf
    def test_add_remove_entry_monitor_admin_conf_add_existing_ip(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0'
        node.mFileExists.return_value = True

        monitor_conf = {
            "monitor_admin": [
                {
                    "type": "admin_ip",
                    "ip": "10.0.0.1",
                    "interface_type": "admin_bondmonitor",
                    "mac": "aa:bb",
                    "standby_vnic_mac": "",
                    "vlantag": "1",
                    "floating": False
                }
            ]
        }

        with patch('exabox.ovm.clubonding.node_read_text_file', return_value=json.dumps(monitor_conf)), \
             patch('exabox.ovm.clubonding.node_write_text_file') as mock_write, \
             patch('exabox.ovm.clubonding.get_interface_mac_address', return_value='ff:ee:dd:cc:bb:aa') as mock_mac, \
             patch('exabox.ovm.clubonding.ebLogInfo') as mock_log:
            clubonding.add_remove_entry_monitor_admin_conf(node, '10.0.0.1', vlan=3)

            mock_mac.assert_called_once_with(node, clubonding.BRIDGE_INTERFACE_FMT.format(0))
            mock_write.assert_called_once()
            args = mock_write.call_args[0]
            self.assertEqual(args[0], node)
            self.assertEqual(args[1], clubonding.REMOTE_MONITOR_ADMIN_CONFIG_FILE)
            written_conf = json.loads(args[2])
            self.assertEqual(len(written_conf['monitor_admin']), 1)
            entry = written_conf['monitor_admin'][0]
            self.assertEqual(entry['ip'], '10.0.0.1')
            self.assertEqual(entry['vlantag'], '3')
            self.assertEqual(entry['mac'], 'ff:ee:dd:cc:bb:aa')
            self.assertFalse(entry['floating'])
            self.assertIn('Updated monitor_admin entry', mock_log.call_args[0][0])

    # Auto-generated test for add_remove_entry_monitor_admin_conf
    def test_add_remove_entry_monitor_admin_conf_add_new_ip(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0'
        node.mFileExists.return_value = True

        monitor_conf = {
            "monitor_admin": []
        }

        with patch('exabox.ovm.clubonding.node_read_text_file', return_value=json.dumps(monitor_conf)), \
             patch('exabox.ovm.clubonding.node_write_text_file') as mock_write, \
             patch('exabox.ovm.clubonding.get_interface_mac_address', return_value='ff:ee:dd:cc:bb:aa') as mock_mac:
            clubonding.add_remove_entry_monitor_admin_conf(node, '10.0.0.2', vlan=7)

            mock_mac.assert_called_once_with(node, clubonding.BRIDGE_INTERFACE_FMT.format(0))
            mock_write.assert_called_once()
            args = mock_write.call_args[0]
            self.assertEqual(args[0], node)
            self.assertEqual(args[1], clubonding.REMOTE_MONITOR_ADMIN_CONFIG_FILE)
            written_conf = json.loads(args[2])
            self.assertEqual(len(written_conf['monitor_admin']), 1)
            entry = written_conf['monitor_admin'][0]
            self.assertEqual(entry['ip'], '10.0.0.2')
            self.assertEqual(entry['mac'], 'ff:ee:dd:cc:bb:aa')
            self.assertEqual(entry['vlantag'], '7')
            self.assertFalse(entry['floating'])

    # Auto-generated test for add_remove_entry_monitor_admin_conf
    def test_add_remove_entry_monitor_admin_conf_remove_ip_not_found(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0'
        node.mFileExists.return_value = True

        monitor_conf = {
            "monitor_admin": [
                {
                    "type": "admin_ip",
                    "ip": "10.0.0.3",
                    "interface_type": "admin_bondmonitor",
                    "mac": "aa:bb",
                    "standby_vnic_mac": "",
                    "vlantag": "1",
                    "floating": False
                }
            ]
        }

        with patch('exabox.ovm.clubonding.node_read_text_file', return_value=json.dumps(monitor_conf)), \
             patch('exabox.ovm.clubonding.node_write_text_file') as mock_write, \
             patch('exabox.ovm.clubonding.ebLogInfo') as mock_log:
            clubonding.add_remove_entry_monitor_admin_conf(node, '10.0.0.4', add=False)

            mock_write.assert_not_called()
            self.assertIn('not found', mock_log.call_args[0][0])

    # Auto-generated test for add_remove_entry_monitor_admin_conf
    def test_add_remove_entry_monitor_admin_conf_remove_existing_ip(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0'
        node.mFileExists.return_value = True

        monitor_conf = {
            "monitor_admin": [
                {
                    "type": "admin_ip",
                    "ip": "10.0.0.5",
                    "interface_type": "admin_bondmonitor",
                    "mac": "aa:bb",
                    "standby_vnic_mac": "",
                    "vlantag": "1",
                    "floating": False
                },
                {
                    "type": "admin_ip",
                    "ip": "10.0.0.6",
                    "interface_type": "admin_bondmonitor",
                    "mac": "cc:dd",
                    "standby_vnic_mac": "",
                    "vlantag": "2",
                    "floating": False
                }
            ]
        }

        with patch('exabox.ovm.clubonding.node_read_text_file', return_value=json.dumps(monitor_conf)), \
                patch('exabox.ovm.clubonding.node_write_text_file') as mock_write:
            clubonding.add_remove_entry_monitor_admin_conf(node, '10.0.0.5', add=False)

            mock_write.assert_called_once()
            args = mock_write.call_args[0]
            self.assertEqual(args[0], node)
            self.assertEqual(args[1], clubonding.REMOTE_MONITOR_ADMIN_CONFIG_FILE)
            written_conf = json.loads(args[2])
            self.assertEqual(len(written_conf['monitor_admin']), 1)
            self.assertEqual(written_conf['monitor_admin'][0]['ip'], '10.0.0.6')

    # Auto-generated test for validate_bond_monitor_config_file
    def test_validate_bond_monitor_config_file_missing(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0'
        node.mFileExists.return_value = False

        result = clubonding.validate_bond_monitor_config_file(
            node,
            'domu1',
            '/tmp/missing.json'
        )

        self.assertFalse(result)

    # Auto-generated test for validate_bond_monitor_config_file
    def test_validate_bond_monitor_config_file_invalid_json(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0'
        node.mFileExists.return_value = True

        with patch('exabox.ovm.clubonding.node_read_text_file', return_value='{invalid'):
            result = clubonding.validate_bond_monitor_config_file(
                node,
                'domu1',
                '/tmp/invalid.json'
            )

        self.assertFalse(result)

    # Auto-generated test for validate_bond_monitor_config_file
    def test_validate_bond_monitor_config_file_domu_mismatch(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0'
        node.mFileExists.return_value = True
        monitor_content = json.dumps({'domu2': []})

        with patch('exabox.ovm.clubonding.node_read_text_file', return_value=monitor_content):
            result = clubonding.validate_bond_monitor_config_file(
                node,
                'domu1',
                '/tmp/config.json'
            )

        self.assertFalse(result)

    # Auto-generated test for validate_bond_monitor_config_file
    def test_validate_bond_monitor_config_file_success(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0'
        node.mFileExists.return_value = True
        monitor_content = json.dumps({'domu1': []})

        with patch('exabox.ovm.clubonding.node_read_text_file', return_value=monitor_content):
            result = clubonding.validate_bond_monitor_config_file(
                node,
                'domu1',
                '/tmp/config.json'
            )

        self.assertTrue(result)

    def test_install_bond_monitor_rpm_skip_when_force_disabled(self):
        # Auto-generated test for install_bond_monitor_rpm
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0'

        with patch('exabox.ovm.clubonding.get_bond_monitor_installed', return_value='bondmonitor-1'), \
             patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_exec_cmd_check:
            clubonding.install_bond_monitor_rpm(
                node,
                '/tmp/bondmonitor.rpm',
                force_reinstall=False
            )

        node.mCopyFile.assert_not_called()
        mock_exec_cmd_check.assert_not_called()

    def test_install_bond_monitor_rpm_moves_old_config(self):
        # Auto-generated test for install_bond_monitor_rpm
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0'

        def _file_exists(path):
            if path == clubonding.REMOTE_MONITOR_CONFIG_FILE_OLD:
                return True
            if path == clubonding.REMOTE_MONITOR_CONFIG_FILE_FMT.format('domu-test'):
                return False
            return False

        node.mFileExists.side_effect = _file_exists

        with patch('exabox.ovm.clubonding.get_bond_monitor_installed', return_value=None), \
             patch('exabox.ovm.clubonding.node_exec_cmd', return_value=(1, '', '')) as mock_exec_cmd, \
             patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_exec_cmd_check, \
             patch('exabox.ovm.clubonding.restart_bond_monitor') as mock_restart:
            clubonding.install_bond_monitor_rpm(
                node,
                '/tmp/bondmonitor.rpm',
                domu='domu-test'
            )

        mock_exec_cmd.assert_called_once()
        expected_mv = (
            f'/bin/mv {clubonding.REMOTE_MONITOR_CONFIG_FILE_OLD} '
            f"{clubonding.REMOTE_MONITOR_CONFIG_FILE_FMT.format('domu-test')}"
        )
        expected_install = (
            f"/bin/rpm -U --nodigest --nofiledigest --replacepkgs --oldpackage "
            f"{os.path.join(clubonding.REMOTE_BONDING_DIR, os.path.basename('/tmp/bondmonitor.rpm'))}"
        )
        mock_exec_cmd_check.assert_any_call(node, expected_mv)
        mock_exec_cmd_check.assert_any_call(node, expected_install)
        mock_restart.assert_not_called()

    def test_install_bond_monitor_rpm_removes_old_config_when_new_exists(self):
        # Auto-generated test for install_bond_monitor_rpm
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0'

        def _file_exists(path):
            if path == clubonding.REMOTE_MONITOR_CONFIG_FILE_OLD:
                return True
            if path == clubonding.REMOTE_MONITOR_CONFIG_FILE_FMT.format('domu-test'):
                return True
            return False

        node.mFileExists.side_effect = _file_exists

        with patch('exabox.ovm.clubonding.get_bond_monitor_installed', return_value=None), \
             patch('exabox.ovm.clubonding.node_exec_cmd', return_value=(1, '', '')) as mock_exec_cmd, \
             patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_exec_cmd_check, \
             patch('exabox.ovm.clubonding.restart_bond_monitor') as mock_restart:
            clubonding.install_bond_monitor_rpm(
                node,
                '/tmp/bondmonitor.rpm',
                domu='domu-test'
            )

        mock_exec_cmd.assert_called_once()
        expected_rm = f'/bin/rm -f {clubonding.REMOTE_MONITOR_CONFIG_FILE_OLD}'
        expected_install = (
            f"/bin/rpm -U --nodigest --nofiledigest --replacepkgs --oldpackage "
            f"{os.path.join(clubonding.REMOTE_BONDING_DIR, os.path.basename('/tmp/bondmonitor.rpm'))}"
        )
        mock_exec_cmd_check.assert_any_call(node, expected_rm)
        mock_exec_cmd_check.assert_any_call(node, expected_install)
        mock_restart.assert_not_called()

    def test_install_bond_monitor_rpm_restarts_when_release_matches(self):
        # Auto-generated test for install_bond_monitor_rpm
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0'
        node.mFileExists.return_value = False
        rpm_path = '/tmp/bondmonitor.rpm'
        remote_rpm_path = os.path.join(clubonding.REMOTE_BONDING_DIR, os.path.basename(rpm_path))

        with patch('exabox.ovm.clubonding.get_bond_monitor_installed', return_value='bondmonitor-1'), \
             patch('exabox.ovm.clubonding.node_exec_cmd') as mock_exec_cmd, \
             patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_exec_cmd_check, \
             patch('exabox.ovm.clubonding.restart_bond_monitor') as mock_restart:
            mock_exec_cmd.side_effect = [
                (0, 'Release     : 1', ''),
                (0, 'Release     : 1', '')
            ]

            clubonding.install_bond_monitor_rpm(node, rpm_path)

        node.mCopyFile.assert_called_once_with(rpm_path, remote_rpm_path)
        mock_restart.assert_called_once_with(node)
        mock_exec_cmd_check.assert_not_called()

    def test_install_bond_monitor_rpm_installs_when_release_differs(self):
        # Auto-generated test for install_bond_monitor_rpm
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0'
        node.mFileExists.return_value = False
        rpm_path = '/tmp/bondmonitor.rpm'
        remote_rpm_path = os.path.join(clubonding.REMOTE_BONDING_DIR, os.path.basename(rpm_path))

        with patch('exabox.ovm.clubonding.get_bond_monitor_installed', return_value='bondmonitor-1'), \
             patch('exabox.ovm.clubonding.node_exec_cmd') as mock_exec_cmd, \
             patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_exec_cmd_check, \
             patch('exabox.ovm.clubonding.restart_bond_monitor') as mock_restart:
            mock_exec_cmd.side_effect = [
                (0, 'Release     : 1', ''),
                (0, 'Release     : 2', '')
            ]

            clubonding.install_bond_monitor_rpm(node, rpm_path)

        node.mCopyFile.assert_called_once_with(rpm_path, remote_rpm_path)
        install_cmd = (
            f"/bin/rpm -U --nodigest --nofiledigest --replacepkgs --oldpackage {remote_rpm_path}"
        )
        mock_exec_cmd_check.assert_any_call(node, install_cmd)
        mock_restart.assert_not_called()

    # Auto-generated test for monitor_consistency_check
    def test_monitor_consistency_check_reports_all_states(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-1'

        monitor_file = clubonding.REMOTE_MONITOR_CONFIG_FILE_FMT.format('domu1')
        custom_vips_file = clubonding.REMOTE_VM_CUSTOM_VIP_FILE_FMT.format('domu1')
        file_contents = _build_monitor_files_map(
            active_slave='eth1',
            inactive_slave='eth2',
            monitor_config=monitor_file,
            custom_vips_config=custom_vips_file
        )

        def _file_exists(path):
            return path in file_contents

        def _read_file(node_arg, path):
            return file_contents[path]

        node.mFileExists.side_effect = _file_exists

        with patch('exabox.ovm.clubonding.node_read_text_file', side_effect=_read_file), \
             patch('exabox.ovm.clubonding.validate_bond_monitor_config_file', return_value=True), \
             patch('exabox.ovm.clubonding.get_bond_monitor_status', return_value=True):
            result = clubonding.monitor_consistency_check(node, ['domu1.example.com'])

        self.assertTrue(result['eth1_link'])
        self.assertTrue(result['eth2_link'])
        self.assertTrue(result['eth1_ifstatus'])
        self.assertTrue(result['eth2_ifstatus'])
        self.assertTrue(result['bondmonitor_json'])
        self.assertEqual(result['active_slave'], 'eth1')
        self.assertEqual(result['inactive_slave'], 'eth2')

    def test_configure_bonding_if_enabled_eth0_removed_forces_monitor(self):
        # Auto-generated test for configure_bonding_if_enabled
        ebox = self.mGetClubox()
        payload = self.mGetPayload()
        payload['bonding_operation'] = 'setup-bonding'
        dom0 = next(iter(ebox.mReturnDom0DomUPair()))[0]

        mock_conf = clubonding_config.NodeBondingConf(
            dom0=dom0,
            domu='test_domu',
            domu_client='test_client',
            domu_admin_ip='192.168.1.10',
            domu_admin_vlan=10,
            bond_iface_confs=tuple(),
            bond_cavium_info=None,
            monitor_conf='{}',
            monitor_conf_type=clubonding_config.MonitorConfType.CUSTOMER
        )

        with patch('exabox.ovm.clubonding.is_bonding_supported', return_value=True), \
             patch('exabox.ovm.clubonding.get_bond_monitor_rpm_local_path', return_value='/tmp/bondmonitor.rpm'), \
             patch('exabox.ovm.clubonding.extract_bonding_conf_from_payload', return_value=(mock_conf,)), \
             patch('exabox.ovm.clubonding.filter_nodes_by_cluctrl', return_value=(mock_conf,)), \
             patch('exabox.ovm.clubonding.connect_to_host') as mock_connect, \
             patch('exabox.ovm.clubonding.ebMiscFx.mIsEth0Removed', return_value=True) as mock_eth0_removed, \
             patch('exabox.ovm.clubonding.ebMiscFx.mIsSkipBondingBridge', return_value=False), \
             patch('exabox.ovm.clubonding.node_create_bonding_dirs'), \
             patch('exabox.ovm.clubonding.install_bond_monitor_rpm'), \
             patch('exabox.ovm.clubonding.configure_bond_bridges'), \
             patch('exabox.ovm.clubonding.save_bonding_config_state') as mock_save_state, \
             patch('exabox.ovm.clubonding.save_cavium_info'), \
             patch('exabox.ovm.clubonding.configure_bond_monitor') as mock_conf_monitor, \
             patch('exabox.ovm.clubonding.restart_bond_monitor') as mock_restart_monitor, \
             patch('exabox.ovm.clubonding.configure_custom_vips'), \
             patch('exabox.ovm.clubonding.ProcessManager') as mock_proc_manager, \
             patch('exabox.ovm.clubonding.ProcessStructure') as mock_proc_structure, \
             patch('exabox.ovm.clubonding.dom0_supports_static_bridge', return_value=True):
            class _ImmediateProcess:
                def __init__(self, target, args):
                    self._target = target
                    self._args = args
                def mSetMaxExecutionTime(self, *args, **kwargs):
                    return None
                def mSetJoinTimeout(self, *args, **kwargs):
                    return None
                def mSetLogTimeoutFx(self, *args, **kwargs):
                    return None
                def run(self):
                    self._target(*self._args)

            class _ImmediateManager:
                def __init__(self):
                    self._results = []
                def mStartAppend(self, proc):
                    proc.run()
                def mJoinProcess(self):
                    return None
                class _ManagerList:
                    def __init__(self, backing):
                        self._backing = backing
                    def list(self):
                        return self._backing
                def mGetManager(self):
                    return self._ManagerList(self._results)

            mock_proc_structure.side_effect = lambda target, args: _ImmediateProcess(target, args)
            mock_proc_manager.return_value = _ImmediateManager()
            dom0_node = MagicMock()
            mock_connect.return_value.__enter__.return_value = dom0_node

            result = clubonding.configure_bonding_if_enabled(
                ebox,
                payload,
                configure_bridge=True,
                configure_monitor=False
            )

            self.assertTrue(result)
            mock_save_state.assert_any_call(dom0_node, is_cleanup=False, bridge=True)
            mock_conf_monitor.assert_called_once_with(ebox, dom0_node, mock_conf)
            mock_restart_monitor.assert_called_once_with(dom0_node)
            mock_eth0_removed.assert_called()

    def test_configure_bonding_if_enabled_returns_false_without_operations(self):
        # Auto-generated test for configure_bonding_if_enabled
        ebox = self.mGetClubox()
        payload = self.mGetPayload()
        payload.pop('bonding_operation', None)

        result = clubonding.configure_bonding_if_enabled(
            ebox,
            payload,
            configure_bridge=False,
            configure_monitor=False
        )

        self.assertFalse(result)

    def test_configure_bonding_if_enabled_skips_when_not_supported(self):
        # Auto-generated test for configure_bonding_if_enabled
        ebox = self.mGetClubox()
        payload = self.mGetPayload()
        payload['bonding_operation'] = 'setup-bonding'

        with patch('exabox.ovm.clubonding.is_bonding_supported', return_value=False):
            result = clubonding.configure_bonding_if_enabled(
                ebox,
                payload,
                configure_bridge=True,
                configure_monitor=True
            )

            self.assertFalse(result)

    def test_configure_bonding_if_enabled_skips_bonding_when_flagged(self):
        # Auto-generated test for configure_bonding_if_enabled
        ebox = self.mGetClubox()
        payload = self.mGetPayload()
        payload['bonding_operation'] = 'setup-bonding'
        dom0 = next(iter(ebox.mReturnDom0DomUPair()))[0]

        mock_conf = clubonding_config.NodeBondingConf(
            dom0=dom0,
            domu='test_domu',
            domu_client='test_client',
            domu_admin_ip='192.168.1.10',
            domu_admin_vlan=10,
            bond_iface_confs=tuple(),
            bond_cavium_info=None,
            monitor_conf='{}',
            monitor_conf_type=clubonding_config.MonitorConfType.CUSTOMER
        )

        with patch('exabox.ovm.clubonding.is_bonding_supported', return_value=True), \
             patch('exabox.ovm.clubonding.get_bond_monitor_rpm_local_path', return_value='/tmp/bondmonitor.rpm'), \
             patch('exabox.ovm.clubonding.extract_bonding_conf_from_payload', return_value=(mock_conf,)), \
             patch('exabox.ovm.clubonding.filter_nodes_by_cluctrl', return_value=(mock_conf,)), \
             patch('exabox.ovm.clubonding.connect_to_host') as mock_connect, \
             patch('exabox.ovm.clubonding.ebMiscFx.mIsEth0Removed', return_value=False) as mock_eth0_removed, \
             patch('exabox.ovm.clubonding.ebMiscFx.mIsSkipBondingBridge', return_value=True) as mock_skip_bonding, \
             patch('exabox.ovm.clubonding.node_create_bonding_dirs') as mock_create_dirs, \
             patch('exabox.ovm.clubonding.install_bond_monitor_rpm') as mock_install_rpm, \
             patch('exabox.ovm.clubonding.configure_bond_bridges') as mock_conf_bridges, \
             patch('exabox.ovm.clubonding.save_bonding_config_state') as mock_save_state, \
             patch('exabox.ovm.clubonding.save_cavium_info') as mock_save_cavium, \
             patch('exabox.ovm.clubonding.configure_bond_monitor') as mock_conf_monitor, \
             patch('exabox.ovm.clubonding.restart_bond_monitor') as mock_restart_monitor, \
             patch('exabox.ovm.clubonding.configure_custom_vips'), \
             patch('exabox.ovm.clubonding.ProcessManager') as mock_proc_manager, \
             patch('exabox.ovm.clubonding.ProcessStructure') as mock_proc_structure, \
             patch('exabox.ovm.clubonding.dom0_supports_static_bridge', return_value=True):

            class _ImmediateProcess:
                def __init__(self, target, args):
                    self._target = target
                    self._args = args
                def mSetMaxExecutionTime(self, *args, **kwargs):
                    return None
                def mSetJoinTimeout(self, *args, **kwargs):
                    return None
                def mSetLogTimeoutFx(self, *args, **kwargs):
                    return None
                def run(self):
                    self._target(*self._args)

            class _ImmediateManager:
                def __init__(self):
                    self._results = []
                def mStartAppend(self, proc):
                    proc.run()
                def mJoinProcess(self):
                    return None
                class _ManagerList:
                    def __init__(self, backing):
                        self._backing = backing
                    def list(self):
                        return self._backing
                def mGetManager(self):
                    return self._ManagerList(self._results)

            mock_proc_structure.side_effect = lambda target, args: _ImmediateProcess(target, args)
            mock_proc_manager.return_value = _ImmediateManager()
            dom0_node = MagicMock()
            mock_connect.return_value.__enter__.return_value = dom0_node

            result = clubonding.configure_bonding_if_enabled(
                ebox,
                payload,
                configure_bridge=True,
                configure_monitor=True
            )

            self.assertTrue(result)
            mock_eth0_removed.assert_called_once_with(payload, dom0)
            mock_skip_bonding.assert_called_once_with(payload, dom0)
            mock_create_dirs.assert_not_called()
            mock_install_rpm.assert_not_called()
            mock_conf_bridges.assert_not_called()
            mock_save_cavium.assert_not_called()
            mock_conf_monitor.assert_called_once_with(ebox, dom0_node, mock_conf)
            mock_restart_monitor.assert_called_once_with(dom0_node)
            mock_save_state.assert_called_once_with(dom0_node, is_cleanup=False, monitor_domu=mock_conf.domu)

    def test_configure_bonding_if_enabled_filters_nodes_and_custom_vips(self):
        # Auto-generated test for configure_bonding_if_enabled
        ebox = self.mGetClubox()
        payload = self.mGetPayload()
        payload['bonding_operation'] = 'setup-bonding'
        payload.setdefault('customer_network', {})['customvip'] = [{'interfacetype': 'client'}]

        dom0_a = 'dom0-1'
        dom0_b = 'dom0-2'

        conf_a = clubonding_config.NodeBondingConf(
            dom0=dom0_a,
            domu='domu_a',
            domu_client='client_a',
            domu_admin_ip='10.0.0.10',
            domu_admin_vlan=20,
            bond_iface_confs=tuple(),
            bond_cavium_info=None,
            monitor_conf='{}',
            monitor_conf_type=clubonding_config.MonitorConfType.CUSTOMER
        )
        conf_b = clubonding_config.NodeBondingConf(
            dom0=dom0_b,
            domu='domu_b',
            domu_client='client_b',
            domu_admin_ip='10.0.0.11',
            domu_admin_vlan=21,
            bond_iface_confs=tuple(),
            bond_cavium_info=None,
            monitor_conf='{}',
            monitor_conf_type=clubonding_config.MonitorConfType.CUSTOMER
        )

        with patch('exabox.ovm.clubonding.is_bonding_supported', return_value=True), \
             patch('exabox.ovm.clubonding.get_bond_monitor_rpm_local_path', return_value='/tmp/bondmonitor.rpm'), \
             patch('exabox.ovm.clubonding.extract_bonding_conf_from_payload', return_value=(conf_a, conf_b)), \
             patch('exabox.ovm.clubonding.filter_nodes_by_cluctrl', return_value=(conf_a,)), \
             patch('exabox.ovm.clubonding.connect_to_host') as mock_connect, \
             patch('exabox.ovm.clubonding.ebMiscFx.mIsEth0Removed', return_value=False) as mock_eth0_removed, \
             patch('exabox.ovm.clubonding.ebMiscFx.mIsSkipBondingBridge', return_value=False) as mock_skip_bonding, \
             patch('exabox.ovm.clubonding.node_create_bonding_dirs') as mock_create_dirs, \
             patch('exabox.ovm.clubonding.install_bond_monitor_rpm') as mock_install_rpm, \
             patch('exabox.ovm.clubonding.configure_bond_bridges') as mock_conf_bridges, \
             patch('exabox.ovm.clubonding.save_bonding_config_state') as mock_save_state, \
             patch('exabox.ovm.clubonding.save_cavium_info') as mock_save_cavium, \
             patch('exabox.ovm.clubonding.configure_bond_monitor') as mock_conf_monitor, \
             patch('exabox.ovm.clubonding.restart_bond_monitor') as mock_restart_monitor, \
             patch('exabox.ovm.clubonding.configure_custom_vips') as mock_configure_custom_vips, \
             patch('exabox.ovm.clubonding.ProcessManager') as mock_proc_manager, \
             patch('exabox.ovm.clubonding.ProcessStructure') as mock_proc_structure, \
             patch('exabox.ovm.clubonding.dom0_supports_static_bridge', return_value=True):

            class _ImmediateProcess:
                def __init__(self, target, args):
                    self._target = target
                    self._args = args
                def mSetMaxExecutionTime(self, *args, **kwargs):
                    return None
                def mSetJoinTimeout(self, *args, **kwargs):
                    return None
                def mSetLogTimeoutFx(self, *args, **kwargs):
                    return None
                def run(self):
                    self._target(*self._args)

            class _ImmediateManager:
                def __init__(self):
                    self._results = []
                def mStartAppend(self, proc):
                    proc.run()
                def mJoinProcess(self):
                    return None
                class _ManagerList:
                    def __init__(self, backing):
                        self._backing = backing
                    def list(self):
                        return self._backing
                def mGetManager(self):
                    return self._ManagerList(self._results)

            processes = []

            def _immediate_structure(target, args):
                proc = _ImmediateProcess(target, args)
                processes.append(proc)
                return proc

            class _SingletonManager:
                def __init__(self):
                    self._processed = []
                def mStartAppend(self, proc):
                    proc.run()
                    self._processed.append(proc)
                def mJoinProcess(self):
                    return None
                class _ManagerList:
                    def __init__(self, processed):
                        self._processed = processed
                    def list(self):
                        return self._processed
                def mGetManager(self):
                    return self._ManagerList(self._processed)

            mock_proc_structure.side_effect = _immediate_structure
            mock_proc_manager.return_value = _SingletonManager()
            dom0_node = MagicMock()
            mock_connect.return_value.__enter__.return_value = dom0_node

            result = clubonding.configure_bonding_if_enabled(
                ebox,
                payload,
                configure_bridge=False,
                configure_monitor=True,
                nodes=[dom0_a]
            )

            self.assertTrue(result)
            mock_eth0_removed.assert_called_once_with(payload, dom0_a)
            mock_skip_bonding.assert_any_call(payload, dom0_a)
            mock_create_dirs.assert_called_once_with(dom0_node)
            mock_install_rpm.assert_called_once_with(dom0_node, '/tmp/bondmonitor.rpm')
            mock_conf_bridges.assert_not_called()
            mock_save_cavium.assert_not_called()
            mock_conf_monitor.assert_called_once_with(ebox, dom0_node, conf_a)
            mock_restart_monitor.assert_called_once_with(dom0_node)
            mock_save_state.assert_called_once_with(dom0_node, is_cleanup=False, monitor_domu=conf_a.domu)
            mock_configure_custom_vips.assert_called_once_with(
                ebox,
                {'customvip': payload['customer_network']['customvip']}
            )
            self.assertLessEqual(mock_connect.call_count, 2)
            self.assertEqual(mock_skip_bonding.call_count, 1)
            self.assertLessEqual(len(processes), 2)

    def _build_bond_iface_conf(self):
        return BondIfaceConf(
            bond_id=0,
            primary_interface='eth1',
            secondary_interface='eth2',
            ip_addr=IPv4Address('10.0.0.10'),
            netmask=IPv4Address('255.255.255.0'),
            gateway=IPv4Address('10.0.0.1')
        )

    def test_configure_bond_bridges_dynamic_creates_and_patches(self):
        # Auto-generated test for configure_bond_bridges
        node = MagicMock()
        cluctrl = MagicMock()
        bond_iface_conf = self._build_bond_iface_conf()

        with patch('exabox.ovm.clubonding.create_bonded_bridge') as mock_create_bonded, \
             patch('exabox.ovm.clubonding.create_static_bonded_bridge') as mock_create_static, \
             patch('exabox.ovm.clubonding.patch_bond_bridge_ifcfg') as mock_patch_ifcfg, \
             patch('exabox.ovm.clubonding.node_copy_file') as mock_copy, \
             patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_exec_cmd:
            clubonding.configure_bond_bridges(
                cluctrl,
                node,
                PayloadBondOp.SetupBridge,
                (bond_iface_conf,),
                is_kvm=False,
                static_bridge=False,
                reuse_bridge=False
            )

        mock_create_bonded.assert_called_once_with(node, bond_iface_conf, False)
        mock_create_static.assert_not_called()
        mock_patch_ifcfg.assert_called_once_with(
            node,
            bond_iface_conf,
            is_cleanup=False,
            restart_network=False
        )

        expected_bond_path = clubonding.BOND_IFCFG_PATH_FMT.format(bond_iface_conf.bond_id)
        expected_bridge_path = clubonding.BRIDGE_IFCFG_PATH_FMT.format(bond_iface_conf.bond_id)

        mock_copy.assert_has_calls([
            call(
                node,
                expected_bond_path,
                os.path.join(clubonding.REMOTE_BACKUP_DIR, os.path.basename(expected_bond_path)),
                overwrite=True
            ),
            call(
                node,
                expected_bridge_path,
                os.path.join(clubonding.REMOTE_BACKUP_DIR, os.path.basename(expected_bridge_path)),
                overwrite=True
            )
        ])

        mock_exec_cmd.assert_has_calls([
            call(node, f'{clubonding.REMOTE_BOND_UTILS_CMD} activate_primary'),
            call(node, f'{clubonding.REMOTE_BOND_UTILS_CMD} check_all')
        ])
        self.assertEqual(mock_exec_cmd.call_count, 2)

    def test_configure_bond_bridges_static_skips_patch(self):
        # Auto-generated test for configure_bond_bridges
        node = MagicMock()
        cluctrl = MagicMock()
        bond_iface_conf = self._build_bond_iface_conf()

        with patch('exabox.ovm.clubonding.create_bonded_bridge') as mock_create_bonded, \
             patch('exabox.ovm.clubonding.create_static_bonded_bridge') as mock_create_static, \
             patch('exabox.ovm.clubonding.patch_bond_bridge_ifcfg') as mock_patch_ifcfg, \
             patch('exabox.ovm.clubonding.node_copy_file') as mock_copy, \
             patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_exec_cmd:
            clubonding.configure_bond_bridges(
                cluctrl,
                node,
                PayloadBondOp.SetupBridge,
                (bond_iface_conf,),
                is_kvm=True,
                static_bridge=True,
                reuse_bridge=False
            )

        mock_create_static.assert_called_once_with(node, bond_iface_conf, True)
        mock_create_bonded.assert_not_called()
        mock_patch_ifcfg.assert_not_called()

        expected_bond_path = clubonding.BOND_IFCFG_PATH_FMT.format(bond_iface_conf.bond_id)
        expected_bridge_path = clubonding.BRIDGE_IFCFG_PATH_FMT.format(bond_iface_conf.bond_id)

        mock_copy.assert_has_calls([
            call(
                node,
                expected_bond_path,
                os.path.join(clubonding.REMOTE_BACKUP_DIR, os.path.basename(expected_bond_path)),
                overwrite=True
            ),
            call(
                node,
                expected_bridge_path,
                os.path.join(clubonding.REMOTE_BACKUP_DIR, os.path.basename(expected_bridge_path)),
                overwrite=True
            )
        ])

        mock_exec_cmd.assert_has_calls([
            call(node, f'{clubonding.REMOTE_BOND_UTILS_CMD} activate_primary'),
            call(node, f'{clubonding.REMOTE_BOND_UTILS_CMD} check_all')
        ])
        self.assertEqual(mock_exec_cmd.call_count, 2)

    def test_configure_bond_bridges_reuse_bridge_restarts_network(self):
        # Auto-generated test for configure_bond_bridges
        node = MagicMock()
        cluctrl = MagicMock()
        bond_iface_conf = self._build_bond_iface_conf()

        with patch('exabox.ovm.clubonding.create_bonded_bridge') as mock_create_bonded, \
             patch('exabox.ovm.clubonding.create_static_bonded_bridge') as mock_create_static, \
             patch('exabox.ovm.clubonding.patch_bond_bridge_ifcfg') as mock_patch_ifcfg, \
             patch('exabox.ovm.clubonding.node_copy_file') as mock_copy, \
             patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_exec_cmd:
            clubonding.configure_bond_bridges(
                cluctrl,
                node,
                PayloadBondOp.SetupBridge,
                (bond_iface_conf,),
                is_kvm=False,
                static_bridge=False,
                reuse_bridge=True
            )

        mock_create_bonded.assert_not_called()
        mock_create_static.assert_not_called()
        mock_patch_ifcfg.assert_called_once_with(
            node,
            bond_iface_conf,
            is_cleanup=False,
            restart_network=True
        )

        expected_bond_path = clubonding.BOND_IFCFG_PATH_FMT.format(bond_iface_conf.bond_id)
        expected_bridge_path = clubonding.BRIDGE_IFCFG_PATH_FMT.format(bond_iface_conf.bond_id)

        mock_copy.assert_has_calls([
            call(
                node,
                expected_bond_path,
                os.path.join(clubonding.REMOTE_BACKUP_DIR, os.path.basename(expected_bond_path)),
                overwrite=True
            ),
            call(
                node,
                expected_bridge_path,
                os.path.join(clubonding.REMOTE_BACKUP_DIR, os.path.basename(expected_bridge_path)),
                overwrite=True
            )
        ])

        mock_exec_cmd.assert_has_calls([
            call(node, f'{clubonding.REMOTE_BOND_UTILS_CMD} activate_primary'),
            call(node, f'{clubonding.REMOTE_BOND_UTILS_CMD} check_all')
        ])
        self.assertEqual(mock_exec_cmd.call_count, 2)

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_setup_uses_json_payload(self):
        cluctrl = MagicMock()
        payload = {'bonding_operation': 'setup-bonding'}

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('setup', json.dumps(payload), True, False,
                                 {})), \
             patch('exabox.ovm.clubonding.os.path.isfile', return_value=False), \
             patch('exabox.ovm.clubonding.configure_bonding_if_enabled') as mock_cfg:
            clubonding.handle_bonding_operation(cluctrl)

        mock_cfg.assert_called_once_with(
            cluctrl, payload, configure_bridge=True, configure_monitor=False)

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_install_monitor_failure(self):
        cluctrl = MagicMock()
        payload = {'nodes': ['dom0-1']}
        node = MagicMock()
        ctx_mgr = MagicMock()
        ctx_mgr.__enter__.return_value = node
        ctx_mgr.__exit__.return_value = None

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=(
                       'install_monitor', payload, False, False,
                       {'dom0-1': 'domu-1'}
                   )), \
             patch('exabox.ovm.clubonding.get_bond_monitor_rpm_local_path',
                   return_value='/tmp/bondmonitor.rpm'), \
             patch('exabox.ovm.clubonding.connect_to_host', return_value=ctx_mgr) as mock_conn, \
             patch('exabox.ovm.clubonding.node_create_bonding_dirs') as mock_mkdir, \
             patch('exabox.ovm.clubonding.install_bond_monitor_rpm',
                   side_effect=Exception('boom')), \
             patch('exabox.ovm.clubonding.persist_stack_identifier') as mock_persist:
            with self.assertRaises(ExacloudRuntimeError):
                clubonding.handle_bonding_operation(cluctrl)

        mock_conn.assert_called_once()
        mock_mkdir.assert_called_once_with(node)
        mock_persist.assert_not_called()

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_linkfailover_triggers_failover(self):
        cluctrl = self.mGetClubox()
        payload = {'nodes': ['dom0-1'], 'newactive': 'eth2'}
        node = MagicMock()
        ctx_mgr = MagicMock()
        ctx_mgr.__enter__.return_value = node
        ctx_mgr.__exit__.return_value = None

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('linkfailover', payload, False, False, {})), \
             patch('exabox.ovm.clubonding.connect_to_host', return_value=ctx_mgr), \
             patch('exabox.ovm.clubonding.getActiveNetworkInformation',
                   return_value={'nodes': [{'node': 'dom0-1',
                                            'active_slave': 'eth1'}]}), \
             patch('exabox.ovm.clubonding.test_failover') as mock_failover:
            clubonding.handle_bonding_operation(cluctrl)

        mock_failover.assert_called_once_with(node, 'eth1')

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_status_monitor_updates_request(self):
        cluctrl = self.mGetClubox()
        payload = {'nodes': {'dom0-1': ['domu-1']}}
        node = MagicMock()
        ctx_mgr = MagicMock()
        ctx_mgr.__enter__.return_value = node
        ctx_mgr.__exit__.return_value = None
        request = MagicMock()
        db = MagicMock()

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('status_monitor', payload, False, False, {})), \
             patch('exabox.ovm.clubonding.connect_to_host', return_value=ctx_mgr), \
             patch('exabox.ovm.clubonding.monitor_consistency_check',
                   return_value={'healthy': True}), \
             patch('exabox.ovm.clubonding.ebGetDefaultDB', return_value=db), \
             patch('exabox.ovm.clubonding.json.dumps', wraps=json.dumps) as mock_dumps, \
             patch.object(cluctrl, 'mGetRequestObj', return_value=request):
            clubonding.handle_bonding_operation(cluctrl)

        request.mSetData.assert_called_once()
        db.mUpdateRequest.assert_called_once_with(request)

        mock_dumps.assert_any_call({'nodes': {'dom0-1': {'healthy': True}}},
                                   indent=4)

    def test_handle_bonding_operation_wraps_unexpected_error(self):
        # Auto-generated test for handle_bonding_operation
        cluctrl = self.mGetClubox()
        payload = {'nodes': {'dom0-err': ['domu-err']}}

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('setup', payload, True, True, {})), \
             patch('exabox.ovm.clubonding.configure_bonding_if_enabled',
                   side_effect=ValueError('explode')) as mock_configure:
            with self.assertRaises(ExacloudRuntimeError) as ctx:
                clubonding.handle_bonding_operation(cluctrl)

        mock_configure.assert_called_once_with(
            cluctrl,
            payload,
            configure_bridge=True,
            configure_monitor=True
        )
        self.assertIn('bonding_operation failed', str(ctx.exception))

    def test_configure_bond_bridges_migration_flow_updates_existing(self):
        # Auto-generated test for configure_bond_bridges
        node = MagicMock()
        cluctrl = MagicMock()
        bond_iface_conf = self._build_bond_iface_conf()

        with patch('exabox.ovm.clubonding.create_bonded_bridge') as mock_create_bonded, \
             patch('exabox.ovm.clubonding.create_static_bonded_bridge') as mock_create_static, \
             patch('exabox.ovm.clubonding.patch_bond_bridge_ifcfg') as mock_patch_ifcfg, \
             patch('exabox.ovm.clubonding.node_copy_file') as mock_copy, \
             patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_exec_cmd:
            clubonding.configure_bond_bridges(
                cluctrl,
                node,
                PayloadBondOp.MigrationFlow,
                (bond_iface_conf,),
                is_kvm=False,
                static_bridge=False,
                reuse_bridge=False
            )

        mock_create_bonded.assert_not_called()
        mock_create_static.assert_not_called()
        mock_patch_ifcfg.assert_called_once_with(
            node,
            bond_iface_conf,
            is_cleanup=False,
            restart_network=False
        )

        expected_bond_path = clubonding.BOND_IFCFG_PATH_FMT.format(bond_iface_conf.bond_id)
        expected_bridge_path = clubonding.BRIDGE_IFCFG_PATH_FMT.format(bond_iface_conf.bond_id)

        mock_copy.assert_has_calls([
            call(
                node,
                expected_bond_path,
                os.path.join(clubonding.REMOTE_BACKUP_DIR, os.path.basename(expected_bond_path)),
                overwrite=True
            ),
            call(
                node,
                expected_bridge_path,
                os.path.join(clubonding.REMOTE_BACKUP_DIR, os.path.basename(expected_bridge_path)),
                overwrite=True
            )
        ])

        mock_exec_cmd.assert_has_calls([
            call(node, f'{clubonding.REMOTE_BOND_UTILS_CMD} activate_primary'),
            call(node, f'{clubonding.REMOTE_BOND_UTILS_CMD} check_all')
        ])
        self.assertEqual(mock_exec_cmd.call_count, 2)

    def test_patch_bond_bridge_ifcfg_restart_network(self):
        # Auto-generated test for patch_bond_bridge_ifcfg
        node = MagicMock()
        bond_iface_conf = BondIfaceConf(
            bond_id=1,
            primary_interface="eth3",
            secondary_interface="eth4",
            ip_addr=IPv4Interface("10.0.0.5/24").ip,
            netmask=IPv4Interface("10.0.0.5/24").netmask,
            gateway=IPv4Address("10.0.0.1")
        )

        node.mFileExists.side_effect = lambda path: True

        with patch('exabox.ovm.clubonding.validate_bonding_config', return_value=False), \
             patch('exabox.ovm.clubonding.validate_bridge_config', return_value=False), \
             patch('exabox.ovm.clubonding.node_update_key_val_file') as mock_update_file, \
             patch('exabox.ovm.clubonding.node_interface_down') as mock_if_down, \
             patch('exabox.ovm.clubonding.node_interface_up') as mock_if_up, \
             patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_exec_cmd:
            clubonding.patch_bond_bridge_ifcfg(
                node,
                bond_iface_conf,
                is_cleanup=False,
                restart_network=True
            )

            self.assertTrue(mock_update_file.called)
            mock_exec_cmd.assert_called_once_with(node, "/bin/systemctl restart network")
            mock_if_down.assert_not_called()
            mock_if_up.assert_not_called()

    def test_patch_bond_bridge_ifcfg_setup(self):
        """Test patch_bond_bridge_ifcfg for setup operation"""
        node = MagicMock()
        node.mGetHostname.return_value = "dom0"
        bond_iface_conf = BondIfaceConf(
            bond_id=0,
            primary_interface="eth1",
            secondary_interface="eth2",
            ip_addr=IPv4Interface("192.168.1.100/24").ip,
            netmask=IPv4Interface("192.168.1.100/24").netmask,
            gateway=IPv4Address("192.168.1.1")
        )

        node.mFileExists.side_effect = lambda path: True

        with patch('exabox.ovm.clubonding.validate_bonding_config', return_value=True), \
                patch('exabox.ovm.clubonding.validate_bridge_config', return_value=True), \
                patch('exabox.ovm.clubonding.node_update_key_val_file') as mock_update_file, \
                patch('exabox.ovm.clubonding.node_interface_down') as mock_if_down, \
                patch('exabox.ovm.clubonding.node_interface_up') as mock_if_up, \
                patch('exabox.ovm.clubonding.get_gcontext') as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_ctx.mGetConfigOptions.return_value = {
                "force_network_interfaces_reboot": "false"
            }
            mock_get_ctx.return_value = mock_ctx

            clubonding.patch_bond_bridge_ifcfg(node, bond_iface_conf, is_cleanup=False)

            mock_update_file.assert_not_called()
            mock_if_down.assert_not_called()
            mock_if_up.assert_has_calls([
                call(node, 'eth1'),
                call(node, 'eth2')
            ])
            self.assertEqual(mock_if_up.call_count, 2)

    def test_patch_bond_bridge_ifcfg_cleanup(self):
        """Test patch_bond_bridge_ifcfg for cleanup operation"""
        node = MagicMock()
        node.mGetHostname.return_value = "dom0"
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

        with patch('exabox.ovm.clubonding.validate_bonding_config', return_value=False), \
                patch('exabox.ovm.clubonding.validate_bridge_config', return_value=False), \
                patch('exabox.ovm.clubonding.node_update_key_val_file') as mock_update_file, \
                patch('exabox.ovm.clubonding.node_interface_down') as mock_if_down, \
                patch('exabox.ovm.clubonding.node_interface_up') as mock_if_up, \
                patch('exabox.ovm.clubonding.get_gcontext') as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_ctx.mGetConfigOptions.return_value = {
                "force_network_interfaces_reboot": "false"
            }
            mock_get_ctx.return_value = mock_ctx

            clubonding.patch_bond_bridge_ifcfg(node, bond_iface_conf, is_cleanup=True)

            self.assertEqual(mock_update_file.call_count, 1)
            mock_if_down.assert_called_once_with(node, 'vmbondeth0')
            mock_if_up.assert_called_once_with(node, 'vmbondeth0')

    def test_patch_bond_bridge_ifcfg_cleanup_missing_bridge_file(self):
        """Ensure cleanup skips bridge operations when file missing"""
        node = MagicMock()
        node.mGetHostname.return_value = "dom0"
        node.mFileExists.side_effect = lambda path: "ifcfg-bondeth0" in path

        bond_iface_conf = BondIfaceConf(
            bond_id=0,
            primary_interface="eth1",
            secondary_interface="eth2",
            ip_addr=IPv4Interface("192.168.1.100/24").ip,
            netmask=IPv4Interface("192.168.1.100/24").netmask,
            gateway=IPv4Address("192.168.1.1")
        )

        with patch('exabox.ovm.clubonding.validate_bonding_config', return_value=False), \
                patch('exabox.ovm.clubonding.validate_bridge_config', return_value=False), \
                patch('exabox.ovm.clubonding.node_update_key_val_file') as mock_update_file, \
                patch('exabox.ovm.clubonding.node_interface_down') as mock_if_down, \
                patch('exabox.ovm.clubonding.node_interface_up') as mock_if_up, \
                patch('exabox.ovm.clubonding.get_gcontext') as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_ctx.mGetConfigOptions.return_value = {
                "force_network_interfaces_reboot": "false"
            }
            mock_get_ctx.return_value = mock_ctx

            clubonding.patch_bond_bridge_ifcfg(
                node,
                bond_iface_conf,
                is_cleanup=True,
                remove_bridge_ip_on_cleanup=True
            )

            mock_update_file.assert_called_once_with(
                node,
                '/etc/sysconfig/network-scripts/ifcfg-bondeth0',
                {'BONDING_OPTS': '"mode=active-backup miimon=100 downdelay=2000 updelay=5000 num_grat_arp=100"'}
            )
            mock_if_down.assert_called_once_with(node, 'bondeth0')
            mock_if_up.assert_called_once_with(node, 'bondeth0')

    def test_patch_bond_bridge_ifcfg_skip_bridge_restart_when_matching(self):
        """Ensure bridge config is not updated when already matching"""
        node = MagicMock()
        node.mGetHostname.return_value = "dom0"
        node.mFileExists.side_effect = lambda path: True

        bond_iface_conf = BondIfaceConf(
            bond_id=0,
            primary_interface="eth1",
            secondary_interface="eth2",
            ip_addr=IPv4Interface("192.168.1.100/24").ip,
            netmask=IPv4Interface("192.168.1.100/24").netmask,
            gateway=IPv4Address("192.168.1.1")
        )

        with patch('exabox.ovm.clubonding.validate_bonding_config', return_value=False), \
                patch('exabox.ovm.clubonding.validate_bridge_config', return_value=True), \
                patch('exabox.ovm.clubonding.node_update_key_val_file') as mock_update_file, \
                patch('exabox.ovm.clubonding.node_interface_down') as mock_if_down, \
                patch('exabox.ovm.clubonding.node_interface_up') as mock_if_up, \
                patch('exabox.ovm.clubonding.get_gcontext') as mock_get_ctx:
            mock_ctx = MagicMock()
            mock_ctx.mGetConfigOptions.return_value = {
                "force_network_interfaces_reboot": "false"
            }
            mock_get_ctx.return_value = mock_ctx

            clubonding.patch_bond_bridge_ifcfg(node, bond_iface_conf, is_cleanup=False)

            mock_update_file.assert_called_once()  # only bond updates executed
            mock_if_down.assert_called_once_with(node, 'bondeth0')
            mock_if_up.assert_has_calls([call(node, 'bondeth0'), call(node, 'eth1'), call(node, 'eth2')])

    def test_update_bonded_bridges_skips_when_eth0_removed(self):
        # Auto-generated test for update_bonded_bridges
        cluctrl = MagicMock()
        payload = {'bonding_operation': 'setup-bonding'}

        bond_conf = MagicMock()
        bond_conf.dom0 = 'dom0-1'
        iface_conf = MagicMock()
        bond_conf.bond_iface_confs = [iface_conf]

        cluctrl.mGetCtx.return_value = MagicMock()

        with patch('exabox.ovm.clubonding.get_bonding_operation_from_payload', return_value='setup'), \
                patch('exabox.ovm.clubonding.extract_bonding_conf_from_payload', return_value=[bond_conf]), \
                patch('exabox.ovm.clubonding.filter_nodes_by_cluctrl', return_value=[bond_conf]), \
                patch('exabox.ovm.clubonding.connect_to_host') as mock_connect, \
                patch('exabox.ovm.clubonding.patch_bond_bridge_ifcfg') as mock_patch_bridge, \
                patch('exabox.ovm.clubonding.ebMiscFx.mIsEth0Removed', return_value=True):
            mock_node = MagicMock()
            mock_connect.return_value.__enter__.return_value = mock_node

            clubonding.update_bonded_bridges(cluctrl, payload)

            mock_patch_bridge.assert_not_called()
            mock_connect.assert_called_once_with(bond_conf.dom0, cluctrl.mGetCtx())

    def test_update_bonded_bridges_invokes_patch_when_eth0_present(self):
        # Auto-generated test for update_bonded_bridges
        cluctrl = MagicMock()
        payload = {'bonding_operation': 'setup-bonding'}

        bond_conf = MagicMock()
        bond_conf.dom0 = 'dom0-2'
        iface_conf = MagicMock()
        bond_conf.bond_iface_confs = [iface_conf]

        cluctrl.mGetCtx.return_value = MagicMock()

        with patch('exabox.ovm.clubonding.ebCluCmdCheckOptions', return_value=True), \
                patch('exabox.ovm.clubonding.get_bonding_operation_from_payload', return_value='setup'), \
                patch('exabox.ovm.clubonding.extract_bonding_conf_from_payload', return_value=[bond_conf]), \
                patch('exabox.ovm.clubonding.filter_nodes_by_cluctrl', return_value=[bond_conf]), \
                patch('exabox.ovm.clubonding.connect_to_host') as mock_connect, \
                patch('exabox.ovm.clubonding.patch_bond_bridge_ifcfg') as mock_patch_bridge, \
                patch('exabox.ovm.clubonding.ebMiscFx.mIsEth0Removed', return_value=False):
            mock_node = MagicMock()
            ctx_mgr = MagicMock()
            ctx_mgr.__enter__.return_value = mock_node
            ctx_mgr.__exit__.return_value = False
            mock_connect.return_value = ctx_mgr

            clubonding.update_bonded_bridges(cluctrl, payload)

            mock_connect.assert_called_once_with(bond_conf.dom0, cluctrl.mGetCtx())
            mock_patch_bridge.assert_called_once_with(mock_node, iface_conf, False, False)

    # Auto-generated test for get_bond_monitor_rpm_local_path
    def test_get_bond_monitor_rpm_local_path_success(self):
        local_rpm = '/tmp/bondmonitor.rpm'
        with patch('os.path.realpath', return_value=local_rpm) as mock_realpath, \
             patch('os.path.isfile', return_value=True) as mock_isfile:
            result = clubonding.get_bond_monitor_rpm_local_path()

        mock_realpath.assert_called_once_with(
            clubonding.LOCAL_MONITOR_RPM_FILE)
        mock_isfile.assert_called_once_with(local_rpm)
        self.assertEqual(result, local_rpm)

    # Auto-generated test for get_bond_monitor_rpm_local_path
    def test_get_bond_monitor_rpm_local_path_missing_file(self):
        missing_rpm = '/missing/rpm'
        with patch('os.path.realpath', return_value=missing_rpm) as mock_realpath, \
             patch('os.path.isfile', return_value=False) as mock_isfile, \
             patch('exabox.ovm.clubonding.ebLogError') as mock_log:
            with self.assertRaises(ExacloudRuntimeError) as exc:
                clubonding.get_bond_monitor_rpm_local_path()

        mock_realpath.assert_called_once_with(
            clubonding.LOCAL_MONITOR_RPM_FILE)
        mock_isfile.assert_called_once_with(missing_rpm)
        self.assertIn('Bonding monitor RPM file /missing/rpm',
                      str(exc.exception))
        mock_log.assert_called_once()


    # Auto-generated test for bonding_consistency_check
    def test_bonding_consistency_check_detects_missing_state_file(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-9'
        missing_path = '/sys/class/net/eth1/operstate'

        def fake_exists(path):
            if path == clubonding.REMOTE_BOND_UTILS_CMD:
                return True
            return path != missing_path

        node.mFileExists.side_effect = fake_exists

        with patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_exec, \
             patch('exabox.ovm.clubonding.node_read_text_file') as mock_read:
            mock_exec.return_value = (0, 'ok', '')
            with self.assertRaises(ExacloudRuntimeError) as ctx:
                clubonding.bonding_consistency_check(node)

        self.assertIn(missing_path, str(ctx.exception))
        mock_read.assert_not_called()

    # Auto-generated test for bonding_consistency_check
    def test_bonding_consistency_check_handles_retry_then_failure(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-10'
        state_file = '/sys/class/net/eth1/operstate'
        master_file = '/sys/class/net/eth1/master/operstate'
        read_results = {
            state_file: ['down', 'up'],
            master_file: ['down'] * 10
        }

        def fake_exists(path):
            if path == clubonding.REMOTE_BOND_UTILS_CMD:
                return True
            return True

        node.mFileExists.side_effect = fake_exists

        def fake_read(node_arg, path):
            values = read_results.get(path)
            if values:
                return values.pop(0)
            return 'up'

        with patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_exec, \
             patch('exabox.ovm.clubonding.node_read_text_file',
                   side_effect=fake_read), \
             patch('exabox.ovm.clubonding.time.sleep') as mock_sleep:
            mock_exec.return_value = (0, 'ok', '')
            with self.assertRaises(ExacloudRuntimeError) as ctx:
                clubonding.bonding_consistency_check(node)

        self.assertIn('Bad state', str(ctx.exception))
        self.assertGreaterEqual(mock_sleep.call_count, 9)

    # Auto-generated test for bonding_consistency_check
    def test_bonding_consistency_check_validates_monitor_config(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-11'
        node.mFileExists.side_effect = lambda path: path == clubonding.REMOTE_BOND_UTILS_CMD or 'operstate' in path

        with patch('exabox.ovm.clubonding.node_exec_cmd_check',
                   return_value=(0, 'ok', '')), \
             patch('exabox.ovm.clubonding.node_read_text_file',
                   return_value='up'), \
             patch('exabox.ovm.clubonding.get_bond_monitor_status',
                   return_value=False):
            with self.assertRaises(ExacloudRuntimeError) as ctx:
                clubonding.bonding_consistency_check(node, 'domu-1')

        self.assertIn('bondmonitor servie is not active', str(ctx.exception))

    # Auto-generated test for bonding_consistency_check
    def test_bonding_consistency_check_requires_monitor_json(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-12'
        node.mFileExists.side_effect = lambda path: path == clubonding.REMOTE_BOND_UTILS_CMD or 'operstate' in path

        with patch('exabox.ovm.clubonding.node_exec_cmd_check',
                   return_value=(0, 'ok', '')), \
             patch('exabox.ovm.clubonding.node_read_text_file',
                   return_value='up'), \
             patch('exabox.ovm.clubonding.get_bond_monitor_status',
                   return_value=True), \
             patch('exabox.ovm.clubonding.validate_bond_monitor_config_file',
                   return_value=False):
            with self.assertRaises(ExacloudRuntimeError) as ctx:
                clubonding.bonding_consistency_check(node, 'domu-2')

        self.assertIn('monitor config file not found', str(ctx.exception))

    # Auto-generated test for bonding_consistency_check
    def test_bonding_consistency_check_requires_custom_vips(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-13'
        node.mFileExists.side_effect = lambda path: path == clubonding.REMOTE_BOND_UTILS_CMD or 'operstate' in path

        with patch('exabox.ovm.clubonding.node_exec_cmd_check',
                   return_value=(0, 'ok', '')), \
             patch('exabox.ovm.clubonding.node_read_text_file',
                   return_value='up'), \
             patch('exabox.ovm.clubonding.get_bond_monitor_status',
                   return_value=True), \
             patch('exabox.ovm.clubonding.validate_bond_monitor_config_file',
                   side_effect=[True, False]):
            with self.assertRaises(ExacloudRuntimeError) as ctx:
                clubonding.bonding_consistency_check(
                    node, 'domu-3', custom_vips=[{'vip': '10.0.0.1'}])

        self.assertIn('Custom VIPs config file not found', str(ctx.exception))

    # Auto-generated test for migrate_static_bridges
    def test_migrate_static_bridges_returns_false_when_not_supported(self):
        cluctrl = self.mGetClubox()
        payload = {'bonding_operation': 'cleanup'}

        with patch('exabox.ovm.clubonding.is_bonding_supported',
                   return_value=False) as mock_supported:
            result = clubonding.migrate_static_bridges(cluctrl, payload)

        self.assertFalse(result)
        mock_supported.assert_called_once_with(cluctrl)

    # Auto-generated test for migrate_static_bridges
    def test_migrate_static_bridges_skips_when_no_nodes_need_migration(self):
        cluctrl = self.mGetClubox()
        payload = {'bonding_operation': 'cleanup'}
        conf = MagicMock()
        conf.dom0 = 'dom0-14'

        with patch('exabox.ovm.clubonding.is_bonding_supported',
                   return_value=True), \
             patch('exabox.ovm.clubonding.get_bonding_operation_from_payload',
                   return_value='cleanup'), \
             patch('exabox.ovm.clubonding.is_static_monitoring_bridge_supported',
                   return_value=True), \
             patch('exabox.ovm.clubonding.extract_bonding_conf_from_payload',
                   return_value=[conf]), \
             patch('exabox.ovm.clubonding.filter_nodes_by_cluctrl',
                   return_value=[]):
            result = clubonding.migrate_static_bridges(cluctrl, payload)

        self.assertFalse(result)

    # Auto-generated test for migrate_static_bridges
    def test_migrate_static_bridges_invokes_configure_when_needed(self):
        cluctrl = MagicMock()
        payload = {'bonding_operation': 'cleanup'}
        conf = MagicMock()
        conf.dom0 = 'dom0-15'
        ctx = MagicMock()

        node_ctx = MagicMock()
        node_ctx.__enter__.return_value = MagicMock()
        node_ctx.__exit__.return_value = False
        bridge_prefix = clubonding.BRIDGE_INTERFACE_FMT.format('')

        with patch('exabox.ovm.clubonding.is_bonding_supported',
                   return_value=True), \
             patch('exabox.ovm.clubonding.get_bonding_operation_from_payload',
                   return_value='cleanup'), \
             patch('exabox.ovm.clubonding.is_static_monitoring_bridge_supported',
                   return_value=True), \
             patch('exabox.ovm.clubonding.extract_bonding_conf_from_payload',
                   return_value=[conf]), \
             patch('exabox.ovm.clubonding.filter_nodes_by_cluctrl',
                   return_value=[conf]), \
             patch.object(cluctrl, 'mGetCtx', return_value=ctx), \
             patch('exabox.ovm.clubonding.connect_to_host',
                   return_value=node_ctx), \
             patch('exabox.ovm.clubonding.dom0_has_static_bridge',
                   return_value=False), \
             patch('exabox.ovm.clubonding.get_node_nics',
                   return_value=[bridge_prefix + '0']), \
             patch('exabox.ovm.clubonding.configure_bonding_if_enabled',
                   return_value=True) as mock_configure:
            result = clubonding.migrate_static_bridges(cluctrl, payload)

        self.assertTrue(result)
        mock_configure.assert_called_once_with(
            cluctrl,
            payload,
            configure_bridge=True,
            configure_monitor=False,
            nodes=[conf.dom0]
        )

    # Auto-generated test for get_bond_monitor_installed
    def test_get_bond_monitor_installed_returns_version(self):
        node = MagicMock()

        with patch('exabox.ovm.clubonding.node_exec_cmd',
                   return_value=(0, 'bondmonitor-1.2.3', '')):
            result = clubonding.get_bond_monitor_installed(node)

        self.assertEqual(result, 'bondmonitor-1.2.3')

    # Auto-generated test for get_bond_monitor_installed
    def test_get_bond_monitor_installed_handles_missing_package(self):
        node = MagicMock()

        with patch('exabox.ovm.clubonding.node_exec_cmd',
                   return_value=(1, '', 'not installed')):
            result = clubonding.get_bond_monitor_installed(node)

        self.assertIsNone(result)


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


class BondingEdgeCaseTests(unittest.TestCase):

    # Auto-generated test for validate_bonding_config
    def test_validate_bonding_config_missing_attribute(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-1'

        with patch('exabox.ovm.clubonding.read_bond_interface_atr',
                   return_value=''):
            result = clubonding.validate_bonding_config(
                node,
                'bondeth0',
                {'arp_interval': '1000'}
            )

        self.assertFalse(result)

    # Auto-generated test for validate_bonding_config
    def test_validate_bonding_config_suffixed_missing_value(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-2'

        with patch('exabox.ovm.clubonding.read_bond_interface_atr',
                   return_value='fail_over_mac=1'):
            result = clubonding.validate_bonding_config(
                node,
                'bondeth0',
                {'fail_over_mac': '1'}
            )

        self.assertFalse(result)

    # Auto-generated test for validate_bridge_config
    def test_validate_bridge_config_handles_read_failure(self):
        node = MagicMock()

        with patch('exabox.ovm.clubonding.read_bridge_interface_attrs',
                   side_effect=Exception('boom')):
            result = clubonding.validate_bridge_config(
                node,
                'vmbondeth0',
                {'ipaddr': '10.0.0.1'}
            )

        self.assertFalse(result)

    # Auto-generated test for validate_bridge_config
    def test_validate_bridge_config_detects_mismatches(self):
        node = MagicMock()
        expected = {
            'ipaddr': '10.0.0.1',
            'netmask': '255.255.255.0',
            'arpcheck': 'yes',
            'mtu': '9000'
        }
        actual = {
            'IPADDR': '10.0.0.2',
            'NETMASK': '255.255.0.0',
            'ARPCHECK': '',
            'MTU': '8000'
        }

        with patch('exabox.ovm.clubonding.read_bridge_interface_attrs',
                   return_value=actual):
            result = clubonding.validate_bridge_config(
                node,
                'vmbondeth0',
                expected
            )

        self.assertFalse(result)

    # Auto-generated test for filter_nodes_by_cluctrl
    def test_filter_nodes_by_cluctrl_filters_dom0s(self):
        cluctrl = MagicMock()
        cluctrl.mGetCmd.return_value = 'delete_service'
        cluctrl.mReturnDom0DomUPair.return_value = [('dom0-1', 'domu1')]
        node_a = MagicMock()
        node_a.dom0 = 'dom0-1'
        node_b = MagicMock()
        node_b.dom0 = 'dom0-2'

        with patch('exabox.ovm.clubonding.ebCluCmdCheckOptions',
                   return_value=True):
            result = clubonding.filter_nodes_by_cluctrl(
                cluctrl,
                [node_a, node_b]
            )

        self.assertEqual([node_a], result)

    # Auto-generated test for create_bonded_bridge
    def test_create_bonded_bridge_raises_on_failure(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-3'
        bond_iface_conf = BondIfaceConf(
            bond_id=1,
            primary_interface='eth1',
            secondary_interface='eth2',
            ip_addr=IPv4Interface('10.0.0.10/24').ip,
            netmask=IPv4Interface('10.0.0.10/24').netmask,
            gateway=IPv4Address('10.0.0.1')
        )
        cmd_result = MagicMock(exit_code=1, stdout='out', stderr='err')

        with patch('exabox.ovm.clubonding.node_exec_cmd',
                   return_value=cmd_result):
            with self.assertRaises(ExacloudRuntimeError):
                clubonding.create_bonded_bridge(
                    node,
                    bond_iface_conf,
                    is_kvm=False
                )

    # Auto-generated test for create_static_bonded_bridge
    def test_create_static_bonded_bridge_wraps_exceptions(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-4'
        bond_iface_conf = BondIfaceConf(
            bond_id=1,
            primary_interface='eth1',
            secondary_interface='eth2',
            ip_addr=IPv4Interface('10.0.0.20/24').ip,
            netmask=IPv4Interface('10.0.0.20/24').netmask,
            gateway=IPv4Address('10.0.0.1')
        )

        with patch('exabox.ovm.clubonding.delete_bonded_bridge'), \
             patch('exabox.ovm.clubonding.build_bonded_bridge_ipconf_xml',
                   return_value='<xml/>'), \
             patch('exabox.ovm.clubonding.node_write_text_file'), \
             patch('exabox.ovm.clubonding.node_exec_cmd_check',
                   side_effect=Exception('fail')):
            with self.assertRaises(ExacloudRuntimeError):
                clubonding.create_static_bonded_bridge(
                    node,
                    bond_iface_conf,
                    is_kvm=False
                )

    # Auto-generated test for create_static_bonded_bridge
    def test_create_static_bonded_bridge_success(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-success'
        bond_iface_conf = BondIfaceConf(
            bond_id=2,
            primary_interface='eth1',
            secondary_interface='eth2',
            ip_addr=IPv4Interface('10.1.0.10/24').ip,
            netmask=IPv4Interface('10.1.0.10/24').netmask,
            gateway=IPv4Address('10.1.0.1')
        )
        bridge_iface = 'vmbondeth2'
        remote_path = clubonding.REMOTE_IPCONF_XML_FMT.format(bridge_iface)
        expected_cmd = f"{clubonding.REMOTE_IPCONF_CMD} -conf-add {remote_path}"

        with patch('exabox.ovm.clubonding.delete_bonded_bridge') as mock_delete, \
             patch('exabox.ovm.clubonding.build_bonded_bridge_ipconf_xml',
                   return_value='<xml/>') as mock_build_xml, \
             patch('exabox.ovm.clubonding.node_write_text_file') as mock_write, \
             patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_exec:
            mock_exec.return_value = MagicMock(stdout='', exit_code=0, stderr='')

            clubonding.create_static_bonded_bridge(
                node,
                bond_iface_conf,
                is_kvm=False
            )

        mock_delete.assert_called_once_with(node, bond_iface_conf, False)
        mock_build_xml.assert_called_once_with(
            'dom0-success',
            'bondeth2',
            'vmbondeth2',
            bond_iface_conf
        )
        mock_write.assert_called_once_with(node, remote_path, '<xml/>')
        mock_exec.assert_called_once_with(
            node,
            expected_cmd,
            log_stdout_on_error=True
        )

    # Auto-generated test for create_static_bonded_bridge
    def test_create_static_bonded_bridge_success(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-success'
        bond_iface_conf = BondIfaceConf(
            bond_id=2,
            primary_interface='eth1',
            secondary_interface='eth2',
            ip_addr=IPv4Interface('10.1.0.10/24').ip,
            netmask=IPv4Interface('10.1.0.10/24').netmask,
            gateway=IPv4Address('10.1.0.1')
        )

        bridge_iface = 'vmbondeth2'
        remote_path = clubonding.REMOTE_IPCONF_XML_FMT.format(bridge_iface)
        expected_cmd = f"{clubonding.REMOTE_IPCONF_CMD} -conf-add {remote_path}"

        with patch('exabox.ovm.clubonding.delete_bonded_bridge') as mock_delete, \
             patch('exabox.ovm.clubonding.build_bonded_bridge_ipconf_xml',
                   return_value='<xml/>') as mock_build_xml, \
             patch('exabox.ovm.clubonding.node_write_text_file') as mock_write, \
             patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_exec:
            mock_exec.return_value = MagicMock(stdout='', exit_code=0, stderr='')

            clubonding.create_static_bonded_bridge(
                node,
                bond_iface_conf,
                is_kvm=False
            )

        mock_delete.assert_called_once_with(node, bond_iface_conf, False)
        mock_build_xml.assert_called_once_with(
            'dom0-success',
            'bondeth2',
            'vmbondeth2',
            bond_iface_conf
        )
        mock_write.assert_called_once_with(node, remote_path, '<xml/>')
        mock_exec.assert_called_once_with(
            node,
            expected_cmd,
            log_stdout_on_error=True
        )

    # Auto-generated test for get_interface_mac_address
    def test_get_interface_mac_address_reads_file(self):
        node = MagicMock()

        with patch('exabox.ovm.clubonding.node_read_text_file',
                   return_value='aa:bb\n') as mock_read:
            result = clubonding.get_interface_mac_address(node, 'eth0')

        self.assertEqual('aa:bb', result)
        mock_read.assert_called_once()

    # Auto-generated test for save_cavium_info
    def test_save_cavium_info_writes_primary_and_backup(self):
        node = MagicMock()
        cavium_info = '{"key": "value"}'

        with patch('exabox.ovm.clubonding.node_write_text_file') as mock_write:
            clubonding.save_cavium_info(node, cavium_info)

        expected_calls = [
            call(node, clubonding.REMOTE_MONITOR_CAVIUM_INFO_FILE, cavium_info),
            call(node, clubonding.REMOTE_MONITOR_CAVIUM_INFO_BK_FILE, cavium_info)
        ]
        mock_write.assert_has_calls(expected_calls)
        self.assertEqual(2, mock_write.call_count)

    # Auto-generated test for configure_bond_monitor
    def test_configure_bond_monitor_admin_updates_admin_conf(self):
        cluctrl = MagicMock()
        node = MagicMock()
        cluctrl.isBaseDB.return_value = False
        bond_conf = clubonding_config.NodeBondingConf(
            dom0='dom0-5',
            domu='domu1',
            domu_client='domuclient1',
            domu_admin_ip='192.168.0.10',
            domu_admin_vlan=2,
            monitor_conf_type=clubonding_config.MonitorConfType.ADMIN,
            monitor_conf='{}',
            bond_iface_confs=[],
            bond_cavium_info=None
        )

        updated_bond_conf = bond_conf._replace(monitor_conf='{"monitor_admin": []}')

        with patch('exabox.ovm.clubonding.update_monitor_admin_conf',
                   return_value=updated_bond_conf) as mock_update, \
             patch('exabox.ovm.clubonding.add_remove_entry_monitor_admin_conf') as mock_add_remove, \
             patch('exabox.ovm.clubonding.node_write_text_file') as mock_write, \
             patch('exabox.ovm.clubonding.ebCluAcceleratedNetwork.isClusterEnabledWithAcceleratedNetwork',
                   return_value=False):
            clubonding.configure_bond_monitor(cluctrl, node, bond_conf)

        mock_update.assert_called_once_with(node, bond_conf)
        mock_add_remove.assert_called_once_with(
            node,
            bond_conf.domu_admin_ip,
            bond_conf.domu_admin_vlan,
            add=True
        )
        admin_calls = [
            call.args for call in mock_write.call_args_list
            if call.args[1] == clubonding.REMOTE_MONITOR_ADMIN_CONFIG_FILE
        ]
        self.assertEqual(1, len(admin_calls))
        admin_node, admin_path, admin_payload = admin_calls[0]
        self.assertIs(admin_node, node)
        self.assertEqual(admin_path, clubonding.REMOTE_MONITOR_ADMIN_CONFIG_FILE)
        self.assertEqual(
            json.loads(admin_payload),
            json.loads(updated_bond_conf.monitor_conf)
        )

        backup_calls = [
            call.args for call in mock_write.call_args_list
            if call.args[1] == clubonding.REMOTE_MONITOR_CONFIG_BK_FILE_FMT.format(bond_conf.domu)
        ]
        self.assertEqual(1, len(backup_calls))
        _, backup_path, backup_payload = backup_calls[0]
        self.assertEqual(
            backup_path,
            clubonding.REMOTE_MONITOR_CONFIG_BK_FILE_FMT.format(bond_conf.domu)
        )
        self.assertEqual(
            json.loads(backup_payload),
            json.loads(updated_bond_conf.monitor_conf)
        )

    # Auto-generated test for configure_bond_monitor
    def test_configure_bond_monitor_skips_for_accelerated_customer(self):
        cluctrl = MagicMock()
        node = MagicMock()
        bond_conf = clubonding_config.NodeBondingConf(
            dom0='dom0-6',
            domu='domu2',
            domu_client='domuclient2',
            domu_admin_ip='192.168.0.11',
            domu_admin_vlan=3,
            monitor_conf_type=clubonding_config.MonitorConfType.CUSTOMER,
            monitor_conf='{}',
            bond_iface_confs=[],
            bond_cavium_info=None
        )

        with patch('exabox.ovm.clubonding.add_remove_entry_monitor_admin_conf') as mock_add_remove, \
             patch('exabox.ovm.clubonding.node_write_text_file') as mock_write, \
             patch('exabox.ovm.clubonding.ebCluAcceleratedNetwork.isClusterEnabledWithAcceleratedNetwork',
                   return_value=True):
            clubonding.configure_bond_monitor(cluctrl, node, bond_conf)

        mock_add_remove.assert_called_once_with(
            node,
            bond_conf.domu_admin_ip,
            bond_conf.domu_admin_vlan,
            add=True
        )
        mock_write.assert_not_called()

    # Auto-generated test for configure_bond_monitor
    def test_configure_bond_monitor_unknown_type_raises(self):
        cluctrl = MagicMock()
        node = MagicMock()
        bond_conf = clubonding_config.NodeBondingConf(
            dom0='dom0-7',
            domu='domu3',
            domu_client=None,
            domu_admin_ip='192.168.0.12',
            domu_admin_vlan=4,
            monitor_conf_type='UNKNOWN',
            monitor_conf='{}',
            bond_iface_confs=[],
            bond_cavium_info=None
        )

        with self.assertRaises(ExacloudRuntimeError):
            clubonding.configure_bond_monitor(cluctrl, node, bond_conf)

    # Auto-generated test for run_operation_with_bond_utils_script
    def test_run_operation_with_bond_utils_script_missing_binary(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-8'
        node.mFileExists.return_value = False

        with patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_exec:
            with self.assertRaises(ExacloudRuntimeError):
                clubonding.run_operation_with_bond_utils_script(node, 'check_all')

        mock_exec.assert_not_called()

    # Auto-generated test for test_failover
    def test_test_failover_requires_active_monitor(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-9'

        with patch('exabox.ovm.clubonding.get_bond_monitor_status',
                   return_value=False), \
             patch('exabox.ovm.clubonding.run_operation_with_bond_utils_script'), \
             patch('exabox.ovm.clubonding.bring_up_interface_DOM0'):
            with self.assertRaises(ExacloudRuntimeError):
                clubonding.test_failover(node, 'eth1')

    # Auto-generated test for test_failover
    def test_test_failover_retries_and_failback(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-10'
        responses = [
            {'nodes': [{'node': 'dom0-10', 'active_slave': 'eth1'}]},
            {'nodes': [{'node': 'dom0-10', 'active_slave': 'eth2'}]},
            {'nodes': [{'node': 'dom0-10', 'active_slave': 'eth1'}]},
            {'nodes': [{'node': 'dom0-10', 'active_slave': 'eth1'}]}
        ]

        with patch('exabox.ovm.clubonding.get_bond_monitor_status',
                   return_value=True), \
             patch('exabox.ovm.clubonding.run_operation_with_bond_utils_script',
                   return_value='ok'), \
             patch('exabox.ovm.clubonding.bring_up_interface_DOM0') as mock_bring, \
             patch('exabox.ovm.clubonding.node_exec_cmd') as mock_exec, \
             patch('exabox.ovm.clubonding.getActiveNetworkInformation',
                   side_effect=responses), \
             patch('exabox.ovm.clubonding.time.sleep'):
            clubonding.test_failover(node, 'eth1', bounce_back=True)

        self.assertTrue(mock_bring.called)
        self.assertGreaterEqual(mock_exec.call_count, 4)

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_cleanup_invokes_cleanup(self):
        cluctrl = MagicMock()
        payload = {'nodes': ['dom0-11']}

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('cleanup', payload, True, True, {})), \
             patch('exabox.ovm.clubonding.cleanup_bonding_if_enabled') as mock_cleanup:
            clubonding.handle_bonding_operation(cluctrl)

        mock_cleanup.assert_called_once_with(
            cluctrl,
            payload,
            cleanup_bridge=True,
            cleanup_monitor=True
        )

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_install_monitor_success(self):
        cluctrl = MagicMock()
        payload = {'nodes': ['dom0-12']}
        dom_map = {'dom0-12': 'domu12'}
        node = MagicMock()
        node_ctx = MagicMock()
        node_ctx.__enter__.return_value = node
        node_ctx.__exit__.return_value = False

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('install_monitor', payload, False, False, dom_map)), \
             patch('exabox.ovm.clubonding.get_bond_monitor_rpm_local_path',
                   return_value='/tmp/bondmonitor.rpm'), \
             patch('exabox.ovm.clubonding.connect_to_host', return_value=node_ctx) as mock_connect, \
             patch('exabox.ovm.clubonding.node_create_bonding_dirs') as mock_dirs, \
             patch('exabox.ovm.clubonding.install_bond_monitor_rpm') as mock_install, \
             patch('exabox.ovm.clubonding.persist_stack_identifier') as mock_persist:
            clubonding.handle_bonding_operation(cluctrl)

        mock_connect.assert_called_once_with('dom0-12', cluctrl.mGetCtx())
        mock_dirs.assert_called_once_with(node)
        mock_install.assert_called_once_with(
            node,
            '/tmp/bondmonitor.rpm',
            domu=dom_map['dom0-12']
        )
        mock_persist.assert_called_once_with(node, payload, 'dom0-12')

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_smartnic_action(self):
        cluctrl = MagicMock()
        payload = {'node_id': 'dom0-16', 'operation': 'check_all'}

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('smartNIC_action', payload, False, False, {})), \
             patch('exabox.ovm.clubonding.connect_to_host') as mock_connect, \
             patch('exabox.ovm.clubonding.run_operation_with_bond_utils_script') as mock_run:
            ctx_mgr = MagicMock()
            node = MagicMock()
            ctx_mgr.__enter__.return_value = node
            ctx_mgr.__exit__.return_value = False
            mock_connect.return_value = ctx_mgr

            clubonding.handle_bonding_operation(cluctrl)

        mock_run.assert_called_once_with(node, 'check_all')

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_linkfailover_skips_when_already_desired(self):
        cluctrl = MagicMock()
        payload = {'nodes': ['dom0-17'], 'newactive': 'eth1'}

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('linkfailover', payload, False, False, {})), \
             patch('exabox.ovm.clubonding.connect_to_host') as mock_connect, \
             patch('exabox.ovm.clubonding.getActiveNetworkInformation',
                   return_value={'nodes': [{'node': 'dom0-17', 'active_slave': 'eth1'}]}), \
             patch('exabox.ovm.clubonding.test_failover') as mock_failover:
            ctx_mgr = MagicMock()
            node = MagicMock()
            ctx_mgr.__enter__.return_value = node
            ctx_mgr.__exit__.return_value = False
            mock_connect.return_value = ctx_mgr

            clubonding.handle_bonding_operation(cluctrl)

        mock_failover.assert_not_called()

    # Auto-generated test for test_failover
    def test_test_failover_raises_when_failover_never_switches(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-18'
        responses = [
            {'nodes': [{'node': 'dom0-18', 'active_slave': 'eth1'}]},
            {'nodes': [{'node': 'dom0-18', 'active_slave': 'eth1'}]}
        ]

        with patch('exabox.ovm.clubonding.get_bond_monitor_status',
                   return_value=True), \
             patch('exabox.ovm.clubonding.run_operation_with_bond_utils_script',
                   return_value='ok') as mock_run, \
             patch('exabox.ovm.clubonding.bring_up_interface_DOM0') as mock_bring, \
             patch('exabox.ovm.clubonding.node_exec_cmd'), \
             patch('exabox.ovm.clubonding.getActiveNetworkInformation',
                   side_effect=responses) as mock_get_active, \
             patch('exabox.ovm.clubonding.time.sleep'):
            with self.assertRaises(ExacloudRuntimeError):
                clubonding.test_failover(node, 'eth1')

        mock_run.assert_called_once_with(node, 'check_all')
        mock_bring.assert_any_call('eth2', node, None, 'dom0-18', aRaiseError=True)
        self.assertEqual(mock_get_active.call_count, 2)

    # Auto-generated test for test_failover
    def test_test_failover_returns_without_bounce_back(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-19'
        responses = [
            {'nodes': [{'node': 'dom0-19', 'active_slave': 'eth2'}]}
        ]

        with patch('exabox.ovm.clubonding.get_bond_monitor_status',
                   return_value=True), \
             patch('exabox.ovm.clubonding.run_operation_with_bond_utils_script',
                   return_value='ok'), \
             patch('exabox.ovm.clubonding.bring_up_interface_DOM0'), \
             patch('exabox.ovm.clubonding.node_exec_cmd'), \
             patch('exabox.ovm.clubonding.getActiveNetworkInformation',
                   side_effect=responses) as mock_get_active, \
             patch('exabox.ovm.clubonding.time.sleep'):
            clubonding.test_failover(node, 'eth1', bounce_back=False)

        mock_get_active.assert_called_once()

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_start_monitor_restarts_nodes(self):
        cluctrl = MagicMock()
        cluctrl.mGetCtx.return_value = MagicMock()
        payload = {'nodes': ['dom0-20', 'dom0-21']}
        node_a = MagicMock()
        node_b = MagicMock()
        ctx_mgr_a = MagicMock()
        ctx_mgr_a.__enter__.return_value = node_a
        ctx_mgr_a.__exit__.return_value = False
        ctx_mgr_b = MagicMock()
        ctx_mgr_b.__enter__.return_value = node_b
        ctx_mgr_b.__exit__.return_value = False

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('start_monitor', payload, False, False, {})), \
             patch('exabox.ovm.clubonding.connect_to_host') as mock_connect, \
             patch('exabox.ovm.clubonding.restart_bond_monitor') as mock_restart:
            mock_connect.side_effect = [ctx_mgr_a, ctx_mgr_b]

            clubonding.handle_bonding_operation(cluctrl)

        mock_restart.assert_has_calls([call(node_a), call(node_b)])
        mock_connect.assert_has_calls([
            call('dom0-20', cluctrl.mGetCtx()),
            call('dom0-21', cluctrl.mGetCtx())
        ])

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_stop_monitor_stops_nodes(self):
        cluctrl = MagicMock()
        cluctrl.mGetCtx.return_value = MagicMock()
        payload = {'nodes': ['dom0-22']}
        node = MagicMock()
        ctx_mgr = MagicMock()
        ctx_mgr.__enter__.return_value = node
        ctx_mgr.__exit__.return_value = False

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('stop_monitor', payload, False, False, {})), \
             patch('exabox.ovm.clubonding.connect_to_host', return_value=ctx_mgr) as mock_connect, \
             patch('exabox.ovm.clubonding.stop_bond_monitor') as mock_stop:
            clubonding.handle_bonding_operation(cluctrl)

        mock_stop.assert_called_once_with(node)
        mock_connect.assert_called_once_with('dom0-22', cluctrl.mGetCtx())

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_precheck_invokes_prechecks(self):
        cluctrl = MagicMock()
        payload = {'some': 'payload'}

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('precheck', payload, False, False, {})), \
             patch('exabox.ovm.clubonding.bonding_migration_prechecks') as mock_pre:
            clubonding.handle_bonding_operation(cluctrl)

        mock_pre.assert_called_once_with(cluctrl, payload)

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_status_monitor_updates_request(self):
        cluctrl = MagicMock()
        ctx = MagicMock()
        cluctrl.mGetCtx.return_value = ctx
        request = MagicMock()
        cluctrl.mGetRequestObj.return_value = request
        payload = {'nodes': {'dom0-23': ['domuA'], 'dom0-24': []}}
        dom_map = {}
        node_a = MagicMock()
        node_b = MagicMock()
        ctx_mgr_a = MagicMock()
        ctx_mgr_a.__enter__.return_value = node_a
        ctx_mgr_a.__exit__.return_value = False
        ctx_mgr_b = MagicMock()
        ctx_mgr_b.__enter__.return_value = node_b
        ctx_mgr_b.__exit__.return_value = False
        monitor_results = [
            {'healthy': True},
            {'healthy': False}
        ]
        db = MagicMock()

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('status_monitor', payload, False, False, dom_map)), \
             patch('exabox.ovm.clubonding.connect_to_host') as mock_connect, \
             patch('exabox.ovm.clubonding.monitor_consistency_check',
                   side_effect=monitor_results) as mock_check, \
             patch('exabox.ovm.clubonding.ebGetDefaultDB', return_value=db), \
             patch('exabox.ovm.clubonding.json.dumps', wraps=json.dumps) as mock_dumps:
            mock_connect.side_effect = [ctx_mgr_a, ctx_mgr_b]

            clubonding.handle_bonding_operation(cluctrl)

        self.assertEqual(mock_check.call_count, 2)
        mock_dumps.assert_called()
        request.mSetData.assert_called_once()
        db.mUpdateRequest.assert_called_once_with(request)

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_install_monitor_collects_failures(self):
        cluctrl = MagicMock()
        cluctrl.mGetCtx.return_value = MagicMock()
        payload = {'nodes': ['dom0-25']}
        dom_map = {'dom0-25': 'domu25'}
        node = MagicMock()
        ctx_mgr = MagicMock()
        ctx_mgr.__enter__.return_value = node
        ctx_mgr.__exit__.return_value = False

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('install_monitor', payload, False, False, dom_map)), \
             patch('exabox.ovm.clubonding.get_bond_monitor_rpm_local_path',
                   return_value='/tmp/bondmonitor.rpm'), \
             patch('exabox.ovm.clubonding.connect_to_host', return_value=ctx_mgr), \
             patch('exabox.ovm.clubonding.node_create_bonding_dirs'), \
             patch('exabox.ovm.clubonding.install_bond_monitor_rpm',
                   side_effect=Exception('install failed')):
            with self.assertRaises(ExacloudRuntimeError) as exc:
                clubonding.handle_bonding_operation(cluctrl)

        self.assertIn('dom0-25', str(exc.exception))



class TestBondingEdgeCaseCoverage(unittest.TestCase):

    # Auto-generated test for extract_bonding_operation_params
    def test_extract_bonding_operation_params_raises_when_not_supported(self):
        cluctrl = MagicMock()
        cluctrl.mCheckConfigOption.return_value = 'false'
        cluctrl.mGetArgsOptions.return_value = SimpleNamespace(
            bonding_action='setup',
            bonding_json='/tmp/payload.json',
            bonding_component='bridge',
            bonding_start_monitor=False
        )

        with patch('exabox.ovm.clubonding.is_bonding_supported', return_value=False):
            with self.assertRaises(ValueError) as exc:
                clubonding.extract_bonding_operation_params(cluctrl)

        self.assertIn('Bonding not supported', str(exc.exception))

    # Auto-generated test for extract_bonding_operation_params
    def test_extract_bonding_operation_params_invalid_action_raises(self):
        cluctrl = MagicMock()
        cluctrl.mReturnDom0DomUNATPair.return_value = []
        cluctrl.mGetArgsOptions.return_value = SimpleNamespace(
            bonding_action='invalid',
            bonding_json='/tmp/payload.json',
            bonding_component=None,
            bonding_start_monitor=False
        )

        with patch('exabox.ovm.clubonding.is_bonding_supported', return_value=True):
            with self.assertRaises(ValueError):
                clubonding.extract_bonding_operation_params(cluctrl)

    # Auto-generated test for extract_bonding_operation_params
    def test_extract_bonding_operation_params_missing_payload_raises(self):
        cluctrl = MagicMock()
        cluctrl.mReturnDom0DomUNATPair.return_value = []
        cluctrl.mGetArgsOptions.return_value = SimpleNamespace(
            bonding_action='setup',
            bonding_json='',
            bonding_component='bridge',
            bonding_start_monitor=False
        )

        with patch('exabox.ovm.clubonding.is_bonding_supported', return_value=True):
            with self.assertRaises(ValueError):
                clubonding.extract_bonding_operation_params(cluctrl)

    # Auto-generated test for extract_bonding_operation_params
    def test_extract_bonding_operation_params_invalid_component_raises(self):
        cluctrl = MagicMock()
        cluctrl.mReturnDom0DomUNATPair.return_value = []
        cluctrl.mGetArgsOptions.return_value = SimpleNamespace(
            bonding_action='setup',
            bonding_json='/tmp/payload.json',
            bonding_component='invalid',
            bonding_start_monitor=False
        )

        with patch('exabox.ovm.clubonding.is_bonding_supported', return_value=True):
            with self.assertRaises(ValueError):
                clubonding.extract_bonding_operation_params(cluctrl)

    # Auto-generated test for extract_bonding_operation_params
    def test_extract_bonding_operation_params_missing_component_for_setup(self):
        cluctrl = MagicMock()
        cluctrl.mReturnDom0DomUNATPair.return_value = []
        cluctrl.mGetArgsOptions.return_value = SimpleNamespace(
            bonding_action='setup',
            bonding_json='/tmp/payload.json',
            bonding_component=None,
            bonding_start_monitor=False
        )

        with patch('exabox.ovm.clubonding.is_bonding_supported', return_value=True):
            with self.assertRaises(ValueError):
                clubonding.extract_bonding_operation_params(cluctrl)

    # Auto-generated test for extract_bonding_operation_params
    def test_extract_bonding_operation_params_returns_expected_tuple(self):
        cluctrl = MagicMock()
        cluctrl.mReturnDom0DomUNATPair.return_value = [('dom0-1', 'domu1')]
        cluctrl.mGetArgsOptions.return_value = SimpleNamespace(
            bonding_action='setup',
            bonding_json='/tmp/payload.json',
            bonding_component='all',
            bonding_start_monitor=True
        )

        with patch('exabox.ovm.clubonding.is_bonding_supported', return_value=True):
            result = clubonding.extract_bonding_operation_params(cluctrl)

        self.assertEqual('setup', result[0])
        self.assertEqual('/tmp/payload.json', result[1])
        self.assertTrue(result[2])
        self.assertTrue(result[3])
        self.assertEqual({'dom0-1': 'domu1'}, result[4])

    # Auto-generated test for extract_bonding_operation_params
    def test_extract_bonding_operation_params_non_setup_defaults(self):
        cluctrl = MagicMock()
        cluctrl.mReturnDom0DomUNATPair.return_value = [('dom0-2', 'domu2')]
        cluctrl.mGetArgsOptions.return_value = SimpleNamespace(
            bonding_action='install_monitor',
            bonding_json='/tmp/install.json',
            bonding_component=None,
            bonding_start_monitor=False
        )

        with patch('exabox.ovm.clubonding.is_bonding_supported', return_value=True):
            action, payload_path, target_bridge, target_monitor, dom_map = (
                clubonding.extract_bonding_operation_params(cluctrl)
            )

        self.assertEqual('install_monitor', action)
        self.assertEqual('/tmp/install.json', payload_path)
        self.assertFalse(target_bridge)
        self.assertFalse(target_monitor)
        self.assertEqual({'dom0-2': 'domu2'}, dom_map)

    # Auto-generated test for remove_cavium_info
    def test_remove_cavium_info_invokes_remote_cleanup(self):
        node = MagicMock()

        with patch('exabox.ovm.clubonding.node_exec_cmd') as mock_exec:
            clubonding.remove_cavium_info(node)

        mock_exec.assert_called_once_with(
            node,
            f"/bin/rm -f {clubonding.REMOTE_MONITOR_CAVIUM_INFO_FILE}",
            log_warning=True
        )

    # Auto-generated test for validate_bonding_config
    def test_validate_bonding_config_missing_attribute_branch(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-missing'

        with patch('exabox.ovm.clubonding.read_bond_interface_atr',
                   return_value=''):
            result = clubonding.validate_bonding_config(
                node,
                'bondeth0',
                {'arp_interval': '1000'}
            )

        self.assertFalse(result)

    # Auto-generated test for validate_bonding_config
    def test_validate_bonding_config_suffixed_attribute_single_value(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-suffix'

        with patch('exabox.ovm.clubonding.read_bond_interface_atr',
                   return_value='fail_over_mac=1'):
            result = clubonding.validate_bonding_config(
                node,
                'bondeth0',
                {'fail_over_mac': '1'}
            )

        self.assertFalse(result)

    # Auto-generated test for validate_bridge_config
    def test_validate_bridge_config_handles_missing_actual_value(self):
        node = MagicMock()
        actual = {
            'IPADDR': '10.0.0.1',
            'NETMASK': '255.255.255.0',
            'ARPCHECK': '',
            'MTU': '9000'
        }

        with patch('exabox.ovm.clubonding.read_bridge_interface_attrs',
                   return_value=actual):
            result = clubonding.validate_bridge_config(
                node,
                'vmbondeth0',
                {'arpcheck': 'yes'}
            )

        self.assertFalse(result)

    # Auto-generated test for validate_bridge_config
    def test_validate_bridge_config_detects_ip_and_netmask_mismatch(self):
        node = MagicMock()
        expected = {
            'ipaddr': '10.0.0.10',
            'netmask': '255.255.255.0'
        }
        actual = {
            'IPADDR': '10.0.0.11',
            'NETMASK': '255.255.0.0'
        }

        with patch('exabox.ovm.clubonding.read_bridge_interface_attrs',
                   return_value=actual):
            result = clubonding.validate_bridge_config(
                node,
                'vmbondeth0',
                expected
            )

        self.assertFalse(result)

    # Auto-generated test for filter_nodes_by_cluctrl
    def test_filter_nodes_by_cluctrl_filters_matching_dom0(self):
        cluctrl = MagicMock()
        cluctrl.mGetCmd.return_value = 'delete_service'
        cluctrl.mReturnDom0DomUPair.return_value = [('dom0-keep', 'domu1')]
        nodes = [
            SimpleNamespace(dom0='dom0-keep'),
            SimpleNamespace(dom0='dom0-drop')
        ]

        with patch('exabox.ovm.clubonding.ebCluCmdCheckOptions',
                   return_value=True):
            result = clubonding.filter_nodes_by_cluctrl(cluctrl, nodes)

        self.assertEqual([nodes[0]], result)

    # Auto-generated test for create_bonded_bridge
    def test_create_bonded_bridge_error_path_raises(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-error'
        bond_iface_conf = BondIfaceConf(
            bond_id=1,
            primary_interface='eth1',
            secondary_interface='eth2',
            ip_addr=IPv4Interface('10.0.0.1/24').ip,
            netmask=IPv4Interface('10.0.0.1/24').netmask,
            gateway=IPv4Address('10.0.0.254')
        )
        cmd_result = MagicMock(exit_code=1, stdout='out', stderr='err')

        with patch('exabox.ovm.clubonding.node_exec_cmd', return_value=cmd_result):
            with self.assertRaises(ExacloudRuntimeError):
                clubonding.create_bonded_bridge(node, bond_iface_conf, False)

    # Auto-generated test for create_static_bonded_bridge
    def test_create_static_bonded_bridge_wraps_exception_path(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-static'
        bond_iface_conf = BondIfaceConf(
            bond_id=2,
            primary_interface='eth1',
            secondary_interface='eth2',
            ip_addr=IPv4Interface('10.0.0.2/24').ip,
            netmask=IPv4Interface('10.0.0.2/24').netmask,
            gateway=IPv4Address('10.0.0.254')
        )

        with patch('exabox.ovm.clubonding.delete_bonded_bridge'), \
             patch('exabox.ovm.clubonding.build_bonded_bridge_ipconf_xml',
                   return_value='<xml/>'), \
             patch('exabox.ovm.clubonding.node_write_text_file'), \
             patch('exabox.ovm.clubonding.node_exec_cmd_check',
                   side_effect=Exception('boom')):
            with self.assertRaises(ExacloudRuntimeError):
                clubonding.create_static_bonded_bridge(node, bond_iface_conf, False)

    # Auto-generated test for save_cavium_info
    def test_save_cavium_info_writes_primary_and_backup_files(self):
        node = MagicMock()
        with patch('exabox.ovm.clubonding.node_write_text_file') as mock_write:
            clubonding.save_cavium_info(node, '{"key": "value"}')

        expected_calls = [
            call(node, clubonding.REMOTE_MONITOR_CAVIUM_INFO_FILE, '{"key": "value"}'),
            call(node, clubonding.REMOTE_MONITOR_CAVIUM_INFO_BK_FILE, '{"key": "value"}')
        ]
        mock_write.assert_has_calls(expected_calls)

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_cleanup_path(self):
        cluctrl = MagicMock()
        payload = {'nodes': []}

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('cleanup', payload, True, False, {})), \
             patch('exabox.ovm.clubonding.cleanup_bonding_if_enabled') as mock_cleanup:
            clubonding.handle_bonding_operation(cluctrl)

        mock_cleanup.assert_called_once_with(
            cluctrl,
            payload,
            cleanup_bridge=True,
            cleanup_monitor=False
        )

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_install_monitor_persists_state(self):
        cluctrl = MagicMock()
        cluctrl.mGetCtx.return_value = MagicMock()
        payload = {'nodes': ['dom0-1']}
        dom_map = {'dom0-1': 'domu1'}
        node = MagicMock()
        ctx_mgr = MagicMock()
        ctx_mgr.__enter__.return_value = node
        ctx_mgr.__exit__.return_value = False

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('install_monitor', payload, False, False, dom_map)), \
             patch('exabox.ovm.clubonding.get_bond_monitor_rpm_local_path',
                   return_value='/tmp/rpm'), \
             patch('exabox.ovm.clubonding.connect_to_host', return_value=ctx_mgr) as mock_connect, \
             patch('exabox.ovm.clubonding.node_create_bonding_dirs') as mock_dirs, \
             patch('exabox.ovm.clubonding.install_bond_monitor_rpm') as mock_install, \
             patch('exabox.ovm.clubonding.persist_stack_identifier') as mock_persist:
            clubonding.handle_bonding_operation(cluctrl)

        mock_connect.assert_called_once_with('dom0-1', cluctrl.mGetCtx())
        mock_dirs.assert_called_once_with(node)
        mock_install.assert_called_once_with(node, '/tmp/rpm', domu='domu1')
        mock_persist.assert_called_once_with(node, payload, 'dom0-1')

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_start_monitor_path(self):
        cluctrl = MagicMock()
        cluctrl.mGetCtx.return_value = MagicMock()
        payload = {'nodes': ['dom0-start']}
        node = MagicMock()
        ctx_mgr = MagicMock()
        ctx_mgr.__enter__.return_value = node
        ctx_mgr.__exit__.return_value = False

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('start_monitor', payload, False, False, {})), \
             patch('exabox.ovm.clubonding.connect_to_host', return_value=ctx_mgr) as mock_connect, \
             patch('exabox.ovm.clubonding.restart_bond_monitor') as mock_restart:
            clubonding.handle_bonding_operation(cluctrl)

        mock_connect.assert_called_once_with('dom0-start', cluctrl.mGetCtx())
        mock_restart.assert_called_once_with(node)

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_stop_monitor_path(self):
        cluctrl = MagicMock()
        cluctrl.mGetCtx.return_value = MagicMock()
        payload = {'nodes': ['dom0-stop']}
        node = MagicMock()
        ctx_mgr = MagicMock()
        ctx_mgr.__enter__.return_value = node
        ctx_mgr.__exit__.return_value = False

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('stop_monitor', payload, False, False, {})), \
             patch('exabox.ovm.clubonding.connect_to_host', return_value=ctx_mgr) as mock_connect, \
             patch('exabox.ovm.clubonding.stop_bond_monitor') as mock_stop:
            clubonding.handle_bonding_operation(cluctrl)

        mock_connect.assert_called_once_with('dom0-stop', cluctrl.mGetCtx())
        mock_stop.assert_called_once_with(node)

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_consistency_check_invocation(self):
        cluctrl = MagicMock()
        cluctrl.mGetCtx.return_value = MagicMock()
        payload = {
            'nodes': ['dom0-consistency'],
            'isprovisioned': True,
            'customvips': {'value': 1}
        }
        dom_map = {'dom0-consistency': 'domu-consistency'}
        node = MagicMock()
        ctx_mgr = MagicMock()
        ctx_mgr.__enter__.return_value = node
        ctx_mgr.__exit__.return_value = False

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('consistency_check', payload, False, False, dom_map)), \
             patch('exabox.ovm.clubonding.connect_to_host', return_value=ctx_mgr) as mock_connect, \
             patch('exabox.ovm.clubonding.bonding_consistency_check') as mock_check:
            clubonding.handle_bonding_operation(cluctrl)

        mock_connect.assert_called_once_with('dom0-consistency', cluctrl.mGetCtx())
        mock_check.assert_called_once_with(
            node,
            domu='domu-consistency',
            custom_vips={'value': 1}
        )

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_smartnic_action_invokes_script(self):
        cluctrl = MagicMock()
        cluctrl.mGetCtx.return_value = MagicMock()
        payload = {'node_id': 'dom0-smart', 'operation': 'check_all'}
        node = MagicMock()
        ctx_mgr = MagicMock()
        ctx_mgr.__enter__.return_value = node
        ctx_mgr.__exit__.return_value = False

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('smartNIC_action', payload, False, False, {})), \
             patch('exabox.ovm.clubonding.connect_to_host', return_value=ctx_mgr) as mock_connect, \
             patch('exabox.ovm.clubonding.run_operation_with_bond_utils_script') as mock_run:
            clubonding.handle_bonding_operation(cluctrl)

        mock_connect.assert_called_once_with('dom0-smart', cluctrl.mGetCtx())
        mock_run.assert_called_once_with(node, 'check_all')

    # Auto-generated test for handle_bonding_operation
    def test_handle_bonding_operation_linkfailover_skips_when_desired(self):
        cluctrl = MagicMock()
        cluctrl.mGetCtx.return_value = MagicMock()
        payload = {'nodes': ['dom0-link'], 'newactive': 'eth1'}

        with patch('exabox.ovm.clubonding.extract_bonding_operation_params',
                   return_value=('linkfailover', payload, False, False, {})), \
             patch('exabox.ovm.clubonding.getActiveNetworkInformation',
                   return_value={'nodes': [{'node': 'dom0-link', 'active_slave': 'eth1'}]}), \
             patch('exabox.ovm.clubonding.test_failover') as mock_failover:
            clubonding.handle_bonding_operation(cluctrl)

        mock_failover.assert_not_called()

    # Auto-generated test for node_copy_file
    def test_node_copy_file_success(self):
        node = MagicMock()
        executor = SimpleNamespace(exit_code=0)

        with patch('exabox.ovm.clubonding.node_exec_cmd', return_value=executor) as mock_exec:
            result = clubonding.node_copy_file(
                node,
                '/tmp/src_file',
                '/var/tmp/dest/file.conf',
                overwrite=True
            )

        self.assertTrue(result)
        mock_exec.assert_called_once()
        _, cmd = mock_exec.call_args[0]
        self.assertIn('/bin/mkdir -p /var/tmp/dest', cmd)
        self.assertIn('/bin/cp -f', cmd)
        self.assertTrue(mock_exec.call_args.kwargs.get('log_error'))

    # Auto-generated test for node_copy_file
    def test_node_copy_file_failure_without_overwrite(self):
        node = MagicMock()
        executor = SimpleNamespace(exit_code=1)

        with patch('exabox.ovm.clubonding.node_exec_cmd', return_value=executor) as mock_exec:
            result = clubonding.node_copy_file(
                node,
                '/tmp/src_file',
                '/var/tmp/dest/file.conf',
                overwrite=False
            )

        self.assertFalse(result)
        _, cmd = mock_exec.call_args[0]
        self.assertIn('/bin/cp -n', cmd)

    # Auto-generated test for read_bond_interface_atr
    def test_read_bond_interface_atr_uses_mtu_path(self):
        node = MagicMock()

        with patch('exabox.ovm.clubonding.node_cmd_abs_path_check', return_value='/bin/cat') as mock_cmd, \
             patch('exabox.ovm.clubonding.node_exec_cmd',
                   return_value=SimpleNamespace(stdout='9100\n')) as mock_exec:
            result = clubonding.read_bond_interface_atr(node, 'bondeth0', 'MTU')

        self.assertEqual('9100', result)
        mock_cmd.assert_called_once_with(node, 'cat')
        self.assertIn('/sys/class/net/bondeth0/mtu', mock_exec.call_args[0][1])

    # Auto-generated test for read_bond_interface_atr
    def test_read_bond_interface_atr_uses_bonding_dir_for_other_attrs(self):
        node = MagicMock()

        with patch('exabox.ovm.clubonding.node_cmd_abs_path_check', return_value='/bin/cat') as mock_cmd, \
             patch('exabox.ovm.clubonding.node_exec_cmd',
                   return_value=SimpleNamespace(stdout='primary eth1\n')) as mock_exec:
            result = clubonding.read_bond_interface_atr(node, 'bondeth0', 'primary')

        self.assertEqual('primary eth1', result)
        mock_cmd.assert_called_once_with(node, 'cat')
        self.assertIn('/sys/class/net/bondeth0/bonding/primary', mock_exec.call_args[0][1])

    # Auto-generated test for read_bridge_interface_attrs
    def test_read_bridge_interface_attrs_returns_expected_dictionary(self):
        node = MagicMock()
        ip_output = SimpleNamespace(stdout='192.168.0.10/24\n')
        mtu_output = SimpleNamespace(stdout='9000\n')

        with patch('exabox.ovm.clubonding.node_cmd_abs_path_check',
                   side_effect=['/usr/sbin/ip', '/bin/awk', '/bin/grep', '/bin/cat']) as mock_paths, \
             patch('exabox.ovm.clubonding.node_exec_cmd_check',
                   side_effect=[ip_output, mtu_output]) as mock_exec_check, \
             patch('exabox.ovm.clubonding.node_exec_cmd',
                   return_value=SimpleNamespace(stdout='ARPCHECK=no\n')) as mock_exec:
            attrs = clubonding.read_bridge_interface_attrs(node, 'vmbondeth0')

        self.assertEqual(attrs['ARPCHECK'], 'no')
        self.assertEqual(attrs['IPADDR'], IPv4Address('192.168.0.10'))
        self.assertEqual(attrs['NETMASK'], IPv4Address('255.255.255.0'))
        self.assertEqual(attrs['MTU'], '9000')

        self.assertEqual(mock_paths.call_args_list,
                         [call(node, 'ip', sbin=True),
                          call(node, 'awk'),
                          call(node, 'grep'),
                          call(node, 'cat', sbin=False)])
        ip_cmd = mock_exec_check.call_args_list[0][0][1]
        self.assertIn('addr show vmbondeth0', ip_cmd)
        grep_cmd = mock_exec.call_args[0][1]
        self.assertIn('ARPCHECK', grep_cmd)

    # Auto-generated test for validate_bonding_config
    def test_validate_bonding_config_all_attributes_match(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-match'

        def fake_read(_node, _iface, attr):
            if attr == 'fail_over_mac':
                return 'fail_over_mac 1'
            if attr == 'primary':
                return 'eth1'
            return '1000'

        config = {
            'fail_over_mac': '1',
            'arp_interval': '1000',
            'primary': 'eth1'
        }

        with patch('exabox.ovm.clubonding.read_bond_interface_atr', side_effect=fake_read):
            result = clubonding.validate_bonding_config(node, 'bondeth0', config)

        self.assertTrue(result)

    # Auto-generated test for validate_bridge_config
    def test_validate_bridge_config_all_values_match(self):
        node = MagicMock()
        expected = {
            'ipaddr': '10.0.0.10',
            'netmask': '255.255.255.0',
            'arpcheck': 'no',
            'mtu': '9000'
        }
        actual = {
            'IPADDR': IPv4Address('10.0.0.10'),
            'NETMASK': IPv4Address('255.255.255.0'),
            'ARPCHECK': 'no',
            'MTU': '9000'
        }

        with patch('exabox.ovm.clubonding.read_bridge_interface_attrs', return_value=actual):
            result = clubonding.validate_bridge_config(node, 'vmbondeth0', expected)

        self.assertTrue(result)

    # Auto-generated test for patch_bond_bridge_ifcfg
    def test_patch_bond_bridge_ifcfg_cleanup_preserves_ip(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-cleanup'
        node.mFileExists.side_effect = lambda path: True

        bond_iface_conf = SimpleNamespace(
            bond_id=3,
            ip_addr=IPv4Address('10.0.0.2'),
            netmask=IPv4Address('255.255.255.0'),
            gateway=IPv4Address('10.0.0.1'),
            primary_interface='eth1',
            secondary_interface='eth2'
        )

        with patch('exabox.ovm.clubonding.validate_bonding_config', return_value=False), \
             patch('exabox.ovm.clubonding.validate_bridge_config', return_value=False), \
             patch('exabox.ovm.clubonding.node_update_key_val_file') as mock_update, \
             patch('exabox.ovm.clubonding.node_interface_down') as mock_down, \
             patch('exabox.ovm.clubonding.node_interface_up') as mock_up, \
             patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_exec_check, \
             patch('exabox.ovm.clubonding.get_gcontext') as mock_get_ctx:
            ctx = MagicMock()
            ctx.mGetConfigOptions.return_value = {
                'force_network_interfaces_reboot': 'false'
            }
            mock_get_ctx.return_value = ctx

            clubonding.patch_bond_bridge_ifcfg(
                node,
                bond_iface_conf,
                is_cleanup=True,
                restart_network=False,
                remove_bridge_ip_on_cleanup=False
            )

        bond_path = clubonding.BOND_IFCFG_PATH_FMT.format(3)
        bridge_path = clubonding.BRIDGE_IFCFG_PATH_FMT.format(3)

        mock_update.assert_any_call(node, bridge_path, {
            'IPADDR': str(bond_iface_conf.ip_addr),
            'NETMASK': str(bond_iface_conf.netmask)
        })
        mock_update.assert_any_call(node, bond_path, {
            'BONDING_OPTS': '"mode=active-backup miimon=100 downdelay=2000 updelay=5000 num_grat_arp=100"'
        })
        down_calls = [call(node, clubonding.BRIDGE_INTERFACE_FMT.format(3)),
                      call(node, clubonding.BOND_INTERFACE_FMT.format(3))]
        up_calls = [call(node, clubonding.BRIDGE_INTERFACE_FMT.format(3)),
                    call(node, clubonding.BOND_INTERFACE_FMT.format(3))]
        self.assertEqual(mock_down.call_args_list, down_calls)
        self.assertEqual(mock_up.call_args_list, up_calls)
        mock_exec_check.assert_not_called()
    # Auto-generated test for patch_bond_bridge_ifcfg
    def test_patch_bond_bridge_ifcfg_setup_updates_and_restarts(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-setup'
        node.mFileExists.side_effect = lambda path: True

        bond_iface_conf = SimpleNamespace(
            bond_id=4,
            ip_addr=IPv4Address('10.0.10.5'),
            netmask=IPv4Address('255.255.255.0'),
            gateway=IPv4Address('10.0.10.1'),
            primary_interface='eth3',
            secondary_interface='eth4'
        )

        with patch('exabox.ovm.clubonding.validate_bonding_config', return_value=False), \
             patch('exabox.ovm.clubonding.validate_bridge_config', return_value=False), \
             patch('exabox.ovm.clubonding.node_update_key_val_file') as mock_update, \
             patch('exabox.ovm.clubonding.node_interface_down') as mock_down, \
             patch('exabox.ovm.clubonding.node_interface_up') as mock_up, \
             patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_exec_check, \
             patch('exabox.ovm.clubonding.get_gcontext') as mock_get_ctx:
            ctx = MagicMock()
            ctx.mGetConfigOptions.return_value = {
                'force_network_interfaces_reboot': 'false'
            }
            mock_get_ctx.return_value = ctx

            clubonding.patch_bond_bridge_ifcfg(
                node,
                bond_iface_conf,
                is_cleanup=False,
                restart_network=False
            )

        bridge_path = clubonding.BRIDGE_IFCFG_PATH_FMT.format(4)
        bond_path = clubonding.BOND_IFCFG_PATH_FMT.format(4)
        bridge_vals = {
            'MTU': '9000',
            'IPADDR': str(bond_iface_conf.ip_addr),
            'NETMASK': str(bond_iface_conf.netmask),
            'ARPCHECK': 'no'
        }
        bond_vals = {
            'MTU': '9000',
            'BONDING_OPTS': '"mode=active-backup fail_over_mac=1 num_grat_arp=8 '
                            'arp_interval=1000 primary_reselect=failure arp_allslaves=1 '
                            f'arp_ip_target={bond_iface_conf.gateway} primary=eth3"'
        }
        self.assertIn(call(node, bridge_path, bridge_vals), mock_update.call_args_list)
        self.assertIn(call(node, bond_path, bond_vals), mock_update.call_args_list)

        expected_down = [
            call(node, clubonding.BRIDGE_INTERFACE_FMT.format(4)),
            call(node, clubonding.BOND_INTERFACE_FMT.format(4))
        ]
        expected_up = [
            call(node, clubonding.BRIDGE_INTERFACE_FMT.format(4)),
            call(node, clubonding.BOND_INTERFACE_FMT.format(4)),
            call(node, 'eth3'),
            call(node, 'eth4')
        ]
        self.assertEqual(mock_down.call_args_list, expected_down)
        self.assertEqual(mock_up.call_args_list, expected_up)
        mock_exec_check.assert_not_called()

    # Auto-generated test for create_bonded_bridge
    def test_create_bonded_bridge_success_non_kvm(self):
        node = MagicMock()
        node_exec_result = SimpleNamespace(exit_code=0, stdout='', stderr='')

        bond_iface_conf = SimpleNamespace(
            bond_id=5,
            primary_interface='eth1',
            secondary_interface='eth2'
        )

        with patch('exabox.ovm.clubonding.node_exec_cmd', return_value=node_exec_result) as mock_exec:
            clubonding.create_bonded_bridge(node, bond_iface_conf, is_kvm=False)

        expected_cmd = (
            '/opt/exadata_ovm/exadata.img.domu_maker remove-bridge-dom0 vmbondeth5'
            ' ; /opt/exadata_ovm/exadata.img.domu_maker add-bonded-bridge-dom0 '
            'vmbondeth5 eth1 eth2'
        )
        mock_exec.assert_called_once_with(node, expected_cmd)

    # Auto-generated test for create_bonded_bridge
    def test_create_bonded_bridge_success_kvm(self):
        node = MagicMock()
        node_exec_result = SimpleNamespace(exit_code=0, stdout='', stderr='')

        bond_iface_conf = SimpleNamespace(
            bond_id=6,
            primary_interface='peth1',
            secondary_interface='peth2'
        )

        with patch('exabox.ovm.clubonding.node_exec_cmd', return_value=node_exec_result) as mock_exec:
            clubonding.create_bonded_bridge(node, bond_iface_conf, is_kvm=True)

        expected_cmd = (
            '/opt/exadata_ovm/vm_maker --remove-bridge vmbondeth6'
            ' ; /opt/exadata_ovm/vm_maker --add-bonded-bridge vmbondeth6 '
            '--first-slave peth1 --second-slave peth2'
        )
        mock_exec.assert_called_once_with(node, expected_cmd)

    # Auto-generated test for create_static_bonded_bridge
    def test_create_static_bonded_bridge_success_kvm(self):
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-static'

        bond_iface_conf = SimpleNamespace(
            bond_id=7,
            primary_interface='eth9',
            secondary_interface='eth10',
            ip_addr=IPv4Address('10.2.0.5'),
            netmask=IPv4Address('255.255.255.0'),
            gateway=IPv4Address('10.2.0.1')
        )

        with patch('exabox.ovm.clubonding.delete_bonded_bridge') as mock_delete, \
             patch('exabox.ovm.clubonding.build_bonded_bridge_ipconf_xml', return_value='<xml/>') as mock_build, \
             patch('exabox.ovm.clubonding.node_write_text_file') as mock_write, \
             patch('exabox.ovm.clubonding.node_exec_cmd_check') as mock_exec:
            mock_exec.return_value = SimpleNamespace(stdout='', exit_code=0, stderr='')

            clubonding.create_static_bonded_bridge(node, bond_iface_conf, is_kvm=True)

        mock_delete.assert_called_once_with(node, bond_iface_conf, True)
        mock_build.assert_called_once()
        remote_xml = clubonding.REMOTE_IPCONF_XML_FMT.format('vmbondeth7')
        mock_write.assert_called_once_with(node, remote_xml, '<xml/>')
        mock_exec.assert_called_once_with(
            node,
            f"{clubonding.REMOTE_IPCONF_CMD} -conf-add {remote_xml}",
            log_stdout_on_error=True
        )


if __name__ == '__main__':
    unittest.main()
