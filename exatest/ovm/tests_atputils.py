#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_atputils.py /main/2 2025/06/26 18:22:18 jfsaldan Exp $
#
# tests_atputils.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_atputils.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    05/28/25 - Bug 37945713 - ADBD: OBSERVING WRONG PERMISSIONS IN
#                           /OPT/EXACLOUD DIRECTORY FOR FILES ATP.INI,
#                           NODES.JSON AND GET_CS_DATA.PY
#    aararora    07/03/22 - Creation
#

import unittest

from unittest.mock import patch

from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.AtpUtils import ebAtpUtils

SCAN_NAME = "SCAN name: scaqak01dvclu06-scan1, Network: 1"
DOMAIN_NAME = "us.oracle.com"
SCAN_FQDN_NAME = "SCAN name: scaqak01dvclu06-scan1.us.oracle.com, Network: 1"

class testOptions(object): pass

class ebTestAtpUtils(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestAtpUtils, self).setUpClass(False,False)
    
    def test_setScanFqdn(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario unit test on AtpUtils.setScanFqdn.")

        mockCommands = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("cat /etc/oratab *", aRc=0, aStdout="+ASM2:/u01/app/19.0.0.0/gridHome2:N", aPersist=True)
                ],
                [
                    exaMockCommand("/u01/app/19.0.0.0/gridHome2/bin/srvctl config scan *", aRc=0, aStdout=SCAN_NAME),
                    exaMockCommand("/bin/hostname", aRc=0, aPersist=True, aStdout=DOMAIN_NAME),
                    exaMockCommand("/u01/app/19.0.0.0/gridHome2/bin/srvctl modify scan *", aRc=0, aPersist=True),
                    exaMockCommand("/u01/app/19.0.0.0/gridHome2/bin/srvctl config scan *", aRc=0, aStdout=SCAN_FQDN_NAME)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)
        ebAtpUtils.setScanFqdn([(None,'scaqab10adm07vm02.us.oracle.com'), (None,'scaqab10adm08vm02.us.oracle.com')])

    def test_setScanFqdnError(self):
        ebLogInfo("")
        ebLogInfo("Running error scenario unit test on AtpUtils.setScanFqdn.")

        mockCommands = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("cat /etc/oratab *", aRc=0, aStdout="+ASM2:/u01/app/19.0.0.0/gridHome2:N", aPersist=True)
                ],
                [
                    exaMockCommand("/u01/app/19.0.0.0/gridHome2/bin/srvctl config scan *", aRc=0, aStdout=SCAN_NAME),
                    exaMockCommand("/bin/hostname", aRc=0, aPersist=True, aStdout=DOMAIN_NAME),
                    exaMockCommand("/u01/app/19.0.0.0/gridHome2/bin/srvctl modify scan *", aRc=0, aPersist=True),
                    exaMockCommand("/u01/app/19.0.0.0/gridHome2/bin/srvctl config scan *", aRc=0, aStdout=SCAN_NAME)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)
        ebAtpUtils.setScanFqdn([(None,'scaqab10adm07vm02.us.oracle.com'), (None,'scaqab10adm08vm02.us.oracle.com')])

    def test_setScanFqdnAlreadyFqdn(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario unit test on AtpUtils.setScanFqdn where scan name is already in fqdn format.")

        mockCommands = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("cat /etc/oratab *", aRc=0, aStdout="+ASM2:/u01/app/19.0.0.0/gridHome2:N", aPersist=True)
                ],
                [
                    exaMockCommand("/u01/app/19.0.0.0/gridHome2/bin/srvctl config scan *", aRc=0, aStdout=SCAN_FQDN_NAME),
                    exaMockCommand("/bin/hostname", aRc=0, aPersist=True, aStdout=DOMAIN_NAME)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)
        ebAtpUtils.setScanFqdn([(None,'scaqab10adm07vm02.us.oracle.com'), (None,'scaqab10adm08vm02.us.oracle.com')])

    def test_mWriteAtpIniFile(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario unit test on AtpUtils.mWriteAtpIniFile")

        mockCommands = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("[ ! -e /opt/exacloud ] && mkdir -p /opt/exacloud", aRc=0),
                    exaMockCommand("/bin/scp /tmp/atp_scaqab10client01vm08.us.oracle.com.ini /opt/exacloud/atp.ini", aRc=0),
                    exaMockCommand("/bin/scp /tmp/atp_scaqab10client02vm08.us.oracle.com.ini /opt/exacloud/atp.ini", aRc=0),
                    exaMockCommand("test -e /bin/chmod", aRc=0),
                    exaMockCommand("/bin/chmod 644 /opt/exacloud/atp.ini", aRc=0)
                ],
            ]
        }

        self.mPrepareMockCommands(mockCommands)
        _dict = {"somekey":"somval"}
        _ebox = self.mGetClubox()
        for _, _domU in _ebox.mReturnDom0DomUPair():
            self.assertEqual(None, ebAtpUtils.mWriteAtpIniFile(_dict, _domU))

    def test_mWriteAtpNamespaceFile(self):
        ebLogInfo("")
        ebLogInfo("Running success scenario unit test on AtpUtils.mWriteAtpNamespaceFile")

        mockCommands = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("[ ! -e /opt/exacloud ] && mkdir -p /opt/exacloud", aRc=0),
                    exaMockCommand("/bin/scp /tmp/nodes_scaqab10client01vm08.us.oracle.com.ini /opt/exacloud/nodes.json", aRc=0),
                    exaMockCommand("/bin/scp /tmp/nodes_scaqab10client02vm08.us.oracle.com.ini /opt/exacloud/nodes.json", aRc=0),
                    exaMockCommand("test -e /bin/chmod", aRc=0),
                    exaMockCommand("/bin/chmod 644 /opt/exacloud/nodes.json", aRc=0)
                ],
            ]
        }

        self.mPrepareMockCommands(mockCommands)
        _dict = {"somekey":"somval"}
        _ebox = self.mGetClubox()
        for _, _domU in _ebox.mReturnDom0DomUPair():
            self.assertEqual(None, ebAtpUtils.mWriteAtpNamespaceFile(_dict, _domU))


if __name__ == '__main__':
    unittest.main() 
