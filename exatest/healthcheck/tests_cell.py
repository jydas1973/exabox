#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/healthcheck/tests_cell.py /main/1 2021/07/28 03:20:36 aypaul Exp $
#
# tests_cell.py
#
# Copyright (c) 2021, Oracle and/or its affiliates. 
#
#    NAME
#      tests_cell.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      07/11/21 - Creation
#
import json
import unittest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.healthcheck.cluhealthcheck import ebCluHealth
from exabox.healthcheck.healthcheck import HealthCheck
from exabox.ovm.cluhealth import ebCluHealthCheck
import warnings

HEALTHCHECK_FAIL = 1
HEALTHCHECK_SUCC = 0

FLASHCACHE_NORMAL = """         name:                   scaqab10celadm01_FLASHCACHE
         cellDisk:               FD_03_scaqab10celadm01,FD_00_scaqab10celadm01,FD_02_scaqab10celadm01,FD_01_scaqab10celadm01
         creationTime:           2021-07-06T04:50:51-07:00
         degradedCelldisks:      
         effectiveCacheSize:     5.82122802734375T
         id:                     dc842733-3727-45e0-8bfd-0a99601f8f7f
         size:                   5.82122802734375T
         status:                 normal"""
FLASHCACHE_DEGRADED = """         name:                   scaqab10celadm02_FLASHCACHE
         cellDisk:               FD_03_scaqab10celadm02,FD_00_scaqab10celadm02,FD_02_scaqab10celadm02,FD_01_scaqab10celadm02
         creationTime:           2021-07-06T04:50:51-07:00
         degradedCelldisks:      
         effectiveCacheSize:     5.82122802734375T
         id:                     dc842733-3727-45e0-8bfd-0a99601f8f7f
         size:                   5.82122802734375T
         status:                 warning - degraded"""
CELLDB_LIST_NORMAL = """         ASM"""
CELLDB_LIST_DBPRESENT = """         ASM
         UWHDYFN"""
CELLDB_LIST_ERROR = """CELL-02559: There is a communication error between MS and CELLSRV."""

class testOptions(object): pass

class ebTestCellHealthCheck(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCellHealthCheck, self).setUpClass(False, False)
        warnings.filterwarnings("ignore")

    def test_mCheckFlashCache(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckFlashCache")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        fullOptions.healthcheck = "custom"
        fullOptions.jsonconf = {"targetHosts": "cells"}
        cluHealthCheck = ebCluHealthCheck(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), cluHealthCheck)

        resultsExpected = {
            "scaqab10celadm01.us.oracle.com": [HEALTHCHECK_SUCC, "normal"],
            "scaqab10celadm02.us.oracle.com": [HEALTHCHECK_FAIL, "warning - degraded"],
            "scaqab10celadm03.us.oracle.com": [HEALTHCHECK_FAIL, None]
            }

        for cell in self.mGetClubox().mReturnCellNodes():
            flashCacheOutput = FLASHCACHE_NORMAL
            if cell == "scaqab10celadm02.us.oracle.com":
                flashCacheOutput = FLASHCACHE_DEGRADED
            elif cell == "scaqab10celadm03.us.oracle.com":
                flashCacheOutput = ""
            _cmds = {
            self.mGetRegexCell(): [
                        [
                            exaMockCommand("cellcli -e list flashcache detail", aRc=0, aStdout= flashCacheOutput, aPersist=True)
                        ]
                    ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("ping -c 1 -W 4 scaqab10celadm01.us.oracle.com ", aRc=0, aPersist=True),
                    exaMockCommand("ping -c 1 -W 4 scaqab10celadm02.us.oracle.com ", aRc=0, aPersist=True),
                    exaMockCommand("ping -c 1 -W 4 scaqab10celadm03.us.oracle.com ", aRc=0, aPersist=True)
                ]
            ]
                }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckFlashCache(cell)
            cellStatus = returnedResult.get("hcMsgDetail").get("status:", None)
            self.assertEqual(resultsExpected[cell][0], returnedResult["hcTestResult"])
            self.assertEqual(resultsExpected[cell][1], cellStatus)

    def test_mCheckDBStatusOnCell(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on HealthCheck.mCheckDBStatusOnCell")
        fullOptions = testOptions()
        fullOptions.configpath = ""
        fullOptions.healthcheck = "custom"
        fullOptions.jsonconf = {"targetHosts": "cells"}
        cluHealthCheck = ebCluHealthCheck(self.mGetClubox(), fullOptions)
        currentHealthObject = HealthCheck(self.mGetClubox(), cluHealthCheck)

        resultsExpected = {
            "scaqab10celadm01.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10celadm02.us.oracle.com": HEALTHCHECK_SUCC,
            "scaqab10celadm03.us.oracle.com": HEALTHCHECK_FAIL
            }

        for cell in self.mGetClubox().mReturnCellNodes():
            cellDBList = CELLDB_LIST_NORMAL
            if cell == "scaqab10celadm02.us.oracle.com":
                cellDBList = CELLDB_LIST_DBPRESENT
            elif cell == "scaqab10celadm03.us.oracle.com":
                cellDBList = CELLDB_LIST_ERROR
            _cmds = {
            self.mGetRegexCell(): [
                        [
                            exaMockCommand("cellcli -e LIST DATABASE", aRc=0, aStdout= cellDBList, aPersist=True)
                        ]
                    ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("ping -c 1 -W 4 scaqab10celadm01.us.oracle.com ", aRc=0, aPersist=True),
                    exaMockCommand("ping -c 1 -W 4 scaqab10celadm02.us.oracle.com ", aRc=0, aPersist=True),
                    exaMockCommand("ping -c 1 -W 4 scaqab10celadm03.us.oracle.com ", aRc=0, aPersist=True)
                ]
            ]
                }
            self.mPrepareMockCommands(_cmds)

            returnedResult = currentHealthObject.mCheckDBStatusOnCell(cell)
            self.assertEqual(resultsExpected[cell], returnedResult["hcTestResult"])

if __name__ == "__main__":
    unittest.main()