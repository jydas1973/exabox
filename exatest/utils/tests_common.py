#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/utils/tests_common.py /main/2 2024/08/12 15:59:21 naps Exp $
#
# tests_common.py
#
# Copyright (c) 2023, 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_common.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    naps        08/12/24 - Bug 36908342 - X11 support.
#    ndesanto    01/24/23 - Tests for funcions in exabox/utils/common.py file
#    ndesanto    01/24/23 - Creation
#

import unittest

from exabox.utils.common import mGetModelNumber, mIsStrModel, mCompareModel


class UtilsNodeTest(unittest.TestCase):
    """exabox.utils.node unit tests"""

    def test_mGetModelNumber_not_a_number(self):
        self.assertRaises(ValueError, mGetModelNumber, "not a number")

    def test_mGetModelNumber_empty(self):
        self.assertRaises(ValueError, mGetModelNumber, "")

    def test_mGetModelNumber_None(self):
        self.assertRaises(TypeError, mGetModelNumber, None)

    def test_mGetModelNumber_X8(self):
        self.assertEqual(8, mGetModelNumber("X8"))

    def test_mGetModelNumber_X10(self):
        self.assertEqual(10, mGetModelNumber("X10"))

    def test_mGetModelNumber_X11(self):
        self.assertEqual(11, mGetModelNumber("X11"))

    def test_mGetModelNumber_X100(self):
        self.assertEqual(100, mGetModelNumber("X100"))

    def test_mIsStrModel_None(self):
        self.assertFalse(mIsStrModel(None))

    def test_mIsStrModel_empty(self):
        self.assertFalse(mIsStrModel(""))

    def test_mIsStrModel_Not_a_model_number(self):
        self.assertFalse(mIsStrModel("Not a model number"))

    def test_mIsStrModel_X8(self):
        self.assertTrue(mIsStrModel("X8"))

    def test_mIsStrModel_X10(self):
        self.assertTrue(mIsStrModel("X10"))

    def test_mIsStrModel_X11(self):
        self.assertTrue(mIsStrModel("X11"))

    def test_mIsStrModel_X100(self):
        self.assertTrue(mIsStrModel("X100"))

    def test_mCompareModel_not_a_number_first_arg(self):
        self.assertRaises(ValueError, mCompareModel, "not a number", "X10")

    def test_mCompareModel_not_a_number_second_arg(self):
        self.assertRaises(ValueError, mCompareModel, "X10", "not a number")

    def test_mCompareModel_not_a_number_first_arg_X11(self):
        self.assertRaises(ValueError, mCompareModel, "not a number", "X11")

    def test_mCompareModel_not_a_number_second_arg_X11(self):
        self.assertRaises(ValueError, mCompareModel, "X11", "not a number")

    def test_mCompareModel_False_X8_more_than_X10(self):
        self.assertFalse(mCompareModel("X8", "X10") > -1)

    def test_mCompareModel_False_X10_less_than_X8(self):
        self.assertFalse(mCompareModel("X10", "X8") < 1)

    def test_mCompareModel_False_X10_more_than_X11(self):
        self.assertFalse(mCompareModel("X10", "X11") > -1)

    def test_mCompareModel_False_X11_less_than_X10(self):
        self.assertFalse(mCompareModel("X11", "X10") < 1)

    def test_mCompareModel_False_X8_equals_X10(self):
        self.assertFalse(mCompareModel("X8", "X10") == 0)

    def test_mCompareModel_False_X10_not_equals_X10(self):
        self.assertFalse(mCompareModel("X10", "X10") != 0)

    def test_mCompareModel_True_X10_more_than_X8(self):
        self.assertTrue(mCompareModel("X10", "X8") > 0)

    def test_mCompareModel_True_X8_equals_X8(self):
        self.assertTrue(mCompareModel("X8", "X8") == 0)

    def test_mCompareModel_True_X10_equals_X10(self):
        self.assertTrue(mCompareModel("X10", "X10") == 0)

    def test_mCompareModel_True_X8_less_than_X10(self):
        self.assertTrue(mCompareModel("X8", "X10") < 0)

    def test_mCompareModel_True_X8_less_than_or_equal_X10(self):
        self.assertTrue(mCompareModel("X8", "X10") <= 0)

    def test_mCompareModel_True_X10_less_than_or_equal_X10(self):
        self.assertTrue(mCompareModel("X10", "X10") <= 0)

    def test_mCompareModel_True_X10_more_than_or_equal_X8(self):
        self.assertTrue(mCompareModel("X10", "X8") >= 0)

    def test_mCompareModel_True_X10_more_than_or_equal_X10(self):
        self.assertTrue(mCompareModel("X10", "X10") >= 0)


    def test_mCompareModel_False_X10_equals_X11(self):
        self.assertFalse(mCompareModel("X10", "X11") == 0)

    def test_mCompareModel_False_X11_not_equals_X11(self):
        self.assertFalse(mCompareModel("X11", "X11") != 0)

    def test_mCompareModel_True_X11_more_than_X10(self):
        self.assertTrue(mCompareModel("X11", "X10") > 0)

    def test_mCompareModel_True_X11_equals_X11(self):
        self.assertTrue(mCompareModel("X11", "X11") == 0)

    def test_mCompareModel_True_X10_less_than_X11(self):
        self.assertTrue(mCompareModel("X10", "X11") < 0)

    def test_mCompareModel_True_X10_less_than_or_equal_X11(self):
        self.assertTrue(mCompareModel("X10", "X11") <= 0)

    def test_mCompareModel_True_X11_less_than_or_equal_X11(self):
        self.assertTrue(mCompareModel("X11", "X11") <= 0)

    def test_mCompareModel_True_X11_more_than_or_equal_X10(self):
        self.assertTrue(mCompareModel("X11", "X10") >= 0)

    def test_mCompareModel_True_X11_more_than_or_equal_X11(self):
        self.assertTrue(mCompareModel("X11", "X11") >= 0)

if __name__ == '__main__':
    unittest.main()
