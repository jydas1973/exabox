#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/clumisc/tests_clumisc.py /main/25 2025/11/07 20:59:33 jfsaldan Exp $
#
# tests_clumisc.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_clumisc.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    remamid     10/14/25 - Add unittest for libvirtd enable bug 38481712
#    remamid     05/08/25 - Add unittest for mRunComputePhysicalDiskTest
#    ririgoye    11/05/24 - Bug 36994764 - EXACS-PREPROD: VM CLUSTER PROVISION
#                           FAIL AT PREVMCHECKS - FLASHCACHE STATUS ON CELL IS
#                           ABNORMAL
#    ririgoye    11/04/24 - Bug 37137239 - Modifying precheck tests to stop
#                           using queue and event
#    naps        08/14/24 - Bug 36949876 - X11 ipconf path changes.
#    aararora    03/07/24 - Bug 36367482: Unit test fix
#    joysjose    10/23/23 - 35920613 Cancel exception raising and return 
#                           error message when keys are not found during fetchkeys.
#    gparada     07/10/23 - 35529689 Removed cluctl.mGetMinSystemImageVersion 
#                           and moved to clumisc mGetDom0sImagesListSorted 
#    gparada     06/13/23 - 35495548 Fix version used to compare in validation
#    gparada     05/26/23 - 34556452 Test mValidateVersionForMVV
#    alsepulv    06/15/22 - Bug 34236957: Add hostnames' length precheck test
#    araghave    04/28/22 - Bug 34094559 - REVERTING THE CHANGES FOR ENH
#                           33729129
#    araghave    01/06/22 - Enh 33729129 - Provide both .zip and .bz2 file
#                           extension support on System image files.
#    jesandov    09/07/20 - Creation
#

import unittest
from unittest.mock import patch, MagicMock, call, mock_open
import warnings
 
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.core.Error import ExacloudRuntimeError
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.clumisc import ebCluPreChecks
from exabox.ovm.clumisc import ebCluDom0SanityTests, ebCluCellSanityTests, ebCluIbSwitchSanityTests, ebCluCellValidate
from exabox.ovm.clumisc import  ebCluScheduleManager, ebCluFetchSshKeys, OracleVersion
from multiprocessing import Process, Manager, Queue, Event
from exabox.core.DBStore import ebGetDefaultDB
from exabox.exakms.ExaKmsFileSystem import ExaKmsFileSystem
from exabox.log.LogMgr import ebLogInfo, ebLogWarn
from exabox.ovm.kvmvmmgr import ebKvmVmMgr
import os, re
import json
import copy

ELASTIC_SHAPES_PAYLOAD = {
   "ostype" : "ib",
   "operationtype" : "CEI_RESERVE",
   "quarter-rack-servers":[
      {
         "domainname":"us.oracle.com",
         "hostname":"scaqab10adm01",
         "hw_type":"COMPUTE",
         "preprov":True
      },
      {
         "domainname":"us.oracle.com",
         "hostname":"scaqab10celadm01",
         "hw_type":"CELL",
         "preprov":True
      }
   ],
   "elastic-servers":[
      {
         "domainname":"us.oracle.com",
         "hostname":"scaqab10celadm02",
         "hw_type":"COMPUTE",
         "preprov":False
      },
      {
         "domainname":"us.oracle.com",
         "hostname":"scas22celadm06",
         "hw_type":"CELL",
         "preprov":False
      }
   ]
}

ELASTIC_SHAPES_RESULT = {
    "scaqab10celadm01.us.oracle.com":{
        "Details":{
        },
        "ping_test":"normal",
        "ssh_test":"normal",
        "fan":"normal",
        "power":"normal",
        "temperature":"normal",
        "cellsrvStatus":"running",
        "msStatus":"running",
        "rsStatus":"running",
        "lun":"normal",
        "physicaldisk":"normal",
        "griddisk":"normal",
        "celldisk":"normal",
        "flashcache":"normal",
        "root_storage_test":"normal",
        "node_info":[
           {
               "domainname":"us.oracle.com",
               "hostname":"scaqab10celadm01",
               "hw_type":"CELL",
               "preprov":False,
               "error_list":[
               ],
               "node_type":"elastic-servers"
            }
        ]
   },
   "scaqab10adm01.us.oracle.com":{
      "ping_test":"normal",
      "ssh_test":"normal",
      "fan":"normal",
      "power":"normal",
      "temperature":"normal",
      "hypervisor":"running",
      "root_storage_test":"normal",
      "ilom_admin_consistency":"normal",
      "image_info_check":"normal",
      "bridge_check":"abnormal",
      "stale_domu_check":"abnormal",
      "image_info_check":"normal",
      "node_info":[
         {
            "domainname":"us.oracle.com",
            "hostname":"scaqab10adm01",
            "hw_type":"COMPUTE",
            "preprov":True,
            "error_list":[
               {
                  "error-type":"bridge_check",
                  "error-message":"bridge_check test failed on dom0:scaqab10adm01.us.oracle.com"
               },
               {
                  "error-type":"stale_domu_check",
                  "error-message":"stale_domu_check test failed on dom0:scaqab10adm01.us.oracle.com"
               }
            ],
            "node_type":"quarter-rack-servers" 
         }
      ]
   },
}

ELASTIC_SHAPES_RESULT_FLUSH = {
    "scaqab10celadm01.us.oracle.com":{
        "Details":{
        },
        "ping_test":"normal",
        "ssh_test":"normal",
        "fan":"normal",
        "power":"normal",
        "temperature":"normal",
        "cellsrvStatus":"running",
        "msStatus":"running",
        "rsStatus":"running",
        "lun":"normal",
        "physicaldisk":"normal",
        "griddisk":"normal",
        "celldisk":"normal",
        "flashcache":"normal - flushed",
        "root_storage_test":"normal",
        "node_info":[
           {
               "domainname":"us.oracle.com",
               "hostname":"scaqab10celadm01",
               "hw_type":"CELL",
               "preprov":False,
               "error_list":[
               ],
               "node_type":"elastic-servers"
            }
        ]
   },
   "scaqab10adm01.us.oracle.com":{
      "ping_test":"normal",
      "ssh_test":"normal",
      "fan":"normal",
      "power":"normal",
      "temperature":"normal",
      "hypervisor":"running",
      "root_storage_test":"normal",
      "ilom_admin_consistency":"normal",
      "image_info_check":"normal",
      "bridge_check":"abnormal",
      "stale_domu_check":"abnormal",
      "image_info_check":"normal",
      "node_info":[
         {
            "domainname":"us.oracle.com",
            "hostname":"scaqab10adm01",
            "hw_type":"COMPUTE",
            "preprov":True,
            "error_list":[
               {
                  "error-type":"bridge_check",
                  "error-message":"bridge_check test failed on dom0:scaqab10adm01.us.oracle.com"
               },
               {
                  "error-type":"stale_domu_check",
                  "error-message":"stale_domu_check test failed on dom0:scaqab10adm01.us.oracle.com"
               }
            ],
            "node_type":"quarter-rack-servers" 
         }
      ]
   },
}

class ebTestClumisc(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        #super().setUpClass()
        super(ebTestClumisc, self).setUpClass(aGenerateDatabase=True,aUseOeda=True)
        warnings.filterwarnings("ignore")
 
    def test_ebCluPreChecks_001_preservate_matching(self):

        _imgList = """/EXAVMIMAGES/System.first.boot.20.1.1.0.0.200808.img
/EXAVMIMAGES/System.first.boot.20.1.1.0.0.200808.imgBACK
/EXAVMIMAGES/System.first.boot.20.1.1.0.0.200722"""

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/local/bin/imageinfo -version", aStdout="20.1.1.0.0.200808"),
                    exaMockCommand("ls /EXAVMIMAGES/System.first.boot.*"),
                    exaMockCommand("test.*find"),
                    exaMockCommand('/sbin/find /EXAVMIMAGES/ -maxdepth 1 -iname "System.first.boot.*.img" -mtime \+7')
                ],
                [
                    exaMockCommand("ls /EXAVMIMAGES/System.first.boot.*", aStdout=_imgList),
                    exaMockCommand("rm -rf /EXAVMIMAGES/System.first.boot.20.1.1.0.0.200722.*img"),
                    exaMockCommand("rm -rf /EXAVMIMAGES/System.first.boot.20.1.1.0.0.200722.*bz2")
                ]
            ]
        }
 
        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _imgrev = self.mGetClubox().mGetImageVersion(_dom0)

            _pchecks = ebCluPreChecks(self.mGetClubox())
            _pchecks.cleanup_old_system_boot_files(_dom0, {_imgrev}) 


    def test_ebCluPreChecks_002_remove_no_matching(self):
 
        _imgList = """/EXAVMIMAGES/System.first.boot.20.1.1.0.0.200808.img
/EXAVMIMAGES/System.first.boot.20.1.1.0.0.200808.imgBACK
/EXAVMIMAGES/System.first.boot.20.1.1.0.0.200722"""

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/local/bin/imageinfo -version", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand("ls /EXAVMIMAGES/System.first.boot.*"),
                    exaMockCommand("test.*find"),
                    exaMockCommand('/sbin/find /EXAVMIMAGES/ -maxdepth 1 -iname "System.first.boot.*.img" -mtime \+7')
                ],
                [
                    exaMockCommand("ls /EXAVMIMAGES/System.first.boot.*", aStdout=_imgList),
                    exaMockCommand("rm -rf /EXAVMIMAGES/System.first.boot.20.1.1.0.0.200808.*img"),
                    exaMockCommand("rm -rf /EXAVMIMAGES/System.first.boot.20.1.1.0.0.200808.*bz2"),
                    exaMockCommand("rm -rf /EXAVMIMAGES/System.first.boot.20.1.1.0.0.200722.*img"),
                    exaMockCommand("rm -rf /EXAVMIMAGES/System.first.boot.20.1.1.0.0.200722.*bz2")
                ]
            ]
        }
 
        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _imgrev = self.mGetClubox().mGetImageVersion(_dom0)

            _pchecks = ebCluPreChecks(self.mGetClubox())
            _pchecks.cleanup_old_system_boot_files(_dom0, {_imgrev})

 
    def test_ebCluPreChecks_003_old_new_latest(self):
 
        _imgList = """/EXAVMIMAGES/System.first.boot.20.1.1.0.0.200808.img
/EXAVMIMAGES/System.first.boot.20.1.1.0.0.200808.imgBACK
/EXAVMIMAGES/System.first.boot.20.1.1.0.0.200808.img
/EXAVMIMAGES/System.first.boot.20.1.1.0.0.200808.bz2
/EXAVMIMAGES/System.first.boot.20.1.1.0.0.200803
/EXAVMIMAGES/System.first.boot.20.1.1.0.0.200803.imgBACK
/EXAVMIMAGES/System.first.boot.20.1.1.0.0.200803.img
/EXAVMIMAGES/System.first.boot.20.1.1.0.0.200803.bz2
/EXAVMIMAGES/System.first.boot.20.1.1.0.0.200722"""

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/local/bin/imageinfo -version", aStdout="20.1.1.0.0.200803"),
                    exaMockCommand("ls /EXAVMIMAGES/System.first.boot.*"),
                    exaMockCommand("test.*find"),
                    exaMockCommand('/sbin/find /EXAVMIMAGES/ -maxdepth 1 -iname "System.first.boot.*.img" -mtime \+7')
                ],
                [
                    exaMockCommand("ls /EXAVMIMAGES/System.first.boot.*", aStdout=_imgList),
                    exaMockCommand("rm -rf /EXAVMIMAGES/System.first.boot.20.1.1.0.0.200808.*img"),
                    exaMockCommand("rm -rf /EXAVMIMAGES/System.first.boot.20.1.1.0.0.200808.*bz2"),
                    exaMockCommand("rm -rf /EXAVMIMAGES/System.first.boot.20.1.1.0.0.200722.*img"),
                    exaMockCommand("rm -rf /EXAVMIMAGES/System.first.boot.20.1.1.0.0.200722.*bz2")
                ]
            ]
        }
 
        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _imgrev = self.mGetClubox().mGetImageVersion(_dom0)

            _pchecks = ebCluPreChecks(self.mGetClubox())
            _pchecks.cleanup_old_system_boot_files(_dom0, {_imgrev})
    
    def test_ebCluPreChecks__004_connectivity_checks(self):

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand('/bin/ping -c 1 *', aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexSwitch(): [
                [
                    exaMockCommand('smpartition list active *', aRc=0, aStdout='', aPersist=True)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _pchecks = ebCluPreChecks(self.mGetClubox())
        _pchecks.mConnectivityChecks(aCheckDomU=False)

    def test_ebCluDom0SanityTests_001_mRunIlomConsistencyTest(self):

        _jobs = []
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/ping *", aRc=0, aStdout="64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=47 time=17.8 ms", aPersist=True),
                    exaMockCommand("/bin/test -e /opt/oracle.cellos/cell.conf", aRc=0,  aPersist=True),
                    exaMockCommand("/usr/local/bin/ipconf -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime", aRc=0,aStdout="True"),
                    exaMockCommand("/usr/local/bin/imageinfo -version", aStdout="20.1.1.0.0.200803")
                ],
                [
                    exaMockCommand("/bin/test -e /opt/oracle.cellos/cell.conf", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/ping -c 1 *", aRc=0, aStdout="64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=47 time=17.8 ms", aPersist=True),
                    exaMockCommand("/usr/local/bin/ipconf -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime", aRc=0, aStdout="[Info]: Consistency check PASSED")
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 *", aRc=0, aStdout="64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=47 time=17.8 ms", aPersist=True)
                ]
            ]
        }

        # Init new Args
        self.mPrepareMockCommands(_cmds)
        _configpath = os.getcwd() + "/config/hardware_prechecks.conf"
        _precheck_config = {}
        with open(_configpath) as fd:
            _precheck_config = json.load(fd)

        # Prepare process manager
        _step = "ESTP_PREVM_CHECKS"
        _procManager = ProcessManager()
        _hw_health_table = _procManager.mGetManager().dict()
        _hw_health_table["nodes"] = []

        #Execute the clucontrol function
        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _imgrev = self.mGetClubox().mGetImageVersion(_dom0)
            _timeout = 300

            _pchecks = ebCluPreChecks(self.mGetClubox())
            _precheck_config['dom0_prechecks'] = {}
            _precheck_config['dom0_prechecks'] = {"ilom_consistency_test": "True"}
            _test_handler = ebCluDom0SanityTests(_pchecks, _dom0, aStep=_step, aPrecheckConfig=_precheck_config['dom0_prechecks'])

            _process = ProcessStructure(_test_handler.run, aArgs=[_hw_health_table], aId=_dom0)
            _process.mSetMaxExecutionTime(_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)
        
        ebLogInfo(f"Waiting for {_step} processes to end. This might take a while.")
        _procManager.mJoinProcess()
        del(_procManager)


    def test_ebCluDom0SanityTests_002_mRunIlomConsistencyTest(self):
        _jobs = []
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/ping *", aRc=0, aStdout="64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=47 time=17.8 ms", aPersist=True),
                    exaMockCommand("/bin/test -e /opt/oracle.cellos/cell.conf", aRc=0,  aPersist=True),
                    exaMockCommand("/usr/local/bin/ipconf -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime", aRc=0,aStdout="True"),
                    exaMockCommand("/usr/local/bin/imageinfo -version", aStdout="20.1.1.0.0.200803")
                ],
                [
                    exaMockCommand("/bin/test -e /opt/oracle.cellos/cell.conf", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/ping -c 1 *", aRc=0, aStdout="64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=47 time=17.8 ms", aPersist=True),
                    exaMockCommand("/usr/local/bin/ipconf -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime", aRc=0, aStdout="[Info]: Consistency check FAILED")
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 *", aRc=0, aStdout="64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=47 time=17.8 ms", aPersist=True)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _configpath = os.getcwd() + "/config/hardware_prechecks.conf"
        _precheck_config = {}
        with open(_configpath) as fd:
            _precheck_config = json.load(fd)

        # Prepare process manager
        _step = "ESTP_PREVM_CHECKS"
        _timeout = 300
        _procManager = ProcessManager()
        _hw_health_table = _procManager.mGetManager().dict()
        _hw_health_table["nodes"] = []

        #Execute the clucontrol function
        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _imgrev = self.mGetClubox().mGetImageVersion(_dom0)

            _pchecks = ebCluPreChecks(self.mGetClubox())
            _precheck_config['dom0_prechecks'] = {}
            _precheck_config['dom0_prechecks'] = {"ilom_consistency_test": "True"}
            _test_handler = ebCluDom0SanityTests(_pchecks, _dom0, aStep=_step, aPrecheckConfig=_precheck_config['dom0_prechecks'])

            _process = ProcessStructure(_test_handler.run, aArgs=[_hw_health_table], aId=_dom0)
            _process.mSetMaxExecutionTime(_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)

        ebLogInfo(f"Waiting for {_step} processes to end. This might take a while.")
        _procManager.mJoinProcess()
        del(_procManager)

    def test_ebCluDom0SanityTests_001_mRunComputePhysicalDiskTest(self):

        _jobs = []
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("dbmcli -e list physicaldisk attributes name,status", aRc=0, aStdout="", aPersist=True),   
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 *", aRc=0, aStdout="64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=47 time=17.8 ms", aPersist=True)
                ]
            ]
        }

        # Init new Args
        self.mPrepareMockCommands(_cmds)
        _configpath = os.getcwd() + "/config/hardware_prechecks.conf"
        _precheck_config = {}
        with open(_configpath) as fd:
            _precheck_config = json.load(fd)

        # Prepare process manager
        _step = "ESTP_PREVM_CHECKS"
        _procManager = ProcessManager()
        _hw_health_table = _procManager.mGetManager().dict()
        _hw_health_table["nodes"] = []

        #Execute the clucontrol function
        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _timeout = 300

            _pchecks = ebCluPreChecks(self.mGetClubox())
            _precheck_config['dom0_prechecks'] = {}
            _precheck_config['dom0_prechecks'] = {"computephysicaldisk_test": "True"}
            _test_handler = ebCluDom0SanityTests(_pchecks, _dom0, aStep=_step, aPrecheckConfig=_precheck_config['dom0_prechecks'])

            _process = ProcessStructure(_test_handler.run, aArgs=[_hw_health_table], aId=_dom0)
            _process.mSetMaxExecutionTime(_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)
        
        ebLogInfo(f"Waiting for {_step} processes to end. This might take a while.")
        _procManager.mJoinProcess()
        del(_procManager)

    def test_ebCluDom0SanityTests_002_mRunComputePhysicalDiskTest(self):

        _jobs = []
        _diskOutput="	 252:0	 failed"
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("dbmcli -e list physicaldisk attributes name,status", aRc=0, aStdout=_diskOutput, aPersist=True),   
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 *", aRc=0, aStdout="64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=47 time=17.8 ms", aPersist=True)
                ]
            ]
        }

        # Init new Args
        self.mPrepareMockCommands(_cmds)
        _configpath = os.getcwd() + "/config/hardware_prechecks.conf"
        _precheck_config = {}
        with open(_configpath) as fd:
            _precheck_config = json.load(fd)

        # Prepare process manager
        _step = "ESTP_PREVM_CHECKS"
        _procManager = ProcessManager()
        _hw_health_table = _procManager.mGetManager().dict()
        _hw_health_table["nodes"] = []

        #Execute the clucontrol function
        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _timeout = 300

            _pchecks = ebCluPreChecks(self.mGetClubox())
            _precheck_config['dom0_prechecks'] = {}
            _precheck_config['dom0_prechecks'] = {"computephysicaldisk_test": "True"}
            _test_handler = ebCluDom0SanityTests(_pchecks, _dom0, aStep=_step, aPrecheckConfig=_precheck_config['dom0_prechecks'])

            _process = ProcessStructure(_test_handler.run, aArgs=[_hw_health_table], aId=_dom0)
            _process.mSetMaxExecutionTime(_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)
        
        ebLogInfo(f"Waiting for {_step} processes to end. This might take a while.")
        _procManager.mJoinProcess()
        del(_procManager)

    def test_ebCluPreChecks_001_mFetchHardwareAlertsTest(self):

        _jobs = []
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/ping *", aRc=0, aStdout="64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=47 time=17.8 ms", aPersist=True),
                    exaMockCommand("/bin/test -e /opt/oracle.cellos/cell.conf", aRc=0,  aPersist=True),
                    exaMockCommand("/usr/local/bin/ipconf -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime", aRc=0,aStdout="['[Info]: Consistency check PASSED']"),
                    exaMockCommand("/usr/local/bin/imageinfo -version", aStdout="20.1.1.0.0.200803"),
                    exaMockCommand("ipmitool sdr type fan", aRc=0, aStdout="['ok', 'ok']"),
                    exaMockCommand("ipmitool chassis status *", aRc=0, aStdout="['System Power         : on']", aPersist=True),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2"),
                    exaMockCommand("ipmitool sdr type temperature *", aRc=0, aStdout="T_CORE_NET01 ok"),
                    exaMockCommand("df -h -B G |grep EXAVMIMAGES", aRc=0, aStdout="                         1589G  864G      725G  55% /EXAVMIMAGES"),
                    exaMockCommand("/bin/test -e /opt/oracle.cellos/cell.conf", aRc=0,  aPersist=True),
                    exaMockCommand("/usr/local/bin/ipconf -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime", aRc=0,aStdout="['[Info]: Consistency check PASSED']"),
                    exaMockCommand("dbmcli -e list physicaldisk attributes name,status*", aRc=0,aStdout="")
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True),
                    exaMockCommand("xm info |grep 'free_memory'", aRc=0, aStdout="free_memory            : 436429", aPersist=True),
                    
                ],
                [
                    exaMockCommand("service xend status | grep running", aRc=0, aStdout="xend daemon (pid 42613) is running...", aPersist=True)

                ],
                [
                    exaMockCommand("df -P *", aRc=0, aStdout="")
                ],
                [
                    exaMockCommand("xm info |grep 'free_memory'", aRc=0, aStdout="free_memory            : 436429", aPersist=True),
                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                ],
                [
                    exaMockCommand("xm info |grep 'free_memory'", aRc=0, aStdout="free_memory            : 436429", aPersist=True),
                ]
            ],
            self.mGetRegexCell(): [
                [
                   exaMockCommand("cellcli -e list cell detail | grep -E 'fanStatus|powerStatus|temperatureStatus|cellsrvStatus|msStatus|rsStatus'", aStdout="['fanStatus: normal', 'powerStatus: normal', 'temperatureStatus: normal', 'cellsrvStatus: normal', 'msStatus: normal', 'rsStatus: normal']", aPersist=True),
                   exaMockCommand("cellcli -e list *", aStdout="", aPersist=True),
                   exaMockCommand("/bin/uname -r", aRc=0, aStdout="", aPersist=True)
                ],
                [
                    exaMockCommand("cellcli -e list *", aStdout="", aPersist=True),
                    exaMockCommand("/bin/uname -r", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("df -P *", aRc=0, aStdout="")
                ]
            ],
            self.mGetRegexSwitch(): [
                [
                    exaMockCommand("env_test *", aRc=0, aStdout="['Voltage test returned OK', 'PSU test returned OK', 'Temperature test returned OK', 'FAN test returned OK', 'Connector test returned OK', 'Onboard ibdevice test returned OK', 'SSD test returned OK', 'Auto-link-disable test returned OK']")

                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 *", aRc=0, aStdout="64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=47 time=17.8 ms", aPersist=True)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _configpath = os.getcwd() + "/config/hardware_prechecks.conf"
        _precheck_config = {}
        with open(_configpath) as fd:
            _precheck_config = json.load(fd)

        self.mGetClubox().mSetCmd("hardware_alerts")
        self.mGetClubox().mSetSharedEnv(True)
        _options = self.mGetClubox().mGetOptions()

        _switch_list = ""
        if not self.mGetClubox().mIsKVM():
            _switch_list = self.mGetClubox().mReturnSwitches(True)

        # Prepare process manager
        _step = "ESTP_PREVM_CHECKS"
        _timeout = 300
        _procManager = ProcessManager()
        _hw_health_table = _procManager.mGetManager().dict()
        _hw_health_table["nodes"] = []

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _imgrev = self.mGetClubox().mGetImageVersion(_dom0)

            _pchecks = ebCluPreChecks(self.mGetClubox())
            _test_handler = ebCluDom0SanityTests(_pchecks, _dom0, 'quarter-rack-servers', aStep=_step, aOsType="ib", aOperationType="ADD_COMPUTE", aPrecheckConfig=_precheck_config['dom0_prechecks'])

            _process = ProcessStructure(_test_handler.run, aArgs=[_hw_health_table], aId=_dom0)
            _process.mSetMaxExecutionTime(_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)

        for _cell in self.mGetClubox().mReturnCellNodes().keys():
            _pchecks = ebCluPreChecks(self.mGetClubox())
            _test_handler = ebCluCellSanityTests(_pchecks, _cell, 'quarter-rack-servers', aStep=_step, aPrecheckConfig=_precheck_config['cell_prechecks'])

            _process = ProcessStructure(_test_handler.run, aArgs=[_hw_health_table], aId=_cell)
            _process.mSetMaxExecutionTime(_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)

        for _switch in _switch_list:
            _pchecks = ebCluPreChecks(self.mGetClubox())
            #_precheck_config['dom0_prechecks'] = {}
            #_precheck_config['dom0_prechecks'] = {"ilom_consistency_test": "True"}
            _test_handler = ebCluIbSwitchSanityTests(_pchecks, _switch, 'quarter-rack-servers', aStep=_step, aPrecheckConfig=_precheck_config['ibswitch_prechecks'])

            _process = ProcessStructure(_test_handler.run, aArgs=[_hw_health_table], aId=_switch)
            _process.mSetMaxExecutionTime(_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)

        ebLogInfo(f"Waiting for {_step} processes to end. This might take a while.")
        _procManager.mJoinProcess()
        del(_procManager)

        ebLogInfo(f"Result table: {_hw_health_table}")
        

    def test_ebCluPreChecks_002_mFetchHardwareAlertsTest(self):

        _jobs = []
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/ping *", aRc=0, aStdout="64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=47 time=17.8 ms", aPersist=True),
                    exaMockCommand("/bin/test -e /opt/oracle.cellos/cell.conf", aRc=0,  aPersist=True),
                    exaMockCommand("/usr/local/bin/ipconf -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime", aRc=0,aStdout="['[Info]: Consistency check PASSED']"),
                    exaMockCommand("/usr/local/bin/imageinfo -version", aStdout="20.1.1.0.0.200803"),
                    exaMockCommand("ipmitool sdr type fan", aRc=0, aStdout="['ok', 'ok']"),
                    exaMockCommand("ipmitool chassis status *", aRc=0, aStdout="['System Power         : on']", aPersist=True),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2"),
                    exaMockCommand("ipmitool sdr type temperature *", aRc=0, aStdout="T_CORE_NET01 ok"),
                    exaMockCommand("df -h -B G |grep EXAVMIMAGES", aRc=0, aStdout="                         1589G  864G      725G  55% /EXAVMIMAGES"),
                    exaMockCommand("/bin/test -e /opt/oracle.cellos/cell.conf", aRc=0,  aPersist=True),
                    exaMockCommand("/usr/local/bin/ipconf -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime", aRc=0,aStdout="['[Info]: Consistency check PASSED']"),
                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True),
                    exaMockCommand("dbmcli -e list physicaldisk attributes name,status*", aRc=0,aStdout="")
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True),
                    exaMockCommand("xm info |grep 'free_memory'", aRc=0, aStdout="free_memory            : 436429", aPersist=True),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2", aPersist=True)
                    
                ],
                [
                    exaMockCommand("service xend status | grep running", aRc=0, aStdout="xend daemon (pid 42613) is running...", aPersist=True),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2", aPersist=True)

                ],
                [
                    exaMockCommand("df -P *", aRc=0, aStdout=""),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2", aPersist=True)
                ],
                [
                    exaMockCommand("xm info |grep 'free_memory'", aRc=0, aStdout="free_memory            : 436429", aPersist=True),
                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2", aPersist=True)
                ],
                [
                    exaMockCommand("xm info |grep 'free_memory'", aRc=0, aStdout="free_memory            : 436429", aPersist=True),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2", aPersist=True) 
                ]
            ],
            self.mGetRegexCell(): [
                [
                   exaMockCommand("cellcli -e list cell detail | grep -E 'fanStatus|powerStatus|temperatureStatus|cellsrvStatus|msStatus|rsStatus'", aStdout="['fanStatus: normal', 'powerStatus: normal', 'temperatureStatus: normal', 'cellsrvStatus: normal', 'msStatus: normal', 'rsStatus: normal']", aPersist=True),
                   exaMockCommand("cellcli -e list *", aStdout="", aPersist=True),
                   exaMockCommand("/bin/uname -r", aRc=0, aStdout="", aPersist=True)
                ],
                [
                    exaMockCommand("cellcli -e list *", aStdout="", aPersist=True),
                    exaMockCommand("/bin/uname -r", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("df -P *", aRc=0, aStdout="")
                ]
            ],
            self.mGetRegexSwitch(): [
                [
                    exaMockCommand("env_test *", aRc=0, aStdout="['Voltage test returned OK', 'PSU test returned OK', 'Temperature test returned OK', 'FAN test returned OK', 'Connector test returned OK', 'Onboard ibdevice test returned OK', 'SSD test returned OK', 'Auto-link-disable test returned OK']")

                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 *", aRc=0, aStdout="64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=47 time=17.8 ms", aPersist=True)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _configpath = os.getcwd() + "/config/hardware_prechecks.conf"
        _precheck_config = {}
        with open(_configpath) as fd:
            _precheck_config = json.load(fd)

        self.mGetClubox().mSetCmd("hardware_alerts")
        self.mGetClubox().mSetSharedEnv(True)
        _options = self.mGetClubox().mGetOptions()

        _switch_list = ""
        if not self.mGetClubox().mIsKVM():
            _switch_list = self.mGetClubox().mReturnSwitches(True)

        # Prepare process manager
        _step = "ELASTIC_SHAPES_VALIDATION"
        _timeout = 300
        _procManager = ProcessManager()
        _hw_health_table = _procManager.mGetManager().dict()

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _host, _domain = _dom0.split('.', 1)
            _nodeInfo = {}
            _nodeInfo["hostname"] = _host
            _nodeInfo["domainname"] = _domain
            _nodeInfo["preprov"] = False
            _imgrev = self.mGetClubox().mGetImageVersion(_dom0)

            _pchecks = ebCluPreChecks(self.mGetClubox())
            _test_handler = ebCluDom0SanityTests(_pchecks,_nodeInfo, 'quarter-rack-servers', aStep=_step, aOsType="ib", aOperationType="ADD_COMPUTE",aPrecheckConfig=_precheck_config['dom0_prechecks'])

            _process = ProcessStructure(_test_handler.run, aArgs=[_hw_health_table], aId=_dom0)
            _process.mSetMaxExecutionTime(_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)

        for _cell in self.mGetClubox().mReturnCellNodes().keys():

            _host, _domain = _cell.split('.', 1)
            _nodeInfo = {}
            _nodeInfo["hostname"] = _host
            _nodeInfo["domainname"] = _domain
            _nodeInfo["preprov"] = False

            _pchecks = ebCluPreChecks(self.mGetClubox())
            _test_handler = ebCluCellSanityTests(_pchecks, _nodeInfo, 'quarter-rack-servers', aStep=_step, aPrecheckConfig=_precheck_config['cell_prechecks'])

            _process = ProcessStructure(_test_handler.run, aArgs=[_hw_health_table], aId=_cell)
            _process.mSetMaxExecutionTime(_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)

        for _switch in _switch_list:

            _host, _domain = _switch.split('.', 1)
            _nodeInfo = {}
            _nodeInfo["hostname"] = _host
            _nodeInfo["domainname"] = _domain
            _nodeInfo["preprov"] = False

            _pchecks = ebCluPreChecks(self.mGetClubox())
            _test_handler = ebCluIbSwitchSanityTests(_pchecks, _nodeInfo, 'quarter-rack-servers', aStep=_step, aPrecheckConfig=_precheck_config['ibswitch_prechecks'])

            _process = ProcessStructure(_test_handler.run, aArgs=[_hw_health_table], aId=_switch)
            _process.mSetMaxExecutionTime(_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)

        ebLogInfo(f"Waiting for {_step} processes to end. This might take a while.")
        _procManager.mJoinProcess()
        del(_procManager)

    def test_ebCluPreChecks_003_mCheckClusterIntegrityTest(self):

        _cmds = {

            self.mGetRegexVm(): [
                [
                   exaMockCommand("cat /etc/oratab *", aRc=0, aStdout="/u02/app/19.13.0.0/gridHome2", aPersist=True),
                   exaMockCommand(re.escape("export ORACLE_HOME=/u02/app/19.13.0.0/gridHome2; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                   exaMockCommand(re.escape("export ORACLE_HOME=/u02/app/19.13.0.0/gridHome2; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                   
                ],
                [
                    exaMockCommand("su - oracle -c *", aRc=0, aStdout="", aPersist=True)

                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 *", aRc=0, aStdout="64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=47 time=17.8 ms", aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = { "cell_list":["scaqab10celadm01"] }

        _pchecks = ebCluPreChecks(self.mGetClubox())
        _pchecks.mCheckClusterIntegrity(True)

    def test_ebCluPreChecks_004_mResetSwitchesTest(self):

        _cmds = {

            self.mGetRegexSwitch(): [
                [
                   exaMockCommand("getmaster", aRc=0, aStdout="Master SubnetManager on sm lid 1 sm guid 0x10e080265ca0a0 : SUN DCS 36P QDR scas22sw-ibb0 10.133.45.67", aPersist=True),
                   exaMockCommand("disablesm", aRc=0, aStdout="", aPersist=True),
                   exaMockCommand("enablesm", aRc=0, aStdout="", aPersist=True),
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 *", aRc=0, aStdout="64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=47 time=17.8 ms", aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _pchecks = ebCluPreChecks(self.mGetClubox())
        _pchecks.mResetSwitches()

    def test_ebCluPreChecks_005_mDigTest(self):

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("dig *", aRc=0, aStdout="no servers could be reached", aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _pchecks = ebCluPreChecks(self.mGetClubox())
        _pchecks.mDigTest(aIp="127.0.0.1")

    def test_ebCluPreChecks_006_mGeneratePasswordTest(self):

        _dpairs = self.mGetClubox().mReturnDom0DomUPair()
        _pchecks = ebCluPreChecks(self.mGetClubox())
        _pchecks.mGeneratePassword(aClusterID=self.mGetClubox().mGetClusters().mGetCluster().mGetCluId(), aClusterName= self.mGetClubox().mGetClusters().mGetCluster().mGetCluName(), aHostName=_dpairs[0][1])

    def test_ebCluPreChecks_007_mCheckScanNameTest(self):

        _pchecks = ebCluPreChecks(self.mGetClubox())
        _pchecks.mCheckScanName()

    def test_ebCluPreChecks_008_mGetAsmDbSnmpPasswordsTest(self):

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/var/opt/oracle/ocde/rops get_creg_key *", aRc=0, aStdout="Zl4_Qf0#397#9_84", aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.dbsid = "welcome1"

        _pchecks = ebCluPreChecks(self.mGetClubox())
        _pchecks.mGetAsmDbSnmpPasswords(_options)

    def test_ebCluPreChecks_009_mEMDBDetailsTest(self):

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/var/opt/oracle/ocde/rops get_creg_key c12279 service_name", aRc=0, aStdout="c12279.us.oracle.com", aPersist=True),
                    exaMockCommand("/var/opt/oracle/ocde/rops get_creg_key c12279 db_home", aRc=0, aStdout="/u02/app/oracle/product/12.2.0/dbhome_1", aPersist=True),
                    exaMockCommand("/var/opt/oracle/ocde/rops get_creg_key c12279 dbname", aRc=0, aStdout="c12279", aPersist=True),
                    exaMockCommand("srvctl status database -db `/var/opt/oracle/ocde/rops get_creg_key c12279 db_unique_name` | cut -d ' ' --output-delimiter ',' -f 2,7 | tr '\n' ' ' `", aRc=0, aStdout="c12279_L0oon1,scaqar07dv0105 c12279_L0oon2,scaqar07dv0305"),
                    exaMockCommand("srvctl config database -db `/var/opt/oracle/ocde/rops get_creg_key c12279 db_unique_name` | grep 'Database role:' | cut -d ' ' -f 3", aRc=0, aStdout="PRIMARY")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.dbsid = "c12279"

        _pchecks = ebCluPreChecks(self.mGetClubox())
        _pchecks.mEMDBDetails(_options)

    def test_ebCluPreChecks_010_mEMClusterDetailsTest(self):

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("ip netns", aRc=0, aStdout=""),
                    exaMockCommand("cat /var/opt/oracle/creg/grid/grid.ini", aRc=0, aStdout="/u02/app/19.13.0.0/gridHome2"),
                    exaMockCommand("cemutlo -", aRc=0, aStdout="iad163933exd-atpmg-scaqar07XXX-clu09"),
                    exaMockCommand("srvctl config scan | grep \"SCAN.*2.*IPv4 VIP:\" | cut -d \" \" -f 5", aRc=0, aStdout="10.32.176.245", aPersist=True),
                    exaMockCommand("srvctl config vip -node *", aRc=0, aStdout="10.32.176.245", aPersist=True),
                    exaMockCommand("crsctl stat res ora.LISTENER_SCAN1.lsnr | grep \"STATE=ONLINE\" | cut -d \" \" -f 3", aRc=0, aStdout="scaqar07dv0205", aPersist=True),
                    exaMockCommand("lsnrctl status ASMNET1LSNR_ASM *", aRc=0, aStdout="1525", aPersist=True),
                    exaMockCommand("echo *", aRc=0, aStdout="121", aPersist=True),
                    exaMockCommand("srvctl config scan_listener *", aRc=0, aStdout="1521", aPersist=True),
                    exaMockCommand("/var/opt/oracle/ocde/rops get_creg_key grid sid", aRc=0, aStdout="+ASM1", aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mSetExabm(True)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.dbsid = "c12279"

        _pchecks = ebCluPreChecks(self.mGetClubox())
        _pchecks.mEMClusterDetails(_options)

    def test_ebCluPreChecks_011_mCheckVMTimeDriftTest(self):

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("chronyc -c tracking", aRc=0, aStdout="0A1F8A14,10.31.138.20,3,1643039471.756592938,-0.000002127,0.000004000,0.000009529,-9.079,0.004,0.226,0.002991384,0.003501811,16.3,Normal"),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _pchecks = ebCluPreChecks(self.mGetClubox())
        _pchecks.mCheckVMTimeDrift()

    def test_ebCluPreChecks_012_mResetIBNetworkTest(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("cat /opt/oracle.cellos/ORACLE_CELL_OS_IS_SETUP | grep ovs", aRc=0, aStdout="ovs=no"),
                    exaMockCommand("sed *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("ip addr flush dev *", aRc=0, aStdout="", aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _pchecks = ebCluPreChecks(self.mGetClubox())
        _pchecks.mResetIBNetwork()

    def test_ebCluPreChecks_013_mParseHWAlertPayloadTest(self):

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = ELASTIC_SHAPES_PAYLOAD

        _pchecks = ebCluPreChecks(self.mGetClubox())
        _pchecks.mParseHWAlertPayload(_options)

    def test_ebCluPreChecks_014_validate_hw_resultsTest(self):

        _result = copy.deepcopy(ELASTIC_SHAPES_RESULT)
        _pchecks = ebCluPreChecks(self.mGetClubox())
        _pchecks.validate_hw_results("ELASTIC_SHAPES_VALIDATION", _result)

    def test_ebCluPrechecks_015_mHostnamesLengthChecks(self):
        with open(os.path.join(self.mGetPath(), "inventory.json"), "r") as _f:
            _inventory = json.loads(_f.read())
        self.mGetClubox().mSetRepoInventory(_inventory)

        _pchecks = ebCluPreChecks(self.mGetClubox())
        _pchecks.mHostnamesLengthChecks()

    def test_ebCluPreChecks_016_mUpdateNormalFlushedCellDisks(self):
        _jobs = []
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/ping *", aRc=0, aStdout="64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=47 time=17.8 ms", aPersist=True),
                    exaMockCommand("/bin/test -e /opt/oracle.cellos/cell.conf", aRc=0,  aPersist=True),
                    exaMockCommand("/usr/local/bin/ipconf -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime", aRc=0,aStdout="['[Info]: Consistency check PASSED']"),
                    exaMockCommand("/usr/local/bin/imageinfo -version", aStdout="20.1.1.0.0.200803"),
                    exaMockCommand("ipmitool sdr type fan", aRc=0, aStdout="['ok', 'ok']"),
                    exaMockCommand("ipmitool chassis status *", aRc=0, aStdout="['System Power         : on']", aPersist=True),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2", aPersist=True),
                    exaMockCommand("ipmitool sdr type temperature *", aRc=0, aStdout="T_CORE_NET01 ok"),
                    exaMockCommand("df -h -B G |grep EXAVMIMAGES", aRc=0, aStdout="                         1589G  864G      725G  55% /EXAVMIMAGES"),
                    exaMockCommand("/bin/test -e /opt/oracle.cellos/cell.conf", aRc=0,  aPersist=True),
                    exaMockCommand("/usr/local/bin/ipconf -nocodes -conf /opt/oracle.cellos/cell.conf -check-consistency -semantic -at-runtime", aRc=0,aStdout="['[Info]: Consistency check PASSED']"),
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True),
                    exaMockCommand("xm info |grep 'free_memory'", aRc=0, aStdout="free_memory            : 436429", aPersist=True),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2", aPersist=True)    
                ],
                [
                    exaMockCommand("service xend status | grep running", aRc=0, aStdout="xend daemon (pid 42613) is running...", aPersist=True),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2", aPersist=True)
                ],
                [
                    exaMockCommand("df -P *", aRc=0, aStdout=""),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2", aPersist=True)
                ],
                [
                    exaMockCommand("xm info |grep 'free_memory'", aRc=0, aStdout="free_memory            : 436429", aPersist=True),
                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2", aPersist=True)
                ],
                [
                    exaMockCommand("xm info |grep 'free_memory'", aRc=0, aStdout="free_memory            : 436429", aPersist=True),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aRc=0, aStdout="ORACLE SERVER X5-2", aPersist=True)
                ]
            ],
            self.mGetRegexCell(): [
                [
                   exaMockCommand("cellcli -e list cell detail | grep -E 'fanStatus|powerStatus|temperatureStatus|cellsrvStatus|msStatus|rsStatus'", aStdout="['fanStatus: normal', 'powerStatus: normal', 'temperatureStatus: normal', 'cellsrvStatus: normal', 'msStatus: normal', 'rsStatus: normal']", aPersist=True),
                   exaMockCommand("cellcli -e list *", aStdout="", aPersist=True),
                   exaMockCommand("/bin/uname -r", aRc=0, aStdout="", aPersist=True),
                   exaMockCommand("cellcli -e list flashcache attributes name,status where status!=\\'normal - flushed\\'", aStdout="['name: randomcel05_FLASHCACHE', 'cellDisk: FD_00_iad202834exdcl06,FD_01_iad202834exdcl06,FD_02_iad202834exdcl06,FD_03_iad202834exdcl06', 'creationTime: 2024-08-22T09:41:51+00:00', 'degradedCelldisks: ', 'effectiveCacheSize: 3.28692626953125T', 'id: 4dc2bb56-a231-47e2-99b3-9a7b111cae8f', 'size: 23.28692626953125T', 'status: normal - flushed']", aPersist=True),
                   exaMockCommand("cellcli -e alter flashcache all cancel flush", aRc=0, aStdout="Flash cache randomcel05_FLASHCACHE altered successfully", aPersist=True),
                ],
                [
                    exaMockCommand("cellcli -e list *", aStdout="", aPersist=True),
                    exaMockCommand("/bin/uname -r", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("df -P *", aRc=0, aStdout="")
                ]
            ],
            self.mGetRegexSwitch(): [
                [
                    exaMockCommand("env_test *", aRc=0, aStdout="['Voltage test returned OK', 'PSU test returned OK', 'Temperature test returned OK', 'FAN test returned OK', 'Connector test returned OK', 'Onboard ibdevice test returned OK', 'SSD test returned OK', 'Auto-link-disable test returned OK']")

                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 *", aRc=0, aStdout="64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=47 time=17.8 ms", aPersist=True)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _configpath = os.getcwd() + "/config/hardware_prechecks.conf"
        _precheck_config = {}
        with open(_configpath) as fd:
            _precheck_config = json.load(fd)

        self.mGetClubox().mSetCmd("hardware_alerts")
        self.mGetClubox().mSetSharedEnv(True)
        _options = self.mGetClubox().mGetOptions()

        _switch_list = ""
        if not self.mGetClubox().mIsKVM():
            _switch_list = self.mGetClubox().mReturnSwitches(True)

        # Prepare process manager
        _step = "ELASTIC_SHAPES_VALIDATION"
        _timeout = 300
        _procManager = ProcessManager()
        _hw_health_table = _procManager.mGetManager().dict()

        for _cell in self.mGetClubox().mReturnCellNodes().keys():

            _pchecks = ebCluPreChecks(self.mGetClubox())

            _test_handler = ebCluCellSanityTests(_pchecks, _cell, 'quarter-rack-servers', aStep="ESTP_PREVM_CHECKS", aPrecheckConfig=_precheck_config['cell_prechecks'])

            _process = ProcessStructure(_test_handler.run, aArgs=[_hw_health_table], aId=_cell)
            _process.mSetMaxExecutionTime(_timeout)
            _process.mSetLogTimeoutFx(ebLogWarn)
            _procManager.mStartAppend(_process)
        
        ebLogInfo(f"Waiting for {_step} processes to end. This might take a while.")
        _procManager.mJoinProcess()
        del(_procManager)

    def test_ebCluFetchSshKeys_001_mGetSSHkeys(self):
        #test to check the functionality of exacloud returning error message without exception raising when keys are not found.
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _data = {}
        _pchecks = ebCluFetchSshKeys(self.mGetClubox(), _options.hostname)
        _rc, _jsondata = _pchecks.mGetSSHkeys(_data, "all_nodes", "all", "root", None)
        ebLogInfo(f"output: {_jsondata}")
        

    def test_ebCluFetchSshKeys_001_mFetchSshKeysTest(self):
    
        _exakms = ExaKmsFileSystem()
        self.mGetClubox().mSetExabm(True)

        #1. ADD DOM0 Key to KMS
        # Generate private key
        _privateKey = _exakms.mGetEntryClass().mGeneratePrivateKey()
        _hostname = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        _user = "root"

        # Add new KMS Entry
        _entry = _exakms.mBuildExaKmsEntry(_hostname, _user, _privateKey)
        _exakms.mInsertExaKmsEntry(_entry)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = {"node_type":"dom0", "host":"scaqab10adm01.us.oracle.com", "user":"root"}

        _pchecks = ebCluFetchSshKeys(self.mGetClubox(), _options.hostname)
        _output = _pchecks.mFetchSshKeys(_options)

        _entries = _exakms.mSearchExaKmsEntries({})

        # Delete KMS Entry
        _exakms.mDeleteExaKmsEntry(_entry)

        #2. ADD CELL Key to KMS
        # Generate private key
        _privateKey = _exakms.mGetEntryClass().mGeneratePrivateKey()
        _hostname = list(self.mGetClubox().mReturnCellNodes().keys())[0]
        _user = "root"

        # Add new KMS Entry
        _entry = _exakms.mBuildExaKmsEntry(_hostname, _user, _privateKey)
        _exakms.mInsertExaKmsEntry(_entry)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = {"node_type":"cell", "host":"scaqab10celadm01.us.oracle.com", "user":"root"}

        _pchecks = ebCluFetchSshKeys(self.mGetClubox(), _options.hostname)
        _output = _pchecks.mFetchSshKeys(_options)

        _entries = _exakms.mSearchExaKmsEntries({})

        # Delete KMS Entry
        _exakms.mDeleteExaKmsEntry(_entry)

        #3. ADD SWITCH Key to KMS
        # Generate private key
        _switch_list = []
        if not self.mGetClubox().mIsKVM():
            _switch_list = self.mGetClubox().mReturnSwitches(True)
        _privateKey = _exakms.mGetEntryClass().mGeneratePrivateKey()
        _hostname = _switch_list[0]
        _user = "root"

        # Add new KMS Entry
        _entry = _exakms.mBuildExaKmsEntry(_hostname, _user, _privateKey)
        _exakms.mInsertExaKmsEntry(_entry)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = {"node_type":"ibswitch", "host":"scaqab10sw-iba0.us.oracle.com", "user":"root"}

        _pchecks = ebCluFetchSshKeys(self.mGetClubox(), _options.hostname)
        _output = _pchecks.mFetchSshKeys(_options)

        _entries = _exakms.mSearchExaKmsEntries({})

        # Delete KMS Entry
        _exakms.mDeleteExaKmsEntry(_entry)

        #4. ADD DOMU Key to KMS
        # Generate private key
        _privateKey = _exakms.mGetEntryClass().mGeneratePrivateKey()
        _hostname = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _user = "root"

        # Add new KMS Entry
        _entry = _exakms.mBuildExaKmsEntry(_hostname, _user, _privateKey)
        _exakms.mInsertExaKmsEntry(_entry)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = {"node_type":"domu", "host":"scaqab10client01vm08.us.oracle.com", "user":"root"}

        _pchecks = ebCluFetchSshKeys(self.mGetClubox(), _options.hostname)
        _output = _pchecks.mFetchSshKeys(_options)

        _entries = _exakms.mSearchExaKmsEntries({})

        # Delete KMS Entry
        _exakms.mDeleteExaKmsEntry(_entry)

    def test_ebCluScheduleManager_001_mListScheduledJobsTest(self):

        _options = self.mGetClubox().mGetArgsOptions()
        _options.sccmd = "list"

        _psched_manager = ebCluScheduleManager(self.mGetClubox())
        _psched_manager.mHandleRequest(_options)

    def test_ebCluCellValidate_001_mValidateCellStatTest(self):

        _cmds = {

            self.mGetRegexCell(): [
                [
                   exaMockCommand("/usr/local/bin/imageinfo -version", aRc=0, aStdout="21.2.5.0.0.211013", aPersist=True),
                   exaMockCommand("dmidecode | grep Exadata | tail -1", aRc=0, aStdout="Exadata X8M-2", aPersist=True),
                   exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli *", aRc=0, aStdout="", aPersist=True),
                   exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e list cell detail", aRc=0, aStdout="name: scas22celadm05\ncellsrvStatus: running\nmsStatus: running\nrsStatus: running\n", aPersist=True),
                   exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e *", aRc=0, aStdout="", aPersist=True),
                ],
                [
                    exaMockCommand("/usr/local/bin/imageinfo -version", aRc=0, aStdout="21.2.5.0.0.211013", aPersist=True),
                    exaMockCommand("/bin/rpm -qa *", aRc=0, aStdout="", aPersist=True),
                ],
                [
                    exaMockCommand("/usr/local/bin/imageinfo -version", aRc=0, aStdout="21.2.5.0.0.211013", aPersist=True),
                    exaMockCommand("/bin/rpm -qa *", aRc=0, aStdout="", aPersist=True),
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 *", aRc=0, aStdout="64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=47 time=17.8 ms", aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = {"cell_list":["scaqab10celadm01.us.oracle.com"]}
        _cell_list = _options.jsonconf["cell_list"]

        _cell_validate = ebCluCellValidate(self.mGetClubox(), _options)
        for _cell in _cell_list:
            _cell_validate.mValidateCellStat(_options, _cell)

        _cell_validate.mValidateAuthConfig(_cell_list)

    def test_OracleVersion_001_mSortVersionTest(self):

        _listVersions = ["12.2.1.1.2.170830", "12.2.1.1.2.170926", "18.1.1.0.0.171018"]
        _version = OracleVersion()
        _sortlist = _version.mSortVersion(_listVersions)

        _high_ver = _version.mGetHighestVer(_sortlist)
        self.assertEqual(_high_ver, "18.1.1.0.0.171018")

    def test_mValidateVersionForMVM(self):
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand(".*",aPersist=True)
                ]
            ]
        }
 
        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = { "skip_sysimage_version_check":"true" }

        _pchecks = ebCluPreChecks(self.mGetClubox())        
        with patch('exabox.ovm.clumisc.mGetDom0sImagesListSorted', return_value=["21.2.15"]):
            _pchecks.mValidateVersionForMVM(_options)

        _pchecks = ebCluPreChecks(self.mGetClubox())        
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetCmd', side_effect=iter(["relax_oeda_image_version_check", "mvm_migrate_check"])),\
             patch('exabox.ovm.clumisc.mGetDom0sImagesListSorted', return_value=["21.2.16"]),\
             patch('exabox.ovm.clumisc.ebCluCmdCheckOptions', return_value=True),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetDomUImageVer'):
            _pchecks.mValidateVersionForMVM(_options)

        _pchecks = ebCluPreChecks(self.mGetClubox())        
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetCmd', side_effect=iter(["relax_oeda_image_version_check", "mvm_migrate_check"])),\
             patch('exabox.ovm.clumisc.mGetDom0sImagesListSorted', return_value=["21.2.15"]),\
             patch('exabox.ovm.clumisc.ebCluCmdCheckOptions', return_value=True):
            try: 
                _pchecks.mValidateVersionForMVM(_options)
            except ExacloudRuntimeError as e:
                self.assertEqual('2066',str(e.mGetErrorCode()))
                self.assertEqual('EXACLOUD : System version invalid for migration',str(e.mGetErrorMsg()))

        # v21.2.13 Raises Exception
        # System Image version({_minVersion}) is be same or older than minimum cut off version({_cutOffVersionMVM}) required for MVM
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSharedEnv', return_value=True),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetCmd', return_value="createservice"),\
             patch('exabox.ovm.clumisc.mGetDom0sImagesListSorted', return_value=["21.2.13"]):
            try: 
                _pchecks.mValidateVersionForMVM(_options)
            except ExacloudRuntimeError as e:
                self.assertEqual('2066',str(e.mGetErrorCode()))
                self.assertEqual('EXACLOUD : System Image version(21.2.13) must be same or older than minimum cut off version(21.2.14) required for MVM',str(e.mGetErrorMsg()))

    def test_ebCluDom0SanityTests_mRunHypervisorTest(self):
        _jobs = []
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"imageinfo | grep 'Node type:'", aRc=0, aStdout="Type Hypervisor KVMHOST", aPersist=True),
                    exaMockCommand(f"cat /sys/hypervisor/type", aRc=0, aStdout="KVMHOST", aPersist=True),
                    exaMockCommand("systemctl is-enabled libvirtd*", aRc=0,aStdout="disabled"),
                    exaMockCommand("systemctl enable libvirtd*", aStdout=""),
                    exaMockCommand("systemctl is-enabled libvirtd*", aStdout="enabled")
                ],
                [
                    exaMockCommand(f"imageinfo | grep 'Node type:'", aRc=0, aStdout="Type Hypervisor KVMHOST", aPersist=True),
                    exaMockCommand(f"cat /sys/hypervisor/type", aRc=0, aStdout="KVMHOST", aPersist=True),
                ],
                [
                    exaMockCommand("systemctl is-active libvirtd.service", aRc=0, aStdout="active", aPersist=True),
                    exaMockCommand("systemctl start libvirtd.service", aRc=0,  aPersist=True)
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 *", aRc=0, aStdout="64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=47 time=17.8 ms", aPersist=True)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _configpath = os.getcwd() + "/config/hardware_prechecks.conf"
        _precheck_config = {}
        with open(_configpath) as fd:
            _precheck_config = json.load(fd)

        # Prepare process manager
        _step = "ESTP_PREVM_CHECKS"
        _timeout = 300
        _procManager = ProcessManager()
        _hw_health_table = _procManager.mGetManager().dict()
        _hw_health_table["nodes"] = []

        #Execute the clucontrol function
        _ebox_local = copy.deepcopy(self.mGetClubox())  #local ebox
        _dom0 = _ebox_local.mReturnDom0DomUPair()[0][0] #local ebox
        _ebox_local.mSetEnableKVM(True)                 #local ebox
        _pchecks = ebCluPreChecks(_ebox_local)          #local ebox
        #_dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        #_pchecks = ebCluPreChecks(self.mGetClubox())

        _precheck_config['dom0_prechecks'] = {}
        _precheck_config['dom0_prechecks'] = {"hypervisor_test": "True"}
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True), \
            patch('exabox.ovm.hypervisorutils.getHVInstance', return_value=ebKvmVmMgr({"hostname":"scaqab10adm01.us.oracle.com"})):
            _test_handler = ebCluDom0SanityTests(_pchecks, _dom0, aStep=_step, aPrecheckConfig=_precheck_config['dom0_prechecks'])

        _process = ProcessStructure(_test_handler.run, aArgs=[_hw_health_table], aId=_dom0)
        _process.mSetMaxExecutionTime(_timeout)
        _process.mSetLogTimeoutFx(ebLogWarn)
        _procManager.mStartAppend(_process)

        ebLogInfo(f"Waiting for {_step} processes to end. This might take a while.")
        _procManager.mJoinProcess()
        del(_procManager)
        ebLogInfo(f"Result table: {_hw_health_table}")

if __name__ == '__main__':
    unittest.main(warnings='ignore', buffer=True)

# end file
