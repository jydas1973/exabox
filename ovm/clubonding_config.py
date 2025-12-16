#
# clubonding_config.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      clubonding_config.py - Bonding configuration parsing logic
#
#    DESCRIPTION
#      Bonding configuration parsing logic.
#
#    NOTES
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    11/26/25 - Bug 38636333 - EXACLOUD PYTHON:ADD INSTANTCLIENT TO
#                           LD_LIBRARY_PATH
#    prsshukl    11/20/25 - Bug 38675257 - EXADBXS PROVISIONING FAILING IN
#                           FETCHUPDATEDXMLFROMEXACLOUD
#    scoral      10/28/25 - Enh 38452359: Added domu_admin_ip & domu_admin_vlan
#                           to NodeBondingConf.
#    aararora    07/30/25 - ER 38132942: Single stack support for ipv6
#    zpallare    11/01/24 - Bug 37235760 - EXACS:X11M:No eth0: setup bonding
#                           fails at bondingsetupteardown
#    aararora    10/04/24 - Bug 37133807: Get scan IPs for ipv6 from xml
#    aararora    09/17/24 - Bug 37031113: Scan entries not added to monitor
#                           conf
#    aararora    08/28/24 - Bug 36998256: IPv6 fixes
#    scoral      06/18/24 - Bug 36740875: Add domu_client to NodeBondingConf.
#    aararora    04/16/24 - ER 36485120: Support IPv6 in exacloud
#    aararora    03/20/24 - Bug 33667094: Add Rollback Migration flow to list
#                           of operations
#    scoral      10/03/23 - Enh 35946456: Configure bondmonitor for envs with
#                           eth0 removed during bonding setup.
#    scoral      05/24/23 - Bug 35285863: Increase arp_interval from 100 to 1000
#    aararora    12/04/22 - Bug 34640693: Add bonding_operation for delete
#                           compute.
#    scoral      08/10/22 - Enh 34429828: made bonding_network and
#                           customer_network optional fields in payload.
#    scoral      07/28/22 - Bug 34430106: add extract_networks_from_monitor_conf
#    scoral      04/03/22 - Enh 34022930: add support for Custom VIPs parsing
#                           in Create-service and Elastic-reshape payloads.
#    jlombera    03/18/22 - Bug 33244220: add support for MultiVM
#    jlombera    10/12/21 - Bug 33461455: add backup VIPs to MonitorConf
#    jlombera    05/21/21 - Bug 32912942: moving bonding config parsing logic
#                           to clubonding_config.py
#    jlombera    05/21/21 - Creation
#
"""
Bonding payload configuration parsing logic.

Two payload formats are supported, one is used during create service and the
other during elastic reshape.  Following are example payloads, only the
required fields for bonding are shown.

    * Create-service payload:

    {
       "bonding_operation": "create-service",
       "customer_network": {                                 # [optional]
          "nodes": [
             {
                "fqdn": "sea201108exdd003.client1.bonding.oraclevcn.com",
                "monitoring": {
                   "bond0": {
                      "ip": "192.168.1.52",
                      "netmask": "255.255.255.0",
                      "gateway": "192.168.1.1",
                      "preferred_interface": "eth1",
                      "cavium_ids": [
                            {
                                "id": "id5",
                                "interface": "eth1"
                            },
                            {
                                "id": "id6",
                                "interface": "eth2"
                            }
                        ],
                   },
                   "bond1": {
                      "ip": ...,
                      "netmask": ...,
                      "gateway": ...,
                      "preferred_interface": ...,
                      "cavium_ids": ...
                   },
                   ...
                },
                "admin_network": [                           # [optional]
                  {
                    "fqdn": "sea201733exdd008.client1.bonding.oraclevcn.com",
                    "ip": "10.0.160.137",
                    "vlantag": 0,
                    "mac": "b8:3f:d2:31:1c:39"               # [optional]
                  },
                  {
                    "fqdn": "sea201733exddu0801.client1.bonding.oraclevcn.com",
                    "ip": "10.0.160.182",
                    "vlantag": 3168,
                    "mac": "b8:3f:d2:31:1c:39"               # [optional]
                  },
                  {
                    "fqdn": "sea201733exddu0802.mvm.bonding.oraclevcn.com",
                    "ip": "10.1.4.131",
                    "vlantag": 3169,
                    "mac": "b8:3f:d2:31:1c:39"               # [optional]
                  },
                  ...
                ],
                "vip": {                                     # Mon
                   "ip": "10.0.3.124",
                   "ipv6": "::"
                },
                "client": {                                  # Mon
                   "domu_oracle_name": "sea201108exddu0301",
                   "ip": "10.0.3.126",
                   "ipv6": "::",
                   "vlantag":1,
                   "mac": "00:00:17:01:06:C3"
                },
                "backup": {                                  # Mon
                   "ip": "10.0.4.80",
                   "ipv6": "::",
                   "vlantag": "2",
                   "mac": "00:00:17:01:B7:9F",
                   "vip": "172.16.65.68",                     # [optional]
                   "v6vip": "::"
                },
                "admin": {                                    # [optional]
                   "hostname": "iad103709exddu1701",
                   "ip": "10.1.0.128",
                   "vlantag": 3001
                }
             },
             ...
          ],
          "scan": {                                          # Mon
             "ips": [
                "10.0.3.128",
                "10.0.3.130",
                "10.0.3.129",
                ...
             ],
             "v6ips": [
                 ::
             ]
          },
          "backup_scans": {                                  # Mon [optional]
             "ips": [
                "10.0.4.82",
                "10.0.4.83",
                "10.0.4.84",
                ...
             ],
             "v6ips": [
                 ::
             ]
          },
          "customvip": [                                     # [optional]
             {
                "interfacetype": "client/backup",
                "ip": "10.0.0.5",
                "ipv6": "::",
                "standby_vnic_mac": "00:09:A9:78:67"
             },
             ...
          ]
       }
    }


    * Elastic-reshape payload:

    {
      "bonding_operation": "add-compute",
      "reshaped_node_subset": {
        "added_computes": [
          {
            "compute_node_hostname":
                "iad103709exdd017.iad103709exd.adminiad1.oraclevcn.com",
            "virtual_compute_info": {
              "network_info": {
                "virtualcomputenetworks": [
                  {
                    "client": [                              # Mon
                      {
                        "nathostname": "iad103709exddu1701",
                        "ipaddr": "10.0.0.68",
                        "ipv6addr": "::",
                        "vlantag": "1",
                        "mac": "00:10:69:E5:EF:85"
                      }
                    ]
                  },
                  {
                    "backup": [                              # Mon
                      {
                        "ipaddr": "10.0.32.26",
                        "ipv6addr": "::",
                        "vlantag": "2",
                        "mac": "02:00:17:00:FF:6F",
                        "vip": "172.16.65.68",                # [optional]
                        "v6vip": "::"
                      }
                    ]
                  },
                  {
                    "admin": [                                # [optional]
                      {
                        "hostname": "iad103709exddu1701",
                        "ipaddr": "10.1.0.128",
                        "vlantag": 3001
                      }
                    ]
                  },
                  {
                    "monitoring": {
                       "bond0": {
                          "ip": "192.168.1.52",
                          "netmask": "255.255.255.0",
                          "gateway": "192.168.1.1",
                          "preferred_interface": "eth1",
                          "cavium_ids": [
                                {
                                    "id": "id5",
                                    "interface": "eth1"
                                },
                                {
                                    "id": "id6",
                                    "interface": "eth2"
                                }
                            ],
                       },
                       "bond1": {
                          "ip": ...,
                          "netmask": ...,
                          "gateway": ...,
                          "preferred_interface": ...,
                          "cavium_ids": ...
                       },
                       ...
                    }
                  },
                  {
                    "vip": [                                 # Mon
                      {
                        "ipaddr": "10.0.0.76",
                        "ipv6addr": "::"
                      }
                    ]
                  }
                ]
              }
            }
          }
        ]
      },
      "customer_network": {                                  # [optional]
        "customvip": [                                       # [optional]
          {
            "interfacetype": "client/backup",
            "ip": "10.0.0.5",
            "ipv6": "::",
            "standby_vnic_mac": "00:09:A9:78:67"
          },
          ...
        ]
      }
    }

    Fields marked with '# Mon' are only required if we want to also configure
    the bonding monitor.  Fields marked with '[optional]' are optional.

    Both payloads contain essentially the same information, just structured
    differently.  The exception is scan IPs, they are not provided in the
    elastic reshape payload.  That information is extracted from the cluster
    XML in that case.

    The delete service payload is slightly different:

    {
       "bonding_operation": "delete-service",
       "bonding_network": {  # "bonding_network" instead of "customer_network"
          "nodes": [
             {
             ...  # Everything else as Create-service payload

"""

# Public API
__all__ = [
    'BondIfaceConf', 'MonitorBondCaviumInfo', 'MonitorConf', 'NodeBondingConf',
    'Payload', 'PayloadBondOp', 'build_bonded_bridge_ipconf_xml',
    'extract_bonding_conf_from_payload', 'get_bonding_operation_from_payload',
    'MonitorConfType'
]

import copy
import json
from enum import Enum
from ipaddress import IPv4Address, IPv4Interface, IPv6Address
from typing import Any, Dict, Mapping, NamedTuple, Optional, Sequence

from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogWarn
from exabox.network.NetworkUtils import NetworkUtils

#
# Auxiliary data structures and types
#

# Simple aliases for convenience/documentation
Payload = Mapping[str, Any]
MonitorConf = str
MonitorBondCaviumInfo = str


class MonitorConfType(Enum):
    CUSTOMER    = 'customer'
    ADMIN       = 'admin' 


class BondIfaceConf(NamedTuple):
    """Network interface bonding configuration.

    Internal, auxiliary NamedTuple to keep bonding configuration related to the
    network interfaces.
    """
    bond_id: int
    ip_addr: IPv4Address
    netmask: IPv4Address
    gateway: IPv4Address
    primary_interface: str
    secondary_interface: str


class NodeBondingConf(NamedTuple):
    """Node bonding configuration.

    Internal, auxiliary NamedTuple to keep bonding configuration specific to a
    Dom0.
    """
    dom0: str
    domu: str = ''
    domu_client: str = ''
    domu_admin_ip: str = ''
    domu_admin_vlan: int = 0
    bond_iface_confs: Sequence[BondIfaceConf] = ()
    bond_cavium_info: MonitorBondCaviumInfo = ''
    monitor_conf: MonitorConf = ''
    monitor_conf_type: MonitorConfType = MonitorConfType.CUSTOMER


class NodeNetworkConf(NamedTuple):
    """Node network configuration parameters needed for bonding configuration.

    Internal, auxiliary NamedTuple to keep bonding configuration related to the
    monitor.
    """
    interface_type: str = ''
    mac: str = ''
    standby_vnic_mac: str = ''
    vlantag: Optional[int] = None


class PayloadBondOp(Enum):
    """Enum with allowed values of "bonding_operation" in payload."""
    SetupBridge = "setup-bonding"
    CleanupBridge = "delete-bonding"
    CreateService = "create-service"
    DeleteService = "delete-service"
    AddCompute = "add-compute"
    VMBackupRestore = "vmbackup-restore"
    ReconfigService = "reconfig-service"
    MigrationFlow = "migration-flow"
    DeleteCompute = "delete-compute"
    RollbackMigration = "rollback-migration"

#
# Payload parsing functions
#


MAX_NR_BONDS = 4


def extract_bond_iface_confs(
    node_payload: Payload,
    bonding_operation: PayloadBondOp) -> Sequence[BondIfaceConf]:
    """Extract node net interface bonding configurations.

    :param node_payload: node payload.
    :returns: sequence (possibly empty) of BondIfaceConf's.
    :raises Exception: if payload is invalid or malformed.
    """
    monitoring = node_payload['monitoring']

    bond_confs = []
    for bond_id in range(MAX_NR_BONDS):
        bond = monitoring.get(f'bond{bond_id}', None)

        if bond:
            # Create intermediate IPv4Interface just to validate that the
            # ip/netmask are valid.
            gateway = None
            ip_interface = None
            if bonding_operation != PayloadBondOp.RollbackMigration:
                ip_interface = IPv4Interface(f"{bond['ip']}/{bond['netmask']}")
                gateway = IPv4Address(bond['gateway'])

            primary_interface = bond['preferred_interface'].lower()
            secondary_interface = None
            if bonding_operation != PayloadBondOp.RollbackMigration:
                slave_interfaces = [
                    cid['networkinterface'].lower() for cid in\
                        bond['cavium_ids']]
                # secondary interface will be the first one that is not the
                # primary
                slave_interfaces.remove(primary_interface)
                secondary_interface = slave_interfaces[0]

            bond_confs.append(
                BondIfaceConf(
                    bond_id=bond_id,
                    ip_addr=ip_interface.ip if ip_interface else None,
                    netmask=ip_interface.netmask if ip_interface else None,
                    gateway=gateway if gateway else None,
                    primary_interface=primary_interface,
                    secondary_interface=secondary_interface
                )
            )

    return tuple(bond_confs)


def extract_bond_cavium_info(node_payload: Payload) -> MonitorBondCaviumInfo:
    """Extract node bond cavium info.

    :param node_payload: node payload.
    :returns: bond cavium info.
    :raises Exception: on invalid/malformed payload.
    """
    monitoring = node_payload['monitoring']

    bond_cavium_infos = {}
    for bond_id in range(MAX_NR_BONDS):
        bond_name = f'bond{bond_id}'
        bond = monitoring.get(bond_name, None)

        if bond:
            bond_cavium_infos[bond_name] = bond['cavium_ids']

    return json.dumps(bond_cavium_infos, indent=2)


def build_monitor_conf(
        node_payload: Payload,
        scan_ips: Sequence[IPv4Address],
        backup_scan_ips: Sequence[IPv4Address],
        scan_ipv6: Sequence[IPv6Address] = (),
        backup_scan_ips_ipv6: Sequence[IPv6Address] = ()) -> MonitorConf:
    """Build a monitor configuration.

    :param node_payload: node payload.
    :param scan_ips: scan IPs.
    :param backup_scan_ips: backup scan IPs.
    :returns: monitor configuration
    :raises Exception: if payload invalid or malformed.
    """
    # The use of many local variables its ok in this function
    # pylint: disable=too-many-locals
    client = node_payload['client']
    backup = node_payload['backup']
    admin = node_payload.get('admin') or {}
    domu = admin.get('hostname', client['domu_oracle_name'])

    client_mac = client['mac']
    client_standby_mac = client.get('standby_vnic_mac')
    client_vlantag = int(client.get('vlantag', 0))

    backup_mac = backup['mac']
    backup_standby_mac = backup.get('standby_vnic_mac')
    backup_vlantag = int(backup.get('vlantag', 0))
    nw_utils = NetworkUtils()

    def __build_client_entry(
            ip_addr: IPv4Address,
            floating: bool, ip_type: str, ipv6_addr: IPv6Address = "::"
            ) -> Dict[str, Any]:
        return {'type': ip_type, 'ip': str(ip_addr), 'ipv6': str(ipv6_addr),
                'interface_type': 'client', 'mac': client_mac,
                'standby_vnic_mac': client_standby_mac,
                'vlantag': client_vlantag, 'floating': floating}

    def __build_backup_entry(
            ip_addr: IPv4Address,
            floating: bool, ip_type: str, ipv6_addr: IPv6Address = "::"
            ) -> Dict[str, Any]:
        return {'type': ip_type, 'ip': str(ip_addr), 'ipv6': str(ipv6_addr),
                'interface_type': 'backup', 'mac': backup_mac,
                'standby_vnic_mac': backup_standby_mac,
                'vlantag': backup_vlantag, 'floating': floating}

    # Collect entries for MonitorConf.  Wrap IPs in IPv4Address() to make sure
    # they are valid.

    entries = []
    # Scan IPs
    length_scan_ipv6 = len(scan_ipv6)
    for index in range(len(scan_ips)):
        if index < length_scan_ipv6:
            # dual stack
            entries.append(__build_client_entry(
                scan_ips[index], floating=True,
                ip_type="scan_ip", ipv6_addr=scan_ipv6[index]))
        else:
            # IPv4 only
            entries.append(__build_client_entry(
                scan_ips[index], floating=True,
                ip_type="scan_ip"))
    else:
        if len(scan_ips) == 0:
            # IPv6 only
            for ipv6 in scan_ipv6:
                entries.append(__build_client_entry(
                    '0.0.0.0', floating=True, ip_type="scan_ip",
                    ipv6_addr=ipv6))

    length_backup_scan_ips_ipv6 = len(backup_scan_ips_ipv6)
    for index in range(len(backup_scan_ips)):
        # dual stack
        if index < length_backup_scan_ips_ipv6:
            entries.append(__build_backup_entry(
                backup_scan_ips[index], floating=True,
                ip_type="scan_ip", ipv6_addr=backup_scan_ips_ipv6[index]))
        else:
            # ipv4 only
            entries.append(__build_backup_entry(
                backup_scan_ips[index], floating=True,
                ip_type="scan_ip"))
    else:
        if len(backup_scan_ips) == 0:
            # IPv6 only
            for ipv6 in backup_scan_ips_ipv6:
                entries.append(__build_backup_entry(
                    '0.0.0.0', floating=True, ip_type="scan_ip",
                    ipv6_addr=ipv6))

    # Host IPs
    ipv4, ipv6 = nw_utils.mGetIPv4IPv6PayloadNotNoneValues(client)

    entries.append(
        __build_client_entry(
            IPv4Address(ipv4), floating=False, ip_type="host_ip",
            ipv6_addr=IPv6Address(ipv6)))

    ipv4, ipv6 = nw_utils.mGetIPv4IPv6PayloadNotNoneValues(backup)

    entries.append(
        __build_backup_entry(
            IPv4Address(ipv4), floating=False, ip_type="host_ip",
            ipv6_addr=IPv6Address(ipv6)))

    # VIPs.  These are optional.
    if 'vip' in node_payload:
        ipv4, ipv6 = nw_utils.mGetIPv4IPv6PayloadNotNoneValues(
            node_payload['vip'])
        entries.append(__build_client_entry(ipv4, floating=True, ip_type="vip",
                                            ipv6_addr=ipv6))

    if "vip" in backup:
        ipv4, ipv6 = nw_utils.mGetIPv4IPv6PayloadNotNoneValues(backup,
                                                               key_single_stack='vip',
                                                               key_dual_stack='v6vip')
        entries.append(
            __build_backup_entry(ipv4, floating=False, ip_type="vip",
                                 ipv6_addr=ipv6))

    # Build the MonitorConf (just a JSON string; we pretty print it just to
    # make it easy to read, but it's not required).
    return json.dumps({domu: entries}, indent=2)


def build_monitor_admin_conf(
        node_payload: Payload) -> MonitorConf:
    """Build a monitor admin configuration.

    :param node_payload: node payload.
    :returns: monitor admin configuration.
    :raises Exception: if payload invalid or malformed.
    """
    entries = [
        {
            'type': 'admin_ip',
            'ip': entry.get('ip', ''),
            'interface_type': 'admin_bondmonitor',
            'mac': entry.get('mac', ''),
            'standby_vnic_mac': '',
            'vlantag': str(entry.get('vlantag', 0)),
            'floating': False
        }
        for entry in node_payload.get('admin_network', [])
    ]
    return json.dumps({'monitor_admin': entries}, indent=2)


def build_node_bonding_conf(
        node_payload: Payload,
        extract_monitor_conf: bool,
        scan_ips: Sequence[IPv4Address],
        backup_scan_ips: Sequence[IPv4Address],
        bonding_operation: PayloadBondOp,
        dom0s_domus: Mapping[str, str]={},
        scan_ipv6: Sequence[IPv6Address] = (),
        backup_scan_ips_ipv6: Sequence[IPv6Address] = ()) -> NodeBondingConf:
    """Build node bonding configuration.

    :param node_payload: node payload.
    :param extract_monitor_conf: whether also extract monitor configuration.
    :param scan_ips: scan IPs; ignored if extract_monitor_conf is False.
    :param backup_scan_ips: backup scan IPs; ignored if extract_monitor_conf
        is False.
    :param bonding_operation: Specified the bonding operation
    :param dom0s_domus: Mapping of Dom0s FQDNs -> DomUs client FQDNs.
    :returns: NodeBondingConf
    :raises Exception: if payload is invalid/malformed.
    """
    dom0 = node_payload['fqdn']
    domu = ''
    domu_client = dom0s_domus.get(dom0, '')
    if (bonding_operation == PayloadBondOp.DeleteCompute 
        or bonding_operation == PayloadBondOp.VMBackupRestore):
        bond_iface_confs = ()
        bond_cavium_info = ''
    else:
        bond_iface_confs = extract_bond_iface_confs(node_payload,
                                                    bonding_operation)
        bond_cavium_info = ''
        if bonding_operation != PayloadBondOp.RollbackMigration:
            bond_cavium_info = extract_bond_cavium_info(node_payload)
    monitor_conf = ''
    monitor_conf_type = MonitorConfType.CUSTOMER
    domu_admin_ip = ''
    domu_admin_vlan = 0

    if extract_monitor_conf or ('eth0_removed' in node_payload and \
        node_payload['eth0_removed'].lower() == 'true'):
        # extract client and backup networks configuration
        if 'client' in node_payload and 'backup' in node_payload:
            domu = (node_payload.get('admin') or {}).get('hostname')
            if domu is None:
                domu = node_payload['client']['domu_oracle_name']
            monitor_conf = build_monitor_conf(
                node_payload, scan_ips, backup_scan_ips, scan_ipv6,
                backup_scan_ips_ipv6)

            domu_admin_ip = (node_payload.get('admin') or {}).get('ip')
            if domu_admin_ip is None:
                domu_admin_ip = node_payload['client'].get('natip')
            domu_admin_vlan = (node_payload.get('admin') or {}).get('vlantag')
            if domu_admin_vlan is None:
                domu_admin_vlan = node_payload['client'].get('natvlantag', 0)

        # extract admin networks configuration
        elif 'admin_network' in node_payload:
            monitor_conf = build_monitor_admin_conf(node_payload)
            monitor_conf_type = MonitorConfType.ADMIN

    return NodeBondingConf(
        dom0, domu, domu_client, domu_admin_ip, domu_admin_vlan,
        bond_iface_confs, bond_cavium_info, monitor_conf, monitor_conf_type)


def extract_bonding_conf_from_common_payload(
        payload: Payload,
        extract_monitor_conf: bool,
        scan_ips: Sequence[IPv4Address],
        bonding_operation: PayloadBondOp,
        dom0s_domus: Mapping[str, str]={},
        scan_ipv6=()) -> Sequence[NodeBondingConf]:
    """Extract per-node bonding configuration from common payload.

    See module documentation for a description of the payload.

    scan_ips is ignored if extract_monitor_conf=False.  If the payload contains
    Scan IPs, those are preferred over the ones passed in scan_ips.

    :param payload: payload to extract configuration from.
    :param extract_monitor_conf: whether to also extract monitor configuration.
    :param scan_ips: cluster Scan IPs.
    :param bonding_operation: bonding operation the payload belong to
    :param dom0s_domus: Mapping of Dom0s FQDNs -> DomUs client FQDNs.
    :returns: sequence of node bonding configurations.
    :raises Exception: if payload is invalid/malformed.
    """
    if bonding_operation in [PayloadBondOp.DeleteService,
                             PayloadBondOp.RollbackMigration]:
        net_payload = payload.get('bonding_network')
    else:
        net_payload = payload.get('customer_network')

    if net_payload is None:
        ebLogWarn('BONDING: No bonding network config found in payload.')
        return ()

    nw_utils = NetworkUtils()
    backup_scan_ips: Sequence[IPv4Address] = ()
    backup_scan_ips_ipv6: Sequence[IPv6Address] = ()

    if extract_monitor_conf:
        # if payload has Scan IPs, prefer it over the ones received as param
        if 'scan' in net_payload:
            scan_ips, scan_ipv6 = nw_utils.mGetIPv4IPv6Scans(
                net_payload['scan'], aReturnIPv4IPv6Scans=True)
            scan_ips = tuple(map(IPv4Address, scan_ips))
            scan_ipv6 = tuple(map(IPv6Address, scan_ipv6))

        # 'backup_scans' is optional
        if 'backup_scans' in net_payload:
            backup_scan_ips, backup_scan_ips_ipv6 = nw_utils.mGetIPv4IPv6Scans(
                net_payload['backup_scans'], aReturnIPv4IPv6Scans=True)
            backup_scan_ips = tuple(map(IPv4Address, backup_scan_ips))
            backup_scan_ips_ipv6 = tuple(map(IPv6Address, backup_scan_ips_ipv6))

    return tuple(map(
        lambda node: build_node_bonding_conf(node, extract_monitor_conf,
                                             scan_ips, backup_scan_ips,
                                             bonding_operation, dom0s_domus,
                                             scan_ipv6,
                                             backup_scan_ips_ipv6),
        net_payload['nodes']))


def elastic_node_payload_to_common_payload(
        node_payload: Payload,
        bonding_operation: PayloadBondOp) -> Payload:
    """Convert elastic-reshape node payload to common node payload.

    See module documentation for a description of the payload.

    :param node_payload: elastic-reshape node payload.
    :param bonding_operation: Specifies bonding operation
    :returns: create-service node payload.
    :raises Exception: if payload is invalid or malformed.
    """
    new_payload = {'fqdn': node_payload['compute_node_hostname']}

    if bonding_operation == PayloadBondOp.DeleteCompute:
        return new_payload

    # extract 'monitoring', 'client', 'backup' and 'vip' dictionaries
    for elem in (node_payload['virtual_compute_info']
                             ['network_info']
                             ['virtualcomputenetworks']):
        # we make deep copies of the dictionaries to preserve the original ones
        if 'monitoring' in elem:
            new_payload['monitoring'] = copy.deepcopy(elem['monitoring'])
        elif 'client' in elem:
            client_dict = copy.deepcopy(elem['client'][0])

            # rename some keys
            if 'nathostname' in client_dict:
                client_dict['domu_oracle_name'] = client_dict.pop('nathostname')
            if 'ipaddr' in client_dict:
                client_dict['ip'] = client_dict.pop('ipaddr')
            if 'ipv6addr' in client_dict:
                client_dict['ipv6'] = client_dict.pop('ipv6addr')

            new_payload['client'] = client_dict
        elif 'backup' in elem:
            backup_dict = copy.deepcopy(elem['backup'][0])
            if 'ipaddr' in backup_dict:
                backup_dict['ip'] = backup_dict.pop('ipaddr')  # rename 'ipaddr'
            if 'ipv6addr' in backup_dict:
                backup_dict['ipv6'] = backup_dict.pop('ipv6addr')
            new_payload['backup'] = backup_dict
        elif 'admin' in elem:
            admin_dict = copy.deepcopy(elem['admin'][0])
            if 'ipaddr' in admin_dict:
                admin_dict['ip'] = admin_dict.pop('ipaddr')  # rename 'ipaddr'
            new_payload['admin'] = admin_dict
        elif 'vip' in elem:
            vip_dict = copy.deepcopy(elem['vip'][0])
            if 'ipaddr' in vip_dict:
                vip_dict['ip'] = vip_dict.pop('ipaddr')  # rename 'ipaddr'
            if 'ipv6addr' in vip_dict:
                vip_dict['ipv6'] = vip_dict.pop('ipv6addr')
            new_payload['vip'] = vip_dict

    return new_payload

def backup_restore_payload_to_common_payload(
        node_payload: Payload,
        bonding_operation: PayloadBondOp) -> Payload:
    """Convert vmbackup restore node payload to common node payload.

    See module documentation for a description of the payload.

    :param node_payload: vmbackup restore node payload.
    :param bonding_operation: Specifies bonding operation
    :returns: create-service node payload.
    :raises Exception: if payload is invalid or malformed.
    """
    new_payload = {'fqdn': node_payload['fqdn']}

    # extract 'monitoring', 'client', 'backup' and 'vip' dictionaries
    if 'client' in node_payload:
        new_payload['client'] = node_payload.get("client")
    if 'backup' in node_payload:
        new_payload['backup'] = node_payload.get("backup")
    if 'vip' in node_payload:
        new_payload['vip'] = node_payload.get("vip")

    return new_payload

def extract_bonding_conf_from_xml(
        payload: Payload,
        extract_monitor_conf: bool,
        scan_ips: Sequence[IPv4Address],
        bonding_operation: PayloadBondOp,
        dom0s_domus: Mapping[str, str]={},
        scan_ipv6=()) -> Sequence[NodeBondingConf]:
    """Extract per-node bonding configuration from vmbackup restore payload.

    See module documentation for a description of the payload.

    scan_ips is ignored if extract_monitor_conf=False.

    :param payload: payload to extract configuration from.
    :param extract_monitor_conf: whether to also extract monitor configuration.
    :param scan_ips: cluster Scan IPs.
    :param bonding_operation: Specifies bonding operation
    :param dom0s_domus: Mapping of Dom0s FQDNs -> DomUs client FQDNs.
    :returns: sequence of node bonding configurations.
    :raises Exception: if payload is invalid/malformed.
    """
    nodes = []
    nodes.append(payload)

    # convert to common node payload
    nodes = map(lambda payload: backup_restore_payload_to_common_payload(
        payload, bonding_operation), nodes)

    backup_scan_ips: Sequence[IPv4Address] = ()

    return tuple(map(
        lambda node: build_node_bonding_conf(node, extract_monitor_conf,
                                             scan_ips, backup_scan_ips,
                                             bonding_operation, dom0s_domus,
                                             scan_ipv6=scan_ipv6),
        nodes))

def extract_bonding_conf_from_elastic_payload(
        payload: Payload,
        extract_monitor_conf: bool,
        scan_ips: Sequence[IPv4Address],
        bonding_operation: PayloadBondOp,
        dom0s_domus: Mapping[str, str]={},
        scan_ipv6=()) -> Sequence[NodeBondingConf]:
    """Extract per-node bonding configuration from elastic-reshape payload.

    See module documentation for a description of the payload.

    scan_ips is ignored if extract_monitor_conf=False.

    :param payload: payload to extract configuration from.
    :param extract_monitor_conf: whether to also extract monitor configuration.
    :param scan_ips: cluster Scan IPs.
    :param bonding_operation: Specifies bonding operation
    :param dom0s_domus: Mapping of Dom0s FQDNs -> DomUs client FQDNs.
    :returns: sequence of node bonding configurations.
    :raises Exception: if payload is invalid/malformed.
    """
    nodes = None

    if bonding_operation == PayloadBondOp.AddCompute:
        nodes = payload['reshaped_node_subset']['added_computes']
    elif bonding_operation == PayloadBondOp.DeleteCompute:
        nodes = payload['reshaped_node_subset']['removed_computes']

    # convert to common node payload
    nodes = map(lambda payload: elastic_node_payload_to_common_payload(
        payload, bonding_operation), nodes)

    backup_scan_ips: Sequence[IPv4Address] = ()

    return tuple(map(
        lambda node: build_node_bonding_conf(node, extract_monitor_conf,
                                             scan_ips, backup_scan_ips,
                                             bonding_operation, dom0s_domus,
                                             scan_ipv6=scan_ipv6),
        nodes))


def get_bonding_operation_from_payload(
        payload: Payload) -> Optional[PayloadBondOp]:
    """Get type of bonding operation from payload.

    Get type of bonding operation from top-level attribute "bonding_operation"
    from the payload.  If the attribute is not present in the payload, None is
    returned.

    :param payload: payload to get bonding operation from.
    :returns: type of bonding operation; None if not specified.
    :raises ExacloudRuntimeError: if the type of bonding operation is invalid.
    """
    if "bonding_operation" in payload:
        bond_op_str = payload.get("bonding_operation")
        try:
            return PayloadBondOp(bond_op_str)
        except ValueError:
            msg = ('Invalid value of "bonding_operation" in payload: '
                   f'"{bond_op_str}"')
            ebLogError(msg)
            raise ExacloudRuntimeError(0x803, 0xA, msg) from None

    return None


def extract_bonding_conf_from_payload(
        payload: Payload,
        bonding_operation: PayloadBondOp,
        extract_monitor_conf: bool,
        scan_ips: Sequence[IPv4Address],
        dom0s_domus: Mapping[str, str]={},
        scan_ipv6=()) -> Sequence[NodeBondingConf]:
    """Extract per-node bonding configuration from payload.

    See module documentation for a description of the payload.

    scan_ips is ignored if extract_monitor_conf=False.

    :param payload: payload to extract configuration from.
    :param extract_monitor_conf: whether to also extract monitor configuration.
    :param scan_ips: cluster Scan IPs.
    :param dom0s_domus: Mapping of Dom0s FQDNs -> DomUs client FQDNs.
    :returns: sequence of node bonding configurations.
    :raises ExacloudRuntimeError: if payload is invalid/malformed.
    """
    try:
        if bonding_operation in [PayloadBondOp.AddCompute,
                                 PayloadBondOp.DeleteCompute]:
            return extract_bonding_conf_from_elastic_payload(
                payload, extract_monitor_conf, scan_ips, bonding_operation,
                dom0s_domus, scan_ipv6)
        if bonding_operation in [PayloadBondOp.VMBackupRestore]:
            return extract_bonding_conf_from_xml(
                payload, extract_monitor_conf, scan_ips, bonding_operation,
                dom0s_domus, scan_ipv6)

        # Scan IPs are extracted from the common payload
        return extract_bonding_conf_from_common_payload(
            payload, extract_monitor_conf, scan_ips, bonding_operation,
            dom0s_domus, scan_ipv6)
    except Exception as exp:
        msg = ('Error while extracting bonding configuration from payload:'
               f' extract_monitor_conf={extract_monitor_conf}, '
               f'error="{exp}", payload={payload}')
        raise ExacloudRuntimeError(0x803, 0xA, msg) from exp


def extract_networks_from_monitor_conf(
        monitor_conf: MonitorConf) -> Mapping[str, NodeNetworkConf]:
    """Extracts the available network fields from the monitor config file.

    This includes the following fields:
    - interface_type
    - mac
    - standby_vnic_mac
    - vlantag

    It is implied that all the networks are consistent among all the IPs
    configured in the monitor config passed.

    :param monitor_conf: a monitor config file text.
    :returns: a payload like the one shown in the example.
    """
    monitor_json: Mapping[str, Sequence[Payload]] = json.loads(monitor_conf)

    networks: Mapping[str, NodeNetworkConf] = {}
    for configs in monitor_json.values():
        for conf in configs:
            networks[conf['interface_type']] = NodeNetworkConf(
                conf['interface_type'], conf['mac'], conf['standby_vnic_mac'],
                conf.get('vlantag'))

    return networks


def build_bonded_bridge_ipconf_xml(
        dom0: str,
        bond_interface: str,
        bridge_interface: str,
        bond_iface_conf: BondIfaceConf) -> str:
    """Build static bonded-bridge XML configuration for ipconf.

    Build the XML data to be consumed by ipconf in Dom0 to create a static
    bonded-bridge with bonding configuration as specified by bond_iface_conf.

    :param dom0: Dom0's hostname where the bridge will be created.
    :param bond_iface_conf: net interface bonding configuration.
    :returns: the XML as a string.
    """
    bonding_opts = (
        "mode=active-backup fail_over_mac=1 num_grat_arp=8 "
        "arp_interval=1000 primary_reselect=failure arp_allslaves=1 "
        f"arp_ip_target={str(bond_iface_conf.gateway)} "
        f"primary={bond_iface_conf.primary_interface}"
    )
    monitoring_hostname = f"bondmonitoring-{dom0}"
    return f"""\
<?xml version='1.0' standalone='yes'?>
<Set_interfaces>
 <Interfaces>
  <Arpcheck>no</Arpcheck>
  <Bond_options>"{bonding_opts}"</Bond_options>
  <Bond_type>bonded</Bond_type>
  <Bondeth_mode>active-backup</Bondeth_mode>
  <Bridge>{bridge_interface}</Bridge>
  <Hostname>{monitoring_hostname}</Hostname>
  <IP_address>{bond_iface_conf.ip_addr}</IP_address>
  <IP_enabled>yes</IP_enabled>
  <IP_ssh_listen>disabled</IP_ssh_listen>
  <Inet_protocol>IPv4</Inet_protocol>
  <Mtu_size>9000</Mtu_size>
  <Name>{bond_interface}</Name>
  <Net_type>Other</Net_type>
  <Netmask>{bond_iface_conf.netmask}</Netmask>
  <Slaves>{bond_iface_conf.primary_interface}</Slaves>
  <Slaves>{bond_iface_conf.secondary_interface}</Slaves>
  <State>1</State>
  <Status>UP</Status>
  <Vlan_id>0</Vlan_id>
 </Interfaces>
 <Interfaces>
  <Bond_type>single</Bond_type>
  <Master>{bond_interface}</Master>
  <Name>{bond_iface_conf.primary_interface}</Name>
  <State>1</State>
  <Status>UP</Status>
 </Interfaces>
 <Interfaces>
  <Bond_type>single</Bond_type>
  <Master>{bond_interface}</Master>
  <Name>{bond_iface_conf.secondary_interface}</Name>
  <State>1</State>
  <Status>UP</Status>
 </Interfaces>
</Set_interfaces>
"""
