"""

 $Header: 

 Copyright (c) 2018, 2025, Oracle and/or its affiliates. 

 NAME:
      tests_exaccIB.py - Unitest for IB ExaCC

 DESCRIPTION:
      Tests for IB ExaCC

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
    oespinos    07/03/25 - 38006547: Modified return from mSetupCPSIB 
    vgerard     09/06/18 - Creation of the file for exacloud unit test
"""

import os
import unittest
import json
from exabox.ovm.cluexaccib import ExaCCIB_CPS, ExaCCIB_DomU
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

class ebTestExaCC(ebTestClucontrol):

    @classmethod
    def setUpClass(self):

        _resources = "exabox/exatest/cluctrl/cluexacc/resources/exaccIB/"
        super().setUpClass(aResourceFolder=_resources)

    def setUp(self):

        _setup = os.path.join(self.mGetPath(), "ocpsSetup.json")
        self.mGetClubox().mGetCtx().mSetConfigOption('ocps_jsonpath', _setup)

        self._domUs = ['domU_1','domU_2']
        self._dom0s = ['dom0_1','dom0_2']
        self._cells = ['cell_1','cell_2','cell_3']
        self._allGUID = {'dom0_1':['0xAAAAABBBB1','0xAAAAABBBB2'],
                          'dom0_2':['0xCCCCCDDDD1','0xCCCCCDDDD2'],
                          'cell_1':['0xAAAAADDDD1','0xAAAAADDDD2'],
                          'cell_2':['0xEEEEEDDDD1','0xEEEEEDDDD2'],
                          'cell_3':['0xFFFFFDDDD1','0xFFFFFDDDD2'],
                          #Remote cps key will match configuration remote_cps_host key
                          '173.222.333.2':['0x44444DDDD1','0x44444DDDD2'],
                          'localCPS':['0x33333DDDD1','0x33333DDDD2']}

    def test_CPSAlreadyCreated(self):
        _checkPkey = ('masterswhost','staa32','0x2a32',True)
        exaCCib = ExaCCIB_CPS(self._allGUID, _checkPkey)
        self.assertTrue(exaCCib.mSetupIBSwitches(self._dom0s,self._cells))

    def test_PartitionwithoutCPSSetup(self):
        _checkPkey = ('masterswhost','staa32','0x2a32',False)
        exaCCib = ExaCCIB_CPS(self._allGUID, _checkPkey)
        # Add 2 CPS to partition
        self.assertEqual(exaCCib.mSetupIBSwitches(self._dom0s,self._cells),
            ['smpartition start',
            'smpartition add -n staa32 -port 0x33333DDDD1 -m full',
            'smpartition add -n staa32 -port 0x33333DDDD2 -m full',
            'smpartition commit'])

    def test_withoutPartition(self):
        _checkPkey = ('masterswhost',None,'0x2a32',False)
        exaCCib = ExaCCIB_CPS(self._allGUID, _checkPkey)
        self.assertEqual(exaCCib.mSetupIBSwitches(self._dom0s,self._cells),
            ['smpartition start',
              'smpartition create -n staa32 -pkey 0x2a32 -flag ipoib -m full',
              'smpartition add -n staa32 -port 0xAAAAABBBB1 -m limited',
              'smpartition add -n staa32 -port 0xAAAAABBBB2 -m limited',
              'smpartition add -n staa32 -port 0xCCCCCDDDD1 -m limited',
              'smpartition add -n staa32 -port 0xCCCCCDDDD2 -m limited',
              'smpartition add -n staa32 -port 0xAAAAADDDD1 -m full',
              'smpartition add -n staa32 -port 0xAAAAADDDD2 -m full',
              'smpartition add -n staa32 -port 0xEEEEEDDDD1 -m full',
              'smpartition add -n staa32 -port 0xEEEEEDDDD2 -m full',
              'smpartition add -n staa32 -port 0xFFFFFDDDD1 -m full',
              'smpartition add -n staa32 -port 0xFFFFFDDDD2 -m full',
              'smpartition add -n staa32 -port 0x33333DDDD1 -m full',
              'smpartition add -n staa32 -port 0x33333DDDD2 -m full',
              'smpartition commit'])

    def test_OCPS_IBSetup(self):
        _checkPkey = ('masterswhost','staa32','0x2a32',False)
        exaCCib = ExaCCIB_CPS(self._allGUID, _checkPkey)
        self.assertEqual(exaCCib.mSetupCPSIB()[:4],
             (['192.168.11.46', '192.168.11.47'], #IB IPs of local CPS Server
              '255.255.255.0', #Netmask
              '0xaa31',        #PKEY
              ['192.168.11.48', '192.168.11.49'])) #Remote CPS IBIPs

    def test_domU_iptables(self):
        exaccDomU = ExaCCIB_DomU(self._domUs)
        self.assertEqual(exaccDomU.mSecureDomUIB(),
             ['-A INPUT -i stib0 -p tcp -m tcp -m multiport ! --dports 7060,7070 -s 192.168.11.46 -j DROP',
              '-A INPUT -i stib0 -p tcp -m tcp -m multiport ! --dports 7060,7070 -s 192.168.11.47 -j DROP',
              '-A INPUT -i stib0 -p tcp -m tcp -m multiport ! --dports 7060,7070 -s 192.168.11.48 -j DROP',
              '-A INPUT -i stib0 -p tcp -m tcp -m multiport ! --dports 7060,7070 -s 192.168.11.49 -j DROP',
              '-A INPUT -i stib1 -p tcp -m tcp -m multiport ! --dports 7060,7070 -s 192.168.11.46 -j DROP',
              '-A INPUT -i stib1 -p tcp -m tcp -m multiport ! --dports 7060,7070 -s 192.168.11.47 -j DROP',
              '-A INPUT -i stib1 -p tcp -m tcp -m multiport ! --dports 7060,7070 -s 192.168.11.48 -j DROP',
              '-A INPUT -i stib1 -p tcp -m tcp -m multiport ! --dports 7060,7070 -s 192.168.11.49 -j DROP'])

if __name__ == '__main__':
    unittest.main()
