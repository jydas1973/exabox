#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/exascale/tests_escli_util.py pbellary_bug-38972840/2 2026/02/20 13:08:38 pbellary Exp $
#
# tests_escli_util.py
#
# Copyright (c) 2022, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_escli_util.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    shapatna    02/10/26 - Enh: 38900613 - EXACLOUD SHOULD USE THE JSON FORMAT
#                           OUTPUT FOR ALL ESCLI GET COMMANDS
#    siyarlag    02/05/26 - Updating tests for mCreateEsWalletUser
#    pbellary    01/06/26 - Codex UT enhancement
#    pbellary    07/15/25 - Enh 37980305 - EXACLOUD TO SUPPORT CHANGE OF VM BACKUP STORAGE FROM LOCAL TO EXASCALE STORAGE (EXISTING CLUSTERS)
#    pbellary    05/21/25 - Enh 37698277 - EXASCALE: CREATE SERVICE FLOW TO SUPPORT VM STORAGE ON EDV OF IMAGE VAULT 
#    pbellary    04/16/25 - Enh 37842812 - EXASCALE: REFACTOR ACFS CREATION DURING CREATE SERVICE
#    pbellary    04/16/25 - Creation
#
import re
import json
import copy
import unittest
from unittest import mock
import hashlib
from types import SimpleNamespace
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.csstep.exascale.escli_util import *
from exabox.core.Context import get_gcontext
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
import warnings

EXASCALE_PAYLOAD = """ 
{
   "exascale":{
      "exascale_cluster_name":"sea2d2cl37541fe175f7847febc200f6b51aa9cb3clu01ers",
      "storage_pool":{
         "name":"hcpool",
         "gb_size":"10240"
      },
      "db_vault":{
         "name":"vault1clu02",
         "gb_size":10
      },
      "ctrl_network":{
         "ip":"10.0.130.110",
         "port":"5052",
         "name":"sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
      }
    },
    "exadataInfraId": "etf_infra_230603_111"
}
"""

VAULT_PAYLOAD = """
{
    "db_vault":{
        "name":"vault1clu02",
        "gb_size":10
    },
    "ctrl_network":{
        "ip":"10.0.130.110",
        "port":"5052",
        "name":"sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
    }
}
"""

class ebTestEscliUtil(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestEscliUtil, self).setUpClass(aGenerateDatabase = True, aUseOeda = True)
        self.mGetClubox(self).mSetUt(True)
        warnings.filterwarnings("ignore")

    def test_mGetUser(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json lsuser", aRc=0, aStdout='{"data":[{"id":"gridiad1046clu040a1"}]}', aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _giclusterName = _escli.mGetUser(_cell, "iad1046clu040a1", _options)
        self.assertEqual(_giclusterName, "gridiad1046clu040a1")   
        ebLogInfo("Unit test on ebEscliUtils.py:mGetUser successful")

    def test_mGetEDVInitiator(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]
        _dom0_short_name = "scaqab10adm01"

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json lsinitiator --attributes id,hostName", aRc=0, aStdout='{"data":[{"id":"a3311f85-8414-ac62-a331-1f858414ac62","attributes":{"hostName":"scaqab10adm01"}}]}', aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _initiatorId = _escli.mGetEDVInitiator(_cell, _dom0_short_name, _options)
        self.assertEqual(_initiatorId, "a3311f85-8414-ac62-a331-1f858414ac62")   
        ebLogInfo("Unit test on ebEscliUtils.py:mGetUser successful")

    def test_mGetERSEndpoint(self):
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _escli = ebEscliUtils(_ebox)
        _ctrl_ip, _ctrl_port = _escli.mGetERSEndpoint(_options)
        self.assertEqual(_ctrl_ip, "10.0.130.110")
        self.assertEqual(_ctrl_port, "5052")
        ebLogInfo("Unit test on ebEscliUtils.py:mGetERSEndpoint successful")

    def test_mGetClusterID(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json lsinitiator --attributes giClusterName,giClusterId", aRc=0, aStdout='{"data":[{"attributes":{"giClusterName":"club086e35-128","giClusterId":"9e827518-8a9f-5fd9-ffbe-c2ae1c46734c"}}]}', aPersist=True)
                            ],
                            [
                                exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json lsuser", aRc=0, aStdout='{"data":[{"id":"gridclub086e35-128"}]}', aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _giclusterName, _giClusterId = _escli.mGetClusterID(_cell, _options)
        self.assertEqual(_giclusterName, "gridclub086e35-128")
        self.assertEqual(_giClusterId, "9e827518-8a9f-5fd9-ffbe-c2ae1c46734c")   

        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json lsvolume --attributes id,vault,name,owners", aRc=0, aStdout='{"data":[{"id":"2:b4d00303b12f46d6a31b4a5339395cd3","attributes":{"vault":"@vault1clu02","name":"acfs_gridclub086e35-128","owners":"admin"}}]}', aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _vol_id, _owner = _escli.mGetVolumeID(_cell, "acfs_gridclub086e35-128", _options)
        self.assertEqual(_vol_id, "2:b4d00303b12f46d6a31b4a5339395cd3")
        self.assertEqual(_owner, "admin")

    def test_mGetVolumeIDP02(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json lsvolume --attributes id,vault,name,owners", aRc=0, aStdout='{"data":[{"id":"2:b4d00303b12f46d6a31b4a5339395cd3","attributes":{"vault":"@image","name":"acfs_gridclub086e35-128","owners":"admin"}}]}', aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _vol_id, _owner = _escli.mGetVolumeID(_cell, "acfs_gridclub086e35-128", _options, aVaultName="image")
        self.assertEqual(_vol_id, "2:b4d00303b12f46d6a31b4a5339395cd3")
        self.assertEqual(_owner, "admin")

    def test_mGetVolumeID_vmbackup_restore_suffix(self):
        # Auto-generated test for mGetVolumeID
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json lsvolume --attributes id,vault,name,owners", aRc=0, aStdout='{"data":[{"id":"4:aa11bb22cc33dd44ee55","attributes":{"vault":"@vault1clu02","name":"acfs_gridclub086e35-128_vmbackup_restore01","owners":"admin"}}]}', aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _vol_id, _owners = _escli.mGetVolumeID(_cell, "acfs_gridclub086e35-128", _options)
        self.assertEqual(_vol_id, "4:aa11bb22cc33dd44ee55")
        self.assertEqual(_owners, "admin")

    def test_mGetVolumeAttachments(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json lsvolumeattachment --attributes id,volume,deviceName", aRc=0, aStdout='{"data":[{"id":"3:175ebf661f8e49c09d03f8214f6c5b39","attributes":{"volume":"2:b4d00303b12f46d6a31b4a5339395cd3","deviceName":"xacfsvol"}}]}', aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _id, _volume, _device_name = _escli.mGetVolumeAttachments(_cell, "2:b4d00303b12f46d6a31b4a5339395cd3", _options)
        self.assertEqual(_id, "3:175ebf661f8e49c09d03f8214f6c5b39")

    def test_mGetVolumeAttachments_handles_missing_volume(self):
        # Auto-generated test for mGetVolumeAttachments
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json lsvolumeattachment --attributes id,volume,deviceName", aRc=0, aStdout='{"data":[{"id":"4:bb11cc22dd33ee44ff55","attributes":{"volume":"2:aaaa1111bbbb2222cccc3333","deviceName":"anotherdev"}}]}', aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _id, _volume, _device_name = _escli.mGetVolumeAttachments(_cell, "2:nonexistent", _options)
        self.assertEqual(_id, "")
        self.assertEqual(_volume, "")
        self.assertEqual(_device_name, "")

    def test_mGetACFSFileSystem(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json lsacfsfilesystem --attributes id,volume,mountPath,size,totalFree", aRc=0, aStdout='{"data":[{"id":"1:6cafd8310b3d49a2becd17e9c08f7919","attributes":{"volume":"2:2fad5a43ed1f46be8eb3687ba59b1d00","mountPath":"/acfs_1","size":10737418240,"totalFree":4294967296}}]}', aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _acfs_id, _mount_path, _size, _used = _escli.mGetACFSFileSystem(_cell, "2:2fad5a43ed1f46be8eb3687ba59b1d00", _options)
        self.assertEqual(_acfs_id, "1:6cafd8310b3d49a2becd17e9c08f7919")
        self.assertEqual(_mount_path, "/acfs_1")
        self.assertEqual(_size, 10.0)
        self.assertEqual(_used, 4.0)

    def test_mGetACFSFileSystemByJsonFormat(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand("/bin/test -e *", aRc=0, aStdout="" ,aPersist=True),
                                exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json lsacfsfilesystem --attributes id,volume,mountPath,size,totalFree", aRc=0, aStdout='{"data":[{"attributes":{"id":"1","volume":"vol_1","mountPath":"/acfs","size":10737418240,"totalFree":5368709120}}]}', aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _ret, _out, _err = _escli.mGetACFSFileSystemByJsonFormat(_cell, _options)
        self.assertEqual(_ret, 0)
        self.assertIn('"volume":"vol_1"', _out)

    def test_mChangeACL(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chacl @vault1clu02 +club086e35-128:none"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _escli.mChangeACL(_cell, "club086e35-128", "none", _options)

    def test_mCreateEDVVolumeP01(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 mkvolume 200GB --vault vault1clu02 --attributes name=acfs_gridclub086e35-128"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _rc =_escli.mCreateEDVVolume(_cell, "200GB", "acfs_gridclub086e35-128", _options)
        self.assertEqual(_rc, 0)   

    def test_mCreateEDVVolumeP02(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 mkvolume 200GB --vault image --attributes name=c3716n15c2_u01"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _rc =_escli.mCreateEDVVolume(_cell, "200GB", "c3716n15c2_u01", _options, aVaultName="image")
        self.assertEqual(_rc, 0)  

    def test_mCreateEDVVolumeAttachmentP01(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 mkvolumeattachment --protocol edv 2:2fad5a43ed1f46be8eb3687ba59b1d00 xacfsvol --attributes giClusterId=9e827518-8a9f-5fd9-ffbe-c2ae1c46734c,user=gridclub086e35-128"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _rc =_escli.mCreateEDVVolumeAttachment(_cell, "2:2fad5a43ed1f46be8eb3687ba59b1d00", "xacfsvol", "9e827518-8a9f-5fd9-ffbe-c2ae1c46734c", "gridclub086e35-128", _options)
        self.assertEqual(_rc, 0)   

    def test_mCreateEDVVolumeAttachmentP02(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 mkvolumeattachment --protocol edv 2:2fad5a43ed1f46be8eb3687ba59b1d00 xacfsvol --initiator a3311f85-8414-ac62-a331-1f858414ac62 --attributes user=gridclub086e35-128"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _rc =_escli.mCreateEDVVolumeAttachment(_cell, "2:2fad5a43ed1f46be8eb3687ba59b1d00", "xacfsvol", "9e827518-8a9f-5fd9-ffbe-c2ae1c46734c", "gridclub086e35-128", _options, aInitiatorID="a3311f85-8414-ac62-a331-1f858414ac62")
        self.assertEqual(_rc, 0)   

    def test_mCreateACFSFileSystem(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 mkacfsfilesystem 2:2fad5a43ed1f46be8eb3687ba59b1d00 /var/opt/oracle/dbaas_acfs --attributes name=default_acfs,user=gridclub086e35-128,mountLeafOwner=1001,mountLeafGroup=1001,mountLeafMode=0755"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _rc =_escli.mCreateACFSFileSystem(_cell, "2:2fad5a43ed1f46be8eb3687ba59b1d00", "/var/opt/oracle/dbaas_acfs", "default_acfs", "gridclub086e35-128", _options)
        self.assertEqual(_rc, 0)   

    def test_mChangeVolume(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chvolume 2:2fad5a43ed1f46be8eb3687ba59b1d00 --attributes owners=+gridclub086e35-128"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _rc =_escli.mChangeVolume(_cell, "2:2fad5a43ed1f46be8eb3687ba59b1d00", "gridclub086e35-128", _options)
        self.assertEqual(_rc, 0) 

    def test_mMountACFSFileSystem(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 acfsctl register 2:2fad5a43ed1f46be8eb3687ba59b1d00 /acfs_1 --attributes mountLeafOwner=1001,mountLeafGroup=1001,mountLeafMode=0755,user=gridclub086e35-128"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _rc =_escli.mMountACFSFileSystem(_cell, "2:2fad5a43ed1f46be8eb3687ba59b1d00", "/acfs_1", "gridclub086e35-128", _options)
        self.assertEqual(_rc, 0)

    def test_mUnMountACFSFileSystem(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 acfsctl deregister 1:6cafd8310b3d49a2becd17e9c08f7919"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _escli.mUnMountACFSFileSystem(_cell, "1:6cafd8310b3d49a2becd17e9c08f7919", _options)

    def test_mRemoveACFSFileSystem(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 rmacfsfilesystem 1:6cafd8310b3d49a2becd17e9c08f7919"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _escli.mRemoveACFSFileSystem(_cell, "1:6cafd8310b3d49a2becd17e9c08f7919", _options)

    def test_mRemoveEDVAttachment(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 rmvolumeattachment 3:175ebf661f8e49c09d03f8214f6c5b39"), aRc=0, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 rmvolumeattachment 3:175ebf661f8e49c09d03f8214f6c5b39 --force"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _escli.mRemoveEDVAttachment(_cell, _options, "3:175ebf661f8e49c09d03f8214f6c5b39", aForce=False)
        _escli.mRemoveEDVAttachment(_cell, _options, "3:175ebf661f8e49c09d03f8214f6c5b39", aForce=True)

    def test_mRemoveEDVVolume(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 rmvolume 2:b4d00303b12f46d6a31b4a5339395cd3"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _escli.mRemoveEDVVolume(_cell, "2:b4d00303b12f46d6a31b4a5339395cd3", _options)

    def test_mRemoveFile(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 rmfile @vault1clu02/CLUB086e35-128* "), aRc=0, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 rmfile @vault1clu02/CLUB086e35-128* --force"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _escli.mRemoveFile(_cell, "@vault1clu02/CLUB086e35-128*", _options, aForce=False)
        _escli.mRemoveFile(_cell, "@vault1clu02/CLUB086e35-128*", _options, aForce=True)

    def test_mCreateVault(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(VAULT_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-ef 10G"), aRc=0, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json mkvault @vault1clu02 --provision-space-hc 10G"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _escli.mCreateVault(_cell, True, "vault1clu02", "10", _options)
        _escli.mCreateVault(_cell, False, "vault1clu02", "10", _options)

    def test_mListVault(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(VAULT_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02 --attributes spaceUsedHC"), aRc=0, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json lsvault @vault1clu02 --detail"), aRc=0, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvault @vault1clu02"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _attributes = ["spaceUsedHC"]
        _escli = ebEscliUtils(_ebox)
        _escli.mListVault(_cell, "vault1clu02", _options, aDetail=False, aAttributes=_attributes)
        _escli.mListVault(_cell, "vault1clu02", _options, aDetail=True, aAttributes=[])
        _escli.mListVault(_cell, "vault1clu02", _options)

    def test_mListVault_json_attributes(self):
        # Auto-generated test for mListVault
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(VAULT_PAYLOAD)
        _escli = ebEscliUtils(_ebox)

        with mock.patch.object(_escli, "mExecuteEscliCmd", return_value=(0, "out", "err")) as _mock_exec:
            _escli.mListVault(_cell, "vault1clu02", _options, aAttributes=["spaceUsedHC"], aJson=True)

            _mock_exec.assert_called_once()
            _called_cell, _cmd_str = _mock_exec.call_args[0]
            self.assertEqual(_called_cell, _cell)
            self.assertIn("--json lsvault @vault1clu02 --attributes spaceUsedHC", _cmd_str)

    def test_mListVault_handles_json_flag(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(VAULT_PAYLOAD)

        _escli = ebEscliUtils(_ebox)

        with mock.patch.object(_escli, "mExecuteEscliCmd", return_value=(0, ["{}"], "")) as _mock_exec:
            _escli.mListVault(_cell, "vault1clu02", _options, aDetail=True, aJson=True)

            _mock_exec.assert_called_once()
            _called_cell, _cmd_str = _mock_exec.call_args[0]
            self.assertEqual(_called_cell, _cell)
            self.assertIn("--json lsvault @vault1clu02 --detail", _cmd_str)

    def test_mChangeVault(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(VAULT_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json chvault @vault1clu02 --attributes spaceProvEF=10G"), aRc=0, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json chvault @vault1clu02 --attributes spaceProvHC=10G"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _escli.mChangeVault(_cell, True, "vault1clu02", "10", _options)
        _escli.mChangeVault(_cell, False, "vault1clu02", "10", _options)

    def test_mRemoveVault(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(VAULT_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 rmvault @vault1clu02"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _escli.mRemoveVault(_cell, "vault1clu02", _options)

    def test_mGetProvisionedValue(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(VAULT_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvEF"), aRc=0, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsvault *xsvlt-* --attributes spaceProvHC"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _escli.mGetProvisionedValue(_cell, True, _options)
        _escli.mGetProvisionedValue(_cell, False, _options)

    def test_mListStoragePool(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(VAULT_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceRaw,spaceProvisioned,spaceUsed"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _escli.mListStoragePool(_cell, "hcpool", _options)

    def test_mCurrentStoragePoolSize(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(VAULT_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 --json  lsstoragepool hcpool --attributes spaceProvisionable,spaceProvisioned,spaceUsed"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _escli.mCurrentStoragePoolSize(_cell, "hcpool", _options)

    def test_mReconfigStoragePool(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(VAULT_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 chstoragepool hcpool --reconfig --force"), aRc=0, aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _escli.mReconfigStoragePool(_cell, "hcpool", _options)

    def test_mCreateEsWalletUser_invalid_user(self):
        # Auto-generated test for mCreateEsWalletUser
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _escli = ebEscliUtils(_ebox)
        _result = _escli.mCreateEsWalletUser(_options, _cell, "", aVaultName="vault1")
        self.assertIsNone(_result)

    def test_mCreateEsWalletUser_ctrl_lookup_fallback(self):
        # Auto-generated test for mCreateEsWalletUser
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]
        _options = SimpleNamespace(jsonconf=None)

        _mock_stdout = mock.MagicMock()
        _mock_stdout.readlines.return_value = []
        _mock_node = mock.MagicMock()
        _mock_node.mFileExists.return_value = True
        _mock_node.mExecuteCmd.return_value = (0, _mock_stdout, "")
        _mock_ctx = mock.MagicMock()
        _mock_ctx.__enter__.return_value = _mock_node
        _mock_ctx.__exit__.return_value = None

        with mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.0.130.110", "host")) as _ctrl_mock:
            with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_mock_ctx) as _connect_mock:
                _escli = ebEscliUtils(_ebox)
                _escli.mCreateEsWalletUser(_options, _cell, "user01")
                _ctrl_mock.assert_called_once()
                _connect_mock.assert_called_once()
                _mock_node.mExecuteCmd.assert_called_once()

    def test_mCreateEsWalletUser_missing_escli_path(self):
        # Auto-generated test for mCreateEsWalletUser
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]
        _options = SimpleNamespace(jsonconf={"exascale": {"ctrl_network": {"ip": "10.0.0.21", "port": "5052"}}})

        _mock_node = mock.MagicMock()
        _mock_node.mFileExists.return_value = False
        _mock_ctx = mock.MagicMock()
        _mock_ctx.__enter__.return_value = _mock_node
        _mock_ctx.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_mock_ctx):
            _escli = ebEscliUtils(_ebox)
            with self.assertRaises(ExacloudRuntimeError):
                _escli.mCreateEsWalletUser(_options, _cell, "griduser")

        _mock_node.mExecuteCmd.assert_not_called()

    def test_mCreateEsWalletUser_updates_pubkey_and_acl(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]
        _options = SimpleNamespace(jsonconf={
            "exascale": {
                "ctrl_network": {"ip": "10.0.0.22", "port": "5052"}
            }
        })

        _mk_stdout = mock.MagicMock()
        _mk_stdout.readlines.return_value = []
        _lsacl_stdout = mock.MagicMock()
        _lsacl_stdout.readlines.return_value = [
            json.dumps({
                "data": {
                    "attributes": {
                        "acl": "existing:I"
                    }
                }
            })
        ]

        _mock_node = mock.MagicMock()
        _mock_node.mFileExists.return_value = True
        _mock_node.mExecuteCmd.side_effect = [
            (0, _mk_stdout, ""),
            (0, mock.MagicMock(), ""),
            (0, mock.MagicMock(), ""),
            (0, _lsacl_stdout, ""),
        ]

        _mock_ctx = mock.MagicMock()
        _mock_ctx.__enter__.return_value = _mock_node
        _mock_ctx.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_mock_ctx), \
             mock.patch("exabox.ovm.csstep.exascale.escli_util.node_exec_cmd_check") as _exec_check_mock:
            _escli = ebEscliUtils(_ebox)
            _escli.mCreateEsWalletUser(
                _options,
                _cell,
                "user02",
                aPubKeyFile="/tmp/key.pub",
                aVaultName="vault1",
            )

        _cmds = [call_args[0][0] for call_args in _mock_node.mExecuteCmd.call_args_list]
        self.assertEqual(len(_cmds), 4)
        self.assertIn("mkuser oracle --id user02", _cmds[0])
        self.assertIn("chuser user02 --public-key-file1 /tmp/key.pub", _cmds[1])
        self.assertEqual(_cmds[2], "/bin/rm -f /tmp/key.pub")
        self.assertIn("--json lsacl vault1", _cmds[3])
        _exec_check_mock.assert_called_once_with(
            _mock_node,
            f'{ESCLI} --wallet {WALLET_LOC} --ctrl 10.0.0.22:{CTRL_PORT} chacl vault1 "existing:I;user02:I"',
        )

    def test_mCreateEsWalletUser_acl_already_contains_user(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]
        _options = SimpleNamespace(jsonconf={
            "exascale": {
                "ctrl_network": {"ip": "10.0.0.23", "port": "5052"}
            }
        })

        _mk_stdout = mock.MagicMock()
        _mk_stdout.readlines.return_value = []
        _lsacl_stdout = mock.MagicMock()
        _lsacl_stdout.readlines.return_value = [
            json.dumps({
                "data": {
                    "attributes": {
                        "acl": "existing:I;user03:I"
                    }
                }
            })
        ]

        _mock_node = mock.MagicMock()
        _mock_node.mFileExists.return_value = True
        _mock_node.mExecuteCmd.side_effect = [
            (0, _mk_stdout, ""),
            (0, _lsacl_stdout, ""),
        ]

        _mock_ctx = mock.MagicMock()
        _mock_ctx.__enter__.return_value = _mock_node
        _mock_ctx.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_mock_ctx), \
             mock.patch("exabox.ovm.csstep.exascale.escli_util.node_exec_cmd_check") as _exec_check_mock:
            _escli = ebEscliUtils(_ebox)
            _escli.mCreateEsWalletUser(_options, _cell, "user03", aVaultName="vault1")

        _cmds = [call_arg[0][0] for call_arg in _mock_node.mExecuteCmd.call_args_list]
        self.assertEqual(len(_cmds), 2)
        self.assertIn("mkuser oracle --id user03", _cmds[0])
        self.assertIn("--json lsacl vault1", _cmds[1])
        _exec_check_mock.assert_not_called()

    def test_mCreateEsWalletUser_acl_missing_output(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]
        _options = SimpleNamespace(jsonconf={
            "exascale": {
                "ctrl_network": {"ip": "10.0.0.24", "port": "5052"}
            }
        })

        _mk_stdout = mock.MagicMock()
        _mk_stdout.readlines.return_value = []
        _lsacl_stdout = mock.MagicMock()
        _lsacl_stdout.readlines.return_value = [
            json.dumps({
                "data": {
                    "attributes": {
                        "acl": None
                    }
                }
            })
        ]

        _mock_node = mock.MagicMock()
        _mock_node.mFileExists.return_value = True
        _mock_node.mExecuteCmd.side_effect = [
            (0, _mk_stdout, ""),
            (0, _lsacl_stdout, ""),
        ]

        _mock_ctx = mock.MagicMock()
        _mock_ctx.__enter__.return_value = _mock_node
        _mock_ctx.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_mock_ctx), \
             mock.patch("exabox.ovm.csstep.exascale.escli_util.node_exec_cmd_check") as _exec_check_mock:
            _escli = ebEscliUtils(_ebox)
            with self.assertRaises(ExacloudRuntimeError):
                _escli.mCreateEsWalletUser(_options, _cell, "user04", aVaultName="vault1")

        _cmds = [call_arg[0][0] for call_arg in _mock_node.mExecuteCmd.call_args_list]
        self.assertEqual(len(_cmds), 2)
        self.assertIn("mkuser oracle --id user04", _cmds[0])
        self.assertIn("--json lsacl vault1", _cmds[1])
        _exec_check_mock.assert_not_called()

    def test_mParseExascaleAttrib(self):
        _ebox = self.mGetClubox()
        _escli = ebEscliUtils(_ebox)

        _options = SimpleNamespace(jsonconf={'exascale': {'ctrl_network': {'ip': '1.1.1.1'}}})
        self.assertEqual(_escli.mParseExascaleAttrib(_options), {'ctrl_network': {'ip': '1.1.1.1'}})

        _options = SimpleNamespace(jsonconf={'ctrl_network': {'ip': '2.2.2.2'}})
        self.assertEqual(_escli.mParseExascaleAttrib(_options), {'ctrl_network': {'ip': '2.2.2.2'}})

        _options = SimpleNamespace(jsonconf={'db_vaults': [{'ctrl_network': {'ip': '3.3.3.3'}}]})
        self.assertEqual(_escli.mParseExascaleAttrib(_options), {'ctrl_network': {'ip': '3.3.3.3'}})

        _options = SimpleNamespace(jsonconf=None)
        self.assertEqual(_escli.mParseExascaleAttrib(_options), "")
        # Auto-generated test for mParseExascaleAttrib

    def test_mIsEFRack(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _stdout_with_cf = mock.MagicMock()
        _stdout_with_cf.readlines.return_value = ['CF_disk']
        _node_with_cf = mock.MagicMock()
        _node_with_cf.mExecuteCmd.return_value = (0, _stdout_with_cf, '')
        _node_with_cf.mGetCmdExitStatus.return_value = 0
        _context_with_cf = mock.MagicMock()
        _context_with_cf.__enter__.return_value = _node_with_cf
        _context_with_cf.__exit__.return_value = False

        with mock.patch('exabox.ovm.csstep.exascale.escli_util.connect_to_host', return_value=_context_with_cf):
            _escli = ebEscliUtils(_ebox)
            self.assertTrue(_escli.mIsEFRack(_cell))

        _stdout_without_cf = mock.MagicMock()
        _stdout_without_cf.readlines.return_value = []
        _node_without_cf = mock.MagicMock()
        _node_without_cf.mExecuteCmd.return_value = (0, _stdout_without_cf, '')
        _node_without_cf.mGetCmdExitStatus.return_value = 0
        _context_without_cf = mock.MagicMock()
        _context_without_cf.__enter__.return_value = _node_without_cf
        _context_without_cf.__exit__.return_value = False

        with mock.patch('exabox.ovm.csstep.exascale.escli_util.connect_to_host', return_value=_context_without_cf):
            _escli = ebEscliUtils(_ebox)
            self.assertFalse(_escli.mIsEFRack(_cell))
        # Auto-generated test for mIsEFRack

    def test_mGetDBVaultName(self):
        _ebox = self.mGetClubox()
        _escli = ebEscliUtils(_ebox)
        _sample_xml = '<root><exascale><vaults><vault><name>vaultOne</name></vault></vaults></exascale></root>'

        with mock.patch.object(_ebox, 'mGetPatchConfig', return_value='/tmp/mock_patch.xml'),              mock.patch.object(_ebox, 'mIsClusterLessXML', return_value=False),              mock.patch('builtins.open', mock_open(read_data=_sample_xml)),              mock.patch('os.path.exists', return_value=True):
            self.assertEqual(_escli.mGetDBVaultName(), 'vaultOne')

        with mock.patch.object(_ebox, 'mGetPatchConfig', return_value='/tmp/mock_patch.xml'),              mock.patch.object(_ebox, 'mIsClusterLessXML', return_value=True):
            self.assertEqual(_escli.mGetDBVaultName(), '')
        # Auto-generated test for mGetDBVaultName

    def test_mGetCtrlIP(self):
        _ebox = self.mGetClubox()
        _escli = ebEscliUtils(_ebox)

        _mock_config = mock.MagicMock()
        _mock_config.mGetExascaleClusterConfigList.return_value = ['cluster']
        _mock_config.mGetExascaleClusterConfig.return_value = mock.MagicMock(mGetMacNetworks=lambda: ['net1'])

        _mock_network = mock.MagicMock()
        _mock_network.mGetNetIpAddr.return_value = '10.0.0.1'
        _mock_network.mGetNetHostName.return_value = 'host'
        _mock_network.mGetNetDomainName.return_value = 'domain'

        _mock_networks = mock.MagicMock()
        _mock_networks.mGetNetworkConfig.return_value = _mock_network

        with mock.patch('exabox.ovm.csstep.exascale.escli_util.ebCluExascaleConfig', return_value=_mock_config):
            with mock.patch.object(_ebox, 'mGetNetworks', return_value=_mock_networks):
                result = _escli.mGetCtrlIP()
        self.assertEqual(result, ('10.0.0.1', 'host.domain'))
        # Auto-generated test for mGetCtrlIP

    def test_mListFiles(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = SimpleNamespace(jsonconf={'exascale': {'db_vault': {'name': 'vault1'}, 'ctrl_network': {'ip': '10.0.0.2', 'port': '5052'}}})

        _mock_node = mock.MagicMock()
        _mock_node.mFileExists.return_value = True

        _mock_ctx = mock.MagicMock()
        _mock_ctx.__enter__.return_value = _mock_node
        _mock_ctx.__exit__.return_value = False

        with mock.patch('exabox.ovm.csstep.exascale.escli_util.connect_to_host', return_value=_mock_ctx), \
             mock.patch('exabox.ovm.csstep.exascale.escli_util.node_exec_cmd', return_value=(0, 'file1\nfile2\n', '')):
            _escli = ebEscliUtils(_ebox)
            result = _escli.mListFiles(_cell, 'somefile', _options)
        self.assertEqual(result, ['file1', 'file2'])
        # Auto-generated test for mListFiles

    def test___init__stores_cluctrl(self):
        # Auto-generated test for __init__
        _ebox = self.mGetClubox()
        _escli = ebEscliUtils(_ebox)
        self.assertIs(_escli._ebEscliUtils__cluctrl, _ebox)

    def test_mUpdateRequestData_no_request_obj(self):
        # Auto-generated test for mUpdateRequestData
        _ebox = self.mGetClubox()
        _escli = ebEscliUtils(_ebox)

        with mock.patch.object(_ebox, "mGetRequestObj", return_value=None):
            _escli.mUpdateRequestData(0, {"data": "ok"}, "")

    def test_mUpdateRequestData_updates_request(self):
        # Auto-generated test for mUpdateRequestData
        _ebox = self.mGetClubox()
        _req_obj = mock.MagicMock()
        _payload = {"data": "failure"}
        _error = "something went wrong"

        with mock.patch.object(_ebox, "mGetRequestObj", return_value=_req_obj),              mock.patch("exabox.ovm.csstep.exascale.escli_util.ebGetDefaultDB") as _db_mock:
            _db_instance = mock.MagicMock()
            _db_mock.return_value = _db_instance

            _escli = ebEscliUtils(_ebox)
            _escli.mUpdateRequestData(1, _payload, _error)

        _req_obj.mSetData.assert_called_once()
        _stored_json = _req_obj.mSetData.call_args[0][0]
        self.assertEqual(
            json.loads(_stored_json),
            {"success": "False", "error": _error, "output": _payload}
        )
        _db_instance.mUpdateRequest.assert_called_once_with(_req_obj)

    def test_mExecuteEscliCmd_missing_escli(self):
        # Auto-generated test for mExecuteEscliCmd
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand(re.escape("/bin/test -e /opt/oracle/cell/cellsrv/bin/escli"), aRc=1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        with self.assertRaises(ExacloudRuntimeError):
            _escli.mExecuteEscliCmd(_cell, "escli --help")

    def test_mExecuteEscliCmd_success(self):
        # Auto-generated test for mExecuteEscliCmd
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _mock_node = mock.MagicMock()
        _mock_node.mFileExists.return_value = True

        _context = mock.MagicMock()
        _context.__enter__.return_value = _mock_node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            with mock.patch("exabox.ovm.csstep.exascale.escli_util.node_exec_cmd", return_value=(0, "ok", "")) as _exec_mock:
                _escli = ebEscliUtils(_ebox)
                _result = _escli.mExecuteEscliCmd(_cell, "escli --version")

        self.assertEqual(_result, (0, "ok", ""))
        _exec_mock.assert_called_once_with(_mock_node, "escli --version")

    def test_mRemoveACFSFileSystem_force_retry(self):
        # Auto-generated test for mRemoveACFSFileSystem
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _mock_node = mock.MagicMock()
        _mock_node.mGetCmdExitStatus.side_effect = [1, 0]
        _context = mock.MagicMock()
        _context.__enter__.return_value = _mock_node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            _escli = ebEscliUtils(_ebox)
            _escli.mRemoveACFSFileSystem(_cell, "1:6cafd8310b3d49a2becd17e9c08f7919", _options)

        self.assertEqual(_mock_node.mExecuteCmdLog.call_count, 2)
        _first_cmd = _mock_node.mExecuteCmdLog.call_args_list[0][0][0]
        _second_cmd = _mock_node.mExecuteCmdLog.call_args_list[1][0][0]
        self.assertIn("rmacfsfilesystem 1:6cafd8310b3d49a2becd17e9c08f7919", _first_cmd)
        self.assertNotIn("--force", _first_cmd)
        self.assertIn("--force", _second_cmd)

    def test_mRemoveEDVAttachment_no_id(self):
        # Auto-generated test for mRemoveEDVAttachment
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _mock_node = mock.MagicMock()
        _context = mock.MagicMock()
        _context.__enter__.return_value = _mock_node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            _escli = ebEscliUtils(_ebox)
            _escli.mRemoveEDVAttachment(_cell, _options, "", aForce=True)

        _mock_node.mExecuteCmdLog.assert_not_called()

    def test_mRemoveEDVVolume_no_id(self):
        # Auto-generated test for mRemoveEDVVolume
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _mock_node = mock.MagicMock()
        _context = mock.MagicMock()
        _context.__enter__.return_value = _mock_node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            _escli = ebEscliUtils(_ebox)
            _escli.mRemoveEDVVolume(_cell, "", _options)

        _mock_node.mExecuteCmdLog.assert_not_called()

    def test_mRemoveFile_fallback_force(self):
        # Auto-generated test for mRemoveFile
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = SimpleNamespace(jsonconf=None)

        _mock_node = mock.MagicMock()
        _context = mock.MagicMock()
        _context.__enter__.return_value = _mock_node
        _context.__exit__.return_value = None

        with mock.patch.object(ebEscliUtils, "mGetDBVaultName", return_value="vaultFallback") as _vault_mock:
            with mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.0.0.1", "host.domain")) as _ctrl_mock:
                with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
                    _escli = ebEscliUtils(_ebox)
                    _escli.mRemoveFile(_cell, "@vaultFallback/file.dat", _options, aForce=True)

        _vault_mock.assert_called_once()
        _ctrl_mock.assert_called_once()
        _mock_node.mExecuteCmdLog.assert_called_once_with("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.0.1:5052 rmfile @vaultFallback/file.dat --force")

    def test_mResizeEDVVolume_success(self):
        # Auto-generated test for mResizeEDVVolume
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = SimpleNamespace(jsonconf={"ctrl_network": {"ip": "10.0.0.2", "port": "5052"}})

        _mock_node = mock.MagicMock()
        _mock_node.mGetCmdExitStatus.return_value = 0
        _context = mock.MagicMock()
        _context.__enter__.return_value = _mock_node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            _escli = ebEscliUtils(_ebox)
            _rc = _escli.mResizeEDVVolume(_cell, "200GB", "vol-01", _options)

        self.assertEqual(_rc, 0)
        _mock_node.mExecuteCmdLog.assert_called_once_with("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.0.2:5052 chvolume vol-01 --attributes size=200GB")

    def test_mResizeEDVVolume_error(self):
        # Auto-generated test for mResizeEDVVolume
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = SimpleNamespace(jsonconf={"ctrl_network": {"ip": "10.0.0.3", "port": "5052"}})

        _mock_node = mock.MagicMock()
        _mock_node.mGetCmdExitStatus.return_value = 1
        _context = mock.MagicMock()
        _context.__enter__.return_value = _mock_node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            with mock.patch.object(_ebox, "mUpdateErrorObject") as _error_mock:
                _escli = ebEscliUtils(_ebox)
                with self.assertRaises(ExacloudRuntimeError):
                    _escli.mResizeEDVVolume(_cell, "300GB", "vol-02", _options)

        _error_mock.assert_called_once()
        _mock_node.mExecuteCmdLog.assert_called_once_with("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.0.3:5052 chvolume vol-02 --attributes size=300GB")

    def test_mRemoveUser_executes_rmuser(self):
        # Auto-generated test for mRemoveUser
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = SimpleNamespace(jsonconf={"ctrl_network": {"ip": "10.0.0.4", "port": "5052"}})

        _mock_node = mock.MagicMock()
        _context = mock.MagicMock()
        _context.__enter__.return_value = _mock_node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            _escli = ebEscliUtils(_ebox)
            _escli.mRemoveUser(_cell, "griduser", _options)

        _mock_node.mExecuteCmdLog.assert_called_once_with("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.0.4:5052 rmuser griduser")

    def test_mAlterAutoFileEncryption_paths(self):
        # Auto-generated test for mAlterAutoFileEncryption
        _ebox = self.mGetClubox()

        _options = SimpleNamespace(jsonconf={"ctrl_network": {"ip": "10.0.0.5", "port": "5053"}})
        with mock.patch.object(ebEscliUtils, "mExecuteEscliCmd", return_value=(0, "", "")) as _exec_mock:
            _escli = ebEscliUtils(_ebox)
            _ret = _escli.mAlterAutoFileEncryption("cell-1", True, _options)

        self.assertEqual(_ret, 0)
        _exec_mock.assert_called_once_with("cell-1", "/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.0.5:5053 chcluster --attributes autoFileEncryption=true")

        _fallback_options = SimpleNamespace(jsonconf=None)
        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=Exception("fail")):
            with mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.0.0.6", "host")):
                with mock.patch.object(ebEscliUtils, "mExecuteEscliCmd", return_value=(0, "", "")) as _fallback_exec:
                    _escli = ebEscliUtils(_ebox)
                    _escli.mAlterAutoFileEncryption("cell-2", False, _fallback_options)

        _fallback_exec.assert_called_once_with("cell-2", "/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.0.6:5052 chcluster --attributes autoFileEncryption=false")

    def test_mGetClusterAttribute_invokes_execute(self):
        # Auto-generated test for mGetClusterAttribute
        _ebox = self.mGetClubox()
        _options = SimpleNamespace(jsonconf={"ctrl_network": {"ip": "10.0.0.7", "port": "5052"}})

        with mock.patch.object(ebEscliUtils, "mExecuteEscliCmd", return_value=(0, "out", "")) as _exec_mock:
            _escli = ebEscliUtils(_ebox)
            _ret = _escli.mGetClusterAttribute("cell-3", "autoFileEncryption", _options)

        self.assertEqual(_ret, (0, "out", ""))
        _exec_mock.assert_called_once_with("cell-3", "/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.0.7:5052 lscluster --attributes autoFileEncryption")

    def test_mGetERSEndpoint_fallback_ctrl_ip(self):
        # Auto-generated test for mGetERSEndpoint
        _ebox = self.mGetClubox()
        _escli = ebEscliUtils(_ebox)
        _options = SimpleNamespace(jsonconf=None)

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=Exception("boom")), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.99.0.1", "ctrl-host")) as _ctrl_mock:
            _ctrl_ip, _ctrl_port = _escli.mGetERSEndpoint(_options)

        self.assertEqual((_ctrl_ip, _ctrl_port), ("10.99.0.1", CTRL_PORT))
        _ctrl_mock.assert_called_once()

    def test_mGetEDVInitiator_error_raises(self):
        # Auto-generated test for mGetEDVInitiator
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]
        _options = SimpleNamespace(jsonconf={"ctrl_network": {"ip": "10.0.0.10", "port": "5052"}})

        _stdout = mock.MagicMock()
        _stdout.readlines.return_value = []
        _node = mock.MagicMock()
        _node.mExecuteCmd.return_value = (0, _stdout, "")
        _node.mGetCmdExitStatus.return_value = 1

        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context), \
             mock.patch.object(_ebox, "mUpdateErrorObject") as _error_mock:
            _escli = ebEscliUtils(_ebox)
            with self.assertRaises(ExacloudRuntimeError):
                _escli.mGetEDVInitiator(_cell, "host-1", _options)

        _error_mock.assert_called_once()

    def test_mCreateEDVVolume_error_propagates(self):
        # Auto-generated test for mCreateEDVVolume
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]
        _options = SimpleNamespace(jsonconf={
            "exascale": {
                "ctrl_network": {"ip": "10.0.0.11", "port": "5052"},
                "db_vault": {"name": "vaultX"}
            }
        })

        _node = mock.MagicMock()
        _node.mExecuteCmdLog.return_value = None
        _node.mGetCmdExitStatus.return_value = 1

        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context), \
             mock.patch.object(_ebox, "mUpdateErrorObject") as _error_mock:
            _escli = ebEscliUtils(_ebox)
            with self.assertRaises(ExacloudRuntimeError):
                _escli.mCreateEDVVolume(_cell, "500GB", "volX", _options)

        _error_mock.assert_called_once()
        _node.mExecuteCmdLog.assert_called_once()

    def test_mCreateEDVVolumeAttachment_error_initiator(self):
        # Auto-generated test for mCreateEDVVolumeAttachment
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]
        _options = SimpleNamespace(jsonconf={"ctrl_network": {"ip": "10.0.0.12", "port": "5052"}})

        _node = mock.MagicMock()
        _node.mExecuteCmdLog.return_value = None
        _node.mGetCmdExitStatus.return_value = 1

        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context), \
             mock.patch.object(_ebox, "mUpdateErrorObject") as _error_mock:
            _escli = ebEscliUtils(_ebox)
            with self.assertRaises(ExacloudRuntimeError):
                _escli.mCreateEDVVolumeAttachment(_cell, "vol-id", "dev0", "cluster-id", "cluster-name", _options, aInitiatorID="init-01")

        _error_mock.assert_called_once()
        _node.mExecuteCmdLog.assert_called_once()

    def test_mChangeACL_raises_on_esnp_not_running(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]
        _options = SimpleNamespace(jsonconf={"exascale": {"ctrl_network": {"ip": "10.0.0.13", "port": "5052"}}})

        _cell_node = mock.MagicMock()
        _host_node = mock.MagicMock()
        _host_node.mExecuteCmd.return_value = (0, mock.MagicMock(readlines=lambda: ["stopped\n"]), None)
        _host_node.mGetCmdExitStatus.return_value = 0

        def _connect_side_effect(host, *_args, **_kwargs):
            if host == "host1":
                return mock.MagicMock(__enter__=lambda self=_host_node: _host_node, __exit__=lambda *a, **k: None)
            return mock.MagicMock(__enter__=lambda self=_cell_node: _cell_node, __exit__=lambda *a, **k: None)

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", side_effect=_connect_side_effect):
            _escli = ebEscliUtils(_ebox)
            with self.assertRaises(ExacloudRuntimeError):
                _escli.mChangeACL(_cell, "clusterA", "read", _options, aHost="host1", aVaultName="vaultCustom")

    def test_mUnMountACFSFileSystem_no_raise_on_error(self):
        # Auto-generated test for mUnMountACFSFileSystem
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]
        _options = SimpleNamespace(jsonconf={"ctrl_network": {"ip": "10.0.0.14", "port": "5052"}})

        _node = mock.MagicMock()
        _node.mExecuteCmdLog.return_value = None
        _node.mGetCmdExitStatus.return_value = 1

        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            _escli = ebEscliUtils(_ebox)
            _escli.mUnMountACFSFileSystem(_cell, "acfs-01", _options, aRaiseError=False)

        _node.mExecuteCmdLog.assert_called_once()

    def test_mCreateACFSFileSystem_error(self):
        # Auto-generated test for mCreateACFSFileSystem
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]
        _options = SimpleNamespace(jsonconf={"exascale": {"ctrl_network": {"ip": "10.0.0.15", "port": "5052"}}})

        _node = mock.MagicMock()
        _node.mExecuteCmdLog.return_value = None
        _node.mGetCmdExitStatus.return_value = 1

        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context), \
             mock.patch.object(_ebox, "mUpdateErrorObject") as _error_mock:
            _escli = ebEscliUtils(_ebox)
            with self.assertRaises(ExacloudRuntimeError):
                _escli.mCreateACFSFileSystem(_cell, "vol-id", "/mnt", "fsname", "cluster", _options)

        _error_mock.assert_called_once()
        _node.mExecuteCmdLog.assert_called_once()

    def test_mGetVolumeAttachments_error_path(self):
        # Auto-generated test for mGetVolumeAttachments
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = SimpleNamespace(jsonconf={"ctrl_network": {"ip": "10.1.0.1", "port": "5052"}})

        _stdout = mock.MagicMock()
        _stdout.readlines.return_value = []
        _node = mock.MagicMock()
        _node.mExecuteCmd.return_value = (1, _stdout, "")
        _node.mGetCmdExitStatus.return_value = 1

        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context), \
             mock.patch.object(_ebox, "mUpdateErrorObject") as _error_mock:
            _escli = ebEscliUtils(_ebox)
            with self.assertRaises(ExacloudRuntimeError):
                _escli.mGetVolumeAttachments(_cell, "vol-01", _options)

        _error_mock.assert_called_once()
        _node.mExecuteCmd.assert_called_once()

    def test_mGetACFSFileSystem_branch_lengths(self):
        # Auto-generated test for mGetACFSFileSystem
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = SimpleNamespace(jsonconf={"ctrl_network": {"ip": "10.1.0.2", "port": "5052"}})

        _stdout_len2 = mock.MagicMock()
        _stdout_len2.read.return_value = '{"data":[{"id":"acfsTwo","attributes":{"volume":"vol-01"}}]}'
        _stdout_len3 = mock.MagicMock()
        _stdout_len3.read.return_value = '{"data":[{"id":"acfsThree","attributes":{"volume":"vol-01","size":161061273600}}]}'
        _stdout_len4 = mock.MagicMock()
        _stdout_len4.read.return_value = '{"data":[{"id":"acfsFour","attributes":{"volume":"vol-01","mountPath":"/mnt/acfs","size":"bad-size","totalFree":2147483648}}]}'

        _node = mock.MagicMock()
        _node.mExecuteCmd.side_effect = [
            (0, _stdout_len2, ""),
            (0, _stdout_len3, ""),
            (0, _stdout_len4, ""),
        ]
        _node.mGetCmdExitStatus.side_effect = [0, 0, 0]

        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            _escli = ebEscliUtils(_ebox)
            self.assertEqual(_escli.mGetACFSFileSystem(_cell, "vol-01", _options), ("acfsTwo", None, "", ""))
            self.assertEqual(_escli.mGetACFSFileSystem(_cell, "vol-01", _options), ("acfsThree", None, 150.0, ""))
            self.assertEqual(_escli.mGetACFSFileSystem(_cell, "vol-01", _options), ("acfsFour", "/mnt/acfs", "", 2.0))

        self.assertEqual(_node.mExecuteCmd.call_count, 3)

    def test_mRemoveFile_fallback_ctrl_config(self):
        # Auto-generated test for mRemoveFile
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = SimpleNamespace(jsonconf=None)

        _node = mock.MagicMock()
        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        def _raise_parse(*_args, **_kwargs):
            raise Exception("fail")

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=_raise_parse) as _parse_mock, \
             mock.patch.object(ebEscliUtils, "mGetDBVaultName", return_value="fallbackVault") as _vault_mock, \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.1.0.3", "ers")) as _ctrl_mock, \
             mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            _escli = ebEscliUtils(_ebox)
            _escli.mRemoveFile(_cell, "@fallbackVault/*", _options, aForce=True)

        _parse_mock.assert_called_once()
        _vault_mock.assert_called_once()
        _ctrl_mock.assert_called_once()
        _node.mExecuteCmdLog.assert_called_once_with(f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.1.0.3:{CTRL_PORT} rmfile @fallbackVault/* --force")

    def test_mCreateVault_fallback_ctrl_ip(self):
        # Auto-generated test for mCreateVault
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = SimpleNamespace(jsonconf=None)

        with mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.1.0.4", "ers")) as _ctrl_mock, \
             mock.patch.object(ebEscliUtils, "mExecuteEscliCmd", return_value=(0, "", "")) as _exec_mock:
            _escli = ebEscliUtils(_ebox)
            _escli.mCreateVault(_cell, True, "vaultX", "20", _options)
            _escli.mCreateVault(_cell, False, "vaultX", "20", _options)

        self.assertEqual(_ctrl_mock.call_count, 2)
        _exec_mock.assert_has_calls([
            mock.call(_cell, f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.1.0.4:{CTRL_PORT} --json mkvault @vaultX --provision-space-ef 20G"),
            mock.call(_cell, f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.1.0.4:{CTRL_PORT} --json mkvault @vaultX --provision-space-hc 20G")
        ])

    def test_mGetProvisionedValue_fallback_ctrl(self):
        # Auto-generated test for mGetProvisionedValue
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = SimpleNamespace(jsonconf=None)

        def _raise_parse(*_args, **_kwargs):
            raise Exception("fail")

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=_raise_parse), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.1.0.5", "ers")) as _ctrl_mock, \
             mock.patch.object(ebEscliUtils, "mExecuteEscliCmd", return_value=(0, "", "")) as _exec_mock:
            _escli = ebEscliUtils(_ebox)
            _escli.mGetProvisionedValue(_cell, True, _options)
            _escli.mGetProvisionedValue(_cell, False, _options)

        self.assertEqual(_ctrl_mock.call_count, 2)
        _exec_mock.assert_has_calls([
            mock.call(_cell, f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.1.0.5:{CTRL_PORT} --json  lsvault *xsvlt-* --attributes spaceProvEF"),
            mock.call(_cell, f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.1.0.5:{CTRL_PORT} --json  lsvault *xsvlt-* --attributes spaceProvHC")
        ])

    def test_mChangeVault_fallback_ctrl_ip(self):
        # Auto-generated test for mChangeVault
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = SimpleNamespace(jsonconf=None)

        def _raise_parse(*_args, **_kwargs):
            raise Exception("fail")

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=_raise_parse), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.1.0.4", "ers")) as _ctrl_mock, \
             mock.patch.object(ebEscliUtils, "mExecuteEscliCmd", return_value=(0, "", "")) as _exec_mock:
            _escli = ebEscliUtils(_ebox)
            _escli.mChangeVault(_cell, True, "vault1", "10", _options)

        _ctrl_mock.assert_called_once()
        _exec_mock.assert_called_once_with(_cell, f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.1.0.4:{CTRL_PORT} --json chvault @vault1 --attributes spaceProvEF=10G")

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=_raise_parse), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.1.0.4", "ers")) as _ctrl_mock2, \
             mock.patch.object(ebEscliUtils, "mExecuteEscliCmd", return_value=(0, "", "")) as _exec_mock2:
            _escli = ebEscliUtils(_ebox)
            _escli.mChangeVault(_cell, False, "vault1", "10", _options)

        _ctrl_mock2.assert_called_once()
        _exec_mock2.assert_called_once_with(_cell, f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.1.0.4:{CTRL_PORT} --json chvault @vault1 --attributes spaceProvHC=10G")

    def test_mCreateEDVVolumeAttachment_error_path(self):
        # Auto-generated test for mCreateEDVVolumeAttachment
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _mock_node = mock.MagicMock()
        _mock_node.mGetCmdExitStatus.return_value = 1
        _context = mock.MagicMock()
        _context.__enter__.return_value = _mock_node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            with mock.patch.object(_ebox, "mUpdateErrorObject") as _err_mock:
                _escli = ebEscliUtils(_ebox)
                with self.assertRaises(ExacloudRuntimeError):
                    _escli.mCreateEDVVolumeAttachment(_cell, "2:vol", "xacfsvol", "cluster-id", "griduser", _options)

        _mock_node.mExecuteCmdLog.assert_called_once()
        _err_mock.assert_called_once()

        _cell = list(_cell_list.keys())[0]

        _options = SimpleNamespace(jsonconf=None)

        def _raise_parse(*_args, **_kwargs):
            raise Exception("fail")

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=_raise_parse), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.1.0.6", "ers")) as _ctrl_mock, \
             mock.patch.object(ebEscliUtils, "mExecuteEscliCmd", return_value=(0, "", "")) as _exec_mock:
            _escli = ebEscliUtils(_ebox)
            _escli.mChangeVault(_cell, True, "vaultY", "30", _options)
            _escli.mChangeVault(_cell, False, "vaultY", "30", _options)

        self.assertEqual(_ctrl_mock.call_count, 2)
        _exec_mock.assert_has_calls([
            mock.call(_cell, f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.1.0.6:{CTRL_PORT} --json chvault @vaultY --attributes spaceProvEF=30G"),
            mock.call(_cell, f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.1.0.6:{CTRL_PORT} --json chvault @vaultY --attributes spaceProvHC=30G")
        ])

    def test_mGetByPath_and_mParseEscliJson_branches(self):
        # Auto-generated test for mGetByPath
        # Auto-generated test for mParseEscliJson
        _ebox = self.mGetClubox()
        _escli = ebEscliUtils(_ebox)

        _payload = {
            "data": [
                "skip-me",
                {
                    "id": "first",
                    "attributes": {
                        "hostName": "host-a",
                        "state": "offline"
                    }
                },
                {
                    "id": "second",
                    "attributes": {
                        "hostName": "host-b",
                        "state": "online"
                    }
                }
            ]
        }

        self.assertEqual(_escli.mGetByPath(_payload["data"][1], "attributes.hostName"), "host-a")
        self.assertIsNone(_escli.mGetByPath({"attributes": "not-a-dict"}, "attributes.hostName"))
        self.assertEqual(_escli.mParseEscliJson(None, {"id": "second"}, ["id"]), {})
        self.assertEqual(_escli.mParseEscliJson({"data": []}, {"id": "second"}, ["id"]), {})

        _result = _escli.mParseEscliJson(
            _payload,
            match_dict={
                "attributes.hostName": lambda _value: _value == "host-b",
                "attributes.state": "online"
            },
            return_keys=["id", "attributes.hostName"]
        )

        self.assertEqual(_result, {"id": "second", "hostName": "host-b"})

    def test_mGetDictFromOutputString_paths(self):
        # Auto-generated test for mGetDictFromOutputString
        _ebox = self.mGetClubox()
        _escli = ebEscliUtils(_ebox)

        _valid_out = mock.MagicMock()
        _valid_out.read.return_value = ' {"data": [{"id": "ok"}]} '
        self.assertEqual(
            _escli.mGetDictFromOutputString(_valid_out, "escli --json lsuser", _ebox),
            {"data": [{"id": "ok"}]}
        )

        _empty_out = mock.MagicMock()
        _empty_out.read.return_value = "   "
        with mock.patch.dict(gExascaleError, {"EMPTY_ESCLI_OUTPUT": "EMPTY_ESCLI_OUTPUT"}, clear=False):
            with mock.patch.object(_ebox, "mUpdateErrorObject") as _update_error:
                with self.assertRaises(ExacloudRuntimeError):
                    _escli.mGetDictFromOutputString(_empty_out, "escli --json empty", _ebox)
        self.assertEqual(_update_error.call_count, 2)

        _invalid_out = mock.MagicMock()
        _invalid_out.read.return_value = "{not-json}"
        with mock.patch.dict(gExascaleError, {"EMPTY_ESCLI_OUTPUT": "EMPTY_ESCLI_OUTPUT"}, clear=False):
            with mock.patch.object(_ebox, "mUpdateErrorObject") as _update_error_invalid:
                with self.assertRaises(ExacloudRuntimeError):
                    _escli.mGetDictFromOutputString(_invalid_out, "escli --json invalid", _ebox)
        _update_error_invalid.assert_called_once()

    def test_mIsEFRack_error_path(self):
        # Auto-generated test for mIsEFRack
        _ebox = self.mGetClubox()
        _cell = list(_ebox.mReturnCellNodes().keys())[0]

        _stdout = mock.MagicMock()
        _stdout.read.return_value = "cmd out"
        _stderr = mock.MagicMock()
        _stderr.read.return_value = "cmd err"
        _node = mock.MagicMock()
        _node.mExecuteCmd.return_value = (1, _stdout, _stderr)
        _node.mGetCmdExitStatus.return_value = 1

        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context), \
             mock.patch.object(_ebox, "mUpdateErrorObject") as _error_mock:
            _escli = ebEscliUtils(_ebox)
            with self.assertRaises(ExacloudRuntimeError):
                _escli.mIsEFRack(_cell)

        _error_mock.assert_called_once()

    def test_mGetCtrlIP_exception_returns_empty_values(self):
        # Auto-generated test for mGetCtrlIP
        _ebox = self.mGetClubox()
        _escli = ebEscliUtils(_ebox)

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.ebCluExascaleConfig", side_effect=Exception("config lookup failed")):
            self.assertEqual(_escli.mGetCtrlIP(), ("", ""))

    def test_mGetUser_fallback_and_no_match(self):
        # Auto-generated test for mGetUser
        _ebox = self.mGetClubox()
        _cell = list(_ebox.mReturnCellNodes().keys())[0]
        _options = SimpleNamespace(jsonconf=None)

        _stdout = mock.MagicMock()
        _stdout.read.return_value = '{"data":[{"id":"gridother-cluster"}]}'
        _node = mock.MagicMock()
        _node.mExecuteCmd.return_value = (0, _stdout, "")
        _node.mGetCmdExitStatus.return_value = 0

        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=Exception("missing ctrl")), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.2.0.1", "ers-host")) as _ctrl_mock, \
             mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            _escli = ebEscliUtils(_ebox)
            _user = _escli.mGetUser(_cell, "cluster-a", _options)

        self.assertEqual(_user, "")
        _ctrl_mock.assert_called_once()
        _node.mExecuteCmd.assert_called_once_with(
            f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.2.0.1:{CTRL_PORT} --json lsuser"
        )

    def test_mGetClusterID_returns_empty_cluster_id_when_user_missing(self):
        # Auto-generated test for mGetClusterID
        _ebox = self.mGetClubox()
        _cell = list(_ebox.mReturnCellNodes().keys())[0]
        _options = SimpleNamespace(jsonconf=None)

        _stdout = mock.MagicMock()
        _stdout.read.return_value = '{"data":[{"attributes":{"giClusterName":"%s","giClusterId":"cluster-id-1"}}]}' % (
            _ebox.mGetClusters().mGetCluster().mGetCluName()
        )
        _node = mock.MagicMock()
        _node.mExecuteCmd.return_value = (0, _stdout, "")
        _node.mGetCmdExitStatus.return_value = 0

        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=Exception("missing ctrl")), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.2.0.2", "ers-host")) as _ctrl_mock, \
             mock.patch.object(ebEscliUtils, "mGetUser", return_value="") as _get_user_mock, \
             mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            _escli = ebEscliUtils(_ebox)
            _cluster_name, _cluster_id = _escli.mGetClusterID(_cell, _options)

        self.assertEqual((_cluster_name, _cluster_id), ("", ""))
        _ctrl_mock.assert_called_once()
        _get_user_mock.assert_called_once()

    def test_mRemoveFile_missing_ctrl_fallback(self):
        # Auto-generated test for mRemoveFile
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = SimpleNamespace(jsonconf=None)

        _mock_node = mock.MagicMock()
        _context = mock.MagicMock()
        _context.__enter__.return_value = _mock_node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            with mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.0.0.7", "host")):
                _escli = ebEscliUtils(_ebox)
                _escli.mRemoveFile(_cell, "@vault1/file", _options, aForce=True)

        _mock_node.mExecuteCmdLog.assert_called_once_with(f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.0.0.7:{CTRL_PORT} rmfile @vault1/file --force")

    def test_mCreateEsWalletUser_acl_json_parse_error(self):
        # Auto-generated test for mCreateEsWalletUser
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]
        _options = SimpleNamespace(jsonconf={
            "exascale": {
                "ctrl_network": {"ip": "10.0.0.31", "port": "5052"}
            }
        })

        _mk_stdout = mock.MagicMock()
        _mk_stdout.readlines.return_value = []
        _lsacl_stdout = mock.MagicMock()
        _lsacl_stdout.readlines.return_value = ["{not-json}"]

        _mock_node = mock.MagicMock()
        _mock_node.mFileExists.return_value = True
        _mock_node.mExecuteCmd.side_effect = [
            (0, _mk_stdout, ""),
            (0, _lsacl_stdout, ""),
        ]
        _context = mock.MagicMock()
        _context.__enter__.return_value = _mock_node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context), \
             mock.patch("exabox.ovm.csstep.exascale.escli_util.node_exec_cmd_check") as _exec_check_mock, \
             mock.patch.object(_ebox, "mUpdateErrorObject") as _error_mock:
            _escli = ebEscliUtils(_ebox)
            with self.assertRaises(ExacloudRuntimeError):
                _escli.mCreateEsWalletUser(_options, _cell, "user05", aVaultName="vault1")

        _exec_check_mock.assert_not_called()
        _error_mock.assert_called_once()

    def test_mGetEDVInitiator_fallback_no_match(self):
        # Auto-generated test for mGetEDVInitiator
        _ebox = self.mGetClubox()
        _cell = list(_ebox.mReturnCellNodes().keys())[0]
        _options = SimpleNamespace(jsonconf=None)

        _stdout = mock.MagicMock()
        _stdout.read.return_value = '{"data":[{"id":"init-1","attributes":{"hostName":"other-host"}}]}'
        _node = mock.MagicMock()
        _node.mExecuteCmd.return_value = (0, _stdout, "")
        _node.mGetCmdExitStatus.return_value = 0
        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=Exception("missing ctrl")), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.3.0.1", "ers")) as _ctrl_mock, \
             mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            _escli = ebEscliUtils(_ebox)
            _initiator_id = _escli.mGetEDVInitiator(_cell, "host-1", _options)

        self.assertEqual(_initiator_id, "")
        _ctrl_mock.assert_called_once()

    def test_mGetClusterID_error_path(self):
        # Auto-generated test for mGetClusterID
        _ebox = self.mGetClubox()
        _cell = list(_ebox.mReturnCellNodes().keys())[0]
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _stdout = mock.MagicMock()
        _stdout.read.return_value = "{}"
        _node = mock.MagicMock()
        _node.mExecuteCmd.return_value = (1, _stdout, "")
        _node.mGetCmdExitStatus.return_value = 1
        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context), \
             mock.patch.object(_ebox, "mUpdateErrorObject") as _error_mock:
            _escli = ebEscliUtils(_ebox)
            with self.assertRaises(ExacloudRuntimeError):
                _escli.mGetClusterID(_cell, _options)

        _error_mock.assert_called_once()

    def test_mGetVolumeID_fallback_and_error_paths(self):
        # Auto-generated test for mGetVolumeID
        _ebox = self.mGetClubox()
        _cell = list(_ebox.mReturnCellNodes().keys())[0]
        _options = SimpleNamespace(jsonconf=None)

        _stdout_ok = mock.MagicMock()
        _stdout_ok.read.return_value = '{"data":[{"id":"vol-1","attributes":{"name":"different-vol","owners":"owner1"}}]}'
        _node_ok = mock.MagicMock()
        _node_ok.mExecuteCmd.return_value = (0, _stdout_ok, "")
        _node_ok.mGetCmdExitStatus.return_value = 0
        _context_ok = mock.MagicMock()
        _context_ok.__enter__.return_value = _node_ok
        _context_ok.__exit__.return_value = None

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=Exception("missing ctrl")), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.3.0.2", "ers")) as _ctrl_mock, \
             mock.patch.object(ebEscliUtils, "mGetDBVaultName", return_value="vaultFallback") as _vault_mock, \
             mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context_ok):
            _escli = ebEscliUtils(_ebox)
            self.assertEqual(_escli.mGetVolumeID(_cell, "target-vol", _options, aVaultName="image"), ("", ""))

        _ctrl_mock.assert_called_once()
        _vault_mock.assert_called_once()

        _stdout_err = mock.MagicMock()
        _stdout_err.read.return_value = "{}"
        _node_err = mock.MagicMock()
        _node_err.mExecuteCmd.return_value = (1, _stdout_err, "")
        _node_err.mGetCmdExitStatus.return_value = 1
        _context_err = mock.MagicMock()
        _context_err.__enter__.return_value = _node_err
        _context_err.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context_err), \
             mock.patch.object(_ebox, "mUpdateErrorObject") as _error_mock:
            _escli = ebEscliUtils(_ebox)
            with self.assertRaises(ExacloudRuntimeError):
                _escli.mGetVolumeID(_cell, "target-vol", copy.deepcopy(self.mGetClubox().mGetArgsOptions()))

        _error_mock.assert_called_once()

    def test_mGetVolumeAttachments_fallback_no_match(self):
        # Auto-generated test for mGetVolumeAttachments
        _ebox = self.mGetClubox()
        _cell = list(_ebox.mReturnCellNodes().keys())[0]
        _options = SimpleNamespace(jsonconf=None)

        _stdout = mock.MagicMock()
        _stdout.read.return_value = '{"data":[{"id":"attach-1","attributes":{"volume":"other-vol","deviceName":"dev1"}}]}'
        _node = mock.MagicMock()
        _node.mExecuteCmd.return_value = (0, _stdout, "")
        _node.mGetCmdExitStatus.return_value = 0
        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=Exception("missing ctrl")), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.3.0.3", "ers")) as _ctrl_mock, \
             mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            _escli = ebEscliUtils(_ebox)
            self.assertEqual(_escli.mGetVolumeAttachments(_cell, "target-vol", _options), ("", "", ""))

        _ctrl_mock.assert_called_once()

    def test_mGetACFSFileSystem_fallback_error_path(self):
        # Auto-generated test for mGetACFSFileSystem
        _ebox = self.mGetClubox()
        _cell = list(_ebox.mReturnCellNodes().keys())[0]
        _options = SimpleNamespace(jsonconf=None)

        _stdout = mock.MagicMock()
        _stdout.read.return_value = "{}"
        _node = mock.MagicMock()
        _node.mExecuteCmd.return_value = (1, _stdout, "")
        _node.mGetCmdExitStatus.return_value = 1
        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=Exception("missing ctrl")), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.3.0.4", "ers")) as _ctrl_mock, \
             mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context), \
             mock.patch.object(_ebox, "mUpdateErrorObject") as _error_mock:
            _escli = ebEscliUtils(_ebox)
            with self.assertRaises(ExacloudRuntimeError):
                _escli.mGetACFSFileSystem(_cell, "vol-1", _options)

        _ctrl_mock.assert_called_once()
        _error_mock.assert_called_once()

    def test_mGetACFSFileSystemByJsonFormat_fallback_executes(self):
        # Auto-generated test for mGetACFSFileSystemByJsonFormat
        _ebox = self.mGetClubox()
        _cell = list(_ebox.mReturnCellNodes().keys())[0]
        _options = SimpleNamespace(jsonconf=None)

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=Exception("missing ctrl")), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.3.0.5", "ers")) as _ctrl_mock, \
             mock.patch.object(ebEscliUtils, "mExecuteEscliCmd", return_value=(0, "{}", "")) as _exec_mock:
            _escli = ebEscliUtils(_ebox)
            self.assertEqual(_escli.mGetACFSFileSystemByJsonFormat(_cell, _options), (0, "{}", ""))

        _ctrl_mock.assert_called_once()
        _exec_mock.assert_called_once_with(
            _cell,
            f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.0.5:{CTRL_PORT} --json lsacfsfilesystem --attributes id,volume,mountPath,size,totalFree",
        )

    def test_mChangeACL_fallback_paths(self):
        # Auto-generated test for mChangeACL
        _ebox = self.mGetClubox()
        _cell = list(_ebox.mReturnCellNodes().keys())[0]
        _options = SimpleNamespace(jsonconf=None)

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=Exception("missing ctrl")), \
             mock.patch.object(ebEscliUtils, "mGetDBVaultName", return_value="vaultFallback") as _vault_mock, \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.3.0.6", "ers")) as _ctrl_mock, \
             mock.patch.object(ebEscliUtils, "mGetDBServerStatus", return_value=(2, "")) as _status_mock:
            _escli = ebEscliUtils(_ebox)
            self.assertIsNone(_escli.mChangeACL(_cell, "clusterA", "read", _options, aHost="host1.example.com", aVaultName="vaultCustom"))

        _vault_mock.assert_called_once()
        _ctrl_mock.assert_called_once()
        _status_mock.assert_called_once_with("host1.example.com", aService="esnpStatus")

        _node = mock.MagicMock()
        _node.mGetCmdExitStatus.return_value = 1
        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=Exception("missing ctrl")), \
             mock.patch.object(ebEscliUtils, "mGetDBVaultName", return_value="vaultFallback"), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.3.0.7", "ers")), \
             mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context), \
             mock.patch.object(_ebox, "mUpdateErrorObject") as _error_mock:
            _escli = ebEscliUtils(_ebox)
            with self.assertRaises(ExacloudRuntimeError):
                _escli.mChangeACL(_cell, "clusterA", "read", _options)

        _node.mExecuteCmdLog.assert_called_once_with(
            f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.0.7:{CTRL_PORT} chacl @vaultFallback +clusterA:read"
        )
        _error_mock.assert_called_once()

    def test_wrapper_fallback_commands(self):
        # Auto-generated test for mCreateEDVVolume
        # Auto-generated test for mCreateACFSFileSystem
        # Auto-generated test for mChangeVolume
        # Auto-generated test for mMountACFSFileSystem
        # Auto-generated test for mUnMountACFSFileSystem
        # Auto-generated test for mRemoveEDVAttachment
        # Auto-generated test for mRemoveEDVVolume
        # Auto-generated test for mRemoveUser
        _ebox = self.mGetClubox()
        _cell = list(_ebox.mReturnCellNodes().keys())[0]
        _options = SimpleNamespace(jsonconf=None)

        _node = mock.MagicMock()
        _node.mGetCmdExitStatus.side_effect = [0, 0, 1, 1, 1, 0, 0, 0]
        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=Exception("missing ctrl")), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.3.0.8", "ers")), \
             mock.patch.object(ebEscliUtils, "mGetDBVaultName", return_value="vaultFallback"), \
             mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context), \
             mock.patch.object(_ebox, "mUpdateErrorObject") as _error_mock:
            _escli = ebEscliUtils(_ebox)
            self.assertEqual(_escli.mCreateEDVVolume(_cell, "100G", "volA", _options), 0)
            self.assertEqual(_escli.mCreateACFSFileSystem(_cell, "volA", "/mnt/a", "fsA", "gridA", _options), 0)
            with self.assertRaises(ExacloudRuntimeError):
                _escli.mChangeVolume(_cell, "volA", "gridA", _options)
            with self.assertRaises(ExacloudRuntimeError):
                _escli.mMountACFSFileSystem(_cell, "volA", "/mnt/a", "gridA", _options)
            with self.assertRaises(ExacloudRuntimeError):
                _escli.mUnMountACFSFileSystem(_cell, "acfsA", _options)
            _escli.mRemoveEDVAttachment(_cell, _options, "attachA", aForce=True)
            _escli.mRemoveEDVVolume(_cell, "volA", _options)
            _escli.mRemoveUser(_cell, "gridA", _options)

        self.assertGreaterEqual(_error_mock.call_count, 3)
        _commands = [str(_call[0][0]) for _call in _node.mExecuteCmdLog.call_args_list]
        self.assertIn(f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.0.8:{CTRL_PORT} mkvolume 100G --vault vaultFallback --attributes name=volA", _commands)
        self.assertIn(f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.0.8:{CTRL_PORT} mkacfsfilesystem volA /mnt/a --attributes name=fsA,user=gridA,mountLeafOwner=1001,mountLeafGroup=1001,mountLeafMode=0755", _commands)
        self.assertIn(f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.0.8:{CTRL_PORT} chvolume volA --attributes owners=+gridA", _commands)
        self.assertIn(f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.0.8:{CTRL_PORT} acfsctl register volA /mnt/a --attributes mountLeafOwner=1001,mountLeafGroup=1001,mountLeafMode=0755,user=gridA", _commands)
        self.assertIn(f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.0.8:{CTRL_PORT} acfsctl deregister acfsA", _commands)
        self.assertIn(f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.0.8:{CTRL_PORT} rmvolumeattachment attachA --force", _commands)
        self.assertIn(f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.0.8:{CTRL_PORT} rmvolume volA", _commands)
        self.assertIn(f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.0.8:{CTRL_PORT} rmuser gridA", _commands)

    def test_fallback_execute_wrappers(self):
        # Auto-generated test for mListFiles
        # Auto-generated test for mListVault
        # Auto-generated test for mRemoveVault
        # Auto-generated test for mListStoragePool
        # Auto-generated test for mCurrentStoragePoolSize
        # Auto-generated test for mReconfigStoragePool
        # Auto-generated test for mGetClusterAttribute
        _ebox = self.mGetClubox()
        _cell = list(_ebox.mReturnCellNodes().keys())[0]
        _options = SimpleNamespace(jsonconf=None)

        _node = mock.MagicMock()
        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=Exception("missing ctrl")), \
             mock.patch.object(ebEscliUtils, "mGetDBVaultName", return_value="vaultFallback"), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.3.0.9", "ers")) as _ctrl_mock, \
             mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context), \
             mock.patch.object(ebEscliUtils, "mExecuteEscliCmd", side_effect=[
                 (0, "", ""),
                 (0, "vault-out", ""),
                 (0, "rmvault-out", ""),
                 (0, "pool-out", ""),
                 (0, "curr-out", ""),
                 (0, "reconfig-out", ""),
                 (0, "cluster-out", ""),
             ]) as _exec_mock:
            _escli = ebEscliUtils(_ebox)
            self.assertEqual(_escli.mListFiles(_cell, "@vaultFallback/*", _options), [])
            self.assertEqual(_escli.mListVault(_cell, "vaultA", _options, aDetail=True), (0, "vault-out", ""))
            self.assertEqual(_escli.mRemoveVault(_cell, "vaultA", _options), (0, "rmvault-out", ""))
            self.assertEqual(_escli.mListStoragePool(_cell, "poolA", _options), (0, "pool-out", ""))
            self.assertEqual(_escli.mCurrentStoragePoolSize(_cell, "poolA", _options), (0, "curr-out", ""))
            self.assertEqual(_escli.mReconfigStoragePool(_cell, "poolA", _options), (0, "reconfig-out", ""))
            self.assertEqual(_escli.mGetClusterAttribute(_cell, "autoFileEncryption", _options), (0, "cluster-out", ""))

        self.assertGreaterEqual(_ctrl_mock.call_count, 7)
        self.assertEqual(_exec_mock.call_args_list[0][0], (_cell, f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.0.9:{CTRL_PORT} ls @vaultFallback/*"))
        self.assertEqual(_exec_mock.call_args_list[1][0], (_cell, f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.0.9:{CTRL_PORT} --json lsvault @vaultA --detail"))
        self.assertEqual(_exec_mock.call_args_list[2][0], (_cell, f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.0.9:{CTRL_PORT} rmvault @vaultA"))
        self.assertEqual(_exec_mock.call_args_list[3][0], (_cell, f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.0.9:{CTRL_PORT} --json  lsstoragepool poolA --attributes spaceRaw,spaceProvisioned,spaceUsed"))
        self.assertEqual(_exec_mock.call_args_list[4][0], (_cell, f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.0.9:{CTRL_PORT} --json  lsstoragepool poolA --attributes spaceProvisionable,spaceProvisioned,spaceUsed"))
        self.assertEqual(_exec_mock.call_args_list[5][0], (_cell, f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.0.9:{CTRL_PORT} chstoragepool poolA --reconfig --force"))
        self.assertEqual(_exec_mock.call_args_list[6][0], (_cell, f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.0.9:{CTRL_PORT} lscluster --attributes autoFileEncryption"))

    def test_mCreateEDVVolumeAttachment_ctrl_lookup_failure(self):
        # Auto-generated test for mCreateEDVVolumeAttachment
        _ebox = self.mGetClubox()
        _cell = list(_ebox.mReturnCellNodes().keys())[0]
        _options = SimpleNamespace(jsonconf=None)

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=Exception("missing ctrl")), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", side_effect=Exception("lookup failed")):
            _escli = ebEscliUtils(_ebox)
            with self.assertRaises(Exception):
                _escli.mCreateEDVVolumeAttachment(_cell, "2:vol", "xacfsvol", "cluster-id", "griduser", _options)

    def test_mGetUser_result_without_id_returns_empty(self):
        # Auto-generated test for mGetUser
        _ebox = self.mGetClubox()
        _cell = list(_ebox.mReturnCellNodes().keys())[0]
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)

        _stdout = mock.MagicMock()
        _stdout.read.return_value = '{"data":[{"id":"gridcluster-a"}]}'
        _node = mock.MagicMock()
        _node.mExecuteCmd.return_value = (0, _stdout, "")
        _node.mGetCmdExitStatus.return_value = 0
        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context), \
             mock.patch.object(ebEscliUtils, "mGetDictFromOutputString", return_value={"data": [{"id": "gridcluster-a"}]}), \
             mock.patch.object(ebEscliUtils, "mParseEscliJson", return_value={"hostName": "cluster-a"}):
            _escli = ebEscliUtils(_ebox)
            self.assertEqual(_escli.mGetUser(_cell, "cluster-a", _options), "")

    def test_mResizeEDVVolume_fallback_success(self):
        # Auto-generated test for mResizeEDVVolume
        _ebox = self.mGetClubox()
        _cell = list(_ebox.mReturnCellNodes().keys())[0]
        _options = SimpleNamespace(jsonconf=None)

        _node = mock.MagicMock()
        _node.mGetCmdExitStatus.return_value = 0
        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=Exception("missing ctrl")), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.3.1.1", "ers")) as _ctrl_mock, \
             mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            _escli = ebEscliUtils(_ebox)
            self.assertEqual(_escli.mResizeEDVVolume(_cell, "120G", "vol-fallback", _options), 0)

        _ctrl_mock.assert_called_once()
        _node.mExecuteCmdLog.assert_called_once_with(
            f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.1.1:{CTRL_PORT} chvolume vol-fallback --attributes size=120G"
        )

    def test_mCreateEDVVolumeAttachment_fallback_success(self):
        # Auto-generated test for mCreateEDVVolumeAttachment
        _ebox = self.mGetClubox()
        _cell = list(_ebox.mReturnCellNodes().keys())[0]
        _options = SimpleNamespace(jsonconf=None)

        _node = mock.MagicMock()
        _node.mGetCmdExitStatus.return_value = 0
        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=Exception("missing ctrl")), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.3.1.2", "ers")) as _ctrl_mock, \
             mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            _escli = ebEscliUtils(_ebox)
            self.assertEqual(
                _escli.mCreateEDVVolumeAttachment(_cell, "vol-fallback", "dev1", "cluster-id", "griduser", _options, aInitiatorID="init-1"),
                0,
            )

        _ctrl_mock.assert_called_once()
        _node.mExecuteCmdLog.assert_called_once_with(
            f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.1.2:{CTRL_PORT} mkvolumeattachment --protocol edv vol-fallback dev1 --initiator init-1 --attributes user=griduser"
        )

    def test_mRemoveACFSFileSystem_fallback_force_retry(self):
        # Auto-generated test for mRemoveACFSFileSystem
        _ebox = self.mGetClubox()
        _cell = list(_ebox.mReturnCellNodes().keys())[0]
        _options = SimpleNamespace(jsonconf=None)

        _node = mock.MagicMock()
        _node.mGetCmdExitStatus.side_effect = [1, 0]
        _context = mock.MagicMock()
        _context.__enter__.return_value = _node
        _context.__exit__.return_value = None

        with mock.patch.object(ebEscliUtils, "mParseExascaleAttrib", side_effect=Exception("missing ctrl")), \
             mock.patch.object(ebEscliUtils, "mGetCtrlIP", return_value=("10.3.1.3", "ers")) as _ctrl_mock, \
             mock.patch("exabox.ovm.csstep.exascale.escli_util.connect_to_host", return_value=_context):
            _escli = ebEscliUtils(_ebox)
            _escli.mRemoveACFSFileSystem(_cell, "acfs-fallback", _options)

        _ctrl_mock.assert_called_once()
        self.assertEqual(_node.mExecuteCmdLog.call_args_list[0][0][0], f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.1.3:{CTRL_PORT} rmacfsfilesystem acfs-fallback")
        self.assertEqual(_node.mExecuteCmdLog.call_args_list[1][0][0], f"{ESCLI} --wallet {WALLET_LOC} --ctrl 10.3.1.3:{CTRL_PORT} rmacfsfilesystem acfs-fallback --force")

if __name__ == '__main__':
    unittest.main()
