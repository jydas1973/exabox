#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/tests_cs_exascale_complete.py /main/5 2026/01/07 11:04:03 naps Exp $
#
# tests_cs_exascale_complete.py
#
# Copyright (c) 2023, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_exascale_complete.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    prsshukl    05/23/26 - Bug 39416987 - EXACC: SSL INSPECTION: PHASE1: EXACLOUD ISN'T
#                           COPYING CUSTOMER ROOT CA AS UNABLE TO LOGIN TO THE CPS WALLET
#    naps        01/05/26 - Bug 38779989 - UT Updation.
#    naps        07/03/25 - Bug 38116390 - copy weblogic cert for R1 env.
#    gparada     08/30/23 - Creation
#

import os
import unittest
from types import SimpleNamespace

# pylint: disable=missing-class-docstring,missing-function-docstring

from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.csstep.cs_exascale_complete import csExaScaleComplete
from exabox.core.Error import ExacloudRuntimeError
from exabox.ovm.cluexascale import ebCluExaScale

from unittest.mock import MagicMock, patch


class _FakeImageBom:

    def __init__(self, aStep, aPendingSubsteps):
        self._step = aStep
        self._pending = set(aPendingSubsteps)

    def mIsSubStepExecuted(self, aStep, aSubStep):
        if aStep != self._step:
            raise AssertionError(f"Unexpected step {aStep}")
        return aSubStep not in self._pending


class _InlineProcessStructure:

    def __init__(self, aCallable, aArgs):
        self._callable = aCallable
        self._args = aArgs

    def mSetMaxExecutionTime(self, *_args, **_kwargs):
        return None

    def mSetJoinTimeout(self, *_args, **_kwargs):
        return None

    def mSetLogTimeoutFx(self, *_args, **_kwargs):
        return None

    def run(self):
        self._callable(*self._args)


class _InlineProcessManager:

    def __init__(self):
        self._processes = []

    def mStartAppend(self, aProcess):
        self._processes.append(aProcess)
        if hasattr(aProcess, 'run'):
            aProcess.run()

    def mJoinProcess(self):
        return None

class ebTestCsExascaleComplete(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def setUp(self):
        super().setUp()
        remove_alg_patch = patch('exabox.ovm.csstep.cs_exascale_complete.csUtil.mRemoveDeprecatedSshAlgorithms', autospec=True)
        self.addCleanup(remove_alg_patch.stop)
        remove_alg_patch.start()

    def test_updDomUsToJdk11(self):
        ebLogInfo("")
        ebLogInfo("Running unit test for CsExascaleComplete.updDomUsToJdk11")
        _fileExist = "/bin/test -e"
        _java11 = "/usr/lib/jvm/jdk-11-oracle-x64/bin/java"
        _javac11 = "/usr/lib/jvm/jdk-11-oracle-x64/bin/java"
        _updAlt = ".*update-alternatives"
        _set_java = "--set java"
        _set_javac = "--set javac"


        mockCommands = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand(f"{_fileExist} {_java11}",aRc=0),
                    exaMockCommand(f"{_fileExist} {_updAlt}",aRc=0),
                    exaMockCommand(f"{_updAlt} {_set_java} {_java11}",aRc=0),
                    exaMockCommand(f"{_updAlt} {_set_javac} {_javac11}",aRc=0)
                ]
            ]            
        }
        self.mPrepareMockCommands(mockCommands)
        csExaScaleCompleteInstance = csExaScaleComplete()
        _ebox = self.mGetClubox()
        csExaScaleCompleteInstance.updDomUsToJdk11(_ebox)


    def test_doExecuteBaseDB_cert_unavailable(self):
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/usr/bin/curl.*", aPersist=True),
                ]
            ],
            self.mGetRegexDom0():
                [[
                    exaMockCommand("/bin/stat.*", aRc=0,  aPersist=True)
                ]]
        }
        self.mGetContext().mSetConfigOption("weblogic_cert", {"Enabled": "True", "weblogic_cert_localpath": "config/weblogic.jks", "weblogic_cert_oss_link": "https://objectstorage.us", "weblogic_cert_vmpath": "/opt/oracle/dcs/rdbaas/config/weblogic.jks"})
        self.mPrepareMockCommands(_cmds)

        _exascale = ebCluExaScale(self.mGetClubox())

        _step = csExaScaleComplete()
        _options = self.mGetClubox().mGetOptions()
        with self.assertRaises(ExacloudRuntimeError):
            _exascale.mCopyWeblogicCert()


    @patch('exabox.core.Node.exaBoxNode.mCopyFile', return_value=1)
    def test_doExecuteBaseDB_cert_scp_fail(self, aCopy):
        _cmds = {
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/usr/bin/curl.*", aRc=0, aPersist=True),
                ]
            ],
            self.mGetRegexDom0():
                [[
                    exaMockCommand("/bin/stat.*", aRc=0,  aPersist=True)
                ]],
            self.mGetRegexVm():
                [[
                   exaMockCommand("/bin/test -e.*", aRc=1,  aPersist=True)
                ]]
        }
        self.mGetContext().mSetConfigOption("weblogic_cert", {"Enabled": "True", "weblogic_cert_localpath": "config/weblogic.jks", "weblogic_cert_oss_link": "https://objectstorage.us", "weblogic_cert_vmpath": "/opt/oracle/dcs/rdbaas/config/weblogic.jks"})
        self.mPrepareMockCommands(_cmds)
        _exascale = ebCluExaScale(self.mGetClubox())

        _step = csExaScaleComplete()
        _options = self.mGetClubox().mGetOptions()
        with patch('os.path.exists', return_value=True):
            with self.assertRaises(ExacloudRuntimeError):
                _exascale.mCopyWeblogicCert()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebNoSqlInstaller')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_skips_nosql_install_when_disabled(self, aImageBom, aNoSqlInstaller, aCluExaScale):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['RPM_UPDATE'])
        aCluExaScale.return_value = MagicMock()

        _config_map = {
            ('install_nosql', 'True'): False,
            ('grid_tfa_enabled', 'True'): False,
            ('allow_23c_grid_image_download', 'True'): False,
            ('exadbxs_image_base_provisioning_enable', 'True'): False
        }

        def _check_config(aKey, aValue=None):
            return _config_map.get((aKey, aValue), False)

        _ebox = MagicMock()
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mCopySAPfile.return_value = None
        _ebox.mIsExabm.return_value = False
        _ebox.isATP.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.mIsOciEXACC.return_value = False
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]

        _options = SimpleNamespace(jsonconf=None)
        _step = csExaScaleComplete()
        _step.doExecute(_ebox, _options, [])

        aNoSqlInstaller.assert_not_called()
        _ebox.mCopySAPfile.assert_called_once()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_disables_tfa_for_non_atp(self, aImageBom, aCluExaScale):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['TFA_ATP_CONFIG'])
        aCluExaScale.return_value = MagicMock()

        config_map = {
            ('grid_tfa_enabled', 'True'): False,
            ('install_nosql', 'True'): False,
            ('allow_23c_grid_image_download', 'True'): False,
            ('enable_validate_volumes', 'True'): False,
            ('ociexacc', 'True'): False,
        }

        def _check_config(aKey, aValue=None):
            if aValue is None:
                return False
            return config_map.get((aKey, aValue), False)

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.isATP.return_value = False
        _ebox.mIsExabm.return_value = False
        _ebox.mIsOciEXACC.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mDisableTFA = MagicMock()
        _ebox.mAtpConfig = MagicMock()
        _ebox.mCopySAPfile.return_value = None
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mCopyExaDataScript.return_value = None
        _ebox.mSaveClusterDomUList.return_value = None

        csExaScaleComplete().doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        _ebox.mDisableTFA.assert_called_once()
        _ebox.mAtpConfig.assert_not_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_runs_atp_config_when_enabled(self, aImageBom, aCluExaScale):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['TFA_ATP_CONFIG'])
        aCluExaScale.return_value = MagicMock()

        config_map = {
            ('grid_tfa_enabled', 'True'): True,
            ('install_nosql', 'True'): False,
            ('allow_23c_grid_image_download', 'True'): False,
            ('enable_validate_volumes', 'True'): False,
            ('ociexacc', 'True'): False,
        }

        def _check_config(aKey, aValue=None):
            if aValue is None:
                return False
            return config_map.get((aKey, aValue), False)

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.isATP.return_value = True
        _ebox.mIsExabm.return_value = False
        _ebox.mIsOciEXACC.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mDisableTFA = MagicMock()
        _ebox.mAtpConfig = MagicMock()
        _ebox.mCopySAPfile.return_value = None
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mCopyExaDataScript.return_value = None
        _ebox.mSaveClusterDomUList.return_value = None

        csExaScaleComplete().doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        _ebox.mDisableTFA.assert_not_called()
        _ebox.mAtpConfig.assert_called_once()

    @patch('exabox.ovm.csstep.cs_exascale_complete.csUtil')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_installs_dbcs_agent_for_exacc(self, aImageBom, aCluExaScale, aCsUtil):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['DBCS_AGENT_UPDATE'])
        aCluExaScale.return_value = MagicMock()
        aCsUtil.return_value = MagicMock()

        config_map = {
            ('grid_tfa_enabled', 'True'): True,
            ('install_nosql', 'True'): False,
            ('allow_23c_grid_image_download', 'True'): False,
            ('enable_validate_volumes', 'True'): False,
            ('ociexacc', 'True'): True,
            ('force_install_dbcs_agent', 'exacc'): False,
            ('force_dbcsagent_auth', 'True'): False,
        }

        def _check_config(aKey, aValue=None):
            if aValue is None:
                return False
            return config_map.get((aKey, aValue), False)

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mGetMajorityHostVersion.return_value = 'OL7'
        _ebox.mIsExabm.return_value = False
        _ebox.mIsOciEXACC.return_value = True
        _ebox.mIsExacm.return_value = False
        _ebox.isATP.return_value = False
        _ebox.mEnvTarget.return_value = True
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mUpdateRpm = MagicMock()
        _ebox.mDisableTFA = MagicMock()
        _ebox.mAtpConfig = MagicMock()
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mCopySAPfile.return_value = None
        _ebox.mCopyExaDataScript.return_value = None
        _ebox.mSaveClusterDomUList.return_value = None

        csExaScaleComplete().doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        _ebox.mUpdateRpm.assert_any_call('dbcs-agent-exacc.OL7.x86_64.rpm')

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluUtils')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_secures_dbcs_agent_for_exacc(self, aImageBom, aCluExaScale, aCluUtils):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['SECURE_DBCSAGENT'])
        aCluExaScale.return_value = MagicMock()
        _clu_utils = MagicMock()
        aCluUtils.return_value = _clu_utils

        config_map = {
            ('grid_tfa_enabled', 'True'): True,
            ('install_nosql', 'True'): False,
            ('allow_23c_grid_image_download', 'True'): False,
            ('enable_validate_volumes', 'True'): False,
            ('ociexacc', 'True'): True,
        }

        def _check_config(aKey, aValue=None):
            if aValue is None:
                return False
            return config_map.get((aKey, aValue), False)

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mIsExabm.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.mIsOciEXACC.return_value = True
        _ebox.isATP.return_value = False
        _ebox.mSetupDomUsForSecureDBCSCommunication = MagicMock()
        _ebox.mAddAgentWallet = MagicMock()
        _ebox.mCopySAPfile.return_value = None
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None

        csExaScaleComplete().doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        _ebox.mSetupDomUsForSecureDBCSCommunication.assert_called_once_with()
        _ebox.mAddAgentWallet.assert_called_once_with()
        _clu_utils.mSetupCustomerRootCACertificates.assert_called_once_with()

    @patch('exabox.ovm.csstep.cs_exascale_complete.csUtil')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluUtils')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.expand_domu_filesystem')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_handles_pre_boot_sequence(self, aImageBom, aExpandFs, aCluExaScale, aCluUtils, aCsUtil):
        # Auto-generated test for doExecute
        pending_steps = [
            'MAKE_FIPS_COMPLIANCE',
            'MANAGE_OPC_KEY',
            'PATCH_VM_BEFORE_BOOT',
            'PATCH_VM_CFG'
        ]
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', pending_steps)

        _exascale = MagicMock()
        aExpandFs.return_value = None
        aCluExaScale.return_value = _exascale
        _clu_utils = MagicMock()
        aCluUtils.return_value = _clu_utils
        _csu = MagicMock()
        aCsUtil.return_value = _csu

        _options = SimpleNamespace(jsonconf=None)
        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]

        _lock = MagicMock()
        _lock.__enter__.return_value = None
        _lock.__exit__.return_value = False
        _ebox.remote_lock.return_value = _lock

        _ebox.mCheckConfigOption.side_effect = lambda *args, **kwargs: False
        _ebox.IsZdlraProv.return_value = False
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mUpdateVmetrics.return_value = None
        _ebox.mPatchVMCfgBeforeBoot.return_value = None
        _ebox.mCopyVmexacsRpm.return_value = None
        _ebox.mConfigureShmAll.return_value = None
        _ebox.mParallelDomUShutdown.return_value = None
        _ebox.mPatchVMCfgOnShutdown.return_value = None
        _ebox.mStartVMExacsServiceOnShutdown.return_value = None
        _ebox.mParallelDomUStart.return_value = None
        _ebox.mPatchVMCfgAfterBoot.return_value = None
        _ebox.mCheckCaviumInstanceDomUs.return_value = None
        _ebox.mStartVMExacsServiceAfterBoot.return_value = None
        _ebox.mCopySAPfile.return_value = None
        _ebox.mReturnAllClusterHosts.return_value = ([], [], [], [])
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None

        csExaScaleComplete().doExecute(_ebox, _options, [])

        _ebox.mMakeFipsCompliant.assert_called_once_with(_options, aHost='domuA')
        _ebox.mAddUserPubKey.assert_called_once_with('opc')
        _ebox.mPatchVMCfgBeforeBoot.assert_called_once_with(_options)
        _exascale.mConfigureHugePage.assert_called_once_with(_options)
        _ebox.mConfigureShmAll.assert_called_once()
        _ebox.mParallelDomUShutdown.assert_called_once()
        _ebox.mPatchVMCfgOnShutdown.assert_called_once_with(_options)
        _ebox.mStartVMExacsServiceOnShutdown.assert_called_once_with(_options)
        _ebox.mParallelDomUStart.assert_called_once()
        _ebox.mPatchVMCfgAfterBoot.assert_called_once_with(_options)
        aExpandFs.assert_called_once_with(
            _ebox,
            perform_dom0_resize=True,
            domu_reboot=False
        )
        _ebox.mStartVMExacsServiceAfterBoot.assert_called_once_with(_options)

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogInfo')
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_sets_css_misscount_when_configured(self, aImageBom, aCluExaScale, aGetContext, aLogInfo):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', [])
        aCluExaScale.return_value = MagicMock()

        _context = MagicMock()
        _context.mGetConfigOptions.return_value = {'css_misscount': '45'}
        aGetContext.return_value = _context

        def _check_config(aKey, aValue=None):
            return False

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mIsExabm.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.mIsOciEXACC.return_value = False
        _ebox.isATP.return_value = True
        _ebox.mDomUCSSMisscountHandler = MagicMock()
        _ebox.mCopySAPfile.return_value = None
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None

        csExaScaleComplete().doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        _ebox.mDomUCSSMisscountHandler.assert_called_once_with(aMode=False, aMisscount='45')
        for _call in aLogInfo.call_args_list:
            message = _call[0][0] if _call[0] else ''
            self.assertNotIn('*** Setting CSS Misscount as value set in exabox.conf', message)

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogInfo')
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_logs_css_misscount_message_when_missing(self, aImageBom, aCluExaScale, aGetContext, aLogInfo):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', [])
        aCluExaScale.return_value = MagicMock()

        _context = MagicMock()
        _context.mGetConfigOptions.return_value = {}
        aGetContext.return_value = _context

        def _check_config(aKey, aValue=None):
            return False

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mIsExabm.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.mIsOciEXACC.return_value = False
        _ebox.isATP.return_value = True
        _ebox.mDomUCSSMisscountHandler = MagicMock()
        _ebox.mCopySAPfile.return_value = None
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None

        csExaScaleComplete().doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        _ebox.mDomUCSSMisscountHandler.assert_not_called()
        self.assertTrue(
            any(
                '*** Setting CSS Misscount as value set in exabox.conf' in call[0][0]
                for call in aLogInfo.call_args_list
                if call[0]
            )
        )

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogInfo')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_validates_volumes_when_enabled(self, aImageBom, aCluExaScale, aLogInfo):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', [])
        _exascale = MagicMock()
        aCluExaScale.return_value = _exascale

        config_map = {
            ('enable_validate_volumes', 'True'): True,
            ('grid_tfa_enabled', 'True'): True,
            ('install_nosql', 'True'): False,
            ('allow_23c_grid_image_download', 'True'): False,
            ('ociexacc', 'True'): False,
        }

        def _check_config(aKey, aValue=None):
            if aValue is None:
                return False
            return config_map.get((aKey, aValue), False)

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mIsExabm.return_value = False
        _ebox.mIsOciEXACC.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.isATP.return_value = False
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mCopySAPfile.return_value = None
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mCopyExaDataScript.return_value = None
        _ebox.mSaveClusterDomUList.return_value = None

        csExaScaleComplete().doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        _exascale.mPerformValidateVolumesCheck.assert_called_once_with('dom0a', 'domuA')

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogInfo')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_skips_volume_validation_when_disabled(self, aImageBom, aCluExaScale, aLogInfo):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', [])
        _exascale = MagicMock()
        aCluExaScale.return_value = _exascale

        config_map = {
            ('enable_validate_volumes', 'True'): False,
            ('grid_tfa_enabled', 'True'): True,
            ('install_nosql', 'True'): False,
            ('allow_23c_grid_image_download', 'True'): False,
            ('ociexacc', 'True'): False,
        }

        def _check_config(aKey, aValue=None):
            if aValue is None:
                return False
            return config_map.get((aKey, aValue), False)

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mIsExabm.return_value = False
        _ebox.mIsOciEXACC.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.isATP.return_value = False
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mCopySAPfile.return_value = None
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mCopyExaDataScript.return_value = None
        _ebox.mSaveClusterDomUList.return_value = None

        csExaScaleComplete().doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        _exascale.mPerformValidateVolumesCheck.assert_not_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.csUtil')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_waits_for_ahf_install(self, aImageBom, aCluExaScale, aCsUtil):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['AHF_UPDATE'])
        aCluExaScale.return_value = MagicMock()
        _csu = MagicMock()
        aCsUtil.return_value = _csu

        config_map = {
            ('enable_validate_volumes', 'True'): False,
            ('grid_tfa_enabled', 'True'): True,
            ('install_nosql', 'True'): False,
            ('allow_23c_grid_image_download', 'True'): False,
            ('ociexacc', 'True'): False,
        }

        def _check_config(aKey, aValue=None):
            if aValue is None:
                return False
            return config_map.get((aKey, aValue), False)

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.isATP.return_value = False
        _ebox.mIsExabm.return_value = False
        _ebox.mIsOciEXACC.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mCopySAPfile.return_value = None
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mCopyExaDataScript.return_value = None
        _ebox.mSaveClusterDomUList.return_value = None

        csExaScaleComplete().doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        _csu.mInstallAhfonDomU.assert_any_call(_ebox, 'ESTP_EXASCALE_COMPLETE', [], aInit=False, aWait=True)

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogError')
    @patch('exabox.ovm.csstep.cs_exascale_complete.node_cmd_abs_path_check')
    @patch('exabox.ovm.csstep.cs_exascale_complete.exaBoxNode')
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    def test_mSeedOCIDonDomU_seeds_ocid(self, aGetContext, aNodeCls, aCmdPath, aLogError):
        # Auto-generated test for mSeedOCIDonDomU
        aGetContext.return_value = MagicMock()
        aCmdPath.side_effect = lambda *_args, **_kwargs: f"/bin/{_args[1]}"

        _created_nodes = []

        class _FakeNode:

            def __init__(self):
                self.commands = []
                self._exit = 0

            def mConnect(self, aHost=None):
                self.host = aHost

            def mFileExists(self, aPath):
                return aPath == '/var/opt/oracle/exacc.props'

            def mExecuteCmd(self, aCmd):
                self.commands.append(aCmd)
                return (None, None, None)

            def mGetCmdExitStatus(self):
                return self._exit

            def mDisconnect(self):
                return None

        def _node_factory(*_args, **_kwargs):
            _node = _FakeNode()
            _created_nodes.append(_node)
            return _node

        aNodeCls.side_effect = _node_factory

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]

        csExaScaleComplete().mSeedOCIDonDomU(_ebox, SimpleNamespace(jsonconf={'vmClusterOcid': 'ocid1.example'}))

        self.assertTrue(_created_nodes)
        self.assertTrue(any('vmcluster_ocid=ocid1.example' in cmd for cmd in _created_nodes[0].commands))
        aLogError.assert_not_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogWarn')
    @patch('exabox.ovm.csstep.cs_exascale_complete.node_cmd_abs_path_check')
    @patch('exabox.ovm.csstep.cs_exascale_complete.connect_to_host')
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    def test_updDomUsToJdk11_logs_warning_when_missing(self, aGetContext, aConnect, aCmdPath, aLogWarn):
        # Auto-generated test for updDomUsToJdk11
        aGetContext.return_value = MagicMock()

        class _FakeNode:

            def mFileExists(self, aPath):
                return False

            def mExecuteCmdLog(self, _cmd):
                raise AssertionError('Unexpected command execution')

            def mGetCmdExitStatus(self):
                return 0

        class _Ctx:

            def __enter__(self):
                return _FakeNode()

            def __exit__(self, *_args):
                return False

        aConnect.return_value = _Ctx()
        aCmdPath.side_effect = lambda *_args, **_kwargs: f"/usr/bin/{_args[1]}"

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]

        csExaScaleComplete().updDomUsToJdk11(_ebox)

        aLogWarn.assert_called_once()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebAtpUtils')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogWarn')
    @patch('exabox.ovm.csstep.cs_exascale_complete.exaBoxNode')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebExaCCAtpListener')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_atp_backup_listener_exacc_warning(self, aImageBom, aCluExaScale, aAtpListener, aNodeCls, aLogWarn, aAtpUtils):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['ATP_BACKUP_LISTENER'])
        aCluExaScale.return_value = MagicMock()
        aAtpListener.sExtractInfoFromDomU.return_value = None

        _created_nodes = []

        def _node_factory(*args, **kwargs):
            _node = MagicMock()
            _node.mConnect.return_value = None
            _node.mDisconnect.return_value = None
            _node.mSetUser.return_value = None
            _node.mExecuteCmdLog.return_value = None
            _node.mExecuteCmd.return_value = (None, MagicMock(), None)
            _node.mFileExists.return_value = False
            _node.mGetCmdExitStatus.return_value = 0
            _node.mCopy2Local.return_value = None
            _created_nodes.append(_node)
            return _node

        aNodeCls.side_effect = _node_factory

        _config_map = {
            ('grid_tfa_enabled', 'True'): True,
            ('allow_23c_grid_image_download', 'True'): False,
            ('exadbxs_image_base_provisioning_enable', 'True'): False
        }

        def _check_config(aKey, aValue=None):
            return _config_map.get((aKey, aValue), False)

        _ebox = MagicMock()
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA'), ('dom0b', 'domuB')]
        _ebox.mIsExabm.return_value = False
        _ebox.isATP.return_value = True
        _ebox.mIsOciEXACC.return_value = True
        _ebox.mIsExacm.return_value = False
        _ebox.mIsDebug.return_value = False
        _ebox.mGetATP.return_value = SimpleNamespace()
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mDropPmemlogs.return_value = None

        _options = SimpleNamespace(jsonconf=None)
        _step = csExaScaleComplete()
        _step.doExecute(_ebox, _options, [])

        self.assertTrue(_created_nodes)
        aAtpListener.sExtractInfoFromDomU.assert_called_once_with(_created_nodes[0])
        _created_nodes[0].mDisconnect.assert_called_once()
        aLogWarn.assert_called()
        aAtpListener.sGenerateListenerCommands.assert_not_called()
        aAtpUtils.setScanFqdn.assert_called_once()

    @patch('exabox.ovm.csstep.cs_exascale_complete.time.sleep')
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebAtpUtils')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogWarn')
    @patch('exabox.ovm.csstep.cs_exascale_complete.exaBoxNode')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebExaCCAtpListener')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_atp_backup_listener_exacc_success(self, aImageBom, aCluExaScale, aAtpListener,
                                                         aNodeCls, aLogWarn, aAtpUtils, aGetContext, aSleep):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['ATP_BACKUP_LISTENER'])
        aCluExaScale.return_value = MagicMock()
        aGetContext.return_value = MagicMock()
        aSleep.return_value = None

        _listener_info = {
            'aListenerPort': '1575',
            'cluster': 'clusterA'
        }
        aAtpListener.sExtractInfoFromDomU.return_value = _listener_info
        _root_cmds = ['root_cmd_1']
        _grid_cmds = ['grid_cmd_1']
        _final_grid_cmds = ['final_grid_cmd_1']
        _final_root_cmds = ['final_root_cmd_1']
        aAtpListener.sGenerateListenerCommands.return_value = (
            _root_cmds,
            _grid_cmds,
            _final_grid_cmds,
            _final_root_cmds
        )

        class _TrackingNode:

            def __init__(self):
                self._user = 'root'
                self.connections = []
                self.commands = []

            def mSetUser(self, aUser):
                self._user = aUser

            def mConnect(self, aHost=None):
                self.connections.append(('connect', self._user, aHost))

            def mExecuteCmdLog(self, aCmd):
                self.commands.append((self._user, aCmd))

            def mExecuteCmd(self, _cmd):
                _out = MagicMock()
                _out.read.return_value = ''
                return None, _out, None

            def mGetCmdExitStatus(self):
                return 0

            def mFileExists(self, _path):
                return True

            def mDisconnect(self):
                self.connections.append(('disconnect', self._user))

        _created_nodes = []

        def _node_factory(*_args, **_kwargs):
            _node = _TrackingNode()
            _created_nodes.append(_node)
            return _node

        aNodeCls.side_effect = _node_factory

        _config_map = {
            ('grid_tfa_enabled', 'True'): True,
            ('allow_23c_grid_image_download', 'True'): False,
            ('exadbxs_image_base_provisioning_enable', 'True'): False,
            ('force_starter_db_install', None): False
        }

        def _check_config(aKey, aValue=None):
            return _config_map.get((aKey, aValue), False)

        _dom_pairs = [('dom0a', 'domuA'), ('dom0b', 'domuB')]
        _ebox = MagicMock()
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mReturnDom0DomUPair.return_value = _dom_pairs
        _ebox.mIsExabm.return_value = False
        _ebox.isATP.return_value = True
        _ebox.mIsOciEXACC.return_value = True
        _ebox.mIsExacm.return_value = False
        _ebox.mIsDebug.return_value = False
        _ebox.mGetATP.return_value = SimpleNamespace()
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mDropPmemlogs.return_value = None

        _options = SimpleNamespace(jsonconf=None)
        _step = csExaScaleComplete()
        _step.doExecute(_ebox, _options, [])

        self.assertTrue(_created_nodes)
        first_node = _created_nodes[0]
        aAtpListener.sExtractInfoFromDomU.assert_called_once_with(first_node)
        aAtpListener.sGenerateListenerCommands.assert_called_once()
        self.assertIn(('root', _root_cmds[0]), first_node.commands)

        _all_commands = [cmd for _node in _created_nodes for cmd in _node.commands]
        self.assertIn(('grid', _grid_cmds[0]), _all_commands)
        self.assertIn(('grid', _final_grid_cmds[0]), _all_commands)
        self.assertIn(('root', _final_root_cmds[0]), _all_commands)

        self.assertEqual(aAtpListener.sRegisterListenerOnBKUPOnly.call_count, len(_dom_pairs))
        aLogWarn.assert_not_called()
        aAtpUtils.setScanFqdn.assert_called_once_with(_dom_pairs)

    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessManager', new=_InlineProcessManager)
    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessStructure', new=_InlineProcessStructure)
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogTrace')
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    @patch('exabox.ovm.csstep.cs_exascale_complete.os.path.exists')
    @patch('exabox.ovm.csstep.cs_exascale_complete.connect_to_host')
    def test_mInstallSuricataRPM_logs_when_tar_missing(self, aConnect, aExists, aGetContext, aLogTrace):
        # Auto-generated test for mInstallSuricataRPM
        aGetContext.return_value = SimpleNamespace(mGetBasePath=lambda: '/tmp/base')

        def _fake_exists(path):
            if path.endswith('suricata_installer.tgz'):
                return False
            return True

        aExists.side_effect = _fake_exists

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]

        csExaScaleComplete().mInstallSuricataRPM(_ebox)

        aConnect.assert_not_called()
        self.assertTrue(aLogTrace.called)



    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessManager', new=_InlineProcessManager)
    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessStructure', new=_InlineProcessStructure)
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogInfo')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogError')
    @patch('exabox.ovm.csstep.cs_exascale_complete.node_cmd_abs_path_check')
    @patch('exabox.ovm.csstep.cs_exascale_complete.exaBoxNode')
    def test_maxDistanceUpdate_updates_configs(self, aNodeCls, aCmdPath, aLogError, aLogInfo):
        # Auto-generated test for maxDistanceUpdate

        class _FakeNode:

            def __init__(self):
                self.commands = []
                self.connected_host = None

            def mConnect(self, aHost=None):
                self.connected_host = aHost

            def mFileExists(self, path):
                return path in ['/etc/chrony.conf', '/etc/ntp.conf']

            def mExecuteCmdLog(self, cmd):
                self.commands.append(cmd)

            def mGetCmdExitStatus(self):
                return 0

            def mDisconnect(self):
                return None

        _created = []

        def _node_factory(*_args, **_kwargs):
            _node = _FakeNode()
            _created.append(_node)
            return _node

        aNodeCls.side_effect = _node_factory
        aCmdPath.side_effect = lambda *_args, **_kwargs: f"/usr/bin/{_args[1]}"

        _ebox = MagicMock()
        _ebox.mReturnAllClusterHosts.return_value = (['dom0a'], ['domuA'], [], [])

        csExaScaleComplete().maxDistanceUpdate(_ebox)

        self.assertTrue(_created)
        commands = _created[0].commands
        self.assertIn("/usr/bin/sed -i '/maxdistance/d' /etc/chrony.conf", commands)
        self.assertIn("/usr/bin/sed -i '$ a maxdistance 16.0' /etc/chrony.conf", commands)
        self.assertIn("/usr/bin/systemctl restart chronyd", commands)
        self.assertIn("/usr/bin/sed -i '/maxdist/d' /etc/ntp.conf", commands)
        self.assertIn("/usr/bin/sed -i '$ a tos maxdist 16' /etc/ntp.conf", commands)
        aLogError.assert_not_called()
        self.assertTrue(aLogInfo.called)

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.csUtil')
    def test_undoExecute_uninstalls_exacc_agent(self, aCsUtil, aCluExaScale):
        # Auto-generated test for undoExecute
        _clu = MagicMock()
        _clu.mGetLVDev.return_value = (None, None)
        aCluExaScale.return_value = _clu
        aCsUtil.return_value = MagicMock()

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mGetMajorityHostVersion.return_value = 'OL7'
        _ebox.mIsExabm.return_value = False
        _ebox.mIsOciEXACC.return_value = True
        _ebox.mIsExacm.return_value = False
        _ebox.IsZdlraProv.return_value = False
        _ebox.mPingHost.return_value = True
        _ebox.mGetCmd.return_value = 'noop'
        _ebox.mUpdateRpm = MagicMock()
        _ebox.mReturnAllClusterHosts.return_value = ([], [], [], [])

        csExaScaleComplete().undoExecute(_ebox, SimpleNamespace(), [])

        _ebox.mUpdateRpm.assert_any_call('dbcs-agent-exacc.OL7.x86_64.rpm', aUndo=True)

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogWarn')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.csUtil')
    def test_undoExecute_skips_uninstall_when_domus_down(self, aCsUtil, aCluExaScale, aLogWarn):
        # Auto-generated test for undoExecute
        _clu = MagicMock()
        _clu.mGetLVDev.return_value = (None, None)
        aCluExaScale.return_value = _clu
        aCsUtil.return_value = MagicMock()

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mGetMajorityHostVersion.return_value = 'OL7'
        _ebox.mIsExabm.return_value = False
        _ebox.mIsOciEXACC.return_value = True
        _ebox.IsZdlraProv.return_value = False
        _ebox.mPingHost.return_value = False
        _ebox.mGetCmd.return_value = 'noop'
        _ebox.mUpdateRpm = MagicMock()
        _ebox.mReturnAllClusterHosts.return_value = ([], [], [], [])

        csExaScaleComplete().undoExecute(_ebox, SimpleNamespace(), [])

        _ebox.mUpdateRpm.assert_not_called()
        aLogWarn.assert_called_with('Skipping Uninstalling DBCS Agent rpm as VMs are not running')
    @patch('exabox.ovm.csstep.cs_exascale_complete.csExaScaleComplete.updDomUsToJdk11')
    @patch('exabox.ovm.csstep.cs_exascale_complete.exaBoxNode')
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_skips_adb_end_script_when_forced(self, aImageBom, aCluExaScale, aGetContext, aNodeCls, aUpdJdk):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['UPDATE_DBFILES'])
        aCluExaScale.return_value = MagicMock()
        aGetContext.return_value = MagicMock()

        class _FakeNode:

            def mConnect(self, aHost=None):
                self._host = aHost

            def mFileExists(self, _path):
                return False

            def mExecuteCmd(self, _cmd):
                return None, None, None

            def mGetCmdExitStatus(self):
                return 0

            def mDisconnect(self):
                return None

        aNodeCls.side_effect = lambda *_args, **_kwargs: _FakeNode()

        _config_map = {
            'force_starter_db_install': 'True'
        }

        def _check_config(aKey, aValue=None):
            return _config_map.get(aKey, False)

        _ebox = MagicMock()
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mRunScript = MagicMock(return_value=(0, 'noop'))
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mCopySAPfile.return_value = None
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mCopyExaDataScript.return_value = None
        _ebox.mSaveClusterDomUList.return_value = None
        _ebox.mIsExabm.return_value = False
        _ebox.mIsOciEXACC.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.isATP.return_value = True

        _step = csExaScaleComplete()
        _step.doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        _ebox.mRunScript.assert_not_called()
        self.assertTrue(aUpdJdk.called)

    @patch('exabox.ovm.csstep.cs_exascale_complete.csExaScaleComplete.updDomUsToJdk11')
    @patch('exabox.ovm.csstep.cs_exascale_complete.exaBoxNode')
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_adb_end_script_raises_on_failure(self, aImageBom, aCluExaScale, aGetContext, aNodeCls, aUpdJdk):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['UPDATE_DBFILES'])
        aCluExaScale.return_value = MagicMock()
        aGetContext.return_value = MagicMock()

        class _FakeNode:

            def mConnect(self, aHost=None):
                self._host = aHost

            def mFileExists(self, _path):
                return False

            def mExecuteCmd(self, _cmd):
                return None, None, None

            def mGetCmdExitStatus(self):
                return 0

            def mDisconnect(self):
                return None

        aNodeCls.side_effect = lambda *_args, **_kwargs: _FakeNode()

        _config_map = {
            'force_starter_db_install': 'False'
        }

        def _check_config(aKey, aValue=None):
            return _config_map.get(aKey, False)

        _ebox = MagicMock()
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mRunScript = MagicMock(return_value=(1, 'fail_cmd'))
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mCopySAPfile.return_value = None
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mCopyExaDataScript.return_value = None
        _ebox.mSaveClusterDomUList.return_value = None
        _ebox.mIsExabm.return_value = False
        _ebox.mIsOciEXACC.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.isATP.return_value = True

        _step = csExaScaleComplete()
        with self.assertRaises(ExacloudRuntimeError):
            _step.doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        _ebox.mRunScript.assert_called_once()
        aUpdJdk.assert_not_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.expand_domu_filesystem')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluUtils')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogWarn')
    def test_doExecute_cavium_success_path(self, aLogWarn, aImageBom, aCluExaScale, aCluUtils, aExpandFs):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['PATCH_VM_CFG'])
        _exascale = MagicMock()
        aCluExaScale.return_value = _exascale
        _clu_utils = MagicMock()
        aCluUtils.return_value = _clu_utils

        def _check_config(_aKey, _aValue=None):
            return False

        _remote_lock = MagicMock()
        _remote_lock.__enter__.return_value = None
        _remote_lock.__exit__.return_value = False

        _ebox = MagicMock()
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mCopyVmexacsRpm.return_value = None
        _ebox.IsZdlraProv.return_value = False
        _ebox.mConfigureShmAll.return_value = None
        _ebox.mParallelDomUShutdown.return_value = None
        _ebox.mPatchVMCfgOnShutdown.return_value = None
        _ebox.mUpdateVmetrics.return_value = None
        _ebox.mStartVMExacsServiceOnShutdown.return_value = None
        _ebox.mParallelDomUStart.return_value = None
        _ebox.mPatchVMCfgAfterBoot.return_value = None
        _ebox.mStartVMExacsServiceAfterBoot.return_value = None
        _ebox.mCheckCaviumInstanceDomUs.return_value = None
        _ebox.mCopyExaDataScript.return_value = None
        _ebox.mSaveClusterDomUList.return_value = None
        _ebox.remote_lock.return_value = _remote_lock
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.isATP.return_value = False
        _ebox.mIsExabm.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.mIsOciEXACC.return_value = False

        _options = SimpleNamespace(jsonconf=None)
        _step = csExaScaleComplete()
        _step.doExecute(_ebox, _options, [])

        _ebox.mCheckCaviumInstanceDomUs.assert_called_once()
        _clu_utils.mInstallFalconAgentOnDomus.assert_not_called()
        aLogWarn.assert_not_called()
        aExpandFs.assert_called_once()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogError')
    @patch('exabox.ovm.csstep.cs_exascale_complete.csUtil')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluUtils')
    @patch('exabox.ovm.csstep.cs_exascale_complete.csExaScaleComplete.maxDistanceUpdate')
    @patch('exabox.ovm.csstep.cs_exascale_complete.csExaScaleComplete.mSeedOCIDonDomU')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_logs_seed_failure(self, aImageBom, aSeedOcid, aMaxDistance, aCluUtils, aCsUtil, aLogError):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['ADDITIONAL_DOMU_CHECKS'])
        aSeedOcid.side_effect = Exception('seed failure')
        aMaxDistance.return_value = None
        _clu_utils = MagicMock()
        aCluUtils.return_value = _clu_utils
        _csu = MagicMock()
        aCsUtil.return_value = _csu

        def _check_config(aKey, aValue=None):
            return False

        _ebox = MagicMock()
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mAddXsPingTargets.return_value = None
        _ebox.mStoreDomUInterconnectIps.return_value = None
        _ebox.mRemoveDatabaseMachineXmlDomU.return_value = None
        _ebox.mCopyExaDataScript.return_value = None
        _ebox.mSaveClusterDomUList.return_value = None
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.isATP.return_value = False
        _ebox.mIsExabm.return_value = False
        _ebox.mIsOciEXACC.return_value = False
        _ebox.mIsExacm.return_value = False

        _options = SimpleNamespace(jsonconf=None)
        _step = csExaScaleComplete()
        _step.doExecute(_ebox, _options, [])

        aSeedOcid.assert_called_once_with(_ebox, _options)
        aMaxDistance.assert_called_once_with(_ebox)
        _clu_utils.mInstallFalconAgentOnDomus.assert_called_once_with(['domuA'], 'Create Service')
        _ebox.mCopyExaDataScript.assert_called_once_with()
        _ebox.mSaveClusterDomUList.assert_called_once_with()
        self.assertTrue(
            any(
                'mSeedOCIDonDomU failed with Exception' in call[0][0]
                for call in aLogError.call_args_list
                if call[0]
            )
        )

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogWarn')
    @patch('exabox.ovm.csstep.cs_exascale_complete.csUtil')
    @patch('exabox.ovm.csstep.cs_exascale_complete.csExaScaleComplete.maxDistanceUpdate')
    @patch('exabox.ovm.csstep.cs_exascale_complete.csExaScaleComplete.mSeedOCIDonDomU')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_installs_23c_grid_image(self, aImageBom, aSeedOcid, aMaxDistance, aCsUtil, aLogWarn):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['ADDITIONAL_DOMU_CHECKS'])
        aSeedOcid.return_value = None
        aMaxDistance.return_value = None
        _csu = MagicMock()
        aCsUtil.return_value = _csu
        _options = SimpleNamespace(jsonconf=None)

        _config_map = {
            ('allow_23c_grid_image_download', 'True'): True,
            ('grid_tfa_enabled', 'True'): True,
            ('install_nosql', 'True'): False,
            ('enable_validate_volumes', 'True'): False,
            ('ociexacc', 'True'): False,
        }

        def _check_config(aKey, aValue=None):
            if aKey == 'domu_grid_image_path' and aValue is None:
                return '/tmp/grid_image'
            return _config_map.get((aKey, aValue), False)

        _ebox = MagicMock()
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.isATP.return_value = False
        _ebox.mIsExabm.return_value = False
        _ebox.mIsOciEXACC.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.mAddXsPingTargets.return_value = None
        _ebox.mStoreDomUInterconnectIps.return_value = None
        _ebox.mRemoveDatabaseMachineXmlDomU.return_value = None
        _ebox.mCopyExaDataScript.return_value = None
        _ebox.mSaveClusterDomUList.return_value = None
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mCopySAPfile.return_value = None

        csExaScaleComplete().doExecute(_ebox, _options, [])

        _csu.mInstall23cGridImageInDomU.assert_called_once_with(_ebox, '/tmp/grid_image', _options)
        aLogWarn.assert_not_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogWarn')
    @patch('exabox.ovm.csstep.cs_exascale_complete.csUtil')
    @patch('exabox.ovm.csstep.cs_exascale_complete.csExaScaleComplete.maxDistanceUpdate')
    @patch('exabox.ovm.csstep.cs_exascale_complete.csExaScaleComplete.mSeedOCIDonDomU')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_logs_warning_when_grid_image_fails(self, aImageBom, aSeedOcid, aMaxDistance, aCsUtil, aLogWarn):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['ADDITIONAL_DOMU_CHECKS'])
        aSeedOcid.return_value = None
        aMaxDistance.return_value = None
        _csu = MagicMock()
        _csu.mInstall23cGridImageInDomU.side_effect = Exception('copy failed')
        aCsUtil.return_value = _csu
        _options = SimpleNamespace(jsonconf=None)

        _config_map = {
            ('allow_23c_grid_image_download', 'True'): True,
            ('grid_tfa_enabled', 'True'): True,
            ('install_nosql', 'True'): False,
            ('enable_validate_volumes', 'True'): False,
            ('ociexacc', 'True'): False,
        }

        def _check_config(aKey, aValue=None):
            if aKey == 'domu_grid_image_path' and aValue is None:
                return '/tmp/grid_image'
            return _config_map.get((aKey, aValue), False)

        _ebox = MagicMock()
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.isATP.return_value = False
        _ebox.mIsExabm.return_value = False
        _ebox.mIsOciEXACC.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.mAddXsPingTargets.return_value = None
        _ebox.mStoreDomUInterconnectIps.return_value = None
        _ebox.mRemoveDatabaseMachineXmlDomU.return_value = None
        _ebox.mCopyExaDataScript.return_value = None
        _ebox.mSaveClusterDomUList.return_value = None
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mCopySAPfile.return_value = None

        csExaScaleComplete().doExecute(_ebox, _options, [])

        aLogWarn.assert_called()


    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessStructure', new=_InlineProcessStructure)
    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessManager', new=_InlineProcessManager)
    @patch('exabox.ovm.csstep.cs_exascale_complete.connect_to_host')
    @patch('exabox.ovm.csstep.cs_exascale_complete.node_cmd_abs_path_check')
    @patch('exabox.ovm.csstep.cs_exascale_complete.os.path.exists')
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    def test_mInstallSuricataRPM_success_domus(self, aGetContext, aPathExists, aNodeCmd, aConnect):
        # Auto-generated test for mInstallSuricataRPM
        _context = MagicMock()
        _context.mGetBasePath.return_value = '/tmp/base'
        aGetContext.return_value = _context
        aPathExists.return_value = True
        aNodeCmd.side_effect = lambda *_args, **_kwargs: _args[1]

        class _FakeNode:

            def __init__(self):
                self._files = set()
                self._commands = []
                self._last_status = 0

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def mFileExists(self, aPath):
                return aPath in self._files

            def mMakeDir(self, aPath):
                self._files.add(aPath)

            def mCopyFile(self, _src, aDest):
                self._files.add(os.path.join(aDest, 'suricata_installer.tgz'))

            def mExecuteCmdLog(self, aCmd):
                self._commands.append(aCmd)
                if 'tar -xzf' in aCmd:
                    self._files.add('/tmp/rpm/install.py')
                if 'rm -rf' in aCmd:
                    self._files = {f for f in self._files if not f.startswith('/tmp/rpm')}
                self._last_status = 0

            def mGetCmdExitStatus(self):
                return self._last_status

            def mCopy2Local(self, *_args, **_kwargs):
                return None

        _node = _FakeNode()

        class _Ctx:

            def __init__(self, aNode):
                self._node = aNode

            def __enter__(self):
                return self._node

            def __exit__(self, *_args):
                return False

        aConnect.side_effect = lambda *_args, **_kwargs: _Ctx(_node)

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]

        _step = csExaScaleComplete()
        _step.mInstallSuricataRPM(_ebox)

        self.assertTrue(any('--action Install' in cmd for cmd in _node._commands))
        self.assertFalse(any('suricata-installer.log' in cmd for cmd in _node._commands))

    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessStructure', new=_InlineProcessStructure)
    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessManager', new=_InlineProcessManager)
    @patch('exabox.ovm.csstep.cs_exascale_complete.connect_to_host')
    @patch('exabox.ovm.csstep.cs_exascale_complete.node_cmd_abs_path_check')
    @patch('exabox.ovm.csstep.cs_exascale_complete.os.path.exists', return_value=False)
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogTrace')
    def test_mInstallSuricataRPM_missing_installer_logs_trace(self, aLogTrace, aGetContext, _aExists, aNodeCmd, aConnect):
        # Auto-generated test for mInstallSuricataRPM
        _context = MagicMock()
        _context.mGetBasePath.return_value = '/tmp/base'
        aGetContext.return_value = _context
        aNodeCmd.side_effect = lambda *_args, **_kwargs: _args[1]

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]

        _step = csExaScaleComplete()
        _step.mInstallSuricataRPM(_ebox)

        aLogTrace.assert_called()
        aConnect.assert_not_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessStructure', new=_InlineProcessStructure)
    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessManager', new=_InlineProcessManager)
    @patch('exabox.ovm.csstep.cs_exascale_complete.gLogMgrDirectory', '/var/log/eb')
    @patch('exabox.ovm.csstep.cs_exascale_complete.time.time', return_value=1234.567)
    @patch('exabox.ovm.csstep.cs_exascale_complete.os.path.exists', return_value=True)
    @patch('exabox.ovm.csstep.cs_exascale_complete.connect_to_host')
    @patch('exabox.ovm.csstep.cs_exascale_complete.node_cmd_abs_path_check')
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogTrace')
    def test_mInstallSuricataRPM_copies_logs_on_install_failure(self, aLogTrace, aGetContext, aNodeCmd, aConnect, _aExists, _aTime):
        # Auto-generated test for mInstallSuricataRPM

        class _FailingNode:

            def __init__(self, aHost):
                self.host = aHost
                self._files = {'/tmp/rpm'}
                self._last_status = 0
                self.commands = []
                self.copied_logs = []

            def mMakeDir(self, aPath):
                self._files.add(aPath)

            def mFileExists(self, aPath):
                return aPath in self._files

            def mCopyFile(self, _src, aDest):
                self._files.add(os.path.join(aDest, 'suricata_installer.tgz'))

            def mExecuteCmdLog(self, aCmd):
                self.commands.append(aCmd)
                if 'rm -rf /tmp/rpm' in aCmd:
                    self._files = {f for f in self._files if not f.startswith('/tmp/rpm')}
                    self._last_status = 0
                elif '-xzf' in aCmd:
                    self._files.add('/tmp/rpm/install.py')
                    self._last_status = 0
                elif '--action Install' in aCmd:
                    self._files.add('/tmp/rpm/suricata-installer.log')
                    self._last_status = 1
                elif 'mv ' in aCmd:
                    parts = aCmd.split()
                    src = parts[-2]
                    dst = parts[-1]
                    if src in self._files:
                        self._files.remove(src)
                    self._files.add(dst)
                    self._last_status = 0
                else:
                    self._last_status = 0

            def mGetCmdExitStatus(self):
                return self._last_status

            def mCopy2Local(self, aSrc, aDest):
                self.copied_logs.append((aSrc, aDest))

        class _Ctx:

            def __init__(self, aNode):
                self._node = aNode

            def __enter__(self):
                return self._node

            def __exit__(self, *_args):
                return False

        _context = MagicMock()
        _context.mGetBasePath.return_value = '/tmp/base'
        aGetContext.return_value = _context
        aNodeCmd.side_effect = lambda *_args, **_kwargs: _args[1]

        _created_nodes = []

        def _connect(host, *_args, **_kwargs):
            _node = _FailingNode(host)
            _created_nodes.append(_node)
            return _Ctx(_node)

        aConnect.side_effect = _connect

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA.example.com')]

        _step = csExaScaleComplete()
        _step.mInstallSuricataRPM(_ebox)

        self.assertTrue(_created_nodes)
        _node = _created_nodes[0]
        self.assertTrue(any('--action Install' in cmd for cmd in _node.commands))
        self.assertTrue(_node.copied_logs)
        _remote_path, _local_path = _node.copied_logs[0]
        self.assertIn('1234567_domuA_suricata-installer.log', _remote_path)
        self.assertIn('1234567_domuA_suricata-installer.log', _local_path)
        aLogTrace.assert_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessStructure', new=_InlineProcessStructure)
    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessManager', new=_InlineProcessManager)
    @patch('exabox.ovm.csstep.cs_exascale_complete.node_cmd_abs_path_check')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogError')
    @patch('exabox.ovm.csstep.cs_exascale_complete.exaBoxNode')
    def test_maxDistanceUpdate_updates_chrony_and_ntp(self, aNodeCls, aLogError, aNodeCmd):
        # Auto-generated test for maxDistanceUpdate
        _commands = []

        aNodeCmd.side_effect = lambda *_args, **_kwargs: _args[1]

        class _FakeNode(MagicMock):

            def mFileExists(self, aPath):
                return aPath in {'/etc/chrony.conf', '/etc/ntp.conf'}

            def mExecuteCmdLog(self, aCmd):
                _commands.append(aCmd)

            def mGetCmdExitStatus(self):
                return 0

        aNodeCls.return_value = _FakeNode()

        _ebox = MagicMock()
        _ebox.mReturnAllClusterHosts.return_value = (['dom0a'], ['domuA'], [], [])

        _step = csExaScaleComplete()
        _step.maxDistanceUpdate(_ebox)

        self.assertTrue(any('systemctl restart chronyd' in cmd for cmd in _commands))
        self.assertTrue(any('service ntpd restart' in cmd for cmd in _commands))
        aLogError.assert_not_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessStructure', new=_InlineProcessStructure)
    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessManager', new=_InlineProcessManager)
    @patch('exabox.ovm.csstep.cs_exascale_complete.node_cmd_abs_path_check')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogError')
    @patch('exabox.ovm.csstep.cs_exascale_complete.exaBoxNode')
    def test_maxDistanceUpdate_logs_error_on_failure(self, aNodeCls, aLogError, aNodeCmd):
        # Auto-generated test for maxDistanceUpdate
        _statuses = [1, 0, 0, 0]

        aNodeCmd.side_effect = lambda *_args, **_kwargs: _args[1]

        class _FailNode(MagicMock):

            def mFileExists(self, aPath):
                return aPath == '/etc/chrony.conf'

            def mExecuteCmdLog(self, _cmd):
                return None

            def mGetCmdExitStatus(self):
                return _statuses.pop(0) if _statuses else 0

        aNodeCls.return_value = _FailNode()

        _ebox = MagicMock()
        _ebox.mReturnAllClusterHosts.return_value = (['dom0a'], [], [], [])

        csExaScaleComplete().maxDistanceUpdate(_ebox)

        aLogError.assert_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.csUtil')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    def test_undoExecute_unmounts_and_uninstalls(self, aCluExaScale, aCsUtil):
        # Auto-generated test for undoExecute
        _step = csExaScaleComplete()

        _exascale = MagicMock()
        _exascale.mGetLVDev.side_effect = [('lvmdev', 'snapdev'), (None, None)]
        aCluExaScale.return_value = _exascale

        _csu = MagicMock()
        aCsUtil.return_value = _csu

        _zdlra = MagicMock()
        _zdlra.mGetWalletViewEntry.return_value = 'secret'

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.IsZdlraProv.return_value = True
        _ebox.mGetZDLRA.return_value = _zdlra
        _ebox.mGetOedaPath.return_value = '/tmp/oeda'
        _ebox.mIsExabm.return_value = False
        _ebox.mGetCmd.return_value = 'createservice'
        _ebox.mGetMajorityHostVersion.return_value = 'OL7'
        _ebox.mPingHost.return_value = True
        _ebox.mIsOciEXACC.return_value = True

        _step.undoExecute(_ebox, SimpleNamespace(), [])

        _exascale.mUnmountVolume.assert_called_once()
        _ebox.mUpdateOedaUserPswd.assert_called_once()
        _ebox.mUpdateRpm.assert_called_once_with('dbcs-agent-exacc.OL7.x86_64.rpm', aUndo=True)
        _ebox.mReleaseRemoteLock.assert_called_once()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogWarn')
    @patch('exabox.ovm.csstep.cs_exascale_complete.csUtil')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    def test_undoExecute_skips_update_when_vms_down(self, aCluExaScale, aCsUtil, aLogWarn):
        # Auto-generated test for undoExecute
        _exascale = MagicMock()
        _exascale.mGetLVDev.return_value = (None, None)
        aCluExaScale.return_value = _exascale

        _csu = MagicMock()
        aCsUtil.return_value = _csu

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.IsZdlraProv.return_value = False
        _ebox.mIsExabm.return_value = False
        _ebox.mGetCmd.return_value = 'createservice'
        _ebox.mGetMajorityHostVersion.return_value = 'OL7'
        _ebox.mPingHost.return_value = False

        csExaScaleComplete().undoExecute(_ebox, SimpleNamespace(), [])

        _ebox.mUpdateRpm.assert_not_called()
        aLogWarn.assert_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.csUtil')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    def test_undoExecute_returns_early_for_exabm_delete(self, aCluExaScale, aCsUtil):
        # Auto-generated test for undoExecute
        _exascale = MagicMock()
        _exascale.mGetLVDev.return_value = (None, None)
        aCluExaScale.return_value = _exascale

        _csu = MagicMock()
        aCsUtil.return_value = _csu

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.IsZdlraProv.return_value = False
        _ebox.mIsExabm.return_value = True
        _ebox.mGetCmd.return_value = 'deleteservice'

        _step = csExaScaleComplete()
        _step.undoExecute(_ebox, SimpleNamespace(), [])

        _csu.mDeleteVM.assert_called_once_with(_ebox, _step.step, [])
        _ebox.mAcquireRemoteLock.assert_not_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_manage_opc_key_pending(self, aImageBom):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['MANAGE_OPC_KEY'])

        _ebox = MagicMock()
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mAddUserPubKey.return_value = None
        _ebox.mCheckConfigOption.side_effect = lambda *_args, **_kwargs: False
        _ebox.mIsExabm.return_value = False
        _ebox.isATP.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.mIsOciEXACC.return_value = False
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mCopySAPfile.return_value = None

        _step = csExaScaleComplete()
        _step.doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        _ebox.mAddUserPubKey.assert_called_once_with('opc')

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebNoSqlInstaller')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_installs_nosql_when_enabled(self, aImageBom, aNoSqlInstaller):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['RPM_UPDATE'])

        _installer = MagicMock()
        aNoSqlInstaller.return_value = _installer

        def _check_config(aKey, aValue=None):
            return (aKey, aValue) == ('install_nosql', 'True')

        _ebox = MagicMock()
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA'), ('dom0b', 'domuB')]
        _ebox.mGetRackSize.return_value = 'rack'
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mCopySAPfile.return_value = None
        _ebox.mIsExabm.return_value = False
        _ebox.isATP.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.mIsOciEXACC.return_value = False
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None

        _step = csExaScaleComplete()
        _step.doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        aNoSqlInstaller.assert_called_once_with(['domuA', 'domuB'], 'rack')
        _installer.mRunInstall.assert_called_once_with()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessStructure', new=_InlineProcessStructure)
    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessManager', new=_InlineProcessManager)
    @patch('exabox.ovm.csstep.cs_exascale_complete.connect_to_host')
    @patch('exabox.ovm.csstep.cs_exascale_complete.node_cmd_abs_path_check')
    @patch('exabox.ovm.csstep.cs_exascale_complete.os.path.exists', return_value=True)
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogTrace')
    def test_mInstallSuricataRPM_directory_creation_failure(self, aLogTrace, aGetContext, _aPathExists, aNodeCmd, aConnect):
        # Auto-generated test for mInstallSuricataRPM
        _context = MagicMock()
        _context.mGetBasePath.return_value = '/tmp/base'
        aGetContext.return_value = _context
        aNodeCmd.side_effect = lambda *_args, **_kwargs: _args[1]

        class _DirFailNode:

            def __init__(self):
                self._status = 0
                self.made_dir = False
                self.commands = []

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def mFileExists(self, aPath):
                return False

            def mMakeDir(self, _path):
                self.made_dir = True

            def mExecuteCmdLog(self, aCmd):
                self.commands.append(aCmd)
                if 'rm -rf /tmp/rpm' in aCmd:
                    self._status = 0

            def mGetCmdExitStatus(self):
                return self._status

            def mCopyFile(self, *_args, **_kwargs):
                raise AssertionError('copy should not run')

            def mCopy2Local(self, *_args, **_kwargs):
                raise AssertionError('copy2local should not run')

        class _Ctx:

            def __init__(self, aNode):
                self._node = aNode

            def __enter__(self):
                return self._node

            def __exit__(self, *_args):
                return False

        _node = _DirFailNode()
        aConnect.side_effect = lambda *_args, **_kwargs: _Ctx(_node)

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]

        csExaScaleComplete().mInstallSuricataRPM(_ebox)

        self.assertTrue(_node.made_dir)
        self.assertFalse(_node.commands)
        aLogTrace.assert_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessStructure', new=_InlineProcessStructure)
    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessManager', new=_InlineProcessManager)
    @patch('exabox.ovm.csstep.cs_exascale_complete.connect_to_host')
    @patch('exabox.ovm.csstep.cs_exascale_complete.node_cmd_abs_path_check')
    @patch('exabox.ovm.csstep.cs_exascale_complete.os.path.exists', return_value=True)
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogTrace')
    def test_mInstallSuricataRPM_untar_failure_logs_trace(self, aLogTrace, aGetContext, _aPathExists, aNodeCmd, aConnect):
        # Auto-generated test for mInstallSuricataRPM
        _context = MagicMock()
        _context.mGetBasePath.return_value = '/tmp/base'
        aGetContext.return_value = _context
        aNodeCmd.side_effect = lambda *_args, **_kwargs: _args[1]

        class _UntarFailNode:

            def __init__(self):
                self._files = set()
                self._status = 0
                self.commands = []

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def mFileExists(self, aPath):
                return aPath in self._files

            def mMakeDir(self, aPath):
                self._files.add(aPath)

            def mCopyFile(self, _src, aDest):
                self._files.add(os.path.join(aDest, 'suricata_installer.tgz'))

            def mExecuteCmdLog(self, aCmd):
                self.commands.append(aCmd)
                if 'tar -xzf' in aCmd:
                    self._status = 1
                else:
                    self._status = 0

            def mGetCmdExitStatus(self):
                return self._status

            def mCopy2Local(self, *_args, **_kwargs):
                raise AssertionError('copy2local should not run')

        class _Ctx:

            def __init__(self, aNode):
                self._node = aNode

            def __enter__(self):
                return self._node

            def __exit__(self, *_args):
                return False

        _node = _UntarFailNode()
        aConnect.side_effect = lambda *_args, **_kwargs: _Ctx(_node)

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]

        csExaScaleComplete().mInstallSuricataRPM(_ebox)

        self.assertTrue(any('tar -xzf' in cmd for cmd in _node.commands))
        self.assertNotIn('/tmp/rpm/install.py', _node._files)
        aLogTrace.assert_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessStructure', new=_InlineProcessStructure)
    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessManager', new=_InlineProcessManager)
    @patch('exabox.ovm.csstep.cs_exascale_complete.connect_to_host')
    @patch('exabox.ovm.csstep.cs_exascale_complete.node_cmd_abs_path_check')
    @patch('exabox.ovm.csstep.cs_exascale_complete.os.path.exists', return_value=True)
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogTrace')
    def test_mInstallSuricataRPM_existing_directory_removal_failure(self, aLogTrace, aGetContext, _aPathExists, aNodeCmd, aConnect):
        # Auto-generated test for mInstallSuricataRPM
        _context = MagicMock()
        _context.mGetBasePath.return_value = '/tmp/base'
        aGetContext.return_value = _context
        aNodeCmd.side_effect = lambda *_args, **_kwargs: _args[1]

        _captured = {}

        class _FailingNode:

            def __init__(self):
                self._status = 0
                self._files = {'/tmp/rpm'}
                self.commands = []
                self.make_dir_called = False

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def mFileExists(self, aPath):
                return aPath in self._files

            def mExecuteCmdLog(self, aCmd):
                self.commands.append(aCmd)
                if 'rm -rf /tmp/rpm' in aCmd:
                    self._status = 1
                else:
                    self._status = 0

            def mMakeDir(self, _path):
                self.make_dir_called = True

            def mGetCmdExitStatus(self):
                return self._status

            def mCopy2Local(self, *_args, **_kwargs):
                return None

            def mCopyFile(self, *_args, **_kwargs):
                return None

        class _Ctx:

            def __init__(self, aNode):
                self._node = aNode

            def __enter__(self):
                _captured['node'] = self._node
                return self._node

            def __exit__(self, *_args):
                return False

        aConnect.side_effect = lambda *_args, **_kwargs: _Ctx(_FailingNode())

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]

        csExaScaleComplete().mInstallSuricataRPM(_ebox)

        _node = _captured['node']
        self.assertIn('rm -rf /tmp/rpm', _node.commands)
        self.assertFalse(_node.make_dir_called)
        aLogTrace.assert_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessStructure', new=_InlineProcessStructure)
    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessManager', new=_InlineProcessManager)
    @patch('exabox.ovm.csstep.cs_exascale_complete.connect_to_host')
    @patch('exabox.ovm.csstep.cs_exascale_complete.node_cmd_abs_path_check')
    @patch('exabox.ovm.csstep.cs_exascale_complete.os.path.exists', return_value=True)
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogTrace')
    def test_mInstallSuricataRPM_copy_failure_raises_exception(self, aLogTrace, aGetContext, _aPathExists, aNodeCmd, aConnect):
        # Auto-generated test for mInstallSuricataRPM
        _context = MagicMock()
        _context.mGetBasePath.return_value = '/tmp/base'
        aGetContext.return_value = _context
        aNodeCmd.side_effect = lambda *_args, **_kwargs: _args[1]

        _captured = {}

        class _CopyFailNode:

            def __init__(self):
                self._files = set()
                self._status = 0
                self.commands = []

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def mFileExists(self, aPath):
                return aPath in self._files

            def mMakeDir(self, aPath):
                self._files.add(aPath)

            def mCopyFile(self, *_args, **_kwargs):
                return None

            def mExecuteCmdLog(self, aCmd):
                self.commands.append(aCmd)
                self._status = 0

            def mGetCmdExitStatus(self):
                return self._status

        class _Ctx:

            def __init__(self, aNode):
                self._node = aNode

            def __enter__(self):
                _captured['node'] = self._node
                return self._node

            def __exit__(self, *_args):
                return False

        aConnect.side_effect = lambda *_args, **_kwargs: _Ctx(_CopyFailNode())

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]

        csExaScaleComplete().mInstallSuricataRPM(_ebox)

        _node = _captured['node']
        self.assertIn('/tmp/rpm', _node._files)
        aLogTrace.assert_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessStructure', new=_InlineProcessStructure)
    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessManager', new=_InlineProcessManager)
    @patch('exabox.ovm.csstep.cs_exascale_complete.connect_to_host')
    @patch('exabox.ovm.csstep.cs_exascale_complete.node_cmd_abs_path_check')
    @patch('exabox.ovm.csstep.cs_exascale_complete.os.path.exists', return_value=True)
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogTrace')
    def test_mInstallSuricataRPM_missing_installer_raises_exception(self, aLogTrace, aGetContext, _aPathExists, aNodeCmd, aConnect):
        # Auto-generated test for mInstallSuricataRPM
        _context = MagicMock()
        _context.mGetBasePath.return_value = '/tmp/base'
        aGetContext.return_value = _context
        aNodeCmd.side_effect = lambda *_args, **_kwargs: _args[1]

        _captured = {}

        class _MissingInstallerNode:

            def __init__(self):
                self._files = set()
                self._status = 0
                self.commands = []

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def mFileExists(self, aPath):
                return aPath in self._files

            def mMakeDir(self, aPath):
                self._files.add(aPath)

            def mCopyFile(self, _src, aDest):
                self._files.add(os.path.join(aDest, 'suricata_installer.tgz'))

            def mExecuteCmdLog(self, aCmd):
                self.commands.append(aCmd)
                self._status = 0

            def mGetCmdExitStatus(self):
                return self._status

        class _Ctx:

            def __init__(self, aNode):
                self._node = aNode

            def __enter__(self):
                _captured['node'] = self._node
                return self._node

            def __exit__(self, *_args):
                return False

        aConnect.side_effect = lambda *_args, **_kwargs: _Ctx(_MissingInstallerNode())

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]

        csExaScaleComplete().mInstallSuricataRPM(_ebox)

        _node = _captured['node']
        self.assertTrue(any('tar -xzf' in cmd for cmd in _node.commands))
        aLogTrace.assert_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessStructure', new=_InlineProcessStructure)
    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessManager', new=_InlineProcessManager)
    @patch('exabox.ovm.csstep.cs_exascale_complete.time.time', return_value=1234.0)
    @patch('exabox.ovm.csstep.cs_exascale_complete.connect_to_host')
    @patch('exabox.ovm.csstep.cs_exascale_complete.node_cmd_abs_path_check')
    @patch('exabox.ovm.csstep.cs_exascale_complete.os.path.exists', return_value=True)
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogTrace')
    def test_mInstallSuricataRPM_log_copy_missing_raises(self, aLogTrace, aGetContext, _aPathExists, aNodeCmd, aConnect, _aTime):
        # Auto-generated test for mInstallSuricataRPM
        _context = MagicMock()
        _context.mGetBasePath.return_value = '/tmp/base'
        aGetContext.return_value = _context
        aNodeCmd.side_effect = lambda *_args, **_kwargs: _args[1]

        _captured = {}

        class _LogMissingNode:

            def __init__(self, aHost):
                self.host = aHost
                self._files = set()
                self._status = 0
                self.commands = []
                self.copied = []

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def mFileExists(self, aPath):
                return aPath in self._files

            def mMakeDir(self, aPath):
                self._files.add(aPath)

            def mCopyFile(self, _src, aDest):
                self._files.add(os.path.join(aDest, 'suricata_installer.tgz'))

            def mExecuteCmdLog(self, aCmd):
                self.commands.append(aCmd)
                if '--action Install' in aCmd:
                    self._files.add('/tmp/rpm/suricata-installer.log')
                    self._status = 1
                elif 'mv ' in aCmd:
                    parts = aCmd.split()
                    src = parts[-2]
                    if src in self._files:
                        self._files.remove(src)
                    self._status = 0
                else:
                    if 'tar -xzf' in aCmd:
                        self._files.add('/tmp/rpm/install.py')
                    self._status = 0

            def mGetCmdExitStatus(self):
                return self._status

            def mCopy2Local(self, aSrc, aDest):
                self.copied.append((aSrc, aDest))

        class _Ctx:

            def __init__(self, aNode):
                self._node = aNode

            def __enter__(self):
                _captured['node'] = self._node
                return self._node

            def __exit__(self, *_args):
                return False

        def _make_node(host, *_args, **_kwargs):
            return _Ctx(_LogMissingNode(host))

        aConnect.side_effect = _make_node

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a.example.com', 'domuA.example.com')]

        csExaScaleComplete().mInstallSuricataRPM(_ebox)

        _node = _captured['node']
        self.assertTrue(any('--action Install' in cmd for cmd in _node.commands))
        self.assertFalse(_node.copied)
        aLogTrace.assert_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessStructure', new=_InlineProcessStructure)
    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessManager', new=_InlineProcessManager)
    @patch('exabox.ovm.csstep.cs_exascale_complete.connect_to_host')
    @patch('exabox.ovm.csstep.cs_exascale_complete.node_cmd_abs_path_check')
    @patch('exabox.ovm.csstep.cs_exascale_complete.os.path.exists', return_value=True)
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogTrace')
    def test_mInstallSuricataRPM_cleanup_failure_logs_trace(self, aLogTrace, aGetContext, _aPathExists, aNodeCmd, aConnect):
        # Auto-generated test for mInstallSuricataRPM
        _context = MagicMock()
        _context.mGetBasePath.return_value = '/tmp/base'
        aGetContext.return_value = _context
        aNodeCmd.side_effect = lambda *_args, **_kwargs: _args[1]

        _captured = {}

        class _CleanupFailNode:

            def __init__(self):
                self._files = set()
                self._status = 0
                self.commands = []

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def mFileExists(self, aPath):
                return aPath in self._files

            def mMakeDir(self, aPath):
                self._files.add(aPath)

            def mCopyFile(self, _src, aDest):
                self._files.add(os.path.join(aDest, 'suricata_installer.tgz'))

            def mExecuteCmdLog(self, aCmd):
                self.commands.append(aCmd)
                if '--action Install' in aCmd:
                    self._status = 0
                elif 'tar -xzf' in aCmd:
                    self._files.add('/tmp/rpm/install.py')
                    self._status = 0
                elif 'rm -rf /tmp/rpm' in aCmd:
                    self._status = 1
                else:
                    self._status = 0

            def mGetCmdExitStatus(self):
                return self._status

            def mCopy2Local(self, *_args, **_kwargs):
                return None

        class _Ctx:

            def __init__(self, aNode):
                self._node = aNode

            def __enter__(self):
                _captured['node'] = self._node
                return self._node

            def __exit__(self, *_args):
                return False

        aConnect.side_effect = lambda *_args, **_kwargs: _Ctx(_CleanupFailNode())

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]

        csExaScaleComplete().mInstallSuricataRPM(_ebox)

        _node = _captured['node']
        self.assertTrue(any('rm -rf /tmp/rpm' in cmd for cmd in _node.commands))
        aLogTrace.assert_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_skips_namespace_install_without_enable_flag(self, aImageBom, aCluExaScale):
        # Auto-generated test for doExecute
        pending = ['RPM_UPDATE']
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', pending)
        aCluExaScale.return_value = MagicMock()

        config_map = {
            ('install_nosql', 'True'): False,
            ('grid_tfa_enabled', 'True'): True,
            ('enable_validate_volumes', 'True'): False,
            ('allow_23c_grid_image_download', 'True'): False,
            ('ociexacc', 'True'): False,
        }

        def _check_config(key, value=None):
            if key == 'atp' and value is None:
                return {'enable_namespace': 'False'}
            return config_map.get((key, value), False)

        _ebox = MagicMock()
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mIsExabm.return_value = True
        _ebox.isATP.return_value = True
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mGetMajorityHostVersion.return_value = 'OL7'
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mCopySAPfile.return_value = None
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mRunScript.return_value = (0, 'post.gi_adb_init')

        _step = csExaScaleComplete()
        _step.doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        _ebox.mSetupNamespace.assert_not_called()
        self.assertFalse(any(call.args[0] == 'atp-namespace.x86_64.rpm' for call in _ebox.mUpdateRpm.call_args_list))

    @patch('exabox.ovm.csstep.cs_exascale_complete.ExaKmsHostType')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_installs_namespace_rpm_when_enabled(self, aImageBom, aCluExaScale, aHostType):
        # Auto-generated test for doExecute
        pending = ['RPM_UPDATE']
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', pending)
        aCluExaScale.return_value = MagicMock()
        aHostType.DOMU = 'DOMU'

        config_map = {
            ('install_nosql', 'True'): False,
            ('grid_tfa_enabled', 'True'): True,
            ('enable_validate_volumes', 'True'): False,
            ('allow_23c_grid_image_download', 'True'): False,
            ('ociexacc', 'True'): False,
        }

        def _check_config(key, value=None):
            if key == 'atp' and value is None:
                return {'enable_namespace': 'True'}
            return config_map.get((key, value), False)

        _ebox = MagicMock()
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mIsExabm.return_value = True
        _ebox.isATP.return_value = True
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mGetMajorityHostVersion.return_value = 'OL8'
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mCopySAPfile.return_value = None
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mRunScript.return_value = (0, 'post.gi_adb_init')

        _step = csExaScaleComplete()
        _step.doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        _ebox.mSetupNamespace.assert_called_once_with()
        _ebox.mUpdateRpm.assert_any_call('atp-namespace.x86_64.rpm')

    @patch('exabox.ovm.csstep.cs_exascale_complete.exaBoxNode')
    @patch('exabox.ovm.csstep.cs_exascale_complete.AtpSetupASMListener')
    @patch('exabox.ovm.csstep.cs_exascale_complete.AtpSetupSecondListener')
    @patch('exabox.ovm.csstep.cs_exascale_complete.AtpAddScanname2EtcHosts')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_exabm_atp_listener_flow(self, aImageBom, aCluExaScale, aAddHosts, aSecondListener, aAsmListener, aNodeCls):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['ATP_BACKUP_LISTENER'])
        aCluExaScale.return_value = MagicMock()

        _dom_pairs = [('dom0a', 'domuA'), ('dom0b', 'domuB')]

        def _check_config(key, value=None):
            if key == 'grid_tfa_enabled' and value == 'True':
                return True
            if key == 'install_nosql' and value == 'True':
                return False
            if key == 'allow_23c_grid_image_download' and value == 'True':
                return False
            if key == 'exadbxs_image_base_provisioning_enable' and value == 'True':
                return False
            return False

        _ebox = MagicMock()
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mReturnDom0DomUPair.return_value = _dom_pairs
        _ebox.mIsExabm.return_value = True
        _ebox.isATP.return_value = True
        _ebox.mIsOciEXACC.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.mGetATP.return_value = SimpleNamespace()
        _ebox.mGetMachines.return_value = MagicMock()
        _ebox.mGetNetworks.return_value = MagicMock()
        _ebox.mGetClusters.return_value = MagicMock()
        _ebox.mCheckClusterNetworkType.return_value = True
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mRunScript.return_value = (0, 'mocked')

        class _MockNode:
            def __init__(self):
                self._exists = False
                self.executed = []

            def mConnect(self, aHost):
                return None

            def mFileExists(self, _path):
                return self._exists

            def mExecuteCmd(self, _cmd):
                self.executed.append(_cmd)
                return None, None, None

            def mGetCmdExitStatus(self):
                return 0

            def mDisconnect(self):
                return None

        _nodes = {}

        def _node_factory(*_args, **_kwargs):
            node = _MockNode()
            _nodes[len(_nodes)] = node
            return node

        aNodeCls.side_effect = _node_factory

        _step = csExaScaleComplete()
        _step.doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        _ebox.mCheckClusterNetworkType.assert_called_once_with()
        _ebox.mGetATP.assert_called()
        self.assertGreaterEqual(len(aAddHosts.mock_calls), len(_dom_pairs))
        aSecondListener.assert_called_once()
        aAsmListener.assert_called_once_with(None, _ebox, None)

    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_force_dbcs_auth_enabled(self, aImageBom):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['DBCS_AGENT_UPDATE'])

        def _check_config(key, value=None):
            config_map = {
                ('grid_tfa_enabled', 'True'): True,
                ('install_nosql', 'True'): False,
                ('allow_23c_grid_image_download', 'True'): False,
                ('enable_validate_volumes', 'True'): False,
                ('force_install_dbcs_agent', 'exacc'): False,
                ('force_dbcsagent_auth', 'True'): True,
            }
            return config_map.get((key, value), False)

        _ebox = MagicMock()
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mGetMajorityHostVersion.return_value = 'OL7'
        _ebox.mIsExabm.return_value = True
        _ebox.mIsOciEXACC.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.isATP.return_value = False
        _ebox.mEnvTarget.return_value = False
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mUpdateRpm = MagicMock()
        _ebox.mEnableNoAuthDBCS = MagicMock()
        _ebox.mCopySAPfile.return_value = None
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mRunScript.return_value = (0, 'mocked')

        csExaScaleComplete().doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        _ebox.mUpdateRpm.assert_any_call('dbcs-agent.OL7.x86_64.rpm')
        _ebox.mEnableNoAuthDBCS.assert_called_once_with()

    @patch('exabox.ovm.csstep.cs_exascale_complete.time.sleep', return_value=None)
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebAtpUtils')
    @patch('exabox.ovm.csstep.cs_exascale_complete.AtpSetupASMListener')
    @patch('exabox.ovm.csstep.cs_exascale_complete.AtpSetupSecondListener')
    @patch('exabox.ovm.csstep.cs_exascale_complete.AtpAddScanname2EtcHosts')
    @patch('exabox.ovm.csstep.cs_exascale_complete.exaBoxNode')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_repairs_cellkey_permissions(self, aImageBom, aCluExaScale, aNodeCls,
                                                   aAddHosts, aSecondListener, aAsmListener,
                                                   aAtpUtils, _aSleep):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['ATP_BACKUP_LISTENER'])
        aCluExaScale.return_value = MagicMock()

        _add_hosts = MagicMock()
        _add_hosts.mExecute.return_value = None
        aAddHosts.return_value = _add_hosts

        _second_listener = MagicMock()
        _second_listener.mExecute.return_value = None
        aSecondListener.return_value = _second_listener

        _asm_listener = MagicMock()
        _asm_listener.mExecute.return_value = None
        aAsmListener.return_value = _asm_listener

        aAtpUtils.setScanFqdn = MagicMock()

        _dom_pairs = [('dom0a', 'domuA'), ('dom0b', 'domuB')]

        def _check_config(key, value=None):
            config_map = {
                ('grid_tfa_enabled', 'True'): True,
                ('install_nosql', 'True'): False,
                ('allow_23c_grid_image_download', 'True'): False,
                ('exadbxs_image_base_provisioning_enable', 'True'): False,
            }
            return config_map.get((key, value), False)

        class _FakeNode:

            def __init__(self):
                self.commands = []
                self.host = None

            def mConnect(self, aHost=None):
                self.host = aHost

            def mFileExists(self, aPath):
                return aPath == '/etc/oracle/cell/network-config/cellkey.ora'

            def mExecuteCmd(self, aCmd):
                self.commands.append(aCmd)
                return None, None, None

            def mDisconnect(self):
                return None

        _created_nodes = []

        def _node_factory(*_args, **_kwargs):
            _node = _FakeNode()
            _created_nodes.append(_node)
            return _node

        aNodeCls.side_effect = _node_factory

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = _dom_pairs
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mIsExabm.return_value = True
        _ebox.isATP.return_value = True
        _ebox.mIsOciEXACC.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.mCheckClusterNetworkType.return_value = True
        _ebox.mGetATP.return_value = SimpleNamespace()
        _ebox.mGetMachines.return_value = MagicMock()
        _ebox.mGetNetworks.return_value = MagicMock()
        _ebox.mGetClusters.return_value = MagicMock()
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mDropPmemlogs = MagicMock()
        _ebox.mCopySAPfile.return_value = None
        _ebox.mRunScript.return_value = (0, 'mocked')
        _ebox.mIsDebug.return_value = False

        _options = SimpleNamespace(jsonconf=None)

        csExaScaleComplete().doExecute(_ebox, _options, [])

        self.assertEqual(len(_created_nodes), len(_dom_pairs))
        for _node in _created_nodes:
            self.assertIn('chmod 640 /etc/oracle/cell/network-config/cellkey.ora', _node.commands)
        _ebox.mDropPmemlogs.assert_called_once_with(_options)
        aAtpUtils.setScanFqdn.assert_called_once_with(_dom_pairs)

    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessStructure', new=_InlineProcessStructure)
    @patch('exabox.ovm.csstep.cs_exascale_complete.ProcessManager', new=_InlineProcessManager)
    @patch('exabox.ovm.csstep.cs_exascale_complete.exaBoxNode')
    @patch('exabox.ovm.csstep.cs_exascale_complete.node_cmd_abs_path_check')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogError')
    def test_maxDistanceUpdate_logs_error_on_chronyd_restart(self, aLogError, aNodeCmd, aNodeCls):
        # Auto-generated test for maxDistanceUpdate
        aNodeCmd.side_effect = lambda *_args, **_kwargs: _args[1]

        class _ChronydFailureNode(MagicMock):

            def __init__(self):
                super().__init__()
                self._statuses = [0, 0, 1]
                self.commands = []

            def mConnect(self, aHost=None):
                return None

            def mFileExists(self, aPath):
                return aPath == '/etc/chrony.conf'

            def mExecuteCmdLog(self, aCmd):
                self.commands.append(aCmd)
                return None

            def mGetCmdExitStatus(self):
                if self._statuses:
                    return self._statuses.pop(0)
                return 1

            def mDisconnect(self):
                return None

        aNodeCls.return_value = _ChronydFailureNode()

        _ebox = MagicMock()
        _ebox.mReturnAllClusterHosts.return_value = (['dom0a'], [], [], [])

        csExaScaleComplete().maxDistanceUpdate(_ebox)

        self.assertTrue(aNodeCls.return_value.commands)
        self.assertIn('systemctl restart chronyd', aNodeCls.return_value.commands)
        aLogError.assert_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.csExaScaleComplete.maxDistanceUpdate')
    @patch('exabox.ovm.csstep.cs_exascale_complete.csExaScaleComplete.mSeedOCIDonDomU')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_maxdistance_success(self, aImageBom, aSeedOcid, aMaxDistance):
        # Auto-generated test for doExecute
        pending = ['ADDITIONAL_DOMU_CHECKS']
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', pending)

        _ebox = MagicMock()
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mReturnAllClusterHosts.return_value = (['dom0a'], ['domuA'], [], [])
        _ebox.mStoreDomUInterconnectIps.return_value = None
        _ebox.isATP.return_value = False
        _ebox.mIsExabm.return_value = False
        _ebox.mIsOciEXACC.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.mAddXsPingTargets.return_value = None
        _ebox.mCheckConfigOption.side_effect = lambda *args, **kwargs: False
        _ebox.mCopySAPfile.return_value = None
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None
        _ebox.mRunScript.return_value = (0, 'mocked')

        csExaScaleComplete().doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        aMaxDistance.assert_called_once_with(_ebox)
        aSeedOcid.assert_called_once()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebLogError')
    @patch('exabox.ovm.csstep.cs_exascale_complete.node_cmd_abs_path_check')
    @patch('exabox.ovm.csstep.cs_exascale_complete.get_gcontext')
    @patch('exabox.ovm.csstep.cs_exascale_complete.exaBoxNode')
    def test_mSeedOCIDonDomU_updates_existing_seed_file(self, aNodeCls, aGetContext, aCmdCheck, aLogError):
        # Auto-generated test for mSeedOCIDonDomU
        _context = MagicMock()
        aGetContext.return_value = _context
        aCmdCheck.side_effect = lambda *_args, **_kwargs: _args[1]

        class _FakeNode:

            def __init__(self):
                self._commands = []

            def mConnect(self, aHost):
                self._host = aHost

            def mFileExists(self, _path):
                return True

            def mExecuteCmd(self, aCmd):
                self._commands.append(aCmd)
                return None, None, None

            def mGetCmdExitStatus(self):
                return 0

            def mDisconnect(self):
                return None

        _node = _FakeNode()
        aNodeCls.return_value = _node

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]

        _options = SimpleNamespace(jsonconf={'vmClusterOcid': 'ocid-test'})

        csExaScaleComplete().mSeedOCIDonDomU(_ebox, _options)

        self.assertTrue(_node._commands)
        self.assertIn("sed -i '/d' /var/opt/oracle/exacc.props", _node._commands[0])
        self.assertIn("vmcluster_ocid=ocid-test", _node._commands[0])
        aLogError.assert_not_called()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluUtils')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_sets_up_customer_root_ca_for_exacc(self, aImageBom, aCluExaScale, aCluUtils):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['SECURE_DBCSAGENT'])
        aCluExaScale.return_value = MagicMock()
        _clu_utils = MagicMock()
        aCluUtils.return_value = _clu_utils

        _config_map = {
            ('grid_tfa_enabled', 'True'): True,
            ('install_nosql', 'True'): False,
            ('allow_23c_grid_image_download', 'True'): False,
            ('enable_validate_volumes', 'True'): False,
            ('ociexacc', 'True'): True,
        }

        def _check_config(aKey, aValue=None):
            if aValue is None:
                return False
            return _config_map.get((aKey, aValue), False)

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mIsExabm.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.mIsOciEXACC.return_value = True
        _ebox.isATP.return_value = False
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mSetupDomUsForSecureDBCSCommunication = MagicMock()
        _ebox.mAddAgentWallet = MagicMock()
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None

        csExaScaleComplete().doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        _ebox.mSetupDomUsForSecureDBCSCommunication.assert_called_once_with()
        _ebox.mAddAgentWallet.assert_called_once_with()
        _clu_utils.mSetupCustomerRootCACertificates.assert_called_once_with()

    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluUtils')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ebCluExaScale')
    @patch('exabox.ovm.csstep.cs_exascale_complete.ImageBOM')
    def test_doExecute_skips_customer_root_ca_for_non_exacc(self, aImageBom, aCluExaScale, aCluUtils):
        # Auto-generated test for doExecute
        aImageBom.return_value = _FakeImageBom('ESTP_EXASCALE_COMPLETE', ['SECURE_DBCSAGENT'])
        aCluExaScale.return_value = MagicMock()
        _clu_utils = MagicMock()
        aCluUtils.return_value = _clu_utils

        _config_map = {
            ('grid_tfa_enabled', 'True'): True,
            ('install_nosql', 'True'): False,
            ('allow_23c_grid_image_download', 'True'): False,
            ('enable_validate_volumes', 'True'): False,
            ('ociexacc', 'True'): False,
        }

        def _check_config(aKey, aValue=None):
            if aValue is None:
                return False
            return _config_map.get((aKey, aValue), False)

        _ebox = MagicMock()
        _ebox.mReturnDom0DomUPair.return_value = [('dom0a', 'domuA')]
        _ebox.mCheckConfigOption.side_effect = _check_config
        _ebox.mIsExabm.return_value = False
        _ebox.mIsExacm.return_value = False
        _ebox.mIsOciEXACC.return_value = False
        _ebox.isATP.return_value = False
        _ebox.mUpdateStatus.return_value = None
        _ebox.mUpdateStatusCS.return_value = None
        _ebox.mLogStepElapsedTime.return_value = None
        _ebox.mSetupDomUsForSecureDBCSCommunication = MagicMock()
        _ebox.mAddAgentWallet = MagicMock()
        _ebox.mDropPmemlogs.return_value = None
        _ebox.mATPUnlockListeners.return_value = None

        csExaScaleComplete().doExecute(_ebox, SimpleNamespace(jsonconf=None), [])

        _ebox.mSetupDomUsForSecureDBCSCommunication.assert_not_called()
        _ebox.mAddAgentWallet.assert_not_called()
        _clu_utils.mSetupCustomerRootCACertificates.assert_not_called()

if __name__ == "__main__":
    unittest.main()
