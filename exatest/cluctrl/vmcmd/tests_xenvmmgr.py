"""

 $Header: 

 Copyright (c) 2020, 2024, Oracle and/or its affiliates.

 NAME:
      tests_xenvmmgr.py - Unitest for xenvmmgr.py module

 DESCRIPTION:
      Run tests for the methods of xenvmmgr.py

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
       bhpati   09/09/24 - EXACS: PROVISIONING FAILED WITH EXACLOUD ERROR CODE:
                           16 HYPERVISOR STOPPED ON DOM0.

        hnvenkat    05/04/20 - Creation of the file
"""

import unittest

from random import shuffle

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.ovm.xenvmmgr import ebXenVmMgr
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *

class ebTestNode(ebTestClucontrol):

    def test_dom0Mem(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("'xm info |grep \'free_memory\'", aStdout="free_memory            : 187091")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _mem = _xenmgr.getDom0FreeMem()
            if _mem is not None:
                _mem = str(_mem)
            self.assertEqual("187091", _mem)
            break

    def test_dom0TotalMem(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("'xm info |grep \'total_memory\'", aStdout="total_memory            : 765000")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _mem = _xenmgr.getDom0TotalMem()
            if _mem is not None:
                _mem = str(_mem)
            self.assertEqual("765000", _mem)
            break

    def test_XenInfoRetryLogic(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                # 3 mConnect are done due to retry, hence 2 different arrays
                [exaMockCommand("'xm info |grep \'free_memory\'", aStdout="ERROR", aRc=1)],
                [exaMockCommand("'xm info |grep \'free_memory\'", aStderr="STDERRonly", aRc=1)],
                [exaMockCommand("'xm info |grep \'free_memory\'", aStdout="free_memory            : 187091")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # first Dom0
        _xenmgr = ebXenVmMgr({'hostname':self.mGetClubox().mReturnDom0DomUPair()[0][0]})

        _mem = _xenmgr.getDom0FreeMem(aRetryTime=1) #1s for Retry
        self.assertEqual(187091, _mem)


    def test_XenInfo3FailedRetry(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                # Last correct value will not be hit, 0(existing semantics for failure) returned 
                [exaMockCommand("'xm info |grep \'free_memory\'", aStdout="ERROR", aRc=1)],
                [exaMockCommand("'xm info |grep \'free_memory\'", aStderr="STDERRonly", aRc=1)],
                [exaMockCommand("'xm info |grep \'free_memory\'", aStderr="STDERRonly", aRc=1)],
                [exaMockCommand("'xm info |grep \'free_memory\'", aStdout="free_memory            : 187091")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # first Dom0
        _xenmgr = ebXenVmMgr({'hostname':self.mGetClubox().mReturnDom0DomUPair()[0][0]})
        _mem = _xenmgr.getDom0FreeMem(aRetryTime=1) #1s for Retry

        self.assertEqual(0, _mem)


    def test_dom0TotalVMs(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("xm list -l | grep guest_os_type | wc -l", aStdout="4")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _vms = _xenmgr.getTotalVMs()
            self.assertEqual("4", _vms)
            break

    def test_mGetDomUList(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("xm list", aStdout="scas22dv0306m.us.oracle.com               1513 65539     8     r-----  25154.2")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _cmdstr, _xmlist = _xenmgr.mGetDomUList()
            self.assertEqual(_cmdstr, "xm list")
            for _xml in _xmlist:
                _xml = _xml.split()[0].strip()
                self.assertEqual(_xml, "scas22dv0306m.us.oracle.com")
            break 

    def test_mGetDom0Info(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("xm info", aStdout="xen_caps               : xen-3.0-x86_64 xen-3.0-x86_32p hvm-3.0-x86_32 hvm-3.0-x86_32p hvm-3.0-x86_64")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _cmdstr, _xminfo = _xenmgr.mGetDom0Info()
            self.assertEqual(_cmdstr, "xm info")
            for _xmi in _xminfo:
                _xmi = _xmi.split()[0].strip()
                self.assertEqual(_xmi, "xen_caps")
            break 

    def test_mGetDom0Logs(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("xm log", aStdout="[2020-05-04 21:33:10 268674] DEBUG (XendDomainInfo:3369) Check if cpu 4 is in cpus")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _cmdstr, _xmlog = _xenmgr.mGetDom0Logs()
            self.assertEqual(_cmdstr, "xm log")
            for _xml in _xmlog:
                _xml = _xml.split()[3].strip()
                self.assertEqual(_xml, "DEBUG")
            break 

    def test_mGetUptime(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("xm uptime", aStdout="scas22dv0306m.us.oracle.com       1513 21:53:53")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _cmdstr, _xmtime = _xenmgr.mGetUptime()
            self.assertEqual(_cmdstr, "xm uptime")
            for _xmt in _xmtime:
                _xmt = _xmt.split()[1].strip()
                self.assertEqual(_xmt, "1513")
            break 

    def test_mGetVcpuList(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("xm vcpu-list", aStdout="scas22dv0306m.us.oracle.com       1513    71     -   --p       0.0 12-19")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _cmdstr, _xmvcpu = _xenmgr.mGetVcpuList()
            self.assertEqual(_cmdstr, "xm vcpu-list")
            for _xmv in _xmvcpu:
                _xmv = _xmv.split()[2].strip()
                self.assertEqual(_xmv, "71")
            break 

    def test_mGetDomains(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("xm list | awk '{print $1,$2}' | grep com", aStdout="scas22dv0302m.us.oracle.com 1524")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _xmdom = _xenmgr.mGetDomains()
            for _xmd in _xmdom:
                _xmd = _xmd.split()[0].strip()
                self.assertEqual(_xmd, "scas22dv0302m.us.oracle.com")
            break 

    def test_mRetrieveVMID(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("xm li .* | grep .* | awk '{print $2}'", aStdout="1524")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _vmid = _xenmgr.mRetrieveVMID("scas22dv0302m.us.oracle.com")
            self.assertEqual(str(_vmid), "152")
            break 

    def test_mGetVMMemory(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("xm li .* | grep .* | awk '{ print $3 }'", aStdout="65539"),
                    exaMockCommand("xm li .* -l | grep '(maxmem' | tr -d ')' | awk '{ print $2 }'", aStdout="75536")
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _vmmem = _xenmgr.mGetVMMemory("scas22dv0302m.us.oracle.com", "CUR_MEM")
            self.assertEqual(str(_vmmem), "6553")
            _vmmem = _xenmgr.mGetVMMemory("scas22dv0302m.us.oracle.com", "MAX_MEM")
            self.assertEqual(str(_vmmem), "7553")
            break 

    def test_mNodeType(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _hypervisor, _dom0, _uuid = _xenmgr.mNodeType()
            self.assertEqual(_hypervisor, "xen")
            self.assertEqual(_dom0, False)
            self.assertEqual(_uuid, "00000000-0000-0000-0000-00000000000")
            break 

    def test_mRefreshDomUs(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("xm list", aStdout="scas22dv0302m.us.oracle.com               1525 65539     8     r-----    808.0")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _domus = _xenmgr.mRefreshDomUs()
            for _domu in _domus:
                self.assertEqual(_domu, "scas22dv0302m.us.oracle.com")
            break

    def test_mRefreshDomUsCfg(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scas22dv0302m.us.oracle.com  scas22dv0306m.us.oracle.com")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _domuscfg = _xenmgr.mRefreshDomUsCfg()
            for _domu in _domuscfg:
                self.assertEqual(_domu, "scas22dv0302m.us.oracle.com  scas22dv0306m.us.oracle.com")
                break
            break

    def test_mCreateVM(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker start-domain .*")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _xenmgr.mCreateVM("scas22dv0302m.us.oracle.com")
            break

    def test_mDeleteVM(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker remove-domain .*")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _xenmgr.mDeleteVM("scas22dv0302m.us.oracle.com")
            break

    def test_mLogListVms(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/.*") ,
                    exaMockCommand("xm list")
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _xenmgr.mLogListVms()
            break

    def test_mStatus(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("xentop -b -r  -i 1")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _xenmgr.mStatus()
            break

    def test_mInfo(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("xm info")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _xenmgr.mInfo()
            break

    def test_mVMInfo(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("xm list -l .*")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _xenmgr.mVMInfo("scas22dv0302m.us.oracle.com")
            break

    def test_mDestroyVM(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("xm destroy .*")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _xenmgr.mDestroyVM("scas22dv0302m.us.oracle.com")
            break

    def test_mStartVM(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("xm create /EXAVMIMAGES/GuestImages/.*", aStdout="0")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _rc = _xenmgr.mStartVM("scas22dv0302m.us.oracle.com")
            self.assertEqual(_rc, 0)
            break

    def test_mShutdownVM(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("xm shutdown .*")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _rc = _xenmgr.mShutdownVM("scas22dv0302m.us.oracle.com")
            break

    def test_mUptime(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("xm uptime")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _rc = _xenmgr.mUptime()
            break

    def test_mSetVcpus(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [exaMockCommand("domu_maker vcpu-set .*")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _rc = _xenmgr.mSetVcpus("scas22dv0302m.us.oracle.com", "10-20")
            break

    def test_mGetHVStatus(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("service xend status | grep running", aStdout="xend daemon (pid 222349) is running..."),
                    exaMockCommand("service xend start", aStdout="")
                    ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)

            _rc = _xenmgr.mGetHVStatus()
            self.assertEqual("running", _rc)
            break

if __name__ == '__main__':
    unittest.main()

