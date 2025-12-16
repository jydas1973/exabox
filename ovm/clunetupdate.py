#
# $Header: ecs/exacloud/exabox/ovm/clunetupdate.py /main/15 2025/12/02 17:57:52 ririgoye Exp $
#
# clunetupdate.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      clunetupdate.py - logic for ReST CluCtrl command "network_update"
#
#    DESCRIPTION
#      Logic to handle ReST CluCtrl command "network_update".
#
#    NOTES
#      - If you change this file, please make sure lines are no longer than 80
#        characters (including newline) and it passes pylint, mypy and flake8
#        with all the default checks enabled.
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    11/26/25 - Bug 38636333 - EXACLOUD PYTHON:ADD INSTANTCLIENT TO
#                           LD_LIBRARY_PATH
#    scoral      10/07/25 - Enh 38452359: Support up to 199 VMs.
#    scoral      05/03/24 - Bug 36554412: Made get_kvm_guest_bridges more
#                           resilient on guests with no pre-NAT bridge.
#    scoral      02/22/24 - Bug 36324828: Fixed regex in get_kvm_guest_bridges
#                           to support also VLAN 0.
#    scoral      02/16/24 - Bug 36309292: Make add_kvm_guest_nat_routing &
#                           get_kvm_guest_nat_routing support multiple egress
#                           IPs.
#    aararora    02/05/24 - ER 33667094: Bonding migration rollback.
#    scoral      01/22/24 - Enh 36197938: implemented a few functions to
#                           re-create the guest NAT routing tables/rules
#    scoral      11/10/23 - Bug 35998430: update nftables during vlan update
#    jlombera    08/31/21 - Enh 33220812: move cluctrl_get_domu_configs() to
#                           exaBoxCluCtrl
#    jlombera    06/04/21 - Bug 32912942: add ReST CluCtrl command
#                           "network_update
#    jlombera    06/04/21 - Creation
#
"""
Logic to handle ReST CluCtrl command "network_update".
"""

# Public API
__all__ = ['handle_network_update', 'handle_rollback_bonding_migration']

from itertools import count, dropwhile, takewhile
import os
import re
import tempfile
from typing import (
    Any, Callable, Dict, Iterator, List, Mapping, NamedTuple, Optional,
    Sequence, Set, Tuple, TYPE_CHECKING, TypeVar
)
import xml.etree.ElementTree as ET

import exabox.ovm.clubonding as clubonding
from exabox.ovm.cludomufilesystems import shutdown_domu, start_domu
from exabox.core.Context import exaBoxContext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogInfo, ebLogError
from exabox.utils.common import tails
from exabox.utils.node import (
    connect_to_host, node_cmd_abs_path_check, node_exec_cmd,
    node_exec_cmd_check, node_read_text_file, node_write_text_file
)
from exabox.tools.ebOedacli.ebOedacli import ebOedacli

# We need to import exaBoxCluCtrl for type annotations, but it will cause a
# cyclic-import at runtime.  Thus we import it only when type-checking.  We
# still need to define type exaBoxCluCtrl or pylint will complain, though, so
# we just make it an alias to 'object' when not type-checking.
if TYPE_CHECKING:
    from exabox.ovm.clucontrol import exaBoxCluCtrl
else:
    exaBoxCluCtrl = object  # pylint: disable=invalid-name


A = TypeVar('A')


NET_SCRIPTS: str = "/etc/sysconfig/network-scripts"


class Bridge(NamedTuple):
    """Node bridges information obtained from brctl utility.

    The fields are just the parsed output of the "brctl show" command.
    """
    name: str
    id: str
    stp_enabled: str
    interfaces: List[str]


class KVMGuestInterface(NamedTuple):
    """KVM Guest connected interfaces information.

    The fields are just the parsed output of "virsh domiflist" command.
    """
    name: str
    if_type: str
    source: str
    model: str
    mac: str


class IfCfg(NamedTuple):
    """Basic fields from ifcfg-<ifname> config files under network-scripts.

    Represents the following fields of the interfaces configuration files:

    IPADDR=10.0.160.134
    NETMASK=255.255.240.0
    GATEWAY=10.0.160.1
    NETWORK=10.0.160.0
    BROADCAST=10.0.175.255
    MTU=9000
    """
    ipaddr: Optional[str]
    netmask: Optional[str]
    gateway: Optional[str]
    network: Optional[str]
    broadcast: Optional[str]
    mtu: Optional[int]


class NetUpdates(NamedTuple):
    """Supported network updates.

    Represents Net changes.

    Attributes:
        vlans: VLANID changes; (old_vlan, new_vlan)
        macs: MAC address changes; (vlan, old_mac, new_mac)

    Each of the above attributes is optional (can be None), which means no
    change for it if not present.

    NOTE: either of old_vlan/new_vlan can be None, which means "no vlan" (some
          times referred as VLAN 0, although not always the same thing).
    """
    vlans: Optional[Tuple[Optional[int], Optional[int]]]
    macs: Optional[Tuple[Optional[int], str, str]]


class NodeVMNetUpdates(NamedTuple):
    """Node network updates.

    Represent network changes for a VM in a Dom0.

    Attributes:
        dom0: FQDN of the Dom0
        domu_vm_name: name of the DomU VM in the Dom0 to affect
        net_updates: net updates; see NetUpdates for details.
    """
    dom0: str
    domu_vm_name: str
    net_updates: Mapping[str, NetUpdates]  # {(net_type, net_updates)}


Payload = Mapping[str, Any]


def get_node_bridges(node: exaBoxNode) -> Iterator[Bridge]:
    """Gets the bridges information of a node.

    :param node: exaBoxNode from where to get the bridges.
    :returns: map of bridge name -> bridge info.
    """
    BRCTL: str = node_cmd_abs_path_check(node, 'brctl', sbin=True)
    _, *brctl_show = node_exec_cmd_check(
        node, f"{BRCTL} show").stdout.splitlines()

    bridges_raw: List[str] = [
        lines[0] + ' '.join(takewhile(
        lambda line: len(line.split()) == 1, lines[1:]))
        for lines in map(list, tails(brctl_show))
        if len(lines[0].split()) > 1 ]

    for line in map(lambda line: line.split(), bridges_raw):
        yield Bridge(line[0], line[1], line[2], line[3:])


def get_ifcfg_contents(node: exaBoxNode, ifname: str) -> Optional[IfCfg]:
    """Gets the IfCfg fields of an interface in a given node.

    :param node: exaBoxNode from where to get the ifcfg file.
    :param ifname: str with interface name.
    :returns: IfCfg of interface if available.
    """
    ifcfg_path: str = f"{NET_SCRIPTS}/ifcfg-{ifname}"
    if not node.mFileExists(ifcfg_path):
        return None

    def get_field_value(
            lines: Sequence[str],
            field: str,
            decorator: Callable[[str], A] = lambda x: x) -> Optional[A]:
        for line in lines:
            if line.startswith(field):
                return decorator(line.split('=')[1])
        return None

    ifcfg: List[str] = node_read_text_file(node, ifcfg_path).splitlines()

    ipaddr: str = get_field_value(ifcfg, "IPADDR")
    netmask: str = get_field_value(ifcfg, "NETMASK")
    gateway: str = get_field_value(ifcfg, "GATEWAY")
    network: str = get_field_value(ifcfg, "NETWORK")
    broadcast: str = get_field_value(ifcfg, "BROADCAST")
    mtu: int = get_field_value(ifcfg, "MTU", int)

    return IfCfg(ipaddr, netmask, gateway, network, broadcast, mtu)


def get_kvm_guest_interfaces(
        host: exaBoxNode,
        guest: str) -> Iterator[KVMGuestInterface]:
    """Gets the interfaces information of a KVM guest in a given host.

    :param host: exaBoxNode of a KVM host.
    :param guest: str of the guest name.
    :returns: map of interface name -> interface info.
    """
    VIRSH: str = node_cmd_abs_path_check(host, 'virsh')
    _, _, *virsh_domiflist = node_exec_cmd_check(
        host, f"{VIRSH} domiflist {guest}").stdout.strip().splitlines()

    for line in map(lambda line: line.split(), virsh_domiflist):
        yield KVMGuestInterface(*line)


def get_kvm_guest_bridges(
        host: exaBoxNode,
        guest: str,
        guest_ifaces: Optional[Sequence[KVMGuestInterface]] = None
        ) -> Tuple[str, str, str, str]:
    """Gets all the bridges names of a KVM guest in a given host.

    :param host: exaBoxNode of a KVM host.
    :param guest: str of the guest name.
    :param guest_ifaces: Sequence of KVMGuestInterface if known.
    :returns: tuple of str [client, backup, pre-nat, post-nat]
    """
    if guest_ifaces is None:
        guest_ifaces = get_kvm_guest_interfaces(host, guest)

    client, backup = None, None
    client_backup: List[str] = []
    post_nat: str = ''
    for iface in guest_ifaces:
        if iface.source.startswith('vmbondeth0'):
            client_backup.append(iface.source)
        if iface.source.startswith('vmeth'):
            post_nat = iface.source
    if len(client_backup) == 2:
        client, backup = sorted(client_backup)
    if len(client_backup) == 1:
        client = client_backup[0]
        backup = None

    post_nat_id, *_ = re.search(r'vmeth(\d\d\d)', post_nat).groups()
    LS: str = node_cmd_abs_path_check(host, 'ls')
    pre_nat_file_ret: str = node_exec_cmd(
        host, f"{LS} {NET_SCRIPTS}/ifcfg-vmeth0*:{post_nat_id}")
    if pre_nat_file_ret.exit_code == 0:
        pre_nat, *_ = re.search(
            r'ifcfg-(vmeth0(\.\d+)?):', pre_nat_file_ret.stdout).groups()
    else:
        pre_nat_file_ret: str = node_exec_cmd(
            host, f"{LS} {NET_SCRIPTS}/ifcfg-vmbondeth0*:{post_nat_id}")
        if pre_nat_file_ret.exit_code == 0:
            pre_nat, *_ = re.search(
                r'ifcfg-(vmbondeth0(\.\d+)?):', pre_nat_file_ret.stdout).groups()
        else:
            pre_nat = None

    return client, backup, pre_nat, post_nat


def get_kvm_guest_nat_ips(
        host: exaBoxNode,
        guest: str,
        guest_nat_bridges: Optional[Tuple[str, str]] = None
        ) -> Tuple[str, str]:
    """Gets the NAT IP addresses of a KVM guest in a given host.

    This method returns the IP of the pre-NAT bridge and the internal IP

    :param host: exaBoxNode of a KVM host.
    :param guest: str of the guest name.
    :param guest_nat_bridges: Tuple of [pre-nat, post-nat] guest bridges if
                              known.
    :returns: Tuple of str with [NAT IP, internal IP] of the guest.
    """
    if guest_nat_bridges is None:
        _, _, *guest_nat_bridges = get_kvm_guest_bridges(host, guest)

    pre_nat_iface, post_nat_iface = guest_nat_bridges
    post_nat_id, *_ = re.search(r'vmeth(\d\d\d)', post_nat_iface).groups()
    pre_nat: str = node_read_text_file(
        host, f"{NET_SCRIPTS}/ifcfg-{pre_nat_iface}:{post_nat_id}")
    nat_ip_line, *_ = \
        ( line for line in pre_nat.splitlines() if line.startswith('IPADDR') )
    _, nat_ip = nat_ip_line.split('=')

    ###
    # The pre-NAT guest bridge (vmethXXX) configuration file will contain the
    # following IPs:
    #
    # NETWORK=169.254.200.0
    # IPADDR=169.254.200.1
    # BROADCAST=169.254.200.3
    #
    # The only IP that is not included in this file if the actual guest
    # internal IP, but these IPs can be calculated with the following formulas:
    #
    # For any given vmethX(n):
    #
    # NETWORK       = 169.254.200.(4*n)
    # IPADDR        = 169.254.200.(4*n + 1)
    # (INTERNALIP)  = 169.254.200.(4*n + 2)
    # BROADCAST     = 169.254.200.(4*n + 3)
    #
    # So below code reads this configuration file and will calculate the guest
    # internal IP from the IPADDR by simply adding 1 to its last octet.
    ###
    post_nat: str = node_read_text_file(
        host, f"{NET_SCRIPTS}/ifcfg-{post_nat_iface}")
    post_nat_ip_line, *_ = ( line
        for line in post_nat.splitlines() if line.startswith('IPADDR') )
    _, post_nat_ip = post_nat_ip_line.split('=')
    post_nat_ip_octets: List[str] = post_nat_ip.split('.')
    internal_ip: str = \
        f"{'.'.join(post_nat_ip_octets[:3])}.{int(post_nat_ip_octets[3]) + 1}"

    return nat_ip, internal_ip


def get_kvm_guest_nat_routing(
        host: exaBoxNode,
        guest: str) -> Optional[List[str]]:
    """Gets the NAT routing information for a KVM guest in a given host.

    This method reads the VM maker auto-generated XML from the host under

    /EXAVMIMAGES/GuestImages/<guest>/<guest>.xml

    So it is assumed that this file exists because it will be taken as the
    source of truth.

    :param host: exaBoxNode of a KVM host.
    :param guest: str of the guest name.
    :returns: List of [NAT gateway, NAT egress IPs...] if available.
    """
    guest_xml_file: str = node_read_text_file(
        host, f"/EXAVMIMAGES/GuestImages/{guest}/{guest}.xml")
    guest_ifaces_xml: List[ET.Element] = \
        ET.fromstring(guest_xml_file).findall('Interfaces')

    for guest_iface_xml in guest_ifaces_xml:
        bridge_xml: Optional[ET.Element] = \
            guest_iface_xml.find('Bridge')
        if bridge_xml is None or bridge_xml.text != 'dummy':
            continue

        nat_egress_ips_xml: List[ET.Element] = \
            guest_iface_xml.findall('nategressipaddresses')
        gateway_xml: Optional[ET.Element] = \
            guest_iface_xml.find('Gateway')

        if gateway_xml is not None:
            return [gateway_xml.text] + \
                   [ ip_xml.text for ip_xml in nat_egress_ips_xml ]

    return None


def add_kvm_guest_nat_routing(
        host: exaBoxNode,
        guest: str,
        force: bool = False,
        host_default_gateway: Optional[str] = None,
        guest_nat_bridges: Optional[Tuple[str, str]] = None,
        guest_nat_ips: Optional[Tuple[str, str]] = None,
        guest_nat_routing: Optional[List[str]] = None):
    """Adds the missing NAT routing table and rules for a KVM guest.

    :param host: exaBoxNode of a KVM host.
    :param guest: str of the guest name.
    :param force: whether we should override the existing routing tables and
                  rules.
    :param host_default_gateway: str of host default gateway IP if known.
    :param guest_nat_bridges: Tuple of [pre-nat, post-nat] guest bridges if known.
    :param guest_nat_ips: Tuple of [NAT IP, internal IP] of the guest if known.
    :param guest_nat_routing: List of [NAT gateway, NAT egress IPs...] if known.
    """
    if host_default_gateway is None:
        interface_contents = get_ifcfg_contents(host, "vmeth0")
        if not interface_contents:
            interface_contents = get_ifcfg_contents(host, "vmbondeth0")
        host_default_gateway = interface_contents.gateway
    if guest_nat_bridges is None:
        _, _, *guest_nat_bridges = get_kvm_guest_bridges(host, guest)
    if guest_nat_ips is None:
        guest_nat_ips = get_kvm_guest_nat_ips(host, guest, guest_nat_bridges)
    if guest_nat_routing is None:
        guest_nat_routing = get_kvm_guest_nat_routing(host, guest)

    if guest_nat_routing is None:
        ebLogInfo(f"*** No available NAT routing information for DomU {guest}")
        return

    pre_nat_bridge, post_nat_bridge = guest_nat_bridges
    nat_gateway, *nat_egress_ips = guest_nat_routing
    _, internal_ip = guest_nat_ips

    if nat_gateway == host_default_gateway:
        ebLogInfo(f"*** NAT gateway for {guest} is the same as the host "
                  "default gateway, so we don't need to create any extra "
                  "rules/routes, skipping re-creation...")
        return

    route_file: str = f"{NET_SCRIPTS}/route-{post_nat_bridge}"
    rule_file: str = f"{NET_SCRIPTS}/rule-{post_nat_bridge}"
    if host.mFileExists(route_file) and host.mFileExists(rule_file):
        if not force:
            ebLogInfo(f"*** NAT routing info already available in {guest}, "
                      "skipping re-creation...")
            return

    post_nat_id, *_ = re.search(r'vmeth(\d\d\d)', post_nat_bridge).groups()
    table_id: int = int(post_nat_id) - 100
    routes: List[str] = [ f"{nat_egress_ip} via {nat_gateway} "
                          f"dev {pre_nat_bridge} table {table_id}"
                          for nat_egress_ip in nat_egress_ips ] + [""]
    rules: List[str] = [ f"from {internal_ip} to {nat_egress_ip} "
                         f"table {table_id} priority 1"
                         for nat_egress_ip in nat_egress_ips ] + [""]
    node_write_text_file(host, route_file, "\n".join(routes))
    node_write_text_file(host, rule_file, "\n".join(rules))

    IFDOWN: str = node_cmd_abs_path_check(host, 'ifdown', sbin=True)
    IFUP: str = node_cmd_abs_path_check(host, 'ifup', sbin=True)
    node_exec_cmd_check(host, f"{IFDOWN} {post_nat_bridge}")
    node_exec_cmd_check(host, f"{IFUP} {post_nat_bridge}")

    ebLogInfo(f"*** NAT routing info re-created for {guest}")


def update_guest_vm_maker_xml_nat(
        host: exaBoxNode,
        guest: str,
        ip: str,
        hostnames: Tuple[str, str],
        domainnames: Tuple[str, str],
        netmask: str,
        gateway: str,
        vlan_id: Optional[int] = None,
        nat_egress_ips: Sequence[str] = []):
    """Updated the Guest VM maker file with the given information.

    The updated will go under...
    /EXAVMIMAGES/GuestImages/<guest>/<guest>.xml

    :param host: exaBoxNode of a KVM host.
    :param guest: str of the guest name.
    :param ip: str of new NAT IP.
    :param hostnames: Tuple of old & new NAT hostname.
    :param domainnames: Tuple of old & new NAT domain names.
    :param netmask: str of the new NAT netmask IP.
    :param gateway: str of the new NAT gateway IP.
    :param vlan_id: int of new NAT VLAN ID or None if 0.
    :param net_egress_ips: List of str with NAT egress IPs.
    """
    guest_xml_path: str = f"/EXAVMIMAGES/GuestImages/{guest}/{guest}.xml"
    guest_xml_file: str = node_read_text_file(host, guest_xml_path)
    guest_xml: ET.Element = ET.fromstring(guest_xml_file)

    nat_interface_xml: Optional[ET.Element] = None
    for interface_xml in guest_xml.findall('Interfaces'):
        bridge_xml: Optional[ET.Element] = interface_xml.find('Bridge')
        if bridge_xml is not None and bridge_xml.text == 'dummy':
            nat_interface_xml = interface_xml
            break
    else:
        return

    nat_interface_xml.find('IP_address').text = ip
    nat_interface_xml.find('Netmask').text = netmask
    nat_interface_xml.find('Gateway').text = gateway

    vlan_id_xml: Optional[ET.Element] = nat_interface_xml.find('Vlan_id')
    if vlan_id is None:
        if vlan_id_xml is not None:
            nat_interface_xml.remove(vlan_id_xml)
    else:
        if vlan_id_xml is None:
            vlan_id_xml = ET.Element('Vlan_id')
            nat_interface_xml.append(vlan_id_xml)
        vlan_id_xml.text = f"{vlan_id}"

    nat_egress_ip_xmls: List[ET.Element] = \
        nat_interface_xml.findall('nategressipaddresses')
    for nat_egress_ip_xml in nat_egress_ip_xmls:
        nat_interface_xml.remove(nat_egress_ip_xml)
    for nat_egress_ip in nat_egress_ips:
        nat_egress_ip_xml: ET.Element = ET.Element('nategressipaddresses')
        nat_egress_ip_xml.text = nat_egress_ip
        nat_interface_xml.append(nat_egress_ip_xml)

    # stylize the XML
    guest_xml_str: str = ET.tostring(guest_xml).decode('utf8')
    if not guest_xml_str.endswith('\n'):
        guest_xml_str += '\n'
    if not guest_xml_str.startswith('<?xml'):
        guest_xml_str = \
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + \
            guest_xml_str

    # replace NAT hostname & domain names
    guest_xml_str = guest_xml_str.replace(*hostnames).replace(*domainnames)

    node_write_text_file(host, guest_xml_path, guest_xml_str)


# Calculate the bonding interface name for a given VLAN.
# For ExaCS the bonding id is always 0
# For example:
#   bond_for_vlan(0) == 'bondeth0'
#   bond_for_vlan(100) == 'bondeth0.100'
bond_for_vlan = lambda vlan: \
    clubonding.BOND_INTERFACE_FMT.format(f"0.{vlan}" if vlan else '0')


def apply_net_updates_to_xml(
        net_updates: Sequence[NodeVMNetUpdates],
        src_xml_path: str,
        dst_xml_path: str,
        oedacli_bin: str) -> None:
    """Apply net updates to given XML.

    Use oedacli to apply network updates.

    :param net_updates: updates to perform.
    :param src_xml_path: path to original XML.
    :param dst_xml_path: path to XML where changes will be present.
    :param oedacli_path: path to oedacli executable
    :returs: Nothing
    :raises Exception: if something went wrong.
    """
    oedacli = ebOedacli(
        aOedacliPath=oedacli_bin, aSaveDir=os.path.dirname(dst_xml_path),
        aLogFile=f'{dst_xml_path}.log', aDeploy=False)

    # insert 'SAVE ACTION' after every oedacli.mAppendCommand()
    oedacli.mSetAutoSaveActions(True)

    # don't insert 'MERGE ACTIONS' after every oedacli.mAppendCommand()
    oedacli.mSetAutoMergeActions(False)

    # build the oedacli commands to run
    for node_net_update in net_updates:
        domu = node_net_update.domu_vm_name

        for net_type, updates in node_net_update.net_updates.items():
            args = {}

            if updates.vlans:
                # NOTE: "no vlan" (i.e None) must be set to empty string;
                #       otherwise ebOedacli will ignore it.
                new_vlan = updates.vlans[1]
                args['VLANID'] = '' if new_vlan is None else str(new_vlan)

            if updates.macs:
                new_mac = updates.macs[2]
                args['MAC'] = new_mac

            if args:
                oedacli.mAppendCommand(
                    aCommand='ALTER NETWORK',
                    aArgs=args,
                    aWhere={'HOSTNAME': domu, 'NETWORKTYPE': net_type})

    # Run oedacli commands to generate updated XML.
    #
    # NOTE: This method will automatically insert command 'MERGE ACTIONS FORCE'
    #       at the end of list of actions to execute.
    oedacli.mRun(aLoadPath=src_xml_path, aSavePath=dst_xml_path)


def cluctrl_change_net_from_payload(
        cluctrl: exaBoxCluCtrl,
        payload: Payload,
        rollback: bool = False) -> Sequence[NodeVMNetUpdates]:
    """Change network description from changes in the payload.

    Updates network description of cluster from changes in the payload.  The
    expected shape of the payload is:

        {
            "nodes": [
                {
                    "hostname": "<dom0_fqdn",
                    "client": {                    # OPTIONAL
                        "mac": "<new_mac_addr>",       # OPTIONAL
                        "vlanag": "<new_vlanid>"       # OPTIONAL
                    },
                    "backup": {                    # OPTIONAL
                        "mac": "<new_mac_addr>",       # OPTIONAL
                        "vlanag": "<new_vlanid>"       # OPTIONAL
                    }
                },
                ...
            ]
        }

    Payload for rollback of bonding migration:

        {
            "nodes": [
                {
                    "hostname": "<dom0_fqdn>",
                    "client": {
                        "mac": "<old_mac_addr>"
                    },
                    "backup": {
                        "mac": "<old_mac_addr>"
                    }
                },
                ...
            ]
        }

    The payload represents changes to the networks of the VMs of the given
    Dom0s.  Currently only support changes to VLAN and MAC for both client
    and backup networks.

    For non-rollback mode, The changes are optional in the payload and no
    change to the specific value is performed if not present in the payload.
    If the new value is the same than the current one, no change is performed.

    NOTE: these changes are performed only to the cluctrl internal
          representation of the cluster's configuration; no change is done to
          the actual network in the cluster.

    Returns a sequence of changes performed (one per Dom0 affected).  See
    NodeVMNetUpdates for details.

    :param cluctrl: exaBoxCluCtrl object to affect.
    :param payload: payload with description with changes.
    :param rollback: rollback of bonding migration or normal mode.
    :returns: sequence with changes performed.
    :raises Exception: if something went wrong.
    """

    # DomU VM names are just the non-Nat FQDN of the DomUs
    dom0_vms = dict(cluctrl.mReturnDom0DomUPair())
    vlan_ids_rollback = {"client": 0, "backup": 1}

    def __build_node_net_update(
            node_payload: Payload,
            rollback: bool) -> Optional[NodeVMNetUpdates]:
        dom0 = node_payload['hostname']
        domu_vm_name = dom0_vms[dom0]

        domu_networks = cluctrl.mGetVMNetConfigs(domu_vm_name)
        confs = {}

        # Extract net update info for client and backup networks and update net
        # configs with new values.
        for net_type in ('client', 'backup'):
            net_payload = node_payload.get(net_type)

            if net_payload:
                net_conf = domu_networks[net_type]

                # get current vlan/mac
                curr_vlan = net_conf.mGetNetVlanId()
                curr_mac = net_conf.mGetNetMacAddr()

                # Fix value of current vlan.  "UNDEFINED" means "no vlan",
                # which we represent here as None.
                if curr_vlan == "UNDEFINED":
                    curr_vlan = None
                else:
                    curr_vlan = int(curr_vlan)

                vlans = None
                macs = None

                # Get new vlan from the payload and update it in cluctrl.
                #
                # NOTE: 'vlantag' can be 'null' (i.e. None), which is a valid
                #       value.
                if 'vlantag' in net_payload:
                    new_vlan = net_payload['vlantag']

                    if new_vlan is not None:
                        new_vlan = int(new_vlan)

                    if new_vlan != curr_vlan:
                        vlans = (curr_vlan, new_vlan)
                        net_conf.mSetNetVlanId(new_vlan)
                elif rollback:
                    new_vlan = vlan_ids_rollback[net_type]
                    if new_vlan != curr_vlan:
                        vlans = (curr_vlan, new_vlan)
                        net_conf.mSetNetVlanId(new_vlan)

                # Get new MAC from the payload and update it in cluctrl.
                #
                # NOTE: notice that we use the current vlan for the MAC
                # For rollback, we will try to update the mac address to the
                # one provided in payload - Note that this will be the old mac
                # address which would be there for a non bonded env
                new_mac = net_payload.get('mac')
                if new_mac and new_mac != curr_mac:
                    macs = (curr_vlan, curr_mac, new_mac)
                    net_conf.mSetMacAddr(new_mac)

                # add update config only if there are indeed changes
                if vlans or macs:
                    confs[net_type] = NetUpdates(vlans=vlans, macs=macs)

        if confs:
            return NodeVMNetUpdates(
                dom0=dom0, domu_vm_name=domu_vm_name, net_updates=confs)

        return None  # no updates

    entries = []
    # update network in cluctrl and skip entries with no updates
    for _node in payload['nodes']:
        entries.append(__build_node_net_update(_node, rollback))
    updates = tuple(e for e in entries if e is not None)

    #
    # Patch XML
    #

    # create new XML file that will contain the changes
    cluster_conf_dir = os.path.join('clusters', cluctrl.mGetKey(), 'config')
    with tempfile.NamedTemporaryFile(
            prefix='network_update_', suffix='.xml', dir=cluster_conf_dir,
            delete=False) as xml_fd:
        new_xml = xml_fd.name

    oedacli_bin = os.path.join(cluctrl.mGetOedaPath(), 'oedacli')

    # generate updated XML
    apply_net_updates_to_xml(
        net_updates=updates, src_xml_path=cluctrl.mGetPatchConfig(),
        dst_xml_path=new_xml, oedacli_bin=oedacli_bin)

    # point to updated XML
    cluctrl.mSetPatchConfig(new_xml)

    return updates


# Expected arguments: <vm_name> <net_type> <new_value> <old_value>
#
# where net_type = {client, backup, ...}
#
# NOTE: Currently a script from clubonding bond monitor RPM is used for this.
#       This might change in the future.
#
# NOTE2: This is private logic of both clubonding and bondmonitor, and it's
#        being used here under consent of the owners.  Please don't replicate
#        anywhere else without explicit consent of the owners of those
#        components.
CHANGE_VLAN_CMD_FMT = \
    '/opt/exacloud/bondmonitor/bond_utils.py change_vlan {} {} {} {}'
CHANGE_MAC_CMD_FMT = \
    '/opt/exacloud/bondmonitor/bond_utils.py change_mac {} {} {} {} {}'
REMOTE_ROLLBACK_VLANID = '/opt/exacloud/bondmonitor/rollback_vlanid.sh'


def update_networks(
        ctx: exaBoxContext,
        net_update_configs: Sequence[NodeVMNetUpdates],
        rollback: bool = False) -> None:
    """Apply changes to VM networks in Dom0s.

    Perform actual network changes as described in net_update_configs.  See
    NodeVMNetUpdates for a description of how the changes are inerpreted.

    :param ctx: context to use when establishing connections to the hosts.
    :param net_update_configs: descriptions of changes to perform.
    :param rollback: rollback of bonding migration.
    :returns: nothing
    :raises ExacloudRuntimeError: if an error occurred.
    """

    # NOTE: Here we use some private functions from clubonding as an EXCEPTION.
    #       Please don't do this anywhere else without first contacting owner
    #       of clubonding.

    # get clubonding bond monitor RPM.
    rpm_path = clubonding.get_bond_monitor_rpm_local_path()
    nft_rules = '/etc/nftables/exadata.nft'

    def __update_net(node_conf: NodeVMNetUpdates,
                     rollback: bool) -> None:
        vm_name = node_conf.domu_vm_name
        with connect_to_host(node_conf.dom0, ctx) as node:
            # Shutdown VM if rollback
            if rollback:
                shutdown_domu(node, vm_name)
            update_nft_rules = node.mFileExists(nft_rules)

            # We must be sure bond monitor RPM is installed for change vlan/mac
            # commands to work.
            clubonding.node_create_bonding_dirs(node)
            clubonding.install_bond_monitor_rpm(node, rpm_path)

            for net_type, conf in node_conf.net_updates.items():
                # NOTE: we need to change the MAC before VLAN because we pass
                #       the current VLAN to CHANGE_MAC_CMD_FMT.
                if conf.macs:
                    curr_vlan, old_mac, new_mac = conf.macs
                    cmd = CHANGE_MAC_CMD_FMT.format(
                        vm_name, curr_vlan, net_type, new_mac, old_mac)
                    node_exec_cmd_check(node, cmd)

                if conf.vlans:
                    old_vlan, new_vlan = conf.vlans

                    # NOTE: the command to change VLANs in Dom0 expects vlan 0
                    #       to mean "no vlan" (which we represent with None).
                    #       We have to adjust the values.
                    old_vlan = 0 if old_vlan is None else old_vlan
                    new_vlan = 0 if new_vlan is None else new_vlan

                    if not rollback:
                        cmd = CHANGE_VLAN_CMD_FMT.format(
                            vm_name, net_type, new_vlan, old_vlan)
                        node_exec_cmd_check(node, cmd)

                    # update the nftables rules for this cluster if needed
                    if update_nft_rules:
                        old_bond = f'"{bond_for_vlan(old_vlan)}"'
                        new_bond = f'"{bond_for_vlan(new_vlan)}"'
                        cmd = (f"/bin/sed -i 's/{old_bond}/{new_bond}/g' "
                               f"{nft_rules}")
                        node_exec_cmd_check(node, cmd)

            if rollback:
                # call the rollback vlan script
                if node.mFileExists(REMOTE_ROLLBACK_VLANID):
                    cmd = f"{REMOTE_ROLLBACK_VLANID} {vm_name}"
                    node_exec_cmd_check(node, cmd)
                else:
                    msg = f'{REMOTE_ROLLBACK_VLANID} script does not'\
                            f' exist on DOM0 {node_conf.dom0}.'
                    ebLogError(msg)
                    raise ExacloudRuntimeError(0x805, 0xA, msg)

            if update_nft_rules:
                cmd = "/bin/systemctl restart nftables"
                node_exec_cmd_check(node, cmd)
            # Start VM in case it is rollback of bonding migration
            if rollback:
                start_domu(node, vm_name, wait_for_connectable=False)

    for conf in net_update_configs:
        try:
            __update_net(conf, rollback)
            ebLogInfo(f'VM network updated: {conf}')
        except Exception as exp:
            msg = f'Falied to update VM network: {exp}\n config: {conf}'
            ebLogError(msg)
            raise ExacloudRuntimeError(aErrorMsg=msg) from exp


#
# Public API
#

def handle_network_update(cluctrl: exaBoxCluCtrl) -> None:
    """Update networks of cluster as described in JSON payload.

    Updates the VM networks in the cluster as described in the JSON payload
    (see cluctrl_change_net_from_payload() for a description of the payload).

    On return, if the operation succeeds:
      - The networks in the cluster have been updated;
      - Network descriptions in cluctrl have been updated;
      - cluctrl points to an XML with networks updated.

    :param cluctrl: exaBoxCluCtrl on which perform the update.
    :returns: nothing
    :raises ExacloudRuntimeError: if an error occurred.
    """
    try:
        payload = cluctrl.mGetArgsOptions().jsonconf

        # update networks in cluctrl and XML
        net_update_confs = cluctrl_change_net_from_payload(cluctrl, payload)

        if not net_update_confs:
            ebLogInfo('CluCtrl:network_update: no network update required; '
                      'skipping.')
            return

        # update networks in cluster
        update_networks(cluctrl.mGetCtx(), net_update_confs)
    except Exception as exp:
        msg = f'CluCtrl:network_update failed: {exp}'
        ebLogError(msg)
        raise ExacloudRuntimeError(0x805, 0xA, msg) from exp

    ebLogInfo('CluCtrl:network_update: update succeeded.')


def handle_rollback_bonding_migration(cluctrl: exaBoxCluCtrl) -> None:
    """
    Does rollback of network which was migrated to bonding enabled network
    during bonding migration using network update API.

    This method first takes care of updating the xml with correct network info
    and then, it does the following for each VM sequentially:
    - Stop VM
    - Call rollback vlan ids script for the VM
    - Change Mac address to old mac
    - Start VM

    :param cluctrl: exaBoxCluCtrl on which to perform the update.
    :returns: nothing
    :raises ExacloudRuntimeError: if an error occurred.
    """
    try:
        payload = cluctrl.mGetArgsOptions().jsonconf

        # update networks in cluctrl and XML - in rollback mode i.e. rolling
        # back bonded env to non bonded env
        net_update_confs = cluctrl_change_net_from_payload(cluctrl, payload,
                                                           rollback=True)

        if not net_update_confs:
            ebLogInfo('CluCtrl:rollback_bonding_migration: no network update '\
                      'required; skipping.')
            return

        # update networks in cluster - in rollback mode i.e. rolling
        # back bonded env to non bonded env
        update_networks(cluctrl.mGetCtx(), net_update_confs, rollback=True)
    except Exception as exp:
        msg = f'CluCtrl:rollback_bonding_migration failed: {exp}'
        ebLogError(msg)
        raise ExacloudRuntimeError(0x805, 0xA, msg) from exp

    ebLogInfo('CluCtrl:rollback_bonding_migration: update succeeded.')
