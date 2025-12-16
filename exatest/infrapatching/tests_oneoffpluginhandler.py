#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/infrapatching/tests_oneoffpluginhandler.py /main/1 2025/02/14 17:58:04 avimonda Exp $
#
# tests_oneoffpluginhandler.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
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
from exabox.infrapatching.handlers.generichandler import GenericHandler
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

if __name__ == "__main__":
    unittest.main()
