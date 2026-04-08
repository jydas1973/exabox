#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_host_state.py jesandov_bug-39109980/1 2026/03/23 15:21:00 jesandov Exp $
#
# tests_host_state.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_host_state.py - Unit tests for host_state endpoint
#
#    DESCRIPTION
#      Validates the reachability checks orchestrated by the host_state handler.
#
#    NOTES
#      Uses exatest mocking helpers to emulate SSH and local command execution.
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    03/23/26 - Creation
#

import copy
import re
import unittest

from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebExacloudUtil import ebJsonObject
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol


class TestHostState(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_missing_hostname_returns_missing_param_error(self):
        """Verify we surface parameter error when hostname is absent."""
        clubox = self.mGetClubox()
        original_options = clubox.mGetOptions()
        if original_options is not None:
            original_options = copy.deepcopy(original_options)

        try:
            clubox.mSetOptions(ebJsonObject({}))
            rc = clubox.mHandlerHostState()
        finally:
            clubox.mSetOptions(original_options)

        self.assertEqual(rc, 0x0119)

    def test_ping_failure_returns_connectivity_error(self):
        """Ensure we stop when the target host cannot be pinged."""
        clubox = self.mGetClubox()
        ctx = self.mGetContext()
        original_options = clubox.mGetOptions()
        if original_options is not None:
            original_options = copy.deepcopy(original_options)

        host = clubox.mReturnDom0DomUPair()[0][0]
        host_regex = re.escape(host)
        options = ebJsonObject({"jsonconf": {"hostname": host}})

        _cmd = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand(
                        rf"/bin/ping\s+-c\s+1\s+{host_regex}\s*",
                        aRc=1,
                        aStderr="mocked ping failure",
                        aPersist=True,
                    )
                ]
            ],
        }

        try:
            clubox.mSetOptions(options)
            self.mPrepareMockCommands(_cmd)
            rc = clubox.mHandlerHostState()
        finally:
            clubox.mSetOptions(original_options)
            args_options = ctx.mGetArgsOptions()
            args_options.pop("mock_cmds", None)
            args_options.pop("mock_cmds_instances", None)
            self.mGetClubox().mGetLocalNode().mSetMockMode(False)

        self.assertEqual(rc, 0x0403)

    def test_success_executes_hostname_check(self):
        """Happy path issues hostname -f on the remote host."""
        clubox = self.mGetClubox()
        ctx = self.mGetContext()
        original_options = clubox.mGetOptions()
        if original_options is not None:
            original_options = copy.deepcopy(original_options)

        host = clubox.mReturnDom0DomUPair()[0][0]
        host_regex = re.escape(host)
        options = ebJsonObject({"jsonconf": {"hostname": host}})

        _cmd = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand(
                        rf"/bin/ping\s+-c\s+1\s+{host_regex}\s*",
                        aRc=0,
                        aStdout="mocked ping success",
                        aPersist=True,
                    )
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(
                        r"hostname\s+-f",
                        aRc=0,
                        aStdout=f"{host}\n",
                    )
                ]
            ],
        }

        try:
            clubox.mSetOptions(options)
            self.mPrepareMockCommands(_cmd)
            rc = clubox.mHandlerHostState()
        finally:
            clubox.mSetOptions(original_options)
            args_options = ctx.mGetArgsOptions()
            args_options.pop("mock_cmds", None)
            args_options.pop("mock_cmds_instances", None)
            self.mGetClubox().mGetLocalNode().mSetMockMode(False)

        self.assertEqual(rc, 0)


if __name__ == '__main__':
    unittest.main(warnings='ignore')


# end file
