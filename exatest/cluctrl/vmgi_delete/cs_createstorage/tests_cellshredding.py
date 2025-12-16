#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/vmgi_delete/cs_createstorage/tests_cellshredding.py /main/2 2024/12/06 04:46:57 aararora Exp $
#
# tests_cellshredding.py
#
# Copyright (c) 2021, 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_cellshredding.py - cell erase and shredding test cases.
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    11/27/24 - Bug 37067118: Use cellcli drop command for
#                           performing secure erase.
#    aypaul      10/29/21 - Creation
#
import json
import unittest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
import warnings

class ebTestCellHealthCheck(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCellHealthCheck, self).setUpClass(True, True)
        warnings.filterwarnings("ignore")

    def test_mIsCryptoEraseSupported(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mIsCryptoEraseSupported.")
        resultsExpected = {
            "scaqab10celadm01.us.oracle.com": True,
            "scaqab10celadm02.us.oracle.com": False,
            "scaqab10celadm03.us.oracle.com": True
        }

        for cell in self.mGetClubox().mReturnCellNodes():
            _cmds = {
            self.mGetRegexCell(): 
                [
                    [
                        exaMockCommand("secureeraser", aRc=1 if cell == "scaqab10celadm02.us.oracle.com" else 0, aPersist=True),
                        exaMockCommand("test", aRc=0, aStdout="/bin/python", aPersist=True)
                    ],
                    [
                        exaMockCommand("/usr/local/bin/imageinfo -version", aStdout="24.1.0", aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)
            result = self.mGetClubox().mIsCryptoEraseSupported()
            self.assertEqual(resultsExpected[cell], result)


if __name__ == "__main__":
    unittest.main()