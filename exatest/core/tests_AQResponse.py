#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/core/tests_AQResponse.py /main/2 2025/08/22 07:11:21 aypaul Exp $
#
# tests_AQResponse.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_AQResponse.py - Unit tests for AQ response publishing
#
#    DESCRIPTION
#      Tests ECRA AQ response publishing, queue name synchronization, and
#      liveliness message handling.
#
#    NOTES
#      Uses mocks for database, queue, and request objects to avoid external AQ
#      dependencies.
#
#    MODIFIED   (MM/DD/YY)
#    kanmanic    06/17/26 - 39560339 - Cover AQ logging
#    kanmanic    06/15/26 - 39560339 - Retry failed AQ response publishes
#    kanmanic    06/15/26 - 39560339 - Mark AQ response failures for
#                           missing AQ name and DB connect errors
#    kanmanic    03/17/26 - 37764703 AQ Status Tracker Support
#    aararora    03/02/26 - ER 38951653: Increase code coverage
#    aararora    05/21/25 - Tests methods related to sending response to ecra using AQ
#    aararora    05/21/25 - Creation
#
import json
import os
import sys
import unittest
import uuid
from contextlib import contextmanager
from datetime import datetime
from types import SimpleNamespace
from unittest import mock
from unittest.mock import MagicMock, patch

with patch('multiprocessing.Lock', return_value=MagicMock()):
    from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
    from exabox.log.LogMgr import ebLogInfo
    from exabox.core import AQResponse
    from exabox.core.DBStore import ebGetDefaultDB
    from exabox.agent.ebJobRequest import ebJobRequest

DB_REG_ENTRY = {"user": "ecratestecra",
                "password": "welcome",
                "host": "phoenix26.dev3sub3phx.databasede3phx.oraclevcn.com",
                "port": "1621",
                "service_name": "ecrapdb.dev3sub3phx.databasede3phx.oraclevcn.com"}

class testOptions(object): pass

class ebTestAQResponse(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestAQResponse, self).setUpClass(aGenerateDatabase=True)

    def _stub_db_execute(self, db_obj):
        db_obj.mExecuteLog = MagicMock(return_value=0)
        db_obj.mExecute = MagicMock(return_value=0)

    def test_01_mUpdateRequestDataPushDisabled(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for updating request data - This test is"\
                  " executed when the push status support is not enabled but the"\
                  " given uuid is present in the DB")
        _db = ebGetDefaultDB()
        self._stub_db_execute(_db)
        _db.mUpdateResponseSent = MagicMock(return_value=0)
        _reqobj = ebJobRequest('cluctrl.dom0_details', {}, aDB=_db)
        self.mGetClubox().mSetRequestObj(_reqobj)
        _reqobj = self.mGetClubox().mGetRequestObj()
        _reqobj.mSetUUID("9419f694-9494-11ec-ba6e-565c06664853")
        with patch('exabox.core.AQResponse.ebJobRequest.mGetUUID', return_value="9419f694-9494-11ec-ba6e-565c06664853"):
            _db.mUpdateRequest(_reqobj)
        ebLogInfo("Unit test for updating request data is successful.")

    def test_02_mUpdateRequestDataInternalCall(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for updating request data - This test is"\
                  " executed when we don't want the response to be sent to ecra.")
        _db = ebGetDefaultDB()
        self._stub_db_execute(_db)
        _db.mUpdateResponseSent = MagicMock(return_value=0)
        _reqobj = ebJobRequest('cluctrl.dom0_details', {}, aDB=_db)
        self.mGetClubox().mSetRequestObj(_reqobj)
        _reqobj = self.mGetClubox().mGetRequestObj()
        _reqobj.mSetUUID("9419f694-9494-11ec-ba6e-565c06664853")
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "True")
        with patch('exabox.core.AQResponse.ebJobRequest.mGetUUID', return_value="9419f694-9494-11ec-ba6e-565c06664853"):
            _db.mUpdateRequest(_reqobj, aInternal=True)
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "False")
        ebLogInfo("Unit test for updating request data is successful.")

    def test_03_mUpdateRequestDataInvalidUuid(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for updating request data - This test is"\
                  " executed when the given uuid does not exist in DB.")
        _db = ebGetDefaultDB()
        self._stub_db_execute(_db)
        _db.mUpdateResponseSent = MagicMock(return_value=0)
        _reqobj = ebJobRequest('cluctrl.dom0_details', {}, aDB=_db)
        self.mGetClubox().mSetRequestObj(_reqobj)
        _reqobj = self.mGetClubox().mGetRequestObj()
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "True")
        _db.mUpdateChildRequestError(_reqobj.mGetUUID(), 'Error')
        _db.mUpdateRequest(_reqobj)
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "False")
        ebLogInfo("Unit test for updating request data is successful.")

    def test_04_mUpdateChildRequestError(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for updating request data - This test is"\
                  " executed for method mUpdateChildRequestError.")
        _db = ebGetDefaultDB()
        self._stub_db_execute(_db)
        _db.mUpdateResponseSent = MagicMock(return_value=0)
        _reqobj = ebJobRequest('cluctrl.dom0_details', {}, aDB=_db)
        self.mGetClubox().mSetRequestObj(_reqobj)
        _reqobj = self.mGetClubox().mGetRequestObj()
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "True")
        with patch('exabox.core.DBStore3.ebExacloudDB.mGetCompleteRequest', return_value=_reqobj):
            _db.mUpdateChildRequestError(_reqobj.mGetUUID(), 'Error')
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "False")
        ebLogInfo("Unit test for mUpdateChildRequestError is successful.")

    def test_05_mUpdateRequestDataLoadDBError(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for updating request data - This test is"\
                  " executed for method mUpdateRequestData and error is raised when loading"\
                  " request from DB.")
        _db = ebGetDefaultDB()
        self._stub_db_execute(_db)
        _reqobj = ebJobRequest('cluctrl.dom0_details', {}, aDB=_db)
        self.mGetClubox().mSetRequestObj(_reqobj)
        _reqobj = self.mGetClubox().mGetRequestObj()
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "True")
        with patch('exabox.core.AQResponse.ebJobRequest.mLoadRequestFromDB', side_effect=Exception("Mock exception")),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetCompleteRequest', return_value=_reqobj):
            _db.mUpdateRequest(_reqobj)
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "False")
        ebLogInfo("Unit test for updating request data is successful.")

    def test_06_mUpdateRequestDataRegEntryKeyMissing(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for updating request data - This test is"\
                  " executed when there is key error in obtaining DB details from registry.")
        _db = ebGetDefaultDB()
        self._stub_db_execute(_db)
        _reqobj = ebJobRequest('cluctrl.dom0_details', {}, aDB=_db)
        self.mGetClubox().mSetRequestObj(_reqobj)
        _reqobj = self.mGetClubox().mGetRequestObj()
        _reqobj.mSetUUID("9419f694-9494-11ec-ba6e-565c06664853")
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "True")
        with patch('exabox.core.AQResponse.ebJobRequest.mGetUUID', return_value="9419f694-9494-11ec-ba6e-565c06664853"),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetCompleteRequest', return_value=_reqobj):
            _db.mUpdateRequest(_reqobj)
        self.mGetContext().mDelRegEntry('ecradbreg_name')
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "False")
        ebLogInfo("Unit test for updating request data is successful.")

    def test_07_mUpdateRequestDataDBDetailsAbsent(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for updating request data - This test is"\
                  " executed when the DB details are not present in registry.")
        _db = ebGetDefaultDB()
        self._stub_db_execute(_db)
        _reqobj = ebJobRequest('cluctrl.dom0_details', {}, aDB=_db)
        self.mGetClubox().mSetRequestObj(_reqobj)
        _reqobj = self.mGetClubox().mGetRequestObj()
        _reqobj.mSetUUID("9419f694-9494-11ec-ba6e-565c06664853")
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "True")
        self.mGetContext().mSetRegEntry('ecradbreg_name', None)
        with patch('exabox.core.AQResponse.ebJobRequest.mGetUUID', return_value="9419f694-9494-11ec-ba6e-565c06664853"),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetCompleteRequest', return_value=_reqobj):
            _db.mUpdateRequest(_reqobj)
        self.mGetContext().mDelRegEntry('ecradbreg_name')
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "False")
        ebLogInfo("Unit test for updating request data is successful.")

    def test_08_mUpdateRequestDataAQDetailsAbsent(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for updating request data - This test is"\
                  " executed when the AQ details are not present in request object.")
        _db = ebGetDefaultDB()
        self._stub_db_execute(_db)
        _reqobj = ebJobRequest('cluctrl.dom0_details', {}, aDB=_db)
        self.mGetClubox().mSetRequestObj(_reqobj)
        _reqobj = self.mGetClubox().mGetRequestObj()
        _reqobj.mSetUUID("9419f694-9494-11ec-ba6e-565c06664853")
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "True")
        self.mGetContext().mSetRegEntry('ecradbreg_name', DB_REG_ENTRY)
        with patch('exabox.core.AQResponse.ebJobRequest.mGetUUID', return_value="9419f694-9494-11ec-ba6e-565c06664853"),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetCompleteRequest', return_value=_reqobj):
            _db.mUpdateRequest(_reqobj)
        self.mGetContext().mSetRegEntry('ecradbreg_name', None)
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "False")
        ebLogInfo("Unit test for updating request data is successful.")

    def test_09_mUpdateRequestDataResponseDataAbsent(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for updating request data - This test is"\
                  " executed when the response data could not be obtained.")
        _db = ebGetDefaultDB()
        self._stub_db_execute(_db)
        _reqobj = ebJobRequest('cluctrl.dom0_details', {}, aDB=_db)
        self.mGetClubox().mSetRequestObj(_reqobj)
        _reqobj = self.mGetClubox().mGetRequestObj()
        _reqobj.mSetUUID("9419f694-9494-11ec-ba6e-565c06664853")
        _reqobj.mSetAqName("DEMO_QUEUE")
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "True")
        self.mGetContext().mSetRegEntry('ecradbreg_name', DB_REG_ENTRY)
        with patch('exabox.core.AQResponse.ebJobRequest.mGetUUID', return_value="9419f694-9494-11ec-ba6e-565c06664853"),\
             patch('exabox.core.AQResponse.ebJobRequest.mGetAqName', return_value="DEMO_QUEUE"),\
             patch('exabox.core.AQResponse.mGetResponseData', return_value=None),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetCompleteRequest', return_value=_reqobj):
            _db.mUpdateRequest(_reqobj)
        self.mGetContext().mSetRegEntry('ecradbreg_name', None)
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "False")
        ebLogInfo("Unit test for updating request data is successful.")

    def test_10_mUpdateRequestDataOracleClientHomeAbsent(self):
        return
        ebLogInfo("")
        ebLogInfo("Running unit test for updating request data - This test is"\
                  " executed when the oracle client home details are absent in config.")
        _db = ebGetDefaultDB()
        self._stub_db_execute(_db)
        _reqobj = ebJobRequest('cluctrl.dom0_details', {}, aDB=_db)
        self.mGetClubox().mSetRequestObj(_reqobj)
        _reqobj = self.mGetClubox().mGetRequestObj()
        _reqobj.mSetUUID("9419f694-9494-11ec-ba6e-565c06664853")
        _reqobj.mGetResponseSent()
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "True")
        self.mGetContext().mSetRegEntry('ecradbreg_name', DB_REG_ENTRY)
        with patch('exabox.core.AQResponse.ebJobRequest.mGetUUID', return_value="9419f694-9494-11ec-ba6e-565c06664853"),\
             patch('exabox.core.AQResponse.ebJobRequest.mGetAqName', return_value="DEMO_QUEUE"),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetCompleteRequest', return_value=_reqobj):
            _db.mUpdateRequest(_reqobj)
        self.mGetContext().mSetRegEntry('ecradbreg_name', None)
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "False")
        ebLogInfo("Unit test for updating request data is successful.")

    def test_11_mUpdateRequestDataOracleDBClientAbsent(self):
        return
        ebLogInfo("")
        ebLogInfo("Running unit test for updating request data - This test is"\
                  " executed when the oracle db client could not be initialized.")
        _db = ebGetDefaultDB()
        _reqobj = ebJobRequest('cluctrl.dom0_details', {}, aDB=_db)
        self.mGetClubox().mSetRequestObj(_reqobj)
        _reqobj = self.mGetClubox().mGetRequestObj()
        _reqobj.mSetUUID("9419f694-9494-11ec-ba6e-565c06664853")
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "True")
        self.mGetContext().mSetRegEntry('ecradbreg_name', DB_REG_ENTRY)
        os.environ['ORACLE_HOME'] = 'Mock home'
        with patch('exabox.core.AQResponse.ebJobRequest.mGetUUID', return_value="9419f694-9494-11ec-ba6e-565c06664853"),\
             patch('exabox.core.AQResponse.ebJobRequest.mGetAqName', return_value="DEMO_QUEUE"),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetCompleteRequest', return_value=_reqobj):
            _db.mUpdateRequest(_reqobj)
        self.mGetContext().mSetConfigOption('oracleclient_home', None)
        self.mGetContext().mSetRegEntry('ecradbreg_name', None)
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "False")
        ebLogInfo("Unit test for updating request data is successful.")

    def test_12_mUpdateRequestDataErrorOracleDBConnect(self):
        return
        ebLogInfo("")
        ebLogInfo("Running unit test for updating request data - This test is"\
                  " executed when there is an error while connecting to oracle db.")
        _db = ebGetDefaultDB()
        _reqobj = ebJobRequest('cluctrl.dom0_details', {}, aDB=_db)
        self.mGetClubox().mSetRequestObj(_reqobj)
        _reqobj = self.mGetClubox().mGetRequestObj()
        _reqobj.mSetUUID("9419f694-9494-11ec-ba6e-565c06664853")
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "True")
        self.mGetContext().mSetRegEntry('ecradbreg_name', DB_REG_ENTRY)
        sys.modules['oracledb'] = MagicMock()
        sys.modules['oracledb'].connect.side_effect = Exception('Mocked connection error')
        os.environ['ORACLE_HOME'] = 'Mock home'
        with patch('exabox.core.AQResponse.ebJobRequest.mGetUUID', return_value="9419f694-9494-11ec-ba6e-565c06664853"),\
             patch('exabox.core.AQResponse.ebJobRequest.mGetAqName', return_value="DEMO_QUEUE"),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetCompleteRequest', return_value=_reqobj):
            _db.mUpdateRequest(_reqobj)
        self.mGetContext().mSetConfigOption('oracleclient_home', None)
        self.mGetContext().mSetRegEntry('ecradbreg_name', None)
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "False")
        ebLogInfo("Unit test for updating request data is successful.")

    def test_13_mUpdateRequestDataCommitException(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for updating request data - This test is"\
                  " executed when there is an exception during transaction commit.")
        _db = ebGetDefaultDB()
        self._stub_db_execute(_db)
        _db.mUpdateResponseSent = MagicMock(return_value=0)
        _reqobj = ebJobRequest('cluctrl.dom0_details', {}, aDB=_db)
        self.mGetClubox().mSetRequestObj(_reqobj)
        _reqobj = self.mGetClubox().mGetRequestObj()
        _reqobj.mSetUUID("9419f694-9494-11ec-ba6e-565c06664853")
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "True")
        self.mGetContext().mSetRegEntry('ecradbreg_name', DB_REG_ENTRY)
        sys.modules['oracledb'] = MagicMock()
        sys.modules['oracledb'].connect.return_value.queue.return_value.deqone.return_value = False
        sys.modules['oracledb'].connect.return_value.commit.side_effect = Exception('Mocked commit error')
        os.environ['ORACLE_HOME'] = 'Mock home'
        with patch('exabox.core.AQResponse.ebJobRequest.mGetUUID', return_value="9419f694-9494-11ec-ba6e-565c06664853"),\
             patch('exabox.core.AQResponse.ebJobRequest.mGetAqName', return_value="DEMO_QUEUE"),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetCompleteRequest', return_value=_reqobj):
            _db.mUpdateRequest(_reqobj)
        self.mGetContext().mSetConfigOption('oracleclient_home', None)
        self.mGetContext().mSetRegEntry('ecradbreg_name', None)
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "False")
        ebLogInfo("Unit test for updating request data is successful.")

    def test_14_mUpdateRequestData(self):
        return
        ebLogInfo("")
        ebLogInfo("Running unit test for updating request data - This test is"\
                  " executed when the response is successfully sent to ecra.")
        _db = ebGetDefaultDB()
        _reqobj = ebJobRequest('cluctrl.dom0_details', {}, aDB=_db)
        self.mGetClubox().mSetRequestObj(_reqobj)
        _reqobj = self.mGetClubox().mGetRequestObj()
        _reqobj.mSetUUID("9419f694-9494-11ec-ba6e-565c06664853")
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "True")
        self.mGetContext().mSetRegEntry('ecradbreg_name', DB_REG_ENTRY)
        sys.modules['oracledb'] = MagicMock()
        sys.modules['oracledb'].connect.return_value.queue.return_value.deqone.return_value = False
        os.environ['ORACLE_HOME'] = 'Mock home'
        with patch('exabox.core.AQResponse.ebJobRequest.mGetUUID', return_value="9419f694-9494-11ec-ba6e-565c06664853"),\
             patch('exabox.core.AQResponse.ebJobRequest.mGetAqName', return_value="DEMO_QUEUE"),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetCompleteRequest', return_value=_reqobj):
            _db.mUpdateRequest(_reqobj)
        self.mGetContext().mSetConfigOption('oracleclient_home', None)
        self.mGetContext().mSetRegEntry('ecradbreg_name', None)
        self.mGetContext().mSetConfigOption('enable_pushstatus_support', "False")
        ebLogInfo("Unit test for updating request data is successful.")

    # Auto-generated test for is_valid_uuid
    def test_15_is_valid_uuid(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for is_valid_uuid.")
        from exabox.core.AQResponse import is_valid_uuid

        self.assertTrue(is_valid_uuid(str(uuid.uuid4())))
        self.assertFalse(is_valid_uuid("not-a-uuid"))
        ebLogInfo("Unit test for is_valid_uuid is successful.")

    # Auto-generated test for getRequestDetails
    def test_16_getRequestDetails_missing_in_db(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for getRequestDetails with missing DB entry.")
        from exabox.core.AQResponse import getRequestDetails

        db_obj = MagicMock()
        db_obj.mGetCompleteRequest.return_value = False
        req_obj = ebJobRequest('cluctrl.dom0_details', {}, aDB=db_obj)
        req_obj.mSetUUID(str(uuid.uuid4()))

        uuid_val, request_val = getRequestDetails(req_obj, db_obj)
        self.assertIsNone(uuid_val)
        self.assertIsNone(request_val)
        db_obj.mGetCompleteRequest.assert_called_once_with(req_obj.mGetUUID())
        ebLogInfo("Unit test for getRequestDetails is successful.")

    # Auto-generated test for getRequestDetails
    def test_17_getRequestDetails_uuid_mismatch(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for getRequestDetails with UUID mismatch.")
        from exabox.core.AQResponse import getRequestDetails

        class FakeRequest(object):
            def __init__(self, *args, **kwargs):
                self._uuid = "fixed-uuid"

            def mLoadRequestFromDB(self, req_uuid):
                self._uuid = "different-uuid"

            def mGetUUID(self):
                return self._uuid

        db_obj = MagicMock()
        valid_uuid = str(uuid.uuid4())
        with patch('exabox.core.AQResponse.ebJobRequest', FakeRequest):
            uuid_val, request_val = getRequestDetails(valid_uuid, db_obj)

        self.assertIsNone(uuid_val)
        self.assertIsNone(request_val)
        ebLogInfo("Unit test for getRequestDetails is successful.")

    # Auto-generated test for getRequestDetails
    def test_18_getRequestDetails_invalid_request(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for getRequestDetails with invalid request.")
        from exabox.core.AQResponse import getRequestDetails

        db_obj = MagicMock()
        uuid_val, request_val = getRequestDetails("not-a-uuid", db_obj)
        self.assertIsNone(uuid_val)
        self.assertIsNone(request_val)
        db_obj.mGetCompleteRequest.assert_not_called()
        ebLogInfo("Unit test for getRequestDetails is successful.")

    # Auto-generated test for getRequestDetails
    def test_19_getRequestDetails_exception_path(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for getRequestDetails exception path.")
        from exabox.core.AQResponse import getRequestDetails

        db_obj = MagicMock()
        req_obj = ebJobRequest('cluctrl.dom0_details', {}, aDB=db_obj)
        req_obj.mSetUUID(str(uuid.uuid4()))
        with patch.object(req_obj, 'mGetUUID', side_effect=Exception('boom')):
            uuid_val, request_val = getRequestDetails(req_obj, db_obj)

        self.assertIsNone(uuid_val)
        self.assertIsNone(request_val)
        ebLogInfo("Unit test for getRequestDetails is successful.")

    # Auto-generated test for getEcraDBDetails
    def test_20_getEcraDBDetails_empty(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for getEcraDBDetails with empty registry.")
        from exabox.core.AQResponse import getEcraDBDetails, ERROR_RESPONSE

        db_obj = MagicMock()
        with patch('exabox.core.AQResponse.get_ecradb_details', return_value={}):
            result = getEcraDBDetails(str(uuid.uuid4()), db_obj)

        self.assertIsNone(result)
        db_obj.mUpdateResponseSent.assert_called_once_with(mock.ANY, ERROR_RESPONSE)
        ebLogInfo("Unit test for getEcraDBDetails is successful.")

    # Auto-generated test for getEcraDBDetails
    def test_21_getEcraDBDetails_exception(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for getEcraDBDetails exception path.")
        from exabox.core.AQResponse import getEcraDBDetails, ERROR_RESPONSE

        db_obj = MagicMock()
        with patch('exabox.core.AQResponse.get_ecradb_details', side_effect=Exception('boom')):
            result = getEcraDBDetails(str(uuid.uuid4()), db_obj)

        self.assertIsNone(result)
        db_obj.mUpdateResponseSent.assert_called_once_with(mock.ANY, ERROR_RESPONSE)
        ebLogInfo("Unit test for getEcraDBDetails is successful.")

    # Auto-generated test for mGetAQName
    def test_22_mGetAQName_empty(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mGetAQName with empty AQ name.")
        from exabox.core.AQResponse import mGetAQName, ERROR_RESPONSE

        db_obj = MagicMock()
        req_obj = MagicMock()
        req_obj.mGetAqName.return_value = ''
        result = mGetAQName(str(uuid.uuid4()), db_obj, req_obj)

        self.assertIsNone(result)
        db_obj.mUpdateResponseSent.assert_called_once_with(mock.ANY, ERROR_RESPONSE)
        ebLogInfo("Unit test for mGetAQName is successful.")

    # Auto-generated test for mUpdateResponseToEcra
    def test_23_mUpdateResponseToEcra_skip_for_exacc(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mUpdateResponseToEcra skip path.")
        from exabox.core.AQResponse import mUpdateResponseToEcra

        called = []

        @mUpdateResponseToEcra
        def _dummy_update(db_obj, request_obj):
            called.append(True)

        context = MagicMock()
        context.mCheckConfigOption.return_value = True
        context.mGetConfigOptions.return_value = {'enable_pushstatus_support': 'True'}
        with patch('exabox.core.AQResponse.get_gcontext', return_value=context), \
             patch('exabox.core.AQResponse.connect_to_ecradb') as mock_connect:
            _dummy_update(MagicMock(), MagicMock())

        self.assertTrue(called)
        mock_connect.assert_not_called()
        ebLogInfo("Unit test for mUpdateResponseToEcra is successful.")

    # Auto-generated test for mUpdateResponseToEcra
    def test_24_mUpdateResponseToEcra_success(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mUpdateResponseToEcra success path.")
        from exabox.core.AQResponse import mUpdateResponseToEcra

        @contextmanager
        def _fake_connect():
            connection = MagicMock()
            msg_props = MagicMock()
            msg_props.msgid.hex.return_value = 'abcd'
            connection.msgproperties.return_value = msg_props
            connection.queue.return_value = MagicMock()
            yield connection

        @mUpdateResponseToEcra
        def _dummy_update(db_obj, request_obj):
            return

        context = MagicMock()
        context.mCheckConfigOption.return_value = False
        context.mGetConfigOptions.return_value = {'enable_pushstatus_support': 'True'}

        db_obj = MagicMock()
        db_obj.mGetCompleteRequest.return_value = True
        req_obj = ebJobRequest('cluctrl.dom0_details', {}, aDB=db_obj)
        req_obj.mSetUUID(str(uuid.uuid4()))

        with patch.object(req_obj, 'mGetAqName', return_value='AQ_NAME'), \
             patch('exabox.core.AQResponse.get_gcontext', return_value=context), \
             patch('exabox.core.AQResponse.get_ecradb_details', return_value={'foo': 'bar'}), \
             patch('exabox.core.AQResponse.mGetResponseData', return_value={'status': 'OK'}), \
             patch('exabox.core.AQResponse.connect_to_ecradb', _fake_connect), \
             patch('exabox.core.AQResponse.ebLogInfo') as aq_info_mock:
            _dummy_update(db_obj, req_obj)

        self.assertTrue(db_obj.mUpdateResponseSent.called)
        args = db_obj.mUpdateResponseSent.call_args[0]
        self.assertEqual(args[0], req_obj.mGetUUID())
        self.assertIsInstance(args[1], datetime)
        self.assertTrue(any("to queue AQ_NAME:ABCD" in call_args[0][0]
                            for call_args in aq_info_mock.call_args_list))
        ebLogInfo("Unit test for mUpdateResponseToEcra is successful.")

    # Auto-generated test for mUpdateResponseToEcra
    def test_25_mUpdateResponseToEcra_enqueue_exception(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mUpdateResponseToEcra enqueue exception.")
        from exabox.core.AQResponse import mUpdateResponseToEcra, ERROR_RESPONSE

        @contextmanager
        def _fake_connect():
            connection = MagicMock()
            msg_props = MagicMock()
            msg_props.msgid.hex.return_value = 'abcd'
            connection.msgproperties.return_value = msg_props
            queue = MagicMock()
            queue.enqone.side_effect = Exception('enqueue failed')
            connection.queue.return_value = queue
            yield connection

        @mUpdateResponseToEcra
        def _dummy_update(db_obj, request_obj):
            return

        context = MagicMock()
        context.mCheckConfigOption.return_value = False
        context.mGetConfigOptions.return_value = {'enable_pushstatus_support': 'True'}

        db_obj = MagicMock()
        db_obj.mGetCompleteRequest.return_value = True
        req_obj = ebJobRequest('cluctrl.dom0_details', {}, aDB=db_obj)
        req_obj.mSetUUID(str(uuid.uuid4()))

        with patch.object(req_obj, 'mGetAqName', return_value='AQ_NAME'), \
             patch('exabox.core.AQResponse.get_gcontext', return_value=context), \
             patch('exabox.core.AQResponse.get_ecradb_details', return_value={'foo': 'bar'}), \
             patch('exabox.core.AQResponse.mGetResponseData', return_value={'status': 'OK'}), \
             patch('exabox.core.AQResponse.connect_to_ecradb', _fake_connect), \
             patch('exabox.core.AQResponse.ebLogWarn') as aq_warn_mock:
            _dummy_update(db_obj, req_obj)

        db_obj.mUpdateResponseSent.assert_called_with(req_obj.mGetUUID(), ERROR_RESPONSE)
        aq_warn_mock.assert_any_call(
            f"Could not send the response to ecra for request id {req_obj.mGetUUID()} queue AQ_NAME: enqueue failed.")
        ebLogInfo("Unit test for mUpdateResponseToEcra is successful.")

    # Auto-generated test for mGetResponseData
    def test_26_mGetResponseData(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mGetResponseData.")
        http_request = MagicMock()
        http_request.extractParams.return_value = None
        status_callback = MagicMock()
        status_callback.executeRequest.return_value = {'status': 'OK'}
        listener = MagicMock()
        listener.mGetStatusCallback.return_value = status_callback

        with patch('exabox.agent.HTTPRequest.HttpRequest', return_value=http_request), \
             patch('exabox.agent.Agent.ebRestHttpListener', return_value=listener):
            response = AQResponse.mGetResponseData(str(uuid.uuid4()))

        self.assertEqual(response, {'status': 'OK'})
        listener.mGetStatusCallback.assert_called_once_with(aAuthenticated=False)
        status_callback.executeRequest.assert_called_once_with(http_request)
        ebLogInfo("Unit test for mGetResponseData is successful.")

    # Auto-generated test for is_valid_uuid
    def test_27_is_valid_uuid(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for is_valid_uuid.")
        self.assertTrue(AQResponse.is_valid_uuid(str(uuid.uuid4())))
        self.assertFalse(AQResponse.is_valid_uuid("not-a-uuid"))
        ebLogInfo("Unit test for is_valid_uuid is successful.")

    # Auto-generated test for getRequestDetails
    def test_28_getRequestDetails_missing_request(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for getRequestDetails missing request.")
        db_obj = MagicMock()
        db_obj.mGetCompleteRequest.return_value = False
        req_obj = ebJobRequest('cluctrl.dom0_details', {}, aDB=db_obj)
        req_obj.mSetUUID(str(uuid.uuid4()))

        uuid_val, request_val = AQResponse.getRequestDetails(req_obj, db_obj)

        self.assertIsNone(uuid_val)
        self.assertIsNone(request_val)
        db_obj.mGetCompleteRequest.assert_called_once_with(req_obj.mGetUUID())
        ebLogInfo("Unit test for getRequestDetails is successful.")

    # Auto-generated test for getRequestDetails
    def test_29_getRequestDetails_uuid_mismatch(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for getRequestDetails uuid mismatch.")
        db_obj = MagicMock()
        uuid_val = str(uuid.uuid4())
        mismatch_uuid = str(uuid.uuid4())
        with patch('exabox.core.AQResponse.ebJobRequest.mLoadRequestFromDB') as load_mock, \
             patch('exabox.core.AQResponse.ebJobRequest.mGetUUID', return_value=mismatch_uuid):
            result_uuid, result_req = AQResponse.getRequestDetails(uuid_val, db_obj)

        self.assertIsNone(result_uuid)
        self.assertIsNone(result_req)
        load_mock.assert_called_once_with(uuid_val)
        ebLogInfo("Unit test for getRequestDetails is successful.")

    # Auto-generated test for getRequestDetails
    def test_30_getRequestDetails_uuid_success(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for getRequestDetails uuid success.")
        db_obj = MagicMock()
        uuid_val = str(uuid.uuid4())
        with patch('exabox.core.AQResponse.ebJobRequest.mLoadRequestFromDB') as load_mock, \
             patch('exabox.core.AQResponse.ebJobRequest.mGetUUID', return_value=uuid_val):
            result_uuid, result_req = AQResponse.getRequestDetails(uuid_val, db_obj)

        self.assertEqual(result_uuid, uuid_val)
        self.assertIsNotNone(result_req)
        load_mock.assert_called_once_with(uuid_val)
        ebLogInfo("Unit test for getRequestDetails is successful.")

    # Auto-generated test for mUpdateResponseToEcra
    def test_31_mUpdateResponseToEcra_pushstatus_disabled(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mUpdateResponseToEcra pushstatus disabled.")
        called = []

        @AQResponse.mUpdateResponseToEcra
        def _dummy_update(db_obj, request_obj):
            called.append(True)

        context = MagicMock()
        context.mCheckConfigOption.return_value = False
        context.mGetConfigOptions.return_value = {'enable_pushstatus_support': 'False'}

        with patch('exabox.core.AQResponse.get_gcontext', return_value=context), \
             patch('exabox.core.AQResponse.connect_to_ecradb') as mock_connect:
            _dummy_update(MagicMock(), MagicMock())

        self.assertTrue(called)
        mock_connect.assert_not_called()
        ebLogInfo("Unit test for mUpdateResponseToEcra is successful.")

    # Auto-generated test for mUpdateResponseToEcra
    def test_32_mUpdateResponseToEcra_connection_none(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mUpdateResponseToEcra connection none.")

        @contextmanager
        def _fake_connect():
            yield None

        @AQResponse.mUpdateResponseToEcra
        def _dummy_update(db_obj, request_obj):
            return

        context = MagicMock()
        context.mCheckConfigOption.return_value = False
        context.mGetConfigOptions.return_value = {'enable_pushstatus_support': 'True'}

        db_obj = MagicMock()
        db_obj.mGetCompleteRequest.return_value = True
        req_obj = ebJobRequest('cluctrl.dom0_details', {}, aDB=db_obj)
        req_obj.mSetUUID(str(uuid.uuid4()))

        with patch.object(req_obj, 'mGetAqName', return_value='AQ_NAME'), \
             patch('exabox.core.AQResponse.get_gcontext', return_value=context), \
             patch('exabox.core.AQResponse.get_ecradb_details', return_value={'foo': 'bar'}), \
             patch('exabox.core.AQResponse.mGetResponseData', return_value={'status': 'OK'}), \
             patch('exabox.core.AQResponse.connect_to_ecradb', _fake_connect):
            _dummy_update(db_obj, req_obj)

        db_obj.mUpdateResponseSent.assert_called_once_with(req_obj.mGetUUID(), AQResponse.ERROR_RESPONSE)
        ebLogInfo("Unit test for mUpdateResponseToEcra is successful.")

    # Auto-generated test for getRequestDetails
    def test_33_getRequestDetails_invalid_uuid_value(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for getRequestDetails invalid uuid value.")
        db_obj = MagicMock()

        uuid_val, request_val = AQResponse.getRequestDetails('not-a-uuid', db_obj)

        self.assertIsNone(uuid_val)
        self.assertIsNone(request_val)
        db_obj.mGetCompleteRequest.assert_not_called()
        ebLogInfo("Unit test for getRequestDetails is successful.")

    # Auto-generated test for getRequestDetails
    def test_34_getRequestDetails_exception(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for getRequestDetails exception path.")
        db_obj = MagicMock()
        req_obj = ebJobRequest('cluctrl.dom0_details', {}, aDB=db_obj)
        req_obj.mSetUUID(str(uuid.uuid4()))

        with patch('exabox.core.AQResponse.ebJobRequest.mGetUUID', side_effect=Exception('boom')):
            uuid_val, request_val = AQResponse.getRequestDetails(req_obj, db_obj)

        self.assertIsNone(uuid_val)
        self.assertIsNone(request_val)
        ebLogInfo("Unit test for getRequestDetails is successful.")

    # Auto-generated test for getEcraDBDetails
    def test_35_getEcraDBDetails_empty_registry(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for getEcraDBDetails empty registry.")
        db_obj = MagicMock()
        db_obj.mUpdateResponseSent = MagicMock()
        uuid_val = str(uuid.uuid4())

        with patch('exabox.core.AQResponse.get_ecradb_details', return_value={}):
            result = AQResponse.getEcraDBDetails(uuid_val, db_obj)

        self.assertIsNone(result)
        db_obj.mUpdateResponseSent.assert_called_once_with(uuid_val, AQResponse.ERROR_RESPONSE)
        ebLogInfo("Unit test for getEcraDBDetails is successful.")

    # Auto-generated test for getEcraDBDetails
    def test_36_getEcraDBDetails_exception(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for getEcraDBDetails exception path.")
        db_obj = MagicMock()
        db_obj.mUpdateResponseSent = MagicMock()
        uuid_val = str(uuid.uuid4())

        with patch('exabox.core.AQResponse.get_ecradb_details', side_effect=Exception('boom')):
            result = AQResponse.getEcraDBDetails(uuid_val, db_obj)

        self.assertIsNone(result)
        db_obj.mUpdateResponseSent.assert_called_once_with(uuid_val, AQResponse.ERROR_RESPONSE)
        ebLogInfo("Unit test for getEcraDBDetails is successful.")

    # Auto-generated test for mGetAQName
    def test_37_mGetAQName_empty(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mGetAQName empty value.")
        db_obj = MagicMock()
        db_obj.mUpdateResponseSent = MagicMock()
        uuid_val = str(uuid.uuid4())
        req_obj = MagicMock()
        req_obj.mGetAqName.return_value = ''

        result = AQResponse.mGetAQName(uuid_val, db_obj, req_obj)

        self.assertIsNone(result)
        db_obj.mUpdateResponseSent.assert_called_once_with(uuid_val, AQResponse.ERROR_RESPONSE)
        ebLogInfo("Unit test for mGetAQName is successful.")

    # Auto-generated test for mGetAQName
    def test_37b_mGetAQName_none(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mGetAQName None value.")
        db_obj = MagicMock()
        db_obj.mUpdateResponseSent = MagicMock()
        uuid_val = str(uuid.uuid4())
        req_obj = MagicMock()
        req_obj.mGetAqName.return_value = None

        result = AQResponse.mGetAQName(uuid_val, db_obj, req_obj)

        self.assertIsNone(result)
        db_obj.mUpdateResponseSent.assert_called_once_with(uuid_val, AQResponse.ERROR_RESPONSE)
        ebLogInfo("Unit test for mGetAQName is successful.")

    def test_38_mUpdateResponseToEcra_ociexacc_skip(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mUpdateResponseToEcra ociexacc skip.")
        called = []

        @AQResponse.mUpdateResponseToEcra
        def _dummy_update(db_obj, request_obj):
            called.append(True)

        context = MagicMock()
        context.mCheckConfigOption.return_value = True
        context.mGetConfigOptions.return_value = {'enable_pushstatus_support': 'True'}

        with patch('exabox.core.AQResponse.get_gcontext', return_value=context), \
             patch('exabox.core.AQResponse.connect_to_ecradb') as mock_connect:
            _dummy_update(MagicMock(), MagicMock())

        self.assertTrue(called)
        mock_connect.assert_not_called()
        ebLogInfo("Unit test for mUpdateResponseToEcra is successful.")

    # Auto-generated test for mUpdateResponseToEcra
    def test_39_mUpdateResponseToEcra_request_details_none(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mUpdateResponseToEcra request details none.")

        @AQResponse.mUpdateResponseToEcra
        def _dummy_update(db_obj, request_obj):
            return

        context = MagicMock()
        context.mCheckConfigOption.return_value = False
        context.mGetConfigOptions.return_value = {'enable_pushstatus_support': 'True'}

        db_obj = MagicMock()

        with patch('exabox.core.AQResponse.get_gcontext', return_value=context), \
             patch('exabox.core.AQResponse.getRequestDetails', return_value=(None, None)), \
             patch('exabox.core.AQResponse.connect_to_ecradb') as mock_connect:
            _dummy_update(db_obj, MagicMock())

        mock_connect.assert_not_called()
        db_obj.mUpdateResponseSent.assert_not_called()
        ebLogInfo("Unit test for mUpdateResponseToEcra is successful.")

    # Auto-generated test for mUpdateResponseToEcra
    def test_40_mUpdateResponseToEcra_response_data_none(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mUpdateResponseToEcra response data none.")

        @AQResponse.mUpdateResponseToEcra
        def _dummy_update(db_obj, request_obj):
            return

        context = MagicMock()
        context.mCheckConfigOption.return_value = False
        context.mGetConfigOptions.return_value = {'enable_pushstatus_support': 'True'}

        db_obj = MagicMock()
        db_obj.mGetCompleteRequest.return_value = True
        req_obj = ebJobRequest('cluctrl.dom0_details', {}, aDB=db_obj)
        req_obj.mSetUUID(str(uuid.uuid4()))

        with patch.object(req_obj, 'mGetAqName', return_value='AQ_NAME'), \
             patch('exabox.core.AQResponse.get_gcontext', return_value=context), \
             patch('exabox.core.AQResponse.get_ecradb_details', return_value={'foo': 'bar'}), \
             patch('exabox.core.AQResponse.mGetResponseData', return_value=None), \
             patch('exabox.core.AQResponse.connect_to_ecradb') as mock_connect:
            _dummy_update(db_obj, req_obj)

        mock_connect.assert_not_called()
        db_obj.mUpdateResponseSent.assert_called_once_with(req_obj.mGetUUID(), AQResponse.ERROR_RESPONSE)
        ebLogInfo("Unit test for mUpdateResponseToEcra is successful.")

    # Auto-generated test for mUpdateResponseToEcra
    def test_41_mUpdateResponseToEcra_aq_name_missing(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mUpdateResponseToEcra aq name missing.")

        @AQResponse.mUpdateResponseToEcra
        def _dummy_update(db_obj, request_obj):
            return

        context = MagicMock()
        context.mCheckConfigOption.return_value = False
        context.mGetConfigOptions.return_value = {'enable_pushstatus_support': 'True'}

        db_obj = MagicMock()
        db_obj.mGetCompleteRequest.return_value = True
        req_obj = ebJobRequest('cluctrl.dom0_details', {}, aDB=db_obj)
        req_obj.mSetUUID(str(uuid.uuid4()))

        with patch.object(req_obj, 'mGetAqName', return_value=None), \
             patch('exabox.core.AQResponse.get_gcontext', return_value=context), \
             patch('exabox.core.AQResponse.get_ecradb_details', return_value={'foo': 'bar'}), \
             patch('exabox.core.AQResponse.connect_to_ecradb') as mock_connect:
            _dummy_update(db_obj, req_obj)

        mock_connect.assert_not_called()
        db_obj.mUpdateResponseSent.assert_called_once_with(req_obj.mGetUUID(), AQResponse.ERROR_RESPONSE)
        ebLogInfo("Unit test for mUpdateResponseToEcra is successful.")

    # Auto-generated test for mGetResponseData
    def test_42_mGetResponseData_success(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mGetResponseData success.")
        uuid_val = str(uuid.uuid4())
        status_callback = MagicMock()
        status_callback.executeRequest.return_value = {"status": "OK"}

        listener_instance = MagicMock()
        listener_instance.mGetStatusCallback.return_value = status_callback

        http_request = MagicMock()
        http_request.extractParams = MagicMock()

        with patch('exabox.agent.Agent.ebRestHttpListener', return_value=listener_instance), \
             patch('exabox.agent.HTTPRequest.HttpRequest', return_value=http_request) as http_request_cls:
            result = AQResponse.mGetResponseData(uuid_val)

        http_request_cls.assert_called_once_with('/Status/{}'.format(uuid_val), 'GET', None, None)
        http_request.extractParams.assert_called_once_with(listener_instance, None)
        listener_instance.mGetStatusCallback.assert_called_once_with(aAuthenticated=False)
        status_callback.executeRequest.assert_called_once_with(http_request)
        self.assertEqual(result, {"status": "OK"})
        ebLogInfo("Unit test for mGetResponseData is successful.")

    # Auto-generated test for mUpdateResponseToEcra
    def test_43_mUpdateResponseToEcra_connection_none(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mUpdateResponseToEcra with no connection.")

        @AQResponse.mUpdateResponseToEcra
        def _dummy_update(db_obj, request_obj):
            return

        context = MagicMock()
        context.mCheckConfigOption.return_value = False
        context.mGetConfigOptions.return_value = {'enable_pushstatus_support': 'True'}

        db_obj = MagicMock()
        db_obj.mGetCompleteRequest.return_value = True
        req_obj = ebJobRequest('cluctrl.dom0_details', {}, aDB=db_obj)
        req_obj.mSetUUID(str(uuid.uuid4()))

        @contextmanager
        def _fake_connect():
            yield None

        with patch.object(req_obj, 'mGetAqName', return_value='AQ_NAME'), \
             patch('exabox.core.AQResponse.get_gcontext', return_value=context), \
             patch('exabox.core.AQResponse.get_ecradb_details', return_value={'foo': 'bar'}), \
             patch('exabox.core.AQResponse.mGetResponseData', return_value={'status': 'OK'}), \
             patch('exabox.core.AQResponse.connect_to_ecradb', _fake_connect):
            _dummy_update(db_obj, req_obj)

        db_obj.mUpdateResponseSent.assert_called_once_with(req_obj.mGetUUID(), AQResponse.ERROR_RESPONSE)
        ebLogInfo("Unit test for mUpdateResponseToEcra is successful.")

    # Auto-generated test for mUpdateResponseToEcra
    def test_43b_mUpdateResponseToEcra_connection_none_context(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mUpdateResponseToEcra with context None connection.")

        @contextmanager
        def _fake_connect():
            yield None

        @AQResponse.mUpdateResponseToEcra
        def _dummy_update(db_obj, request_obj):
            return

        context = MagicMock()
        context.mCheckConfigOption.return_value = False
        context.mGetConfigOptions.return_value = {'enable_pushstatus_support': 'True'}

        db_obj = MagicMock()
        db_obj.mGetCompleteRequest.return_value = True
        req_obj = ebJobRequest('cluctrl.dom0_details', {}, aDB=db_obj)
        req_obj.mSetUUID(str(uuid.uuid4()))

        with patch.object(req_obj, 'mGetAqName', return_value='AQ_NAME'), \
             patch('exabox.core.AQResponse.get_gcontext', return_value=context), \
             patch('exabox.core.AQResponse.get_ecradb_details', return_value={'foo': 'bar'}), \
             patch('exabox.core.AQResponse.mGetResponseData', return_value={'status': 'OK'}), \
             patch('exabox.core.AQResponse.connect_to_ecradb', _fake_connect):
            _dummy_update(db_obj, req_obj)

        db_obj.mUpdateResponseSent.assert_called_once_with(req_obj.mGetUUID(), AQResponse.ERROR_RESPONSE)
        ebLogInfo("Unit test for mUpdateResponseToEcra is successful.")

    def test_43c_mUpdateResponseToEcra_connection_exception(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mUpdateResponseToEcra connection exception.")

        @contextmanager
        def _fake_connect():
            raise RuntimeError("connect failed")
            yield

        @AQResponse.mUpdateResponseToEcra
        def _dummy_update(db_obj, request_obj):
            return

        context = MagicMock()
        context.mCheckConfigOption.return_value = False
        context.mGetConfigOptions.return_value = {'enable_pushstatus_support': 'True'}

        db_obj = MagicMock()
        db_obj.mGetCompleteRequest.return_value = True
        req_obj = ebJobRequest('cluctrl.dom0_details', {}, aDB=db_obj)
        req_obj.mSetUUID(str(uuid.uuid4()))

        with patch.object(req_obj, 'mGetAqName', return_value='AQ_NAME'), \
             patch('exabox.core.AQResponse.get_gcontext', return_value=context), \
             patch('exabox.core.AQResponse.get_ecradb_details', return_value={'foo': 'bar'}), \
             patch('exabox.core.AQResponse.mGetResponseData', return_value={'status': 'OK'}), \
             patch('exabox.core.AQResponse.connect_to_ecradb', _fake_connect):
            _dummy_update(db_obj, req_obj)

        db_obj.mUpdateResponseSent.assert_called_once_with(req_obj.mGetUUID(), AQResponse.ERROR_RESPONSE)
        ebLogInfo("Unit test for mUpdateResponseToEcra is successful.")

    # Auto-generated test for mUpdateResponseToEcra
    def test_44_mUpdateResponseToEcra_ecra_details_exception(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mUpdateResponseToEcra ecra details exception.")

        @AQResponse.mUpdateResponseToEcra
        def _dummy_update(db_obj, request_obj):
            return

        context = MagicMock()
        context.mCheckConfigOption.return_value = False
        context.mGetConfigOptions.return_value = {'enable_pushstatus_support': 'True'}

        db_obj = MagicMock()
        db_obj.mGetCompleteRequest.return_value = True
        req_obj = ebJobRequest('cluctrl.dom0_details', {}, aDB=db_obj)
        req_obj.mSetUUID(str(uuid.uuid4()))

        with patch.object(req_obj, 'mGetAqName', return_value='AQ_NAME'), \
             patch('exabox.core.AQResponse.get_gcontext', return_value=context), \
             patch('exabox.core.AQResponse.get_ecradb_details', side_effect=Exception('boom')), \
             patch('exabox.core.AQResponse.connect_to_ecradb') as mock_connect:
            _dummy_update(db_obj, req_obj)

        mock_connect.assert_not_called()
        db_obj.mUpdateResponseSent.assert_called_once_with(req_obj.mGetUUID(), AQResponse.ERROR_RESPONSE)
        ebLogInfo("Unit test for mUpdateResponseToEcra is successful.")

    # Auto-generated test for mUpdateResponseToEcra
    def test_45_mUpdateResponseToEcra_invalid_request_uuid(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mUpdateResponseToEcra invalid request uuid.")

        @AQResponse.mUpdateResponseToEcra
        def _dummy_update(db_obj, request_obj):
            return

        context = MagicMock()
        context.mCheckConfigOption.return_value = False
        context.mGetConfigOptions.return_value = {'enable_pushstatus_support': 'True'}

        db_obj = MagicMock()

        with patch('exabox.core.AQResponse.get_gcontext', return_value=context), \
             patch('exabox.core.AQResponse.connect_to_ecradb') as mock_connect:
            _dummy_update(db_obj, 'not-a-uuid')

        mock_connect.assert_not_called()
        db_obj.mUpdateResponseSent.assert_not_called()
        ebLogInfo("Unit test for mUpdateResponseToEcra is successful.")

    def test_46_normalize_sync_action(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for _normalize_sync_action.")
        self.assertEqual(AQResponse._normalize_sync_action("start"), "START")
        self.assertEqual(AQResponse._normalize_sync_action("Stop"), "STOP")
        self.assertEqual(AQResponse._normalize_sync_action("INVALID"), "")
        self.assertIsNone(AQResponse._normalize_sync_action(None))
        ebLogInfo("Unit test for _normalize_sync_action is successful.")

    def test_47_ensure_sync_queue_with_retry_success(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for _ensure_sync_queue_with_retry success path.")

        @contextmanager
        def _fake_connect():
            yield object()

        with patch('exabox.core.AQResponse.connect_to_ecradb', new=_fake_connect), \
             patch('exabox.core.AQResponse._ensure_sync_queue_exists') as ensure_mock:
            ensure_mock.return_value = None
            result = AQResponse._ensure_sync_queue_with_retry('SYNCQ', 'worker', 'exit')

        self.assertTrue(result)
        ensure_mock.assert_called_once()
        ebLogInfo("Unit test for _ensure_sync_queue_with_retry success is successful.")

    def test_48_ensure_sync_queue_with_retry_stop(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for _ensure_sync_queue_with_retry stop-aware path.")
        original_state = AQResponse._LIVELINESS_STOP_EVENT.is_set()
        try:
            AQResponse._LIVELINESS_STOP_EVENT.set()
            with patch('exabox.core.AQResponse.connect_to_ecradb') as connect_mock:
                result = AQResponse._ensure_sync_queue_with_retry('SYNCQ', 'worker', 'exit', stop_aware=True)
            self.assertFalse(result)
            connect_mock.assert_not_called()
        finally:
            if not original_state:
                AQResponse._LIVELINESS_STOP_EVENT.clear()
        ebLogInfo("Unit test for _ensure_sync_queue_with_retry stop-aware is successful.")

    def test_49_enqueue_pending_liveliness_once(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for _enqueue_pending_liveliness_once.")
        queue_mock = MagicMock()
        connection = MagicMock()
        connection.queue.return_value = queue_mock
        connection.msgproperties.side_effect = lambda **kwargs: SimpleNamespace(**kwargs)
        connection.commit = MagicMock()

        @contextmanager
        def _fake_connect():
            yield connection

        db_obj = MagicMock()
        db_obj.mFetchAll.return_value = [
            ('uuid-1', 'QUEUE1'),
            ('uuid-2', 'QUEUE1'),
            ('uuid-3', 'QUEUE2'),
            ('uuid-4', None),
            ()
        ]

        with patch('exabox.core.AQResponse.connect_to_ecradb', new=_fake_connect):
            enqueued, queues = AQResponse._enqueue_pending_liveliness_once(db_obj, 'SYNCQ')

        self.assertEqual(enqueued, 3)
        self.assertEqual(queues, 2)
        self.assertEqual(queue_mock.enqone.call_count, 2)
        connection.commit.assert_called_once()
        ebLogInfo("Unit test for _enqueue_pending_liveliness_once is successful.")

    def test_50_enqueue_pending_liveliness_once_no_rows(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for _enqueue_pending_liveliness_once with no rows.")
        db_obj = MagicMock()
        db_obj.mFetchAll.return_value = []

        with patch('exabox.core.AQResponse.connect_to_ecradb') as connect_mock:
            enqueued, queues = AQResponse._enqueue_pending_liveliness_once(db_obj, 'SYNCQ')

        self.assertEqual(enqueued, 0)
        self.assertEqual(queues, 0)
        connect_mock.assert_not_called()
        ebLogInfo("Unit test for _enqueue_pending_liveliness_once empty path is successful.")

    def test_51_start_aqname_sync_worker_starts_thread(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for _start_aqname_sync_worker thread creation.")
        original_thread = AQResponse._AQNAME_SYNC_THREAD
        AQResponse._AQNAME_SYNC_THREAD = None
        try:
            with patch('exabox.core.AQResponse.threading.Thread') as thread_cls:
                fake_thread = MagicMock()
                fake_thread.is_alive.return_value = True
                thread_cls.return_value = fake_thread
                result = AQResponse._start_aqname_sync_worker(target=lambda: None, name="TEST")
            thread_cls.assert_called_once()
            fake_thread.start.assert_called_once()
            self.assertIs(result, fake_thread)
        finally:
            AQResponse._AQNAME_SYNC_THREAD = original_thread
            AQResponse._AQNAME_SYNC_STOP_EVENT.clear()
        ebLogInfo("Unit test for _start_aqname_sync_worker thread creation is successful.")

    def test_52_start_aqname_sync_worker_reuses_thread(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for _start_aqname_sync_worker existing thread.")
        original_thread = AQResponse._AQNAME_SYNC_THREAD
        try:
            existing_thread = MagicMock()
            existing_thread.is_alive.return_value = True
            AQResponse._AQNAME_SYNC_THREAD = existing_thread
            result = AQResponse._start_aqname_sync_worker()
            self.assertIs(result, existing_thread)
        finally:
            AQResponse._AQNAME_SYNC_THREAD = original_thread
        ebLogInfo("Unit test for _start_aqname_sync_worker existing thread is successful.")

    def test_53_stop_aqname_sync_worker_with_connection(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for _stop_aqname_sync_worker with active connection.")
        original_thread = AQResponse._AQNAME_SYNC_THREAD
        original_connection = AQResponse._AQNAME_SYNC_CONNECTION
        try:
            active_thread = MagicMock()
            active_thread.is_alive.return_value = True
            active_connection = MagicMock()
            AQResponse._AQNAME_SYNC_THREAD = active_thread
            AQResponse._AQNAME_SYNC_CONNECTION = active_connection
            AQResponse._stop_aqname_sync_worker()
            self.assertTrue(AQResponse._AQNAME_SYNC_STOP_EVENT.is_set())
            active_connection.cancel.assert_called_once()
            active_connection.close.assert_called_once()
            active_thread.join.assert_called_once()
        finally:
            AQResponse._AQNAME_SYNC_STOP_EVENT.clear()
            AQResponse._AQNAME_SYNC_THREAD = original_thread
            AQResponse._AQNAME_SYNC_CONNECTION = original_connection
        ebLogInfo("Unit test for _stop_aqname_sync_worker with connection is successful.")

    def test_54_start_liveliness_worker_singleton(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for _start_liveliness_worker.")
        original_thread = AQResponse._LIVELINESS_THREAD
        AQResponse._LIVELINESS_THREAD = None
        try:
            with patch('exabox.core.AQResponse.threading.Thread') as thread_cls:
                fake_thread = MagicMock()
                fake_thread.is_alive.return_value = True
                thread_cls.return_value = fake_thread
                AQResponse._start_liveliness_worker()
            thread_cls.assert_called_once()
            fake_thread.start.assert_called_once()
        finally:
            AQResponse._LIVELINESS_THREAD = original_thread
            AQResponse._LIVELINESS_STOP_EVENT.clear()
        ebLogInfo("Unit test for _start_liveliness_worker is successful.")

    def test_55_stop_liveliness_worker_sets_event(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for _stop_liveliness_worker.")
        original_thread = AQResponse._LIVELINESS_THREAD
        try:
            active_thread = MagicMock()
            active_thread.is_alive.return_value = True
            AQResponse._LIVELINESS_THREAD = active_thread
            AQResponse._LIVELINESS_STOP_EVENT.clear()
            AQResponse._stop_liveliness_worker()
            self.assertTrue(AQResponse._LIVELINESS_STOP_EVENT.is_set())
        finally:
            AQResponse._LIVELINESS_STOP_EVENT.clear()
            AQResponse._LIVELINESS_THREAD = original_thread
        ebLogInfo("Unit test for _stop_liveliness_worker is successful.")

    def test_56_mSyncUpEcraQueueNameWithRequest(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mSyncUpEcraQueueNameWithRequest.")
        original_interval = AQResponse.SYNCUP_LIVELINESS_INTERVAL_SECONDS
        AQResponse._AQNAME_SYNC_STOP_EVENT.clear()

        class FakeQueue(object):
            def __init__(self, messages):
                self.messages = list(messages)
                self.deqoptions = SimpleNamespace(wait=None, correlation=None)

            def deqone(self):
                if not self.messages:
                    AQResponse._AQNAME_SYNC_STOP_EVENT.set()
                    raise Exception("done")
                payload = self.messages.pop(0)
                if isinstance(payload, Exception):
                    raise payload
                return SimpleNamespace(payload=payload)

        class FakeConnection(object):
            def __init__(self, messages):
                self.queue_obj = FakeQueue(messages)
                self.commit_calls = 0

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def queue(self, name):
                return self.queue_obj

            def commit(self):
                self.commit_calls += 1

            def msgproperties(self, **kwargs):
                return SimpleNamespace(**kwargs)

            def cancel(self):
                pass

            def close(self):
                pass

        class NullConnection(object):
            def __enter__(self):
                return None

            def __exit__(self, exc_type, exc, tb):
                return False

        class FakeDB(object):
            def __init__(self):
                self.updated = []
                self.fetched = []

            def mUpdateAqName(self, uuid, aq_name):
                self.updated.append((uuid, aq_name))

            def mGetCompleteRequest(self, uuid):
                self.fetched.append(uuid)
                row = [None] * 17
                if uuid == "uuid-existing":
                    row[16] = "QUEUE_A"
                return row

        messages = [
            memoryview(json.dumps({
                "aq_name": "QUEUE_A",
                "status_uuids": ["uuid1", "uuid-existing"],
                "action": "START",
                "liveliness_interval_seconds": "450"
            }).encode("utf-8")),
            json.dumps({
                "aq_name": "QUEUE_A",
                "status_uuids": ["uuid-stop"],
                "action": "STOP"
            }).encode("utf-8"),
            json.dumps({
                "aq_name": "QUEUE_B",
                "status_uuids": "uuid-string",
                "action": "START"
            }).encode("utf-8"),
            json.dumps({
                "aq_name": "QUEUE_C",
                "status_uuids": ["uuid-invalid-action"],
                "action": "INVALID"
            }).encode("utf-8"),
            json.dumps({
                "status_uuids": ["uuid-missing-name"],
                "action": "START"
            }).encode("utf-8"),
            json.dumps({
                "aq_name": "QUEUE_D",
                "status_uuids": [],
                "action": "START"
            }).encode("utf-8"),
            json.dumps({
                "aq_name": "QUEUE_E",
                "status_uuids": ["uuid-publish"],
                "action": "START"
            }).encode("utf-8"),
            b"not-json",
            b"{}",
            None
        ]

        db = FakeDB()
        connection = FakeConnection(messages)
        connection_sequence = [NullConnection(), connection]

        def _publish_wrapper(func):
            def _inner(db_obj, req):
                func(db_obj, req)
                publish_calls.append((db_obj, req))
            return _inner

        publish_calls = []

        def _connect_patched():
            obj = connection_sequence.pop(0) if connection_sequence else connection
            return obj

        try:
            with patch('exabox.core.AQResponse._is_pushstatus_sync_enabled', return_value=True), \
                 patch('exabox.core.AQResponse._ensure_sync_queue_with_retry', return_value=True), \
                 patch('exabox.core.AQResponse.connect_to_ecradb', side_effect=_connect_patched), \
                 patch('exabox.core.AQResponse.mUpdateResponseToEcra', side_effect=_publish_wrapper), \
                 patch('exabox.core.DBStore3.ebExacloudDB', return_value=db), \
                 patch('exabox.core.AQResponse.time.sleep', return_value=None), \
                 patch('exabox.core.AQResponse.ebLogWarn') as aq_warn_mock, \
                 patch('exabox.core.AQResponse.ebLogInfo') as aq_info_mock:
                AQResponse.mSyncUpEcraQueueNameWithRequest()

            self.assertIn(("uuid1", "QUEUE_A"), db.updated)
            self.assertIn(("uuid-stop", None), db.updated)
            self.assertIn(("uuid-publish", "QUEUE_E"), db.updated)
            self.assertNotIn(("uuid-existing", "QUEUE_A"), db.updated)
            self.assertGreaterEqual(connection.commit_calls, 6)
            published_ids = [req for (_, req) in publish_calls]
            self.assertIn("uuid1", published_ids)
            self.assertIn("uuid-existing", published_ids)
            self.assertIn("uuid-publish", published_ids)
            self.assertEqual(AQResponse.SYNCUP_LIVELINESS_INTERVAL_SECONDS, 450)
            aq_warn_mock.assert_any_call(
                "SYNCUP_AQ_NAME  status_uuids is not a list for action START queue QUEUE_B: uuid-string")
            aq_info_mock.assert_any_call(
                "SYNCUP_AQ_NAME  no status_uuids present for action START queue QUEUE_D, skipping.")
            aq_info_mock.assert_any_call(
                "SYNCUP_AQ_NAME STOP cleared aq_name for 1 status uuid(s) from queue QUEUE_A.")
            self.assertIsNone(AQResponse._AQNAME_SYNC_CONNECTION)
        finally:
            AQResponse.SYNCUP_LIVELINESS_INTERVAL_SECONDS = original_interval
            AQResponse._AQNAME_SYNC_STOP_EVENT.clear()

    def test_57_mSyncUpRequestLivelinessWithEcra(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mSyncUpRequestLivelinessWithEcra.")
        AQResponse._LIVELINESS_STOP_EVENT.clear()
        enqueue_calls = []

        def _enqueue_side_effect(db_obj, queue_name):
            enqueue_calls.append(queue_name)
            if len(enqueue_calls) == 1:
                return (None, None)
            if len(enqueue_calls) == 2:
                return (0, 1)
            AQResponse._LIVELINESS_STOP_EVENT.set()
            return (3, 1)

        with patch('exabox.core.AQResponse._is_pushstatus_sync_enabled', return_value=True), \
             patch('exabox.core.AQResponse._ensure_sync_queue_with_retry', return_value=True), \
             patch('exabox.core.AQResponse._retry_failed_responses_once', return_value=0) as retry_mock, \
             patch('exabox.core.AQResponse._enqueue_pending_liveliness_once', side_effect=_enqueue_side_effect), \
             patch('exabox.core.AQResponse._sleep_or_stop', side_effect=[False, False, True]):
            AQResponse.mSyncUpRequestLivelinessWithEcra()

        self.assertEqual(retry_mock.call_count, 3)
        self.assertEqual(enqueue_calls, ['SYNCUP_RAW_QUEUE', 'SYNCUP_RAW_QUEUE', 'SYNCUP_RAW_QUEUE'])
        AQResponse._LIVELINESS_STOP_EVENT.clear()

    def test_57a_mSyncUpRequestLivelinessWithEcra_continues_after_retry_failure(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mSyncUpRequestLivelinessWithEcra retry failure isolation.")
        AQResponse._LIVELINESS_STOP_EVENT.clear()
        enqueue_calls = []

        def _enqueue_side_effect(db_obj, queue_name):
            enqueue_calls.append(queue_name)
            AQResponse._LIVELINESS_STOP_EVENT.set()
            return (1, 1)

        with patch('exabox.core.AQResponse._is_pushstatus_sync_enabled', return_value=True), \
             patch('exabox.core.AQResponse._ensure_sync_queue_with_retry', return_value=True), \
             patch('exabox.core.DBStore3.ebExacloudDB', return_value=MagicMock()), \
             patch('exabox.core.AQResponse._retry_failed_responses_once',
                   side_effect=RuntimeError("retry failed")) as retry_mock, \
             patch('exabox.core.AQResponse._enqueue_pending_liveliness_once',
                   side_effect=_enqueue_side_effect), \
             patch('exabox.core.AQResponse._sleep_or_stop', return_value=True), \
             patch('exabox.core.AQResponse.ebLogWarn') as warn_mock:
            AQResponse.mSyncUpRequestLivelinessWithEcra()

        retry_mock.assert_called_once()
        self.assertEqual(enqueue_calls, ['SYNCUP_RAW_QUEUE'])
        warn_mock.assert_any_call("RESPONSE_AQ retry processing failed: retry failed")
        AQResponse._LIVELINESS_STOP_EVENT.clear()

    def test_57b_retry_failed_responses_once(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for _retry_failed_responses_once.")
        db_obj = MagicMock()
        db_obj.mGetFailedAQResponses.return_value = [
            ('uuid-retry-1',),
            (),
            (None,),
            ('uuid-retry-2',)
        ]
        published = []

        def _publish_wrapper(func):
            def _wrapped(db_obj_arg, uuid):
                published.append(uuid)
            return _wrapped

        with patch('exabox.core.AQResponse.mUpdateResponseToEcra', side_effect=_publish_wrapper):
            retry_count = AQResponse._retry_failed_responses_once(db_obj)

        db_obj.mGetFailedAQResponses.assert_called_once_with(AQResponse.AQ_RESPONSE_RETRY_BATCH_SIZE)
        self.assertEqual(retry_count, 2)
        self.assertEqual(published, ['uuid-retry-1', 'uuid-retry-2'])

    def test_58_ensure_sync_queue_exists_creates_resources(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for _ensure_sync_queue_exists success path.")
        executed = []

        class FakeCursor(object):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def execute(self, sql, params):
                executed.append(sql.strip())
                self._last = sql

            def fetchone(self):
                if "user_queue_tables" in self._last:
                    return (0,)
                if "user_queues" in self._last:
                    return (0,)
                return (1,)

        class FakeConnection(object):
            def __init__(self):
                self.cursor_obj = FakeCursor()
                self.commits = 0

            def cursor(self):
                return self.cursor_obj

            def commit(self):
                self.commits += 1

        conn = FakeConnection()
        AQResponse._ensure_sync_queue_exists(conn, "QUEUE_A", "TABLE_A")
        self.assertIn("BEGIN DBMS_AQADM.CREATE_QUEUE_TABLE(queue_table => :1, queue_payload_type => 'RAW'); END;", executed)
        self.assertIn("BEGIN DBMS_AQADM.START_QUEUE(queue_name => :1, enqueue => TRUE, dequeue => TRUE); END;", executed)
        self.assertEqual(conn.commits, 1)

    def test_59_ensure_sync_queue_exists_rollback_on_failure(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for _ensure_sync_queue_exists failure path.")

        class FailingCursor(object):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def execute(self, sql, params):
                raise RuntimeError("boom")

        class FailingConnection(object):
            def __init__(self):
                self.rollback_called = False

            def cursor(self):
                return FailingCursor()

            def commit(self):
                raise AssertionError("should not commit")

            def rollback(self):
                self.rollback_called = True

        conn = FailingConnection()
        with self.assertRaises(RuntimeError):
            AQResponse._ensure_sync_queue_exists(conn, "QUEUE_B", "TABLE_B")
        self.assertTrue(conn.rollback_called)

    def test_60_mSyncUpEcraQueueNameWithRequest_disabled(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for mSyncUpEcraQueueNameWithRequest disabled path.")
        with patch('exabox.core.AQResponse._is_pushstatus_sync_enabled', return_value=False), \
             patch('exabox.core.AQResponse.connect_to_ecradb') as connect_mock:
            AQResponse.mSyncUpEcraQueueNameWithRequest()
            connect_mock.assert_not_called()
        AQResponse._AQNAME_SYNC_STOP_EVENT.clear()


class AQResponseWorkerHelperCoverageTest(unittest.TestCase):

    def test_ensure_sync_queue_with_retry_retries_on_missing_connection(self):
        calls = []

        @contextmanager
        def _fake_connect():
            calls.append("connect")
            yield None

        with patch('exabox.core.AQResponse.connect_to_ecradb', new=_fake_connect), \
             patch('exabox.core.AQResponse.time.sleep', return_value=None) as sleep_mock, \
             patch('exabox.core.AQResponse._ensure_sync_queue_exists') as ensure_mock:
            result = AQResponse._ensure_sync_queue_with_retry('SYNCQ', 'worker', 'exit')

        self.assertFalse(result)
        self.assertEqual(len(calls), 3)
        self.assertEqual(sleep_mock.call_count, 2)
        ensure_mock.assert_not_called()

    def test_stop_aqname_sync_worker_handles_cancel_close_failures(self):
        original_thread = AQResponse._AQNAME_SYNC_THREAD
        original_connection = AQResponse._AQNAME_SYNC_CONNECTION
        try:
            active_thread = MagicMock()
            active_thread.is_alive.side_effect = [True, True]
            active_connection = MagicMock()
            active_connection.cancel.side_effect = RuntimeError("cancel failed")
            active_connection.close.side_effect = RuntimeError("close failed")
            AQResponse._AQNAME_SYNC_THREAD = active_thread
            AQResponse._AQNAME_SYNC_CONNECTION = active_connection

            with patch('exabox.core.AQResponse.ebLogWarn') as warn_mock:
                AQResponse._stop_aqname_sync_worker()

            active_connection.cancel.assert_called_once()
            active_connection.close.assert_called_once()
            active_thread.join.assert_called_once_with(timeout=5)
            self.assertEqual(warn_mock.call_count, 3)
        finally:
            AQResponse._AQNAME_SYNC_STOP_EVENT.clear()
            AQResponse._AQNAME_SYNC_THREAD = original_thread
            AQResponse._AQNAME_SYNC_CONNECTION = original_connection

    def test_mSyncUpRequestLivelinessWithEcra_disabled(self):
        with patch('exabox.core.AQResponse._is_pushstatus_sync_enabled', return_value=False), \
             patch('exabox.core.AQResponse._enqueue_pending_liveliness_once') as enqueue_mock:
            AQResponse.mSyncUpRequestLivelinessWithEcra()

        enqueue_mock.assert_not_called()

    def test_mSyncUpEcraQueueNameWithRequest_standalone(self):
        original_interval = AQResponse.SYNCUP_LIVELINESS_INTERVAL_SECONDS
        AQResponse._AQNAME_SYNC_STOP_EVENT.clear()

        class FakeQueue(object):
            def __init__(self, messages):
                self.messages = list(messages)
                self.deqoptions = SimpleNamespace(wait=None, correlation=None)

            def deqone(self):
                if not self.messages:
                    AQResponse._AQNAME_SYNC_STOP_EVENT.set()
                    raise Exception("done")
                payload = self.messages.pop(0)
                if isinstance(payload, Exception):
                    raise payload
                return SimpleNamespace(payload=payload)

        class FakeConnection(object):
            def __init__(self, messages):
                self.queue_obj = FakeQueue(messages)
                self.commit_calls = 0

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def queue(self, name):
                return self.queue_obj

            def commit(self):
                self.commit_calls += 1

            def msgproperties(self, **kwargs):
                return SimpleNamespace(**kwargs)

            def cancel(self):
                pass

            def close(self):
                pass

        class NullConnection(object):
            def __enter__(self):
                return None

            def __exit__(self, exc_type, exc, tb):
                return False

        class FakeDB(object):
            def __init__(self):
                self.updated = []
                self.fetched = []

            def mUpdateAqName(self, uuid, aq_name):
                self.updated.append((uuid, aq_name))

            def mGetCompleteRequest(self, uuid):
                self.fetched.append(uuid)
                row = [None] * 17
                if uuid == "uuid-existing":
                    row[16] = "QUEUE_A"
                return row

        messages = [
            memoryview(json.dumps({
                "aq_name": "QUEUE_A",
                "status_uuids": ["uuid1", "uuid-existing"],
                "action": "START",
                "liveliness_interval_seconds": "450"
            }).encode("utf-8")),
            json.dumps({
                "aq_name": "QUEUE_A",
                "status_uuids": ["uuid-stop"],
                "action": "STOP"
            }).encode("utf-8"),
            json.dumps({
                "aq_name": "QUEUE_B",
                "status_uuids": "uuid-string",
                "action": "START"
            }).encode("utf-8"),
            json.dumps({
                "aq_name": "QUEUE_C",
                "status_uuids": ["uuid-invalid-action"],
                "action": "INVALID"
            }).encode("utf-8"),
            json.dumps({
                "status_uuids": ["uuid-missing-name"],
                "action": "START"
            }).encode("utf-8"),
            json.dumps({
                "aq_name": "QUEUE_D",
                "status_uuids": [],
                "action": "START"
            }).encode("utf-8"),
            json.dumps({
                "aq_name": "QUEUE_E",
                "status_uuids": ["uuid-publish"],
                "action": "START"
            }).encode("utf-8"),
            b"not-json",
            b"{}",
            None
        ]

        db = FakeDB()
        connection = FakeConnection(messages)
        connection_sequence = [NullConnection(), connection]
        publish_calls = []

        def _publish_wrapper(func):
            def _inner(db_obj, req):
                func(db_obj, req)
                publish_calls.append((db_obj, req))
            return _inner

        def _connect_patched():
            obj = connection_sequence.pop(0) if connection_sequence else connection
            return obj

        try:
            with patch('exabox.core.AQResponse._is_pushstatus_sync_enabled', return_value=True), \
                 patch('exabox.core.AQResponse._ensure_sync_queue_with_retry', return_value=True), \
                 patch('exabox.core.AQResponse.connect_to_ecradb', side_effect=_connect_patched), \
                 patch('exabox.core.AQResponse.mUpdateResponseToEcra', side_effect=_publish_wrapper), \
                 patch('exabox.core.DBStore3.ebExacloudDB', return_value=db), \
                 patch('exabox.core.AQResponse.time.sleep', return_value=None):
                AQResponse.mSyncUpEcraQueueNameWithRequest()

            self.assertIn(("uuid1", "QUEUE_A"), db.updated)
            self.assertIn(("uuid-stop", None), db.updated)
            self.assertIn(("uuid-publish", "QUEUE_E"), db.updated)
            self.assertNotIn(("uuid-existing", "QUEUE_A"), db.updated)
            self.assertGreaterEqual(connection.commit_calls, 6)
            published_ids = [req for (_, req) in publish_calls]
            self.assertIn("uuid1", published_ids)
            self.assertIn("uuid-existing", published_ids)
            self.assertIn("uuid-publish", published_ids)
            self.assertEqual(AQResponse.SYNCUP_LIVELINESS_INTERVAL_SECONDS, 450)
            self.assertIsNone(AQResponse._AQNAME_SYNC_CONNECTION)
        finally:
            AQResponse.SYNCUP_LIVELINESS_INTERVAL_SECONDS = original_interval
            AQResponse._AQNAME_SYNC_STOP_EVENT.clear()

    def test_mSyncUpRequestLivelinessWithEcra_standalone(self):
        AQResponse._LIVELINESS_STOP_EVENT.clear()
        enqueue_calls = []

        def _enqueue_side_effect(db_obj, queue_name):
            enqueue_calls.append(queue_name)
            if len(enqueue_calls) == 1:
                return (None, None)
            if len(enqueue_calls) == 2:
                return (0, 1)
            AQResponse._LIVELINESS_STOP_EVENT.set()
            return (3, 1)

        with patch('exabox.core.AQResponse._is_pushstatus_sync_enabled', return_value=True), \
             patch('exabox.core.AQResponse._ensure_sync_queue_with_retry', return_value=True), \
             patch('exabox.core.AQResponse._enqueue_pending_liveliness_once', side_effect=_enqueue_side_effect), \
             patch('exabox.core.DBStore3.ebExacloudDB', return_value=MagicMock()), \
             patch('exabox.core.AQResponse._sleep_or_stop', side_effect=[False, False, True]):
            AQResponse.mSyncUpRequestLivelinessWithEcra()

        self.assertEqual(enqueue_calls, ['SYNCUP_RAW_QUEUE', 'SYNCUP_RAW_QUEUE', 'SYNCUP_RAW_QUEUE'])
        AQResponse._LIVELINESS_STOP_EVENT.clear()


class AQResponseStandaloneCoverageTest(unittest.TestCase):
    """Runs the mock-only AQResponse tests without the DB-backed exatest bootstrap."""


for _test_name in [
        'test_15_is_valid_uuid',
        'test_16_getRequestDetails_missing_in_db',
        'test_17_getRequestDetails_uuid_mismatch',
        'test_18_getRequestDetails_invalid_request',
        'test_19_getRequestDetails_exception_path',
        'test_20_getEcraDBDetails_empty',
        'test_21_getEcraDBDetails_exception',
        'test_22_mGetAQName_empty',
        'test_23_mUpdateResponseToEcra_skip_for_exacc',
        'test_24_mUpdateResponseToEcra_success',
        'test_25_mUpdateResponseToEcra_enqueue_exception',
        'test_26_mGetResponseData',
        'test_27_is_valid_uuid',
        'test_28_getRequestDetails_missing_request',
        'test_29_getRequestDetails_uuid_mismatch',
        'test_30_getRequestDetails_uuid_success',
        'test_31_mUpdateResponseToEcra_pushstatus_disabled',
        'test_32_mUpdateResponseToEcra_connection_none',
        'test_33_getRequestDetails_invalid_uuid_value',
        'test_34_getRequestDetails_exception',
        'test_35_getEcraDBDetails_empty_registry',
        'test_36_getEcraDBDetails_exception',
        'test_37_mGetAQName_empty',
        'test_37b_mGetAQName_none',
        'test_38_mUpdateResponseToEcra_ociexacc_skip',
        'test_39_mUpdateResponseToEcra_request_details_none',
        'test_40_mUpdateResponseToEcra_response_data_none',
        'test_41_mUpdateResponseToEcra_aq_name_missing',
        'test_42_mGetResponseData_success',
        'test_43_mUpdateResponseToEcra_connection_none',
        'test_43b_mUpdateResponseToEcra_connection_none_context',
        'test_43c_mUpdateResponseToEcra_connection_exception',
        'test_44_mUpdateResponseToEcra_ecra_details_exception',
        'test_45_mUpdateResponseToEcra_invalid_request_uuid',
        'test_46_normalize_sync_action',
        'test_47_ensure_sync_queue_with_retry_success',
        'test_48_ensure_sync_queue_with_retry_stop',
        'test_49_enqueue_pending_liveliness_once',
        'test_50_enqueue_pending_liveliness_once_no_rows',
        'test_51_start_aqname_sync_worker_starts_thread',
        'test_52_start_aqname_sync_worker_reuses_thread',
        'test_53_stop_aqname_sync_worker_with_connection',
        'test_54_start_liveliness_worker_singleton',
        'test_55_stop_liveliness_worker_sets_event',
        'test_57a_mSyncUpRequestLivelinessWithEcra_continues_after_retry_failure',
        'test_57b_retry_failed_responses_once',
        'test_58_ensure_sync_queue_exists_creates_resources',
        'test_59_ensure_sync_queue_exists_rollback_on_failure',
        'test_60_mSyncUpEcraQueueNameWithRequest_disabled',
]:
    setattr(AQResponseStandaloneCoverageTest, _test_name, getattr(ebTestAQResponse, _test_name))

if __name__ == '__main__':
    unittest.main() 
