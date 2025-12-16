#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/tests_cs_driver.py /main/3 2025/10/27 04:36:02 pbellary Exp $
#
# tests_cs_driver.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_driver.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    rajsag      07/21/25 - Creation
#
import unittest
from unittest.mock import MagicMock
from exabox.ovm.csstep.cs_driver import csDriver, csOedaTable, csEDVOedaTable, xsOedaTable, xsEighthOedaTable, csBaseDBOedaTable, csX11ZOedaTable, csEighthOedaTable

class TestCsDriver(unittest.TestCase):

    def setUp(self):
        self.eboxobj = MagicMock()
        self.options = MagicMock()
        self.utils_mock = MagicMock()
        self.cs_driver = csDriver(self.eboxobj, self.options)

    def test_mGetOedaTable_xs_eighth(self):
        self.eboxobj.mIsXS.return_value = True
        self.eboxobj.mGetExascaleUtils.return_value = self.utils_mock
        self.utils_mock.mGetRackSize.return_value = 'eighthrack'
        self.assertEqual(self.cs_driver.mGetOedaTable(), xsEighthOedaTable)

    def test_mGetOedaTable_xs_not_eighth(self):
        self.eboxobj.mIsXS.return_value = True
        self.eboxobj.mGetRackSize.return_value = 'full'
        self.assertEqual(self.cs_driver.mGetOedaTable(), xsOedaTable)

    def test_mGetOedaTable_asm_zrack(self):
        self.eboxobj.mIsXS.return_value = False
        self.eboxobj.isBaseDB.return_value = False
        self.eboxobj.isExacomputeVM.return_value = False
        self.utils_mock.mIsEDVImageSupported.return_value = False
        self.eboxobj.mGetExascaleUtils.return_value = self.utils_mock
        self.utils_mock.mGetRackSize.return_value = 'zrack'
        self.assertEqual(self.cs_driver.mGetOedaTable(), csX11ZOedaTable)

    def test_mGetOedaTable_asm_eighth(self):
        self.eboxobj.mIsXS.return_value = False
        self.eboxobj.isBaseDB.return_value = False
        self.eboxobj.isExacomputeVM.return_value = False
        self.utils_mock.mIsEDVImageSupported.return_value = False
        self.eboxobj.mGetExascaleUtils.return_value = self.utils_mock
        self.utils_mock.mGetRackSize.return_value = 'eighthrack'
        self.assertEqual(self.cs_driver.mGetOedaTable(), csEighthOedaTable)

    def test_mGetOedaTable_base_db(self):
        self.eboxobj.mIsXS.return_value = False
        self.eboxobj.isBaseDB.return_value = True
        self.eboxobj.isExacomputeVM.return_value = False
        self.assertEqual(self.cs_driver.mGetOedaTable(), csBaseDBOedaTable)

    def test_mGetOedaTable_exa_compute_vm(self):
        self.eboxobj.mIsXS.return_value = False
        self.eboxobj.isBaseDB.return_value = False
        self.eboxobj.isExacomputeVM.return_value = True
        self.assertEqual(self.cs_driver.mGetOedaTable(), csBaseDBOedaTable)

    def test_mGetOedaTable_default(self):
        self.eboxobj.mIsXS.return_value = False
        self.eboxobj.isBaseDB.return_value = False
        self.eboxobj.isExacomputeVM.return_value = False
        self.eboxobj.mGetExascaleUtils.return_value = self.utils_mock
        self.utils_mock.mIsEDVImageSupported.return_value = False
        self.assertEqual(self.cs_driver.mGetOedaTable(), csOedaTable)

    def test_mGetOedaTable_edv_asm(self):
        self.eboxobj.mIsXS.return_value = False
        self.eboxobj.isBaseDB.return_value = False
        self.eboxobj.isExacomputeVM.return_value = False
        self.eboxobj.mGetExascaleUtils.return_value = self.utils_mock
        self.utils_mock.mIsEDVImageSupported.return_value = True
        result = self.cs_driver.mGetOedaTable()
        self.assertEqual(result, csEDVOedaTable)

if __name__ == '__main__':
    unittest.main()