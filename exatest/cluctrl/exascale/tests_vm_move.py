#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/exascale/tests_vm_move.py /main/35 2025/11/18 13:05:44 dekuckre Exp $
#
# tests_vm_move.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_vm_move.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    07/12/25 - Bug 38176800 -> Updating test case for validate
#                           volumes
#    prsshukl    06/27/25 - Enh 37747083 - Added check for
#                           mPerformValidateVolumesCheck
#    scoral      05/06/25 - Bug 37665235 - Improved
#                           test_005_vm_move_prechecks_oeda to include mock
#                           commands for source host checks.
#    scoral      03/28/25 - Bug 37756495 - Added unit tests for
#                           mPostVMMoveSteps
#    asrigiri    10/31/24 - Bug 36981061 - EXACC:LOCAL FS RESIZE FETCHES ALL FS
#                           DETAILS INCLUDING NFS MOUNTS
#    prsshukl    05/11/24 - Bug 36608539 - Fix test_001_vm_move_exacloud
#    gparada     10/11/23 - Bug 35891714 Fix test_004_vm_move_prechecks mock
#    jfsaldan    09/04/23 - Bug 35759673 - EXACS:23.4.1:XEN:FILE SYSTEM
#                           ENCRYPTION:SKIP U02 RESIZE ON XEN IF ENCRPYTED
#    gparada     08/01/23 - Added scenario to skip VmMoveSanityChecks on EDV
#    jesandov    12/06/22 - Creation
#

import os
import re
import unittest
import shutil
from unittest.mock import patch
 
from exabox.core.MockCommand import MockCommand, exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.core.Error import ExacloudRuntimeError
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.cluexascale import ebCluExaScale
from exabox.ovm.clucommandhandler import CommandHandler
def myRun(FromXml, ToXml):
    shutil.copyfile(FromXml, ToXml)

class ebTestVmMove(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True, aUseOeda=True)
        self.mGetClubox(self).mSetExaScale(True)
        self.mGetClubox(self).mSetDebug(True)
        self.mGetClubox(self).mGetCtx().mSetConfigOption('exakms_validate_import_export', "False")

    @patch("exabox.ovm.cluexascale.ebCluExaScale.mPerformValidateVolumesCheck")
    @patch("exabox.ovm.cluexascale.ebCluExaScale.mPostVMMoveSteps")
    @patch("exabox.tools.ebOedacli.ebOedacli.ebOedacli.mRun", wraps=myRun)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mDom0UpdateCurrentOpLog')
    @patch('socket.gethostbyname', return_value="localhost")
    def test_001_vm_move_exacloud(self, mock_mPerformValidateVolCheck, mock_postvmsteps, mock_myRun, mock_mDom0UpdateCurrentOpLog, mock_socket):

        #Mock commands
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    MockCommand(".*mkdir.*exascale.*", ebTestClucontrol.mRealExecute),
                    MockCommand(".*rm.*exascale.*", ebTestClucontrol.mRealExecute),
                    MockCommand("cp.*", ebTestClucontrol.mRealExecute),
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test.*", aPersist=True),
                    exaMockCommand("mkdir.*", aPersist=True),
                    exaMockCommand("ls.*zip.*", aStdout="sample_image.zip"),
                    exaMockCommand("virsh list.*", aStdout=""),
                    exaMockCommand("cat.*xml.*", aStdout="<domU></domU>"),
                    exaMockCommand("ls.*img.*", aStdout="sample_image.img"),
                    exaMockCommand("bzip2 sample_image.img.*"),
                    exaMockCommand("scp.*bz2.*"),
                    exaMockCommand("vm_maker.*--remove.*", aPersist=True),
                ],
                [
                    exaMockCommand("test.*", aPersist=True),
                ],
                [
                    exaMockCommand("test.*", aPersist=True),
                    exaMockCommand("virsh list.*", aStdout="scaqab10adm01vm08.us.oracle.com"),
                    exaMockCommand("rm.*", aPersist=True),
                    exaMockCommand("sed.*", aPersist=True),
                    exaMockCommand("scp.*", aPersist=True),
                    exaMockCommand("vm_maker.*", aPersist=True),
                    exaMockCommand("test.*", aPersist=True),
                    exaMockCommand("vm_maker.*--start.*"),
                    exaMockCommand("virsh list.*", aStdout="scaqab10adm01vm08.us.oracle.com"),
                    exaMockCommand("virsh.*destroy.*", aPersist=True),
                    exaMockCommand("virsh list.*", aStdout=""),
                    exaMockCommand("ls.*bz2.*", aStdout="sample_image.bz2"),
                    exaMockCommand("bunzip2 sample_image.bz2"),
                    exaMockCommand("mv.*img.*"),
                    exaMockCommand("virsh domblklist.*", aStdout="sda u02_extra.img"),
                    exaMockCommand("virsh list.*", aStdout=""),
                    exaMockCommand("vm_maker.*", aPersist=True),
                ],
                [
                    exaMockCommand("test.*", aPersist=True),
                    exaMockCommand("vm_maker.*--start.*"),
                    exaMockCommand("virsh list.*", aStdout="scaqab10adm01vm08.us.oracle.com"),
                    exaMockCommand("virsh.*destroy.*"),
                    exaMockCommand("virsh list.*", aStdout=""),
                    exaMockCommand("ls.*bz2.*", aStdout="sample_image.bz2"),
                    exaMockCommand("bunzip2 sample_image.bz2"),
                    exaMockCommand("mv.*img.*"),
                    exaMockCommand("virsh domblklist.*", aStdout="sda u02_extra.img"),
                    exaMockCommand("virsh list.*", aStdout=""),
                    exaMockCommand("vm_maker.*", aPersist=True),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        self.mGetContext().mSetConfigOption("exascale", {"vm_move_api": "exacloud"})
        self.mGetClubox().mSetPatchConfig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/sample.xml"))

        # Create XML for test
        _xmlToUse = os.path.join(self.mGetUtil().mGetOutputDir(), "sample.xml")
        _xmlOriginal = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/sample.xml")

        shutil.copyfile(_xmlOriginal, _xmlToUse)
        self.mGetClubox().mSetPatchConfig(_xmlToUse)

        # Create Exakms key
        _exakms = self.mGetContext().mGetExaKms()
        _privateKey = _exakms.mGetEntryClass().mGeneratePrivateKey()

        _entry = _exakms.mBuildExaKmsEntry("scaqab10adm01vm08.us.oracle.com", "root", _privateKey)
        _exakms.mInsertExaKmsEntry(_entry)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "action": "move",
            "vm_name": "scaqab10adm01vm08.us.oracle.com",
            "target_dom0_name": "scaqab10adm07.us.oracle.com",
            "source_dom0_name": "scaqab10adm01.us.oracle.com",
            "new_admin_ip": "77.10.15.10",
            "new_admin_hostname": "jesandov-test-vm",
            "new_admin_domainname": "us.oracle.com",
        }
        
        #Execute the clucontrol function
        _exascale = ebCluExaScale(self.mGetClubox())
        _exascale.mPerformVmMove(_options)


    @patch("exabox.ovm.cluexascale.ebCluExaScale.mPerformValidateVolumesCheck")
    @patch('exabox.ovm.cluiptablesroce.ebIpTablesRoCE.mSetNfTablesExaBM')
    @patch("exabox.tools.ebOedacli.ebOedacli.ebOedacli.mRun", wraps=myRun)
    @patch("exabox.tools.ebOedacli.ebOedacli.ebOedacli.mProbePath", return_value=True)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mDom0UpdateCurrentOpLog')  
    @patch('socket.gethostbyname', return_value="localhost")
    def test_002_vm_move_oeda(self, mock_mPerformValidateVolCheck, mock_mSetNfTablesExaBM, mock_mRun, mock_mProbePath, mock_mDom0UpdateCurrentOpLog, mock_socket):

        _tgtVMBridges = (
            " Interface   Type      Source            Model     MAC\n"
            "----------------------------------------------------------------------\n"
            " -           bridge    vmbondeth0.1239   virtio    00:00:17:01:bc:70\n"
            " -           bridge    vmbondeth0.1240   virtio    00:00:17:01:1a:7c\n"
            " -           network   re0_vf_pool       rtl8139   52:54:00:81:5f:4f\n"
            " -           network   re1_vf_pool       rtl8139   52:54:00:46:5b:ee\n"
            " -           network   re0_vf_pool       rtl8139   52:54:00:90:73:b4\n"
            " -           network   re1_vf_pool       rtl8139   52:54:00:53:a7:50\n"
            " -           bridge    vmeth205          virtio    52:54:00:6e:97:ee\n"
        )
        _tgtHostBridges = (
            "bridge name     bridge id               STP enabled     interfaces\n"
            "vmbondeth0\t              8000.b8cef67104a0       no              bondeth0\n"
            "vmeth0\t          8000.001b21e7b71d       no              eth0\n"
            "vmeth0.102\t              8000.001b21e7b71d       no              eth0.102\n"
            "vmeth205\t                8000.2ea3253eabe0       no              eth205\n"
        )
        _vmDisks = (
            " sda      /dev/exc/system_Vmrievh_1_e1f4\n"
            " sdb      /dev/exc/u01_Vmrievh_1_f049\n"
        )
        _interfaces_output = """    <Interfaces>
        <Bridge>dummy</Bridge>
        <Gateway>10.1.0.1</Gateway>
        <Hostname>sea201605exddu0803.localdomain</Hostname>
        <IP_address>10.1.2.31</IP_address>
        <Name>eth0</Name>
        <IP_enabled>yes</IP_enabled>
        <IP_ssh_listen>enabled</IP_ssh_listen>
        <Net_type>Other</Net_type>
        <Netmask>255.255.0.0</Netmask>
        <State>1</State>
        <Status>UP</Status>
        <Vlan_id>101</Vlan_id>
        <nategressipaddresses>10.0.1.0/28</nategressipaddresses>
        <nategressipaddresses>10.0.1.32/28</nategressipaddresses>
        <nategressipaddresses>10.0.1.112/28</nategressipaddresses>
        </Interfaces>"""

        _out = """  sda      /dev/exc/system_Vmnhtzu_3_0d9d
         sdb      /dev/exc/u01_Vmnhtzu_3_0bbf
         sdc      /dev/exc/u02_Vmnhtzu_3_46d9
         """

        _vmXMLPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/vm.xml")
        with open(_vmXMLPath, "r") as _f:
            _vmXML = _f.read()
        #Mock commands
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    MockCommand(".*mkdir.*", ebTestClucontrol.mRealExecute, aPersist=True),
                    MockCommand(".*rm.*exascale.*", ebTestClucontrol.mRealExecute),
                    MockCommand(".*chmod.*", ebTestClucontrol.mRealExecute),
                    MockCommand(".*stage.*", ebTestClucontrol.mRealExecute),
                    MockCommand("cp.*", ebTestClucontrol.mRealExecute),
                    MockCommand("grep*", ebTestClucontrol.mRealExecute, aPersist=True),
                    MockCommand("sed*", ebTestClucontrol.mRealExecute, aPersist=True),
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(".*test.*"),
                    exaMockCommand(".*cat.*"),
                    exaMockCommand(".*rm.*"),
                    exaMockCommand(".*test.*"),
                    exaMockCommand(".*cat.*"),
                    exaMockCommand(".*rm.*"),
                    exaMockCommand("nft list chain ip nat PREROUTING .*")
                ],
                [
                    exaMockCommand(".*test.*"),
                    exaMockCommand(".*cat.*"),
                    exaMockCommand(".*rm.*"),
                    exaMockCommand(".*mkdir.*"),
                    exaMockCommand(".*mount.*"),
                    exaMockCommand(".*echo.*"),
                    exaMockCommand(".*test.*"),
                    exaMockCommand(".*ls.*"),
                    exaMockCommand(".*virsh.*", aStdout=_tgtVMBridges),
                    exaMockCommand(".*brctl.*", aStdout=_tgtHostBridges),
                    exaMockCommand(".*ls.*", aStdout="/etc/sysconfig/network-scripts/ifcfg-vmeth0.102:205"),
                    exaMockCommand(".*cat.*", aStdout="IPADDR=10.0.1.1"),
                    exaMockCommand(".*cat.*", aStdout="IPADDR=169.254.200.1"),
                    exaMockCommand("/bin/cat /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/scaqab10client01vm08.us.oracle.com.xml", aStdout=_vmXML),
                    exaMockCommand("/bin/test -e /etc/sysconfig/network-scripts/route-vmeth205"),
                    exaMockCommand("/bin/test -e /etc/sysconfig/network-scripts/rule-vmeth205"),
                    exaMockCommand("/bin/virsh domblklist scaqab10client01vm08.us.oracle.com", aStdout=_vmDisks),
                    exaMockCommand("/bin/ls /dev/exc/u02_Vmrievh", aStdout="/dev/exc/u02_Vmrievh_1_31b1"),
                    exaMockCommand("/bin/test -e /dev/exc/u02_Vmrievh_1_31b1"),
                    exaMockCommand("/bin/test -e /bin/virsh"),
                    exaMockCommand("/bin/virsh domblklist scaqab10client01vm08.us.oracle.com | tail -n +3", aStdout=_vmDisks),
                    exaMockCommand("/bin/virsh list", aStdout="scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("/opt/exadata_ovm/vm_maker --attach --disk-image /dev/exc/u02_Vmrievh_1_31b1 --domain scaqab10client01vm08.us.oracle.com "),
                    exaMockCommand("/bin/virsh dumpxml scaqab10client01vm08.us.oracle.com | /bin/grep serial.sock | /bin/cut -d\"/\" -f4", aStdout="341e"),
                    exaMockCommand("/bin/ln -s /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/console/write-qemu /EXAVMIMAGES/console/341e/write-qemu"),
                    exaMockCommand(".*brctl.*", aStdout=_tgtHostBridges),
                    exaMockCommand("/opt/exadata_ovm/vm_maker --add-bonded-bridge vmbondeth0 --first-slave eth1 --second-slave eth2 --vlan UNDEFINED --bond-mode active-backup"),
                    exaMockCommand("/opt/exadata_ovm/vm_maker --add-bonded-bridge vmbondeth0 --first-slave eth1 --second-slave eth2 --vlan UNDEFINED --bond-mode active-backup"),
                    exaMockCommand("/sbin/ifup bondeth0.UNDEFINED"),
                    exaMockCommand("/sbin/ifup bondeth0.UNDEFINED"),
                    exaMockCommand("/sbin/ifup vmbondeth0.UNDEFINED"),
                    exaMockCommand("/sbin/ifup vmbondeth0.UNDEFINED"),
                    exaMockCommand("/bin/cp -f /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/scaqab10client01vm08.us.oracle.com.xml /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com-vm.xml"),
                    exaMockCommand("nft list chain ip nat PREROUTING .*")
                ],
                [
                    exaMockCommand(".*mkdir.*"),
                    exaMockCommand(".*mount.*"),
                    exaMockCommand(".*cat.*", aRc=1),
                    exaMockCommand(".*echo.*"),
                    exaMockCommand(".*test.*"),
                    exaMockCommand(".*rm.*"),
                    exaMockCommand("vm_maker.*", aPersist=True),
                    exaMockCommand("/usr/sbin/nft add table ip filter"),
                    exaMockCommand("/usr/sbin/nft add table bridge filter"),
                    exaMockCommand("/bin/ls /dev/exc/gcv_Vm53942_1_b60b"),
                    exaMockCommand("/bin/test -e /bin/virsh"),
                    exaMockCommand("/bin/virsh domiflist .*", aStdout=_tgtVMBridges),
                    exaMockCommand("/bin/test -e /bin/ls"),
                    exaMockCommand("/bin/cat /etc/sysconfig/network-scripts/ifcfg-vmeth0:205", aStdout="IPADDR=10.0.131.54"),
                    exaMockCommand("/bin/cat /etc/sysconfig/network-scripts/ifcfg-vmeth205", aStdout="IPADDR=10.0.131.54"),
                    exaMockCommand("/bin/cat /EXAVMIMAGES/GuestImages/.*xml", aStdout=_interfaces_output),
                    exaMockCommand("/bin/virsh domblklist .*", aStdout=_out),
                    exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-vmeth0.*", aStdout="/etc/sysconfig/network-scripts/ifcfg-vmeth0:205"),
                    exaMockCommand("/bin/ls /dev/exc/u02_Vmnhtzu_", aStdout="/dev/exc/u02_Vmnhtzu_3_46d9"),
                    exaMockCommand("/bin/test -e /dev/exc/.*"),
                    exaMockCommand("/bin/test -e /bin/virsh"),
                    exaMockCommand("/bin/virsh domblklist scaqab10client01vm08.us.oracle.com | tail -n +3", aStdout=_out),
                    exaMockCommand("/bin/virsh dumpxml .*"),
                    exaMockCommand("/bin/ln -s .*"),
                    exaMockCommand("/bin/test -e /sbin/brctl"),
                    exaMockCommand("/sbin/brctl show", aStdout=_tgtHostBridges),
                    exaMockCommand("/sbin/ifup .*"),                    
                    exaMockCommand("/sbin/ifup .*"),                    
                    exaMockCommand("/sbin/ifup .*"),                    
                    exaMockCommand("/sbin/ifup .*"),
                    exaMockCommand("/bin/cp -f .*"),
                    exaMockCommand("ls *"),
                    exaMockCommand("ls *")
                ],
                [ 
                    exaMockCommand("vm_maker.*", aPersist=True),
                    exaMockCommand(".*mkdir.*"),
                    exaMockCommand(".*mount.*"),
                    exaMockCommand(".*cat.*", aRc=1),
                    exaMockCommand(".*echo.*"),
                    exaMockCommand(".*test.*"),
                    exaMockCommand(".*rm.*"),
                    exaMockCommand("/usr/sbin/nft .*"),                    
                    exaMockCommand("/usr/sbin/nft .*")                    
                ],
                [
                    exaMockCommand("/usr/bin/mount .*"),
                    exaMockCommand("/usr/bin/mkdir .*"),
                    exaMockCommand("/bin/cat /etc/fstab .*")
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _exacloudPath = os.path.abspath(__file__)
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]

        self.mGetContext().mSetConfigOption("exascale", {"vm_move_api": "oeda"})

        _xmlToUse = os.path.join(self.mGetUtil().mGetOutputDir(), "sample.xml")
        _xmlOriginal = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/sample.xml")

        shutil.copyfile(_xmlOriginal, _xmlToUse)
        self.mGetClubox().mSetPatchConfig(_xmlToUse)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "action": "move",
            "vm_name": "scaqab10client01vm08.us.oracle.com",
            "target_dom0_name": "scaqab10adm07.us.oracle.com",
            "source_dom0_name": "scaqab10adm01.us.oracle.com",
            "new_admin_ip": "77.10.15.10",
            "new_admin_hostname": "jesandov-test-vm",
            "new_admin_domainname": "us.oracle.com",
            "new_admin_mask": "255.255.0.0"
        }

        #Execute the clucontrol function
        _exascale = ebCluExaScale(self.mGetClubox())
        _exascale.mPerformVmMove(_options)
        _exascale.mMountVolumesVmMove(_options)

    @patch("exabox.ovm.cluexascale.ebCluExaScale.mPostVMMoveSteps")
    @patch("exabox.tools.ebOedacli.ebOedacli.ebOedacli.mRun", wraps=myRun)
    @patch("exabox.tools.ebOedacli.ebOedacli.ebOedacli.mProbePath", return_value=True)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mDom0UpdateCurrentOpLog')  
    @patch('socket.gethostbyname', return_value="localhost")
    def test_003_vm_move_prepare_oeda(self, mock_mPostVMMoveSteps, mock_mRun, mock_mProbePath, mock_mDom0UpdateCurrentOpLog, mock_socket):

        #Mock commands
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    MockCommand(".*mkdir.*", ebTestClucontrol.mRealExecute, aPersist=True),
                    MockCommand(".*rm.*exascale.*", ebTestClucontrol.mRealExecute),
                    MockCommand(".*chmod.*", ebTestClucontrol.mRealExecute),
                    MockCommand(".*stage.*", ebTestClucontrol.mRealExecute),
                    exaMockCommand(".*ping.*", aRc=1, aPersist=True),
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(".*umount.*"),
                    exaMockCommand(".*rmdir.*"),
                    exaMockCommand(".*sed.*"),
                    exaMockCommand(".*mount.*"),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _exacloudPath = os.path.abspath(__file__)
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]

        self.mGetContext().mSetConfigOption("exascale", {"vm_move_api": "oeda"})

        _xmlToUse = os.path.join(self.mGetUtil().mGetOutputDir(), "sample.xml")
        _xmlOriginal = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/sample.xml")

        shutil.copyfile(_xmlOriginal, _xmlToUse)
        self.mGetClubox().mSetPatchConfig(_xmlToUse)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "action": "move",
            "vm_name": "scaqab10client01vm08.us.oracle.com",
            "target_dom0_name": "scaqab10adm07.us.oracle.com",
            "source_dom0_name": "scaqab10adm01.us.oracle.com",
            "new_admin_ip": "77.10.15.10",
            "new_admin_hostname": "jesandov-test-vm",
            "new_admin_domainname": "us.oracle.com",
            "new_admin_mask": "255.255.0.0"
        }

        #Execute the clucontrol function
        _exascale = ebCluExaScale(self.mGetClubox())
        _exascale.mPrepareVmMoveOEDA(_options)


    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mDom0UpdateCurrentOpLog')  
    @patch('socket.gethostbyname', return_value="localhost")
    def test_004_vm_move_prechecks_exacloud(self, mock_mDom0UpdateCurrentOpLog, mock_socket):

        _sourceDom0 = "scaqab10adm01.us.oracle.com"
        _targetDom0 = "scaqab10adm07.us.oracle.com"
        _vmName = "scaqab10adm01vm08.us.oracle.com"
        #Mock commands
        _cmds = {
            _sourceDom0: [
                [
                    exaMockCommand("/bin/test -e /bin/ls"),
                    exaMockCommand(re.escape("/bin/ls /EXAVMIMAGES/*.zip"), aStdout="/EXAVMIMAGES/test.zip"),
                    exaMockCommand("/bin/test -e /bin/df"),
                    exaMockCommand("/bin/test -e /bin/grep"),
                    exaMockCommand("/bin/df --local --output=target,source,fstype,size,avail --block-size=1 | /bin/grep -v 'nfs'", aStdout=(
                        "Mounted on   Filesystem   Type   1B-blocks   Avail\n"
                        "/EXAVMIMAGES /dev/sda     ext4   2048        1024")),
                    exaMockCommand(f"/bin/cat /EXAVMIMAGES/conf/{_vmName}-vm.xml",
                                   aStdout="<domuVolume>/EXAVMIMAGES/test2.zip</domuVolume>"),
                    exaMockCommand(re.escape(f"/bin/ls /EXAVMIMAGES/GuestImages/{_vmName}/*.img"),
                                   aStdout=f"/EXAVMIMAGES/GuestImages/{_vmName}/System.img"),
                    exaMockCommand(f"/bin/stat /EXAVMIMAGES/GuestImages/{_vmName}/System.img",
                                   aStdout="Size: 64"),
                    exaMockCommand("/bin/stat /EXAVMIMAGES/test2.zip", aStdout="Size: 32"),
                    exaMockCommand("/bin/test -e /bin/lsblk", aPersist=True),
                    exaMockCommand("/bin/lsblk -rno TYPE /dev/sda"),
                ]
            ],
            _targetDom0: [
                [
                    exaMockCommand("/bin/test -e /bin/ls"),
                    exaMockCommand(re.escape("/bin/ls /EXAVMIMAGES/*.zip"), aStdout="/EXAVMIMAGES/test3.zip"),
                    exaMockCommand("/bin/test -e /bin/df"),
                    exaMockCommand("/bin/test -e /bin/grep"),
                    exaMockCommand("/bin/df --local --output=target,source,fstype,size,avail --block-size=1 | /bin/grep -v 'nfs'", aStdout=(
                        "Mounted on   Filesystem   Type   1B-blocks   Avail\n"
                        "/EXAVMIMAGES /dev/sda     ext4   1024        512")),
                    exaMockCommand("/bin/test -e /bin/lsblk", aPersist=True),
                    exaMockCommand("/bin/lsblk -rno TYPE /dev/sda"),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "action": "moveSanityCheck",
            "vm_name": _vmName,
            "target_dom0_name": _targetDom0,
            "source_dom0_name": _sourceDom0,
            "new_admin_ip": "77.10.15.10",
            "new_admin_hostname": "jesandov-test-vm",
            "new_admin_domainname": "us.oracle.com",
        }

        #Execute the clucontrol function
        _exascale = ebCluExaScale(self.mGetClubox())
        with patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckConfigOption",
                   return_value={"vm_move_api": "exacloud"}):
            _exascale.mPerformVmMove(_options)


    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mDom0UpdateCurrentOpLog')  
    @patch('socket.gethostbyname', return_value="localhost")
    def test_005_vm_move_prechecks_oeda(self, mock_mDom0UpdateCurrentOpLog, mock_socket):

        _sourceDom0 = "scaqab10adm01.us.oracle.com"
        _targetDom0 = "scaqab10adm07.us.oracle.com"
        _vmName = "scaqab10adm01vm08.us.oracle.com"

        _tgtVMBridges = (
            " Interface   Type      Source            Model     MAC\n"
            "----------------------------------------------------------------------\n"
            " -           bridge    vmbondeth0.1239   virtio    00:00:17:01:bc:70\n"
            " -           bridge    vmbondeth0.1240   virtio    00:00:17:01:1a:7c\n"
            " -           network   re0_vf_pool       rtl8139   52:54:00:81:5f:4f\n"
            " -           network   re1_vf_pool       rtl8139   52:54:00:46:5b:ee\n"
            " -           network   re0_vf_pool       rtl8139   52:54:00:90:73:b4\n"
            " -           network   re1_vf_pool       rtl8139   52:54:00:53:a7:50\n"
            " -           bridge    vmeth205          virtio    52:54:00:6e:97:ee\n"
        )
        _tgtHostBridges = (
            "bridge name     bridge id               STP enabled     interfaces\n"
            "vmbondeth0\t              8000.b8cef67104a0       no              bondeth0\n"
            "vmbondeth0.1239\t         8000.b8cef67104a0       no              bondeth0.1239\n"
            "vmbondeth0.1240\t         8000.b8cef67104a0       no              bondeth0.1240\n"
            "vmeth0\t          8000.001b21e7b71d       no              eth0\n"
            "vmeth0.102\t              8000.001b21e7b71d       no              eth0.102\n"
            "vmeth205\t                8000.2ea3253eabe0       no              eth205\n"
        )
        _tgtHostVMBridges = (
            "vmbondeth0.1239\n"
            "vmbondeth0.1240\n"
        )
        _tgtFSs = (
            "Mounted on                                                                   Filesystem                  Type  1B-blocks      Avail\n"
            "/EXAVMIMAGES/GuestImages/exaxs2511-mwnhe.exadbxs.exadbxsdevvcn.oraclevcn.com /dev/exc/gcv_Vmrievh_1_e00a xfs  2042626048 1990975488\n"
        )

        #Mock commands
        _cmds = {
            _targetDom0: [
                [
                    exaMockCommand("/bin/test -e /bin/rmdir"),
                    exaMockCommand("/bin/test -e /bin/df"),
                    exaMockCommand("/bin/test -e /bin/lsblk"),
                    exaMockCommand("/bin/test -e /bin/grep"),
                    exaMockCommand(re.escape("/bin/df --local --output=target,source,fstype,size,avail --block-size=1 | /bin/grep -v 'nfs'"), aStdout=_tgtFSs),
                    exaMockCommand("/bin/lsblk -rno TYPE /dev/exc/gcv_Vmrievh_1_e00a", aStdout="disk"),
                    exaMockCommand("/bin/test -e /bin/virsh"),
                    exaMockCommand("/bin/virsh list --all --name"),
                    exaMockCommand("/bin/test -e /bin/umount"),
                    exaMockCommand("/bin/test -e /bin/sed"),
                    exaMockCommand("/bin/umount /EXAVMIMAGES/GuestImages/exaxs2511-mwnhe.exadbxs.exadbxsdevvcn.oraclevcn.com"),
                    exaMockCommand(re.escape("/bin/sed -i '\\@/EXAVMIMAGES/GuestImages/exaxs2511-mwnhe.exadbxs.exadbxsdevvcn.oraclevcn.com@d' /etc/fstab")),
                    exaMockCommand("/bin/rmdir /EXAVMIMAGES/GuestImages/exaxs2511-mwnhe.exadbxs.exadbxsdevvcn.oraclevcn.com"),
                    exaMockCommand("/sbin/brctl show", aStdout=_tgtHostBridges),
                    exaMockCommand(re.escape("/bin/grep -r \"source bridge=\" /etc/libvirt/qemu/*.xml |  /bin/sed 's/.*<source bridge=\\(.*\\)\\/>.*/\\1/' | /bin/tr -d \"\\'\" | /bin/tr -d \"\\\"\""), aStdout=_tgtHostVMBridges)
                ],
                [
                    exaMockCommand(re.escape("/bin/grep -r \"source bridge=\" /etc/libvirt/qemu/*.xml |  /bin/sed 's/.*<source bridge=\\(.*\\)\\/>.*/\\1/' | /bin/tr -d \"\\'\" | /bin/tr -d \"\\\"\""), aStdout=_tgtHostVMBridges),
                    exaMockCommand("/sbin/brctl show", aStdout=_tgtHostBridges),
                    exaMockCommand("/bin/test -e /bin/grep"),
                    exaMockCommand(re.escape("/usr/local/bin/ipconf -conf-add 2>&1 | /bin/grep -q 'Unknown option: conf-add'"), aRc=1),
                    exaMockCommand("/opt/exadata_ovm/vm_maker --remove-bridge vmeth205"),
                    exaMockCommand("/usr/sbin/vm_maker --list-domains"),
                    exaMockCommand(re.escape("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*bondeth*")),
                    exaMockCommand(re.escape("/usr/bin/rm -f /etc/sysconfig/network-scripts/ifcfg-*bondeth*"))
                ],
                [
                    exaMockCommand("/usr/local/bin/imageinfo --node-type", aStdout="KVMHOST"),
                    exaMockCommand("/bin/virsh list --all --name", aStdout="dummy.us.oracle.com"),
                    exaMockCommand("/sbin/edvutil lsedvnode | /bin/grep state", aStdout="state: ONLINE"),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/GuestImages", aStdout="dummy.us.oracle.com"),
                    exaMockCommand(re.escape("/bin/ls /EXAVMIMAGES/GuestImages/dummy.us.oracle.com/vm*.xml")),
                    exaMockCommand("/bin/ls /dev/exc/gcv_Vm1234_1_abcd", aRc=1),
                    exaMockCommand("/bin/test -e /bin/virsh"),
                    exaMockCommand("/bin/virsh domiflist dummy.us.oracle.com", aStdout=_tgtVMBridges),
                    exaMockCommand("/bin/test -e /bin/ls"),
                    exaMockCommand(re.escape("/bin/ls /etc/sysconfig/network-scripts/ifcfg-vmeth0*:205"),
                        aStdout="/etc/sysconfig/network-scripts/ifcfg-vmeth0.102:205"),
                    exaMockCommand("/bin/test -e /sbin/brctl"),
                    exaMockCommand("/sbin/brctl show", aStdout=_tgtHostBridges),
                    exaMockCommand("/bin/rpm -q bondmonitor", aStdout="bondmonitor"),
                    exaMockCommand("mkdir -p /EXAVMIMAGES/GuestImages/dummy.us.oracle.com/snapshots")
                ]
            ],
            _sourceDom0: [
                [
                    exaMockCommand("/bin/test -e /bin/virsh"),
                    exaMockCommand("/bin/virsh domiflist scaqab10adm01vm08.us.oracle.com", aStdout=_tgtVMBridges),
                    exaMockCommand("/bin/test -e /bin/ls"),
                    exaMockCommand(re.escape("/bin/ls /etc/sysconfig/network-scripts/ifcfg-vmeth0*:205"),
                        aStdout="/etc/sysconfig/network-scripts/ifcfg-vmeth0.102:205"),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/GuestImages/scaqab10adm01vm08.us.oracle.com/vmbondeth0.1239.xml"),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/GuestImages/scaqab10adm01vm08.us.oracle.com/vmbondeth0.1240.xml"),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/GuestImages/scaqab10adm01vm08.us.oracle.com/scaqab10adm01vm08.us.oracle.com.xml"),
                    exaMockCommand(re.escape("/bin/ls /EXAVMIMAGES/GuestImages/scaqab10adm01vm08.us.oracle.com/vmeth*.xml")),
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 scaqab10adm07.us.oracle.com"),
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01.us.oracle.com"),
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01.us.oracle.com"),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "action": "moveSanityCheck",
            "vm_name": _vmName,            
            "target_dom0_name": _targetDom0,
            "source_dom0_name": _sourceDom0,
            "new_admin_ip": "77.10.15.10",
            "new_admin_hostname": "jesandov-test-vm",
            "new_admin_domainname": "us.oracle.com",
        }

        #Execute the clucontrol function
        _exascale = ebCluExaScale(self.mGetClubox())
        with patch("exabox.ovm.cluexascale.ebCluExaScale.mGetGcvDevicePath",
                   return_value="gcv_Vm1234_1_abcd"):
            _exascale.mPerformVmMove(_options)

    def test_validate_volumes_positive(self):

        _volume_device_attached_vm = (
            "Block /dev/exc/system_Vm53942_1_9044\n"
            "Block /dev/exc/u01_Vm53942_1_8044\n"
        )

        self.mGetContext().mSetConfigOption('enable_validate_volumes', "True")

        #Mock commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/opt/exadata_ovm/vm_maker --list --disk --domain scaqab10client01vm08.us.oracle.com", aStdout=_volume_device_attached_vm),
                    exaMockCommand("/opt/exadata_ovm/vm_maker --list --disk --domain scaqab10client02vm08.us.oracle.com", aStdout=_volume_device_attached_vm), 
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _exacloudPath = os.path.abspath(__file__)
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]

        _xmlToUse = os.path.join(self.mGetUtil().mGetOutputDir(), "sample_validate_volumes.xml")
        _xmlOriginal = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/sample_validate_volumes.xml")

        shutil.copyfile(_xmlOriginal, _xmlToUse)
        self.mGetClubox().mSetPatchConfig(_xmlToUse)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "serviceSubType": "exadbxs",
            "clusterType": "blockstorage",            
            "client_hostname": "scaqab10client01vm08.us.oracle.com",
            "edvvolume": "system_Vm53942_1_9044",
        }

        _clucommandhandler = CommandHandler(self.mGetClubox())

        ebLogInfo("Running success scenario where we are checking a specific volume is attached to the domU")
        _clucommandhandler.mHandlerValidateVolumes(_options)

         #Init new Args
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "serviceSubType": "exadbxs",
            "clusterType": "blockstorage",            
            "client_hostname": "scaqab10client01vm08.us.oracle.com",
            "edvvolume": "",
        }

        ebLogInfo("Running success scenario where we are checking for the all the volumes to be attached to the domU")
        _clucommandhandler.mHandlerValidateVolumes(_options)

    def test_validate_volumes_negative_01(self):

        _volume_device_attached_vm = (
            "Block /dev/exc/system_Vm53942_1_9044\n"
            "Block /dev/exc/gcv_Vm53942_1_b60b\n"
            "Block /dev/exc/u01_Vm53942_1_8044\n"
        )

        self.mGetContext().mSetConfigOption('enable_validate_volumes', "True")

        #Mock commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/opt/exadata_ovm/vm_maker --list --disk --domain scaqab10client01vm08.us.oracle.com", aStdout=_volume_device_attached_vm),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _exacloudPath = os.path.abspath(__file__)
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]

        _xmlToUse = os.path.join(self.mGetUtil().mGetOutputDir(), "sample_validate_volumes.xml")
        _xmlOriginal = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/sample_validate_volumes.xml")

        shutil.copyfile(_xmlOriginal, _xmlToUse)
        self.mGetClubox().mSetPatchConfig(_xmlToUse)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "serviceSubType": "exadbxs",
            "clusterType": "blockstorage",            
            "client_hostname": "scaqab10client01vm08.us.oracle.com",
            "edvvolume": "system_Vm53942_1_9047",
        }

        _clucommandhandler = CommandHandler(self.mGetClubox())

        ebLogInfo("Running failure scenario where we are checking a specific volume is not attached to the domU")
        with self.assertRaises(ExacloudRuntimeError):
            _clucommandhandler.mHandlerValidateVolumes(_options)

    def test_validate_volumes_negative_02(self):

        _volume_device_attached_vm_wrong = (
            "Block /dev/exc/system_Vm53942_1_9044\n"
            "Block /dev/exc/gcv_Vm53942_1_b60b\n"
            "Block /dev/exc/u01_Vm53942_1_8040\n"
        )

        self.mGetContext().mSetConfigOption('enable_validate_volumes', "True")

        #Mock commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/opt/exadata_ovm/vm_maker --list --disk --domain scaqab10client01vm08.us.oracle.com", aStdout=_volume_device_attached_vm_wrong),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _exacloudPath = os.path.abspath(__file__)
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]

        _xmlToUse = os.path.join(self.mGetUtil().mGetOutputDir(), "sample_validate_volumes.xml")
        _xmlOriginal = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/sample_validate_volumes.xml")

        shutil.copyfile(_xmlOriginal, _xmlToUse)
        self.mGetClubox().mSetPatchConfig(_xmlToUse)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "serviceSubType": "exadbxs",
            "clusterType": "blockstorage",            
            "client_hostname": "scaqab10client01vm08.us.oracle.com",
            "edvvolume": "",
        }
        
        _clucommandhandler = CommandHandler(self.mGetClubox())

        ebLogInfo("Running failure scenario where we are checking for the all the volumes to be attached to the domU")
        with self.assertRaises(ExacloudRuntimeError):
            _clucommandhandler.mHandlerValidateVolumes(_options)

    def test_validate_volumes_disabled(self):

        _dom0 = "scaqab10adm01.us.oracle.com"
        _domU = "scaqab10client01vm08.us.oracle.com"
        _edvVolume = "system_Vm53942_1_9047"

        _exacloudPath = os.path.abspath(__file__)
        _exacloudPath = _exacloudPath[0: _exacloudPath.rfind("exacloud")+8]

        _xmlToUse = os.path.join(self.mGetUtil().mGetOutputDir(), "sample_validate_volumes.xml")
        _xmlOriginal = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/sample_validate_volumes.xml")

        shutil.copyfile(_xmlOriginal, _xmlToUse)
        self.mGetClubox().mSetPatchConfig(_xmlToUse)

        _options = self.mGetPayload()
        _options.jsonconf = {
            "serviceSubType": "exadbxs",
            "clusterType": "blockstorage",            
            "client_hostname": "",
            "edvvolume": "",
        }

        #Mock commands
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/opt/exadata_ovm/vm_maker"),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        
        self.mGetContext().mSetConfigOption('enable_validate_volumes', "False")
        _clucommandhandler = CommandHandler(self.mGetClubox())
        _clucommandhandler.mHandlerValidateVolumes(_options)
        

if __name__ == '__main__':
    unittest.main(warnings='ignore')


# end of file
