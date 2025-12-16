#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/network/tests_networking.py /main/2 2022/01/24 12:34:30 scoral Exp $
#
# tests_networking.py
#
# Copyright (c) 2022, Oracle and/or its affiliates.
#
#    NAME
#      tests_networking.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ffrrodri    01/06/22 - Creation
#
import unittest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.MockCommand import exaMockCommand


class IPTablesCleanUp(ebTestClucontrol):

    def test_disable_dom0_IBR(self):

        _grep_output = "config:yes"

        _commands = [
            exaMockCommand("grep -n RDS_LOAD*", aRc=0, aStdout=_grep_output)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        self.mGetClubox().mDisableDom0IBRdsModule(False)

        return self.assertTrue(True, "Method mDisableDom0IBRdsModule executed successfully")

    def test_dom0_X7_bondfix(self):

        _commands = [
            exaMockCommand("ifup*", aRc=0, aStdout="output"),
            exaMockCommand("ethtool*", aRc=0, aStdout="output"),
            exaMockCommand("ethtool*", aRc=0, aStdout="output")
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        self.mGetClubox().mDom0X7BondFix()

        return self.assertTrue(True, "Method mDom0X7BondFix executed successfully")

    def test_handler_reset_dom0_network_mapping(self):
        _grep_output = ("/etc/sysconfig/network-scripts/ifcfg-eth5:MASTER=bondeth0\n"
                        "/etc/sysconfig/network-scripts/ifcfg-eth6:MASTER=bondeth0")

        _get_model_commands = [
            exaMockCommand("/opt/oracle.cellos/exadata.img.hw*", aRc=0, aStdout="ORACLE SERVER X7-2L")
        ]

        _commands = [
            exaMockCommand("grep MASTER /etc/sysconfig/network-scripts/ifcfg-eth?", aRc=0, aStdout=_grep_output),
            exaMockCommand("sed*", aRc=0),
            exaMockCommand("sed*", aRc=0),
            exaMockCommand("sed*", aRc=0),
            exaMockCommand("sed*", aRc=0),
            exaMockCommand("rm*", aRc=0)
        ]

        _reboot_commands = [
            exaMockCommand("reboot*", aRc=0)
        ]

        _last_commands = [
            exaMockCommand("ip addr show*", aRc=0)
        ]

        _local_commands = [
            exaMockCommand("/bin/ping -c*", aRc=0, aStdout="reached", aStderr="not reached"),
            exaMockCommand("/bin/ping -c*", aRc=0, aStdout="reached", aStderr="not reached")
        ]

        _cmds = {
            _dom0: [
                _commands,
                _reboot_commands,
                _last_commands
            ]
            for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair()
        }
        _cmds[self.mGetClubox().mReturnDom0DomUPair()[0][0]].insert(0, _get_model_commands)
        _cmds[self.mGetRegexLocal()] = [_local_commands]

        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetTimeoutEcops(0)
        self.mGetClubox().mHandlerResetDom0NetworkMapping()

        return self.assertTrue(True, "Method mHandlerResetDom0NetworkMapping executed successfully")

    def test_dom0_cleanup_ebtables(self):

        _xm_lisr_response = ("Name                                        ID   Mem VCPUs      State   Time(s)\n"
                             "Domain-0                                     0  8792     4     r----- 14341347.0\n"
                             "scaqab10adm01vm02.us.oracle.com             40 92163    10     -b---- 877940.6\n"
                             "scaqab10adm01vm04.us.oracle.com             70 92163    10     -b---- 911741.4\n"
                             "scaqab10adm01vm05.us.oracle.com             61 92163    10     --p---     44.2\n"
                             "scaqab10adm01vm06.us.oracle.com             60 92163    10     --p---     37.8\n")

        _commands = [
            exaMockCommand("xm list*", aRc=0, aStdout=_xm_lisr_response),
            exaMockCommand("ebtables*", aRc=0, aStdout="output")
        ]

        for _i in range(8):
            _commands.append(exaMockCommand("flock*", aRc=0))

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        self.mGetClubox().mCleanupEbtablesOnDom0()

        return self.assertTrue(True, "Method mCleanupEbtablesOnDom0 executed successfully")


if __name__ == '__main__':
    unittest.main()
