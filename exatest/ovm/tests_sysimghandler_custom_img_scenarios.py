#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_sysimghandler_custom_img_scenarios.py /main/1 2023/12/01 21:23:45 gparada Exp $
#
# tests_sysimghandler_custom_img_scenarios.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_sysimghandler_custom_img_scenarios.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    gparada     11/08/23 - 35990044 - Add UT's for hasDomUCustomOS for
#                           permutation table in confluence
#    gparada     11/08/23 - Creation
#
import unittest

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.sysimghandler import hasDomUCustomOS

from unittest.mock import patch
from typing import List, Dict

class ebTestSysImgHandlerScenarios(ebTestClucontrol):
    """
    UNIT TESTS FOR hasDomUCustomOS AS DEFINED IN
    OL7/OL8 VM Cluster OS provisioning workflow
    https://confluence.oraclecorp.com/confluence/pages/viewpage.action?
    pageId=7971995690    
    """
    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def mSetExaboxMock(self, aDict):
        self.exabox_conf = aDict

    # Mock functions
    def mock_exabox_conf(self, aDict, aKey):
        if (aKey in aDict):
            return aDict[aKey]

    def mock_mCheckConfigOption(self, aOption, aValue=None):
        if aValue:
            return self.mock_exabox_conf(self.exabox_conf,aOption) == aValue
        else:
            return self.mock_exabox_conf(self.exabox_conf,aOption)
    
    def hasDomUCustomOS_test_wrapper(
            self,
            aInfraOS:List, 
            aPlatform:str, 
            aExaboxConf: Dict):
        """
        This is MAIN wrapper function, so hasDomUCustomOS() can be tested
        according to the variables from the confluence page.
        Arguments:
            aInfraOS expected values: 'OL7', 'OL8'
            aPlatform expected values: 'X7', 'X8', 'X9', 'X10'
            aExaboxConf expecte values: {'key1':'value1','key2':'value2'}
        """        
        _ebox_local = self.mGetClubox()

        with patch('exabox.ovm.sysimghandler.mGetDom0sImagesListSorted', 
                  return_value=aInfraOS),\
            patch ('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', 
                    return_value=aPlatform),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', 
                  side_effect=self.mock_mCheckConfigOption):            
            _img = hasDomUCustomOS(_ebox_local)
            return _img

    """
    Full table of permutations for reference :
    OL7/OL8 VM Cluster OS provisioning workflow (Link at top of class)

    --+-----+--------+--------+------+---------+-----------------+-----------
    ## INFRA PLATFORM OS_PRECH ALLOW* DEF*_DOMU DEF*_DOMU_LAST_R* EXPECTED
      |     |        |        |      |         |                 |CUSTOM OS VERS
    --+-----+--------+--------+------+---------+-----------------+-----------
    01 OL8/  non-X10M False    True   22.1.11... Empty            22.1.11
       23.1
    02 OL8/  non-X10M False    True   Empty      22.1.16...       22.1.16
       23.1	
    03 OL8/  non-X10M False    True   22.1.11... 22.1.10...       22.1.11
       23.1	
    04 OL8/  non-X10M False    True   Empty      Empty            ERROR
       23.1	
    05 OL8/  non-X10M False    False  Any        Any              None
       23.1	
    06 OL8/  X10M     False    True   Any        Any              None
       23.1	
    07 OL8/  X10M     False    False  Any        Any              None
       23.1	
    08 OL7/  non-X10M False    True   22.1.11... Empty            22.1.11
       22.1	
    09 OL7/  non-X10M False    True   Empty      22.1.16...       None
       22.1	
    10 OL7/  non-X10M False    True   22.1.11... Empty            22.1.11
       22.1	
    11 OL7/  non-X10M False    True   Empty      Empty            None
       22.1	
    12 OL7/  non-X10M False    True   Any        Any              None
       22.1	
    13 OL7/  non-X10M False    True   22.1.11... Empty            22.1.11
       22.1
       OL8/
       23.1	
    14 OL7/  non-X10M False    True   Empty      22.1.16...       None 
       22.1
       OL8/
       23.1	
    15 OL7/  non-X10M False    True   22.1.11... Empty            22.1.11 
       22.1
       OL8/
       23.1	
    16 OL7/  non-X10M False    True   Empty      Empty            None 
       22.1
       OL8/
       23.1	
    17 OL7/  non-X10M False    False  Any        Any              None
       22.1
       OL8/
       23.1	
    
    """

    # ROW 01 
    # IN  Infra                         = OL8/23.1
    # IN  Platform                      = NON-X10M
    # IN  os_precheck                   = False
    # IN  allow_domu_custom_version     = True
    # IN  default_domu_img_version      = 22.1.11
    # IN  default_domu_version_last_res = Empty    
    # OUT Expectation                   = 22.1.11
    def test_hasDomUCustomOS_01(self):        
        _infra = ['23.1']
        _platform = 'X8'
        _flags = {            
            'os_precheck': 'False',
            'allow_domu_custom_version': 'True',
            'default_domu_img_version': '22.1.11',
            'default_domu_img_version_last_res': ''
        }
        self.mSetExaboxMock(_flags)
        _expected = '22.1.11'
        
        # Do test for sysimghandler.hasDomUCustomOS()
        _img = self.hasDomUCustomOS_test_wrapper(
            aInfraOS= _infra,
            aPlatform= _platform,
            aExaboxConf= _flags
        )
        self.assertEqual(_img, _expected)
        print(f'test_hasDomUCustomOS_01 passed with expected val: {_expected}')
        
    # ROW 02
    # IN  Infra                         = OL8/23.1
    # IN  Platform                      = NON-X10M
    # IN  os_precheck                   = False
    # IN  allow_domu_custom_version     = True
    # IN  default_domu_img_version      = Empty
    # IN  default_domu_version_last_res = 22.1.16
    # OUT Expectation                   = 22.1.16
    def test_hasDomUCustomOS_02(self):
        _infra = ['23.1']
        _platform = 'X8'
        _flags = {            
            'os_precheck': 'False',
            'allow_domu_custom_version': 'True',
            'default_domu_img_version': '',
            'default_domu_img_version_last_res': '22.1.16'
        }
        self.mSetExaboxMock(_flags)
        _expected = '22.1.16'
        
        # Do test for sysimghandler.hasDomUCustomOS()
        _img = self.hasDomUCustomOS_test_wrapper(
            aInfraOS= _infra,
            aPlatform= _platform,
            aExaboxConf= _flags
        )
        self.assertEqual(_img, _expected)
        print(f'test_hasDomUCustomOS_02 passed with expected val: {_expected}')

    # ROW 03
    # IN  Infra                         = OL8/23.1
    # IN  Platform                      = NON-X10M
    # IN  os_precheck                   = False
    # IN  allow_domu_custom_version     = True
    # IN  default_domu_img_version      = 22.1.11
    # IN  default_domu_version_last_res = 22.1.10
    # OUT Expectation                   = 22.1.11
    def test_hasDomUCustomOS_03(self):
        _infra = ['23.1']
        _platform = 'X8'
        _flags = {            
            'os_precheck': 'False',
            'allow_domu_custom_version': 'True',
            'default_domu_img_version': '22.1.11',
            'default_domu_img_version_last_res': '22.1.10'
        }
        self.mSetExaboxMock(_flags)
        _expected = '22.1.11'
        
        # Do test for sysimghandler.hasDomUCustomOS()
        _img = self.hasDomUCustomOS_test_wrapper(
            aInfraOS= _infra,
            aPlatform= _platform,
            aExaboxConf= _flags
        )
        self.assertEqual(_img, _expected)
        print(f'test_hasDomUCustomOS_03 passed with expected val: {_expected}')

    # ROW 04
    # IN  Infra                         = OL8/23.1
    # IN  Platform                      = NON-X10M
    # IN  os_precheck                   = False
    # IN  allow_domu_custom_version     = True
    # IN  default_domu_img_version      = Empty
    # IN  default_domu_version_last_res = Empty
    # OUT Expectation                   = ERROR
    def test_hasDomUCustomOS_04(self):
        _infra = ['23.1']
        _platform = 'X8'
        _flags = {            
            'os_precheck': 'False',
            'allow_domu_custom_version': 'True',
            'default_domu_img_version': '',
            'default_domu_img_version_last_res': ''
        }
        self.mSetExaboxMock(_flags)
        _expected = "default_domu_img_version_last_res is required."
        
        # Do test for sysimghandler.hasDomUCustomOS()
        self.assertRaisesRegex(ValueError, 
            _expected, 
            self.hasDomUCustomOS_test_wrapper, _infra, _platform, _flags)
        print(f'test_hasDomUCustomOS_04 passed with expected Err: {_expected}')

    # ROW 05
    # IN  Infra                         = OL8/23.1
    # IN  Platform                      = NON-X10M
    # IN  os_precheck                   = False
    # IN  allow_domu_custom_version     = False
    # IN  default_domu_img_version      = Any
    # IN  default_domu_version_last_res = Any
    # OUT Expectation                   = None
    def test_hasDomUCustomOS_05(self):        
        _infra = ['23.1']
        _platform = 'X8'
        _flags = {            
            'os_precheck': 'False',
            'allow_domu_custom_version': 'False',
            'default_domu_img_version': '',
            'default_domu_img_version_last_res': ''
        }
        self.mSetExaboxMock(_flags)
        
        # Do test for sysimghandler.hasDomUCustomOS()        
        _img = self.hasDomUCustomOS_test_wrapper(
            aInfraOS= _infra,
            aPlatform= _platform,
            aExaboxConf= _flags
        )
        self.assertIsNone(_img)
        print(f'test_hasDomUCustomOS_05 passed with expected val: {_img}')

    # ROW 06
    # IN  Infra                         = OL8/23.1
    # IN  Platform                      = X10M
    # IN  os_precheck                   = False
    # IN  allow_domu_custom_version     = True
    # IN  default_domu_img_version      = Any
    # IN  default_domu_version_last_res = Any
    # OUT Expectation                   = None
    def test_hasDomUCustomOS_06(self):        
        _infra = ['23.1']
        _platform = 'X10'
        _flags = {            
            'os_precheck': 'False',
            'allow_domu_custom_version': 'True',
            'default_domu_img_version': '',
            'default_domu_img_version_last_res': ''
        }
        self.mSetExaboxMock(_flags)
        
        # Do test for sysimghandler.hasDomUCustomOS()        
        _img = self.hasDomUCustomOS_test_wrapper(
            aInfraOS= _infra,
            aPlatform= _platform,
            aExaboxConf= _flags
        )
        self.assertIsNone(_img)
        print(f'test_hasDomUCustomOS_06 passed with expected val: {_img}')

    # ROW 07
    # IN  Infra                         = OL8/23.1
    # IN  Platform                      = X10M
    # IN  os_precheck                   = False
    # IN  allow_domu_custom_version     = False
    # IN  default_domu_img_version      = Any
    # IN  default_domu_version_last_res = Any
    # OUT Expectation                   = None
    def test_hasDomUCustomOS_07(self):
        _infra = ['23.1']
        _platform = 'X10'
        _flags = {            
            'os_precheck': 'False',
            'allow_domu_custom_version': 'False',
            'default_domu_img_version': '',
            'default_domu_img_version_last_res': ''
        }
        self.mSetExaboxMock(_flags)
        
        # Do test for sysimghandler.hasDomUCustomOS()        
        _img = self.hasDomUCustomOS_test_wrapper(
            aInfraOS= _infra,
            aPlatform= _platform,
            aExaboxConf= _flags
        )
        self.assertIsNone(_img)
        print(f'test_hasDomUCustomOS_07 passed with expected val: {_img}')

    # ROW 08
    # IN  Infra                         = OL7/22.1
    # IN  Platform                      = NON-X10M
    # IN  os_precheck                   = False
    # IN  allow_domu_custom_version     = True
    # IN  default_domu_img_version      = 22.1.11
    # IN  default_domu_version_last_res = Any
    # OUT Expectation                   = None
    def test_hasDomUCustomOS_08(self):
        _infra = ['23.1']
        _platform = 'X8'
        _flags = {            
            'os_precheck': 'False',
            'allow_domu_custom_version': 'True',
            'default_domu_img_version': '22.1.11',
            'default_domu_img_version_last_res': ''
        }
        self.mSetExaboxMock(_flags)
        _expected = '22.1.11'
        
        # Do test for sysimghandler.hasDomUCustomOS()        
        _img = self.hasDomUCustomOS_test_wrapper(
            aInfraOS= _infra,
            aPlatform= _platform,
            aExaboxConf= _flags
        )
        self.assertEqual(_img,_expected)
        print(f'test_hasDomUCustomOS_05 passed with expected val: {_expected}')

    # ROW 09
    # IN  Infra                         = OL7/22.1
    # IN  Platform                      = NON-X10M
    # IN  os_precheck                   = False
    # IN  allow_domu_custom_version     = True
    # IN  default_domu_img_version      = Empty
    # IN  default_domu_version_last_res = 22.1.16
    # OUT Expectation                   = NONE (image ver = KVM HOST ver)
    def test_hasDomUCustomOS_09(self):
        _infra = ['22.1']
        _platform = 'X8'
        _flags = {            
            'os_precheck': 'False',
            'allow_domu_custom_version': 'True',
            'default_domu_img_version': '',
            'default_domu_img_version_last_res': '22.1.16'
        }
        self.mSetExaboxMock(_flags)
        
        # Do test for sysimghandler.hasDomUCustomOS()
        _img = self.hasDomUCustomOS_test_wrapper(
            aInfraOS= _infra,
            aPlatform= _platform,
            aExaboxConf= _flags
        )
        self.assertIsNone(_img)
        print(f'test_hasDomUCustomOS_09 passed with expected val: {_img}')

    # ROW 10
    # IN  Infra                         = OL7/22.1
    # IN  Platform                      = NON-X10M
    # IN  os_precheck                   = False
    # IN  allow_domu_custom_version     = True
    # IN  default_domu_img_version      = 22.1.11
    # IN  default_domu_version_last_res = Empty
    # OUT Expectation                   = 22.1.11
    def test_hasDomUCustomOS_10(self):
        _infra = ['22.1']
        _platform = 'X8'
        _flags = {            
            'os_precheck': 'False',
            'allow_domu_custom_version': 'True',
            'default_domu_img_version': '22.1.11',
            'default_domu_img_version_last_res': ''
        }
        self.mSetExaboxMock(_flags)
        _expected = '22.1.11'
        
        # Do test for sysimghandler.hasDomUCustomOS()
        _img = self.hasDomUCustomOS_test_wrapper(
            aInfraOS= _infra,
            aPlatform= _platform,
            aExaboxConf= _flags
        )
        self.assertEqual(_img, _expected)
        print(f'test_hasDomUCustomOS_10 passed with expected val: {_expected}')

    # ROW 11
    # IN  Infra                         = OL7/22.1
    # IN  Platform                      = NON-X10M
    # IN  os_precheck                   = False
    # IN  allow_domu_custom_version     = True
    # IN  default_domu_img_version      = Empty
    # IN  default_domu_version_last_res = Empty
    # OUT Expectation                   = None
    def test_hasDomUCustomOS_11(self):
        _infra = ['22.1']
        _platform = 'X8'
        _flags = {            
            'os_precheck': 'False',
            'allow_domu_custom_version': 'True',
            'default_domu_img_version': '',
            'default_domu_img_version_last_res': ''
        }
        self.mSetExaboxMock(_flags)
        
        # Do test for sysimghandler.hasDomUCustomOS()
        _img = self.hasDomUCustomOS_test_wrapper(
            aInfraOS= _infra,
            aPlatform= _platform,
            aExaboxConf= _flags
        )
        self.assertIsNone(_img)
        print(f'test_hasDomUCustomOS_11 passed with expected val: {_img}')

    # ROW 12
    # IN  Infra                         = OL7/22.1
    # IN  Platform                      = NON-X10M
    # IN  os_precheck                   = False
    # IN  allow_domu_custom_version     = False
    # IN  default_domu_img_version      = Any
    # IN  default_domu_version_last_res = Any
    # OUT Expectation                   = None
    def test_hasDomUCustomOS_12(self):
        _infra = ['22.1']
        _platform = 'X8'
        _flags = {            
            'os_precheck': 'False',
            'allow_domu_custom_version': 'False',
            'default_domu_img_version': '',
            'default_domu_img_version_last_res': ''
        }
        self.mSetExaboxMock(_flags)
        
        # Do test for sysimghandler.hasDomUCustomOS()
        _img = self.hasDomUCustomOS_test_wrapper(
            aInfraOS= _infra,
            aPlatform= _platform,
            aExaboxConf= _flags
        )
        self.assertIsNone(_img)
        print(f'test_hasDomUCustomOS_12 passed with expected val: {_img}')

    # ROW 13
    # IN  Infra                         = OL7/22.1 + OL8/23.1
    # IN  Platform                      = NON-X10M
    # IN  os_precheck                   = False
    # IN  allow_domu_custom_version     = True
    # IN  default_domu_img_version      = 22.1.11
    # IN  default_domu_version_last_res = Any
    # OUT Expectation                   = None
    def test_hasDomUCustomOS_13(self):
        _infra = ['22.1']
        _platform = 'X8'
        _flags = {            
            'os_precheck': 'False',
            'allow_domu_custom_version': 'True',
            'default_domu_img_version': '22.1.11',
            'default_domu_img_version_last_res': ''
        }
        self.mSetExaboxMock(_flags)
        _expected = '22.1.11'
        
        # Do test for sysimghandler.hasDomUCustomOS()
        _img = self.hasDomUCustomOS_test_wrapper(
            aInfraOS= _infra,
            aPlatform= _platform,
            aExaboxConf= _flags
        )
        self.assertEqual(_img, _expected)
        print(f'test_hasDomUCustomOS_13 passed with expected val: {_expected}')

    # ROW 14
    # IN  Infra                         = OL7/22.1 + OL8/23.1
    # IN  Platform                      = NON-X10M
    # IN  os_precheck                   = False
    # IN  allow_domu_custom_version     = True
    # IN  default_domu_img_version      = Empty
    # IN  default_domu_version_last_res = 22.1.16
    # OUT Expectation                   = None
    def test_hasDomUCustomOS_14(self):
        _infra = ['22.1','23.1']
        _platform = 'X8'
        _flags = {            
            'os_precheck': 'False',
            'allow_domu_custom_version': 'True',
            'default_domu_img_version': '',
            'default_domu_img_version_last_res': '22.1.16'
        }
        self.mSetExaboxMock(_flags)
        
        # Do test for sysimghandler.hasDomUCustomOS()
        _img = self.hasDomUCustomOS_test_wrapper(
            aInfraOS= _infra,
            aPlatform= _platform,
            aExaboxConf= _flags
        )
        self.assertIsNone(_img)
        print(f'test_hasDomUCustomOS_14 passed with expected val: {_img}')

    # ROW 15
    # IN  Infra                         = OL7/22.1 + OL8/23.1
    # IN  Platform                      = NON-X10M
    # IN  os_precheck                   = False
    # IN  allow_domu_custom_version     = True
    # IN  default_domu_img_version      = 22.1.11
    # IN  default_domu_version_last_res = Empty
    # OUT Expectation                   = 22.1.11
    def test_hasDomUCustomOS_15(self):
        _infra = ['22.1','23.1']
        _platform = 'X8'
        _flags = {            
            'os_precheck': 'False',
            'allow_domu_custom_version': 'True',
            'default_domu_img_version': '22.1.11',
            'default_domu_img_version_last_res': ''
        }
        self.mSetExaboxMock(_flags)
        _expected = '22.1.11'
        
        # Do test for sysimghandler.hasDomUCustomOS()
        _img = self.hasDomUCustomOS_test_wrapper(
            aInfraOS= _infra,
            aPlatform= _platform,
            aExaboxConf= _flags
        )
        self.assertEqual(_img, _expected)
        print(f'test_hasDomUCustomOS_15 passed with expected val: {_expected}')

    # ROW 16
    # IN  Infra                         = OL7/22.1 + OL8/23.1
    # IN  Platform                      = NON-X10M
    # IN  os_precheck                   = False
    # IN  allow_domu_custom_version     = True
    # IN  default_domu_img_version      = Empty
    # IN  default_domu_version_last_res = Empty
    # OUT Expectation                   = None
    def test_hasDomUCustomOS_16(self):
        _infra = ['22.1','23.1']
        _platform = 'X8'
        _flags = {            
            'os_precheck': 'False',
            'allow_domu_custom_version': 'True',
            'default_domu_img_version': '',
            'default_domu_img_version_last_res': ''
        }
        self.mSetExaboxMock(_flags)
        
        # Do test for sysimghandler.hasDomUCustomOS()
        _img = self.hasDomUCustomOS_test_wrapper(
            aInfraOS= _infra,
            aPlatform= _platform,
            aExaboxConf= _flags
        )
        self.assertIsNone(_img)
        print(f'test_hasDomUCustomOS_16 passed with expected val: {_img}')

    # ROW 17
    # IN  Infra                         = OL7/22.1 + OL8/23.1
    # IN  Platform                      = NON-X10M
    # IN  os_precheck                   = False
    # IN  allow_domu_custom_version     = False
    # IN  default_domu_img_version      = Any
    # IN  default_domu_version_last_res = Any
    # OUT Expectation                   = None
    def test_hasDomUCustomOS_17(self):
        _infra = ['22.1','23.1']
        _platform = 'X8'
        _flags = {            
            'os_precheck': 'False',
            'allow_domu_custom_version': 'False',
            'default_domu_img_version': '',
            'default_domu_img_version_last_res': ''
        }
        self.mSetExaboxMock(_flags)
        
        # Do test for sysimghandler.hasDomUCustomOS()
        _img = self.hasDomUCustomOS_test_wrapper(
            aInfraOS= _infra,
            aPlatform= _platform,
            aExaboxConf= _flags
        )
        self.assertIsNone(_img)
        print(f'test_hasDomUCustomOS_17 passed with expected val: {_img}')

if __name__ == '__main__':
    unittest.main()
