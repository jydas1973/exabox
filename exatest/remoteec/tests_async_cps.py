#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_async_cps.py /main/3 2022/05/20 14:03:46 hgaldame Exp $
#
# tests_async_cps.py
#
# Copyright (c) 2022, Oracle and/or its affiliates.
#
#    NAME
#      tests_async_cps.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    hgaldame    05/15/22 - 34172836 - oci/exacc: check exacloud remote manager
#                           async request status on remote cps
#    hgaldame    05/06/22 - 34146854 - oci/exacc: persists exacloud remote ec
#                           async request status
#    hgaldame    04/06/22 - 33643036 - remote ec to return text as json object
#                           in case of success & failure
#    hgaldame    04/06/22 - Creation
#

import os
import unittest
import uuid
import json
import socket
from datetime import datetime
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.managment.src.apiv2.AsyncTrackEndpointCps import AsyncTrackEndpointCps
from unittest.mock import patch, Mock
from urllib.error import HTTPError
from exabox.network.HTTPSHelper import ebResponse

class ebTestRemoteManagmentAsyncTrack(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateRemoteEC=True)
        os.makedirs("log/threads", exist_ok=True)

    def mCreateProcess(self, aCmds):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Create Dummy Endpoint
        _endpoint = AsyncTrackEndpointCps(None, None, {}, _shared)

        _tag = _endpoint.mGetAsyncLogTag()
        _tag = "{0} - Exatest".format(_tag)
        _endpoint.mSetAsyncLogTag(_tag)

        # Start process
        def mFinnish(self, x):
            self.assertEqual(x, 1)

        _process = _endpoint.mCreateBashProcess(aCmds, aName="exatest01", aOnFinish=mFinnish, aOnFinishArgs=[self, 1])
        return _process

    def test_000_get_request_status(self):
        """
            Scenario: Get uuid status
            Given an uuid request
            When there is a request for check an existent uuid status
            Then reponse should include the detail status of the request       
        """
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
        _endpoint = AsyncTrackEndpointCps(_args, _args, {}, _shared)

        # Wait to finnish
        _alive = True
        while _alive:
            _endpoint.mGet()
            _alive = _endpoint.mGetResponse()['text']['alive']

        _rc = _endpoint.mGetResponse()['text']['rc']
        self.assertEqual(_rc, 0)
        _http_status = _endpoint.mGetResponse()['status']
        self.assertEqual(_http_status, 200)
        


    def test_001_get_request_status_not_found(self):
        """
            Scenario: Get status from  inexistent uuid status
            Given an uuid request
            When there is a request for check an inexistent uuid status
            Then response should be NOT FOUND 
        """

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Create fake uiid
        _fakeId =  "1" * 37
        _args = {
            "id": _fakeId
        }
        _endpoint = AsyncTrackEndpointCps(_args, _args, {}, _shared)

        _alive = True
        while _alive:
            _endpoint.mGet()
            _alive = _endpoint.mGetResponse()['text']['alive']
        _rc = _endpoint.mGetResponse()['text']['rc']
        self.assertNotEqual(_rc, 0)
        _http_status = _endpoint.mGetResponse()['status']
        self.assertEqual(_http_status, 404)
        _response_id =  _endpoint.mGetResponse()['text']["id"]
        self.assertEqual(_fakeId, _response_id)

    def test_002_get_request_list(self):
        """
            Scenario: Get list of request 
            Given an request for get list
            When there is a request for check list of requests
                 uuis is not provided
            Then response should include a list of the status of the 
                current requests      
        """
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
        _endpoint = AsyncTrackEndpointCps(_args, _args, {}, _shared)

        # Wait to finnish
        _alive = True
        while _alive:
            _endpoint.mGet()
            _alive = _endpoint.mGetResponse()['text']['alive']

        _rc = _endpoint.mGetResponse()['text']['rc']
        self.assertEqual(_rc, 0)
        # No uuid parameter        
        _endpoint = AsyncTrackEndpointCps({}, {}, {}, _shared)
        _endpoint.mGet()
        _response = _endpoint.mGetResponse()
        _http_status = _response['status']
        self.assertEqual(_http_status, 200)
        _responseList = _response['text']
        self.assertIsInstance(_responseList, list)
        

    def test_003_get_request_status_from_db(self):
        """
            Scenario: Get uuid status from DB 
            Given an uuid request not in memory
            When there is a request for check an existent uuid status in DB
            Then reponse should include the detail status of the request
        """
        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _uuid = str(uuid.uuid1(clock_seq=1))

        # Create endpoint
        _args = {
            "id": _uuid
        }
        _current_time = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S+%f')
        _endpoint = AsyncTrackEndpointCps(_args, _args, {}, _shared)
        _response = []
        _response.append(_uuid)
        _response.append(json.dumps(0))
        _response.append("exatest")
        _response.append(False)
        _response.append("log/threads/mgnt-{0}.log".format(_uuid))
        _response.append(_current_time)
        _response.append(_current_time)
        with patch('exabox.core.DBStore3.ebExacloudDB.mGetAsyncProcessById', return_value = _response):
            _endpoint.mGet()
            _response = _endpoint.mGetResponse()
            _responseText = _response['text']
            self.assertEqual(_response['status'], 200)
            self.assertEqual(_responseText['id'], _uuid)
            self.assertEqual(_responseText['rc'], 0)
            self.assertEqual(_responseText['alive'], False)
            self.assertEqual(_responseText['time_start'], _current_time)
            self.assertEqual(_responseText['time_end'], _current_time)

    def test_004_get_incomplete_request_status_from_db(self):
        """
            Scenario: Get status of alive request from DB 
            Given an uuid request not in memory and process not able to store state on DB.
            When there is a request for check an existent uuid status in DB
                 and request still alive 
            Then response should include the detail status of the request
                 response should marked as a complete and failed
        """
        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _uuid = str(uuid.uuid1(clock_seq=1))

        # Create endpoint
        _args = {
            "id": _uuid
        }
        _current_time = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S+%f')
        _endpoint = AsyncTrackEndpointCps(_args, _args, {}, _shared)
        _response = []
        _response.append(_uuid)
        _response.append(json.dumps(None))
        _response.append("exatest")
        _response.append(True)
        _response.append("log/threads/mgnt-{0}.log".format(_uuid))
        _response.append(_current_time)
        _response.append(None)
        with patch('exabox.core.DBStore3.ebExacloudDB.mGetAsyncProcessById', return_value = _response):
            with patch('exabox.core.DBStore3.ebExacloudDB.mUpsertAsyncProcess'):
                _endpoint.mGet()
                _response = _endpoint.mGetResponse()
                _responseText = _response['text']
                self.assertEqual(_response['status'], 200)
                self.assertEqual(_responseText['id'], _uuid)
                self.assertEqual(_responseText['rc'], 1)
                self.assertEqual(_responseText['alive'], False)
                self.assertEqual(_responseText['time_start'], _current_time)
                self.assertIsNotNone(_responseText['time_end'])

    def test_005_get_request_status_not_found_in_remote_cps(self):
        """
            Scenario: Get status from inexistent uuid status on remote cps
            Given an uuid request and remote cps
            When there is a request which uuid does not exist on local cps neither on remote cps 
            Then response should be NOT FOUND 
        """

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        # Create fake uiid
        _fakeId =  "1" * 37
        _args = {
            "id": _fakeId
        }
        # Prepare mock data
        _mockCredential = Mock(**{"mGetAdminCredentialForRequest.return_value":"myauth"})
        _configValues = lambda _arg : _mockCredential if _arg == "auth" else 7071
        _mockAttrs = { "mGetExacloudConfigValue.return_value":"hostcps02","mGetConfigValue.side_effect": _configValues}
        _mockConfig = Mock(**_mockAttrs)
        
        _endpoint = AsyncTrackEndpointCps(_args, _args, {}, _shared)
        with patch('exabox.managment.src.apiv2.AsyncTrackEndpointCps.AsyncTrackEndpointCps.mGetConfig', return_value=_mockConfig):
            with patch('exabox.network.HTTPSHelper.build_opener', side_effect=\
                [Exception("mock general error"), socket.error("mock socket error"), HTTPError("404 mock http error",404,{}, None, None)]):
                _alive = True
                while _alive:
                    _endpoint.mGet()
                    _alive = _endpoint.mGetResponse()['text']['alive']
            _rc = _endpoint.mGetResponse()['text']['rc']
            self.assertNotEqual(_rc, 0)
            _http_status = _endpoint.mGetResponse()['status']
            self.assertEqual(_http_status, 404)
            _response_id =  _endpoint.mGetResponse()['text']["id"]
            self.assertEqual(_fakeId, _response_id)

    def test_006_get_request_status_founded_in_remote_cps(self):
        """
            Scenario: Get status uuid from remote cps host 
            Given an uuid request and remote cps
            When there is a request which uuid does not exist on local cps but exists on remote cps 
            Then reponse should include the detail status of the request       
        """

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()
        _uuid = str(uuid.uuid1(clock_seq=1))
        _args = {
            "id": _uuid
        }
        _currentTime = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S+%f')
        _remoteCps = "hostcps02"
        # Prepare mock data
        _mockCredential = Mock(**{"mGetAdminCredentialForRequest.return_value":"myauth"})
        _configValues = lambda _arg : _mockCredential if _arg == "auth" else 7071
        _mockAttrs = { "mGetExacloudConfigValue.return_value": _remoteCps ,"mGetConfigValue.side_effect": _configValues}
        _mockConfig = Mock(**_mockAttrs)
        _mock_response = ebResponse("remote cps")
        _response = {
            "text": 
            {
                "id": _uuid,
                "rc": 0,
                "name": "exatest",
                "alive": False,
                "log_file": "log/threads/mgnt-{0}.log".format(_uuid),
                "time_start": _currentTime,
                "time_end": _currentTime
            },
            "error": "",
            "http_status": 200
        }
        _endpoint = AsyncTrackEndpointCps(_args, _args, {}, _shared)
        with patch('exabox.managment.src.apiv2.AsyncTrackEndpointCps.AsyncTrackEndpointCps.mGetConfig', return_value=_mockConfig):
            with patch('exabox.network.HTTPSHelper.build_opener', return_value=_mock_response):
                with patch('exabox.network.HTTPSHelper.ebResponse.read', return_value=json.dumps(_response)):
                    _alive = True
                    while _alive:
                        _endpoint.mGet()
                        _alive = _endpoint.mGetResponse()['text']['alive']
            _rc = _endpoint.mGetResponse()['text']['rc']
            self.assertEqual(_rc, 0)
            _http_status = _endpoint.mGetResponse()['status']
            self.assertEqual(_http_status, 200)
            _response_id =  _endpoint.mGetResponse()['text']["id"]
            self.assertEqual(_uuid, _response_id)

if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end file
