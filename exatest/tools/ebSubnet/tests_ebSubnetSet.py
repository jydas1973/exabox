"""

 $Header: 

 Copyright (c) 2018, 2020, Oracle and/or its affiliates. All rights reserved.

 NAME:
      tests_ebSubnetSet.py - Unitest for class ebSubnetSet in exabox.ovm.clumisc

 DESCRIPTION:
      Run tests for the class ebSubnetSet using Unitest

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       jesandov    07/17/18 - Creation of the file
"""

import unittest
from exabox.ovm.clumisc import ebSubnetSet, ebSubnetIp

class ebTestSubnetSet(unittest.TestCase):

    def test_add_singles_ip(self):
        _set = ebSubnetSet()
        _set.mAddSubnet('192.168.1.1')
        _set.mAddSubnet('192.168.1.2')
        _set.mAddSubnet(None)
        _set.mAddSubnet('192.168.1.3')
        self.assertEqual(_set.mGetAllIPs(), ['192.168.1.1', '192.168.1.2', '192.168.1.3'])

    def test_add_unique_ip(self):
        _set = ebSubnetSet()
        _set.mAddSubnet('192.168.1.1')
        _set.mAddSubnet('192.168.1.2')
        _set.mAddSubnet('192.168.1.1')
        self.assertEqual(_set.mGetAllIPs(), ['192.168.1.1', '192.168.1.2'])

    def test_add_collapse_inverse(self):
        _set = ebSubnetSet()
        _set.mAddSubnet('192.168.1.1/29')
        _set.mAddSubnet('192.168.1.2/30')
        _set.mAddSubnet('192.168.1.1/32')
        self.assertEqual(_set.mGetAllIPs(), ['192.168.1.0', '192.168.1.1',
                                              '192.168.1.2', '192.168.1.3',
                                              '192.168.1.4', '192.168.1.5',
                                              '192.168.1.6', '192.168.1.7'])

    def test_add_collapse(self):
        _set = ebSubnetSet()
        _set.mAddSubnet('192.168.1.1/32')
        _set.mAddSubnet('192.168.1.2/30')
        _set.mAddSubnet('192.168.1.1/29')
        self.assertEqual(_set.mGetAllIPs(), ['192.168.1.0', '192.168.1.1',
                                              '192.168.1.2', '192.168.1.3',
                                              '192.168.1.4', '192.168.1.5',
                                              '192.168.1.6', '192.168.1.7'])

    def test_oneself_subset_verify(self):
        _ip  = ebSubnetIp('10.15.50.61/29')
        _set = ebSubnetSet()
        _set.mAddSubnet('10.15.50.60/28')
        self.assertEqual(_set.mIpInSet(_ip), [1])

    def test_other_subset_verify(self):
        _ip  = ebSubnetIp('10.15.50.60/28')
        _set = ebSubnetSet()
        _set.mAddSubnet('10.15.50.61/29')
        self.assertEqual(_set.mIpInSet(_ip), [-1])

    def test_subset_not_conflict(self):
        _ip  = ebSubnetIp('10.15.50.60/28')
        _set = ebSubnetSet()
        _set.mAddSubnet('10.15.51.61/29')
        self.assertEqual(_set.mIpInSet(_ip), [])

    def test_read_list(self):
        _list = ['192.168.1.1', '192.168.1.2', '192.168.1.1']
        _set = ebSubnetSet()
        _set.mAppendList(_list)
        self.assertEqual(_set.mGetAllIPs(), ['192.168.1.1', '192.168.1.2'])

    def test_read_none_list(self):
        _list = None
        _set = ebSubnetSet()
        _set.mAppendList(_list)
        self.assertEqual(_set.mGetAllIPs(), [])

    def test_get_subnet_list(self):
        _list = ['192.168.1.1', '192.168.1.2', '192.168.1.1/24']
        _result = ['192.168.1.0/255.255.255.0']
        _set = ebSubnetSet()
        _set.mAppendList(_list)
        self.assertEqual(_set.mGetSubnetList(), _result)

    def test_get_subnet_cidr(self):
        _list = ['192.168.1.1', '192.168.1.2', '192.168.1.1/24']
        _result = ['192.168.1.0/24']
        _set = ebSubnetSet()
        _set.mAppendList(_list)
        self.assertEqual(_set.mGetCIDRList(), _result)

    def test_commas(self):
        _list =  ['192.168.1.1',  '192.168.1.2',    '192.168.1.1/24']
        _list += ['192.168.1.25', '192.168.2.2/32', '192.168.1.8/24']
        _list += ['192.168.0.1',  '192.168.0.2',    '192.168.0.3/255.255.255.0']

        _set = ebSubnetSet()
        _set.mAppendList(_list)
        _res  = '192.168.0.0/24,192.168.1.0/24,192.168.2.2/32'
        _res2 = ','.join(_set.mGetCIDRList())
        self.assertEqual(_res, _res2)

    def test_spaces(self):
        _list =  ['192.168.1.1',  '192.168.1.2',    '192.168.1.1/24']
        _list += ['192.168.0.1',  '192.168.0.2',    '192.168.0.3/255.255.255.0']

        _set = ebSubnetSet()
        _set.mAppendList(_list)
        _res  = '192.168.0.0/255.255.255.0 192.168.1.0/255.255.255.0'
        _res2 = ' '.join(_set.mGetSubnetList())
        self.assertEqual(_res, _res2)


if __name__ == '__main__':
    unittest.main()

