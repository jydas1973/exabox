#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/remote_lock/tests_remotelock.py /main/1 2024/07/02 05:00:42 aararora Exp $
#
# tests_remotelock.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_remotelock.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    06/27/24 - Bug 36743916: op_cleanup command correction.
#    aararora    06/27/24 - Creation
#
import unittest

from unittest.mock import patch

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.remotelock import RemoteLock

class ebGetDefaultDB:
    def __init__(self):
        pass

    def mDeleteLock(uuid, lock, host):
        return

class testOptions(object): pass

class ebTestRemoteLock(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestRemoteLock, self).setUpClass(False,False)
        self._cluctrl = self.mGetClubox(self)

    def test_release_unowned(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario unit test on RemoteLock.release_unowned.")
        self._cluctrl.mSetSharedEnv(True)
        self.remote_lock = RemoteLock(self._cluctrl)
        with patch("exabox.core.Node.exaBoxNode.mConnect"),\
             patch("exabox.ovm.remotelock.node_exec_cmd", return_value=(0, "out", "stderr")),\
             patch("exabox.ovm.remotelock.node_exec_cmd_check"),\
             patch("exabox.ovm.remotelock.ebGetDefaultDB", return_value=ebGetDefaultDB),\
             patch("exabox.ovm.remotelock.RemoteLock.isRemoteLocalFileSame"):
            self.remote_lock.release_unowned("1234", "Default")

if __name__ == '__main__':
    unittest.main()