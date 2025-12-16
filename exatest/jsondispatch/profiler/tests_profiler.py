#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/profiler/tests_profiler.py /main/1 2024/01/12 09:01:07 jesandov Exp $
#
# tests_profiler.py
#
# Copyright (c) 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_profiler.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    01/09/24 - Creation
#

import json
import os
import six
import time
import uuid
import datetime
import unittest

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.DBStore import ebGetDefaultDB
from exabox.agent.ebJobRequest import ebJobRequest

from exabox.tools.profiling.stepwise import create_profile_info
from exabox.jsondispatch.handler_profiler import ProfilerHandler

class ebTestProfiler(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)
        self.maxDiff = None

    def test_000_mPrepareDatabase(self):

        _db = ebGetDefaultDB()
        _db.mExecute("DELETE FROM profiler")

        _toAdd = self.mGetResourcesJsonFile("DB.json")
        for _row in _toAdd["rows"]:

            _pi = create_profile_info(
                  _row["step"],
                  _row["profiler_type"],
                  _row["start_time"],
                  _row["end_time"],
                  _row["operation_id"],
                  _row["workflow_id"],
                  _row["exaunit_id"],
                  _row["cmdtype"],
                  json.loads(_row["details"]),
                  _row["exec_type"],
                  aRawDate=False
            )

            _db.mInsertProfiler(_pi)


    def test_001_endpoint(self):

        _db = ebGetDefaultDB()
        _options = self.mGetContext().mGetArgsOptions()
        _options.jsonconf = self.mGetResourcesJsonFile("payload.json")
        _handler = ProfilerHandler(_options, aDb=_db)

        _rc, _requests = _handler.mExecute()
        self.assertTrue(_handler.mParseJsonConfig())
        self.assertEqual(_rc, 0)


if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end of file
