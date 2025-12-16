#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_async.py /main/2 2023/02/23 09:51:58 jesandov Exp $
#
# tests_help.py
#
# Copyright (c) 2021, 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_help.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    04/05/21 - Creation
#

import os
import time
import unittest

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.managment.src.AsyncTrackEndpoint import AsyncTrackEndpoint

class ebTestRemoteManagmentAsyncTrack(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateRemoteEC=True)
        os.makedirs("log/threads", exist_ok=True)

    def mCreateProcess(self, aCmds):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Create Dummy Endpoint
        _endpoint = AsyncTrackEndpoint(None, None, {}, _shared)

        _tag = _endpoint.mGetAsyncLogTag()
        _tag = "{0} - Exatest".format(_tag)
        _endpoint.mSetAsyncLogTag(_tag)

        # Start process
        def mFinnish(self, x):
            self.assertEqual(x, 1)

        _process = _endpoint.mCreateBashProcess(aCmds, aName="exatest01", aOnFinish=mFinnish, aOnFinishArgs=[self, 1])
        return _process

    def test_000_single(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Create process
        _cmds = [
            ["sleep", "1"],
            ["echo", "exatest"]
        ]

        _process = self.mCreateProcess(_cmds)

        # Create endpoint
        _args = {
            "id": _process['id']
        }
        _endpoint = AsyncTrackEndpoint(_args, _args, {}, _shared)

        # Wait to finnish
        _endtime = None
        while _endtime is None:
            
            _endpoint.mGet()
            _endtime = _endpoint.mGetResponse()['text']['time_end']

        _rc = _endpoint.mGetResponse()['text']['rc']
        self.assertEqual(_rc, 0)

        # Get file content
        _endpoint.mPut()
        self.assertTrue("text" in _endpoint.mGetResponse())
        self.assertTrue("content" in _endpoint.mGetResponse()["text"])
        self.assertTrue("exatest" in _endpoint.mGetResponse()["text"]['content'].values())


    def test_001_delete(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Create process
        _cmds = [
            ["sleep", "600000"],
        ]

        _process = self.mCreateProcess(_cmds)

        # Create endpoint
        _args = {
            "id": _process['id']
        }
        _endpoint = AsyncTrackEndpoint(_args, _args, {}, _shared)

        # Wait to finnish
        _endpoint.mDelete()

        _alive = True
        while _alive:

            _endpoint.mGet()
            _alive = _endpoint.mGetResponse()['text']['alive']

        self.assertEqual(_alive, False)

    def test_002_errors(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Invalid ID on Delete
        _args = {
            "id": "invalid_id"
        }
        _endpoint = AsyncTrackEndpoint(None, _args, {}, _shared)
        _endpoint.mDelete()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

        # Missing ID on PUT
        _args = {
        }
        _endpoint = AsyncTrackEndpoint(None, _args, {}, _shared)
        _endpoint.mPut()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

        # Invalid offset, limit and process id
        _args = {
            "offset": "a",
            "limit": "b",
            "id": "c"
        }
        _endpoint = AsyncTrackEndpoint(None, _args, {}, _shared)
        _endpoint.mPut()
        self.assertEqual(_endpoint.mGetResponse()['status'], 500)

    def test_003_mock(self):

        _logfile = os.path.join(self.mGetUtil().mGetOutputDir(), "dummy.log")

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Execute normally
        _callerCmds = {
            "cmd_list": [
                ["echo", "exatest"]
            ]
        }

        _endpoint = AsyncTrackEndpoint(None, None, {}, _shared)
        _output = _endpoint.mAsyncBashExecutionStdOut(_logfile, "exatest", _callerCmds)

        # Do mock execute
        _shared['exatest_mock'] = True

        _mockCmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("echo exatest", aStdout="exatest\n")
                ],
                [
                    exaMockCommand("echo exatest", aStdout="exatest\n")
                ]
            ]
        }

        # Prepare mock commands
        self.mPrepareMockCommands(_mockCmds)
        _, _stdout,  _stderr = _endpoint.mBashExecution(["echo", "exatest"])

        # Check mock and not mock are the same output
        self.assertEqual(_stdout, _output[0]['stdout'])
        self.assertEqual(_stderr, _output[0]['stderr'])



if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end file
