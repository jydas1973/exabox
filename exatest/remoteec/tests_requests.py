#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_requests.py /main/2 2022/11/02 11:47:05 hgaldame Exp $
#
# tests_help.py
#
# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
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
#    hgaldame    10/27/22 - 34738764 - ociexacc: exacc remoteec enhancements
#                           for exacloud requests
#    jesandov    04/05/21 - Creation
#

import unittest
import uuid

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.managment.src.RequestsEndpoint import RequestsEndpoint
from unittest.mock import patch, Mock

class ebTestRemoteManagmentRequests(ebTestClucontrol):

    reqid = None

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateRemoteEC=True)

    def test_000_insert(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        _body = {
            "status": "pending",
            "body": "exatest"
        }

        _response = {}
        _endpoint = RequestsEndpoint(None, _body, _response, _shared)
        _endpoint.mPost()

        self.assertTrue("text" in _response)
        self.assertTrue("status" in _response["text"])
        self.assertEqual(_response['text']["status"], "pending")

        ebTestRemoteManagmentRequests.reqid = _response['text']['uuid']

    def test_001_0_change_same(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        _body = {
            "uuid": ebTestRemoteManagmentRequests.reqid,
            "status": "pending"
        }

        _response = {}
        _endpoint = RequestsEndpoint(None, _body, _response, _shared)
        _endpoint.mPut()

        self.assertEqual(_response["error"], "Same data, nothing changed")

    def test_001_1_change(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        _body = {
            "uuid": ebTestRemoteManagmentRequests.reqid,
            "status": "done"
        }

        _response = {}
        _endpoint = RequestsEndpoint(None, _body, _response, _shared)
        _endpoint.mPut()

        self.assertTrue("text" in _response)

    def test_001_2_change_invalid(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        _body = {
            "uuid": "exatest",
            "status": "done"
        }

        _response = {}
        _endpoint = RequestsEndpoint(None, _body, _response, _shared)
        _endpoint.mPut()

        self.assertEqual(_response["error"], "Request not found")

    def test_002_list_all(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        _response = {}
        _endpoint = RequestsEndpoint(None, None, _response, _shared)
        with patch.object(_endpoint,"_RequestsEndpoint__exacloudCmdBlackList", None), \
                patch.object(_endpoint, "_RequestsEndpoint__exacloudRequestDefaultOrder", None):
            _endpoint.mGet()
        self.assertTrue("text" in _response)
        self.assertTrue(len(_response["text"]) > 0)

    def test_002_filter_table(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        _args = {
            "uuid": ebTestRemoteManagmentRequests.reqid,
            "limit": 1,
            "columns": "uuid,body"
        }

        _response = {}
        _endpoint = RequestsEndpoint(_args, None, _response, _shared)
        with patch.object(_endpoint,"_RequestsEndpoint__exacloudCmdBlackList", None), \
                patch.object(_endpoint, "_RequestsEndpoint__exacloudRequestDefaultOrder", None):
            _endpoint.mGet()

        self.assertTrue("text" in _response)
        self.assertTrue(len(_response["text"]) > 0)
        self.assertEqual(len(_response['text'][0]), 2)


    def test_002_list(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        _args = {
            "uuid": ebTestRemoteManagmentRequests.reqid,
            "offset": 1
        }

        _response = {}
        _endpoint = RequestsEndpoint(_args, None, _response, _shared)
        with patch.object(_endpoint,"_RequestsEndpoint__exacloudCmdBlackList", None), \
                patch.object(_endpoint, "_RequestsEndpoint__exacloudRequestDefaultOrder", None):
            _endpoint.mGet()
        self.assertTrue("text" in _response)
        self.assertTrue(len(_response["text"]) > 0)
        self.assertEqual(_response['text'][0]["uuid"], ebTestRemoteManagmentRequests.reqid)


    def test_003_list_exacc(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _args = {
            "columns": "uuid,body"
        }
        _response = {}
        _endpoint = RequestsEndpoint(_args, None, _response, _shared)
        _dict = {}
        _dict['uuid'] = ebTestRemoteManagmentRequests.reqid
        with patch.object(_endpoint._RequestsEndpoint__database, "mFilterRequests") as _spy_method:
                _dict = {}
                _dict['uuid'] = str(uuid.uuid1(clock_seq=1))
                _dict['body'] = ""
                _spy_method.return_value = [_dict]
                _endpoint.mGet()
                _spy_method.assert_called_once_with(
                    {'columns': 'uuid,body'}, 20, None, aNotCondition={
                        'cmdtype': ['cluctrl.collect_log', 'cluctrl.vm_cmd', 'cluctrl.exacc_infra_patch_list',
                                    'cluctrl.rack_info', 'cluctrl.cluster_details', 'cluctrl.exacc_patch_list_metadata',
                                    'cluctrl.checkcluster']}, aOrderBy={'starttime': 'DESC'}
                )
                self.assertTrue("text" in _response)
                self.assertTrue(len(_response["text"]) > 0)
                self.assertEqual(len(_response['text'][0]), 2)

    def test_004_list_exacc_filter_by_cmdtype(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _args = {
            "limit": 1,
            "columns": "uuid,body,cmdtype",
            "cmdtype": "cluctrl.vm_cmd"
        }

        _response = {}
        _endpoint = RequestsEndpoint(_args, None, _response, _shared)
        _dict = {}
        _dict['uuid'] = ebTestRemoteManagmentRequests.reqid
        with patch.object(_endpoint._RequestsEndpoint__database, "mFilterRequests") as _spy_method:
                _dict = {}
                _dict['uuid'] = str(uuid.uuid1(clock_seq=1))
                _dict['body'] = ""
                _spy_method.return_value = [_dict]
                _endpoint.mGet()
                _spy_method.assert_called_once_with(
                    {'columns': 'uuid,body,cmdtype',  'cmdtype': 'cluctrl.vm_cmd'}, 1, None, aNotCondition=None,
                    aOrderBy={'starttime': 'DESC'}
                )
                self.assertTrue("text" in _response)
                self.assertTrue(len(_response["text"]) > 0)
                self.assertEqual(len(_response['text'][0]), 2)


if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end file
