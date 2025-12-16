"""

 $Header:

 Copyright (c) 2018, 2021, Oracle and/or its affiliates. 

 NAME:
      tests_exaccIB.py - Unitest for IB ExaCC

 DESCRIPTION:
      Tests for IB ExaCC

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
        vgerard    09/06/18 - Creation of the file for exacloud unit test
"""

import os
import json
import unittest

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

class ebTestIptablesNat(ebTestClucontrol):
    # TODO: Assign to Owner

    @classmethod
    def setUpClass(self):
        _resources = 'exabox/exatest/cluctrl/iptables/resources/iptablesnat/'
        super().setUpClass(aResourceFolder=_resources)

# EXPECTATIONS _-------------------------------------------
    def mCheckDefaultIptables(self, aDefault):

        _default = ['-P INPUT ACCEPT', '-P FORWARD DROP', '-P OUTPUT ACCEPT',
                    '-A INPUT -i lo -j ACCEPT', '-A INPUT -i vmeth0 -j ACCEPT',
                    '-A INPUT -j DROP']

        #Single check for all method since they are default:)
        self.assertEqual(_default, aDefault)

    def mCheckStandardFwdRulesIptables(self, aVMNumber, aRules, aNatSet=[]):

        _standard = ['-A FORWARD -o vmeth{} -p tcp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT',
                     '-A FORWARD -o vmeth{} -p icmp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT',
                     '-A FORWARD -i vmeth{} -p tcp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT',
                     '-A FORWARD -i vmeth{} -p icmp -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT',
                     '-A FORWARD -o vmeth{} -p tcp -m tcp --dport 22 -j ACCEPT',
                     '-A FORWARD -o vmeth{} -p icmp -m icmp --icmp-type 8 -j ACCEPT']

        _ip_fwd_rules = []
        _vmeth_range = list(range(100,100+aVMNumber)) + list(range(200,200+aVMNumber))

        for i in _vmeth_range:
            _ip_fwd_rules += map(lambda x:x.format(i), _standard)

            #Nat set is a list of tuple [(ServiceIP,ServicePort),(serviceIP2,ServicePort)]
            for ip, port in aNatSet:
                _ip_fwd_rules.append('-A FORWARD -d {} -i vmeth{} -p tcp -m tcp --dport {} -j ACCEPT'
                                     .format(ip, i, port))

        _ip_fwd_rules += ['-A OUTPUT -o lo -j ACCEPT', '-A OUTPUT -o vmeth0 -j ACCEPT']

        self.assertEqual(set(aRules),set(_ip_fwd_rules))

    def mCheckStandardNATRulesIptables(self, aVMNumber, aNatRules, aNatSet=[]):
        _ip_NAT_rules = []
        _vmeth_range = list(range(100,100+aVMNumber)) + list(range(200,200+aVMNumber))
        for i in _vmeth_range:
            #Nat set is a list of tuple [(ServiceIP,ServicePort),(serviceIP2,ServicePort)]
            for ip,port in aNatSet:
                _ip_NAT_rules.append('-A PREROUTING -i vmeth{} -p tcp -m tcp --dport {} -j DNAT --to-destination {}'
                                     .format(i, port, ip))

        _ip_NAT_rules.append('-A POSTROUTING -o vmeth0 -j MASQUERADE')
        self.assertEqual(set(aNatRules),set(_ip_NAT_rules))

    # END OF EXPECTATIONS< START OF TEST

    def test_GetSINGLEVMNatInfoWithoutFwdProxyNorFileserver(self):
        return True

        #EXACC Specific
        _setup = os.path.join(self.mGetPath(), "ocpsSetup.json")
        self.mGetClubox().mGetCtx().mSetConfigOption('ocps_jsonpath', _setup)

        self.assertFalse(self.mGetClubox().mGetOciExaCCServicesSetup())
        default, rules, nat, natports = self.mGetClubox().mSetupNATIptablesOnDom0v2(aMode=True)
        self.mCheckDefaultIptables(default)
        self.mCheckStandardFwdRulesIptables(1,rules)
        self.assertFalse(nat)
        self.assertFalse(natports)

    def test_GetNatInfoSINGLEVMWithoutFwdProxy(self):
        return True

        #EXACC Specific
        _setup = os.path.join(self.mGetPath(), "ocpsSetup.json")
        self.mGetClubox().mGetCtx().mSetConfigOption('ocps_jsonpath', _setup)
        self.mGetClubox().mGetCtx().mSetConfigOption('nat_fileserver_ip', "10.10.10.10")
        self.mGetClubox().mGetCtx().mSetConfigOption('nat_fileserver_port', "2081")

        self.assertEqual({'fileserver': {'ip': '10.10.10.10', 'port': '2081'}},
                           self.mGetClubox().mGetOciExaCCServicesSetup())
        default, rules, nat, natports = self.mGetClubox().mSetupNATIptablesOnDom0v2(aMode=True)
        self.mCheckDefaultIptables(default)
        self.mCheckStandardFwdRulesIptables(1,rules,[("10.10.10.10","2081")])
        self.mCheckStandardNATRulesIptables(1,nat,[("10.10.10.10","2081")])
        self.assertEqual(set(["2081"]),set(natports))

    def test_GetNatInfoSINGLEVMWITHPROXY(self):
        return True

        #EXACC Specific
        _setup = os.path.join(self.mGetPath(), "ocpsSetup_fwd_proxy.json")
        self.mGetClubox().mGetCtx().mSetConfigOption('ocps_jsonpath', _setup)
        self.mGetClubox().mGetCtx().mSetConfigOption('nat_fileserver_ip', "10.10.10.10")
        self.mGetClubox().mGetCtx().mSetConfigOption('nat_fileserver_port', "2081")

        self.assertEqual({'forwardproxy': {'ip': '20.20.20.20', 'port': '3081'},
                           'fileserver': {'ip': '10.10.10.10', 'port': '2081'}},
                           self.mGetClubox().mGetOciExaCCServicesSetup())

        default, rules, nat, natports = self.mGetClubox().mSetupNATIptablesOnDom0v2(aMode=True)
        self.mCheckDefaultIptables(default)
        self.mCheckStandardFwdRulesIptables(1,rules,[("10.10.10.10","2081"),("20.20.20.20","3081")])
        self.mCheckStandardNATRulesIptables(1,nat,[("10.10.10.10","2081"),("20.20.20.20","3081")])
        self.assertEqual(set(["2081","3081"]),set(natports))

    def test_GetNatInfoMULTIVMWITHPROXY(self):
        return True

        #EXACC Specific
        _setup = os.path.join(self.mGetPath(), "ocpsSetup_fwd_proxy.json")
        self.mGetClubox().mGetCtx().mSetConfigOption('ocps_jsonpath', _setup)
        self.mGetClubox().mGetCtx().mSetConfigOption('nat_fileserver_ip', "10.10.10.10")
        self.mGetClubox().mGetCtx().mSetConfigOption('nat_fileserver_port', "2081")

        self.assertEqual({'forwardproxy': {'ip': '20.20.20.20', 'port': '3081'},
                           'fileserver': {'ip': '10.10.10.10', 'port': '2081'}},
                           self.mGetClubox().mGetOciExaCCServicesSetup())

        # FORCE SHARED ENV BY UNMANGLING
        self.mGetClubox().mSetSharedEnvironment(True)

        default, rules, nat, natports = self.mGetClubox().mSetupNATIptablesOnDom0v2(aMode=True)
        self.mCheckDefaultIptables(default)
        self.mCheckStandardFwdRulesIptables(8,rules,[("10.10.10.10","2081"),("20.20.20.20","3081")])
        self.mCheckStandardNATRulesIptables(8,nat,[("10.10.10.10","2081"),("20.20.20.20","3081")])
        self.assertEqual(set(["2081","3081"]),set(natports))

    def test_GetNatInfoMULTIVMWITHPROXYforcing12VMs(self):
        return True

        #EXACC Specific
        _setup = os.path.join(self.mGetPath(), "ocpsSetup_fwd_proxy.json")
        self.mGetClubox().mGetCtx().mSetConfigOption('ocps_jsonpath', _setup)
        self.mGetClubox().mGetCtx().mSetConfigOption('nat_fileserver_ip', "10.10.10.10")
        self.mGetClubox().mGetCtx().mSetConfigOption('nat_fileserver_port', "2081")
        self.mGetClubox().mGetCtx().mSetConfigOption('iptables_nat_rules_range', "12")

        self.assertEqual({'forwardproxy': {'ip': '20.20.20.20', 'port': '3081'},
                           'fileserver': {'ip': '10.10.10.10', 'port': '2081'}},
                           self.mGetClubox().mGetOciExaCCServicesSetup())
        # FORCE SHARED ENV BY UNMANGLING
        self.mGetClubox().mSetSharedEnvironment(True)

        default, rules, nat, natports = self.mGetClubox().mSetupNATIptablesOnDom0v2(aMode=True)
        self.mCheckDefaultIptables(default)
        self.mCheckStandardFwdRulesIptables(12,rules,[("10.10.10.10","2081"),("20.20.20.20","3081")])
        self.mCheckStandardNATRulesIptables(12,nat,[("10.10.10.10","2081"),("20.20.20.20","3081")])
        #print(nat)  <- to debug
        self.assertEqual(set(["2081","3081"]),set(natports))



if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end of file
