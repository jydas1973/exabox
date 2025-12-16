#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_rackcontrol.py /main/2 2022/03/25 15:30:43 alsepulv Exp $
#
# tests_rackcontrol.py
#
# Copyright (c) 2022, Oracle and/or its affiliates. 
#
#    NAME
#      tests_rackcontrol.py - Unit test for rackcontrol
#
#    DESCRIPTION
#      Run tests for rackcontrol
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    alsepulv    03/22/22 - Enh 33941264: Improve code coverage
#    alsepulv    01/27/22 - Creation
#

import os
import shutil
import unittest
from unittest.mock import patch

from exabox.core.Context import get_gcontext
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.ovm.rackcontrol import ebRackControl, ebRacksDB, ebRackInfo


class ebTestRackcontrol(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

        self.__tmp_path = os.path.join(self.mGetPath(self), "tmp")
        self.__rack_name = "exatest_dummy_rack"
        get_gcontext().mSetConfigOption("racks_dir", self.__tmp_path)

    def mCreateDirectoriesAndFiles(self):
        # Create directory for dummy cluster
        _path = os.path.join(self.__tmp_path, self.__rack_name)

        if not os.path.exists(_path):
            os.makedirs(_path)

        _xml_file = os.path.join(_path, f"{self.__rack_name}.xml")
        _zip_file = os.path.join(_path, "keys1.zip")

        # Create dummy cluster xml
        shutil.copy(os.path.join(self.mGetPath(), "sample.xml"), _xml_file)

        # create an empty zip file
        _empty_zip_data = (b"PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                           b"\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        with open(_zip_file, 'bw') as zipfile:
            zipfile.write(_empty_zip_data)

    @patch('exabox.ovm.rackcontrol.ebRackControl.mCreateClubox')
    def test_cmds(self, mock_createClubox):
        mock_createClubox.return_value = self.mGetClubox()

        try:
            _cmds = ["list", "listowner", "reserve", "release"]
            self.mCreateDirectoriesAndFiles()

            _options = self.mGetContext().mGetArgsOptions()
            _options.id = self.__rack_name
            _options.uid = self.mGetClubox().mGetUUID()

            for _cmd in _cmds:
                _options.rackcmd = _cmd
                _rack_control = ebRackControl(_options)
                _rack_control.mExecute()

        finally:
            shutil.rmtree(self.__tmp_path)

    def test_ebRacksDB(self):

        try:
            self.mCreateDirectoriesAndFiles()

            # Populate rack info
            _rackinfo = ebRackInfo()
            _rackinfo.mSetRackID(self.__rack_name)
            _rackinfo.mSetOwner(self.mGetClubox().mGetUUID())
            _rackinfo.mSetStatus("reserved")
            _rackinfo.mSetStartTime()
            _rackinfo.mSetHostname("localhost")
            _rackinfo.mSetPath("exacloud")

            # insert and update rack and location
            _racksDB = ebRacksDB()
            _racksDB.mInsertRack(_rackinfo)
            _racksDB.mInsertLocation(_rackinfo)
            _racksDB.mUpdateRack(_rackinfo)
            _racksDB.mUpdateLocation(_rackinfo)

        finally:
            _racksDB.mShutdownDB()
            shutil.rmtree(self.__tmp_path)

if __name__ == '__main__':
    unittest.main()
