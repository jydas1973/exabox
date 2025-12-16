#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/tools/xml_generation/tests_xml_generation.py /main/24 2025/11/15 11:40:55 joysjose Exp $
#
# tests_xml_generation.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_xml_generation.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    08/20/25 - Bug 38299487 - ECS_MAIN -> ETF -> NSLOOKUP COMMAND
#                           IS SENDING RETURN STATUS 1 , CAUSING
#                           TESTS_LACP_XML_GENERATION_PY.DIF AND
#                           TESTS_XML_GENERATION_PY.DIF TO FAIL
#    prsshukl    11/20/24 - Bug 37302755 - ETF: ECS_MAIN : DISABLE
#                           TESTS_XML_GENERATION_PY UNITTEST
#    aararora    08/30/24 - Bug 36998256: IPv6 fixes
#    jesandov    10/16/23 - 35729701: Support of OL7 + OL8
#    gparada     05/26/23 - 34556452 Upd cmd for call to mValidateVersionForMVV
#    jesandov    05/10/23 - 35364835: Add UT for Clusterless removal of
#                           machines
#    jesandov    03/31/23 - 35141247 - Add SSH Connection Pool
#    naps        06/20/22 - check es.properties file.
#    jesandov    11/20/20 - Creation
#

"""
Oracle Heading Comments
"""

import os
import re
import shlex
import unittest
import subprocess
import warnings

warnings.filterwarnings("ignore")

from unittest.mock import patch

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import MockCommand, exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.tools.ebTree.ebTree import ebTree

from exabox.tools.ebXmlGen.ebJsonCallbackGenerator import ebJsonCallbackGenerator
from exabox.tools.ebXmlGen.ebExacloudVanillaGenerator import ebExacloudVanillaGenerator
from exabox.tools.ebXmlGen.ebFacadeXmlGen import ebFacadeXmlGen
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.log.LogMgr import ebLogError, ebLogInfo
 
 
class TestXmlGen(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True, aUseOeda=True, aEnableUTFlag=False)

 
    def mBasicGeneration(self, aUUID, aPayloadFilename, aCsPayloadFilename="cs_payload.json", aOnlyParse=False):

        _uuid = aUUID
        _savedir = self.mGetUtil().mGetOutputDir()
        _payload =  self.mGetResourcesJsonFile(aPayloadFilename)
        _oedapath = self.mGetUtil().mGetOedaDir()

        def mRealExecute(aCmd, aStdIn):

            _cmd = aCmd
            if _cmd.startswith("/bin/scp"):
                _cmd = _cmd.replace("/bin/scp", "/bin/cp")

            _args = shlex.split(_cmd)

            _proc = subprocess.Popen(_args, \
                                     stdin=subprocess.PIPE, \
                                     stdout=subprocess.PIPE, \
                                     stderr=subprocess.PIPE,
                                     cwd=_oedapath)

            _stdout, _stderr = wrapStrBytesFunctions(_proc).communicate()
            _rc = _proc.returncode

            return _rc, _stdout, _stderr


        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("imageinfo -version", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("cellcli -e list.*FLASH.*", aStdout="7.15366"),
                    exaMockCommand("cellcli -e list.*FLASH.*", aStdout="7.15366"),
                    exaMockCommand("cellcli -e list.*DELTA.*", aStdout="7.15366"),
                    exaMockCommand("cellcli -e list.*CATALOG.*", aStdout="7.15366"),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aStdout="ORACLE SERVER E4-2c")
                ],
                [
                    exaMockCommand("cellcli -e list.*FLASH.*", aStdout="7.15366"),
                    exaMockCommand("cellcli -e list.*FLASH.*", aStdout="7.15366"),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aStdout="ORACLE SERVER E4-2c")
                ],
                [
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aStdout="ORACLE SERVER E4-2c"),
                    exaMockCommand("cellcli -e list.*FLASH.*", aStdout="7.15366"),
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(".*shared_env.*", aRc=1)
                ],
                [
                    exaMockCommand("imageinfo -version", aStdout="20.2.0.0.0.200803")
                ],
                [
                    exaMockCommand(".*shared_env.*", aRc=1),
                    exaMockCommand("cat.*virbr.*", aStdout="52:54:00:87:07:09"),
                    exaMockCommand("imageinfo -version", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aStdout="ORACLE SERVER E4-2c")
                ],
                [
                    exaMockCommand("imageinfo -version", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aStdout="ORACLE SERVER E4-2c")
                ],
                [
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aStdout="ORACLE SERVER E4-2c")
                ]
            ],
            self.mGetRegexSwitch(): [
                [
                    # Create Keys folder
                    exaMockCommand(".*ibswitches.*")
                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("ls /u01/app", aRc=1),
                    exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':' "), aRc=0, aStdout="/u01/app/18.1.0.0/grid" ,aPersist=True),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/18.1.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="18.0.0.0.0" ,aPersist=True),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/18.1.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/18.1.0.0/grid" ,aPersist=True),
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    # Create Keys folder
                    MockCommand(".*mkdir.*ibswitch.*", mRealExecute),
                    MockCommand(".*mkdir.*clusters.*", mRealExecute),
                    MockCommand(".*chmod.*600.*", mRealExecute),

                    # NAT lookupt
                    MockCommand(".*nslookup.*", mRealExecute),

                    # Create OEDA workdir
                    MockCommand(".*mkdir.*requests.*", mRealExecute),
                    MockCommand(".*chmod.*stage.sh.*", mRealExecute),
                    MockCommand(".*sed.*", mRealExecute, aPersist=True),
                    MockCommand(".*stage.sh.*", mRealExecute, aPersist=True),

                    # Copy XML
                    MockCommand(".*mkdir.*exacloud.conf.*", mRealExecute),
                    MockCommand(".*scp.*", mRealExecute),

                    #KVM Execution
                    MockCommand(".*mkdir.*log*", mRealExecute),
                    MockCommand(".*cp.*xml*", mRealExecute, aPersist=True),

                    # Execute install.sh
                    exaMockCommand("/bin/test -e .*es.properties", aRc=0,  aPersist=True),
                    MockCommand(".*install.sh.*", mRealExecute),
                    exaMockCommand(".*grep Version.*", aStdout="Version : 201207", aPersist=True),

                    # Execute info call
                    exaMockCommand("/bin/test -e .*es.properties", aRc=0,  aPersist=True),
                    MockCommand(".*install.sh.*", mRealExecute),
                    MockCommand(".*install.sh.*", mRealExecute),

                    # Clean up of environment
                    MockCommand(".*rm -f.*", mRealExecute),

                    # Any other command
                    MockCommand(".*", mRealExecute, aPersist=True),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        self.mGetContext().mSetConfigOption("repository_root", self.mGetPath())

        # Execute xml_generator framework
        _facade = ebFacadeXmlGen(_uuid, _payload, _savedir)
        _xmlpath = _facade.mGenerateXml()
        self.mGetClubox().mSetConfigPath(_xmlpath)

        # Update Payload
        _options = self.mGetResourcesJsonFile(aCsPayloadFilename)
        self.mGetClubox().mSetSharedEnv(None)
        self.mGetClubox().mSetExabm(True)
        self.mGetClubox().mSetIsATP(True)

        if aOnlyParse:
            self.mGetClubox().mGetArgsOptions().jsonconf = None
        else:
            self.mGetClubox().mGetArgsOptions().jsonconf = _options

        # Discover KVM
        self.mGetClubox().mSetEnableKVM(None)
        self.mGetClubox().mSetZdlraProv(None)

        if aOnlyParse:
            self.mGetClubox().mParseXMLConfig(self.mGetClubox().mGetArgsOptions())


        else:
            # Execute info call
            self.mGetClubox().mDispatchCluster("info", self.mGetClubox().mGetArgsOptions())
            ebLogInfo("IsKVM: {0}".format(self.mGetClubox().mIsKVM()))


    def test_000_xen_xml(self):
            self.mSetIsElatic(False)
            self.mBasicGeneration("test000", "payload.json")
            
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSetScanPropertyFalseOeda")
    def test_001_kvm_xml(self, mock_mSetScanPropertyFalseOeda):

        self.mSetIsElatic(False)
        self.mBasicGeneration("test001", "payload_kvm.json")
        self.assertEqual(self.mGetClubox().mIsClusterLessXML(), False)

    def test_002_unsorted_xml(self):

        self.mSetIsElatic(True)
        self.mBasicGeneration("test002", "payload_unsorted.json", aOnlyParse=True)

        _ddpair = [
            ['iad103709exdd003.iad103709exd.adminiad1.oraclevcn.com', 'iad103709exddu0301.us.oracle.com'],
            ['iad103709exdd004.iad103709exd.adminiad1.oraclevcn.com', 'iad103709exddu0401.us.oracle.com'],
            ['iad103709exdd002.iad103709exd.adminiad1.oraclevcn.com', 'iad103709exddu0201.us.oracle.com'],
            ['iad103709exdd001.iad103709exd.adminiad1.oraclevcn.com', 'iad103709exddu0101.us.oracle.com'],
        ]

        self.assertEqual(sorted(_ddpair), sorted(self.mGetClubox().mReturnDom0DomUPair()))

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSetScanPropertyFalseOeda")
    def test_003_clusterless_xml(self, mock_mSetScanPropertyFalseOeda):

        self.mSetIsElatic(False)
        self.mBasicGeneration("test003", "payload_clusterless_kvm.json", "cs_payload_clusterless.json")
        self.assertEqual(self.mGetClubox().mIsClusterLessXML(), True)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsClusterLessXML", return_value=True)
    def test_000_clusterless_machine_removal(self, mock_clusterless):

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("ping", aRc=1, aPersist=True),
                ]
            ]
        }

        # Replace payload information
        _payload = str(self.mGetPayload())
        _payload = _payload.replace(self.mGetClubox().mReturnDom0DomUPair()[0][0], "dummy_host")
        self.mGetClubox().mGetArgsOptions().jsonconf = _payload

        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetCmd("patch")
        self.mGetClubox().mRemoveUnreachableNodes(_payload)
        self.mGetClubox().mSetCmd("info")


if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end of file
