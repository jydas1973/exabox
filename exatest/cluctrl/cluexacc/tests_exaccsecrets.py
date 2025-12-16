"""

 $Header: 

 Copyright (c) 2018, 2025, Oracle and/or its affiliates.

 NAME:
      tests_exaccSecrets.py - Unitest for ExaCC Secrets

 DESCRIPTION:
      Tests for ExaCC Secrets

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
        naps       04/21/25 - Bug 37508678 - UT updation for exaccsecrets.
        ndesanto   01/24/22 - Adding support for GCM AEAD encryption the new
                              Exacloud standard.
        ndesanto   08/21/20 - Removed decrypt test, decription is not supported
        vgerard    09/19/19 - Tests for ExaCC Secrets
"""

import os
import subprocess
import unittest
import json
import string
import tempfile
from base64 import b64encode
import operator

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.ovm.cluexaccsecrets import ebExaCCSecrets
from exabox.exatest.common.ebExacloudUtil import ebExacloudUtil, ebJsonObject
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebExacloudUtil import *
from exabox.kms.crypt import decrypt, cryptographyAES

class ebTestExaCC(ebTestClucontrol):
 
    @classmethod
    def setUpClass(self):
        super(ebTestExaCC, self).setUpClass(True,True,aResourceFolder='./exabox/exatest/common/resources/')
   	
    def setUp(self):
        #Ensure every test begin with standard conf
        self.mGetClubox()._exaBoxCluCtrl__ociexacc = False
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        self.exaccSecrets = ebExaCCSecrets(aDomUs=[],aMode=False)
   
    def test_mGeneratePassKey(self):
        """ test 200 keys """
        for _ in range(0,200):
            _key = self.exaccSecrets.mGeneratePassKey()
            self.assertTrue(all([x in string.printable for x in _key]))
            self.assertTrue(all([x not in string.whitespace for x in _key]))
            self.assertGreater(len(_key),64)
    
    def test_mEncrypt_GCM(self):
        _key = self.exaccSecrets.mGeneratePassKey()
        _secret = 'wehuiUW@@@ij_-3^c'
        _data = {'desc':'ExaCli initial password is:', 'data':_secret}
        _out = self.exaccSecrets.mEncryptData(json.dumps(_data), _key)
        # Test decryption with same key
        p = subprocess.Popen(['openssl','enc','-d','-aes-256-cbc','-md','sha512','-a','-pass', 'env:K'],
                              shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE,env={'K':_key})
        pt = wrapStrBytesFunctions(p).communicate(input=_out.encode('utf8'))[0]
        # Convert back JSON to dict and read secret
        self.assertEqual(json.loads(pt)['data'],_secret)

    def test_mEncrypt_CBC(self):
        _key = self.exaccSecrets.mGeneratePassKey()
        _secret = 'wehuiUW@@@ij_-3^c'
        _data = {'desc':'ExaCli initial password is:', 'data':_secret}
        _out = self.exaccSecrets.mEncryptData(json.dumps(_data), _key)
        # Test decryption with same key
        p = subprocess.Popen(['openssl','enc','-d','-aes-256-cbc','-md','sha512','-a','-pass', 'env:K'],
                              shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE,env={'K':_key})
        pt = wrapStrBytesFunctions(p).communicate(input=_out.encode('utf8'))[0]
        # Convert back JSON to dict and read secret
        self.assertEqual(json.loads(pt)['data'],_secret)

    def test_mPushExacliPasswdToDomUs_root(self):
        _cmds = {
            self.mGetRegexVm(): [[
                    exaMockCommand("/bin/scp *", aStdout="", aPersist=True, aRc=0),
                    exaMockCommand("chown opc *", aStdout="", aPersist=True, aRc=0),
                    exaMockCommand("chmod *", aStdout="", aPersist=True, aRc=0)
                ]],

            self.mGetRegexDom0(): [
                [  
                    exaMockCommand("/bin/scp *", aPersist=True, aRc=0)
                ]],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/scp *", aPersist=True, aRc=0)
                ]]
        }
        self.mPrepareMockCommands(_cmds)

        _secret = 'wehuiUW@@@ij_-3^c'
        _cluctrl = self.mGetClubox()
        _domUs = list(map(operator.itemgetter(1),_cluctrl.mReturnDom0DomUPair()))
        self.exaccSecrets = ebExaCCSecrets(aDomUs=_domUs,aMode=False)
        self.exaccSecrets.mPushExacliPasswdToDomUs(_secret)

    def test_mPushExacliPasswdToDomUs_opc(self):
        _cmds = {
            self.mGetRegexVm(): [[
                    exaMockCommand("/bin/scp *", aStdout="", aPersist=True, aRc=0),
                    exaMockCommand("chown opc *", aStdout="", aPersist=True, aRc=0),
                    exaMockCommand("chmod *", aStdout="", aPersist=True, aRc=0)
                ]],

            self.mGetRegexDom0(): [
                [  
                    exaMockCommand("/bin/scp *", aPersist=True, aRc=0)
                ]],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/scp *", aPersist=True, aRc=0)
                ]]
        }
        self.mPrepareMockCommands(_cmds)

        _secret = 'wehuiUW@@@ij_-3^c'
        _cluctrl = self.mGetClubox()
        _domUs = list(map(operator.itemgetter(1),_cluctrl.mReturnDom0DomUPair()))
        self.exaccSecrets = ebExaCCSecrets(aDomUs=_domUs,aMode=False)
        self.exaccSecrets.mPushExacliPasswdToDomUs(_secret,aUser="opc")


    def test_mPushExacliPasswdToDomUs_default(self):
        _cmds = {
            self.mGetRegexVm(): [[
                    exaMockCommand("/bin/scp *", aStdout="", aPersist=True, aRc=0),
                    exaMockCommand("chown opc *", aStdout="", aPersist=True, aRc=0),
                    exaMockCommand("chmod *", aStdout="", aPersist=True, aRc=0)
                ]],

            self.mGetRegexDom0(): [
                [   
                    exaMockCommand("/bin/scp *", aPersist=True, aRc=0)
                ]],
            self.mGetRegexLocal(): [
                [   
                    exaMockCommand("/bin/scp *", aPersist=True, aRc=0)
                ]]
        }
        self.mPrepareMockCommands(_cmds)

        _cluctrl = self.mGetClubox()
        _domUs = list(map(operator.itemgetter(1),_cluctrl.mReturnDom0DomUPair()))
        self.exaccSecrets = ebExaCCSecrets(aDomUs=_domUs,aMode=False)
        self.exaccSecrets.mPushExacliPasswdToDomUs(aPasswd=None)


if __name__ == '__main__':
    unittest.main()
