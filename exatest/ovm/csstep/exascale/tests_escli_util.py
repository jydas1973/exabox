#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/exascale/tests_escli_util.py /main/6 2025/08/25 12:12:16 pbellary Exp $
#
# tests_escli_util.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
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
                                exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.184.205:5052 lsuser | /bin/grep iad1046clu040a1", aRc=0, aStdout="gridiad1046clu040a1", aPersist=True)
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
                                exaMockCommand("/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsinitiator --attributes id,hostName", aRc=0, aStdout="a3311f85-8414-ac62-a331-1f858414ac62 scaqab10adm01", aPersist=True)
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
                                exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsinitiator --attributes giClusterName,giClusterId", aRc=0, aStdout="club086e35-128 9e827518-8a9f-5fd9-ffbe-c2ae1c46734c", aPersist=True)
                            ],
                            [
                                exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.184.205:5052 lsuser | /bin/grep club086e35-128", aRc=0, aStdout="gridclub086e35-128", aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _giclusterName, _giClusterId = _escli.mGetClusterID(_cell, _options)
        self.assertEqual(_giclusterName, "gridclub086e35-128")
        self.assertEqual(_giClusterId, "9e827518-8a9f-5fd9-ffbe-c2ae1c46734c")   

    def test_mGetVolumeIDP01(self):
        _ebox = self.mGetClubox()
        _cell_list = _ebox.mReturnCellNodes()
        _cell = list(_cell_list.keys())[0]

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(EXASCALE_PAYLOAD)
        _cmds = {
                    self.mGetRegexCell():
                        [
                            [
                                exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvolume --attributes id,vault,name,owner", aRc=0, aStdout="2:b4d00303b12f46d6a31b4a5339395cd3 @vault1clu02 acfs_gridclub086e35-128 admin", aPersist=True)
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
                                exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvolume --attributes id,vault,name,owner", aRc=0, aStdout="2:b4d00303b12f46d6a31b4a5339395cd3 @image acfs_gridclub086e35-128 admin", aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _vol_id, _owner = _escli.mGetVolumeID(_cell, "acfs_gridclub086e35-128", _options, aVaultName="image")
        self.assertEqual(_vol_id, "2:b4d00303b12f46d6a31b4a5339395cd3")
        self.assertEqual(_owner, "admin")

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
                                exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsvolumeattachment --attributes id,volume,deviceName", aRc=0, aStdout="3:175ebf661f8e49c09d03f8214f6c5b39 2:b4d00303b12f46d6a31b4a5339395cd3 xacfsvol", aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _id, _volume, _device_name = _escli.mGetVolumeAttachments(_cell, "2:b4d00303b12f46d6a31b4a5339395cd3", _options)
        self.assertEqual(_id, "3:175ebf661f8e49c09d03f8214f6c5b39")

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
                                exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 lsacfsfilesystem --attributes id,volume,mountPath,size", aRc=0, aStdout="1:6cafd8310b3d49a2becd17e9c08f7919 2:2fad5a43ed1f46be8eb3687ba59b1d00 /acfs_1 10.0000G", aPersist=True)
                            ]
                        ]
                }
        self.mPrepareMockCommands(_cmds)

        _escli = ebEscliUtils(_ebox)
        _acfs_id, _mount_path, _size = _escli.mGetACFSFileSystem(_cell, "2:2fad5a43ed1f46be8eb3687ba59b1d00", _options)
        self.assertEqual(_acfs_id, "1:6cafd8310b3d49a2becd17e9c08f7919")
        self.assertEqual(_size, "10.0000G")

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
                                exaMockCommand(re.escape("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet --ctrl 10.0.130.110:5052 acfsctl register 2:2fad5a43ed1f46be8eb3687ba59b1d00 /acfs_1 --attributes mountLeafMode=777,user=gridclub086e35-128"), aRc=0, aPersist=True)
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

if __name__ == '__main__':
    unittest.main() 
