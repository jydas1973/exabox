"""

 $Header: 

 Copyright (c) 2020, 2021, Oracle and/or its affiliates. 

 NAME:
      tests_proxy_client.py - Unitest for PROXY Client

 DESCRIPTION:
      Run tests for Proxy Client

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       vgerard  10/23/20 - Creation of the file
"""

import unittest

from exabox.core.Context import get_gcontext
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.agent.ProxyClient import ProxyClient, ProxyOperation

class ebTestProxyClient(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)

    def setUp(self):
        # DefaultValue
        get_gcontext().mSetConfigOption('proxy_host','myProxy')
        get_gcontext().mSetConfigOption('proxy_port','12345')
        self.__proxy_client = ProxyClient(aTestMode=True)

   
    def test_mProxyREGISTER(self): 
        request, data =self.__proxy_client.mSendOperation(ProxyOperation.REGISTER)
        self.assertEqual(request,"http://myProxy:12345/ecinstmaintenance")
        self.assertEqual(data['op'],'register')
        self.assertRegex(data['oeda_version'],r'\d\d\d\d\d\d')
        # To see full payload, uncomment the following line
        # print (f"REG: {request} / \n {data}")


    def test_mProxyDEREGISTER(self): 
        request, data =self.__proxy_client.mSendOperation(ProxyOperation.DEREGISTER)
        self.assertEqual(request,"http://myProxy:12345/ecinstmaintenance")
        self.assertEqual(data['op'],'deregister')


    def test_mProxyUPDATE_STATUS_SUSPEND(self): 
        request, data =self.__proxy_client.mSendOperation(ProxyOperation.UPDATE_STATUS_SUSPEND)
        self.assertEqual(request,"http://myProxy:12345/ecinstmaintenance")
        self.assertEqual(data['op'],'update')
        self.assertEqual(data['key'],'status')
        self.assertEqual(data['value'],'Suspend')
        
if __name__ == '__main__':
    unittest.main() 
