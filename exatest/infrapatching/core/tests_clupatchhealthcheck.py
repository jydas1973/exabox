#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/infrapatching/core/tests_clupatchhealthcheck.py /main/4 2025/11/26 16:30:13 remamid Exp $
#
# tests_clupatchhealthcheck.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
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
#    gojoseph    08/07/25 - Enh 38262352 Unit test cases to check ES services
#                           are online
#    bhpati      04/18/25 - Create file
#    bhpati      04/18/25 - Creation
#

import unittest
from unittest import mock
import io
import logging
from unittest.mock import patch, mock_open, MagicMock
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.agent.ebJobRequest import ebJobRequest
from exabox.infrapatching.utils.utility import mGetInfraPatchingConfigParam
from exabox.infrapatching.core.clupatchhealthcheck import ebCluPatchHealthCheck
from exabox.infrapatching.handlers.generichandler import GenericHandler
from exabox.core.MockCommand import exaMockCommand
from exabox.ovm.clumisc import ebCluSshSetup

class ebTestCluPatchHealthCheck(ebTestClucontrol):

    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.core.Node.exaBoxNode.mExecuteCmd', return_value=(io.StringIO(" "), io.StringIO("cellsrvStatus: running\nmsStatus: running\nrsStatus: running\nsysEdsStatus: stopped\n"), io.StringIO("mock_error")))
    def tests_mCheckCellServices(self, _mock_mConnect, _mock_mExecuteCmd):
        ebLogInfo("")
        ebLogInfo("Running unit test for mCheckCellServices")
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e \"list cell detail\" | grep Status", aRc=0, aStdout="'cellsrvStatus: running', 'msStatus: running', 'rsStatus: running'", aPersist=True),
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet lsinitiator", aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/escli --wallet /opt/oracle/cell/cellsrv/deploy/config/security/admwallet lsservice -l | grep -i OFFLINE", aRc=0, aStdout="", aPersist=True)
                ]
            ]
        }
        
        cell_services = {'cellsrvStatus: running', 'msStatus: running', 'rsStatus: running'}
        _cluctrl = self.mGetClubox()
        _clupatchhealthcheck = ebCluPatchHealthCheck(_cluctrl, aGenericHandler=GenericHandler)
        _result = _clupatchhealthcheck.mCheckCellServices("slcs27celadm04.us.oracle.com", cell_services, True)
        self.assertEqual(_result, True)
        ebLogInfo("Executed test for mCheckCellServices")


    # Test case where ES service are offline
    @patch('exabox.core.Node.exaBoxNode.mIsConnected')
    @patch('exabox.core.Node.exaBoxNode.mFileExists')
    @patch('exabox.core.Node.exaBoxNode.mDisconnect')
    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.core.Node.exaBoxNode.mExecuteCmd')
    @patch('exabox.core.Node.exaBoxNode.mGetCmdExitStatus')
    def tests_mESServicesOffline(self, _mock_exit, _mock_exec, _mock_Con, _mock_DisCon, _mock_file, _mock_isCon):
        #_mock_cellNode = _mock_cellNode.return_value
        ebLogInfo("Running unit test for offline ES Services")
        _mock_file.return_value = True
        _mock_isCon.return_value = True

        _lsservice_out = "scaqau11celadm02 scaqau11celadm02 0-0-0-0 rootServices egs_scaqau11celadm02  ONLINE\n \
                         scaqau11celadm01 scaqau11celadm01 0-0-0-0 rootServices egs_scaqau11celadm01  OFFLINE"
        _mock_exec.side_effect = [
            ("", io.StringIO("cellsrvStatus: running\nmsStatus: running\nrsStatus: running"), ""),
            ("", "", ""),  #lsinitiator
            ("", "", ""),  #lsservice -l
            ("", "", ""),  #lsservice -l
            ("", "", ""),  #lsservice -l
            ("", "", ""),  #lsservice -l
            ("", io.StringIO(_lsservice_out), "")              
        ]
        _mock_exit.side_effect = [0,0,0,0,0,0,0]
        _cluctrl = self.mGetClubox()
        _clupatchhealthcheck = ebCluPatchHealthCheck(_cluctrl, aGenericHandler=GenericHandler)
        _result = _clupatchhealthcheck.mCheckCellServices("slcs27celadm04.us.oracle.com", {} , True)
        self.assertEqual(_result, False)
        ebLogInfo("Executed test for offline ES Services")


    # Test case where ES service are online after 2 retries
    @patch('exabox.core.Node.exaBoxNode.mIsConnected')
    @patch('exabox.core.Node.exaBoxNode.mFileExists')
    @patch('exabox.core.Node.exaBoxNode.mDisconnect')
    @patch('exabox.core.Node.exaBoxNode.mConnect')
    @patch('exabox.core.Node.exaBoxNode.mExecuteCmd')
    @patch('exabox.core.Node.exaBoxNode.mGetCmdExitStatus')
    def tests_mESServicesOnline(self, _mock_exit, _mock_exec, _mock_Con, _mock_DisCon, _mock_file, _mock_isCon):
        #_mock_cellNode = _mock_cellNode.return_value
        ebLogInfo("Running unit test for online ES Services")
        _mock_file.return_value = True
        _mock_isCon.return_value = True

        _lsservice_out = "scaqau11celadm02 scaqau11celadm02 0-0-0-0 rootServices egs_scaqau11celadm02  ONLINE\n \
                         scaqau11celadm01 scaqau11celadm01 0-0-0-0 rootServices egs_scaqau11celadm01  OFFLINE"
        _mock_exec.side_effect = [
            ("", io.StringIO("cellsrvStatus: running\nmsStatus: running\nrsStatus: running"), ""),
            ("", "", ""),  #lsinitiator
            ("", "", ""),  #lsservice -l
            ("", "", ""),  #lsservice -l
        ]
        _mock_exit.side_effect = [0,0,0,1]
        _cluctrl = self.mGetClubox()
        _clupatchhealthcheck = ebCluPatchHealthCheck(_cluctrl, aGenericHandler=GenericHandler)
        _result = _clupatchhealthcheck.mCheckCellServices("slcs27celadm04.us.oracle.com", {} , True)
        self.assertEqual(_result, True)
        ebLogInfo("Executed test for online ES Services")

    @patch('exabox.infrapatching.handlers.generichandler.GenericHandler.mIsSingleWorkerRequest', return_value=True)
    @patch('exabox.core.Node.exaBoxNode.mExecuteCmdLog')
    @patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mAddError")
    def tests_mVerifyPatchmgrSshConnectivityBetweenExadataHosts(self, _mock_mAddError, _mock_log_exec, _mock_mIsSingleWorkerRequest):
        _cluctrl = self.mGetClubox()
        self.__patch_args_dict = {'CluControl': _cluctrl,
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
        ebLogInfo("Running unit test for mVerifyPatchmgrSshConnectivityBetweenExadataHosts")
        _sshError = 'Warning: Permanently added the ECDSA host key for IP address ''''10.0.144.130'''' to the list of known hosts. \
                    Connection closed by 10.0.144.130 port 22'
        _ipCIDRInfo = 'inet 10.0.144.2/20 brd 10.0.159.255 scope global vmbondeth0'
        _ipNetMask = 'NETMASK=255.255.240.0 \n NETWORK=10.0.144.0'
        _hacOut = '[2025-11-04 08:15:52 -0800] [INFO] [IMG-SEC-0106] User-origin access rules : \n \
                ### DO NOT REMOVE THIS FILE - REQUIRED FOR SYSTEM ACCESS - DO NOT REMOVE THIS FILE ### \n \
                # EXADATA ACCESS CONTROL \n \
                # user rules \n \
                + : root : console tty1 ttyS0 hvc0 localhost ip6-localhost 10.0.1.2/255.255.255.255 10.0.192.0/255.255.240.0 10.0.1.123/255.255.255.255 10.0.1.124/255.255.255.255 10.0.1.3/255.255.255.255 10.0.1.124/255.255.255.255 \n \
                + : secscan : console tty1 ttyS0 hvc0 localhost ip6-localhost 10.0.1.240/28 10.0.144.0/255.255.240.0 10.0.1.0/28 \n \
                + : cellmonitor : console tty1 ttyS0 hvc0 localhost ip6-localhost 10.0.144.0/255.255.240.0 10.0.1.0/28 \n \
                - : ALL  : ALL"'

        _mock_log_exec.side_effect = [
            ("", io.StringIO(_hacOut), "")
        ] 
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("ssh scaqab10adm02.us.oracle.com 'uptime'", aRc=1, aStderr=_sshError, aPersist=True),
                    exaMockCommand("/usr/local/bin/imageinfo -node", aRc=0, aStdout="kvmhost", aPersist=True),
                    exaMockCommand("/sbin/ip addr show*",  aRc=0, aStdout=_ipCIDRInfo, aPersist=True),
                    exaMockCommand("/bin/ipcalc -nm *",  aRc=0, aStdout=_ipNetMask, aPersist=True),
                    exaMockCommand("/opt/oracle.cellos/host_access_control access --status",  aRc=0, aStdout=_hacOut, aPersist=True),                    
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)
        aNodeList = []
        targetNode = _cluctrl.mReturnDom0DomUPair()[1][0]
        aNodeList.append(targetNode)
        aSourceNode = _cluctrl.mReturnDom0DomUPair()[0][0]
        _gh = GenericHandler(self.__patch_args_dict)
        _clupatchhealthcheck = ebCluPatchHealthCheck(_cluctrl, _gh)
        with patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetCurrentTargetType", return_value='PATCH_DOM0'), \
            patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetCurrentMasterInterface", return_value='vmbondeth0'), \
            patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetValidateSshConnectivityExecutionTimeoutInSeconds", return_value=300), \
            patch("exabox.infrapatching.handlers.generichandler.GenericHandler.mGetCluControl"): #, \
            #patch("exabox.ovm.clumisc.ebCluSshSetup.mValidateSecureSsh", return_value="True"):
            #_clupatchhealthcheck.mVerifyPatchmgrSshConnectivityBetweenExadataHosts(aNodeList, aSourceNode)
            self.assertRaises(Exception, _clupatchhealthcheck.mVerifyPatchmgrSshConnectivityBetweenExadataHosts, aNodeList, aSourceNode)

if __name__ == "__main__":
    unittest.main()
