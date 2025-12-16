#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/exabasedb/tests_cs_createuser.py /main/1 2025/11/25 05:03:58 prsshukl Exp $
#
# tests_cs_createuser.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_createuser.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    11/24/25 - Creation
#

import unittest
from unittest.mock import patch, MagicMock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo, ebLogWarn
from exabox.ovm.csstep.exabasedb.cs_createuser import csCreateUser
from exabox.core.Error import ExacloudRuntimeError


class testCsCreateUser(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super(testCsCreateUser, cls).setUpClass()

    @patch('exabox.ovm.csstep.exabasedb.cs_basedb_util.csBaseDbUtil.mCreateUser')
    def test_doExecute_success(self, mock_mCreateUser):
        """Test doExecute successful user creation"""
        ebLogInfo("Running unit test on cs_createuser.py:test_doExecute_success")
        mock_mCreateUser.return_value = None

        _obj = csCreateUser()
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        steplist = []

        _obj.doExecute(_ebox, _options, steplist)

        mock_mCreateUser.assert_called_once_with(_ebox, _options, steplist, 'ESTP_CREATE_USER')

    @patch('exabox.ovm.csstep.exabasedb.cs_basedb_util.csBaseDbUtil.mCreateUser')
    def test_doExecute_failure(self, mock_mCreateUser):
        """Test doExecute when user creation fails"""
        ebLogInfo("Running unit test on cs_createuser.py:test_doExecute_failure")
        mock_mCreateUser.side_effect = ExacloudRuntimeError(0x0121, 0xA, "User creation failed")

        _obj = csCreateUser()
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        steplist = []

        with self.assertRaises(ExacloudRuntimeError):
            _obj.doExecute(_ebox, _options, steplist)

        mock_mCreateUser.assert_called_once_with(_ebox, _options, steplist, 'ESTP_CREATE_USER')

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetBaseDB')
    @patch.object(csCreateUser, 'mDeleteOpcSSHDirectory')
    def test_undoExecute_success(self, mock_mDeleteOpcSSHDirectory, mock_mGetBaseDB):
        """Test undoExecute successful user deletion"""
        ebLogInfo("Running unit test on cs_createuser.py:test_undoExecute_success")
        mock_basedb = MagicMock()
        mock_basedb.mDeleteUserDomU.return_value = None
        mock_mGetBaseDB.return_value = mock_basedb
        mock_mDeleteOpcSSHDirectory.return_value = None

        _obj = csCreateUser()
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        steplist = []

        _obj.undoExecute(_ebox, _options, steplist)

        mock_mGetBaseDB.assert_called_once()
        mock_basedb.mDeleteUserDomU.assert_called_once_with("opc")
        mock_mDeleteOpcSSHDirectory.assert_called_once_with(_ebox)

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetBaseDB')
    @patch.object(csCreateUser, 'mDeleteOpcSSHDirectory')
    @patch('exabox.log.LogMgr.ebLogWarn')
    def test_undoExecute_delete_user_failure(self, mock_ebLogWarn, mock_mDeleteOpcSSHDirectory, mock_mGetBaseDB):
        """Test undoExecute when user deletion fails but continues"""
        ebLogInfo("Running unit test on cs_createuser.py:test_undoExecute_delete_user_failure")
        mock_basedb = MagicMock()
        mock_basedb.mDeleteUserDomU.side_effect = Exception("Delete user failed")
        mock_mGetBaseDB.return_value = mock_basedb
        mock_mDeleteOpcSSHDirectory.return_value = None

        _obj = csCreateUser()
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        steplist = []

        _obj.undoExecute(_ebox, _options, steplist)

        mock_mGetBaseDB.assert_called_once()
        mock_basedb.mDeleteUserDomU.assert_called_once_with("opc")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetBaseDB')
    @patch.object(csCreateUser, 'mDeleteOpcSSHDirectory')
    @patch('exabox.log.LogMgr.ebLogWarn')
    def test_undoExecute_ssh_directory_failure(self, mock_ebLogWarn, mock_mDeleteOpcSSHDirectory, mock_mGetBaseDB):
        """Test undoExecute when SSH directory deletion fails but continues"""
        ebLogInfo("Running unit test on cs_createuser.py:test_undoExecute_ssh_directory_failure")
        mock_basedb = MagicMock()
        mock_basedb.mDeleteUserDomU.return_value = None
        mock_mGetBaseDB.return_value = mock_basedb
        mock_mDeleteOpcSSHDirectory.side_effect = Exception("SSH delete failed")

        _obj = csCreateUser()
        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        steplist = []

        _obj.undoExecute(_ebox, _options, steplist)

        mock_mGetBaseDB.assert_called_once()
        mock_basedb.mDeleteUserDomU.assert_called_once_with("opc")
        mock_mDeleteOpcSSHDirectory.assert_called_once_with(_ebox)


if __name__ == '__main__':
    unittest.main()
