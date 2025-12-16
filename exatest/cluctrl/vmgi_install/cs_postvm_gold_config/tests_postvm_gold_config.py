#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/vmgi_install/cs_postvm_gold_config/tests_postvm_gold_config.py /main/1 2025/06/03 09:40:04 jesandov Exp $
#
# tests_postvm_gold_config.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_postvm_gold_config.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    05/29/25 - Creation
#

import unittest

import re
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.csstep.cs_base import CSBase
from exabox.log.LogMgr import ebLogError, ebLogInfo
import warnings
from exabox.ovm.clumisc import ebSubnetSet, ebMigrateUsersUtil
from exabox.ovm.csstep.cs_postvm_gold_config import csPostVmGoldConfig

class ebTestCluControlPostVmGoldConfig(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def test_000_mSaveBomFileDomU(self):

        _bom = os.path.join(self.mGetUtil().mGetResourcesPath(), "bom.json")
        _payload = ebJsonObject({"jsonconf": {"image_base_bom": _bom}})

        # Prepare Mock Commands
        _cmds = {
            self.mGetRegexDomU(): [
                [
                    exaMockCommand("mkdir -p", aRc=0),
                    exaMockCommand("scp", aRc=0),
                    exaMockCommand("chmod 444", aRc=0),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        # Patch the user
        _step =  csPostVmGoldConfig()
        _step.mSaveBomFileDomU(self.mGetClubox(), _payload)


if __name__ == '__main__':
    unittest.main(warnings='ignore')


# end of file
