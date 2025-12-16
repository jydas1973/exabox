#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/network/tests_ebtables_setup.py /main/1 2023/12/08 17:38:15 jfsaldan Exp $
#
# tests_ebtables_setup.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_ebtables_setup.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    11/24/23 - Creation
#

import unittest
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

class ebTestEbtablesSetup(ebTestClucontrol):


    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)
        self.maxDiff = None

    def test_disable_ebtables(self):
        """
        This unittest validates that, if there is no white list file,
        and ebtables is disabled (now the default value), we will will
        do nothing and simply return.
        If this unittest fails saying a command is missing, we need to take a
        look at why a command is being attempted to be executed
        """
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(
                        f"test -e /opt/exacloud/network/vif-whitelist", aRc=1),
                ],
                [
                    exaMockCommand(
                        f"test -e /opt/exacloud/network/vif-whitelist", aRc=1),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        self.assertEqual(None, _ebox.mSetupEbtablesOnDom0())

if __name__ == '__main__':
    unittest.main()
