"""
 Copyright (c) 2020, 2025, Oracle and/or its affiliates.

NAME:
    cluejumboframes.py - Exacloud JumboFrames configuration logic

DESCRIPTION:
    Setup JumboFrames for XEN and KVM

    JumboFrames configuration on Dom0 and DomU under the following assumptions:

    - On Dom0:
      * client and backup network interfaces can be configured either alone
        or in conjunction.

      * Interface names expected for the process to work:
        - X6:
          * Client bridge: vmbondeth0[.<client_vlan>]
          * Backup bridge: vmbondeth1[.<backup_vlan>]

        - X7 and higher:
          * Client bridge: vmbondeth0[.<client_vlan>]
          * Backup bridge: vmbondeth0[.<backup_vlan>]

      * Any interface whose master is client/backup bridge will be configured
        as well as any dependent interface.  This includes changing the MTU
        both at runtime configuration (e.g. with command
        'ip link set dev <IFACE> mtu <MTU>') and in
        /etc/sysconfig/network-scripts/ifcfg-* files for persistence.

    - On DomU:
      * Interfaces names expected for the process to work:
        - client network: bondeth0
        - Backup network: bondeth1

      * MTU of those interfaces is changed at runtime configuration and in
        /etc/sysconfig/network-scripts/ifcfg-* files for persistence.

NOTES:
    - If you change this file, please make sure lines are no longer than 80
      characters (including newline) and it passes pylint, mypy and flake8 with
      all the default checks enabled.  (An exception is naming convention, for
      which a Pylint directive to disable the check has been put in place
      below.)

History:

    MODIFIED   (MM/DD/YY)
    scoral      06/07/24 - Bug 36315105: Enable jumbo frames setup with
                           independent VLAN IDs for each node in the cluster.
    scoral      09/12/23 - Bug 35796067: Force jumbo frames to be disabled if
                           no configuration specified in payload.
    scoral      05/17/22 - Bug 34171132: Use OEDA Jumbo Frames API on 21.2.10
                           Recut 2 Exadata Image clusters.
    jlombera    04/14/21 - Bug 32770969: fall back to root namespace if backup
                           namespace is missing
    jlombera    03/22/21 - Bug 32620666: support X6/bonding clusters
    scoral      11/11/20 - Implemented configuration read form ECRA payload.
                           Added a function to copy Jumbo Frames setup from
                           other cluster.
    jimillan    05/13/20 - Creation
"""

# pylint: disable=invalid-name

import itertools
import re
from enum import Enum
from typing import (
    Any, Mapping, NamedTuple, Optional, Sequence, Tuple, TYPE_CHECKING)

from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogDebug, ebLogError, ebLogInfo, ebLogWarn
from exabox.utils.node import (
    connect_to_host, node_cmd_abs_path_check, node_exec_cmd_check,
    node_update_key_val_file)
from exabox.utils.common import version_compare

# We need to import exaBoxCluCtrl for type annotations, but it will cause a
# cyclic-import at runtime.  Thus we import it only when type-checking.  We
# still need to define type exaBoxCluCtrl or pylint will complain, though, so
# we just make it an alias to 'object' when not type-checking.
if TYPE_CHECKING:
    from exabox.ovm.clucontrol import exaBoxCluCtrl
else:
    exaBoxCluCtrl = object  # pylint: disable=invalid-name

# Public API
__all__ = [
    'configureJumboFrames',
    'jumboFramesState',
    'useExacloudJumboFramesAPI'
]


Payload = Mapping[str, Any]


# This is the first ExaData image version where we should stop using the
# ExaCloud Jumbo Frames API and start using the OEDA Jumbo Frames API instead.
EDIMG_OEDA_JF_API = '21.2.10.0.0.220406.1'


class ebMTUSize(Enum):
    """MTU sizes."""
    NORMAL = 1500
    JUMBO = 9000


class ebJFConf(NamedTuple):
    """Jumbo Frames configuration."""
    dom0_client_mtu: ebMTUSize
    dom0_backup_mtu: ebMTUSize
    domu_client_mtu: ebMTUSize
    domu_backup_mtu: ebMTUSize
    dom0_client_bridge: str
    dom0_backup_bridge: str
    domu_client_iface: str
    domu_backup_iface: str
    atp_namespace: Optional[str]


def cluctrlGetDom0Bridges(
    aCluctrl: exaBoxCluCtrl,
    aDomU: str) -> Tuple[str, str]:
    """Get the Dom0's client/backup bridge names for a given cluster config.

    :param aCluctrl: exaBoxCluCtrl object representing cluster configuration.
    :param aDom0: DomU client FQDN.
    :returns: tuple with (client_bridge, backup_bridge)
    """
    _client_bridge = 'vmbondeth0'

    if aCluctrl.mGetExadataDom0Model() == 'X6':
        _backup_bridge = 'vmbondeth1'
    else:
        _backup_bridge = _client_bridge

    # get client/backup VLANIDs
    _client_vlan = None
    _backup_vlan = None
    _machine_config = aCluctrl.mGetMachines().mGetMachineConfig(aDomU)
    _net_ids = _machine_config.mGetMacNetworks()

    for _net_id in _net_ids:
        _net_conf = aCluctrl.mGetNetworks().mGetNetworkConfig(_net_id)
        _net_type = _net_conf.mGetNetType()

        if _net_type == 'client':
            _client_vlan = _net_conf.mGetNetVlanId()
        elif _net_type == 'backup':
            _backup_vlan = _net_conf.mGetNetVlanId()

    # compute client/backup bridge names based on VLANIDs
    if _client_vlan is not None and _client_vlan != 'UNDEFINED':
        _client_bridge = f'{_client_bridge}.{int(_client_vlan)}'

    if _backup_vlan is not None and _backup_vlan != 'UNDEFINED':
        _backup_bridge = f'{_backup_bridge}.{int(_backup_vlan)}'

    if _backup_vlan is None:
        _backup_bridge = None 

    # return unique bridge names
    return (_client_bridge, _backup_bridge)


def cluctrlGetClientBackupIfaces(
        aCluctrl: exaBoxCluCtrl,
        aDomU: str) -> Tuple[str, str, str, str]:
    """Get client/backup interface names in Dom0/DomU for a given cluster.

    :param aCluctrl: exaBoxCluCtrl object representing cluster configuration.
    :param aDomU: DomU client FQDN.
    :returns: tuple (dom0_client_bridge, dom0_backup_bridge,
                     domu_client_iface, domu_backup_iface)
    """
    _dom0_client_bridge, _dom0_backup_bridge = cluctrlGetDom0Bridges(aCluctrl,
                                                                     aDomU)
    _domu_client_iface = 'bondeth0'
    _domu_backup_iface = 'bondeth1'

    return (_dom0_client_bridge, _dom0_backup_bridge,
            _domu_client_iface, _domu_backup_iface)


def getJumboFramesConf(
        aCluctrl: exaBoxCluCtrl,
        aPayload: Payload,
        aDomU: str) -> Optional[ebJFConf]:
    """Get ebJFConf.

    Returns None if JumboFrames configuration is not specified in the payload.
    """
    _conf = aPayload.get('jumbo_frames')

    if _conf is None:
        if aCluctrl.mIsKVM():
            return None
        # Bug 35796067: For XEN environments, we will force Jumbo Frames to be
        # disabled when no configuration is specified in Payload.
        _conf = 'disabled'

    _client_mtu = ebMTUSize.NORMAL
    _backup_mtu = ebMTUSize.NORMAL

    if _conf == "client":
        _client_mtu = ebMTUSize.JUMBO
    elif _conf == "backup":
        _backup_mtu = ebMTUSize.JUMBO
    elif _conf == "both":
        _client_mtu = ebMTUSize.JUMBO
        _backup_mtu = ebMTUSize.JUMBO
    elif _conf != "disabled":
        ebLogWarn('Unexpected value of parameter "jumbo_frames" in '
                  f'payload: "{_conf}".  Skipping.')
        return None

    # In X7 and higher, same base bond (bondeth0) is used in Dom0 for bridges
    # of both client/backup networks, so to be safe in the configuration, we
    # enable JF in both bridges if at least one of client/backup networks need
    # JF configured.  In the DomU, JF is independently enabled/disabled in
    # client/backup interfaces.
    if _client_mtu == ebMTUSize.JUMBO or _backup_mtu == ebMTUSize.JUMBO:
        _dom0_mtu = ebMTUSize.JUMBO
    else:
        _dom0_mtu = ebMTUSize.NORMAL

    _ifaces = cluctrlGetClientBackupIfaces(aCluctrl, aDomU)

    return ebJFConf(
        dom0_client_mtu=_dom0_mtu,
        dom0_backup_mtu=_dom0_mtu,
        domu_client_mtu=_client_mtu,
        domu_backup_mtu=_backup_mtu,
        dom0_client_bridge=_ifaces[0],
        dom0_backup_bridge=_ifaces[1],
        domu_client_iface=_ifaces[2],
        domu_backup_iface=_ifaces[3],
        atp_namespace=aCluctrl.mGetNamespace()
    )


def nodeNamespaceExists(aNode: exaBoxNode, aNetNamespace: str) -> bool:
    """Whether a namespace exists on remote node.

    :param aNode: already connected exaBoxNode where to look for namespace.
    :pram aNetNamespace: namespace to look for.
    :returns: whether the namespace exists.
    :raises ExacloudRuntimeError: if an error occurred
    """
    return aNode.mFileExists(f'/run/netns/{aNetNamespace}')


def nodeSetIfaceMtu(
        aNode: exaBoxNode,
        aIface: str,
        aMtu: ebMTUSize,
        aNetNamespace: Optional[str] = None) -> None:
    """Update MTU of give interface on remote node.

    Updates the MTU in the runtime configuration and persistently in file
    /etc/sysconfig/network-scripts/ifcfg-{aIface} if that file exists.  If a
    'aNetNamespace' is specified, the runtime configuration if changed in that
    namespace.

    :param aNode: already connected exaBoxNode where to perform the config.
    :param aIface: network interface to configure
    :param aMtu: new MTU to set
    :param aNetNamespace: namespace to operate on.
    :returns: Nothing
    :raised ExacloudRuntimeError: if an error occurred
    """
    try:
        _ip_cmd = node_cmd_abs_path_check(aNode, 'ip', sbin=True)
        _cmd = f'{_ip_cmd} link set dev {aIface} mtu {aMtu.value}'

        if aNetNamespace:
            _cmd = f'{_ip_cmd} netns exec {aNetNamespace} {_cmd}'

        # configure runtime MTU
        node_exec_cmd_check(aNode, _cmd)

        # configure MTU in ifcfg file
        _ifcfg_file = f'/etc/sysconfig/network-scripts/ifcfg-{aIface}'

        if aNode.mFileExists(_ifcfg_file):
            node_update_key_val_file(
                aNode, _ifcfg_file, {'MTU': str(aMtu.value)})
    except Exception as _exp:
        _msg = ('Failed net iface MTU configuration: '
                f'host={aNode.mGetHostname()}; iface={aIface}; '
                f'mtu={aMtu.value}; net_amespace={aNetNamespace}; '
                f'error="{_exp}"')
        ebLogError(_msg)
        raise ExacloudRuntimeError(0x0786, 0xA, _msg) from _exp


def nodeGetIfaceMtu(
        aNode: exaBoxNode,
        aIface: str,
        aNetNamespace: Optional[str] = None) -> int:
    """Get MTU of an interface in a remote node.

    :param aNode: already connected exaBoxNode to operate on.
    :param aIface: network interface.
    :param netNamespace: if specified, look into that net namespace.
    :returns: the MTU
    :raises ExacloudRuntimeError: if an error occurred.
    """
    try:
        _cat = node_cmd_abs_path_check(aNode, 'cat')
        _cmd = f'{_cat} /sys/class/net/{aIface}/mtu'

        if aNetNamespace:
            _ip_cmd = node_cmd_abs_path_check(aNode, 'ip', sbin=True)
            _cmd = f'{_ip_cmd} netns exec {aNetNamespace} {_cmd}'

        _ret = node_exec_cmd_check(aNode, _cmd)

        return int(_ret.stdout)
    except Exception as _exp:
        _msg = (f'Failed to get MTU of interface: host={aNode.mGetHostname()};'
                f' iface={aIface}; net_namespace={aNetNamespace}')
        ebLogError(f'{_msg}; error="{_exp}"')
        raise ExacloudRuntimeError(0x0785, 0xA, _msg) from _exp


def nodeGetBridgePorts(aNode: exaBoxNode, aBridge: str) -> Sequence[str]:
    """Get ports of a net bridge in a remote node.

    Any base link will be returned first in the sequence.

    :param aNode: already connected exaBoxNode to operate on.
    :param aBridge: name of the bridge interface.
    :returns: sequence with names of the bridge's ports.
    :raises ExacloudRuntimeError: if an error occurred.
    """
    try:
        # list net links in node
        _ip_cmd = node_cmd_abs_path_check(aNode, 'ip', sbin=True)
        _cmd = f'{_ip_cmd} -oneline link show'
        _ret = node_exec_cmd_check(aNode, _cmd)

        # Extract ports of the bridge (links that have the bridge as master).
        # The expected format of lines matching ports is:
        #
        #   <link_id>: <link_name>: .* master {aBridge} .*
        #
        # We want to extract only <link_name>.
        _port_regex = re.compile(
            fr'[0-9]+:\s+([^:]+):.+ master {re.escape(aBridge)} ')
        _match_entries = map(_port_regex.match, _ret.stdout.splitlines())
        _port_matches = (
            _match.group(1) for _match in _match_entries if _match)

        # Handle related links in the form '<link>@<base_link>' (e.g.
        # 'bondeth0.1@bondeth0').  We split the links and ensure <base_link> is
        # picked first (we reverse the list).
        _ports = itertools.chain(
            *(reversed(_port.split('@')) for _port in _port_matches))

        # pylint: disable=fixme
        # TODO: use a more reliable implementation, like walking through
        #       properties in '/sys/class/net/{aBridge}/*' instead of
        #       parsing/interpreting output of 'ip link show'.

        return tuple(_ports)
    except Exception as _exp:
        _msg = (f'Error getting ports of bridge {aBridge} in node '
                f'{aNode.mGetHostname()}')
        ebLogError(f'{_msg}; error={_exp}')
        raise ExacloudRuntimeError(0x0114, 0xA, _msg) from _exp


def nodeConfigBridgeMtu(
        aNode: exaBoxNode,
        aBridge: str,
        aMtu: ebMTUSize) -> None:
    """Configure MTU of a bridge and all its ports in a remote host.

    :param aNode: already connected exaBoxNode to operate on.
    :param aBridge: bridge to configure.
    :param aMtu: new MTU size.
    :returns: Nothing
    :raises ExacloudRuntimeError: if an error occurred.
    """
    try:
        for _iface in nodeGetBridgePorts(aNode, aBridge):
            nodeSetIfaceMtu(aNode, _iface, aMtu)

        # configure bridge's MTU last
        nodeSetIfaceMtu(aNode, aBridge, aMtu)
    except Exception as _exp:
        _msg = ('Failed configure MTU in bridge an its ports. '
                f'host={aNode.mGetHostname()}; bridge={aBridge}; '
                f'mtu={aMtu.value}')
        ebLogError(f'{_msg}; error="{_exp}"')
        raise ExacloudRuntimeError(0x0786, 0xA, _msg) from _exp


#
# Public functions
#


def configureJumboFrames(aCluctrl: exaBoxCluCtrl, aPayload: Payload) -> None:
    """Configure JumboFrames in the given cluster if supported/enabled.

    This is a no-op if JumboFrames (JF) are not supported in the cluster
    (currently only ExaBM is supported) or no JF where configured in the
    payload.

    We configure JF if attribute "jumbo_frames" is present in the payload and
    has any of the following values (along with the meaning):

      "client": enable JF in client network and ensure it's disabled in backup
                network.

      "backup": enable JF in backup network and ensure it's disabled in client
                network.

      "both": enable JF in both client and backup networks.

      "disabled": ensure JF is disabled in both client and backup networks.

    If "jumbo_frames" is missing in the payload or has a different value than
    one of the above, JF configuration is skipped.

    :param aCluctrl: exaBoxCluCtrl object with description of the cluster.
    :param aPayload: ECRA payload (we only look for attribute "jumbo_frames").
    :returns: Nothing
    :raises ExacloudRuntimeError: if an error occurred.
    """
    # pylint: disable=too-many-locals
    if not aCluctrl.mIsExabm():
        ebLogInfo('JumboFrames only supported on ExaBM; skipping config')
        return

    _confs = { _dom0: (_domu, getJumboFramesConf(aCluctrl, aPayload, _domu))
               for _dom0, _domu in aCluctrl.mReturnDom0DomUPair() }

    if not useExacloudJumboFramesAPI(aCluctrl):
        ebLogInfo('JumboFrames not supported; skipping config')
        return

    _ctx = aCluctrl.mGetCtx()

    for _dom0, (_domu, _conf) in _confs.items():
        if _conf is None:
            ebLogInfo(f'JumboFrames not configured for DomU {_domu}; '
                      'skipping config')
            continue

        ebLogDebug(f'CONFIGURING JumboFrames: dom0={_dom0}; domu={_domu}; '
                   f'client_mtu={_conf.domu_client_mtu.value}; '
                   f'backup_mtu={_conf.domu_backup_mtu.value}')

        try:
            # NOTE: Explicitly connect as 'root' to ensure we have read/write
            #       permissions to system config files.

            # configure Dom0
            with connect_to_host(_dom0, _ctx, username='root') as _node:
                nodeConfigBridgeMtu(
                    _node, _conf.dom0_client_bridge, _conf.dom0_client_mtu)
                nodeConfigBridgeMtu(
                    _node, _conf.dom0_backup_bridge, _conf.dom0_backup_mtu)

            # configure DomU
            with connect_to_host(_domu, _ctx, username='root') as _node:
                nodeSetIfaceMtu(
                    _node, _conf.domu_client_iface, _conf.domu_client_mtu)

                # access backup interface in ATP namespace (if it exists)
                _backup_ns = _conf.atp_namespace

                if _backup_ns and not nodeNamespaceExists(_node, _backup_ns):
                    ebLogWarn(f'JumboFrames: ATP namespace "{_backup_ns}" '
                              f"doesn't exist in DomU {_domu}; falling back to"
                              " root namespace")
                    _backup_ns = None

                nodeSetIfaceMtu(
                    _node, _conf.domu_backup_iface, _conf.domu_backup_mtu,
                    _backup_ns)
        except Exception as _exp:
            _msg = (f'Failed to configure JumboFrames. '
                    f'dom0={_dom0}; domu={_domu}; '
                    f'client_mtu={_conf.domu_client_mtu.value}; '
                    f'backup_mtu={_conf.domu_backup_mtu.value}; '
                    f'atp_namespace={_conf.atp_namespace}')
            ebLogError(f'{_msg}; error="{_exp}"')
            raise ExacloudRuntimeError(0x0786, 0xA, _msg) from _exp

        ebLogDebug(f'CONFIGURED JumboFrames: dom0={_dom0}; domu={_domu}')

    ebLogInfo('SUCCEEDED JumboFrames configuration')


def jumboFramesState(aCluctrl: exaBoxCluCtrl) -> Sequence[Mapping[str, Any]]:
    """Get state of JumboFrames in the given cluster.

    Returns a mapping with the JumboFrams runtime state in the given cluster.

    :param aCluctrl: exaBoxCluCtrl object with description of the cluster.
    :returns: Mapping with JumboFrames state.
    :raises ExacloudRuntimeError: if an error ocurred.
    """
    ebLogInfo('Computing state of JumboFrames')

    _atp_namespace = aCluctrl.mGetNamespace()

    def __dom0_domu_mtus(aDom0: str, aDomU: str,) -> Mapping[str, Any]:
        try:
            ebLogDebug(f'Retrieving runtime MTU config ({aDom0}, {aDomU})')

            (_dom0_client_bridge, _dom0_backup_bridge,
             _domu_client_iface, _domu_backup_iface) \
                = cluctrlGetClientBackupIfaces(aCluctrl, aDomU)

            # get Dom0 MTUs
            with connect_to_host(aDom0, aCluctrl.mGetCtx()) as _node:
                _ports = nodeGetBridgePorts(_node, _dom0_client_bridge)
                _dom0_client_mtus = {
                    _iface: nodeGetIfaceMtu(_node, _iface)
                    for _iface in _ports}
                _dom0_client_mtus[_dom0_client_bridge] = nodeGetIfaceMtu(
                    _node, _dom0_client_bridge)

                _ports = nodeGetBridgePorts(_node, _dom0_backup_bridge)
                _dom0_backup_mtus = {
                    _iface: nodeGetIfaceMtu(_node, _iface)
                    for _iface in _ports}
                _dom0_backup_mtus[_dom0_backup_bridge] = nodeGetIfaceMtu(
                    _node, _dom0_backup_bridge)

            # get DomU MTUs
            with connect_to_host(aDomU, aCluctrl.mGetCtx()) as _node:
                _domu_client_mtu = nodeGetIfaceMtu(_node, _domu_client_iface)

                # access backup interface in ATP namespace (if it exists)
                _backup_ns = _atp_namespace

                if _backup_ns and not nodeNamespaceExists(_node, _backup_ns):
                    ebLogWarn(f'JumboFrames: ATP namespace "{_backup_ns}" '
                              f"doesn't exist in DomU {aDomU}; falling back to"
                              " root namespace")
                    _backup_ns = None

                _domu_backup_mtu = nodeGetIfaceMtu(
                    _node, _domu_backup_iface, _backup_ns)

            return {
                'dom0': {
                    'hostname': aDom0,
                    'client': {
                        'bridge': _dom0_client_bridge,
                        'mtus': _dom0_client_mtus
                    },
                    'backup': {
                        'bridge': _dom0_backup_bridge,
                        'mtus': _dom0_backup_mtus
                    }
                },
                'domu': {
                    'hostname': aDomU,
                    'client': {'mtus': {_domu_client_iface: _domu_client_mtu}},
                    'backup': {'mtus': {_domu_backup_iface: _domu_backup_mtu}}
                }
            }
        except Exception as _exp:
            _msg = f'Failed to get MTUs: dom0={aDom0}; domu={aDomU}'
            ebLogError(f'{_msg}; error="{_exp}"')
            raise ExacloudRuntimeError(0x0785, 0xA, _msg) from _exp

    try:
        return tuple(__dom0_domu_mtus(_dom0, _domu) for _dom0, _domu in
                     aCluctrl.mReturnDom0DomUPair())
    except Exception as _exp:
        _msg = ('Failed to get state of JumboFrames in cluster: '
                f'atp_namespace={_atp_namespace}')
        ebLogError(_msg)
        raise ExacloudRuntimeError(0x0785, 0xA, _msg) from _exp


def useExacloudJumboFramesAPI(aCluctrl: exaBoxCluCtrl) -> bool:
    """Determines if we should use the Exacloud Jumbo Frames API.

    This won't be possible if for any KVM Dom0 in the cluster, the ExaData
    image version is equal or greater than 21.2.10.0.0.220406.1
    In that case, the OEDA API will be used instead.

    :param aCluctrl: exaBoxCluCtrl object with description of the cluster.
    :returns: A boolean indicating if we should use the Exacloud Jumbo Frames.
    :raises ExacloudRuntimeError: if an error ocurred.
    """
    if not aCluctrl.mIsKVM():
        return True

    for _dom0, _ in aCluctrl.mReturnDom0DomUPair():
        _exadata_img_ver = aCluctrl.mGetImageVersion(_dom0)
        if version_compare(_exadata_img_ver, EDIMG_OEDA_JF_API) >= 0:
            return False
    
    return True
