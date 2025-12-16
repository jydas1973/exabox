#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_vmcontrol.py /main/11 2025/09/30 13:23:58 remamid Exp $
#
# tests_vmcontrol.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_vmcontrol.py
#
#    DESCRIPTION
#      Unit test cases for the file $EC_ROOT/exabox/ovm/clucontrol.py
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    remamid     09/24/25 - Add unittest for bugs 38347575,38390358
#    avimonda    09/06/25 - Bug 38205634 - OCI: EXACC: SOFTRESETEXACCVMNODE
#                           FAILS ON EXACLOUD WITH "ERROR WHILE
#                           MULTIPROCESSING(PROCESS TIMEOUT)"
#    gparada     03/23/23 - 35029440 Remove mCollectKernelMsg no longer used
#                           (Xen is not used anymore)
#    naps        01/24/22 - Fix 33783397 - ping test failure.
#    aypaul      09/05/21 - Creation
#

import os, re
import json
import unittest
import copy
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.vmcontrol import exaBoxOVMCtrl, ebVgLifeCycle
from exabox.ovm.clucontrol import exaBoxCluCtrl
import warnings
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
from ast import literal_eval
import time
 
cmd0 = "/bin/test -e /bin/ls"
cmd1 = "/bin/test -e /usr/bin/ls"
cmd2 = "/bin/ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..." 
cmd3 = "/bin/test -e /usr/bin/chmod"
cmd4 = "/bin/test -e /bin/chmod"
cmd5 = "/bin/chmod ug+x /var/opt/oracle/creg/grid"
cmd6 = "cat /var/opt/oracle/creg/grid/grid.ini | grep \"^sid\" | cut -d '=' -f 2"
op6 = "+ASM1"
cmd7 = "cat /var/opt/oracle/creg/grid/grid.ini | grep \"^oracle_home\" | cut -d '=' -f 2"
op7 = "/u01/app/19.0.0.0/grid"


cmdOutput1="""xen
00000000-0000-0000-0000-000000000000
"""

_xmList = """Name                                        ID   Mem VCPUs      State   Time(s)
Domain-0                                     0  8746     4     r----- 2145201.6
scaqab10adm01vm01.us.oracle.com              1 92163    10     -b---- 811282.1
scaqab10adm01vm03.us.oracle.com              2 92163    10     -b---- 495633.3
scaqab10client01vm08.us.oracle.com           8 92163    10     -b----  51637.6
scaqab10adm01vm07.us.oracle.com             11 92163    10     -b----  42935.3
scaqab10client01vm02.us.oracle.com           5 92163    10     -b---- 446566.6
abcd#43                                      3 92163    10     -b---- 446566.6
scaqab10client02vm01.us.oracle.com           4 92163    10     -b---- 811282.1
"""

_guestImages = """scaqab10adm01vm01.us.oracle.com
scaqab10adm01vm07.us.oracle.com
scaqab10adm01vm03.us.oracle.com
scaqab10client01vm02.us.oracle.com
scaqab10client01vm08.us.oracle.com
abcd#43
scaqab10client02vm08.us.oracle.com"""

vmCfg = """
acpi = 1  
apic = 1  
pae = 1  
builder = 'hvm'  
kernel = '/usr/lib/xen/boot/hvmloader'  
device_model = '/usr/lib/xen/bin/qemu-dm' 
cpuid = ['1:edx=xxxxxxxxxxxxxxxxxxx0xxxxxxxxxxxx']  
disk = ['file:/OVS/Repositories/6d015d4f722144b39a0d9ebd71ec464e/VirtualDisks/7078081698234e62ad77ab821ae9f4cf.img,xvda,w', 'file:/OVS/Repositories/6d015d4f722144b39a0d9ebd71ec464e/VirtualDisks/6748344e5d8142a382b13c237e15ae5d.img,xvdb,w', 'file:/OVS/Repositories/6d015d4f722144b39a0d9ebd71ec464e/VirtualDisks/50d2ba78739e49a9a8274040995cb749.img,xvdc,w', 'file:///EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/u02_extra.img,xvdd,w','file:///EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/21222032406_u01ext.img,xvde,w']  
memory = '65536'  
maxmem = '65536'  
OVM_simple_name = 'scaqab10adm01-016'  
name = 'scaqab10client01vm08.us.oracle.com'  
OVM_os_type = 'Oracle Linux 7'  
vcpus = 8  
maxvcpus = 68  
uuid = '6d015d4f722144b39a0d9ebd71ec464e'  
on_crash = 'coredump-restart'  
on_reboot = 'restart'  
serial = 'pty'  
keymap = 'en-us'  
vif = ['type=netfront,mac=00:16:3e:8c:76:99,bridge=vmbondeth0','type=netfront,mac=00:16:3e:7e:13:1e,bridge=vmbondeth1','type=netfront,mac=00:16:3e:80:be:99,bridge=vmeth1']  
timer_mode = 2  
ib_pfs = ['03:00.0']  
ib_pkeys = [{'pf':'03:00.0','port':'1','pkey':['0x2a10','0xa016',]},{'pf':'03:00.0','port':'2','pkey':['0x2a10','0xa016',]},]  
cpus = '12-19'
"""


statusOutput="""      NAME  STATE   CPU(sec) CPU(%)     MEM(k) MEM(%)  MAXMEM(k) MAXMEM(%) VCPUS NETS NETTX(k) NETRX(k) VBDS   VBD_OO   VBD_RD   VBD_WR  VBD_RSECT  VBD_WSECT SSID
  Domain-0 -----r   11436672    0.0    9165992    3.4    9437184       3.5     4    0        0        0    0        0        0        0          0          0    0
      NAME  STATE   CPU(sec) CPU(%)     MEM(k) MEM(%)  MAXMEM(k) MAXMEM(%) VCPUS NETS NETTX(k) NETRX(k) VBDS   VBD_OO   VBD_RD   VBD_WR  VBD_RSECT  VBD_WSECT SSID
scas22dv05 -----r    2307282    0.0   67112952   25.0   67112960      25.0    68    3 13275550   388794    5        0 13580252 66320424   52874816 1646573752    0
      NAME  STATE   CPU(sec) CPU(%)     MEM(k) MEM(%)  MAXMEM(k) MAXMEM(%) VCPUS NETS NETTX(k) NETRX(k) VBDS   VBD_OO   VBD_RD   VBD_WR  VBD_RSECT  VBD_WSECT SSID
scas22dv05 --b---     327925    0.0   52432888   19.5   52432896      19.5    68    3  2269155    77145    5        0  2883430  8095846   14887720  200219625    0
"""
xmInfoOP="""host                   : scas22adm05.us.oracle.com
release                : 4.1.12-124.40.6.3.el6uek.x86_64
version                : #2 SMP Mon Jul 27 20:10:45 PDT 2020
machine                : x86_64
nr_cpus                : 72
nr_nodes               : 2
cores_per_socket       : 18
threads_per_core       : 2
cpu_mhz                : 2294
hw_caps                : bfebfbff:2c100800:00000000:41707f00:77fefbff:00000000:00000021:000037ab
virt_caps              : hvm hvm_directio
total_memory           : 262010
free_memory            : 131462
free_cpus              : 0
xen_major              : 4
xen_minor              : 4
xen_extra              : .4OVM
xen_caps               : xen-3.0-x86_64 xen-3.0-x86_32p hvm-3.0-x86_32 hvm-3.0-x86_32p hvm-3.0-x86_64 
xen_scheduler          : credit
xen_pagesize           : 4096
platform_params        : virt_start=0xffff800000000000
xen_changeset          : 
xen_commandline        : placeholder dom0_mem=9G,max:9G dom0_max_vcpus=4 no-bootscrub loglvl=all guest_loglvl=error/all com1=115200,8n1 conring_size=1m console=com1 console_to_ring crashkernel=448M@128M xsave=1
cc_compiler            : gcc (GCC) 4.4.7 20120313 (Red Hat 4.4.7-18.0.7)
cc_compile_by          : mockbuild
cc_compile_domain      : us.oracle.com
cc_compile_date        : Wed Aug 26 10:23:59 PDT 2020
xend_config_format     : 4
"""

uptimeOutput="""
Name                                ID Uptime 
Domain-0                             0 136 days,  0:38:43
scas22dv0507m.us.oracle.com        171 30 days,  0:31:37
scas22dv0508m.us.oracle.com        259 6 days, 14:54:59
"""

class testOptions(object): pass

class ebTestexaBoxOVMCtrl(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestexaBoxOVMCtrl, self).setUpClass(aGenerateDatabase=True,aUseOeda=True)
        warnings.filterwarnings("ignore")

    def test_vcpuset(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxOVMCtrl.vcpuset.")

        listOfDom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        dom0Instance0Commands = [
                                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                                ]
        dom0Instance1Commands = [
                                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                                    exaMockCommand("xm list", aStdout=_xmList, aPersist=True),
                                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages, aPersist=True),
                                    exaMockCommand("domu_maker vcpu-set", aRc=0, aPersist=True)
                                ]

        mockCommands = {
                           self.mGetRegexDom0(): [dom0Instance0Commands,dom0Instance1Commands,dom0Instance0Commands,dom0Instance1Commands],
                           self.mGetRegexLocal(): [
                               [exaMockCommand("/bin/ping", aRc=0, aStdout="Node type: DOM0", aPersist=True)]
                           ]
                       }

        self.mPrepareMockCommands(mockCommands)
        currentOptions = testOptions()
        currentOptions.vcpuset = None
        currentNode = exaBoxNode(self.mGetContext())
        currentNode.mConnect(aHost=listOfDom0s[0])
        vmHandle = ebVgLifeCycle()
        vmHandle.mSetOVMCtrl(aCtx=self.mGetContext(), aNode=currentNode)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'vcpuset', aVMId="scaqab10client01vm01.us.oracle.com", aOptions=currentOptions), -65536)
        currentOptions.vcpuset = "8"
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'vcpuset', aVMId="scaqab10client01vm01.us.oracle.com", aOptions=currentOptions), 0x412)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'vcpuset', aVMId="scaqab10client02vm08.us.oracle.com", aOptions=currentOptions), 0x411)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'vcpuset', aVMId="scaqab10client01vm08.us.oracle.com", aOptions=currentOptions), 0)
        currentNode.mDisconnect()


    def test_mCreateVM_mDestroyVM(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxOVMCtrl.mCreateVM(),mDestroyVM().")

        listOfDom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        listOfDomUs = [domU for _, domU in self.mGetClubox().mReturnDom0DomUPair()]
        dom0Instance0Commands = [
                                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                                ]
        dom0Instance1Commands = [
                                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                                    exaMockCommand("xm list", aStdout=_xmList, aPersist=True),
                                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages, aPersist=True),
                                    exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker start-domain", aRc=0, aPersist=True),
                                    exaMockCommand("xm shutdown", aRc=0, aPersist=True),
                                    exaMockCommand("xm create /EXAVMIMAGES/GuestImages", aRc=0, aPersist=True),
                                    exaMockCommand("/bin/test -e /etc/xen/auto", aRc=0, aPersist=True),
                                    exaMockCommand("/bin/unlink /etc/xen/auto", aRc=0, aPersist=True),
                                    exaMockCommand("xm destroy", aRc=0, aPersist=True)
                                ]

        mockCommands = {
                           self.mGetRegexDom0(): [dom0Instance0Commands,dom0Instance1Commands,dom0Instance0Commands,dom0Instance1Commands],
                           self.mGetRegexLocal(): [
                               [exaMockCommand("/bin/ping", aRc=0, aStdout="Node type: DOM0", aPersist=True)]
                           ]
                       }

        self.mPrepareMockCommands(mockCommands)
        currentNode = exaBoxNode(self.mGetContext())
        currentNode.mConnect(aHost=listOfDom0s[0])
        vmHandle = ebVgLifeCycle()
        vmHandle.mSetOVMCtrl(aCtx=self.mGetContext(), aNode=currentNode)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'create', aVMId="scaqab10client01vm01.us.oracle.com"), 0x412)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'create', aVMId="scaqab10client01vm08.us.oracle.com"), 0x410)
        currentNode.mDisconnect()
        currentNode = exaBoxNode(self.mGetContext())
        currentNode.mConnect(aHost=listOfDom0s[1])
        vmHandle = ebVgLifeCycle()
        vmHandle.mSetOVMCtrl(aCtx=self.mGetContext(), aNode=currentNode)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'create', aVMId="scaqab10client02vm08.us.oracle.com"), -65536)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'destroy', aVMId="scaqab10client01vm08.us.oracle.com"), 0)
        currentNode.mDisconnect()
    
    def test_mShutdownVM(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxOVMCtrl.mShutdownVM().")

        listOfDom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        listOfDomUs = [domU for _, domU in self.mGetClubox().mReturnDom0DomUPair()]
        dom0Instance0Commands = [
                                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                                ]
        dom0Instance1Commands = [
                                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                                    exaMockCommand("xm list", aStdout=_xmList, aPersist=True),
                                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages, aPersist=True),
                                    exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker start-domain", aRc=0, aPersist=True),
                                    exaMockCommand("xm shutdown", aRc=0, aPersist=True),
                                    exaMockCommand("xm create /EXAVMIMAGES/GuestImages", aRc=0, aPersist=True),
                                    exaMockCommand("/bin/test -e *", aRc=0, aPersist=True),
                                    exaMockCommand("/bin/unlink /etc/xen/auto", aRc=0, aPersist=True),
                                    exaMockCommand("xm destroy", aRc=0, aPersist=True)
                                ]
        dom0Instance2Commands = [
                                    exaMockCommand("/bin/test -e *", aRc=0, aPersist=True),
                                    exaMockCommand("/bin/touch *", aRc=0, aPersist=True)
                                ]
        mockCommands = {
                           self.mGetRegexDom0(): [dom0Instance0Commands,dom0Instance1Commands,dom0Instance2Commands, dom0Instance0Commands,dom0Instance1Commands],
                           self.mGetRegexLocal(): [
                               [exaMockCommand("/bin/ping", aRc=0, aStdout="Node type: DOM0", aPersist=True)]
                           ]
                       }

        self.mPrepareMockCommands(mockCommands)
        currentNode = exaBoxNode(self.mGetContext())
        currentNode.mConnect(aHost=listOfDom0s[0])
        vmHandle = ebVgLifeCycle()
        vmHandle.mSetOVMCtrl(aCtx=self.mGetContext(), aNode=currentNode)
        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()
        _options.jsonconf['non_rolling_patching'] = True
        cluctrl.mSetOptions(_options)
        currentNode.mDisconnect()
        currentNode = exaBoxNode(self.mGetContext())
        currentNode.mConnect(aHost=listOfDom0s[1])
        vmHandle = ebVgLifeCycle()
        vmHandle.mSetOVMCtrl(aCtx=self.mGetContext(), aNode=currentNode)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'create', aVMId="scaqab10client01vm01.us.oracle.com"), 0x412)
        _start_time = time.time()
        vmHandle.mDispatchEvent(aCmd= 'shutdown', aOptions=_options, aVMId="scaqab10client01vm02.us.oracle.com")
        _stop_time = time.time()
        print(_stop_time-_start_time)
        self.assertLessEqual(_stop_time-_start_time, 400)
        currentNode.mDisconnect()

    def test_mRebootVM(self):

        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxOVMCtrl.mRebootVM().")
        listOfDom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        listOfDomUs = [domU for _, domU in self.mGetClubox().mReturnDom0DomUPair()]

        dom0Instance0Commands = [
                                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                                ]
        dom0Instance1Commands = [
                                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                                    exaMockCommand("xm list", aStdout=_xmList, aPersist=True),
                                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages, aPersist=True),
                                    exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker start-domain", aRc=0, aPersist=True),
                                    exaMockCommand("xm reboot", aRc=0, aPersist=True),
                                ]

        mockCommands = {
                           self.mGetRegexLocal(): [
                               [
                                    exaMockCommand(re.escape("/bin/echo EXIT | /usr/bin/nc scaqab10adm01nat08.us.oracle.com 22"), aRc=0, aPersist=True)
                               ]
                           ],
                           self.mGetRegexDom0(): [dom0Instance0Commands, dom0Instance1Commands],
                       }


        self.mPrepareMockCommands(mockCommands)

        currentNode = exaBoxNode(self.mGetContext())
        currentNode.mConnect(aHost=listOfDom0s[0])
        vm_handle = exaBoxOVMCtrl(aCtx=self.mGetContext(), aNode=currentNode)
        self.assertLessEqual(vm_handle.mRebootVM("scaqab10client01vm08.us.oracle.com", 1800, True), True)
        currentNode.mDisconnect()

    def test_status_info_vminfo_uptime(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxOVMCtrl.vmstatus and exaBoxOVMCtrl.info")

        dom0Instance0Commands = [
                                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                                ]
        dom0Instance1Commands = [
                                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages, aPersist=True),
                                    exaMockCommand("xentop -b -r  -i 1", aStdout=statusOutput, aPersist=True),
                                    exaMockCommand("xm list", aStdout=_xmList, aPersist=True),
                                    exaMockCommand("xm info", aStdout=xmInfoOP, aPersist=True),
                                    exaMockCommand("xm uptime", aStdout=uptimeOutput, aPersist=True)
                                ]

        mockCommands = {
                           self.mGetRegexDom0(): [dom0Instance0Commands,dom0Instance1Commands]
                       }

        self.mPrepareMockCommands(mockCommands)
        listOfDom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        currentNode = exaBoxNode(self.mGetContext())
        currentNode.mConnect(aHost=listOfDom0s[0])
        vmHandle = ebVgLifeCycle()
        vmHandle.mSetOVMCtrl(aCtx=self.mGetContext(), aNode=currentNode)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'status'), 0)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'info'), 0)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'vminfo', aVMId="scas22dv0507m.us.oracle.com"), -1)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'vminfo', aVMId="scaqab10client01vm08.us.oracle.com"), 0)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'uptime'), 0)

    def test_cleanup(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxOVMCtrl.cleanup.")

        dom0Instance0Commands = [
                                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                                ]
        dom0Instance1Commands = [
                                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                                    exaMockCommand("cat /EXAVMIMAGES/GuestImages", aStdout=vmCfg, aPersist=True),
                                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="/EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/vm.cfg", aPersist=True),
                                    exaMockCommand("ls /OVS/Repositories/", aStdout="5116b876b9f74c628dc20e2444bfd404  6d015d4f722144b39a0d9ebd71ec464e", aPersist=True),
                                    exaMockCommand("rm -rf /OVS/Repositories/", aRc=0, aPersist=True),
                                    exaMockCommand("xm list", aStdout=_xmList, aPersist=True)
                                ]

        mockCommands = {
                           self.mGetRegexDom0(): [dom0Instance0Commands,dom0Instance1Commands],
                           self.mGetRegexLocal(): [
                               [exaMockCommand("/bin/ping", aRc=0, aStdout="Node type: DOM0", aPersist=True)]
                           ]
                       }

        self.mPrepareMockCommands(mockCommands)

        listOfDom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        currentNode = exaBoxNode(self.mGetContext())
        currentNode.mConnect(aHost=listOfDom0s[0])
        vmHandle = ebVgLifeCycle()
        vmHandle.mSetOVMCtrl(aCtx=self.mGetContext(), aNode=currentNode)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'cleanup'), -65536)


    def test_mListVM(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxOVMCtrl.mListVM.")

        listOfDom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        listOfDomUs = [domU for _, domU in self.mGetClubox().mReturnDom0DomUPair()]
        dom0Instance0Commands = [
                                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                                ]
        dom0Instance1Commands = [
                                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                                    exaMockCommand("xm list", aStdout=_xmList, aPersist=True),
                                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages, aPersist=True)
                                ]

        mockCommands = {
                           self.mGetRegexDom0(): [dom0Instance0Commands,dom0Instance1Commands],
                       }

        self.mPrepareMockCommands(mockCommands)
        currentNode = exaBoxNode(self.mGetContext())
        currentNode.mConnect(aHost=listOfDom0s[0])
        vmHandle = ebVgLifeCycle()
        vmHandle.mSetOVMCtrl(aCtx=self.mGetContext(), aNode=currentNode)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'list'), 0)


    def test_mDeleteVM(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxOVMCtrl.mDeleteVM.")

        listOfDom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        listOfDomUs = [domU for _, domU in self.mGetClubox().mReturnDom0DomUPair()]
        dom0Instance0Commands = [
                                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                                ]
        dom0Instance1Commands = [
                                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                                    exaMockCommand("xm list", aStdout=_xmList, aPersist=True),
                                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages, aPersist=True),
                                    exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker remove-domain", aRc=0, aPersist=True)
                                ]

        mockCommands = {
                           self.mGetRegexDom0(): [dom0Instance0Commands,dom0Instance1Commands,dom0Instance0Commands,dom0Instance1Commands],
                           self.mGetRegexLocal(): [
                               [exaMockCommand("/bin/ping", aRc=0, aStdout="Node type: DOM0", aPersist=True)]
                           ]
                       }

        self.mPrepareMockCommands(mockCommands)
        currentNode = exaBoxNode(self.mGetContext())
        currentNode.mConnect(aHost=listOfDom0s[0])
        vmHandle = ebVgLifeCycle()
        vmHandle.mSetOVMCtrl(aCtx=self.mGetContext(), aNode=currentNode)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'delete', aVMId="scaqab10client01vm01.us.oracle.com"), 0x412)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'delete', aVMId="scaqab10client01vm08.us.oracle.com"), 0)
        currentNode.mDisconnect()


    def test_exaBoxOVMCtrl(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxOVMCtrl.exaBoxOVMCtrl().")

        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["vm_time_sleep_reboot"] = 10
        gContext.mSetConfigOptions(writableGConfigOptions)
        ebLogInfo("Value: {}".format(gContext.mGetConfigOptions()['vm_time_sleep_reboot']))

        dom0Instance0Commands = [
                                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                                ]
        dom0Instance1Commands = [
                                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                                    exaMockCommand("xm list", aStdout=_xmList, aPersist=True),
                                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages, aPersist=True)
                                ]

        mockCommands = {
                           self.mGetRegexDom0(): [dom0Instance0Commands,dom0Instance1Commands]
                       }

        #Check for aNode=None
        exaBoxOVMCtrl(aCtx=gContext)
        self.mPrepareMockCommands(mockCommands)
        for dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            currentNode = exaBoxNode(self.mGetContext())
            currentNode.mConnect(aHost=dom0)
            vmHandle = exaBoxOVMCtrl(aCtx=self.mGetContext(), aNode=currentNode)
            currentNode.mDisconnect()
            break

    def test_mPingHost(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxOVMCtrl.mPingHost().")

        listOfDom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        dom0Instance0Commands = [
                                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                                ]
        dom0Instance1Commands = [
                                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                                    exaMockCommand("xm list", aStdout=_xmList, aPersist=True),
                                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages, aPersist=True)
                                ]

        mockCommands = {
                           self.mGetRegexDom0(): [dom0Instance0Commands,dom0Instance1Commands,dom0Instance0Commands,dom0Instance1Commands],
                           self.mGetRegexLocal(): [
                               [exaMockCommand("/bin/ping", aRc=0, aStdout="Node type: DOM0", aPersist=True)]
                           ]
                       }

        self.mPrepareMockCommands(mockCommands)
        self.mGetContext().mSetRegEntry("ssh_post_fix", "True")
        currentNode = exaBoxNode(self.mGetContext())
        currentNode.mConnect(aHost=listOfDom0s[0])
        vmHandle = ebVgLifeCycle()
        vmHandle.mSetOVMCtrl(aCtx=self.mGetContext(), aNode=currentNode)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'ping', aVMId="scaqab10client01vm01.us.oracle.com"), 0x412)
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'ping', aVMId="scaqab10adm01vm01.us.oracle.com"), 0)
        self.mGetContext().mSetRegEntry("ssh_post_fix", "False")
        vmHandle.mSetOVMCtrl(aCtx=self.mGetContext(), aNode=currentNode)
        #TODO ping tests are not yet mocked with ssh_post_fix disabled.
        #Below vm may or may not exist. Hence lets not check for return value.
        vmHandle.mDispatchEvent(aCmd= 'ping', aVMId="scaqab10adm01vm01.us.oracle.com")
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'ping', aVMId="abcd#43"), 0x411)
        currentNode.mDisconnect()

    def test_mDumpOVSVMConfig(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxOVMCtrl.mDumpOVSVMConfig().")

        dom0Instance0Commands = [
                                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                                ]
        dom0Instance1Commands = [
                                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                                    exaMockCommand("cat /EXAVMIMAGES/GuestImages", aStdout=vmCfg, aPersist=True),
                                    exaMockCommand("xm list", aStdout=_xmList, aPersist=True),
                                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages, aPersist=True)
                                ]

        mockCommands = {
                           self.mGetRegexDom0(): [dom0Instance0Commands,dom0Instance1Commands],
                           self.mGetRegexLocal(): [
                               [exaMockCommand("/bin/ping", aRc=0, aStdout="Node type: DOM0", aPersist=True)]
                           ]
                       }

        self.mPrepareMockCommands(mockCommands)

        listOfDom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        currentOptions = testOptions()
        currentNode = exaBoxNode(self.mGetContext())
        currentNode.mConnect(aHost=listOfDom0s[0])
        vmHandle = ebVgLifeCycle()
        vmHandle.mSetOVMCtrl(aCtx=self.mGetContext(), aNode=currentNode)
        currentOptions.vmid = None
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'dumpovsvmcfg', aOptions=currentOptions), -65536)
        currentOptions.vmid = "scaqab10adm01vm03.us.oracle.com"
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'dumpovsvmcfg', aOptions=currentOptions), -65536)


    def test_mPatchOVSVMConfig(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxOVMCtrl.mPatchOVSVMConfig.")

        dom0Instance0Commands = [
                                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                                ]
        dom0Instance1Commands = [
                                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                                    exaMockCommand("cat /EXAVMIMAGES/GuestImages", aStdout=vmCfg, aPersist=True),
                                    exaMockCommand("cp /EXAVMIMAGES/GuestImages", aRc=0, aPersist=True),
                                    exaMockCommand("/bin/scp", aRc=0, aPersist=True),
                                    exaMockCommand("xm list", aStdout=_xmList, aPersist=True),
                                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages, aPersist=True)
                                ]

        mockCommands = {
                           self.mGetRegexDom0(): [dom0Instance0Commands,dom0Instance1Commands],
                           self.mGetRegexLocal(): [
                               [exaMockCommand("/bin/ping", aRc=0, aStdout="Node type: DOM0", aPersist=True)]
                           ]
                       }

        self.mPrepareMockCommands(mockCommands)
        listOfDom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        currentOptions = testOptions()
        currentNode = exaBoxNode(self.mGetContext())
        currentNode.mConnect(aHost=listOfDom0s[0])
        vmHandle = ebVgLifeCycle()
        vmHandle.mSetOVMCtrl(aCtx=self.mGetContext(), aNode=currentNode)
        currentOptions.vmid = None
        currentOptions.kvlist = None
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'patchovsvmcfg', aOptions=currentOptions), -65536)
        currentOptions.vmid = "scaqab10adm01vm03.us.oracle.com"
        currentOptions.kvlist = "maxmem=65536"
        self.assertEqual(vmHandle.mDispatchEvent(aCmd= 'patchovsvmcfg', aOptions=currentOptions), -65536)



    
    def test_mGetGridHome(self):

        ebLogInfo("Running unit test on exaBoxOVMCtrl.mGetGridHome().")
        i=0
        aRc_Value = [[0,0,0,0,0,0],[0,1,0,0,0,0],[0,0,0,1,0,0],[0,0,0,0,1,0],[0,0,0,0,0,1]]
        for i in range(len(aRc_Value)):
            _cmds = {
                self.mGetRegexVm(): [
                
                    [
                        exaMockCommand(re.escape(cmd0), aRc=aRc_Value[i][0], aPersist=True), 
                        exaMockCommand(re.escape(cmd1), aRc=aRc_Value[i][0], aPersist=True), 
                        exaMockCommand(re.escape(cmd2), aRc=aRc_Value[i][1], aPersist=True), 
                        exaMockCommand(re.escape(cmd3), aRc=aRc_Value[i][2], aPersist=True), 
                        exaMockCommand(re.escape(cmd4), aRc=aRc_Value[i][2], aPersist=True), 
                        exaMockCommand(re.escape(cmd5), aRc=aRc_Value[i][3], aPersist=True), 
                        exaMockCommand(re.escape(cmd6), aRc=aRc_Value[i][4], aStdout=op6 ,aPersist=True), 
                        exaMockCommand(re.escape(cmd7), aRc=aRc_Value[i][5], aStdout=op7 ,aPersist=True)


                    ]
                    
                ]

            }

            self.mPrepareMockCommands(_cmds)
            listOfDomUs = [domU for _, domU in self.mGetClubox().mReturnDom0DomUPair()]
            currentNode = exaBoxNode(self.mGetContext())
            currentNode.mConnect(aHost=listOfDomUs[0])
            _getgridhomeobj=exaBoxCluCtrl(aCtx=self.mGetContext(), aNode=currentNode)
            _getgridhomeobj.mGetGridHome(listOfDomUs[0])

    def test_mRebootVMCheck(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxOVMCtrl.mRebootVMCheck().")
        listOfDom0s = [dom0 for dom0, _ in self.mGetClubox().mReturnDom0DomUPair()]
        listOfDomUs = [domU for _, domU in self.mGetClubox().mReturnDom0DomUPair()]

        dom0Instance0Commands = [
                                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                                ]
        dom0Instance1Commands = [
                                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                                    exaMockCommand("xm list", aStdout=_xmList, aPersist=True),
                                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages, aPersist=True),
                                    exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker start-domain", aRc=0, aPersist=True),
                                    exaMockCommand("xm reboot", aRc=0, aPersist=True),
                                ]
 
        mockCommands = {
                            self.mGetRegexLocal(): [
                                [
                                    exaMockCommand("curl *", aRc=1, aStderr="Ncat: Connection refused", aPersist=True),
                                    exaMockCommand("echo *", aRc=1, aStderr="Ncat: Connection refused", aPersist=True)
                                ]
                            ],
                            self.mGetRegexDom0(): [dom0Instance0Commands, dom0Instance1Commands],
                        }

        self.mPrepareMockCommands(mockCommands)
        currentNode = exaBoxNode(self.mGetContext())
        currentNode.mConnect(aHost=listOfDom0s[0])
        _starttime = time.time()
        _timeout = 100
        vm_handle = exaBoxOVMCtrl(aCtx=self.mGetContext(), aNode=currentNode)
        self.assertLessEqual(vm_handle.mRebootVMCheck("scaqab10client01vm08.us.oracle.com", _starttime, _timeout), 1)
        currentNode.mDisconnect()

if __name__ == "__main__":
    unittest.main()
