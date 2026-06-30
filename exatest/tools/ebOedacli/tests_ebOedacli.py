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
#    jfsaldan    05/20/26 - Enh 39120682 - ECRA/EXACLOUD | PREPARE TO PICK UP
#                           OEDA WITHOUT JAVA INCLUDED | ENV VARIABLE JAVA_HOME
#                           NEEDS TO BE SET FOR OEDA TO RUN | JAVA NEEDS TO BE
#                           PACKAGED IN EXACLOUD FOR ALL DEPLOYMENTS
#    aararora    03/03/26 - Bug 38902170: Correct resource leak issues
#    aararora    03/03/26 - Creation
#

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from exabox.tools.ebOedacli.ebOedacli import ebOedacli, mEnsureOedaJavaHome

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
        tmp.__enter__.return_value.name = "./tmp/oedacli.log"
        tmp.__exit__.return_value = False
        mock_tmp.return_value = tmp

        proc = MagicMock()
        proc.poll.return_value = None
        proc.stdin = MagicMock()
        mock_popen.return_value = proc

        os.makedirs("./tmp", exist_ok=True)
        with tempfile.TemporaryDirectory(dir="./tmp") as oeda_dir:
            oedacli_path = os.path.join(oeda_dir, "oedacli")
            with open(oedacli_path, "w") as oedacli_file:
                oedacli_file.write(
                    '#!/bin/sh\nexport JAVA_HOME="/opt/exacloud/java"\necho run\n'
                )

            cli = ebOedacli(aOedacliPath=oedacli_path, aSaveDir=oeda_dir)
            with patch.object(cli, 'mGetOedacliLogLines', return_value=["oedacli>"]), \
                 patch.object(cli, 'mGetOedacliScript', return_value=[]), \
                 patch('builtins.open', MagicMock()):
                cli.mExecute()

        proc.terminate.assert_called_once()
        proc.wait.assert_called_once()

    @patch('exabox.tools.ebOedacli.ebOedacli.get_gcontext')
    def test_mEnsureOedaJavaHome_patches_oeda_scripts(self, mock_ctx):
        mock_ctx.return_value.mGetJavaHome.return_value = "/opt/exacloud/java"

        os.makedirs("./tmp", exist_ok=True)
        with tempfile.TemporaryDirectory(dir="./tmp") as oeda_dir:
            install_path = os.path.join(oeda_dir, "install.sh")
            oedacli_path = os.path.join(oeda_dir, "oedacli")
            for script_path in [install_path, oedacli_path]:
                with open(script_path, "w") as script_file:
                    script_file.write("#!/bin/sh\necho run\n")

            mEnsureOedaJavaHome(oeda_dir)

            expected_lines = [
                "#!/bin/sh\n",
                'export JAVA_HOME="/opt/exacloud/java"\n',
                "echo run\n"
            ]
            for script_path in [install_path, oedacli_path]:
                with open(script_path, "r") as script_file:
                    self.assertEqual(expected_lines, script_file.readlines())
                self.assertTrue(os.path.exists(
                    "{0}.exacloud_java_home.bak".format(script_path)
                ))
            self.assertTrue(os.path.exists(
                os.path.join(oeda_dir, ".exacloud_java_home.lock")
            ))
            mock_ctx.return_value.mGetJavaHome.assert_called_once()

    @patch('exabox.tools.ebOedacli.ebOedacli.get_gcontext')
    def test_mEnsureOedaJavaHome_no_launchers_skips_lock_and_java_lookup(self, mock_ctx):
        os.makedirs("./tmp", exist_ok=True)
        with tempfile.TemporaryDirectory(dir="./tmp") as oeda_dir:
            mEnsureOedaJavaHome(oeda_dir)

            self.assertFalse(os.path.exists(
                os.path.join(oeda_dir, ".exacloud_java_home.lock")
            ))
            mock_ctx.return_value.mGetJavaHome.assert_not_called()

    @patch('exabox.tools.ebOedacli.ebOedacli.get_gcontext')
    def test_mEnsureOedaJavaHome_existing_java_home_skips_rewrite_and_lock(self, mock_ctx):
        os.makedirs("./tmp", exist_ok=True)
        with tempfile.TemporaryDirectory(dir="./tmp") as oeda_dir:
            script_contents = {
                os.path.join(oeda_dir, "install.sh"):
                    '#!/bin/sh\nexport JAVA_HOME="/oeda/java"\necho install\n',
                os.path.join(oeda_dir, "oedacli"):
                    '#!/bin/sh\nJAVA_HOME="/oeda/java"\necho oedacli\n'
            }
            for script_path, content in script_contents.items():
                with open(script_path, "w") as script_file:
                    script_file.write(content)

            mEnsureOedaJavaHome(oeda_dir)

            for script_path, content in script_contents.items():
                with open(script_path, "r") as script_file:
                    self.assertEqual(content, script_file.read())
                self.assertFalse(os.path.exists(
                    "{0}.exacloud_java_home.bak".format(script_path)
                ))
            self.assertFalse(os.path.exists(
                os.path.join(oeda_dir, ".exacloud_java_home.lock")
            ))
            mock_ctx.return_value.mGetJavaHome.assert_not_called()

if __name__ == '__main__':
    unittest.main() 
