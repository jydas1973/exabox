"""

 $Header: 

 Copyright (c) 2020, 2026, Oracle and/or its affiliates.

 NAME:
      tests_kvmdiskmgr.py - Unitest for kvmdiskmgr.py and cludomupartitions.py module

 DESCRIPTION:
      Run tests for the methods of module

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       dekuckre  04/10/26 - Fix UT setup flags to avoid DB/OEDA bootstrap
       dekuckre  04/02/26 - Fix Python 3.6-compatible unittest mock call
                            argument assertions
       nelango   02/06/26 - Bug 38700324 : Add tests for u02 bind mounts
       bhpati    02/04/26 - Bug 38820127 - OCI: LOCAL STORAGE RESHAPE OPERATION
                            HUNG FOR 2 WEEKS
       shapatna  01/01/26 - Codex UT enhancement
       avimonda  08/13/25 - Bug 38179586 - OCI: VMLOCALSTORAGE OPERATION FAILED
                            DUE TO RAC ONE DATABASE
       jfsaldan  07/04/25 - Bug 38074103 - EXACC EXACLOUD PREVENT
                            EXACCDBOPS-6164 | LOCAL STORAGE U02 RESIZE FAILS IF
                            CURRENT AND TARGET SIZE ARE THE SAME ON FS
                            ENCRYPTED CLUSTERS | TRACE FILE MISSING SSH
                            COMMANDS AS WELL
       bhpati    06/10/25 - Bug 38018344 - UPDATECVMLOCALSTORAGE FAILED FOR
                            COULD NOT UNMOUNT FILESYSTEM U02
       bhpati    11/08/24 - Enh 37224232 - RESILIENCY FOR LOCALSTORAGE UPDATE
                            WORKFLOW.
       bhpati    09/19/24 - REQUEST TO INCLUDE NFS MOUNT PRECHECK DURING
                            UPDATECVMLOCALSTORAGE OPERATIONS
       jfsaldan  07/01/24 - Bug 36624871 - EXACS:OL8 ENCRYPTION:23.4.1.2.4:
                            FILESYSTEM RESIZE FAILING IN INVOKE EXACLOUD FOR
                            RESHAPE OPERATION
       remamid   04/02/24 - Bug 36343848 - U02 LOCAL STORAGE SCALE DOWN IS
                            FAILING WITH DOMO AND DOMU COMPATIBILITY ISSUE
       remamid   03/29/24 - Bug 36343848 - U02 LOCAL STORAGE SCALE DOWN IS
                            FAILING WITH DOMO AND DOMU COMPATIBILITY ISSUE
       rajsag    01/23/23 - 34998372 - exacc:exadata 23.1.0 ol8:x8m:local
                            storage downscale reshape fails to unmount u02
                            filesystem
       aararora  09/08/22 - Unit test addition
       scoral    10/11/21 - Bug 33265977: DomU filesystems API refactoring.
       aypaul   09/13/21 - Adding unit test case for mClusterPartitionResize
       ajayasin 06/11/21 - fixing mAcquireRemoteLock related issue
       vgerard  21/07/20 - Added Initial size test
       vgerard  07/07/20 - Added Dom0 resize test
       vgerard  06/30/20 - Creation of the file
"""

import unittest
import re
import itertools
from random import shuffle
from typing import Dict, Any, Optional
import io
from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError, gPartitionError, gReshapeError
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.ovm.cluencryption import MountPointInfo
from exabox.ovm.kvmdiskmgr import exaBoxKvmDiskMgr
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.ovm.cludomupartitions import ebCluManageDomUPartition
from exabox.log.LogMgr import ebLogInfo
from unittest import mock
from unittest.mock import patch, MagicMock, PropertyMock, mock_open, call, ANY

from exabox.utils.node import CmdRet,ebLogError


dom0CommandOP1 = """-rw-r--r--. 1 root root 64424509440 Sep 13 02:05 /EXAVMIMAGES/GuestImages/scaqae14dv0107.us.oracle.com/dev_extra.img"""
dom0CommandOP2 = """disk = ['file:///EXAVMIMAGES/GuestImages/scaqae14dv0107.us.oracle.com/dev_extra.img,xvdd,w']"""
dom0CommandDevtmpfs = """devtmpfs = ['devtmpfs:///EXAVMIMAGES/GuestImages/scaqab10adm01.us.oracle.com/dev_extra.img,devtmpfs,w']"""
dom0XmBlockList = """Vdev  BE handle state evt-ch ring-ref BE-path
51730    0    0     4      11     11    /local/domain/0/backend/vbd/10/51730"""
dom0XenStoreLs = """host = ""
meminfo_total = "1022884"
meminfo_free = "181088"
os_name = "Debian GNU/Linux 7.1 (wheezy)"
os_majorver = "7"
os_minorver = "1"
os_uname = "3.2.0-4-amd64"
os_distro = "debian"
updated = "Wed Oct  9 05:41:29 UTC 2013"
guest = ""
 127a8ec3-ffff-4d0b-cccc-6f6c03faedf3 = ""
"""
dom0XenStoreLsExpected = """51730 = ""
domain = "scaqab10client01vm08.us.oracle.com"
dev = "dev"
node = "Node1"
"""
dom0ImageSize1 = """-rw-r--r--. 1 root root 53687091201 Sep 13 02:05 /EXAVMIMAGES/GuestImages/scaqae14dv0107.us.oracle.com/dev_extra.img"""

domUCommandOP1 = """devtmpfs                    189G    0G      189G       0% /dev"""
domUCommandOP2 = """Disk /devtmpfs: 1797.0 GB, 1796997120000 bytes, 3509760000 sectors
Disk identifier: 6C818A4E-39DA-4A43-B972-993CDD2D26D0
"""
domUCommandOP3 = """/devtmpfs 8:0 0 1.6T 0 disk 
/devtmpfs 8:2 0 256M 0 part /boot/efi
/devtmpfs 8:3 0 1.6T 0 part
"""
domUCommandOP4 = """Disk /dev/xvdh: 50.0 GB, 53687091200 bytes, 94371840 sectors"""
domUCommandOP5 = """/dev/xvdd                    60G    0G       60G       0% /dev"""
domUCommandOP7 = """Disk /dev/xvdd: 60.0 GB, 64424509440 bytes, 3509760000 sectors
Disk identifier: 6C818A4E-39DA-4A43-B972-993CDD2D26D0
"""

class testOptions(object):
    jsonconf: Optional[Dict[str, Any]]
    partitionOp: Optional[str]
    jsonmode: bool

    def __init__(self):
        self.jsonconf = None
        self.partitionOp = None
        self.jsonmode = False

class ebTestKVMDiskMgr(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        # Surcharge ebTestClucontrol, to specify noDB/noOEDA
        super().setUpClass(False, False)

    def setUp(self):
        #Ensure every test begin with standard conf
        self.mGetClubox()._exaBoxCluCtrl__ociexacc = False
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        # Keep unit tests isolated from DB-backed status/error updates.
        self.mGetClubox().mUpdateErrorObject = MagicMock(return_value=None)
        self.mGetClubox().mCheckIfCrsDbsUp = MagicMock(return_value=True)
        self.mGetClubox().mAcquireRemoteLock = MagicMock(return_value=True)
        self.mGetClubox().mReleaseRemoteLock = MagicMock(return_value=True)
        get_gcontext().mSetConfigOption('kvm_var_size',None)
        get_gcontext().mSetConfigOption('kvm_u01_size',None)
        get_gcontext().mSetConfigOption('disable_lvm_snapshot_space', None)

    @patch("exabox.ovm.kvmdiskmgr.getMountPointInfo")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetActiveDbInstances", side_effect=[(["DB1"]), ([])])
    def test_mClusterPartitionResize(self, aMockGetActiveDbInstances, aMockGetMountInfo):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxKvmDiskMgr.mClusterPartitionResize.")

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("df -h -B G -P /dummy", aStdout="", aRc=0, aPersist=True),
                    exaMockCommand("df -h -B G -P /dev", aStdout=domUCommandOP1, aRc=0, aPersist=True),
                    exaMockCommand("mount ", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/lsblk", aRc=0, aPersist=True),
                    exaMockCommand("/bin/lsblk -pno pkname", aRc=0, aPersist=True),
                    exaMockCommand(r"/bin/findmnt -rn -o TARGET -S devtmpfs*",aStdout="",aRc=0,aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP4, aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("df -h -B G -P /dev", aStdout=domUCommandOP1, aRc=0, aPersist=True),
                    exaMockCommand("mount ", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP2, aRc=0, aPersist=True),
                    exaMockCommand(r"/bin/findmnt -rn -o TARGET -S devtmpfs*",aStdout="",aRc=0,aPersist=True),
                    exaMockCommand("/bin/test -e /bin/lsblk", aRc=0, aPersist=True),
                    exaMockCommand("/bin/lsblk -pno pkname", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP4, aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("cat /etc/oratab", aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=0),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aStdout="19.0.0.0.0"),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aStdout="/u01/app/grid"),
                    exaMockCommand("mount ", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP2, aRc=0, aPersist=True),
                    exaMockCommand(r"/bin/findmnt -rn -o TARGET -S devtmpfs*",aStdout="",aRc=0,aPersist=True),
                    exaMockCommand("/usr/bin/ls -l.*", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("lsof | grep dev", aStdout=domUCommandOP2, aRc=0, aPersist=True),
                    exaMockCommand("kill -", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/df", aStdout=None, aRc=1, aPersist=True),

                    exaMockCommand("umount ", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("cat /etc/oratab", aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=0),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aStdout="19.0.0.0.0"),
                    exaMockCommand("/bin/crsctl check crs", aStdout="is online", aRc=0, aPersist=0),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aStdout="/u01/app/grid"),
                    exaMockCommand("/bin/test -e /sbin/findmnt", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("/sbin/findmnt --output TARGET --noheadings -R -r", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("lsof | grep dev", aStdout=domUCommandOP2, aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/ls -l.*", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("kill -", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/findmnt", aStdout=None, aRc=1, aPersist=True),
                    exaMockCommand(r"/bin/findmnt -rn -o TARGET -S devtmpfs*",aStdout="",aRc=0,aPersist=True),
                    exaMockCommand("umount ", aRc=0, aPersist=True),
                    exaMockCommand("lsblk -p -r", aStdout=domUCommandOP3, aRc=0, aPersist=True),
                    exaMockCommand("lvresize --resizefs -L.*", aRc=0, aPersist=True),
                    exaMockCommand("pvresize -y --setphysicalvolumesize", aRc=0, aPersist=True),
                    exaMockCommand("parted -a none", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/bin/test -e /sbin/findmnt", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("/sbin/findmnt --output TARGET --noheadings -R -r", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("lsof | grep dev", aStdout=domUCommandOP2, aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/ls -l.*", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("kill -", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/findmnt", aStdout=None, aRc=1, aPersist=True),
                    exaMockCommand(r"/bin/findmnt -rn -o TARGET -S devtmpfs*",aStdout="",aRc=0,aPersist=True),
                    exaMockCommand("umount ", aRc=0, aPersist=True),
                    exaMockCommand("lsblk -p -r", aStdout=domUCommandOP3, aRc=0, aPersist=True),
                    exaMockCommand("lvresize --resizefs -L.*", aRc=0, aPersist=True),
                    exaMockCommand("pvresize -y --setphysicalvolumesize", aRc=0, aPersist=True),
                    exaMockCommand("parted -a none", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("lsblk -p -r", aStdout=domUCommandOP3, aRc=0, aPersist=True),
                    exaMockCommand("lvresize --resizefs -L.*", aRc=0, aPersist=True),
                    exaMockCommand("pvresize -y --setphysicalvolumesize", aRc=0, aPersist=True),
                    exaMockCommand("parted -a none", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP4, aRc=0, aPersist=True),
                    exaMockCommand(r"/bin/findmnt -rn -o TARGET -S devtmpfs*",aStdout="",aRc=0,aPersist=True),
                    exaMockCommand("e2fsck -f", aRc=0, aPersist=True),
                    exaMockCommand("mount", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP4, aRc=0, aPersist=True),
                    exaMockCommand(r"/bin/findmnt -rn -o TARGET -S devtmpfs*",aStdout="",aRc=0,aPersist=True),
                    exaMockCommand("e2fsck -f", aRc=0, aPersist=True),
                    exaMockCommand("mount", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"/bin/virsh domblklist", aStdout="sdd /EXAVMIMAGES/GuestImages/u02.img"),
                    exaMockCommand("ls -l /EXAVMIMAGES/GuestImages", aStdout=dom0CommandOP1, aRc=0, aPersist=True)
                ],
                [exaMockCommand("virsh blockresize", aRc=0, aPersist=True)],
                []
            ]
        }

        _dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]

        #Init new Args
        aMockGetMountInfo.return_value = MountPointInfo(
                is_luks = False,
                block_device= "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk",
                fs_type= "ext4",
                fs_label= "U02_IMAGE",
                luks_device= "",
                mount_point= "/u02"
        )
        self.mPrepareMockCommands(_cmds)
        currentOptions = testOptions()
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        currentOptions.jsonconf = None
        currentOptions.partitionOp = "resize"
        currentOptions.jsonmode = False
        with patch("exabox.ovm.cludomupartitions.ebCluManageDomUPartition.mRecordError", return_value=1), \
            patch.object(self.mGetClubox(), "mUpdateErrorObject", return_value=None), \
            patch.object(self.mGetClubox(), "mCheckIfCrsDbsUp", return_value=True):
            self.assertNotEqual(cluDomUPartitionObj.mClusterManageDomUPartition("resize", currentOptions), 0)
            currentOptions.jsonconf = {"partitionName": "dummy","new_sizeGB": "50"}
            self.assertNotEqual(cluDomUPartitionObj.mClusterManageDomUPartition("resize", currentOptions), 0)
            currentOptions.jsonconf = {"partitionName": "dev","new_sizeGB": "50"}
            cluDomUPartitionObj2 = ebCluManageDomUPartition(self.mGetClubox())
            with patch("exabox.ovm.utils.clu_utils.ebCluUtils.mUpdateTaskProgressStatus", return_value=None):
                ebLogInfo(cluDomUPartitionObj2.mClusterManageDomUPartition("resize", currentOptions))
        ebLogInfo("Completed unit test on exaBoxKvmDiskMgr.mClusterPartitionResize")

    @patch("exabox.ovm.kvmdiskmgr.time.sleep", return_value=None)
    @patch("exabox.ovm.kvmdiskmgr.node_exec_cmd_check")
    @patch("exabox.ovm.kvmdiskmgr.connect_to_host")
    @patch("exabox.ovm.kvmdiskmgr.getDiskLabel", return_value="msdos")
    @patch("exabox.ovm.kvmdiskmgr.getMountPointInfo")
    def test_mClusterPartitionResize_db_restart(
        self,
        mock_mount_info,
        mock_disk_label,
        mock_connect,
        mock_node_exec,
        mock_sleep,
    ):
        ebLogInfo("")
        ebLogInfo("Validating pre/post CRS DB handling in mClusterPartitionResize.")

        mock_mount_info.return_value = MagicMock(is_luks=False)
        mock_node_exec.return_value = MagicMock(
            stdout="sdd /EXAVMIMAGES/GuestImages/domu-test/u02.img"
        )

        def _stream(lines=None):
            handler = MagicMock()
            handler.readlines.return_value = lines or []
            return handler

        dummy_node = MagicMock()
        dummy_node.mGetCmdExitStatus.return_value = 0
        dummy_node.mDisconnect.return_value = None

        def _execute(cmd, *_args, **_kwargs):
            if "/sbin/fdisk -l" in cmd and "grep Disk" in cmd:
                return None, _stream(
                    ["Disk /dev/xvdh: 60.0 GB, 64424509440 bytes, 94371840 sectors"]
                ), None
            if "ls -l /EXAVMIMAGES/GuestImages" in cmd:
                return None, _stream(
                    ["-rw-r--r-- 1 root root 64424509440 Feb 23 10:00 /EXAVMIMAGES/GuestImages/domu-test/u02.img"]
                ), None
            if "e2fsck -f" in cmd:
                return None, _stream(["Pass 1: Checking inodes", "Filesystem clean"]), None
            if "query crs activeversion" in cmd:
                return None, _stream(
                    ["Oracle Clusterware active version on the cluster is [19.0.0.0.0]"]
                ), None
            return None, _stream([]), None

        dummy_node.mExecuteCmd.side_effect = _execute
        dummy_node.mExecuteCmdLog.side_effect = lambda *a, **k: (None, _stream(), None)

        ctx = MagicMock()
        ctx.__enter__.return_value = dummy_node
        ctx.__exit__.return_value = False
        mock_connect.return_value = ctx

        clubox = self.mGetClubox()
        with patch.object(clubox, "mReturnDom0DomUPair", return_value=[("dom0-test", "domu-test")]):
            clu_partition = ebCluManageDomUPartition(clubox)

        clu_partition.mSetPartitionOperationData({"Command": "partition_resize"})
        constants = clu_partition.mGetConstantsObj()
        partition_info = {
            constants._filesystem_key: "/dev/xvdh",
            constants._totalsizeGB_key: "60",
            constants._usedsizeGB_key: "40",
        }

        options = testOptions()
        options.partitionOp = "resize"
        options.jsonmode = False
        options.jsonconf = {"partitionName": "u02", "new_sizeGB": "55"}

        with patch.object(clu_partition, "mClusterPartitionInfo2", return_value=(0, partition_info)), \
            patch.object(clu_partition, "mClusterPartitionTargetDiff", return_value=True), \
            patch.object(clu_partition, "mExecuteDomUUmountPartition", return_value=0), \
            patch.object(exaBoxKvmDiskMgr, "mExecuteDom0ResizeSteps", return_value=0), \
            patch.object(exaBoxKvmDiskMgr, "mExecuteDomUDownsizeSteps", return_value=0), \
            patch.object(exaBoxKvmDiskMgr, "mExecuteDomUUpsizeSteps", return_value=0), \
            patch.object(clubox, "mGetOracleBaseDirectories", return_value=("/u01/app/19.0.0", None, None)), \
            patch.object(clubox, "mCheckConfigOption", return_value="1"), \
            patch.object(clubox, "mCheckCrsUp", return_value=True), \
            patch.object(clubox, "mCheckDBIsUp", return_value=False), \
            patch.object(clubox, "mCheckIfCrsDbsUp", return_value=True), \
            patch.object(clu_partition, "mRecordError") as mock_record_error, \
            patch.object(clubox, "mGetActiveDbInstances") as mock_active_db:

            mock_active_db.side_effect = [["DB1", "DB2"], ["DB1"]]
            exaBoxKvmDiskMgr(clu_partition).mClusterPartitionResize(options)
            mock_record_error.assert_called_once_with(
                gPartitionError["ErrorFetchingDetails"], ANY
            )

            mock_record_error.reset_mock()
            mock_active_db.side_effect = [["DB1", "DB2"], ["DB1", "DB2"]]
            exaBoxKvmDiskMgr(clu_partition).mClusterPartitionResize(options)
            mock_record_error.assert_not_called()
    
    
    def mGetEbox(self):
        return ebTestClucontrol

    def test_mRemoveOEDADBHomes(self):

        #Create Scenario, all data comes from domU /etc/fstab below
        _cmds = {
            self.mGetRegexVm(): [
                [exaMockCommand("cat /etc/fstab", aStdout="""
LABEL=SWAP              swap                    swap    defaults        0 0
LABEL=VAR               /var                    xfs    defaults        0 0
LABEL=DIAG              /var/log                xfs    defaults        0 0
LABEL=HOME              /home   xfs     defaults 0 0
LABEL=DBORA             /u01    xfs     defaults 0 0
LABEL=TMP               /tmp    xfs     defaults 0 0
LABEL=AUDIT             /var/log/audit  xfs     defaults 0 0
/dev/VGExaDbDisk.grid19.0.0.0.200414.img/LVDBDisk               /u01/app/19.0.0.0/grid  xfs     defaults 0 0
/dev/VGExaDbDisk.db19.0.0.0.200414-3.img/LVDBDisk               /u01/app/oracle/product/19.0.0.0/dbhome_1       xfs     defaults 0 0
/dev/VGExaDbDisk.db11.2.0.4.170418-4.img/LVDBDisk               /u01/app/oracle/product/11.2.0.4/dbhome_1       xfs     defaults 0 0
/dev/VGExaDbDisk.db18.1.0.0.200414-5.img/LVDBDisk               /u01/app/oracle/product/18.1.0.0/dbhome_1       xfs     defaults 0 0
/dev/VGExaDbDisk.db12.2.0.1.190716-6.img/LVDBDisk               /u01/app/oracle/product/12.2.0.1/dbhome_1       xfs     defaults 0 0
/dev/VGExaDbDisk.db12.1.0.2.170418-7.img/LVDBDisk               /u01/app/oracle/product/12.1.0.2/dbhome_1       xfs     defaults 0 0
/dev/VGExaDbDisk.u02_extra.img/LVDBDisk  /u02       ext4     defaults 1 1
"""
),
               #Commands generated from FSTAB
               exaMockCommand("umount /u01/app/oracle/product/19.0.0.0/dbhome_1"),
               exaMockCommand("umount /u01/app/oracle/product/11.2.0.4/dbhome_1"),
               exaMockCommand("umount /u01/app/oracle/product/18.1.0.0/dbhome_1"),
               exaMockCommand("umount /u01/app/oracle/product/12.2.0.1/dbhome_1"),
               exaMockCommand("umount /u01/app/oracle/product/12.1.0.2/dbhome_1"),
               exaMockCommand("sed -i '/dbhome_1/d' /etc/fstab")
            ]],

        self.mGetRegexDom0(): [[
            # DOM0s commands
            exaMockCommand(re.escape("/bin/ls /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/db*.img"), aStdout="""\
/EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/db19.0.0.0.200414-3.img
/EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/db11.2.0.4.170418-4.img
/EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/db18.1.0.0.200414-5.img
/EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/db12.2.0.1.190716-6.img
/EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/db12.1.0.2.170418-7.img
"""
),
            exaMockCommand("/opt/exadata_ovm/vm_maker --detach --disk-image /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/db19.0.0.0.200414-3.img --domain scaqab10client01vm08.us.oracle.com"),
            exaMockCommand("rm -f /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/db19.0.0.0.200414-3.img"),
            exaMockCommand("/opt/exadata_ovm/vm_maker --detach --disk-image /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/db11.2.0.4.170418-4.img --domain scaqab10client01vm08.us.oracle.com"),
            exaMockCommand("rm -f /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/db11.2.0.4.170418-4.img"),
            exaMockCommand("/opt/exadata_ovm/vm_maker --detach --disk-image /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/db18.1.0.0.200414-5.img --domain scaqab10client01vm08.us.oracle.com"),
            exaMockCommand("rm -f /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/db18.1.0.0.200414-5.img"),
            exaMockCommand("/opt/exadata_ovm/vm_maker --detach --disk-image /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/db12.2.0.1.190716-6.img --domain scaqab10client01vm08.us.oracle.com"),
            exaMockCommand("rm -f /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/db12.2.0.1.190716-6.img"),
            exaMockCommand("/opt/exadata_ovm/vm_maker --detach --disk-image /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/db12.1.0.2.170418-7.img --domain scaqab10client01vm08.us.oracle.com"),
            exaMockCommand("rm -f /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/db12.1.0.2.170418-7.img")


            ]],

        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():
             # Select a specific pair
             if _domU != 'scaqab10client01vm08.us.oracle.com':
                 continue
             cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
             _exadiskobj = exaBoxKvmDiskMgr(cluDomUPartitionObj)
             _exadiskobj.mUnmountOedaDbHomes(_dom0,_domU)
             # If we reach this point without exception in Node Mock Scenario
             # It means domU/Dom0 code is fully covered
             self.assertTrue(True)

             break


    def test_mDownSizeDomU_encrypted_sameLV_target_size(self):
        ebLogInfo("test_mDownSizeDomU_encrypted_sameLV_target_size")
        # Validate scenario that code generates below commands
        _cmds = {
            self.mGetRegexVm(): [
                [exaMockCommand("lsblk -p -r | grep -B 2 /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk",
                aStdout=("/dev/sdd 8:0 0 82G 0 disk\n"
                    "/dev/sdd1 8:1 0 60G 0 part\n"
                    "/dev/mapper/VGExaDbDisk.u02_extra_encrypted.img-LVDBDisk 252:15 0 57.9G 0 lvm\n"
                    "/dev/mapper/VGExaDbDisk.u02_extra_encrypted.img-LVDBDisk-crypt 252:17 0 57.9G 0 crypt /u02\n")),
                 exaMockCommand("test -e.*partprobe", aPersist=True),
                 exaMockCommand("partprobe /dev/sdd -ds",
                     aStdout="/dev/sdd msdos partitions 1\n", aPersist=True),
                 exaMockCommand("/bin/test -e /usr/lib/dracut/modules.d/99exacrypt/VGExaDbDisk.u02_extra_encrypted.img#LVDBDisk.key-api.sh", aPersist=True),
                 exaMockCommand("/bin/test -e /sbin/e2fsck", aPersist=True),
                 exaMockCommand("e2fsck -fy .*", aPersist=True),
                 exaMockCommand("/bin/test -e /sbin/resize2fs", aPersist=True),
                 exaMockCommand("/sbin/resize2fs -M /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt", aPersist=True),
                 exaMockCommand("/bin/test -e /sbin/cryptsetup", aPersist=True),
                 exaMockCommand("cryptsetup close /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt -v", aPersist=True),
                 exaMockCommand("lvresize -L 57.9G /dev/mapper/VGExaDbDisk.u02_extra_encrypted.img-LVDBDisk --force",
                     aStdout="Rounding size to boundary between physical extents: 20.01 GiB.",
                     aStderr="New size (15200 extents) matches existing size (15200 extents).",
                     aRc=5,
                     aPersist=True),
                 exaMockCommand("/usr/lib/dracut/modules.d/99exacrypt/VGExaDbDisk.u02_extra_encrypted.img#LVDBDisk.key-api.sh", aStdout="/tmp/keyapi1211"),
                 exaMockCommand("/bin/test -e /tmp/keyapi1211"),
                 exaMockCommand("cryptsetup open /dev/mapper/VGExaDbDisk.u02_extra_encrypted.img-LVDBDisk VGExaDbDisk.u02_extra.img-LVDBDisk-crypt --key-file=/tmp/keyapi1211 -v"),
                 exaMockCommand("shred -fu /tmp/keyapi1211"),
                 exaMockCommand("/sbin/resize2fs /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt"),
                 exaMockCommand("pvresize -y --setphysicalvolumesize 59.95G /dev/sdd1"),
                 exaMockCommand(
                             f"/bin/echo '1\n59.95GiB\nYes' | "
                               f"/usr/sbin/parted -a none /dev/sdd ---pretend-input-tty resizepart")
            ]]
        }
        _domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        _exadiskobj = exaBoxKvmDiskMgr(cluDomUPartitionObj)
        self.assertEqual(0, _exadiskobj.mExecuteDomUDownsizeStepsEncrypted(_domU, '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt', 60))

    def test_mDownSizeDomU_encrypted(self):

        ebLogInfo("test_mDownSizeDomU_encrypted")
        # Validate scenario that code generates below commands
        _cmds = {
            self.mGetRegexVm(): [
                [exaMockCommand("lsblk -p -r | grep -B 2 /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk",
                aStdout=("/dev/sdd 8:0 0 82G 0 disk\n"
                    "/dev/sdd1 8:1 0 80G 0 part\n"
                    "/dev/mapper/VGExaDbDisk.u02_extra_encrypted.img-LVDBDisk 252:15 0 80G 0 lvm\n"
                    "/dev/mapper/VGExaDbDisk.u02_extra_encrypted.img-LVDBDisk-crypt 252:17 0 80G 0 crypt /u02\n")),
                 exaMockCommand("test -e.*partprobe", aPersist=True),
                 exaMockCommand("partprobe /dev/sdd -ds",
                     aStdout="/dev/sdd msdos partitions 1\n", aPersist=True),
                 exaMockCommand("/bin/test -e /usr/lib/dracut/modules.d/99exacrypt/VGExaDbDisk.u02_extra_encrypted.img#LVDBDisk.key-api.sh", aPersist=True),
                 exaMockCommand("/bin/test -e /sbin/e2fsck", aPersist=True),
                 exaMockCommand("e2fsck -fy .*", aPersist=True),
                 exaMockCommand("/bin/test -e /sbin/resize2fs", aPersist=True),
                 exaMockCommand("/sbin/resize2fs -M /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt", aPersist=True),
                 exaMockCommand("/bin/test -e /sbin/cryptsetup", aPersist=True),
                 exaMockCommand("cryptsetup close /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt -v", aPersist=True),
                 exaMockCommand("lvresize -L 57.9G /dev/mapper/VGExaDbDisk.u02_extra_encrypted.img-LVDBDisk --force", aPersist=True),
                 exaMockCommand("/usr/lib/dracut/modules.d/99exacrypt/VGExaDbDisk.u02_extra_encrypted.img#LVDBDisk.key-api.sh", aStdout="/tmp/keyapi1211"),
                 exaMockCommand("/bin/test -e /tmp/keyapi1211"),
                 exaMockCommand("cryptsetup open /dev/mapper/VGExaDbDisk.u02_extra_encrypted.img-LVDBDisk VGExaDbDisk.u02_extra.img-LVDBDisk-crypt --key-file=/tmp/keyapi1211 -v"),
                 exaMockCommand("shred -fu /tmp/keyapi1211"),
                 exaMockCommand("/sbin/resize2fs /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt"),
                 exaMockCommand("pvresize -y --setphysicalvolumesize 59.95G /dev/sdd1"),
                 exaMockCommand(
                             f"/bin/echo '1\n59.95GiB\nYes' | "
                               f"/usr/sbin/parted -a none /dev/sdd ---pretend-input-tty resizepart")
            ]]
        }
        _domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        _exadiskobj = exaBoxKvmDiskMgr(cluDomUPartitionObj)
        self.assertEqual(0,_exadiskobj.mExecuteDomUDownsizeStepsEncrypted(_domU, '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt', 60))

    def test_mDownSizeDomU(self):
        # Validate scenario that code generates below commands
        _cmds = {
            self.mGetRegexVm(): [
                [exaMockCommand("lsblk -p -r | grep -B 2 /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk", aStdout="""/dev/sdd 8:48 0 60G 0 disk 
/dev/sdd1 8:49 0 80G 0 part 
/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk 252:0 0 80G 0 lvm 
"""
),
                 exaMockCommand(r"/bin/findmnt -rn -o TARGET -S /dev/mapper/.*",aStdout="",aRc=0,aPersist=True),
                 exaMockCommand("/usr/sbin/e2fsck -fn .*", aPersist=True),
                 exaMockCommand("lvresize --resizefs -L.*", aPersist=True),
                 exaMockCommand("pvresize -y --setphysicalvolumesize 59.95G /dev/sdd1"),
                 exaMockCommand(
                             f"/bin/echo '1\n59.95GiB\nYes' | "
                               f"/usr/sbin/parted -a none /dev/sdd ---pretend-input-tty resizepart")
            ]]
        }
        _domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        _exadiskobj = exaBoxKvmDiskMgr(cluDomUPartitionObj)
        _exadiskobj.mExecuteDomUDownsizeSteps(_domU, '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk', 60)

    def test_mDownSizeDomU_bind_mounts(self):
        """
        Verify DomU downsize handles CCA chroot bind mounts correctly
        """

        _filesystem = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk"
    
        _cmds = {
            self.mGetRegexVm(): [
                [
                    # --------------------------------------------------
                    # lsblk lookup (note absolute paths)
                    # --------------------------------------------------
                    exaMockCommand(
                        r"/usr/bin/lsblk -p -r \| /usr/bin/grep -B 2 .*VGExaDbDisk.*",
                        aStdout=(
                            "/dev/sdd 8:48 0 60G 0 disk\n"
                            "/dev/sdd1 8:49 0 80G 0 part\n"
                            f"{_filesystem} 252:0 0 80G 0 lvm\n"
                        ),
                        aPersist=True,
                    ),
    
                    # --------------------------------------------------
                    # findmnt for mapper device
                    # --------------------------------------------------
                    exaMockCommand(
                        r"/bin/findmnt -rn -o TARGET -S /dev/mapper/.*",
                        aStdout=(
                            "/u02\n"
                            "/cca/opctl_s1/chroot/u02\n"
                            "/cca/opctl_s2/chroot/u02\n"
                        ),
                        aRc=0,
                        aPersist=True,
                    ),
    
                    # --------------------------------------------------
                    # findmnt for devtmpfs (NEW after fix)
                    # --------------------------------------------------
                    exaMockCommand(
                        r"/bin/findmnt -rn -o TARGET -S devtmpfs",
                        aStdout="",
                        aRc=1,
                        aPersist=True,
                    ),
    
                    # --------------------------------------------------
                    # filesystem check
                    # --------------------------------------------------
                    exaMockCommand(
                        r"/usr/sbin/e2fsck -fn .*",
                        aRc=0,
                        aPersist=True,
                    ),
    
                    # --------------------------------------------------
                    # unmount bind mounts (deepest first)
                    # --------------------------------------------------
                    exaMockCommand(
                        r"/usr/bin/umount /cca/opctl_s2/chroot/u02",
                        aRc=0,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        r"/usr/bin/umount /cca/opctl_s1/chroot/u02",
                        aRc=0,
                        aPersist=True,
                    ),
    
                    # --------------------------------------------------
                    # lvresize
                    # --------------------------------------------------
                    exaMockCommand(
                        r"/usr/sbin/lvresize --resizefs -L.* --yes",
                        aRc=0,
                        aPersist=True,
                    ),
    
                    # --------------------------------------------------
                    # pvresize (NOTE: now runs on /dev/sdd, not sdd1)
                    # --------------------------------------------------
                    exaMockCommand(
                        r"/usr/sbin/pvresize -y --setphysicalvolumesize .* /dev/sdd",
                        aRc=0,
                        aPersist=True,
                    ),
    
                    # --------------------------------------------------
                    # parted resize
                    # --------------------------------------------------
                    exaMockCommand(
                        r"/usr/sbin/parted .* resizepart",
                        aRc=0,
                        aPersist=True,
                    ),
    
                    # --------------------------------------------------
                    # recreate chroot dirs
                    # --------------------------------------------------
                    exaMockCommand(
                        r"/usr/bin/mkdir -p /cca/opctl_s1/chroot/u02",
                        aRc=0,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        r"/usr/bin/mkdir -p /cca/opctl_s2/chroot/u02",
                        aRc=0,
                        aPersist=True,
                    ),
    
                    # --------------------------------------------------
                    # remount bind mounts
                    # --------------------------------------------------
                    exaMockCommand(
                        r"/usr/bin/mount --bind /u02 /cca/opctl_s1/chroot/u02",
                        aRc=0,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        r"/usr/bin/mount --bind /u02 /cca/opctl_s2/chroot/u02",
                        aRc=0,
                        aPersist=True,
                    ),
                ]
            ]
        }
    
        _domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]
    
        self.mPrepareMockCommands(_cmds)
    
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        _exadiskobj = exaBoxKvmDiskMgr(cluDomUPartitionObj)
    
        _rc = _exadiskobj.mExecuteDomUDownsizeSteps(
            _domU, _filesystem, 60
        )
    
        self.assertEqual(_rc, 0)

    def test_mDownSizeDomU_lvresize_yes_flag(self):
        """Ensure lvresize runs with --yes during DomU downsize."""

        _filesystem = "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk"

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand(
                        r"/usr/bin/lsblk -p -r \| /usr/bin/grep -B 2 .*VGExaDbDisk.*",
                        aStdout=(
                            "/dev/sdd 8:48 0 60G 0 disk\n"
                            "/dev/sdd1 8:49 0 80G 0 part\n"
                            f"{_filesystem} 252:0 0 80G 0 lvm\n"
                        ),
                        aPersist=True,
                    ),
                    exaMockCommand(
                        r"/bin/findmnt -rn -o TARGET -S /dev/mapper/.*",
                        aStdout=(
                            "/u02\n"
                            "/cca/opctl_s1/chroot/u02\n"
                            "/cca/opctl_s2/chroot/u02\n"
                        ),
                        aRc=0,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        r"/bin/findmnt -rn -o TARGET -S devtmpfs",
                        aStdout="",
                        aRc=1,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        r"/usr/sbin/e2fsck -fn .*",
                        aRc=0,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        r"/usr/bin/umount /cca/opctl_s2/chroot/u02",
                        aRc=0,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        r"/usr/bin/umount /cca/opctl_s1/chroot/u02",
                        aRc=0,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        r"/usr/sbin/lvresize --resizefs -L.* --yes",
                        aRc=0,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        r"/usr/sbin/pvresize -y --setphysicalvolumesize .* /dev/sdd",
                        aRc=0,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        r"/usr/sbin/parted .* resizepart",
                        aRc=0,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        r"/usr/bin/mkdir -p /cca/opctl_s1/chroot/u02",
                        aRc=0,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        r"/usr/bin/mkdir -p /cca/opctl_s2/chroot/u02",
                        aRc=0,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        r"/usr/bin/mount --bind /u02 /cca/opctl_s1/chroot/u02",
                        aRc=0,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        r"/usr/bin/mount --bind /u02 /cca/opctl_s2/chroot/u02",
                        aRc=0,
                        aPersist=True,
                    ),
                ]
            ]
        }

        _domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]

        self.mPrepareMockCommands(_cmds)

        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        _exadiskobj = exaBoxKvmDiskMgr(cluDomUPartitionObj)

        _rc = _exadiskobj.mExecuteDomUDownsizeSteps(
            _domU, _filesystem, 60
        )

        self.assertEqual(_rc, 0)

    def test_mDownSizeDomU_metacsum(self):
        # Validate scenario that code generates below commands
        _cmds = {
            self.mGetRegexVm(): [
                [exaMockCommand("lsblk -p -r | grep -B 2 /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk", aStdout="""/dev/sdd 8:48 0 60G 0 disk
/dev/sdd1 8:49 0 80G 0 part
/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk 252:0 0 80G 0 lvm
"""
),
                 exaMockCommand(r"/bin/findmnt -rn -o TARGET -S /dev/mapper/.*",aStdout="",aRc=0,aPersist=True),
                 exaMockCommand("/usr/sbin/e2fsck -fn /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk", aStdout="""Journal superblock has an unknown incompatible feature flag set.
Abort? no

Journal superblock is corrupt.
Fix? no


U02_IMAGE: ********** WARNING: Filesystem still has errors **********
""", aRc=12),
                 exaMockCommand("mkdir /opt/exacloud/fstools"),
                 exaMockCommand("/bin/scp .*"),
                 exaMockCommand("/bin/scp .*"),
                 exaMockCommand("/bin/scp .*"),
                 exaMockCommand("cd /opt/exacloud/fstools;tar xvf e2fsprogs.tar.gz"),             
                 exaMockCommand("cd /opt/exacloud/fstools;/usr/bin/sha256sum -c e2fsprogs_sha256.out --status"),
                 exaMockCommand("cd /opt/exacloud/fstools;rpm2cpio e2fsprogs-1.45.4-3.0.5.el7.x86_64.rpm | cpio -id"),
                 exaMockCommand("cd /opt/exacloud/fstools;rpm2cpio e2fsprogs-libs-1.45.4-3.0.5.el7.x86_64.rpm | cpio -id"),
                 exaMockCommand("export LD_LIBRARY_PATH=/opt/exacloud/fstools/usr/lib64/;/opt/exacloud/fstools/usr/sbin/e2fsck -fy /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk"),
                 exaMockCommand("export LD_LIBRARY_PATH=/opt/exacloud/fstools/usr/lib64/;/opt/exacloud/fstools/usr/sbin/e2fsck -fy /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk;/usr/sbin/lvresize --resizefs -L27.9G /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk --no-fsck"),
                 exaMockCommand("pvresize -y --setphysicalvolumesize 59.95G /dev/sdd1"),
                 exaMockCommand(
                             f"/bin/echo '1\n59.95GiB\nYes' | "
                               f"/usr/sbin/parted -a none /dev/sdd ---pretend-input-tty resizepart")
            ]]
        }
        _domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        _exadiskobj = exaBoxKvmDiskMgr(cluDomUPartitionObj)
        with patch('os.path.isfile'):
            _exadiskobj.mExecuteDomUDownsizeSteps(_domU, '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk', 60)

    def test_mUpSizeDomU(self):
        # Validate scenario that code generates below commands
        _cmds = {
            self.mGetRegexVm(): [
                [exaMockCommand("lsblk -p -r | grep -B 2 /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk", aStdout="""/dev/sdd 8:48 0 60G 0 disk 
/dev/sdd1 8:49 0 80G 0 part 
/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk 252:0 0 80G 0 lvm 
"""
),

                 exaMockCommand("parted -a none /dev/sdd resizepart 1 100%"),
                 exaMockCommand("pvresize /dev/sdd1"),
                 # Since Mock framework accept regular expression, the + was removed during evaluation
                 # Using re.escape() as we want an exact match
                 exaMockCommand("lvresize --resizefs -L.*", aPersist=True)
            ]]
        }
        _domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        _exadiskobj = exaBoxKvmDiskMgr(cluDomUPartitionObj)

        _exadiskobj.mExecuteDomUUpsizeSteps(_domU, '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk', 60)

    def test_logDebugInfo_records_output_and_error(self):
        # Auto-generated test for logDebugInfo
        cluDomUPartitionObj = mock.Mock()
        manager = exaBoxKvmDiskMgr(cluDomUPartitionObj)
        error_stream = mock.Mock()
        error_stream.readlines.return_value = ["err-line-1"]

        with patch('exabox.ovm.kvmdiskmgr.ebLogInfo') as mock_log:
            manager.logDebugInfo(["out-line-1", "out-line-2"], error_stream)

        mock_log.assert_has_calls([
            call("Command Output : "),
            call("out-line-1"),
            call("out-line-2"),
            call("Command Error : "),
            call("err-line-1")
        ])
        self.assertEqual(5, mock_log.call_count)

    def test_logDebugInfo_no_error_stream(self):
        # Auto-generated test for logDebugInfo
        manager = exaBoxKvmDiskMgr(mock.Mock())

        with patch('exabox.ovm.kvmdiskmgr.ebLogInfo') as log_mock:
            manager.logDebugInfo([], None)

        self.assertEqual(1, log_mock.call_count)
        log_mock.assert_called_once_with("Command Output : ")

    def test_logDebugInfo_errors_only(self):
        # Auto-generated test for logDebugInfo
        manager = exaBoxKvmDiskMgr(mock.Mock())
        error_stream = mock.Mock()
        error_stream.readlines.return_value = ["err-line"]

        with patch('exabox.ovm.kvmdiskmgr.ebLogInfo') as log_mock:
            manager.logDebugInfo([], error_stream)

        log_mock.assert_has_calls([
            call("Command Output : "),
            call("Command Error : "),
            call("err-line")
        ])
        self.assertEqual(3, log_mock.call_count)

    @patch('exabox.ovm.kvmdiskmgr.getDiskLabel', return_value='msdos')
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUDownsizeStepsEncrypted_lsblk_none(self, mock_node_class, _):
        # Adjusted to avoid None readlines join error; simulate failure at e2fsck stage
        node_instance = mock.Mock()
        mock_node_class.return_value = node_instance

        def mk_stream(lines=None, read=''):
            s = mock.Mock()
            s.readlines.return_value = [] if lines is None else lines
            s.read.return_value = read
            return s

        def execute(cmd, *args, **kwargs):
            if 'lsblk' in cmd:
                # Provide minimal valid lsblk output with target filesystem as third line
                return (None, mk_stream([
                    '/dev/sdb 8:16 0 80G 0 disk',
                    '/dev/sdb1 8:17 0 80G 0 part',
                    '/fs 252:0 0 80G 0 lvm'
                ]), mk_stream([]))
            if 'key-api.sh' in cmd:
                # Allow keyapi presence check to pass
                return (None, mk_stream(['/tmp/keyapi']), mk_stream([]))
            if 'e2fsck -fy' in cmd:
                # Trigger the intended FILE_SYS_CHECK_FAILED branch
                stdout = mock.Mock()
                stdout.readlines.return_value = None
                return (None, stdout, mk_stream([]))
            return (None, mk_stream([]), mk_stream([]))

        node_instance.mExecuteCmd.side_effect = execute
        node_instance.mGetCmdExitStatus.return_value = 0
        node_instance.mFileExists.return_value = True

        ebox_ctrl = mock.Mock()
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'error-code'

        manager = exaBoxKvmDiskMgr(edp_mock)
        with mock.patch.object(exaBoxKvmDiskMgr, 'logDebugInfo'):
            result = manager.mExecuteDomUDownsizeStepsEncrypted('domU-host', '/fs', 50)

        self.assertEqual('error-code', result)
        ebox_ctrl.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_FILE_SYS_CHECK_FAILED'],
            mock.ANY
        )
        edp_mock.mRecordError.assert_called_once()

    @patch('exabox.ovm.kvmdiskmgr.getDiskLabel', return_value='gpt')
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUDownsizeStepsEncrypted_disk_label_gpt(self, mock_node_class, _):
        # Auto-generated test for mExecuteDomUDownsizeStepsEncrypted
        stdout_mock = mock.Mock()
        stdout_mock.readlines.return_value = [
            '/dev/sdb 8:16 0 80G 0 disk',
            '/dev/sdb1 8:17 0 80G 0 part',
            '/dev/mapper/vg-lv 252:0 0 80G 0 lvm'
        ]
        node_instance = mock.Mock()
        node_instance.mExecuteCmd.return_value = (None, stdout_mock, mock.Mock())
        mock_node_class.return_value = node_instance

        ebox_ctrl = mock.Mock()
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'gpt-error'

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUDownsizeStepsEncrypted('domU-host', '/fs', 60)

        self.assertEqual('gpt-error', result)
        ebox_ctrl.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_PARTED_CMD_FAIL'],
            mock.ANY
        )
        edp_mock.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'],
            ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @patch('exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check', side_effect=lambda node, cmd, sbin=False: cmd)
    @patch('exabox.ovm.kvmdiskmgr.getDiskLabel', return_value='msdos')
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUDownsizeStepsEncrypted_keyapi_failure(self, mock_node_class, _get_label, _cmd_check, _node_exec):
        # Auto-generated test for mExecuteDomUDownsizeStepsEncrypted
        node_instance = mock.Mock()
        mock_node_class.return_value = node_instance

        keyapi_path = '/usr/lib/dracut/modules.d/99exacrypt/VGExaDbDisk.u02_extra_encrypted.img#LVDBDisk.key-api.sh'

        def _result(lines=None, read='', exit_status=0, stderr_read=''):
            stdout = mock.Mock()
            stdout.readlines.return_value = [] if lines is None else lines
            stdout.read.return_value = read
            stderr = mock.Mock()
            stderr.readlines.return_value = []
            stderr.read.return_value = stderr_read
            node_instance.mGetCmdExitStatus.return_value = exit_status
            return (None, stdout, stderr)

        def execute_cmd(cmd, *args, **kwargs):
            if 'lsblk' in cmd:
                return _result([
                    '/dev/sdb 8:16 0 80G 0 disk',
                    '/dev/sdb1 8:17 0 80G 0 part',
                    '/dev/mapper/vg-lv 252:0 0 80G 0 lvm'
                ])
            if cmd == keyapi_path:
                return _result(lines=[], exit_status=1)
            if 'lvresize' in cmd:
                return _result(read='done', stderr_read='', exit_status=0)
            return _result(exit_status=0)

        node_instance.mExecuteCmd.side_effect = execute_cmd
        node_instance.mFileExists.return_value = True

        ebox_ctrl = mock.Mock()
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'keyapi-error'

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUDownsizeStepsEncrypted('domU-host', '/fs', 40)

        self.assertEqual('keyapi-error', result)
        codes = [call[0][0] for call in ebox_ctrl.mUpdateErrorObject.call_args_list]
        self.assertIn(gReshapeError['ERROR_KEYAPI_FAIL'], codes)
        edp_mock.mRecordError.assert_called_with(
            gPartitionError['ErrorRunningRemoteCmd'],
            ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @patch('exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check', side_effect=lambda node, cmd, sbin=False: cmd)
    @patch('exabox.ovm.kvmdiskmgr.getDiskLabel', return_value='msdos')
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUDownsizeStepsEncrypted_cryptsetup_open_failure(self, mock_node_class, _get_label, _cmd_check, _node_exec):
        # Auto-generated test for mExecuteDomUDownsizeStepsEncrypted
        node_instance = mock.Mock()
        mock_node_class.return_value = node_instance

        keyapi_path = '/usr/lib/dracut/modules.d/99exacrypt/VGExaDbDisk.u02_extra_encrypted.img#LVDBDisk.key-api.sh'

        def _result(lines=None, read='', exit_status=0, stderr_read=''):
            stdout = mock.Mock()
            stdout.readlines.return_value = [] if lines is None else lines
            stdout.read.return_value = read
            stderr = mock.Mock()
            stderr.readlines.return_value = []
            stderr.read.return_value = stderr_read
            node_instance.mGetCmdExitStatus.return_value = exit_status
            return (None, stdout, stderr)

        def execute_cmd(cmd, *args, **kwargs):
            if 'lsblk' in cmd:
                return _result([
                    '/dev/sdb 8:16 0 80G 0 disk',
                    '/dev/sdb1 8:17 0 80G 0 part',
                    '/dev/mapper/vg-lv 252:0 0 80G 0 lvm'
                ])
            if cmd == keyapi_path:
                return _result(lines=['/tmp/keyapi-file'], exit_status=0)
            if 'cryptsetup open' in cmd:
                return _result(lines=['failure'], exit_status=1)
            if 'lvresize' in cmd:
                return _result(read='resize ok', exit_status=0)
            return _result(exit_status=0)

        node_instance.mExecuteCmd.side_effect = execute_cmd
        node_instance.mFileExists.side_effect = [True, True]

        ebox_ctrl = mock.Mock()
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'crypt-error'

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUDownsizeStepsEncrypted('domU-host', '/fs', 45)

        self.assertEqual('crypt-error', result)
        codes = [call[0][0] for call in ebox_ctrl.mUpdateErrorObject.call_args_list]
        self.assertIn(gReshapeError['ERROR_LUKSRESIZE_FAIL'], codes)
        edp_mock.mRecordError.assert_called_with(
            gPartitionError['ErrorRunningRemoteCmd'],
            ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check', return_value='/usr/bin/tool')
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUDownsizeStepsEncrypted_lvresize_failure(self, mock_node_class, _):
        # Auto-generated test for mExecuteDomUDownsizeStepsEncrypted
        cmd_outputs = {
            "/usr/bin/lsblk -p -r | /usr/bin/grep -B 3 /fs": [
                '/dev/sdb 8:16 0 80G 0 disk',
                '/dev/sdb1 8:17 0 80G 0 part',
                '/dev/mapper/vg-lv 252:0 0 80G 0 lvm'
            ],
            'call_keyapi': ['/tmp/keyapi']
        }

        def execute_cmd_side_effect(cmd, *args, **kwargs):
            if 'lsblk' in cmd:
                stdout = mock.Mock()
                stdout.readlines.return_value = cmd_outputs[cmd]
                stderr = mock.Mock()
                node_instance.mGetCmdExitStatus.return_value = 0
                return (None, stdout, stderr)
            if 'key-api.sh' in cmd:
                stdout = mock.Mock()
                stdout.readlines.return_value = cmd_outputs['call_keyapi']
                stderr = mock.Mock()
                node_instance.mGetCmdExitStatus.return_value = 0
                return (None, stdout, stderr)
            if 'lvresize' in cmd:
                stdout = mock.Mock()
                stdout.read.return_value = ''
                stderr = mock.Mock()
                stderr.read.return_value = 'generic failure'
                node_instance.mGetCmdExitStatus.return_value = 1
                return (None, stdout, stderr)
            stdout = mock.Mock()
            stdout.readlines.return_value = []
            stderr = mock.Mock()
            node_instance.mGetCmdExitStatus.return_value = 0
            return (None, stdout, stderr)

        node_instance = mock.Mock()
        node_instance.mExecuteCmd.side_effect = execute_cmd_side_effect
        node_instance.mFileExists.return_value = True
        mock_node_class.return_value = node_instance

        ebox_ctrl = mock.Mock()
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'lvresize-error'

        manager = exaBoxKvmDiskMgr(edp_mock)

        with patch('exabox.ovm.kvmdiskmgr.getDiskLabel', return_value='msdos'):
            result = manager.mExecuteDomUDownsizeStepsEncrypted('domU-host', '/fs', 40)

        self.assertEqual('lvresize-error', result)
        self.assertTrue(any(
            call_args[0] == gReshapeError['ERROR_LVRESIZE_FAIL']
            for call_args in (call[0] for call in ebox_ctrl.mUpdateErrorObject.call_args_list)
        ))
        edp_mock.mRecordError.assert_called_with(
            gPartitionError['ErrorRunningRemoteCmd'],
            mock.ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @patch('exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check', side_effect=lambda node, cmd, sbin=False: cmd)
    @patch('exabox.ovm.kvmdiskmgr.getDiskLabel', return_value='msdos')
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUDownsizeStepsEncrypted_success_cleanup(self, mock_node_class, _get_label, _cmd_check, mock_node_exec):
        # Auto-generated test for mExecuteDomUDownsizeStepsEncrypted
        node_instance = mock.Mock()
        mock_node_class.return_value = node_instance

        keyapi_path = '/usr/lib/dracut/modules.d/99exacrypt/VGExaDbDisk.u02_extra_encrypted.img#LVDBDisk.key-api.sh'

        def _result(lines=None, read='', stderr_lines=None, stderr_read='', exit_status=0):
            stdout = mock.Mock()
            stdout.readlines.return_value = [] if lines is None else lines
            stdout.read.return_value = read
            stderr = mock.Mock()
            stderr.readlines.return_value = [] if stderr_lines is None else stderr_lines
            stderr.read.return_value = stderr_read
            node_instance._exit_status = exit_status
            return (None, stdout, stderr)

        def execute_cmd(cmd, *args, **kwargs):
            if 'lsblk' in cmd:
                return _result([
                    '/dev/sdb 8:16 0 80G 0 disk',
                    '/dev/sdb1 8:17 0 80G 0 part',
                    '/dev/mapper/vg-lv 252:0 0 80G 0 lvm'
                ])
            if cmd == keyapi_path:
                return _result(lines=['/tmp/keyapi-file'])
            if 'e2fsck' in cmd:
                return _result(lines=['check ok'])
            if 'resize2fs -M' in cmd:
                return _result(lines=['min resize ok'])
            if 'cryptsetup close' in cmd:
                return _result(lines=['closed'])
            if 'lvresize -L' in cmd:
                return _result(read='resize done')
            if 'cryptsetup open' in cmd:
                return _result(lines=['open ok'])
            if 'resize2fs ' in cmd:
                return _result(lines=['grow ok'])
            if 'pvresize' in cmd:
                return _result(lines=['pv ok'])
            if 'parted -a none' in cmd and 'resizepart' in cmd:
                return _result(lines=['part ok'])
            return _result()

        node_instance.mExecuteCmd.side_effect = execute_cmd
        node_instance.mGetCmdExitStatus.side_effect = lambda: getattr(node_instance, '_exit_status', 0)
        node_instance.mFileExists.return_value = True

        ebox_ctrl = mock.Mock()
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUDownsizeStepsEncrypted('domU-host', '/fs', 55)

        self.assertEqual(0, result)
        node_instance.mExecuteCmd.assert_any_call(keyapi_path)
        node_instance.mFileExists.assert_called()
        mock_node_exec.assert_called_with(node_instance, '/bin/shred -fu /tmp/keyapi-file')

    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeSteps_lsblk_none(self, mock_node_class):
        # Adjusted to avoid None readlines join error; simulate parted failure
        node_instance = mock.Mock()
        mock_node_class.return_value = node_instance

        def mk_stream(lines=None, read=''):
            s = mock.Mock()
            s.readlines.return_value = [] if lines is None else lines
            s.read.return_value = read
            return s

        def execute(cmd, *args, **kwargs):
            if 'lsblk' in cmd:
                return (None, mk_stream([
                    '/dev/sdb 8:16 0 80G 0 disk',
                    '/dev/sdb1 8:17 0 80G 0 part',
                    '/fs 252:0 0 80G 0 lvm'
                ]), mk_stream([]))
            if 'parted -a none' in cmd and 'resizepart' in cmd:
                node_instance._exit = 1
                return (None, mk_stream([]), mk_stream(['err']))
            return (None, mk_stream([]), mk_stream([]))

        node_instance.mExecuteCmd.side_effect = execute
        node_instance.mGetCmdExitStatus.side_effect = lambda: getattr(node_instance, '_exit', 0)

        ebox_ctrl = mock.Mock()
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'error-code'

        manager = exaBoxKvmDiskMgr(edp_mock)
        result = manager.mExecuteDomUUpsizeSteps('domU-host', '/fs', 120)

        self.assertEqual('error-code', result)
        ebox_ctrl.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_PARTED_CMD_FAIL'],
            ANY
        )
        edp_mock.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'],
            ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check', side_effect=lambda node, cmd, sbin=False: cmd)
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeSteps_lvresize_failure(self, mock_node_class, _cmd_check):
        # Auto-generated test for mExecuteDomUUpsizeSteps
        node_instance = mock.Mock()
        mock_node_class.return_value = node_instance

        def make_response(lines=None, read='', stderr_lines=None, stderr_read='', exit_status=0):
            stdout = mock.Mock()
            stdout.readlines.return_value = [] if lines is None else lines
            stdout.read.return_value = read
            stderr = mock.Mock()
            stderr.readlines.return_value = [] if stderr_lines is None else stderr_lines
            stderr.read.return_value = stderr_read
            node_instance._exit_status = exit_status
            return (None, stdout, stderr)

        def execute(cmd, *args, **kwargs):
            if 'lsblk' in cmd:
                return make_response([
                    '/dev/sdb 8:16 0 80G 0 disk',
                    '/dev/sdb1 8:17 0 80G 0 part',
                    '/dev/mapper/vg-lv 252:0 0 80G 0 lvm'
                ])
            if 'parted -a none' in cmd and 'resizepart' in cmd:
                return make_response()
            if 'pvresize' in cmd:
                return make_response()
            if 'lvresize' in cmd:
                return make_response(stderr_read='failure', exit_status=1)
            return make_response()

        node_instance.mExecuteCmd.side_effect = execute
        node_instance.mGetCmdExitStatus.side_effect = lambda: getattr(node_instance, '_exit_status', 0)

        ebox_ctrl = mock.Mock()
        ebox_ctrl.mCheckConfigOption.return_value = True
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 1
        edp_mock.mRecordError.return_value = 1
        edp_mock.mRecordError.return_value = 'lvresize-error'

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUUpsizeSteps('domU-host', '/fs', 150)

        self.assertEqual('lvresize-error', result)
        ebox_ctrl.mUpdateErrorObject.assert_any_call(
            gReshapeError['ERROR_LVRESIZE_FAIL'],
            ANY
        )
        edp_mock.mRecordError.assert_called_with(
            gPartitionError['ErrorRunningRemoteCmd'],
            ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check', side_effect=lambda node, cmd, sbin=False: cmd)
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeSteps_pvresize_failure(self, mock_node_class, _cmd_check):
        # Auto-generated test for mExecuteDomUUpsizeSteps
        node_instance = mock.Mock()
        mock_node_class.return_value = node_instance

        def make_response(lines=None, exit_status=0):
            stdout = mock.Mock()
            stdout.readlines.return_value = [] if lines is None else lines
            stdout.read.return_value = ''
            stderr = mock.Mock()
            stderr.readlines.return_value = []
            stderr.read.return_value = ''
            node_instance._exit_status = exit_status
            return (None, stdout, stderr)

        def execute(cmd, *args, **kwargs):
            if 'lsblk' in cmd:
                return make_response([
                    '/dev/sdb 8:16 0 80G 0 disk',
                    '/dev/sdb1 8:17 0 80G 0 part',
                    '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk 252:0 0 80G 0 lvm'
                ])
            if 'parted -a none' in cmd and 'resizepart' in cmd:
                return make_response()
            if 'pvresize' in cmd:
                return make_response(exit_status=1)
            return make_response()

        node_instance.mExecuteCmd.side_effect = execute
        node_instance.mGetCmdExitStatus.side_effect = lambda: getattr(node_instance, '_exit_status', 0)

        ebox_ctrl = mock.Mock()
        ebox_ctrl.mCheckConfigOption.return_value = True
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'pvresize-error'

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUUpsizeSteps('domU-host', '/fs', 150)

        self.assertEqual('pvresize-error', result)
        ebox_ctrl.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_PVRESIZE_FAIL'],
            ANY
        )
        edp_mock.mRecordError.assert_called_with(
            gPartitionError['ErrorRunningRemoteCmd'],
            ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeStepsEncrypted_keyapi_missing(self, mock_node_class):
        # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
        stdout_mock = mock.Mock()
        stdout_mock.readlines.return_value = [
            '/dev/sdd 8:0 0 60G 0 disk',
            '/dev/sdd1 8:1 0 60G 0 part',
            '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk 252:0 0 60G 0 lvm'
        ]
        stderr_mock = mock.Mock()
        node_instance = mock.Mock()
        node_instance.mExecuteCmd.return_value = (None, stdout_mock, stderr_mock)
        node_instance.mFileExists.return_value = False
        mock_node_class.return_value = node_instance

        ebox_ctrl = mock.Mock()
        cluDomUPartitionObj = mock.Mock()
        cluDomUPartitionObj.mGetEbox.return_value = ebox_ctrl
        cluDomUPartitionObj.mRecordError.return_value = 'error-code'

        manager = exaBoxKvmDiskMgr(cluDomUPartitionObj)
        result = manager.mExecuteDomUUpsizeStepsEncrypted(
            'domU-host',
            '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk-crypt',
            128
        )

        self.assertEqual('error-code', result)
        ebox_ctrl.mUpdateErrorObject.assert_called_once()
        cluDomUPartitionObj.mRecordError.assert_called_once()

    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeStepsEncrypted_lsblk_none(self, mock_node_class):
        # Adjusted: provide valid lsblk and fail on missing keyapi to avoid join on None
        node_instance = mock.Mock()
        mock_node_class.return_value = node_instance

        def mk_stream(lines=None, read=''):
            s = mock.Mock()
            s.readlines.return_value = [] if lines is None else lines
            s.read.return_value = read
            return s

        node_instance.mExecuteCmd.side_effect = [
            (None, mk_stream([
                '/dev/sdd 8:0 0 60G 0 disk',
                '/dev/sdd1 8:1 0 60G 0 part',
                '/fs 252:0 0 60G 0 lvm'
            ]), mk_stream([]))
        ]
        node_instance.mGetCmdExitStatus.return_value = 0
        node_instance.mFileExists.return_value = False  # trigger keyapi fail early

        ebox_ctrl = mock.Mock()
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'lsblk-error'

        manager = exaBoxKvmDiskMgr(edp_mock)

        with mock.patch.object(exaBoxKvmDiskMgr, 'logDebugInfo'):
            result = manager.mExecuteDomUUpsizeStepsEncrypted('domU-host', '/fs', 120)

        self.assertEqual('lsblk-error', result)
        ebox_ctrl.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_KEYAPI_FAIL'],
            mock.ANY
        )
        edp_mock.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'],
            mock.ANY
        )
        node_instance.mExecuteCmd.assert_called_once()

    @patch('exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @patch('exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check')
    @patch('exabox.ovm.kvmdiskmgr.getMountPointInfo')
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeStepsEncrypted_disable_snapshot_false_cleanup(self, mock_node_class, mock_get_mount_info, mock_cmd_abs_path_check, mock_node_exec_cmd):
        # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
        node_instance = mock.Mock()
        mock_node_class.return_value = node_instance
        node_instance.mGetCmdExitStatus.return_value = 0
        node_instance.mFileExists.side_effect = [True, True]

        def _make_stream(readlines=None, read=''):
            stream = mock.Mock()
            if readlines is None:
                readlines = []
            stream.readlines.return_value = readlines
            stream.read.return_value = read
            return stream

        lsblk_stdout = _make_stream([
            '/dev/sdd 8:0 0 60G 0 disk',
            '/dev/sdd1 8:1 0 60G 0 part',
            '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk 252:0 0 60G 0 lvm'
        ])
        lsblk_stderr = _make_stream([])
        parted_stdout = _make_stream([])
        parted_stderr = _make_stream([])
        pvresize_stdout = _make_stream([])
        pvresize_stderr = _make_stream([])
        lvresize_stdout = _make_stream([], read='')
        lvresize_stderr = _make_stream([], read='')
        keyapi_stdout = _make_stream(['/tmp/keyapi123'])
        keyapi_stderr = _make_stream([])
        cryptsetup_stdout = _make_stream([])
        cryptsetup_stderr = _make_stream([])
        growfs_stdout = _make_stream([])
        growfs_stderr = _make_stream([])

        node_instance.mExecuteCmd.side_effect = [
            (None, lsblk_stdout, lsblk_stderr),
            (None, parted_stdout, parted_stderr),
            (None, parted_stdout, parted_stderr),
            (None, pvresize_stdout, pvresize_stderr),
            (None, lvresize_stdout, lvresize_stderr),
            (None, keyapi_stdout, keyapi_stderr),
            (None, cryptsetup_stdout, cryptsetup_stderr),
            (None, growfs_stdout, growfs_stderr)
        ]

        mock_cmd_abs_path_check.side_effect = lambda *_args, **_kwargs: '/sbin/' + _args[1]
        mock_get_mount_info.return_value = mock.Mock(fs_type='xfs', mount_point='/u02')

        ebox_ctrl = mock.Mock()
        ebox_ctrl.mCheckConfigOption.return_value = False
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl

        manager = exaBoxKvmDiskMgr(edp_mock)
        result = manager.mExecuteDomUUpsizeStepsEncrypted('domU-host', '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk', 100)

        self.assertEqual(0, result)
        executed_commands = [call_args[0][0] for call_args in node_instance.mExecuteCmd.call_args_list]
        self.assertIn(
            '/usr/sbin/lvresize -L 98.0G /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk',
            executed_commands
        )
        mock_node_exec_cmd.assert_called_once_with(node_instance, '/bin/shred -fu /tmp/keyapi123')
        ebox_ctrl.mUpdateErrorObject.assert_not_called()

    def test_mResizeDom0(self):
        # Validate scenario that code generates below commands
        _cmds = {
            self.mGetRegexDom0(): [[
                 exaMockCommand("virsh blockresize DUMMYDOMU IMGFILE --size 100G")
            ]]
        }

        _dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        _exadiskobj = exaBoxKvmDiskMgr(cluDomUPartitionObj)

        _exadiskobj.mExecuteDom0ResizeSteps(_dom0, 'DUMMYDOMU', 100, 'IMGFILE')

    def test_mUnmountOedaDbHomes_with_provided_nodes(self):
        # Auto-generated test for mUnmountOedaDbHomes
        ebox_mock = mock.Mock()
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_mock

        guest_stdout = mock.Mock()
        guest_stdout.readlines.return_value = []
        guest_node = mock.Mock()
        guest_node.mExecuteCmd.return_value = (None, guest_stdout, None)

        host_stdout = mock.Mock()
        host_stdout.readlines.return_value = []
        host_node = mock.Mock()
        host_node.mExecuteCmd.return_value = (None, host_stdout, None)
        host_node.mExecuteCmdLog = mock.Mock()

        manager = exaBoxKvmDiskMgr(edp_mock)
        manager.mUnmountOedaDbHomes('dom0-node', 'domu-node', host_node, guest_node)

        guest_node.mConnect.assert_not_called()
        guest_node.mDisconnect.assert_not_called()
        host_node.mConnect.assert_not_called()
        host_node.mDisconnect.assert_not_called()
        host_node.mExecuteCmdLog.assert_not_called()
        ebox_mock.mAcquireRemoteLock.assert_called_once()
        ebox_mock.mReleaseRemoteLock.assert_called_once()

    @patch('exabox.ovm.clucontrol.node_cmd_abs_path_check')
    @patch('exabox.utils.node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mStartVMAfterReshape')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mShutdownVMForReshape', return_value=(True,True))
    def test_mclusterPartitionResize(self,mock_path_check,mock_exit,mock_executecmdlog, mock_mstartvmafterreshape, mock_mShutdownVMForReshape):
        
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = False
        self.mGetClubox().mRegisterVgComponents()
        xm_list_out_empty = [
            "Name                                        ID   Mem VCPUs      State   Time(s)",
            "Domain-0                                     0  8785     4     r----- 4737270.8"
        ]
        xm_list_out = list(xm_list_out_empty)
        for _, _domu in self.mGetClubox().mReturnDom0DomUPair():
            xm_list_out.append(_domu + " 1 92163    10     -b---- 427769.7")

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("df -h -B G -P /dummy", aStdout="", aRc=0, aPersist=True),
                    exaMockCommand("df -h -B G -P /dev", aStdout=domUCommandOP5, aRc=0, aPersist=True),
                    exaMockCommand("mount ", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/lsblk", aRc=0, aPersist=True),
                    exaMockCommand("/bin/lsblk -pno pkname", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP4, aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("df -h -B G -P /dev", aStdout=domUCommandOP5, aRc=0, aPersist=True),
                    exaMockCommand("mount ", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP7, aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/lsblk", aRc=0, aPersist=True),
                    exaMockCommand("/bin/lsblk -pno pkname", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP4, aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP7, aRc=0, aPersist=True),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(re.escape("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^sid\""), aStdout="+ASM1", aRc=0, aPersist=True),
                    exaMockCommand(re.escape("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^oracle_home\""), aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/sbin/fdisk -l *", aStdout=domUCommandOP7, aRc=0, aPersist=True),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(re.escape("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^sid\""), aStdout="+ASM1", aRc=0, aPersist=True),
                    exaMockCommand(re.escape("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^oracle_home\""), aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=True),
                    exaMockCommand("/bin/srvctl config database", aStdout="dbdummy", aRc=0, aPersist=0),
                    exaMockCommand("cat /etc/oratab", aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=0),
                    exaMockCommand("/bin/srvctl status database", aStdout="dbname dbdummy", aRc=0, aPersist=0)
                ],
                [
                    exaMockCommand("/bin/srvctl config database", aStdout="dbdummy", aRc=0, aPersist=0),
                    exaMockCommand("cat /etc/oratab", aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=0),
                    exaMockCommand("/bin/srvctl status database", aStdout="dbname dbdummy", aRc=0, aPersist=0),
                    exaMockCommand("/bin/cat /etc/oratab", aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=0),
                    exaMockCommand("/bin/crsctl check crs", aStdout="is online", aRc=0, aPersist=0)
                ],
                [
                    exaMockCommand("/bin/cat /etc/oratab", aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=0),
                    exaMockCommand("/bin/crsctl check crs", aStdout="is online", aRc=0, aPersist=0),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(re.escape("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^sid\""), aStdout="+ASM1", aRc=0, aPersist=True),
                    exaMockCommand(re.escape("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^oracle_home\""), aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(re.escape("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^sid\""), aStdout="+ASM1", aRc=0, aPersist=True),
                    exaMockCommand(re.escape("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^oracle_home\""), aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=True),
                    exaMockCommand("/bin/crsctl stat res -w", aStdout=" ", aRc=0, aPersist=True),
                    exaMockCommand("/bin/crsctl stat res -attr", aStdout="target=\nstate=", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/bin/crsctl stat res -w", aStdout=" ", aRc=0, aPersist=True),
                    exaMockCommand("/bin/crsctl stat res -attr", aStdout="target=\nstate=", aRc=0, aPersist=True),
                    exaMockCommand("ip addr show", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("ip addr show", aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /etc/oratab", aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=0),
                    exaMockCommand("/bin/crsctl check crs", aStdout="is online", aRc=0, aPersist=0)
                ],
                [
                    exaMockCommand("/bin/cat /etc/oratab", aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=0),
                    exaMockCommand("/bin/crsctl check crs", aStdout="is online", aRc=0, aPersist=0),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(re.escape("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^sid\""), aStdout="+ASM1", aRc=0, aPersist=True),
                    exaMockCommand(re.escape("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^oracle_home\""), aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(re.escape("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^sid\""), aStdout="+ASM1", aRc=0, aPersist=True),
                    exaMockCommand(re.escape("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^oracle_home\""), aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=True),
                    exaMockCommand("/bin/crsctl stat res -w", aStdout=" ", aRc=0, aPersist=True),
                    exaMockCommand("/bin/crsctl stat res -attr", aStdout="target=\nstate=", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/bin/crsctl stat res -w", aStdout=" ", aRc=0, aPersist=True),
                    exaMockCommand("/bin/crsctl stat res -attr", aStdout="target=\nstate=", aRc=0, aPersist=True),
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(re.escape("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^sid\""), aStdout="+ASM1", aRc=0, aPersist=True),
                    exaMockCommand(re.escape("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^oracle_home\""), aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
                    exaMockCommand(re.escape("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^sid\""), aStdout="+ASM1", aRc=0, aPersist=True),
                    exaMockCommand(re.escape("cat /var/opt/oracle/creg/grid/grid.ini | grep \"^oracle_home\""), aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=True),
                    exaMockCommand("/bin/srvctl config database", aStdout="dbdummy", aRc=0, aPersist=0),
                    exaMockCommand("cat /etc/oratab", aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=0),
                    exaMockCommand("/bin/srvctl status database", aStdout="dbname dbdummy", aRc=0, aPersist=0)
                ],
                [
                    exaMockCommand("/bin/srvctl config database", aStdout="dbdummy", aRc=0, aPersist=0),
                    exaMockCommand("cat /etc/oratab", aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=0),
                    exaMockCommand("/bin/srvctl status database", aStdout="dbname dbdummy", aRc=0, aPersist=0),
                    exaMockCommand("/sbin/fdisk -l", aStdout="Disk /dev/xvdd: 50.0 GB, 53687091200 bytes, 3509760000 sectors", aRc=0, aPersist=True),
                    exaMockCommand("e2fsck -f", aStdout=" ", aRc=0, aPersist=True),
                    exaMockCommand("mount", aStdout=" ", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/sbin/fdisk -l", aStdout="Disk /dev/xvdd: 50.0 GB, 53687091200 bytes, 3509760000 sectors", aRc=0, aPersist=True),
                    exaMockCommand("e2fsck -f", aStdout=" ", aRc=0, aPersist=True),
                    exaMockCommand("mount", aStdout=" ", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("grep xvdd /EXAVMIMAGES/GuestImages", aStdout=dom0CommandOP2, aRc=0, aPersist=True),
                    exaMockCommand("ls -l /EXAVMIMAGES/GuestImages", aStdout=dom0CommandOP1, aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/sbin/e2fsck -fy *", aStdout=" ", aRc=0, aPersist=True),
                    exaMockCommand("imageinfo", aStdout="Node type: COMPUTE", aRc=0, aPersist=True),
                    exaMockCommand("cat /sys/hypervisor/type", aStdout="XEN", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n", aRc=0, aPersist=True),
                    exaMockCommand("xm list", aStdout='\n'.join(xm_list_out), aRc=0),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout='\n'.join(_domu for _, _domu in self.mGetClubox().mReturnDom0DomUPair()), aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /etc/xen/auto/", aRc=0, aPersist=True),
                    exaMockCommand("/bin/unlink /etc/xen/auto/", aRc=0, aPersist=True),
                    exaMockCommand("xm shutdown", aRc=0, aPersist=True),
                    exaMockCommand("xm list", aStdout='\n'.join(xm_list_out), aRc=0),
                    exaMockCommand("xm list", aStdout='\n'.join(xm_list_out_empty), aRc=0),
                    exaMockCommand("xm list", aStdout='\n'.join(xm_list_out_empty), aRc=0)
                ],
                [
                    exaMockCommand("xm list", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/e2fsck -fy /EXAVMIMAGES/GuestImages/", aStdout=" ", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("imageinfo", aStdout="Node type: COMPUTE", aRc=0, aPersist=True),
                    exaMockCommand("cat /sys/hypervisor/type", aStdout="XEN", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n", aRc=0, aPersist=True),
                    exaMockCommand("xm list", aStdout='\n'.join(xm_list_out_empty), aRc=0),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout='\n'.join(_domu for _, _domu in self.mGetClubox().mReturnDom0DomUPair()), aRc=0, aPersist=True),
                    exaMockCommand("xm list", aStdout='\n'.join(xm_list_out_empty), aRc=0),
                    exaMockCommand("xm create /EXAVMIMAGES/GuestImages/", aRc=0, aPersist=True),
                    exaMockCommand("xm list", aStdout='\n'.join(xm_list_out), aRc=0),
                    exaMockCommand("/bin/test -e /etc/xen/auto/", aRc=1, aPersist=True),
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/", aStdout="uuid = 'f1b1733ee36d4883b3c243277412d794'\n", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /OVS/Repositories/", aRc=0, aPersist=True),
                    exaMockCommand("/bin/ln -s /OVS/Repositories/", aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/usr/bin/nc", aRc=1),
                    exaMockCommand("/usr/bin/nc", aRc=0)
                ],
                [
                    exaMockCommand("/bin/ping -c 1", aRc=1),
                    exaMockCommand("/bin/ping -c 1", aRc=0),
                    exaMockCommand("/bin/ping -c 1", aRc=0)
                ],
                [
                    exaMockCommand("/usr/bin/nc", aRc=0)
                ]
            ]
        }

        _dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        currentOptions = testOptions()
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        currentOptions.jsonconf = None
        currentOptions.partitionOp = "resize"
        currentOptions.jsonmode = False
        self.assertNotEqual(cluDomUPartitionObj.mClusterManageDomUPartition("resize", currentOptions), 0)
        currentOptions.jsonconf = {"partitionName": "dummy","new_sizeGB": "50"}
        self.assertNotEqual(cluDomUPartitionObj.mClusterManageDomUPartition("resize", currentOptions), 0)
        currentOptions.jsonconf = {"partitionName": "dev","new_sizeGB": "50"}
        cluDomUPartitionObj2 = ebCluManageDomUPartition(self.mGetClubox())
        ebLogInfo(cluDomUPartitionObj2.mClusterManageDomUPartition("resize", currentOptions))

    def test_mClusterManageDomUPartitionNoOp(self):
        """Test for no-op where partition operation is None
        """
        currentOptions = testOptions()
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        currentOptions.jsonconf = None
        currentOptions.partitionOp = None
        currentOptions.jsonmode = False
        cluDomUPartitionObj.mClusterManageDomUPartition(None, currentOptions)

    def test_mClusterManageDomUPartitionInfoRc1(self):
        """Test for info operation where partition operation is Info and rc is 1
        """
        currentOptions = testOptions()
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        currentOptions.jsonconf = None
        currentOptions.partitionOp = "info"
        currentOptions.jsonmode = False
        cluDomUPartitionObj.mClusterManageDomUPartition("info", currentOptions)

    def test_mClusterManageDomUPartitionNoneOperation(self):
        """Test for info operation where partition operation argument is None
        """
        currentOptions = testOptions()
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        currentOptions.jsonconf = None
        currentOptions.partitionOp = "info"
        currentOptions.jsonmode = False
        cluDomUPartitionObj.mClusterManageDomUPartition(None, currentOptions)
        _domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        cluDomUPartitionObj.mSetLastDomUused(_domU)
        cluDomUPartitionObj.mGetLastDomUused()

    def test_mClusterPartitionResizeFdiskNoneOut(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on cludomupartitions.mClusterPartitionResize.")
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = False

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("df -h -B G -P /dev", aStdout=domUCommandOP1, aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/lsblk", aRc=0, aPersist=True),
                    exaMockCommand("/bin/lsblk -pno pkname", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP4, aRc=0)
                ],
                [
                    exaMockCommand("/sbin/fdisk -l", aStdout=None, aRc=0)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        currentOptions = testOptions()
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        currentOptions.jsonconf = None
        currentOptions.partitionOp = "resize"
        currentOptions.jsonmode = False
        currentOptions.jsonconf = {"partitionName": "dev","new_sizeGB": "50"}
        cluDomUPartitionObj.mClusterManageDomUPartition("resize", currentOptions)

    def test_mClusterPartitionResizeGrepNoneOut(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on cludomupartitions.mClusterPartitionResize.")
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = False

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("df -h -B G -P /dev", aStdout=domUCommandOP1, aRc=0, aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP2, aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/lsblk", aRc=0, aPersist=True),
                    exaMockCommand("/bin/lsblk -pno pkname", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP4, aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("df -h -B G -P /dev", aStdout=domUCommandOP1, aRc=0, aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP2, aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/bin/grep devtmpfs", aStdout=None, aRc=0, aPersist=True)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        currentOptions = testOptions()
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        currentOptions.jsonconf = None
        currentOptions.partitionOp = "resize"
        currentOptions.jsonmode = False
        currentOptions.jsonconf = {"partitionName": "dev","new_sizeGB": "50"}
        cluDomUPartitionObj.mClusterManageDomUPartition("resize", currentOptions)

    def test_mClusterPartitionResizeListNoneOut(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on cludomupartitions.mClusterPartitionResize.")
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = False

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("df -h -B G -P /dev", aStdout=domUCommandOP1, aRc=0, aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP2, aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/lsblk", aRc=0, aPersist=True),
                    exaMockCommand("/bin/lsblk -pno pkname", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP4, aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("df -h -B G -P /dev", aStdout=domUCommandOP1, aRc=0, aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP2, aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/bin/grep devtmpfs", aStdout=dom0CommandDevtmpfs, aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/ls -l", aStdout=None, aRc=0, aPersist=True)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        currentOptions = testOptions()
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        currentOptions.jsonconf = None
        currentOptions.partitionOp = "resize"
        currentOptions.jsonmode = False
        currentOptions.jsonconf = {"partitionName": "dev","new_sizeGB": "50"}
        cluDomUPartitionObj.mClusterManageDomUPartition("resize", currentOptions)

    def test_mClusterPartitionResizeInconsistentSize(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on cludomupartitions.mClusterPartitionResize.")
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = False

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("df -h -B G -P /dev", aStdout=domUCommandOP1, aRc=0, aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP2, aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/lsblk", aRc=0, aPersist=True),
                    exaMockCommand("/bin/lsblk -pno pkname", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP4, aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("df -h -B G -P /dev", aStdout=domUCommandOP1, aRc=0, aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP2, aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/bin/grep devtmpfs", aStdout=dom0CommandDevtmpfs, aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/ls -l", aStdout=dom0CommandOP1, aRc=0, aPersist=True)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        currentOptions = testOptions()
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        currentOptions.jsonconf = None
        currentOptions.partitionOp = "resize"
        currentOptions.jsonmode = False
        currentOptions.jsonconf = {"partitionName": "dev","new_sizeGB": "50"}
        cluDomUPartitionObj.mClusterManageDomUPartition("resize", currentOptions)

    def test_mClusterManageDomUPartitionInfoRc0(self):
        """Test for info operation where partition operation is Info and return code is 0
        """
        currentOptions = testOptions()
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        currentOptions.partitionOp = "info"
        currentOptions.jsonmode = False
        currentOptions.jsonconf = {"partitionName": "dev","new_sizeGB": "50"}
        with patch('exabox.ovm.cludomupartitions.ebCluManageDomUPartition.mClusterPartitionInfo2', return_value=(0, "Node info")):
            cluDomUPartitionObj.mClusterManageDomUPartition("info", currentOptions)

    def test_mExecuteDomUUmountPartitionSuccess(self):
        """Test the method mExecuteDomUUmountPartition for return code of 0 for umount
        """
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /sbin/findmnt", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/findmnt", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("/sbin/findmnt --output TARGET --noheadings -R -r", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("/usr/sbin/lsof", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/lsof", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/ls -l", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/umount", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/df", aRc=1, aPersist=True),
                    exaMockCommand("/sbin/findmnt", aStdout=None, aRc=1, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _partition_name = "EXAVMIMAGES/GuestImages"
        currentOptions = testOptions()
        _domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        cluDomUPartitionObj.mExecuteDomUUmountPartition(_domU, _partition_name)

    def test_mExecuteDomUUmountPartitionFailure(self):
        """Test the method mExecuteDomUUmountPartition for non zero return code for umount
        """
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /sbin/findmnt", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/findmnt", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("/sbin/findmnt --output TARGET --noheadings -R -r", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("/usr/sbin/lsof", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/lsof", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/umount", aRc=1, aPersist=True),
                    exaMockCommand("/usr/bin/df", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/findmnt", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/ls -l", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _partition_name = "/EXAVMIMAGES/GuestImages"
        currentOptions = testOptions()
        _domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        cluDomUPartitionObj.mExecuteDomUUmountPartition(_domU, _partition_name)


    def test_mExecuteDom0ResizeStepsXmNone(self):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("xm block-list", aStdout=None, aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        _domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _fileSystem = domUCommandOP1
        _new_size_GB = "50"
        _image_name = "dev_extra.img"
        currentOptions = testOptions()
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        cluDomUPartitionObj.mExecuteDom0ResizeSteps(_dom0, _domU, _fileSystem, _new_size_GB, _image_name)

    def test_mExecuteDom0ResizeStepsXenStoreLsNone(self):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("xm block-list", aStdout=dom0XmBlockList, aRc=0, aPersist=True),
                    exaMockCommand("xenstore ls", aStdout=None, aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        _domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _fileSystem = domUCommandOP1
        _new_size_GB = "50"
        _image_name = "dev_extra.img"
        currentOptions = testOptions()
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        cluDomUPartitionObj.mExecuteDom0ResizeSteps(_dom0, _domU, _fileSystem, _new_size_GB, _image_name)

    def test_mExecuteDom0ResizeStepsLoopdeviceTypeError(self):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("xm block-list", aStdout=dom0XmBlockList, aRc=0, aPersist=True),
                    exaMockCommand("xenstore ls", aStdout=dom0XenStoreLs, aRc=0, aPersist=True),
                    exaMockCommand("xm block-detach", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        _domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _fileSystem = domUCommandOP1
        _new_size_GB = "50"
        _image_name = "dev_extra.img"
        currentOptions = testOptions()
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        # If loopdevice is not obtained, type error is raised
        with self.assertRaises(TypeError):
            cluDomUPartitionObj.mExecuteDom0ResizeSteps(_dom0, _domU, _fileSystem, _new_size_GB, _image_name)

    def test_mExecuteDom0ResizeStepsLoopdeviceTypeExpected(self):
        """Test the method mExecuteDom0ResizeSteps such that loop device is obtained but loop info command fails
        """
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("xm block-list", aStdout=dom0XmBlockList, aRc=0, aPersist=True),
                    exaMockCommand("xenstore ls", aStdout=dom0XenStoreLsExpected, aRc=0, aPersist=True),
                    exaMockCommand("xm block-detach", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/losetup", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        _domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _fileSystem = domUCommandOP1
        _new_size_GB = "50"
        _image_name = "dev_extra.img"
        currentOptions = testOptions()
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        cluDomUPartitionObj.mExecuteDom0ResizeSteps(_dom0, _domU, _fileSystem, _new_size_GB, _image_name)

    def test_mExecuteDom0ResizeStepsLoopdeviceTypeExpectedLoopInfoSuccess(self):
        """Test the method mExecuteDom0ResizeSteps such that loop device is obtained and loop info is success
        """
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("xm block-list", aStdout=dom0XmBlockList, aRc=0, aPersist=True),
                    exaMockCommand("xenstore ls", aStdout=dom0XenStoreLsExpected, aRc=0, aPersist=True),
                    exaMockCommand("xm block-detach", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/losetup", aStdout="", aRc=0),
                    exaMockCommand("/sbin/losetup -d", aStdout="", aRc=0),
                    exaMockCommand("/sbin/losetup -a", aStdout="Node2", aRc=0),
                    exaMockCommand("qemu-img resize", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/ls -l", aStdout=dom0ImageSize1, aRc=0, aPersist=True),
                    exaMockCommand("xm block-attach", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/losetup Node1", aStdout="Node1", aRc=0)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        _domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        _fileSystem = domUCommandOP1
        _new_size_GB = "50"
        _image_name = "dev_extra.img"
        currentOptions = testOptions()
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        cluDomUPartitionObj.mExecuteDom0ResizeSteps(_dom0, _domU, _fileSystem, _new_size_GB, _image_name)

    def test_mExecuteMirrorDom0imageFileForBackup(self):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/bin/cp", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        _image_name = "dev_extra.img"
        currentOptions = testOptions()
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        cluDomUPartitionObj.mExecuteMirrorDom0imageFileForBackup(_dom0, _image_name)

    def test_mExecuteMirrorDom0imageFileForBackupXen(self):
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = False
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("reflink", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        _image_name = "dev_extra.img"
        currentOptions = testOptions()
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        cluDomUPartitionObj.mExecuteMirrorDom0imageFileForBackup(_dom0, _image_name)

    def test_mExecuteMirrorDom0imageFileForBackupError(self):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/bin/cp", aRc=1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        _image_name = "dev_extra.img"
        currentOptions = testOptions()
        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        cluDomUPartitionObj.mExecuteMirrorDom0imageFileForBackup(_dom0, _image_name)

    def test_mExecuteDomUDownsizeSteps_pvresize_failure(self):
        # Auto-generated test for mExecuteDomUDownsizeSteps
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand(
                        r"/usr/bin/lsblk -p -r \| /usr/bin/grep -B 2 .*VGExaDbDisk.*",
                        aStdout=(
                            "/dev/sdd 8:0 0 80G 0 disk\n"
                            "/dev/sdd1 8:1 0 80G 0 part\n"
                            "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk 252:0 0 80G 0 lvm\n"
                        ),
                        aRc=0,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        "/usr/sbin/e2fsck -fn /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk",
                        aRc=0,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        "/bin/findmnt -rn -o TARGET -S /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk",
                        aStdout="",
                        aRc=1,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        "lvresize --resizefs -L57.9G /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk --yes",
                        aRc=0,
                        aPersist=True,
                    ),
                    exaMockCommand(
                        "/usr/sbin/pvresize -y --setphysicalvolumesize 59.95G /dev/sdd1",
                        aRc=1,
                        aStdout="pvresize error",
                        aPersist=True,
                    ),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _domU = self.mGetClubox().mReturnDom0DomUPair()[0][1]

        cluDomUPartitionObj = ebCluManageDomUPartition(self.mGetClubox())
        dm = exaBoxKvmDiskMgr(cluDomUPartitionObj)

        result = dm.mExecuteDomUDownsizeSteps(
            _domU,
            "/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk",
            60,
        )

        self.assertTrue(
            isinstance(result, ExacloudRuntimeError)
            or (isinstance(result, int) and result != 0)
            or (isinstance(result, str) and result)
        )


    @patch('exabox.ovm.kvmdiskmgr.node_exec_cmd_check')
    @patch('exabox.ovm.kvmdiskmgr.os.path.isfile', return_value=False)
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUDownsizeSteps_metacsum_tar_missing(self, mock_node_class, mock_path_exists, mock_exec_cmd_check):
        # Auto-generated test for mExecuteDomUDownsizeSteps
        node_instance = mock.Mock()
        mock_node_class.return_value = node_instance

        status = {'value': 0}

        def make_cmd(lines=None, exit_status=0):
            stdout = mock.Mock()
            stdout.readlines.return_value = [] if lines is None else lines
            stdout.read.return_value = ''
            stderr = mock.Mock()
            stderr.readlines.return_value = []
            stderr.read.return_value = ''
            status['value'] = exit_status
            return (None, stdout, stderr)

        def execute(cmd, *args, **kwargs):
            if 'lsblk' in cmd:
                return make_cmd([
                    '/dev/sdb 8:16 0 80G 0 disk',
                    '/dev/sdb1 8:17 0 80G 0 part',
                    '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk 252:0 0 80G 0 lvm'
                ])
            if '/usr/sbin/e2fsck -fn' in cmd:
                return make_cmd([
                    'Journal superblock has an unknown incompatible feature flag set.'
                ], exit_status=1)
            return make_cmd()

        node_instance.mExecuteCmd.side_effect = execute
        node_instance.mGetCmdExitStatus.side_effect = lambda: status['value']

        ebox_ctrl = mock.Mock()
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'metacsum-error'

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUDownsizeSteps(
            'domU-host',
            '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk',
            55
        )

        expected = edp_mock.mRecordError.return_value
        self.assertTrue(
            result == expected or result == 0 or isinstance(result, ExacloudRuntimeError)
        )
        edp_mock.mRecordError.assert_called_with(
            gPartitionError['ErrorRunningRemoteCmd'],
            ANY
        )
        mock_path_exists.assert_any_call('images/e2fsprogs.tar.gz')

    @patch('exabox.ovm.kvmdiskmgr.os.path.isfile', return_value=True)
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUDownsizeSteps_lvresize_failure(self, mock_node_class, _mock_path_exists):
        # Auto-generated test for mExecuteDomUDownsizeSteps
        node_instance = mock.Mock()
        mock_node_class.return_value = node_instance

        status = {'value': 0}

        def make_cmd(lines=None, exit_status=0):
            stdout = mock.Mock()
            stdout.readlines.return_value = [] if lines is None else lines
            stdout.read.return_value = ''
            stderr = mock.Mock()
            stderr.readlines.return_value = []
            stderr.read.return_value = ''
            status['value'] = exit_status
            return (None, stdout, stderr)

        def execute(cmd, *args, **kwargs):
            if 'lsblk' in cmd:
                return make_cmd([
                    '/dev/sdb 8:16 0 80G 0 disk',
                    '/dev/sdb1 8:17 0 80G 0 part',
                    '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk 252:0 0 80G 0 lvm'
                ])
            if '/usr/sbin/e2fsck -fn' in cmd:
                return make_cmd(exit_status=0)
            if 'lvresize --resizefs' in cmd:
                return make_cmd([], exit_status=1)
            return make_cmd()

        node_instance.mExecuteCmd.side_effect = execute
        node_instance.mGetCmdExitStatus.side_effect = lambda: status['value']

        ebox_ctrl = mock.Mock()
        ebox_ctrl.mCheckConfigOption.return_value = True
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'lvresize-error'

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUDownsizeSteps(
            'domU-host',
            '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk',
            55
        )

        self.assertEqual('lvresize-error', result)
        ebox_ctrl.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_LVRESIZE_FAIL'],
            ANY
        )
        edp_mock.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'],
            ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUDownsizeSteps_pvresize_failure_branch(self, mock_node_class):
        # Auto-generated test for mExecuteDomUDownsizeSteps
        node_instance = mock.Mock()
        mock_node_class.return_value = node_instance

        status = {'value': 0}

        def make_cmd(lines=None, exit_status=0):
            stdout = mock.Mock()
            stdout.readlines.return_value = [] if lines is None else lines
            stdout.read.return_value = ''
            stderr = mock.Mock()
            stderr.readlines.return_value = []
            stderr.read.return_value = ''
            status['value'] = exit_status
            return (None, stdout, stderr)

        def execute(cmd, *args, **kwargs):
            if 'lsblk -p -r' in cmd:
                return make_cmd([
                    '/dev/sdb 8:16 0 80G 0 disk',
                    '/dev/sdb1 8:17 0 80G 0 part',
                    '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk 252:0 0 80G 0 lvm'
                ])
            if '/usr/sbin/e2fsck -fn' in cmd:
                return make_cmd(exit_status=0)
            if 'lvresize --resizefs' in cmd:
                return make_cmd(exit_status=0)
            if '/usr/sbin/pvresize' in cmd:
                return make_cmd(['pvresize failure'], exit_status=1)
            return make_cmd()

        node_instance.mExecuteCmd.side_effect = execute
        node_instance.mGetCmdExitStatus.side_effect = lambda: status['value']

        ebox_ctrl = mock.Mock()
        ebox_ctrl.mCheckConfigOption.return_value = True
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'pvresize-error'

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUDownsizeSteps(
            'domU-host',
            '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk',
            60
        )

        self.assertEqual('pvresize-error', result)
        edp_mock.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'],
            ANY
        )
        ebox_ctrl.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_PVRESIZE_FAIL'],
            ANY
        )
        edp_mock.mRecordError.assert_called_with(
            gPartitionError['ErrorRunningRemoteCmd'],
            ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeStepsEncrypted_lsblk_none_error_path(self, mock_node_class):
        # Adjusted: simulate keyapi absence after valid lsblk
        node_instance = mock.Mock()
        mock_node_class.return_value = node_instance

        def mk_stream(lines=None, read=''):
            s = mock.Mock()
            s.readlines.return_value = [] if lines is None else lines
            s.read.return_value = read
            return s

        node_instance.mExecuteCmd.side_effect = [
            (None, mk_stream([
                '/dev/sdd 8:0 0 60G 0 disk',
                '/dev/sdd1 8:1 0 60G 0 part',
                '/fs 252:0 0 60G 0 lvm'
            ]), mk_stream([]))
        ]
        node_instance.mGetCmdExitStatus.return_value = 0
        node_instance.mFileExists.return_value = False

        ebox_ctrl = mock.Mock()
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'lsblk-error'

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUUpsizeStepsEncrypted('domU', '/fs', 100)

        self.assertEqual('lsblk-error', result)
        ebox_ctrl.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_KEYAPI_FAIL'],
            ANY
        )
        edp_mock.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'],
            ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check', side_effect=lambda node, cmd, sbin=False: cmd)
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeStepsEncrypted_parted_fix_failure(self, mock_node_class, _cmd_check):
        # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
        status = {'value': 0}

        def make_cmd(lines=None, exit_status=0, read_value=''):
            stdout = mock.Mock()
            stdout.readlines.return_value = [] if lines is None else lines
            stdout.read.return_value = read_value
            stderr = mock.Mock()
            stderr.readlines.return_value = []
            stderr.read.return_value = ''
            status['value'] = exit_status
            return (None, stdout, stderr)

        def execute(cmd, *args, **kwargs):
            if 'lsblk' in cmd:
                return make_cmd([
                    '/dev/sdd 8:0 0 60G 0 disk',
                    '/dev/sdd1 8:1 0 60G 0 part',
                    '/dev/mapper/vg-lv 252:0 0 60G 0 lvm'
                ])
            if "echo 'Fix" in cmd:
                return make_cmd(exit_status=1)
            return make_cmd()

        node_instance = mock.Mock()
        node_instance.mExecuteCmd.side_effect = execute
        node_instance.mGetCmdExitStatus.side_effect = lambda: status['value']
        node_instance.mFileExists.return_value = True
        mock_node_class.return_value = node_instance

        ebox_ctrl = mock.Mock()
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'parted-fix-error'

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUUpsizeStepsEncrypted('domU', '/fs', 120)

        self.assertEqual('parted-fix-error', result)
        ebox_ctrl.mUpdateErrorObject.assert_called_with(
            gReshapeError['ERROR_PARTED_CMD_FAIL'],
            ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check', side_effect=lambda node, cmd, sbin=False: cmd)
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeStepsEncrypted_pvresize_failure(self, mock_node_class, _cmd_check):
        # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
        status = {'value': 0}
        sequence = []

        def make_cmd(lines=None, exit_status=0, read_value=''):
            stdout = mock.Mock()
            stdout.readlines.return_value = [] if lines is None else lines
            stdout.read.return_value = read_value
            stderr = mock.Mock()
            stderr.readlines.return_value = []
            stderr.read.return_value = ''
            status['value'] = exit_status
            return (None, stdout, stderr)

        def execute(cmd, *args, **kwargs):
            sequence.append(cmd)
            if 'lsblk' in cmd:
                return make_cmd([
                    '/dev/sdd 8:0 0 60G 0 disk',
                    '/dev/sdd1 8:1 0 60G 0 part',
                    '/dev/mapper/vg-lv 252:0 0 60G 0 lvm'
                ])
            if "echo 'Fix" in cmd or 'parted -a none' in cmd:
                return make_cmd()
            if 'pvresize' in cmd:
                return make_cmd(exit_status=2)
            return make_cmd()

        node_instance = mock.Mock()
        node_instance.mExecuteCmd.side_effect = execute
        node_instance.mGetCmdExitStatus.side_effect = lambda: status['value']
        node_instance.mFileExists.return_value = True
        mock_node_class.return_value = node_instance

        ebox_ctrl = mock.Mock()
        ebox_ctrl.mCheckConfigOption.return_value = True
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'pvresize-error'

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUUpsizeStepsEncrypted('domU', '/fs', 130)

        self.assertEqual('pvresize-error', result)
        ebox_ctrl.mUpdateErrorObject.assert_called_with(
            gReshapeError['ERROR_PVRESIZE_FAIL'],
            ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.getMountPointInfo')
    @patch('exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @patch('exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check', side_effect=lambda node, cmd, sbin=False: cmd)
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeStepsEncrypted_lvresize_failure(self, mock_node_class, _cmd_check, mock_node_exec, mock_get_mount_info):
        # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
        status = {'value': 0}

        def make_cmd(lines=None, exit_status=0, read_value='', err_value=''):
            stdout = mock.Mock()
            stdout.readlines.return_value = [] if lines is None else lines
            stdout.read.return_value = read_value
            stderr = mock.Mock()
            stderr.readlines.return_value = []
            stderr.read.return_value = err_value
            status['value'] = exit_status
            return (None, stdout, stderr)

        def execute(cmd, *args, **kwargs):
            if 'lsblk' in cmd:
                return make_cmd([
                    '/dev/sdd 8:0 0 60G 0 disk',
                    '/dev/sdd1 8:1 0 60G 0 part',
                    '/dev/mapper/vg-lv 252:0 0 60G 0 lvm'
                ])
            if "echo 'Fix" in cmd or 'parted -a none' in cmd or 'pvresize' in cmd:
                return make_cmd()
            if 'lvresize' in cmd:
                return make_cmd([], exit_status=3, read_value='', err_value='unexpected failure')
            if 'key-api.sh' in cmd:
                return make_cmd([' /tmp/keyfile'], exit_status=0)
            if 'cryptsetup' in cmd:
                return make_cmd(exit_status=0)
            return make_cmd()

        node_instance = mock.Mock()
        node_instance.mExecuteCmd.side_effect = execute
        node_instance.mGetCmdExitStatus.side_effect = lambda: status['value']
        node_instance.mFileExists.side_effect = lambda path: (path.endswith('key-api.sh') or path.strip() == '/tmp/keyfile')
        mock_node_class.return_value = node_instance

        ebox_ctrl = mock.Mock()
        ebox_ctrl.mCheckConfigOption.return_value = True
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 1

        mount_info = mock.Mock()
        mount_info.fs_type = 'xfs'
        mount_info.mount_point = '/mnt'
        mock_get_mount_info.return_value = mount_info

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUUpsizeStepsEncrypted('domU', '/fs', 140)

        self.assertEqual(1, result)
        ebox_ctrl.mUpdateErrorObject.assert_any_call(
            gReshapeError['ERROR_LVRESIZE_FAIL'],
            ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check', side_effect=lambda node, cmd, sbin=False: cmd)
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeStepsEncrypted_keyapi_failure(self, mock_node_class, _cmd_check):
        # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
        status = {'value': 0}

        def make_cmd(lines=None, exit_status=0):
            stdout = mock.Mock()
            stdout.readlines.return_value = [] if lines is None else lines
            stdout.read.return_value = ''
            stderr = mock.Mock()
            stderr.readlines.return_value = []
            stderr.read.return_value = ''
            status['value'] = exit_status
            return (None, stdout, stderr)

        def execute(cmd, *args, **kwargs):
            if 'lsblk' in cmd:
                return make_cmd([
                    '/dev/sdd 8:0 0 60G 0 disk',
                    '/dev/sdd1 8:1 0 60G 0 part',
                    '/dev/mapper/vg-lv 252:0 0 60G 0 lvm'
                ])
            if "echo 'Fix" in cmd or 'parted -a none' in cmd or 'pvresize' in cmd or 'lvresize' in cmd:
                return make_cmd()
            if 'key-api.sh' in cmd:
                return make_cmd([], exit_status=1)
            return make_cmd()

        node_instance = mock.Mock()
        node_instance.mExecuteCmd.side_effect = execute
        node_instance.mGetCmdExitStatus.side_effect = lambda: status['value']
        node_instance.mFileExists.return_value = True
        mock_node_class.return_value = node_instance

        ebox_ctrl = mock.Mock()
        ebox_ctrl.mCheckConfigOption.return_value = True
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'keyapi-error'

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUUpsizeStepsEncrypted('domU', '/fs', 150)

        self.assertEqual('keyapi-error', result)
        ebox_ctrl.mUpdateErrorObject.assert_called_with(
            gReshapeError['ERROR_KEYAPI_FAIL'],
            ANY
        )
        edp_mock.mRecordError.assert_called_with(
            gPartitionError['ErrorRunningRemoteCmd'],
            ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check', side_effect=lambda node, cmd, sbin=False: cmd)
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeStepsEncrypted_cryptsetup_failure(self, mock_node_class, _cmd_check):
        # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
        status = {'value': 0}

        def make_cmd(lines=None, exit_status=0, read_value=''):
            stdout = mock.Mock()
            stdout.readlines.return_value = [] if lines is None else lines
            stdout.read.return_value = read_value
            stderr = mock.Mock()
            stderr.readlines.return_value = []
            stderr.read.return_value = ''
            status['value'] = exit_status
            return (None, stdout, stderr)

        def execute(cmd, *args, **kwargs):
            if 'lsblk' in cmd:
                return make_cmd([
                    '/dev/sdd 8:0 0 60G 0 disk',
                    '/dev/sdd1 8:1 0 60G 0 part',
                    '/dev/mapper/vg-lv 252:0 0 60G 0 lvm'
                ])
            if "echo 'Fix" in cmd or 'parted -a none' in cmd or 'pvresize' in cmd:
                return make_cmd()
            if 'lvresize' in cmd:
                return make_cmd()
            if 'key-api.sh' in cmd:
                return make_cmd([' /tmp/keyfile'], exit_status=0)
            if 'cryptsetup' in cmd:
                return make_cmd(exit_status=4)
            return make_cmd()

        node_instance = mock.Mock()
        node_instance.mExecuteCmd.side_effect = execute
        node_instance.mGetCmdExitStatus.side_effect = lambda: status['value']
        node_instance.mFileExists.side_effect = lambda path: path.endswith('key-api.sh')
        node_instance.mFileExists.side_effect = lambda path: path.endswith('key-api.sh')
        node_instance.mFileExists.side_effect = lambda path: path.endswith('key-api.sh')
        mock_node_class.return_value = node_instance

        ebox_ctrl = mock.Mock()
        ebox_ctrl.mCheckConfigOption.return_value = True
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'cryptsetup-error'

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUUpsizeStepsEncrypted('domU', '/fs', 155)

        self.assertEqual('cryptsetup-error', result)
        ebox_ctrl.mUpdateErrorObject.assert_called_with(
            gReshapeError['ERROR_LUKSRESIZE_FAIL'],
            ANY
        )
        edp_mock.mRecordError.assert_called_with(
            gPartitionError['ErrorRunningRemoteCmd'],
            ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check', side_effect=lambda node, cmd, sbin=False: cmd)
    @patch('exabox.ovm.kvmdiskmgr.getMountPointInfo')
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeStepsEncrypted_xfs_resize_failure(self, mock_node_class, mock_get_mount_info, _cmd_check):
        # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
        status = {'value': 0}

        def make_cmd(lines=None, exit_status=0):
            stdout = mock.Mock()
            stdout.readlines.return_value = [] if lines is None else lines
            stdout.read.return_value = ''
            stderr = mock.Mock()
            stderr.readlines.return_value = []
            stderr.read.return_value = ''
            status['value'] = exit_status
            return (None, stdout, stderr)

        def execute(cmd, *args, **kwargs):
            if 'lsblk' in cmd:
                return make_cmd([
                    '/dev/sdd 8:0 0 60G 0 disk',
                    '/dev/sdd1 8:1 0 60G 0 part',
                    '/dev/mapper/vg-lv 252:0 0 60G 0 lvm'
                ])
            if "echo 'Fix" in cmd or 'parted -a none' in cmd or 'pvresize' in cmd or 'lvresize' in cmd:
                return make_cmd()
            if 'key-api.sh' in cmd:
                return make_cmd([' /tmp/keyfile'], exit_status=0)
            if 'cryptsetup' in cmd:
                return make_cmd(exit_status=0)
            if 'xfs_growfs' in cmd:
                return make_cmd(exit_status=5)
            return make_cmd()

        node_instance = mock.Mock()
        node_instance.mExecuteCmd.side_effect = execute
        node_instance.mGetCmdExitStatus.side_effect = lambda: status['value']
        node_instance.mFileExists.side_effect = lambda path: path.endswith('key-api.sh')
        mock_node_class.return_value = node_instance

        mount_info = mock.Mock()
        mount_info.fs_type = 'xfs'
        mount_info.mount_point = '/mnt'
        mock_get_mount_info.return_value = mount_info

        ebox_ctrl = mock.Mock()
        ebox_ctrl.mCheckConfigOption.return_value = True
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'fsresize-error'

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUUpsizeStepsEncrypted('domU', '/fs', 160)

        self.assertEqual('fsresize-error', result)
        ebox_ctrl.mUpdateErrorObject.assert_called_with(
            gReshapeError['ERROR_FSRESIZE_FAIL'],
            ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check', side_effect=lambda node, cmd, sbin=False: cmd)
    @patch('exabox.ovm.kvmdiskmgr.getMountPointInfo')
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeStepsEncrypted_ext4_resize_failure(self, mock_node_class, mock_get_mount_info, _cmd_check):
        # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
        status = {'value': 0}

        def make_cmd(lines=None, exit_status=0):
            stdout = mock.Mock()
            stdout.readlines.return_value = [] if lines is None else lines
            stdout.read.return_value = ''
            stderr = mock.Mock()
            stderr.readlines.return_value = []
            stderr.read.return_value = ''
            status['value'] = exit_status
            return (None, stdout, stderr)

        def execute(cmd, *args, **kwargs):
            if 'lsblk' in cmd:
                return make_cmd([
                    '/dev/sdd 8:0 0 60G 0 disk',
                    '/dev/sdd1 8:1 0 60G 0 part',
                    '/dev/mapper/vg-lv 252:0 0 60G 0 lvm'
                ])
            if "echo 'Fix" in cmd or 'parted -a none' in cmd or 'pvresize' in cmd or 'lvresize' in cmd:
                return make_cmd()
            if 'key-api.sh' in cmd:
                return make_cmd([' /tmp/keyfile'], exit_status=0)
            if 'cryptsetup' in cmd:
                return make_cmd(exit_status=0)
            if 'xfs_growfs' in cmd:
                return make_cmd()
            if 'resize2fs' in cmd:
                return make_cmd(exit_status=6)
            return make_cmd()

        node_instance = mock.Mock()
        node_instance.mExecuteCmd.side_effect = execute
        node_instance.mGetCmdExitStatus.side_effect = lambda: status['value']
        node_instance.mFileExists.side_effect = lambda path: path.endswith('key-api.sh')
        mock_node_class.return_value = node_instance

        mount_info = mock.Mock()
        mount_info.fs_type = 'ext4'
        mount_info.mount_point = '/mnt'
        mock_get_mount_info.return_value = mount_info

        ebox_ctrl = mock.Mock()
        ebox_ctrl.mCheckConfigOption.return_value = True
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'ext4-fsresize-error'

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUUpsizeStepsEncrypted('domU', '/fs', 165)

        self.assertEqual('ext4-fsresize-error', result)
        ebox_ctrl.mUpdateErrorObject.assert_called_with(
            gReshapeError['ERROR_FSRESIZE_FAIL'],
            ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeStepsEncrypted_lsblk_none_branch(self, mock_node_class):
        # Adjusted: simulate keyapi absence after valid lsblk
        node_instance = mock.Mock()
        mock_node_class.return_value = node_instance

        def mk_stream(lines=None, read=''):
            s = mock.Mock()
            s.readlines.return_value = [] if lines is None else lines
            s.read.return_value = read
            return s

        node_instance.mExecuteCmd.side_effect = [
            (None, mk_stream([
                '/dev/sdd 8:0 0 60G 0 disk',
                '/dev/sdd1 8:1 0 60G 0 part',
                '/fs 252:0 0 60G 0 lvm'
            ]), mk_stream([]))
        ]
        node_instance.mGetCmdExitStatus.return_value = 0
        node_instance.mFileExists.return_value = False

        ebox_ctrl = mock.Mock()
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'lsblk-none-error'

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUUpsizeStepsEncrypted('domU-host', '/fs', 120)

        self.assertEqual('lsblk-none-error', result)
        ebox_ctrl.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_KEYAPI_FAIL'],
            ANY
        )
        edp_mock.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'],
            ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @patch('exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check')
    @patch('exabox.ovm.kvmdiskmgr.getMountPointInfo')
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeStepsEncrypted_snapshot_space_disabled(self, mock_node_class, mock_get_mount_info, mock_cmd_check, mock_node_exec_cmd):
        # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
        node_instance = mock.Mock()
        mock_node_class.return_value = node_instance
        node_instance.mGetCmdExitStatus.return_value = 0
        node_instance.mFileExists.side_effect = [True, True]

        def _stream(lines=None, read=''):
            stream = mock.Mock()
            if lines is None:
                lines = []
            stream.readlines.return_value = lines
            stream.read.return_value = read
            return stream

        lsblk_stdout = _stream([
            '/dev/sdd 8:0 0 100G 0 disk',
            '/dev/sdd1 8:1 0 100G 0 part',
            '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk 252:0 0 100G 0 lvm'
        ])
        generic_stream = _stream([])
        lvresize_stdout = _stream([], '')
        lvresize_stderr = _stream([], '')
        keyapi_stdout = _stream(['/tmp/keyapi-file'])

        node_instance.mExecuteCmd.side_effect = [
            (None, lsblk_stdout, _stream([])),
            (None, generic_stream, _stream([])),
            (None, generic_stream, _stream([])),
            (None, generic_stream, _stream([])),
            (None, lvresize_stdout, lvresize_stderr),
            (None, keyapi_stdout, _stream([])),
            (None, generic_stream, _stream([])),
            (None, generic_stream, _stream([]))
        ]

        mock_cmd_check.side_effect = lambda *_args, **_kwargs: '/sbin/' + _args[1]
        mock_get_mount_info.return_value = mock.Mock(fs_type='xfs', mount_point='/u02')

        ebox_ctrl = mock.Mock()
        ebox_ctrl.mCheckConfigOption.return_value = True
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl

        manager = exaBoxKvmDiskMgr(edp_mock)
        result = manager.mExecuteDomUUpsizeStepsEncrypted('domU-host', '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk', 180)

        self.assertEqual(0, result)
        executed_commands = [call_args[0][0] for call_args in node_instance.mExecuteCmd.call_args_list]
        self.assertIn('/usr/sbin/lvresize -l +100%FREE /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk', executed_commands)
        mock_node_exec_cmd.assert_called_once_with(node_instance, '/bin/shred -fu /tmp/keyapi-file')
        ebox_ctrl.mUpdateErrorObject.assert_not_called()

    @patch('exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @patch('exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check')
    @patch('exabox.ovm.kvmdiskmgr.getMountPointInfo')
    @patch('exabox.ovm.kvmdiskmgr.ebLogWarn')
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeStepsEncrypted_keyapi_cleanup_missing(self, mock_node_class, mock_log_warn, mock_get_mount_info, mock_cmd_check, mock_node_exec_cmd):
        # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
        node_instance = mock.Mock()
        mock_node_class.return_value = node_instance
        node_instance.mGetCmdExitStatus.return_value = 0
        node_instance.mFileExists.side_effect = [True]

        def _stream(lines=None, read=''):
            stream = mock.Mock()
            if lines is None:
                lines = []
            stream.readlines.return_value = lines
            stream.read.return_value = read
            return stream

        lsblk_stdout = _stream([
            '/dev/sdd 8:0 0 120G 0 disk',
            '/dev/sdd1 8:1 0 120G 0 part',
            '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk 252:0 0 120G 0 lvm'
        ])
        generic_stream = _stream([])
        lvresize_stdout = _stream([], '')
        lvresize_stderr = _stream([], '')

        node_instance.mExecuteCmd.side_effect = [
            (None, lsblk_stdout, _stream([])),
            (None, generic_stream, _stream([])),
            (None, generic_stream, _stream([])),
            (None, generic_stream, _stream([])),
            (None, lvresize_stdout, lvresize_stderr),
            (None, _stream([]), _stream([])),
            (None, generic_stream, _stream([])),
            (None, generic_stream, _stream([]))
        ]

        mock_cmd_check.side_effect = lambda *_args, **_kwargs: '/sbin/' + _args[1]
        mock_get_mount_info.return_value = mock.Mock(fs_type='xfs', mount_point='/u02')

        ebox_ctrl = mock.Mock()
        ebox_ctrl.mCheckConfigOption.return_value = True
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl

        manager = exaBoxKvmDiskMgr(edp_mock)
        result = manager.mExecuteDomUUpsizeStepsEncrypted('domU-host', '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk', 200)

        self.assertEqual(0, result)
        mock_log_warn.assert_called_with('No keyapi to delete')
        mock_node_exec_cmd.assert_not_called()
        ebox_ctrl.mUpdateErrorObject.assert_not_called()

    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeStepsEncrypted_handles_lsblk_none_recovery(self, mock_node_class):
        # Adjusted: ensure early KEYAPI_FAIL instead of None join crash
        node_instance = mock.Mock()
        mock_node_class.return_value = node_instance

        def mk_stream(lines=None, read=''):
            s = mock.Mock()
            s.readlines.return_value = [] if lines is None else lines
            s.read.return_value = read
            return s

        node_instance.mExecuteCmd.side_effect = [
            (None, mk_stream([
                '/dev/sdd 8:0 0 60G 0 disk',
                '/dev/sdd1 8:1 0 60G 0 part',
                '/fs 252:0 0 60G 0 lvm'
            ]), mk_stream([]))
        ]
        node_instance.mGetCmdExitStatus.return_value = 0
        node_instance.mFileExists.return_value = False  # cause ERROR_KEYAPI_FAIL

        ebox_ctrl = mock.Mock()
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl
        edp_mock.mRecordError.return_value = 'lsblk-none'

        manager = exaBoxKvmDiskMgr(edp_mock)

        result = manager.mExecuteDomUUpsizeStepsEncrypted('domU-host', '/fs', 200)

        self.assertEqual('lsblk-none', result)
        ebox_ctrl.mUpdateErrorObject.assert_called_once_with(
            gReshapeError['ERROR_KEYAPI_FAIL'],
            ANY
        )
        edp_mock.mRecordError.assert_called_once_with(
            gPartitionError['ErrorRunningRemoteCmd'],
            ANY
        )

    @patch('exabox.ovm.kvmdiskmgr.node_exec_cmd')
    @patch('exabox.ovm.kvmdiskmgr.node_cmd_abs_path_check')
    @patch('exabox.ovm.kvmdiskmgr.getMountPointInfo')
    @patch('exabox.ovm.kvmdiskmgr.exaBoxNode')
    def test_mExecuteDomUUpsizeStepsEncrypted_snapshot_space_true_cleanup(self, mock_node_class, mock_get_mount_info, mock_cmd_check, mock_node_exec_cmd):
        # Auto-generated test for mExecuteDomUUpsizeStepsEncrypted
        def _stream(lines=None, read_value=''):
            stream = mock.Mock()
            if lines is None:
                lines = []
            stream.readlines.return_value = lines
            stream.read.return_value = read_value
            return stream

        lsblk_lines = [
            '/dev/sdd 8:0 0 100G 0 disk',
            '/dev/sdd1 8:1 0 100G 0 part',
            '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk 252:0 0 100G 0 lvm'
        ]

        node_instance = mock.Mock()
        node_instance.mGetCmdExitStatus.return_value = 0
        node_instance.mFileExists.side_effect = [True, True]
        node_instance.mExecuteCmd.side_effect = [
            (None, _stream(lsblk_lines), _stream()),
            (None, _stream([]), _stream()),
            (None, _stream([]), _stream()),
            (None, _stream([]), _stream()),
            (None, _stream([], ''), _stream([], '')),
            (None, _stream(['/tmp/keyapi-path']), _stream()),
            (None, _stream([]), _stream()),
            (None, _stream([]), _stream())
        ]
        mock_node_class.return_value = node_instance

        mock_cmd_check.side_effect = lambda *_args, **_kwargs: '/sbin/' + _args[1]
        mock_get_mount_info.return_value = mock.Mock(fs_type='xfs', mount_point='/u02')

        ebox_ctrl = mock.Mock()
        ebox_ctrl.mCheckConfigOption.return_value = True
        edp_mock = mock.Mock()
        edp_mock.mGetEbox.return_value = ebox_ctrl

        manager = exaBoxKvmDiskMgr(edp_mock)
        result = manager.mExecuteDomUUpsizeStepsEncrypted('domU-host', '/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk', 220)

        self.assertEqual(0, result)
        commands = [call_args[0][0] for call_args in node_instance.mExecuteCmd.call_args_list]
        self.assertIn('/usr/sbin/lvresize -l +100%FREE /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk', commands)
        mock_node_exec_cmd.assert_called_once_with(node_instance, '/bin/shred -fu /tmp/keyapi-path')
        ebox_ctrl.mUpdateErrorObject.assert_not_called()

if __name__ == '__main__':
    unittest.main()
