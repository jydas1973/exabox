#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cluvmrecoveryutils.py /main/4 2025/12/01 22:37:00 avimonda Exp $
#
# tests_cluvmrecoveryutils.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cluvmrecoveryutils.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    avimonda    11/10/25 - Bug 38427813 - OCI: EXACS: PROVISIONING FAILED WITH
#                           EXACLOUD ERROR CODE: 1877 EXACLOUD : ERROR IN
#                           MULTIPROCESSING(NON-ZERO EXITCODE(-9) RETURNED
#                           <PROCESSSTRUCTURE(<DOM0 NODE>, STOPPED[SIGKILL])>,
#                           ID: <DOM0 NODE>, START_TIME: <T1>, END_TIME: <T2>,
#                           MAX_TIME
#    akkar       08/18/25 - Bug 38313259: Fix RTG image copy during node
#                           recovery
#    ririgoye    07/28/25 - Enh 38232004 - Fix image lookup tests
#    akkar       04/20/25 - Creation
#

import copy
import os, re
from typing import Dict, List
import unittest
from unittest.mock import patch
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.ovm.cluvmrecoveryutils import NodeRecovery


vm_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Cell>
    <Active_bond_ib>yes</Active_bond_ib>
    <Default_gateway_device>bondeth0</Default_gateway_device>
    <Hostname>c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com</Hostname>
    <Interfaces>
        <Bridge>vmbondeth0</Bridge>
        <Gateway>10.0.0.1</Gateway>
        <Hostname>c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com</Hostname>
        <IP_address>10.0.8.185</IP_address>
        <Mac_address>02:00:17:12:15:d4</Mac_address>
        <Name>bondeth0</Name>
        <IP_enabled>yes</IP_enabled>
        <IP_ssh_listen>enabled</IP_ssh_listen>
        <Link_speed>25000</Link_speed>
        <Net_type>SCAN</Net_type>
        <Netmask>255.255.224.0</Netmask>
        <Slaves>eth1</Slaves>
        <Slaves>eth2</Slaves>
        <State>1</State>
        <Status>UP</Status>
        <Vlan_id>1</Vlan_id>
        <VSwitchNetworkParams>Vnet</VSwitchNetworkParams>
    </Interfaces>
    <Interfaces>
        <Bridge>vmbondeth0</Bridge>
        <Gateway>10.0.32.1</Gateway>
        <Hostname>c3716n11b1.backupsubnet.devx8melastic.oraclevcn.com</Hostname>
        <IP_address>10.0.38.38</IP_address>
        <Mac_address>00:00:17:00:11:3f</Mac_address>
        <Name>bondeth1</Name>
        <IP_enabled>yes</IP_enabled>
        <IP_ssh_listen>disabled</IP_ssh_listen>
        <Net_type>Other</Net_type>
        <Netmask>255.255.224.0</Netmask>
        <Slaves>eth1</Slaves>
        <Slaves>eth2</Slaves>
        <State>1</State>
        <Status>UP</Status>
        <Vlan_id>2</Vlan_id>
        <VSwitchNetworkParams>Vnet</VSwitchNetworkParams>
    </Interfaces>
    <Interfaces>
        <Bridge>dummy</Bridge>
        <Gateway>10.0.7.129</Gateway>
        <Hostname>iad103716exddu1101.localdomain</Hostname>
        <IP_address>10.0.7.185</IP_address>
        <Name>eth0</Name>
        <IP_enabled>yes</IP_enabled>
        <IP_ssh_listen>enabled</IP_ssh_listen>
        <Net_type>Other</Net_type>
        <Netmask>255.255.255.128</Netmask>
        <State>1</State>
        <Status>UP</Status>
        <nategressipaddresses>10.0.1.0/28</nategressipaddresses>
    </Interfaces>
    <Interfaces>
        <Name>re0</Name>
        <Net_type>Private</Net_type>
        <State>1</State>
        <Status>UP</Status>
    </Interfaces>
    <Interfaces>
        <Name>re1</Name>
        <Net_type>Private</Net_type>
        <State>1</State>
        <Status>UP</Status>
    </Interfaces>
    <Internal>
        <Interface_ethernet_prefix>eth</Interface_ethernet_prefix>
        <Interface_infiniband_prefix>re</Interface_infiniband_prefix>
    </Internal>
    <Nameservers>169.254.169.254</Nameservers>
    <Node_type>db</Node_type>
    <Ntp_drift>/var/lib/ntp/drift</Ntp_drift>
    <Ntp_servers>169.254.169.254</Ntp_servers>
    <System_active>non-ovs</System_active>
    <Timezone>UTC</Timezone>
    <Version>12.1.2.1.2</Version>
    <virtualMachine id="iad103716exddu1101.iad103716exd.adminiad1.oraclevcn.com_id">
        <domuName>c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com</domuName>
        <domuSimpleName>myclu1</domuSimpleName>
        <virtualMachineType>KVM</virtualMachineType>
        <Version>3</Version>
        <cpu>8</cpu>
        <maxcpu>100</maxcpu>
        <memorySize>30GB</memorySize>
        <VGExaDbExtraSpace>20</VGExaDbExtraSpace>
        <DbOraPath>/u01</DbOraPath>
        <DbOraFsType>xfs</DbOraFsType>
        <IBCardCount>2</IBCardCount>
        <disks>
            <disk id="disk_1">
                <Version>3</Version>
                <domuVersion>25.1.2.0.0.250213.1</domuVersion>
                <domuVolume>/EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.img</domuVolume>
                <domuType>iso</domuType>
                <imageType>system</imageType>
                <imageSize>default</imageSize>
                <imagePath>default</imagePath>
                <imageFileName>System.img</imageFileName>
                <diskPath>/</diskPath>
            </disk>
            <disk id="disk_2">
                <Version>3</Version>
                <domuVolume>/EXAVMIMAGES/grid-klone-Linux-x86-64-19000250121.zip</domuVolume>
                <domuType>zip</domuType>
                <imageType>none</imageType>
                <imageSize>50</imageSize>
                <imagePath>default</imagePath>
                <imageFileName>grid19.0.0.0.250121.img</imageFileName>
                <diskPath>/u01/app/19.0.0.0/grid</diskPath>
            </disk>
            <disk id="disk_3">
                <Version>3</Version>
                <domuVolume>qemu</domuVolume>
                <domuType>qemu</domuType>
                <imageType>none</imageType>
                <imageSize>20</imageSize>
                <imagePath>default</imagePath>
                <imageFileName>u01.img</imageFileName>
                <diskPath>/u01</diskPath>
            </disk>
        </disks>
        <QinQStructure>
            <Cell>
                <Hostname>c3716n11c1.clientsubnet.devx8melastic.oraclevcn.com</Hostname>
                <Interfaces>
                    <Hostname>iad103716exddu1101-stre0.iad103716exd.adminiad1.oraclevcn.com</Hostname>
                    <IP_address>100.106.136.0</IP_address>
                    <IP_enabled>yes</IP_enabled>
                    <IP_ssh_listen>disabled</IP_ssh_listen>
                    <Membership>Limited</Membership>
                    <Physdev>re0</Physdev>
                    <Intname>stre0</Intname>
                    <Netmask>255.255.0.0</Netmask>
                    <Vlan_id>551</Vlan_id>
                </Interfaces>
                <Interfaces>
                    <Hostname>iad103716exddu1101-stre1.iad103716exd.adminiad1.oraclevcn.com</Hostname>
                    <IP_address>100.106.136.1</IP_address>
                    <IP_enabled>yes</IP_enabled>
                    <IP_ssh_listen>disabled</IP_ssh_listen>
                    <Membership>Limited</Membership>
                    <Physdev>re1</Physdev>
                    <Intname>stre1</Intname>
                    <Netmask>255.255.0.0</Netmask>
                    <Vlan_id>551</Vlan_id>
                </Interfaces>
                <Interfaces>
                    <Hostname>iad103716exddu1101-clre0.iad103716exd.adminiad1.oraclevcn.com</Hostname>
                    <IP_address>100.107.32.0</IP_address>
                    <IP_enabled>yes</IP_enabled>
                    <IP_ssh_listen>disabled</IP_ssh_listen>
                    <Membership>Full</Membership>
                    <Physdev>re0</Physdev>
                    <Intname>clre0</Intname>
                    <Netmask>255.255.0.0</Netmask>
                    <Vlan_id>611</Vlan_id>
                </Interfaces>
                <Interfaces>
                    <Hostname>iad103716exddu1101-clre1.iad103716exd.adminiad1.oraclevcn.com</Hostname>
                    <IP_address>100.107.32.1</IP_address>
                    <IP_enabled>yes</IP_enabled>
                    <IP_ssh_listen>disabled</IP_ssh_listen>
                    <Membership>Full</Membership>
                    <Physdev>re1</Physdev>
                    <Intname>clre1</Intname>
                    <Netmask>255.255.0.0</Netmask>
                    <Vlan_id>611</Vlan_id>
                </Interfaces>
                <Version>3</Version>
            </Cell>
        </QinQStructure>
    </virtualMachine>
</Cell>
"""

class ebTestNodeRecovery(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestNodeRecovery, self).setUpClass(True, True)
    
    # XML parsing tests
    def test_mParseXMLForNodeRecovery(self):
        
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    exaMockCommand("/bin/cat /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com.xml", aRc=0, aStdout=vm_xml, aPersist=True)
                    
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        _xml_path = f'/EXAVMIMAGES/conf/{_domU}.xml'
        _extracted_files = _nc.mParseXMLForNodeRecovery(_dom0, _xml_path)
        self.assertEqual(['System.first.boot.25.1.2.0.0.250213.1.img', 'grid-klone-Linux-x86-64-19000250121.zip'] , _extracted_files)
        
    def test_mUpdateXMLTagValue(self):
        
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    exaMockCommand("/bin/cat /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com.xml", aRc=0, aStdout=vm_xml, aPersist=True),
                    exaMockCommand("/bin/scp /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com.xml /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com_20250422_202823.xml", aRc=0, aStdout="", aPersist=True)
                    
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        _xml_path = f'/EXAVMIMAGES/conf/{_domU}.xml'
        _new_image_path = f'/EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.2.img'
        _status = _nc.mUpdateXMLTagValue(_dom0, _xml_path, _new_image_path)
        self.assertEqual(True , _status)
        
    def test_mUpdateXMLTagValue_no_change(self):
        
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    exaMockCommand("/bin/cat /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com.xml", aRc=0, aStdout=vm_xml, aPersist=True),
                    exaMockCommand("echo *", aRc=0, aStdout="", aPersist=True),
                    
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        _xml_path = f'/EXAVMIMAGES/conf/{_domU}.xml'
        _new_image_path = f'/EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.img'
        _status = _nc.mUpdateXMLTagValue(_dom0, _xml_path, _new_image_path)
        self.assertEqual(False , _status)
        
    # Get lastest image 
    def test_mGetLatestSystemImg_empty_none(self):
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        self.assertIsNone(_nc.mGetLatestSystemImg([]))

    def test_mGetLatestSystemImg_single_image(self):
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        self.assertEqual(_nc.mGetLatestSystemImg(['System.first.boot.25.1.2.0.0.250213.1.img']), 'System.first.boot.25.1.2.0.0.250213.1.img')

    def test_multiple_images(self):  
        images = [  
            '25.1.2.0.0.250213.1.0',  
            '25.1.2.0.0.250213.2.3',  
            '25.1.2.0.0.250213.2.10',  
            '25.1.2.0.0.250213.2.9',  
        ]
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        self.assertEqual(_nc.mGetLatestSystemImg(images), '25.1.2.0.0.250213.2.10')  

    def test_mGetLatestSystemImg_non_sequential_names(self):  
        images = [  
            '25.1.2.0.0.250213.3.0',  
            '25.1.2.0.0.250213.2.9',  
            '25.1.2.0.0.250213.3.1'  
        ]
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        self.assertEqual(_nc.mGetLatestSystemImg(images), '25.1.2.0.0.250213.3.1')

    def test_mGetLatestSystemImg_duplicate_versions(self):
        images = [
            '25.1.2.0.0.250213.3.1',
            '25.1.2.0.0.250213.3.1' 
        ]
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        self.assertIn(_nc.mGetLatestSystemImg(images), images)
    
    # mCheckSystemImageOndomO
    def test_mCheckSystemImageOndomO_image_found_rtg(self):
        
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    exaMockCommand("ls /EXAVMIMAGES/System.first.boot.*.img", aRc=0, \
                                   aStdout='/EXAVMIMAGES/System.first.boot.24.1.2.0.0.250213.img\n/EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.rtg.img\n', aPersist=True)
                    
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        _sys_image_to_find = '25.1.2.0.0.250213.1'
        _sys_image_found = _nc.mGetSystemImageOndomO(_dom0)
        self.assertEqual(_sys_image_to_find, _sys_image_found)
                
    def test_mCheckSystemImageOndomO_image_found(self):
        
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    exaMockCommand("ls /EXAVMIMAGES/System.first.boot.*.img", aRc=0, \
                                   aStdout='/EXAVMIMAGES/System.first.boot.24.1.2.0.0.250213.img\n/EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.img\n', aPersist=True)
                    
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        _sys_image_to_find = f'25.1.2.0.0.250213.1'
        _sys_image_found = _nc.mGetSystemImageOndomO(_dom0)
        self.assertEqual(_sys_image_to_find, _sys_image_found)
        
    def test_mCheckSystemImageOndomO_find_latest(self):
        
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    exaMockCommand("ls /EXAVMIMAGES/System.first.boot.*.img", aRc=0, \
                                   aStdout='/EXAVMIMAGES/System.first.boot.24.1.2.0.0.250213.img\n/EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.img\n', aPersist=True)
                    
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        _sys_image_found = _nc.mGetSystemImageOndomO(_dom0)
        self.assertEqual(_sys_image_found, '25.1.2.0.0.250213.1')
               
    def test_mCheckSystemImageOndomO_no_image(self):
        
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    exaMockCommand("ls /EXAVMIMAGES/System.first.boot.*.img", aRc=0, \
                                   aStdout='', aPersist=True)
                    
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        _sys_image_found = _nc.mGetSystemImageOndomO(_dom0)
        self.assertEqual(_sys_image_found, None)
        
    # mGetSystemImage
    def test_mGetSystemImage_exactMatch_image_exist_in_dom0_rtg(self):
        """
        System.first.boot.25.1.2.0.0.250213.1.rtg.img is the required image
        present in dom0
        """
        
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.rtg.img",  aRc=0, aStdout="", aPersist=True), # copyVMImageVersionToDom0IfMissing
                    
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        cluctrl._exaBoxCluCtrl__kvm_enabled = True
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        
        _VMImagesInRepo = []
        with patch('exabox.ovm.sysimghandler.__getVMImagesInRepo', return_value=_VMImagesInRepo):
            _image_found = _nc.mGetSystemImage(_dom0, 'System.first.boot.25.1.2.0.0.250213.1.rtg.img')
            self.assertEqual(_image_found, 'System.first.boot.25.1.2.0.0.250213.1.rtg.img')
                      
    def test_mGetSystemImage_exactMatch_image_exist_dom0_kvm(self):
        """
        Set up:
        System.first.boot.25.1.2.0.0.250213.1.img is the required image
        present in dom0 but in kvm format
        """
        
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    # copyVMImageVersionToDom0IfMissing
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.rtg.img",  aRc=1, aStdout="", aPersist=True), # rtg missing
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.kvm.img",  aRc=0, aStdout="", aPersist=True), # kvm present
                    # for kvm move is requried
                    exaMockCommand("/bin/mv /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.kvm.img /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.img", aRc=0, aStdout="", aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        cluctrl._exaBoxCluCtrl__kvm_enabled = True
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        _exact_match_img = 'System.first.boot.25.1.2.0.0.250213.1.img'
        
        _VMImagesInRepo = []
        with patch('exabox.ovm.sysimghandler.__getVMImagesInRepo', return_value=_VMImagesInRepo):
            _image_found = _nc.mGetSystemImage(_dom0, _exact_match_img)
            self.assertEqual(_image_found, _exact_match_img)
            
    def test_mGetSystemImage_exactMatch_image_exist_dom0(self):
        """
        Set up:
        System.first.boot.25.1.2.0.0.250213.1.img is the required image
        present in dom0 but in img format
        """
        
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    # copyVMImageVersionToDom0IfMissing
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.rtg.img",  aRc=1, aStdout="", aPersist=True), # rtg MISSING
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.kvm.img",  aRc=1, aStdout="", aPersist=True), # kvm MISSING
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.img",  aRc=0, aStdout="", aPersist=True), # kvm MISSING
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        cluctrl._exaBoxCluCtrl__kvm_enabled = True
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        _exact_match_img = 'System.first.boot.25.1.2.0.0.250213.1.img'
        
        _VMImagesInRepo = []
        with patch('exabox.ovm.sysimghandler.__getVMImagesInRepo', return_value=_VMImagesInRepo):
            _image_found = _nc.mGetSystemImage(_dom0, _exact_match_img)
            self.assertEqual(_image_found, _exact_match_img)
            
    def test_mGetSystemImage_latest_present_in_dom0_rtg(self):
        """
        Set up:
        System.first.boot.25.1.2.0.0.250213.1.rtg.img is the required image
        missing in dom0 but more latest rtg image found in dom0
        """
        
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    # copyVMImageVersionToDom0IfMissing
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.rtg.img",  aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.kvm.img",  aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.img",  aRc=1, aStdout="", aPersist=True),
                ],
                [
                    # mGetSystemImageOndomO
                    exaMockCommand("ls /EXAVMIMAGES/System.first.boot.*.img", aRc=0, aStdout='/EXAVMIMAGES/System.first.boot.24.1.2.0.0.250213.img\n/EXAVMIMAGES/System.first.boot.26.1.2.0.0.250213.1.rtg.img\n', aPersist=True),
                ],
                [
                    # copyVMImageVersionToDom0IfMissing image present
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.26.1.2.0.0.250213.1.rtg.img",  aRc=0, aStdout="", aPersist=True),
                ],
                [
                    exaMockCommand("/bin/cat /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com-vm.xml", aRc=0, aStdout=vm_xml, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        cluctrl._exaBoxCluCtrl__kvm_enabled = True
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        _xml_img = 'System.first.boot.25.1.2.0.0.250213.1.img'
        _dom_img = 'System.first.boot.26.1.2.0.0.250213.1.rtg.img'
        _image_found = _nc.mGetSystemImage(_dom0, _xml_img)
        self.assertEqual(_image_found, _dom_img)
        
    def test_mGetSystemImage_latest_present_in_dom0_kvm(self):
        """
        System.first.boot.25.1.2.0.0.250213.1.rtg.img is the required image
        missing in dom0 but more latest kvm image found in dom0
        """
        
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    # copyVMImageVersionToDom0IfMissing
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.rtg.img",  aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.kvm.img",  aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.img",  aRc=1, aStdout="", aPersist=True),
                ],
                [
                    # mGetSystemImageOndomO
                    exaMockCommand("ls /EXAVMIMAGES/System.first.boot.*.img", aRc=0, aStdout='/EXAVMIMAGES/System.first.boot.24.1.2.0.0.250213.img\n/EXAVMIMAGES/System.first.boot.26.1.2.0.0.250213.1.img\n', aPersist=True),
                ],
                [
                    # copyVMImageVersionToDom0IfMissing image present
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.26.1.2.0.0.250213.1.rtg.img",  aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.26.1.2.0.0.250213.1.kvm.img",  aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.26.1.2.0.0.250213.1.img",  aRc=0, aStdout="", aPersist=True),
                ],
                [
                    exaMockCommand("/bin/cat /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com-vm.xml", aRc=0, aStdout=vm_xml, aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        cluctrl._exaBoxCluCtrl__kvm_enabled = True
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        _xml_img = 'System.first.boot.25.1.2.0.0.250213.1.img'
        _dom_img = 'System.first.boot.26.1.2.0.0.250213.1.img'
        _image_found = _nc.mGetSystemImage(_dom0, _xml_img)
        self.assertEqual(_image_found, _dom_img)
        
    def test_mGetSystemImage_exactMatch_missing_in_dom0_present_local_rtg(self):
        """
        Set up:
        System.first.boot.25.1.2.0.0.250213.1.rtg.img is the required image
        missing in dom0 but present in local
        """
        
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    # copyVMImageVersionToDom0IfMissing - matching image NOT present in dom0
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.rtg.img",  aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.kvm.img",  aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.img",  aRc=1, aStdout="", aPersist=True),
                    # copyVMImageVersionToDom0IfMissing - image copy from local to dom0
                    exaMockCommand("/bin/scp /u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz2 /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz", aRc=0, aStdout="", aPersist=True),\
                    exaMockCommand("/bin/test -e /sbin/pbunzip2", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/sbin/pbunzip2 /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz2", aRc=0, aStdout="", aPersist=True)
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        cluctrl._exaBoxCluCtrl__kvm_enabled = True
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        
        _VMImagesInRepo = [{'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.23.1.13.0.0.240410.1.img.bz2',
              'fileBaseName': 'System.first.boot.23.1.13.0.0.240410.1.img.bz2',
                'imgBaseName': 'System.first.boot.23.1.13.0.0.240410.1.img',
                'imgArchiveBaseName': 'System.first.boot.23.1.13.0.0.240410.1.img.bz2',
                'imgVersion': '23.1.13.0.0.240410.1', 
                'isKvmImg': False, 'isRtgImg': False, 'isArchive': True}, 
             {'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.25.1.2.0.0.250213.1.img.bz2',
              'fileBaseName': 'System.first.boot.25.1.2.0.0.250213.1.img.bz2', 
              'imgBaseName': 'System.first.boot.25.1.2.0.0.250213.1.img', 
              'imgArchiveBaseName': 'System.first.boot.25.1.2.0.0.250213.1.img.bz2', 
              'imgVersion': '25.1.2.0.0.250213.1', 'isKvmImg': False, 'isRtgImg': False, 'isArchive': True}, 
             {'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.25.1.2.0.0.250213.1.kvm.img.bz2', 
              'fileBaseName': 'System.first.boot.25.1.2.0.0.250213.1.kvm.img.bz2', 
              'imgBaseName': 'System.first.boot.25.1.2.0.0.250213.1.kvm.img', 
              'imgArchiveBaseName': 'System.first.boot.25.1.2.0.0.250213.1.kvm.img.bz2', 
              'imgVersion': '25.1.2.0.0.250213.1', 'isKvmImg': True, 'isRtgImg': False, 'isArchive': True}, 
             {'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz2', 
              'fileBaseName': 'System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz2', 
              'imgBaseName': 'System.first.boot.25.1.2.0.0.250213.1.rtg.img', 
              'imgArchiveBaseName': 'System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz2', 
              'imgVersion': '25.1.2.0.0.250213.1', 'isKvmImg': False, 'isRtgImg': True, 'isArchive': True}
             ]
        with patch('exabox.ovm.sysimghandler.__getVMImagesInRepo', return_value=_VMImagesInRepo), \
            patch('exabox.utils.node.exaBoxNode.mCompareFiles', return_value=True):
            _image_found = _nc.mGetSystemImage(_dom0, 'System.first.boot.25.1.2.0.0.250213.1.img')
            self.assertEqual(_image_found, 'System.first.boot.25.1.2.0.0.250213.1.rtg.img')
            
    def test_mGetSystemImage_exactMatch_missing_in_dom0_present_local_kvm(self):
        """
        Set up:
        System.first.boot.25.1.2.0.0.250213.1.rtg.img is the required image
        missing in dom0 and local , only kvm is present in local
        """
        
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    exaMockCommand("/bin/cat /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com-vm.xml", aRc=0, aStdout=vm_xml, aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.rtg.img",  aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.kvm.img",  aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.img", aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/scp /u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.25.1.2.0.0.250213.1.kvm.img.bz2 /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.kvm.img.bz2", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/pbunzip2", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/sbin/pbunzip2 /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.kvm.img.bz2", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/mv /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.kvm.img /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.img",  aRc=0, aStdout="", aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        cluctrl._exaBoxCluCtrl__kvm_enabled = True
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        
        _VMImagesInRepo = [{'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.23.1.13.0.0.240410.1.img.bz2',
              'fileBaseName': 'System.first.boot.23.1.13.0.0.240410.1.img.bz2',
                'imgBaseName': 'System.first.boot.23.1.13.0.0.240410.1.img',
                'imgArchiveBaseName': 'System.first.boot.23.1.13.0.0.240410.1.img.bz2',
                'imgVersion': '23.1.13.0.0.240410.1', 
                'isKvmImg': False, 'isRtgImg': False, 'isArchive': True}, 
             {'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.25.1.2.0.0.250213.1.img.bz2',
              'fileBaseName': 'System.first.boot.25.1.2.0.0.250213.1.img.bz2', 
              'imgBaseName': 'System.first.boot.25.1.2.0.0.250213.1.img', 
              'imgArchiveBaseName': 'System.first.boot.25.1.2.0.0.250213.1.img.bz2', 
              'imgVersion': '25.1.2.0.0.250213.1', 'isKvmImg': False, 'isRtgImg': False, 'isArchive': True}, 
             {'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.25.1.2.0.0.250213.1.kvm.img.bz2', 
              'fileBaseName': 'System.first.boot.25.1.2.0.0.250213.1.kvm.img.bz2', 
              'imgBaseName': 'System.first.boot.25.1.2.0.0.250213.1.kvm.img', 
              'imgArchiveBaseName': 'System.first.boot.25.1.2.0.0.250213.1.kvm.img.bz2', 
              'imgVersion': '25.1.2.0.0.250213.1', 'isKvmImg': True, 'isRtgImg': False, 'isArchive': True},
             ]
        with patch('exabox.ovm.sysimghandler.__getVMImagesInRepo', return_value=_VMImagesInRepo),\
            patch('exabox.utils.node.exaBoxNode.mCompareFiles', return_value=True):
            _image_found = _nc.mGetSystemImage(_dom0, 'System.first.boot.25.1.2.0.0.250213.1.rtg.img')
            self.assertEqual(_image_found, 'System.first.boot.25.1.2.0.0.250213.1.img')
    
    # mVerifySystemAndGridImages
    def test_mVerifySystemAndGridImages_exactMatch_present_in_dom0_xml_update(self):
        """
        Set up:
        System.first.boot.25.1.2.0.0.250213.1.rtg.img is the required image
        present in dom0
        Grid image exists
        """
        
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    # mParseXMLForNodeRecovery
                    exaMockCommand("/bin/cat /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com-vm.xml", aRc=0, aStdout=vm_xml, aPersist=True) # Read the XMl
                    
                ],
                [
                    #mGetSystemImage
                    # copyVMImageVersionToDom0IfMissing - image exist in dom0
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.rtg.img",  aRc=0, aStdout="", aPersist=True),
                ],
                [
                    exaMockCommand("/bin/cat /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com-vm.xml", aRc=0, aStdout=vm_xml, aPersist=True), # mUpdateXMLTagValue
                ],
                [
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/grid-klone-Linux-x86-64-19000250121.zip", aRc=0, aStdout="", aPersist=True), #mCheckGridImageOndomO
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        cluctrl._exaBoxCluCtrl__kvm_enabled = True
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        
        _VMImagesInRepo = [] # no need if image found in dom0
        with patch('exabox.ovm.sysimghandler.__getVMImagesInRepo', return_value=_VMImagesInRepo):
            _nc.mVerifySystemAndGridImages(_dom0, _domU)

    
    def test_mVerifySystemAndGridImages_get_grid_image(self):
        _grid_list_dom0 = """
            /EXAVMIMAGES/grid-klone-Linux-x86-64-19000240116.zip
            /EXAVMIMAGES/grid-klone-Linux-x86-64-19000240416.zip
            /EXAVMIMAGES/grid-klone-Linux-x86-64-19000240716.zip
            /EXAVMIMAGES/grid-klone-Linux-x86-64-19000241015.zip
            /EXAVMIMAGES/grid-klone-Linux-x86-64-19000250121.zip
            /EXAVMIMAGES/grid-klone-Linux-x86-64-192200240116.zip
            /EXAVMIMAGES/grid-klone-Linux-x86-64-192300240416.zip
            /EXAVMIMAGES/grid-klone-Linux-x86-64-192400240716.zip
            /EXAVMIMAGES/grid-klone-Linux-x86-64-192500241015.zip
            /EXAVMIMAGES/grid-klone-Linux-x86-64-192600250121.zip
            /EXAVMIMAGES/grid-klone-Linux-x86-64-23000240118.zip
            /EXAVMIMAGES/grid-klone-Linux-x86-64-23000240716.zip
            /EXAVMIMAGES/grid-klone-Linux-x86-64-23000241015.zip
            /EXAVMIMAGES/grid-klone-Linux-x86-64-23000250121.zip
            /EXAVMIMAGES/grid-klone-Linux-x86-64-23400240118.zip
            /EXAVMIMAGES/grid-klone-Linux-x86-64-23500240716.zip
            /EXAVMIMAGES/grid-klone-Linux-x86-64-23600241015.zip
            /EXAVMIMAGES/grid-klone-Linux-x86-64-23700250121.zip
        """
        
        _cmds = {
            self.mGetRegexDom0():
            [
                [
                    # mParseXMLForNodeRecovery
                    exaMockCommand("/bin/cat /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com-vm.xml", aRc=0, aStdout=vm_xml, aPersist=True),
                    
                ],
                [
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.rtg.img",  aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.kvm.img",  aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.img", aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/scp /u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz2 /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz2", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("ls /EXAVMIMAGES/System.first.boot.*.img", aRc=0, aStdout='', aPersist=True),
                ],
                [
                    exaMockCommand("/bin/cat /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com-vm.xml", aRc=0, aStdout=vm_xml, aPersist=True),
                    exaMockCommand("/bin/scp /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com.xml /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com_20250422_202823.xml", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/pbunzip2", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/sbin/pbunzip2 /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz2", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/mv /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz2 /EXAVMIMAGES/System.first.boot.26.1.2.0.0.250213.1.img", aRc=0, aStdout="", aPersist=True),
                ],
                [
                    
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/grid-klone-Linux-x86-64-19000250121.zip", aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.img", aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.26.1.2.0.0.250213.1.kvm.img",  aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.26.1.2.0.0.250213.1.rtg.img",  aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.rtg.img",  aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.kvm.img",  aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/mv /EXAVMIMAGES/System.first.boot.26.1.2.0.0.250213.1.kvm.img /EXAVMIMAGES/System.first.boot.26.1.2.0.0.250213.1.img", aRc=0, aStdout="", aPersist=True)
                ],
                [
                    exaMockCommand('ls\\ -1\\ /EXAVMIMAGES/grid\\-klone\\-Linux\\-x86\\-64\\-\\*\\.zip', aRc=0, aStdout=_grid_list_dom0, aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/grid-klone-Linux-x86-64-19000250121.zip", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.26.1.2.0.0.250213.1.rtg.img",  aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.26.1.2.0.0.250213.1.kvm.img",  aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.26.1.2.0.0.250213.1.img",  aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/cat /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com-vm.xml", aRc=0, aStdout=vm_xml, aPersist=True),
                    exaMockCommand("/bin/scp /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com.xml /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com_20250422_202823.xml", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/scp /u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.26.1.2.0.0.250213.1.kvm.img.bz2 /EXAVMIMAGES/System.first.boot.26.1.2.0.0.250213.1.kvm.img.bz2", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /sbin/pbunzip2", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/sbin/pbunzip2 /EXAVMIMAGES/System.first.boot.26.1.2.0.0.250213.1.kvm.img.bz2", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/mv /EXAVMIMAGES/System.first.boot.26.1.2.0.0.250213.1.kvm.img /EXAVMIMAGES/System.first.boot.26.1.2.0.0.250213.1.img", aRc=0, aStdout="", aPersist=True),
                ],
                [
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/grid-klone-Linux-x86-64-19000250121.zip", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/cat /EXAVMIMAGES/conf/scaqab10client01vm08.us.oracle.com-vm.xml", aRc=0, aStdout=vm_xml, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        cluctrl._exaBoxCluCtrl__kvm_enabled = True
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        
        _VMImagesInRepo = [{'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.23.1.13.0.0.240410.1.img.bz2',
              'fileBaseName': 'System.first.boot.23.1.13.0.0.240410.1.img.bz2',
                'imgBaseName': 'System.first.boot.23.1.13.0.0.240410.1.img',
                'imgArchiveBaseName': 'System.first.boot.23.1.13.0.0.240410.1.img.bz2',
                'imgVersion': '23.1.13.0.0.240410.1',
                'isKvmImg': False, 'isRtgImg': False, 'isArchive': True},
             {'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.25.1.2.0.0.250213.1.img.bz2',
              'fileBaseName': 'System.first.boot.25.1.2.0.0.250213.1.img.bz2',
              'imgBaseName': 'System.first.boot.25.1.2.0.0.250213.1.img',
              'imgArchiveBaseName': 'System.first.boot.25.1.2.0.0.250213.1.img.bz2',
              'imgVersion': '25.1.2.0.0.250213.1', 'isKvmImg': False, 'isRtgImg': False, 'isArchive': True}, 
             {'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.26.1.2.0.0.250213.1.kvm.img.bz2', 
              'fileBaseName': 'System.first.boot.26.1.2.0.0.250213.1.kvm.img.bz2', 
              'imgBaseName': 'System.first.boot.26.1.2.0.0.250213.1.kvm.img', 
              'imgArchiveBaseName': 'System.first.boot.26.1.2.0.0.250213.1.kvm.img.bz2', 
              'imgVersion': '26.1.2.0.0.250213.1', 'isKvmImg': True, 'isRtgImg': False, 'isArchive': True}, 
             {'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz2', 
              'fileBaseName': 'System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz2', 
              'imgBaseName': 'System.first.boot.25.1.2.0.0.250213.1.rtg.img', 
              'imgArchiveBaseName': 'System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz2', 
              'imgVersion': '25.1.2.0.0.250213.1', 'isKvmImg': False, 'isRtgImg': True, 'isArchive': True}
             ]
        with patch('exabox.ovm.sysimghandler.__getVMImagesInRepo', return_value=_VMImagesInRepo):
            _nc.mVerifySystemAndGridImages(_dom0, _domU)

    
if __name__ == '__main__':
    unittest.main() 
