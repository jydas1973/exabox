import os
import json
import unittest
import copy
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.vmcontrol import exaBoxOVMCtrl, ebVgLifeCycle
import warnings
from ast import literal_eval
from exabox.core.Context import get_gcontext
from unittest.mock import patch

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
"""

_xmList2 = """Name                                        ID   Mem VCPUs      State   Time(s)
Domain-0                                     0  8746     4     r----- 2145201.6
"""

_guestImages = """scaqab10adm01vm01.us.oracle.com
scaqab10adm01vm07.us.oracle.com
scaqab10adm01vm03.us.oracle.com
scaqab10client01vm02.us.oracle.com
scaqab10client01vm08.us.oracle.com
abcd#43
scaqab10client02vm08.us.oracle.com"""


class testOptions(object): pass

class ebTestexaBoxVMCMD(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestexaBoxVMCMD, self).setUpClass(aGenerateDatabase=True,aUseOeda=True)
        warnings.filterwarnings("ignore")

    def setUp(self):
        self.mGetClubox().mRegisterVgComponents()

    
    @patch("exabox.ovm.clucontrol.getHVInstance")
    def test_vmcmd_vm_start(self, aMockHVInstance):
        get_gcontext().mSetConfigOption('vm_handler','virsh')

        # Mock VM is down
        aMockHVInstance.return_value.mGetDomains.return_value = []
        mockCommands = {
                            self.mGetRegexDom0(): [
                                [
                                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                                ],
                                [
                                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                                    exaMockCommand("xm list", aStdout=_xmList, aPersist=True),
                                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages, aPersist=True),
                                    exaMockCommand("/opt/exadata_ovm/exadata.img.domu_maker start-domain", aRc=0, aPersist=True),
                                    exaMockCommand("xm create /EXAVMIMAGES/GuestImages", aRc=0, aPersist=True),
                                ],
                            ],
                            self.mGetRegexVm(): [
                               [
                                   exaMockCommand("ip addr show.*", aRc=0),
                                   
                               ]
                            ],
                            self.mGetRegexLocal(): [
                               [
                                   exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aRc=0),
                                   exaMockCommand("/bin/echo EXIT | /usr/bin/nc scaqab10adm01nat08.us.oracle.com 22", aRc=0)
                               ],
                               [
                                   exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aRc=0),
                                   exaMockCommand("/bin/echo EXIT | /usr/bin/nc scaqab10adm01nat08.us.oracle.com 22", aRc=0),
                               ]
                            ]
                       }

        self.mPrepareMockCommands(mockCommands)
        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()
        _options.jsonconf['vms'] = ['_all_']

        _options.vmid = 'scaqab10client01vm08.us.oracle.com'
        _options.vmcmd = 'start'
        _options.debug = '1'
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()


    @patch("exabox.ovm.clucontrol.getHVInstance")
    def test_vmcmd_vm_stop(self, aMockHVInstance):
        get_gcontext().mSetConfigOption('vm_handler','virsh')

        # VM is up and showing
        aMockHVInstance.return_value.mGetDomains.return_value = ["scaqab10client01vm08.us.oracle.com"]

        mockCommands = {
                           self.mGetRegexDom0(): [
                                [
                                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aRc=0),
                                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                                ],
                                [
                                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                                    exaMockCommand("xm list", aStdout=_xmList),
                                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages, aPersist=True),
                                    exaMockCommand("xm shutdown", aRc=0, aPersist=True),
                                    exaMockCommand("xm list", aStdout=_xmList2),
                                    exaMockCommand("/bin/test -e /etc/xen/auto/scaqab10client01vm08.us.oracle.com.cfg", aRc=0, aPersist=True),
                                    exaMockCommand("/bin/unlink /etc/xen/auto/scaqab10client01vm08.us.oracle.com.cfg", aRc=0, aPersist=True)
                                ],
                           ],
                           self.mGetRegexLocal(): [
                                [
                                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aRc=0),
                                    exaMockCommand("/bin/echo EXIT | /usr/bin/nc scaqab10adm01nat08.us.oracle.com 22", aRc=0)
                                ],
                           ]
                       }


        self.mPrepareMockCommands(mockCommands)
        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()
        _options.jsonconf['vms'] = ['_all_']

        _options.vmid = 'scaqab10client01vm08.us.oracle.com'
        _options.vmcmd = 'shutdown'
        _options.debug = '1'
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()

    @patch("exabox.ovm.clucontrol.getHVInstance")
    def test_vmcmd_vm_bounce(self, aMockHVInstance):
        get_gcontext().mSetConfigOption('vm_handler','virsh')

        # VM is up and showing
        aMockHVInstance.return_value.mGetDomains.return_value = ["scaqab10client01vm08.us.oracle.com"]

        mockCommands = {
                           self.mGetRegexDom0(): [
                                [
                                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aRc=0),
                                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                                ],
                                [
                                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                                    exaMockCommand("xm list", aStdout=_xmList),
                                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages, aPersist=True),
                                    exaMockCommand("xm shutdown", aRc=0, aPersist=True),
                                    exaMockCommand("xm list", aStdout=_xmList2),
                                    exaMockCommand("/bin/test -e /etc/xen/auto/scaqab10client01vm08.us.oracle.com.cfg", aRc=0, aPersist=True),
                                    exaMockCommand("/bin/unlink /etc/xen/auto/scaqab10client01vm08.us.oracle.com.cfg", aRc=0, aPersist=True)
                                ],
                           ],
                           self.mGetRegexLocal(): [
                                [
                                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aRc=0),
                                    exaMockCommand("/bin/echo EXIT | /usr/bin/nc scaqab10adm01nat08.us.oracle.com 22", aRc=0)
                                ],
                           ]
                       }


        self.mPrepareMockCommands(mockCommands)
        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()
        _options.jsonconf['vms'] = ['_all_']

        _options.vmid = 'scaqab10client01vm08.us.oracle.com'
        _options.vmcmd = 'bounce'
        _options.debug = '1'
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()

    @patch("exabox.ovm.clucontrol.getHVInstance")
    def test_vmcmd_vm_stop_vmmaker_already_shutdown(self,aMockHVInstance):

        # No VM listed, already down
        aMockHVInstance.return_value.mGetDomains.return_value = []
        aMockHVInstance.return_value.stopDomU.return_value = 0x411
        get_gcontext().mSetConfigOption('vm_handler','vm_maker')
        mockCommands = {
                           self.mGetRegexDom0(): [
                                [
                                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aRc=0),
                                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: KVMHOST", aPersist=True)
                                ],
                                [
                                    exaMockCommand("vm_maker --list|grep running", aStdout=""),
                                ]
                           ],
                           self.mGetRegexLocal(): [
                                [
                                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aRc=0),
                                    exaMockCommand("/bin/echo EXIT | /usr/bin/nc scaqab10adm01nat08.us.oracle.com 22", aRc=0)
                                ],
                           ]
                       }


        self.mPrepareMockCommands(mockCommands)
        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()
        _options.jsonconf['vms'] = ['_all_']

        _options.vmid = 'scaqab10client01vm08.us.oracle.com'
        _options.vmcmd = 'shutdown'
        _options.debug = '1'
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()
        self.assertEqual(_rc, 0)

    @patch("exabox.ovm.clucontrol.getHVInstance")
    def test_vmcmd_vm_start_vmmaker_vm_already_running(self, aMockHVInstance):

        # Mock is already up
        aMockHVInstance.return_value.mGetDomains.return_value = ["scaqab10client01vm08.us.oracle.com"]
        get_gcontext().mSetConfigOption('vm_handler','vm_maker')
        mockCommands = {
                            self.mGetRegexDom0(): [
                                [
                                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aRc=0),
                                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: KVMHOST", aPersist=True)
                                ],
                                [
                                    exaMockCommand("vm_maker --list|grep running", aStdout="scaqab10client01vm08.us.oracle.com(81)       : running"),
                                ]
                            ],
                           self.mGetRegexLocal(): [
                                [
                                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aRc=0),
                                    exaMockCommand("/bin/echo EXIT | /usr/bin/nc scaqab10adm01nat08.us.oracle.com 22", aRc=0)
                                ],
                           ]
                       }


        self.mPrepareMockCommands(mockCommands)
        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()
        _options.jsonconf['vms'] = ['_all_']

        _options.vmid = 'scaqab10client01vm08.us.oracle.com'
        _options.vmcmd = 'start'
        _options.debug = '1'
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()
        self.assertNotEqual(_rc, 0)
    
    @patch("exabox.ovm.clucontrol.getHVInstance")
    def test_vmcmd_console_history(self, aMockHVInstance):

        get_gcontext().mSetConfigOption('vm_handler','vm_maker')
        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()
        _options.jsonconf['vms'] = ['_all_']

        _options.vmid = 'scaqab10client01vm08.us.oracle.com'
        _options.vmcmd = 'console_history'
        _options.debug = '1'
        cluctrl.mSetOptions(_options)
        with patch('exabox.ovm.clucontrol.exaBoxNode.mIsConnectable', return_value=False):
            _rc = cluctrl.mHandlerVmCmd()
            self.assertNotEqual(_rc, 0)

    @patch("exabox.ovm.clucontrol.getHVInstance")
    def test_vmcmd_vm_force_stop(self, aMockHVInstance):
        get_gcontext().mSetConfigOption('vm_handler','virsh')

        # VM is up and showing
        aMockHVInstance.return_value.mGetDomains.return_value = ["scaqab10client01vm08.us.oracle.com"]

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aRc=0),
                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aStdout="Node type: DOM0", aPersist=True)
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("xm list", aStdout=_xmList),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages, aPersist=True),
                    exaMockCommand("xm list", aStdout=_xmList),
                    exaMockCommand("xm destroy", aRc=0, aPersist=True),
                ],
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aRc=0),
                    exaMockCommand("/bin/echo EXIT | /usr/bin/nc scaqab10adm01nat08.us.oracle.com 22", aRc=0)
                ],
            ]
        }

        self.mPrepareMockCommands(mockCommands)
        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()
        _options.jsonconf['vms'] = ['_all_']

        _options.vmid = 'scaqab10client01vm08.us.oracle.com'
        _options.vmcmd = 'force_shutdown'
        _options.debug = '1'
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()
        self.assertEquals(_rc, 0)

    @patch("exabox.ovm.clucontrol.getHVInstance")
    def test_vmcmd_vm_force_stop_vmmaker_kvm(self, aMockHVInstance):
        get_gcontext().mSetConfigOption('vm_handler','vm_maker')

        # VM is up and showing
        aMockHVInstance.return_value.mGetDomains.return_value = ["scaqab10client01vm08.us.oracle.com"]
        aMockHVInstance.return_value.mDestroyVM.return_value = 0

        mockCommands = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aRc=0),
                ],
            ]
        }

        self.mPrepareMockCommands(mockCommands)
        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()
        _options.jsonconf['vms'] = ['_all_']

        _options.vmid = 'scaqab10client01vm08.us.oracle.com'
        _options.vmcmd = 'force_shutdown'
        _options.debug = '1'
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()
        self.assertEqual(_rc, 0)

    @patch("exabox.ovm.clucontrol.getHVInstance")
    def test_vmcmd_vm_force_stop_vmmaker_already_shutdown(self,aMockHVInstance):
        # No VM listed, already down
        aMockHVInstance.return_value.mGetDomains.return_value = []
        aMockHVInstance.return_value.mDestroyVM.return_value = 1  # won't be called
        get_gcontext().mSetConfigOption('vm_handler','vm_maker')
        mockCommands = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aRc=1),
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aRc=1),
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aRc=1),
                    exaMockCommand("/bin/ping -c 1 scaqab10adm01nat08.us.oracle.com", aRc=1),
                ],
            ]
        }

        self.mPrepareMockCommands(mockCommands)
        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()
        _options.jsonconf['vms'] = ['_all_']

        _options.vmid = 'scaqab10client01vm08.us.oracle.com'
        _options.vmcmd = 'force_shutdown'
        _options.debug = '1'
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()
        self.assertEqual(_rc, 0)


if __name__ == "__main__":
    unittest.main()
