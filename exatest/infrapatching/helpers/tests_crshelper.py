#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/infrapatching/helpers/tests_crshelper.py /main/10 2025/10/28 09:43:01 rbhandar Exp $
#
# tests_clupatchhealthcheck.py
#
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_clupatchhealthcheck.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    rbhandar    10/09/25 - Bug 38510857 - NON ROLLING PATCHING OPERATION POST
#                           PATCH HAS DUPLICATE CELLS IN LIST
#    avimonda    06/23/25 - Bug 37899705 - DOMU IMAGE UPDATE PRECHECK IS NOT
#                           CHECKING CRS AUTOSTART STATUS
#    avimonda    05/23/25 - Bug 37833454 - EXACC GEN2 - INFRA PATCHING - DOM0
#                           POST HEARTBEAT VALIDATION HUNG IF OUTPUT SIZE MORE
#                           THAN 1 MB
#    araghave    03/24/25 - Enh 37164753 - USE ROOT USER TO CONNECT TO DOMU TO
#                           PERFORM CRS CHECKS ON EXACC ENVIRONMENTS DURING
#                           DOM0 PATCHING
#    avimonda    03/28/25 - Bug 37754307 - AIM4ECS:0X0305001D - PDB IS IN A
#                           DEGRADED STATE.
#    sdevasek    03/24/25 - Bug 35265324 - PATCHING IS NOT CHECKING CRS HB WHEN
#                           GRIDDISK STATUS IS UNKNOWN
#    avimonda    02/09/25 - Enh 37291048: EXACC GEN 2 | POST PATCHING HB ISSUE,
#                           VM NOT ACCESSIBLE | ERROR DETAILS ENHANCEMNT NEEDED
#    nelango     01/24/25 - Bug 37509437: Unit test case for txn
#                           nelango_bug-37500959
#    bhpati      12/02/24 - Bug 36563682 - AIM4EXACLOUD:0X03030008 - UNABLE TO
#                           ESTABLISH HEARTBEAT ON THE CELLS. NOT ALL CRS/DB
#                           SERVICES ARE UP ON DOMU
#    avimonda    11/01/24 - Bug 37164251 - EXACC GEN2 | REQUEST TO SHOW
#                           PATCHING FAILURE ISSUE AS AN ERROR IN THREAD
#                           LOG AND TRACE FILE
#    avimonda    10/31/24 - Create file
#    avimonda    10/31/24 - Creation
#
import unittest
import io
from unittest.mock import patch, MagicMock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.infrapatching.helpers.crshelper import CrsHelper, CRS_IS_DISABLED, PATCH_SUCCESS_EXIT_CODE
from exabox.infrapatching.handlers.generichandler import GenericHandler

class ebTestCluPatchHealthCheck(ebTestClucontrol):

    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetDomUCustomerNameforDomuNatHostName", return_value=("iad123456exdd001nat01.oraclecloud.internal"))
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetCurrentTargetType", return_value="dom0")
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mIsRootOrOpcUserExists", return_value=(False, True))
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mGenCrsctlCmd", return_value=("0x00000000", ""))
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetTask", return_value="patch")
    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(io.StringIO(" "), io.StringIO("CRS-4622: Oracle High Availability Services autostart is disabled"), io.StringIO("mock_error")))
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetUsertoConnectWith", return_value=("opc"))
    def test_mCheckCrsIsEnabled(self, _mock_mGetDomUCustomerNameforDomuNatHostName, _mock_mGetCurrentTargetType, _mock_mIsRootOrOpcUserExists, _mock_mGenCrsctlCmd, _mock_mGetTask, _mock_mConnect, _mock_mExecuteCmd, _mock_mGetUsertoConnectWith):

        ebLogInfo("Executing test for mCheckCrsIsEnabled()")
        _cluctrl = self.mGetClubox()
        _crsHelper = CrsHelper(GenericHandler)
        _result = _crsHelper.mCheckCrsIsEnabled("iad123456exdd01.oraclecloud.internal")
        self.assertEqual(_result, "0x03030028")
        ebLogInfo("Executed test for mCheckCrsIsEnabled()")


    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetTask", return_value="patch")
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mCheckCrsIsEnabled", return_value="0x03030027")
    def test_mReturnListofVMsWithCRSAutoStartupEnabled(self, _mock_mGetTask, _mock_mCheckCrsIsEnabled):
        ebLogInfo("Executing test for mReturnListofVMsWithCRSAutoStartupEnabled")
        _cluctrl = self.mGetClubox()
        _crsHelper = CrsHelper(GenericHandler)
        _ret, _list_of_vms_crs_auto_startup_enabled = _crsHelper.mReturnListofVMsWithCRSAutoStartupEnabled(["iad123456exdd01.oraclecloud.internal", "iad123456exdd02.oraclecloud.internal"])
        self.assertEqual(_ret, "0x03030027")
        self.assertEqual(_list_of_vms_crs_auto_startup_enabled, [])
        ebLogInfo("Executed test for mReturnListofVMsWithCRSAutoStartupEnabled")
    
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetDomUCustomerNameforDomuNatHostName", return_value=("iad123456exdd001nat01.oraclecloud.internal"))
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mGenCrsctlCmd", return_value=("0x00000000", ""))
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetTask", return_value="patch")
    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(io.StringIO(" "), io.StringIO("CRS-4639: Could not contact Oracle High Availability Services"), io.StringIO("mock_error")))
    def test_mCheckCrsInitResourcesonDomU(self, _mock_mGetDomUCustomerNameforDomuNatHostName, _mock_mGenCrsctlCmd, _mock_mGetTask, _mock_mConnect, _mock_mExecuteCmd):
        ebLogInfo("Executing test for mCheckCrsInitResourcesonDomU")
        _cluctrl = self.mGetClubox()
        _crsHelper = CrsHelper(GenericHandler)
        _ret, _output = _crsHelper.mCheckCrsInitResourcesonDomU("iad123456exdd01.oraclecloud.internal","iad123456exdd02.oraclecloud.internal")
        self.assertEqual(_ret, "0x03030028")
        self.assertEqual(_output, "")
        ebLogInfo("Executed test for mCheckCrsInitResourcesonDomU")
    
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetDomUCustomerNameforDomuNatHostName", return_value=("iad123456exdd001nat01.oraclecloud.internal"))
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetCurrentTargetType", return_value="dom0")
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mIsRootOrOpcUserExists", return_value=(True, False))
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetTask", return_value="patch")
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mCheckCrsIsEnabled", return_value="0x00000000")
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mGenCrsctlCmd", return_value=("0x00000000", ""))
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mRunCrsctlCheckCrsCommand", return_value=("0x00000000", 'CRS is up and running'))
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mCheckCrsInitResourcesonDomU", return_value=("0x03030028", ""))
    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(io.StringIO(" "), io.StringIO("CRS-2791: Starting shutdown of Oracle High Availability Services-managed resources"), io.StringIO("mock_error")))
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mStartupCrsOnDomU", return_value=("0x00000000", ""))
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetUsertoConnectWith", return_value=("root"))
    def test_mCheckandRestartCRSonDomU(self, _mock_mGetDomUCustomerNameforDomuNatHostName, _mock_mGetCurrentTargetType, _mock_mIsRootOrOpcUserExists, _mock_mCheckCrsIsEnabled, _mock_mGetTask, _mock_mGenCrsctlCmd, _mock_mRunCrsctlCheckCrsCommand, _mock_mCheckCrsInitResourcesonDomU, _mock_mConnect, _mock_mExecuteCmd, _mock_mStartupCrsOnDomU, _mock_mGetUsertoConnectWith):
        ebLogInfo("Executing test for mCheckandRestartCRSonDomU")
        _cluctrl = self.mGetClubox()
        _crsHelper = CrsHelper(GenericHandler)
        _ret = _crsHelper.mCheckandRestartCRSonDomU("iad123456exdd01.oraclecloud.internal")
        self.assertEqual(_ret, "0x03030022")
        ebLogInfo("Executed test for mCheckandRestartCRSonDomU")
    
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mIsExaScale", return_value=False)
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mReturnExecOutput", return_value="/u01/app/19.0.0.0/grid")
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetCluCtrlInstance")
    def test_mGetGiHomePath(self,_mock_mIsExaScale,_mock_mReturnExecOutput,_mock_mGetCluCtrlInstance):
        ebLogInfo("Executing test for mGetGiHomePath")
        _cluctrl = self.mGetClubox()
        _crsHelper = CrsHelper(GenericHandler)
        _ret, _gi_home = _crsHelper.mGetGiHomePath("iad123456exdd01.oraclecloud.internal")
        self.assertEqual(_ret, "0x00000000")
        self.assertEqual(_gi_home, "/u01/app/19.0.0.0/grid")
        ebLogInfo("Executed test for mGetGiHomePath")

    @patch.object(CrsHelper, 'mGetHandlerInstance')
    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, io.StringIO("alert.log\n"), None))
    @patch('exabox.core.Node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    def test_mValidateDomUHeartbeat_domus_not_accessible_from_exacloud_node(self, _mock_mGetCmdExitStatus, _mock_mExecuteCmd, _mock_mConnect, _mock_GetHandlerInstance):
        ebLogInfo("Executing test for mValidateDomUHeartbeat()")
        _mock_instance = MagicMock()
        _mock_GetHandlerInstance.return_value = _mock_instance
        _mock_instance.mGetExadataPatchGridHeartBeatTimeoutSec.return_value = -1
        _mock_instance.mGetDomUCustomerNameforDomuNatHostName.return_value.strip.return_value = "jed143898exdd002nat01.oraclecloud.internal"
        _mock_instance.mGetCluPatchCheck.return_value.mVerifyCellsInUseByASM.return_value = (["jed143898exdcl01.oraclecloud.internal"],[])
        _mock_instance.mGetCellList.return_value = ["jed143898exdcl01.oraclecloud.internal"]
        _mock_instance.mGetDomUNatHostNamesforDomuCustomerHostNames.return_value = ["jed143898exdd002nat01.oraclecloud.internal"]
        _mock_instance.mGetReachableDomuList.return_value = ([], ["jed143898exdd002nat01.oraclecloud.internal"])
        _mock_instance.mReturnBothDomUNATCustomerHostNames.return_value = ["oracle-vmprod01.oracle.com"]

        _cluctrl = self.mGetClubox()
        _crsHelper = CrsHelper(GenericHandler)
        _ret, _failed_heartbeat_domu_list, _domus_accessible_from_exacloud_node = _crsHelper.mValidateDomUHeartbeat(["jed143898exdd002nat01.oraclecloud.internal"], False)
        self.assertEqual(_ret, "0x03030008")
        ebLogInfo("Executed test for mValidateDomUHeartbeat()")

    @patch.object(CrsHelper, 'mGetHandlerInstance')
    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, io.StringIO("alert.log\n"), None))
    @patch('exabox.core.Node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    def test_mValidateDomUHeartbeat(self, _mock_mGetCmdExitStatus, _mock_mExecuteCmd, _mock_mConnect, _mock_GetHandlerInstance):
        ebLogInfo("Executing test for mValidateDomUHeartbeat()")
        _mock_instance = MagicMock()
        _mock_GetHandlerInstance.return_value = _mock_instance
        _mock_instance.mGetExadataPatchGridHeartBeatTimeoutSec.return_value = -1
        _mock_instance.mGetDomUCustomerNameforDomuNatHostName.return_value.strip.return_value = "jed143898exdd002nat01.oraclecloud.internal"
        _mock_instance.mGetCluPatchCheck.return_value.mVerifyCellsInUseByASM.return_value = (["jed143898exdcl01.oraclecloud.internal"],[])
        _mock_instance.mGetCellList.return_value = ["jed143898exdcl01.oraclecloud.internal"]
        _mock_instance.mGetDomUNatHostNamesforDomuCustomerHostNames.return_value = ["jed143898exdd002nat01.oraclecloud.internal"]
        _mock_instance.mGetReachableDomuList.return_value = ([], [])
        _mock_instance.mReturnBothDomUNATCustomerHostNames.return_value = ["oracle-vmprod01.oracle.com"]

        _cluctrl = self.mGetClubox()
        _crsHelper = CrsHelper(GenericHandler)
        _ret, _failed_heartbeat_domu_list, _domus_accessible_from_exacloud_node = _crsHelper.mValidateDomUHeartbeat(["jed143898exdd002nat01.oraclecloud.internal"], False)
        self.assertEqual(_ret, "0x03030008")
        ebLogInfo("Executed test for mValidateDomUHeartbeat()")

    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetCurrentTargetType", return_value="dom0")
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetDomUCustomerNameforDomuNatHostName", return_value=("yosemite-ivruw1.oraclecloud.internal"))
    @patch("exabox.infrapatching.helpers.crshelper.CrsHelper.mIsPDBDegraded", return_value=True)
    def test_mComparePreAndPostPatchPDBSystemDetailsJson(self, _mock_mIsPDBDegraded, _mock_mGetDomUCustomerNameforDomuNatHostName, _mock_mGetCurrentTargetType):
        ebLogInfo("Executing test for mComparePreAndPostPatchPDBSystemDetailsJson()") 

        json_pre = {
          "oalt" : {
            "pdbs" : {
              "PDB1" : {
                "pdbNodeLevelDetails" : {
                  "yosemite-ivruw1" : {
                    "nodeName" : "yosemite-ivruw1",
                    "openMode" : "READ_WRITE",
                    "restricted" : "false"
                  },
                },
                "pdbSize" : "13GB",
                "pdbUsedSize" : "1GB",
                "pdbSnapshotDetails" : "null"
              }
            },
            "messages" : [ ]
          }
        }

        json_post_missing_pdb_node_details = {
          "oalt" : {
            "pdbs" : {
              "PDB1" : {
                "pdbNodeLevelDetails" : {
                },
                "pdbSize" : "13GB",
                "pdbUsedSize" : "1GB",
                "pdbSnapshotDetails" : "null"
              }
            },
            "messages" : [ ]
          }
        }

        json_post_restricted = {
          "oalt" : {
            "pdbs" : {
              "PDB1" : {
                "pdbNodeLevelDetails" : {
                  "yosemite-ivruw1" : {
                    "nodeName" : "yosemite-ivruw1",
                    "openMode" : "READ",
                    "restricted" : "true"
                  },
                },
                "pdbSize" : "13GB",
                "pdbUsedSize" : "1GB",
                "pdbSnapshotDetails" : "null"
              }
            },
            "messages" : [ ]
          }
        }

        json_post_pdb_missing = {
          "oalt" : {
            "messages" : [ ]
          }
        }

        _cluctrl = self.mGetClubox()
        _crsHelper = CrsHelper(GenericHandler)

        _status, _err_msg, _statusdict = _crsHelper.mComparePreAndPostPatchPDBSystemDetailsJson(json_pre, None, "yosemite-ivruw1")
        self.assertEqual(_status, "0x0303002C")
        self.assertEqual(_err_msg, "databases details are missing in db system details json post patching.")

        _status, _err_msg, _statusdict = _crsHelper.mComparePreAndPostPatchPDBSystemDetailsJson(json_pre, json_post_missing_pdb_node_details, "yosemite-ivruw1")
        self.assertEqual(_status, "0x0303002C")
        self.assertEqual(_err_msg, "PDB node details are missing for PDB PDB1 within CDB oalt on VM - yosemite-ivruw1.")

        _status, _err_msg, _statusdict = _crsHelper.mComparePreAndPostPatchPDBSystemDetailsJson(json_pre, json_post_restricted, "yosemite-ivruw1")
        self.assertEqual(_status, "0x0303002C")
        self.assertEqual(_err_msg, "PDB PDB1 within CDB oalt is in degraded state on VM - yosemite-ivruw1, prior to patching it is in READ_WRITE state with restricted set to false, where as post patching it is in READ state with restricted set to true.")

        _status, _err_msg, _statusdict = _crsHelper.mComparePreAndPostPatchPDBSystemDetailsJson(json_pre, json_post_pdb_missing, "yosemite-ivruw1")
        self.assertEqual(_status, "0x0303002C")
        self.assertEqual(_err_msg, "PDB details are missing for PDB PDB1 within CDB oalt on VM - yosemite-ivruw1.")

        ebLogInfo("Executed test for mComparePreAndPostPatchPDBSystemDetailsJson()")

    @patch.object(CrsHelper, 'mGetHandlerInstance')
    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(None, io.StringIO("alert.log\n"), None))
    @patch('exabox.core.Node.exaBoxNode.mGetCmdExitStatus', return_value=0)
    def test_mValidateDomUHeartbeat_mGetHeartBeatDetailsInCellAlertLogExecutionTimeoutSec(self,  _mock_mGetCmdExitStatus, _mock_mExecuteCmd, _mock_mConnect, _mock_GetHandlerInstance):

        ebLogInfo("")
        ebLogInfo("Executing test for test_mValidateDomUHeartbeat_mGetHeartBeatDetailsInCellAlertLogExecutionTimeoutSec()")

        _mock_instance = MagicMock()
        _mock_GetHandlerInstance.return_value = _mock_instance
        _mock_instance.mGetExadataPatchGridHeartBeatTimeoutSec.return_value = 300
        _mock_instance.mGetHeartBeatDetailsInCellAlertLogExecutionTimeoutSec.return_value = 600
        _mock_instance.mGetDomUCustomerNameforDomuNatHostName.return_value.strip.return_value = "jed143898exdd002nat01.oraclecloud.internal"
        _mock_instance.mGetCluPatchCheck.return_value.mVerifyCellsInUseByASM.return_value = (["jed143898exdcl01.oraclecloud.internal"],[])
        _mock_instance.mGetCellList.return_value = ["jed143898exdcl01.oraclecloud.internal"]
        _mock_instance.mGetDomUNatHostNamesforDomuCustomerHostNames.return_value = ["jed143898exdd002nat01.oraclecloud.internal"]
        _mock_instance.mGetReachableDomuList.return_value = ([], [])
        _mock_instance.mReturnBothDomUNATCustomerHostNames.return_value = ["oracle-vmprod01.oracle.com"]

        _cluctrl = self.mGetClubox()
        _crsHelper = CrsHelper(GenericHandler)

        _crsHelper.mValidateDomUHeartbeat(["jed143898exdd002nat01.oraclecloud.internal"], False)
        _mock_instance.mGetHeartBeatDetailsInCellAlertLogExecutionTimeoutSec.assert_called_once()

        ebLogInfo("Executed test for test_mValidateDomUHeartbeat_mGetHeartBeatDetailsInCellAlertLogExecutionTimeoutSec()")
    
    @patch.object(CrsHelper, 'mGetHandlerInstance')
    def test_mGetCellListForCRSHeartbeatValidation(self, _mock_GetHandlerInstance):
        ebLogInfo("Executing test for mGetCellListForCRSHeartbeatValidation()")
        _mock_instance = MagicMock()
        _mock_GetHandlerInstance.return_value = _mock_instance
        _mock_instance.mGetCluPatchCheck.return_value.mVerifyCellsInUseByASM.return_value = (['jed102203exdcl09.oraclecloud.internal', 'jed102203exdcl08.oracle.cloud.internal','jed102203exdcl09.oraclecloud.internal', 'jed102203exdcl08.oraclecloud.internal'], ['jed102203exdcl09.oraclecloud.internal', 'jed102203exdcl08.oraclecloud.internal', 'jed102203exdcl10.oraclecloud.internal', 'jed102203exdcl12.oraclecloud.internal','jed102203exdcl09.oraclecloud.internal', 'jed102203exdcl08.oraclecloud.internal', 'jed102203exdcl10.oraclecloud.internal', 'jed102203exdcl12.oraclecloud.internal'])
        _aCellList = ['jed102203exdcl08.oraclecloud.internal', 'jed102203exdcl09.oraclecloud.internal', 'jed102203exdcl10.oraclecloud.internal', 'jed102203exdcl12.oraclecloud.internal']
        _cluctrl = self.mGetClubox()
        _crsHelper = CrsHelper(GenericHandler)
        _cell_list_to_validate_for_crs, _cells_with_gd_unknown_state = _crsHelper.mGetCellListForCRSHeartbeatValidation(_aCellList)
        self.assertIn('jed102203exdcl12.oraclecloud.internal', _cells_with_gd_unknown_state)
        self.assertIn('jed102203exdcl10.oraclecloud.internal', _cells_with_gd_unknown_state)

        ebLogInfo("Executed test for mGetCellListForCRSHeartbeatValidation()")

    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetCustomizedDomUList")
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mAddError")
    def test_mCheckandRestartCRSonAllDomUWithinCluster(self, _mock_mAddError, _mock_mGetCustomizedDomUList):

        ebLogInfo("Executing test for mCheckandRestartCRSonAllDomUWithinCluster()")

        _mock_mGetCustomizedDomUList.return_value = ["iad123456exddu1.oraclecloud.internal", "iad123456exddu2.oraclecloud.internal"]
        _cluctrl = self.mGetClubox()
        _crsHelper = CrsHelper(GenericHandler)

        _rc_status = [{'domu': 'iad123456exddu1.oraclecloud.internal', 'ret': CRS_IS_DISABLED}, {'domu': 'iad123456exddu2.oraclecloud.internal', 'ret': CRS_IS_DISABLED}]

        with patch.object(_crsHelper, 'mCheckandRestartCRSonDomU', return_value = CRS_IS_DISABLED):
            _result = _crsHelper.mCheckandRestartCRSonAllDomUWithinCluster()
            self.assertEqual(_result, "0x0305000F")

        _rc_status = [{'domu': 'iad123456exddu1.oraclecloud.internal', 'ret': PATCH_SUCCESS_EXIT_CODE}, {'domu': 'iad123456exddu2.oraclecloud.internal', 'ret': PATCH_SUCCESS_EXIT_CODE}]

        with patch.object(_crsHelper, 'mCheckandRestartCRSonDomU', return_value = PATCH_SUCCESS_EXIT_CODE):
            _result = _crsHelper.mCheckandRestartCRSonAllDomUWithinCluster()
            self.assertEqual(_result, "0x00000000")

        ebLogInfo("Executed test for mCheckandRestartCRSonAllDomUWithinCluster()")

if __name__ == "__main__":
    unittest.main()

