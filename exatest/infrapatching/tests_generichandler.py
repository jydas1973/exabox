#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/infrapatching/tests_generichandler.py /main/3 2025/10/09 17:01:05 avimonda Exp $
#
# tests_generichandler.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_generichandler.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    avimonda    09/19/25 - Bug 38324744 - EXACC GEN 2 | PATCHING | SSHD
#                           TIMEOUT ERRORS MISINTERPRETED AS SSHD NOT RUNNING
#    avimonda    07/12/25 - Bug 37934568 - AIM4ECS:0X0301000A - INDIVIDUAL
#                           PATCH REQUEST EXCEPTION DETECTED
#    avimonda    04/24/25 - Bug 37795564 - AIM4ECS:0X030B0010 - EXCEPTION
#                           ENCOUNTERED WHILE READING PLUGIN CONSOLE LOGS ON
#                           DOMU. REFER MOS NOTE 2829056.1 FOR MORE DETAILS.
#    avimonda    04/24/25 - Createfile
#    avimonda    04/24/25 - Creation
#
import unittest
import io
import errno
from unittest.mock import patch, mock_open, MagicMock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.proxy.ebProxyJobRequest import ebProxyJobRequest
from exabox.utils.node import exaBoxNode
from exabox.infrapatching.handlers.generichandler import GenericHandler
from exabox.core.MockCommand import exaMockCommand
import sys, os
sys.path.append(os.path.abspath(".."))

class ebTestGenericHandler(ebTestClucontrol):
    SUCCESS_ERROR_CODE = "0x00000000"

    @classmethod
    def setUpClass(self):
        ebLogInfo("Starting classSetUp GenericHandler")
        super(ebTestGenericHandler, self).setUpClass(aGenerateDatabase=True)
        _cluCtrl = self.mGetClubox(self)
        _cluCtrl._exaBoxCluCtrl__kvm_enabled = True
        self.__patch_args_dict = {'CluControl': _cluCtrl,
                                'LocalLogFile': 'exabox/exatest/infrapatching/resources/patchmgr_logs',
                                'TargetType': ['dom0'], 'Operation': 'patch_prereq_check', 'OperationStyle': 'rolling',
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


    @patch('exabox.infrapatching.handlers.generichandler.json.loads')
    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mGetExadataPatchGridHeartBeatTimeoutSec', return_value=300)
    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mGetExadataPatchWorkingSpaceMB', return_value=500)
    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mIsSingleWorkerRequest', return_value=True)
    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mConvertExasplice')
    def test_mGetErrorCodeFromChildRequest_True(self, _mock_mConvertExasplice, _mock_mIsSingleWorkerRequest, _mock_mGetExadataPatchWorkingSpaceMB, _mock_mGetExadataPatchGridHeartBeatTimeoutSec, _mock_json_loads):
        ebLogInfo("")
        ebLogInfo("Running unit test on GenericHandler.mGetErrorCodeFromChildRequest_True")

        _mock_json_loads.return_value = {'data': {'httpRequestId': 'ddd1ca8224ed49fe81f15cab5f7a0f8b', 'recipients': [{'channelType': 'topics'}], 'notificationType': {'componentId': 'Patch_ExadataInfra_SM', 'id': 'Patch_ExadataInfra_SMnotification_v1'}, 'service': 'ExadataPatch', 'component': 'Patch Exadata Infrastructure', 'subject': 'Patch Exadata Infrastructure Service Update', 'event_post_time': '2025-04-24:18.53.23 ', 'log_dir': '/EXAVMIMAGES/23.1.15.0.0.240614.patch.zip/patch_23.1.15.0.0.240614/patchmgr_log_83a40cec-5412-442d-b29b-40878197ac78', 'oeda_requests_log_path': '/scratch/avimonda/ecra_installs/ecsprod/mw_home/user_projects/domains/exacloud/oeda/requests/0000-0000-0000-0000_49ef074c-213d-11f0-9d00-0200170e7c2a/log/patchmgr_logs', 'cluster_name': 'X8mclu1', 'exadata_rack': 'X8mclu1', 'target_type': ['cell'], 'operation_type': 'patch_prereq_check', 'operation_style': 'rolling', 'target_version': '23.1.15.0.0.240614', 'cluster_less': 'no', 'exaunit_id': 5, 'exa_ocid': None, 'exa_splice': 'no', 'topic': '', 'error_code': '0x03010055', 'error_message': 'Node connect failed. Validate connectivity and authentication before retrying infra patch operations.', 'error_detail': "Connect to Node : ['scaqan10adm07.us.oracle.com', 'scaqan10adm08.us.oracle.com'] failed with Error : [Errno 110] Connection timed out", 'error_action': 'FAIL_DONTSHOW_PAGE_ONCALL', 'node_progressing_status': {}, 'child_request_uuid': '49ef074c-213d-11f0-9d00-0200170e7c2a', 'master_request_uuid': '45584824-213d-11f0-9d00-0200170e7c2a'}}

        _gh = GenericHandler(self.__patch_args_dict)
        _er, _ret = _gh.mGetErrorCodeFromChildRequest()
        self.assertEqual(_er, '0x03010055')
        self.assertEqual(_ret, True)
        ebLogInfo(f"_er = {_er}, _ret = {_ret}")
        ebLogInfo("Unit test on GenericHandler.mGetErrorCodeFromChildRequest_True executed successfully")

        
    @patch('exabox.infrapatching.handlers.generichandler.json.loads')
    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mGetExadataPatchGridHeartBeatTimeoutSec', return_value=300)
    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mGetExadataPatchWorkingSpaceMB', return_value=500)
    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mIsSingleWorkerRequest', return_value=True)
    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mConvertExasplice')
    def test_mGetErrorCodeFromChildRequest_False(self, _mock_mConvertExasplice, _mock_mIsSingleWorkerRequest, _mock_mGetExadataPatchWorkingSpaceMB, _mock_mGetExadataPatchGridHeartBeatTimeoutSec, _mock_json_loads):
        ebLogInfo("")
        ebLogInfo("Running unit test on GenericHandler.mGetErrorCodeFromChildRequest_False")

        _mock_json_loads.return_value = {'data': {'httpRequestId': 'ddd1ca8224ed49fe81f15cab5f7a0f8b'}}

        _gh = GenericHandler(self.__patch_args_dict)
        _er, _ret = _gh.mGetErrorCodeFromChildRequest()
        self.assertEqual(_er, '0x00000000')
        self.assertEqual(_ret, False)
        ebLogInfo("Unit test on GenericHandler.mGetErrorCodeFromChildRequest_False executed successfully")
        

    def test_mReturnBothDomUNATCustomerHostNames(self):

        ebLogInfo("")
        ebLogInfo("Running unit test on GenericHandler.mReturnBothDomUNATCustomerHostNames")
        _gh = GenericHandler(self.__patch_args_dict)
        _list = _gh.mReturnBothDomUNATCustomerHostNames(['ora12db01.oradb.in.cloud.com'])
        self.assertEqual([('Nat Hostname :iad123456exdd001nat01.oraclecloud.internal', 'Customer Hostname :ora12db01.oradb.in.cloud.com')], _list)
        ebLogInfo("Unit test on GenericHandler.mReturnBothDomUNATCustomerHostNames executed successfully")

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckSshd', return_value=False)
    def test_mGetSshdNotRunningNodeList(self, aMock_mCheckSshd):
        ebLogInfo("")
        ebLogInfo("Running unit test on GenericHandler.mGetSshdNotRunningNodeList")

        _node_list = ["node1.oracle.us.com", "node2.oracle.us.com"]
        _gh = GenericHandler(self.__patch_args_dict)
        _result_code, _result_nodes = _gh.mGetSshdNotRunningNodeList(_node_list)
        self.assertCountEqual(_result_nodes, _node_list)

        ebLogInfo("Unit test on GenericHandler.mGetSshdNotRunningNodeList executed successfully")

    @patch('socket.socket')
    def test_mCheckPortSSH(self, mock_socket):
        ebLogInfo("")
        ebLogInfo("Running unit test on exaBoxNode.mCheckPortSSH")

        mock_ctx = MagicMock()
        node = exaBoxNode(mock_ctx)
        host = "node1.oracle.us.com"
        timeout = 10

        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.connect_ex.return_value = 0
        result = node.mCheckPortSSH(host, timeout)
        self.assertTrue(result)

        mock_sock_instance.settimeout.assert_called_with(timeout)

        mock_sock_instance.connect_ex.return_value = errno.ECONNREFUSED
        result = node.mCheckPortSSH(host, timeout)
        self.assertFalse(result)

        mock_sock_instance.connect_ex.return_value = errno.ETIMEDOUT
        result = node.mCheckPortSSH(host, timeout)
        self.assertFalse(result)

        mock_sock_instance.connect_ex.side_effect = Exception("Connection error")
        result = node.mCheckPortSSH(host, timeout)
        self.assertFalse(result)

        ebLogInfo("Unit test on exaBoxNode.mCheckPortSSH executed successfully")

if __name__ == "__main__":
    unittest.main()
