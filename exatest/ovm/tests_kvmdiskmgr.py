"""

 $Header: 

 Copyright (c) 2020, 2025, Oracle and/or its affiliates.

 NAME:
      tests_kvmdiskmgr.py - Unitest for kvmdiskmgr.py and cludomupartitions.py module

 DESCRIPTION:
      Run tests for the methods of module

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
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
from typing import Dict
import io
from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.ovm.cluencryption import MountPointInfo
from exabox.ovm.kvmdiskmgr import exaBoxKvmDiskMgr
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.ovm.cludomupartitions import ebCluManageDomUPartition
from exabox.log.LogMgr import ebLogInfo
from unittest import mock
from unittest.mock import patch, MagicMock, PropertyMock, mock_open

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

class testOptions(object): pass

class ebTestKVMDiskMgr(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        # Surcharge ebTestClucontrol, to specify noDB/noOEDA
        super().setUpClass(True,True)    

    def setUp(self):
        #Ensure every test begin with standard conf
        self.mGetClubox()._exaBoxCluCtrl__ociexacc = False
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        get_gcontext().mSetConfigOption('kvm_var_size',None)
        get_gcontext().mSetConfigOption('kvm_u01_size',None)

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
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP4, aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("df -h -B G -P /dev", aStdout=domUCommandOP1, aRc=0, aPersist=True),
                    exaMockCommand("mount ", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP2, aRc=0, aPersist=True),
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
                    exaMockCommand("/usr/bin/ls -l.*", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("lsof | grep dev", aStdout=domUCommandOP2, aRc=0, aPersist=True),
                    exaMockCommand("kill -", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/df", aStdout=None, aRc=1, aPersist=True),

                    exaMockCommand("umount ", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("cat /etc/oratab", aStdout="/u01/app/19.0.0.0/grid", aRc=0, aPersist=0),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aStdout="19.0.0.0.0"),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/19.0.0.0/grid; $ORACLE_HOME/bin/orabase"), aStdout="/u01/app/grid"),
                    exaMockCommand("/bin/test -e /sbin/findmnt", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("/sbin/findmnt --output TARGET --noheadings -R -r", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("lsof | grep dev", aStdout=domUCommandOP2, aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/ls -l.*", aStdout=None, aRc=0, aPersist=True),
                    exaMockCommand("kill -", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/findmnt", aStdout=None, aRc=1, aPersist=True),
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
                    exaMockCommand("e2fsck -f", aRc=0, aPersist=True),
                    exaMockCommand("mount", aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/sbin/fdisk -l", aStdout=domUCommandOP4, aRc=0, aPersist=True),
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
        self.assertNotEqual(cluDomUPartitionObj.mClusterManageDomUPartition("resize", currentOptions), 0)
        currentOptions.jsonconf = {"partitionName": "dummy","new_sizeGB": "50"}
        self.assertNotEqual(cluDomUPartitionObj.mClusterManageDomUPartition("resize", currentOptions), 0)
        currentOptions.jsonconf = {"partitionName": "dev","new_sizeGB": "50"}
        cluDomUPartitionObj2 = ebCluManageDomUPartition(self.mGetClubox())
        ebLogInfo(cluDomUPartitionObj2.mClusterManageDomUPartition("resize", currentOptions))
        ebLogInfo("Completed unit test on exaBoxKvmDiskMgr.mClusterPartitionResize")


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

    def test_mDownSizeDomU_metacsum(self):
        # Validate scenario that code generates below commands
        _cmds = {
            self.mGetRegexVm(): [
                [exaMockCommand("lsblk -p -r | grep -B 2 /dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk", aStdout="""/dev/sdd 8:48 0 60G 0 disk
/dev/sdd1 8:49 0 80G 0 part
/dev/mapper/VGExaDbDisk.u02_extra.img-LVDBDisk 252:0 0 80G 0 lvm
"""
),
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

if __name__ == '__main__':
    unittest.main() 
