#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/healthcheck/tests_check_executor.py /main/3 2026/01/12 18:01:24 joysjose Exp $
#
# tests_check_executor.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_check_executor.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    joysjose    01/11/26 - Codex UT iteration 1
#    aypaul      12/09/25 - Bug#38736166 Enhance code coverage with Cline
#    bhpati      07/31/25 - Bug 38102552 - OCI: ECRA WORKFLOW FOR
#                           CLUCTRL.CHECKCLUSTER SHOULD RETURN ERROR IF Node IS
#                           NOT REACHABLE
#    bhpati      07/31/25 - Creation
#
import copy
import json
import unittest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo, ebLogWarn, ebLogError
from unittest.mock import MagicMock, patch
from exabox.healthcheck.hclogger import get_logger, init_logging
from exabox.healthcheck.check_executor import Finalize
import warnings

class TestFinalize(unittest.TestCase):

    def setUp(self):
        self.result_dict = {
        '1419976_results': ['exception: GetNode failed to get Connection for root@scaqab10celadm01.us.oracle.com'],
        '1419976_log1': ['Check ImageVersion, could not complete execution, exception: GetNode failed to get Connection for root@scaqab10celadm01.us.oracle.com'],
        '1419976_recommend': ['value5']
        }
        self.finalize = Finalize(self.result_dict)

    def test_finalize_results(self):
        pid = '1419976'
        result = self.finalize.finalize_results(pid)
        self.assertEqual(result, ['value5'])

    def test_extract_list(self):
        result_dict = {'1419976_log1': ['Check ImageVersion, could not complete execution, exception: GetNode failed to get Connection for root@scaqab10celadm01.us.oracle.com']}
        result = self.finalize.extract_list(result_dict)
        self.assertEqual(result, ['Check ImageVersion, could not complete execution, exception: GetNode failed to get Connection for root@scaqab10celadm01.us.oracle.com'])

    def test_getfilteredict(self):
        pid = '1419976'
        filter_str = '_results'
        result = self.finalize.getfilteredict(pid, filter_str)
        self.assertEqual(result, {'1419976_results': ['exception: GetNode failed to get Connection for root@scaqab10celadm01.us.oracle.com']})

    @patch('exabox.healthcheck.hclogger.get_logger')
    @patch('exabox.log.LogMgr.ebLogError')
    def test_update_results(self, mock_ebLogError, mock_get_logger):
        result_dict = {
        '1419976_log1': [
            'Check ImageVersion, could not complete execution, exception: GetNode failed to get Connection for root@scaqab10celadm01.us.oracle.com'
        ]}
        self.finalize.update_results(result_dict)


class DummyProcessStructure:
    def __init__(self, target, args):
        self._target = target
        self._args = args
        self._max_time = None
        self._join_timeout = None
        self._log_timeout_fx = None

    def mSetMaxExecutionTime(self, value):
        self._max_time = value

    def mSetJoinTimeout(self, value):
        self._join_timeout = value

    def mSetLogTimeoutFx(self, value):
        self._log_timeout_fx = value

    def get_target(self):
        return self._target

    def get_args(self):
        return self._args

    def get_max_time(self):
        return self._max_time

    def get_join_timeout(self):
        return self._join_timeout

    def get_log_timeout_fx(self):
        return self._log_timeout_fx


class DummyManager:
    def __init__(self):
        self.storage = {}

    def dict(self):
        return self.storage


class DummyProcessManager:
    def __init__(self):
        self.appended = []
        self.join_called = False

    @classmethod
    def clear_instances(cls):
        return None

    def mStartAppend(self, proc_struct):
        self.appended.append(proc_struct)

    def mJoinProcess(self):
        self.join_called = True


# =========================
# Auto-generated tests begin
# =========================

import types
from unittest import mock
from unittest.mock import Mock, patch
import exabox.healthcheck.check_executor as check_executor
from exabox.healthcheck.hcconstants import HcConstants, CHK_RESULT

class _DummyLogger:
    def __init__(self):
        self.updated = []
        self.recommend = ["rec1"]
    def mGetResultTemplate(self):
        # Minimal template containing all fields referenced by executor/tasks
        return {
            HcConstants.RES_HCID: "",
            HcConstants.RES_CHKNAME: "",
            HcConstants.RES_PROFILE: "",
            HcConstants.RES_ALERTTYPE: "",
            HcConstants.RES_NODETYPE: "",
            HcConstants.RES_NODENAME: "",
            HcConstants.RES_CHECKPARAM: {},
            HcConstants.RES_RESULT: "",
            HcConstants.RES_LOG: [],
            HcConstants.RES_MSGDETAIL: {},
            HcConstants.RES_STARTTIME: "",
            HcConstants.RES_ENDTIME: "",
        }
    def mGetRecommend(self):
        return list(self.recommend)
    def mSetRecommend(self, lst):
        self.recommend = list(lst)
    def mUpdateJsonMap(self, value):
        self.updated.append(value)

class _DummyCheckClass:
    def __init__(self, ebox, hc):
        self._ebox = ebox
        self._hc = hc
    # Accept optional params and host signatures to match executor call variants
    def mCheckDemo(self, *args, **kwargs):
        return {
            HcConstants.RES_RESULT: CHK_RESULT.PASS,
            HcConstants.RES_LOG: ["ok"],
            HcConstants.RES_MSGDETAIL: {"key": "val"},
        }
    def mCleanUp(self):
        return None

class _DummyParser:
    def __init__(self):
        self._check_list = { "CHK_1": { HcConstants.CHK_NAME: "Demo" } }
    def mGetCheckList(self):
        return self._check_list
    def mGetTargetList(self):
        return [HcConstants.DOM0]
    def mGetCheckTargetList(self, chkid):
        return [HcConstants.DOM0]
    def mGetCheckName(self, chkid):
        return "Demo"
    def mGetCheckAlertLevel(self, chkid):
        return "INFO"

class _DummyProfile:
    def mGetProfileTargetList(self):
        return [HcConstants.ALL]
    def mGetProfileName(self):
        return "default"
    def mGetCheckParamForId(self, chkid):
        return {}

class _DummyEbox:
    def mGetVerbose(self): return False
    def mCheckConfigOption(self, key): return None
    # For NodeTask host list providers
    def mGetDom0s(self): return ["dom0-1"]
    def mGetDomUs(self): return ["domu-1", "domu-2"]
    def mGetCells(self): return ["cell-1"]
    def mGetSwitches(self): return ["switch-1"]

class _DummyVerboseEbox(_DummyEbox):
    def __init__(self, timeout_value=None):
        self._timeout_value = timeout_value

    def mGetVerbose(self):
        return True

    def mCheckConfigOption(self, key):
        return self._timeout_value

class _DummyHC:
    def __init__(self, ebox=None, custom=None):
        self._ebox = ebox or _DummyEbox()
        self._parser = _DummyParser()
        self._profile = _DummyProfile()
        self._custom = custom if custom is not None else {"CustomCheck": "echo OK"}
    def mGetEbox(self): return self._ebox
    def mGetCheckParser(self): return self._parser
    def mGetProfileParser(self): return self._profile
    def mGetCheckList(self): return list(self._parser.mGetCheckList().keys())
    def mGetCustomCheckList(self): return self._custom
    def mReturnCellNodes(self): return {"cell-1": object()}
    def mReturnDom0DomUPair(self): return [("dom0-1", "domu-1")]
    # Methods expected by NodeTask.mGetHostList
    def mGetDom0s(self): return ["dom0-1"]
    def mGetDomUs(self): return ["domu-1", "domu-2"]
    def mGetCells(self): return ["cell-1"]
    def mGetSwitches(self): return ["switch-1"]

class TestObjectStoreBasics(unittest.TestCase):
    def test_create_get_delete_instances(self):
        hc = _DummyHC()
        with patch.object(check_executor, "REGISTERED_CLASSES", [_DummyCheckClass]):
            store = check_executor.ObjectStore(hc)
            inst = store.mGetInstance("_DummyCheckClass")
            self.assertIsInstance(inst, _DummyCheckClass)
            store.mDeleteInstance()  # Should not raise

class TestHCTaskExecutePaths(unittest.TestCase):
    def setUp(self):
        self.logger = _DummyLogger()
        self.p_get_logger = patch("exabox.healthcheck.check_executor.get_logger", return_value=self.logger)
        self.p_get_logger.start()
        # Force serial execution branches
        check_executor.gRunExecutorParallel = False
        check_executor.gRunNodeTaskParallel = False
        check_executor.gRunCustomTaskParallel = False

    def tearDown(self):
        self.p_get_logger.stop()

    def _mk_subtask(self, fp):
        tmpl = self.logger.mGetResultTemplate()
        # Ensure required fields that are rewritten are present
        tmpl[HcConstants.RES_CHECKPARAM] = {}
        tmpl[HcConstants.RES_CHKNAME] = "Demo"
        return {"fp": fp, "result": tmpl}

    def test_execute_success_dict_return(self):
        task = check_executor.HCTask(_DummyHC(), [self._mk_subtask(lambda: {
            HcConstants.RES_RESULT: CHK_RESULT.PASS,
            HcConstants.RES_LOG: ["L"],
            HcConstants.RES_MSGDETAIL: {"k": "v"},
            HcConstants.RES_CHECKPARAM: {},
        })])
        res = {}
        res["pids"] = [""]
        task.execute(res)
        # Locate first results entry
        keys = [k for k in res.keys() if k.endswith("_results1")]
        self.assertTrue(keys, "Expected a _results1 key in results")
        self.assertEqual(res[keys[0]][HcConstants.RES_RESULT], "PASS")

    def test_execute_with_check_params(self):
        # Auto-generated test for HCTask.execute
        def fp(params):
            self.assertEqual(params, {"flag": True})
            return {
                HcConstants.RES_RESULT: CHK_RESULT.PASS,
                HcConstants.RES_LOG: ["param"],
                HcConstants.RES_MSGDETAIL: {"seen": True},
                HcConstants.RES_CHECKPARAM: params,
            }

        tmpl = self.logger.mGetResultTemplate()
        tmpl[HcConstants.RES_CHKNAME] = "Demo"
        tmpl[HcConstants.RES_CHECKPARAM] = {"flag": True}
        task = check_executor.HCTask(_DummyHC(), [{"fp": fp, "result": tmpl}])
        res = {"pids": [""]}
        task.execute(res)
        keys = [k for k in res.keys() if k.endswith("_results1")]
        self.assertTrue(keys)
        entry = res[keys[0]]
        self.assertEqual(entry[HcConstants.RES_RESULT], "PASS")
        self.assertEqual(entry[HcConstants.RES_LOG], ["param"])

    def test_execute_with_host_option_no_params(self):
        # Auto-generated test for HCTask.execute
        captured = []

        def fp(host):
            captured.append(host)
            return {
                HcConstants.RES_RESULT: CHK_RESULT.PASS,
                HcConstants.RES_LOG: [host],
                HcConstants.RES_MSGDETAIL: {},
                HcConstants.RES_CHECKPARAM: {},
            }

        tmpl = self.logger.mGetResultTemplate()
        tmpl[HcConstants.RES_CHKNAME] = "Demo"
        tmpl[HcConstants.RES_CHECKPARAM] = {}
        task = check_executor.HCTask(_DummyHC(), [{"fp": fp, "result": tmpl}])
        res = {"pids": [""]}
        task.execute(res, {"host": "dom0-1"})
        self.assertEqual(captured, ["dom0-1"])
        keys = [k for k in res.keys() if k.endswith("_results1")]
        self.assertTrue(keys)

    def test_execute_with_host_option_with_params(self):
        # Auto-generated test for HCTask.execute
        captured = []

        def fp(host, params):
            captured.append((host, params))
            return {
                HcConstants.RES_RESULT: CHK_RESULT.PASS,
                HcConstants.RES_LOG: [host],
                HcConstants.RES_MSGDETAIL: params,
                HcConstants.RES_CHECKPARAM: params,
            }

        tmpl = self.logger.mGetResultTemplate()
        tmpl[HcConstants.RES_CHKNAME] = "Demo"
        tmpl[HcConstants.RES_CHECKPARAM] = {"mode": "full"}
        task = check_executor.HCTask(_DummyHC(), [{"fp": fp, "result": tmpl}])
        res = {"pids": [""]}
        task.execute(res, {"host": "dom0-1"})
        self.assertEqual(captured, [("dom0-1", {"mode": "full"})])

    def test_execute_with_cmdstr_option(self):
        # Auto-generated test for HCTask.execute
        seen = []

        def fp(cmd):
            seen.append(cmd)
            return {
                HcConstants.RES_RESULT: CHK_RESULT.PASS,
                HcConstants.RES_LOG: [cmd],
                HcConstants.RES_MSGDETAIL: {},
                HcConstants.RES_CHECKPARAM: {},
            }

        tmpl = self.logger.mGetResultTemplate()
        tmpl[HcConstants.RES_CHKNAME] = "ShouldOverwrite"
        tmpl[HcConstants.RES_CHECKPARAM] = {}
        task = check_executor.HCTask(_DummyHC(), [{"fp": fp, "result": tmpl}])
        res = {"pids": [""]}
        task.execute(res, {"checkname": "CustomCheck", "cmdstr": "echo hi"})
        self.assertEqual(seen, ["echo hi"])
        keys = [k for k in res.keys() if k.endswith("_results1")]
        self.assertTrue(keys)
        entry = res[keys[0]]
        self.assertEqual(entry[HcConstants.RES_CHKNAME], "CustomCheck")

    @patch("exabox.healthcheck.check_executor.ebLogError")
    def test_execute_missing_result_fields(self, mock_log):
        # Auto-generated test for HCTask.execute
        tmpl = self.logger.mGetResultTemplate()
        tmpl[HcConstants.RES_CHKNAME] = "Demo"
        tmpl[HcConstants.RES_CHECKPARAM] = {}
        task = check_executor.HCTask(_DummyHC(), [{"fp": lambda: {HcConstants.RES_RESULT: CHK_RESULT.PASS}, "result": tmpl}])
        res = {"pids": [""]}
        task.execute(res)
        mock_log.assert_called()

    def test_execute_integer_return_branch(self):
        # Auto-generated test for HCTask.execute
        tmpl = self.logger.mGetResultTemplate()
        tmpl[HcConstants.RES_CHKNAME] = "Demo"
        tmpl[HcConstants.RES_CHECKPARAM] = {}
        task = check_executor.HCTask(_DummyHC(), [{"fp": lambda: 0, "result": tmpl}])
        res = {"pids": [""]}
        task.execute(res)
        keys = [k for k in res.keys() if k.endswith("_results1")]
        self.assertTrue(keys)
        self.assertEqual(res[keys[0]][HcConstants.RES_RESULT], "PASS")

    @patch("exabox.healthcheck.check_executor.ebLogError")
    def test_execute_invalid_return_type(self, mock_log):
        # Auto-generated test for HCTask.execute
        tmpl = self.logger.mGetResultTemplate()
        tmpl[HcConstants.RES_CHKNAME] = "Demo"
        tmpl[HcConstants.RES_CHECKPARAM] = {}

        def fp():
            return "unexpected"

        task = check_executor.HCTask(_DummyHC(), [{"fp": fp, "result": tmpl}])
        res = {"pids": [""]}
        task.execute(res)
        mock_log.assert_called()
        keys = [k for k in res.keys() if k.endswith("_results1")]
        entry = res[keys[0]]
        self.assertEqual(entry[HcConstants.RES_RESULT], "FAIL")

    def test_execute_with_host_option_no_params(self):
        # Auto-generated test for HCTask.execute
        captured = []

        def fp(host):
            captured.append(host)
            return {
                HcConstants.RES_RESULT: CHK_RESULT.PASS,
                HcConstants.RES_LOG: [host],
                HcConstants.RES_MSGDETAIL: {},
            }

        tmpl = self.logger.mGetResultTemplate()
        tmpl[HcConstants.RES_CHKNAME] = "Demo"
        tmpl[HcConstants.RES_CHECKPARAM] = {}
        task = check_executor.HCTask(_DummyHC(), [{"fp": fp, "result": tmpl}])
        res = {"pids": [""]}
        task.execute(res, {"host": "dom0-1"})
        self.assertEqual(captured, ["dom0-1"])

    def test_execute_with_host_option_with_params(self):
        # Auto-generated test for HCTask.execute
        captured = []

        def fp(host, params):
            captured.append((host, params))
            return {
                HcConstants.RES_RESULT: CHK_RESULT.PASS,
                HcConstants.RES_LOG: [host],
                HcConstants.RES_MSGDETAIL: params,
            }

        tmpl = self.logger.mGetResultTemplate()
        tmpl[HcConstants.RES_CHKNAME] = "Demo"
        tmpl[HcConstants.RES_CHECKPARAM] = {"mode": "full"}
        task = check_executor.HCTask(_DummyHC(), [{"fp": fp, "result": tmpl}])
        res = {"pids": [""]}
        task.execute(res, {"host": "dom0-1"})
        self.assertEqual(captured, [("dom0-1", {"mode": "full"})])

    def test_execute_with_cmdstr_option(self):
        # Auto-generated test for HCTask.execute
        seen = []

        def fp(cmd):
            seen.append(cmd)
            return {
                HcConstants.RES_RESULT: CHK_RESULT.PASS,
                HcConstants.RES_LOG: [cmd],
                HcConstants.RES_MSGDETAIL: {},
            }

        tmpl = self.logger.mGetResultTemplate()
        tmpl[HcConstants.RES_CHKNAME] = "ShouldOverwrite"
        tmpl[HcConstants.RES_CHECKPARAM] = {}
        task = check_executor.HCTask(_DummyHC(), [{"fp": fp, "result": tmpl}])
        res = {"pids": [""]}
        task.execute(res, {"checkname": "CustomCheck", "cmdstr": "echo hi"})
        self.assertEqual(seen, ["echo hi"])

    @patch("exabox.healthcheck.check_executor.ebLogError")
    def test_execute_missing_result_fields(self, mock_log):
        # Auto-generated test for HCTask.execute
        tmpl = self.logger.mGetResultTemplate()
        tmpl[HcConstants.RES_CHKNAME] = "Demo"
        tmpl[HcConstants.RES_CHECKPARAM] = {}
        task = check_executor.HCTask(_DummyHC(), [{"fp": lambda: {HcConstants.RES_RESULT: CHK_RESULT.PASS}, "result": tmpl}])
        res = {"pids": [""]}
        task.execute(res)
        mock_log.assert_called()

    def test_execute_integer_return_branch(self):
        # Auto-generated test for HCTask.execute
        tmpl = self.logger.mGetResultTemplate()
        tmpl[HcConstants.RES_CHKNAME] = "Demo"
        tmpl[HcConstants.RES_CHECKPARAM] = {}

        def fp():
            return CHK_RESULT.PASS

        task = check_executor.HCTask(_DummyHC(), [{"fp": fp, "result": tmpl}])
        res = {"pids": [""]}
        task.execute(res)
        keys = [k for k in res.keys() if k.endswith("_results1")]
        self.assertTrue(keys)
        self.assertEqual(res[keys[0]][HcConstants.RES_RESULT], "PASS")

    @patch("exabox.healthcheck.check_executor.ebLogError")
    def test_execute_invalid_return_type(self, mock_log):
        # Auto-generated test for HCTask.execute
        tmpl = self.logger.mGetResultTemplate()
        tmpl[HcConstants.RES_CHKNAME] = "Demo"
        tmpl[HcConstants.RES_CHECKPARAM] = {}

        def fp():
            return "unexpected"

        task = check_executor.HCTask(_DummyHC(), [{"fp": fp, "result": tmpl}])
        res = {"pids": [""]}
        task.execute(res)
        mock_log.assert_called()
        keys = [k for k in res.keys() if k.endswith("_results1")]
        entry = res[keys[0]]
        self.assertEqual(entry[HcConstants.RES_RESULT], "FAIL")

    def test_execute_integer_result(self):
        # Auto-generated test for HCTask.execute
        task = check_executor.HCTask(_DummyHC(), [self._mk_subtask(lambda: CHK_RESULT.FAIL)])
        res = {"pids": [""]}
        task.execute(res)
        keys = [k for k in res.keys() if k.endswith("_results1")]
        self.assertTrue(keys)
        self.assertEqual(res[keys[0]][HcConstants.RES_RESULT], "FAIL")

    @patch("exabox.healthcheck.check_executor.ebLogError")
    def test_execute_exception_sets_fail(self, mock_log):
        def boom():
            raise RuntimeError("bad")
        task = check_executor.HCTask(_DummyHC(), [self._mk_subtask(boom)])
        res = {}
        res["pids"] = [""]
        task.execute(res)
        keys = [k for k in res.keys() if k.endswith("_results1")]
        self.assertTrue(keys, "Expected a _results1 key in results")
        self.assertEqual(res[keys[0]][HcConstants.RES_RESULT], "FAIL")

    def test_parallel_execution_uses_process_manager(self):
        class StubCheckModule:
            def __init__(self):
                self.calls = []

            def mCheckDemo(self, *args, **kwargs):
                self.calls.append((args, kwargs))
                return {
                    HcConstants.RES_RESULT: CHK_RESULT.PASS,
                    HcConstants.RES_LOG: [],
                    HcConstants.RES_MSGDETAIL: {},
                }

            def mCleanUp(self):
                return None

        class StubObjectStore:
            def __init__(self, hc):
                self._stub = StubCheckModule()

            def mGetInstance(self, name):
                return self._stub

            def mDeleteInstance(self):
                return None

        class VerboseTimeoutEbox(_DummyEbox):
            def __init__(self, timeout_value=321):
                self._timeout_value = timeout_value

            def mGetVerbose(self):
                return True

            def mCheckConfigOption(self, key):
                return self._timeout_value

        class TestProcessManager(DummyProcessManager):
            def mStartAppend(self, proc_struct):
                super(TestProcessManager, self).mStartAppend(proc_struct)
                target = proc_struct.get_target()
                args = proc_struct.get_args()
                target(*args)

            def mJoinProcess(self):
                self.join_called = True

        DummyProcessManager.clear_instances()
        original_map = check_executor.CheckExecutor._checkIdToFuncMap
        original_reverse_map = check_executor.CheckExecutor._funcToCheckIdMap
        check_executor.CheckExecutor._checkIdToFuncMap = {"CHK_1": "Stub.mCheckDemo"}
        check_executor.CheckExecutor._funcToCheckIdMap = {"Stub.mCheckDemo": "CHK_1"}

        executor = check_executor.CheckExecutor.__new__(check_executor.CheckExecutor)
        executor._hc = _DummyHC(ebox=VerboseTimeoutEbox())
        executor._objCheckParser = executor._hc.mGetCheckParser()
        executor._objProfileParser = executor._hc.mGetProfileParser()
        executor._CheckList = ["CHK_1"]
        executor.resdict = DummyManager().dict()
        executor.resdict["pids"] = [""]

        check_executor.gRunExecutorParallel = True
        check_executor.gRunNodeTaskParallel = False
        check_executor.gRunCustomTaskParallel = False

        with patch.object(check_executor, "ProcessManager") as pm_ctor, \
             patch.object(check_executor, "ProcessStructure", DummyProcessStructure), \
             patch("exabox.healthcheck.check_executor.Manager", return_value=DummyManager()), \
             patch.object(check_executor, "ObjectStore", StubObjectStore):
            manager_mock = pm_ctor.return_value

            def capture(proc_struct):
                captured.append(proc_struct)
                target = proc_struct.get_target()
                args = proc_struct.get_args()
                target(*args)

            captured = []
            manager_mock.mStartAppend.side_effect = capture
            manager_mock.mJoinProcess.side_effect = lambda: None

            executor.execute_checklist()

            self.assertTrue(captured)
            for proc in captured:
                self.assertIs(proc.get_log_timeout_fx(), ebLogWarn)
                self.assertEqual(proc.get_join_timeout(), 5)
                self.assertEqual(proc.get_max_time(), 321)
            self.assertTrue(manager_mock.mJoinProcess.called)

        check_executor.CheckExecutor._checkIdToFuncMap = original_map
        check_executor.CheckExecutor._funcToCheckIdMap = original_reverse_map
        check_executor.gRunExecutorParallel = False

class TestNodeTaskOtherCustom(unittest.TestCase):
    def setUp(self):
        self.logger = _DummyLogger()
        self.p_get_logger = patch("exabox.healthcheck.check_executor.get_logger", return_value=self.logger)
        self.p_get_logger.start()
        check_executor.gRunNodeTaskParallel = False
        check_executor.gRunCustomTaskParallel = False

    def tearDown(self):
        self.p_get_logger.stop()

    def test_mGetHostList_variants(self):
        hc = _DummyHC()
        # DOM0
        t = check_executor.NodeTask(hc, HcConstants.DOM0, [])
        self.assertEqual(t.mGetHostList(), ["dom0-1"])
        # DOMU
        t = check_executor.NodeTask(hc, HcConstants.DOMU, [])
        self.assertEqual(t.mGetHostList(), ["domu-1", "domu-2"])
        # CELL
        t = check_executor.NodeTask(hc, HcConstants.CELL, [])
        self.assertEqual(t.mGetHostList(), ["cell-1"])
        # SWITCH
        t = check_executor.NodeTask(hc, HcConstants.SWITCH, [])
        self.assertEqual(t.mGetHostList(), ["switch-1"])

    def test_other_task_execute_delegates(self):
        hc = _DummyHC()
        # Subtask returns PASS dict
        st = {"fp": lambda: {
            HcConstants.RES_RESULT: CHK_RESULT.PASS,
            HcConstants.RES_LOG: [],
            HcConstants.RES_MSGDETAIL: {},
            HcConstants.RES_CHECKPARAM: {},
        }, "result": self.logger.mGetResultTemplate()}
        t = check_executor.OtherTask(hc, "OTHER", [st])
        res = {}
        res["pids"] = [""]
        t.execute(res)
        keys = [k for k in res.keys() if k.endswith("_results1")]
        self.assertTrue(keys)

    def test_custom_task_none_list(self):
        hc = _DummyHC()
        hc._custom = None
        t = check_executor.CustomTask(hc, HcConstants.CUSTOMCHECK, [])
        res = {}
        # Should be a no-op
        t.execute(res)

    def test_node_task_parallel_execution(self):
        # Auto-generated test for NodeTask.execute
        hc = _DummyHC(ebox=_DummyVerboseEbox(timeout_value=432))
        subtask = self.logger.mGetResultTemplate()
        subtask[HcConstants.RES_CHKNAME] = "Demo"
        task = check_executor.NodeTask(hc, HcConstants.DOM0, [{
            "fp": lambda host, params=None: {
                HcConstants.RES_RESULT: CHK_RESULT.PASS,
                HcConstants.RES_LOG: [host],
                HcConstants.RES_MSGDETAIL: {},
                HcConstants.RES_CHECKPARAM: params or {},
            },
            "result": copy.deepcopy(subtask),
        }])
        res = {"pids": [""]}
        check_executor.gRunNodeTaskParallel = True
        self.addCleanup(setattr, check_executor, "gRunNodeTaskParallel", False)
        with patch.object(check_executor, "ProcessManager", return_value=DummyProcessManager()) as pm_ctor, \
             patch.object(check_executor, "ProcessStructure", DummyProcessStructure):
            task.execute(res)
            manager = pm_ctor.return_value
            self.assertTrue(manager.appended)
            self.assertTrue(manager.join_called)
            for proc_struct in manager.appended:
                target = proc_struct.get_target()
                args = proc_struct.get_args()
                target(*args)
            keys = [k for k in res.keys() if k.endswith("_results1")]
            self.assertTrue(keys)

    def test_custom_task_parallel_execution(self):
        # Auto-generated test for CustomTask.execute
        hc = _DummyHC()
        hc._custom = {"CustomCheck": "echo hi"}
        subtask = self.logger.mGetResultTemplate()
        subtask[HcConstants.RES_CHKNAME] = "CustomCheck"
        task = check_executor.CustomTask(hc, HcConstants.CUSTOMCHECK, [{
            "fp": lambda cmd, params=None: {
                HcConstants.RES_RESULT: CHK_RESULT.PASS,
                HcConstants.RES_LOG: [cmd],
                HcConstants.RES_MSGDETAIL: {},
                HcConstants.RES_CHECKPARAM: params or {},
            },
            "result": copy.deepcopy(subtask),
        }])
        res = {"pids": [""]}
        check_executor.gRunCustomTaskParallel = True
        self.addCleanup(setattr, check_executor, "gRunCustomTaskParallel", False)
        with patch.object(check_executor, "ProcessManager", return_value=DummyProcessManager()) as pm_ctor, \
             patch.object(check_executor, "ProcessStructure", DummyProcessStructure):
            task.execute(res)
            manager = pm_ctor.return_value
            self.assertTrue(manager.appended)
            self.assertTrue(manager.join_called)
            for proc_struct in manager.appended:
                target = proc_struct.get_target()
                args = proc_struct.get_args()
                target(*args)
                
            keys = [k for k in res.keys() if k.endswith("_results1")]
            self.assertTrue(keys)

class TestCheckExecutorEndToEnd(unittest.TestCase):
    def setUp(self):
        self.logger = _DummyLogger()
        self.p_get_logger = patch("exabox.healthcheck.check_executor.get_logger", return_value=self.logger)
        self.p_get_logger.start()
        # Serial execution for deterministic behavior
        check_executor.gRunExecutorParallel = False
        check_executor.gRunNodeTaskParallel = False
        check_executor.gRunCustomTaskParallel = False

    def tearDown(self):
        self.p_get_logger.stop()

    def test_execute_checklist_success_and_finalize(self):
        hc = _DummyHC()
        with patch.object(check_executor, "REGISTERED_CLASSES", [_DummyCheckClass]), \
             patch.object(check_executor, "get_all_registered_classes", return_value=None):
            ex = check_executor.CheckExecutor(hc)
            ex.execute_checklist()
            # Finalize should have called mSetRecommend with a list
            self.assertIsInstance(self.logger.recommend, list)

    def test_getOrderPid(self):
        hc = _DummyHC()
        ex = check_executor.CheckExecutor.__new__(check_executor.CheckExecutor)
        ex.resdict = {
            "100pid_list": ["200", "300"],
            "200pid_list": ["400"],
            "300pid_list": [],
            "pids": [""]
        }
        order = check_executor.CheckExecutor.getOrderPid(ex, "100")
        # Expected: children of 200 (400), then 200, children of 300 (none), 300, then 100
        self.assertEqual(order, ["400", "200", "300", "100"])

# =========================
# Auto-generated tests end
# =========================

if __name__ == '__main__':
    unittest.main()
