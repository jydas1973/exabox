#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/core/tests_AQResponse.py /main/2 2025/08/22 07:11:21 aypaul Exp $
#
# tests_AQResponse.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
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
#    aararora    05/21/25 - Tests methods related to sending response to ecra using AQ
#    aararora    05/21/25 - Creation
#
import os
import sys
import unittest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
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

    def test_01_mUpdateRequestDataPushDisabled(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for updating request data - This test is"\
                  " executed when the push status support is not enabled but the"\
                  " given uuid is present in the DB")
        _db = ebGetDefaultDB()
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

if __name__ == '__main__':
    unittest.main() 