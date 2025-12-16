#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_vmboci.py /main/3 2025/05/07 20:21:53 jfsaldan Exp $
#
# tests_vmboci.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_vmboci.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      UT for vmboci.py
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    04/28/25 - Bug 37877334 - EXACLOUD VMBACKUP TO OSS PREVENT
#                           EXACSDBOPS-10887 | TERMINATION FAILS IF VMBACKUP TO
#                           OSS COMPARTMENT DOES NOT EXIST
#    jfsaldan    09/19/23 - Bug 35811483 - EXACLOUD SHOULD NOT RELY ON THE
#                           VAULT OCID FROM EXABOX.CONF TO CHECK IF VMBACKUP
#                           BUCKETS NEED TO BE DELETED DURING DELETE SERVICE
#    jfsaldan    09/08/23 - Bug 35790909 - PREVMSETUP TASK FAILED IN
#                           DELETESERVICE: IN DELETE VMBACKUPS FROM DOM0 STEP
#    jfsaldan    09/08/23 - Creation
#


import unittest
from unittest.mock import patch, Mock, MagicMock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.vmboci import ebVMBackupOCI

class ebTestVMBOCI(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        # Call ebTestClucontrol, to specify noDB/noOEDA
        super().setUpClass(False,False)
        self.maxDiff = None

    def test_payload_disabled(self):
        """
        Test payload has vmbackup disabled
        """

        aOptions = self.mGetPayload()
        self.assertFalse(ebVMBackupOCI.mIsVMBOSSEnabled(aOptions))

        aOptions = self.mGetPayload()
        aOptions.jsonconf["vmboss"] = {}
        self.assertFalse(ebVMBackupOCI.mIsVMBOSSEnabled(aOptions))

        aOptions = self.mGetPayload()
        aOptions.jsonconf["vmboss"] = {
                "vmboss_map": []
                }
        self.assertFalse(ebVMBackupOCI.mIsVMBOSSEnabled(aOptions))

    def test_payload_enabled(self):
        """
        Test payload has vmbackup enabled
        """

        aOptions = self.mGetPayload()
        aOptions.jsonconf["vmboss"] = {
            "vmboss_map": [
                {
                    "dom0": "dom0name_1_FQDN",
                    "domu": "DomUNAME_1_customer_FQDN",
                    "customer_tenancy_ocid": "<the ocid of the customer tenancy ID>",
                    "vmboss_compartment": "vmboss_comp_<the ocid of the customer tenancy ID>",
                    "vmboss_metadata_bucket": "vmboss_metadata_bucket_<the ocid of the customer tenancy ID>",
                    "vmboss_bucket": "vmboss_bucket_<the ocid of the customer tenancy ID>_<ecra_clustername>"
                },
            ]
        }
        self.mGetContext().mSetConfigOption('exabm', 'False')
        self.assertFalse(ebVMBackupOCI.mIsVMBOSSEnabled(aOptions))

        self.mGetContext().mSetConfigOption('exabm', 'True')
        self.assertTrue(ebVMBackupOCI.mIsVMBOSSEnabled(aOptions))

    @patch("exabox.ovm.vmboci.ExaOCIFactory")
    def test_mGetVMBackupCompartmentId_noOCID(self, aMockFactory):
        """
        """

        aOptions = self.mGetPayload()
        aOptions.jsonconf["vmboss"] = {
            "vmboss_map": [
                {
                    "dom0": "dom0name_1_FQDN",
                    "domu": "DomUNAME_1_customer_FQDN",
                    "customer_tenancy_ocid": "<the ocid of the customer tenancy ID>",
                    "vmboss_compartment": "vmboss_comp_<the ocid of the customer tenancy ID>",
                    "vmboss_metadata_bucket": "vmboss_metadata_bucket_<the ocid of the customer tenancy ID>",
                    "vmboss_bucket": "vmboss_bucket_<the ocid of the customer tenancy ID>_<ecra_clustername>"
                },
            ]
        }

        aMockFactory.return_value.get_identity_client.return_value.list_compartments.return_value = MagicMock()

        self.mGetContext().mSetConfigOption('kms_key_id', 'somekmsocid')
        _vmbackup_oci_mgr = ebVMBackupOCI(aOptions)

        self.assertEqual( (None, None), _vmbackup_oci_mgr.mGetVMBackupCompartmentId())

if __name__ == '__main__':
    unittest.main()
