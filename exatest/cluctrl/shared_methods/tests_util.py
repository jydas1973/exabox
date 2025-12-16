#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/shared_methods/tests_util.py /main/18 2025/09/23 15:37:41 bhpati Exp $
#
# tests_util.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_util.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    bhpati      09/11/25 - Bug 38276080 - delete-service is not removing vm's
#                           from the host if hypervisor service is down
#    abflores    05/01/25 - Bug 37862473: EXACLOUD SECRET CLEANER ISSUE |
#                           CLUCONTROL CONTAINS AUTHORIZATION TOKENS
#    aararora    03/13/25 - Bug 37672091: Set global properties in
#                           es.properties oeda file
#    aararora    02/04/25 - Bug 37495011: Exclude lines beginning with comment
#    ririgoye    06/18/24 - Bug 36746656 - PYTHON 3.11 - EXACLOUD NEEDS TO
#                           UPDATE DEPRECATED/OLDER IMPORTS DYNAMICALLY
#    jfsaldan    03/21/24 - Bug 36004327 - EXACS: PROVISIONING FAILED WITH
#                           EXACLOUD ERROR CODE: 276 EXACLOUD : TIMEOUT WHILE
#                           WAITING FOR ASM TO BE RUNNING. ABORTING
#    rajsag      01/09/24 - 35946483- exacc - support fs encryption at rest -
#                           exacloud create vm cluster encrypted
#    hcheon      08/30/23 - 35197827 Use OCI instance metadata v2
#    aypaul      09/16/21 - Creation
#
import io
import json
import unittest
import re
from unittest import mock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.utils.clu_utils import ebCluUtils
import glob

from base64 import b64decode, b64encode

try:
    from base64 import decodestring
except ImportError:
    from base64 import b64decode as decodestring

import os
import warnings
from unittest.mock import patch, MagicMock

OEDA_FAIL = False
OEDA_SUCC = True

OEDA_IGNORE_ERROR_LOG = """2021-09-12 20:45:14,831 [INFO][785-thread-5][        OcmdException:74] Error: Command [/opt/oracle.SupportTools/exadataAIDE -u] run on node scas07celadm04.us.oracle.com as user root did not execute successfully...
2021-09-12 20:45:15,472 [INFO][785-thread-5][            ZipUtils:205] Errors occurred. Send /scratch/aime1/ecra_installs/etfdlq09121647/mw_home/user_projects/domains/exacloud/oeda/requests/ccac3756-1406-11ec-b545-020017093317/WorkDir/Diag-210912_204514.zip to Oracle to receive assistance.
"""

OEDA_ERROR_LOG = """2021-09-12 20:45:15,041 [FINE][785-thread-5][            ZipUtils:201] Creating zip file /scratch/aime1/ecra_installs/etfdlq09121647/mw_home/user_projects/domains/exacloud/oeda/requests/ccac3756-1406-11ec-b545-020017093317/WorkDir/Diag-210912_204514 with 307 files
2021-09-12 20:45:15,472 [INFO][785-thread-5][            ZipUtils:205] Errors occurred. Send /scratch/aime1/ecra_installs/etfdlq09121647/mw_home/user_projects/domains/exacloud/oeda/requests/ccac3756-1406-11ec-b545-020017093317/WorkDir/Diag-210912_204514.zip to Oracle to receive assistance.
"""

OEDA_SKIP_LOG = """2021-09-12 20:45:14,829 [FINE][785-thread-5][        CommonUtils:1892]  ORA-15063: ASM discovered an insufficient number of disks for diskgroup
2021-09-12 20:45:15,041 [FINE][785-thread-5][            ZipUtils:201] Creating zip file /scratch/aime1/ecra_installs/etfdlq09121647/mw_home/user_projects/domains/exacloud/oeda/requests/ccac3756-1406-11ec-b545-020017093317/WorkDir/Diag-210912_204514 with 307 files
2021-09-12 20:45:15,472 [INFO][785-thread-5][            ZipUtils:205] Errors occurred. Send /scratch/aime1/ecra_installs/etfdlq09121647/mw_home/user_projects/domains/exacloud/oeda/requests/ccac3756-1406-11ec-b545-020017093317/WorkDir/Diag-210912_204514.zip to Oracle to receive assistance.
"""

PING_OUTPUT = """PING scaqab10adm01.us.oracle.com (10.252.161.82) 56(84) bytes of data.
64 bytes from scaqab10adm01.us.oracle.com (10.252.161.82): icmp_seq=1 ttl=49 time=12.2 ms

--- scaqab10adm01.us.oracle.com ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 12.221/12.221/12.221/0.000 ms
"""

class ebTestClucontrolUtil(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestClucontrolUtil, self).setUpClass(True, True)
        warnings.filterwarnings("ignore")
    
    def test_mParseOEDALog(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaboxCluCtrl.mParseOEDALog")

        _exabox_cluctrl_obj = self.mGetClubox()
        self.mGetContext().mSetConfigOption("ssh_diagnostic", "False")
        _cmd_op = OEDA_IGNORE_ERROR_LOG.split("\n"),None
        self.assertEqual(_exabox_cluctrl_obj.mParseOEDALog(_cmd_op,"ESTP_POSTGI_NID",True),OEDA_SUCC)
        _cmd_op = OEDA_ERROR_LOG.split("\n"),None
        self.assertEqual(_exabox_cluctrl_obj.mParseOEDALog(_cmd_op,"ESTP_POSTGI_NID",True),OEDA_FAIL)
        _cmd_op = OEDA_SKIP_LOG.split("\n"),None
        self.assertEqual(_exabox_cluctrl_obj.mParseOEDALog(_cmd_op,"ESTP_POSTGI_NID",True),OEDA_SUCC)

    def test_mCheckImagesVersion(self):
        ebLogInfo("Running unit test on exaboxCluCtrl.mCheckImagesVersion")

        _out1 = "/dev/mapper/VGExaDbDisk.grid19.0.0.0.211019.img-LVDBDisk on /u01/app/19.0.0.0/grid type xfs (rw,relatime,attr2,inode64,noquota)"
        _cmds = {
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand("mount | grep '/u01/app.*/grid.*'", aRc=0, aStdout=_out1 ,aPersist=True),
                        exaMockCommand("cat /u01/app/19.0.0.0/grid/.bpl", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("ls /u01/app/19.0.0.0/grid/.patch_storage/NApply", aRc=0, aStdout="2019-04-18_07-35-05AM", aPersist=True),
                        exaMockCommand("imageinfo | grep 'Image version'", aRc=0, aStdout="Image version: 21.2.6.0.0.211220", aPersist=True)
                    ]
                ]
                }

        self.mPrepareMockCommands(_cmds)
        _clu_obj = self.mGetClubox()
        _clu_obj.mCheckImagesVersion()
    
    def test_mClusterCheckInfo(self):
        ebLogInfo("Running unit test on exaboxCluCtrl.mClusterCheckInfo")

        _cmds = {
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand(re.escape('grep "^PermitRootLogin without-password" /etc/ssh/sshd_config &> /dev/null'), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape('grep "^PasswordAuthentication no" /etc/ssh/sshd_config &> /dev/null'), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape('grep "^root:" /etc/shadow'), aRc=0, aStdout="", aPersist=True)
                    ]
                ],
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand(re.escape("ping *"), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape('grep "^PasswordAuthentication no" /etc/ssh/sshd_config &> /dev/null'), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape('grep "^root:" /etc/shadow'), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape('grep "^PermitRootLogin without-password" /etc/ssh/sshd_config &> /dev/null'), aRc=0, aStdout="", aPersist=True)
                    ]
                ],
                self.mGetRegexCell():
                [
                    [
                        exaMockCommand(re.escape("ping *"), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape('grep "^PasswordAuthentication no" /etc/ssh/sshd_config &> /dev/null'), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape('grep "^root:" /etc/shadow'), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape('grep "^PermitRootLogin without-password" /etc/ssh/sshd_config &> /dev/null'), aRc=0, aStdout="", aPersist=True)
                    ]
                ],
                self.mGetRegexSwitch():
                [
                    [
                        exaMockCommand(re.escape('grep "^PasswordAuthentication no" /etc/ssh/sshd_config &> /dev/null'), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape('grep "^root:" /etc/shadow'), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand('smpartition list active no-page | head -10', aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape('grep "^PermitRootLogin without-password" /etc/ssh/sshd_config &> /dev/null'), aRc=0, aStdout="", aPersist=True)
                    ]
                ],
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/ping", aRc=0, aStdout=PING_OUTPUT, aPersist=True),
                        exaMockCommand('/bin/ssh-keygen', aRc=0, aStdout="", aPersist=True)
                    ]
                ]
                }
        self.mPrepareMockCommands(_cmds)
        _clu_obj = self.mGetClubox()
        _clu_obj.mClusterCheckInfo()
    
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mParseOEDALog", return_value=1)
    def test_mExecuteApplySecurityFixes(self, mock_mParseOEDALog):  
        ebLogInfo("Running unit test on exaboxCluCtrl.mExecuteApplySecurityFixes")                
                       
        _sqlnetfile = "/u02/app/oracle/product/19.0.0.0/dbhome_2/network/admin/sqlnet.ora"           
        _dbcmd = 'export ORACLE_HOME=/u02/app/oracle/product/19.0.0.0/dbhome_2; /u02/app/oracle/product/19.0.0.0/dbhome_2/bin/srvctl status database -d sdb19 | grep -c "is running" | grep -w 2'
        _cmds = {                                                                                                                                                            
                self.mGetRegexVm():                                                                                                                                          
                [                                                                                                                                                            
                    [                                                                                                                                                        
                        exaMockCommand('cat /etc/oratab | grep -e "sdb19"', aRc=0, aStdout="sdb19:/u02/app/oracle/product/19.0.0.0/dbhome_2:Y" ,aPersist=True),              
                        exaMockCommand("cat /etc/oratab", aRc=0, aStdout="sdb19:/u02/app/oracle/product/19.0.0.0/dbhome_2" ,aPersist=True),                                  
                        exaMockCommand(f"cp -f {_sqlnetfile} {_sqlnetfile}.orig", aRc=0, aStdout="", aPersist=True)                                                          
                    ],                                                                                                                                                       
                    [             
                        exaMockCommand(re.escape("cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),                                                                                                                                        
                        exaMockCommand(f"cp -f {_sqlnetfile} {_sqlnetfile}.orig", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl check cluster | grep -c online | grep -w 3", aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'"), aRc=0, aStdout="/u01/app/19.0.0.0/grid" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="19.0.0.0.0" ,aPersist=True),
                        exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/grid" ,aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl check cluster | grep -c online | grep -w 3", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand('/u01/app/19.0.0.0/grid/bin/crsctl query css votedisk | grep "Located 5 voting disk"', aRc=0, aStdout="", aPersist=True),
                    ],
                    [
                        exaMockCommand('/u01/app/19.0.0.0/grid/bin/crsctl query css votedisk | grep "Located 5 voting disk"', aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape("cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"),  aRc=0, aStdout="/u01/app/19.0.0.0/grid", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl check cluster | grep -c online | grep -w 3", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl status asm | grep 'ASM is running on'", aRc=0, aStdout="ASM is running on c3709n10c2,c3716n2c2", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl status filesystem | grep 'is mounted on nodes'", aRc=0, aStdout="ACFS file system /acfs01 is mounted on nodes c3709n10c2,c3709n5c2", aPersist=True)
            
                    ],
                    [
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl check cluster | grep -c online | grep -w 3", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("tac /etc/oratab | grep -v ASM", aRc=0, aStdout="sdb19:/u02/app/oracle/product/19.0.0.0/dbhome_2:Y", aPersist=True),
                        exaMockCommand(re.escape("cat /etc/oratab | grep '^sdb19.*' | cut -f 2 -d ':'"), aRc=0, aStdout="/u02/app/oracle/product/19.0.0.0/dbhome_2", aPersist=True),
                        exaMockCommand(re.escape("cat /etc/oratab | grep '^+ASM.*' | cut -f 2 -d ':'"),  aRc=0, aStdout="/u01/app/19.0.0.0/grid", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl  status asm", aRc=0, aStdout="ASM is running on c3709n10c2,c3716n2c2", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl status asm | grep 'ASM is running on'", aRc=0, aStdout="ASM is running on scaqab10client01vm08,scaqab10client02vm08", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl  status filesystem", aRc=0, aStdout="ACFS file system /acfs01 is mounted on nodes scaqab10client01vm08,scaqab10client02vm08", aPersist=True),
                        exaMockCommand("/u01/app/19.0.0.0/grid/bin/srvctl status filesystem | grep 'is mounted on nodes'", aRc=0, aStdout="ACFS file system /acfs01 is mounted on nodes scaqab10client01vm08,scaqab10client02vm08", aPersist=True),
                        exaMockCommand(_dbcmd, aRc=0, aStdout="2", aPersist=True)
                    ],
                    [
                        exaMockCommand("/u02/app/oracle/product/19.0.0.0/dbhome_2/bin/srvctl  status asm", aRc=0, aStdout="ASM is running on c3709n10c2,c3716n2c2", aPersist=True),
                        exaMockCommand("/u02/app/oracle/product/19.0.0.0/dbhome_2/bin/srvctl status asm | grep 'ASM is running on'", aRc=0, aStdout="ASM is running on scaqab10client01vm08,scaqab10client02vm08", aPersist=True),
                        exaMockCommand("/u02/app/oracle/product/19.0.0.0/dbhome_2/bin/srvctl  status filesystem", aRc=0, aStdout="ACFS file system /acfs01 is mounted on nodes scaqab10client01vm08,scaqab10client02vm08", aPersist=True),
                        exaMockCommand("/u02/app/oracle/product/19.0.0.0/dbhome_2/bin/srvctl status filesystem | grep 'is mounted on nodes'", aRc=0, aStdout="ACFS file system /acfs01 is mounted on nodes scaqab10client01vm08,scaqab10client02vm08", aPersist=True),
                        exaMockCommand("cat /etc/oratab | grep '^sdb19.*' | cut -f 2 -d ':'", aRc=0, aStdout="/u02/app/oracle/product/19.0.0.0/dbhome_2", aPersist=True), 

                    ],
                    [
                        exaMockCommand("tac /etc/oratab | grep -v ASM", aRc=0, aStdout="sdb19:/u02/app/oracle/product/19.0.0.0/dbhome_2:Y", aPersist=True),                                          
                        exaMockCommand("cat /etc/oratab | grep '^sdb19.*' | cut -f 2 -d ':'", aRc=0, aStdout="/u02/app/oracle/product/19.0.0.0/dbhome_2", aPersist=True), 
                        exaMockCommand('export ORACLE_HOME=/u02/app/oracle/product/19.0.0.0/dbhome_2; /u02/app/oracle/product/19.0.0.0/dbhome_2/bin/srvctl status database -d sdb19 | grep -c "is running" | grep -w 2', aRc=0, aStdout="Instance sdb191 is running on node scaqab10client01vm08", aPersist=True)
                    ]
                ],
                self.mGetRegexLocal():  
                [
                    [
                        exaMockCommand("/bin/bash install.sh -cf ", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ]
                }      
                       
        self.mPrepareMockCommands(_cmds)           
        _clu_obj = self.mGetClubox()            
        _clu_obj.mExecuteApplySecurityFixes(_clu_obj.mGetOedaPath(), "19000")    

    def test_mDomUCSSMisscountHandler(self): 
        _cmds = {
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand("`sed -n 's#^oracle_home=\(/.*\)$#\1/bin/crsctl get css misscount#p' /var/opt/oracle/creg/grid/grid.ini` | grep -o '[0-9]*' | tail -1", aRc=0, aStdout="30" ,aPersist=True)
                    ]
                ]
                }

        self.mPrepareMockCommands(_cmds)
        _clu_obj = self.mGetClubox()
        _clu_obj.mDomUCSSMisscountHandler()

    def test_mUpdateAllClusterHostsKeys(self):
        _out1 = """PING sea201608exddu0105.sea2xx2xx0051qf.adminsea2.oraclevcn.com (10.0.130.61) 56(84) bytes of data.
        64 bytes from sea201608exddu0105.sea2xx2xx0051qf.adminsea2.oraclevcn.com (10.0.130.61): icmp_seq=1 ttl=63 time=0.558 ms

        --- sea201608exddu0105.sea2xx2xx0051qf.adminsea2.oraclevcn.com ping statistics ---
        1 packets transmitted, 1 received, 0% packet loss, time 0ms
        rtt min/avg/max/mdev = 0.558/0.558/0.558/0.000 ms
        """
        _cmds = {
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand(re.escape("test -e .ssh/authorized_keys || mkdir -p .ssh && touch .ssh/authorized_keys && chmod 700 .ssh && chmod 600 .ssh/authorized_keys"), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape("sh -c "), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape("/bin/test -e .ssh/authorized_keys"), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape("bin/grep "), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape('grep "EXACLOUD KEY" .ssh/authorized_keys'), aRc=0, aStdout="", aPersist=True)
                    ]
                ],
                self.mGetRegexCell():
                [
                    [
                        exaMockCommand(re.escape("ping *"), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape("test -e .ssh/authorized_keys || mkdir -p .ssh && touch .ssh/authorized_keys && chmod 700 .ssh && chmod 600 .ssh/authorized_keys"), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape("sh -c "), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape("bin/grep "), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape("/bin/test -e .ssh/authorized_keys"), aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape('grep "EXACLOUD KEY" .ssh/authorized_keys'), aRc=0, aStdout="", aPersist=True)
                    ]
                ],
                self.mGetRegexSwitch():
                [
                    [
                        exaMockCommand("sh -c *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/bin/grep ", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand('grep "EXACLOUD KEY scaqab10adm01scaqab10client01vm08scaqab10adm02scaqab10client02vm" .ssh/authorized_keys ;', aRc=0, aStdout="", aPersist=True),
                        exaMockCommand('grep "EXACLOUD KEY scaqab10adm01scaqab10adm01nat08scaqab10adm02scaqab10adm02nat08" .ssh/authorized_keys ;', aRc=0, aStdout="", aPersist=True),
                        exaMockCommand(re.escape("/bin/test -e .ssh/authorized_keys"), aRc=0, aStdout="", aPersist=True)
                    ]
                ],
                self.mGetRegexLocal():  
                [
                    [
                        exaMockCommand("/bin/ping -c 1 *", aRc=0, aStdout=_out1 ,aPersist=True)
                    ]
                ]
                }

        self.mPrepareMockCommands(_cmds)
        _clu_obj = self.mGetClubox()
        _clu_obj.mUpdateAllClusterHostsKeys()

    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNode")
    def test_mCheckVMCyclesAndReboot(self, mock_mRebootNode):
        _out1 = """PING scaqab10adm01.us.oracle.com (10.31.112.4) 56(84) bytes of data.
        64 bytes from scaqab10adm01.us.oracle.com (10.31.112.4): icmp_seq=1 ttl=50 time=28.3 ms

        --- scaqab10adm01.us.oracle.com ping statistics ---
        1 packets transmitted, 1 received, 0% packet loss, time 0ms
        rtt min/avg/max/mdev = 28.383/28.383/28.383/0.000 ms
        """
        _out2 = """    inet 127.0.0.1/8 scope host lo
        10: ib0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 65520 qdisc pfifo_fast state UP qlen 4096
        11: ib1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 65520 qdisc pfifo_fast state UP qlen 4096
            inet 10.31.112.10/24 brd 10.31.112.255 scope global vmeth0
        """
        _cmds = {
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0" ,aPersist=True)
                    ],
                    [
                        exaMockCommand("xm li *", aRc=0, aStdout="2776" ,aPersist=True)
                    ],
                    [
                        exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh && vmbackup cleanall --vm scaqab10client01vm08.us.oracle.com", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("xm destroy *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker remove-domain scaqab10client01vm08.us.oracle.com -force", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("losetup -a | grep /exavmimages/guestimages/scaqab10client01vm08.us.oracle.com", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh && vmbackup cleanall --vm scaqab10client02vm08.us.oracle.com", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker remove-domain scaqab10client02vm08.us.oracle.com -force", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("ip addr show | grep 'ib0\|ib1\|inet '", aRc=0, aStdout=_out2, aPersist=True)
                    ],
                    [
                        exaMockCommand("reboot -f", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ],
                self.mGetRegexLocal():  
                [
                    [
                        exaMockCommand("/bin/ping -c 1 *", aRc=1, aStdout=_out1 ,aPersist=True)
                    ]
                ]
                }

        self.mPrepareMockCommands(_cmds)
        _clu_obj = self.mGetClubox()
        _clu_obj.mCheckVMCyclesAndReboot()

    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("subprocess.check_output", return_value=b64encode(b'1057c25598e20f8accb923c0006534a00f135e4008da872ee7258ae44aec1308'))
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCopyFileToDomus")
    def test_mCopyOneoffZipToDomus(self, mock_path, mock_subprocess, mock_copyfile):

        _cmds = {
                self.mGetRegexVm():  
                [                    
                    [
                        exaMockCommand("sha256sum /u02/opt/dbaas_images/ecsOneoffArchive.zip", aRc=0, aStdout="1057c25598e20f8accb923c0006534a00f135e4008da872ee7258ae44aec1308" ,aPersist=True)
                    ]
                ],
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("sha256sum", aRc=0, aStdout="1057c25598e20f8accb923c0006534a00f135e4008da872ee7258ae44aec1308" ,aPersist=True)
                    ]
                ]
                }

        self.mPrepareMockCommands(_cmds)
        _clu_obj = self.mGetClubox()
        _clu_obj.mCopyOneoffZipToDomus()

    def test_mHandlerNodeDetails(self):
        _cmds = {
                self.mGetRegexCell():
                [
                    [
                        exaMockCommand("/usr/local/bin/imageinfo -version", aRc=0, aStdout="21.2.6.0.0.211117.1", aPersist=True)
                    ]
                ],
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("/usr/local/bin/imageinfo -version", aRc=0, aStdout="21.2.6.0.0.211117.1", aPersist=True)
                    ],
                    [
                        exaMockCommand("/usr/bin/who -b", aRc=0, aStdout="system boot  2022-02-14 05:06", aPersist=True)
                    ]
                ],
                self.mGetRegexSwitch():
                [
                    [
                        exaMockCommand("/usr/local/bin/version | /usr/bin/head -1", aRc=0, aStdout="SUN DCS 36p version: 2.2.13-2" ,aPersist=True)
                    ]
                ]
                }
        self.mPrepareMockCommands(_cmds)
        _clu_obj = self.mGetClubox()
        _clu_obj.mHandlerNodeDetails()

    def test_mHandlerCheckConnection(self):
        _cmds = {                    
                self.mGetRegexVm():  
                [                    
                    [
                        exaMockCommand("hostname -f", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("ping *", aRc=0, aStdout="" ,aPersist=True)
       
                    ]                
                ],  
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("ping *", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ]
                }   
   
        self.mPrepareMockCommands(_cmds)              
        _clu_obj = self.mGetClubox() 
        _clu_obj.mGetCommandHandler().mHandlerCheckConnection() 

    def test_mCleanUpStaleVm(self):
        _cmds = {
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh && vmbackup cleanall --vm *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/usr/sbin/xm destroy *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("systemctl is-active xend", aRc=0, aStdout="active", aPersist=True),
                        exaMockCommand("chkconfig --list xend 2>&1", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("chkconfig xend on", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/usr/sbin/xm list | /bin/grep -w scaqab10client01vm08.us.oracle.com", aRc=1, aStdout="" ,aPersist=True),
                        exaMockCommand("rm -rf /EXAVMIMAGES/GuestImages/*", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ]
                }
        self.mPrepareMockCommands(_cmds)
        _clu_obj = self.mGetClubox()
        _clu_obj.mCleanUpStaleVm(False)    
    
    @mock.patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', retrun_value=True)    
    @mock.patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mStartDom0Service')
    @mock.patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mEnableDom0Service')
    @mock.patch('exabox.core.Node.exaBoxNode.mConnect')
    @mock.patch('exabox.core.Node.exaBoxNode.mSingleLineOutput', return_value='inactive')
    def test_mCleanUpStaleVm_hypervisor_service_not_running(self, mockmIsKVM, mockmStartDom0Service, mockmEnableDom0Service, mockmSingleLineOutput, _mock_node):
    
        _cmds = {
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh && vmbackup cleanall --vm *", aRc=0, aStdout="", aPersist=True),                        
                        exaMockCommand("systemctl is-active 'libvirtd'", aRc=0, aStdout="inactive", aPersist=True),                   
                    ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _clu_obj = self.mGetClubox()
        _mock_node = MagicMock()
        _mock_node.mSingleLineOutput.return_value 
        with self.assertRaises(ExacloudRuntimeError) as cm:
            _clu_obj.mCleanUpStaleVm(False)
        self.assertEqual(cm.exception.args[0], 0x0801)     


    def test_mHandlerRestartRemoteEc(self):
        _cmds = {   
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/usr/bin/sudo /usr/bin/systemctl restart remotemgmtagent", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ]
                }   
   
        self.mPrepareMockCommands(_cmds)              
        _clu_obj = self.mGetClubox()
        _clu_obj.mSetOciExacc(True)
        _clu_obj.mHandlerRestartRemoteEc()

    def test_mDisableQoSM(self):
        _cmds = {
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand("srvctl disable qosmserver", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("srvctl stop qosmserver", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ]
                }

        self.mPrepareMockCommands(_cmds)
        _clu_obj = self.mGetClubox()
        _clu_obj.mDisableQoSM()

    def test_mAtpConfig(self):
        _cmds = {
                self.mGetRegexVm():
                [
                    [
                        exaMockCommand("http://169.254.169.254/opc/v1/instance/canonicalRegionName", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("cat /etc/passwd", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("cat /etc/group", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("test ! -f /etc/ssh/sshd_config.bkbyHostUpdater && cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bkbyHostUpdater", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("sed -i *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("service sshd restart", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("! *", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("mkdir -p /etc/ssh-keys", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("ln -sf /root/.ssh/authorized_keys /etc/ssh-keys/root", aRc=0, aStdout="", aPersist=True),
                        exaMockCommand("ls /home * ", aRc=0, aStdout="", aPersist=True)
                    ]
                ]
                }
        self.mPrepareMockCommands(_cmds)
        _clu_obj = self.mGetClubox()
        _clu_obj.mAtpConfig()

    def test_mHardenOCISecurity(self):
        _cmds = {
                self.mGetRegexCell():
                [
                    [
                        exaMockCommand("/opt/oracle.cellos/host_access_control pam-auth --deny 3", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/host_access_control pam-auth --status", aRc=0, aStdout="", aPersist=True)

                    ],
                    [
                        exaMockCommand("reboot", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/host_access_control pam-auth --deny 3", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/host_access_control pam-auth --status", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/host_access_control idle-timeout --shell 900 --client 900", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/host_access_control idle-timeout --status", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand('echo "Warning: This system is restricted to authorized users for business purposes only." > /opt/oracle.cellos/login_banner.txt', aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/host_access_control banner --file /opt/oracle.cellos/login_banner.txt", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/host_access_control banner --status", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ],
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("rpm -q screen", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ]
                }

        self.mPrepareMockCommands(_cmds)
        _clu_obj = self.mGetClubox()
        _clu_obj.mSetExabm(True)
        _clu_obj.mHardenOCISecurity()
        
        
    def test_mHardenOCISecurity_retry(self):
        _cmds = {
                self.mGetRegexCell():
                [
                    [
                        exaMockCommand("/opt/oracle.cellos/host_access_control pam-auth --deny 3", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/host_access_control pam-auth --status", aRc=0, aStdout="", aPersist=True)

                    ],
                    [
                        exaMockCommand("reboot", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/host_access_control pam-auth --deny 3", aRc=1, aStdout="" ,aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/host_access_control pam-auth --status", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/host_access_control idle-timeout --shell 900 --client 900", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/host_access_control idle-timeout --status", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand('echo "Warning: This system is restricted to authorized users for business purposes only." > /opt/oracle.cellos/login_banner.txt', aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/host_access_control banner --file /opt/oracle.cellos/login_banner.txt", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/opt/oracle.cellos/host_access_control banner --status", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ],
                self.mGetRegexDom0():
                [
                    [
                        exaMockCommand("rpm -q screen", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ]
                }

        self.mPrepareMockCommands(_cmds)
        _clu_obj = self.mGetClubox()
        _clu_obj.mSetExabm(True)
        with self.assertRaises(ExacloudRuntimeError) as context:
            _clu_obj.mHardenOCISecurity()
            self.assertIn("failed", str(context.exception))

    @patch('exabox.core.Node.exaBoxNode.mExecuteCmd')
    def test_mGetSysCtlConfigValue(self, mock_mExecuteCmd):
        """
        Tests mGetSysCtlConfigValue method in clucontrol
        """
        # Set up the mock objects
        node = MagicMock()
        node.mGetHostname.return_value = 'test-host'
        # Create a mock file-like object for _out
        out_mock = MagicMock(spec=io.StringIO)
        out_mock.readlines.return_value = ['net.ipv4.tcp_syncookies=1\n']
        node.mExecuteCmd.side_effect = [
            (None, out_mock, None),  # Return a successful command execution
            (None, out_mock, None),  # Return a successful command execution
        ]
        node.mGetCmdExitStatus.return_value = 0

        # Call the method under test
        _clu_obj = self.mGetClubox()
        result = _clu_obj.mGetSysCtlConfigValue(node, 'net.ipv4.tcp_syncookies')

    def test_mUpdateOEDAProperties(self):
        """
        Tests setting property/value in exacloud/oeda/properties/es.properties
        """
        _cmds = {
                self.mGetRegexLocal():
                [
                    [
                        exaMockCommand("/bin/grep -q *", aRc=0, aStdout="" ,aPersist=True),
                        exaMockCommand("/bin/sed *", aRc=0, aStdout="" ,aPersist=True)
                    ]
                ]
        }
        self.mPrepareMockCommands(_cmds)
        # Call the method under test
        _clu_obj = self.mGetClubox()
        _options = self.mGetPayload()
        _clu_obj.mSetNoOeda(True)
        result = _clu_obj.mUpdateOEDAProperties(_options)
        _clu_utils = ebCluUtils(_clu_obj)
        # Sample property update for a request specific directory
        _clu_utils.mSetPropertyValueOeda("DISABLEVALIDATEDGSPACEFOR37371565", "true", "false")
        # Below is the happy path scenario where we have successfully appended the property value
        _clu_utils.mAppendPropertyValueOeda("HC_CELL_TYPES", "X11MHCXRMEM:X11_XRMEM_ROCE_CELL_XC", ",")
        # Below is a case where the property is found but there is an error while updating in the es.properties file
        _clu_obj.mExecuteLocal = MagicMock(side_effect=[(0, None, None, None), Exception("Mocked mExecuteLocal error"),
                                                        Exception("Mocked mExecuteLocal error")])
        _clu_utils.mAppendPropertyValueOeda("HC_CELL_TYPES", "X11MHCXRMEM:X11_XRMEM_ROCE_CELL_XC", ",")
        # Below is a case where the property is not found in the es.properties file
        _clu_obj.mExecuteLocal = MagicMock(side_effect=[(1, None, None, None), Exception("Mocked mExecuteLocal error"),
                                                        Exception("Mocked mExecuteLocal error")])
        _clu_utils.mAppendPropertyValueOeda("HC_CELL_TYPES", "X11MHCXRMEM:X11_XRMEM_ROCE_CELL_XC", ",")

if __name__ == "__main__":
    unittest.main()
