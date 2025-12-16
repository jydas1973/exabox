#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/exakms/tests_exakmshistorydb.py /main/2 2022/08/16 12:13:32 jesandov Exp $
#
# tests_exakmshistorydb.py
#
# Copyright (c) 2022, Oracle and/or its affiliates.
#
#    NAME
#      tests_exakmshistorydb.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      06/08/22 - Creation
#
import os, stat
import unittest
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exakms.ExaKmsHistoryDB import ExaKmsHistoryDB
from exabox.exakms.ExaKmsSingleton import ExaKmsSingleton
from exabox.exakms.ExaKmsFileSystem import ExaKmsFileSystem

class ebTestExaKmsHistoryDB(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)

        self.authorizedKeysFile = os.path.expanduser('~/.ssh/authorized_keys')
        self.currentPermissions = os.stat(self.authorizedKeysFile).st_mode
        if self.currentPermissions & stat.S_IWUSR != 1:
            os.chmod(self.authorizedKeysFile, stat.S_IRUSR | stat.S_IWUSR)

        self.mGetClubox(self).mGetCtx().mSetConfigOption('exakms_type', 'ExaKmsFileSystem')
        self.exakmsSingleton = ExaKmsSingleton()

        self.exakms = ExaKmsFileSystem()
        self.user = os.environ["USER"]
        self.home = os.environ["HOME"]
        self.host = os.environ["HOSTNAME"]

    def test_mPutExaKmsHistory(self):

        _mock_exakms_entry = _entry = self.exakms.mBuildExaKmsEntry(self.host, self.user, self.exakms.mGetEntryClass().mGeneratePrivateKey())
        _exakms_history = ExaKmsHistoryDB()
        _exakms_history.mPutExaKmsHistory(_mock_exakms_entry, "insert")
        _exakms_history.mPutExaKmsHistory(_mock_exakms_entry, "delete")

    def test_mGetExaKmsHistory(self):

        _exakms_history = ExaKmsHistoryDB()
        _exakms_history.mGetExaKmsHistory(aUser = "root", aHostName = None, aNumEntries = 10)
        _exakms_history.mGetExaKmsHistory(aUser = "root", aHostName = "scaqab10adm01", aNumEntries = 10)


if __name__ == '__main__':
    unittest.main(warnings='ignore')