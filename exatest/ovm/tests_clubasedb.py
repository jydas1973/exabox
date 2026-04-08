#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_clubasedb.py /main/1 2025/12/11 08:28:16 prsshukl Exp $
#
# tests_clubasedb.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_clubasedb.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    12/10/25 - Creation
#
import unittest
from types import SimpleNamespace
from xml.etree.ElementTree import Element
from unittest.mock import MagicMock, patch

from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.clubasedb import exaBoxBaseDB


class TestExaBoxBaseDB(unittest.TestCase):

    def _build_ctrl_for_patchcluster(self):
        ctrl = MagicMock()
        ctrl.mGetCmd.return_value = 'patchcluster'
        ctrl.mIsKVM.return_value = True
        ctrl.IsZdlraProv.return_value = False
        ctrl.mGetSharedEnv.return_value = False
        ctrl.mReturnDom0DomUPair.return_value = [('dom0', 'domu1')]
        ctrl.mIsDebug.return_value = False
        ctrl.mGetTimeZone.return_value = None

        config_root = Element('config')
        config_root.append(Element('configKeys'))
        config_wrapper = MagicMock()
        config_wrapper.mConfigRoot.return_value = config_root
        ctrl.mGetConfig.return_value = config_wrapper

        vm_size_large = MagicMock()
        vm_size_large.mGetVMSizeAttr.side_effect = lambda key: {
            'cpuCount': '4',
            'MemSize': '64GB',
            'DiskSize': '200GB'
        }[key]
        vm_size_large.mSetVMSizeAttr = MagicMock()

        vm_size_medium = MagicMock()
        vm_size_medium.mGetVMSizeAttr.side_effect = lambda key: {
            'cpuCount': '2',
            'MemSize': '32GB',
            'DiskSize': '120GB'
        }[key]
        vm_size_medium.mSetVMSizeAttr = MagicMock()

        vm_size_small = MagicMock()
        vm_size_small.mGetVMSizeAttr.side_effect = lambda key: {
            'cpuCount': '1',
            'MemSize': '16GB',
            'DiskSize': '80GB'
        }[key]
        vm_size_small.mSetVMSizeAttr = MagicMock()

        vm_sizes = MagicMock()
        vm_sizes.mGetVMSize.side_effect = lambda size: {
            'Large': vm_size_large,
            'Medium': vm_size_medium,
            'Small': vm_size_small
        }[size]
        ctrl.mGetVMSizesConfig.return_value = vm_sizes

        dom0_config = MagicMock()
        dom0_config.mGetMacMachines.return_value = ['domu1']

        domu_config = MagicMock()
        domu_config.mSetMacCores = MagicMock()
        domu_config.mSetMacMemory = MagicMock()
        domu_config.mSetMacDisk = MagicMock()
        domu_config.mSetMacTimeZone = MagicMock()
        domu_config.mGetMacTimeZone.return_value = 'UTC'

        machines = MagicMock()
        machines.mGetMachineConfigList.return_value = {'dom0': dom0_config, 'domu1': domu_config}
        machines.mGetMachineConfig.side_effect = lambda name: {'dom0': dom0_config, 'domu1': domu_config}[name]
        ctrl.mGetMachines.return_value = machines

        db_home_used = MagicMock()
        db_home_used.mGetDBHomeId.return_value = 'home1'
        db_home_used.mGetDBHomeMacs.return_value = ['dom0']
        db_home_used.mGetDBHomeConfig_ptr.return_value = object()

        db_home_mgr = MagicMock()
        db_home_mgr.mGetDBHomeConfigs.return_value = [db_home_used]
        db_home_mgr.mRemoveDBHomeConfig = MagicMock()
        ctrl.mGetDBHomes.return_value = db_home_mgr

        db_config_used = MagicMock()
        db_config_used.mGetDBHome.return_value = 'home1'
        db_config_used.mGetDBId.return_value = 'db1'
        db_config_unused = MagicMock()
        db_config_unused.mGetDBHome.return_value = 'home2'
        db_config_unused.mGetDBId.return_value = 'db2'

        db_mgr = MagicMock()
        db_mgr.mGetDBconfigs.return_value = {'db1': db_config_used, 'db2': db_config_unused}
        db_mgr.mRemoveDatabaseConfig = MagicMock()
        ctrl.mGetDatabases.return_value = db_mgr

        ctrl.mSetDbStorage = MagicMock()
        ctrl.mSetRackNameEcra = MagicMock()
        ctrl.mSetVmClusterType = MagicMock()
        ctrl.mSetToolsKey = MagicMock()
        ctrl.mSetToolsKeyPrivate = MagicMock()
        ctrl.mSetOHSize = MagicMock()
        ctrl.mSetAdditionalDisks = MagicMock()
        ctrl.mSetTimeZone = MagicMock()
        ctrl.mGetUiOedaXml.return_value = False

        return ctrl, config_root, vm_size_large, domu_config, db_mgr

    def test_mUpdateOedaPropertiesInterface_sets_network_and_runs_commands(self):
        ctrl = MagicMock()
        ctrl.mGetOedaPath.return_value = '/tmp/oeda'

        base_db = exaBoxBaseDB(ctrl)
        base_db.mUpdateOedaPropertiesInterface()

        ctrl.mSetNetworkDiscovered.assert_called_once_with(
            aAdminNet='vmeth0::eth0', aClientNet='vmbondeth0:eth1,eth2:bondeth0')
        self.assertEqual(ctrl.mExecuteLocal.call_count, 2)

    def test_mPatchClusterDB_updates_sizes_and_removes_configkeys(self):
        ctrl, config_root, vm_size_large, domu_config, db_mgr = self._build_ctrl_for_patchcluster()

        options = SimpleNamespace(
            debug=True,
            jsonconf={
                'rack': {
                    'gb_storage': '500',
                    'ecra_db_rack_name': 'rack-1',
                    'vmclustertype': 'cluster-type',
                    'timezone': 'UTC'
                },
                'exaunitAllocations': {
                    'storageTb': 1,
                    'memoryGb': 64,
                    'cores': 4,
                    'ohomeSizeGb': 50
                },
                'vm': {
                    'size': 'Large',
                    'cores': 4,
                    'gb_memory': 64,
                    'gb_disk': 200,
                    'gb_ohsize': 60,
                    'gb_tmpsize': 10,
                    'gb_logsize': 20
                },
                'tools_ssh': {
                    'ssh_public_key': 'public_key',
                    'ssh_private_key': 'private_key'
                }
            }
        )

        def check_config_option(key, default=None):
            mapping = {
                'core_to_vcpu_ratio': 2,
                'remove_configkeys': 'True',
                'ignore_memory_payload': 'False',
                'force_vm_u01_disksize': '150GB'
            }
            return mapping.get(key, default)

        with patch('exabox.ovm.clubasedb.umaskSensitiveData', side_effect=lambda data: data), \
             patch('exabox.ovm.clubasedb.ebCluCmdCheckOptions', return_value=False), \
             patch.object(ctrl, 'mCheckConfigOption', side_effect=check_config_option):
            base_db = exaBoxBaseDB(ctrl)
            base_db.mPatchClusterDB(options)

        ctrl.mUpdateCelldiskSize.assert_called_once()
        ctrl.mSetDbStorage.assert_any_call('500G')
        ctrl.mSetDbStorage.assert_any_call('1024G')
        ctrl.mSetDbStorage.assert_any_call('500G')
        ctrl.mSetRackNameEcra.assert_called_once_with('rack-1')
        ctrl.mSetVmClusterType.assert_called_once_with('cluster-type')
        ctrl.mSetToolsKey.assert_called_once_with('public_key')
        ctrl.mSetToolsKeyPrivate.assert_called_once_with('private_key')
        self.assertIsNone(config_root.find('configKeys'))
        vm_size_large.mSetVMSizeAttr.assert_any_call('cpuCount', '8')
        vm_size_large.mSetVMSizeAttr.assert_any_call('MemSize', '64GB')
        vm_size_large.mSetVMSizeAttr.assert_any_call('DiskSize', '200GB')
        ctrl.mSetAdditionalDisks.assert_any_call(('/tmp', '10GB'))
        ctrl.mSetAdditionalDisks.assert_any_call(('/var/opt/oracle/logs', '20GB'))
        ctrl.mSetTimeZone.assert_called_once_with('UTC')
        domu_config.mSetMacCores.assert_called_with('8')
        db_mgr.mRemoveDatabaseConfig.assert_called_once_with('db2')
        
    def test_mPatchClusterDB_handles_zdlra_ratio_and_existing_xml_sizes(self):
        ctrl, config_root, vm_size_large, domu_config, db_mgr = self._build_ctrl_for_patchcluster()
        ctrl.IsZdlraProv.return_value = True
        ctrl.mCheckConfigOption.side_effect = None

        def check_config_option(key, default=None):
            mapping = {
                'core_to_vcpu_ratio': 4,
                'zdlra_core_to_vcpu_ratio': 1,
                'remove_configkeys': 'False',
                'ignore_memory_payload': 'True',
                'force_vm_u01_disksize': None
            }
            return mapping.get(key, default)

        vm_size_large.mGetVMSizeAttr.side_effect = lambda key: {
            'cpuCount': '6',
            'MemSize': '48GB',
            'DiskSize': '300GB'
        }[key]

        options = SimpleNamespace(
            debug=False,
            jsonconf={
                'vm': {
                    'size': 'Large',
                    'cores': 2,
                    'gb_disk': 120
                },
                'exaunitAllocations': {
                    'memoryGb': 32
                }
            }
        )

        with patch('exabox.ovm.clubasedb.umaskSensitiveData', side_effect=lambda data: data), \
             patch('exabox.ovm.clubasedb.ebCluCmdCheckOptions', return_value=False), \
             patch.object(ctrl, 'mCheckConfigOption', side_effect=check_config_option):
            base_db = exaBoxBaseDB(ctrl)
            base_db.mPatchClusterDB(options)

        vm_size_large.mSetVMSizeAttr.assert_any_call('cpuCount', '2')
        vm_size_large.mSetVMSizeAttr.assert_any_call('MemSize', '32GB')
        vm_size_large.mSetVMSizeAttr.assert_any_call('DiskSize', '120GB')

    def test_mPatchClusterDB_raises_on_invalid_u01_disksize(self):
        ctrl, _, _, _, _ = self._build_ctrl_for_patchcluster()

        options = SimpleNamespace(
            debug=False,
            jsonconf={
                'rack': {
                    'gb_storage': '100'
                },
                'vm': {
                    'size': 'Large',
                    'cores': 2,
                    'gb_memory': 32,
                    'gb_disk': 120,
                    'gb_tmpsize': 5
                },
                'force_vm_u01_disksize': '5GB'
            }
        )

        def check_config_option(key, default=None):
            mapping = {
                'core_to_vcpu_ratio': 2,
                'remove_configkeys': 'True',
                'ignore_memory_payload': 'False'
            }
            return mapping.get(key, default)

        with patch('exabox.ovm.clubasedb.umaskSensitiveData', side_effect=lambda data: data), \
             patch('exabox.ovm.clubasedb.ebCluCmdCheckOptions', return_value=False), \
             patch.object(ctrl, 'mCheckConfigOption', side_effect=check_config_option):
            base_db = exaBoxBaseDB(ctrl)
            with self.assertRaises(ExacloudRuntimeError) as ctx:
                base_db.mPatchClusterDB(options)

        self.assertIn('force_vm_u01_disksize', str(ctx.exception))

    def test_mPatchClusterDB_invalid_base64_sshkey_raises(self):
        ctrl, _, _, _, _ = self._build_ctrl_for_patchcluster()
        ctrl.mGetToolsKey.return_value = 'invalid'

        options = SimpleNamespace(
            debug=False,
            jsonconf={
                'vm': {
                    'size': 'Large',
                    'sshkey': 'invalid'
                }
            }
        )

        def check_config_option(key, default=None):
            mapping = {
                'core_to_vcpu_ratio': 2,
                'remove_configkeys': 'True',
                'ignore_memory_payload': 'True'
            }
            return mapping.get(key, default)

        with patch('exabox.ovm.clubasedb.umaskSensitiveData', side_effect=lambda data: data), \
             patch('exabox.ovm.clubasedb.check_string_base64', return_value=False), \
             patch('exabox.ovm.clubasedb.ebCluCmdCheckOptions', return_value=False), \
             patch.object(ctrl, 'mCheckConfigOption', side_effect=check_config_option):
            base_db = exaBoxBaseDB(ctrl)
            with self.assertRaises(ExacloudRuntimeError) as ctx:
                base_db.mPatchClusterDB(options)

        self.assertIn('sshkey', str(ctx.exception))

    def test_mPatchClusterDB_applies_u01_disksize_commands(self):
        ctrl, _, vm_size_large, _, _ = self._build_ctrl_for_patchcluster()
        ctrl.mGetOEDARequestsPath.return_value = '/tmp/oeda'
        ctrl.mExecuteLocal = MagicMock()

        options = SimpleNamespace(
            debug=False,
            jsonconf={
                'rack': {
                    'gb_storage': '300'
                },
                'vm': {
                    'size': 'Medium',
                    'cores': 2,
                    'gb_memory': 32,
                    'gb_disk': 150
                },
                'force_vm_u01_disksize': '200GB'
            }
        )

        def check_config_option(key, default=None):
            mapping = {
                'core_to_vcpu_ratio': 2,
                'remove_configkeys': 'True',
                'ignore_memory_payload': 'False'
            }
            return mapping.get(key, default)

        with patch('exabox.ovm.clubasedb.umaskSensitiveData', side_effect=lambda data: data), \
             patch('exabox.ovm.clubasedb.ebCluCmdCheckOptions', return_value=False), \
             patch.object(ctrl, 'mCheckConfigOption', side_effect=check_config_option):
            base_db = exaBoxBaseDB(ctrl)
            base_db.mPatchClusterDB(options)

        sed_calls = [call.args[0] for call in ctrl.mExecuteLocal.call_args_list]
        self.assertTrue(any("VGEXTRASPACE=190" in cmd for cmd in sed_calls))
        self.assertEqual(len(sed_calls), 3)

    def test_mAddUserDomU_executes_expected_commands(self):
        ctrl = MagicMock()
        ctrl.mReturnDom0DomUPair.return_value = [('dom0', 'domu')]
        ctrl.mAddUserPubKey = MagicMock()

        base_db = exaBoxBaseDB(ctrl)

        with patch('exabox.ovm.clubasedb.get_gcontext', return_value=MagicMock()), \
             patch('exabox.ovm.clubasedb.node_cmd_abs_path_check', side_effect=lambda node, cmd: f'/mock/{cmd}'), \
             patch('exabox.ovm.clubasedb.connect_to_host') as mock_connect:

            mock_node = MagicMock()
            mock_cm = MagicMock()
            mock_cm.__enter__.return_value = mock_node
            mock_cm.__exit__.return_value = False
            mock_connect.return_value = mock_cm

            base_db.mAddUserDomU('testuser', 1001, 1001, aSudoAccess=True)

        expected = [
            '/usr/sbin/groupadd -g 1001 testuser',
            '/usr/sbin/useradd -u 1001 -g 1001 -d /home/testuser -s /bin/bash -G adm,wheel,systemd-journal testuser',
            "echo 'testuser ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers",
            '/mock/mkdir -p /home/testuser/.ssh',
            '/mock/chmod 700 /home/testuser/.ssh',
            '/mock/chown testuser:testuser /home/testuser/.ssh'
        ]
        executed = [args.args[0] for args in mock_node.mExecuteCmd.call_args_list]
        self.assertEqual(executed, expected)
        ctrl.mAddUserPubKey.assert_called_once_with('testuser')

    def test_mDeleteUserDomU_executes_userdel_command(self):
        ctrl = MagicMock()
        ctrl.mReturnDom0DomUPair.return_value = [('dom0', 'domu')]

        base_db = exaBoxBaseDB(ctrl)

        with patch('exabox.ovm.clubasedb.get_gcontext', return_value=MagicMock()), \
             patch('exabox.ovm.clubasedb.connect_to_host') as mock_connect:

            mock_node = MagicMock()
            mock_cm = MagicMock()
            mock_cm.__enter__.return_value = mock_node
            mock_cm.__exit__.return_value = False
            mock_connect.return_value = mock_cm

            base_db.mDeleteUserDomU('obsolete')

        mock_node.mExecuteCmd.assert_called_once_with('/usr/sbin/userdel -r obsolete')

    def test_mCustomerNetworkXMLUpdateBaseDB_missing_ntp_conf_raises(self):
        ctrl = MagicMock()
        ctrl.mIsExabm.return_value = True
        ctrl.mIsOciEXACC.return_value = False
        ctrl.mReturnDom0DomUPair.return_value = [('dom0.example.com', 'domu.example.com')]
        ctrl.mReturnDom0DomUNATPair.return_value = [('dom0.example.com', 'domu.example.com')]
        ctrl.mFetchEgressIpsFromPayload.return_value = []
        ctrl.mSetDRNetPresent = MagicMock()
        ctrl.mSetIPv6SingleStackPresent = MagicMock()

        dom0_machine = MagicMock()
        dom0_machine.mGetMacMachines.return_value = ['domu1']
        dom0_machine.mGetMacHostName.return_value = 'dom0.example.com'
        dom0_machine.mGetMacNetworks.return_value = ['net-admin']

        domu_machine = MagicMock()
        domu_machine.mGetMacNetworks.return_value = ['net-client']
        domu_machine.mGetMacHostName.return_value = 'domu-host'
        domu_machine.mGetMacMachines.return_value = []
        domu_machine.mSetMacTimeZone = MagicMock()
        dom0_network = MagicMock()
        dom0_network.mGetNetType.return_value = 'client'
        dom0_network.mGetNetNatHostName.return_value = 'domu.example.com'
        dom0_network.mGetNetNatAddr.return_value = '10.0.0.50'

        machines = MagicMock()
        machines.mGetMachineConfig.side_effect = lambda host: {
            'dom0.example.com': dom0_machine,
            'domu1': domu_machine,
            'domu-host': domu_machine,
            'domu.example.com': domu_machine
        }[host]
        machines.mGetMachineConfigList.return_value = {
            'dom0.example.com': dom0_machine,
            'domu1': domu_machine
        }
        ctrl.mGetMachines.return_value = machines

        client_net = MagicMock()
        client_net.mGetNetType.return_value = 'client'
        client_net.mGetNetNatHostName.return_value = 'domu.example.com'
        client_net.mGetNetNatAddr.return_value = '10.0.0.50'
        client_net.mDumpConfig = MagicMock()
        client_net_v6 = MagicMock()
        client_net_v6.mGetNetType.return_value = 'client'

        admin_net = MagicMock()
        admin_net.mGetNetType.return_value = 'admin'
        admin_net.mGetNetDomainName.return_value = 'example.com'
        admin_net.mGetNetMask.return_value = '255.255.255.0'

        networks = MagicMock()
        networks.mGetNetworkConfigList.return_value = {
            'net-client': client_net,
            'net-admin': admin_net
        }
        networks.mGetNetworkConfig.side_effect = lambda net_id: {
            'net-client': client_net,
            'net-admin': admin_net
        }[net_id]
        ctrl.mGetNetworks.return_value = networks

        ctrl.mGetNetworkDiscovered.return_value = {
            'client_net': {
                'bond_master': 'bond0',
                'bond_slaves': 'eth0,eth1'
            }
        }

        options = SimpleNamespace(
            jsonconf={
                'customer_network': {
                    'timezone': 'UTC',
                    'nodes': [{
                        'client': {
                            'hostname': 'client-host',
                            'domainname': 'example.com',
                            'ip': '10.0.0.10',
                            'netmask': '255.255.255.0',
                            'gateway': '10.0.0.1',
                            'mac': 'AA:BB:CC:DD:EE:FF',
                            'nathostname': 'client-nat',
                            'natip': 'discover',
                            'natdomainname': 'example.com',
                            'natmask': '255.255.255.0',
                            'domu_oracle_name': 'domu.example.com'
                        },
                        'dom0': 'dom0.example.com',
                        'admin': {
                            'hostname': 'admin-host',
                            'domainname': 'example.com',
                            'ip': '192.168.0.10',
                            'netmask': '255.255.255.0'
                        }
                    }]
                }
            }
        )

        with patch('exabox.ovm.clubasedb.NetworkUtils') as mock_utils:
            mock_utils.return_value.mClassifyStack.return_value = 'single'
            mock_utils.return_value.mGetIPv4IPv6Payload.side_effect = [
                ('10.0.0.10', None),
                ('255.255.255.0', None),
                ('10.0.0.1', None)
            ]
            base_db = exaBoxBaseDB(ctrl)
            with self.assertRaises(ExacloudRuntimeError) as ctx:
                base_db.mCustomerNetworkXMLUpdateBaseDB(options)

        self.assertIn('_ntp_conf', str(ctx.exception))

    def test_mCustomerNetworkXMLUpdateBaseDB_raises_when_domu_missing(self):
        ctrl = MagicMock()
        ctrl.mIsExabm.return_value = True
        ctrl.mIsOciEXACC.return_value = False
        ctrl.mReturnDom0DomUPair.return_value = [('dom0.example.com', 'domu.example.com')]
        ctrl.mFetchEgressIpsFromPayload.return_value = []

        machines = MagicMock()
        dom0_mac = MagicMock()
        dom0_mac.mGetMacMachines.return_value = ['domu1']
        machines.mGetMachineConfig.side_effect = lambda name: {
            'dom0.example.com': dom0_mac,
            'domu1': MagicMock()
        }.get(name, MagicMock())
        ctrl.mGetMachines.return_value = machines

        networks = MagicMock()
        network_conf = MagicMock()
        network_conf.mGetNetType.return_value = 'client'
        network_conf.mGetNetNatHostName.return_value = 'domu-nat.example.com'
        networks.mGetNetworkConfig.return_value = network_conf
        ctrl.mGetNetworks.return_value = networks

        options = SimpleNamespace(
            jsonconf={
                'customer_network': {
                    'nodes': [{
                        'client': {
                            'hostname': 'client-host',
                            'domainname': 'example.com',
                            'ip': '10.0.0.10',
                            'netmask': '255.255.255.0',
                            'gateway': '10.0.0.1',
                            'mac': 'aa:bb:cc:dd:ee:ff'
                        },
                        'dom0': 'dom0.example.com'
                    }]
                }
            }
        )

        base_db = exaBoxBaseDB(ctrl)
        with patch('exabox.ovm.clubasedb.NetworkUtils') as mock_utils:
            mock_utils.return_value.mClassifyStack.return_value = 'single'
            mock_utils.return_value.mGetIPv4IPv6Payload.return_value = ('10.0.0.10', None)
            with self.assertRaises(ExacloudRuntimeError):
                base_db.mCustomerNetworkXMLUpdateBaseDB(options)


if __name__ == '__main__':
    unittest.main()
