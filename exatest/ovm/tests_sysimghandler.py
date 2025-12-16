#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_sysimghandler.py /main/20 2025/12/01 22:37:00 avimonda Exp $
#
# tests_sysimghandler.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_sysimghandler.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    avimonda    11/05/25 - Bug 38427813 - OCI: EXACS: PROVISIONING FAILED WITH
#                           EXACLOUD ERROR CODE: 1877 EXACLOUD : ERROR IN
#                           MULTIPROCESSING(NON-ZERO EXITCODE(-9) RETURNED
#                           <PROCESSSTRUCTURE(<DOM0 NODE>, STOPPED[SIGKILL])>,
#                           ID: <DOM0 NODE>, START_TIME: <T1>, END_TIME: <T2>,
#                           MAX_TIME
#    jfsaldan    10/28/25 - Bug 38559314 - EXADBXS Y25W42 | CREATEVM FAILED | 2
#                           DOM0S HAVE DIFFERENT IMAGE VERSION | PARALLEL
#                           CREATE SERVICE 'B' WITH DIFFERENT FIRST.BOOT IMAGE
#                           SELECTED DELETED FIRST.BOOT IMAGE OF OPERATIONS 'A'
#    avimonda    07/23/25 - Bug 38151443 - EXACS: PROVISIONING FAILED WITH
#                           EXACLOUD ERROR CODE: 1793 EXACLOUD : SOMETHING
#                           WRONG HAPPENED WHILE IN FTL | ATP | U02 VOLUME NOT
#                           PROPERLY MOUNTED/CREATED
#    gparada     06/02/25 - 37963204 Fix for System Image in hybrid infra
#    bhpati      05/27/25 - Bug 37860899 - Fix mIsRtgImgPresent if NoneType
#                           object returned
#    gparada     04/24/25 - 37872666 Fix mGetSystemImageVersionMap regex
#    jfsaldan    04/08/25 - Enh 37647115 - EXACLOUD - REDUCE
#                           COMPRESSION/DECOMPRESSION TIME FOR SYSTEM IMAGE.
#                           REPLACE BZIP2 BY PBZIP2 OR SIMILAR
#    gparada     01/27/25 - Bug 37450961 Fallback to IMG file if RGT not present
#    naps        08/12/24 - Bug 36908342 - X11 support.
#    aararora    03/07/24 - Bug 36367482: Unit test fix
#    gparada     11/22/23 - Skip Custom Img code for ExaDB-XS/ExaCompute
#    gparada     08/18/23 - UT's for hasDomUCustomOS, and untested functions
#    gparada     08/18/23 - Creation
#

import unittest
import io
from typing import Tuple

from exabox.core.Context import get_gcontext
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.ovm.sysimghandler import \
    getVMImageArchiveInRepo, \
    getNewestVMImageArchiveInRepo, \
    hasDomUCustomOS, \
    mGetSystemImageVersionMap, \
    mSearchImgInDom0s, \
    mCleanOldImgsAndEnsureGivenImgInDom0, \
    mVerifyImagesMultiProc, \
    getDom0VMImagesInfo, \
    copyVMImageVersionToDom0IfMissing, \
    mUnmountImageLVM, \
    mIsRtgImgPresent, \
    mGetVMImageArchiveInfoInLocalRepo, \
    mGetLocalFileHash

from exabox.core.Node import exaBoxNode

from unittest.mock import patch, Mock

class ebTestSysImgHandler(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    # Mock functions
    def mock_mCheckConfigOptionAllowCustomVersion(self, aOption, aValue=None):
        if aOption == 'allow_domu_custom_version':
            return 'True'
        if aOption == 'exadata_custom_domu_version':
            return None

    def mock_mCheckConfigOptionExaCC(self, aOption, aValue=None):
        if aOption == 'allow_domu_custom_version':
            return 'True'
        if aOption == 'exadata_custom_domu_version':
            return "21.2.16.0.0.220914"

    def mock_mCheckConfigOptionExaCS(self, aOption, aValue=None):
        if aOption == 'allow_domu_custom_version':
            return 'True'
        if aOption == 'default_domu_img_version':
            return "21.2.16.0.0.220914"
        return None 

    def mock_mCheckConfigOptionExaconfNone(self, aOption, aValue=None):
        if aOption == 'allow_domu_custom_version':
            return 'True'
        if aOption == 'default_domu_img_version_last_res':
            return None
        return None 

    def mock_mCheckConfigOptionExaconfValid(self, aOption, aValue=None):
        if aOption == 'allow_domu_custom_version':
            return 'True'
        if aOption == 'default_domu_img_version_last_res':
            return "21.1.2.3"
        return None 

    def mock_mGetConfigOptionsRTG(self):
        # _config_opts = get_gcontext().mGetConfigOptions()
        _config_opts = {}
        _config_opts["rtg_enabled_exacc"] = "True"
        _config_opts["rtg_enabled_exadbxs"] = "True"
        _config_opts["rtg_enabled_exacs"] = "True"
        return _config_opts 

    # Unit Tests
    def test_getVMImageArchiveInRepo(self):
        # This tests __getVMImagesInRepo() internally
        _img_name = "System.first.boot.20.1.1.0.0.img"
        _files = [f"{_img_name}.bz2"]
        with patch('os.listdir', return_value = _files),\
            patch('os.path.isfile', return_value = True):
            img = getVMImageArchiveInRepo("20.1.1.0.0",False,False)
            self.assertIsNotNone(img)
            self.assertEqual(img["imgBaseName"],_img_name)
            self.assertEqual(img["imgVersion"],"20.1.1.0.0")
            self.assertFalse(img["isKvmImg"])
            self.assertTrue(img["isArchive"])

    def test_getVMImageArchiveInRepoNone(self):
        # This tests __getVMImagesInRepo() internally
        _files = ["System.first.boot.20.1.1.0.0.xyz"]
        with patch('os.listdir', return_value = _files),\
            patch('os.path.isfile', return_value = True):
            img = getVMImageArchiveInRepo("20.1.1.0.0",False,False)            
            self.assertIsNone(img)

    def test_getNewestVMImageArchiveInRepo(self):
        # This tests __getVMImagesInRepo() internally
        _img_name = "System.first.boot.20.1.1.0.0.img"
        _files = [f"{_img_name}.bz2"]
        with patch('os.listdir', return_value = _files),\
            patch('os.path.isfile', return_value = True):
            img = getNewestVMImageArchiveInRepo(False)
            self.assertIsNotNone(img)

    def test_hasDomUCustomOS_ExaCC(self):
        _ebox_local = self.mGetClubox()
        self.mGetClubox().mSetOciExacc(True)

        # Scenario 01 for ExaCC, exadata_custom_domu_version
        with patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', 
                   return_value="X9"),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', 
                   side_effect=self.mock_mCheckConfigOptionExaCC):
            _img = hasDomUCustomOS(_ebox_local)
            self.assertEqual(_img, "21.2.16.0.0.220914")

    def test_hasDomUCustomOS_JSON(self):
        _ebox_local = self.mGetClubox()

        # Scenario 02, uses json properties        
        _options = self.mGetPayload()
        _options['rack'] = {}
        _options['rack']['image_version'] = "22.2.1.032223"
        _ebox_local.mGetArgsOptions().jsonconf = _options
        
        with patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', 
                   return_value="X9"),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', 
                   side_effect=self.mock_mCheckConfigOptionAllowCustomVersion): 
            _img = hasDomUCustomOS(_ebox_local)
            self.assertEqual(_img, "22.2.1.032223")

    def test_hasDomUCustomOS_ExaCS(self):
        _ebox_local = self.mGetClubox()

        # Scenario 03 for ExaCS, default_domu_img_version
        with patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', 
                   return_value="X9"),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', 
                   side_effect=self.mock_mCheckConfigOptionAllowCustomVersion),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', 
                   side_effect=self.mock_mCheckConfigOptionExaCS):      
            _img = hasDomUCustomOS(_ebox_local)
            self.assertEqual(_img, "21.2.16.0.0.220914")

    def test_hasDomUCustomOS_X10_negative(self):
        _ebox_local = self.mGetClubox()

        # Scenario 04 for ExaCS, Model X10, clear previous payload
        _options = self.mGetPayload()
        _options['rack'] = {}
        _ebox_local.mGetArgsOptions().jsonconf = _options

        with patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', 
                   return_value="X10"),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', 
                   side_effect=self.mock_mCheckConfigOptionAllowCustomVersion),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', 
                   side_effect=self.mock_mCheckConfigOptionExaCS):                  
            # self.assertRaisesRegex(ValueError, 
            #     f"Custom DomU version 21.2.16.0.0.220914 is not compatible " \
            #     "with X10M, please choose a version greater than 23.", 
            #     hasDomUCustomOS, _ebox_local)
            _img = hasDomUCustomOS(_ebox_local)
            self.assertIsNone(_img)

    def test_hasDomUCustomOS_X11_negative(self):
        _ebox_local = self.mGetClubox()

        # Scenario 04 for ExaCS, Model X11, clear previous payload
        _options = self.mGetPayload()
        _options['rack'] = {}
        _ebox_local.mGetArgsOptions().jsonconf = _options

        with patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel',
                   return_value="X11"),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption',
                   side_effect=self.mock_mCheckConfigOptionAllowCustomVersion),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption',
                   side_effect=self.mock_mCheckConfigOptionExaCS):
            _img = hasDomUCustomOS(_ebox_local)
            self.assertIsNone(_img)

    def test_hasDomUCustomOS_ExaDB_XS(self):
        _ebox_local = self.mGetClubox()

        # Scenario 03b for ExaDB-XS, return None
        _options = self.mGetPayload()
        _options['rack'] = {}
        _ebox_local.mGetArgsOptions().jsonconf = _options

        with patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', 
                   return_value="X9"),\
            patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsExaScale', 
                   return_value=True),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', 
                   side_effect=self.mock_mCheckConfigOptionAllowCustomVersion),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', 
                   side_effect=self.mock_mCheckConfigOptionExaCS):                  
            _img = hasDomUCustomOS(_ebox_local)
            self.assertIsNone(_img)

    def test_hasDomUCustomOS_exabox_conf_missing(self):
        _ebox_local = self.mGetClubox()

        # Scenario 05 NO custom version provided, exabox conf is present
        with patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', 
                   return_value="X9"),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', 
                   side_effect=self.mock_mCheckConfigOptionAllowCustomVersion),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption',
                  side_effect=self.mock_mCheckConfigOptionExaconfNone),\
            patch('exabox.ovm.sysimghandler.mGetDom0sImagesListSorted', 
                  return_value=["23.1"]):            
            self.assertRaisesRegex(ValueError, 
                f"default_domu_img_version_last_res is required.", 
                hasDomUCustomOS, _ebox_local)

    def test_hasDomUCustomOS_exabox_conf_valid(self):
        _ebox_local = self.mGetClubox()

        # Scenario 06 NO custom version provided, exabox conf missing
        with patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', 
                   return_value="X9"),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', 
                   side_effect=self.mock_mCheckConfigOptionAllowCustomVersion),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption',
                  side_effect=self.mock_mCheckConfigOptionExaconfValid),\
            patch('exabox.ovm.sysimghandler.mGetDom0sImagesListSorted', 
                  return_value=["23.1"]):            
            _img = hasDomUCustomOS(_ebox_local)
            self.assertEqual(_img, "21.1.2.3")
            
                        
    def test_hasDomUCustomOS_negative(self):
        _ebox_local = self.mGetClubox()

        # Scenario 07 NO custom version provided, return None
        with patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', 
                   return_value="X9"),\
            patch('exabox.ovm.sysimghandler.mGetDom0sImagesListSorted', 
                  return_value=["21.2.15"]):
            _img = hasDomUCustomOS(_ebox_local)
            self.assertIsNone(_img)

    def test_mGetSystemImageVersionMap(self):
        _command01 = [
            exaMockCommand("/bin/ls /EXAVMIMAGES " \
                "| /bin/grep 'System.first.boot.*.img$'", aRc=0, aStdout= 
                    "System.first.boot.24.1.0.0.0.240517.1.img\n" \
                    "System.first.boot.24.1.0.0.0.240517.1.kvm.img\n" \
                    "System.first.boot.24.1.0.0.0.240517.1.rtg.img"
                )
        ]
        _command02 = [
            exaMockCommand("/bin/ls /EXAVMIMAGES " \
                "| /bin/grep 'System.first.boot.*.img$'", aRc=0, 
                aStdout="System.first.boot.24.1.0.0.0.240517.1.img")
        ]

        _cmds = {
            self.mGetRegexDom0(aSeqNo="01"): [
                _command01
            ],
            self.mGetRegexDom0(aSeqNo="02"): [
                _command02
            ]
        }

        _expected_map = {
            "scaqab10adm01.us.oracle.com": 
                [
                    "System.first.boot.24.1.0.0.0.240517.1.img",
                    "System.first.boot.24.1.0.0.0.240517.1.kvm.img",
                    "System.first.boot.24.1.0.0.0.240517.1.rtg.img",
                ],
            "scaqab10adm02.us.oracle.com": 
                ["System.first.boot.24.1.0.0.0.240517.1.img"]
        }

        self.mPrepareMockCommands(_cmds)

        _ebox_local = self.mGetClubox()
        _map = mGetSystemImageVersionMap(_ebox_local)
        self.assertEqual(_map, _expected_map)

    def test_mSearchImgInDom0s(self):
        _command01 = [
            exaMockCommand("/bin/ls /EXAVMIMAGES " \
                "| /bin/grep 'System.first.boot.*.img$'", aRc=0, aStdout="/EXAVMIMAGES/System.first.boot.21.2.14.0.0.250706.img\n")
        ]
        _command02 = [
            exaMockCommand("/bin/ls /EXAVMIMAGES " \
                "| /bin/grep 'System.first.boot.*.img$'", aRc=0, aStdout="/EXAVMIMAGES/System.first.boot.22.3.14.0.0.250706.img\n")
        ]

        _cmds = {
            self.mGetRegexDom0(aSeqNo="01"): [
                _command01,
                [
                    exaMockCommand("test.*touch"),
                    exaMockCommand("/sbin/touch /EXAVMIMAGES/System.first.boot.21.2.14.0.0.250706.img"),
                ]
            ],
            self.mGetRegexDom0(aSeqNo="02"): [
                _command02,
                [
                    exaMockCommand("test.*touch"),
                ]
            ],
        }

        _expected_list = [ "scaqab10adm01.us.oracle.com" ]

        self.mPrepareMockCommands(_cmds)

        _ebox_local = self.mGetClubox()
        _list = mSearchImgInDom0s(_ebox_local,"System.first.boot.21.2.14.0.0.250706.img")
        self.assertEqual(_list, _expected_list)

    def test_mCleanOldImgsAndEnsureGivenImgInDom0_no_repo_location(self):
        _loc = "/EXAVMIMAGES/"
        _img = "System.first.boot.20.1.1.0.0."
        _ver = "20.1.1.0.0.200808"
        _imgList = f"{_loc}{_img}.200808.img"\
                   f"{_loc}{_img}.200808.imgBACK"\
                   f"{_loc}{_img}.200722"
        _dom0 = "scaqab10adm01.us.oracle.com"
        _expected_img = "20.1.1.0.0.200808"

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/local/bin/imageinfo -version", aStdout=_ver),
                    exaMockCommand(f"test.*find"),
                    exaMockCommand('/sbin/find /EXAVMIMAGES/ -maxdepth 1 -iname "System.first.boot.*.img" -mtime \+7'),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _ebox_local = self.mGetClubox()
        _rc_status = {_dom0: -1}

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOciExacc', return_value=False), \
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', return_value=None):
            with self.assertRaisesRegex(ExacloudRuntimeError, "Repository download location is None or empty"):
                mCleanOldImgsAndEnsureGivenImgInDom0(
                    _ebox_local,
                    _dom0,
                    _expected_img,
                    _rc_status,
                    False,
                    tuple(),
                    None,
                    {"image/System.first.boot.*": "d2fd86..."})

    def test_mCleanOldImgsAndEnsureGivenImgInDom0_negative(self):
        _loc = "/EXAVMIMAGES/"
        _img = "System.first.boot.20.1.1.0.0."
        _ver = "20.1.1.0.0.200808"
        _imgList = f"{_loc}{_img}.200808.img"\
                   f"{_loc}{_img}.200808.imgBACK"\
                   f"{_loc}{_img}.200722"
        _dom0 = "scaqab10adm01.us.oracle.com"
        _expected_img = "20.1.1.0.0.200722"
        
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    # Param in mCleanOldImgsAndEnsureGivenImgInDom0
                    # when calling cleanup_old_system_boot_files
                    exaMockCommand("/usr/local/bin/imageinfo -version", 
                        aStdout=_ver),
                    exaMockCommand(f"test.*find"),
                ],
                [
                    # cleanup_old_system_boot_files
                    exaMockCommand(f"ls {_loc}System.first.boot.*", 
                        aStdout=_imgList),
                    exaMockCommand(f"rm -rf {_loc}{_img}.200722.*img"),
                    exaMockCommand(f"rm -rf {_loc}{_img}.200722.*bz2"),
                    exaMockCommand(f"rm -rf {_loc}{_img}.200808.*img"),
                    exaMockCommand(f"rm -rf {_loc}{_img}.200808.*bz2"),
                    exaMockCommand(f"test.*find"),
                    exaMockCommand('/sbin/find /EXAVMIMAGES/ -maxdepth 1 -iname "System.first.boot.*.img" -mtime \+7'),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _ebox_local = self.mGetClubox()
        _rc_status={_dom0:-1}        
        
        mCleanOldImgsAndEnsureGivenImgInDom0(
            _ebox_local,
            _dom0,
            _expected_img,
            _rc_status,
            False,
            tuple(),
            "image",
            {"image/System.first.boot.*":"d2fd86..."})
        # Img not found or nor copied
        self.assertEqual(_rc_status[_dom0], 0x0730) 

    def test_mCleanOldImgsAndEnsureGivenImgInDom0_positive(self):
        _loc = "/EXAVMIMAGES/"
        _img = "System.first.boot.20.1.1.0.0."
        _ver = "20.1.1.0.0.200808"
        _imgList = f"{_loc}{_img}.200808.img"\
                   f"{_loc}{_img}.200808.imgBACK"\
                   f"{_loc}{_img}.200722"
        _dom0 = "scaqab10adm01.us.oracle.com"        
        _expected_img = "20.1.1.0.0.200722"
        _expected_file = f"System.first.boot.{_expected_img}.img"

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    # Param in mCleanOldImgsAndEnsureGivenImgInDom0
                    # when calling cleanup_old_system_boot_files
                    exaMockCommand("/usr/local/bin/imageinfo -version",
                        aStdout=_ver),
                    exaMockCommand("ls /EXAVMIMAGES/System.first.boot.*"),
                    exaMockCommand("test.*find"),
                    exaMockCommand('/sbin/find /EXAVMIMAGES/ -maxdepth 1 -iname "System.first.boot.*.img" -mtime \+7', aStdout=_imgList),
                    exaMockCommand(f"rm -rf {_loc}{_img}.200808.*img"),
                    exaMockCommand(f"rm -rf {_loc}{_img}.200808.*bz2"),
                ],
                [
                    # cleanup_old_system_boot_files
                    exaMockCommand(f"ls {_loc}System.first.boot.*", 
                        aStdout=_imgList),
                    exaMockCommand(f"rm -rf {_loc}{_img}.200722.*img"),
                    exaMockCommand(f"rm -rf {_loc}{_img}.200722.*bz2"),
                    exaMockCommand(f"rm -rf {_loc}{_img}.200808.*img"),
                    exaMockCommand(f"rm -rf {_loc}{_img}.200808.*bz2"),
                ],
                [
                    # Test node.mFileExists in copyVMImageVersionToDom0IfMissing
                    exaMockCommand(f"/bin/test -e {_loc}{_expected_file}")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _ebox_local = self.mGetClubox()
        _rc_status={_dom0:-1}        

        mCleanOldImgsAndEnsureGivenImgInDom0(
            _ebox_local,
            _dom0,
            _expected_img,
            _rc_status,
            False,
             tuple(),
            "image",
            {"image/System.first.boot.*":"d2fd86..."})
        # Img file was found or copied
        self.assertNotEqual(_rc_status[_dom0], 0) 

    def test_mVerifyImagesMultiProc_negative(self):
        _loc = "/EXAVMIMAGES/"
        _img = "System.first.boot.20.1.1.0.0."
        _ver = "20.1.1.0.0.200808"
        _imgList = f"{_loc}{_img}.200808.img"\
                   f"{_loc}{_img}.200808.imgBACK"\
                   f"{_loc}{_img}.200722"
        _dom0_01 = "scaqab10adm01.us.oracle.com"
        _dom0_02 = "scaqab10adm02.us.oracle.com"
        _expected_img = "20.1.1.0.0.200722"
        
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    # Param in mCleanOldImgsAndEnsureGivenImgInDom0
                    # when calling cleanup_old_system_boot_files
                    exaMockCommand("/usr/local/bin/imageinfo -version", 
                        aStdout=_ver),
                    exaMockCommand("ls /EXAVMIMAGES/System.first.boot.*"),
                    exaMockCommand(f"test.*find"),
                    exaMockCommand(f"rm -rf {_loc}{_img}.200808.*img"),
                    exaMockCommand(f"rm -rf {_loc}{_img}.200808.*bz2"),
                    exaMockCommand('/sbin/find /EXAVMIMAGES/ -maxdepth 1 -iname "System.first.boot.*.img" -mtime \+7', aStdout=_imgList),
                ],
                [
                    # cleanup_old_system_boot_files
                    exaMockCommand(f"ls {_loc}System.first.boot.*", 
                        aStdout=_imgList),
                    exaMockCommand(f"rm -rf {_loc}{_img}.200722.*img"),
                    exaMockCommand(f"rm -rf {_loc}{_img}.200722.*img"),
                    exaMockCommand(f"rm -rf {_loc}{_img}.200722.*bz2"),
                    exaMockCommand(f"rm -rf {_loc}{_img}.200808.*img"),
                    exaMockCommand(f"rm -rf {_loc}{_img}.200808.*bz2"),
                    exaMockCommand("test.*find"),
                    exaMockCommand('/sbin/find /EXAVMIMAGES/ -maxdepth 1 -iname "System.first.boot.*.img" -mtime \+7', aStdout=_imgList),
                ],
                [
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _ebox_local = self.mGetClubox()
        _exp_status={_dom0_01: 0x0730, _dom0_02: 0x0730}
       
        with patch('exabox.ovm.sysimghandler.mGetLocalFileHash', return_value={"image/System.first.boot.*": "d2fd86..."}):
            _rc_status = mVerifyImagesMultiProc(
                _ebox_local,
                _expected_img)
            # Img not found or nor copied
            self.assertEqual(_rc_status, _exp_status, False) 

    def test_mVerifyImagesMultiProc_no_repo_location(self):
        _expected_img = "20.1.1.0.0.200808"

        _ebox_local = self.mGetClubox()

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOciExacc', return_value=True), \
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', return_value=None):
            with self.assertRaisesRegex(ExacloudRuntimeError, "Repository download location is None or empty"):
                mVerifyImagesMultiProc(_ebox_local, _expected_img)

    def test_getDom0VMImagesInfo(self):
        _loc = "/EXAVMIMAGES/"
        _img = "System.first.boot.20.1.1.0.0"
        _imgList = f"{_loc}{_img}.200808.img\r\n"\
                   f"{_loc}{_img}.200808.imgBACK\r\n"\
                   f"{_loc}{_img}.200722.img\r\n"
        _dom0 = "scaqab10adm01.us.oracle.com"
        
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"ls {_loc}System.first.boot.*", 
                        aRc=0, aStdout=_imgList),
                    exaMockCommand(f"md5sum {_loc}System.first.boot.*", 
                        aRc=0, aStdout="md5_xyz_123", aPersist=True),
                    exaMockCommand(f"sha256sum {_loc}System.first.boot.*", 
                        aRc=0, aStdout="sha256_xyz_123", aPersist=True)
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)
                
        img_info = getDom0VMImagesInfo(
            aDom0 = _dom0,
            aComputeMd5Sum = True,
            aComputeSha256Sum = True)
                
        self.assertIsNotNone(img_info)        
        self.assertEqual(img_info[0]["imgBaseName"],f"{_img}.200808.img")
        self.assertEqual(img_info[0]["imgVersion"],"20.1.1.0.0.200808")
        self.assertFalse(img_info[0]["isKvmImg"])
        self.assertEqual(img_info[0]["md5sum"],"md5_xyz_123")
        self.assertEqual(img_info[0]["sha256sum"],"sha256_xyz_123")

        self.assertEqual(img_info[1]["imgBaseName"],f"{_img}.200722.img")
        self.assertEqual(img_info[1]["imgVersion"],"20.1.1.0.0.200722")
        self.assertFalse(img_info[1]["isKvmImg"])
        self.assertEqual(img_info[1]["md5sum"],"md5_xyz_123")
        self.assertEqual(img_info[1]["sha256sum"],"sha256_xyz_123")

    def test_copyVMImageVersionToDom0IfMissing(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0("02"): [
                [
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System*", aRc=1, aPersist=True),
                    # Adding scp for node.mCopyFile()
                    exaMockCommand("/bin/scp *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/pbunzip2", aRc=0),
                    exaMockCommand("/sbin/pbunzip *", aRc=0),
                    exaMockCommand("/bin/test -e /sbin/touch", aRc=0),
                    exaMockCommand("/sbin/touch System.first.boot.22.1.10.0.0.230422.img", aRc=0),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _img_name = "System.first.boot.22.1.10.0.0.230422.img"
        _files = [f"{_img_name}.bz2"]
        with patch('os.listdir', return_value = _files),\
            patch('os.path.isfile', return_value = True), \
            patch('exabox.core.Node.exaBoxNode.mCompareFiles', return_value=True):
            remoteImgFound, imgInfo, imgCopied = copyVMImageVersionToDom0IfMissing("scaqab10adm02.us.oracle.com","22.1.10.0.0.230422",False, None, {"image/System.first.boot.*":"d2fd86..."})
            self.assertFalse(remoteImgFound)
            self.assertIsNotNone(imgInfo)
            self.assertTrue(imgCopied)

    def test_copyVMImageVersionToDom0IfMissing_001_RTG_is_found(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0("01"): [
                [
                    # Next command will simulate the RTG file DOES EXIST (1st attempt to search)
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.rtg.img", aRc=0),
                    exaMockCommand("/bin/test -e /sbin/touch", aRc=0),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _img_name = "System.first.boot.24.1.2.0.0.240812.img"
        _files = [f"{_img_name}.bz2"]
        _imgInfo = {
         "filePath": "/EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.rtg.img",
         "fileBaseName": "System.first.boot.24.1.2.0.0.240812.rtg.img",
         "imgBaseName": "System.first.boot.24.1.2.0.0.240812.rtg.img",
         "imgArchiveBaseName": "System.first.boot.24.1.2.0.0.240812.rtg.img.bz2",
         "imgVersion": "24.1.2.0.0.240812",
         "isKvmImg": False,
         "isRtgImg": True,
         "isArchive": False
        }
        with patch('exabox.core.Context.GlobalContext.mGetConfigOptions',              
                   side_effect=self.mock_mGetConfigOptionsRTG),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', 
                   return_value=True, aPersist=True):
            (remoteImgFoundInDom0, imgInfo, imgCopied) = copyVMImageVersionToDom0IfMissing("scaqab10adm01.us.oracle.com","24.1.2.0.0.240812",True,None)
            self.assertTrue(remoteImgFoundInDom0)
            self.assertEqual(imgInfo, _imgInfo)
            self.assertFalse(imgCopied)

    def test_copyVMImageVersionToDom0IfMissing_002_RTG_fallback_to_NONRTG(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0("01"): [
                [                    
                    # Next command will simulate the RTG file DOES NOT exist (1st attempt to search)
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.rtg.img", aRc=1), 
                    # Next command will simulate the NON_RTG file DOES NOT exist (2nd attempt to search)
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.kvm.img", aRc=1), 
                    # Next command will simulate the NON_RTG file DOES EXIST (3rd attempt to search)
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img", aRc=0), 

                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _img_name = "System.first.boot.24.1.2.0.0.240812.img"
        _files = [f"{_img_name}.bz2"]
        _imgInfo = {
         "filePath": "/EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img",
         "fileBaseName": "System.first.boot.24.1.2.0.0.240812.img",
         "imgBaseName": "System.first.boot.24.1.2.0.0.240812.img",
         "imgArchiveBaseName": "System.first.boot.24.1.2.0.0.240812.img.bz2",
         "imgVersion": "24.1.2.0.0.240812",
         "isKvmImg": False,
         "isRtgImg": False,
         "isArchive": False
        }
        with patch('exabox.core.Context.GlobalContext.mGetConfigOptions', 
                   side_effect=self.mock_mGetConfigOptionsRTG),\
             patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', 
                   return_value=True, aPersist=True):
            (remoteImgFoundInDom0, imgInfo, imgCopied) = copyVMImageVersionToDom0IfMissing("scaqab10adm01.us.oracle.com","24.1.2.0.0.240812",True,None)
            self.assertTrue(remoteImgFoundInDom0)
            self.assertEqual(imgInfo, _imgInfo)
            self.assertFalse(imgCopied)    

    def test_copyVMImageVersionToDom0IfMissing_003_RTG_in_local_only(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0("01"): [
                [                    
                    # Next command will simulate the RTG file DOES NOT exist (1st attempt to search)
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.rtg.img", aRc=1), 
                    # Next command will simulate the NON_RTG file DOES NOT exist (2nd attempt to search)
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.kvm.img", aRc=1), 
                    # Next command will simulate the NON_RTG file DOES NOT EXIST (3rd attempt to search)
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img", aRc=1), 
                    # Next command will simulate the BZ2 file EXIST in Local and will be copied
                    exaMockCommand("/bin/scp *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/pbunzip2", aRc=0),
                    exaMockCommand("/bin/test -e /sbin/touch", aRc=0),
                    exaMockCommand("touch /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img", aRc=0),
                    exaMockCommand("/sbin/pbunzip2 *", aRc=0), 
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.rtg.img.bz2", aRc=0), 
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img", aRc=0), 
                    exaMockCommand("sha256sum /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.rtg.img.bz2", aRc=0, aStdout="SOMEHASH SOMEFILE"), 
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # We are simulating RTG file will exist in Local Repo
        _img_name = "System.first.boot.24.1.2.0.0.240812.rtg.img"
        _files = [f"{_img_name}.bz2"]
        with patch('os.listdir', return_value = _files),\
            patch('os.path.isfile', return_value = True),\
            patch('exabox.core.Context.GlobalContext.mGetConfigOptions', 
                   side_effect=self.mock_mGetConfigOptionsRTG),\
            patch('exabox.core.Node.exaBoxNode.mCompareFiles',
                   return_value = True),\
            patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', 
                   return_value=True, aPersist=True), \
             patch('exabox.ovm.sysimghandler.mGetVMImageArchiveInfoInLocalRepo', return_value={
                 'filePath': '/EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.rtg.img.bz2',
                 'fileBaseName': 'System.first.boot.24.1.2.0.0.240812.rtg.img.bz2',
                 'imgBaseName': 'System.first.boot.24.1.2.0.0.240812.rtg.img',
                 'imgArchiveBaseName': 'System.first.boot.24.1.2.0.0.240812.rtg.img.bz2',
                 'imgVersion': '24.1.2.0.0.240812',
                 'isKvmImg': False,
                 'isRtgImg': True,
                 'isArchive': True
             }):
            (remoteImgFoundInDom0, imgInfo, imgCopied) = copyVMImageVersionToDom0IfMissing(
                aDom0="scaqab10adm01.us.oracle.com",
                aVersion="24.1.2.0.0.240812",
                aIsKvm=True,
                aImageBaseLocation=None,
                aLocalFileHash={"image/System.first.boot.*":"d2fd86..."})
            self.assertFalse(remoteImgFoundInDom0)
            self.assertIsNotNone(imgInfo)
            self.assertTrue(imgCopied)

    def test_copyVMImageVersionToDom0IfMissing_004_RTG_in_local_only_fallback_NONRTG(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0("01"): [
                [                    
                    exaMockCommand("/bin/ls /EXAVMIMAGES/*", aStdout="System.first.boot.24.1.2.0.0.240812.rtg.img", aPersist=True),
                    # Next command will simulate the RTG file DOES NOT exist (1st attempt to search)
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.rtg.img", aRc=1), 
                    # Next command will simulate the NON_RTG file DOES NOT exist (2nd attempt to search)
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.kvm.img", aRc=1), 
                    # Next command will simulate the NON_RTG file DOES NOT EXIST (3rd attempt to search)
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img", aRc=1), 
                    # Next command will simulate the BZ2 file EXIST in Local and will be copied
                    exaMockCommand("/bin/scp *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/pbunzip2", aRc=0),
                    exaMockCommand("/sbin/pbunzip2 *", aRc=0), 
                    exaMockCommand("/bin/test -e /sbin/touch", aRc=0),
                    exaMockCommand("touch /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img", aRc=0),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img", aRc=0), 
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img.bz2", aRc=0), 
                    exaMockCommand("/bin/mv /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.kvm.img *", aRc=0)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # We are simulating RTG file will exist in Local Repo
        _img_name = "System.first.boot.24.1.2.0.0.240812.kvm.img"
        _files = [f"{_img_name}.bz2"]
        with patch('os.listdir', return_value=_files),\
            patch('os.path.isfile', return_value=True),\
            patch('exabox.core.Context.GlobalContext.mGetConfigOptions', 
                side_effect=self.mock_mGetConfigOptionsRTG),\
            patch('exabox.core.Node.exaBoxNode.mCompareFiles', return_value=True),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True, aPersist=True),\
            patch('exabox.ovm.sysimghandler.mGetVMImageArchiveInfoInLocalRepo', return_value={
                'filePath': '/EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.kvm.img.bz2',
                'fileBaseName': 'System.first.boot.24.1.2.0.0.240812.kvm.img.bz2',
                'imgBaseName': 'System.first.boot.24.1.2.0.0.240812.kvm.img',
                'imgArchiveBaseName': 'System.first.boot.24.1.2.0.0.240812.kvm.img.bz2',
                'imgVersion': '24.1.2.0.0.240812',
                'isKvmImg': True,
                'isRtgImg': False,
                'isArchive': True
            }):
            (remoteImgFoundInDom0, imgInfo, imgCopied) = copyVMImageVersionToDom0IfMissing(
                aDom0="scaqab10adm01.us.oracle.com",
                aVersion="24.1.2.0.0.240812",
                aIsKvm=True,
                aImageBaseLocation=None,
                aLocalFileHash={"image/System.first.boot.24.1.2.0.0.240812.kvm.img":"d2fd86..."})
            self.assertFalse(remoteImgFoundInDom0)
            self.assertIsNotNone(imgInfo)  # This should now pass
            self.assertTrue(imgCopied)

    def test_mIsRtgImgPresent_LocalOnly(self):

        _command01 = [
            exaMockCommand("/bin/ls /EXAVMIMAGES " \
                "| /bin/grep 'System.first.boot.*.img$'", 
                aRc=0, aStdout="System.first.boot.23.1.0.0.0.img")
        ]
        _command02 = [
            exaMockCommand("/bin/ls /EXAVMIMAGES " \
                "| /bin/grep 'System.first.boot.*.img$'", 
                aRc=0, aStdout="System.first.boot.25.1.0.0.0.rtg.img")
        ]

        _cmds = {
            self.mGetRegexDom0(aSeqNo="01"): [
                _command01
            ],
            self.mGetRegexDom0(aSeqNo="02"): [
                _command02
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _expected_tuple = False, True

        _ebox_local = self.mGetClubox()

        # This tests __getVMImagesInRepo() internally
        _img_name = "System.first.boot.24.1.0.0.0.rtg.img"
        _files = [f"{_img_name}.bz2"]
        with patch('os.listdir', return_value = _files),\
            patch('os.path.isfile', return_value = True):
            _tuple = mIsRtgImgPresent(_ebox_local,"24.1.0.0.0")
            self.assertEqual(_tuple, _expected_tuple)

    def test_mIsRtgImgPresent_Dom0Only(self):

        _command01 = [
            exaMockCommand("/bin/ls /EXAVMIMAGES " \
                "| /bin/grep 'System.first.boot.*.img$'", 
                aRc=0, aStdout="System.first.boot.24.1.0.0.0.rtg.img")
        ]
        _command02 = [
            exaMockCommand("/bin/ls /EXAVMIMAGES " \
                "| /bin/grep 'System.first.boot.*.img$'", 
                aRc=0, aStdout="System.first.boot.23.1.0.0.0.img")
        ]

        _cmds = {
            self.mGetRegexDom0(aSeqNo="01"): [
                _command01
            ],
            self.mGetRegexDom0(aSeqNo="02"): [
                _command02
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _expected_tuple = True, False

        _ebox_local = self.mGetClubox()

        # This tests __getVMImagesInRepo() internally
        _img_name = "System.first.boot.24.1.0.0.0.img"
        _files = [f"{_img_name}.bz2"]
        with patch('os.listdir', return_value = _files),\
            patch('os.path.isfile', return_value = True):
            _tuple = mIsRtgImgPresent(_ebox_local,"24.1.0.0.0")
            self.assertEqual(_tuple, _expected_tuple)            

    def test_mIsRtgImgPresent_Negative(self):
        # In this test, we want to verify that exacloud is able to 
        # FIND the RTG images for the GIVEN version. 
        # In other words, even if other RTG images files are present, 
        # exacloud NEEDs to match the version as well.
        _command01 = [
            # Dom0 MAY have other RTG's 
            exaMockCommand("/bin/ls /EXAVMIMAGES " \
                "| /bin/grep 'System.first.boot.*.img$'", 
                aRc=0, aStdout="System.first.boot.24.1.1.0.0.rtg.img\n" \
                    "System.first.boot.24.1.2.0.0.rtg.img")
        ]
        _command02 = [
            exaMockCommand("/bin/ls /EXAVMIMAGES " \
                "| /bin/grep 'System.first.boot.*.img$'", 
                aRc=0, aStdout="System.first.boot.23.1.0.0.0.img\n"
                    "System.first.boot.24.1.2.0.0.rtg.img")
        ]

        _cmds = {
            self.mGetRegexDom0(aSeqNo="01"): [
                _command01
            ],
            self.mGetRegexDom0(aSeqNo="02"): [
                _command02
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _expected_tuple = False, False

        _ebox_local = self.mGetClubox()

        # This tests __getVMImagesInRepo() internally
        _img_name = "System.first.boot.24.1.0.0.0.img"
        _files = [f"{_img_name}.bz2"]
        with patch('os.listdir', return_value = _files),\
            patch('os.path.isfile', return_value = True):
            _tuple = mIsRtgImgPresent(_ebox_local,"24.1.0.0.0")
            self.assertEqual(_tuple, _expected_tuple)          

    @patch('exabox.core.Node.exaBoxNode')
    def test_mUnmountImageLVM_Failure(self, mock_exaBoxNode):

        mock_node = mock_exaBoxNode.return_value
        mock_node.mExecuteCmd.side_effect = [(io.StringIO(""), io.StringIO("/EXAVMIMAGES/GuestImages/host-name1234.oracle.internal.oraclevcn.com/u02_extra.img"), io.StringIO("")),
                                             (io.StringIO(""), io.StringIO(""), io.StringIO("")),
                                             (io.StringIO(""), io.StringIO(""), io.StringIO("")),
                                             (io.StringIO(""), io.StringIO(""), io.StringIO("")),
                                             (io.StringIO(""), io.StringIO(""), io.StringIO("")),
                                             (io.StringIO(""), io.StringIO("'loop deleted : /dev/loop112400\n', 'losetup: /EXAVMIMAGES/GuestImages/host-name1234.oracle.internal.oraclevcn.com/u02_extra.img: detach failed: Inappropriate ioctl for device\n'"), io.StringIO("")),
                                             (io.StringIO(""), io.StringIO(""), io.StringIO(""))
                                            ]
        mock_node.mGetCmdExitStatus.side_effect = [0, 5, 0, 5, 0, 1, 0]

        _ebox_local = self.mGetClubox()
        _path = "/EXAVMIMAGES/GuestImages/host-name1234.oracle.internal.oraclevcn.com/u02_extra.img"
        mUnmountImageLVM(_ebox_local, mock_node, _path)

        mock_node.mExecuteCmd.assert_called()
        mock_node.mGetCmdExitStatus.assert_called() 

    @patch('exabox.core.Node.exaBoxNode')
    def test_mUnmountImageLVM_Success(self, mock_exaBoxNode):

        mock_node = mock_exaBoxNode.return_value
        mock_node.mExecuteCmd.side_effect = [(io.StringIO(""), io.StringIO("/EXAVMIMAGES/GuestImages/host-name1234.oracle.internal.oraclevcn.com/u02_extra.img"), io.StringIO("")),
                                             (io.StringIO(""), io.StringIO(""), io.StringIO("")),
                                             (io.StringIO(""), io.StringIO(""), io.StringIO("")),
                                             (io.StringIO(""), io.StringIO(""), io.StringIO("")),
                                             (io.StringIO(""), io.StringIO(""), io.StringIO("")),
                                             (io.StringIO(""), io.StringIO("'loop deleted : /dev/loop112400\n', 'losetup: /EXAVMIMAGES/GuestImages/host-name1234.oracle.internal.oraclevcn.com/u02_extra.img: detach failed: Inappropriate ioctl for device\n'"), io.StringIO("")),
                                             (io.StringIO(""), io.StringIO(""), io.StringIO(""))
                                            ]
        mock_node.mGetCmdExitStatus.return_value = 0

        _ebox_local = self.mGetClubox()
        _path = "/EXAVMIMAGES/GuestImages/host-name1234.oracle.internal.oraclevcn.com/u02_extra.img"
        mUnmountImageLVM(_ebox_local, mock_node, _path)

        mock_node.mExecuteCmd.assert_called()
        mock_node.mGetCmdExitStatus.assert_called()

    def test_mGetVMImageArchiveInfoInRepo_RTG_ExactMatch(self):
        with patch('exabox.ovm.sysimghandler.getVMImageArchiveInRepo') as mock_get_archive:
            mock_get_archive.side_effect = [
                {'isArchive': True, 'imgVersion': '24.1.0.0.0', 'isKvmImg': False, 'isRtgImg': True, 'filePath': 'image/System.first.boot.24.1.0.0.0.rtg.img.bz2'},
                None,
                None
            ]
            result = mGetVMImageArchiveInfoInLocalRepo('24.1.0.0.0', 'image')
            self.assertIsNotNone(result)
            self.assertTrue(result['isRtgImg'])
            self.assertFalse(result['isKvmImg'])
            self.assertEqual(result['filePath'], 'image/System.first.boot.24.1.0.0.0.rtg.img.bz2')

    def test_mGetVMImageArchiveInfoInRepo_RTG_Fallback_NonRTG(self):
        with patch('exabox.ovm.sysimghandler.getVMImageArchiveInRepo') as mock_get_archive:
            mock_get_archive.side_effect = [
                None,
                {'isArchive': True, 'imgVersion': '24.1.0.0.0', 'isKvmImg': True, 'isRtgImg': False, 'filePath': 'image/System.first.boot.24.1.0.0.0.kvm.img.bz2'},
                None
            ]
            result = mGetVMImageArchiveInfoInLocalRepo('24.1.0.0.0', 'image')
            self.assertIsNotNone(result)
            self.assertFalse(result['isRtgImg'])
            self.assertTrue(result['isKvmImg'])
            self.assertEqual(result['filePath'], 'image/System.first.boot.24.1.0.0.0.kvm.img.bz2')

    def test_mGetVMImageArchiveInfoInRepo_RTG_Fallback_NonKVM_NonRTG(self):
        with patch('exabox.ovm.sysimghandler.getVMImageArchiveInRepo') as mock_get_archive, \
             patch('exabox.ovm.sysimghandler.mIsRtgImg', return_value=False):
            
            mock_get_archive.side_effect = [
                None,
                {'isArchive': True, 'imgVersion': '24.1.0.0.0', 'isKvmImg': False, 'isRtgImg': False, 'filePath': 'image/System.first.boot.24.1.0.0.0.img.bz2'}
            ]
            result = mGetVMImageArchiveInfoInLocalRepo('24.1.0.0.0', 'image')
            self.assertIsNotNone(result)
            self.assertFalse(result['isRtgImg'])
            self.assertFalse(result['isKvmImg'])
            self.assertEqual(result['filePath'], 'image/System.first.boot.24.1.0.0.0.img.bz2')

    def test_mGetVMImageArchiveInfoInRepo_NoMatch(self):
        with patch('exabox.ovm.sysimghandler.getVMImageArchiveInRepo') as mock_get_archive:
            mock_get_archive.return_value = None
            result = mGetVMImageArchiveInfoInLocalRepo('24.1.0.0.0', 'image')
            self.assertIsNone(result)

    def test_mGetVMImageArchiveInfoInRepo_EmptyVersion(self):
        version = ''
        with self.assertRaises(ValueError):
            mGetVMImageArchiveInfoInLocalRepo(version, 'image')

    def test_mGetLocalFileHash(self):
        """
        Test mGetLocalFileHash for calculating SHA256 checksum of local VM image file.
        """
        with patch('os.path.exists') as mock_exists, \
             patch('exabox.core.Node.exaBoxNode.mExecuteLocal') as mock_execute, \
             patch('exabox.core.Node.exaBoxNode.mDisconnect') as mock_disconnect:
            # Typical case: successful checksum calculation
            mock_exists.return_value = True
            mock_execute.return_value = (0, None, b'd2fd86...  image/System.first.boot.24.1.2.0.0.240812.img\n', b'')
            result = mGetLocalFileHash('image/System.first.boot.24.1.2.0.0.240812.img')
            self.assertIsNotNone(result)
            self.assertEqual(result, {"image/System.first.boot.24.1.2.0.0.240812.img": "d2fd86..."})

            # Edge case: file does not exist
            mock_exists.return_value = False
            result = mGetLocalFileHash('image/System.first.boot.24.1.2.0.0.240812.img')
            self.assertIsNone(result)

            # Edge case: sha256sum command fails
            mock_exists.return_value = True
            mock_execute.return_value = (1, None, b'', b'error message')
            result = mGetLocalFileHash('image/System.first.boot.24.1.2.0.0.240812.img')
            self.assertIsNone(result)

            # Edge case: sha256sum produces no output
            mock_execute.return_value = (0, None, b'', b'')
            result = mGetLocalFileHash('image/System.first.boot.24.1.2.0.0.240812.img')
            self.assertIsNone(result)


    def test_mCompareFiles_TypicalMatch(self):
        _dom0 = "scaqab10adm01.us.oracle.com"
        _local_file = "image/System.first.boot.24.1.2.0.0.240812.img"
        _remote_file = "/EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img"
        _hash_value = "d2fd86abc..."
        
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/bin/test -e {_remote_file}", aRc=0, aStdout=""),
                    exaMockCommand(f"/bin/test -e /bin/sha256sum", aRc=0, aStdout=""),
                    exaMockCommand(f"sha256sum {_remote_file}", aRc=0, aStdout=f"{_hash_value}  {_remote_file}")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        
        node = exaBoxNode(get_gcontext())
        node.mConnect(aHost=_dom0)
        
        with patch('os.path.exists', return_value=True), \
             patch('exabox.core.Node.exaBoxNode.mExecuteLocal', return_value=(0, None, f"{_hash_value}  {_local_file}\n".encode(), b'')):
            result = node.mCompareFiles(_local_file, _remote_file, {})
            self.assertTrue(result)

    def test_mCompareFiles_TypicalMismatch(self):
        _dom0 = "scaqab10adm01.us.oracle.com"
        _local_file = "image/System.first.boot.24.1.2.0.0.240812.img"
        _remote_file = "/EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img"
        _local_hash = "d2fd86abc..."
        _remote_hash = "different_hash..."
        
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/bin/test -e {_remote_file}", aRc=0, aStdout=""),
                    exaMockCommand(f"/bin/test -e /bin/sha256sum", aRc=0, aStdout=""),
                    exaMockCommand(f"sha256sum {_remote_file}", aRc=0, aStdout=f"{_remote_hash}  {_remote_file}")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        
        node = exaBoxNode(get_gcontext())
        node.mConnect(aHost=_dom0)
        
        with patch('os.path.exists', return_value=True), \
             patch('exabox.core.Node.exaBoxNode.mExecuteLocal', return_value=(0, None, f"{_local_hash}  {_local_file}\n".encode(), b'')):
            result = node.mCompareFiles(_local_file, _remote_file, {})
            self.assertFalse(result)

    def test_mCompareFiles_LocalFileNotExists(self):
        _dom0 = "scaqab10adm01.us.oracle.com"
        _local_file = "image/System.first.boot.24.1.2.0.0.240812.img"
        _remote_file = "/EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img"
        
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/bin/test -e {_remote_file}", aRc=0, aStdout=""),
                    exaMockCommand(f"/bin/test -e /bin/sha256sum", aRc=0, aStdout="")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        
        node = exaBoxNode(get_gcontext())
        node.mConnect(aHost=_dom0)
        
        with patch('os.path.exists', return_value=False):
            result = node.mCompareFiles(_local_file, _remote_file, {})
            self.assertFalse(result)

    def test_mCompareFiles_RemoteFileNotExists(self):
        _dom0 = "scaqab10adm01.us.oracle.com"
        _local_file = "image/System.first.boot.24.1.2.0.0.240812.img"
        _remote_file = "/EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img"
        
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/bin/test -e {_remote_file}", aRc=1, aStdout="")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        
        node = exaBoxNode(get_gcontext())
        node.mConnect(aHost=_dom0)
        
        with patch('os.path.exists', return_value=True):
            result = node.mCompareFiles(_local_file, _remote_file, {})
            self.assertFalse(result)

    def test_mGetRemoteFileCksum_TypicalSuccess(self):
        _dom0 = "scaqab10adm01.us.oracle.com"
        _remote_file = "/EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img"
        _hash_value = "d2fd86abc..."
        
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/bin/test -e {_remote_file}", aRc=0, aStdout=""),
                    exaMockCommand(f"/bin/test -e /bin/sha256sum", aRc=0, aStdout=""),
                    exaMockCommand(f"/bin/test -e /usr/bin/sha256sum", aRc=1, aStdout=""),
                    exaMockCommand(f"sha256sum {_remote_file}", aRc=0, aStdout=f"{_hash_value}  {_remote_file}")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        
        node = exaBoxNode(get_gcontext())
        node.mConnect(aHost=_dom0)
        
        result = node.mGetRemoteFileCksum(_remote_file)
        self.assertEqual(result, _hash_value)

    def test_mGetRemoteFileCksum_FileNotExists(self):
        _dom0 = "scaqab10adm01.us.oracle.com"
        _remote_file = "/EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img"
        
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/bin/test -e {_remote_file}", aRc=1, aStdout="")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        
        node = exaBoxNode(get_gcontext())
        node.mConnect(aHost=_dom0)
        
        result = node.mGetRemoteFileCksum(_remote_file)
        self.assertIsNone(result)

    def test_mGetRemoteFileCksum_CommandFails(self):
        _dom0 = "scaqab10adm01.us.oracle.com"
        _remote_file = "/EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img"
        
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/bin/test -e {_remote_file}", aRc=0, aStdout=""),
                    exaMockCommand(f"/bin/test -e /bin/sha256sum", aRc=0, aStdout=""),
                    exaMockCommand(f"/bin/test -e /usr/bin/sha256sum", aRc=1, aStdout=""),
                    exaMockCommand(f"sha256sum {_remote_file}", aRc=1, aStdout="", aStderr="Error executing sha256sum")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        
        node = exaBoxNode(get_gcontext())
        node.mConnect(aHost=_dom0)
        
        result = node.mGetRemoteFileCksum(_remote_file)
        self.assertIsNone(result)

    def test_mGetLocalFileCksum_TypicalSuccess(self):
        _local_file = "image/System.first.boot.24.1.2.0.0.240812.img"
        _hash_value = "d2fd86abc..."
        
        node = exaBoxNode(get_gcontext())
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('exabox.core.Node.exaBoxNode.mExecuteLocal', return_value=(0, None, f"{_hash_value}  {_local_file}\n".encode(), b'')):
            result = node.mGetLocalFileCksum(_local_file)
            self.assertEqual(result, _hash_value)

    def test_mGetLocalFileCksum_FileNotExists(self):
        _local_file = "image/System.first.boot.24.1.2.0.0.240812.img"
        
        node = exaBoxNode(get_gcontext())
        
        with patch('os.path.exists', return_value=False):
            result = node.mGetLocalFileCksum(_local_file)
            self.assertIsNone(result)

    def test_mGetLocalFileCksum_CommandFails(self):
        _local_file = "image/System.first.boot.24.1.2.0.0.240812.img"
        
        node = exaBoxNode(get_gcontext())
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('exabox.core.Node.exaBoxNode.mExecuteLocal', return_value=(1, None, b'', b'error message')):
            result = node.mGetLocalFileCksum(_local_file)
            self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
