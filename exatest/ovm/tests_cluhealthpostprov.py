#!/bin/python
#
# $Header: tests_cluhealthpostprov.py 12-may-2026.10:33:17 prsshukl Exp $
#
# tests_cluhealthpostprov.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_cluhealthpostprov.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    05/12/26 - Creation
#

import io
import unittest
from types import SimpleNamespace
from unittest import mock

from exabox.ovm.cluhealthpostprov import (
    ARGUMENT,
    CURR_VAL,
    COMMAND,
    CURRENT_RETURN_CODE,
    ERROR,
    ERR_MSG,
    EXPECTED,
    EXPECTED_RETURN_CODE,
    FAIL,
    FILESYSTEM,
    PASS,
    RESULT,
    TYPE,
    checkDriver,
    executeHealthPostProv,
    _getGridHome,
    _isFsMntPoint,
    _sanitize_mount_point,
    ExacloudRuntimeError,
)


class ebTestCluhealthpostprov(unittest.TestCase):

    # Auto-generated test for checkDriver
    @mock.patch("exabox.ovm.cluhealthpostprov.get_gcontext")
    @mock.patch("exabox.ovm.cluhealthpostprov.exaBoxNode")
    @mock.patch("exabox.ovm.cluhealthpostprov._isFsMntPoint", return_value=True)
    def test_check_driver_df_command_quotes_mount_point(self, mock_is_mount, mock_node_cls, mock_ctx):
        mock_ctx.return_value = object()

        node = mock.Mock()
        node.mIsConnectable.return_value = True
        node.mExecuteCmd.return_value = (
            None,
            io.StringIO("Filesystem 1K-blocks Used Available Use% Mounted on\n/dev/vdb 2048K 0 2048 0% /mnt/data path\n"),
            io.StringIO("")
        )
        node.mGetCmdExitStatus.return_value = 0
        node.mDisconnect.return_value = None
        mock_node_cls.return_value = node

        checks = {
            "/mnt/data path": {
                "type": FILESYSTEM,
                EXPECTED: "2048",
                "metric": "K",
                "mandatory": True,
            }
        }

        result = checkDriver(["host-quote"], checks, "dom0")

        exec_cmd = node.mExecuteCmd.call_args_list[0][0][0]
        self.assertIn("'", exec_cmd)
        self.assertIn("-PBK", exec_cmd)
        host_res = result["host-quote"][FILESYSTEM][0]
        self.assertEqual(host_res[RESULT], PASS)
        self.assertEqual(host_res["currentValue"], "2048K")
        mock_is_mount.assert_called_once()

    # Auto-generated test for checkDriver
    @mock.patch("exabox.ovm.cluhealthpostprov.get_gcontext")
    @mock.patch("exabox.ovm.cluhealthpostprov.exaBoxNode")
    def test_check_driver_allows_cellcli_command(self, mock_node_cls, mock_ctx):
        mock_ctx.return_value = object()

        node = mock.Mock()
        node.mIsConnectable.return_value = True
        node.mExecuteCmd.return_value = (None, io.StringIO("success\n"), io.StringIO(""))
        node.mGetCmdExitStatus.return_value = 0
        node.mDisconnect.return_value = None
        mock_node_cls.return_value = node

        checks = {
            "cellcli-check": {
                "type": COMMAND,
                COMMAND: "cellcli",
                ARGUMENT: "list alerthistory",
                EXPECTED: "success",
                EXPECTED_RETURN_CODE: "0",
                "mandatory": True,
            }
        }

        result = checkDriver(["cell-host"], checks, "dom0")

        executed_cmd = node.mExecuteCmd.call_args[0][0]
        self.assertEqual(executed_cmd, "cellcli list alerthistory")
        host_res = result["cell-host"][COMMAND][0]
        self.assertEqual(host_res[RESULT], PASS)
        self.assertEqual(host_res[CURRENT_RETURN_CODE], "0")

    # Auto-generated test for _isFsMntPoint
    @mock.patch("exabox.ovm.cluhealthpostprov._sanitize_mount_point")
    def test_is_fs_mount_point_invokes_findmnt(self, mock_sanitize):
        mock_sanitize.return_value = "/mnt"
        node = mock.Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO(""), io.StringIO(""))
        node.mGetCmdExitStatus.return_value = 0

        self.assertTrue(_isFsMntPoint(node, "/mnt"))
        node.mExecuteCmd.assert_called_once()
        executed_cmd = node.mExecuteCmd.call_args[0][0]
        self.assertIn("/usr/bin/findmnt", executed_cmd)
        mock_sanitize.assert_called_once_with("/mnt")

    # Auto-generated test for _sanitize_mount_point
    def test_sanitize_mount_point_rejects_pipe_and_quotes(self):
        self.assertIsNone(_sanitize_mount_point("/data|pipe"))
        self.assertIsNone(_sanitize_mount_point('/path"double'))
        self.assertIsNone(_sanitize_mount_point("/path'quote"))

    # Auto-generated test for checkDriver
    @mock.patch("exabox.ovm.cluhealthpostprov.get_gcontext")
    @mock.patch("exabox.ovm.cluhealthpostprov.exaBoxNode")
    @mock.patch("exabox.ovm.cluhealthpostprov._isFsMntPoint", return_value=True)
    @mock.patch("exabox.ovm.cluhealthpostprov._getGridHome", return_value="/u01/app/grid")
    def test_check_driver_substitutes_grid_home_for_dom_u(self, mock_grid_home, mock_is_mount, mock_node_cls, mock_ctx):
        mock_ctx.return_value = object()

        node = mock.Mock()
        node.mIsConnectable.return_value = True
        node.mExecuteCmd.return_value = (
            None,
            io.StringIO("Filesystem 1K-blocks Used Available Use% Mounted on\n"
                        "/dev/vdb 4096K 0 4096 0% /u01/app/grid/log\n"),
            io.StringIO("")
        )
        node.mGetCmdExitStatus.return_value = 0
        node.mDisconnect.return_value = None
        mock_node_cls.return_value = node

        checks = {
            "$GRID_HOME/log": {
                TYPE: FILESYSTEM,
                EXPECTED: "4096",
                "metric": "K",
                "mandatory": True,
            }
        }

        result = checkDriver(["domu-host"], checks, "domU")

        exec_cmd = node.mExecuteCmd.call_args_list[0][0][0]
        self.assertIn("/u01/app/grid/log", exec_cmd)
        host_res = result["domu-host"][FILESYSTEM][0]
        self.assertEqual(host_res[RESULT], PASS)
        self.assertEqual(host_res[EXPECTED], "4096")
        mock_grid_home.assert_called_once_with(node)
        mock_is_mount.assert_called_once()

    # Auto-generated test for checkDriver
    @mock.patch("exabox.ovm.cluhealthpostprov.get_gcontext")
    @mock.patch("exabox.ovm.cluhealthpostprov.exaBoxNode")
    def test_check_driver_marks_command_failure_on_unexpected_output(self, mock_node_cls, mock_ctx):
        mock_ctx.return_value = object()

        node = mock.Mock()
        node.mIsConnectable.return_value = True
        node.mExecuteCmd.return_value = (
            None,
            io.StringIO("different output\n"),
            io.StringIO("")
        )
        node.mGetCmdExitStatus.return_value = 1
        node.mDisconnect.return_value = None
        mock_node_cls.return_value = node

        checks = {
            "cmd-check": {
                TYPE: COMMAND,
                COMMAND: "echo",
                ARGUMENT: "ok",
                EXPECTED: "expected",
                EXPECTED_RETURN_CODE: "0",
                "mandatory": False,
            }
        }

        result = checkDriver(["dom0"], checks, "dom0")

        host_res = result["dom0"][COMMAND][0]
        self.assertEqual(host_res[RESULT], FAIL)
        self.assertEqual(host_res[CURRENT_RETURN_CODE], "1")

    # Auto-generated test for checkDriver
    @mock.patch("exabox.ovm.cluhealthpostprov.get_gcontext")
    @mock.patch("exabox.ovm.cluhealthpostprov.exaBoxNode")
    def test_check_driver_marks_command_failure_when_rc_mismatch(self, mock_node_cls, mock_ctx):
        mock_ctx.return_value = object()

        node = mock.Mock()
        node.mIsConnectable.return_value = True
        node.mExecuteCmd.return_value = (
            None,
            io.StringIO("expected output\n"),
            io.StringIO("")
        )
        node.mGetCmdExitStatus.return_value = 2
        node.mDisconnect.return_value = None
        mock_node_cls.return_value = node

        checks = {
            "cmd-rc-mismatch": {
                TYPE: COMMAND,
                COMMAND: "echo",
                ARGUMENT: "test",
                EXPECTED: "expected output",
                EXPECTED_RETURN_CODE: "0",
                "mandatory": True,
            }
        }

        result = checkDriver(["dom0"], checks, "dom0")

        host_res = result["dom0"][COMMAND][0]
        self.assertEqual(host_res[RESULT], FAIL)
        self.assertEqual(host_res[CURRENT_RETURN_CODE], "2")
        self.assertIn("expected output", host_res[CURR_VAL])

    # Auto-generated test for checkDriver
    @mock.patch("exabox.ovm.cluhealthpostprov.get_gcontext")
    @mock.patch("exabox.ovm.cluhealthpostprov.exaBoxNode")
    def test_check_driver_records_error_when_execute_cmd_raises(self, mock_node_cls, mock_ctx):
        mock_ctx.return_value = object()

        node = mock.Mock()
        node.mIsConnectable.return_value = True

        def _raise(*args, **kwargs):
            raise RuntimeError("boom")

        node.mExecuteCmd.side_effect = _raise
        node.mGetCmdExitStatus.return_value = 0
        node.mDisconnect.return_value = None
        mock_node_cls.return_value = node

        checks = {
            "cmd-error": {
                TYPE: COMMAND,
                COMMAND: "echo",
                ARGUMENT: "123",
                EXPECTED: "123",
                EXPECTED_RETURN_CODE: "0",
                "mandatory": True,
            }
        }

        result = checkDriver(["dom0"], checks, "dom0")

        self.assertEqual(result[ERR_MSG], 'Unexpected error while doing checks')

    # Auto-generated test for checkDriver
    @mock.patch("exabox.ovm.cluhealthpostprov.get_gcontext")
    @mock.patch("exabox.ovm.cluhealthpostprov.exaBoxNode")
    def test_check_driver_skips_unreachable_host(self, mock_node_cls, mock_ctx):
        mock_ctx.return_value = object()

        node = mock.Mock()
        node.mIsConnectable.return_value = False
        node.mDisconnect.return_value = None
        mock_node_cls.return_value = node

        checks = {
            "/mnt/data": {
                TYPE: FILESYSTEM,
                EXPECTED: "10",
                "metric": "K",
                "mandatory": False,
            }
        }

        result = checkDriver(["unreachable-host"], checks, "dom0")

        self.assertNotIn("unreachable-host", result)
        node.mConnect.assert_not_called()
        node.mExecuteCmd.assert_not_called()

    # Auto-generated test for checkDriver
    @mock.patch("exabox.ovm.cluhealthpostprov.get_gcontext")
    @mock.patch("exabox.ovm.cluhealthpostprov.exaBoxNode")
    @mock.patch("exabox.ovm.cluhealthpostprov._sanitize_mount_point", return_value=None)
    def test_check_driver_invalid_mount_point_sets_error(self, mock_sanitize, mock_node_cls, mock_ctx):
        mock_ctx.return_value = object()

        node = mock.Mock()
        node.mIsConnectable.return_value = True
        node.mDisconnect.return_value = None
        mock_node_cls.return_value = node

        checks = {
            "/bad|mount": {
                TYPE: FILESYSTEM,
                EXPECTED: "10",
                "metric": "K",
                "mandatory": True,
            }
        }

        result = checkDriver(["dom0"], checks, "dom0")

        host_res = result.get("dom0", {}).get(FILESYSTEM, [])[0]
        self.assertEqual(host_res[RESULT], ERROR)
        self.assertIn("Invalid mount point", host_res[ERR_MSG])
        mock_sanitize.assert_called_once()

    # Auto-generated test for checkDriver
    @mock.patch("exabox.ovm.cluhealthpostprov.get_gcontext")
    @mock.patch("exabox.ovm.cluhealthpostprov.exaBoxNode")
    @mock.patch("exabox.ovm.cluhealthpostprov._isFsMntPoint", return_value=False)
    def test_check_driver_detects_non_mounted_path(self, mock_is_mount, mock_node_cls, mock_ctx):
        mock_ctx.return_value = object()

        node = mock.Mock()
        node.mIsConnectable.return_value = True
        node.mExecuteCmd.return_value = (
            None,
            io.StringIO(""),
            io.StringIO("")
        )
        node.mGetCmdExitStatus.return_value = 0
        node.mDisconnect.return_value = None
        mock_node_cls.return_value = node

        checks = {
            "/mnt/valid": {
                TYPE: FILESYSTEM,
                EXPECTED: "1",
                "metric": "K",
                "mandatory": False,
            }
        }

        result = checkDriver(["dom0"], checks, "dom0")

        host_res = result["dom0"][FILESYSTEM][0]
        self.assertEqual(host_res[RESULT], ERROR)
        self.assertIn("Invalid mount point", host_res[ERR_MSG])
        mock_is_mount.assert_called_once_with(node, "/mnt/valid")

    # Auto-generated test for checkDriver
    @mock.patch("exabox.ovm.cluhealthpostprov.get_gcontext")
    @mock.patch("exabox.ovm.cluhealthpostprov.exaBoxNode")
    def test_check_driver_sets_retry_and_connects(self, mock_node_cls, mock_ctx):
        mock_ctx.return_value = object()

        node = mock.Mock()
        node.mIsConnectable.return_value = True
        node.mExecuteCmd.return_value = (
            None,
            io.StringIO("Filesystem 1K-blocks Used Available Use% Mounted on\n/dev/vdb 1024K 0 1024 0% /mnt/data\n"),
            io.StringIO("")
        )
        node.mGetCmdExitStatus.return_value = 0
        node.mDisconnect.return_value = None
        mock_node_cls.return_value = node

        checks = {
            "/mnt/data": {
                TYPE: FILESYSTEM,
                EXPECTED: "1024",
                "metric": "K",
                "mandatory": True,
            }
        }

        result = checkDriver(["host-a"], checks, "dom0")

        self.assertIn("host-a", result)
        node.mSetMaxRetries.assert_called_once_with(2)
        node.mConnect.assert_called_once_with(aHost="host-a")

    # Auto-generated test for executeHealthPostProv
    @mock.patch("exabox.ovm.cluhealthpostprov.checkDriver", side_effect=RuntimeError(FAIL))
    def test_execute_health_post_prov_handles_driver_exception(self, mock_driver):
        class _Clubox:
            def mReturnDom0DomUPair(self, aIsClusterLessXML=False):
                return [("dom0", "domu")]

            def mReturnCellNodes(self, aIsClusterLessXML=False):
                return {"cell1": {}}

            def mIsClusterLessXML(self):
                return False

        options = SimpleNamespace(jsonconf={
            "hostnames": ["dom0"],
            "dom0": {"check": {TYPE: COMMAND}},
            "cell": {"check": {TYPE: COMMAND}},
        })

        response = executeHealthPostProv(_Clubox(), options)

        self.assertIn("dom0_checks", response)
        self.assertEqual(response["dom0_checks"][ERR_MSG], "Something unexpected happened while running 'dom0' checks")
        self.assertIn("cell_checks", response)
        self.assertEqual(response["cell_checks"][ERR_MSG], "Something unexpected happened while running 'cell' checks")
        mock_driver.assert_called()

    # Auto-generated test for _getGridHome
    def test_get_grid_home_returns_trimmed_path(self):
        node = mock.Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO('/u01/app/grid\n'), io.StringIO(""))

        result = _getGridHome(node)

        self.assertEqual(result, "/u01/app/grid")
        node.mExecuteCmd.assert_called_once()

    # Auto-generated test for _getGridHome
    def test_get_grid_home_raises_when_missing_entry(self):
        node = mock.Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO(""), io.StringIO("error"))

        with self.assertRaises(ExacloudRuntimeError):
            _getGridHome(node)

    # Auto-generated test for checkDriver
    @mock.patch("exabox.ovm.cluhealthpostprov.get_gcontext")
    @mock.patch("exabox.ovm.cluhealthpostprov.exaBoxNode")
    def test_check_driver_accepts_pipeline_arguments(self, mock_node_cls, mock_ctx):
        mock_ctx.return_value = object()

        node = mock.Mock()
        node.mIsConnectable.return_value = True
        node.mExecuteCmd.return_value = (
            None,
            io.StringIO("pipeline ok\n"),
            io.StringIO("")
        )
        node.mGetCmdExitStatus.return_value = 0
        node.mDisconnect.return_value = None
        mock_node_cls.return_value = node

        checks = {
            "pipeline": {
                TYPE: COMMAND,
                COMMAND: "bash",
                ARGUMENT: "-c 'echo ok | grep ok'",
                EXPECTED: "pipeline ok",
                EXPECTED_RETURN_CODE: "0",
                "mandatory": True,
            }
        }

        result = checkDriver(["dom0"], checks, "dom0")

        executed_cmd = node.mExecuteCmd.call_args[0][0]
        self.assertEqual(executed_cmd, "bash -c 'echo ok | grep ok'")
        host_res = result["dom0"][COMMAND][0]
        self.assertEqual(host_res[RESULT], PASS)
        self.assertEqual(host_res[CURRENT_RETURN_CODE], "0")

    # Auto-generated test for checkDriver
    @mock.patch("exabox.ovm.cluhealthpostprov.get_gcontext")
    @mock.patch("exabox.ovm.cluhealthpostprov.exaBoxNode")
    @mock.patch("exabox.ovm.cluhealthpostprov._isFsMntPoint", return_value=True)
    def test_check_driver_records_filesystem_error_on_df_failure(self, mock_is_mount, mock_node_cls, mock_ctx):
        mock_ctx.return_value = object()

        node = mock.Mock()
        node.mIsConnectable.return_value = True
        node.mExecuteCmd.return_value = (
            None,
            io.StringIO("Filesystem\n"),
            io.StringIO("df error\n"),
        )
        node.mGetCmdExitStatus.return_value = 1
        node.mDisconnect.return_value = None
        mock_node_cls.return_value = node

        checks = {
            "/mnt/error": {
                TYPE: FILESYSTEM,
                EXPECTED: "1",
                "metric": "K",
                "mandatory": True,
            }
        }

        result = checkDriver(["dom0"], checks, "dom0")

        host_res = result["dom0"][FILESYSTEM][0]
        self.assertEqual(host_res[RESULT], ERROR)
        self.assertIn("Something unexpected occurred", host_res[ERR_MSG])
        node.mExecuteCmd.assert_called()
        mock_is_mount.assert_called_once()

    # Auto-generated test for _sanitize_mount_point
    def test_sanitize_mount_point_strips_whitespace(self):
        self.assertEqual(_sanitize_mount_point("  /grid/mnt  "), "/grid/mnt")

    # Auto-generated test for _sanitize_mount_point
    def test_sanitize_mount_point_rejects_control_characters(self):
        self.assertIsNone(_sanitize_mount_point("/grid/\npath"))
        self.assertIsNone(_sanitize_mount_point("-bad"))

    # Auto-generated test for executeHealthPostProv
    @mock.patch("exabox.ovm.cluhealthpostprov.ebError", return_value={"status": "error"})
    @mock.patch("exabox.ovm.cluhealthpostprov.ebLogError")
    def test_execute_health_post_prov_requires_jsonconf_attribute(self, mock_log, mock_error):
        result = executeHealthPostProv(SimpleNamespace(), object())

        self.assertEqual(result, {"status": "error"})
        mock_error.assert_called_once_with(0x0808)
        mock_log.assert_called()

    # Auto-generated test for executeHealthPostProv
    @mock.patch("exabox.ovm.cluhealthpostprov.ebError", return_value={"status": "error"})
    @mock.patch("exabox.ovm.cluhealthpostprov.ebLogError")
    def test_execute_health_post_prov_rejects_empty_jsonconf(self, mock_log, mock_error):
        options = SimpleNamespace(jsonconf={})

        result = executeHealthPostProv(SimpleNamespace(), options)

        self.assertEqual(result, {"status": "error"})
        mock_error.assert_called_once_with(0x0808)
        mock_log.assert_called()

if __name__ == "__main__":
    unittest.main()
