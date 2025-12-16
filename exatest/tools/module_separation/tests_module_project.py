"""

 $Header: 

 Copyright (c) 2018, 2021, Oracle and/or its affiliates. 

 NAME:
      module_project.py - Unitest for Module Project

 DESCRIPTION:
      Run tests for the method of module_project

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)

        jesandov    07/27/18 - Creation of the file for xmlpatching
"""

import unittest
import os

from random import shuffle

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.modules.module_manager import ModuleManager

class ebTestModuleManager(ebTestClucontrol):

    def test_001_exist_modules(self):

        #Prepare Module Manager
        _module_path = "exabox/exatest/tools/module_separation/modules/"
        module_manager = ModuleManager(self.mGetClubox(), _module_path)

        #Validate the modules
        module_manager.mBuildCache()
        modules = ['dummy_dbaastools_exa_atp.tar', \
                   'dummy_dbaastools_exa_rpm.tar', \
                   'dummy_kv-ee.tar']

        self.assertEqual(modules, list(sorted(module_manager.mGetCache().keys())))

    def test_002_build_graph(self):

        #Prepare Module Manager
        _module_path = "exabox/exatest/tools/module_separation/modules/"
        module_manager = ModuleManager(self.mGetClubox(), _module_path)

        #Validate the modules
        module_manager.mBuildCache()
        module_manager.mBuildDependencyGraph()

        install = module_manager.mGetInstallationOrder()
        install = list(map(lambda x: x.mGetElement().name, install))

        order = ['nosql', 'perl-JSON', 'dbaastools_exa', 'dbaastools_exa_atp']

        self.assertEqual(order, install)



if __name__ == '__main__':
    unittest.main(warnings='ignore')
