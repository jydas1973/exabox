#!/usr/bin/env python3
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#

import importlib.util
import os
import sys
import unittest

try:
    from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
except ImportError:
    class ebTestClucontrol(unittest.TestCase):
        pass


VIEW_ROOT = os.environ.get("ADE_VIEW_ROOT", "/ade/joysjose_voxioissue2")
SCRIPTS_ROOT = os.path.join(VIEW_ROOT, "ecs", "exacloud", "scripts")
PROCESS_MONITOR_PATH = os.path.join(SCRIPTS_ROOT, "exacloud_process_monitor.py")


def _load_module(module_name, module_path, argv=None):
    original_argv = list(sys.argv)
    try:
        if argv is not None:
            sys.argv = list(argv)
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.argv = original_argv


class ebTestScriptsExacloudProcessMonitor(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        pass

    def test_get_pid_from_mysql_output_returns_pid_from_second_line(self):
        module = _load_module(
            "exacloud_process_monitor_test",
            PROCESS_MONITOR_PATH,
            argv=["exacloud_process_monitor.py"]
        )

        self.assertEqual(module.get_pid_from_mysql_output(b"pid\n12345\n"), 12345)

    def test_get_pid_from_mysql_output_rejects_invalid_rows(self):
        module = _load_module(
            "exacloud_process_monitor_test_invalid",
            PROCESS_MONITOR_PATH,
            argv=["exacloud_process_monitor.py"]
        )

        self.assertIsNone(module.get_pid_from_mysql_output(None))
        self.assertIsNone(module.get_pid_from_mysql_output(b"pid\n"))
        self.assertIsNone(module.get_pid_from_mysql_output(b"pid\nabc\n"))


if __name__ == "__main__":
    unittest.main()
