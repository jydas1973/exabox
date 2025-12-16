#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/vmgi_install/cs_prevmchecks/tests_dom0_resources.py /main/7 2025/11/07 18:27:15 scoral Exp $
#
# tests_db_delete.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_db_delete.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      Unittesting class to cs_dbinstall.py containers files
#
#    NOTES
#      NONE
#
#    MODIFIED   (MM/DD/YY)
#    naps        03/12/25 - Bug 37486891 - dom0 access inside
#                           mCheckDom0Resources need to made in parallel.
#    naps        01/10/23 - Bug 34884577- UT updation.
#    naps        06/09/22 - zdlra hyperthreading change.
#    jesandov    07/23/20 - Creation

import copy
import unittest
from unittest import mock
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
from exabox.core.Context import get_gcontext
 
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Error import ebError, ExacloudRuntimeError

class mockHVInstance():

    def __init__(self):
        self.__running_domus = list()

    def getDom0FreeMem(_dom0):
        return "1024000"

class mockHVInstanceLessMem():

    def __init__(self):
        self.__running_domus = ['vm1.oracle.com', 'vm2.oracle.com']

    def getDom0FreeMem(_dom0):
        return "10240"

    def mSetRunningDomUs(self, aListOfRunningDomUs):
        self.__running_domus = copy.deepcopy(aListOfRunningDomUs)

    def mRefreshDomUs(self):
        return self.__running_domus 

class ebTestDom0Resources(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def test_001_mCheckDom0Resources_default(self):
 
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("reboot"),
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand(".*", aPersist=True)
                ]
            ]
        }
 
        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _payload = self.mGetPayload()
        self.mGetClubox().mSetUUID("")
        self.mGetClubox().mSetTimeoutEcops(0)
        self.mGetClubox()._exaBoxCluCtrl__shared_env = False

        #Execute the clucontrol function
        with self.assertRaisesRegex(ExacloudRuntimeError, "/opt/MegaRAID/MegaCli/MegaCli64"):
            self.mGetClubox().mCheckDom0Resources(_payload)

    def test_002_mCheckDom0Resources_disabled(self):
 
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("scp scripts/cpu_vnuma_to_pinning.sh /tmp/cpu_vnuma_to_pinning.sh"),
                    exaMockCommand("bash /tmp/cpu_vnuma_to_pinning.sh"),
                    exaMockCommand("rm /tmp/cpu_vnuma_to_pinning.sh"),
                    exaMockCommand("xm info | grep dom0_vcpu_pin", aRc=0),
                ],
                [
                    exaMockCommand("reboot"),
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand(".*", aPersist=True)
                ]
            ]
        }
 
        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _payload = self.mGetPayload()
        _payload.jsonconf['vm'] = {'cloud_vnuma': "disabled"}
        self.mGetClubox().mSetUUID("")
        self.mGetClubox().mSetTimeoutEcops(0)
        self.mGetClubox()._exaBoxCluCtrl__shared_env = False

        #Execute the clucontrol function
        with self.assertRaisesRegex(ExacloudRuntimeError, "/opt/MegaRAID/MegaCli/MegaCli64"):
            self.mGetClubox().mCheckDom0Resources(_payload)

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNodesIfNoVMExists')
    def test_002_mCheckDom0Resources_enable_without_overlap(self, mock_RebootNodesIfNoVMExists):
 
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("scp scripts/cpu_pinning_to_vnuma.sh /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("bash /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("rm /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("xm info | grep dom0_vcpu_pin", aRc=1),
                ],
                [
                    exaMockCommand("reboot"),
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand(".*", aPersist=True)
                ]
            ]
        }
 
        #Init new Args
        self.mPrepareMockCommands(_cmds)
        self.mGetClubox()._exaBoxCluCtrl__shared_env = False

        _payload = self.mGetPayload()
        _payload.jsonconf['vm'] = {'cloud_vnuma': "enabled_without_dom0_overlap"}
        self.mGetClubox().mSetUUID("")
        self.mGetClubox().mSetTimeoutEcops(0)

        #Execute the clucontrol function
        with self.assertRaisesRegex(ExacloudRuntimeError, "/opt/MegaRAID/MegaCli/MegaCli64"):
            self.mGetClubox().mCheckDom0Resources(_payload)
 
    def test_003_mCheckDom0Resources_enable_with_overlap(self):
 
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("scp scripts/cpu_pinning_to_vnuma.sh /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("bash /tmp/cpu_pinning_to_vnuma.sh -overlap"),
                    exaMockCommand("rm /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("xm info | grep dom0_vcpu_pin", aRc=1),
                ],
                [
                    exaMockCommand("reboot"),
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand(".*", aPersist=True)
                ]
            ]
        }
 
        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _payload = self.mGetPayload()
        _payload.jsonconf['vm'] = {'cloud_vnuma': "enabled_with_dom0_overlap"}
        self.mGetClubox().mSetUUID("")
        self.mGetClubox().mSetTimeoutEcops(0)
        self.mGetClubox()._exaBoxCluCtrl__shared_env = False

        #Execute the clucontrol function
        with self.assertRaisesRegex(ExacloudRuntimeError, "/opt/MegaRAID/MegaCli/MegaCli64"):
            self.mGetClubox().mCheckDom0Resources(_payload)

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNodesIfNoVMExists')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mMakeFipsCompliant', return_value=(0, "reboot_host"))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetSeLinux', return_value=(1))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSELinuxMode', return_value=("disabled"))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetu02Size', return_value=("100G"))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckEthInterfaces')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckNumVM', return_value=(10))
    def test_002_mCheckDom0Resources_parallel_ut(self, mock_RebootNodesIfNoVMExists, mock_mMakeFipsCompliant, mock_mSetSeLinux, mock_mGetSELinuxMode, mock_mGetu02Size, mock_mCheckEthInterfaces, mock_mCheckNumVM):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("scp scripts/cpu_pinning_to_vnuma.sh /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("bash /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("rm /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("/usr/sbin/xm info | /bin/grep dom0_vcpus_pin", aRc=0),
                    exaMockCommand("df -h -B G*", aRc=0, aStdout="/dev/mapper/VGExaDb-LVDbExaVMImages     6726G  196G     6530G   3% /EXAVMIMAGES")
                ],
                [
                    exaMockCommand("reboot"),
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand(".*", aPersist=True)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _payload = self.mGetPayload()
        _payload.jsonconf['vm'] = {'cloud_vnuma': "enabled_with_dom0_overlap"}
        seLinuxPayload = dict()
        infraComponentDom0 = dict()
        infraComponentDom0["mode"] = "disabled"
        infraComponentDom0["component"] = "dom0"
        infraComponentDom0["targetComponentName"] = "all"
        infraComponentDom0["policy"] = "dom0_policy"

        infraComponent = dict()
        infraComponent["infraComponent"] = [infraComponentDom0]
        _payload.jsonconf["se_linux"] = infraComponent
        self.mGetClubox().mSetUUID("")
        self.mGetClubox().mSetTimeoutEcops(0)
        #_ebox_local = copy.deepcopy(self.mGetClubox())
        #_ebox_local._exaBoxCluCtrl__shared_env = True
        self.mGetClubox()._exaBoxCluCtrl__shared_env = True
        #Execute the clucontrol function
        #with self.assertRaisesRegex(ExacloudRuntimeError, "/opt/MegaRAID/MegaCli/MegaCli64"):
        _mock_hv_instance = mockHVInstance()
        with patch('exabox.ovm.clucontrol.getHVInstance', return_value=_mock_hv_instance):
            self.mGetClubox().mCheckDom0Resources(_payload)


    #'''
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNodesIfNoVMExists')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mMakeFipsCompliant', return_value=(0, "reboot_host"))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetSeLinux', return_value=(1))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSELinuxMode', return_value=("disabled"))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetu02Size', return_value=("100G"))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckEthInterfaces')
    def test_002_mCheckDom0Resources_parallel_ut_lessmem(self, mock_RebootNodesIfNoVMExists, mock_mMakeFipsCompliant, mock_mSetSeLinux, mock_mGetSELinuxMode, mock_mGetu02Size, mock_mCheckEthInterfaces):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("scp scripts/cpu_pinning_to_vnuma.sh /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("bash /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("rm /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("/usr/sbin/xm info | /bin/grep dom0_vcpus_pin", aRc=0),
                    exaMockCommand("df -h -B G*", aRc=0, aStdout="/dev/mapper/VGExaDb-LVDbExaVMImages     6726G  196G     6530G   3% /EXAVMIMAGES")
                ],
                [
                    exaMockCommand("reboot"),
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand(".*", aPersist=True)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _payload = self.mGetPayload()
        _payload.jsonconf['vm'] = {'cloud_vnuma': "enabled_with_dom0_overlap"}
        seLinuxPayload = dict()
        infraComponentDom0 = dict()
        infraComponentDom0["mode"] = "disabled"
        infraComponentDom0["component"] = "dom0"
        infraComponentDom0["targetComponentName"] = "all"
        infraComponentDom0["policy"] = "dom0_policy"

        infraComponent = dict()
        infraComponent["infraComponent"] = [infraComponentDom0]
        _payload.jsonconf["se_linux"] = infraComponent
        self.mGetClubox().mSetUUID("")
        self.mGetClubox().mSetTimeoutEcops(0)
        self.mGetClubox()._exaBoxCluCtrl__shared_env = False

        #Execute the clucontrol function
        #with self.assertRaisesRegex(ExacloudRuntimeError, "/opt/MegaRAID/MegaCli/MegaCli64"):
        _mock_hv_instance = mockHVInstanceLessMem()
        with patch('exabox.ovm.clucontrol.getHVInstance', return_value=_mock_hv_instance):
            try:
                self.mGetClubox().mCheckDom0Resources(_payload)
            except Exception as e:
                _rc = "Error in multiprocessing" in str(e)
                self.assertEqual(_rc, 1)
    #'''

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNodesIfNoVMExists')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mMakeFipsCompliant', return_value=(0, "reboot_host"))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetSeLinux', return_value=(1))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSELinuxMode', return_value=("disabled"))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetu02Size', return_value=("100G"))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckEthInterfaces')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckNumVM', return_value=(10))
    def test_002_mCheckDom0Resources_parallel_ut_exception_1(self, mock_RebootNodesIfNoVMExists, mock_mMakeFipsCompliant, mock_mSetSeLinux, mock_mGetSELinuxMode, mock_mGetu02Size, mock_mCheckEthInterfaces, mock_mCheckNumVM):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("scp scripts/cpu_pinning_to_vnuma.sh /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("bash /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("rm /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("/usr/sbin/xm info | /bin/grep dom0_vcpus_pin", aRc=0),
                    exaMockCommand("df -h -B G*", aRc=1, aStdout="/dev/mapper/VGExaDb-LVDbExaVMImages     6726G  196G     6530G   3% /EXAVMIMAGES")
                ],
                [
                    exaMockCommand("reboot"),
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand(".*", aPersist=True)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _payload = self.mGetPayload()
        _payload.jsonconf['vm'] = {'cloud_vnuma': "enabled_with_dom0_overlap"}
        seLinuxPayload = dict()
        infraComponentDom0 = dict()
        infraComponentDom0["mode"] = "disabled"
        infraComponentDom0["component"] = "dom0"
        infraComponentDom0["targetComponentName"] = "all"
        infraComponentDom0["policy"] = "dom0_policy"

        infraComponent = dict()
        infraComponent["infraComponent"] = [infraComponentDom0]
        _payload.jsonconf["se_linux"] = infraComponent
        self.mGetClubox().mSetUUID("")
        self.mGetClubox().mSetTimeoutEcops(0)
        #_ebox_local = copy.deepcopy(self.mGetClubox())
        #_ebox_local._exaBoxCluCtrl__shared_env = True
        self.mGetClubox()._exaBoxCluCtrl__shared_env = True
        #Execute the clucontrol function
        #with self.assertRaisesRegex(ExacloudRuntimeError, "/opt/MegaRAID/MegaCli/MegaCli64"):
        _mock_hv_instance = mockHVInstance()
        with patch('exabox.ovm.clucontrol.getHVInstance', return_value=_mock_hv_instance):
            try:
                self.mGetClubox().mCheckDom0Resources(_payload)
            except Exception as e:
                _rc = "Error in multiprocessing" in str(e)
                self.assertEqual(_rc, 1)

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNodesIfNoVMExists')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mMakeFipsCompliant', return_value=(0, "reboot_host"))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetSeLinux', return_value=(1))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSELinuxMode', return_value=("disabled"))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetu02Size', return_value=("100G"))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckEthInterfaces')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckNumVM', return_value=(10))
    def test_002_mCheckDom0Resources_parallel_ut_exception_2(self, mock_RebootNodesIfNoVMExists, mock_mMakeFipsCompliant, mock_mSetSeLinux, mock_mGetSELinuxMode, mock_mGetu02Size, mock_mCheckEthInterfaces, mock_mCheckNumVM):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("scp scripts/cpu_pinning_to_vnuma.sh /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("bash /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("rm /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("/usr/sbin/xm info | /bin/grep dom0_vcpus_pin", aRc=0),
                    exaMockCommand("df -h -B G*", aRc=0, aStdout="/dev/mapper/VGExaDb-LVDbExaVMImages     6726G  10G     10G   3% /EXAVMIMAGES")
                ],
                [
                    exaMockCommand("reboot"),
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand(".*", aPersist=True)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _payload = self.mGetPayload()
        _payload.jsonconf['vm'] = {'cloud_vnuma': "enabled_with_dom0_overlap"}
        seLinuxPayload = dict()
        infraComponentDom0 = dict()
        infraComponentDom0["mode"] = "disabled"
        infraComponentDom0["component"] = "dom0"
        infraComponentDom0["targetComponentName"] = "all"
        infraComponentDom0["policy"] = "dom0_policy"


        infraComponent = dict()
        infraComponent["infraComponent"] = [infraComponentDom0]
        _payload.jsonconf["se_linux"] = infraComponent
        self.mGetClubox().mSetUUID("")
        self.mGetClubox().mSetTimeoutEcops(0)
        #_ebox_local = copy.deepcopy(self.mGetClubox())
        #_ebox_local._exaBoxCluCtrl__shared_env = True
        self.mGetClubox()._exaBoxCluCtrl__shared_env = True
        #Execute the clucontrol function
        #with self.assertRaisesRegex(ExacloudRuntimeError, "/opt/MegaRAID/MegaCli/MegaCli64"):
        _mock_hv_instance = mockHVInstance()
        with patch('exabox.ovm.clucontrol.getHVInstance', return_value=_mock_hv_instance):
            try:
                self.mGetClubox().mCheckDom0Resources(_payload)
            except Exception as e:
                _rc = "Error in multiprocessing" in str(e)
                self.assertEqual(_rc, 1)


    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNodesIfNoVMExists')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mMakeFipsCompliant', return_value=(0, "reboot_host"))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetSeLinux', return_value=(1))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSELinuxMode', return_value=("disabled"))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetu02Size', return_value=("100G"))
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckEthInterfaces')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckNumVM', return_value=(200))
    def test_002_mCheckDom0Resources_parallel_ut_exception_3(self, mock_RebootNodesIfNoVMExists, mock_mMakeFipsCompliant, mock_mSetSeLinux, mock_mGetSELinuxMode, mock_mGetu02Size, mock_mCheckEthInterfaces, mock_mCheckNumVM):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("scp scripts/cpu_pinning_to_vnuma.sh /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("bash /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("rm /tmp/cpu_pinning_to_vnuma.sh"),
                    exaMockCommand("/usr/sbin/xm info | /bin/grep dom0_vcpus_pin", aRc=0),
                    exaMockCommand("df -h -B G*", aRc=0, aStdout="/dev/mapper/VGExaDb-LVDbExaVMImages     6726G  10G     10G   3% /EXAVMIMAGES")
                ],
                [
                    exaMockCommand("reboot"),
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand(".*", aPersist=True)
                ]
            ]
        }


        #Init new Args
        self.mPrepareMockCommands(_cmds)

        _payload = self.mGetPayload()
        _payload.jsonconf['vm'] = {'cloud_vnuma': "enabled_with_dom0_overlap"}
        seLinuxPayload = dict()
        infraComponentDom0 = dict()
        infraComponentDom0["mode"] = "disabled"
        infraComponentDom0["component"] = "dom0"
        infraComponentDom0["targetComponentName"] = "all"
        infraComponentDom0["policy"] = "dom0_policy"


        infraComponent = dict()
        infraComponent["infraComponent"] = [infraComponentDom0]
        _payload.jsonconf["se_linux"] = infraComponent
        self.mGetClubox().mSetUUID("")
        self.mGetClubox().mSetTimeoutEcops(0)
        #_ebox_local = copy.deepcopy(self.mGetClubox())
        #_ebox_local._exaBoxCluCtrl__shared_env = True
        self.mGetClubox()._exaBoxCluCtrl__shared_env = True
        #Execute the clucontrol function
        #with self.assertRaisesRegex(ExacloudRuntimeError, "/opt/MegaRAID/MegaCli/MegaCli64"):
        _mock_hv_instance = mockHVInstance()
        with patch('exabox.ovm.clucontrol.getHVInstance', return_value=_mock_hv_instance):
            try:
                self.mGetClubox().mCheckDom0Resources(_payload)
            except Exception as e:
                _rc = "Cluster limit" in str(e)
                self.assertEqual(_rc, 1)

if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end file
