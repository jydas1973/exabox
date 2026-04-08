#!/bin/python
#
# $Header: tests_ebOedacli.py 03-mar-2026.10:47:50 aararora Exp $
#
# tests_ebOedacli.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_ebOedacli.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    03/03/26 - Bug 38902170: Correct resource leak issues
#    aararora    03/03/26 - Creation
#

import unittest
from unittest.mock import MagicMock, patch

from exabox.tools.ebOedacli.ebOedacli import ebOedacli

with patch('multiprocessing.Lock', return_value=MagicMock()):
    from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

class TestEbOedacli(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        with patch.object(
            ebTestClucontrol, "setUpClass", autospec=True
        ) as _mock_setup:
            _mock_setup.return_value = None
            super(TestEbOedacli, self).setUpClass(False, False)

    @patch('exabox.tools.ebOedacli.ebOedacli.subprocess.run')
    @patch('exabox.tools.ebOedacli.ebOedacli.subprocess.Popen')
    @patch('exabox.tools.ebOedacli.ebOedacli.tempfile.NamedTemporaryFile')
    @patch('exabox.tools.ebOedacli.ebOedacli.get_gcontext')
    @patch('exabox.tools.ebOedacli.ebOedacli.ebOedacli.mProbePath', return_value=True)
    def test_mExecute_closes_subprocess(self, mock_probe, mock_ctx, mock_tmp, mock_popen, mock_run):
        mock_ctx.return_value.mGetConfigOptions.return_value = {
            "oedacli_extra_args": "",
            "oedacli_ignorable_messages": []
        }
        mock_ctx.return_value.mGetExaKms.return_value.mGetDefaultKeyAlgorithm.return_value = "RSA"

        tmp = MagicMock()
        tmp.__enter__.return_value.name = "/tmp/oedacli.log"
        tmp.__exit__.return_value = False
        mock_tmp.return_value = tmp

        proc = MagicMock()
        proc.poll.return_value = None
        proc.stdin = MagicMock()
        mock_popen.return_value = proc

        cli = ebOedacli(aOedacliPath="/bin/true", aSaveDir="/tmp")
        with patch.object(cli, 'mGetOedacliLogLines', return_value=["oedacli>"]), \
             patch.object(cli, 'mGetOedacliScript', return_value=[]), \
             patch('builtins.open', MagicMock()):
            cli.mExecute()

        proc.terminate.assert_called_once()
        proc.wait.assert_called_once()

if __name__ == '__main__':
    unittest.main() 
