#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/exascale/tests_xml_patching.py /main/3 2023/12/07 19:11:00 jesandov Exp $
#
# tests_vm_move.py
#
# Copyright (c) 2022, 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_vm_move.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    05/17/23 - 35395484: Add extra validation for EDV
#    jesandov    12/06/22 - Creation
#

import os
import unittest
import shutil
from unittest.mock import patch
 
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import MockCommand, exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.cluexascale import ebCluExaScale

def myRun(FromXml, ToXml):
    shutil.copyfile(FromXml, ToXml)

class ebExaScaleXml(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)
        self.mGetClubox(self).mSetExaScale(True)
        self.mGetClubox(self).mSetDebug(True)
        self.mGetClubox(self).mGetCtx().mSetConfigOption('exascale_edv_enable', "True")

    @patch("exabox.tools.ebOedacli.ebOedacli.ebOedacli.mRun", wraps=myRun)
    def test_001_xml_patching(self, mock_mRun):

        #Mock commands
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    MockCommand(".*mkdir.*exascale.*", ebTestClucontrol.mRealExecute, aPersist=True),
                    MockCommand(".*rm.*exascale.*", ebTestClucontrol.mRealExecute, aPersist=True),
                ]
            ],
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _exacloudPath = os.path.abspath(__file__)
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]

        _xmlToUse = os.path.join(self.mGetUtil().mGetOutputDir(), "sample.xml")
        _xmlOriginal = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/sample.xml")

        shutil.copyfile(_xmlOriginal, _xmlToUse)
        self.mGetClubox().mSetPatchConfig(_xmlToUse)

        #Execute the clucontrol function
        _exascale = ebCluExaScale(self.mGetClubox())
        _exascale.mApplyExaScaleXmlPatching()


    def test_002_dummy_cell_keys(self):

        #Mock commands
        _cmds = {
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _exacloudPath = os.path.abspath(__file__)
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]

        _xmlToUse = os.path.join(self.mGetUtil().mGetOutputDir(), "sample.xml")
        _xmlOriginal = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/sample.xml")

        shutil.copyfile(_xmlOriginal, _xmlToUse)
        self.mGetClubox().mSetPatchConfig(_xmlToUse)

        #Execute the clucontrol function
        _exascale = ebCluExaScale(self.mGetClubox())
        _exascale.mCreateDummyCellsKeys()


if __name__ == '__main__':
    unittest.main(warnings='ignore')


# end of file
