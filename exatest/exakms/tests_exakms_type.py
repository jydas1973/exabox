#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/exakms/tests_exakms_type.py /main/4 2025/05/16 06:54:04 naps Exp $
#
# tests_exakms_type.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_exakms_type.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    naps        05/15/25 - Bug 37942960 - clusterless patching fix for
#                           fetching compute node name.
#    avimonda    05/05/25 - Bug 37878113 - DOMU OS PRECHECK FAILING WITH SSH
#                           CONNECTIVITY ISSUE
#    jesandov    02/23/24 - 36334338: Unittest for ExaKms Type detection
#    jesandov    02/23/24 - Creation
#

import oci
import os
import sys
import json
import time
import unittest
from unittest import mock

import subprocess
from unittest.mock import patch

from random import shuffle

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import ebJsonObject

from exabox.exakms.ExaKms import ExaKms, exakms_enable_fetch_clustername_decorator
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType
from exabox.exakms.ExaKmsOCI import ExaKmsOCI
from exabox.exakms.ExaKmsKeysDB import ExaKmsKeysDB
from exabox.exakms.ExaKmsFileSystem import ExaKmsFileSystem
from exabox.exakms.ExaKmsSIV import ExaKmsSIV
from exabox.exakms.ExaKmsSingleton import ExaKmsSingleton
from exabox.exakms.ExaKmsEntryOCI import ExaKmsEntryOCIRSA

class ebTestExaKmsType(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)
        self.maxDiff = None

    def mGeneratePatchingPayload(self, aOracleLinuxVersion, aTargetHost, aCustomeExtra=None):

        _payload = self.mGetResourcesJsonFile("patching_payload.json")

        if aOracleLinuxVersion == "OL7":
            _payload["TargetVersion"] = "22.10.9.0.0.240208"
        else:
            _payload["TargetVersion"] = "23.1.10.0.0.240208"

        if aTargetHost == "DOM0":
            _payload["TargetType"] = ["dom0"]

        elif aTargetHost == "DOMU":
            _payload["TargetType"] = ["domu"]

        elif aTargetHost == "CELL":
            _payload["TargetType"] = ["cell"]

        if aCustomeExtra:
            _payload["AdditionalOptions"] = aCustomeExtra

        self.mGetClubox().mGetArgsOptions().jsonconf = _payload

    def mCleanExaKmsKeyType(self):

        if get_gcontext().mCheckRegEntry("exakms_default_keygen_algorithm"):
            get_gcontext().mDelRegEntry("exakms_default_keygen_algorithm")

    def mValidateExaKmsKeyType(self, aKeyType):

        get_gcontext().mSetExaKmsSingleton(ExaKmsSingleton())
        _exakms = get_gcontext().mGetExaKms()
        self.assertEqual(_exakms.mGetDefaultKeyAlgorithm(), aKeyType)

    def test_mDispatchCluster_opc_enabled_false(self):

        self.mGetClubox().mDispatchCluster("opc_enabled_false", self.mGetClubox().mGetArgsOptions())

    def test_mDispatchCluster_info(self):
        #self.mGetContext().mSetConfigOption('remove_root_access', False)
        self.mGetClubox().mDispatchCluster("", self.mGetClubox().mGetArgsOptions())

    def test_mDispatchCluster_patch(self):
        self.mGetContext().mSetConfigOption('remove_root_access', False)
        self.mGetClubox().mDispatchCluster("Patch", self.mGetClubox().mGetArgsOptions())

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsOciEXACC', return_value=True)
    @patch('exabox.config.Config.ebCluCmdCheckOptions', return_value='opc_enabled_false')
    def test_patching_domu(self, _mock_ebCluCmdCheckOptions, _mock_mIsOciEXACC):

        _fipsOff = "FIPS mode is not configured"
        _sestatusOff = "sestatus status:    disabled"

        self.mGetClubox().mSetCmd("patch")

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("sestatus", aStdout=_sestatusOff),
                    exaMockCommand("host_access_control fips-mode --status", aStdout=_fipsOff),
                ]
            ],
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # DomU
        self.mCleanExaKmsKeyType()
        self.mGeneratePatchingPayload("OL8", "DOMU")
        self.mGetClubox().mRefreshExaKmsSingleton()
        self.mValidateExaKmsKeyType("RSA")

    def test_001_patching_ol7(self):

        self.mGetClubox().mSetCmd("patch")

        # Cell
        self.mCleanExaKmsKeyType()
        self.mGeneratePatchingPayload("OL7", "CELL")
        self.mGetClubox().mRefreshExaKmsSingleton()
        self.mValidateExaKmsKeyType("RSA")

        # Dom0
        self.mCleanExaKmsKeyType()
        self.mGeneratePatchingPayload("OL7", "DOM0")
        self.mGetClubox().mRefreshExaKmsSingleton()
        self.mValidateExaKmsKeyType("RSA")

        # DomU
        self.mCleanExaKmsKeyType()
        self.mGeneratePatchingPayload("OL7", "DOMU")
        self.mGetClubox().mRefreshExaKmsSingleton()
        self.mValidateExaKmsKeyType("RSA")


    def test_002_patching_ol8(self):

        _fipsOn = "FIPS mode is configured and active"
        _sestatusOn = "SELinux status:    enabled\nCurrent mode:   enforcing"
        _fipsOff = "FIPS mode is not configured"
        _sestatusOff = "SELinux status:    disabled\nCurrent mode:   off"

        self.mGetClubox().mSetCmd("patch")

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("sestatus", aStdout=_sestatusOff),
                    exaMockCommand("host_access_control fips-mode --status", aStdout=_fipsOn),
                ]
            ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("sestatus", aStdout=_sestatusOn),
                    exaMockCommand("host_access_control fips-mode --status", aStdout=_fipsOn),
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("sestatus", aStdout=_sestatusOn),
                    exaMockCommand("host_access_control fips-mode --status", aStdout=_fipsOff),
                ]
            ]
        }
 
        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # Cell
        self.mCleanExaKmsKeyType()
        self.mGeneratePatchingPayload("OL8", "CELL")
        self.mGetClubox().mRefreshExaKmsSingleton()
        self.mValidateExaKmsKeyType("ECDSA")

        # Dom0
        self.mCleanExaKmsKeyType()
        self.mGeneratePatchingPayload("OL8", "DOM0")
        self.mGetClubox().mRefreshExaKmsSingleton()
        self.mValidateExaKmsKeyType("ECDSA")

        # DomU
        self.mCleanExaKmsKeyType()
        self.mGeneratePatchingPayload("OL8", "DOMU")
        self.mGetClubox().mRefreshExaKmsSingleton()
        self.mValidateExaKmsKeyType("ECDSA")

    def test_003_patching_ol8_off(self):

        _fipsOn = "FIPS mode is configured and active"
        _sestatusOn = "sestatus status:    enabled"
        _fipsOff = "FIPS mode is not configured"
        _sestatusOff = "sestatus status:    disabled"

        self.mGetClubox().mSetCmd("patch")

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("sestatus", aStdout=_sestatusOff),
                    exaMockCommand("host_access_control fips-mode --status", aStdout=_fipsOff),
                ]
            ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("sestatus", aStdout=_sestatusOff),
                    exaMockCommand("host_access_control fips-mode --status", aStdout=_fipsOff),
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("sestatus", aStdout=_sestatusOff),
                    exaMockCommand("host_access_control fips-mode --status", aStdout=_fipsOff),
                ]
            ]
        }
 
        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # Cell
        self.mCleanExaKmsKeyType()
        self.mGeneratePatchingPayload("OL8", "CELL")
        self.mGetClubox().mRefreshExaKmsSingleton()
        self.mValidateExaKmsKeyType("RSA")

        # Dom0
        self.mCleanExaKmsKeyType()
        self.mGeneratePatchingPayload("OL8", "DOM0")
        self.mGetClubox().mRefreshExaKmsSingleton()
        self.mValidateExaKmsKeyType("RSA")

        # DomU
        self.mCleanExaKmsKeyType()
        self.mGeneratePatchingPayload("OL8", "DOMU")
        self.mGetClubox().mRefreshExaKmsSingleton()
        self.mValidateExaKmsKeyType("RSA")

        # Exasplice
        _exasplice = [
            {
                'exasplice': 'yes', 
                'serviceType': 'EXACS', 
                'FpCrId': '6573d876-c37b-41c3-923a-1aadc89fc129', 
                'exaOcid': 
                'ocid1.cloudexadatainfrastructur',
                'exaunitId': '0', 
                'LaunchNode': ''
            }
        ]

        self.mCleanExaKmsKeyType()
        self.mGeneratePatchingPayload("OL8", "DOMU", aCustomeExtra=_exasplice)
        self.mGetClubox().mRefreshExaKmsSingleton()

        self.mCleanExaKmsKeyType()
        self.mGeneratePatchingPayload("OL8", "DOM0", aCustomeExtra=_exasplice)
        self.mGetClubox().mRefreshExaKmsSingleton()

        self.mValidateExaKmsKeyType("RSA")



if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end file
