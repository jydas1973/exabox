#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/ilom_pwd/tests_ilom_pwd.py /main/1 2025/08/11 16:10:09 gparada Exp $
#
# tests_ilom_pwd.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_ilom_pwd.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    gparada     07/08/25 - 37996087-jsondisp-reset-ilom-pwd
#    gparada     07/08/25 - Creation
#
import json
import os
import re
import unittest

from unittest import mock
from unittest.mock import patch

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.utils.node import exaBoxNode

from exabox.jsondispatch.handler_ilom_pwd import IlomPasswordHandler

PAYLOAD = {
    "jsonconf": {
        "servers": [
            {
                "host": "scaqab10adm01.us.oracle.com",
                "ilomhost": "scaqab10adm01lo.us.oracle.com",
                "new_sct": "d2VsY29tZTE="
            },
            {
                "host": "scaqab10adm02.us.oracle.com",
                "ilomhost": "scaqab10adm01lo.us.oracle.com",
                "new_sct": "d2VsY29tZTE="
            },
        ]
    }
}

PAYLOAD_WITHOUT_SCT = {
    "jsonconf": {    
        "servers": [
            {
                "host": "scaqab10adm01.us.oracle.com",
                "ilomhost": "scaqab10adm01lo.us.oracle.com"        },
            {
                "host": "scaqab10adm02.us.oracle.com",
                "ilomhost": "scaqab10adm01lo.us.oracle.com"
            },
        ]
    },
    "wf_uuid":"5dace735-1b60-47ef-8f3e-45b542246fdf",
    "operation_uuid":"79006b9f-747f-4819-b8cd-ec1ab5e335c4"    
}

def mockMUnmaskNatHost(aHost):
    return aHost

class ebTestIlomPwdHandler(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestIlomPwdHandler, self).setUpClass()
        # prepareKmsEntries()

    def test_001_empty_payload(self):
        # Prepare payload
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf =  {"jsonconf": {"servers": []}}

        _handler = IlomPasswordHandler(_options)
        _rc, _result = _handler.mExecute()
        print(json.dumps(_result, indent=4))
        self.assertEqual(_rc, 1)
        self.assertEqual(_result["reason"], "Zero destination hosts.")

    def test_002_reset_ok(self):
        # Prepare payload
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD

        # Prepare mocks
        _cmds = {
            self.mGetRegexDom0(aSeqNo='01'): [
                [
                    exaMockCommand(
                        'ipmitool sunoem cli "set -script ' \
                        + '/SP/users/root/ locked=false"',
                        aRc=0),
                    exaMockCommand(re.escape(
                        'ipmitool sunoem cli "set -script /SP/preferences/' \
                        + 'password_policy/account_lockout/ state=disabled"'), 
                        aRc=0),
                    exaMockCommand('ipmitool user list 0x02 *', 
                        aRc=0, aStdout="2", aPersist=0),
                    exaMockCommand('ipmitool user set *', aRc=0),
                ],
            ],
            self.mGetRegexDom0(aSeqNo='02'): [
                [
                    exaMockCommand(
                        'ipmitool sunoem cli "set -script ' \
                        + '/SP/users/root/ locked=false"',
                        aRc=0),
                    exaMockCommand(re.escape(
                        'ipmitool sunoem cli "set -script /SP/preferences/' \
                        + 'password_policy/account_lockout/ state=disabled"'), 
                        aRc=0),
                    exaMockCommand('ipmitool user list *', 
                        aRc=0, aStdout="2", aPersist=0),
                    exaMockCommand('ipmitool user set *', aRc=0),
                ],
            ],
        }        
        self.mPrepareMockCommands(_cmds)

        _handler = IlomPasswordHandler(_options)
        _rc, _result = _handler.mExecute()
        print(json.dumps(_result, indent=4))
        self.assertEqual(_rc, 0)
        self.assertEqual(_result["reason"], "Success")

    def test_003_missing_pwd(self):
        # Prepare payload
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = PAYLOAD_WITHOUT_SCT

        # Prepare mocks
        _cmds = {
            self.mGetRegexDom0(aSeqNo='01'): [
                [
                    exaMockCommand(
                        'ipmitool sunoem cli "set -script ' \
                        + '/SP/users/root/ locked=false"',
                        aRc=0),
                    exaMockCommand(re.escape(
                        'ipmitool sunoem cli "set -script /SP/preferences/' \
                        + 'password_policy/account_lockout/ state=disabled"'), 
                        aRc=0),
                    exaMockCommand('ipmitool user list 0x02 *', 
                        aRc=0, aStdout="2", aPersist=0),
                    exaMockCommand('ipmitool user set *', aRc=0),
                ],
            ],
            self.mGetRegexDom0(aSeqNo='02'): [
                [
                    exaMockCommand(
                        'ipmitool sunoem cli "set -script ' \
                        + '/SP/users/root/ locked=false"',
                        aRc=0),
                    exaMockCommand(re.escape(
                        'ipmitool sunoem cli "set -script /SP/preferences/' \
                        + 'password_policy/account_lockout/ state=disabled"'), 
                        aRc=0),
                    exaMockCommand('ipmitool user list *', 
                        aRc=0, aStdout="2", aPersist=0),
                    exaMockCommand('ipmitool user set *', aRc=0),
                ],
            ],
        }        
        self.mPrepareMockCommands(_cmds)

        _handler = IlomPasswordHandler(_options)
        _rc, _result = _handler.mExecute()
        print(json.dumps(_result, indent=4))
        self.assertEqual(_rc, 1)
        self.assertEqual(_result["reason"], "Error")

if __name__ == '__main__':
    unittest.main() 