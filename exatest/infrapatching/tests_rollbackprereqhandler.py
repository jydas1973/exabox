#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/infrapatching/tests_rollbackprereqhandler.py /main/1 2025/03/14 04:03:37 avimonda Exp $
#
# tests_rollbackprereqhandler.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_rollbackprereqhandler.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    avimonda    03/03/25 - Bug 37541893 - EXACS |DOM0 ROLLBACK | FAILED (NOT
#                           SUPPORTED)
#    avimonda    03/04/25 - Createfile
#    avimonda    03/04/25 - Creation
#
import unittest
import io
from unittest.mock import patch, mock_open, MagicMock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.proxy.ebProxyJobRequest import ebProxyJobRequest
from exabox.utils.node import exaBoxNode
from exabox.infrapatching.handlers.taskHandler.rollbackprereqhandler  import RollbackPreReqHandler
from exabox.core.MockCommand import exaMockCommand

class ebTestTargetHandler(ebTestClucontrol):
    SUCCESS_ERROR_CODE = '0x00000000'

    @classmethod
    def setUpClass(self):
        ebLogInfo('Starting classSetUp RollbackPreReqHandler')
        super(ebTestTargetHandler, self).setUpClass(aGenerateDatabase=True)
        self.mGetClubox(self).mGetCtx().mSetConfigOption('repository_root', self.mGetPath(self))
        _cluCtrl = self.mGetClubox(self)
        _cluCtrl._exaBoxCluCtrl__kvm_enabled = True
        self.__patch_args_dict = {'CluControl': _cluCtrl,
                                'LocalLogFile': 'exabox/exatest/infrapatching/resources/patchmgr_logs',
                                'TargetType': ['dom0'], 'Operation': 'self.__patch_args_dict = ', 'OperationStyle': 'rolling',
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
        ebLogInfo('Ending classSetUp RollbackPreReqHandler')


    def test_mExecute_Dom0(self):

        ebLogInfo(" ")
        ebLogInfo("Running unit test for Dom0 on RollbackPreReqHandler.mExecute")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.__patch_args_dict['TargetType'] = ["dom0"]
        _rollbackPreReqHandler = RollbackPreReqHandler(self.__patch_args_dict)
        _ret = _rollbackPreReqHandler.mExecute()
        self.assertEqual(_ret, "0x0301006B")

        ebLogInfo("Unit test for Dom0 on RollbackPreReqHandler.mExecute executed successfully")

    def test_mExecute_DomU(self):

        ebLogInfo(" ")
        ebLogInfo("Running unit test for DomU on RollbackPreReqHandler.mExecute")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.__patch_args_dict['TargetType'] = ["domu"]
        _rollbackPreReqHandler = RollbackPreReqHandler(self.__patch_args_dict)
        _ret = _rollbackPreReqHandler.mExecute()
        self.assertEqual(_ret, "0x0301006B")

        ebLogInfo("Unit test for DomU on RollbackPreReqHandler.mExecute executed successfully")

    @patch('exabox.infrapatching.utils.utility.getTargetHandlerInstance', return_value="tahertHandler")
    @patch('exabox.infrapatching.handlers.targetHandler.cellhandler.CellHandler.mRollBackPreCheck', return_value=('0x00000000', 0))
    def test_mExecute_CELL(self, _mock_getTargetHandlerInstance, mock_mRollBackPreCheck):

        ebLogInfo(" ")
        ebLogInfo("Running unit test for CELL on RollbackPreReqHandler.mExecute")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.__patch_args_dict['TargetType'] = ["cell"]
        _rollbackPreReqHandler = RollbackPreReqHandler(self.__patch_args_dict)
        _ret = _rollbackPreReqHandler.mExecute()
        self.assertEqual(_ret, "0x00000000")

        ebLogInfo("Unit test for CELL on RollbackPreReqHandler.mExecute executed successfully")

if __name__ == "__main__":
    unittest.main() 
