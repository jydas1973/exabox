"""

 $Header:

 Copyright (c) 2020, 2021, Oracle and/or its affiliates. 

 NAME:
      tests_exaccRoCE.py - Unitest for RoCE ExaCC

 DESCRIPTION:
      Tests for RoCE ExaCC

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
        oerincon  04/03/20 - 31124650: Validate QinQ proper setup for RoCE enabled
                             environments during Create Service
        oerincon  03/11/20 - Creation of the file for exacloud unit test

"""

import os
import unittest
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.cluexaccroce import ExaCCRoCE_CPS
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import ebJsonObject


class ebTestRoCEExaCC(ebTestClucontrol):

    @classmethod
    def setUpClass(self):

        _resources = 'exabox/exatest/cluctrl/cluexacc/resources/exaccRoCE/QinQ/'
        super().setUpClass(aResourceFolder=_resources)

    def setUp(self):

        _setup = os.path.join(self.mGetPath(), "ocpsSetup.json")
        self.mGetClubox().mGetCtx().mSetConfigOption('ocps_jsonpath', _setup)

    def test_OCPS_RoCESetup(self):
        exaCCRoCE = ExaCCRoCE_CPS()
        self.assertEqual(exaCCRoCE.mSetupCPSRoCE()[:3],
                         ('192.168.11.46',  # RoCE IP of local CPS Server
                          '255.255.255.0',  # Netmask
                          '192.168.11.48'))  # Remote CPS RoCE IP

    def test_RoCE_identification(self):
        self.mGetClubox().mParseXMLConfig(ebJsonObject())
        # Verify we can detect a RoCE setup
        self.assertEqual(self.mGetClubox().mIsKVM(), True)

    def test_RoCE_QinQ_identification(self):
        self.mGetClubox().mParseXMLConfig(ebJsonObject())
        self.assertEqual(self.mGetClubox().mIsRoCEQinQ(), True)

    # Validates the ExaCCRoCE_CPS returns a valid set of cell ips (same as input)
    def test_RoCE_QinQ_setup_validation (self):
        exaCCRoCE = ExaCCRoCE_CPS()
        self.assertEqual(exaCCRoCE.mVerifyCPSRoCEQinQSetup(
            ['192.168.0.1', '192.168.0.2'])[0],
            ['192.168.0.1', '192.168.0.2'])

    # Validates the clucontrol pass the correct QinQ RoCE IPs to the shell script
    def test_RoCE_QinQ_identify_cell_roce_ips_validation (self):
        self.mGetClubox().mParseXMLConfig(ebJsonObject())
        _roce_cell_ips = self.mGetClubox().mCheckCPSQinQSetup(False)[0]
        _roce_cell_ips.sort()
        self.assertEqual(_roce_cell_ips,
            ['192.168.34.203', '192.168.34.204',  # RoCE QinQ cell 1 ips
             '192.168.34.205', '192.168.34.206',  # RoCE QinQ cell 2 ips
             '192.168.34.207', '192.168.34.208'])  # RoCE QinQ cell 3 ips


if __name__ == '__main__':
    unittest.main()
