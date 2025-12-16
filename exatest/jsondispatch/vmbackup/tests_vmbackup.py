#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/vmbackup/tests_vmbackup.py /main/4 2024/01/24 16:55:49 jfsaldan Exp $
#
# tests_vmbackup.py
#
# Copyright (c) 2023, 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_vmbackup.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    01/24/24 - Bug 36197480 - EXACS - EXACLOUD FAILS TO SET
#                           VMBACKUP.CONF VALUES TO ENABLED VMBACKUP TO OSS
#    jfsaldan    06/30/23 - Enh 35399269 - EXACLOUD TO SUPPORT RETRIEVAL OF
#                           STATUS FILES FROM DOM0 FOR BACKUP OPERATION.
#    jfsaldan    06/06/23 - Enh 34965441 - EXACLOUD TO SUPPORT NEW TASK FOR
#                           GOLD IMAGE BACKUP
#    jfsaldan    03/23/23 - Enh 35135691 - EXACLOUD - ADD SUPPORT FOR VMBACKUP
#                           LOCAL BACKUP WITH ECRA SCHEDULER
#    jfsaldan    03/23/23 - Creation
#

import unittest
from unittest.mock import patch

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.jsondispatch.handler_vmbackup import VMBackupHandler

class ebTestVMbackup(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.maxDiff = None

    def test_payload_empty_payload(self):

        _options = self.mGetContext().mGetArgsOptions()

        # No payload
        _options.jsonconf = {}
        _handler = VMBackupHandler(_options)
        self.assertFalse(_handler.mParseJsonConfig())

    def test_payload_parsing_good_payload(self):

        _options = self.mGetContext().mGetArgsOptions()

        # Correct payload
        _options.jsonconf = self.mGetResourcesJsonFile("payload_vmbackup.json")
        _handler = VMBackupHandler(_options)
        self.assertTrue(_handler.mParseJsonConfig())

    def test_mExecute_payload_invalid_operation(self):

        _options = self.mGetContext().mGetArgsOptions()

        # Correct payload
        _options.jsonconf = self.mGetResourcesJsonFile("payload_vmbackup.json")

        # Operation
        _options.vmbackup_operation = "backup"
        _expected = (VMBackupHandler.ERR_INVALID_OPERATION, {})

        _handler = VMBackupHandler(_options)
        self.assertEqual(_expected, _handler.mExecute())

    @patch("exabox.ovm.vmbackup.ebCluManageVMBackup.mTriggerBackgrounBackupHost")
    def test_mExecute_payload_valid_operation_backup_success(self,
            aMagicTriggerBackgrounBackupHost):

        _options = self.mGetContext().mGetArgsOptions()

        # Prepare Mock obj
        aMagicTriggerBackgrounBackupHost.return_value = 0

        # Correct payload
        _options.jsonconf = self.mGetResourcesJsonFile("payload_vmbackup.json")

        # Operation
        _options.vmbackup_operation = "backup_host"
        _expected = (VMBackupHandler.SUCCESS, {'Exacloud Cmd Status': 'Pass', 'Command': 'backup_host'})

        _handler = VMBackupHandler(_options)
        self.assertEqual(_expected, _handler.mExecute())


if __name__ == '__main__':
    unittest.main()
