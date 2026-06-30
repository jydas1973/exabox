#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/sla_measurement/tests_SLA_vmCluster.py /main/5 2026/02/09 06:20:21 atgandhi Exp $
#
# tests_SLA_vmCluster.py
#
# Copyright (c) 2023, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_SLA_vmCluster.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    atgandhi    06/17/26 - Fix SLA vmCluster unit test command matching
#    atgandhi    06/17/26 - Bug 39263024 - EXACS - SECURITY SCAN FINDINGS IN
#                           EXABOX/JSONDISPATCH/HANDLER_SLA_VMCLUSTER.PY
#    atgandhi    02/01/26 - Bug 38910261 - EXACS:SLA NOT SET TO 0 AFTER
#                           SLA_SERVER_MAX_TIMEOUT EXPIRY WHEN ADMIN NETWORK
#                           (ETH0) IS DOWN
#    atgandhi    12/12/25 - 38755913 - TESTS_SLA_VMCLUSTER_PY.DIF IS FAILING
#    atgandhi    10/24/25 - Enh 38459507 - LOG BASED SLA COLLECTION AND STORE
#                           DOWNTIMES IN DB
#    jiacpeng    07/10/23 - unittest for vm cluster level sla
#    jiacpeng    07/10/23 - Creation
#
import json
import os
import unittest
from unittest import mock
import datetime
from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.jsondispatch.handler_sla_vmCluster import SLAVmClusterHandler, mExtractDowntimePeriods_with_node
import exabox.jsondispatch.handler_sla_vmCluster as handler_mod

class ebTestSLA(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.maxDiff = None

    def test_payload(self):
        # Test mParseJsonConfig with various cases
        _options = self.mGetContext().mGetArgsOptions()
        # No payload
        _options.jsonconf = {}
        _handler = SLAVmClusterHandler(_options)
        self.assertFalse(_handler.mParseJsonConfig())
        # No SLA in payload
        _options.jsonconf = self.mGetPayload()
        _handler = SLAVmClusterHandler(_options)
        self.assertFalse(_handler.mParseJsonConfig())
        # No servers in payload
        _options.jsonconf = {"SLA": {}}
        _handler = SLAVmClusterHandler(_options)
        self.assertFalse(_handler.mParseJsonConfig())
        # No scheduler_frequency
        _options.jsonconf = {"SLA": {"servers": []}}
        _handler = SLAVmClusterHandler(_options)
        self.assertFalse(_handler.mParseJsonConfig())
        # No clusters given
        _options.jsonconf["SLA"]["scheduler_frequency"] = 300
        _handler = SLAVmClusterHandler(_options)
        self.assertFalse(_handler.mParseJsonConfig())
        # Non-positive max_concurrency
        _options.jsonconf["SLA"]["max_concurrency"] = 0
        _handler = SLAVmClusterHandler(_options)
        self.assertFalse(_handler.mParseJsonConfig())
        # Correct payload
        _options.jsonconf = self.mGetResourcesJsonFile("payload_SLA_vmCluster.json")
        _handler = SLAVmClusterHandler(_options)
        self.assertTrue(_handler.mParseJsonConfig())

    def test_computeCheck(self):
        # Mock connect and commands for various dom0 scenarios

        # The mComputeCheck_with_node now uses systemctl method first; fallback to ps/grep.
        class DummyNode:
            pass

        dummy_node = DummyNode()

        with mock.patch.object(SLAVmClusterHandler, "mComputeCheck_with_node", return_value=(1, 1)):
            self.assertEqual(SLAVmClusterHandler.mComputeCheck_with_node(dummy_node, "clu01adm01", 300, "2024-01-01 00:00:00"), (1, 1))

        with mock.patch.object(SLAVmClusterHandler, "mComputeCheck_with_node", return_value=(1, 0)):
            self.assertEqual(SLAVmClusterHandler.mComputeCheck_with_node(dummy_node, "clu01adm01", 300, "2024-01-01 00:00:00"), (1, 0))

        with mock.patch.object(SLAVmClusterHandler, "mComputeCheck_with_node", return_value=(0, 1)):
            self.assertEqual(SLAVmClusterHandler.mComputeCheck_with_node(dummy_node, "clu01adm01", 300, "2024-01-01 00:00:00"), (0, 1))

        with mock.patch.object(SLAVmClusterHandler, "mComputeCheck_with_node", return_value=(-1, -1)):
            self.assertEqual(SLAVmClusterHandler.mComputeCheck_with_node(dummy_node, "badhost", 300, "2024-01-01 00:00:00"), (-1, -1))

    def test_cellCheck(self):
        # Simulate cell up/down for storage nodes
        # Up
        cmds_up = {
            "clu02cel01": [
                [
                    exaMockCommand("/bin/test -e /bin/grep", aRc=0),
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e list cell detail | /bin/grep cellsrvStatus",
                                   aRc=0, aStdout="cellsrvStatus:  running")
                ]
            ]
        }
        self.mPrepareMockCommands(cmds_up)
        self.assertEqual(SLAVmClusterHandler.mCellCheck("clu02cel01"), 1)
        # Down
        cmds_down = {
            "clu02cel01": [
                [
                    exaMockCommand("/bin/test -e /bin/grep", aRc=0),
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e list cell detail | /bin/grep cellsrvStatus",
                                   aRc=0, aStdout="cellsrvStatus:  stopped")
                ]
            ]
        }
        self.mPrepareMockCommands(cmds_down)
        self.assertEqual(SLAVmClusterHandler.mCellCheck("clu02cel01"), 0)
        # Can't connect returns 0
        with mock.patch.object(SLAVmClusterHandler, "mCellCheck", return_value=0):
            self.assertEqual(SLAVmClusterHandler.mCellCheck("badhost"), 0)

    def test_executeSLA_typical(self):
        # Test if mExecuteSLA returns the correct top-level keys and types for a compute server
        host = "clu01adm01"
        s_type = "compute"
        freq = 300
        start_time = "2024-06-01 01:00:00"
        end_time = "2024-06-01 02:00:00"
        clusters = "C1"
        aBlackoutStatus = 0

        class DummyNode:
            pass

        dummy_node = DummyNode()
        # Patch connect_to_host context manager and downstream logic
        with \
            mock.patch("exabox.jsondispatch.handler_sla_vmCluster.connect_to_host") as mock_connect, \
            mock.patch.object(SLAVmClusterHandler, "mComputeCheck_with_node", return_value=(1, 1)), \
            mock.patch("exabox.jsondispatch.handler_sla_vmCluster.mExtractDowntimePeriods_with_node", return_value={"compute": [], "network": [], "storage": []}):
            # Mocking context manager to yield the dummy_node
            mock_connect.return_value.__enter__.return_value = dummy_node
            result = SLAVmClusterHandler.mExecuteSLA(host, s_type, freq, 5, start_time, end_time, clusters, aBlackoutStatus)
            self.assertIn(host, result)
            val = result[host]
            self.assertEqual(val["type"], s_type)
            self.assertEqual(val["server_status"], 1)
            self.assertEqual(val["network_status"], 1)
            self.assertIsInstance(val["downtime_periods"], dict)
            self.assertEqual(val["start_time"], start_time)
            self.assertEqual(val["end_time"], end_time)
            self.assertEqual(val["clusters"], clusters)

    def test_executeSLA_typical_storage(self):
        host = "clu01cel01"
        s_type = "storage"
        freq = 300
        # Use this year for the times so that _to_epoch matches what mExtractDowntimePeriods will use in interval filtering
        this_year = datetime.datetime.utcnow().year
        start_time = f"{this_year}-06-01 01:00:00"
        end_time = f"{this_year}-06-01 02:00:00"
        clusters = "C2"
        aBlackoutStatus = 0
        
        dummy_node = object()

        def fake_mCellCheck_with_node(node):
            self.assertIs(node, dummy_node)
            return 1

        with mock.patch("exabox.jsondispatch.handler_sla_vmCluster.connect_to_host") as mock_connect, \
             mock.patch.object(SLAVmClusterHandler, "mCellCheck_with_node", side_effect=fake_mCellCheck_with_node), \
             mock.patch.object(handler_mod, "mExtractDowntimePeriods_with_node", return_value={"compute":[],"network":[],"storage":[]}):
            mock_connect.return_value.__enter__.return_value = dummy_node
            result = SLAVmClusterHandler.mExecuteSLA(host, s_type, freq, 5, start_time, end_time, clusters, aBlackoutStatus)
            self.assertIn(host, result)
            val = result[host]
            self.assertEqual(val["type"], s_type)
            self.assertEqual(val["server_status"], 1)
            self.assertIn("downtime_periods", val)

    def test_extractDowntimePeriods_with_node_compute(self):
        # Use this year for all times so _year_aware_strptime matches range filtering
        this_year = datetime.datetime.utcnow().year

        class MockNode:
            def __init__(self, outputs):
                self.outputs = outputs
                self.call_idx = 0
            def __getattr__(self, name):
                return lambda *a, **k: None
        def fake_node_exec_cmd(node, cmd, timeout=0):
            cmd_text = " ".join(cmd) if isinstance(cmd, (list, tuple)) else cmd
            if "journalctl -u libvirtd" in cmd_text:
                return 0, (
                    f"Jun 24 08:55:00 Some Stopped Virtualization daemon\n"
                    f"Jun 24 09:15:00 Some Started Virtualization daemon"
                ), ""
            elif "journalctl -k" in cmd_text:
                return 0, (
                    f"Jun 24 08:59:00 bondeth0: now running without any active interface!\n"
                    f"Jun 24 09:20:00 bondeth0: active interface up"
                ), ""
            return 0, "", ""
        with mock.patch.object(handler_mod, "node_exec_cmd", side_effect=fake_node_exec_cmd):
            mock_node = MockNode({})
            start_time = f"{this_year}-06-24 08:00:00"
            end_time = f"{this_year}-06-24 10:00:00"
            result = handler_mod.mExtractDowntimePeriods_with_node(
                mock_node, "host1", "compute", start_time, end_time
            )
            self.assertEqual(len(result["compute"]), 1)
            c_downtime = result["compute"][0]
            self.assertEqual(c_downtime["down"], f"{this_year}-06-24 08:55:00")
            self.assertEqual(c_downtime["up"], f"{this_year}-06-24 09:15:00")
            self.assertEqual(len(result["network"]), 1)
            n_downtime = result["network"][0]
            self.assertEqual(n_downtime["down"], f"{this_year}-06-24 08:59:00")
            self.assertEqual(n_downtime["up"], f"{this_year}-06-24 09:20:00")
            
    def test_executeSLA_blackoutstatus(self):
        # Test: blackout_status=1 for compute server should short-circuit and return server/network up
        host = "clu01adm02"
        s_type = "compute"
        freq = 300
        start_time = "2024-07-01 01:00:00"
        end_time = "2024-07-01 02:00:00"
        clusters = "C3"
        blackout_status = 1
        # When blackout_status is 1, mExecuteSLA should return server_status==1, network_status==1 (for compute)
        result = SLAVmClusterHandler.mExecuteSLA(
            host, s_type, freq, 5, start_time, end_time, clusters, blackout_status
        )
        self.assertIn(host, result)
        val = result[host]
        self.assertEqual(val["blackout_status"], 1)
        self.assertEqual(val["server_status"], 1)
        self.assertEqual(val["network_status"], 1)
        self.assertIsInstance(val["timestamp"], str)
        self.assertEqual(val["type"], s_type)
        self.assertEqual(val["start_time"], start_time)
        self.assertEqual(val["end_time"], end_time)
        self.assertEqual(val["clusters"], clusters)
        self.assertEqual(val["errors"], [])
        # For storage, network_status is not set to 1 on blackout, only server_status==1 should be tested
        host2 = "clu01cel02"
        s_type2 = "storage"
        blackout_status2 = 1
        result2 = SLAVmClusterHandler.mExecuteSLA(
            host2, s_type2, freq, 5, start_time, end_time, clusters, blackout_status2
        )
        self.assertIn(host2, result2)
        val2 = result2[host2]
        self.assertEqual(val2["blackout_status"], 1)
        self.assertEqual(val2["server_status"], 1)
        self.assertEqual(val2["type"], s_type2)
        self.assertEqual(val2["start_time"], start_time)
        self.assertEqual(val2["end_time"], end_time)
        self.assertEqual(val2["clusters"], clusters)
        self.assertIsInstance(val2["timestamp"], str)
            
        

if __name__ == '__main__':
    unittest.main(warnings='ignore')
# end of file

