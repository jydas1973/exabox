"""

 $Header: 

 Copyright (c) 2020, 2025, Oracle and/or its affiliates.

 NAME:
      tests_vmbackup.py - Unitest for vmbackup.py module

 DESCRIPTION:
      Run tests for the methods of vmbackup.py

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       gsundara 11/03/25 - Bug 38606770 - FATAL PYTHON ERROR: INIT_FS_ENCODING
       jfsaldan 09/30/25 - Bug 38485986 - EXACS: VMBOSS: USE 'VMBACKUP VERSION'
                           FROM DOM0 TO COMPARE THE VERSION AGAINST
                           $EC_HOME/IMAGES/<VMBACKUP TGZ>
       jfsaldan 08/01/25 - Enh 38250708 - ECRACLI VMBACKUP INSTALL CHANGES
                           CRONTAB ENTRIES ON DOM0
       akkar    07/24/25 - Bug 38222695 - Raise exception if backup sequence not available
       aypaul   07/03/25 - Bug#38105139 Fix unit test issue with
                           test_mDisableOSSVMBackupConfig.
       jfsaldan 06/26/25 - Bug 38114936 - ECS_MAIN: UNITTEST TESTS_VMBACKUP
                           FAILING INTERMITTENTLY IN METHOD
                           TEST_MDISABLEOSSVMBACKUPCONFIG WITH ERROR OCI ERROR
                           DURING INSTANCE PRINCIPALS CREATION
       jfsaldan 06/11/25 - Bug 38058481 - EXACS:25.2.1, RC4:VMBACKUP TO OSS:ONE
                           COMPUTE FAILED VMBACKUP TO OSS ON MVM EXASCLE IF
                           ANOTHER OSSLIST RUNS WHILE THE BACKUP IS ONGOING
       abflores 05/19/25 - Bug 37916975: UPDATE VMBACKUP PACKAGE DURING
                           ON-DEMAND VMBACKUP TOO
       jfsaldan 05/09/25 - Bug 37932135 - ECS_MAIN: TESTS_VMBACKUP_PY.DIF IS
                           FAILING ON ECS_MAIN_LINUX.X64_250508.0901
       jfsaldan 11/11/24 - Bug 37262021 - ECS_MAIN: UNITTEST TESTS_VMBACKUP
                           FAILING INTERMITTENTLY IN METHOD
                           TEST_MLISTOSSVMBACKUP_SUCCESS_RACKNAME WITH ERROR
                           OCI ERROR DURING INSTANCE PRINCIPALS CREATION
       jfsaldan 10/28/24 - Bug 37178530 - 2.4.1.2.7 | OSS_BACKUP VMBACKUP
                           OSSLIST SHOW ALL MVM CLUSTER BACKUP LIST
       jfsaldan 10/09/24 - Bug 37137506 - EXACLOUD VMBACKUP TO OSS: EXACLOUD
                           SHOULD DISABLE OSS BACKUP FROM VMBACKUP.CONF AFTER
                           THE ECRA SCHEDULED BACKUP FINISH
       gsundara 10/04/24 - Bug 36741285 - EXADB-XS: DISABLING VM BACKUP WHILE
                           INGESTION FROM EXACS TO EXACOMPUTE
       jfsaldan 09/26/24 - Bug 37107371 - EXACS X11M - DELETE SERVICE TAKING
                           EXTRA 1HR AND HANGING DURING PREVMSETUP STEP
       ririgoye 09/12/24 - Bug 36348868 - Fix vm backup unit tests after
                           changing exassh buffer
       prsshukl 09/11/24 - Bug 37046856 - ECS_MAIN: UNITTEST TESTS_VMBACKUP
                           FAILING INTERMITTENTLY OCI ERROR DURING INSTANCE
                           PRINCIPALS CREATION.
       jfsaldan 08/27/24 - Bug 36899424 - EXACLOUD VMBACKUP TO OSS: EXACLOUD
                           SHOULD ENABLE THE OSSBACKUP FLAG IN VMBACKUP.CONF
                           BEFORE ANY OSS OPERATION, AND DISABLE AFTER IS DONE
       jfsaldan 06/24/24 - Enh 36755943 - EXACLOUD VMBACKUP: EXACLOUD SHOULD
                           HAVE A FEATURE FLAG SO THAT WE CAN ENABLE/DISABLE
                           THE CRONTAB ENTRY FOR VMBACKUP IN THE DOM0S
       jfsaldan 06/06/24 - Bug 36696343 - ECS MAIN:VMBACKUP: VMBACKUP BACKUP
                           WORKFLOW DID NOT SHOW VMBACKUP ERROR VMBOSS WHILE
                           SUFFICENT SPACE IS UNAVAILABLE
       jfsaldan 05/29/24 - Enh 36474098 - EXACLOUD TO SUPPORT VM RESTORE ON
                           INDIVIDUAL FILESYSTEMS
       remamid  05/16/24 - Bug 36037417 - ONLY PRINT JSON FORMATTED OUTPUT WHEN
                           USING THE --JSON FLAG ON VMBACKUP
       enrivera 03/07/24 - Bug 36059011 - LATEST VM BACKUP UPGRADE IS NOT
                           UPDATING THE VMBACKUP.CONF WITH RIGHT VALUES
       pbellary 01/26/24 - Bug 36174750 - NODE RECOVERY : VMBACKUP RESTORE OPERATION FAILED 
                           BUT THE STATUS API FROM EXACLOUD DOES NOT REFER THE API FAILURE 
       jfsaldan 01/22/24 - Bug 36197480 - EXACS - EXACLOUD FAILS TO SET
                           VMBACKUP.CONF VALUES TO ENABLED VMBACKUP TO OSS
       gparada  01/04/24 - Broken test
       aypaul   12/26/23 - Fix vmbackup install unit test regression.
       jfsaldan 11/01/23 - Bug 35969085 - ECS:EXACLOUD:23.4.1.2:ADD KMS KEY
                           OCID AND CRYPTO ENDPOINT IN ALREADY PROVISIONED
                           CLUSTERS IF PARAMETER IS MISSING FROM VMBACKUP.CONF
       jfsaldan 10/20/23 - Bug 35857923 - ECS:23.4.1.2:EXACLOUD SHOULD NOT
                           EXPECT THE DEST_DIR VALUE ON VMBACKUP RESTORE_OSS
                           CALL
       jfsaldan 08/24/23 - Enh 35692408 - EXACLOUD - VMBOSS - CREATE A FLAG IN
                           EXABOX.CONF THAT TOGGLES BETWEEN INSTANCE PRINCIPALS
                           AND USERS PRINCIPALS FOR VMBACKUP TO OSS MODULE
       pbellary 08/02/23 - Bug 35665469 - UNIT TEST FAILURE ON TESTS_VMBACKUP.PY
       jfsaldan 06/22/23 - Enh 35399269 - EXACLOUD TO SUPPORT RETRIEVAL OF
                           METADATA FILES FROM DOM0 FOR BACKUP OPERATION.
       vikasras 04/14/23 - 35276663 - VMBACKUP UTILITY INSTALL IS ADDING WRONG
                           ENTRY IN CRONTAB
       jfsaldan 03/16/23 - Enh 35135691 - EXACLOUD - ADD SUPPORT FOR VMBACKUP
                           ECRA SCHEDULER
       jfsaldan 02/10/23 - Bug 35054534 - EXACS:22.2.1:DROP2:FILE SYSTEM
                           ENCRYPTION TEST: VMBACKUP INSTALL FAILED AT
                           IMAGES/PYTHON-FOR-VMBACKUP-OL6.TGZ: NO SUCH FILE OR
                           DIRECTORY
       jfsaldan 01/11/23 - Enh 34965441 - EXACLOUD TO SUPPORT NEW TASK FOR GOLD
                           IMAGE BACKUP
       pkandhas 12/23/22 - Add unitTest for bug 34482941
       aypaul   12/13/22 - Add unit tests for mCleanVMbackup.
       ajayasin 01/19/22 - new ut file for vmbackup.py

        ajayasin    14/12/21 - Creation of the file
"""

import unittest
import json
import copy
import uuid
import warnings

warnings.filterwarnings("ignore")

from random import shuffle

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.ovm.vmbackup import ebCluManageVMBackup
from exabox.ovm.vmboci import ebVMBackupOCI
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from unittest import mock
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
from exabox.log.LogMgr import ebLogInfo
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check)
from exabox.core.Context import get_gcontext
from exabox.ovm.hypervisorutils import *
from exabox.exaoci.connectors.R1Connector import R1Connector

EXASCALE_PAYLOAD = """ 
{
   "exascale":{
      "cell_list":[
         "scaqab10celadm01.us.oracle.com",
         "scaqab10celadm02.us.oracle.com",
         "scaqab10celadm03.us.oracle.com"
      ],
      "ctrl_network":{
         "ip":"10.0.130.110",
         "port":"5052",
         "name":"sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
      }
    },
   "rack":{
      "name":"iad100642exd-atpmg-scaqau11XXX-clu06",
      "storageType":"XS",
      "xsVmBackup": "True",
      "system_vault": [
             {
                "vault_type":"backup",
                "name":"backupvault",
                "xsVmBackupRetentionNum": "2"
            }
      ]
   }
}
"""

class MockebVgCompRegistry():
    __component = {}

    def mRegisterComponent(self, aCompType, aVirtGuestObj):
        _type = aCompType
        self.__component[_type] = aVirtGuestObj

    def mGetComponent(self, aCompType):
        _type = aCompType
        self.__handle = self.__component[_type]
        return self.__handle

class MockebVgLifeCycle(ebVgBase):
    def __init__(self):
        self.__id = uuid.uuid4()
    
    def mSetOVMCtrl(self, aCtx, aNode = None):
        _ctx = aCtx
        _node = aNode

    def mDispatchEvent(self, aCmd, aOptions=None, aVMId=None, aCluCtrlObj=None):
        return 0

class mockFileStream():

    def __init__(self, message):
        self.__message = message

    def read(self):
        return self.__message

    def readlines(self):
        return self.__message

class ebTestNode(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.maxDiff = None

        self.VMBACKUPENV_FILE = "/opt/python-vmbackup/bin/set-vmbackup-env.sh"


    def test_mExecuteOperation(self):
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
        _options.jsonconf['vmbackup_operation'] = None
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = None
        _vmBackup.mExecuteOperation(_options)

    def test_mExecuteOperation_enable(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("cp *", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mv -f *", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['vmbackup_operation'] = None
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "enable"
        _vmBackup.mExecuteOperation(_options)

    def test_mExecuteOperation_enable_error(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("cp *", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mv -f *", aStdout=None)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['vmbackup_operation'] = None
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "enable"
        _vmBackup.mExecuteOperation(_options)


    def test_mExecuteOperation_disable(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("cp *", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mv -f *", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['vmbackup_operation'] = None
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "disable"
        _vmBackup.mExecuteOperation(_options)




    def test_mExecuteOperation_disable_error(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("cp *", aStdout="free : 193987172\ncached : 0"),
                    exaMockCommand("mv -f *", aStdout=None)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['vmbackup_operation'] = None
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "disable"
        _vmBackup.mExecuteOperation(_options)

    def test_mExecuteOperation_setparam_back_not_enabled(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",aRc=1, aPersist=True)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['vmbackup_operation'] = "setparam"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "setparam"
        _vmBackup.mExecuteOperation(_options)

    @patch("exabox.ovm.vmbackup.fileinput.FileInput")
    @patch("exabox.ovm.vmbackup.os.remove")
    @patch("exabox.ovm.vmbackup.os.makedirs")
    def test_mExecuteOperation_setparam(self, aMockMkdir, aMockRemove, aMockFileInput):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",aRc=0, aPersist=True),
                    exaMockCommand("/bin/scp .*tmp/.*vmbackup.conf_.* /opt/oracle/vmbackup/conf/vmbackup.conf",aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",aRc=1, aPersist=True)
                ],
                [
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",aRc=1, aPersist=True)
                ]
            ],
            self.mGetRegexLocal(): [
                [
                   exaMockCommand("/bin/ls *", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                ],
                [
                   exaMockCommand("/bin/ls *", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                ]
           ]
        }
        f = open("./vmbackup.conf", "w")
        f.write("vmbackup_operation=setparam")
        f.write("vmbackup_operation=param")
        f.close()
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['vmbackup_operation'] = "setparam"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "setparam"
        _vmBackup.mExecuteOperation(_options)
        #os.remove("./vmbackup.conf")
        

    def test_mExecuteOperation_getparam_back_not_enabled(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",aRc=1, aPersist=True)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['vmbackup_operation'] = "getparam"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "getparam"
        _vmBackup.mExecuteOperation(_options)

    @patch("exabox.ovm.vmbackup.open")
    def test_mExecuteOperation_getparam(self, aMockOpen):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",aRc=1, aPersist=True)
                ],
                [
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",aRc=1, aPersist=True)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['vmbackup_operation'] = "getparam"
        _options.jsonconf['param'] = "getparam"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "getparam"
        _vmBackup.mExecuteOperation(_options)

    def test_mExecuteOperation_install_jsonconf_none(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",aRc=1),
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf = None
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "install"
        self.assertRaises(Exception, _vmBackup.mExecuteOperation,_options)




    def test_mExecuteOperation_install(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",aRc=1, aPersist=True),
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand("uname -a  | awk*",aRc=0, aStdout="4.1.12-124.52.4.el6uek.x86_64",aPersist=True),
                    exaMockCommand("mkdir -p /opt/exacloud/vmbackup/release-vmbackup/*",aRc=0, aPersist=True),
                    exaMockCommand("/bin/scp images/python-for-vmbackup.tgz*",aRc=0, aPersist=True),
                    exaMockCommand("/bin/scp ./release-vmbackup1.tgz*",aRc=0, aPersist=True),
                    exaMockCommand("tar -xzf /opt/exacloud/vmbackup/python-for-vmbackup.tgz*",aRc=0, aPersist=True),
                    exaMockCommand("tar -xzf /opt/exacloud/vmbackup/release-vmbackup.tgz*",aRc=0, aPersist=True),
                    exaMockCommand("cd /opt/exacloud/vmbackup/release-vmbackup*",aRc=0, aPersist=True),
                    exaMockCommand("grep vmbackup_operation /opt/oracle/vmbackup/conf/vmbackup.conf*",aRc=0, aStdout="vmbackup_operation",aPersist=True),
                    exaMockCommand("grep remote_backup /opt/oracle/vmbackup/conf/vmbackup.conf",aRc=0, aStdout="remote_backup",aPersist=True),
                    exaMockCommand("sed -i -e*",aRc=0, aStdout="remote_backup",aPersist=True),
                    exaMockCommand("sed -i ",aRc=0, aPersist=True),
                    exaMockCommand("rm -f /opt/exacloud/vmbackup/release-vmbackup",aRc=0, aPersist=True),
                    exaMockCommand("test -f /opt/python-vmbackup/bin/python3.6",aRc=0),
                    exaMockCommand("! /bin/test -e /var/spool/cron/root*",aRc=0),
                    exaMockCommand("/bin/grep.*/opt/oracle/vmbackup/sched_vmb.sh.*/var/spool/cron/root",aRc=0),
                    exaMockCommand("/bin/grep.*/opt/oracle/vmbackup/sched_vmb.sh.*/var/spool/cron/root",aRc=0),
                    exaMockCommand("/bin/cat /var/spool/cron/root",aRc=0,
                        aStdout=(
                            "00 23 * * 6 /opt/oracle/vmbackup/sched_vmb.sh\n"
                            "0 8 10 * * SUN /opt/exacloud/bondmonitor/bond_utils.py check_all\n"
                            ))
                ],
                [
                    exaMockCommand("test -e.*id_rsa",aPersist=True),
                    exaMockCommand("mv.*id_rsa",aPersist=True),
                    exaMockCommand("if [[ ! `find ~/.ssh -maxdepth 1 -name 'id_rsa'` || ! `find ~/.ssh -maxdepth 1 -name 'id_rsa.pub'` ]]*",aRc=0, aStdout="aaaasdasdafasfafa",aPersist=True),
                    exaMockCommand("sed --follow-symlinks -i*",aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("awk*",aRc=0, aPersist=True),
                    exaMockCommand("ssh-keygen -R*",aRc=0, aPersist=True),
                    exaMockCommand("sed --follow-symlinks -i*",aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("ssh-keygen -R*",aRc=0, aPersist=True),
                    exaMockCommand("sh -c 'echo aaaasdasdafasfafa*",aRc=0, aPersist=True),
                    exaMockCommand("ssh-keyscan *",aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("ssh-keyscan *",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh*",aRc=0, aPersist=True),
                    exaMockCommand("uname -a  | awk*",aRc=0, aStdout="4.1.12-124.52.4.el6uek.x86_64",aPersist=True),
                    exaMockCommand("mkdir -p /opt/exacloud/vmbackup/release-vmbackup/*",aRc=0, aPersist=True),
                    exaMockCommand("rm -f /opt/exacloud/vmbackup/release-vmbackup",aRc=0, aPersist=True),
                    exaMockCommand("/bin/scp images/python-for-vmbackup.tgz*",aRc=0, aPersist=True),
                    exaMockCommand("/bin/scp ./release-vmbackup1.tgz*",aRc=0, aPersist=True),
                    exaMockCommand("tar -xzf /opt/exacloud/vmbackup/python-for-vmbackup.tgz*",aRc=0, aPersist=True),
                    exaMockCommand("tar -xzf /opt/exacloud/vmbackup/release-vmbackup.tgz*",aRc=0, aPersist=True),
                    exaMockCommand("cd /opt/exacloud/vmbackup/release-vmbackup*",aRc=0, aPersist=True),
                    exaMockCommand("grep vmbackup_operation /opt/oracle/vmbackup/conf/vmbackup.conf*",aRc=0, aStdout="vmbackup_operation",aPersist=True),
                    exaMockCommand("grep remote_backup /opt/oracle/vmbackup/conf/vmbackup.conf",aRc=0, aStdout="remote_backup",aPersist=True),
                    exaMockCommand("sed -i -e*",aRc=0, aStdout="remote_backup",aPersist=True),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh*",aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("test -e.*id_rsa",aPersist=True),
                    exaMockCommand("mv.*id_rsa",aPersist=True),
                    exaMockCommand("if [[ ! `find ~/.ssh -maxdepth 1 -name 'id_rsa'` || ! `find ~/.ssh -maxdepth 1 -name 'id_rsa.pub'` ]]*",aRc=0, aStdout="aaaasdasdafasfafa",aPersist=True),
                    exaMockCommand("sed --follow-symlinks -i*",aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("awk*",aRc=0, aPersist=True),
                    exaMockCommand("ssh-keygen -R*",aRc=0, aPersist=True),
                    exaMockCommand("sed --follow-symlinks -i*",aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("ssh-keygen -R*",aRc=0, aPersist=True),
                    exaMockCommand("sh -c 'echo aaaasdasdafasfafa*",aRc=0, aPersist=True),
                    exaMockCommand("ssh-keyscan *",aRc=0, aPersist=True),
                    exaMockCommand("sed --follow-symlinks -i*",aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("ssh-keyscan *",aRc=0, aPersist=True),
                    exaMockCommand("sh -c 'echo aaaasdasdafasfafa*",aRc=0, aPersist=True)
                ],
                [
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['vmbackup_operation'] = "install"
        _options.jsonconf['remote_backup'] = "remote_backup"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "install"
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _ebox.mSetOrigDom0sDomUs(_ddp)
        _vmBackup.VMBACKUPPKG_BITS = "./"
        f = open("./release-vmbackup1.tgz", "w")
        f.close()
        _vmBackup.mExecuteOperation(_options)

    def test_mRecordError(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",aRc=1, aPersist=True)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf = None
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "install"
        aErrorCode = "808"
        aString = "FATAL"
        _vmBackup.mRecordError(aErrorCode)
        _vmBackup.mRecordError(aErrorCode,aString)

    def test_mExecuteOperation_backup_error(self):
        _stdout_status = (
            '''{"GuestVMs": {'''
                '''"gold-luks-real-k0obn1.client.exaclouddev.oraclevcn.com":'''
                '''{"CurrentStatus": "Failed",'''
                '''"LatestSuccessfulSequenceNumber": "13",'''
                '''"TimestampOfLastSuccessfulBackup": "2024-05-31-19-59-13",'''
                '''"NumberOfBackupsInOss": 11},'''
                '''"passphrasetest-vuhwa1.client.exaclouddev.oraclevcn.com":'''
                '''{"CurrentStatus": "Failed",'''
                '''"LatestSuccessfulSequenceNumber": "None",'''
                '''"TimestampOfLastSuccessfulBackup": "None",'''
                '''"NumberOfBackupsInOss": 0}},'''
                '''"CurrentBackupOperationCompleted": true}\n''')
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=1, aPersist=True),
                    exaMockCommand("/usr/bin/ps -fe| /bin/grep 'python-vmbackup' | /bin/grep -v grep",
                        aStdout="",
                        aRc=1),
                    exaMockCommand("/bin/cat /EXAVMIMAGES/Backup/OSSMetadata/ossbackup_status.json",
                        aRc=0, aPersist=True, aStdout=_stdout_status)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "backup"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "backup"
        #This should only log a warn but not cause an error
        with patch(
                "exabox.ovm.vmbackup.ebCluManageVMBackup.mInstallNewestVMBackupTool",
                    return_value = 1):
            self.assertRaises(ExacloudRuntimeError,
                lambda : _vmBackup.mExecuteOperation(_options))

    def test_mExecuteOperation_backup(self):
        #Create args structure
        _stdout_status = (
            '''{"GuestVMs": {'''
                '''"gold-luks-real-k0obn1.client.exaclouddev.oraclevcn.com":'''
                '''{"CurrentStatus": "Succeeded",'''
                '''"LatestSuccessfulSequenceNumber": "13",'''
                '''"TimestampOfLastSuccessfulBackup": "2024-05-31-19-59-13",'''
                '''"NumberOfBackupsInOss": 11},'''
                '''"passphrasetest-vuhwa1.client.exaclouddev.oraclevcn.com":'''
                '''{"CurrentStatus": "Succeeded",'''
                '''"LatestSuccessfulSequenceNumber": "None",'''
                '''"TimestampOfLastSuccessfulBackup": "None",'''
                '''"NumberOfBackupsInOss": 0}},'''
                '''"CurrentBackupOperationCompleted": true}\n''')
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/ps -fe| /bin/grep 'python-vmbackup' | /bin/grep -v grep",
                        aStdout="",
                        aRc=1),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /EXAVMIMAGES/Backup/OSSMetadata/ossbackup_status.json",
                        aRc=0, aPersist=True, aStdout=_stdout_status)
                ],
                [
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model",aRc=0,
                        aStdout="ORACLE SERVER E4-2c\n"),
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "backup"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "backup"
        with patch(
                "exabox.ovm.vmbackup.ebCluManageVMBackup.mInstallNewestVMBackupTool",
                    return_value = 0):
            _vmBackup.mExecuteOperation(_options)

    def test_mExecuteOperation_restore_json_none(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=1, aPersist=True)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf = None
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "restore"
        self.assertRaises(Exception, _vmBackup.mExecuteOperation,_options)

    def test_mExecuteOperation_restore(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=1, aPersist=True)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "restore"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "restore"
        _vmBackup.mExecuteOperation(_options)

    def test_mExecuteOperation_restore_node_vmname(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aStdout="2", aPersist=True),
                    exaMockCommand("/bin/mv -f *",aRc=0, aPersist=True),
                    exaMockCommand("/bin/rm -rf *",aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("find /EXAVMIMAGES/Backup/ | grep 'scaqab10client01vm08.us.oracle.com",aRc=0, aStdout="/EXAVMIMAGES/Backup/vm/data/2", aPersist=True),
                ],
                [
                    exaMockCommand("ls -lA /EXAVMIMAGES/Backup/vm/data/backup | awk 'BEGIN{sum=0} {sum+=$5} END{print sum}'",aRc=0, aStdout="5",aPersist=True),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh; vmbackup restore --vm*",aRc=0, aPersist=True),
                    exaMockCommand("ls -lA /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com | awk 'BEGIN{sum=0} {sum+=$5} END{print sum}'",aStdout="5",aRc=0, aPersist=True),
                    exaMockCommand("/bin/mv -f *",aRc=0, aPersist=True),
                    exaMockCommand("/bin/rm -rf *",aRc=0, aPersist=True),
                     exaMockCommand("/bin/mkdir *",aRc=0, aPersist=True),
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "restore"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "restore"
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup.mRestoreVMbackup(_options,_dom0,_domU)

    def test_mExecuteOperation_restore_source_valid(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0,aStdout="Data", aPersist=True)
                ],
                [
                    exaMockCommand("find /EXAVMIMAGES/Backup/ | grep 'scaqab10client01vm08.us.oracle.com",aRc=0, aStdout="/EXAVMIMAGES/Backup/vm/data/Data", aPersist=True),
                ],
                [
                    exaMockCommand("/bin/mv -f *",aRc=0, aPersist=True),
                    exaMockCommand("/bin/rm -rf *",aRc=0, aPersist=True),
                    exaMockCommand("/bin/mkdir *",aRc=0, aPersist=True),
                    exaMockCommand(f"source /opt/python-vmbackup/bin/set-vmbackup-env.sh; vmbackup restore --vm scaqab10client01vm08.us.oracle.com --seq Data --loc local --uuid .*", aRc=0, aPersist=True)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "restore"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "restore"
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup.mRestoreVMbackup(_options,_dom0,_domU)

    def test_mExecuteOperation_restore_source_backup(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="Node type: KVMHOST"),
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0,aStdout="backup", aPersist=True)
                ],
                [
                    exaMockCommand("find /EXAVMIMAGES/Backup/ | grep 'scaqab10client01vm08.us.oracle.com",aRc=0, aStdout="/EXAVMIMAGES/Backup/vm/data/backup", aPersist=True),
                ],
                [
                    exaMockCommand("ls -lA /EXAVMIMAGES/Backup/vm/data/backup | awk 'BEGIN{sum=0} {sum+=$5} END{print sum}'",aRc=0, aStdout="5",aPersist=True),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh; vmbackup restore --vm*",aRc=0, aPersist=True),
                    exaMockCommand("ls -lA /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com | awk 'BEGIN{sum=0} {sum+=$5} END{print sum}'",aStdout="5",aRc=0, aPersist=True),
                    exaMockCommand("/bin/mv -f *",aRc=0, aPersist=True),
                    exaMockCommand("/bin/rm -rf *",aRc=0, aPersist=True),
                     exaMockCommand("/bin/mkdir *",aRc=0, aPersist=True),
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "restore"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "restore"
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _compHandler = _ebox.mGetComponentRegistry()
        _vm_obj = MockebVgLifeCycle()
        _compHandler.mRegisterComponent("vm_operations", _vm_obj)
        _vmBackup.mRestoreVMbackup(_options,_dom0,_domU)

    def test_mExecuteOperation_restore_source_restore_fail(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0,aStdout="backup", aPersist=True)
                ],
                [
                    exaMockCommand("find /EXAVMIMAGES/Backup/ | grep 'scaqab10client01vm08.us.oracle.com",aRc=0, aStdout="/EXAVMIMAGES/Backup/vm/data/backup", aPersist=True),
                ],
                [
                    exaMockCommand("ls -lA /EXAVMIMAGES/Backup/vm/data/backup | awk 'BEGIN{sum=0} {sum+=$5} END{print sum}'",aRc=0, aStdout="5",aPersist=True),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh; vmbackup restore --vm*",aRc=0, aStderr="error",aPersist=True),
                    exaMockCommand("ls -lA /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com | awk 'BEGIN{sum=0} {sum+=$5} END{print sum}'",aStdout="5",aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("/bin/mv -f *",aRc=0, aPersist=True),
                    exaMockCommand("/bin/rm -rf *",aRc=0, aPersist=True),
                    exaMockCommand("/bin/mkdir *",aRc=0, aPersist=True),
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "restore"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "restore"
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup.mRestoreVMbackup(_options,_dom0,_domU)




    def test_mExecuteOperation_restore_json_conf(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=1, aPersist=True)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "restore"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "restore"

        _options.jsonconf['dom0'] = _dom0
        _options.jsonconf['vm_name'] = _domU
        _options.jsonconf['backup_seq'] = 'backup_seq'
        _options.jsonconf['local'] = 'local'
        _options.jsonconf['dest'] = 'dest'
        try:
            _vmBackup.mExecuteOperation(_options)
        except:
            ebLogInfo("Exception Caught..")


    def test_mExecuteOperation_restore_with_node(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=1, aPersist=True),
                    exaMockCommand("/bin/test -e *",aRc=1, aPersist=True),
                    exaMockCommand("/bin/mv -f *",aRc=0, aPersist=True),
                    exaMockCommand("/bin/rm -rf *",aRc=0, aPersist=True),
                    exaMockCommand("/bin/mkdir *",aRc=0, aPersist=True),
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "restore"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "restore"
        _vmBackup.mExecuteOperation(_options)
        _node = exaBoxNode(self.mGetContext())
        _node.mConnect(_domU)
        _vmBackup.mRestoreVMbackup(_options,_node,_domU)

    def test_mExecuteOperation_patch(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=1, aPersist=True),
                    exaMockCommand("uname -a  | awk*",aRc=0, aStdout="4.1.12-124.52.4.el6uek.x86_64",aPersist=True),
                    exaMockCommand("cd /opt/exacloud/vmbackup/release-vmbackup*",aRc=0, aPersist=True),
                    exaMockCommand("tar -xzf /opt/exacloud/vmbackup/python-for-vmbackup.tgz*",aRc=0, aPersist=True),
                    exaMockCommand("tar -xzf /opt/exacloud/vmbackup/release-vmbackup.tgz*",aRc=0, aPersist=True),
                    exaMockCommand("/bin/scp ./release-vmbackup1.tgz*",aRc=0, aPersist=True),
                    exaMockCommand("mkdir -p /opt/exacloud/vmbackup/release-vmbackup/*",aRc=0, aPersist=True),
                    exaMockCommand("test -f /opt/python-vmbackup/bin/python3.6",aRc=0),
                    exaMockCommand("rm -f /opt/exacloud/vmbackup/release-vmbackup",aRc=0, aPersist=True),
                    exaMockCommand("/bin/scp images/python-for-vmbackup.tgz*",aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("if [[ ! `find ~/.ssh -maxdepth 1 -name 'id_rsa'` || ! `find ~/.ssh -maxdepth 1 -name 'id_rsa.pub'` ]]*",aRc=0, aStdout="aaaasdasdafasfafa",aPersist=True),
                    exaMockCommand("sed --follow-symlinks -i*",aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("ssh-keygen -R*",aRc=0, aPersist=True),
                    exaMockCommand("sed --follow-symlinks -i*",aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("ssh-keygen -R*",aRc=0, aPersist=True),
                    exaMockCommand("sh -c 'echo aaaasdasdafasfafa*",aRc=0, aPersist=True),
                    exaMockCommand("ssh-keyscan -t rsa*",aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh*",aRc=0, aPersist=True),
                    exaMockCommand("uname -a  | awk*",aRc=0, aStdout="4.1.12-124.52.4.el6uek.x86_64",aPersist=True),
                    exaMockCommand("mkdir -p /opt/exacloud/vmbackup/release-vmbackup/*",aRc=0, aPersist=True),
                    exaMockCommand("rm -f /opt/exacloud/vmbackup/release-vmbackup",aRc=0, aPersist=True),
                    exaMockCommand("/bin/scp images/python-for-vmbackup.tgz*",aRc=0, aPersist=True),
                    exaMockCommand("/bin/scp ./release-vmbackup1.tgz*",aRc=0, aPersist=True),
                    exaMockCommand("tar -xzf /opt/exacloud/vmbackup/python-for-vmbackup.tgz*",aRc=0, aPersist=True),
                    exaMockCommand("tar -xzf /opt/exacloud/vmbackup/release-vmbackup.tgz*",aRc=0, aPersist=True),
                    exaMockCommand("cd /opt/exacloud/vmbackup/release-vmbackup*",aRc=0, aPersist=True),
                    exaMockCommand("grep vmbackup_operation /opt/oracle/vmbackup/conf/vmbackup.conf*",aRc=0, aStdout="vmbackup_operation",aPersist=True),
                    exaMockCommand("grep remote_backup /opt/oracle/vmbackup/conf/vmbackup.conf",aRc=0, aStdout="remote_backup",aPersist=True),
                    exaMockCommand("sed -i -e*",aRc=0, aStdout="remote_backup",aPersist=True),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh*",aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("if [[ ! `find ~/.ssh -maxdepth 1 -name 'id_rsa'` || ! `find ~/.ssh -maxdepth 1 -name 'id_rsa.pub'` ]]*",aRc=0, aStdout="aaaasdasdafasfafa",aPersist=True),
                    exaMockCommand("sed --follow-symlinks -i*",aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("ssh-keygen -R*",aRc=0, aPersist=True),
                    exaMockCommand("sed --follow-symlinks -i*",aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("ssh-keygen -R*",aRc=0, aPersist=True),
                    exaMockCommand("sh -c 'echo aaaasdasdafasfafa*",aRc=0, aPersist=True),
                    exaMockCommand("ssh-keyscan -t rsa*",aRc=0, aPersist=True)
                ],
                [
                ]

            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "patch"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "patch"
        _vmBackup.VMBACKUPPKG_BITS = "./"
        f = open("./release-vmbackup1.tgz", "w")
        f.close()
        _vmBackup.mExecuteOperation(_options)

    def test_mExecuteOperation_list(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=1, aPersist=True)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "list"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "list"
        _vmBackup.mExecuteOperation(_options)

    def test_mExecuteOperation_list_vmbackup_install(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "list"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "list"
        _vmBackup.mExecuteOperation(_options)

    def test_mExecuteOperation_list_vmbackup_install_pass(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aStdout="backup",aPersist=True)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "list"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "list"
        _vmBackup.mExecuteOperation(_options)



    def test_mExecuteOperation_mCleanAllVMbackup(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=1, aPersist=True)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "list"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "list"
        _vmBackup.mCleanAllVMbackup()

    def test_mExecuteOperation_mCleanAllVMbackup_else(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True)
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "list"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "list"
        _vmBackup.mCleanAllVMbackup()

    def test_mExecuteOperation_mSetSSHDOptions(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand("/bin/sed 's/^ClientAliveCountMax.*/ClientAliveCountMax 24/' -i /etc/ssh/sshd_config",aRc=0, aPersist=True),
                    exaMockCommand("/bin/sed*",aRc=0, aPersist=True),
                    exaMockCommand("/sbin/service sshd restart",aRc=0, aPersist=True),
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "list"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "list"
        _node = exaBoxNode(self.mGetContext())
        _node.mConnect(_dom0)
        _vmBackup.mSetSSHDOptions(_options,_node)

    def test_mExecuteOperation_mSetSSHDOptions_error(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand("/bin/sed 's/^ClientAliveCountMax.*/ClientAliveCountMax 24/' -i /etc/ssh/sshd_config",aRc=0, aPersist=True),
                    exaMockCommand("/bin/sed*",aRc=0, aPersist=True),
                    exaMockCommand("/sbin/service sshd restart",aRc=1, aPersist=True),
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "list"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "list"
        _node = exaBoxNode(self.mGetContext())
        _node.mConnect(_dom0)
        _vmBackup.mSetSSHDOptions(_options,_node)

    def test_mExecuteOperation_mSetVMBackupCronJob(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/grep*",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand("! /bin/test -e /var/spool/cron/root*",aRc=0, aPersist=True),
                    exaMockCommand("/bin/grep \".\*$ /opt/oracle/vmbackup/sched_vmb.sh\" /var/spool/cron/root",aRc=0, aPersist=True), 
                    exaMockCommand("/bin/sed*",aRc=0, aPersist=True),
                    exaMockCommand("/sbin/service sshd restart",aRc=0, aPersist=True),
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "list"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "list"
        _node = exaBoxNode(self.mGetContext())
        _node.mConnect(_dom0)
        _vmBackup.mSetVMBackupCronJob(_options,_node)

    def test_mExecuteOperation_mSetVMBackupCronJob_error1(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/grep*",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand("! /bin/test -e /var/spool/cron/root*",aRc=0, aPersist=True),
                    exaMockCommand("/bin/grep \".\*$ /opt/oracle/vmbackup/sched_vmb.sh\" /var/spool/cron/root",aRc=0, aPersist=True),
                    exaMockCommand("/bin/sh -c 'echo *",aRc=1, aPersist=True),
                    exaMockCommand("/bin/sed*",aRc=0, aPersist=True),
                    exaMockCommand("/sbin/service sshd restart",aRc=0, aPersist=True),
                ]
            ]
        }
        #Init new Args
        _options = self.mGetPayload()
        _options.jsonconf['param'] = "list"
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ddp = _ebox.mReturnDom0DomUPair(True)
        _dom0,_domU = _ddp[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "list"
        _node = exaBoxNode(self.mGetContext())
        _node.mConnect(_dom0)
        _vmBackup.mSetVMBackupCronJob(_options,_node)

    def test_mCleanVMbackup(self):
        ebLogInfo("Running tests on ebCluManageVMBackup.mCleanVMbackup")

        _ebox = self.mGetClubox()
        _options = _ebox.mGetArgsOptions()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _vmBackup.mCleanVMbackup(_options, None, False)

        self.assertEqual(_vmBackup.mGetVMBackupData()['Exacloud Cmd Status'], _vmBackup.FAIL)
        _ddp = _ebox.mReturnDom0DomUPair()
        self.mPrepareMockCommands({})
        with patch('exabox.ovm.vmbackup.ebCluManageVMBackup.mCheckVMbackupInstalled', return_value = False):
            _vmBackup.mCleanVMbackup(_options, _ddp, False)
            self.assertEqual(_vmBackup.mGetVMBackupData()['Exacloud Cmd Status'], _vmBackup.FAIL)
        with patch('exabox.ovm.vmbackup.ebCluManageVMBackup.mCheckVMbackupInstalled', return_value = True),\
             patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value = (mockFileStream("None"), mockFileStream("output message"), mockFileStream("error message"))),\
             patch('exabox.core.Node.exaBoxNode.mGetCmdExitStatus', return_value = 0):
            _vmBackup.mCleanVMbackup(_options, _ddp, False)
            self.assertEqual(_vmBackup.mGetVMBackupData()['Exacloud Cmd Status'], _vmBackup.PASS)
        with patch('exabox.ovm.vmbackup.ebCluManageVMBackup.mCheckVMbackupInstalled', return_value = True),\
             patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value = (mockFileStream("None"), mockFileStream("output message"), mockFileStream("mock error message"))),\
             patch('exabox.core.Node.exaBoxNode.mGetCmdExitStatus', return_value = 1):
            _vmBackup.mCleanVMbackup(_options, _ddp, False)
            self.assertEqual(_vmBackup.mGetVMBackupData()['Exacloud Cmd Status'], _vmBackup.FAIL)

    def test_mTriggerBackgrounBackupHost_success_ondemand_false(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/bin/test -e {self.VMBACKUPENV_FILE}",
                        aRc=0),
                    exaMockCommand("/usr/bin/ps -fe| /bin/grep 'python-vmbackup' | /bin/grep -v grep",
                        aStdout="",
                        aRc=1),
                    exaMockCommand(f"source {self.VMBACKUPENV_FILE}",
                        aRc=0),
                    exaMockCommand(f"/bin/test -e /sbin/nohup",
                        aRc=0),
                    exaMockCommand(f"nohup /bin/sh -c \"source {self.VMBACKUPENV_FILE} && vmbackup backup --localtooci 2> /dev/null \" &",
                        aRc=0),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()

        _options = self.mGetPayload()

        # Chose first dom0
        # NOTE change this for a complete payload like in jsondispatch
        # vmbackup unittest
        _options.jsonconf["dom0"] = _ebox.mReturnDom0DomUPair()[0][0]

        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "backup_host"
        with patch(
                'exabox.ovm.vmbackup.ebCluManageVMBackup.mDisableVMBackupCronJob',
                    return_value = True), patch(
                "exabox.ovm.csstep.cs_golden_backup.ebVMBackupOCI",
                    return_value = True), patch(
                "exabox.ovm.vmbackup.ebCluManageVMBackup.mInstallNewestVMBackupTool",
                    return_value = 0):
            self.assertEqual(0, _vmBackup.mExecuteOperation(_options))

    def test_mTriggerBackgrounBackupHost_success_ondemand_true(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/bin/test -e {self.VMBACKUPENV_FILE}",
                        aRc=0),
                    exaMockCommand(f"source {self.VMBACKUPENV_FILE}",
                        aRc=0),
                    exaMockCommand(f"/bin/test -e /sbin/nohup",
                        aRc=0),
                    exaMockCommand(f"/bin/sh -c \"source {self.VMBACKUPENV_FILE} && vmbackup backup --localtooci 2> /dev/null \"",
                        aRc=0),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()

        _options = self.mGetPayload()

        # Chose first dom0
        # NOTE change this for a complete payload like in jsondispatch
        # vmbackup unittest
        _options.jsonconf["dom0"] = _ebox.mReturnDom0DomUPair()[0][0]

        _options.ondemand = "true"

        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "backup_host"
        with patch(
                'exabox.ovm.vmbackup.ebCluManageVMBackup.mDisableVMBackupCronJob',
                    return_value = True), patch(
                "exabox.ovm.vmbackup.ebCluManageVMBackup.mInstallNewestVMBackupTool",
                    return_value = 0):
            self.assertEqual(0, _vmBackup.mExecuteOperation(_options))

    def test_mTriggerBackgrounBackupHost_error_no_dom0_in_payload_ondemand_false(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/bin/test -e {self.VMBACKUPENV_FILE}",
                        aRc=0),
                    exaMockCommand(f"source {self.VMBACKUPENV_FILE}",
                        aRc=0),
                    exaMockCommand(f"/bin/test -e /sbin/nohup",
                        aRc=0),
                    exaMockCommand(f"nohup /bin/sh -c \"source {self.VMBACKUPENV_FILE} && vmbackup backup\" &",
                        aRc=0),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()

        _options = self.mGetPayload()

        # Chose first dom0
        # NOTE change this for a complete payload like in jsondispatch
        # vmbackup unittest
        _options.jsonconf["vmboss"] = {}

        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "backup_host"
        self.assertEqual(1, _vmBackup.mExecuteOperation(_options))

    def test_mTriggerBackgrounBackupHost_error_on_dom0_command_ondemand_false(self):
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/bin/test -e {self.VMBACKUPENV_FILE}",
                        aRc=0),
                    exaMockCommand(f"source {self.VMBACKUPENV_FILE}",
                        aRc=0),
                    exaMockCommand(f"/bin/test -e /sbin/nohup",
                        aRc=0),
                    exaMockCommand(f"nohup \"source {self.VMBACKUPENV_FILE} && vmbackup backup &\"",
                        aRc=1),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()

        _options = self.mGetPayload()

        # Chose first dom0
        # NOTE change this for a complete payload like in jsondispatch
        # vmbackup unittest
        _options.jsonconf["vmboss"] = {}
        _options.jsonconf["vmboss"]["dom0"] = _ebox.mReturnDom0DomUPair()[0][0]

        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "backup_host"
        with patch(
                'exabox.ovm.vmbackup.ebCluManageVMBackup.mDisableVMBackupCronJob',
                return_value = 0):
            self.assertEqual(1, _vmBackup.mExecuteOperation(_options))

    @patch("exabox.ovm.vmbackup.ebVMBackupOCI")
    @patch("exabox.ovm.vmbackup.ebCluManageVMBackup.mCheckVMbackupInstalled")
    def test_mListOSSVMbackup_success_dom0(self,aMockIsInstalled, aMockOCI):

        # This is a real sample of how the osslist command stdout looks like
        _osslist_sample = (

'Version : ECS_MAIN_LINUX.X64_230401.0901'
''
'---------------------------------------------------------------------'
'OSS Backup (On objectstorage.r1.oracleiaas.com)'
'---------------------------------------------------------------------'
'{'
'    "ganesh-clu1-xvd8f1.client.exaclouddev.oraclevcn.com": ['
'        ['
'            "ganesh-clu1-xvd8f1.client.exaclouddev.oraclevcn.com.tar",'
'            "2023-04-07-08-23-32"'
'        ],'
'        ['
'            "ganesh-clu1-xvd8f1.client.exaclouddev.oraclevcn.com_SEQ10.tar",'
'            "2023-04-07-08-56-30"'
'        ],'
'        ['
'            "ganesh-clu1-xvd8f1.client.exaclouddev.oraclevcn.com_SEQ11.tar",'
'            "2023-04-07-08-56-44"'
'        ]'
'    ],'
'    "jorge-host-bpel61.client.exaclouddev.oraclevcn.com": ['
'        ['
'            "jorge-host-bpel61.client.exaclouddev.oraclevcn.com_SEQ11.tar",'
'            "2023-04-07-08-56-44"'
'        ],'
'        ['
'            "jorge-host-bpel61.client.exaclouddev.oraclevcn.com.tar",'
'            "2023-04-07-08-57-15"'
'        ]'
'    ]'
'}')

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",
                        aRc=1, aPersist=True),
                    exaMockCommand(f"/bin/test -e {self.VMBACKUPENV_FILE}",
                        aRc=0),
                ],
                [
                    exaMockCommand(f"source {self.VMBACKUPENV_FILE} ; vmbackup osslist",
                        aRc=0, aStdout=_osslist_sample),
                    exaMockCommand("/usr/bin/ps -fe| /bin/grep 'python-vmbackup' | /bin/grep -v grep",
                        aStdout="",
                        aRc=1),
                ],
                [
                    exaMockCommand("/usr/bin/ps -fe| /bin/grep 'python-vmbackup' | /bin/grep -v grep",
                        aStdout="",
                        aRc=1),
                ],
                [
                    exaMockCommand("/usr/bin/ps -fe| /bin/grep 'python-vmbackup' | /bin/grep -v grep",
                        aStdout="",
                        aRc=1),
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",
                        aRc=1, aPersist=True),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()

        _options = self.mGetPayload()

        # Chose first dom0
        # vmbackup unittest
        _options.jsonconf["reload"] = False
        _options.jsonconf["dom0"] = _ebox.mReturnDom0DomUPair()[0][0]
        _options.jsonconf["vmboss"] = {
            "vmboss_map": [
                {
                    "dom0": _ebox.mReturnDom0DomUPair()[0][0],
                    "domu": _ebox.mReturnDom0DomUPair()[0][1],
                    "customer_tenancy_ocid": "<the ocid of the customer tenancy ID>",
                    "vmboss_compartment": "vmboss_comp_<the ocid of the customer tenancy ID>",
                    "vmboss_metadata_bucket": "vmboss_metadata_bucket_<the ocid of the customer tenancy ID>",
                    "vmboss_bucket": "vmboss_bucket_<the ocid of the customer tenancy ID>_<ecra_clustername>",
                },
            ],
            "seq": "1"
        }

        self.mGetContext().mSetConfigOption('exabm', 'True')
        self.mGetContext().mSetConfigOption('kms_key_id', 'ocid.key.aaa')
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "list_oss"
        self.assertEqual(0, _vmBackup.mExecuteOperation(_options))

    @patch("exabox.ovm.vmbackup.ebVMBackupOCI")
    @patch("exabox.ovm.vmbackup.ebCluManageVMBackup.mCheckVMbackupInstalled")
    def test_mListOSSVMbackup_success_rackname(self, aMockIsInstalled, aMockOCI):

        # This is a real sample of how the osslist command stdout looks like
        _osslist_sample = (

'Version : ECS_MAIN_LINUX.X64_230401.0901'
''
'---------------------------------------------------------------------'
'OSS Backup (On objectstorage.r1.oracleiaas.com)'
'---------------------------------------------------------------------'
'{'
'    "ganesh-clu1-xvd8f1.client.exaclouddev.oraclevcn.com": ['
'        ['
'            "ganesh-clu1-xvd8f1.client.exaclouddev.oraclevcn.com.tar",'
'            "2023-04-07-08-23-32"'
'        ],'
'        ['
'            "ganesh-clu1-xvd8f1.client.exaclouddev.oraclevcn.com_SEQ10.tar",'
'            "2023-04-07-08-56-30"'
'        ],'
'        ['
'            "ganesh-clu1-xvd8f1.client.exaclouddev.oraclevcn.com_SEQ11.tar",'
'            "2023-04-07-08-56-44"'
'        ]'
'    ]'
'}')

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",
                        aRc=1, aPersist=True),
                    exaMockCommand(f"/bin/test -e {self.VMBACKUPENV_FILE}",
                        aRc=0),
                ],
                [
                    exaMockCommand(f"source {self.VMBACKUPENV_FILE} ; vmbackup osslist --vm",
                        aRc=0, aStdout=_osslist_sample),
                ],
                [
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",
                        aRc=1, aPersist=True),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()

        _options = self.mGetPayload()

        # Chose first dom0
        # vmbackup unittest
        _options.jsonconf["reload"] = False
        _options.jsonconf["dom0"] = None
        _options.jsonconf["vmboss"] = {
            "vmboss_map": [
                {
                    "dom0": _ebox.mReturnDom0DomUPair()[0][0],
                    "domu": _ebox.mReturnDom0DomUPair()[0][1],
                    "customer_tenancy_ocid": "<the ocid of the customer tenancy ID>",
                    "vmboss_compartment": "vmboss_comp_<the ocid of the customer tenancy ID>",
                    "vmboss_metadata_bucket": "vmboss_metadata_bucket_<the ocid of the customer tenancy ID>",
                    "vmboss_bucket": "vmboss_bucket_<the ocid of the customer tenancy ID>_<ecra_clustername>",
                },
            ],
            "seq": "1"
        }

        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "list_oss"
        self.assertEqual(0, _vmBackup.mExecuteOperation(_options))

    def test_mRestoreOSSVMbackup_missing_fields(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/bin/test -e {self.VMBACKUPENV_FILE}",
                        aRc=0),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()

        _options = self.mGetPayload()

        # Chose first dom0
        # NOTE change this for a complete payload like in jsondispatch
        # vmbackup unittest
        _options.jsonconf["vmboss"] = {}
        _options.jsonconf["vmboss"]["dom0"] = _ebox.mReturnDom0DomUPair()[0][0]

        _vmBackup = ebCluManageVMBackup(_ebox)
        self.mGetContext().mSetConfigOption('exabm', 'True')
        self.mGetContext().mSetConfigOption('kms_key_id', 'ocid.key.aaa')
        _options.vmbackup_operation = "restore_oss"
        with self.assertRaises(ExacloudRuntimeError):
            _vmBackup.mExecuteOperation(_options)

    @patch("exabox.ovm.vmbackup.ebVMBackupOCI.mSetupVMBackupDom0Cache")
    @patch("exabox.ovm.vmbackup.ebVMBackupOCI.mUploadCertificatesToDom0")
    @patch("exabox.ovm.vmbackup.ebVMBackupOCI")
    def test_mRestoreOSSVMbackup_success(self,
            aMagicSetupCache, aMagicPushCerts, aMagicVMBOCI):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/bin/test -e {self.VMBACKUPENV_FILE}",
                        aRc=0),
                    exaMockCommand(f"/bin/mkdir.*",
                        aRc=0),
                    exaMockCommand(f"/bin/test -e .*",
                        aRc=0),
                    exaMockCommand(f"/bin/cat .*",
                        aRc=0),
                    exaMockCommand(f"source {self.VMBACKUPENV_FILE}",
                        aRc=0),
                    exaMockCommand(f"source {self.VMBACKUPENV_FILE} ; vmbackup restore --vm .*  --loc oss --seq [0-9]+", aRc=0)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()

        _options = self.mGetPayload()

        # Chose first dom0
        # vmbackup unittest
        _options.jsonconf["vmboss"] = {
            "vmboss_map": [
                {
                    "dom0": _ebox.mReturnDom0DomUPair()[0][0],
                    "domu": _ebox.mReturnDom0DomUPair()[0][1],
                    "customer_tenancy_ocid": "<the ocid of the customer tenancy ID>",
                    "vmboss_compartment": "vmboss_comp_<the ocid of the customer tenancy ID>",
                    "vmboss_metadata_bucket": "vmboss_metadata_bucket_<the ocid of the customer tenancy ID>",
                    "vmboss_bucket": "vmboss_bucket_<the ocid of the customer tenancy ID>_<ecra_clustername>",
                },
            ],
            "seq": "1"
        }

        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "restore_oss"
        self.mGetContext().mSetConfigOption('exabm', 'True')
        self.mGetContext().mSetConfigOption('kms_key_id', 'ocid.key.aaa')
        self.assertEqual(0, _vmBackup.mExecuteOperation(_options))

    def test_mGetLocalVMBackupVersion(self):
        ebLogInfo("Running tests on ebCluManageVMBackup.mGetLocalVMBackupVersion")
        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)

        with patch('exabox.ovm.vmbackup.glob.glob',
                return_value = ["images/release-vmbackup-MAIN+251001.0901.tgz"]):
            _local_series, _local_date = _vmBackup.mGetLocalVMBackupVersion()
            self.assertEqual(_local_series, "MAIN")
            self.assertEqual(_local_date, "251001")

        with patch('exabox.ovm.vmbackup.glob.glob',
                return_value = ["images/release-vmbackup-25.2.2.1.5+250905.0159.tgz"]):
            _local_series, _local_date = _vmBackup.mGetLocalVMBackupVersion()
            self.assertEqual(_local_series, "25.2.2.1.5")
            self.assertEqual(_local_date, "250905")

    def test_mGetVMBackupVersion(self):
        ebLogInfo("Running tests on ebCluManageVMBackup.mGetVMBackupVersion")

        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand('source /opt/python-vmbackup/bin/set-vmbackup-env.sh; vmbackup version',
                        aStdout="ECS_25.2.2.1.5_LINUX.X64_250905.159\n")
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _results = []
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_dom0, get_gcontext()) as _node:
                _series, _date = _vmBackup.mGetVMBackupVersion(_node)
                self.assertEqual(_series, "25.2.2.1.5")
                self.assertEqual(_date, "250905")

    def test_mCheckRemoteProcessOngoingOneProcessPresent(self):
        ebLogInfo("Running tests on ebCluManageVMBackup.mCheckRemoteProcessOngoing")

        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/bin/ps -fe| /bin/grep 'python-vmbackup' | /bin/grep -v grep",
                        aStdout="216857 /opt/python-vmbackup/bin/python /opt/python-vmbackup/bin/vmbackup -h\n",
                        aRc=0),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _results = []
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_dom0, get_gcontext()) as _node:
                _results.append(_vmBackup.mCheckRemoteProcessOngoing(_node))

        self.assertEqual(_results, [True, True])

    def test_mCheckRemoteProcessOngoingNoProcess(self):
        ebLogInfo("Running tests on ebCluManageVMBackup.mCheckRemoteProcessOngoing")

        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/bin/ps -fe| /bin/grep 'python-vmbackup' | /bin/grep -v grep",
                        aStdout="",
                        aRc=1),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _results = []
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_dom0, get_gcontext()) as _node:
                _results.append(_vmBackup.mCheckRemoteProcessOngoing(_node))

        self.assertEqual(_results, [False, False])

    def test_mGetDom0BackupStatus_success(self):
        ebLogInfo("Running tests on ebCluManageVMBackup.mGetDom0BackupStatus")

        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options = self.mGetPayload()
        _options.jsonconf['dom0'] = "scaqab10adm01.us.oracle.com"

        _remote_file_content = {
            "GuestVMs": {
                "jorgeclu3vmboss-ur65p1.client.exaclouddev.oraclevcn.com": {
                    "CurrentStatus": "Failed",
                    "LatestSuccessfulSequenceNumber": "None",
                    "TimestampOfLastSuccessfulBackup": "None",
                    "NumberOfBackupsInOss": 0
                },
                "ganesh-clu1-xvd8f1.client.exaclouddev.oraclevcn.com": {
                    "CurrentStatus": "Failed",
                    "LatestSuccessfulSequenceNumber": "2",
                    "TimestampOfLastSuccessfulBackup": "2023-06-12-07-44-24",
                    "NumberOfBackupsInOss": 3
                },
                "golden-jfsal-rscoc1.client.exaclouddev.oraclevcn.com": {
                    "CurrentStatus": "Failed",
                    "LatestSuccessfulSequenceNumber": "0",
                    "TimestampOfLastSuccessfulBackup": "2023-06-21-21-18-05",
                    "NumberOfBackupsInOss": 1
                }
            },
            "CurrentBackupOperationCompleted": True
        }

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f'cat {_vmBackup.VMBACKUP_STATUS_FILE}', aRc=0,
                        aStdout=json.dumps(_remote_file_content)),
                    exaMockCommand("/usr/bin/ps -fe| /bin/grep 'python-vmbackup' | /bin/grep -v grep",
                        aStdout="",
                        aRc=1),
                ],
                [
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",
                        aRc=1, aPersist=True),
                    exaMockCommand("/usr/bin/ps -fe| /bin/grep 'python-vmbackup' | /bin/grep -v grep",
                        aStdout="",
                        aRc=1),
                ],
                [
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",
                        aRc=1, aPersist=True),
                    exaMockCommand("/usr/bin/ps -fe| /bin/grep 'python-vmbackup' | /bin/grep -v grep",
                        aStdout="",
                        aRc=1),
                ]
            ],
            self.mGetRegexLocal(): [
                [
                   exaMockCommand("/bin/ls *", aRc=0, aStdout="./vmbackup.conf", aPersist=True)
                ],
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _result = _vmBackup.mGetDom0BackupStatus(_options)
        _status = _vmBackup.mGetVMBackupData()

        self.assertEqual(_result, 0)
        self.assertEqual(_status.get("status"), json.dumps(_remote_file_content))

    def test_mGetDom0BackupStatus_error_no_file(self):
        ebLogInfo("Running tests on ebCluManageVMBackup.mGetDom0BackupStatus")

        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options = self.mGetPayload()
        _options.jsonconf['dom0'] = "scaqab10adm01.us.oracle.com"

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f'cat {_vmBackup.VMBACKUP_STATUS_FILE}', aRc=1, aStdout="\n"),
                    exaMockCommand("/usr/bin/ps -fe| /bin/grep 'python-vmbackup' | /bin/grep -v grep",
                        aStdout="",
                        aRc=1),
                ],
                [
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",
                        aRc=1, aPersist=True),
                    exaMockCommand("/usr/bin/ps -fe| /bin/grep 'python-vmbackup' | /bin/grep -v grep",
                        aStdout="",
                        aRc=1),
                ],
                [
                    exaMockCommand("/bin/test -e /opt/oracle/vmbackup/conf/vmbackup.conf",
                        aRc=1, aPersist=True),
                    exaMockCommand("/usr/bin/ps -fe| /bin/grep 'python-vmbackup' | /bin/grep -v grep",
                        aStdout="",
                        aRc=1),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _result = _vmBackup.mGetDom0BackupStatus(_options)
        _status = _vmBackup.mGetVMBackupData()

        self.assertEqual(_result, 1)

    def test_mGetDom0BackupStatus_error_no_dom0_in_payload(self):
        ebLogInfo("Running tests on ebCluManageVMBackup.mGetDom0BackupStatus")

        _ebox = self.mGetClubox()
        _vmBackup = ebCluManageVMBackup(_ebox)
        _options = self.mGetPayload()
        _options.jsonconf['dom0'] = ""

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f'command', aRc=1, aStdout="\n")
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _result = _vmBackup.mGetDom0BackupStatus(_options)
        _status = _vmBackup.mGetVMBackupData()

        self.assertEqual(_result, 2)

    @patch("exabox.ovm.vmbackup.ExaOCIFactory.get_oci_connector")
    @patch("exabox.ovm.vmbackup.ebVMBackupOCI")
    @patch("exabox.ovm.vmbackup.ebCluManageVMBackup.mSetVMBackupParameter")
    @patch("exabox.ovm.vmbackup.ebCluManageVMBackup.mCheckVMbackupInstalled")
    def test_mEnableOssVMBackupConfig(self, aMockCheckToolInstalled, aMockSetParam,
            aMockVMBOCI, aMockOcIConnector):


        ebLogInfo("Test - Enable VMbackup OSS config, all good")
        self.mGetContext().mSetConfigOption('vmbackup',
                {'enable_vmbackup_install': 'True'})

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("dummy", aRc=0),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _json = self.mGetPayload()
        _dom0_list = [_dom0 for _dom0, _ in _ebox.mReturnDom0DomUPair()]

        self.mGetContext().mSetConfigOption('kms_dp_endpoint',
                'https://avpga2q7aaay2-crypto.kms.r1.oracleiaas.com/')
        self.mGetContext().mSetConfigOption('kms_key_id',
                'ocid1.key.region1.sea.avpga2q7aaay2.abzwkljsfsyx4jznloy7g2zgermj4gsdpbkjwnrripzi5wcdbcp2xyws3baq')

        # Mock oci connector type
        aMockOcIConnector.return_value.__class__ = R1Connector
        aMockVMBOCI.return_value.mReturnDom0DomUPair = _ebox.mReturnDom0DomUPair

        # Mock successfull set_param call
        aMockSetParam.return_value = 0

        # Mock if the tool is installed
        aMockCheckToolInstalled.return_value = True

        _vmBackup = ebCluManageVMBackup(_ebox)
        _rc = _vmBackup.mEnableOssVMBackupConfig(_json)
        self.assertEqual(_rc, 0)

        # Make sure set_param is called
        self.assertEqual(aMockSetParam.call_count, 1)


    @patch("exabox.ovm.vmbackup.ebVMBackupOCI")
    @patch("exabox.ovm.vmbackup.ebCluManageVMBackup.mCheckVMbackupInstalled")
    @patch("exabox.ovm.vmbackup.ebCluManageVMBackup.mSetVMBackupParameter")
    def test_mEnableOssVMBackupConfig_no_crypto_endpoint(self, aMockSetParam,
            aMockIsToolInstalled, aMockVMBOCI):

        ebLogInfo("Test - Enable VMbackup OSS config, no crypto endpoint")
        self.mGetContext().mSetConfigOption('vmbackup',
                {'enable_goldvm_backup': "false"})

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("dummy", aRc=0),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        # Mock tool installed
        aMockIsToolInstalled.return_value = True

        _ebox = self.mGetClubox()
        _json = self.mGetPayload()
        _dom0_list = [_dom0 for _dom0, _ in _ebox.mReturnDom0DomUPair()]

        self.mGetContext().mSetConfigOption('kms_dp_endpoint','')
        self.mGetContext().mSetConfigOption('kms_key_id',
                'ocid1.key.region1.sea.avpga2q7aaay2.abzwkljsfsyx4jznloy7g2zgermj4gsdpbkjwnrripzi5wcdbcp2xyws3baq')

        _vmBackup = ebCluManageVMBackup(_ebox)
        with self.assertRaises(ExacloudRuntimeError):
            _vmBackup.mEnableOssVMBackupConfig(_json)

    @patch("exabox.ovm.vmbackup.ebVMBackupOCI")
    @patch("exabox.ovm.vmbackup.ebCluManageVMBackup.mSetVMBackupParameter")
    @patch("exabox.ovm.vmbackup.ebCluManageVMBackup.mCheckVMbackupInstalled")
    def test_mEnableOssVMBackupConfig_no_master_key_ocid(self, aMockCheckIsInstalled,
            aMockSetParam, aMockVMBOCI):

        ebLogInfo("Test - Enable OSS config, no master key ocid")
        self.mGetContext().mSetConfigOption('vmbackup',
                {'enable_goldvm_backup': "false"})

        _ebox = self.mGetClubox()
        _json = self.mGetPayload()
        _dom0_list = [_dom0 for _dom0, _ in _ebox.mReturnDom0DomUPair()]

        self.mGetContext().mSetConfigOption('kms_dp_endpoint',
                'https://avpga2q7aaay2-crypto.kms.r1.oracleiaas.com/')
        self.mGetContext().mSetConfigOption('kms_key_id', '')

        # Mock if tool is installed
        aMockCheckIsInstalled.return_value = True

        _vmBackup = ebCluManageVMBackup(_ebox)
        with self.assertRaises(ExacloudRuntimeError):
            _vmBackup.mEnableOssVMBackupConfig(_json)

    @patch("exabox.ovm.vmbackup.ebVMBackupOCI")
    @patch("exabox.ovm.vmbackup.ebCluManageVMBackup.mCheckVMbackupInstalled")
    @patch("exabox.ovm.vmbackup.ebCluManageVMBackup.mSetVMBackupParameter")
    def test_mEnableOssVMBackup_set_param_fails_crypto_endpoint(self, aMockSetParam,
            aMockIsToolInstalled, aMockVMBOCI):

        ebLogInfo("Test - Update backup config, set param fails crypto endpoint")
        self.mGetContext().mSetConfigOption('vmbackup',
                {'enable_goldvm_backup': "false"})

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("dummy", aRc=0),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        _json = self.mGetPayload()
        _dom0_list = [_dom0 for _dom0, _ in _ebox.mReturnDom0DomUPair()]

        self.mGetContext().mSetConfigOption('kms_dp_endpoint',
                'https://avpga2q7aaay2-crypto.kms.r1.oracleiaas.com/')
        self.mGetContext().mSetConfigOption('kms_key_id',
                'ocid1.key.region1.sea.avpga2q7aaay2.abzwkljsfsyx4jznloy7g2zgermj4gsdpbkjwnrripzi5wcdbcp2xyws3baq')

        # Mock error on set_param call
        aMockSetParam.return_value = [1]

        # Mock tool is installed
        aMockIsToolInstalled.return_value = True

        _vmBackup = ebCluManageVMBackup(_ebox)
        with self.assertRaises(ExacloudRuntimeError):
            _vmBackup.mEnableOssVMBackupConfig(_json)

        # Make sure set_param is called
        self.assertEqual(aMockSetParam.call_count, 1)


    def test_mRestoreLocalVMbackup_working(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0),
                    exaMockCommand(("source .*; vmbackup restore --vm .* --loc local "
                        "--seq 0 --restoreimage u01  --uuid .*"),aRc=0),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/Restore/.*/ossrestore_status.dat",aRc=0),
                    exaMockCommand("/bin/cat /EXAVMIMAGES/Restore/.*/ossrestore_status.dat",
                        aRc=0, aStdout="COMPLETEDSUCCESSFULLY\n"),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()

        # Use first pair
        _dom0, _domU = _ebox.mReturnDom0DomUPair()[0]
        _options = self.mGetPayload()
        _options.jsonconf = {
            "vmboss" : {
                "dom0": _dom0,
                "domu": _domU,
                "seq": 0,
                "image": "u01",
                "restart_vm": False
            }
        }
        _vmBackup = ebCluManageVMBackup(_ebox)

        self.assertEqual(0, _vmBackup.mRestoreLocalVMbackup(_options))

    def test_mRestoreLocalVMbackup_fail(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0),
                    exaMockCommand(("source .*; vmbackup restore --vm .* --loc local "
                        "--seq 0 --restoreimage u01  --uuid .*"),aRc=0),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/Restore/.*/ossrestore_status.dat",aRc=0),
                    exaMockCommand("/bin/cat /EXAVMIMAGES/Restore/.*/ossrestore_status.dat",
                        aRc=0, aStdout="FAILED\n"),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()

        # Use first pair
        _dom0, _domU = _ebox.mReturnDom0DomUPair()[0]
        _options = self.mGetPayload()
        _options.jsonconf = {
            "vmboss" : {
                "dom0": _dom0,
                "domu": _domU,
                "seq": 0,
                "image": "u01",
                "restart_vm": False
            }
        }
        _vmBackup = ebCluManageVMBackup(_ebox)

        #self.assertEqual(1, _vmBackup.mRestoreLocalVMbackup(_options))
        self.assertRaises(ExacloudRuntimeError,
            lambda : _vmBackup.mRestoreLocalVMbackup(_options))

    def test_mRestoreLocalVMbackup_working_no_image(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0),
                    exaMockCommand(("source .*; vmbackup restore --vm .* --loc local "
                        "--seq 0.*--uuid .*"),aRc=0),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/Restore/.*/ossrestore_status.dat",aRc=0),
                    exaMockCommand("/bin/cat /EXAVMIMAGES/Restore/.*/ossrestore_status.dat",
                        aRc=0, aStdout="COMPLETEDSUCCESSFULLY\n"),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()

        # Use first pair
        _dom0, _domU = _ebox.mReturnDom0DomUPair()[0]
        _options = self.mGetPayload()
        _options.jsonconf = {
            "vmboss" : {
                "dom0": _dom0,
                "domu": _domU,
                "seq": 0,
                "image": "",
                "restart_vm": False
            }
        }
        _vmBackup = ebCluManageVMBackup(_ebox)

        self.assertEqual(0, _vmBackup.mRestoreLocalVMbackup(_options))

    def test_mRestoreLocalVMbackup_working_no_image_yes_restart_no_seq(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0),
                    exaMockCommand(("source .*; vmbackup restore --vm .* --loc local.*"
                        "--restart-vm --uuid .*"),aRc=0),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/Restore/.*/ossrestore_status.dat",aRc=0),
                    exaMockCommand("/bin/cat /EXAVMIMAGES/Restore/.*/ossrestore_status.dat",
                        aRc=0, aStdout="COMPLETEDSUCCESSFULLY\n"),
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()

        # Use first pair
        _dom0, _domU = _ebox.mReturnDom0DomUPair()[0]
        _options = self.mGetPayload()
        _options.jsonconf = {
            "vmboss" : {
                "dom0": _dom0,
                "domu": _domU,
                "seq": "",
                "image": "",
                "restart_vm": True
            }
        }
        _vmBackup = ebCluManageVMBackup(_ebox)

        self.assertEqual(0, _vmBackup.mRestoreLocalVMbackup(_options))

    @patch("exabox.ovm.vmbackup.ExaOCIFactory.get_oci_connector")
    def test_mCheckNodeCanReachOci_fails(self, aMagicConnection):
        """
        Tests mCheckNodeCanReachOci
        """

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test.*",aRc=0, aPersist=True),
                    exaMockCommand('curl --local-port 49152-65535 https://objectstorage.r1.oracleiaas.com:443/tmp -vvv 2>&1 --max-time 10 | /bin/grep -E "^\* Connected to"',aRc=1, aPersist=True),
                ]
            ]
        }

        aMagicConnection.return_value.__class__ = R1Connector
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()

        # Use first pair
        _dom0, _domU = _ebox.mReturnDom0DomUPair()[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        self.assertEquals(False, _vmBackup.mCheckNodeCanReachOci(_dom0))

    @patch("exabox.ovm.vmbackup.ExaOCIFactory.get_oci_connector")
    def test_mCheckNodeCanReachOci_works(self, aMagicConnection):
        """
        Tests mCheckNodeCanReachOci
        """

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test.*",aRc=0, aPersist=True),
                    exaMockCommand('curl --local-port 49152-65535 https://objectstorage.r1.oracleiaas.com:443/tmp -vvv 2>&1 --max-time 10 | /bin/grep -E "^\* Connected to"',aRc=1),
                    exaMockCommand('curl --local-port 49152-65535 https://objectstorage.r1.oracleiaas.com:443/tmp -vvv 2>&1 --max-time 10 | /bin/grep -E "^\* Connected to"',aRc=0, aStdout="* Connected to auth.r1.oracleiaas.com (140.91.2.217) port 443 (#0)\n"),
                ]
            ]
        }

        aMagicConnection.return_value.__class__ = R1Connector
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _options = self.mGetPayload()

        # Use first pair
        _dom0, _domU = _ebox.mReturnDom0DomUPair()[0]
        _vmBackup = ebCluManageVMBackup(_ebox)
        self.assertEquals(True, _vmBackup.mCheckNodeCanReachOci(_dom0))

    def test_mDisableOSSVMBackupConfig(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebCluManageVMBackup.mDisableOSSVMBackupConfig")

        vmbackupinstance = ebCluManageVMBackup(self.mGetClubox())
        options = get_gcontext().mGetArgsOptions()
        options.jsonconf = {"mock_key": "mock_value"}

        with patch('exabox.ovm.vmbackup.connect_to_host'),\
             patch('exabox.ovm.vmbackup.ebCluManageVMBackup.mCheckRemoteProcessOngoing', return_value=True):
             self.assertEqual(vmbackupinstance.mDisableOSSVMBackupConfig(options,[["mockdom0","mockdomu"]]), None)

        with patch('exabox.ovm.vmbackup.connect_to_host'),\
             patch('exabox.ovm.vmbackup.ebCluManageVMBackup.mCheckRemoteProcessOngoing', return_value=False),\
             patch('exabox.ovm.vmbackup.ebCluManageVMBackup.mSetVMBackupParameter', side_effect=[1,0]):
             self.assertRaises(ExacloudRuntimeError, vmbackupinstance.mDisableOSSVMBackupConfig, options, [["mockdom0","mockdomu"]])
             self.assertEqual(vmbackupinstance.mDisableOSSVMBackupConfig(options,[["mockdom0","mockdomu"]]), 0)

        with patch('exabox.ovm.vmboci.ebVMBackupOCI.mParseCustomerValues'),\
             patch('exabox.ovm.vmboci.ebVMBackupOCI.mIsForceUsersPrincipalsSet', return_value=False),\
             patch('exabox.ovm.vmboci.ExaOCIFactory'),\
             patch('exabox.ovm.vmboci.ExaOCIFactory.get_identity_client'),\
             patch('exabox.ovm.vmboci.ebVMBackupOCI.mGetTenancyOcid', return_value="ocid.mock.tenanacy"),\
             patch('exabox.ovm.vmboci.ebVMBackupOCI.mGetVMBackupCompartmentId', return_value=("ocid.mockcompartment.vmboss","ocid.parentmockcompartment.vmboss")),\
             patch('exabox.ovm.vmboci.ebVMBackupOCI.mGetVMBossMasterKeyOcid', return_value="ocid.mock.masterkey"),\
             patch('exabox.ovm.vmboci.ExaOCIFactory.get_secrets_client'),\
             patch('exabox.ovm.vmboci.ExaOCIFactory.get_object_storage_client'),\
             patch('exabox.ovm.vmboci.ebVMBackupOCI.mGetVMBossOSSNamespace', return_value="mockvmbossnamespace"),\
             patch('exabox.ovm.vmbackup.ebVMBackupOCI.mReturnDom0DomUPair', return_value=[["mockdom0","mockdomu"]]),\
             patch('exabox.ovm.vmbackup.connect_to_host'),\
             patch('exabox.ovm.vmbackup.ebCluManageVMBackup.mCheckRemoteProcessOngoing', return_value=False),\
             patch('exabox.ovm.vmbackup.ebCluManageVMBackup.mSetVMBackupParameter', return_value=0):
             self.assertEqual(vmbackupinstance.mDisableOSSVMBackupConfig(options), 0)

        ebLogInfo("Unit test on ebCluManageVMBackup.mDisableOSSVMBackupConfig completed successfully.")

    @patch("exabox.core.Node.exaBoxNode.mReadFile")
    def test_mExascaleEDVbackup(self, mock_mReadFile):

        _vm_json = """{ "backup_type": "Legacy", "exascale_backup_vault": "", "source_vm_images": "Exascale", "exascale_images_vault": "xsvlt-19789-sys-image-00", "exascale_retention_num": 2, "exascale_ers_ip_port": "10.0.163.167:5052"}"""
        mock_mReadFile.return_value = _vm_json
        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh",aRc=0, aPersist=True),
                    exaMockCommand(f"/bin/test -e *", aRc=0, aPersist=True),
                    exaMockCommand(f"bin/scp *", aRc=0, aPersist=True),
                    exaMockCommand(f"/bin/rm -rf /opt/oracle/vmbackup/conf/*", aRc=0, aPersist=True),
                    exaMockCommand(f"/bin/cat /opt/oracle/vmbackup/conf/*", aRc=0, aPersist=True, aStdout=_vm_json),
                ],
                [
                    exaMockCommand(f"/bin/test -e *", aRc=0, aPersist=True),
                    exaMockCommand(f"/bin/rm -rf /opt/oracle/vmbackup/conf/*", aRc=0, aPersist=True),
                    exaMockCommand(f"bin/scp *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /opt/python-vmbackup/bin/set-vmbackup-env.sh", aRc=0, aPersist=True),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh", aRc=0, aPersist=True),
                    exaMockCommand("source /opt/python-vmbackup/bin/set-vmbackup-env.sh; vmbackup backup --vm *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /EXAVMIMAGES/Backup/OSSMetadata/ossbackup_status.json", aRc=0, aPersist=True)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ebox.mSetEnableKVM(True)

        _options = copy.deepcopy(_ebox.mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _vmBackup = ebCluManageVMBackup(_ebox)
        _options.vmbackup_operation = "exascale_edv_backup"
        self.assertEqual(_vmBackup.mExascaleEDVbackup(_options), 0)

        ebLogInfo("Unit test on ebCluManageVMBackup.mExascaleEDVbackup completed successfully.")

def suite():
    """
    This method ensures the execution in the intended order of the tests.
    """
    suite = unittest.TestSuite()

    suite.addTest(ebTestNode('test_mExecuteOperation'))
    suite.addTest(ebTestNode('test_mExecuteOperation_enable'))
    suite.addTest(ebTestNode('test_mExecuteOperation_enable_error'))
    suite.addTest(ebTestNode('test_mExecuteOperation_disable'))
    suite.addTest(ebTestNode('test_mExecuteOperation_disable_error'))
    suite.addTest(ebTestNode('test_mExecuteOperation_setparam_back_not_enabled'))
    suite.addTest(ebTestNode('test_mExecuteOperation_setparam'))
    suite.addTest(ebTestNode('test_mExecuteOperation_getparam_back_not_enabled'))
    suite.addTest(ebTestNode('test_mExecuteOperation_getparam'))
    suite.addTest(ebTestNode('test_mExecuteOperation_install_jsonconf_none'))
    suite.addTest(ebTestNode('test_mExecuteOperation_install'))
    suite.addTest(ebTestNode('test_mRecordError'))
    suite.addTest(ebTestNode('test_mExecuteOperation_backup'))
    suite.addTest(ebTestNode('test_mExecuteOperation_backup_error'))
    suite.addTest(ebTestNode('test_mExecuteOperation_restore'))
    suite.addTest(ebTestNode('test_mExecuteOperation_restore_node_vmname'))
    suite.addTest(ebTestNode('test_mExecuteOperation_restore_source_valid'))
    suite.addTest(ebTestNode('test_mExecuteOperation_restore_source_backup'))
    suite.addTest(ebTestNode('test_mExecuteOperation_restore_source_restore_fail'))
    suite.addTest(ebTestNode('test_mExecuteOperation_restore_json_none'))
    suite.addTest(ebTestNode('test_mExecuteOperation_restore_json_conf'))
    suite.addTest(ebTestNode('test_mExecuteOperation_patch'))
    suite.addTest(ebTestNode('test_mExecuteOperation_list'))
    suite.addTest(ebTestNode('test_mExecuteOperation_mCleanAllVMbackup'))
    suite.addTest(ebTestNode('test_mExecuteOperation_mCleanAllVMbackup_else'))
    suite.addTest(ebTestNode('test_mExecuteOperation_mSetSSHDOptions'))
    suite.addTest(ebTestNode('test_mExecuteOperation_mSetSSHDOptions_error'))
    suite.addTest(ebTestNode('test_mExecuteOperation_mSetVMBackupCronJob'))
    suite.addTest(ebTestNode('test_mExecuteOperation_mSetVMBackupCronJob_error1'))
    suite.addTest(ebTestNode('test_mExecuteOperation_list_vmbackup_install'))
    suite.addTest(ebTestNode('test_mExecuteOperation_list_vmbackup_install_pass'))
    suite.addTest(ebTestNode('test_mCleanVMbackup'))
    suite.addTest(ebTestNode('test_mTriggerBackgrounBackupHost_success_ondemand_false'))
    suite.addTest(ebTestNode('test_mTriggerBackgrounBackupHost_error_no_dom0_in_payload_ondemand_false'))
    suite.addTest(ebTestNode('test_mTriggerBackgrounBackupHost_error_on_dom0_command_ondemand_false'))
    suite.addTest(ebTestNode('test_mTriggerBackgrounBackupHost_success_ondemand_true'))
    suite.addTest(ebTestNode('test_mListOSSVMbackup_success_dom0'))
    suite.addTest(ebTestNode('test_mListOSSVMbackup_success_rackname'))
    suite.addTest(ebTestNode('test_mRestoreOSSVMbackup_missing_fields'))
    suite.addTest(ebTestNode('test_mRestoreOSSVMbackup_success'))
    suite.addTest(ebTestNode('test_mGetLocalVMBackupVersion'))
    suite.addTest(ebTestNode('test_mGetVMBackupVersion'))
    suite.addTest(ebTestNode('test_mCheckRemoteProcessOngoingOneProcessPresent'))
    suite.addTest(ebTestNode('test_mCheckRemoteProcessOngoingNoProcess'))
    suite.addTest(ebTestNode('test_mGetDom0BackupStatus_success'))
    suite.addTest(ebTestNode('test_mGetDom0BackupStatus_error_no_file'))
    suite.addTest(ebTestNode('test_mGetDom0BackupStatus_error_no_dom0_in_payload'))
    suite.addTest(ebTestNode('test_mEnableOssVMBackupConfig'))
    suite.addTest(ebTestNode('test_mEnableOssVMBackupConfig_no_crypto_endpoint'))
    suite.addTest(ebTestNode('test_mEnableOssVMBackupConfig_no_master_key_ocid'))
    suite.addTest(ebTestNode('test_mEnableOssVMBackup_set_param_fails_crypto_endpoint'))
    suite.addTest(ebTestNode('test_mRestoreLocalVMbackup_working'))
    suite.addTest(ebTestNode('test_mRestoreLocalVMbackup_fail'))
    suite.addTest(ebTestNode('test_mRestoreLocalVMbackup_working_no_image'))
    suite.addTest(ebTestNode('test_mRestoreLocalVMbackup_working_no_image_yes_restart_no_seq'))
    suite.addTest(ebTestNode('test_mCheckNodeCanReachOci_fails'))
    suite.addTest(ebTestNode('test_mCheckNodeCanReachOci_works'))
    suite.addTest(ebTestNode('test_mDisableOSSVMBackupConfig'))
    suite.addTest(ebTestNode('test_mExascaleEDVbackup'))

    #suite.addTest(ebTestNode('test_mExecuteOperation_restore_with_node'))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suite())
