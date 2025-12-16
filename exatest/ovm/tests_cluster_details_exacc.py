#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cluster_details_exacc.py /main/2 2023/11/21 09:21:41 ritikhan Exp $
#
# tests_domu_details_exacc.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_cluster_details_exacc.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      runs tests for cluster_details_exacc api
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ritikhan    11/03/23 - Enh 35405135 - VMCLUSTER PAYLOAD CREATION: HANDLE
#                           ALL VMS IN SHUT DOWN STATE SCENARIO
#    bthampi     07/13/23 - ENH 35573065- CREATE AN API TO GET CPU AND MEMORY  DETAILS OF VMS IN A CLUSTER
#    bthampi     07/13/23 - Creation
#
import unittest

from exabox.core.Context import get_gcontext
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo

from exabox.ovm.kvmvmmgr import ebKvmVmMgr
from exabox.ovm.xenvmmgr import ebXenVmMgr


class ebTestebKvmVmMgr(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestebKvmVmMgr, self).setUpClass(False, False)

    def test_mGetVMCPU_xen(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                 [exaMockCommand("/usr/sbin/xm li scaqab10client01vm08.us.oracle.com.*", aStdout="2\n")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)
             
            _ret = _xenmgr.mGetVMCpu(_domU,"CUR_CPU")
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("2" , _ret)
            break


    def test_mGetVMCPU_kvm(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                 [exaMockCommand("/usr/sbin/vm_maker --list --vcpu --domain scaqab10client01vm08.us.oracle.com.*", aStdout="scaqab10client01vm08.us.oracle.com. 2")]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mGetVMCpu(_domU,"CUR_CPU")
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("2" , _ret)
            break

    def test_mGetVMCPUFromConfig_kvm(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                 
                 [exaMockCommand("/usr/bin/xmllint --xpath /domain/vcpu/@current /etc/libvirt/qemu/scaqab10client01vm08.us.oracle.com.xml.*", aStdout="8\n" ),
                 exaMockCommand("/bin/test -e /etc/libvirt/qemu/scaqab10client01vm08.us.oracle.com.xml.*", aRc=0, aStdout="", aPersist=True)]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)
             
            _ret = _kvmmgr.mGetVMCPUFromConfig(_domU)
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("8" , _ret)
            break
    
    def test_mGetVMCPUFromConfig_xen(self):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                 
                 [exaMockCommand("/bin/grep -i \^'vcpus = ' /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/vm.cfg.*", aStdout="8\n" ),
                 exaMockCommand("/bin/test -e /EXAVMIMAGES/GuestImages/scaqab10client01vm08.us.oracle.com/vm.cfg", aRc=0, aStdout="", aPersist=True)]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)
             
            _ret = _xenmgr.mGetVMCPUFromConfig(_domU)
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("8" , _ret)
            break

    def test_mGetVmStatus_kvm(self):
        _cmds = {
            self.mGetRegexDom0(): [
                 
                 [exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/grep scaqab10client01vm08.us.oracle.com | awk '{ print $3; }'", aStdout="running" )]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _kvmmgr = ebKvmVmMgr(_hvAttributes)

            _ret = _kvmmgr.mGetVmStatus(_domU)
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("running" , _ret)
            break
    
    def test_mGetVmStatus_xen(self):
        _cmds = {
            self.mGetRegexDom0(): [
                 
                 [exaMockCommand("/usr/sbin/xm li | /bin/grep scaqab10client01vm08.us.oracle.com | awk '{ print $5; }'", aStdout="r-----" )]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():

            _hvAttributes={'hostname':_dom0}
            _xenmgr = ebXenVmMgr(_hvAttributes)
            
            _ret = _xenmgr.mGetVmStatus(_domU)
            if _ret is not None:
                _ret = str(_ret)
            self.assertEqual("r-----" , _ret)
            break
            
if __name__ == '__main__':
    unittest.main() 