#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/tests_cs_installcluster.py /main/7 2025/08/25 06:17:10 pbellary Exp $
#
# tests_cs_installcluster.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_installcluster.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    bhpati      06/03/25 - Bug 37906334 - Add option for force shutdown of
#                           domU in parallel
#    naps        02/18/25 - Bug 37492116 - UT for bug 37492116 .
#    jesandov    04/14/23 - Backport 35294394 of jesandov_bug-35264867 from
#                           main
#    joysjose    04/10/23 - 35264867: Correction on RDS ping cellinit IP retrieval.
#    joysjose    10/03/22 - Unit Test for cs_installcluster.py file added as
#                           part of rds-ping feature
#    joysjose    10/03/22 - Creation
#

import unittest
import copy

from unittest.mock import patch, MagicMock

from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.csstep.cs_installcluster import csInstallCluster
from exabox.ovm.vmcontrol import exaBoxOVMCtrl, ebVgLifeCycle

OUT0 = """
'/etc/sysconfig/network-scripts/ifcfg-stib0'
'/etc/sysconfig/network-scripts/ifcfg-stib1'"""

OUT1 = """
/etc/sysconfig/network-scripts/ifcfg-stre0
/etc/sysconfig/network-scripts/ifcfg-stre1
/etc/sysconfig/network-scripts/ifcfg-clre0
/etc/sysconfig/network-scripts/ifcfg-clre1"""

out2 = """    ipaddress1=192.168.12.9/23"""
out3 = """    ipaddress2=192.168.12.10/23"""
out4 = """'ipaddress1=192.168.12.9/23'
'ipaddress2=192.168.12.10/23'"""
out5 = """'ipaddress1=192.168.12.11/23'
'ipaddress2=192.168.12.12/23'"""

class testOptions(object): pass

class ebTestCSInstallCluster(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCSInstallCluster, self).setUpClass(True,True)

   
    def test_getIPDictKVM_storage_interface_domu(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for csInstallCluster.rdsPingDriver")

        mockCommands = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /bin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/ls",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/find",aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev clre0 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out4,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev clre1 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out5,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stre0 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out4,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stre1 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out5,aRc=0, aPersist=True),
                    exaMockCommand("find /etc -name cellinit.ora", aStdout="/etc/cellinit.ora",aRc=0, aPersist=True),
                    exaMockCommand("grep -E 'ipaddress1|ipaddress2'", aStdout=out4,aRc=0, aPersist=True),
                    exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*", aStdout = OUT1, aRc=0, aPersist=True)
                ]
            ]
            
        }
        self.mPrepareMockCommands(mockCommands)
        csInstallClusterInstance = csInstallCluster()
        _ebox = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True):
            _domUClusterIPDict = {}
            _cellinitiplist=[]
            for _,aDomU in  _ebox.mReturnDom0DomUPair():
                self.assertEqual(csInstallClusterInstance.getIPDict(self.mGetClubox(),aDomU,_domUClusterIPDict,"storage_interface",_cellinitiplist, "DOMU"), None)
                

    def test_getIPDictXEN_storage_interface_domu(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for csInstallCluster.rdsPingDriver")

        mockCommands = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /bin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/ls",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/find",aRc=0, aPersist=True),
                    exaMockCommand("/bin/find /etc -name cellinit.ora", aStdout=out2,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev clre0 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out4,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev clre1 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out5,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stib0 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out4,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stib1 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out5,aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /opt/oracle/cell21.2.11.0.0_LINUX.X64_220414.1/cellsrv/deploy/config/cellinit.ora | grep -E 'ipaddress1|ipaddress2' ", aStdout= out3, aRc=0),
                    exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*", aStdout = OUT1, aRc=0, aPersist=True)
                ]
            ]
            
        }
        self.mPrepareMockCommands(mockCommands)
        csInstallClusterInstance = csInstallCluster()
        _ebox = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=False):
            try:
                _domUClusterIPDict = {}
                _cellinitiplist=[]
                for _,aDomU in  _ebox.mReturnDom0DomUPair():
                    self.assertEqual(csInstallClusterInstance.getIPDict(self.mGetClubox(),aDomU,_domUClusterIPDict,"storage_interface",_cellinitiplist, "DOMU"),None)
            except:
                ebLogInfo("Exception Caught..")
            

    def test_getIPDictKVM_storage_interface_cells(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for csInstallCluster.rdsPingDriver")

        mockCommands = {
            self.mGetRegexCell():[
                [
                    exaMockCommand("/bin/test -e /bin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/ls",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/find",aRc=0, aPersist=True),
                    exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*", aStdout = OUT1, aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stre0 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out4,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stre1 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out5,aRc=0, aPersist=True),
                    exaMockCommand("cellcli.*ipaddress1", aStdout=out2,aRc=0, aPersist=True),
                    exaMockCommand("cellcli.*ipaddress2", aStdout=out3,aRc=0, aPersist=True),
                ]
            ]
            
        }
        self.mPrepareMockCommands(mockCommands)
        csInstallClusterInstance = csInstallCluster()
        _ebox = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True):
            _domUClusterIPDict = {}
            _cellinitiplist=[]
            for _cell in _ebox.mReturnCellNodes().keys():
                self.assertEqual(csInstallClusterInstance.getIPDict(self.mGetClubox(),_cell,_domUClusterIPDict,"storage_interface",_cellinitiplist, "CELL"),None)

    def test_getIPDictXEN_storage_interface_cells(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for csInstallCluster.rdsPingDriver")

        mockCommands = {
            self.mGetRegexCell():[
                [
                    exaMockCommand("/bin/test -e /bin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/ls",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/find",aRc=0, aPersist=True),
                    exaMockCommand("/bin/find /etc -name cellinit.ora", aStdout=out2,aRc=0, aPersist=True),
                    exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*", aStdout = OUT1, aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stre0 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out4,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stre1 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out5,aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /opt/oracle/cell21.2.11.0.0_LINUX.X64_220414.1/cellsrv/deploy/config/cellinit.ora | grep -E 'ipaddress1|ipaddress2' ", aStdout= out3, aRc=0),
                ]
            ]
            
        }
        self.mPrepareMockCommands(mockCommands)
        csInstallClusterInstance = csInstallCluster()
        _ebox = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=False):
            try:
                _domUClusterIPDict = {}
                _cellinitiplist=[]
                for _cell in _ebox.mReturnCellNodes().keys():
                    self.assertEqual(csInstallClusterInstance.getIPDict(self.mGetClubox(),_cell,_domUClusterIPDict,"storage_interface",_cellinitiplist, "DOMU"),None)
            except:
                ebLogInfo("Exception Caught..")


    def test_getIPDictKVM_cluster_interface_domu(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for csInstallCluster.rdsPingDriver")

        mockCommands = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /bin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/ls",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/find",aRc=0, aPersist=True),
                    exaMockCommand("/bin/find /etc -name cellinit.ora", aStdout=out2,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev clre0 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out4,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev clre1 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out5,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stre0 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out4,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stre1 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out5,aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /opt/oracle/cell21.2.11.0.0_LINUX.X64_220414.1/cellsrv/deploy/config/cellinit.ora | grep -E 'ipaddress1|ipaddress2' ", aStdout= out3, aRc=0),
                    exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*", aStdout = OUT1, aRc=0, aPersist=True)
                ]
            
            ]
        }
        self.mPrepareMockCommands(mockCommands)
        csInstallClusterInstance = csInstallCluster()
        _ebox = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True):
            _domUClusterIPDict = {}
            _cellinitiplist=None
            for _,aDomU in  _ebox.mReturnDom0DomUPair():
                self.assertEqual(csInstallClusterInstance.getIPDict(self.mGetClubox(),aDomU,_domUClusterIPDict,"cluster_interface",_cellinitiplist, "DOMU"),None)

    def test_getIPDictXEN_cluster_interface_domu(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for csInstallCluster.rdsPingDriver")

        mockCommands = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /bin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/ls",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/find",aRc=0, aPersist=True),
                    exaMockCommand("/bin/find /etc -name cellinit.ora", aStdout=out2,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev clre0 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out4,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev clre1 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out5,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stre0 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out4,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stre1 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out5,aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /opt/oracle/cell21.2.11.0.0_LINUX.X64_220414.1/cellsrv/deploy/config/cellinit.ora | grep -E 'ipaddress1|ipaddress2' ", aStdout= out3, aRc=0),
                    exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*", aStdout = OUT1, aRc=0, aPersist=True)
                ]
            
            ]
        }
        self.mPrepareMockCommands(mockCommands)
        csInstallClusterInstance = csInstallCluster()
        _ebox = self.mGetClubox()
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=False):
            _domUClusterIPDict = {}
            _cellinitiplist=None
            for _,aDomU in  _ebox.mReturnDom0DomUPair():
                self.assertEqual(csInstallClusterInstance.getIPDict(self.mGetClubox(),aDomU,_domUClusterIPDict,"cluster_interface",_cellinitiplist, "DOMU"),None)

    

    def test_rdsPingDriverKVM(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for csInstallCluster.rdsPingDriver")

        mockCommands = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /bin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/ls",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/find",aRc=0, aPersist=True),
                    exaMockCommand("/bin/find /etc -name cellinit.ora", aStdout=out2,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stre0 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out4,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stre1 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out5,aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /opt/oracle/cell21.2.11.0.0_LINUX.X64_220414.1/cellsrv/deploy/config/cellinit.ora | grep -E 'ipaddress1|ipaddress2' ", aStdout= out3, aRc=0),
                    exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*", aStdout = OUT1, aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/bin/test -e /bin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/ls",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/find",aRc=0, aPersist=True),
                    exaMockCommand("/bin/find /etc -name cellinit.ora", aStdout=out2,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stre0 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out4, aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stre1 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out5, aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /opt/oracle/cell21.2.11.0.0_LINUX.X64_220414.1/cellsrv/deploy/config/cellinit.ora | grep -E 'ipaddress1|ipaddress2' ", aStdout= out3, aRc=0),
                    exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*", aStdout = OUT1, aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexCell():[
                [
                    exaMockCommand("/bin/test -e /bin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/ls",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/find",aRc=0, aPersist=True),
                    exaMockCommand("/bin/find /etc -name cellinit.ora", aStdout=out2,aRc=0, aPersist=True),
                    exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*", aStdout = OUT1, aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stre0 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out4,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stre1 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out5,aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /opt/oracle/cell21.2.11.0.0_LINUX.X64_220414.1/cellsrv/deploy/config/cellinit.ora | grep -E 'ipaddress1|ipaddress2' ", aStdout= out3, aRc=0),




                ]
            ],
        }
        self.mPrepareMockCommands(mockCommands)
        csInstallClusterInstance = csInstallCluster()
        try:
            with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=True):
                csInstallClusterInstance.rdsPingDriver(self.mGetClubox())
        except:
            ebLogInfo("Exception Caught..")

    def test_rdsPingDriverXEN(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for csInstallCluster.rdsPingDriver")

        mockCommands = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /bin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/ls",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/find",aRc=0, aPersist=True),
                    exaMockCommand("/bin/find /etc -name cellinit.ora", aStdout=out2,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stib0 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out4,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stib1 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out5,aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /opt/oracle/cell21.2.11.0.0_LINUX.X64_220414.1/cellsrv/deploy/config/cellinit.ora | grep -E 'ipaddress1|ipaddress2' ", aStdout= out3, aRc=0),
                    exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*", aStdout = OUT1, aRc=0, aPersist=True)
                ],
                [
                    exaMockCommand("/bin/test -e /bin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/ls",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/find",aRc=0, aPersist=True),
                    exaMockCommand("/bin/find /etc -name cellinit.ora", aStdout=out2,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stib0 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out4, aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stib1 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out5, aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /opt/oracle/cell21.2.11.0.0_LINUX.X64_220414.1/cellsrv/deploy/config/cellinit.ora | grep -E 'ipaddress1|ipaddress2' ", aStdout= out3, aRc=0),
                    exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*", aStdout = OUT1, aRc=0, aPersist=True)
                ]
            ],
            self.mGetRegexCell():[
                [
                    exaMockCommand("/bin/test -e /bin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/ls",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/ip",aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /bin/find",aRc=0, aPersist=True),
                    exaMockCommand("/bin/find /etc -name cellinit.ora", aStdout=out2,aRc=0, aPersist=True),
                    exaMockCommand("/bin/ls /etc/sysconfig/network-scripts/ifcfg-*", aStdout = OUT1, aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stre0 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out4,aRc=0, aPersist=True),
                    exaMockCommand("ip addr show dev stre1 | grep 'inet' | cut -d: -f2 | awk '{print $2}'", aStdout=out5,aRc=0, aPersist=True),
                    exaMockCommand("/bin/cat /opt/oracle/cell21.2.11.0.0_LINUX.X64_220414.1/cellsrv/deploy/config/cellinit.ora | grep -E 'ipaddress1|ipaddress2' ", aStdout= out3, aRc=0),




                ]
            ],
        }
        self.mPrepareMockCommands(mockCommands)
        csInstallClusterInstance = csInstallCluster()
        try:
            with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsKVM', return_value=False):
                csInstallClusterInstance.rdsPingDriver(self.mGetClubox())
        except:
            ebLogInfo("Exception Caught..")



    def test_patchKVMGuestCfg(self):
        _cmds = {
                    self.mGetRegexDom0(): [
                        [
                           exaMockCommand("/opt/exadata_ovm/vm_maker --list --disk-image --domain *", aRc=1, aPersist=True)
                        ]
                    ],
                    self.mGetRegexVm(): [
                        [
                           exaMockCommand("chown -fR oracle.oinstall*", aRc=1, aPersist=True)
                        ]
                    ]
                }

        self.mPrepareMockCommands(_cmds)
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mDyndepFilesList', return_value=(None, None), aPersist=True),\
             patch('exabox.ovm.clucontrol.mBuildAndAttachU02DiskKVM', return_value=0, aPersist=True):
                self.mGetClubox().patchKVMGuestCfg()

    def test_mConfigureShmAll(self):
        _cmds = {
                    self.mGetRegexVm(): [
                        [
                           exaMockCommand("getconf PAGE_SIZE", aRc=0,  aStdout="4096", aPersist=True),
                           exaMockCommand("/bin/echo .* > /proc/sys/kernel/shmall", aRc=0, aPersist=True)
                        ]
                    ]
                }

        self.mPrepareMockCommands(_cmds)
        with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetSysCtlConfigValue', return_value=(None, 180000432947), aPersist=True),\
             patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetSysCtlConfigValue', aPersist=True):
                self.mGetClubox().mConfigureShmAll()

    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mPatchVMCfgBeforeBoot")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mParallelDomUShutdown")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mPatchVMCfgOnShutdown")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mParallelDomUStart")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mPatchVMCfgAfterBoot")
    def test_mPatchVMCfg(self, mock_mPatchVMCfgAfterBoot, mock_mParallelDomUStart, mock_mPatchVMCfgOnShutdown, mock_mParallelDomUShutdown, mock_mPatchVMCfgBeforeBoot):
        # Call the function being tested
        _ddpair = [('dom0', 'domU')]
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        with patch('exabox.ovm.clucontrol.time.sleep'),\
            patch('exabox.ovm.clucontrol.ProcessManager.mStartAppend'),\
            patch("exabox.ovm.clucontrol.ProcessManager.mJoinProcess"):
            self.mGetClubox().mPatchVMCfg(_options)
        
        # Assert the expected behavior or result
        mock_mPatchVMCfgBeforeBoot.assert_called_once()
        mock_mParallelDomUShutdown.assert_called_once()
        mock_mPatchVMCfgOnShutdown.assert_called_once()
        mock_mParallelDomUStart.assert_called_once()
        mock_mPatchVMCfgAfterBoot.assert_called_once()

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCellsServicesUp', return_value=False)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRunScript')
    @patch('exabox.ovm.csstep.cs_util.csUtil.mExecuteOEDAStep')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateDepFiles')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mConfigureSyslogIlomHost')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPatchVMCfg')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mConfigureShmAll')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetCachingPolicyRecoGD')
    def test_undoExecute(self, mock_mSetCachingPolicyRecoGD, mock_mConfigureShmAll, mock_mPatchVMCfg, 
                         mock_mConfigureSyslogIlomHost, mock_mUpdateDepFiles, mock_mExecuteOEDAStep,
                         mock_mRunScript, mock_mCheckCellsServicesUp):
        _ebox = self.mGetClubox()
        _ebox.mSetEnableKVM(True)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _step_list = ["ESTP_INSTALL_CLUSTER"]

        _handler = csInstallCluster()
        _handler.doExecute(_ebox, _options, _step_list)

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCellsServicesUp', return_value=False)
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRunScript')
    @patch('exabox.ovm.csstep.cs_util.csUtil.mExecuteOEDAStep')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mDetachU02')
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mIsEDVImageSupported', return_value=True)
    def test_undoExecute(self, mock_mIsEDVSupported, mock_mDetachU02, mock_mExecuteOEDAStep,
                         mock_mRunScript, mock_mCheckCellsServicesUp):
        _ebox = self.mGetClubox()
        _ebox.mSetEnableKVM(True)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _step_list = ["ESTP_INSTALL_CLUSTER"]

        _handler = csInstallCluster()
        _handler.undoExecute(_ebox, _options, _step_list)

if __name__ == '__main__':
    unittest.main() 
