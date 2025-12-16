#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/tests_cs_prevmsetup.py /main/7 2025/08/25 06:17:10 pbellary Exp $
#
# tests_cs_prevmsetup.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_prevmsetup.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    02/24/25 - Bug 37570873 - EXADB-D|XS -- EXACLOUD |
#                           PROVISIONING | REVIEW AND ORGANIZE PREVM_CHECKS AND
#                           PREVM_SETUP STEPS
#    prsshukl    07/17/24 - Enh 34014317 - Unit tests for mRemoveStoragePool
#                           method
#    prsshukl    01/19/23 - Bug 34989467 - Added the new commands for Unit Test
#                           of mChangeForwardAccept method
#    aararora    11/09/22 - Unit test for mExecuteCmdLog2.
#    aararora    06/16/22 - Unit test file for prevm setup for mChangeForwardAccept and mCopyVifFiles methods
#    aararora    06/16/22 - Creation
#

import unittest

from unittest.mock import patch

from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.csstep.cs_prevmsetup import csPreVMSetup
from exabox.ovm.csstep.exascale.exascaleutils import ebExascaleUtils
from exabox.ovm.csstep.cs_util import csUtil

_active_storage_pool = \
"""scaqab10client01vm01.us.oracle.com
scaqab10client01vm02.us.oracle.com
scaqab10client01vm03.us.oracle.com
scaqab10client01vm04.us.oracle.com
scaqab10client01vm05.us.oracle.com
scaqab10client01vm06.us.oracle.com
scaqab10client01vm07.us.oracle.com
scaqab10client01vm08.us.oracle.com
"""

class testOptions(object): pass

class ebTestCSPreVmSetup(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCSPreVmSetup, self).setUpClass(False,False)
    
    def test_mChangeForwardAcceptSuccess(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario unit test on csPreVmSetup.mChangeForwardAccept.")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/mkdir -p", aRc=0, aPersist=True),
                    exaMockCommand("/bin/scp", aRc=0, aPersist=True),
                    exaMockCommand("/bin/sed -i", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csPreVMSetupInstance = csPreVMSetup()
        csPreVMSetupInstance.mChangeForwardAccept(self.mGetClubox())

    def test_mChangeForwardAcceptFailure(self):
        ebLogInfo("")
        ebLogInfo("Running failure scenario unit test on csPreVmSetup.mChangeForwardAccept.")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/mkdir -p", aRc=0, aPersist=True),
                    exaMockCommand("/bin/scp", aRc=0, aPersist=True),
                    exaMockCommand("/bin/sed -i", aRc=1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csPreVMSetupInstance = csPreVMSetup()
        csPreVMSetupInstance.mChangeForwardAccept(self.mGetClubox())

    def test_mCopyVifFilesIsKVM(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPreVmSetup.mCopyVifFiles for KVM system.")

        csPreVMSetupInstance = csPreVMSetup()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True):
            csPreVMSetupInstance.mCopyVifFiles(self.mGetClubox())

    def test_mCopyVifFilesIsNotKvmEbtExists(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPreVmSetup.mCopyVifFiles for Xen system and Ebt file exists.")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e", aRc=0, aPersist=True),
                    exaMockCommand("/bin/scp", aRc=0, aPersist=True),
                    exaMockCommand("/bin/ln -sf", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csPreVMSetupInstance = csPreVMSetup()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=False):
            csPreVMSetupInstance.mCopyVifFiles(self.mGetClubox())

    def test_mCopyVifFilesIsNotKvmEbtNotExists(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPreVmSetup.mCopyVifFiles for Xen system and ebt file does not exist.")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e", aRc=1, aPersist=True),
                    exaMockCommand("/bin/scp", aRc=0, aPersist=True),
                    exaMockCommand("/bin/ln -sf", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csPreVMSetupInstance = csPreVMSetup()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=False):
            csPreVMSetupInstance.mCopyVifFiles(self.mGetClubox())

    def test_mCopyVifFilesIsNotKvmEbtNotExistsLinkError(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPreVmSetup.mCopyVifFiles for Xen system and ebt file does not exist and there is copy/link error raised.")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e", aRc=1, aPersist=True),
                    exaMockCommand("/bin/scp", aRc=0, aPersist=True),
                    exaMockCommand("/bin/ln -sf", aRc=1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csPreVMSetupInstance = csPreVMSetup()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=False):
            self.assertRaisesRegex(Exception, "\*\*\* Could not copy/link vif files in Dom0: (.*[0-9]{1}adm[0-9]{1}.*|.*exdd*.*) \*\*\*", csPreVMSetupInstance.mCopyVifFiles, self.mGetClubox())

    def test_mExecuteCmdLog2Timeout(self):

        ebLogInfo("Running unit test on mExecuteCmdLog for timeout case.")
        _lsCmd = "ls -ltr"
        _timeout = 0
        with self.assertRaises(ExacloudRuntimeError):
            self.mGetClubox().mExecuteCmdLog2(_lsCmd, aTimeOut=_timeout)

    def test_mRemoveStoragePool_positive(self):

        ebLogInfo("Running unit test on csUtil.mRemoveStoragePool")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/virsh pool-list --name", aStdout=_active_storage_pool, aRc=0, aPersist=True),
                    exaMockCommand("/bin/virsh pool-destroy *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/virsh pool-undefine *", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csUtilInstance = csUtil()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True):
            csUtilInstance.mRemoveStoragePool(self.mGetClubox())
    
    def test_mRemoveStoragePool_domU_not_active(self):

        ebLogInfo("Running unit test on csUtil.mRemoveStoragePool when no active pool")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/virsh pool-list --name", aRc=1, aPersist=True),
                    exaMockCommand("/bin/virsh pool-undefine *", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csUtilInstance = csUtil()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True):
            csUtilInstance.mRemoveStoragePool(self.mGetClubox())

    def test_mRemoveStoragePool_virsh_pool_list_Fail(self):

        ebLogInfo("Running unit test on csUtil.mRemoveStoragePool when virsh pool-list command fails")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/virsh pool-list --name", aRc=1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csUtilInstance = csUtil()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True):
            csUtilInstance.mRemoveStoragePool(self.mGetClubox())

    def test_mRemoveStoragePool_virsh_pool_undefine_Fail(self):

        ebLogInfo("Running unit test on csUtil.mRemoveStoragePool when virsh pool-undefine command fails")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/virsh pool-list --name", aStdout=_active_storage_pool, aRc=0, aPersist=True),
                    exaMockCommand("/bin/virsh pool-destroy *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/virsh pool-undefine *", aRc=1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csUtilInstance = csUtil()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True):
            csUtilInstance.mRemoveStoragePool(self.mGetClubox())

    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mUpdateACL')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mDeleteFilesInDbVault')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mDetachAcfsVolume')
    @patch('exabox.ovm.csstep.cs_prevmsetup.csPreVMSetup.mPostVMDeleteSteps')
    def test_undoExecute(self, mock_mPostVMDeleteSteps, mock_mDetachAcfsVolume, mock_mDeleteFilesInDbVault, mUpdateACL):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPreVmSetup.undoExecute.")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e", aRc=0, aPersist=True),
                    exaMockCommand("/bin/scp", aRc=0, aPersist=True),
                    exaMockCommand("/bin/ln -sf", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csPreVMSetupInstance = csPreVMSetup()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=False):
            csPreVMSetupInstance.undoExecute(self.mGetClubox(), self.mGetClubox().mGetArgsOptions(), "ESTP_PREVM_SETUP")

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=False),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsXS', return_value=True):
            csPreVMSetupInstance.undoExecute(self.mGetClubox(), self.mGetClubox().mGetArgsOptions(), "ESTP_PREVM_SETUP")
        

if __name__ == '__main__':
    unittest.main() 
