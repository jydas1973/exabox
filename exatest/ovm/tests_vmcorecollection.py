#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_vmcorecollection.py /main/1 2025/04/01 20:53:23 ririgoye Exp $
#
# tests_vmcorecollection.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_vmcorecollection.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    03/05/25 - Enh 35314599 - exacloud: create an api in ecra for
#                           mars team to push the vmcore to mos
#    ririgoye    03/14/25 - Creation
#

import json
import unittest
import re
import copy
import warnings

from unittest.mock import patch, MagicMock, Mock, mock_open

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Context import get_gcontext
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.vmcorecollection import ebVMCoreCollector
from exabox.core.Error import ExacloudRuntimeError

TEST_TENANCY_OCID = "ocid1.tenancy.test..aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
TEST_OSS_NAMESPACE = "oss.test.namespace"
TEST_BUCKET_NAME = "test-bucket-for-vmcore"
TEST_VM_NAME = "test.vm.name.us.oracle.com"
TEST_OSS_PATH = {
    "bucket": TEST_BUCKET_NAME,
    "object_name": TEST_VM_NAME
}

class ebTestVMCoreCollector(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestVMCoreCollector, self).setUpClass(True, True)
        warnings.filterwarnings("ignore")
    
    def test_mCollectVMCoreLogs(self):
        # Prepare commands
        _mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/bin/virsh dump --live --memory-only --bypass-cache *", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/mkdir -p *", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/rm -rf *", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/usr/bin/mkdir -p *", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/rm -rf *", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_mockCommands)

        # Prepare exabox
        _ebox = copy.deepcopy(self.mGetClubox())
        _options = {"vm_name": TEST_VM_NAME}
        _ebox._exaBoxCluCtrl__options.jsonconf = _options
        _dpairs = _ebox.mReturnDom0DomUPair()
        _dom0s = [dom0 for dom0, _ in _dpairs]

        # Run tests
        _clucollector = ebVMCoreCollector(_ebox, _options)
        _rc = _clucollector.mCollectVMCoreLogs(_dom0s[0])
        self.assertEqual(_rc, 0)

    @patch('exabox.ovm.vmcorecollection.ebOSSBucketManager')
    def test_mUploadToOSS(self, aMockBucketManager):
        # Prepare exabox
        _ebox = copy.deepcopy(self.mGetClubox())
        _options = {"vm_name": TEST_VM_NAME}
        _ebox._exaBoxCluCtrl__options.jsonconf = _options
        _dpairs = _ebox.mReturnDom0DomUPair()
        _dom0s = [dom0 for dom0, _ in _dpairs]

        # Prepare mocks
        _fakeManager = MagicMock()
        _fakeManager.mBucketExists.return_value = None

        _dummyBucket = MagicMock()
        _dummyBucket.name = TEST_BUCKET_NAME
        _fakeManager.mCreateBucket.return_value = _dummyBucket

        _fakeManager.mUploadToBucket.return_value = None
        aMockBucketManager.return_value = _fakeManager

        _instance = ebVMCoreCollector(_ebox, _options)
        _instance.mGetVMName = MagicMock(return_value=TEST_VM_NAME)
        _instance.mSetTargetOssPath = MagicMock()

        # Run tests
        _testPath = "/tmp/testvmcore/test.tar.xz"
        _rc = _instance.mUploadToOss(_testPath)

        # Run assertions
        _fakeManager.mBucketExists.assert_called_once()
        _fakeManager.mCreateBucket.assert_called_once()
        _fakeManager.mUploadToBucket.assert_called_once_with(_testPath, TEST_VM_NAME)
        _instance.mSetTargetOssPath.assert_called_once_with(TEST_BUCKET_NAME, TEST_VM_NAME)

        self.assertEqual(_rc, 0)


if __name__ == "__main__":
    unittest.main()
