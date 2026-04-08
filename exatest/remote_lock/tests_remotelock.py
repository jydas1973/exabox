#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/remote_lock/tests_remotelock.py /main/2 2026/01/07 15:02:49 bhpati Exp $
#
# tests_remotelock.py
#
# Copyright (c) 2024, 2026, Oracle and/or its affiliates.
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
#    dekuckre    03/10/26 - add rollback unit test
#    bhpati      12/08/25 - Bug 38635249 - FIX DOM0 LOCK HANG ISSUE
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
    
    def test_acquire_fails_when_host_unreachable(self):
        ebLogInfo("")
        ebLogInfo("Running failure scenario unit test on RemoteLock.acquire when host is unreachable.")
        self._cluctrl.mSetSharedEnv(True)
        original_hosts_fn = self._cluctrl.mReturnAllClusterHosts
        self._cluctrl.mReturnAllClusterHosts = lambda: (["host1"], [], [], [])
        remote_lock = RemoteLock(self._cluctrl)
        try:
            with patch.object(exaBoxNode, "mIsConnectable", return_value=False) as mock_is_connectable, \
                patch("exabox.ovm.remotelock.RemoteLock.update_worker_port"), \
                patch("exabox.ovm.remotelock.RemoteLock._cleanup_processes"):
                with self.assertRaises(ExacloudRuntimeError):
                    remote_lock.acquire(lock_name="dom0")
                mock_is_connectable.assert_called_once_with("host1")
        finally:
            self._cluctrl.mReturnAllClusterHosts = original_hosts_fn

    def test_acquire_rolls_back_on_partial_failure(self):
        ebLogInfo("")
        ebLogInfo("Running rollback scenario unit test on RemoteLock.acquire.")
        self._cluctrl.mSetSharedEnv(True)
        original_hosts_fn = self._cluctrl.mReturnAllClusterHosts
        self._cluctrl.mReturnAllClusterHosts = lambda: (["host1", "host2"], [], [], [])
        remote_lock = RemoteLock(self._cluctrl)
        try:
            with patch.object(exaBoxNode, "mIsConnectable", return_value=True), \
                patch("exabox.ovm.remotelock.RemoteLock.update_worker_port"), \
                patch("exabox.ovm.remotelock.RemoteLock._cleanup_processes"), \
                patch("exabox.ovm.remotelock.RemoteLock._release_per_host") as mock_release, \
                patch("exabox.ovm.remotelock.RemoteLock._acquire_per_host") as mock_acquire:
                def _acquire_side_effect(host, uuid, lock_name, acquired_count, host_count):
                    if host == "host2":
                        raise RuntimeError("acquire failed")

                mock_acquire.side_effect = _acquire_side_effect
                with self.assertRaises(ExacloudRuntimeError):
                    remote_lock.acquire(lock_name="dom0")

                mock_release.assert_called_once()
                release_args = mock_release.call_args[0]
                self.assertEqual(release_args[0], "host1")
                self.assertEqual(release_args[2], "dom0")
                self.assertEqual(release_args[3], 1)
                self.assertEqual(release_args[4], 1)
        finally:
            self._cluctrl.mReturnAllClusterHosts = original_hosts_fn

if __name__ == '__main__':
    unittest.main()
