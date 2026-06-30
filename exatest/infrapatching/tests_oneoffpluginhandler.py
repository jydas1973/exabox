#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/infrapatching/tests_oneoffpluginhandler.py /main/1 2025/02/14 17:58:04 avimonda Exp $
#
# tests_oneoffpluginhandler.py
#
# Copyright (c) 2024, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_oneoffpluginhandler.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#       araghave 06/08/26 - Bug 39483306 - QMR PATCHING FAILING DUE TO "BAD
#                           AUTHENTICATION TYPE; ALLOWED TYPES: [PUBLICKEY] ON
#                           DOMU TARGET
#    avimonda    05/15/26 - Bug 39189788 use plugin-specific console timeout
#    avimonda    11/14/24 - Bug 37201334 - AIM4ECS:0X030D0000 - ONE OFF PATCH
#                           APPLY FAILED.
#    avimonda    11/06/24 - Create new file
#    avimonda    11/06/24 - Creation
import unittest
from unittest import mock
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from unittest.mock import patch, mock_open, MagicMock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.infrapatching.handlers.pluginHandler.oneoffpluginhandler import OneOffPluginHandler
from exabox.infrapatching.handlers.pluginHandler.exacloudpluginhandler import ExacloudPluginHandler
from exabox.infrapatching.handlers.generichandler import GenericHandler
from exabox.infrapatching.utils.constants import PATCH_DOMU
from exabox.core.MockCommand import exaMockCommand

class TestOneOffPluginHandler(ebTestClucontrol):#

    @classmethod
    def setUpClass(self):
        ebLogInfo("Starting classSetUp OneOffPluginHandler")
        super(TestOneOffPluginHandler, self).setUpClass(aGenerateDatabase=True)
        self.mGetClubox(self).mGetCtx().mSetConfigOption("repository_root", self.mGetPath(self))
        _cluCtrl = self.mGetClubox(self)
        _cluCtrl._exaBoxCluCtrl__kvm_enabled = True
        self.__patch_args_dict = {'CluControl': _cluCtrl,
                                'LocalLogFile': 'exabox/exatest/infrapatching/resources/patchmgr_logs',
                                'TargetType': ['domu'], 'Operation': 'oneoff', 'OperationStyle': 'auto',
                                'PayloadType': 'exadata_release', 'TargetEnv': 'production', 'EnablePlugins': 'no',
                                'PluginTypes': 'none',
                                'CellIBSwitchesPatchZipFile': 'exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/CellPatchFile/21.2.11.0.0.220414.1.patch.zip',
                                'Dom0DomuPatchZipFile': 'exabox/exatest/infrapatching/resources/PatchPayloads/21.2.11.0.0.220414.1/CellPatchFile/21.2.11.0.0.220414.1.patch.zip', 'TargetVersion': '21.2.11.0.0.220414.1', 'ClusterID': 1,
                                'BackupMode': 'yes', 'Fedramp': 'DISABLED', 'Retry': 'no',
                                'RequestId': 'e2f947dd-b902-4949-bc04-8b8c52ec170b', 'RackName': 'slcs27', 'isMVM':'no', "ComputeNodeList":["iad123456exdd001.oraclecloud.internal","iad123456exdd004.oraclecloud.internal","iad123456exdd002.oraclecloud.internal","iad123456exdd003.oraclecloud.internal"],"StorageNodeList":["iad123456exdcl02.oraclecloud.internal","iad123456exdcl05.oraclecloud.internal","iad123456exdcl01.oraclecloud.internal","iad123456exdcl06.oraclecloud.internal","iad123456exdcl04.oraclecloud.internal","iad123456exdcl03.oraclecloud.internal"],"Dom0domUDetails":{"iad123456exdd001.oraclecloud.internal":{"domuDetails":[{"customerHostname":"ora12db01.oradb.in.cloud.com","domuNatHostname":"iad123456exdd001nat01.oraclecloud.internal","clusterName":"iad123456exd-oracle-ora12XXXXXXX-clu01","meterocpus":"0"}]},"iad123456exdd004.oraclecloud.internal":{"domuDetails":[{"customerHostname":"ora12db04.oradb.in.cloud.com","domuNatHostname":"iad123456exdd004nat01.oraclecloud.internal","clusterName":"iad123456exd-oracle-ora12XXXXXXX-clu01","meterocpus":"0"}]},"iad123456exdd002.oraclecloud.internal":{"domuDetails":[{"customerHostname":"ora12db02.oradb.in.cloud.com","domuNatHostname":"iad123456exdd002nat01.oraclecloud.internal","clusterName":"iad123456exd-oracle-ora12XXXXXXX-clu01","meterocpus":"0"}]},"iad123456exdd003.oraclecloud.internal":{"domuDetails":[{"customerHostname":"ora12db03.oradb.in.cloud.com","domuNatHostname":"iad123456exdd003nat01.oraclecloud.internal","clusterName":"iad123456exd-oracle-ora12XXXXXXX-clu01","meterocpus":"0"}]}},'ComputeNodeListByAlias':[],
                                'AdditionalOptions': [
                                    {'AllowActiveNfsMounts': 'yes', 'ClusterLess': 'no', 'EnvType': 'ecs',
                                     'ForceRemoveCustomRpms': 'no', 'IgnoreAlerts': 'no', 'IgnoreDateValidation': 'yes',
                                     'IncludeNodeList': 'none', 'LaunchNode': 'none',
                                     'OneoffCustomPluginFile': 'none', 'OneoffScriptArgs': 'none',
                                     'RackSwitchesOnly': 'no', 'SingleUpgradeNodeName': 'none', 'SkipDomuCheck': 'no',
                                     'exasplice': 'no', 'isSingleNodeUpgrade': 'no', 'serviceType': 'EXACC',
                                     'exaunitId': 0}]} 
        ebLogInfo("Ending classSetUp OneOffPluginHandler")



    @patch('exabox.core.Node.exaBoxNode.mCopy2Local')
    @patch('exabox.core.Node.exaBoxNode.mFileExists', return_value=True)
    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mGetDomUListFromXml', return_value=False)
    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.core.Node.exaBoxNode.mIsConnectable', return_value=True)
    def test_mCleanupOneoffPluginScript(self, _mock_mIsConnectable, _mock_mConnect, _mock_mGetDomUListFromXml, _mock_mFileExists, _mock_mCopy2Local):

        ebLogInfo("Executing test for mCleanupOneoffPluginScript()")
        _mock_mCopy2Local.return_value = None
        _oneOffPluginHandler = OneOffPluginHandler(self.__patch_args_dict)
        _oneOffPluginHandler.mCleanupOneoffPluginScript(['iad123456exdd004nat01.oraclecloud.internal'], '/opt/exacloud/customs/plugins/oneoff_patches/oneoff_patch.sh', '/opt/exacloud/customs/plugins/oneoff_patches/', '/opt/exacloud/customs/plugins/oneoff_logs/', '/opt/exacloud/customs/plugins/oneoff_patches/oneoff_console.log')
        _mock_mCopy2Local.assert_called_once_with('/opt/exacloud/customs/plugins/oneoff_patches/oneoff_console.log', 'exabox/exatest/infrapatching/resources/patchmgr_logs/oneoff.iad123456exdd004nat01.oraclecloud.internal.log')
        ebLogInfo("Executed test for mCleanupOneoffPluginScript()")



    @patch('exabox.core.Node.exaBoxNode.mCopyFile', return_value=None)
    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mGetDomUListFromXml', return_value=False)
    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.core.Node.exaBoxNode.mIsConnectable', return_value=True)
    def test_mCopyOneOffPatch_Success(self, _mock_mIsConnectable, _mock_mConnect, _mock_mGetDomUListFromXml, _mock_mCopyFile):

        ebLogInfo("Executing test for mCopyOneOffPatch()")
        _oneOffPluginHandler = OneOffPluginHandler(self.__patch_args_dict)
        ret = _oneOffPluginHandler.mCopyOneOffPatch('/opt/exacloud/customs/plugins/oneoff_patches/', '/opt/exacloud/customs/plugins/oneoff_logs/', 'exadataPrePostPlugins/oneoff_patch/oneoff_patch.sh', ['iad123456exdd004nat01.oraclecloud.internal'])
        self.assertEqual(ret, "0x00000000")
        ebLogInfo(f"ret = {ret}")
        ebLogInfo("Executed test for mCopyOneOffPatch()")



    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mGetDomUListFromXml', return_value=False)
    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.core.Node.exaBoxNode.mIsConnectable', return_value=True)
    def test_mCopyOneOffPatch_OneOffPatchCopyFailed(self, _mock_mIsConnectable, _mock_mConnect, _mock_mGetDomUListFromXml):

        ebLogInfo("Executing test for mCopyOneOffPatch()")
        _oneOffPluginHandler = OneOffPluginHandler(self.__patch_args_dict)
        ret = _oneOffPluginHandler.mCopyOneOffPatch('/opt/exacloud/customs/plugins/oneoff_patches/', '/opt/exacloud/customs/plugins/oneoff_logs/', 'exadataPrePostPlugins/oneoff_patch/oneoff_patch.sh', ['iad123456exdd004nat01.oraclecloud.internal'])
        self.assertEqual(ret, "0x030D0008")
        ebLogInfo(f"ret = {ret}")
        ebLogInfo("Executed test for mCopyOneOffPatch()")



    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mGetDomUListFromXml', return_value=False)
    @patch('exabox.core.Node.exaBoxNode.mConnect')
    def test_mCopyOneOffPatch_OneoffApplyFailed(self, _mock_mConnect, _mock_mGetDomUListFromXml):

        ebLogInfo("Executing test for mCopyOneOffPatch()")
        _oneOffPluginHandler = OneOffPluginHandler(self.__patch_args_dict)
        ret = _oneOffPluginHandler.mCopyOneOffPatch('/opt/exacloud/customs/plugins/oneoff_patches/', '/opt/exacloud/customs/plugins/oneoff_logs/', 'exadataPrePostPlugins/oneoff_patch/oneoff_patch.sh', ['iad123456exdd004nat01.oraclecloud.internal'])
        self.assertEqual(ret, "0x030D0000")
        ebLogInfo(f"ret = {ret}")
        ebLogInfo("Executed test for mCopyOneOffPatch()")

    def mCreateExacloudPluginHandler(self, aPluginTypes='none', aIsExaCC=False,
                                     aAutonomousVMList=None):
        _handler = ExacloudPluginHandler.__new__(ExacloudPluginHandler)
        _handler.mPatchLogInfo = MagicMock()
        _handler.mGetExacloudPluginConsoleExecutionTimeoutInSeconds = MagicMock(return_value=6)
        _handler.mGetExadataPatchmgrConsoleReadTimeoutSec = MagicMock(return_value=82800)
        _handler.mGetPluginConsoleReadCustomTimeoutSec = MagicMock(return_value=3)
        _handler.mGetTargetTypes = MagicMock(return_value=[PATCH_DOMU])
        _handler.mGetUserDetailsBasedOnDomUhostnameToRunPlugins = MagicMock(return_value='root')
        _handler.mGetAutonomousVMListWithCustomerHostnames = MagicMock(return_value=[])
        _handler.mGetAutonomousVMList = MagicMock(return_value=aAutonomousVMList or [])
        _handler.mGetPluginTypes = MagicMock(return_value=aPluginTypes)
        _handler.mIsExaCC = MagicMock(return_value=aIsExaCC)
        _handler.mGetDomUCustomerNameforDomuNatHostName = MagicMock(return_value=None)
        _handler.mAddError = MagicMock()
        return _handler

    @patch('exabox.infrapatching.handlers.generichandler.mGetInfraPatchingConfigParam')
    def test_mGetExacloudPluginConsoleExecutionTimeoutInSeconds_ReadsConfigKey(
            self, _mock_mGetInfraPatchingConfigParam):

        ebLogInfo("Executing test for mGetExacloudPluginConsoleExecutionTimeoutInSeconds")
        _mock_mGetInfraPatchingConfigParam.return_value = '82800'
        _genericHandler = GenericHandler.__new__(GenericHandler)

        _timeout = _genericHandler.mGetExacloudPluginConsoleExecutionTimeoutInSeconds()

        self.assertEqual(_timeout, 82800)
        _mock_mGetInfraPatchingConfigParam.assert_called_once_with(
            'exacloud_plugin_console_execution_timeout_in_seconds')
        ebLogInfo("Executed test for mGetExacloudPluginConsoleExecutionTimeoutInSeconds")

    @patch('exabox.infrapatching.handlers.pluginHandler.pluginhandler.sleep', return_value=None)
    @patch('exabox.infrapatching.handlers.pluginHandler.pluginhandler.exaBoxNode')
    @patch('exabox.infrapatching.handlers.pluginHandler.pluginhandler.connect_to_host')
    def test_mReadPluginScriptConsoleOut_UsesPluginSpecificTimeout(self, _mock_connect_to_host,
                                                                   _mock_exaBoxNode, _mock_sleep):

        ebLogInfo("Executing test for mReadPluginScriptConsoleOut plugin timeout")
        _node = MagicMock()
        _node.mExecuteCmd.return_value = (None, MagicMock(readlines=lambda: []), None)
        _node.mGetCmdExitStatus.return_value = 1
        _mock_connect_to_host.return_value.__enter__.return_value = _node

        _exacloudPluginHandler = self.mCreateExacloudPluginHandler()

        _exacloudPluginHandler.mReadPluginScriptConsoleOut(
            'iad123456exdd004nat01.oraclecloud.internal',
            '/tmp/plugin_pre_patch_console.out',
            PATCH_DOMU)

        _exacloudPluginHandler.mGetExacloudPluginConsoleExecutionTimeoutInSeconds.assert_called_once()
        _exacloudPluginHandler.mGetExadataPatchmgrConsoleReadTimeoutSec.assert_not_called()
        self.assertEqual(_node.mExecuteCmd.call_count, 2)
        ebLogInfo("Executed test for mReadPluginScriptConsoleOut plugin timeout")

    @patch('exabox.infrapatching.handlers.pluginHandler.pluginhandler.sleep', return_value=None)
    @patch('exabox.infrapatching.handlers.pluginHandler.pluginhandler.exaBoxNode')
    @patch('exabox.infrapatching.handlers.pluginHandler.pluginhandler.connect_to_host')
    def test_mReadPluginScriptConsoleOut_KeepsAdbCcCustomTimeout(self, _mock_connect_to_host,
                                                                 _mock_exaBoxNode, _mock_sleep):

        ebLogInfo("Executing test for mReadPluginScriptConsoleOut ADB CC custom timeout")
        _node_name = 'iad123456exdd004nat01.oraclecloud.internal'
        _node = MagicMock()
        _node.mExecuteCmd.return_value = (None, MagicMock(readlines=lambda: []), None)
        _node.mGetCmdExitStatus.return_value = 1
        _mock_connect_to_host.return_value.__enter__.return_value = _node

        _exacloudPluginHandler = self.mCreateExacloudPluginHandler(
            aPluginTypes='domu',
            aIsExaCC=True,
            aAutonomousVMList=[('dom0', [_node_name])])

        _exacloudPluginHandler.mReadPluginScriptConsoleOut(
            _node_name,
            '/tmp/plugin_pre_patch_console.out',
            PATCH_DOMU)

        _exacloudPluginHandler.mGetExacloudPluginConsoleExecutionTimeoutInSeconds.assert_called_once()
        _exacloudPluginHandler.mGetPluginConsoleReadCustomTimeoutSec.assert_called_once()
        self.assertEqual(_node.mExecuteCmd.call_count, 1)
        ebLogInfo("Executed test for mReadPluginScriptConsoleOut ADB CC custom timeout")

if __name__ == "__main__":
    unittest.main()
