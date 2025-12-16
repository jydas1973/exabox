#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/vmgi_install/cs_createuser/tests_createuser.py /main/7 2025/11/08 00:10:46 jfsaldan Exp $
#
# tests_createuser.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_createuser.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    10/20/25 - Bug 38518160 - EXADB-XS Y25W41/41 | EXACLOUD CREATE
#                           USERS STEP TAKES 1.5 MINUTES TO FINISH MAKING ECRA
#                           TO LAST 2 MINUTES | EXPLORE OPTIONS TO REDUCE IT TO
#                           BE 1 MINUTE AT MOST
#    hgaldame    10/11/24 - 37160302 - exacc:gen2: resilent fix to create user
#                           and groups when oeda does not create them
#    aararora    07/22/24 - Bug 36864046: Cleanup ssh directory for opc user
#                           during undo step of create user
#    gparada     05/03/23 - Fix class constructor params
#    jesandov    06/21/22 - Creation
#


import unittest

import re
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.ovm.csstep.cs_util import csUtil
from exabox.ovm.csstep.cs_base import CSBase
from exabox.log.LogMgr import ebLogError, ebLogInfo
import warnings
from exabox.ovm.clumisc import ebSubnetSet, ebMigrateUsersUtil

class TestCSBase(CSBase):
    def doExecute(self, aExaBoxCluCtrlObj, aOptions, steplist):
        pass
    def undoExecute(self, aExaBoxCluCtrlObj, aOptions, aStepList):
        pass

class ebTestCluControlCreateUsers(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)

        self.mGetClubox(self).mSetOciExacc(True)

        for _, _domU in self.mGetClubox(self).mReturnDom0DomUPair():
            self.mGetClubox(self).mGetExadataImagesMap()[_domU] = "23.4.1"

            _ctx = self.mGetContext(self)
            if _ctx.mCheckRegEntry('_natHN_' + _domU):
                _natdomU = _ctx.mGetRegEntry('_natHN_' + _domU)
                self.mGetClubox(self).mGetExadataImagesMap()[_natdomU] = "23.4.1"

    def test_000_mUpdateUserConfiguration(self):

        _configFile = os.path.join(self.mGetUtil().mGetResourcesPath(), "user_config_file.json")
        _userJson = self.mGetResourcesJsonFile("user_config_file.json")
        self.mGetClubox().mGetCtx().mSetConfigOption("user_config_file", _configFile)

        # Prepare Mock Commands
        _cmds = {}
        self.mPrepareMockCommands(_cmds)

        # Patch the users
        self.mGetClubox().mUpdateUserConfiguration()

        # Verify the users
        for _name, _info in _userJson.items():

            if "uid" in _info:
                _cfg = self.mGetClubox().mGetUsers().mGetUserByName(_name)
                if _cfg:
                    self.assertEqual(str(_cfg.mGetUserId()), str(_info["uid"]))

            if "gid" in _info:
                _cfg = self.mGetClubox().mGetGroups().mGetGroupByName(_name)
                if _cfg:
                    self.assertEqual(str(_cfg.mGetGroupId()), str(_info["gid"]))

        # Export XML
        self.mGetClubox().mSaveXMLClusterConfiguration()
        ebLogInfo(f'ebCluCtrl: Saved patched Cluster Config: {self.mGetClubox().mGetPatchConfig()}')

    def test_001_mRemapUserGroup_original(self):

        self.mGetClubox().mGetCtx().mSetConfigOption("user_config_file", "this_file_not_exists")
        _passwd = self.mGetResourcesTextFile("passwd.txt")
        _group = self.mGetResourcesTextFile("group.txt")
        _dbcli = self.mGetResourcesTextFile("dbcli.txt")
        _dbcliDom0 = f"{_dbcli}\nesnpStatus:    running"

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("cat.*passwd.*sysadmin", aStdout="sysadmin", aPersist=True),
                    exaMockCommand("cat.*shadow.*sysadmin", aStdout="sysadmin", aPersist=True),
                    exaMockCommand("cat.*group.*sysadmin", aStdout="sysadmin", aPersist=True),

                    exaMockCommand("cat.*passwd.*exacloud", aStdout="exacloud", aPersist=True),
                    exaMockCommand("cat.*shadow.*exacloud", aStdout="exacloud", aPersist=True),
                    exaMockCommand("cat.*group.*exacloud", aStdout="exacloud", aPersist=True),

                    exaMockCommand("cat.*passwd.*3000", aStdout="oracle,5000\ngrid,4000"),
                    exaMockCommand("cat.*group.*4000000", aStdout="dba,3500"),
                    exaMockCommand("dbmcli -e list dbserver detail", aStdout=_dbcli, aPersist=True),

                    # Migrate groups
                    exaMockCommand("test.*migrate_ids.sh"),
                    exaMockCommand("cat /etc/group", aStdout=_group, aPersist=True),
                    exaMockCommand("migrate_ids.sh -gid oinstall 2005"),
                    exaMockCommand("migrate_ids.sh -gid sysadmin 88889"),
                    exaMockCommand("migrate_ids.sh -gid exacloud 2007"),

                    # Migrate users
                    exaMockCommand("test.*migrate_ids.sh"),
                    exaMockCommand("cat /etc/passwd", aStdout=_passwd, aPersist=True),
                    exaMockCommand("migrate_ids.sh -uid sysadmin 2004"),
                    exaMockCommand("migrate_ids.sh -uid exacloud 2005"),

                    exaMockCommand("dbmcli -e list dbserver detail", aStdout=_dbcli),
                ],
                [
                    exaMockCommand("imageinfo -version", aStdout="22.2.1"),
                ],
                [
                    exaMockCommand("imageinfo -version", aStdout="22.2.1"),
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    #exaMockCommand("dbmcli -e list dbserver detail", aStdout=_dbcliDom0, aPersist=True),
                    exaMockCommand("dbmcli -e list dbserver detail", aStdout=_dbcli, aPersist=True),
                    exaMockCommand("cat.*passwd.*", aPersist=True),
                    exaMockCommand("cat.*group.*", aPersist=True)
                ],
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _remapUtil = ebMigrateUsersUtil(self.mGetClubox())
        _remapUtil.mExecuteRemap()

    def test_002_mRemapUserGroup_user_config_file(self):

        _configFile = os.path.join(self.mGetUtil().mGetResourcesPath(), "user_config_file.json")
        _userJson = self.mGetResourcesJsonFile("user_config_file.json")
        self.mGetClubox().mGetCtx().mSetConfigOption("user_config_file", _configFile)

        _passwd = self.mGetResourcesTextFile("passwd.txt")
        _group = self.mGetResourcesTextFile("group.txt")
        _dbcli = self.mGetResourcesTextFile("dbcli.txt")
        _dbcliDom0 = f"{_dbcli}\nesnpStatus:    running"

        _mock_cmd_resilent_create = [
            exaMockCommand(f'/bin/cat /etc/group', aStdout=_group, aRc=0, aPersist=True),
            exaMockCommand(f'/bin/cat /etc/passwd', aStdout=_passwd, aRc=0, aPersist=True),
            exaMockCommand("dbmcli -e list dbserver detail", aStdout=_dbcli, aPersist=True),

            # Migrate groups
            exaMockCommand("test.*migrate_ids.sh"),
            exaMockCommand("cat /etc/group", aStdout=_group, aPersist=True),
            exaMockCommand("migrate_ids.sh -gid asmdba 1527"),
            exaMockCommand("migrate_ids.sh -gid asmoper 54328"),
            exaMockCommand("migrate_ids.sh -gid asmadmin 1999945824"),
            exaMockCommand("migrate_ids.sh -gid fuse 34563"),
            exaMockCommand("migrate_ids.sh -gid racoper 495509"),
            exaMockCommand("migrate_ids.sh -gid sysadmin 88889"),

            # Migrate users
            exaMockCommand("test.*migrate_ids.sh"),
            exaMockCommand("cat /etc/passwd", aStdout=_passwd, aPersist=True),
            exaMockCommand("migrate_ids.sh -uid oracle 30181"),
            exaMockCommand("migrate_ids.sh -uid opc 495637"),
            exaMockCommand("migrate_ids.sh -uid sysadmin 2004"),
            exaMockCommand("migrate_ids.sh -uid grid 195590"),

            exaMockCommand("dbmcli -e list dbserver detail", aStdout=_dbcli),
        ]
    
        for _name, _configU in _userJson.items():
            if "gid" in _configU:
                _mock_cmd_resilent_create.append(exaMockCommand(f'/bin/cat /etc/group | grep', aRc=1, aPersist=True))
                _mock_cmd_resilent_create.append(exaMockCommand(f"/usr/sbin/groupadd", aRc=0, aPersist=True))

            if "uid" in _configU:
                _mock_cmd_resilent_create.append(exaMockCommand(f'/bin/cat /etc/passwd | grep', aRc=1, aPersist=True))
                _mock_cmd_resilent_create.append(exaMockCommand(f'/bin/cat /etc/shadow | grep', aRc=1, aPersist=True))
                _mock_cmd_resilent_create.append(exaMockCommand(f"/usr/sbin/useradd", aRc=0, aPersist=True))

        _mock_cmd_resilent_create.append(exaMockCommand("dbmcli -e list dbserver detail", aStdout=_dbcli, aPersist=True))

        _cmds = {
            self.mGetRegexVm(): [
                _mock_cmd_resilent_create,
                [
                    exaMockCommand("imageinfo -version", aStdout="22.2.1"),
                ],
                [
                    exaMockCommand("imageinfo -version", aStdout="22.2.1"),
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("dbmcli -e list dbserver detail", aStdout=_dbcliDom0, aPersist=True),
                ]
            ]
        }
        #Init new Args 
        self.mPrepareMockCommands(_cmds)

        _remapUtil = ebMigrateUsersUtil(self.mGetClubox())
        _remapUtil.mExecuteRemap()

    def test_003_mRemoveOpcSSHDirectory(self):

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/rm -rf /home/opc/.ssh", aRc=0),
                ],
                [
                    exaMockCommand("/bin/rm -rf /home/opc/.ssh", aRc=0),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _cs_base = TestCSBase()
        _cs_base.mDeleteOpcSSHDirectory(self.mGetClubox())

    def test_mLockDBMUsers(self):
        """
        Helper to test mLockDBMUsers
        """

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 scaqab10adm0.*", aRc=0),
                ],
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("echo dbmadmin:$(openssl rand -base64 32) | chpasswd", aRc=0),
                    exaMockCommand("passwd -l dbmadmin", aRc=0),
                    exaMockCommand("echo dbmmonitor:$(openssl rand -base64 32) | chpasswd", aRc=0),
                    exaMockCommand("passwd -l dbmmonitor", aRc=0),
                    exaMockCommand("echo dbmsvc:$(openssl rand -base64 32) | chpasswd", aRc=0),
                    exaMockCommand("passwd -l dbmsvc", aRc=0),
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("echo dbmadmin:$(openssl rand -base64 32) | chpasswd", aRc=0),
                    exaMockCommand("passwd -l dbmadmin", aRc=0),
                    exaMockCommand("echo dbmmonitor:$(openssl rand -base64 32) | chpasswd", aRc=0),
                    exaMockCommand("passwd -l dbmmonitor", aRc=0),
                    exaMockCommand("echo dbmsvc:$(openssl rand -base64 32) | chpasswd", aRc=0),
                    exaMockCommand("passwd -l dbmsvc", aRc=0),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        self.assertEqual(None, _ebox.mLockDBMUsers())

if __name__ == '__main__':
    unittest.main(warnings='ignore')


# end of file
