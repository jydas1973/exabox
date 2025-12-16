#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/shared_methods/tests_create_unmount_lvm.py /main/7 2025/08/28 00:24:12 scoral Exp $
#
# tests_create_unmount_lvm.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_create_unmount_lvm.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    remamid     03/06/24 - Bug 36360004 - add mock commands for domu ol7 dom0
#                           ol8 case for u02 filesystem creation
#    jfsaldan    03/02/22 - Creation
#

import unittest
from unittest.mock import patch
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.cludomufilesystems import parse_size
from exabox.ovm.sysimghandler import mCreateImageLVM, mUnmountImageLVM
from exabox.utils.node import connect_to_host
from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
class ebTestCreateDeleteLVM(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.maxDiff = None

    #
    # Test mCreateImageLVM
    #
    def test_create_lvm_ok_u02_not_present_add_a_keep_false(self):
        """
        Function to test clucontrol mCreateImageLVM method
        """

        # Declare variables to use
        _img_path = "/EXAVMIMAGES/GuestImages/scaqab10adm07vm03.us.oracle.com/u02_extra.img"
        _type = "ext4"
        _size = "60G"
        _sector_size =  4194304
        _sector_size_mkpart = _sector_size - 34

        # Prepare Commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("pvs | grep u02_extra", aStdout = "\n", aRc = 0),
                    exaMockCommand(f"test -e {_img_path}", aStdout = "\n", aRc = 1),
                    exaMockCommand("losetup -a", aStdout = "\n", aRc = 0),
                    exaMockCommand("/bin/test -e /bin/qemu-img"),
                    exaMockCommand("/bin/test -e /sbin/parted"),
                    exaMockCommand(f"/bin/qemu-img create {_img_path} {parse_size(_size)}B -f raw"),
                    exaMockCommand(f"/sbin/parted -s {_img_path} mktable msdos"),
                    exaMockCommand(f"/sbin/parted -s {_img_path} mkpart primary 0% 100%"),
                    exaMockCommand(f"/sbin/parted {_img_path} set 1 lvm on"),
                    exaMockCommand(f"kpartx -a -v {_img_path}",
                        aStdout = "add map loop0p1 (252:11): 0 4194207 linear /dev/loop0 64\n",
                        aRc = 0),
                    exaMockCommand("losetup -a",
                        aStdout = f"/dev/loop0: [64518]:{_sector_size} ({_img_path})",
                        aRc = 0),
                    exaMockCommand("lvm pvcreate --force  /dev/mapper/loop0p1", aStdout = "\n", aRc = 0),
                    exaMockCommand("lvm vgcreate VGExaDbDisk.u02_extra.img /dev/mapper/loop0p1", aStdout = "\n", aRc = 0),
                    exaMockCommand("lvm lvcreate -L 58G -n LVDBDisk VGExaDbDisk.u02_extra.img", aStdout = "\n", aRc = 0),
                    exaMockCommand("lvm lvchange -a y /dev/VGExaDbDisk.u02_extra.img/LVDBDisk", aStdout = "\n", aRc = 0),
                    exaMockCommand("mkfs.ext4 -F /dev/VGExaDbDisk.u02_extra.img/LVDBDisk", aStdout = "\n", aRc = 0),
                    exaMockCommand("mkfs.ext4 -F /dev/VGExaDbDisk.u02_extra.img/LVDBDisk -O ^metadata_csum", aStdout = "\n", aRc = 0),
                    exaMockCommand("e2label /dev/VGExaDbDisk.u02_extra.img/LVDBDisk U02_IMAGE", aStdout = "\n", aRc = 0),
                    exaMockCommand("lvm lvchange -a n /dev/VGExaDbDisk.u02_extra.img/LVDBDisk", aStdout = "\n", aRc = 0),
                    exaMockCommand("/usr/sbin/udevadm settle ;  pvscan --cache", aStdout = "\n", aRc = 0),
                    exaMockCommand("lvremove -f VGExaDbDisk.u02_extra.img/LVDBDisk", aStdout = "\n", aRc = 0),
                    exaMockCommand("vgchange -an VGExaDbDisk.u02_extra.img", aStdout = "\n", aRc = 0),
                    exaMockCommand("vgremove VGExaDbDisk.u02_extra.img --force", aStdout = "\n", aRc = 0),
                    exaMockCommand("pvremove /dev/mapper/loop0p1 --force --force <<< y", aStdout = "\n", aRc = 0),
                    exaMockCommand("kpartx -d -v /dev/loop0", aStdout = "\n", aRc = 0),
                    exaMockCommand("losetup -d /dev/loop0", aStdout = "\n", aRc = 0),
                    exaMockCommand("/usr/sbin/udevadm settle ;  pvscan --cache", aStdout = "\n", aRc = 0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variable to use
        _ebox = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetMajorityHostVersion', return_value="OL7"),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleLinuxVersion', return_value="OL8"):

            _results = []
            _expected = [
                    '/dev/VGExaDbDisk.u02_extra.img/LVDBDisk',
                    '/dev/VGExaDbDisk.u02_extra.img/LVDBDisk']
    
            # Run test
            for _dom0, _domU in _ebox.mReturnDom0DomUPair():
    
                with connect_to_host(_dom0, get_gcontext()) as _node:
    
                    _results.append(mCreateImageLVM(
                        _ebox,
                        aNode = _node,
                        aPath = _img_path,
                        aSize = _size,
                        aType = _type,
                        aKeep = False))
    
            self.assertEqual(_expected, _results)

    def test_create_lvm_ok_u02_not_present_add_a_keep_true(self):
        """
        Function to test clucontrol mCreateImageLVM method
        """

        # Declare variables to use
        _img_path = "/EXAVMIMAGES/GuestImages/scaqab10adm07vm03.us.oracle.com/u02_extra.img"
        _type = "ext4"
        _size = "60G"
        _sector_size =  4194304
        _sector_size_mkpart = _sector_size - 34

        # Prepare Commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("pvs | grep u02_extra", aStdout = "\n", aRc = 0),
                    exaMockCommand(f"test -e {_img_path}", aStdout = "\n", aRc = 1),
                    exaMockCommand("losetup -a", aStdout = "\n", aRc = 0),
                    exaMockCommand("/bin/test -e /bin/qemu-img"),
                    exaMockCommand("/bin/test -e /sbin/parted"),
                    exaMockCommand(f"/bin/qemu-img create {_img_path} {parse_size(_size)}B -f raw"),
                    exaMockCommand(f"/sbin/parted -s {_img_path} mktable msdos"),
                    exaMockCommand(f"/sbin/parted -s {_img_path} mkpart primary 0% 100%"),
                    exaMockCommand(f"/sbin/parted {_img_path} set 1 lvm on"),
                    exaMockCommand(f"kpartx -a -v {_img_path}",
                        aStdout = "add map loop0p1 (252:11): 0 4194207 linear /dev/loop0 64\n",
                        aRc = 0),
                    exaMockCommand("losetup -a",
                        aStdout = f"/dev/loop0: [64518]:{_sector_size} ({_img_path})",
                        aRc = 0),
                    exaMockCommand("lvm pvcreate --force  /dev/mapper/loop0p1", aStdout = "\n", aRc = 0),
                    exaMockCommand("lvm vgcreate VGExaDbDisk.u02_extra.img /dev/mapper/loop0p1", aStdout = "\n", aRc = 0),
                    exaMockCommand("lvm lvcreate -L 58G -n LVDBDisk VGExaDbDisk.u02_extra.img", aStdout = "\n", aRc = 0),
                    exaMockCommand("lvm lvchange -a y /dev/VGExaDbDisk.u02_extra.img/LVDBDisk", aStdout = "\n", aRc = 0),
                    exaMockCommand("mkfs.ext4 -F /dev/VGExaDbDisk.u02_extra.img/LVDBDisk", aStdout = "\n", aRc = 0),
                    exaMockCommand("mkfs.ext4 -F /dev/VGExaDbDisk.u02_extra.img/LVDBDisk -O ^metadata_csum", aStdout = "\n", aRc = 0),
                    exaMockCommand("e2label /dev/VGExaDbDisk.u02_extra.img/LVDBDisk U02_IMAGE", aStdout = "\n", aRc = 0),

                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variable to use
        _ebox = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetMajorityHostVersion', return_value="OL7"),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleLinuxVersion', return_value="OL7"):

            _results = []
            _expected = [
                    '/dev/VGExaDbDisk.u02_extra.img/LVDBDisk',
                    '/dev/VGExaDbDisk.u02_extra.img/LVDBDisk']
    
            # Run test
            for _dom0, _domU in _ebox.mReturnDom0DomUPair():
    
                with connect_to_host(_dom0, get_gcontext()) as _node:
    
                    _results.append(mCreateImageLVM(
                        _ebox,
                        aNode = _node,
                        aPath = _img_path,
                        aSize = _size,
                        aType = _type,
                        aKeep = True))
    
            self.assertEqual(_expected, _results)

    def test_create_lvm_ok_u02_already_present_error(self):
        """
        Function to test clucontrol mCreateImageLVM method
        """

        # Declare variables to use
        _img_path = "/EXAVMIMAGES/GuestImages/scaqab10adm07vm03.us.oracle.com/u02_extra.img"
        _type = "ext4"
        _size = "60G"

        # Prepare Commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("pvs | grep u02_extra", aStdout = "\n", aRc = 0),
                    exaMockCommand(f"test -e {_img_path}", aStdout = "\n", aRc = 0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variable to use
        _ebox = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetMajorityHostVersion', return_value="OL7"),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleLinuxVersion', return_value="OL8"):

            _results = []
            _expected = [
                    '/dev/VGExaDbDisk.u02_extra.img/LVDBDisk',
                    '/dev/VGExaDbDisk.u02_extra.img/LVDBDisk']
    
            # Run test
            for _dom0, _domU in _ebox.mReturnDom0DomUPair():
    
                with connect_to_host(_dom0, get_gcontext()) as _node:
    
                    self.assertRaises(
                        ExacloudRuntimeError,
                        lambda: mCreateImageLVM(
                            _ebox,
                            aNode = _node,
                            aPath = _img_path,
                            aSize = _size,
                            aType = _type,
                            aKeep = True))

    def test_create_lvm_ok_u02_lefotver_cleaning_ok_keep_false(self):
        """
        Function to test clucontrol mCreateImageLVM method
        """

        # Declare variables to use
        _img_path = "/EXAVMIMAGES/GuestImages/scaqab10adm07vm03.us.oracle.com/u02_extra.img"
        _type = "ext4"
        _size = "60G"
        _sector_size =  4194304
        _sector_size_mkpart = _sector_size - 34

        # Prepare Commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("pvs | grep u02_extra", aStdout = "\n", aRc = 0),
                    exaMockCommand(f"test -e {_img_path}", aStdout = "\n", aRc = 1),
                    exaMockCommand("losetup -a", aStdout = "\n", aRc = 0),
                    exaMockCommand("/bin/test -e /bin/qemu-img"),
                    exaMockCommand("/bin/test -e /sbin/parted"),
                    exaMockCommand(f"/bin/qemu-img create {_img_path} {parse_size(_size)}B -f raw"),
                    exaMockCommand(f"/sbin/parted -s {_img_path} mktable msdos"),
                    exaMockCommand(f"/sbin/parted -s {_img_path} mkpart primary 0% 100%"),
                    exaMockCommand(f"/sbin/parted {_img_path} set 1 lvm on"),
                    exaMockCommand(f"kpartx -a -v {_img_path}",
                        aStdout = "add map loop0p1 (252:11): 0 4194207 linear /dev/loop0 64\n",
                        aRc = 0),
                    exaMockCommand("losetup -a",
                        aStdout = f"/dev/loop0: [64518]:{_sector_size} ({_img_path})",
                        aRc = 0),
                    exaMockCommand("lvm pvcreate --force  /dev/mapper/loop0p1", aStdout = "\n", aRc = 0),
                    exaMockCommand("lvm vgcreate VGExaDbDisk.u02_extra.img /dev/mapper/loop0p1", aStdout = "\n", aRc = 0),
                    exaMockCommand("lvm lvcreate -L 58G -n LVDBDisk VGExaDbDisk.u02_extra.img", aStdout = "\n", aRc = 0),
                    exaMockCommand("lvm lvchange -a y /dev/VGExaDbDisk.u02_extra.img/LVDBDisk", aStdout = "\n", aRc = 0),
                    exaMockCommand("mkfs.ext4 -F /dev/VGExaDbDisk.u02_extra.img/LVDBDisk", aStdout = "\n", aRc = 0),
                    exaMockCommand("mkfs.ext4 -F /dev/VGExaDbDisk.u02_extra.img/LVDBDisk -O ^metadata_csum", aStdout = "\n", aRc = 0),
                    exaMockCommand("e2label /dev/VGExaDbDisk.u02_extra.img/LVDBDisk U02_IMAGE", aStdout = "\n", aRc = 0),
                    exaMockCommand("lvm lvchange -a n /dev/VGExaDbDisk.u02_extra.img/LVDBDisk", aStdout = "\n", aRc = 0),
                    exaMockCommand("/usr/sbin/udevadm settle ;  pvscan --cache", aStdout = "\n", aRc = 0),
                    exaMockCommand("lvremove -f VGExaDbDisk.u02_extra.img/LVDBDisk", aStdout = "\n", aRc = 0),
                    exaMockCommand("vgchange -an VGExaDbDisk.u02_extra.img", aStdout = "\n", aRc = 0),
                    exaMockCommand("vgremove VGExaDbDisk.u02_extra.img --force", aStdout = "\n", aRc = 0),
                    exaMockCommand("pvremove /dev/mapper/loop0p1 --force --force <<< y", aStdout = "\n", aRc = 0),
                    exaMockCommand("kpartx -d -v /dev/loop0", aStdout = "\n", aRc = 0),
                    exaMockCommand("losetup -d /dev/loop0", aStdout = "\n", aRc = 0),
                    exaMockCommand("/usr/sbin/udevadm settle ;  pvscan --cache", aStdout = "\n", aRc = 0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variable to use
        _ebox = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetMajorityHostVersion', return_value="OL7"),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleLinuxVersion', return_value="OL8"):

            _results = []
            _expected = [
                    '/dev/VGExaDbDisk.u02_extra.img/LVDBDisk',
                    '/dev/VGExaDbDisk.u02_extra.img/LVDBDisk']
    
            # Run test
            for _dom0, _domU in _ebox.mReturnDom0DomUPair():
    
                with connect_to_host(_dom0, get_gcontext()) as _node:
    
                    _results.append(mCreateImageLVM(
                        _ebox,
                        aNode = _node,
                        aPath = _img_path,
                        aSize = _size,
                        aType = _type,
                        aKeep = False))
    
            self.assertEqual(_expected, _results)

    def test_create_lvm_not_ok_u02_leftover_cleaning_fails(self):
        """
        Function to test clucontrol mCreateImageLVM method
        """

        # Declare variables to use
        _img_path = "/EXAVMIMAGES/GuestImages/scaqab10adm07vm03.us.oracle.com/u02_extra.img"
        _type = "ext4"
        _size = "60G"
        _sector_size =  4194304

        # Prepare Commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("pvs | grep u02_extra", aStdout = "\n", aRc = 0),
                    exaMockCommand(f"test -e {_img_path}", aStdout = "\n", aRc = 1),
                    exaMockCommand("losetup -a",
                        aStdout = f"/dev/loop0: [64518]:{_sector_size} ({_img_path})", # already present /dev/loop0
                        aRc = 0),
                    exaMockCommand("kpartx -v -d /dev/loop0 ; losetup -d /dev/loop0"),
                    exaMockCommand("losetup -a",
                        aStdout = f"/dev/loop0: [64518]:{_sector_size} ({_img_path})",
                        aRc = 0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variable to use
        _ebox = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetMajorityHostVersion', return_value="OL7"),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleLinuxVersion', return_value="OL8"):

            _results = []
            _expected = [
                    '/dev/VGExaDbDisk.u02_extra.img/LVDBDisk',
                    '/dev/VGExaDbDisk.u02_extra.img/LVDBDisk']
    
            # Run test
            for _dom0, _domU in _ebox.mReturnDom0DomUPair():
    
                with connect_to_host(_dom0, get_gcontext()) as _node:
    
                    self.assertRaises(
                        ExacloudRuntimeError,
                        lambda: mCreateImageLVM(
                            _ebox,
                            aNode = _node,
                            aPath = _img_path,
                            aSize = _size,
                            aType = _type,
                            aKeep = True))

    #
    # Test mCreateImageLVM
    #

    #
    # Test mUnmountImageLVM
    #
    def test_unmount_lvm_ok_u02_is_not_present(self):
        """
        Function to test clucontrol mUnmountImageLVM method
        """

        # Declare variables to use
        _img_path = "/EXAVMIMAGES/GuestImages/scaqab10adm07vm03.us.oracle.com/u02_extra.img"

        # Prepare Commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("pvs | grep u02_extra", aStdout = "\n", aRc = 0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Declare variable to use
        _ebox = self.mGetClubox()

        _results = []
        _expected = [None, None]

        # Run test
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():

            with connect_to_host(_dom0, get_gcontext()) as _node:

                _results.append(mUnmountImageLVM(
                    _ebox,
                    aNode = _node,
                    aPath = _img_path))

        self.assertEqual(_expected, _results)

    def test_unmount_lvm_ok_u02_is_present_cleanup_ok(self):
        """
        Function to test clucontrol mUnmountImageLVM method
        """

        # Declare variables to use
        _img_path = "/EXAVMIMAGES/GuestImages/scaqab10adm07vm03.us.oracle.com/u02_extra.img"

        # Prepare Commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("pvs | grep u02_extra",
                        aStdout = "/dev/sdb1 VGExaDbDisk.u02_extra.img lvm2 a-- <80.00g <2.00g\n",
                        aRc = 0),
                    exaMockCommand("lvm lvchange -a n /dev/VGExaDbDisk.u02_extra.img/LVDBDisk",
                        aStdout = "\n", aRc = 0),
                    exaMockCommand("vgchange -an VGExaDbDisk.u02_extra.img",
                        aStdout = "\n", aRc = 0),
                    exaMockCommand("kpartx -d -v",
                        aStdout = "\n", aRc = 0),
                    exaMockCommand("/usr/sbin/udevadm settle ;  pvscan --cache",
                        aStdout = "\n", aRc = 0),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        # Declare variable to use
        _ebox = self.mGetClubox()

        _results = []
        _expected = [None, None]

        # Run test
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():

            with connect_to_host(_dom0, get_gcontext()) as _node:

                _results.append(mUnmountImageLVM(
                    _ebox,
                    aNode = _node,
                    aPath = _img_path))

        self.assertEqual(_expected, _results)


    #
    # Test mUnmountImageLVM
    #

if __name__ == '__main__':
    unittest.main()

