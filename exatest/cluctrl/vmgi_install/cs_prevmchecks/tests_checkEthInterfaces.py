#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/vmgi_install/cs_prevmchecks/tests_checkEthInterfaces.py /main/3 2022/06/02 07:34:42 ffrrodri Exp $
#
# tests_checkEthInterfaces.py
#
# Copyright (c) 2021, 2022, Oracle and/or its affiliates. 
#
#    NAME
#      tests_checkEthInterfaces.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ffrrodri    03/12/21 - Creation
#
import unittest

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand


class EthInterfacesCheck(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    _network_files_result = ("/etc/sysconfig/network-scripts/ifcfg-eth0\n"
                             "/etc/sysconfig/network-scripts/ifcfg-eth4\n"
                             "/etc/sysconfig/network-scripts/ifcfg-eth1\n"
                             "/etc/sysconfig/network-scripts/ifcfg-eth5\n"
                             "/etc/sysconfig/network-scripts/ifcfg-eth2\n"
                             "/etc/sysconfig/network-scripts/ifcfg-eth6\n"
                             "/etc/sysconfig/network-scripts/ifcfg-eth3\n"
                             "/etc/sysconfig/network-scripts/ifcfg-eth7")

    _interfaces_result = ("2: eth4: <BROADCAST,MULTICAST,SLAVE,UP,LOWER_UP> mtu 1500 qdisc mq master bondeth0 state UP qlen 1000 link/ether 90:e2:ba:da:52:e4 brd ff:ff:ff:ff:ff:ff\n"
                          "3: eth5: <BROADCAST,MULTICAST,SLAVE,UP,LOWER_UP> mtu 1500 qdisc mq master bondeth0 state UP qlen 1000 link/ether 90:e2:ba:da:52:e4 brd ff:ff:ff:ff:ff:ff\n"
                          "4: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq master vmeth0 state UP qlen 1000 link/ether 00:10:e0:c1:3a:2e brd ff:ff:ff:ff:ff:ff\n"
                          "5: eth2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq master vmeth1 state UP qlen 1000 link/ether 00:10:e0:c1:3a:2f brd ff:ff:ff:ff:ff:ff\n"
                          "6: eth10: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN qlen 1000 link/ether 00:10:e0:c1:3a:30 brd ff:ff:ff:ff:ff:ff\n"
                          "7: eth11: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN qlen 1000 ink/ether 00:10:e0:c1:3a:31 brd ff:ff:ff:ff:ff:ff\n"
                          "8: eth6: <BROADCAST,MULTICAST,SLAVE,UP,LOWER_UP> mtu 1500 qdisc mq master bondeth1 state UP qlen 1000 link/ether 90:e2:ba:47:ff:c8 brd ff:ff:ff:ff:ff:ff\n"
                          "9: eth10: <BROADCAST,MULTICAST,SLAVE,UP,LOWER_UP> mtu 1500 qdisc mq master bondeth1 state UP qlen 1000 link/ether 90:e2:ba:47:ff:c8 brd ff:ff:ff:ff:ff:ff\n"
                          "13: eth10: <BROADCAST,MULTICAST,MASTER,UP,LOWER_UP> mtu 1500 qdisc noqueue master vmbond state UP  link/ether 90:e2:ba:da:52:e4 brd ff:ff:ff:ff:ff:ff\n"
                          "15: bondeth1: <BROADCAST,MULTICAST,MASTER,UP,LOWER_UP> mtu 1500 qdisc noqueue master vmbondeth1 state UP  link/ether 90:e2:ba:47:ff:c8 brd ff:ff:ff:ff:ff:ff")

    _result = ['rm -f /etc/sysconfig/network-scripts/ifcfg-eth1',
               'rm -f /etc/sysconfig/network-scripts/ifcfg-eth3',
               'rm -f /etc/sysconfig/network-scripts/ifcfg-eth7']

    def test_interfaces_check(self):

        _commands = [
            exaMockCommand('/sbin/ip link show', aStdout=self._interfaces_result),
            exaMockCommand('/bin/ls /etc/sysconfig/network-scripts/ifcfg-eth*', aStdout=self._network_files_result),
            exaMockCommand('rm -f /etc/sysconfig/network-scripts/ifcfg-*'),
            exaMockCommand('rm -f /etc/sysconfig/network-scripts/ifcfg-*'),
            exaMockCommand('rm -f /etc/sysconfig/network-scripts/ifcfg-*'),
            exaMockCommand('/sbin/brctl show | /bin/awk*')
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        _dom0, _ = self.mGetClubox().mReturnDom0DomUPair()

        self.mPrepareMockCommands(_cmds)

        _interfaces_files_removed = self.mGetClubox().mCheckEthInterfaces(_dom0[0])

        self.assertEqual(self._result, _interfaces_files_removed)


if __name__ == '__main__':
    unittest.main()
