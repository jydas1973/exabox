#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_edv.py /main/1 2026/01/13 17:55:25 jfsaldan Exp $
#
# tests_edv.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_edv.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    12/01/25 - Bug 38694363 - EXADB-XS-PP: VMC PROVISION FAILED AT
#                           THE TASK OF CREATEVM WITH ERROR OF "NO SUCH FILE OR
#                           DIRECTORY: DISK_CONFIG.XML" | EXACLOUD UNMOUNTS GCV
#                           VOLUME FROM OTHER VMS DURING PARALLEL CREATE
#                           SERVICE
#    jfsaldan    12/01/25 - Creation
#

import unittest
from unittest.mock import Mock, patch
from unittest.mock import MagicMock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from collections import namedtuple
from exabox.exadbxs.edv import unmount_stale_gcv_edv
from exabox.ovm.cludomufilesystems import ebNodeFilesystemInfo
from exabox.core.MockCommand import exaMockCommand
from exabox.utils.node import (node_exec_cmd, node_exec_cmd_check,
    node_cmd_abs_path_check, connect_to_host, node_list_process)
from exabox.core.Context import get_gcontext

class ebTestExaDBXSEdv(ebTestClucontrol):


    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)
        self.maxDiff = None

    @patch("exabox.exadbxs.edv.node_cmd_abs_path_check")
    @patch("exabox.exadbxs.edv.get_node_filesystems")
    def test_unmount_stale_gcv_edv_happy_path(self,
		mock_get_fs,
	  	mock_cmd_path):
        stale_fs = ebNodeFilesystemInfo(
            mountpoint="/EXAVMIMAGES/GuestImages/stalevm",
            device="/dev/exc/stalevol",
            fs_type="ext4",
            size_bytes=0,
            free_bytes=0,
            encrypted=False,
        )
        mock_get_fs.return_value = [stale_fs]
        mock_cmd_path.side_effect = [
            "/usr/bin/virsh",   # for list --all --name
            "/usr/bin/umount",  # for the umount call
            "/bin/sed",         # for the sed cleanup
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(
                        "/usr/bin/virsh list --all --name",
                        aRc=0,
                        aStdout="activevm\n",
                        aPersist=True,
                    ),
                    exaMockCommand(
                        "test.*pgrep",
                        aRc=0,
                    ),
                    exaMockCommand(
                        "test.*grep",
                        aRc=0,
                    ),
                    exaMockCommand(
                        "/sbin/pgrep -af 'vm_maker.*stalevm' | /sbin/grep -v $$",
                        aRc=0,
                        aStdout="",
                    ),
                    exaMockCommand(
                        "/usr/bin/umount /EXAVMIMAGES/GuestImages/stalevm",
                        aRc=0,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        "/bin/sed -i.*",
                        aRc=0,
                        aPersist=True,
                    ),
                ],
                [
                ],
            ],
        }
        self.mPrepareMockCommands(_cmds)

        _dom0, _ = self.mGetClubox().mReturnDom0DomUPair()[0]
        with connect_to_host(_dom0, get_gcontext()) as _node:
            unmounted = unmount_stale_gcv_edv(_node)

        self.assertEqual([stale_fs], unmounted)

    @patch("exabox.exadbxs.edv.node_cmd_abs_path_check")
    @patch("exabox.exadbxs.edv.get_node_filesystems")
    def test_unmount_stale_gcv_edv_nothing_stale(self,
		mock_get_fs,
	  	mock_cmd_path):
        stale_fs = ebNodeFilesystemInfo(
            mountpoint="/EXAVMIMAGES/GuestImages/stalevm",
            device="/dev/exc/stalevol",
            fs_type="ext4",
            size_bytes=0,
            free_bytes=0,
            encrypted=False,
        )
        mock_get_fs.return_value = [stale_fs]
        mock_cmd_path.side_effect = [
            "/usr/bin/virsh",   # for list --all --name
            "/usr/bin/umount",  # for the umount call
            "/bin/sed",         # for the sed cleanup
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(
                        "/usr/bin/virsh list --all --name",
                        aRc=0,
                        aStdout="activevm\nstalevm",
                        aPersist=True,
                    ),
                    exaMockCommand(
                        "test.*pgrep",
                        aRc=0,
                    ),
                    exaMockCommand(
                        "test.*grep",
                        aRc=0,
                    ),
                    exaMockCommand(
                        "/sbin/pgrep -af 'vm_maker.*stalevm' | /sbin/grep -v $$",
                        aRc=0,
                        aStdout="",
                    ),
                ],
                [
                ],
            ],
        }
        self.mPrepareMockCommands(_cmds)

        _dom0, _ = self.mGetClubox().mReturnDom0DomUPair()[0]
        with connect_to_host(_dom0, get_gcontext()) as _node:
            unmounted = unmount_stale_gcv_edv(_node)

        self.assertEqual([], unmounted)

    @patch("exabox.exadbxs.edv.node_cmd_abs_path_check")
    @patch("exabox.exadbxs.edv.get_node_filesystems")
    def test_unmount_stale_gcv_edv_vm_maker_running(self,
		mock_get_fs,
	  	mock_cmd_path):
        stale_fs = ebNodeFilesystemInfo(
            mountpoint="/EXAVMIMAGES/GuestImages/stalevm",
            device="/dev/exc/stalevol",
            fs_type="ext4",
            size_bytes=0,
            free_bytes=0,
            encrypted=False,
        )
        mock_get_fs.return_value = [stale_fs]
        mock_cmd_path.side_effect = [
            "/usr/bin/virsh",   # for list --all --name
            "/usr/bin/umount",  # for the umount call
            "/bin/sed",         # for the sed cleanup
        ]

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(
                        "/usr/bin/virsh list --all --name",
                        aRc=0,
                        aStdout="activevm\n",
                        aPersist=True,
                    ),
                    exaMockCommand(
                        "test.*pgrep",
                        aRc=0,
                    ),
                    exaMockCommand(
                        "test.*grep",
                        aRc=0,
                    ),
                    exaMockCommand(
                        "/sbin/pgrep -af 'vm_maker.*stalevm' | /sbin/grep -v $$",
                        aRc=0,
                        aStdout="1213 some vm_maker pid output",
                    ),
                ],
                [
                ],
            ],
        }
        self.mPrepareMockCommands(_cmds)

        _dom0, _ = self.mGetClubox().mReturnDom0DomUPair()[0]
        with connect_to_host(_dom0, get_gcontext()) as _node:
            unmounted = unmount_stale_gcv_edv(_node)

        self.assertEqual([], unmounted)


if __name__ == '__main__':
    unittest.main()
