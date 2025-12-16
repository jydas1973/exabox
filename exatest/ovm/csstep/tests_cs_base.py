#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/tests_cs_base.py /main/1 2025/08/25 06:17:10 pbellary Exp $
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
#    pbellary    08/20/25 - Creation
#
import unittest
from unittest.mock import MagicMock, patch
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_createvm import csCreateVM

class TestCSBase(unittest.TestCase):

    def setUp(self):
        self.cs_base = csCreateVM()
        self.ebox_mock = MagicMock()
        self.options_mock = MagicMock()
        self.step_list_mock = MagicMock()

    def test_remove_guest_edv_volumes(self):
        self.ebox_mock.isBaseDB.return_value = False
        self.ebox_mock.mIsExaScale.return_value = False
        self.ebox_mock.mIsOciEXACC.return_value = False

        utils_mock = MagicMock()
        with patch.object(self.ebox_mock, 'mGetExascaleUtils') as mock_get_exascale_utils:
            mock_get_exascale_utils.return_value = utils_mock
            self.cs_base.mDeleteVM(self.ebox_mock, self.options_mock, self.step_list_mock)
            utils_mock.mRemoveGuestEDVVolumes.assert_called_once_with(self.options_mock)

if __name__ == '__main__':
    unittest.main()