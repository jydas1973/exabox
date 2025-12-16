#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/iptables/tests_iptableskvm.py /main/10 2023/05/09 16:47:23 scoral Exp $
#
# tests_iptableskvm.py
#
# Copyright (c) 2021, 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_iptableskvm.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    01/31/23 - Bug 35032256: Created a tmp copy of
#                           expected_client.xml for testing
#                           mInsertRemoveRulesFromNetFilterSchema()
#    hnvenkat    01/30/23 - Modified json_rules to reflect new ATP iptables
#    naps        01/12/23 - Adding UT for vm reboot.
#    scoral      10/20/22 - XbranchMerge scoral_bug-34701313 from
#                           st_ecs_22.3.1.0.0
#    naps        03/07/22 - remove virsh layer dependency.
#    ffrrodri    12/08/21 - Creation
#
import os
import shutil
import unittest
import xml.etree.cElementTree as etree
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.cluiptablesroce import ebIpTablesRoCE
from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from unittest.mock import patch

class IPTablesCleanUp(ebTestClucontrol):
    net_filter_name = "vm-net0-exabm.xml"

    json_rules = {
        'atp': {
            'whitelist': {
                'client': {
                    'protocol': {
                        'all': [
                            '@@out',
                            '@@in'
                        ]
                    }
                }
            }
        }
    }

    @classmethod
    def setUpClass(self):
        super().setUpClass(False, False, aResourceFolder='exabox/exatest/cluctrl/iptables/resources/iptablesnat/')
        self._atp_path = 'exabox/exatest/cluctrl/iptables/resources/iptablesatp/'

    def test_exist_net_filter(self):
        _dom0, _ = self.mGetClubox().mReturnDom0DomUPair()[0]

        _commands = [
            exaMockCommand(f"virsh nwfilter-list | awk '{{ print $2 }}' | grep -c {self.net_filter_name} || true",
                           aStdout="1",
                           aRc=0)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        return self.assertEqual(True, ebIpTablesRoCE.mExistsNetFilter(_dom0, self.net_filter_name))

    def test_create_net_filter(self):
        _dom0, _ = self.mGetClubox().mReturnDom0DomUPair()[0]

        tmp_file = "/tmp/tmp.FRlsuaKzHr.xml\n"

        _commands_exist_method = [
            exaMockCommand(f"virsh nwfilter-list | awk '{{ print $2 }}' | grep -c {self.net_filter_name} || true",
                           aRc=0,
                           aStdout="0")

        ]

        _commands = [
            exaMockCommand("mktemp*", aRc=0, aStdout=tmp_file),
            exaMockCommand(f"echo*", aRc=0),
            exaMockCommand(f"virsh*", aRc=0)

        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands_exist_method,
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        ebIpTablesRoCE.mCreateNetFilter(_dom0, self.net_filter_name)

        return self.assertTrue(True, "Method mCreateNetFilter executed successfully")

    def test_remove_net_filter(self):
        _dom0, _ = self.mGetClubox().mReturnDom0DomUPair()[0]

        _commands = [
            exaMockCommand(f"virsh*", aRc=0)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        ebIpTablesRoCE.mRemoveNetFilter(_dom0, self.net_filter_name)

        return self.assertTrue(True, "Method mRemoveNetFilter executed successfully")

    def test_read_iptables_dict(self):

        ebIpTablesRoCE.mReadIpTablesDictATPPayload(self.json_rules, "client")

        return self.assertTrue(True, "Method mReadIpTablesDictATPPayload executed successfully")

    def test_prevm_setup_iptables(self):
        _commands_general = [
            exaMockCommand("iptables -D*", aRc=0),
            exaMockCommand("cp.*", aRc=0),
            exaMockCommand("iptables.*save", aRc=0)
        ]

        _commands_nested = [
            exaMockCommand("iptables -S*", aRc=0, aStdout="0\n"),
            exaMockCommand("iptables -S*", aRc=0, aStdout="0\n"),
            exaMockCommand("cp.*", aRc=0),
            exaMockCommand("iptables.*save", aRc=0),
            exaMockCommand("sed -i*", aRc=0)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands_nested,
                _commands_nested,
                _commands_nested,
                _commands_nested,
                _commands_general,
                _commands_general
            ]
        }

        self.mPrepareMockCommands(_cmds)

        ebIpTablesRoCE.mPrevmSetupIptables(self.mGetClubox(), True)

        return self.assertTrue(True, "Method mPrevmSetupIptables executed successfully")

    def test_define_kvm_resource_dom0(self):
        _dom0, _ = self.mGetClubox().mReturnDom0DomUPair()[0]

        _commands = [
            exaMockCommand("/bin/scp*", aRc=0),
            exaMockCommand("virsh*", aRc=0, aStdout="local_schema\n")
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        ebIpTablesRoCE.mDefineKVMResourceInDom0(_dom0, "local_schema", "remote_schema", "nwfilter-")

        return self.assertTrue(True, "Method mDefineKVMResourceInDom0 executed successfully")

    def test_get_kvm_schema_dom0(self):
        _dom0, _ = self.mGetClubox().mReturnDom0DomUPair()[0]

        tmp_file = "/tmp/tmp.FRlsuaKzHr.xml\n"

        _commands = [
            exaMockCommand("mktemp*", aRc=0, aStdout=tmp_file),
            exaMockCommand("virsh*", aRc=0),
            exaMockCommand("mktemp*", aRc=0, aStdout=tmp_file, aStderr="")

        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        return self.assertEqual(True,
                                bool(ebIpTablesRoCE.mGetKVMSchemaFromDom0(_dom0, "vm_name-net0-exabm", "nwfilter")))

    def test_validate_iptables(self):
        _dom0, _ = self.mGetClubox().mReturnDom0DomUPair()[0]

        # Read rules from config file
        abs_path = get_gcontext().mGetBasePath()
        atp_path = os.path.join(abs_path, self._atp_path)
        text_file = open(atp_path+"ADBD-iptables.tpl", "r")
        iprules = text_file.read()

        # close file
        text_file.close()

        _commands = [
            exaMockCommand("/sbin/iptables -S", aStdout=iprules)
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                _commands
            ]
        }

        self.mPrepareMockCommands(_cmds)

        return self.assertEqual(True, bool(ebIpTablesRoCE.mValidateIptables(_dom0)))

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRestartVM")
    @patch("exabox.ovm.vmcontrol.ebVgLifeCycle.mDispatchEvent")
    @patch("exabox.ovm.vmcontrol.ebVgLifeCycle.mSetOVMCtrl")
    def test_reboot_VM_Virsh(self, mock_mSetOVMCtrl, mock_dispatchEvent, mock_restartVM):
        _dom0, _domU = self.mGetClubox().mReturnDom0DomUPair()[0]
        cluctrl = self.mGetClubox()

        #vm stop and start functionality is already covered to a good extent in vm operations UT
        #hence just mock/patch it here in iptables UT.
        mock_dispatchEvent.side_effect = None
        mock_dispatchEvent.return_value = 0
        mock_restartVM.side_effect = None
        mock_restartVM.return_value = 0

        ebIpTablesRoCE.mRebootVMViaVirsh(cluctrl, _domU, _dom0)

        return self.assertTrue(True, "Method mRebootVMViaVirsh executed successfully")

    def test_insert_remove_rules_from_schema(self):
        try:
            tmp_client_rules_path = self.mGetUtil().mGetOutputDir() + '/expected_client.xml'

            # Create a tmp XML to work
            abs_path = get_gcontext().mGetBasePath()
            client_rules_path = os.path.join(abs_path, self._atp_path) + "expected_client.xml"
            shutil.copy2(client_rules_path, tmp_client_rules_path)
            os.chmod(tmp_client_rules_path, 0o777)

            _parse = lambda payload, iftype: list(ebIpTablesRoCE.mReadIpTablesDictATPPayload(self.json_rules, "client"))
            _client_net_rules = _parse(self.json_rules, 'client')

            ebIpTablesRoCE.mInsertRemoveRulesFromNetFilterSchema(tmp_client_rules_path, True, *_client_net_rules)
        finally:
            # Remove the tmp XML file created
            os.remove(tmp_client_rules_path)

        return self.assertTrue(True, "Method mInsertRemoveRulesFromNetFilterSchema executed successfully")

    def test_remove_add_net_filter_from_vmschema(self):
        try:
            tmp_file_vmconfig = self.mGetUtil().mGetOutputDir() + '/vmconfig.xml'

            # Create a tmp XML to work
            abs_path = get_gcontext().mGetBasePath()
            vm_config_path = os.path.join(abs_path, self._atp_path) + "vmconfig.xml"
            shutil.copy2(vm_config_path, tmp_file_vmconfig)
            os.chmod(tmp_file_vmconfig, 0o777)

            ebIpTablesRoCE.mRemoveNetFilterFromVMSchema(tmp_file_vmconfig, 'net0')

            ebIpTablesRoCE.mAddNetFilterToVMSchema(tmp_file_vmconfig, 'net1',
                                                   'c3714n5c1.clientmvm.devx8mroce.oraclevcn.com-net1-exabm')
        finally:
            # Remove the tmp XML file created
            os.remove(tmp_file_vmconfig)

        return self.assertTrue(True, "Methods mRemoveNetFilterFromVMSchema and mAddNetFilterToVMSchema executed "
                                     "successfully")


if __name__ == '__main__':
    unittest.main()
