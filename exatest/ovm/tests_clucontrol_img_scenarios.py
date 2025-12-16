#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_clucontrol_img_scenarios.py /main/7 2025/12/01 22:37:00 avimonda Exp $
#
# tests_clucontrol_img_scenarios.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_clucontrol_img_scenarios.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    avimonda    11/06/25 - Bug 38427813 - OCI: EXACS: PROVISIONING FAILED WITH
#                           EXACLOUD ERROR CODE: 1877 EXACLOUD : ERROR IN
#                           MULTIPROCESSING(NON-ZERO EXITCODE(-9) RETURNED
#                           <PROCESSSTRUCTURE(<DOM0 NODE>, STOPPED[SIGKILL])>,
#                           ID: <DOM0 NODE>, START_TIME: <T1>, END_TIME: <T2>,
#                           MAX_TIME
#    gparada     06/02/25 - 37963204 Fix for System Image in hybrid infra
#    gparada     09/18/24 - 37022415 Validate scenarios to handle System first
#                           boot image for NON-RTG and RTG
#    gparada     09/18/24 - Creation
#
import os
import unittest
import xml.etree.ElementTree as ET

from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo, ebLogError

from unittest.mock import patch
from typing import List, Dict

class ebTestSystemFirstBootScenarios(ebTestClucontrol):
    """
    UNIT TESTS FOR mCheckSystemImage AS DEFINED IN
    RTG System Image Provisioning Testing

    https://confluence.oraclecorp.com/confluence/display/EDCS/
    RTG+System+Image+Provisioning+Testing

    Overall sequence of calls (to understand patch and mocking below):
    mCheckSystemImage is the MAIN function
        mGetDom0sImagesListSorted
            mGetImageVersion
            mReturnDom0DomUPair
        mCheckDomUImageFor23ai
        formatVMImageBaseName
        mSearchImgInDom0s
            mGetSystemImageVersionMap
        mCopySystemImgLocalToDOM0
            mReturnAllClusterHosts
            mGetImageFromDom0ToLocal
            mVerifyImagesMultiProc
                mCleanOldImgsAndEnsureGivenImgInDom0
                    ebCluPreChecks
                    cleanup_old_system_boot_files
                    copyVMImageVersionToDom0IfMissing
                        mExecuteCmdLog
        mSetImageVersionProperty
        mGetImageFromDom0ToLocal
            mIsRtgImg
            formatVMImageBaseName
            mCopy2Local
        mGetImageFromOSSToLocal
            mIsRtgImg
            formatVMImageBaseName
        mVerifyImagesMultiProc
            mCleanOldImgsAndEnsureGivenImgInDom0
                ebCluPreChecks
                cleanup_old_system_boot_files
                copyVMImageVersionToDom0IfMissing
                    mExecuteCmdLog
        mReturnDom0DomUPair
        mSaveXMLClusterConfiguration

    """
    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)

    def mSetExaboxMock(self, aDict):
        self.exabox_conf = aDict
        
        # Capture the original os.path.exists function (used in a mock below)
        self.original_os_path_exists = os.path.exists

    def mock_mGetConfigOptionsRTG(self):
        # _config_opts = get_gcontext().mGetConfigOptions()        
        _config_opts = {}
        _config_opts["rtg_enabled_exacc"] = "True"
        _config_opts["rtg_enabled_exadbxs"] = "True"
        _config_opts["rtg_enabled_exacs"] = "True"        
        return _config_opts

    # Mock functions
    def mock_exabox_conf(self, aDict, aKey):
        if (aKey in aDict):
            return aDict[aKey]

    def mock_mCheckConfigOption(self, aOption, aValue=None):
        if aValue:
            return self.mock_exabox_conf(self.exabox_conf,aOption) == aValue
        else:
            return self.mock_exabox_conf(self.exabox_conf,aOption)
    
    def mCheckOedaProperties(self):
        _oeda_path  = self.mGetClubox().mGetOedaPath()
        ebLogInfo(f"_oeda_path: {_oeda_path}")
        _path = _oeda_path + '/properties/es.properties'
        # if not os.path.exists(_path):
        #     os.makedirs(_path)

    def mock_localimageBz2File(self, file:str):
        self.localimageBz2File = file

    def mCheckLocalSystemExists(self, path):
        imageBz2File = f'images/{self.localimageBz2File}' 
        if path == imageBz2File: 
            return True
        return self.original_os_path_exists(path)

    def mListDirLocal(self, path:str):        
        if path == "images/":
            return [f'{self.localimageBz2File}']
        return []

    def mCheckSystemImage_test_wrapper(
            self,            
            aCustomVersion:str,
            aDom0ImagesMap:Dict,
            aInfraOS:List
        ):
        """
        This is MAIN wrapper function, so mCheckSystemImage() can be tested
        according to the variables from the confluence page.
        Arguments:
            aInfraOS expected values: 
                '23.1', '24.1'
            aCustomVersion expected values: 
                '22.1.17.0.0.240306', '23.1.17.0.0.240807', '24.1.3.0.0.240910'
        """        
        _ebox_local = self.mGetClubox()
        _img = ''
        
        self.mCheckOedaProperties()        

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetVersionGi', 
                  return_value="191"),\
            patch('exabox.ovm.sysimghandler.mGetSystemImageVersionMap', 
                  return_value=aDom0ImagesMap),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetImageVersion', 
                return_value=""),\
            patch("exabox.ovm.sysimghandler.ebCluPreChecks.cleanup_old_system_boot_files"),\
            patch('exabox.ovm.clucontrol.mGetDom0sImagesListSorted', 
                  return_value=aInfraOS),\
            patch('os.path.isdir'),\
            patch('os.listdir', 
                  side_effect=self.mListDirLocal),\
            patch('os.path.isfile'),\
            patch('os.path.exists', 
                  side_effect=self.mCheckLocalSystemExists),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', 
                  side_effect=self.mock_mCheckConfigOption),\
            patch('exabox.ovm.sysimghandler.mGetLocalFileHash', return_value={'System.first.boot.22.1.10.0.0.230422.img':'d2fd86...'}), \
            patch('exabox.core.Context.GlobalContext.mGetConfigOptions',
                  side_effect=self.mock_mGetConfigOptionsRTG),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', 
                   return_value=True, aPersist=True):
            
            _img = _ebox_local.mCheckSystemImage(aCustomVersion)            

        _xmlPath = _ebox_local.mGetPatchConfig()
        ebLogInfo(f"_img: {_img} _xmlPath: {_xmlPath}")

        return _img, _xmlPath
        
    # ROW NN
    # IN  Infra                         = OL8/23.1.2.0.0.230523
    # IN  allow_domu_custom_version     = False
    # IN  default_domu_img_version      = Empty
    # IN  default_domu_version_last_res = Empty
    # IN  Image in Dom0-1 (NON-RTG) System.first.boot.23.1.2.0.0.230523.img
    # IN  Image in Dom0-2 (NON-RTG) System.first.boot.23.1.2.0.0.230523.img
    # IN  Image in Local  (NON-RTG) System.first.boot.23.1.2.0.0.230523.img.bz2
    # OUT Expectation     (NON-RTG)     = 23.1.2.0.0.230523
    def test_mCheckSystemImage_01_backwards_compatibility(self):        

        # _infra should have the NUMERIC VERSION of each Dom0 in ASC order
        _infra = ['23.1.2.0.0.230523','23.1.2.0.0.230523'] 
        
        # _flags will mock the "used" properties from exabox.conf in this flow
        _flags = {            
            'allow_domu_custom_version': 'False',
            'default_domu_img_version': '',
            'default_domu_img_version_last_res': '',
        }
        
        # _imageMap will mock the list of System Image files for each Dom0
        _imageMap =     {
            "scaqab10adm01.us.oracle.com" :
                [
                    '/EXAVMIMAGES/System.first.boot.22.1.10.0.0.230527.img', 
                    '/EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.img'
                ],
            "scaqab10adm02.us.oracle.com" : 
                [
                    '/EXAVMIMAGES/System.first.boot.22.1.10.0.0.230527.img', 
                    '/EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.img'
                ]
        }

        _cmds = {
            self.mGetRegexLocal():
            [
                [   # clucontrol mSetImageVersionProperty
                    exaMockCommand("/bin/sed -i *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/sed -r *", aRc=0, aStdout="", aPersist=True),

                    # clucontrol mCheckSystemImage /bin/mkdir -p * opt/oeda/linux-x64/exacloud.conf
                    exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="", aPersist=True),

                    # # clucontrol mCheckSystemImage /bin/scp */config/uuid.xml */opt/oeda/linux-x64/exacloud.conf/uuid.xml
                    exaMockCommand("/bin/scp *", aRc=0, aStdout="", aPersist=True),
                ]
            ],            
            self.mGetRegexDom0("01"): [
                [   # sysimghandler copyVMImageVersionToDom0IfMissing
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.img", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.kvm.img", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("/bin/mv /EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.kvm.img /EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.img", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("test.*touch", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("/sbin/touch /EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.img", aRc=0, aStdout="" ,aPersist=True),
                ],
                [
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.kvm.img"),
                    exaMockCommand("mv /EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.kvm.img /EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.img"),
                ]
            ],
            self.mGetRegexDom0("02"): [
                [   # sysimghandler copyVMImageVersionToDom0IfMissing
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.img", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.kvm.img", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("/bin/mv /EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.kvm.img /EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.img", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("test.*touch", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("/sbin/touch /EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.img", aRc=0, aStdout="" ,aPersist=True),
                ],
                [
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.kvm.img"),
                    exaMockCommand("mv /EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.kvm.img /EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.img"),
                ]
            ]

        }
        
        self.mSetExaboxMock(_flags)
        
        _expectedImgVer = '23.1.2.0.0.230523'
        _expectedImg = f'System.first.boot.{_expectedImgVer}.img'
        self.mock_localimageBz2File(f'{_expectedImg}.bz2')
        self.mPrepareMockCommands(_cmds)
        
        # Do test for clucontrol.mCheckSystemImage()
        _img, _xml = self.mCheckSystemImage_test_wrapper(
            aCustomVersion = None,
            aDom0ImagesMap = _imageMap,
            aInfraOS= _infra            
        )

        # Assert (1 of 2) return from mCheckSystemImage
        self.assertEqual(_img, _expectedImg)

        # Assert (2 of 2) present image in XML
        self.assertIsNotNone(_xml) 
        root = ET.parse(_xml)
        for _ , _domU in self.mGetClubox().mReturnDom0DomUPair():
            ebLogInfo(f'Assert Img in XML for domU: {_domU}' )
            for machine in root.findall('machine'):
                # Check if the <hostName> element matches the target
                host_name_elem = machine.find('hostName')
                if host_name_elem is not None and \
                    host_name_elem.text == _domU:
                    imgVerNum = host_name_elem.find('ImageVersion').text
                    domUImageName = host_name_elem.find('DomUImageName').text
                    self.assertEqual(imgVerNum, _expectedImgVer)
                    self.assertEqual(domUImageName, _expectedImg)

    # ROW NN
    # IN  Infra                         = OL8/24.1.2.0.0.240812
    # IN  allow_domu_custom_version     = False
    # IN  default_domu_img_version      = Empty
    # IN  default_domu_version_last_res = Empty
    # IN  Image in Dom0-1 (NON-RTG) None matching
    # IN  Image in Dom0-2 (NON-RTG) None matching
    # IN  Image in Local  (NON-RTG) System.first.boot.24.1.2.0.0.240812.img.bz2
    # OUT Expectation     (NON-RTG)     = 24.1.2.0.0.240812
    def test_mCheckSystemImage_02_img24_non_rtg(self):        
        # JIRA EXACS-139008
        # Bug 37022415

        # _infra should have the NUMERIC VERSION of each Dom0 in ASC order
        _infra = ['24.1.2.0.0.240812','24.1.2.0.0.240812'] 
        
        # _flags will mock the "used" properties from exabox.conf in this flow
        _flags = {            
            'allow_domu_custom_version': 'False',
            'default_domu_img_version': '',
            'default_domu_img_version_last_res': '',
        }
        
        # _imageMap will mock the list of System Image files for each Dom0
        _imageMap =     {
            "scaqab10adm01.us.oracle.com" :
                [
                    '/EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img'
                ],
            "scaqab10adm02.us.oracle.com" : 
                [
                    '/EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img'
                ]
        }

        _cmds = {
            self.mGetRegexLocal():
            [
                [   # clucontrol mSetImageVersionProperty
                    exaMockCommand("/bin/sed -i *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/sed -r *", aRc=0, aStdout="", aPersist=True),

                    # clucontrol mCheckSystemImage /bin/mkdir -p * opt/oeda/linux-x64/exacloud.conf
                    exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="", aPersist=True),

                    # # clucontrol mCheckSystemImage /bin/scp */config/uuid.xml */opt/oeda/linux-x64/exacloud.conf/uuid.xml
                    exaMockCommand("/bin/scp *", aRc=0, aStdout="", aPersist=True),
                ]
            ],            
            self.mGetRegexDom0("01"): [
                [   # sysimghandler copyVMImageVersionToDom0IfMissing                    
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.rtg.img", aRc=1, aStdout="" ,aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.kvm.img", aRc=1, aStdout="" ,aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("test.*touch", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("/sbin/touch /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img", aRc=0, aStdout="" ,aPersist=True),
                ],
                [   # sysimghandler mGetImageFromDom0ToLocal                    
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.rtg.img", aRc=1, aStdout="",aPersist=True), 
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.kvm.img", aRc=1, aStdout="",aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img", aRc=0, aStdout=""),                    
                ],
                [
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.rtg.img")
                ]
            ],
            self.mGetRegexDom0("02"): [
                [   # sysimghandler copyVMImageVersionToDom0IfMissing
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.rtg.img", aRc=1, aStdout="" ,aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.kvm.img", aRc=1, aStdout="" ,aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("test.*touch", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("/sbin/touch /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.img", aRc=0, aStdout="" ,aPersist=True),
                ],
                [
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.2.0.0.240812.rtg.img")
                ]
            ]

        }
        
        self.mSetExaboxMock(_flags)
        
        _expectedImgVer = '24.1.2.0.0.240812'
        _expectedImg = f'System.first.boot.{_expectedImgVer}.img'
        self.mock_localimageBz2File(f'{_expectedImg}.bz2')
        self.mPrepareMockCommands(_cmds)
        
        # Do test for clucontrol.mCheckSystemImage()
        _img, _xml = self.mCheckSystemImage_test_wrapper(
            aCustomVersion = None,
            aDom0ImagesMap = _imageMap,
            aInfraOS= _infra            
        )

        # Assert (1 of 2) return from mCheckSystemImage
        self.assertEqual(_img, _expectedImg)

        # Assert (2 of 2) present image in XML
        self.assertIsNotNone(_xml) 
        root = ET.parse(_xml)
        for _ , _domU in self.mGetClubox().mReturnDom0DomUPair():
            ebLogInfo(f'Assert Img in XML for domU: {_domU}' )
            for machine in root.findall('machine'):
                # Check if the <hostName> element matches the target
                host_name_elem = machine.find('hostName')
                if host_name_elem is not None and \
                    host_name_elem.text == _domU:
                    imgVerNum = host_name_elem.find('ImageVersion').text
                    domUImageName = host_name_elem.find('DomUImageName').text
                    self.assertEqual(imgVerNum, _expectedImgVer)
                    self.assertEqual(domUImageName, _expectedImg)
        
    # ROW NN
    # IN  Infra                         = OL8/23.1.2.0.0.230523
    # IN  allow_domu_custom_version     = False
    # IN  default_domu_img_version      = Empty
    # IN  default_domu_version_last_res = Empty
    # IN  Image in Dom0-1 (NON-RTG) System.first.boot.23.1.13.0.0.240410.1.img
    # IN  Image in Dom0-2 (NON-RTG) System.first.boot.23.1.13.0.0.240410.1.img
    # IN  Image in Local  (NON-RTG) System.first.boot.23.1.13.0.0.240410.1.kvm.img.bz2
    # OUT Expectation     (NON-RTG)     = 23.1.2.0.0.230523
    def test_mCheckSystemImage_03_custom_img_non_rtg(self):
        # JIRA EXACS-139500
        # Bug 37046560
        # ADB is using "23.1.13.0.0.240410.1" sent as Custom Image

        # [oracle@qaecrahardos1 exacloud]$ pwd 
        # /u04/23415/admin/exacloud
        # [oracle@qaecrahardos1 exacloud]$ ls -ltr images/|grep 23.1.13
        # rw-r---- 1 oracle oinstall 2752037651 Apr 11 06:46 System.first.boot.23.1.13.0.0.240410.1.kvm.img.bz2
        # rw-r---- 1 oracle oinstall 2672763454 Apr 11 07:00 System.first.boot.23.1.13.0.0.240410.1.img.bz2

        _infra = ['24.1.0.0.0.240517.1','24.1.0.0.0.240517.1'] 
        
        # _flags will mock the "used" properties from exabox.conf in this flow
        _flags = {            
            'allow_domu_custom_version': 'True',
            'default_domu_img_version': '23.1.13.0.0.240410.1',
            'default_domu_img_version_last_res': '',
        }
        
        # _imageMap will mock the list of System Image files for each Dom0
        _imageMap =     {
            "scaqab10adm01.us.oracle.com" :
                [
                    '/EXAVMIMAGES/System.first.boot.22.1.10.0.0.230527.img', 
                    '/EXAVMIMAGES/System.first.boot.23.1.13.0.0.240410.1.img'
                ],
            "scaqab10adm02.us.oracle.com" : 
                [
                    '/EXAVMIMAGES/System.first.boot.23.1.13.0.0.240410.1.img'
                    '/EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img', 
                ]
        }

        _cmds = {
            self.mGetRegexLocal():
            [
                [   # clucontrol mSetImageVersionProperty
                    exaMockCommand("/bin/sed -i *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/sed -r *", aRc=0, aStdout="", aPersist=True),

                    # clucontrol mCheckSystemImage /bin/mkdir -p * opt/oeda/linux-x64/exacloud.conf
                    exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="", aPersist=True),

                    # # clucontrol mCheckSystemImage /bin/scp */config/uuid.xml */opt/oeda/linux-x64/exacloud.conf/uuid.xml
                    exaMockCommand("/bin/scp *", aRc=0, aStdout="", aPersist=True),
                ]
            ],            
            self.mGetRegexDom0("01"): [
                [   # sysimghandler copyVMImageVersionToDom0IfMissing
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.23.1.13.0.0.240410.1.rtg.img", aRc=1, aStdout="" ,aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.23.1.13.0.0.240410.1.kvm.img", aRc=1, aStdout="" ,aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.23.1.13.0.0.240410.1.img", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("test.*touch", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("/sbin/touch /EXAVMIMAGES/System.first.boot.23.1.13.0.0.240410.1.img", aRc=0, aStdout="" ,aPersist=True),

                ],
                [
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.23.1.13.0.0.240410.1.kvm.img", aRc=1, aStdout="" ,aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.23.1.13.0.0.240410.1.img", aRc=0, aStdout="" ,aPersist=True),
                ]
            ],
            self.mGetRegexDom0("02"): [
                [   # sysimghandler copyVMImageVersionToDom0IfMissing
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.23.1.13.0.0.240410.1.rtg.img", aRc=1, aStdout="" ,aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.23.1.13.0.0.240410.1.kvm.img", aRc=1, aStdout="" ,aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.23.1.13.0.0.240410.1.img", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("test.*touch", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("/sbin/touch /EXAVMIMAGES/System.first.boot.23.1.13.0.0.240410.1.img", aRc=0, aStdout="" ,aPersist=True),

                ],
                [
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.23.1.13.0.0.240410.1.kvm.img", aRc=1, aStdout="" ,aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.23.1.13.0.0.240410.1.img", aRc=0, aStdout="" ,aPersist=True),
                ]
            ]

        }
        
        self.mSetExaboxMock(_flags)
        
        _expectedImgVer = '23.1.13.0.0.240410.1'
        _expectedImg = f'System.first.boot.{_expectedImgVer}.img'
        self.mock_localimageBz2File(f'{_expectedImg}.bz2')
        self.mPrepareMockCommands(_cmds)
        
        # Do test for clucontrol.mCheckSystemImage()
        _img, _xml = self.mCheckSystemImage_test_wrapper(
            aCustomVersion = _expectedImgVer,
            aDom0ImagesMap = _imageMap,
            aInfraOS= _infra            
        )

        # Assert (1 of 2) return from mCheckSystemImage
        self.assertEqual(_img, _expectedImg)

        # Assert (2 of 2) present image in XML
        self.assertIsNotNone(_xml) 
        root = ET.parse(_xml)
        for _ , _domU in self.mGetClubox().mReturnDom0DomUPair():
            ebLogInfo(f'Assert Img in XML for domU: {_domU}' )
            for machine in root.findall('machine'):
                # Check if the <hostName> element matches the target
                host_name_elem = machine.find('hostName')
                if host_name_elem is not None and \
                    host_name_elem.text == _domU:
                    imgVerNum = host_name_elem.find('ImageVersion').text
                    domUImageName = host_name_elem.find('DomUImageName').text
                    self.assertEqual(imgVerNum, _expectedImgVer)
                    self.assertEqual(domUImageName, _expectedImg)

    # ROW NN
    # IN  Infra                         = OL8/23.1.2.0.0.230523
    # IN  allow_domu_custom_version     = False
    # IN  default_domu_img_version      = Empty
    # IN  default_domu_version_last_res = Empty
    # IN  Image in Dom0-1 (NON-RTG) System.first.boot.24.1.4.0.0.241007.img
    # IN  Image in Dom0-2 (NON-RTG) System.first.boot.24.1.4.0.0.241007.img
    # IN  Image in Local  (NON-RTG) System.first.boot.24.1.4.0.0.241007.kvm.img.bz2
    # OUT Expectation     (NON-RTG)     = 23.1.2.0.0.230523
    def test_mCheckSystemImage_04_custom_img_rtg_enabled_but_use_img(self):
        # JIRA EXACS-145967
        # Bug 37450961
        # ADB is using "24.1.4.0.0.241007" sent as Custom Image

        # [oracle@qaecra2 exacloud]$ ls -lrt images/*24.1.4.*
        # -rw------- 1 oracle oinstall 3007743194 Oct  8 02:26 images/System.first.boot.24.1.4.0.0.241007.kvm.img.bz2
        # -rw-r----- 1 oracle oinstall 3626761139 Oct  8 02:28 images/System.first.boot.24.1.4.0.0.241007.img.bz2

        _infra = ['24.1.4.0.0.241007','24.1.4.0.0.241007'] 
        
        # _flags will mock the "used" properties from exabox.conf in this flow
        _flags = {            
            'allow_domu_custom_version': 'False',
            'default_domu_img_version': '',
            'default_domu_img_version_last_res': '22.1.18.0.0.231208',
        }
        
        # _imageMap will mock the list of System Image files for each Dom0
        _imageMap =     {
            "scaqab10adm01.us.oracle.com" :
                [
                    '/EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.img'
                ],
            "scaqab10adm02.us.oracle.com" : 
                [
                    '/EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.img'
                ]
        }

        _cmds = {
            self.mGetRegexLocal():
            [
                [   # clucontrol mSetImageVersionProperty
                    exaMockCommand("/bin/sed -i *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/sed -r *", aRc=0, aStdout="", aPersist=True),

                    # clucontrol mCheckSystemImage /bin/mkdir -p * opt/oeda/linux-x64/exacloud.conf
                    exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="", aPersist=True),

                    # # clucontrol mCheckSystemImage /bin/scp */config/uuid.xml */opt/oeda/linux-x64/exacloud.conf/uuid.xml
                    exaMockCommand("/bin/scp *", aRc=0, aStdout="", aPersist=True),
                ]
            ],            
            self.mGetRegexDom0("01"): [
                [   # sysimghandler copyVMImageVersionToDom0IfMissing
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.rtg.img", aRc=1, aStdout=""), # Just 1 time
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.img", aRc=0, aStdout=""),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.rtg.img", aRc=1, aStdout=""), 
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.rtg.img.bz2", aRc=1, aStdout=""),
                    exaMockCommand("test.*touch", aRc=0, aStdout=""),
                    exaMockCommand("touch /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.img", aRc=0, aStdout=""),
                ],
                [   # sysimghandler mGetImageFromDom0ToLocal
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.rtg.img.bz2", aRc=1, aStdout=""),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.rtg.img", aRc=1, aStdout=""), 
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.rtg.img.bz2", aRc=1, aStdout=""),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.kvm.img", aRc=1, aStdout="",aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.img", aRc=0, aStdout=""),
                ],
                [
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.rtg.img", aRc=0, aStdout=""), 
                ]
            ],
            self.mGetRegexDom0("02"): [
                [   # sysimghandler copyVMImageVersionToDom0IfMissing
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.rtg.img", aRc=1, aStdout="" ),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.img", aRc=0, aStdout=""),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.kvm.img", aRc=1, aStdout="",aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.img", aRc=0, aStdout=""),
                    exaMockCommand("test.*touch", aRc=0, aStdout=""),
                    exaMockCommand("touch /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.img", aRc=0, aStdout=""),
                ],
                [
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.rtg.img", aRc=0, aStdout=""), 
                ]
            ]
        }
        
        self.mSetExaboxMock(_flags)
        
        _expectedImgVer = '24.1.4.0.0.241007'
        _expectedImg = f'System.first.boot.{_expectedImgVer}.img'
        self.mock_localimageBz2File(f'{_expectedImg}.bz2')
        self.mPrepareMockCommands(_cmds)
        
        # Do test for clucontrol.mCheckSystemImage()
        _img, _xml = self.mCheckSystemImage_test_wrapper(
            aCustomVersion = _expectedImgVer,
            aDom0ImagesMap = _imageMap,
            aInfraOS= _infra            
        )

        # Assert (1 of 2) return from mCheckSystemImage
        self.assertEqual(_img, _expectedImg)

        # Assert (2 of 2) present image in XML
        self.assertIsNotNone(_xml) 
        root = ET.parse(_xml)
        for _ , _domU in self.mGetClubox().mReturnDom0DomUPair():
            ebLogInfo(f'Assert Img in XML for domU: {_domU}' )
            for machine in root.findall('machine'):
                # Check if the <hostName> element matches the target
                host_name_elem = machine.find('hostName')
                if host_name_elem is not None and \
                    host_name_elem.text == _domU:
                    imgVerNum = host_name_elem.find('ImageVersion').text
                    domUImageName = host_name_elem.find('DomUImageName').text
                    self.assertEqual(imgVerNum, _expectedImgVer)
                    self.assertEqual(domUImageName, _expectedImg)

    # ROW NN
    # IN  Infra (HYBRID!)               = OL8/24.1.4.0.0.241007, OL8/25.1.1.0.0.250121
    # IN  allow_domu_custom_version     = False
    # IN  default_domu_img_version      = Empty
    # IN  default_domu_version_last_res = Empty
    # IN  Image in Dom0-1 (NON-RTG) System.first.boot.24.1.4.0.0.241007.img
    # IN  Image in Dom0-2 (NON-RTG) System.first.boot.24.1.4.0.0.241007.img
    # IN  Image in Local  (NON-RTG) System.first.boot.24.1.4.0.0.241007.kvm.img.bz2
    # OUT Expectation     (NON-RTG)     = 23.1.2.0.0.230523
    def test_mCheckSystemImage_05_hybrid_infra_rtg_enabled_but_use_img(self):
        # JIRA EXACS-153541
        # Bug 37963204
        # Using "24.1.4.0.0.241007" sent as Custom Image

        # $ ls -lrt images/*24.1.4.*
        # -rw------- 1 oracle oinstall 3007743194 Oct  8 02:26 images/System.first.boot.24.1.4.0.0.241007.kvm.img.bz2
        # -rw-r----- 1 oracle oinstall 3626761139 Oct  8 02:28 images/System.first.boot.24.1.4.0.0.241007.img.bz2

        _infra = ['24.1.4.0.0.241007','25.1.1.0.0.250121'] 
        
        # _flags will mock the "used" properties from exabox.conf in this flow
        _flags = {            
            'allow_domu_custom_version': 'True',
            'default_domu_img_version': '',
            'default_domu_img_version_last_res': '22.1.18.0.0.231208',
        }
        
        # _imageMap will mock the list of System Image files for each Dom0
        _imageMap = {}

        _cmds = {
            self.mGetRegexLocal():
            [
                [   # clucontrol mSetImageVersionProperty
                    exaMockCommand("/bin/sed -i *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/sed -r *", aRc=0, aStdout="", aPersist=True),

                    # clucontrol mCheckSystemImage /bin/mkdir -p * opt/oeda/linux-x64/exacloud.conf
                    exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="", aPersist=True),

                    # # clucontrol mCheckSystemImage /bin/scp */config/uuid.xml */opt/oeda/linux-x64/exacloud.conf/uuid.xml
                    exaMockCommand("/bin/scp *", aRc=0, aStdout="", aPersist=True),
                ]
            ],            
            self.mGetRegexDom0("01"): [
                [   # sysimghandler copyVMImageVersionToDom0IfMissing                
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.rtg.img", aRc=1, aStdout="",aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.kvm.img", aRc=1, aStdout="",aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.img", aRc=1, aStdout=""),
                    exaMockCommand("/bin/scp images/System.first.boot.24.1.4.0.0.241007.kvm.img.bz2 /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.kvm.img.bz2", aRc=0, aStdout="",aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/pbunzip2", aRc=0, aStdout=""),
                    exaMockCommand("/sbin/pbunzip2 /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.kvm.img.bz2", aRc=0, aStdout=""),                    
                    exaMockCommand("/bin/mv /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.kvm.img /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.img", aRc=0, aStdout=""),
                    exaMockCommand("test.*touch", aRc=0, aStdout=""),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.img", aRc=0, aStdout=""),
                    exaMockCommand("/sbin/touch /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.img", aRc=0, aPersist=True)
                ],
                [   # sysimghandler mGetImageFromDom0ToLocal                    
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.rtg.img", aRc=1, aStdout="",aPersist=True), 
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.kvm.img", aRc=1, aStdout="",aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.img", aRc=1, aStdout=""),                    
                ]
            ],
            self.mGetRegexDom0("02"): [
                [   # sysimghandler copyVMImageVersionToDom0IfMissing
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.rtg.img", aRc=1, aStdout="",aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.kvm.img", aRc=1, aStdout="",aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.img", aRc=1, aStdout=""),                    
                    exaMockCommand("/bin/scp images/System.first.boot.24.1.4.0.0.241007.kvm.img.bz2 /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.kvm.img.bz2", aRc=0,aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/pbunzip2", aRc=0, aStdout=""),
                    exaMockCommand("/sbin/pbunzip2 /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.kvm.img.bz2", aRc=0, aStdout=""),
                    exaMockCommand("/bin/mv /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.kvm.img /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.img", aRc=0, aStdout=""),
                    exaMockCommand("test.*touch", aRc=0, aStdout=""),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.img", aRc=0, aStdout=""),
                    exaMockCommand("/sbin/touch /EXAVMIMAGES/System.first.boot.24.1.4.0.0.241007.img", aRc=0, aPersist=True)
                ]
            ]
        }
        
        self.mSetExaboxMock(_flags)
        
        _expectedImgVer = '24.1.4.0.0.241007'
        _expectedImg = f'System.first.boot.{_expectedImgVer}.img'
        self.mock_localimageBz2File(f'System.first.boot.{_expectedImgVer}.kvm.img.bz2')
        self.mPrepareMockCommands(_cmds)
        
        # Do test for clucontrol.mCheckSystemImage()
        _img, _xml = self.mCheckSystemImage_test_wrapper(
            aCustomVersion = _expectedImgVer,
            aDom0ImagesMap = _imageMap,
            aInfraOS= _infra            
        )

        # Assert (1 of 2) return from mCheckSystemImage
        self.assertEqual(_img, _expectedImg)

        # Assert (2 of 2) present image in XML
        self.assertIsNotNone(_xml) 
        root = ET.parse(_xml)
        for _ , _domU in self.mGetClubox().mReturnDom0DomUPair():
            ebLogInfo(f'Assert Img in XML for domU: {_domU}' )
            for machine in root.findall('machine'):
                # Check if the <hostName> element matches the target
                host_name_elem = machine.find('hostName')
                if host_name_elem is not None and \
                    host_name_elem.text == _domU:
                    imgVerNum = host_name_elem.find('ImageVersion').text
                    domUImageName = host_name_elem.find('DomUImageName').text
                    self.assertEqual(imgVerNum, _expectedImgVer)
                    self.assertEqual(domUImageName, _expectedImg)

if __name__ == '__main__':
    unittest.main()
