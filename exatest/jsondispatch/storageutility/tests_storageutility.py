#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/storageutility/tests_storageutility.py /main/1 2026/02/10 12:18:51 jesandov Exp $
#
# tests_storageutility.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_storageutility.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    02/04/26 - Creation

import json
import os
import unittest

from unittest import mock
from unittest.mock import patch

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode

from exabox.jsondispatch.handler_storage_utility import StorageUtility

class ebTestStorageUility(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.maxDiff = None

    def test_endpoint(self):

        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = self.mGetResourcesJsonFile("payload.json")
        _cellcli = self.mGetResourcesTextFile("cellcli.out")

        # Prepare mocks
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli", aRc=0, aStdout=_cellcli),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        # Correct payload
        _handler = StorageUtility(_options)
        _rc, _result = _handler.mExecute()
        self.assertEqual(_rc, 0)


if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end of file
