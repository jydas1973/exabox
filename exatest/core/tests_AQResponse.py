#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/core/tests_AQResponse.py /main/2 2025/08/22 07:11:21 aypaul Exp $
#
# tests_AQResponse.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_AQResponse.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    03/02/26 - ER 38951653: Increase code coverage
#    aararora    05/21/25 - Tests methods related to sending response to ecra using AQ
#    aararora    05/21/25 - Creation
#
import os
import sys
import unittest
import uuid
from contextlib import contextmanager
from datetime import datetime
from unittest import mock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.core import AQResponse
from exabox.core.DBStore import ebGetDefaultDB
from exabox.agent.ebJobRequest import ebJobRequest
from unittest.mock import patch, MagicMock

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
             patch('exabox.core.AQResponse.connect_to_ecradb', _fake_connect):
            _dummy_update(db_obj, req_obj)

        self.assertTrue(db_obj.mUpdateResponseSent.called)
        args = db_obj.mUpdateResponseSent.call_args[0]
        self.assertEqual(args[0], req_obj.mGetUUID())
        self.assertIsInstance(args[1], datetime)
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
             patch('exabox.core.AQResponse.connect_to_ecradb', _fake_connect):
            _dummy_update(db_obj, req_obj)

        db_obj.mUpdateResponseSent.assert_called_with(req_obj.mGetUUID(), ERROR_RESPONSE)
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

        db_obj.mUpdateResponseSent.assert_not_called()
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

    # Auto-generated test for mUpdateResponseToEcra
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

        with patch('exabox.core.AQResponse.get_gcontext', return_value=context), \
             patch('exabox.core.AQResponse.get_ecradb_details', return_value={'foo': 'bar'}), \
             patch('exabox.core.AQResponse.mGetAQName', return_value=None), \
             patch('exabox.core.AQResponse.connect_to_ecradb') as mock_connect:
            _dummy_update(db_obj, req_obj)

        mock_connect.assert_not_called()
        db_obj.mUpdateResponseSent.assert_not_called()
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

        db_obj.mUpdateResponseSent.assert_not_called()
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

        db_obj.mUpdateResponseSent.assert_not_called()
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

if __name__ == '__main__':
    unittest.main() 
