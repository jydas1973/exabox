#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/healthcheck/tests_cluexachk.py /main/9 2026/01/12 04:30:19 ajayasin Exp $
#
# tests_cluexachk.py
#
# Copyright (c) 2021, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_cluexachk.py
#
#    DESCRIPTION
#      Unit test cases for the file $EC_ROOT/exabox/healthcheck/cluexachk.py
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ajayasin     01/06/26 - Codex UT enhancement
#    remamid      09/18/24 - test case for bug 37005729
#    ajayasin     04/06/22 - ut addition
#    ajayasin     01/10/22 - cluexachk unit test file added
#    ajayasin     01/06/22 - Creation
#
from asyncio.log import logger
import os
import json
import unittest
import fcntl
from unittest.mock import patch, MagicMock, PropertyMock, mock_open, call
from contextlib import contextmanager
from types import SimpleNamespace
import copy
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.cluhealth import ebCluHealthCheck
from exabox.healthcheck.cluexachk import (
    ebCluExachk as cluexachk,
    FileLockMgr,
    LockMode,
    obtain_cp_lock,
    obtain_remote_lock,
)
import warnings
from ast import literal_eval

from exabox.core.Error import ExacloudRuntimeError


class testebCluExachk(cluexachk):
    def __init__(self,aCluHealthCheck, aOptions):
        cluexachk.__init__(self,aCluHealthCheck, aOptions)
    def mInstallAhf(self,deviceType,aOptions=None,_selected_host = None):
        return {'scaqab10adm01.us.oracle.com': True}

class ebTestNode(ebTestClucontrol):

    def _build_cluexachk_with_ebox(self, ebox):
        class DummyHealthCheck(object):
            def __init__(self, inner_ebox):
                self._inner_ebox = inner_ebox

            def mGetEbox(self):
                return self._inner_ebox

        return cluexachk(DummyHealthCheck(ebox), MagicMock())

    def _create_remote_run_setup(self, pingable=True, host='dom0-1', host_list=None, config=None, skip_exacc=False):
        recommend = []
        json_map = {}
        node = MagicMock()
        node.mGetNodeType.return_value = 'dom0'
        node.mGetPingable.return_value = pingable
        node.mGetHostname.return_value = host
        cluster_host_d = {host: node}

        host_entries = host_list if host_list is not None else [host]

        ebox = MagicMock()
        ebox.mCheckConfigOption.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (host_entries, ['domu-1'], [], [])
        ebox.mReturnDom0DomUNATPair.return_value = []
        ebox.mIsExabm.return_value = False
        ebox.mIsOciEXACC.return_value = skip_exacc
        ebox.isATP.return_value = False
        ebox.mIsKVM.return_value = False
        ebox.SharedEnv.return_value = False
        ebox.mGetUUID.return_value = 'uuid'
        ebox.mGetClusterPath.return_value = '/cluster'
        ebox.mGetClusterName.return_value = 'cluster-name'
        ebox.mGetCmd.return_value = 'other'
        ebox.mGetOedaPath.return_value = '/oeda'
        ebox.mExecuteCmdLog2.return_value = (['ok'], '')
        ebox.mUpdateErrorObject = MagicMock()
        ebox.mReleaseRemoteLock = MagicMock()

        cfg = config if config is not None else {}

        class DummyHealthCheck(object):
            def __init__(self, inner_ebox, cluster_hosts, cfg_map, rec_map, jmap):
                self._ebox = inner_ebox
                self._cluster_hosts = cluster_hosts
                self._config = cfg_map
                self._recommend = rec_map
                self._json_map = jmap
                self._log_handler = MagicMock()
                self._default_log_handler = MagicMock()

            def mGetEbox(self):
                return self._ebox

            def mGetClusterPath(self):
                return '/cluster'

            def mGetRecommend(self):
                return self._recommend

            def mGetJsonMap(self):
                return self._json_map

            def mGetLogHandler(self):
                return self._log_handler

            def mGetDefaultLogHandler(self):
                return self._default_log_handler

            def mGetClusterHostD(self):
                return self._cluster_hosts

            def mGetHcConfig(self):
                return self._config

        hc = DummyHealthCheck(ebox, cluster_host_d, cfg, recommend, json_map)
        options = SimpleNamespace(jsonconf={'dom0_verify': 'True'})
        test_obj = cluexachk(hc, options)
        return test_obj, options, hc, json_map, recommend, node, ebox

    # Auto-generated test for mSetupExachkEnv
    def test_mSetupExachkEnv_initializes_and_sets_passwordless(self):
        hc = MagicMock()
        ebox = MagicMock()
        hc.mGetEbox.return_value = ebox
        ssh_setup = MagicMock()

        with patch('exabox.healthcheck.cluexachk.ebCluSshSetup', return_value=ssh_setup) as mock_ssh_setup:
            test_obj = cluexachk(hc, MagicMock())
            test_obj.mSetupExachkEnv('dom0-host', ['domu-1', 'domu-2'])

        mock_ssh_setup.assert_called_once_with(ebox)
        ssh_setup.mSetSSHPasswordless.assert_called_once_with('dom0-host', ['domu-1', 'domu-2'])

    # Auto-generated test for mCleanupExachkEnv
    def test_mCleanupExachkEnv_uses_existing_setup(self):
        hc = MagicMock()
        ebox = MagicMock()
        hc.mGetEbox.return_value = ebox
        ssh_setup = MagicMock()

        with patch('exabox.healthcheck.cluexachk.ebCluSshSetup', return_value=ssh_setup):
            test_obj = cluexachk(hc, MagicMock())
            test_obj.mSetupExachkEnv('dom0-host', ['domu-1'])

        test_obj.mCleanupExachkEnv('dom0-host', ['domu-1'])
        ssh_setup.mCleanSSHPasswordless.assert_called_once_with('dom0-host', ['domu-1'])

    # Auto-generated test for mRemoteRunExachk
    def test_mRemoteRunExachk_handles_empty_host_list(self):
        test_obj, options, hc, json_map, recommend, node, ebox = self._create_remote_run_setup()
        ebox.mReturnAllClusterHosts.return_value = ([], ['domu-1'], [], [])

        json_map.clear()
        recommend[:] = []

        with patch('exabox.healthcheck.cluexachk.ebLogInfo') as mock_log, \
             patch('exabox.healthcheck.cluexachk.ebLogHealth') as mock_health, \
             patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'), \
             patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination') as mock_remove:
            test_obj.mRemoteRunExachk(options)

        self.assertEqual(json_map['Exachk']['hostCheck'], {})
        mock_log.assert_any_call('*** Completed Running exachk\n')
        mock_log.assert_any_call('WARNING: host list is empty for Exachk execution')
        mock_health.assert_any_call('WRN', 'No hosts provided for Exachk execution')
        mock_remove.assert_called_once_with('tmp_dest')

    # Auto-generated test for mRemoteRunExachk
    def test_mRemoteRunExachk_processes_domU_host(self):
        host = 'domu-1'
        test_obj, options, hc, json_map, recommend, node, ebox = self._create_remote_run_setup(host=host, host_list=[host])

        node.mGetNodeType.return_value = 'domu'
        options.jsonconf['domu_verify'] = 'True'
        with patch('exabox.healthcheck.cluexachk.datetime') as mock_datetime, \
             patch('exabox.healthcheck.cluexachk.os.makedirs') as mock_makedirs, \
             patch('exabox.healthcheck.cluexachk.os.stat', side_effect=FileNotFoundError()), \
             patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True), \
             patch('exabox.healthcheck.cluexachk.glob.glob', return_value=['/tmp/exachk.zip']), \
             patch('exabox.healthcheck.cluexachk.zipfile.ZipFile') as mock_zip:
            mock_datetime.now.return_value.strftime.return_value = '010203_040506'
            json_map.clear()
            recommend[:] = []

            test_obj.mRemoteRunExachk(options)

        mock_makedirs.assert_called()  # ensure output dir created
        self.assertIn(host, json_map['Exachk']['hostCheck'])
        # Logs key removed on success
        self.assertNotIn('logs', json_map['Exachk']['hostCheck'][host])
        self.assertEqual(json_map['Exachk']['hostCheck'][host]['TestResult'], 'Pass')
        mock_zip.assert_called_once_with('/tmp/exachk.zip')

    # Auto-generated test for mRunExachk
    def test_mRunExachk_skips_for_exacc(self):
        test_obj, options, _, _, _, _, _ = self._create_remote_run_setup(skip_exacc=True)

        with patch.dict('os.environ', {}, clear=True):
            with patch('exabox.healthcheck.cluexachk.ebLogInfo') as mock_log, \
                 patch.object(test_obj, 'mInstallAhf') as mock_install, \
                 patch.object(test_obj, 'mInstallAhfOnRemoteCps') as mock_remote_cps, \
                 patch.object(test_obj, 'mRemoteRunExachk') as mock_remote_run:
                test_obj.mRunExachk(options)

        mock_log.assert_any_call('AHF/Exack operations skipped for exacc')
        mock_install.assert_not_called()
        mock_remote_cps.assert_not_called()
        mock_remote_run.assert_not_called()

    # Auto-generated test for mRunExachk
    def test_mRunExachk_only_dom0_installation_skips_remote_flows(self):
        test_obj, options, _, _, _, _, _ = self._create_remote_run_setup()
        options.jsonconf['other'] = 'ahf_install_dom0'

        with patch.dict('os.environ', {}, clear=True):
            with patch.object(test_obj, 'mInstallAhf', return_value=None) as mock_install, \
                 patch.object(test_obj, 'mInstallAhfOnRemoteCps') as mock_remote_cps, \
                 patch.object(test_obj, 'mRemoteRunExachk') as mock_remote_run:
                test_obj.mRunExachk(options)

        mock_install.assert_called_once_with('dom0', options)
        mock_remote_cps.assert_not_called()
        mock_remote_run.assert_not_called()
        self.assertEqual(os.environ['RAT_ECRA'], '1')
        self.assertEqual(os.environ['RAT_ROOT_COLLECTIONS_IN_SERIAL'], '1')
        self.assertEqual(os.environ['RAT_NOCLEAN_DIR'], '1')

    # Auto-generated test for mRunExachk
    def test_mRunExachk_logs_and_raises_on_install_failure(self):
        class StrInstallError(str, Exception):
            pass

        test_obj, options, _, _, _, _, ebox = self._create_remote_run_setup()

        with patch.dict('os.environ', {}, clear=True):
            with patch.object(test_obj, 'mInstallAhf', side_effect=StrInstallError('install failed')) as mock_install, \
                 patch.object(test_obj, 'mInstallAhfOnRemoteCps') as mock_remote_cps, \
                 patch.object(test_obj, 'mRemoteRunExachk') as mock_remote_run, \
                 patch('exabox.healthcheck.cluexachk.ebLogError') as mock_log_error:
                with self.assertRaises(ExacloudRuntimeError):
                    test_obj.mRunExachk(options)

        mock_install.assert_called_once_with('dom0', options)
        mock_remote_cps.assert_not_called()
        mock_remote_run.assert_not_called()
        mock_log_error.assert_any_call('*** install failed')
        ebox.mUpdateErrorObject.assert_called_once()


    def test_ahf_install_on_domU_case1(self):
        ebLogInfo("Running unit test for cluexachk.")
        ebLogInfo("AHF install path /u01/oracle.ahf/data")

        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle.ahf/install.properties",aRc=0, aPersist=True),
                    exaMockCommand("/bin/grep 'DATA_DIR'*", aStdout="DATA_DIR=/u01/oracle.ahf/data\n TFA_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/tfa\n EXACHK_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/exachk\n", aRc=0, aPersist=True)
                ]
            ], 
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        _options = ebox.mGetArgsOptions()
        _options.healthcheck = "exachk"
        #aOptions.jsonconf
        ebox.mSetOptions(_options)
        _dom0s, _domUs, _cells, _switches = ebox.mReturnAllClusterHosts()
        aCluHealthCheck = "aCluHealthCheck"
        testObj = cluexachk(aCluHealthCheck,_options)
        node = exaBoxNode(self.mGetContext())
        node.mConnect(_domUs[0])
        _remote_ahf_install_path = ebox.mCheckSubConfigOption('ahf_paths', 'remote_ahf_install_path')
        _data_path = testObj.mRetriveAhfInstallDataPath(node,_remote_ahf_install_path)
        assert _data_path == "/u01/oracle.ahf/data\n"

    def test_ahf_install_on_domU_case2(self):
        ebLogInfo("Running unit test for cluexachk.")
        ebLogInfo("/opt/oracle.ahf/install.properties does not exist")


        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle.ahf/install.properties",aRc=1, aPersist=True),
                    exaMockCommand("/bin/grep 'DATA_DIR'*", aStdout="DATA_DIR=/u02/oracle.ahf/data\n", aRc=0, aPersist=True)
                ]
            ], 
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        _options = ebox.mGetArgsOptions()
        _options.healthcheck = "exachk"
        #aOptions.jsonconf
        ebox.mSetOptions(_options)
        _dom0s, _domUs, _cells, _switches = ebox.mReturnAllClusterHosts()
        aCluHealthCheck = "aCluHealthCheck"
        testObj = cluexachk(aCluHealthCheck,_options)
        node = exaBoxNode(self.mGetContext())
        node.mConnect(_domUs[0])
        _remote_ahf_install_path = ebox.mCheckSubConfigOption('ahf_paths', 'remote_ahf_install_path')
        _data_path = testObj.mRetriveAhfInstallDataPath(node,_remote_ahf_install_path)
        assert _data_path != "/u01/oracle.ahf/data\n"

    def test_ahf_install_on_domU_case3(self):
        ebLogInfo("Running unit test for cluexachk.")
        ebLogInfo("AHF install path /u02/oracle.ahf/data")

        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle.ahf/install.properties",aRc=0, aPersist=True),
                    exaMockCommand("/bin/grep 'DATA_DIR'*", aStdout="DATA_DIR=/u02/oracle.ahf/data\n TFA_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/tfa\n EXACHK_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/exachk\n", aRc=0, aPersist=True)
                ]
            ], 
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        _options = ebox.mGetArgsOptions()
        _options.healthcheck = "exachk"
        #aOptions.jsonconf
        ebox.mSetOptions(_options)
        _dom0s, _domUs, _cells, _switches = ebox.mReturnAllClusterHosts()
        aCluHealthCheck = "aCluHealthCheck"
        testObj = cluexachk(aCluHealthCheck,_options)
        node = exaBoxNode(self.mGetContext())
        node.mConnect(_domUs[0])
        _remote_ahf_install_path = ebox.mCheckSubConfigOption('ahf_paths', 'remote_ahf_install_path')
        _data_path = testObj.mRetriveAhfInstallDataPath(node,_remote_ahf_install_path)
        assert _data_path == "/u02/oracle.ahf/data\n"

    def test_ahf_install_on_cps(self):
        ebLogInfo("AHF install path cps")

        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle.ahf/install.properties",aRc=0, aPersist=True),
                    exaMockCommand("/bin/grep 'DATA_DIR'*", aStdout="DATA_DIR=/u02/oracle.ahf/data\n TFA_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/tfa\n EXACHK_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/exachk\n", aRc=0, aPersist=True)
                ]
            ], 
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        ebox.mSetOciExacc(True)
        _options = ebox.mGetArgsOptions()
        _options.healthcheck = "exachk"
        self.mGetContext().mSetConfigOption('remote_cps_host', 'iad163933exdcp02')
        #aOptions.jsonconf
        #ebox.mSetOptions(_options)
        _hcObj = ebCluHealthCheck(ebox, _options)
        testObj = cluexachk(_hcObj,_options)
        try:
            testObj.mInstallAhfOnRemoteCps(_options)
        except Exception as e:
            logger.info(f"Exception while Installing AHF: {e}")

    def test_mAhfCtrlPlaneVersionCheck(self):
        ebLogInfo("AHF install path cps")

        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle.ahf/install.properties",aRc=0, aPersist=True),
                    exaMockCommand("/bin/grep 'DATA_DIR'*", aStdout="DATA_DIR=/u02/oracle.ahf/data\n TFA_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/tfa\n EXACHK_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/exachk\n", aRc=0, aPersist=True)
                ]
            ], 
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        ebox.mSetOciExacc(True)
        _options = ebox.mGetArgsOptions()
        _options.healthcheck = "exachk"
        _hcObj = ebCluHealthCheck(ebox, _options)
        testObj = cluexachk(_hcObj,_options)
        #self.mGetContext().mSetConfigOption('remote_cps_host', 'iad163933exdcp02')
        #aOptions.jsonconf
        #ebox.mSetOptions(_options)
        if os.path.exists("./oracle.ahf/install.properties"):
            os.remove("./oracle.ahf/install.properties")
        if not os.path.exists("./oracle.ahf"):
            os.makedirs("./oracle.ahf")
        fd = open("./oracle.ahf/install.properties", "w+")
        fd.write("BUILD_VERSION=214300")
        fd.close()
        try:
            testObj.mAhfCtrlPlaneVersionCheck(".",".")
        except Exception as e:
            logger.error('*** AHF install failed on control plane with exception : %s' % (str(e)))

    # Auto-generated test for mAhfCtrlPlaneVersionCheck
    # Auto-generated test for mAhfCtrlPlaneVersionCheck
    def test_mAhfCtrlPlaneVersionCheck_upgrade_required(self):
        ebox = MagicMock()
        ebox.mExecuteCmd.return_value = (None, ['properties'], None)
        ebox.mExecuteCmdLog2.side_effect = [
            (['BUILD_VERSION=214300'], ''),
            (['BUILD_DATE=20250101'], ''),
        ]

        hc = MagicMock()
        hc.mGetEbox.return_value = ebox
        test_obj = cluexachk(hc, MagicMock())

        with patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True), \
             patch.object(test_obj, 'mGetAhfBinVerFromCtrlPlane', return_value=21430020260101) as mock_get_version:
            result = test_obj.mAhfCtrlPlaneVersionCheck('/tmp/ahf_setup', '/tmp/install')

        self.assertTrue(result)
        mock_get_version.assert_called_once_with('/tmp/ahf_setup')
        self.assertEqual(ebox.mExecuteCmdLog2.call_count, 2)

    # Auto-generated test for mAhfCtrlPlaneVersionCheck
    def test_mAhfCtrlPlaneVersionCheck_upgrade_not_required(self):
        ebox = MagicMock()
        ebox.mExecuteCmd.return_value = (None, ['properties'], None)
        ebox.mExecuteCmdLog2.side_effect = [
            (['BUILD_VERSION=214300'], ''),
            (['BUILD_DATE=20250101'], ''),
        ]

        hc = MagicMock()
        hc.mGetEbox.return_value = ebox
        test_obj = cluexachk(hc, MagicMock())

        with patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True), \
             patch.object(test_obj, 'mGetAhfBinVerFromCtrlPlane', return_value=21430020250101) as mock_get_version:
            result = test_obj.mAhfCtrlPlaneVersionCheck('/tmp/ahf_setup', '/tmp/install')

        self.assertFalse(result)
        mock_get_version.assert_called_once_with('/tmp/ahf_setup')
        self.assertEqual(ebox.mExecuteCmdLog2.call_count, 2)

    def test_mGetHigherAHFPath(self):
        """
        CP ahf_setup path is set wrong to test file not found flow
        this shall return version as 0 if file not found
        """
        ebLogInfo("AHF install path cps")
        _cntrlPlanePath = ''

        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /opt/oracle.ahf/install.properties",aRc=0, aPersist=True),
                    exaMockCommand("/bin/grep 'DATA_DIR'*", aStdout="DATA_DIR=/u02/oracle.ahf/data\n TFA_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/tfa\n EXACHK_DATA_DIR=/u02/oracle.ahf/data/scas22dv0308m/exachk\n", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /var/opt/oracle/misc/ahf/ahf_setup", aRc=0, aPersist=True),
                    exaMockCommand("/var/opt/oracle/misc/ahf/ahf_setup -v", aStdout="AHF Build ID : 23200020230302111526\n AHF Build Platform : Linux\n AHF Build Architecture : x86_64\n", aRc=0, aPersist=True)
                ]
            ], 
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ],
            self.mGetRegexLocal(): [
                exaMockCommand(f"{_cntrlPlanePath} -v", aStdout="AHF Build ID : 22330020230116220213\n AHF Build Platform : Linux\n AHF Build Architecture : x86_64\n", aRc=0, aPersist=True)
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        _dom0s, _domUs, _cells, _switches = ebox.mReturnAllClusterHosts()
        node = exaBoxNode(self.mGetContext())
        node.mConnect(_domUs[0])
        _options = ebox.mGetArgsOptions()
        _options.healthcheck = "exachk"
        _hcObj = ebCluHealthCheck(ebox, _options)
        testObj = cluexachk(_hcObj,_options)
        _path = testObj.mGetHigherAHFPath(node, _cntrlPlanePath)
        ebLogInfo(f'Selected AHF path: {_path}')
        assert _path == ebox.mCheckSubConfigOption('ahf_paths', 'remote_ahf_dbaas_path')


    def test_mCopyAhfImage(self):
        ebLogInfo("ahf_setup file copy to remote node")
        _ahf_bin_path = os.getcwd()
        _remote_ahf_bin_path = "/opt/oracle.SupportTools/ahf/ahf_setup"

        #Create args structure
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("df -PBM",aRc=0, aPersist=True),
                    exaMockCommand("rm -rf*", aRc=0, aPersist=True),
                    exaMockCommand("mkdir*", aRc=0, aPersist=True),
                    exaMockCommand("scp *", aRc=0, aPersist=True),
                    exaMockCommand("/bin/test -e /opt/oracle.SupportTools/ahf/ahf_setup", aRc=0, aPersist=True),
                    exaMockCommand("chmod 700*", aRc=0, aPersist=True)
                ]
            ], 
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("virsh nodememstats.*free", aStdout="free : 193987172\ncached : 0")
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        ebox = self.mGetClubox()
        _dom0s, _domUs, _cells, _switches = ebox.mReturnAllClusterHosts()
        _options = ebox.mGetArgsOptions()
        _options.healthcheck = "exachk"
        _hcObj = ebCluHealthCheck(ebox, _options)
        testObj = cluexachk(_hcObj,_options)
        node = exaBoxNode(self.mGetContext())
        node.mConnect(_domUs[0])
        with patch('os.path.isfile'):
            _ret = testObj.mCopyAhfImage(node,_ahf_bin_path,_remote_ahf_bin_path)
        assert _ret != 0

    # Auto-generated test for FileLockMgr.check_and_create_file
    def test_FileLockMgr_check_and_create_file_creates_when_missing(self):
        mgr = object.__new__(FileLockMgr)
        mgr.lockfile = '/tmp/exachk.lock'

        with patch('exabox.healthcheck.cluexachk.os.path.exists', return_value=False) as mock_exists, \
             patch('exabox.healthcheck.cluexachk.Path.touch') as mock_touch:
            mgr.check_and_create_file()

        mock_exists.assert_called_with('/tmp/exachk.lock')
        mock_touch.assert_called_once()

    # Auto-generated test for FileLockMgr.check_and_create_file
    def test_FileLockMgr_check_and_create_file_skips_when_present(self):
        mgr = object.__new__(FileLockMgr)
        mgr.lockfile = '/tmp/exachk.lock'

        with patch('exabox.healthcheck.cluexachk.os.path.exists', return_value=True) as mock_exists, \
             patch('exabox.healthcheck.cluexachk.Path.touch') as mock_touch:
            mgr.check_and_create_file()

        mock_exists.assert_called_with('/tmp/exachk.lock')
        mock_touch.assert_not_called()

    # Auto-generated test for FileLockMgr.file_lock
    def test_FileLockMgr_file_lock_shared_success(self):
        mgr = object.__new__(FileLockMgr)
        mgr.lockfile = '/tmp/exachk.lock'
        mgr.fd = 0
        mock_file = MagicMock()
        mock_file.fileno.return_value = 42

        with patch('builtins.open', return_value=mock_file) as mock_open_obj, \
             patch('exabox.healthcheck.cluexachk.fcntl.flock') as mock_flock, \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'):
            result = mgr.file_lock(LockMode.SHARED)

        self.assertTrue(result)
        mock_open_obj.assert_called_with('/tmp/exachk.lock', 'r')
        mock_file.flush.assert_called_once()
        mock_flock.assert_called_once()
        mgr.fd = 0

    # Auto-generated test for FileLockMgr.file_lock
    def test_FileLockMgr_file_lock_exclusive_success(self):
        mgr = object.__new__(FileLockMgr)
        mgr.lockfile = '/tmp/exachk.lock'
        mgr.fd = 0
        mock_file = MagicMock()
        mock_file.fileno.return_value = 99

        with patch('builtins.open', return_value=mock_file) as mock_open_obj, \
             patch('exabox.healthcheck.cluexachk.fcntl.flock') as mock_flock, \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'):
            result = mgr.file_lock(LockMode.EXCLUSIVE)

        self.assertTrue(result)
        mock_open_obj.assert_called_with('/tmp/exachk.lock', 'w')
        mock_file.flush.assert_called_once()
        mock_flock.assert_called_once()
        mgr.fd = 0

    # Auto-generated test for FileLockMgr.file_lock
    def test_FileLockMgr_file_lock_handles_exception(self):
        mgr = object.__new__(FileLockMgr)
        mgr.lockfile = '/tmp/exachk.lock'
        mgr.fd = 0

        with patch('builtins.open', side_effect=OSError('open failed')), \
             patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error:
            result = mgr.file_lock(LockMode.EXCLUSIVE)

        self.assertFalse(result)
        mock_error.assert_called()

    # Auto-generated test for obtain_cp_lock
    def test_obtain_cp_lock_acquires_and_releases(self):
        mock_mgr = MagicMock()
        mock_mgr.file_lock.return_value = True
        mock_mgr.fd = MagicMock()
        mock_mgr.fd.fileno.return_value = 55

        with patch('exabox.healthcheck.cluexachk.FileLockMgr', return_value=mock_mgr), \
             patch('exabox.healthcheck.cluexachk.fcntl.flock') as mock_flock, \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'):
            with obtain_cp_lock('/tmp/exachk.lock', LockMode.SHARED) as acquired:
                self.assertTrue(acquired)

        mock_mgr.file_lock.assert_called_once_with(LockMode.SHARED)
        self.assertEqual(mock_flock.call_count, 1)

    # Auto-generated test for obtain_cp_lock
    def test_obtain_cp_lock_handles_creation_error(self):
        with patch('exabox.healthcheck.cluexachk.FileLockMgr', side_effect=Exception('fail')), \
             patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error:
            with obtain_cp_lock('/tmp/exachk.lock', LockMode.EXCLUSIVE) as acquired:
                self.assertFalse(acquired)

        mock_error.assert_called()

    # Auto-generated test for obtain_remote_lock
    def test_obtain_remote_lock_acquires_and_releases_on_shared_env(self):
        ebox = MagicMock()
        ebox.SharedEnv.return_value = True

        with obtain_remote_lock(ebox) as yielded:
            self.assertIs(yielded, ebox)

        ebox.mAcquireRemoteLock.assert_called_once()
        ebox.mReleaseRemoteLock.assert_called_once()

    # Auto-generated test for obtain_remote_lock
    def test_obtain_remote_lock_skips_when_not_shared(self):
        ebox = MagicMock()
        ebox.SharedEnv.return_value = False

        with obtain_remote_lock(ebox) as yielded:
            self.assertIs(yielded, ebox)

        ebox.mAcquireRemoteLock.assert_not_called()
        ebox.mReleaseRemoteLock.assert_not_called()


    # Auto-generated test for mAhfUninstall
    def test_mAhfUninstall_success_and_failure_paths(self):
        hc = MagicMock()
        hc.mGetEbox.return_value = MagicMock()
        test_obj = cluexachk(hc, MagicMock())

        uninstall_stream = MagicMock()
        uninstall_stream.readlines.return_value = ['ok']
        remove_stream = MagicMock()
        remove_stream.readlines.return_value = ['deleted']
        node_success = MagicMock()
        node_success.mGetHostname.return_value = 'domu-1'
        node_success.mFileExists.side_effect = [True, True]
        node_success.mExecuteCmd.side_effect = [
            (None, uninstall_stream, None),
            (None, remove_stream, None),
        ]
        node_success.mGetCmdExitStatus.side_effect = [False, False]

        with patch('exabox.healthcheck.cluexachk.ebLogHealth') as mock_health, \
             patch('exabox.healthcheck.cluexachk.ebLogInfo') as mock_info:
            result = test_obj.mAhfUninstall(node_success, '/remote/install')

        self.assertTrue(result)
        node_success.mExecuteCmd.assert_has_calls([
            call('/remote/install/oracle.ahf/ahf/bin/uninstallahf.sh -silent -local'),
            call('rm -rf /remote/install/oracle.ahf'),
        ])
        mock_health.assert_any_call('NFO','*** AHF : Uninstallation Success. command output for host : domu-1')
        mock_info.assert_any_call('*** AHF: ahf install directory /remote/install/oracle.ahf deleted for host: domu-1')

        error_stream = MagicMock()
        error_stream.readlines.return_value = ['failure']
        node_failure = MagicMock()
        node_failure.mGetHostname.return_value = 'domu-1'
        node_failure.mFileExists.side_effect = [True, False]
        node_failure.mExecuteCmd.return_value = (None, error_stream, None)
        node_failure.mGetCmdExitStatus.return_value = True

        with patch('exabox.healthcheck.cluexachk.ebLogWarn') as mock_warn, \
             patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error:
            result = test_obj.mAhfUninstall(node_failure, '/remote/install')

        self.assertFalse(result)
        mock_warn.assert_called_with('*** AHF: Unable to uninstall Ahf, binary not found for host: domu-1')
        mock_error.assert_called_with('*** AHF: Unable to delete ahf install directory /remote/install/oracle.ahf for host: domu-1')

    # Auto-generated test for mChgFolderOwnShip
    def test_mChgFolderOwnShip_success_and_error(self):
        test_obj = cluexachk(MagicMock(), MagicMock())

        node_success = MagicMock()
        node_success.mGetHostname.return_value = 'domu-2'
        node_success.mGetCmdExitStatus.return_value = False
        with patch('exabox.healthcheck.cluexachk.ebLogInfo') as mock_info:
            result = test_obj.mChgFolderOwnShip(node_success, '/opt/oracle/ahf', 'root', 'root')

        self.assertTrue(result)
        node_success.mExecuteCmd.assert_called_once_with('chown root:root /opt')
        mock_info.assert_any_call('*** Base directory /opt ownership changed to root:root for host: domu-2')

        error_stream = MagicMock()
        error_stream.readlines.return_value = ['failure']
        node_failure = MagicMock()
        node_failure.mGetHostname.return_value = 'domu-err'
        node_failure.mExecuteCmd.return_value = (None, None, error_stream)
        node_failure.mGetCmdExitStatus.return_value = True
        with patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error:
            result = test_obj.mChgFolderOwnShip(node_failure, '/opt/oracle/ahf', 'root', 'root')

        self.assertFalse(result)
        mock_error.assert_called_with('*** change folder ownership failed for host domu-err with error: [\'failure\']')

    # Auto-generated test for mInstallAhfOnRemoteCps
    def test_mInstallAhfOnRemoteCps_handles_missing_host_and_success(self):
        ebox = MagicMock()
        ebox.mGetOciExacc.return_value = True
        hc = MagicMock()
        hc.mGetEbox.return_value = ebox
        options = SimpleNamespace(jsonconf={})
        test_obj = cluexachk(hc, options)

        ebox.mCheckConfigOption.return_value = None
        with patch('exabox.healthcheck.cluexachk.ebLogWarn') as mock_warn:
            result = test_obj.mInstallAhfOnRemoteCps(options)

        self.assertIsNone(result)
        mock_warn.assert_called_with('*** Remote CPS not configured, AHF installation on remote cps is skipped')

        ebox.mCheckConfigOption.return_value = 'remote-cps'
        context = MagicMock()
        context.mGetBasePath.return_value = '/base'
        fake_node = MagicMock()
        with patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=context), \
             patch('exabox.healthcheck.cluexachk.connect_to_host') as mock_connect, \
             patch.object(test_obj, 'mSetupAhfonRemote', return_value=True) as mock_setup:
            conn_ctx = MagicMock()
            conn_ctx.__enter__.return_value = fake_node
            conn_ctx.__exit__.return_value = False
            mock_connect.return_value = conn_ctx

            result = test_obj.mInstallAhfOnRemoteCps(options)

        self.assertIsNone(result)
        mock_connect.assert_called_once_with('remote-cps', context)
        mock_setup.assert_called_once_with(
            fake_node,
            'standby_cps',
            '/base/ahf_setup',
            '/base',
            '/base/ahf_install',
            '/base/ahf_install'
        )

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_logs_error_for_invalid_device(self):
        hc = MagicMock()
        ebox = MagicMock()
        hc.mGetEbox.return_value = ebox
        test_obj = cluexachk(hc, MagicMock())

        with patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error:
            result = test_obj.mInstallAhf('switch', MagicMock())

        self.assertIsNone(result)
        mock_error.assert_called_once_with('*** AHF: Wrong device type given. It should be dom0 or domU')

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_requires_absolute_paths(self):
        hc = MagicMock()
        ebox = MagicMock()
        hc.mGetEbox.return_value = ebox

        ebox.mCheckSubConfigOption.side_effect = lambda section, key: {
            ('ahf_paths', 'remote_ahf_bin_path'): '/remote/bin',
            ('ahf_paths', 'remote_ahf_data_path_dom0'): 'relative/path',
        }[(section, key)]
        ebox.mCheckConfigOption.return_value = False

        test_obj = cluexachk(hc, MagicMock())

        with patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error, \
             patch('exabox.healthcheck.cluexachk.get_gcontext') as mock_ctx:
            mock_ctx.return_value.mGetBasePath.return_value = '/base/'
            result = test_obj.mInstallAhf('dom0', SimpleNamespace(jsonconf=None))

        self.assertIsNone(result)
        mock_error.assert_called_once_with('*** AHF: Absolute install path / data path not given for AHF installation')

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_dom0_uses_remote_lock_and_filters_host(self):
        hc = MagicMock()
        ebox = MagicMock()
        hc.mGetEbox.return_value = ebox
        hc.mGetLogHandler.return_value = MagicMock()
        hc.mGetDefaultLogHandler.return_value = MagicMock()

        ebox.mCheckSubConfigOption.side_effect = lambda section, key: {
            ('ahf_paths', 'remote_ahf_bin_path'): '/remote/bin',
            ('ahf_paths', 'remote_ahf_data_path_dom0'): '/remote/data',
        }[(section, key)]
        ebox.mCheckConfigOption.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-1', 'dom0-2'], ['domu-1'], [], [])
        ebox.mIsExaScale.return_value = False

        context = MagicMock()
        context.mGetBasePath.return_value = '/base/'

        node = MagicMock()
        node.mSetUser.return_value = None
        node.mConnectTimed.return_value = None

        class FakeProcessStructure(object):
            def __init__(self, func, args):
                self.func = func
                self.args = args
            def mSetMaxExecutionTime(self, *args, **kwargs):
                return None
            def mSetJoinTimeout(self, *args, **kwargs):
                return None
            def mSetLogTimeoutFx(self, *args, **kwargs):
                return None

        class FakeProcessManager(object):
            def __init__(self):
                self.structures = []
            def mStartAppend(self, structure):
                self.structures.append(structure)
                structure.func(*structure.args)
            def mJoinProcess(self):
                return None

        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        with patch('exabox.healthcheck.cluexachk.ProcessStructure', FakeProcessStructure), \
             patch('exabox.healthcheck.cluexachk.ProcessManager', FakeProcessManager), \
             patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=context), \
             patch('exabox.healthcheck.cluexachk.exaBoxNode', return_value=node), \
             patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'), \
             patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'), \
             patch.object(test_obj, 'mSetupAhfonRemote', return_value=True) as mock_setup_remote:
            result = test_obj.mInstallAhf('dom0', test_obj.mGetCluHealthCheck().mGetEbox(), _selected_host='dom0-2')

        self.assertEqual(result, {'dom0-2': True})
        mock_setup_remote.assert_called_once()
        called_node = mock_setup_remote.call_args[0][0]
        self.assertIs(called_node, node)
        ebox.mAcquireRemoteLock.assert_called_once()
        ebox.mReleaseRemoteLock.assert_called_once()

    # Auto-generated test for mInstallAhf
    def test_mInstallAhf_domu_exascale_uses_exascale_install(self):
        hc = MagicMock()
        ebox = MagicMock()
        hc.mGetEbox.return_value = ebox
        hc.mGetLogHandler.return_value = MagicMock()
        hc.mGetDefaultLogHandler.return_value = MagicMock()

        ebox.mCheckSubConfigOption.side_effect = lambda section, key: {
            ('ahf_paths', 'remote_ahf_bin_path'): '/remote/bin',
            ('ahf_paths', 'remote_ahf_data_path_domu'): '/remote/data',
        }[(section, key)]
        ebox.mCheckConfigOption.return_value = False
        ebox.mReturnAllClusterHosts.return_value = (['dom0-1'], ['domu-1'], [], [])
        ebox.mIsExaScale.return_value = True

        context = MagicMock()
        context.mGetBasePath.return_value = '/base/'

        node = MagicMock()
        node.mSetUser.return_value = None
        node.mConnectTimed.return_value = None

        class FakeProcessStructure(object):
            def __init__(self, func, args):
                self.func = func
                self.args = args
            def mSetMaxExecutionTime(self, *args, **kwargs):
                return None
            def mSetJoinTimeout(self, *args, **kwargs):
                return None
            def mSetLogTimeoutFx(self, *args, **kwargs):
                return None

        class FakeProcessManager(object):
            def __init__(self):
                self.structures = []
            def mStartAppend(self, structure):
                self.structures.append(structure)
                structure.func(*structure.args)
            def mJoinProcess(self):
                return None

        test_obj = cluexachk(hc, SimpleNamespace(jsonconf={'ahf_install_path': '/install'}))

        with patch('exabox.healthcheck.cluexachk.ProcessStructure', FakeProcessStructure), \
             patch('exabox.healthcheck.cluexachk.ProcessManager', FakeProcessManager), \
             patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=context), \
             patch('exabox.healthcheck.cluexachk.exaBoxNode', return_value=node), \
             patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'), \
             patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'), \
             patch.object(test_obj, 'mSetupAhfonExascale', return_value=True) as mock_setup_exascale, \
             patch.object(test_obj, 'mSetupAhfonRemote') as mock_setup_remote:
            result = test_obj.mInstallAhf('domU', test_obj.mGetCluHealthCheck().mGetEbox())

        self.assertEqual(result, {'domu-1': True})
        mock_setup_exascale.assert_called_once()
        mock_setup_remote.assert_not_called()
        ebox.mAcquireRemoteLock.assert_not_called()
        ebox.mReleaseRemoteLock.assert_not_called()

    # Auto-generated test for mDeleteAhfImage
    def test_mDeleteAhfImage_skips_when_file_missing(self):
        testObj = cluexachk(MagicMock(), MagicMock())
        testObj.ahf_copy_path = '/tmp/ahf_setup'
        node = MagicMock()
        node.mFileExists.return_value = False
        with patch('exabox.healthcheck.cluexachk.ebLogInfo') as mock_info:
            testObj.mDeleteAhfImage(node)
            node.mExecuteCmd.assert_not_called()
            node.mGetCmdExitStatus.assert_not_called()
            mock_info.assert_any_call('ahf_setup file not present in path:/tmp/ahf_setup, skipping removal')

    # Auto-generated test for mDeleteAhfImage
    def test_mDeleteAhfImage_removes_when_present(self):
        testObj = cluexachk(MagicMock(), MagicMock())
        testObj.ahf_copy_path = '/tmp/ahf_setup'
        node = MagicMock()
        node.mFileExists.return_value = True
        node.mGetCmdExitStatus.return_value = False
        node.mGetHostname.return_value = 'domu-host'
        with patch('exabox.healthcheck.cluexachk.ebLogInfo') as mock_info:
            testObj.mDeleteAhfImage(node)
        node.mExecuteCmd.assert_called_once_with('rm /tmp/ahf_setup')
        node.mGetCmdExitStatus.assert_called_once()
        mock_info.assert_any_call('ahf_setup deleted from host :domu-host')

    # Auto-generated test for mDeleteAhfImage
    def test_mDeleteAhfImage_logs_error_on_failure(self):
        testObj = cluexachk(MagicMock(), MagicMock())
        testObj.ahf_copy_path = '/var/tmp/ahf_setup'
        node = MagicMock()
        node.mFileExists.return_value = True
        node.mGetCmdExitStatus.return_value = True
        node.mGetHostname.return_value = 'domu-error'
        with patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error:
            testObj.mDeleteAhfImage(node)
            node.mExecuteCmd.assert_called_once_with('rm /var/tmp/ahf_setup')
            node.mGetCmdExitStatus.assert_called_once()
            mock_error.assert_called_with('*** Could not delete ahf_setup for host - domu-error')

    # Auto-generated test for mDeleteAhfImage
    def test_mDeleteAhfImage_handles_exception(self):
        testObj = cluexachk(MagicMock(), MagicMock())
        testObj.ahf_copy_path = '/var/tmp/ahf_setup'
        node = MagicMock()
        node.mFileExists.side_effect = Exception('failure')
        node.mGetHostname.return_value = 'domu-exception'
        with patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error:
            testObj.mDeleteAhfImage(node)
            mock_error.assert_called()
            self.assertIn('failure', mock_error.call_args[0][0])

    # Auto-generated test for mRemoveOldExachk
    def test_mRemoveOldExachk_skips_when_not_present(self):
        test_obj = cluexachk(MagicMock(), MagicMock())
        node = MagicMock()
        node.mFileExists.return_value = False

        test_obj.mRemoveOldExachk(node)

        node.mExecuteCmd.assert_not_called()
        node.mGetCmdExitStatus.assert_not_called()

    # Auto-generated test for mRemoveOldExachk
    def test_mRemoveOldExachk_deletes_when_present(self):
        test_obj = cluexachk(MagicMock(), MagicMock())
        node = MagicMock()
        node.mFileExists.return_value = True
        node.mGetCmdExitStatus.return_value = False
        node.mGetHostname.return_value = 'dom0-host'

        with patch('exabox.healthcheck.cluexachk.ebLogInfo') as mock_info:
            test_obj.mRemoveOldExachk(node)

        node.mExecuteCmd.assert_called_once_with('rm -rf /opt/oracle.SupportTools/exachk')
        node.mGetCmdExitStatus.assert_called_once()
        mock_info.assert_called_with('*** AHF: old exachk version found and deleted on path /opt/oracle.SupportTools/exachk for host: dom0-host')

    # Auto-generated test for mRemoveOldExachk
    def test_mRemoveOldExachk_logs_error_on_failure(self):
        test_obj = cluexachk(MagicMock(), MagicMock())
        node = MagicMock()
        node.mFileExists.return_value = True
        node.mGetCmdExitStatus.return_value = True
        node.mGetHostname.return_value = 'dom0-error'

        with patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error:
            test_obj.mRemoveOldExachk(node)

        node.mExecuteCmd.assert_called_once_with('rm -rf /opt/oracle.SupportTools/exachk')
        node.mGetCmdExitStatus.assert_called_once()
        mock_error.assert_called_with('*** AHF: old exachk version found but, could not delete on path /opt/oracle.SupportTools/exachk for host: dom0-error')

    # Auto-generated test for mRemoveOldExachk
    def test_mRemoveOldExachk_handles_exception(self):
        test_obj = cluexachk(MagicMock(), MagicMock())
        node = MagicMock()
        node.mFileExists.side_effect = Exception('boom')
        node.mGetHostname.return_value = 'dom0-exception'

        with patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error:
            test_obj.mRemoveOldExachk(node)

        mock_error.assert_called_with('*** AHF: old exachk version detection on path /opt/oracle.SupportTools/exachk for host failed : dom0-exception')

    # Auto-generated test for mGetTFACTLStatus
    def test_mGetTFACTLStatus_reads_status_when_tfa_home_present(self):
        hc = MagicMock()
        hc.mGetEbox.return_value = MagicMock()
        test_obj = cluexachk(hc, MagicMock())

        props_stream = MagicMock()
        props_stream.readlines.return_value = [
            'DATA_DIR=/u01/oracle.ahf/data\n',
            'TFA_HOME=/opt/tfa\n',
        ]
        status_stream = MagicMock()
        status_stream.readlines.return_value = ['Service ONLINE\n', 'Daemon RUNNING\n']

        node = MagicMock()
        node.mFileExists.return_value = True
        node.mExecuteCmd.side_effect = [
            (None, props_stream, None),
            (None, status_stream, None),
        ]

        with patch('exabox.healthcheck.cluexachk.ebLogInfo') as mock_info:
            result = test_obj.mGetTFACTLStatus('/remote/install', node)

        self.assertTrue(result)
        node.mExecuteCmd.assert_has_calls([
            call('/bin/cat /remote/install/oracle.ahf/install.properties'),
            call('/opt/tfa/bin/tfactl print status'),
        ])
        logged_lines = [args[0] for args, _ in mock_info.call_args_list]
        self.assertIn('Service ONLINE', ''.join(logged_lines))
        self.assertIn('Daemon RUNNING', ''.join(logged_lines))

    # Auto-generated test for mGetTFACTLStatus
    def test_mGetTFACTLStatus_returns_false_without_tfa_home(self):
        hc = MagicMock()
        hc.mGetEbox.return_value = MagicMock()
        test_obj = cluexachk(hc, MagicMock())

        props_stream = MagicMock()
        props_stream.readlines.return_value = ['DATA_DIR=/u01/oracle.ahf/data\n']

        node = MagicMock()
        node.mFileExists.return_value = True
        node.mExecuteCmd.return_value = (None, props_stream, None)

        result = test_obj.mGetTFACTLStatus('/remote/install', node)

        self.assertFalse(result)
        node.mExecuteCmd.assert_called_once_with('/bin/cat /remote/install/oracle.ahf/install.properties')

    # Auto-generated test for mAhfRemoteVersionCheck
    def test_mAhfRemoteVersionCheck_requests_upgrade_when_local_newer(self):
        hc = MagicMock()
        hc.mGetEbox.return_value = MagicMock()
        test_obj = cluexachk(hc, MagicMock())

        version_stream = MagicMock()
        version_stream.readlines.return_value = ['BUILD_VERSION=214300\n']
        date_stream = MagicMock()
        date_stream.readlines.return_value = ['BUILD_DATE=20240101\n']

        node = MagicMock()
        node.mFileExists.return_value = True
        node.mExecuteCmd.side_effect = [
            (None, version_stream, None),
            (None, date_stream, None),
        ]
        node.mGetHostname.return_value = 'domu-1'

        with patch.object(test_obj, 'mGetAhfBinVerFromCtrlPlane', return_value=21430020250101) as mock_get_version:
            upgrade, fresh = test_obj.mAhfRemoteVersionCheck(node, '/ctrl/bin/ahf_setup', '/remote/install')

        self.assertTrue(upgrade)
        self.assertFalse(fresh)
        mock_get_version.assert_called_once_with('/ctrl/bin/ahf_setup')

    # Auto-generated test for mAhfRemoteVersionCheck
    def test_mAhfRemoteVersionCheck_skips_upgrade_when_remote_newer(self):
        hc = MagicMock()
        hc.mGetEbox.return_value = MagicMock()
        test_obj = cluexachk(hc, MagicMock())

        version_stream = MagicMock()
        version_stream.readlines.return_value = ['BUILD_VERSION=214300\n']
        date_stream = MagicMock()
        date_stream.readlines.return_value = ['BUILD_DATE=20250101\n']

        node = MagicMock()
        node.mFileExists.return_value = True
        node.mExecuteCmd.side_effect = [
            (None, version_stream, None),
            (None, date_stream, None),
        ]
        node.mGetHostname.return_value = 'domu-2'

        with patch.object(test_obj, 'mGetAhfBinVerFromCtrlPlane', return_value=21430020240101) as mock_get_version:
            upgrade, fresh = test_obj.mAhfRemoteVersionCheck(node, '/ctrl/bin/ahf_setup', '/remote/install', _device_type='standby_cps')

        self.assertFalse(upgrade)
        self.assertFalse(fresh)
        mock_get_version.assert_called_once_with('/ctrl/bin/ahf_setup', node)

    # Auto-generated test for mAhfRemoteVersionCheck
    def test_mAhfRemoteVersionCheck_marks_fresh_install_when_missing(self):
        hc = MagicMock()
        hc.mGetEbox.return_value = MagicMock()
        test_obj = cluexachk(hc, MagicMock())

        node = MagicMock()
        node.mFileExists.return_value = False
        node.mGetHostname.return_value = 'domu-3'

        with patch.object(test_obj, 'mGetAhfBinVerFromCtrlPlane') as mock_get_version:
            upgrade, fresh = test_obj.mAhfRemoteVersionCheck(node, '/ctrl/bin/ahf_setup', '/remote/install')

        self.assertTrue(upgrade)
        self.assertTrue(fresh)
        mock_get_version.assert_not_called()

    # Auto-generated test for mSetupAhfonCtrlPlane
    def test_mSetupAhfonCtrlPlane_returns_true_when_upgrade_not_required(self):
        ebox = MagicMock()
        hc = MagicMock()
        hc.mGetEbox.return_value = ebox
        test_obj = cluexachk(hc, MagicMock())

        with patch.object(test_obj, 'mAhfCtrlPlaneVersionCheck', return_value=False) as mock_version:
            result = test_obj.mSetupAhfonCtrlPlane('/ctrl/bin/ahf_setup', '/install/path')

        self.assertTrue(result)
        mock_version.assert_called_once_with('/ctrl/bin/ahf_setup', '/install/path')

    # Auto-generated test for mSetupAhfonCtrlPlane
    def test_mSetupAhfonCtrlPlane_returns_false_when_binary_missing(self):
        ebox = MagicMock()
        hc = MagicMock()
        hc.mGetEbox.return_value = ebox
        test_obj = cluexachk(hc, MagicMock())

        with patch.object(test_obj, 'mAhfCtrlPlaneVersionCheck', return_value=True), \
             patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=False), \
             patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error:
            result = test_obj.mSetupAhfonCtrlPlane('/ctrl/bin/ahf_setup', '/install/path')

        self.assertFalse(result)
        mock_error.assert_called_with('*** AHF: ahf binary not preset in ctrl plane at path /ctrl/bin/ahf_setup ')

    # Auto-generated test for mSetupAhfonCtrlPlane
    def test_mSetupAhfonCtrlPlane_installs_when_upgrade_needed(self):
        ebox = MagicMock()
        ebox.mExecuteCmdLog2.return_value = (['success'], [])
        hc = MagicMock()
        hc.mGetEbox.return_value = ebox
        test_obj = cluexachk(hc, MagicMock())

        @contextmanager
        def fake_lock(*args, **kwargs):
            yield True

        context = MagicMock()
        context.mGetBasePath.return_value = '/base'

        with patch.object(test_obj, 'mAhfCtrlPlaneVersionCheck', return_value=True), \
             patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True), \
             patch('exabox.healthcheck.cluexachk.os.stat', side_effect=FileNotFoundError()), \
             patch('exabox.healthcheck.cluexachk.os.mkdir') as mock_mkdir, \
             patch('exabox.healthcheck.cluexachk.obtain_cp_lock', fake_lock), \
             patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=context), \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch('exabox.healthcheck.cluexachk.ebLogHealth'):
            result = test_obj.mSetupAhfonCtrlPlane('/ctrl/bin/ahf_setup', '/install/path', '/tmpdir')

        self.assertTrue(result)
        mock_mkdir.assert_called_once_with('/install/path')
        ebox.mExecuteCmdLog2.assert_called_once()

    # Auto-generated test for mSetupAhfonExascale
    def test_mSetupAhfonExascale_returns_true_when_all_steps_succeed(self):
        ebox = MagicMock()
        ebox.isATP.return_value = False
        hc = MagicMock()
        hc.mGetEbox.return_value = ebox
        test_obj = cluexachk(hc, MagicMock())

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-1'
        stdout = MagicMock()
        stdout.readlines.return_value = ['log line']
        node.mExecuteCmd.return_value = (None, stdout, None)
        node.mGetCmdExitStatus.return_value = False

        with patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]) as mock_chg, \
             patch.object(test_obj, 'mCopyAhfImage', return_value=True) as mock_copy, \
             patch.object(test_obj, 'mGetTFACTLStatus', return_value=True), \
             patch.object(test_obj, 'mDeleteAhfImage') as mock_delete, \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch('exabox.healthcheck.cluexachk.ebLogWarn'), \
             patch('exabox.healthcheck.cluexachk.ebLogError'), \
             patch('exabox.healthcheck.cluexachk.ebLogHealth'):
            result = test_obj.mSetupAhfonExascale(
                node,
                'domU',
                '/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertTrue(result)
        self.assertEqual(node.mExecuteCmd.call_count, 1)
        mock_copy.assert_called_once_with(node, '/ahf_setup', '/remote/bin')
        mock_delete.assert_called_once_with(node)
        self.assertEqual(
            mock_chg.call_args_list,
            [
                call(node, '/remote/data', 'root', 'root'),
                call(node, '/remote/data', 'oracle', 'oinstall')
            ]
        )

    # Auto-generated test for mSetupAhfonExascale
    def test_mSetupAhfonExascale_logs_install_command_details(self):
        ebox = MagicMock()
        ebox.isATP.return_value = False
        hc = MagicMock()
        hc.mGetEbox.return_value = ebox
        test_obj = cluexachk(hc, MagicMock())

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-log'
        stdout = MagicMock()
        stdout.readlines.return_value = ['install log entry']
        node.mExecuteCmd.return_value = (None, stdout, None)
        node.mGetCmdExitStatus.return_value = False

        expected_cmd = '(/remote/bin/ahf_setup -silent -local -ahf_loc /remote/install -data_dir /remote/data -tmp_loc /tmp )'

        with patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]) as mock_chg, \
             patch.object(test_obj, 'mCopyAhfImage', return_value=True) as mock_copy, \
             patch.object(test_obj, 'mGetTFACTLStatus', return_value=True), \
             patch.object(test_obj, 'mDeleteAhfImage'), \
             patch('exabox.healthcheck.cluexachk.ebLogInfo') as mock_log, \
             patch('exabox.healthcheck.cluexachk.ebLogWarn'), \
             patch('exabox.healthcheck.cluexachk.ebLogError'), \
             patch('exabox.healthcheck.cluexachk.ebLogHealth'):
            result = test_obj.mSetupAhfonExascale(
                node,
                'domU',
                '/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertTrue(result)
        mock_copy.assert_called_once_with(node, '/ahf_setup', '/remote/bin')
        mock_chg.assert_has_calls([
            call(node, '/remote/data', 'root', 'root'),
            call(node, '/remote/data', 'oracle', 'oinstall')
        ])
        node.mExecuteCmd.assert_called_once_with(expected_cmd)
        mock_log.assert_any_call('*** installing AHF Image on Exascale host domu-log , device type domU in progress...')
        mock_log.assert_any_call('*** AHF installation command:  %s ' % (expected_cmd))

    # Auto-generated test for mSetupAhfonExascale
    def test_mSetupAhfonExascale_sets_tfactl_flags_for_atp_host(self):
        ebox = MagicMock()
        ebox.isATP.return_value = True
        hc = MagicMock()
        hc.mGetEbox.return_value = ebox
        test_obj = cluexachk(hc, MagicMock())

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-atp-success'
        stdout_install = MagicMock()
        stdout_install.readlines.return_value = ['install ok']
        stdout_sanitize = MagicMock()
        stdout_sanitize.readlines.return_value = ['sanitize done']
        stdout_autopurge = MagicMock()
        stdout_autopurge.readlines.return_value = ['autopurge done']
        node.mExecuteCmd.side_effect = [
            (None, stdout_install, None),
            (None, stdout_sanitize, None),
            (None, stdout_autopurge, None),
        ]
        node.mGetCmdExitStatus.side_effect = [False, False, False]

        with patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]) as mock_chg, \
             patch.object(test_obj, 'mCopyAhfImage', return_value=True), \
             patch.object(test_obj, 'mGetTFACTLStatus', return_value=True), \
             patch.object(test_obj, 'mDeleteAhfImage') as mock_delete, \
             patch('exabox.healthcheck.cluexachk.ebLogInfo') as mock_log, \
             patch('exabox.healthcheck.cluexachk.ebLogWarn'), \
             patch('exabox.healthcheck.cluexachk.ebLogError'), \
             patch('exabox.healthcheck.cluexachk.ebLogHealth'):
            result = test_obj.mSetupAhfonExascale(
                node,
                'domU',
                '/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertTrue(result)
        self.assertEqual(node.mExecuteCmd.call_count, 3)
        manage_logs_cmd = node.mExecuteCmd.call_args_list[2][0][0]
        sanitize_cmd = node.mExecuteCmd.call_args_list[1][0][0]
        self.assertIn('manageLogsAutoPurge=ON', manage_logs_cmd)
        self.assertIn('redact=SANITIZE', sanitize_cmd)
        mock_delete.assert_called_once_with(node)
        mock_log.assert_any_call('*** Setting TFA settings on DOMU Completed')
        self.assertEqual(
            mock_chg.call_args_list,
            [
                call(node, '/remote/data', 'root', 'root'),
                call(node, '/remote/data', 'oracle', 'oinstall')
            ]
        )

    # Auto-generated test for mSetupAhfonExascale
    def test_mSetupAhfonExascale_returns_false_when_initial_permission_change_fails(self):
        ebox = MagicMock()
        ebox.isATP.return_value = False
        hc = MagicMock()
        hc.mGetEbox.return_value = ebox
        test_obj = cluexachk(hc, MagicMock())

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-fail'

        with patch.object(test_obj, 'mChgFolderOwnShip', return_value=False) as mock_chg, \
             patch.object(test_obj, 'mCopyAhfImage') as mock_copy, \
             patch.object(test_obj, 'mDeleteAhfImage') as mock_delete, \
             patch('exabox.healthcheck.cluexachk.ebLogError') as mock_log:
            result = test_obj.mSetupAhfonExascale(
                node,
                'domU',
                '/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertFalse(result)
        mock_chg.assert_called_once_with(node, '/remote/data', 'root', 'root')
        mock_copy.assert_not_called()
        mock_delete.assert_not_called()
        mock_log.assert_called_with('*** AHF cannot be installed for host due to permission issue : %s  ' % ('domu-fail'))

    # Auto-generated test for mSetupAhfonExascale
    def test_mSetupAhfonExascale_marks_failure_when_tfactl_command_fails(self):
        ebox = MagicMock()
        ebox.isATP.return_value = True
        hc = MagicMock()
        hc.mGetEbox.return_value = ebox
        test_obj = cluexachk(hc, MagicMock())

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-atp'
        stdout_install = MagicMock()
        stdout_install.readlines.return_value = ['install ok']
        stdout_tf1 = MagicMock()
        stdout_tf1.readlines.return_value = ['tfactl sanitize']
        stdout_tf2 = MagicMock()
        stdout_tf2.readlines.return_value = ['tfactl autopurge']
        node.mExecuteCmd.side_effect = [
            (None, stdout_install, None),
            (None, stdout_tf1, None),
            (None, stdout_tf2, None)
        ]
        node.mGetCmdExitStatus.side_effect = [False, False, True]

        with patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]) as mock_chg, \
             patch.object(test_obj, 'mCopyAhfImage', return_value=True), \
             patch.object(test_obj, 'mGetTFACTLStatus', return_value=True), \
             patch.object(test_obj, 'mDeleteAhfImage') as mock_delete, \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch('exabox.healthcheck.cluexachk.ebLogWarn'), \
             patch('exabox.healthcheck.cluexachk.ebLogHealth'):
            result = test_obj.mSetupAhfonExascale(
                node,
                'domU',
                '/ahf_setup',
                '/remote/bin',
                '/remote/install',
                '/remote/data'
            )

        self.assertFalse(result)
        self.assertEqual(node.mExecuteCmd.call_count, 3)
        mock_delete.assert_called_once_with(node)
        self.assertEqual(
            mock_chg.call_args_list,
            [
                call(node, '/remote/data', 'root', 'root'),
                call(node, '/remote/data', 'oracle', 'oinstall')
            ]
        )

    # Auto-generated test for mSetupAhfonExascale
    def test_mSetupAhfonExascale_raises_and_reverts_on_command_exception(self):
        ebox = MagicMock()
        ebox.isATP.return_value = False
        hc = MagicMock()
        hc.mGetEbox.return_value = ebox
        test_obj = cluexachk(hc, MagicMock())

        node = MagicMock()
        node.mGetHostname.return_value = 'domu-ex'

        with patch.object(test_obj, 'mChgFolderOwnShip', side_effect=[True, True]) as mock_chg, \
             patch.object(test_obj, 'mCopyAhfImage', return_value=True), \
             patch.object(test_obj, 'mGetTFACTLStatus') as mock_tfactl_status, \
             patch.object(test_obj, 'mDeleteAhfImage') as mock_delete, \
             patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error:
            node.mExecuteCmd.side_effect = Exception('cmd failed')
            with self.assertRaises(Exception) as context:
                test_obj.mSetupAhfonExascale(
                    node,
                    'domU',
                    '/ahf_setup',
                    '/remote/bin',
                    '/remote/install',
                    '/remote/data'
                )

        self.assertEqual(str(context.exception), 'cmd failed')
        self.assertEqual(
            mock_chg.call_args_list,
            [
                call(node, '/remote/data', 'root', 'root'),
                call(node, '/remote/data', 'oracle', 'oinstall')
            ]
        )
        mock_tfactl_status.assert_not_called()
        mock_delete.assert_not_called()
        mock_error.assert_called()

    # Auto-generated test for mDeleteDataDir
    def test_mDeleteDataDir_removes_non_install_path(self):
        class DummyEbox(object):
            def __init__(self):
                self._paths = {
                    ('ahf_paths', 'remote_ahf_data_path_zdlra_domu'): '/u02',
                    ('ahf_paths', 'remote_ahf_data_path_domu'): '/u01'
                }

            def mCheckSubConfigOption(self, section, key):
                return self._paths[(section, key)]

            def IsZdlraProv(self):
                return False

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        node = MagicMock()
        node.mFileExists.return_value = True
        node.mGetCmdExitStatus.return_value = False
        node.mGetHostname.return_value = 'domu-clean'
        with patch('exabox.healthcheck.cluexachk.ebLogInfo') as mock_info:
            testObj.mDeleteDataDir(node)
        node.mExecuteCmd.assert_called_once_with('/bin/rm -rf /u02/oracle.ahf')
        node.mGetCmdExitStatus.assert_called_once()
        mock_info.assert_any_call('*** AHF: Data directory /u02/oracle.ahf deleted for host: domu-clean')

    # Auto-generated test for mDeleteDataDir
    def test_mDeleteDataDir_logs_error_when_removal_fails(self):
        class DummyEbox(object):
            def __init__(self):
                self._paths = {
                    ('ahf_paths', 'remote_ahf_data_path_zdlra_domu'): '/zdlra',
                    ('ahf_paths', 'remote_ahf_data_path_domu'): '/domu'
                }

            def mCheckSubConfigOption(self, section, key):
                return self._paths[(section, key)]

            def IsZdlraProv(self):
                return True

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        node = MagicMock()
        node.mFileExists.return_value = True
        node.mGetCmdExitStatus.return_value = True
        node.mGetHostname.return_value = 'domu-fail'
        with patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error:
            testObj.mDeleteDataDir(node)
            node.mExecuteCmd.assert_called_once_with('/bin/rm -rf /domu/oracle.ahf')
            node.mGetCmdExitStatus.assert_called_once()
            mock_error.assert_called_with('*** AHF: Unable to delete Data directory /domu/oracle.ahf for host: domu-fail')

    # Auto-generated test for mDeleteDataDir
    def test_mDeleteDataDir_skips_when_directory_missing(self):
        class DummyEbox(object):
            def __init__(self):
                self._paths = {
                    ('ahf_paths', 'remote_ahf_data_path_zdlra_domu'): '/u03',
                    ('ahf_paths', 'remote_ahf_data_path_domu'): '/u01'
                }

            def mCheckSubConfigOption(self, section, key):
                return self._paths[(section, key)]

            def IsZdlraProv(self):
                return False

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        node = MagicMock()
        node.mFileExists.return_value = False
        node.mGetHostname.return_value = 'domu-none'
        with patch('exabox.healthcheck.cluexachk.ebLogInfo') as mock_info:
            testObj.mDeleteDataDir(node)
        node.mExecuteCmd.assert_not_called()
        mock_info.assert_any_call('*** AHF: Data directory on /u03/oracle.ahf doesnt exist for host: domu-none, skipping deletion')

    # Auto-generated test for mGetAhfBinVerFromCtrlPlane
    def test_mGetAhfBinVerFromCtrlPlane_returns_local_version(self):
        class DummyEbox(object):
            def mExecuteCmdLog2(self, cmd, aStdIn=None):
                return (["AHF Build ID : 23200020230302111526"], "")

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        with patch('os.path.isfile', return_value=True):
            version = testObj.mGetAhfBinVerFromCtrlPlane('/opt/oracle/ahf_setup')
        self.assertEqual(version, 232000202303021115)

    # Auto-generated test for mGetAhfBinVerFromCtrlPlane
    def test_mGetAhfBinVerFromCtrlPlane_reads_remote_node(self):
        class DummyEbox(object):
            pass

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        node = MagicMock()
        node.mFileExists.return_value = True
        stdout = MagicMock()
        stdout.readlines.return_value = ['AHF Build ID : 23200020230302111526\n']
        node.mExecuteCmd.return_value = (None, stdout, None)
        node.mGetCmdExitStatus.return_value = False
        version = testObj.mGetAhfBinVerFromCtrlPlane('/opt/oracle/ahf_setup', node)
        node.mExecuteCmd.assert_called_once_with('/opt/oracle/ahf_setup -v')
        self.assertEqual(version, 232000202303021115)

    # Auto-generated test for mGetAhfBinVerFromCtrlPlane
    def test_mGetAhfBinVerFromCtrlPlane_returns_zero_if_missing(self):
        class DummyEbox(object):
            def mExecuteCmdLog2(self, cmd, aStdIn=None):
                return ([], "")

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        with patch('os.path.isfile', return_value=False):
            version = testObj.mGetAhfBinVerFromCtrlPlane('/missing/bin')
        self.assertEqual(version, 0)

    # Auto-generated test for mAhfCtrlPlaneVersionCheck
    def test_mAhfCtrlPlaneVersionCheck_skips_upgrade_when_versions_match(self):
        class DummyEbox(object):
            def mExecuteCmd(self, cmd):
                return (None, None, None)

            def mExecuteCmdLog2(self, cmd, aStdIn=None):
                if 'BUILD_VERSION' in cmd:
                    return (["BUILD_VERSION=214300"], "")
                if 'BUILD_DATE' in cmd:
                    return (["BUILD_DATE=20240101"], "")
                return ([], "")

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        with patch('os.path.isfile', return_value=True), \
             patch.object(testObj, 'mGetAhfBinVerFromCtrlPlane', return_value=21430020240101):
            upgrade_needed = testObj.mAhfCtrlPlaneVersionCheck('/opt/bin', '/opt/install')
        self.assertFalse(upgrade_needed)

    # Auto-generated test for mAhfCtrlPlaneVersionCheck
    def test_mAhfCtrlPlaneVersionCheck_returns_true_when_properties_missing(self):
        class DummyEbox(object):
            def mExecuteCmd(self, cmd):
                return (None, None, None)

            def mExecuteCmdLog2(self, cmd, aStdIn=None):
                return ([], "")

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        with patch('os.path.isfile', return_value=False):
            upgrade_needed = testObj.mAhfCtrlPlaneVersionCheck('/opt/bin', '/opt/install')
        self.assertTrue(upgrade_needed)

    # Auto-generated test for mGetHigherAHFPath
    def test_mGetHigherAHFPath_keeps_exacloud_when_version_higher(self):
        class DummyEbox(object):
            def __init__(self):
                self._paths = {
                    ('ahf_paths', 'remote_ahf_bin_path'): '/remote/exacloud',
                    ('ahf_paths', 'remote_ahf_dbaas_path'): '/remote/dbaas'
                }

            def mCheckSubConfigOption(self, section, key):
                return self._paths[(section, key)]

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        node = MagicMock()
        node.mGetHostname.return_value = 'domu-node'
        with patch.object(testObj, 'mGetAhfBinVerFromCtrlPlane', side_effect=[300, 200]):
            path = testObj.mGetHigherAHFPath(node, '/ctrl/bin')
        self.assertEqual(path, '/remote/exacloud')

    # Auto-generated test for mGetHigherAHFPath
    def test_mGetHigherAHFPath_returns_default_on_exception(self):
        class DummyEbox(object):
            def __init__(self):
                self._paths = {
                    ('ahf_paths', 'remote_ahf_bin_path'): '/remote/exacloud',
                    ('ahf_paths', 'remote_ahf_dbaas_path'): '/remote/dbaas'
                }

            def mCheckSubConfigOption(self, section, key):
                return self._paths[(section, key)]

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        node = MagicMock()
        node.mGetHostname.return_value = 'domu-node'
        with patch.object(testObj, 'mGetAhfBinVerFromCtrlPlane', side_effect=Exception('failure')):
            path = testObj.mGetHigherAHFPath(node, '/ctrl/bin')
        self.assertEqual(path, '/remote/exacloud')

    # Auto-generated test for mRetriveAhfInstallDataPath
    def test_mRetriveAhfInstallDataPath_returns_empty_when_file_missing(self):
        testObj = self._build_cluexachk_with_ebox(MagicMock())
        node = MagicMock()
        node.mFileExists.return_value = False
        data_path = testObj.mRetriveAhfInstallDataPath(node, '/remote/install')
        self.assertEqual(data_path, '')
        node.mExecuteCmd.assert_not_called()

    # Auto-generated test for mRetriveAhfInstallDataPath
    def test_mRetriveAhfInstallDataPath_handles_exception(self):
        testObj = self._build_cluexachk_with_ebox(MagicMock())
        node = MagicMock()
        node.mFileExists.side_effect = Exception('broken')
        data_path = testObj.mRetriveAhfInstallDataPath(node, '/remote/install')
        self.assertEqual(data_path, '')

    # Auto-generated test for mRetriveAhfInstallDataPath
    def test_mRetriveAhfInstallDataPath_returns_data_dir(self):
        testObj = self._build_cluexachk_with_ebox(MagicMock())
        node = MagicMock()
        node.mFileExists.return_value = True
        grep_stdout = MagicMock()
        grep_stdout.readlines.return_value = [
            'DATA_DIR=/u03/oracle.ahf/data\n',
            'TFA_DATA_DIR=/u03/oracle.ahf/data/tfa\n'
        ]
        node.mExecuteCmd.return_value = (None, grep_stdout, None)

        data_path = testObj.mRetriveAhfInstallDataPath(node, '/remote/install')

        expected_cmd = "/bin/grep 'DATA_DIR' /remote/install/oracle.ahf/install.properties"
        node.mExecuteCmd.assert_called_once_with(expected_cmd)
        self.assertEqual(data_path, '/u03/oracle.ahf/data\n')

    # Auto-generated test for mGetTFACTLStatus
    def test_mGetTFACTLStatus_returns_false_without_properties(self):
        testObj = self._build_cluexachk_with_ebox(MagicMock())
        node = MagicMock()
        node.mFileExists.return_value = False

        result = testObj.mGetTFACTLStatus('/remote/install', node)

        self.assertFalse(result)
        node.mExecuteCmd.assert_not_called()

    # Auto-generated test for mGetTFACTLStatus
    def test_mGetTFACTLStatus_returns_true_and_logs_status(self):
        testObj = self._build_cluexachk_with_ebox(MagicMock())
        node = MagicMock()
        node.mGetHostname.return_value = 'domu-host'
        node.mFileExists.return_value = True

        cat_stdout = MagicMock()
        cat_stdout.readlines.return_value = ['TFA_HOME=/opt/oracle.ahf/tfa']
        status_stdout = MagicMock()
        status_stdout.readlines.return_value = ['Service STATUS: RUNNING']
        node.mExecuteCmd.side_effect = [
            (None, cat_stdout, None),
            (None, status_stdout, None)
        ]

        result = testObj.mGetTFACTLStatus('/remote/install', node)

        self.assertTrue(result)
        self.assertEqual(node.mExecuteCmd.call_count, 2)
        tfactl_cmd = node.mExecuteCmd.call_args_list[1][0][0]
        self.assertEqual(tfactl_cmd, '/opt/oracle.ahf/tfa/bin/tfactl print status')

    # Auto-generated test for mGetTFACTLStatus
    def test_mGetTFACTLStatus_returns_false_without_tfahome(self):
        testObj = self._build_cluexachk_with_ebox(MagicMock())
        node = MagicMock()
        node.mFileExists.return_value = True
        cat_stdout = MagicMock()
        cat_stdout.readlines.return_value = ['DATA_DIR=/u01/oracle.ahf/data']
        node.mExecuteCmd.return_value = (None, cat_stdout, None)

        result = testObj.mGetTFACTLStatus('/remote/install', node)

        self.assertFalse(result)
        node.mExecuteCmd.assert_called_once_with("/bin/cat /remote/install/oracle.ahf/install.properties")

    # Auto-generated test for mGetTFACTLStatus
    def test_mGetTFACTLStatus_handles_exception(self):
        testObj = self._build_cluexachk_with_ebox(MagicMock())
        node = MagicMock()
        node.mFileExists.side_effect = Exception('read error')

        with patch('exabox.healthcheck.cluexachk.ebLogWarn') as mock_warn:
            result = testObj.mGetTFACTLStatus('/remote/install', node)

        self.assertFalse(result)
        mock_warn.assert_called()
        self.assertIn('read error', mock_warn.call_args[0][0])

    # Auto-generated test for mAhfRemoteVersionCheck
    def test_mAhfRemoteVersionCheck_upgrade_required_for_standby(self):
        testObj = self._build_cluexachk_with_ebox(MagicMock())
        node = MagicMock()
        node.mGetHostname.return_value = 'standby'
        node.mFileExists.return_value = True
        build_version_stdout = MagicMock()
        build_version_stdout.readlines.return_value = ['BUILD_VERSION=202401\n']
        build_date_stdout = MagicMock()
        build_date_stdout.readlines.return_value = ['BUILD_DATE=0101\n']
        node.mExecuteCmd.side_effect = [
            (None, build_version_stdout, None),
            (None, build_date_stdout, None)
        ]

        with patch.object(testObj, 'mGetAhfBinVerFromCtrlPlane', return_value=2024020201) as mock_version:
            upgrade, fresh = testObj.mAhfRemoteVersionCheck(
                node,
                '/ctrl/bin',
                '/remote/install',
                'standby_cps'
            )

        self.assertTrue(upgrade)
        self.assertFalse(fresh)
        self.assertEqual(node.mExecuteCmd.call_count, 2)
        mock_version.assert_called_with('/ctrl/bin', node)

    # Auto-generated test for mAhfRemoteVersionCheck
    def test_mAhfRemoteVersionCheck_skips_upgrade_when_remote_newer(self):
        testObj = self._build_cluexachk_with_ebox(MagicMock())
        node = MagicMock()
        node.mGetHostname.return_value = 'domu-1'
        node.mFileExists.return_value = True
        build_version_stdout = MagicMock()
        build_version_stdout.readlines.return_value = ['BUILD_VERSION=202402\n']
        build_date_stdout = MagicMock()
        build_date_stdout.readlines.return_value = ['BUILD_DATE=0202\n']
        node.mExecuteCmd.side_effect = [
            (None, build_version_stdout, None),
            (None, build_date_stdout, None)
        ]

        with patch.object(testObj, 'mGetAhfBinVerFromCtrlPlane', return_value=2024010101) as mock_version:
            upgrade, fresh = testObj.mAhfRemoteVersionCheck(
                node,
                '/ctrl/bin',
                '/remote/install',
                'dom0'
            )

        self.assertFalse(upgrade)
        self.assertFalse(fresh)
        self.assertEqual(node.mExecuteCmd.call_count, 2)
        mock_version.assert_called_with('/ctrl/bin')

    # Auto-generated test for mAhfRemoteVersionCheck
    def test_mAhfRemoteVersionCheck_marks_fresh_when_missing_installation(self):
        testObj = self._build_cluexachk_with_ebox(MagicMock())
        node = MagicMock()
        node.mGetHostname.return_value = 'domu-2'
        node.mFileExists.return_value = False

        upgrade, fresh = testObj.mAhfRemoteVersionCheck(
            node,
            '/ctrl/bin',
            '/remote/install',
            None
        )

        self.assertTrue(upgrade)
        self.assertTrue(fresh)
        node.mExecuteCmd.assert_not_called()

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_skips_when_upgrade_not_required_dom0(self):
        class DummyEbox(object):
            def mIsOciEXACC(self):
                return False

            def mCheckSubConfigOption(self, section, key):
                return '/opt/oracle.ahf'

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        node = MagicMock()
        node.mFileExists.return_value = True

        with patch.object(testObj, 'mAhfRemoteVersionCheck', return_value=(False, False)) as mock_ver, \
             patch.object(testObj, 'mRemoveOldExachk') as mock_remove, \
             patch.object(testObj, 'mCopyAhfImage') as mock_copy:
            result = testObj.mSetupAhfonRemote(node, 'dom0', '/ahf_setup', '/remote/bin', '/remote/install', '/remote/data')

        self.assertTrue(result)
        mock_ver.assert_called_once()
        mock_remove.assert_not_called()
        mock_copy.assert_not_called()

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_returns_false_when_copy_fails(self):
        class DummyEbox(object):
            def mIsOciEXACC(self):
                return False

            def mCheckSubConfigOption(self, section, key):
                return '/opt/oracle.ahf'

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        node = MagicMock()
        node.mGetHostname.return_value = 'dom0-host'
        node.mFileExists.return_value = True

        with patch.object(testObj, 'mAhfRemoteVersionCheck', return_value=(True, False)), \
             patch.object(testObj, 'mRemoveOldExachk'), \
             patch.object(testObj, 'mCopyAhfImage', return_value=False):
            result = testObj.mSetupAhfonRemote(node, 'dom0', '/ahf_setup', '/remote/bin', '/remote/install', '/remote/data')

        self.assertFalse(result)

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_skips_domU_when_data_path_matches(self):
        class DummyEbox(object):
            def __init__(self):
                self.paths = {
                    ('ahf_paths', 'remote_ahf_data_path_domu'): '/u02',
                    ('ahf_paths', 'remote_ahf_data_path_zdlra_domu'): '/zdlra'
                }

            def mIsOciEXACC(self):
                return False

            def mCheckSubConfigOption(self, section, key):
                return self.paths[(section, key)]

            def IsZdlraProv(self):
                return False

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        node = MagicMock()
        node.mFileExists.return_value = True

        with patch.object(testObj, 'mAhfRemoteVersionCheck', return_value=(False, False)), \
             patch.object(testObj, 'mRemoveOldExachk'), \
             patch.object(testObj, 'mCopyAhfImage', return_value=True), \
             patch.object(testObj, 'mRetriveAhfInstallDataPath', return_value='/u02/oracle.ahf/data'), \
             patch.object(testObj, 'mAhfUninstall') as mock_uninstall, \
             patch.object(testObj, 'mDeleteDataDir') as mock_delete, \
             patch.object(testObj, 'mChgFolderOwnShip') as mock_chown:
            result = testObj.mSetupAhfonRemote(node, 'domU', '/ahf_setup', '/remote/bin', '/remote/install', '/remote/data')

        self.assertTrue(result)
        mock_uninstall.assert_not_called()
        mock_delete.assert_not_called()
        mock_chown.assert_not_called()

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_returns_false_when_paths_missing(self):
        class DummyEbox(object):
            def mIsOciEXACC(self):
                return False

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        node = MagicMock()
        node.mFileExists.return_value = False
        with patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error:
            result = testObj.mSetupAhfonRemote(node, 'dom0', '/ahf_setup', '/remote/bin', '/remote/install', '/remote/data')
        self.assertFalse(result)
        node.mFileExists.assert_called_once_with('/remote/install')
        mock_error.assert_called_with('*** remote ahf install and data path does not exist.install path: /remote/install, data path /remote/data')

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_retries_dom0_install_after_failure(self):
        class DummyEbox(object):
            def mIsOciEXACC(self):
                return False

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        node = MagicMock()
        node.mFileExists.side_effect = [True, True]
        node.mGetHostname.return_value = 'dom0-host'
        first_log = MagicMock()
        first_log.readlines.return_value = ['fail']
        second_log = MagicMock()
        second_log.readlines.return_value = ['retry success']
        node.mExecuteCmd.side_effect = [(None, first_log, None), (None, second_log, None)]
        node.mGetCmdExitStatus.side_effect = [True, False]
        with patch.object(testObj, 'mAhfRemoteVersionCheck', return_value=(True, False)), \
             patch.object(testObj, 'mRemoveOldExachk') as mock_remove, \
             patch.object(testObj, 'mCopyAhfImage', return_value=True) as mock_copy, \
             patch.object(testObj, 'mChgFolderOwnShip', return_value=True) as mock_chown, \
             patch.object(testObj, 'mAhfUninstall', return_value=True) as mock_uninstall, \
             patch.object(testObj, 'mDeleteAhfImage') as mock_delete:
            result = testObj.mSetupAhfonRemote(node, 'dom0', '/ahf_setup', '/remote/bin', '/remote/install', '/remote/data')

        self.assertTrue(result)
        self.assertEqual(node.mExecuteCmd.call_count, 2)
        self.assertEqual(node.mGetCmdExitStatus.call_count, 2)
        mock_copy.assert_called_once_with(node, '/ahf_setup', '/remote/bin')
        mock_chown.assert_called_once_with(node, '/opt', 'root', 'root')
        mock_uninstall.assert_called_once_with(node, '/remote/install')
        mock_delete.assert_called_once_with(node)
        mock_remove.assert_called_once_with(node)

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_installs_standby_cps_without_copy(self):
        class DummyEbox(object):
            def mIsOciEXACC(self):
                return True

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        node = MagicMock()
        node.mFileExists.side_effect = [True, True]
        node.mGetHostname.return_value = 'standby-host'
        log_stream = MagicMock()
        log_stream.readlines.return_value = ['ok']
        node.mExecuteCmd.return_value = (None, log_stream, None)
        node.mGetCmdExitStatus.return_value = False
        with patch.object(testObj, 'mAhfRemoteVersionCheck', return_value=(True, False)), \
             patch.object(testObj, 'mRemoveOldExachk') as mock_remove, \
             patch.object(testObj, 'mCopyAhfImage') as mock_copy, \
             patch.object(testObj, 'mDeleteAhfImage') as mock_delete:
            result = testObj.mSetupAhfonRemote(node, 'standby_cps', '/ahf_setup', '/remote/bin', '/remote/install', '/remote/data')

        self.assertTrue(result)
        node.mExecuteCmd.assert_called_once()
        mock_copy.assert_not_called()
        mock_remove.assert_not_called()
        mock_delete.assert_called_once_with(node)

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_dom0_failure_without_retry_when_fresh(self):
        class DummyEbox(object):
            def mIsOciEXACC(self):
                return False

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        node = MagicMock()
        node.mFileExists.side_effect = [True, True]
        node.mGetHostname.return_value = 'dom0-fresh'
        log_stream = MagicMock()
        log_stream.readlines.return_value = ['fail']
        node.mExecuteCmd.return_value = (None, log_stream, None)
        node.mGetCmdExitStatus.return_value = True
        with patch.object(testObj, 'mAhfRemoteVersionCheck', return_value=(True, True)), \
             patch.object(testObj, 'mRemoveOldExachk') as mock_remove, \
             patch.object(testObj, 'mCopyAhfImage', return_value=True) as mock_copy, \
             patch.object(testObj, 'mChgFolderOwnShip', return_value=True) as mock_chown, \
             patch.object(testObj, 'mAhfUninstall', return_value=True) as mock_uninstall, \
             patch.object(testObj, 'mDeleteAhfImage') as mock_delete:
            result = testObj.mSetupAhfonRemote(node, 'dom0', '/ahf_setup', '/remote/bin', '/remote/install', '/remote/data')

        self.assertFalse(result)
        node.mExecuteCmd.assert_called_once()
        mock_copy.assert_called_once()
        mock_chown.assert_called_once()
        mock_uninstall.assert_not_called()
        mock_delete.assert_called_once_with(node)
        mock_remove.assert_called_once_with(node)

    # Auto-generated test for mRemoteRunExachk
    def test_mRemoteRunExachk_logs_when_control_plane_lock_unavailable(self):
        test_obj, options, hc, json_map, _, node, ebox = self._create_remote_run_setup()

        base_ctx = MagicMock()
        base_ctx.mGetBasePath.return_value = '/base'

        @contextmanager
        def fake_cp_lock(*_args, **_kwargs):
            yield False

        with patch.object(test_obj, 'mSetupAhfonCtrlPlane', return_value=True), \
             patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=base_ctx), \
             patch('exabox.healthcheck.cluexachk.maskSensitiveData', side_effect=lambda x: x), \
             patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'), \
             patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'), \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch('exabox.healthcheck.cluexachk.ebLogHealth'), \
             patch('exabox.healthcheck.cluexachk.ebLogError'), \
             patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True), \
             patch('exabox.healthcheck.cluexachk.os.stat', side_effect=OSError()), \
             patch('exabox.healthcheck.cluexachk.os.makedirs'), \
             patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_cp_lock), \
             patch('exabox.healthcheck.cluexachk.obtain_remote_lock') as mock_remote, \
             patch.dict('exabox.healthcheck.cluexachk.os.environ', {'PYTHONPATH': 'orig'}, clear=False):
            test_obj.mRemoteRunExachk(options)

        host_key = list(json_map['Exachk']['hostCheck'].keys())[0]
        self.assertEqual(json_map['Exachk']['hostCheck'][host_key]['logs'][0], 'could not get ctrl pln lock')
        self.assertEqual(json_map['Exachk']['hostCheck'][host_key]['TestResult'], 'Fail')
        mock_remote.assert_not_called()

    # Auto-generated test for mRemoteRunExachk
    def test_mRemoteRunExachk_handles_command_error(self):
        test_obj, options, hc, json_map, recommend, node, ebox = self._create_remote_run_setup()

        base_ctx = MagicMock()
        base_ctx.mGetBasePath.return_value = '/base'

        ebox.mExecuteCmdLog2.return_value = (['out'], 'error-message')

        @contextmanager
        def fake_cp_lock(*_args, **_kwargs):
            yield True

        @contextmanager
        def fake_remote_lock(inner_ebox):
            yield inner_ebox

        with patch.object(test_obj, 'mSetupAhfonCtrlPlane', return_value=True), \
             patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=base_ctx), \
             patch('exabox.healthcheck.cluexachk.maskSensitiveData', side_effect=lambda x: x), \
             patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'), \
             patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'), \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch('exabox.healthcheck.cluexachk.ebLogHealth'), \
             patch('exabox.healthcheck.cluexachk.ebLogError'), \
             patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True), \
             patch('exabox.healthcheck.cluexachk.os.stat', side_effect=OSError()), \
             patch('exabox.healthcheck.cluexachk.os.makedirs'), \
             patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_cp_lock), \
             patch('exabox.healthcheck.cluexachk.obtain_remote_lock', side_effect=fake_remote_lock), \
             patch.dict('exabox.healthcheck.cluexachk.os.environ', {'PYTHONPATH': 'orig'}, clear=False):
            test_obj.mRemoteRunExachk(options)

        host_key = list(json_map['Exachk']['hostCheck'].keys())[0]
        self.assertIn('ERROR: on host', json_map['Exachk']['hostCheck'][host_key]['logs'][0])
        self.assertEqual(json_map['Exachk']['hostCheck'][host_key]['TestResult'], 'Fail')
        self.assertIn('ERROR: on host', recommend[-1])

    # Auto-generated test for mRemoteRunExachk
    def test_mRemoteRunExachk_marks_non_pingable_host(self):
        test_obj, options, hc, json_map, recommend, node, ebox = self._create_remote_run_setup(pingable=False)

        base_ctx = MagicMock()
        base_ctx.mGetBasePath.return_value = '/base'

        with patch.object(test_obj, 'mSetupAhfonCtrlPlane', return_value=True), \
             patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=base_ctx), \
             patch('exabox.healthcheck.cluexachk.maskSensitiveData', side_effect=lambda x: x), \
             patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'), \
             patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'), \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch('exabox.healthcheck.cluexachk.ebLogHealth'), \
             patch('exabox.healthcheck.cluexachk.ebLogError'), \
             patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True), \
             patch('exabox.healthcheck.cluexachk.obtain_cp_lock') as mock_lock, \
             patch.dict('exabox.healthcheck.cluexachk.os.environ', {'PYTHONPATH': 'orig'}, clear=False):
            test_obj.mRemoteRunExachk(options)

        host_key = list(json_map['Exachk']['hostCheck'].keys())[0]
        self.assertIn('host: dom0-1 is not pingable', json_map['Exachk']['hostCheck'][host_key]['logs'][0])
        self.assertEqual(json_map['Exachk']['hostCheck'][host_key]['TestResult'], 'Fail')
        self.assertIn('host: dom0-1 is not pingable', recommend[-1])
        mock_lock.assert_not_called()

    # Auto-generated test for mRemoteRunExachk
    def test_mRemoteRunExachk_clears_logs_when_successful(self):
        config = {}
        test_obj, options, hc, json_map, recommend, node, ebox = self._create_remote_run_setup(config=config)

        base_ctx = MagicMock()
        base_ctx.mGetBasePath.return_value = '/base'

        fake_zip_path = '/cluster/exachk/result.zip'

        class FakeZip(object):
            def __init__(self, *_args, **_kwargs):
                pass

            def namelist(self):
                return ['report.json']

            def extract(self, *_args, **_kwargs):
                return None

            def close(self):
                return None

        @contextmanager
        def fake_cp_lock(*_args, **_kwargs):
            yield True

        @contextmanager
        def fake_remote_lock(inner_ebox):
            yield inner_ebox

        with patch.object(test_obj, 'mSetupAhfonCtrlPlane', return_value=True), \
             patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=base_ctx), \
             patch('exabox.healthcheck.cluexachk.maskSensitiveData', side_effect=lambda x: x), \
             patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'), \
             patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'), \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch('exabox.healthcheck.cluexachk.ebLogHealth'), \
             patch('exabox.healthcheck.cluexachk.ebLogError'), \
             patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True), \
             patch('exabox.healthcheck.cluexachk.os.stat', side_effect=OSError()), \
             patch('exabox.healthcheck.cluexachk.os.makedirs'), \
             patch('exabox.healthcheck.cluexachk.glob.glob', return_value=[fake_zip_path]), \
             patch('exabox.healthcheck.cluexachk.zipfile.ZipFile', side_effect=FakeZip), \
             patch('exabox.healthcheck.cluexachk.os.walk', return_value=[]), \
             patch('exabox.healthcheck.cluexachk.os.chmod'), \
             patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_cp_lock), \
             patch('exabox.healthcheck.cluexachk.obtain_remote_lock', side_effect=fake_remote_lock), \
             patch.dict('exabox.healthcheck.cluexachk.os.environ', {'PYTHONPATH': 'orig'}, clear=False):
            test_obj.mRemoteRunExachk(options)

        host_key = list(json_map['Exachk']['hostCheck'].keys())[0]
        self.assertEqual(json_map['Exachk']['hostCheck'][host_key]['TestResult'], 'Pass')
        self.assertNotIn('logs', json_map['Exachk']['hostCheck'][host_key])

    # Auto-generated test for mRemoteRunExachk
    def test_mRemoteRunExachk_handles_missing_zip_result(self):
        config = {}
        test_obj, options, hc, json_map, recommend, node, _ = self._create_remote_run_setup(config=config)

        base_ctx = MagicMock()
        base_ctx.mGetBasePath.return_value = '/base'

        @contextmanager
        def fake_cp_lock(*_args, **_kwargs):
            yield True

        @contextmanager
        def fake_remote_lock(inner_ebox):
            yield inner_ebox

        with patch.object(test_obj, 'mSetupAhfonCtrlPlane', return_value=True), \
             patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=base_ctx), \
             patch('exabox.healthcheck.cluexachk.maskSensitiveData', side_effect=lambda x: x), \
             patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'), \
             patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'), \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch('exabox.healthcheck.cluexachk.ebLogHealth'), \
             patch('exabox.healthcheck.cluexachk.ebLogError'), \
             patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True), \
             patch('exabox.healthcheck.cluexachk.glob.glob', return_value=[]), \
             patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_cp_lock), \
             patch('exabox.healthcheck.cluexachk.obtain_remote_lock', side_effect=fake_remote_lock), \
             patch.dict('exabox.healthcheck.cluexachk.os.environ', {'PYTHONPATH': 'orig'}, clear=False):
            test_obj.mRemoteRunExachk(options)

        host_key = list(json_map['Exachk']['hostCheck'].keys())[0]
        self.assertEqual(json_map['Exachk']['hostCheck'][host_key]['TestResult'], 'Fail')
        self.assertIn('Exachk failed to generate report', json_map['Exachk']['hostCheck'][host_key]['logs'][0])
        self.assertEqual(recommend[-1], json_map['Exachk']['hostCheck'][host_key]['logs'][0])
        self.assertEqual(json_map['Exachk']['hostCheck'][host_key]['logs'][0], 'WARNING: Exachk failed to generate report for dom0-1')

    # Auto-generated test for mRemoteRunExachk
    def test_mRemoteRunExachk_includes_remoteuser_parameter(self):
        test_obj, options, hc, json_map, recommend, node, ebox = self._create_remote_run_setup()

        base_ctx = MagicMock()
        base_ctx.mGetBasePath.return_value = '/base'

        options.jsonconf.update({'domu_verify': 'True', 'remoteuser': 'ahfuser'})

        # ensure DOMU_MODE branch is taken by setting matching evaluation mode
        options.jsonconf['evaluation_mode'] = 'dom0domu'
        ebox.mCheckConfigOption.side_effect = lambda group, key: key == 'evaluation_mode'
        ebox.mCheckSubConfigOption.side_effect = lambda group, key: 'domu' in key

        @contextmanager
        def fake_cp_lock(*_args, **_kwargs):
            yield True

        @contextmanager
        def fake_remote_lock(inner_ebox):
            yield inner_ebox

        with patch.object(test_obj, 'mSetupAhfonCtrlPlane', return_value=True), \
             patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=base_ctx), \
             patch('exabox.healthcheck.cluexachk.maskSensitiveData', side_effect=lambda x: x), \
             patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'), \
             patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'), \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch('exabox.healthcheck.cluexachk.ebLogHealth'), \
             patch('exabox.healthcheck.cluexachk.ebLogError'), \
             patch('exabox.healthcheck.cluexachk.os.stat', side_effect=OSError()), \
             patch('exabox.healthcheck.cluexachk.os.makedirs'), \
             patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True), \
             patch('exabox.healthcheck.cluexachk.glob.glob', return_value=['/tmp/exachk_010101.zip']), \
             patch('exabox.healthcheck.cluexachk.zipfile.ZipFile') as mock_zip, \
             patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_cp_lock), \
             patch('exabox.healthcheck.cluexachk.obtain_remote_lock', side_effect=fake_remote_lock), \
             patch('exabox.healthcheck.cluexachk.os.walk', return_value=[('/tmp', [], [])]), \
             patch('exabox.healthcheck.cluexachk.os.chmod'), \
             patch.dict('exabox.healthcheck.cluexachk.os.environ', {'PYTHONPATH': 'orig'}, clear=False):
            mock_zip.return_value.namelist.return_value = []
            test_obj.mRemoteRunExachk(options)

        cmdlist = ebox.mExecuteCmdLog2.call_args[0][0]
        self.assertIn('-remoteuser', cmdlist)
        self.assertIn('ahfuser', cmdlist)
        host_key = list(json_map['Exachk']['hostCheck'].keys())[0]
        self.assertEqual(json_map['Exachk']['hostCheck'][host_key]['TestResult'], 'Pass')

    # Auto-generated test for mRemoteRunExachk
    def test_mRemoteRunExachk_defaults_identitydir_when_file_missing(self):
        test_obj, options, hc, json_map, recommend, node, ebox = self._create_remote_run_setup()

        base_ctx = MagicMock()
        base_ctx.mGetBasePath.return_value = '/base'

        options.jsonconf.update({
            'dom0_verify': 'False',
            'domu_verify': 'True',
            'remoteuser': 'ahfuser',
            'identitydir': '/missing/key'
        })

        domu_node = MagicMock()
        domu_node.mGetNodeType.return_value = 'domu'
        domu_node.mGetPingable.return_value = True
        domu_node.mGetHostname.return_value = 'domu-1'
        hc.mGetClusterHostD()['domu-1'] = domu_node
        ebox.mReturnAllClusterHosts.return_value = (['dom0-1'], ['domu-1'], [], [])

        @contextmanager
        def fake_cp_lock(*_args, **_kwargs):
            yield True

        @contextmanager
        def fake_remote_lock(inner_ebox):
            yield inner_ebox

        mock_zip = MagicMock()
        mock_zip.namelist.return_value = []

        def fake_isfile(path):
            if path == '/missing/key':
                return False
            if path.endswith('oracle.ahf/bin/exachk'):
                return True
            return True

        with patch.object(test_obj, 'mSetupAhfonCtrlPlane', return_value=True), \
             patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=base_ctx), \
             patch('exabox.healthcheck.cluexachk.maskSensitiveData', side_effect=lambda x: x), \
             patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'), \
             patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'), \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch('exabox.healthcheck.cluexachk.ebLogHealth'), \
             patch('exabox.healthcheck.cluexachk.ebLogError'), \
             patch('exabox.healthcheck.cluexachk.os.stat', side_effect=OSError()), \
             patch('exabox.healthcheck.cluexachk.os.makedirs'), \
             patch('exabox.healthcheck.cluexachk.os.path.isfile', side_effect=fake_isfile), \
             patch('exabox.healthcheck.cluexachk.glob.glob', return_value=['/tmp/exachk_010101.zip']), \
             patch('exabox.healthcheck.cluexachk.zipfile.ZipFile', return_value=mock_zip), \
             patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_cp_lock), \
             patch('exabox.healthcheck.cluexachk.obtain_remote_lock', side_effect=fake_remote_lock), \
             patch('exabox.healthcheck.cluexachk.os.walk', return_value=[('/tmp', [], [])]), \
             patch('exabox.healthcheck.cluexachk.os.chmod'), \
             patch('exabox.healthcheck.cluexachk.shutil.rmtree'), \
             patch.dict('exabox.healthcheck.cluexachk.os.environ', {'PYTHONPATH': 'orig'}, clear=False):
            test_obj.mRemoteRunExachk(options)

        cmdlist = ebox.mExecuteCmdLog2.call_args[0][0]
        self.assertIn('-remoteuser', cmdlist)
        self.assertIn('ahfuser', cmdlist)
        self.assertIn('-identitydir', cmdlist)
        identity_index = cmdlist.index('-identitydir')
        self.assertEqual(cmdlist[identity_index + 1], '/oeda/WorkDir')

        host_key = list(json_map['Exachk']['hostCheck'].keys())[0]
        self.assertEqual(json_map['Exachk']['hostCheck'][host_key]['TestResult'], 'Pass')

    # Auto-generated test for mRemoteRunExachk
    def test_mRemoteRunExachk_uses_cluster_name_when_ipmitool_fails(self):
        config = {'exachk_zip_dir': '/dest'}
        test_obj, options, hc, json_map, recommend, node, ebox = self._create_remote_run_setup(config=config)

        base_ctx = MagicMock()
        base_ctx.mGetBasePath.return_value = '/base'

        @contextmanager
        def fake_cp_lock(*_args, **_kwargs):
            yield True

        @contextmanager
        def fake_remote_lock(inner_ebox):
            yield inner_ebox

        mock_zip = MagicMock()
        mock_zip.namelist.return_value = []

        with patch.object(test_obj, 'mSetupAhfonCtrlPlane', return_value=True), \
             patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=base_ctx), \
             patch('exabox.healthcheck.cluexachk.maskSensitiveData', side_effect=lambda x: x), \
             patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'), \
             patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'), \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch('exabox.healthcheck.cluexachk.ebLogHealth'), \
             patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error, \
             patch('exabox.healthcheck.cluexachk.os.stat', side_effect=OSError()), \
             patch('exabox.healthcheck.cluexachk.os.makedirs'), \
             patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True), \
             patch('exabox.healthcheck.cluexachk.glob.glob', return_value=['/tmp/exachk_010101.zip']), \
             patch('exabox.healthcheck.cluexachk.zipfile.ZipFile', return_value=mock_zip), \
             patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_cp_lock), \
             patch('exabox.healthcheck.cluexachk.obtain_remote_lock', side_effect=fake_remote_lock), \
             patch('exabox.healthcheck.cluexachk.shutil.move'), \
             patch('exabox.healthcheck.cluexachk.shutil.make_archive') as mock_make_archive, \
             patch('exabox.healthcheck.cluexachk.shutil.rmtree'), \
             patch('exabox.healthcheck.cluexachk.exaBoxNode') as mock_node_cls, \
             patch.dict('exabox.healthcheck.cluexachk.os.environ', {'PYTHONPATH': 'orig'}, clear=False):
            mock_node = mock_node_cls.return_value
            mock_node.mConnectTimed.side_effect = Exception('ipmitool failure')
            test_obj.mRemoteRunExachk(options)

        error_messages = [args[0] for args, _ in mock_error.call_args_list if 'Exception while fetching serial number' in args[0]]
        self.assertTrue(error_messages)
        host_key = list(json_map['Exachk']['hostCheck'].keys())[0]
        self.assertEqual(json_map['Exachk']['hostCheck'][host_key]['TestResult'], 'Pass')
        archive_args = mock_make_archive.call_args[0][0]
        self.assertIn('cluster-name', archive_args)

    # Auto-generated test for mRemoteRunExachk
    def test_mRemoteRunExachk_uses_cluster_name_when_ipmitool_command_fails(self):
        config = {'exachk_zip_dir': '/dest'}
        test_obj, options, hc, json_map, recommend, node, ebox = self._create_remote_run_setup(config=config)

        base_ctx = MagicMock()
        base_ctx.mGetBasePath.return_value = '/base'

        @contextmanager
        def fake_cp_lock(*_args, **_kwargs):
            yield True

        @contextmanager
        def fake_remote_lock(inner_ebox):
            yield inner_ebox

        mock_zip = MagicMock()
        mock_zip.namelist.return_value = []

        fake_stdout = MagicMock()
        fake_stdout.readlines.return_value = []
        fake_error = MagicMock()
        fake_error.readlines.return_value = ['failure']

        with patch.object(test_obj, 'mSetupAhfonCtrlPlane', return_value=True), \
             patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=base_ctx), \
             patch('exabox.healthcheck.cluexachk.maskSensitiveData', side_effect=lambda x: x), \
             patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'), \
             patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'), \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch('exabox.healthcheck.cluexachk.ebLogHealth'), \
             patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error, \
             patch('exabox.healthcheck.cluexachk.os.stat', side_effect=OSError()), \
             patch('exabox.healthcheck.cluexachk.os.makedirs'), \
             patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True), \
             patch('exabox.healthcheck.cluexachk.glob.glob', return_value=['/tmp/exachk_010101.zip']), \
             patch('exabox.healthcheck.cluexachk.zipfile.ZipFile', return_value=mock_zip), \
             patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_cp_lock), \
             patch('exabox.healthcheck.cluexachk.obtain_remote_lock', side_effect=fake_remote_lock), \
             patch('exabox.healthcheck.cluexachk.shutil.move'), \
             patch('exabox.healthcheck.cluexachk.shutil.make_archive') as mock_make_archive, \
             patch('exabox.healthcheck.cluexachk.shutil.rmtree'), \
             patch('exabox.healthcheck.cluexachk.exaBoxNode') as mock_node_cls, \
             patch.dict('exabox.healthcheck.cluexachk.os.environ', {'PYTHONPATH': 'orig'}, clear=False):
            mock_node = mock_node_cls.return_value
            mock_node.mExecuteCmd.return_value = (None, fake_stdout, fake_error)
            mock_node.mGetCmdExitStatus.return_value = True
            test_obj.mRemoteRunExachk(options)

        self.assertTrue(any('Dom0 Serial number fetch failed' in args[0] for args, _ in mock_error.call_args_list))
        archive_path = mock_make_archive.call_args[0][0]
        self.assertIn('cluster-name', archive_path)
        host_key = list(json_map['Exachk']['hostCheck'].keys())[0]
        self.assertEqual(json_map['Exachk']['hostCheck'][host_key]['TestResult'], 'Pass')

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_returns_false_when_paths_missing(self):
        class DummyEbox(object):
            def mIsOciEXACC(self):
                return False

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        node = MagicMock()
        node.mFileExists.return_value = False
        with patch('exabox.healthcheck.cluexachk.ebLogError') as mock_error:
            result = testObj.mSetupAhfonRemote(node, 'dom0', '/ahf_setup', '/remote/bin', '/remote/install', '/remote/data')
        self.assertFalse(result)
        node.mFileExists.assert_called_once_with('/remote/install')
        mock_error.assert_called_with('*** remote ahf install and data path does not exist.install path: /remote/install, data path /remote/data')

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_retries_dom0_install_after_failure(self):
        class DummyEbox(object):
            def mIsOciEXACC(self):
                return False

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        node = MagicMock()
        node.mFileExists.side_effect = [True, True]
        node.mGetHostname.return_value = 'dom0-host'
        first_log = MagicMock()
        first_log.readlines.return_value = ['fail']
        second_log = MagicMock()
        second_log.readlines.return_value = ['retry success']
        node.mExecuteCmd.side_effect = [(None, first_log, None), (None, second_log, None)]
        node.mGetCmdExitStatus.side_effect = [True, False]
        with patch.object(testObj, 'mAhfRemoteVersionCheck', return_value=(True, False)), \
             patch.object(testObj, 'mRemoveOldExachk') as mock_remove, \
             patch.object(testObj, 'mCopyAhfImage', return_value=True) as mock_copy, \
             patch.object(testObj, 'mChgFolderOwnShip', return_value=True) as mock_chown, \
             patch.object(testObj, 'mAhfUninstall', return_value=True) as mock_uninstall, \
             patch.object(testObj, 'mDeleteAhfImage') as mock_delete:
            result = testObj.mSetupAhfonRemote(node, 'dom0', '/ahf_setup', '/remote/bin', '/remote/install', '/remote/data')

        self.assertTrue(result)
        self.assertEqual(node.mExecuteCmd.call_count, 2)
        self.assertEqual(node.mGetCmdExitStatus.call_count, 2)
        mock_copy.assert_called_once_with(node, '/ahf_setup', '/remote/bin')
        mock_chown.assert_called_once_with(node, '/opt', 'root', 'root')
        mock_uninstall.assert_called_once_with(node, '/remote/install')
        mock_delete.assert_called_once_with(node)
        mock_remove.assert_called_once_with(node)

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_installs_standby_cps_without_copy(self):
        class DummyEbox(object):
            def mIsOciEXACC(self):
                return True

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        node = MagicMock()
        node.mFileExists.side_effect = [True, True]
        node.mGetHostname.return_value = 'standby-host'
        log_stream = MagicMock()
        log_stream.readlines.return_value = ['ok']
        node.mExecuteCmd.return_value = (None, log_stream, None)
        node.mGetCmdExitStatus.return_value = False
        with patch.object(testObj, 'mAhfRemoteVersionCheck', return_value=(True, False)), \
             patch.object(testObj, 'mRemoveOldExachk') as mock_remove, \
             patch.object(testObj, 'mCopyAhfImage') as mock_copy, \
             patch.object(testObj, 'mDeleteAhfImage') as mock_delete:
            result = testObj.mSetupAhfonRemote(node, 'standby_cps', '/ahf_setup', '/remote/bin', '/remote/install', '/remote/data')

        self.assertTrue(result)
        node.mExecuteCmd.assert_called_once()
        mock_copy.assert_not_called()
        mock_remove.assert_not_called()
        mock_delete.assert_called_once_with(node)

    # Auto-generated test for mSetupAhfonRemote
    def test_mSetupAhfonRemote_dom0_failure_without_retry_when_fresh(self):
        class DummyEbox(object):
            def mIsOciEXACC(self):
                return False

        testObj = self._build_cluexachk_with_ebox(DummyEbox())
        node = MagicMock()
        node.mFileExists.side_effect = [True, True]
        node.mGetHostname.return_value = 'dom0-fresh'
        log_stream = MagicMock()
        log_stream.readlines.return_value = ['fail']
        node.mExecuteCmd.return_value = (None, log_stream, None)
        node.mGetCmdExitStatus.return_value = True
        with patch.object(testObj, 'mAhfRemoteVersionCheck', return_value=(True, True)), \
             patch.object(testObj, 'mRemoveOldExachk') as mock_remove, \
             patch.object(testObj, 'mCopyAhfImage', return_value=True) as mock_copy, \
             patch.object(testObj, 'mChgFolderOwnShip', return_value=True) as mock_chown, \
             patch.object(testObj, 'mAhfUninstall', return_value=True) as mock_uninstall, \
             patch.object(testObj, 'mDeleteAhfImage') as mock_delete:
            result = testObj.mSetupAhfonRemote(node, 'dom0', '/ahf_setup', '/remote/bin', '/remote/install', '/remote/data')

        self.assertFalse(result)
        node.mExecuteCmd.assert_called_once()
        mock_copy.assert_called_once()
        mock_chown.assert_called_once()
        mock_uninstall.assert_not_called()
        mock_delete.assert_called_once_with(node)
        mock_remove.assert_called_once_with(node)


def suite():
    """
    This method ensures the execution in the intended order of the tests.
    """
    suite = unittest.TestSuite()
    suite.addTest(ebTestNode('test_ahf_install_on_domU_case1'))
    suite.addTest(ebTestNode('test_ahf_install_on_domU_case2'))
    suite.addTest(ebTestNode('test_ahf_install_on_domU_case3'))
    suite.addTest(ebTestNode('test_ahf_install_on_cps'))
    suite.addTest(ebTestNode('test_mAhfCtrlPlaneVersionCheck'))
    suite.addTest(ebTestNode('test_mGetHigherAHFPath'))
    suite.addTest(ebTestNode('test_mCopyAhfImage'))
    #suite.addTest(ebTestNode('test_ahf_local_run_exachk_shared'))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(suite())
    # Auto-generated test for mRunExachk
    def test_mRunExachk_skips_when_exacc(self):
        test_obj, options, hc, json_map, recommend, node, ebox = self._create_remote_run_setup(skip_exacc=True)

        with patch.object(test_obj, 'mInstallAhf') as mock_install, \
             patch.object(test_obj, 'mInstallAhfOnRemoteCps') as mock_install_remote, \
             patch.object(test_obj, 'mRemoteRunExachk') as mock_remote_run, \
             patch('exabox.healthcheck.cluexachk.ebLogInfo') as mock_log, \
             patch.dict('exabox.healthcheck.cluexachk.os.environ', {}, clear=False):
            test_obj.mRunExachk(options)

        mock_install.assert_not_called()
        mock_install_remote.assert_not_called()
        mock_remote_run.assert_not_called()
        mock_log.assert_any_call('AHF/Exack operations skipped for exacc')

    # Auto-generated test for mRunExachk
    def test_mRunExachk_handles_dom0_only_install_request(self):
        test_obj, options, hc, json_map, recommend, node, ebox = self._create_remote_run_setup()
        options.jsonconf['other'] = 'ahf_install_dom0'

        with patch.object(test_obj, 'mInstallAhf') as mock_install, \
             patch.object(test_obj, 'mInstallAhfOnRemoteCps') as mock_install_remote, \
             patch.object(test_obj, 'mRemoteRunExachk') as mock_remote_run, \
             patch('exabox.healthcheck.cluexachk.ebLogInfo') as mock_log, \
             patch.dict('exabox.healthcheck.cluexachk.os.environ', {}, clear=False):
            test_obj.mRunExachk(options)

        mock_install.assert_called_once_with('dom0', options)
        mock_install_remote.assert_not_called()
        mock_remote_run.assert_not_called()
        mock_log.assert_any_call('Request only for AHF installation on dom0 , skipping other flows of exachk!')

    # Auto-generated test for mRunExachk
    def test_mRunExachk_installs_and_runs_when_no_special_options(self):
        test_obj, options, hc, json_map, recommend, node, ebox = self._create_remote_run_setup()
        options.jsonconf.pop('dom0_verify', None)
        options.jsonconf = {'other': 'somethingelse'}

        with patch.object(test_obj, 'mInstallAhf') as mock_install, \
             patch.object(test_obj, 'mInstallAhfOnRemoteCps') as mock_install_remote, \
             patch.object(test_obj, 'mRemoteRunExachk') as mock_remote_run, \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch.dict('exabox.healthcheck.cluexachk.os.environ', {}, clear=False):
            test_obj.mRunExachk(options)

        mock_install.assert_has_calls([call('dom0', options)])
        mock_install_remote.assert_called_once_with(options)
        mock_remote_run.assert_called_once_with(options)

    # Auto-generated test for mRunExachk
    def test_mRunExachk_propagates_install_exception(self):
        test_obj, options, hc, json_map, recommend, node, ebox = self._create_remote_run_setup()

        error = Exception('install failed')

        with patch.object(test_obj, 'mInstallAhf', side_effect=error), \
             patch.object(test_obj, 'mInstallAhfOnRemoteCps') as mock_remote_install, \
             patch.object(test_obj.mGetCluHealthCheck().mGetEbox(), 'mUpdateErrorObject') as mock_update, \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch('exabox.healthcheck.cluexachk.ebLogError'), \
             patch.dict('exabox.healthcheck.cluexachk.os.environ', {}, clear=False):
            with self.assertRaises(ExacloudRuntimeError):
                test_obj.mRunExachk(options)

        mock_remote_install.assert_not_called()
        mock_update.assert_called_once()

    # Auto-generated test for mRunExachk
    def test_mRunExachk_propagates_remote_cp_exception(self):
        test_obj, options, hc, json_map, recommend, node, ebox = self._create_remote_run_setup()

        error = Exception('remote cps failed')

        with patch.object(test_obj, 'mInstallAhf') as mock_install, \
             patch.object(test_obj, 'mInstallAhfOnRemoteCps', side_effect=error), \
             patch.object(test_obj.mGetCluHealthCheck().mGetEbox(), 'mUpdateErrorObject') as mock_update, \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch('exabox.healthcheck.cluexachk.ebLogError'), \
             patch.dict('exabox.healthcheck.cluexachk.os.environ', {}, clear=False):
            with self.assertRaises(ExacloudRuntimeError):
                test_obj.mRunExachk(options)

        mock_install.assert_called_once_with('dom0', options)
        mock_update.assert_called_once()

    # Auto-generated test for mRemoteRunExachk
    def test_mRemoteRunExachk_uses_dom0_serial_number_when_ipmitool_succeeds(self):
        config = {'exachk_zip_dir': '/dest'}
        test_obj, options, hc, json_map, recommend, node, ebox = self._create_remote_run_setup(config=config)

        base_ctx = MagicMock()
        base_ctx.mGetBasePath.return_value = '/base'

        @contextmanager
        def fake_cp_lock(*_args, **_kwargs):
            yield True

        @contextmanager
        def fake_remote_lock(inner_ebox):
            yield inner_ebox

        mock_zip = MagicMock()
        mock_zip.namelist.return_value = []

        stdout_stream = MagicMock()
        stdout_stream.readlines.return_value = ['SN123456']

        with patch.object(test_obj, 'mSetupAhfonCtrlPlane', return_value=True), \
             patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=base_ctx), \
             patch('exabox.healthcheck.cluexachk.maskSensitiveData', side_effect=lambda x: x), \
             patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'), \
             patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'), \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch('exabox.healthcheck.cluexachk.ebLogHealth'), \
             patch('exabox.healthcheck.cluexachk.ebLogError'), \
             patch('exabox.healthcheck.cluexachk.os.stat', side_effect=OSError()), \
             patch('exabox.healthcheck.cluexachk.os.makedirs'), \
             patch('exabox.healthcheck.cluexachk.os.path.isfile', return_value=True), \
             patch('exabox.healthcheck.cluexachk.glob.glob', return_value=['/tmp/exachk_serial.zip']), \
             patch('exabox.healthcheck.cluexachk.zipfile.ZipFile', return_value=mock_zip), \
             patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_cp_lock), \
             patch('exabox.healthcheck.cluexachk.obtain_remote_lock', side_effect=fake_remote_lock), \
             patch('exabox.healthcheck.cluexachk.shutil.move'), \
             patch('exabox.healthcheck.cluexachk.shutil.make_archive') as mock_make_archive, \
             patch('exabox.healthcheck.cluexachk.shutil.rmtree'), \
             patch('exabox.healthcheck.cluexachk.exaBoxNode') as mock_node_cls, \
             patch.dict('exabox.healthcheck.cluexachk.os.environ', {'PYTHONPATH': 'orig'}, clear=False):
            mock_node = mock_node_cls.return_value
            mock_node.mConnectTimed.return_value = None
            mock_node.mExecuteCmd.return_value = (None, stdout_stream, MagicMock())
            mock_node.mGetCmdExitStatus.return_value = False

            test_obj.mRemoteRunExachk(options)

        host_key = list(json_map['Exachk']['hostCheck'].keys())[0]
        self.assertEqual(json_map['Exachk']['hostCheck'][host_key]['TestResult'], 'Pass')
        archive_path = mock_make_archive.call_args[0][0]
        self.assertIn('SN123456', archive_path)

    # Auto-generated test for mRemoteRunExachk
    def test_mRemoteRunExachk_uses_provided_identitydir_when_available(self):
        test_obj, options, hc, json_map, recommend, node, ebox = self._create_remote_run_setup()

        base_ctx = MagicMock()
        base_ctx.mGetBasePath.return_value = '/base'

        options.jsonconf.update({
            'dom0_verify': 'False',
            'domu_verify': 'True',
            'remoteuser': 'ahfuser',
            'identitydir': '/custom/key'
        })

        @contextmanager
        def fake_cp_lock(*_args, **_kwargs):
            yield True

        @contextmanager
        def fake_remote_lock(inner_ebox):
            yield inner_ebox

        mock_zip = MagicMock()
        mock_zip.namelist.return_value = []

        domu_node = MagicMock()
        domu_node.mGetNodeType.return_value = 'domu'
        domu_node.mGetPingable.return_value = True
        domu_node.mGetHostname.return_value = 'domu-1'
        hc.mGetClusterHostD()['domu-1'] = domu_node
        ebox.mReturnAllClusterHosts.return_value = (['dom0-1'], ['domu-1'], [], [])

        def fake_isfile(path):
            if path == '/custom/key':
                return True
            if path.endswith('oracle.ahf/bin/exachk'):
                return True
            return False

        with patch.object(test_obj, 'mSetupAhfonCtrlPlane', return_value=True), \
             patch('exabox.healthcheck.cluexachk.get_gcontext', return_value=base_ctx), \
             patch('exabox.healthcheck.cluexachk.maskSensitiveData', side_effect=lambda x: x), \
             patch('exabox.healthcheck.cluexachk.ebLogSetHCLogDestination', return_value='tmp_dest'), \
             patch('exabox.healthcheck.cluexachk.ebLogRemoveHCLogDestination'), \
             patch('exabox.healthcheck.cluexachk.ebLogInfo'), \
             patch('exabox.healthcheck.cluexachk.ebLogHealth'), \
             patch('exabox.healthcheck.cluexachk.ebLogError'), \
             patch('exabox.healthcheck.cluexachk.os.stat', side_effect=OSError()), \
             patch('exabox.healthcheck.cluexachk.os.makedirs'), \
             patch('exabox.healthcheck.cluexachk.os.path.isfile', side_effect=fake_isfile), \
             patch('exabox.healthcheck.cluexachk.glob.glob', return_value=['/tmp/exachk_identity.zip']), \
             patch('exabox.healthcheck.cluexachk.zipfile.ZipFile', return_value=mock_zip), \
             patch('exabox.healthcheck.cluexachk.obtain_cp_lock', side_effect=fake_cp_lock), \
             patch('exabox.healthcheck.cluexachk.obtain_remote_lock', side_effect=fake_remote_lock), \
             patch('exabox.healthcheck.cluexachk.os.walk', return_value=[('/tmp', [], [])]), \
             patch('exabox.healthcheck.cluexachk.os.chmod'), \
             patch('exabox.healthcheck.cluexachk.shutil.rmtree'), \
             patch.dict('exabox.healthcheck.cluexachk.os.environ', {'PYTHONPATH': 'orig'}, clear=False):
            test_obj.mRemoteRunExachk(options)

        cmdlist = ebox.mExecuteCmdLog2.call_args[0][0]
        self.assertIn(' -identitydir', cmdlist)
        identity_index = cmdlist.index(' -identitydir')
        self.assertEqual(cmdlist[identity_index + 1], '/custom/key')
        host_key = list(json_map['Exachk']['hostCheck'].keys())[0]
        self.assertEqual(json_map['Exachk']['hostCheck'][host_key]['TestResult'], 'Pass')
