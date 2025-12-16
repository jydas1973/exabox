#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/vmcmd/tests_vmstatus.py /main/1 2022/09/15 23:13:07 jfsaldan Exp $
#
# tests_vmstatus.py
#
# Copyright (c) 2022, Oracle and/or its affiliates.
#
#    NAME
#      tests_vmstatus.py - <one-line expansion of the name>
#
#    DESCRIPTION
#     Test file for clucontrol method mGetVMStatus()
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    09/05/22 - Creation
#

import unittest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.MockCommand import exaMockCommand
from exabox.utils.node import connect_to_host
from exabox.core.Context import get_gcontext

class ebTestVMStatus(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.maxDiff = None

    def template_test_xen_vm(self, aRc:int, aXenState:str):
        """
        Template method to test clucontrol.mGetVMStatus
        """

        # Mock commands
        _cmds = {
            self.mGetRegexDom0():[
                [
                exaMockCommand("test -e .*", aRc=0),
                exaMockCommand("xm domstate scaqab10.*", aRc=aRc,
                    aStdout=aXenState)
                ]
            ]
        }

        # Init new Args
        self.mPrepareMockCommands(_cmds)

        _results = []
        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():
            with connect_to_host(_dom0, get_gcontext()) as _node:
                _results.append(self.mGetClubox().mGetVMStatus(_node, _domU))
        return _results

    def test_xen_vm_running(self):

        self.assertEqual(["running", "running"],
                self.template_test_xen_vm(0, "running\n "))

    def test_xen_vm_iddle(self):
        self.assertEqual(["iddle", "iddle"],
                self.template_test_xen_vm(0, "iddle\n "))

    def test_xen_vm_iddle_error(self):
        self.assertEqual(["", ""],
                self.template_test_xen_vm(1, "iddle\n "))

    def test_xen_vm_runnig_error(self):
        self.assertEqual(["", ""],
                self.template_test_xen_vm(1, "running\n "))

    def template_test_kvm_vm(self, aRc:int, aKvmState:str):
        """
        Template method to test clucontrol.mGetVMStatus
        """

        # Mock commands
        _cmds = {
            self.mGetRegexDom0():[
                [
                exaMockCommand("test -e .*", aRc=0),
                exaMockCommand("virsh domstate scaqab10.*", aRc=aRc,
                    aStdout=aKvmState)
                ]
            ]
        }

        # Init new Args
        self.mPrepareMockCommands(_cmds)
        self.mGetContext().mSetConfigOption("enable_kvm", "True")

        _results = []
        _expected = []
        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():
            with connect_to_host(_dom0, get_gcontext()) as _node:
                _results.append(self.mGetClubox().mGetVMStatus(_node, _domU))
        return _results

    def test_kvm_vm_running(self):

        self.assertEqual(["running", "running"],
                self.template_test_xen_vm(0, "running\n "))

    def test_kvm_vm_iddle(self):
        self.assertEqual(["iddle", "iddle"],
                self.template_test_xen_vm(0, "iddle\n "))

    def test_kvm_vm_iddle_error(self):
        self.assertEqual(["", ""],
                self.template_test_xen_vm(1, "iddle\n "))

    def test_kvm_vm_running_error(self):
        self.assertEqual(["", ""],
                self.template_test_xen_vm(1, "running\n "))

if __name__ == '__main__':
    unittest.main()

