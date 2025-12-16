"""

 $Header: 

 Copyright (c) 2020, 2023, Oracle and/or its affiliates.

 NAME:
      tests_oeda_args.py - Unitest for OEDA arguments

 DESCRIPTION:
      Run tests for OEDA args

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       vgerard  08/20/20 - Creation of the file
"""

import unittest

from exabox.core.Context import get_gcontext
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

class ebTestOEDAArgs(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        # Surcharge ebTestClucontrol, to specify noDB/noOEDA
        super().setUpClass(False,False)    

    def setUp(self):
        # DefaultValue
        get_gcontext().mSetConfigOption('oeda_extra_args','-usesu -sshkeys')

    def setCluControlCmd(self, aCmd : str) -> None:
        self.mGetClubox()._exaBoxCluCtrl__cmd = aCmd 
        
   
    def test_mDefaultUntouchedValue(self): 
        self.assertEqual('-usesu -sshkeys -usersa', self.mGetClubox().mGetOEDAExtraArgs())

    def test_mTestDeleteService(self):
        self.setCluControlCmd('vmgi_delete')
        self.assertEqual('-usersa', self.mGetClubox().mGetOEDAExtraArgs())

    def test_mTestStepwiseDeleteService(self):
        self.setCluControlCmd('deleteservice')
        self.assertEqual('-usersa', self.mGetClubox().mGetOEDAExtraArgs())

    def test_mMultipleSpacesAndOtherOpts(self):
        get_gcontext().mSetConfigOption('oeda_extra_args','  -usesu  -opt2    -sshkeys  -opt3  ')
        self.setCluControlCmd('vmgi_delete')
        self.assertEqual('-opt2 -opt3 -usersa', self.mGetClubox().mGetOEDAExtraArgs())

    def test_mNoOpts(self):
        get_gcontext().mSetConfigOption('oeda_extra_args',None)
        self.assertEqual('', self.mGetClubox().mGetOEDAExtraArgs())

    def test_mNoOptsInDelete(self):
        get_gcontext().mSetConfigOption('',None)
        self.setCluControlCmd('vmgi_delete')
        self.assertEqual('-usersa', self.mGetClubox().mGetOEDAExtraArgs())


if __name__ == '__main__':
    unittest.main() 
