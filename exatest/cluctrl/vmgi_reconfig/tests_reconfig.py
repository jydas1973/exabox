#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/vmgi_reconfig/tests_reconfig.py /main/23 2025/06/26 18:22:18 jfsaldan Exp $
#
# tests_reconfig.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_reconfig.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    06/04/25 - ?Bug 37945713 - ADBD: OBSERVING WRONG PERMISSIONS
#                           IN /OPT/EXACLOUD DIRECTORY FOR FILES ATP.INI,
#                           NODES.JSON AND GET_CS_DATA.PY
#    prsshukl    05/12/23 - Bug 35366341 - Fix unittest failure
#    siyarlag    07/15/22 - 34362512: add test for scan resource
#    siyarlag    05/22/22 - 34169987: GARP env set
#    naps        03/06/22 - remove virsh layer dependency.
#    ffrrodri    07/13/21 - Bug 33111535: Remove update agent certs test cases
#    ffrrodri    02/08/21 - Enh 32460437: Add tests for arping check
#    jesandov    05/18/20 - Creation
#

import unittest
import io
import copy
import inspect
import json
from random import shuffle
import re
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import ebLogInfo
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from unittest.mock import patch

from exabox.ovm.atp import ebCluATPConfig

_vm_cfg_prev_list = """/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev1
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev2
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev3
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev4
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev5
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev6
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev7
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev8
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev9
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev10
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev11
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev12"""

class ebTestReconfig(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def test_000_setup_env(self):

        # Set up ATP environment
        self.mGetClubox().mSetExabm(True)
        self.mGetClubox().mSetIsATP(True)

        _atp = copy.deepcopy(self.mGetClubox().mCheckConfigOption('atp'))
        _atp.update(self.mGetPayload()['atp'])
        _atp['dbSystemOCID'] = "reconfig"
        self.mGetClubox().mGetCtx().mSetConfigOption('atp', _atp)

        self.mGetClubox().mSetATP(ebCluATPConfig(self.mGetPayload()))
 
    def test_001_node(self):

        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/sed --follow-symlinks -i .*UseDNS.*"),
                    exaMockCommand("/bin/sed --follow-symlinks -i .*UseDNS.*"),
                    exaMockCommand("/bin/echo.*UseDNS no.*"),
                    exaMockCommand("/sbin/service sshd restart")
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        self.mGetClubox().mAddUseDnsFlag()

    def test_002_dom0_xen(self):

        _xmList = self.mGetResourcesTextFile("cmd_xmlist.txt")
        _guestImages = self.mGetResourcesTextFile("cmd_guestlist.txt")
        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        #Create args structure
        _baseCmd = [

            exaMockCommand("/bin/mkdir -p /opt/exacloud/reconfig.*", aPersist=True),
            exaMockCommand("/bin/ls -la /opt/exacloud/reconfig.*", aRc=1, aPersist=True),
            exaMockCommand("/bin/touch /opt/exacloud/reconfig.*", aPersist=True),

            # Detect XEN
            exaMockCommand("imageinfo | grep 'Node type:'"),
            exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n"),
            exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),

            #Vmcontrol standard load
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
            exaMockCommand("xm list", aStdout=_xmList),
            exaMockCommand("scp .*", aPersist=True),

            #read of vmcfg
            exaMockCommand("xm list", aStdout=_xmList),
            exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*/vm.cfg", aStdout=_vmcfg),

            #save of vmcfg
            exaMockCommand("cp /EXAVMIMAGES/GuestImages/.*/vm.cfg /EXAVMIMAGES/GuestImages/.*/vm.cfg.*"),
            exaMockCommand("/bin/test -e .*", aRc=0,  aPersist=True),
            exaMockCommand("/bin/find /EXAVMIMAGES/GuestImages/.*/ -name 'vm.cfg.prev*' | /bin/xargs /bin/ls -t",aStdout=_vm_cfg_prev_list),
            exaMockCommand("/bin/test -e /bin/rm", aRc=0,  aPersist=True),
            exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev11"),
            exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev12"),
            exaMockCommand(".*mv \$vifListOld \$vifListNew.*"),

            #reconfig cmds apply bondeth0 vlan change
            exaMockCommand("/bin/test -e /etc/sysconfig/network-scripts/ifcfg-bondeth0.*", aPersist=True),
            exaMockCommand("/sbin/ifup bondeth0.*", aPersist=True),

            #reconfig cmds apply vmbondeth0 vlan change
            exaMockCommand("/bin/test -e /etc/sysconfig/network-scripts/ifcfg-vmbondeth0.*", aPersist=True),
            exaMockCommand("/sbin/ifup vmbondeth0.*", aPersist=True),

            #save changes of vm.cfg
            exaMockCommand("/bin/sed --follow-symlinks -i s/.*/.*/g /EXAVMIMAGES/GuestImages/.*/vm.cfg"),

            #ATP Relate command
            exaMockCommand("mkdir -p /opt/exacloud/network")

        ]

        _cmds = {
            self.mGetRegexDom0(): [],
        }

        _atpConnections = 3
        _stepConnections = 3 # 2 steps + 1 workdir

        for _ in range(0, len(self.mGetClubox().mReturnDom0DomUPair()) + _atpConnections + _stepConnections):
            _cmds[self.mGetRegexDom0()].append(_baseCmd)

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        _reconfig = self.mGetClubox().mGetFactoryPreprovReconfig().mCreateReconfig()

        _steps = {
            _reconfig.mExecuteReconfigDom0: [
                _reconfig.mReconfigDom0ChangeVifVlan,
                _reconfig.mReconfigDom0UpdateNetwork
            ]
        }
        _reconfig.mSetWaitSteps(_steps)
        _reconfig.mExecuteReconfig()

        #Build step tables
        for _step, _stepInfo in _reconfig.mGetStepRecord().items():

            _expectedSteps = list(map(lambda x: x.__name__, _steps[getattr(_reconfig, _step)]))
            _substepsNames =  list(map(lambda x: x.split("-")[0], _stepInfo['substeps'].keys()))

            for _substep in _substepsNames:
                self.assertTrue(_substep in _expectedSteps)

    def test_002_2_dom0_kvm(self):

        _kvmXml = self.mGetResourcesTextFile("kvm_guest.xml")

        _baseCmd = [

            # Base Reconfig
            exaMockCommand("/bin/mkdir -p .*", aPersist=True),
            exaMockCommand("/bin/ls -la .*", aRc=1, aPersist=True),
            exaMockCommand("/bin/touch .*", aPersist=True),

            # Detect KVM Envroment
            exaMockCommand("imageinfo | grep 'Node type:'", aStdout="Node type: KVMHOST"),

            # VLAN Change
            exaMockCommand("/bin/test -e .*", aRc=1),
            exaMockCommand("/usr/sbin/vm_maker --dumpxml .*", aStdout=_kvmXml),
            exaMockCommand("/bin/scp .*", aPersist=True),

            #reconfig cmds apply bondeth0 vlan change
            exaMockCommand("/bin/test -e /etc/sysconfig/network-scripts/ifcfg-bondeth0.*", aPersist=True),
            exaMockCommand("/sbin/ifup bondeth0.*", aPersist=True),

            #reconfig cmds apply vmbondeth0 vlan change
            exaMockCommand("/bin/test -e /etc/sysconfig/network-scripts/ifcfg-vmbondeth0.*", aPersist=True),
            exaMockCommand("/sbin/ifup vmbondeth0.*", aPersist=True),

            #ATP Relate command
            exaMockCommand("mkdir -p /opt/exacloud/network")

        ]

        _cmds = {
            self.mGetRegexDom0(): [],
        }

        _atpConnections = 3
        _stepConnections = 1

        for _ in range(0, len(self.mGetClubox().mReturnDom0DomUPair()) + _atpConnections + _stepConnections):
            _cmds[self.mGetRegexDom0()].append(_baseCmd)

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        _reconfig = self.mGetClubox().mGetFactoryPreprovReconfig().mCreateReconfig()
        _reconfig.mSetReconfigWorkdir(self.mGetUtil().mGetOutputDir())

        _steps = {
            _reconfig.mExecuteReconfigDom0: [
                _reconfig.mReconfigDom0ChangeVifVlan,
                _reconfig.mReconfigDom0UpdateNetwork
            ]
        }
        _reconfig.mSetWaitSteps(_steps)
        _reconfig.mExecuteReconfig()

        #Build step tables
        for _step, _stepInfo in _reconfig.mGetStepRecord().items():

            _expectedSteps = list(map(lambda x: x.__name__, _steps[getattr(_reconfig, _step)]))
            _substepsNames =  list(map(lambda x: x.split("-")[0], _stepInfo['substeps'].keys()))

            for _substep in _substepsNames:
                self.assertTrue(_substep in _expectedSteps)

    def test_002_domU_xen(self):

        _xmList = self.mGetResourcesTextFile("cmd_xmlist.txt")
        _guestImages = self.mGetResourcesTextFile("cmd_guestlist.txt")
        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _domUs = list(map(lambda x: x[1], self.mGetClubox().mReturnDom0DomUPair()))

        _domUBase = [

            # atp file creation
            exaMockCommand("[ ! -e /opt/exacloud ] && mkdir -p /opt/exacloud", aRc=0),
            exaMockCommand("/bin/scp /tmp/nodes_scaqab10client01vm08.us.oracle.com.ini /opt/exacloud/nodes.json", aRc=0),
            exaMockCommand("/bin/scp /tmp/nodes_scaqab10client02vm08.us.oracle.com.ini /opt/exacloud/nodes.json", aRc=0),
            exaMockCommand("test -e /bin/chmod", aRc=0),
            exaMockCommand("/bin/chmod 644 /opt/exacloud/nodes.json", aRc=0),
            exaMockCommand("[ ! -e /opt/exacloud ] && mkdir -p /opt/exacloud", aRc=0),
            exaMockCommand("/bin/scp /tmp/atp_scaqab10client01vm08.us.oracle.com.ini /opt/exacloud/atp.ini", aRc=0),
            exaMockCommand("/bin/scp /tmp/atp_scaqab10client02vm08.us.oracle.com.ini /opt/exacloud/atp.ini", aRc=0),
            exaMockCommand("test -e /bin/chmod", aRc=0),
            exaMockCommand("/bin/chmod 644 /opt/exacloud/atp.ini", aRc=0),

            #udev rules (client and backup)
            exaMockCommand("/bin/sed --follow-symlinks -i s/.*/.*/g.*70\-persistent\-net\.rules"),
            exaMockCommand("/bin/sed --follow-symlinks -i s/.*/.*/g.*70\-persistent\-net\.rules"),

            #/etc/ changes
            exaMockCommand("/bin/sed.*\/etc\/hosts"),
            exaMockCommand("/bin/sed.*\/etc\/resolv.conf"),
            exaMockCommand("/bin/sed.*\/etc\/hostname"),

            #ssh changes (client and backup)
            exaMockCommand("/bin/sed.*\/etc\/ssh\/sshd_config"),
            exaMockCommand("/bin/sed.*\/etc\/ssh\/sshd_config"),

            #sysconfig scripts
            exaMockCommand("/bin/sed.*\/etc\/sysconfig\/network"),

            #sysconfig scripts rule-bondeth0 (net + cidr)
            exaMockCommand("/bin/sed.*\/etc\/sysconfig\/network\-scripts\/rule\-bondeth0"),

            #sysconfig network route (net + gateway)
            exaMockCommand("/bin/sed.*\/etc\/sysconfig\/network\-scripts\/route\-bondeth0"),
            exaMockCommand("/bin/sed.*\/etc\/sysconfig\/network\-scripts\/route\-bondeth0"),

            #sysconfig network ifcfg
            exaMockCommand("/bin/sed.*IPADDR.*\/etc\/sysconfig\/network\-scripts\/ifcfg\-bondeth0"),
            exaMockCommand("/bin/sed.*NETMASK.*\/etc\/sysconfig\/network\-scripts\/ifcfg\-bondeth0"),
            exaMockCommand("/bin/sed.*GATEWAY.*\/etc\/sysconfig\/network\-scripts\/ifcfg\-bondeth0"),
            exaMockCommand("/bin/sed.*NETWORK.*\/etc\/sysconfig\/network\-scripts\/ifcfg\-bondeth0"),
            exaMockCommand("/bin/sed.*BROADCAST.*\/etc\/sysconfig\/network\-scripts\/ifcfg\-bondeth0"),

            #ATP relate commands
            exaMockCommand("scp .*", aPersist=True),
            exaMockCommand(".*mkdir -p /opt/exacloud.*"),
            exaMockCommand("ps -efww |grep pmon .*", aStdout="+ASM1"),
            exaMockCommand("lsnrctl status listener_bkup.*", aStdout="localhost"),
            exaMockCommand("ALTER SYSTEM SET LOCAL_LISTENER=.*"),

            exaMockCommand("cat /etc/oratab.*", aStdout="+ASM1:/u01/app/19.0.0.0/grid:N"),
            exaMockCommand("ALTER SYSTEM REGISTER.*"),
            exaMockCommand(".*crsctl modify resourcegroup.*"),
            exaMockCommand(".*crsctl stop cluster.*"),
            exaMockCommand(".*crsctl start cluster.*"),

            # Check ASM
            exaMockCommand(".*crsctl check cluster -all | grep -c online | grep -w 6.*", aStdout="0"),
            exaMockCommand(".*srvctl status asm.*", aStdout="ASM is running on {0}".format(",".join(_domUs))),

            # Check FileSystem Mounted
            exaMockCommand(".*srvctl status filesystem | grep 'is mounted on nodes'.*",\
                           aStdout="is mounted on nodes {0}".format(",".join(_domUs))),


        ]

        _dom0Base = [

            # Step base execution
            exaMockCommand("/bin/mkdir -p /opt/exacloud/reconfig.*", aPersist=True),
            exaMockCommand("/bin/ls -la /opt/exacloud/reconfig.*", aRc=1, aPersist=True),
            exaMockCommand("/bin/touch /opt/exacloud/reconfig.*", aPersist=True),

            # Detect XEN
            exaMockCommand("imageinfo | grep 'Node type:'"),
            exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),
            exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n"),

            #Vmcontrol standard load
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
            exaMockCommand("xm list", aStdout=_xmList),

        ]

        _localBase = [
            # Check SSH port running
            exaMockCommand(".*nc.*")
        ]

        _cmds = {
            self.mGetRegexVm(): [],
            self.mGetRegexDom0(): [],
            self.mGetRegexLocal(): []
        }

        _atpConnections = 3 + len(self.mGetClubox().mReturnDom0DomUPair())
        _stepConnections = 1

        for _ in range(0, len(self.mGetClubox().mReturnDom0DomUPair()) + _atpConnections + _stepConnections):
            _cmds[self.mGetRegexVm()].append(_domUBase)
            _cmds[self.mGetRegexDom0()].append(_dom0Base)
            _cmds[self.mGetRegexLocal()].append(_localBase)

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        _reconfig = self.mGetClubox().mGetFactoryPreprovReconfig().mCreateReconfig()

        _steps = {
            _reconfig.mExecuteReconfigDomU: [
                _reconfig.mReconfigDomUChangeEtc,
                _reconfig.mReconfigDomUNetworkInfo,
                _reconfig.mReconfigDomUNetworkAtp
            ]
        }
        _reconfig.mSetWaitSteps(_steps)
        _reconfig.mExecuteReconfig()

        #Build step tables
        for _step, _stepInfo in _reconfig.mGetStepRecord().items():

            _expectedSteps = list(map(lambda x: x.__name__, _steps[getattr(_reconfig, _step)]))
            _substepsNames =  list(map(lambda x: x.split("-")[0], _stepInfo['substeps'].keys()))

            for _substep in _substepsNames:
                self.assertTrue(_substep in _expectedSteps)

    @patch('exabox.ovm.vmcontrol.ebVgLifeCycle.mDispatchEvent', return_value=0)
    @patch('exabox.ovm.cluserialconsole.serialConsole.mStopContainer')
    @patch('exabox.ovm.cluserialconsole.serialConsole.mRestartContainer')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRestartVM')
    def test_003_domU_reboot_xen(self, mock_restartVM, mock_restartContainer, mock_stopContainer, mock_dispatchEvent):

        _xmList = self.mGetResourcesTextFile("cmd_xmlist.txt")
        _guestImages = self.mGetResourcesTextFile("cmd_guestlist.txt")
        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _dom0_reboot = [

            # Reconfig workdir
            exaMockCommand("/bin/mkdir -p /opt/exacloud/reconfig.*", aPersist=True),
            exaMockCommand("/bin/ls -la /opt/exacloud/reconfig.*", aRc=1, aPersist=True),
            exaMockCommand("/bin/touch /opt/exacloud/reconfig.*", aPersist=True),

            # Detect XEN
            exaMockCommand("imageinfo | grep 'Node type:'"),
            exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),
            exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n"),

            #Vmcontrol standard load
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
            exaMockCommand("xm list", aStdout=_xmList),

            #Shutdown
            exaMockCommand("xm list", aStdout=_xmList),
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
            exaMockCommand("xm shutdown .*"),
            exaMockCommand("/bin/test -e .*", aRc=1),
            exaMockCommand("unlink /etc/xen/auto/.*"),

            #Check vm alive
            exaMockCommand("xm list", aStdout=_xmList.replace("vm", "novm")),
            exaMockCommand("xm list", aStdout=_xmList.replace("vm", "novm")),
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages.replace("vm", "novm")),

            #Rename of folder on other Node
            exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*/vm.cfg", aStdout=_vmcfg),

            # Detect XEN
            exaMockCommand("imageinfo | grep 'Node type:'"),
            exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),
            exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n"),

            #Vmcontrol standard load
            exaMockCommand("xm list", aStdout=_xmList.replace("vm", "novm")),
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages.replace("vm", "novm")),

            # Move of disk of vm.cfg inside Dom0
            exaMockCommand("/bin/ls \/OVS\/Repositories\/.*", aStdout="1bcb6407fa5440fa86dece08505542c9.img"),
            exaMockCommand("/bin/ls -la \/OVS\/Repositories\/.*unlink.*"),
            exaMockCommand("/bin/mv /EXAVMIMAGES/GuestImages/.* /EXAVMIMAGES/GuestImages/.*"),
            exaMockCommand("vmLink=(.*); /bin/unlink .*; /bin/ln -sf .*"),

            # Restart of the vm
            exaMockCommand("xm list", aStdout=_xmList.replace("vm", "novm")),
            exaMockCommand("xm create .*"),
            exaMockCommand("/bin/test -e .*", aRc=1),
            exaMockCommand("/bin/test -e /OVS/.*"),
            exaMockCommand("ln -s.*/OVS/.*"),

            # Check vm created
            exaMockCommand("xm list", aStdout=_xmList),
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),

        ]

        _localBase = [

            # Check SSH port running
            exaMockCommand(".*nc.*")
        ]

        _domUBase = [
            # Check IP after vm reboot
            exaMockCommand("ip addr show.*")
        ]

        _cmds = {
            self.mGetRegexVm(): [],
            self.mGetRegexDom0(): [],
            self.mGetRegexLocal(): [],
        }

        _stepConnections = 2

        # Add extra pair extra *3 connections:
        # 1* connection stream are from the begining to vm shutdown
        # 2* connection stream are for vm move in the Dom0 from old name to new name
        # 3* connection stream are from vm start to the end
        for _ in range(0, len(self.mGetClubox().mReturnDom0DomUPair())*3 + _stepConnections):
            _cmds[self.mGetRegexVm()].append(_domUBase)
            _cmds[self.mGetRegexDom0()].append(_dom0_reboot)
            _cmds[self.mGetRegexLocal()].append(_localBase)

        #Init new Args
        self.mGetClubox().mGetCtx().mSetConfigOption('vm_time_sleep_reboot', 0)
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        _reconfig = self.mGetClubox().mGetFactoryPreprovReconfig().mCreateReconfig()

        _steps = {
            _reconfig.mExecuteReconfigDomU: [
                _reconfig.mReconfigDomURestartVM
            ]
        }
        _reconfig.mSetWaitSteps(_steps)
        _reconfig.mExecuteReconfig()

        #Build step tables
        for _step, _stepInfo in _reconfig.mGetStepRecord().items():

            _expectedSteps = list(map(lambda x: x.__name__, _steps[getattr(_reconfig, _step)]))
            _substepsNames =  list(map(lambda x: x.split("-")[0], _stepInfo['substeps'].keys()))

            for _substep in _substepsNames:
                self.assertTrue(_substep in _expectedSteps)

    @patch('exabox.ovm.vmcontrol.ebVgLifeCycle.mDispatchEvent', return_value=0)
    @patch('exabox.ovm.cluserialconsole.serialConsole.mStopContainer')
    @patch('exabox.ovm.cluserialconsole.serialConsole.mRestartContainer')
    def test_003_2_domU_reboot_kvm(self, mock_restartContainer, mock_stopContainer, mock_dispatchEvent):

        _kvmXml = self.mGetResourcesTextFile("kvm_guest.xml")
        _kvmList = self.mGetResourcesTextFile("kvm_list.txt")
        _guestImages = self.mGetResourcesTextFile("cmd_guestlist.txt")

        _dom0_reboot = [

            # Base Reconfig
            exaMockCommand("/bin/mkdir -p .*", aPersist=True),
            exaMockCommand("/bin/ls -la .*", aRc=1, aPersist=True),
            exaMockCommand("/bin/touch .*", aPersist=True),

            # Detect KVM Envroment
            exaMockCommand("imageinfo | grep 'Node type:'", aStdout="Node type: KVMHOST"),
            exaMockCommand(".*/usr/sbin/vm_maker --list.*", aStdout=_kvmList),
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),

            #Shutdown
            exaMockCommand(".*/usr/sbin/vm_maker --list.*", aStdout=_kvmList),
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
            exaMockCommand(".*vm_maker.*stop.*"),
            exaMockCommand(".*vm_maker.*autostart.*--disable.*"),

            #Check vm alive
            exaMockCommand(".*/usr/sbin/vm_maker --list.*", aStdout=_kvmList.replace("vm", "novm")),
            exaMockCommand(".*/usr/sbin/vm_maker --list.*", aStdout=_kvmList.replace("vm", "novm")),
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages.replace("vm", "novm")),

            #Stop the VM
            exaMockCommand(".*/usr/sbin/vm_maker --list.*", aStdout=_kvmList.replace("vm", "novm")),
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages.replace("vm", "novm")),

            #Rename of folder on other Node
            exaMockCommand("/bin/test -e .*", aRc=1),
            exaMockCommand("/usr/sbin/vm_maker --dumpxml .*", aStdout=_kvmXml),
            exaMockCommand("/bin/scp .*", aPersist=True),

            # Define and modify the XML
            exaMockCommand(".*virsh undefine .*"),
            exaMockCommand(".*virsh define .*"),
            exaMockCommand(".*virsh.*autostart"),

            # Modify the nw-filters
            exaMockCommand(".*virsh nwfilter-list .*", aStdout="rule1"),
            exaMockCommand(".*virsh nwfilter-dumpxml rule1"),
            exaMockCommand(".*virsh nwfilter-undefine.*"),
            exaMockCommand(".*sed -i .*"),
            exaMockCommand(".*virsh nwfilter-define.*"),

            # Move Guest folder
            exaMockCommand(".*mv.*GuestImages.*GuestImages.*"),

            # Save Cleanup
            exaMockCommand(".*mv.*qemu.*"),

            # Restart of the vm
            exaMockCommand(".*vm_maker.*start.*"),
            exaMockCommand(".*vm_maker.*autostart.*--enable.*"),
            exaMockCommand(".*/usr/sbin/vm_maker --list.*", aStdout=_kvmList),

        ]

        _localBase = [

            # Check SSH port running
            exaMockCommand(".*nc.*")
        ]

        _domUBase = [
            # Check IP after vm reboot
            exaMockCommand("ip addr show.*")
        ]

        _cmds = {
            self.mGetRegexVm(): [],
            self.mGetRegexDom0(): [],
            self.mGetRegexLocal(): []
        }

        _stepConnections = 1

        # Add extra pair extra *3 connections:
        # 1* connection stream are from the begining to vm shutdown
        # 2* connection stream are for vm move in the Dom0 from old name to new name
        # 3* connection stream are from vm start to the end
        for _ in range(0, len(self.mGetClubox().mReturnDom0DomUPair())*3 + _stepConnections):
            _cmds[self.mGetRegexVm()].append(_domUBase)
            _cmds[self.mGetRegexDom0()].append(_dom0_reboot)
            _cmds[self.mGetRegexLocal()].append(_localBase)

        #Init new Args
        self.mGetClubox().mGetCtx().mSetConfigOption('vm_time_sleep_reboot', 0)
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        _reconfig = self.mGetClubox().mGetFactoryPreprovReconfig().mCreateReconfig()
        _reconfig.mSetReconfigWorkdir(self.mGetUtil().mGetOutputDir())

        _steps = {
            _reconfig.mExecuteReconfigDomU: [
                _reconfig.mReconfigDomURestartVM
            ]
        }
        _reconfig.mSetWaitSteps(_steps)
        _reconfig.mExecuteReconfig()

        #Build step tables
        for _step, _stepInfo in _reconfig.mGetStepRecord().items():

            _expectedSteps = list(map(lambda x: x.__name__, _steps[getattr(_reconfig, _step)]))
            _substepsNames =  list(map(lambda x: x.split("-")[0], _stepInfo['substeps'].keys()))

            for _substep in _substepsNames:
                self.assertTrue(_substep in _expectedSteps)


    def test_004_gi_execute(self):

        _xmList = self.mGetResourcesTextFile("cmd_xmlist.txt")
        _guestImages = self.mGetResourcesTextFile("cmd_guestlist.txt")
        _dbPath = "/u01/app/19.0.0.0/grid"

        _domUBase = [

            # Find clusterware and check the status
            exaMockCommand("/bin/cat /etc/oratab .*", aStdout="/u01/app/19.0.0.0/grid"),
            exaMockCommand(".*crsctl check cluster -all .*"),

            # Stop and change network of clusterware
            exaMockCommand(".*crsctl stop res.*"),
            exaMockCommand(".*srvctl config nodeapps -a.*"),
            exaMockCommand(".*srvctl modify network -k 1"),

            # Stop cluster
            exaMockCommand(".*crsctl stop cluster -all"),
            exaMockCommand(".*crsctl check cluster -all"),

            # Start cluster
            exaMockCommand(".*crsctl start cluster -all"),
            exaMockCommand(".*crsctl check cluster -all"),

            # Listener stop
            exaMockCommand(".*srvctl stop listener"),

            # Stop and remove vips
            exaMockCommand(".*srvctl stop vip.*", aPersist=True),
            exaMockCommand(".*srvctl remove vip.*"),

            # Add in every node
            exaMockCommand(".*srvctl add vip.*", aPersist=True),
            exaMockCommand(".*srvctl start vip.*", aPersist=True),

            # Scans
            exaMockCommand(".*srvctl stop scan_listener.*"),
            exaMockCommand(".*srvctl stop scan.*"),
            exaMockCommand(".*srvctl modify scan.*"),
            exaMockCommand(".*srvctl modify scan_listener.*"),
            exaMockCommand(".*srvctl config scan_listener.*"),
            exaMockCommand(".*srvctl start scan"),
            exaMockCommand(".*srvctl start scan_listener"),
            exaMockCommand(".*srvctl status scan"),
            exaMockCommand(".*srvctl config scan"),
            exaMockCommand(".*srvctl status scan_listener"),

            # Listener start
            exaMockCommand(".*srvctl status listener"),
            exaMockCommand(".*srvctl start listener"),

            # Additional cmds
            exaMockCommand("/bin/test -e /bin/ls"),
            exaMockCommand(".*ls -la /var/opt/oracle/creg/grid | head -2 | grep ...x..x..."),
            exaMockCommand("/bin/test -e /bin/chmod"),
            exaMockCommand(re.escape("/bin/chmod ug+x /var/opt/oracle/creg/grid")),
            exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*sid.*", aStdout="ASM+"),
            exaMockCommand(".*cat /var/opt/oracle/creg/grid/grid.ini.*oracle_home.*", aStdout="/u01/app/19.0.0.0/grid"),
            exaMockCommand(".*srvctl setenv nodeapps -envs ORA_NET_DEEP_CHECK.*"),
            exaMockCommand(".*srvctl setenv nodeapps -envs ORA_NET_PING_TIMEOUT.*"),
            exaMockCommand(".*srvctl setenv nodeapps -envs \"ORA_VIP_GARP_AFTER.*\""),
            exaMockCommand(".*crsctl modify res ora.scan1.vip -attr \"USR_ORA_ENV=ORA_VIP_GARP_AFTER.*\" -unsupported"),
            exaMockCommand(".*crsctl modify res ora.scan2.vip -attr \"USR_ORA_ENV=ORA_VIP_GARP_AFTER.*\" -unsupported"),
            exaMockCommand(".*crsctl modify res ora.scan3.vip -attr \"USR_ORA_ENV=ORA_VIP_GARP_AFTER.*\" -unsupported"),

        ]

        _dom0Base = [

            # Reconfig workdir
            exaMockCommand("/bin/mkdir -p /opt/exacloud/reconfig.*", aPersist=True),
            exaMockCommand("/bin/ls -la /opt/exacloud/reconfig.*", aRc=1, aPersist=True),
            exaMockCommand("/bin/touch /opt/exacloud/reconfig.*", aPersist=True),

            # Detect XEN
            exaMockCommand("imageinfo | grep 'Node type:'"),
            exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),
            exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n"),

            #Vmcontrol standard load
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
            exaMockCommand("xm list", aStdout=_xmList),
        ]

        _cmds = {
            self.mGetRegexVm(): [],
            self.mGetRegexDom0(): []
        }

        _stepConnections = 1

        for _ in range(0, len(self.mGetClubox().mReturnDom0DomUPair()) + _stepConnections):
            _cmds[self.mGetRegexVm()].append(_domUBase)
            _cmds[self.mGetRegexDom0()].append(_dom0Base)

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        # mock_execute.side_effect = iter([None,None,None,None,None,None,NotImplementedError("Undefined type of enviroment")])
        #Execute the clucontrol function
        _reconfig = self.mGetClubox().mGetFactoryPreprovReconfig().mCreateReconfig()

        _steps = {
            _reconfig.mExecuteReconfigGI: [
                _reconfig.mReconfigGiExecuteCommand
            ]
        }
        _reconfig.mSetWaitSteps(_steps)
        _reconfig.mExecuteReconfig()

        #Build step tables
        for _step, _stepInfo in _reconfig.mGetStepRecord().items():

            _expectedSteps = list(map(lambda x: x.__name__, _steps[getattr(_reconfig, _step)]))
            _substepsNames =  list(map(lambda x: x.split("-")[0], _stepInfo['substeps'].keys()))

            for _substep in _substepsNames:
                self.assertTrue(_substep in _expectedSteps)

    def test_005_already_execute_reconfig(self):

        _xmList = self.mGetResourcesTextFile("cmd_xmlist.txt")
        _guestImages = self.mGetResourcesTextFile("cmd_guestlist.txt")

        _cmds = {
            self.mGetRegexLocal(): [
                [
                    # Check SSH port running
                    exaMockCommand(".*nc.*")
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    # Detect XEN
                    exaMockCommand("imageinfo | grep 'Node type:'"),
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),
                    exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n"),

                    #Vmcontrol standard load
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
                    exaMockCommand("xm list", aStdout=_xmList),

                ],
                [
                    # Reconfig workdir Dom0
                    exaMockCommand("/bin/mkdir -p /opt/exacloud/reconfig.*", aPersist=True),
                    exaMockCommand("/bin/ls -la /opt/exacloud/reconfig.*", aPersist=True),
                    exaMockCommand("/bin/touch /opt/exacloud/reconfig.*", aPersist=True)
                ],
                [
                    # Reconfig workdir DomU
                    exaMockCommand("/bin/mkdir -p /opt/exacloud/reconfig.*", aPersist=True),
                    exaMockCommand("/bin/ls -la /opt/exacloud/reconfig.*", aPersist=True),
                    exaMockCommand("/bin/touch /opt/exacloud/reconfig.*", aPersist=True)
                ],
                [
                    # Reconfig workdir GI
                    exaMockCommand("/bin/mkdir -p /opt/exacloud/reconfig.*", aPersist=True),
                    exaMockCommand("/bin/ls -la /opt/exacloud/reconfig.*", aPersist=True),
                    exaMockCommand("/bin/touch /opt/exacloud/reconfig.*", aPersist=True)
                ],
                [
                    # Reconfig Cleanup
                    exaMockCommand("/bin/ls -la /opt/exacloud/reconfig.*01_mReconfigCleanUp.*", aRc=1),
                    exaMockCommand("/bin/rm -rf /opt/exacloud/reconfig.*"),

                    exaMockCommand("/bin/mkdir -p /opt/exacloud/reconfig.*", aPersist=True),
                    exaMockCommand("/bin/ls -la /opt/exacloud/reconfig.*", aPersist=True),
                    exaMockCommand("/bin/touch /opt/exacloud/reconfig.*", aPersist=True)
                ],
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        _reconfig = self.mGetClubox().mGetFactoryPreprovReconfig().mCreateReconfig()

        _steps = {

            _reconfig.mExecuteReconfigDom0: [
                _reconfig.mReconfigDom0ChangeVifVlan,
            ],
            _reconfig.mExecuteReconfigDomU: [
                _reconfig.mReconfigDomURestartVM
            ],
            _reconfig.mExecuteReconfigGI: [
                _reconfig.mReconfigGiExecuteCommand
            ],
            _reconfig.mExecuteReconfigCleanUp: [
                _reconfig.mReconfigCleanUp
            ]
        }

        _reconfig.mSetWaitSteps(_steps)
        _reconfig.mExecuteReconfig()

        #Build step tables
        for _step, _stepInfo in _reconfig.mGetStepRecord().items():

            _expectedSteps = list(map(lambda x: x.__name__, _steps[getattr(_reconfig, _step)]))
            _substepsNames =  list(map(lambda x: x.split("-")[0], _stepInfo['substeps'].keys()))

            for _substep in _substepsNames:
                self.assertTrue(_substep in _expectedSteps)

    @patch('exabox.ovm.vmcontrol.ebVgLifeCycle.mDispatchEvent', return_value=0)
    @patch('exabox.ovm.cluserialconsole.serialConsole.mStopContainer')
    @patch('exabox.ovm.cluserialconsole.serialConsole.mRestartContainer')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRestartVM')
    def test_006_rollback_xen(self, mock_restartVM, mock_restartContainer, mock_stopContainer, mock_dispatchEvent):

        _xmList = self.mGetResourcesTextFile("cmd_xmlist.txt")
        _guestImages = self.mGetResourcesTextFile("cmd_guestlist.txt")
        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")
        
        _dom0Base = [

            # Clean Up
            exaMockCommand("/bin/ls -la /opt/exacloud/reconfig.*mReconfigCleanUp.*", aRc=1),
            exaMockCommand("/bin/rm -rf /opt/exacloud/reconfig.*"),

            # Reconfig cleanup
            exaMockCommand("/bin/ls -la .*DomU.*", aRc=1),
            exaMockCommand("/bin/touch.*", aPersist=True),

            # Persist
            exaMockCommand("/bin/ls -la .*", aPersist=True),
            exaMockCommand("/bin/rm -rf .*", aPersist=True),

            # Detect XEN
            exaMockCommand("imageinfo | grep 'Node type:'"),
            exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),
            exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n"),

            #Vmcontrol standard load
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
            exaMockCommand("xm list", aStdout=_xmList),

            #Find backup on Dom0
            exaMockCommand("/bin/find /EXAVMIMAGES/RollbackBackup.*", aStdout="find /EXAVMIMAGES/RollbackBackup/vm/", aPersist=True),

            #Shutdown
            exaMockCommand("xm list", aStdout=_xmList),
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
            exaMockCommand("xm shutdown .*"),
            exaMockCommand("/bin/test -e .*"),
            exaMockCommand("unlink /etc/xen/auto/.*"),

            #Check vm alive
            exaMockCommand("xm list", aStdout=_xmList.replace("vm", "novm")),
            exaMockCommand("xm list", aStdout=_xmList.replace("vm", "novm")),
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages.replace("vm", "novm")),

            #Rename of folder on other Node
            exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*/vm.cfg", aStdout=_vmcfg),

            # Move of disk of vm.cfg inside Dom0
            exaMockCommand("/bin/ls \/OVS\/Repositories\/.*", aStdout="1bcb6407fa5440fa86dece08505542c9.img"),
            exaMockCommand("/bin/ls -la \/OVS\/Repositories\/.*unlink.*"),
            exaMockCommand("/bin/mv /EXAVMIMAGES/GuestImages/.* /EXAVMIMAGES/GuestImages/.*"),
            exaMockCommand("vmLink=(.*); /bin/unlink .*; /bin/ln -sf .*"),

            # Remove old vm (new name and old name)
            exaMockCommand("/bin/rm -rf /EXAVMIMAGES/GuestImages/.*"),
            exaMockCommand("/bin/rm -rf /EXAVMIMAGES/GuestImages/.*"),

            # Restore backup
            exaMockCommand("/bin/mkdir -p /EXAVMIMAGES/GuestImages/.*"),
            exaMockCommand("/bin/ls /EXAVMIMAGES/RollbackBackup/.*", aStdout="vm.cfg"),
            exaMockCommand("/bin/cp /EXAVMIMAGES/RollbackBackup/.*/vm.cfg /EXAVMIMAGES/GuestImages/.*/vm.cfg"),

            # Restart of the vm
            exaMockCommand("xm list", aStdout=_xmList.replace("vm", "novm")),
            exaMockCommand("xm create .*"),
            exaMockCommand("/bin/test -e /etc/xen/auto/.*"),
            exaMockCommand("/bin/test -e /OVS/.*"),
            exaMockCommand("ln -s.*/OVS/.*"),

            # Check vm created
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
            exaMockCommand("xm list", aStdout=_xmList),

        ]

        _localBase = [

            # Check vm up
            exaMockCommand(".*nc.*")
        ]

        _domUBase = [
            # Check IP after vm reboot
            exaMockCommand("ip addr show.*")
        ]

        _cmds = {
            self.mGetRegexVm(): [],
            self.mGetRegexDom0(): [],
            self.mGetRegexLocal(): [],
        }

        _stepConnections = 2

        for _ in range(0, len(self.mGetClubox().mReturnDom0DomUPair())*4 + _stepConnections):
            _cmds[self.mGetRegexVm()].append(_domUBase)
            _cmds[self.mGetRegexDom0()].append(_dom0Base)
            _cmds[self.mGetRegexLocal()].append(_localBase)

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        _reconfig = self.mGetClubox().mGetFactoryPreprovReconfig().mCreateReconfig()

        # Execte Rollback
        _reconfig.mExecuteRollback()

    @patch('exabox.ovm.vmcontrol.ebVgLifeCycle.mDispatchEvent', return_value=0)
    @patch('exabox.ovm.cluserialconsole.serialConsole.mStopContainer')
    @patch('exabox.ovm.cluserialconsole.serialConsole.mRestartContainer')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRestartVM')
    def test_006_rollback_kvm(self, mock_restartVM, mock_restartContainer, mock_stopContainer, mock_dispatchEvent):

        _kvmXml = self.mGetResourcesTextFile("kvm_guest.xml")
        _kvmList = self.mGetResourcesTextFile("kvm_list.txt")
        _guestImages = self.mGetResourcesTextFile("cmd_guestlist.txt")

        _dom0Base = [

            # Clean Up
            exaMockCommand("/bin/ls -la /opt/exacloud/reconfig.*mReconfigCleanUp.*", aRc=1),
            exaMockCommand("/bin/rm -rf /opt/exacloud/reconfig.*"),

            # Reconfig cleanup
            exaMockCommand("/bin/ls -la .*DomU.*", aRc=1),
            exaMockCommand("/bin/touch.*", aPersist=True),

            # Persist
            exaMockCommand("/bin/ls -la .*", aPersist=True),
            exaMockCommand("/bin/rm -rf .*", aPersist=True),

            # Detect KVM Envroment
            exaMockCommand("imageinfo | grep 'Node type:'", aStdout="Node type: KVMHOST"),
            exaMockCommand(".*/usr/sbin/vm_maker --list-domains | grep running.*", aStdout=_kvmList),
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),

            #Find backup on Dom0
            exaMockCommand("/bin/find /EXAVMIMAGES/RollbackBackup.*", aStdout="find /EXAVMIMAGES/RollbackBackup/vm/", aPersist=True),

            #Shutdown
            exaMockCommand(".*/usr/sbin/vm_maker --list-domains | grep running.*", aStdout=_kvmList),
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
            exaMockCommand(".*vm_maker.*stop.*"),
            exaMockCommand(".*vm_maker.*autostart.*--disable.*"),

            #Check vm alive
            exaMockCommand(".*/usr/sbin/vm_maker --list-domains | grep running.*", aStdout=_kvmList.replace("vm", "novm")),
            exaMockCommand(".*/usr/sbin/vm_maker --list-domains | grep running.*", aStdout=_kvmList.replace("vm", "novm")),
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),

            #Rename of folder on other Node
            exaMockCommand(".*virsh undefine.*"),
            exaMockCommand(".*virsh undefine.*"),

            # Modify the nw-filters
            exaMockCommand(".*virsh nwfilter-list .*", aStdout="rule1"),
            exaMockCommand(".*virsh nwfilter-dumpxml rule1"),
            exaMockCommand(".*virsh nwfilter-undefine.*"),
            exaMockCommand(".*sed -i .*"),
            exaMockCommand(".*virsh nwfilter-define.*"),

            # Restore XML
            exaMockCommand(".*virsh undefine.*"),
            exaMockCommand(".*virsh define.*"),
            exaMockCommand(".*virsh autostart .*"),
            exaMockCommand(".*mkdir.*"),
            exaMockCommand(".*mv.*xml.*"),

            # Remove old vm (new name and old name)
            exaMockCommand("/bin/rm -rf /EXAVMIMAGES/GuestImages/.*"),
            exaMockCommand("/bin/rm -rf /EXAVMIMAGES/GuestImages/.*"),

            # Restore backup
            exaMockCommand("/bin/mkdir -p /EXAVMIMAGES/GuestImages/.*"),
            exaMockCommand("/bin/ls /EXAVMIMAGES/RollbackBackup/.*", aStdout="dummy.xml\nimg.tar.gz"),
            exaMockCommand("/bin/cp /EXAVMIMAGES/RollbackBackup/.*/dummy.xml /EXAVMIMAGES/GuestImages/.*/dummy.xml"),
            exaMockCommand("/bin/cp /EXAVMIMAGES/RollbackBackup/.*/img.tar.gz /EXAVMIMAGES/GuestImages/.*/img.tar.gz"),

            # Restart of the vm
            exaMockCommand(".*/usr/sbin/vm_maker --list-domains | grep running", aStdout=_kvmList.replace("vm", "novm")),
            exaMockCommand(".*vm_maker.*start.*"),
            exaMockCommand(".*vm_maker.*autostart.*--enable.*"),

            # Check vm created
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
            exaMockCommand("/usr/sbin/vm_maker --list-domains | grep running", aStdout=_kvmList),

            # Remove backup
            exaMockCommand("/bin/rm.*backup.*"),

        ]

        _localBase = [

            # Check vm up
            exaMockCommand(".*nc.*")
        ]

        _domUBase = [
            # Check IP after vm reboot
            exaMockCommand("ip addr show.*")
        ]

        _cmds = {
            self.mGetRegexVm(): [],
            self.mGetRegexDom0(): [],
            self.mGetRegexLocal(): []
        }

        _stepConnections = 2

        for _ in range(0, len(self.mGetClubox().mReturnDom0DomUPair())*4 + _stepConnections):
            _cmds[self.mGetRegexVm()].append(_domUBase)
            _cmds[self.mGetRegexDom0()].append(_dom0Base)
            _cmds[self.mGetRegexLocal()].append(_localBase)

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        _reconfig = self.mGetClubox().mGetFactoryPreprovReconfig().mCreateReconfig()
        _reconfig.mSetReconfigWorkdir(self.mGetUtil().mGetOutputDir())

        # Execte Rollback
        _reconfig.mExecuteRollback()

    @patch('exabox.ovm.vmcontrol.ebVgLifeCycle.mDispatchEvent', return_value=0)
    def test_007_rollback_backup_xen(self, mock_dispatchEvent):

        _xmList = self.mGetResourcesTextFile("cmd_xmlist.txt")
        _guestImages = self.mGetResourcesTextFile("cmd_guestlist.txt")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    # Detect XEN
                    exaMockCommand("imageinfo | grep 'Node type:'"),
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),
                    exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n"),

                    #Vmcontrol standard load
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
                    exaMockCommand("xm list", aStdout=_xmList),

                    # Find backups
                    exaMockCommand("/bin/find /EXAVMIMAGES/RollbackBackup.*", aRc=1),

                    #Create backup folder
                    exaMockCommand("/bin/mkdir -p /EXAVMIMAGES/RollbackBackup.*"),
                    exaMockCommand("/bin/mv /EXAVMIMAGES/GuestImages/.* /EXAVMIMAGES/RollbackBackup"),

                    # Find backups
                    exaMockCommand("/bin/find /EXAVMIMAGES/RollbackBackup.*", aStdout="/EXAVMIMAGES/RollbackBackup/vm"),
                    exaMockCommand("/bin/find /EXAVMIMAGES/RollbackBackup.*", aStdout="/EXAVMIMAGES/RollbackBackup/vm"),

                    # Restore of backup
                    exaMockCommand("/bin/mkdir -p /EXAVMIMAGES/GuestImages.*"),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/RollbackBackup/.*", aStdout="vm.cfg"),
                    exaMockCommand("/bin/cp /EXAVMIMAGES/RollbackBackup/.*/vm.cfg /EXAVMIMAGES/GuestImages/.*/vm.cfg"),

                ],
                [
                    # Detect XEN
                    exaMockCommand("imageinfo | grep 'Node type:'"),
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),
                    exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n"),

                    #Vmcontrol standard load
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
                    exaMockCommand("xm list", aStdout=_xmList),

                    # Find backups
                    exaMockCommand("/bin/find /EXAVMIMAGES/RollbackBackup.*", aRc=1),

                    #Create backup folder
                    exaMockCommand("/bin/mkdir -p /EXAVMIMAGES/RollbackBackup.*"),
                    exaMockCommand("/bin/mv /EXAVMIMAGES/GuestImages/.* /EXAVMIMAGES/RollbackBackup"),

                    # Find backups
                    exaMockCommand("/bin/find /EXAVMIMAGES/RollbackBackup.*", aStdout="/EXAVMIMAGES/RollbackBackup/vm"),
                    exaMockCommand("/bin/find /EXAVMIMAGES/RollbackBackup.*", aStdout="/EXAVMIMAGES/RollbackBackup/vm"),

                    # Restore of backup
                    exaMockCommand("/bin/mkdir -p /EXAVMIMAGES/GuestImages.*"),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/RollbackBackup/.*", aStdout="vm.cfg"),
                    exaMockCommand("/bin/cp /EXAVMIMAGES/RollbackBackup/.*/vm.cfg /EXAVMIMAGES/GuestImages/.*/vm.cfg"),
                ],
                [
                    # Detect XEN
                    exaMockCommand("imageinfo | grep 'Node type:'"),
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),
                    exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n"),

                    #Vmcontrol standard load
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
                    exaMockCommand("xm list", aStdout=_xmList),

                    # Shutdown vms to take backup
                    exaMockCommand("xm list", aStdout=_xmList),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
                    exaMockCommand("xm shutdown .*"),
                    exaMockCommand("/bin/test -e .*", aRc=1),
                    exaMockCommand("unlink /etc/xen/auto/.*"),

                    #Check vm alive
                    exaMockCommand("xm list", aStdout=_xmList.replace("adm", "client")),
                    exaMockCommand("xm list", aStdout=_xmList.replace("adm", "client")),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages.replace("adm", "client")),

                ],
                [
                    # Detect XEN
                    exaMockCommand("imageinfo | grep 'Node type:'"),
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),
                    exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n"),

                    #Vmcontrol standard load
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
                    exaMockCommand("xm list", aStdout=_xmList),

                    # Shutdown vms to take backup
                    exaMockCommand("xm list", aStdout=_xmList.replace("adm", "client")),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages.replace("adm", "client")),
                    exaMockCommand("xm shutdown .*"),
                    exaMockCommand("/bin/test -e .*", aRc=1),
                    exaMockCommand("unlink /etc/xen/auto/.*"),

                    #Check vm alive
                    exaMockCommand("xm list", aStdout=_xmList),
                    exaMockCommand("xm list", aStdout=_xmList),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),

                    # Restart of the vm
                    exaMockCommand("xm list", aStdout=_xmList.replace("adm", "client")),
                    exaMockCommand("xm list", aStdout=_xmList.replace("vm", "novm")),
                    exaMockCommand("xm create .*"),
                    exaMockCommand("/bin/test -e .*"),

                ],
                [
                    # Check vm created
                    exaMockCommand("xm list", aStdout=_xmList.replace("adm", "client")),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages.replace("adm", "client")),
                ]
            ],
            self.mGetRegexVm(): [
                [
                    # Check IP after vm reboot
                    exaMockCommand("ip addr show.*")
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    # Check vm up
                    exaMockCommand(".*nc.*")
                ]
            ],
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # Execte Backup
        _backupTool = self.mGetClubox().mGetFactoryPreprovReconfig().mCreateBackupTool()
        _backupTool.mBackupAll()

    @patch('exabox.ovm.vmcontrol.ebVgLifeCycle.mDispatchEvent', return_value=0)
    def test_007_rollback_backup_kvm(self, mock_dispatchEvent):

        _kvmXml = self.mGetResourcesTextFile("kvm_guest.xml")
        _kvmList = self.mGetResourcesTextFile("kvm_list.txt")
        _guestImages = self.mGetResourcesTextFile("cmd_guestlist.txt")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    # Detect KVM Envroment
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="Node type: KVMHOST"),
                    exaMockCommand(".*vm_maker --list .*", aStdout=_kvmList),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),

                    # Find backups
                    exaMockCommand("/bin/find /EXAVMIMAGES/RollbackBackup.*", aRc=1),

                    #Create backup folder
                    exaMockCommand("/bin/mkdir -p /EXAVMIMAGES/RollbackBackup.*"),
                    exaMockCommand("/usr/sbin/vm_maker --dumpxml.*"),
                    exaMockCommand("/bin/mv /EXAVMIMAGES/GuestImages/.* /EXAVMIMAGES/RollbackBackup"),
                    exaMockCommand("/bin/mv .*xml.*backup.xml"),
                    exaMockCommand(".*virsh undefine .*"),

                    # Find backups
                    exaMockCommand("/bin/find /EXAVMIMAGES/RollbackBackup.*", aStdout="/EXAVMIMAGES/RollbackBackup/vm"),
                    exaMockCommand("/bin/find /EXAVMIMAGES/RollbackBackup.*", aStdout="/EXAVMIMAGES/RollbackBackup/vm"),

                    # Restore of backup
                    exaMockCommand("/bin/mkdir -p /EXAVMIMAGES/GuestImages.*"),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/RollbackBackup/.*", aStdout="backup.xml"),
                    exaMockCommand("/bin/cp /EXAVMIMAGES/RollbackBackup/.*/backup.xml /EXAVMIMAGES/GuestImages/.*/backup.xml"),

                    # Redine the vm
                    exaMockCommand(".*virsh define.*"),

                ],
                [
                    # Detect KVM Envroment
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="Node type: KVMHOST"),
                    exaMockCommand(".*vm_maker --list.*", aStdout=_kvmList),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),

                    # Find backups
                    exaMockCommand("/bin/find /EXAVMIMAGES/RollbackBackup.*", aRc=1),

                    #Create backup folder
                    exaMockCommand("/bin/mkdir -p /EXAVMIMAGES/RollbackBackup.*"),
                    exaMockCommand("/usr/sbin/vm_maker --dumpxml .*"),
                    exaMockCommand("/bin/mv /EXAVMIMAGES/GuestImages/.* /EXAVMIMAGES/RollbackBackup"),
                    exaMockCommand("/bin/mv .*xml.*backup.xml"),
                    exaMockCommand(".*virsh undefine .*"),

                    # Find backups
                    exaMockCommand("/bin/find /EXAVMIMAGES/RollbackBackup.*", aStdout="/EXAVMIMAGES/RollbackBackup/vm"),
                    exaMockCommand("/bin/find /EXAVMIMAGES/RollbackBackup.*", aStdout="/EXAVMIMAGES/RollbackBackup/vm"),

                    # Restore of backup
                    exaMockCommand("/bin/mkdir -p /EXAVMIMAGES/GuestImages.*"),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/RollbackBackup/.*", aStdout="backup.xml"),
                    exaMockCommand("/bin/cp /EXAVMIMAGES/RollbackBackup/.*/backup.xml /EXAVMIMAGES/GuestImages/.*/backup.xml"),

                    # Redine the vm
                    exaMockCommand(".*virsh define.*"),

                ],
                [
                    # Detect KVM Envroment
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="Node type: KVMHOST"),
                    exaMockCommand(".*vm_maker --list.*", aStdout=_kvmList),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),

                    # Shutdown vms to take backup
                    exaMockCommand(".*vm_maker --list", aStdout=_kvmList),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
                    exaMockCommand(".*vm_maker.*stop.*"),
                    exaMockCommand(".*vm_maker.*autostart.*--disable.*"),

                    #Check vm alive
                    exaMockCommand(".*vm_maker --list", aStdout=_kvmList.replace("adm", "client")),
                    exaMockCommand(".*vm_maker --list", aStdout=_kvmList.replace("adm", "client")),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages.replace("adm", "client")),

                ],
                [
                    # Detect KVM Envroment
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="Node type: KVMHOST"),
                    exaMockCommand(".*vm_maker --list.*", aStdout=_kvmList),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),

                    # Shutdown vms to take backup
                    exaMockCommand(".*vm_maker --list.*", aStdout=_kvmList),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
                    exaMockCommand(".*vm_maker.*stop.*"),
                    exaMockCommand(".*vm_maker.*autostart.*--disable.*"),

                    #Check vm alive
                    exaMockCommand(".*vm_maker --list", aStdout=_kvmList.replace("adm", "client")),
                    exaMockCommand(".*vm_maker --list", aStdout=_kvmList.replace("adm", "client")),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages.replace("adm", "client")),

                    # Restart of the vm
                    exaMockCommand(".*vm_maker --list.*", aStdout=_kvmList.replace("adm", "client")),
                    exaMockCommand(".*vm_maker --list.*", aStdout=_kvmList.replace("vm", "novm")),
                    exaMockCommand(".*virsh create .*"),
                    exaMockCommand(".*virsh autostart.*"),

                ],
                [
                    # Check vm created
                    exaMockCommand(".*vm_maker --list.*", aStdout=_kvmList.replace("adm", "client")),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages.replace("adm", "client")),
                ]
            ],
            self.mGetRegexVm(): [
                [
                    # Check IP after vm reboot
                    exaMockCommand("ip addr show.*")
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    # Check vm up
                    exaMockCommand(".*nc.*")
                ]
            ],
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # Execute Backup
        _backupTool = self.mGetClubox().mGetFactoryPreprovReconfig().mCreateBackupTool()
        _backupTool.mBackupAll()


        _xmList = self.mGetResourcesTextFile("cmd_xmlist.txt")
        _guestImages = self.mGetResourcesTextFile("cmd_guestlist.txt")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    # Detect XEN
                    exaMockCommand("imageinfo | grep 'Node type:'"),
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),
                    exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n"),

                    #Vmcontrol standard load
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
                    exaMockCommand("xm list", aStdout=_xmList),

                    # Check backup
                    exaMockCommand("/bin/find /EXAVMIMAGES/RollbackBackup.*", aStdout="/EXAVMIMAGES/RollbackBackup/vm"),

                    # Remove backup
                    exaMockCommand("/bin/find /EXAVMIMAGES/RollbackBackup.*", aStdout="/EXAVMIMAGES/RollbackBackup/vm"),
                    exaMockCommand("/bin/rm -rf /EXAVMIMAGES/RollbackBackup.*"),
                ],
                [
                    # Remove backup
                    exaMockCommand("/bin/find /EXAVMIMAGES/RollbackBackup.*", aStdout="/EXAVMIMAGES/RollbackBackup/vm"),
                    exaMockCommand("/bin/rm -rf /EXAVMIMAGES/RollbackBackup.*"),

                    exaMockCommand("/bin/find /EXAVMIMAGES/RollbackBackup.*", aStdout="/EXAVMIMAGES/RollbackBackup/vm"),
                    exaMockCommand("/bin/rm -rf /EXAVMIMAGES/RollbackBackup.*"),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # Execte Backup
        _backupTool = self.mGetClubox().mGetFactoryPreprovReconfig().mCreateBackupTool()
        _backupTool.mDeleteAll()

    def test_009_arping_check(self):

        _xmList = self.mGetResourcesTextFile("cmd_xmlist.txt")
        _guestImages = self.mGetResourcesTextFile("cmd_guestlist.txt")

        _domUBase = [
            exaMockCommand('/sbin/arping -c 4 -I bondeth0.*'),
            exaMockCommand('/bin/rpm --version', aRc=0),
            exaMockCommand('/sbin/ip netns exec mgmt /sbin/arping -c 4 -I bondeth1.*')
        ]

        _dom0Base = [

            # Reconfig workdir
            exaMockCommand("/bin/mkdir -p /opt/exacloud/reconfig.*", aPersist=True),
            exaMockCommand("/bin/ls -la /opt/exacloud/reconfig.*", aRc=1, aPersist=True),
            exaMockCommand("/bin/touch /opt/exacloud/reconfig.*", aPersist=True),

            # Detect XEN
            exaMockCommand("imageinfo | grep 'Node type:'"),
            exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid",
                           aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),
            exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n"),

            # Vmcontrol standard load
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
            exaMockCommand("xm list", aStdout=_xmList),
        ]

        _cmds = {
            self.mGetRegexVm(): [],
            self.mGetRegexDom0(): []
        }

        _stepConnections = 1

        for _ in range(0, len(self.mGetClubox().mReturnDom0DomUPair()) + _stepConnections):
            _cmds[self.mGetRegexVm()].append(_domUBase)
            _cmds[self.mGetRegexDom0()].append(_dom0Base)

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        _reconfig = self.mGetClubox().mGetFactoryPreprovReconfig().mCreateReconfig()

        _steps = {
            _reconfig.mExecuteReconfigChecks: [
                _reconfig.mReconfigArpingCheck
            ]
        }
        _reconfig.mSetWaitSteps(_steps)
        _reconfig.mExecuteReconfig()

        #Build step tables
        for _step, _stepInfo in _reconfig.mGetStepRecord().items():

            _expectedSteps = list(map(lambda x: x.__name__, _steps[getattr(_reconfig, _step)]))
            _substepsNames = list(map(lambda x: x.split("-")[0], _stepInfo['substeps'].keys()))

            for _substep in _substepsNames:
                self.assertTrue(_substep in _expectedSteps)

    def test_010_arping_check(self):

        _xmList = self.mGetResourcesTextFile("cmd_xmlist.txt")
        _guestImages = self.mGetResourcesTextFile("cmd_guestlist.txt")

        _domUBase = [
            exaMockCommand('/sbin/arping -c 4 -I bondeth0.*'),
            exaMockCommand('/bin/rpm --version', aRc=1),
            exaMockCommand('/sbin/arping -c 4 -I bondeth1.*')
        ]

        _dom0Base = [

            # Reconfig workdir
            exaMockCommand("/bin/mkdir -p /opt/exacloud/reconfig.*", aPersist=True),
            exaMockCommand("/bin/ls -la /opt/exacloud/reconfig.*", aRc=1, aPersist=True),
            exaMockCommand("/bin/touch /opt/exacloud/reconfig.*", aPersist=True),

            # Detect XEN
            exaMockCommand("imageinfo | grep 'Node type:'"),
            exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid",
                           aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),
            exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n"),

            # Vmcontrol standard load
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
            exaMockCommand("xm list", aStdout=_xmList),
        ]

        _cmds = {
            self.mGetRegexVm(): [],
            self.mGetRegexDom0(): []
        }

        _stepConnections = 1

        for _ in range(0, len(self.mGetClubox().mReturnDom0DomUPair()) + _stepConnections):
            _cmds[self.mGetRegexVm()].append(_domUBase)
            _cmds[self.mGetRegexDom0()].append(_dom0Base)

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        _reconfig = self.mGetClubox().mGetFactoryPreprovReconfig().mCreateReconfig()

        _steps = {
            _reconfig.mExecuteReconfigChecks: [
                _reconfig.mReconfigArpingCheck
            ]
        }
        _reconfig.mSetWaitSteps(_steps)
        _reconfig.mExecuteReconfig()

        #Build step tables
        for _step, _stepInfo in _reconfig.mGetStepRecord().items():

            _expectedSteps = list(map(lambda x: x.__name__, _steps[getattr(_reconfig, _step)]))
            _substepsNames = list(map(lambda x: x.split("-")[0], _stepInfo['substeps'].keys()))

            for _substep in _substepsNames:
                self.assertTrue(_substep in _expectedSteps)

    def test_011_arping_check_error(self):

        _xmList = self.mGetResourcesTextFile("cmd_xmlist.txt")
        _guestImages = self.mGetResourcesTextFile("cmd_guestlist.txt")

        _domUBase = [
            exaMockCommand('/sbin/arping -c 4 -I bondeth0.*'),
            exaMockCommand('/bin/rpm --version', aRc=0),
            exaMockCommand('/sbin/arping -c 4 -I bondeth1.*', aRc=1)
        ]

        _dom0Base = [

            # Reconfig workdir
            exaMockCommand("/bin/mkdir -p /opt/exacloud/reconfig.*", aPersist=True),
            exaMockCommand("/bin/ls -la /opt/exacloud/reconfig.*", aRc=1, aPersist=True),
            exaMockCommand("/bin/touch /opt/exacloud/reconfig.*", aPersist=True),

            # Detect XEN
            exaMockCommand("imageinfo | grep 'Node type:'"),
            exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid",
                           aStdout="xen\n00000000-0000-0000-0000-000000000000\n"),
            exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n"),

            # Vmcontrol standard load
            exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=_guestImages),
            exaMockCommand("xm list", aStdout=_xmList),
        ]

        _cmds = {
            self.mGetRegexVm(): [],
            self.mGetRegexDom0(): []
        }

        _stepConnections = 1

        for _ in range(0, len(self.mGetClubox().mReturnDom0DomUPair()) + _stepConnections):
            _cmds[self.mGetRegexVm()].append(_domUBase)
            _cmds[self.mGetRegexDom0()].append(_dom0Base)

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        _reconfig = self.mGetClubox().mGetFactoryPreprovReconfig().mCreateReconfig()

        _steps = {
            _reconfig.mExecuteReconfigChecks: [
                _reconfig.mReconfigArpingCheck
            ]
        }
        _reconfig.mSetWaitSteps(_steps)
        try:
            _reconfig.mExecuteReconfig()
        except ExacloudRuntimeError as e:
            ebLogInfo("The Negative Arping check testcase is successful")

if __name__ == '__main__':
    unittest.main(warnings='ignore')


# end file
