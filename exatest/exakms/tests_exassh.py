#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/exakms/tests_exassh.py /main/11 2026/02/05 19:38:13 bhpati Exp $
#
# tests_exassh.py
#
# Copyright (c) 2021, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_exassh.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    06/19/26 - Bug#39568198 Support RoCE switch download without
#                           SFTP
#    jesandov    04/27/26 - 39263025: Fix vulnerabilities found by IA
#    bhpati      01/27/26 - Enh 38820677 - EXASSH WITH DEBUG FLAG SHOULD WRITE
#                           THE ENTRIES TO THE LOG FILE WHEN IT IS RAN WITH -FL
#                           FLAG
#    ririgoye    08/03/23 - Enh 35637033 - Added unit test for remote file
#                           execution
#    jesandov    05/31/22 - Add ExaKms KeyValue Info
#    aypaul      09/02/21 - Bug#33306269 Fix authorized keys file access issue
#                           on build machines.
#    jesandov    06/07/21 - Creation
#

import os
import unittest
import stat
import logging
import inspect
import socket
import base64
import gzip
import tempfile
import paramiko

from random import shuffle
from unittest.mock import patch
from unittest import mock

from exabox.core.Context import get_gcontext, set_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.exakms.ExaKms import ExaKms
from exabox.exakms.ExaKmsEntry import ExaKmsEntry
from exabox.exakms.ExaKmsKeysDB import ExaKmsKeysDB
from exabox.exakms.ExaKmsFileSystem import ExaKmsFileSystem
from exabox.exakms.ExaKmsSingleton import ExaKmsSingleton

from exabox.exassh.ExasshManager import ExasshManager
from exabox.exassh.ExasshScript import ExasshScript

import shlex, subprocess

SKIP_UT=True

def mExecuteCmd(aArgs, aFail=True):
    try:
        print(aArgs, flush=True)
        proc = subprocess.Popen(aArgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        outs, errs = proc.communicate()
        _msg = f"Cmd: {aArgs} returned: {proc.returncode}.\nstdout:'{outs}',\nstderr:'{errs}'"
        print(_msg, flush=True)
        if proc.returncode != 0:
            if aFail:
                raise RuntimeError(_msg)
        return outs.decode("utf8"), errs.decode("utf8")
    except:
        proc.kill()
        raise

class ebTestExaKms(ebTestClucontrol):

    @classmethod
    def setUpClass(self):

        super().setUpClass(aGenerateDatabase=True, aUseOeda=True)

        self.authorizedKeysFile = os.path.expanduser('~/.ssh/authorized_keys')
        self.currentPermissions = os.stat(self.authorizedKeysFile).st_mode
        if self.currentPermissions & stat.S_IWUSR != 1:
            os.chmod(self.authorizedKeysFile, stat.S_IRUSR | stat.S_IWUSR)

        _exakms_keys = os.path.abspath(os.path.join(self.mGetUtil(self).mGetOutputDir(), "exakms_keys"))
        _exakms_keys_bk = os.path.abspath(os.path.join(self.mGetUtil(self).mGetOutputDir(), "exakms_keys_bk"))

        self.mGetClubox(self).mGetCtx().mSetConfigOption('exakms_fs_keypath', _exakms_keys)
        self.mGetClubox(self).mGetCtx().mSetConfigOption('exakms_fs_keypath_bk', _exakms_keys_bk)
        self.mGetClubox(self).mGetCtx().mSetConfigOption('exakms_type', 'ExaKmsFileSystem')
        self.mGetClubox(self).mGetCtx().mSetConfigOption('enable_block_opctl', 'True')
        self.exakmsSingleton = ExaKmsSingleton()

        self.exakms = ExaKmsFileSystem()
        self.user = os.environ["USER"]
        self.home = os.environ["HOME"]
        self.host = os.environ["HOSTNAME"]
        
        self.mGenerateLocalKey(self)

    @classmethod
    def tearDownClass(self):
        self.mCleanUpKeys(self)
        os.chmod(self.authorizedKeysFile, self.currentPermissions)

    def mCleanUpKeys(self):

        # Delete all keys
        _entries = self.exakms.mSearchExaKmsEntries({})
        for _entry  in _entries:
            self.exakms.mDeleteExaKmsEntry(_entry)

        # Delete all exatest_keys
        _home = os.environ["HOME"]
        mExecuteCmd(["/bin/sed", "-i", "/exatest_key/d", f"{_home}/.ssh/authorized_keys"])

    def mGenerateLocalKey(self):

        _entry = self.exakms.mBuildExaKmsEntry(self.host, self.user, self.exakms.mGetEntryClass().mGeneratePrivateKey())
        self.exakms.mInsertExaKmsEntry(_entry)

        _pubkey =  _entry.mGetPublicKey("exatest_key")

        mExecuteCmd(["/bin/mkdir", "-p", f"{self.home}/.ssh"])
        mExecuteCmd(["/bin/chmod", "700", f"{self.home}/.ssh"])

        with open(f"{self.home}/.ssh/authorized_keys", "a+") as _f:
            _f.write(_pubkey)
            _f.write("\n")

        print(f"Host info: {socket.getfqdn()} / {socket.gethostname()}", flush=True)

        mExecuteCmd(["/bin/chmod", "600", f"{self.home}/.ssh/authorized_keys"])
        mExecuteCmd(["/usr/bin/ssh-keygen", "-R", socket.getfqdn()])
        mExecuteCmd(["/usr/bin/ssh-keygen", "-R", socket.gethostname()])

        _commandBase = ["/bin/ssh", "-o", "PasswordAuthentication=no", "-o", "StrictHostKeyChecking=accept-new"]

        mExecuteCmd(_commandBase + [f"{self.user}@{socket.getfqdn()}", '/bin/echo new'], aFail=False)
        mExecuteCmd(_commandBase + [f"{self.user}@{socket.gethostname()}", '/bin/echo new'], aFail=False)

    def test_000_command(self):

        if SKIP_UT:
            return

        _commandRc = 1

        try:

            _cparam = {"FQDN": self.host, "user": self.user}
            _exassh = ExasshManager(self.mGetClubox(), aConsoleLog=True, aFileLog=True)
            _exassh.mSetExaKmsSingleton(self.exakmsSingleton)
            _exassh.mSetConnParams(_cparam)
            _exassh.mConnect()

            _commandRc, _stdout, _stderr = _exassh.mExecuteSshCommand("hostname")
            self.assertEqual(_stdout.strip(),self.host)

        finally:

            _exassh.mDisconnect()

        self.assertEqual(_commandRc, 0)

    def test_001_status(self):

        _exassh = ExasshManager(self.mGetClubox(), aConsoleLog=False, aFileLog=True)
        _exassh.mSetExaKmsSingleton(self.exakmsSingleton)
        _exassh.mSetMode("soft")

        _cparams = {"FQDN": self.host, "user": self.user}
        _exassh.mSetConnParams(_cparams)
        _entries = _exassh.mSearchExaKms()
        _status = _exassh.mGetHostStatus(_entries[0])

        self.assertEqual(_status["pingable"], True)

    def test_002_download_upload(self):

        if SKIP_UT:
            return

        # Create file to upload
        _file1 = os.path.abspath(os.path.join(self.mGetUtil().mGetOutputDir(), "exassh_example0.txt"))
        _file2 = os.path.abspath(os.path.join(self.mGetUtil().mGetOutputDir(), "exassh_example_upload.txt"))
        _file3 = os.path.abspath(os.path.join(self.mGetUtil().mGetOutputDir(), "exassh_example_download.txt"))

        with open(_file1, "w") as _f:
            _f.write("exassh_example")

        try:

            _cparam = {"FQDN": self.host, "user": self.user}

            _exassh = ExasshManager(self.mGetClubox(), aConsoleLog=False, aFileLog=True)
            _exassh.mSetExaKmsSingleton(self.exakmsSingleton)
            _exassh.mSetConnParams(_cparam)
            _exassh.mConnect()

            _exassh.mUpload(_file1, _file2)
            _exassh.mDownload(_file2, _file3)

            self.assertTrue(os.path.exists(_file3))

            _c = ""
            with open(_file3, "r") as _f:
                _c = _f.read()

            self.assertEqual(_c, "exassh_example")

        finally:
            _exassh.mDisconnect()

    def test_003_download_upload_recursive(self):

        if SKIP_UT:
            return

        # Create file to upload
        _dirDW = os.path.abspath(os.path.join(self.mGetUtil().mGetOutputDir(), "exassh_workdir_dw"))
        _dirUP = os.path.abspath(os.path.join(self.mGetUtil().mGetOutputDir(), "exassh_workdir_up"))

        _dir1 = os.path.abspath(os.path.join(self.mGetUtil().mGetOutputDir(), "exassh_workdir"))
        _dir2 = os.path.join(_dir1, "sample")

        if not os.path.exists(_dir1):
            os.makedirs(_dir1)

        if not os.path.exists(_dir2):
            os.makedirs(_dir2)

        _file1 = os.path.join(_dir2, "exassh_example1")
        _file2 = os.path.join(_dirUP, "sample", "exassh_example1")
        _file3 = os.path.join(_dirDW, "sample", "exassh_example1")

        with open(_file1, "w") as _f:
            _f.write("exassh_example")

        # Do copy and upload
        try:

            _cparam = {"FQDN": self.host, "user": self.user}

            _exassh = ExasshManager(self.mGetClubox(), aConsoleLog=False, aFileLog=True)
            _exassh.mSetExaKmsSingleton(self.exakmsSingleton)
            _exassh.mSetConnParams(_cparam)
            _exassh.mConnect()

            _exassh.mUpload(_dir1, _dirUP)
            _exassh.mDownload(_dirUP, _dirDW)

            self.assertTrue(os.path.exists(_file1))
            self.assertTrue(os.path.exists(_file2))
            self.assertTrue(os.path.exists(_file3))

            _c = ""
            with open(_file3, "r") as _f:
                _c = _f.read()

            self.assertEqual(_c, "exassh_example")

        finally:
            _exassh.mDisconnect()


    def test_004_print(self):

        _exassh = ExasshManager(self.mGetClubox(), aConsoleLog=False, aFileLog=True)
        _exassh.mSetExaKmsSingleton(self.exakmsSingleton)

        _exassh.mSetOutput("delimiter")
        _exassh.mPrintAll()

        _exassh.mSetOutput("json")
        _exassh.mPrintAll()

        _exassh.mSetOutput("default")
        _exassh.mPrintAll()

    def test_005_status_bad(self):

        try:

            _basepath = os.path.abspath(self.mGetUtil().mGetOutputDir())

            # Prepare keysdb env
            if not os.path.exists(f"{_basepath}/dbcli/bin/mkstore"):
                mExecuteCmd(["/bin/mkdir", "-p", f"{_basepath}/dbcli/"])
                mExecuteCmd(["/usr/bin/unzip", "packages/wallet_util.zip", "-d", f"{_basepath}/dbcli/"])

            get_gcontext().mSetRegEntry("MKSTORE_BASEPATH", _basepath)
            self.mGetClubox().mGetCtx().mSetConfigOption('exakms_type', 'ExaKmsKeysDB')

            _exakms = ExaKmsKeysDB()
            _exakmsSingleton = ExaKmsSingleton()

            _manager = ExasshManager(self.mGetClubox(), aConsoleLog=False, aFileLog=True)
            _manager.mSetExaKmsSingleton(_exakmsSingleton)
            _manager.mSetMode("soft")

            # Create dummy entry
            _invalidEntry = _exakms.mBuildExaKmsEntry("dummy", "dummy", self.exakms.mGetEntryClass().mGeneratePrivateKey())
            _exakms.mInsertExaKmsEntry(_invalidEntry)

            # Find dummy entry and change the PkDB
            _cparams = {"FQDN": "dummy", "user": "dummy"}
            _manager.mSetConnParams(_cparams)
            _entries = _manager.mSearchExaKms()
            _entries[0].mSetPkDB("invalid")

            _exakms.mDeleteExaKmsEntry(_invalidEntry)

            # Validate that it fails
            _status = _manager.mGetHostStatus(_entries[0], aValidateEntry=True)
            self.assertTrue("invalid" in _status)

        finally:
            self.mGetClubox().mGetCtx().mSetConfigOption('exakms_type', 'ExaKmsFileSystem')

    def test_006_exassh_mina(self):

        _exasshScript = ExasshScript()
        _exasshScript.mArgsParse()

        _exasshScript.mCreateManager([
            self.host,
            "--mina",
            "-u", self.user,
            "-e", "/bin/echo x"
        ])


        _manager = _exasshScript.mGetExassManager()
        _manager.mSetClubox(self.mGetClubox())
        _manager.mSetExaKmsSingleton(self.exakmsSingleton)
        set_gcontext(self.mGetClubox().mGetCtx())

        _rc = _exasshScript.mExecute()
        self.assertEqual(_rc, 0)


    def test_006_exassh_script(self):

        _exasshScript = ExasshScript()
        _exasshScript.mArgsParse()

        _exasshScript.mCreateManager([
            self.host,
            "-u", self.user,
            "-sl", "-fl", "-nc",
            "-k", "x",
            "-w", "1000",
            "-o", "json",
            "-e", "/bin/echo hi"
        ])

        _manager = _exasshScript.mGetExassManager()
        _manager.mSetExaKmsSingleton(self.exakmsSingleton)
        set_gcontext(self.mGetClubox().mGetCtx())

        _rc = _exasshScript.mExecute()
        self.assertEqual(_rc, 0)

    def test_097_status_bad_exassh_script(self):

        def get_status_pregenerate(aExaKmsEntry, aValidateEntry=True):

            return {
                "FQDN": self.host,
                "user": self.user,
                "invalid": True
            }

        _exakms = self.exakmsSingleton.mGetExaKms()
        _exasshScript = ExasshScript()
        _exasshScript.mArgsParse()

        # Upload not existing file to host 1
        _exasshScript.mCreateManager([
            self.host,
            "-u", self.user,
            "-s",
            "-nc", "-fl",
            "-oi", "-di"
        ])

        _manager = _exasshScript.mGetExassManager()
        _manager.mSetExaKmsSingleton(self.exakmsSingleton)
        _manager.mGetHostStatus = get_status_pregenerate
        set_gcontext(self.mGetClubox().mGetCtx())

        # Find dummy entry and change the PkDB
        self.assertEqual(len(_exakms.mSearchExaKmsEntries({})), 1)

        _rc = _exasshScript.mExecute()
        self.assertEqual(_rc, 0)

        self.assertEqual(len(_exakms.mSearchExaKmsEntries({})), 0)

    @patch('exabox.exassh.ExasshManager.ExasshManager.mStartCli')
    def test_008_optcl_flag(self, mock_prepareChannel):

        # Mock functions
        mock_prepareChannel.return_value = 0

        # Create script
        _exakms = self.exakmsSingleton.mGetExaKms()
        _exasshScript = ExasshScript()
        _exasshScript.mArgsParse()

        # Add OPCTL_ENABLE flag
        _entry = _exakms.mGetExaKmsEntry({"FQDN": self.host, "user": self.user})
        _entry.mGetKeyValueInfo()["OPCTL_ENABLE"] = "TRUE"
        _exakms.mUpdateKeyValueInfo(_entry)

        # Upload not existing file to host 1
        _exasshScript.mCreateManager([
            self.host,
            "-u", self.user
        ])

        _manager = _exasshScript.mGetExassManager()
        _manager.mSetExaKmsSingleton(self.exakmsSingleton)
        set_gcontext(self.mGetClubox().mGetCtx())

        # Execute
        _rc = _exasshScript.mExecute()
        self.assertEqual(_rc, 126)

        # Remove flag
        _entry = _exakms.mGetExaKmsEntry({"FQDN": self.host, "user": self.user})
        del _entry.mGetKeyValueInfo()["OPCTL_ENABLE"]
        _exakms.mUpdateKeyValueInfo(_entry)

        # Retry connection
        _rc = _exasshScript.mExecute()
        self.assertEqual(_rc, 0)
    

    def test_009_remotelyexecute_no_args(self):

        if SKIP_UT:
            return

        # Create working directories
        _currDir = os.path.abspath(os.path.join(self.mGetUtil().mGetOutputDir(), "exassh_re_workdir"))

        if not os.path.exists(_currDir):
            os.makedirs(_currDir)

        # Create test script
        _fileContent1 = self.mGetResourcesTextFile("sample_python_executable.py")
        _file1 = os.path.join(_currDir, "exassh_re_test.py")

        with open(_file1, "w") as _f:
            _f.write(_fileContent1)
        mExecuteCmd(["/bin/chmod", "u+x", _file1])

        # Upload created test file
        _exassh = ExasshManager(self.mGetClubox(), aConsoleLog=True, aFileLog=True)

        try:
            # Set connection
            _cparam = {"FQDN": self.host, "user": self.user}
            _exassh.mSetExaKmsSingleton(self.exakmsSingleton)
            _exassh.mSetConnParams(_cparam)
            _exassh.mConnect()
            # Check that remote file runs fine 
            _commandRc = _exassh.mRemotelyExecute(_file1, [])
            # Execute uploaded file
            self.assertEqual(_commandRc, 0)
        finally:
            _exassh.mDisconnect()


    def test_010_remotelyexecute_with_args(self):

        if SKIP_UT:
            return

        # Create working directories
        _currDir = os.path.abspath(os.path.join(self.mGetUtil().mGetOutputDir(), "exassh_re_workdir"))

        if not os.path.exists(_currDir):
            os.makedirs(_currDir)

        # Create test script
        _fileContent1 = self.mGetResourcesTextFile("sample_python_executable.py")
        _file1 = os.path.join(_currDir, "exassh_re_test.py")

        with open(_file1, "w") as _f:
            _f.write(_fileContent1)
        mExecuteCmd(["/bin/chmod", "u+x", _file1])

        # Upload created test file
        _exassh = ExasshManager(self.mGetClubox(), aConsoleLog=True, aFileLog=True)

        try:
            # Set connection
            _cparam = {"FQDN": self.host, "user": self.user}
            _exassh.mSetExaKmsSingleton(self.exakmsSingleton)
            _exassh.mSetConnParams(_cparam)
            _exassh.mConnect()
            # Check that remote file runs fine 
            _commandRc = _exassh.mRemotelyExecute(_file1, ["-r", "-s", "-n"])
            # Execute uploaded file
            self.assertEqual(_commandRc, 0)
        finally:
            _exassh.mDisconnect()

    @patch("logging.FileHandler")
    @patch("os.makedirs")
    @patch("os.getcwd", return_value="/tmp/exacloud/test")
    @patch("exabox.exassh.ExasshManager.ExasshManager.mInitExacloud", return_value=None)
    @patch("logging.getLogger")
    def test_010_paramiko_logger_gets_file_handler(self, mock_get_logger, mock_init, mock_getcwd,
                                                mock_makedirs, mock_file_handler):

        file_handler = mock.Mock(name="file_handler")
        mock_file_handler.return_value = file_handler

        exassh_logger = mock.Mock(name="exassh_logger")
        exassh_logger.handlers = []
        exassh_logger.addHandler.side_effect = lambda handler: exassh_logger.handlers.append(handler)

        paramiko_logger = mock.Mock(name="paramiko_logger")
        paramiko_logger.handlers = []
        paramiko_logger.addHandler.side_effect = lambda handler: paramiko_logger.handlers.append(handler)
        paramiko_logger.level = logging.INFO
        paramiko_logger.setLevel.side_effect = lambda level: setattr(paramiko_logger, "level", level)

        mock_get_logger.side_effect = lambda name: exassh_logger if name == "exassh" else paramiko_logger

        manager = ExasshManager(aConsoleLog=True, aFileLog=True, aSilent=True, aDebug=True)
        manager.mGetLog()

        self.assertIn(file_handler, exassh_logger.handlers)
        self.assertIn(file_handler, paramiko_logger.handlers)
        self.assertEqual(logging.DEBUG, paramiko_logger.level)


    @patch("os.getcwd", return_value="/tmp/exacloud/test")
    @patch("exabox.exassh.ExasshManager.ExasshManager.mInitExacloud", return_value=None)
    def test_011_roce_chunk_size_defaults_and_caps(self, mock_init, mock_getcwd):

        _manager = ExasshManager(aConsoleLog=False, aFileLog=False)
        _context = mock.Mock(name="context")

        with patch("exabox.exassh.ExasshManager.get_gcontext", return_value=_context):
            _context.mCheckConfigOption.return_value = "bad"
            self.assertEqual(_manager.mGetRoceDownloadChunkBytes(), 4 * 1024 * 1024)

            _context.mCheckConfigOption.return_value = "0"
            self.assertEqual(_manager.mGetRoceDownloadChunkBytes(), 4 * 1024 * 1024)

            _context.mCheckConfigOption.return_value = "65"
            self.assertEqual(_manager.mGetRoceDownloadChunkBytes(), 64 * 1024 * 1024)

            _context.mCheckConfigOption.return_value = "16"
            self.assertEqual(_manager.mGetRoceDownloadChunkBytes(), 16 * 1024 * 1024)

    @patch("os.getcwd", return_value="/tmp/exacloud/test")
    @patch("exabox.exassh.ExasshManager.ExasshManager.mInitExacloud", return_value=None)
    def test_012_has_roce_fqdn_uses_raw_requested_conn_and_host_names(self, mock_init, mock_getcwd):

        _manager = ExasshManager(aConsoleLog=False, aFileLog=False)
        self.assertFalse(_manager.mHasRoceFqdn())

        _manager.mSetConnParams({"FQDN": "scaqan17sw-rocea0"})
        self.assertTrue(_manager.mHasRoceFqdn())

        _manager.mSetConnParams({"FQDN": "scaqan17sw-rocea0.us.oracle.com"})
        self.assertTrue(_manager.mHasRoceFqdn())

        _manager.mSetConnParams({"FQDN": "scaqan17sw-leafa0.us.oracle.com"})
        setattr(_manager, "_ExasshManager__host", "scaqan17sw-rocea0.us.oracle.com")
        self.assertTrue(_manager.mHasRoceFqdn())

    @patch("os.getcwd", return_value="/tmp/exacloud/test")
    @patch("exabox.exassh.ExasshManager.ExasshManager.mInitExacloud", return_value=None)
    def test_013_has_roce_fqdn_uses_requested_conn_and_entry_names(self, mock_init, mock_getcwd):

        _manager = ExasshManager(aConsoleLog=False, aFileLog=False)
        _entry = mock.Mock(name="entry")
        _entry.mGetFQDN.return_value = "stored-switch-entry.example.com"

        self.assertFalse(_manager.mHasRoceFqdn())

        _manager.mSetConnParams({"FQDN": "rack-sw-rocea0.example.com"})
        self.assertTrue(_manager.mHasRoceFqdn())

        _manager.mGetConnParams()["FQDN"] = "stored-switch-entry.example.com"
        self.assertTrue(_manager.mHasRoceFqdn())

        _manager.mSetConnParams({"FQDN": "stored-switch-entry.example.com"})
        _entry.mGetFQDN.return_value = "rack-sw-rocea0.example.com"
        _manager.mSetConnectedEntry(_entry)
        self.assertTrue(_manager.mHasRoceFqdn())

    @patch("os.getcwd", return_value="/tmp/exacloud/test")
    @patch("exabox.exassh.ExasshManager.ExasshManager.mInitExacloud", return_value=None)
    def test_014_roce_guestshell_file_size_ignores_prompt_noise(self, mock_init, mock_getcwd):

        _manager = ExasshManager(aConsoleLog=False, aFileLog=False)

        with patch.object(_manager, "mExecuteGuestShellMarkedCommand", return_value="12345\n>\n"):
            self.assertEqual(_manager.mGetRoceGuestShellFileSize("/var/log/messages"), 12345)

    @patch("os.getcwd", return_value="/tmp/exacloud/test")
    @patch("exabox.exassh.ExasshManager.ExasshManager.mInitExacloud", return_value=None)
    def test_015_roce_guestshell_file_size_error_has_message(self, mock_init, mock_getcwd):

        _manager = ExasshManager(aConsoleLog=False, aFileLog=False)

        with patch.object(_manager, "mExecuteGuestShellMarkedCommand", return_value=">\n"):
            with self.assertRaises(Exception) as _ctx:
                _manager.mGetRoceGuestShellFileSize("/var/log/messages")

        self.assertIn("Exacloud error code: 0", str(_ctx.exception))
        self.assertIn("Unable to determine remote file size from guestshell output", str(_ctx.exception))
        self.assertNotIn("No Error Message Defined", str(_ctx.exception))

    @patch("os.getcwd", return_value="/tmp/exacloud/test")
    @patch("exabox.exassh.ExasshManager.ExasshManager.mInitExacloud", return_value=None)
    def test_016_download_roce_guestshell_writes_complete_file_atomically(self, mock_init, mock_getcwd):

        _content = b"hello from roce guestshell"
        _payload = base64.b64encode(gzip.compress(_content)).decode("ascii")
        _manager = ExasshManager(aConsoleLog=False, aFileLog=False)

        with tempfile.TemporaryDirectory() as _tmpdir:
            _localFile = os.path.join(_tmpdir, "messages")

            with patch.object(_manager, "mEnterRoceGuestShell"), \
                 patch.object(_manager, "mGetRoceGuestShellFileSize", return_value=len(_content)), \
                 patch.object(_manager, "mGetRoceDownloadChunkBytes", return_value=1024), \
                 patch.object(_manager, "mGetRoceDownloadChunkTimeout", return_value=180), \
                 patch.object(_manager, "mExecuteGuestShellMarkedCommand", return_value=_payload):

                self.assertEqual(_manager.mDownloadRoceGuestShellFile("/var/log/messages", _localFile), 0)

            with open(_localFile, "rb") as _file:
                self.assertEqual(_file.read(), _content)
            self.assertEqual(
                [f for f in os.listdir(_tmpdir) if f.endswith(".tmp")],
                []
            )

    @patch("os.getcwd", return_value="/tmp/exacloud/test")
    @patch("exabox.exassh.ExasshManager.ExasshManager.mInitExacloud", return_value=None)
    def test_017_download_roce_guestshell_preserves_existing_file_on_failure(self, mock_init, mock_getcwd):

        _manager = ExasshManager(aConsoleLog=False, aFileLog=False)

        with tempfile.TemporaryDirectory() as _tmpdir:
            _localFile = os.path.join(_tmpdir, "messages")
            with open(_localFile, "wb") as _file:
                _file.write(b"existing")

            with patch.object(_manager, "mEnterRoceGuestShell"), \
                 patch.object(_manager, "mGetRoceGuestShellFileSize", return_value=16), \
                 patch.object(_manager, "mGetRoceDownloadChunkBytes", return_value=1024), \
                 patch.object(_manager, "mGetRoceDownloadChunkTimeout", return_value=180), \
                 patch.object(_manager, "mExecuteGuestShellMarkedCommand", side_effect=RuntimeError("chunk failed")):

                self.assertEqual(_manager.mDownloadRoceGuestShellFile("/var/log/messages", _localFile), 1)

            with open(_localFile, "rb") as _file:
                self.assertEqual(_file.read(), b"existing")
            self.assertEqual(
                [f for f in os.listdir(_tmpdir) if f.endswith(".tmp")],
                []
            )

    @patch("os.getcwd", return_value="/tmp/exacloud/test")
    @patch("exabox.exassh.ExasshManager.ExasshManager.mInitExacloud", return_value=None)
    def test_018_drain_interactive_channel_logs_and_raises(self, mock_init, mock_getcwd):

        _manager = ExasshManager(aConsoleLog=False, aFileLog=False)
        _channel = mock.Mock(name="channel")
        _channel.recv_ready.side_effect = RuntimeError("closed")

        with patch.object(_manager, "mGetChannel", return_value=_channel), \
             patch.object(_manager.mGetLog(), "error") as _error:
            with self.assertRaises(RuntimeError):
                _manager.mDrainInteractiveChannel()

        _error.assert_any_call("Failed to drain interactive SSH channel: closed")



    @patch("os.getcwd", return_value="/tmp/exacloud/test")
    @patch("exabox.exassh.ExasshManager.ExasshManager.mInitExacloud", return_value=None)
    def test_019_download_retries_guestshell_when_sftp_fails_on_roce(self, mock_init, mock_getcwd):

        _manager = ExasshManager(aConsoleLog=False, aFileLog=False)
        _manager.mSetConnParams({"FQDN": "rack-sw-rocea0.example.com"})
        _channel = mock.Mock(name="channel")
        _channel.get_transport.return_value = mock.Mock(name="transport")

        with patch.object(_manager, "mGetChannel", return_value=_channel), \
             patch.object(_manager, "mDownloadRoceGuestShellFile", return_value=0) as _download, \
             patch("exabox.exassh.ExasshManager.paramiko.SFTPClient.from_transport", side_effect=paramiko.SSHException("Subsystem request failed")):

            self.assertEqual(_manager.mDownload("/var/log/messages", "messages"), 0)
            _download.assert_called_once_with("/var/log/messages", "messages")

    @patch("os.getcwd", return_value="/tmp/exacloud/test")
    @patch("exabox.exassh.ExasshManager.ExasshManager.mInitExacloud", return_value=None)
    def test_020_download_does_not_retry_guestshell_for_non_roce_sftp_failure(self, mock_init, mock_getcwd):

        _manager = ExasshManager(aConsoleLog=False, aFileLog=False)
        _manager.mSetConnParams({"FQDN": "rack-sw-leafa0.example.com"})
        _channel = mock.Mock(name="channel")
        _channel.get_transport.return_value = mock.Mock(name="transport")

        with patch.object(_manager, "mGetChannel", return_value=_channel), \
             patch.object(_manager, "mDownloadRoceGuestShellFile", return_value=0) as _download, \
             patch("exabox.exassh.ExasshManager.paramiko.SFTPClient.from_transport", side_effect=paramiko.SSHException("Channel closed")):

            self.assertEqual(_manager.mDownload("/var/log/messages", "messages"), 1)
            _download.assert_not_called()



if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end of file
