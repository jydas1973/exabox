#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/clunetworkdetect.py /main/13 2025/05/19 14:20:00 akkar Exp $
#
# cluinetworkdetect.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      cluinetworkdetect.py - Functions to detect network and set OEDA properties
#
#    DESCRIPTION
#      Class made to for future refactoring of network code
#      Straightforward impl for X9 only for now
#
#    NOTES
#      THIS FILE IS CODE COVERED BY tests_x9discovery.py
#
#    MODIFIED   (MM/DD/YY)
#    akkar       04/06/25 - 37641178: 100gbs client network support
#    naps        08/09/24 - Bug 36908342 - X11M support.
#    aararora    06/26/24 - Bug 36285522: Add error fields for healthcheck in
#                           case of network detection failure.
#    pbellary    09/01/24 - Enh 35586531 - EXACC X10M : SUPPORT FOR 100GBE CARD 
#                           FOR BACKUP NETWORK IN PCI SLOT 2
#    aararora    08/01/23 - Check if the length of set union for
#                           interfaces is 1. If it is 1, raise an exception.
#    rkhemcha    05/15/23 - 35392118 - Fix eth bump logic
#    rajsag      01/09/23 - x10m support
#    aypaul      09/05/22 - Enh#34411005 API implementation for active network
#                           information.
#    ffrrodri    03/01/21 - Enh 32490987: Add support for half_net extra
#                           parameter to allow backup net on client net
#    alsepulv    02/23/21 - Bug 32513420: Fix pylint error '__repr__ does not
#                           return str'
#    ffrrodri    02/22/21 - Bug 32527936: Changed ebLogError to
#                           ebLogCritical with more detailed information
#    ffrrodri    01/06/21 - Enh 32350429: Complete path added in commands.
#                           Data of networks supported x9 separated from
#                           code in supportedNetworks.json file
#    vgerard     12/18/20 - Creation
#
import itertools
import os.path
from pathlib import Path
import json
from enum import Enum, IntEnum
from typing import Optional, Tuple, Iterable, NamedTuple, Set

from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogInfo, ebLogTrace, ebLogWarn, ebLogDebug, ebLogError, ebLogCritical
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.utils.node import (connect_to_host, node_exec_cmd, node_cmd_abs_path_check)
from exabox.core.Context import get_gcontext

def parseOutputAndGetInterfaceName(_output: str, _information_type: str) -> str:

    _return_str = "ERROR"
    if _information_type == "active_slave":
        _output_lines = _output.splitlines()
        for _line in _output_lines:
            if "Currently Active Slave" in _line:
                _return_str = _line.split(":")[1].strip()
                break

    return _return_str


def getActiveNetworkInformation(_payload: dict()) -> dict:
    #The function will expect the payload to be in proper format since its expected to be called in conjunction with network_info endpoint.
    #If at all this utility function is used apart from network_info endpoint, make sure validate the payload correctly.
    _interface_value = _payload['interface']
    _information_list = _payload['information']
    _requested_nodes = _payload['nodes']
    _json_response = {"nodes" : []}
    _nodes_list = _json_response['nodes']

    for _node in _requested_nodes:
        with connect_to_host(_node, get_gcontext()) as _connected_node:
            for _network_information in _information_list:
                if _network_information == "active_slave":
                    _cat_cmd = node_cmd_abs_path_check(_connected_node, "cat")
                    _cmd = f"{_cat_cmd} /proc/net/bonding/{_interface_value}"
                    _return_tuple = node_exec_cmd(_connected_node, _cmd)
                    if _return_tuple.exit_code != 0:
                        ebLogError(f"Failed to get {_network_information} information for {_interface_value} interface on {_node}.")
                        ebLogError(f"Detail error: {_return_tuple.stderr}")
                        _output = {"node" : _node, "active_slave": "ERROR"}
                    else:
                        _information_value = parseOutputAndGetInterfaceName(_return_tuple.stdout, "active_slave")
                        _output = {"node" : _node, "active_slave": _information_value}
                    _nodes_list.append(_output)

    return _json_response

class ebNetworkType(Enum):
    """ 
       Network types for autodetection
    """
    FIBER = "FIBER"
    COPPER = "Twisted Pair"
    UNKNOWN = "Unknown"

    def __repr__(self) -> str:
        return str(self.name)


class ebOEDANetwork(NamedTuple):
    """
    Represents an OEDA network spec, for instance
       CLIENT_NETWORK=vmbondeth0:eth1,eth2:bondeth0
       Would be dom0_bridge:  'vmbondeth0'   
                dom0_interfaces :   ['eth1','eth2']
                domU_name  :  'bondeth0'     
    """
    dom0_bridge: str
    dom0_interfaces: Iterable[str]
    domU_name: str

    def __str__(self) -> str:
        """ Returns the string as expected by OEDA property """
        return f'{self.dom0_bridge}:{",".join(self.dom0_interfaces)}:{self.domU_name}'


class ebOEDANetworkConfiguration(NamedTuple):
    """
    This NamedTuple will represent the discovered network configuration
    And will be the returned object for the Network Detection
    """
    client_net: Tuple[ebNetworkType, ebOEDANetwork]
    backup_net: Tuple[ebNetworkType, ebOEDANetwork]
    # Degraded Net is used for HALF, to keep looking for better match
    degraded_net: bool = False
    half_net: bool = False
    # Default value for admin_net is NAT type
    admin_net: ebOEDANetwork = ebOEDANetwork('vmeth0', [], 'eth0')

    # Avoid array access to tuples :) 
    def mGetClientNetType(self) -> ebNetworkType:
        return self.client_net[0]

    def mGetClientNet(self) -> ebOEDANetwork:
        return self.client_net[1]

    def mGetBackupNetType(self) -> ebNetworkType:
        return self.backup_net[0]

    def mGetBackupNet(self) -> ebOEDANetwork:
        return self.backup_net[1]

    def mGetAdminNet(self) -> ebOEDANetwork:
        return self.admin_net

    def mGetAllUniqueDom0Interfaces(self) -> Set[str]:
        return set(itertools.chain(self.mGetClientNet().dom0_interfaces,
                                   self.mGetBackupNet().dom0_interfaces))


def generateSupportedNetworkMap(aModel, aEnvType='default', a100GbsInterfaces={}):
    """
       Obtains supported network information of a
       model from JSON data supportedNetwork.json
       :param str aModel: 'x9'
       :param str aEnvType: 'ociexacc'
       :param bool a100GbsSupported: True/False

       :return: dict supportedNetworksMap:
                {
                    'OCIEXACC_FULL_FIBER':
                        ebOEDANetworkConfiguration(
                            client_net=(FIBER,
                                        ebOEDANetwork(dom0_bridge='vmbondeth0',
                                                      dom0_interfaces=['eth1', 'eth2'],
                                                      domU_name='bondeth0')
                                        ),
                            backup_net=(FIBER,
                                        ebOEDANetwork(dom0_bridge='vmbondeth1',
                                                      dom0_interfaces=['eth9', 'eth10'],
                                                      domU_name='bondeth1')
                                        ),
                            degraded_net=False,
                            admin_net=ebOEDANetwork(dom0_bridge='vmeth0', dom0_interfaces=[], domU_name='eth0')),
                    'OCIEXACC_BASE_HALF_FIBER':
                        ebOEDANetworkConfiguration(
                            client_net=(FIBER,
                                        ebOEDANetwork(dom0_bridge='vmbondeth0',
                                                      dom0_interfaces=['eth5', 'eth6'],
                                                      domU_name='bondeth0')
                                        ),
                            backup_net=(FIBER,
                                        ebOEDANetwork(dom0_bridge='vmbondeth0',
                                                      dom0_interfaces=['eth5', 'eth6'],
                                                      domU_name='bondeth1')
                                        ),
                            degraded_net=True,
                            admin_net=ebOEDANetwork(dom0_bridge='vmeth0', dom0_interfaces=[], domU_name='eth0'))
                }
    """
    _100gbs_interfaces = a100GbsInterfaces
    _100gbs_backup_interfaces = _100gbs_interfaces.get('backup', [])
    _100gbs_client_interfaces = _100gbs_interfaces.get('client', [])
    SUPPORTED_NETWORK_PATH = 'properties/supportedNetworks.json'
    supportedNetworks = None
    abs_file_path = None
    supportedNetworksMap = {}

    try:
        abs_path = os.path.dirname(__file__)
        path = str(Path(abs_path).parents[1])
        abs_file_path = os.path.join(path, SUPPORTED_NETWORK_PATH)
        with open(abs_file_path) as json_data_file:
            supportedNetworks = json.load(json_data_file)
    except Exception as e:
        ebLogError(e)

    # Obtains information of a particular model if model exists
    if supportedNetworks:
        if aModel in supportedNetworks['models']:
            supportedNetworks = supportedNetworks['models'][aModel]
        else:
            ebLogInfo(f"Model {aModel} not found in suported networks data")
            return supportedNetworksMap
    else:
        ebLogError(f"File {abs_file_path} not found")
        return supportedNetworksMap

    # Add the values obtained from supportedNetworks.json to the map if env_type matches
    for sn in supportedNetworks.keys():
        if aEnvType in supportedNetworks[sn]['env_type']:
            _degraded_net = True if 'degraded_net' in supportedNetworks[sn] and supportedNetworks[sn]['degraded_net'] else False
            _half_net = True if 'half_net' in supportedNetworks[sn] and supportedNetworks[sn]['half_net'] else False
            
            # Get default interfaces
            client_config = supportedNetworks.get(sn, {}).get('client', {})
            backup_config = supportedNetworks.get(sn, {}).get('backup', {})
            default_client_interfaces = client_config.get('dom0_interfaces', [])
            default_backup_interfaces = backup_config.get('dom0_interfaces', [])

            # Determine Client Network parameters
            client_type = ebNetworkType(client_config.get('ebNetworkType'))
            client_dom0_interfaces = _100gbs_client_interfaces if _100gbs_client_interfaces else default_client_interfaces
            client_net = ebOEDANetwork('vmbondeth0', client_dom0_interfaces, 'bondeth0')

            # Determine Backup Network parameters 
            backup_type = ebNetworkType(client_config.get('ebNetworkType') if _half_net else backup_config.get('ebNetworkType'))
            backup_dom0_bridge = 'vmbondeth0' if _degraded_net or _half_net else 'vmbondeth1'
            if _half_net:
                backup_dom0_interfaces = default_client_interfaces
            else:
                backup_dom0_interfaces = _100gbs_backup_interfaces if _100gbs_backup_interfaces else default_backup_interfaces
            backup_net = ebOEDANetwork(backup_dom0_bridge, backup_dom0_interfaces, 'bondeth1')

            # Final configuration object using the calculated components
            ebLogTrace(f'ebOEDANetworkConfiguration object creation : {client_type},{client_dom0_interfaces}, {backup_type}, {backup_dom0_bridge}, {backup_dom0_interfaces} ')
            supportedNetworksMap[sn] = ebOEDANetworkConfiguration(  
                (client_type, client_net),
                (backup_type, backup_net),  
                _degraded_net,
                _half_net
            )  
    return supportedNetworksMap


class ebPortState(IntEnum):
    MISSING = -2
    DOWN = -1
    UP = 0
    UP_AFTER_BOUNCE = 1

    def isUp(self):
        return self >= 0


# TODO: This is specific to X9 for now, we need in the future to implement
# OTHER MODELS AND OCI/EXACS.  LIKELY RETROFIT OLDER MODELS AS WELL
class ebDiscoverOEDANetwork():
    """
       Class to implement network discovery for X9
    """

    NETWORK_FILENAME = '/opt/exacloud/network/DETECTED_NETWORK'

    def __init__(self, aNode: exaBoxNode,
                 aExadataModel: str,
                 aCluCtrlObj,
                 aDebug: bool = False):
        """
           Initialize the network detection Class
           :param exaBoxNode aNode:  A node CONNECTED to a dom0
           :param str aExadataModel: Exadata model ('X9')
           :param bool aDebug:       Debug Flag
        """
        self.__node = aNode
        self.__model = aExadataModel
        self.__ebox = aCluCtrlObj
        self.__debug = aDebug

        _dom0 = self.__node.mGetHostname()
        _exadata_model = self.__ebox.mGetNodeModel(_dom0)
        _physical_eth_attr = self.__ebox.mCheckConfigOption('exacc_high_speed_physical_network')
        
        if _physical_eth_attr is not None:
            _eth_attr = _physical_eth_attr.get(_exadata_model, {})
            _backup_interfaces = _eth_attr.get("backup_interfaces", ["eth5", "eth6"])
            _client_interfaces = _eth_attr.get("client_interfaces", ["eth1", "eth2"])
            ebLogInfo(f"Interface list: backup-{_backup_interfaces}, client-{_client_interfaces} from exabox.conf")
        else:
            _exadata_model = "X10"
            _backup_interfaces = ["eth5", "eth6"]
            _client_interfaces = ["eth1", "eth2"]
        
        _100gbs_interfaces = {}
        if self.__ebox.Is100GbsSpeedSupported(_dom0, 'backup'):
            _100gbs_interfaces['backup'] = _backup_interfaces
        if self.__ebox.Is100GbsSpeedSupported(_dom0, 'client'):
            _100gbs_interfaces['client'] = _client_interfaces
        

        # Creates dinamically the Enum with the map generated
        self.SupportedX9Network = Enum('SupportedX9Network', generateSupportedNetworkMap('x9', 'ociexacc', _100gbs_interfaces))
        self.SupportedX10Network = Enum('SupportedX10Network', generateSupportedNetworkMap('x10', 'ociexacc', _100gbs_interfaces))
        self.SupportedX11Network = Enum('SupportedX11Network', generateSupportedNetworkMap('x11', 'ociexacc', _100gbs_interfaces))

    # THIS method is copied and modernized from clucontrol
    # Ultimately we will remove it from clucontrol

    def mBumpInterface(self, aInterface: str) -> ebPortState:
        """
            Checks if interface is up, try to bounce it if not
            :param str aInterface: Interface name, like 'eth1'

            :return ebPortState: Port State
        """
        #
        # Check Link status if online/up then skip bump
        #
        _node = self.__node

        _cmdstr = f'/sbin/ethtool {aInterface} | /bin/grep "Link detected"'
        _, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if not _out or not len(_out):
            if self.__debug:
                ebLogDebug(f"PORT {aInterface} MISSING")
            return ebPortState.MISSING
        if (_out[0].find('yes') != -1):
            if self.__debug:
                ebLogDebug(f"PORT {aInterface} UP")
            return ebPortState.UP
        #
        # Force bump if offline/down
        #
        _cmdstr = '/sbin/ifdown {0} ; /bin/sleep 5 ; /sbin/ifup {0} ; /bin/sleep 15 ; /sbin/ifconfig  {0} up ; ' \
                  '/bin/sleep 5 ;'.format(aInterface)
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _cmdstr = '/sbin/ethtool {0} | /bin/grep "Link detected"'.format(aInterface)
        _i, _o, _e = _node.mExecuteCmd(_cmdstr)
        _out = _o.readlines()
        if _out and _out[0].find('yes') != -1:
            if self.__debug:
                ebLogDebug(f"PORT {aInterface} UP AFTER BOUNCE")
            return ebPortState.UP_AFTER_BOUNCE
        else:
            if self.__debug:
                ebLogDebug(f"PORT {aInterface} UP AFTER BOUNCE")
            return ebPortState.DOWN

    def mGetInterfaceType(self, aInterface: str) -> ebNetworkType:
        """
        Returns the type of the interface
        :param str aInterface: Interface name ('eth1')
        
        :return ebNetworkType: UNKNOWN,FIBER,COPPER
        """
        _node = self.__node
        _i, _o, _e = _node.mExecuteCmd(f'/sbin/ethtool {aInterface} | /bin/grep Port')
        _out = _o.readlines()
        if not _out or not len(_out):
            return ebNetworkType.UNKNOWN
        if 'FIBRE' in _out[0] or 'Direct Attach Copper' in _out[0]:
            return ebNetworkType.FIBER
        elif 'Twisted Pair' in _out[0]:
            return ebNetworkType.COPPER
        return ebNetworkType.UNKNOWN

    def mValidateNetwork(self, aNetwork: ebOEDANetworkConfiguration) -> bool:
        """ Validate that all interfaces in aNetwork are UP """
        # Iterate over all unique interfaces
        _down_interfaces = []
        for _if in aNetwork.value.mGetAllUniqueDom0Interfaces():
            if self.mBumpInterface(_if) in (ebPortState.DOWN, ebPortState.MISSING):
                _down_interfaces.append(_if)

        if _down_interfaces:
            ebLogWarn(f"Network has interfaces down: {_down_interfaces}")
            return False

        return True

    def mCacheNetworkOnDom0(self, aNetwork: ebOEDANetworkConfiguration) -> None:
        """ Write the network enum name to dom0 """
        _node = self.__node
        _node.mExecuteCmd(f"/bin/mkdir -p {os.path.dirname(self.NETWORK_FILENAME)}")
        _node.mExecuteCmd(f"/bin/sh -c '/bin/echo {aNetwork.name} > {self.NETWORK_FILENAME}'")

    def mQueryCachedNetwork(self, aModelNetworks) -> Optional[ebOEDANetworkConfiguration]:
        """
           Query if Network Detection  has been cached on dom0 and is Valid
           :param Enum[ebOEDANetworkConfiguration] aModelNetwork: 
                                                   Networks valid for model

           :return: None if no cached or cached invalid or 
                    ebOEDANetworkConfiguration
        """
        _node = self.__node
        _cached_network = None
        if _node.mFileExists(self.NETWORK_FILENAME):
            ebLogInfo("*** Found Cached Network Detection type, reusing it")
            _, _o, _err = _node.mExecuteCmd(f"/bin/cat {self.NETWORK_FILENAME}")
            _file_content = _o.readlines()[0].strip()
            # Try to find a network in the model network Enum matching it
            try:
                _cached_network = getattr(aModelNetworks, _file_content)
            except AttributeError:
                ebLogWarn(f"Cached network {_file_content} do not exist for model {self.__model}")
                _node.mExecuteCmd(f"/bin/rm -f {self.NETWORK_FILENAME}")

            if _cached_network:
                # Validate Cached Network
                if not self.mValidateNetwork(_cached_network):
                    ebLogWarn(f"Cached network {_file_content} have interfaces down, retrying detection")
                    _node.mExecuteCmd(f"/bin/rm -f {self.NETWORK_FILENAME}")
                    _cached_network = None
                else:
                    ebLogInfo(f"Network is valid. Using {_file_content}")

        return _cached_network

    def mGetInterfaceDetails(self, aIfStates, aResult):
        """
        Method to structure the returned dictionary to healtcheck for error scenarios
        aIfStates: Map for states of different interfaces
        aResult: Map for interfaces type to set of interfaces
        """
        _interface_types = {}
        _up = []
        _down = []
        _missing = []
        _up_after_bounce = []
        for _interface_state in aIfStates:
            # aIfStates structure is like below:
            # {'eth10: UP', 'eth11: UP', 'eth9: UP', 'eth2: MISSING'}
            _interface_state_list = _interface_state.split(':')
            _interface = _interface_state_list[0].strip()
            _state = _interface_state_list[1].strip()
            if _state == 'UP':
                _up.append(_interface)
            elif _state == 'DOWN':
                _down.append(_interface)
            elif _state == 'MISSING':
                _missing.append(_interface)
            elif _state == 'UP_AFTER_BOUNCE':
                _up_after_bounce.append(_interface)
        _operational_state = {'UP': _up, 'DOWN': _down, 'MISSING': _missing, 'UP_AFTER_BOUNCE': _up_after_bounce}
        for _interface_type, _interface_set in aResult.items():
            _interface_types[str(_interface_type.name)] = list(_interface_set)
        _interface_details = {"OPERATIONAL_STATE": _operational_state,
                              "INTERFACE_TYPES": _interface_types}
        return _interface_details

    # PUBLIC API OF THE CLASS #
    def mGetNetwork(self) -> Optional[ebOEDANetworkConfiguration]:
        """
        Discover network from Dom0 and persist it in a FILE 
        (In StepWise network autodetect is ran a lot)
        """
        # THIS NEW MODEL ONLY SUPPORTS X9, X10 and X11 (and OCIEXACC)
        if self.__model == 'X9':
            _modelNetworks = self.SupportedX9Network
        elif self.__model == 'X10':
            _modelNetworks = self.SupportedX10Network
        elif self.__model == 'X11':
            _modelNetworks = self.SupportedX11Network
        else:
            raise NotImplementedError
        
        # Lookup Cached result
        _cached_network = self.mQueryCachedNetwork(_modelNetworks)

        if _cached_network:
            return _cached_network

        # START OF DETECTION
        _node = self.__node

        # Extract the list of unique interfaces for MODEL
        _unique_ifs = set()
        for _network in _modelNetworks:
            _unique_ifs.update(_network.value.mGetAllUniqueDom0Interfaces())

        # Get interfaces status and UP interfaces
        _if_states, _up_ifs = set(), set()
        for _unique_if in _unique_ifs:
            _state = self.mBumpInterface(_unique_if)
            _if_states.add(f'{_unique_if}: {_state.name}')
            if _state.isUp():
                _up_ifs.add(_unique_if)

        # Find FIBER/COPPER interfaces, set, to compare easily afterwards
        _result = {ebNetworkType.COPPER: set(), ebNetworkType.FIBER: set(), ebNetworkType.UNKNOWN: set()}
        for _if in (_up_ifs):
            _result[self.mGetInterfaceType(_if)].add(_if)

        ebLogInfo(f"*** Detection of interfaces done, Interfaces state:\n{_result}")

        _matching_network = None
        _hardware_fault = False
        _faulty_interface = None
        _full_config_network = None
        for _netenum in _modelNetworks:
            _net = _netenum.value

            # Client and Backup Net are tuple, 
            # [0] is the TYPE (FIBER/COPPER), [1] the content
            # If the SET of UP interface of same type contains all expected
            # dom0s interfaces (empty difference), it should result of an EMPTY set
            if not ((set(_net.mGetClientNet().dom0_interfaces) - _result[_net.mGetClientNetType()]) |
                    (set(_net.mGetBackupNet().dom0_interfaces) - _result[_net.mGetBackupNetType()])):

                # If half_net parameter is true, there is required additional validation before assign it
                # to _matching_network
                if not _net.half_net:
                    # MATCHING NETWORK FOUND
                    _matching_network = _netenum

                # Prioritises degrated_net over half_net
                if _net.degraded_net:
                    # DO NOT BREAK on DEGRADED NET (HALF Cabled configs)
                    # in case a FULL config is matched
                    ebLogInfo(f"*** Network is a 'degraded' configuration (HALF Cabled)")
                elif _net.half_net:
                    # Set as half_net only if there is not a degrated_net detected before
                    if not _matching_network or not _matching_network.value.degraded_net:
                        # DO NOT BREAK on HALF NET (HALF Cabled configs)
                        # in case a FULL config is matched
                        _matching_network = _netenum
                        ebLogInfo(f"*** Network is a 'half' configuration (HALF Cabled)")
                else:
                    ebLogInfo(f"*** Found Matching Network:\n{_matching_network}")
                    break
            elif ((not (set(_net.mGetClientNet().dom0_interfaces) - _result[_net.mGetClientNetType()]) or
                  not (set(_net.mGetBackupNet().dom0_interfaces) - _result[_net.mGetBackupNetType()])) and
                 (len((set(_net.mGetClientNet().dom0_interfaces) - _result[_net.mGetClientNetType()]) |
                      (set(_net.mGetBackupNet().dom0_interfaces) - _result[_net.mGetBackupNetType()])) == 1)):
                # For a full config, either one of set of client interface difference OR backup interface difference
                # would be empty & union of set of client interface difference and backup interface difference
                # would be 1 in case of hardware fault.
                # Full config found closer to the DOM0 network config. Raise an exception since this should be
                # either empty set or length should be greater than 1 if no matching network found.
                # If this is 1, it means that one of the expected interface is having hardware issue.
                _hardware_fault = True
                _faulty_interface = ((set(_net.mGetClientNet().dom0_interfaces) - _result[_net.mGetClientNetType()]) |
                    (set(_net.mGetBackupNet().dom0_interfaces) - _result[_net.mGetBackupNetType()]))
                _full_config_network = _netenum.name

        _is_healthcheck = self.__ebox.mGetCmd() in ["checkcluster"]
        _dom0_hostname = _node.mGetHostname()
        if not _matching_network:
            _if_states_map = '\n'.join(map(str, _if_states))
            _error_msg = "No Network found matching interfaces state\n"\
                        f"Interfaces states:\n{_if_states_map}"
            _action = f"Check the Interface Physical states on dom0: {_node.mGetHostname()}"
            ebLogCritical(_error_msg, _action)
            if _is_healthcheck:
                _cause = "No network found matching runtime interfaces state."
                _action = "Check the states of physical interfaces on the respective dom0"
                _interface_details = self.mGetInterfaceDetails(_if_states, _result)
                _error_dict = {"CAUSE": _cause, "ACTION": _action, "INTERFACE_DETAILS": _interface_details}
                self.__ebox.mSetNetDetectError(_dom0_hostname, _error_dict)
        elif _hardware_fault:
            _error_msg = f"Faulty interface found: {_faulty_interface}, "\
                         f"Expected configuration: {_full_config_network}, Discovered configuration: {_matching_network.name}."
            _action = f"Bring the faulty interface {_faulty_interface} up for the expected configuration."
            ebLogCritical(_error_msg, _action)
            if _is_healthcheck:
                _interface_details = self.mGetInterfaceDetails(_if_states, _result)
                _error_dict = {"CAUSE": _error_msg, "ACTION": _action, "INTERFACE_DETAILS": _interface_details}
                self.__ebox.mSetNetDetectError(_dom0_hostname, _error_dict)
            return None
        else:
            self.mCacheNetworkOnDom0(_matching_network)

        return _matching_network
