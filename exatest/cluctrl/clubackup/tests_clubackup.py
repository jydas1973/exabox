"""

 $Header: 

 Copyright (c) 2018, 2021, Oracle and/or its affiliates. 

 NAME:
      tests_clubackup.py - Unitest for xmlpatching on clucontrol

 DESCRIPTION:
      Run tests for the log backup for VM create fail on clucontrol

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
    ndesanto    11/11/20 - bug 32143165: Remove randint call for securety
    ndesanto    08/06/19 - bug 30139439: Added test for file changing during tar command
    ndesanto    06/24/19 - File creation
"""

import datetime
import unittest
import uuid
import warnings
import os
import socket
import sys
import time
import xml.etree.ElementTree as ET
import exabox.ovm.clubackup as clubackup

from threading import Thread
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode


class ebTest_clubackup(ebTestClucontrol):

    @classmethod
    def setUpClass(self):

        super().setUpClass()

        self._hostname = socket.gethostname().split('.')[0]
        self._files_to_backup = str(os.path.abspath(self.mGetPath(self) + "*"))

        self._dmesg_file_name = "/tmp/dmesg_test.txt"
        self._numbers_file_name = "/tmp/numbers_test.txt"
        self._origin_file = "/tmp/clubackup.test.tar.gz"
        self._result_file = "/tmp/copy.clubackup.test.tar.gz"

    def test_log_backup(self):

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("dmesg > .*"),
                    exaMockCommand("tar.*czf.*"),
                    exaMockCommand("scp.*"),
                    exaMockCommand("rm -f.*"),
                    exaMockCommand("test -e.*"),
                    exaMockCommand("test -e.*"),
                    exaMockCommand("test -e.*", aRc=1),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _node = exaBoxNode(get_gcontext(), True)

        try:
            _node.mConnect("localhost")

            self._files_to_backup = self._dmesg_file_name

            clubackup._backup_log(
                _node.mExecuteCmd,
                _node.mGetCmdExitStatus,
                _node.mCopyFile,
                self._hostname,
                self._files_to_backup,
                self._dmesg_file_name,
                self._origin_file,
                self._result_file
            )

            # Test dmesg worked
            assert(_node.mFileExists(self._dmesg_file_name))

            # Test tar and cp worked
            assert(_node.mFileExists(self._result_file))

            # Test del worked
            assert(_node.mFileExists(self._origin_file) == False)

        finally:
            _node.mDisconnect()


if __name__ == '__main__':
    unittest.main(warnings='ignore')

