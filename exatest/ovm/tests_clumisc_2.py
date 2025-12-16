import json
import unittest
import re
import copy
import os
import io
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo, ebLogError
from exabox.ovm.clumisc import ebCluPreChecks,ebCluSshSetup,OracleVersion,ebCluStorageReshapePrecheck,ebCluStartStopHostFromIlom, ebCluNodeSubsetPrecheck, ebCluRestartVmExacsService, ebCluFaultInjection, ebMigrateUsersUtil, mGetGridListSupportedByOeda, ebCluCellSanityTests
from exabox.ovm.monitor import ebClusterNode
import warnings
from unittest.mock import patch, Mock, mock_open
from exabox.core.Error import ExacloudRuntimeError
from exabox.utils.node import  connect_to_host
from exabox.ovm.adbs_elastic_service import mCreateADBSSiteGroupConfig
from exabox.ovm.clumisc import mWaitForSystemBoot, ebMiscFx, mGetAlertHistoryOptions, ebADBSUtil
from exabox.ovm.kvmvmmgr import ebKvmVmMgr
from exabox.agent.ebJobRequest import ebJobRequest


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
        patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetRequestObj', return_value=ebJobRequest("cmd_type", {})):
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
        try:
            with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'), \
                    patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
                self.assertEqual(_ebox_local.mHandlerStopStartHostViaIlom(), None)
        except Exception as e:
            ebLogError(f"Exception caught: {str(e)} ")

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
                patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
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
            with connect_to_host(_cell, get_gcontext()) as _node:
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
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e LIST GRIDDISK ATTRIBUTES NAME;", aRc=0, aPersist=True, aStdout="testGrid\n")
                ],
                [
                    exaMockCommand("cellcli -e LIST GRIDDISK ATTRIBUTES NAME;", aRc=0, aPersist=True, aStdout="testGrid\n")
                ],
                [
                    exaMockCommand("cellcli -e LIST GRIDDISK ATTRIBUTES NAME;", aRc=0, aPersist=True, aStdout="testGrid\n")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ebox.mSetCmd('createservice')
        _dom0s, _, _, _ = _ebox.mReturnAllClusterHosts()
        _prechecks = ebCluPreChecks(_ebox)
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

if __name__ == "__main__":
    unittest.main()
