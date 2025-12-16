#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_help.py /main/1 2021/04/16 12:46:05 jesandov Exp $
#
# tests_help.py
#
# Copyright (c) 2021, Oracle and/or its affiliates. 
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

import unittest

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.managment.src.HelpEndpoint import HelpEndpoint

class ebTestRemoteManagmentHelp(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateRemoteEC=True)

    def test_help(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Execute endpoint
        _responseGet = {}
        _endpoint = HelpEndpoint(None, None, _responseGet, _shared)
        _endpoint.mGet()

        _responsePost = {}
        _endpoint = HelpEndpoint(None, None, _responsePost, _shared)
        _endpoint.mPost()

        _responsePut = {}
        _endpoint = HelpEndpoint(None, None, _responsePut, _shared)
        _endpoint.mPut()

        _responsePatch = {}
        _endpoint = HelpEndpoint(None, None, _responsePatch, _shared)
        _endpoint.mPatch()

        _responseDelete = {}
        _endpoint = HelpEndpoint(None, None, _responseDelete, _shared)
        _endpoint.mDelete()

        self.assertEqual(_responseGet, _responsePost)
        self.assertEqual(_responsePost, _responsePut)
        self.assertEqual(_responsePut, _responsePatch)
        self.assertEqual(_responsePatch, _responseDelete)


if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end file
