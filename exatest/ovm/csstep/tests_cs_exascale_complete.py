#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/tests_cs_exascale_complete.py /main/4 2025/11/25 05:03:58 prsshukl Exp $
#
# tests_cs_exascale_complete.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_exascale_complete.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    naps        07/03/25 - Bug 38116390 - copy weblogic cert for R1 env.
#    gparada     08/30/23 - Creation
#

import unittest

from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.csstep.cs_exascale_complete import csExaScaleComplete
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.cluexascale import ebCluExaScale

from unittest.mock import patch

class ebTestCsExascaleComplete(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def test_updDomUsToJdk11(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for CsExascaleComplete.updDomUsToJdk11")
        _fileExist = "/bin/test -e"
        _java11 = "/usr/lib/jvm/jdk-11-oracle-x64/bin/java"
        _javac11 = "/usr/lib/jvm/jdk-11-oracle-x64/bin/java"
        _updAlt = ".*update-alternatives"
        _set_java = "--set java"
        _set_javac = "--set javac"


        mockCommands = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand(f"{_fileExist} {_java11}",aRc=0),
                    exaMockCommand(f"{_fileExist} {_updAlt}",aRc=0),
                    exaMockCommand(f"{_updAlt} {_set_java} {_java11}",aRc=0),
                    exaMockCommand(f"{_updAlt} {_set_javac} {_javac11}",aRc=0)
                ]
            ]            
        }
        self.mPrepareMockCommands(mockCommands)
        csExaScaleCompleteInstance = csExaScaleComplete()
        _ebox = self.mGetClubox()
        csExaScaleCompleteInstance.updDomUsToJdk11(_ebox)


    def test_doExecuteBaseDB_cert_unavailable(self):
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/usr/bin/curl.*", aPersist=True),
                ]
            ],
            self.mGetRegexDom0():
                [[
                    exaMockCommand("/bin/stat.*", aRc=0,  aPersist=True)
                ]]
        }
        self.mGetContext().mSetConfigOption("weblogic_cert", {"Enabled": "True", "weblogic_cert_localpath": "config/weblogic.jks", "weblogic_cert_oss_link": "https://objectstorage.us", "weblogic_cert_vmpath": "/opt/oracle/dcs/rdbaas/config/weblogic.jks"})
        self.mPrepareMockCommands(_cmds)

        _exascale = ebCluExaScale(self.mGetClubox())

        _step = csExaScaleComplete()
        _options = self.mGetClubox().mGetOptions()
        with self.assertRaises(ExacloudRuntimeError):
            _exascale.mCopyWeblogicCert()


    @patch('exabox.core.Node.exaBoxNode.mCopyFile', return_value=1)
    def test_doExecuteBaseDB_cert_scp_fail(self, aCopy):
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/usr/bin/curl.*", aRc=0, aPersist=True),
                ]
            ],
            self.mGetRegexDom0():
                [[
                    exaMockCommand("/bin/stat.*", aRc=0,  aPersist=True)
                ]],
            self.mGetRegexVm():
                [[
                   exaMockCommand("/bin/test -e.*", aRc=1,  aPersist=True)
                ]]
        }
        self.mGetContext().mSetConfigOption("weblogic_cert", {"Enabled": "True", "weblogic_cert_localpath": "config/weblogic.jks", "weblogic_cert_oss_link": "https://objectstorage.us", "weblogic_cert_vmpath": "/opt/oracle/dcs/rdbaas/config/weblogic.jks"})
        self.mPrepareMockCommands(_cmds)
        _exascale = ebCluExaScale(self.mGetClubox())

        _step = csExaScaleComplete()
        _options = self.mGetClubox().mGetOptions()
        with patch('os.path.exists', return_value=True):
            with self.assertRaises(ExacloudRuntimeError):
                _exascale.mCopyWeblogicCert()

if __name__ == '__main__':
    unittest.main() 
