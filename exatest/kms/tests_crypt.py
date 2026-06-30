#!/bin/python
#
# $Header: tests_crypt.py 18-jun-2026.05:27:39 aypaul   Exp $
#
# tests_crypt.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_crypt.py - Tests for the cryptographyAES wrapper
#
#    DESCRIPTION
#      Unit tests for AES-GCM encryption and decryption behavior exposed by
#      exabox.kms.crypt.cryptographyAES.
#
#    NOTES
#      Run with exatest/exatest.py -r -f exatest/kms/tests_crypt.py
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      06/18/26 - Creation
#

import base64
import unittest

from exabox.core.Error import ExacloudRuntimeError
from exabox.kms.crypt import cryptographyAES


class TestCryptographyAES(unittest.TestCase):

    PASSPHRASE = base64.b64decode("V2VsY29tZTEK")
    TEXT_PASSPHRASE = "Welcome1"
    WRONG_PASSPHRASE = b"not-the-passphrase"
    PLAINTEXT = b"Hello World!"
    LEGACY_CBC_ENCRYPTED = "U2FsdGVkX1+S5927fbF2XmBVXZTiC22XkFgwB3sIZpE="

    def setUp(self):
        self.crypto = cryptographyAES()

    def _encrypt_as_text(self, password=None, plaintext=None, chunkit=True):
        if password is None:
            password = self.PASSPHRASE
        if plaintext is None:
            plaintext = self.PLAINTEXT

        encrypted = self.crypto.mEncrypt(password, plaintext, chunkit)
        self.assertIsInstance(encrypted, bytes)
        return encrypted.decode("ascii")

    def test_mEncrypt_returns_base64_salted_aes_gcm_payload(self):
        encrypted = self.crypto.mEncrypt(self.PASSPHRASE, self.PLAINTEXT)

        self.assertIsInstance(encrypted, bytes)
        raw = base64.b64decode(encrypted, validate=True)
        self.assertEqual(b"Salted__", raw[:8])
        self.assertEqual(8, len(raw[8:16]))
        self.assertEqual(16 + len(self.PLAINTEXT) + 16, len(raw))

    def test_mEncrypt_allows_chunkit_false_for_compatibility(self):
        encrypted = self._encrypt_as_text(chunkit=False)

        self.assertEqual(self.PLAINTEXT,
                         self.crypto.mDecrypt(self.PASSPHRASE, encrypted))

    def test_mEncrypt_accepts_text_passwords(self):
        encrypted = self._encrypt_as_text(password=self.TEXT_PASSPHRASE)

        self.assertEqual(self.PLAINTEXT,
                         self.crypto.mDecrypt(self.TEXT_PASSPHRASE,
                                              encrypted))

    def test_mDecrypt_returns_plaintext_for_valid_ciphertext(self):
        encrypted = self._encrypt_as_text()

        self.assertEqual(self.PLAINTEXT,
                         self.crypto.mDecrypt(self.PASSPHRASE, encrypted))

    def test_mDecrypt_ignores_blank_lines_and_comments(self):
        encrypted = self._encrypt_as_text()
        mid = len(encrypted) // 2
        wrapped = "\n# ignored comment\n  %s\n\n# another comment\n%s\n" % (
            encrypted[:mid], encrypted[mid:])

        self.assertEqual(self.PLAINTEXT,
                         self.crypto.mDecrypt(self.PASSPHRASE, wrapped))

    def test_mDecrypt_raises_error_for_wrong_password(self):
        encrypted = self._encrypt_as_text()

        with self.assertRaisesRegex(ExacloudRuntimeError,
                                    "Decryption failed"):
            self.crypto.mDecrypt(self.WRONG_PASSPHRASE, encrypted)

    def test_mDecrypt_raises_error_for_invalid_payload(self):
        with self.assertRaisesRegex(ExacloudRuntimeError,
                                    "Incorrect padding"):
            self.crypto.mDecrypt(self.PASSPHRASE, "not valid ciphertext")

    def test_mDecrypt_does_not_fallback_to_legacy_cbc(self):
        with self.assertRaisesRegex(ExacloudRuntimeError,
                                    "Decryption failed"):
            self.crypto.mDecrypt(self.PASSPHRASE,
                                 self.LEGACY_CBC_ENCRYPTED)


if __name__ == "__main__":
    unittest.main()
