#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/scheduleJobs/tests_kms_module.py /main/1 2025/11/18 03:55:10 shapatna Exp $
#
# tests_kms_module.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
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
#    aypaul      04/16/26 - Bug#38900303 Fix unit tests for codev identified issues
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

import six
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.scheduleJobs.kms_module import ebKmsObjectStore

if not hasattr(six, "ensure_binary"):
    def _ensure_binary(value, encoding='utf-8', errors='strict'):
        if isinstance(value, bytes):
            return value
        return str(value).encode(encoding, errors)

    def _ensure_text(value, encoding='utf-8', errors='strict'):
        if isinstance(value, bytes):
            return value.decode(encoding, errors)
        return str(value)

    six.ensure_binary = _ensure_binary
    six.ensure_text = _ensure_text
    six.ensure_str = _ensure_text


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

    @patch("exabox.scheduleJobs.kms_module.ExaOCIFactory")
    def test_helper_accessors(self, mock_factory_cls):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebKmsObjectStore helper accessors")

        factory, _, _ = _make_factory_mocks()
        mock_factory_cls.return_value = factory

        ctx = _make_ctx()
        kms = ebKmsObjectStore(ctx)

        aes = kms.mGetAES()
        keys_dir = kms.mGetClusterKeyDir()
        self.assertIsNotNone(aes)
        self.assertTrue(keys_dir.endswith("/clusters/keys/"))
        ebLogInfo("Helper accessor test executed successfully")

    @patch("exabox.scheduleJobs.kms_module.wrapStrBytesFunctions")
    @patch("exabox.scheduleJobs.kms_module.Popen")
    @patch("exabox.scheduleJobs.kms_module.ExaOCIFactory")
    def test_mExecuteLocal_invokes_subprocess(self, mock_factory_cls, mock_popen, mock_wrap):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebKmsObjectStore.mExecuteLocal")

        factory, _, _ = _make_factory_mocks()
        mock_factory_cls.return_value = factory

        proc = Mock()
        proc.returncode = 7
        mock_popen.return_value = proc
        mock_wrap.return_value.communicate.return_value = ("stdout", "stderr")

        ctx = _make_ctx()
        kms = ebKmsObjectStore(ctx)

        rc, stdout, stderr = kms.mExecuteLocal("echo hi", aCurrDir="/tmp")
        self.assertEqual(rc, 7)
        self.assertEqual(stdout, "stdout")
        self.assertEqual(stderr, "stderr")
        mock_popen.assert_called_once()
        mock_wrap.assert_called_once()
        ebLogInfo("mExecuteLocal executed successfully")

    @patch("exabox.scheduleJobs.kms_module.ExaOCIFactory")
    def test_mDeleteOndiskKeys_invokes_execute_local(self, mock_factory_cls):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebKmsObjectStore.mDeleteOndiskKeys")

        factory, _, _ = _make_factory_mocks()
        mock_factory_cls.return_value = factory

        ctx = _make_ctx()
        kms = ebKmsObjectStore(ctx)
        cluster_dir = kms.mGetClusterKeyDir()

        with patch.object(ebKmsObjectStore, "mExecuteLocal") as mock_exec:
            kms.mDeleteOndiskKeys("id_rsa.test.root")
            self.assertEqual(mock_exec.call_count, 2)
            self.assertEqual(mock_exec.call_args_list[0].kwargs["aCurrDir"], cluster_dir)
            self.assertIn("id_rsa.test.root", mock_exec.call_args_list[0].args[0])
            self.assertIn("id_rsa.test.root.pub", mock_exec.call_args_list[1].args[0])
        ebLogInfo("mDeleteOndiskKeys executed successfully")

    @patch("exabox.scheduleJobs.kms_module.ExaOCIFactory")
    def test_mListObjects_success_and_failure(self, mock_factory_cls):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebKmsObjectStore.mListObjects")

        factory, obj_client, _ = _make_factory_mocks()
        mock_factory_cls.return_value = factory

        ctx = _make_ctx()
        kms = ebKmsObjectStore(ctx)

        rc, objects = kms.mListObjects()
        self.assertEqual(rc, 0)
        self.assertEqual(len(objects), 2)

        obj_client.list_objects.side_effect = Exception("boom")
        rc, msg = kms.mListObjects()
        self.assertEqual(rc, 1)
        self.assertIn("boom", msg)
        ebLogInfo("mListObjects executed successfully")

    @patch.object(ebKmsObjectStore, "mUploadObject", return_value=(0, "OK"))
    @patch.object(ebKmsObjectStore, "mEncryptKey", return_value={"key": {"encDEK": "a", "encData": "b"}})
    @patch("exabox.scheduleJobs.kms_module.ExaOCIFactory")
    def test_mPutKey_uploads_encrypted_payload(self, mock_factory_cls, mock_encrypt, mock_upload):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebKmsObjectStore.mPutKey")

        factory, _, _ = _make_factory_mocks()
        mock_factory_cls.return_value = factory

        ctx = _make_ctx()
        kms = ebKmsObjectStore(ctx)
        rc, resp = kms.mPutKey("object", "/tmp/key")
        self.assertEqual(rc, 0)
        self.assertEqual(resp, "OK")
        mock_encrypt.assert_called_once()
        mock_upload.assert_called_once()
        ebLogInfo("mPutKey executed successfully")

    @patch.object(ebKmsObjectStore, "mGetKey", return_value=(0, None))
    @patch("exabox.scheduleJobs.kms_module.ExaOCIFactory")
    def test_mImportKeys_invokes_get_key(self, mock_factory_cls, mock_get_key):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebKmsObjectStore.mImportKeys")

        factory, _, _ = _make_factory_mocks()
        mock_factory_cls.return_value = factory

        ctx = _make_ctx()
        kms = ebKmsObjectStore(ctx)
        kms.mImportKeys("host.example.com", aDir="/tmp")
        mock_get_key.assert_called_once_with("host.example.com", "/tmp")
        ebLogInfo("mImportKeys executed successfully")

    @patch.object(ebKmsObjectStore, "mDeleteObject", return_value=(0, "deleted"))
    @patch("exabox.scheduleJobs.kms_module.ExaOCIFactory")
    def test_mDeleteKeys_invokes_delete_object(self, mock_factory_cls, mock_delete):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebKmsObjectStore.mDeleteKeys")

        factory, _, _ = _make_factory_mocks()
        mock_factory_cls.return_value = factory

        ctx = _make_ctx()
        kms = ebKmsObjectStore(ctx)
        rc, resp = kms.mDeleteKeys("cluster")
        self.assertEqual(rc, 0)
        self.assertEqual(resp, "deleted")
        mock_delete.assert_called_once_with("cluster")
        ebLogInfo("mDeleteKeys executed successfully")


if __name__ == '__main__':
    unittest.main()
