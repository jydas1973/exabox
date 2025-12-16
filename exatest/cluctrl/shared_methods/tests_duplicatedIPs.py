#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/shared_methods/tests_duplicatedIPs.py /main/2 2021/03/26 10:22:32 jesandov Exp $
#
# tests_duplicatedIPs.py
#
# Copyright (c) 2021, Oracle and/or its affiliates. 
#
#    NAME
#      tests_duplicatedIPs.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ffrrodri    02/16/21 - Test for validate duplicated IPs
#    ffrrodri    02/16/21 - Creation
#
import unittest

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Error import ExacloudRuntimeError


class IPCells(ebTestClucontrol):
    UNIQUE_CELLS = {
        "cell_1": [
            ['scas07celadm12', 'admin', 'eth0', '10.128.76.118'],
            ['scas07celadm12-priv1', 'private', 'stpkeyib0', '201.168.76.137'],
            ['scas07celadm12-priv2', 'private', 'stpkeyib1', '201.168.76.138']
        ],
        "cell_2": [
            ['scas07celadm12', 'admin', 'eth0', '10.128.76.119'],
            ['scas07celadm12-priv1', 'private', 'stpkeyib0', '201.168.76.139'],
            ['scas07celadm12-priv2', 'private', 'stpkeyib1', '201.168.76.140']
        ],
        "cell_3": [
            ['scas07celadm12', 'admin', 'eth0', '10.128.76.120'],
            ['scas07celadm12-priv1', 'private', 'stpkeyib0', '201.168.76.141'],
            ['scas07celadm12-priv2', 'private', 'stpkeyib1', '201.168.76.142']
        ],
        "cell_4": [
            ['scas07celadm12', 'admin', 'eth0', '10.128.76.121'],
            ['scas07celadm12-priv1', 'private', 'stpkeyib0', '201.168.76.143'],
            ['scas07celadm12-priv2', 'private', 'stpkeyib1', '201.168.76.144']
        ]
    }

    DUPLICATE_CELLS = {
        "cell_1": [
            ['scas07celadm12', 'admin', 'eth0', '10.128.76.118'],
            ['scas07celadm12-priv1', 'private', 'stpkeyib0', '201.168.76.137'],
            ['scas07celadm12-priv2', 'private', 'stpkeyib1', '201.168.76.138']
        ],
        "cell_2": [
            ['scas07celadm12', 'admin', 'eth0', '10.128.76.119'],
            ['scas07celadm12-priv1', 'private', 'stpkeyib0', '201.168.76.138'],
            ['scas07celadm12-priv2', 'private', 'stpkeyib1', '201.168.76.140']
        ],
        "cell_3": [
            ['scas07celadm12', 'admin', 'eth0', '10.128.76.120'],
            ['scas07celadm12-priv1', 'private', 'stpkeyib0', '201.168.76.141'],
            ['scas07celadm12-priv2', 'private', 'stpkeyib1', '201.168.76.141']
        ],
        "cell_4": [
            ['scas07celadm12', 'admin', 'eth0', '10.128.76.121'],
            ['scas07celadm12-priv1', 'private', 'stpkeyib0', '201.168.76.143'],
            ['scas07celadm12-priv2', 'private', 'stpkeyib1', '201.168.76.140']
        ]
    }

    DUPLICATE_CELLS_DETECTED = [
        ['scas07celadm12-priv2', 'private', 'stpkeyib1', '201.168.76.138'],
        ['scas07celadm12-priv1', 'private', 'stpkeyib0', '201.168.76.138'],
        ['scas07celadm12-priv2', 'private', 'stpkeyib1', '201.168.76.140'],
        ['scas07celadm12-priv1', 'private', 'stpkeyib0', '201.168.76.141'],
        ['scas07celadm12-priv2', 'private', 'stpkeyib1', '201.168.76.141'],
        ['scas07celadm12-priv2', 'private', 'stpkeyib1', '201.168.76.140']
    ]

    DUPLICATE_IPS = [
        '201.168.76.138',
        '201.168.76.141',
        '201.168.76.140'
    ]

    def test_returnDuplicatedIPs_001(self):
        return self.assertEqual(self.mGetClubox().mReturnDuplicateCellIPs(self.DUPLICATE_CELLS), self.DUPLICATE_IPS)

    def test_detectDuplicatedIPs_001(self):
        return self.assertEqual(self.mGetClubox().mDetectDuplicatedIPCells(self.UNIQUE_CELLS), [])

    def test_detectDuplicatedIPs_002(self):
        return self.assertEqual(self.mGetClubox().mDetectDuplicatedIPCells(self.DUPLICATE_CELLS),
                             self.DUPLICATE_CELLS_DETECTED)

    def test_detectDuplicatedIPs_003(self):
        _empty_dict = {}
        return self.assertEqual(self.mGetClubox().mDetectDuplicatedIPCells(_empty_dict), [])


if __name__ == '__main__':
    unittest.main()
