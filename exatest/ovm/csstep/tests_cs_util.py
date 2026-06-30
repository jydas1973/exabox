#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/tests_cs_util.py /main/4 2025/10/27 04:36:02 pbellary Exp $
#
# tests_cs_util.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_util.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    remamid     04/29/26 - Adjust switch SSH handling
#    remamid     03/04/26 - Bug 38973298 Add AIDE tests
#    jfsaldan    03/13/26 - Bug 39002144 - EXADB-XS-PP: VMC PROVISION GOT STUCK
#                           AT THE STEP OF AWAIT_ADD_SSH_KEYS | EXACLOUD DOES
#                           NOT ENSURE AGENT SYSTEMD SERVICE IS UP AFTER
#                           PROVISIONING
#    rajsag      07/21/25 - Creation
#
import json
import copy
import io
import base64
import unittest
from unittest.mock import Mock, patch, call
from exabox.core.MockCommand import exaMockCommand
from exabox.ovm.csstep.cs_util import csUtil, _SSH_DROPIN_HEADER
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.csstep.exascale.exascaleutils import ebExascaleUtils
from exabox.ovm.csstep.cs_constants import csConstants, csXSConstants, csXSEighthConstants, csBaseDBXSConstants, csAsmEDVConstants
from exabox.utils.node import connect_to_host
from exabox.core.Context import get_gcontext
from exabox.ovm.userutils import ebUserUtils
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.vmbackup import ebCluManageVMBackup
from exabox.ovm.clucontrol import exaBoxCluCtrl

CREATE_SERVICE_PAYLOAD = """ 
{
   "exascale":{
      "network_services":{
         "dns":[
            "169.254.169.254"
         ],
         "ntp":[
            "169.254.169.254"
         ]
      },
      "cell_list":[
         "scaqab10celadm01.us.oracle.com",
         "scaqab10celadm02.us.oracle.com",
         "scaqab10celadm03.us.oracle.com"
      ],
      "exascale_cluster_name":"sea2d2cl37541fe175f7847febc200f6b51aa9cb3clu01ers",
      "storage_pool":{
         "name":"hcpool",
         "gb_size":"10240"
      },
      "db_vault":{
         "name":"vault1clu02",
         "gb_size":10
      },
      "ctrl_network":{
         "ip":"10.0.130.110",
         "port":"5052",
         "name":"sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
      }
    },
   "rack":{
      "storageType":"XS",
      "xsVmImage": "True",
      "xsVmBackup": "True",
      "system_vault": [
            {
                "vault_type":"image",
                "name":"imagevault"
            },
             {
                "vault_type":"backup",
                "name":"backupvault",
                "xsVmBackupRetentionNum": "2"
            }
      ]
   }
}
"""

class TestCsUtil(ebTestClucontrol):

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsXS', return_value=True)
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mGetRackSize', return_value="eighthrack")
    def test_mGetConstants_xs_eighth(self, mock_mGetRackSize, mock_mIsXS):
        # Arrange
        ebox = self.mGetClubox()
        ebox.mSetEnableKVM(True)
        cs_util = csUtil()

        # Act
        result = cs_util.mGetConstants(ebox)

        # Assert
        self.assertEqual(result, csXSEighthConstants)

    def test_mGetConstants_asm_edv(self):
        # Arrange
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(CREATE_SERVICE_PAYLOAD)
        _ebox.mSetEnableKVM(True)

        _utils = ebExascaleUtils(_ebox)
        _status = _utils.mIsEDVImageSupported(_options)
        cs_util = csUtil()

        # Act
        result = cs_util.mGetConstants(_ebox, _options)

        # Assert
        self.assertEqual(result, csAsmEDVConstants)

    def test_mGetConstants_xs_not_eighth(self):
        # Arrange
        ebox = Mock()
        ebox.mIsXS.return_value = True
        ebox.mGetRackSize.return_value = 'not_eighth'
        cs_util = csUtil()

        # Act
        result = cs_util.mGetConstants(ebox)

        # Assert
        self.assertEqual(result, csXSConstants)

    def test_mGetConstants_base_db(self):
        # Arrange
        ebox = Mock()
        ebox.mIsXS.return_value = False
        ebox.isBaseDB.return_value = True
        ebox.isExacomputeVM.return_value = False
        base_db = Mock()
        ebox.mGetBaseDB.return_value = base_db
        cs_util = csUtil()

        # Act
        result = cs_util.mGetConstants(ebox)

        # Assert
        self.assertEqual(result, csBaseDBXSConstants)
        base_db.mUpdateOedaPropertiesInterface.assert_called_once()

    def test_mGetConstants_exacompute_vm(self):
        # Arrange
        ebox = Mock()
        ebox.mIsXS.return_value = False
        ebox.isBaseDB.return_value = False
        ebox.isExacomputeVM.return_value = True
        base_db = Mock()
        ebox.mGetBaseDB.return_value = base_db
        cs_util = csUtil()

        # Act
        result = cs_util.mGetConstants(ebox)

        # Assert
        self.assertEqual(result, csBaseDBXSConstants)
        base_db.mUpdateOedaPropertiesInterface.assert_called_once()

    def test_mGetConstants_default(self):
        # Arrange
        ebox = Mock()
        ebox.mIsXS.return_value = False
        ebox.isBaseDB.return_value = False
        ebox.isExacomputeVM.return_value = False
        cs_util = csUtil()

        # Act
        result = cs_util.mGetConstants(ebox)

        # Assert
        self.assertEqual(result, csConstants)

    def test_mGetConstants_check_base_db_false(self):
        # Arrange
        ebox = Mock()
        ebox.mIsXS.return_value = False
        ebox.isBaseDB.return_value = True
        ebox.isExacomputeVM.return_value = False
        base_db = Mock()
        ebox.mGetBaseDB.return_value = base_db
        cs_util = csUtil()

        # Act
        result = cs_util.mGetConstants(ebox, aCheckBaseDb=False)

        # Assert
        self.assertEqual(result, csConstants)
        base_db.mUpdateOedaPropertiesInterface.assert_not_called()

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mOEDASkipPassProperty')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateOEDAProperties')
    def test_mUpdateOEDAConfiguration(self, mock_mUpdateOEDAProperties, mock_mOEDASkipPassProperty):
        _ebox = self.mGetClubox()
        cs_util = csUtil()
        cs_util.mUpdateOEDAConfiguration(_ebox, self.mGetClubox().mGetArgsOptions())

    @patch('exabox.ovm.csstep.cs_util.time.sleep')
    def test_mStartServiceInNode_restarts_service(self, aMockSleep):
        cs_util = csUtil()
        service_name = "unit-test-service"
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /sbin/systemctl", aPersist=True),
                    exaMockCommand(f"systemctl stop {service_name}", aPersist=True),
                    exaMockCommand(f"systemctl start {service_name}", aPersist=True),
                    exaMockCommand(f"systemctl is-active {service_name}", aPersist=True),
                ],
            ],
        }


        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _domU = _ebox.mReturnDom0DomUPair()[0][1]

        with connect_to_host(_domU, get_gcontext()) as _node:
            _res = cs_util.mStartServiceInNode(_node, service_name)

        self.assertTrue(aMockSleep.called)
        self.assertIsNone(_res)

    def test_mSetupDBCSAgentAuth(self):
        cs_util = csUtil()

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/opt/oracle/dcs/bin/setupAuthDcs.py"),
                    exaMockCommand("/bin/test -e /sbin/systemctl", aPersist=True),
                    exaMockCommand(f"systemctl stop dbcsagent", aPersist=True),
                    exaMockCommand(f"systemctl start dbcsagent", aPersist=True),
                    exaMockCommand(f"systemctl is-active dbcsagent", aPersist=True),
                    exaMockCommand(f"systemctl stop dbcsadmin", aPersist=True),
                    exaMockCommand(f"systemctl start dbcsadmin", aPersist=True),
                    exaMockCommand(f"systemctl is-active dbcsadmin", aPersist=True),
                ],
            ],
        }


        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _dom0_domU_pairs = _ebox.mReturnDom0DomUPair()

        _res = cs_util.mSetupDBCSAgentAuth(_dom0_domU_pairs)

        self.assertIsNone(_res)

    def test_mSetupDBCSAgentAuth_first_start_fails(self):
        cs_util = csUtil()

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/opt/oracle/dcs/bin/setupAuthDcs.py"),
                    exaMockCommand("/bin/test -e /sbin/systemctl", aPersist=True),
                    exaMockCommand(f"systemctl stop dbcsagent", aPersist=True),
                    exaMockCommand(f"systemctl start dbcsagent", aPersist=True),
                    exaMockCommand(f"systemctl is-active dbcsagent", aPersist=True),

                    exaMockCommand(f"systemctl stop dbcsadmin", aPersist=True),
                    exaMockCommand(f"systemctl start dbcsadmin", aPersist=True),
                    exaMockCommand(f"systemctl is-active dbcsadmin", aRc=1),## Here we mock an error
                    exaMockCommand(f"systemctl is-active dbcsadmin", aRc=0), ## Here we mock a subsequent success
                ],
            ],
        }


        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _dom0_domU_pairs = _ebox.mReturnDom0DomUPair()

        _res = cs_util.mSetupDBCSAgentAuth(_dom0_domU_pairs)

        self.assertIsNone(_res)
        
    @patch('exabox.core.Node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.core.Node.exaBoxNode.mDisconnect')
    @patch('exabox.core.Node.exaBoxNode.mConnect')
    def test_mExadataAide(self, mock_mConnect, mock_mDisconnect, mock_mExecuteCmdLog):
        _ebox = Mock()
        _ebox.mReturnDom0DomUPair.return_value = [
            ("dom0-1", "domu-1"),
            ("dom0-2", "domu-2"),
        ]
        cs_util = csUtil()
        cs_util.mExadataAide(_ebox, "disable")

        self.assertEqual(mock_mConnect.call_count, 2)
        self.assertEqual(mock_mDisconnect.call_count, 2)
        mock_mExecuteCmdLog.assert_any_call("/opt/oracle.SupportTools/exadataAIDE -disable")

    @patch('exabox.ovm.userutils.node_exec_cmd_check')
    @patch('exabox.ovm.userutils.node_cmd_abs_path_check')
    @patch('exabox.ovm.userutils.csUtil')
    @patch('exabox.ovm.userutils.exaBoxNode')
    def test_mAddSecscanSshdSingle_switch_skips_aide(
        self,
        mock_exa_node_cls,
        mock_csutil_cls,
        mock_node_cmd_abs_path_check,
        mock_node_exec_cmd_check,
    ):
        ebox = Mock()
        ebox.mReturnAllClusterHosts.return_value = (
            ['dom0-host'],
            [],
            ['cell-1'],
            ['switch-host'],
        )

        mock_node = mock_exa_node_cls.return_value
        mock_node.mFileExists.return_value = False
        mock_node_cmd_abs_path_check.return_value = '/sbin/service'
        cs_util_instance = mock_csutil_cls.return_value
        cs_util_instance.mUpdateExacloudSshd.return_value = ('/etc/ssh/sshd_config', True)

        ebUserUtils.mAddSecscanSshdSingle(ebox, 'switch-host')

        cs_util_instance.mUpdateExacloudSshd.assert_called_once_with(
            mock_node,
            {'TrustedUserCAKeys': '/etc/ssh/ca.pub'},
            conf_file='/etc/ssh/sshd_config',
        )
        mock_node_exec_cmd_check.assert_called_once_with(mock_node, '/sbin/service sshd restart')
        mock_node.mConnect.assert_called_once_with(aHost='switch-host')
        mock_node.mDisconnect.assert_called_once()

    @patch('exabox.ovm.userutils.node_exec_cmd_check')
    @patch('exabox.ovm.userutils.node_cmd_abs_path_check')
    @patch('exabox.ovm.userutils.csUtil')
    @patch('exabox.ovm.userutils.exaBoxNode')
    def test_mAddSecscanSshdSingle_dom0_restarts_sshd(
        self,
        mock_exa_node_cls,
        mock_csutil_cls,
        mock_node_cmd_abs_path_check,
        mock_node_exec_cmd_check,
    ):
        ebox = Mock()
        ebox.mReturnAllClusterHosts.return_value = (
            ['dom0-host'],
            ['domu-host'],
            ['cell-1'],
            [],
        )

        mock_node = mock_exa_node_cls.return_value
        mock_node_cmd_abs_path_check.return_value = '/sbin/service'
        cs_util_instance = mock_csutil_cls.return_value
        cs_util_instance.mUpdateExacloudSshd.return_value = ("/etc/ssh/sshd_config", True)

        ebUserUtils.mAddSecscanSshdSingle(ebox, 'dom0-host')

        cs_util_instance.mUpdateExacloudSshd.assert_called_once()
        call_args = cs_util_instance.mUpdateExacloudSshd.call_args
        self.assertEqual(call_args.kwargs.get('aHosts'), ['dom0-host'])
        mock_node_exec_cmd_check.assert_called_once_with(mock_node, '/sbin/service sshd restart')
        mock_node.mDisconnect.assert_called_once()

    @patch('exabox.ovm.csstep.cs_util.node_write_text_file')
    @patch('exabox.ovm.csstep.cs_util.node_exec_cmd_check')
    def test_mUpdateExacloudSshd_dropin_creates_file(self, mock_exec, mock_write):
        node = Mock()
        node.mFileExists.return_value = False

        cs_util = csUtil()
        conf, changed = cs_util.mUpdateExacloudSshd(node, {'MaxStartups': '100'})

        self.assertTrue(changed)
        self.assertEqual(conf, "/etc/ssh/sshd_config.d/exacloud.config")
        self.assertEqual(
            mock_exec.call_args_list,
            [
                call(node, '/bin/mkdir -p /etc/ssh/sshd_config.d'),
                call(node, '/bin/chmod 755 /etc/ssh/sshd_config.d'),
                call(node, '/bin/chmod 644 /etc/ssh/sshd_config.d/exacloud.config'),
            ],
        )
        written_content = mock_write.call_args.args[2]
        self.assertTrue(written_content.startswith(_SSH_DROPIN_HEADER))
        self.assertIn('MaxStartups 100', written_content)

    @patch('exabox.ovm.csstep.cs_util.node_read_text_file', return_value='PermitRootLogin without-password\n')
    @patch('exabox.ovm.csstep.cs_util.node_write_text_file')
    @patch('exabox.ovm.csstep.cs_util.node_exec_cmd_check')
    def test_mUpdateExacloudSshd_noop_when_content_matches(self, mock_exec, mock_write, mock_read):
        node = Mock()
        node.mFileExists.return_value = True
        ebox = Mock()
        ebox.mCheckConfigOption.return_value = ''

        cs_util = csUtil()
        with patch.object(cs_util, 'mDisableAIDE') as mock_disable, \
             patch.object(cs_util, 'mEnableAIDE') as mock_enable, \
             patch.object(cs_util, 'mUpdateAIDE') as mock_update:
            conf, changed = cs_util.mUpdateExacloudSshd(
                node,
                {'PermitRootLogin': 'without-password'},
                ebox=ebox,
                aHosts=['dom0-host'],
            )

        self.assertFalse(changed)
        self.assertEqual(conf, "/etc/ssh/sshd_config")
        mock_exec.assert_not_called()
        mock_write.assert_not_called()
        mock_read.assert_called_once()
        mock_disable.assert_not_called()
        mock_enable.assert_not_called()
        mock_update.assert_not_called()

    @patch('exabox.ovm.csstep.cs_util.node_write_text_file')
    def test_mUpdateExacloudSshd_triggers_aide_for_hosts(self, mock_write):
        node = Mock()
        node.mFileExists.return_value = False
        ebox = Mock()
        ebox.mCheckConfigOption.return_value = ''

        cs_util = csUtil()
        with patch.object(cs_util, 'mDisableAIDE') as mock_disable, \
             patch.object(cs_util, 'mEnableAIDE') as mock_enable, \
             patch.object(cs_util, 'mUpdateAIDE') as mock_update:
            _, changed = cs_util.mUpdateExacloudSshd(
                node,
                {'PasswordAuthentication': 'no'},
                ebox=ebox,
                aHosts=['dom0-host'],
            )

        self.assertTrue(changed)
        mock_write.assert_called_once()
        mock_disable.assert_called_once_with(ebox, aHosts=['dom0-host'])
        mock_enable.assert_called_once_with(ebox, aHosts=['dom0-host'])
        mock_update.assert_called_once_with(ebox, aHosts=['dom0-host'])

    @patch('exabox.ovm.csstep.cs_util.node_exec_cmd_check')
    def test_mHostAccessControlRootssh_invokes_binary(self, mock_exec):
        node = Mock()
        node.mIsConnected.return_value = True

        cs_util = csUtil()
        cs_util.mHostAccessControlRootssh(node)

        mock_exec.assert_called_once_with(node, '/opt/oracle.cellos/host_access_control rootssh -k')

    @patch('exabox.ovm.csstep.cs_util.node_exec_cmd_check')
    def test_mHostAccessControlRootssh_unlock_invokes_binary(self, mock_exec):
        node = Mock()
        node.mIsConnected.return_value = True

        cs_util = csUtil()
        cs_util.mHostAccessControlRootsshUnlock(node)

        mock_exec.assert_called_once_with(node, '/opt/oracle.cellos/host_access_control rootssh -u')

    def test_mHostAccessControlRootssh_raises_if_not_connected(self):
        node = Mock()
        node.mIsConnected.return_value = False
        cs_util = csUtil()

        with self.assertRaises(ExacloudRuntimeError):
            cs_util.mHostAccessControlRootssh(node)

    def test_mHostAccessControlRootsshUnlock_raises_if_not_connected(self):
        node = Mock()
        node.mIsConnected.return_value = False
        cs_util = csUtil()

        with self.assertRaises(ExacloudRuntimeError):
            cs_util.mHostAccessControlRootsshUnlock(node)

    def test_mPatchCellsSSHDConfig_restarts_when_updated(self):
        fake_ctrl = type('FakeCtrl', (), {})()
        fake_ctrl._exaBoxCluCtrl__cmd = 'createservice'
        fake_ctrl.mReturnCellNodes = Mock(return_value=['cell-1'])

        class ImmediateProcess:
            def __init__(self, callback, args=None):
                self._callback = callback
                self._args = args or []

            def mSetMaxExecutionTime(self, *args, **kwargs):
                return self

            def mSetJoinTimeout(self, *args, **kwargs):
                return self

            def mSetLogTimeoutFx(self, *args, **kwargs):
                return self

        class ImmediateManager:
            def __init__(self, *args, **kwargs):
                self._processes = []

            def mStartAppend(self, process):
                self._processes.append(process)

            def mJoinProcess(self):
                for proc in self._processes:
                    proc._callback(*proc._args)

        stdout = io.StringIO("50\n")

        with patch('exabox.ovm.clucontrol.ProcessStructure', ImmediateProcess), \
             patch('exabox.ovm.clucontrol.ProcessManager', ImmediateManager), \
             patch('exabox.ovm.clucontrol.exaBoxNode') as mock_node_cls, \
             patch('exabox.ovm.clucontrol.csUtil') as mock_csutil_cls, \
             patch('exabox.ovm.clucontrol.node_exec_cmd_check') as mock_exec, \
             patch('exabox.ovm.clucontrol.ebCluCmdCheckOptions', return_value=False):

            mock_node = mock_node_cls.return_value
            mock_node.mExecuteCmd.return_value = (None, stdout, None)
            mock_csutil = mock_csutil_cls.return_value
            mock_csutil.mUpdateExacloudSshd.return_value = ("/etc/ssh/sshd_config", True)

            exaBoxCluCtrl.mPatchCellsSSHDConfig(fake_ctrl)

        mock_csutil.mUpdateExacloudSshd.assert_called_once()
        mock_exec.assert_called_once_with(mock_node, 'service sshd restart')
        mock_node.mDisconnect.assert_called()

    def test_mPatchCellsSSHDConfig_skips_when_already_patched(self):
        fake_ctrl = type('FakeCtrl', (), {})()
        fake_ctrl._exaBoxCluCtrl__cmd = 'createservice'
        fake_ctrl.mReturnCellNodes = Mock(return_value=['cell-1'])

        class ImmediateProcess:
            def __init__(self, callback, args=None):
                self._callback = callback
                self._args = args or []

            def mSetMaxExecutionTime(self, *args, **kwargs):
                return self

            def mSetJoinTimeout(self, *args, **kwargs):
                return self

            def mSetLogTimeoutFx(self, *args, **kwargs):
                return self

        class ImmediateManager:
            def __init__(self, *args, **kwargs):
                self._processes = []

            def mStartAppend(self, process):
                self._processes.append(process)

            def mJoinProcess(self):
                for proc in self._processes:
                    proc._callback(*proc._args)

        stdout = io.StringIO("100\n")

        with patch('exabox.ovm.clucontrol.ProcessStructure', ImmediateProcess), \
             patch('exabox.ovm.clucontrol.ProcessManager', ImmediateManager), \
             patch('exabox.ovm.clucontrol.exaBoxNode') as mock_node_cls, \
             patch('exabox.ovm.clucontrol.csUtil') as mock_csutil_cls, \
             patch('exabox.ovm.clucontrol.node_exec_cmd_check') as mock_exec, \
             patch('exabox.ovm.clucontrol.ebCluCmdCheckOptions', return_value=False):

            mock_node = mock_node_cls.return_value
            mock_node.mExecuteCmd.return_value = (None, stdout, None)
            mock_csutil = mock_csutil_cls.return_value

            exaBoxCluCtrl.mPatchCellsSSHDConfig(fake_ctrl)

        mock_csutil.mUpdateExacloudSshd.assert_not_called()
        mock_exec.assert_not_called()
        mock_node.mDisconnect.assert_called_once()

    def test_mPatchCellsSSHDConfig_no_restart_when_unchanged(self):
        fake_ctrl = type('FakeCtrl', (), {})()
        fake_ctrl._exaBoxCluCtrl__cmd = 'createservice'
        fake_ctrl.mReturnCellNodes = Mock(return_value=['cell-1'])

        class ImmediateProcess:
            def __init__(self, callback, args=None):
                self._callback = callback
                self._args = args or []

            def mSetMaxExecutionTime(self, *args, **kwargs):
                return self

            def mSetJoinTimeout(self, *args, **kwargs):
                return self

            def mSetLogTimeoutFx(self, *args, **kwargs):
                return self

        class ImmediateManager:
            def __init__(self, *args, **kwargs):
                self._processes = []

            def mStartAppend(self, process):
                self._processes.append(process)

            def mJoinProcess(self):
                for proc in self._processes:
                    proc._callback(*proc._args)

        stdout = io.StringIO("50\n")

        with patch('exabox.ovm.clucontrol.ProcessStructure', ImmediateProcess), \
             patch('exabox.ovm.clucontrol.ProcessManager', ImmediateManager), \
             patch('exabox.ovm.clucontrol.exaBoxNode') as mock_node_cls, \
             patch('exabox.ovm.clucontrol.csUtil') as mock_csutil_cls, \
             patch('exabox.ovm.clucontrol.node_exec_cmd_check') as mock_exec, \
             patch('exabox.ovm.clucontrol.ebCluCmdCheckOptions', return_value=False):

            mock_node = mock_node_cls.return_value
            mock_node.mExecuteCmd.return_value = (None, stdout, None)
            mock_csutil = mock_csutil_cls.return_value
            mock_csutil.mUpdateExacloudSshd.return_value = ("/etc/ssh/sshd_config", False)

            exaBoxCluCtrl.mPatchCellsSSHDConfig(fake_ctrl)

        mock_csutil.mUpdateExacloudSshd.assert_called_once()
        mock_exec.assert_not_called()
        mock_node.mDisconnect.assert_called_once()

    def test_mSetupLockdown_lock_mode_fallback_to_dropin(self):
        fake_ctrl = type('FakeCtrl', (), {})()
        fake_ctrl._exaBoxCluCtrl__debug = False
        fake_ctrl._exaBoxCluCtrl__ociexacc = False
        fake_ctrl.mReturnAllClusterHosts = Mock(return_value=(['dom0-host'], [], [], []))
        fake_ctrl.mIsKVM = Mock(return_value=False)
        fake_ctrl.mIsXS = Mock(return_value=False)
        fake_ctrl.mPingHost = Mock(return_value=True)
        fake_ctrl.mLockCellUsers = Mock()

        options = type('Opt', (), {'jsonconf': None, 'force': True, 'resetpwd': False})()

        class FakeKms:
            def mGetExaKmsEntry(self, _):
                return True

        class FakeContext:
            def mGetExaKms(self):
                return FakeKms()

            def mGetConfigOptions(self):
                return {'default_pwd': base64.b64encode(b'dummy').decode('ascii')}

        with patch('exabox.ovm.clucontrol.get_gcontext', return_value=FakeContext()), \
             patch('exabox.ovm.clucontrol.exaBoxNode') as mock_node_cls, \
             patch('exabox.ovm.clucontrol.csUtil') as mock_csutil_cls, \
             patch('exabox.ovm.clucontrol.node_exec_cmd_check') as mock_exec:

            mock_node = mock_node_cls.return_value
            mock_node.mFileExists.return_value = False
            mock_cs = mock_csutil_cls.return_value
            mock_cs.mHostAccessControlRootssh.side_effect = Exception('fail')
            mock_cs.mUpdateExacloudSshd.return_value = ("/etc/ssh/sshd_config", False)

            exaBoxCluCtrl.mSetupLockdown(fake_ctrl, True, options)

        mock_cs.mHostAccessControlRootssh.assert_called_once()
        mock_cs.mUpdateExacloudSshd.assert_called_once()
        mock_exec.assert_not_called()
        mock_node.mDisconnect.assert_called_once()

    def test_mSetupLockdown_unlock_executes_restart(self):
        fake_ctrl = type('FakeCtrl', (), {})()
        fake_ctrl._exaBoxCluCtrl__debug = False
        fake_ctrl._exaBoxCluCtrl__ociexacc = False
        fake_ctrl.mReturnAllClusterHosts = Mock(return_value=(['dom0-host'], [], [], []))
        fake_ctrl.mIsKVM = Mock(return_value=False)
        fake_ctrl.mIsXS = Mock(return_value=False)
        fake_ctrl.mPingHost = Mock(return_value=True)
        fake_ctrl.mLockCellUsers = Mock()

        default_pwd = base64.b64encode(b'Password1!').decode('ascii')
        options = type('Opt', (), {'jsonconf': None, 'force': True, 'resetpwd': True})()

        class FakeKms:
            def mGetExaKmsEntry(self, _):
                return True

        class FakeContext:
            def mGetExaKms(self):
                return FakeKms()

            def mGetConfigOptions(self):
                return {'default_pwd': default_pwd}

        with patch('exabox.ovm.clucontrol.get_gcontext', return_value=FakeContext()), \
             patch('exabox.ovm.clucontrol.exaBoxNode') as mock_node_cls, \
             patch('exabox.ovm.clucontrol.csUtil') as mock_csutil_cls, \
             patch('exabox.ovm.clucontrol.node_exec_cmd_check') as mock_exec:

            mock_node = mock_node_cls.return_value
            mock_node.mFileExists.side_effect = [True, True]
            mock_node.mExecuteCmdLog = Mock()
            mock_cs = mock_csutil_cls.return_value

            exaBoxCluCtrl.mSetupLockdown(fake_ctrl, False, options)

        mock_cs.mHostAccessControlRootsshUnlock.assert_called_once()
        mock_cs.mUpdateExacloudSshd.assert_not_called()
        self.assertEqual(
            mock_exec.call_args_list,
            [
                call(mock_node, "/bin/sed -i 's/^auth\\s*required\\s*pam_tally2.so/#&/g' /etc/pam.d/login"),
                call(mock_node, "/bin/sed -i 's/^auth\\s*required\\s*pam_tally2.so/#&/g' /etc/pam.d/sshd"),
                call(mock_node, "service sshd restart"),
            ],
        )
        mock_node.mExecuteCmdLog.assert_called()
        mock_node.mDisconnect.assert_called_once()

    def test_mSetupLockdown_calls_lock_cell_users_when_ociexacc(self):
        ebox = self.mGetClubox()
        setattr(ebox, '_exaBoxCluCtrl__debug', False)
        setattr(ebox, '_exaBoxCluCtrl__ociexacc', True)

        options = type('Opt', (), {'jsonconf': None, 'force': True, 'resetpwd': False})()

        class FakeKms:
            def mGetExaKmsEntry(self, _):
                return True

        class FakeContext:
            def mGetExaKms(self):
                return FakeKms()

            def mGetConfigOptions(self):
                return {'default_pwd': base64.b64encode(b'dummy').decode('ascii')}

        with patch.object(ebox, 'mReturnAllClusterHosts', return_value=(['dom0-host'], [], [], [])), \
             patch.object(ebox, 'mIsKVM', return_value=False), \
             patch.object(ebox, 'mIsXS', return_value=False), \
             patch.object(ebox, 'mPingHost', return_value=True), \
             patch('exabox.ovm.clucontrol.get_gcontext', return_value=FakeContext()), \
             patch('exabox.ovm.clucontrol.exaBoxNode') as mock_node_cls, \
             patch('exabox.ovm.clucontrol.csUtil') as mock_csutil_cls, \
             patch('exabox.ovm.clucontrol.node_exec_cmd_check'), \
             patch.object(ebox, 'mLockCellUsers') as mock_lock:

            mock_node = mock_node_cls.return_value
            mock_node.mFileExists.return_value = False
            mock_cs = mock_csutil_cls.return_value
            mock_cs.mHostAccessControlRootsshUnlock.return_value = True

            exaBoxCluCtrl.mSetupLockdown(ebox, False, options)

        mock_lock.assert_called_once_with(aMode=False)

    @patch('exabox.ovm.vmbackup.node_exec_cmd_check')
    @patch('exabox.ovm.csstep.cs_util.csUtil.mUpdateExacloudSshd')
    def test_mSetSSHDOptions_restarts_when_changed(self, mock_update, mock_exec):
        mock_update.return_value = ("/etc/ssh/sshd_config", True)
        node = Mock()

        backup = ebCluManageVMBackup.__new__(ebCluManageVMBackup)
        result = backup.mSetSSHDOptions(Mock(), node)

        self.assertEqual(result, 0)
        mock_exec.assert_called_with(node, "/sbin/service sshd restart")

    @patch('exabox.ovm.vmbackup.node_exec_cmd_check')
    @patch('exabox.ovm.csstep.cs_util.csUtil.mUpdateExacloudSshd')
    def test_mSetSSHDOptions_handles_exception(self, mock_update, mock_exec):
        mock_update.side_effect = ExacloudRuntimeError(0x0, 0x0, "boom")
        node = Mock()

        backup = ebCluManageVMBackup.__new__(ebCluManageVMBackup)
        result = backup.mSetSSHDOptions(Mock(), node)

        self.assertEqual(result, 1)
        mock_exec.assert_not_called()

    @patch('exabox.ovm.vmbackup.node_exec_cmd_check')
    @patch('exabox.ovm.csstep.cs_util.csUtil.mUpdateExacloudSshd')
    def test_mSetSSHDOptions_no_restart_when_unchanged(self, mock_update, mock_exec):
        mock_update.return_value = ("/etc/ssh/sshd_config", False)
        node = Mock()

        backup = ebCluManageVMBackup.__new__(ebCluManageVMBackup)
        result = backup.mSetSSHDOptions(Mock(), node)

        self.assertEqual(result, 0)
        mock_exec.assert_not_called()


if __name__ == '__main__':
    unittest.main()
