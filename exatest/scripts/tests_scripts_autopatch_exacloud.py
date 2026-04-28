#!/usr/bin/env python3
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#

import importlib.util
import os
import sys
import unittest
from unittest import mock

try:
    from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
except ImportError:
    class ebTestClucontrol(unittest.TestCase):
        pass


VIEW_ROOT = os.environ.get("ADE_VIEW_ROOT", "/ade/joysjose_voxioissue2")
SCRIPTS_ROOT = os.path.join(VIEW_ROOT, "ecs", "exacloud", "scripts")
AUTOPATCH_PATH = os.path.join(SCRIPTS_ROOT, "autopatch_exacloud.py")


def _load_module(module_name, module_path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ebTestScriptsAutopatchExacloud(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        pass

    def test_execute_uses_wildcards_for_tar_extract(self):
        module = _load_module("autopatch_exacloud_test", AUTOPATCH_PATH)
        upgrade = module.AutoUpgrade()
        upgrade._AutoUpgrade__exacloud = "/tmp/exacloud-home"
        upgrade._AutoUpgrade__mini = "/tmp/exacloud-mini.tar"
        upgrade._AutoUpgrade__atp = "/tmp/atp.tar"
        upgrade._AutoUpgrade__args = type("Args", (), {"verbose": False})()
        upgrade._AutoUpgrade__start_time = "2603270912"

        recorded_commands = []

        def fake_bash(command, soft=False, debug=False):
            recorded_commands.append(command)
            return 0

        with mock.patch.object(upgrade, "bash", side_effect=fake_bash), \
             mock.patch.object(module.AutoUpgrade, "read_json", return_value={}), \
             mock.patch.object(module.AutoUpgrade, "write_json"), \
             mock.patch.object(module.os.path, "exists", return_value=False):
            upgrade.execute()

        tar_commands = [
            command for command in recorded_commands
            if command.startswith("tar -C ") and upgrade._AutoUpgrade__mini in command
        ]

        self.assertEqual(len(tar_commands), 4)
        self.assertTrue(all("--wildcards" in command for command in tar_commands))


if __name__ == "__main__":
    unittest.main()
