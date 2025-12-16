#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/exabasedb/tests_cs_createvm.py /main/1 2025/11/25 05:03:58 prsshukl Exp $
#
# tests_cs_createvm.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_createvm.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    11/24/25 - Creation
#

import json
import unittest
from unittest import mock
import hashlib
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.log.LogMgr import ebLogInfo, ebLogTrace
from exabox.ovm.bom_manager import ImageBOM
from exabox.ovm.cluexascale import ebCluExaScale
from exabox.utils.node import connect_to_host
from exabox.core.Context import get_gcontext
from exabox.ovm.csstep.exabasedb.cs_createvm import csCreateVM
from unittest.mock import Mock, patch, MagicMock, PropertyMock, mock_open
import warnings

class ebTestCSCreateVM(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCSCreateVM, self).setUpClass(aGenerateDatabase=True, aUseOeda=True)
        self.mGetClubox(self).mSetUt(True)
        warnings.filterwarnings("ignore")

    @patch('exabox.log.LogMgr.ebLogInfo')
    def test_undoExecute(self, mock_log_info):
        # Set up mocks
        mock_ebox = Mock()
        mock_options = {}
        mock_step_list = ['ESTP_CREATE_VM']

        # Create instance
        cs_create_vm = csCreateVM()
        cs_create_vm.mDeleteVM = Mock()

        # Call undoExecute
        cs_create_vm.undoExecute(mock_ebox, mock_options, mock_step_list)

        # Assertions
        cs_create_vm.mDeleteVM.assert_called_once_with(mock_ebox, mock_options, mock_step_list)


if __name__ == '__main__':
    unittest.main()
