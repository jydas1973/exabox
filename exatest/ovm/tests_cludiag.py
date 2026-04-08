#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cludiag.py /main/2 2025/10/21 04:37:43 hcheon Exp $
#
# tests_cludiag.py
#
# Copyright (c) 2021, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_cludiag.py - Unit test for cludiag
#
#    DESCRIPTION
#      Run tests for cludiag
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    hcheon      03/03/26 - 39030501 Fixed command hang
#    hcheon      10/12/25 - 38491623 Fixed tail command hang
#    alsepulv    12/14/21 - Creation
#

import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from exabox.agent.ebJobRequest import ebJobRequest
from exabox.core.Context import get_gcontext
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.ovm.cludiag import exaBoxDiagCtrl


class ebTestCludiag(ebTestClucontrol):
    __real_popen = subprocess.Popen

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    @patch('exabox.ovm.cludiag.ebGetDefaultDB')
    def test_collect_log(self, _db_mock):
        _options = self.mGetContext().mGetArgsOptions()
        _options.diagtype = "dom0,domU,cell,switch"
        _options.jsonconf = self.mGetPayload()
        _options.jsonconf['log_collection_targets'] = {}

        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("/bin/date +%:z",
                                   aRc=0, aStdout="-08:00", aPersist=True),
                    exaMockCommand("/bin/date +%s",
                                   aRc=0, aStdout="1639520412", aPersist=True),
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/date +%:z",
                                   aRc=0, aStdout="-08:00", aPersist=True),
                    exaMockCommand("/bin/date +%s",
                                   aRc=0, aStdout="1639520412", aPersist=True),
                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/date +%:z",
                                   aRc=0, aStdout="-08:00", aPersist=True),
                    exaMockCommand("/bin/date +%s",
                                   aRc=0, aStdout="1639520412", aPersist=True),
                ]
            ],
            self.mGetRegexSwitch(): [
                    exaMockCommand("/bin/date +%:z",
                                   aRc=0, aStdout="-08:00", aPersist=True),
                    exaMockCommand("/bin/date +%s",
                                   aRc=0, aStdout="1639520412", aPersist=True),
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _req = ebJobRequest("version", {})
        self.mGetClubox().mSetRequestObj(_req)

        _diag_ctrl = exaBoxDiagCtrl(self.mGetClubox())
        _cmd = "collect_log"
        self.assertEqual(_diag_ctrl.mRunDiagnosis(_cmd, _options), 0)

    def _mCreateDummyFile(self, aPath, aSize):
        with open(__file__) as f:
            _data = f.read()
        _written = 0
        with open(aPath, 'w') as f:
            while _written < aSize:
                _written += f.write(_data)

    @patch('exabox.ovm.cludiag.subprocess.Popen')
    def test_mDownloadLogFile_on_local(self, aPopenMock):
        def _remove_sudo(cmd, *args, **kwargs):
            if cmd[0].endswith('sudo'):
                cmd = cmd[1:]
            return self.__real_popen(cmd, *args, **kwargs)

        aPopenMock.side_effect = _remove_sudo
        _diag_ctrl = exaBoxDiagCtrl(self.mGetClubox())
        with tempfile.TemporaryDirectory() as tmp_dir:
            os.makedirs(tmp_dir, exist_ok=True)
            _src = os.path.join(tmp_dir, 'input')
            _dst = os.path.join(tmp_dir, 'output')
            _offset = 500_000
            _size = 30_000_000
            self._mCreateDummyFile(_src, _offset + _size + 1)
            _diag_ctrl.mDownloadLogFile(None, _src, _dst, _offset, _size, 'cps')

            with open(_src, 'rb') as f:
                _expected = f.read()[_offset:_offset+_size]
            with open(_dst, 'rb') as f:
                _result = f.read()
            self.assertEqual(_expected, _result)

    @patch('exabox.ovm.cludiag.ebLogDiag')
    @patch('exabox.ovm.cludiag.subprocess.Popen')
    def test_mDownloadLogFile_timeout(self, aPopenMock, aLogMock):
        class _FakeStdout(object):
            def close(self):
                return None

        class _FakeProc(object):
            def __init__(self, cmd, stdout):
                self.cmd = cmd
                self.stdout = stdout
                self.terminated = False
                self.killed = False

            def wait(self, timeout=None):
                if self.killed:
                    return 0
                raise subprocess.TimeoutExpired(self.cmd, timeout)

            def terminate(self):
                self.terminated = True

            def kill(self):
                self.killed = True

        _procs = []

        def _mock_popen(cmd, stdin=None, stdout=None):
            _stdout = stdout
            if stdout == subprocess.PIPE:
                _stdout = _FakeStdout()
            _proc = _FakeProc(cmd, _stdout)
            _procs.append(_proc)
            return _proc

        aPopenMock.side_effect = _mock_popen
        _diag_ctrl = exaBoxDiagCtrl(self.mGetClubox())
        with tempfile.TemporaryDirectory() as tmp_dir:
            _src = os.path.join(tmp_dir, 'input')
            _dst = os.path.join(tmp_dir, 'output')
            with open(_src, 'wb') as f:
                f.write(b'testdata')
            _diag_ctrl.mDownloadLogFile(None, _src, _dst, 0, 1, 'cps')

        self.assertTrue(all(_proc.terminated for _proc in _procs))
        self.assertTrue(all(_proc.killed for _proc in _procs))
        aLogMock.assert_any_call('ERR', 'Cmd timeout while reading %s' % _src)


if __name__ == '__main__':
    unittest.main()
