#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/proxy/tests_ebProxyJobRequest.py /main/1 2021/08/23 23:05:34 aypaul Exp $
#
# tests_ebProxyJobRequest.py
#
# Copyright (c) 2021, Oracle and/or its affiliates. 
#
#    NAME
#      tests_ebProxyJobRequest.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      08/16/21 - Creation
#
import json
import unittest
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
import warnings
from exabox.proxy.ebProxyJobRequest import ebProxyJobRequest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.DBStore import ebGetDefaultDB
from ast import literal_eval
import uuid

class ebTestProxyJobRequest(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestProxyJobRequest, self).setUpClass(aGenerateDatabase=True)
        warnings.filterwarnings("ignore")

    def test_mValidateConstrcutor(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on class ebTestProxyJobRequest constructor.")
        currentParams = {"uuid" : "287911f0-f9c5-11eb-9181-fa163e8a4946"}
        proxyJobRequest = ebProxyJobRequest("CLUCtrl.POST", currentParams)

        self.assertEqual(proxyJobRequest.mGetUUID(), "287911f0-f9c5-11eb-9181-fa163e8a4946")
        self.assertEqual(proxyJobRequest.mGetCmdType(), "CLUCtrl.POST")
        self.assertEqual(proxyJobRequest.mGetType(), "CLUCtrl")
        self.assertEqual(proxyJobRequest.mGetCmd(), "POST")
        self.assertEqual(proxyJobRequest.mGetParams().get("uuid",None), "287911f0-f9c5-11eb-9181-fa163e8a4946")
        self.assertEqual(proxyJobRequest.mGetOptions().uuid, "287911f0-f9c5-11eb-9181-fa163e8a4946")

        ebLogInfo("Unit test on ebProxyJobRequest constructor succeeded.")

    def test_mValidateSettersGetters(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on class ebTestProxyJobRequest constructor.")
        currentParams = {"uuid" : "287911f0-f9c5-11eb-9181-fa163e8a4946"}
        proxyJobRequest = ebProxyJobRequest("CLUCtrl.POST", currentParams)

        proxyJobRequest.mSetCmdType("Status.GET")
        proxyJobRequest.mSetUUID("1d1f8ba6-f9b4-11eb-9181-fa163e8a4946")
        proxyJobRequest.mSetParams({"dbName" : "sampleDBName"})
        proxyJobRequest.mSetUrlFullPath("http://slc17qpf.us.oracle.com:7080/Status/1d1f8ba6-f9b4-11eb-9181-fa163e8a4946")
        proxyJobRequest.mSetUrlHeaders({"Authorization": "Basic YWxhZGRpbjpvcGVuc2VzYW1l"})
        proxyJobRequest.mSetRespBody("Dummy Response Body")
        proxyJobRequest.mSetRespCode(200)
        proxyJobRequest.mSetReqType("GET")
        proxyJobRequest.mSetReqBody("Dummy Request Body")


        self.assertEqual(proxyJobRequest.mGetReqBody(), "Dummy Request Body")
        self.assertEqual(proxyJobRequest.mGetReqType(), "GET")
        self.assertEqual(proxyJobRequest.mGetRespCode(), 200)
        self.assertEqual(proxyJobRequest.mGetRespBody(), "Dummy Response Body")
        self.assertEqual(proxyJobRequest.mGetUrlHeaders().get("Authorization",None), "Basic YWxhZGRpbjpvcGVuc2VzYW1l")
        self.assertEqual(proxyJobRequest.mGetUrlFullPath(), "http://slc17qpf.us.oracle.com:7080/Status/1d1f8ba6-f9b4-11eb-9181-fa163e8a4946")
        self.assertEqual(proxyJobRequest.mGetOptions().dbName, "sampleDBName")
        self.assertEqual(proxyJobRequest.mGetUUID(), "1d1f8ba6-f9b4-11eb-9181-fa163e8a4946")
        self.assertEqual(proxyJobRequest.mGetCmdType(), "Status.GET")
        self.assertEqual(proxyJobRequest.mGetType(), "Status")
        self.assertEqual(proxyJobRequest.mGetCmd(), "GET")

    def test_mValidateDBEntries(self):

        mysqlDB = ebGetDefaultDB()
        mysqlDB.mCreateProxyRequestsTable()
        ebLogInfo("")
        ebLogInfo("Running unit test on class ebTestProxyJobRequest constructor.")
        currentParams = {"uuid" : "0000-0000-0000-0000"}
        proxyJobRequest = ebProxyJobRequest("CLUCtrl.POST", currentParams, mysqlDB)

        newUUID = str(uuid.uuid1())
        proxyJobRequest.mSetCmdType("Status.GET")
        proxyJobRequest.mSetUUID(newUUID)
        proxyJobRequest.mSetParams({"dbName" : "sampleDBName"})
        proxyJobRequest.mSetUrlFullPath("http://slc17qpf.us.oracle.com:7080/Status/{}".format(newUUID))
        proxyJobRequest.mSetUrlHeaders({"Authorization": "Basic YWxhZGRpbjpvcGVuc2VzYW1l"})
        proxyJobRequest.mSetRespBody("Dummy Response Body")
        proxyJobRequest.mSetRespCode(200)
        proxyJobRequest.mSetReqType("GET")
        proxyJobRequest.mSetReqBody("Dummy Request Body")

        proxyJobRequest.mRegister()
        newProxyJobRequest = ebProxyJobRequest("DUMMY.CMD", {}, mysqlDB)
        newProxyJobRequest.mLoadRequestFromDB(newUUID)

        self.assertEqual(newProxyJobRequest.mGetReqBody(), "Dummy Request Body")
        self.assertEqual(newProxyJobRequest.mGetReqType(), "GET")
        self.assertEqual(newProxyJobRequest.mGetRespCode(), 200)
        self.assertEqual(newProxyJobRequest.mGetRespBody(), "Dummy Response Body")
        self.assertEqual(literal_eval(newProxyJobRequest.mGetUrlHeaders()).get("Authorization",None), "Basic YWxhZGRpbjpvcGVuc2VzYW1l")
        self.assertEqual(newProxyJobRequest.mGetUrlFullPath(), "http://slc17qpf.us.oracle.com:7080/Status/{}".format(newUUID))
        self.assertEqual(newProxyJobRequest.mGetOptions().dbName, "sampleDBName")
        self.assertEqual(newProxyJobRequest.mGetUUID(), newUUID)
        self.assertEqual(newProxyJobRequest.mGetCmdType(), "Status.GET")
        self.assertEqual(newProxyJobRequest.mGetType(), "Status")
        self.assertEqual(newProxyJobRequest.mGetCmd(), "GET")

if __name__ == "__main__":
    unittest.main()