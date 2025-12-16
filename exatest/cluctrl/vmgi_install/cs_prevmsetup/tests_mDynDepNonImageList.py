#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/vmgi_install/cs_prevmsetup/tests_mDynDepNonImageList.py /main/1 2024/05/13 16:49:47 remamid Exp $
#
# tests_mDynDepNonImageList.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_mDynDepNonImageList.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    remamid     04/01/24 - new file
#    remamid     04/01/24 - Creation
#
import unittest
from unittest.mock import patch

import os
from random import shuffle

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.globalcache.GlobalCacheWorker import GlobalCacheWorker
from exabox.globalcache.GlobalCacheFactory import GlobalCacheFactory
from exabox.core.Error import ExacloudRuntimeError

class ebTestDynDepNonImages(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def test_mDynDepNonImages_mGetMajorityHostVersion_ol7(self):
            
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aStdout = "ORACLE SERVER X8-2", aRc = 0)
                ],
                [
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aStdout = "ORACLE SERVER X8-2", aRc = 0)
                ]
           ]
        }
        _extraRpm1 = []
        
        _ebox = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetMajorityHostVersion', return_value='ol7'):
    
            # Execute mDynDepNonImageList
            self.__dyndepfiles = _ebox.mReadDynDepConfig()
            _rc = _ebox.mDynDepNonImageList(['rpm'])
            self.assertNotEqual(_rc, _extraRpm1)

    def test_mDynDepNonImages_mGetMajorityHostVersion(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aStdout = "ORACLE SERVER X8-2", aRc = 0)
                ]
           ]
        }

        self.mPrepareMockCommands(_cmds)
        _extraRpm = {
                "dom0": "<GlobalCache>/libxenstore-4.7.0-4.el7.x86_64.rpm",
                "local": "images/libxenstore-4.7.0-4.el7.x86_64.rpm"
            }

        _ebox = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetMajorityHostVersion', return_value='ol8'):

        # Execute mDynDepNonImageList
            self.__dyndepfiles = _ebox.mReadDynDepConfig()
            _rc = _ebox.mDynDepNonImageList(['rpm'])
            print(_rc)
            self.assertNotEqual(_rc, 0)

if __name__ == '__main__':
    unittest.main(warnings='ignore')

