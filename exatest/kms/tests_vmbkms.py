#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/kms/tests_vmbkms.py $
#
# tests_vmbkms.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_vmbkms.py - Unit tests for VM backup KMS object store support
#
#    DESCRIPTION
#      ExaTest-compatible unit tests for exabox.kms.vmbkms.
#
#    NOTES
#      Keeps OCI and OpenSSL interactions mocked so the tests are hermetic.
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      06/15/26 - Creation
#

import json
import unittest
from unittest.mock import Mock, patch

from exabox.kms import vmbkms


OPENSSL_ERROR = "Failed to encrypt backup file using openssl"


class FakeOpenSslProcess(object):
    def __init__(self, aReturnCode=0, aCommunicateSideEffect=None):
        self.returncode = aReturnCode
        self.communicate = Mock(
            return_value=(b"", b""), side_effect=aCommunicateSideEffect
        )


class ebTestVmbKms(unittest.TestCase):

    def setUp(self):
        self._kms = vmbkms.ebKmsVmbObjectStore.__new__(
            vmbkms.ebKmsVmbObjectStore
        )
        self._kms._ebKmsVmbObjectStore__bkupdict = {}
        self._kms.mGenerateDataEncryptionKey = Mock(return_value="cipher-dek")
        self._kms.mDecryptData = Mock(return_value="plain-dek")
        self._kms.mUploadMultiPartFileObject = Mock(return_value="upload-ok")
        self._kms.mUploadObject = Mock(return_value="details-ok")

    def mAssertOpenSslCalled(self, aPopenMock, aInputFile):
        aPopenMock.assert_called_once()
        _args, _kwargs = aPopenMock.call_args

        self.assertEqual(
            _args[0],
            [
                "/usr/bin/openssl", "enc", "-aes-256-cbc", "-md", "sha256",
                "-in", aInputFile, "-out", aInputFile + ".enc", "-pass",
                "env:PASS", "-a"
            ]
        )
        self.assertFalse(_kwargs["shell"])
        self.assertEqual(_kwargs["env"], {"PASS": "plain-dek"})
        self.assertIs(_kwargs["stdin"], vmbkms.PIPE)
        self.assertIs(_kwargs["stdout"], vmbkms.PIPE)
        self.assertIs(_kwargs["stderr"], vmbkms.PIPE)

    def mAssertEncryptionStoppedBeforeUpload(self):
        self._kms.mUploadMultiPartFileObject.assert_not_called()
        self._kms.mUploadObject.assert_not_called()

    def test_mPutKms_encrypts_uploads_and_persists_details(self):
        _inputFile = "/tmp/vmbkms-test-backup"
        _process = FakeOpenSslProcess()

        with patch("exabox.kms.vmbkms.Popen", return_value=_process) as _popen:
            with patch(
                "exabox.kms.vmbkms.subprocess.check_output",
                return_value=b"encrypted-md5  /tmp/vmbkms-test-backup.enc\n"
            ) as _checkOutput:
                with patch("exabox.kms.vmbkms.ebLogInfo") as _logInfo:
                    self._kms.mPutKms("backup-object", _inputFile, "plain-md5")

        self._kms.mGenerateDataEncryptionKey.assert_called_once_with()
        self._kms.mDecryptData.assert_called_once_with("cipher-dek")
        self.mAssertOpenSslCalled(_popen, _inputFile)
        _process.communicate.assert_called_once_with()

        self._kms.mUploadMultiPartFileObject.assert_called_once_with(
            "backup-object", _inputFile + ".enc"
        )
        _checkOutput.assert_called_once_with(
            ["/usr/bin/md5sum", _inputFile + ".enc"]
        )

        self._kms.mUploadObject.assert_called_once()
        _detailsObject, _detailsPayload = self._kms.mUploadObject.call_args[0]
        self.assertEqual(_detailsObject, "backup-object.details")
        self.assertEqual(
            json.loads(_detailsPayload),
            {"dek": "cipher-dek", "hash": "plain-md5", "enchash": "encrypted-md5"}
        )
        self.assertEqual(
            json.loads(self._kms.mGetBkupDict())["enchash"], "encrypted-md5"
        )
        self.assertGreaterEqual(_logInfo.call_count, 2)

    def test_mPutKms_raises_generic_exception_when_openssl_launch_fails(self):
        with patch(
            "exabox.kms.vmbkms.Popen", side_effect=OSError("openssl missing")
        ) as _popen:
            with patch("exabox.kms.vmbkms.subprocess.check_output") as _checkOutput:
                with self.assertRaises(Exception) as _ctx:
                    self._kms.mPutKms("backup-object", "/tmp/input", "plain-md5")

        self.assertEqual(str(_ctx.exception), OPENSSL_ERROR)
        _popen.assert_called_once()
        _checkOutput.assert_not_called()
        self.mAssertEncryptionStoppedBeforeUpload()

    def test_mPutKms_raises_generic_exception_when_communicate_fails(self):
        _process = FakeOpenSslProcess(
            aCommunicateSideEffect=RuntimeError("pipe failed")
        )

        with patch("exabox.kms.vmbkms.Popen", return_value=_process) as _popen:
            with patch("exabox.kms.vmbkms.subprocess.check_output") as _checkOutput:
                with self.assertRaises(Exception) as _ctx:
                    self._kms.mPutKms("backup-object", "/tmp/input", "plain-md5")

        self.assertEqual(str(_ctx.exception), OPENSSL_ERROR)
        self.mAssertOpenSslCalled(_popen, "/tmp/input")
        _process.communicate.assert_called_once_with()
        _checkOutput.assert_not_called()
        self.mAssertEncryptionStoppedBeforeUpload()

    def test_mPutKms_raises_generic_exception_when_openssl_returns_failure(self):
        _process = FakeOpenSslProcess(aReturnCode=1)

        with patch("exabox.kms.vmbkms.Popen", return_value=_process) as _popen:
            with patch("exabox.kms.vmbkms.subprocess.check_output") as _checkOutput:
                with self.assertRaises(Exception) as _ctx:
                    self._kms.mPutKms("backup-object", "/tmp/input", "plain-md5")

        self.assertEqual(str(_ctx.exception), OPENSSL_ERROR)
        self.mAssertOpenSslCalled(_popen, "/tmp/input")
        _process.communicate.assert_called_once_with()
        _checkOutput.assert_not_called()
        self.mAssertEncryptionStoppedBeforeUpload()


if __name__ == "__main__":
    unittest.main(warnings="ignore")


# end file
