"""
 Copyright (c) 2020, 2025, Oracle and/or its affiliates.

NAME:
    clubonding.py - Excloud  OCI Bonding implementation

DESCRIPTION:
    Configures bonding between eth1 and eth0 in OCI ATP and ExaBM environments.

    References:
      https://confluence.oraclecorp.com/confluence/display/EDCS/Bonding+Design

    Implementation relies on the availability of monitoring node entries in
    ECRA payload.  Additional information of the DomUs is required if we want
    to configure the bonding monitor in the Dom0s.  See clubonding_config.py
    for a description of the payload.

    This configuration is expected to be executed only in ATP and ExaBM
    environments.

    When bonding is configured in a Dom0 (see configure_bonding_if_enabled()),
    two sub-configurations take place:

    1. bondmonitor package is installed (daemon is not started by default).
       See function install_bond_monitor_rpm().

    2. Interfaces bondethX and vmbondethX are configured using information in
       the node's "monitoring.bondX" dictionary in the payload.  See function
       configure_bond_bridges().

    3. Optionally, the bondmonitor daemon is configured and started.  The
       configuration is created using all other information depicted in example
       payload as documented in clubonding_config.py that is not "monitoring".
       See function configure_bond_monitor().

    At cleanup (see cleanup_bonding_if_enabled()), we perform the reverse
    steps:

    1. Stop the monitor daemon and remove its configuration.  See function
       cleanup_bond_monitor_config().

    2. Revert interfaces bondethX and vmbondethX to their original state
       without bonding configuration.  See function cleanup_bond_bridges().

    3. Uninstall bondmonitor package.  See function
       uninstall_bond_monitor_rpm().

NOTES:
    - The public API of this module is conformed of following functions:

          configure_bonding_if_enabled()
          cleanup_bonding_if_enabled()
          handle_bonding_operation()
          is_bonding_supported()
          is_static_monitoring_bridge_supported()

      With the exception of testing, no other function/definition should be
      used outside this module.

    - If you change this file, please make sure lines are no longer than 80
      characters (including newline) and it passes pylint, mypy and flake8 with
      all the default checks enabled.

History:

    MODIFIED   (MM/DD/YY)
    scoral      11/26/25 - Bug 38699734 - Fixed json indent in
                           add_remove_entry_monitor_admin_conf.
    mpedapro    11/20/25 - Enh::38602758 bonding changes for accelerated
                           network enabled dom0s
    scoral      10/28/25 - Enh 38452359 - Implemented
                           add_remove_entry_monitor_admin_conf.
    kaggupta    09/29/25 - Enh 38335432 - SUPPORT FOR HANDLING THE STACK IDENTIFIER IN ECRA AND CONFIGURING IN KVM HOSTS
    bhpati      09/15/25 - Bug 38381325 - ERROR FAILED TO CREATE STATIC BONDED
                           BRIDGE VMBONDETH0.
    scoral      07/29/25 - Bug 38226814 - Remove workaround to manually setup
                           ksplice in the Dom0 during bonding bridge setup
                           since UEK bug 33352736 is already included in all
                           official Exadata releases in production envs.
    scoral      07/17/25 - Bug 38200446 - Keep bonding bridge IP during delete
                           bonding in non-eth0 environments.
    scoral      28/05/25 - Bug 37989871 - Ignore exabox.conf parameters, use
                           only Payload values to enable or disable bonding.
    abflores    03/19/25 - Bug 37604161: Fix unnecesary interfaces restart
    llmartin    02/19/25 - Bug 37595827 - Return active and inactive interfaces
                           in status endpoint
    bhpati      02/07/25 - Bug 37520825 - NJA1 | LAUNCHEXADBSYSTEM FAILED |
                           ERROR FAILED TO CREATE STATIC BONDED BRIDGE
                           VMBONDETH0
    akkar       01/21/25 - Bug 37487880: Parallelize bonding configuration
    zpallare    12/10/24 - Enh 37144837 - EXACS ECRA - Create an api to do
                           re-bonding of existing node and update
                           admin_monitor.json
    jesandov    11/12/24 - Bug 37248993 - Change set sysctl value of ksplice
    naps        10/24/24 - Bug 37192649 - Handle eth0 removal per node instead
                           of cluster wide.
    aararora    10/08/24 - Bug 37133558: Compare rpm versions of bondmonitor
                           rpm before updating the rpm
    aararora    10/04/24 - Bug 37133807: Get scan IPs for ipv6 from xml
    aararora    08/26/24 - Bug 36892583: Precheck for standby interface before
                           failover
    naps        08/14/24 - Bug 36949876 - X11 ipconf path changes.
    aararora    07/30/24 - Bug 36440760: Fix the link on the previous active
                           interface after failover
    jesandov    06/20/24 - Bug 36732647: Add filter of dom0s by XML information
    scoral      06/18/24 - Bug 36740875: Create a copy of the VM monitor files
                           inside the VM files directory.
    aararora    04/16/24 - ER 36485120: Support IPv6 in exacloud
    aararora    03/20/24 - Bug 33667094: Add Rollback Migration flow to list of
                           operations
    scoral      01/24/24 - Bug 36212842: Enhanced delete_bonded_bridge, now
                           it also removes any residual guests bridges.
    scoral      01/23/24 - Bug 36204364: Implemented a retry logic in
                           bonding_consistency_check during eth interfaces
                           check in case bond_utils.py doesn't leave the
                           interfaces up.
    aararora    01/22/24 - Bug 36207111: Install bond monitor should work for
                           DOM0s which are connectable.
    scoral      12/05/23 - Bug 36016531: Fail when eth interfaces are down
                           during bonding_consistency_check.
    scoral      11/24/23 - Enh 34992242: Implement "status_monitor" action.
    scoral      10/03/23 - Enh 35946456: Configure bondmonitor for envs with
                           eth0 removed during bonding setup.
    scoral      10/10/23 - Enh 35779476: Support eth0 removal.
    dekuckre    10/03/23 - 35858427: check for bond monitor to decide if bonding is supported.
    scoral      06/26/23 - Bug 35539565: remove the monitor RPM for bridge
                           cleanup.
    gparada     05/31/23 - 35111184 Allow to set active eth for bonding failover
    jesandov    05/26/23 - 35426921: Validate bonding_json as string and json
    scoral      05/24/23 - Bug 35285863: Increase arp_interval from 100 to 1000
    dekuckre    04/10/23 - 35241403: Check other bridges when deleting bonding
    scoral      03/13/23 - Bug 35147511: Support Custom VIPs setup even when
                           MVM migration hasn't been performed and bondmonitor
                           still supports the old config file path.
    dekuckre    12/09/22 - 34545343: Add support for link failover.
    scoral      12/16/22 - Enh 34865278: Implemented a new bonding action
                           consistency_check.
    aararora    12/13/22 - Delete compute needs to be handled for bonding
    scoral      11/29/22 - Bug 34743277: Always force the reinstallation of
                           the monitor RPM for each Create Service and Elastic
                           Add Compute.
    scoral      10/27/22 - Bug 34741231: Added strict_bridge_removal to the
                           exabox.conf
    aararora    10/13/22 - Expose bond_utils.py features in exacloud.
    scoral      09/28/22 - Bug 34646856: Update monitor JSON path on monitor
                           RPM upgrade.
    scoral      09/08/22 - Bug 34541001: Don't delete the current bridge in the
                           Dom0 for Bonding migration, just configure the
                           existing one.
    scoral      09/01/22 - Bug 34557231: Now we migrate the dynamic bridges to
                           static bridges just in case it's needed.
    scoral      08/26/22 - Bug 34538948: Implemented is_bonding_supported_dom0.
    scoral      08/24/22 - Bug 34482855: Implemented migrate_static_bridges.
    aypaul      08/17/22 - Bug#34500653 Mask sensitive information from
                           payload.
    scoral      08/10/22 - Enh 34429828: Cleanup monitor for all DomUs when
                           bonding config payload field is absent.
    scoral      07/28/22 - Bug 34430106: Build Custom VIPs config using DomU
                           Networks taken from current monitor config.
    scoral      07/15/22 - Bug 34390580: Implemented send_bond_monitor_garps
                           to avoid calling restart_bond_monitor.
    scoral      04/03/22 - Enh 34022930: add support for Custom VIPs setup
                           in Create-service and Elastic-reshape.
    jlombera    03/28/22 - Bug 34000208: properly handle clusterless XMLs in
                           is_static_monitoring_bridge_supported()
    jlombera    03/18/22 - Bug 33244220: add support for MultiVM
    jlombera    12/14/21 - Bug 33220812: add action "config_vip" to command
                           "bonding_operation
    jlombera    12/09/21 - Bug 33472503: restart monitor instead of start
    jlombera    11/08/21 - Bug 33484463: add runtime sysctl
                           ksplice_arp_allslaves=1
    jlombera    10/29/21 - Bug 33519515: add space between attributes in
                           BONDING_OPTS
    jlombera    10/04/21 - EHN 33427481: add "arp_allslaves=1" to BONDING_OPTS
    jlombera    08/23/21 - Bug 33252769: use initctl(8) to start/stop
                           bondmonitor in Upstart systems
    jlombera    08/19/21 - Enh 33027376: add action "install_monitor" to
                           command "bonding_operation
    jlombera    08/05/21 - Bug 33195995: skip bridge cleanup if ifcfg files are
                           missing
    jlombera    07/09/21 - Bug 32912942: add support for
                           CluCtrl.bonding_operation command
    jlombera    07/08/21 - Bug 33081442: mark VIPs as floating in bondmonitor
                           config
    jlombera    04/19/21 - Bug 32753598: handle 'standby_vnic_mac' from ECRA
                           payload
    jlombera    03/26/21 - Bug 32665421: check bonding is working after
                           configuration
    jlombera    03/26/21 - Bug 32676792: retrieve SSH keys per host
    jlombera    02/26/21 - Bug 32546908: ignore 'dom0_bonding' in payload
    jlombera    02/17/21 - Bug 31525380: add support for VMGI_RESHAPE payload
    jlombera    02/17/21 - Bug 32422373: use exadata's vm_maker to create
                           bonded-bridge
    jlombera    01/12/21 - Bug 32295581: support new multi-bond bonding payload
    jlombera    12/07/20 - Bug 32166259: use symlink to bondmonitor RPM
    jlombera    11/02/20 - Bug 31862187: configure vmbondeth0
    jlombera    08/14/20 - Bug 31727529: don't touch field BRIDGE in bonding
                           config file
    jimillan    05/06/20 - Creation
"""

# pylint: disable=too-many-lines

# Public API
__all__ = [
    'cleanup_bonding_if_enabled',
    'configure_bonding_if_enabled',
    'handle_bonding_operation',
    'is_bonding_supported',
    'is_static_monitoring_bridge_supported',
    'migrate_static_bridges',
    'is_bonding_supported_dom0'
]

import copy
import json
import os
import shlex
import time
from ipaddress import IPv4Address, IPv6Address, IPv4Interface
from typing import List, Mapping, Optional, Sequence, Tuple, TYPE_CHECKING
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.ovm.clubonding_config import (
    BondIfaceConf, MonitorBondCaviumInfo, MonitorConf, Payload, PayloadBondOp,
    build_bonded_bridge_ipconf_xml, extract_bonding_conf_from_payload,
    get_bonding_operation_from_payload, extract_networks_from_monitor_conf,
    NodeNetworkConf, NodeBondingConf, MonitorConfType
)
from exabox.ovm.clubonding_migration import bonding_migration_prechecks
from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogTrace, ebLogWarn
from exabox.network.NetworkUtils import NetworkUtils
from exabox.utils.node import (
    connect_to_host, node_cmd_abs_path_check,
    node_exec_cmd, node_exec_cmd_check, node_update_key_val_file,
    node_write_text_file, node_read_text_file
)

from exabox.utils.common import mask_keys_json
from exabox.ovm.clunetworkdetect import getActiveNetworkInformation
from exabox.config.Config import ebCluCmdCheckOptions
from exabox.ovm.clumisc import ebMiscFx
from exabox.ovm.cluacceleratednetwork import ebCluAcceleratedNetwork

# We need to import exaBoxCluCtrl for type annotations, but it will cause a
# cyclic-import at runtime.  Thus we import it only when type-checking.  We
# still need to define type exaBoxCluCtrl or pylint will complain, though, so
# we just make it an alias to 'object' when not type-checking.
if TYPE_CHECKING:
    from exabox.ovm.clucontrol import exaBoxCluCtrl
    from exabox.ovm.cluconfig import ebCluNetworkConfig
else:
    exaBoxCluCtrl = object  # pylint: disable=invalid-name
    ebCluNetworkConfig = object  # pylint: disable=invalid-name

#
# Auxiliary functions related to remote node operations
#

def node_copy_file(
        node: exaBoxNode,
        src_file: str,
        dest_file: str,
        overwrite: bool) -> bool:
    """Copy a file in a node to another location (in the same node).

    The destination directory will be created if it doesn't exist.

    :param node: node to operate on.
    :param src_file: file to copy.
    :param dest_file: destination file.
    :param overwrite: whether overwrite dest_file if it already exists.
    :returns: whether the copy succeeded.
    """
    dest_dir = shlex.quote(os.path.dirname(dest_file))
    src_file = shlex.quote(src_file)
    dest_file = shlex.quote(dest_file)

    if overwrite:
        cp_cmd = '/bin/cp -f'
    else:
        cp_cmd = '/bin/cp -n'

    cmd = f'/bin/mkdir -p {dest_dir} && {cp_cmd} {src_file} {dest_file}'

    ret = node_exec_cmd(node, cmd, log_error=True)

    return ret.exit_code == 0


def node_interface_down(node: exaBoxNode, interface: str) -> None:
    """Bring down a net interface in a node.

    :param node: node to oparate on.
    :param interface: interface to bring down (e.g. 'bondeth0').
    :returns: nothing.
    :raises ExacloudRuntimeError: if an error occurred.
    """
    cmd = f'/sbin/ifdown {interface}'
    node_exec_cmd_check(node, cmd)


def node_interface_up(node: exaBoxNode, interface: str) -> None:
    """Bring up a net interface in a node.

    :param node: node to oparate on.
    :param interface: interface to bring up (e.g. 'bondeth0').
    :returns: nothing.
    :raises ExacloudRuntimeError: if an error occurred.
    """
    cmd = f'/sbin/ifup {interface}'
    node_exec_cmd_check(node, cmd)

def read_bond_interface_atr(node: exaBoxNode, interface: str, attr: str) -> str:
    """Read bond interface attribute
    
    :param node: node to oparate on.
    :param interface: interface to get from (e.g. 'bondeth0').
    :param attr: the attribute to get
    :returns: attribute found.
    :raises ExacloudRuntimeError: if an error occurred.
    """
    attr = attr.lower()

    bin_cat = node_cmd_abs_path_check(node, "cat")

    if attr == "mtu":
        cmd = f'{bin_cat} /sys/class/net/{interface}/{attr}'
    else:
        cmd = f'{bin_cat} /sys/class/net/{interface}/bonding/{attr}'
    
    ret = node_exec_cmd(node, cmd)

    return ret.stdout.strip()

def read_bridge_interface_attrs(node: exaBoxNode, interface: str) -> dict:
    """Read all bridge interface attributes
    
    :param node: node to oparate on.
    :param interface: interface to get from (e.g. 'vmbondeth0').
    :returns: attributes found.
    :raises ExacloudRuntimeError: if an error occurred.
    """
    attrs = {}

    ip_path = node_cmd_abs_path_check(node, 'ip', sbin=True)
    awk_path = node_cmd_abs_path_check(node, 'awk')

    ip_cmd = f"{ip_path} -o -4 addr show {interface} | {awk_path} '/scope global/ {{print $4}}'"

    ip_ret = node_exec_cmd_check(node, ip_cmd)
    ip_ret = ip_ret.stdout.strip()  

    ebLogInfo(f'IP found in {interface}: {ip_ret}')

    ip_addres = IPv4Interface(ip_ret)

    attrs["IPADDR"]  = ip_addres.ip
    attrs["NETMASK"] = ip_addres.netmask

    bin_grep = node_cmd_abs_path_check(node, "grep")

    arp_cmd = f"{bin_grep} ARPCHECK /etc/sysconfig/network-scripts/ifcfg-{interface}"

    arp_ret = node_exec_cmd(node, arp_cmd)
    arp_ret = arp_ret.stdout.strip()
    
    arp = arp_ret.split("=")

    ebLogInfo(f'ARP found in {interface}: {arp[1]}')

    attrs["ARPCHECK"] = arp[1]

    bin_cat = node_cmd_abs_path_check(node, "cat", sbin=False)

    mtu_cmd = f'{bin_cat} /sys/class/net/{interface}/mtu'

    mtu_ret = node_exec_cmd_check(node, mtu_cmd)
    mtu_ret = mtu_ret.stdout.strip()

    attrs["MTU"] = mtu_ret

    return attrs


def validate_bonding_config(node: exaBoxNode, 
                            interface: str, 
                            config: dict) -> bool:
    """Validates actual network interface config
    
    :param node: node to operate on.
    :param interface: interface to get from (e.g. 'bondeth0').
    :param config: expected values
    :returns: validation success
    :raises ExacloudRuntimeError: if an error occurred.
    """
    success = True

    #These are attributes that have prefixes in their files
    suffixed_attr = {"fail_over_mac", "arp_allslaves"} 
    
    for attr, valueExpected in config.items():
        actual_value = read_bond_interface_atr(node, interface, attr).split()
        if not actual_value:
            ebLogError(f"Bonding value {attr} not found for {node.mGetHostname()}")
            success = False
            continue

        if attr in suffixed_attr:
            if len(actual_value) == 1:
                ebLogWarn(f"BONDING Value checks: {node.mGetHostname()}: {attr} is not matching")
                ebLogWarn(f"BONDING Value expected {valueExpected} found {actual_value}")
                success = False
                continue

            actual_value = actual_value[1]
        else:
            actual_value = actual_value[0]

        if actual_value != valueExpected:
            ebLogWarn(f"BONDING Value checks: {node.mGetHostname()}: {attr} is not matching")
            ebLogWarn(f"BONDING Value expected {valueExpected} found {actual_value}")
            success = False
    
    return success

def validate_bridge_config(node: exaBoxNode, 
                            interface: str, 
                            configExpected: dict) -> bool:
    """Validates actual network interface config
    
    :param node: node to operate on.
    :param interface: interface to get from (e.g. 'vmbondeth0').
    :param configExpected: expected values
    :returns: validation success
    :raises ExacloudRuntimeError: if an error occurred.
    """
    success = True

    try:
        config_found = read_bridge_interface_attrs(node, interface)
    except Exception as e:
        ebLogError(f"Unexpected exception found while getting bridge interface data {e}")
        return False

    for key, valueExpected in configExpected.items():
        actual_value = config_found[key.upper()]

        if not actual_value:
            ebLogWarn(f"{key} not found for bridge interface")
            success = False
            continue

        if key.upper() in ["IPADDR", "NETMASK"]:
            if key.upper() == "IPADDR":
                expected_ip = IPv4Address(valueExpected)
                actual_ip = IPv4Address(actual_value)
                if expected_ip != actual_ip:
                    ebLogWarn(f"BRIDGE Value checks: {node.mGetHostname()}")
                    ebLogWarn(f"Bridge {key} is not matching, expected {expected_ip} found {actual_ip}")
                    success = False
                
            elif key.upper() == "NETMASK":
                expected_netmask = IPv4Address(valueExpected)
                actual_netmask = IPv4Address(actual_value)
                if expected_netmask != actual_netmask:
                    ebLogWarn(f"BRIDGE Value checks: {node.mGetHostname()}")
                    ebLogWarn(f"Bridge {key} is not matching, expected {expected_netmask} found {actual_netmask}")
                    success = False

        else:
            if valueExpected != actual_value:
                ebLogWarn(f"BRIDGE Value checks: {node.mGetHostname()}")
                ebLogWarn(f"Bridge {key} is not matching, expected {valueExpected} found {actual_value}")
                success = False

    return success

#
#  Bonding configuration logic
#


# Bonding ifcfg-files config constants
BOND_INTERFACE_FMT = 'bondeth{}'
BRIDGE_INTERFACE_FMT = 'vmbondeth{}'
IFCFG_DIR = '/etc/sysconfig/network-scripts'
BOND_IFCFG_PATH_FMT = f'{IFCFG_DIR}/ifcfg-bondeth{{}}'
BRIDGE_IFCFG_PATH_FMT = f'{IFCFG_DIR}/ifcfg-vmbondeth{{}}'
DOMU_CLIENT_INTERFACE = 'bondeth0'
DOMU_BACKUP_INTERFACE = 'bondeth1'
DOMU_CLIENT_IFCFG_PATH = f'{IFCFG_DIR}/ifcfg-{DOMU_CLIENT_INTERFACE}'
DOMU_BACKUP_IFCFG_PATH = f'{IFCFG_DIR}/ifcfg-{DOMU_BACKUP_INTERFACE}'
SYSTEM_NET_BACKUP_DIR = \
    '/opt/oracle.cellos/conf/network-scripts/backup_by_Exadata_ipconf'
REMOTE_BONDING_DIR = '/opt/exacloud/bonding'
REMOTE_MONITOR_DIR = '/opt/exacloud/bondmonitor'
REMOTE_BACKUP_DIR = f'{REMOTE_BONDING_DIR}/backup'
REMOTE_BONDING_STATE_FILE = f'{REMOTE_BONDING_DIR}/config_state'
REMOTE_IPCONF_CMD = "/usr/local/bin/ipconf"
REMOTE_IPCONF_XML_FMT = f"{REMOTE_BONDING_DIR}/{{}}_ipconf.xml"
REMOTE_MONITOR_LINK_CMD = f'{REMOTE_MONITOR_DIR}/monitor_link.py'
REMOTE_BOND_UTILS_CMD = f'{REMOTE_MONITOR_DIR}/bond_utils.py'


# Bonding monitor-related config constants
LOCAL_MONITOR_RPM_FILE = 'images/bondmonitor.x86_64.rpm'
MONITOR_RPM_PACKAGE_NAME = 'bondmonitor'
MONITOR_RPM_FILE_GLOB = 'bondmonitor*.x86_64.rpm'
MONITOR_SERVICE = 'bondmonitor'
REMOTE_MONITOR_CONFIG_FILE_OLD = '/opt/exacloud/monitor.json'
REMOTE_MONITOR_ADMIN_CONFIG_FILE = f'{REMOTE_BONDING_DIR}/monitor_admin.json'
REMOTE_MONITOR_CONFIG_FILE_FMT = f'{REMOTE_BONDING_DIR}/monitor_{{}}.json'
REMOTE_MONITOR_CONFIG_VM_FILE_FMT = \
    f'/EXAVMIMAGES/GuestImages/{{}}/monitor_{{}}.json'
REMOTE_MONITOR_CAVIUM_INFO_FILE = f'{REMOTE_BONDING_DIR}/cavium_info.json'
REMOTE_MONITOR_CONFIG_BK_FILE_FMT = f'{REMOTE_BACKUP_DIR}/monitor_{{}}.json'
REMOTE_MONITOR_CAVIUM_INFO_BK_FILE = f'{REMOTE_BACKUP_DIR}/cavium_info.json'
REMOTE_VM_CUSTOM_VIP_FILE_FMT = f'{REMOTE_BONDING_DIR}/custom_vips_{{}}.json'
REMOTE_VM_CUSTOM_VIP_VM_FILE_FMT = \
    f'/EXAVMIMAGES/GuestImages/{{}}/custom_vips_{{}}.json'
REMOTE_STACK_IDENTIFIER_CONFIG = f'{REMOTE_MONITOR_DIR}/stack_identifier.config'

def patch_bond_bridge_ifcfg(
        node: exaBoxNode,
        bond_iface_conf: BondIfaceConf,
        is_cleanup: bool,
        restart_network: bool = False,
        remove_bridge_ip_on_cleanup: bool = True) -> None:
    """Patch bonding interfaces' ifcfg configuration and restart interfaces.

    Adds/cleans up bonding monitoring info to bonding interfaces (bond and
    bridge) and restarts them for the changes to take effect.

    :param node: node where to configure.
    :param bond_iface_conf: net interface bonding configuration.
    :param is_cleanup: whether we should perform cleanup instead of setup.
    :param restart_network: whether to restart the entire network service
                            instead of just the interfaces.
    :param remove_bridge_ip_on_cleanup: whether to remove or keep the bonding
                                        interface IP during cleanup.
    :returns: Nothing
    :raises ExacloudRuntimeError: if an error occurred.
    """
    bond_interface = BOND_INTERFACE_FMT.format(bond_iface_conf.bond_id)
    primary_interface = get_slave_name(node, bond_interface, bond_iface_conf.primary_interface)
    secondary_interface = get_slave_name(node, bond_interface, bond_iface_conf.secondary_interface)
    
    if is_cleanup:
        bond_vals = {
            "mode": "active-backup",
            "miimon": "100",
            "downdelay": "2000",
            "updelay": "5000",
            "num_grat_arp": "100"
        }

        bond_key_vals = {
            'BONDING_OPTS': (
                f'"mode={bond_vals["mode"]} miimon={bond_vals["miimon"]} '
                f'downdelay={bond_vals["downdelay"]} updelay={bond_vals["updelay"]} '
                f'num_grat_arp={bond_vals["num_grat_arp"]}"'
            )
        }

        # only remove parameters from bridge config
        bridge_key_vals = {
            "IPADDR": None if remove_bridge_ip_on_cleanup \
                else str(bond_iface_conf.ip_addr),
            "NETMASK": None if remove_bridge_ip_on_cleanup \
                else str(bond_iface_conf.netmask)
        }
    else:
        bond_vals = {
            "MTU": "9000",
            "mode": "active-backup",
            "fail_over_mac": "1",
            "num_grat_arp": "8",
            "arp_interval": "1000",
            "primary_reselect": "failure",
            "arp_allslaves": "1",
            "arp_ip_target": str(bond_iface_conf.gateway),
            "primary": primary_interface
        }

        bridge_key_vals = {
            "MTU": "9000",
            "IPADDR": str(bond_iface_conf.ip_addr),
            "NETMASK": str(bond_iface_conf.netmask),
            "ARPCHECK": "no"
        }

        bond_key_vals = {
            "MTU": bond_vals["MTU"],
            "BONDING_OPTS": (
                f'"mode={bond_vals["mode"]} fail_over_mac={bond_vals["fail_over_mac"]} '
                f'num_grat_arp={bond_vals["num_grat_arp"]} arp_interval={bond_vals["arp_interval"]} '
                f'primary_reselect={bond_vals["primary_reselect"]} arp_allslaves={bond_vals["arp_allslaves"]} '
                f'arp_ip_target={bond_vals["arp_ip_target"]} primary={bond_vals["primary"]}"'
            )
        }

    bond_interface = BOND_INTERFACE_FMT.format(bond_iface_conf.bond_id)
    bridge_interface = BRIDGE_INTERFACE_FMT.format(bond_iface_conf.bond_id)
    bond_ifcfg_path = BOND_IFCFG_PATH_FMT.format(bond_iface_conf.bond_id)
    bridge_ifcfg_path = BRIDGE_IFCFG_PATH_FMT.format(bond_iface_conf.bond_id)

    bridge_exists = node.mFileExists(bridge_ifcfg_path)
    bond_exists = node.mFileExists(bond_ifcfg_path)

    restart_bond = True
    restart_bridge = True
    _force_network_interfaces_reboot  = get_gcontext().mGetConfigOptions().get(
            "force_network_interfaces_reboot", "false")

    if _force_network_interfaces_reboot.upper() == "FALSE":
        if bond_exists and validate_bonding_config(node, bond_interface, bond_vals):
            ebLogInfo(f'Actual bond interface config is already matching with desire config, skipping bond interface {bond_interface} restart.')
            restart_bond = False

        if bridge_exists and validate_bridge_config(node, bridge_interface, bridge_key_vals):
            ebLogInfo(f'Actual bridge interface config is already matching with desire config, skipping bridge interface {bridge_interface} restart.')
            restart_bridge = False


    # Patch interfaces.  Skip cleanup if ifcfg files are missing.
    if is_cleanup and not bridge_exists:
        ebLogWarn(f"BONDING: {node.mGetHostname()}: "
                  f"{bridge_ifcfg_path} missing, skipping cleanup.")
    elif not restart_bridge:
        ebLogInfo("Current bridge config is matching desired config, skiping config file update")
    else:
        node_update_key_val_file(node, bridge_ifcfg_path, bridge_key_vals)

    if is_cleanup and not bond_exists:
        ebLogWarn(f"BONDING: {node.mGetHostname()}: "
                  f"{bond_ifcfg_path} missing, skipping cleanup.")
    elif not restart_bond:
        ebLogInfo("Current bond conig is matching desired config, skiping config file update")
    else:
        node_update_key_val_file(node, bond_ifcfg_path, bond_key_vals)

    # restart the entire network to reload the interfaces configuration
    if restart_network and (restart_bridge or restart_bond):
        node_exec_cmd_check(node, "/bin/systemctl restart network")
        return

    # restart interfaces (we need to do it in the given order)
    if bridge_exists and restart_bridge:
        node_interface_down(node, bridge_interface)
    if bond_exists and restart_bond:
        node_interface_down(node, bond_interface)
    if bridge_exists and restart_bridge:
        node_interface_up(node, bridge_interface)
    if bond_exists and restart_bond:
        node_interface_up(node, bond_interface)

    # ensure slaves are up for setup only
    if not is_cleanup:
        node_interface_up(node, primary_interface)
        node_interface_up(node, secondary_interface)


def get_slave_name(node, bond_interface_name, interface_name):
    '''
        Checks if dom0 physical function(i.e eth1, eth2 etc) is enabled with switch dev mode.
        If enabled, bond will be present on VF's of those interfaces. So, returns actual vf slave name in this case. Otherwise returns same value.
    '''
    if ebCluAcceleratedNetwork.isDom0InterfaceEnabledWithSwitchDevMode(node, interface_name):
        vf_slave = ebCluAcceleratedNetwork.getVirtualFnSlaveForPhysicalFnSlave(node, bond_interface_name, interface_name)
        if vf_slave is None:
            msg = f'Unable to update get the virtual function name associated with physical interface : {interface_name}'
            ebLogError(msg)
            raise ExacloudRuntimeError(0x804, 0xA, msg)
        ebLogInfo(f'Virtual function name associated with physical interface : {interface_name} enabled with switch dev mode is ::  + {vf_slave}')
        return vf_slave
    #If dom0 is not enabled with switch dev then just returns the same name.
    return interface_name

def filter_nodes_by_cluctrl(cluctrl: exaBoxCluCtrl, nodes_confs: Payload) -> Payload:
    """Filter the nodes in the payload with the information of the XML

    :param cluctrl: cluster object.
    :param payload: payload to extract bonding configuration from.
    :returns payload: List of nodes in the payload and the XML
    """


    if not ebCluCmdCheckOptions(cluctrl.mGetCmd(), ['delete_service']):
        return nodes_confs

    filter_info = []
    dom0_list = [_dom0 for _dom0, _ in cluctrl.mReturnDom0DomUPair()]
    for node in nodes_confs:
        if node.dom0 in dom0_list:
            filter_info.append(node)
    return filter_info


def update_bonded_bridges(cluctrl: exaBoxCluCtrl, payload: Payload) -> None:
    """Executes patch_bond_bridge_ifcfg for each node.

    This ensures that the bonded bridges and interfaces configuration are
    updated discarding the previous values.

    It is assumed that the bonded interfaces and bridges are already created
    in all the nodes.

    :param cluctrl: cluster object.
    :param payload: payload to extract bonding configuration from.
    :returns: Nothing.
    :raises ExacloudRuntimeError: on error.
    """

    bonding_operation = get_bonding_operation_from_payload(payload)
    nodes_bonding_confs = extract_bonding_conf_from_payload(
        payload, bonding_operation, extract_monitor_conf=False, scan_ips=())
    nodes_bonding_confs = filter_nodes_by_cluctrl(cluctrl, nodes_bonding_confs)
    ctx = cluctrl.mGetCtx()

    for bond_conf in nodes_bonding_confs:
        with connect_to_host(bond_conf.dom0, ctx) as node:
            for if_conf in bond_conf.bond_iface_confs:
                eth0_removed = ebMiscFx.mIsEth0Removed(payload, bond_conf.dom0)
                if eth0_removed:
                    ebLogInfo(f'Skipping bonding update for {bond_conf.dom0}... eth0 not present!')
                    continue
                restart_network = eth0_removed
                ebLogInfo('BONDING: Updating bonding interface in Dom0: '
                            f'{bond_conf.dom0}')
                patch_bond_bridge_ifcfg(node, if_conf, False, restart_network)


def create_bonded_bridge(
        node: exaBoxNode,
        bond_iface_conf: BondIfaceConf,
        is_kvm: bool) -> None:
    """Create a bonded-bridge in the given node.

    Creates a bonded-bridge in the given node with slaves as specified in the
    given BondIfaceConf.

    :param node: node where to create the bonded-bridge.
    :param bond_iface_conf: net interface bonding configuration.
    :param is_kvm: whether it is a KVM node.
    :returns: Nothing.
    :raises ExacloudRuntimeError: on error
    """
    bridge_interface = BRIDGE_INTERFACE_FMT.format(bond_iface_conf.bond_id)
    primary_interface = bond_iface_conf.primary_interface
    secondary_interface = bond_iface_conf.secondary_interface

    if is_kvm:
        delete_bridge_cmd = (
            f'/opt/exadata_ovm/vm_maker --remove-bridge {bridge_interface}')
        create_bridge_cmd = (
            '/opt/exadata_ovm/vm_maker '
            f'--add-bonded-bridge {bridge_interface} '
            f'--first-slave {primary_interface} '
            f'--second-slave {secondary_interface}')

    else:
        delete_bridge_cmd = (
            '/opt/exadata_ovm/exadata.img.domu_maker remove-bridge-dom0 '
            f'{bridge_interface}')
        create_bridge_cmd = (
            '/opt/exadata_ovm/exadata.img.domu_maker add-bonded-bridge-dom0 '
            f'{bridge_interface} {primary_interface} {secondary_interface}')

    cmd = f'{delete_bridge_cmd} ; {create_bridge_cmd}'

    ret = node_exec_cmd(node, cmd)

    if ret.exit_code != 0:
        msg = (f'Error creating bonded-bridge {bridge_interface} in Dom0 '
               f'{node.mGetHostname()}; cmd="{cmd}"; rc={ret.exit_code}; '
               f'stdout="{ret.stdout}"; stderr="{ret.stderr}"')
        ebLogError(msg)
        raise ExacloudRuntimeError(0x804, 0xA, msg)


def create_static_bonded_bridge(
        node: exaBoxNode,
        bond_iface_conf: BondIfaceConf,
        is_kvm: bool) -> None:
    """Create a static bonded-bridge in the given node.

    Creates a static bonded-bridge in the given node with slaves as specified
    in the given BondIfaceConf.

    :param node: node where to create the bonded-bridge.
    :param bond_iface_conf: net interface bonding configuration.
    :returns: Nothing.
    :raises ExacloudRuntimeError: on error
    """
    bond_id = bond_iface_conf.bond_id
    bond_iface = BOND_INTERFACE_FMT.format(bond_id)
    bridge_iface = BRIDGE_INTERFACE_FMT.format(bond_id)

    try:
        # first we ensure the bridge doesn't exist
        delete_bonded_bridge(node, bond_iface_conf, is_kvm)

        # create bridge XML config for ipconf
        xml = build_bonded_bridge_ipconf_xml(
            node.mGetHostname(), bond_iface, bridge_iface, bond_iface_conf)
        remote_xml_path = REMOTE_IPCONF_XML_FMT.format(bridge_iface)
        node_write_text_file(node, remote_xml_path, xml)

        # create the bridge
        cmd = f"{REMOTE_IPCONF_CMD} -conf-add {remote_xml_path}"
        node_exec_cmd_check(node, cmd, log_stdout_on_error=True)
    except Exception as exp:
        msg = (f'Failed to create static bonded bridge {bridge_iface}.  '
               f'error="{exp}"')
        ebLogError(msg)
        raise ExacloudRuntimeError(0x804, 0xA, msg) from exp


def delete_bonded_bridge(
        node: exaBoxNode,
        bond_iface_conf: BondIfaceConf,
        is_kvm: bool,
        strict: bool = True) -> None:
    """Delete bonding monitoring bridge in the given node.

    Deletes bonding monitoring bridge as described by bond_iface_conf in the
    given node.  This method succeeds if the bridge doesn't exists.

    :param node: node to delete bridge from.
    :param bond_iface_conf: net interface bonding configuration.
    :param is_kvm: whether is a KVM system.
    :param strict: whether an exception should be raised in case the bridge
                   deletion fails for any reason.
    :returns: nothing.
    :raises ExacloudRuntimeError: if failed to delete the bridge.
    """
    bond_id = bond_iface_conf.bond_id
    bond_iface = BOND_INTERFACE_FMT.format(bond_id)
    bridge_iface = BRIDGE_INTERFACE_FMT.format(bond_id)

    try:
        # verify first that there are no guests provisioned in this host.
        cmd = "/bin/ls /EXAVMIMAGES/GuestImages"
        guests = node_exec_cmd_check(node, cmd).stdout.split()
        if guests:
            msg = (f"BONDING: Cannot delete monitoring bridge in "
                   f"{node.mGetHostname()} since there are still provisioned "
                   f"guests ({guests}).")
            raise ExacloudRuntimeError(0x804, 0xA, msg)

        # delete any possible residual guests bridges
        cmd = "/sbin/brctl show"
        brctl_show = node_exec_cmd_check(node, cmd).stdout.splitlines()
        bridges = [ line.split()[0] for line in brctl_show
                   if line.startswith(f"{bridge_iface}.")]
        if is_kvm:
            remove_bridge_fmt = "/opt/exadata_ovm/vm_maker --remove-bridge {}"
        else:
            remove_bridge_fmt = ("/opt/exadata_ovm/exadata.img.domu_maker "
                                 "remove-bridge-dom0 {}")
        for bridge in bridges:
            cmd = remove_bridge_fmt.format(bridge)
            node_exec_cmd(node, cmd, log_warning=True)
            ebLogInfo(f"BONDING: Removed stale bridge {bridge} "
                      f"in {node.mGetHostname()}")

        # Try to delete bridge both as static and non-static bridge.  These
        # commands may fail, but it's expected in some cases (e.g. if the
        # bridge doesn't exist or is of different type static/non-static), so
        # we do not fail in those cases, but we check that the bridge doesn't
        # exist after this and if it does we do fail in that case.

        # delete non-static bridge
        cmd = remove_bridge_fmt.format(bridge_iface)
        node_exec_cmd(node, cmd, log_warning=True, log_stdout_on_error=True)

        # delete static bridge
        cmd = f"{REMOTE_IPCONF_CMD} -int-delet {bond_iface}"
        node_exec_cmd(node, cmd, log_warning=True, log_stdout_on_error=True)

        # delete stale interfaces eth1 and eth2 if found in cell.conf
        for if_name in ('eth1', 'eth2'):
             cmd = f"/bin/grep {if_name} /opt/oracle.cellos/cell.conf"
             ret = node_exec_cmd(node, cmd)
             if ret.exit_code == 0:
                 cmd = f"{REMOTE_IPCONF_CMD} -int-delet {if_name}"
                 node_exec_cmd(node, cmd, log_warning=True, log_stdout_on_error=True)                

        # delete any possible residual bridge configuration file
        cmd = f"/bin/rm -f {IFCFG_DIR}/ifcfg-*bondeth{bond_id}*"
        node_exec_cmd(node, cmd)

        # check bond/bridge doesn't exist at this point
        # The code here checks only for ifcfg-bondeth0 and ifcfg-vmbondeth0
        # So, added the code in the next segment to check for ifcfg-bondeth0.1
        # and ifcfg-vmbondeth0.1 etc..
        # basically check for ifcfg-bondeth0.* and ifcfg-vmbondeth0.*
        if (node.mFileExists(BOND_IFCFG_PATH_FMT.format(bond_id))
                or node.mFileExists(f"/sys/class/net/{bond_iface}/operstate")
                or node.mFileExists(BRIDGE_IFCFG_PATH_FMT.format(bond_id))
                or node.mFileExists(
                    f"/sys/class/net/{bridge_iface}/operstate")):
            msg = f"{bond_iface}/{bridge_iface} exist"
            ebLogError(f"{msg}.  We failed to remove existing bridge, look for"
                       " previous command execution warnings for details.")
            raise ExacloudRuntimeError(0x804, 0xA, msg)

        # Check for presece of ifcfg-vmbondeth0.61, ifcfg-vmbondeth0.62
        # while checking for ifcfg-vmbondeth0 similarly for bondeth interface
        bondfile = BOND_IFCFG_PATH_FMT.format(bond_id)
        bridgefile = BRIDGE_IFCFG_PATH_FMT.format(bond_id)
        cmdstr = (f'ls -l {bondfile}* {bridgefile}* '
                  f'| grep -E "{bondfile}.[0-9]*$|{bridgefile}.[0-9]*$"')
        ret_code, out, _ = node_exec_cmd(node,cmdstr) 
        if ret_code == 0:
            msg = f"Following interfaces exist: {out} "
            ebLogError(f"{msg}. We failed to remove existing bridge, look for"
                       " previous command execution warnings for details.")
            raise ExacloudRuntimeError(0x804, 0xA, msg)

    except Exception as exp:
        msg = (f'Failed to delete bonded bridge {bridge_iface}. error="{exp}"')
        ebLogError(msg)
        if strict:
            raise ExacloudRuntimeError(0x804, 0xA, msg) from exp


def dom0_has_static_bridge(node: exaBoxNode) -> bool:
    """Wether the given Dom0 has a registered static bridge.

    We verify if /opt/oracle.cellos/cell.conf contains a Bridge entry 
    that corresponds to any bonding bridge vmbondeth.

    :param node: dom0 to check.
    :returns: boolean specifying if the given bridge is a static bridge.
    """
    bridge_iface = BRIDGE_INTERFACE_FMT.format('')
    grep = node_cmd_abs_path_check(node, "grep")
    cmd = f"{grep} {bridge_iface} /opt/oracle.cellos/cell.conf"
    ret = node_exec_cmd(node, cmd)
    return ret.exit_code == 0


def dom0_supports_static_bridge(node: exaBoxNode) -> bool:
    """Wether the given Dom0 supports creation of static bonded-bridges.

    Support for static bonded-bridges was added to Exadata's ipconf tool as
    part of bug 33254265.

    :param node: dom0 to check.
    :returs: whether creation of static bonded-bridges is supported.
    :raises Exception: if something went wrong.
    """
    # The Dom0 doesn't support static bonding monitoring bridge creation if the
    # installed ipconf script doesn't support option '-conf-add'.
    grep = node_cmd_abs_path_check(node, "grep")
    cmd = (f"{REMOTE_IPCONF_CMD} -conf-add 2>&1 "
           f"| {grep} -q 'Unknown option: conf-add'")
    ret = node_exec_cmd(node, cmd)

    # If the above grep command didn't find a match means ipconf supports
    # -conf-add.
    return ret.exit_code != 0


def get_node_nics(node: exaBoxNode) -> List[str]:
    """Gets a list of all network interfaces for a given node.

    :param node: exaBoxNode.
    :returns: list of network interfaces.
    """
    ip: str = node_cmd_abs_path_check(node, 'ip', sbin=True)
    cmd: str = f"{ip} -oneline link show"
    _, out, _ = node_exec_cmd_check(node, cmd)
    # The ip command appends a colon (:) at the end of the name of each
    # interface, we'll just take it out.
    return [ if_info.split()[1][:-1]
        for if_info in out.splitlines() if if_info.strip() ]


def get_interface_mac_address(node: exaBoxNode, iface: str) -> str:
    """Gets the MAC address for a given interface of a given node.

    :param node: exaBoxNode.
    :param iface: interface name.
    :returns: str with interface MAC address.
    :raises Exception: if interface does not exist.
    """
    return node_read_text_file(node, f"/sys/class/net/{iface}/address").strip()


def node_create_bonding_dirs(node: exaBoxNode) -> None:
    """Ensure bonding data dirs exist in the given node.

    :param node: exaBoxNode.
    :returs: Nothing.
    :raisen Exception: if an error occurred.
    """
    node_exec_cmd_check(node, f'/bin/mkdir -p {REMOTE_BONDING_DIR}')
    node_exec_cmd_check(node, f'/bin/mkdir -p {REMOTE_BACKUP_DIR}')

def persist_stack_identifier(
        node: exaBoxNode,
        payload: Payload,
        dom0: str) -> None:
    """Persist stack_identifier for bondmonitor on the remote node.

    Expects install_monitor payload shape (bonding_json) and reads
    payload['stack_identifier'], saving it to REMOTE_STACK_IDENTIFIER_CONFIG.
    If not present, logs a warning and returns without failing the operation.
    """
    try:
        stack_id: Optional[str] = None
        if isinstance(payload, dict):
            stack_id = payload.get('stack_identifier')

        if not stack_id:
            ebLogWarn(f'BONDING: No stack_identifier found; skipping for {dom0}')
            return

        node_exec_cmd_check(node, f'/bin/mkdir -p {REMOTE_MONITOR_DIR}')
        node_write_text_file(
            node, REMOTE_STACK_IDENTIFIER_CONFIG, f'{stack_id}\n')
        ebLogInfo('BONDING: Saved stack_identifier at '
                  f'{REMOTE_STACK_IDENTIFIER_CONFIG} on {dom0}')
    except Exception as ex:
        ebLogWarn('BONDING: Failed to persist stack_identifier on '
                  f'{dom0}: {ex}')
        
def save_bonding_config_state(
        node: exaBoxNode,
        is_cleanup: bool,
        bridge: bool = False,
        monitor_domu: str = "") -> None:
    """Save state of bonding configuration for the given operations.

    Just keeps track of which bonding components (bridge, monitor) are
    currently configured in the node in file REMOTE_BONDING_STATE_FILE.  If
    monitor_domu is non-empty, the monitor state of that DomU is updated.

    :param node: exaBoxNode
    :param is_cleanup: whether state should be update for cleanup operations
        rathern than setup.
    :param bridge: whether change state of monitoring bridge.
    :param monitor_domu: DomU to change monitor state for.
    :returns: nothing.
    :raises Exception: if an error occurred.
    """
    bridge_value = 'bridge_configured'
    monitor_value = f'monitor_configured:{monitor_domu}'
    if is_cleanup:
        # nothing to cleanup if state file doesn't exist
        if node.mFileExists(REMOTE_BONDING_STATE_FILE):
            sed = node_cmd_abs_path_check(node, 'sed')
            cmd_fmt = f"{sed} -i '/{{}}/d' {REMOTE_BONDING_STATE_FILE}"

            if bridge:
                node_exec_cmd_check(node, cmd_fmt.format(bridge_value))

            if monitor_domu:
                node_exec_cmd_check(node, cmd_fmt.format(monitor_value))
    else:
        echo = node_cmd_abs_path_check(node, 'echo')
        cmd_fmt = f'{echo} "{{}}" >> {REMOTE_BONDING_STATE_FILE}'

        if bridge:
            node_exec_cmd_check(node, cmd_fmt.format(bridge_value))

        if monitor_domu:
            node_exec_cmd_check(node, cmd_fmt.format(monitor_value))


def configure_bond_bridges(
        cluctrl: exaBoxCluCtrl,
        node: exaBoxNode,
        operation: PayloadBondOp,
        bond_iface_confs: Sequence[BondIfaceConf],
        is_kvm: bool,
        static_bridge: bool,
        reuse_bridge: bool = False) -> None:
    """Configure bonding net interfaces in a node.

    This assumes the monitor has already been installed (see
    install_bond_monitor_rpm()).

    :param cluctrl: clucontrol object
    :param node: node to configure.
    :param operation: Bonding operation specified in payload.
    :param bond_iface_confs: net interface bonding configurations.
    :param is_kvm: whether is a KVM system.
    :param static_bridg: whether creation of static bonded-bridge is supported.
    :param reuse_bridge: whether to reuse the existing bonding bridge.
    :returns: nothing.
    :raises ExacloudRuntimeError: if an error occurred during configuration.
    """
    ebLogTrace('BONDING: Configuring bonding interfaces in Dom0 '
               f'{node.mGetHostname()}...')

    for conf in bond_iface_confs:
        ebLogTrace(f'BONDING: Configuring bond {conf.bond_id}')

        if operation == PayloadBondOp.MigrationFlow or reuse_bridge:
            # for migration flow, we only need to update the current bridge
            patch_bond_bridge_ifcfg(node, conf, is_cleanup=False,
                                    restart_network=reuse_bridge)

        else:
            if static_bridge:
                create_static_bonded_bridge(node, conf, is_kvm)
            else:
                # ensure bonded-bridge exists
                create_bonded_bridge(node, conf, is_kvm)

                # configure interfaces with bonding info
                patch_bond_bridge_ifcfg(node, conf, is_cleanup=False,
                                        restart_network=False)

        # backup bonding-enabled ifcfg files
        bond_ifcfg_path = BOND_IFCFG_PATH_FMT.format(conf.bond_id)
        dest_file = os.path.join(
            REMOTE_BACKUP_DIR, os.path.basename(bond_ifcfg_path))
        node_copy_file(node, bond_ifcfg_path, dest_file, overwrite=True)

        bridge_ifcfg_path = BRIDGE_IFCFG_PATH_FMT.format(conf.bond_id)
        dest_file = os.path.join(
            REMOTE_BACKUP_DIR, os.path.basename(bridge_ifcfg_path))
        node_copy_file(node, bridge_ifcfg_path, dest_file, overwrite=True)

        # WORKAROUND for bug 32356629: ensure primary slave is the active one.
        cmd = f'{REMOTE_BOND_UTILS_CMD} activate_primary'
        node_exec_cmd_check(node, cmd)

        # ensure the bonds are working
        cmd = f'{REMOTE_BOND_UTILS_CMD} check_all'
        node_exec_cmd_check(node, cmd)

        # WORKAROUND for bug 33352736.  Until the fix is included in mainline
        # Exadata images, we need the workaround in bug 33039295, which is
        # delivered as a KSplice patch (which we assume is already installed by
        # OPS).  As part of that workaround, we need to set sysctl variable
        # "ksplice_arp_allslaves=1", both in a persistent location and the
        # runtime value.  If the runtime operation fails, we just log an
        # informative warning since a) bonding can work without the workaround
        # and b) the workaround won't be required in Dom0s which already have
        # the mainline fix for bug 33352736.
        #
        # REMOVE ONCE ALL PRODUCTION FLEET IS UPGRADED TO EXADATA IMAGE WITH
        # MAINLINE FIX.

        """
        _ok = cluctrl.mSetSysCtlConfigValue(
            node,
            "ksplice_arp_allslaves",
            "1",
            aRaiseException=False
        )

        if not _ok:
            ret = node_exec_cmd(
                node, "/usr/local/bin/imageinfo", log_warning=True)
            msg = ('BONDING: Falied to set runtime sysctl config '
                   '"ksplice_arp_allslaves=1".  This is required for bug '
                   '33039295; ensure that the KSplice patch has been applied.'
                   '  If this Dom0 does not require the fix, you can ignore '
                   'this warning.  '
                   f'dom0={node.mGetHostname()}; imageinfo:\n{ret.stdout}')
            ebLogWarn(msg)
        """


def save_cavium_info(
        node: exaBoxNode,
        cavium_info: MonitorBondCaviumInfo) -> None:
    """Save Cavium info in node.

    :param node: node where to save the Cavium info.
    :param cavium_info: Cavium info.
    :returns: nothing
    :raises ExacloudRuntimeError: if an error occurred.
    """
    # save cavium info into file and a backup of it
    node_write_text_file(node, REMOTE_MONITOR_CAVIUM_INFO_FILE, cavium_info)
    node_write_text_file(node, REMOTE_MONITOR_CAVIUM_INFO_BK_FILE, cavium_info)


def remove_cavium_info(node: exaBoxNode) -> None:
    """Remove Cavium info from a node.

    :param node: node where to remove the Cavium info from.
    :param cavium_info: Cavium info.
    :returns: nothing
    :raises ExacloudRuntimeError: if an error occurred.
    """
    # remove cavium info file (not critical, just log a warning if it fails)
    cmd = f"/bin/rm -f {REMOTE_MONITOR_CAVIUM_INFO_FILE}"
    node_exec_cmd(node, cmd, log_warning=True)


def get_bond_monitor_rpm_local_path() -> str:
    """Return local path to bond monitor RPM file.

    :returns: path to RPM (with symlinks expanded).
    :raises ExacloudRuntimeError: if RPM file found.
    """
    # find local monitor RPM (following symlinks)
    rpm_path = os.path.realpath(LOCAL_MONITOR_RPM_FILE)

    if not os.path.isfile(rpm_path):
        msg = (f'Bonding monitor RPM file {rpm_path} does not exist in local '
               'repository or is not a regular file.')
        ebLogError(msg)
        raise ExacloudRuntimeError(0x804, 0xA, msg)

    return rpm_path


def get_bond_monitor_installed(node: exaBoxNode) -> Optional[str]:
    """Returns the monitor version currently installed in the node.

    :param node: node where to check the monitor version.
    :returns: a string of the installed monitor version or None if the monitor
              is not installed in the node.
    """
    cmd = f'/bin/rpm -q {MONITOR_RPM_PACKAGE_NAME}'
    ret_code, out, _ = node_exec_cmd(node, cmd)
    if ret_code == 0:
        return out.strip()
    return None


def install_bond_monitor_rpm(
        node: exaBoxNode,
        rpm_path: str,
        domu: Optional[str] = None,
        force_reinstall: bool = True) -> None:
    """Install bonding monitor RPM in a node.

    :param node: node where to install the RPM.
    :param domu: DomU NAT Hostname needed in case we want to migrate the
                 monitor configuration JSON file to the new path.
    :param rpm_path: path to the local monitor RPM package.
    :param force_reinstall: reinstall the monitor even if already installed.
    :returns: nothing
    :raises ExacloudRuntimeError: if an error occurred
    """
    ebLogTrace('BONDING: Installing bonding monitor RPM in Dom0 '
               f'{node.mGetHostname()}')

    monitor_installed: Optional[str] = get_bond_monitor_installed(node)
    if monitor_installed is not None:
        ebLogTrace(f'BONDING: {monitor_installed} already installed in '
                   f'{node.mGetHostname()}')
        if not force_reinstall:
            ebLogTrace('BONDING: Skipping reinstall of bondmonitor.')
            return

    # Make sure we move the JSON from the old path to the new path since
    # the new monitor does not support the old path.
    old_conf_file = REMOTE_MONITOR_CONFIG_FILE_OLD
    if domu and node.mFileExists(old_conf_file):
        conf_file = REMOTE_MONITOR_CONFIG_FILE_FMT.format(domu)
        if node.mFileExists(conf_file):
            ebLogWarn(f'BONDING: Tried to move {old_conf_file} to {conf_file} '
                      'but the latter was alreay present in '
                      f'{node.mGetHostname()} We will skip the file moving '
                      'to keep the new one and we will delete the old one.')
            node_exec_cmd_check(node, f'/bin/rm -f {old_conf_file}')
        else:
            ebLogInfo(f'BONDING: Moving {old_conf_file} to {conf_file} in '
                      f'{node.mGetHostname()}')
            node_exec_cmd_check(node, f'/bin/mv {old_conf_file} {conf_file}')

    # Force reinstall if already installed, even if we are reinstalling an
    # older version.
    rpm_basename = os.path.basename(rpm_path)
    remote_rpm_path = os.path.join(REMOTE_BONDING_DIR, rpm_basename)
    node.mCopyFile(rpm_path, remote_rpm_path)
    # Get the Release version of bondmonitor rpm if it is already installed
    # and the release version of the rpm we are going to install
    # If both the versions match, we don't need to install the rpm again
    # but we can restart the bondmonitor service once since monitor config
    # could have got changed
    force_install_rpm = True
    ret, out, err = node_exec_cmd(node, f"/bin/rpm -qi {MONITOR_SERVICE} | grep Release")
    # Check return code - if it is not zero, we need to force install the
    # bondmonitor rpm
    if ret == 0:
        _release_version_installed = out.split(':')[1].strip()
        ebLogTrace(f"BONDING: Release version of installed bondmonitor: {_release_version_installed}")
        ret, out, err = node_exec_cmd(node, f"/bin/rpm -qip {remote_rpm_path} | grep Release")
        _release_version_rpm = out.split(':')[1].strip()
        ebLogTrace(f"BONDING: Release version of bondmonitor rpm: {_release_version_rpm}")
        if _release_version_installed == _release_version_rpm:
            force_install_rpm = False
            ebLogTrace("BONDING: Bondmonitor already installed with same release version.")
    if force_install_rpm:
        ebLogTrace(f'BONDING: Forcing install of {rpm_basename} in '
                f'{node.mGetHostname()}')
        cmd = f'/bin/rpm -U --nodigest --nofiledigest --replacepkgs --oldpackage {remote_rpm_path}'
        node_exec_cmd_check(node, cmd)
    else:
        # Just restart the bondmonitor service to accommodate monitor config
        # change
        ebLogTrace(f'BONDING: Restarting bondmonitor service on {node.mGetHostname()}')
        restart_bond_monitor(node)


def uninstall_bond_monitor_rpm(node: exaBoxNode) -> None:
    """Uinstall bonding monitor RPM in a node.

    :param node: node where to install the RPM.
    :raises ExacloudRuntimeError: if an error occurred
    """
    ebLogTrace('BONDING: Uninnstalling bonding monitor RPM in Dom0 '
               f'{node.mGetHostname()}')

    monitor_installed: Optional[str] = get_bond_monitor_installed(node)
    if monitor_installed is not None:
        ebLogTrace(f'Removing {monitor_installed} in {node.mGetHostname()}')
        cmd = f'/bin/rpm -e --allmatches {MONITOR_RPM_PACKAGE_NAME}'
        node_exec_cmd_check(node, cmd)
    else:
        ebLogTrace('BONDING: bondmonitor not installed in '
                   f'{node.mGetHostname()}. Skipping uninstall.')

    # Remove RPM file.  Not critical, just log a warning if it fails.
    rpm_file_glob = os.path.join(REMOTE_BONDING_DIR, MONITOR_RPM_FILE_GLOB)
    node_exec_cmd(node, f'/bin/rm -f {rpm_file_glob}', log_warning=True)


def configure_bond_monitor(
        cluctrl: exaBoxCluCtrl,
        node: exaBoxNode,
        bond_conf: NodeBondingConf) -> None:
    """Configure bonding monitor in a node.

    This assumes the monitor has already been installed (see
    install_bond_monitor_rpm()).
   
    :param cluctrl: clucontrol object
    :param node: node to configure monitor in.
    :param monitor_conf: node bonding conf.
    :returns: nothing
    :raises ExacloudRuntimeError: if an error occurred during configuration.
    """
    if bond_conf.monitor_conf_type == MonitorConfType.CUSTOMER:
        conf_file = REMOTE_MONITOR_CONFIG_FILE_FMT.format(bond_conf.domu)
    elif bond_conf.monitor_conf_type == MonitorConfType.ADMIN:
        conf_file = REMOTE_MONITOR_ADMIN_CONFIG_FILE
        bond_conf = update_monitor_admin_conf(node, bond_conf)
    else:
        msg = ('Unknown monitor configuration type: '
               f'{bond_conf.monitor_conf_type}')
        ebLogError(msg)
        raise ExacloudRuntimeError(0x804, 0xA, msg)

    # For non-eth0, update the monitor_admin.json as well
    add_remove_entry_monitor_admin_conf(node, bond_conf.domu_admin_ip,
                                        bond_conf.domu_admin_vlan, add=True)

    if bond_conf.monitor_conf_type == MonitorConfType.CUSTOMER and ebCluAcceleratedNetwork.isClusterEnabledWithAcceleratedNetwork(cluctrl):
        ebLogInfo('BONDING: Skipping monitor configuration for customer network of cluster ' + cluctrl.mGetClusterName() + ' as it is enabled with accelerated network')
        return

    ebLogTrace('BONDING: Configuring bonding monitor in Dom0 '
               f'{node.mGetHostname()}; creating file {conf_file}')

    # copy monitor config to Dom0 (one file per-VM) and create a backup of it
    node_write_text_file(node, conf_file, bond_conf.monitor_conf)
    node_write_text_file(
        node, REMOTE_MONITOR_CONFIG_BK_FILE_FMT.format(bond_conf.domu),
        bond_conf.monitor_conf)
    if bond_conf.domu_client:
        conf_file_vm = (f'/EXAVMIMAGES/GuestImages/{bond_conf.domu_client}/'
                        f'monitor_{bond_conf.domu}.json')
        node_write_text_file(node, conf_file_vm, bond_conf.monitor_conf)


def cleanup_bond_bridges(
        node: exaBoxNode,
        bond_iface_confs: Sequence[BondIfaceConf],
        is_kvm: bool,
        static_bridge: bool,
        bonding_operation: PayloadBondOp,
        strict_removal: bool = True,
        keep_bridge: bool = False) -> None:
    """Cleanup bonding monitoring bridges in a node.

    :param node: node to perform the cleanup in.
    :param bond_iface_confs: net interface bonding configurations.
    :param is_kvm: whether is a KVM system.
    :param bonding_operation: Bonding operation from payload
    :param static_bridge: whether static bridges should be cleaned up.
    :param strict_removal: whether an exception should be raised in case the
                           bridge deletion fails for any reason.
    :param keep_bridge: whether we should keep the bonding bridge.
    :returns: nothing
    :raises ExacloudRuntimeError: if an error occurred during cleanup.
    """
    for conf in bond_iface_confs:
        # If static bridge is used, then remove the interface altogether;
        # otherwise only cleanup the bondig configuration from it.
        if static_bridge and not keep_bridge and\
            bonding_operation != PayloadBondOp.RollbackMigration:
            delete_bonded_bridge(node, conf, is_kvm, strict=strict_removal)
        else:
            patch_bond_bridge_ifcfg(node, conf, is_cleanup=True,
                                    restart_network=keep_bridge,
                                    remove_bridge_ip_on_cleanup=not keep_bridge)


def cleanup_bond_monitor_config(
        node: exaBoxNode,
        bond_conf: NodeBondingConf) -> None:
    """Cleanup bonding monitor in a node.

    :param node: node to perform the cleanup in.
    :param conf: NodeBondingConf for which cleanup bondmonitor's config.
    :returns: nothing
    :raises ExacloudRuntimeError: if an error occurred during cleanup.
    """
    # For non-eth0, update the monitor_admin.json as well
    add_remove_entry_monitor_admin_conf(node, bond_conf.domu_admin_ip,
                                        add=False)
    # remove monitor config (not critical, just log a warning if it fails)
    conf_file = REMOTE_MONITOR_CONFIG_FILE_FMT.format(bond_conf.domu)
    ebLogTrace(f"BONDING: removing {conf_file}")
    cmd = f"/bin/rm -f {conf_file} {REMOTE_MONITOR_CONFIG_FILE_OLD}"
    node_exec_cmd(node, cmd, log_warning=True)


def get_bond_monitor_status(node: exaBoxNode) -> bool:
    """Returns true if the bondmonitor service is up and running.
    
    :param node: node to check if bondmonitor is up and running.
    :returns: bool indicating if bondmonitor is up and running.
    """
    if node.mFileExists("/sbin/initctl"):
        cmd = f"/sbin/initctl status {MONITOR_SERVICE}"
    else:
        cmd = f"/sbin/service {MONITOR_SERVICE} status"

    ret, _, _ = node_exec_cmd(node, cmd)
    return ret == 0


def start_bond_monitor(node: exaBoxNode) -> None:
    """Start bonding monitor in a node.

    This assumes the monitor has already been installed (see
    install_bond_monitor_rpm()).

    Raises ExacloudRuntimeError if an error occurred.
    """
    # On systems where Upstart is installed, initctl(8) must be used to control
    # bondmonitor service.
    if node.mFileExists("/sbin/initctl"):
        cmd = f"/sbin/initctl start {MONITOR_SERVICE}"
    else:
        cmd = f"/sbin/service {MONITOR_SERVICE} start"

    ret, out, err = node_exec_cmd(node, cmd)
    valid_error = f'Job is already running: {MONITOR_SERVICE}'
    if ret == 0 or err.strip().endswith(valid_error):
        return

    msg = (f'Could not start {MONITOR_SERVICE} in {node.mGetHostname()}; '
           f'cmd="{cmd}"; rc={ret}; stdout="{out}"; stderr="{err}"')
    ebLogError(msg)
    raise ExacloudRuntimeError(0x804, 0xA, msg)


def stop_bond_monitor(node: exaBoxNode) -> None:
    """Stop bonding monitor in a node.

    This assumes the monitor has already been installed (see
    install_bond_monitor_rpm()).

    Raises ExacloudRuntimeError if an error occurred.
    """
    # On systems where Upstart is installed, initctl(8) must be used to control
    # bondmonitor service.
    if node.mFileExists("/sbin/initctl"):
        cmd = f"/sbin/initctl stop {MONITOR_SERVICE}"
    else:
        cmd = f"/sbin/service {MONITOR_SERVICE} stop"

    # not critical command, just log a warning if it fails
    node_exec_cmd(node, cmd, log_warning=True)


def restart_bond_monitor(node: exaBoxNode) -> None:
    """Restarts bonding monitor in a node.

    To make the operation reliable in all cases, we first stop the service and
    then start it again.  If the service was not running, the result is as if
    start_bond_monitor(node) was called.

    This assumes the monitor has already been installed (see
    install_bond_monitor_rpm()).

    Raises ExacloudRuntimeError if an error occurred.
    """
    stop_bond_monitor(node)
    start_bond_monitor(node)


def run_operation_with_bond_utils_script(
        node: exaBoxNode,
        operation: str) -> str:
    """Runs the bond_utils script with the specified operation.

    The smartNIC_action action is being used to expose the functionality
    of bond_utils.py script through ecra to oneview.

    :param node: node where to run the bond_utils script.
    :param operation: str with the bond_utils operation to execute.
    :returns: nothing.
    """
    try:
        if not node.mFileExists(REMOTE_BOND_UTILS_CMD):
            msg = (f"The script {REMOTE_BOND_UTILS_CMD} does "
                   f"not exist on node {node.mGetHostname()}.")
            ebLogError(msg)
            raise ExacloudRuntimeError(0x804, 0xA, msg)

        cmd = f"{REMOTE_BOND_UTILS_CMD} {operation}"
        ebLogInfo(f'BONDING: Running cmd: "{cmd}"; '
                  f'in Dom0: {node.mGetHostname()}')
        _, out, _ = node_exec_cmd_check(node, cmd, log_stdout_on_error=True)
        ebLogInfo(f'BONDING: stdout for cmd: "{cmd}"; '
                  f'in Dom0: {node.mGetHostname()} is "{out}".')
        return out

    except Exception as ex:
        msg = (f"Failed to run the {REMOTE_BOND_UTILS_CMD} script "
               f"on node {node.mGetHostname()} error={ex}.")
        ebLogError(msg)
        raise ExacloudRuntimeError(0x804, 0xA, msg) from ex

def bring_up_interface_DOM0(aInterface, aNode, aData, aDOM0, aRaiseError=False):
    """
    Bring up the interface on the node.
    """
    ebLogInfo(f"Bringing {aInterface} up")
    node_exec_cmd(aNode, f"/sbin/ip link set up {aInterface}",
                  log_error=True, log_stdout_on_error=True,
                  check_error=aRaiseError)
    time.sleep(3)
    if aData:
        resp = getActiveNetworkInformation(aData)
        ebLogInfo(f"State of active slaves in {aDOM0}: {resp}")

def test_failover(
        node: exaBoxNode, 
        active_slave: str, 
        bounce_back: bool = False) -> None:
    """ Brings down active ethernet interface and brings up inactive one.
    This triggers bondmonitor to failover indicated by the new active slaves.

    :param node - host to operate on 
    :returns nothing
    """
    data = {'interface': 'bondeth0', 'information': ['active_slave'],
            'nodes': node.mGetHostname()}
    dom0 = node.mGetHostname()
    # Check for status of bondmonitor
    if not get_bond_monitor_status(node):
        msg = ("BONDING: bondmonitor service is not active & running in Dom0: "
               f"{node.mGetHostname()}")
        ebLogError(msg)
        raise ExacloudRuntimeError(0x804, 0xA, msg)

    # Validate interfaces are up and running
    out = run_operation_with_bond_utils_script(node, "check_all")

    # failover
    if active_slave == "eth1":
        inactive_slave = "eth2"
    elif active_slave == "eth2":
        inactive_slave = "eth1"

    # If the standby interface is not up before the failover, we will try
    # to bring it up and then do failover
    # If the standby interface could not be brought up, we will raise an
    # exception.
    bring_up_interface_DOM0(inactive_slave, node, None, dom0, aRaiseError=True)

    ebLogInfo(f"Attempting failover in {dom0}: {active_slave} down, "
            f"{inactive_slave} up")
    node_exec_cmd(node, f"/sbin/ip link set down {active_slave}", 
            log_error=True, log_stdout_on_error=True)
    node_exec_cmd(node, f"/sbin/ip link set up {inactive_slave}", 
            log_error=True, log_stdout_on_error=True)
    time.sleep(3)
    data['nodes'] = [dom0]
    resp = getActiveNetworkInformation(data)
    ebLogInfo(f"State of active slaves in {dom0}: {resp}")

    # Bring the previous active slave back up after failover.
    bring_up_interface_DOM0(active_slave, node, data, dom0)

    # If current active is not changed to inactive_slave, retry failover
    if resp['nodes'][0]['active_slave'] != inactive_slave:
        time.sleep(3)
        node_exec_cmd(node, f"/sbin/ip link set down {active_slave}",
                log_error=True, log_stdout_on_error=True) 
        node_exec_cmd(node, f"/sbin/ip link set up {inactive_slave}",
                log_error=True, log_stdout_on_error=True)                                                                                                                                
        time.sleep(3)    
        data['nodes'] = [dom0]               
        resp = getActiveNetworkInformation(data)

        # Bring the previous active slave back up after failover.
        bring_up_interface_DOM0(active_slave, node, data, dom0)

        # If current active is still not changed to inactive_slave
        # or basically failover failed, report error
        if resp['nodes'][0]['active_slave'] != inactive_slave:
            msg = ("BONDING: failover failed in Dom0: "
                   f"{node.mGetHostname()}")
            ebLogError(msg)
            raise ExacloudRuntimeError(0x804, 0xA, msg)
    
    if not bounce_back:
        return # do not bounce back the interface and finish
    
    # Failback
    ebLogInfo(f"Failback in {dom0}: {active_slave} up, {inactive_slave} down")
    node_exec_cmd(node, f"/sbin/ip link set up {active_slave}", log_error=True,
            log_stdout_on_error=True)
    node_exec_cmd(node, f"/sbin/ip link set down {inactive_slave}", 
            log_error=True, log_stdout_on_error=True)
    time.sleep(3)
    resp = getActiveNetworkInformation(data)
    ebLogInfo(f"State of active slaves in {dom0}: {resp}")

    ebLogInfo(f"Bringing {inactive_slave} up")
    node_exec_cmd(node, f"/sbin/ip link set up {inactive_slave}", 
            log_error=True, log_stdout_on_error=True)
    time.sleep(3)
    resp = getActiveNetworkInformation(data)
    ebLogInfo(f"State of active slaves in {dom0}: {resp}")

def send_bond_monitor_garps(node: exaBoxNode, monitor_conf: str) -> None:
    """Calls the monitor_link.py utility with the given configuration file.

    This method will make the monitor to send the GARPs of the IPs that are
    contained only in the given remote configuration file path to avoid
    restarting the whole monitor or resending the GARPs of the already working
    VMs in the cluster.

    :param node: a Dom0 node where monitor_link.py will be executed.
    :param monitor_conf: a string with the remote monitor configuration file.
    """
    # make sure bondmonitor is up and running
    start_bond_monitor(node)
    cmd = f'{REMOTE_MONITOR_LINK_CMD} --json {monitor_conf}'
    node_exec_cmd_check(node, cmd)


def build_custom_vips_config(
        domu: str,
        domu_net_configs: Mapping[str, ebCluNetworkConfig],
        domu_net_configs_monitor: Mapping[str, NodeNetworkConf],
        payload: Payload) -> str:
    """Build custom VIPs config for a given DomU.

    Builds custom VIPs config from the paylod for the given DomU.  See
    documentation of extract_bonding_operation_params() for a description of
    the expected payload (for "bonding_action=config_app_vips").

    domu_net_configs must be a mapping from network type
    ("client"/"backup"/etc) to ebCluNetworkConfig objects and represents the
    networks of the DomU.

    :param domu: domu name.
    :param domu_net_configs: network configs of the DomU.
    :param domu_net_configs_monitor: network configs from monitor config.
    :param payload: custom vips payload.
    :returns: the configuration built (str).
    :raises Exception: if an error occurred.
    """
    # We generate a JSON string with following structure:
    #  {
    #    "<domu>": [
    #      {
    #        "type": "app_vip",
    #        "ip": "<ip_addr>",
    #        "ipv6": "<ipv6_addr>",
    #        "interface_type": "client"/"backup",
    #        "mac": "<mac_addr>",
    #        "standby_vnic_mac": "<mac_addr>",
    #        "vlantag": <vlanid>/null,
    #        "floating": true
    #      },
    #     ...
    #    ]
    #  }
    #
    # "mac" and "vlantag" of the VIP are not part of the payload, thus we take
    # that info from DomU's network of same type ("client"/"backup") in
    # cluctrl.
    def __build_vip_config(payload: Payload) -> Payload:
        net_type = payload["interfacetype"]
        net_config = domu_net_configs[net_type]
        mac = net_config.mGetNetMacAddr()
        vlan = net_config.mGetNetVlanId()
        standby_vnic_mac = payload.get("standby_vnic_mac")

        # Fix value of vlan.  "UNDEFINED" means "no vlan", which we represent
        # here as None.
        if vlan == "UNDEFINED":
            vlan = None
        else:
            vlan = int(vlan)

        # TODO: Due to bug 34390526 we cannot rely on cluctrl for previous
        # information. Instead, let's take it from the current monitor config.
        net_config = domu_net_configs_monitor[net_type]
        mac = net_config.mac
        vlan = net_config.vlantag
        standby_vnic_mac = net_config.standby_vnic_mac
        nw_utils = NetworkUtils()
        ipv4, ipv6 = nw_utils.mGetIPv4IPv6PayloadNotNoneValues(payload)

        # Bond monitor will be accepting '0.0.0.0' IPv4 if it is IPv6 only
        # system. It will be accepting '::' IPv6 if it is IPv4 only system.

        return {
            "type": "app_vip",
            "ip": str(IPv4Address(ipv4)),  # ensure it's a valid IP
            "ipv6": str(IPv6Address(ipv6)),
            "interface_type": net_type,
            "mac": mac,
            "standby_vnic_mac": standby_vnic_mac,
            "vlantag": vlan,
            "floating": True
        }

    return json.dumps(
        {domu: [__build_vip_config(vip) for vip in payload["customvip"]]},
        indent=2)


def configure_custom_vips(
        cluctrl: exaBoxCluCtrl,
        payload: Payload) -> None:
    """Configure custom VIPs for bonding in a cluster.

    Configures the custom VIPs in the payload for bonding in the cluster.   See
    documentation of extract_bonding_operation_params() for a description of
    the expected payload (for "bonding_action=config_app_vips").

    This assumes the monitor has already been installed (see
    install_bond_monitor_rpm()).

    :param cluctrl: cluster object.
    :param payload: custom vips payload.
    :returns: nothing.
    :raises ExacloudRuntimeError: if an error occurred.
    """
    ebLogInfo("BONDING: configuring custom VIPs")

    # We just generate a JSON file similar to /opt/exacloud/monitor.json with
    # config of the custom VIPs to be consumed by bondmonitor.  One file per-VM
    # is created and put at /opt/exacloud/bonding/custom_vips_<DOMU>.json in
    # the Dom0s.
    try:
        ctx = cluctrl.mGetCtx()
        
        #For sriov enabled clusters we no need to do bond monitor configuration for custom vips. 
        if ebCluAcceleratedNetwork.isClusterEnabledWithAcceleratedNetwork(cluctrl):
            ebLogInfo('BONDING: Skipping custom vip bond monitor configuration for cluster ' + cluctrl.mGetClusterName() + ' as it is enabled with accelerated network')
            return 
       
        def _configure_custom_vips(dom0, domu):
            
            domu_net_configs = cluctrl.mGetVMNetConfigs(domu)
            domu_client = domu

            # we use the NAT name of the DomU
            domu = \
                domu_net_configs["client"].mGetNetNatHostName(aFallBack=False)

            ebLogInfo(
                f"BONDING: configuring custom VIPs: dom0={dom0}; domu={domu}")

            try:
                with connect_to_host(dom0, ctx) as node:
                    remote_monitor_config = \
                        REMOTE_MONITOR_CONFIG_FILE_FMT.format(domu)
                    if not node.mFileExists(remote_monitor_config):
                        remote_monitor_config = REMOTE_MONITOR_CONFIG_FILE_OLD
                    remote_monitor_config_contents = node_read_text_file(
                        node, remote_monitor_config)
                    domu_net_configs_monitor = \
                        extract_networks_from_monitor_conf(
                            remote_monitor_config_contents)

                    vip_config = build_custom_vips_config(
                        domu, domu_net_configs, domu_net_configs_monitor,
                        payload)
                    remote_vip_config = \
                        REMOTE_VM_CUSTOM_VIP_FILE_FMT.format(domu)
                    remote_vip_vm_config = REMOTE_VM_CUSTOM_VIP_VM_FILE_FMT\
                        .format(domu_client, domu)

                    node_write_text_file(node, remote_vip_config, vip_config)
                    node_write_text_file(node, remote_vip_vm_config, vip_config)
                    # restart bondmonitor for the changes to take effect
                    restart_bond_monitor(node)

            except Exception as exp:
                msg = (f"BONDING: failed to configure custom VIPs: "
                       f"dom0={dom0}; domu={domu}; error={exp}")
                ebLogError(msg)
                raise ExacloudRuntimeError(0x804, 0xA, msg) from exp
            
        _plist = ProcessManager()
        for dom0, domu in cluctrl.mReturnDom0DomUPair():
            _poolArgs = []
            _poolArgs = [dom0, domu]
            _p = ProcessStructure(_configure_custom_vips, _poolArgs)
            _p.mSetMaxExecutionTime(15*60) # 15 minutes 
            _p.mSetJoinTimeout(5)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()
    except Exception as exp:
        msg = f"BONDING: Failed to configure custom vips: {exp}"
        ebLogError(msg)
        raise ExacloudRuntimeError(0x804, 0xA, msg) from exp

    ebLogInfo("BONDING: configuration of custom VIPs succeeded")


def cleanup_custom_vips_config(node: exaBoxNode, domu: str) -> None:
    """Cleanup DomU's custom VIPs config in given node.

    :param node: node connected to Dom0.
    :param domu: domu.
    :returns: nothing.
    :raises Exception: if an error occurred.
    """
    # Just remove the DomU's custom VIP config file in the Dom0.  We assume
    # that command `/bin/rm -f <file>` succeeds if the file doesn't exist.
    remote_vips_config = REMOTE_VM_CUSTOM_VIP_FILE_FMT.format(domu)
    node_exec_cmd_check(node, f"/bin/rm -f {remote_vips_config}")


def extract_bonding_operation_params(
        cluctrl: exaBoxCluCtrl) -> Tuple[
            str, str, bool, bool, Mapping[str, str]]:
    """Extracts and validate parameter for "bonding_operation" command.

    Extracts the parameters for "bonding_operation" command from the given
    exaBoxCluCtrl and validates them.  It looks for the following parameters in
    the options:

      - bonding_action: the bonding operation to perform
          * Valid values: {"setup", "cleanup", "config_app_vips", "precheck",
                           "install_monitor", "start_monitor", "stop_monitor",
                           "smartNIC_action", "linkfailover", "status_monitor"}
          * Returned value: same string value

      - bonding_json: path to the json payload
          * See below for a description of the expected payload.
          * Returned value: same string value

      - bonding_component: the bonding "component" to affect
          * Valid values: { "bridge", "monitor", "all" }
          * Value not returned; used to compute target_bridge, target_monitor
            (see below)

      - bonding_start_monitor: whether start bonding monitor during setup
          * Valid values: this is a "flag", interpreted as True is present
            (regardless of the value), False otherwise.
          * Returned value: bool

    bonding_action and bonding_json are always required.  bonding_component is
    required if bonding_action={setup|cleanup}.

    Boolean values target_bridge/target_monitor are computed as follows:

      - If bonding_action={setup|cleanup}:
          for value of bonding_component:
            * "bridge":  target_bridge=True
                         target_monitor=False

            * "monitor": target_bridge=False
                         target_monitor=True

            * "all":     target_bridge=True
                         target_monitor=True

      - otherwise: target_bridge=False
                   target_monitor=False

    We expect different JSON payloads in file pointed out by bonding_json
    depending on the value of bonding_action as follows:
      * "setup": same payload as create-service, as described in
          clubonding_config.py.  If bonding_component={"monitor"|"all"}, the
          monitor info must be provided.

      * "cleanup": same payload as delete-service, as described in
          clubonding_config.py.  If bonding_component={"monitor"|"all"}, the
          monitor info must be provided.

      * "linkfailover":
          {
            "rackname": "<rackname>",
            "racktype": "QUARTER",
            "nodes": ["<LIST_OF_DOM0_FQDNs>"],
            "newactive": "interface"
          }

      * "install_monitor"/"start_monitor"/"stop_monitor":
          {
            "nodes": [
                <LIST_OF_DOM0_FQDNs>
            ]
          }

      * "config_app_vips":
          {
            "customvip": [
              {
                "domainname": <vip_domainname>,
                "hostname": <vip_hostname>,
                "ip": <vip>,
                "interfacetype" : "client"/"backup",
                "standby_vnic_mac": <mac>
              },
              ...
            ]
          }

      * "smartNIC_action":
          {
            "operation": "test_standby/check_all/check_active/activate_primary",
            "node_id": "<dom0 on which above operation need to be run>"
          }

      * "status_monitor":
          {
            "nodes": {
              "iad103709exdd011.iad103709exd.adminiad1.oraclevcn.com": [
                "iad103709exddu1101.iad103709exd.adminiad1.oraclevcn.com",
                "iad103709exddu1102.iad103709exd.adminiad1.oraclevcn.com"
              ],
              "iad103709exdd014.iad103709exd.adminiad1.oraclevcn.com": [],
              "iad103709exdd004.iad103709exd.adminiad1.oraclevcn.com": [],
              "iad103709exdd015.iad103709exd.adminiad1.oraclevcn.com": []
            }
          }

    :param cluctrl: exaBoxCluCtrl to extract parameters from.
    :returns: tuple
        (bonding_action, bonding_json, target_bridge, target_monitor,
         bonding_start_monitor) with values as described above.
    :raises ExacloudRuntimeError: if the validation failed or an error occurred
    """
    if not is_bonding_supported(cluctrl):
        bond_conf = cluctrl.mCheckConfigOption('activate_oci_bonding')
        msg = ('Bonding not supported in this cluster.  '
               f'ATP={cluctrl.isATP()}; ExaBM={cluctrl.mIsExabm()}; '
               f'activate_oci_bonding={bond_conf}')
        ebLogError(msg)
        raise ValueError(msg)

    options = cluctrl.mGetArgsOptions()

    valid_actions = (
        'setup', 'cleanup', 'config_app_vips', 'install_monitor',
        'start_monitor', 'stop_monitor', 'precheck', 'smartNIC_action',
        'consistency_check', 'linkfailover', 'status_monitor'
    )
    action = options.bonding_action

    if not action or action not in valid_actions:
        msg = f'Parameter "bonding_action" wrong, missing or empty: {action}'
        ebLogError(msg)
        raise ValueError(msg)

    if not options.bonding_json:
        msg = 'No "bonding_json" option passed'
        ebLogError(msg)
        raise ValueError(msg)

    component = options.bonding_component

    target_bridge = False
    target_monitor = False

    if component:
        if component == 'bridge':
            target_bridge = True
        elif component == 'monitor':
            target_monitor = True
        elif component == 'all':
            target_bridge = True
            target_monitor = True
        else:
            msg = ('Invalid value of parameter "bonding_component": '
                   f'"{component}"')
            ebLogError(msg)
            raise ValueError(msg)
    elif action in ('setup', 'cleanup'):
        msg = 'Required parameter "bonding_component" not specified'
        ebLogError(msg)
        raise ValueError(msg)

    dom0_domu_map = dict(cluctrl.mReturnDom0DomUNATPair())

    ebLogTrace('BONDING: bonding_operation params: '
               f'bonding_action={options.bonding_action}; '
               f'bonding_json={options.bonding_json}; '
               f'bonding_component={options.bonding_component}; '
               f'bonding_start_monitor={options.bonding_start_monitor}')

    return (action, options.bonding_json, target_bridge, target_monitor,
            dom0_domu_map)


def update_monitor_admin_conf(
        node: exaBoxNode,
        bond_conf: NodeBondingConf) -> NodeBondingConf:
    """Updated the missing fields for the admin monitor cofiguration.

    This includes:
     - If some IP is missing the interface MAC address, we will take the node's
       first monitoring bridge MAC address to fill it.

    :param node: exaBoxNode,
    :param monitor_conf: node bonding conf.
    :returns: The updated admin monitor config.
    :raises ExacloudRuntimeError: if an error occurred.
    """
    if 'monitor_admin' not in bond_conf.monitor_conf or \
        not bond_conf.bond_iface_confs:
        return bond_conf

    bridges_mac = [ get_interface_mac_address(
                        node, BRIDGE_INTERFACE_FMT.format(conf.bond_id))
                    for conf in bond_conf.bond_iface_confs ]

    monitor_conf = json.loads(bond_conf.monitor_conf)
    for entry in monitor_conf['monitor_admin']:
        if not entry.get('mac'):
            entry['mac'] = bridges_mac[0]

    return bond_conf._replace(monitor_conf=json.dumps(monitor_conf, indent=2))



def add_remove_entry_monitor_admin_conf(
        node: exaBoxNode,
        ip: str,
        vlan: int=0,
        add=True):
    """Adds a new entry in the monitor_admin.json of the given node.

    The following algorithm is performed:
    - Check if monitor_admin.json exists in the given node.
        In case it is not, just exit.
    - For adding: Check if the given IP is already added in the node.
        In case it is, just exit.
    - Obtain the MAC address for the vmbondeth0 interface
    - Add the new entry in monitor_admin.json.
    - For removing: Remove the entry with the given IP if exists.
    
    In order to reload the changes for all the added IPs, it is needed to
    restart the monitor after calling this method.

    :param node: exaBoxNode.
    :param ip: NAT IP.
    :param vlan: NAT VLAN.
    :param add: Whether add or remove the IP.
    """
    json_path: str = REMOTE_MONITOR_ADMIN_CONFIG_FILE
    dom0: str = node.mGetHostname()
    if not node.mFileExists(json_path):
        ebLogInfo(f"BONDING: {json_path} is missing in Dom0 "
                  f"{dom0}, skipping update.")
        return

    # Parse JSON
    monitor_conf: dict = json.loads(node_read_text_file(node, json_path))
    if add:
        # Search for requested IP.
        if any(entry["ip"] == ip for entry in monitor_conf["monitor_admin"]):
            ebLogInfo(f"BONDING: {ip} already in {json_path} in Dom0 "
                    f"{dom0}, skipping update.")
            return

        # Get node's vmbondeth0 MAC and append new entry.
        mac: str = get_interface_mac_address(
            node, BRIDGE_INTERFACE_FMT.format(0))
        monitor_conf["monitor_admin"].append({
            "type": "admin_ip",
            "ip": ip,
            "interface_type": "admin_bondmonitor",
            "mac": mac,
            "standby_vnic_mac": "",
            "vlantag": str(vlan),
            "floating": False
        })
    else:
        # For entry removal...
        new_monitor_admin = [ entry for entry in monitor_conf["monitor_admin"]
                              if entry["ip"] != ip ]
        if monitor_conf["monitor_admin"] == new_monitor_admin:
            ebLogInfo(f"BONDING: {ip} not found {json_path} in Dom0 "
                    f"{dom0}, skipping update.")
            return
        monitor_conf["monitor_admin"] = new_monitor_admin

    # Save the new config.
    node_write_text_file(node, json_path, json.dumps(monitor_conf, indent=2))


def monitor_consistency_check(
        node: exaBoxNode,
        domus: Sequence[str]) -> Mapping[str, bool]:
    """Check the bonding health status of a given node.

    This includes the following individual checks:
     - eth link status.
     - eth master status.
     - monitor service status.
     - monitor configuration for guests present.

    The result will be a dictionary similar to this one:
    {
      "eth1_link": true,
      "eth2_link": false,
      "eth1_ifstatus": true,
      "eth2_ifstatus": false,
      "bondmonitor": false,
      "bondmonitor_json": true
    }

    :param node: Dom0 node.
    :param domus: Sequence of DomUs in this Dom0.
    :returns: Check results.
    """

    # check for eth interfaces state and link state
    eth_states: Mapping[str, Mapping[str, bool]] = {}
    for if_name in ('eth1', 'eth2'):
        eth_state: Mapping[str, str] = {}
        physical_state_file: str = f"/sys/class/net/{if_name}/operstate"
        bond_state_file: str = f"/sys/class/net/{if_name}/master/operstate"
        for if_type, if_state_file in (('physical', physical_state_file),
                                       ('master', bond_state_file)):
            if_state: bool = False
            if node.mFileExists(if_state_file):
                if node_read_text_file(node, if_state_file).strip() == 'up':
                    if_state = True
            eth_state[if_type] = if_state
        eth_states[if_name] = eth_state

    # check for monitor status
    monitor_status: bool = get_bond_monitor_status(node)

    # check active slaves
    active_slave: str = ""
    bondeth0_active_file: str = f"/sys/class/net/bondeth0/bonding/active_slave"
    if node.mFileExists(bondeth0_active_file):
        active_slave = node_read_text_file(node, bondeth0_active_file).strip()

    inactive_slave: str = ""
    bondeth0_slaves_file: str = f"/sys/class/net/bondeth0/bonding/slaves"
    if node.mFileExists(bondeth0_slaves_file):
        slaves_list = node_read_text_file(node, bondeth0_slaves_file).strip().split(" ")
        inactive_slave, *_ = set(slaves_list) - {active_slave}

    # check for monitor config files
    monitor_config_status: bool = False
    for domu in domus:
        domu_hostname, *_ = domu.split('.')

        # regular config file
        monitor_remote_files = (
            REMOTE_MONITOR_CONFIG_FILE_FMT.format(domu_hostname),
            REMOTE_MONITOR_CONFIG_FILE_OLD
        )
        if not any(validate_bond_monitor_config_file(node, domu_hostname, file)
                   for file in monitor_remote_files):
            msg: str = ("BONDING: monitor config file not found or corrupt "
                        f"for DomU: {domu} in Dom0: {node.mGetHostname()}")
            ebLogError(msg)
            break

        # custom VIPs config file if exists
        custom_vips_file = REMOTE_VM_CUSTOM_VIP_FILE_FMT.format(domu_hostname)
        if not node.mFileExists(custom_vips_file):
            msg: str = ("BONDING: Skipping Custom VIPs config validation "
                        f"for DomU {domu} in Dom0 {node.mGetHostname()} "
                        "since config file is missing.")
            ebLogInfo(msg)
            continue
        if not validate_bond_monitor_config_file(node, domu_hostname,
                                                 custom_vips_file):
            msg = ("BONDING: Custom VIPs config file is corrupt for "
                   f"DomU: {domu} in Dom0: {node.mGetHostname()}")
            ebLogError(msg)
            break
    else:
        monitor_config_status = True

    return {
        'eth1_link': eth_states['eth1']['physical'],
        'eth2_link': eth_states['eth2']['physical'],
        'eth1_ifstatus': eth_states['eth1']['master'],
        'eth2_ifstatus': eth_states['eth2']['master'],
        'bondmonitor': monitor_status,
        'bondmonitor_json': monitor_config_status,
        'active_slave': active_slave,
        'inactive_slave' : inactive_slave
    }


def bonding_consistency_check(
        node: exaBoxNode,
        domu: Optional[str] = None,
        custom_vips: Optional[Sequence[Payload]] = None) -> None:
    """Checks the bonding health status of a given node.

    It is assumed that bonding has been previosuly configured for the node.
    If the node has not been provisioned, the domu parameter should be omitted.
    In case the bonding is not in good shape, an ExacloudRuntimeError will be
    raised.

    :param node: node to check the bonding health.
    :param domu: str with DomU name in case it is provisioned.
    :param custom_vips: Sequence of custom VIPs dictionaries if applicable.
    :return: nothing.
    :raises ExacloudRuntimeError: if the bonding health is not good.
    """
    ebLogInfo(f'BONDING: Consistency check for {node.mGetHostname()}')

    # Validate interfaces are up and running
    run_operation_with_bond_utils_script(node, "check_all")

    # check for eth interfaces state and link state
    for if_name in ('eth1', 'eth2'):
        physical_state_file: str = f"/sys/class/net/{if_name}/operstate"
        bond_state_file: str = f"/sys/class/net/{if_name}/master/operstate"
        for if_type, if_state_file in (('physical', physical_state_file),
                                       ('master', bond_state_file)):
            if not node.mFileExists(if_state_file):
                msg = (f"BONDING: Cannot read {if_state_file} "
                       f"in Dom0 {node.mGetHostname()}")
                ebLogError(msg)
                raise ExacloudRuntimeError(0x804, 0xA, msg)
            for _ in range(10):
                if_state = node_read_text_file(node, if_state_file).strip()
                if if_state == 'up':
                    break
                msg = (f'BONDING: Bad state "{if_state}" from {if_state_file} '
                       f"in Dom0 {node.mGetHostname()}, retrying in 1s...")
                ebLogWarn(msg)
                time.sleep(1)
            else:
                msg = (f'BONDING: Bad state "{if_state}" from {if_state_file} '
                       f"in Dom0 {node.mGetHostname()}")
                ebLogError(msg)
                raise ExacloudRuntimeError(0x804, 0xA, msg)

    # Validate Bond Monitor Status is up and runnning
    if not get_bond_monitor_status(node):
        msg = ("BONDING: bondmonitor servie is not active & running in Dom0: "
               f"{node.mGetHostname()}")
        ebLogError(msg)
        raise ExacloudRuntimeError(0x804, 0xA, msg)

    # Checks for provisioned clusters
    if domu is None:
        return

    # Validate bond monitor.json file
    monitor_remote_files = (
        REMOTE_MONITOR_CONFIG_FILE_FMT.format(domu),
        REMOTE_MONITOR_CONFIG_FILE_OLD
    )
    if not any(validate_bond_monitor_config_file(node, domu, file)
               for file in monitor_remote_files):
        msg = ("BONDING: monitor config file not found or corrupt for DomU: "
               f"{domu} in Dom0: {node.mGetHostname()}")
        ebLogError(msg)
        raise ExacloudRuntimeError(0x804, 0xA, msg)

    # Validate Custom VIPs
    if not custom_vips:
        return

    custom_vips_file = REMOTE_VM_CUSTOM_VIP_FILE_FMT.format(domu)
    if not validate_bond_monitor_config_file(node, domu, custom_vips_file):
        msg = ("BONDING: Custom VIPs config file not found or corrupt for "
               f"DomU: {domu} in Dom0: {node.mGetHostname()}")
        ebLogError(msg)
        raise ExacloudRuntimeError(0x804, 0xA, msg)


def validate_bond_monitor_config_file(
        node: exaBoxNode,
        domu: str,
        remote_file_path: str) -> bool:
    """Validates that the bondmonitor config file is consistent.

    :param node: node where to validate the monitor config file.
    :param domu: str with DomU to validate the monitor configuration.
    :returns: bool indicating whether the monitor file is consistent.
    """
    if not node.mFileExists(remote_file_path):
        ebLogError(f'BONDING: The specified monitor config file '
                   f'{remote_file_path} does not exist in Dom0 '
                   f'{node.mGetHostname()}')
        return False
    try:
        monitor_json = node_read_text_file(node, remote_file_path)
        if domu not in json.loads(monitor_json):
            ebLogError(f'BONDING: The specified monitor config file '
                       f'{remote_file_path} in Dom0 {node.mGetHostname()} '
                       f'Does not correspond to DomU {domu}')
            return False

        ebLogInfo(f'BONDING: Monitor config found at {remote_file_path} '
                  f'for DomU {domu} in Dom0 {node.mGetHostname()}')

        # TODO: Add extra consistency checks to the bondmonitor config file.

    except Exception as ex:
        ebLogError('BONDING: Error reading the monitor config file at '
                   f'{remote_file_path} in Dom0 {node.mGetHostname()}. '
                   f'Probably the file is corrupted. Exception: {ex}')
        return False

    return True


#
# Public functions
#


def is_bonding_supported(cluctrl: exaBoxCluCtrl) -> bool:
    """Whether net boding is supported in the given cluster."""
    # Bug 37989871: Ignore exabox.conf parametters, enable only by Payload.
    return True
    """
    supported = False
    activate_bonding = cluctrl.mCheckConfigOption('activate_oci_bonding')

    if activate_bonding:
        is_exabm = cluctrl.mIsExabm()
        is_atp = cluctrl.isATP()

        if activate_bonding == 'both' and (is_exabm and is_atp):
            supported = True
        elif activate_bonding == 'exabm' and is_exabm:
            supported = True
        elif activate_bonding == 'atp' and is_atp:
            supported = True
        elif activate_bonding != 'False':
            ebLogWarn("BONDING: Unexpected value of option "
                      f"'active_oci_bonding': {activate_bonding}")

    else:
        for dom0, domu in cluctrl.mReturnDom0DomUPair():
            with connect_to_host(dom0, cluctrl.mGetCtx()) as node:
                if not get_bond_monitor_installed(node):
                    supported = False
                    return supported
                else:
                    supported = True

    return supported
    """


def is_static_monitoring_bridge_supported(
        cluctrl: exaBoxCluCtrl,
        payload: Payload) -> bool:
    """Wether static bonded-bridges are supported in the cluster.

    A cluster is assumed to support creation of static bonded-bridges if all
    the nodes of the cluster support it.

    Support for this was added to Exadata's ipconf tool as part of bug
    33254265.

    :param cluctrl: cluster to check.
    :param payload: payload to extract bonding configuration from.
    :returns: whether the feature is supported or not.
    :raises Exception: if something went wrong.
    """
    bonding_operation = get_bonding_operation_from_payload(payload)

    if not bonding_operation:
        return False  # no bonding payload

    nodes_bonding_confs = extract_bonding_conf_from_payload(
        payload, bonding_operation, extract_monitor_conf=False, scan_ips=())
    nodes_bonding_confs = filter_nodes_by_cluctrl(cluctrl, nodes_bonding_confs)

    if not nodes_bonding_confs:
        return False  # no nodes configured for bonding

    ctx = cluctrl.mGetCtx()

    # Cluster does not support creation of staitc bridge if at least one Dom0
    # does not support it.
    def check_nodes_bonding_support(conf, status_list):
        """
        Function to check if a single node supports the static monitoring bridge
        """
        with connect_to_host(conf.dom0, ctx) as node:
            if not dom0_supports_static_bridge(node):
                ebLogWarn(f"BONDING: {conf.dom0} doesn't support static monitoring bridge.")
                status_list.append(False)
                return
        status_list.append(True)
    
    _plist = ProcessManager()
    results = _plist.mGetManager().list()
    for conf in nodes_bonding_confs:
        _poolArgs = []
        _poolArgs = [conf, results]
        _p = ProcessStructure(check_nodes_bonding_support, _poolArgs)
        _p.mSetMaxExecutionTime(15*60) # 15 mins should be enough
        _p.mSetJoinTimeout(5)
        _p.mSetLogTimeoutFx(ebLogWarn)
        _plist.mStartAppend(_p)
    
    _plist.mJoinProcess()
    
    # if any node doesnt support the bridge , return false
    if not all(results):
        return False

    ebLogInfo("BONDING: cluster supports static monitoring bridge")
    return True


def is_bonding_supported_dom0(
        cluctrl: exaBoxCluCtrl,
        payload: Payload,
        dom0: str) -> bool:
    """Whether bonding should be configured for any given Dom0.

    :param cluctrl: cluster to configure bonding in.
    :param payload: payload to extract bonding configuration from.
    :param dom0: Dom0 FQDN to verify.
    :returns: boolean specifying if bonding should be enabled for that Dom0.
    """
    if not is_bonding_supported(cluctrl):
        ebLogInfo('BONDING: Bonding not supported in this cluster.')
        return False
    
    bonding_operation = get_bonding_operation_from_payload(payload)
    if bonding_operation is None:
        ebLogWarn("BONDING: No bonding operation specified in payload.")
        return False

    nodes_bonding_confs = extract_bonding_conf_from_payload(
        payload, bonding_operation, extract_monitor_conf=False, scan_ips=())
    nodes_bonding_confs = filter_nodes_by_cluctrl(cluctrl, nodes_bonding_confs)

    if not nodes_bonding_confs:
        ebLogInfo('BONDING: No nodes with bonding config enabled.')
        return False

    return dom0 in (config.dom0 for config in nodes_bonding_confs)


def configure_bonding_if_enabled(
        cluctrl: exaBoxCluCtrl,
        payload: Payload,
        configure_bridge: bool,
        configure_monitor: bool,
        nodes: Optional[List[str]] = None) -> bool:
    """Configure network bonding in a cluster if enabled.

    Configures network bonding in a cluster if it is supported (see
    is_bonding_supported()) and it's enabled in the payload.

    If configure_monitor is True, the bonding monitor is installed and
    configured in the nodes of the cluster as well.  In such case, the payload
    must contain the additional information required for the monitor
    configuration.  If start_monitor == True, additionally the monitor is
    started.  start_monitor is ignored when configure_monitor == False.

    See the module's documentation for a description of the payload and for
    what the configuration entails.

    :param cluctrl: cluster to configure bonding in.
    :param payload: payload to extract bonding configuration from.
    :param configure_monitor: whether bonding monitor should be configured too.
    :param node: list of nodes FQDNs where to configure bonding or None to
                 configure for all nodes specified in the payload.
    :return: whether bonding was configured.
    :raises ExacloudRuntimeError: if an error occurred during configuration.
    """
    # pylint: disable=too-many-locals
    ebLogInfo('BONDING: Configuring bonding')

    if not is_bonding_supported(cluctrl):
        ebLogInfo('BONDING: Bonding not supported in this cluster, '
                  'skipping configuration.')
        return False

    if not (configure_bridge or configure_monitor):
        ebLogWarn(
            'BONDING: No bonding operation specified, skipping configuration.')
        return False

    bonding_operation = get_bonding_operation_from_payload(payload)

    if bonding_operation is None:
        ebLogWarn("BONDING: No bonding operation specified in payload, "
                  "skipping configuration.")
        return False
   
    configure_monitor_bk = configure_monitor 

    scan_ips = cluctrl.mGetScanIps()
    scan_ipv6 = cluctrl.mGetScanIps(aIPv6=True)
    nodes_bonding_confs = extract_bonding_conf_from_payload(
        payload, bonding_operation, extract_monitor_conf=configure_monitor,
        scan_ips=scan_ips, dom0s_domus=dict(cluctrl.mReturnDom0DomUPair()),
        scan_ipv6=scan_ipv6)
    nodes_bonding_confs = filter_nodes_by_cluctrl(cluctrl, nodes_bonding_confs)

    if not nodes_bonding_confs:
        ebLogInfo('BONDING: No nodes with bonding config enabled, '
                  'skipping configuration.')
        ebLogTrace(f'BONDING: ECRA payload: {payload}')
        return False

    # find local monitor RPM
    rpm_path = get_bond_monitor_rpm_local_path()

    ctx = cluctrl.mGetCtx()
    is_kvm = cluctrl.mIsKVM()
    static_bridge = is_static_monitoring_bridge_supported(cluctrl, payload)
    
    def bonding_configuration_dom0(conf):
        ebLogInfo(f'BONDING: Configuring bonding in Dom0 {conf.dom0}')

        try:

            with connect_to_host(conf.dom0, ctx) as dom0_node:

                eth0_removed = ebMiscFx.mIsEth0Removed(payload, conf.dom0)
                configure_monitor = configure_monitor_bk
                configure_monitor |= eth0_removed
                skip_bonding = ebMiscFx.mIsSkipBondingBridge(payload, conf.dom0)
                if not skip_bonding:
                    node_create_bonding_dirs(dom0_node)
                    install_bond_monitor_rpm(dom0_node, rpm_path)

                    if configure_bridge:
                        configure_bond_bridges(
                            cluctrl,
                            dom0_node,
                            bonding_operation,
                            conf.bond_iface_confs,
                            is_kvm,
                            static_bridge,
                            reuse_bridge=eth0_removed
                        )
                        save_bonding_config_state(
                            dom0_node, is_cleanup=False, bridge=True)
                        save_cavium_info(dom0_node, conf.bond_cavium_info)
                else:
                    ebLogInfo('BONDING: Skipping bonding configuration for node '
                          f'{conf.dom0}')

                if configure_monitor:
                    configure_bond_monitor(cluctrl, dom0_node, conf)
                    # restart bondmonitor for the changes to take effect
                    restart_bond_monitor(dom0_node)
                    save_bonding_config_state(
                        dom0_node, is_cleanup=False, monitor_domu=conf.domu)

        except Exception as exp:
            msg = ('Bonding configuration failed: '
                   f'dom0={conf.dom0}; domu={conf.domu}; error="{exp}"')
            ebLogError(msg)
            _print_payload = copy.deepcopy(payload)
            mask_keys_json(_print_payload, "sshkey")
            mask_keys_json(_print_payload, "adminpassword")
            ebLogTrace(f'BONDING: Payload:\n{json.dumps(_print_payload, indent=2)}')
            raise ExacloudRuntimeError(0x804, 0xA, msg) from exp
    
    # configure bonding in Dom0s/DomUs
    _plist = ProcessManager()
    for conf in nodes_bonding_confs:
        if nodes is not None:
            if conf.dom0 not in nodes:
                ebLogInfo('BONDING: Skipping bonding configuration for node '
                          f'{conf.dom0}')
                continue
        _poolArgs = []
        _poolArgs = [conf]
        _p = ProcessStructure(bonding_configuration_dom0, _poolArgs)
        _p.mSetMaxExecutionTime(15*60) # 15 mins should be enough
        _p.mSetJoinTimeout(5)
        _p.mSetLogTimeoutFx(ebLogWarn)
        _plist.mStartAppend(_p)
    
    _plist.mJoinProcess()

    # configure the Custom VIPs if any
    try:
        custom_vips_payload = {
            "customvip": payload.get("customer_network", {})
                                .get("customvip", [])
        }
        if custom_vips_payload['customvip']:
            configure_custom_vips(cluctrl, custom_vips_payload)

    except Exception as exp:
        msg = f'BONDING: Failed to configure custom vips: {exp}; '
        ebLogError(msg)
        _print_payload = copy.deepcopy(payload)
        mask_keys_json(_print_payload, "sshkey")
        mask_keys_json(_print_payload, "adminpassword")
        ebLogTrace(f'BONDING: Payload:\n{json.dumps(_print_payload, indent=2)}')
        raise ExacloudRuntimeError(0x804, 0xA, msg) from exp

    ebLogInfo('BONDING: Bonding configuration succeeded.')

    return True


def cleanup_bonding_if_enabled(
        cluctrl: exaBoxCluCtrl,
        payload: Payload,
        cleanup_bridge: bool,
        cleanup_monitor: bool) -> bool:
    """Cleanup bonding configuration in a cluster if enabled.

    Cleanup bonding configuration in a cluster if it is supported (see
    is_bonding_supported()) and it is enabled in the payload.  This function
    basically undoes the configuration made by configure_bonding_if_enabled().

    See the module's documentation for a description of the payload and for
    what the cleanup entails.

    :param cluctrl: cluster to cleanup bonding in.
    :param payload: payload to extract bonding configuration from.
    :returns: whether cleanup was performed.
    :raises ExacloudRuntimeError: if an error occurred during the cleanup.
    """
    ebLogInfo('BONDING: Cleaning up bonding')

    if not is_bonding_supported(cluctrl):
        ebLogInfo('BONDING: Bonding not supported in this cluster, '
                  'skipping cleanup.')
        return False

    bonding_operation = get_bonding_operation_from_payload(payload)

    if bonding_operation is None:
        ebLogWarn("BONDING: No bonding operation specified in payload, "
                  "skipping cleanup.")
        return False

    if (cleanup_monitor and
            bonding_operation in (
                PayloadBondOp.CleanupBridge, PayloadBondOp.SetupBridge)):
        msg = (f"BONDING: cannot cleanup bondmonitor using {bonding_operation}"
               " payload; skipping bondmonitor cleanup")
        ebLogWarn(msg)
        cleanup_monitor = False

    if not (cleanup_bridge or cleanup_monitor):
        ebLogWarn('BONDING: No bonding operation specified, skipping cleanup.')
        return False

    # delete-service/delete-compute payload doesn't contain DomU net info and
    # thus we cannot extract the bondmonitor config from it.
    extract_monitor_conf = \
        cleanup_monitor and bonding_operation not in\
            [PayloadBondOp.DeleteService, PayloadBondOp.DeleteCompute,
             PayloadBondOp.RollbackMigration]

    nodes_bonding_confs = extract_bonding_conf_from_payload(
        payload, bonding_operation, extract_monitor_conf=extract_monitor_conf,
        scan_ips=())
    nodes_bonding_confs = filter_nodes_by_cluctrl(cluctrl, nodes_bonding_confs)

    if not nodes_bonding_confs:
        ebLogInfo(
            'BONDING: No nodes with bonding config enabled found in payload.')
        ebLogTrace(f'BONDING: ECRA payload: {payload}')
        if not cleanup_monitor:
            ebLogInfo('BONDING: Skipping cleanup.')
            return False

        ebLogInfo(
            'BONDING: We will delete just the monitor config for all DomUs '
            'in this cluster.')
        cleanup_bridge = False
        nodes_bonding_confs = tuple(
            NodeBondingConf(dom0) for dom0, _ in cluctrl.mReturnDom0DomUPair())

    # For delete-service/delete-compute payload we need to retrive the DomU NAT
    # names from the XML if bondmonitor config is required to be cleaned up.
    if cleanup_monitor and not extract_monitor_conf:
        dom0_domu_map = dict(cluctrl.mReturnDom0DomUNATPair())

        # Get NAT IPs
        dom0_natip_map = {}
        for dom0, domu in cluctrl.mReturnDom0DomUPair():
            machine = cluctrl.mGetMachines().mGetMachineConfig(domu)
            network_ids = machine.mGetMacNetworks()
            for network_id in network_ids:
                network = cluctrl.mGetNetworks().mGetNetworkConfig(network_id)
                network_type = network.mGetNetType()
                if network_type != 'client':
                    continue
                nat_ip = network.mGetNetNatAddr()
                dom0_natip_map[dom0] = nat_ip

        # Since named tuples are read-only, we have to create new objects with
        # new values for domu.  Ensure we use only the hostname, not the FQDN.
        nodes_bonding_confs = tuple(
            conf._replace(domu=dom0_domu_map[conf.dom0].split(".")[0],
                          domu_admin_ip=dom0_natip_map[conf.dom0])
            for conf in nodes_bonding_confs
            if conf.dom0 in dom0_domu_map
        )

    ctx = cluctrl.mGetCtx()
    is_kvm = cluctrl.mIsKVM()
    static_bridge = is_static_monitoring_bridge_supported(cluctrl, payload)

    # Read the Exacloud config parameters.
    strict_bridge_removal = True

    exacloud_options: Optional[Mapping[str, str]] = \
        cluctrl.mCheckConfigOption('bonding')
    if exacloud_options:
        strict_bridge_removal = exacloud_options.get(
            'strict_bridge_removal', 'true').lower() == 'true'


    # clean up bonding in Dom0s/DomUs
    for conf in nodes_bonding_confs:
        ebLogTrace(f'BONDING: Cleaning up bonding in Dom0 {conf.dom0}')

        try:

            with connect_to_host(conf.dom0, ctx) as dom0_node:
                if cleanup_monitor:
                    cleanup_custom_vips_config(dom0_node, conf.domu)
                    cleanup_bond_monitor_config(dom0_node, conf)
                    save_bonding_config_state(
                        dom0_node, is_cleanup=True, monitor_domu=conf.domu)

                if cleanup_bridge:
                    eth0_removed = ebMiscFx.mIsEth0Removed(payload, conf.dom0)
                    cleanup_bond_bridges(
                        dom0_node, conf.bond_iface_confs, is_kvm,
                        static_bridge, bonding_operation,
                        strict_removal=strict_bridge_removal,
                        keep_bridge=eth0_removed)
                    save_bonding_config_state(
                        dom0_node, is_cleanup=True, bridge=True)
                    remove_cavium_info(dom0_node)
                    uninstall_bond_monitor_rpm(dom0_node)

        except Exception as exp:
            msg = ('Bonding cleanup failed: '
                   f'dom0={conf.dom0}; domu={conf.domu}; error="{exp}"')
            ebLogError(msg)
            _print_payload = copy.deepcopy(payload)
            mask_keys_json(_print_payload, "sshkey")
            mask_keys_json(_print_payload, "adminpassword")
            ebLogTrace(f'BONDING: Payload:\n{json.dumps(_print_payload, indent=2)}')
            raise ExacloudRuntimeError(0x804, 0xA, msg) from exp

    ebLogInfo('BONDING: Bonding cleanup succeeded.')

    return True


def migrate_static_bridges(
    cluctrl: exaBoxCluCtrl,
    payload: Payload) -> bool:
    """Makes sure all bonded nodes have static bridges if required.

    In order to determine whether a Dom0 requires a static bridge or a dymanic
    bridge, we'll verify if the current bridge is a dynamic bridge and if that
    is the only bridge in the Dom0. If that is the case we will recreate the
    bridge as a static bridge, otherwise, we will keep the current bridge even
    if it's dynamic, sice the ipconf consistency check never complains when
    there is at least one VM running in the node.
    We need to check that we don't have any remaining bridges in the node
    because the ipconf tool can only create a static bridge if we don't have
    any bridges in the Dom0 and if we have any bridges other than vmbondeth0,
    that means there is at least one VM running in the cluster, and we don't
    need to remove the bridge in that case as explained above.

    :param cluctrl: cluster to cleanup bonding in.
    :param payload: payload to extract bonding configuration from.
    :returns: whether bridges migration was performed.
    """
    if not is_bonding_supported(cluctrl):
        ebLogInfo('BONDING: Bonding not supported in this cluster, '
                  'skipping static bridges migration.')
        return False

    bonding_operation = get_bonding_operation_from_payload(payload)
    if bonding_operation is None:
        ebLogWarn("BONDING: No bonding operation specified in payload, "
                  "skipping static bridges migration.")
        return False

    static_bridge = is_static_monitoring_bridge_supported(cluctrl, payload)
    if not static_bridge:
        ebLogWarn("BONDING: This cluster does not support static bridges, "
                  "skipping static bridges migration.")
        return False

    nodes_bonding_confs = extract_bonding_conf_from_payload(
        payload, bonding_operation, extract_monitor_conf=False, scan_ips=())
    nodes_bonding_confs = filter_nodes_by_cluctrl(cluctrl, nodes_bonding_confs)

    if not nodes_bonding_confs:
        ebLogInfo("BONDING: No nodes with bonding config enabled, "
                  "skipping static bridges migration.")
        return False

    ctx = cluctrl.mGetCtx()

    nodes: List[str] = []
    for conf in nodes_bonding_confs:
        with connect_to_host(conf.dom0, ctx) as node:
            if not dom0_has_static_bridge(node):

                interfaces: List[str] = get_node_nics(node)
                bridge: str = BRIDGE_INTERFACE_FMT.format('')
                bridges: List[str] = [ if_name
                    for if_name in interfaces if if_name.startswith(bridge) ]

                if len(bridges) < 2:
                    nodes.append(conf.dom0)
                    ebLogInfo(f"BONDING: {conf.dom0} has a dynamic bridge. "
                              "We will migrate this to a static bridge.")
                else:
                    ebLogInfo(f"BONDING: {conf.dom0} has a dynamic bridge but "
                              f"it still has the following bridges {bridges}. "
                              "We will keep this bridge as it is.")
            else:
                ebLogInfo(f"BONDING: {conf.dom0} has already a static bridge. "
                          "We will keep this bridge as it is.")

    if not nodes:
        ebLogInfo("BONDING: No nodes require static bridge migration, "
                  "skipping static bridges migration.")
        return False

    ebLogInfo("BONDING: Some nodes are still using dynamic bridges, "
              "we will migrate those to static bridges.")
    return configure_bonding_if_enabled(cluctrl, payload,
        configure_bridge=True, configure_monitor=False, nodes=nodes)


def handle_bonding_operation(cluctrl: exaBoxCluCtrl) -> None:
    """Perform a bonding operation.

    Loads operation details from options in cluctrl.  See
    extract_bonding_operation_params() for details.

    :param cluctrl: exaBoxCluCtrl to operate on.
    :returns: nothing
    :raises ExacloudRuntimeError: if an error occurred.
    """
    ebLogInfo('BONDING: Bonding operation')

    try:
        (action, json_file, target_bridge, target_monitor, dom0_domu_map) \
            = extract_bonding_operation_params(cluctrl)

        payload = json_file
        if isinstance(json_file, str):
            if os.path.isfile(json_file):
                with open(json_file) as json_fd:
                    payload = json.load(json_fd)
            else:
                payload = json.loads(json_file)

        if action == 'setup':
            ebLogInfo('BONDING: Starting bonding configuration: '
                      f'configure_bridge={target_bridge}, '
                      f'configure_monitor={target_monitor}')
            configure_bonding_if_enabled(
                cluctrl, payload, configure_bridge=target_bridge,
                configure_monitor=target_monitor)
        elif action == 'cleanup':
            ebLogInfo('BONDING: Starting bonding cleanup: '
                      f'cleanup_bridge={target_bridge}, '
                      f'cleanup_monitor={target_monitor}')
            cleanup_bonding_if_enabled(
                cluctrl, payload, cleanup_bridge=target_bridge,
                cleanup_monitor=target_monitor)
        elif action == 'config_app_vips':
            configure_custom_vips(cluctrl, payload)
        elif action == 'install_monitor':
            rpm_path = get_bond_monitor_rpm_local_path()
            _error_nodes = []
            for dom0 in payload['nodes']:
                try:
                    ebLogInfo(
                        f'BONDING: Installing bonding monitor in host {dom0}')
                    with connect_to_host(dom0, cluctrl.mGetCtx()) as node:
                        node_create_bonding_dirs(node)
                        install_bond_monitor_rpm(node, rpm_path,
                            domu=dom0_domu_map.get(dom0))
                        persist_stack_identifier(node, payload, dom0)
                except Exception as ex:
                    ebLogError("BONDING: Could not install/update bond monitor"\
                              f" rpm in host {dom0}. Error: {ex}.")
                    _error_nodes.append(dom0)
            if len(_error_nodes) > 0:
                _msg = "BONDING: Could not install/update bond monitor rpm"\
                        f" in hosts - {_error_nodes}. Check exacloud log for"\
                        " more details on the errors."
                raise ExacloudRuntimeError(0x804, 0xA, _msg)
        elif action == 'start_monitor':
            for dom0 in payload['nodes']:
                ebLogInfo(f'BONDING: Starting bonding monitor in host {dom0}')
                with connect_to_host(dom0, cluctrl.mGetCtx()) as node:
                    restart_bond_monitor(node)
        elif action == 'stop_monitor':
            for dom0 in payload['nodes']:
                ebLogInfo(f'BONDING: Stopping bonding monitor in host {dom0}')
                with connect_to_host(dom0, cluctrl.mGetCtx()) as node:
                    stop_bond_monitor(node)
        elif action == 'precheck':
            bonding_migration_prechecks(cluctrl, payload)
        elif action == 'consistency_check':
            for dom0 in payload['nodes']:
                with connect_to_host(dom0, cluctrl.mGetCtx()) as node:
                    bonding_consistency_check(node,
                        domu=dom0_domu_map.get(dom0)
                            if payload['isprovisioned']
                            else None,
                        custom_vips=payload.get('customvips'))
        elif action == 'smartNIC_action':
            dom0: str = payload['node_id']
            operation: str = payload['operation']
            with connect_to_host(dom0, cluctrl.mGetCtx()) as node:
                run_operation_with_bond_utils_script(node, operation)
        elif action == "linkfailover":
            data = {'interface': 'bondeth0', 'information': ['active_slave'],
                    'nodes': payload['nodes']}
            resp = getActiveNetworkInformation(data)
            for entry in resp['nodes']:
                dom0 = entry['node']
                active_slave = entry['active_slave']
                if payload.get('newactive') == active_slave:
                    continue # current slave is the desired one, nothing to do. 
                with connect_to_host(dom0, cluctrl.mGetCtx()) as node:
                    test_failover(node, active_slave)
        elif action == 'status_monitor':
            result: Mapping[str, Mapping[str, bool]] = {}
            for dom0, domus in payload['nodes'].items():
                res_node: Mapping[str, bool] = {}
                with connect_to_host(dom0, cluctrl.mGetCtx()) as node:
                    res_node = monitor_consistency_check(node, domus)
                result[dom0] = res_node

            # build and log the Exacloud request respose
            result_str: str = json.dumps({ 'nodes': result }, indent=4)
            ebLogInfo(f"BONDING: status_monitor results: {result_str}")
            req = cluctrl.mGetRequestObj()
            if req is not None:
                req.mSetData(result_str)
                db = ebGetDefaultDB()
                db.mUpdateRequest(req)

    except Exception as exp:
        msg = f'bonding_operation failed: error="{exp}"'
        ebLogError(msg)
        raise ExacloudRuntimeError(0x804, 0xA, msg) from exp

    ebLogInfo('BONDING: Bonding operation succeeded.')
