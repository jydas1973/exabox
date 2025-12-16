#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/clunetworkvalidations.py /main/4 2025/03/13 19:59:04 jfsaldan Exp $
#
# clunetworkvalidations.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      clunetworkvalidations.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    02/12/25 - Bug 37570873 - EXADB-D|XS -- EXACLOUD |
#                           PROVISIONING | REVIEW AND ORGANIZE PREVM_CHECKS AND
#                           PREVM_SETUP STEPS
#    aararora    04/29/24 - ER 36485120: Support IPv6 in exacloud
#    jfsaldan    09/29/23 - Bug 35834771 - NODE RECOVERY: BONDETH0 OF NEWLY
#                           CREATED VM WAS NOT BROUGHT UP RESULTING IN CLIENT
#                           NETWORK ISSUE
#    ffrrodri    02/22/21 - Creation
#

import time
from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogTrace, ebLogWarn
from exabox.core.Context import get_gcontext
from exabox.utils.node import (connect_to_host, node_connect_to_host,
    node_exec_cmd, node_exec_cmd_check, node_cmd_abs_path_check,
    node_read_text_file)
from exabox.ovm.clumisc import ebCluEthernetConfig


class NetworkValidations:

    def __init__(self, aDomUNode=None):
        self.__domUNode = aDomUNode

    def mGetDomU(self):
        return self.__domUNode

    def mSetDomU(self, aDomUNode):
        self.__domUNode = aDomUNode

    def mArpingCheck(self, aInterfaceToArping, aGatewayIP, aNamespaceName=None):
        """
            Arping check of a Network from DomU

            :param: exaBoxNode aDomUNode: A live DomU where to run commands
            :param: str aInterfaceToArping: Interface to Arping to ('bondeth0' or 'bondeth1')
            :param: str aNamespaceName: Namespace installed
            :param: str aGatewayIP: Gateway IP address

            :return: boolean result: Result of the validation

            :raises: TypeError, ExacloudRuntimeError
        """

        _result = True
        _node = self.mGetDomU()

        if not _node:
            _msg = f'DomU not setted'
            ebLogError(_msg)
            raise TypeError(_msg)

        if aNamespaceName:
            _cmd = f'/sbin/ip netns exec {aNamespaceName} /sbin/arping -c 4 -I {aInterfaceToArping} {aGatewayIP}'
        else:
            _cmd = f'/sbin/arping -c 4 -I {aInterfaceToArping} {aGatewayIP}'
        _node.mExecuteCmd(_cmd)

        if _node.mGetCmdExitStatus() != 0:
            _msg = f'Error during arping check execution from DomU {_node.mGetHostname()} to gateway {aGatewayIP}'
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x800, 0xA, _msg)

        return _result

class ebNetworkValidations():

    def __init__(self, aCluctrl, aDom0DomUPair):
        self._ebox = aCluctrl
        self._dom0DomUPair = aDom0DomUPair
        self._ethConfig = ebCluEthernetConfig(self._ebox,
                self._ebox.mGetArgsOptions())

    def mCheckClientBackupIPSet(self):
        """
        This method is used to validate that both the Client and Backup
        interfaces in the DomUs from aDom0DomUPair (bondeth0/1) have an IP
        assigned. If they don't we try to set the IPs.
        Then
        """

        for _dom0, _domU in self._dom0DomUPair:

            # Get Network config from XML
            _net_config = self._ebox.mGetVMNetConfigs(_domU)
            _client_ip = _net_config.get("client").mGetNetIpAddr()
            _backup_ip = _net_config.get("backup").mGetNetIpAddr()
            _client_ipv6 = None
            if "client_ipv6" in _net_config:
                _client_ipv6 = _net_config.get("client_ipv6").mGetNetIpAddr()
            _backup_ipv6 = None
            if "backup_ipv6" in _net_config:
                _backup_ipv6 = _net_config.get("backup_ipv6").mGetNetIpAddr()

            ebLogInfo(f"Validating client ipv4: '{_client_ip}', "
                f"backup ipv4: '{_backup_ip}', client ipv6: '{_client_ipv6}', "
                f" backup ipv6: '{_backup_ipv6}', for '{_domU}'.")

            with connect_to_host(_domU, get_gcontext()) as _node:

                # Client/backup Interface check
                _interface_dict = {"bondeth0": [_client_ip, _client_ipv6], "bondeth1": [_backup_ip, _backup_ipv6]}
                _interface_mapping = {"bondeth0": "Client", "bondeth1": "Backup"}
                for _interface, _ip_list in _interface_dict.items():
                    for _ip in _ip_list:
                        # One of IPv4 or IPv6 IP may not be assigned
                        if not _ip or _ip == "::" or _ip == "0.0.0.0":
                            continue
                        if self.mChekIPIsSetInInterface(_node, _interface, _ip):
                            ebLogInfo(f"{_interface_mapping[_interface]} IP: {_ip} is set in {_domU}")
                        else:
                            # Attempt to reload
                            self.mReloadInterface(_node, _interface)
                            if self.mChekIPIsSetInInterface(
                                    _node, _interface, _ip):
                                ebLogInfo(f"{_interface_mapping[_interface]} IP: {_ip} is set in "
                                    f"{_domU} '{_interface}' after a reload")

                                if _interface_mapping[_interface] == "Client":
                                    # Restart sshd service so that ssshd listens on
                                    # bondeth0 interface
                                    self.mRestartService(_node, "sshd")

                            else:
                                _err = (f"{_interface_mapping[_interface]} IP is not assigned to '{_interface}' "
                                    f"after a reload on {_domU}")
                                ebLogError(_err)
                                raise ExacloudRuntimeError(0x0114, 0xA, _err)

    @staticmethod
    def mChekIPIsSetInInterface(aNode, aInterface, aIp)-> bool:
        """
        Uses ip and grep to check if aIp is assigned to aInterface in aNode

        :param aNode: an already connected exaBoxNode
        :param aInterface: an interface to reload

        :returns bool:
            True: If aIp is assigned
            False: if the ip is not assigned

        """
        _bin_ip = node_cmd_abs_path_check(aNode, "ip", sbin=True)
        _bin_grep = node_cmd_abs_path_check(aNode, "grep")

        _out_ip_check = node_exec_cmd(aNode,
            f'{_bin_ip} a s {aInterface} | {_bin_grep} "{aIp}"')

        return _out_ip_check.exit_code == 0


    @staticmethod
    def mReloadInterface(aNode, aInterface):
        """
        Uses 'ifdown' and 'ifup' to reload aInterface on aNode

        :param aNode: an already connected exaBoxNode
        :param aInterface: an interface to reload
        """

        _bin_ifup = node_cmd_abs_path_check(aNode, "ifup", sbin=True)
        _bin_ifdown = node_cmd_abs_path_check(aNode, "ifdown", sbin=True)

        _out_ifdown = node_exec_cmd(aNode, f"{_bin_ifdown} {aInterface}")
        ebLogTrace(_out_ifdown)

        time.sleep(2)

        _out_ifup = node_exec_cmd(aNode, f"{_bin_ifup} {aInterface}")
        ebLogTrace(_out_ifup)

        time.sleep(2)

        ebLogInfo(f"Interface {aInterface} reloaded in {aNode.mGetHostname()}")

    @staticmethod
    def mRestartService(aNode, aService):
        """
        Uses systemctl to restart the aService

        :param aNode: an already connected exaBoxNode
        :param aService: the name of the service to restart
        """

        _bin_systemctl = node_cmd_abs_path_check(aNode, "systemctl", sbin=True)

        _out_restart = node_exec_cmd(
                aNode, f"{_bin_systemctl} restart {aService}")
        ebLogTrace(_out_restart)
        time.sleep(2)

        ebLogInfo(f"Service: '{aService}' restarted in: '{aNode.mGetHostname()}'")


    def mCheckDom0EthernetSpeed(self)-> dict:
        """
        Checks Ethernet interfaces on each Dom0 node and returns a dictionary
        with interfaces that need their speed changed.

        Returns:
            dict: A dictionary where keys are Dom0 node names and values are
            dictionaries with Ethernet interface names as keys and expected
            speeds and autoned as values.
            {
                "dom0A": {
                    "eth1": (500, True),
                    "eth2": (500, True)
                }
            }
        """
        interfaces_to_update = {}

        for _dom0, _domU in self._dom0DomUPair:
            with connect_to_host(_dom0, get_gcontext()) as _node:
                _map = self._ebox.mGenBondMap(_node, True)

                for _ethx, _bondx in _map.items():
                    self._ethConfig.mValidateInterface(_node, _ethx)

                    _exadata_model = self._ebox.mGetExadataDom0Model(_dom0)
                    if self._ebox.mCompareExadataModel(_exadata_model, 'X9') >= 0:
                        if self._ebox.mCompareExadataModel(_exadata_model, 'X10') >= 0:
                            _base_speed = 100000
                        else:
                            _base_speed = 50000

                        _current_speed = int(node_read_text_file(_node, f"/sys/class/net/{_ethx}/speed").strip())
                        ebLogInfo(f"{_dom0}: {_ethx} link speed is {_current_speed}")

                        if _base_speed != _current_speed:
                            if _dom0 not in interfaces_to_update:
                                interfaces_to_update[_dom0] = {}
                            interfaces_to_update[_dom0][_ethx] = (_base_speed, True)  # Use autoneg on
                    else:
                        _cmd = f"/bin/cat /etc/sysconfig/network-scripts/ifcfg-{_ethx} | /bin/grep ETHTOOL_OPTS |  /bin/cut -d '=' -f 2"
                        _, _o, _ = _node.mExecuteCmd(_cmd)
                        _out = _o.readlines()
                        _base_speed = 25000
                        try:
                            if _out:
                                _base_speed = int(_out[0].strip().split()[1])
                                ebLogInfo(f"{_dom0}: speed in ifcfg-{_ethx} is configured to {_base_speed}")
                        except:
                            _base_speed = 25000
                            ebLogInfo(f"{_dom0}: unable to fetch link speed from ifcfg-{_ethx} defaulting the link speed to {_base_speed}")

                        _current_speed = int(node_read_text_file(_node, f"/sys/class/net/{_ethx}/speed").strip())
                        ebLogInfo(f"{_dom0}: {_ethx} link speed is {_current_speed}")

                        if _base_speed != _current_speed:
                            if _dom0 not in interfaces_to_update:
                                interfaces_to_update[_dom0] = {}
                            interfaces_to_update[_dom0][_ethx] = (_base_speed, False)  # Use autoneg off

                    _ethx_link_detect = node_read_text_file(_node, f"/sys/class/net/{_ethx}/carrier")
                    _issue_soft_warning = self._ebox.mIssueSoftWarningOnLinkfailure(_dom0, _ethx)
                    if int(_ethx_link_detect) == 1:
                        ebLogInfo(f"{_dom0}: {_ethx} link detected: yes")
                    else:
                        _err = f"Ethernet interfaces {_ethx} link detected: no"
                        if _issue_soft_warning:
                            ebLogWarn(f"{_dom0}: {_err}")
                        else:
                            ebLogError(f"{_dom0}: {_err}")
                            raise ExacloudRuntimeError(0x0126, 0x0A, _err)

        return interfaces_to_update

    def mUpdateDom0EthernetSpeeds(self, interfaces_to_update):
        """
        Updates the speed of Ethernet interfaces on remote nodes.

        Args:
            interfaces_to_update (dict): A dictionary where keys are Dom0 node
                names and values are dictionaries with Ethernet interface
                names as keys and tuples containing the expected speed and
                autoneg flag as values.
            {
                "dom0A": {
                    "eth1": (500, True),
                    "eth2": (500, True)
                }
            }
        """

        for _dom0, interfaces in interfaces_to_update.items():
            with connect_to_host(_dom0, get_gcontext()) as _node:
                for _ethx, (_base_speed, autoneg) in interfaces.items():
                    if autoneg:
                        node_exec_cmd(_node,
                            f"/usr/sbin/ethtool -s {_ethx} speed {_base_speed} autoneg on",
                            log_error=True, log_stdout_on_error=True)
                    else:
                        node_exec_cmd(_node,
                            f"/usr/sbin/ethtool -s {_ethx} speed {_base_speed} autoneg off",
                            log_error=True, log_stdout_on_error=True)

                    _count = 0
                    while True:
                        _current_speed = int(node_read_text_file(_node,
                            f"/sys/class/net/{_ethx}/speed").strip())
                        ebLogInfo(f"{_dom0}: {_ethx} updated link speed is {_current_speed}")

                        if _base_speed == _current_speed:
                            break

                        if _count >= 5:
                            # configure custom speeds when the default speed fails
                            _exadata_model = self._ebox.mGetExadataDom0Model(_dom0)
                            self._ethConfig.mUpdateCustomEthernetSpeed(
                                _node, _dom0, _ethx, _current_speed, _exadata_model)
                            break

                        _count += 1
                        time.sleep(10)
