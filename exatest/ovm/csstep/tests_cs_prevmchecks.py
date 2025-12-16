#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/tests_cs_prevmchecks.py /main/5 2025/05/09 16:28:23 avimonda Exp $
#
# tests_cs_prevmchecks.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_prevmchecks.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    avimonda    04/04/25 - Bug 37742228 - EXACS: PROVISIONING FAILED WITH
#                           ERROR:OEDA-1602: INVALID BOND FOR BRIDGE BONDETH1
#                           ON HOST <DOM0>
#    jfsaldan    03/03/25 - Bug 37609603 - EXADB-XS-PP: VMC PROVISION FAILED AT
#                           THE STEP5 _CREATE_VIRTUAL_MACHINE WITH ERROR "MOUNT
#                           POINT DOES NOT EXIST" | PARALLEL OP INCORRECTLY
#                           REMOVES A NON STALE GUEST DIRECTORY
#    jfsaldan    02/24/25 - Bug 37570873 - EXADB-D|XS -- EXACLOUD |
#                           PROVISIONING | REVIEW AND ORGANIZE PREVM_CHECKS AND
#                           PREVM_SETUP STEPS
#    avimonda    10/14/23 - Unit tests for mDetectAndRemoveStaleVMdirs method
#    prsshukl    10/26/22 - Unit test file for prevm check for mRpmCheck method
#    prsshukl    10/26/22 - Creation
#

import unittest

import io
from io import StringIO
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.csstep.cs_prevmchecks import csPreVMChecks
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check)
from unittest.mock import patch, call, mock_open

_vm_dirs_with_stale_dir = \
"""xsdb6-3642.exacp10.jboduvcn.oraclevcn.com
nodehostr042-7157.exacp10.jboduvcn.oraclevcn.com
nodehostr052-4018.exacp10.jboduvcn.oraclevcn.com
xsdb6-1391.exacp10.jboduvcn.oraclevcn.com
rlaunch-09jfg2-9327.exacsx8mtest.bemeng.oraclevcn.com
"""

_vm_dirs_without_stale_dir = \
"""nodehostr042-7157.exacp10.jboduvcn.oraclevcn.com
nodehostr052-4018.exacp10.jboduvcn.oraclevcn.com
xsdb6-1391.exacp10.jboduvcn.oraclevcn.com
rlaunch-09jfg2-9327.exacsx8mtest.bemeng.oraclevcn.com
"""
 
_domus = \
"""rlaunch-09jfg2-9327.exacsx8mtest.bemeng.oraclevcn.com
xsdb6-1391.exacp10.jboduvcn.oraclevcn.com
nodehostr052-4018.exacp10.jboduvcn.oraclevcn.com
nodehostr042-7157.exacp10.jboduvcn.oraclevcn.com
"""

_libvirt_xmls = \
"""/etc/libvirt/qemu/rlaunch-09jfg2-9327.exacsx8mtest.bemeng.oraclevcn.com.xml
/etc/libvirt/qemu/nodehostr042-7157.exacp10.jboduvcn.oraclevcn.com.xml
/etc/libvirt/qemu/xsdb6-1391.exacp10.jboduvcn.oraclevcn.com.xml
/etc/libvirt/qemu/nodehostr052-4018.exacp10.jboduvcn.oraclevcn.com.xml
"""

_ls_bondeth_output = \
"""/proc/net/bonding/bondeth0
/proc/net/bonding/bondeth1
"""

_ls_bridge_name_xml_output = \
"""/etc/exadata/ovm/bridge.conf.d/bridge.vmbondeth1.0.bondeth1.0.eth1.eth2.xml
"""

_cat_bondmaster_output = \
"""beth12
"""

class testOptions(object): pass

class ebTestCSPreVmChecks(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCSPreVmChecks, self).setUpClass()
    
    def test_mRpmCheckIsNotCorrupt(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPreVMChecks.mRpmCheck when Rpm database is Not Corrupt")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/rpm -qa", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csPreVMChecksInstance = csPreVMChecks()
        csPreVMChecksInstance.mRpmCheck(self.mGetClubox())

    def test_mRpmCheckIsCorruptRebuildIsSuccessQueryIsSuccess(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPreVMChecks.mRpmCheck when Rpm database is Corrupt and Rebuild of Rpm database is Successful and Query on it is also Successful")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/rpm -qa", aRc=1),
                    exaMockCommand("/bin/rpm -vv --rebuilddb", aRc=0, aPersist=True),
                    exaMockCommand("/bin/rpm -qa", aRc=0)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csPreVMChecksInstance = csPreVMChecks()
        csPreVMChecksInstance.mRpmCheck(self.mGetClubox())

    def test_mRpmCheckIsCorruptRebuildIsFailure(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPreVMChecks.mRpmCheck when Rpm database is Corrupt and Rebuild of Rpm database has Failed")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/rpm -qa", aRc=1, aPersist=True),
                    exaMockCommand("/bin/rpm -vv --rebuilddb", aRc=1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csPreVMChecksInstance = csPreVMChecks()
        with self.assertRaises(ExacloudRuntimeError):
            csPreVMChecksInstance.mRpmCheck(self.mGetClubox())

    def test_mRpmCheckIsCorruptRebuildIsSuccessQueryIsFailure(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPreVMChecks.mRpmCheck when Rpm database is Corrupt and Rebuild of Rpm database is successful but Query on it has Failed")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/rpm -qa", aRc=1, aPersist=True),
                    exaMockCommand("/bin/rpm -vv --rebuilddb", aRc=0, aPersist=True),
                    exaMockCommand("/bin/rpm -qa", aRc=1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csPreVMChecksInstance = csPreVMChecks()
        with self.assertRaises(ExacloudRuntimeError):
            csPreVMChecksInstance.mRpmCheck(self.mGetClubox())

    def test_mDetectAndRemoveStaleBondethInterface_vm_maker_remove_bridge_success(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPreVMChecks.mDetectAndRemoveStaleBondethInterface")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test.*ls"),
                    exaMockCommand("ls /proc/net/bonding/bondeth*", aStdout=_ls_bondeth_output, aRc=0, aPersist=True),
                    exaMockCommand("test.*rm"),
                    exaMockCommand("ls /etc/exadata/ovm/bridge.conf.d/.*.bondeth1.*.xml", aStdout=_ls_bridge_name_xml_output, aRc=0, aPersist=True),
                    exaMockCommand("rm -rf /etc/exadata/ovm/bridge.conf.d/.*.bondeth1.*.xml", aRc=0, aPersist=True),
                    exaMockCommand("test.*ip"),
                    exaMockCommand("vm_maker --remove-bridge vmbondeth1 --force", aRc=0, aPersist=True),
                    exaMockCommand("rm -rf /etc/sysconfig/network-scripts/ifcfg-bondeth1", aRc=0, aPersist=True),
                    exaMockCommand("ip link delete bondeth1", aRc=0, aPersist=True),
                    exaMockCommand("test.*cat"),
                    exaMockCommand("cat /sys/class/net/bonding_masters", aStdout=_cat_bondmaster_output, aRc=0, aPersist=True),
                    exaMockCommand("rm -rf /proc/net/bonding/bondeth1", aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csPreVMChecksInstance = csPreVMChecks()
        csPreVMChecksInstance.mDetectAndRemoveStaleBondethInterface(self.mGetClubox())

    def test_mDetectAndRemoveStaleBondethInterface_vm_maker_remove_bridge_fail(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPreVMChecks.mDetectAndRemoveStaleBondethInterface")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test.*ls"),
                    exaMockCommand("ls /proc/net/bonding/bondeth*", aStdout=_ls_bondeth_output, aRc=0, aPersist=True),
                    exaMockCommand("test.*rm"),
                    exaMockCommand("ls /etc/exadata/ovm/bridge.conf.d/.*.bondeth1.*.xml", aStdout=_ls_bridge_name_xml_output, aRc=0, aPersist=True),
                    exaMockCommand("rm -rf /etc/exadata/ovm/bridge.conf.d/.*.bondeth1.*.xml", aRc=0, aPersist=True),
                    exaMockCommand("test.*ip"),
                    exaMockCommand("vm_maker --remove-bridge vmbondeth1 --force", aRc=1, aPersist=True),
                    exaMockCommand("rm -rf /etc/sysconfig/network-scripts/ifcfg-bondeth1", aRc=0, aPersist=True),
                    exaMockCommand("rm -rf /etc/sysconfig/network-scripts/ifcfg-vmbondeth1", aRc=0, aPersist=True),
                    exaMockCommand("ip link delete bondeth1", aRc=0, aPersist=True),
                    exaMockCommand("ip link delete vmbondeth1", aRc=0, aPersist=True),
                    exaMockCommand("test.*cat"),
                    exaMockCommand("cat /sys/class/net/bonding_masters", aStdout=_cat_bondmaster_output, aRc=0, aPersist=True),
                    exaMockCommand("rm -rf /proc/net/bonding/bondeth1", aRc=0, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csPreVMChecksInstance = csPreVMChecks()
        csPreVMChecksInstance.mDetectAndRemoveStaleBondethInterface(self.mGetClubox())

    def test_mDetectAndRemoveStaleVMdirs_With_Stale_Directories(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPreVMChecks.mDetectAndRemoveStaleVMdirs when /bin/ls /EXAVMIMAGES/GuestImages commands failed")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test.*pgrep"),
                    exaMockCommand("test.*grep"),
                    exaMockCommand("pgrep -af 'vm_maker' | /sbin/grep -v ", aRc=1),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/GuestImages", aStdout=_vm_dirs_with_stale_dir, aRc=0, aPersist=True),
                    exaMockCommand("virsh list --all --name", aStdout=_domus, aRc=0, aPersist=True),
                    exaMockCommand("/bin/ls /etc/libvirt/qemu/\*.xml", aStdout=_libvirt_xmls, aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/virsh undefine xsdb6-3642.exacp10.jboduvcn.oraclevcn.com", aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/rm -rf /EXAVMIMAGES/GuestImages/xsdb6-3642.exacp10.jboduvcn.oraclevcn.com", aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csPreVMChecksInstance = csPreVMChecks()
        csPreVMChecksInstance.mDetectAndRemoveStaleVMdirs(self.mGetClubox())


    def test_mDetectAndRemoveStaleVMdirs_Without_Stale_Directories(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPreVMChecks.mDetectAndRemoveStaleVMdirs when /bin/ls /EXAVMIMAGES/GuestImages commands failed")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test.*pgrep"),
                    exaMockCommand("test.*grep"),
                    exaMockCommand("pgrep -af 'vm_maker' | /sbin/grep -v ", aRc=1),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/GuestImages", aStdout=_vm_dirs_without_stale_dir, aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/virsh list --all --name", aStdout=_domus, aRc=0, aPersist=True),
                    exaMockCommand("/bin/ls /etc/libvirt/qemu/\*.xml", aStdout=_libvirt_xmls, aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csPreVMChecksInstance = csPreVMChecks()
        csPreVMChecksInstance.mDetectAndRemoveStaleVMdirs(self.mGetClubox())


    def test_mDetectAndRemoveStaleVMdirs_ls_EXAVMIMAGES_GuestImages_Fail(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPreVMChecks.mDetectAndRemoveStaleVMdirs when /bin/ls /EXAVMIMAGES/GuestImages command failed")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test.*pgrep"),
                    exaMockCommand("test.*grep"),
                    exaMockCommand("pgrep -af 'vm_maker' | /sbin/grep -v ", aRc=1),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/GuestImages", aStdout="", aRc=1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csPreVMChecksInstance = csPreVMChecks()
        csPreVMChecksInstance.mDetectAndRemoveStaleVMdirs(self.mGetClubox())


    def test_mDetectAndRemoveStaleVMdirs_virsh_list_all_name_Fail(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPreVMChecks.mDetectAndRemoveStaleVMdirs when /bin/ls /EXAVMIMAGES/GuestImages command failed")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test.*pgrep"),
                    exaMockCommand("test.*grep"),
                    exaMockCommand("pgrep -af 'vm_maker' | /sbin/grep -v ", aRc=1),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/GuestImages", aStdout=_vm_dirs_with_stale_dir, aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/virsh list --all --name", aStdout="", aRc=1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csPreVMChecksInstance = csPreVMChecks()
        csPreVMChecksInstance.mDetectAndRemoveStaleVMdirs(self.mGetClubox())


    def test_mDetectAndRemoveStaleVMdirs_ls_etc_libvirt_qemu_xml_Fail(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPreVMChecks.mDetectAndRemoveStaleVMdirs when /bin/ls /EXAVMIMAGES/GuestImages command failed")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test.*pgrep"),
                    exaMockCommand("test.*grep"),
                    exaMockCommand("pgrep -af 'vm_maker' | /sbin/grep -v ", aRc=1),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/GuestImages", aStdout=_vm_dirs_with_stale_dir, aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/virsh list --all --name", aStdout=_domus, aRc=0, aPersist=True),
                    exaMockCommand("/bin/ls /etc/libvirt/qemu/\*.xml", aStdout="", aRc=1, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csPreVMChecksInstance = csPreVMChecks()
        csPreVMChecksInstance.mDetectAndRemoveStaleVMdirs(self.mGetClubox())

    def test_mDetectAndRemoveStaleVMdirs_Without_Stale_Directories_vm_maker_running(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on csPreVMChecks.mDetectAndRemoveStaleVMdirs when /bin/ls /EXAVMIMAGES/GuestImages commands failed")

        mockCommands = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test.*pgrep"),
                    exaMockCommand("test.*grep"),
                    exaMockCommand("pgrep -af 'vm_maker' | /sbin/grep -v ",
                        aStdout="3476164 vm_maker start-domain someDomainName"),
                    exaMockCommand("/bin/ls /EXAVMIMAGES/GuestImages", aStdout=_vm_dirs_without_stale_dir, aRc=0, aPersist=True),
                    exaMockCommand("/usr/bin/virsh list --all --name", aStdout=_domus, aRc=0, aPersist=True),
                    exaMockCommand("/bin/ls /etc/libvirt/qemu/\*.xml", aStdout=_libvirt_xmls, aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(mockCommands)

        csPreVMChecksInstance = csPreVMChecks()
        csPreVMChecksInstance.mDetectAndRemoveStaleVMdirs(self.mGetClubox())

if __name__ == '__main__':
    unittest.main()
