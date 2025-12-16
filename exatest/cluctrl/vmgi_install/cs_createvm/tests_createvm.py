"""

 $Header: 

 Copyright (c) 2020, 2025, Oracle and/or its affiliates.

 NAME:
      tests_clucontrol_createvm.py - Unitest for CRS/DB related funcs in clucontrl

 DESCRIPTION:
      Run tests for createVM related function of clucontrol

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       avimonda 07/17/25 - Bug 38019086 - EXACS: PROVISIONING FAILED WITH
                           EXACLOUD ERROR CODE: 0 EXACLOUD : NETWORK TIME
                           PROTOCOL (NTP) TEST FAILED BEFORE INSTALL CLUSTER
       naps     08/14/24 - Bug 36949876 - X11 ipconf path changes.
       jfsaldan 09/04/23 - Bug 35759673 - EXACS:23.4.1:XEN:FILE SYSTEM
                           ENCRYPTION:SKIP U02 RESIZE IF ENCRYPTED AND NON-LVM
                           (XEN)
       naps     01/10/23 - Bug 34884579 - UT test updation for bridge deletion.
       jfsaldan 12/02/22 - Bug 34833579 - EXACS-MVM:CREATE VM CLUSTER FAILED IN
                           CREATEVM DUE TO UNABLE TO REMOVE STALE DUMMY BRIDGE
       ajayasin 01/08/22 - test case for stale bridge removal

    vgerard    07/28/20 - Creation of the file
"""

import unittest

import re
import io
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.ovm.csstep.cs_util import csUtil
from unittest.mock import patch
import warnings

class ebTestCluControlCreateVM(ebTestClucontrol):
    @classmethod
    def setUpClass(self):
        # Call ebTestClucontrol, to specify DB/OEDA
        super().setUpClass(True,True)
        warnings.filterwarnings("ignore", category=ResourceWarning)


    def setUp(self):
        # All tests will be per default in SingleVM / XEN
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = False
        self.mGetClubox()._exaBoxCluCtrl__shared_env = False
        self.mGetClubox().mSetUt(True)

    def test_doNothingInMultiVM(self):
        self.mGetClubox()._exaBoxCluCtrl__shared_env = True
        self.mGetClubox().mCleanupSingleVMNatBridge()
        # If no exception are thrown by SSH layer, it means function did nothing

    # Default XML is a Xen one
    def test_noLeftoverXen(self):
        #bridge not present = no cleanup
        _cmds = {
            self.mGetRegexDom0(): [[
                exaMockCommand(re.escape("""/sbin/ip addr show vmeth100"""),aStderr='Device "vmeth100" does not exist.',aRc=1)
            ]]
        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mCleanupSingleVMNatBridge()
       
    def test_LeftoverXen(self):
        #bridge not present = no cleanup
        _cmds = {
            self.mGetRegexDom0(): [[
                exaMockCommand(re.escape("""/sbin/ip addr show vmeth100"""),aStdout="""
    37: vmeth100: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP
    link/ether 46:76:90:5e:e6:6c brd ff:ff:ff:ff:ff:ff
    inet 169.254.200.1/30 brd 169.254.200.3 scope global vmeth100
       valid_lft forever preferred_lft forever
    inet6 fe80::4476:90ff:fe5e:e66c/64 scope link
       valid_lft forever preferred_lft forever"""),
                exaMockCommand(re.escape("""/opt/exadata_ovm/exadata.img.domu_maker remove-bridge-dom0 vmeth100 -force""")) 
            ]]
        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mCleanupSingleVMNatBridge()

    def test_noLeftoverKVM(self):
        # Override KVM default variable
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        #bridge not present = no cleanup
        _cmds = {
            self.mGetRegexDom0(): [[
                exaMockCommand(re.escape("""/sbin/ip addr show vmeth200"""),aStderr='Device "vmeth200" does not exist.',aRc=1)
            ]]
        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mCleanupSingleVMNatBridge()

    def test_LeftoverKVM(self):
        # Override KVM default variable
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        #bridge not present = no cleanup
        _cmds = {
            self.mGetRegexDom0(): [[
                exaMockCommand(re.escape("""/sbin/ip addr show vmeth200"""),aStdout="""
    37: vmeth200: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP
    link/ether 46:76:90:5e:e6:6c brd ff:ff:ff:ff:ff:ff
    inet 169.254.200.1/30 brd 169.254.200.3 scope global vmeth100
       valid_lft forever preferred_lft forever
    inet6 fe80::4476:90ff:fe5e:e66c/64 scope link
       valid_lft forever preferred_lft forever"""),
                exaMockCommand(re.escape("/opt/exadata_ovm/vm_maker --remove-bridge vmeth200"))
            ]]
        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox().mCleanupSingleVMNatBridge()

    def test_mFetchBridges(self):
        # Override KVM default variable
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        #bridge not present = no cleanup
        _cmds = {
            self.mGetRegexDom0(): [[
               exaMockCommand("/sbin/brctl show*",aStdout="vmbondeth0.432\n vmbondeth1.406\n",aRc=0),
                exaMockCommand("/usr/bin/virsh dumpxml",aStderr="error: failed to get domain \n",aRc=0),
                exaMockCommand("/bin/grep -r \"source bridge\" /EXAVMIMAGES/GuestImages/*",aStdout="vmbondeth0.432\n vmbondeth1.406\n",aRc=0)
            ]]
        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _csu = csUtil()
        _bridges_out = _csu.mFetchBridges(_ebox)
        _bridges_exp = {'scaqab10adm01.us.oracle.com': ['vmbondeth0.432', 'vmbondeth1.406'], 'scaqab10adm02.us.oracle.com': ['vmbondeth0.432', 'vmbondeth1.406']}
        #_csu.mDeleteBridges(_ebox,_bridges_exp)
        assert _bridges_out == _bridges_exp

    def test_mDeleteBridges_no_stale_bridge(self):
        # Override KVM default variable
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        #bridge not present = no cleanup
        _cmds = {
            self.mGetRegexDom0(): [[
                exaMockCommand("/sbin/brctl show*",aStdout="bridge name     bridge id               STP enabled     interfaces/n vmbondeth0.43           can't get info No such device\n",aRc=0,aPersist=True),
                exaMockCommand("/bin/grep -r \"source bridge\" /etc/libvirt/qemu*",aStdout="vmbondeth0.434\n vmbondeth1.404\n",aRc=0,aPersist=True),
                exaMockCommand("/opt/exadata_ovm/vm_maker --remove-bridge",aRc=0,aPersist=True),
                exaMockCommand("/usr/sbin/vm_maker --list-domains",aRc=0),
                exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*",aRc=0),
                exaMockCommand("/usr/bin/rm -f /etc/sysconfig/network-scripts/ifcfg-*",aRc=0)
            ]]
        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _csu = csUtil()
        _bridges = {'scaqab10adm01.us.oracle.com': ['vmbondeth0.43', 'vmbondeth1.40'], 'scaqab10adm02.us.oracle.com': ['vmbondeth0.43', 'vmbondeth1.40']}
        _csu.mDeleteBridges(_ebox,_bridges)

    def test_mDeleteBridges_stale_bridge(self):
        # Override KVM default variable
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        #bridge not present = no cleanup
        _cmds = {
            self.mGetRegexDom0(): [[
                exaMockCommand("/bin/test -e /bin/grep",aRc=0,aPersist=True),
                exaMockCommand(re.escape("/usr/local/bin/ipconf -conf-add 2>&1 | /bin/grep -q 'Unknown option: conf-add'"),aRc=0,aPersist=True),
                exaMockCommand("/sbin/brctl show*",aStdout="bridge name     bridge id               STP enabled     interfaces\n vmbondeth0.432          8000.0010e0db65d3       no              bondeth0.432\n",aRc=0,aPersist=True),
                exaMockCommand("/bin/grep -r \"source bridge\" /etc/libvirt/qemu*",aStdout="vmbondeth0.434\n vmbondeth1.404\n",aRc=0,aPersist=True),
                exaMockCommand("/opt/exadata_ovm/vm_maker --remove-bridge",aRc=0,aPersist=True),
                exaMockCommand("/usr/sbin/vm_maker --list-domains",aRc=0),
                exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*",aRc=0),
                exaMockCommand("/usr/bin/rm -f /etc/sysconfig/network-scripts/ifcfg-*",aRc=0)
            ]]
        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _csu = csUtil()
        _bridges = {'scaqab10adm01.us.oracle.com': ['vmbondeth0.432', 'vmbondeth1.406'], 'scaqab10adm02.us.oracle.com': ['vmbondeth0.432', 'vmbondeth1.406']}
        _csu.mDeleteBridges(_ebox,_bridges)
 
    def test_mDeleteBridges_stale_bridge_failed(self):
        # Override KVM default variable
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        #bridge not present = no cleanup
        _cmds = {
            self.mGetRegexDom0(): [[
                exaMockCommand("/bin/test -e /bin/grep",aRc=0,aPersist=True),
                exaMockCommand(re.escape("/usr/local/bin/ipconf -conf-add 2>&1 | /bin/grep -q 'Unknown option: conf-add'"),aRc=0,aPersist=True),
                exaMockCommand("/sbin/brctl show*",aStdout="bridge name     bridge id               STP enabled     interfaces\n vmbondeth0.432          8000.0010e0db65d3       no              bondeth0.432\n",aRc=0,aPersist=True),
                exaMockCommand("/bin/grep -r \"source bridge\" /etc/libvirt/qemu*",aStdout="vmbondeth0.434\n vmbondeth1.404\n",aRc=0,aPersist=True),
                exaMockCommand("/opt/exadata_ovm/vm_maker --remove-bridge",aRc=1, aPersist=True, aStdout="Stdout example\n", aStderr="Stderr example\n"),
                exaMockCommand("/usr/sbin/vm_maker --list-domains",aRc=0),
                exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*",aRc=0),
                exaMockCommand("/usr/bin/rm -f /etc/sysconfig/network-scripts/ifcfg-*",aRc=0)
            ]]
        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _csu = csUtil()
        _bridges = {'scaqab10adm01.us.oracle.com': ['vmbondeth0.432', 'vmbondeth1.406'], 'scaqab10adm02.us.oracle.com': ['vmbondeth0.432', 'vmbondeth1.406']}
        _csu.mDeleteBridges(_ebox,_bridges)
 
    def test_mDeleteBridges_stale_bridge_used_by_other_vm(self):
        # Override KVM default variable
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        #bridge not present = no cleanup
        _cmds = {
            self.mGetRegexDom0(): [[
                exaMockCommand("/bin/test -e /bin/grep",aRc=0,aPersist=True),
                exaMockCommand(re.escape("/usr/local/bin/ipconf -conf-add 2>&1 | /bin/grep -q 'Unknown option: conf-add'"),aRc=0,aPersist=True),
                exaMockCommand("/sbin/brctl show*",aStdout="bridge name     bridge id               STP enabled     interfaces\n vmbondeth0.432          8000.0010e0db65d3       no              bondeth0.432\n",aRc=0,aPersist=True),
                exaMockCommand("/bin/grep -r \"source bridge\" /etc/libvirt/qemu*",aStdout="vmbondeth0.432\n vmbondeth1.406\n",aRc=0,aPersist=True),
                exaMockCommand("/opt/exadata_ovm/vm_maker --remove-bridge",aRc=0,aPersist=True),
                exaMockCommand("/usr/sbin/vm_maker --list-domains",aRc=0),
                exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*",aRc=0),
                exaMockCommand("/usr/bin/rm -f /etc/sysconfig/network-scripts/ifcfg-*",aRc=0)
            ]]
        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _csu = csUtil()
        _bridges = {'scaqab10adm01.us.oracle.com': ['vmbondeth0.432', 'vmbondeth1.406'], 'scaqab10adm02.us.oracle.com': ['vmbondeth0.432', 'vmbondeth1.406']}
        _csu.mDeleteBridges(_ebox,_bridges)

    def test_mDeleteStaleDummyBridge_nostale_bridge(self):
        # Override KVM default variable
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        #bridge not present = no cleanup
        _cmds = {
            self.mGetRegexDom0(): [[
                exaMockCommand("/bin/test -e /bin/df"),
                exaMockCommand("/bin/test -e /bin/lsblk"),
                exaMockCommand("/bin/df --local --output=target,source,fstype,size,avail --block-size=1"),
                exaMockCommand("/bin/lsblk -rno TYPE devtmpfs", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE devtmpfs", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE tmpfs", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE tmpfs", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE tmpfs", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE tmpfs", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/mapper/VGExaDb-LVDbSys1", aStdout="lvm"),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/mapper/VGExaDb-LVDbVar1", aStdout="lvm"),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/mapper/VGExaDb-LVDbHome", aStdout="lvm"),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/md24p1", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/mapper/VGExaDb-LVDbTmp", aStdout="lvm"),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/mapper/VGExaDb-LVDbExaVMImages", aStdout="lvm"),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/md24p2", aStdout="disk"),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/mapper/VGExaDb-LVDbVarLog", aStdout="lvm"),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/mapper/VGExaDb-LVDbVarLogAudit", aStdout="lvm"),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/exc/gcv_Vm3131_1_9552", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/exc/gcv_Vm3430_1_94cc", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/exc/gcv_Vm8170_1_ff24", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/exc/gcv_Vm2719_1_d895", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/exc/gcv_Vm7749_1_e5aa", aStdout=""),
                exaMockCommand("/bin/test -e /bin/virsh"),
                exaMockCommand("/bin/virsh list --all --name"),
                exaMockCommand("/bin/test -e /bin/umount"),
                exaMockCommand("/bin/test -e /bin/sed"),
                exaMockCommand("/bin/test -e /bin/rmdir"),
                exaMockCommand("/bin/test -e /bin/grep",aRc=0,aPersist=True),
                exaMockCommand(re.escape("/usr/local/bin/ipconf -conf-add 2>&1 | /bin/grep -q 'Unknown option: conf-add'"),aRc=0,aPersist=True),
                exaMockCommand("/sbin/brctl show*",aStdout="bridge name	bridge	id	STP	enabled	interfaces\nvmeth200	8000.e2780d6a24f9	no	eth200\nvmeth201	8000.da8b18988a21	no	eth201\n",aRc=0,aPersist=True),
                exaMockCommand("/bin/grep -r \"source bridge=\" /etc/libvirt/qemu/*",aStdout="vmeth200\n vmeth201\n",aRc=0,aPersist=True),
                exaMockCommand("/opt/exadata_ovm/vm_maker --remove-bridge",aRc=0,aPersist=True),
                exaMockCommand("/usr/sbin/vm_maker --list-domains",aRc=0),
                exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*",aRc=0),
                exaMockCommand("/usr/bin/rm -f /etc/sysconfig/network-scripts/ifcfg-*",aRc=0)
            ],
            [
                exaMockCommand("/bin/test -e /bin/grep",aRc=0,aPersist=True),
                exaMockCommand(re.escape("/opt/exadata_ovm/exadata.img.domu_makers/ipconf -conf-add 2>&1 | /bin/grep -q 'Unknown option: conf-add'"),aRc=0,aPersist=True),
                exaMockCommand("/sbin/brctl show*",aStdout="bridge name	bridge	id	STP	enabled	interfaces\nvmeth200	8000.e2780d6a24f9	no	eth200\nvmeth201	8000.da8b18988a21	no	eth201\n",aRc=0,aPersist=True),
                exaMockCommand("/bin/grep -r \"source bridge=\" /etc/libvirt/qemu/*",aStdout="vmeth200\n vmeth201\n",aRc=0,aPersist=True),
                exaMockCommand("/opt/exadata_ovm/vm_maker --remove-bridge",aRc=0,aPersist=True),
                exaMockCommand("/usr/sbin/vm_maker --list-domains",aRc=0),
                exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*",aRc=0),
                exaMockCommand("/usr/bin/rm -f /etc/sysconfig/network-scripts/ifcfg-*",aRc=0)
            ]
            ]
        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _csu = csUtil()
        _csu.mDeleteStaleDummyBridge(_ebox)
 
    def test_mDeleteStaleDummyBridge_stale_bridge(self):
        # Override KVM default variable
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        _filesystems = \
"""Mounted on                                                                     Filesystem                          Type      Size Avail
/dev                                                                           devtmpfs                            devtmpfs  811273265152  811273265152
/dev/shm                                                                       tmpfs                               tmpfs    1622587473920 1622587387904
/run                                                                           tmpfs                               tmpfs     811293122560  811213860864
/sys/fs/cgroup                                                                 tmpfs                               tmpfs     811293122560  811293122560
/                                                                              /dev/mapper/VGExaDb-LVDbSys1        xfs        16001269760    4325986304
/var                                                                           /dev/mapper/VGExaDb-LVDbVar1        xfs         2042626048    1866186752
/home                                                                          /dev/mapper/VGExaDb-LVDbHome        xfs         4190109696    4126920704
/boot                                                                          /dev/md24p1                         xfs         7633580032    7467855872
/tmp                                                                           /dev/mapper/VGExaDb-LVDbTmp         xfs         3116367872    3059650560
/EXAVMIMAGES                                                                   /dev/mapper/VGExaDb-LVDbExaVMImages xfs      7583345672192 7512868319232
/boot/efi                                                                      /dev/md24p2                         vfat         266336256     261107712
/var/log                                                                       /dev/mapper/VGExaDb-LVDbVarLog      xfs        19222495232    7051493376
/var/log/audit                                                                 /dev/mapper/VGExaDb-LVDbVarLogAudit xfs          968884224     816783360
/EXAVMIMAGES/GuestImages/xsdb6-3642.exacp10.jboduvcn.oraclevcn.com             /dev/exc/gcv_Vm3131_1_9552          xfs        34254880768   33982091264
/EXAVMIMAGES/GuestImages/nodehostr042-7157.exacp10.jboduvcn.oraclevcn.com      /dev/exc/gcv_Vm3430_1_94cc          xfs        34254880768   33982091264
/EXAVMIMAGES/GuestImages/nodehostr052-4018.exacp10.jboduvcn.oraclevcn.com      /dev/exc/gcv_Vm8170_1_ff24          xfs        34254880768   33982091264
/EXAVMIMAGES/GuestImages/xsdb6-1391.exacp10.jboduvcn.oraclevcn.com             /dev/exc/gcv_Vm2719_1_d895          xfs        34254880768   33982091264
/EXAVMIMAGES/GuestImages/rlaunch-09jfg2-9327.exacsx8mtest.bemeng.oraclevcn.com /dev/exc/gcv_Vm7749_1_e5aa          xfs        34254880768   33982091264
/run/user/0                                                                    tmpfs                               tmpfs     164007649280  164007649280
"""
        _domus = \
"""rlaunch-09jfg2-9327.exacsx8mtest.bemeng.oraclevcn.com
xsdb6-1391.exacp10.jboduvcn.oraclevcn.com
nodehostr052-4018.exacp10.jboduvcn.oraclevcn.com
"""
        #bridge not present = no cleanup
        _cmds = {
            self.mGetRegexDom0(): [[
                exaMockCommand("/bin/test -e /bin/df"),
                exaMockCommand("/bin/test -e /bin/lsblk"),
                exaMockCommand("/bin/df --local --output=target,source,fstype,size,avail --block-size=1", aStdout=_filesystems),
                exaMockCommand("/bin/test -e /bin/virsh"),
                exaMockCommand("/bin/lsblk -rno TYPE devtmpfs", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE devtmpfs", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE tmpfs", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE tmpfs", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE tmpfs", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE tmpfs", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/mapper/VGExaDb-LVDbSys1", aStdout="lvm"),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/mapper/VGExaDb-LVDbVar1", aStdout="lvm"),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/mapper/VGExaDb-LVDbHome", aStdout="lvm"),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/md24p1", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/mapper/VGExaDb-LVDbTmp", aStdout="lvm"),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/mapper/VGExaDb-LVDbExaVMImages", aStdout="lvm"),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/md24p2", aStdout="disk"),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/mapper/VGExaDb-LVDbVarLog", aStdout="lvm"),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/mapper/VGExaDb-LVDbVarLogAudit", aStdout="lvm"),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/exc/gcv_Vm3131_1_9552", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/exc/gcv_Vm3430_1_94cc", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/exc/gcv_Vm8170_1_ff24", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/exc/gcv_Vm2719_1_d895", aStdout=""),
                exaMockCommand("/bin/lsblk -rno TYPE /dev/exc/gcv_Vm7749_1_e5aa", aStdout=""),
                exaMockCommand("/bin/virsh list --all --name", aStdout=_domus),
                exaMockCommand("/bin/test -e /bin/umount"),
                exaMockCommand("/bin/test -e /bin/sed"),
                exaMockCommand("/bin/umount /EXAVMIMAGES/GuestImages/xsdb6-3642.exacp10.jboduvcn.oraclevcn.com"),
                exaMockCommand(re.escape("/bin/sed -i '\\@/EXAVMIMAGES/GuestImages/xsdb6-3642.exacp10.jboduvcn.oraclevcn.com@d' /etc/fstab")),
                exaMockCommand("/bin/umount /EXAVMIMAGES/GuestImages/nodehostr042-7157.exacp10.jboduvcn.oraclevcn.com"),
                exaMockCommand(re.escape("/bin/sed -i '\\@/EXAVMIMAGES/GuestImages/nodehostr042-7157.exacp10.jboduvcn.oraclevcn.com@d' /etc/fstab")),
                exaMockCommand("/bin/test -e /bin/rmdir"),
                exaMockCommand("/bin/rmdir /EXAVMIMAGES/GuestImages/xsdb6-3642.exacp10.jboduvcn.oraclevcn.com"),
                exaMockCommand("/bin/rmdir /EXAVMIMAGES/GuestImages/nodehostr042-7157.exacp10.jboduvcn.oraclevcn.com"),
                exaMockCommand("/bin/test -e /bin/grep",aRc=0,aPersist=True),
                exaMockCommand(re.escape("/usr/local/bin/ipconf -conf-add 2>&1 | /bin/grep -q 'Unknown option: conf-add'"),aRc=0,aPersist=True),
                exaMockCommand("/sbin/brctl show*",aStdout="bridge name	bridge	id	STP	enabled	interfaces\nvmeth200	8000.e2780d6a24f9	no	eth200\nvmeth201	8000.da8b18988a21	no	eth201\nvmeth202	8000.da8b18988a21	no	eth202\n",aRc=0,aPersist=True),
                exaMockCommand("/bin/grep -r \"source bridge=\" /etc/libvirt/qemu/*",aStdout="vmeth200\n vmeth201\n",aRc=0,aPersist=True),
                exaMockCommand("/opt/exadata_ovm/vm_maker --remove-bridge",aRc=0,aPersist=True),
                exaMockCommand("/usr/sbin/vm_maker --list-domains",aRc=0),
                exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*",aRc=0),
                exaMockCommand("/usr/bin/rm -f /etc/sysconfig/network-scripts/ifcfg-*",aRc=0)
            ],
            [
                exaMockCommand("/bin/test -e /bin/grep",aRc=0,aPersist=True),
                exaMockCommand(re.escape("/opt/exadata_ovm/exadata.img.domu_makers/ipconf -conf-add 2>&1 | /bin/grep -q 'Unknown option: conf-add'"),aRc=0,aPersist=True),
                exaMockCommand("/sbin/brctl show*",aStdout="bridge name	bridge	id	STP	enabled	interfaces\nvmeth200	8000.e2780d6a24f9	no	eth200\nvmeth201	8000.da8b18988a21	no	eth201\nvmeth202	8000.da8b18988a21	no	eth202\n",aRc=0,aPersist=True),
                exaMockCommand("/bin/grep -r \"source bridge=\" /etc/libvirt/qemu/*",aStdout="vmeth200\n vmeth201\n",aRc=0,aPersist=True),
                exaMockCommand("/opt/exadata_ovm/vm_maker --remove-bridge",aRc=0,aPersist=True),
                exaMockCommand("/usr/sbin/vm_maker --list-domains",aRc=0),
                exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*",aRc=0),
                exaMockCommand(re.escape("/usr/local/bin/ipconf -conf-add 2>&1 | /bin/grep -q 'Unknown option: conf-add'"),aRc=0,aPersist=True),
                exaMockCommand("/usr/bin/rm -f /etc/sysconfig/network-scripts/ifcfg-*",aRc=0),
                # TAO
            ],
            ]
        }
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _csu = csUtil()
        _csu.mDeleteStaleDummyBridge(_ebox)

    def test_mIsRestartChronyDSuccessful_True(self):

        for dom0, domU in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexDomU(): [
                    [
                        exaMockCommand("test.*systemctl"),
                        exaMockCommand("systemctl is-active --quiet chronyd", aRc=1, aPersist=True),
                        exaMockCommand("systemctl restart chronyd", aRc=0, aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)
            _csu = csUtil()
            _ret = _csu.mIsRestartChronyDSuccessful(domU)
            self.assertEqual(_ret, True)
   
            _cmds = {
                self.mGetRegexDomU(): [
                    [
                        exaMockCommand("test.*systemctl"),
                        exaMockCommand("systemctl is-active --quiet chronyd", aRc=0, aPersist=True),
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)
            _csu = csUtil()
            _ret = _csu.mIsRestartChronyDSuccessful(domU)
            self.assertEqual(_ret, True)

    def test_mIsRestartChronyDSuccessful_False(self):

        for dom0, domU in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexDomU(): [
                    [
                        exaMockCommand("test.*systemctl"),
                        exaMockCommand("systemctl is-active --quiet chronyd", aRc=1, aPersist=True),
                        exaMockCommand("systemctl restart chronyd", aRc=1, aPersist=True)
                    ]
                ]
            }
            self.mPrepareMockCommands(_cmds)
            _csu = csUtil()
            _ret = _csu.mIsRestartChronyDSuccessful(domU)
            self.assertEqual(_ret, False)

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    @patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, io.StringIO("Network Time Protocol (NTP) ...FAILED (PRVG-1017)"), None))
    @patch('exabox.core.Node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    @patch('exabox.ovm.csstep.cs_util.csUtil.mIsRestartChronyDSuccessful', return_value=False) 
    def test_mHealthCheckClufy_PRVG_1017(self, mock_mIsRestartChronyDSuccessful, mock_mGetCmdExitStatus, mock_mExecuteCmd, mock_mGetOracleBaseDirectories):

        for dom0, domU in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexDomU(): [
                    [
                        exaMockCommand("/bin/test -e /bin/dbaascli"),
                        exaMockCommand("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'", aRc=0, aStdout="/u01/app/19.0.0.0/grid"),
                    ]
                ]
            }
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ebox._exaBoxCluCtrl__kvm_enabled = True 
        _csu = csUtil()
        with self.assertRaises(ExacloudRuntimeError) as cm:
            _csu.mHealthCheckClufy(_ebox)
        self.assertEqual(str(cm.exception), '\n************************************************EXACLOUD FATAL EXCEPTION BEGIN************************************************\n\nExacloud error code: 0\nExacloud error message: EXACLOUD : Network Time Protocol (NTP) test Failed before install cluster\n\n************************************************EXACLOUD FATAL EXCEPTION END**************************************************\n')

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=("/u01/app/19.0.0.0/grid", None, None))
    @patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, io.StringIO("Network Time Protocol (NTP) ...FAILED (PRVG-13606)"), None))
    @patch('exabox.core.Node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    def test_mHealthCheckClufy_PRVG_13606(self, mock_mGetCmdExitStatus, mock_mExecuteCmd, mock_mGetOracleBaseDirectories):

        for dom0, domU in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexDomU(): [
                    [
                        exaMockCommand("/bin/test -e /bin/dbaascli"),
                        exaMockCommand("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'", aRc=0, aStdout="/u01/app/19.0.0.0/grid"),
                    ]
                ]
            }
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ebox._exaBoxCluCtrl__kvm_enabled = True
        _csu = csUtil()
        with self.assertRaises(ExacloudRuntimeError) as cm:
            _csu.mHealthCheckClufy(_ebox)
        self.assertEqual(str(cm.exception), '\n************************************************EXACLOUD FATAL EXCEPTION BEGIN************************************************\n\nExacloud error code: 0\nExacloud error message: EXACLOUD : Network Time Protocol (NTP) test Failed before install cluster\n\n************************************************EXACLOUD FATAL EXCEPTION END**************************************************\n')

if __name__ == '__main__':
    unittest.main()
