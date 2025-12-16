#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/infrapatching/core/tests_clupatchmetadata.py /main/1 2024/10/21 20:15:23 avimonda Exp $
#
# tests_clupatchmetadata.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
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
#    avimonda    10/15/24 - Bug 37156068 - EXCEPTION IN
#                           MREADPATCHSTATESOBJECTFROMFILE() IS MISLEADING
#    avimonda    10/15/24 - Create file
#    avimonda    10/15/24 - Creation
#

import unittest
from unittest.mock import patch
import socket
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.infrapatching.core.clupatchmetadata import ebCluPatchStateInfo
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand

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

if __name__ == "__main__":
    unittest.main()
