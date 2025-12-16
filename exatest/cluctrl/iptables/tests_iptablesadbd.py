#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/iptables/tests_iptablesadbd.py /main/1 2021/10/11 15:32:27 ffrrodri Exp $
#
# tests_iptablesadbd.py
#
# Copyright (c) 2021, Oracle and/or its affiliates. 
#
#    NAME
#      tests_iptablesadbd.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ffrrodri    10/01/21 - Creation
#
import unittest

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.ovm.cluiptablesroce import ebIpTablesRoCE


class IPTablesADBD(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        _resources = 'exabox/exatest/cluctrl/iptables/resources/iptablesnat/'
        super().setUpClass(aResourceFolder=_resources)

    _iptables = (
                    "-P INPUT ACCEPT\n"
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
                    "-A INPUT -j libvirt-host-in\n"
                    "-A INPUT -i lo -j ACCEPT\n"
                    "-A INPUT -i vmeth0 -j ACCEPT\n"
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
                    "-A FO-vnet100 -s 169.254.169.254/32 -p tcp -m tcp --dport 7060 -m conntrack --ctstate NEW,ESTABLISHED -m conntrack --ctdir ORIGINAL -j ACCEPT\n"
                    "-A FO-vnet100 -s 169.254.169.254/32 -p tcp -m tcp --dport 7070 -m conntrack --ctstate NEW,ESTABLISHED -m conntrack --ctdir ORIGINAL -j ACCEPT\n"
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
                    "-A libvirt-out -m physdev --physdev-out vnet101 --physdev-is-bridged -g FO-vnet101"
    )

    _incomplete_iptables = (
        "-P INPUT ACCEPT\n"
        "-P FORWARD DROP\n"
        "-P OUTPUT ACCEPT\n"
    )

    def test_success_iptables_validation(self):

        _commands = [
            exaMockCommand('iptables -S', aStdout=self._iptables)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _dom0, _ = self.mGetClubox().mReturnDom0DomUPair()

        _result = ebIpTablesRoCE.mValidateIptables(_dom0[0])

        self.assertTrue(_result)

    def test_fail_iptables_validation(self):

        _commands = [
            exaMockCommand('iptables -S', aStdout=self._incomplete_iptables)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _dom0, _ = self.mGetClubox().mReturnDom0DomUPair()

        self.assertRaises(ExacloudRuntimeError, lambda: ebIpTablesRoCE.mValidateIptables(_dom0[0]))


if __name__ == '__main__':
    unittest.main()






