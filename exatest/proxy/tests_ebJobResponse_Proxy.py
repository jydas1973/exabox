#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/proxy/tests_ebJobResponse_Proxy.py /main/1 2021/08/23 23:05:34 aypaul Exp $
#
# tests_ebJobResponse_Proxy.py
#
# Copyright (c) 2021, Oracle and/or its affiliates. 
#
#    NAME
#      tests_ebJobResponse_Proxy.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      08/19/21 - Creation
#
import json
import unittest
from exabox.log.LogMgr import ebLogInfo
import warnings
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.proxy.ebJobResponse import ebJobResponse
from ast import literal_eval
import uuid

class ebTestProxyJobResponse(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestProxyJobResponse, self).setUpClass()
        warnings.filterwarnings("ignore")

    def test_ProxyJobResponse(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on class ebJobResponse.mPopulate.")
        proxyJobResponse = ebJobResponse()

        newUUID = str(uuid.uuid1)
        entriesToPopulate = ['uuid','status','statusinfo','success','start_time','end_time','cmd',
        'error','error_str','body','data','patch_list','statuscode','xml']
        valuesToPopulate = [newUUID,'Pending','create VM completed','True','Thu Aug 19 01:23:26 PDT 2021','Fri Aug 20 01:23:26 PDT 2021',
        'selinux_update','700-890','No errors','[This is a sample body]', 'Sample data', '[]', '202', 'Sample XML']

        for index, entry in enumerate(entriesToPopulate):
            ebLogInfo("{0} -> {1}".format(entry, valuesToPopulate[index]))
            proxyJobResponse.mPopulate(entry,valuesToPopulate[index])
        
        proxyJobResponse.mSetParams("{\"dbName\": \"myDB\"}")

        _responseJSON = proxyJobResponse.mToJson()
        self.assertEqual(_responseJSON.get("status",None), 'Pending')
        self.assertEqual(_responseJSON.get("success",None), 'True')
        self.assertEqual(_responseJSON.get("body",None), '[This is a sample body]')
        self.assertEqual(_responseJSON.get("xml",None), 'Sample XML')
        self.assertEqual(_responseJSON.get("error",None), '700-890')
        self.assertEqual(_responseJSON.get("error_str",None), 'No errors')

        self.assertEqual(proxyJobResponse.mGetXml(), 'Sample XML')
        self.assertEqual(proxyJobResponse.mGetSuccess(), 'True')
        self.assertEqual(proxyJobResponse.mGetStatus(), 'Pending')
        self.assertEqual(proxyJobResponse.mGetStatusInfo(), 'create VM completed')
        self.assertEqual(proxyJobResponse.mGetStatusCode(), '202')
        self.assertEqual(proxyJobResponse.mGetUUID(), newUUID)
        self.assertEqual(proxyJobResponse.mGetTimeStampStart(), 'Thu Aug 19 01:23:26 PDT 2021')
        self.assertEqual(proxyJobResponse.mGetTimeStampEnd(), 'Fri Aug 20 01:23:26 PDT 2021')
        self.assertEqual(proxyJobResponse.mGetCmdType(), 'selinux_update')
        self.assertEqual(proxyJobResponse.mGetParams(), "{\"dbName\": \"myDB\"}")
        self.assertEqual(proxyJobResponse.mGetError(), '700-890')
        self.assertEqual(proxyJobResponse.mGetErrorStr(), 'No errors')
        self.assertEqual(proxyJobResponse.mGetBody(), '[This is a sample body]')
        self.assertEqual(proxyJobResponse.mGetData(), 'Sample data')
        self.assertEqual(proxyJobResponse.mGetPatchList(), '[]')

if __name__ == "__main__":
    unittest.main()