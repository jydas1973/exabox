#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/shared_methods/tests_grid_symlink.py /main/1 2025/03/21 17:00:37 jfsaldan Exp $
#
# tests_grid_symlink.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_grid_symlink.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    03/10/25 - Creation
#

import unittest
from unittest.mock import Mock, patch
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

class ebTestGridImagesSetup(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)
        self.maxDiff = None

    def test_mGenerateSymLinks_exascale(self):
        """
        """
        _ebox = self.mGetClubox()
        _ebox.mSetNoOeda(False)
        _ebox.mSetExaScale(True)
        self.assertEqual(2, _ebox.mGenerateSymLinks())

    def test_mGenerateSymLinks_no_oeda(self):
        """
        """
        _ebox = self.mGetClubox()
        _ebox.mSetNoOeda(True)
        self.assertEqual(1, _ebox.mGenerateSymLinks())

if __name__ == '__main__':
    unittest.main()

