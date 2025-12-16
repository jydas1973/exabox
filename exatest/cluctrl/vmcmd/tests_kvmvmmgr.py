"""

 $Header: 

 Copyright (c) 2020, 2024, Oracle and/or its affiliates.

 NAME:
      tests_kvmvmmgr.py - Unitest for kvmvmmgr.py module

 DESCRIPTION:
      Run tests for the methods of kvmvmmgr.py

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       bhpati   09/09/24 - EXACS: PROVISIONING FAILED WITH EXACLOUD ERROR CODE:
                           16 HYPERVISOR STOPPED ON DOM0.
       naps     03/07/22 - remove virsh layer dependency.

        ajayasin    17/06/20 - Creation of the file
"""

import unittest

from random import shuffle

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.ovm.kvmvmmgr import ebKvmVmMgr
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *

_vmid_out = """Id:             8
Name:           scaqae14dv0105.us.oracle.com
UUID:           3833d626-739c-45f7-9258-5e6a785540de
OS Type:        hvm
State:          running
CPU(s):         22
CPU time:       284268.3s
Max memory:     33554432 KiB
Used memory:    33554432 KiB
Persistent:     yes
Autostart:      disable
Managed save:   no
Security model: selinux
Security DOI:   0
Security label: system_u:system_r:svirt_t:s0:c186,c738 (permissive)
"""

class ebTestNode(ebTestClucontrol):

    def test_dom0Mem(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)

            _mem = _kvmmgr.getDom0FreeMem(aVirshMode=True)
            if _mem is not None:
                _mem = str(int(_mem))
            self.assertEqual("189440", _mem)
            break

    def test_dom0TotalMem(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand('/usr/sbin/vm_maker --list --memory | /bin/grep "Total OS memory"', aStdout="Total OS memory            : 385227 M")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)

            _mem = _kvmmgr.getDom0TotalMem()
            if _mem is not None:
                _mem = str(int(_mem))
            self.assertEqual("385227", _mem)
            break

    def test_KvmInfoRetryLogic(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                # 3 mConnect are done due to retry, hence 2 different arrays
                [exaMockCommand("virsh nodememstat.*free", aStdout="ERROR")],
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # first Dom0
        _kvmmgr = ebKvmVmMgr({'hostname':self.mGetClubox().mReturnDom0DomUPair()[0][0]})

        _mem = _kvmmgr.getDom0FreeMem(aVirshMode=True) #1s for Retry
        self.assertEqual(0, _mem)

    def test_getTotalVMs(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("'virsh list |grep running | wc -l ", aStdout="5")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)

            _vm = _kvmmgr.getTotalVMs()
            if _vm is not None:
                _vm = str(_vm)
            self.assertEqual("5", _vm)
            break

    def test_mRefreshDomUsOedacli(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("'vm_maker --list|grep running", aStdout="scaqae14dv0107.us.oracle.com(81)       : running")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)

            _kvmmgr.mRefreshDomUsOedacli()
            break

    def test_pingVMOedaCli(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("'vm_maker --list|grep running", aStdout="scaqae14dv0107.us.oracle.com(81)       : running")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.pingVMOedaCli(_domU)
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("1041", _ret)
            break


    def test_mGetDomUList(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/grep running.*", aStdout="scaqae14dv0107.us.oracle.com(16)       : running")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mGetDomUList()
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("('/usr/sbin/vm_maker --list-domains | /bin/grep running', ['scaqae14dv0107.us.oracle.com(16)       : running'])" , _ret)
            break
     
    def test_mGetDom0Info(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("virsh nodeinfo", aStdout="CPU model:           x86_64")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mGetDom0Info()
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("('virsh nodeinfo', ['CPU model:           x86_64'])", _ret)
            break
 
    def test_unimplemented(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("virsh nodeinfo", aStdout="CPU model:           x86_64")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
    
            try:
                _ret = _kvmmgr.mReadRemoteCfg()
            except :
                pass 
            try:
                _ret = _kvmmgr.mDumpOVSVMConfig("aVMName")
            except :
                pass 
            try:
                _ret = _kvmmgr.mPatchOVSVMConfig("aVMName")
            except :
                pass 
            try:
                _ret = _kvmmgr.mGetOVSVMConfig("aVMName")
            except :
                pass 
            try:
                _ret = _kvmmgr.mGetOVSVMList()
            except :
                pass 
            try:
                _ret = _kvmmgr.mReadRemoteAllCfg()
            except :
                pass 
            try:
                _ret = _kvmmgr.mPruneOVSRepo("aOptions")
            except :
                pass 

    def test_mRefreshDomUs(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/grep 'running'", aStdout="scaqae14dv0107.us.oracle.com(16)       : running")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mRefreshDomUs()
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("['scaqae14dv0107.us.oracle.com']" , _ret)
            break
  
    def test_mRefreshDomUsCfg(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqae14dv0102.us.oracle.com  scaqae14dv0104.us.oracle.com")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mRefreshDomUsCfg()
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("['scaqae14dv0102.us.oracle.com  scaqae14dv0104.us.oracle.com']" , _ret)
            break
            _ret = _kvmmgr.mGetDom0Logs()
            _ret = _kvmmgr.mGetUptime()

    def test_mGetVcpuList(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/grep running", aStdout="scaqae14dv0107.us.oracle.com(16)       : running"),
                    exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/grep running", aStdout="scaqae14dv0107.us.oracle.com(16)       : running"),
                    exaMockCommand("virsh vcpuinfo Name --pretty.*", aStdout=""),
                    exaMockCommand("virsh vcpuinfo scaqae14dv0107.us.oracle.com --pretty.*", aStdout="")
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mGetVcpuList()
            if _ret is not None:
                _ret = str(_ret)
            break
        _ret = _kvmmgr.mGetUptime()
        _ret = _kvmmgr.mVmConfigExist("sNode","aDomuName")

    def test_mGetDomains(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                 [exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/grep running.*", aStdout="scaqae14dv0107.us.oracle.com(81)       : running")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mGetDomains()
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("['scaqae14dv0107.us.oracle.com']" , _ret)
            break
 
    def test_mRetrieveVMID(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                 [exaMockCommand("/usr/sbin/vm_maker --list --domain scaqab10client01vm08.us.oracle.com --detail.*", aStdout=_vmid_out)]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mRetrieveVMID(_domU)
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("8" , _ret)
            break


    def test_mGetVMMemory(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                 [exaMockCommand("/usr/sbin/vm_maker --list --memory --domain scaqab10client01vm08.us.oracle.com.*", aStdout="scaqab10client01vm08.us.oracle.com. 128 128")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mGetVMMemory(_domU,"CUR_MEM")
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("128" , _ret)
            break
 
    def test_mGetVMMemory_2(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                 [exaMockCommand("virsh dominfo scaqab10client01vm08.us.oracle.com | grep 'Max memory' | awk '{ print $3/1024 }'", aStdout="8182")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mGetVMMemory(_domU,"MAX_MEM")
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("818" , _ret)
            break
 
    def test_mSetVMMemory(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                 [exaMockCommand("/opt/exadata_ovm/vm_maker --set --memory 32 --domain scaqab10client01vm08.us.oracle.com", aStdout="")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mSetVMMemory(_domU,"32")
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("0" , _ret)
            break
 
    def test_mNodeType(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                 [exaMockCommand("imageinfo | grep 'Node type:'", aStdout="Node type: KVMHOST")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mNodeType()
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("('KVMHOST', True, '00000000-0000-0000-0000-000000000000')" , _ret)
            break
 
    def test_mNodeType_2(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                 [exaMockCommand("imageinfo | grep 'Node type:'", aStdout="Node type: GUEST")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mNodeType()
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("('GUEST', False, None)" , _ret)
            break


    def test_vm_opertion(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                  exaMockCommand("/usr/sbin/vm_maker --list-domains", aStdout="scaqae14dv0107.us.oracle.com(16)       : running\n"),
                  exaMockCommand("/opt/exadata_ovm/vm_maker --start-domain /EXAVMIMAGES/conf/123-vm.xml", aStdout=""),
                  exaMockCommand("/opt/exadata_ovm/vm_maker --stop-domain 123 --force", aStdout=""),
                  exaMockCommand("/opt/exadata_ovm/vm_maker --remove-domain 123 --force", aStdout=""),
                  exaMockCommand("virsh nodecpustats", aStdout=""),
                  exaMockCommand("virsh nodeinfo", aStdout=""),
                  exaMockCommand("virsh destroy 123", aStdout=""),
                  exaMockCommand("/opt/exadata_ovm/vm_maker --reboot 123", aStdout=""),
                  exaMockCommand("/usr/sbin/vm_maker --list-domains", aStdout=""),
                  exaMockCommand("virsh nodememstats", aStdout=""),
                  exaMockCommand("/opt/exadata_ovm/vm_maker --stop-domain 123", aStdout=""),
                  exaMockCommand("/opt/exadata_ovm/vm_maker --stop-domain 123 --destroy", aStdout=""),
                  exaMockCommand("virsh detach-device 123  --file aFile", aStdout=""),
                  exaMockCommand("virsh attach-device 123  --file aFile --config", aStdout=""),
                  exaMockCommand("/usr/sbin/vm_maker --set --vcpu aVcpuset --domain 123", aStdout=""),
                  exaMockCommand("ls /EXAVMIMAGES/.* | xargs rm -f", aStdout=""),
                  exaMockCommand("virsh start 123", aStdout="")
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _kvmmgr.mLogListVms()
            _kvmmgr.mCreateVM("123")
            _kvmmgr.mDeleteVM("123")
            _kvmmgr.mStatus()
            _kvmmgr.mInfo()
            _kvmmgr.mDestroyVM("123")
            _kvmmgr.mVMInfo("123")
            _kvmmgr.mRebootVM("123")
            _kvmmgr.mShutdownVM("123")
            _kvmmgr.mUptime()
            _kvmmgr.mSetVcpus("123","aVcpuset")
            _kvmmgr.mAttachDevice("123","aFile")
            _kvmmgr.mDetachDevice("123","aFile")
            break

    def test_mStartVM(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("vm_maker --start-domain 123", aStdout="")
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mStartVM("123")
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("0" , _ret)
            break

    def test_mGetSysInfo(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                 [exaMockCommand("virsh sysinfo", aStdout="<sysinfo type='smbios'>\n<bios>\n<entry name='vendor'>American Megatrends Inc.</entry>\n<entry name='version'>51021000</entry>\n</bios>")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mGetSysInfo()
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("<sysinfo type='smbios'>\n<bios>\n<entry name='vendor'>American Megatrends Inc.</entry>\n<entry name='version'>51021000</entry>\n</bios>" , _ret)
            break

    def test_mReadRemoteXML(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/vm_maker --dumpxml.*", aStdout="")
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mReadRemoteXML(_dom0)
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("" , _ret)
            break

    def test_mDefineXMLToGuest(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                 [exaMockCommand("virsh define /etc/libvirt/qemu/scaqab10adm01.us.oracle.com.xml", aStdout="")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mDefineXMLToGuest("/etc/libvirt/qemu/scaqab10adm01.us.oracle.com.xml")
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("0" , _ret)
            break

    def test_mUnDefineXMLToGuest(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                 [exaMockCommand("virsh undefine /etc/libvirt/qemu/scaqab10adm01.us.oracle.com.xml", aStdout="")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mUnDefineXMLToGuest("/etc/libvirt/qemu/scaqab10adm01.us.oracle.com.xml")
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("0" , _ret)
            break

    def test_mGetHVStatus(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                    [
                        exaMockCommand("systemctl is-active libvirtd.service", aStdout="active"),
                        exaMockCommand("systemctl start libvirtd.service", aStdout="")
                     ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
                
            _ret = _kvmmgr.mGetHVStatus()
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("running" , _ret)
            break

    def test_test(self):
        assert(True)


def suite():
    """
    This method ensures the execution in the intended order of the tests.
    """
    suite = unittest.TestSuite()
    suite.addTest(ebTestNode('test_dom0Mem'))
    suite.addTest(ebTestNode('test_dom0TotalMem'))
    suite.addTest(ebTestNode('test_getTotalVMs'))
    suite.addTest(ebTestNode('test_KvmInfoRetryLogic'))
    suite.addTest(ebTestNode('test_mDefineXMLToGuest'))
    suite.addTest(ebTestNode('test_mGetDom0Info'))
    suite.addTest(ebTestNode('test_mGetDomains'))
    suite.addTest(ebTestNode('test_mGetDomUList'))
    suite.addTest(ebTestNode('test_mGetSysInfo'))
    suite.addTest(ebTestNode('test_mGetVcpuList'))
    suite.addTest(ebTestNode('test_mGetVMMemory'))
    suite.addTest(ebTestNode('test_mGetVMMemory_2'))
    suite.addTest(ebTestNode('test_mNodeType'))
    suite.addTest(ebTestNode('test_mNodeType_2'))
    suite.addTest(ebTestNode('test_mReadRemoteXML'))
    suite.addTest(ebTestNode('test_mRefreshDomUs'))
    suite.addTest(ebTestNode('test_mRefreshDomUsCfg'))
    suite.addTest(ebTestNode('test_mRefreshDomUsOedacli'))
    suite.addTest(ebTestNode('test_mRetrieveVMID'))
    suite.addTest(ebTestNode('test_mSetVMMemory'))
    suite.addTest(ebTestNode('test_mStartVM'))
    suite.addTest(ebTestNode('test_mUnDefineXMLToGuest'))
    suite.addTest(ebTestNode('test_pingVMOedaCli'))
    suite.addTest(ebTestNode('test_unimplemented'))
    suite.addTest(ebTestNode('test_vm_opertion'))
    suite.addTest(ebTestNode('test_mGetHVStatus'))
    # suite.addTest(ebTestNode('test_test'))
    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suite())
