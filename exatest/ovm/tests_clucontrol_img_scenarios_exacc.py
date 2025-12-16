#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_clucontrol_img_scenarios_exacc.py /main/5 2025/12/01 22:37:00 avimonda Exp $
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
#    jfsaldan    04/21/25 - Enh 37647115 - EXACLOUD - REDUCE
#                           COMPRESSION/DECOMPRESSION TIME FOR SYSTEM IMAGE.
#                           REPLACE BZIP2 BY PBZIP2 OR SIMILAR
#    gparada     09/18/24 - 37032724 Validate scenarios to handle System first
#                           boot image for NON-RTG and RTG
#    gparada     09/18/24 - Creation
#
import os
import unittest
import xml.etree.ElementTree as ET

from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo, ebLogError

from pathlib import Path
from unittest.mock import patch
from typing import List, Dict

class ebTestSystemFirstBootScenarios(ebTestClucontrol):
    """
    UNIT TESTS FOR mCheckSystemImage AS DEFINED IN
    RTG System Image Provisioning Testing

    https://confluence.oraclecorp.com/confluence/display/EDCS/
    RTG+System+Image+Provisioning+Testing

    NOTE:  
    I highly recommend a future refactor in mCheckSystemImage, 
    we started some refactor with Samuel/Gustavo in 2023 for handling custom
    image for DomUs.
    Now for RTG we created a more comprehensive set of tests (see URL above)
    and it helped us to test with broader coverage in the following functions. 
    The points that lead me to this suggestions are based on:
    * The bug tested below helped us to identify most of the functions 
      shown below, which may be repeated, this could be avoided.
    * For image handling, functions use a "version", but the current arguments
      use different domain of values (some functions receive version as a 
    number, while others receive a filename with extension included).
    * Handling of KVM, NON-KVM and now the optional RTG has caused our 
      code is more convoluted.
    * Once the logic for image handling is understood, the logic could be 
      simplified to: 
      * Consider conditions (business rules) to calculate version to be used.
      * Identify the filename AND version to be used.
      * Ensure this filename (extension included) exists across local and Dom0s
      * Ensure the XML is patched with the expected filename (to ensure OEDA
        will not complain).

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
        self.original_os_listdir = os.listdir

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

    def mListLocalSystem(self, path):
        # Patches in the parent process are not carried over to subprocesses.

        # This os.listdir is only patched in parent process
        # But it is tricky to patch in a multiprocess execution.ade         
        imageBz2File = f'images/{self.localimageBz2File}'
        if path == imageBz2File:
            _files = [f"{imageBz2File}"]
            Path(imageBz2File).touch() # Simulate file
            return _files
        return self.original_os_listdir(path)

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

        # Since this file is tests_clucontrol_img_scenarios_exacc.py
        # we should set flag for ExaCC
        _ebox_localmSetOciExacc = True

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
            patch('os.path.exists', side_effect=self.mCheckLocalSystemExists),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', 
                  side_effect=self.mock_mCheckConfigOption),\
            patch('exabox.core.Context.GlobalContext.mGetConfigOptions',
                  side_effect=self.mock_mGetConfigOptionsRTG),\
            patch('exabox.ovm.sysimghandler.mGetLocalFileHash', return_value={'System.first.boot.22.1.10.0.0.230422.img':'d2fd86...'}), \
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', 
                   return_value=True, aPersist=True):
            # patch('os.listdir', side_effect=self.mListLocalSystem),\
            # patch('exabox.core.Node.exaBoxNode.mCompareFiles',return_value = True):
            
            _img = _ebox_local.mCheckSystemImage(aCustomVersion)            

        _xmlPath = _ebox_local.mGetPatchConfig()
        ebLogInfo(f"_img: {_img} _xmlPath: {_xmlPath}")

        return _img, _xmlPath

    # ROW NN
    # IN  Infra                         = OL8/24.1.0.0.0.240517.1
    # IN  allow_domu_custom_version     = False
    # IN  default_domu_img_version      = Empty
    # IN  default_domu_version_last_res = Empty
    # IN  Image in Dom0-1 (NON-RTG) None matching
    # IN  Image in Dom0-2 (RTG)     System.first.boot.24.1.0.0.0.240517.1.rtg.img
    # IN  Image in Local  (NON-RTG) None matching
    # OUT Expectation     (RTG)     System.first.boot.24.1.0.0.0.240517.1.rtg.img
    def test_mCheckSystemImage_04_partial_rtg(self):
        # JIRA EXACS-139222
        # Bug 37032724

        # JIRA EXACS_139223
        # Bug 37032788

        # On rack scaqau06adm0304, we tried to provision a single vm cluster with 23ai grid.
        # Here we selected Dom0 for vm placement which does not have RTG image file but another Dom0 has this RTG file. CPS also does NOT have RTG file. 

        # [ecra@scaqau06cps02 bin]$ ./exassh scaqau06adm03 -e ls -lrt /EXAVMIMAGES/ | grep rtg
        # [ecra@scaqau06cps02 bin]$ ./exassh scaqau06adm04 -e ls -lrt /EXAVMIMAGES/ | grep rtg
        # rw-r---- 1 root root 108770046976 Sep 3 08:06 System.first.boot.24.1.0.0.0.240517.1.rtg.img
        # rw-r---- 1 root root 3025765534 Sep 6 02:13 System.first.boot.24.1.0.0.0.240517.1.rtg.img.bz2

        # CPS does not have RTG image file-
        # [ecra@scaqau06cps02 bin]$ ls -lrt /u01/downloads/exadata/images/.rtg
        # ls: cannot access '/u01/downloads/exadata/images/.rtg': No such file or directory

        # _infra should have the NUMERIC VERSION of each Dom0 in ASC order
        _infra = ['24.1.0.0.0.240517.1','24.1.0.0.0.240517.1'] 
        
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
                ],
            "scaqab10adm02.us.oracle.com" : 
                [
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
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.img", aRc=0, aStdout=""),
                    # I am not persisting this command because in order to test/validate the scenario, we need to tell 1 time this is a failure (see ret code 1)
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img", aRc=1, aStdout=""), # When searching for RTG in Dom0-1, simulate NOT FOUND.
                    # After Img is 1) copied in local (from Dom0-2), 
                    # we need to 2) copy from local to Dom0-1
                    exaMockCommand("/bin/scp images/System.first.boot.24.1.0.0.0.240517.1.rtg.img.bz2 /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img.bz2", aRc=0, aStdout="",aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img.bz2", aRc=0, aStdout=""),
                    exaMockCommand("sha256sum /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img.bz2", aRc=0, aStdout="somesha",aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img.bz2", aRc=0, aStdout=""),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img.bz2", aRc=0, aStdout=""),
                    exaMockCommand("/bin/test -e .*pbunzip2", aRc=0, aStdout=""),
                    exaMockCommand("pbunzip2 /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img.bz2", aRc=0, aStdout=""),
                    exaMockCommand("test.*touch", aRc=0, aStdout=""),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img", aRc=0, aStdout=""),
                    exaMockCommand("touch /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img", aRc=0, aStdout=""),
                ]
            ],
            self.mGetRegexDom0("02"): [
                [   # sysimghandler copyVMImageVersionToDom0IfMissing
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img", aRc=0, aStdout=""),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img.bz2", aRc=1, aStdout=""),
                    exaMockCommand("test.*touch", aRc=0, aStdout=""),
                    exaMockCommand("/sbin/touch /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img", aRc=0, aStdout=""),
                ],                
                [   # sysimghandler copyVMImageVersionToDom0IfMissing                    
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img.bz2", aRc=1, aStdout=""),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img", aRc=0, aStdout=""),
                    exaMockCommand("/usr/sbin/pbzip2 -k /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img", aRc=0, aStdout=""),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img.bz2", aRc=0, aStdout=""),
                ],                
                [   # sysimghandler copyVMImageVersionToDom0IfMissing aForceRtg=True
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img", aRc=0, aStdout=""),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.24.1.0.0.0.240517.1.rtg.img.bz2", aRc=0, aStdout=""),
                ]
            ]

        }
        
        self.mSetExaboxMock(_flags)
        
        _expectedImgVer = '24.1.0.0.0.240517.1'
        _expectedImg = f'System.first.boot.{_expectedImgVer}.rtg.img'
        self.mock_localimageBz2File('System.first.boot.23.1.2.0.0.230523.img.bz2') # NON RTG
        self.mPrepareMockCommands(_cmds)

        imageBz2File = f'images/{_expectedImg}.bz2'
        Path(imageBz2File).touch() # Simulate file

        with patch('exabox.ovm.sysimghandler.mVerifyImagesMultiProc', 
                   return_value={"scaqab10adm01.us.oracle.com": 0, "scaqab10adm02.us.oracle.com": 0}), \
             patch('exabox.ovm.sysimghandler.mGetImageFromDom0ToLocal', return_value=None), \
             patch('exabox.ovm.sysimghandler.getVMImageArchiveInRepo', 
                   return_value={
                       'filePath': imageBz2File,
                       'fileBaseName': os.path.basename(imageBz2File),
                       'imgBaseName': _expectedImg,
                       'imgArchiveBaseName': os.path.basename(imageBz2File),
                       'imgVersion': _expectedImgVer,
                       'isKvmImg': False,
                       'isRtgImg': True,
                       'isArchive': True
                   }), \
             patch('exabox.ovm.sysimghandler.mGetVMImageArchiveInfoInLocalRepo', 
                   return_value={
                       'filePath': imageBz2File,
                       'fileBaseName': os.path.basename(imageBz2File),
                       'imgBaseName': _expectedImg,
                       'imgArchiveBaseName': os.path.basename(imageBz2File),
                       'imgVersion': _expectedImgVer,
                       'isKvmImg': False,
                       'isRtgImg': True,
                       'isArchive': True
                   }): 
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

if __name__ == '__main__':
    unittest.main()
