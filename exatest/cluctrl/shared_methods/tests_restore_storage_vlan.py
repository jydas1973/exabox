#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/shared_methods/tests_restore_storage_vlan.py /main/1 2023/03/29 19:17:14 jfsaldan Exp $
#
# tests_restore_storage_vlan.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_restore_storage_vlan.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    03/14/23 - Creation
#

import unittest
from unittest.mock import Mock, patch
from unittest.mock import MagicMock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Error import ExacloudRuntimeError

class ebTestRestoreVlanId(ebTestClucontrol):


    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)
        self.maxDiff = None

    @patch("exabox.ovm.clucontrol.ebOedacli.mRun")
    def test_restore_vlan_all_good_regular_xml(self, aMagicOedacliRun):

        # Declare variables
        _options = self.mGetPayload()
        _ebox = self.mGetClubox()

        aMagicOedacliRun.return_value = "Deploy successful, mock"

        _cell_list = [ _cell for _cell in _ebox.mReturnCellNodes().keys() ]
        _result = _ebox.mRestoreStorageVlan(_cell_list)
        self.assertEqual(None, _result)

    @patch("exabox.ovm.clucontrol.ebOedacli.mRun")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsExabm")
    def test_restore_vlan_clucontrol_handler(self, aMagicExaBM,
            aMagicKvm, aMagicOedacliRun):

        # Declare variables
        _options = self.mGetPayload()
        _ebox = self.mGetClubox()

        aMagicOedacliRun.return_value = "Deploy successful, mock"
        aMagicKvm.return_value = True
        aMagicOedacliRun.return_value = True

        _cell_list = [ _cell for _cell in _ebox.mReturnCellNodes().keys() ]
        _options.jsonconf["cells"] = list(_cell_list)
        _ebox.mSetOptions(_options)
        _result = _ebox.mHandlerResetVlan()
        self.assertEqual(None, _result)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRestoreStorageVlan")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsExabm")
    def test_restore_vlan_clucontrol_handler_calls_restore_logic(self, aMagicExaBM,
            aMagicKvm, aMagicRestoreVlan):

        # Declare variables
        _options = self.mGetPayload()
        _ebox = self.mGetClubox()

        aMagicRestoreVlan.return_value = "Deploy successful, mock"
        aMagicKvm.return_value = True
        aMagicExaBM.return_value = True

        _cell_list = [ _cell for _cell in _ebox.mReturnCellNodes().keys() ]
        _options.jsonconf["cells"] = list(_cell_list)
        _ebox.mSetOptions(_options)
        _result = _ebox.mHandlerResetVlan()
        self.assertEqual(None, _result)

        # Assert that the restore vlan logic is called
        aMagicRestoreVlan.assert_called_once()

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRestoreStorageVlan")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsExabm")
    def test_restore_vlan_clucontrol_handler_skip_because_xen(self, aMagicExaBM,
            aMagicKvm, aMagicRestoreVlan):

        # Declare variables
        _options = self.mGetPayload()
        _ebox = self.mGetClubox()

        aMagicKvm.return_value = False
        aMagicExaBM.return_value = True

        _cell_list = [ _cell for _cell in _ebox.mReturnCellNodes().keys() ]
        _options.jsonconf["cells"] = list(_cell_list)
        _ebox.mSetOptions(_options)
        _result = _ebox.mHandlerResetVlan()
        self.assertEqual(None, _result)

        # Assert that the restore vlan logic is called
        aMagicRestoreVlan.assert_not_called()

if __name__ == '__main__':
    unittest.main()
