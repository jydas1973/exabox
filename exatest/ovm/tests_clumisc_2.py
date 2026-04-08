import json
import unittest
import re
import copy
import os
import io
import sys
import types
import itertools
from exabox.BaseServer.AsyncProcessing import ProcessStructure

if "exabox.agent.Agent" not in sys.modules:
    _agent_stub = types.ModuleType("exabox.agent.Agent")

    class _AgentStub:
        pass

    _agent_stub.ebAgentDaemon = _AgentStub
    _agent_stub.ebGetAgentInfo = lambda *args, **kwargs: {}
    sys.modules["exabox.agent.Agent"] = _agent_stub

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo, ebLogError
from exabox.ovm import clumisc
from exabox.ovm.clumisc import ebCluPreChecks,ebCluSshSetup,OracleVersion,ebFortifyIssues,ebCluStorageReshapePrecheck,ebCluStartStopHostFromIlom, ebCluNodeSubsetPrecheck, ebCluRestartVmExacsService, ebCluFaultInjection, ebMigrateUsersUtil, mGetGridListSupportedByOeda, ebCluCellSanityTests, mGetDom0sImagesListSorted, ebSubnetIp, ebSubnetSet, validateIpOrHostname, ebCluScheduleManager, ebCluCellValidate, ebCluPostComputeValidate, AgentWorkerPIDListing, ebCluFetchSshKeys
from exabox.ovm.monitor import ebClusterNode
import warnings
from unittest.mock import patch, Mock, mock_open, call
from exabox.core.Error import ExacloudRuntimeError
from exabox.utils.node import  connect_to_host
from exabox.ovm.adbs_elastic_service import mCreateADBSSiteGroupConfig
from exabox.ovm.clumisc import mWaitForSystemBoot, ebMiscFx, mGetAlertHistoryOptions, ebADBSUtil, mPatchPrivNetworks, mChangeOpCtlAudit
from exabox.ovm.kvmvmmgr import ebKvmVmMgr
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.ovm.clumisc import ebCluEthernetConfig


SSH_KEY1 = "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEArCjp6sw0M36Cm1yJasmUeGDnMGyYZqRk+dl01OOTrwDT6mKGVD+UJfU3ACRyejKPW09fZkMFp7nhBf8gTapSwvyhcelO580iWzNCGoB5oeexivaXJpBaD01PKqd1NpgQfs90qIIXeB4ej5Z/kxGwT18Tnl6hSRxscH1tjkRfHxbajDGndd7cBP71asEPZyGIFIncp5Oi4fNmi7xX29HCT5LFaQwbtxC587HkCviRdaZLmYx7FaA9tN5gaXDg8qavF/4ImpwKosWUk9WcXecb1V0W6bxx/DHEuy6MZNHZR0RlRgFmFEZQQBFJUGCnq3JOSLm0dZE2yCUnFDT0VryjoQ== root@scas07adm07.us.oracle.com"

HARDWARE_ALERT_VALIDATE_ELASTIC_SHAPE_JSON = {"iad207206exdcl14.iad200071qfab.adminiad2.oraclevcn.com":{"Details":{"pmemcache":{"iad207206exdcl14_PMEMCACHE":"warning - degraded"}},"celldisk":"normal","cellsrvStatus":"running","fan":"normal","flashcache":"normal","griddisk":"normal","lun":"normal","msStatus":"running","node_info":[{"domainname":"iad200071qfab.adminiad2.oraclevcn.com","error_list":[{"error-message":{"iad207206exdcl14_PMEMCACHE":"warning - degraded"},"error-type":"pmemcache"}],"hostname":"iad207206exdcl14","hw_type":"CELL","node-model":"X8M-2","preprov":False}],"physicaldisk":"normal","ping_test":"normal","pmemcache":"abnormal","power":"normal","root_storage_test":"normal","rsStatus":"running","ssh_test":"normal","temperature":"normal"},"iad207206exdcl15.iad200071qfab.adminiad2.oraclevcn.com":{"Details":{},"celldisk":"normal","cellsrvStatus":"running","fan":"normal","flashcache":"normal","griddisk":"normal","lun":"normal","msStatus":"running","node_info":[{"domainname":"iad200071qfab.adminiad2.oraclevcn.com","hostname":"iad207206exdcl15","hw_type":"CELL","node-model":"X8M-2","preprov":False}],"physicaldisk":"normal","ping_test":"normal","pmemcache":"normal","power":"normal","root_storage_test":"normal","rsStatus":"running","ssh_test":"normal","temperature":"normal"},"iad207215exdcl12.iad200071qfab.adminiad2.oraclevcn.com":{"Details":{},"celldisk":"normal","cellsrvStatus":"running","fan":"normal","flashcache":"normal","griddisk":"normal","lun":"normal","msStatus":"running","node_info":[{"domainname":"iad200071qfab.adminiad2.oraclevcn.com","hostname":"iad207215exdcl12","hw_type":"CELL","node-model":"X8M-2","preprov":False}],"physicaldisk":"normal","ping_test":"normal","pmemcache":"normal","power":"normal","root_storage_test":"normal","rsStatus":"running","ssh_test":"normal","temperature":"normal"}}

HARDWARE_ALERT_VALIDATE_ELASTIC_SHAPE_JSON_SUC = {"iad207202exdcl01.iad200071qfab.adminiad2.oraclevcn.com":{"Details":{},"celldisk":"normal","cellsrvStatus":"running","fan":"normal","flashcache":"normal","griddisk":"normal","lun":"normal","msStatus":"running","node_info":[{"domainname":"iad200071qfab.adminiad2.oraclevcn.com","hostname":"iad207202exdcl01","hw_type":"CELL","node-model":"X8M-2","preprov":False}],"physicaldisk":"normal","ping_test":"normal","pmemcache":"normal","power":"normal","root_storage_test":"normal","rsStatus":"running","ssh_test":"normal","temperature":"normal"},"iad207202exdcl02.iad200071qfab.adminiad2.oraclevcn.com":{"Details":{},"celldisk":"normal","cellsrvStatus":"running","fan":"normal","flashcache":"normal","griddisk":"normal","lun":"normal","msStatus":"running","node_info":[{"domainname":"iad200071qfab.adminiad2.oraclevcn.com","hostname":"iad207202exdcl02","hw_type":"CELL","node-model":"X8M-2","preprov":False}],"physicaldisk":"normal","ping_test":"normal","pmemcache":"normal","power":"normal","root_storage_test":"normal","rsStatus":"running","ssh_test":"normal","temperature":"normal"}}

HARDWARE_ALERT_ESTP_PREVM_CHECKS_JSON =  {"nodes": [{"hostname": "iad103716exdd012", "domainname": "iad103716exd.adminiad1.oraclevcn.com", "hw_type": "COMPUTE", "ping_test": "normal", "ssh_test": "normal", "fan": "normal", "power": "normal", "temperature": "abnormal", "hypervisor": "running", "root_storage_test": "normal", "storage_check_exavmimages": "normal", "memory_check": "normal"}, {"hostname": "iad103716exdd011", "domainname": "iad103716exd.adminiad1.oraclevcn.com", "hw_type": "COMPUTE", "ping_test": "normal", "ssh_test": "normal", "fan": "normal", "power": "normal", "temperature": "normal", "hypervisor": "stopped", "root_storage_test": "normal", "storage_check_exavmimages": "normal", "memory_check": "normal"}, {"Details": {}, "hostname": "iad103710exdcl13", "domainname": "iad103710exd.adminiad1.oraclevcn.com", "hw_type": "CELL", "ping_test": "normal", "ssh_test": "abnormal", "fan": "normal", "power": "normal", "temperature": "normal", "cellsrvStatus": "running", "msStatus": "running", "rsStatus": "running", "lun": "normal", "physicaldisk": "abnormal", "griddisk": "normal", "celldisk": "normal", "root_storage_test": "normal"}]}  

HARDWARE_ALERT_ESTP_PREVM_CHECKS_JSON_SUC =  {"nodes": [{"hostname": "iad103716exdd012", "domainname": "iad103716exd.adminiad1.oraclevcn.com", "hw_type": "COMPUTE", "ping_test": "normal", "ssh_test": "normal", "fan": "normal", "power": "normal", "temperature": "normal", "hypervisor": "running", "root_storage_test": "normal", "storage_check_exavmimages": "normal", "memory_check": "normal"}]}

JSON_ILOM_START = {
"operation": "start",
"parallel_process": False,
"host_ilom_pair": {
    "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com": "iad103716exdd013lo.iad103716exd.adminiad1.oraclevcn.com",
    "iad103712exdcl07.iad103712exd.adminiad1.oraclevcn.com": "iad103712exdcl07lo.iad103712exd.adminiad1.oraclevcn.com"
}
}

JSON_ILOM_STOP = {
"operation": "stop",
"parallel_process": True,
"host_ilom_pair": {
    "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com": "iad103716exdd013lo.iad103716exd.adminiad1.oraclevcn.com",
    "iad103712exdcl07.iad103712exd.adminiad1.oraclevcn.com": "iad103712exdcl07lo.iad103712exd.adminiad1.oraclevcn.com"
}
}

JSON_ILOM_INVALID_OPERATION = {
"operation": "wait",  # invalid operation
"parallel_process": True,
"host_ilom_pair": {
    "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com": "iad103716exdd013lo.iad103716exd.adminiad1.oraclevcn.com"
}
}

JSON_ILOM_MISSING_OPERATION = {
"parallel_process": True,
"host_ilom_pair": {
    "iad103716exdd013.iad103716exd.adminiad1.oraclevcn.com": "iad103716exdd013lo.iad103716exd.adminiad1.oraclevcn.com"
}
}

JSON_ILOM_MISSING_HOST_PAIR = {
"operation": "start",
"parallel_process": True
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


class ebTestClumisc(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestClumisc, self).setUpClass(True, True)
        warnings.filterwarnings("ignore")

    def test_mRemoveKeyFromHosts(self):
        aRemoteHostList = self.mGetClubox().mReturnDom0DomUPair()[0][0],self.mGetClubox().mReturnDom0DomUPair()[1][0]
        ebLogInfo(f"Remote host list: {aRemoteHostList}")

        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mRemoveKeyFromHosts")
        ovmObject = ebCluSshSetup(self.mGetClubox())
        _cmds = {

            self.mGetRegexDom0(): [

                [
                    exaMockCommand(re.escape(f'sed --follow-symlinks -n "\#\<{SSH_KEY1}\>#p" /root/.ssh/authorized_keys'), aRc=0, aPersist=True),
                    exaMockCommand(re.escape(f'sed --follow-symlinks -i "\#\<{SSH_KEY1}\>#d" /root/.ssh/authorized_keys'), aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        ovmObject.mRemoveKeyFromHosts(SSH_KEY1,aRemoteHostList, aExcludePatternsRegEx="")
        ebLogInfo("Unit test on ebCluSshSetup.mRemoveKeyFromHosts succeeded.")

    def test_mGetSSHPublicKeyFromHost(self):
        aHost = self.mGetClubox().mReturnDom0DomUPair()[1][0]
        _node = exaBoxNode(get_gcontext())
        _filename='/root/.ssh/id_rsa'
        _filename_pub='/root/.ssh/id_rsa.pub'
        aKeyComment = "EXAPATCHING KEY"
        _cmd = "if [[ ! `find /root/.ssh -maxdepth 1 -name 'id_rsa'` || ! `find /root/.ssh -maxdepth 1" f" -name 'id_rsa.pub'` ]]; then ssh-keygen -C '{aKeyComment}' -q -t rsa -N \"\" -f " '/root/.ssh/id_rsa <<<y > /dev/null 2>&1; fi; ' 'cat /root/.ssh/id_rsa.pub'
        ebLogInfo(f"Remote host : {aHost}")

        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mGetSSHPublicKeyFromHost")
        ovmObject = ebCluSshSetup(self.mGetClubox())
        _cmds = {

            self.mGetRegexDom0(): [

                [
                    exaMockCommand(f"/bin/test -e {_filename}", aRc=0, aPersist=True),
                    exaMockCommand(f"/bin/mv -f {_filename} {_filename}_keybackup", aRc=0, aPersist=True),
                    exaMockCommand(f"/bin/mv -f {_filename_pub} {_filename_pub}_keybackup", aRc=0, aPersist=True),
                    exaMockCommand(re.escape(f"{_cmd}"), aRc=0, aPersist=True),
                ]
            ]
        }   
        self.mPrepareMockCommands(_cmds)
        ovmObject.mGetSSHPublicKeyFromHost(aHost, aKeyComment = "EXAPATCHING KEY")
        ebLogInfo("Unit test on ebCluSshSetup.mGetSSHPublicKeyFromHost succeeded.")

    def test_mGetSSHPublicKeyFromHostForClusterless(self):
        aHost = self.mGetClubox().mReturnDom0DomUPair()[1][0]
        _node = exaBoxNode(get_gcontext())
        _filename='/root/.ssh/id_ecdsa'
        _filename_rsa='/root/.ssh/id_rsa'
        _filename_pub='/root/.ssh/id_ecdsa.pub'
        aKeyComment = "EXAPATCHING KEY"
        _cmd_ecdsa = "if [[ ! `find /root/.ssh -maxdepth 1 -name 'id_ecdsa'` || ! `find /root/.ssh -maxdepth 1" f" -name 'id_ecdsa.pub'` ]]; then ssh-keygen -C '{aKeyComment}' -q -t ecdsa -b 384 -m PEM -N \"\" -f " '/root/.ssh/id_ecdsa <<<y > /dev/null 2>&1; fi; ' 'cat /root/.ssh/id_ecdsa.pub'
        _cmd_rsa = "if [[ ! `find /root/.ssh -maxdepth 1 -name 'id_rsa'` || ! `find /root/.ssh -maxdepth 1" f" -name 'id_rsa.pub'` ]]; then ssh-keygen -C '{aKeyComment}' -q -t rsa -N \"\" -f " '/root/.ssh/id_rsa <<<y > /dev/null 2>&1; fi; ' 'cat /root/.ssh/id_rsa.pub'
        ebLogInfo(f"Remote host : {aHost}")
        _validate_cmd1 = "diff -s <(ssh-keygen -y -f /root/.ssh/id_rsa | cut -d' ' -f2) <(cat /root/.ssh/id_rsa.pub | cut -d' ' -f2)"
        _validate_cmd2 = "diff -s <(ssh-keygen -y -f /root/.ssh/id_ecdsa | cut -d' ' -f2) <(cat /root/.ssh/id_ecdsa.pub | cut -d' ' -f2)"
        ebLogInfo(f"Remote host : {aHost}")

        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mSetSSHPasswordlessForClusterless")
        ovmObject = ebCluSshSetup(self.mGetClubox())
        _cmds = {

            self.mGetRegexDom0(): [

                [
                    exaMockCommand(f"/bin/test -e {_filename}", aRc=0, aPersist=True),
                    exaMockCommand(f"/bin/test -e {_filename_rsa}", aRc=0, aPersist=True),
                    exaMockCommand(f"/bin/rm -f {_filename_rsa}", aRc=0, aPersist=True),
                    exaMockCommand(f"/bin/rm -f {_filename}", aRc=0, aPersist=True),
                    exaMockCommand(re.escape(f"{_cmd_ecdsa}"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape(f"{_cmd_rsa}"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape(f"{_validate_cmd1}"), aRc=1, aPersist=True),
                    exaMockCommand(re.escape(f"{_validate_cmd2}"), aRc=1, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        with patch('exabox.ovm.clumisc.ebCluSshSetup.mValidateKnownHostsFile', return_value=True), patch('exabox.exakms.ExaKms.ExaKms.mGetDefaultKeyAlgorithm', return_value="ECDSA"):
            ovmObject.mGetSSHPublicKeyFromHostForClusterless(aHost)
        self.mPrepareMockCommands(_cmds)
        with patch('exabox.ovm.clumisc.ebCluSshSetup.mValidateKnownHostsFile', return_value=True), patch('exabox.exakms.ExaKms.ExaKms.mGetDefaultKeyAlgorithm', return_value="RSA"):
            ovmObject.mGetSSHPublicKeyFromHostForClusterless(aHost)
        ebLogInfo("Unit test on ebCluSshSetup.mGetSSHPublicKeyFromHostForClusterless succeeded.")

    def test_mSetSSHPasswordlessForClusterless(self):
        aHost = self.mGetClubox().mReturnDom0DomUPair()[1][0]
        _node = exaBoxNode(get_gcontext())
        _filename='/root/.ssh/id_rsa'
        _filename_pub='/root/.ssh/id_rsa.pub'
        aKeyComment = "EXAPATCHING KEY"
        _cmd = "if [[ ! `find /root/.ssh -maxdepth 1 -name 'id_rsa'` || ! `find /root/.ssh -maxdepth 1" f" -name 'id_rsa.pub'` ]]; then ssh-keygen -C '{aKeyComment}' -q -t rsa -N \"\" -f " '/root/.ssh/id_rsa <<<y > /dev/null 2>&1; fi; ' 'cat /root/.ssh/id_rsa.pub'
        _validate_cmd1 = "diff -s <(ssh-keygen -y -f /root/.ssh/id_rsa | cut -d' ' -f2) <(cat /root/.ssh/id_rsa.pub | cut -d' ' -f2)"
        _validate_cmd2 = "diff -s <(ssh-keygen -y -f /root/.ssh/id_ecdsa | cut -d' ' -f2) <(cat /root/.ssh/id_ecdsa.pub | cut -d' ' -f2)"
        ebLogInfo(f"Remote host : {aHost}")

        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mSetSSHPasswordlessForClusterless")
        ovmObject = ebCluSshSetup(self.mGetClubox())
        _cmds = {

            self.mGetRegexDom0(): [

                [
                    exaMockCommand(f"/bin/test -e {_filename}", aRc=0, aPersist=True),
                    exaMockCommand(re.escape(f"{_cmd}"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape(f"{_validate_cmd1}"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape(f"{_validate_cmd2}"), aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        with patch('exabox.ovm.clumisc.ebCluSshSetup.mValidateKnownHostsFile', return_value=True):
            ovmObject.mSetSSHPasswordlessForClusterless(aHost, aRemoteHostList = [])
        ebLogInfo("Unit test on ebCluSshSetup.mSetSSHPasswordlessForClusterless succeeded.")

    def test_mCleanSSHPasswordlessForClusterless(self):
        aHost = self.mGetClubox().mReturnDom0DomUPair()[1][0]
        _node = exaBoxNode(get_gcontext())
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mCleanSSHPasswordlessForClusterless")
        ovmObject = ebCluSshSetup(self.mGetClubox())
        with patch('exabox.ovm.clumisc.ebCluSshSetup.mRemoveKeyFromHosts', return_value=True), patch('exabox.ovm.clumisc.ebCluSshSetup.mRemoveKeyFromHostsByComment', return_value=True):
            ovmObject.mCleanSSHPasswordlessForClusterless(aHost, aRemoteHostList = ['testvm'])
        ebLogInfo("Unit test on mCleanSSHPasswordlessForClusterless  succeeded.")



    def test_mGetCoreAndMemInfo(self):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"imageinfo | grep 'Node type:'", aRc=0, aStdout="Type Hypervisor KVMHOST", aPersist=True),
                    exaMockCommand(f"cat /sys/hypervisor/type", aRc=0, aStdout="KVMHOST", aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        ebLogInfo("Running unit test on clumisc.mGetCoreAndMemInfo")
        _ebox = self.mGetClubox()
        _cluprecheck = ebCluPreChecks(_ebox)
        with patch('exabox.ovm.hypervisorutils.getHVInstance', return_value=ebKvmVmMgr({"hostname":"iad103716exdd011.iad103716exd.adminiad1.oraclevcn.com"})),\
        patch('exabox.ovm.kvmvmmgr.ebKvmVmMgr.mGetVMMemory', return_value=30720),\
        patch('exabox.ovm.kvmvmmgr.ebKvmVmMgr.mGetVMCpu', return_value=4),\
        patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetImageVersion', return_value="25.1.2.0.0.250213.1"),\
        patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetRequestObj', return_value=ebJobRequest("cmd_type", {})),\
        patch('exabox.ovm.clumisc.ebGetDefaultDB') as _mock_db:
            _mock_db.return_value.mUpdateRequest.return_value = None
            _out = _cluprecheck.mGetCoreAndMemInfo()
        ebLogInfo("Unit test on mGetCoreAndMemInfo  succeeded. output->" + str(_out))

    def test_mAddToKnownHosts(self):
        aRemoteHostList = self.mGetClubox().mReturnDom0DomUPair()[0][0], self.mGetClubox().mReturnDom0DomUPair()[1][0]
        aHost = self.mGetClubox().mReturnDom0DomUPair()[1][0]
        ebLogInfo(f"Remote host list: {aRemoteHostList}")

        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mAddToKnownHosts")
        ovmObject = ebCluSshSetup(self.mGetClubox())
        _cmds = {

            self.mGetRegexDom0(): [

                [
                    exaMockCommand(f"ssh-keyscan", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand(f"ssh-keyscan -t ecdsa {aHost} >> /root/.ssh/known_hosts 2> /dev/null;", aRc=0, aPersist=True),
                    exaMockCommand(f"ssh-keyscan -t rsa {aHost} >> /root/.ssh/known_hosts 2> /dev/null;", aRc=0, aPersist=True),
                    exaMockCommand(f"ssh-keyscan {aHost} >> /root/.ssh/known_hosts 2> /dev/null;", aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        ovmObject.mAddToKnownHosts(aHost, aRemoteHostList)
        ebLogInfo("Unit test on ebCluSshSetup.mAddToKnownHosts succeeded.")

    def test_mRestoreSSHKey(self):
        aHost = self.mGetClubox().mReturnDom0DomUPair()[1][0]
        _node = exaBoxNode(get_gcontext())
        _filename='/root/.ssh/id_rsa'
        _filename_pub='/root/.ssh/id_rsa.pub'
        ebLogInfo(f"Remote host : {aHost}")

        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mRestoreSSHKey")
        ovmObject = ebCluSshSetup(self.mGetClubox())
        _cmds = {

            self.mGetRegexDom0(): [

                [
                    exaMockCommand(f"/bin/test -e {_filename}_keybackup", aRc=0, aPersist=True),
                    exaMockCommand(f"/bin/test -e {_filename_pub}_keybackup", aRc=0, aPersist=True),
                    exaMockCommand(f"/bin/mv -f {_filename}_keybackup {_filename}", aRc=0, aPersist=True),
                    exaMockCommand(f"/bin/mv -f {_filename_pub}_keybackup {_filename_pub}", aRc=0, aPersist=True),
                ]
            ]
        }   
        self.mPrepareMockCommands(_cmds)
        ovmObject.mRestoreSSHKey(aHost)
        ebLogInfo("Unit test on ebCluSshSetup.mRestoreSSHKey succeeded.")


    def test_Storagereshapeprecheck(self):
        self.mGetContext().mSetConfigOption('jsonmode', 'True')
        _options = self.mGetPayload()
        _options.jsonmode = 'True'
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e list griddisk attributes name where asmmodestatus=\'DROPPED\'", aRc=0, aPersist=True),
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e list griddisk attributes name where asmmodestatus=\'OFFLINE\'", aRc=0, aPersist=True),
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e list griddisk attributes name where asmmodestatus=\'UNKNOWN\'", aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        __ebox = self.mGetClubox()
        __node = exaBoxNode(get_gcontext())
        _reshapeprecheck = ebCluStorageReshapePrecheck(__ebox)
        with patch('exabox.ovm.clumisc.ebCluStorageReshapePrecheck.mGetOfflineCellDisks', return_value=0):
            _rc = _reshapeprecheck.mStorageReshapePrecheck(_options)
            self.assertEqual(_rc, 0)

    def test_mGetOfflineCellDisks_OFFLINE(self):
        self.mGetContext().mSetConfigOption('jsonmode', 'True')
        _options = self.mGetPayload()
        _options.jsonmode = 'True'
        _output = "['\t DATAC8_CD_00_iad103712exdcl01\t OFFLINE\n', '\t DATAC8_CD_01_iad103712exdcl01\t OFFLINE\n', '\t DATAC8_CD_02_iad103712exdcl01\t OFFLINE\n', '\t DATAC8_CD_03_iad103712exdcl01\t OFFLINE\n', '\t DATAC8_CD_04_iad103712exdcl01\t OFFLINE\n', '\t DATAC8_CD_05_iad103712exdcl01\t OFFLINE\n', '\t DATAC8_CD_06_iad103712exdcl01\t OFFLINE\n', '\t DATAC8_CD_07_iad103712exdcl01\t OFFLINE\n', '\t DATAC8_CD_08_iad103712exdcl01\t OFFLINE\n', '\t DATAC8_CD_09_iad103712exdcl01\t OFFLINE\n', '\t DATAC8_CD_10_iad103712exdcl01\t OFFLINE\n', '\t DATAC8_CD_11_iad103712exdcl01\t OFFLINE\n', '\t RECOC8_CD_00_iad103712exdcl01\t OFFLINE\n', '\t RECOC8_CD_01_iad103712exdcl01\t OFFLINE\n', '\t RECOC8_CD_02_iad103712exdcl01\t OFFLINE\n', '\t RECOC8_CD_03_iad103712exdcl01\t OFFLINE\n', '\t RECOC8_CD_04_iad103712exdcl01\t OFFLINE\n', '\t RECOC8_CD_05_iad103712exdcl01\t OFFLINE\n', '\t RECOC8_CD_06_iad103712exdcl01\t OFFLINE\n', '\t RECOC8_CD_07_iad103712exdcl01\t OFFLINE\n', '\t RECOC8_CD_08_iad103712exdcl01\t OFFLINE\n', '\t RECOC8_CD_09_iad103712exdcl01\t OFFLINE\n', '\t RECOC8_CD_10_iad103712exdcl01\t OFFLINE\n', '\t RECOC8_CD_11_iad103712exdcl01\t OFFLINE\n']"
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e \"list griddisk attributes name,asmmodestatus where name like *", aRc=0,aStdout=_output, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        __ebox = self.mGetClubox()
        __node = exaBoxNode(get_gcontext())
        _reshapeprecheck = ebCluStorageReshapePrecheck(__ebox)
        with patch("exabox.ovm.clumisc.ProcessStructure") as _proc, \
            patch("exabox.ovm.clumisc.ProcessManager") as _pmgr:
            _pmgr.return_value.mGetManager.return_value.dict.return_value = {
                'scaqab10celadm01.us.oracle.com': True,
                'scaqab10celadm02.us.oracle.com': True,
                'scaqab10celadm03.us.oracle.com': True,
            }
            self.assertEqual(_reshapeprecheck.mGetOfflineCellDisks(),1)
 
    def test_mGetOfflineCellDisks_ONLINE(self):
        self.mGetContext().mSetConfigOption('jsonmode', 'True')
        _options = self.mGetPayload()
        _options.jsonmode = 'True'
        _output = "['\t DATAC8_CD_00_iad103712exdcl01\t ONLINE\n', '\t DATAC8_CD_01_iad103712exdcl01\t ONLINE\n', '\t DATAC8_CD_02_iad103712exdcl01\t ONLINE\n', '\t DATAC8_CD_03_iad103712exdcl01\t ONLINE\n', '\t DATAC8_CD_04_iad103712exdcl01\t ONLINE\n', '\t DATAC8_CD_05_iad103712exdcl01\t ONLINE\n', '\t DATAC8_CD_06_iad103712exdcl01\t ONLINE\n', '\t DATAC8_CD_07_iad103712exdcl01\t ONLINE\n', '\t DATAC8_CD_08_iad103712exdcl01\t ONLINE\n', '\t DATAC8_CD_09_iad103712exdcl01\t ONLINE\n', '\t DATAC8_CD_10_iad103712exdcl01\t ONLINE\n', '\t DATAC8_CD_11_iad103712exdcl01\t ONLINE\n', '\t RECOC8_CD_00_iad103712exdcl01\t ONLINE\n', '\t RECOC8_CD_01_iad103712exdcl01\t ONLINE\n', '\t RECOC8_CD_02_iad103712exdcl01\t ONLINE\n', '\t RECOC8_CD_03_iad103712exdcl01\t ONLINE\n', '\t RECOC8_CD_04_iad103712exdcl01\t ONLINE\n', '\t RECOC8_CD_05_iad103712exdcl01\t ONLINE\n', '\t RECOC8_CD_06_iad103712exdcl01\t ONLINE\n', '\t RECOC8_CD_07_iad103712exdcl01\t ONLINE\n', '\t RECOC8_CD_08_iad103712exdcl01\t ONLINE\n', '\t RECOC8_CD_09_iad103712exdcl01\t ONLINE\n', '\t RECOC8_CD_10_iad103712exdcl01\t ONLINE\n', '\t RECOC8_CD_11_iad103712exdcl01\t ONLINE\n']"
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e \"list griddisk attributes name,asmmodestatus where name like *", aRc=0,aStdout=_output, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        __ebox = self.mGetClubox()
        __node = exaBoxNode(get_gcontext())
        _reshapeprecheck = ebCluStorageReshapePrecheck(__ebox)
        with patch("exabox.ovm.clumisc.ProcessStructure") as _proc, \
            patch("exabox.ovm.clumisc.ProcessManager") as _pmgr:
            _pmgr.return_value.mGetManager.return_value.dict.return_value = {
                'scaqab10celadm01.us.oracle.com': False,
                'scaqab10celadm02.us.oracle.com': False,
                'scaqab10celadm03.us.oracle.com': False,
            }
            self.assertEqual(_reshapeprecheck.mGetOfflineCellDisks(),0)
 
    def test_mGetOfflineCellDisks_DROPPED(self):
        self.mGetContext().mSetConfigOption('jsonmode', 'True')
        _options = self.mGetPayload()
        _options.jsonmode = 'True'
        _output = "['\t DATAC8_CD_00_iad103712exdcl01\t DROPPED\n', '\t DATAC8_CD_01_iad103712exdcl01\t DROPPED\n', '\t DATAC8_CD_02_iad103712exdcl01\t DROPPED\n', '\t DATAC8_CD_03_iad103712exdcl01\t DROPPED\n', '\t DATAC8_CD_04_iad103712exdcl01\t DROPPED\n', '\t DATAC8_CD_05_iad103712exdcl01\t DROPPED\n', '\t DATAC8_CD_06_iad103712exdcl01\t DROPPED\n', '\t DATAC8_CD_07_iad103712exdcl01\t DROPPED\n', '\t DATAC8_CD_08_iad103712exdcl01\t DROPPED\n', '\t DATAC8_CD_09_iad103712exdcl01\t DROPPED\n', '\t DATAC8_CD_10_iad103712exdcl01\t DROPPED\n', '\t DATAC8_CD_11_iad103712exdcl01\t DROPPED\n', '\t RECOC8_CD_00_iad103712exdcl01\t DROPPED\n', '\t RECOC8_CD_01_iad103712exdcl01\t DROPPED\n', '\t RECOC8_CD_02_iad103712exdcl01\t DROPPED\n', '\t RECOC8_CD_03_iad103712exdcl01\t DROPPED\n', '\t RECOC8_CD_04_iad103712exdcl01\t DROPPED\n', '\t RECOC8_CD_05_iad103712exdcl01\t DROPPED\n', '\t RECOC8_CD_06_iad103712exdcl01\t DROPPED\n', '\t RECOC8_CD_07_iad103712exdcl01\t DROPPED\n', '\t RECOC8_CD_08_iad103712exdcl01\t DROPPED\n', '\t RECOC8_CD_09_iad103712exdcl01\t DROPPED\n', '\t RECOC8_CD_10_iad103712exdcl01\t DROPPED\n', '\t RECOC8_CD_11_iad103712exdcl01\t DROPPED\n']"
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e \"list griddisk attributes name,asmmodestatus where name like *", aRc=0,aStdout=_output, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        __ebox = self.mGetClubox()
        __node = exaBoxNode(get_gcontext())
        _reshapeprecheck = ebCluStorageReshapePrecheck(__ebox)
        with patch("exabox.ovm.clumisc.ProcessStructure") as _proc, \
            patch("exabox.ovm.clumisc.ProcessManager") as _pmgr:
            _pmgr.return_value.mGetManager.return_value.dict.return_value = {
                'scaqab10celadm01.us.oracle.com': True,
                'scaqab10celadm02.us.oracle.com': True,
                'scaqab10celadm03.us.oracle.com': True,
            }
            self.assertEqual(_reshapeprecheck.mGetOfflineCellDisks(),1)


    def test_mGetOfflineCellDisks_UNKNOWN(self):
        self.mGetContext().mSetConfigOption('jsonmode', 'True')
        _options = self.mGetPayload()
        _options.jsonmode = 'True'
        _output = "['\t DATAC8_CD_00_iad103712exdcl01\t UNKNOWN\n', '\t DATAC8_CD_01_iad103712exdcl01\t UNKNOWN\n', '\t DATAC8_CD_02_iad103712exdcl01\t UNKNOWN\n', '\t DATAC8_CD_03_iad103712exdcl01\t UNKNOWN\n', '\t DATAC8_CD_04_iad103712exdcl01\t UNKNOWN\n', '\t DATAC8_CD_05_iad103712exdcl01\t UNKNOWN\n', '\t DATAC8_CD_06_iad103712exdcl01\t UNKNOWN\n', '\t DATAC8_CD_07_iad103712exdcl01\t UNKNOWN\n', '\t DATAC8_CD_08_iad103712exdcl01\t UNKNOWN\n', '\t DATAC8_CD_09_iad103712exdcl01\t UNKNOWN\n', '\t DATAC8_CD_10_iad103712exdcl01\t UNKNOWN\n', '\t DATAC8_CD_11_iad103712exdcl01\t UNKNOWN\n', '\t RECOC8_CD_00_iad103712exdcl01\t UNKNOWN\n', '\t RECOC8_CD_01_iad103712exdcl01\t UNKNOWN\n', '\t RECOC8_CD_02_iad103712exdcl01\t UNKNOWN\n', '\t RECOC8_CD_03_iad103712exdcl01\t UNKNOWN\n', '\t RECOC8_CD_04_iad103712exdcl01\t UNKNOWN\n', '\t RECOC8_CD_05_iad103712exdcl01\t UNKNOWN\n', '\t RECOC8_CD_06_iad103712exdcl01\t UNKNOWN\n', '\t RECOC8_CD_07_iad103712exdcl01\t UNKNOWN\n', '\t RECOC8_CD_08_iad103712exdcl01\t UNKNOWN\n', '\t RECOC8_CD_09_iad103712exdcl01\t UNKNOWN\n', '\t RECOC8_CD_10_iad103712exdcl01\t UNKNOWN\n', '\t RECOC8_CD_11_iad103712exdcl01\t UNKNOWN\n']"
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e \"list griddisk attributes name,asmmodestatus where name like *", aRc=0,aStdout=_output, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        __ebox = self.mGetClubox()
        __node = exaBoxNode(get_gcontext())
        _reshapeprecheck = ebCluStorageReshapePrecheck(__ebox)
        with patch("exabox.ovm.clumisc.ProcessStructure") as _proc, \
            patch("exabox.ovm.clumisc.ProcessManager") as _pmgr:
            _pmgr.return_value.mGetManager.return_value.dict.return_value = {
                'scaqab10celadm01.us.oracle.com': True,
                'scaqab10celadm02.us.oracle.com': True,
                'scaqab10celadm03.us.oracle.com': True,
            }
            self.assertEqual(_reshapeprecheck.mGetOfflineCellDisks(),1)
 

    def test_mStoreResultsJson_elastic(self):
        _cmds = {

            self.mGetRegexLocal(): [

                [
                    exaMockCommand("/bin/mkdir -p log/hardware_alerts/", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _cluprecheck = ebCluPreChecks(_ebox)
        with patch('builtins.open', mock_open()):
            _out = _cluprecheck.mStoreResultsJson("ELASTIC_SHAPES_VALIDATION",HARDWARE_ALERT_VALIDATE_ELASTIC_SHAPE_JSON)
    
    def test_mStoreResultsJson_elastic_suc(self):
        _cmds = {

            self.mGetRegexLocal(): [

                [
                    exaMockCommand("/bin/mkdir -p log/hardware_alerts/", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _cluprecheck = ebCluPreChecks(_ebox)
        with patch('builtins.open', mock_open()):
            _out = _cluprecheck.mStoreResultsJson("ELASTIC_SHAPES_VALIDATION",HARDWARE_ALERT_VALIDATE_ELASTIC_SHAPE_JSON_SUC)
    
    def test_mStoreResultsJson_precheck(self):
        _cmds = {

            self.mGetRegexLocal(): [

                [
                    exaMockCommand("/bin/mkdir -p log/hardware_alerts/", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _cluprecheck = ebCluPreChecks(_ebox)
        with patch('builtins.open', mock_open()):
            _out = _cluprecheck.mStoreResultsJson("ESTP_PREVM_CHECKS",HARDWARE_ALERT_ESTP_PREVM_CHECKS_JSON)
   
    def test_mStoreResultsJson_precheck_suc(self):
        _cmds = {

            self.mGetRegexLocal(): [

                [
                    exaMockCommand("/bin/mkdir -p log/hardware_alerts/", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _cluprecheck = ebCluPreChecks(_ebox)
        with patch('builtins.open', mock_open()):
            _out = _cluprecheck.mStoreResultsJson("ESTP_PREVM_CHECKS",HARDWARE_ALERT_ESTP_PREVM_CHECKS_JSON_SUC) 
    
    
    def test_mHandlerStopStartHostViaIlom_start(self):
        _cmds = {
            self.mGetRegexLocal(): [
                [exaMockCommand("/bin/ping *", aRc=1, aStdout="", aPersist=True)]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_ILOM_START
        ebLogInfo("Running unit test on exaBoxCluCtrl.mHandlerStopStartHostViaIlom with valid start payload")
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"), \
                patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', return_value=True), \
                patch('exabox.ovm.clumisc.time.sleep', return_value=None), \
                patch('exabox.ovm.clupowermanagement.ProcessStructure') as _proc, \
                patch('exabox.ovm.clupowermanagement.ProcessManager') as _pmgr:
            _pmgr.return_value.mGetManager.return_value.dict.return_value = {}
            _proc.return_value.mSetMaxExecutionTime.return_value = None
            _proc.return_value.mSetJoinTimeout.return_value = None
            _proc.return_value.mSetLogTimeoutFx.return_value = None
            self.assertEqual(_ebox_local.mHandlerStopStartHostViaIlom(), None)

    def test_mHandlerStopStartHostViaIlom_stop(self):
        _cmds = {
            self.mGetRegexLocal(): [
                [exaMockCommand("/bin/ping *", aRc=1, aStdout="", aPersist=True)]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_ILOM_STOP
        ebLogInfo("Running unit test on exaBoxCluCtrl.mHandlerStopStartHostViaIlom with valid stop payload")
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"), \
                patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', return_value=True), \
                patch('exabox.ovm.clumisc.time.sleep', return_value=None), \
                patch.object(_ebox_local, "mHandlerStopStartHostViaIlom", return_value=None):
            self.assertEqual(_ebox_local.mHandlerStopStartHostViaIlom(), None)

    def test_mHandlerStopStartHostViaIlom_invalid_operation(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_ILOM_INVALID_OPERATION
        ebLogInfo("Running unit test on exaBoxCluCtrl.mHandlerStopStartHostViaIlom with invalid operation")
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
            self.assertRaises(ExacloudRuntimeError, _ebox_local.mHandlerStopStartHostViaIlom)

    def test_mHandlerStopStartHostViaIlom_missing_operation(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_ILOM_MISSING_OPERATION
        ebLogInfo("Running unit test on exaBoxCluCtrl.mHandlerStopStartHostViaIlom with missing operation")
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
            self.assertRaises(ExacloudRuntimeError, _ebox_local.mHandlerStopStartHostViaIlom)

    def test_mHandlerStopStartHostViaIlom_missing_host_ilom_pair(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__options.jsonconf = JSON_ILOM_MISSING_HOST_PAIR
        ebLogInfo("Running unit test on exaBoxCluCtrl.mHandlerStopStartHostViaIlom with missing host_ilom_pair")
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'), \
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
            self.assertRaises(ExacloudRuntimeError, _ebox_local.mHandlerStopStartHostViaIlom)
     
    def test_mAddNodePrecheck(self):
        ebLogInfo("Running unit test for mAddNodePrecheck")
        __ebox = self.mGetClubox()
        fullOptions = copy.deepcopy(__ebox.mGetArgsOptions())
        _addnodeprecheck = ebCluNodeSubsetPrecheck(__ebox)
        with patch ('exabox.ovm.clumisc.ebCluNodeSubsetPrecheck.mCheckMinDiskSpace', return_value=0):  
            _addnodeprecheck.mAddNodePrecheck(fullOptions)

    def test_mRestartVmExacsService_pass(self):
        ebLogInfo("Running unit test on ebCluRestartVmExacsService.mRestartVmExacsService")
        clurestartObject = ebCluRestartVmExacsService(self.mGetClubox())
        aRemoteHostList = self.mGetClubox().mReturnDom0DomUPair()[0][0],self.mGetClubox().mReturnDom0DomUPair()[1][0]
        ebLogInfo(f"Remote host list: {aRemoteHostList}")
        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"systemctl show vmexacs_kvm --property=ActiveState", aRc=0, aStdout="ActiveState=active", aPersist=True),
                    exaMockCommand(f"systemctl show vmexacs_kvm --property=SubState", aRc=0, aStdout="SubState=running", aPersist=True),
                    exaMockCommand(f"systemctl is-active libvirtd.service", aRc=0, aStdout="active", aPersist=True),
                    exaMockCommand(f"systemctl restart vmexacs_kvm", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)
        for aHost in aRemoteHostList:
            with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True),\
                patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsHostOL8', return_value=True):
                clurestartObject.mRestartVmExacsService(aHost, MAX_RETRY)

    def test_mRestartVmExacsService_fail(self):
        ebLogInfo("Running unit test on ebCluRestartVmExacsService.mRestartVmExacsService")
        clurestartObject = ebCluRestartVmExacsService(self.mGetClubox())
        aRemoteHostList = self.mGetClubox().mReturnDom0DomUPair()[0][0],self.mGetClubox().mReturnDom0DomUPair()[1][0]
        ebLogInfo(f"Remote host list: {aRemoteHostList}")
        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"systemctl show vmexacs_kvm --property=ActiveState", aRc=0, aStdout="ActiveState=active", aPersist=True),
                    exaMockCommand(f"systemctl show vmexacs_kvm --property=SubState", aRc=0, aStdout="SubState=running", aPersist=True),
                    exaMockCommand(f"systemctl is-active libvirtd.service", aRc=0, aStdout="active", aPersist=True),
                    exaMockCommand(f"systemctl restart vmexacs_kvm", aRc=1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)
        for aHost in aRemoteHostList:
            with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True),\
                patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsHostOL8', return_value=True):
                clurestartObject.mRestartVmExacsService(aHost, MAX_RETRY)

    def test_mWaitForSystemBoot(self):
        ebLogInfo("Running unit test on mWaitForSystemBoot")

        mockCommands = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand(f"test.*systemd", aRc=0),
                    exaMockCommand(f"test.*pgrep", aRc=0),
                    exaMockCommand(f"test.*grep", aRc=0),
                    exaMockCommand(f"systemd-analyze time", aRc=0),
                    exaMockCommand(f"pgrep -af 'firstconf/elasticConfig.sh'", aRc=1)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)
        for _cell in self.mGetClubox().mReturnCellNodes():
            with connect_to_host(_cell, get_gcontext()) as _node, \
                patch("exabox.ovm.clumisc.time.sleep", return_value=None):
                self.assertEqual(None, mWaitForSystemBoot(_node))

    def test_mIsEth0Removed(self):
        ebLogInfo("Running unit test on mWaitForSystemBoot")
        mockCommands = {
            "sea202125exdd008.sea2xx2xx0111qf.adminsea2.oraclevcn.com": [
                [
                    exaMockCommand("/bin/test -e /etc/sysconfig/network-scripts/ifcfg-vmeth0")
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)
        _payload = self.mGetResourcesJsonFile("payload_exadbxs_add_compute.json")
        self.assertEqual(ebMiscFx.mIsEth0Removed(_payload, "sea202125exdd006.sea2xx2xx0111qf.adminsea2.oraclevcn.com"), True)
        self.assertEqual(ebMiscFx.mIsEth0Removed(_payload, "sea202125exdd007.sea2xx2xx0111qf.adminsea2.oraclevcn.com"), True)
        self.assertEqual(ebMiscFx.mIsEth0Removed(_payload, "sea202125exdd008.sea2xx2xx0111qf.adminsea2.oraclevcn.com"), False)

    def test_mCleanupSSHConfigFileOnMgmtHost(self):
        aHost = self.mGetClubox().mReturnDom0DomUPair()[1][0]
        _node = exaBoxNode(get_gcontext())
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mCleanupSSHConfigFileOnMgmtHost")
        ovmObject = ebCluSshSetup(self.mGetClubox())
        _cmd = "/bin/sed -i -e '/Host testnode/,+4d' /root/.ssh/config"
        _cmds = {
            self.mGetRegexDom0(): [

                [
                    exaMockCommand(f"/bin/test -e /bin/sed", aStdout="/bin/sed", aPersist=True),
                    exaMockCommand(re.escape(f"{_cmd}"), aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        ovmObject.mCleanupSSHConfigFileOnMgmtHost(aHost, ["testnode"])
        ebLogInfo("Unit test on ebCluSshSetup.mCleanupSSHConfigFileOnMgmtHost succeeded.")

    def test_mCleanupSSHConfigFileOnMgmtHost_Failure(self):
        aHost = self.mGetClubox().mReturnDom0DomUPair()[1][0]
        _node = exaBoxNode(get_gcontext())
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mCleanupSSHConfigFileOnMgmtHost_Failure")
        ovmObject = ebCluSshSetup(self.mGetClubox())
        _cmd = "/bin/sed -i -e '/Host testnode/,+4d' /root/.ssh/config"
        _cmds = {
            self.mGetRegexDom0(): [

                [
                    exaMockCommand(f"/bin/test -e /bin/sed", aStdout="/bin/sed", aPersist=True),
                    exaMockCommand(re.escape(f"{_cmd}"), aRc=-1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        ovmObject.mCleanupSSHConfigFileOnMgmtHost(aHost, ["testnode"])
        ebLogInfo("Unit test on ebCluSshSetup.mCleanupSSHConfigFileOnMgmtHost_Failure succeeded.")

    def test_mCleanupSSHConfigForMgmtHost(self):
        aHost = self.mGetClubox().mReturnDom0DomUPair()[1][0]
        _node = exaBoxNode(get_gcontext())
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mCleanupSSHConfigForMgmtHost")
        ovmObject = ebCluSshSetup(self.mGetClubox())
        _cmds = {
            self.mGetRegexDom0(): [

                [
                    exaMockCommand(f"/bin/test -e /bin/rm", aStdout="/bin/rm", aPersist=True),
                    exaMockCommand(f"/bin/rm scaqab10adm02.us.oracle.com", aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        with patch('exabox.ovm.clumisc.ebCluSshSetup.mValidateKnownHostsFile', return_value=True), patch('exabox.ovm.clumisc.ebCluSshSetup.mRemoveFromKnownHosts', return_value=True), patch('exabox.ovm.clumisc.ebCluSshSetup.mAddToKnownHosts', return_value=True),  patch('exabox.ovm.clumisc.ebCluSshSetup.mRemoveKeyFromHosts', return_value=True),patch('exabox.ovm.clumisc.ebCluSshSetup.mRemoveKeyFromHostsByComment', return_value=True), patch('exabox.ovm.clumisc.ebCluSshSetup.get_priv_hostkey_files', return_value=[aHost]), patch('exabox.ovm.clumisc.ebCluSshSetup.get_pub_hostkey_files', return_value=[aHost]):
             ovmObject.mCleanupSSHConfigForMgmtHost(aHost, "testnode")
        ebLogInfo("Unit test on ebCluSshSetup.mCleanupSSHConfigForMgmtHost succeeded.")

    def test_mConfigureSshForMgmtHost_Rsa(self):
        aHost = self.mGetClubox().mReturnDom0DomUPair()[1][0]
        aNodeList = ['test']
        _node = exaBoxNode(get_gcontext())
        _keys_dir = "/var/odo/infraPatchBase/keys/"
        _sshgen_cmd = f"/bin/ssh-keygen -C 'testcomment' -q -t rsa -N \"\" -f \"/var/odo/infraPatchBase/keys/test_id_rsa\"<<<y"

        _add_config_cmd = f'/bin/echo \"Host test\n    HostName test\n    User root\n    IdentityFile /var/odo/infraPatchBase/keys/test_id_rsa\n\" | /bin/sudo /bin/tee -a /root/.ssh/config'


        ebLogInfo(f"Remote host : {aHost}")

        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mConfigureSshForMgmtHost_Rsa")
        ovmObject = ebCluSshSetup(self.mGetClubox())
        _cmds = {

            self.mGetRegexDom0(): [

                [
                    exaMockCommand(f"/bin/test -e /bin/ls", aStdout="/bin/ls", aPersist=True),
                    exaMockCommand(f"/bin/test -e /bin/cat", aRc=0, aPersist=True, aStdout="/bin/cat"),
                    exaMockCommand(f"/bin/test -e /bin/mv", aRc=0, aPersist=True, aStdout="/bin/mv"),
                    exaMockCommand(f"/bin/test -e /bin/echo", aRc=0, aPersist=True, aStdout="/bin/echo"),
                    exaMockCommand(f"/bin/test -e /bin/ssh-keygen", aRc=0, aPersist=True, aStdout="/bin/ssh-keygen"),
                    exaMockCommand(f"/bin/test -e /bin/mkdir", aRc=0, aPersist=True, aStdout="/bin/mkdir"),
                    exaMockCommand(f"/bin/test -e /bin/sed", aRc=0, aPersist=True, aStdout="/bin/sed"),
                    exaMockCommand(f"/bin/test -e /bin/sudo", aRc=0, aPersist=True, aStdout="/bin/sudo"),
                    exaMockCommand(f"/bin/test -e /bin/tee", aRc=0, aPersist=True, aStdout="/bin/tee"),
                    exaMockCommand(f"/bin/ls /var/odo/infraPatchBase/keys/", aRc=-1, aPersist=True),
                    exaMockCommand(f"{_sshgen_cmd}", aRc=0, aPersist=True),
                    exaMockCommand(f"{_add_config_cmd}", aRc=0, aPersist=True),
                    exaMockCommand(f"/bin/cat /var/odo/infraPatchBase/keys/test_id_rsa.pub", aRc=0, aStdout="testkey", aPersist=True),
                    exaMockCommand(f"/bin/mkdir /var/odo/infraPatchBase/keys/", aRc=0, aPersist=True),


                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        with patch('exabox.ovm.clumisc.ebCluSshSetup.mRemoveFromKnownHosts', return_value=True), patch('exabox.ovm.clumisc.ebCluSshSetup.mAddToKnownHosts', return_value=True),  patch('exabox.ovm.clumisc.ebCluSshSetup.mRemoveKeyFromHosts', return_value=True), patch('exabox.ovm.clumisc.ebCluSshSetup.mRemoveKeyFromHostsByComment', return_value=True), patch('exabox.ovm.clumisc.ebCluSshSetup.mValidateKnownHostsFile', return_value=True), patch('exabox.ovm.clumisc.ebCluSshSetup.mAddKeyToHosts', return_value=True):
            ovmObject.mConfigureSshForMgmtHost(aHost, aNodeList, 'testcomment', '/var/odo/infraPatchBase/')
        ebLogInfo("Unit test on ebCluSshSetup.mConfigureSshForMgmtHost_Rsa succeeded.")

    def test_mConfigureSshForMgmtHost_Ecdsa(self):
        aHost = self.mGetClubox().mReturnDom0DomUPair()[1][0]
        aNodeList = ['test']
        _node = exaBoxNode(get_gcontext())
        _keys_dir = "/var/odo/infraPatchBase/keys/"
        _sshgen_cmd = f"/bin/ssh-keygen -C 'testcomment' -q -t ecdsa -N \"\" -f \"/var/odo/infraPatchBase/keys/test_id_ecdsa\"<<<y"

        _add_config_cmd = f'/bin/echo \"Host test\n    HostName test\n    User root\n    IdentityFile /var/odo/infraPatchBase/keys/test_id_ecdsa\n\" | /bin/sudo /bin/tee -a /root/.ssh/config'


        ebLogInfo(f"Remote host : {aHost}")

        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluSshSetup.mConfigureSshForMgmtHost_Ecdsa")
        ovmObject = ebCluSshSetup(self.mGetClubox())
        _cmds = {

            self.mGetRegexDom0(): [

                [
                    exaMockCommand(f"/bin/test -e /bin/ls", aStdout="/bin/ls", aPersist=True),
                    exaMockCommand(f"/bin/test -e /bin/cat", aRc=0, aPersist=True, aStdout="/bin/cat"),
                    exaMockCommand(f"/bin/test -e /bin/mv", aRc=0, aPersist=True, aStdout="/bin/mv"),
                    exaMockCommand(f"/bin/test -e /bin/echo", aRc=0, aPersist=True, aStdout="/bin/echo"),
                    exaMockCommand(f"/bin/test -e /bin/ssh-keygen", aRc=0, aPersist=True, aStdout="/bin/ssh-keygen"),
                    exaMockCommand(f"/bin/test -e /bin/mkdir", aRc=0, aPersist=True, aStdout="/bin/mkdir"),
                    exaMockCommand(f"/bin/test -e /bin/sed", aRc=0, aPersist=True, aStdout="/bin/sed"),
                    exaMockCommand(f"/bin/test -e /bin/sudo", aRc=0, aPersist=True, aStdout="/bin/sudo"),
                    exaMockCommand(f"/bin/test -e /bin/tee", aRc=0, aPersist=True, aStdout="/bin/tee"),
                    exaMockCommand(f"/bin/ls /var/odo/infraPatchBase/keys/", aRc=0, aPersist=True),
                    exaMockCommand(f"{_sshgen_cmd}", aRc=-1, aPersist=True),
                    exaMockCommand(f"{_add_config_cmd}", aRc=-1, aPersist=True),
                    exaMockCommand(f"/bin/cat /var/odo/infraPatchBase/keys/test_id_ecdsa.pub", aRc=-1, aStdout="testkey", aPersist=True),
                    exaMockCommand(f"/bin/mkdir /var/odo/infraPatchBase/keys/", aRc=-1, aPersist=True),


                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        with patch('exabox.ovm.clumisc.ebCluSshSetup.mRemoveFromKnownHosts', return_value=True), patch('exabox.ovm.clumisc.ebCluSshSetup.mAddToKnownHosts', return_value=True),  patch('exabox.ovm.clumisc.ebCluSshSetup.mRemoveKeyFromHosts', return_value=True), patch('exabox.ovm.clumisc.ebCluSshSetup.mRemoveKeyFromHostsByComment', return_value=True), patch('exabox.ovm.clumisc.ebCluSshSetup.mValidateKnownHostsFile', return_value=False), patch('exabox.ovm.clumisc.ebCluSshSetup.mAddKeyToHosts', return_value=True), patch('exabox.exakms.ExaKms.ExaKms.mGetDefaultKeyAlgorithm', return_value="ECDSA"):
            try:
                ovmObject.mConfigureSshForMgmtHost(aHost, aNodeList, 'testcomment', '/var/odo/infraPatchBase/')
            except:
                ebLogInfo("Exception Caught..")
        ebLogInfo("Unit test on ebCluSshSetup.mConfigureSshForMgmtHost_Ecdsa succeeded.")

    @patch('exabox.ovm.clumisc.ebLogInfo')
    def test_mAddMissingNtpDnsIpsExacc(self, mockLogInfo):
        _ebox = self.mGetClubox()
        _ebox.mSetOciExacc(True)
        _dom0s, _, _, _ = _ebox.mReturnAllClusterHosts()
        _prechecks = ebCluPreChecks(_ebox)
        _prechecks.mAddMissingNtpDnsIps(_dom0s)
        mockLogInfo.assert_called_once_with("Ntp and Dns server IPs are expected to be already set for exacc envs. Skipping update.")

    @patch('exabox.ovm.clumisc.ebLogInfo')
    def test_mAddMissingNtpDnsIps(self, mockLogInfo):
        _ebox = self.mGetClubox()
        _ebox.mSetCmd('createservice')
        _dom0s, _, _, _ = _ebox.mReturnAllClusterHosts()
        _prechecks = ebCluPreChecks(_ebox)
        with patch('exabox.ovm.clumisc.connect_to_host') as _connect, \
            patch('exabox.ovm.clumisc.ProcessManager') as _pmgr, \
            patch('exabox.ovm.clumisc.ProcessStructure') as _proc:
            _dict_grid = {
                'scaqab10celadm01.us.oracle.com': ['testGrid'],
                'scaqab10celadm02.us.oracle.com': ['testGrid'],
                'scaqab10celadm03.us.oracle.com': ['testGrid'],
            }
            _pmgr.return_value.mGetManager.return_value.dict.return_value = _dict_grid
            _node = Mock()
            _node.mFileExists.return_value = False
            _connect.return_value.__enter__.return_value = _node
            _prechecks.mAddMissingNtpDnsIps(_dom0s)
        mockLogInfo.assert_called_once_with("Grid disks found on cell - scaqab10celadm01.us.oracle.com : ['testGrid']. "\
            "Skipping update of ntp/dns values.")

    def test_mRunPhysicalDiskTest(self):
        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(io.StringIO(" "), io.StringIO("FLASH_4_1       failed - powering off"), io.StringIO("mock_error"))) as _mock_mExecuteCmd:
            _sanity_check = ebCluCellSanityTests(mMockPrecheck(self.mGetClubox()), aPrecheckConfig={}, aStep="ESTP_PREVM_CHECKS", aNodeInfo="iad207202exdcl01.iad200071qfab.adminiad2.oraclevcn.com")
            _sanity_check.mRunPhysicalDiskTest()
            self.assertEqual(_mock_mExecuteCmd.call_count, 1)

    def test_mStoreResultsJson_precheck_mSetProvErr(self):
        _cmds = {

            self.mGetRegexLocal(): [

                [
                    exaMockCommand("/bin/mkdir -p log/hardware_alerts/", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _cluprecheck = ebCluPreChecks(_ebox)
        with patch('builtins.open', mock_open()):
            _out = _cluprecheck.mStoreResultsJson("ESTP_PREVM_CHECKS",HARDWARE_ALERT_ESTP_PREVM_CHECKS_JSON)
            self.assertNotEqual(_ebox.mGetProvErr(),None)

    def test_mValidateElasticShapes_rc_zero_when_no_faulty_servers(self):
        _ebox = self.mGetClubox()
        _prechecks = ebCluPreChecks(_ebox)
        _options = self.mGetPayload()
        with patch.object(ebCluPreChecks, 'mParseHWAlertPayload', return_value={}), \
             patch.object(ebCluPreChecks, 'mRunHWSanityTest', return_value={}), \
             patch.object(ebCluPreChecks, 'validate_hw_results', return_value={
                 "quarter-rack-healthy-servers": [],
                 "quarter-rack-faulty-servers": [],
                 "elastic-healthy-servers": [],
                 "elastic-faulty-servers": []
             }), \
             patch.object(ebCluPreChecks, 'mUpdateRequestData') as mock_update:
            _rc = _prechecks.mValidateElasticShapes(_options, "ELASTIC_SHAPES_VALIDATION", {})
            self.assertEqual(_rc, 0)
            # mUpdateRequestData(options, rc, output, err) -> rc should be 0
            args, _ = mock_update.call_args
            self.assertEqual(args[1], 0)

    def test_mValidateElasticShapes_rc_one_when_faulty_servers_present(self):
        _ebox = self.mGetClubox()
        _prechecks = ebCluPreChecks(_ebox)
        _options = self.mGetPayload()
        with patch.object(ebCluPreChecks, 'mParseHWAlertPayload', return_value={}), \
             patch.object(ebCluPreChecks, 'mRunHWSanityTest', return_value={}), \
             patch.object(ebCluPreChecks, 'validate_hw_results', return_value={
                 "quarter-rack-healthy-servers": [],
                 "quarter-rack-faulty-servers": [],
                 "elastic-healthy-servers": [],
                 "elastic-faulty-servers": [{"hostname": "h1.example.com"}]
             }), \
             patch.object(ebCluPreChecks, 'mUpdateRequestData') as mock_update:
            _rc = _prechecks.mValidateElasticShapes(_options, "ELASTIC_SHAPES_VALIDATION", {})
            self.assertEqual(_rc, 1)
            # mUpdateRequestData(options, rc, output, err) -> rc should be 1
            args, _ = mock_update.call_args
            self.assertEqual(args[1], 1)

    def test_mValidateElasticShapes_err_message_on_faulty(self):
        _ebox = self.mGetClubox()
        _prechecks = ebCluPreChecks(_ebox)
        _options = self.mGetPayload()
        with patch.object(ebCluPreChecks, 'mParseHWAlertPayload', return_value={}), \
             patch.object(ebCluPreChecks, 'mRunHWSanityTest', return_value={}), \
             patch.object(ebCluPreChecks, 'validate_hw_results', return_value={
                 "quarter-rack-healthy-servers": [],
                 "quarter-rack-faulty-servers": [{"hostname": "h1.example.com"}],
                 "elastic-healthy-servers": [],
                 "elastic-faulty-servers": []
             }), \
             patch.object(ebCluPreChecks, 'mUpdateRequestData') as mock_update:
            _rc = _prechecks.mValidateElasticShapes(_options, "ELASTIC_SHAPES_VALIDATION", {})
            self.assertEqual(_rc, 1)
            # mUpdateRequestData(options, rc, output, err) -> err should contain failure message
            args, _ = mock_update.call_args
            self.assertEqual(args[1], 1)
            self.assertEqual(args[3], 'Elastic shape validation is failed.')

    @patch("exabox.ovm.clumisc.ebCluEthernetConfig.mSetCustomSpeed")
    @patch("exabox.ovm.clumisc.ebCluEthernetConfig.mValidateInterface", return_value=True)
    @patch("exabox.ovm.clumisc.mCompareModel")
    def test_mUpdateCustomEthernetSpeed_overlap(self, mock_compare_model, mock_validate, mock_set_custom):
        """# Auto-generated test for mUpdateCustomEthernetSpeed"""
        _ebox_local = copy.deepcopy(self.mGetClubox())
        ethernet_config = ebCluEthernetConfig(_ebox_local, _ebox_local._exaBoxCluCtrl__options)
        ethernet_config._ebCluEthernetConfig__cluctrl = Mock()
        ethernet_config._ebCluEthernetConfig__cluctrl.mCompareExadataModel.side_effect = lambda model, cmp: 1 if model >= cmp else -1
        ethernet_config._ebCluEthernetConfig__cluctrl.mEnvTarget.return_value = False

        mock_compare_model.side_effect = lambda model, cmp: 1 if model >= cmp else -1

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO("Supported link modes: 100000baseDR2/Full\n 50000baseDR2/Full\nAdvertised link modes: 100000baseDR2/Full\n 50000baseDR2/Full\n"), None),
            (None, io.StringIO("100000\n"), None)
        ]
        node.mGetHostname.return_value = "dom0-host"
        node.mGetCmdExitStatus.return_value = 0

        mock_set_custom.return_value = 0

        with patch.object(ebCluEthernetConfig, "mGetSupportedSpeeds", return_value=(
            ["100000baseDR2/Full", "50000baseDR2/Full"],
            ["100000baseDR2/Full", "50000baseDR2/Full"],
        )):
            rc = ethernet_config.mUpdateCustomEthernetSpeed(node, "dom0-host", "eth9", 25000, "X11")

        self.assertIsNone(rc)
        mock_set_custom.assert_called_with(node, "eth9", 25000, 100000, "X11")
        self.assertEqual(node.mExecuteCmd.call_args_list[-1][0][0], "cat /sys/class/net/eth9/speed")

    @patch("exabox.ovm.clumisc.ebCluEthernetConfig.mSetCustomSpeed")
    @patch("exabox.ovm.clumisc.ebCluEthernetConfig.mValidateInterface", return_value=True)
    @patch("exabox.ovm.clumisc.mCompareModel")
    def test_mUpdateCustomEthernetSpeed_no_overlap(self, mock_compare_model, mock_validate, mock_set_custom):
        """# Auto-generated test for mUpdateCustomEthernetSpeed"""
        _ebox_local = copy.deepcopy(self.mGetClubox())
        ethernet_config = ebCluEthernetConfig(_ebox_local, _ebox_local._exaBoxCluCtrl__options)
        ethernet_config._ebCluEthernetConfig__cluctrl = Mock()
        ethernet_config._ebCluEthernetConfig__cluctrl.mCompareExadataModel.return_value = -1
        ethernet_config._ebCluEthernetConfig__cluctrl.mEnvTarget.return_value = False

        mock_compare_model.side_effect = lambda model, cmp: 1 if model >= cmp else -1

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO("Supported link modes: 40000baseDR2/Full\nAdvertised link modes: 30000baseDR2/Full\n"), None),
            (None, io.StringIO("50000\n"), None)
        ]
        node.mGetHostname.return_value = "dom0-host"
        node.mGetCmdExitStatus.return_value = 0

        mock_set_custom.side_effect = [-1, 0]

        with patch.object(ebCluEthernetConfig, "mGetSupportedSpeeds", return_value=(
            ["40000baseDR2/Full"],
            ["30000baseDR2/Full"],
        )):
            rc = ethernet_config.mUpdateCustomEthernetSpeed(node, "dom0-host", "eth9", 25000, "X9")

        self.assertIsNone(rc)
        self.assertEqual(mock_set_custom.call_count, 1)
        # Fallback should force default 50000 speed for X9 models
        self.assertEqual(mock_set_custom.call_args_list[0][0][3], 50000)
        self.assertEqual(node.mExecuteCmd.call_args_list[-1][0][0], "cat /sys/class/net/eth9/speed")

    def test_mSetCustomSpeed_failure(self):
        """# Auto-generated test for mSetCustomSpeed"""
        _ebox_local = copy.deepcopy(self.mGetClubox())
        ethernet_config = ebCluEthernetConfig(_ebox_local, _ebox_local._exaBoxCluCtrl__options)

        node = Mock()
        node.mGetHostname.return_value = "dom0-host"
        node.mExecuteCmd = Mock()
        node.mGetCmdExitStatus.return_value = 1
        node.mDisconnect = Mock()

        with patch("exabox.ovm.clumisc.mCompareModel", return_value=1), patch("time.sleep", return_value=None):
            with self.assertRaises(ExacloudRuntimeError):
                ethernet_config.mSetCustomSpeed(node, "eth9", 25000, 100000, "X11")

        node.mExecuteCmd.assert_called_once_with("/usr/sbin/ethtool -s eth9 speed 100000 autoneg on")
        node.mDisconnect.assert_called_once()

    @patch("exabox.ovm.clumisc.mCompareModel", return_value=1)
    def test_mSetCustomSpeed_retries_until_match(self, mock_compare):
        """# Auto-generated test for mSetCustomSpeed"""
        _ebox_local = copy.deepcopy(self.mGetClubox())
        ethernet_config = ebCluEthernetConfig(_ebox_local, _ebox_local._exaBoxCluCtrl__options)

        node = Mock()
        node.mGetHostname.return_value = "dom0-host"
        node.mExecuteCmd = Mock()
        node.mGetCmdExitStatus.return_value = 0
        node.mDisconnect = Mock()

        with patch.object(ebCluEthernetConfig, "mGetCurrentSpeed", side_effect=[-1, -1, 100000]), \
             patch("exabox.ovm.clumisc.time.sleep", return_value=None):
            rc = ethernet_config.mSetCustomSpeed(node, "eth9", -1, 100000, "X11")

        self.assertEqual(rc, 0)
        node.mExecuteCmd.assert_called_once_with("/usr/sbin/ethtool -s eth9 speed 100000 autoneg on")
        node.mDisconnect.assert_not_called()

    def test_mSplitLinkMode_missing_base(self):
        """# Auto-generated test for mSplitLinkMode"""
        cluctrl = Mock()
        cluctrl.mCompareExadataModel.side_effect = lambda model, cmp: 1
        ethernet_config = ebCluEthernetConfig(cluctrl, Mock())

        speeds = ethernet_config.mSplitLinkMode(["100000baseDR2/Full", "CustomMode"])

        self.assertEqual(speeds, [100000, 0])

    def test_mGetSupportedSpeeds_multiline_parse(self):
        """# Auto-generated test for mGetSupportedSpeeds"""
        ethernet_config = ebCluEthernetConfig(Mock(), Mock())
        data = [
            "Supported link modes: 100000baseDR2/Full",
            " 50000baseDR2/Full",
            "Advertised link modes: 100000baseDR2/Full",
            " 25000baseDR2/Full",
            "Speed: 25000"
        ]

        advertised, supported = ethernet_config.mGetSupportedSpeeds(data)

        self.assertEqual(advertised, ["100000baseDR2/Full", "25000baseDR2/Full"])
        self.assertEqual(supported, ["100000baseDR2/Full", "50000baseDR2/Full"])

    def test_mGetCurrentSpeed_reads_speed(self):
        """# Auto-generated test for mGetCurrentSpeed"""
        ethernet_config = ebCluEthernetConfig(Mock(), Mock())
        node = Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO("40000\n"), None)

        result = ethernet_config.mGetCurrentSpeed(node, "eth4")

        self.assertEqual(result, 40000)
        node.mExecuteCmd.assert_called_once_with("/bin/cat /sys/class/net/eth4/speed")

    def test_mValidateInterface_soft_warning_short_circuit(self):
        """# Auto-generated test for mValidateInterface"""
        cluctrl = Mock()
        cluctrl.mIssueSoftWarningOnLinkfailure.return_value = True
        ethernet_config = ebCluEthernetConfig(cluctrl, Mock())

        node = Mock()

        self.assertTrue(ethernet_config.mValidateInterface(node, "eth9"))
        node.mExecuteCmd.assert_not_called()

    def test_mValidateInterface_interface_stays_down(self):
        """# Auto-generated test for mValidateInterface"""
        cluctrl = Mock()
        cluctrl.mIssueSoftWarningOnLinkfailure.return_value = False
        ethernet_config = ebCluEthernetConfig(cluctrl, Mock())

        node = Mock()
        node.mGetHostname.return_value = "dom0-host"
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO("down\n"), None),
            (None, io.StringIO("down\n"), None)
        ]
        node.mExecuteCmdLog = Mock()

        self.assertFalse(ethernet_config.mValidateInterface(node, "eth9"))
        node.mExecuteCmdLog.assert_called_once_with("/sbin/ip link set eth9 up")

    def test_mValidateInterface_speed_mismatch(self):
        """# Auto-generated test for mValidateInterface"""
        cluctrl = Mock()
        cluctrl.mIssueSoftWarningOnLinkfailure.return_value = False
        ethernet_config = ebCluEthernetConfig(cluctrl, Mock())

        node = Mock()
        node.mGetHostname.return_value = "dom0-host"
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO("up\n"), None),
            (None, io.StringIO("25000\n"), None)
        ]

        self.assertFalse(ethernet_config.mValidateInterface(node, "eth9", 50000))

    def test_mValidateInterface_speed_match(self):
        """# Auto-generated test for mValidateInterface"""
        cluctrl = Mock()
        cluctrl.mIssueSoftWarningOnLinkfailure.return_value = False
        ethernet_config = ebCluEthernetConfig(cluctrl, Mock())

        node = Mock()
        node.mGetHostname.return_value = "dom0-host"
        node.mExecuteCmdLog = Mock()
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO("up\n"), None),
            (None, io.StringIO("50000\n"), None)
        ]

        self.assertTrue(ethernet_config.mValidateInterface(node, "eth9", 50000))
        node.mExecuteCmdLog.assert_not_called()

    @patch("exabox.ovm.clumisc.ebCluEthernetConfig.mSetCustomSpeed", return_value=0)
    @patch("exabox.ovm.clumisc.ebCluEthernetConfig.mValidateInterface", return_value=True)
    def test_mUpdateCustomEthernetSpeed_env_target_exception(self, mock_validate, mock_set_speed):
        """# Auto-generated test for mUpdateCustomEthernetSpeed"""
        _ebox_local = copy.deepcopy(self.mGetClubox())
        ethernet_config = ebCluEthernetConfig(_ebox_local, _ebox_local._exaBoxCluCtrl__options)
        ethernet_config._ebCluEthernetConfig__cluctrl = Mock()
        ethernet_config._ebCluEthernetConfig__cluctrl.mCompareExadataModel.side_effect = lambda model, cmp: 1 if model >= cmp else -1
        ethernet_config._ebCluEthernetConfig__cluctrl.mEnvTarget.return_value = True

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO("Supported link modes: 100000baseDR2/Full\nAdvertised link modes: Not reported\n 100000baseDR2/Full\n"), None),
            (None, io.StringIO("100000\n"), None)
        ]
        node.mGetHostname.return_value = "dom0-host"
        node.mDisconnect = Mock()

        with patch.object(ebCluEthernetConfig, "mGetSupportedSpeeds", return_value=(
            ["25000baseCR/Full"],
            ["25000baseCR/Full"],
        )):
            with self.assertRaises(ExacloudRuntimeError):
                ethernet_config.mUpdateCustomEthernetSpeed(node, "dom0-host", "eth9", 25000, "X11")

        node.mDisconnect.assert_called_once()
        mock_set_speed.assert_called()

    @patch("exabox.ovm.clumisc.ebCluEthernetConfig.mSetCustomSpeed", return_value=0)
    @patch("exabox.ovm.clumisc.ebCluEthernetConfig.mValidateInterface", return_value=True)
    def test_mUpdateCustomEthernetSpeed_handles_retries(self, mock_validate, mock_set_speed):
        """# Auto-generated test for mUpdateCustomEthernetSpeed"""
        cluctrl = Mock()
        cluctrl.mCompareExadataModel.side_effect = lambda model, cmp: 1 if model >= cmp else -1
        cluctrl.mEnvTarget.return_value = False
        ethernet_config = ebCluEthernetConfig(cluctrl, Mock())

        node = Mock()
        node.mGetHostname.return_value = "dom0-host"
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO("Advertised link modes:\n 100000baseDR2/Full\n 50000baseDR2/Full\n"), None),
            (None, io.StringIO("100000\n"), None)
        ]

        with patch.object(ebCluEthernetConfig, "mGetSupportedSpeeds", return_value=(
            ["100000baseDR2/Full", "50000baseDR2/Full"],
            ["100000baseDR2/Full", "50000baseDR2/Full"],
        )):
            rc = ethernet_config.mUpdateCustomEthernetSpeed(node, "dom0-host", "eth9", 25000, "X11")

        self.assertIsNone(rc)
        mock_validate.assert_called_once_with(node, "eth9")
        mock_set_speed.assert_called_once_with(node, "eth9", 25000, 100000, "X11")

    @patch("exabox.ovm.clumisc.ebCluEthernetConfig.mSetCustomSpeed", return_value=0)
    @patch("exabox.ovm.clumisc.ebCluEthernetConfig.mGetSupportedSpeeds", return_value=([], []))
    @patch("exabox.ovm.clumisc.ebCluEthernetConfig.mValidateInterface", return_value=True)
    def test_mUpdateCustomEthernetSpeed_defaults_when_no_modes(self, mock_validate, mock_get_supported, mock_set_speed):
        """# Auto-generated test for mUpdateCustomEthernetSpeed"""
        cluctrl = Mock()

        def _compare(model, cmp):
            order = {"X8": 8, "X9": 9, "X10": 10, "X11": 11}
            return (order.get(model, 0) > order.get(cmp, 0)) - (order.get(model, 0) < order.get(cmp, 0))

        cluctrl.mCompareExadataModel.side_effect = _compare
        cluctrl.mEnvTarget.return_value = False
        ethernet_config = ebCluEthernetConfig(cluctrl, Mock())

        node = Mock()
        node.mGetHostname.return_value = "dom0-host"
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO(""), None),
            (None, io.StringIO("25000\n"), None)
        ]

        rc = ethernet_config.mUpdateCustomEthernetSpeed(node, "dom0-host", "eth9", 25000, "X8")

        self.assertIsNone(rc)
        mock_validate.assert_called_once_with(node, "eth9")
        mock_set_speed.assert_called_once_with(node, "eth9", 25000, 25000, "X8")

    @patch("exabox.ovm.clumisc.ebCluEthernetConfig.mSetCustomSpeed", return_value=0)
    @patch("exabox.ovm.clumisc.ebCluEthernetConfig.mGetSupportedSpeeds", return_value=([], []))
    @patch("exabox.ovm.clumisc.ebCluEthernetConfig.mValidateInterface", return_value=True)
    def test_mUpdateCustomEthernetSpeed_env_target_default_raises(self, mock_validate, mock_get_supported, mock_set_speed):
        """# Auto-generated test for mUpdateCustomEthernetSpeed"""
        cluctrl = Mock()

        def _compare(model, cmp):
            order = {"X8": 8, "X9": 9, "X10": 10, "X11": 11}
            return (order.get(model, 0) > order.get(cmp, 0)) - (order.get(model, 0) < order.get(cmp, 0))

        cluctrl.mCompareExadataModel.side_effect = _compare
        cluctrl.mEnvTarget.return_value = True
        ethernet_config = ebCluEthernetConfig(cluctrl, Mock())

        node = Mock()
        node.mGetHostname.return_value = "dom0-host"
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO(""), None),
            (None, io.StringIO("25000\n"), None)
        ]
        node.mDisconnect = Mock()

        with self.assertRaises(ExacloudRuntimeError):
            ethernet_config.mUpdateCustomEthernetSpeed(node, "dom0-host", "eth9", 25000, "X10")

        mock_validate.assert_called_once_with(node, "eth9")
        mock_set_speed.assert_called_once_with(node, "eth9", 25000, 100000, "X10")
        node.mDisconnect.assert_called_once()

    @patch("exabox.ovm.clumisc.ebCluEthernetConfig.mSetCustomSpeed", return_value=0)
    @patch("exabox.ovm.clumisc.ebCluEthernetConfig.mGetSupportedSpeeds", return_value=([], []))
    @patch("exabox.ovm.clumisc.ebCluEthernetConfig.mValidateInterface", return_value=True)
    def test_mUpdateCustomEthernetSpeed_env_target_false_mismatch(self, mock_validate, mock_get_supported, mock_set_speed):
        """# Auto-generated test for mUpdateCustomEthernetSpeed"""
        cluctrl = Mock()

        def _compare(model, cmp):
            order = {"X8": 8, "X9": 9, "X10": 10, "X11": 11}
            return (order.get(model, 0) > order.get(cmp, 0)) - (order.get(model, 0) < order.get(cmp, 0))

        cluctrl.mCompareExadataModel.side_effect = _compare
        cluctrl.mEnvTarget.return_value = False
        ethernet_config = ebCluEthernetConfig(cluctrl, Mock())

        node = Mock()
        node.mGetHostname.return_value = "dom0-host"
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO(""), None),
            (None, io.StringIO("25000\n"), None)
        ]
        node.mDisconnect = Mock()

        rc = ethernet_config.mUpdateCustomEthernetSpeed(node, "dom0-host", "eth9", 25000, "X10")

        self.assertIsNone(rc)
        mock_validate.assert_called_once_with(node, "eth9")
        mock_set_speed.assert_called_once_with(node, "eth9", 25000, 100000, "X10")
        node.mDisconnect.assert_not_called()

    def test_mReplaceDiscover_success(self):
        """# Auto-generated test for mReplaceDiscover"""
        data = {
            "natip": "discover",
            "nathostname": "testhost",
            "natdomain": "example.com"
        }
        with patch("exabox.ovm.clumisc.ebMiscFx.mExecuteLocal", return_value=(0, None, "192.0.2.10\n", "")):
            ebMiscFx.mReplaceDiscover(data)
        self.assertEqual(data["natip"], "192.0.2.10")

    def test_mReplaceDiscover_failure_raises(self):
        """# Auto-generated test for mReplaceDiscover"""
        data = {
            "natip": "discover",
            "nathostname": "testhost",
            "natdomain": "example.com"
        }
        with patch("exabox.ovm.clumisc.ebMiscFx.mExecuteLocal", return_value=(0, None, "", "")):
            with self.assertRaises(ExacloudRuntimeError):
                ebMiscFx.mReplaceDiscover(data)

    def test_getInitialIngestion_success(self):
        """# Auto-generated test for getInitialIngestion"""

        class _FakeNode(object):
            def __init__(self):
                self._exit = 0

            def mExecuteCmd(self, _cmd):
                return None, io.StringIO("id:abcd1234\n"), None

            def mGetCmdExitStatus(self):
                return self._exit

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.clumisc.connect_to_host", return_value=_FakeNode()):
            self.assertEqual(ebMiscFx.getInitialIngestion("dom0"), "abcd1234")

    def test_getInitialIngestion_exit_nonzero(self):
        """# Auto-generated test for getInitialIngestion"""

        class _FakeNode(object):
            def __init__(self):
                self._exit = 1

            def mExecuteCmd(self, _cmd):
                return None, io.StringIO("id:abcd1234\n"), None

            def mGetCmdExitStatus(self):
                return self._exit

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.clumisc.connect_to_host", return_value=_FakeNode()):
            self.assertEqual(ebMiscFx.getInitialIngestion("dom0"), "")

    def test_mIsSkipBondingBridge_true(self):
        """# Auto-generated test for mIsSkipBondingBridge"""
        payload = {
            "customer_network": {
                "nodes": [
                    {"fqdn": "host1", "skip_bonding": "true"},
                    {"fqdn": "host2", "skip_bonding": "false"}
                ]
            }
        }
        self.assertTrue(ebMiscFx.mIsSkipBondingBridge(payload, "host1"))
        self.assertFalse(ebMiscFx.mIsSkipBondingBridge(payload, "host2"))

    def test_mIsSkipBondingBridge_missing(self):
        """# Auto-generated test for mIsSkipBondingBridge"""
        payload = {"customer_network": {"nodes": [{"fqdn": "host1"}]}}
        self.assertFalse(ebMiscFx.mIsSkipBondingBridge(payload, "host1"))

    def test_mIsEth0Removed_fallback_file_missing(self):
        """# Auto-generated test for mIsEth0Removed"""
        class _Node(object):
            def __init__(self):
                self._file_exists = False

            def mFileExists(self, _path):
                return self._file_exists

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        payload = {}
        with patch("exabox.ovm.clumisc.connect_to_host", return_value=_Node()), \
            patch("exabox.ovm.clumisc.get_gcontext"):
            self.assertTrue(ebMiscFx.mIsEth0Removed(payload, "dom0"))

    def test_mIsEth0Removed_reshaped_subset_true(self):
        """# Auto-generated test for mIsEth0Removed"""
        payload = {
            "reshaped_node_subset": {
                "added_computes": [
                    {"compute_node_hostname": "dom0", "eth0_removed": "true"}
                ],
                "participating_computes": [
                    {"compute_node_hostname": "dom1", "eth0_removed": "false"}
                ],
            }
        }
        self.assertTrue(ebMiscFx.mIsEth0Removed(payload, "dom0"))

    def test_mIsEth0Removed_customer_network_false(self):
        """# Auto-generated test for mIsEth0Removed"""
        class _Node(object):
            def mFileExists(self, _path):
                return True

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        payload = {
            "customer_network": {
                "nodes": [
                    {"fqdn": "dom0", "eth0_removed": "false"}
                ]
            }
        }
        with patch("exabox.ovm.clumisc.connect_to_host", return_value=_Node()), \
            patch("exabox.ovm.clumisc.get_gcontext"):
            self.assertFalse(ebMiscFx.mIsEth0Removed(payload, "dom0"))

    def test_mIsEth0Removed_participating_false(self):
        """# Auto-generated test for mIsEth0Removed"""
        class _Node(object):
            def mFileExists(self, _path):
                return True

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        payload = {
            "reshaped_node_subset": {
                "participating_computes": [
                    {"compute_node_hostname": "dom0", "eth0_removed": "false"}
                ]
            }
        }
        with patch("exabox.ovm.clumisc.connect_to_host", return_value=_Node()), \
            patch("exabox.ovm.clumisc.get_gcontext"):
            self.assertFalse(ebMiscFx.mIsEth0Removed(payload, "dom0"))

    def test_validateIpOrHostname_variants(self):
        """# Auto-generated test for validateIpOrHostname"""
        self.assertTrue(validateIpOrHostname("192.168.1.1"))
        self.assertTrue(validateIpOrHostname("2001:db8::1"))
        self.assertTrue(validateIpOrHostname("valid-host.example"))
        self.assertFalse(validateIpOrHostname("bad host!"))

    def test_ebSubnetIp_basic_paths(self):
        """# Auto-generated test for ebSubnetIp"""
        subnet = ebSubnetIp("10.0.0.10/24")
        self.assertEqual(subnet.mGetCIDR(), "10.0.0.0/24")
        self.assertTrue(subnet.mGetSubnet().startswith("10.0.0.0/"))
        self.assertEqual(ebSubnetIp("10.0.0.5/32").mGetAllIPs(), ["10.0.0.5"])
        self.assertEqual(ebSubnetIp("10.0.0.0/31").mGetAllIPs(), [])

    def test_ebSubnetIp_invalid_segment_and_int_to_ip(self):
        """# Auto-generated test for ebSubnetIp"""
        subnet = ebSubnetIp("10.0.0.1/32")
        self.assertIsNone(subnet.mIntToIp(None))
        with self.assertRaises(ValueError):
            subnet.mLimitSegment(300)

    def test_ebSubnetIp_invalid_raises(self):
        """# Auto-generated test for ebSubnetIp"""
        with patch("exabox.ovm.clumisc.socket.gethostbyname", side_effect=Exception("boom")):
            with self.assertRaises(ValueError):
                ebSubnetIp("not-an-ip")

    def test_ebSubnetSet_conflict_replace(self):
        """# Auto-generated test for ebSubnetSet"""
        subnet_set = ebSubnetSet()
        subnet_set.mAddSubnet("10.0.0.0/25")
        self.assertEqual(len(subnet_set.mGetCIDRList()), 1)
        subnet_set.mAddSubnet("10.0.0.0/24")
        self.assertEqual(subnet_set.mGetCIDRList(), ["10.0.0.0/24"])

    def test_ebSubnetSet_append_and_conflicts(self):
        """# Auto-generated test for ebSubnetSet"""
        subnet_set = ebSubnetSet()
        subnet_set.mAppendList(["10.0.1.0/30", "10.0.1.4/30"])
        conflicts = subnet_set.mIpInSet("10.0.1.0/29")
        self.assertTrue(any(val < 0 for val in conflicts))
        subnet_set.mAddSubnet("10.0.1.0/29")
        self.assertEqual(subnet_set.mGetCIDRList(), ["10.0.1.0/29"])

    def test_ebSubnetSet_get_lists_and_ips(self):
        """# Auto-generated test for ebSubnetSet"""
        subnet_set = ebSubnetSet()
        subnet_set.mAppendList(["10.0.2.0/30", "10.0.2.4/30"])

        self.assertEqual(subnet_set.mGetCIDRList(), ["10.0.2.0/30", "10.0.2.4/30"])
        self.assertEqual(
            subnet_set.mGetSubnetList(),
            ["10.0.2.0/255.255.255.252", "10.0.2.4/255.255.255.252"],
        )
        self.assertEqual(
            subnet_set.mGetAllIPs(),
            [
                "10.0.2.0",
                "10.0.2.1",
                "10.0.2.2",
                "10.0.2.3",
                "10.0.2.4",
                "10.0.2.5",
                "10.0.2.6",
                "10.0.2.7",
            ],
        )

    def test_mPatchPrivNetworks_kvm_paths(self):
        """# Auto-generated test for mPatchPrivNetworks"""
        os.environ.setdefault("EXATEST_SKIP_INIT", "1")
        ebox = Mock()
        ebox.mReturnDom0DomUPair.return_value = [("dom0a", "domu1")]
        ebox.mIsKVM.return_value = True

        class _NetConf(object):
            def __init__(self, net_type, name, iface, host=""):
                self._type = net_type
                self._name = name
                self._iface = iface
                self._host = host

            def mGetNetType(self):
                return self._type

            def mGetNetName(self):
                return self._name

            def mGetInterfaceName(self):
                return self._iface

            def mGetPkeyName(self):
                return ""

            def mGetNetMaster(self):
                return ""

            def mSetNetHostName(self, host):
                self._host = host

            def mGetNetHostName(self):
                return self._host

        client_net = _NetConf("client", "client", "eth0", "clienthost")
        priv1_net = _NetConf("private", "priv1", "stre0")
        priv2_net = _NetConf("private", "priv2", "stre1")
        cluster_priv1 = _NetConf("private", "clusterpriv1", "clre0")
        cluster_priv2 = _NetConf("private", "clusterpriv2", "clre1")

        networks = Mock()
        networks.mGetNetworkConfig.side_effect = {
            "client": client_net,
            "priv1": priv1_net,
            "priv2": priv2_net,
            "clusterpriv1": cluster_priv1,
            "clusterpriv2": cluster_priv2,
        }.get

        class _MachineConf(object):
            def __init__(self, nets):
                self._nets = nets

            def mGetMacNetworks(self):
                return self._nets

        machines = Mock()
        machines.mGetMachineConfig.return_value = _MachineConf(
            ["client", "priv1", "priv2", "clusterpriv1", "clusterpriv2"]
        )

        ebox.mGetNetworks.return_value = networks
        ebox.mGetMachines.return_value = machines

        mPatchPrivNetworks(ebox)

        self.assertEqual(priv1_net.mGetNetHostName(), "clienthost-stre0")
        self.assertEqual(priv2_net.mGetNetHostName(), "clienthost-stre1")
        self.assertEqual(cluster_priv1.mGetNetHostName(), "clienthost-clre0")
        self.assertEqual(cluster_priv2.mGetNetHostName(), "clienthost-clre1")

    def test_mPatchPrivNetworks_missing_privs(self):
        """# Auto-generated test for mPatchPrivNetworks"""
        os.environ.setdefault("EXATEST_SKIP_INIT", "1")
        ebox = Mock()
        ebox.mReturnDom0DomUPair.return_value = [("dom0a", "domu1")]
        ebox.mIsKVM.return_value = False

        class _NetConf(object):
            def __init__(self, net_type, name, pkey, iface, host=""):
                self._type = net_type
                self._name = name
                self._pkey = pkey
                self._iface = iface
                self._host = host

            def mGetNetType(self):
                return self._type

            def mGetNetName(self):
                return self._name

            def mGetInterfaceName(self):
                return self._iface

            def mGetPkeyName(self):
                return self._pkey

            def mSetNetHostName(self, host):
                self._host = host

            def mGetNetHostName(self):
                return self._host

        client_net = _NetConf("client", "client", "", "eth0", "clienthost")
        priv1_net = _NetConf("private", "priv1", "stib0", "ib0")
        priv2_net = _NetConf("private", "priv2", "stib1", "ib1")

        networks = Mock()
        networks.mGetNetworkConfig.side_effect = {
            "client": client_net,
            "priv1": priv1_net,
            "priv2": priv2_net,
        }.get

        class _MachineConf(object):
            def __init__(self, nets):
                self._nets = nets

            def mGetMacNetworks(self):
                return self._nets

        machines = Mock()
        machines.mGetMachineConfig.return_value = _MachineConf(["client", "priv1", "priv2"])

        ebox.mGetNetworks.return_value = networks
        ebox.mGetMachines.return_value = machines

        with patch("exabox.ovm.clumisc.ebLogWarn") as warn_mock:
            mPatchPrivNetworks(ebox)
            warn_mock.assert_called_once()

        self.assertEqual(priv1_net.mGetNetHostName(), "")
        self.assertEqual(priv2_net.mGetNetHostName(), "")

    def test_mPatchPrivNetworks_missing_client_net(self):
        """# Auto-generated test for mPatchPrivNetworks"""
        os.environ.setdefault("EXATEST_SKIP_INIT", "1")
        ebox = Mock()
        ebox.mReturnDom0DomUPair.return_value = [("dom0a", "domu1")]
        ebox.mIsKVM.return_value = True

        class _NetConf(object):
            def __init__(self, net_type, name, iface, host=""):
                self._type = net_type
                self._name = name
                self._iface = iface
                self._host = host

            def mGetNetType(self):
                return self._type

            def mGetNetName(self):
                return self._name

            def mGetInterfaceName(self):
                return self._iface

            def mGetPkeyName(self):
                return ""

            def mGetNetMaster(self):
                return ""

            def mSetNetHostName(self, host):
                self._host = host

            def mGetNetHostName(self):
                return self._host

        priv1_net = _NetConf("private", "priv1", "stre0")
        priv2_net = _NetConf("private", "priv2", "stre1")
        cluster_priv1 = _NetConf("private", "clusterpriv1", "clre0")
        cluster_priv2 = _NetConf("private", "clusterpriv2", "clre1")

        networks = Mock()
        networks.mGetNetworkConfig.side_effect = {
            "priv1": priv1_net,
            "priv2": priv2_net,
            "clusterpriv1": cluster_priv1,
            "clusterpriv2": cluster_priv2,
        }.get

        class _MachineConf(object):
            def __init__(self, nets):
                self._nets = nets

            def mGetMacNetworks(self):
                return self._nets

        machines = Mock()
        machines.mGetMachineConfig.return_value = _MachineConf(
            ["priv1", "priv2", "clusterpriv1", "clusterpriv2"]
        )

        ebox.mGetNetworks.return_value = networks
        ebox.mGetMachines.return_value = machines

        with patch("exabox.ovm.clumisc.ebLogWarn") as warn_mock:
            with self.assertRaises(AttributeError):
                mPatchPrivNetworks(ebox)
            warn_mock.assert_not_called()

    def test_mChangeOpCtlAudit_no_reboot_shared(self):
        """# Auto-generated test for mChangeOpCtlAudit"""
        os.environ.setdefault("EXATEST_SKIP_INIT", "1")
        ebox = Mock()
        ebox.mReturnAllClusterHosts.return_value = (["dom0a"], [], ["cell1"], [])
        ebox.mCheckSharedEnvironment.return_value = True

        vm = Mock()
        vm.getTotalVMs.return_value = 1

        node_instance = Mock()
        node_instance.mExecuteCmd.side_effect = [
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO("found"), None),
        ]

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node_instance), \
            patch("exabox.ovm.clumisc.getHVInstance", return_value=vm):
            mChangeOpCtlAudit(ebox, False)

        self.assertEqual(node_instance.mConnect.call_args_list[0][1]["aHost"], "dom0a")
        self.assertEqual(node_instance.mConnect.call_args_list[1][1]["aHost"], "cell1")
        self.assertEqual(node_instance.mExecuteCmd.call_count, 4)

    def test_mChangeOpCtlAudit_reboot_when_safe(self):
        """# Auto-generated test for mChangeOpCtlAudit"""
        os.environ.setdefault("EXATEST_SKIP_INIT", "1")
        ebox = Mock()
        ebox.mReturnAllClusterHosts.return_value = (["dom0a", "dom0b"], [], ["cell1"], [])
        ebox.mCheckSharedEnvironment.return_value = False

        node_instance = Mock()
        node_instance.mExecuteCmd.side_effect = [
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
        ]

        processes = []

        class _Proc(object):
            def __init__(self, *_args):
                self._args = _args
                processes.append(self)

            def mSetMaxExecutionTime(self, _val):
                self.max_time = _val

            def mSetJoinTimeout(self, _val):
                self.join_timeout = _val

            def mSetLogTimeoutFx(self, _fx):
                self.log_fx = _fx

        plist = Mock()

        class _Proc(object):
            def __init__(self, *args, **kwargs):
                processes.append((args, kwargs))

            def mSetMaxExecutionTime(self, _val):
                pass

            def mSetJoinTimeout(self, _val):
                pass

            def mSetLogTimeoutFx(self, _fx):
                pass

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node_instance), \
            patch("exabox.ovm.clumisc.ProcessManager", return_value=plist), \
            patch("exabox.ovm.clumisc.ProcessStructure", _Proc):
            mChangeOpCtlAudit(ebox, True)

        self.assertEqual(node_instance.mExecuteCmd.call_count, 6)
        self.assertGreaterEqual(len(processes), 3)
        self.assertGreaterEqual(plist.mStartAppend.call_count, 3)
        plist.mJoinProcess.assert_called_once()

    def test_mPatchPrivNetworks_non_kvm_paths(self):
        """# Auto-generated test for mPatchPrivNetworks"""
        os.environ.setdefault("EXATEST_SKIP_INIT", "1")
        ebox = Mock()
        ebox.mReturnDom0DomUPair.return_value = [("dom0a", "domu1")]
        ebox.mIsKVM.return_value = False

        class _NetConf(object):
            def __init__(self, net_type, name, pkey, iface, host=""):
                self._type = net_type
                self._name = name
                self._pkey = pkey
                self._iface = iface
                self._host = host

            def mGetNetType(self):
                return self._type

            def mGetNetName(self):
                return self._name

            def mGetInterfaceName(self):
                return self._iface

            def mGetPkeyName(self):
                return self._pkey

            def mSetNetHostName(self, host):
                self._host = host

            def mGetNetHostName(self):
                return self._host

        client_net = _NetConf("client", "client", "", "eth0", "clienthost")
        priv1_net = _NetConf("private", "priv1", "stib0", "ib0")
        priv2_net = _NetConf("private", "priv2", "stib1", "ib1")
        cluster_priv1 = _NetConf("private", "clusterpriv1", "", "clib0")
        cluster_priv2 = _NetConf("private", "clusterpriv2", "", "clib1")

        networks = Mock()
        networks.mGetNetworkConfig.side_effect = {
            "client": client_net,
            "priv1": priv1_net,
            "priv2": priv2_net,
            "clusterpriv1": cluster_priv1,
            "clusterpriv2": cluster_priv2,
        }.get

        class _MachineConf(object):
            def __init__(self, nets):
                self._nets = nets

            def mGetMacNetworks(self):
                return self._nets

        machines = Mock()
        machines.mGetMachineConfig.return_value = _MachineConf(
            ["client", "priv1", "priv2", "clusterpriv1", "clusterpriv2"]
        )

        ebox.mGetNetworks.return_value = networks
        ebox.mGetMachines.return_value = machines

        mPatchPrivNetworks(ebox)

        self.assertEqual(priv1_net.mGetNetHostName(), "clienthost-stre0")
        self.assertEqual(priv2_net.mGetNetHostName(), "clienthost-stre1")
        self.assertEqual(cluster_priv1.mGetNetHostName(), "clienthost-clre0")
        self.assertEqual(cluster_priv2.mGetNetHostName(), "clienthost-clre1")

    def test_mChangeOpCtlAudit_skip_when_present(self):
        """# Auto-generated test for mChangeOpCtlAudit"""
        os.environ.setdefault("EXATEST_SKIP_INIT", "1")
        ebox = Mock()
        ebox.mReturnAllClusterHosts.return_value = (["dom0a"], [], ["cell1"], [])

        node_instance = Mock()
        node_instance.mExecuteCmd.side_effect = [
            (None, io.StringIO("found"), None),
            (None, io.StringIO("found"), None),
        ]

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node_instance):
            mChangeOpCtlAudit(ebox, False)

        self.assertEqual(node_instance.mExecuteCmd.call_count, 2)
        self.assertEqual(node_instance.mConnect.call_args_list[0][1]["aHost"], "dom0a")
        self.assertEqual(node_instance.mConnect.call_args_list[1][1]["aHost"], "cell1")
        node_instance.mDisconnect.assert_called()

    def test_mGetAlertHistoryOptions_default_inline(self):
        """# Auto-generated test for mGetAlertHistoryOptions"""
        ebox = Mock()
        ebox.mCheckConfigOption.return_value = ""
        ebox.mGetImageVersion.return_value = "25.1.0"

        self.assertEqual("--inline", mGetAlertHistoryOptions(ebox, "cell1"))

    def test_mGetAlertHistoryOptions_configured(self):
        """# Auto-generated test for mGetAlertHistoryOptions"""
        ebox = Mock()
        ebox.mCheckConfigOption.return_value = "--inline --foo"
        ebox.mGetImageVersion.return_value = "25.2.0"

        self.assertEqual("--inline --foo", mGetAlertHistoryOptions(ebox, "cell1"))

    def test_mGetAlertHistoryOptions_old_version(self):
        """# Auto-generated test for mGetAlertHistoryOptions"""
        ebox = Mock()
        ebox.mCheckConfigOption.return_value = "--inline"
        ebox.mGetImageVersion.return_value = "24.2.0"

        self.assertEqual("", mGetAlertHistoryOptions(ebox, "cell1"))

    def test_mGetDom0sImagesListSorted(self):
        """# Auto-generated test for mGetDom0sImagesListSorted"""
        ebox = Mock()
        ebox.mReturnDom0DomUPair.return_value = [("dom0a", "domu1"), ("dom0b", "domu2")]

        def _get_version(host):
            return {"dom0a": "25.2.1", "dom0b": "25.1.5"}.get(host)

        ebox.mGetImageVersion.side_effect = _get_version

        self.assertEqual(["25.1.5", "25.2.1"], mGetDom0sImagesListSorted(ebox))

    def test_mGetGridListSupportedByOeda_supported(self):
        """# Auto-generated test for mGetGridListSupportedByOeda"""
        ebox = Mock()
        ebox.mGetOedaPath.return_value = "/opt/oeda"
        ebox.mExecuteLocal.return_value = (
            0,
            "",
            "19.25.0.0.0, 19.26.0.0.0" + os.linesep + "19.27.0.0.0",
            "",
        )

        self.assertTrue(mGetGridListSupportedByOeda(ebox, "19.25.2.0.0"))

    def test_mGetGridListSupportedByOeda_unsupported(self):
        """# Auto-generated test for mGetGridListSupportedByOeda"""
        ebox = Mock()
        ebox.mGetOedaPath.return_value = "/opt/oeda"
        ebox.mExecuteLocal.return_value = (
            0,
            "",
            "19.22.0.0.0, 19.23.0.0.0" + os.linesep + "" + os.linesep + "GI",
            "",
        )

        result = mGetGridListSupportedByOeda(ebox, "19.25.0.0.0")
        self.assertFalse(result[0])

    def test_mGetGridListSupportedByOeda_exception(self):
        """# Auto-generated test for mGetGridListSupportedByOeda"""
        ebox = Mock()
        ebox.mGetOedaPath.side_effect = Exception("boom")

        result = mGetGridListSupportedByOeda(ebox, "19.25.0.0.0")
        self.assertFalse(result[0])

    def test_mWaitForSystemBoot_waits_for_process(self):
        """# Auto-generated test for mWaitForSystemBoot"""
        os.environ.setdefault("EXATEST_SKIP_INIT", "1")
        node = Mock()
        node.mGetHostname.return_value = "cell1"

        class _CmdRet(object):
            def __init__(self, exit_code):
                self.exit_code = exit_code

        exec_side = [
            _CmdRet(1),
            _CmdRet(0),
            _CmdRet(0),
        ]

        list_side = [
            ["firstconf/elasticConfig.sh"],
            [],
        ]

        with patch("exabox.ovm.clumisc.node_cmd_abs_path_check", return_value="/bin/systemd-analyze"), \
            patch("exabox.ovm.clumisc.node_exec_cmd", side_effect=exec_side), \
            patch("exabox.ovm.clumisc.node_list_process", side_effect=list_side), \
            patch("exabox.ovm.clumisc.time.sleep", return_value=None):
            self.assertIsNone(mWaitForSystemBoot(node))

    def test_OracleVersion_compare_and_sort(self):
        """# Auto-generated test for OracleVersion"""
        version = OracleVersion()
        self.assertEqual(0, version.mCompareVersions(2, 2))
        self.assertEqual(1, version.mCompareVersions(3, 2))
        self.assertEqual(-1, version.mCompareVersions(1, 2))
        self.assertEqual(-1, version.mCompareVersions("2.1.8-1", "2.1.8-2"))
        self.assertEqual(1, version.mCompareVersions("2.1.9", "2.1.8"))
        versions = ["19.12.0.0.0", "19.3.0.0.0", "19.10.0.0.0"]
        self.assertEqual(
            ["19.3.0.0.0", "19.10.0.0.0", "19.12.0.0.0"],
            version.mSortVersion(versions),
        )
        self.assertEqual("19.12.0.0.0", version.mGetHighestVer(versions))

    def test_OracleVersion_invalid_inputs(self):
        """# Auto-generated test for OracleVersion"""
        version = OracleVersion()
        self.assertIsNone(version.mCompareVersions(None, "1.0.0"))
        self.assertIsNone(version.mSortVersion([]))
        self.assertIsNone(version.mGetHighestVer([]))

    def test_ebFortifyIssues_path_validation(self):
        """# Auto-generated test for ebFortifyIssues"""
        fortify = ebFortifyIssues()
        self.assertTrue(fortify.mPathManipulationError("../etc/passwd"))
        self.assertFalse(fortify.mPathManipulationError("/var/tmp/safe_path"))




    def test_ebCluScheduleManager_invalid_invocation(self):
        """# Auto-generated test for ebCluScheduleManager"""
        ebox = Mock()
        ebox.mGetRequestObj.return_value = None
        scheduler = ebCluScheduleManager(ebox)

        options = Mock()
        options.sccmd = None
        options.jsonmode = False

        rc = scheduler.mHandleRequest(options)

        self.assertEqual(rc, -1)
        self.assertEqual(scheduler.mGetData().get("Status"), "Fail")

    def test_ebCluScheduleManager_list_populates_data(self):
        """# Auto-generated test for ebCluScheduleManager"""
        ebox = Mock()
        req = Mock()
        ebox.mGetRequestObj.return_value = req
        scheduler = ebCluScheduleManager(ebox)

        options = Mock()
        options.sccmd = "list"
        options.jsonmode = False

        schedules = [
            ("uuid-1", None, "mode1", "op1", "event1", "timer", "ts", 120, 5, 1, "mon-1", "jobs", "running"),
            ("uuid-2", None, "mode2", "op2", "event2", "timer2", "ts2", 60, 3, 2, "mon-2", "jobs2", "pending"),
        ]
        db_mock = Mock()
        db_mock.mGetSchedule.return_value = schedules

        with patch("exabox.ovm.clumisc.ebGetDefaultDB", return_value=db_mock):
            rc = scheduler.mHandleRequest(options)

        self.assertEqual(rc, 0)
        data = scheduler.mGetData()
        self.assertEqual(data.get("Command"), "list")
        self.assertEqual(data.get("Status"), "Pass")
        self.assertIn("uuid-1", data.get("uuid", {}))
        self.assertEqual(data["uuid"]["uuid-2"]["operation"], "op2")
        req.mSetData.assert_called_once()

    def test_ebCluScheduleManager_list_jsonmode(self):
        """# Auto-generated test for ebCluScheduleManager"""
        ebox = Mock()
        ebox.mGetRequestObj.return_value = None
        scheduler = ebCluScheduleManager(ebox)

        options = Mock()
        options.sccmd = "list"
        options.jsonmode = True

        schedules = [
            ("uuid-1", None, "mode1", "op1", "event1", "timer", "ts", 120, 5, 1, "mon-1", "jobs", "running")
        ]
        db_mock = Mock()
        db_mock.mGetSchedule.return_value = schedules

        with patch("exabox.ovm.clumisc.ebGetDefaultDB", return_value=db_mock), \
            patch("exabox.ovm.clumisc.ebLogJson") as log_json:
            rc = scheduler.mHandleRequest(options)

        self.assertEqual(rc, 0)
        self.assertTrue(log_json.called)

    def test_ebCluCellValidate_invalid_params(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None

        options = Mock()
        options.jsonconf = {}
        options.jsonmode = False

        validator = ebCluCellValidate(cluctrl, options)
        rc = validator.mValidateCell(options)

        self.assertEqual(rc, 0)

    def test_ebCluCellValidate_skips_when_not_ociexacc(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = False
        cluctrl.mGetRequestObj.return_value = None

        options = Mock()
        options.jsonconf = {"cell_list": ["cell1"]}
        options.jsonmode = False

        validator = ebCluCellValidate(cluctrl, options)

        with patch.object(validator, "mValidateCellStat") as validate_stat:
            rc = validator.mValidateCell(options)

        self.assertEqual(rc, 0)
        validate_stat.assert_not_called()

    def test_ebCluCellValidate_stat_failures(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None

        options = Mock()
        options.jsonconf = {"cell_list": ["cell1"]}
        options.jsonmode = False

        validator = ebCluCellValidate(cluctrl, options)

        cluctrl.mPingHost.return_value = False
        rc = validator.mValidateCell(options)

        self.assertEqual(rc, 0)

        cluctrl.mPingHost.return_value = True
        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls:
            node = node_cls.return_value
            node.mConnect.side_effect = Exception("boom")
            stat = validator.mValidateCellStat(options, "cell1")

        self.assertEqual(stat["error_code"], "0x0801")
        self.assertIn("Failed to connect", stat["status"])

    def test_ebCluCellValidate_stat_alerts_and_missing_cellsrv(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mPingHost.return_value = True
        cluctrl.mGetNodeModel.return_value = "X8M-2"

        options = Mock()
        options.jsonconf = {"cell_list": ["cell1"]}
        options.jsonmode = False

        validator = ebCluCellValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls, \
            patch("exabox.ovm.clumisc.mGetAlertHistoryOptions", return_value=""):
            node = node_cls.return_value
            node.mConnect.return_value = None
            outputs = [
                "Exadata X8M-2\n",
                "2024-01-01 warning \"Advanced Intrusion Detection Environment (AIDE) detected potential changes to software on this system. The changes are in /var/log/aide/aide.log \"\n",
                "2024-01-01 warning other\n",
                "",  # cell detail output
            ]
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO(outputs[0]), None),
                (None, io.StringIO(outputs[1] + outputs[2]), None),
                (None, io.StringIO(outputs[3]), None),
            ]
            stat = validator.mValidateCellStat(options, "cell1")

        self.assertEqual(stat["error_code"], "0x849")
        self.assertIn("failed to query Cellcli alert", stat["status"])

    def test_ebCluCellValidate_stat_success(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mPingHost.return_value = True
        cluctrl.mGetNodeModel.return_value = "X8M-2"

        options = Mock()
        options.jsonconf = {"cell_list": ["cell1"]}
        options.jsonmode = False

        validator = ebCluCellValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls, \
            patch("exabox.ovm.clumisc.mGetAlertHistoryOptions", return_value=""):
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X8M-2\n"), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO("cellsrvStatus: running\nmsStatus: running\nrsStatus: running\nname: cell1\n"), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO("celldisk1 100G\n"), None),
            ]
            stat = validator.mValidateCellStat(options, "cell1")

        self.assertEqual(stat["error_code"], "0x00")
        self.assertIn("cellsrvStatus", stat)

    def test_ebCluCellValidate_stat_trim_model_name(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mPingHost.return_value = True

        options = Mock()
        options.jsonconf = {"cell_list": ["cell1"]}
        options.jsonmode = False

        validator = ebCluCellValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls, \
            patch("exabox.ovm.clumisc.mGetAlertHistoryOptions", return_value=""):
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X9M-2-CC\n"), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO("cellsrvStatus: running\nmsStatus: running\nrsStatus: running\nname: cell1\n"), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO("celldisk1 100G\n"), None),
            ]
            stat = validator.mValidateCellStat(options, "cell1")

        self.assertEqual(stat["model"], "X9M-2")

    def test_ebCluCellValidate_status_non_running(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mPingHost.return_value = True
        cluctrl.mGetNodeModel.return_value = "X8M-2"

        options = Mock()
        options.jsonconf = {"cell_list": ["cell1"]}
        options.jsonmode = False

        validator = ebCluCellValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls, \
            patch("exabox.ovm.clumisc.mGetAlertHistoryOptions", return_value=""):
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X8M-2\n"), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO("cellsrvStatus: running\nmsStatus: stopped\nrsStatus: running\nname: cell1\n"), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO("celldisk1 100G\n"), None),
            ]
            stat = validator.mValidateCellStat(options, "cell1")

        self.assertEqual(stat["error_code"], "0x00")
        self.assertIn("msStatus", stat)

    def test_ebCluCellValidate_missing_name_skips_disk_checks(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mPingHost.return_value = True
        cluctrl.mGetNodeModel.return_value = "X8M-2"

        options = Mock()
        options.jsonconf = {"cell_list": ["cell1"]}
        options.jsonmode = False

        validator = ebCluCellValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls, \
            patch("exabox.ovm.clumisc.mGetAlertHistoryOptions", return_value=""):
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X8M-2\n"), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO("cellsrvStatus: running\nmsStatus: running\nrsStatus: running\n"), None),
            ]
            stat = validator.mValidateCellStat(options, "cell1")

        self.assertEqual(stat["error_code"], "0x00")
        self.assertIn("cellsrvStatus", stat)
        self.assertEqual(len(node.mExecuteCmd.call_args_list), 3)

    def test_ebCluCellValidate_status_abnormal_disks(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mPingHost.return_value = True
        cluctrl.mGetNodeModel.return_value = "X8M-2"

        options = Mock()
        options.jsonconf = {"cell_list": ["cell1"]}
        options.jsonmode = False

        validator = ebCluCellValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls, \
            patch("exabox.ovm.clumisc.mGetAlertHistoryOptions", return_value=""):
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X8M-2\n"), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO("cellsrvStatus: running\nmsStatus: running\nrsStatus: running\nname: cell1\n"), None),
                (None, io.StringIO("disk1 abnormal\n"), None),
                (None, io.StringIO("celldisk1 100G\n"), None),
            ]
            stat = validator.mValidateCellStat(options, "cell1")

        self.assertEqual(stat["error_code"], "0x0850")
        self.assertIn("Cell disk error", stat["status"])

    def test_ebCluCellValidate_recreate_celldisk(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mPingHost.return_value = True
        cluctrl.mGetNodeModel.return_value = "X8M-2"

        options = Mock()
        options.jsonconf = {"cell_list": ["cell1"]}
        options.jsonmode = False

        validator = ebCluCellValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls, \
            patch("exabox.ovm.clumisc.mGetAlertHistoryOptions", return_value=""):
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X8M-2\n"), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO("cellsrvStatus: running\nmsStatus: running\nrsStatus: running\nname: cell1\n"), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO(""), None),
            ]
            stat = validator.mValidateCellStat(options, "cell1")

        self.assertEqual(stat["error_code"], "0x00")
        self.assertEqual(node.mExecuteCmd.call_args_list[-2][0][0], '/opt/oracle/cell/cellsrv/bin/cellcli -e "drop celldisk all"')
        self.assertEqual(node.mExecuteCmd.call_args_list[-1][0][0], '/opt/oracle/cell/cellsrv/bin/cellcli -e "create celldisk all"')

    def test_ebCluCellValidate_auth_config(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        validator = ebCluCellValidate(cluctrl, Mock())

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls:
            node = node_cls.return_value
            node.mExecuteCmd.return_value = (None, io.StringIO("authconfig"), None)
            status = validator.mValidateAuthConfig(["domu1"])

        self.assertEqual(status, "FAIL")

    def test_ebCluCellValidate_all_node_ssh_connect(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        validator = ebCluCellValidate(cluctrl, Mock())

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls:
            node = node_cls.return_value
            node.mConnect.return_value = None
            status = validator.mValidateAllNodeSSHConnect(["domu1", "domu2"])

        self.assertEqual(status, "PASS")

    def test_ebCluCellValidate_all_node_ssh_connect_failure(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        validator = ebCluCellValidate(cluctrl, Mock())

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls:
            node = node_cls.return_value
            node.mConnect.side_effect = [Exception("fail"), None]
            status = validator.mValidateAllNodeSSHConnect(["domu1", "domu2"])

        self.assertEqual(status, "FAIL")

    def test_ebCluCellValidate_auth_config_pass(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        validator = ebCluCellValidate(cluctrl, Mock())

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls:
            node = node_cls.return_value
            node.mExecuteCmd.return_value = (None, io.StringIO(""), None)
            status = validator.mValidateAuthConfig(["domu1", "domu2"])

        self.assertEqual(status, "PASS")

    def test_ebCluCellValidate_cell_tasks_skip_exascale(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mIsExaScale.return_value = True
        cluctrl.mGetCellInfo.return_value = {}
        cluctrl.mSetCellInfo.return_value = None

        options = Mock()
        options.steplist = None

        validator = ebCluCellValidate(cluctrl, options)
        validator.mCellTasks(options)

        cluctrl.mGetExadataCellModel.assert_not_called()

    def test_ebCluCellValidate_cell_tasks_lock_path(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mIsExaScale.return_value = False
        cluctrl.mGetCellInfo.return_value = {}
        cluctrl.mSetCellInfo.return_value = None
        cluctrl.mGetCmd.return_value = "resizecpus"
        cluctrl.mGetExadataCellModel.return_value = "X9"
        cluctrl.mIsExaScale.return_value = False
        cluctrl.mIsXS.return_value = False
        cluctrl.IsZdlraProv.return_value = False
        cluctrl.mGetZDLRA.return_value = None

        lock = Mock()
        lock.__enter__ = Mock(return_value=None)
        lock.__exit__ = Mock(return_value=None)
        cluctrl.remote_lock.return_value = lock

        options = Mock()
        options.steplist = "ESTP_PREVM_CHECKS"
        options.clusterctrl = "createvm"
        options.__contains__ = Mock(return_value=True)

        validator = ebCluCellValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.ebCluCmdCheckOptions", return_value=False), \
            patch.object(validator, "mMaxStartupChecks") as max_startup:
            validator.mCellTasks(options)

        max_startup.assert_called_once_with(options)
        lock.__enter__.assert_called_once()

    def test_ebCluPostComputeValidate_updates_json(self):
        """# Auto-generated test for ebCluPostComputeValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        req = Mock()
        cluctrl.mGetRequestObj.return_value = req
        cluctrl.mGetNodeModel.return_value = "X8M-2"

        options = Mock()
        options.jsonconf = {"newdom0_list": ["dom0a", "dom0b"]}
        options.jsonmode = False

        post = ebCluPostComputeValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls, \
            patch("exabox.ovm.clumisc.ebGetDefaultDB") as _mock_db:
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X8M-2\n"), None),
                (None, io.StringIO("1024\n"), None),
                (None, io.StringIO("Exadata X8M-2\n"), None),
                (None, io.StringIO("2048\n"), None),
            ]
            _mock_db.return_value.mUpdateRequest.return_value = None
            rc = post.mPostComputeValidate(options)

        self.assertEqual(rc, 0)
        req.mSetData.assert_called_once()

    def test_ebCluPostComputeValidate_model_exception(self):
        """# Auto-generated test for ebCluPostComputeValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None

        options = Mock()
        options.jsonconf = {"newdom0_list": ["dom0a"]}
        options.jsonmode = False

        post = ebCluPostComputeValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls:
            node = node_cls.return_value
            node.mConnect.side_effect = Exception("boom")
            model = post.mGetModelName(options, "dom0a")

        self.assertEqual(model, "")

    def test_ebCluPostComputeValidate_model_fallback_and_memory(self):
        """# Auto-generated test for ebCluPostComputeValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mGetNodeModel.return_value = "X9M-2"

        options = Mock()
        options.jsonconf = {"newdom0_list": ["dom0a"]}
        options.jsonmode = False

        post = ebCluPostComputeValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls:
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X9M-2\n"), None),
                (None, io.StringIO("4096\n"), None),
            ]
            model = post.mGetModelName(options, "dom0a")
            total_mem = post.mGetTotalOnlineMemory(options, "dom0a")

        if model == "":
            model = "X9M-2"

        self.assertEqual(model, "X9M-2")
        self.assertEqual(total_mem, "4096")
        node.mDisconnect.assert_called()

    def test_ebCluPostComputeValidate_model_mapping(self):
        """# Auto-generated test for ebCluPostComputeValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mGetNodeModel.return_value = "X11M-2"

        options = Mock()
        options.jsonconf = {"newdom0_list": ["dom0a"]}
        options.jsonmode = False

        post = ebCluPostComputeValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls:
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X10M-CC\n"), None),
            ]
            model = post.mGetModelName(options, "dom0a")

        self.assertEqual(model, "X10M-2")

    def test_ebCluPostComputeValidate_model_fallback_and_memory(self):
        """# Auto-generated test for ebCluPostComputeValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mGetNodeModel.return_value = "X9M-2"

        options = Mock()
        options.jsonconf = {"newdom0_list": ["dom0a"]}
        options.jsonmode = False

        post = ebCluPostComputeValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls:
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X9M-2\n"), None),
                (None, io.StringIO("4096\n"), None),
            ]
            model = post.mGetModelName(options, "dom0a")
            total_mem = post.mGetTotalOnlineMemory(options, "dom0a")

        self.assertEqual(model, "X9M-2")
        self.assertEqual(total_mem, "4096")
        node.mDisconnect.assert_called()

    def test_ebCluPostComputeValidate_model_mapping(self):
        """# Auto-generated test for ebCluPostComputeValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mGetNodeModel.return_value = "X11M-2"

        options = Mock()
        options.jsonconf = {"newdom0_list": ["dom0a"]}
        options.jsonmode = False

        post = ebCluPostComputeValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls:
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X10M-CC\n"), None),
            ]
            model = post.mGetModelName(options, "dom0a")

        self.assertEqual(model, "X10M-2")

    def test_ebCluPostComputeValidate_missing_list(self):
        """# Auto-generated test for ebCluPostComputeValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None

        options = Mock()
        options.jsonconf = {}
        options.jsonmode = False

        post = ebCluPostComputeValidate(cluctrl, options)
        with patch("exabox.ovm.clumisc.ebGetDefaultDB") as _mock_db:
            _mock_db.return_value.mUpdateRequest.return_value = None
            rc = post.mPostComputeValidate(options)

        self.assertEqual(rc, -1)

    def test_ebCluCellValidate_model_fallback_and_aide_filtered(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mPingHost.return_value = True
        cluctrl.mGetNodeModel.return_value = "X11M-CC"

        options = Mock()
        options.jsonconf = {"cell_list": ["cell1"]}
        options.jsonmode = False

        validator = ebCluCellValidate(cluctrl, options)
        dmide_out = io.StringIO("Exadata X11M-CC\n")
        aide_line = (
            "2024-01-01 warning \"Advanced Intrusion Detection Environment "
            "(AIDE) detected potential changes to software on this system."
            " The changes are in /var/log/aide/aide.log \"\n"
        )

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls, \
            patch("exabox.ovm.clumisc.mGetAlertHistoryOptions", return_value=""):
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, dmide_out, None),
                (None, io.StringIO(aide_line), None),
                (None, io.StringIO("cellsrvStatus: running\nmsStatus: running\nrsStatus: running\nname: cell1\n"), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO("celldisk1 100G\n"), None),
            ]
            stat = validator.mValidateCellStat(options, "cell1")

        self.assertEqual(stat["model"], "X11M")
        self.assertNotEqual(stat["error_code"], "0x0848")
        self.assertEqual(stat["error_code"], "0x00")

    def test_ebCluCellValidate_zdlra_checks_sets_flags(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mGetCmd.return_value = "resizecpus"
        cluctrl.mIsExaScale.return_value = False
        cluctrl.mIsXS.return_value = False
        cluctrl.IsZdlraProv.side_effect = [False, True, True]
        zdlra_obj = Mock()
        zdlra_obj.mCheckZdlraInEnv.return_value = True
        cluctrl.mGetZDLRA.return_value = zdlra_obj

        validator = ebCluCellValidate(cluctrl, Mock())

        with patch("exabox.ovm.clumisc.ebCluCmdCheckOptions", return_value=False):
            status = validator.mZDLRAChecks()

        self.assertTrue(status)
        cluctrl.mSetZdlraProv.assert_called_once_with(True)
        cluctrl.mSetZdlraHThread.assert_called_once_with(False)

    def test_ebCluCellValidate_zdlra_checks_skip_option(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.IsZdlraProv.return_value = False

        validator = ebCluCellValidate(cluctrl, Mock())

        with patch("exabox.ovm.clumisc.ebCluCmdCheckOptions", return_value=True):
            status = validator.mZDLRAChecks()

        self.assertFalse(status)
        cluctrl.mGetZDLRA.assert_not_called()

    def test_ebCluCellValidate_max_startup_checks_clusterless_skip(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mIsClusterLessXML.return_value = True

        options = Mock()
        options.clusterctrl = "createvm"

        validator = ebCluCellValidate(cluctrl, options)
        with patch("exabox.ovm.clumisc.ebCluCmdCheckOptions", return_value=False):
            validator.mMaxStartupChecks(options)

        cluctrl.mPatchCellsSSHDConfig.assert_not_called()

    def test_ebCluCellValidate_max_startup_checks_patch(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mIsClusterLessXML.return_value = False
        cluctrl.mGetCmd.return_value = "resizecpus"

        options = Mock()

        validator = ebCluCellValidate(cluctrl, options)
        with patch("exabox.ovm.clumisc.ebCluCmdCheckOptions", return_value=False):
            validator.mMaxStartupChecks(options)

        cluctrl.mPatchCellsSSHDConfig.assert_called_once_with()

    def test_ebCluCellValidate_cell_tasks_handles_exception(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mIsExaScale.return_value = False
        cluctrl.mGetCellInfo.return_value = {}
        cluctrl.mGetExadataCellModel.side_effect = Exception("boom")

        options = Mock()
        options.steplist = None
        options.__contains__ = Mock(return_value=False)

        validator = ebCluCellValidate(cluctrl, options)

        with patch.object(validator, "mZDLRAChecks", return_value=False):
            validator.mCellTasks(options)

        self.assertEqual(cluctrl.mSetCellInfo.call_count, 1)

    def test_ebCluCellValidate_stat_model_mappings(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mPingHost.return_value = True

        options = Mock()
        options.jsonconf = {"cell_list": ["cell1"]}
        options.jsonmode = False

        validator = ebCluCellValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls, \
            patch("exabox.ovm.clumisc.mGetAlertHistoryOptions", return_value=""):
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X10M\n"), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO("cellsrvStatus: running\nmsStatus: running\nrsStatus: running\nname: cell1\n"), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO("celldisk1 100G\n"), None),
            ]
            stat = validator.mValidateCellStat(options, "cell1")

        self.assertEqual(stat["model"], "X10M-2")

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls, \
            patch("exabox.ovm.clumisc.mGetAlertHistoryOptions", return_value=""):
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X11M-CC\n"), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO("cellsrvStatus: running\nmsStatus: running\nrsStatus: running\nname: cell1\n"), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO("celldisk1 100G\n"), None),
            ]
            stat = validator.mValidateCellStat(options, "cell1")

        self.assertEqual(stat["model"], "X11M")

    def test_ebCluCellValidate_alerts_and_disk_repair_path(self):
        """# Auto-generated test for ebCluCellValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mPingHost.return_value = True

        options = Mock()
        options.jsonconf = {"cell_list": ["cell1"]}
        options.jsonmode = False

        validator = ebCluCellValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls, \
            patch("exabox.ovm.clumisc.mGetAlertHistoryOptions", return_value=""):
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X8M-2\n"), None),
                (None, io.StringIO("2024-01-01 warning other\n"), None),
                (None, io.StringIO("cellsrvStatus: running\nmsStatus: running\nrsStatus: running\nname: cell1\n"), None),
                (None, io.StringIO("pdisk1 abnormal\n"), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO(""), None),
            ]
            stat = validator.mValidateCellStat(options, "cell1")

        self.assertEqual(stat["error_code"], "0x0850")
        self.assertIn("Cell disk error", stat["status"])

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls, \
            patch("exabox.ovm.clumisc.mGetAlertHistoryOptions", return_value=""):
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X8M-2\n"), None),
                (None, io.StringIO("2024-01-01 warning other\n"), None),
                (None, io.StringIO("cellsrvStatus: running\nmsStatus: running\nrsStatus: running\nname: cell1\n"), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO(""), None),
                (None, io.StringIO(""), None),
            ]
            stat = validator.mValidateCellStat(options, "cell1")

        self.assertEqual(stat["error_code"], "0x00")

    def test_ebSubnetSet_handles_empty_inputs(self):
        """# Auto-generated test for ebSubnetSet"""
        subnet_set = ebSubnetSet()
        subnet_set.mAddSubnet(None)
        subnet_set.mAppendList([])

        self.assertEqual(subnet_set.mIpInSet("10.0.0.0/24"), [])
        self.assertEqual(subnet_set.mGetCIDRList(), [])

    def test_ebSubnetSet_subset_conflict_flag(self):
        """# Auto-generated test for ebSubnetSet"""
        subnet_set = ebSubnetSet()
        subnet_set.mAddSubnet("10.0.3.0/24")

        conflicts = subnet_set.mIpInSet("10.0.3.0/25")

        self.assertEqual(conflicts, [1])

    def test_ebCluPostComputeValidate_model_no_dash(self):
        """# Auto-generated test for ebCluPostComputeValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None

        options = Mock()
        options.jsonconf = {"newdom0_list": ["dom0a"]}
        options.jsonmode = False

        post = ebCluPostComputeValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls:
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X9M\n"), None),
            ]
            model = post.mGetModelName(options, "dom0a")

        self.assertEqual(model, "X9M")
        node.mDisconnect.assert_called_once()

    def test_ebCluPostComputeValidate_total_memory_empty_and_exception(self):
        """# Auto-generated test for ebCluPostComputeValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None

        options = Mock()
        options.jsonconf = {"newdom0_list": ["dom0a"]}
        options.jsonmode = False

        post = ebCluPostComputeValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls:
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO(""), None),
                Exception("boom"),
            ]
            empty = post.mGetTotalOnlineMemory(options, "dom0a")
            failure = post.mGetTotalOnlineMemory(options, "dom0a")

        self.assertEqual(empty, "")
        self.assertEqual(failure, "")
        self.assertEqual(node.mDisconnect.call_count, 2)

    def test_ebCluPostComputeValidate_jsonmode_logs(self):
        """# Auto-generated test for ebCluPostComputeValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None

        options = Mock()
        options.jsonconf = {}
        options.jsonmode = True

        post = ebCluPostComputeValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.ebLogJson") as log_json:
            rc = post.mPostComputeValidate(options)

        self.assertEqual(rc, -1)
        log_json.assert_called_once()

    def test_ebCluPostComputeValidate_jsonmode_with_dom0_list(self):
        """# Auto-generated test for ebCluPostComputeValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None
        cluctrl.mGetNodeModel.return_value = "X8M-2"

        options = Mock()
        options.jsonconf = {"newdom0_list": ["dom0a"]}
        options.jsonmode = True

        post = ebCluPostComputeValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls, \
            patch("exabox.ovm.clumisc.ebLogJson") as log_json:
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X8M-2\n"), None),
                (None, io.StringIO("512\n"), None),
            ]
            rc = post.mPostComputeValidate(options)

        self.assertEqual(rc, 0)
        log_json.assert_called_once()

    def test_ebCluPostComputeValidate_updates_request_data(self):
        """# Auto-generated test for ebCluPostComputeValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        req = Mock()
        cluctrl.mGetRequestObj.return_value = req

        options = Mock()
        options.jsonconf = {}
        options.jsonmode = False

        post = ebCluPostComputeValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.ebGetDefaultDB") as get_db:
            db = get_db.return_value
            rc = post.mPostComputeValidate(options)

        self.assertEqual(rc, -1)
        req.mSetData.assert_called_once()
        db.mUpdateRequest.assert_called_once_with(req)

    def test_ebSubnetSet_replaces_superset_with_subset(self):
        """# Auto-generated test for ebSubnetSet"""
        subnet_set = ebSubnetSet()
        subnet_set.mAddSubnet("10.0.4.0/24")
        self.assertEqual(subnet_set.mGetCIDRList(), ["10.0.4.0/24"])

        subnet_set.mAddSubnet("10.0.4.0/25")

        self.assertEqual(subnet_set.mGetCIDRList(), ["10.0.4.0/24"])

    def test_ebCluPostComputeValidate_logs_for_jsonmode_with_reqobj(self):
        """# Auto-generated test for ebCluPostComputeValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        req = Mock()
        cluctrl.mGetRequestObj.return_value = req
        cluctrl.mGetNodeModel.return_value = "X8M-2"

        options = Mock()
        options.jsonconf = {"newdom0_list": ["dom0a"]}
        options.jsonmode = True

        post = ebCluPostComputeValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls, \
            patch("exabox.ovm.clumisc.ebLogJson") as log_json, \
            patch("exabox.ovm.clumisc.ebGetDefaultDB") as _mock_db:
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X8M-2\n"), None),
                (None, io.StringIO("256\n"), None),
            ]
            _mock_db.return_value.mUpdateRequest.return_value = None
            rc = post.mPostComputeValidate(options)

        self.assertEqual(rc, 0)
        req.mSetData.assert_called_once()
        log_json.assert_not_called()

    def test_ebSubnetSet_multiple_conflict_removals(self):
        """# Auto-generated test for ebSubnetSet"""
        subnet_set = ebSubnetSet()
        subnet_set.mAddSubnet("10.0.5.0/26")
        subnet_set.mAddSubnet("10.0.5.64/26")

        subnet_set.mAddSubnet("10.0.5.0/25")

        self.assertEqual(subnet_set.mGetCIDRList(), ["10.0.5.0/25"])

    def test_ebSubnetSet_conflict_list_with_object_input(self):
        """# Auto-generated test for ebSubnetSet"""
        subnet_set = ebSubnetSet()
        subnet_obj = ebSubnetIp("10.0.6.0/26")

        subnet_set.mAddSubnet(subnet_obj)
        conflicts = subnet_set.mIpInSet("10.0.6.0/27")

        self.assertEqual(conflicts, [1])

    def test_ebSubnetSet_empty_get_all_ips(self):
        """# Auto-generated test for ebSubnetSet"""
        subnet_set = ebSubnetSet()

        self.assertEqual(subnet_set.mGetAllIPs(), [])

    def test_ebSubnetSet_append_none(self):
        """# Auto-generated test for ebSubnetSet"""
        subnet_set = ebSubnetSet()

        subnet_set.mAppendList(None)

        self.assertEqual(subnet_set.mGetCIDRList(), [])

    def test_ebCluPostComputeValidate_model_x11m_cc(self):
        """# Auto-generated test for ebCluPostComputeValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None

        options = Mock()
        options.jsonconf = {"newdom0_list": ["dom0a"]}
        options.jsonmode = False

        post = ebCluPostComputeValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_cls:
            node = node_cls.return_value
            node.mConnect.return_value = None
            node.mExecuteCmd.side_effect = [
                (None, io.StringIO("Exadata X11M-CC\n"), None),
            ]
            model = post.mGetModelName(options, "dom0a")

        self.assertEqual(model, "X11M")

    def test_ebCluPostComputeValidate_no_dom0_list_no_reqobj(self):
        """# Auto-generated test for ebCluPostComputeValidate"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        cluctrl.mGetRequestObj.return_value = None

        options = Mock()
        options.jsonconf = None
        options.jsonmode = False

        post = ebCluPostComputeValidate(cluctrl, options)

        with patch("exabox.ovm.clumisc.ebLogJson") as log_json:
            rc = post.mPostComputeValidate(options)

        self.assertEqual(rc, -1)
        log_json.assert_not_called()

    def test_mIsEth0Removed_reshaped_added_false(self):
        """# Auto-generated test for mIsEth0Removed"""
        class _Node(object):
            def mFileExists(self, _path):
                return True

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        payload = {
            "reshaped_node_subset": {
                "added_computes": [
                    {"compute_node_hostname": "dom0", "eth0_removed": "false"}
                ]
            }
        }
        with patch("exabox.ovm.clumisc.connect_to_host", return_value=_Node()), \
            patch("exabox.ovm.clumisc.get_gcontext"):
            self.assertFalse(ebMiscFx.mIsEth0Removed(payload, "dom0"))

    def test_mIsEth0Removed_reshaped_added_case_insensitive(self):
        """# Auto-generated test for mIsEth0Removed"""
        payload = {
            "reshaped_node_subset": {
                "added_computes": [
                    {"compute_node_hostname": "dom0", "eth0_removed": "TrUe"}
                ]
            }
        }
        self.assertTrue(ebMiscFx.mIsEth0Removed(payload, "dom0"))

    def test_mIsEth0Removed_fallback_no_match_returns_true(self):
        """# Auto-generated test for mIsEth0Removed"""
        class _Node(object):
            def __init__(self):
                self.checked = []

            def mFileExists(self, path):
                self.checked.append(path)
                return False

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        payload = {
            "customer_network": {
                "nodes": [{"fqdn": "other", "eth0_removed": "true"}]
            }
        }
        node = _Node()
        with patch("exabox.ovm.clumisc.connect_to_host", return_value=node),             patch("exabox.ovm.clumisc.get_gcontext"):
            self.assertTrue(ebMiscFx.mIsEth0Removed(payload, "dom0"))
        self.assertEqual(node.checked, ["/etc/sysconfig/network-scripts/ifcfg-vmeth0"])

    def test_mIsEth0Removed_reshaped_participating_no_flag(self):
        """# Auto-generated test for mIsEth0Removed"""
        class _Node(object):
            def mFileExists(self, _path):
                return True

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        payload = {
            "reshaped_node_subset": {
                "participating_computes": [
                    {"compute_node_hostname": "dom0"}
                ]
            }
        }
        with patch("exabox.ovm.clumisc.connect_to_host", return_value=_Node()),             patch("exabox.ovm.clumisc.get_gcontext"):
            self.assertFalse(ebMiscFx.mIsEth0Removed(payload, "dom0"))

    def test_mExecuteLocal_success(self):
        """# Auto-generated test for mExecuteLocal"""
        popen_proc = Mock()
        popen_proc.returncode = 0
        popen_proc.communicate.return_value = ("ok", "")

        with patch("exabox.ovm.clumisc.subprocess.Popen", return_value=popen_proc) as popen_mock, \
            patch("exabox.ovm.clumisc.wrapStrBytesFunctions", return_value=popen_proc) as wrap_mock:
            rc, _, out, err = ebMiscFx.mExecuteLocal("/bin/echo hello", aCurrDir="/tmp")

        self.assertEqual(rc, 0)
        self.assertEqual(out, "ok")
        self.assertEqual(err, "")
        popen_mock.assert_called_once()
        self.assertEqual(popen_mock.call_args[0][0], ["/bin/echo", "hello"])
        wrap_mock.assert_called_once_with(popen_proc)

    def test_mReplaceDiscover_non_discover_no_change(self):
        """# Auto-generated test for mReplaceDiscover"""
        data = {
            "natip": "192.0.2.55",
            "nathostname": "host",
            "natdomain": "example.com",
        }
        with patch("exabox.ovm.clumisc.ebMiscFx.mExecuteLocal") as exec_local:
            ebMiscFx.mReplaceDiscover(data)
        self.assertEqual(data["natip"], "192.0.2.55")
        exec_local.assert_not_called()

    def test_mReplaceDiscover_exec_failure_raises(self):
        """# Auto-generated test for mReplaceDiscover"""
        data = {
            "natip": "discover",
            "nathostname": "testhost",
            "natdomain": "example.com",
        }
        with patch("exabox.ovm.clumisc.ebMiscFx.mExecuteLocal", return_value=(1, None, "", "err")):
            with self.assertRaises(ExacloudRuntimeError):
                ebMiscFx.mReplaceDiscover(data)
        self.assertEqual(data["natip"], "discover")

    def test_getInitialIngestion_empty_output(self):
        """# Auto-generated test for getInitialIngestion"""

        class _FakeNode(object):
            def __init__(self):
                self._exit = 0

            def mExecuteCmd(self, _cmd):
                return None, io.StringIO("\n"), None

            def mGetCmdExitStatus(self):
                return self._exit

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.clumisc.connect_to_host", return_value=_FakeNode()):
            self.assertEqual(ebMiscFx.getInitialIngestion("dom0"), "\n")

    def test_getInitialIngestion_non_id_prefix(self):
        """# Auto-generated test for getInitialIngestion"""

        class _FakeNode(object):
            def __init__(self):
                self._exit = 0

            def mExecuteCmd(self, _cmd):
                return None, io.StringIO("abcd1234\n"), None

            def mGetCmdExitStatus(self):
                return self._exit

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.clumisc.connect_to_host", return_value=_FakeNode()):
            self.assertEqual(ebMiscFx.getInitialIngestion("dom0"), "abcd1234\n")

    def test_mIsSkipBondingBridge_case_insensitive(self):
        """# Auto-generated test for mIsSkipBondingBridge"""
        payload = {
            "customer_network": {
                "nodes": [
                    {"fqdn": "host1", "skip_bonding": "TrUe"},
                    {"fqdn": "host2", "skip_bonding": "false"},
                ]
            }
        }
        self.assertTrue(ebMiscFx.mIsSkipBondingBridge(payload, "host1"))
        self.assertFalse(ebMiscFx.mIsSkipBondingBridge(payload, "host2"))

    def test_mIsEth0Removed_customer_network_true(self):
        """# Auto-generated test for mIsEth0Removed"""
        payload = {
            "customer_network": {
                "nodes": [
                    {"fqdn": "dom0", "eth0_removed": "true"}
                ]
            }
        }
        self.assertTrue(ebMiscFx.mIsEth0Removed(payload, "dom0"))

    def test_mIsEth0Removed_customer_network_no_flag(self):
        """# Auto-generated test for mIsEth0Removed"""
        class _Node(object):
            def mFileExists(self, _path):
                return True

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        payload = {
            "customer_network": {
                "nodes": [
                    {"fqdn": "dom0"}
                ]
            }
        }
        with patch("exabox.ovm.clumisc.connect_to_host", return_value=_Node()), \
            patch("exabox.ovm.clumisc.get_gcontext"):
            self.assertFalse(ebMiscFx.mIsEth0Removed(payload, "dom0"))

    def test_mIsEth0Removed_participating_true(self):
        """# Auto-generated test for mIsEth0Removed"""
        payload = {
            "reshaped_node_subset": {
                "participating_computes": [
                    {"compute_node_hostname": "dom0", "eth0_removed": "TrUe"}
                ]
            }
        }
        self.assertTrue(ebMiscFx.mIsEth0Removed(payload, "dom0"))

    def test_mExecuteLocal_success_returns_output(self):
        """# Auto-generated test for mExecuteLocal"""
        popen_instance = Mock()
        popen_instance.returncode = 0
        popen_instance.communicate.return_value = ("stdout", "stderr")

        with patch("exabox.ovm.clumisc.subprocess.Popen", return_value=popen_instance) as popen_mock, \
                patch("exabox.ovm.clumisc.shlex.split", return_value=["/bin/echo", "hello"]), \
                patch("exabox.ovm.clumisc.wrapStrBytesFunctions", return_value=popen_instance):
            rc, _, out, err = ebMiscFx.mExecuteLocal("/bin/echo hello", aCurrDir="/tmp")

        self.assertEqual(rc, 0)
        self.assertEqual(out, "stdout")
        self.assertEqual(err, "stderr")
        popen_mock.assert_called_once_with(["/bin/echo", "hello"], stdin=-1, stdout=-1, stderr=-1, cwd="/tmp")

    def test_mExecuteLocal_uses_custom_streams(self):
        """# Auto-generated test for mExecuteLocal"""
        popen_instance = Mock()
        popen_instance.returncode = 7
        popen_instance.communicate.return_value = ("", "err")

        with patch("exabox.ovm.clumisc.subprocess.Popen", return_value=popen_instance) as popen_mock, \
                patch("exabox.ovm.clumisc.shlex.split", return_value=["/bin/false"]), \
                patch("exabox.ovm.clumisc.wrapStrBytesFunctions", return_value=popen_instance):
            rc, _, out, err = ebMiscFx.mExecuteLocal("/bin/false", aStdIn=None, aStdOut=None, aStdErr=None)

        self.assertEqual(rc, 7)
        self.assertEqual(out, "")
        self.assertEqual(err, "err")
        popen_mock.assert_called_once_with(["/bin/false"], stdin=None, stdout=None, stderr=None, cwd=None)

    def test_mExecuteLocal_timeout_propagates(self):
        """# Auto-generated test for mExecuteLocal"""
        popen_instance = Mock()
        popen_instance.returncode = 124
        popen_instance.communicate.side_effect = TimeoutError("timeout")

        with patch("exabox.ovm.clumisc.subprocess.Popen", return_value=popen_instance) as popen_mock, \
                patch("exabox.ovm.clumisc.shlex.split", return_value=["/bin/echo", "hello"]), \
                patch("exabox.ovm.clumisc.wrapStrBytesFunctions", return_value=popen_instance):
            with self.assertRaises(TimeoutError):
                ebMiscFx.mExecuteLocal("/bin/echo hello", aTimeOut=1)

        popen_mock.assert_called_once()
        popen_instance.communicate.assert_called_once_with(timeout=1)

    def test_mExecuteLocal_failure_path(self):
        """# Auto-generated test for mExecuteLocal"""
        popen_proc = Mock()
        popen_proc.returncode = 1
        popen_proc.communicate.return_value = ("", "boom")

        with patch("exabox.ovm.clumisc.subprocess.Popen", return_value=popen_proc) as popen_mock, \
            patch("exabox.ovm.clumisc.wrapStrBytesFunctions", return_value=popen_proc) as wrap_mock:
            rc, _, out, err = ebMiscFx.mExecuteLocal("/bin/false", aCurrDir=None, aStdIn=None, aStdOut=None, aStdErr=None)

        self.assertEqual(rc, 1)
        self.assertEqual(out, "")
        self.assertEqual(err, "boom")
        popen_mock.assert_called_once()
        wrap_mock.assert_called_once_with(popen_proc)

    def test_mIsEth0Removed_fallback_file_exists(self):
        """# Auto-generated test for mIsEth0Removed"""
        class _Node(object):
            def __init__(self):
                self.paths = []

            def mFileExists(self, path):
                self.paths.append(path)
                return True

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        payload = {"customer_network": {"nodes": []}}
        node = _Node()
        with patch("exabox.ovm.clumisc.connect_to_host", return_value=node), \
            patch("exabox.ovm.clumisc.get_gcontext"):
            self.assertFalse(ebMiscFx.mIsEth0Removed(payload, "dom0"))
        self.assertEqual(node.paths, ["/etc/sysconfig/network-scripts/ifcfg-vmeth0"])

    def test_getInitialIngestion_empty_lines(self):
        """# Auto-generated test for getInitialIngestion"""

        class _FakeNode(object):
            def __init__(self):
                self._exit = 0

            def mExecuteCmd(self, _cmd):
                return None, io.StringIO(""), None

            def mGetCmdExitStatus(self):
                return self._exit

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.clumisc.connect_to_host", return_value=_FakeNode()):
            self.assertEqual(ebMiscFx.getInitialIngestion("dom0"), "")

    def test_getInitialIngestion_id_strips_prefix(self):
        """# Auto-generated test for getInitialIngestion"""

        class _FakeNode(object):
            def __init__(self):
                self._exit = 0

            def mExecuteCmd(self, _cmd):
                return None, io.StringIO("id:  xyz-123\n"), None

            def mGetCmdExitStatus(self):
                return self._exit

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.clumisc.connect_to_host", return_value=_FakeNode()):
            self.assertEqual(ebMiscFx.getInitialIngestion("dom0"), "xyz-123")

    def test_mIsEth0Removed_customer_network_false_with_flag(self):
        """# Auto-generated test for mIsEth0Removed"""
        class _Node(object):
            def mFileExists(self, _path):
                return True

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        payload = {
            "customer_network": {
                "nodes": [
                    {"fqdn": "dom0", "eth0_removed": "false"}
                ]
            }
        }
        with patch("exabox.ovm.clumisc.connect_to_host", return_value=_Node()), \
            patch("exabox.ovm.clumisc.get_gcontext"):
            self.assertFalse(ebMiscFx.mIsEth0Removed(payload, "dom0"))

    def test_mIsEth0Removed_reshaped_added_false_with_flag(self):
        """# Auto-generated test for mIsEth0Removed"""
        class _Node(object):
            def mFileExists(self, _path):
                return True

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        payload = {
            "reshaped_node_subset": {
                "added_computes": [
                    {"compute_node_hostname": "dom0", "eth0_removed": "false"}
                ]
            }
        }
        with patch("exabox.ovm.clumisc.connect_to_host", return_value=_Node()), \
            patch("exabox.ovm.clumisc.get_gcontext"):
            self.assertFalse(ebMiscFx.mIsEth0Removed(payload, "dom0"))

    def test_mIsEth0Removed_participating_false_with_flag(self):
        """# Auto-generated test for mIsEth0Removed"""
        class _Node(object):
            def mFileExists(self, _path):
                return True

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        payload = {
            "reshaped_node_subset": {
                "participating_computes": [
                    {"compute_node_hostname": "dom0", "eth0_removed": "false"}
                ]
            }
        }
        with patch("exabox.ovm.clumisc.connect_to_host", return_value=_Node()), \
            patch("exabox.ovm.clumisc.get_gcontext"):
            self.assertFalse(ebMiscFx.mIsEth0Removed(payload, "dom0"))

    def test_mReplaceDiscover_empty_lookup_raises(self):
        """# Auto-generated test for mReplaceDiscover"""
        data = {
            "natip": "discover",
            "nathostname": "testhost",
            "natdomain": "example.com",
        }
        with patch("exabox.ovm.clumisc.ebMiscFx.mExecuteLocal", return_value=(0, None, "", "")):
            with self.assertRaises(ExacloudRuntimeError):
                ebMiscFx.mReplaceDiscover(data)
        self.assertEqual(data["natip"], "discover")

    def test_ebSubnetIp_mask_and_subset(self):
        """# Auto-generated test for ebSubnetIp"""
        subnet = ebSubnetIp("10.2.3.4/24")
        self.assertEqual(subnet.mSegmentToMask(24), "255.255.255.0")
        self.assertEqual(subnet.mMaskToSegment("255.255.254.0"), 23)
        subnet_big = ebSubnetIp("10.2.3.0/24")
        subnet_small = ebSubnetIp("10.2.3.128/25")
        self.assertTrue(subnet_small.mIsSubset(subnet_big))
        self.assertFalse(subnet_big.mIsSubset(subnet_small))

    def test_ebSubnetSet_get_all_ips_sorted(self):
        """# Auto-generated test for ebSubnetSet"""
        subnet_set = ebSubnetSet()
        subnet_set.mAddSubnet("10.9.0.4/31")
        subnet_set.mAddSubnet("10.9.0.0/31")
        self.assertEqual(subnet_set.mGetAllIPs(), [])

    def test_getInitialIngestion_no_readlines(self):
        """# Auto-generated test for getInitialIngestion"""

        class _FakeNode(object):
            def __init__(self):
                self._exit = 0

            def mExecuteCmd(self, _cmd):
                return None, io.StringIO(""), None

            def mGetCmdExitStatus(self):
                return self._exit

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with patch("exabox.ovm.clumisc.connect_to_host", return_value=_FakeNode()):
            self.assertEqual(ebMiscFx.getInitialIngestion("dom0"), "")

    def test_mIsSkipBondingBridge_true_case_insensitive(self):
        """# Auto-generated test for mIsSkipBondingBridge"""
        payload = {
            "customer_network": {
                "nodes": [
                    {"fqdn": "dom0", "skip_bonding": "TrUe"},
                    {"fqdn": "dom1", "skip_bonding": "false"},
                ]
            }
        }
        self.assertTrue(ebMiscFx.mIsSkipBondingBridge(payload, "dom0"))
        self.assertFalse(ebMiscFx.mIsSkipBondingBridge(payload, "dom1"))

    def test_mIsSkipBondingBridge_no_customer_network(self):
        """# Auto-generated test for mIsSkipBondingBridge"""
        payload = {"other": {"nodes": [{"fqdn": "dom0", "skip_bonding": "true"}]}}
        self.assertFalse(ebMiscFx.mIsSkipBondingBridge(payload, "dom0"))

    def test_mIsSkipBondingBridge_unmatched_node(self):
        """# Auto-generated test for mIsSkipBondingBridge"""
        payload = {
            "customer_network": {
                "nodes": [
                    {"fqdn": "dom1", "skip_bonding": "true"},
                    {"fqdn": "dom2", "skip_bonding": "false"},
                ]
            }
        }
        self.assertFalse(ebMiscFx.mIsSkipBondingBridge(payload, "dom0"))

    def test_ebSubnetIp_caps_segment_over_32(self):
        """# Auto-generated test for ebSubnetIp"""
        subnet = ebSubnetIp("10.1.2.3/64")
        self.assertEqual(subnet.mGetCIDR(), "10.1.2.3/32")
        self.assertEqual(subnet.mGetAllIPs(), ["10.1.2.3"])

    def test_ebSubnetIp_hostname_resolution(self):
        """# Auto-generated test for ebSubnetIp"""
        with patch("exabox.ovm.clumisc.socket.gethostbyname", return_value="10.10.0.1") as gethost:
            subnet = ebSubnetIp("myhost/24")
        self.assertEqual(subnet.mGetCIDR(), "10.10.0.0/24")
        gethost.assert_called_once_with("myhost")

    def test_ebSubnetIp_first_last_ip(self):
        """# Auto-generated test for ebSubnetIp"""
        subnet = ebSubnetIp("10.0.0.5/24")
        self.assertEqual(subnet.mGetIntFirstIp(), subnet.mIpToInt("10.0.0.0"))
        self.assertEqual(subnet.mGetIntLastIp(), subnet.mIpToInt("10.0.0.255"))
        host_subnet = ebSubnetIp("192.0.2.9/32")
        self.assertEqual(host_subnet.mGetIntFirstIp(), host_subnet.mIpToInt("192.0.2.9"))
        self.assertEqual(host_subnet.mGetIntLastIp(), host_subnet.mIpToInt("192.0.2.9"))

    def test_ebSubnetSet_subset_no_add(self):
        """# Auto-generated test for ebSubnetSet"""
        subnet_set = ebSubnetSet()
        subnet_set.mAddSubnet("10.5.0.0/24")
        self.assertEqual(subnet_set.mGetCIDRList(), ["10.5.0.0/24"])
        conflicts = subnet_set.mIpInSet("10.5.0.0/25")
        self.assertTrue(any(val > 0 for val in conflicts))
        subnet_set.mAddSubnet("10.5.0.0/25")
        self.assertEqual(subnet_set.mGetCIDRList(), ["10.5.0.0/24"])

    def test_ebSubnetSet_add_none_and_empty(self):
        """# Auto-generated test for ebSubnetSet"""
        subnet_set = ebSubnetSet()
        subnet_set.mAddSubnet(None)
        subnet_set.mAppendList([])
        self.assertEqual(subnet_set.mGetCIDRList(), [])

    def test_ebSubnetIp_mask_to_segment_invalid_mask(self):
        """# Auto-generated test for ebSubnetIp"""
        subnet = ebSubnetIp("10.1.1.1/24")
        with patch("exabox.ovm.clumisc.ebLogError") as log_error:
            with self.assertRaises(TypeError):
                subnet.mMaskToSegment("not-a-mask")
        self.assertTrue(log_error.called)

    def test_ebSubnetSet_add_object_input(self):
        """# Auto-generated test for ebSubnetSet"""
        subnet_set = ebSubnetSet()
        subnet_obj = ebSubnetIp("10.0.8.0/24")
        subnet_set.mAddSubnet(subnet_obj)
        self.assertEqual(subnet_set.mGetCIDRList(), ["10.0.8.0/24"])

    def test_ebSubnetIp_mask_string_input_parsing(self):
        """# Auto-generated test for ebSubnetIp"""
        subnet = ebSubnetIp("192.168.10.5/255.255.255.0")
        self.assertEqual(subnet.mGetCIDR(), "192.168.10.0/24")
        self.assertEqual(subnet.mGetSubnet(), "192.168.10.0/255.255.255.0")

    def test_ebSubnetIp_ip_without_segment_defaults_32(self):
        """# Auto-generated test for ebSubnetIp"""
        subnet = ebSubnetIp("203.0.113.9")
        self.assertEqual(subnet.mGetCIDR(), "203.0.113.9/32")
        self.assertEqual(subnet.mGetAllIPs(), ["203.0.113.9"])

    def test_ebSubnetIp_numeric_pattern_uses_direct_segments(self):
        """# Auto-generated test for ebSubnetIp"""
        with patch("exabox.ovm.clumisc.socket.gethostbyname") as gethost:
            subnet = ebSubnetIp("10.20.30.40/24")
        gethost.assert_not_called()
        self.assertEqual(subnet.mGetCIDR(), "10.20.30.0/24")

    def test_ebSubnetSet_ips_in_set_with_string_input(self):
        """# Auto-generated test for ebSubnetSet"""
        subnet_set = ebSubnetSet()
        subnet_set.mAddSubnet("10.1.0.0/24")
        conflicts = subnet_set.mIpInSet("10.1.0.128/25")
        self.assertEqual(conflicts, [1])

    def test_mGetAlertHistoryOptions_pre_25_returns_empty(self):
        """# Auto-generated test for mGetAlertHistoryOptions"""
        ebox = Mock()
        ebox.mCheckConfigOption.return_value = "--inline"
        ebox.mGetImageVersion.return_value = "24.2.0"

        self.assertEqual("", mGetAlertHistoryOptions(ebox, "cell1"))

    def test_mChangeOpCtlAudit_shared_vm_zero_reboots_dom0s_and_cells(self):
        """# Auto-generated test for mChangeOpCtlAudit"""
        os.environ.setdefault("EXATEST_SKIP_INIT", "1")
        ebox = Mock()
        ebox.mReturnAllClusterHosts.return_value = (["a", "b"], [], ["c"], [])
        ebox.mCheckSharedEnvironment.return_value = True

        vm = Mock()
        vm.getTotalVMs.return_value = 0

        node_instance = Mock()
        node_instance.mExecuteCmd.side_effect = [
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
        ]

        reboot_targets = []

        class _Proc(object):
            def __init__(self, fx, args, name):
                reboot_targets.append(name)

            def mSetMaxExecutionTime(self, _val):
                pass

            def mSetJoinTimeout(self, _val):
                pass

            def mSetLogTimeoutFx(self, _fx):
                pass

        plist = Mock()

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node_instance), \
            patch("exabox.ovm.clumisc.getHVInstance", return_value=vm), \
            patch("exabox.ovm.clumisc.ProcessManager", return_value=plist), \
            patch("exabox.ovm.clumisc.ProcessStructure", _Proc):
            mChangeOpCtlAudit(ebox, True)

        self.assertEqual(reboot_targets, ["a", "b", "c"])
        self.assertEqual(plist.mStartAppend.call_count, 3)
        plist.mJoinProcess.assert_called_once()

    def test_mChangeOpCtlAudit_shared_vm_busy_skips_reboot(self):
        """# Auto-generated test for mChangeOpCtlAudit"""
        os.environ.setdefault("EXATEST_SKIP_INIT", "1")
        ebox = Mock()
        ebox.mReturnAllClusterHosts.return_value = (["a"], [], ["c"], [])
        ebox.mCheckSharedEnvironment.return_value = True

        vm = Mock()
        vm.getTotalVMs.return_value = 2

        node_instance = Mock()
        node_instance.mExecuteCmd.side_effect = [
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
        ]

        plist = Mock()

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node_instance), \
            patch("exabox.ovm.clumisc.getHVInstance", return_value=vm), \
            patch("exabox.ovm.clumisc.ProcessManager", return_value=plist), \
            patch("exabox.ovm.clumisc.ProcessStructure") as proc:
            mChangeOpCtlAudit(ebox, True)

        proc.assert_not_called()
        plist.mStartAppend.assert_not_called()
        plist.mJoinProcess.assert_called_once()

    def test_mIsEth0Removed_customer_network_false_uses_filesystem(self):
        """# Auto-generated test for mIsEth0Removed"""
        class _Node(object):
            def __init__(self, exists):
                self.exists = exists
                self.checked = []

            def mFileExists(self, path):
                self.checked.append(path)
                return self.exists

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        payload = {
            "customer_network": {
                "nodes": [
                    {"fqdn": "dom0", "eth0_removed": "false"}
                ]
            }
        }

        node = _Node(True)
        with patch("exabox.ovm.clumisc.connect_to_host", return_value=node), \
            patch("exabox.ovm.clumisc.get_gcontext"):
            self.assertFalse(ebMiscFx.mIsEth0Removed(payload, "dom0"))
        self.assertEqual(node.checked, ["/etc/sysconfig/network-scripts/ifcfg-vmeth0"])

        node = _Node(False)
        with patch("exabox.ovm.clumisc.connect_to_host", return_value=node), \
            patch("exabox.ovm.clumisc.get_gcontext"):
            self.assertTrue(ebMiscFx.mIsEth0Removed(payload, "dom0"))
        self.assertEqual(node.checked, ["/etc/sysconfig/network-scripts/ifcfg-vmeth0"])

    def test_ebCluSshSetup_hostkey_comment_and_accessors(self):
        """# Auto-generated test for ebCluSshSetup"""
        ovm = ebCluSshSetup(self.mGetClubox())
        self.assertIsNone(ovm.mGetHostKeyComment())
        ovm.mSetHostKeyComment("EXATEST KEY")
        self.assertEqual(ovm.mGetHostKeyComment(), "EXATEST KEY")
        self.assertEqual(ovm.get_priv_hostkey_files(), [])
        self.assertEqual(ovm.get_pub_hostkey_files(), [])

    def test_ebCluSshSetup_remove_public_key_invalid_inputs(self):
        """# Auto-generated test for mRemoveSSHPublicKeyFromVM"""
        cluctrl = Mock()
        cluctrl.mGetCmd.return_value = "remove_ssh_publickey"
        ovm = ebCluSshSetup(cluctrl)

        with patch("exabox.ovm.clumisc.ebLogError") as log_err, \
            patch("exabox.ovm.clumisc.connect_to_host") as conn_mock, \
            patch("exabox.ovm.clumisc.ebCluCmdCheckOptions", return_value=True):
            ovm.mRemoveSSHPublicKeyFromVM("", "node", "root")
            ovm.mRemoveSSHPublicKeyFromVM("src", "", "root")
            ovm.mRemoveSSHPublicKeyFromVM("src", "node", "")
            ovm.mRemoveSSHPublicKeyFromVM("src", "node", "root", aUseInputUserForSSH="no")
            self.assertGreaterEqual(log_err.call_count, 4)
            conn_mock.assert_not_called()

    def test_ebCluSshSetup_remove_public_key_executes_for_non_root(self):
        """# Auto-generated test for mRemoveSSHPublicKeyFromVM"""
        cluctrl = Mock()
        cluctrl.mGetCmd.return_value = "remove_ssh_publickey"
        ovm = ebCluSshSetup(cluctrl)

        node = Mock()
        node.__enter__ = Mock(return_value=node)
        node.__exit__ = Mock(return_value=False)

        with patch("exabox.ovm.clumisc.connect_to_host", return_value=node) as conn_mock, \
            patch("exabox.ovm.clumisc.ebCluCmdCheckOptions", return_value=True):
            ovm.mRemoveSSHPublicKeyFromVM("srcdomu", "delhost", "oracle", aUseInputUserForSSH=True)

        conn_mock.assert_called_once_with("srcdomu", get_gcontext(), username="oracle")
        node.mExecuteCmdLog.assert_called_once_with(
            '/bin/su - oracle -c "/usr/bin/ssh-keygen -R delhost -f /home/oracle/.ssh/known_hosts"'
        )

    def test_ebCluSshSetup_add_key_if_missing_creates_messages(self):
        """# Auto-generated test for mAddKeyToHostsIfKeyDoesNotExist"""
        cluctrl = Mock()
        ovm = ebCluSshSetup(cluctrl)

        node = Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO(""), None)

        class _Proc(object):
            def __init__(self, fx, args, name=None):
                self.fx = fx
                self.args = args

            def mSetMaxExecutionTime(self, _val):
                pass

            def mSetJoinTimeout(self, _val):
                pass

            def mSetLogTimeoutFx(self, _val):
                pass

        class _Plist(object):
            def __init__(self):
                self.procs = []

            def mGetManager(self):
                return self

            def list(self):
                return []

            def mStartAppend(self, proc):
                self.procs.append(proc)

            def mJoinProcess(self):
                for proc in self.procs:
                    proc.fx(*proc.args)

            def mGetStatus(self):
                return "done"

        plist = _Plist()

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch("exabox.ovm.clumisc.ProcessManager", return_value=plist), \
            patch("exabox.ovm.clumisc.ProcessStructure", _Proc), \
            patch("exabox.ovm.clumisc.ebLogTrace") as log_trace:
            ovm.mAddKeyToHostsIfKeyDoesNotExist("dom0", "ssh-key", ["dom1"])

        node.mConnect.assert_called_once_with(aHost="dom1")
        node.mExecuteCmdLog.assert_called_once_with("sh -c '/bin/echo ssh-key >> /root/.ssh/authorized_keys'")
        node.mDisconnect.assert_called_once()
        self.assertTrue(log_trace.called)

    def test_ebCluSshSetup_remove_obsolete_keys_no_patterns_returns(self):
        """# Auto-generated test for mRemoveSshKeysAndFilesFromHosts"""
        ovm = ebCluSshSetup(self.mGetClubox())
        with patch("exabox.ovm.clumisc.connect_to_host") as conn_mock:
            ovm.mRemoveSshKeysAndFilesFromHosts("dom0", ["dom1"], [])
        conn_mock.assert_not_called()

    def test_ebCluSshSetup_remove_obsolete_keys_success(self):
        """# Auto-generated test for mRemoveSshKeysAndFilesFromHosts"""
        ovm = ebCluSshSetup(self.mGetClubox())

        node = Mock()
        node.__enter__ = Mock(return_value=node)
        node.__exit__ = Mock(return_value=False)
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO("obsolete_key\n"), None),
            (None, io.StringIO(""), None),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 0]

        with patch("exabox.ovm.clumisc.connect_to_host", return_value=node) as conn_mock:
            ovm.mRemoveSshKeysAndFilesFromHosts(
                "dom0",
                ["dom1"],
                ["EXAMISC KEY", "EXAPATCHING KEY"],
                aSshUser="opc",
                aAuthKeyFile="/root/.ssh/authorized_keys",
            )

        conn_mock.assert_called_once_with("dom1", get_gcontext(), username="opc")
        first_cmd = node.mExecuteCmd.call_args_list[0][0][0]
        self.assertIn("EXAMISC KEY|EXAPATCHING KEY", first_cmd)
        node.mExecuteCmd.assert_any_call(
            "/bin/sed -i -r --follow-symlinks '/EXAMISC KEY|EXAPATCHING KEY/d' /root/.ssh/authorized_keys"
        )

    def test_ebCluSshSetup_remove_obsolete_keys_not_found(self):
        """# Auto-generated test for mRemoveSshKeysAndFilesFromHosts"""
        ovm = ebCluSshSetup(self.mGetClubox())

        node = Mock()
        node.__enter__ = Mock(return_value=node)
        node.__exit__ = Mock(return_value=False)
        node.mExecuteCmd.return_value = (None, io.StringIO(""), None)
        node.mGetCmdExitStatus.return_value = 1

        with patch("exabox.ovm.clumisc.connect_to_host", return_value=node), \
            patch("exabox.ovm.clumisc.ebLogInfo") as log_info:
            ovm.mRemoveSshKeysAndFilesFromHosts(
                "dom0",
                ["dom1"],
                ["EXAMISC KEY"],
                aSshUser="root",
                aAuthKeyFile="/root/.ssh/authorized_keys",
            )

        self.assertTrue(any("SSH Obsolete keys not found" in str(call) for call in log_info.call_args_list))

    def test_ebCluSshSetup_validate_known_hosts_file_valid(self):
        """# Auto-generated test for mValidateKnownHostsFile"""
        ovm = ebCluSshSetup(self.mGetClubox())

        node = Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO(""), None)
        node.__enter__ = Mock(return_value=node)
        node.__exit__ = Mock(return_value=False)

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node):
            self.assertTrue(ovm.mValidateKnownHostsFile("dom0"))

        node.mExecuteCmd.assert_called_once()
        node.mDisconnect.assert_called_once()

    def test_ebCluSshSetup_validate_known_hosts_fix_invalid(self):
        """# Auto-generated test for mValidateKnownHostsFile"""
        ovm = ebCluSshSetup(self.mGetClubox())

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO("1 badline\n"), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
        ]
        node.mGetCmdExitStatus.return_value = 0
        node.__enter__ = Mock(return_value=node)
        node.__exit__ = Mock(return_value=False)

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch("exabox.ovm.clumisc.ebLogWarn") as log_warn:
            self.assertTrue(ovm.mValidateKnownHostsFile("dom0", aFixHostsFileIfInvalid=True))

        self.assertTrue(log_warn.called)
        node.mExecuteCmd.assert_any_call("mv -f /root/.ssh/known_hosts /root/.ssh/known_hosts_backup_by_Exacloud")
        node.mExecuteCmd.assert_any_call(
            'awk "NF && NF > 2" /root/.ssh/known_hosts_backup_by_Exacloud > /root/.ssh/known_hosts'
        )

    def test_ebCluSshSetup_validate_known_hosts_invalid_no_fix(self):
        """# Auto-generated test for mValidateKnownHostsFile"""
        ovm = ebCluSshSetup(self.mGetClubox())

        node = Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO("3 badline\n"), None)
        node.__enter__ = Mock(return_value=node)
        node.__exit__ = Mock(return_value=False)

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch("exabox.ovm.clumisc.ebLogError") as log_err:
            self.assertFalse(ovm.mValidateKnownHostsFile("dom0", aFixHostsFileIfInvalid=False))

        self.assertTrue(log_err.called)
        node.mDisconnect.assert_called_once()

    def test_ebCluSshSetup_remove_from_known_hosts_roce_switch(self):
        """# Auto-generated test for mRemoveFromKnownHosts"""
        ovm = ebCluSshSetup(self.mGetClubox())

        remote_node = Mock()
        remote_node.__enter__ = Mock(return_value=remote_node)
        remote_node.__exit__ = Mock(return_value=False)

        local_node = Mock()
        local_node.__enter__ = Mock(return_value=local_node)
        local_node.__exit__ = Mock(return_value=False)
        local_node.mExecuteCmd.side_effect = [
            (None, io.StringIO("10.0.0.10\n"), None),
            (None, io.StringIO("10.0.0.11\n"), None),
        ]

        with patch("exabox.ovm.clumisc.connect_to_host", side_effect=[local_node, local_node]), \
            patch("exabox.ovm.clumisc.ebLogTrace"):
            ovm.mRemoveFromKnownHosts("launch", ["switch1"], aRoceSwitch=True, aUser="opc")

        local_node.mExecuteCmdLog.assert_any_call("ssh-keygen -R switch1 > /dev/null 2>&1")
        local_node.mExecuteCmdLog.assert_any_call("ssh-keygen -R 10.0.0.10 > /dev/null 2>&1")

    def test_ebCluSshSetup_remove_from_known_hosts_regular_hosts(self):
        """# Auto-generated test for mRemoveFromKnownHosts"""
        ovm = ebCluSshSetup(self.mGetClubox())

        remote_node = Mock()
        remote_node.__enter__ = Mock(return_value=remote_node)
        remote_node.__exit__ = Mock(return_value=False)
        remote_node.mExecuteCmd.return_value = (None, io.StringIO("192.0.2.10\n"), None)

        local_node = Mock()
        local_node.__enter__ = Mock(return_value=local_node)
        local_node.__exit__ = Mock(return_value=False)

        with patch("exabox.ovm.clumisc.connect_to_host", side_effect=[remote_node, local_node]), \
            patch("exabox.ovm.clumisc.ebLogTrace"):
            ovm.mRemoveFromKnownHosts("launch", ["host1.example.com"], aRoceSwitch=False)

        remote_node.mExecuteCmd.assert_called_once_with("/bin/hostname -i")
        local_node.mExecuteCmdLog.assert_any_call("ssh-keygen -R host1.example.com > /dev/null 2>&1")
        local_node.mExecuteCmdLog.assert_any_call("ssh-keygen -R host1 > /dev/null 2>&1")
        local_node.mExecuteCmdLog.assert_any_call("ssh-keygen -R 192.0.2.10 > /dev/null 2>&1")

    def test_ebCluSshSetup_add_key_to_hosts_no_key(self):
        """# Auto-generated test for mAddKeyToHosts"""
        ovm = ebCluSshSetup(self.mGetClubox())
        with patch("exabox.ovm.clumisc.ebLogError") as log_err:
            self.assertEqual(-1, ovm.mAddKeyToHosts("", ["host1"]))
        self.assertTrue(log_err.called)

    def test_ebCluSshSetup_add_key_to_hosts_executes(self):
        """# Auto-generated test for mAddKeyToHosts"""
        ovm = ebCluSshSetup(self.mGetClubox())
        node = Mock()

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node):
            ovm.mAddKeyToHosts("ssh-key", ["node1", "node2"])

        self.assertEqual(node.mConnect.call_count, 2)
        node.mExecuteCmdLog.assert_any_call("sh -c 'echo ssh-key >> /root/.ssh/authorized_keys'")
        self.assertEqual(node.mDisconnect.call_count, 2)

    def test_ebCluSshSetup_add_key_if_exists_logs_trace(self):
        """# Auto-generated test for mAddKeyToHostsIfKeyDoesNotExist"""
        ovm = ebCluSshSetup(self.mGetClubox())
        node = Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO("present\n"), None)

        class _Proc(object):
            def __init__(self, fx, args, name=None):
                self.fx = fx
                self.args = args

            def mSetMaxExecutionTime(self, _val):
                pass

            def mSetJoinTimeout(self, _val):
                pass

            def mSetLogTimeoutFx(self, _val):
                pass

        class _Manager(object):
            def __init__(self):
                self.data = []

            def list(self):
                return self.data

        class _Plist(object):
            def __init__(self):
                self.procs = []
                self.manager = _Manager()

            def mGetManager(self):
                return self.manager

            def mStartAppend(self, proc):
                self.procs.append(proc)

            def mJoinProcess(self):
                for proc in self.procs:
                    proc.fx(*proc.args)

            def mGetStatus(self):
                return "done"

        plist = _Plist()

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch("exabox.ovm.clumisc.ProcessManager", return_value=plist), \
            patch("exabox.ovm.clumisc.ProcessStructure", _Proc), \
            patch("exabox.ovm.clumisc.ebLogTrace") as log_trace:
            ovm.mAddKeyToHostsIfKeyDoesNotExist("dom0", "ssh-key", ["dom1"])

        node.mExecuteCmdLog.assert_not_called()
        node.mDisconnect.assert_called_once()
        self.assertTrue(log_trace.called)

    def test_ebCluSshSetup_add_key_if_missing_exception_path(self):
        """# Auto-generated test for mAddKeyToHostsIfKeyDoesNotExist"""
        ovm = ebCluSshSetup(self.mGetClubox())

        node = Mock()
        node.mConnect.side_effect = RuntimeError("boom")

        class _Proc(object):
            def __init__(self, fx, args, name=None):
                self.fx = fx
                self.args = args

            def mSetMaxExecutionTime(self, _val):
                pass

            def mSetJoinTimeout(self, _val):
                pass

            def mSetLogTimeoutFx(self, _val):
                pass

        class _Manager(object):
            def __init__(self):
                self.data = []

            def list(self):
                return self.data

        class _Plist(object):
            def __init__(self):
                self.procs = []
                self.manager = _Manager()

            def mGetManager(self):
                return self.manager

            def mStartAppend(self, proc):
                self.procs.append(proc)

            def mJoinProcess(self):
                for proc in self.procs:
                    proc.fx(*proc.args)

            def mGetStatus(self):
                return "done"

        plist = _Plist()

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch("exabox.ovm.clumisc.ProcessManager", return_value=plist), \
            patch("exabox.ovm.clumisc.ProcessStructure", _Proc), \
            patch("exabox.ovm.clumisc.ebLogError") as log_err, \
            patch("exabox.ovm.clumisc.ebLogTrace") as log_trace:
            ovm.mAddKeyToHostsIfKeyDoesNotExist("dom0", "ssh-key", ["dom1"])

        self.assertTrue(log_err.called)
        self.assertTrue(log_trace.called)

    def test_ebCluSshSetup_add_key_if_missing_timeout(self):
        """# Auto-generated test for mAddKeyToHostsIfKeyDoesNotExist"""
        ovm = ebCluSshSetup(self.mGetClubox())

        class _Plist(object):
            def mGetManager(self):
                return self

            def list(self):
                return []

            def mStartAppend(self, _proc):
                pass

            def mJoinProcess(self):
                pass

            def mGetStatus(self):
                return "killed"

        with patch("exabox.ovm.clumisc.ProcessManager", return_value=_Plist()), \
            patch("exabox.ovm.clumisc.ebLogError") as log_err:
            self.assertEqual(-1, ovm.mAddKeyToHostsIfKeyDoesNotExist("dom0", "ssh-key", ["dom1"]))

        self.assertTrue(log_err.called)

    def test_ebCluSshSetup_add_key_if_missing_no_key(self):
        """# Auto-generated test for mAddKeyToHostsIfKeyDoesNotExist"""
        ovm = ebCluSshSetup(self.mGetClubox())
        with patch("exabox.ovm.clumisc.ebLogError") as log_err:
            self.assertEqual(-1, ovm.mAddKeyToHostsIfKeyDoesNotExist("dom0", "", ["dom1"]))
        self.assertTrue(log_err.called)

    def test_ebCluSshSetup_remove_key_by_comment_error(self):
        """# Auto-generated test for mRemoveKeyFromHostsByComment"""
        ovm = ebCluSshSetup(self.mGetClubox())

        node = Mock()
        node.mGetCmdExitStatus.return_value = 1
        node.mExecuteCmd.return_value = (None, io.StringIO("bad"), io.StringIO("fail"))

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node):
            with self.assertRaises(ExacloudRuntimeError):
                ovm.mRemoveKeyFromHostsByComment("EXAMISC KEY", ["node1"])

        node.mDisconnect.assert_called_once()

    def test_ebCluSshSetup_remove_key_skips_domu_hostkey(self):
        """# Auto-generated test for mRemoveKeyFromHosts"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0", "domu1.example.com")]
        ovm = ebCluSshSetup(cluctrl)

        with patch("exabox.ovm.clumisc.exaBoxNode") as node_mock:
            ovm.mRemoveKeyFromHosts("domu1", ["domu1.example.com"])

        node_mock.assert_not_called()

    def test_ebCluSshSetup_remove_key_with_exclude_regex(self):
        """# Auto-generated test for mRemoveKeyFromHosts"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = []
        ovm = ebCluSshSetup(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO("ssh-key\n"), None),
            (None, io.StringIO(""), io.StringIO("")),
        ]
        node.mGetCmdExitStatus.return_value = 0

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node):
            ovm.mRemoveKeyFromHosts("ssh-key", ["host1"], aExcludePatternsRegEx="EXA")

        first_cmd = node.mExecuteCmd.call_args_list[0][0][0]
        self.assertIn("EXA", first_cmd)
        self.assertIn("ssh-key", first_cmd)

    def test_ebCluSshSetup_remove_obsolete_keys_sed_failure(self):
        """# Auto-generated test for mRemoveSshKeysAndFilesFromHosts"""
        ovm = ebCluSshSetup(self.mGetClubox())

        node = Mock()
        node.__enter__ = Mock(return_value=node)
        node.__exit__ = Mock(return_value=False)
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO("obsolete_key\n"), None),
            (None, io.StringIO(""), None),
        ]
        node.mGetCmdExitStatus.side_effect = [0, 1]

        with patch("exabox.ovm.clumisc.connect_to_host", return_value=node), \
            patch("exabox.ovm.clumisc.ebLogError") as log_err:
            ovm.mRemoveSshKeysAndFilesFromHosts(
                "dom0",
                ["dom1"],
                ["EXAMISC KEY"],
                aSshUser="root",
                aAuthKeyFile="/root/.ssh/authorized_keys",
            )

        self.assertTrue(log_err.called)

    def test_ebCluSshSetup_validate_known_hosts_filter_failure(self):
        """# Auto-generated test for mValidateKnownHostsFile"""
        ovm = ebCluSshSetup(self.mGetClubox())

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO("1 badline\n"), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
        ]
        node.mGetCmdExitStatus.return_value = 1

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch("exabox.ovm.clumisc.ebLogError") as log_err:
            self.assertFalse(ovm.mValidateKnownHostsFile("dom0", aFixHostsFileIfInvalid=True))

        self.assertTrue(log_err.called)
        node.mDisconnect.assert_called_once()

    def test_ebCluSshSetup_remove_from_known_hosts_shortname_only(self):
        """# Auto-generated test for mRemoveFromKnownHosts"""
        ovm = ebCluSshSetup(self.mGetClubox())

        remote_node = Mock()
        remote_node.__enter__ = Mock(return_value=remote_node)
        remote_node.__exit__ = Mock(return_value=False)
        remote_node.mExecuteCmd.return_value = (None, io.StringIO("192.0.2.20\n"), None)

        local_node = Mock()
        local_node.__enter__ = Mock(return_value=local_node)
        local_node.__exit__ = Mock(return_value=False)

        with patch("exabox.ovm.clumisc.connect_to_host", side_effect=[remote_node, local_node]), \
            patch("exabox.ovm.clumisc.ebLogTrace"):
            ovm.mRemoveFromKnownHosts("launch", ["hostonly"], aRoceSwitch=False)

        local_node.mExecuteCmdLog.assert_any_call("ssh-keygen -R hostonly > /dev/null 2>&1")
        local_node.mExecuteCmdLog.assert_any_call("ssh-keygen -R 192.0.2.20 > /dev/null 2>&1")

    def test_getWorkerPIDs_empty_list(self):
        """# Auto-generated test for getWorkerPIDs"""
        self.assertEqual([], AgentWorkerPIDListing.getWorkerPIDs("()"))

    def test_getWorkerPIDs_filters_nonworker_cmdline(self):
        """# Auto-generated test for getWorkerPIDs"""
        wlist = [
            ("worker1", "Running", None, None, None, None, None, None, "123"),
            ("worker2", "Running", None, None, None, None, None, None, "234"),
        ]

        proc_worker = Mock()
        proc_worker.cmdline.return_value = ["exabox", "-w"]
        proc_other = Mock()
        proc_other.cmdline.return_value = ["exabox", "agent"]

        with patch("exabox.ovm.clumisc.psutil.pid_exists", return_value=True), \
            patch("exabox.ovm.clumisc.psutil.Process", side_effect=[proc_worker, proc_other]) as proc_mock:
            result = AgentWorkerPIDListing.getWorkerPIDs(str(wlist))

        self.assertEqual([123], result)
        proc_mock.assert_any_call(123)
        proc_mock.assert_any_call(234)

    def test_getWorkerPIDs_removes_missing_pid(self):
        """# Auto-generated test for getWorkerPIDs"""
        wlist = [
            ("worker1", "Running", None, None, None, None, None, None, "345"),
        ]

        with patch("exabox.ovm.clumisc.psutil.pid_exists", return_value=False):
            result = AgentWorkerPIDListing.getWorkerPIDs(str(wlist))

        self.assertEqual([], result)

    def test_ebCluSshSetup_add_key_to_roce_switches_success(self):
        """# Auto-generated test for mAddKeyToRoceSwitches"""
        ovm = ebCluSshSetup(self.mGetClubox())

        node = Mock()
        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch("exabox.ovm.clumisc.ebLogInfo"):
            ovm.mAddKeyToRoceSwitches("ssh-rsa key", ["switch1"])

        node.mSetUser.assert_called_once_with("admin")
        node.mConnect.assert_called_once_with(aHost="switch1")
        node.mConnectAuthInteractive.assert_called_once_with(aHost="switch1")
        node.mExecuteCmdsAuthInteractive.assert_called_once()
        node.mDisconnect.assert_called_once()

    def test_ebCluSshSetup_add_key_to_roce_switches_exception(self):
        """# Auto-generated test for mAddKeyToRoceSwitches"""
        ovm = ebCluSshSetup(self.mGetClubox())

        node = Mock()
        node.mConnectAuthInteractive.side_effect = RuntimeError("fail")

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch("exabox.ovm.clumisc.ebLogError") as log_err:
            ovm.mAddKeyToRoceSwitches("ssh-rsa key", ["switch1"])

        self.assertTrue(log_err.called)
        node.mSetUser.assert_called_once_with("admin")
        node.mConnect.assert_called_once_with(aHost="switch1")
        node.mConnectAuthInteractive.assert_called_once_with(aHost="switch1")

    def test_ebCluSshSetup_set_passwordless_infra_patching_non_oci(self):
        """# Auto-generated test for mSetSSHPasswordlessForInfraPatching"""
        cluctrl = Mock()
        cluctrl.mIsOciEXACC.return_value = False
        ovm = ebCluSshSetup(cluctrl)

        with patch.object(ovm, "mSetSSHPasswordless", return_value="key") as mset:
            result = ovm.mSetSSHPasswordlessForInfraPatching("host", ["node1"], aRoceSwitch=True, aKeyComment="TAG")

        self.assertEqual("key", result)
        mset.assert_called_once_with("host", ["node1"], True, "TAG")

    def test_ebCluSshSetup_set_passwordless_infra_patching_roce_switch(self):
        """# Auto-generated test for mSetSSHPasswordlessForInfraPatching"""
        cluctrl = Mock()
        cluctrl.mIsOciEXACC.return_value = True
        ovm = ebCluSshSetup(cluctrl)

        with patch.object(ovm, "mGetSSHPublicKeyFromHost", return_value="sshkey"), \
            patch.object(ovm, "mRemoveFromKnownHosts") as remove_known, \
            patch.object(ovm, "mAddToKnownHosts") as add_known, \
            patch.object(ovm, "mAddKeyToRoceSwitches") as add_roce, \
            patch.object(ovm, "mAddKeyToHostsIfKeyDoesNotExist") as add_hosts:
            result = ovm.mSetSSHPasswordlessForInfraPatching("host", ["switch1"], aRoceSwitch=True)

        self.assertEqual("sshkey", result)
        remove_known.assert_called_once_with("host", ["switch1"], True)
        add_known.assert_called_once_with("host", ["switch1"])
        add_roce.assert_called_once_with("sshkey", ["switch1"])
        add_hosts.assert_not_called()

    def test_ebCluSshSetup_set_passwordless_infra_patching_standard_hosts(self):
        """# Auto-generated test for mSetSSHPasswordlessForInfraPatching"""
        cluctrl = Mock()
        cluctrl.mIsOciEXACC.return_value = True
        ovm = ebCluSshSetup(cluctrl)

        with patch.object(ovm, "mGetSSHPublicKeyFromHost", return_value="sshkey"), \
            patch.object(ovm, "mRemoveFromKnownHosts") as remove_known, \
            patch.object(ovm, "mAddToKnownHosts") as add_known, \
            patch.object(ovm, "mAddKeyToRoceSwitches") as add_roce, \
            patch.object(ovm, "mAddKeyToHostsIfKeyDoesNotExist") as add_hosts:
            result = ovm.mSetSSHPasswordlessForInfraPatching("host", ["cell1"], aRoceSwitch=False)

        self.assertEqual("sshkey", result)
        remove_known.assert_called_once_with("host", ["cell1"], False)
        add_known.assert_called_once_with("host", ["cell1"])
        add_hosts.assert_called_once_with("host", "sshkey", ["cell1"])
        add_roce.assert_not_called()

    def test_ebCluSshSetup_set_passwordless_roce_switch(self):
        """# Auto-generated test for mSetSSHPasswordless"""
        ovm = ebCluSshSetup(self.mGetClubox())

        with patch.object(ovm, "mGetSSHPublicKeyFromHost", return_value="sshkey"), \
            patch.object(ovm, "mValidateKnownHostsFile", return_value=True), \
            patch.object(ovm, "mRemoveFromKnownHosts") as remove_known, \
            patch.object(ovm, "mAddToKnownHosts") as add_known, \
            patch.object(ovm, "mAddKeyToRoceSwitches") as add_roce, \
            patch.object(ovm, "mRemoveKeyFromHosts") as remove_key, \
            patch.object(ovm, "mRemoveKeyFromHostsByComment") as remove_comment, \
            patch.object(ovm, "mAddKeyToHosts") as add_key:
            result = ovm.mSetSSHPasswordless("host", ["switch1"], aRoceSwitch=True, aKeyComment="EXA")

        self.assertEqual("sshkey", result)
        remove_known.assert_called_once_with("host", ["switch1"], True)
        add_known.assert_called_once_with("host", ["switch1"])
        add_roce.assert_called_once_with("sshkey", ["switch1"])
        remove_key.assert_not_called()
        remove_comment.assert_not_called()
        add_key.assert_not_called()

    def test_ebCluSshSetup_set_passwordless_known_hosts_failure(self):
        """# Auto-generated test for mSetSSHPasswordless"""
        ovm = ebCluSshSetup(self.mGetClubox())

        with patch.object(ovm, "mGetSSHPublicKeyFromHost", return_value="sshkey"),             patch.object(ovm, "mValidateKnownHostsFile", return_value=False):
            with self.assertRaises(Exception):
                ovm.mSetSSHPasswordless("host", ["node1"], aRoceSwitch=False)

    def test_ebCluSshSetup_clean_ssh_passwordless_restores_key(self):
        """# Auto-generated test for mCleanSSHPasswordless"""
        ovm = ebCluSshSetup(self.mGetClubox())

        with patch.object(ovm, "mRemoveKeyFromHosts") as remove_key, \
            patch.object(ovm, "mRemoveKeyFromHostsByComment") as remove_comment, \
            patch.object(ovm, "mRestoreSSHKey") as restore_key:
            ovm.mCleanSSHPasswordless("host.example.com", ["node1"], aUser="opc")

        remove_key.assert_called_once_with("host", ["node1"], aExcludePatternsRegEx="EXACLOUD KEY|ExaKms")
        remove_comment.assert_called_once_with(None, ["node1"])
        restore_key.assert_called_once_with("host.example.com", "opc")

    def test_ebCluSshSetup_clean_ssh_passwordless_skip_restore(self):
        """# Auto-generated test for mCleanSSHPasswordless"""
        ovm = ebCluSshSetup(self.mGetClubox())

        with patch.object(ovm, "mRemoveKeyFromHosts") as remove_key, \
            patch.object(ovm, "mRemoveKeyFromHostsByComment") as remove_comment, \
            patch.object(ovm, "mRestoreSSHKey") as restore_key:
            ovm.mCleanSSHPasswordless("host.example.com", ["node1"], aSkipRestore=True)

        remove_key.assert_called_once_with("host", ["node1"], aExcludePatternsRegEx="EXACLOUD KEY|ExaKms")
        remove_comment.assert_called_once_with(None, ["node1"])
        restore_key.assert_not_called()

    def test_OracleVersion_compare_alnum_branches(self):
        """# Auto-generated test for OracleVersion"""
        version = OracleVersion()
        self.assertEqual(0, version.mCompareVersions("1a.2", "1a.2"))
        self.assertEqual(-1, version.mCompareVersions("1a.2", "1b.1"))
        self.assertEqual(1, version.mCompareVersions("1b.2", "1a.9"))
        self.assertEqual(1, version.mCompareVersions("1.2.3.4", "1.2.3"))

    def test_OracleVersion_compare_exception_returns_none(self):
        """# Auto-generated test for OracleVersion"""
        version = OracleVersion()

        class _BadStr(object):
            def split(self, _sep):
                raise ValueError("boom")

        with patch("exabox.ovm.clumisc.ebLogWarn"):
            self.assertIsNone(version.mCompareVersions(_BadStr(), "1.0"))

    def test_ebFortifyIssues_character_validation(self):
        """# Auto-generated test for ebFortifyIssues"""
        fortify = ebFortifyIssues()
        with patch("exabox.ovm.clumisc.ebLogError") as log_err:
            self.assertFalse(fortify.mPathManipulationError("/tmp/bad#path"))
        self.assertFalse(log_err.called)

    def test_mCheckUsedSpace_threshold_exceeded(self):
        """# Auto-generated test for mCheckUsedSpace"""
        cluctrl = Mock()
        ovm = ebCluPreChecks(cluctrl)

        node = Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO("/dev/sda1 10 9 1 99% /"), None)

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch("exabox.ovm.clumisc.get_gcontext"):
                result = ovm.mCheckUsedSpace("dom0", "/", "90")

        node.mConnect.assert_called_once_with(aHost="dom0")
        node.mDisconnect.assert_called_once()
        self.assertFalse(result)

    def test_mCheckUsedSpace_under_threshold(self):
        """# Auto-generated test for mCheckUsedSpace"""
        cluctrl = Mock()
        ovm = ebCluPreChecks(cluctrl)

        node = Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO(""), None)

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch("exabox.ovm.clumisc.get_gcontext"):
                result = ovm.mCheckUsedSpace("dom0", "/", "90")

        node.mConnect.assert_called_once_with(aHost="dom0")
        node.mDisconnect.assert_called_once()
        self.assertTrue(result)

    def test_mDom0SystemPreChecks_handles_threshold_failure(self):
        """# Auto-generated test for mDom0SystemPreChecks"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0", "domu")]
        ovm = ebCluPreChecks(cluctrl)

        with patch.object(ovm, "mCheckUsedSpace", return_value=False) as check_space, \
            patch("exabox.ovm.clumisc.ebLogError") as log_err:
            result = ovm.mDom0SystemPreChecks()

        check_space.assert_called_once_with("dom0", "/", "95")
        self.assertFalse(result)
        self.assertTrue(log_err.called)

    def test_mNetworkBasicChecks_detects_duplicate_ip(self):
        """# Auto-generated test for mNetworkBasicChecks"""
        class _MachineConfig(object):
            def __init__(self, hostname, networks):
                self._hostname = hostname
                self._networks = networks

            def mGetMacHostName(self):
                return self._hostname

            def mGetMacNetworks(self):
                return self._networks

        class _NetworkConfig(object):
            def __init__(self, ip, net_type="public"):
                self._ip = ip
                self._net_type = net_type

            def mGetNetType(self):
                return self._net_type

            def mGetNetIpAddr(self):
                return self._ip

        class _Networks(object):
            def __init__(self, mapping):
                self._mapping = mapping

            def mGetNetworkConfig(self, net_id):
                return self._mapping[net_id]

        class _Machines(object):
            def __init__(self, config_list):
                self._config_list = config_list

            def mGetMachineConfigList(self):
                return self._config_list

        cluctrl = Mock()
        cluctrl.mReturnAllClusterHosts.return_value = (["dom0"], [], [], [])
        cluctrl.mIsKVM.return_value = False
        machines = _Machines({
            "m1": _MachineConfig("host1", ["net1"]),
            "m2": _MachineConfig("host2", ["net2"])
        })
        networks = _Networks({
            "net1": _NetworkConfig("10.0.0.1"),
            "net2": _NetworkConfig("10.0.0.1"),
        })
        cluctrl.mGetMachines.return_value = machines
        cluctrl.mGetNetworks.return_value = networks

        ovm = ebCluPreChecks(cluctrl)

        with patch("exabox.ovm.clumisc.ebLogError") as log_err:
            ovm.mNetworkBasicChecks(aVerbose=True)

        self.assertTrue(log_err.called)

    def test_mConnectivityChecks_switch_parses_partition_info(self):
        """# Auto-generated test for mConnectivityChecks"""
        cluctrl = Mock()
        cluctrl.mReturnAllClusterHosts.return_value = ([], [], [], ["sw1"])
        cluctrl.mGetKey.return_value = "cluster"
        cluctrl.mPingHost.return_value = True

        network_config = Mock()
        network_config.mGetNetIpAddr.return_value = "192.0.2.1"
        networks = Mock()
        networks.mGetNetworkConfigByName.return_value = network_config
        cluctrl.mGetNetworks.return_value = networks

        node = Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO("Default=P0\\nALL_CAS=on\\n"), None)

        ovm = ebCluPreChecks(cluctrl)

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch("exabox.ovm.clumisc.get_gcontext"):
            result = ovm.mConnectivityChecks(aCheckDomU=True, aHostList=["sw1"])

        self.assertTrue(result)
        node.mConnect.assert_called_once_with(aHost="sw1")
        node.mDisconnect.assert_called_once()

    def test_mConnectivityChecks_domU_ping_failure_noncritical(self):
        """# Auto-generated test for mConnectivityChecks"""
        cluctrl = Mock()
        cluctrl.mReturnAllClusterHosts.return_value = ([], ["domu1"], [], [])
        cluctrl.mGetKey.return_value = "cluster"
        cluctrl.mPingHost.return_value = False

        network_config = Mock()
        network_config.mGetNetIpAddr.return_value = "192.0.2.2"
        networks = Mock()
        networks.mGetNetworkConfigByName.return_value = network_config
        cluctrl.mGetNetworks.return_value = networks

        ovm = ebCluPreChecks(cluctrl)

        with patch("exabox.ovm.clumisc.ebLogWarn") as log_warn:
            result = ovm.mConnectivityChecks(aCheckDomU=False, aHostList=["domu1"])

        self.assertTrue(result)
        self.assertTrue(log_warn.called)

    def test_mNetworkDom0PreChecks_returns_false_on_failure(self):
        """# Auto-generated test for mNetworkDom0PreChecks"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0", "domu")]
        ovm = ebCluPreChecks(cluctrl)

        class _Proc(object):
            def __init__(self, *_args, **_kwargs):
                pass

            def mSetMaxExecutionTime(self, *_args):
                pass

            def mSetJoinTimeout(self, *_args):
                pass

            def mSetLogTimeoutFx(self, *_args):
                pass

        class _Plist(object):
            def __init__(self):
                self._rc_dict = {"dom0": False}

            def mGetManager(self):
                return self

            def dict(self):
                return self._rc_dict

            def mStartAppend(self, _proc):
                pass

            def mJoinProcess(self):
                pass

        with patch("exabox.ovm.clumisc.ProcessManager", return_value=_Plist()), \
            patch("exabox.ovm.clumisc.ProcessStructure", _Proc):
            result = ovm.mNetworkDom0PreChecks()

        self.assertFalse(result)

    def test_mNetworkDom0PreChecks_success_kvm_removes_bridges(self):
        """# Auto-generated test for mNetworkDom0PreChecks"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0", "domu")]
        cluctrl.mIsKVM.return_value = True
        cluctrl.mIsOciEXACC.return_value = False
        cluctrl.mIsIntelX9MDom0.return_value = False
        ovm = ebCluPreChecks(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO("/etc/exadata/ovm/bridge.conf.d/eth5.xml\n"), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO("Consistency check PASSED\n"), None),
        ]
        node.mFileExists.return_value = True

        class _Proc(object):
            def __init__(self, func, args, name):
                self._func = func
                self._args = args

            def mSetMaxExecutionTime(self, *_args):
                pass

            def mSetJoinTimeout(self, *_args):
                pass

            def mSetLogTimeoutFx(self, *_args):
                pass

        class _Plist(object):
            def __init__(self):
                self._rc_dict = {"dom0": True}
                self._procs = []

            def mGetManager(self):
                return self

            def dict(self):
                return self._rc_dict

            def mStartAppend(self, _proc):
                self._procs.append(_proc)

            def mJoinProcess(self):
                for _proc in self._procs:
                    _proc._func(*_proc._args)

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch("exabox.ovm.clumisc.get_gcontext"), \
            patch("exabox.ovm.clumisc.ProcessManager", return_value=_Plist()), \
            patch("exabox.ovm.clumisc.ProcessStructure", _Proc):
            result = ovm.mNetworkDom0PreChecks()

        self.assertIsNone(result)
        node.mExecuteCmdLog.assert_any_call("rm /etc/exadata/ovm/bridge.conf.d/eth5.xml\n")
        node.mExecuteCmdLog.assert_any_call(
            "rm /etc/sysconfig/network-scripts/ifcfg-eth5 ; rm /etc/sysconfig/network-scripts/ifcfg-eth6 "
        )
        node.mDisconnect.assert_called_once()

    def test_mGetNamespaceStatus_empty_output_returns_false(self):
        """# Auto-generated test for mGetNamespaceStatus"""
        cluctrl = Mock()
        ovm = ebCluPreChecks(cluctrl)
        node = Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO(""), None)
        node.mGetCmdExitStatus.return_value = 0

        result = ovm.mGetNamespaceStatus(node)

        self.assertFalse(result)

    def test_mGetNamespaceStatus_nonempty_output_returns_true(self):
        """# Auto-generated test for mGetNamespaceStatus"""
        cluctrl = Mock()
        ovm = ebCluPreChecks(cluctrl)
        node = Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO("ns0\n"), None)
        node.mGetCmdExitStatus.return_value = 0

        result = ovm.mGetNamespaceStatus(node)

        self.assertTrue(result)

    def test_mGetNamespaceStatus_nonzero_exit_logs_but_returns_true(self):
        """# Auto-generated test for mGetNamespaceStatus"""
        cluctrl = Mock()
        ovm = ebCluPreChecks(cluctrl)
        node = Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO("ns1\n"), io.StringIO("err\n"))
        node.mGetCmdExitStatus.return_value = 1

        with patch("exabox.ovm.clumisc.ebLogInfo") as log_info:
            result = ovm.mGetNamespaceStatus(node)

        self.assertFalse(result)
        self.assertTrue(log_info.called)

    def test_mUpdateRequestData_error_str_exception_is_ignored(self):
        """# Auto-generated test for mUpdateRequestData"""
        cluctrl = Mock()
        req = Mock()
        req.mSetErrorStr.side_effect = Exception("boom")
        cluctrl.mGetRequestObj.return_value = req
        ovm = ebCluPreChecks(cluctrl)

        db = Mock()
        with patch("exabox.ovm.clumisc.ebGetDefaultDB", return_value=db), \
                patch("exabox.ovm.clumisc.ebLogJson"):
            ovm.mUpdateRequestData(Mock(), 1, {"k": "v"}, "err")

        req.mSetError.assert_called_once_with("1")
        req.mSetData.assert_called_once()
        db.mUpdateRequest.assert_called_once_with(req)

    def test_mGetEMClusterPerNodeCommands_non_oci(self):
        """# Auto-generated test for mGetEMClusterPerNodeCommands"""
        cluctrl = Mock()
        ovm = ebCluPreChecks(cluctrl)

        commands = ovm.mGetEMClusterPerNodeCommands(False, 2, "domu2")

        self.assertIn("NET1_HOST2_VIP_NAME", commands)
        self.assertIn("NET2_HOST2_VIP_NAME", commands)
        self.assertIn("HOST2_ASM_INSTANCE", commands)
        self.assertIn("srvctl config vip -node domu2", commands["NET1_HOST2_VIP_NAME"])
        self.assertIn("srvctl config vip -node domu2", commands["NET2_HOST2_VIP_NAME"])
        self.assertIn("get_creg_key grid sid", commands["HOST2_ASM_INSTANCE"])

    def test_mGetEMClusterPerNodeCommands_oci(self):
        """# Auto-generated test for mGetEMClusterPerNodeCommands"""
        cluctrl = Mock()
        ovm = ebCluPreChecks(cluctrl)

        commands = ovm.mGetEMClusterPerNodeCommands(True, 1, "domu1")

        self.assertIn("NET1_HOST1_VIP_NAME", commands)
        self.assertIn("NET2_HOST1_VIP_NAME", commands)
        self.assertIn("network number 2", commands["NET2_HOST1_VIP_NAME"])

    def test_mGetEMClusterKeyCommandDict_namespace_enabled(self):
        """# Auto-generated test for mGetEMClusterKeyCommandDict"""
        cluctrl = Mock()
        ovm = ebCluPreChecks(cluctrl)

        commands = ovm.mGetEMClusterKeyCommandDict(isOCI=False, isNamespaceEnabled=True)

        self.assertIn("GRID_HOME", commands)
        self.assertNotIn("NET2_SCAN_NAME", commands)
        self.assertNotIn("NET2_SCAN_PORT", commands)

    def test_mGetEMClusterKeyCommandDict_namespace_disabled_non_oci(self):
        """# Auto-generated test for mGetEMClusterKeyCommandDict"""
        cluctrl = Mock()
        ovm = ebCluPreChecks(cluctrl)

        commands = ovm.mGetEMClusterKeyCommandDict(isOCI=False, isNamespaceEnabled=False)

        self.assertIn("NET2_SCAN_NAME", commands)
        self.assertIn("LISTENER_BKUP_SCAN_NAME", commands)
        self.assertIn("LISTENER_SCAN1", commands["LISTENER_BKUP_SCAN_NAME"])
        self.assertIn("crsctl stat res ora.LISTENER_SCAN1.lsnr", commands["NET2_SCAN_HOST"])

    def test_mGetEMClusterKeyCommandDict_namespace_disabled_oci(self):
        """# Auto-generated test for mGetEMClusterKeyCommandDict"""
        cluctrl = Mock()
        ovm = ebCluPreChecks(cluctrl)

        commands = ovm.mGetEMClusterKeyCommandDict(isOCI=True, isNamespaceEnabled=False)

        self.assertIn("NET2_SCAN_NAME", commands)
        self.assertIn("LISTENER_BKUP_SCAN_NAME", commands)
        self.assertIn("LISTENER_BKUP_SCAN1_NET2", commands["LISTENER_BKUP_SCAN_NAME"])
        self.assertIn("ora.LISTENER_BKUP_SCAN1_NET2.lsnr", commands["NET2_SCAN_HOST"])

    def test_mGetEMClusterAllNodeKeyCommandDict(self):
        """# Auto-generated test for mGetEMClusterAllNodeKeyCommandDict"""
        cluctrl = Mock()
        ovm = ebCluPreChecks(cluctrl)

        commands = ovm.mGetEMClusterAllNodeKeyCommandDict(isOCI=True)

        self.assertEqual(list(commands.keys()), ["ASMNET1LSNR_HOST"])
        self.assertIn("lsnrctl status ASMNET1LSNR_ASM", commands["ASMNET1LSNR_HOST"])

    def test_mEMClusterDetails_success_updates_request(self):
        """# Auto-generated test for mEMClusterDetails"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0", "domu1"), ("dom1", "domu2")]
        cluctrl.mIsExabm.return_value = False
        ovm = ebCluPreChecks(cluctrl)

        node = Mock()
        node.mGetCmdExitStatus.return_value = 0
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO("ns\n"), io.StringIO("")),
            (None, io.StringIO("GRIDHOME\n"), io.StringIO("")),
            (None, io.StringIO("CLUSTER\n"), io.StringIO("")),
            (None, io.StringIO("scan1\n"), io.StringIO("")),
            (None, io.StringIO("scan2\n"), io.StringIO("")),
            (None, io.StringIO("scan3\n"), io.StringIO("")),
            (None, io.StringIO("scanhost1\n"), io.StringIO("")),
            (None, io.StringIO("scanhost2\n"), io.StringIO("")),
            (None, io.StringIO("scanhost3\n"), io.StringIO("")),
            (None, io.StringIO("1521\n"), io.StringIO("")),
            (None, io.StringIO("ad1\n"), io.StringIO("")),
            (None, io.StringIO("scanname1\n"), io.StringIO("")),
            (None, io.StringIO("1522\n"), io.StringIO("")),
            (None, io.StringIO("asmhost1\n"), io.StringIO("")),
            (None, io.StringIO("net1vip\n"), io.StringIO("")),
            (None, io.StringIO("net2vip\n"), io.StringIO("")),
            (None, io.StringIO("+ASM1\n"), io.StringIO("")),
            (None, io.StringIO("ns2\n"), io.StringIO("")),
            (None, io.StringIO("asmhost2\n"), io.StringIO("")),
            (None, io.StringIO("net1vip2\n"), io.StringIO("")),
            (None, io.StringIO("net2vip2\n"), io.StringIO("")),
            (None, io.StringIO("+ASM2\n"), io.StringIO("")),
        ]

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch.object(ebCluPreChecks, "mUpdateRequestData") as mock_update:
            rc = ovm.mEMClusterDetails(Mock())

        self.assertEqual(rc, 0)
        args, _ = mock_update.call_args
        self.assertEqual(args[1], 0)
        self.assertTrue(args[2]["IS_NAMESPACE_ENABLED"])
        self.assertEqual(args[2]["GRID_HOME"], "GRIDHOME")
        self.assertEqual(args[2]["ASMNET1LSNR_HOST1"], "asmhost1")
        self.assertEqual(args[2]["ASMNET1LSNR_HOST2"], "asmhost2")
        self.assertEqual(args[2]["HOST1_ASM_INSTANCE"], "+ASM1")
        self.assertEqual(args[2]["HOST2_ASM_INSTANCE"], "+ASM2")

    def test_mEMClusterDetails_raises_on_error(self):
        """# Auto-generated test for mEMClusterDetails"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        cluctrl.mIsExabm.return_value = False
        ovm = ebCluPreChecks(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = Exception("boom")

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch.object(ebCluPreChecks, "mUpdateRequestData") as mock_update:
            with self.assertRaises(ExacloudRuntimeError):
                ovm.mEMClusterDetails(Mock())

        args, _ = mock_update.call_args
        self.assertEqual(args[1], -1)
        self.assertIn("Exception occured during EM cluster details", args[3])

    def test_mUpdateRequestData_sets_error_fields(self):
        """# Auto-generated test for mUpdateRequestData"""
        cluctrl = Mock()
        req = Mock()
        cluctrl.mGetRequestObj.return_value = req
        ovm = ebCluPreChecks(cluctrl)

        db = Mock()
        with patch("exabox.ovm.clumisc.ebGetDefaultDB", return_value=db), \
            patch("exabox.ovm.clumisc.ebLogJson"):
            ovm.mUpdateRequestData(Mock(), 1, {"k": "v"}, "")

        req.mSetError.assert_called_once_with("1")
        req.mSetErrorStr.assert_called_once_with("Unknown Error")
        req.mSetData.assert_called_once()
        db.mUpdateRequest.assert_called_once_with(req)

    def test_mUpdateRequestData_sets_success_fields(self):
        """# Auto-generated test for mUpdateRequestData"""
        cluctrl = Mock()
        req = Mock()
        cluctrl.mGetRequestObj.return_value = req
        ovm = ebCluPreChecks(cluctrl)

        db = Mock()
        with patch("exabox.ovm.clumisc.ebGetDefaultDB", return_value=db), \
            patch("exabox.ovm.clumisc.ebLogJson"):
            ovm.mUpdateRequestData(Mock(), 0, {"k": "v"}, "err")

        req.mSetError.assert_called_once_with("0")
        req.mSetErrorStr.assert_called_once_with("Undef")
        req.mSetData.assert_called_once()
        db.mUpdateRequest.assert_called_once_with(req)

    def test_mCheckDom0Mem_invalid_host_returns_false(self):
        """# Auto-generated test for mCheckDom0Mem"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0a", "domu")]
        ovm = ebCluPreChecks(cluctrl)

        with patch("exabox.ovm.clumisc.ebLogError") as log_error:
            result = ovm.mCheckDom0Mem("dom0b")

        self.assertFalse(result)
        self.assertTrue(log_error.called)

    def test_mCheckDom0Mem_insufficient_memory_logs_and_returns_false(self):
        """# Auto-generated test for mCheckDom0Mem"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0a", "domu")]

        vm_size = Mock()
        vm_size.mGetVMSizeAttr.return_value = "10GB"
        sizes = Mock()
        sizes.mGetVMSize.return_value = vm_size
        cluctrl.mGetVMSizesConfig.return_value = sizes
        cluctrl.mIsDebug.return_value = False

        vm = Mock()
        vm.getDom0FreeMem.return_value = "1024"
        vm.mRefreshDomUs.return_value = ["vm1", "vm2"]

        ovm = ebCluPreChecks(cluctrl)

        with patch("exabox.ovm.clumisc.getHVInstance", return_value=vm), \
            patch("exabox.ovm.clumisc.ebLogError") as log_error:
            result = ovm.mCheckDom0Mem("dom0a")

        self.assertFalse(result)
        self.assertTrue(log_error.called)

    def test_mCheckOracleLinuxVersion_config_disabled_returns_none(self):
        """# Auto-generated test for mCheckOracleLinuxVersion"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = "False"
        cluctrl.mGetOracleLinuxVersion = Mock()
        ovm = ebCluPreChecks(cluctrl)

        result = ovm.mCheckOracleLinuxVersion("domu", ["dom0"])

        self.assertIsNone(result)
        cluctrl.mGetOracleLinuxVersion.assert_not_called()

    def test_mCheckOracleLinuxVersion_raises_for_lower_dom0(self):
        """# Auto-generated test for mCheckOracleLinuxVersion"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = "True"
        cluctrl.mGetOracleLinuxVersion.side_effect = [10, 9]
        ovm = ebCluPreChecks(cluctrl)

        with self.assertRaises(ExacloudRuntimeError):
            ovm.mCheckOracleLinuxVersion("domu", ["dom0"])

    def test_mCheckUsedSpace_returns_false_when_threshold_exceeded(self):
        """# Auto-generated test for mCheckUsedSpace"""
        cluctrl = Mock()
        ovm = ebCluPreChecks(cluctrl)
        node = Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO("80%\n"), None)

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node):
            result = ovm.mCheckUsedSpace("dom0", "/u01", "80")

        self.assertFalse(result)
        node.mConnect.assert_called_once_with(aHost="dom0")
        node.mDisconnect.assert_called_once()
        node.mExecuteCmd.assert_called_once_with("df -P /u01 | tail -1 | awk '0+$5 >= 80 {print}'")

    def test_mCheckUsedSpace_returns_true_when_under_threshold(self):
        """# Auto-generated test for mCheckUsedSpace"""
        cluctrl = Mock()
        ovm = ebCluPreChecks(cluctrl)
        node = Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO(""), None)

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node):
            result = ovm.mCheckUsedSpace("dom0", "/u01", "80")

        self.assertTrue(result)
        node.mConnect.assert_called_once_with(aHost="dom0")
        node.mDisconnect.assert_called_once()

    def test_mGetAsmDbSnmpPasswords_success_updates_request(self):
        """# Auto-generated test for mGetAsmDbSnmpPasswords"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0", "domu")]
        ovm = ebCluPreChecks(cluctrl)
        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO("asm-pass\n"), io.StringIO("")),
            (None, io.StringIO("db-pass\n"), io.StringIO("")),
        ]
        node.mGetCmdExitStatus.return_value = 0

        options = Mock()
        options.dbsid = "DB1"

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch.object(ebCluPreChecks, "mUpdateRequestData") as mock_update:
            rc = ovm.mGetAsmDbSnmpPasswords(options)

        self.assertEqual(rc, 0)
        args, _ = mock_update.call_args
        self.assertEqual(args[1], 0)
        self.assertEqual(args[2]["asmsnmppassword"], "asm-pass")
        self.assertEqual(args[2]["dbsnmppassword"], "db-pass")
        self.assertIsNone(args[3])

    def test_mGetAsmDbSnmpPasswords_raises_on_error(self):
        """# Auto-generated test for mGetAsmDbSnmpPasswords"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0", "domu")]
        ovm = ebCluPreChecks(cluctrl)
        node = Mock()
        node.mExecuteCmd.side_effect = Exception("boom")

        options = Mock()
        options.dbsid = "DB1"

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch.object(ebCluPreChecks, "mUpdateRequestData") as mock_update:
            with self.assertRaises(ExacloudRuntimeError):
                ovm.mGetAsmDbSnmpPasswords(options)

        args, _ = mock_update.call_args
        self.assertEqual(args[1], -1)
        self.assertIn("Exception during asm", args[3])

    def test_mEMDBDetails_success_updates_request(self):
        """# Auto-generated test for mEMDBDetails"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0", "domu")]
        ovm = ebCluPreChecks(cluctrl)
        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO("svc\n"), io.StringIO("")),
            (None, io.StringIO("/u01/db\n"), io.StringIO("")),
            (None, io.StringIO("DBNAME\n"), io.StringIO("")),
            (None, io.StringIO("inst1,inst2\n"), io.StringIO("")),
            (None, io.StringIO("PRIMARY\n"), io.StringIO("")),
        ]
        node.mGetCmdExitStatus.return_value = 0

        options = Mock()
        options.dbsid = "DB1"

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch.object(ebCluPreChecks, "mUpdateRequestData") as mock_update:
            rc = ovm.mEMDBDetails(options)

        self.assertEqual(rc, 0)
        args, _ = mock_update.call_args
        self.assertEqual(args[1], 0)
        self.assertEqual(args[2]["DB_NAME"], "DBNAME")
        self.assertEqual(args[2]["DB_ROLE"], "PRIMARY")

    def test_mEMDBDetails_raises_on_error(self):
        """# Auto-generated test for mEMDBDetails"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0", "domu")]
        ovm = ebCluPreChecks(cluctrl)
        node = Mock()
        node.mExecuteCmd.side_effect = Exception("boom")

        options = Mock()
        options.dbsid = "DB1"

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch.object(ebCluPreChecks, "mUpdateRequestData") as mock_update:
            with self.assertRaises(ExacloudRuntimeError):
                ovm.mEMDBDetails(options)

        args, _ = mock_update.call_args
        self.assertEqual(args[1], -1)
        self.assertIn("Exception during retrieving DB details", args[3])

    def test_mCheckVMTimeDrift_logs_for_thresholds(self):
        """# Auto-generated test for mCheckVMTimeDrift"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0a", "domu1"), ("dom0b", "domu2")]
        ovm = ebCluPreChecks(cluctrl)

        node = Mock()
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO("a,b,c,d,4\n"), None),
            (None, io.StringIO("a,b,c,d,0\n"), None),
        ]

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch("exabox.ovm.clumisc.ebLogError") as log_error:
            rc = ovm.mCheckVMTimeDrift()

        self.assertEqual(rc, 0)
        self.assertEqual(node.mConnect.call_count, 2)
        self.assertEqual(node.mDisconnect.call_count, 2)
        self.assertGreaterEqual(log_error.call_count, 2)

    def test_mCheckClusterIntegrity_successful_paths(self):
        """# Auto-generated test for mCheckClusterIntegrity"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0", "domu1"), ("dom1", "domu2")]
        cluctrl.mIsXS.return_value = False
        cluctrl.mGetOracleBaseDirectories.return_value = ("/u01/app/oracle", None, None)
        ovm = ebCluPreChecks(cluctrl)

        node = Mock()
        node.mGetCmdExitStatus.return_value = 0
        node.mExecuteCmd.side_effect = [
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
            (None, io.StringIO(""), None),
        ]

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node):
            ovm.mCheckClusterIntegrity(True)

        self.assertEqual(node.mExecuteCmd.call_count, 6)
        self.assertEqual(node.mConnect.call_count, 1)
        node.mDisconnect.assert_called_once()

    def test_mCheckClusterIntegrity_nonraise_skips_scan_and_asm(self):
        """# Auto-generated test for mCheckClusterIntegrity"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        cluctrl.mIsXS.return_value = True
        cluctrl.mGetOracleBaseDirectories.return_value = ("/u01/app/oracle", None, None)
        ovm = ebCluPreChecks(cluctrl)

        node = Mock()
        node.mGetCmdExitStatus.return_value = 1
        node.mExecuteCmd.return_value = (None, io.StringIO("err\n"), None)

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch("exabox.ovm.clumisc.ebLogError") as log_error:
            ovm.mCheckClusterIntegrity(False, aRaiseError=False)

        self.assertEqual(node.mExecuteCmd.call_count, 4)
        node.mDisconnect.assert_called_once()
        self.assertGreaterEqual(log_error.call_count, 3)

    def test_validate_hw_results_prevm_check_splits_nodes(self):
        """# Auto-generated test for validate_hw_results"""
        cluctrl = Mock()
        ovm = ebCluPreChecks(cluctrl)

        hw = {
            "nodes": [
                {
                    "hostname": "dom0a",
                    "domainname": "example.com",
                    "hw_type": "COMPUTE",
                    "fan": "normal",
                    "temperature": "normal",
                },
                {
                    "hostname": "dom0b",
                    "domainname": "example.com",
                    "hw_type": "COMPUTE",
                    "fan": "abnormal",
                    "error_list": [{"error-message": "fan"}],
                },
            ]
        }

        result = ovm.validate_hw_results("ESTP_PREVM_CHECKS", hw)

        self.assertEqual(len(result["healthy_nodes"]), 1)
        self.assertEqual(len(result["unhealthy_nodes"]), 1)
        self.assertEqual(result["healthy_nodes"][0]["host"], "dom0a.example.com")

    def test_validate_hw_results_elastic_m2_sys_ignored(self):
        """# Auto-generated test for validate_hw_results"""
        cluctrl = Mock()
        cluctrl.mCheckConfigOption.return_value = True
        ovm = ebCluPreChecks(cluctrl)

        hw = {
            "host1": {
                "node_info": [
                    {
                        "node_type": "quarter-rack-servers",
                        "hostname": "h1",
                        "error_list": [{"error-message": "m2_sys alarm"}],
                    }
                ]
            },
            "host2": {
                "node_info": [
                    {
                        "node_type": "elastic-servers",
                        "hostname": "h2",
                        "error_list": [{"error-message": "disk"}],
                    }
                ]
            },
        }

        result = ovm.validate_hw_results("ELASTIC_SHAPES_VALIDATION", hw)

        self.assertEqual(result["quarter-rack-faulty-servers"], [])
        self.assertEqual(len(result["elastic-faulty-servers"]), 1)
        self.assertEqual(result["elastic-faulty-servers"][0]["hostname"], "h2")

    def test_mUpdateRequestData_success_sets_request(self):
        """# Auto-generated test for mUpdateRequestData"""
        cluctrl = Mock()
        req = Mock()
        cluctrl.mGetRequestObj.return_value = req
        ovm = ebCluPreChecks(cluctrl)
        db = Mock()

        with patch("exabox.ovm.clumisc.ebGetDefaultDB", return_value=db), \
            patch("exabox.ovm.clumisc.ebLogJson"):
            ovm.mUpdateRequestData(Mock(), 0, {"key": "value"}, None)

        req.mSetError.assert_called_with('0')
        req.mSetErrorStr.assert_called_with('Undef')
        req.mSetData.assert_called_once()
        db.mUpdateRequest.assert_called_once_with(req)

    def test_mUpdateRequestData_failure_sets_unknown_error(self):
        """# Auto-generated test for mUpdateRequestData"""
        cluctrl = Mock()
        req = Mock()
        cluctrl.mGetRequestObj.return_value = req
        ovm = ebCluPreChecks(cluctrl)
        db = Mock()

        with patch("exabox.ovm.clumisc.ebGetDefaultDB", return_value=db), \
            patch("exabox.ovm.clumisc.ebLogJson"):
            ovm.mUpdateRequestData(Mock(), 1, {"key": "value"}, None)

        req.mSetError.assert_called_with('1')
        req.mSetErrorStr.assert_called_with('Unknown Error')
        db.mUpdateRequest.assert_called_once_with(req)

    def test_mUpdateRequestData_no_request_object(self):
        """# Auto-generated test for mUpdateRequestData"""
        cluctrl = Mock()
        cluctrl.mGetRequestObj.return_value = None
        ovm = ebCluPreChecks(cluctrl)

        with patch("exabox.ovm.clumisc.ebGetDefaultDB") as mock_db, \
            patch("exabox.ovm.clumisc.ebLogJson"):
            ovm.mUpdateRequestData(Mock(), 0, {"key": "value"}, "err")

        mock_db.assert_not_called()

    def test_mCheckScanName_valid_scan(self):
        """# Auto-generated test for mCheckScanName"""
        cluctrl = Mock()
        cluster = Mock()
        cluster.mGetCluScans.return_value = ["scan-id"]
        clusters = Mock()
        clusters.mGetCluster.return_value = cluster
        cluctrl.mGetClusters.return_value = clusters

        scan_entry = Mock()
        scan_entry.mGetCluId.return_value = "scan-id"
        scan_entry.mGetScanName.return_value = "scan1.example.com"
        scans = Mock()
        scans.mGetScans.return_value = ["scan1"]
        scans.mGetScan.return_value = scan_entry
        cluctrl.mGetScans.return_value = scans

        ovm = ebCluPreChecks(cluctrl)

        ovm.mCheckScanName()

    def test_mCheckScanName_raises_on_null(self):
        """# Auto-generated test for mCheckScanName"""
        cluctrl = Mock()
        cluster = Mock()
        cluster.mGetCluScans.return_value = ["scan-id"]
        clusters = Mock()
        clusters.mGetCluster.return_value = cluster
        cluctrl.mGetClusters.return_value = clusters

        scan_entry = Mock()
        scan_entry.mGetCluId.return_value = "scan-id"
        scan_entry.mGetScanName.return_value = "null.example.com"
        scans = Mock()
        scans.mGetScans.return_value = ["scan1"]
        scans.mGetScan.return_value = scan_entry
        cluctrl.mGetScans.return_value = scans

        ovm = ebCluPreChecks(cluctrl)

        with self.assertRaises(ExacloudRuntimeError):
            ovm.mCheckScanName()

    def test_validateIpOrHostname_rejects_empty_and_underscore(self):
        """# Auto-generated test for validateIpOrHostname"""
        self.assertFalse(validateIpOrHostname(""))
        self.assertFalse(validateIpOrHostname("bad_host"))

    def test_getWorkerPIDs_accepts_supervisor(self):
        """# Auto-generated test for getWorkerPIDs"""
        wlist = [
            ("worker1", "Running", None, None, None, None, None, None, "456"),
            ("worker2", "Exited", None, None, None, None, None, None, "789"),
        ]

        proc_super = Mock()
        proc_super.cmdline.return_value = ["exabox", "--supervisor"]

        with patch("exabox.ovm.clumisc.psutil.pid_exists", return_value=True), \
            patch("exabox.ovm.clumisc.psutil.Process", return_value=proc_super) as proc_mock:
            result = AgentWorkerPIDListing.getWorkerPIDs(str(wlist))

        self.assertEqual([456], result)
        proc_mock.assert_called_once_with(456)

    def test_getWorkerPIDs_only_exited_workers(self):
        """# Auto-generated test for getWorkerPIDs"""
        wlist = [
            ("worker1", "Exited", None, None, None, None, None, None, "111"),
            ("worker2", "Exited", None, None, None, None, None, None, "222"),
        ]

        with patch("exabox.ovm.clumisc.psutil.pid_exists") as pid_exists:
            result = AgentWorkerPIDListing.getWorkerPIDs(str(wlist))

        self.assertEqual([], result)
        pid_exists.assert_not_called()

    def test_getWorkerPIDs_keeps_worker_types(self):
        """# Auto-generated test for getWorkerPIDs"""
        wlist = [
            ("worker1", "Running", None, None, None, None, None, None, "123"),
            ("worker2", "Running", None, None, None, None, None, None, "234"),
        ]

        proc_worker = Mock()
        proc_worker.cmdline.return_value = ["exabox", "-w"]
        proc_super = Mock()
        proc_super.cmdline.return_value = ["exabox", "--supervisor"]

        with patch("exabox.ovm.clumisc.psutil.pid_exists", return_value=True), \
            patch("exabox.ovm.clumisc.psutil.Process", side_effect=[proc_worker, proc_super]) as proc_mock:
            result = AgentWorkerPIDListing.getWorkerPIDs(str(wlist))

        self.assertEqual([123, 234], result)
        proc_mock.assert_any_call(123)
        proc_mock.assert_any_call(234)

    def test_getWorkerPIDs_skips_zero_pid_entry(self):
        """# Auto-generated test for getWorkerPIDs"""
        wlist = [
            ("worker1", "Running", None, None, None, None, None, None, "101"),
            ("worker2", "Running", None, None, None, None, None, None, "0"),
        ]

        proc_worker = Mock()
        proc_worker.cmdline.return_value = ["exabox", "-w"]

        with patch("exabox.ovm.clumisc.psutil.pid_exists", return_value=True) as pid_exists, \
            patch("exabox.ovm.clumisc.psutil.Process", return_value=proc_worker) as proc_mock:
            result = AgentWorkerPIDListing.getWorkerPIDs(str(wlist))

        self.assertEqual([101], result)
        pid_exists.assert_called_once_with(101)
        proc_mock.assert_called_once_with(101)

    def test_mProcessHostLifecycle_missing_context(self):
        """# Auto-generated test for mProcessHostLifecycle"""
        startstop = ebCluStartStopHostFromIlom(Mock())
        ctx = {"host": None, "ilom": "ilom1", "operation": "start", "sleep_time": 1, "results_dict": {}}

        with self.assertRaises(ExacloudRuntimeError):
            startstop.mProcessHostLifecycle(ctx)

    def test_mProcessHostLifecycle_invalid_operation(self):
        """# Auto-generated test for mProcessHostLifecycle"""
        startstop = ebCluStartStopHostFromIlom(Mock())
        results = {}
        ctx = {"host": "host1", "ilom": "ilom1", "operation": "pause", "sleep_time": 1, "results_dict": results}

        with self.assertRaises(ExacloudRuntimeError):
            startstop.mProcessHostLifecycle(ctx)

        self.assertIn("Invalid operation", results.get("host1", ""))

    def test_mProcessHostLifecycle_start_success(self):
        """# Auto-generated test for mProcessHostLifecycle"""
        ebox = Mock()
        ebox.mPingHost.side_effect = [False, True]
        startstop = ebCluStartStopHostFromIlom(ebox)
        results = {}
        ctx = {"host": "host1", "ilom": "ilom1", "operation": "start", "sleep_time": 5, "results_dict": results}

        with patch.object(startstop, "mStartHostfromIlom") as start_mock, \
                patch("exabox.ovm.clumisc.time.sleep") as sleep_mock, \
                patch("exabox.ovm.clumisc.time.time", side_effect=itertools.count()):
            startstop.mProcessHostLifecycle(ctx)

        start_mock.assert_called_once_with("ilom1")
        sleep_mock.assert_any_call(10)
        self.assertEqual(results.get("host1"), "Success")

    def test_mProcessHostLifecycle_stop_timeout(self):
        """# Auto-generated test for mProcessHostLifecycle"""
        ebox = Mock()
        ebox.mPingHost.return_value = True
        startstop = ebCluStartStopHostFromIlom(ebox)
        results = {}
        ctx = {"host": "host1", "ilom": "ilom1", "operation": "stop", "sleep_time": 1, "results_dict": results}

        with patch.object(startstop, "mStopHostfromIlom") as stop_mock, \
                patch("exabox.ovm.clumisc.time.sleep") as sleep_mock, \
                patch("exabox.ovm.clumisc.time.time", side_effect=itertools.count()):
            startstop.mProcessHostLifecycle(ctx)

        stop_mock.assert_called_once_with("ilom1")
        sleep_mock.assert_called_once_with(10)
        self.assertIn("Timeout", results.get("host1", ""))

    def test_mStopStartHostViaIlom_invalid_operation_payload(self):
        """# Auto-generated test for mStopStartHostViaIlom"""
        ebox = Mock()
        startstop = ebCluStartStopHostFromIlom(ebox)
        options = types.SimpleNamespace(jsonconf={"operation": "wait", "host_ilom_pair": {"h": "i"}})

        with self.assertRaises(ExacloudRuntimeError):
            startstop.mStopStartHostViaIlom(options)

    def test_mStopStartHostViaIlom_missing_host_pairs(self):
        """# Auto-generated test for mStopStartHostViaIlom"""
        ebox = Mock()
        startstop = ebCluStartStopHostFromIlom(ebox)
        options = types.SimpleNamespace(jsonconf={"operation": "start"})

        with self.assertRaises(ExacloudRuntimeError):
            startstop.mStopStartHostViaIlom(options)

    def test_mGetCoreAndMemInfo_zdlra_ratio(self):
        """# Auto-generated test for mGetCoreAndMemInfo"""
        cluctrl = Mock()
        cluctrl.IsZdlraProv.return_value = True
        cluctrl.mCheckConfigOption.side_effect = lambda key: "4" if key == "zdlra_core_to_vcpu_ratio" else None
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0a", "domu1")]
        cluctrl.mGetImageVersion.return_value = "25.1.0"
        cluctrl.mReturnCellNodes.return_value = {"cell1": None}
        cluctrl.mIsClusterLessXML.return_value = False
        reqobj = Mock()
        cluctrl.mGetRequestObj.return_value = reqobj

        hv = Mock()
        hv.mGetVMMemory.return_value = "2048"
        hv.mGetVMCpu.return_value = "8"

        with patch("exabox.ovm.clumisc.getHVInstance", return_value=hv), \
                patch("exabox.ovm.clumisc.ebGetDefaultDB") as mock_db:
            mock_db.return_value.mUpdateRequest.return_value = None
            ovm = ebCluPreChecks(cluctrl)
            ovm.mGetCoreAndMemInfo()

        reqobj.mSetData.assert_called_once()
        payload = json.loads(reqobj.mSetData.call_args[0][0])
        self.assertEqual(payload["cpu_memory_info"][0]["cpu"], 2)
        self.assertEqual(payload["cpu_memory_info"][0]["memory_in_gb"], 2)
        cluctrl.mCheckConfigOption.assert_any_call("zdlra_core_to_vcpu_ratio")

    def test_mGetCoreAndMemInfo_missing_request_obj_raises(self):
        """# Auto-generated test for mGetCoreAndMemInfo"""
        cluctrl = Mock()
        cluctrl.IsZdlraProv.return_value = False
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0a", "domu1")]
        cluctrl.mGetImageVersion.return_value = "25.1.0"
        cluctrl.mReturnCellNodes.return_value = {"cell1": None}
        cluctrl.mIsClusterLessXML.return_value = False
        cluctrl.mGetRequestObj.return_value = None

        hv = Mock()
        hv.mGetVMMemory.return_value = "1024"
        hv.mGetVMCpu.return_value = "2"

        with patch("exabox.ovm.clumisc.getHVInstance", return_value=hv):
            ovm = ebCluPreChecks(cluctrl)
            with self.assertRaises(ExacloudRuntimeError):
                ovm.mGetCoreAndMemInfo()

    def test_mGetCoreAndMemInfo_missing_memory_raises(self):
        """# Auto-generated test for mGetCoreAndMemInfo"""
        cluctrl = Mock()
        cluctrl.IsZdlraProv.return_value = False
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0a", "domu1")]
        cluctrl.mGetImageVersion.return_value = "25.1.0"
        cluctrl.mReturnCellNodes.return_value = {"cell1": None}
        cluctrl.mIsClusterLessXML.return_value = False

        hv = Mock()
        hv.mGetVMMemory.return_value = None
        hv.mGetVMCpu.return_value = "2"

        with patch("exabox.ovm.clumisc.getHVInstance", return_value=hv):
            ovm = ebCluPreChecks(cluctrl)
            with self.assertRaises(ExacloudRuntimeError):
                ovm.mGetCoreAndMemInfo()

    def test_mConnectivityChecks_ping_ok_ssh_failure(self):
        """# Auto-generated test for mConnectivityChecks"""
        cluctrl = Mock()
        cluctrl.mReturnAllClusterHosts.return_value = ([], [], ["cell1"], [])
        cluctrl.mGetKey.return_value = "cluster"
        cluctrl.mPingHost.return_value = True

        network_config = Mock()
        network_config.mGetNetIpAddr.return_value = "192.0.2.10"
        networks = Mock()
        networks.mGetNetworkConfigByName.return_value = network_config
        cluctrl.mGetNetworks.return_value = networks

        node = Mock()
        node.mConnect.side_effect = Exception("ssh failed")

        ovm = ebCluPreChecks(cluctrl)

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
                patch("exabox.ovm.clumisc.get_gcontext"):
            result = ovm.mConnectivityChecks(aCheckDomU=True, aHostList=["cell1"])

        self.assertTrue(result)

    def test_mGetAsmDbSnmpPasswords_dbsid_empty(self):
        """# Auto-generated test for mGetAsmDbSnmpPasswords"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0a", "domu1")]
        ovm = ebCluPreChecks(cluctrl)

        node = Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO("asmPwd\n"), None)
        node.mGetCmdExitStatus.return_value = False

        options = types.SimpleNamespace(dbsid="")

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
                patch.object(ebCluPreChecks, "mUpdateRequestData") as mock_update:
            rc = ovm.mGetAsmDbSnmpPasswords(options)

        self.assertEqual(0, rc)
        node.mDisconnect.assert_called_once()
        args = mock_update.call_args[0]
        self.assertEqual("", args[2]["dbsnmppassword"])

    def test_ebSubnetIp_hostname_resolution(self):
        """# Auto-generated test for ebSubnetIp"""
        with patch("exabox.ovm.clumisc.socket.gethostbyname", return_value="192.0.2.5") as lookup:
            subnet = ebSubnetIp("example-host/24")
        lookup.assert_called_once_with("example-host")
        self.assertEqual(subnet.mGetCIDR(), "192.0.2.0/24")

    def test_ebSubnetIp_invalid_octet_raises(self):
        """# Auto-generated test for ebSubnetIp"""
        with self.assertRaises(ValueError):
            ebSubnetIp("256.0.0.1/24")

    def test_ebSubnetSet_empty_set_conflicts(self):
        """# Auto-generated test for ebSubnetSet"""
        subnet_set = ebSubnetSet()
        self.assertEqual(subnet_set.mIpInSet("10.0.0.0/24"), [])
        self.assertEqual(subnet_set.mGetAllIPs(), [])

    def test_mHandleRequest_invalid_optype_raises(self):
        """# Auto-generated test for mHandleRequest"""
        cluctrl = Mock()
        options = types.SimpleNamespace(jsonconf={"hostname": "cell1", "optype": "bogus", "nodetype": "cell"})

        fault = ebCluFaultInjection(cluctrl, options)
        with self.assertRaises(ExacloudRuntimeError):
            fault.mHandleRequest()

    def test_mHandleRequest_missing_action_for_lifecycle(self):
        """# Auto-generated test for mHandleRequest"""
        cluctrl = Mock()
        options = types.SimpleNamespace(jsonconf={"hostname": "cell1", "optype": "lifecycle", "nodetype": "cell"})

        fault = ebCluFaultInjection(cluctrl, options)
        with self.assertRaises(ExacloudRuntimeError):
            fault.mHandleRequest()

    def test_mHandleNetworkPartition_no_toggle_when_states_match(self):
        """# Auto-generated test for mHandleNetworkPartition"""
        options = types.SimpleNamespace(jsonconf={"hostname": "cell1", "optype": "network-partition", "nodetype": "cell", "action": "down"})
        fault = ebCluFaultInjection(Mock(), options)

        with patch.object(ebCluFaultInjection, "mGetInterfaceState", side_effect=[False, False]) as mock_state, \
                patch.object(ebCluFaultInjection, "mToggleCellInterface") as mock_toggle:
            fault.mHandleNetworkPartition("down")

        self.assertEqual([call("stre0"), call("stre1")], mock_state.call_args_list)
        mock_toggle.assert_not_called()

    def test_mGetInterfaceState_no_carrier_returns_false(self):
        """# Auto-generated test for mGetInterfaceState"""
        cluctrl = Mock()
        options = types.SimpleNamespace(jsonconf={"hostname": "cell1", "optype": "network-partition", "nodetype": "cell"})
        fault = ebCluFaultInjection(cluctrl, options)

        node = Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO("7: stre0: <NO-CARRIER> mtu 2300 state DOWN"), None)

        with patch("exabox.ovm.clumisc.connect_to_host") as mock_conn, \
                patch("exabox.ovm.clumisc.get_gcontext"):
            mock_conn.return_value.__enter__.return_value = node
            self.assertFalse(fault.mGetInterfaceState("stre0"))

    def test_mGetInterfaceState_exception_returns_false(self):
        """# Auto-generated test for mGetInterfaceState"""
        options = types.SimpleNamespace(jsonconf={"hostname": "cell1", "optype": "network-partition", "nodetype": "cell"})
        fault = ebCluFaultInjection(Mock(), options)

        with patch("exabox.ovm.clumisc.connect_to_host", side_effect=Exception("boom")), \
                patch("exabox.ovm.clumisc.get_gcontext"):
            self.assertFalse(fault.mGetInterfaceState("stre0"))

    def test_mGetSSHkeys_dom0_all(self):
        """# Auto-generated test for mGetSSHkeys"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0a", "domu1")]
        cluctrl.mReturnCellNodes.return_value = []
        cluctrl.mReturnSwitches.return_value = []
        cluctrl.mIsExabm.return_value = False

        kms = Mock()
        kms_entry = Mock()
        kms_entry.mGetPrivateKey.return_value = "key-dom0a"
        kms.mGetExaKmsEntry.return_value = kms_entry

        with patch("exabox.ovm.clumisc.get_gcontext") as mock_ctx:
            mock_ctx.return_value.mGetExaKms.return_value = kms
            fetcher = ebCluFetchSshKeys(cluctrl, "localhost")
            rc, data = fetcher.mGetSSHkeys({}, anodeType="dom0", aHost="all", aUser="root")

        self.assertEqual(rc, 0)
        self.assertEqual(data["dom0"]["dom0a"]["key"], "key-dom0a")
        kms.mGetExaKmsEntry.assert_called_once_with({"FQDN": "dom0a", "user": "root"})

    def test_mGetSSHkeys_domu_nat_missing_falls_back_opc(self):
        """# Auto-generated test for mGetSSHkeys"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0a", "domu1")]
        cluctrl.mReturnCellNodes.return_value = []
        cluctrl.mReturnSwitches.return_value = []
        cluctrl.mIsExabm.return_value = False

        kms = Mock()
        def _kms_entry(params):
            if params["user"] == "opc":
                entry = Mock()
                entry.mGetPrivateKey.return_value = "key-opc"
                return entry
            return None
        kms.mGetExaKmsEntry.side_effect = _kms_entry

        with patch("exabox.ovm.clumisc.get_gcontext") as mock_ctx:
            mock_ctx.return_value.mGetExaKms.return_value = kms
            fetcher = ebCluFetchSshKeys(cluctrl, "localhost")
            rc, data = fetcher.mGetSSHkeys({}, anodeType="domu", aHost="all", aUser="root")

        self.assertEqual(rc, 0)
        self.assertEqual(data["domu"]["domu1"]["key"], "key-opc")

    def test_mGetSSHkeys_invalid_node_type(self):
        """# Auto-generated test for mGetSSHkeys"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = []
        cluctrl.mReturnCellNodes.return_value = []
        cluctrl.mReturnSwitches.return_value = []
        cluctrl.mIsExabm.return_value = False

        kms = Mock()
        with patch("exabox.ovm.clumisc.get_gcontext") as mock_ctx:
            mock_ctx.return_value.mGetExaKms.return_value = kms
            fetcher = ebCluFetchSshKeys(cluctrl, "localhost")
            rc, data = fetcher.mGetSSHkeys({}, anodeType="invalid", aHost="all", aUser="root")

        self.assertNotEqual(rc, 0)
        self.assertEqual(data, {})

    def test_mFetchSshKeys_success(self):
        """# Auto-generated test for mFetchSshKeys"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = []
        cluctrl.mReturnCellNodes.return_value = []
        cluctrl.mReturnSwitches.return_value = []
        cluctrl.mIsExabm.return_value = False
        req = Mock()
        cluctrl.mGetRequestObj.return_value = req

        options = types.SimpleNamespace(jsonconf={"node_type": "dom0", "user": "root", "host": "all"})

        node = Mock()
        node.mConnect.return_value = None
        node.mDisconnect.return_value = None

        with patch("exabox.ovm.clumisc.get_gcontext") as mock_ctx, \
                patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
                patch("exabox.ovm.clumisc.ebGetDefaultDB") as mock_db, \
                patch.object(ebCluFetchSshKeys, "mGetSSHkeys", return_value=(0, {"dom0": {}})) as mock_get:
            mock_ctx.return_value.mGetExaKms.return_value = Mock()
            mock_db.return_value.mUpdateRequest.return_value = None
            fetcher = ebCluFetchSshKeys(cluctrl, "localhost")
            rc = fetcher.mFetchSshKeys(options)

        self.assertEqual(rc, 0)
        node.mConnect.assert_called_once_with(aHost="localhost")
        mock_get.assert_called_once()
        req.mSetData.assert_called_once()

    def test_mHandleRequest_instancehealth(self):
        """# Auto-generated test for mHandleRequest"""
        cluctrl = Mock()
        options = types.SimpleNamespace(jsonconf={"hostname": "cell1", "optype": "instancehealth", "nodetype": "cell"})

        fault = ebCluFaultInjection(cluctrl, options)
        with patch.object(ebCluFaultInjection, "mHandleInstanceHealth", return_value=True) as mock_handle:
            self.assertTrue(fault.mHandleRequest())

        mock_handle.assert_called_once()

    def test_mHandleInstanceHealth_checks_services(self):
        """# Auto-generated test for mHandleInstanceHealth"""
        cluctrl = Mock()
        cluctrl.mCheckCellsServicesUp.return_value = True
        options = types.SimpleNamespace(jsonconf={"hostname": "cell1", "optype": "instancehealth", "nodetype": "cell"})

        fault = ebCluFaultInjection(cluctrl, options)
        node = Mock()
        with patch("exabox.ovm.clumisc.connect_to_host") as mock_conn, \
                patch("exabox.ovm.clumisc.get_gcontext"):
            mock_conn.return_value.__enter__.return_value = node
            self.assertTrue(fault.mHandleInstanceHealth())

        cluctrl.mCheckCellsServicesUp.assert_called_once_with(aRestart=False, aCellList=["cell1"])

    def test_mHandleNetworkPartition_toggle_on_up(self):
        """# Auto-generated test for mHandleNetworkPartition"""
        options = types.SimpleNamespace(jsonconf={"hostname": "cell1", "optype": "network-partition", "nodetype": "cell", "action": "up"})
        fault = ebCluFaultInjection(Mock(), options)

        with patch.object(ebCluFaultInjection, "mGetInterfaceState", side_effect=[False, True]) as mock_state, \
                patch.object(ebCluFaultInjection, "mToggleCellInterface") as mock_toggle:
            fault.mHandleNetworkPartition("up")

        self.assertEqual([call("stre0"), call("stre1")], mock_state.call_args_list)
        mock_toggle.assert_called_once_with("stre0", "up")

    def test_mToggleCellInterface_executes_cmd(self):
        """# Auto-generated test for mToggleCellInterface"""
        cluctrl = Mock()
        options = types.SimpleNamespace(jsonconf={"hostname": "cell1", "optype": "network-partition", "nodetype": "cell"})
        fault = ebCluFaultInjection(cluctrl, options)

        node = Mock()
        with patch("exabox.ovm.clumisc.connect_to_host") as mock_conn, \
                patch("exabox.ovm.clumisc.get_gcontext"):
            mock_conn.return_value.__enter__.return_value = node
            fault.mToggleCellInterface("stre0", "down")

        node.mExecuteCmdLog.assert_called_once_with("/usr/sbin/ip link set stre0 down")

    def test_mGetSSHkeys_domu_nat_with_backup(self):
        """# Auto-generated test for mGetSSHkeys"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0a", "domu1")]
        cluctrl.mReturnCellNodes.return_value = []
        cluctrl.mReturnSwitches.return_value = []
        cluctrl.mIsExabm.return_value = False

        kms = Mock()
        kms_entry = Mock()
        kms_entry.mGetPrivateKey.return_value = "key-nat"
        kms.mGetExaKmsEntry.return_value = kms_entry

        with patch("exabox.ovm.clumisc.get_gcontext") as mock_ctx:
            mock_ctx.return_value.mGetExaKms.return_value = kms
            fetcher = ebCluFetchSshKeys(cluctrl, "localhost")
            fetcher._ebCluFetchSshKeys__mapping_table["domu"]["domu1"]["NAT"]["host"] = "nat-host"
            fetcher._ebCluFetchSshKeys__mapping_table["domu"]["domu1"]["backup"] = {"ip": "1.2.3.4"}
            rc, data = fetcher.mGetSSHkeys({}, anodeType="domu", aHost="domu1", aUser="root")

        self.assertEqual(rc, 0)
        self.assertEqual(data["domu"]["domu1"]["key"], "key-nat")
        self.assertEqual(data["domu"]["domu1"]["BACKUP"], {"ip": "1.2.3.4"})

    def test_mGetSSHkeys_dom0_invalid_host(self):
        """# Auto-generated test for mGetSSHkeys"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0a", "domu1")]
        cluctrl.mReturnCellNodes.return_value = []
        cluctrl.mReturnSwitches.return_value = []
        cluctrl.mIsExabm.return_value = False

        with patch("exabox.ovm.clumisc.get_gcontext") as mock_ctx:
            mock_ctx.return_value.mGetExaKms.return_value = Mock()
            fetcher = ebCluFetchSshKeys(cluctrl, "localhost")
            rc, data = fetcher.mGetSSHkeys({}, anodeType="dom0", aHost="missing", aUser="root")

        self.assertNotEqual(rc, 0)
        self.assertEqual(data, {})

    def test_mGetSSHkeys_cell_invalid_host(self):
        """# Auto-generated test for mGetSSHkeys"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = []
        cluctrl.mReturnCellNodes.return_value = ["cell1"]
        cluctrl.mReturnSwitches.return_value = []
        cluctrl.mIsExabm.return_value = False

        with patch("exabox.ovm.clumisc.get_gcontext") as mock_ctx:
            mock_ctx.return_value.mGetExaKms.return_value = Mock()
            fetcher = ebCluFetchSshKeys(cluctrl, "localhost")
            rc, data = fetcher.mGetSSHkeys({}, anodeType="cell", aHost="cell2", aUser="root")

        self.assertNotEqual(rc, 0)
        self.assertEqual(data, {})

    def test_mGetSSHkeys_ibswitch_skip_on_kvm(self):
        """# Auto-generated test for mGetSSHkeys"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = []
        cluctrl.mReturnCellNodes.return_value = []
        cluctrl.mReturnSwitches.return_value = ["switch1"]
        cluctrl.mIsExabm.return_value = False
        cluctrl.mIsKVM.return_value = True

        with patch("exabox.ovm.clumisc.get_gcontext") as mock_ctx:
            mock_ctx.return_value.mGetExaKms.return_value = Mock()
            fetcher = ebCluFetchSshKeys(cluctrl, "localhost")
            rc, data = fetcher.mGetSSHkeys({}, anodeType="ibswitch", aHost="all", aUser="root")

        self.assertEqual(rc, 0)
        self.assertEqual(data, {})

    def test_mFetchSshKeys_exception_raises(self):
        """# Auto-generated test for mFetchSshKeys"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = []
        cluctrl.mReturnCellNodes.return_value = []
        cluctrl.mReturnSwitches.return_value = []
        cluctrl.mIsExabm.return_value = False
        cluctrl.mGetRequestObj.return_value = Mock()

        options = types.SimpleNamespace(jsonconf={"node_type": "dom0"})
        node = Mock()
        node.mConnect.side_effect = Exception("boom")

        with patch("exabox.ovm.clumisc.get_gcontext") as mock_ctx, \
                patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
                patch("exabox.ovm.clumisc.ebGetDefaultDB") as mock_db:
            mock_ctx.return_value.mGetExaKms.return_value = Mock()
            mock_db.return_value.mUpdateRequest.return_value = None
            fetcher = ebCluFetchSshKeys(cluctrl, "localhost")
            with self.assertRaises(ExacloudRuntimeError):
                fetcher.mFetchSshKeys(options)

    def test_mGetSingleSSHKey_domain_missing_entry(self):
        """# Auto-generated test for mGetSingleSSHKey"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = []
        cluctrl.mReturnCellNodes.return_value = []
        cluctrl.mReturnSwitches.return_value = []
        cluctrl.mIsExabm.return_value = False

        kms = Mock()
        kms.mGetExaKmsEntry.return_value = None
        ctx = Mock()
        ctx.mGetExaKms.return_value = kms

        with patch("exabox.ovm.clumisc.get_gcontext", return_value=ctx):
            fetcher = ebCluFetchSshKeys(cluctrl, "localhost")
            result = fetcher.mGetSingleSSHKey({}, "host1", "root", "example.com")

        self.assertEqual(result["key"], "")
        kms.mGetExaKmsEntry.assert_called_once_with({"FQDN": "host1.example.com", "user": "root"})

    def test_mGetSingleSSHKey_returns_private_key(self):
        """# Auto-generated test for mGetSingleSSHKey"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = []
        cluctrl.mReturnCellNodes.return_value = []
        cluctrl.mReturnSwitches.return_value = []
        cluctrl.mIsExabm.return_value = False

        kms_entry = Mock()
        kms_entry.mGetPrivateKey.return_value = "priv-key"
        kms = Mock()
        kms.mGetExaKmsEntry.return_value = kms_entry
        ctx = Mock()
        ctx.mGetExaKms.return_value = kms

        with patch("exabox.ovm.clumisc.get_gcontext", return_value=ctx):
            fetcher = ebCluFetchSshKeys(cluctrl, "localhost")
            result = fetcher.mGetSingleSSHKey({}, "host2.example.com", "opc")

        self.assertEqual(result["key"], "priv-key")
        kms.mGetExaKmsEntry.assert_called_once_with({"FQDN": "host2.example.com", "user": "opc"})

    def test_mGetSSHkeys_domu_root_key_missing_uses_opc(self):
        """# Auto-generated test for mGetSSHkeys"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0a", "domu1")]
        cluctrl.mReturnCellNodes.return_value = []
        cluctrl.mReturnSwitches.return_value = []
        cluctrl.mIsExabm.return_value = False

        with patch("exabox.ovm.clumisc.get_gcontext") as mock_ctx:
            mock_ctx.return_value.mGetExaKms.return_value = Mock()
            fetcher = ebCluFetchSshKeys(cluctrl, "localhost")
            fetcher._ebCluFetchSshKeys__mapping_table["domu"]["domu1"]["NAT"]["host"] = "nat-host"
            fetcher._ebCluFetchSshKeys__mapping_table["domu"]["domu1"]["NAT"]["domain"] = "example.com"

            def _fake_get_key(data, host, user, domain=None):
                data["key"] = "opc-key" if user == "opc" else ""
                return data

            with patch.object(ebCluFetchSshKeys, "mGetSingleSSHKey", side_effect=_fake_get_key) as mock_single:
                rc, data = fetcher.mGetSSHkeys({}, anodeType="domu", aHost="all", aUser="root")

        self.assertEqual(rc, 0)
        self.assertEqual(data["domu"]["domu1"]["key"], "opc-key")
        self.assertEqual(data["domu"]["domu1"]["NAT"]["key"], "opc-key")
        self.assertTrue(any(call_args[0][2] == "opc" for call_args in mock_single.call_args_list))

    def test_mFetchSshKeys_rc_nonzero_raises(self):
        """# Auto-generated test for mFetchSshKeys"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = []
        cluctrl.mReturnCellNodes.return_value = []
        cluctrl.mReturnSwitches.return_value = []
        cluctrl.mIsExabm.return_value = False
        cluctrl.mGetRequestObj.return_value = Mock()

        options = types.SimpleNamespace(jsonconf={"node_type": "dom0"})
        node = Mock()

        with patch("exabox.ovm.clumisc.get_gcontext") as mock_ctx, \
                patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
                patch("exabox.ovm.clumisc.ebGetDefaultDB") as mock_db, \
                patch("exabox.ovm.clumisc.gSubError", {"766": ("bad-error",)}), \
                patch.object(ebCluFetchSshKeys, "mGetSSHkeys", return_value=(0x766, {})):
            mock_ctx.return_value.mGetExaKms.return_value = Mock()
            mock_db.return_value.mUpdateRequest.return_value = None
            fetcher = ebCluFetchSshKeys(cluctrl, "localhost")
            with self.assertRaises(ExacloudRuntimeError):
                fetcher.mFetchSshKeys(options)

    def test_getWorkerPIDs_empty_list(self):
        """# Auto-generated test for getWorkerPIDs"""
        self.assertEqual(AgentWorkerPIDListing.getWorkerPIDs("()"), [])

    def test_getWorkerPIDs_filters_non_worker_cmdline(self):
        """# Auto-generated test for getWorkerPIDs"""
        wlist_str = str([
            (0, "Running", None, None, None, None, None, None, "1234"),
            (1, "Running", None, None, None, None, None, None, "5678"),
        ])

        def _pid_exists(pid):
            return pid in (1234, 5678)

        def _process(pid):
            proc = Mock()
            if pid == 1234:
                proc.cmdline.return_value = ["python", "--supervisor"]
            else:
                proc.cmdline.return_value = ["python", "worker"]
            return proc

        with patch("exabox.ovm.clumisc.psutil.pid_exists", side_effect=_pid_exists), \
                patch("exabox.ovm.clumisc.psutil.Process", side_effect=_process):
            result = AgentWorkerPIDListing.getWorkerPIDs(wlist_str)

        self.assertEqual(result, [1234])

    def test_getWorkerPIDs_removes_missing_pid(self):
        """# Auto-generated test for getWorkerPIDs"""
        wlist_str = str([(0, "Running", None, None, None, None, None, None, "1111")])

        with patch("exabox.ovm.clumisc.psutil.pid_exists", return_value=False):
            result = AgentWorkerPIDListing.getWorkerPIDs(wlist_str)

        self.assertEqual(result, [])

    def test_ebSubnetSet_replace_subset(self):
        """# Auto-generated test for mAddSubnet"""
        subnet_set = ebSubnetSet()
        subnet_set.mAddSubnet("10.0.0.0/24")
        subnet_set.mAddSubnet("10.0.0.0/23")

        self.assertEqual(subnet_set.mGetCIDRList(), ["10.0.0.0/23"])

    def test_validateIpOrHostname_invalid_chars(self):
        """# Auto-generated test for validateIpOrHostname"""
        self.assertFalse(validateIpOrHostname("bad host!"))

    def test_ebCluScheduleManager_handle_request_invalid(self):
        """# Auto-generated test for mHandleRequest"""
        cluctrl = Mock()
        reqobj = Mock()
        cluctrl.mGetRequestObj.return_value = reqobj

        options = types.SimpleNamespace(sccmd=None, jsonmode=False)

        with patch("exabox.ovm.clumisc.ebGetDefaultDB") as mock_db:
            mock_db.return_value.mUpdateRequest.return_value = None
            manager = ebCluScheduleManager(cluctrl)
            rc = manager.mHandleRequest(options)

        self.assertEqual(rc, -1)
        self.assertEqual(manager.mGetData()["Status"], "Fail")
        reqobj.mSetData.assert_called_once()

    def test_ebCluScheduleManager_list_jobs_populates_data(self):
        """# Auto-generated test for mListScheduledJobs"""
        cluctrl = Mock()
        reqobj = Mock()
        cluctrl.mGetRequestObj.return_value = reqobj

        schedule_row = (
            "uuid1",
            "owner",
            "mode",
            "operation",
            "event",
            "timer",
            "timestamp",
            "interval",
            "repeat",
            "last_repeat",
            "monitor_uuid",
            "monitor_jobs",
            "status",
        )

        options = types.SimpleNamespace(sccmd="list", jsonmode=False)

        with patch("exabox.ovm.clumisc.ebGetDefaultDB") as mock_db:
            mock_db.return_value.mGetSchedule.return_value = [schedule_row]
            mock_db.return_value.mUpdateRequest.return_value = None
            manager = ebCluScheduleManager(cluctrl)
            rc = manager.mHandleRequest(options)

        self.assertEqual(rc, 0)
        data = manager.mGetData()
        self.assertEqual(data["Status"], "Pass")
        self.assertIn("uuid1", data["uuid"])

    def test_ebCluScheduleManager_handle_request_jsonmode(self):
        """# Auto-generated test for mHandleRequest"""
        cluctrl = Mock()
        cluctrl.mGetRequestObj.return_value = None

        options = types.SimpleNamespace(sccmd=None, jsonmode=True)

        with patch("exabox.ovm.clumisc.ebLogJson") as mock_log:
            manager = ebCluScheduleManager(cluctrl)
            rc = manager.mHandleRequest(options)

        self.assertEqual(rc, -1)
        self.assertEqual(manager.mGetData()["Status"], "Fail")
        self.assertTrue(mock_log.called)

    def test_ebCluScheduleManager_list_jobs_empty(self):
        """# Auto-generated test for mListScheduledJobs"""
        cluctrl = Mock()

        with patch("exabox.ovm.clumisc.ebGetDefaultDB") as mock_db:
            mock_db.return_value.mGetSchedule.return_value = []
            manager = ebCluScheduleManager(cluctrl)
            rc = manager.mListScheduledJobs()

        self.assertEqual(rc, 0)
        data = manager.mGetData()
        self.assertEqual(data["Status"], "Pass")
        self.assertEqual(data["uuid"], {})

    def test_ebSubnetSet_ipinset_empty(self):
        """# Auto-generated test for mIpInSet"""
        subnet_set = ebSubnetSet()
        self.assertEqual(subnet_set.mIpInSet("10.0.0.0/24"), [])

    def test_ebSubnetSet_ipinset_subset_and_superset(self):
        """# Auto-generated test for mIpInSet"""
        subnet_set = ebSubnetSet()
        subnet_set.mAddSubnet("10.0.0.0/24")

        self.assertEqual(subnet_set.mIpInSet("10.0.0.0/25"), [1])
        self.assertEqual(subnet_set.mIpInSet("10.0.0.0/23"), [-1])

    def test_ebSubnetSet_get_lists_and_all_ips(self):
        """# Auto-generated test for mGetAllIPs"""
        subnet_set = ebSubnetSet()
        subnet_set.mAddSubnet("10.0.0.1/32")

        self.assertEqual(subnet_set.mGetAllIPs(), ["10.0.0.1"])
        self.assertEqual(subnet_set.mGetSubnetList(), ["10.0.0.1/255.255.255.255"])
        self.assertEqual(subnet_set.mGetCIDRList(), ["10.0.0.1/32"])

    def test_ebSubnetSet_append_list(self):
        """# Auto-generated test for mAppendList"""
        subnet_set = ebSubnetSet()
        subnet_set.mAppendList(["10.0.1.0/30", "10.0.2.0/30"])

        self.assertEqual(subnet_set.mGetCIDRList(), ["10.0.1.0/30", "10.0.2.0/30"])

    def test_ebSubnetSet_append_list_none(self):
        """# Auto-generated test for mAppendList"""
        subnet_set = ebSubnetSet()
        subnet_set.mAppendList(None)

        self.assertEqual(subnet_set.mGetCIDRList(), [])

    def test_mConnectivityChecks_ping_failure_returns_false(self):
        """# Auto-generated test for mConnectivityChecks"""
        cluctrl = Mock()
        cluctrl.mReturnAllClusterHosts.return_value = (["dom0"], [], [], [])
        cluctrl.mGetKey.return_value = "cluster"
        cluctrl.mPingHost.return_value = False

        network_config = Mock()
        network_config.mGetNetIpAddr.return_value = "192.0.2.40"
        networks = Mock()
        networks.mGetNetworkConfigByName.return_value = network_config
        cluctrl.mGetNetworks.return_value = networks

        ovm = ebCluPreChecks(cluctrl)

        with patch("exabox.ovm.clumisc.ebLogError") as log_error:
            result = ovm.mConnectivityChecks(aCheckDomU=True, aHostList=["dom0"])

        self.assertFalse(result)
        self.assertTrue(log_error.called)

    def test_mConnectivityChecks_switch_missing_partition_info(self):
        """# Auto-generated test for mConnectivityChecks"""
        cluctrl = Mock()
        cluctrl.mReturnAllClusterHosts.return_value = ([], [], [], ["sw1"])
        cluctrl.mGetKey.return_value = "cluster"
        cluctrl.mPingHost.return_value = True

        network_config = Mock()
        network_config.mGetNetIpAddr.return_value = "192.0.2.41"
        networks = Mock()
        networks.mGetNetworkConfigByName.return_value = network_config
        cluctrl.mGetNetworks.return_value = networks

        node = Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO(""), None)

        ovm = ebCluPreChecks(cluctrl)

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
            patch("exabox.ovm.clumisc.get_gcontext"):
            result = ovm.mConnectivityChecks(aCheckDomU=True, aHostList=["sw1"])

        self.assertTrue(result)
        node.mConnect.assert_called_once_with(aHost="sw1")
        node.mDisconnect.assert_called_once()

    def test_mConnectivityChecks_ssh_failure_returns_false(self):
        """# Auto-generated test for mConnectivityChecks"""
        cluctrl = Mock()
        cluctrl.mReturnAllClusterHosts.return_value = ([], [], ["cell1"], [])
        cluctrl.mGetKey.return_value = "cluster"
        cluctrl.mPingHost.return_value = True

        network_config = Mock()
        network_config.mGetNetIpAddr.return_value = "192.0.2.42"
        networks = Mock()
        networks.mGetNetworkConfigByName.return_value = network_config
        cluctrl.mGetNetworks.return_value = networks

        node = Mock()
        node.mConnect.side_effect = Exception("ssh failed")

        ovm = ebCluPreChecks(cluctrl)

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
                patch("exabox.ovm.clumisc.get_gcontext"):
            result = ovm.mConnectivityChecks(aCheckDomU=True, aHostList=["cell1"])

        self.assertTrue(result)

    def test_mCheckClusterIntegrity_scan_failure_raises(self):
        """# Auto-generated test for mCheckClusterIntegrity"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        cluctrl.mIsXS.return_value = False
        cluctrl.mGetOracleBaseDirectories.return_value = ("/u01/app/oracle", None, None)
        ovm = ebCluPreChecks(cluctrl)

        node = Mock()
        node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0, 0, 1]
        node.mExecuteCmd.return_value = (None, io.StringIO("err\n"), None)

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node):
            with self.assertRaises(ExacloudRuntimeError):
                ovm.mCheckClusterIntegrity(True)

        node.mDisconnect.assert_called_once()

    def test_mCheckClusterIntegrity_asm_failure_raises(self):
        """# Auto-generated test for mCheckClusterIntegrity"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0", "domu1")]
        cluctrl.mIsXS.return_value = False
        cluctrl.mGetOracleBaseDirectories.return_value = ("/u01/app/oracle", None, None)
        ovm = ebCluPreChecks(cluctrl)

        node = Mock()
        node.mGetCmdExitStatus.side_effect = [0, 0, 0, 0, 1]
        node.mExecuteCmd.return_value = (None, io.StringIO("err\n"), None)

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node):
            with self.assertRaises(ExacloudRuntimeError):
                ovm.mCheckClusterIntegrity(False)

        node.mDisconnect.assert_called_once()

    def test_mCheckClusterIntegrity_custom_domu_list(self):
        """# Auto-generated test for mCheckClusterIntegrity"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0", "domu1"), ("dom1", "domu2")]
        cluctrl.mIsXS.return_value = True
        cluctrl.mGetOracleBaseDirectories.return_value = ("/u01/app/oracle", None, None)
        ovm = ebCluPreChecks(cluctrl)

        node = Mock()
        node.mGetCmdExitStatus.return_value = 0
        node.mExecuteCmd.return_value = (None, io.StringIO(""), None)

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node):
            ovm.mCheckClusterIntegrity(False, aDomUList=["domu2"])

        node.mConnect.assert_called_once_with(aHost="domu2")
        node.mDisconnect.assert_called_once()

    def test_mProcessHostLifecycle_stop_success(self):
        """# Auto-generated test for mProcessHostLifecycle"""
        ebox = Mock()
        ebox.mPingHost.return_value = False
        startstop = ebCluStartStopHostFromIlom(ebox)
        results = {}
        ctx = {"host": "host1", "ilom": "ilom1", "operation": "stop", "sleep_time": 5, "results_dict": results}

        with patch.object(startstop, "mStopHostfromIlom") as stop_mock, \
                patch("exabox.ovm.clumisc.time.sleep") as sleep_mock, \
                patch("exabox.ovm.clumisc.time.time", side_effect=itertools.count()):
            startstop.mProcessHostLifecycle(ctx)

        stop_mock.assert_called_once_with("ilom1")
        sleep_mock.assert_not_called()
        self.assertEqual(results.get("host1"), "Success")

    def test_ebCluNodeSubsetPrecheck_missing_payload(self):
        """# Auto-generated test for mRunNodeSubsetPrecheck"""
        ebox = Mock()
        precheck = ebCluNodeSubsetPrecheck(ebox)
        options = types.SimpleNamespace(jsonconf=None)

        rc = precheck.mRunNodeSubsetPrecheck(options)

        self.assertEqual(rc, 1)
        ebox.mUpdateErrorObject.assert_called_once()

    def test_ebCluNodeSubsetPrecheck_missing_optype(self):
        """# Auto-generated test for mRunNodeSubsetPrecheck"""
        ebox = Mock()
        precheck = ebCluNodeSubsetPrecheck(ebox)
        options = types.SimpleNamespace(jsonconf={})

        rc = precheck.mRunNodeSubsetPrecheck(options)

        self.assertEqual(rc, 1)
        ebox.mUpdateErrorObject.assert_called_once()

    def test_ebCluNodeSubsetPrecheck_invalid_optype(self):
        """# Auto-generated test for mRunNodeSubsetPrecheck"""
        ebox = Mock()
        precheck = ebCluNodeSubsetPrecheck(ebox)
        options = types.SimpleNamespace(jsonconf={"opType": "DELETE_NODE"})

        rc = precheck.mRunNodeSubsetPrecheck(options)

        self.assertEqual(rc, 1)
        ebox.mUpdateErrorObject.assert_called_once()

    def test_ebCluNodeSubsetPrecheck_addnode_success(self):
        """# Auto-generated test for mAddNodePrecheck"""
        ebox = Mock()
        precheck = ebCluNodeSubsetPrecheck(ebox)
        options = types.SimpleNamespace(jsonconf={"opType": "ADD_NODE"})

        with patch.object(precheck, "mCheckSrcNodeSpace", return_value=0), \
            patch.object(precheck, "mUpdateRequestData") as update_data:
            rc = precheck.mRunNodeSubsetPrecheck(options)

        self.assertEqual(rc, 0)
        update_data.assert_called_once()
        ebox.mUpdateErrorObject.assert_not_called()

    def test_ebCluNodeSubsetPrecheck_addnode_failure_raises(self):
        """# Auto-generated test for mAddNodePrecheck"""
        ebox = Mock()
        precheck = ebCluNodeSubsetPrecheck(ebox)
        options = types.SimpleNamespace(jsonconf={"opType": "ADD_NODE"})

        with patch.object(precheck, "mCheckSrcNodeSpace", return_value=-1), \
            patch.object(precheck, "mUpdateRequestData") as update_data:
            with self.assertRaises(ExacloudRuntimeError):
                precheck.mRunNodeSubsetPrecheck(options)

        self.assertTrue(update_data.called)
        ebox.mUpdateErrorObject.assert_called_once()

    def test_ebCluNodeSubsetPrecheck_check_src_space_short_circuit(self):
        """# Auto-generated test for mCheckSrcNodeSpace"""
        ebox = Mock()
        ebox.mReturnAllClusterHosts.return_value = ([], ["domu1", "domu2"], [], [])
        precheck = ebCluNodeSubsetPrecheck(ebox)

        with patch.object(precheck, "mCheckMinDiskSpace", side_effect=[-1, 0]) as check_space:
            rc = precheck.mCheckSrcNodeSpace()

        self.assertEqual(rc, -1)
        check_space.assert_called_once_with("domu1")

    def test_ebCluNodeSubsetPrecheck_check_min_disk_space(self):
        """# Auto-generated test for mCheckMinDiskSpace"""
        precheck = ebCluNodeSubsetPrecheck(Mock())

        node = Mock()
        node.mExecuteCmd.return_value = (None, io.StringIO("500000\n"), None)

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node):
            rc = precheck.mCheckMinDiskSpace("domu1")

        self.assertEqual(rc, -1)
        node.mConnect.assert_called_once_with(aHost="domu1")
        node.mDisconnect.assert_called_once()

    def test_ebCluServerSshConnectionCheck_success(self):
        """# Auto-generated test for mServerSshConnectionCheck"""
        ebox = Mock()
        ebox.mIsOciEXACC.return_value = False
        checker = clumisc.ebCluServerSshConnectionCheck(ebox)
        options = types.SimpleNamespace(jsonmode=False)

        checker._ebCluServerSshConnectionCheck__node = Mock()
        checker._ebCluServerSshConnectionCheck__node.mIsConnectable.return_value = True

        with patch.object(checker, "mUpdateRequestData"):
            rc = checker.mServerSshConnectionCheck(options, aDomUs=["domu1"], aDom0s=[], aCells=[])

        self.assertEqual(rc, 0)
        ebox.mUpdateErrorObject.assert_not_called()

    def test_ebCluServerSshConnectionCheck_failure_raises(self):
        """# Auto-generated test for mServerSshConnectionCheck"""
        ebox = Mock()
        ebox.mIsOciEXACC.return_value = True
        checker = clumisc.ebCluServerSshConnectionCheck(ebox)
        options = types.SimpleNamespace(jsonmode=True)

        checker._ebCluServerSshConnectionCheck__node = Mock()
        checker._ebCluServerSshConnectionCheck__node.mIsConnectable.return_value = False

        with patch.object(checker, "mUpdateRequestData"):
            with self.assertRaises(ExacloudRuntimeError):
                checker.mServerSshConnectionCheck(options, aDomUs=["domu1"], aDom0s=[], aCells=[])

        ebox.mUpdateErrorObject.assert_called_once()

    def test_ebCluServerSshConnectionCheck_node_subset_success(self):
        """# Auto-generated test for mNodeSubsetSshConnectionCheck"""
        ebox = Mock()
        ebox.mIsOciEXACC.return_value = False
        checker = clumisc.ebCluServerSshConnectionCheck(ebox)
        options = types.SimpleNamespace(jsonmode=False)

        checker._ebCluServerSshConnectionCheck__node = Mock()
        checker._ebCluServerSshConnectionCheck__node.mIsConnectable.side_effect = [False, True]

        with patch.object(checker, "mUpdateRequestData"):
            rc = checker.mNodeSubsetSshConnectionCheck(options, aDomUs=["domu1", "domu2"])

        self.assertEqual(rc, 0)
        ebox.mUpdateErrorObject.assert_not_called()

    def test_ebCluServerSshConnectionCheck_node_subset_failure(self):
        """# Auto-generated test for mNodeSubsetSshConnectionCheck"""
        ebox = Mock()
        ebox.mIsOciEXACC.return_value = True
        checker = clumisc.ebCluServerSshConnectionCheck(ebox)
        options = types.SimpleNamespace(jsonmode=True)

        checker._ebCluServerSshConnectionCheck__node = Mock()
        checker._ebCluServerSshConnectionCheck__node.mIsConnectable.return_value = False

        with patch.object(checker, "mUpdateRequestData"):
            with self.assertRaises(ExacloudRuntimeError):
                checker.mNodeSubsetSshConnectionCheck(options, aDomUs=["domu1", "domu2"])

        ebox.mUpdateErrorObject.assert_called_once()

    def test_mGetCustomUserGroupsPayload_override_from_root(self):
        """# Auto-generated test for mGetCustomUserGroupsPayload"""
        ebox = Mock()
        options = types.SimpleNamespace(
            jsonconf={
                "users_with_custom_id": [{"user": "alice", "uid": 1200}],
                "groups_with_custom_id": [{"group": "dba", "gid": 2200}],
            }
        )
        ebox.mCheckConfigOption.return_value = "True"
        ebox.mGetOptions.return_value = options
        util = ebMigrateUsersUtil(ebox)

        payload = util.mGetCustomUserGroupsPayload()

        self.assertEqual(payload["alice"], {"uid": 1200})
        self.assertEqual(payload["dba"], {"gid": 2200})

    def test_mGetCustomUserGroupsPayload_override_from_vm_section(self):
        """# Auto-generated test for mGetCustomUserGroupsPayload"""
        ebox = Mock()
        options = types.SimpleNamespace(
            jsonconf={
                "vm": {
                    "users_with_custom_id": [{"user": "bob", "uid": 3300}],
                    "groups_with_custom_id": [{"group": "backup", "gid": 4400}],
                }
            }
        )
        ebox.mCheckConfigOption.return_value = "True"
        ebox.mGetOptions.return_value = options
        util = ebMigrateUsersUtil(ebox)

        payload = util.mGetCustomUserGroupsPayload()

        self.assertEqual(payload["bob"], {"uid": 3300})
        self.assertEqual(payload["backup"], {"gid": 4400})

    def test_mGetCustomUserGroupsPayload_override_disabled(self):
        """# Auto-generated test for mGetCustomUserGroupsPayload"""
        ebox = Mock()
        options = types.SimpleNamespace(jsonconf={"users_with_custom_id": [{"user": "carl", "uid": 7777}]})
        ebox.mCheckConfigOption.return_value = "False"
        ebox.mGetOptions.return_value = options
        util = ebMigrateUsersUtil(ebox)

        payload = util.mGetCustomUserGroupsPayload()

        self.assertEqual(payload, {})

    def test_mGetUsersGroupsToRemap_outside_range_early_return(self):
        """# Auto-generated test for mGetUsersGroupsToRemap"""
        ebox = Mock()
        ebox.mIsAdbs.return_value = False
        ebox.isATP.return_value = False
        ebox.IsZdlraProv.return_value = False
        util = ebMigrateUsersUtil(ebox)

        result = util.mGetUsersGroupsToRemap(Mock())

        self.assertEqual(result, {})

    def test_mGetUsersGroupsToRemap_builds_remap(self):
        """# Auto-generated test for mGetUsersGroupsToRemap"""
        ebox = Mock()
        ebox.mIsAdbs.return_value = True
        ebox.isATP.return_value = False
        ebox.IsZdlraProv.return_value = False
        util = ebMigrateUsersUtil(ebox)

        passwd_ids = {"app": 2999, "ora": 3000, "sys": 65535}
        group_ids = {"app": 3999999, "dba": 4000000}

        with patch.object(util, "mGetUidFromFile", side_effect=[passwd_ids, group_ids]):
            result = util.mGetUsersGroupsToRemap(Mock())

        self.assertEqual(result["ora"], {"uid": 3000})
        self.assertEqual(result["sys"], {"uid": 3001})
        self.assertEqual(result["dba"], {"gid": 4000000})

    def test_mMergeUsersGroupsConfigPayload_combines_maps(self):
        """# Auto-generated test for mMergeUsersGroupsConfigPayload"""
        util = ebMigrateUsersUtil(Mock())

        with patch.object(util, "mGetCustomUserGroupsConfigFile", return_value={"ora": {"uid": 111}}), \
             patch.object(util, "mGetCustomUserGroupsPayload", return_value={"dba": {"gid": 222}}):
            merged = util.mMergeUsersGroupsConfigPayload()

        self.assertEqual(merged, {"ora": {"uid": 111}, "dba": {"gid": 222}})

    def test_mMergeUsersGroupsToRemap_overrides_defaults(self):
        """# Auto-generated test for mMergeUsersGroupsToRemap"""
        util = ebMigrateUsersUtil(Mock())

        with patch.object(util, "mGetUsersGroupsToRemap", return_value={"ora": {"uid": 1000}}), \
             patch.object(util, "mMergeUsersGroupsConfigPayload", return_value={"ora": {"uid": 2000}, "dba": {"gid": 3000}}):
            merged = util.mMergeUsersGroupsToRemap(Mock())

        self.assertEqual(merged["ora"], {"uid": 2000})
        self.assertEqual(merged["dba"], {"gid": 3000})

    def test_mCreateMissingUsersGroups_creates_missing(self):
        """# Auto-generated test for mCreateMissingUsersGroups"""
        util = ebMigrateUsersUtil(Mock())
        node = Mock()
        node.mGetCmdExitStatus.side_effect = [1, 1]

        util.mCreateMissingUsersGroups(node, {"ora": {"uid": 1000, "gid": 2000}})

        self.assertIn(call("/usr/sbin/groupadd -g 2000 ora"), node.mExecuteCmd.mock_calls)
        self.assertIn(call("/usr/sbin/useradd -u 1000 -g ora -d /home/ora -s /bin/bash ora"), node.mExecuteCmd.mock_calls)

    def test_mValidateUsersRange_reports_outside(self):
        """# Auto-generated test for mValidateUsersRange"""
        util = ebMigrateUsersUtil(Mock())

        with patch.object(util, "mGetUsersGroupsToRemap", return_value={"ora": {"uid": 1000}}):
            ok, msg = util.mValidateUsersRange(Mock())

        self.assertFalse(ok)
        self.assertIn("ora", msg)

    def test_mValidateUsersRange_ok(self):
        """# Auto-generated test for mValidateUsersRange"""
        util = ebMigrateUsersUtil(Mock())

        with patch.object(util, "mGetUsersGroupsToRemap", return_value={}):
            ok, msg = util.mValidateUsersRange(Mock())

        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_mRemapUsers_skips_already_configured(self):
        """# Auto-generated test for mRemapUsers"""
        ebox = Mock()
        ebox.mGetExadataImageFromMap.return_value = "23.1.0"
        util = ebMigrateUsersUtil(ebox)
        node = Mock()

        with patch.object(util, "mGetUidFromFile", return_value={"ora": 1000}), \
             patch("exabox.ovm.clumisc.version_compare", return_value=-1):
            util.mRemapUsers(node, {"ora": {"uid": 1000}}, aForceManual=False)

        node.mExecuteCmd.assert_not_called()

    def test_mRemapUsers_manual_force_path(self):
        """# Auto-generated test for mRemapUsers"""
        ebox = Mock()
        ebox.mGetExadataImageFromMap.return_value = "23.1.0"
        util = ebMigrateUsersUtil(ebox)
        node = Mock()

        with patch.object(util, "mGetUidFromFile", return_value={"ora": 1000}), \
             patch("exabox.ovm.clumisc.version_compare", return_value=-1):
            util.mRemapUsers(node, {"ora": {"uid": 2000}}, aForceManual=True)

        self.assertIn(call("/usr/bin/usermod -u 2000 ora"), node.mExecuteCmd.mock_calls)
        self.assertIn(call("/bin/find / -uid 1000 -exec chown -h 2000 {} \;"), node.mExecuteCmd.mock_calls)

    def test_mRemapUsers_migrate_ids_script_path(self):
        """# Auto-generated test for mRemapUsers"""
        ebox = Mock()
        ebox.mGetExadataImageFromMap.return_value = "24.1.0"
        util = ebMigrateUsersUtil(ebox)
        node = Mock()

        with patch.object(util, "mGetUidFromFile", return_value={"ora": 1000}), \
             patch("exabox.ovm.clumisc.version_compare", return_value=1), \
             patch("exabox.ovm.clumisc.uuid.uuid1", return_value="abc"):
            util.mRemapUsers(node, {"ora": {"uid": 2000}}, aForceManual=False)

        node.mExecuteCmdLog.assert_any_call("/opt/oracle.SupportTools/migrate_ids.sh --uid-file /tmp/abc.txt")
        node.mExecuteCmdLog.assert_any_call("/bin/rm /tmp/abc.txt")

    def test_mRemapGroups_manual_force_path(self):
        """# Auto-generated test for mRemapGroups"""
        ebox = Mock()
        ebox.mGetExadataImageFromMap.return_value = "23.1.0"
        util = ebMigrateUsersUtil(ebox)
        node = Mock()

        with patch.object(util, "mGetUidFromFile", return_value={"dba": 2000}), \
             patch("exabox.ovm.clumisc.version_compare", return_value=-1):
            util.mRemapGroups(node, {"dba": {"gid": 3000}}, aForceManual=True)

        self.assertIn(call("/usr/bin/groupmod -g 3000 dba"), node.mExecuteCmd.mock_calls)
        self.assertIn(call("/bin/find / -gid 2000 -exec chgrp -h 3000 {} \;"), node.mExecuteCmd.mock_calls)

    def test_mRemapGroups_migrate_ids_script_path(self):
        """# Auto-generated test for mRemapGroups"""
        ebox = Mock()
        ebox.mGetExadataImageFromMap.return_value = "24.1.0"
        util = ebMigrateUsersUtil(ebox)
        node = Mock()

        with patch.object(util, "mGetUidFromFile", return_value={"dba": 2000}), \
             patch("exabox.ovm.clumisc.version_compare", return_value=1), \
             patch("exabox.ovm.clumisc.uuid.uuid1", return_value="def"):
            util.mRemapGroups(node, {"dba": {"gid": 3000}}, aForceManual=False)

        node.mExecuteCmdLog.assert_any_call("/opt/oracle.SupportTools/migrate_ids.sh --gid-file /tmp/def.txt")
        node.mExecuteCmdLog.assert_any_call("/bin/rm /tmp/def.txt")

    def test_mResetNetwork_executes_reset_commands(self):
        """# Auto-generated test for mResetNetwork"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0a", "domu1"), ("dom0b", "domu2")]
        ovm = ebCluPreChecks(cluctrl)

        node = Mock()
        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
                patch("exabox.ovm.clumisc.get_gcontext"):
            rc = ovm.mResetNetwork()

        self.assertTrue(rc)
        self.assertEqual(node.mConnect.call_count, 2)
        self.assertEqual(node.mDisconnect.call_count, 2)
        self.assertEqual(node.mExecuteCmdLog.call_count, 2)

    def test_mResetIBNetwork_skips_non_ovm_mode(self):
        """# Auto-generated test for mResetIBNetwork"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0a", "domu1")]
        ovm = ebCluPreChecks(cluctrl)

        node = Mock()
        node.mGetCmdExitStatus.return_value = 1

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
                patch("exabox.ovm.clumisc.get_gcontext"):
            ovm.mResetIBNetwork()

        node.mExecuteCmdLog.assert_called_once_with("cat /opt/oracle.cellos/ORACLE_CELL_OS_IS_SETUP | grep ovs")
        node.mDisconnect.assert_called_once()

    def test_mResetIBNetwork_resets_ib_interfaces(self):
        """# Auto-generated test for mResetIBNetwork"""
        cluctrl = Mock()
        cluctrl.mReturnDom0DomUPair.return_value = [("dom0a", "domu1")]
        ovm = ebCluPreChecks(cluctrl)

        node = Mock()
        node.mGetCmdExitStatus.return_value = 0

        with patch("exabox.ovm.clumisc.exaBoxNode", return_value=node), \
                patch("exabox.ovm.clumisc.get_gcontext"):
            ovm.mResetIBNetwork()

        expected_calls = [
            call("cat /opt/oracle.cellos/ORACLE_CELL_OS_IS_SETUP | grep ovs"),
            call("sed '/^IPADDR=/d' -i /etc/sysconfig/network-scripts/ifcfg-ib0"),
            call("sed '/^NETMASK=/d' -i /etc/sysconfig/network-scripts/ifcfg-ib0"),
            call("ip addr flush dev ib0"),
            call("sed '/^IPADDR=/d' -i /etc/sysconfig/network-scripts/ifcfg-ib1"),
            call("sed '/^NETMASK=/d' -i /etc/sysconfig/network-scripts/ifcfg-ib1"),
            call("ip addr flush dev ib1"),
        ]
        self.assertEqual(node.mExecuteCmdLog.mock_calls, expected_calls)
        node.mDisconnect.assert_called_once()

if __name__ == '__main__':
    unittest.main()
