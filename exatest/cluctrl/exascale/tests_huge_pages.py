#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/exascale/tests_huge_pages.py /main/3 2024/11/12 13:12:43 jesandov Exp $
#
# tests_vm_move.py
#
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_vm_move.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    12/06/22 - Creation
#

import os
import unittest
import shutil
from unittest.mock import patch
 
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import MockCommand, exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.cluexascale import ebCluExaScale

class ebTestHugePages(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=False)
        self.mGetClubox(self).mSetExaScale(True)
        self.mGetClubox(self).mSetDebug(True)

    @patch("exabox.ovm.vmcontrol.ebVgLifeCycle.mDispatchEvent", return_value=0)
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRestartVM", return_value=0)
    def test_001_huge_page_new_value(self, mock_mDispatchEvent, mock_mRestartVM):

        #Mock commands
        _cmds = {
            self.mGetRegexVm(): [
                [
                    # Try to find the value from other files
                    exaMockCommand("sysctl -n vm.nr_hugepages", aStdout="0"),
                    exaMockCommand("cat /etc/sysctl.conf.*", aRc=1),
                    exaMockCommand("/bin/ls /etc/sysctl.d/", aStdout="999_new_config.conf"),
                    exaMockCommand("cat .*999_new_config.conf", aStdout="not_huge_pages = 100"),

                    # Copy new value
                    exaMockCommand("cp.*sysctl.conf"),
                    exaMockCommand("echo.*sysctl.conf"),
                    exaMockCommand("sysctl -p"),

                    # Verify new value
                    exaMockCommand("sysctl -n vm.nr_hugepages.*", aStdout="25600"),
                    exaMockCommand("cat /etc/sysctl.conf.*", aStdout="vm.nr_hugepages = 25600"),
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("imageinfo | grep 'Node type:'"),
                    exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n"),
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'"),
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),

                    exaMockCommand("xm list", aStdout=""),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=""),
                ],
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "vm": {
                "gb_memory": 100
            }
        }

        #Execute the clucontrol function
        _exascale = ebCluExaScale(self.mGetClubox())
        _exascale.mConfigureHugePage(_options)


    @patch("exabox.ovm.vmcontrol.ebVgLifeCycle.mDispatchEvent", return_value=0)
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRestartVM", return_value=0)
    def test_002_huge_page_replace(self, mock_mDispatchEvent, mock_mRestartVM):

        #Mock commands
        _cmds = {
            self.mGetRegexVm(): [
                [
                    # Try to find the value from other files
                    exaMockCommand("sysctl -n vm.nr_hugepages", aStdout="100"),
                    exaMockCommand("cat /etc/sysctl.conf.*", aRc=1),
                    exaMockCommand("/bin/ls /etc/sysctl.d/", aStdout="999_new_config.conf"),
                    exaMockCommand("cat .*999_new_config.conf", aStdout="vm.nr_hugepages = 100"),

                    # Copy new value
                    exaMockCommand("cp.*999_new_config.conf"),
                    exaMockCommand("sed.*999_new_config.conf"),
                    exaMockCommand("sysctl -p"),

                    # Verify new value
                    exaMockCommand("sysctl -n vm.nr_hugepages.*", aStdout="25600"),
                    exaMockCommand("cat /etc/sysctl.conf.*", aRc=1),
                    exaMockCommand("/bin/ls /etc/sysctl.d/", aStdout="999_new_config.conf"),
                    exaMockCommand("cat .*999_new_config.conf", aStdout="vm.nr_hugepages = 25600"),
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("imageinfo | grep 'Node type:'"),
                    exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n"),
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'"),
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),

                    exaMockCommand("xm list", aStdout=""),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=""),
                ],
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "gb_memory": 100
        }

        #Execute the clucontrol function
        _exascale = ebCluExaScale(None)
        if _exascale.mGetCluCtrl() is None:
            _exascale.mSetCluCtrl(self.mGetClubox())
        _exascale.mConfigureHugePage(_options)



if __name__ == '__main__':
    unittest.main(warnings='ignore')


# end of file
