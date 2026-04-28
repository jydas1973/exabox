#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_clucontrol.py /main/73 2026/02/20 01:32:33 avimonda Exp $
#
# tests_clucontrol.py
#
# Copyright (c) 2022, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_clucontrol.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      04/26/26 - Fix unit tests for 39255849
#    aararora    04/14/26 - 39200237: ISSUES OBSERVED FOR EXACLOUD IN SRE
#                           TESTING FOR CHANGES FOR CA SIGNED CERTS IN EXACC
#    bhpati      04/09/26 - Bug 39083181 - CREATEVM UNDO TRIES TO DELETE WRONG
#                           BRIDGE VMETH200
#    aypaul      03/30/26 - Adding unit tests for aypaul_bug-38277507
#    avimonda    03/12/26 - Add tests for OEDA log handling
#    avimonda    03/07/26 - Adding tests for fix related to Bug 38951559 - GCP:
#                           WF WAS STUCK DUE TO NFT RULES MISMATCHES ON DIFFERENT NODES
#    pbellary    03/04/26 - Bug 39037277 - CLUSTER XMLS GET BONDETH4 SET FOR BACKUP NETWORK CONFIGURATION INSTEAD OF BONDETH1
#    avimonda    02/12/26 - Bug 38904960 - OCI: EXADB-D DOMU OS PATCH PRECHECK
#                           FAILED WITH ECRA ERROR WHEN ADMIN CAVIUM IS DOWN
#    aypaul      01/29/26 - Updating unit tests for selinux code refactor 
#    avimonda    12/18/25 - Bug 38740007 - OCI: EXADB-XS OS PATCH PRECHECK
#                           FAILED WITH ECRA ERROR MESSAGE
#    pbellary    12/09/25 - Bug 38740441 - EXACLOUD: ADD COMPUTE WF DID NOT ENABLE QINQ IN ELASTIC NODE 
#    prsshukl    12/02/25 - Bug 38711578 - [EXACC EXACLOUD]: REMOVE
#                           ENABLE_CA_SIGNED_CERTS FLAG FROM EXABOX.CONF
#    prsshukl    11/28/25 - Bug 38394526 - [EXACC EXACLOUD]: SUPPORT PER DOMU
#                           DOMUCLIENT CERTIFICATE DURING CREATE SERVICE, ADD
#                           NODE
#    avimonda    11/26/25 - Bug 38632230 - GCP: EXACS: PROVISIONING FAILED WITH
#                           FILENOTFOUNDERROR: [ERRNO 2] NO SUCH FILE OR
#                           DIRECTORY:
#                           'CLUSTERS/KQQ100319EXDDU1101KQQ100319EXDDU1201'
#    ririgoye    11/26/25 - Enh 38344608 - WRITE A UNIT TEST TO CATCH THE PKEYS
#                           ISSUE
#    pbellary    11/12/25 - Bug 38635045: EXASCALE CLUSTERS DON'T HAVE GET_CS_DATA.PY FILE IN DOMUS
#    aararora    10/31/25 - Bug 38595677: Fix unit test failure
#    jfsaldan    09/02/25 - Bug 38244250 - EXACS: PROVISIONING FAILED WITH
#                           EXACLOUD ERROR CODE: 1859 EXACLOUD : CELL
#                           CONSISTENCY/SEMANTIC CHECKFAILED. | CELL
#                           CONSISTENCY CHECK SHOULD NOT RAISE AN EXCEPTION IN
#                           CREATE SERVICE
#    avimonda    08/07/25 - Bug 38184216 - OCI: EXACS | SCALE MEMORY STRUCK AT
#                           AWT_TMP_SSH_KEY_ASYN STEP
#    bhpati      03/10/25 - Bug 37653016 - MEMORY SCALE UP STUCK
#    naps        02/25/25 - Bug 37556553 - UT for 37556553 .
#    jfsaldan    02/18/25 - 37570873 - EXADB-D|XS -- EXACLOUD | PROVISIONING |
#                           REVIEW AND ORGANIZE PREVM_CHECKS AND PREVM_SETUP
#                           STEPS
#    gparada     02/10/25 - UT mUpdateCelldiskSize, cellcli out more than 1 line
#    remamid     11/26/24 - test case for bug fix 37240150
#    remamid     11/18/24 - Bug 37292498 unittest fixes
#    remamid     10/04/24 - Add testcase for sysctl -p timeout bug 36986469
#    aararora    09/10/24 - Bug 37041670: Provide list of serial numbers for
#                           secure erase
#    naps        08/14/24 - Bug 36949876 - X11 ipconf path changes.
#    naps        08/12/24 - Bug 36908342 - X11 support.
#    prsshukl    07/24/24 - Resolve unittest failure
#    aypaul      07/15/24 - Add unit tests for 36790953
#    jesandov    10/16/23 - 35729701: Support of OL7 + OL8
#    pbellary    05/22/23 - 35410491 - EXACC GEN2: U01 RESHAPE OPERATIONS FAILS 
#                           DUE TO SSH KEY AUTHENTICATION ISSUE AFTER INSERTING ROOT TMP SSH KEY
#    aararora    05/05/23 - Add UT for mHandlerGetDom0ExistingGuestsSize.
#    talagusu    04/17/23 - Bug 35173116 oratab entry missed for ASM instance
#    gparada     04/04/23 - 35182276 Add ut's for mGetIlomPass and related
#    gparada     03/15/23 - 35171045 Update BaseSystem Id for X10M model
#    aypaul      11/15/22 - Bug#34697937 Adding unit test cases for
#                           mSetEnvTypeInConfiguration
#    jfsaldan    11/02/22 - Bug 34748225 - EXACLOUD - IAD - NOT CORRECTLY
#                           CHECKING INTERFACES IN NON BONDED IAD NODES
#    naps        10/11/22 - Bug 34563765 - add UT for mAddOratabEntry.
#    naps        07/31/22 - Bug 34410322 - UT for checking disksize in cells.
#    aypaul      03/22/22 - Creation
#
import datetime
import json
import unittest
import warnings
import copy
import os, re, shutil
import sys
from io import StringIO
from unittest import mock
from exabox.infrapatching.core.infrapatcherror import PATCHING_NODE_SSH_CHECK_FAILED, PATCHING_CONNECT_FAILED
from unittest.mock import patch, MagicMock, PropertyMock, mock_open, Mock, call
from paramiko.ssh_exception import SSHException
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.core.DBStore import ebGetDefaultDB
from exabox.log.LogMgr import ebLogInfo, ebLogError
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.network.Connection import exaBoxConnection
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.ovm.clucommandhandler import CommandHandler
from exabox.ovm.clunetworkdetect import ebDiscoverOEDANetwork
from exabox.utils.node import connect_to_host
from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType

customOutput1 = """<sysinfo type='smbios'><chassis><entry name='manufacturer'>Oracle Corporation</entry><entry name='version'>ORACLE SERVER X7-2</entry><entry name='serial'>1801XC303J</entry><entry name='asset'>7338405</entry></chassis></sysinfo>"""
customOutput2 = """    inet 10.0.7.144/25 brd 10.0.7.255 scope global vmeth0"""
customOutput3 = """+ : root : console tty1 ttyS0 hvc0 localhost ip6-localhost 10.0.1.4/255.255.255.255"""
customOutput4 = """+ : secscan : console tty1 ttyS0 hvc0 localhost ip6-localhost 10.0.1.4/255.255.255.255"""
customOutput5 = """+ : cellmonitor : console tty1 ttyS0 hvc0 localhost ip6-localhost 10.0.1.4/255.255.255.255"""
customOutput6 = """NETMASK=255.255.255.128
NETWORK=10.0.7.128"""
customOutput7 = """Server:         100.70.127.250
Address:        100.70.127.250#53

** server can't find phoenix262086: NXDOMAIN"""

MOCK_ERROR_JSON="""
{
   "exceptions":[
      {
         "errorCode":"1001",
         "errorMsg":": Exception message: Errors occurred...",
         "cause":"Unspecified error",
         "action":"Send the below Diag.zip file to Oracle for assistance.",
         "timeStamp":"09-09-2022 21:43:58 UTC"
      }
   ]
}
"""

MOCK_SKIP_ERROR_JSON="""
{
   "exceptions":[
      {
         "errorCode":"1002",
         "errorMsg":": KommandException error Command return code: 1. Host: scas22celadm06.us.oracle.com User: root Command: /opt/oracle.SupportTools/exadataAIDE -u KommandException message: Command output: AIDE: database update request accepted.",
         "cause":"KommandException error",
         "action":"Send the following diagnostic output file to Oracle for assistance.",
         "timeStamp":"09-09-2022 21:43:58 UTC"
      }
   ]
}
"""

MOCK_SELINUX_PAYLOAD={
    "se_linux":
    {
        "infraComponent":
        [
            {
                "mode": "enforcing",
                "component": "dom0",
                "targetComponentName":
                [
                    "iad103709exdd012.iad103709exd.adminiad1.oraclevcn.com",
                    "iad103709exdd011.iad103709exd.adminiad1.oraclevcn.com"
                ]
            }
        ],
        "dom0_policy": ["/tmp/mock_policy_file_name"]
    }
}

MOCK_CRONJOB_CONF={
    "rpm_watch" : {
        "local_file" : "images/rpmwatch-latest.noarch.rpm",
        "remote_file": "/tmp/rpmwatch-latest.noarch.rpm",
        "min_period" : 2,
        "host_types" : ["dom0", "cell"],
        "install_cmd": "rpm -Uvh /tmp/rpmwatch-latest.noarch.rpm",
        "exec_cmd"   : "/opt/rpmwatch/bin/rpmwatch"
    },
    "firmware_watch" : {
        "local_file" : "scripts/fedramp/fwwatch",
        "remote_file": "/opt/rpmwatch/bin/fwwatch",
        "min_period" : 2,
        "host_types" : ["domu", "cell"],
        "install_cmd": "chmod 740 /opt/rpmwatch/bin/fwwatch",
        "exec_cmd"   : "/opt/rpmwatch/bin/fwwatch"
    },
    "diskdrop_watch" : {
        "local_file" : "scripts/fedramp/ddwatch",
        "remote_file": "/opt/rpmwatch/bin/ddwatch",
        "min_period" : 30,
        "host_types" : ["switch"],
        "install_cmd": "chmod 740 /opt/rpmwatch/bin/ddwatch",
        "exec_cmd"   : "/opt/rpmwatch/bin/ddwatch"
    }
}

ENABLE_QINQ_PAYLOAD = """ 
{
    "Overall Status: ": "True",
    "exa_ocid": "ocid1.exadatainfrastructure.region1.sea.anzwkljsjajnm5iada6x2mbtvrnfywyzvif6ocrz6orfw64kl6zgkbq7vvna",
    "exascale": {
        "cell_list": [
            "scaqau11celadm01.oracle.local",
            "scaqau11celadm02.oracle.local",
            "scaqau11celadm03.oracle.local"
        ],
        "ctrl_network": {
            "ip": "10.106.65.163",
            "name": "scaqau11ers01.oracle.local",
            "port": "5052"
        },
        "db_vault": {
            "gb_size": 4096,
            "name": "xsvlt-65841-02"
        },
        "exascale_cluster_name": "sea119487exddbaasscaqau11XXXclu01ers",
        "host_nodes": [
            {
                "compute_hostname": "scaqau11adm01.oracle.local",
                "interface1": "stre0",
                "interface2": "stre1",
                "netmask": "255.255.240.0",
                "priv1": "scaqau11adm01-priv1",
                "priv2": "scaqau11adm01-priv2",
                "storage_ip1": "192.168.64.1",
                "storage_ip2": "192.168.64.2"
            },
            {
                "compute_hostname": "scaqau11adm02.oracle.local",
                "interface1": "stre0",
                "interface2": "stre1",
                "netmask": "255.255.240.0",
                "priv1": "scaqau11adm02-priv1",
                "priv2": "scaqau11adm02-priv2",
                "storage_ip1": "192.168.64.3",
                "storage_ip2": "192.168.64.4"
            },
            {
                "compute_hostname": "scaqau11adm03.oracle.local",
                "interface1": "stre0",
                "interface2": "stre1",
                "netmask": "255.255.240.0",
                "priv1": "scaqau11adm03-priv1",
                "priv2": "scaqau11adm03-priv2",
                "storage_ip1": "192.168.64.79",
                "storage_ip2": "192.168.64.80"
            }
        ],
        "storage_pool": {
            "gb_size": "51189",
            "name": "hcpool"
        },
        "storage_vlan_id": "2900"
    },
    "newComputes": [
        "scaqau11adm03"
    ],
    "node_type": "compute",
    "operation": "activate-new-computes",
    "requestId": "b71273bd-a223-481a-b6e7-d4851154cf68",
    "validationResponse": [
        {
            "TotOnlineMem": "1.5T",
            "model": "X10M-2",
            "nodeStatus": "PASS",
            "node_name": "scaqau11adm03",
            "server": "scaqau11adm03",
            "testsFailed": [],
            "testsPassed": []
        }
    ]
}
"""

ROOT_SHADOW_OP="""root:$6$/PVVK/D..$KQum5zORV7GGf.kVSVYR/sloEelpxjbhi.5Qy.4Fakk6cobknadnszAsxcVaiJesz/yBNm4KHyL0ZuzpvTte1/:19075:1:60:7:::"""
SMPARTITION_OP="Default=0x7fff, ipoib : ALL_CAS=full, ALL_SWITCHES=full, SELF=full;"
TOP_CMD_OP="""%Cpu39 :  0.0 us,  0.0 sy,  0.0 ni,100.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
%Cpu40 :  0.0 us,  0.0 sy,  0.0 ni,100.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
%Cpu41 :  0.0 us,  0.0 sy,  0.0 ni,100.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
%Cpu42 :  9.5 us, 19.0 sy,  0.0 ni, 71.4 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
%Cpu43 :  0.0 us,  0.0 sy,  0.0 ni,100.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
%Cpu44 :  0.0 us,  0.0 sy,  0.0 ni,100.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
%Cpu45 :  0.0 us,  0.0 sy,  0.0 ni,100.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
%Cpu46 :  0.0 us,  0.0 sy,  0.0 ni,100.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
%Cpu47 :  0.0 us,  0.0 sy,  0.0 ni,100.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
KiB Mem : 74259481+total, 73247347+free,  5059352 used,  5061996 buff/cache
KiB Swap: 16777212 total, 16777212 free,        0 used. 72758220+avail Mem"""

XM_INFO_CMD_OP="""host                   : sea200214exdd003.sea200214exd.adminsea2.oraclevcn.com
release                : 4.1.12-124.42.4.el6uek.x86_64
machine                : x86_64
nr_cpus                : 96
nr_nodes               : 2
cores_per_socket       : 24
threads_per_core       : 2
total_memory           : 785069
free_memory            : 22336"""

XENTOP_CMD_OP="""      NAME  STATE   CPU(sec) CPU(%)     MEM(k) MEM(%)  MAXMEM(k) MAXMEM(%) VCPUS NETS NETTX(k) NETRX(k) VBDS   VBD_OO   VBD_RD   VBD_WR  VBD_RSECT  VBD_WSECT SSID
c2214-vkge -----r       2084    0.0  754978808   93.9  754978816      93.9    92    3     4249    52707    4        0    84460    75132    4754377    8759386    0
  Domain-0 -----r     393575    0.0    9357356    1.2    9437184       1.2     4    0        0        0    0        0        0        0          0          0    0"""

HAC_SUCCESS_PROV_PAYLOAD = {
"ecra": {
    "whitelist_cidr": [
      "10.0.1.0/32",
      "10.0.2.0/28"
    ]
  }
}

HAC_FAILURE_PROV_PAYLOAD = {
"ecra": {
    "whitelist_cidr": [
      "10.0.1.0",
      "10.0.2.0"
    ]
  }
}

DB_INSTALL = """
{
    "atp": {
        "AutonomousDb": "N"
    },
    "clusterId": "cluster_exaunit_262",
    "concurrent_operation": "true",
    "dbParams": {
        "archlog": "yes",
        "asm": "false",
        "automem": "yes",
        "bkup_cfg_files": "no",
        "bkup_cfg_recovery_window": "7",
        "bkup_cron_entry": "yes",
        "bkup_daily_time": "01:01",
        "bkup_disk": "no",
        "bkup_disk_recovery_window": "7",
        "bkup_nfs": "no",
        "bkup_nfs_recovery_window": "30",
        "bkup_oss": "no",
        "bkup_oss_recovery_window": "30",
        "bkup_use_rcat": "no",
        "bkup_zdlra": "no",
        "bkup_zdlra_passwd": "",
        "bkup_zdlra_url": "",
        "bkup_zdlra_user": "",
        "bp": "default",
        "bp_update": "no",
        "bp_url": "",
        "bundle": "extreme-perf",
        "byol": "no",
        "cdb": "yes",
        "charset": "AL32UTF8",
        "db_unique_name": "dbu269",
        "dbca_vars": "-characterSet AL32UTF8 -initParams filesystemio_options=setall,db_files=250",
        "dbkey": "",
        "dbmac": "exa",
        "dbname": "db269",
        "dborch_version": "19.280",
        "dbtemplate": "oltp",
        "dbtype": "exarac",
        "demo": "no",
        "demo_uri": "https://storage.us2.oraclecloud.com/v1/dbcsswlibp-usoracle29538/pdb_demo/demo.pl",
        "demo_user": "oracle",
        "dg_config": "no",
        "dg_connect_aliases": "",
        "dg_observer": "no",
        "dg_observer_exists": "no",
        "dg_observer_user": "oracle",
        "dg_observer_zone": "primary",
        "dg_scan_ips": "",
        "dg_uniq_names": "",
        "dg_vm_names": "",
        "dv": "no",
        "edition": "enterprise",
        "em": "yes",
        "exacm": "no",
        "flashback": "yes",
        "flashback_days": "1",
        "flashback_minutes": "120",
        "gfish": "no",
        "gg": "no",
        "hdg": "no",
        "init_params": "",
        "libopc_mode": "prod",
        "lvm": "yes",
        "managed": "no",
        "managed_uri": "https://storage.us2.oraclecloud.com/v1/dbaastest-usoracle05695/dbaas_managed/dbaasm/configure_dbaasm.pl",
        "managed_user": "root",
        "ncharset": "AL16UTF16",
        "net_security_enable": "yes",
        "net_security_encryption_enable": "yes",
        "net_security_encryption_methods": "AES256,AES192,AES128",
        "net_security_encryption_target": "server",
        "net_security_encryption_type": "required",
        "net_security_integrity_checksum_level": "required",
        "net_security_integrity_enable": "yes",
        "net_security_integrity_methods": "SHA1",
        "net_security_integrity_target": "server",
        "nodelist": "",
        "ohome_name": "",
        "ohome_owner_group": "dba",
        "ords_config": "no",
        "ore": "no",
        "passwd": "Fl5-Og9-93Ry1va",
        "pdb_name": "pdb1",
        "pdbss": "no",
        "psu": "default",
        "psu_url": "",
        "redo_log_size": "1024M",
        "service": "ecs",
        "setup_rcat": "no",
        "shared_oh_dbname": "",
        "sid": "db269",
        "sm": "yes",
        "tde_action": "config",
        "tde_ks_login": "auto",
        "tde_ks_passwd": "Fl5-Og9-93Ry1va",
        "timezone": "UTC",
        "tmpl_blksz": "8K",
        "tmpl_dbrecoverydestsize": "",
        "tmpl_logsz": "1000MB",
        "tmpl_sysauxsz": "2000MB",
        "tmpl_systemsz": "2000MB",
        "tmpl_tempsz": "1000MB",
        "upgrade_apex": "no",
        "useInternalIP": "no",
        "version": "23000"
    },
    "ecraExaunitID": "262",
    "exaunitID": "ec86e02c-9e71-4cc3-8438-33ccd42a55d6",
    "grid_version": "23",
    "rack": {
        "create_sparse": "false"
    },
    "sshkey": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC8WZS2pacvtMtqY+ZUCriOZ/xpOUnBO3J+yAPRW7XvFUaTa/SDU2lFN8lDe7ZiUL2akbxUc4XPqLZF5pWvkVjpoQOsnlocggp2hB0LvsYF6nrwn81vAe/KXLVG+8bNBhzBY/M8rnl6zy/gVR9EEfP89NsOfBsOSt7ZRy+KqGbK5M7sAGL82oGVryDKnHr51sxuTkWVG2wkKHBtf8z9VknoagqnJ/20lqBV2iBSCEywT3fqBCtDylA8hI5hWW6GBfRzwoLhHDHKTnjhGijRO2dOn14885gdco6wOB6gXkkHbj2xctxr7AbWoKF4tJKjZGhxS/N1rKBA/6rPwqFJ0vc+LtuvIpIWDgwvJh+7R/Hqdc58K3EwNBXmnitdTUqFPMeOhabOge0gg7lhhhJc81pyC/7E4fEOEoT101Y57sSDz2gLHPEyq6UiKDp56tcLdtUQbuW4f1Meg+0xgSmIB+i3O7RpVjJfzcpjyPgFNBwMvMTVk6AW70P750ThyQEj3IE= ControlPlane",
    "tenantID": "tenant_exaunit_262"
}
"""

OSTP_PREVM_INSTALL  = 128

class mockStream():

    def __init__(self, aStreamContents=["None"]):
        self.stream_content = aStreamContents

    def readlines(self):
        return self.stream_content

    def readline(self):
        return self.stream_content[0]

    def read(self):
        return self.stream_content[0]

class mockHVInstance():

    def __init__(self):
        self.__running_domus = list()

    def mSetRunningDomUs(self, aListOfRunningDomUs):
        self.__running_domus = copy.deepcopy(aListOfRunningDomUs)

    def mRefreshDomUs(self):
        return self.__running_domus

class testOptions(object): pass

class ebTestClucontrolClasses(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestClucontrolClasses, self).setUpClass(aGenerateDatabase=True, aEnableUTFlag=False, aUseOeda = True)
        self.mGetClubox(self).mSetUt(True)
        warnings.filterwarnings("ignore")
        self._db = ebGetDefaultDB()

    def _mock_check_config_option(self, return_value="true"):
        return patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption", return_value=return_value)

    def _mock_update_error(self):
        return patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateErrorObject")

    @patch("exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mCheckVaultTag", return_value=False)
    def test_mParseXMLForXS_raises_when_vault_missing(self, mock_check_vault):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        with self._mock_check_config_option("true") as mock_config, self._mock_update_error() as mock_update_error:
            with self.assertRaises(ExacloudRuntimeError) as ctx:
                _ebox_local.mGetExascaleUtils().mParseXMLForXS()

        mock_config.assert_called_once_with('enable_xs_service')
        mock_check_vault.assert_called_once()
        mock_update_error.assert_called_once()
        self.assertIn("vault tag is missing", str(ctx.exception))

    @patch("exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mCheckVaultTag", return_value=True)
    def test_mParseXMLForXS_no_error_when_vault_present(self, mock_check_vault):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local.mSetXS(False)

        with self._mock_check_config_option("true") as mock_config, self._mock_update_error() as mock_update_error:
            _ebox_local.mGetExascaleUtils().mParseXMLForXS()

        mock_config.assert_called_once_with('enable_xs_service')
        mock_check_vault.assert_called_once()
        mock_update_error.assert_not_called()
        self.assertFalse(_ebox_local.mGetXS())

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mEnvTarget", return_value=True)
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteLocal", return_value=(None, None, customOutput7, None))
    def test_mSecureDom0SSH(self, aEnabledProdTargetMock, aMExecuteLocalObj):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mSecureDom0SSH")
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local.mGetLocalNode().mSetMockMode(False)

        _ddpair_list = [("dom0-1.us.oracle.com", "dom0-1-vm.us.oracle.com")]
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf['ecra'] = HAC_FAILURE_PROV_PAYLOAD['ecra']
        _ebox_local.mSetOptions(_options)
        self.assertRaises(ExacloudRuntimeError, _ebox_local.mSecureDom0SSH, _ddpair_list)

        outputAddrShowSet = (None, mockStream([customOutput2]), None)
        outputIpCalcSet = (None, mockStream([customOutput6]), None)
        outputRulesGrepRootSet = (None, mockStream([customOutput3]), None)
        outputRulesGrepSecscanSet = (None, mockStream([customOutput4]), None)

        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetCurrentMasterInterface", return_value="mockmasterinformation"),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmd', side_effect=iter([outputAddrShowSet, outputIpCalcSet, outputRulesGrepRootSet, outputRulesGrepSecscanSet, outputRulesGrepRootSet, outputRulesGrepSecscanSet])),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mOpenSSHFromECRA", return_value=list()),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption", return_value=None),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
            patch('exabox.utils.node.exaBoxNode.mGetHostname', return_value="mocknode"),\
            patch('exabox.utils.node.exaBoxNode.mCopyFile'),\
            patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0):
            _options.jsonconf['ecra'] = HAC_SUCCESS_PROV_PAYLOAD['ecra']
            _ebox_local.mSetOptions(_options)
            _ebox_local.mSecureDom0SSH(_ddpair_list)
        
        ebLogInfo("Unit test on exaBoxCluCtrl.mSecureDom0SSH succeeded.")

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mEnvTarget", return_value=True)
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteLocal", return_value=(None, None, customOutput7, None))
    def test_mSecureCellsSSH(self, aEnabledProdTargetMock, aMExecuteLocalObj):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mSecureCellsSSH")
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local.mGetLocalNode().mSetMockMode(False)

        _cellnode_information = {"cellnode-1.us.oracle.com": "mock cell data"}
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf['ecra'] = HAC_FAILURE_PROV_PAYLOAD['ecra']
        _ebox_local.mSetOptions(_options)
        self.assertRaises(ExacloudRuntimeError, _ebox_local.mSecureCellsSSH, _cellnode_information)

        outputAddrShowSet = (None, mockStream([customOutput2]), None)
        outputIpCalcSet = (None, mockStream([customOutput6]), None)
        outputRulesGrepRootSet = (None, mockStream([customOutput3]), None)
        outputRulesGrepSecscanSet = (None, mockStream([customOutput4]), None)
        outputRulesGrepCellmonitorSet = (None, mockStream([customOutput5]), None)

        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetCurrentMasterInterface", return_value="mockmasterinformation"),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmd', side_effect=iter([outputAddrShowSet, outputIpCalcSet, outputRulesGrepRootSet, outputRulesGrepSecscanSet, outputRulesGrepCellmonitorSet, outputRulesGrepRootSet, outputRulesGrepSecscanSet, outputRulesGrepCellmonitorSet])),\
            patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mOpenSSHFromECRA", return_value=list()),\
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption", return_value=None),\
            patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
            patch('exabox.utils.node.exaBoxNode.mGetHostname', return_value="mocknode"),\
            patch('exabox.utils.node.exaBoxNode.mCopyFile'),\
            patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0):
            _options.jsonconf['ecra'] = HAC_SUCCESS_PROV_PAYLOAD['ecra']
            _ebox_local.mSetOptions(_options)
            _ebox_local.mSecureCellsSSH(_cellnode_information)
        
        ebLogInfo("Unit test on exaBoxCluCtrl.mSecureCellsSSH succeeded.")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsXS', return_value=False)
    def test_mExecuteProfileClusterCheck(self, mock_mIsXS):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mSecureCellsSSH")

        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local.mExecuteProfileClusterCheck()
        with patch('os.path.exists', return_value=False),\
             patch('os.path.join', return_value="/dir1/dir2/mockprofile.prf"):
            _ebox_local.mExecuteProfileClusterCheck("mockprofile.prf")

        with patch('os.path.exists', return_value=True),\
             patch('builtins.open', mock_open(read_data=json.dumps({"key1": "value1"}))),\
             patch('exabox.ovm.clucontrol.ebCluHealthCheck.mDoHealthCheck'),\
             patch('os.path.join', return_value="/dir1/dir2/mockprofile.prf"):
            _ebox_local.mExecuteProfileClusterCheck("mockprofile.prf")
        ebLogInfo("Unit test on exaBoxCluCtrl.mExecuteProfileClusterCheck succeeded.")

    @patch("exabox.ovm.clucontrol.clubonding.is_bonding_supported_dom0")
    def test_mIssueSoftWarningOnLinkfailure(self, aMagicIsBondingEnabled):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mIssueSoftWarningOnLinkfailure")

        _ebox_local = copy.deepcopy(self.mGetClubox())

        # Mock as if bonding is NOT supported
        aMagicIsBondingEnabled.return_value = False
        self.assertEqual(_ebox_local.mIssueSoftWarningOnLinkfailure("iad103714exdd005.iad103714exd.adminiad1.oraclevcn.com", "eth1"), False)
        self.assertEqual(_ebox_local.mIssueSoftWarningOnLinkfailure("iad103714exdd004.iad103714exd.adminiad1.oraclevcn.com", "eth0"), False)
        self.assertEqual(_ebox_local.mIssueSoftWarningOnLinkfailure("iad103714exdd004.iad103714exd.adminiad1.oraclevcn.com", "eth1"), True)

        # Mock as if bonding IS supported
        aMagicIsBondingEnabled.return_value = True
        self.assertEqual(_ebox_local.mIssueSoftWarningOnLinkfailure("iad103714exdd004.iad103714exd.adminiad1.oraclevcn.com", "eth1"), False)
        self.assertEqual(_ebox_local.mIssueSoftWarningOnLinkfailure("iad103714exdd005.iad103714exd.adminiad1.oraclevcn.com", "eth1"), False)
        ebLogInfo("Unit test on exaBoxCluCtrl.mIssueSoftWarningOnLinkfailure succeeded.")

    def test_mClusterCheckInfo(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mClusterCheckInfo")

        _ebox_local = copy.deepcopy(self.mGetClubox())
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["default_pwd"] = "V2VsY29tZUAxMjM="
        gContext.mSetConfigOptions(writableGConfigOptions)
        with patch('exabox.core.DBStore3.ebExacloudDB.mCheckTableExist', return_value=True),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateClusterStatusTable'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', return_value=False),\
             patch('exabox.ovm.clucontrol.ebClusterNode.mGetPingable', return_value=True),\
             patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
             patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=True),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(None, mockStream([ROOT_SHADOW_OP]), None)),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteLocal'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetClusterStatus', return_value=False),\
             patch('exabox.core.DBStore3.ebExacloudDB.mInsertNewClusterStatus', return_value=False):
             _ebox_local.mClusterCheckInfo()

        with patch('exabox.core.DBStore3.ebExacloudDB.mCheckTableExist', return_value=True),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateClusterStatusTable'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=False),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', return_value=False),\
             patch('exabox.ovm.clucontrol.ebClusterNode.mGetPingable', return_value=True),\
             patch('exabox.ovm.clucontrol.ebClusterNode.mSetSwitchDefault', return_value=True),\
             patch('exabox.ovm.clucontrol.ebClusterNode.mSetSwitchAllCas', return_value=True),\
             patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
             patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=True),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(None, mockStream([SMPARTITION_OP]), None)),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteLocal'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetClusterStatus', return_value=False),\
             patch('exabox.core.DBStore3.ebExacloudDB.mInsertNewClusterStatus', return_value=False):
             _ebox_local.mClusterCheckInfo()


        _cmds = {
                    self.mGetRegexDom0(): [
                        [
                            exaMockCommand("top -n 1 -b", aStdout=TOP_CMD_OP, aRc=0, aPersist=True),
                            exaMockCommand("xm info", aStdout=XM_INFO_CMD_OP, aRc=0, aPersist=True),
                            exaMockCommand("xentop -b -i 1", aStdout=XENTOP_CMD_OP, aRc=0, aPersist=True),
                            exaMockCommand("grep", aStdout=ROOT_SHADOW_OP, aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexSwitch(): [
                        [
                            exaMockCommand("top -n 1 -b", aStdout=TOP_CMD_OP, aRc=0, aPersist=True),
                            exaMockCommand("grep", aStdout=ROOT_SHADOW_OP, aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexCell(): [
                        [
                            exaMockCommand("top -n 1 -b", aStdout=TOP_CMD_OP, aRc=0, aPersist=True),
                            exaMockCommand("grep", aStdout=ROOT_SHADOW_OP, aRc=0, aPersist=True)
                        ]
                    ],
                    self.mGetRegexVm(): [
                        [
                            exaMockCommand("top -n 1 -b", aStdout=TOP_CMD_OP, aRc=0, aPersist=True),
                            exaMockCommand("grep", aStdout=ROOT_SHADOW_OP, aRc=0, aPersist=True)
                        ]
                    ]
                }
        self.mPrepareMockCommands(_cmds)
        with patch('exabox.core.DBStore3.ebExacloudDB.mCheckTableExist', return_value=True),\
             patch('exabox.core.DBStore3.ebExacloudDB.mCreateClusterStatusTable'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost', return_value=False),\
             patch('exabox.ovm.clucontrol.ebClusterNode.mGetPingable', return_value=True),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
             patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=True),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteLocal'),\
             patch('exabox.core.DBStore3.ebExacloudDB.mGetClusterStatus', return_value=False),\
             patch('exabox.core.DBStore3.ebExacloudDB.mInsertNewClusterStatus', return_value=False):
             _ebox_local.mClusterCheckInfo(aMonitor=True)

        gContext.mSetConfigOptions(gConfigOptions)
        ebLogInfo("Unit test on exaBoxCluCtrl.mClusterCheckInfo succeeded.")

    def test_mHandlerGetCellIBInfo(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mGetCommandHandler().mHandlerGetCellIBInfo")

        _ebox_local = copy.deepcopy(self.mGetClubox())
        with patch('exabox.core.DBStore3.ebExacloudDB.mUpdateRequest'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True):
             _ebox_local.mGetCommandHandler().mHandlerGetCellIBInfo()

        with patch('exabox.core.DBStore3.ebExacloudDB.mUpdateRequest'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetPkeysConfig', return_value=("mock_spk", "mock_cpk")),\
             patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(None, mockStream(["mock_pname=some_value"]), None)),\
             patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=False):
             _ebox_local.mGetCommandHandler().mHandlerGetCellIBInfo()

        _ebox_local.mSetRequestObj(ebJobRequest("mock_cmd_type", {}))
        with patch('exabox.core.DBStore3.ebExacloudDB.mUpdateRequest'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetPkeysConfig', return_value=("mock_spk", "mock_cpk")),\
             patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(None, mockStream(["mock_pname=some_value"]), None)),\
             patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=False):
             _ebox_local.mGetCommandHandler().mHandlerGetCellIBInfo()
             _data_json = json.loads(_ebox_local.mGetRequestObj().mGetData())
             self.assertEqual(_data_json["pkey"], "mock_spk")
             self.assertEqual(_data_json["pname"], "mock_pname")
        ebLogInfo("Unit test on exaBoxCluCtrl.mGetCommandHandler().mHandlerGetCellIBInfo succeeded.")

    def test_mCheckDBNameOnCells(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mCheckDBNameOnCells")

        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local._exaBoxCluCtrl__dbname = "mockdb"

        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmdCellcli', return_value=(None, mockStream(["MOCKDB"]), None)),\
             patch('exabox.utils.node.exaBoxNode.mDisconnect'):
             self.assertRaises(ExacloudRuntimeError, _ebox_local.mCheckDBNameOnCells)

        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmdCellcli', return_value=(None, mockStream(["NOTAMOCKDB"]), None)),\
             patch('exabox.utils.node.exaBoxNode.mDisconnect'):
             _ebox_local.mCheckDBNameOnCells()
        ebLogInfo("Unit test on exaBoxCluCtrl.mCheckDBNameOnCells succeeded.")

    def mCreateMockRequest(self, data_value='Undef'):
        class _Req:
            def __init__(self, data):
                self._data = data

            def mGetData(self):
                return self._data

            def mSetData(self, value):
                self._data = value

        return _Req(data_value)

    def mCreateExaBoxCluCtrl(self):

        class _Req:
            def __init__(self):
                self._data = 'Undef'

            def mGetData(self):
                return self._data

            def mSetData(self, value):
                self._data = value

        clu_ctrl = exaBoxCluCtrl(self.mGetClubox())
        clu_ctrl.mSetRequestObj(_Req())
        return clu_ctrl

    @patch('exabox.ovm.clucontrol.ebSelinuxControls')
    @patch('exabox.ovm.clucontrol.ebGetDefaultDB')
    def test_mCompileSelinuxResponse_updates_request_data(self, mock_db, mock_selinux_controls_cls):
        ebLogInfo("Running unit test on exaBoxCluCtrl.mCompileSelinuxResponse when operations exist")

        mock_request = self.mCreateMockRequest()
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance

        mock_selinux_instance = MagicMock()
        mock_selinux_instance.mGetSELinuxStatusForClusterOperations.return_value = [
            {"componentType": "dom0", "hostname": "host-dom0", "modeUpdate": "Success", "selinuxStatus": "enforcing"},
            {"componentType": "cell", "hostname": "host-cell", "modeUpdate": "Failure", "selinuxStatus": "permissive"}
        ]
        mock_selinux_controls_cls.return_value = mock_selinux_instance

        clu_ctrl = self.mCreateExaBoxCluCtrl()
        clu_ctrl.mSetRequestObj(mock_request)

        clu_ctrl.mCompileSelinuxResponse()

        expected_data = {
            "sestatus": [
                {
                    "componentType": "dom0",
                    "nodeStatus": [
                        {
                            "hostname": "host-dom0",
                            "status": {"modeUpdate": "Success", "selinuxStatus": "enforcing"}
                        }
                    ]
                },
                {
                    "componentType": "cell",
                    "nodeStatus": [
                        {
                            "hostname": "host-cell",
                            "status": {"modeUpdate": "Failure", "selinuxStatus": "permissive"}
                        }
                    ]
                }
            ]
        }

        mock_db_instance.mUpdateRequest.assert_called_once()
        updated = json.loads(mock_request.mGetData())
        self.assertEqual(updated["sestatus"], expected_data["sestatus"])

    @patch('exabox.ovm.clucontrol.ebSelinuxControls')
    @patch('exabox.ovm.clucontrol.ebGetDefaultDB')
    def test_mCompileSelinuxResponse_preserves_existing_data(self, mock_db, mock_selinux_controls_cls):
        ebLogInfo("Running unit test on exaBoxCluCtrl.mCompileSelinuxResponse merging existing request data")

        initial_data = json.dumps({"existing": "value"})
        mock_request = self.mCreateMockRequest(initial_data)
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance

        mock_selinux_instance = MagicMock()
        mock_selinux_instance.mGetSELinuxStatusForClusterOperations.return_value = [
            {"componentType": "dom0", "hostname": "host-dom0", "modeUpdate": "Success", "selinuxStatus": "enforcing"}
        ]
        mock_selinux_controls_cls.return_value = mock_selinux_instance

        clu_ctrl = self.mCreateExaBoxCluCtrl()
        clu_ctrl.mSetRequestObj(mock_request)

        clu_ctrl.mCompileSelinuxResponse()

        expected_data = {
            "sestatus": [
                {
                    "componentType": "dom0",
                    "nodeStatus": [
                        {
                            "hostname": "host-dom0",
                            "status": {"modeUpdate": "Success", "selinuxStatus": "enforcing"}
                        }
                    ]
                }
            ]
        }

        mock_db_instance.mUpdateRequest.assert_called_once()
        updated_data = json.loads(mock_request.mGetData())
        self.assertEqual(updated_data["existing"], "value")
        self.assertEqual(updated_data["sestatus"], expected_data["sestatus"])

    @patch('exabox.ovm.clucontrol.ebSelinuxControls')
    @patch('exabox.ovm.clucontrol.ebGetDefaultDB')
    def test_mCompileSelinuxResponse_no_operations(self, mock_db, mock_selinux_controls_cls):
        ebLogInfo("Running unit test on exaBoxCluCtrl.mCompileSelinuxResponse when no operations executed")

        mock_selinux_instance = MagicMock()
        mock_selinux_instance.mGetSELinuxStatusForClusterOperations.return_value = list()
        mock_selinux_controls_cls.return_value = mock_selinux_instance

        mock_request = self.mCreateMockRequest()
        clu_ctrl = self.mCreateExaBoxCluCtrl()
        clu_ctrl.mSetRequestObj(mock_request)
        clu_ctrl.mCompileSelinuxResponse()
        self.assertEqual(mock_request.mGetData(), 'Undef')
        mock_db.assert_not_called()

    def test_mCheckNodeList(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mCheckNodeList")

        _ebox_local = copy.deepcopy(self.mGetClubox())
        self.assertEqual(_ebox_local.mCheckNodeList("scaqab10client01vm08")[0][0], 'scaqab10adm01.us.oracle.com')
        self.assertRaises(ExacloudRuntimeError, _ebox_local.mCheckNodeList, "scaqab10adm01")
        ebLogInfo("Unit test on exaBoxCluCtrl.mCheckNodeList succeeded.")

    def test_mCheckSingleNode(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mCheckSingleNode")

        _ebox_local = copy.deepcopy(self.mGetClubox())
        self.assertEqual(_ebox_local.mCheckSingleNode("")[0], False)
        self.assertEqual(_ebox_local.mCheckSingleNode("scaqab10adm01")[0], False)
        self.assertEqual(_ebox_local.mCheckSingleNode("scaqab10client01vm08")[0], True)
        ebLogInfo("Unit test on exaBoxCluCtrl.mCheckSingleNode succeeded.")

    def test_mEnableNoAuthDBCS(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mEnableNoAuthDBCS")

        _ebox_local = copy.deepcopy(self.mGetClubox())
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
             patch('exabox.utils.node.exaBoxNode.mDisconnect'):
             _ebox_local._exaBoxCluCtrl__exacm = False
             _ebox_local._exaBoxCluCtrl__ociexacc = False
             _ebox_local.mEnableNoAuthDBCS()
             _ebox_local._exaBoxCluCtrl__ociexacc = True
             _ebox_local.mEnableNoAuthDBCS()
        ebLogInfo("Unit test on exaBoxCluCtrl.mEnableNoAuthDBCS succeeded.")

    def test_mFedrampConfig(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mFedrampConfig")

        _ebox_local = copy.deepcopy(self.mGetClubox())

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=False),\
             patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mCompareFiles', return_value=False),\
             patch('exabox.utils.node.exaBoxNode.mCopyFile'),\
             patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteFileFedramp'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRegisterCronJob'):
             _ebox_local.mFedrampConfig("ibswitch")

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True),\
             patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mCompareFiles', return_value=False),\
             patch('exabox.utils.node.exaBoxNode.mCopyFile'),\
             patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteFileFedramp'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRegisterCronJob'):
             _ebox_local.mFedrampConfig("cells")
             _ebox_local.mFedrampConfig("dom0")
             _ebox_local.mFedrampConfig("domu")

        ebLogInfo("Unit test on exaBoxCluCtrl.mFedrampConfig succeeded.")

    def test_mRegisterCronJob(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mRegisterCronJob")

        _ebox_local = copy.deepcopy(self.mGetClubox())
        with patch('json.loads', side_effect=Exception("File cronjob.conf doesn't exist.")):
            _ebox_local.mRegisterCronJob(["mock_dom0_1", "mock_dom0_2"], ["mock_domu_1", "mock_domu_2"], ["mock_cell_1", "mock_cell_2"], ["mock_sw_1", "mock_sw_2"])

        with patch('json.loads', return_value=MOCK_CRONJOB_CONF),\
             patch("builtins.open", mock_open(read_data="data")),\
             patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mCompareFiles', return_value=False),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmd'),\
             patch('exabox.utils.node.exaBoxNode.mCopyFile'),\
             patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'):
            _ebox_local.mRegisterCronJob(["mock_dom0_1", "mock_dom0_2"], ["mock_domu_1", "mock_domu_2"], ["mock_cell_1", "mock_cell_2"], ["mock_sw_1", "mock_sw_2"])
        ebLogInfo("Unit test on exaBoxCluCtrl.mRegisterCronJob succeeded.")

    def test_mExecuteFileFedramp(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mExecuteFileFedramp")

        _ebox_local = copy.deepcopy(self.mGetClubox())

        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mCompareFiles', return_value=False),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmd'),\
             patch('exabox.utils.node.exaBoxNode.mCopyFile'),\
             patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'):
            _ebox_local.mExecuteFileFedramp("mock_host", "mock_local_file", "mock_remote_file")
        ebLogInfo("Unit test on exaBoxCluCtrl.mExecuteFileFedramp succeeded.")

    def test_mSetupDomUsForSecurePatchServerCommunicationNonCaSignedCert(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mSetupDomUsForSecurePatchServerCommunication")

        _ebox_local = copy.deepcopy(self.mGetClubox())

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsCaSignedCerts', return_value=False),\
             patch('os.path.isfile', return_value=True),\
             patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mCopyFile'),\
             patch('exabox.utils.node.exaBoxNode.mFileExists', return_value=True),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
             patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', side_effect=iter([0, 1])),\
             patch('exabox.utils.node.exaBoxNode.mDisconnect'):
            _ebox_local.mSetupDomUsForSecurePatchServerCommunication()
        ebLogInfo("Unit test on exaBoxCluCtrl.mSetupDomUsForSecurePatchServerCommunication succeeded.")

    def test_mSetupDomUsForSecurePatchServerCommunicationCaSignedCert(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mSetupDomUsForSecurePatchServerCommunication")

        _ebox_local = copy.deepcopy(self.mGetClubox())

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsCaSignedCerts', return_value=True),\
             patch('os.path.exists', return_value=False),\
             patch('os.path.isfile', return_value=True),\
             patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mCopyFile'),\
             patch('exabox.utils.node.exaBoxNode.mFileExists', return_value=True),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
             patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', side_effect=iter([0, 1])),\
             patch('exabox.utils.node.exaBoxNode.mDisconnect'):
             _ebox_local.mSetupDomUsForSecurePatchServerCommunication()
        ebLogInfo("Unit test on exaBoxCluCtrl.mSetupDomUsForSecurePatchServerCommunication succeeded.")

    def test_mSetupDomUsForSecureDBCSCommunication(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mSetupDomUsForSecureDBCSCommunication")

        _ebox_local = copy.deepcopy(self.mGetClubox())

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', return_value="mock_json_file.json"),\
             patch('json.load', return_value={"ociAdminHeadEndType": "WSS"}),\
             patch("builtins.open", mock_open(read_data="data")),\
             patch('os.path.isfile', return_value=True),\
             patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
             patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', side_effect=iter([0, 1, 1])),\
             patch('exabox.utils.node.exaBoxNode.mCopyFile'),\
             patch('exabox.utils.node.exaBoxNode.mDisconnect'):
             _ebox_local.mSetupDomUsForSecureDBCSCommunication()

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', return_value="mock_json_file.json"),\
             patch('json.load', return_value={"ociAdminHeadEndType": "NOTWSS"}),\
             patch("builtins.open", mock_open(read_data="data")),\
             patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mDisconnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
             patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', side_effect=iter([0, 0, 1])),\
             patch('exabox.utils.node.exaBoxNode.mCopyFile'),\
             patch('os.path.isfile', return_value=True):
             _ebox_local.mSetupDomUsForSecureDBCSCommunication()

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption', return_value=None),\
             patch('os.path.isfile', return_value=False):
            _ebox_local.mSetupDomUsForSecureDBCSCommunication()

        ebLogInfo("Unit test on exaBoxCluCtrl.mSetupDomUsForSecureDBCSCommunication succeeded.")

    def test_mRebootNodesIfNoVMExists(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mRebootNodesIfNoVMExists")
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _ebox_local.mSetRequestObj(ebJobRequest("cmd_type", {}))

        _domu_set = {"domu1.us.oracle.com", "domu2.us.oracle.com"}
        with patch('exabox.ovm.clucontrol.ProcessManager.mStartAppend'),\
             patch('exabox.ovm.clucontrol.ProcessManager.mJoinProcess'):
             _ebox_local.mRebootNodesIfNoVMExists(_domu_set, "domu")

        _dom0_set = {"dom0-1.us.oracle.com", "dom0-2.us.oracle.com"}
        _mock_hv_instance = mockHVInstance()
        _ebox_local._exaBoxCluCtrl__shared_env = True
        """
        with patch('exabox.ovm.clucontrol.ProcessManager.mStartAppend'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNode'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mAcquireRemoteLock'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mReleaseRemoteLock'),\
             patch('exabox.ovm.clucontrol.getHVInstance', return_value=_mock_hv_instance),\
             patch('exabox.ovm.clucontrol.ProcessManager.mJoinProcess'):
             _ebox_local.mRebootNodesIfNoVMExists(_dom0_set, "dom0")
        """

        _mock_hv_instance.mSetRunningDomUs(["domu1.us.oracle.com", "domu2.us.oracle.com"])
        with patch('exabox.ovm.clucontrol.ProcessManager.mStartAppend'),\
             patch('exabox.ovm.clucontrol.getHVInstance', return_value=_mock_hv_instance),\
             patch('exabox.ovm.clucontrol.ProcessManager.mJoinProcess'):
             _ebox_local.mRebootNodesIfNoVMExists(_dom0_set, "dom0")

        _mock_hv_instance.mSetRunningDomUs([])
        _cell_set = {"cell1.us.oracle.com", "cell2.us.oracle.com"}
        with patch('exabox.ovm.clucontrol.ProcessManager.mStartAppend'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNode'),\
             patch('exabox.ovm.clucontrol.getHVInstance', return_value=_mock_hv_instance),\
             patch('exabox.ovm.clucontrol.ProcessManager.mJoinProcess'):
             _ebox_local.mRebootNodesIfNoVMExists(_cell_set, "cell")

        _mock_hv_instance.mSetRunningDomUs(["domu1.us.oracle.com", "domu2.us.oracle.com"])
        with patch('exabox.ovm.clucontrol.getHVInstance', return_value=_mock_hv_instance):
             _ebox_local.mRebootNodesIfNoVMExists(_cell_set, "cell")


    def test_mHandlerUnlockDeviceUsingIlom(self):
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'),\
             patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
             self.mGetClubox().mHandlerUnlockDeviceUsingIlom()
        
    def test_mHandlerEnableAccessControlIlom(self):
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'),\
             patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
             self.mGetClubox().mHandlerEnableAccessControlIlom()

    def test_mIlomsCommandStream(self):
        _cmds = [['->', 'start -script /SP/Console'], ['\\(', 'root'], ['Password:', 'welcome1'], ['#', '/opt/oracle.cellos/host_access_control access --open'], ['#', 'exit']]
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'),\
             patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
             self.mGetClubox().mIlomsCommandStream(_cmds)

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsHostOL8', return_value=True)
    def test_mRemoveFqdnOnDomU(self, mock_mIsHostOL8):
        _cmds = {                
            self.mGetRegexVm():                            
            [        
                [    
                    exaMockCommand("hostname | grep", aRc=0, aStdout="scaqab10client01vm08.us.oracle.com", aPersist=True),          
                    exaMockCommand("sed -i '/HOSTNAME/d' /etc/sysconfig/network", aRc=0, aStdout="", aPersist=True),                                    
                    exaMockCommand("echo 'HOSTNAME=scaqab10client01vm08' >> /etc/sysconfig/network", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("echo 'HOSTNAME=scaqab10client02vm08' >> /etc/sysconfig/network", aRc=0, aStdout="", aPersist=True)
                     
                ]    
            ]        
        }            
        self.mPrepareMockCommands(_cmds)                   
        self.mGetClubox().mRemoveFqdnOnDomU()      


    def test_mVerifyClusterwareBmCloud(self):
        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("cat /etc/oratab *", aRc=0, aStdout="+ASM2:/u01/app/19.0.0.0/gridHome2:N", aPersist=True),
                    exaMockCommand("/u01/app/19.0.0.0/gridHome2/bin/cluvfy stage -post crsinst -n *", aRc=0, aStdout="", aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mVerifyClusterwareBmCloud()

    def test_mAppendOedaKeysLog(self):
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    exaMockCommand("mkdir -p *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("echo *", aRc=0, aStdout="", aPersist=True),
                    
                ]
            ],
            self.mGetRegexCell():
            [
                [
                    exaMockCommand("mkdir -p *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("echo *", aRc=0, aStdout="", aPersist=True),
                ]
            ],
            self.mGetRegexSwitch():
            [
                [
                    exaMockCommand("mkdir -p *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("echo *", aRc=0, aStdout="", aPersist=True),
                ]
            ],
            self.mGetRegexLocal():
            [
                [
                    exaMockCommand("/bin/hostname", aRc=0, aStdout="hostname", aPersist=True),
                ]
            ],
        }
        self.mPrepareMockCommands(_cmds)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        self.mGetClubox().mAppendOedaKeysLog(_options)

    def test_mCopyExacmPatchKeyScript(self):
        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("mkdir -p *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("scp *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("chmod *", aRc=0, aStdout="", aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mCopyExacmPatchKeyScript()

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsHostOL8', return_value=True)
    def test_mATPSecureListeners_forced(self, mock_mIsHostOL8):
        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("iptables *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/sbin/iptables-save *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("systemctl *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/usr/sbin/nft *", aRc=0, aStdout="", aPersist=True),

                ]
            ]
        }


        self.mGetContext().mSetConfigOption('skip_atpseclistener', 'False')
        self.mPrepareMockCommands(_cmds)
        self.assertEqual(None, self.mGetClubox().mATPSecureListeners())

    def test_mATPSecureListeners_skipped(self):

        _cmds = {
            self.mGetRegexVm():
            [
                [

                ]
            ]
        }


        # No mock commands to run, this should be a no-op. Ref 36814084
        self.mGetContext().mSetConfigOption('skip_atpseclistener', 'True')
        self.mPrepareMockCommands(_cmds)
        self.assertEqual(2, self.mGetClubox().mATPSecureListeners())

    @patch('exabox.agent.ebJobRequest.ebJobRequest.mLoadRequestFromDB')
    @patch('exabox.core.DBStore3.ebExacloudDB.mGetCompleteRequest')
    @patch('exabox.core.DBStore3.ebExacloudDB.mUpdateRequest')
    @patch('exabox.core.DBStore3.ebExacloudDB.mInsertNewRequest')
    def test_mHandlerOperationCleanup(self, mock_mInsertNewRequest, mock_mUpdateRequest, mock_mGetCompleteRequest,
                                      mock_mLoadRequestFromDB):
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf['uuid'] = "fbf57ed8-75d1-11eb-8273-fa163e241d20"

        _db = ebGetDefaultDB()
        _params = {"uuid": "fbf57ed8-75d1-11eb-8273-fa163e241d20"}
        _req = ebJobRequest(f"cluctrl.xsvault", _params, aDB=ebGetDefaultDB())
        _req.mRegister()

        self.mGetClubox().mHandlerOperationCleanup(_options)

    @patch("exabox.ovm.vmcontrol.ebVgLifeCycle.mDispatchEvent")
    def test_mForceDeleteDomainUnnamed(self, mock_dispatchEvent):
        _cmds = {
            self.mGetRegexDom0():[
                    [
                        exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: KVMHOST" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: KVMHOST" ,aPersist=True),
                        exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/grep 'running' | /bin/awk '{print $1}'", aRc=0, aStdout="scaqab10client01vm08.us.oracle.com(2)" ,aPersist=True),
                        exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aRc=0, aStdout="scaqab10client01vm08.us.oracle.com" ,aPersist=True),
                    ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        mock_dispatchEvent.side_effect = None

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        get_gcontext().mSetConfigOption('_force_delete_unnamed', 'True')
        self.mGetClubox().mRegisterVgComponents()
        self.mGetClubox().mForceDeleteDomainUnnamed(_options)

    def test_mValidateTmpKeyVm(self):
        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("mkdir -p *", aRc=0, aStdout="", aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())

        _jsonconf = {}
        _jsonconf['user'] = 'root'
        _jsonconf['vmName'] = 'scaqab10client01vm08.us.oracle.com'
        self.mGetClubox().mValidateTmpKeyVm(_options, _jsonconf)

    def test_mGenerateTmpKeyVm(self):
        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("mkdir -p *", aRc=0, aStdout="", aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())

        _jsonconf = {}
        _jsonconf['user'] = 'root'
        _jsonconf['vmName'] = 'scaqab10client01vm08.us.oracle.com'
        self.mGetClubox().mGenerateTmpKeyVm(_options, _jsonconf)

    def test_mCleanUpTmpKeyVm(self):
        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("sed -i '/TEMPORAL_KEY/d' .ssh/authorized_keys", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/opt/oracle.cellos/host_access_control rootssh -l", aRc=0, aStdout="", aPersist=True),

                ]
            ],
            self.mGetRegexNatVm():
            [
                [
                    exaMockCommand("sed -i '/TEMPORAL_KEY/d' .ssh/authorized_keys", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/opt/oracle.cellos/host_access_control rootssh -l", aRc=0, aStdout="", aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())

        _jsonconf = {}
        _jsonconf['user'] = 'root'
        _jsonconf['vmName'] = 'scaqab10client01vm08.us.oracle.com'
        self.mGetClubox().mCleanUpTmpKeyVm(_options, _jsonconf)

    def test_mRestoreRootAccess(self):
        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("sh -c *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/opt/oracle.cellos/host_access_control rootssh -l", aRc=0, aStdout="", aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        get_gcontext().mSetConfigOption('enable_restore_root', 'True')
        get_gcontext().mSetConfigOption('remove_root_access', 'True')

        _options.jsonconf['TargetType'] = 'domu'
        self.mGetClubox().mRestoreRootAccess(_options)

    def test_mUnRestoreRootAccess(self):
        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("sed -i '/TEMPORAL_KEY/d' .ssh/authorized_keys", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/opt/oracle.cellos/host_access_control rootssh -l", aRc=0, aStdout="", aPersist=True),

                ]
            ],
            self.mGetRegexNatVm():
            [
                [
                    exaMockCommand("sed -i '/TEMPORAL_KEY/d' .ssh/authorized_keys", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/opt/oracle.cellos/host_access_control rootssh -l", aRc=0, aStdout="", aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        get_gcontext().mSetConfigOption('enable_restore_root', 'True')
        get_gcontext().mSetConfigOption('remove_root_access', 'True')

        _options.jsonconf['TargetType'] = 'domu'
        self.mGetClubox().mUnRestoreRootAccess(_options)

    def test_mRemoveUseDnsFlag(self):
        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("/bin/sed *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/sbin/service sshd restart", aRc=0, aStdout="", aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        self.mGetClubox().mRemoveUseDnsFlag()

    def test_mLockCellUsers(self):
        _cmds = {
            self.mGetRegexCell():
            [
                [
                    exaMockCommand("echo *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("passwd *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("ip a sync", aRc=0, aStdout="", aPersist=True),

                ]
            ],
                self.mGetRegexLocal():                           
                [
                     [ 
                         exaMockCommand("/bin/ping *", aRc=0, aStdout="" ,aPersist=True),
                     ]
                ]
        }
        self.mPrepareMockCommands(_cmds)

        self.mGetClubox().mLockCellUsers(aMode=True)

    def test_mDeletePKeyCell(self):
        _cmds = {
            self.mGetRegexCell():
            [
                [
                    exaMockCommand("cellcli -e *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("ipconf *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("ip a sync", aRc=0, aStdout="", aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        self.mGetClubox().mSetExabm(True)
        self.mGetClubox().mSetSharedEnv(False)

        with patch('exabox.ovm.clucontrol.ProcessManager.mStartAppend'),\
             patch("exabox.ovm.clucontrol.ProcessManager.mJoinProcess"):
             self.mGetClubox().mDeletePKeyCell()

    def test_mCheckDom0Status(self):
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    exaMockCommand("/usr/local/bin/ipconf *", aRc=0, aStdout="Consistency check PASSED", aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        get_gcontext().mSetConfigOption('skip_dom0_consistency_fix', 'False')
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        self.mGetClubox().mCheckDom0Status(_options)

    def test_mCheckCellsStatus_DISABLED_EXABOX_CONF(self):
        _cmds = {
            self.mGetRegexCell():
            [
                [

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        get_gcontext().mSetConfigOption('skip_cells_consistency_fix', 'True')
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        self.assertEqual(2, self.mGetClubox().mCheckCellsStatus(_options))

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNode")
    def test_mCheckCellsStatus_SUCCESS(self, mock_rebootNode):
        _cmds = {
            self.mGetRegexCell():
            [
                [
                    exaMockCommand("ipconf -check-consistency -semantic", aRc=0, aStdout="Consistency check PASSED", aPersist=True),
                    exaMockCommand("cp *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("ipconf *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("service *", aRc=0, aStdout="", aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        get_gcontext().mSetConfigOption('skip_cells_consistency_fix', 'False')
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        self.assertEqual(None, self.mGetClubox().mCheckCellsStatus(_options))

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNode")
    def test_mCheckCellsStatus_FAILURE(self, mock_rebootNode):
        _cmds = {
            self.mGetRegexCell():
            [
                [
                    exaMockCommand("ipconf -check-consistency -semantic", aRc=0, aStdout="Consistency check FAILED", aPersist=True),
                    exaMockCommand("cp *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("ipconf *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("service *", aRc=0, aStdout="", aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        get_gcontext().mSetConfigOption('skip_cells_consistency_fix', 'False')
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        self.assertRaises(ExacloudRuntimeError, self.mGetClubox().mCheckCellsStatus, _options)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNode")
    def test_mCheckCellLimits(self, mock_rebootNode):
        _cmds = {
            self.mGetRegexCell():
            [
                [
                    exaMockCommand("grep *", aRc=0, aStdout="UsePAM yes", aPersist=True),
                    exaMockCommand("echo *", aRc=0, aStdout="", aPersist=True),


                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        self.mGetClubox().mCheckCellLimits()

    def test_mCheckIsCellConfigured(self):
        _cmds = {
            self.mGetRegexCell():
            [
                [
                    exaMockCommand("ip link show *", aRc=0, aStdout="0", aPersist=True),
                    exaMockCommand("grep -c *", aRc=0, aStdout="2", aPersist=True),


                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        self.mGetClubox().mCheckIsCellConfigured()

    def test_mPostVMArpingCheck(self):
        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("/sbin/ip addr show bondeth1", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/sbin/arping *", aRc=0, aStdout="", aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        self.mGetClubox().mPostVMArpingCheck(_options)

    def test_mHandlerCellsReset(self):
        _cmds = {
            self.mGetRegexCell():
            [
                [
                    exaMockCommand("cellcli -e *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/opt/oracle.ExaWatcher/StopExaWatcher.sh", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("reboot", aRc=0, aStdout="", aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        self.mGetClubox().mHandlerCellsReset(_options)

    def test_formStepList(self):
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.runstep = "OSTP_PREVM_INSTALL"
        self.mGetClubox().formStepList(True, _options)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetExadataCellModel")
    def test_mCellSecureShredding(self, mock_getCellModel):
        _cmds = {
            
            self.mGetRegexCell():
            [
                [
                    exaMockCommand("cellcli -e *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("/bin/python /opt/oracle.cellos/lib/python/secureeraser --list --hdd *",
                        aRc=0, aStdout="21130UM7XE\n21130SEYLE\n", aPersist=True),
                    exaMockCommand("/bin/python /opt/oracle.cellos/lib/python/secureeraser --erase --erasure_method_optional *",
                        aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/usr/bin/ls /root/secure_cell_erase_certs/*", aRc=0, aStdout="secureeraser.2004XLA0KF.20240802_125741.certificate.html", aPersist=True),
                ],
                [
                    exaMockCommand("/usr/local/bin/imageinfo -version", aStdout="20.1.1.0.0.200808"),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        mock_getCellModel.return_value = 'X7'

        get_gcontext().mSetConfigOption('cellerase_pass', '7PASS')
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.skip_serase = False
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteLocal', return_value=(0, None, "", None)):
            self.mGetClubox().mCellSecureShredding(_options)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetExadataCellModel")
    def test_mVMImagesShredding(self, mock_getCellModel):
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    exaMockCommand("echo *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("shred --verbose *", aRc=0, aStdout="", aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        mock_getCellModel.return_value = 'X7'

        get_gcontext().mSetConfigOption('shredding_enabled', 'True')
        get_gcontext().mSetConfigOption('vmerase_pass', '7PASS')
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.skip_serase = False
        self.mGetClubox().mVMImagesShredding(_options)

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckAsmIsUp")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCrsIsUp")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRestartVM")
    @patch("exabox.ovm.vmcontrol.ebVgLifeCycle.mDispatchEvent")
    def test_mStartVMExacsService(self, mock_dispatchEvent, mock_restartVM, mock_crs, mock_asm):
        _cmds = {
            self.mGetRegexDom0():[
                    [
                        exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: KVMHOST" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: KVMHOST" ,aPersist=True),
                        exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/grep 'running' | /bin/awk '{print $1}'", aRc=0, aStdout="scaqab10client01vm08.us.oracle.com(2)" ,aPersist=True),
                        exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aRc=0, aStdout="scaqab10client01vm08.us.oracle.com" ,aPersist=True),
                        exaMockCommand("virsh sysinfo", aRc=0, aStdout=customOutput1 ,aPersist=True),
                        exaMockCommand("/usr/sbin/vm_maker --dumpxml *", aRc=0, aStdout="<domain type='kvm' id='2'><os><type arch='x86_64' machine='pc-q35-4.2'>hvm</type><boot dev='hd'/></os></domain>" ,aPersist=True),
                        exaMockCommand("/usr/bin/virsh undefine *", aRc=0,aStdout="",aPersist=True),
                        exaMockCommand("/usr/bin/virsh define *", aRc=0,aStdout="",aPersist=True),
                        exaMockCommand("/opt/exadata_ovm/vm_maker --autostart *", aRc=0,aStdout="",aPersist=True),
                        exaMockCommand("virsh attach-device *", aRc=0,aStdout="",aPersist=True),
                    ],
                    [
                        exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: KVMHOST" ,aPersist=True),
                        exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/grep 'running' | /bin/awk '{print $1}'", aRc=0, aStdout="scaqab10client01vm08.us.oracle.com(2)" ,aPersist=True),
                        exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aRc=0, aStdout="scaqab10client01vm08.us.oracle.com" ,aPersist=True),
                        exaMockCommand("/bin/virsh list"),
                        exaMockCommand("/opt/exadata_ovm/vm_maker --autostart *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/opt/exadata_ovm/vm_maker --stop-domain *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/rm *", aRc=0,aStdout="",aPersist=True),
                        exaMockCommand("/bin/mkdir -p *", aRc=0,aStdout="",aPersist=True),
                        exaMockCommand("/usr/sbin/vm_maker --dumpxml *", aRc=0, aStdout="<domain type='kvm' id='2'><os><type arch='x86_64' machine='pc-q35-4.2'>hvm</type><boot dev='hd'/></os></domain>" ,aPersist=True),
                        exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("systemctl is-enabled vmexacs_kvm", aRc=0, aStdout="enabled" ,aPersist=True),
                        exaMockCommand("systemctl daemon-reload", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/virsh list", aStdout="scaqab10client01vm08.us.oracle.com scaqab10client02vm08.us.oracle.com")
                    ],
                    [
                        exaMockCommand("virsh sysinfo", aRc=0, aStdout=customOutput1 ,aPersist=True),
                        exaMockCommand("/usr/sbin/vm_maker --dumpxml *", aRc=0, aStdout="<domain type='kvm' id='2'><os><type arch='x86_64' machine='pc-q35-4.2'>hvm</type><boot dev='hd'/></os></domain>" ,aPersist=True),
                        exaMockCommand("/usr/bin/virsh undefine *", aRc=0,aStdout="",aPersist=True),
                        exaMockCommand("/usr/bin/virsh define *", aRc=0,aStdout="",aPersist=True),
                        exaMockCommand("/opt/exadata_ovm/vm_maker --autostart *", aRc=0,aStdout="",aPersist=True),
                        exaMockCommand("virsh attach-device *", aRc=0,aStdout="",aPersist=True),
                    ],
                    [
                        exaMockCommand("/bin/rm *", aRc=0,aStdout="",aPersist=True),
                        exaMockCommand("/bin/mkdir -p *", aRc=0,aStdout="",aPersist=True),
                        exaMockCommand("/usr/sbin/vm_maker --dumpxml *", aRc=0,aStdout="",aPersist=True),
                        exaMockCommand("/bin/scp *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("systemctl is-enabled vmexacs_kvm", aRc=0, aStdout="enabled" ,aPersist=True),
                        exaMockCommand("systemctl daemon-reload", aRc=0, aStdout="" ,aPersist=True),
                    ]
            ],
            self.mGetRegexLocal():                           
            [
                [ 
                    exaMockCommand("/bin/rm -rf *", aRc=0, aStdout="" ,aPersist=True),
                ]
            ],
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("cat /sys/devices/virtual/dmi/id/chassis_asset_tag", aRc=0, aStdout="7338405" ,aPersist=True),

                ],
                [
                    exaMockCommand(re.escape("cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                    exaMockCommand(re.escape("/u01/app/19.0.0.0/grid/bin/crsctl check cluster -all | grep -c online | grep -w 6"), aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl query css votedisk *", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl *", aRc=0, aStdout="2" ,aPersist=True),
                ],
                [
                    exaMockCommand(re.escape("cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        mock_dispatchEvent.side_effect = None
        mock_dispatchEvent.return_value = 0
        mock_restartVM.return_value = 0

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        self.mGetClubox().mRegisterVgComponents()
        with patch('exabox.ovm.clucontrol.time.sleep'),\
             patch('exabox.ovm.clucontrol.ProcessManager.mStartAppend'),\
             patch("exabox.ovm.clucontrol.ProcessManager.mJoinProcess"):
             self.mGetClubox().mStartVMExacsService(_options)
             
    def test_mUpdateVmetrics(self):
        _cmds = {
            self.mGetRegexDom0():[
                    [
                        exaMockCommand("/bin/test -e /etc/init.d/vmexacs", aRc=1, aStdout="", aPersist=True),
                        exaMockCommand("/bin/test -e /etc/init.d/vmexacs.conf", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/test -e /etc/init.d/networkstatus.py", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("chmod 555 /etc/init.d/vmexacs;mkdir -p /opt/oracle.vmexacs/",  aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("chmod 555 /opt/oracle.vmexacs/vmexacs", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("chmod 555 /opt/oracle.vmexacs/networkstatus.py", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("chmod 555 /opt/oracle.vmexacs/vmexacs.conf", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("chkconfig vmexacs on", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("cd /etc/init.d; service vmexacs start", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("cd /etc/init.d; service vmexacs status", aRc=0, aStdout='[["Running"]]', aPersist=True)
                    ]
            ],
            self.mGetRegexLocal():                           
            [
                [ 
                    exaMockCommand("/bin/rm -rf *", aRc=0, aStdout="" ,aPersist=True),
                ]
            ],
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("cat /sys/devices/virtual/dmi/id/chassis_asset_tag", aRc=0, aStdout="7338405" ,aPersist=True),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        self.mGetClubox().mRegisterVgComponents()
        with patch('exabox.utils.node.exaBoxNode.mCopyFile'),\
             patch('exabox.ovm.clucontrol.ProcessManager.mStartAppend'),\
             patch("exabox.ovm.clucontrol.ProcessManager.mJoinProcess"):
             self.mGetClubox().mUpdateVmetrics('vmexacs')

    def test_mUpdateCelldiskSize(self):
        _cmds = {
            self.mGetRegexCell():
            [
                [
                    exaMockCommand("cellcli -e list physicaldisk *", aRc=0, aStdout="16.03"),
                    exaMockCommand("cellcli -e list physicaldisk *", aRc=0, aStdout="12.47"),
                    exaMockCommand("cellcli -e list physicaldisk *", aRc=0, aStdout="16.03"),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mUpdateCelldiskSize()
        self.assertEqual(self.mGetClubox()._exaBoxCluCtrl__esracks.mGetDiskSize(), 18)
        
    def test_mUpdateCelldiskSize_edge_case_X7(self):  
        _cmds = {
            self.mGetRegexCell():
            [
                [
                    exaMockCommand("cellcli -e list physicaldisk *", aRc=0, aStdout="8.9"),
                    exaMockCommand("cellcli -e list physicaldisk *", aRc=0, aStdout="8.9"),
                    exaMockCommand("cellcli -e list physicaldisk *", aRc=0, aStdout="8.9"),

                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mUpdateCelldiskSize()
        self.assertEqual(self.mGetClubox()._exaBoxCluCtrl__esracks.mGetDiskSize(), 10)
        
        
    def test_mUpdateCelldiskSize_handle_specific_sizes(self):  
        # Simulate known specific sizes for direct mapping  
        specific_sizes = {  
            "8.9": 10, "12.47": 14, "16.03": 18, "20.00": 22  
        }
        for size, expected in specific_sizes.items():  
            with self.subTest(size=size, expected=expected):  
                _cmds = {
                    self.mGetRegexCell():
                    [
                        [
                            exaMockCommand("cellcli -e list physicaldisk *", aRc=0, aStdout=size),
                            exaMockCommand("cellcli -e list physicaldisk *", aRc=0, aStdout=size),
                            exaMockCommand("cellcli -e list physicaldisk *", aRc=0, aStdout=size),

                        ]
                    ]
                }
                self.mPrepareMockCommands(_cmds)  
                self.mGetClubox().mUpdateCelldiskSize()  
                self.assertEqual(self.mGetClubox()._exaBoxCluCtrl__esracks.mGetDiskSize(), expected) 

    def test_mUpdateCelldiskSize_multiline(self):
        _cmds = {
            self.mGetRegexCell("01"):
            [
                [
                    exaMockCommand("cellcli -e list physicaldisk *", aRc=0, aStdout="16.03\n12.34"),
                ]
            ],
            self.mGetRegexCell("02"):
            [
                [
                    exaMockCommand("cellcli -e list physicaldisk *", aRc=0, aStdout="12.47\n1.234\n2.345"),
                ]
            ],
            self.mGetRegexCell("03"):
            [
                [
                    exaMockCommand("cellcli -e list physicaldisk *", aRc=0, aStdout="98.7654321"),
                ]
            ]

        }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mUpdateCelldiskSize()
        self.assertEqual(self.mGetClubox()._exaBoxCluCtrl__esracks.mGetDiskSize(), 14)

    def test_generic_exception_handling(self):
        _cmds = {
            self.mGetRegexCell(): [  
                exaMockCommand("cellcli -e list physicaldisk *", aRc=0, aStdout=""),  
            ] 
        }
        self.mPrepareMockCommands(_cmds)  

        clubox = self.mGetClubox()
        try:
            clubox.mUpdateCelldiskSize() 
        except ExacloudRuntimeError as e:
            self.assertEqual(e.mGetErrorMsg(), 'EXACLOUD : Could not update Cell Disk Size')
            self.assertEqual(e.mGetErrorCode(), 2085)
            
    def test_mParseOEDAErrorJson(self):

        get_gcontext().mSetConfigOption('ssh_diagnostic', 'False')

        _cmds = {
            self.mGetRegexCell(): [  
                [
                    exaMockCommand("cellcli -e list griddisk ATTRIBUTES name, size | /bin/grep hcpool", aRc=1, aStdout="")
                ],
                [
                    exaMockCommand("cellcli -e list griddisk ATTRIBUTES name, size | /bin/grep hcpool", aRc=1, aStdout="")
                ],
                [
                    exaMockCommand("cellcli -e list griddisk ATTRIBUTES name, size | /bin/grep hcpool", aRc=1, aStdout="")
                ]
            ] 
        }
        self.mPrepareMockCommands(_cmds)  

        with patch('os.path.exists', return_value=False):

            _cmd_output = [["Successfully completed execution of step Install Cluster Software.", "Releasing all sessions for cleanup..."], None]
            _rc, _skip_exception = self.mGetClubox().mParseOEDAErrorJson(_cmd_output, 'ESTP_INSTALL_CLUSTER')
            self.assertEqual(_rc, True)

        with patch('os.path.exists', return_value=True),\
             patch("builtins.open", mock_open(read_data=MOCK_ERROR_JSON)):
            _cmd_output = [["ERROR:Lock phx107125exdcl09phx107125exdadminphx1oraclevcncom-creategridlock on node phx107125exdcl09.phx107125exd.adminphx1.oraclevcn.com", "Releasing all sessions for cleanup..."], None]
            _rc, _skip_exception = self.mGetClubox().mParseOEDAErrorJson(_cmd_output, 'ESTP_CREATE_STORAGE')
            self.assertEqual(_rc, False)
            self.assertEqual(_skip_exception, False)

            _cmd_output = [["Error: Errors occurred...", "Releasing all sessions for cleanup..."], None]
            _rc, _skip_exception = self.mGetClubox().mParseOEDAErrorJson(_cmd_output, 'ESTP_CREATE_STORAGE')
            self.assertEqual(_rc, False)
            self.assertEqual(_skip_exception, False)

        with patch('os.path.exists', return_value=True),\
             patch("builtins.open", mock_open(read_data=MOCK_SKIP_ERROR_JSON)):

            _cmd_output = [[": KommandException error\nCommand return code: 1.\nHost: scas22celadm06.us.oracle.com\nUser: root\nCommand: /opt/oracle.SupportTools/exadataAIDE -u\nKommandException message: Command output:\n AIDE: database update request accepted."], None]
            _rc, _skip_exception = self.mGetClubox().mParseOEDAErrorJson(_cmd_output, 'ESTP_INSTALL_CLUSTER')
            self.assertEqual(_rc, False)
            self.assertEqual(_skip_exception, True)

    def test_mParseOEDALog_success_banner_followed_by_error_line(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _oeda_path = _ebox_local.mGetOedaPath()
        _work_dir = os.path.join(_oeda_path, 'WorkDir')
        os.makedirs(_work_dir, exist_ok=True)
        _error_json = os.path.join(_work_dir, 'OedaErrors.json')

        _cmd_output = ([
            "===== Successfully completed execution of step Setup Cell Connectivity =====",
            "Errors occurred. Send /tmp/Diag-260206_205651.zip to Oracle to receive assistance."
        ], None)

        def _exists_side_effect(path, _orig=os.path.exists):
            if path == _error_json:
                return False
            return _orig(path)

        with patch('os.path.exists', side_effect=_exists_side_effect), \
             patch('exabox.ovm.clucontrol.ebLogWarn') as mock_warn, \
             patch.object(_ebox_local, 'mCollectExtraInfoFromErrorOEDA') as mock_collect, \
             patch.object(_ebox_local, 'mSshDiagnostic') as mock_diag:

            _rc = _ebox_local.mParseOEDALog(_cmd_output, aStep='ESTP_SETUP_CELL_CONNECTIVITY')

        self.assertTrue(_rc)
        mock_warn.assert_not_called()
        mock_collect.assert_not_called()
        mock_diag.assert_not_called()

    def test_mParseOEDALog_success_banner_followed_by_error_line_config_disabled(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _oeda_path = _ebox_local.mGetOedaPath()
        _work_dir = os.path.join(_oeda_path, 'WorkDir')
        os.makedirs(_work_dir, exist_ok=True)
        _error_json = os.path.join(_work_dir, 'OedaErrors.json')

        _cmd_output = ([
            "===== Successfully completed execution of step Setup Cell Connectivity =====",
            "Errors occurred. Send /tmp/Diag-260206_205651.zip to Oracle to receive assistance."
        ], None)

        def _exists_side_effect(path, _orig=os.path.exists):
            if path == _error_json:
                return False
            return _orig(path)

        _orig_check = _ebox_local.mCheckConfigOption

        def _check_config(option, value=None):
            if option == 'ignore_oeda_trailing_errors_after_success' and value == 'True':
                return False
            return _orig_check(option, value)

        with patch('os.path.exists', side_effect=_exists_side_effect), \
             patch('exabox.ovm.clucontrol.ebLogWarn') as mock_warn, \
             patch.object(_ebox_local, 'mCheckConfigOption', side_effect=_check_config), \
             patch.object(_ebox_local, 'mCollectExtraInfoFromErrorOEDA') as mock_collect, \
             patch.object(_ebox_local, 'mSshDiagnostic') as mock_diag:

            _rc = _ebox_local.mParseOEDALog(_cmd_output, aStep='ESTP_SETUP_CELL_CONNECTIVITY')

        self.assertFalse(_rc)
        mock_warn.assert_not_called()
        mock_collect.assert_called_once_with(_cmd_output, 'ESTP_SETUP_CELL_CONNECTIVITY', None)
        mock_diag.assert_not_called()

    def test_mParseOEDALog_success_banner_followed_by_real_error(self):
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _oeda_path = _ebox_local.mGetOedaPath()
        _work_dir = os.path.join(_oeda_path, 'WorkDir')
        os.makedirs(_work_dir, exist_ok=True)
        _error_json = os.path.join(_work_dir, 'OedaErrors.json')

        _cmd_output = ([
            "===== Successfully completed execution of step Setup Cell Connectivity =====",
            "Errors occurred. Send /tmp/Diag-260206_205651.zip to Oracle to receive assistance.",
            "ERROR:Lock Failed to acquire remote lock"
        ], None)

        def _exists_side_effect(path, _orig=os.path.exists):
            if path == _error_json:
                return False
            return _orig(path)

        _orig_check = _ebox_local.mCheckConfigOption

        def _check_config(option, value=None):
            if option == 'ignore_oeda_trailing_errors_after_success' and value == 'True':
                return True
            if option == 'ssh_diagnostic' and value == 'False':
                return True
            return _orig_check(option, value)

        with patch('os.path.exists', side_effect=_exists_side_effect), \
             patch('exabox.ovm.clucontrol.ebLogWarn') as mock_warn, \
             patch('exabox.ovm.clucontrol.ebLogError') as mock_error, \
             patch.object(_ebox_local, 'mCheckConfigOption', side_effect=_check_config), \
             patch.object(_ebox_local, 'mCollectExtraInfoFromErrorOEDA') as mock_collect, \
             patch.object(_ebox_local, 'mSshDiagnostic') as mock_diag:

            _rc = _ebox_local.mParseOEDALog(_cmd_output, aStep='ESTP_SETUP_CELL_CONNECTIVITY')

        self.assertTrue(_rc)
        mock_warn.assert_not_called()
        mock_error.assert_not_called()
        mock_collect.assert_not_called()
        mock_diag.assert_not_called()
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckAsmIsUp")
    def test_mAddOratabEntry(self, mock_mCheckAsmIsUp):
        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("export ORACLE_HOME=/u01/app/19.0.0.0/grid; /u01/app/19.0.0.0/grid/bin/srvctl status asm -node scaqab10client01vm08.us.oracle.com -detail | /bin/grep -m1 'ASM instance'", aRc=0, aStdout="+ASM1"),
                    exaMockCommand("grep \^\+ASM /etc/oratab", aRc=0, aStdout="")
                ],
                [
                    exaMockCommand("export ORACLE_HOME=.* /u01/app/19.0.0.0/grid/bin/srvctl status asm -node scaqab10client02vm08.us.oracle.com*", aRc=0, aStdout="+ASM2"),
                    exaMockCommand("grep \^\+ASM /etc/oratab", aRc=0, aStdout="")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        self.mGetClubox().mAddOratabEntry(aGridHome="/u01/app/19.0.0.0/grid")

    def test_mSetEnvTypeInConfiguration(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mSetEnvTypeInConfiguration")
        _ebox_local = copy.deepcopy(self.mGetClubox())

        _ebox_local.mSetEnvTypeInConfiguration()
        self.assertEqual(self.mGetContext().mGetRegEntry('_dom0_domU_relation')['scaqab10client01vm08.us.oracle.com'], "scaqab10adm01.us.oracle.com")
        self.assertEqual(self.mGetContext().mGetRegEntry('_dom0_domU_relation')['scaqab10adm01nat08.us.oracle.com'], "scaqab10adm01.us.oracle.com")
        self.assertEqual(self.mGetContext().mGetRegEntry('_dom0_domU_relation')['scaqab10client02vm08.us.oracle.com'], "scaqab10adm02.us.oracle.com")
        self.assertEqual(self.mGetContext().mGetRegEntry('_dom0_domU_relation')['scaqab10adm02nat08.us.oracle.com'], "scaqab10adm02.us.oracle.com")
        ebLogInfo("Unit test on exaBoxCluCtrl.mSetEnvTypeInConfiguration succeeded.")

    def test_mGetIlomPass(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mGetIlomPass with ConfigOption")
        _ebox_local = copy.deepcopy(self.mGetClubox())

        with patch('os.path.exists', return_value=False):
            _lastpwd = _ebox_local.mGetIlomPass()
            self.assertIsNotNone(_lastpwd)
        
        with patch('os.path.exists', return_value=True),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmd'),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteLocal', return_value=(0, None, " Dummy password ", None)):
            _lastpwd = _ebox_local.mGetIlomPass()
            self.assertEqual(_lastpwd,"Dummy password")

    def test_mHandlerCaviumReset(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mGetCommandHandler().mHandlerCaviumReset with Ilom Device")
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _local_options = {"hostname": "somehost","ilom_hostname":"someilom","domain_name":"dh","etherface":"eth1"}
        _ebox_local._exaBoxCluCtrl__options.jsonconf = _local_options

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', return_value="X9"),\
             patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'),\
             patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
            self.assertEqual(_ebox_local.mGetCommandHandler().mHandlerCaviumReset(),0)

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', return_value="X10"),\
             patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'),\
             patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
            self.assertEqual(_ebox_local.mGetCommandHandler().mHandlerCaviumReset(),0)

        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', return_value="X11"),\
             patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'),\
             patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"):
            self.assertEqual(_ebox_local.mGetCommandHandler().mHandlerCaviumReset(),0)

    def test_mHandlerCaviumColletDiag(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mGetCommandHandler().test_mHandlerCaviumColletDiag() with Ilom Device")
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _local_options = {"ilom_hostname":"someilom","domain_name":"dh"}
        _ebox_local._exaBoxCluCtrl__options.jsonconf = _local_options
        
        with patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'),\
             patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"),\
             patch('exabox.core.DBStore3.ebExacloudDB.mUpdateRequest'):
            self.assertEqual(_ebox_local.mGetCommandHandler().mHandlerCaviumColletDiag(),0)
    
    def test_mConfigureSyslogIlomHost(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mConfigureSyslogIlomHost")
        
        with patch('exabox.utils.node.exaBoxNode.mConnect'),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog'),\
             patch('exabox.ovm.clucontrol.exaBoxNode.mConnectAuthInteractive'),\
             patch("exabox.ovm.clucontrol.exaBoxNode.mExecuteCmdsAuthInteractive"),\
             patch('exabox.utils.node.exaBoxNode.mExecuteCmd', return_value=(None, mockStream([""]), None)):
            self.mGetClubox().mConfigureSyslogIlomHost()

    def test_mHandlerGetDom0ExistingGuestsSize(self):
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/GuestImages", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/du", aRc=0, aPersist=True),
                    exaMockCommand("/bin/du -sb /EXAVMIMAGES/GuestImages", aRc=0, aStdout="405000850       /EXAVMIMAGES/GuestImages", aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mHandlerGetDom0ExistingGuestsSize()

    def test_mSetSysCtlConfigValue(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mSetSysCtlConfigValue")
        _hpage_param = "vm.nr_hugepages"
        _hpage_value = 8000
        print(self.mGetClubox().mReturnDom0DomUPair()[0][1])
        aDomU = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("/bin/cat /etc/sysctl.conf*", aRc=0, aStdout="vm.nr_hugepages = 61440", aPersist=True),
                    exaMockCommand("/usr/sbin/sysctl -n vm.nr_hugepages", aRc=0, aStdout="61440", aPersist=True),
                    exaMockCommand("/bin/cp *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/sed -i  --follow-symlinks*", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/sysctl", aRc=0, aStdout="/usr/sbin/sysctl", aPersist=True),
                    exaMockCommand("/sbin/sysctl -p /etc/sysctl.conf", aRc=1, aPersist=True),
                    exaMockCommand("/usr/sbin/sysctl -n vm.nr_hugepages", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        with connect_to_host(aDomU, get_gcontext()) as aNode:
            #would fail because sysctl -p returns rc:1
            self.assertEqual(False, self.mGetClubox().mSetSysCtlConfigValue(aNode, _hpage_param, _hpage_value))

    @patch('exabox.ovm.clucontrol.time.sleep')
    @patch('exabox.ovm.clucontrol.node_read_text_file', return_value='kernel.pid_max = 1024')
    def test_mRefreshSysctl(self, mock_node_read_text_file, mock_sleep):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mRefreshSysctl")

        clubox = self.mGetClubox()
        _dom0, _domu = clubox.mReturnDom0DomUPair()[0]

        success_cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /sbin/sysctl", aRc=0, aStdout="/usr/sbin/sysctl", aPersist=True),
                    exaMockCommand("/sbin/sysctl -p /etc/sysctl.conf", aRc=0, aStdout="kernel.pid_max = 4194304", aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(success_cmds)

        with connect_to_host(_dom0, get_gcontext()) as node:
            self.assertEqual(0, clubox.mRefreshSysctl(node, '/etc/sysctl.conf'))

        failure_cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /sbin/sysctl", aRc=0, aStdout="/usr/sbin/sysctl", aPersist=True),
                    exaMockCommand("/sbin/sysctl -p /etc/sysctl.conf", aRc=1, aStdout="kernel.pid_max = 1024", aPersist=True),
                    exaMockCommand("/sbin/sysctl -p /etc/sysctl.conf", aRc=1, aStdout="kernel.pid_max = 1024", aPersist=True),
                    exaMockCommand("/sbin/sysctl -p /etc/sysctl.conf", aRc=1, aStdout="kernel.pid_max = 1024", aPersist=True)
                ]
            ]
        }

        self.mPrepareMockCommands(failure_cmds)

        with connect_to_host(_dom0, get_gcontext()) as node:
            self.assertEqual(1, clubox.mRefreshSysctl(node, '/etc/sysctl.conf'))
        mock_sleep.assert_called_with(3)
        self.assertEqual(mock_sleep.call_count, 2)
        mock_node_read_text_file.assert_called_once()


    def test_mUpdateHugePagesSysctlConf(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mUpdateHugePagesSysctlConf")
        _newmem = "49152"
        _currvmem = "65536"
        _MinHugepageMem = "26"
        print(self.mGetClubox().mReturnDom0DomUPair()[0][1])
        aDomU = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("/bin/grep Hugepagesize /proc/meminfo*", aRc=0, aStdout="2", aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        with patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSysCtlConfigValue", return_value=('/etc/sysctl.conf', "15360")),\
             patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mSetSysCtlConfigValue", return_value=True):
            self.assertEqual(0, self.mGetClubox().mUpdateHugePagesSysctlConf(aDomU, _currvmem, _newmem, _MinHugepageMem))      

    def test_mConfigurePasswordLessDomU_ssh_keyscan_failure_port22(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mConfigurePasswordLessDomU")
        _user = "opc"
        _sshkeyscan_verbose = "debug1: match: OpenSSH_7.4 pat OpenSSH* compat 0x04000000\
                                # se-dbcs-ash-iqnog2:22 SSH-2.0-OpenSSH_7.4\
                                debug1: Enabling compatibility mode for protocol 2.0\
                                debug1: SSH2_MSG_KEXINIT sent\
                                debug1: SSH2_MSG_KEXINIT received\
                                debug1: kex: algorithm: ecdh-sha2-nistp256\
                                debug1: kex: host key algorithm: ssh-rsa\
                                debug1: kex: server->client cipher: aes128-ctr MAC: hmac-sha2-256 compression: none\
                                debug1: kex: client->server cipher: aes128-ctr MAC: hmac-sha2-256 compression: none\
                                debug1: kex: ecdh-sha2-nistp256 need=32 dh_need=32\
                                debug1: kex: ecdh-sha2-nistp256 need=32 dh_need=32\
                                debug1: sending SSH2_MSG_KEX_ECDH_INIT\
                                debug1: expecting SSH2_MSG_KEX_ECDH_REPLY\
                                debug1: match: OpenSSH_7.4 pat OpenSSH* compat 0x04000000\
                                # se-dbcs-ash-iqnog2:22 SSH-2.0-OpenSSH_7.4\
                                debug1: SSH2_MSG_KEXINIT sent\
                                debug1: SSH2_MSG_KEXINIT received\
                                debug1: kex: algorithm: ecdh-sha2-nistp256\
                                debug1: kex: host key algorithm: ecdsa-sha2-nistp256\
                                debug1: kex: server->client cipher: aes128-ctr MAC: hmac-sha2-256 compression: none\
                                debug1: kex: client->server cipher: aes128-ctr MAC: hmac-sha2-256 compression: none\
                                debug1: kex: ecdh-sha2-nistp256 need=32 dh_need=32\
                                debug1: kex: ecdh-sha2-nistp256 need=32 dh_need=32\
                                debug1: sending SSH2_MSG_KEX_ECDH_INIT\
                                debug1: expecting SSH2_MSG_KEX_ECDH_REPLY\
                                debug1: match: OpenSSH_7.4 pat OpenSSH* compat 0x04000000\
                                # se-dbcs-ash-iqnog2:22 SSH-2.0-OpenSSH_7.4\
                                debug1: SSH2_MSG_KEXINIT sent\
                                debug1: SSH2_MSG_KEXINIT received\
                                debug1: kex: algorithm: ecdh-sha2-nistp256\
                                debug1: kex: host key algorithm: ssh-ed25519\
                                debug1: kex: server->client cipher: aes128-ctr MAC: hmac-sha2-256 compression: none\
                                debug1: kex: client->server cipher: aes128-ctr MAC: hmac-sha2-256 compression: none\
                                debug1: kex: ecdh-sha2-nistp256 need=32 dh_need=32\
                                debug1: kex: ecdh-sha2-nistp256 need=32 dh_need=32\
                                debug1: sending SSH2_MSG_KEX_ECDH_INIT\
                                debug1: expecting SSH2_MSG_KEX_ECDH_REPLY"
        _pubkey = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDut20bFm9zUbWFs7GghzTy8CsxR7d6hOaIdKjGUQzIW8hEsJ1DawGmEur0j/M0vz9F8y8FBN3gEASVVnKVInQ30etTEPTzdtTfsGITyxu0Eb0FGwM5jLFwrMOwx35mhv6eDa9pRgku/LO5p2W39Ub5yfh2Xg98SmcJdXDB3Lb4KwE5HT93jLWSogMkyQuke3NKiX8bRE9q2bBzQ1z7DUUvvi1y7ZmqwHtV2PIogPViy2Tvl2aj6C4cosBjS9rxePj+dRg/qAF8OvDPRNr3/VD5NLvPBzWgWGpgsOJnwzX/Vi6/Y4szJXujcumBzz0P1x0XfqOgyhvT2d9wMf/M2ybMI5kjWiQZYUyVPUCSqH0j9K4SX/CCZequsOGMgDTqGCVEhOXAn1wjB4ngby0rOsp6VWT/o0a3b0J7OSbBsHjr2tV7J5gWxlN6Gny/vP8lBm3PxT5Om85FAbMuplsrCl/SPYaB86BnIV6CDeVB/p8a2cQ/ddIW/M8IYBHix/IKc+0= USER_KEY"
        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("/bin/su - opc -c \"/bin/mkdir -p /home/opc/.ssh\"", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chown `id -u opc`:`id -g opc` /home/opc/.ssh\"", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 700 /home/opc/.ssh\"", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e*", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 600*", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chown *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/cat *", aRc=0, aStdout=_pubkey, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 600 *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chown *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keygen -R localhost\"", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keygen -R *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keyscan -H *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/mkdir -p *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 700 *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/echo ssh-rsa *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 600 *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chown *", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/chage *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keygen -R*", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat < /dev/null > /dev/tcp/*", aRc=1, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keyscan -T 30 -H*", aRc=1, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keyscan -vv -T 30 -H *", aRc=1, aStderr=_sshkeyscan_verbose, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keyscan -T 30 -H scaqab10client02vm08", aRc=1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        with patch('exabox.exakms.ExaKms.ExaKms.mGetDefaultKeyAlgorithm', return_value="RSA"):
            self.assertRaises(ExacloudRuntimeError, self.mGetClubox().mConfigurePasswordLessDomU, "opc")

    def test_mConfigurePasswordLessDomU_ssh_keyscan_failure(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mConfigurePasswordLessDomU")
        _user = "opc"
        _sshkeyscan_verbose = "debug1: match: OpenSSH_7.4 pat OpenSSH* compat 0x04000000\
                                # se-dbcs-ash-iqnog2:22 SSH-2.0-OpenSSH_7.4\
                                debug1: Enabling compatibility mode for protocol 2.0\
                                debug1: SSH2_MSG_KEXINIT sent\
                                debug1: SSH2_MSG_KEXINIT received\
                                debug1: kex: algorithm: ecdh-sha2-nistp256\
                                debug1: kex: host key algorithm: ssh-rsa\
                                debug1: kex: server->client cipher: aes128-ctr MAC: hmac-sha2-256 compression: none\
                                debug1: kex: client->server cipher: aes128-ctr MAC: hmac-sha2-256 compression: none\
                                debug1: kex: ecdh-sha2-nistp256 need=32 dh_need=32\
                                debug1: kex: ecdh-sha2-nistp256 need=32 dh_need=32\
                                debug1: sending SSH2_MSG_KEX_ECDH_INIT\
                                debug1: expecting SSH2_MSG_KEX_ECDH_REPLY\
                                debug1: match: OpenSSH_7.4 pat OpenSSH* compat 0x04000000\
                                # se-dbcs-ash-iqnog2:22 SSH-2.0-OpenSSH_7.4\
                                debug1: SSH2_MSG_KEXINIT sent\
                                debug1: SSH2_MSG_KEXINIT received\
                                debug1: kex: algorithm: ecdh-sha2-nistp256\
                                debug1: kex: host key algorithm: ecdsa-sha2-nistp256\
                                debug1: kex: server->client cipher: aes128-ctr MAC: hmac-sha2-256 compression: none\
                                debug1: kex: client->server cipher: aes128-ctr MAC: hmac-sha2-256 compression: none\
                                debug1: kex: ecdh-sha2-nistp256 need=32 dh_need=32\
                                debug1: kex: ecdh-sha2-nistp256 need=32 dh_need=32\
                                debug1: sending SSH2_MSG_KEX_ECDH_INIT\
                                debug1: expecting SSH2_MSG_KEX_ECDH_REPLY\
                                debug1: match: OpenSSH_7.4 pat OpenSSH* compat 0x04000000\
                                # se-dbcs-ash-iqnog2:22 SSH-2.0-OpenSSH_7.4\
                                debug1: SSH2_MSG_KEXINIT sent\
                                debug1: SSH2_MSG_KEXINIT received\
                                debug1: kex: algorithm: ecdh-sha2-nistp256\
                                debug1: kex: host key algorithm: ssh-ed25519\
                                debug1: kex: server->client cipher: aes128-ctr MAC: hmac-sha2-256 compression: none\
                                debug1: kex: client->server cipher: aes128-ctr MAC: hmac-sha2-256 compression: none\
                                debug1: kex: ecdh-sha2-nistp256 need=32 dh_need=32\
                                debug1: kex: ecdh-sha2-nistp256 need=32 dh_need=32\
                                debug1: sending SSH2_MSG_KEX_ECDH_INIT\
                                debug1: expecting SSH2_MSG_KEX_ECDH_REPLY"
        _pubkey = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDut20bFm9zUbWFs7GghzTy8CsxR7d6hOaIdKjGUQzIW8hEsJ1DawGmEur0j/M0vz9F8y8FBN3gEASVVnKVInQ30etTEPTzdtTfsGITyxu0Eb0FGwM5jLFwrMOwx35mhv6eDa9pRgku/LO5p2W39Ub5yfh2Xg98SmcJdXDB3Lb4KwE5HT93jLWSogMkyQuke3NKiX8bRE9q2bBzQ1z7DUUvvi1y7ZmqwHtV2PIogPViy2Tvl2aj6C4cosBjS9rxePj+dRg/qAF8OvDPRNr3/VD5NLvPBzWgWGpgsOJnwzX/Vi6/Y4szJXujcumBzz0P1x0XfqOgyhvT2d9wMf/M2ybMI5kjWiQZYUyVPUCSqH0j9K4SX/CCZequsOGMgDTqGCVEhOXAn1wjB4ngby0rOsp6VWT/o0a3b0J7OSbBsHjr2tV7J5gWxlN6Gny/vP8lBm3PxT5Om85FAbMuplsrCl/SPYaB86BnIV6CDeVB/p8a2cQ/ddIW/M8IYBHix/IKc+0= USER_KEY"
        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("/bin/su - opc -c \"/bin/mkdir -p /home/opc/.ssh\"", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chown `id -u opc`:`id -g opc` /home/opc/.ssh\"", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 700 /home/opc/.ssh\"", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e*", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 600*", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chown *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/cat /home/opc/.ssh/id_rsa.pub", aRc=0, aStdout=_pubkey, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 600 *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chown *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keygen -R localhost\"", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keygen -R *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keyscan -H *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/mkdir -p *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 700 *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/echo ssh-rsa *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 600 *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chown *", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/chage *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keygen -R*", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat < /dev/null > /dev/tcp/*", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keyscan -T 30 -H scaqab10client02vm08.us.oracle.com*", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keyscan -vv -T 30 -H *", aRc=1, aStderr=_sshkeyscan_verbose, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keyscan -T 30 -H scaqab10client02vm08", aRc=1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        with patch('exabox.exakms.ExaKms.ExaKms.mGetDefaultKeyAlgorithm', return_value="RSA"):
            self.assertRaises(ExacloudRuntimeError, self.mGetClubox().mConfigurePasswordLessDomU, "opc")
        
    def test_mConfigurePasswordLessDomU(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mConfigurePasswordLessDomU")
        _user = "opc"
        _sshkeyscan_verbose = "debug1: match: OpenSSH_7.4 pat OpenSSH* compat 0x04000000 \n \
                                # se-dbcs-ash-iqnog2:22 SSH-2.0-OpenSSH_7.4 \n \
                                debug1: Enabling compatibility mode for protocol 2.0 \n \
                                debug1: SSH2_MSG_KEXINIT sent \n \
                                debug1: SSH2_MSG_KEXINIT received \n \
                                debug1: kex: algorithm: ecdh-sha2-nistp256 \n \
                                debug1: kex: host key algorithm: ssh-rsa \n \
                                debug1: kex: server->client cipher: aes128-ctr MAC: hmac-sha2-256 compression: none \n \
                                debug1: kex: client->server cipher: aes128-ctr MAC: hmac-sha2-256 compression: none \n \
                                debug1: kex: ecdh-sha2-nistp256 need=32 dh_need=32 \n \
                                debug1: kex: ecdh-sha2-nistp256 need=32 dh_need=32 \n \
                                debug1: sending SSH2_MSG_KEX_ECDH_INIT \n \
                                debug1: expecting SSH2_MSG_KEX_ECDH_REPLY \n \
                                debug1: match: OpenSSH_7.4 pat OpenSSH* compat 0x04000000 \n \
                                # se-dbcs-ash-iqnog2:22 SSH-2.0-OpenSSH_7.4 \n \
                                debug1: SSH2_MSG_KEXINIT sent \n \
                                debug1: SSH2_MSG_KEXINIT received \n \
                                debug1: kex: algorithm: ecdh-sha2-nistp256 \n \
                                debug1: kex: host key algorithm: ecdsa-sha2-nistp256 \n \
                                debug1: kex: server->client cipher: aes128-ctr MAC: hmac-sha2-256 compression: none \n \
                                debug1: kex: client->server cipher: aes128-ctr MAC: hmac-sha2-256 compression: none \n \
                                debug1: kex: ecdh-sha2-nistp256 need=32 dh_need=32 \n \
                                debug1: kex: ecdh-sha2-nistp256 need=32 dh_need=32 \n \
                                debug1: sending SSH2_MSG_KEX_ECDH_INIT \n \
                                debug1: expecting SSH2_MSG_KEX_ECDH_REPLY \n \
                                debug1: match: OpenSSH_7.4 pat OpenSSH* compat 0x04000000 \n \
                                # se-dbcs-ash-iqnog2:22 SSH-2.0-OpenSSH_7.4\n \
                                debug1: SSH2_MSG_KEXINIT sent \n \
                                debug1: SSH2_MSG_KEXINIT received\n \
                                debug1: kex: algorithm: ecdh-sha2-nistp256\n \
                                debug1: kex: host key algorithm: ssh-ed25519\n \
                                debug1: kex: server->client cipher: aes128-ctr MAC: hmac-sha2-256 compression: none\n \
                                debug1: kex: client->server cipher: aes128-ctr MAC: hmac-sha2-256 compression: none\n \
                                debug1: kex: ecdh-sha2-nistp256 need=32 dh_need=32\n \
                                debug1: kex: ecdh-sha2-nistp256 need=32 dh_need=32\n \
                                debug1: sending SSH2_MSG_KEX_ECDH_INIT\n \
                                debug1: expecting SSH2_MSG_KEX_ECDH_REPLY"
        _pubkey = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDut20bFm9zUbWFs7GghzTy8CsxR7d6hOaIdKjGUQzIW8hEsJ1DawGmEur0j/M0vz9F8y8FBN3gEASVVnKVInQ30etTEPTzdtTfsGITyxu0Eb0FGwM5jLFwrMOwx35mhv6eDa9pRgku/LO5p2W39Ub5yfh2Xg98SmcJdXDB3Lb4KwE5HT93jLWSogMkyQuke3NKiX8bRE9q2bBzQ1z7DUUvvi1y7ZmqwHtV2PIogPViy2Tvl2aj6C4cosBjS9rxePj+dRg/qAF8OvDPRNr3/VD5NLvPBzWgWGpgsOJnwzX/Vi6/Y4szJXujcumBzz0P1x0XfqOgyhvT2d9wMf/M2ybMI5kjWiQZYUyVPUCSqH0j9K4SX/CCZequsOGMgDTqGCVEhOXAn1wjB4ngby0rOsp6VWT/o0a3b0J7OSbBsHjr2tV7J5gWxlN6Gny/vP8lBm3PxT5Om85FAbMuplsrCl/SPYaB86BnIV6CDeVB/p8a2cQ/ddIW/M8IYBHix/IKc+0= USER_KEY"
        _cmds = {
            self.mGetRegexVm():
            [
                [
                    exaMockCommand("/bin/su - opc -c \"/bin/mkdir -p *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chown `id -u opc`:`id -g opc` /home/opc/.ssh\"", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 700 /home/opc/.ssh\"", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e*", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 600*", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chown *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/cat /home/opc/.ssh/id_rsa.pub", aRc=0, aStdout=_pubkey, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 600 *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chown *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keygen -R localhost\"", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keygen -R *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keyscan -H *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/mkdir -p *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 700 *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/echo ssh-rsa *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 600 *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chown *", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/chage *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keygen -R*", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat < /dev/null > /dev/tcp/*", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keyscan -T 30 -H scaqab10client02vm08.us.oracle.com", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keyscan -vv -T 30 -H *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keyscan -T 30 -H scaqab10client02vm08", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/bin/su - opc -c \"/bin/mkdir -p *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chown `id -u opc`:`id -g opc` /home/opc/.ssh\"", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 700 /home/opc/.ssh\"", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e*", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 600*", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chown *", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/cat /home/opc/.ssh/id_rsa.pub", aRc=0, aStdout=_pubkey, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 600 *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chown *", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/chage *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keygen -R localhost\"", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keygen -R *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keyscan -H *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/mkdir -p *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 700 *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/echo ssh-rsa *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chmod 600 *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/chown *", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/chage *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keygen -R*", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat < /dev/null > /dev/tcp/*", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keyscan -T 30 -H scaqab10client01vm08.us.oracle.com", aRc=1, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keyscan -vv -T 30 -H scaqab10client01vm08.us.oracle.com", aRc=0, aPersist=True),
                    exaMockCommand("/bin/su - opc -c \"/bin/ssh-keyscan -T 30 -H scaqab10client01vm08", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        with patch('exabox.exakms.ExaKms.ExaKms.mGetDefaultKeyAlgorithm', return_value="RSA"):
            self.mGetClubox().mConfigurePasswordLessDomU("opc")
    
    def test_mExecuteCmdParallel(self):
        pairs = self.mGetClubox().mReturnDom0DomUPair()

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("date", aStdout="Tue Feb 11 16:31:38 UTC 2025", aRc=0),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)              
        _basecmds = ["date"]
        _toExecute = {}
        for _dom0, _domU in pairs:
            _toExecute[_dom0] = _basecmds
        _result = self.mGetClubox().mExecuteCmdParallel(_toExecute)

        for _host, _status in _result.items():
            _nodeResult = {}
            _nodeResult['hostname'] = _host

            self.assertEqual(_status[0]["rc"],0)
            self.assertGreater(len(_status[0]["stdout"]),0)
            self.assertEqual(len(_status[0]["stderr"]),0)

    def test_mExecuteCmdParallel_EmptyOut_EmptyErr(self):
        pairs = self.mGetClubox().mReturnDom0DomUPair()

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("mockedcommmand", aStdout=None, aStderr=None, aRc=1),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)              
        _basecmds = ["mockedcommmand"]
        _toExecute = {}
        for _dom0, _domU in pairs:
            _toExecute[_dom0] = _basecmds
        _result = self.mGetClubox().mExecuteCmdParallel(_toExecute)

        for _host, _status in _result.items():
            _nodeResult = {}
            _nodeResult['hostname'] = _host

            self.assertEqual(_status[0]["rc"],1)
            self.assertEqual(len(_status[0]["stdout"]),0)
            self.assertEqual(len(_status[0]["stderr"]),0)            

    
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mDoVaultOp')
    def test_mHandlerXsVaultOperation(self, mock_mDoVaultOp):
        ebLogInfo("Running unit test on exaBoxCluCtrl.mHandlerXsVaultOperation")
        _ebox = self.mGetClubox()
        _handler = CommandHandler(_ebox)
        _handler.mHandlerXsVaultOperation()
 
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mRemoveACFS')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mUnMountACFS')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mMountACFS')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mGetACFSSize')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mResizeACFS')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mCreateACFS')
    def test_mHandlerXsAcfsOperations(self, mock_mCreateACFS, mock_mResizeACFS, mock_mGetACFSSize,
                                      mock_mMountACFS, mock_mUnMountACFS, mock_mRemoveACFS):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mHandlerXsAcfsOperations")
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _ebox = self.mGetClubox()
        _handler = CommandHandler(_ebox)

        ACFS_CREATE = """{"acfs_op": "create"} """
        _options.jsonconf = json.loads(ACFS_CREATE)
        _handler.mHandlerXsAcfsOperations(_options)

        ACFS_RESIZE = """{"acfs_op": "resize"} """
        _options.jsonconf = json.loads(ACFS_RESIZE)
        _handler.mHandlerXsAcfsOperations(_options)

        ACFS_GET = """{"acfs_op": "get"} """
        _options.jsonconf = json.loads(ACFS_GET)
        _handler.mHandlerXsAcfsOperations(_options)

        ACFS_MOUNT = """{"acfs_op": "mount"} """
        _options.jsonconf = json.loads(ACFS_MOUNT)
        _handler.mHandlerXsAcfsOperations(_options)

        ACFS_UNMOUNT = """{"acfs_op": "unmount"} """
        _options.jsonconf = json.loads(ACFS_UNMOUNT)
        _handler.mHandlerXsAcfsOperations(_options)

        ACFS_REMOVE = """{"acfs_op": "remove"} """
        _options.jsonconf = json.loads(ACFS_REMOVE)
        _handler.mHandlerXsAcfsOperations(_options)

    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mGetComputeDetails')
    def test_mHandlerXsGet(self, mock_mGetComputeDetails):
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _ebox = self.mGetClubox()
        _handler = CommandHandler(_ebox)
        ebLogInfo("Running unit test on mHandlerXsGet")
        _handler.mHandlerXsGet()

    def test_mHandlerXsPut(self):
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _ebox = self.mGetClubox()
        _handler = CommandHandler(_ebox)
        ebLogInfo("Running unit test on mHandlerXsPut")
        _handler.mHandlerXsPut()

    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetExadataImageFromMap', return_value='ImageVersion not Found')
    def test_mGetMajorityHostVersion_Exception(self, mock_mConnect, mock_mGetExadataImageFromMap):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mGetMajorityHostVersion")

        pattern = "EXACLOUD FATAL EXCEPTION BEGIN"
        with self.assertRaises(ExacloudRuntimeError) as cm:
            _ol_versions = self.mGetClubox().mGetMajorityHostVersion(ExaKmsHostType.DOMU)
            ebLogInfo(f"_ol_versions = {_ol_versions}")
        self.assertIn(pattern, str(cm.exception))

    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetExadataImageFromMap', return_value='24.1.1.0.0.240210')
    def test_mGetMajorityHostVersion_Success_ol8(self, mock_mConnect, mock_mGetExadataImageFromMap):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mGetMajorityHostVersion")

        _ol_versions = self.mGetClubox().mGetMajorityHostVersion(ExaKmsHostType.DOMU)
        self.assertEqual(_ol_versions, 'OL8')

    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mCreateVMbackupNodesConf')
    def test_mHandlerXsVaultOperation(self, mock_mCreateVMbackupNodesConf):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mHandlerXsUpdateNodesConf")
        _ebox = self.mGetClubox()
        _handler = CommandHandler(_ebox)
        _handler.mHandlerXsUpdateNodesConf()

    def mGetNodeModel(self, aHostName):
        return 'X11'

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCopyFile')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateInMemoryXmlConfig')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPatchNetworkSlaves')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNetworkSetupInformation')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mReturnDom0DomUPair', return_value=[('dom0a.oracle.com', 'domUa.oracle.com')])
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsOciEXACC', return_value=True)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.IsHeteroConfig', return_value=(True, {'X11'}))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetNodeModel', return_value='X11')
    def test_mOEDASkipPassProperty(self, mock_mGetNodeModel, mock_IsHeteroConfig, mock_mIsOciEXACC,
                                   mock_mReturnDom0DomUPair, mock_mGetNetworkSetupInformation,
                                   mock_mPatchNetworkSlaves, mock_mUpdateInMemoryXmlConfig, mock_mCopyFile):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mOEDASkipPassProperty")
        _ebox = self.mGetClubox()
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/grep PAAS *", aRc=0, aStdout="PASS" ,aPersist=True),
                    exaMockCommand("/bin/sed *", aRc=0, aStdout="" ,aPersist=True),
                    exaMockCommand("/bin/cp *", aRc=0, aStdout="" ,aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)    

        _xml_save_dir = os.getcwd() + '/' + 'clusters/' + self.mGetClubox().mGetKey() + '/config'
        if not os.path.exists(_xml_save_dir):
           os.makedirs(_xml_save_dir)
        _exacc_log_dir = os.getcwd() + '/' + 'log/exacc_exatest/'
        if not os.path.exists(_exacc_log_dir):
           os.makedirs(_exacc_log_dir)
        _path_config = _xml_save_dir + '/exacc.xml'
        shutil.copyfile(self.mGetClubox().mGetConfigPath(), _path_config)
        ebLogInfo(f"ConfigPath: {self.mGetClubox().mGetConfigPath()}")
        _ebox.mSetPatchConfig(_path_config)

        mock_mGetNetworkSetupInformation.return_value = {
            'client': {'bond_slaves': 'eth0 eth1', 'bond_master': 'bondeth0'},
            'backup': {'bond_slaves': 'eth2', 'bond_master': 'bondeth1'}
        }

        _ebox.mOEDASkipPassProperty(self.mGetClubox().mGetArgsOptions())

        mock_mReturnDom0DomUPair.assert_called_once()
        mock_mGetNetworkSetupInformation.assert_called_once_with(aNetworkType="all", aDom0='dom0a.oracle.com')
        mock_mPatchNetworkSlaves.assert_called_once_with('domUa.oracle.com', ['eth0', 'eth1'], ['eth2'], 'bondeth0', 'bondeth1')

    @patch('exabox.ovm.clucontrol.OedacliCmdMgr')
    def test_mPatchNetworkSlaves_updates_master_attributes(self, mock_oedacli_cmd_mgr):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mPatchNetworkSlaves master wiring")
        _ebox = copy.deepcopy(self.mGetClubox())
        _client_slaves = ['eth0', 'eth1']
        _backup_slaves = ['eth2']
        _updated_xml = '/tmp/oeda/exacloud.conf/patched_network_slaves_uuid.xml'

        mock_manager = mock_oedacli_cmd_mgr.return_value
        with patch.object(_ebox, 'mGetOedaPath', return_value='/tmp/oeda'), \
             patch.object(_ebox, 'mGetUUID', return_value='uuid'), \
             patch.object(_ebox, 'mGetPatchConfig', return_value='/tmp/config.xml'), \
             patch.object(_ebox, 'mSetPatchConfig') as mock_set_patch_config, \
             patch.object(_ebox, 'mExecuteLocal') as mock_execute_local, \
             patch.object(_ebox, 'mGetNetworkSlaves', side_effect=[('id1', 'host1', 'slave1'),
                                                                    ('id2', 'host2', 'slave2')]):
            _ebox.mPatchNetworkSlaves('domU1', _client_slaves, _backup_slaves, 'bondeth0', 'bondeth1')

        mock_oedacli_cmd_mgr.assert_called_once_with('/tmp/oeda/oedacli', '/tmp/oeda/exacloud.conf')
        mock_execute_local.assert_called_once_with(f"/bin/cp /tmp/config.xml {_updated_xml}")
        mock_manager.mUpdateNetworkSlaves.assert_has_calls([
            call(_client_slaves, 'id1', 'host1', 'client', '/tmp/config.xml', _updated_xml, aMaster='bondeth0'),
            call(_backup_slaves, 'id2', 'host2', 'backup', _updated_xml, _updated_xml, aMaster='bondeth1')
        ])
        mock_set_patch_config.assert_called_once_with(_updated_xml)

    def test_IsHeteroConfig_uses_original_dom0_domus(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.IsHeteroConfig original dom0-domU list usage")
        _ebox = copy.deepcopy(self.mGetClubox())
        _orig_pairs = [('dom0-a.oracle.com', 'domU-a.oracle.com'),
                       ('dom0-b.oracle.com', 'domU-b.oracle.com')]

        def _model_map(host):
            return {
                'dom0-a.oracle.com': 'X9',
                'dom0-b.oracle.com': 'X10'
            }[host]

        with patch.object(_ebox, 'mGetOrigDom0sDomUs', return_value=_orig_pairs) as mock_get_orig, \
             patch.object(_ebox, 'mReturnDom0DomUPair', side_effect=AssertionError('mReturnDom0DomUPair should not be used')), \
             patch.object(_ebox, 'mGetNodeModel', side_effect=_model_map) as mock_get_model:
            _is_hetero, _models = _ebox.IsHeteroConfig()

        self.assertTrue(_is_hetero)
        self.assertEqual(_models, {'X9', 'X10'})
        mock_get_orig.assert_called_once()
        self.assertEqual(mock_get_model.call_count, len(_orig_pairs))

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateCloudUser')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetWalletEntry')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPostDBSSHKeyPatching')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPatchVMSSHKey')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsOciEXACC', return_value=True)
    def test_mUpdateExacliPwd(self, mock_mIsOciEXACC, mock_mPatchVMSSHKey, 
                              mock_mPostDBSSHKeyPatching, mock_mSetWalletEntry, mock_mUpdateCloudUser):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mUpdateExacliPwd")
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(DB_INSTALL)

        _cmds = {
            self.mGetRegexCell(): [  
                [
                    exaMockCommand("cellcli -e alter cell remotePwdChangeAllowed=TRUE", aRc=0, aStdout="")
                ]
            ] 
        }
        self.mPrepareMockCommands(_cmds)  

        _ebox.mUpdateExacliPwd(_options)

    def test_mGetAsmSysPasswordForAdbs_success(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mGetAsmSysPasswordForAdbs - success path")
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _wallet_key = "asm_sys_password"

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("ps -ef | grep ocssd | grep grid", aRc=0, aStdout="/u01/app/oracle/product/19.0.0.0/grid/bin/ocssd.bin", aPersist=True),
                ],
                [
                    exaMockCommand("/u01/app/oracle/product/19.0.0.0/grid/bin/mkstore -wrl /u01/app/oracle/admin/cprops/cprops_wallet -viewEntry asm_sys_password | grep asm_sys_password", aRc=0, aStdout="asm_sys_password=secretpass", aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _passwd = _ebox_local.mGetAsmSysPasswordForAdbs(_wallet_key)
        self.assertEqual(_passwd, "secretpass")

        ebLogInfo("Unit test on exaBoxCluCtrl.mGetAsmSysPasswordForAdbs - success path succeeded.")

    def test_mGetAsmSysPasswordForAdbs_failure(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mGetAsmSysPasswordForAdbs - failure path")
        _ebox_local = copy.deepcopy(self.mGetClubox())
        _wallet_key = "asm_sys_password"

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("ps -ef | grep ocssd | grep grid", aRc=0, aStdout="/u01/app/oracle/product/19.0.0.0/grid/bin/ocssd.bin", aPersist=True),
                ],
                [
                    exaMockCommand("/u01/app/oracle/product/19.0.0.0/grid/bin/mkstore -wrl /u01/app/oracle/admin/cprops/cprops_wallet -viewEntry asm_sys_password | grep asm_sys_password", aRc=1, aStdout="", aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _passwd = _ebox_local.mGetAsmSysPasswordForAdbs(_wallet_key)
        self.assertIsNone(_passwd)

        ebLogInfo("Unit test on exaBoxCluCtrl.mGetAsmSysPasswordForAdbs - failure path succeeded.")

    @patch('exabox.ovm.clucontrol.os.symlink')
    @patch('exabox.ovm.clucontrol.os.listdir', return_value=[])
    @patch('exabox.ovm.clucontrol.os.mkdir')
    @patch('exabox.ovm.clucontrol.os.stat', side_effect=FileNotFoundError)
    @patch('exabox.ovm.clucontrol.os.unlink')
    @patch('exabox.ovm.clucontrol.os.path.exists', return_value=True)
    @patch('exabox.ovm.clucontrol.os.readlink')
    @patch('exabox.ovm.clucontrol.os.path.islink', return_value=False)
    @patch('exabox.ovm.clucontrol.os.makedirs')
    def test_mSaveXMLClusterConfiguration_creates_directory(self, mock_makedirs, mock_islink,
                                                            mock_readlink, mock_exists, mock_unlink,
                                                            mock_stat, mock_mkdir, mock_listdir,
                                                            mock_symlink):
        ebLogInfo("")
        ebLogInfo("Running unit test on mSaveXMLClusterConfiguration directory creation")
        _ebox_local = copy.deepcopy(self.mGetClubox())
        config_mock = mock.MagicMock()
        config_mock.mGetConfigXMLData.return_value = "<config/>"
        _ebox_local.mSetConfig(config_mock)
        _ebox_local.mSetRequestObj(None)

        with patch.object(_ebox_local, "mGetRequestObj", return_value=None):
            _ebox_local.mSaveXMLClusterConfiguration()

        target_dir = f"clusters/{_ebox_local.mGetKey()}"

        mock_makedirs.assert_called_once_with(target_dir, exist_ok=True)
        config_mock.mWriteConfig.assert_called_once()

    def test_mCheckPkeysConfig_returns_none_on_kvm(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mCheckPkeysConfig for KVM")

        _ebox_local = copy.deepcopy(self.mGetClubox())
        with patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM", return_value=True):
            self.assertIsNone(_ebox_local.mCheckPkeysConfig({}, False))

        ebLogInfo("Unit test on exaBoxCluCtrl.mCheckPkeysConfig for KVM succeeded.")

    def test_mCheckPkeysConfig_returns_expected_tuple(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mCheckPkeysConfig happy path")

        _ebox_local = copy.deepcopy(self.mGetClubox())
        mock_cluster = MagicMock()
        mock_cluster.mGetCluName.return_value = "MyCluster"
        _ebox_local._exaBoxCluCtrl__clusters = MagicMock()
        _ebox_local._exaBoxCluCtrl__clusters.mGetCluster.return_value = mock_cluster

        aAllGUIDs = {
            0: ["CELL-A"],
            1: ["CELL-B"],
            "localCPS": ["CPS-GUID"],
        }

        mock_node = MagicMock()
        mock_node.mExecuteCmd.side_effect = lambda cmd: (
            (None, mockStream(["sm lid 12 MASTER switch-1 extra\n"]), None)
            if cmd == "getmaster"
            else (None, mockStream([
                "storage_partition = 0x1234 CELL-A CELL-B CPS-GUID;\n",
                "cl_MyCluster = 0x4321;\n"
            ]), None)
        )
        mock_node.mExecuteCmdLog = MagicMock()
        mock_node.mDisconnect = MagicMock()
        mock_node.mConnect = MagicMock()
        mock_node.mGetCmdExitStatus.return_value = 0

        with patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM", return_value=False), \
             patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetPkeysConfig", return_value=("0x1234", "0x4321")), \
             patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mReturnSwitches", return_value=["switch-1"]), \
             patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mReturnCellNodes", return_value={0: None, 1: None}), \
             patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption", return_value=None), \
             patch("exabox.ovm.clucontrol.exaBoxNode", return_value=mock_node), \
             patch("exabox.ovm.clucontrol.get_gcontext"):
            result = _ebox_local.mCheckPkeysConfig(aAllGUIDs, False)

        self.assertEqual(result, ("switch-1", "storage_partition", "0x1234", True))
        ebLogInfo("Unit test on exaBoxCluCtrl.mCheckPkeysConfig happy path succeeded.")
        
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetupNatNfTablesOnDom0v2')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNode')
    def test_mHandlerEnableQinQ(self, mock_mRebootNode, mock_mSetupNatNfTablesOnDom0v2):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxCluCtrl.mUpdateExacliPwd")
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(ENABLE_QINQ_PAYLOAD)

        _cmds = { 
            self.mGetRegexDom0(): [
            [
               exaMockCommand("/usr/sbin/vm_maker --check", aRc=1),
               exaMockCommand("/bin/virsh list --all --name"),
               exaMockCommand("/opt/oracle.SupportTools/switch_to_ovm.sh --qinq")
            ],
            [
                exaMockCommand("/usr/sbin/ip a s stre0 | /bin/grep inet | grep 192.168.64.79", aRc=1),
                exaMockCommand("/usr/sbin/ip a s stre1 | /bin/grep inet | grep 192.168.64.80", aRc=1)
            ],
            [
                exaMockCommand("/bin/virsh list --name"),
                exaMockCommand("/usr/sbin/vm_maker --set --storage-vlan 2900 --ip 192.168.64.79 --netmask 255.255.240.0"),
                exaMockCommand("/usr/sbin/ip a s re*", aRc=0, aStdout="")
            ],
            [
                exaMockCommand("/usr/sbin/ip a s stre0 | /bin/grep inet", aRc=0),
                exaMockCommand("/usr/sbin/ip a s stre1 | /bin/grep inet", aRc=0)
            ]
          ]
        }
        self.mPrepareMockCommands(_cmds)

        _ebox.mExecuteStep("enable_qinq", _options)

    def test_mDispatchCluster_params_storage_type_unknown_defaults_asm(self):
        class StopDispatch(Exception):
            """Sentinel exception to exit mDispatchCluster after setup."""

        clubox = self.mGetClubox()
        options = copy.deepcopy(clubox.mGetArgsOptions())

        original_jsonconf = copy.deepcopy(options.jsonconf)
        original_is_exascale = clubox.mIsExaScale()
        original_xs = clubox.mGetXS()
        original_storage_type = clubox.mGetStorageType()
        had_option_storage = hasattr(options, "storageType")
        original_option_storage = getattr(options, "storageType", None) if had_option_storage else None

        try:
            payload = copy.deepcopy(original_jsonconf)
            payload.pop("storageType", None)
            payload["Params"] = [
                {
                    "PayloadType": "exadata_release",
                    "Operation": "patch_prereq_check",
                    #"storageType": "unsupported",
                }
            ]
            options.jsonconf = payload
            if had_option_storage:
                setattr(options, "storageType", "STANDARD")

            clubox.mSetExaScale(True)
            clubox.mSetXS(True)
            clubox.mSetStorageType("EXASCALE")

            with patch.object(exaBoxCluCtrl, "mIsFedramp", side_effect=StopDispatch):
                with self.assertRaises(StopDispatch):
                    clubox.mDispatchCluster("patch", options)

            self.assertFalse(clubox.mIsExaScale())
            self.assertFalse(clubox.mGetXS())
            self.assertEqual(clubox.mGetStorageType(), "ASM")
        finally:
            clubox.mSetExaScale(original_is_exascale)
            clubox.mSetXS(original_xs)
            clubox.mSetStorageType(original_storage_type)
            options.jsonconf = original_jsonconf
            if had_option_storage:
                setattr(options, "storageType", original_option_storage)
            for key in ("aOptions", "ssh_post_fix"):
                if get_gcontext().mCheckRegEntry(key):
                    get_gcontext().mDelRegEntry(key)

    def test_mDispatchCluster_params_storage_type_sets_exascale(self):
        class StopDispatch(Exception):
            """Sentinel exception to exit mDispatchCluster after flag checks."""

        clubox = self.mGetClubox()
        options = copy.deepcopy(clubox.mGetArgsOptions())

        original_jsonconf = copy.deepcopy(options.jsonconf)
        original_is_exascale = clubox.mIsExaScale()
        original_storage_type = clubox.mGetStorageType()
        had_option_storage = hasattr(options, "storageType")
        original_option_storage = getattr(options, "storageType", None) if had_option_storage else None

        try:
            payload = copy.deepcopy(original_jsonconf)
            payload.pop("storageType", None)
            payload["Params"] = [
                {
                    "PayloadType": "exadata_release",
                    "Operation": "patch_prereq_check",
                    "OperationStyle": "auto",
                    "TargetVersion": "25.2.3.0.0.251020",
                    "BackupMode": "yes",
                    "EnablePlugins": "no",
                    "PluginTypes": "",
                    "FedrampEnabled": "DISABLED",
                    "RequestId": "dcd05e14-1ccf-49d3-bd4e-cc8941177448",
                    "Retry": "no",
                    "isMVM": "no",
                    "storageType": "Exascale",
                    "adb_s": "False",
                    "Clusters": [
                        {
                            "target_env": "production",
                            "rack_name": "exacompute-fra2-d2-ea56e0af-3e12-4596-9ad5-f7e3a4573884-clu01",
                        }
                    ],
                    "TargetType": ["domu"],
                    "AdditionalOptions": [
                        {
                            "serviceType": "EXACS",
                            "FpCrId": "db0eff7a-2bea-4ab4-aae5-5b9e615bb55c",
                            "rackModel": "NOMODEL",
                            "EnvType": "ecs",
                            "CellCountFromCP": 0,
                            "exaunitId": "4208277",
                            "exasplice": "no",
                        }
                    ],
                    "ComputeNodeList": [
                        "fra203316exdd006.fra2xx4xx0211qf.adminfra2.oraclevcn.com",
                        "fra203205exdd003.fra2xx4xx0211qf.adminfra2.oraclevcn.com",
                    ],
                    "InfraPatchPluginMetaData": [],
                    "Dom0domUDetails": {
                        "fra203316exdd006.fra2xx4xx0211qf.adminfra2.oraclevcn.com": {
                            "domuDetails": [
                                {
                                    "customerHostname": "mam2-tqcrt.sub12170906421.vcnexacs.oraclevcn.com",
                                    "domuNatHostname": "fra203316exddu0603.fra2mvm01roce.adminfra2.oraclevcn.com",
                                    "clusterName": "exacompute-fra2-d2-ea56e0af-3e12-4596-9ad5-f7e3a4573884-clu01",
                                    "isSingleNodeVMCluster": "no",
                                    "meterocpus": "4",
                                    "AutonomousDb": "N",
                                    "exaunitId": "4208277",
                                    "clusterStorageType": "EXASCALE",
                                    "cluster_status": "ACTIVE",
                                }
                            ]
                        },
                        "fra203205exdd003.fra2xx4xx0211qf.adminfra2.oraclevcn.com": {
                            "domuDetails": [
                                {
                                    "customerHostname": "mam1-zvniy.sub12170906421.vcnexacs.oraclevcn.com",
                                    "domuNatHostname": "fra203205exddu0301.fra2xx4xx0211qf.adminfra2.oraclevcn.com",
                                    "clusterName": "exacompute-fra2-d2-ea56e0af-3e12-4596-9ad5-f7e3a4573884-clu01",
                                    "isSingleNodeVMCluster": "no",
                                    "meterocpus": "4",
                                    "AutonomousDb": "N",
                                    "exaunitId": "4208277",
                                    "clusterStorageType": "EXASCALE",
                                    "cluster_status": "ACTIVE",
                                }
                            ]
                        },
                    },
                    "DBPatchFile": "/u01/app/oracle/admin/exacloud/PatchPayloads/25.2.3.0.0.251020/DBPatchFile/dbserver.patch.zip",
                    "DomuYumRepository": "/u01/app/oracle/admin/exacloud/PatchPayloads/25.2.3.0.0.251020/DomuYumRepository/exadata_ol8_25.2.3.0.0.251020_Linux-x86-64.zip",
                }
            ]
            options.jsonconf = payload
            if had_option_storage:
                setattr(options, "storageType", "STANDARD")

            clubox.mSetExaScale(False)
            clubox.mSetStorageType("ASM")

            with patch.object(exaBoxCluCtrl, "mIsFedramp", side_effect=StopDispatch):
                with self.assertRaises(StopDispatch):
                    clubox.mDispatchCluster("patch", options)

            self.assertTrue(clubox.mIsExaScale())
            self.assertEqual(clubox.mGetStorageType(), "EXASCALE")
        finally:
            clubox.mSetExaScale(original_is_exascale)
            clubox.mSetStorageType(original_storage_type)
            options.jsonconf = original_jsonconf
            if had_option_storage:
                setattr(options, "storageType", original_option_storage)
            if get_gcontext().mCheckRegEntry("aOptions"):
                get_gcontext().mDelRegEntry("aOptions")
            if get_gcontext().mCheckRegEntry("ssh_post_fix"):
                get_gcontext().mDelRegEntry("ssh_post_fix")
            if get_gcontext().mCheckRegEntry("aOptions"):
                get_gcontext().mDelRegEntry("aOptions")
            if get_gcontext().mCheckRegEntry("ssh_post_fix"):
                get_gcontext().mDelRegEntry("ssh_post_fix")

    def test_mDispatchCluster_params_storage_type_sets_xs(self):
        class StopDispatch(Exception):
            """Sentinel exception to exit mDispatchCluster after flag checks."""

        clubox = self.mGetClubox()
        options = copy.deepcopy(clubox.mGetArgsOptions())

        original_jsonconf = copy.deepcopy(options.jsonconf)
        original_is_exascale = clubox.mIsExaScale()
        original_storage_type = clubox.mGetStorageType()
        original_xs = clubox.mGetXS()
        had_option_storage = hasattr(options, "storageType")
        original_option_storage = getattr(options, "storageType", None) if had_option_storage else None

        try:
            payload = copy.deepcopy(original_jsonconf)
            payload.pop("storageType", None)
            payload["Params"] = [
                {
                    "PayloadType": "exadata_release",
                    "Operation": "patch_prereq_check",
                    "OperationStyle": "auto",
                    "TargetVersion": "25.2.3.0.0.251020",
                    "BackupMode": "yes",
                    "EnablePlugins": "no",
                    "PluginTypes": "",
                    "FedrampEnabled": "DISABLED",
                    "RequestId": "dcd05e14-1ccf-49d3-bd4e-cc8941177448",
                    "Retry": "no",
                    "isMVM": "no",
                    "storageType": "xs",
                    "adb_s": "False",
                    "Clusters": [
                        {
                            "target_env": "production",
                            "rack_name": "exacompute-fra2-d2-ea56e0af-3e12-4596-9ad5-f7e3a4573884-clu01",
                        }
                    ],
                    "TargetType": ["domu"],
                    "AdditionalOptions": [
                        {
                            "serviceType": "EXACS",
                            "FpCrId": "db0eff7a-2bea-4ab4-aae5-5b9e615bb55c",
                            "rackModel": "NOMODEL",
                            "EnvType": "ecs",
                            "CellCountFromCP": 0,
                            "exaunitId": "4208277",
                            "exasplice": "no",
                        }
                    ],
                    "ComputeNodeList": [
                        "fra203316exdd006.fra2xx4xx0211qf.adminfra2.oraclevcn.com",
                        "fra203205exdd003.fra2xx4xx0211qf.adminfra2.oraclevcn.com",
                    ],
                    "InfraPatchPluginMetaData": [],
                    "Dom0domUDetails": {
                        "fra203316exdd006.fra2xx4xx0211qf.adminfra2.oraclevcn.com": {
                            "domuDetails": [
                                {
                                    "customerHostname": "mam2-tqcrt.sub12170906421.vcnexacs.oraclevcn.com",
                                    "domuNatHostname": "fra203316exddu0603.fra2mvm01roce.adminfra2.oraclevcn.com",
                                    "clusterName": "exacompute-fra2-d2-ea56e0af-3e12-4596-9ad5-f7e3a4573884-clu01",
                                    "isSingleNodeVMCluster": "no",
                                    "meterocpus": "4",
                                    "AutonomousDb": "N",
                                    "exaunitId": "4208277",
                                    "clusterStorageType": "XS",
                                    "cluster_status": "ACTIVE",
                                }
                            ]
                        },
                        "fra203205exdd003.fra2xx4xx0211qf.adminfra2.oraclevcn.com": {
                            "domuDetails": [
                                {
                                    "customerHostname": "mam1-zvniy.sub12170906421.vcnexacs.oraclevcn.com",
                                    "domuNatHostname": "fra203205exddu0301.fra2xx4xx0211qf.adminfra2.oraclevcn.com",
                                    "clusterName": "exacompute-fra2-d2-ea56e0af-3e12-4596-9ad5-f7e3a4573884-clu01",
                                    "isSingleNodeVMCluster": "no",
                                    "meterocpus": "4",
                                    "AutonomousDb": "N",
                                    "exaunitId": "4208277",
                                    "clusterStorageType": "XS",
                                    "cluster_status": "ACTIVE",
                                }
                            ]
                        },
                    },
                    "DBPatchFile": "/u01/app/oracle/admin/exacloud/PatchPayloads/25.2.3.0.0.251020/DBPatchFile/dbserver.patch.zip",
                    "DomuYumRepository": "/u01/app/oracle/admin/exacloud/PatchPayloads/25.2.3.0.0.251020/DomuYumRepository/exadata_ol8_25.2.3.0.0.251020_Linux-x86-64.zip",
                }
            ]
            options.jsonconf = payload
            if had_option_storage:
                setattr(options, "storageType", "STANDARD")

            clubox.mSetExaScale(True)
            clubox.mSetXS(False)
            clubox.mSetStorageType("ASM")

            with patch.object(exaBoxCluCtrl, "mIsFedramp", side_effect=StopDispatch):
                with self.assertRaises(StopDispatch):
                    clubox.mDispatchCluster("patch", options)

            self.assertFalse(clubox.mIsExaScale())
            self.assertTrue(clubox.mGetXS())
            self.assertEqual(clubox.mGetStorageType(), "XS")
        finally:
            clubox.mSetExaScale(original_is_exascale)
            clubox.mSetXS(original_xs)
            clubox.mSetStorageType(original_storage_type)
            options.jsonconf = original_jsonconf
            if had_option_storage:
                setattr(options, "storageType", original_option_storage)
            for key in ("aOptions", "ssh_post_fix"):
                if get_gcontext().mCheckRegEntry(key):
                    get_gcontext().mDelRegEntry(key)

    def test_mDispatchCluster_jsonconf_storage_type_sets_exascale(self):
        class StopDispatch(Exception):
            """Sentinel exception to exit mDispatchCluster after flag checks."""

        clubox = self.mGetClubox()
        options = copy.deepcopy(clubox.mGetArgsOptions())

        original_jsonconf = copy.deepcopy(options.jsonconf)
        original_is_exascale = clubox.mIsExaScale()
        original_is_xs = clubox.mGetXS()
        original_storage_type = clubox.mGetStorageType()
        had_option_storage = hasattr(options, "storageType")
        original_option_storage = getattr(options, "storageType", None) if had_option_storage else None

        try:
            payload = copy.deepcopy(original_jsonconf)
            payload["storageType"] = "Exascale"

            rack_conf = payload.get("rack")
            if isinstance(rack_conf, dict):
                rack_conf.pop("storageType", None)

            params = payload.get("Params")
            if isinstance(params, list) and params:
                params[0] = copy.deepcopy(params[0])
                params[0].pop("storageType", None)

            options.jsonconf = payload
            if had_option_storage:
                setattr(options, "storageType", "STANDARD")

            clubox.mSetExaScale(False)
            clubox.mSetXS(False)
            clubox.mSetStorageType("ASM")

            with patch.object(exaBoxCluCtrl, "mIsFedramp", side_effect=StopDispatch):
                with self.assertRaises(StopDispatch):
                    clubox.mDispatchCluster("patch", options)

            self.assertTrue(clubox.mIsExaScale())
            self.assertFalse(clubox.mGetXS())
            self.assertEqual(clubox.mGetStorageType(), "EXASCALE")
        finally:
            clubox.mSetExaScale(original_is_exascale)
            clubox.mSetXS(original_is_xs)
            clubox.mSetStorageType(original_storage_type)
            options.jsonconf = original_jsonconf
            if had_option_storage:
                setattr(options, "storageType", original_option_storage)
            for key in ("aOptions", "ssh_post_fix"):
                if get_gcontext().mCheckRegEntry(key):
                    get_gcontext().mDelRegEntry(key)

    def test_mDispatchCluster_jsonconf_storage_type_sets_xs(self):
        class StopDispatch(Exception):
            """Sentinel exception to exit mDispatchCluster after flag checks."""

        clubox = self.mGetClubox()
        options = copy.deepcopy(clubox.mGetArgsOptions())

        original_jsonconf = copy.deepcopy(options.jsonconf)
        original_is_exascale = clubox.mIsExaScale()
        original_is_xs = clubox.mGetXS()
        original_storage_type = clubox.mGetStorageType()
        had_option_storage = hasattr(options, "storageType")
        original_option_storage = getattr(options, "storageType", None) if had_option_storage else None

        try:
            payload = copy.deepcopy(original_jsonconf)
            payload["storageType"] = "xs"

            rack_conf = payload.get("rack")
            if isinstance(rack_conf, dict):
                rack_conf.pop("storageType", None)

            params = payload.get("Params")
            if isinstance(params, list) and params:
                params[0] = copy.deepcopy(params[0])
                params[0].pop("storageType", None)

            options.jsonconf = payload
            if had_option_storage:
                setattr(options, "storageType", "STANDARD")

            clubox.mSetExaScale(True)
            clubox.mSetXS(False)
            clubox.mSetStorageType("ASM")

            with patch.object(exaBoxCluCtrl, "mIsFedramp", side_effect=StopDispatch):
                with self.assertRaises(StopDispatch):
                    clubox.mDispatchCluster("patch", options)

            self.assertFalse(clubox.mIsExaScale())
            self.assertTrue(clubox.mGetXS())
            self.assertEqual(clubox.mGetStorageType(), "XS")
        finally:
            clubox.mSetExaScale(original_is_exascale)
            clubox.mSetXS(original_is_xs)
            clubox.mSetStorageType(original_storage_type)
            options.jsonconf = original_jsonconf
            if had_option_storage:
                setattr(options, "storageType", original_option_storage)
            for key in ("aOptions", "ssh_post_fix"):
                if get_gcontext().mCheckRegEntry(key):
                    get_gcontext().mDelRegEntry(key)

    def test_mDispatchCluster_rack_storage_type_sets_exascale(self):
        class StopDispatch(Exception):
            """Sentinel exception to exit mDispatchCluster after flag checks."""

        clubox = self.mGetClubox()
        options = copy.deepcopy(clubox.mGetArgsOptions())

        original_jsonconf = copy.deepcopy(options.jsonconf)
        original_is_exascale = clubox.mIsExaScale()
        original_is_xs = clubox.mGetXS()
        original_storage_type = clubox.mGetStorageType()
        had_option_storage = hasattr(options, "storageType")
        original_option_storage = getattr(options, "storageType", None) if had_option_storage else None

        try:
            payload = copy.deepcopy(original_jsonconf)
            payload.pop("storageType", None)

            rack_conf = payload.get("rack")
            if isinstance(rack_conf, dict):
                rack_conf["storageType"] = "Exascale"
            else:
                payload["rack"] = {"storageType": "Exascale"}

            params = payload.get("Params")
            if isinstance(params, list) and params:
                params[0] = copy.deepcopy(params[0])
                params[0].pop("storageType", None)

            options.jsonconf = payload
            if had_option_storage:
                setattr(options, "storageType", "STANDARD")

            clubox.mSetExaScale(False)
            clubox.mSetXS(False)
            clubox.mSetStorageType("ASM")

            with patch.object(exaBoxCluCtrl, "mIsFedramp", side_effect=StopDispatch):
                with self.assertRaises(StopDispatch):
                    clubox.mDispatchCluster("patch", options)

            self.assertTrue(clubox.mIsExaScale())
            self.assertFalse(clubox.mGetXS())
            self.assertEqual(clubox.mGetStorageType(), "EXASCALE")
        finally:
            clubox.mSetExaScale(original_is_exascale)
            clubox.mSetXS(original_is_xs)
            clubox.mSetStorageType(original_storage_type)
            options.jsonconf = original_jsonconf
            if had_option_storage:
                setattr(options, "storageType", original_option_storage)
            for key in ("aOptions", "ssh_post_fix"):
                if get_gcontext().mCheckRegEntry(key):
                    get_gcontext().mDelRegEntry(key)

    def test_mDispatchCluster_rack_storage_type_sets_xs(self):
        class StopDispatch(Exception):
            """Sentinel exception to exit mDispatchCluster after flag checks."""

        clubox = self.mGetClubox()
        options = copy.deepcopy(clubox.mGetArgsOptions())

        original_jsonconf = copy.deepcopy(options.jsonconf)
        original_is_exascale = clubox.mIsExaScale()
        original_is_xs = clubox.mGetXS()
        original_storage_type = clubox.mGetStorageType()
        had_option_storage = hasattr(options, "storageType")
        original_option_storage = getattr(options, "storageType", None) if had_option_storage else None

        try:
            payload = copy.deepcopy(original_jsonconf)
            payload.pop("storageType", None)

            rack_conf = payload.get("rack")
            if isinstance(rack_conf, dict):
                rack_conf["storageType"] = "xs"
            else:
                payload["rack"] = {"storageType": "xs"}

            params = payload.get("Params")
            if isinstance(params, list) and params:
                params[0] = copy.deepcopy(params[0])
                params[0].pop("storageType", None)

            options.jsonconf = payload
            if had_option_storage:
                setattr(options, "storageType", "STANDARD")

            clubox.mSetExaScale(True)
            clubox.mSetXS(False)
            clubox.mSetStorageType("ASM")

            with patch.object(exaBoxCluCtrl, "mIsFedramp", side_effect=StopDispatch):
                with self.assertRaises(StopDispatch):
                    clubox.mDispatchCluster("patch", options)

            self.assertFalse(clubox.mIsExaScale())
            self.assertTrue(clubox.mGetXS())
            self.assertEqual(clubox.mGetStorageType(), "XS")
        finally:
            clubox.mSetExaScale(original_is_exascale)
            clubox.mSetXS(original_is_xs)
            clubox.mSetStorageType(original_storage_type)
            options.jsonconf = original_jsonconf
            if had_option_storage:
                setattr(options, "storageType", original_option_storage)
            for key in ("aOptions", "ssh_post_fix"):
                if get_gcontext().mCheckRegEntry(key):
                    get_gcontext().mDelRegEntry(key)

    def test_mDispatchCluster_options_storage_type_sets_exascale(self):
        class StopDispatch(Exception):
            """Sentinel exception to exit mDispatchCluster after flag checks."""

        clubox = self.mGetClubox()
        options = copy.deepcopy(clubox.mGetArgsOptions())

        original_jsonconf = copy.deepcopy(options.jsonconf)
        original_is_exascale = clubox.mIsExaScale()
        original_is_xs = clubox.mGetXS()
        original_storage_type = clubox.mGetStorageType()
        had_option_storage = hasattr(options, "storageType")
        original_option_storage = getattr(options, "storageType", None) if had_option_storage else None

        try:
            payload = copy.deepcopy(original_jsonconf)
            payload.pop("storageType", None)

            rack_conf = payload.get("rack")
            if isinstance(rack_conf, dict):
                rack_conf.pop("storageType", None)

            params = payload.get("Params")
            if isinstance(params, list) and params:
                params[0] = copy.deepcopy(params[0])
                params[0].pop("storageType", None)

            options.jsonconf = payload

            setattr(options, "storageType", "Exascale")

            clubox.mSetExaScale(False)
            clubox.mSetXS(False)
            clubox.mSetStorageType("ASM")

            with patch.object(exaBoxCluCtrl, "mIsFedramp", side_effect=StopDispatch):
                with self.assertRaises(StopDispatch):
                    clubox.mDispatchCluster("patch", options)

            self.assertTrue(clubox.mIsExaScale())
            self.assertFalse(clubox.mGetXS())
            self.assertEqual(clubox.mGetStorageType(), "EXASCALE")
        finally:
            clubox.mSetExaScale(original_is_exascale)
            clubox.mSetXS(original_is_xs)
            clubox.mSetStorageType(original_storage_type)
            options.jsonconf = original_jsonconf
            if had_option_storage:
                setattr(options, "storageType", original_option_storage)
            else:
                delattr(options, "storageType")
            for key in ("aOptions", "ssh_post_fix"):
                if get_gcontext().mCheckRegEntry(key):
                    get_gcontext().mDelRegEntry(key)

    def test_mDispatchCluster_options_storage_type_sets_xs(self):
        class StopDispatch(Exception):
            """Sentinel exception to exit mDispatchCluster after flag checks."""

        clubox = self.mGetClubox()
        options = copy.deepcopy(clubox.mGetArgsOptions())

        original_jsonconf = copy.deepcopy(options.jsonconf)
        original_is_exascale = clubox.mIsExaScale()
        original_is_xs = clubox.mGetXS()
        original_storage_type = clubox.mGetStorageType()
        had_option_storage = hasattr(options, "storageType")
        original_option_storage = getattr(options, "storageType", None) if had_option_storage else None

        try:
            payload = copy.deepcopy(original_jsonconf)
            payload.pop("storageType", None)

            rack_conf = payload.get("rack")
            if isinstance(rack_conf, dict):
                rack_conf.pop("storageType", None)

            params = payload.get("Params")
            if isinstance(params, list) and params:
                params[0] = copy.deepcopy(params[0])
                params[0].pop("storageType", None)

            options.jsonconf = payload

            setattr(options, "storageType", " xs ")

            clubox.mSetExaScale(True)
            clubox.mSetXS(False)
            clubox.mSetStorageType("ASM")

            with patch.object(exaBoxCluCtrl, "mIsFedramp", side_effect=StopDispatch):
                with self.assertRaises(StopDispatch):
                    clubox.mDispatchCluster("patch", options)

            self.assertFalse(clubox.mIsExaScale())
            self.assertTrue(clubox.mGetXS())
            self.assertEqual(clubox.mGetStorageType(), "XS")
        finally:
            clubox.mSetExaScale(original_is_exascale)
            clubox.mSetXS(original_is_xs)
            clubox.mSetStorageType(original_storage_type)
            options.jsonconf = original_jsonconf
            if had_option_storage:
                setattr(options, "storageType", original_option_storage)
            else:
                delattr(options, "storageType")
            for key in ("aOptions", "ssh_post_fix"):
                if get_gcontext().mCheckRegEntry(key):
                    get_gcontext().mDelRegEntry(key)

    def test_mDispatchCluster_patch_handles_timeout_error_with_failure_code(self):
        clubox = copy.deepcopy(self.mGetClubox())
        options = copy.deepcopy(clubox.mGetArgsOptions())
        options.jsonconf = {}
        clubox.mSetOptions(options)
        setattr(clubox, "_exaBoxCluCtrl__skip_dom0_validation", False)

        command = "mock_patch_cmd"

        def mock_cmd_options(a_cmd, a_options):
            if a_cmd != command:
                return False
            return set(a_options).issubset({"patch", "check_shared_env"})

        db_instance = MagicMock()
        db_instance.mCheckRegEntry.return_value = False

        clubox.mRefreshExaKmsSingleton = MagicMock()
        clubox.mCheckSharedEnvironment = MagicMock(side_effect=TimeoutError("[Errno 110] Connection timed out"))
        clubox.mHandlerDeleteOndiskKeys = MagicMock()
        clubox.mSyncKeysOverNetworkSend = MagicMock()
        clubox.mSyncKVDBOverNetworkSend = MagicMock()
        clubox.mCleanUpExaKmsSingleton = MagicMock()
        clubox.mUIOedaCliXmlCleanUp = MagicMock()
        clubox.mCleanKeysOedaFolder = MagicMock()
        clubox.mHandlerRestartRemoteEc = MagicMock()
        clubox.mCalculateSkipXmlPatching = MagicMock()
        clubox.mParseXMLConfig = MagicMock()
        clubox.mGenerateExacloudXML = MagicMock()
        clubox.mSetEnvTypeInConfiguration = MagicMock()
        clubox.mExecuteCmd = MagicMock(return_value=(None, None, None))
        clubox.mExecuteCmdLog = MagicMock(return_value=(None, None, None))
        clubox.mExecuteLocal = MagicMock(return_value=(None, None, None, None))
        clubox.mCreateCluster = MagicMock(return_value=0)
        clubox.mExecuteOEDAStep = MagicMock(return_value=0)
        clubox.mIsExaScale = MagicMock(return_value=False)
        clubox.mIsNoOeda = MagicMock(return_value=True)

        with patch("exabox.ovm.clucontrol.ebCluCmdCheckOptions", side_effect=mock_cmd_options), \
            patch("exabox.ovm.clucontrol.ebGetDefaultDB", return_value=db_instance), \
            patch.object(exaBoxCluCtrl, "mCalculateNoOeda"):
            rc = clubox.mDispatchCluster(command, options)

        self.assertEqual(rc, PATCHING_CONNECT_FAILED)
        clubox.mCheckSharedEnvironment.assert_called_once()
        clubox.mRefreshExaKmsSingleton.assert_called_once()

    def test_mDispatchCluster_patch_handles_ssh_error_with_failure_code(self):
        clubox = copy.deepcopy(self.mGetClubox())
        options = copy.deepcopy(clubox.mGetArgsOptions())
        options.jsonconf = {}
        clubox.mSetOptions(options)
        setattr(clubox, "_exaBoxCluCtrl__skip_dom0_validation", False)

        command = "mock_patch_cmd"

        def mock_cmd_options(a_cmd, a_options):
            if a_cmd != command:
                return False
            return set(a_options).issubset({"patch", "check_shared_env"})

        db_instance = MagicMock()
        db_instance.mCheckRegEntry.return_value = False

        clubox.mRefreshExaKmsSingleton = MagicMock()
        clubox.mCheckSharedEnvironment = MagicMock(side_effect=SSHException("TimeoutError: [Errno 110] Connection timed out"))
        clubox.mHandlerDeleteOndiskKeys = MagicMock()
        clubox.mSyncKeysOverNetworkSend = MagicMock()
        clubox.mSyncKVDBOverNetworkSend = MagicMock()
        clubox.mCleanUpExaKmsSingleton = MagicMock()
        clubox.mUIOedaCliXmlCleanUp = MagicMock()
        clubox.mCleanKeysOedaFolder = MagicMock()
        clubox.mHandlerRestartRemoteEc = MagicMock()
        clubox.mCalculateSkipXmlPatching = MagicMock()
        clubox.mParseXMLConfig = MagicMock()
        clubox.mGenerateExacloudXML = MagicMock()
        clubox.mSetEnvTypeInConfiguration = MagicMock()
        clubox.mExecuteCmd = MagicMock(return_value=(None, None, None))
        clubox.mExecuteCmdLog = MagicMock(return_value=(None, None, None))
        clubox.mExecuteLocal = MagicMock(return_value=(None, None, None, None))
        clubox.mCreateCluster = MagicMock(return_value=0)
        clubox.mExecuteOEDAStep = MagicMock(return_value=0)
        clubox.mIsExaScale = MagicMock(return_value=False)
        clubox.mIsNoOeda = MagicMock(return_value=True)

        with patch("exabox.ovm.clucontrol.ebCluCmdCheckOptions", side_effect=mock_cmd_options), \
            patch("exabox.ovm.clucontrol.ebGetDefaultDB", return_value=db_instance), \
            patch.object(exaBoxCluCtrl, "mCalculateNoOeda"):
            rc = clubox.mDispatchCluster(command, options)

        self.assertEqual(rc, PATCHING_NODE_SSH_CHECK_FAILED)
        clubox.mCheckSharedEnvironment.assert_called_once()
        clubox.mRefreshExaKmsSingleton.assert_called_once()

    def test_mDispatchCluster_patch_raise_other_exception(self):
        clubox = copy.deepcopy(self.mGetClubox())
        options = copy.deepcopy(clubox.mGetArgsOptions())
        options.jsonconf = {}
        clubox.mSetOptions(options)
        setattr(clubox, "_exaBoxCluCtrl__skip_dom0_validation", False)

        command = "mock_patch_cmd"

        def mock_cmd_options(a_cmd, a_options):
            if a_cmd != command:
                return False
            return set(a_options).issubset({"patch", "check_shared_env"})

        db_instance = MagicMock()
        db_instance.mCheckRegEntry.return_value = False

        clubox.mRefreshExaKmsSingleton = MagicMock()
        clubox.mCheckSharedEnvironment = MagicMock(side_effect=Exception("MockException"))
        clubox.mHandlerDeleteOndiskKeys = MagicMock()
        clubox.mSyncKeysOverNetworkSend = MagicMock()
        clubox.mSyncKVDBOverNetworkSend = MagicMock()
        clubox.mCleanUpExaKmsSingleton = MagicMock()
        clubox.mUIOedaCliXmlCleanUp = MagicMock()
        clubox.mCleanKeysOedaFolder = MagicMock()
        clubox.mHandlerRestartRemoteEc = MagicMock()
        clubox.mCalculateSkipXmlPatching = MagicMock()
        clubox.mParseXMLConfig = MagicMock()
        clubox.mGenerateExacloudXML = MagicMock()
        clubox.mSetEnvTypeInConfiguration = MagicMock()
        clubox.mExecuteCmd = MagicMock(return_value=(None, None, None))
        clubox.mExecuteCmdLog = MagicMock(return_value=(None, None, None))
        clubox.mExecuteLocal = MagicMock(return_value=(None, None, None, None))
        clubox.mCreateCluster = MagicMock(return_value=0)
        clubox.mExecuteOEDAStep = MagicMock(return_value=0)
        clubox.mIsExaScale = MagicMock(return_value=False)
        clubox.mIsNoOeda = MagicMock(return_value=True)

        with patch("exabox.ovm.clucontrol.ebCluCmdCheckOptions", side_effect=mock_cmd_options), \
            patch("exabox.ovm.clucontrol.ebGetDefaultDB", return_value=db_instance), \
            patch.object(exaBoxCluCtrl, "mCalculateNoOeda"):
            with self.assertRaises(Exception):
                clubox.mDispatchCluster(command, options)

        clubox.mCheckSharedEnvironment.assert_called_once()
        clubox.mRefreshExaKmsSingleton.assert_called_once()
    
    @patch('exabox.ovm.clucontrol.time.sleep', return_value=None)
    def test_mCleanUpStaleVm(self, _mock_sleep):
        ctrl = self.mGetClubox()
        ctrl.mSetExabm(True)
        ctrl.mSetDebug(False)

        dom0_host = 'mock1adm1'
        domU = 'mock-domu'
        hypervisor_service = 'libvirtd'
        chkvm_cmd = '/usr/sbin/vm_maker --list-domains | /bin/grep "^{}("'.format(domU)

        mock_cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(re.escape(f"systemctl is-active {hypervisor_service}"), aRc=0, aStdout="active", aPersist=True),
                    exaMockCommand(re.escape(f"/usr/sbin/vm_maker --stop-domain {domU} --force"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape(f"/opt/exadata_ovm/vm_maker --remove-domain {domU} --force"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape(f"/usr/bin/virsh undefine {domU}"), aRc=0, aPersist=True),
                    exaMockCommand(re.escape(chkvm_cmd), aRc=1, aPersist=True),
                    exaMockCommand(re.escape('losetup -a'), aRc=0, aStdout='', aPersist=True),
                    exaMockCommand(re.escape('ls /EXAVMIMAGES/GuestImages/{}'.format(domU)), aRc=0, aPersist=True),
                    exaMockCommand(re.escape(f"rm -rf /EXAVMIMAGES/GuestImages/{domU}"), aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mock_cmds)

        def _check_config(option, *args, **kwargs):
            if option == 'delete_vmbackup':
                return None
            if option == 'force_delete_vm':
                return 'False'
            return None

        with (
            patch.object(ctrl, 'mIsKVM', return_value=True),
            patch.object(ctrl, 'mAcquireRemoteLock'),
            patch.object(ctrl, 'mReleaseRemoteLock'),
            patch.object(ctrl, 'mStartDom0Service'),
            patch.object(ctrl, 'mEnableDom0Service'),
            patch.object(ctrl, 'mCleanUpBackupsQemu'),
            patch.object(ctrl, 'mGetHostsByTypeAndOLVersion', return_value=[]),
            patch.object(ctrl, 'mCheckConfigOption', side_effect=_check_config),
        ):
            ctrl.mCleanUpStaleVm(False, [(dom0_host, domU)])

if __name__ == "__main__":
    unittest.main(warnings='ignore')
