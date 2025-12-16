"""

 $Header: ecs/exacloud/exabox/exatest/cluctrl/kms/tests_encrypt_decrypt.py /main/4 2022/02/23 11:47:47 ndesanto Exp $

 Copyright (c) 2020, 2022, Oracle and/or its affiliates.

    NAME
      tests_encrypt_decrypt.py - <one-line expansion of the name>

    DESCRIPTION
      Run tests for the class cryptographyAES using Unitest

    NOTES
      <other useful comments, qualifications, etc.>

    MODIFIED   (MM/DD/YY)
    ndesanto    12/21/21 - Security requested the change of cipher
    gsundara    12/07/20 - Creation
"""

import base64
import unittest
from exabox.kms.crypt import decrypt, cryptographyAES, cryptographyAES_CBC


class TestcryptographyAES(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.__crypt = cryptographyAES()
        self.__passphrase = base64.b64decode("V2VsY29tZTEK")
        self.__plaintext = "Hello World!"
        # This text is "Hello World!" encrypted in CBC (old cipher)
        self.__cbc_encrypted = "U2FsdGVkX1+S5927fbF2XmBVXZTiC22XkFgwB3sIZpE="

    @classmethod
    def tearDownClass(self):
        pass

    def test_encrypt_decrypt(self):
        enc_data = self.__crypt.mEncrypt(self.__passphrase, self.__plaintext.encode("ascii")).decode("utf-8")
        dec_data = self.__crypt.mDecrypt(self.__passphrase, enc_data).decode("utf-8")
        self.assertEqual(self.__plaintext, dec_data)

    def test_decrypt_cbc_failure(self):
        """
        This test uses the decrypt method directly, this methods implements 
        the new GCM decryption algorihtm and will not be able to decrypt 
        text encrypted with the previous method.
        """
        with self.assertRaises(Exception):
            dec_data = decrypt(self.__passphrase, self.__cbc_encrypted).decode("utf-8")

    def test_decrypt_fallback(self):
        """
        This method uses the class implementation of decrypt that includes the 
        code to fallback into the previous method.
        """
        dec_data = self.__crypt.mDecrypt(self.__passphrase, self.__cbc_encrypted).decode("utf-8")
        self.assertEqual(self.__plaintext, dec_data)

    def test_not_implemented(self):
        _cbc = cryptographyAES_CBC()
        with self.assertRaises(NotImplementedError):
            enc_data = _cbc.mEncrypt(self.__passphrase, self.__plaintext.encode("ascii")).decode("utf-8")

if __name__ == "__main__":
    unittest.main()
