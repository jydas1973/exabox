#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_hostaccesscontrol.py /main/1 2025/02/07 17:53:57 jfsaldan Exp $
#
# tests_hostaccesscontrol.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_hostaccesscontrol.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    11/27/24 - Enh 37327500 - EXADB-XS: EXACLOUD - OPEN HOST
#                           ACCESS CONTROL FOR ROCE NETWORK IN TARGET HOST
#                           DURING CREATE SERVICE AND ADD COMPUTE FLOWS
#    jfsaldan    11/27/24 - Creation
#

import unittest
from unittest.mock import Mock, patch
from unittest.mock import MagicMock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.MockCommand import exaMockCommand

from exabox.ovm.cluhostaccesscontrol import addRoceNetworkHostAccessControl

class ebTestHostAccessControl(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)
        self.maxDiff = None

    def test_addRoceNetworkHostAccessControlPerHost(self):
        """
        """

        _status_before = (
            "[2024-11-27 22:29:56 +0000] [INFO] [IMG-SEC-0106] User-origin access rules :\n"
            "### DO NOT REMOVE THIS FILE - REQUIRED FOR SYSTEM ACCESS - DO NOT REMOVE THIS FILE ###\n"
            "# EXADATA ACCESS CONTROL\n"
            "# user rules\n"
            "+ : root : console tty1 ttyS0 hvc0 localhost ip6-localhost 10.0.9.128/25 10.0.1.32/28\n"
            "+ : secscan : console tty1 ttyS0 hvc0 localhost ip6-localhost 10.0.9.128/25 10.0.1.32/28\n"
            "- : ALL  : ALL\n"
        )
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/opt/oracle.cellos/host_access_control access --status", aRc=0,
                        aStdout=_status_before),
                    exaMockCommand("/opt/oracle.cellos/host_access_control access --add --user=root --origins='console,tty1,ttyS0,hvc0,localhost,ip6-localhost,10.0.9.128/25,10.0.1.32/28,100.105.0.0/16'", aRc=0,
                        aStdout="[2024-11-27 21:59:55 +0000] [INFO] [IMG-SEC-0104] Added user-origin access rule for user root\n"),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _dom0_a = _ebox.mReturnDom0DomUPair()[0][0]
        _dom0_b = _ebox.mReturnDom0DomUPair()[1][0]

        _options = self.mGetPayload()
        _options.jsonconf["roce_information"] = {
            _dom0_a : {
                "stre0_ip": "100.105.74.24",
                "stre1_ip": "100.105.74.25",
                "subnet_mask": "255.255.0.0",
                "vlan_id": "3999"
            },
            _dom0_b : {
                "stre0_ip": "100.105.74.26",
                "stre1_ip": "100.105.74.27",
                "subnet_mask": "255.255.0.0",
                "vlan_id": "3999"
            }
        }

        self.assertEqual(0, addRoceNetworkHostAccessControl(_options))

    def test_addRoceNetworkHostAccessControlPerHost_skip(self):
        """
        """


        _ebox = self.mGetClubox()
        _dom0_a = _ebox.mReturnDom0DomUPair()[0][0]
        _dom0_b = _ebox.mReturnDom0DomUPair()[1][0]

        _options = self.mGetPayload()
        _options.jsonconf["roce_information"] = {
            _dom0_a : {
                "stre0_ip": "100.105.74.24",
                "stre1_ip": "100.105.74.25",
                "subnet_mask": "255.255.0.0",
                "vlan_id": "3999"
            },
            _dom0_b : {
                "stre0_ip": "100.105.74.26",
                "stre1_ip": "100.105.74.27",
                "subnet_mask": "255.255.0.0",
                "vlan_id": "3999"
            }
        }

        self.mGetContext().mSetConfigOption('skip_roce_access_control_setup', 'true')
        self.assertEqual(1, addRoceNetworkHostAccessControl(_options))

if __name__ == '__main__':
    unittest.main()

