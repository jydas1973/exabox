#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/imagebase_copy/tests_imagebase_copy_volumes.py /main/1 2026/03/30 00:00:00 jesandov Exp $
#
# tests_imagebase_copy_volumes.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_imagebase_copy_volumes.py - Unit tests for imagebase copy volumes endpoint.
#
#    DESCRIPTION
#      Validates that the handler assigns unique device targets while copying
#      imagebase volumes and exercises the happy-path flow used by clucontrol.
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    03/30/26 - Creation (codex)
#

import copy
import io
import json
import os
import re
import shlex
import shutil
import sys
import types
import uuid
from unittest import mock


class _StubInstaller:
    def __init__(self, *_args, **_kwargs):
        pass

    def mExecuteLocal(self, *_args, **_kwargs):
        return 0, "", ""

    def mInstall(self, *_args, **_kwargs):
        return None


sys.modules.setdefault(
    "exabox.exatest.common.ebAgentInstaller",
    types.SimpleNamespace(ebAgentInstaller=_StubInstaller),
)
sys.modules.setdefault(
    "exabox.exatest.common.ebRemoteManagmentInstaller",
    types.SimpleNamespace(ebRemoteManagmentInstaller=_StubInstaller),
)

from exabox.core.MockCommand import MockCommand, exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.jsondispatch.handler_imagebase_copy_volumes import ImagebaseCopyVolume


class _DummyLock:
    """Minimal substitute for RemoteLock used by the unit test."""

    def __init__(self, *_args, **_kwargs):
        self.acquired = False

    def acquire(self, *_args, **_kwargs):
        self.acquired = True

    def release(self, *_args, **_kwargs):
        self.acquired = False


class ebTestImagebaseCopyVolumes(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        resources = os.path.join(os.path.dirname(__file__), "resources/")
        super().setUpClass(aResourceFolder=resources)
        cls.maxDiff = None

    def setUp(self):
        super().setUp()
        self.mSetIsElatic(True)

    def test_mexecute_attaches_next_free_device(self):
        options = copy.deepcopy(self.mGetContext().mGetArgsOptions())
        options.jsonconf = copy.deepcopy(self.mGetPayload())

        handler = ImagebaseCopyVolume(options)

        uuid_values = [
            uuid.UUID("00000000-0000-0000-0000-000000000001"),
            uuid.UUID("00000000-0000-0000-0000-000000000002"),
        ]

        nat_output = "sea201611exddu1201.sea2xx2xx0051qf.adminsea2.oraclevcn.com.\n"
        client_output = "gold021-xqnxx\n"
        domblk_outputs = iter(
            [
                "Target Source\nsdx /dev/exc/existing\n",
                "Target Source\nsdy /dev/exc/existing\n",
            ]
        )

        attached_targets = []
        domblk_calls = []

        def _make_nat_cmd():
            return MockCommand(
                r"(?s).*virsh list --all --name.*nslookup.*",
                lambda *_: (0, nat_output, ""),
            )

        def _make_client_cmd():
            return MockCommand(
                r"\s*virsh list --all --name \| grep -v 'gold\\..*\\.internal'\s*",
                lambda *_: (0, client_output, ""),
            )

        def _make_domblk_cmd():
            def _callback(cmd, _stdin):
                try:
                    stdout = next(domblk_outputs)
                except StopIteration as exc:  # pragma: no cover - defensive
                    raise AssertionError("Unexpected virsh domblklist call") from exc
                domblk_calls.append(cmd)
                return (0, stdout, "")

            return MockCommand(r"virsh domblklist .*", _callback)

        def _make_xml_copy_cmd(uuid_token):

            pattern = (
                rf"/bin/scp .*tmp/{uuid_token}/{uuid_token}\.xml "
                rf"/opt/exacloud/{uuid_token}/{uuid_token}\.xml"
            )

            def _callback(cmd, _stdin):
                parts = shlex.split(cmd)
                local_path = parts[1]
                with open(local_path, "r", encoding="utf-8") as fh:
                    xml_content = fh.read()
                match = re.search(r"target dev='([^']+)'", xml_content)
                if match:
                    attached_targets.append(match.group(1))
                return (0, "", "")

            return MockCommand(pattern, _callback)

        def _make_local_executor():
            def _handler(cmd, *args, **kwargs):
                if cmd.startswith("/bin/mkdir -p "):
                    target = shlex.split(cmd)[2]
                    os.makedirs(target, exist_ok=True)
                    return (0, "", "")
                if cmd.startswith("/bin/rm -rf "):
                    target = shlex.split(cmd)[2]
                    shutil.rmtree(target, ignore_errors=True)
                    return (0, "", "")
                if (
                    "oss_instance_principal_script.py" in cmd
                    and "--to=" in cmd
                ):
                    dest = cmd.split("--to=")[1].split()[0]
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with open(dest, "w", encoding="utf-8"):
                        pass
                    return (0, "", "")
                return (0, "", "")

            return _handler

        system_uuid = str(uuid_values[0])
        u01_uuid = str(uuid_values[1])

        dom0_regex = self.mGetRegexDom0()
        domu_regex = self.mGetRegexDomU()

        _cmd = {
            dom0_regex: [
                [
                    _make_nat_cmd(),
                    _make_client_cmd(),
                    exaMockCommand(
                        rf"/bin/mkdir -p /opt/exacloud/{system_uuid}", aRc=0
                    ),
                    _make_domblk_cmd(),
                    _make_xml_copy_cmd(system_uuid),
                    exaMockCommand(
                        rf"virsh attach-device gold021-xqnxx "
                        rf"/opt/exacloud/{system_uuid}/{system_uuid}.xml --live",
                        aRc=0,
                    ),
                ],
                [
                    exaMockCommand(
                        r"virsh detach-disk gold021-xqnxx "
                        r"/dev/exc/system_Vmrujgo_1_0aa2 --live",
                        aRc=0,
                    ),
                ],
                [
                    exaMockCommand(
                        rf"\s*/bin/rm -rf /opt/exacloud/{system_uuid}\s*", aRc=0
                    ),
                ],
                [
                    _make_nat_cmd(),
                    _make_client_cmd(),
                    exaMockCommand(
                        rf"/bin/mkdir -p /opt/exacloud/{u01_uuid}", aRc=0
                    ),
                    _make_domblk_cmd(),
                    _make_xml_copy_cmd(u01_uuid),
                    exaMockCommand(
                        rf"virsh attach-device gold021-xqnxx "
                        rf"/opt/exacloud/{u01_uuid}/{u01_uuid}.xml --live",
                        aRc=0,
                    ),
                ],
                [
                    exaMockCommand(
                        r"virsh detach-disk gold021-xqnxx "
                        r"/dev/exc/u01_Vmrujgo_1_08c4 --live",
                        aRc=0,
                    ),
                ],
                [
                    exaMockCommand(
                        rf"\s*/bin/rm -rf /opt/exacloud/{u01_uuid}\s*", aRc=0
                    ),
                ],
            ],
            domu_regex: [
                [
                    exaMockCommand(
                        r'dmesg \| grep "Attached SCSI disk" \| grep ":3:1: "',
                        aRc=1,
                        aStderr="no match",
                    ),
                ],
                [
                    exaMockCommand(
                        rf"/bin/mkdir -p /opt/exacloud/{system_uuid}", aRc=0
                    ),
                    exaMockCommand(
                        rf"/bin/scp .*tmp/{system_uuid}/.*system.* "
                        rf"/opt/exacloud/{system_uuid}/.*system.*",
                        aRc=0,
                    ),
                    exaMockCommand(
                        r'dmesg \| grep "Attached SCSI disk" \| grep ":3:1: "',
                        aRc=0,
                        aStdout="[ 0.000000] ... [sdy]",
                    ),
                    exaMockCommand(r"pbzip2 -t .*system.*", aRc=0),
                    exaMockCommand(
                        r"pbzip2 -dc .*system.* \| dd of=/dev/sdy bs=64K", aRc=0
                    ),
                    exaMockCommand(
                        r"/bin/echo -e 'Fix\nFix' \| parted ---pretend-input-tty "
                        r"/dev/sdy print",
                        aRc=0,
                        aStdout="parted ok\n",
                    ),
                ],
                [
                    exaMockCommand(
                        rf"\s*/bin/rm -rf /opt/exacloud/{system_uuid}\s*", aRc=0
                    ),
                ],
                [
                    exaMockCommand(
                        r'dmesg \| grep "Attached SCSI disk" \| grep ":3:1: "',
                        aRc=1,
                        aStderr="no match",
                    ),
                ],
                [
                    exaMockCommand(
                        rf"/bin/mkdir -p /opt/exacloud/{u01_uuid}", aRc=0
                    ),
                    exaMockCommand(
                        rf"/bin/scp .*tmp/{u01_uuid}/.*u01.* "
                        rf"/opt/exacloud/{u01_uuid}/.*u01.*",
                        aRc=0,
                    ),
                    exaMockCommand(
                        r'dmesg \| grep "Attached SCSI disk" \| grep ":3:1: "',
                        aRc=0,
                        aStdout="[ 0.000000] ... [sdz]",
                    ),
                    exaMockCommand(r"pbzip2 -t .*u01.*", aRc=0),
                    exaMockCommand(
                        r"pbzip2 -dc .*u01.* \| dd of=/dev/sdz bs=64K", aRc=0
                    ),
                    exaMockCommand(
                        r"/bin/echo -e 'Fix\nFix' \| parted ---pretend-input-tty "
                        r"/dev/sdz print",
                        aRc=0,
                        aStdout="parted ok\n",
                    ),
                ],
                [
                    exaMockCommand(
                        rf"\s*/bin/rm -rf /opt/exacloud/{u01_uuid}\s*", aRc=0
                    ),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmd)

        real_open = open

        def _mocked_open(path, mode="r", *args, **kwargs):
            if "exagip/config/oss.conf" in path and "r" in mode:
                payload = {"bom_namespace": "mockns", "bom_bucket": "mockbucket"}
                return io.StringIO(json.dumps(payload))
            return real_open(path, mode, *args, **kwargs)

        with mock.patch("uuid.uuid4", side_effect=uuid_values), mock.patch(
            "builtins.open", side_effect=_mocked_open
        ), mock.patch(
            "exabox.jsondispatch.handler_imagebase_copy_volumes.RemoteLock",
            _DummyLock,
        ), mock.patch.object(
            ImagebaseCopyVolume,
            "mExecuteLocal",
            side_effect=_make_local_executor(),
        ):
            rc, response = handler.mExecute()

        self.assertEqual(rc, 0)
        self.assertEqual(response, {})
        self.assertEqual(domblk_calls, ["virsh domblklist gold021-xqnxx"] * 2)
        self.assertEqual(attached_targets, ["sdy", "sdz"])


if __name__ == "__main__":
    import unittest

    unittest.main(warnings="ignore")
