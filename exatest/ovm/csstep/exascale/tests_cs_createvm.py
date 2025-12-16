#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/exascale/tests_cs_createvm.py /main/1 2025/10/31 17:31:05 bhpati Exp $
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
#    bhpati      10/20/25 - Creation
#

import re
import json
import copy
import time
import unittest
import hashlib
import exabox.ovm.clubonding as clubonding
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.ovm.csstep.cs_base import CSBase
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.log.LogMgr import ebLogInfo, ebLogTrace
from exabox.ovm.csstep.exascale.exascaleutils import *
from exabox.ovm.csstep.exascale.escli_util import *
from exabox.ovm.csstep.exascale.cs_createvm import *
from exabox.core.Context import get_gcontext
from unittest.mock import Mock, patch, MagicMock, PropertyMock, mock_open
import warnings

class ebTestCreateVM(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
            super(ebTestCreateVM, self).setUpClass(aGenerateDatabase = True, aUseOeda = True)
            self.mGetClubox(self).mSetUt(True)
            warnings.filterwarnings("ignore")

    @patch('exabox.ovm.csstep.cs_util.csUtil')
    @patch('exabox.ovm.clumisc.ebCluPreChecks')
    def test_doExecute(self, mock_csUtil, mock_ebCluPreChecks):
        # Set up mocks
        mock_aCluCtrlObj = Mock()
        mock_aCluCtrlObj.mIsKVM.return_value = True
        mock_aCluCtrlObj.mReturnAllClusterHosts.return_value = (['dom0'], [], ['cell'], []) 
        mock_aOptions = {}
        mock_aStepList = ['ESTP_CREATE_VM']
        mock_csu = mock_csUtil.return_value
        mock_csu.mReturnCountofVm.return_value = 1 
        mock_pchecks = mock_ebCluPreChecks.return_value

        # Create instance and call doExecute
        cs_create_vm = csCreateVM()
        cs_create_vm.mCreateVM = Mock()
        cs_create_vm.doExecute(mock_aCluCtrlObj, mock_aOptions, mock_aStepList)


if __name__ == '__main__':
    unittest.main()