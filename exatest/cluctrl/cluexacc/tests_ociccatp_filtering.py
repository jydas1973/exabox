"""

 $Header: 

 Copyright (c) 2018, 2023, Oracle and/or its affiliates.

 NAME:
      tests_ociccatpfiltering.py - Unitest for ATP EXACC EB/IPtables

 DESCRIPTION:
      Run tests for ATP EXACC

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       aararora 08/18/23 - Bug 35685169: Unittest fixes
       aararora 04/10/23 - Unit test correction to take ATP prefix instead of
                           EXACC_ATP_.
       jesandov 03/31/23 - 35188255 - Add prefix to ebtables in ExaCC ATP

        vgerard     03/22/20 - Creation
"""

import unittest
import os
import sys
import time
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
from exabox.ovm.cluexaccatp_filtering import ebExaCCAtpFiltering
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext


def override_config(*tags):
    """
    Decorator to specify exabox.conf params for a test class or method.
    """
    def decorator(obj):
        setattr(obj, 'config', tags)
        return obj
    return decorator

class ebTestOciCCAtpPayload(ebTestClucontrol):

    @classmethod
    def setUpClass(self):

        _resources = "exabox/exatest/cluctrl/cluexacc/resources/exaccIB/"
        super().setUpClass(aResourceFolder=_resources)

    def setUp(self):

        self.maxDiff = 4000

        _setup = os.path.join(self.mGetPath(), "ocpsSetup.json")
        self.mGetClubox().mGetCtx().mSetConfigOption('ocps_jsonpath', _setup)

        method = getattr(self,self._testMethodName)
        config_decorator = getattr(method,'config', {})
        if config_decorator: #[0] to get first tuple elem
            for _configKey, _configValue in list(config_decorator[0].items()):
                self.mGetClubox().mGetCtx().mSetConfigOption(_configKey, _configValue)


    @patch('exabox.utils.node.exaBoxNode.mExecuteCmd')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=1)
    def test_EbTablesHalfRackNoServices(self, mock_cmd, mock_rc):
        _macData = {"scaqak03dv0102":{"admin_mac":"00:16:3e:e1:86:9d"},
                    "scaqak03dv0202":{"admin_mac":"00:16:3e:9d:7d:5b"},
                    "scaqak03dv0302":{"admin_mac":"00:16:3e:57:a9:90"},
                    "scaqak03dv0402":{"admin_mac":"00:16:3e:14:7e:9e"}}

        _filterClass = ebExaCCAtpFiltering({},aTestMode=True)
        _filterClass.mSetDom0MacData(_macData)
        _node = exaBoxNode(get_gcontext())
        _ebt_commands_vm1 = _filterClass.mProcessDom0(_node, "scaqak03dv0102")
        _ebt_commands_vm1_expected = [
            'ebtables -F INPUT',
            'ebtables -F OUTPUT',
            'ebtables -D FORWARD -d 00:16:3e:e1:86:9d -i eth0 -j ATP00163EE1869D_IN',
            'ebtables -D FORWARD -s 00:16:3e:e1:86:9d -j ATP00163EE1869D_OUT',
            'ebtables -X ATP00163EE1869D_IN',
            'ebtables -X ATP00163EE1869D_IN_FROM_CPS',
            'ebtables -X ATP00163EE1869D_OUT',
            'ebtables -X ATP00163EE1869D_OUT_TO_CPS',
            'ebtables -A INPUT -s 00:16:3e:e1:86:9d -j DROP',
            'ebtables -A OUTPUT -d 00:16:3e:e1:86:9d -j DROP',
            'ebtables -N ATP00163EE1869D_IN -P DROP',
            'ebtables -N ATP00163EE1869D_IN_FROM_CPS -P DROP',
            'ebtables -N ATP00163EE1869D_OUT -P DROP',
            'ebtables -N ATP00163EE1869D_OUT_TO_CPS -P DROP',
            'ebtables -A FORWARD -d 00:16:3e:e1:86:9d -i eth0 -j ATP00163EE1869D_IN',
            'ebtables -A FORWARD -s 00:16:3e:e1:86:9d -j ATP00163EE1869D_OUT',
            'ebtables -A ATP00163EE1869D_IN -p ARP -j ACCEPT',
            'ebtables -A ATP00163EE1869D_OUT -p ARP -j ACCEPT',
            'ebtables -A ATP00163EE1869D_IN -s 00:16:3e:14:7e:9e -j ACCEPT',
            'ebtables -A ATP00163EE1869D_OUT -d 00:16:3e:14:7e:9e -j ACCEPT',
            'ebtables -A ATP00163EE1869D_IN -s 00:16:3e:57:a9:90 -j ACCEPT',
            'ebtables -A ATP00163EE1869D_OUT -d 00:16:3e:57:a9:90 -j ACCEPT',
            'ebtables -A ATP00163EE1869D_IN -s 00:16:3e:9d:7d:5b -j ACCEPT',
            'ebtables -A ATP00163EE1869D_OUT -d 00:16:3e:9d:7d:5b -j ACCEPT',
            'ebtables -A ATP00163EE1869D_IN -p IPv4 --ip-src 10.31.20.174 -j ATP00163EE1869D_IN_FROM_CPS',
            'ebtables -A ATP00163EE1869D_OUT -p IPv4 --ip-dst 10.31.20.174 -j ATP00163EE1869D_OUT_TO_CPS',
            'ebtables -A ATP00163EE1869D_IN -p IPv4 --ip-src 10.31.20.175 -j ATP00163EE1869D_IN_FROM_CPS',
            'ebtables -A ATP00163EE1869D_OUT -p IPv4 --ip-dst 10.31.20.175 -j ATP00163EE1869D_OUT_TO_CPS',
            'ebtables -A ATP00163EE1869D_IN_FROM_CPS -p IPv4 --ip-proto icmp -j ACCEPT',
            'ebtables -A ATP00163EE1869D_IN_FROM_CPS -p IPv4 --ip-proto tcp --ip-dport 22 -j ACCEPT',
            'ebtables -A ATP00163EE1869D_OUT_TO_CPS -p IPv4 --ip-proto icmp -j ACCEPT',
            'ebtables -A ATP00163EE1869D_OUT_TO_CPS -p IPv4 --ip-proto tcp --ip-sport 22 -j ACCEPT'
        ]
        self.assertEqual(_ebt_commands_vm1_expected, _ebt_commands_vm1)

    @patch('exabox.utils.node.exaBoxNode.mExecuteCmd')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=1)
    @override_config({"nat_fileserver_ip":"10.10.0.4",
                      "nat_fileserver_port" : "2080"})
    def test_EbTablesHalfRackServices(self, mock_cmd, mock_rc):
        _macData = {"scaqak03dv0102":{"admin_mac":"00:16:3e:e1:86:9d"},
                    "scaqak03dv0202":{"admin_mac":"00:16:3e:9d:7d:5b"},
                    "scaqak03dv0302":{"admin_mac":"00:16:3e:57:a9:90"},
                    "scaqak03dv0402":{"admin_mac":"00:16:3e:14:7e:9e"}}

        _filterClass = ebExaCCAtpFiltering({},aTestMode=True)
        _filterClass.mSetDom0MacData(_macData)
        _node = exaBoxNode(get_gcontext())
        _ebt_commands_vm2 = _filterClass.mProcessDom0(_node, "scaqak03dv0202")
        _ebt_commands_vm2_expected = [
            'ebtables -F INPUT',
            'ebtables -F OUTPUT',
            'ebtables -D FORWARD -d 00:16:3e:9d:7d:5b -i eth0 -j ATP00163E9D7D5B_IN',
            'ebtables -D FORWARD -s 00:16:3e:9d:7d:5b -j ATP00163E9D7D5B_OUT',
            'ebtables -X ATP00163E9D7D5B_IN',
            'ebtables -X ATP00163E9D7D5B_IN_FROM_CPS',
            'ebtables -X ATP00163E9D7D5B_OUT',
            'ebtables -X ATP00163E9D7D5B_OUT_TO_CPS',
            'ebtables -A INPUT -s 00:16:3e:9d:7d:5b -j DROP',
            'ebtables -A OUTPUT -d 00:16:3e:9d:7d:5b -j DROP',
            'ebtables -N ATP00163E9D7D5B_IN -P DROP',
            'ebtables -N ATP00163E9D7D5B_IN_FROM_CPS -P DROP',
            'ebtables -N ATP00163E9D7D5B_OUT -P DROP',
            'ebtables -N ATP00163E9D7D5B_OUT_TO_CPS -P DROP',
            'ebtables -A FORWARD -d 00:16:3e:9d:7d:5b -i eth0 -j ATP00163E9D7D5B_IN',
            'ebtables -A FORWARD -s 00:16:3e:9d:7d:5b -j ATP00163E9D7D5B_OUT',
            'ebtables -A ATP00163E9D7D5B_IN -p ARP -j ACCEPT',
            'ebtables -A ATP00163E9D7D5B_OUT -p ARP -j ACCEPT',
            'ebtables -A ATP00163E9D7D5B_IN -s 00:16:3e:14:7e:9e -j ACCEPT',
            'ebtables -A ATP00163E9D7D5B_OUT -d 00:16:3e:14:7e:9e -j ACCEPT',
            'ebtables -A ATP00163E9D7D5B_IN -s 00:16:3e:57:a9:90 -j ACCEPT',
            'ebtables -A ATP00163E9D7D5B_OUT -d 00:16:3e:57:a9:90 -j ACCEPT',
            'ebtables -A ATP00163E9D7D5B_IN -s 00:16:3e:e1:86:9d -j ACCEPT',
            'ebtables -A ATP00163E9D7D5B_OUT -d 00:16:3e:e1:86:9d -j ACCEPT',
            'ebtables -A ATP00163E9D7D5B_IN -p IPv4 --ip-src 10.31.20.174 -j ATP00163E9D7D5B_IN_FROM_CPS',
            'ebtables -A ATP00163E9D7D5B_OUT -p IPv4 --ip-dst 10.31.20.174 -j ATP00163E9D7D5B_OUT_TO_CPS',
            'ebtables -A ATP00163E9D7D5B_IN -p IPv4 --ip-src 10.31.20.175 -j ATP00163E9D7D5B_IN_FROM_CPS',
            'ebtables -A ATP00163E9D7D5B_OUT -p IPv4 --ip-dst 10.31.20.175 -j ATP00163E9D7D5B_OUT_TO_CPS',
            'ebtables -A ATP00163E9D7D5B_IN_FROM_CPS -p IPv4 --ip-proto icmp -j ACCEPT',
            'ebtables -A ATP00163E9D7D5B_IN_FROM_CPS -p IPv4 --ip-proto tcp --ip-dport 22 -j ACCEPT',
            'ebtables -A ATP00163E9D7D5B_OUT_TO_CPS -p IPv4 --ip-proto icmp -j ACCEPT',
            'ebtables -A ATP00163E9D7D5B_OUT_TO_CPS -p IPv4 --ip-proto tcp --ip-sport 22 -j ACCEPT',
            'ebtables -A ATP00163E9D7D5B_IN -p IPv4 --ip-src 10.10.0.4 --ip-proto tcp --ip-sport 2080 -j ACCEPT',
            'ebtables -A ATP00163E9D7D5B_OUT -p IPv4 --ip-dst 10.10.0.4 --ip-proto tcp --ip-dport 2080 -j ACCEPT'
        ]
        self.assertEqual(_ebt_commands_vm2_expected, _ebt_commands_vm2)
        self.assertRaises(ValueError,_filterClass.mProcessDom0, None, "DONOTEXISTS")

    @patch('exabox.utils.node.exaBoxNode.mExecuteCmd')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=1)
    def test_EbTablesQuarterRack(self, mock_exec, mock_rc):
        _macData = {"scaqak03dv0102":{"admin_mac":"00:16:3e:e1:86:9d"},
                    "scaqak03dv0202":{"admin_mac":"00:16:3e:9d:7d:5b"}}

        _filterClass = ebExaCCAtpFiltering({},aTestMode=True)
        _filterClass.mSetDom0MacData(_macData)
        _node = exaBoxNode(get_gcontext())
        _ebt_commands_vm1 = _filterClass.mProcessDom0(_node, "scaqak03dv0102")

        _result = ['ebtables -F INPUT', \
            'ebtables -F OUTPUT', \
            'ebtables -D FORWARD -d 00:16:3e:e1:86:9d -i eth0 -j ATP00163EE1869D_IN', \
            'ebtables -D FORWARD -s 00:16:3e:e1:86:9d -j ATP00163EE1869D_OUT', \
            'ebtables -X ATP00163EE1869D_IN', \
            'ebtables -X ATP00163EE1869D_IN_FROM_CPS', \
            'ebtables -X ATP00163EE1869D_OUT', \
            'ebtables -X ATP00163EE1869D_OUT_TO_CPS', \
            'ebtables -A INPUT -s 00:16:3e:e1:86:9d -j DROP', \
            'ebtables -A OUTPUT -d 00:16:3e:e1:86:9d -j DROP', \
            'ebtables -N ATP00163EE1869D_IN -P DROP', \
            'ebtables -N ATP00163EE1869D_IN_FROM_CPS -P DROP', \
            'ebtables -N ATP00163EE1869D_OUT -P DROP', \
            'ebtables -N ATP00163EE1869D_OUT_TO_CPS -P DROP', \
            'ebtables -A FORWARD -d 00:16:3e:e1:86:9d -i eth0 -j ATP00163EE1869D_IN', \
            'ebtables -A FORWARD -s 00:16:3e:e1:86:9d -j ATP00163EE1869D_OUT', \
            'ebtables -A ATP00163EE1869D_IN -p ARP -j ACCEPT', \
            'ebtables -A ATP00163EE1869D_OUT -p ARP -j ACCEPT', \
            'ebtables -A ATP00163EE1869D_IN -s 00:16:3e:9d:7d:5b -j ACCEPT', \
            'ebtables -A ATP00163EE1869D_OUT -d 00:16:3e:9d:7d:5b -j ACCEPT', \
            'ebtables -A ATP00163EE1869D_IN -p IPv4 --ip-src 10.31.20.174 -j ATP00163EE1869D_IN_FROM_CPS', \
            'ebtables -A ATP00163EE1869D_OUT -p IPv4 --ip-dst 10.31.20.174 -j ATP00163EE1869D_OUT_TO_CPS', \
            'ebtables -A ATP00163EE1869D_IN -p IPv4 --ip-src 10.31.20.175 -j ATP00163EE1869D_IN_FROM_CPS', \
            'ebtables -A ATP00163EE1869D_OUT -p IPv4 --ip-dst 10.31.20.175 -j ATP00163EE1869D_OUT_TO_CPS', \
            'ebtables -A ATP00163EE1869D_IN_FROM_CPS -p IPv4 --ip-proto icmp -j ACCEPT', \
            'ebtables -A ATP00163EE1869D_IN_FROM_CPS -p IPv4 --ip-proto tcp --ip-dport 22 -j ACCEPT', \
            'ebtables -A ATP00163EE1869D_OUT_TO_CPS -p IPv4 --ip-proto icmp -j ACCEPT', \
            'ebtables -A ATP00163EE1869D_OUT_TO_CPS -p IPv4 --ip-proto tcp --ip-sport 22 -j ACCEPT', \
            'ebtables -A ATP00163EE1869D_IN -p IPv4 --ip-src 10.10.0.4 --ip-proto tcp --ip-sport 2080 -j ACCEPT',
            'ebtables -A ATP00163EE1869D_OUT -p IPv4 --ip-dst 10.10.0.4 --ip-proto tcp --ip-dport 2080 -j ACCEPT'
        ]

        self.assertEqual(_result, _ebt_commands_vm1)

if __name__ == '__main__':
    unittest.main()

