#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/iptables/tests_iptablesatp.py /main/7 2023/01/24 02:57:16 hnvenkat Exp $
#
# tests_iptablesatp.py
#
# Copyright (c) 2020, 2023, Oracle and/or its affiliates. 
#
#    NAME
#      tests_iptablesatp.py - Test the XML generation for the iptables rules.
#
#    DESCRIPTION
#      iptables rules XML generation tests for ATP KVM environments.
#
#    NOTES
#      None.
#
#    MODIFIED   (MM/DD/YY)
#    hnvenkat    01/20/23 - don't invoke ATP tests
#    naps        03/07/22 - remove virsh layer dependency.
#    ffrrodri    10/07/21 - Bug 33229330: Added test to validate flipped
#                           interfaces.
#    scoral      11/03/20 - Creation
#


import unittest
from exabox.ovm.cluiptablesroce import ebIpTablesRoCE, EB_IPTABLES_ATP_IMPLICIT_RULES
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
import json
import os
import tempfile
import xml.etree.ElementTree as etree


def eq_Element(et1: etree.Element, et2: etree.Element) -> bool:
    """
    Recursively compares if two xml Elements are equal.
    """
    return et1.tag == et2.tag and \
           et1.attrib == et2.attrib and \
           len(et1) == len(et2) and \
           all(eq_Element(ch1, ch2) for ch1, ch2 in zip(list(et1), list(et2)))


class ebTestIptablesATP(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self._path = 'exabox/exatest/cluctrl/iptables/resources/iptablesatp/'
        self._payload_path = self._path + 'payload.json'
        self._expected_client_path = self._path + 'expected_client.xml'
        self._expected_backup_path = self._path + 'expected_backup.xml'

    def xml_generation_tests(self, iftype: str, expected_result_path: str):
        # Read & parse payload and implicit rules

        with open(self._payload_path) as fd:
            _payload = json.load(fd)

        _parse = lambda payload, iftype: list(ebIpTablesRoCE.mReadIpTablesDictATPPayload(payload, iftype))
        _rules = _parse(EB_IPTABLES_ATP_IMPLICIT_RULES, iftype) + _parse(_payload, iftype)

        # Generate rules xmls

        _generated_xml_fd, _generated_xml_path = tempfile.mkstemp(suffix='.xml', prefix='nwfiltr-schema.')
        with os.fdopen(_generated_xml_fd, 'w') as fd:
            fd.write('<filter name="my_filter" />')

        ebIpTablesRoCE.mAddRulesToNetFilterSchema(_generated_xml_path, *_rules)

        # Check if generated xmls are correct

        _generated_rules = etree.parse(_generated_xml_path).getroot().findall('rule')
        _expected_rules = etree.parse(expected_result_path).getroot().findall('rule')
        self.assertEqual(len(_generated_rules), len(_expected_rules))
        self.assertTrue(all(eq_Element(g_rule, e_rule) for g_rule, e_rule in zip(_generated_rules, _expected_rules)))

        # Removing rules from the generated xmls & check they end up empty

        ebIpTablesRoCE.mRemoveRulesFromNetFilterSchema(_generated_xml_path, *_rules)
        self.assertFalse(etree.parse(_generated_xml_path).getroot().findall('rule'))

        # Free resources

        os.unlink(_generated_xml_path)

    #def test_client_rules_xml_generation(self):
    #    self.xml_generation_tests('client', self._expected_client_path)

    #def test_backup_rules_xml_generation(self):
    #    self.xml_generation_tests('backup', self._expected_backup_path)


class Interfaces(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        _resources = 'exabox/exatest/cluctrl/iptables/resources/iptablesnat/'
        super().setUpClass(aResourceFolder=_resources)

    def generic_alias_interfaces_test(self, aExpectedResult, aInterfacesTypes, aXML):
        _generated_xml_fd, _generated_xml_path = tempfile.mkstemp(suffix='.xml', prefix='vm-schema.')
        with os.fdopen(_generated_xml_fd, 'w') as fd:
            fd.write(aXML)

        _interfaces_alias_dict = ebIpTablesRoCE._mGetInterfacesAlias(_generated_xml_path, aInterfacesTypes)
        os.unlink(_generated_xml_path)

        self.assertDictEqual(aExpectedResult, _interfaces_alias_dict)

    def test_validate_ordered_alias_interfaces(self):
        _xml_contents = ("<domain type='kvm' id='6'><devices>"
                         "<interface type='bridge'>"
                           "<source bridge='vmbondeth0.31'/>"
                           "<alias name='net0'/>"
                         "</interface><interface type='bridge'>"
                           "<source bridge='vmbondeth0.32'/>"
                           "<alias name='net1'/>"
                         "</interface></devices></domain>")

        _interfaces_types_dict = {
            'vmbondeth0.31': 'client',
            'vmbondeth0.32': 'backup'
        }

        _interfaces_alias_dict_expected = {
            'client': 'net0',
            'backup': 'net1'
        }

        self.generic_alias_interfaces_test(_interfaces_alias_dict_expected, _interfaces_types_dict, _xml_contents)

    def test_validate_flipped_alias_interfaces(self):
        _xml_contents = ("<domain type='kvm' id='6'><devices>"
                         "<interface type='bridge'>"
                           "<source bridge='vmbondeth0'/>"
                           "<alias name='net1'/>"
                         "</interface><interface type='bridge'>"
                           "<source bridge='vmbondeth0.1'/>"
                           "<alias name='net0'/>"
                         "</interface></devices></domain>")

        _interfaces_types_dict = {
            'vmbondeth0': 'client',
            'vmbondeth0.1': 'backup'
        }

        _interfaces_alias_dict_expected = {
            'client': 'net1',
            'backup': 'net0'
        }

        self.generic_alias_interfaces_test(_interfaces_alias_dict_expected, _interfaces_types_dict, _xml_contents)

    def test_validate_missing_alias_interfaces(self):
        _xml_contents = ("<domain type='kvm' id='6'><devices>"
                         "<interface type='bridge'>"
                           "<source bridge='vmbondeth0'/>"
                         "</interface><interface type='bridge'>"
                           "<source bridge='vmbondeth0.1'/>"
                         "</interface></devices></domain>")

        _interfaces_types_dict = {
            'vmbondeth0': 'client',
            'vmbondeth0.1': 'backup'
        }

        _interfaces_alias_dict_expected = {
            'client': 'net0',
            'backup': 'net1'
        }

        self.generic_alias_interfaces_test(_interfaces_alias_dict_expected, _interfaces_types_dict, _xml_contents)


if __name__ == '__main__':
    unittest.main()
