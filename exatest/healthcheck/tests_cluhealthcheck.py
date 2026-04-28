#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/healthcheck/tests_cluhealthcheck.py /main/1 2026/01/09 05:01:12 shapatna Exp $
#
# tests_cluhealthcheck.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_cluhealthcheck.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    joysjose    03/24/26 - Bug 38900203 :Codev fixes for exabox/healtcheck
#    aararora    03/03/26 - Bug 38902170: Correct resource leak issues
#    shapatna    01/05/26 - Creation
#
import json
import os
import tempfile
import unittest
from unittest import mock

from exabox.healthcheck.cluhealthcheck import (
    INTERNAL_ERROR_REPORT,
    SUPPORTED_NETWORKS,
    ebCluHealth,
    LOG_TYPE,
)
from exabox.healthcheck.hcutil import mReadConfigFile


class _DummyEbox(object):

    def __init__(self, network_info=None):
        self._uuid = "dummy-uuid"
        self._network_info = network_info or {}

    def mGetUUID(self):
        return self._uuid

    def mReturnAllClusterHosts(self):
        return [], [], [], []

    def mReturnDom0DomUPair(self):
        return []

    def mReturnSwitches(self, aMode=True, aRoceQinQ=False):
        return []

    def mGetNetworkSetupInformation(self, mode, dom0):
        return self._network_info.get(dom0, {})

    def mExecuteLocal(self, *args, **kwargs):
        return 0, None, "", ""

    def mGetRequestObj(self):
        return None

    def mIsOciEXACC(self):
        return False

    def mIsKVM(self):
        return False

    def mGetBasePath(self):
        return "/tmp"


class TestEbCluHealth(unittest.TestCase):

    def _bare_health(self, base_dir=None):
        health = ebCluHealth.__new__(ebCluHealth)
        base = base_dir or tempfile.mkdtemp()
        health._ebCluHealth__ebox = _DummyEbox()
        health._ebCluHealth__jsonmap = {}
        health._ebCluHealth__recommend = []
        health._ebCluHealth__profile_parser = mock.Mock()
        health._ebCluHealth__profile_parser.mGetHcConf.return_value = {}
        health._ebCluHealth__hcconfig = {"diag_root": "/tmp"}
        health._ebCluHealth__resultdir = base + os.sep
        health._ebCluHealth__loghandler = "dummy/log.log"
        health._ebCluHealth__recohandler = "dummy/reco.tmp"
        health._ebCluHealth__basepath = base
        health._ebCluHealth__confpath = os.path.join(base, "healthcheck.conf")
        health._ebCluHealth__jsonhandler = os.path.join(base, "hc.json")
        health._ebCluHealth__jsonreshandler = os.path.join(base, "hc_res.json")
        health._ebCluHealth__defloghandler = "default.log"
        health._ebCluHealth__tmp_log_destination = "tmpdest"
        health._ebCluHealth__jsonresult = []
        health._ebCluHealth__updateNetwork = {}
        health._ebCluHealth__dom0s = []
        health._ebCluHealth__domus = []
        health._ebCluHealth__cells = []
        health._ebCluHealth__switches = []
        health._ebCluHealth__deltaNetValidation = False
        health._ebCluHealth__reNetValidation = False
        health._ebCluHealth__reconfiguration = False
        health._ebCluHealth__drNet = False
        health._ebCluHealth__runningVMs = False
        health._ebCluHealth__preChecksPass = True
        health._ebCluHealth__datetime = "20240101_010101"
        health._dom0Networks = {}
        os.makedirs(base, exist_ok=True)
        os.makedirs(health._ebCluHealth__resultdir, exist_ok=True)
        with open(health._ebCluHealth__confpath, "w") as handle:
            json.dump({}, handle)
        return health

    def test_mSetUpdateNetwork_initializes_and_updates(self):
        # Auto-generated test for mSetUpdateNetwork
        health = self._bare_health()
        health.mSetUpdateNetwork("dom0-a")
        for network in SUPPORTED_NETWORKS:
            self.assertIn(network, health.mGetUpdateNetwork()["dom0-a"])
            self.assertFalse(health.mGetUpdateNetwork()["dom0-a"][network]["isReconfiguring"])
        health.mSetUpdateNetwork("dom0-a", SUPPORTED_NETWORKS[0], True, {"key": "value"})
        entry = health.mGetUpdateNetwork()["dom0-a"][SUPPORTED_NETWORKS[0]]
        self.assertTrue(entry["isReconfiguring"])
        self.assertEqual({"key": "value"}, entry["updateProperties"])

    def test_mSetUpdateNetworkServices_defaults_and_toggle(self):
        # Auto-generated test for mSetUpdateNetworkServices
        health = self._bare_health()
        health.mSetUpdateNetworkServices()
        services = health.mGetUpdateNetwork()["networkServices"]
        self.assertFalse(services["dns"])
        self.assertFalse(services["ntp"])
        health.mSetUpdateNetworkServices("dns", True)
        self.assertTrue(health.mGetUpdateNetwork()["networkServices"]["dns"])

    def test_mSetDom0Networks_collects_data_per_dom0(self):
        # Auto-generated test for mSetDom0Networks
        network_info = {"dom0-a": {"client": {"ip": "1.1.1.1"}}}
        health = self._bare_health()
        health._ebCluHealth__ebox = _DummyEbox(network_info=network_info)
        health.mSetDom0Networks(["dom0-a"])
        self.assertEqual(network_info["dom0-a"], health.mGetDom0Networks("dom0-a"))

    def test_mReadHcConfig_returns_empty_on_missing_file(self):
        # Auto-generated test for mReadHcConfig
        health = self._bare_health()
        missing_path = os.path.join(tempfile.gettempdir(), "nonexistent_hc.json")
        health._ebCluHealth__confpath = missing_path
        with mock.patch("exabox.healthcheck.cluhealthcheck.ebLogError") as log_error:
            self.assertEqual({}, health.mReadHcConfig())
        log_error.assert_called_once()

    def test_mReadHcConfig_reads_valid_json_file(self):
        # Auto-generated test for mReadHcConfig
        with tempfile.NamedTemporaryFile("w", delete=False) as handle:
            json.dump({"key": "value"}, handle)
            conf_path = handle.name
        self.addCleanup(lambda: os.path.exists(conf_path) and os.remove(conf_path))
        health = self._bare_health()
        health._ebCluHealth__confpath = conf_path
        self.assertEqual({"key": "value"}, health.mReadHcConfig())

    def test_mReadHcConfig_closes_file(self):
        health = self._bare_health()
        handle = mock.Mock()
        handle.__enter__ = mock.Mock(return_value=handle)
        handle.__exit__ = mock.Mock(return_value=False)
        with mock.patch('builtins.open', return_value=handle), \
             mock.patch('json.load', return_value={}):
            health.mReadHcConfig()
        handle.__exit__.assert_called_once()

    def test_mReadConfigFile_returns_none_and_logs_error(self):
        missing_path = os.path.join(tempfile.gettempdir(), "missing_healthcheck_profile.json")
        with mock.patch("exabox.healthcheck.hcutil.ebLogError") as log_error:
            self.assertIsNone(mReadConfigFile(missing_path))
        log_error.assert_called_once()
        self.assertIn(missing_path, log_error.call_args[0][0])

    def test_mDoHealthCheck_update_network_mismatch_sets_error(self):
        # Auto-generated test for mDoHealthCheck
        health = self._bare_health()
        health._ebCluHealth__hcconfig = {}

        class _DoHealthEbox(object):

            def mReturnAllClusterHosts(self):
                return ["dom0-a"], ["domu-a"], [], []

            def mReturnDom0DomUPair(self):
                return [("dom0-a", "domu-a")]

            def mReturnSwitches(self, aMode=True, aRoceQinQ=False):
                return []

            def mIsOciEXACC(self):
                return False

            def mIsKVM(self):
                return False

            def mGetNetworkSetupInformation(self, mode, dom0):
                return {}

            def mExecuteLocal(self, *args, **kwargs):
                return 0, None, "", ""

            def mGetBasePath(self):
                return "/tmp"

            def mGetRequestObj(self):
                return None

        health._ebCluHealth__ebox = _DoHealthEbox()
        os.makedirs(health.mGetResultDir(), exist_ok=True)
        options = mock.Mock()
        options.healthcheck = None
        options.jsonmode = False
        options.jsonconf = {
            "profile_type": "custnet_validate",
            "updateNetwork": {
                "nodes": [
                    {
                        SUPPORTED_NETWORKS[0]: {"flag": True},
                        "updateProperties": {SUPPORTED_NETWORKS[0]: {"mtu": 9000}},
                    },
                    {SUPPORTED_NETWORKS[0]: {"flag": True}},
                ],
                "networkServices": [{"op": "dnsEnable"}],
            },
            "network": {},
        }

        health.mLogCPData = mock.Mock()
        health.mUpdateRequestData = mock.Mock()
        health.mDumpJSON = mock.Mock()
        health.mZipResults = mock.Mock()

        with mock.patch("exabox.healthcheck.cluhealthcheck.get_logger") as get_logger, \
                mock.patch("exabox.healthcheck.cluhealthcheck.CheckParser") as CheckParser, \
                mock.patch("exabox.healthcheck.cluhealthcheck.ProfileParser") as ProfileParser, \
                mock.patch("exabox.healthcheck.cluhealthcheck.CheckExecutor") as CheckExecutor, \
                mock.patch("exabox.healthcheck.cluhealthcheck.mReadConfigFile", return_value={}), \
                mock.patch("exabox.healthcheck.cluhealthcheck.ebLogTrace"), \
                mock.patch("exabox.healthcheck.cluhealthcheck.ebLogHealth"), \
                mock.patch("exabox.healthcheck.cluhealthcheck.ebLogInfo"), \
                mock.patch("exabox.healthcheck.cluhealthcheck.ebLogError"), \
                mock.patch("exabox.healthcheck.cluhealthcheck.ebLogRemoveHCLogDestination"), \
                mock.patch("exabox.healthcheck.cluhealthcheck.ebLogSetHCLogDestination"):

            parser_instance = CheckParser.return_value
            parser_instance.mInitCheckParser.return_value = True

            profile_instance = ProfileParser.return_value
            profile_instance.mInitProfileParser.return_value = True
            profile_instance.buildChecklist.return_value = []
            profile_instance.mGetHcConf.return_value = {}

            executor_instance = CheckExecutor.return_value
            executor_instance.execute_checklist = mock.Mock()

            logger_instance = mock.Mock()
            logger_instance.mGetRecommend.return_value = []
            logger_instance.mAppendLog = mock.Mock()
            get_logger.return_value = logger_instance

            health.mDoHealthCheck(options)

        self.assertFalse(health.mGetPreChecksStatus())
        self.assertEqual(INTERNAL_ERROR_REPORT, health.mGetJsonMap())
        logger_instance.mAppendLog.assert_called()
        args, _ = logger_instance.mAppendLog.call_args
        self.assertEqual(LOG_TYPE.ERROR, args[0])
        self.assertTrue(
            "Nodes information" in args[1]
            or "Could not identify network info" in args[1]
        )
        self.assertFalse(health.mGetUpdateNetwork()["networkServices"]["dns"])
        self.assertNotIn("dom0-a", health.mGetUpdateNetwork())

    def test_mDoHealthCheck_update_network_success_sets_flags(self):
        # Auto-generated test for mDoHealthCheck
        health = self._bare_health()
        health._ebCluHealth__hcconfig = {}

        class _SuccessEbox(object):

            def __init__(self):
                self._network_info = {
                    "dom0-a": {
                        SUPPORTED_NETWORKS[0]: {"ip": "1.1.1.1"},
                        SUPPORTED_NETWORKS[1]: {"ip": "2.2.2.2"},
                    }
                }

            def mReturnAllClusterHosts(self):
                return ["dom0-a"], ["domu-a"], [], []

            def mReturnDom0DomUPair(self):
                return [("dom0-a", "domu-a")]

            def mReturnSwitches(self, aMode=True, aRoceQinQ=False):
                return []

            def mIsOciEXACC(self):
                return False

            def mIsKVM(self):
                return False

            def mGetNetworkSetupInformation(self, mode, dom0):
                return self._network_info.get(dom0, {})

            def mExecuteLocal(self, *args, **kwargs):
                return 0, None, "", ""

            def mGetBasePath(self):
                return "/tmp"

            def mGetRequestObj(self):
                return None

        health._ebCluHealth__ebox = _SuccessEbox()
        os.makedirs(health.mGetResultDir(), exist_ok=True)
        options = mock.Mock()
        options.healthcheck = None
        options.jsonmode = False
        options.jsonconf = {
            "profile_type": "custnet_validate",
            "updateNetwork": {
                "nodes": [
                    {
                        SUPPORTED_NETWORKS[0]: {"flag": True},
                        "updateProperties": {SUPPORTED_NETWORKS[0]: {"mtu": 9000}},
                    }
                ],
                "networkServices": [{"op": "dnsEnable"}],
            },
            "network": {},
        }

        health.mLogCPData = mock.Mock()
        health.mUpdateRequestData = mock.Mock()
        health.mDumpJSON = mock.Mock()
        health.mZipResults = mock.Mock()

        with mock.patch("exabox.healthcheck.cluhealthcheck.get_logger") as get_logger, \
                mock.patch("exabox.healthcheck.cluhealthcheck.CheckParser") as CheckParser, \
                mock.patch("exabox.healthcheck.cluhealthcheck.ProfileParser") as ProfileParser, \
                mock.patch("exabox.healthcheck.cluhealthcheck.CheckExecutor") as CheckExecutor, \
                mock.patch("exabox.healthcheck.cluhealthcheck.mReadConfigFile", return_value={}), \
                mock.patch("exabox.healthcheck.cluhealthcheck.ebLogTrace"), \
                mock.patch("exabox.healthcheck.cluhealthcheck.ebLogHealth"), \
                mock.patch("exabox.healthcheck.cluhealthcheck.ebLogInfo"), \
                mock.patch("exabox.healthcheck.cluhealthcheck.ebLogError"), \
                mock.patch("exabox.healthcheck.cluhealthcheck.ebLogRemoveHCLogDestination"), \
                mock.patch("exabox.healthcheck.cluhealthcheck.ebLogSetHCLogDestination"):

            parser_instance = CheckParser.return_value
            parser_instance.mInitCheckParser.return_value = True

            profile_instance = ProfileParser.return_value
            profile_instance.mInitProfileParser.return_value = True
            profile_instance.buildChecklist.return_value = []
            profile_instance.mGetHcConf.return_value = {}

            executor_instance = CheckExecutor.return_value
            executor_instance.execute_checklist = mock.Mock()

            logger_instance = mock.Mock()
            logger_instance.mGetRecommend.return_value = []
            logger_instance.mAppendLog = mock.Mock()
            get_logger.return_value = logger_instance

            health.mDoHealthCheck(options)

        logger_instance.mAppendLog.assert_not_called()
        self.assertTrue(health.mGetPreChecksStatus())
        self.assertTrue(health.mGetUpdateNetwork()["networkServices"]["dns"])
        dom0_entry = health.mGetUpdateNetwork()["dom0-a"][SUPPORTED_NETWORKS[0]]
        self.assertTrue(dom0_entry["isReconfiguring"])
        self.assertEqual({"mtu": 9000}, dom0_entry["updateProperties"])

    def test_mUpdateHcConfig_missing_key_logs_error(self):
        # Auto-generated test for mUpdateHcConfig
        health = self._bare_health()
        profile_conf = {"known": "value", "unknown": "value"}
        health._ebCluHealth__profile_parser.mGetHcConf.return_value = profile_conf
        health._ebCluHealth__hcconfig = {"known": "old"}
        with mock.patch("exabox.healthcheck.cluhealthcheck.ebLogError") as log_error:
            health.mUpdateHcConfig()
        self.assertEqual("value", health.mGetHcConfig()["known"])
        log_error.assert_called_once()

    def test_mUpdateRequestData_with_request_object(self):
        # Auto-generated test for mUpdateRequestData
        health = self._bare_health()
        request = mock.Mock()
        health._ebCluHealth__ebox = mock.Mock()
        health._ebCluHealth__ebox.mGetRequestObj.return_value = request
        health._ebCluHealth__jsonmap = {"key": "value"}
        with mock.patch("exabox.healthcheck.cluhealthcheck.ebGetDefaultDB") as db_mock:
            db_instance = db_mock.return_value
            health.mUpdateRequestData(mock.Mock(jsonmode=False))
        request.mSetData.assert_called_once_with(json.dumps({"key": "value"}))
        db_instance.mUpdateRequest.assert_called_once_with(request)

    def test_mUpdateRequestData_jsonmode_logs_json(self):
        # Auto-generated test for mUpdateRequestData
        health = self._bare_health()
        health._ebCluHealth__ebox = mock.Mock()
        health._ebCluHealth__ebox.mGetRequestObj.return_value = None
        health._ebCluHealth__jsonmap = {"key": "value"}
        options = mock.Mock(jsonmode=True)
        with mock.patch("exabox.healthcheck.cluhealthcheck.ebLogJson") as log_json:
            health.mUpdateRequestData(options)
        log_json.assert_called_once_with(json.dumps({"key": "value"}, indent=4))

    def test_mDumpJSON_writes_controlplane_and_checks(self):
        # Auto-generated test for mDumpJSON
        with tempfile.TemporaryDirectory() as tmp_dir:
            health = self._bare_health(tmp_dir)
            health._ebCluHealth__jsonmap = {
                "ControlPlane": {"overallStatus": "PASS"},
                "CheckA": {"target1": {"status": "OK"}},
            }
            output_path = os.path.join(tmp_dir, "hc_res.json")
            health._ebCluHealth__jsonreshandler = output_path
            with mock.patch("exabox.healthcheck.cluhealthcheck.ebLogTrace"):
                health.mDumpJSON()

            with open(output_path, "r") as fh:
                content = fh.read()

            decoder = json.JSONDecoder()
            index = 0
            lines = []
            while index < len(content):
                while index < len(content) and content[index].isspace():
                    index += 1
                if index >= len(content):
                    break
                value, index = decoder.raw_decode(content, idx=index)
                lines.append(value)

        self.assertEqual({"overallStatus": "PASS"}, lines[0])
        self.assertEqual({"status": "OK"}, lines[1])

    def test_mZipResults_creates_zip_file(self):
        # Auto-generated test for mZipResults
        with tempfile.TemporaryDirectory() as tmp_dir:
            health = self._bare_health(tmp_dir)
            result_dir = os.path.join(tmp_dir, "result")
            os.makedirs(result_dir, exist_ok=True)
            health._ebCluHealth__resultdir = result_dir + os.sep
            file_path = os.path.join(result_dir, "sample.txt")
            with open(file_path, "w") as fh:
                fh.write("content")
            health.mZipResults()
            self.assertTrue(os.path.exists(result_dir + ".zip"))

    def test_mLogCPData_exacc_records_versions_and_counts(self):
        # Auto-generated test for mLogCPData
        health = self._bare_health()
        ebox = mock.Mock()
        ebox.mIsOciEXACC.return_value = True
        ebox.mExecuteLocal.return_value = (0, None, "18.1", "")
        ebox.mGetBasePath.return_value = "/exa/base"
        health._ebCluHealth__ebox = ebox
        recommendations = [
            "CRITICAL outage detected",
            "ERROR component failed",
            "WARNING low space",
            "RECOMMEND tune setting",
        ]
        logger_stub = mock.Mock(mGetRecommend=mock.Mock(return_value=recommendations))
        options = mock.Mock()
        with mock.patch("exabox.healthcheck.cluhealthcheck.get_logger", return_value=logger_stub), \
                mock.patch("exabox.healthcheck.cluhealthcheck.exaBoxCoreInit") as core_init, \
                mock.patch("exabox.healthcheck.cluhealthcheck.get_gcontext") as ctx_mock:
            core_obj = mock.Mock()
            core_obj.mGetVersion.return_value = ("19.3", "build1")
            core_init.return_value = core_obj
            ctx_obj = mock.Mock()
            ctx_obj.mGetOEDAVersion.return_value = "5.0\n"
            ctx_mock.return_value = ctx_obj
            health.mLogCPData(options)

        control_plane = health.mGetJsonMap()["ControlPlane"]
        self.assertEqual("19.3 (build1)", control_plane["exacloudVersion"])
        self.assertEqual("5.0", control_plane["oedaVersion"])
        self.assertEqual("18.1", control_plane["cpsImageVersion"])
        self.assertEqual(1, control_plane["totalCriticals"])
        self.assertEqual(1, control_plane["totalErrors"])
        self.assertEqual(1, control_plane["totalWarnings"])
        self.assertEqual(1, control_plane["totalRecommends"])
        self.assertEqual("FAIL", control_plane["overallStatus"])
        ebox.mExecuteLocal.assert_called_once_with(
            "sudo /usr/local/bin/imageinfo -ver", aCurrDir="/exa/base"
        )

    def test_mLogCPData_standard_flow_pass_status(self):
        # Auto-generated test for mLogCPData
        health = self._bare_health()
        ebox = mock.Mock()
        ebox.mIsOciEXACC.return_value = False
        health._ebCluHealth__ebox = ebox
        logger_stub = mock.Mock(mGetRecommend=mock.Mock(return_value=[]))
        options = mock.Mock()
        with mock.patch("exabox.healthcheck.cluhealthcheck.get_logger", return_value=logger_stub), \
                mock.patch("exabox.healthcheck.cluhealthcheck.exaBoxCoreInit") as core_init, \
                mock.patch("exabox.healthcheck.cluhealthcheck.get_gcontext") as ctx_mock:
            core_obj = mock.Mock()
            core_obj.mGetVersion.return_value = ("20.1", "release")
            core_init.return_value = core_obj
            ctx_obj = mock.Mock()
            ctx_obj.mGetOEDAVersion.return_value = "7.1\n"
            ctx_mock.return_value = ctx_obj
            health.mLogCPData(options)

        control_plane = health.mGetJsonMap()["ControlPlane"]
        self.assertEqual("20.1 (release)", control_plane["exacloudVersion"])
        self.assertEqual("7.1", control_plane["oedaVersion"])
        self.assertEqual(0, control_plane["totalCriticals"])
        self.assertEqual(0, control_plane["totalErrors"])
        self.assertEqual(0, control_plane["totalWarnings"])
        self.assertEqual(0, control_plane["totalRecommends"])
        self.assertEqual("PASS", control_plane["overallStatus"])
        ebox.mExecuteLocal.assert_not_called()

    def test_mSetLogPaths_network_validation_uses_network_name(self):
        # Auto-generated test for mSetLogPaths
        health = self._bare_health()
        options = mock.Mock()
        options.jsonconf = {
            "profile_type": "custnet_validate",
            "network": {"network_name": "CUSTOM_NET"},
        }

        with mock.patch.object(
            health,
            "mCheckIfNetworkValidation",
            return_value=True,
        ) as mock_check:
            health.mSetLogPaths(options, "cluster-1")

        expected_prefix = health.mGetEbox().mGetUUID() + "/healthcheck-CUSTOM_NET-"
        self.assertTrue(health.mGetLogHandler().startswith(expected_prefix))
        self.assertIn("hc_CUSTOM_NET_", health.mGetJsonResHandler())
        self.assertIn("-healthcheck-CUSTOM_NET.json", health.mGetJsonHandler())
        mock_check.assert_has_calls([mock.call(options)] * 2)

    def test_mSetLogPaths_standard_flow_uses_cluster_name(self):
        # Auto-generated test for mSetLogPaths
        health = self._bare_health()
        options = mock.Mock()
        options.jsonconf = {
            "profile_type": "standard",
            "network": {},
        }

        with mock.patch.object(
            health,
            "mCheckIfNetworkValidation",
            return_value=False,
        ) as mock_check:
            health.mSetLogPaths(options, "cluster-2")

        expected_prefix = health.mGetEbox().mGetUUID() + "/healthcheck-cluster-2-"
        self.assertTrue(health.mGetLogHandler().startswith(expected_prefix))
        self.assertIn("hc_cluster-2_", health.mGetJsonResHandler())
        self.assertIn("healthcheck-cluster-2-", health.mGetJsonHandler())
        mock_check.assert_has_calls([mock.call(options)] * 2)

    def test_mCheckIfNetworkValidation_returns_true_for_supported_profiles(self):
        # Auto-generated test for mCheckIfNetworkValidation
        health = self._bare_health()

        for profile in ["custnet_validate", "custnet_revalidate", "nw_vldn_testsuite"]:
            options = mock.Mock()
            options.jsonconf = {
                "profile_type": profile,
                "network": {"network_name": "N1"},
            }
            self.assertTrue(health.mCheckIfNetworkValidation(options))

    def test_mCheckIfNetworkValidation_returns_false_when_missing_network(self):
        # Auto-generated test for mCheckIfNetworkValidation
        health = self._bare_health()
        options = mock.Mock()
        options.jsonconf = {"profile_type": "custnet_validate", "network": {}}
        self.assertFalse(health.mCheckIfNetworkValidation(options))

    def test_mCheckIfNetworkValidation_returns_false_for_invalid_profiles(self):
        # Auto-generated test for mCheckIfNetworkValidation
        health = self._bare_health()
        options = mock.Mock()
        options.jsonconf = {"profile_type": "something_else", "network": {"k": "v"}}
        self.assertFalse(health.mCheckIfNetworkValidation(options))

    def test_simple_setters_assign_values(self):
        # Auto-generated test suite for simple setters
        health = self._bare_health()
        self.assertEqual([], health.mGetDom0s())
        health.mSetDom0s(["dom0"])
        self.assertEqual(["dom0"], health.mGetDom0s())

        self.assertEqual([], health.mGetDomUs())
        health.mSetDomUs(["domu"])
        self.assertEqual(["domu"], health.mGetDomUs())

        self.assertEqual([], health.mGetCells())
        health.mSetCells(["cell"])
        self.assertEqual(["cell"], health.mGetCells())

        self.assertEqual([], health.mGetSwitches())
        health.mSetSwitches(["switch"])
        self.assertEqual(["switch"], health.mGetSwitches())

        self.assertFalse(health.mGetDeltaNetValidation())
        health.mSetDeltaNetValidation(True)
        self.assertTrue(health.mGetDeltaNetValidation())

        self.assertFalse(health.mGetReNetValidation())
        health.mSetReNetValidation(True)
        self.assertTrue(health.mGetReNetValidation())

        self.assertFalse(health.mGetReconfiguration())
        health.mSetReconfiguration(True)
        self.assertTrue(health.mGetReconfiguration())

        self.assertFalse(health.mGetAnyRunningVMs())
        health.mSetAnyRunningVMs(True)
        self.assertTrue(health.mGetAnyRunningVMs())

        self.assertFalse(health.mGetDrNetConfigured())
        health.mSetDrNetConfigured(True)
        self.assertTrue(health.mGetDrNetConfigured())


if __name__ == "__main__":
    unittest.main()
