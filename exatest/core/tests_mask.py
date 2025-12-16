"""
$Header:

 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    test_cryptography.py - Base Class for cryptography testing

FUNCTION:
    Use this class when is necessary to test the cryptography methods

NOTE:
    None

History:

    MODIFIED   (MM/DD/YY)
    aypaul      04/29/25 - Add unit tests for isSensitiveParamsSalted.
    ndesanto    03/07/22 - Removed comented code
    ndesanto    05/03/19 - Creation of the file
"""

import base64
import unittest
from unittest import mock
from unittest.mock import patch

from exabox.exatest.common.ebExacloudUtil import ebExacloudUtil
from exabox.core.Mask import umask, mask, maskSensitiveData, umaskSensitiveData, checkifsaltedandb64encoded
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

class TestCryptography(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(TestCryptography, self).setUpClass(aGenerateDatabase=False)

        _PADDING = '.'
        _BLOCK_SIZE = 16
        self.__mask = "=$Y6_2RJ"
        self.__mask_ECB = "=$Y6_2RJkhJ.W`-v=#m/\"BX;H}Gf[aS^"
        self.__secret = "Secret1!!"
        self.__encrypted = "U2FsdGVkX1+2ZyJ6zjo3nZ5YkkKR4iUyUOo1+n4sd/lV5R9aco0qb8o="
        self.__encrypted_masked = "U2FsdGVkX189JFk2XzJSShgvKD5PSHxM/keBK+gomBgPZVmHs78ygjQ="
        self.__secret_ECB = "welcome1"
        self.__encrypted_ECB = "nnqdBcnEAGwiQG8SJEFOTQ=="
        self.__dict = {"user": "user", "passwd": self.__secret}
        self.__dict_masked_true = {"user": "user", "passwd": self.__encrypted}
        self.__dict_masked_false = {"user": "user", "passwd": "********"}
        self.__sensitive_fields = ["passwd","ssh_passphrase", "sshkey", "ssh_private_key", "root_spwd", "db_connstr"]
        self.__data_dict = {
            "ssh_passphrase": "<p^i#$6N", 
            "ssh_private_key": u"-----BEGIN RSA PRIVATE KEY-----\nProc-Type: 4,ENCRYPTED\nDEK-Info: DES-EDE3-CBC,43FB35F661ED9BC8\n\nfDLQ2gBEeQVQDfzmCdB3eAaX3fUrMao0okA87+LEXU7YWnmcZ8uMMxzBJZA1zF7n\nmlbY+6RuAb5yBkyGHbhRmqSYVaUfhCVXqpPeovMtFH8GIQIMND65XjbxPis1s8Ha\nP76JORGvyXt/exSppDNRTAD4gMfiUKxz0UTk+8V5l8A5FwNHhuGMHJaY+YxJd/GF\nYoXIIfxuaSTq9iQajBfMqsS/vRN3eEnwKFHxp71MiBYoGSSoe0NKPH0FQAkHTI1t\nu2KpH2pbkb6yiOcA5f+e5t262yWxrznr8C2oPOC4eOF4MatbI/Xg9F5IiZMi+1hr\nMDPZ9d5YX+uy/cOK1pZ4FvzF8SU3ZcpyXYPZQA5V/aca66btS/BmYHTQa6ZjkT+U\nVzQZ96J0VI4X1CTA3q3mG2A6Ek96O0vJw1VZb/5FEzkuo/VEBs4+OkS6cBqOyZCu\nFloHco700pSET6YaJ/UgpPmAdER+zCxhRH8SyMdG79qMupcQwQh61jfxAiJ1jcXr\nFMOmFZuuVHVCn8551PjWq2lgmLJrzQdPRUcJF0/i8b3jV7eLBdgs1RgVM8SBIuHI\nNEGrfqtAx/5Zwjk2SF4eT2tmeIMnt20BI9gX4wLg386yPfU9lOy/Bvalb2CcPIf/\nXPR68A88soFZscWNsJSAmEaz3hGZYNBWjRoUMaEtlFR9jZAXzpa7kv6nWU7z3ijd\nLtWGE5Y+0804iLaJP8TRbEFcf0J3CpDA0uAR5yW6isfGwzv9gL9/jQzm5k54wm/+\nXloubpL3jFoj9yP3J4mPCQEpCcxs/R5pAzA+QFh7y9AN+I9eP7H3sQ==",
            "ssh_public_key": u"ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAgQCGcEEhsYh94dk3bIeSCJXuaPg9r8tZT13EwQ5fIMM44U/0GA0oKO7R1k8t+kOppSng3e2N7Gay7QfguM21bIfgLL5bP2SgXe8ikoOK0LAlah52nqyOmCYNu1JcoR3hf41bZi02JuXOvXnZGZIvAHUu27Py7LSxQ6CVCJjlZBAoEQ== \n" 
        }
        self.__masked_dict = {
            "ssh_passphrase": "U2FsdGVkX18WT/rrXVvKF7XBkQPNiauoZex1rEMcgq3oLLLoUTY/Zg==", 
            "ssh_private_key": u"U2FsdGVkX187/Z62OQ8i53wznB48OoLQB/RoPhKK5bDV1gEowN6887NCvNGEvK0ya9ev4hqL1Zgzcw9hjOYnRlgDPnXIdDs0/lkceUVPLGsZHLASmi8KweqADLHglsU2UO5IreV3zD79Bx42OhmejOVAPQeBigQJcwarZ0t6xEqM//5cUAbRaMeRuxs0NT4w6h8L4Diq6e7eJ4si1cWJf7arXqn8yABOqY9ayA/kautnBnHPMN0V0+L4teHoI4AsBvBcUZGVaxC5YrHhP08s/LXbjXUUogthMAFeMCcJMoyEk3djnmqknQekPW+vxMAr81woaEIXsH5KfaEwwTy8ASnIRHKwyH1BoT4AY31XbLWsLKbHBPWtvFfx+aiRWHDX9RcqsZKzqiQv6p4VrAnP9DMfVyIsWsmLGZcZId46bI2Tynt6948L0YNoU9JDuX2hkAS5fEStMayeV2M9uXVwG77jEx1nmZdlifzy2XC0h3Wur+l552TSJePX/7cedzR+akGUQsw8gHnlzqXdCyyiVhY7+V3ffgkF/pvye9IQNvAATLDDz2l5L8J2ELtU6WbVbwBkAUiJjG+02IWJwouqjIST5Zvpqzkuwd2zF8Qz/BavEDmwnoKwt6Lw+lULNGFDGyztt83B5O4j0p/8/S3mi2l74xTzMC9j5Qi2KgmAbZ96wp4nyG2P8wc7fm38p4IaB8Bs/mjV8M5S37LZcxv1YeBQV+Qu4ssoBf2fM2x6+xyrXMwm7JcwP2anlftVNO3vDiv7vnZcumoMBl3zcTTnBUphBrvLI2RndoiPuyGkrtUjZM2jgoC/Sc9E+D7057YnnLI71ZHobdA6CFXwQDPCqtNyprjAnKI/MQk2I+3iilGKcc15V7mw8tVqsMYI7zMszGaD+gjsFAQEwpjieOhnr4qV5x6GzdpG2ntEXUrdF6uSVfe/n4yusJIE31A0VS+dzLQL7PZ0Usja8SymXzRcx5cGho4Lqup0sRibfll43CTGqoGUUK8SG2yRewPuuXa+YA8gFeDJ5sHUU+G+PDRDMVnD2iVcXA3Y33o1xGeow9r2MObXf9UKUkT+NKa/hHZ6neitgQN3JP5DHTAB23uEyNdFSi3dfS47XO+JiLvVDhn0K7LgKbCFsxL5rcroEpZoSoeEtU6v0VRsHNE96gZ1fJdTRXMIdYDhIy/FWNn6z17f7PVymWyMEUdIlCzs/WcmLS2NrEN+PgF6zqZ6sv+whXNFc8BdWfJItP7G9H9/tSLGtM5etWSmYoPUn763gsmjkeUlOQ==",
            "ssh_public_key": u"ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAgQCGcEEhsYh94dk3bIeSCJXuaPg9r8tZT13EwQ5fIMM44U/0GA0oKO7R1k8t+kOppSng3e2N7Gay7QfguM21bIfgLL5bP2SgXe8ikoOK0LAlah52nqyOmCYNu1JcoR3hf41bZi02JuXOvXnZGZIvAHUu27Py7LSxQ6CVCJjlZBAoEQ== \n"
        }
        self.__ssh_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCsgGKMQPSgqK2x4VHCD03fr58AxXZVVBVldi2oqyROU3rZ/XF2ZQoTcwSXtW1WlK/2VmF3DYXuceB9GzEBIe18WVkUAZpYqRPULVvfx1SKcyEvM3koeGexBO2xhBZ0A7K6SWyUjzQxRhzhhkfIUWwVyQ1o+XGJ6ueDMG0vvCjdmKdBoX7aO9dwDUC3P1OXgPmJgWLuqcik5KK4UhgZCcHdMib8Fo6z71T9sDNIMwsZ4QLS4moPcAiyI1iyQf4eQgq8TYnDfNhj57UCU3akQf0cBJxLLk9XzXILl5j8/vzzWLF7t6ze77c+9wFBvHFvvZIUnEMXL5bGOVkMthc/jGxH aime1@phxdbfbe41"

    @classmethod
    def tearDownClass(self):
        pass

    def test_encryption(self):
        new_mask = mask(self.__secret)
        new_umask = umask(new_mask)
        self.assertEqual(new_umask, self.__secret)

    def test_encryption_idempotent(self):
        masked = mask(self.__secret)
        new_mask = mask(masked)
        self.assertEqual(masked, new_mask)

    def test_encryption_with_mask(self):
        new_mask = mask(self.__secret, self.__mask)
        new_umask = umask(new_mask, self.__mask)
        self.assertEqual(new_umask, self.__secret)

    def test_decryption(self):
        new_umask = umask(self.__encrypted)
        self.assertEqual(new_umask, self.__secret)

    def test_decryption_ECB(self):
        new_umask = umask(self.__encrypted_ECB)
        self.assertEqual(new_umask, self.__secret_ECB)

    def test_decryption_with_mask(self):
        new_umask = umask(self.__encrypted_masked, self.__mask)
        self.assertEqual(new_umask, self.__secret)

    def test_maskSensitiveData(self):
        _data = maskSensitiveData(self.__dict, \
            sensitive_fields=self.__sensitive_fields, use_mask=True)
        _data_u = umaskSensitiveData(self.__dict_masked_true, \
            sensitive_fields=self.__sensitive_fields)
        self.assertEqual(self.__dict["passwd"], _data_u["passwd"])
        _data = maskSensitiveData(self.__dict, \
            sensitive_fields=self.__sensitive_fields, use_mask=False)
        self.assertEqual(_data["passwd"], self.__dict_masked_false["passwd"])

    def test_umaskSensitiveData(self):
        _data = umaskSensitiveData(self.__dict_masked_true, \
            sensitive_fields=self.__sensitive_fields)
        self.assertEqual(_data["passwd"], self.__dict["passwd"])

    def test_maskSensitiveDataFullMask(self):
        _data = maskSensitiveData(self.__dict, \
            sensitive_fields=self.__sensitive_fields, use_mask=True, full_mask=True)
        _undata = umaskSensitiveData(_data, \
            sensitive_fields=self.__sensitive_fields, full_mask=True)
        _redata = maskSensitiveData(_undata, \
            sensitive_fields=self.__sensitive_fields, use_mask=True, full_mask=True)
        self.assertEqual(_undata, self.__dict)
        
        _data = maskSensitiveData(self.__dict, \
            sensitive_fields=self.__sensitive_fields, use_mask=False, full_mask=True)
        _undata = umaskSensitiveData(_data, \
            sensitive_fields=self.__sensitive_fields, full_mask=True)
        _redata = maskSensitiveData(_undata, \
            sensitive_fields=self.__sensitive_fields, use_mask=False, full_mask=True)
        self.assertEqual(_undata, self.__dict_masked_false)

    def test_umaskSensitiveDataDict(self):
        _umasked = umaskSensitiveData(self.__masked_dict, self.__sensitive_fields)
        self.assertDictEqual(self.__data_dict, _umasked)

    def test_maskUmaskSSHKey(self):
        _masked = mask(self.__ssh_key)
        _umasked = umask(_masked)
        self.assertEqual(self.__ssh_key, _umasked)

    def test_umask_idempotent_if_not_base64_input(self):
        _umasked = umask(self.__ssh_key)
        self.assertEqual(self.__ssh_key, _umasked)

    def test_checkifsaltedandb64encoded(self):
        self.assertEqual(checkifsaltedandb64encoded(None), False)
        with patch('base64.b64decode', side_effect=iter([Exception])):
            self.assertEqual(checkifsaltedandb64encoded("mockstring"), False)
        self.assertEqual(checkifsaltedandb64encoded("bWNrc3Ry"), False) #plaintext value: mckstr 
        self.assertEqual(checkifsaltedandb64encoded("bW9ja2RhdGF2YWx1ZQ=="), False) #paintext value: mockdatavalue
        self.assertEqual(checkifsaltedandb64encoded("U2FsdGVkX19tb2NrZGF0YXZhbHVl"), True) #paintext value: Salted__mockdatavalue

def suite():
    """
    This method ensures the execution in the intended order of the tests.
    """
    suite = unittest.TestSuite()
    suite.addTest(TestCryptography("test_encryption"))
    suite.addTest(TestCryptography("test_encryption_idempotent"))
    suite.addTest(TestCryptography("test_encryption_with_mask"))
    suite.addTest(TestCryptography("test_decryption"))
    suite.addTest(TestCryptography("test_decryption_ECB"))
    suite.addTest(TestCryptography("test_decryption_with_mask"))
    suite.addTest(TestCryptography("test_maskSensitiveData"))
    suite.addTest(TestCryptography("test_umaskSensitiveData"))
    suite.addTest(TestCryptography("test_maskSensitiveDataFullMask"))
    suite.addTest(TestCryptography("test_umaskSensitiveDataDict"))
    suite.addTest(TestCryptography("test_maskUmaskSSHKey"))
    suite.addTest(TestCryptography("test_umask_idempotent_if_not_base64_input"))
    suite.addTest(TestCryptography("test_checkifsaltedandb64encoded"))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suite())

