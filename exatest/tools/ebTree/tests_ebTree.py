"""

 $Header: 

 Copyright (c) 2018, 2021, Oracle and/or its affiliates. 

 NAME:
      tests_ebTree.py - Unitest for ebTreeClass

 DESCRIPTION:
      Run tests for ebTree class

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
        ndesanto    08/19/20 - Chaged to test suite and added maxDiff
        jesandov    07/27/18 - Creation of the file for xmlpatching
"""

import unittest
from exabox.tools.ebTree.ebTree import ebTree
import os
import sys

class ebTestTree(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self._path = 'exabox/exatest/tools/ebTree/resources/'
        self.maxDiff = None

    def test_structure(self):

        _baseXml = ebTree(self._path + "exacloud.xml")
        _structXml = _baseXml.mGetStructure()
        _compareXml = ebTree(self._path + "exacloudStructure.xml")

        self.assertEqual(_structXml.mToStringDFS(), _compareXml.mToStringDFS())

        _baseXml = ebTree(self._path + "oeda.xml")
        _structXml = _baseXml.mGetStructure()
        _compareXml = ebTree(self._path + "oedaStructure.xml")

        self.assertEqual(_structXml.mToStringDFS(), _compareXml.mToStringDFS())

    def test_tricolor_sample(self):
        
        _redXml = ebTree(self._path + "red.xml")
        _greenXml = ebTree(self._path + "green.xml")

        _tri    = _redXml.mTricolorTree(_greenXml)
        _triRes = ebTree(self._path + "tricolor.xml")

        self.assertEqual(_tri.mToStringDFS(), _triRes.mToStringDFS())
        self.assertEqual(_tri.mToStringBFS(), _triRes.mToStringBFS())

    def test_tricolor_middle(self):
        
        _redXml = ebTree(self._path + "exacloud.xml")
        _greenXml = ebTree(self._path + "patch.xml")

        _tri    = _redXml.mTricolorTree(_greenXml)
        _triRes = ebTree(self._path + "tricolorExacloud.xml")

        self.assertEqual(_tri.mToStringDFS(), _triRes.mToStringDFS())
        self.assertEqual(_tri.mToStringBFS(), _triRes.mToStringBFS())

    def test_tricolor_full(self):

        _redXml = ebTree(self._path + "fullrack.xml")

        _greenXml = _redXml.mCopy()
        _tri = _redXml.mTricolorTree(_greenXml)

        self.assertEqual(_tri.mGetNodesByType("Red"), [])
        self.assertEqual(_tri.mGetNodesByType("Green"), [])


def suite():
    """
    This method ensures the execution in the intended order of the tests.
    """
    suite = unittest.TestSuite()
    suite.addTest(ebTestTree('test_structure'))
    suite.addTest(ebTestTree('test_tricolor_sample'))
    suite.addTest(ebTestTree('test_tricolor_middle'))
    #suite.addTest(ebTestTree('test_tricolor_full'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suite())
