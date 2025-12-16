#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/exakms/tests_exassh.py /main/10 2025/01/07 14:09:31 jesandov Exp $
#
# tests_exassh.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
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

from random import shuffle
from unittest.mock import patch

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
        os.system(f"/bin/sed -i '/exatest_key/d' {_home}/.ssh/authorized_keys")

    def mGenerateLocalKey(self):

        _entry = self.exakms.mBuildExaKmsEntry(self.host, self.user, self.exakms.mGetEntryClass().mGeneratePrivateKey())
        self.exakms.mInsertExaKmsEntry(_entry)

        _pubkey =  _entry.mGetPublicKey("exatest_key")

        os.system(f"/bin/mkdir -p {self.home}/.ssh")
        os.system(f"/bin/chmod 700 {self.home}/.ssh")
        os.system(f"/bin/echo '{_pubkey}' >> {self.home}/.ssh/authorized_keys")
        os.system(f"/bin/chmod 600 {self.home}/.ssh/authorized_keys")

    def test_000_command(self):

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
                os.system(f"mkdir -p {_basepath}/dbcli/")
                os.system(f"unzip packages/wallet_util.zip -d {_basepath}/dbcli/ 2>&1 >/dev/null")

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
            "-e", "echo ."
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
            "-e", "echo hi",
            "-sl", "-fl", "-nc",
            "-k", "x",
            "-w", "1000",
            "-o", "json"
        ])

        _manager = _exasshScript.mGetExassManager()
        _manager.mSetExaKmsSingleton(self.exakmsSingleton)
        set_gcontext(self.mGetClubox().mGetCtx())

        _rc = _exasshScript.mExecute()
        self.assertEqual(_rc, 0)

    def test_007_status_bad_exassh_script(self):

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

        # Generate key again after the delete
        self.mGenerateLocalKey()

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
        # Create working directories
        _currDir = os.path.abspath(os.path.join(self.mGetUtil().mGetOutputDir(), "exassh_re_workdir"))

        if not os.path.exists(_currDir):
            os.makedirs(_currDir)

        # Create test script
        _fileContent1 = self.mGetResourcesTextFile("sample_python_executable.py")
        _file1 = os.path.join(_currDir, "exassh_re_test.py")

        with open(_file1, "w") as _f:
            _f.write(_fileContent1)
        os.system(f"/bin/chmod u+x {_file1}")

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
        # Create working directories
        _currDir = os.path.abspath(os.path.join(self.mGetUtil().mGetOutputDir(), "exassh_re_workdir"))

        if not os.path.exists(_currDir):
            os.makedirs(_currDir)

        # Create test script
        _fileContent1 = self.mGetResourcesTextFile("sample_python_executable.py")
        _file1 = os.path.join(_currDir, "exassh_re_test.py")

        with open(_file1, "w") as _f:
            _f.write(_fileContent1)
        os.system(f"/bin/chmod u+x {_file1}")

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


if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end of file
