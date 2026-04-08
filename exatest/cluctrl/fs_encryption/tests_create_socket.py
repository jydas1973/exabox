#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/fs_encryption/tests_create_socket.py /main/1 2026/02/04 16:08:46 jfsaldan Exp $
#
# tests_create_socket.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_create_socket.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      Unittest for create_socket.py
#
#    NOTES
#      Ref: confluence.oraclecorp.com/confluence/display/EDCS/ExaCC+FedRamp+FS+Encryption+-+Exacloud+APIs+and+Debug+Steps
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    01/26/26 - Ut file for 'create_socket.py'
#    jfsaldan    01/26/26 - Creation
#

import unittest
from unittest.mock import MagicMock, patch

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo

import scripts.fs_encryption.create_socket as create_socket

class ebTestCreateSocket(ebTestClucontrol):


    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)
        self.maxDiff = None

    def test_mGetKVMSocketPath(self):
        """Validate happy-path socket resolution for a single domU."""
        ebLogInfo("Validating mGetKVMSocketPath happy path")

        expected_id = "123"
        expected_socket_path = f"/var/lib/libvirt/qemu/channel/target/domain-{expected_id}-domu1/vmfsexacc"
        util = create_socket.utility()

        stdout_mock = MagicMock()
        stdout_mock.read.return_value = f"{expected_id}\n".encode("utf-8")

        with patch.object(create_socket.utility, "mExecuteLocal") as mock_exec,\
             patch("scripts.fs_encryption.create_socket.glob.glob") as mock_glob,\
             patch("scripts.fs_encryption.create_socket.os.path.exists") as mock_exists:

            mock_exec.return_value = (0, stdout_mock, None)
            mock_glob.return_value = [expected_socket_path]
            mock_exists.return_value = True

            result = util.mGetKVMSocketPath("domu1.example.com")

        self.assertEqual(result, expected_socket_path)
        mock_exec.assert_called_once_with("/usr/bin/virsh domid domu1.example.com")
        mock_glob.assert_called_once_with(f"/var/lib/libvirt/qemu/channel/target/domain-{expected_id}-*/{create_socket.utility.SOCKET_NAME}")
        mock_exists.assert_called_once_with(expected_socket_path)

    def test_mGetKVMSocketPath_multiple_sockets_chosing_same_host(self):
        """Happy path, multiple sockets found but only 1 per domU"""
        ebLogInfo("Validating mGetKVMSocketPath multiple sockets but only 1 per host")

        expected_id = "456"
        socket_paths = [
            f"/var/lib/libvirt/qemu/channel/target/domain-{expected_id}-domu1/vmfsexacc",
            f"/var/lib/libvirt/qemu/channel/target/domain-{expected_id}-domu1-extra/vmfsexacc",
        ]
        util = create_socket.utility()
        expected_socket_path = f"/var/lib/libvirt/qemu/channel/target/domain-{expected_id}-domu1/vmfsexacc"

        stdout_mock = MagicMock()
        stdout_mock.read.return_value = f"{expected_id}\n".encode("utf-8")

        with patch.object(create_socket.utility, "mExecuteLocal") as mock_exec,\
             patch("scripts.fs_encryption.create_socket.glob.glob") as mock_glob,\
             patch("scripts.fs_encryption.create_socket.os.path.exists") as mock_exists:

            mock_exec.return_value = (0, stdout_mock, None)
            mock_glob.return_value = socket_paths
            mock_exists.side_effect = [True, True]


            result = util.mGetKVMSocketPath("domu1.example.com")

        self.assertEqual(result, expected_socket_path)
        mock_exec.assert_called_once_with("/usr/bin/virsh domid domu1.example.com")
        mock_glob.assert_called_once_with(f"/var/lib/libvirt/qemu/channel/target/domain-{expected_id}-*/{create_socket.utility.SOCKET_NAME}")

if __name__ == '__main__':
    unittest.main()
