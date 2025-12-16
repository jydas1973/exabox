#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_clumisc.py /main/41 2025/11/15 11:40:54 joysjose Exp $
#
# tests_clumisc.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_clumisc.py - Unit Tests for ovm/clumisc.py
#
#    DESCRIPTION
#      Unit Tests for ovm/clumisc module
#
#    NOTES
#
#    MODIFIED   (MM/DD/YY)
#    joysjose    10/23/25   - Bug 38417178 Refactoring cell connections before
#                             create VM
#    nelango     10/10/25   - Bug 38524837: unittest correction for 38261183
#    nelango     09/24/25   - Bug 38261183: Unittest for check eth speed
#    bhpati      09/09/25   - Bug 38258245 - prevmchecks during create cluster
#                             is trying to set the speed even if the speed is
#                             already correct
#    naps        09/09/25   - Bug 38347003 - For zdlra migrate users confirming
#                             to accessUpdater.
#    nelango     08/29/25   - Bug 38299928: Postpone restore SSH keys after
#                             cleanup and validation are complete
#    ririgoye    07/21/25   - Enh 38219932 - Adding invalid location info for
#                             site groups configuration
#    hcheon      07/21/25   - 38196008 Cell force shutdown for fault injection
#    ririgoye    06/26/25   - Enh 38086929 - Test creation of sitegroups config
#                             file
#    araghave    05/07/25   - Enh 37892080 - TO IMPLEMENT NEWER PATCHSWITCHTYPE
#                             CHANGES APPLICABLE TO ALL SWITCH TARGET TYPES AND
#                             PATCH COMBINATIONS
#    ririgoye    03/28/25   - Enh 37735179 - Adding tests for locks of dom0s
#                             during users remap
#    akkar       03/06/25   - Bug 37573195: Test cases for interface to inject network errors for stre0 and stre1
#    antamil     02/12/25 - 37567374: Multiple patchmgr session on launch node
#                           for clusterless patching
#    antamil     01/31/25 - Enh 37300427 - Enable clusterless cell patching
#                           using management host
#    prsshukl    11/28/24 - Bug 37240032 - Removal of testcase
#                           test_mCorrectTimeDifinNode_success
#    prsshukl    11/19/24 - Bug 37288941 - MRESTARTVMEXACSSERVICE SHOULD CHECK
#                           IF VMEXACS_KVM SERVICE IS UP PRIOR TO RESTART
#    prsshukl    11/13/24 - Bug 37274900 - CAIXA-BANK : EXACS: STORAGE NODE
#                           SCALE OPERATION FAILED WITH ERROR - <PID> - OEDACLI
#                           ERRORS FOUND:
#    jfsaldan    11/04/24 - Bug 37207274 -
#                           EXACS:24.4.1:241021.0914:MULTI-VM:PARALLEL VM
#                           CLUSTER PROVISIONING FAILING AT PREVM SETUP
#                           STEP:EXACLOUD : COULD NOT UPDATE CELL DISK SIZE
#    bhpati      09/27/24 - DOMU PRECHECK IS REMOVING EXISTING ROOT
#                           SSH-EQUIVALENCE FROM NODE1 TO NODE2
#    prsshukl    08/12/24 - Enh 36557797 - Unittest for
#                           mRestartVmExacsService
#    bhpati      07/31/24 - BUG 36672855 Test case for public key backup and
#                           restore.
#    joysjose    07/30/24 - bug36563704 remove mCheckHostImage from
#                           mAddNodePrecheck
#    joysjose    07/25/24 - ER-36120286 - EXACS: EXACLOUD TO DISPLAY A SUMMARY
#                           REPORT OF ISSUES FOUND DURING SCALE PRECHECK
#    gojoseph    07/08/24 - BUG 36672995 Test case for asmmodestatus='UNKNOWN'
#    remamid     05/14/24 - Bug 36554329 - IMPROVE DBAAS.UPDATEEXADATASTORAGE
#                           WORKREQUEST FAILURE
#    pkandhas    03/18/24 - test case for pkandhas_bug-36154049
#    avimonda    12/22/23 - 35631991 TXN AVIMONDA_BUG-35412261 REQUIRES A UNIT
#                           TEST CASE FOR BUG(S) 35412261
#    avimonda    12/22/23 - new file
#    avimonda    12/22/23 - Creation
#

import json
import unittest
import re
import copy
import os
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.clumisc import ebCluPreChecks,ebCluSshSetup,OracleVersion,ebCluStorageReshapePrecheck,ebCluStartStopHostFromIlom, ebCluNodeSubsetPrecheck, ebCluRestartVmExacsService, ebCluFaultInjection, ebMigrateUsersUtil, mGetGridListSupportedByOeda, ebCluCellSanityTests, ebCluEthernetConfig, ebCluCellValidate
from exabox.ovm.monitor import ebClusterNode
import warnings
from unittest.mock import patch, Mock, mock_open, call
from exabox.core.Error import ExacloudRuntimeError
from exabox.utils.node import  connect_to_host
from exabox.ovm.adbs_elastic_service import mCreateADBSSiteGroupConfig
from exabox.ovm.clumisc import mWaitForSystemBoot, ebMiscFx, mGetAlertHistoryOptions, ebADBSUtil, ebCluEthernetConfig
from exabox.ovm.kvmvmmgr import ebKvmVmMgr
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.utils.common import mCompareModel


SSH_KEY1 = "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEArCjp6sw0M36Cm1yJasmUeGDnMGyYZqRk+dl01OOTrwDT6mKGVD+UJfU3ACRyejKPW09fZkMFp7nhBf8gTapSwvyhcelO580iWzNCGoB5oeexivaXJpBaD01PKqd1NpgQfs90qIIXeB4ej5Z/kxGwT18Tnl6hSRxscH1tjkRfHxbajDGndd7cBP71asEPZyGIFIncp5Oi4fNmi7xX29HCT5LFaQwbtxC587HkCviRdaZLmYx7FaA9tN5gaXDg8qavF/4ImpwKosWUk9WcXecb1V0W6bxx/DHEuy6MZNHZR0RlRgFmFEZQQBFJUGCnq3JOSLm0dZE2yCUnFDT0VryjoQ== root@scas07adm07.us.oracle.com"

HARDWARE_ALERT_VALIDATE_ELASTIC_SHAPE_JSON = {"iad207206exdcl14.iad200071qfab.adminiad2.oraclevcn.com":{"Details":{"pmemcache":{"iad207206exdcl14_PMEMCACHE":"warning - degraded"}},"celldisk":"normal","cellsrvStatus":"running","fan":"normal","flashcache":"normal","griddisk":"normal","lun":"normal","msStatus":"running","node_info":[{"domainname":"iad200071qfab.adminiad2.oraclevcn.com","error_list":[{"error-message":{"iad207206exdcl14_PMEMCACHE":"warning - degraded"},"error-type":"pmemcache"}],"hostname":"iad207206exdcl14","hw_type":"CELL","node-model":"X8M-2","preprov":False}],"physicaldisk":"normal","ping_test":"normal","pmemcache":"abnormal","power":"normal","root_storage_test":"normal","rsStatus":"running","ssh_test":"normal","temperature":"normal"},"iad207206exdcl15.iad200071qfab.adminiad2.oraclevcn.com":{"Details":{},"celldisk":"normal","cellsrvStatus":"running","fan":"normal","flashcache":"normal","griddisk":"normal","lun":"normal","msStatus":"running","node_info":[{"domainname":"iad200071qfab.adminiad2.oraclevcn.com","hostname":"iad207206exdcl15","hw_type":"CELL","node-model":"X8M-2","preprov":False}],"physicaldisk":"normal","ping_test":"normal","pmemcache":"normal","power":"normal","root_storage_test":"normal","rsStatus":"running","ssh_test":"normal","temperature":"normal"},"iad207215exdcl12.iad200071qfab.adminiad2.oraclevcn.com":{"Details":{},"celldisk":"normal","cellsrvStatus":"running","fan":"normal","flashcache":"normal","griddisk":"normal","lun":"normal","msStatus":"running","node_info":[{"domainname":"iad200071qfab.adminiad2.oraclevcn.com","hostname":"iad207215exdcl12","hw_type":"CELL","node-model":"X8M-2","preprov":False}],"physicaldisk":"normal","ping_test":"normal","pmemcache":"normal","power":"normal","root_storage_test":"normal","rsStatus":"running","ssh_test":"normal","temperature":"normal"}}

HARDWARE_ALERT_VALIDATE_ELASTIC_SHAPE_JSON_SUC = {"iad207202exdcl01.iad200071qfab.adminiad2.oraclevcn.com":{"Details":{},"celldisk":"normal","cellsrvStatus":"running","fan":"normal","flashcache":"normal","griddisk":"normal","lun":"normal","msStatus":"running","node_info":[{"domainname":"iad200071qfab.adminiad2.oraclevcn.com","hostname":"iad207202exdcl01","hw_type":"CELL","node-model":"X8M-2","preprov":False}],"physicaldisk":"normal","ping_test":"normal","pmemcache":"normal","power":"normal","root_storage_test":"normal","rsStatus":"running","ssh_test":"normal","temperature":"normal"},"iad207202exdcl02.iad200071qfab.adminiad2.oraclevcn.com":{"Details":{},"celldisk":"normal","cellsrvStatus":"running","fan":"normal","flashcache":"normal","griddisk":"normal","lun":"normal","msStatus":"running","node_info":[{"domainname":"iad200071qfab.adminiad2.oraclevcn.com","hostname":"iad207202exdcl02","hw_type":"CELL","node-model":"X8M-2","preprov":False}],"physicaldisk":"normal","ping_test":"normal","pmemcache":"normal","power":"normal","root_storage_test":"normal","rsStatus":"running","ssh_test":"normal","temperature":"normal"}}

HARDWARE_ALERT_ESTP_PREVM_CHECKS_JSON =  {"nodes": [{"hostname": "iad103716exdd012", "domainname": "iad103716exd.adminiad1.oraclevcn.com", "hw_type": "COMPUTE", "ping_test": "normal", "ssh_test": "normal", "fan": "normal", "power": "normal", "temperature": "abnormal", "hypervisor": "running", "root_storage_test": "normal", "storage_check_exavmimages": "normal", "memory_check": "normal"}, {"hostname": "iad103716exdd011", "domainname": "iad103716exd.adminiad1.oraclevcn.com", "hw_type": "COMPUTE", "ping_test": "normal", "ssh_test": "normal", "fan": "normal", "power": "normal", "temperature": "normal", "hypervisor": "stopped", "root_storage_test": "normal", "storage_check_exavmimages": "normal", "memory_check": "normal"}, {"Details": {}, "hostname": "iad103710exdcl13", "domainname": "iad103710exd.adminiad1.oraclevcn.com", "hw_type": "CELL", "ping_test": "normal", "ssh_test": "abnormal", "fan": "normal", "power": "normal", "temperature": "normal", "cellsrvStatus": "running", "msStatus": "running", "rsStatus": "running", "lun": "normal", "physicaldisk": "abnormal", "griddisk": "normal", "celldisk": "normal", "root_storage_test": "normal"}]}  

HARDWARE_ALERT_ESTP_PREVM_CHECKS_JSON_SUC =  {"nodes": [{"hostname": "iad103716exdd012", "domainname": "iad103716exd.adminiad1.oraclevcn.com", "hw_type": "COMPUTE", "ping_test": "normal", "ssh_test": "normal", "fan": "normal", "power": "normal", "temperature": "normal", "hypervisor": "running", "root_storage_test": "normal", "storage_check_exavmimages": "normal", "memory_check": "normal"}]}

JSON_STOP_START_ILOM = {
"operation": "stop",
"host_ilom_pair": {
"some_host" : "some_ilom"                                                                                     
}
}

JSON_STOP_START_ILOM_ERROR1 = {
"operation": "wait",
"host_ilom_pair": {
"some_host" : "some_ilom"                                                                                    
}
}

JSON_STOP_START_ILOM_ERROR2 = {
"host_ilom_pair": {
"some_host" : "some_ilom"}
}

JSON_STOP_START_ILOM_ERROR3 = {
"operation": "stop"                                                                                 
}

JSON_INSTANCE_HEALTH = {
"optype": "instancehealth",
"hostname": "iad207202exdcl02.iad200071qfab.adminiad2.oraclevcn.com",
"nodetype": "cell"
}

JSON_LIFECYCLE_START = {
"optype": "lifecycle",
"hostname": "scaqab10adm01.us.oracle.com",
"nodetype": "compute",
"action" : "start"
}

JSON_LIFECYCLE_STOP = {
"optype": "lifecycle",
"hostname": "scaqab10adm01.us.oracle.com",
"nodetype": "compute",
"action" : "stop"
}
JSON_LIFECYCLE_NONE = {
"optype": "lifecycle",
"hostname": "scaqab10adm01.us.oracle.com",
"nodetype": "compute",
"action" : None
}

JSON_NETWORK_PARTITION_DOWN = {
"optype": "network-partition",
"hostname": "iad207202exdcel01.iad200071qfab.adminiad2.oraclevcn.com",
"nodetype": "cell",
"action": "down"
}

JSON_NETWORK_PARTITION_UP = {
"optype": "network-partition",
"hostname": "iad207202exdcel01.iad200071qfab.adminiad2.oraclevcn.com",
"nodetype": "cell",
"action": "up"
}

USER_GROUPS_REMAPPING = {
"rrichards": {"uid": 5431, "gid": 8201},
"pparker": {"uid": 1205, "gid": 6743},
"ckent": {"uid": 7889, "gid": 1532},
"asmith": {"uid": 3349, "gid": 4011},
"lskywalker": {"uid": 6277, "gid": 5509},
"dprince": {"uid": 4156, "gid": 3076},
"tstark": {"uid": 8823, "gid": 7765},
"jdoe": {"uid": 2998, "gid": 9120},
"bwayne": {"uid": 1054, "gid": 6354}
}

SITE_GROUPS_JSON = {
"location": { 
    "ad": "IAD1",
    "building": "ririgoyebuilding",
    "cloud_vendor": "ririgoye",
    "region": "iad1.region1",
    "restricted": "N",
    "site_group": "ririgoyesitegroup"
    }
}

MAX_RETRY = 3

def mRemoteExecute(aCmd):
    return "critical HW Alert"

class mMockPrecheck:
    def __init__(self, aCluCtrl):
        self.__cluctrl = aCluCtrl

    def mGetEbox(self):
        return self.__cluctrl


class ebTestFaultInjection(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestFaultInjection, self).setUpClass(True, True)
        warnings.filterwarnings("ignore")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCellsServicesUp', return_value=True)
    def test_mHandleInstanceHealth(self, aMockmCheckCellsServicesUp):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_INSTANCE_HEALTH
        _faultInjection = ebCluFaultInjection(self.mGetClubox(), _ebox_local._exaBoxCluCtrl__options)
        _cmds = {
        }
        self.mPrepareMockCommands(_cmds)
        _faultInjection.mHandleRequest()

    @patch('exabox.ovm.clumisc.FAULT_INJECTION_INIT_CHECK_DELAY_AFTER_START', 0.01)
    def test_mHandleLifeCycle_start_server(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LIFECYCLE_START
        _faultInjection = ebCluFaultInjection(self.mGetClubox(), _ebox_local._exaBoxCluCtrl__options)
        _cmds = {

            self.mGetRegexLocal(): [

                [
                    exaMockCommand(re.escape("[['->', 'start /System'], ['->', 'show /System']]"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape(f'/bin/ping -c 1 scaqab10adm01.us.oracle.com'), aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _faultInjection.mHandleRequest()

    def test_mHandleLifeCycle_stop_server(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LIFECYCLE_STOP
        _faultInjection = ebCluFaultInjection(self.mGetClubox(), _ebox_local._exaBoxCluCtrl__options)
        _cmds = {

            self.mGetRegexLocal(): [

                [
                    exaMockCommand(re.escape(f'/bin/ping -c 1 scaqab10adm01.us.oracle.com'), aRc=1, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _faultInjection.mHandleRequest()

    @patch('exabox.ovm.clumisc.FAULT_INJECTION_STOP_SLEEP_TIME_FROM_ILOM', 0.3)
    @patch('exabox.ovm.clumisc.FAULT_INJECTION_PING_CHECK_INTERVAL', 0.1)
    @patch('exabox.core.Node.exaBoxNode.mExecuteCmdsAuthInteractive')
    def test_mHandleLifeCycle_stop_server_force(self, mock_mExecuteCmdsAuthInteractive):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LIFECYCLE_STOP
        _faultInjection = ebCluFaultInjection(self.mGetClubox(), _ebox_local._exaBoxCluCtrl__options)
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand(re.escape(f'/bin/ping -c 1 scaqab10adm01.us.oracle.com'), aRc=0),
                    exaMockCommand(re.escape(f'/bin/ping -c 1 scaqab10adm01.us.oracle.com'), aRc=0),
                    exaMockCommand(re.escape(f'/bin/ping -c 1 scaqab10adm01.us.oracle.com'), aRc=0),
                    exaMockCommand(re.escape(f'/bin/ping -c 1 scaqab10adm01.us.oracle.com'), aRc=0),
                    exaMockCommand(re.escape(f'/bin/ping -c 1 scaqab10adm01.us.oracle.com'), aRc=1, aPersist=True),
                ]
            ],
        }
        self.mPrepareMockCommands(_cmds)
        _faultInjection.mHandleRequest()
        self.assertEqual(
            [
                call([['->', 'stop /System'], ['->', 'show /System']]),
                call([['->', 'stop -f /System'], ['->', 'show /System']])
            ],
            mock_mExecuteCmdsAuthInteractive.call_args_list)

    def test_mHandleLifeCycle_none(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_LIFECYCLE_NONE
        _faultInjection = ebCluFaultInjection(self.mGetClubox(), _ebox_local._exaBoxCluCtrl__options)
        _cmds = {
        }
        self.mPrepareMockCommands(_cmds)
        try:
            _faultInjection.mHandleRequest()
        except:
            pass

    def test_mHandleNetworkPartitio_down(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_NETWORK_PARTITION_DOWN
        _faultInjection = ebCluFaultInjection(self.mGetClubox(), _ebox_local._exaBoxCluCtrl__options)
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("/usr/sbin/ip a s stre0 | /bin/grep state", aRc=0, aStdout="7: stre0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 2300 qdisc mq state UP group default qlen 1000 ",  aPersist=True),
                    exaMockCommand("/usr/sbin/ip a s stre1 | /bin/grep state", aRc=0, aStdout="8: stre1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 2300 qdisc mq state UP group default qlen 1000 ",  aPersist=True)
                ],
                [
                    exaMockCommand("/usr/sbin/ip link set stre0 down", aRc=0, aStdout="",  aPersist=True),
                    exaMockCommand("/usr/sbin/ip link set stre1 down", aRc=0, aStdout="",  aPersist=True)
                ],
                [
                    exaMockCommand("/usr/sbin/ip a s stre0 | /bin/grep state", aRc=0, aStdout="7: stre0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 2300 qdisc mq state UP group default qlen 1000 ",  aPersist=True),
                    exaMockCommand("/usr/sbin/ip a s stre1 | /bin/grep state", aRc=0, aStdout="8: stre1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 2300 qdisc mq state UP group default qlen 1000 ",  aPersist=True)
                ],
                [
                    exaMockCommand("/usr/sbin/ip link set stre0 down", aRc=0, aStdout="",  aPersist=True),
                    exaMockCommand("/usr/sbin/ip link set stre1 down", aRc=0, aStdout="",  aPersist=True)
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _faultInjection.mHandleRequest()
        
    def test_mHandleNetworkPartitio_up(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_NETWORK_PARTITION_UP
        _faultInjection = ebCluFaultInjection(self.mGetClubox(), _ebox_local._exaBoxCluCtrl__options)
        _cmds = {
                    self.mGetRegexCell(): [
                [
                    exaMockCommand("/usr/sbin/ip a s stre0 | /bin/grep state", aRc=0, aStdout="7: stre0: <BROADCAST,MULTICAST> mtu 2300 qdisc mq state DOWN group default qlen 1000 ",  aPersist=True),
                    exaMockCommand("/usr/sbin/ip a s stre1 | /bin/grep state", aRc=0, aStdout="7: stre1: <BROADCAST,MULTICAST> mtu 2300 qdisc mq state DOWN group default qlen 1000 ",  aPersist=True)
                ],
                [
                    exaMockCommand("/usr/sbin/ip a s stre1 | /bin/grep state", aRc=0, aStdout="8: stre1: <BROADCAST,MULTICAST,DOWN,LOWER_UP> mtu 2300 qdisc mq state DOWN group default qlen 1000 ",  aPersist=True),
                    exaMockCommand("/usr/sbin/ip link set stre0 up", aRc=0, aStdout="",  aPersist=True),
                    exaMockCommand("/usr/sbin/ip link set stre1 up", aRc=0, aStdout="",  aPersist=True)
                ],
                [
                    exaMockCommand("/usr/sbin/ip a s stre0 | /bin/grep state", aRc=0, aStdout="7: stre0: <BROADCAST,MULTICAST> mtu 2300 qdisc mq state DOWN group default qlen 1000",  aPersist=True),
                    exaMockCommand("/usr/sbin/ip a s stre1 | /bin/grep state", aRc=0, aStdout="8: stre1: <BROADCAST,MULTICAST> mtu 2300 qdisc mq state DOWN group default qlen 1000",  aPersist=True)
                ],
                [
                    exaMockCommand("/usr/sbin/ip link set stre0 up", aRc=0, aStdout="",  aPersist=True),
                    exaMockCommand("/usr/sbin/ip link set stre1 up", aRc=0, aStdout="",  aPersist=True)
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _faultInjection.mHandleRequest()
           

class ebTestMigrateUsersUtil(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestMigrateUsersUtil, self).setUpClass(True, True)
        warnings.filterwarnings("ignore")
        self.__testHostname = "test.hostname.us.oracle.com"

    @patch('exabox.ovm.clumisc.ebMigrateUsersUtil._is_esnp_running', return_value=True)
    def test_mFailHandleUserRegroupESNPRunning(self, aIsEsnpRunningMock):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _migrateUsers = ebMigrateUsersUtil(_ebox_local)
        with patch('exabox.core.Node.exaBoxNode') as _node:
            _mockNode = _node.return_value
            _toRemap = _migrateUsers.mGetRequiredRemapping(self.__testHostname, _mockNode)
            self.assertEqual(_toRemap, None)
    
    @patch('exabox.ovm.clumisc.ebMigrateUsersUtil._is_esnp_running', return_value=False)
    @patch('exabox.ovm.clumisc.ebMigrateUsersUtil._is_dbmcli_running', return_value=False)
    def test_mFailHandleUserRegroupDBMCLIDown(self, aIsDbmcliRunning, aIsEsnpRunningMock):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _migrateUsers = ebMigrateUsersUtil(self.mGetClubox())
        with patch('exabox.core.Node.exaBoxNode') as _node:
            _mockNode = _node.return_value
            self.assertRaises(ExacloudRuntimeError, _migrateUsers.mGetRequiredRemapping, self.__testHostname, _mockNode)

    def test_mHandleUserRegroup(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _migrateUsers = ebMigrateUsersUtil(self.mGetClubox())
        with patch('exabox.core.Node.exaBoxNode') as _node:
            _mockNode = _node.return_value
            _toRemap = _migrateUsers.mGetUsersGroupsToRemap(_mockNode)
            self.assertEqual(_toRemap, {})

    @patch('exabox.ovm.clumisc.ebMigrateUsersUtil.mGetUidFromFile', return_value=USER_GROUPS_REMAPPING)
    @patch('exabox.ovm.clumisc.ebMigrateUsersUtil.mGetRequiredRemapping', return_value=USER_GROUPS_REMAPPING)
    @patch('exabox.ovm.clumisc.ebMigrateUsersUtil.mExecuteNodeRemap', return_value=None)
    def test_mExecuteRemapSingle(self, aMockNodeRemap, aMockRemapping, aMockFileContent):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        get_gcontext().mSetConfigOption("force_manual_uidmove", "False")
        _migrateUsers = ebMigrateUsersUtil(_ebox_local)

        _host = self.mGetClubox().mReturnDom0DomUPair()[1][0]
        _mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/cat /etc/group | /bin/grep *", aRc=0, aPersist=True),
                    exaMockCommand("/usr/sbin/groupadd -g *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /etc/shadow | /bin/grep *", aRc=0, aPersist=True),
                    exaMockCommand("/usr/sbin/useradd -u *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/echo *", aRc=0, aPersist=True),
                    exaMockCommand("/opt/oracle.SupportTools/migrate_ids.sh --gid-file *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/rm *", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/groupmod -g *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/find / -gid *", aRc=0, aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_mockCommands)
        _migrateUsers.mExecuteRemapSingle(_host, aGrabLock=True)


    def test_mGetGridListSupportedByOeda_present(self):
        _oeda_path  = self.mGetClubox().mGetOedaPath()
        _oedacli_bin = os.path.join(_oeda_path, 'oedacli')
        grid_list = """ GI Versions for x10m
        19.25.0.0.241015, 19.24.0.0.240716, 19.23.0.0.240416, 19.22.0.0.240116, 19.21.0.0.231017, 19.20.0.0.230718, 19.19.0.0.230418, 19.18.0.0.230117, 19.17.0.0.221018, 19.16.0.0.220719, 19.15.0.0.220419
        21.16.0.0.241015, 21.15.0.0.240716, 21.14.0.0.240416, 21.13.0.0.240116, 21.12.0.0.231017, 21.11.0.0.230718, 21.10.0.0.230418, 21.9.0.0.230117, 21.8.0.0.221018, 21.7.0.0.220719, 21.6.0.0.220419
        23.6.0.24.10, 23.5.0.24.07
        Recommended GI version: 23.6.0.24.10
        """
        _cmds = {
            self.mGetRegexLocal():
                [
                    [
                        exaMockCommand(f'{_oedacli_bin} -e "list softwareversions grid"', aRc=0, aStdout=grid_list, aPersist=True)
                    ]
                ]
            }
        self.mPrepareMockCommands(_cmds)
        _status = mGetGridListSupportedByOeda(self.mGetClubox(), "19.25.0.0.240315")
        self.assertEqual(True, _status)
        
    def test_mGetGridListSupportedByOeda_missing(self):
        _oeda_path  = self.mGetClubox().mGetOedaPath()
        _oedacli_bin = os.path.join(_oeda_path, 'oedacli')
        grid_list = """ GI Versions for x10m
        19.25.0.0.241015, 19.24.0.0.240716, 19.23.0.0.240416, 19.22.0.0.240116, 19.21.0.0.231017, 19.20.0.0.230718, 19.19.0.0.230418, 19.18.0.0.230117, 19.17.0.0.221018, 19.16.0.0.220719, 19.15.0.0.220419
        21.16.0.0.241015, 21.15.0.0.240716, 21.14.0.0.240416, 21.13.0.0.240116, 21.12.0.0.231017, 21.11.0.0.230718, 21.10.0.0.230418, 21.9.0.0.230117, 21.8.0.0.221018, 21.7.0.0.220719, 21.6.0.0.220419
        23.6.0.24.10, 23.5.0.24.07
        Recommended GI version: 23.6.0.24.10
        """
        _cmds = {
            self.mGetRegexLocal():
                [
                    [
                        exaMockCommand(f'{_oedacli_bin} -e "list softwareversions grid"', aRc=0, aStdout=grid_list, aPersist=True),
                    ]
                ]
            }
        self.mPrepareMockCommands(_cmds)
        _status = mGetGridListSupportedByOeda(self.mGetClubox(), "23.7.0.0.240315")
        self.assertEqual(False, _status)

    @patch('exabox.ovm.clucontrol.exaBoxNode.mSetUser', return_value="admin")
    @patch('exabox.ovm.clumisc.ebCluSshSetup.mConnectandExecuteonCiscoSwitches', return_value="")
    def test_mConnectandExecuteonCiscoSwitches(self, mock_mSetUser, mock_mConnectandExecuteonCiscoSwitches):
        aNode = self.mGetClubox().mReturnDom0DomUPair()[1][0]
        aUser = "admin"
        aSwitch = "scaqau08sw-adm0.us.oracle.com"
        _pubKeyContent = "testkeycontent"
        _cmds = []
        _cmds.append(['#', 'configure terminal'])
        _cmds.append(['#', 'username switchexa role network-admin'])
        _cmds.append(['#', 'username switchexa sshkey {0}'.format(_pubKeyContent)])
        _cmds.append(['#', 'copy running-config startup-config'])
        _cmds.append(['#', 'exit']) # exit configure terminal
        _cmds.append(['#', 'exit']) # exit ssh connection

        mockCommands = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand(_cmds, aRc=0, aStdout="", aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _node = exaBoxNode(get_gcontext())
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mConnectandExecuteonCiscoSwitches")
        ovmObject = ebCluSshSetup(self.mGetClubox())
        ovmObject.mConnectandExecuteonCiscoSwitches(aNode, aUser, aSwitch, _cmds)
        ebLogInfo("Unit test on mSetCiscoSwitchSSHPasswordless succeeded.")

    @patch('exabox.ovm.clucontrol.exaBoxNode.mSetUser', return_value="admin")
    @patch('exabox.ovm.clumisc.ebCluSshSetup.mConnectandExecuteonCiscoSwitches', return_value="")
    def test_mSetCiscoSwitchSSHPasswordless(self, mock_mSetUser, mock_mConnectandExecuteonCiscoSwitches):
        _node = exaBoxNode(get_gcontext())
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mSetCiscoSwitchSSHPasswordless")
        ovmObject = ebCluSshSetup(self.mGetClubox())
        ovmObject.mSetCiscoSwitchSSHPasswordless(False, True)
        ebLogInfo("Unit test on mSetCiscoSwitchSSHPasswordless succeeded.")


    def test_mGetAlertHistoryOptions(self):
        """
        Tests mGetAlertHistoryOptions method
        """
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetImageVersion', return_value="25.1.0.0.0.241025"):
            _cellcli_alerthistory_options = mGetAlertHistoryOptions(self.mGetClubox(), "iad207202exdcl01.iad200071qfab.adminiad2.oraclevcn.com")
            self.mGetContext().mSetConfigOption('cellcli_alerthistory_options', None)
            _cellcli_alerthistory_options = mGetAlertHistoryOptions(self.mGetClubox(), "iad207202exdcl01.iad200071qfab.adminiad2.oraclevcn.com")
            self.mGetContext().mSetConfigOption('cellcli_alerthistory_options', "--inline")
            _sanity_check = ebCluCellSanityTests(mMockPrecheck(self.mGetClubox()), aPrecheckConfig={}, aStep="ESTP_PREVM_CHECKS", aNodeInfo="iad207202exdcl01.iad200071qfab.adminiad2.oraclevcn.com")
            _sanity_check.mRemoteExecute = mRemoteExecute
            _sanity_check.mRunListAlertHistory()

class ebTestADBSUtil(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestADBSUtil, self).setUpClass(True, True)
        warnings.filterwarnings("ignore")

    def test_mGetSiteGroupInfoFromPayload(self):
        # Set ebox
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = SITE_GROUPS_JSON
        # Set mocks
        _ebox_local.mSetOptions(_options)
        # Retrieve json from mock payload
        _utility = ebADBSUtil(_ebox_local._exaBoxCluCtrl__options)
        _required_keys = {"ad", "building", "cloud_vendor", "region", "restricted", "site_group"}
        _retrieved_json = _utility.mGetSiteGroupInfoFromPayload()
        # Check that retrieved json contains at least all the required keys
        self.assertTrue(_required_keys.issubset(_retrieved_json.keys()))

    def test_mCreateSiteGroupConfigFile(self):
        # Set ebox
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = SITE_GROUPS_JSON
        # Set mocks
        _ebox_local.mSetOptions(_options)
        # Prepare commands
        _mockCommands = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/scp *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /var/opt/oracle/location.json", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/chown -fR oracle:oinstall *", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/chmod 400 *", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/cat *", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/scp *", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_mockCommands)
        # Get the exit code of the creation of the SG file
        _exit_code = mCreateADBSSiteGroupConfig(_ebox_local)
        self.assertEqual(0, _exit_code)

class TestSsh(ebTestClucontrol):

    @classmethod
    def setUpClass(cls):
        super(TestSsh, cls).setUpClass(True, True)
        warnings.filterwarnings("ignore")

    def setUp(self):
        ctrl = self.mGetClubox()
        self.ssh_env = ebCluSshSetup(ctrl)
        self.host = "sc1iad00dd01.us.oracle.com"
        self.remote_hosts = ["sc1iad00cl01.us.oracle.com", "sc1iad00cl02.us.oracle.com","sc1iad00cl03.us.oracle.com"]

    @patch("exabox.ovm.clumisc.ebCluSshSetup.mRemoveKeyFromHostsByComment", return_value=None)
    @patch("exabox.ovm.clumisc.ebCluSshSetup.mRemoveKeyFromHosts", return_value=None)
    @patch("exabox.ovm.clumisc.ebCluSshSetup.mRestoreSSHKey")
    def test_mCleanSSHPasswordless_restore_default(self, mock_restore, mock_remove, mock_remove_comment):
        self.ssh_env.mCleanSSHPasswordless(
            self.host, self.remote_hosts
        )
        mock_remove.assert_called_once()
        mock_remove_comment.assert_called_once()
        mock_restore.assert_called_once()

    @patch("exabox.ovm.clumisc.ebCluSshSetup.mRemoveKeyFromHostsByComment", return_value=None)
    @patch("exabox.ovm.clumisc.ebCluSshSetup.mRemoveKeyFromHosts", return_value=None)
    @patch("exabox.ovm.clumisc.ebCluSshSetup.mRestoreSSHKey")
    def test_mCleanSSHPasswordless_restoreFalse_default(self, mock_restore, mock_remove, mock_remove_comment):
        self.ssh_env.mCleanSSHPasswordless(
            self.host, self.remote_hosts, aSkipRestore=False
        )
        mock_remove.assert_called_once()
        mock_remove_comment.assert_called_once()
        mock_restore.assert_called_once()

    @patch("exabox.ovm.clumisc.ebCluSshSetup.mRemoveKeyFromHostsByComment", return_value=None)
    @patch("exabox.ovm.clumisc.ebCluSshSetup.mRemoveKeyFromHosts", return_value=None)
    @patch("exabox.ovm.clumisc.ebCluSshSetup.mRestoreSSHKey")
    def test_mCleanSSHPasswordless_skip_restoreTrue(self, mock_restore, mock_remove, mock_remove_comment):
        self.ssh_env.mCleanSSHPasswordless(
            self.host, self.remote_hosts, aSkipRestore=True
        )
        mock_remove.assert_called_once()
        mock_remove_comment.assert_called_once()
        mock_restore.assert_not_called()

class ebTestCluEthernetConfig(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCluEthernetConfig, self).setUpClass(True, True)
        warnings.filterwarnings("ignore")
    
    @patch('exabox.utils.node.exaBoxNode.mConnect')
    @patch('exabox.ovm.clumisc.ebCluEthernetConfig.mGetCurrentSpeed', return_value=10000)
    def test_mSetCustomSpeed(self, aMockNode, aMockGetCurrentSpeed):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ethernetConfig = ebCluEthernetConfig(_ebox_local, _ebox_local._exaBoxCluCtrl__options)
        _host = self.mGetClubox().mReturnDom0DomUPair()[1][0]
        _ethx = "eth9"
        _curr_speed = 25000
        _opt_speed = 10000
        _exadata_model = "X9"
        aMockNode.mGetCmdExitStatus.return_value = 0

        _mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/usr/sbin/ethtool -s {_ethx} speed {_opt_speed} autoneg on", aRc=0, aPersist=True),
                    exaMockCommand(f"/bin/cat /sys/class/net/{_ethx}/speed", aStdout=[str(_opt_speed)], aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_mockCommands)

        _rc = _ethernetConfig.mSetCustomSpeed(aMockNode, _ethx, _curr_speed, _opt_speed, _exadata_model)
        self.assertEqual(_rc, 0)
    
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetExadataCellModel")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetCmd")
    def test_mCellTasks(self, mock_getCellModel, mock_getCmd):
        _cmds = {
            self.mGetRegexCell():
            [
                [
                    exaMockCommand("/usr/sbin/sshd -T | grep  -i maxstartups | cut -d ' ' -f 2 |  cut -d ':' -f 1", aRc=0, aStdout="100", aPersist=True),
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e list griddisk | /bin/grep 'CATALOG'", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("sed -i'.backup_by_exacloud' '/MaxStartups/d; ${p;s/.*/MaxStartups 100/}' /etc/ssh/sshd_config", aRc=0, aStdout="", aPersist=True),
                    
                ],
                [
                    exaMockCommand("/usr/sbin/sshd -T | grep  -i maxstartups | cut -d ' ' -f 2 |  cut -d ':' -f 1", aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e list griddisk | /bin/grep 'CATALOG'", aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("sed -i'.backup_by_exacloud'*", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("service sshd restart", aRc=0, aStdout="", aPersist=True),
                ]
                
            ]
        }
        self.mPrepareMockCommands(_cmds)
        mock_getCmd.return_value = "resizecpus"
        mock_getCellModel.return_value = 'X8'
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _obCellTasks = ebCluCellValidate(self.mGetClubox(),_options)
        _obCellTasks.mCellTasks(_options)
        
class TestEthernetSpeed(ebTestClucontrol):
    @classmethod
    def setUpClass(cls):
        super(TestEthernetSpeed, cls).setUpClass()

    def setUp(self):
        self._ebox_local = self.mGetClubox()
        self.eth_config = ebCluEthernetConfig(self._ebox_local, aOptions={})

    @patch("exabox.ovm.clumisc.ebCluEthernetConfig.mGetCurrentSpeed")
    def test_mSetCustomSpeed_unknown_speed(self, mock_get_speed):
        _node = Mock()
        _node.mGetHostname.return_value = "sc1iad00dd01.us.oracle.com"
        _node.mGetCmdExitStatus.return_value = 0
        _node.mDisconnect.return_value = None
        mock_get_speed.return_value = -1
        self.eth_config.__cluctrl = Mock()
        self.eth_config.__cluctrl.mEnvTarget.return_value = True
        _mockCommands = {
            ".*": [[
                exaMockCommand("/usr/sbin/ethtool eth10", aRc=0, aStdout="Speed: -1\n", aPersist=True),
                exaMockCommand("/usr/sbin/ethtool -s eth10 speed 25000 autoneg on",aRc=0, aPersist=True),
                exaMockCommand("/usr/sbin/ethtool eth10", aRc=0, aStdout="Speed: -1\n", aPersist=True),
            ]]
        }

        self.mPrepareMockCommands(_mockCommands)
        with patch("time.sleep", return_value=None):
            rc = self.eth_config.mSetCustomSpeed(
                aNode=_node,
                aEthx="eth10",
                aCurrSpeed=-1,
                aOptSpeed=25000,
                aExadataModel="X11"
            )

        self.assertEqual(rc, -1)
        _node.mExecuteCmd.assert_called_once_with("/usr/sbin/ethtool -s eth10 speed 25000 autoneg on")

if __name__ == "__main__":
    unittest.main()
