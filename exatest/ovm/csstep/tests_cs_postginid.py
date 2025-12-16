#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/tests_cs_postginid.py /main/2 2025/09/10 15:17:42 scoral Exp $
#
# tests_cs_driver.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_driver.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    pbellary    08/20/25 - Creation
#
import unittest
import copy, re
from unittest.mock import patch, MagicMock

from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.exatest.common.ebExacloudUtil import *
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.csstep.cs_postginid import csPostGINID
from exabox.ovm.csstep.cs_util import csUtil

class testOptions(object): pass

class ebTestcsPostGINID(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestcsPostGINID, self).setUpClass(aGenerateDatabase=True)

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mDropPmemlogs')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mStartVMExacsService')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateVmetrics')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mEnableTFABlackout')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mATPUnlockListeners')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mExecuteCRSReboot')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mEnableRemotePwdChange')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateCloudUser')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mHandlerGenerateSwitchesKeys')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mResetClusterSSHKeys')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateHugepagesForCluster')
    @patch('exabox.ovm.csstep.cs_base.CSBase.mSanitizeDomUSysctlConf')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRemoveDatabaseMachineXmlDomU')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mStoreDomUInterconnectIps')
    @patch('exabox.ovm.csstep.cs_util.csUtil.mInstallAhfonDomU')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateRpm')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetMajorityHostVersion', return_value="OL8")
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mEnableNoAuthDBCS')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mApplyExtraSrvctlConfig')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCopySAPfile')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mAddUserPubKey')
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRemoveCloudPropertiesPayload")
    @patch('exabox.ovm.csstep.cs_postginid.mUpdateListenerPort')
    @patch('exabox.ovm.csstep.cs_postginid.executeOCDEInitOnDomUs', return_value=0)
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mPushCloudPropertiesPayload")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mPrepareCloudPropertiesPayload")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mGetExadataDom0Model", return_value="X6")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCopyVmexacsRpm")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRunScript", return_value=(0, ""))
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckAsmIsUp")
    @patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCrsIsUp")
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSaveCellInformation')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mAddOratabEntry')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSaveClusterDomUList')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateStatusCS')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mReleaseRemoteLock')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mAcquireRemoteLock')
    @patch('exabox.ovm.csstep.cs_util.csUtil.mExecuteOEDAStep')
    @patch('exabox.ovm.csstep.cs_postginid.expand_domu_filesystem')
    def test_doExecute(self, mock_expand_domu_filesystem, mock_mExecuteOEDAStep, mock_mAcquireRemoteLock,
                       mock_mReleaseRemoteLock, mock_mUpdateStatusCS, mock_mSaveClusterDomUList,
                       mock_mAddOratabEntry, mock_mSaveCellInformation, mock_mCheckCrsIsUp, mock_mCheckAsmIsUp,
                       mock_mRunScript, mock_mCopyVmexacsRpm, mock_mGetExadataDom0Model, mock_mPrepareCloudPropertiesPayload,
                       mock_mPushCloudPropertiesPayload, mock_executeOCDEInitOnDomUs, mock_mUpdateListenerPort,
                       mock_mRemoveCloudPropertiesPayload, mock_mAddUserPubKey, mock_mCopySAPfile,
                       mock_mApplyExtraSrvctlConfig, mock_mEnableNoAuthDBCS, mock_mGetMajorityHostVersion,
                       mock_mUpdateRpm, mock_mInstallAhfonDomU, mock_mStoreDomUInterconnectIps,
                       mock_mRemoveDatabaseMachineXmlDomU, mock_mSanitizeDomUSysctlConf, mock_mUpdateHugepagesForCluster,
                       mock_mResetClusterSSHKeys, mock_mHandlerGenerateSwitchesKeys, mock_mUpdateCloudUser,
                       mock_mEnableRemotePwdChange, mock_mExecuteCRSReboot, mock_mATPUnlockListeners, mock_mEnableTFABlackout,
                       mock_mUpdateVmetrics, mock_mStartVMExacsService, mock_mDropPmemlogs):
      _ebox = self.mGetClubox()
      _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
      _step_list = ["ESTP_POSTGI_NID"]
      _cmds = {
                    self.mGetRegexVm():
                        [
                            [   
                                exaMockCommand("/bin/test -e *", aRc=0, aPersist=True),
                                exaMockCommand("/bin/scp *", aRc=0, aPersist=True),
                                exaMockCommand("/bin/sh *", aRc=0, aPersist=True),
                                exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                                exaMockCommand(re.escape("/var/opt/oracle/dbaas_acfs"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/usr/bin/dbaascli admin initializeCluster"), aRc=0, aPersist=True),
                                exaMockCommand("/bin/chmod *", aRc=0, aPersist=True)
                            ],
                            [
                                exaMockCommand("/bin/chmod *", aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/usr/bin/dbaascli admin initializeCluster"), aRc=0, aPersist=True),
                                exaMockCommand("/bin/test -e *", aRc=0, aPersist=True),
                                 exaMockCommand("chmod *", aRc=0, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/etc/oracle/cell/network-config/cellkey.ora"), aRc=1, aPersist=True),
                                exaMockCommand(re.escape("/usr/bin/dbaascli admin initializeCluster"), aRc=0, aPersist=True)
                            ]
                        ]
                }
      self.mPrepareMockCommands(_cmds)

      _handler = csPostGINID()
      _handler.doExecute(_ebox, _options, _step_list)


    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetMajorityHostVersion', return_value="OL8")
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateRpm')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateStatusCS')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mReleaseRemoteLock')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mAcquireRemoteLock')
    @patch('exabox.ovm.csstep.cs_util.csUtil.mExecuteOEDAStep')
    def test_undoExecute(self, mock_mExecuteOEDAStep, mock_mAcquireRemoteLock,
                       mock_mReleaseRemoteLock, mock_mUpdateStatusCS, mock_mUpdateRpm, mock_mGetMajorityHostVersion):
      _ebox = self.mGetClubox()
      _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
      _step_list = ["ESTP_POSTGI_NID"]
      _cmds = {
                    self.mGetRegexVm():
                        [
                            [   
                                exaMockCommand("/bin/test -e *", aRc=0, aPersist=True),
                                exaMockCommand("/bin/scp *", aRc=0, aPersist=True),
                                exaMockCommand("/bin/sh *", aRc=0, aPersist=True),
                                exaMockCommand("/bin/mkdir -p *", aRc=0, aStdout="" ,aPersist=True),
                                exaMockCommand(re.escape("/var/opt/oracle/dbaas_acfs"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/usr/bin/dbaascli admin initializeCluster"), aRc=0, aPersist=True),
                                exaMockCommand("/bin/chmod *", aRc=0, aPersist=True)
                            ],
                            [
                                exaMockCommand("/bin/chmod *", aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/usr/bin/dbaascli admin initializeCluster"), aRc=0, aPersist=True),
                                exaMockCommand("/bin/test -e *", aRc=0, aPersist=True),
                                 exaMockCommand("chmod *", aRc=0, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/etc/oracle/cell/network-config/cellkey.ora"), aRc=1, aPersist=True),
                                exaMockCommand(re.escape("/usr/bin/dbaascli admin initializeCluster"), aRc=0, aPersist=True)
                            ]
                        ]
                }
      self.mPrepareMockCommands(_cmds)

      _handler = csPostGINID()
      _handler.undoExecute(_ebox, _options, _step_list)

if __name__ == '__main__':
    unittest.main()