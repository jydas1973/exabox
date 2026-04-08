#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_vmboci.py /main/4 2025/12/11 09:46:13 aypaul Exp $
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
#    aypaul      12/09/25 - Bug#38736166 Enhance code coverage with Cline
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
from exabox.core.Error import ExacloudRuntimeError

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


# ===== Cline auto-generated enhancements (appended) =====
class ebTestVMBOCI_ClineEnhancements(ebTestClucontrol):
    """
    Auto-generated tests to increase coverage on ebVMBackupOCI.
    """

    @classmethod
    def setUpClass(self):
        super().setUpClass(False, False)
        self.maxDiff = None

    def _valid_payload(self):
        aOptions = self.mGetPayload()
        aOptions.jsonconf["vmboss"] = {
            "vmboss_map": [
                {
                    "dom0": "dom0host1.fqdn",
                    "domu": "custvm1.fqdn",
                    "customer_tenancy_ocid": "ocid1.tenancy.oc1..abc",
                    "vmboss_compartment": "vmboss_comp_ocid1",
                    "vmboss_metadata_bucket": "vmboss_metadata_bucket_ten1",
                    "vmboss_bucket": "vmboss_bucket_ten1_cluster"
                },
                {
                    "dom0": "dom0host2.fqdn",
                    "domu": "custvm2.fqdn",
                    "customer_tenancy_ocid": "ocid1.tenancy.oc1..def",
                    "vmboss_compartment": "vmboss_comp_ocid2",
                    "vmboss_metadata_bucket": "vmboss_metadata_bucket_ten2",
                    "vmboss_bucket": "vmboss_bucket_ten2_cluster"
                }
            ]
        }
        # Ensure exabm true so mIsVMBOSSEnabled can be true if needed
        self.mGetContext().mSetConfigOption('exabm', 'True')
        # Ensure kms key available for __init__
        self.mGetContext().mSetConfigOption('kms_key_id', 'kms-ocid-123')
        return aOptions

    def test_parse_customer_values_missing_fields_raises(self):
        # Auto-generated test: missing mandatory keys must raise ExacloudRuntimeError
        aOptions = self.mGetPayload()
        aOptions.jsonconf["vmboss"] = {"vmboss_map": [{"dom0": "d0-only"}]}
        with self.assertRaises(ExacloudRuntimeError):
            ebVMBackupOCI(aOptions)

    @patch("exabox.ovm.vmboci.ExaOCIFactory")
    @patch("exabox.ovm.vmboci.get_instance_root_compartment", return_value="ocid.root")
    @patch("exabox.ovm.vmboci.get_instance_compartment", return_value="ocid.comp")
    def test_return_dom0_domu_pair(self, _gic, _girc, mock_factory):
        # Auto-generated positive path for mReturnDom0DomUPair
        aOptions = self._valid_payload()
        # Stub clients
        id_cli = MagicMock()
        obj_cli = MagicMock()
        obj_cli.get_namespace.return_value = MagicMock(data="ns", request_id="req-1")
        mock_factory.return_value.get_identity_client.return_value = id_cli
        mock_factory.return_value.get_object_storage_client.return_value = obj_cli
        mock_factory.return_value.get_secrets_client.return_value = MagicMock()
        mock_factory.return_value.get_vault_client.return_value = MagicMock()

        mgr = ebVMBackupOCI(aOptions)
        pairs = mgr.mReturnDom0DomUPair()
        self.assertIn(("dom0host1.fqdn", "custvm1.fqdn"), pairs)
        self.assertIn(("dom0host2.fqdn", "custvm2.fqdn"), pairs)
        self.assertEqual(len(pairs), 2)

    @patch("exabox.ovm.vmboci.ExaOCIFactory")
    @patch("exabox.ovm.vmboci.get_instance_root_compartment", return_value="ocid.root")
    def test_check_bucket_exists_true_false(self, _girc, mock_factory):
        # Auto-generated test for mCheckBucketExists
        aOptions = self._valid_payload()
        obj_cli = MagicMock()
        obj_cli.get_namespace.return_value = MagicMock(data="ns", request_id="req-1")
        # head_bucket returns ok first, then raises to simulate missing
        obj_cli.head_bucket.side_effect = [MagicMock(), Exception("not found")]
        mock_factory.return_value.get_object_storage_client.return_value = obj_cli
        mock_factory.return_value.get_identity_client.return_value = MagicMock()
        mock_factory.return_value.get_secrets_client.return_value = MagicMock()
        mock_factory.return_value.get_vault_client.return_value = MagicMock()

        mgr = ebVMBackupOCI(aOptions)
        self.assertTrue(mgr.mCheckBucketExists("bucket1"))
        self.assertFalse(mgr.mCheckBucketExists("bucket2"))

    def test_compare_fingerprints_true_and_false(self):
        # Auto-generated test for mCompareFingerPrints
        # Build an instance without running full __init__
        mgr = ebVMBackupOCI.__new__(ebVMBackupOCI)
        siv_ok = {"public_key_details": {"fingerprint": "aa:bb:cc"}}
        public_keys = []
        pk1 = MagicMock()
        pk1.fingerprint = "11:22"
        pk2 = MagicMock()
        pk2.fingerprint = "aa:bb:cc"
        public_keys.extend([pk1, pk2])
        self.assertTrue(mgr.mCompareFingerPrints(siv_ok, public_keys))

        siv_miss = {"public_key_details": {"fingerprint": "xx:yy"}}
        self.assertFalse(mgr.mCompareFingerPrints(siv_miss, public_keys))

    @patch("exabox.ovm.vmboci.ExaOCIFactory")
    @patch("exabox.ovm.vmboci.get_instance_root_compartment", return_value="ocid.root")
    def test_master_key_fallback_to_kms_key_id(self, _girc, mock_factory):
        # Auto-generated test to verify _KEY_VMBOSS_OCID fallback to kms_key_id
        aOptions = self._valid_payload()
        # Ensure vmbackup.vmboss_key_ocid absent so kms_key_id is used
        # object storage namespace stub
        obj_cli = MagicMock()
        obj_cli.get_namespace.return_value = MagicMock(data="ns", request_id="req-1")
        mock_factory.return_value.get_object_storage_client.return_value = obj_cli
        mock_factory.return_value.get_identity_client.return_value = MagicMock()
        mock_factory.return_value.get_secrets_client.return_value = MagicMock()
        mock_factory.return_value.get_vault_client.return_value = MagicMock()

        mgr = ebVMBackupOCI(aOptions)
        self.assertEqual(mgr._KEY_VMBOSS_OCID, 'kms-ocid-123')

    def test_setup_dom0_cache_missing_config_raises(self):
        # Auto-generated negative path: missing crypto endpoint or master key triggers error
        mgr = ebVMBackupOCI.__new__(ebVMBackupOCI)
        # minimal attributes for method to run until config checks
        mgr._customer_nodes_details = tuple()
        mgr.CONFIG_CRYPTO_EP = "kms_dp_endpoint"
        mgr.CONFIG_MASTER_KEY_OCID = "kms_key_id"
        with patch("exabox.ovm.vmboci.get_gcontext") as gc:
            # Missing crypto endpoint
            gc.return_value.mGetConfigOptions.return_value = {}
            with self.assertRaises(ExacloudRuntimeError):
                mgr.mSetupVMBackupDom0Cache()
            # Present endpoint but missing key
            gc.return_value.mGetConfigOptions.return_value = {"kms_dp_endpoint": "ep"}
            with self.assertRaises(ExacloudRuntimeError):
                mgr.mSetupVMBackupDom0Cache()


if __name__ == '__main__':
    unittest.main()
