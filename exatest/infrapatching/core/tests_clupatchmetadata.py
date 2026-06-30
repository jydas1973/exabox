#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/infrapatching/core/tests_clupatchmetadata.py /main/1 2024/10/21 20:15:23 avimonda Exp $
#
# tests_clupatchmetadata.py
#
# Copyright (c) 2024, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_clupatchmetadata.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jyotdas     04/28/26 - Bug 39263019 - Security Scan Finding in
#                           clupatchmetadata.py
#    avimonda    10/15/24 - Bug 37156068 - EXCEPTION IN
#                           MREADPATCHSTATESOBJECTFROMFILE() IS MISLEADING
#    avimonda    10/15/24 - Create file
#    avimonda    10/15/24 - Creation
#

import unittest
from unittest.mock import patch, MagicMock, call
from unittest.mock import patch
import socket
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.infrapatching.core.clupatchmetadata import (
    ebCluPatchStateInfo,
    _mValidatePatchMetadataPath,
)
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand

_VALID_PATH = (
    "/EXAVMIMAGES/dbserver.patch.zip_exadata_ol8_23.1.13.0.0.240510_Linux-x86-64.zip"
    "/dbserver_patch_240510/patch_states_data"
    "/638cf483-a3a9-4165-a6dd-e34e56be6c38_patch_progress_report.json"
)

class ebTestCluPatchMetadata(ebTestClucontrol):

    @patch('exabox.core.Node.exaBoxNode.mConnect')
    def test_mReadPatchStatesObjectFromFile(self, _mock_mConnect):

        ebLogInfo("Executing test_mReadPatchStatesObjectFromFile")

        _mock_mConnect.side_effect = OSError(110, "Connection timed out")

        with self.assertRaises(Exception) as _context:
            _file_Path = "/EXAVMIMAGES/dbserver.patch.zip_exadata_ol8_23.1.13.0.0.240510_Linux-x86-64.zip/dbserver_patch_240510/patch_states_data/638cf483-a3a9-4165-a6dd-e34e56be6c38_patch_progress_report.json"
            _target_node = "iad309809exdd011.iad8xx3xx0321qf.adminiad3.oraclevcn.com"
            _user = 'root'
            result = ebCluPatchStateInfo.mReadPatchStatesObjectFromFile(_file_Path, _target_node, _user) 

        expected_message = "Error: [Errno 110] Connection timed out occurred while trying to read the patch states JSON file: /EXAVMIMAGES/dbserver.patch.zip_exadata_ol8_23.1.13.0.0.240510_Linux-x86-64.zip/dbserver_patch_240510/patch_states_data/638cf483-a3a9-4165-a6dd-e34e56be6c38_patch_progress_report.json from the target node: iad309809exdd011.iad8xx3xx0321qf.adminiad3.oraclevcn.com."
        self.assertEqual(str(_context.exception), expected_message)

        ebLogInfo("Executed test_mReadPatchStatesObjectFromFile")

    def test_mValidatePatchMetadataPath_valid(self):
        valid_paths = [
            '/EXAVMIMAGES/dbserver.patch.zip_ol8/dbserver_patch/patch_states_data/'
                '638cf483-a3a9-4165-a6dd-e34e56be6c38_patch_progress_report.json',
            '/opt/oci/exacc/exacloud/InfraPatchBase/patch_dir/patch_states_data/'
                'aaaabbbb-cccc-dddd-eeee-ffffffffffff_patch_progress_report.json',
            '/var/odo/InfraPatchBase/patch_dir/patch_states_data/'
                '11111111-2222-3333-4444-555555555555_patch_progress_report.json',
            '/u02/patch_dir/patch_states_data/'
                'abcdef01-2345-6789-abcd-ef0123456789_patch_progress_report.json',
        ]
        for p in valid_paths:
            _mValidatePatchMetadataPath(p)

    def test_mValidatePatchMetadataPath_invalid(self):
        invalid_paths = [
            '',
            None,
            '/tmp/evil; rm -rf /',
            '/etc/passwd',
            '../../etc/shadow',
            '/u02/foo;touch /tmp/pwned',
            '/u02/patch_states_data/no_suffix',
            '/home/opc/malicious/patch_states_data/uuid_patch_progress_report.json',
            '/u02/foo/../bar/patch_states_data/638cf483-a3a9-4165-a6dd-e34e56be6c38_patch_progress_report.json',
        ]
        for p in invalid_paths:
            with self.assertRaises((ValueError, TypeError)):
                _mValidatePatchMetadataPath(p)

    @patch('exabox.infrapatching.core.clupatchmetadata.get_gcontext')
    @patch('exabox.infrapatching.core.clupatchmetadata.mGetInfraPatchingConfigParam', return_value='3')
    @patch('exabox.infrapatching.core.clupatchmetadata.exaBoxNode')
    def test_mReadPatchStatesObjectFromFile_uses_mReadFile(
            self, mock_node_cls, mock_cfg, mock_ctx):
        mock_node = MagicMock()
        mock_node_cls.return_value = mock_node
        mock_node.mReadFile.return_value = b'{"patchStates":[]}'

        ebCluPatchStateInfo.mReadPatchStatesObjectFromFile(
            _VALID_PATH,
            "somehost.example.com",
            'root',
        )

        mock_node.mReadFile.assert_called_once_with(_VALID_PATH)
        for call_args in mock_node.mExecuteCmd.call_args_list:
            cmd = call_args[0][0] if call_args[0] else ''
            self.assertNotIn(_VALID_PATH, cmd if isinstance(cmd, str) else '')

    @patch('exabox.infrapatching.core.clupatchmetadata.get_gcontext')
    @patch('exabox.infrapatching.core.clupatchmetadata.mGetInfraPatchingConfigParam', return_value='3')
    @patch('exabox.infrapatching.core.clupatchmetadata.exaBoxNode')
    def test_mWritePatchStatesToFile_root_uses_mWriteFile(
            self, mock_node_cls, mock_cfg, mock_ctx):
        mock_node = MagicMock()
        mock_node_cls.return_value = mock_node

        pss = ebCluPatchStateInfo([], _VALID_PATH, "somehost.example.com")
        pss.mWritePatchStatesToFile(aUser='root')

        mock_node.mWriteFile.assert_called_once()
        call_args = mock_node.mWriteFile.call_args
        self.assertEqual(call_args[0][0], _VALID_PATH)
        self.assertIsInstance(call_args[0][1], bytes)

    @patch('exabox.infrapatching.core.clupatchmetadata.get_gcontext')
    @patch('exabox.infrapatching.core.clupatchmetadata.mGetInfraPatchingConfigParam', return_value='3')
    @patch('exabox.infrapatching.core.clupatchmetadata.exaBoxNode')
    def test_mWritePatchStatesToFile_opc_mv_failure_cleans_up(
            self, mock_node_cls, mock_cfg, mock_ctx):
        mock_node = MagicMock()
        mock_node_cls.return_value = mock_node
        mock_node.mGetCmdExitStatus.return_value = 1

        pss = ebCluPatchStateInfo([], _VALID_PATH, "somehost.example.com")
        with self.assertRaises(Exception) as ctx:
            pss.mWritePatchStatesToFile(aUser='opc')

        exec_calls = [str(c) for c in mock_node.mExecuteCmd.call_args_list]
        rm_calls = [c for c in exec_calls if 'rm -f' in c]
        self.assertTrue(len(rm_calls) >= 1, "Expected rm -f cleanup call")
        self.assertIn('launchNode', str(ctx.exception))

if __name__ == "__main__":
    unittest.main()
