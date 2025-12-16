#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/shared_methods/tests_vm_image_shredding.py /main/1 2022/03/09 07:34:02 jfsaldan Exp $
#
# tests_vm_image_shredding.py
#
# Copyright (c) 2022, Oracle and/or its affiliates. 
#
#    NAME
#      tests_vm_image_shredding.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    03/02/22 - Creation
#

import unittest
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

class ebTestVMImageShredding(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.maxDiff = None

    def test_vm_image_shredding_ok(self):
        """
        Function to test clucontrol mVMImagesShredding method
        """

        # Prepare Commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand('echo "Start time: scaqab10adm01.us.oracle.com->scaqab10client01vm08.us.oracle.com is `date`"'),
                    exaMockCommand('echo "Start time: scaqab10adm02.us.oracle.com->scaqab10client02vm08.us.oracle.com is `date`"'),
                    exaMockCommand('echo "Cumulative image size on.*'),
                    exaMockCommand('shred --verbose -n3 /EXAVMIMAGES/GuestImages/scaqab10client02vm08.us.oracle.com/\*.img'),
                    exaMockCommand('shred --verbose -n3 /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/\*.img'),
                    exaMockCommand('echo "End time: scaqab10adm01.us.oracle.com->scaqab10client01vm08.us.oracle.com is `date`"'),
                    exaMockCommand('echo "End time: scaqab10adm02.us.oracle.com->scaqab10client02vm08.us.oracle.com is `date`"'),

                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variable to use
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()

        # Prepare the enviroment variables
        self.mGetContext().mSetConfigOption("shredding_enabled", "True")

        # Run test
        self.assertEqual(None, _ebox.mVMImagesShredding(_options))

    def test_vm_image_shredding_config_not_present_skip_shredding(self):
        """
        Function to test clucontrol mVMImagesShredding method
        """

        # Declare variable to use
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()

        # Prepare the enviroment variables
        self.mGetContext().mSetConfigOption("shredding_enabled", None)

        # Run test
        self.assertEqual(None, _ebox.mVMImagesShredding(_options))

    def test_vm_image_shredding_disabled_config(self):
        """
        Function to test clucontrol mVMImagesShredding method
        """

        # Declare variable to use
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()

        # Prepare the enviroment variables
        self.mGetContext().mSetConfigOption("shredding_enabled", "False")

        # Run test
        self.assertEqual(None, _ebox.mVMImagesShredding(_options))

if __name__ == '__main__':
    unittest.main()

