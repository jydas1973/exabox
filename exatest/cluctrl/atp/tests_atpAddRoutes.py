"""

 $Header: 

 Copyright (c) 2018, 2020, Oracle and/or its affiliates. All rights reserved.

 NAME:
      tests_atpAddRoutes.py - Unitest for add routes ATP

 DESCRIPTION:
      Run tests for the class ebSubnetIp using Unitest

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
        vgerard    09/06/18 - Creation of the file for exacloud unit test
"""

import unittest
import json
from exabox.ovm.atpaddroutes import ATPAddBackupRoutes 

class ATPMockExecution(object):
    def __init__(self):
        self.__stagedCmds = []
    def mExecute(self, aStaging, aDomUs):
        self.__stagedCmds = aStaging.getCommands()
    def getCommands(self):
        return self.__stagedCmds

class ebTestATPAddBackupRoutes(unittest.TestCase):

    def setUp(self):
       self.__mock = ATPMockExecution()
   	
    def test_ValidRealisticPayload(self):
       _validPayload =\
'''
{
  "routes":[
     {
        "cidr":"10.0.0.112\/29",
        "hostinfo":[
           {
              "ip":"10.0.0.117",
              "domainname":"scanip.s1536284491045.dibtest.oraclevcn.com",
              "write_hostfile":"force"
           }
        ]
     }
  ]
}
'''
       # Double \\ is in fact \ in command , it is just the escape of the \ for python string
       _expectations = ['/var/opt/oracle/misc/db-route add -net 10.0.0.112 netmask 255.255.255.248 dev bondeth1',
                        'grep -qe "10\\.0\\.0\\.117\\s" /etc/hosts || echo "10.0.0.117 scanip.s1536284491045.dibtest.oraclevcn.com" >> /etc/hosts']
       _json = json.loads(_validPayload)
       atproutes = ATPAddBackupRoutes(_json)
       atproutes.mExecute([],'bondeth1',self.__mock)
       self.assertEqual(_expectations,self.__mock.getCommands())

    def test_validMiniPayloads(self):
       _expectations = ['/var/opt/oracle/misc/db-route add -net 10.10.10.0 netmask 255.255.255.128 dev bondeth1',
                        '/var/opt/oracle/misc/db-route add -net 5.5.5.5 netmask 255.255.224.0 dev bondeth1']
       atproutes = ATPAddBackupRoutes(json.loads('{"routes":[{"cidr":"10.10.10.0/25"},{"cidr":"5.5.5.5/19"}]}'))
       atproutes.mExecute([],'bondeth1',self.__mock)
       self.assertEqual(_expectations,self.__mock.getCommands())

    def test_InvalidPayloads(self):
        self.assertRaises(ValueError, ATPAddBackupRoutes, json.loads('{}')) 
        self.assertRaises(ValueError, ATPAddBackupRoutes, json.loads('{"dewqdewq":43}')) 
        self.assertRaises(ValueError, ATPAddBackupRoutes, json.loads('{"routes":[]}')) 
        self.assertRaises(ValueError, ATPAddBackupRoutes, json.loads('{"routes":[{"dsdsa":"sss"}]}')) 
        self.assertRaises(ValueError, ATPAddBackupRoutes, json.loads('{"routes":[{"cidr":"abcd"}]}')) 
        self.assertRaises(ValueError, ATPAddBackupRoutes, json.loads('{"routes":[{"cidr":"10.10.10.0/25"},{"cidr":"invalid"}]}')) 
        self.assertRaises(ValueError, ATPAddBackupRoutes, json.loads('{"routes":[{"cidr":"10.10.10.0/11111"}]}')) 
        self.assertRaises(ValueError, ATPAddBackupRoutes, json.loads('{"routes":[{"cidr":"10.10.10.400/25"}]}')) 
        self.assertRaises(ValueError, ATPAddBackupRoutes, json.loads('{"routes":[{"cidr":"10.10.10.200/33"}]}')) 
        # invalid IP in scan clause
        self.assertRaises(ValueError, ATPAddBackupRoutes, json.loads('{"routes":[{"cidr":"10.10.10.0/25","hostinfo":[{"ip":"dwdw","domainname":"dwddw"}]}]}')) 
        self.assertRaises(ValueError, ATPAddBackupRoutes, json.loads('{"routes":[{"cidr":"10.10.10.0/25","hostinfo":[{"ip":"127.0.0.1","domainname":"dwddw", "write_hostfile":"invalid"}]}]}')) 

    def test_ValidRealisticPayloadWithAuto(self):
       _validPayload =\
'''
{
  "routes":[
     {
        "cidr":"10.0.0.112\/29",
        "hostinfo":[
           {
              "ip":"10.0.0.117",
              "domainname":"scanip.s1536284491045.dibtest.oraclevcn.com",
              "write_hostfile":"auto"
           }
        ]
     }
  ]
}
'''
       _expectations = ['/var/opt/oracle/misc/db-route add -net 10.0.0.112 netmask 255.255.255.248 dev bondeth1',
                        'dig +search +short scanip.s1536284491045.dibtest.oraclevcn.com || grep -qe "10\\.0\\.0\\.117\\s" /etc/hosts || echo "10.0.0.117 scanip.s1536284491045.dibtest.oraclevcn.com" >> /etc/hosts']
       _json = json.loads(_validPayload)
       atproutes = ATPAddBackupRoutes(_json)
       atproutes.mExecute([],'bondeth1', self.__mock)
       self.assertEqual(_expectations,self.__mock.getCommands())

    def test_ValidComplexPayload(self):
       _validPayload =\
'''
{
  "routes":[
     {
        "cidr":"10.0.0.112\/29",
        "hostinfo":[
           {
              "ip":"10.0.0.117",
              "domainname":"scanip.s1536284491045.dibtest.oraclevcn.com",
              "write_hostfile":"auto"
           },
           {
              "ip":"10.0.0.118",
              "domainname":"scanip.s1536284491045.dibtest.oraclevcn.com",
              "write_hostfile":"force"
           }
        ]
     },
     {
        "cidr":"20.0.0.110\/10",
        "hostinfo":[
           {
              "ip":"10.0.0.117",
              "domainname":"scanip.s1536284491045.dibtest.oraclevcn.com"
           }
        ]
     },
     {
        "cidr":"30.0.0.110\/10"
     }
  ]
}
'''
       _expectations = ['/var/opt/oracle/misc/db-route add -net 10.0.0.112 netmask 255.255.255.248 dev bondeth1',
                        'dig +search +short scanip.s1536284491045.dibtest.oraclevcn.com || grep -qe "10\\.0\\.0\\.117\\s" /etc/hosts || echo "10.0.0.117 scanip.s1536284491045.dibtest.oraclevcn.com" >> /etc/hosts',
                        'grep -qe "10\\.0\\.0\\.118\\s" /etc/hosts || echo "10.0.0.118 scanip.s1536284491045.dibtest.oraclevcn.com" >> /etc/hosts',
                        '/var/opt/oracle/misc/db-route add -net 20.0.0.110 netmask 255.192.0.0 dev bondeth1',
                        'dig +search +short scanip.s1536284491045.dibtest.oraclevcn.com || grep -qe "10\\.0\\.0\\.117\\s" /etc/hosts || echo "10.0.0.117 scanip.s1536284491045.dibtest.oraclevcn.com" >> /etc/hosts',
                        '/var/opt/oracle/misc/db-route add -net 30.0.0.110 netmask 255.192.0.0 dev bondeth1']


       _json = json.loads(_validPayload)
       atproutes = ATPAddBackupRoutes(_json)
       atproutes.mExecute([],'bondeth1', self.__mock)
       self.assertEqual(_expectations,self.__mock.getCommands())



if __name__ == '__main__':
    unittest.main()

