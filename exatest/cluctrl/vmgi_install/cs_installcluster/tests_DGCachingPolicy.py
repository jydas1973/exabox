#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/vmgi_install/cs_installcluster/tests_DGCachingPolicy.py /main/1 2021/05/04 12:18:08 jfsaldan Exp $
#
# tests_DGCachingPolicy.py
#
# Copyright (c) 2021, Oracle and/or its affiliates. 
#
#    NAME
#      tests_DGCachingPolicy.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    04/26/21 - Creation
#

import unittest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.core.Error import ExacloudRuntimeError

class ebTestDGCachingPolicy(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()


    def template_test_Caching_policy(self, aRc, aStdout, aIsAdb):
        """
        This is the template used to test method mSetCachingPolicy in clucontrol
        """


        # Create args structure
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand('cellcli -e \'ALTER GRIDDISK WHERE NAME LIKE "RECO.*" '
                                    'CANCEL FLUSH\'' , aRc=aRc["flush"], aStdout=aStdout["flush"]),
                    exaMockCommand('cellcli -e \'ALTER GRIDDISK CACHINGPOLICY="default" '
                                    'WHERE NAME LIKE "RECO.*"\'', aRc=aRc["policy"], aStdout=aStdout["policy"])
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _options = self.mGetPayload()
        _options.jsonconf['adb_s'] = aIsAdb
        self.mGetClubox().mSetCachingPolicyRecoGD(self.mGetClubox().mReturnCellNodes(),  _options)
        #self.mGetClubox().mSetCachingPolicyRecoGD("default", _options)

    def test_caching_policy_not_adb(self):
        """ ADB is not detected"""

        ebLogInfo("Test Description- ADB env is not detected, this should be nop")

        _rc = {
                "flush": 0,
                "policy" :0
              }

        _stdout = {
                "flush": "",
                "policy": ""
                  }

        _is_adb = "False"

        self.template_test_Caching_policy(_rc, _stdout, _is_adb)


    def test_caching_policy_adb_all_suc(self):
        """ ADB is detected"""

        ebLogInfo("Test Description- ADB env is detected, nothing fails")

        _rc = {
                "flush": 0,
                "policy" :0
              }

        _stdout = {
                "flush": "",
                "policy": ""
                  }

        _is_adb = "True"

        self.template_test_Caching_policy(_rc, _stdout, _is_adb)


    def test_caching_policy_adb_flush_fails(self):
        """ ADB is detected"""

        ebLogInfo("Test Description- ADB env is detected, flush fails\n")

        _rc = {
                "flush": 1,
                "policy" :0
              }

        _stdout = {
                "flush": "Cellcli failed",
                "policy": ""
                  }

        _is_adb = "True"

        self.assertRaises(ExacloudRuntimeError, lambda : self.template_test_Caching_policy(_rc, _stdout, _is_adb))


    def test_caching_policy_adb_policy_fails(self):
        """ ADB is detected"""

        ebLogInfo("Test Description- ADB env is detected, flush fails\n")

        _rc = {
                "flush": 0,
                "policy" :1
              }

        _stdout = {
                "flush": "Cellcli failed",
                "policy": ""
                  }

        _is_adb = "True"

        self.assertRaises(ExacloudRuntimeError, lambda : self.template_test_Caching_policy(_rc, _stdout, _is_adb))
if __name__ == '__main__':
    unittest.main()
