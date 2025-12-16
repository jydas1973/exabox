#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/tools/tests_utils.py /main/1 2025/05/06 06:50:19 aypaul Exp $
#
# tests_utils.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_utils.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      04/24/25 - Creation
#
import unittest
from unittest import mock
from unittest.mock import patch

from exabox.tools.Utils import mBackupFile
from exabox.log.LogMgr import ebLogInfo
from exabox.core.Error import ExacloudRuntimeError

class ebTestUtils(unittest.TestCase):

    def setUp(self):
        super().setUp()

    def test_mBackupFile(self):
        ebLogInfo("Running unit tests on Utils.mBackupFile")

        self.assertRaises(ExacloudRuntimeError, mBackupFile, "config/exabox.conf", True)
        self.assertEqual(mBackupFile("config/exabox.conf"), False)

        with patch ('os.path.exists', return_value=False):
            self.assertRaises(ExacloudRuntimeError, mBackupFile, "/u01/admin/exacloud/config/exabox.conf", True)
            self.assertEqual(mBackupFile("/u01/admin/exacloud/config/exabox.conf"), False)

        with patch ('os.path.exists', return_value=True), \
             patch ('shutil.copy2', side_effect=iter([PermissionError,PermissionError,Exception])):
             self.assertRaises(ExacloudRuntimeError, mBackupFile, "/u01/admin/exacloud/config/exabox.conf", True)
             self.assertEqual(mBackupFile("/u01/admin/exacloud/config/exabox.conf"), False)
             self.assertRaises(ExacloudRuntimeError, mBackupFile, "/u01/admin/exacloud/config/exabox.conf", True)
             self.assertEqual(mBackupFile("/u01/admin/exacloud/config/exabox.conf"), False)

        with patch ('os.path.exists', side_effect=iter([True,True,True,True])), \
             patch ('shutil.copy2'), \
             patch ('os.remove'), \
             patch ('shutil.move', side_effect=iter([Exception,Exception])):
             self.assertRaises(ExacloudRuntimeError, mBackupFile, "/u01/admin/exacloud/config/exabox.conf", True)
             self.assertEqual(mBackupFile("/u01/admin/exacloud/config/exabox.conf"), False)

        with patch ('os.path.exists', side_effect=iter([True,False,True,True])), \
             patch ('shutil.copy2'), \
             patch ('os.remove'), \
             patch ('shutil.move'):
             self.assertEqual(mBackupFile("/u01/admin/exacloud/config/exabox.conf"), True)
             self.assertEqual(mBackupFile("/u01/admin/exacloud/config/exabox.conf"), True)

        ebLogInfo("Unit test on Utils.mBackupFile successful.")

if __name__ == '__main__':
    unittest.main() 