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

import unittest
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.cluexaccroce import ExaCCRoCE_CPS
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import ebJsonObject

class ebTestRoCEExaCC(ebTestClucontrol):

    @classmethod
    def setUpClass(self):

        _resources = 'exabox/exatest/cluctrl/cluexacc/resources/exaccRoCE/NoQinQ/'
        super().setUpClass(aResourceFolder=_resources)

    def test_RoCE_no_QinQ_identification(self):
        self.mGetClubox().mParseXMLConfig(ebJsonObject())
        self.assertEqual(self.mGetClubox().mIsRoCEQinQ(), False)

    # Validates the clucontrol pass do not find any RoCE IP for non QinQ env, leading to an exception
    def test_RoCE_NonQinQ_identify_cell_roce_ips_failure (self):

        self.mGetClubox().mParseXMLConfig(ebJsonObject())

        # Must throw an exception, as no valid RoCE cell ips are identified for this cluster
        with self.assertRaises(ExacloudRuntimeError):
            self.mGetClubox().mCheckCPSQinQSetup(False)


if __name__ == '__main__':
    unittest.main()
