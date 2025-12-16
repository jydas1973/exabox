"""

 $Header: 

 Copyright (c) 2020, 2025, Oracle and/or its affiliates.

 NAME:
      tests_clusparse.py - Unitest for vmbackup.py module

 DESCRIPTION:
      Run tests for the methods of clusparse.py

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       ajayasin 03/06/22 - new ut file for clusparse.py
       ajayasin 04/03/22 - new ut file for clusparse.py
"""

import unittest

from random import shuffle

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.ovm.clusparse import ebCluSparseClone
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
import os

class ebTestNode(ebTestClucontrol):

    def test_mClusterSparseclone(self):
        print("test started") 
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _clusparse = ebCluSparseClone(_ebox,_options)
        _clusparse.mClusterSparseclone(_options)

    def test_mClusterSparseclone_tm_create(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mkdir -p*", aStdout=None)
                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\"\n}\n"),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None,aPersist=True),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("/usr/bin/chmod 600 oeda/log/exatest/dbaasapi_Testmaster_prepare.out", aStdout=None),
                    exaMockCommand("/usr/bin/chmod 600 oeda/log/exatest/edcsss_Testmaster_prepare.out", aStdout=None),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    #exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                    exaMockCommand("/usr/bin/chmod 600 oeda/log/exatest/dbaasapi_Testmaster_prepare.out", aStdout=None,aPersist=True),
                    exaMockCommand("/usr/bin/chmod 600 oeda/log/exatest/edcsss_Testmaster_prepare.out", aStdout=None,aPersist=True),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                ],
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/rm -f*", aStdout=None),
                    exaMockCommand("/bin/ping -c *", aStdout=None),
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/rm -f /tmp/sparse_input_exatest.json*", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/ping -c 1*", aStdout=None),
                    exaMockCommand("/bin/mkdir -p oeda/log/exatest", aStdout=None, aPersist=True)
                ]
            ],
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.sparseclone = "tm_create"
        _options.jsonconf = {"data":"true"}
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _clusparse = ebCluSparseClone(_ebox,_options)
        _clusparse.mClusterSparseclone(_options)
        _options.jsonconf = {"sourcedb":"true"}
        _clusparse.mClusterSparseclone(_options)
        _options.jsonconf = {"sourcedb":"true","tmdb":"true"}
        _clusparse.mClusterSparseclone(_options)
        _options.jsonconf = {"sourcedb":"true","tmdb":"true","passwd":"true"}
        os.makedirs("/tmp/true",exist_ok=True)
        f = open("/tmp/true/dbaas_input_exatest.json","w+")
        f.close()
        _clusparse.mClusterSparseclone(_options)
        _options.jsonconf = {"sourcedb":"true","tmdb":"true","passwd":"true","clonedb":"true"}
        _clusparse.mClusterSparseclone(_options)

    def test_mClusterSparseclone_tm_create_async(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mkdir -p*", aStdout=None)
                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\"\n}\n"),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None,aPersist=True),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    #exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout="{\n\"id\":\"123\"\n}",aPersist=True),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout="{\n\"id\":\"123\"\n}",aPersist=True),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout="{\n\"id\":\"123\"\n}",aPersist=True),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                ],
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/rm -f*", aStdout=None),
                    exaMockCommand("/bin/ping -c *", aStdout=None),
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/rm -f /tmp/sparse_input_exatest.json*", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/ping -c 1*", aStdout=None)
                ]
            ],
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.sparseclone = "tm_create"
        _options.jsonconf = {"data":"true"}
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        os.makedirs("/tmp/true",exist_ok=True)
        f = open("/tmp/true/dbaas_input_exatest.json","w+")
        f.close()
        _clusparse = ebCluSparseClone(_ebox,_options)
        _options.jsonconf = {"sourcedb":"true","tmdb":"true","passwd":"true","async":"true",}
        _clusparse.mClusterSparseclone(_options)



    def test_mClusterSparseclone_snap_create(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.sparseclone = "snap_create"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _clusparse = ebCluSparseClone(_ebox,_options)
        _clusparse.mClusterSparseclone(_options)

    def test_mClusterSparseclone_status(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.sparseclone = "status"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _clusparse = ebCluSparseClone(_ebox,_options)
        _clusparse.mClusterSparseclone(_options)

    def test_mClusterSparseclone_tm_delete(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/db1/sparse_delete.out*", aStdout="{\n\"Dummy\":\"OUT\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"Dummy\":\"OUT\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("/bin/rm -f*", aStdout=None),
                    exaMockCommand("/bin/ping -c *", aStdout=None),
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/rm -f /tmp/sparse_input_exatest.json*", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/ping -c 1*", aStdout=None)
                ]
            ],
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.sparseclone = "tm_delete"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _clusparse = ebCluSparseClone(_ebox,_options)
        _clusparse.mClusterSparseclone(_options)
        _options.jsonconf = {"dbParams":{"notdbname":"db1"}}
        _clusparse.mClusterSparseclone(_options)
        _options.jsonconf = {"dbParams":{"dbname":"db1"}}
        _clusparse.mClusterSparseclone(_options)

    def test_mClusterSparseclone_snap_delete(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.sparseclone = "snap_delete"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _clusparse = ebCluSparseClone(_ebox,_options)
        _clusparse.mClusterSparseclone(_options)

    def test_mClusterSparseclone_unsupported(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.sparseclone = "unsupported"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _clusparse = ebCluSparseClone(_ebox,_options)
        _clusparse.mClusterSparseclone(_options)

    def test_mClusterSparseStatus(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None,aPersist=True),
                    exaMockCommand("at /var/opt/oracle/log/dbsid/dbaas_status.out", aStdout=None,aPersist=True),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("/bin/rm -f*", aStdout=None),
                    exaMockCommand("/bin/ping -c *", aStdout=None),
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/rm -f /tmp/sparse_input_exatest.json*", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/ping -c 1*", aStdout=None)
                ]
            ],
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.sparseclone = "unsupported"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _clusparse = ebCluSparseClone(_ebox,_options)
        aSparseData = {}
        _options.jsonconf = {"operation":"sparse"}
        _clusparse.mClusterSparseStatus(_options,aSparseData)
        _options.id = "123"
        _clusparse.mClusterSparseStatus(_options,aSparseData)
        _options.dbsid = "dbsid"
        _clusparse.mClusterSparseStatus(_options,aSparseData)


    def test_mClusterSparseclone_tm_create_success(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mkdir -p*", aStdout=None)
                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                    exaMockCommand("/usr/bin/chmod 600 oeda/log/exatest/dbaasapi_Testmaster_prepare.out", aStdout=None, aPersist=True),
                    exaMockCommand("/usr/bin/chmod 600 oeda/log/exatest/edcsss_Testmaster_prepare.out", aStdout=None, aPersist=True),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout=None),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                ],
                [
                    exaMockCommand("mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/true/sparse_create.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i*", aStdout=None,aPersist=True),
                    exaMockCommand("cat /var/opt/oracle/log/true/dbaas_status.out", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n"),
                ],
                [
                    exaMockCommand("/usr/bin/chmod 600 oeda/log/exatest/dbaasapi_Testmaster_prepare-undo.out", aStdout=None,aPersist=True),
                    exaMockCommand("/usr/bin/chmod 600 oeda/log/exatest/edcsss_Testmaster_prepare-undo.out", aStdout=None,aPersist=True)
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/rm -f*", aStdout=None),
                    exaMockCommand("/bin/ping -c *", aStdout=None),
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/rm -f /tmp/sparse_input_exatest.json*", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/ping -c 1*", aStdout=None),
                    exaMockCommand("/bin/mkdir -p oeda/log/exatest", aStdout=None, aPersist=True),
                ]
            ],
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.sparseclone = "tm_create"
        _options.jsonconf = {"data":"true"}
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        os.makedirs("/tmp/true",exist_ok=True)
        f = open("/tmp/true/dbaas_input_exatest.json","w+")
        f.close()
        _clusparse = ebCluSparseClone(_ebox,_options)
        _options.jsonconf = {"sourcedb":"true","tmdb":"true","passwd":"true","clonedb":"true"}
        _clusparse.mClusterSparseclone(_options)




def suite():
    """
    This method ensures the execution in the intended order of the tests.
    """
    suite = unittest.TestSuite()
    suite.addTest(ebTestNode('test_mClusterSparseclone'))
    suite.addTest(ebTestNode('test_mClusterSparseclone_tm_create'))
    suite.addTest(ebTestNode('test_mClusterSparseclone_tm_create_success'))
    suite.addTest(ebTestNode('test_mClusterSparseclone_tm_create_async'))
    suite.addTest(ebTestNode('test_mClusterSparseclone_snap_create'))
    suite.addTest(ebTestNode('test_mClusterSparseclone_status'))
    suite.addTest(ebTestNode('test_mClusterSparseclone_tm_delete'))
    suite.addTest(ebTestNode('test_mClusterSparseclone_snap_delete'))
    suite.addTest(ebTestNode('test_mClusterSparseclone_unsupported'))
    suite.addTest(ebTestNode('test_mClusterSparseStatus'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suite())


