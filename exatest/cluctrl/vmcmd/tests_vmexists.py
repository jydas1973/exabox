#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/vmcmd/tests_vmexists.py /main/1 2021/05/17 02:22:31 aypaul Exp $
#
# tests_vmexists.py
#
# Copyright (c) 2021, Oracle and/or its affiliates. 
#
#    NAME
#      tests_vmexists.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      05/06/21 - Creation
#
import unittest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo

class ebTestVMExists(ebTestClucontrol):
   
    @classmethod
    def setUpClass(self):
        super(ebTestVMExists, self).setUpClass(False, False)

    def template_VMExists(self, aDom0, aDomU):
        '''
            Test mCheckIfVMExists()
        '''     
        #Prepare env variables
        ebLogInfo("")
        ebLogInfo("Current dom0: {0}, domU: {1}".format(aDom0, aDomU))
        _expected_rc = True
        _expectedDomU = None
        if aDom0 is None or aDomU is None:
            _expected_rc = False
        for _dom0, _domU in self.mGetClubox().mReturnDom0DomUPair():
            if aDom0 == _dom0:
                _expectedDomU = _domU
            if aDom0 == _dom0 and aDomU != _domU:
                _expected_rc = False

        _returnCode = (0 if _expected_rc is True else 1)
        _xmList = """Name                                        ID   Mem VCPUs      State   Time(s)
Domain-0                                     0  8746     4     r----- 2145201.6
{0}              1 92163    10     -b---- 811282.1""".format(_expectedDomU)
        #Create args structure
        if aDom0 is not None and aDomU is not None:
            _cmds = {
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("imageinfo | grep 'Node type:'"),
                        exaMockCommand("cat /sys/hypervisor/type", aStdout="xen\n")
                    ],
                    [
                        exaMockCommand("xm list", aStdout=_xmList),
                        exaMockCommand("virsh list", aStdout="81    {0}   running".format(aDomU))
                    ]
                ]
            }

            # Init new Args
            self.mPrepareMockCommands(_cmds)
        
        # Execute Clucontrol functions
        """dom0 : scaqab10adm01.us.oracle.com, domU: scaqab10client01vm08.us.oracle.com
           dom0 : scaqab10adm02.us.oracle.com, domU: scaqab10client02vm08.us.oracle.com"""

        
        _doesVMExist = self.mGetClubox().mCheckIfVMExists( aDomU, aDom0)
        ebLogInfo("My function returns: {0}".format(_doesVMExist))
        self.assertEqual(_doesVMExist, _expected_rc)

    def test_dom0None(self):
        self.template_VMExists(None, "scaqab10client01vm08.us.oracle.com")

    def test_domUNone(self):
        self.template_VMExists("scaqab10adm01.us.oracle.com", None)
    
    def test_validDomU1(self):
        self.template_VMExists("scaqab10adm01.us.oracle.com", "scaqab10client01vm08.us.oracle.com")
    
    def test_validDomU2(self):
        self.template_VMExists("scaqab10adm02.us.oracle.com", "scaqab10client02vm08.us.oracle.com")

    def test_invalidDomU(self):
        self.template_VMExists("scaqab10adm01.us.oracle.com", "scaqab10client02vm08.us.oracle.com")

if __name__ == "__main__":
    unittest.main()

