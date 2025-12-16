#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/infrapatching/tests_targethandler.py /main/16 2025/10/09 17:03:44 avimonda Exp $
#
# tests_targethandler.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_targethandler.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    avimonda    10/07/25 - Bug 38475354 - AIM4ECS:0X03050015 - PATCHMGR
#                           SESSION ON VM ALREADY EXISTS. REFER MOS NOTE
#                           2829056.1 FOR MORE DETAILS
#    nelango     08/29/25 - Bug 38299928: Postpone restore SSH keys after
#                           cleanup and validation are complete
#    avimonda    07/28/25 - Bug 38177025 - GUEST OS PATCHING FAILED WITH ERROR
#                           INDIVIDUAL PATCH REQUEST DURING PRECHECK EXCEPTION
#                           DETECTED ON VM
#    remamid     06/10/25 - Add unittest for bug 37878442
#    remamid     06/24/25 - Unittest for bug 37916448
#    avimonda    05/19/25 - Bug 37962294 - 25.1.4.0.0.250512 - PRE-CHECK FAILED
#                           BECAUSE OF ALERT.CHASSIS.FW.FPGA-UPGRADE-BLOCKED -
#                           IGNORED ALERT
#    avimonda    05/14/25 - Bug 37877715 - EXACS: DOMU OS PATCHING FAILED WITH
#                           NO ERROR MESSAGES OR LOGS AT VM END
#    nelango     01/28/25 - Bug 37328906: ipmi servicestate checks during
#                           precheck
#    avimonda    01/11/25 - Bug 37232903 - AIM4ECS:0X03010010 - TASK HANDLER
#                           PATCH REQUEST EXCEPTION DETECTED.
#    avimonda    11/26/24 - Enhancement Request 37232972 - EXACC GEN 2| PATCHING
#                           | OPTIMIZE DOMU CONNECTION TIMEOUT TO REDUCE FAILED
#                           PRE-CHECK TIME FROM 41 MINUTES TO A CONFIGURABLE
#                           THRESHOLD (E.G., 5-10 MINUTES)
#    avimonda    07/23/24 - Bug 36563684 - AIM4EXACLOUD:0X03040001 - VM PRECHECK
#                           EXCEPTION DETECTED. (23.4.1.2.1-DOMU)
#    avimonda    07/16/24 - Bug 36563675: Add more unit tests for
#                           mCheckHwCriticalAlert 
#    araghave    07/15/24 - Enh 36830077 - CLEANUP KSPLICE CODE FROM
#                           INFRAPATCHING FILES
#    avimonda    04/29/24 - Bug 36555012: Add unit tests for
#                           mCheckHwCriticalAlert 
#    avimonda    02/14/24 - Bug 36238752: PRECHECK FAILURE - UNABLE TO LOCATE
#                           PATCHMGR SCRIPT ON THE LAUNCH NODE | ERROR CODE
#                           0X0301003A
#    avimonda    02/14/24 - Creation
#
import unittest
import io
from unittest.mock import patch, mock_open, MagicMock 
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.proxy.ebProxyJobRequest import ebProxyJobRequest
from exabox.utils.node import exaBoxNode
from exabox.infrapatching.handlers.targetHandler.targethandler import TargetHandler
from exabox.core.MockCommand import exaMockCommand
from paramiko.ssh_exception import SSHException
from exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler import InfraPatchManager

PATCH_DIR_1 = io.StringIO("/EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_22.1.17.0.0.231109.1_Linux-x86-64.zip/dbserver_patch_231023\n/EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_22.1.17.0.0.231109.1_Linux-x86-64.zip/dbserver_patch_231115")
PATCH_DIR_2 = io.StringIO("/EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_22.1.17.0.0.231109.1_Linux-x86-64.zip/dbserver_patch_231003\n/EXAVMIMAGES/dbserver.patch.zip_exadata_ol7_22.1.17.0.0.231109.1_Linux-x86-64.zip/dbserver_patch_231115")
IMAGE_INFO_STATUS_NONE_CELL = io.StringIO(" ")
IMAGE_INFO_STATUS_EMPTY_OR_INVALID = "0x03010066"
ALERT_NONE = io.StringIO("")
ALERT_NONE_DOMU = io.StringIO("")
ALERT_OUTPUT_CELL = io.StringIO('\t 35_1\t 2024-01-18T23:52:31+00:00\t critical\t "A fault occurred.  Fault class    : fault.memory.intel.dimm_ue  Fault message  : http://support.oracle.com/msg/SPX86A-8002-Y8"\n')
ALERT_OUTPUT_DOM0 = io.StringIO('\t 35_1\t 2024-01-18T23:52:31+00:00\t critical\t "A fault occurred.  Fault class    : fault.memory.intel.dimm_ue  Fault message  : http://support.oracle.com/msg/SPX86A-8002-Y8"\n')

class mockFileHandler():

    def __init__(self, fileoutput=None):
        self.terminal_op = fileoutput

    def read(self):
        return self.terminal_op

    def readlines(self):
        return self.terminal_op.readlines()

class ebTestTargetHandler(ebTestClucontrol):
    SUCCESS_ERROR_CODE = "0x00000000"

    @classmethod
    def setUpClass(self):
        ebLogInfo("Starting classSetUp TargetHandler")
        super(ebTestTargetHandler, self).setUpClass(aGenerateDatabase=True)
        self.mGetClubox(self).mGetCtx().mSetConfigOption("repository_root", self.mGetPath(self))
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
        ebLogInfo("Ending classSetUp TargetHandler")

    def test_mVerifyAndCleanupMissingPatchmgrRemotePatchBase1(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on TargetHandler.mVerifyAndCleanupMissingPatchmgrRemotePatchBase")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _targetHandler = TargetHandler(self.__patch_args_dict)
        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, mockFileHandler(PATCH_DIR_1), mockFileHandler())) as _mock_mExecuteCmd,\
             patch('exabox.core.Node.exaBoxNode.mGetCmdExitStatus', return_value=0):
            _targetHandler.mVerifyAndCleanupMissingPatchmgrRemotePatchBase("/EXAVMIMAGES/dbservero.patch.zip_exadata_ol7_22.1.17.0.0.231109.1_Linux-x86-64.zip", ['scaqan10adm07.us.oracle.com', 'scaqan10adm08.us.oracle.com'])
            self.assertEqual(_mock_mExecuteCmd.call_count, 7)
        ebLogInfo("Unit test on TargetHandler.mVerifyAndCleanupMissingPatchmgrRemotePatchBase executed successfully")



    def test_mVerifyAndCleanupMissingPatchmgrRemotePatchBase2(self):
        ebLogInfo(" ")
        ebLogInfo("Running unit test on TargetHandler.mVerifyAndCleanupMissingPatchmgrRemotePatchBase")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _mock_mGetCmdExitStatus_Val = [0,0,1]    
        _targetHandler = TargetHandler(self.__patch_args_dict)
        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, mockFileHandler(PATCH_DIR_2), mockFileHandler())) as _mock_mExecuteCmd,\
             patch('exabox.core.Node.exaBoxNode.mGetCmdExitStatus', side_effect= _mock_mGetCmdExitStatus_Val):
            _targetHandler.mVerifyAndCleanupMissingPatchmgrRemotePatchBase("/EXAVMIMAGES/dbservero.patch.zip_exadata_ol7_22.1.17.0.0.231109.1_Linux-x86-64.zip", ['scaqan10adm07.us.oracle.com'])
            self.assertEqual(_mock_mExecuteCmd.call_count, 4)

        ebLogInfo("Unit test on TargetHandler.mVerifyAndCleanupMissingPatchmgrRemotePatchBase executed successfully")

    @patch('exabox.core.Node.exaBoxNode.mFileExists')
    def test_mVerifyAndCleanupMissingPatchmgrRemotePatchBase3(self, _mock_mFileExists):
        ebLogInfo(" ")
        ebLogInfo("Running unit test on TargetHandler.mVerifyAndCleanupMissingPatchmgrRemotePatchBase")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)

        _mock_mFileExists.side_effect=SSHException("Channel closed")

        _targetHandler = TargetHandler(self.__patch_args_dict)
        with self.assertRaises(Exception) as context:
            _targetHandler.mVerifyAndCleanupMissingPatchmgrRemotePatchBase("/EXAVMIMAGES/dbservero.patch.zip_exadata_ol7_22.1.17.0.0.231109.1_Linux-x86-64.zip", ['scaqan10adm07.us.oracle.com'])
        self.assertEqual(str(context.exception), "Unable to verify and cleanup missing patchmgr remote patch base on Node : [scaqan10adm07.us.oracle.com]. Error : Channel closed")
        _mock_mFileExists.assert_called_once()

        ebLogInfo("Unit test on TargetHandler.mVerifyAndCleanupMissingPatchmgrRemotePatchBase executed successfully")

    @patch('exabox.core.Node.exaBoxNode.mConnect')
    def test_mCleanupExadataPatches_Connection_Timeout(self, _mock_mConnect):
        ebLogInfo(" ")
        ebLogInfo("Running unit test on TargetHandler.mCleanupExadataPatches")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _mock_mConnect.side_effect = TimeoutError("[Errno 110] Connection timed out")
        _targetHandler = TargetHandler(self.__patch_args_dict)
        _ret_stats = _targetHandler.mCleanupExadataPatches(['scaqan10adm07.us.oracle.com', 'scaqan10adm08.us.oracle.com'])
        for _ret, _errmsg in _ret_stats.items():
            self.assertEqual(_ret, "0x03010055") 
        ebLogInfo("Unit test on TargetHandler.mCleanupExadataPatches executed successfully")

    def test_mCheckAndUpdateNodeList(self):

        ebLogInfo("")
        ebLogInfo("Running unit test on CellHandler.mCheckAndUpdateCellListPostPatchFailure")
        _cell_list = ["slcs27celadm04.us.oracle.com", "slcs27celadm05.us.oracle.com", "slcs27celadm06.us.oracle.com"]
        _partial_cell_list = ["slcs27celadm04.us.oracle.com", "slcs27celadm06.us.oracle.com"]
        _base_dir = " /EXAVMIMAGES/23.1.3.0.0.230613.patch.zip/patch_23.1.3.0.0.230613/"
        _dom0 = "scaqan10adm07.us.oracle.com"
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com")
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        _targetHandler = TargetHandler(self.__patch_args_dict)
        with patch('exabox.ovm.clucontrol.exaBoxNode.mIsConnectable', return_value=True):
            _input_list = _targetHandler.mCheckAndUpdateNodeList(_cell_list)
            self.assertEqual(_input_list, _cell_list)

        with patch('exabox.ovm.clucontrol.exaBoxNode.mIsConnectable', side_effect=[True, False, True]):
            _input_list = _targetHandler.mCheckAndUpdateNodeList(_cell_list)
            self.assertEqual(_input_list, _partial_cell_list)

        with patch('exabox.ovm.clucontrol.exaBoxNode.mIsConnectable', return_value=False, aPersist=False):
            _input_list = _targetHandler.mCheckAndUpdateNodeList(["slcs27celadm05.us.oracle.com"])
            self.assertEqual(_input_list, [])

        ebLogInfo("Unit test on CellHandler.mCheckAndUpdateCellListPostPatchFailure succeeded.")
        ebLogInfo("")                                                                                                                                                                                              

    def test_mCheckHwCriticalAlert_CELL(self):
        ebLogInfo(" ")
        ebLogInfo("Running unit test on TargetHandler.mCheckHwCriticalAlert for CELL")
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e list cell |awk '{print $1}'", aStdout="iad123456exdcl02.oraclecloud.internal", aPersist=True),
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        self.__patch_args_dict['TargetType'] = ["cell"] 
        _targetHandler = TargetHandler(self.__patch_args_dict)
        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', side_effect=[(None, mockFileHandler(io.StringIO("25.1.14.0.0.240509")), mockFileHandler()) , (None, mockFileHandler(ALERT_OUTPUT_CELL), mockFileHandler())]):
            _hw_alert_flag, _hw_alert_details, _MS_down_nodes = _targetHandler.mCheckHwCriticalAlert("cell", ['iad123456exdcl02.oraclecloud.internal'])
            ebLogInfo(f'_hw_alert_flag={_hw_alert_flag}, _hw_alert_details= {_hw_alert_details}, _MS_down_nodes = {_MS_down_nodes}')
            self.assertTrue(_hw_alert_flag, "_hw_alert_flag should be True")
            self.assertEqual(_MS_down_nodes, [], "_MS_down_nodes should be an empty list")
            self.assertEqual(_hw_alert_details, {'iad123456exdcl02.oraclecloud.internal': ['"A fault occurred.  Fault class    '
                                           ': fault.memory.intel.dimm_ue  '
                                           'Fault message  : '
                                           'http://support.oracle.com/msg/SPX86A-8002-Y8"']}, "_hw_alert_details should not be an empty dictionary")

        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', side_effect=[(None, mockFileHandler(io.StringIO("25.1.14.0.0.240509")), mockFileHandler()) , (None, mockFileHandler(ALERT_NONE), mockFileHandler())]):
            _hw_alert_flag, _hw_alert_details, _MS_down_nodes = _targetHandler.mCheckHwCriticalAlert("cell", ['iad123456exdcl02.oraclecloud.internal'])
            ebLogInfo(f'_hw_alert_flag={_hw_alert_flag}, _hw_alert_details= {_hw_alert_details}, _MS_down_nodes = {_MS_down_nodes}')
            self.assertFalse(_hw_alert_flag, "_hw_alert_flag should be False")
            self.assertEqual(_MS_down_nodes, [], "_MS_down_nodes should be an empty list")
            self.assertEqual(_hw_alert_details, {}, "_hw_alert_details be an empty dictionary")

        ebLogInfo("Unit test on TargetHandler.mCheckHwCriticalAlert for CELL executed successfully")

    def test_mCheckHwCriticalAlert_DOM0(self):
        ebLogInfo(" ")
        ebLogInfo("Running unit test on TargetHandler.mCheckHwCriticalAlert for DOM0")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com", aPersist=True),
                ],
            ],
        }
        self.mPrepareMockCommands(_cmds)

        _targetHandler = TargetHandler(self.__patch_args_dict)

        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', side_effect=[(None, mockFileHandler(io.StringIO("25.1.14.0.0.240509")), mockFileHandler()) , (None, mockFileHandler(ALERT_OUTPUT_DOM0), mockFileHandler())]):
            _hw_alert_flag, _hw_alert_details, _MS_down_nodes = _targetHandler.mCheckHwCriticalAlert("dom0", ['iad123456exdd001.oraclecloud.internal'])
            ebLogInfo(f'_hw_alert_flag={_hw_alert_flag}, _hw_alert_details= {_hw_alert_details}, _MS_down_nodes = {_MS_down_nodes}')
            self.assertTrue(_hw_alert_flag, "_hw_alert_flag should be True")
            self.assertEqual(_MS_down_nodes, [], "_MS_down_nodes should be an empty list")
            self.assertEqual(_hw_alert_details, {'iad123456exdd001.oraclecloud.internal': ['"A fault occurred.  Fault class    '
                                           ': fault.memory.intel.dimm_ue  '
                                           'Fault message  : '
                                           'http://support.oracle.com/msg/SPX86A-8002-Y8"']}, "_hw_alert_details should not be an empty dictionary")

        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', side_effect=[(None, mockFileHandler(io.StringIO("25.1.14.0.0.240509")), mockFileHandler()) , (None, mockFileHandler(ALERT_NONE), mockFileHandler())]):
            _hw_alert_flag, _hw_alert_details, _MS_down_nodes = _targetHandler.mCheckHwCriticalAlert("dom0", ['iad123456exdd001.oraclecloud.internal'])
            ebLogInfo(f'_hw_alert_flag={_hw_alert_flag}, _hw_alert_details= {_hw_alert_details}, _MS_down_nodes = {_MS_down_nodes}')
            self.assertFalse(_hw_alert_flag, "_hw_alert_flag should be False")
            self.assertEqual(_MS_down_nodes, [], "_MS_down_nodes should be an empty list")
            self.assertEqual(_hw_alert_details, {}, "_hw_alert_details be an empty dictionary")

        ebLogInfo("Unit test on TargetHandler.mCheckHwCriticalAlert for DOM0 executed successfully")
        
    def test_mCheckHwCriticalAlert_DOMU(self):
        ebLogInfo(" ")
        ebLogInfo("Running unit test on TargetHandler.mCheckHwCriticalAlert for DOMU")
        for dom0, domU in self.mGetClubox().mReturnDom0DomUPair():
            _cmds = {
                self.mGetRegexDomU(): [
                    [
                        exaMockCommand("/sbin/arping", aRc=0 if domU == "iad123456exdd001nat01.oraclecloud.internal" else 1, aPersist=True),
                    ]
                ]
            }
        self.mPrepareMockCommands(_cmds)
        self.__patch_args_dict['TargetType'] = ["domu"] 
        _targetHandler = TargetHandler(self.__patch_args_dict)

        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd', side_effect=[(None, mockFileHandler(io.StringIO("25.1.14.0.0.240509")), mockFileHandler()) , (None, mockFileHandler(ALERT_NONE_DOMU), mockFileHandler())]):
            _hw_alert_flag, _hw_alert_details, _MS_down_nodes = _targetHandler.mCheckHwCriticalAlert("domu", ['iad123456exdd001nat01.oraclecloud.internal'])
            self.assertFalse(_hw_alert_flag, "_hw_alert_flag should be False")
            self.assertEqual(_MS_down_nodes, [], "_MS_down_nodes should be an empty list")
            self.assertEqual(_hw_alert_details, {}, "_hw_alert_details be an empty dictionary")
        ebLogInfo("Unit test on TargetHandler.mCheckHwCriticalAlert for DOMU executed successfully")

    def test_mFilterNodesToPatch_DOM0(self):
        ebLogInfo(" ")
        ebLogInfo("Running unit test on TargetHandler.mFilterNodesToPatch for Dom0")
        _task_list = [ 
            (io.StringIO(" "), "patch_prereq_check", IMAGE_INFO_STATUS_EMPTY_OR_INVALID),
            (io.StringIO(" "), "patch", IMAGE_INFO_STATUS_EMPTY_OR_INVALID),
            (io.StringIO("success"), "rollback_prereq_check", "0x00000000"),
            (io.StringIO("success"), "rollback", "0x00000000"),
            (io.StringIO(" "), "backup_image", IMAGE_INFO_STATUS_EMPTY_OR_INVALID) 
            ]

        for _image_info, _task, _expected_output in _task_list:
            _cmds = {
                self.mGetRegexDom0(): [
                    [
                        exaMockCommand("virsh", aStdout="iad123456exdd001.oraclecloud.internal"),
                    ],
                ]
            }
            self.mPrepareMockCommands(_cmds)

            _targetHandler = TargetHandler(self.__patch_args_dict)
            with patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mCheckTargetVersion", return_value=1),\
                 patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, _image_info, mockFileHandler())) as _mock_mExecuteCmd:

                _mock_output = MagicMock()
                _mock_output.readline.return_value = mockFileHandler(_image_info)
                _mock_mExecuteCmd.return_value = (None, _image_info, mockFileHandler())

                _ret, _suggestion_msg, _list_of_nodes, _discarded = _targetHandler.mFilterNodesToPatch(['iad123456exdd001.oraclecloud.internal'], "dom0", _task)
                self.assertEqual(_ret, _expected_output) 

        ebLogInfo("Unit test on TargetHandler.mFilterNodesToPatch for Dom0 executed successfully")

    def test_mFilterNodesToPatch_DOMU(self):
        ebLogInfo(" ")
        ebLogInfo("Running unit test on TargetHandler.mFilterNodesToPatch for DomU")

        _task_list = [
            (io.StringIO(" "), "patch_prereq_check", IMAGE_INFO_STATUS_EMPTY_OR_INVALID),
            (io.StringIO(" "), "patch", IMAGE_INFO_STATUS_EMPTY_OR_INVALID),
            (io.StringIO("success"), "rollback_prereq_check", "0x00000000"),
            (io.StringIO("success"), "rollback", "0x00000000"),
            (io.StringIO(" "), "backup_image", IMAGE_INFO_STATUS_EMPTY_OR_INVALID)
            ]

        for _image_info, _task, _expected_output in _task_list:
            for dom0, domU in self.mGetClubox().mReturnDom0DomUPair():
                _cmds = {
                    self.mGetRegexDomU(): [
                        [
                            exaMockCommand("/sbin/arping", aRc=0 if domU == "iad123456exdd001nat01.oraclecloud.internal" else 1, aPersist=True)
                        ]
                    ]
                }
            self.mPrepareMockCommands(_cmds)

            self.__patch_args_dict['TargetType'] = ["domu"] 
            _targetHandler = TargetHandler(self.__patch_args_dict)

            with patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mCheckTargetVersion", return_value=1),\
                 patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, _image_info, mockFileHandler())) as _mock_mExecuteCmd:

                _mock_output = MagicMock()
                _mock_output.readline.return_value = mockFileHandler(_image_info)
                _mock_mExecuteCmd.return_value = (None, _image_info, mockFileHandler())

                _ret, _suggestion_msg, _list_of_nodes, _discarded = _targetHandler.mFilterNodesToPatch(['iad123456exdd001nat01.oraclecloud.internal'], "domu", _task)
                self.assertEqual(_ret, _expected_output)

        ebLogInfo("Unit test on TargetHandler.mFilterNodesToPatch for DomU executed successfully")

    def test_mFilterNodesToPatch_CELL(self):
        ebLogInfo(" ")
        ebLogInfo("Running unit test on TargetHandler.mFilterNodesToPatch for CELL")
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e list cell |awk '{print $1}'", aStdout="iad123456exdcl02.oraclecloud.internal", aPersist=True),
                ]
            ]
        } 
        self.mPrepareMockCommands(_cmds)

        self.__patch_args_dict['TargetType'] = ["cell"] 
        _targetHandler = TargetHandler(self.__patch_args_dict)

        with patch("exabox.infrapatching.core.clupatchhealthcheck.ebCluPatchHealthCheck.mCheckTargetVersion", return_value=1),\
             patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, IMAGE_INFO_STATUS_NONE_CELL, mockFileHandler())) as _mock_mExecuteCmd:

            _mock_output = MagicMock()
            _mock_output.readline.return_value = mockFileHandler(IMAGE_INFO_STATUS_NONE_CELL)
            _mock_mExecuteCmd.return_value = (None, IMAGE_INFO_STATUS_NONE_CELL, mockFileHandler())
                
            _ret, _suggestion_msg, _list_of_nodes, _discarded = _targetHandler.mFilterNodesToPatch(['iad123456exdcl02.oraclecloud.internal'], "cell", "patch")
            self.assertEqual(_ret, IMAGE_INFO_STATUS_EMPTY_OR_INVALID)

        ebLogInfo("Unit test on TargetHandler.mFilterNodesToPatch for CELL executed successfully")
        
    @patch("exabox.infrapatching.utils.infrapatchexecutionvalidator.InfrapatchExecutionValidator.mCheckCondition", return_value=True)
    @patch("exabox.core.Node.exaBoxNode.mExecuteCmd", return_value=(None, MagicMock(readlines=MagicMock(return_value=["Target Value: enabled"])), MagicMock(readlines=MagicMock(return_value=[]))))
    @patch("exabox.infrapatching.handlers.loghandler.LogHandler.mPatchLogInfo")
    def test_mValidateServiceStateOnIlom_CELL(self, mock_mPatchLogInfo,mock_mExecuteCmd, mock_mCheckCondition):
        ebLogInfo("Running unit test on TargetHandler.mValidateServiceStateOnIlom for CELL")
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e list cell |awk '{print $1}'", aStdout="iad123456exdcl02.oraclecloud.internal", aPersist=True),
                ]
            ]
        } 
        self.mPrepareMockCommands(_cmds)

        self.__patch_args_dict['TargetType'] = ["cell"] 
        _targetHandler = TargetHandler(self.__patch_args_dict)
        _targetHandler.mValidateServiceStateOnIlom(['iad123456exdcl02.oraclecloud.internal'])
        mock_mCheckCondition.assert_called_with('enableServiceStateOnIlomsPriorToDom0CellPatchingEnabled')
        mock_mExecuteCmd.assert_called_with("ipmitool sunoem getval /SP/services/ipmi/servicestate")
        mock_mPatchLogInfo.assert_called_with("Service State of ilom on node : iad123456exdcl02.oraclecloud.internal. output : ['Target Value: enabled'].")
        mock_mExecuteCmd.assert_called_with("ipmitool sunoem getval /SP/services/ipmi/servicestate")
        
        ebLogInfo("Unit test on TargetHandler.mValidateServiceStateOnIlom for CELL executed successfully")
        
    @patch("exabox.infrapatching.utils.infrapatchexecutionvalidator.InfrapatchExecutionValidator.mCheckCondition", return_value=True)
    @patch("exabox.core.Node.exaBoxNode.mExecuteCmd", return_value=(None, MagicMock(readlines=MagicMock(return_value=["Target Value: enabled"])), MagicMock(readlines=MagicMock(return_value=[]))))
    @patch("exabox.infrapatching.handlers.loghandler.LogHandler.mPatchLogInfo")
    def test_mValidateServiceStateOnIlom_DOM0(self, mock_mPatchLogInfo,mock_mExecuteCmd, mock_mCheckCondition):
        ebLogInfo("Running unit test on TargetHandler.mValidateServiceStateOnIlom for DOM0")        
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com", aPersist=True),
                ],
            ],
        }
        self.mPrepareMockCommands(_cmds)
        _targetHandler = TargetHandler(self.__patch_args_dict)
        _targetHandler.mValidateServiceStateOnIlom(['scaqan03dv0208.us.oracle.com'])
        mock_mCheckCondition.assert_called_with('enableServiceStateOnIlomsPriorToDom0CellPatchingEnabled')
        mock_mExecuteCmd.assert_called_with("ipmitool sunoem getval /SP/services/ipmi/servicestate")
        mock_mPatchLogInfo.assert_called_with("Service State of ilom on node : scaqan03dv0208.us.oracle.com. output : ['Target Value: enabled'].")
        mock_mExecuteCmd.assert_called_with("ipmitool sunoem getval /SP/services/ipmi/servicestate")

        ebLogInfo("Unit test on TargetHandler.mValidateServiceStateOnIlom for DOM0 executed successfully")
    
    @patch("exabox.infrapatching.utils.infrapatchexecutionvalidator.InfrapatchExecutionValidator.mIsManagementHostLaunchNodeForDomU", return_value=False)
    @patch("exabox.infrapatching.utils.infrapatchexecutionvalidator.InfrapatchExecutionValidator.mCheckCondition", return_value=False)
    @patch('exabox.core.Node.exaBoxNode.mFileExists', return_value=False)
    def test_mValidateImageCheckSum(self, mock_mFileExists, mock_mCheckCondition, mock_mIsManagementHostLaunchNodeForDomU):
        ebLogInfo("Running unit test on TargetHandler.mValidateImageCheckSum._mExecute_FileCopy")
        _PatchFile = "dbserver.patch.zip"
        _local_patch_path = "PatchPayloads/24.1.7.0.0.241204/DBPatchFile"
        aRemotePatchBase = "/u02/dbserver.patch.zip_exadata_ol8_23.1.21.0.0.241204_Linux-x86-64.zip/"
        aNodeList = []
        aNodeList.append(self.mGetClubox().mReturnDom0DomUPair()[1][1])
        aRemoteNecessarySpaceMb = 400
        aSingleVmHandler = None
        _SUCCESS_ERROR_CODE = "0x00000000"
        _cmds = {
                    self.mGetRegexLocal(): [
                        [
                            exaMockCommand("/bin/sha256sum*", aRc=0, aStdout="d509ecc7c0736b488ba7adc79ffd56d31b9674af89e0f7d835c741bd05867e0f  PatchPayloads/DBPatchFile/dbserver.patch.zip", aPersist=True),
                            exaMockCommand("/bin/awk*", aRc=0, aStdout="d509ecc7c0736b488ba7adc79ffd56d31b9674af89e0f7d835c741bd05867e0f"),
                            exaMockCommand("/bin/du*", aRc=0, aStdout="327M	PatchPayloads/DBPatchFile/dbserver.patch.zip", aPersist=True),
                            exaMockCommand("/bin/awk*", aRc=0, aStdout="327M"),
                        ]
                    ],
                    self.mGetRegexDomU(): [
                        [
                            exaMockCommand("/usr/bin/sha256sum /u02/dbserver.patch.zip_exadata_ol8_23.1.21.0.0.241204_Linux-x86-64.zip/dbserver.patch.zip | /bin/awk '{print $1}'", aRc=0, aStdout="d509ecc7c0736b488ba7adc79ffd56d31b9674af89e0f7d835c741bd05867e0f", aPersist=True),
                            exaMockCommand("mkdir -p*", aRc=0, aPersist=True),
                            exaMockCommand("chmod 775", aRc=0, aPersist=True),
                            exaMockCommand("df -mP*", aRc=0, aStdout="8142", aPersist=True),
                            exaMockCommand("ls -l *", aRc=0, aStdout="-rw-r--r-- 1 root root 342452486 Jun 13 12:53 /u02/dbserver.patch.zip_exadata_ol8_23.1.21.0.0.241204_Linux-x86-64.zip/dbserver.patch.zip", aPersist=True),
                            exaMockCommand("unzip -d* ", aRc=0, aPersist=True),
                        ],
                        [
                            exaMockCommand("/usr/bin/sha256sum /u02/dbserver.patch.zip_exadata_ol8_23.1.21.0.0.241204_Linux-x86-64.zip/dbserver.patch.zip | /bin/awk '{print $1}'", aRc=0, aStdout="d509ecc7c0736b488ba7adc79ffd56d31b9674af89e0f7d835c741bd05867e0f", aPersist=True),
                            exaMockCommand("mkdir -p*", aRc=0, aPersist=True),
                            exaMockCommand("df -mP*", aRc=0, aStdout="8142", aPersist=True),
                            exaMockCommand("ls -l *", aRc=0, aStdout="-rw-r--r-- 1 root root 342452486 Jun 13 12:53 /u02/dbserver.patch.zip_exadata_ol8_23.1.21.0.0.241204_Linux-x86-64.zip/dbserver.patch.zip", aPersist=True),
                            exaMockCommand("unzip -d* ", aRc=0, aPersist=True),
                        ]
                    ]
        }
        self.__patch_args_dict['TargetType'] = ["domu"] 
        _targetHandler = TargetHandler(self.__patch_args_dict)
        self.mPrepareMockCommands(_cmds)
        _rc, _errmsg = _targetHandler.mValidateImageCheckSum(_PatchFile, _local_patch_path, aRemotePatchBase, aNodeList, aRemoteNecessarySpaceMb, aSingleVmHandler)
        self.assertEqual(_rc, _SUCCESS_ERROR_CODE)


    def test_mCheckKnownAlertHistory(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on TargetHandler.mCheckKnownAlertHistory")
        _target_type = "domu"
        _domU_list = self.mGetClubox().mReturnDom0DomUPair()[1]

        _cmds = {
        }
        self.__patch_args_dict['TargetType'] = ["domu"] 
        self.mPrepareMockCommands(_cmds)
        _targetHandler = TargetHandler(self.__patch_args_dict)
        self.assertEqual(_targetHandler.mCheckKnownAlertHistory(_target_type, _domU_list), True)

    def test_mGetKnownAlertHistoryCmd(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on TargetHandler.mGetKnownAlertHistoryCmd")
        _target_type = "domu"
        _cmds = {
        }
        self.__patch_args_dict['TargetType'] = ["domu"]
        self.mPrepareMockCommands(_cmds)
        _targetHandler = TargetHandler(self.__patch_args_dict)
        self.assertEqual(_targetHandler.mGetKnownAlertHistoryCmd(_target_type, "23.1.21.0.0.241204"), "")
        
    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mGetTargetVersion')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mIsConnected', return_value=True)
    def test_mCleanupExadataPatches_no_exasplice_versions(self, mock_mIsConnected, mock_mExecuteCmdLog, mock_mGetTargetVersion, mock_mConnect):
        ebLogInfo(" ")
        ebLogInfo("Running unit test for test_mCleanupExadataPatches_no_exasplice_versions")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)

        mock_mGetTargetVersion.return_value = '25.1.16.0.0.240509'
        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd') as mock_executeCmd:
            mock_executeCmd.side_effect=[(None, mockFileHandler(io.StringIO("25.1.14.0.0.240509")), None) , (None, mockFileHandler(io.StringIO("25.1.13.0.0.240509")), None)]

            target_handler = TargetHandler(self.__patch_args_dict)
            _ret_stats = target_handler.mCleanupExadataPatches(['scaqan10adm01.us.oracle.com', 'scaqan10adm02.us.oracle.com'])
            for _ret, _errmsg in _ret_stats.items():
                self.assertEqual(_ret, "0x00000000")
        ebLogInfo("Unit test for test_mCleanupExadataPatches_no_exasplice_versions executed successfully")


    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mGetTargetVersion')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mIsConnected', return_value=True)
    def test_mCleanupExadataPatches_no_exasplice_same_active_inactive_versions(self, mock_mIsConnected, mock_mExecuteCmdLog, mock_mGetTargetVersion, mock_mConnect):
        ebLogInfo(" ")
        ebLogInfo("Running unit test for test_mCleanupExadataPatches_no_exasplice_same_active_inactive_versions")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)

        mock_mGetTargetVersion.return_value = '25.1.16.0.0.240509'
        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd') as mock_executeCmd:
            mock_executeCmd.side_effect=[(None, mockFileHandler(io.StringIO("25.1.14.0.0.240509")), None) , (None, mockFileHandler(io.StringIO("25.1.14.0.0.240509")), None)]

            target_handler = TargetHandler(self.__patch_args_dict)
            _ret_stats = target_handler.mCleanupExadataPatches(['scaqan10adm05.us.oracle.com', 'scaqan10adm06.us.oracle.com'])
            for _ret, _errmsg in _ret_stats.items():
                self.assertEqual(_ret, "0x00000000")
        ebLogInfo("Unit test for test_mCleanupExadataPatches_no_exasplice_same_active_inactive_versions executed successfully")


    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mGetTargetVersion')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mIsConnected', return_value=True)
    def test_mCleanupExadataPatches_no_exasplice_same_active_target_versions(self, mock_mIsConnected, mock_mExecuteCmdLog, mock_mGetTargetVersion, mock_mConnect):
        ebLogInfo(" ")
        ebLogInfo("Running unit test for test_mCleanupExadataPatches_no_exasplice_same_active_target_versions")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)

        mock_mGetTargetVersion.return_value = '25.1.14.0.0.240509'
        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd') as mock_executeCmd:
            mock_executeCmd.side_effect=[(None, mockFileHandler(io.StringIO("25.1.14.0.0.240509")), None) , (None, mockFileHandler(io.StringIO("25.1.14.0.0.240509")), None)]

            target_handler = TargetHandler(self.__patch_args_dict)
            _ret_stats = target_handler.mCleanupExadataPatches(['scaqan10adm05.us.oracle.com', 'scaqan10adm06.us.oracle.com'])
            for _ret, _errmsg in _ret_stats.items():
                self.assertEqual(_ret, "0x00000000")
        ebLogInfo("Unit test for test_mCleanupExadataPatches_no_exasplice_same_active_target_versions executed successfully")


    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mGetTargetVersion')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mIsConnected', return_value=True)
    def test_mCleanupExadataPatches_with_exasplice_versions(self, imock_mIsConnected, mock_mExecuteCmdLog, mock_mGetTargetVersion, mock_mConnect):
        ebLogInfo(" ")
        ebLogInfo("Running unit test for test_mCleanupExadataPatches_with_exasplice_versions")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)

        mock_mGetTargetVersion.return_value = '25.1.16.0.0.240509'
        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd') as mock_executeCmd:
            mock_executeCmd.side_effect=[(None, mockFileHandler(io.StringIO("25.1.14.0.0.240509.exasplice.suffix")), mockFileHandler()) , (None, mockFileHandler(io.StringIO("25.1.13.0.0.240509.exasplice.suffix")), mockFileHandler())]
            target_handler = TargetHandler(self.__patch_args_dict)
            _ret_stats = target_handler.mCleanupExadataPatches(['scaqan10adm03.us.oracle.com', 'scaqan10adm04.us.oracle.com'])
            for _ret, _errmsg in _ret_stats.items():
                self.assertEqual(_ret, "0x00000000")
        ebLogInfo("Unit test for test_mCleanupExadataPatches_with_exasplice_versions executed successfully")


    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mGetTargetVersion')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mIsConnected', return_value=True)
    def test_mCleanupExadataPatches_with_exasplice_same_active_inactive_versions(self, imock_mIsConnected, mock_mExecuteCmdLog, mock_mGetTargetVersion, mock_mConnect):
        ebLogInfo(" ")
        ebLogInfo("Running unit test for test_mCleanupExadataPatches_with_exasplice_same_active_inactive_versions")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)

        mock_mGetTargetVersion.return_value = '25.1.16.0.0.240509'
        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd') as mock_executeCmd:
            mock_executeCmd.side_effect=[(None, mockFileHandler(io.StringIO("25.1.14.0.0.240509.exasplice.suffix")), mockFileHandler()) , (None, mockFileHandler(io.StringIO("25.1.14.0.0.240509.exasplice.suffix")), mockFileHandler())]
            target_handler = TargetHandler(self.__patch_args_dict)
            _ret_stats = target_handler.mCleanupExadataPatches(['scaqan10adm05.us.oracle.com', 'scaqan10adm06.us.oracle.com'])
            for _ret, _errmsg in _ret_stats.items():
                self.assertEqual(_ret, "0x00000000")
        ebLogInfo("Unit test for test_mCleanupExadataPatches_with_exasplice_same_active_inactive_versions executed successfully")


    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mGetTargetVersion')
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch('exabox.utils.node.exaBoxNode.mIsConnected', return_value=True)
    def test_mCleanupExadataPatches_with_exasplice_same_active_target_versions(self, imock_mIsConnected, mock_mExecuteCmdLog, mock_mGetTargetVersion, mock_mConnect):
        ebLogInfo(" ")
        ebLogInfo("Running unit test for test_mCleanupExadataPatches_with_exasplice_same_active_target_versions")
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh", aStdout="scaqan03dv0208.us.oracle.com"),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)

        mock_mGetTargetVersion.return_value = '25.1.14.0.0.240509'
        with patch('exabox.core.Node.exaBoxNode.mExecuteCmd') as mock_executeCmd:
            mock_executeCmd.side_effect=[(None, mockFileHandler(io.StringIO("25.1.14.0.0.240509.exasplice.suffix")), mockFileHandler()) , (None, mockFileHandler(io.StringIO("25.1.14.0.0.240509.exasplice.suffix")), mockFileHandler())]
            target_handler = TargetHandler(self.__patch_args_dict)
            _ret_stats = target_handler.mCleanupExadataPatches(['scaqan10adm05.us.oracle.com', 'scaqan10adm06.us.oracle.com'])
            for _ret, _errmsg in _ret_stats.items():
                self.assertEqual(_ret, "0x00000000")
        ebLogInfo("Unit test for test_mCleanupExadataPatches_with_exasplice_same_active_target_versions executed successfully")

    @patch("exabox.ovm.clumisc.ebCluSshSetup.mRestoreSSHKey", return_value=True)
    @patch("exabox.ovm.clumisc.ebCluSshSetup.mCleanSSHPasswordless", return_value=True)
    @patch("exabox.core.Node.exaBoxNode.mConnect", return_value=True)
    def test_mCleanEnvironment_cell_success(
        self, mock_connect, mock_clean_ssh, mock_restore_ssh
    ):
        """
        Verify TargetHandler.mCleanEnvironment:
          1. Calls mCleanSSHPasswordless with aSkipRestore=True when node type is CELL
          2. Calls mRestoreSSHKey afterwards
        """

        with patch.dict(self.__patch_args_dict, {"target_type": "CELL"}, clear=False):
            target_handler = TargetHandler(self.__patch_args_dict)
            target_handler.mPatchLogInfo = MagicMock()
            target_handler.mUpdatePatchStatus = MagicMock()
            target_handler.mGetPatchMgrOutFiles = MagicMock()
            target_handler.mGetPatchMgrDiagFiles = MagicMock()
            target_handler.mGetPatchMgrMiscLogFiles = MagicMock()
            target_handler.mGetCellLogs = MagicMock()
            target_handler.mGetUpgradeROCESwitchOutFiles = MagicMock()
            target_handler.mGetUpgradeIBSwitchOutFiles = MagicMock()
            target_handler.mPrintPatchmgrLogFormattedDetails = MagicMock()
            target_handler.mDeleteNodesFile = MagicMock()
            target_handler.mGetCluPatchCheck = MagicMock(
                return_value=MagicMock(mVerifyPatchmgrSshConnectivityBetweenExadataHosts=MagicMock())
            )

            dom0 = "sc1iad00dd01.us.oracle.com"
            nodes = ["sc1iad00cl01.us.oracle.com", "sc1iad00cl02.us.oracle.com","sc1iad00cl03.us.oracle.com"]
            # Call with CELL + success exit code
            target_handler.mCleanEnvironment(
                aDom0=dom0,
                aNodesList=nodes,
                aListFilePath="/tmp/list.txt",
                aBaseDir="/tmp/base",
                aLogDir="/tmp/logs",
                aNodeType="CELL",
                aPatchExitStatus=0,
            )
            mock_clean_ssh.assert_called_once_with(dom0, nodes, aSkipRestore=True)
            mock_restore_ssh.assert_called_once_with(dom0, aUser=None)

    @patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mGetNodeListFromNodesToBePatchedFile", return_value=['slcs27adm04.us.oracle.com'])
    @patch("exabox.core.Node.exaBoxNode.mExecuteCmd")
    @patch('exabox.utils.node.exaBoxNode.mExecuteCmdLog')
    @patch("exabox.core.Node.exaBoxNode.mGetCmdExitStatus", return_value=0)
    @patch("exabox.core.Node.exaBoxNode.mFileExists", return_value=True)
    def test_mExecutePatchMgrCmd(self, mock_mFileExists, mock_mGetCmdExitStatus, mock_mExecuteCmdLog, mock_mExecuteCmd, mock_mGetNodeListFromNodesToBePatchedFile):
        ebLogInfo("")
        ebLogInfo("Running unit test on InfraPatchManager.mExecutePatchMgrCmd")

        mock_mExecuteCmd.side_effect=[(None, mockFileHandler(io.StringIO("mock_output")), None), (None, mockFileHandler(io.StringIO("123")), mockFileHandler())]

        _patch_mgr = InfraPatchManager(aTarget="domu", aOperation="patch", aPatchBaseAfterUnzip="/patch/base", aLogPathOnLaunchNode="/log/path", aHandler=TargetHandler(self.__patch_args_dict))
        result = _patch_mgr.mExecutePatchMgrCmd("mocked_patchmgr_cmd")
        self.assertEqual(result, '0x00000000')

        _patch_mgr = InfraPatchManager(aTarget="domu", aOperation="patch", aPatchBaseAfterUnzip="/patch/base", aLogPathOnLaunchNode="/log/path", aHandler=TargetHandler(self.__patch_args_dict))
        with patch("exabox.core.Node.exaBoxNode.mFileExists", return_value=False):
            with patch("exabox.infrapatching.handlers.targetHandler.infrapatchmgrhandler.InfraPatchManager.mCheckForPatchMgrSessionExistence", return_value=(1, None)):
                result = _patch_mgr.mExecutePatchMgrCmd("mocked_patchmgr_cmd")
                self.assertEqual(result, '0x03030026')

        _patch_mgr = InfraPatchManager(aTarget="cell", aOperation="patch", aPatchBaseAfterUnzip="/patch/base", aLogPathOnLaunchNode="/log/path", aHandler=TargetHandler(self.__patch_args_dict))
        result = _patch_mgr.mExecutePatchMgrCmd("mocked_patchmgr_cmd")
        self.assertEqual(result, '0x03030025')

if __name__ == "__main__":
    unittest.main()
