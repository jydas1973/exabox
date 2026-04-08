#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_cluvmrecoveryutils.py jesandov_bug-38358445/1 2026/02/09 14:27:25 jesandov Exp $
#
# tests_cluvmrecoveryutils.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
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
#    prsshukl    01/26/26 - Bug 38841393 - Codex -> increase code coverage of 
#                           exabox/ovm/cluvmrecoveryutils.py
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
from unittest.mock import patch, MagicMock, call
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError, gNodeElasticError
from exabox.ovm.cluvmrecoveryutils import NodeRecovery, QuorumDiskManager


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

    # Auto-generated test for mNormalizeHost
    def test_mNormalizeHost_truncates_and_prefixes_hostname(self):

        qdm = self.mCreateQuorumManager()
        original_name = 'very-long-hostname-with-hyphen'

        normalized = qdm.mNormalizeHost(original_name)
        expected_tail = original_name.replace('-', '')[-9:]

        self.assertTrue(normalized.startswith('qm'))
        self.assertEqual(len(normalized), 13)
        self.assertEqual(normalized[4:], expected_tail)
        self.assertIn(original_name, qdm.fake_hosts)
        self.assertEqual(qdm.fake_hosts[original_name], normalized)

    # Auto-generated test for mSetSrcDom0DomU
    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogWarn')
    def test_mSetSrcDom0DomU_selects_connectable_domU(self, mock_log_warn, mock_log_info, mock_get_ctx, mock_node_cls):

        options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, options)

        dom_pairs = [('dom0a', 'domuA.example.com'), ('dom0b', 'domuB.example.com')]

        with patch.object(cluctrl, 'mReturnDom0DomUPair', return_value=dom_pairs), \
             patch.object(cluctrl, 'mIsExaScale', return_value=False), \
             patch.object(cluctrl, 'mUpdateErrorObject') as mock_update_error:

            mock_get_ctx.return_value = MagicMock()

            node_first = MagicMock()
            node_first.mIsConnectable.return_value = False

            node_second = MagicMock()
            node_second.mIsConnectable.return_value = True
            node_second.mExecuteCmd.side_effect = [
                (None, MagicMock(readlines=MagicMock(return_value=['+ASM1:/u01/app/grid\n'])), None),
                (None, MagicMock(readlines=MagicMock(return_value=[])), None),
                (None, MagicMock(readlines=MagicMock(return_value=['domuB\t1\n'])), None),
            ]
            node_second.mGetCmdExitStatus.side_effect = [0, 0, 0]

            mock_node_cls.side_effect = [node_first, node_second]

            node_recovery.mSetSrcDom0DomU('dom0new', 'domuNew.example.com')

        mock_update_error.assert_not_called()

        mock_log_warn.assert_called_once_with('*** mSetSrcDom0DomU: DomU domuA.example.com is not connectable. Run the temporal keys addition workflow for existing VMs. Root ssh access is required for this operation.')
        mock_log_info.assert_any_call("Connectable DomU:domuB detected.")
        self.assertEqual(node_recovery.mGetSrcDom0(), 'dom0b')
        self.assertEqual(node_recovery.mGetSrcDomU(), 'domuB.example.com')

    # Auto-generated test for mSetSrcDom0DomU
    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mSetSrcDom0DomU_raises_when_no_connectable_node(self, mock_get_ctx, mock_node_cls):

        options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, options)

        dom_pairs = [('dom0a', 'domuA.example.com')]

        with patch.object(cluctrl, 'mReturnDom0DomUPair', return_value=dom_pairs), \
             patch.object(cluctrl, 'mIsExaScale', return_value=False), \
             patch.object(cluctrl, 'mUpdateErrorObject') as mock_update_error:

            mock_get_ctx.return_value = MagicMock()

            node_instance = MagicMock()
            node_instance.mIsConnectable.return_value = False
            mock_node_cls.return_value = node_instance

            with self.assertRaises(ExacloudRuntimeError):
                node_recovery.mSetSrcDom0DomU('dom0new', 'domuNew.example.com')

            mock_update_error.assert_called_once_with(gNodeElasticError['NO_ACTIVE_NODE'], 'No Pingable/Active node in the cluster')

        self.assertEqual(node_recovery.mGetSrcDom0(), '')
        self.assertEqual(node_recovery.mGetSrcDomU(), '')

    # Auto-generated test for mCreateQuorum
    def test_mCreateQuorum_skips_when_enough_cells(self):

        qdm = self.mCreateQuorumManager()

        with patch.object(qdm, 'mGetCellCount', return_value='5') as mock_cell_count, \
             patch.object(qdm, 'mVerifyVD') as mock_verify, \
             patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo') as mock_log:

            qdm.mCreateQuorum('domu1')

        mock_cell_count.assert_called_once_with('domu1')
        mock_verify.assert_not_called()
        mock_log.assert_any_call('*** Quorum disks are not needed since there are 5 cells.')

    # Auto-generated test for mCreateQuorum
    def test_mCreateQuorum_invokes_creation_flow_when_missing_vd(self):

        qdm = self.mCreateQuorumManager()

        with patch.object(qdm, 'mGetCellCount', return_value='4'), \
             patch.object(qdm, 'mVerifyVD', side_effect=[False, True]) as mock_verify, \
             patch.object(qdm, 'mCreateQDConfig') as mock_config, \
             patch.object(qdm, 'mCreateQT') as mock_create_qt, \
             patch.object(qdm, 'mCreateQD') as mock_create_qd, \
             patch.object(qdm, 'mAddQD') as mock_add_qd:

            qdm.mCreateQuorum('domu2', 'C2')

        mock_verify.assert_any_call('domu2')
        mock_config.assert_called_once()
        mock_create_qt.assert_called_once_with('C2')
        mock_create_qd.assert_called_once()
        mock_add_qd.assert_called_once_with('domu2', 'C2')

    # Auto-generated test for mDeleteQuorum
    def test_mDeleteQuorum_no_action_when_vd_present(self):

        qdm = self.mCreateQuorumManager()

        with patch.object(qdm, 'mVerifyVD', return_value=True) as mock_verify, \
             patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo') as mock_log:

            qdm.mDeleteQuorum('domu1')

        mock_verify.assert_called_once_with('domu1')
        mock_log.assert_any_call('*** nothing to be done')

    # Auto-generated test for mDeleteQuorum
    def test_mDeleteQuorum_executes_cleanup_when_drop_succeeds(self):

        qdm = self.mCreateQuorumManager()

        with patch.object(qdm, 'mVerifyVD', return_value=False), \
             patch.object(qdm, 'mQDConfigNodes', return_value=['domu1', 'domu2']) as mock_config_nodes, \
             patch.object(qdm, 'mDropQD') as mock_drop, \
             patch.object(qdm, 'mIsQDdropped', return_value=True) as mock_is_dropped, \
            patch.object(qdm, 'mDeleteQD') as mock_delete_qd, \
            patch.object(qdm, 'mDeleteQT') as mock_delete_qt, \
            patch.object(qdm, 'mDeleteQDConfig') as mock_delete_config:

            qdm.mDeleteQuorum('domuX', 'C3')

        mock_config_nodes.assert_called_once_with('domuX')
        mock_drop.assert_called_once_with('domuX', 'C3')
        mock_is_dropped.assert_called_once_with('domuX')
        mock_delete_qd.assert_called_once_with(['domu1', 'domu2'])
        mock_delete_qt.assert_called_once_with(['domu1', 'domu2'])
        mock_delete_config.assert_called_once_with(['domu1', 'domu2'])

    # Auto-generated test for mDetectVirtEnv
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mDetectVirtEnv_returns_detected_environment(self, mock_get_ctx, mock_connect, mock_log_info):

        qdm = self.mCreateQuorumManager(aUser="root")

        mock_ctx = MagicMock()
        mock_get_ctx.return_value = mock_ctx

        stdout = MagicMock()
        stdout.read.return_value = 'kvm\n'
        mock_node = MagicMock()
        mock_node.mExecuteCmd.return_value = (None, stdout, None)
        mock_connect.return_value.__enter__.return_value = mock_node
        mock_connect.return_value.__exit__.return_value = False

        result = qdm.mDetectVirtEnv('domu1')

        self.assertEqual(result, 'kvm')
        mock_connect.assert_called_once_with('domu1', mock_ctx, username='root')
        mock_node.mExecuteCmd.assert_called_once_with('/usr/bin/systemd-detect-virt')
        mock_log_info.assert_called_once_with('kvm environment detected.')

    # Auto-generated test for mDetectVirtEnv
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mDetectVirtEnv_raises_when_command_fails(self, mock_get_ctx, mock_connect, mock_log_info):

        qdm = self.mCreateQuorumManager(aUser="root")

        mock_ctx = MagicMock()
        mock_get_ctx.return_value = mock_ctx

        mock_context = MagicMock()
        mock_context.__enter__.side_effect = RuntimeError('connect failed')
        mock_context.__exit__.return_value = False
        mock_connect.return_value = mock_context

        with self.assertRaises(RuntimeError):
            qdm.mDetectVirtEnv('domu1')

        mock_connect.assert_called_once_with('domu1', mock_ctx, username='root')
        mock_log_info.assert_not_called()

    # Auto-generated test for mGetClusterNodes
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mGetClusterNodes_returns_active_nodes(self, mock_get_ctx, mock_connect, mock_log_info, mock_log_error):

        qdm = self.mCreateQuorumManager(aUser="grid")

        mock_ctx = MagicMock()
        mock_get_ctx.return_value = mock_ctx

        stdout = MagicMock()
        stdout.readlines.return_value = ['node1\t1\n', 'node2\t2\n']

        mock_node = MagicMock()
        mock_node.mExecuteCmd.return_value = (None, stdout, None)
        mock_node.mGetCmdExitStatus.return_value = 0

        mock_connect.return_value.__enter__.return_value = mock_node
        mock_connect.return_value.__exit__.return_value = False

        result = qdm.mGetClusterNodes('domuA', '/u01/app/grid')

        mock_connect.assert_called_once_with('domuA', mock_ctx, username='grid')
        mock_node.mExecuteCmd.assert_called_once_with('/u01/app/grid/bin/olsnodes -s -n|grep Active')
        mock_log_info.assert_any_call("olsnodes reported: ['node1\\t1\\n', 'node2\\t2\\n']")
        mock_log_error.assert_not_called()
        self.assertEqual(result, ['node1', 'node2'])

    # Auto-generated test for mGetClusterNodes
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mGetClusterNodes_logs_error_on_failure(self, mock_get_ctx, mock_connect, mock_log_info, mock_log_error):

        qdm = self.mCreateQuorumManager(aUser="grid")

        mock_ctx = MagicMock()
        mock_get_ctx.return_value = mock_ctx

        stdout = MagicMock()
        stdout.readlines.return_value = []

        mock_node = MagicMock()
        mock_node.mExecuteCmd.return_value = (None, stdout, None)
        mock_node.mGetCmdExitStatus.return_value = 1

        mock_connect.return_value.__enter__.return_value = mock_node
        mock_connect.return_value.__exit__.return_value = False

        result = qdm.mGetClusterNodes('domuB', '/u01/app/grid')

        mock_connect.assert_called_once_with('domuB', mock_ctx, username='grid')
        mock_node.mExecuteCmd.assert_called_once()
        mock_log_info.assert_any_call('olsnodes reported: []')
        mock_log_error.assert_called_once_with('*** No active node in the cluster')
        self.assertEqual(result, [])

    # Auto-generated test for mQDList
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogTrace')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.time.sleep')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mQDList_retries_until_success_and_collects_disks(self, mock_get_ctx, mock_connect, mock_sleep, mock_log_info, mock_log_trace):

        qdm = self.mCreateQuorumManager()

        mock_ctx = MagicMock()
        mock_get_ctx.return_value = mock_ctx

        stdout_first = MagicMock()
        stdout_second = MagicMock()
        stdout_second.read.return_value = "NAME\n-----\nQD_DATA1\nQD_RECO1\nrows selected\n"

        mock_node = MagicMock()
        mock_node.mExecuteCmd.side_effect = [
            (None, stdout_first, None),
            (None, stdout_second, None)
        ]
        mock_node.mGetCmdExitStatus.side_effect = [1, 0]

        mock_connect.return_value.__enter__.return_value = mock_node
        mock_connect.return_value.__exit__.return_value = False

        with patch.object(qdm._QuorumDiskManager__cluctrl, 'mGetOracleBaseDirectories', return_value=('/grid/home', None, None)) as mock_dirs:
            result = qdm.mQDList('domuC')

        mock_dirs.assert_called_once_with(aDomU='domuC')
        mock_connect.assert_called_once_with('domuC', mock_ctx, username='grid')
        self.assertEqual(mock_node.mExecuteCmd.call_count, 2)
        mock_sleep.assert_called_once_with(30)
        mock_log_trace.assert_any_call('*** Waiting for sql connection...')
        mock_log_trace.assert_any_call('SQL CMD OUTPUT:NAME\n-----\nQD_DATA1\nQD_RECO1\nrows selected\n')
        mock_log_info.assert_any_call("Quorum disks ['QD_DATA1', 'QD_RECO1']")
        self.assertEqual(result, ['QD_DATA1', 'QD_RECO1'])

    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mGetCellCount_returns_line_count(self, mock_get_ctx, mock_connect):
        # Auto-generated test for mGetCellCount

        qdm = self.mCreateQuorumManager(aUser="grid")

        ctx = MagicMock()
        node = MagicMock()
        stdout = MagicMock()
        stdout.read.return_value = '7\n'
        node.mExecuteCmd.return_value = (None, stdout, None)
        ctx.__enter__.return_value = node
        ctx.__exit__.return_value = False
        mock_get_ctx.return_value = MagicMock()
        mock_connect.return_value = ctx

        result = qdm.mGetCellCount('domu-host')

        mock_connect.assert_called_once_with('domu-host', mock_get_ctx.return_value, username='grid')
        node.mExecuteCmd.assert_called_once_with('cat /etc/oracle/cell/network-config/cellip.ora |wc -l')
        self.assertEqual(result, '7')

    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mQDConfigNodes_filters_by_exit_status(self, mock_get_ctx, mock_connect):
        # Auto-generated test for mQDConfigNodes

        qdm = self.mCreateQuorumManager(aUser="grid")

        pairs = [('dom0a', 'domu1.domain'), ('dom0b', 'domu2.domain')]
        with patch.object(qdm._QuorumDiskManager__cluctrl, 'mReturnDom0DomUPair', return_value=pairs):
            node_success = MagicMock()
            node_success.mExecuteCmd.return_value = (None, MagicMock(), None)
            node_success.mGetCmdExitStatus.return_value = 0

            node_failure = MagicMock()
            node_failure.mExecuteCmd.return_value = (None, MagicMock(), None)
            node_failure.mGetCmdExitStatus.return_value = 1

            ctx_success = MagicMock()
            ctx_success.__enter__.return_value = node_success
            ctx_success.__exit__.return_value = False

            ctx_failure = MagicMock()
            ctx_failure.__enter__.return_value = node_failure
            ctx_failure.__exit__.return_value = False

            mock_get_ctx.return_value = MagicMock()
            mock_connect.side_effect = [ctx_success, ctx_failure]

            result = qdm.mQDConfigNodes('domu-src')

        self.assertEqual(result, ['domu1.domain'])
        self.assertEqual(mock_connect.call_count, 2)
        node_success.mExecuteCmd.assert_called_once_with('/opt/oracle.SupportTools/quorumdiskmgr --list --config')
        node_failure.mExecuteCmd.assert_called_once_with('/opt/oracle.SupportTools/quorumdiskmgr --list --config')

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mDropQD_executes_drop_commands_for_each_disk(self, mock_connect, mock_log_info):
        # Auto-generated test for mDropQD

        qdm = self.mCreateQuorumManager(aUser="grid")

        with patch.object(qdm._QuorumDiskManager__cluctrl, 'mGetGridHome', return_value=('/u01/grid', 'ASM1')) as mock_grid_home, \
             patch.object(qdm, 'mQDList', return_value=['QD_DATA_01', 'QD_RECO_02']):

            node = MagicMock()
            stdout_data = MagicMock()
            stdout_data.read.return_value = 'drop success'
            node.mExecuteCmd.return_value = (None, stdout_data, None)
            ctx = MagicMock()
            ctx.__enter__.return_value = node
            ctx.__exit__.return_value = False
            mock_connect.return_value = ctx

            qdm.mDropQD('domu-test', 'C5')

        mock_grid_home.assert_called_with('domu-test')
        node_calls = [call_args[0][0] for call_args in node.mExecuteCmd.call_args_list]
        self.assertEqual(len(node_calls), 2)
        self.assertTrue(any("alter diskgroup DATAC5 drop quorum disk QD_DATA_01 force;" in cmd for cmd in node_calls))
        self.assertTrue(any("alter diskgroup RECOC5 drop quorum disk QD_RECO_02 force;" in cmd for cmd in node_calls))
        mock_log_info.assert_any_call('*** Drop the DATA/RECO QDs from ASM diskgroups')
        mock_log_info.assert_any_call('drop success')

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mIsQDdropped_returns_true_when_all_dropped(self, mock_connect, mock_log_info):
        # Auto-generated test for mIsQDdropped

        qdm = self.mCreateQuorumManager(aUser="grid")

        stdout = MagicMock()
        stdout.read.return_value = "exadata_quorum_DROPPED_DATA\nexadata_quorum_DROPPED_RECO\n"
        node = MagicMock()
        node.mExecuteCmd.return_value = (None, stdout, None)

        ctx = MagicMock()
        ctx.__enter__.return_value = node
        ctx.__exit__.return_value = False
        mock_connect.return_value = ctx

        with patch.object(qdm._QuorumDiskManager__cluctrl, 'mGetGridHome', return_value=('/u01/grid', 'ASM1')):
            result = qdm.mIsQDdropped('domu-test')

        self.assertTrue(result)
        mock_log_info.assert_called_once_with('*** Check if all offline DATA/RECO QDs are dropped')

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mIsQDdropped_returns_false_when_active_disk_found(self, mock_connect, mock_log_info):
        # Auto-generated test for mIsQDdropped

        qdm = self.mCreateQuorumManager(aUser="grid")

        stdout = MagicMock()
        stdout.read.return_value = "exadata_quorum_ACTIVE_DATA\n"
        node = MagicMock()
        node.mExecuteCmd.return_value = (None, stdout, None)

        ctx = MagicMock()
        ctx.__enter__.return_value = node
        ctx.__exit__.return_value = False
        mock_connect.return_value = ctx

        with patch.object(qdm._QuorumDiskManager__cluctrl, 'mGetGridHome', return_value=('/u01/grid', 'ASM1')):
            result = qdm.mIsQDdropped('domu-test')

        self.assertFalse(result)
        mock_log_info.assert_any_call('exadata_quorum_ACTIVE_DATA')

    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mDeleteQD_invokes_delete_on_all_nodes(self, mock_connect):
        # Auto-generated test for mDeleteQD

        qdm = self.mCreateQuorumManager(aUser="grid")
        node = MagicMock()
        ctx = MagicMock()
        ctx.__enter__.return_value = node
        ctx.__exit__.return_value = False
        mock_connect.return_value = ctx

        qdm.mDeleteQD(['domu1', 'domu2'])

        self.assertEqual(node.mExecuteCmdLog.call_count, 2)
        node.mExecuteCmdLog.assert_called_with('/opt/oracle.SupportTools/quorumdiskmgr --delete --device')

    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mDeleteQT_invokes_delete_on_all_nodes(self, mock_connect):
        # Auto-generated test for mDeleteQT

        qdm = self.mCreateQuorumManager(aUser="grid")
        node = MagicMock()
        ctx = MagicMock()
        ctx.__enter__.return_value = node
        ctx.__exit__.return_value = False
        mock_connect.return_value = ctx

        qdm.mDeleteQT(['domu1'])

        node.mExecuteCmdLog.assert_called_once_with('/opt/oracle.SupportTools/quorumdiskmgr --delete --target')

    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mDeleteQDConfig_invokes_delete_on_all_nodes(self, mock_connect):
        # Auto-generated test for mDeleteQDConfig

        qdm = self.mCreateQuorumManager(aUser="grid")
        node = MagicMock()
        ctx = MagicMock()
        ctx.__enter__.return_value = node
        ctx.__exit__.return_value = False
        mock_connect.return_value = ctx

        qdm.mDeleteQDConfig(['domu1'])

        node.mExecuteCmdLog.assert_called_once_with('/opt/oracle.SupportTools/quorumdiskmgr --delete --config')

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mVerifyVD_returns_true_when_two_quorum_disks(self, mock_connect, mock_log_info, mock_log_error):
        # Auto-generated test for mVerifyVD

        qdm = self.mCreateQuorumManager(aUser="grid")

        node = MagicMock()
        stdout = MagicMock()
        stdout.read.return_value = 'ONLINE exadata_quorum_data\nONLINE exadata_quorum_reco\n'
        node.mExecuteCmd.return_value = (None, stdout, None)

        ctx = MagicMock()
        ctx.__enter__.return_value = node
        ctx.__exit__.return_value = False
        mock_connect.return_value = ctx

        with patch.object(node, 'mSingleLineOutput', return_value='/u01/grid'), \
             patch.object(qdm._QuorumDiskManager__cluctrl, 'mGetOracleBaseDirectories', return_value=('/u01/grid', None, None)):
            result = qdm.mVerifyVD('domu1')

        self.assertTrue(result)
        mock_log_error.assert_not_called()
        mock_log_info.assert_any_call('*** SUCCESS: Located 2 QD based voting disks')

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mVerifyVD_returns_false_when_missing_quorum_disks(self, mock_connect, mock_log_info, mock_log_error):
        # Auto-generated test for mVerifyVD

        qdm = self.mCreateQuorumManager(aUser="grid")

        node = MagicMock()
        stdout = MagicMock()
        stdout.read.return_value = 'ONLINE somethingelse\n'
        node.mExecuteCmd.return_value = (None, stdout, None)

        ctx = MagicMock()
        ctx.__enter__.return_value = node
        ctx.__exit__.return_value = False
        mock_connect.return_value = ctx

        with patch.object(node, 'mSingleLineOutput', return_value='/u01/grid'), \
             patch.object(qdm._QuorumDiskManager__cluctrl, 'mGetOracleBaseDirectories', return_value=('/u01/grid', None, None)):
            result = qdm.mVerifyVD('domu1')

        self.assertFalse(result)
        mock_log_error.assert_called_once_with('*** ERROR: Located less than 2 QD based voting disks')

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mVerifyQD_returns_true_when_four_devices_found(self, mock_connect, mock_log_info):
        # Auto-generated test for mVerifyQD

        qdm = self.mCreateQuorumManager(aUser="grid")

        stdout = MagicMock()
        stdout.read.return_value = '\n'.join([f'exadata_quorum_{i}' for i in range(4)])
        node = MagicMock()
        node.mExecuteCmd.return_value = (None, stdout, None)

        ctx = MagicMock()
        ctx.__enter__.return_value = node
        ctx.__exit__.return_value = False
        mock_connect.return_value = ctx

        with patch.object(qdm._QuorumDiskManager__cluctrl, 'mGetOracleBaseDirectories', return_value=('/u01/grid', None, '/oracle/base')):
            result = qdm.mVerifyQD('domu1')

        self.assertTrue(result)
        mock_log_info.assert_called_once_with('*** Ensure ASM can discover the quorum devices')

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mVerifyQD_returns_false_when_insufficient_devices(self, mock_connect, mock_log_info):
        # Auto-generated test for mVerifyQD

        qdm = self.mCreateQuorumManager(aUser="grid")

        stdout = MagicMock()
        stdout.read.return_value = 'exadata_quorum_only_one\n'
        node = MagicMock()
        node.mExecuteCmd.return_value = (None, stdout, None)

        ctx = MagicMock()
        ctx.__enter__.return_value = node
        ctx.__exit__.return_value = False
        mock_connect.return_value = ctx

        with patch.object(qdm._QuorumDiskManager__cluctrl, 'mGetOracleBaseDirectories', return_value=('/u01/grid', None, '/oracle/base')):
            result = qdm.mVerifyQD('domu1')

        self.assertFalse(result)
        mock_log_info.assert_called_once_with('*** Ensure ASM can discover the quorum devices')

    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mCreateQDConfig_uses_env_specific_interface_list(self, mock_connect):
        # Auto-generated test for mCreateQDConfig

        qdm = self.mCreateQuorumManager(aUser="grid")

        pairs = [('dom0a', 'domua.xen.example.com'), ('dom0b', 'domub.kvm.example.com')]
        with patch.object(qdm._QuorumDiskManager__cluctrl, 'mReturnDom0DomUPair', return_value=pairs), \
             patch.object(qdm, 'mDetectVirtEnv', side_effect=['xen', 'kvm']):

            ctx_xen = MagicMock()
            node_xen = MagicMock()
            ctx_xen.__enter__.return_value = node_xen
            ctx_xen.__exit__.return_value = False

            ctx_kvm = MagicMock()
            node_kvm = MagicMock()
            ctx_kvm.__enter__.return_value = node_kvm
            ctx_kvm.__exit__.return_value = False

            mock_connect.side_effect = [ctx_xen, ctx_kvm]

            qdm.mCreateQDConfig()

        node_xen.mExecuteCmdLog.assert_called_once_with("/opt/oracle.SupportTools/quorumdiskmgr --create --config --owner='grid' --group='asmadmin' --network-iface-list='clib0,clib1'")
        node_kvm.mExecuteCmdLog.assert_called_once_with("/opt/oracle.SupportTools/quorumdiskmgr --create --config --owner='grid' --group='asmadmin' --network-iface-list='clre0,clre1'")

    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mCreateQT_creates_targets_with_collected_ips_and_normalized_hosts(self, mock_connect):
        # Auto-generated test for mCreateQT

        qdm = self.mCreateQuorumManager(aUser="grid")

        pairs = [
            ('dom0a', 'short.example.com'),
            ('dom0b', 'averyverylonghostnameoverlimit.example.com')
        ]
        with patch.object(qdm._QuorumDiskManager__cluctrl, 'mReturnDom0DomUPair', return_value=pairs), \
             patch.object(qdm, 'mDetectVirtEnv', side_effect=['xen', 'kvm', 'xen', 'kvm']), \
             patch.object(qdm, 'mNormalizeHost', return_value='qmnormalized') as mock_normalize:

            def make_ctx(outputs, log_calls):
                node = MagicMock()
                node.mExecuteCmd.side_effect = outputs
                node.mExecuteCmdLog.side_effect = log_calls
                ctx = MagicMock()
                ctx.__enter__.return_value = node
                ctx.__exit__.return_value = False
                return ctx, node

            def make_output(values):
                stdout = MagicMock()
                stdout.read.return_value = '\n'.join(values)
                return (None, stdout, None)

            xen_outputs = [
                make_output(['10.0.0.1/24']),
                make_output(['10.0.0.2/24'])
            ]
            kvm_outputs = [
                make_output(['10.1.0.1/24']),
                make_output(['10.1.0.2/24'])
            ]

            ctx1, node1 = make_ctx(xen_outputs, [None, None])
            ctx2, node2 = make_ctx(kvm_outputs, [None, None])
            ctx3, node3 = make_ctx([], [None, None])
            ctx4, node4 = make_ctx([], [None, None])

            mock_connect.side_effect = [ctx1, ctx2, ctx3, ctx4]

            qdm.mCreateQT('C7')

        mock_normalize.assert_called_with('averyverylonghostnameoverlimit')
        # Ensure target creation commands invoked with aggregated IPs
        target_calls = [call[0][0] for call in node3.mExecuteCmdLog.call_args_list + node4.mExecuteCmdLog.call_args_list]
        self.assertTrue(any('--asm-disk-group=DATA' in cmd and '10.0.0.1' in cmd and '10.1.0.1' in cmd for cmd in target_calls))
        self.assertTrue(any('--asm-disk-group=RECO' in cmd for cmd in target_calls))

    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mCreateQD_creates_devices_using_collected_ips(self, mock_connect):
        # Auto-generated test for mCreateQD

        qdm = self.mCreateQuorumManager(aUser="grid")

        pairs = [('dom0a', 'short.example.com'), ('dom0b', 'another.example.com')]
        with patch.object(qdm._QuorumDiskManager__cluctrl, 'mReturnDom0DomUPair', return_value=pairs), \
             patch.object(qdm, 'mDetectVirtEnv', side_effect=['xen', 'kvm']), \
             patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo') as mock_log_info:

            def make_output(values):
                stdout = MagicMock()
                stdout.read.return_value = '\n'.join(values)
                return (None, stdout, None)

            node_xen = MagicMock()
            node_xen.mExecuteCmd.side_effect = [
                make_output(['10.0.0.1/24']),
                make_output(['10.0.0.2/24'])
            ]
            node_xen.mExecuteCmdLog.return_value = None

            node_kvm = MagicMock()
            node_kvm.mExecuteCmd.side_effect = [
                make_output(['10.1.0.1/24']),
                make_output(['10.1.0.2/24'])
            ]
            node_kvm.mExecuteCmdLog.return_value = None

            ctx1 = MagicMock()
            ctx1.__enter__.return_value = node_xen
            ctx1.__exit__.return_value = False

            ctx2 = MagicMock()
            ctx2.__enter__.return_value = node_kvm
            ctx2.__exit__.return_value = False

            ctx3 = MagicMock()
            ctx3.__enter__.return_value = MagicMock()
            ctx3.__exit__.return_value = False

            ctx4 = MagicMock()
            ctx4.__enter__.return_value = MagicMock()
            ctx4.__exit__.return_value = False

            mock_connect.side_effect = [ctx1, ctx2, ctx3, ctx4]

            qdm.mCreateQD()

        mock_log_info.assert_any_call('*** Following operation takes 2 mins per node...')
        device_calls = [call[0][0] for call in ctx3.__enter__.return_value.mExecuteCmdLog.call_args_list + ctx4.__enter__.return_value.mExecuteCmdLog.call_args_list]
        for cmd in device_calls:
            self.assertIn('--create --device', cmd)

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mAddQD_logs_error_when_verify_fails(self, mock_connect, mock_log_error):
        # Auto-generated test for mAddQD

        qdm = self.mCreateQuorumManager(aUser="grid")

        with patch.object(qdm, 'mVerifyQD', return_value=False), \
             patch.object(qdm._QuorumDiskManager__cluctrl, 'mGetOracleBaseDirectories', return_value=('/u01/grid', 'ASM1')):

            stdout = MagicMock()
            stdout.read.return_value = '/dev/exadata_quorum/DATA_QD1\n/dev/exadata_quorum/RECO_QD1\n'
            node = MagicMock()
            node.mExecuteCmd.return_value = (None, stdout, None)
            ctx = MagicMock()
            ctx.__enter__.return_value = node
            ctx.__exit__.return_value = False
            mock_connect.return_value = ctx

            qdm.mAddQD('domu1', 'C9')

        mock_log_error.assert_called_once_with('*** ERROR:  ASM cannot discover the quorum devices')
        sql_calls = [call[0][0] for call in node.mExecuteCmdLog.call_args_list]
        self.assertTrue(any('alter diskgroup DATAC9 add ' in cmd for cmd in sql_calls))
        self.assertTrue(any('alter diskgroup RECOC9 add ' in cmd for cmd in sql_calls))

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mAddQD_skips_error_when_verify_succeeds(self, mock_connect, mock_log_error):
        # Auto-generated test for mAddQD

        qdm = self.mCreateQuorumManager(aUser="grid")

        with patch.object(qdm, 'mVerifyQD', return_value=True), \
             patch.object(qdm._QuorumDiskManager__cluctrl, 'mGetOracleBaseDirectories', return_value=('/u01/grid', 'ASM1')):

            stdout = MagicMock()
            stdout.read.return_value = '/dev/exadata_quorum/DATA_QD1\n'
            node = MagicMock()
            node.mExecuteCmd.return_value = (None, stdout, None)
            ctx = MagicMock()
            ctx.__enter__.return_value = node
            ctx.__exit__.return_value = False
            mock_connect.return_value = ctx

            qdm.mAddQD('domu1')

        mock_log_error.assert_not_called()

    def mCreateQuorumManager(self, aUser="grid"):
        options = self.mGetClubox().mGetArgsOptions()
        return QuorumDiskManager(self.mGetClubox(), aUser, options)

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
        
    # Auto-generated test for mUpdateXMLTagValue
    def test_mUpdateXMLTagValue_invalid_prefix(self):

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        _xml_path = f'/EXAVMIMAGES/conf/{_domU}.xml'
        _invalid_path = '/invalid/System.first.boot.25.1.2.0.0.250213.2.img'

        _status = _nc.mUpdateXMLTagValue(_dom0, _xml_path, _invalid_path)
        self.assertFalse(_status)

    # Auto-generated test for mUpdateXMLTagValue
    def test_mUpdateXMLTagValue_type_mismatch_returns_false(self):

        sample_xml = """
        <Root>
            <disk>
                <domuVolume>/EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.img</domuVolume>
            </disk>
        </Root>
        """

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        _xml_path = f'/EXAVMIMAGES/conf/{_domU}.xml'
        _new_image_path = '/EXAVMIMAGES/grid-klone-25.1.2.0.0.250213.2.zip'

        with patch('exabox.ovm.cluvmrecoveryutils.connect_to_host') as _mock_connect:
            _node = MagicMock()
            _node.mReadFile.return_value = sample_xml
            _context = MagicMock()
            _context.__enter__.return_value = _node
            _context.__exit__.return_value = False
            _mock_connect.return_value = _context

            _status = _nc.mUpdateXMLTagValue(_dom0, _xml_path, _new_image_path)

            self.assertFalse(_status)
            _node.mWriteFile.assert_not_called()

    # Auto-generated test for mUpdateXMLTagValue
    def test_mUpdateXMLTagValue_parse_error_returns_false(self):

        malformed_xml = "<Root>"

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        _xml_path = f'/EXAVMIMAGES/conf/{_domU}.xml'
        _new_image_path = '/EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.2.img'

        with patch('exabox.ovm.cluvmrecoveryutils.connect_to_host') as _mock_connect:
            _node = MagicMock()
            _node.mReadFile.return_value = malformed_xml
            _context = MagicMock()
            _context.__enter__.return_value = _node
            _context.__exit__.return_value = False
            _mock_connect.return_value = _context

            _status = _nc.mUpdateXMLTagValue(_dom0, _xml_path, _new_image_path)

            self.assertFalse(_status)
            _node.mWriteFile.assert_not_called()

    # Auto-generated test for mUpdateXMLTagValue
    def test_mUpdateXMLTagValue_no_disk_elements_returns_true(self):

        xml_no_disk = """
        <Root>
            <data/>
        </Root>
        """

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        _xml_path = f'/EXAVMIMAGES/conf/{_domU}.xml'
        _new_image_path = '/EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.2.img'

        with patch('exabox.ovm.cluvmrecoveryutils.connect_to_host') as _mock_connect:
            _node = MagicMock()
            _node.mReadFile.return_value = xml_no_disk
            _context = MagicMock()
            _context.__enter__.return_value = _node
            _context.__exit__.return_value = False
            _mock_connect.return_value = _context

            _status = _nc.mUpdateXMLTagValue(_dom0, _xml_path, _new_image_path)

            self.assertTrue(_status)
            _node.mWriteFile.assert_not_called()

    # Auto-generated test for mUpdateXMLTagValue
    def test_mUpdateXMLTagValue_write_failure_returns_false(self):

        sample_xml = """
        <Root>
            <disk>
                <domuVolume>/EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.img</domuVolume>
                <domuVersion>25.1.2.0.0.250213.1</domuVersion>
            </disk>
        </Root>
        """

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]
        _xml_path = f'/EXAVMIMAGES/conf/{_domU}.xml'
        _new_image_path = '/EXAVMIMAGES/System.first.boot.25.1.2.0.0.250214.1.img'

        with patch('exabox.ovm.cluvmrecoveryutils.connect_to_host') as _mock_connect:
            _node = MagicMock()
            _node.mReadFile.return_value = sample_xml
            _node.mWriteFile.side_effect = Exception('write failed')
            _context = MagicMock()
            _context.__enter__.return_value = _node
            _context.__exit__.return_value = False
            _mock_connect.return_value = _context

            _status = _nc.mUpdateXMLTagValue(_dom0, _xml_path, _new_image_path)

            self.assertFalse(_status)
            _node.mWriteFile.assert_called_once()

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

    # Auto-generated test for mParseSystemImgVersion
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    def test_mParseSystemImgVersion_standard_image(self, mock_log_error):
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        image_name = 'System.first.boot.25.1.2.0.0.250213.1.img'
        version = _nc.mParseSystemImgVersion(image_name)

        self.assertEqual(version, '25.1.2.0.0.250213.1')
        mock_log_error.assert_not_called()

    # Auto-generated test for mParseSystemImgVersion
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    def test_mParseSystemImgVersion_handles_rtg_suffix(self, mock_log_error):
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        image_name = 'System.first.boot.25.1.2.0.0.250213.1.rtg.img'
        version = _nc.mParseSystemImgVersion(image_name)

        self.assertEqual(version, '25.1.2.0.0.250213.1')
        mock_log_error.assert_not_called()

    # Auto-generated test for mParseSystemImgVersion
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    def test_mParseSystemImgVersion_invalid_format_returns_none(self, mock_log_error):
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        image_name = 'invalid.img'
        version = _nc.mParseSystemImgVersion(image_name)

        self.assertIsNone(version)
        mock_log_error.assert_called_once_with(f"Unexpected image name format: {image_name}")
    
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
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.uefi.img",  aRc=1, aStdout="", aPersist=True),
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
                'isKvmImg': False, 'isRtgImg': False, 'isArchive': True, 'isUefiImg': False}, 
             {'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.25.1.2.0.0.250213.1.img.bz2',
              'fileBaseName': 'System.first.boot.25.1.2.0.0.250213.1.img.bz2', 
              'imgBaseName': 'System.first.boot.25.1.2.0.0.250213.1.img', 
              'imgArchiveBaseName': 'System.first.boot.25.1.2.0.0.250213.1.img.bz2', 
              'imgVersion': '25.1.2.0.0.250213.1', 'isKvmImg': False, 'isRtgImg': False, 'isArchive': True, 'isUefiImg': False}, 
             {'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.25.1.2.0.0.250213.1.kvm.img.bz2', 
              'fileBaseName': 'System.first.boot.25.1.2.0.0.250213.1.kvm.img.bz2', 
              'imgBaseName': 'System.first.boot.25.1.2.0.0.250213.1.kvm.img', 
              'imgArchiveBaseName': 'System.first.boot.25.1.2.0.0.250213.1.kvm.img.bz2', 
              'imgVersion': '25.1.2.0.0.250213.1', 'isKvmImg': True, 'isRtgImg': False, 'isArchive': True, 'isUefiImg': False}, 
             {'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz2', 
              'fileBaseName': 'System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz2', 
              'imgBaseName': 'System.first.boot.25.1.2.0.0.250213.1.rtg.img', 
              'imgArchiveBaseName': 'System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz2', 
              'imgVersion': '25.1.2.0.0.250213.1', 'isKvmImg': False, 'isRtgImg': True, 'isArchive': True, 'isUefiImg': False}
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
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.uefi.img",  aRc=1, aStdout="", aPersist=True),
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
                'isKvmImg': False, 'isRtgImg': False, 'isArchive': True, 'isUefiImg': False}, 
             {'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.25.1.2.0.0.250213.1.img.bz2',
              'fileBaseName': 'System.first.boot.25.1.2.0.0.250213.1.img.bz2', 
              'imgBaseName': 'System.first.boot.25.1.2.0.0.250213.1.img', 
              'imgArchiveBaseName': 'System.first.boot.25.1.2.0.0.250213.1.img.bz2', 
              'imgVersion': '25.1.2.0.0.250213.1', 'isKvmImg': False, 'isRtgImg': False, 'isArchive': True, 'isUefiImg': False}, 
             {'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.25.1.2.0.0.250213.1.kvm.img.bz2', 
              'fileBaseName': 'System.first.boot.25.1.2.0.0.250213.1.kvm.img.bz2', 
              'imgBaseName': 'System.first.boot.25.1.2.0.0.250213.1.kvm.img', 
              'imgArchiveBaseName': 'System.first.boot.25.1.2.0.0.250213.1.kvm.img.bz2', 
              'imgVersion': '25.1.2.0.0.250213.1', 'isKvmImg': True, 'isRtgImg': False, 'isArchive': True, 'isUefiImg': False},
             ]
        with patch('exabox.ovm.sysimghandler.__getVMImagesInRepo', return_value=_VMImagesInRepo),\
            patch('exabox.utils.node.exaBoxNode.mCompareFiles', return_value=True):
            _image_found = _nc.mGetSystemImage(_dom0, 'System.first.boot.25.1.2.0.0.250213.1.rtg.img')
            self.assertEqual(_image_found, 'System.first.boot.25.1.2.0.0.250213.1.img')

    # Auto-generated test for mGetGridImageFromDom0
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogTrace')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mGetGridImageFromDom0_returns_first_matching_image(self, mock_get_ctx, mock_connect, mock_log_trace):

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, _options)

        mock_ctx = MagicMock()
        mock_get_ctx.return_value = mock_ctx

        stdout = MagicMock()
        stdout.read.return_value = '/EXAVMIMAGES/grid-klone-Linux-x86-64-19000250121.zip\n/EXAVMIMAGES/grid-klone-Linux-x86-64-ABCD1234.zip\n'

        node = MagicMock()
        node.mExecuteCmd.return_value = (None, stdout, None)
        node.mGetCmdExitStatus.return_value = 0

        context = MagicMock()
        context.__enter__.return_value = node
        context.__exit__.return_value = False
        mock_connect.return_value = context

        result = node_recovery.mGetGridImageFromDom0('dom0-host')

        expected_command = 'ls -1 /EXAVMIMAGES/grid-klone-Linux-x86-64-*.zip'
        node.mExecuteCmd.assert_called_once_with(expected_command)
        mock_connect.assert_called_once_with('dom0-host', mock_ctx)
        self.assertEqual(result, '/EXAVMIMAGES/grid-klone-Linux-x86-64-19000250121.zip')
        mock_log_trace.assert_any_call('Found valid image: /EXAVMIMAGES/grid-klone-Linux-x86-64-19000250121.zip')

    # Auto-generated test for mExecutePreVMStep
    @patch('exabox.ovm.cluvmrecoveryutils.clubonding')
    def test_mExecutePreVMStep_handles_dynamic_bridge_cleanup(self, mock_clubonding):

        options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, options)

        payload = {'dummy': 'payload'}

        with patch.object(cluctrl, 'mAcquireRemoteLock') as mock_lock, \
             patch.object(cluctrl, 'mReleaseRemoteLock') as mock_unlock:

            mock_clubonding.is_static_monitoring_bridge_supported.side_effect = [False, True]

            node_recovery.mExecutePreVMStep('dom0-source', 'domu-target', payload)

        mock_lock.assert_called_once()
        mock_unlock.assert_called_once()
        mock_clubonding.migrate_static_bridges.assert_called_once_with(cluctrl, payload)
        mock_clubonding.cleanup_bonding_if_enabled.assert_called_once_with(
            cluctrl,
            payload=payload,
            cleanup_bridge=True,
            cleanup_monitor=False
        )
        mock_clubonding.update_bonded_bridges.assert_called_once_with(cluctrl, payload=payload)

    # Auto-generated test for mGetGridImageFromDom0
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogTrace')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mGetGridImageFromDom0_returns_none_on_nonzero_exit(self, mock_get_ctx, mock_connect, mock_log_trace):

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, _options)

        mock_ctx = MagicMock()
        mock_get_ctx.return_value = mock_ctx

        stdout = MagicMock()
        stdout.read.return_value = ''

        node = MagicMock()
        node.mExecuteCmd.return_value = (None, stdout, None)
        node.mGetCmdExitStatus.return_value = 1

        context = MagicMock()
        context.__enter__.return_value = node
        context.__exit__.return_value = False
        mock_connect.return_value = context

        result = node_recovery.mGetGridImageFromDom0('dom0-host')

        expected_command = 'ls -1 /EXAVMIMAGES/grid-klone-Linux-x86-64-*.zip'
        node.mExecuteCmd.assert_called_once_with(expected_command)
        mock_connect.assert_called_once_with('dom0-host', mock_ctx)
        self.assertIsNone(result)
        mock_log_trace.assert_any_call('No valid grid image found in the list.')

    # Auto-generated test for mGetGridImageFromDom0
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogTrace')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mGetGridImageFromDom0_logs_error_on_exception(self, mock_get_ctx, mock_connect, mock_log_error, mock_log_trace):

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, _options)

        mock_ctx = MagicMock()
        mock_get_ctx.return_value = mock_ctx

        context = MagicMock()
        context.__enter__.side_effect = RuntimeError('connect failed')
        context.__exit__.return_value = False
        mock_connect.return_value = context

        result = node_recovery.mGetGridImageFromDom0('dom0-host')

        mock_connect.assert_called_once_with('dom0-host', mock_ctx)
        mock_log_error.assert_called_once_with('Error cheking grid image in dom0 dom0-host, error: connect failed')
        mock_log_trace.assert_not_called()
        self.assertIsNone(result)

    # Auto-generated test for mCheckGridImageOndomO
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogTrace')
    @patch('exabox.ovm.cluvmrecoveryutils.getDom0VMImageLocation', return_value='/EXAVMIMAGES/')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mCheckGridImageOndomO_returns_true_when_image_present(self, mock_get_ctx, mock_connect, mock_get_location, mock_log_trace):

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, _options)

        mock_ctx = MagicMock()
        mock_get_ctx.return_value = mock_ctx

        node = MagicMock()
        node.mFileExists.return_value = True

        context = MagicMock()
        context.__enter__.return_value = node
        context.__exit__.return_value = False
        mock_connect.return_value = context

        result = node_recovery.mCheckGridImageOndomO('dom0-host', 'grid-klone.zip')

        node.mFileExists.assert_called_once_with('/EXAVMIMAGES/grid-klone.zip')
        mock_log_trace.assert_called_once_with('Grid image: grid-klone.zip present in dom0: dom0-host')
        self.assertTrue(result)

    # Auto-generated test for mCheckGridImageOndomO
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogTrace')
    @patch('exabox.ovm.cluvmrecoveryutils.getDom0VMImageLocation', return_value='/EXAVMIMAGES/')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mCheckGridImageOndomO_returns_none_when_image_missing(self, mock_get_ctx, mock_connect, mock_get_location, mock_log_trace):

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, _options)

        mock_ctx = MagicMock()
        mock_get_ctx.return_value = mock_ctx

        node = MagicMock()
        node.mFileExists.return_value = False

        context = MagicMock()
        context.__enter__.return_value = node
        context.__exit__.return_value = False
        mock_connect.return_value = context

        result = node_recovery.mCheckGridImageOndomO('dom0-host', 'grid-klone.zip')

        node.mFileExists.assert_called_once_with('/EXAVMIMAGES/grid-klone.zip')
        mock_log_trace.assert_not_called()
        self.assertIsNone(result)

    # Auto-generated test for mCheckGridImageOndomO
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.getDom0VMImageLocation', return_value='/EXAVMIMAGES/')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host', side_effect=RuntimeError('connect failed'))
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mCheckGridImageOndomO_logs_error_on_exception(self, mock_get_ctx, mock_connect, mock_get_location, mock_log_error):

        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, _options)

        result = node_recovery.mCheckGridImageOndomO('dom0-host', 'grid-klone.zip')

        mock_log_error.assert_called_once_with('Grid image: grid-klone.zip missing in dom0: dom0-host !')
        self.assertIsNone(result)
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
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.uefi.img",  aRc=1, aStdout="", aPersist=True),
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
                    exaMockCommand("/bin/test -e /EXAVMIMAGES/System.first.boot.25.1.2.0.0.250213.1.uefi.img",  aRc=1, aStdout="", aPersist=True),
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
                'isKvmImg': False, 'isRtgImg': False, 'isArchive': True, 'isUefiImg': False},
             {'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.25.1.2.0.0.250213.1.img.bz2',
              'fileBaseName': 'System.first.boot.25.1.2.0.0.250213.1.img.bz2',
              'imgBaseName': 'System.first.boot.25.1.2.0.0.250213.1.img',
              'imgArchiveBaseName': 'System.first.boot.25.1.2.0.0.250213.1.img.bz2',
              'imgVersion': '25.1.2.0.0.250213.1', 'isKvmImg': False, 'isRtgImg': False, 'isArchive': True, 'isUefiImg': False}, 
             {'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.26.1.2.0.0.250213.1.kvm.img.bz2', 
              'fileBaseName': 'System.first.boot.26.1.2.0.0.250213.1.kvm.img.bz2', 
              'imgBaseName': 'System.first.boot.26.1.2.0.0.250213.1.kvm.img', 
              'imgArchiveBaseName': 'System.first.boot.26.1.2.0.0.250213.1.kvm.img.bz2', 
              'imgVersion': '26.1.2.0.0.250213.1', 'isKvmImg': True, 'isRtgImg': False, 'isArchive': True, 'isUefiImg': False}, 
             {'filePath': '/u01/oracle/ecra_installs/naramaliorg/mw_home/user_projects/domains/exacloud/images/System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz2', 
              'fileBaseName': 'System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz2', 
              'imgBaseName': 'System.first.boot.25.1.2.0.0.250213.1.rtg.img', 
              'imgArchiveBaseName': 'System.first.boot.25.1.2.0.0.250213.1.rtg.img.bz2', 
              'imgVersion': '25.1.2.0.0.250213.1', 'isKvmImg': False, 'isRtgImg': True, 'isArchive': True, 'isUefiImg': False}
             ]
        with patch('exabox.ovm.sysimghandler.__getVMImagesInRepo', return_value=_VMImagesInRepo):
            _nc.mVerifySystemAndGridImages(_dom0, _domU)


    # Auto-generated test for mVerifySystemAndGridImages
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    def test_mVerifySystemAndGridImages_raises_when_xml_missing(self, mock_log_error):
        # Auto-generated test for mVerifySystemAndGridImages
        options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, options)

        with patch.object(NodeRecovery, 'mParseXMLForNodeRecovery', return_value=[]):
            with self.assertRaises(ExacloudRuntimeError) as ctx:
                node_recovery.mVerifySystemAndGridImages('dom0-host', 'domu-host')

        expected = "Unable to parsel XML /EXAVMIMAGES/conf/domu-host-vm.xml"
        self.assertIn(expected, str(ctx.exception))
        mock_log_error.assert_called_once_with(expected)

    # Auto-generated test for mVerifySystemAndGridImages
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    def test_mVerifySystemAndGridImages_raises_when_system_image_missing(self, mock_log_error):
        # Auto-generated test for mVerifySystemAndGridImages
        options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, options)

        system_image = 'System.first.boot.25.1.2.0.0.250213.1.img'
        grid_image = 'grid-klone-Linux-x86-64-19000250121.zip'
        with patch.object(NodeRecovery, 'mParseXMLForNodeRecovery', return_value=[system_image, grid_image]), \
             patch.object(NodeRecovery, 'mGetSystemImage', return_value=None):
            with self.assertRaises(ExacloudRuntimeError) as ctx:
                node_recovery.mVerifySystemAndGridImages('dom0-host', 'domu-host')

        expected = f'System image {system_image} not present in dom0 dom0-host and exacloud image repo'
        self.assertIn(expected, str(ctx.exception))
        mock_log_error.assert_called_once_with(expected)

    # Auto-generated test for mVerifySystemAndGridImages
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    def test_mVerifySystemAndGridImages_system_update_failure_raises(self, mock_log_error):
        options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, options)

        original_image = 'System.first.boot.25.1.2.0.0.250213.1.img'
        replacement_image = 'System.first.boot.26.1.2.0.0.250213.1.img'
        grid_image = 'grid-klone-Linux-x86-64-19000250121.zip'

        with patch.object(NodeRecovery, 'mParseXMLForNodeRecovery', return_value=[original_image, grid_image]), \
             patch.object(NodeRecovery, 'mGetSystemImage', return_value=replacement_image), \
             patch.object(NodeRecovery, 'mUpdateXMLTagValue', return_value=False) as mock_update, \
             patch.object(NodeRecovery, 'mCheckGridImageOndomO') as mock_check_grid:
            with self.assertRaises(ExacloudRuntimeError) as ctx:
                node_recovery.mVerifySystemAndGridImages('dom0-host', 'domu-host')

        expected = f'System image /EXAVMIMAGES/{replacement_image} could not be updated in XML'
        self.assertIn(expected, str(ctx.exception))
        mock_update.assert_called_once_with('dom0-host', '/EXAVMIMAGES/conf/domu-host-vm.xml', f'/EXAVMIMAGES/{replacement_image}')
        mock_check_grid.assert_not_called()
        self.assertIn(expected, [call[0][0] for call in mock_log_error.call_args_list])

    # Auto-generated test for mVerifySystemAndGridImages
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    def test_mVerifySystemAndGridImages_grid_update_failure_raises(self, mock_log_error):
        options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, options)

        system_image = 'System.first.boot.25.1.2.0.0.250213.1.img'
        grid_image = 'grid-klone-Linux-x86-64-19000250121.zip'
        grid_replacement = '/EXAVMIMAGES/grid-klone-Linux-x86-64-23000250121.zip'

        with patch.object(NodeRecovery, 'mParseXMLForNodeRecovery', return_value=[system_image, grid_image]), \
             patch.object(NodeRecovery, 'mGetSystemImage', return_value=system_image), \
             patch.object(NodeRecovery, 'mCheckGridImageOndomO', return_value=False) as mock_check_grid, \
             patch.object(NodeRecovery, 'mGetGridImageFromDom0', return_value=grid_replacement) as mock_get_grid, \
             patch.object(NodeRecovery, 'mUpdateXMLTagValue', return_value=False) as mock_update:
            with self.assertRaises(ExacloudRuntimeError) as ctx:
                node_recovery.mVerifySystemAndGridImages('dom0-host', 'domu-host')

        expected = f'System image {grid_replacement} could not be updated in XML'
        self.assertIn(expected, str(ctx.exception))
        mock_check_grid.assert_called_once_with('dom0-host', grid_image)
        mock_get_grid.assert_called_once_with('dom0-host')
        mock_update.assert_called_once_with('dom0-host', '/EXAVMIMAGES/conf/domu-host-vm.xml', grid_replacement)
        self.assertIn(expected, [call[0][0] for call in mock_log_error.call_args_list])


    # Auto-generated test for mGetSystemImage
    def test_mGetSystemImage_invalid_image_name(self):
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _ = cluctrl.mReturnDom0DomUPair()[0]

        invalid_image = "invalid.img"
        with patch("exabox.ovm.cluvmrecoveryutils.copyVMImageVersionToDom0IfMissing") as mock_copy:
            _image_found = _nc.mGetSystemImage(_dom0, invalid_image)

        self.assertIsNone(_image_found)
        mock_copy.assert_not_called()

    def test_mInstallRpm_ol7_exabm_updates_dom0_pair(self):
        # Auto-generated test for mInstallRpm
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]

        with patch.object(cluctrl, 'mGetOracleLinuxVersion', return_value='OL7'), \
             patch.object(cluctrl, 'mIsExabm', return_value=True), \
             patch.object(cluctrl, 'mUpdateRpm') as mock_update:
            _nc.mInstallRpm(_dom0, _domU)

        mock_update.assert_has_calls([
            call('dbcs-agent.OL7.x86_64.rpm', aUndo=True, aDom0DomUPair=[[_dom0, _domU]]),
            call('dbcs-agent.OL7.x86_64.rpm', aDom0DomUPair=[[_dom0, _domU]], aForce=True)
        ])

    def test_mInstallRpm_ol7_exacc_updates_expected_packages(self):
        # Auto-generated test for mInstallRpm
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]

        with patch.object(cluctrl, 'mGetOracleLinuxVersion', return_value='OL8'), \
             patch.object(cluctrl, 'mIsExabm', return_value=False), \
             patch.object(cluctrl, 'mIsOciEXACC', return_value=True), \
             patch.object(cluctrl, 'mUpdateRpm') as mock_update:
            _nc.mInstallRpm(_dom0, _domU)

        mock_update.assert_has_calls([
            call('dbcs-agent-exacc.OL7.x86_64.rpm', aUndo=True, aDom0DomUPair=[[_dom0, _domU]]),
            call('dbcs-agent-exacc.OL7.x86_64.rpm', aDom0DomUPair=[[_dom0, _domU]], aForce=True)
        ])

    def test_mInstallRpm_ol6_exabm_uses_legacy_package(self):
        # Auto-generated test for mInstallRpm
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]

        with patch.object(cluctrl, 'mGetOracleLinuxVersion', return_value='OL6'), \
             patch.object(cluctrl, 'mIsExabm', return_value=True), \
             patch.object(cluctrl, 'mUpdateRpm') as mock_update:
            _nc.mInstallRpm(_dom0, _domU)

        mock_update.assert_has_calls([
            call('dbcs-agent.OL6.x86_64.rpm', aUndo=True, aDom0DomUPair=[[_dom0, _domU]]),
            call('dbcs-agent.OL6.x86_64.rpm', aDom0DomUPair=[[_dom0, _domU]], aForce=True)
        ])

    def test_mInstallRpm_ol6_exacc_updates_expected_packages(self):
        # Auto-generated test for mInstallRpm
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]

        with patch.object(cluctrl, 'mGetOracleLinuxVersion', return_value='OL6'), \
             patch.object(cluctrl, 'mIsExabm', return_value=False), \
             patch.object(cluctrl, 'mIsOciEXACC', return_value=True), \
             patch.object(cluctrl, 'mUpdateRpm') as mock_update:
            _nc.mInstallRpm(_dom0, _domU)

        mock_update.assert_has_calls([
            call('dbcs-agent-exacc.OL6.x86_64.rpm', aUndo=True, aDom0DomUPair=[[_dom0, _domU]]),
            call('dbcs-agent-exacc.OL6.x86_64.rpm', aDom0DomUPair=[[_dom0, _domU]], aForce=True)
        ])

    # Auto-generated test for mGetSystemImageOndomO
    @patch('exabox.ovm.cluvmrecoveryutils.getDom0VMImagesInfo')
    def test_mGetSystemImageOndomO_returns_latest_version(self, mock_get_info):

        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _ = cluctrl.mReturnDom0DomUPair()[0]

        mock_get_info.return_value = [
            {"imgVersion": "25.1.2.0.0.250213.1"},
            {"imgVersion": "25.1.2.0.0.250213.5"},
            {"imgVersion": "25.1.2.0.0.250213.3"},
        ]

        result = _nc.mGetSystemImageOndomO(_dom0)

        self.assertEqual(result, "25.1.2.0.0.250213.5")

    # Auto-generated test for mGetSystemImageOndomO
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.getDom0VMImagesInfo', return_value=[])
    def test_mGetSystemImageOndomO_handles_empty_list(self, mock_get_info, mock_log_info):

        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _ = cluctrl.mReturnDom0DomUPair()[0]

        result = _nc.mGetSystemImageOndomO(_dom0)

        self.assertIsNone(result)
        mock_get_info.assert_called_once_with(_dom0)
        mock_log_info.assert_any_call(f"No system image present on {_dom0}")

    # Auto-generated test for mGetSystemImageOndomO
    @patch('exabox.ovm.cluvmrecoveryutils.traceback.format_exc', return_value='stack-trace')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.getDom0VMImagesInfo', side_effect=RuntimeError('boom'))
    def test_mGetSystemImageOndomO_logs_error_on_failure(self, mock_get_info, mock_log_error, mock_traceback):

        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _ = cluctrl.mReturnDom0DomUPair()[0]

        result = _nc.mGetSystemImageOndomO(_dom0)

        self.assertIsNone(result)
        mock_get_info.assert_called_once_with(_dom0)
        mock_traceback.assert_called_once_with()
        self.assertIn(_dom0, mock_log_error.call_args[0][0])

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mGetServiceStatus_returns_running_when_active(self, mock_get_ctx, mock_node_cls, mock_log_error, mock_log_info):
        # Auto-generated test for mGetServiceStatus
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        node_instance = MagicMock()
        stdout = MagicMock()
        stdout.readlines.return_value = ['active\n']
        node_instance.mExecuteCmd.return_value = (None, stdout, None)
        mock_node_cls.return_value = node_instance

        status = _nc.mGetServiceStatus('domu-host', 'dbcsagent')

        mock_node_cls.assert_called_once_with(mock_get_ctx.return_value)
        node_instance.mConnect.assert_called_once_with(aHost='domu-host')
        node_instance.mExecuteCmd.assert_called_once_with('/bin/systemctl is-active dbcsagent')
        node_instance.mDisconnect.assert_called_once()
        self.assertEqual(status, 'running')
        mock_log_info.assert_called_once_with('*** dbcsagent service running on DOMU:domu-host')
        mock_log_error.assert_not_called()

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mGetServiceStatus_handles_empty_output_as_stopped(self, mock_get_ctx, mock_node_cls, mock_log_error, mock_log_info):
        # Auto-generated test for mGetServiceStatus
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        node_instance = MagicMock()
        stdout = MagicMock()
        stdout.readlines.return_value = []
        node_instance.mExecuteCmd.return_value = (None, stdout, None)
        mock_node_cls.return_value = node_instance

        status = _nc.mGetServiceStatus('domu-host', 'dbcsagent')

        self.assertEqual(status, 'stopped')
        mock_log_error.assert_called_once_with('*** dbcsagent service stopped on DOMU:domu-host')
        mock_log_info.assert_not_called()

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogWarn')
    @patch('exabox.ovm.cluvmrecoveryutils.time.sleep')
    @patch('exabox.ovm.cluvmrecoveryutils.time.time')
    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mCheckSshd_returns_true_when_port_becomes_available(self, mock_get_ctx, mock_node_cls, mock_time_time, mock_time_sleep, mock_log_warn):
        # Auto-generated test for mCheckSshd
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        mock_ctx = MagicMock()
        mock_ctx.mCheckRegEntry.return_value = False
        mock_get_ctx.return_value = mock_ctx

        mock_time_time.side_effect = [0, 1]
        mock_time_sleep.side_effect = lambda *_args, **_kwargs: None

        local_node = MagicMock()
        local_node.mCheckPortSSH.return_value = True
        mock_node_cls.return_value = local_node

        result = _nc.mCheckSshd('domu-host', 10, 2)

        self.assertTrue(result)
        local_node.mConnect.assert_called_once()
        local_node.mCheckPortSSH.assert_called_once_with('domu-host')
        local_node.mDisconnect.assert_called_once()
        mock_log_warn.assert_not_called()

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogWarn')
    @patch('exabox.ovm.cluvmrecoveryutils.time.sleep')
    @patch('exabox.ovm.cluvmrecoveryutils.time.time')
    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mCheckSshd_returns_false_after_timeout(self, mock_get_ctx, mock_node_cls, mock_time_time, mock_time_sleep, mock_log_warn, mock_log_error):
        # Auto-generated test for mCheckSshd
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        mock_ctx = MagicMock()
        mock_ctx.mCheckRegEntry.return_value = False
        mock_get_ctx.return_value = mock_ctx

        mock_time_time.side_effect = [0, 2, 6]
        mock_time_sleep.side_effect = lambda *_args, **_kwargs: None

        local_node = MagicMock()
        local_node.mCheckPortSSH.side_effect = [False, False]
        mock_node_cls.return_value = local_node

        result = _nc.mCheckSshd('domu-host', 5, 1)

        self.assertFalse(result)
        self.assertTrue(mock_log_warn.called)
        mock_log_error.assert_called_once_with('*** Timeout while waiting for ssh port')
        local_node.mDisconnect.assert_called_once()

    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mUpdateSSHKeys_uses_existing_entry(self, mock_get_ctx, mock_node_cls):
        # Auto-generated test for mUpdateSSHKeys
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        entry = MagicMock()
        entry.mGetPublicKey.return_value = 'EXISTING_KEY\n'

        exakms = MagicMock()
        exakms.mGetExaKmsEntry.return_value = entry

        mock_ctx = MagicMock()
        mock_ctx.mGetExaKms.return_value = exakms
        mock_get_ctx.return_value = mock_ctx

        node_instance = MagicMock()
        mock_node_cls.return_value = node_instance

        _nc.mUpdateSSHKeys('dom0-host', 'domu-host', '/mnt', 'root')

        node_instance.mConnect.assert_called_once_with(aHost='dom0-host')
        node_instance.mDisconnect.assert_called_once()
        executed_cmd = node_instance.mExecuteCmdLog.call_args[0][0]
        self.assertIn('/mnt/root/.ssh/authorized_keys', executed_cmd)
        self.assertIn('EXISTING_KEY', executed_cmd)

    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mUpdateSSHKeys_creates_new_entry_when_missing(self, mock_get_ctx, mock_node_cls):
        # Auto-generated test for mUpdateSSHKeys
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        dummy_entry = MagicMock()
        dummy_entry.mGetPrivateKey.return_value = 'PRIVATE'

        new_entry = MagicMock()
        new_entry.mGetPublicKey.return_value = 'NEW_KEY'

        entry_class = MagicMock()
        entry_class.mGeneratePrivateKey.return_value = 'PRIVATE'

        exakms = MagicMock()
        exakms.mGetExaKmsEntry.return_value = None
        exakms.mGetEntryClass.return_value = entry_class
        exakms.mBuildExaKmsEntry.side_effect = [dummy_entry, new_entry]

        mock_ctx = MagicMock()
        mock_ctx.mGetExaKms.return_value = exakms
        mock_get_ctx.return_value = mock_ctx

        node_instance = MagicMock()
        mock_node_cls.return_value = node_instance

        _nc.mUpdateSSHKeys('dom0-host', 'domu-host', '/mnt', 'root')

        exakms.mInsertExaKmsEntry.assert_called_once_with(new_entry)
        executed_cmd = node_instance.mExecuteCmdLog.call_args[0][0]
        self.assertIn('NEW_KEY', executed_cmd)
        node_instance.mDisconnect.assert_called_once()

    @patch('exabox.ovm.cluvmrecoveryutils.QuorumDiskManager')
    def test_mCreateQuorumDevices_invokes_manager_flows(self, mock_qdm_cls):
        # Auto-generated test for mCreateQuorumDevices
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        mock_manager = MagicMock()
        mock_qdm_cls.return_value = mock_manager

        _nc.mCreateQuorumDevices('domu-test')

        suffix = cluctrl.mGetClusterSuffix()
        mock_manager.mDeleteQuorum.assert_called_once_with('domu-test', suffix)
        mock_manager.mCreateQuorum.assert_called_once_with('domu-test', suffix)

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mGetServiceStatus_returns_empty_when_no_output_object(self, mock_get_ctx, mock_node_cls, mock_log_error, mock_log_info):
        # Auto-generated test for mGetServiceStatus
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        node_instance = MagicMock()
        node_instance.mExecuteCmd.return_value = (None, None, None)
        mock_node_cls.return_value = node_instance

        status = _nc.mGetServiceStatus('domu-host', 'dbcsagent')

        self.assertEqual(status, '')
        mock_log_error.assert_not_called()
        mock_log_info.assert_not_called()
        node_instance.mDisconnect.assert_called_once()

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mGetServiceStatus_logs_error_when_inactive(self, mock_get_ctx, mock_node_cls, mock_log_error, mock_log_info):
        # Auto-generated test for mGetServiceStatus
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        node_instance = MagicMock()
        stdout = MagicMock()
        stdout.readlines.return_value = ['inactive\n']
        node_instance.mExecuteCmd.return_value = (None, stdout, None)
        mock_node_cls.return_value = node_instance

        status = _nc.mGetServiceStatus('domu-host', 'dbcsagent')

        self.assertEqual(status, 'stopped')
        mock_log_error.assert_called_once_with('*** dbcsagent service stopped on DOMU:domu-host')
        mock_log_info.assert_not_called()
        node_instance.mDisconnect.assert_called_once()

    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mGetServiceStatus_disconnects_on_connect_failure(self, mock_get_ctx, mock_node_cls):
        # Auto-generated test for mGetServiceStatus
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        node_instance = MagicMock()
        node_instance.mConnect.side_effect = RuntimeError('connect failed')
        mock_node_cls.return_value = node_instance

        with self.assertRaises(RuntimeError):
            _nc.mGetServiceStatus('domu-host', 'dbcsagent')

        node_instance.mDisconnect.assert_called_once()

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.node_update_key_val_file')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.ebCluDbaas')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mUpdateNetworkConfig_route_missing_logs_error(self, mock_get_ctx, mock_dbaas, mock_connect, mock_update_key, mock_log_error):
        # Auto-generated test for mUpdateNetworkConfig
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _nc._NodeRecovery__adminNetwork = {
            "IPADDR": "169.254.200.10",
            "NETMASK": "255.255.255.0",
            "GATEWAY": "169.254.200.1",
            "NETWORK": "169.254.200.0",
            "BROADCAST": "169.254.200.255",
        }

        ctx = MagicMock()
        ctx.mCheckRegEntry.return_value = False
        mock_get_ctx.return_value = ctx

        host = MagicMock()
        host.mFileExists.side_effect = lambda path: True

        def _exec_side_effect(cmd):
            stdout = MagicMock()
            if 'grep 169.254.200' in cmd:
                stdout.readlines.return_value = ['ListenAddress 169.254.200.8']
            elif 'head -1' in cmd and 'route-eth0' in cmd:
                stdout.readlines.return_value = []
            elif 'head -1' in cmd and 'rule-eth0' in cmd:
                stdout.readlines.return_value = ['169.254.200.0 dev eth0 tab 201']
            else:
                stdout.readlines.return_value = ['noop']
            return (None, stdout, None)

        host.mExecuteCmd.side_effect = _exec_side_effect
        ctx_mgr = MagicMock()
        ctx_mgr.__enter__.return_value = host
        ctx_mgr.__exit__.return_value = False
        mock_connect.return_value = ctx_mgr

        _nc.mUpdateNetworkConfig('dom0.example.com', 'domu.example.com', '/mnt/sys', 'root')

        mock_update_key.assert_not_called()
        mock_log_error.assert_called_once_with('*** Failed to Update admin ip in network configuration files for VM:domu.example.com')

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.node_update_key_val_file')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.ebCluDbaas')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mUpdateNetworkConfig_nat_missing_logs_error(self, mock_get_ctx, mock_dbaas, mock_connect, mock_update_key, mock_log_error):
        # Auto-generated test for mUpdateNetworkConfig
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _nc._NodeRecovery__adminNetwork = {
            "IPADDR": "169.254.200.10",
            "NETMASK": "255.255.255.0",
            "GATEWAY": "169.254.200.1",
            "NETWORK": "169.254.200.0",
            "BROADCAST": "169.254.200.255",
        }

        ctx = MagicMock()
        ctx.mCheckRegEntry.return_value = True
        ctx.mGetRegEntry.return_value = 'nat.example.com'
        mock_get_ctx.return_value = ctx

        host = MagicMock()
        host.mFileExists.return_value = True
        host._disconnect_called = False

        def _disconnect_side_effect(*_args, **_kwargs):
            host._disconnect_called = True

        host.mDisconnect.side_effect = _disconnect_side_effect

        def _exec_side_effect(cmd):
            stdout = MagicMock()
            if 'grep 169.254.200' in cmd:
                stdout.readlines.return_value = ['ListenAddress 169.254.200.8']
            elif 'head -1' in cmd and 'route-eth0' in cmd:
                stdout.readlines.return_value = ['169.254.200.0 dev eth0 tab 201']
            elif 'tail -1' in cmd and 'route-eth0' in cmd:
                stdout.readlines.return_value = ['default via 169.254.200.1 dev eth0']
            elif 'head -1' in cmd and 'rule-eth0' in cmd:
                stdout.readlines.return_value = ['from 169.254.200.0/24 table 201']
            elif 'grep -E' in cmd:
                stdout.readlines.return_value = ['169.254.200.1 natcps nat.localdomain']
            elif '/bin/grep nat ' in cmd:
                stdout.readlines.return_value = []
            else:
                stdout.readlines.return_value = ['noop']
            return (None, stdout, None)

        host.mExecuteCmd.side_effect = _exec_side_effect
        ctx_mgr = MagicMock()
        ctx_mgr.__enter__.return_value = host

        def _exit_side_effect(*args):
            host.mDisconnect()
            return False

        ctx_mgr.__exit__.side_effect = _exit_side_effect
        mock_connect.return_value = ctx_mgr

        _nc.mUpdateNetworkConfig('dom0.example.com', 'domu.example.com', '/mnt/sys', 'root')

        self.assertTrue(host._disconnect_called)
        ctx_mgr.__exit__.assert_called()
        mock_log_error.assert_any_call('*** Failed to Update admin ip in network configuration files for VM:domu.example.com')

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.node_update_key_val_file')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.ebCluDbaas')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mUpdateNetworkConfig_success_updates_all_files(self, mock_get_ctx, mock_dbaas, mock_connect, mock_update_key, mock_log_error):
        # Auto-generated test for mUpdateNetworkConfig
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _nc._NodeRecovery__adminNetwork = {
            "IPADDR": "169.254.200.10",
            "NETMASK": "255.255.255.0",
            "GATEWAY": "169.254.200.1",
            "NETWORK": "169.254.200.0",
            "BROADCAST": "169.254.200.255",
        }

        ctx = MagicMock()
        ctx.mCheckRegEntry.return_value = True
        ctx.mGetRegEntry.return_value = 'nat.example.com'
        mock_get_ctx.return_value = ctx

        host = MagicMock()
        host._disconnect_called = False
        host.mReadFile.return_value = """
<Cell>
    <Interfaces>
        <Name>eth0</Name>
        <IP_address>169.254.200.8</IP_address>
        <Netmask>255.255.255.0</Netmask>
        <Gateway>169.254.200.2</Gateway>
    </Interfaces>
</Cell>
"""

        def _disconnect_side_effect(*_args, **_kwargs):
            host._disconnect_called = True

        host.mDisconnect.side_effect = _disconnect_side_effect

        def _exec_side_effect(cmd):
            stdout = MagicMock()
            if 'grep 169.254.200' in cmd:
                stdout.readlines.return_value = ['ListenAddress 169.254.200.8']
            elif 'head -1' in cmd and 'route-eth0' in cmd:
                stdout.readlines.return_value = ['169.254.200.0/24 via 169.254.200.1 dev eth0']
            elif 'tail -1' in cmd and 'route-eth0' in cmd:
                stdout.readlines.return_value = ['default via 169.254.200.1 dev eth0']
            elif 'head -1' in cmd and 'rule-eth0' in cmd:
                stdout.readlines.return_value = ['from 169.254.200.0/24 lookup 201']
            elif "grep -E" in cmd:
                stdout.readlines.return_value = ['169.254.200.1 natcps nat.localdomain']
            elif '/bin/grep nat ' in cmd:
                stdout.readlines.return_value = ['169.254.200.8 nat.example.com']
            else:
                stdout.readlines.return_value = ['noop']
            return (None, stdout, None)

        host.mExecuteCmd.side_effect = _exec_side_effect
        host.mExecuteCmdLog.side_effect = lambda *_args, **_kwargs: None
        host.mFileExists.return_value = True
        host.mWriteFile.side_effect = lambda *_args, **_kwargs: None

        ctx_mgr = MagicMock()
        ctx_mgr.__enter__.return_value = host

        def _exit_success(*args):
            host.mDisconnect()
            return False

        ctx_mgr.__exit__.side_effect = _exit_success
        mock_connect.return_value = ctx_mgr

        _nc.mUpdateNetworkConfig('dom0.example.com', 'domu.example.com', '/mnt/sys', 'root')

        self.assertTrue(host.mExecuteCmdLog.call_args_list)
        self.assertEqual(host.mWriteFile.call_count, 1)
        self.assertEqual(mock_update_key.call_count, 5)
        mock_log_error.assert_not_called()
        self.assertTrue(host._disconnect_called)

    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mStartService_invokes_systemctl_start(self, mock_get_ctx, mock_node_cls):
        # Auto-generated test for mStartService
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        _node_instance = MagicMock()
        mock_node_cls.return_value = _node_instance
        mock_get_ctx.return_value = MagicMock()

        _nc.mStartService('domu-host', 'dbcsagent')

        mock_node_cls.assert_called_once_with(mock_get_ctx.return_value)
        _node_instance.mConnect.assert_called_once_with(aHost='domu-host')
        _node_instance.mExecuteCmdLog.assert_called_once_with('/bin/systemctl start dbcsagent')
        _node_instance.mDisconnect.assert_called_once()

    def test_mStartServices_starts_missing_services_and_updates_kvm(self):
        # Auto-generated test for mStartServices
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]

        with patch.object(_nc, 'mGetServiceStatus', side_effect=['stopped', 'stopped', 'stopped']) as mock_status, \
             patch.object(_nc, 'mStartService') as mock_start_service, \
             patch.object(cluctrl, 'mIsKVM', return_value=True), \
             patch.object(cluctrl, 'mUpdateVmetrics') as mock_update_vmetrics, \
             patch.object(cluctrl, 'mStartVMExacsService') as mock_start_vm:
            _nc.mStartServices(_dom0, _domU)

        mock_status.assert_has_calls([
            call(_domU, aService='dbcsagent'),
            call(_domU, aService='dbcsadmin'),
            call(_domU, aService='syslens')
        ])
        mock_start_service.assert_has_calls([
            call(_domU, aService='dbcsagent'),
            call(_domU, aService='dbcsadmin'),
            call(_domU, aService='syslens')
        ])
        mock_update_vmetrics.assert_called_once_with('vmexacs_kvm')
        mock_start_vm.assert_called_once_with(_options, aDom0DomUPair=[[_dom0, _domU]])

    def test_mStartServices_skips_running_services(self):
        # Auto-generated test for mStartServices
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)
        _dom0, _domU = cluctrl.mReturnDom0DomUPair()[0]

        with patch.object(_nc, 'mGetServiceStatus', side_effect=['running', 'running', 'running']) as mock_status, \
             patch.object(_nc, 'mStartService') as mock_start_service, \
             patch.object(cluctrl, 'mIsKVM', return_value=False), \
             patch.object(cluctrl, 'mUpdateVmetrics') as mock_update_vmetrics, \
             patch.object(cluctrl, 'mStartVMExacsService') as mock_start_vm:
            _nc.mStartServices(_dom0, _domU)

        self.assertEqual(mock_status.call_count, 3)
        mock_start_service.assert_not_called()
        mock_update_vmetrics.assert_not_called()
        mock_start_vm.assert_not_called()

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mRestoreRootAccessForRestoredNode_executes_command(self, mock_get_ctx, mock_connect, mock_log_error):
        # Auto-generated test for mRestoreRootAccessForRestoredNode
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        mock_ctx = MagicMock()
        mock_get_ctx.return_value = mock_ctx

        mock_node = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_node
        mock_connect.return_value.__exit__.return_value = False

        _nc.mRestoreRootAccessForRestoredNode('domu-host')

        mock_connect.assert_called_once_with('domu-host', mock_ctx, username='opc')
        mock_node.mExecuteCmdLog.assert_called_once_with("sh -c '/opt/oracle.cellos/host_access_control rootssh -u'")
        mock_log_error.assert_not_called()

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mRestoreRootAccessForRestoredNode_logs_and_raises_on_failure(self, mock_get_ctx, mock_connect, mock_log_error):
        # Auto-generated test for mRestoreRootAccessForRestoredNode
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        mock_get_ctx.return_value = MagicMock()
        mock_connect.return_value.__enter__.side_effect = RuntimeError('connect failure')
        mock_connect.return_value.__exit__.return_value = False

        with self.assertRaises(RuntimeError):
            _nc.mRestoreRootAccessForRestoredNode('domu-host')

        mock_connect.assert_called_once()
        mock_log_error.assert_called_once()

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.getHVInstance')
    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mUpdateLibvirtXML_updates_mac_and_backups(self, mock_get_ctx, mock_node_cls, mock_hv, mock_log_error):
        # Auto-generated test for mUpdateLibvirtXML
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        mock_ctx = MagicMock()
        mock_get_ctx.return_value = mock_ctx

        mock_node = MagicMock()
        mock_node_cls.return_value = mock_node
        mock_node.mGetCmdExitStatus.return_value = 0

        stdout = MagicMock()
        stdout.readlines.return_value = ['"52:54:00:11:22:33"']
        mock_node.mExecuteCmd.return_value = (None, stdout, None)

        mock_hv_instance = MagicMock()
        mock_hv_instance.mGetVMUUID.return_value = 'uuid-1234'
        mock_hv_instance.mGetVMAdminBridge.return_value = ('admin_bridge', '52:54:00:aa:bb:cc')
        mock_hv.return_value = mock_hv_instance

        _nc.mUpdateLibvirtXML('dom0-host', 'domu-host')

        mock_node_cls.assert_called_once_with(mock_ctx)
        mock_node.mConnect.assert_called_once_with(aHost='dom0-host')
        mock_hv.assert_called_once_with('dom0-host')
        mock_node.mExecuteCmdLog.assert_has_calls([
            call('/bin/cp -p /EXAVMIMAGES/GuestImages/domu-host/domu-host.xml.libvirt.qemu /EXAVMIMAGES/GuestImages/domu-host/domu-host.xml.libvirt.qemu.backup'),
            call('/bin/cp -p /EXAVMIMAGES/GuestImages/domu-host/admin_bridge.xml /EXAVMIMAGES/GuestImages/domu-host/admin_bridge.xml.backup'),
            call("/bin/sed -i 's|52:54:00:11:22:33|52:54:00:aa:bb:cc|g' /EXAVMIMAGES/GuestImages/domu-host/admin_bridge.xml"),
            call('/bin/cp -p /etc/libvirt/qemu/domu-host.xml /EXAVMIMAGES/GuestImages/domu-host/domu-host.xml.libvirt.qemu'),
        ])
        mock_node.mDisconnect.assert_called_once()
        mock_log_error.assert_not_called()

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.getHVInstance')
    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mUpdateLibvirtXML_logs_error_and_raises_when_mac_missing(self, mock_get_ctx, mock_node_cls, mock_hv, mock_log_error):
        # Auto-generated test for mUpdateLibvirtXML
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        mock_ctx = MagicMock()
        mock_get_ctx.return_value = mock_ctx

        mock_node = MagicMock()
        mock_node_cls.return_value = mock_node
        mock_node.mGetCmdExitStatus.return_value = 1
        stdout_missing = MagicMock()
        stdout_missing.readlines.return_value = []

        mock_node.mExecuteCmd.return_value = (None, stdout_missing, None)

        mock_hv_instance = MagicMock()
        mock_hv_instance.mGetVMUUID.return_value = 'uuid-1234'
        mock_hv_instance.mGetVMAdminBridge.return_value = ('admin_bridge', '52:54:00:aa:bb:cc')
        mock_hv.return_value = mock_hv_instance

        _nc.mUpdateLibvirtXML('dom0-host', 'domu-host')

        mock_node_cls.assert_called_once_with(mock_ctx)
        mock_node.mConnect.assert_called_once_with(aHost='dom0-host')
        mock_hv.assert_called_once_with('dom0-host')
        mock_log_error.assert_any_call('*** mac address is missing from /EXAVMIMAGES/GuestImages/domu-host/admin_bridge.xml')
        mock_log_error.assert_any_call('Failed to updated libvirt XML from VMBackup XML')
        self.assertEqual(mock_node.mDisconnect.call_count, 2)

    def test_mConfigurePasswordlessAllUsers_invokes_configure_for_unique_users(self):
        # Auto-generated test for mConfigurePasswordlessAllUsers
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        unique_users = ['root', 'opc', 'grid']

        user_entries = {idx: user for idx, user in enumerate(['grid', 'root', 'opc', 'root'])}
        users_container = MagicMock()
        users_container.mGetUsers.return_value = user_entries

        def _get_user(entry_id):
            user = user_entries[entry_id]
            mock_user = MagicMock()
            mock_user.mGetUserName.return_value = user
            return mock_user

        users_container.mGetUser.side_effect = _get_user

        with patch.object(cluctrl, 'mGetUsers', return_value=users_container):
            with patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo') as mock_log, \
                 patch.object(_nc, 'mConfigurePasswordLessDomU') as mock_configure:
                _nc.mConfigurePasswordlessAllUsers()
                self.assertCountEqual([call('root'), call('opc'), call('grid')], mock_configure.call_args_list)
                for user in unique_users:
                    mock_log.assert_any_call(f'Configuring passwordless on user {user}')

    def test_mConfigurePasswordLessDomU_raises_runtime_on_primary_failure(self):
        # Auto-generated test for mConfigurePasswordLessDomU
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        fake_domus = ['domu-main', 'domu-other']
        with patch.object(cluctrl, 'mReturnElasticAllDom0DomUPair', return_value=[('dom0-a', fake_domus[0]), ('dom0-b', fake_domus[1])]), \
             patch('exabox.ovm.cluvmrecoveryutils.get_gcontext') as mock_ctx, \
             patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode') as mock_node_cls, \
             patch('exabox.ovm.cluvmrecoveryutils.ebLogError') as mock_log:
            mock_ctx_instance = MagicMock()
            mock_ctx.return_value = mock_ctx_instance

            primary_node = MagicMock()
            primary_node.mReturnValue = None
            primary_node.mFileExists.return_value = False
            primary_node.mExecuteCmd.side_effect = Exception('cat failed')

            secondary_node = MagicMock()

            mock_node_cls.side_effect = [primary_node, secondary_node]

            with self.assertRaises(ExacloudRuntimeError):
                _nc.mConfigurePasswordLessDomU('opc')

            self.assertEqual(mock_node_cls.call_count, 1)
            primary_node.mDisconnect.assert_called()
            mock_log.assert_called()

    @patch('exabox.ovm.cluvmrecoveryutils.clubonding.configure_bonding_if_enabled')
    @patch('exabox.ovm.cluvmrecoveryutils.clubonding.is_static_monitoring_bridge_supported', return_value=False)
    def test_mExecutePostVMStep_configures_bridge_when_not_supported(self, mock_supported, mock_configure):
        # Auto-generated test for mExecutePostVMStep
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        payload = {'bond': 'payload'}
        _nc.mExecutePostVMStep('dom0-host', 'domu-host', payload)

        mock_supported.assert_called_once_with(cluctrl, payload=payload)
        mock_configure.assert_called_once_with(cluctrl, payload=payload, configure_bridge=True, configure_monitor=True)

    @patch('exabox.ovm.cluvmrecoveryutils.clubonding.configure_bonding_if_enabled')
    @patch('exabox.ovm.cluvmrecoveryutils.clubonding.is_static_monitoring_bridge_supported', return_value=True)
    def test_mExecutePostVMStep_skips_bridge_when_supported(self, mock_supported, mock_configure):
        # Auto-generated test for mExecutePostVMStep
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        payload = {'bond': 'payload'}
        _nc.mExecutePostVMStep('dom0-host', 'domu-host', payload)

        mock_supported.assert_called_once_with(cluctrl, payload=payload)
        mock_configure.assert_called_once_with(cluctrl, payload=payload, configure_bridge=False, configure_monitor=True)

    def test_mPatchCellConfig_updates_interface_values(self):
        # Auto-generated test for mPatchCellConfig
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        sample_xml = """<?xml version='1.0' standalone='yes'?>\n<Cell>\n  <Interfaces>\n    <Name>eth0</Name>\n    <IP_address>10.0.0.1</IP_address>\n    <Netmask>255.255.255.0</Netmask>\n    <Gateway>10.0.0.254</Gateway>\n  </Interfaces>\n  <Interfaces>\n    <Name>eth1</Name>\n    <IP_address>10.0.1.1</IP_address>\n    <Netmask>255.255.255.0</Netmask>\n    <Gateway>10.0.1.254</Gateway>\n  </Interfaces>\n</Cell>\n"""

        node = MagicMock()
        node.mReadFile.return_value = sample_xml

        patched = _nc.mPatchCellConfig(node, '192.168.0.10', '255.255.255.128', '192.168.0.1', 'eth1', '/opt/cell.conf')

        decoded = patched.decode('utf-8') if isinstance(patched, bytes) else patched
        self.assertIn('<IP_address>192.168.0.10</IP_address>', decoded)
        self.assertIn('<Netmask>255.255.255.128</Netmask>', decoded)
        self.assertIn('<Gateway>192.168.0.1</Gateway>', decoded)
        self.assertTrue(decoded.startswith("<?xml version='1.0' standalone='yes'?>"))

    def test_mGetAdminIpAddr_returns_configured_value(self):
        # Auto-generated test for mGetAdminIpAddr
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        _nc._NodeRecovery__adminNetwork['IPADDR'] = '10.10.10.10'
        self.assertEqual('10.10.10.10', _nc.mGetAdminIpAddr())

    def test_mGetAdminNetMask_returns_configured_value(self):
        # Auto-generated test for mGetAdminNetMask
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        _nc._NodeRecovery__adminNetwork['NETMASK'] = '255.255.255.0'
        self.assertEqual('255.255.255.0', _nc.mGetAdminNetMask())

    def test_mGetAdminGateway_returns_configured_value(self):
        # Auto-generated test for mGetAdminGateway
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        _nc._NodeRecovery__adminNetwork['GATEWAY'] = '10.10.10.1'
        self.assertEqual('10.10.10.1', _nc.mGetAdminGateway())

    def test_mGetAdminNetwork_returns_configured_value(self):
        # Auto-generated test for mGetAdminNetwork
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        _nc._NodeRecovery__adminNetwork['NETWORK'] = '10.10.10.0'
        self.assertEqual('10.10.10.0', _nc.mGetAdminNetwork())

    def test_mGetAdminBroadcast_returns_configured_value(self):
        # Auto-generated test for mGetAdminBroadcast
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        _nc._NodeRecovery__adminNetwork['BROADCAST'] = '10.10.10.255'
        self.assertEqual('10.10.10.255', _nc.mGetAdminBroadcast())

    def test_mCopyPubKey_copies_file_when_directory_exists(self):
        # Auto-generated test for mCopyPubKey
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, _options)

        with patch('exabox.ovm.cluvmrecoveryutils.get_gcontext') as mock_ctx, \
             patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode') as mock_node_cls, \
             patch('exabox.ovm.cluvmrecoveryutils.ebLogError') as mock_log_error:

            mock_ctx.return_value = MagicMock()
            node = MagicMock()
            node.mFileExists.return_value = True
            mock_node_cls.return_value = node

            node_recovery.mCopyPubKey('dom0-host', '/tmp/local.pub', '/remote/path/key.pub')

        node.mConnect.assert_called_once_with(aHost='dom0-host')
        node.mCopyFile.assert_called_once_with('/tmp/local.pub', '/remote/path/key.pub')
        node.mExecuteCmdLog.assert_called_once_with('/usr/bin/chmod 600 /remote/path/key.pub')
        node.mDisconnect.assert_called_once()
        mock_log_error.assert_not_called()

    def test_mCopyPubKey_logs_error_when_directory_missing(self):
        # Auto-generated test for mCopyPubKey
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, _options)

        with patch('exabox.ovm.cluvmrecoveryutils.get_gcontext') as mock_ctx, \
             patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode') as mock_node_cls, \
             patch('exabox.ovm.cluvmrecoveryutils.ebLogError') as mock_log_error:

            mock_ctx.return_value = MagicMock()
            node = MagicMock()
            node.mFileExists.return_value = False
            mock_node_cls.return_value = node

            node_recovery.mCopyPubKey('dom0-host', '/tmp/local.pub', '/remote/path/key.pub')

        node.mConnect.assert_called_once_with(aHost='dom0-host')
        node.mCopyFile.assert_not_called()
        node.mExecuteCmdLog.assert_not_called()
        node.mDisconnect.assert_called_once()
        mock_log_error.assert_called_once_with('*** Failed to copy /tmp/local.pub to dom0:dom0-host  /remote/path directory not exists')

    def test_mCopyPubKey_handles_exception_and_logs_error(self):
        # Auto-generated test for mCopyPubKey
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, _options)

        with patch('exabox.ovm.cluvmrecoveryutils.get_gcontext') as mock_ctx, \
             patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode') as mock_node_cls, \
             patch('exabox.ovm.cluvmrecoveryutils.ebLogError') as mock_log_error:

            mock_ctx.return_value = MagicMock()
            node = MagicMock()
            node.mConnect.side_effect = RuntimeError('connect failed')
            mock_node_cls.return_value = node

            node_recovery.mCopyPubKey('dom0-host', '/tmp/local.pub', '/remote/path/key.pub')

        node.mConnect.assert_called_once_with(aHost='dom0-host')
        node.mDisconnect.assert_called_once()
        self.assertIn('connect failed', mock_log_error.call_args[0][0])
        self.assertIn('dom0-host', mock_log_error.call_args[0][0])

    def test_mGetRoceInterfaces_returns_mac_mapping(self):
        # Auto-generated test for mGetRoceInterfaces
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, _options)

        node = MagicMock()
        interface_xml = """
        <domain>
            <devices>
                <interface type=\"network\">
                    <mac address=\"52:54:00:11:22:33\" />
                    <address type=\"pci\" domain=\"0x0000\" bus=\"0x04\" slot=\"0x00\" function=\"0x01\" />
                </interface>
                <interface type=\"bridge\">
                    <mac address=\"52:54:00:aa:bb:cc\" />
                </interface>
            </devices>
        </domain>
        """
        node.mReadFile.return_value = interface_xml

        result = node_recovery.mGetRoceInterfaces(node, '/etc/libvirt/qemu/domu-host.xml')

        self.assertEqual(result, {'52:54:00:11:22:33': '0000:ff:00.01'})
        node.mReadFile.assert_called_once_with('/etc/libvirt/qemu/domu-host.xml')

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    def test_mGetVFConfig_builds_interconnect_mapping(self, mock_log_info):
        # Auto-generated test for mGetVFConfig
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, _options)

        node = MagicMock()
        qinq_xml = """
        <root>
            <interface>
                <mac>52:54:00:11:22:33</mac>
                <guest_interface>clre0</guest_interface>
            </interface>
            <interface>
                <mac>52:54:00:aa:bb:cc</mac>
                <guest_interface>stre0</guest_interface>
            </interface>
        </root>
        """
        node.mReadFile.return_value = qinq_xml

        rocelist = {'52:54:00:11:22:33': '0000:ff:00.01'}

        result = node_recovery.mGetVFConfig(node, '/EXAVMIMAGES/GuestImages/domu-host/qinq.xml', rocelist)

        self.assertEqual(result, {'clre0': '0000:ff:00.01'})
        mock_log_info.assert_called_once_with('UDEV ADDRESS:0000:ff:00.01, MAC:52:54:00:11:22:33 INTERFACE:clre0')

    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mGetInterConnectVifs_invokes_roce_and_vf_helpers(self, mock_connect_to_host, mock_get_ctx):
        # Auto-generated test for mGetInterConnectVifs
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, _options)

        mock_get_ctx.return_value = MagicMock()

        node_manager = MagicMock()
        node = MagicMock()
        node_manager.__enter__.return_value = node
        node_manager.__exit__.return_value = False
        mock_connect_to_host.return_value = node_manager

        with patch.object(node_recovery, 'mGetRoceInterfaces', return_value={'52:54:00:11:22:33': '0000:ff:00.01'}) as mock_roce, \
             patch.object(node_recovery, 'mGetVFConfig', return_value={'clre0': '0000:ff:00.01'}) as mock_vf:

            result = node_recovery.mGetInterConnectVifs('dom0-host', 'domu-host')

        self.assertEqual(result, {'clre0': '0000:ff:00.01'})
        mock_connect_to_host.assert_called_once_with('dom0-host', mock_get_ctx.return_value, username='root')
        mock_roce.assert_called_once_with(node, '/etc/libvirt/qemu/domu-host.xml')
        mock_vf.assert_called_once_with(node, '/EXAVMIMAGES/GuestImages/domu-host/qinq.xml', {'52:54:00:11:22:33': '0000:ff:00.01'})

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mGetInterConnectVifs_returns_empty_when_fetch_fails(self, mock_connect_to_host, mock_get_ctx, mock_log_error):
        # Auto-generated test for mGetInterConnectVifs
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, _options)

        mock_get_ctx.return_value = MagicMock()
        mock_connect_to_host.side_effect = RuntimeError('connection failed')

        result = node_recovery.mGetInterConnectVifs('dom0-host', 'domu-host')

        self.assertEqual(result, {})
        mock_log_error.assert_called_once_with('*** Failed to fetch interconnect vifs for VM:domu-host on dom0:dom0-host')

    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mUpdatePersistentRules_updates_file_and_backup(self, mock_connect_to_host, mock_get_ctx):
        # Auto-generated test for mUpdatePersistentRules
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, _options)

        mock_get_ctx.return_value = MagicMock()

        node_manager = MagicMock()
        node = MagicMock()
        node_manager.__enter__.return_value = node
        node_manager.__exit__.return_value = False
        mock_connect_to_host.return_value = node_manager

        node.mFileExists.side_effect = [False, True, True]

        pci_stdout = MagicMock()
        pci_stdout.readlines.return_value = ['PCI_SLOT_NAME=0000:04:00.1\n']
        grep_stdout = MagicMock()
        grep_stdout.read.return_value = "SUBSYSTEM==\"net\", KERNELS==\"0000:ff:00.01\""
        sed_stdout = MagicMock()
        sed_stdout.read.return_value = 'updated rule'

        node.mExecuteCmd.side_effect = [
            (0, pci_stdout, None),
            (0, grep_stdout, None),
            (0, sed_stdout, None),
        ]

        node_recovery.mUpdatePersistentRules('domu-host', {'clre0': '0000:ff:00.01'})

        node.mExecuteCmdLog.assert_has_calls([
            call('/bin/cp -p /etc/udev/rules.d/70-persistent-net.rules /etc/udev/rules.d/70-persistent-net.rules_bk'),
            call("/bin/sed -i '/clre0/d' /etc/udev/rules.d/70-persistent-net.rules_bk"),
            call("/bin/sed -i '/clre1/d' /etc/udev/rules.d/70-persistent-net.rules_bk"),
            call("/bin/sed -i '/stre0/d' /etc/udev/rules.d/70-persistent-net.rules_bk"),
            call("/bin/sed -i '/stre1/d' /etc/udev/rules.d/70-persistent-net.rules_bk"),
        ], any_order=False)
        node.mWriteFile.assert_called_once_with('/etc/udev/rules.d/70-persistent-net.rules_bk', 'updated rule', aAppend=True)
        self.assertEqual(
            node.mExecuteCmdLog.call_args_list[-1],
            call('/bin/mv /etc/udev/rules.d/70-persistent-net.rules_bk /etc/udev/rules.d/70-persistent-net.rules'),
        )

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    def test_mUpdatePersistentRules_logs_error_when_pci_slot_missing(self, mock_connect_to_host, mock_get_ctx, mock_log_error):
        # Auto-generated test for mUpdatePersistentRules
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, _options)

        mock_get_ctx.return_value = MagicMock()

        node_manager = MagicMock()
        node = MagicMock()
        node_manager.__enter__.return_value = node
        node_manager.__exit__.return_value = False
        mock_connect_to_host.return_value = node_manager

        node.mFileExists.return_value = True
        empty_stdout = MagicMock()
        empty_stdout.readlines.return_value = []
        node.mExecuteCmd.return_value = (0, empty_stdout, None)

        result = node_recovery.mUpdatePersistentRules('domu-host', {'clre0': '0000:ff:00.01'})

        self.assertIsNone(result)
        mock_log_error.assert_called_once_with('*** Failed to get PCI_SLOT_NAME for clre0 for VM:domu-host')

    def test_mFetchNetworkInfo_returns_payload_with_ipv6_fallbacks(self):
        # Auto-generated test for mFetchNetworkInfo
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        mock_machine_config = MagicMock()
        mock_machine_config.mGetMacNetworks.return_value = ['client_net', 'backup_net', 'admin_net']
        mock_machine_config.mGetMacHostName.return_value = 'domu-host'

        mock_network_client = MagicMock()
        mock_network_client.mGetNetHostName.return_value = 'client-host.'
        mock_network_client.mGetNetDomainName.return_value = 'domain'
        mock_network_client.mGetNetGateWay.return_value = 'fe80::1'
        mock_network_client.mGetNetMacAddr.return_value = 'aa:bb:cc:dd:ee:ff'
        mock_network_client.mGetNetMask.return_value = 'ffff:ffff:ffff'
        mock_network_client.mGetNetSlave.return_value = ['eth1']
        mock_network_client.mGetNetVlanId.return_value = '100'
        mock_network_client.mGetNetIpAddr.return_value = 'fe80::2'
        mock_network_client.mGetNetType.return_value = 'client'
        mock_network_client.mGetNetNatDomainName.return_value = 'nat.dom'
        mock_network_client.mGetNetNatAddr.return_value = 'fe80::3'
        mock_network_client.mGetNetNatMask.return_value = 'ffff:ffff:ffff'
        mock_network_client.mGetNetNatHostName.return_value = 'oracle'

        mock_network_backup = MagicMock()
        mock_network_backup.mGetNetHostName.return_value = 'backup-host.'
        mock_network_backup.mGetNetDomainName.return_value = 'domain'
        mock_network_backup.mGetNetGateWay.return_value = 'fe80::4'
        mock_network_backup.mGetNetMacAddr.return_value = '11:22:33:44:55:66'
        mock_network_backup.mGetNetMask.return_value = 'ffff:ffff:ffff'
        mock_network_backup.mGetNetSlave.return_value = ['eth2']
        mock_network_backup.mGetNetVlanId.return_value = '200'
        mock_network_backup.mGetNetIpAddr.return_value = 'fe80::5'
        mock_network_backup.mGetNetType.return_value = 'backup'

        mock_network_admin = MagicMock()
        mock_network_admin.mGetNetHostName.return_value = 'admin-host.'
        mock_network_admin.mGetNetDomainName.return_value = 'domain'
        mock_network_admin.mGetNetGateWay.return_value = 'fe80::7'
        mock_network_admin.mGetNetMacAddr.return_value = '77:88:99:aa:bb:cc'
        mock_network_admin.mGetNetMask.return_value = 'ffff:ffff:ffff'
        mock_network_admin.mGetNetSlave.return_value = ['eth3']
        mock_network_admin.mGetNetVlanId.return_value = '300'
        mock_network_admin.mGetNetIpAddr.return_value = 'fe80::8'
        mock_network_admin.mGetNetType.return_value = 'admin'
        mock_network_admin.mGetNetNatDomainName.return_value = 'admin.dom'
        mock_network_admin.mGetNetNatAddr.return_value = 'fe80::9'
        mock_network_admin.mGetNetNatMask.return_value = 'ffff:ffff:ffff'
        mock_network_admin.mGetNetNatHostName.return_value = 'admin-oracle'

        mock_vip_entry = MagicMock()
        mock_vip_entry.mGetCVIPMachines.return_value = ['domu-host']
        mock_vip_entry.mGetCVIPDomainName.return_value = '.vipdomain'
        mock_vip_entry.mGetCVIPAddr.return_value = 'fe80::6'
        mock_vip_entry.mGetCVIPName.return_value = 'vipname'

        mock_cluster = MagicMock()
        mock_cluster.mGetCluVips.return_value = {'vip1': mock_vip_entry}

        with patch.object(cluctrl.mGetMachines(), 'mGetMachineConfig', return_value=mock_machine_config), \
             patch.object(cluctrl.mGetNetworks(), 'mGetNetworkConfig', side_effect=[mock_network_client, mock_network_backup, mock_network_admin]), \
             patch.object(cluctrl.mGetClusters(), 'mGetCluster', return_value=mock_cluster), \
             patch('exabox.ovm.cluvmrecoveryutils.NetworkUtils') as mock_nw_utils:
            mock_nw = MagicMock()
            mock_nw.mIsIPv6.return_value = True
            mock_nw_utils.return_value = mock_nw

            payload = _nc.mFetchNetworkInfo('dom0-host', 'domu-host', 'bonding')

        self.assertEqual(payload['vip']['fqdn'], 'vipname.vipdomain')
        self.assertEqual(payload['vip']['ip'], 'fe80::6')
        self.assertEqual(payload['client']['ip'], 'fe80::2')
        self.assertEqual(payload['client']['gateway'], 'fe80::1')
        self.assertEqual(payload['backup']['ip'], 'fe80::5')
        self.assertEqual(payload['backup']['gateway'], 'fe80::4')
        self.assertEqual(payload['admin']['ipv6'], 'fe80::8')
        self.assertEqual(payload['admin']['v6gateway'], 'fe80::7')
        self.assertEqual(payload['admin']['v6netmask'], 'ffff:ffff:ffff')
        self.assertEqual(payload['admin']['natdomain'], 'admin.dom')
        self.assertEqual(payload['admin']['natip'], 'fe80::9')
        self.assertEqual(payload['admin']['natnetmask'], 'ffff:ffff:ffff')

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogTrace')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogWarn')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mFetchAdminNWDetails_populates_admin_network(self, mock_get_ctx, mock_connect, mock_log_error, mock_log_warn, mock_log_trace):
        # Auto-generated test for mFetchAdminNWDetails
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        mock_get_ctx.return_value = MagicMock()

        responses = iter([
            ['IPADDR=10.0.0.5\n'],
            ['NETMASK=255.255.255.0\n'],
            ['GATEWAY=10.0.0.1\n'],
            ['NETWORK=10.0.0.0\n'],
            ['BROADCAST=10.0.0.255\n']
        ])

        def _side_effect(*args, **kwargs):
            stdout = MagicMock()
            stdout.readlines.return_value = next(responses)
            return (None, stdout, None)

        node = MagicMock()
        node.mExecuteCmd.side_effect = _side_effect

        ctx_mgr = MagicMock()
        ctx_mgr.__enter__.return_value = node
        ctx_mgr.__exit__.return_value = False
        mock_connect.return_value = ctx_mgr

        _nc.mFetchAdminNWDetails('dom0-host', 'domu-host')

        mock_connect.assert_called_once_with('domu-host', mock_get_ctx.return_value, username='root')
        self.assertEqual(_nc.mGetAdminIpAddr(), '10.0.0.5')
        self.assertEqual(_nc.mGetAdminNetMask(), '255.255.255.0')
        self.assertEqual(_nc.mGetAdminGateway(), '10.0.0.1')
        self.assertEqual(_nc.mGetAdminNetwork(), '10.0.0.0')
        self.assertEqual(_nc.mGetAdminBroadcast(), '10.0.0.255')
        mock_log_warn.assert_not_called()
        mock_log_error.assert_not_called()
        self.assertTrue(ctx_mgr.__exit__.called)

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogWarn')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mFetchAdminNWDetails_handles_missing_gateway(self, mock_get_ctx, mock_connect, mock_log_warn, mock_log_error):
        # Auto-generated test for mFetchAdminNWDetails
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        mock_get_ctx.return_value = MagicMock()

        responses = iter([
            ['IPADDR=10.0.0.5\n'],
            ['NETMASK=255.255.255.0\n'],
            [],
            ['NETWORK=10.0.0.0\n'],
            ['BROADCAST=10.0.0.255\n']
        ])

        def _side_effect(*args, **kwargs):
            stdout = MagicMock()
            stdout.readlines.return_value = next(responses)
            return (None, stdout, None)

        node = MagicMock()
        node.mExecuteCmd.side_effect = _side_effect

        ctx_mgr = MagicMock()
        ctx_mgr.__enter__.return_value = node
        ctx_mgr.__exit__.return_value = False
        mock_connect.return_value = ctx_mgr

        _nc.mFetchAdminNWDetails('dom0-host', 'domu-host')

        self.assertEqual(_nc.mGetAdminIpAddr(), '10.0.0.5')
        self.assertEqual(_nc.mGetAdminNetMask(), '255.255.255.0')
        self.assertEqual(_nc.mGetAdminGateway(), '')
        self.assertEqual(_nc.mGetAdminNetwork(), '10.0.0.0')
        self.assertEqual(_nc.mGetAdminBroadcast(), '10.0.0.255')
        mock_log_warn.assert_called_once_with('*** DomU:domu-host:: Gateway not configured in ifcfg-eth0')
        mock_log_error.assert_not_called()

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogError')
    @patch('exabox.ovm.cluvmrecoveryutils.connect_to_host')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mFetchAdminNWDetails_logs_error_when_missing_ip(self, mock_get_ctx, mock_connect, mock_log_error):
        # Auto-generated test for mFetchAdminNWDetails
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        mock_get_ctx.return_value = MagicMock()

        def _side_effect(*args, **kwargs):
            stdout = MagicMock()
            stdout.readlines.return_value = []
            return (None, stdout, None)

        node = MagicMock()
        node.mExecuteCmd.side_effect = _side_effect

        ctx_mgr = MagicMock()
        ctx_mgr.__enter__.return_value = node
        ctx_mgr.__exit__.return_value = False
        mock_connect.return_value = ctx_mgr

        _nc.mFetchAdminNWDetails('dom0-host', 'domu-host')

        mock_log_error.assert_any_call('*** DomU:domu-host:: IPADDR not configured in ifcfg-eth0')
        mock_log_error.assert_any_call('*** Failed to get admin network for VM:domu-host')
        self.assertEqual(_nc.mGetAdminIpAddr(), '')
        self.assertEqual(_nc.mGetAdminNetMask(), '')
        self.assertEqual(_nc.mGetAdminGateway(), '')
        self.assertEqual(_nc.mGetAdminNetwork(), '')
        self.assertEqual(_nc.mGetAdminBroadcast(), '')
        self.assertTrue(ctx_mgr.__exit__.called)

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogWarn')
    @patch('exabox.ovm.cluvmrecoveryutils.time.sleep')
    @patch('exabox.ovm.cluvmrecoveryutils.time.time')
    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    def test_mCheckSshd_warns_before_success(self, mock_get_ctx, mock_node_cls, mock_time_time, mock_time_sleep, mock_log_warn, mock_log_info):
        # Auto-generated test for mCheckSshd
        _options = self.mGetClubox().mGetArgsOptions()
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        ctx = MagicMock()
        ctx.mCheckRegEntry.return_value = False
        mock_get_ctx.return_value = ctx

        mock_time_time.side_effect = [0, 5, 11]
        mock_time_sleep.side_effect = lambda *_args, **_kwargs: None

        node = MagicMock()
        node.mCheckPortSSH.side_effect = [False, False, True]
        mock_node_cls.return_value = node

        result = _nc.mCheckSshd('domu-host', 30, 2)

        self.assertTrue(result)
        mock_log_warn.assert_called_once()
        mock_log_info.assert_called_once_with('SSH port is alive on domU')
        node.mConnect.assert_called_once()
        node.mDisconnect.assert_called_once()

    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    def test_mEnableSSHConnectivity_stops_after_root_failure(self, mock_node_cls, mock_get_ctx):
        # Auto-generated test for mEnableSSHConnectivity
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        mock_get_ctx.return_value = MagicMock()

        node = MagicMock()
        node.mFileExists.return_value = True
        mock_node_cls.return_value = node

        with patch.object(_nc, 'mUpdateSSHKeys', side_effect=[RuntimeError('root failure')]) as mock_update_keys, \
             patch.object(_nc, 'mUpdateNetworkConfig') as mock_update_network:
            with self.assertRaises(RuntimeError):
                _nc.mEnableSSHConnectivity('dom0.example.com', 'domu.example.com')

        mock_update_keys.assert_called_once_with('dom0.example.com', 'domu.example.com', '/mnt/vmsys1_domu', 'root')
        mock_update_network.assert_not_called()
        node.mConnect.assert_called_once_with(aHost='dom0.example.com')
        node.mDisconnect.assert_called_once()
        first_call = node.mExecuteCmdLog.call_args_list[0][0][0]
        self.assertIn('mount domu.example.com -ml LVDbSys1', first_call)

    @patch('exabox.ovm.cluvmrecoveryutils.get_gcontext')
    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    def test_mEnableSSHConnectivity_updates_all_users(self, mock_node_cls, mock_get_ctx):
        # Auto-generated test for mEnableSSHConnectivity
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        _nc = NodeRecovery(cluctrl, _options)

        mock_get_ctx.return_value = MagicMock()

        node = MagicMock()
        node.mFileExists.return_value = True
        mock_node_cls.return_value = node

        with patch.object(_nc, 'mUpdateSSHKeys') as mock_update_keys, \
             patch.object(_nc, 'mUpdateNetworkConfig') as mock_update_network:
            _nc.mEnableSSHConnectivity('dom0.example.com', 'domu.example.com')

        expected_calls = [
            call('/usr/bin/python3 /opt/exacloud/bin/dmgr.py mount domu.example.com -ml LVDbSys1 -mp /mnt/vmsys1_domu'),
            call('/usr/bin/python3 /opt/exacloud/bin/dmgr.py umount domu.example.com -mp /mnt/vmsys1_domu'),
            call('/usr/bin/python3 /opt/exacloud/bin/dmgr.py mount domu.example.com -ml LVDbHome -mp /mnt/vmhome_domu'),
            call('/usr/bin/python3 /opt/exacloud/bin/dmgr.py umount domu.example.com -mp /mnt/vmhome_domu'),
        ]
        node.mExecuteCmdLog.assert_has_calls(expected_calls)
        node.mConnect.assert_called_once_with(aHost='dom0.example.com')
        node.mDisconnect.assert_called_once()

        mock_update_network.assert_called_once_with('dom0.example.com', 'domu.example.com', '/mnt/vmsys1_domu', 'root')
        self.assertEqual(
            mock_update_keys.call_args_list,
            [
                call('dom0.example.com', 'domu.example.com', '/mnt/vmsys1_domu', 'root'),
                call('dom0.example.com', 'domu.example.com', '/mnt/vmhome_domu', 'oracle'),
                call('dom0.example.com', 'domu.example.com', '/mnt/vmhome_domu', 'grid'),
                call('dom0.example.com', 'domu.example.com', '/mnt/vmhome_domu', 'opc'),
            ],
        )

    def test_admin_getters_return_defaults(self):
        # Auto-generated test for mGetAdminIpAddr
        # Auto-generated test for mGetAdminNetMask
        # Auto-generated test for mGetAdminGateway
        # Auto-generated test for mGetAdminNetwork
        # Auto-generated test for mGetAdminBroadcast
        options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, options)

        self.assertEqual(node_recovery.mGetAdminIpAddr(), '')
        self.assertEqual(node_recovery.mGetAdminNetMask(), '')
        self.assertEqual(node_recovery.mGetAdminGateway(), '')
        self.assertEqual(node_recovery.mGetAdminNetwork(), '')
        self.assertEqual(node_recovery.mGetAdminBroadcast(), '')

    def test_admin_getters_reflect_updates(self):
        # Auto-generated test for mGetAdminIpAddr
        # Auto-generated test for mGetAdminNetMask
        # Auto-generated test for mGetAdminGateway
        # Auto-generated test for mGetAdminNetwork
        # Auto-generated test for mGetAdminBroadcast
        options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, options)

        values = {
            "IPADDR": "10.10.10.5",
            "NETMASK": "255.255.255.0",
            "GATEWAY": "10.10.10.1",
            "NETWORK": "10.10.10.0",
            "BROADCAST": "10.10.10.255",
        }
        node_recovery._NodeRecovery__adminNetwork = values

        self.assertEqual(node_recovery.mGetAdminIpAddr(), '10.10.10.5')
        self.assertEqual(node_recovery.mGetAdminNetMask(), '255.255.255.0')
        self.assertEqual(node_recovery.mGetAdminGateway(), '10.10.10.1')
        self.assertEqual(node_recovery.mGetAdminNetwork(), '10.10.10.0')
        self.assertEqual(node_recovery.mGetAdminBroadcast(), '10.10.10.255')

    def test_source_getters_handle_defaults(self):
        # Auto-generated test for mGetSrcDom0
        # Auto-generated test for mGetSrcDomU
        options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, options)

        self.assertEqual(node_recovery.mGetSrcDom0(), '')
        self.assertEqual(node_recovery.mGetSrcDomU(), '')

    def test_source_getters_reflect_internal_state(self):
        # Auto-generated test for mGetSrcDom0
        # Auto-generated test for mGetSrcDomU
        options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, options)

        node_recovery._NodeRecovery__srcdom0 = 'dom0-active'
        node_recovery._NodeRecovery__srcdomU = 'domu-active.example.com'

        self.assertEqual(node_recovery.mGetSrcDom0(), 'dom0-active')
        self.assertEqual(node_recovery.mGetSrcDomU(), 'domu-active.example.com')

    @patch('exabox.ovm.cluvmrecoveryutils.ebLogInfo')
    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.NodeRecovery.mGetVIPHost')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogWarn')
    def test_mAddVIP_returns_when_already_started(self, mock_log_warn, mock_get_vip, mock_node_cls, mock_log_info):
        # Auto-generated test for mAddVIP
        options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, options)

        mock_get_vip.return_value = {
            'vip_host': 'vipname.example.com',
            'ip': '198.51.100.10',
        }

        node = MagicMock()
        node.mGetCmdExitStatus.return_value = 0
        mock_node_cls.return_value = node

        with patch.object(cluctrl, 'mGetOracleBaseDirectories', return_value=('/u01/app/19.0.0', None, None)):
            node_recovery.mAddVIP('domu.example.com')

        node.mExecuteCmdLog.assert_called_once_with('/u01/app/19.0.0/bin/srvctl config vip -node domu')
        node.mExecuteCmd.assert_not_called()
        node.mDisconnect.assert_called_once()
        mock_log_info.assert_called_once_with('vipname.example.com is already started on nodes: domu')
        mock_log_warn.assert_not_called()

    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.NodeRecovery.mGetVIPHost')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogWarn')
    def test_mAddVIP_adds_dual_stack_addresses(self, mock_log_warn, mock_get_vip, mock_node_cls):
        # Auto-generated test for mAddVIP
        options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, options)

        mock_get_vip.return_value = {
            'vip_host': 'vipname.example.com',
            'ip': '198.51.100.10',
            'ipv6': '2001:db8::10',
        }

        stdout = MagicMock()
        stdout.readlines.return_value = [
            'Network 1 exists\n',
            'Subnet IPv4: 198.51.100.0/255.255.255.0/bondeth0, static (inactive)\n',
            'Subnet IPv6: 2001:0db8:418:1ea4:0:0:0:0/64/bondeth0, static\n',
        ]

        node = MagicMock()
        node.mGetCmdExitStatus.return_value = 1
        node.mExecuteCmd.return_value = (None, stdout, None)
        mock_node_cls.return_value = node

        with patch.object(cluctrl, 'mGetOracleBaseDirectories', return_value=('/u01/app/19.0.0', None, None)):
            node_recovery.mAddVIP('domu.example.com')

        node.mExecuteCmdLog.assert_has_calls([
            call('/u01/app/19.0.0/bin/srvctl config vip -node domu'),
            call('/u01/app/19.0.0/bin/srvctl add vip -node domu -netnum 1 -address 198.51.100.10/255.255.255.0/bondeth0'),
            call('/u01/app/19.0.0/bin/srvctl modify vip -node domu -address 2001:db8::10/64/bondeth0'),
            call('/u01/app/19.0.0/bin/srvctl start vip -node domu'),
            call('/u01/app/19.0.0/bin/srvctl config vip -node domu'),
        ])
        node.mDisconnect.assert_called_once()
        mock_log_warn.assert_not_called()

    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.NodeRecovery.mGetVIPHost')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogWarn')
    def test_mAddVIP_handles_single_stack_variants(self, mock_log_warn, mock_get_vip, mock_node_cls):
        # Auto-generated test for mAddVIP
        options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, options)

        stdout = MagicMock()
        stdout.readlines.return_value = [
            'Network 2 exists\n',
            'Subnet IPv4: 203.0.113.0/255.255.255.0/bondeth1, static\n',
            'Subnet IPv6: 2001:db8:ffff::/64/bondeth1, static\n',
        ]

        node = MagicMock()
        node.mGetCmdExitStatus.return_value = 1
        node.mExecuteCmd.return_value = (None, stdout, None)
        mock_node_cls.return_value = node

        with patch.object(cluctrl, 'mGetOracleBaseDirectories', return_value=('/u01/app/19.0.0', None, None)):
            # IPv4-only path
            mock_get_vip.return_value = {
                'vip_host': 'vip4.example.com',
                'ip': '203.0.113.10',
                'ipv6': '::',
            }
            node_recovery.mAddVIP('domu4.example.com')

        ipv4_calls = [
            call('/u01/app/19.0.0/bin/srvctl config vip -node domu4'),
            call('/u01/app/19.0.0/bin/srvctl add vip -node domu4 -netnum 2 -address vip4.example.com/255.255.255.0/bondeth1'),
            call('/u01/app/19.0.0/bin/srvctl start vip -node domu4'),
            call('/u01/app/19.0.0/bin/srvctl config vip -node domu4'),
        ]
        node.mExecuteCmdLog.assert_has_calls(ipv4_calls)

        node.mExecuteCmdLog.reset_mock()
        node.mGetCmdExitStatus.return_value = 1

        with patch.object(cluctrl, 'mGetOracleBaseDirectories', return_value=('/u01/app/19.0.0', None, None)):
            # IPv6-only path
            mock_get_vip.return_value = {
                'vip_host': 'vip6.example.com',
                'ip': '0.0.0.0',
                'ipv6': '2001:db8:ffff::25',
            }
            node_recovery.mAddVIP('domu6.example.com')

        ipv6_calls = [
            call('/u01/app/19.0.0/bin/srvctl config vip -node domu6'),
            call('/u01/app/19.0.0/bin/srvctl add vip -node domu6 -netnum 2 -address vip6.example.com/64/bondeth1'),
            call('/u01/app/19.0.0/bin/srvctl start vip -node domu6'),
            call('/u01/app/19.0.0/bin/srvctl config vip -node domu6'),
        ]
        node.mExecuteCmdLog.assert_has_calls(ipv6_calls)
        mock_log_warn.assert_not_called()
        node.mDisconnect.assert_called()

    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.NodeRecovery.mGetVIPHost')
    @patch('exabox.ovm.cluvmrecoveryutils.ebLogWarn')
    def test_mAddVIP_logs_warnings_on_netmask_parse_failure(self, mock_log_warn, mock_get_vip, mock_node_cls):
        # Auto-generated test for mAddVIP
        options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, options)

        mock_get_vip.return_value = {
            'vip_host': 'vipname.example.com',
            'ip': '198.51.100.10',
            'ipv6': '2001:db8::10',
        }

        stdout = MagicMock()
        stdout.readlines.return_value = [
            'Network 3 exists\n',
            'Subnet IPv4: invalid-output\n',
            'Subnet IPv6: invalid-output\n',
        ]

        node = MagicMock()
        node.mGetCmdExitStatus.return_value = 1
        node.mExecuteCmd.return_value = (None, stdout, None)
        mock_node_cls.return_value = node

        with patch.object(cluctrl, 'mGetOracleBaseDirectories', return_value=('/u01/app/19.0.0', None, None)):
            node_recovery.mAddVIP('domu.example.com')

        warn_messages = [call_args[0][0] for call_args in mock_log_warn.call_args_list]
        self.assertTrue(any('Could not get IPv4 netmask' in message for message in warn_messages))
        self.assertTrue(any('Could not get IPv6 netmask' in message for message in warn_messages))

        node.mExecuteCmdLog.assert_has_calls([
            call('/u01/app/19.0.0/bin/srvctl config vip -node domu'),
            call('/u01/app/19.0.0/bin/srvctl add vip -node domu -netnum 3 -address 198.51.100.10/None'),
            call('/u01/app/19.0.0/bin/srvctl modify vip -node domu -address 2001:db8::10/None'),
            call('/u01/app/19.0.0/bin/srvctl start vip -node domu'),
            call('/u01/app/19.0.0/bin/srvctl config vip -node domu'),
        ])
        node.mDisconnect.assert_called_once()

    @patch('exabox.ovm.cluvmrecoveryutils.exaBoxNode')
    @patch('exabox.ovm.cluvmrecoveryutils.NodeRecovery.mGetVIPHost')
    def test_mAddVIP_raises_when_add_command_fails(self, mock_get_vip, mock_node_cls):
        # Auto-generated test for mAddVIP
        options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, options)

        mock_get_vip.return_value = {
            'vip_host': 'vipname.example.com',
            'ip': '198.51.100.10',
        }

        stdout = MagicMock()
        stdout.readlines.return_value = [
            'Network 4 exists\n',
            'Subnet IPv4: 198.51.100.0/255.255.255.0/bondeth0\n',
        ]

        node = MagicMock()
        node.mGetCmdExitStatus.return_value = 1
        node.mExecuteCmd.return_value = (None, stdout, None)
        node.mExecuteCmdLog.side_effect = [
            None,
            ExacloudRuntimeError(0x0001, 0xA, 'srvctl add failed'),
        ]
        mock_node_cls.return_value = node

        with patch.object(cluctrl, 'mGetOracleBaseDirectories', return_value=('/u01/app/19.0.0', None, None)):
            with self.assertRaises(ExacloudRuntimeError):
                node_recovery.mAddVIP('domu.example.com')

        node.mExecuteCmdLog.assert_called_with('/u01/app/19.0.0/bin/srvctl add vip -node domu -netnum 4 -address vipname.example.com/255.255.255.0/bondeth0')
        node.mDisconnect.assert_called_once()

    def test_mGetVIPHost_builds_ipv4_and_ipv6_mapping(self):
        # Auto-generated test for mGetVIPHost
        options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, options)

        ipv4_vip = MagicMock()
        ipv4_vip.mGetCVIPMachines.return_value = ['vip-1']
        ipv4_vip.mGetCVIPName.return_value = 'vipname4'
        ipv4_vip.mGetCVIPDomainName.return_value = 'example.com'
        ipv4_vip.mGetCVIPAddr.return_value = '198.51.100.15'

        ipv6_vip = MagicMock()
        ipv6_vip.mGetCVIPMachines.return_value = ['vip-1']
        ipv6_vip.mGetCVIPName.return_value = 'vipname6'
        ipv6_vip.mGetCVIPDomainName.return_value = 'example.com'
        ipv6_vip.mGetCVIPAddr.return_value = '2001:db8::2'

        cluster = MagicMock()
        cluster.mGetCluVips.return_value = {
            'vip4': ipv4_vip,
            'vip6': ipv6_vip,
        }

        clusters = MagicMock()
        clusters.mGetCluster.return_value = cluster

        machine_config = MagicMock()
        machine_config.mGetMacHostName.return_value = 'domu.example.com'

        machines = MagicMock()
        machines.mGetMachineConfig.side_effect = lambda vip_id: machine_config

        with patch.object(cluctrl, 'mGetClusters', return_value=clusters), \
             patch.object(cluctrl, 'mGetMachines', return_value=machines):
            result = node_recovery.mGetVIPHost('domu.example.com')

        self.assertEqual(result['vip_host'], 'vipname6.example.com')
        self.assertEqual(result['ip'], '198.51.100.15')
        self.assertEqual(result['ipv6'], '2001:db8::2')

    def test_mGetVIPHost_returns_empty_when_not_found(self):
        # Auto-generated test for mGetVIPHost
        options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        cluctrl = self.mGetClubox()
        node_recovery = NodeRecovery(cluctrl, options)

        clusters = MagicMock()
        cluster = MagicMock()
        cluster.mGetCluVips.return_value = {}
        clusters.mGetCluster.return_value = cluster

        with patch.object(cluctrl, 'mGetClusters', return_value=clusters), \
             patch.object(cluctrl, 'mGetMachines'):  # machines not required when dict empty
            result = node_recovery.mGetVIPHost('domu.example.com')

        self.assertEqual(result, {})


if __name__ == '__main__':
    unittest.main() 
