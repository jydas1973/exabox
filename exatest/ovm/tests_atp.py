#!/bin/python
#
# $Header: tests_atp.py 26-feb-2026.06:24:02 prsshukl Exp $
#
# tests_atp.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_atp.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    03/06/26 - Bug 38723384: Add retry/force logic for crs restart
#    prsshukl    02/26/26 - Creation
#

import io
import contextlib
import unittest

from unittest.mock import ANY, MagicMock, patch

from exabox.core.Error import ExacloudRuntimeError
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.atp import (
    AUTONOMOUS_FLAG,
    AtpAddRoutes2DomU,
    AtpAddiptables2Dom0,
    AtpAddScanname2EtcHosts,
    AtpCreateAtpIni,
    AtpSetupASMListener,
    AtpSetupSecondListener,
    AtpSetupNamespace,
    ebATPTest,
    ebATPNetworkUtils,
    ebAtpStep,
    ebAtpUtils,
    ebCluATPConfig,
    areATPFeatureDependenciesSatisfied,
)


class DummyOptions(object):
    def __init__(self, jsonconf):
        self.jsonconf = jsonconf


class ebTestAtp(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super(ebTestAtp, cls).setUpClass(False, False)

    def _assert_log_contains(self, mock_log, text):
        self.assertTrue(
            any(text in str(call.args[0]) for call in mock_log.call_args_list)
        )

    # Auto-generated test for areATPFeatureDependenciesSatisfied
    def test_feature_dependency_success_and_failure(self):
        dep_map = {"Step": ({"one", "two"}, {"off"})}
        def is_enabled(feature):
            return feature != "off"
        with patch("exabox.ovm.atp.ebAtpUtils.isFeatureEnabled", side_effect=is_enabled):
            self.assertTrue(areATPFeatureDependenciesSatisfied("Step", dep_map))

        def is_enabled_with_disabled(feature):
            return True
        with patch("exabox.ovm.atp.ebAtpUtils.isFeatureEnabled", side_effect=is_enabled_with_disabled):
            self.assertFalse(areATPFeatureDependenciesSatisfied("Step", dep_map))

    # Auto-generated test for ebCluATPConfig.__init__
    def test_cluatpconfig_payload_and_options(self):
        payload = {
            "atp": {
                AUTONOMOUS_FLAG: "y",
                "casperIp": "10.0.0.1",
                "omvcnSubnet": "10.0.1.0/24",
                "reserved_subnets": ["10.0.2.0/24"],
            }
        }
        cfg = ebCluATPConfig(DummyOptions(payload))
        self.assertTrue(cfg.isATP())
        self.assertEqual("10.0.0.1", cfg.mGetATPOption("casperIp"))
        self.assertEqual("10.0.1.0/24", cfg.mGetATPOption("omvcnSubnet"))

    # Auto-generated test for ebCluATPConfig.mGetATPOption
    def test_cluatpconfig_default_option_fallback(self):
        cfg = ebCluATPConfig(DummyOptions({}))
        with patch("exabox.ovm.atp.ebAtpUtils.mCheckExaboxConfigOption", return_value={"foo": "bar"}):
            self.assertEqual("bar", cfg.mGetATPOption("foo"))

    # Auto-generated test for ebCluATPConfig.mGetBackupIP
    def test_cluatpconfig_network_accessors(self):
        networks = MagicMock()
        net_config = MagicMock()
        net_config.mGetNetIpAddr.return_value = "10.0.0.5"
        net_config.mGetNetMaster.return_value = "bond0"
        networks.mGetNetworkConfig.return_value = net_config

        mac_cfg = MagicMock()
        mac_cfg.mGetMacNetworks.return_value = ["bond0_backup", "bond0_client"]
        machines = MagicMock()
        machines.mGetMachineConfig.return_value = mac_cfg

        cfg = ebCluATPConfig(DummyOptions({"atp": {AUTONOMOUS_FLAG: "y"}}))
        self.assertEqual("10.0.0.5", cfg.mGetBackupIP("domu", machines, networks))
        self.assertEqual("10.0.0.5", cfg.mGetClientIP("domu", machines, networks))
        self.assertEqual("bond0", cfg.mGetBackupNIC("domu", machines, networks))
        self.assertEqual("bond0", cfg.mGetClientNIC("domu", machines, networks))

    # Auto-generated test for ebAtpStep.mExecute
    def test_step_execute_respects_dependencies(self):
        class DummyStep(ebAtpStep):
            def __init__(self):
                super(DummyStep, self).__init__(MagicMock(), MagicMock())
                self.executed = False

            def _mExecute(self):
                self.executed = True

        step = DummyStep()
        with patch("exabox.ovm.atp.areATPFeatureDependenciesSatisfied", return_value=False):
            step.mExecute()
            self.assertFalse(step.executed)

        with patch("exabox.ovm.atp.areATPFeatureDependenciesSatisfied", return_value=True):
            step.mExecute()
            self.assertTrue(step.executed)

    # Auto-generated test for ebAtpStep._mExecute
    def test_step_execute_raises_not_implemented(self):
        class DummyStep(ebAtpStep):
            def __init__(self):
                super(DummyStep, self).__init__(MagicMock(), MagicMock())

            def _mExecute(self):
                return ebAtpStep._mExecute(self)

        step = DummyStep()
        with self.assertRaises(NotImplementedError):
            step._mExecute()

    # Auto-generated test for AtpAddRoutes2DomU._mAddRoute2Backup
    def test_add_routes_error_raises(self):
        node = MagicMock()
        node.mExecuteCmd.return_value = (0, io.StringIO("out"), io.StringIO("err"))
        node.mGetCmdExitStatus.return_value = 1

        atp = MagicMock()
        atp.mGetBackupNIC.return_value = "bond0"

        with patch("exabox.ovm.atp.ebAtpUtils.mGetIFGateway", return_value="10.0.0.1"):
            step = AtpAddRoutes2DomU(node, atp, "domu", [("dom0", "domu")], MagicMock(), MagicMock())
            with self.assertRaises(ExacloudRuntimeError):
                step._mAddRoute2Backup("10.0.0.0", "255.255.255.0")

    # Auto-generated test for AtpAddRoutes2DomU._mExecute
    def test_add_routes_execute_cidr(self):
        node = MagicMock()
        atp = MagicMock()

        def option_lookup(key):
            if key == "casperIp":
                return "10.0.0.0/24"
            if key == "reserved_subnets":
                return ["10.1.0.0/24"]
            return None

        atp.mGetATPOption.side_effect = option_lookup

        step = AtpAddRoutes2DomU(node, atp, "domu", [("dom0", "domu")], MagicMock(), MagicMock())
        step._mAddRoute2Backup = MagicMock()

        with patch("exabox.ovm.atp.ebAtpUtils.isCidr", return_value=True), \
            patch("exabox.ovm.atp.ebAtpUtils.cidr_to_netmask", side_effect=lambda val: (val.split("/")[0], "255.255.255.0")):
            step._mExecute()

        step._mAddRoute2Backup.assert_any_call("10.0.0.0", "255.255.255.0")
        step._mAddRoute2Backup.assert_any_call("10.1.0.0", "255.255.255.0")

    # Auto-generated test for AtpAddRoutes2DomU._mExecute
    def test_add_routes_execute_non_cidr(self):
        node = MagicMock()
        atp = MagicMock()
        atp.mGetATPOption.side_effect = lambda key: "10.0.0.9" if key == "casperIp" else None

        step = AtpAddRoutes2DomU(node, atp, "domu", [("dom0", "domu")], MagicMock(), MagicMock())
        step._mAddRoute2Backup = MagicMock()

        with patch("exabox.ovm.atp.ebAtpUtils.isCidr", return_value=False):
            step._mExecute()

        step._mAddRoute2Backup.assert_called_once_with("10.0.0.9", "255.255.255.255")


    # Auto-generated test for AtpAddiptables2Dom0._mExecute
    def test_addiptables_creates_config(self):
        node = MagicMock()
        node.mConnect.return_value = None
        node.mDisconnect.return_value = None

        with patch("exabox.ovm.atp.exaBoxNode", return_value=node), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetIF2IPMapping", return_value={"client": {"domu1": "10.0.0.5"}}), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetClientMac", return_value="aa:bb"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetIFGateway", return_value="10.0.0.1"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetDictFromGen2Payload", return_value=[1521, 1522]), \
            patch("exabox.ovm.atp.NamedTemporaryFile") as mock_tmp, \
            patch("exabox.ovm.atp.os.unlink") as mock_unlink, \
            patch("exabox.ovm.atp.os.path.exists", return_value=False):

            temp_file = MagicMock()
            temp_file.name = "/tmp/mockfile"
            temp_file.file = MagicMock()
            mock_tmp.return_value = temp_file

            atp = MagicMock()
            atp.mGetATPOption.return_value = {"client": {"protocol": {"tcp": [1521, 1522]}}}
            step = AtpAddiptables2Dom0(MagicMock(), atp, [("dom0", "domu1")], MagicMock(), MagicMock())
            step._mExecute()

            node.mExecuteCmd.assert_any_call("mkdir -p %s" % ebAtpUtils.DOM0_EXACLOUD_CONFIG_NETWORK_DIR)
            node.mCopyFile.assert_called_once_with("/tmp/mockfile", ebAtpUtils.DOM0_VIF_INFO_FILE + ".domu1")
            mock_unlink.assert_called_once_with("/tmp/mockfile")

    # Auto-generated test for AtpAddScanname2EtcHosts._mExecute
    def test_add_scanname_updates_hosts(self):
        node = MagicMock()
        with patch("exabox.ovm.atp.exaBoxNode", return_value=node), \
            patch("exabox.ovm.atp.ebAtpUtils.mReadAtpIniFile2Dict", return_value={
                "scanip": "10.0.0.10",
                "scanname": "scan01",
                "domainname": "example.com",
            }):
            step = AtpAddScanname2EtcHosts(MagicMock(), MagicMock(), "domu1")
            step._mExecute()
            self.assertTrue(node.mExecuteCmd.called)

    # Auto-generated test for AtpCreateAtpIni._mExecute
    def test_create_atp_ini_file(self):
        atp = MagicMock()
        atp.mGetATPOption.return_value = "ocid"
        payload = {
            "nodes": [
                {
                    "client": {"hostname": "domu1"},
                    "backup": {},
                }
            ],
            "backup_scans": {"hostname": "scanbkp", "ips": ["10.1.0.5"]},
            "network_services": {
                "backupdns": {"domain_name": "example.com", "ip": "10.1.0.2"},
                "dns": ["10.1.0.3"],
            },
        }

        def dict_payload(_, path):
            mapping = {
                "backup_scans/hostname": "scanbkp",
                "backup_scans/ips": ["10.1.0.5"],
                "network_services/backupdns/domain_name": "example.com",
                "network_services/backupdns/ip": "10.1.0.2",
                "network_services/dns": ["10.1.0.3"],
            }
            return mapping[path]

        with patch("exabox.ovm.atp.ebAtpUtils.mGetDictFromGen2Payload", side_effect=dict_payload), \
            patch("exabox.ovm.atp.ebAtpUtils.mWriteAtpIniFile") as mock_write:
            step = AtpCreateAtpIni(MagicMock(), atp, payload, "domu1.example.com")
            step._mExecute()

            self.assertTrue(mock_write.called)
            args, _ = mock_write.call_args
            self.assertEqual("scanbkp", args[0]["scanname"])
            self.assertEqual("ocid", args[0]["dbSystemOCID"])

    # Auto-generated test for AtpCreateAtpIni._mExecute
    def test_create_atp_ini_skips_missing_customer_network(self):
        step = AtpCreateAtpIni(MagicMock(), MagicMock(), None, "domu1")
        with patch("exabox.ovm.atp.ebAtpUtils.mWriteAtpIniFile") as mock_write:
            step._mExecute()
            mock_write.assert_not_called()

    # Auto-generated test for AtpSetupNamespace._mExecute
    def test_setup_namespace_file_written(self):
        payload = {
            "nodes": [
                {"client": {"hostname": "domu1"}},
                {"client": {"hostname": "domu2"}},
            ]
        }

        with patch("exabox.ovm.atp.ebAtpUtils.mWriteAtpNamespaceFile") as mock_write:
            step = AtpSetupNamespace(MagicMock(), MagicMock(), payload, "domu1.example.com")
            step._mExecute()
            mock_write.assert_called_once()

    # Auto-generated test for AtpSetupNamespace._mExecute
    def test_setup_namespace_no_payload(self):
        with patch("exabox.ovm.atp.ebAtpUtils.mWriteAtpNamespaceFile") as mock_write:
            step = AtpSetupNamespace(MagicMock(), MagicMock(), None, "domu1")
            step._mExecute()
            mock_write.assert_not_called()

    # Auto-generated test for ebATPNetworkUtils.mATPGetNetwork
    def test_network_utils_selects_network(self):
        networks = MagicMock()
        networks.mGetNetworkConfig.return_value = "config"
        net_list = ["bond0_backup", "bond0_client"]
        self.assertEqual("config", ebATPNetworkUtils.mATPGetBackupNetworkConfig(net_list, networks))
        self.assertEqual("config", ebATPNetworkUtils.mATPGetClientNetworkConfig(net_list, networks))

    # Auto-generated test for AtpSetupSecondListener._mExecute
    def test_setup_second_listener_skips_oracle_home(self):
        pair = [("dom0", "domu1"), ("dom0b", "domu2")]
        atp = MagicMock()

        node_config = MagicMock()
        node_config.mExecuteCmd.return_value = (0, io.StringIO("5\n"), io.StringIO(""))

        node_root = MagicMock()
        node_grid = MagicMock()

        def opt_lookup(key):
            return {"sec_listener_port": "1522", "netnum": "7"}.get(key)

        with patch("exabox.ovm.atp.exaBoxNode", side_effect=[node_config, node_root, node_grid]) as mock_node, \
            patch("exabox.ovm.atp.get_gcontext"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetExaboxATPOption", side_effect=opt_lookup), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupVipFromAtpIni", side_effect=["10.0.0.10", "10.0.0.11"]), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleHome", side_effect=lambda domu, name: None if name == "dbname" else "/grid"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupIps", return_value="10.0.0.20"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetIFNetmask", return_value="255.255.255.0"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetSubnetFromIpAndNetmask", return_value="10.0.0.0"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupScannameFromAtpIni", return_value="scanname"):

            step = AtpSetupSecondListener(MagicMock(), atp, pair, MagicMock(), MagicMock(), "dbname", MagicMock(), MagicMock())
            step._mExecute()

        self.assertEqual(3, mock_node.call_count)
        node_root.mExecuteScript.assert_called_once()
        node_grid.mExecuteScript.assert_called_once()
        node_grid.mSetUser.assert_called_with("grid")

    # Auto-generated test for AtpSetupASMListener._mExecute
    def test_setup_asm_listener_happy_path(self):
        ebox = MagicMock()
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetMachines.return_value = MagicMock()
        ebox.mGetNetworks.return_value = MagicMock()
        ebox.mGetClusters.return_value = MagicMock()
        ebox.mGetArgsOptions.return_value = MagicMock()
        ebox.mGetATP.return_value = MagicMock()

        node_pair = MagicMock()
        node_pair.mExecuteCmd.side_effect = [
            (0, io.StringIO("10.0.0.5\n"), io.StringIO("")),
            (0, io.StringIO("altered"), io.StringIO("")),
        ]

        node_register = MagicMock()
        node_register.mExecuteCmd.side_effect = [
            (0, io.StringIO("ok"), io.StringIO("")),
            (0, io.StringIO("ok"), io.StringIO("")),
        ]

        node_root = MagicMock()
        node_root.mExecuteCmd.side_effect = [
            (0, io.StringIO("stopped"), io.StringIO("")),
            (0, io.StringIO("started"), io.StringIO("")),
        ]
        node_root.mGetCmdExitStatus.return_value = 0

        with patch("exabox.ovm.atp.exaBoxNode", side_effect=[node_pair, node_register, node_root]) as mock_node, \
            patch("exabox.ovm.atp.get_gcontext"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleSid", return_value="+ASM1"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleHome", return_value="/grid"):

            step = AtpSetupASMListener(MagicMock(), ebox, "dbname")
            step._mExecute()

        self.assertEqual(3, mock_node.call_count)
        node_pair.mSetUser.assert_called_with("grid")
        node_register.mSetUser.assert_called_with("grid")
        node_root.mSetUser.assert_called_with("root")
        node_root.mExecuteCmd.assert_any_call("/grid/bin/crsctl stop cluster -all", ANY)
        node_root.mExecuteCmd.assert_any_call("/grid/bin/crsctl start cluster -all", ANY)

    # Auto-generated test for AtpSetupASMListener._mExecute
    def test_setup_asm_listener_missing_output_raises(self):
        ebox = MagicMock()
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetMachines.return_value = MagicMock()
        ebox.mGetNetworks.return_value = MagicMock()
        ebox.mGetClusters.return_value = MagicMock()
        ebox.mGetArgsOptions.return_value = MagicMock()
        ebox.mGetATP.return_value = MagicMock()

        node_pair = MagicMock()
        node_pair.mExecuteCmd.return_value = (0, None, io.StringIO("fail"))

        with patch("exabox.ovm.atp.exaBoxNode", return_value=node_pair), \
            patch("exabox.ovm.atp.get_gcontext"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleSid", return_value="+ASM1"):

            step = AtpSetupASMListener(MagicMock(), ebox, "dbname")
            with self.assertRaises(ExacloudRuntimeError):
                step._mExecute()

    # Auto-generated test for AtpSetupASMListener._mExecute
    def test_setup_asm_listener_empty_readlines_raises(self):
        ebox = MagicMock()
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetMachines.return_value = MagicMock()
        ebox.mGetNetworks.return_value = MagicMock()
        ebox.mGetClusters.return_value = MagicMock()
        ebox.mGetArgsOptions.return_value = MagicMock()
        ebox.mGetATP.return_value = MagicMock()

        node_pair = MagicMock()
        node_pair.mExecuteCmd.return_value = (0, io.StringIO(""), io.StringIO(""))

        with patch("exabox.ovm.atp.exaBoxNode", return_value=node_pair), \
            patch("exabox.ovm.atp.get_gcontext"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleSid", return_value="+ASM1"):

            step = AtpSetupASMListener(MagicMock(), ebox, "dbname")
            with self.assertRaises(ExacloudRuntimeError):
                step._mExecute()

    # Auto-generated test for AtpCreateAtpIni._mExecute
    def test_create_atp_ini_missing_node(self):
        payload = {
            "nodes": [
                {
                    "client": {"hostname": "domu2"},
                    "backup": {},
                }
            ]
        }
        with patch("exabox.ovm.atp.ebAtpUtils.mWriteAtpIniFile") as mock_write:
            step = AtpCreateAtpIni(MagicMock(), MagicMock(), payload, "domu1")
            step._mExecute()
            mock_write.assert_not_called()

    # Auto-generated test for AtpSetupSecondListener._mExecute
    def test_setup_second_listener_runs_oracle_branch(self):
        pair = [("dom0", "domu1"), ("dom0b", "domu2")]
        atp = MagicMock()
        node_config = MagicMock()
        node_config.mExecuteCmd.return_value = (0, io.StringIO("3\n"), io.StringIO(""))
        node_root = MagicMock()
        node_grid = MagicMock()
        node_oracle1 = MagicMock()
        node_oracle2 = MagicMock()

        def opt_lookup(key):
            return {"sec_listener_port": "1522", "netnum": None}.get(key)

        with patch("exabox.ovm.atp.exaBoxNode", side_effect=[node_config, node_root, node_grid, node_oracle1, node_oracle2]) as mock_node, \
            patch("exabox.ovm.atp.get_gcontext"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetExaboxATPOption", side_effect=opt_lookup), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupVipFromAtpIni", side_effect=["10.0.0.10", "10.0.0.11", "10.0.0.10", "10.0.0.11"]), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleHome", side_effect=lambda domu, name: "/oracle" if name == "dbname" else "/grid"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupIps", return_value="10.0.0.20"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetIFNetmask", return_value="255.255.255.0"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetSubnetFromIpAndNetmask", return_value="10.0.0.0"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupScannameFromAtpIni", return_value="scanname"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleSid", return_value="ORCL"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetClientVip", side_effect=["10.0.0.30", "10.0.0.31"]):

            step = AtpSetupSecondListener(MagicMock(), atp, pair, MagicMock(), MagicMock(), "dbname", MagicMock(), MagicMock())
            step._mExecute()

        self.assertEqual(5, mock_node.call_count)
        node_oracle1.mSetUser.assert_called_with("oracle")
        node_oracle2.mSetUser.assert_called_with("oracle")
        self.assertTrue(node_oracle1.mExecuteScript.called)
        self.assertTrue(node_oracle2.mExecuteScript.called)

    # Auto-generated test for AtpAddRoutes2DomU._mExecute
    def test_add_routes_warns_on_missing_subnets(self):
        node = MagicMock()
        atp = MagicMock()
        casper_value = MagicMock()
        casper_value.strip.return_value = None
        def option_lookup(key):
            if key == "casperIp":
                return casper_value
            return None
        atp.mGetATPOption.side_effect = option_lookup

        step = AtpAddRoutes2DomU(node, atp, "domu", [("dom0", "domu")], MagicMock(), MagicMock())
        step._mAddRoute2Backup = MagicMock()
        with patch.object(step, "mLogWarn") as mock_warn:
            step._mExecute()

        self.assertEqual(2, mock_warn.call_count)
        step._mAddRoute2Backup.assert_not_called()

    # Auto-generated test for AtpSetupSecondListener._mExecute
    def test_setup_second_listener_dbname_none(self):
        pair = [("dom0", "domu1"), ("dom0b", "domu2")]
        atp = MagicMock()
        node_config = MagicMock()
        node_config.mExecuteCmd.return_value = (0, io.StringIO("2\n"), io.StringIO(""))
        node_root = MagicMock()
        node_grid = MagicMock()

        with patch("exabox.ovm.atp.exaBoxNode", side_effect=[node_config, node_root, node_grid]) as mock_node, \
            patch("exabox.ovm.atp.get_gcontext"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetExaboxATPOption", side_effect=lambda key: None), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupVipFromAtpIni", side_effect=["10.0.0.10", "10.0.0.11"]), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleHome", side_effect=lambda domu, name: None if name is None else "/grid"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupIps", return_value="10.0.0.20"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetIFNetmask", return_value="255.255.255.0"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetSubnetFromIpAndNetmask", return_value="10.0.0.0"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupScannameFromAtpIni", return_value="scanname"):

            step = AtpSetupSecondListener(MagicMock(), atp, pair, MagicMock(), MagicMock(), None, MagicMock(), MagicMock())
            with patch.object(step, "mLogInfo") as mock_info:
                step._mExecute()

        self.assertEqual(3, mock_node.call_count)
        self._assert_log_contains(mock_info, "DB Name is None")
        node_root.mExecuteScript.assert_called_once()
        node_grid.mExecuteScript.assert_called_once()

    # Auto-generated test for AtpSetupASMListener._mExecute
    def test_setup_asm_listener_logs_error_on_group_failure(self):
        ebox = MagicMock()
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetMachines.return_value = MagicMock()
        ebox.mGetNetworks.return_value = MagicMock()
        ebox.mGetClusters.return_value = MagicMock()
        ebox.mGetArgsOptions.return_value = MagicMock()
        ebox.mGetATP.return_value = MagicMock()

        node_pair = MagicMock()
        node_pair.mExecuteCmd.side_effect = [
            (0, io.StringIO("10.0.0.5\n"), io.StringIO("")),
            (0, io.StringIO("altered"), io.StringIO("")),
        ]

        node_register = MagicMock()
        node_register.mExecuteCmd.side_effect = [
            (0, io.StringIO(""), io.StringIO("")),
            (0, None, io.StringIO("")),
        ]

        with patch("exabox.ovm.atp.exaBoxNode", side_effect=[node_pair, node_register]) as mock_node, \
            patch("exabox.ovm.atp.get_gcontext"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleSid", return_value="+ASM1"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleHome", return_value="/grid"):

            step = AtpSetupASMListener(MagicMock(), ebox, "dbname")
            with patch.object(step, "mLogError") as mock_error:
                step._mExecute()

        self.assertEqual(2, mock_node.call_count)
        mock_error.assert_called_once()

    # Auto-generated test for ebATPTest.mAtpTest
    def test_atp_test_runs_routes_and_network_lookup(self):
        ddp = [("dom0", "domu1")]

        options = DummyOptions({"atp": {AUTONOMOUS_FLAG: "y"}})
        machines = MagicMock()
        mac_cfg = MagicMock()
        mac_cfg.mGetMacNetworks.return_value = ["bond0_backup"]
        machines.mGetMachineConfig.return_value = mac_cfg

        networks = MagicMock()
        net_cfg = MagicMock()
        net_cfg.mGetNetIpAddr.return_value = "10.0.0.8"
        networks.mGetNetworkConfig.return_value = net_cfg

        node_domu = MagicMock()
        node_dom0 = MagicMock()

        @contextlib.contextmanager
        def fake_connect(host, ctx):
            if host == "domu1":
                yield node_domu
            else:
                yield node_dom0

        with patch("exabox.ovm.atp.connect_to_host", side_effect=fake_connect) as mock_connect, \
            patch("exabox.ovm.atp.get_gcontext"), \
            patch("exabox.ovm.atp.AtpAddRoutes2DomU.mExecute") as mock_routes, \
            patch("exabox.ovm.atp.ebAtpUtils.mGetExaboxATPOption", return_value="db1"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupMac", return_value=["aa:bb"]):

            ebATPTest.mAtpTest(ddp, options, machines, networks, MagicMock())

        self.assertEqual(3, mock_connect.call_count)
        mock_routes.assert_called_once()

    # Auto-generated test for ebCluATPConfig.__repr__
    def test_cluatpconfig_repr_and_missing_key(self):
        payload = {"atp": {AUTONOMOUS_FLAG: "y", "casperIp": "10.0.0.1"}}
        cfg = ebCluATPConfig(DummyOptions(payload))
        with patch("exabox.ovm.atp.ebLogWarn") as mock_warn:
            self.assertIsNone(cfg._getJsonValueByKey("missing"))
            mock_warn.assert_called_once()
        rep = repr(cfg)
        self.assertIn("__IsATP: True", rep)
        self.assertIn("casperIp", rep)

    # Auto-generated test for ebCluATPConfig.__init__
    def test_cluatpconfig_options_none_logs_warning(self):
        with patch("exabox.ovm.atp.ebLogWarn") as mock_warn:
            cfg = ebCluATPConfig(None)
        self.assertFalse(cfg.isATP())
        self.assertIsNone(cfg.mGetATPOptions())
        mock_warn.assert_called_once()

    # Auto-generated test for AtpAddScanname2EtcHosts._mExecute
    def test_add_scanname_handles_fqdn(self):
        node = MagicMock()
        with patch("exabox.ovm.atp.exaBoxNode", return_value=node), \
            patch("exabox.ovm.atp.ebAtpUtils.mReadAtpIniFile2Dict", return_value={
                "scanip": "10.0.0.10",
                "scanname": "scan01.example.com",
                "domainname": "example.com",
            }):
            step = AtpAddScanname2EtcHosts(MagicMock(), MagicMock(), "domu1")
            step._mExecute()

        cmd = node.mExecuteCmd.call_args[0][0]
        self.assertIn("scan01.example.com scan01", cmd)

    # Auto-generated test for AtpSetupNamespace._mExecute
    def test_setup_namespace_missing_node_logs_info(self):
        payload = {
            "nodes": [
                {"client": {"hostname": "domu2"}},
            ]
        }

        with patch("exabox.ovm.atp.ebAtpUtils.mWriteAtpNamespaceFile") as mock_write:
            step = AtpSetupNamespace(MagicMock(), MagicMock(), payload, "domu1.example.com")
            with patch.object(step, "mLogInfo") as mock_info:
                step._mExecute()

        mock_write.assert_not_called()
        self._assert_log_contains(mock_info, "Node")

    # Auto-generated test for ebATPNetworkUtils.mATPGetNetwork
    def test_network_utils_no_match_returns_none(self):
        networks = MagicMock()
        net_list = ["bond0_backup"]
        self.assertIsNone(ebATPNetworkUtils.mATPGetNetwork(net_list, "client", networks))

    # Auto-generated test for AtpSetupSecondListener._mExecute
    def test_setup_second_listener_default_netnum(self):
        pair = [("dom0", "domu1"), ("dom0b", "domu2")]
        atp = MagicMock()
        node_config = MagicMock()
        node_config.mExecuteCmd.return_value = (0, io.StringIO(""), io.StringIO(""))
        node_root = MagicMock()
        node_grid = MagicMock()

        with patch("exabox.ovm.atp.exaBoxNode", side_effect=[node_config, node_root, node_grid]), \
            patch("exabox.ovm.atp.get_gcontext"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetExaboxATPOption", side_effect=lambda key: None), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupVipFromAtpIni", side_effect=["10.0.0.10", "10.0.0.11"]), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleHome", side_effect=lambda domu, name: None if name == "dbname" else "/grid"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupIps", return_value="10.0.0.20"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetIFNetmask", return_value="255.255.255.0"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetSubnetFromIpAndNetmask", return_value="10.0.0.0"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupScannameFromAtpIni", return_value="scanname"):

            step = AtpSetupSecondListener(MagicMock(), atp, pair, MagicMock(), MagicMock(), "dbname", MagicMock(), MagicMock())
            step._mExecute()

        cmd_root = node_root.mExecuteScript.call_args[0][0]
        self.assertIn("-netnum 2", cmd_root)

    # Auto-generated test for AtpSetupSecondListener._mExecute
    def test_setup_second_listener_registers_oracle_listener(self):
        pair = [("dom0", "domu1"), ("dom0b", "domu2")]
        atp = MagicMock()
        node_config = MagicMock()
        node_config.mExecuteCmd.return_value = (0, io.StringIO("3\n"), io.StringIO(""))
        node_root = MagicMock()
        node_root.mExecuteScript.return_value = "root-ok"
        node_grid = MagicMock()
        node_grid.mExecuteScript.return_value = "grid-ok"
        node_oracle1 = MagicMock()
        node_oracle2 = MagicMock()

        def opt_lookup(key):
            return {"sec_listener_port": "1522"}.get(key)

        def oracle_home(domu, name):
            if name == "grid":
                return "/grid"
            return "/u01/app/oracle"

        with patch(
            "exabox.ovm.atp.exaBoxNode",
            side_effect=[node_config, node_root, node_grid, node_oracle1, node_oracle2],
        ) as mock_node, \
            patch("exabox.ovm.atp.get_gcontext"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetExaboxATPOption", side_effect=opt_lookup), \
            patch(
                "exabox.ovm.atp.ebAtpUtils.mGetBackupVipFromAtpIni",
                side_effect=["10.0.0.10", "10.0.0.11", "10.0.0.10", "10.0.0.11"],
            ), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleHome", side_effect=oracle_home), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleSid", side_effect=["ORCL1", "ORCL2"]), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetClientVip", side_effect=["10.0.0.30", "10.0.0.31"]), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupIps", return_value="10.0.0.20"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetIFNetmask", return_value="255.255.255.0"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetSubnetFromIpAndNetmask", return_value="10.0.0.0"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupScannameFromAtpIni", return_value="scanname"):

            step = AtpSetupSecondListener(MagicMock(), atp, pair, MagicMock(), MagicMock(), "dbname", MagicMock(), MagicMock())
            step._mExecute()

        self.assertEqual(5, mock_node.call_count)
        node_grid.mSetUser.assert_called_with("grid")
        node_oracle1.mSetUser.assert_called_with("oracle")
        node_oracle2.mSetUser.assert_called_with("oracle")
        script_root = node_root.mExecuteScript.call_args[0][0]
        self.assertIn("-netnum 3", script_root)
        script_oracle = node_oracle1.mExecuteScript.call_args[0][0]
        self.assertIn("LOCAL_LISTENER", script_oracle)
        self.assertIn("HOST=10.0.0.30", script_oracle)

    # Auto-generated test for AtpAddRoutes2DomU._mExecute
    def test_add_routes_warns_when_reserved_subnets_missing(self):
        node = MagicMock()
        atp = MagicMock()
        atp.mGetATPOption.side_effect = lambda key: "10.0.0.9" if key == "casperIp" else None

        step = AtpAddRoutes2DomU(node, atp, "domu", [("dom0", "domu")], MagicMock(), MagicMock())
        step._mAddRoute2Backup = MagicMock()

        with patch("exabox.ovm.atp.ebAtpUtils.isCidr", return_value=False), \
            patch.object(step, "mLogWarn") as mock_warn:
            step._mExecute()

        step._mAddRoute2Backup.assert_called_once_with("10.0.0.9", "255.255.255.255")
        self._assert_log_contains(mock_warn, "No reserved subnets")

    # Auto-generated test for AtpAddRoutes2DomU._mExecute
    def test_add_routes_raises_when_casper_value_none(self):
        node = MagicMock()
        atp = MagicMock()
        atp.mGetATPOption.side_effect = lambda key: None

        step = AtpAddRoutes2DomU(node, atp, "domu", [("dom0", "domu")], MagicMock(), MagicMock())

        with self.assertRaises(AttributeError):
            step._mExecute()

    # Auto-generated test for ebCluATPConfig.mGetATPOption
    def test_cluatpconfig_option_defaults_missing_value(self):
        cfg = ebCluATPConfig(DummyOptions({}))
        with patch("exabox.ovm.atp.ebAtpUtils.mCheckExaboxConfigOption", return_value={"foo": None}):
            self.assertIsNone(cfg.mGetATPOption("foo"))

    # Auto-generated test for AtpAddRoutes2DomU._mExecute
    def test_add_routes_skips_non_cidr_reserved_subnet(self):
        node = MagicMock()
        atp = MagicMock()

        def option_lookup(key):
            if key == "casperIp":
                return "10.0.0.0/24"
            if key == "reserved_subnets":
                return ["10.1.0.0/24", "not-a-cidr"]
            return None

        atp.mGetATPOption.side_effect = option_lookup

        step = AtpAddRoutes2DomU(node, atp, "domu", [("dom0", "domu")], MagicMock(), MagicMock())
        step._mAddRoute2Backup = MagicMock()

        def is_cidr(value):
            return value != "not-a-cidr"

        with patch("exabox.ovm.atp.ebAtpUtils.isCidr", side_effect=is_cidr), \
            patch("exabox.ovm.atp.ebAtpUtils.cidr_to_netmask", side_effect=lambda val: (val.split("/")[0], "255.255.255.0")):
            step._mExecute()

        self.assertEqual(2, step._mAddRoute2Backup.call_count)
        step._mAddRoute2Backup.assert_any_call("10.0.0.0", "255.255.255.0")
        step._mAddRoute2Backup.assert_any_call("10.1.0.0", "255.255.255.0")

    # Auto-generated test for AtpAddiptables2Dom0._mExecute
    def test_addiptables_writes_multiple_clients(self):
        node = MagicMock()
        node.mConnect.return_value = None
        node.mDisconnect.return_value = None

        with patch("exabox.ovm.atp.exaBoxNode", return_value=node), \
            patch(
                "exabox.ovm.atp.ebAtpUtils.mGetIF2IPMapping",
                return_value={"client": {"domu1": "10.0.0.5", "domu2": "10.0.0.6"}},
            ), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetClientMac", return_value="aa:bb"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetIFGateway", return_value="10.0.0.1"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetDictFromGen2Payload", return_value=[1521]), \
            patch("exabox.ovm.atp.NamedTemporaryFile") as mock_tmp, \
            patch("exabox.ovm.atp.os.unlink") as mock_unlink, \
            patch("exabox.ovm.atp.os.path.exists", return_value=False):

            temp_file = MagicMock()
            temp_file.name = "/tmp/mockfile"
            temp_file.file = MagicMock()
            mock_tmp.return_value = temp_file

            atp = MagicMock()
            atp.mGetATPOption.return_value = {"client": {"protocol": {"tcp": [1521]}}}
            step = AtpAddiptables2Dom0(MagicMock(), atp, [("dom0", "domu1"), ("dom0", "domu2")], MagicMock(), MagicMock())
            step._mExecute()

            written_data = temp_file.file.write.call_args[0][0].decode("utf8")
            self.assertIn("domu1", written_data)
            self.assertIn("domu2", written_data)
            self.assertIn("whitelist:tcp=1521", written_data)
            self.assertEqual(2, node.mCopyFile.call_count)
            mock_unlink.assert_called_once_with("/tmp/mockfile")

    # Auto-generated test for AtpSetupSecondListener._mExecute
    def test_setup_second_listener_uses_netnum_from_config(self):
        pair = [("dom0", "domu1"), ("dom0b", "domu2")]
        atp = MagicMock()
        node_config = MagicMock()
        node_config.mExecuteCmd.return_value = (0, io.StringIO("4\n"), io.StringIO(""))
        node_root = MagicMock()
        node_grid = MagicMock()

        def opt_lookup(key):
            if key == "sec_listener_port":
                return "1522"
            if key == "netnum":
                return "9"
            return None

        with patch("exabox.ovm.atp.exaBoxNode", side_effect=[node_config, node_root, node_grid]), \
            patch("exabox.ovm.atp.get_gcontext"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetExaboxATPOption", side_effect=opt_lookup), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupVipFromAtpIni", side_effect=["10.0.0.10", "10.0.0.11"]), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleHome", side_effect=lambda domu, name: None if name == "dbname" else "/grid"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupIps", return_value="10.0.0.20"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetIFNetmask", return_value="255.255.255.0"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetSubnetFromIpAndNetmask", return_value="10.0.0.0"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupScannameFromAtpIni", return_value="scanname"):

            step = AtpSetupSecondListener(MagicMock(), atp, pair, MagicMock(), MagicMock(), "dbname", MagicMock(), MagicMock())
            step._mExecute()

        script_root = node_root.mExecuteScript.call_args[0][0]
        self.assertIn("-netnum 9", script_root)

    # Auto-generated test for AtpSetupASMListener._mExecute
    def test_setup_asm_listener_raises_on_missing_output_handle(self):
        ebox = MagicMock()
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetMachines.return_value = MagicMock()
        ebox.mGetNetworks.return_value = MagicMock()
        ebox.mGetClusters.return_value = MagicMock()
        ebox.mGetArgsOptions.return_value = MagicMock()
        ebox.mGetATP.return_value = MagicMock()

        node_pair = MagicMock()
        node_pair.mExecuteCmd.return_value = (0, None, io.StringIO("bad"))

        with patch("exabox.ovm.atp.exaBoxNode", return_value=node_pair), \
            patch("exabox.ovm.atp.get_gcontext"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleSid", return_value="+ASM1"):

            step = AtpSetupASMListener(MagicMock(), ebox, "dbname")
            with self.assertRaises(ExacloudRuntimeError):
                step._mExecute()

    # Auto-generated test for ebCluATPConfig.__init__
    def test_cluatpconfig_missing_autonomous_flag_logs_info(self):
        payload = {"atp": {"casperIp": "10.0.0.1"}}
        with patch("exabox.ovm.atp.ebLogInfo") as mock_info:
            cfg = ebCluATPConfig(DummyOptions(payload))

        self.assertFalse(cfg.isATP())
        self.assertIsNone(cfg.mGetATPOptions())
        self.assertEqual("10.0.0.1", cfg.mGetATPOption("casperIp"))
        self._assert_log_contains(mock_info, "no value")

    # Auto-generated test for ebCluATPConfig._getJsonValueByKey
    def test_cluatpconfig_getjsonvalue_logs_debug(self):
        payload = {"atp": {AUTONOMOUS_FLAG: "y", "casperIp": "10.0.0.2"}}
        cfg = ebCluATPConfig(DummyOptions(payload))
        with patch("exabox.ovm.atp.ebLogDebug") as mock_debug:
            value = cfg._getJsonValueByKey("casperIp")

        self.assertEqual("10.0.0.2", value)
        mock_debug.assert_called_once()

    # Auto-generated test for AtpSetupSecondListener._mExecute
    def test_setup_second_listener_raises_when_netnum_output_missing(self):
        pair = [("dom0", "domu1"), ("dom0b", "domu2")]
        atp = MagicMock()
        node_config = MagicMock()
        node_config.mExecuteCmd.return_value = (0, None, io.StringIO(""))
        node_root = MagicMock()
        node_grid = MagicMock()

        with patch("exabox.ovm.atp.exaBoxNode", side_effect=[node_config, node_root, node_grid]) as mock_node, \
            patch("exabox.ovm.atp.get_gcontext"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetExaboxATPOption", side_effect=lambda key: None), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupVipFromAtpIni", side_effect=["10.0.0.10", "10.0.0.11"]), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleHome", side_effect=lambda domu, name: None if name == "dbname" else "/grid"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupIps", return_value="10.0.0.20"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetIFNetmask", return_value="255.255.255.0"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetSubnetFromIpAndNetmask", return_value="10.0.0.0"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetBackupScannameFromAtpIni", return_value="scanname"):

            step = AtpSetupSecondListener(MagicMock(), atp, pair, MagicMock(), MagicMock(), "dbname", MagicMock(), MagicMock())
            with self.assertRaises(AttributeError):
                step._mExecute()

        self.assertEqual(1, mock_node.call_count)

    # Auto-generated test for AtpSetupASMListener._mExecute
    def test_setup_asm_listener_handles_missing_sid_output(self):
        ebox = MagicMock()
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetMachines.return_value = MagicMock()
        ebox.mGetNetworks.return_value = MagicMock()
        ebox.mGetClusters.return_value = MagicMock()
        ebox.mGetArgsOptions.return_value = MagicMock()
        ebox.mGetATP.return_value = MagicMock()

        node_pair = MagicMock()
        node_pair.mExecuteCmd.side_effect = [
            (0, io.StringIO("10.0.0.5\n"), io.StringIO("")),
            (0, io.StringIO("altered"), io.StringIO("")),
        ]

        node_register = MagicMock()
        node_register.mExecuteCmd.side_effect = [
            (0, io.StringIO(""), io.StringIO("")),
            (0, None, io.StringIO("")),
        ]

        with patch("exabox.ovm.atp.exaBoxNode", side_effect=[node_pair, node_register]) as mock_node, \
            patch("exabox.ovm.atp.get_gcontext"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleSid", return_value="+ASM1"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleHome", return_value="/grid"):

            step = AtpSetupASMListener(MagicMock(), ebox, "dbname")
            with patch.object(step, "mLogError") as mock_error:
                step._mExecute()

        self.assertEqual(2, mock_node.call_count)
        mock_error.assert_called_once()

    # Auto-generated test for ebAtpStep.mGetStepName
    def test_step_get_stepname_and_logging(self):
        class DummyStep(ebAtpStep):
            def __init__(self):
                super(DummyStep, self).__init__(MagicMock(), MagicMock())

            def _mExecute(self):
                pass

        step = DummyStep()
        self.assertEqual("DummyStep", step.mGetStepName())

        with patch("exabox.ovm.atp.ebLogInfo") as mock_info, \
            patch("exabox.ovm.atp.ebLogDebug") as mock_debug, \
            patch("exabox.ovm.atp.ebLogError") as mock_error, \
            patch("exabox.ovm.atp.ebLogWarn") as mock_warn:

            step.mLogInfo("hello")
            step.mLogDebug("debug")
            step.mLogError("error")
            step.mLogWarn("warn")

        mock_info.assert_called_once()
        mock_debug.assert_called_once()
        mock_error.assert_called_once()
        mock_warn.assert_called_once()

    # Auto-generated test for ebCluATPConfig.mGetATPOptions
    def test_cluatpconfig_get_options_when_atp(self):
        payload = {"atp": {AUTONOMOUS_FLAG: "y", "casperIp": "10.0.0.4"}}
        cfg = ebCluATPConfig(DummyOptions(payload))
        self.assertEqual(payload["atp"], cfg.mGetATPOptions())

    # Auto-generated test for ebCluATPConfig.mGetATPOption
    def test_cluatpconfig_option_missing_returns_none(self):
        payload = {"atp": {AUTONOMOUS_FLAG: "y"}}
        cfg = ebCluATPConfig(DummyOptions(payload))
        self.assertIsNone(cfg.mGetATPOption("missing"))

    # Auto-generated test for AtpAddRoutes2DomU._mAddRoute2Backup
    def test_add_routes_add_route_success(self):
        node = MagicMock()
        node.mExecuteCmd.return_value = (0, io.StringIO("out"), io.StringIO(""))
        node.mGetCmdExitStatus.return_value = 0
        atp = MagicMock()
        atp.mGetBackupNIC.return_value = "bond0"

        with patch("exabox.ovm.atp.ebAtpUtils.mGetIFGateway", return_value="10.0.0.1"):
            step = AtpAddRoutes2DomU(node, atp, "domu", [("dom0", "domu")], MagicMock(), MagicMock())
            step._mAddRoute2Backup("10.0.0.0", "255.255.255.0")

        node.mExecuteCmd.assert_called_once()

    # Auto-generated test for AtpAddRoutes2DomU._mExecute
    def test_add_routes_skips_non_cidr_reserved_subnet(self):
        node = MagicMock()
        atp = MagicMock()

        def option_lookup(key):
            if key == "casperIp":
                return "10.0.0.0/24"
            if key == "reserved_subnets":
                return ["10.2.0.0/24", "not-a-cidr"]
            return None

        atp.mGetATPOption.side_effect = option_lookup
        step = AtpAddRoutes2DomU(node, atp, "domu", [("dom0", "domu")], MagicMock(), MagicMock())
        step._mAddRoute2Backup = MagicMock()

        def is_cidr(val):
            return val != "not-a-cidr"

        with patch("exabox.ovm.atp.ebAtpUtils.isCidr", side_effect=is_cidr), \
            patch("exabox.ovm.atp.ebAtpUtils.cidr_to_netmask", side_effect=lambda val: (val.split("/")[0], "255.255.255.0")):
            step._mExecute()

        self.assertEqual(2, step._mAddRoute2Backup.call_count)
        step._mAddRoute2Backup.assert_any_call("10.0.0.0", "255.255.255.0")
        step._mAddRoute2Backup.assert_any_call("10.2.0.0", "255.255.255.0")

    # Auto-generated test for AtpCreateAtpIni._mExecute
    def test_create_atp_ini_logs_when_node_missing(self):
        payload = {
            "nodes": [
                {"client": {"hostname": "domu2"}, "backup": {}}
            ]
        }

        step = AtpCreateAtpIni(MagicMock(), MagicMock(), payload, "domu1.example.com")
        with patch.object(step, "mLogInfo") as mock_info, \
            patch("exabox.ovm.atp.ebAtpUtils.mWriteAtpIniFile") as mock_write:
            step._mExecute()

        mock_write.assert_not_called()
        self._assert_log_contains(mock_info, "not found in ATP ini payload")

    # Auto-generated test for AtpSetupASMListener._mExecute
    def test_setup_asm_listener_raises_when_empty_output(self):
        ebox = MagicMock()
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetMachines.return_value = MagicMock()
        ebox.mGetNetworks.return_value = MagicMock()
        ebox.mGetClusters.return_value = MagicMock()
        ebox.mGetArgsOptions.return_value = MagicMock()
        ebox.mGetATP.return_value = MagicMock()

        node_pair = MagicMock()
        node_pair.mExecuteCmd.return_value = (0, io.StringIO(""), io.StringIO(""))

        with patch("exabox.ovm.atp.exaBoxNode", return_value=node_pair), \
            patch("exabox.ovm.atp.get_gcontext"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleSid", return_value="+ASM1"):

            step = AtpSetupASMListener(MagicMock(), ebox, "dbname")
            with self.assertRaises(ExacloudRuntimeError):
                step._mExecute()

    # Auto-generated test for AtpAddRoutes2DomU._mExecute
    def test_add_routes_casper_option_none_raises(self):
        node = MagicMock()
        atp = MagicMock()
        atp.mGetATPOption.return_value = None

        step = AtpAddRoutes2DomU(node, atp, "domu", [("dom0", "domu")], MagicMock(), MagicMock())
        with self.assertRaises(AttributeError):
            step._mExecute()

    # Auto-generated test for ebCluATPConfig.mGetATPOption
    def test_cluatpconfig_default_none_returns_none(self):
        cfg = ebCluATPConfig(DummyOptions({}))
        with patch("exabox.ovm.atp.ebAtpUtils.mCheckExaboxConfigOption", return_value={"foo": None}):
            self.assertIsNone(cfg.mGetATPOption("foo"))

    # Auto-generated test for ebCluATPConfig.__init__
    def test_cluatpconfig_missing_autonomous_flag_logs_info(self):
        payload = {"atp": {"client_vip": "10.0.0.5"}}
        with patch("exabox.ovm.atp.ebLogInfo") as mock_info:
            cfg = ebCluATPConfig(DummyOptions(payload))
        self.assertFalse(cfg.isATP())
        self._assert_log_contains(mock_info, "no value of")

    # Auto-generated test for ebCluATPConfig.__init__
    def test_cluatpconfig_debug_logs_options(self):
        payload = {"atp": {AUTONOMOUS_FLAG: "n"}}
        with patch("exabox.ovm.atp.ebLogDebug") as mock_debug:
            ebCluATPConfig(DummyOptions(payload), aDebug=True)
        mock_debug.assert_called_once_with(payload["atp"])

    # Auto-generated test for AtpSetupASMListener._mExecute
    def test_setup_asm_listener_raises_on_missing_output_stream(self):
        ebox = MagicMock()
        ebox.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        ebox.mGetMachines.return_value = MagicMock()
        ebox.mGetNetworks.return_value = MagicMock()
        ebox.mGetClusters.return_value = MagicMock()
        ebox.mGetArgsOptions.return_value = MagicMock()
        ebox.mGetATP.return_value = MagicMock()

        node_pair = MagicMock()
        node_pair.mExecuteCmd.return_value = (0, None, io.StringIO("err"))

        with patch("exabox.ovm.atp.exaBoxNode", return_value=node_pair), \
            patch("exabox.ovm.atp.get_gcontext"), \
            patch("exabox.ovm.atp.ebAtpUtils.mGetOracleSid", return_value="+ASM1"):

            step = AtpSetupASMListener(MagicMock(), ebox, "dbname")
            with self.assertRaises(ExacloudRuntimeError):
                step._mExecute()

    # Auto-generated test for ebCluATPConfig.__repr__
    def test_cluatpconfig_repr_includes_multiple_keys(self):
        payload = {"atp": {AUTONOMOUS_FLAG: "y", "client_vip": "10.0.0.5", "casperIp": "10.0.0.6"}}
        cfg = ebCluATPConfig(DummyOptions(payload))
        rep = repr(cfg)
        self.assertIn("client_vip", rep)
        self.assertIn("casperIp", rep)

    # Auto-generated test for AtpAddScanname2EtcHosts._mExecute
    def test_add_scanname_uses_existing_scan_fqdn(self):
        node = MagicMock()
        with patch("exabox.ovm.atp.exaBoxNode", return_value=node), \
            patch("exabox.ovm.atp.ebAtpUtils.mReadAtpIniFile2Dict", return_value={
                "scanip": "10.0.0.20",
                "scanname": "scan02.example.com",
                "domainname": "example.com",
            }):
            step = AtpAddScanname2EtcHosts(MagicMock(), MagicMock(), "domu1")
            step._mExecute()

        cmd = node.mExecuteCmd.call_args[0][0]
        self.assertIn("scan02.example.com scan02", cmd)


if __name__ == '__main__':
    unittest.main()
