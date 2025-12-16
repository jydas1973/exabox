#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/exascale/tests_cs_installcluster.py /main/2 2025/08/25 06:17:10 pbellary Exp $
#
# tests_cs_exascale_complete.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_installcluster.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    pbellary    06/06/25 - Enh 38035467 - EXACLOUD TO PROVIDE ACFS FILE SYSTEM SIZES IN SYNCH CALL 
#    pbellary    06/06/25 - Creation
#
import re
import json
import copy
import time
import hashlib
import unittest
import warnings
from unittest import mock
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebExacloudUtil import *
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.csstep.exascale.cs_installcluster import csInstallCluster

class ebTestExascaleInstallCluster(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestExascaleInstallCluster, self).setUpClass(aGenerateDatabase = True, aUseOeda = True)
        self.mGetClubox(self).mSetUt(True)
        warnings.filterwarnings("ignore")

    @patch('exabox.ovm.csstep.cs_util.csUtil.mExecuteOEDAStep')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mReleaseRemoteLock')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mConfigureShmAll')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mAcquireRemoteLock')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPatchVMCfg')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mConfigureSyslogIlomHost')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateDepFiles')
    def test_doExecute(self, mock_mUpdateDepFiles, mock_mConfigureSyslogIlomHost, mock_mPatchVMCfg,
                       mock_mAcquireRemoteLock, mock_mConfigureShmAll, mock_mExecuteOEDAStep,
                       mock_mReleaseRemoteLock):
        _ebox = self.mGetClubox()
        _ebox.mSetEnableKVM(True)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _step_list = ["ESTP_INSTALL_CLUSTER"]

        _handler = csInstallCluster()
        _handler.doExecute(_ebox, _options, _step_list)

    @patch('exabox.ovm.csstep.cs_util.csUtil.mExecuteOEDAStep')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mDetachU02')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mIsEDVImageSupported', return_value=True)
    def test_undoExecute(self, mock_mIsEDVSupported, mock_mDetachU02, mock_mExecuteOEDAStep):
        _ebox = self.mGetClubox()
        _ebox.mSetEnableKVM(True)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _step_list = ["ESTP_INSTALL_CLUSTER"]

        _handler = csInstallCluster()
        _handler.undoExecute(_ebox, _options, _step_list)

if __name__ == '__main__':
    unittest.main()