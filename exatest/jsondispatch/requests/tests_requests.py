#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/jsondispatch/requests/tests_requests.py /main/1 2022/10/17 09:03:22 jesandov Exp $
#
# tests_SLA.py
#
# Copyright (c) 2022, Oracle and/or its affiliates.
#
#    NAME
#      tests_requests.py - Unit test for requests dispatch
#
#    DESCRIPTION
#      Run tests for Requests json dispatch
#
#    NOTES
#      None
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    09/21/22 - Creation
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

from exabox.jsondispatch.handler_requests import RequestsHandler

class ebTestSLA(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)
        self.maxDiff = None

    def test_001_mPrepareDatabase(self):

        _db = ebGetDefaultDB()
        _uuids = []

        self.assertTrue(_db.mCheckTableExist('requests'))
        self.assertTrue(_db.mCheckTableExist('requests_archive'))

        _db.mExecute("DELETE FROM requests")
        _db.mExecute("DELETE FROM requests_archive")

        for i in range(1, 9):
            _uuids.append(six.text_type(uuid.uuid1(clock_seq=i)))

        now = datetime.datetime.now()

        minus60d30 = (now - datetime.timedelta(days=60, minutes=30)).strftime('%a %b %d %H:%M:%S %Y')
        minus30d30 = (now - datetime.timedelta(days=30, minutes=30)).strftime('%a %b %d %H:%M:%S %Y')
        minus240m  = (now - datetime.timedelta(minutes=240)).strftime('%a %b %d %H:%M:%S %Y')

        minus60d10  = (now - datetime.timedelta(days=60, minutes=10)).strftime('%a %b %d %H:%M:%S %Y')
        minus30d10  = (now - datetime.timedelta(days=30, minutes=10)).strftime('%a %b %d %H:%M:%S %Y')
        minus180min = (now  - datetime.timedelta(minutes=180)).strftime('%a %b %d %H:%M:%S %Y')
        
        request = ebJobRequest(None, {})
        request.mFromDict({"uuid": _uuids[0], "status": "Done", "starttime": minus60d30, "endtime": minus60d10, "cmdtype": "cluctrl.sim_install"})
        _db.mInsertNewRequest(request)
        request.mFromDict({"uuid": _uuids[1], "status": "Done", "starttime": minus30d30, "endtime": minus30d10, "cmdtype": "cluctrl.sim_install"})
        _db.mInsertNewRequest(request)
        request.mFromDict({"uuid": _uuids[2], "status": "Done", "starttime": minus240m, "endtime": minus180min, "cmdtype": "cluctrl.sim_install"})
        _db.mInsertNewRequest(request)
        request.mFromDict({"uuid": _uuids[3], "status": "Done", "starttime": minus240m, "endtime": 'Undef', "cmdtype": "cluctrl.fetchkeys"})
        _db.mInsertNewRequest(request)
        request.mFromDict({"uuid": _uuids[4], "status": "Done", "starttime": minus240m, "endtime": minus180min, "cmdtype": "cluctrl.fetchkeys"})
        _db.mInsertNewRequest(request)


    def test_001_payload(self):

        _db = ebGetDefaultDB()
        _options = self.mGetContext().mGetArgsOptions()
        _handler = RequestsHandler(_options, aDb=_db)

        # No payload / All requests
        _options.jsonconf = {}

        _rc, _requests = _handler.mExecute()
        self.assertTrue(_handler.mParseJsonConfig())
        self.assertEqual(_rc, 0)
        self.assertEqual(len(_requests), 5)

        # Single query
        _options.jsonconf = {
            "status": "Done"
        }

        _rc, _requests = _handler.mExecute()
        self.assertTrue(_handler.mParseJsonConfig())
        self.assertEqual(_rc, 0)
        self.assertEqual(len(_requests), 5)

        # Multiples arguments query
        _options.jsonconf = {
            "status": "Done",
            "cmdtype": "cluctrl.fetchkeys"
        }

        _rc, _requests = _handler.mExecute()
        self.assertTrue(_handler.mParseJsonConfig())
        self.assertEqual(_rc, 0)
        self.assertEqual(len(_requests), 2)

        # Complex Query
        _options.jsonconf = {
            "status": "Done",
            "cmdtype": "cluctrl.sim_install",
            "columns": "uuid,status",
            "limit": "1",
            "offset": "1"
        }

        _rc, _requests = _handler.mExecute()
        self.assertTrue(_handler.mParseJsonConfig())
        self.assertEqual(_rc, 0)
        self.assertEqual(len(_requests), 1)
        self.assertEqual(list(_requests[0].keys()), ["uuid", "status"])


if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end of file
