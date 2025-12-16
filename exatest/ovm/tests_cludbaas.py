""", ebLogTrace

 $Header: 

 Copyright (c) 2020, 2025, Oracle and/or its affiliates.

 NAME:
      tests_cludbaas.py - Unitest for vmbackup.py module

 DESCRIPTION:
      Run tests for the methods of cludbaas.py

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       remamid  10/07/25 - Unittest for bug 38468451
       aararora 09/09/25 - 38391988: Disable tcps for atp
       aararora 08/07/25 - ER 37858683: Add tcps config if present in the payload
       abflores 06/18/25 - Bug 37508725 - IMPROVE PORT SCAN
       jfsaldan 01/29/25 - Bug 37459561 - REVIEW ECRA STEP OCDE NID
                           CONFIGURATION SCRIPT FOR PARALLEL PROCESSING
       akkar    07/24/24 - Bug 36875774: Add unit test for dbascli
       ajayasin 04/17/22 - cludbaas.py ut added
       ajayasin 03/06/22 - new ut file for cludbaas.py
       ajayasin 04/03/22 - new ut file for cludbaas.py
"""

import unittest
from unittest import mock

from random import shuffle

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.ovm.cludbaas import (ebCluDbaas, getDatabaseHomes, getDatabases,
    getDatabaseDetails, executeOCDEInitOnDomUs, cloneDbHome, updateGridINI, addInstance, deleteInstance, mUpdateListenerPort)
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
import os

class ebTestNode(ebTestClucontrol):

    def test_mCluDbaas_mClusterDbaas_t1(self):
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
        _cludbaas = ebCluDbaas(_ebox,_options)
        _cludbaas.mClusterDbaas(_options,"db_info")


    def test_mCluDbaas_mClusterDbaas_t2(self):
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
        _cludbaas = ebCluDbaas(_ebox,_options)
        Data = {}
        _cludbaas.mClusterDbaas(_options,"db_info",Data)

    def test_mCluDbaas_mClusterDbaas_t3(self):
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
        _options.dbaas = None
        _cludbaas = ebCluDbaas(_ebox,_options)
        Data = {}
        _cludbaas.mClusterDbaas(_options,"dbinfo",Data)

    def test_mCluDbaas_mClusterDbaas_t4(self):
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
        _cludbaas = ebCluDbaas(_ebox,_options)
        Data = {}
        _cludbaas.mClusterDbaas(_options,"cprops_update")

    def test_mCluDbaas_mClusterDbaas_t5(self):
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
        _cludbaas = ebCluDbaas(_ebox,_options)
        Data = {}
        _cludbaas.mClusterDbaas(_options,"dummy_update")

    def test_mCluDbaas_mClusterDbInfo_t1(self):
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
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/db_infofetch_input_exatest.json*", aRc=0),
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/db_infofetch_input_exatest.json*", aRc=0),
                    exaMockCommand("cat /var/opt/oracle/log/dbinfoexatest_outfile.out",aRc=0)
                ]

           ],
           self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/rm -f*", aStdout=None),
                    exaMockCommand("/bin/ping -c *", aStdout=None),
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/rm -f /tmp/sparse_input_exatest.json*", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/ping -c 1*", aStdout=None)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _options.jsonconf  = {}
        _options.jsonconf["mode"] ="all"         
        _cludbaas = ebCluDbaas(_ebox,_options)
        Data = {}
        _cludbaas.mClusterDbInfo(_options)

    def test_mCluDbaas_mClusterDbInfo_t2(self):
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
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/db_infofetch_input_exatest.json*", aRc=0),
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/db_infofetch_input_exatest.json*", aRc=0),
                    exaMockCommand("cat /var/opt/oracle/log/dbinfoexatest_outfile.out",aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n", aRc=0)
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/db_infofetch_input_exatest.json*", aRc=0),
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/dbinfoexatest_outfile.out",aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n", aRc=0)
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/db_infofetch_input_exatest.json*", aRc=0),
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/dbinfoexatest_outfile.out",aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n", aRc=0)
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/db_infofetch_input_exatest.json*", aRc=0),
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/dbinfoexatest_outfile.out",aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n", aRc=0)
                ],
                [
                    exaMockCommand("/usr/bin/cat file.log",aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n", aRc=0)
                ],
                [
                    exaMockCommand("/usr/bin/cat /var/opt/oracle/log/dbinfoexatest_infofile.out",aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n", aRc=0)
                ]

           ],
           self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/rm -f*", aStdout=None),
                    exaMockCommand("/bin/mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/ping -c *", aStdout=None),
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/rm -f /tmp/sparse_input_exatest.json*", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/ping -c 1*", aStdout=None)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _options.jsonconf  = {}
        _options.jsonconf["mode"] ="all"         
        _cludbaas = ebCluDbaas(_ebox,_options)
        Data = {}
        _cludbaas.mClusterDbInfo(_options)

    def test_mCluDbaas_mClusterDbInfo_t3(self):
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
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/db_infofetch_input_exatest.json*", aRc=0),
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/db_infofetch_input_exatest.json*", aRc=0),
                    exaMockCommand("cat /var/opt/oracle/log/dbinfoexatest_outfile.out",aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n", aRc=0)
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/db_infofetch_input_exatest.json*", aRc=0),
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/dbinfoexatest_outfile.out",aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n", aRc=0)
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/db_infofetch_input_exatest.json*", aRc=0),
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/dbinfoexatest_outfile.out",aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n", aRc=0)
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/db_infofetch_input_exatest.json*", aRc=0),
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/dbinfoexatest_outfile.out",aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n", aRc=0)
                ],

           ],
           self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/rm -f*", aStdout=None),
                    exaMockCommand("/bin/mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/ping -c *", aStdout=None),
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/rm -f /tmp/sparse_input_exatest.json*", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/ping -c 1*", aStdout=None)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _options.jsonconf  = {}
        _options.jsonconf["mode"] ="one"         
        _options.jsonconf["dbname"] ="db"         
        _cludbaas = ebCluDbaas(_ebox,_options)
        Data = {}
        _cludbaas.mClusterDbInfo(_options)

    def test_mCluDbaas_mExecuteUpdateCprops_t1(self):
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
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aRc=0),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/db_infofetch_input_exatest.json*", aRc=0),
                    exaMockCommand("cat /var/opt/oracle/log/update_exatest_outfile.out*", aRc=0),
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/db_infofetch_input_exatest.json*", aRc=0),
                    exaMockCommand("cat /var/opt/oracle/log/dbinfoexatest_outfile.out",aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n", aRc=0)
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/db_infofetch_input_exatest.json*", aRc=0),
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/dbinfoexatest_outfile.out",aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n", aRc=0)
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/db_infofetch_input_exatest.json*", aRc=0),
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/dbinfoexatest_outfile.out",aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n", aRc=0)
                ],
                [
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi -i /var/opt/oracle/log/db_infofetch_input_exatest.json*", aRc=0),
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("chown -R*", aStdout=None),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi*", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/dbinfoexatest_outfile.out",aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n", aRc=0)
                ],

           ],
           self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/rm -f*", aStdout=None),
                    exaMockCommand("/bin/mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/ping -c *", aStdout=None),
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/rm -f /tmp/sparse_input_exatest.json*", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/ping -c 1*", aStdout=None)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _options.jsonconf  = {}
        _options.jsonconf["mode"] ="one"         
        _options.jsonconf["dbname"] ="db"         
        _cludbaas = ebCluDbaas(_ebox,_options)
        Data = {}
        Data["Command"] = "update"
        _cludbaas.mExecuteUpdateCprops(_options,Data,_options.jsonconf,"update_tfactl")

    def test_mCluDbaas_mParseTfaInput_t1(self):
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
        _cludbaas = ebCluDbaas(_ebox,_options)
        aParams = {}
        aParams["diag"] = None
        _cludbaas.mParseTfaInput(aParams)

    def test_mCluDbaas_mParseTfaInput_t2(self):
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
        _cludbaas = ebCluDbaas(_ebox,_options)
        aParams = {}
        Data = {}
        Data2 = {}
        Data["passwd_data"] = Data2
        aParams["diag"] = Data
        _cludbaas.mParseTfaInput(aParams)

    def test_mCluDbaas_mExecuteDBaaSAPIAction_t1(self):
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
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aRc=0),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aRc=0),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n",aRc=0),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aRc=0),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n",aRc=0),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aRc=0),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n",aRc=0),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aRc=0),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/log/Update_exatest_outfile.out*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n",aRc=0),
                    exaMockCommand("cat /var/opt/*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n",aRc=0),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aRc=0),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mkdir -p *", aStdout=None, aRc=0),
                    exaMockCommand("/var/opt/oracle/dbaasapi/dbaasapi -i *", aStdout=None, aRc=0),
                    exaMockCommand("/bin/scp *", aStdout=None),
                    exaMockCommand("cat /var/opt/oracle/*", aStdout="{\n\"id\":\"123\",\n\"logfile\":\"file.log\"\n}\n",aRc=0),
                    exaMockCommand("nohup /var/opt/oracle/dbaasapi/dbaasapi*", aRc=0),
                    exaMockCommand("chown -R*", aStdout=None)
                ],
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/rm -f*", aStdout=None),
                    exaMockCommand("/bin/mkdir -p*", aStdout=None),
                    exaMockCommand("/bin/ping -c *", aStdout=None),
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/rm -f /tmp/sparse_input_exatest.json*", aStdout=None,aPersist=True),
                    exaMockCommand("/bin/ping -c 1*", aStdout=None)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _cludbaas = ebCluDbaas(_ebox,_options)
        aParams = {}
        Data = {}
        Data2 = {}
        Data["passwd_data"] = Data2
        aParams["dbname"] = "db"
        aAction = "validate"
        aOperation = "validate"
        aDbaasdata = {}
        for _,aDomU in  _ebox.mReturnDom0DomUPair():
            _cludbaas.mExecuteDBaaSAPIAction(aAction, aOperation, aDbaasdata, aDomU, aParams, _options)
            break

    def test_getDatabaseHomes_withoutdb(self):
        dbhomes_error_msg = """
            DBAAS CLI version 24.2.1.0.0
            Executing command system getDBHomes
            Job id: eb725cc8-3b57-488e-98f4-0bc0bf397a47
            Session log: /var/opt/oracle/log/system/getDBHomes/dbaastools_2024-07-23_06-27-06-PM_205228.log
            [WARNING] [DBAAS-80102] Unable to get list of homes.
            CAUSE: There are no homes registered in the system.

            dbaascli execution completed
        """
        _cmds = {
             self.mGetRegexVm(): [
                [
                    exaMockCommand("dbaascli system getDBHomes", aStdout=dbhomes_error_msg),
                ],
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        for _,aDomU in  _ebox.mReturnDom0DomUPair():
            _output = getDatabaseHomes(aDomU)
            self.assertEqual(_output, {})
            
    def test_getDatabaseHomes_withdb(self):
        dbhomes_success_msg = """
            DBAAS CLI version MAIN
            Executing command system getDBHomes
            Job id: 0b409fb8-371b-404b-a233-09791e880ac6
            Session log: /var/opt/oracle/log/system/getDBHomes/dbaastools_2024-06-02_08-22-02-AM_322346.log
            {
            "OraHome1" : {
                "homePath" : "/u02/app/oracle/product/19.0.0.0/dbhome_2",
                "homeName" : "OraHome1",
                "version" : "19.23.0.0.0",
                "createTime" : 1717316044728,
                "updateTime" : 1717316044728,
                "unifiedAuditEnabled" : false,
                "ohNodeLevelDetails" : {
                "c3716n15c2" : {
                    "nodeName" : "c3716n15c2",
                    "version" : "19.23.0.0.0",
                    "patches" : [ "36459041", "36195566", "36199232", "36260537", "36240578", "36233263" ]
                },
                "c3716n16c2" : {
                    "nodeName" : "c3716n16c2",
                    "version" : "19.23.0.0.0",
                    "patches" : [ "36459041", "36195566", "36199232", "36260537", "36240578", "36233263" ]
                }
                },
                "messages" : [ ]
            },
            "ETFDB64" : {
                "homePath" : "/u02/app/oracle/product/19.0.0.0/dbhome_1",
                "homeName" : "ETFDB64",
                "version" : "19.23.0.0.0",
                "createTime" : 1717314884502,
                "updateTime" : 1717314884502,
                "unifiedAuditEnabled" : false,
                "ohNodeLevelDetails" : {
                "c3716n15c2" : {
                    "nodeName" : "c3716n15c2",
                    "version" : "19.23.0.0.0",
                    "patches" : [ "36459041", "36195566", "36199232", "36260537", "36240578", "36233263" ]
                },
                "c3716n16c2" : {
                    "nodeName" : "c3716n16c2",
                    "version" : "19.23.0.0.0",
                    "patches" : [ "36459041", "36195566", "36199232", "36260537", "36240578", "36233263" ]
                }
                },
                "messages" : [ ]
            }
            }

            dbaascli execution completed
        """
        _cmds = {
             self.mGetRegexVm(): [
                [
                    exaMockCommand("dbaascli system getDBHomes", aStdout=dbhomes_success_msg),
                ],
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        for _,aDomU in  _ebox.mReturnDom0DomUPair():
            getDatabaseHomes(aDomU)
            
    def test_getDatabases_withoutdb(self):
        dbhomes_error_msg = """
            DBAAS CLI version 24.2.1.0.0
            Executing command system getDatabases --reload
            Job id: 012c2851-b54a-42bb-8dc4-516f5afc58e4
            Session log: /var/opt/oracle/log/system/getDatabases/dbaastools_2024-07-23_06-53-40-PM_314883.log
            [WARNING] [DBAAS-80101] Unable to get list of databases.
            CAUSE: There are no databases registered in the system.

            dbaascli execution completed
        """
        _cmds = {
             self.mGetRegexVm(): [
                [
                    exaMockCommand("dbaascli system getDBHomes", aStdout=dbhomes_error_msg),
                ],
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        for _,aDomU in  _ebox.mReturnDom0DomUPair():
            _output = getDatabases(aDomU)
            self.assertEqual(_output, {})
            
    def test_getDatabaseDetails_withoutdb(self):
        dbdetail_error_msg = """
            DBAAS CLI version 24.2.1.0.0
            Executing command database getDetails --dbname db1 --reload
            Job id: c1678a26-acf6-4088-90b7-52eefbe26a82
            Session log: /var/opt/oracle/log/db1/database/getDetails/dbaastools_2024-07-23_06-53-30-PM_314073.log
            [FATAL] [DBAAS-80034] The following database was not found in the environment: db1.
            ACTION: Verify the requested database and try again.
        """
        _cmds = {
             self.mGetRegexVm(): [
                [
                    exaMockCommand("dbaascli system getDBHomes", aStdout=dbdetail_error_msg),
                ],
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        for _,aDomU in  _ebox.mReturnDom0DomUPair():
            _output = getDatabaseDetails(aDomU, 'db1')
            self.assertEqual(_output, {})

    def test_executeOCDEInitOnDomU_success_sequential(self):
        """
        Test of executeOCDEInitOnDomUs
        """

        _cmds = {
             self.mGetRegexVm(): [
                [
                    exaMockCommand("/usr/bin/dbaascli admin initializeCluster",
                        aStdout=""),
                    exaMockCommand("chmod",
                        aStdout=""),
                    exaMockCommand("echo.*",
                        aStdout=""),
                ],
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        for _, _domU in  _ebox.mReturnDom0DomUPair():
            self.assertEqual(0, executeOCDEInitOnDomUs([_domU], aParallel=False, aTcpSslPort='1560'))

        _cmds = {
             self.mGetRegexVm(): [
                [
                    exaMockCommand("/var/opt/oracle/ocde/ocde -exa -init;",
                        aStdout=""),
                    exaMockCommand("chmod",
                        aStdout=""),
                    exaMockCommand("echo.*",
                        aStdout=""),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)
        for _, _domU in  _ebox.mReturnDom0DomUPair():
            self.assertEqual(0, executeOCDEInitOnDomUs([_domU], aParallel=False, aTcpSslPort='1560', aIsAtp=True))

    def test_executeOCDEInitOnDomU_success_parallel(self):
        """
        Test of executeOCDEInitOnDomUs
        """

        _cmds = {
             self.mGetRegexVm(): [
                [
                    exaMockCommand("/usr/bin/dbaascli admin initializeCluster",
                        aStdout=""),
                    exaMockCommand("chmod",
                        aStdout=""),
                    exaMockCommand("echo.*",
                        aStdout=""),
                ],
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()

        _domUs = [ _domU for _, _domU in _ebox.mReturnDom0DomUPair()]
        self.assertEqual(0, executeOCDEInitOnDomUs(_domUs, aParallel=True))
        # ATP test
        _cmds = {
             self.mGetRegexVm(): [
                [
                    exaMockCommand("/var/opt/oracle/ocde/ocde -exa -init;",
                        aStdout=""),
                    exaMockCommand("chmod",
                        aStdout=""),
                    exaMockCommand("echo.*",
                        aStdout=""),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        self.assertEqual(0, executeOCDEInitOnDomUs(_domUs, aParallel=True, aIsAtp=True))

    def test_executeOCDEInitOnDomU_error_sequential(self):
        """
        Test of executeOCDEInitOnDomUs
        """

        RC_ERROR = 1
        _cmds = {
             self.mGetRegexVm(): [
                [
                    exaMockCommand("/usr/bin/dbaascli admin initializeCluster",
                        aRc=RC_ERROR, aStdout="Error stdout ocde"),
                ],
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()

        for _, _domU in  _ebox.mReturnDom0DomUPair():
            self.assertEqual(RC_ERROR, executeOCDEInitOnDomUs([_domU], aParallel=False))

    def test_executeOCDEInitOnDomU_error_parallel(self):
        """
        Test of executeOCDEInitOnDomUs
        """

        RC_ERROR = 1
        _cmds = {
             self.mGetRegexVm(): [
                [
                    exaMockCommand("/usr/bin/dbaascli admin initializeCluster",
                        aRc = RC_ERROR, aStdout=""),
                    exaMockCommand("chmod.*",
                        aStdout=""),
                    exaMockCommand("echo.*",
                        aStdout=""),
                ],
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()

        _domUs = [ _domU for _, _domU in _ebox.mReturnDom0DomUPair()]
        self.assertEqual(RC_ERROR, executeOCDEInitOnDomUs(_domUs, aParallel=True))

    def test_cloneDbHome(self):
        """
        Test of cloneDbHome
        """
        _srcdomU = "scaqab10client01vm05.us.oracle.com"
        _targetdomU = "scaqab10client01vm06.us.oracle.com"
        _cmds = {
             self.mGetRegexVm(): [
                [
                    exaMockCommand("dbaascli dbhome create --version 19.22.0.0.0 --oraclehome /u02/app/oracle/product/19.0.0.0/dbhome_2 --extendHome --newNodes scaqab10client01vm06", aRc = 0, aStdout=""),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)
        cloneDbHome(_srcdomU, "19.22.0.0.0", "/u02/app/oracle/product/19.0.0.0/dbhome_2", "scaqab10client01vm06")

    def test_addInstance(self):
        """
        Test of addInstance
        """
        RC_ERROR = -1
        _srcdomU = "scaqab10client01vm05.us.oracle.com"
        _targetdomU = "scaqab10client01vm06.us.oracle.com"
        _dbname = "DBclu01"
        _cmds = {
             self.mGetRegexVm(): [
                [
                    exaMockCommand("dbaascli database addInstance --dbname DBclu01 --nodeListForInstanceMgmt scaqab10client01vm06.us.oracle.com", aRc = 0, aStdout=""),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)
        addInstance(_srcdomU, _dbname, _targetdomU)

    def test_updateGridINI(self):
        """
        Test of updateGridINI
        """
        _targetdomU = "scaqab10client01vm06.us.oracle.com"
        _cmds = {
             self.mGetRegexVm(): [
                [
                    exaMockCommand("/usr/bin/dbaascli admin initializeCluster", aRc = 0, aStdout=""),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _rc = updateGridINI(_targetdomU)
        self.assertEqual(_rc, 0)

    def test_deleteInstance(self):
        """
        Test of deleteInstance
        """
        RC_ERROR = -1
        _srcdomU = "scaqab10client01vm05.us.oracle.com"
        _targetdomU = "scaqab10client01vm06.us.oracle.com"
        _dbname = "DBclu01"
        _cmds = {
             self.mGetRegexVm(): [
                [
                    exaMockCommand("dbaascli database deleteInstance --dbname DBclu01 --nodeListForInstanceMgmt scaqab10client01vm06.us.oracle.com ", aRc = 0, aStdout=""),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.assertEqual(0, deleteInstance(_srcdomU, _dbname, _targetdomU))

        _cmds = {
             self.mGetRegexVm(): [
                [
                    exaMockCommand("dbaascli database deleteInstance --dbname DBclu01 --nodeListForInstanceMgmt scaqab10client01vm06.us.oracle.com ", aRc = RC_ERROR, aStdout=""),
                    exaMockCommand("dbaascli database deleteInstance --dbname DBclu01 --nodeListForInstanceMgmt scaqab10client01vm06.us.oracle.com --force", aRc = 0, aStdout=""),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.assertEqual(0, deleteInstance(_srcdomU, _dbname, _targetdomU))

        _cmds = {
             self.mGetRegexVm(): [
                [
                    exaMockCommand("dbaascli database deleteInstance --dbname DBclu01 --nodeListForInstanceMgmt scaqab10client01vm06.us.oracle.com ", aRc = RC_ERROR, aStdout=""),
                    exaMockCommand("dbaascli database deleteInstance --dbname DBclu01 --nodeListForInstanceMgmt scaqab10client01vm06.us.oracle.com --force", aRc = RC_ERROR, aStdout=""),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.assertEqual(RC_ERROR, deleteInstance(_srcdomU, _dbname, _targetdomU))

    def test_mUpdateListenerPort(self):
        """
        Test that mUpdateListenerPort correctly updates the listener port for the given domU list.
        """
        pairs = self.mGetClubox().mReturnDom0DomUPair()
        scan_port = "1521"

        commands = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand(f"/var/opt/oracle/ocde/rops set_creg_key grid lsnr_port {scan_port}", aStdout=None, aStderr=None, aRc=0,  aPersist=True),
                    exaMockCommand(f"/var/opt/oracle/ocde/rops get_creg_key grid lsnr_port", aStdout=scan_port, aStderr=None, aRc=0,  aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(commands)
        
        domUList = [_domU for _dom0, _domU in pairs]
        _ebox = self.mGetClubox()

        with mock.patch('exabox.ovm.cluconfig.ebCluDRScanConfig.mGetScanPort', return_value=scan_port):
            update_result = mUpdateListenerPort(_ebox, domUList)
        self.assertEqual(None, update_result)

    #@patch('exabox.ovm.cludbaas.mExecCommandOnDomU', return_value=None)     
    def test_mCopyDomuInfoLogs(self):
        _cmds = {
             self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/mkdir*", aStdout=""),
                    exaMockCommand("/usr/bin/cat*", aStdout=""),
                    exaMockCommand("/bin/mkdir*", aStdout=""),
                    exaMockCommand("/usr/bin/cat*", aStdout="")
                ],
            ]
        }
        #Init new Args
        _ebox = self.mGetClubox()
        _ebox.mSetOedaPath("/opt/oci/exacc/exacloud/oeda/requests/exaunit_00016104048_dd2653e6-dec9-4cbb-839b-45f34eddf445")
        _logfile = "/var/opt/oracle/log/grid/dbaasapi/db/diskgroup/7af8f379-b528-41cb-baa2-fc9569d41b1f.log"
        _infofile = "/var/opt/oracle/log/grid/diskgroupOp-dd2653e6-dec9-4cbb-839b-45f34eddf445-0.341926.status.out"
        _domU = _ebox.mReturnDom0DomUPair()[0][1]
        _options = self.mGetPayload()
        self.mPrepareMockCommands(_cmds)
        _cludbaas = ebCluDbaas(_ebox,_options)
        with mock.patch("exabox.ovm.cludbaas.ebCluDbaas.mExecCommandOnDomU", return_value=None):
            _cludbaas.mCopyDomuInfoLog(_options, _domU, _logfile, _infofile)
        #self.assertEqual(_output, {})

def suite():
    """
    This method ensures the execution in the intended order of the tests.
    """
    suite = unittest.TestSuite()
    suite.addTest(ebTestNode('test_mCluDbaas_mClusterDbaas_t1'))
    suite.addTest(ebTestNode('test_mCluDbaas_mClusterDbaas_t2'))
    suite.addTest(ebTestNode('test_mCluDbaas_mClusterDbaas_t3'))
    suite.addTest(ebTestNode('test_mCluDbaas_mClusterDbaas_t4'))
    suite.addTest(ebTestNode('test_mCluDbaas_mClusterDbaas_t5'))
    suite.addTest(ebTestNode('test_mCluDbaas_mClusterDbInfo_t1'))
    suite.addTest(ebTestNode('test_mCluDbaas_mClusterDbInfo_t2'))
    suite.addTest(ebTestNode('test_mCluDbaas_mClusterDbInfo_t3'))
    suite.addTest(ebTestNode('test_mCluDbaas_mExecuteUpdateCprops_t1'))
    suite.addTest(ebTestNode('test_mCluDbaas_mParseTfaInput_t1'))
    suite.addTest(ebTestNode('test_mCluDbaas_mParseTfaInput_t2'))
    suite.addTest(ebTestNode('test_mCluDbaas_mExecuteDBaaSAPIAction_t1'))
    suite.addTest(ebTestNode('test_getDatabaseHomes_withoutdb'))
    suite.addTest(ebTestNode('test_getDatabaseHomes_withdb'))
    suite.addTest(ebTestNode('test_getDatabases_withoutdb'))
    suite.addTest(ebTestNode('test_getDatabaseDetails_withoutdb'))
    suite.addTest(ebTestNode('test_executeOCDEInitOnDomU_success_sequential'))
    suite.addTest(ebTestNode('test_executeOCDEInitOnDomU_success_parallel'))
    suite.addTest(ebTestNode('test_executeOCDEInitOnDomU_error_sequential'))
    suite.addTest(ebTestNode('test_cloneDbHome'))
    suite.addTest(ebTestNode('test_addInstance'))
    suite.addTest(ebTestNode('test_updateGridINI'))
    suite.addTest(ebTestNode('test_deleteInstance'))
    suite.addTest(ebTestNode('test_mUpdateListenerPort'))
    suite.addTest(ebTestNode('test_mCopyDomuInfoLogs'))

    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suite())


