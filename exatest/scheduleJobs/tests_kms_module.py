#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/scheduleJobs/tests_kms_module.py /main/1 2025/11/18 03:55:10 shapatna Exp $
#
# tests_kms_module.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_kms_module.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    shapatna    11/11/25 - Enh 38574081: Add unit tests to improve the
#                           coverage using Cline
#    shapatna    11/11/25 - Creation
#
#!/bin/python
#
# tests_kms_module.py
#
# Unit tests for ebKmsObjectStore in kms_module.py
#

import os
import json
import unittest
import tempfile

from unittest import mock
from unittest.mock import Mock, patch, call

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.scheduleJobs.kms_module import ebKmsObjectStore


def _make_ctx(config=None):
    """
    Build a minimal viable context object where mGetConfigOptions().get(...) is used.
    """
    if config is None:
        config = {
            "kms_key_id": "ocid1.key.oc1..exampleuniqueID",
            "kms_dp_endpoint": "https://kms.example.com"
        }
    ctx = Mock()
    ctx.mGetConfigOptions.return_value = config
    return ctx


def _make_factory_mocks():
    """
    Create a mocked ExaOCIFactory with object storage and crypto clients wired up
    to return realistic primitive values/structures.
    """
    # Object Storage client
    obj_client = Mock()
    # get_namespace returns an object with .data being the namespace string
    obj_client.get_namespace.return_value = Mock(data="example-namespace")
    # delete/put return simple markers
    obj_client.delete_object.return_value = "DELETE_OK"
    obj_client.put_object.return_value = "PUT_OK"

    class _ObjGetResp:
        def __init__(self, content_bytes):
            self.data = Mock()
            self.data.content = content_bytes

    # Default get_object will be configured within tests as needed
    obj_client.get_object.return_value = _ObjGetResp(b'{"id_rsa.host.root": {"encDEK":"C1","encData":"E1"}}')
    # list_objects returns an object whose .data when str()&#x2F;json.loads produces a dict with 'objects'
    obj_client.list_objects.return_value = Mock(data='{"objects": [{"name": "obj1"}, {"name": "obj2"}]}')

    # KMS Crypto client
    crypto_client = Mock()
    crypto_client.generate_data_encryption_key.return_value = Mock(data='{"ciphertext": "CIPHERTEXT_SAMPLE"}')
    crypto_client.decrypt.return_value = Mock(data='{"plaintext": "PLAINTEXT_DEK_SAMPLE"}')

    # Factory
    factory = Mock()
    factory.get_object_storage_client.return_value = obj_client
    factory.get_crypto_client.return_value = crypto_client

    return factory, obj_client, crypto_client


class ebTestKmsModule(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        # Mirror reference tests setup style
        super(ebTestKmsModule, cls).setUpClass(True, False)

    @patch("exabox.scheduleJobs.kms_module.ExaOCIFactory")
    @patch("exabox.scheduleJobs.kms_module.cryptographyAES")
    def test_mEncryptKey_builds_expected_dict(self, mock_aes_cls, mock_factory_cls):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebKmsObjectStore.mEncryptKey")

        # Arrange
        factory, _, _ = _make_factory_mocks()
        mock_factory_cls.return_value = factory

        # AES mock
        mock_aes = Mock()
        # Return bytes; production decodes it as utf-8
        mock_aes.mEncrypt.return_value = b"ENCRYPTED_BYTES"
        mock_aes_cls.return_value = mock_aes

        ctx = _make_ctx()
        with tempfile.NamedTemporaryFile("wb", delete=False) as tf:
            tf.write(b"PRIVATE_KEY_BYTES")
            priv_path = tf.name
        try:
            kms = ebKmsObjectStore(ctx, bucketName="bucket-x")

            # Act
            result = kms.mEncryptKey(priv_path, {})

            # Assert
            base = os.path.basename(priv_path)
            self.assertIn(base, result)
            self.assertEqual(result[base]["encDEK"], "CIPHERTEXT_SAMPLE")
            self.assertEqual(result[base]["encData"], "ENCRYPTED_BYTES")
            ebLogInfo("Unit test on ebKmsObjectStore.mEncryptKey executed successfully")
        finally:
            try:
                os.unlink(priv_path)
            except Exception:
                pass

    @patch("exabox.scheduleJobs.kms_module.ExaOCIFactory")
    @patch("exabox.scheduleJobs.kms_module.cryptographyAES")
    def test_mDecryptPrivateData_returns_plain_bytes(self, mock_aes_cls, mock_factory_cls):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebKmsObjectStore.mDecryptPrivateData")

        factory, _, _ = _make_factory_mocks()
        mock_factory_cls.return_value = factory

        mock_aes = Mock()
        mock_aes.mDecrypt.return_value = b"PLAINTEXT_PRIVATE_KEY"
        mock_aes_cls.return_value = mock_aes

        ctx = _make_ctx()
        kms = ebKmsObjectStore(ctx)

        enc_element = {"encDEK": "ANY", "encData": "SOME_CIPHERTEXT"}
        rc, data = kms.mDecryptPrivateData(enc_element)
        self.assertIsNone(rc)
        self.assertEqual(data, b"PLAINTEXT_PRIVATE_KEY")
        ebLogInfo("Unit test on ebKmsObjectStore.mDecryptPrivateData executed successfully")

    @patch("exabox.scheduleJobs.kms_module.ExaOCIFactory")
    @patch("exabox.scheduleJobs.kms_module.cryptographyAES")
    @patch("os.chmod")
    @patch("os.path.exists", return_value=True)
    def test_mDecryptKey_writes_private_key_and_regenerates_pub(self, mock_exists, mock_chmod, mock_aes_cls, mock_factory_cls):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebKmsObjectStore.mDecryptKey")

        factory, _, _ = _make_factory_mocks()
        mock_factory_cls.return_value = factory

        mock_aes = Mock()
        mock_aes.mDecrypt.return_value = b"DECRYPTED_PRIVATE_KEY_CONTENT"
        mock_aes_cls.return_value = mock_aes

        ctx = _make_ctx()
        kms = ebKmsObjectStore(ctx)

        # Patch mRegeneratePubKey to avoid calling ssh-keygen
        with patch.object(ebKmsObjectStore, "mRegeneratePubKey") as mock_regen:
            with tempfile.TemporaryDirectory() as td:
                enc_keys = {
                    "id_rsa.host1.root": {
                        "encDEK": "C_TEXT",
                        "encData": "ENC_DATA"
                    },
                    "rack": "ignore-this-key"
                }
                # Act
                kms.mDecryptKey(enc_keys, aDir=td)

                # Assert private key file written
                priv_path = os.path.join(td, "id_rsa.host1.root")
                self.assertTrue(os.path.isfile(priv_path))
                with open(priv_path, "rb") as fp:
                    content = fp.read()
                self.assertEqual(content, b"DECRYPTED_PRIVATE_KEY_CONTENT")
                mock_chmod.assert_called_with(priv_path, 0o600)
                mock_regen.assert_called_once_with("id_rsa.host1.root", td)
                ebLogInfo("Unit test on ebKmsObjectStore.mDecryptKey executed successfully")

    @patch("exabox.scheduleJobs.kms_module.ExaOCIFactory")
    def test_mGetKey_invokes_mDecryptKey_with_parsed_payload(self, mock_factory_cls):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebKmsObjectStore.mGetKey")

        factory, obj_client, _ = _make_factory_mocks()
        mock_factory_cls.return_value = factory

        # Build get_object response with realistic content bytes
        payload = {"id_rsa.h2.root": {"encDEK": "C2", "encData": "E2"}}

        class _ObjGetResp:
            def __init__(self, content_bytes):
                self.data = Mock()
                self.data.content = content_bytes

        obj_client.get_object.return_value = _ObjGetResp(json.dumps(payload).encode("utf-8"))

        ctx = _make_ctx()
        kms = ebKmsObjectStore(ctx)
        with patch.object(ebKmsObjectStore, "mDecryptKey", return_value=None) as mock_dec:
            rc, res = kms.mGetKey("clusterA", aDir="/tmp/somedir")
            self.assertEqual(rc, 0)
            self.assertEqual(res, None)  # mDecryptKey returns None; wrapper returns (0, None)
            # The method itself returns (0, self.mDecryptKey(...)) so verify call arguments
            mock_dec.assert_called_once()
            call_args = mock_dec.call_args[0]
            self.assertIsInstance(call_args[0], dict)
            self.assertIn("id_rsa.h2.root", call_args[0])
            self.assertEqual(call_args[1], "/tmp/somedir")
            ebLogInfo("Unit test on ebKmsObjectStore.mGetKey executed successfully")

    @patch("exabox.scheduleJobs.kms_module.ExaOCIFactory")
    def test_mObjectAvailable_success_and_mGetObject_fail(self, mock_factory_cls):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebKmsObjectStore.mObjectAvailable")

        factory, obj_client, _ = _make_factory_mocks()
        mock_factory_cls.return_value = factory

        ctx = _make_ctx()
        kms = ebKmsObjectStore(ctx)

        class _ObjGetResp:
            def __init__(self, content_bytes):
                self.data = Mock()
                self.data.content = content_bytes

        # Success case
        obj_client.get_object.return_value = _ObjGetResp(b'{"somekey": {"encDEK": "X", "encData": "Y"}}')
        with patch.object(ebKmsObjectStore, "mGetObject", return_value=(0, obj_client.get_object("", "", ""))):
            d = kms.mObjectAvailable("whatever")
            self.assertIn("somekey", d)

        # Failure case returns empty dict
        with patch.object(ebKmsObjectStore, "mGetObject", return_value=(1, "error")):
            d = kms.mObjectAvailable("whatever")
            self.assertEqual(d, {})
        ebLogInfo("Unit test on ebKmsObjectStore.mObjectAvailable executed successfully")

    @patch("exabox.scheduleJobs.kms_module.ExaOCIFactory")
    def test_mDeleteObject_and_mUploadObject_success_and_exception(self, mock_factory_cls):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebKmsObjectStore.mDeleteObject/mUploadObject")

        factory, obj_client, _ = _make_factory_mocks()
        mock_factory_cls.return_value = factory

        ctx = _make_ctx()
        kms = ebKmsObjectStore(ctx)

        # Success paths
        rc, resp = kms.mDeleteObject("obj-x")
        self.assertEqual(rc, 0)
        self.assertEqual(resp, "DELETE_OK")
        rc, resp = kms.mUploadObject("obj-x", "data")
        self.assertEqual(rc, 0)
        self.assertEqual(resp, "PUT_OK")

        # Exception paths
        obj_client.delete_object.side_effect = Exception("boom-del")
        obj_client.put_object.side_effect = Exception("boom-put")
        rc, resp = kms.mDeleteObject("obj-y")
        self.assertEqual(rc, 1)
        self.assertIn("boom-del", str(resp))
        rc, resp = kms.mUploadObject("obj-y", "data")
        self.assertEqual(rc, 1)
        self.assertIn("boom-put", str(resp))
        ebLogInfo("Unit test on ebKmsObjectStore.mDeleteObject/mUploadObject executed successfully")

    @patch("exabox.scheduleJobs.kms_module.ExaOCIFactory")
    @patch.object(ebKmsObjectStore, "mExecuteLocal")
    def test_mRegeneratePubKey_writes_pub_and_chmod(self, mock_exec_local, mock_factory_cls):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebKmsObjectStore.mRegeneratePubKey")

        factory, _, _ = _make_factory_mocks()
        mock_factory_cls.return_value = factory

        ctx = _make_ctx()
        kms = ebKmsObjectStore(ctx)

        # mExecuteLocal is called twice; first returns stdout to be written to .pub
        mock_exec_local.side_effect = [
            (0, "SSH_RSA_PUBLIC_CONTENT", ""),  # ssh-keygen -y
            (0, "", "")                          # chmod 0600
        ]

        with tempfile.TemporaryDirectory() as td:
            # Prepare a private key file with expected name
            priv_basename = "id_rsa.host3.root"
            priv_full = os.path.join(td, priv_basename)
            with open(priv_full, "w") as fp:
                fp.write("PRIVATE")

            kms.mRegeneratePubKey(priv_basename, td + os.sep)

            pub_path = priv_full + ".pub"
            self.assertTrue(os.path.isfile(pub_path))
            with open(pub_path, "r") as fp:
                content = fp.read()
            self.assertEqual(content, "SSH_RSA_PUBLIC_CONTENT")
            # Ensure chmod command was invoked (second call)
            self.assertEqual(mock_exec_local.call_count, 2)
            ebLogInfo("Unit test on ebKmsObjectStore.mRegeneratePubKey executed successfully")

    @patch("exabox.scheduleJobs.kms_module.ExaOCIFactory")
    def test_mExportKeys_present_and_missing(self, mock_factory_cls):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebKmsObjectStore.mExportKeys")

        factory, _, _ = _make_factory_mocks()
        mock_factory_cls.return_value = factory

        ctx = _make_ctx()
        kms = ebKmsObjectStore(ctx)

        with tempfile.TemporaryDirectory() as td:
            # Ensure trailing slash to match production concatenation pattern
            td_slash = td + os.sep

            # Override cluster key dir to our temp location
            with patch.object(ebKmsObjectStore, "mGetClusterKeyDir", return_value=td_slash):
                # Present case: create the expected key file
                hostname = "host4.example.com"
                key_name = "id_rsa.host4.root"
                key_path = os.path.join(td_slash, key_name)
                with open(key_path, "w") as fp:
                    fp.write("PRIVATE")

                with patch.object(ebKmsObjectStore, "mPutKey", return_value=(0, "OK")) as mock_put, \
                     patch.object(ebKmsObjectStore, "mDeleteOndiskKeys") as mock_del:
                    kms.mExportKeys(hostname)
                    # Production concatenates keysdir + key_name (keysdir already ends with slash)
                    mock_put.assert_called_once_with(hostname, td_slash + key_name)
                    mock_del.assert_called_once()

                # Missing case: ensure file removed
                try:
                    os.unlink(key_path)
                except FileNotFoundError:
                    pass
                with patch.object(ebKmsObjectStore, "mPutKey") as mock_put, \
                     patch.object(ebKmsObjectStore, "mDeleteOndiskKeys") as mock_del:
                    kms.mExportKeys(hostname)
                    mock_put.assert_not_called()
                    mock_del.assert_called_once()
        ebLogInfo("Unit test on ebKmsObjectStore.mExportKeys executed successfully")


if __name__ == '__main__':
    unittest.main()
