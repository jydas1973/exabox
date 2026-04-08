#!/bin/python
#
# $Header: tests_tools_regressions.py 02-apr-2026.11:33:26 aararora Exp $
#
# tests_tools_regressions.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_tools_regressions.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    04/02/26 - Add unit tests for bug 38900321
#    aararora    04/02/26 - Creation
#
import sys
import types
import unittest
import multiprocessing
from unittest.mock import MagicMock, patch

import defusedxml.ElementTree

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.tools.scripts import ebScripts
from exabox.tools.ebOedacli.ebCommandGenerator import ebCommandGenerator
from exabox.tools.ebNoSql.ebNoSqlInstaller import ebNoSqlInstaller
from exabox.tools.ebGraph.ebGraph import ebGraph
from exabox.tools.profiling import profiler


class ToolsRegressionBase(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        with patch.object(
            ebTestClucontrol, "setUpClass", autospec=True
        ) as mock_setup:
            mock_setup.return_value = None
            super(ToolsRegressionBase, cls).setUpClass(False, False)


class TestEbScriptsFallback(ToolsRegressionBase):

    @patch("exabox.tools.scripts.ebIOFile")
    @patch("exabox.tools.scripts.get_gcontext")
    def test_uses_default_paths_when_missing(self, mock_get_ctx, mock_io_file):
        ctx = MagicMock()
        ctx.mGetBasePath.return_value = "/tmp"
        ctx.mGetConfigOptions.return_value = {}
        mock_get_ctx.return_value = ctx

        file_handle = MagicMock()
        file_handle.mOpenFile.return_value = None
        file_handle.mGetFilePath.return_value = "/tmp/dummy.xml"
        file_handle.mReadFile.return_value = "<scripts/>"
        file_handle.mCloseFile.return_value = None
        mock_io_file.return_value = file_handle

        with patch.object(ebScripts, "mParseScript", autospec=True):
            scripts_obj = ebScripts("dummy.xml")

        mock_io_file.assert_called_once_with("dummy.xml", ['.'])
        self.assertEqual(scripts_obj._ebScripts__paths, ['.'])


class TestEbCommandGeneratorPreExtra(ToolsRegressionBase):

    def test_pre_extra_accessors_are_consistent(self):
        generator = object.__new__(ebCommandGenerator)
        generator._ebCommandGenerator__preExtraCommands = ['initial']

        self.assertEqual(generator.mGetPreExtraCommands(), ['initial'])

        new_commands = ['cmd']
        generator.mSetPreExtraCommands(new_commands)
        self.assertIs(generator.mGetPreExtraCommands(), new_commands)


class TestEbNoSqlInstaller(ToolsRegressionBase):

    def test_returns_original_list_for_small_clusters(self):
        nodes = ['n1', 'n2', 'n3']
        installer = ebNoSqlInstaller(nodes, len(nodes))
        self.assertEqual(installer.mGetParticipantNodes(), nodes)

    def test_selects_first_second_last_for_larger_clusters(self):
        nodes = ['n1', 'n2', 'n3', 'n4', 'n5']
        installer = ebNoSqlInstaller(nodes, len(nodes))
        self.assertEqual(installer.mGetParticipantNodes(), ['n1', 'n2', 'n5'])


class TestEbGraphVisitAll(ToolsRegressionBase):

    def test_cycle_graph_visits_all_nodes(self):
        graph = ebGraph()
        graph.mAddConnection("A", "B", aBidirectional=True)
        graph.mAddConnection("B", "C", aBidirectional=True)
        graph.mAddConnection("C", "A", aBidirectional=True)

        visited = graph.mVisitAll()
        elements = {node.mGetElement() for node in visited}
        self.assertEqual(elements, {"A", "B", "C"})


class TestProfilerMeasureExecTime(ToolsRegressionBase):

    def setUp(self):
        profiler.flush_profiled_data()

    def tearDown(self):
        profiler.flush_profiled_data()

    def test_ret_stealer_runs_only_on_success(self):
        success_returns = []

        def ret_capture(ret):
            success_returns.append(ret)
            return ret

        @profiler.measure_exec_time(ret_stealer=ret_capture)
        def compute():
            return 99

        self.assertEqual(compute(), 99)
        self.assertEqual(success_returns, [99])

        failure_returns = []

        def ret_failure(ret):
            failure_returns.append(ret)
            return ret

        @profiler.measure_exec_time(ret_stealer=ret_failure)
        def explode():
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            explode()
        self.assertEqual(failure_returns, [])


if __name__ == '__main__':
    unittest.main()
