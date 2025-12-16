"""

 $Header: 

 Copyright (c) 2018, 2025, Oracle and/or its affiliates.

 NAME:
      tests_ebSubnetIp.py - Unitest for class ebSubnetIp in exabox.ovm.clumisc

 DESCRIPTION:
      Run tests for the class ebSubnetIp using Unitest

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)

        prsshukl    09/11/25 - Bug 38417085 - ECS_MAIN -> TESTS_EBSUBNETIP_PY.DIF 
                               FAILING AS SLCS16ADM0708CLU* CLUSTERS ARE DECOMMISSIONED
        jesandov    07/17/18 - Creation of the file for exacloud unit test
"""

import unittest
from exabox.ovm.clumisc import ebSubnetIp

class ebTestSubnet(unittest.TestCase):

    def test_mInternalInt(self):
        e = ebSubnetIp()
        self.assertEqual(e.mIntToIp(2130706433), '127.0.0.1')
        self.assertEqual(e.mIpToInt('127.0.0.1'), 2130706433)

    def test_mInternalMask(self):
        e = ebSubnetIp()
        self.assertEqual(e.mSegmentToMask(32), '255.255.255.255')
        self.assertEqual(e.mMaskToSegment('255.255.255.255'), 32)

    def test_localhost(self):
        e = ebSubnetIp('127.0.0.1')
        self.assertEqual(e.mGetAllIPs(), ['127.0.0.1'])
        self.assertEqual(e.mGetSubnet(), '127.0.0.1/255.255.255.255')
        self.assertEqual(e.mGetCIDR(), '127.0.0.1/32')
      
    def test_segment(self):
        e = ebSubnetIp('192.168.1.2/30')
        self.assertEqual(e.mGetAllIPs(), ['192.168.1.0', '192.168.1.1', '192.168.1.2', '192.168.1.3'])
        self.assertEqual(e.mGetSubnet(), '192.168.1.0/255.255.255.252')
        self.assertEqual(e.mGetCIDR(), '192.168.1.0/30')

    def test_mask(self):
        e = ebSubnetIp('10.15.50.10/255.255.255.248')
        self.assertEqual(e.mGetAllIPs(), ['10.15.50.8',  '10.15.50.9',  
                                          '10.15.50.10', '10.15.50.11', 
                                          '10.15.50.12', '10.15.50.13', 
                                          '10.15.50.14', '10.15.50.15'])
        self.assertEqual(e.mGetSubnet(), '10.15.50.8/255.255.255.248')
        self.assertEqual(e.mGetCIDR(), '10.15.50.8/29')

    def test_dns(self):
        e = ebSubnetIp('slcqab02adm03.us.oracle.com')
        self.assertEqual(e.mGetAllIPs(), ['10.249.54.70'])

    def test_dns_mask(self):
        e = ebSubnetIp('slcqab02adm03.us.oracle.com/31')
        self.assertEqual(e.mGetAllIPs(), [])
        self.assertEqual(e.mGetSubnet(), '10.249.54.70/255.255.255.254')
        self.assertEqual(e.mGetCIDR(), '10.249.54.70/31')

    def test_first(self):
        e = ebSubnetIp('77.0.0.5/24')
        f = e.mGetIntFirstIp()
        f = e.mIntToIp(f)
        self.assertEqual(f, '77.0.0.0')

    def test_first_31(self):
        e = ebSubnetIp('77.0.0.5/31')
        f = e.mGetIntFirstIp()
        f = e.mIntToIp(f)
        self.assertEqual(f, '77.0.0.4')

    def test_first_single(self):
        e = ebSubnetIp('77.0.0.5')
        f = e.mGetIntFirstIp()
        f = e.mIntToIp(f)
        self.assertEqual(f, '77.0.0.5')

    def test_last(self):
        e = ebSubnetIp('77.0.0.5/24')
        f = e.mGetIntLastIp()
        f = e.mIntToIp(f)
        self.assertEqual(f, '77.0.0.255')

    def test_last_31(self):
        e = ebSubnetIp('77.1.2.3/31')
        f = e.mGetIntLastIp()
        f = e.mIntToIp(f)
        self.assertEqual(f, '77.1.2.3')

    def test_last_single(self):
        e = ebSubnetIp('77.1.2.3')
        f = e.mGetIntLastIp()
        f = e.mIntToIp(f)
        self.assertEqual(f, '77.1.2.3')

    def test_subset(self):
        e1 = ebSubnetIp('192.168.1.1/25')
        e2 = ebSubnetIp('192.168.2.1/25')
        self.assertFalse(e1.mIsSubset(e2))
        self.assertFalse(e2.mIsSubset(e1))

    def test_subset_expand(self):
        e1 = ebSubnetIp('192.168.1.0/25')
        e2 = ebSubnetIp('192.168.1.0/26')
        self.assertFalse(e1.mIsSubset(e2))
        self.assertTrue(e2.mIsSubset(e1))
        
    def test_subset_colide(self):
        e1 = ebSubnetIp('192.168.1.0/24')
        e2 = ebSubnetIp('192.168.2.1/24')
        self.assertFalse(e1.mIsSubset(e2))
        self.assertFalse(e2.mIsSubset(e1))

    def test_subset_single_ip(self):
        e1 = ebSubnetIp('192.168.1.1/24')
        e2 = ebSubnetIp('192.168.1.25')
        self.assertFalse(e1.mIsSubset(e2))
        self.assertTrue(e2.mIsSubset(e1))

    def test_space_pad1(self):
        e = ebSubnetIp('192.168.1.1 / 24')
        self.assertEqual(e.mGetSubnet(), '192.168.1.0/255.255.255.0')
        self.assertEqual(e.mGetCIDR(), '192.168.1.0/24')

    def test_space_pad2(self):
        e = ebSubnetIp('192 . 168 . 1 . 1 /24')
        self.assertEqual(e.mGetSubnet(), '192.168.1.0/255.255.255.0')
        self.assertEqual(e.mGetCIDR(), '192.168.1.0/24')

    def test_space_pad3(self):
        e = ebSubnetIp('192 .168 .1 .1')
        self.assertEqual(e.mGetSubnet(), '192.168.1.1/255.255.255.255')
        self.assertEqual(e.mGetCIDR(), '192.168.1.1/32')

    def test_max_ip(self):
        self.assertRaises(ValueError, ebSubnetIp, '300.300.300.300')

    def test_min_ip(self):
        self.assertRaises(ValueError, ebSubnetIp, '-24.70.-40.3')

    def tets_max_segment(self):
        e = ebSubnetIp('')
        self.assertRaises(ValueError, e.mLimitSegment, '400')
        self.assertRaises(ValueError, e.mLimitSegment, '-10')
        self.assertEqual(e.mLimitSegment(77), 77)
        
    def test_none(self):
        e = ebSubnetIp(None)
        self.assertEqual(e.mGetSubnet(), '0.0.0.0/255.255.255.255')
        self.assertEqual(e.mGetCIDR(), '0.0.0.0/32')

if __name__ == '__main__':
    unittest.main()

