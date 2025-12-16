#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/iptables/tests_iptablesnatcleanup.py /main/16 2025/05/08 08:36:37 gojoseph Exp $
#
# tests_iptablesnatcleanup.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_iptablesnatcleanup.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ffrrodri    10/29/21 - BUG 33520563: Correction of test failure after
#                           bug-33467589
#    ffrrodri    09/15/21 - Added tests for multivm iptables
#    alsepulv    04/19/21 - Enh 32789412: Move file location / update resource
#                           path
#    ffrrodri    03/19/21 - Creation
#
import unittest
import os
import json
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.core.Context import get_gcontext


class IPTablesCleanUp(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(False, False, aResourceFolder='exabox/exatest/cluctrl/iptables/resources/iptablesnat/')
        self._path = 'exabox/exatest/cluctrl/iptables/resources/iptablesnat/'

    def setUp(self):
        _add_config = {"nat_fileserver_ip": "10.10.10.10",
                       "nat_fileserver_port": "2081",
                       "ocps_jsonpath":
                           "exabox/exatest/resources/iptablesnat/ocpsSetup_fwd_proxy.json"}
        self.mGetUtil().mGetExaboxCfg().update(_add_config)
        self.mGetUtil().mPrepareEnviroment()

    IPRULES_PATH = 'exabox/exatest/cluctrl/iptables/resources/iptablesnatcleanup/iptables_rules.json'

    def read_json(self, path):
        abs_path = get_gcontext().mGetBasePath()
        json_file = os.path.join(abs_path, path)
        with open(json_file) as json_data_file:
            json_dict = json.load(json_data_file)
            return json_dict

    _iptables = ("-P INPUT ACCEPT\n"
                 "-P FORWARD DROP\n"
                 "-P OUTPUT ACCEPT\n"
                 "-A INPUT -i lo -j ACCEPT\n"
                 "-A INPUT -i vmeth0 -j ACCEPT\n"
                 '-A INPUT -m limit --limit 2/min -j LOG --log-prefix "IPTables-INPUT Dropped: "\n'
                 "-A INPUT -j DROP\n"
                 "-A FORWARD -o vmeth100 -p tcp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                 "-A FORWARD -o vmeth100 -p icmp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                 "-A FORWARD -i vmeth100 -p tcp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                 "-A FORWARD -i vmeth100 -p icmp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                 "-A FORWARD -o vmeth100 -p tcp -m tcp --dport 22 -j ACCEPT\n"
                 "-A FORWARD -o vmeth100 -p icmp -m icmp --icmp-type 8 -j ACCEPT\n"
                 "-A FORWARD -d 10.10.10.10/32 -i vmeth100 -p tcp -m tcp --dport 2081 -j ACCEPT\n"
                 "-A FORWARD -d 20.20.20.20/32 -i vmeth100 -p tcp -m tcp --dport 3081 -j ACCEPT\n"
                 "-A FORWARD -o vmeth200 -p tcp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                 "-A FORWARD -o vmeth200 -p icmp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                 "-A FORWARD -i vmeth200 -p tcp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                 "-A FORWARD -i vmeth200 -p icmp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                 "-A FORWARD -o vmeth200 -p tcp -m tcp --dport 22 -j ACCEPT\n"
                 "-A FORWARD -o vmeth200 -p icmp -m icmp --icmp-type 8 -j ACCEPT\n"
                 "-A FORWARD -d 10.10.10.10/32 -i vmeth200 -p tcp -m tcp --dport 2081 -j ACCEPT\n"
                 "-A FORWARD -d 20.20.20.20/32 -i vmeth200 -p tcp -m tcp --dport 3081 -j ACCEPT\n"
                 "-A FORWARD -o vmeth201 -p tcp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                 "-A FORWARD -o vmeth201 -p icmp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                 "-A FORWARD -i vmeth201 -p tcp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                 "-A FORWARD -i vmeth201 -p icmp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                 "-A FORWARD -o vmeth201 -p tcp -m tcp --dport 22 -j ACCEPT\n"
                 "-A FORWARD -o vmeth201 -p icmp -m icmp --icmp-type 8 -j ACCEPT\n"
                 "-A FORWARD -d 10.10.10.10/32 -i vmeth201 -p tcp -m tcp --dport 2081 -j ACCEPT\n"
                 "-A FORWARD -d 20.20.20.20/32 -i vmeth201 -p tcp -m tcp --dport 3081 -j ACCEPT\n"
                 "-A OUTPUT -o lo -j ACCEPT\n"
                 "-A OUTPUT -o vmeth0 -j ACCEPT")

    _iptables_nat = ("-P PREROUTING ACCEPT\n"
                     "-P INPUT ACCEPT\n"
                     "-P OUTPUT ACCEPT\n"
                     "-P POSTROUTING ACCEPT\n"
                     "-A PREROUTING -i vmeth100 -p tcp -m tcp --dport 2081 -j DNAT --to-destination 10.10.10.10\n"
                     "-A PREROUTING -i vmeth100 -p tcp -m tcp --dport 3081 -j DNAT --to-destination 20.20.20.20\n"
                     "-A PREROUTING -i vmeth200 -p tcp -m tcp --dport 2081 -j DNAT --to-destination 10.10.10.10\n"
                     "-A PREROUTING -i vmeth200 -p tcp -m tcp --dport 3081 -j DNAT --to-destination 20.20.20.20\n"
                     "-A PREROUTING -i vmeth201 -p tcp -m tcp --dport 2081 -j DNAT --to-destination 10.10.10.10\n"
                     "-A PREROUTING -i vmeth201 -p tcp -m tcp --dport 3081 -j DNAT --to-destination 20.20.20.20\n")

    _multivm_drop_rules = ("-P INPUT ACCEPT\n"
                           "-P FORWARD DROP\n"
                           "-P OUTPUT ACCEPT\n"
                           "-N FI-vnet100\n"
                           "-N FI-vnet101\n"
                           "-N FO-vnet100\n"
                           "-N FO-vnet101\n"
                           "-N HI-vnet100\n"
                           "-N HI-vnet101\n"
                           "-N libvirt-host-in\n"
                           "-N libvirt-in\n"
                           "-N libvirt-in-post\n"
                           "-N libvirt-out\n"
                           "-A INPUT -j libvirt -host-in\n"
                           "-A INPUT -i lo -j ACCEPT\n"
                           "-A INPUT -i vmeth0 -j ACCEPT\n"
                           "-A INPUT -p icmp -m icmp --icmp-type 8 -j ACCEPT\n"
                           '-A INPUT -m limit --limit 2/min -j LOG --log-prefix "IPTables-INPUT Dropped: "\n'
                           "-A INPUT -j DROP\n"
                           "-A FORWARD -j libvirt-in\n"
                           "-A FORWARD -j libvirt-out\n"
                           "-A FORWARD -j libvirt-in-post\n"
                           "-A FORWARD -o vmeth100 -p tcp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                           "-A FORWARD -o vmeth100 -p icmp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                           "-A FORWARD -i vmeth100 -p tcp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                           "-A FORWARD -i vmeth100 -p icmp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                           "-A FORWARD -o vmeth100 -p tcp -m tcp --dport 22 -j ACCEPT\n"
                           "-A FORWARD -o vmeth100 -p icmp -m icmp --icmp-type 8 -j ACCEPT\n"
                           "-A FORWARD -o vmeth200 -p tcp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                           "-A FORWARD -o vmeth200 -p icmp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                           "-A FORWARD -i vmeth200 -p tcp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                           "-A FORWARD -i vmeth200 -p icmp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                           "-A FORWARD -o vmeth200 -p tcp -m tcp --dport 22 -j ACCEPT\n"
                           "-A FORWARD -o vmeth200 -p icmp -m icmp --icmp-type 8 -j ACCEPT\n"
                           "-A FORWARD -o vmeth201 -p tcp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                           "-A FORWARD -o vmeth201 -p icmp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                           "-A FORWARD -i vmeth201 -p tcp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                           "-A FORWARD -i vmeth201 -p icmp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT\n"
                           "-A FORWARD -o vmeth201 -p tcp -m tcp --dport 22 -j ACCEPT\n"
                           "-A FORWARD -o vmeth201 -p icmp -m icmp --icmp-type 8 -j ACCEPT\n"
                           '-A FORWARD -m limit --limit 2/min -j LOG --log-prefix "IPTables-FORWARD Dropped: "\n'
                           "-A OUTPUT -o lo -j ACCEPT\n"
                           "-A OUTPUT -o vmeth0 -j ACCEPT\n"
                           "-A FI-vnet100 -d 169.254.169.254/32 -p tcp -m tcp --sport 7060 -m conntrack --ctstate ESTABLISHED -m conntrack --ctdir REPLY -j RETURN\n"
                           "-A FI-vnet100 -d 169.254.169.254/32 -p tcp -m tcp --sport 7070 -m conntrack --ctstate ESTABLISHED -m conntrack --ctdir REPLY -j RETURN\n"
                           "-A FI-vnet100 -p tcp -m tcp --sport 7060 -j DROP\n"
                           "-A FI-vnet100 -p tcp -m tcp --sport 7070 -j DROP\n"
                           "-A FI-vnet100 -j RETURN\n"
                           "-A FI-vnet101 -p tcp -m tcp --sport 7060 -j DROP\n"
                           "-A FI-vnet101 -p tcp -m tcp --sport 7070 -j DROP\n"
                           "-A FI-vnet101 -j RETURN\n"
                           "-A FO-vnet100 -s 169.254.169.254/32 -p tcp -m tcp --dport 7060 -m conntrack --ctstate NEW, ESTABLISHED -m conntrack --ctdir ORIGINAL -j ACCEPT\n"
                           "-A FO-vnet100 -s 169.254.169.254/32 -p tcp -m tcp --dport 7070 -m conntrack --ctstate NEW, ESTABLISHED -m conntrack --ctdir ORIGINAL -j ACCEPT\n"
                           "-A FO-vnet100 -p tcp -m tcp --dport 7060 -j DROP\n"
                           "-A FO-vnet100 -p tcp -m tcp --dport 7070 -j DROP\n"
                           "-A FO-vnet100 -j ACCEPT\n"
                           "-A FO-vnet101 -p tcp -m tcp --dport 7060 -j DROP\n"
                           "-A FO-vnet101 -p tcp -m tcp --dport 7070 -j DROP\n"
                           "-A FO-vnet101 -j ACCEPT\n"
                           "-A HI-vnet100 -d 169.254.169.254/32 -p tcp -m tcp --sport 7060 -m conntrack --ctstate ESTABLISHED -m conntrack --ctdir REPLY -j RETURN\n"
                           "-A HI-vnet100 -d 169.254.169.254/32 -p tcp -m tcp --sport 7070 -m conntrack --ctstate ESTABLISHED -m conntrack --ctdir REPLY -j RETURN\n"
                           "-A HI-vnet100 -p tcp -m tcp --sport 7060 -j DROP\n"
                           "-A HI-vnet100 -p tcp -m tcp --sport 7070 -j DROP\n"
                           "-A HI-vnet100 -j RETURN\n"
                           "-A HI-vnet101 -p tcp -m tcp --sport 7060 -j DROP\n"
                           "-A HI-vnet101 -p tcp -m tcp --sport 7070 -j DROP\n"
                           "-A HI-vnet101 -j RETURN\n"
                           "-A libvirt-host-in -m physdev --physdev-in vnet100 -g HI-vnet100\n"
                           "-A libvirt-host-in -m physdev --physdev-in vnet101 -g HI-vnet101\n"
                           "-A libvirt-in -m physdev --physdev-in vnet100 -g FI-vnet100\n"
                           "-A libvirt-in -m physdev --physdev-in vnet101 -g FI-vnet101\n"
                           "-A libvirt-in-post -m physdev --physdev-in vnet100 -j ACCEPT\n"
                           "-A libvirt-in-post -m physdev --physdev-in vnet101 -j ACCEPT\n"
                           "-A libvirt-out -m physdev --physdev-out vnet100 --physdev-is-bridged -g FO-vnet100\n"
                           "-A libvirt-out -m physdev --physdev-out vnet101 --physdev-is-bridged -g FO-vnet101\n")

    def test_iptablesnat_cleanup(self):

        _commands = [
            exaMockCommand('/bin/mkdir*'),
            exaMockCommand('/bin/scp*'),
            exaMockCommand('iptables -S', aStdout=self._iptables),
            exaMockCommand('iptables -S -t nat', aStdout=self._iptables_nat),
            exaMockCommand('iptables -S')
        ]

        _ip_rules_list = []
        for _ in range(116):
            _ip_rules_list.append(exaMockCommand('iptables -A*'))
        _commands.extend(_ip_rules_list)

        _commands.extend([exaMockCommand('-A FORWARD -m limit --limit 2/min -j LOG --log-prefix "IPTables-FORWARD '
                                         'Dropped: "'),
                          exaMockCommand('iptables -A OUTPUT -o*'),
                          exaMockCommand('iptables -A OUTPUT -o*')])

        _ip_rules_d_list = []
        for _ in range(27):
            _ip_rules_d_list.append(exaMockCommand('iptables -D*'))
        _commands.extend(_ip_rules_list)

        _ip_rules_t_nat_d_list = []
        for _ in range(40):
            _ip_rules_t_nat_d_list.append(exaMockCommand('iptables -t nat -D*'))
        _commands.extend(_ip_rules_t_nat_d_list)

        _ip_rules_t_nat_a_list = []
        for _ in range(12):
            _ip_rules_t_nat_a_list.append(exaMockCommand('iptables -t nat -A*'))
        _commands.extend(_ip_rules_t_nat_a_list)

        _final_command_list = [
            exaMockCommand("ip6tables -P INPUT*"),
            exaMockCommand("ip6tables -P FORWARD*"),
            exaMockCommand("ip6tables -P OUTPUT*"),
            exaMockCommand("iptables -S"),
            exaMockCommand("cp /etc/sysconfig/iptables*"),
            exaMockCommand("/sbin/service*"),
            exaMockCommand("cp*"),
            exaMockCommand("/sbin/iptables-save*"),
            exaMockCommand("/bin/cat*"),
            exaMockCommand("/bin/cat*"),
            exaMockCommand("iptables -S"),
            exaMockCommand("cat /etc/sysconfig/iptables"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*")
        ]

        _commands.extend(_final_command_list)

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        self.mGetClubox().mSetupNATIptablesOnDom0v2()

    def test_iptables_log_dropped_packets(self):
        _ip_default_rules, _ip_rules_list, _, _ = self.mGetClubox().mSetupNATIptablesOnDom0v2(
            True)

        _rules = self.read_json(self.IPRULES_PATH)['rules']

        return self.assertEqual(_ip_default_rules + _ip_rules_list, _rules)

    def test_iptables_from_json_file(self):
        _ip_default_rules, _ip_rules_list, _nat, _ports = self.mGetClubox().mSetupNATIptablesOnDom0v2(
            True)

        _rules = self.read_json(self.IPRULES_PATH)['rules']

        return self.assertEqual(_ip_default_rules + _ip_rules_list, _rules)

    def test_iptablesnat_cleanup_all_rules(self):

        _iptables_s = ("-P INPUT ACCEPT\n"
                       "-P FORWARD DROP\n"
                       "-P OUTPUT ACCEPT\n"
                       "-N CUSTOM_CHAIN\n"
                       "-A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT\n"
                       "-A INPUT -p icmp -j ACCEPT\n"
                       "-A INPUT -i lo -j ACCEPT\n"
                       "-A INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT\n"
                       "-A INPUT -j REJECT --reject-with icmp-host-prohibited\n"
                       "-A FORWARD -j REJECT --reject-with icmp-host-prohibited\n"
                       )

        _iptables_bin = "/usr/bin/flock /var/lock/iptables /sbin/iptables --wait 10"
        _commands = [
            exaMockCommand('/usr/bin/flock /var/lock/iptables /sbin/iptables --help', aStdout="wait seconds"),
            exaMockCommand('/bin/mkdir*'),
            exaMockCommand('/bin/scp*'),
            exaMockCommand(f"{_iptables_bin} -S", aStdout=_iptables_s),
            exaMockCommand(f"{_iptables_bin} -S -t nat", aStdout=self._iptables_nat),
            exaMockCommand(f"{_iptables_bin} -S", aStdout=self._iptables),
            exaMockCommand(f"{_iptables_bin}",aStdout=self._iptables),
            exaMockCommand(f"{_iptables_bin} -A FORWARD",aPersist=True)
        ]

        _ip_rules_d_list = [
            exaMockCommand(f"{_iptables_bin} -D FORWARD -j REJECT --reject-with icmp-host-prohibited"),
            exaMockCommand(f"{_iptables_bin} -D INPUT -j REJECT --reject-with icmp-host-prohibited"),
            exaMockCommand(f"{_iptables_bin} -D INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT"),
            exaMockCommand(f"{_iptables_bin} -D INPUT -p icmp -j ACCEPT"),
            exaMockCommand(f"{_iptables_bin} -D INPUT -i lo -j ACCEPT"),
            exaMockCommand(f"{_iptables_bin} -D INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT"),
            exaMockCommand(f"{_iptables_bin} -X CUSTOM_CHAIN"),
            exaMockCommand(f"{_iptables_bin} -A FORWARD -o*")
        ]
        _commands.extend(_ip_rules_d_list)

        _ip_rules_list = []
        for _ in range(120):
            _ip_rules_list.append(exaMockCommand(f"{_iptables_bin} -A*"))
        _commands.extend(_ip_rules_list)

        _commands.extend([exaMockCommand(f'-A FORWARD -m limit --limit 2/min -j LOG --log-prefix "IPTables-FORWARD '
                                         'Dropped: "'),
                          exaMockCommand(f"{_iptables_bin} -A OUTPUT -o*"),
                          exaMockCommand(f"{_iptables_bin} -A OUTPUT -o*")])

        _final_command_list = [
            exaMockCommand("/sbin/ip6tables -P*"),
            exaMockCommand("/sbin/ip6tables -P*"),
            exaMockCommand("/sbin/ip6tables -P*"),
            exaMockCommand(f"{_iptables_bin} -S"),
            exaMockCommand("cp /etc/sysconfig/iptables*"),
            exaMockCommand("/sbin/service*"),
            exaMockCommand("cp*"),
            exaMockCommand("/sbin/iptables-save*"),
            exaMockCommand("/bin/cat*"),
            exaMockCommand("/bin/cat*"),
            exaMockCommand(f"{_iptables_bin} -S"),
            exaMockCommand("cat /etc/sysconfig/iptables"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*")
        ]

        _commands.extend(_final_command_list)

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        self.mGetClubox().mSetupNATIptablesOnDom0v2()

    def test_iptables_multivm_cleanup(self):

        _commands = [
            exaMockCommand('/bin/mkdir*'),
            exaMockCommand('/bin/scp*'),
            exaMockCommand('iptables -S', aStdout=self._multivm_drop_rules),
            exaMockCommand('iptables -S -t nat', aStdout=self._iptables_nat),
            exaMockCommand('iptables -S')
        ]

        _ip_rules_list = []
        for _ in range(116):
            _ip_rules_list.append(exaMockCommand('iptables -A*'))
        _commands.extend(_ip_rules_list)

        _commands.extend([exaMockCommand('-A FORWARD -m limit --limit 2/min -j LOG --log-prefix "IPTables-FORWARD '
                                         'Dropped: "'),
                          exaMockCommand('iptables -A OUTPUT -o*'),
                          exaMockCommand('iptables -A OUTPUT -o*')])

        _ip_rules_d_list = []
        for _ in range(27):
            _ip_rules_d_list.append(exaMockCommand('iptables -D*'))
        _commands.extend(_ip_rules_list)

        _ip_rules_t_nat_d_list = []
        for _ in range(40):
            _ip_rules_t_nat_d_list.append(exaMockCommand('iptables -t nat -D*'))
        _commands.extend(_ip_rules_t_nat_d_list)

        _ip_rules_t_nat_a_list = []
        for _ in range(12):
            _ip_rules_t_nat_a_list.append(exaMockCommand('iptables -t nat -A*'))
        _commands.extend(_ip_rules_t_nat_a_list)

        _final_command_list = [
            exaMockCommand("ip6tables -P INPUT*"),
            exaMockCommand("ip6tables -P FORWARD*"),
            exaMockCommand("ip6tables -P OUTPUT*"),
            exaMockCommand("iptables -S"),
            exaMockCommand("cp /etc/sysconfig/iptables*"),
            exaMockCommand("/sbin/service*"),
            exaMockCommand("cp*"),
            exaMockCommand("/sbin/iptables-save*"),
            exaMockCommand("/bin/cat*"),
            exaMockCommand("/bin/cat*"),
            exaMockCommand("iptables -S"),
            exaMockCommand("cat /etc/sysconfig/iptables"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*")
        ]

        _commands.extend(_final_command_list)

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        self.mGetClubox().mSetupNATIptablesOnDom0v2()

    def test_iptables_multivm_cleanup_input_chain(self):

        self._multivm_drop_rules.replace("-A INPUT -p icmp -m icmp --icmp-type 8 -j ACCEPT\n",
                                         "-A INPUT -p icmp --icmp-type 8 -j ACCEPT\n")

        _commands = [
            exaMockCommand('/bin/mkdir*'),
            exaMockCommand('/bin/scp*'),
            exaMockCommand('iptables -S', aStdout=self._multivm_drop_rules),
            exaMockCommand('iptables -S -t nat', aStdout=self._iptables_nat),
            exaMockCommand('iptables -S')
        ]

        _ip_rules_list = []
        for _ in range(116):
            _ip_rules_list.append(exaMockCommand('iptables -A*'))
        _commands.extend(_ip_rules_list)

        _commands.extend([exaMockCommand('-A FORWARD -m limit --limit 2/min -j LOG --log-prefix "IPTables-FORWARD '
                                         'Dropped: "'),
                          exaMockCommand('iptables -A OUTPUT -o*'),
                          exaMockCommand('iptables -A OUTPUT -o*')])

        _ip_rules_d_list = []
        for _ in range(27):
            _ip_rules_d_list.append(exaMockCommand('iptables -D*'))
        _commands.extend(_ip_rules_list)

        _ip_rules_t_nat_d_list = []
        for _ in range(40):
            _ip_rules_t_nat_d_list.append(exaMockCommand('iptables -t nat -D*'))
        _commands.extend(_ip_rules_t_nat_d_list)

        _ip_rules_t_nat_a_list = []
        for _ in range(12):
            _ip_rules_t_nat_a_list.append(exaMockCommand('iptables -t nat -A*'))
        _commands.extend(_ip_rules_t_nat_a_list)

        _final_command_list = [
            exaMockCommand("ip6tables -P INPUT*"),
            exaMockCommand("ip6tables -P FORWARD*"),
            exaMockCommand("ip6tables -P OUTPUT*"),
            exaMockCommand("iptables -S"),
            exaMockCommand("cp /etc/sysconfig/iptables*"),
            exaMockCommand("/sbin/service*"),
            exaMockCommand("cp*"),
            exaMockCommand("/sbin/iptables-save*"),
            exaMockCommand("/bin/cat*"),
            exaMockCommand("/bin/cat*"),
            exaMockCommand("iptables -S"),
            exaMockCommand("cat /etc/sysconfig/iptables"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*")
        ]

        _commands.extend(_final_command_list)

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        self.mGetClubox().mSetSharedEnv(True)

        self.mGetClubox().mSetupNATIptablesOnDom0v2()

    def test_iptables_multivm_cleanup_drop_all(self):

        _commands = [
            exaMockCommand('/bin/mkdir*'),
            exaMockCommand('/bin/scp*'),
            exaMockCommand('iptables -S', aStdout=self._multivm_drop_rules),
            exaMockCommand('iptables -S -t nat', aStdout=self._iptables_nat),
            exaMockCommand('iptables -S')
        ]

        _ip_rules_list = []
        for _ in range(116):
            _ip_rules_list.append(exaMockCommand('iptables -A*'))
        _commands.extend(_ip_rules_list)

        _commands.extend([exaMockCommand('-A FORWARD -m limit --limit 2/min -j LOG --log-prefix "IPTables-FORWARD '
                                         'Dropped: "'),
                          exaMockCommand('iptables -A OUTPUT -o*'),
                          exaMockCommand('iptables -A OUTPUT -o*')])

        _ip_rules_d_list = []
        for _ in range(27):
            _ip_rules_d_list.append(exaMockCommand('iptables -D*'))
        _commands.extend(_ip_rules_list)

        _ip_rules_t_nat_d_list = []
        for _ in range(40):
            _ip_rules_t_nat_d_list.append(exaMockCommand('iptables -t nat -D*'))
        _commands.extend(_ip_rules_t_nat_d_list)

        _ip_rules_t_nat_a_list = []
        for _ in range(12):
            _ip_rules_t_nat_a_list.append(exaMockCommand('iptables -t nat -A*'))
        _commands.extend(_ip_rules_t_nat_a_list)

        _final_command_list = [
            exaMockCommand("ip6tables -P INPUT*"),
            exaMockCommand("ip6tables -P FORWARD*"),
            exaMockCommand("ip6tables -P OUTPUT*"),
            exaMockCommand("iptables -S"),
            exaMockCommand("cp /etc/sysconfig/iptables*"),
            exaMockCommand("/sbin/service*"),
            exaMockCommand("cp*"),
            exaMockCommand("/sbin/iptables-save*"),
            exaMockCommand("/bin/cat*"),
            exaMockCommand("/bin/cat*"),
            exaMockCommand("iptables -S"),
            exaMockCommand("cat /etc/sysconfig/iptables"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*"),
            exaMockCommand("/bin/sed*")
        ]

        _commands.extend(_final_command_list)

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        self.mGetClubox().mSetSharedEnv(False)

        self.mGetClubox().mSetupNATIptablesOnDom0v2()


if __name__ == '__main__':
    unittest.main()
