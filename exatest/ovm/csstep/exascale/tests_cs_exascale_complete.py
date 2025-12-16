#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/exascale/tests_cs_exascale_complete.py /main/7 2025/10/31 17:31:05 bhpati Exp $
#
# tests_cs_exascale_complete.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
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
#    bhpati      10/20/25 - Bug 38490905 - OCI: ExaDB-D on exascale
#                           provisioning fails if ICMP ingress is not open on
#                           client network
#    pbellary    05/26/25 - Enh 37768130 - SUPPORT RESHAPE/RESIZE FOR THE ACFS FILESYSTEM CREATED ON EXASCALE CLUSTERS 
#    pbellary    05/26/25 - Creation
#
import re
import json
import copy
import time
import unittest
from unittest import mock
import hashlib
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.csstep.exascale.exascaleutils import *
from exabox.ovm.csstep.exascale.escli_util import *
from exabox.ovm.csstep.exascale.cs_exascale_complete import *
from exabox.core.Context import get_gcontext
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
import warnings

EXASCALE_PAYLOAD = """ 
{
   "exascale":{
      "cell_list":[
         "scaqab10celadm01.us.oracle.com",
         "scaqab10celadm02.us.oracle.com",
         "scaqab10celadm03.us.oracle.com"
      ],
      "exascale_cluster_name":"sea2d2cl37541fe175f7847febc200f6b51aa9cb3clu01ers",
      "storage_pool":{
         "name":"hcpool",
         "gb_size":"10240"
      },
      "db_vault":{
         "name":"vault1clu02",
         "gb_size":10
      },
      "ctrl_network":{
         "ip":"10.0.130.110",
         "port":"5052",
         "name":"sea201507exdcl13ers01.sea2xx2xx0051qf.adminsea2.oraclevcn.com"
      }
    }
}
"""

class ebTestExascaleComplete(ebTestClucontrol):

   @classmethod
   def setUpClass(self):
        super(ebTestExascaleComplete, self).setUpClass(aGenerateDatabase = True, aUseOeda = True)
        self.mGetClubox(self).mSetUt(True)
        warnings.filterwarnings("ignore")

   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mAlterVolumeAccess')
   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mUpdateACL')
   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mConfigureEDVbackup')
   @patch('exabox.ovm.csstep.exascale.cs_exascale_complete.mUpdateListenerPort')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mStartVMExacsService')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateVmetrics')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRemoveCloudPropertiesPayload')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mEnableTFABlackout')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mATPUnlockListeners')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mEnableRemotePwdChange')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateCloudUser')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetWalletEntry')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCopyOneoffZipToDomus')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCopyCreateVIP')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mHandlerGenerateSwitchesKeys')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mResetClusterSSHKeys')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mMakeFipsCompliant', return_value=(0, "ok"))
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateHugepagesForCluster')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSaveClusterDomUList')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRemoveDatabaseMachineXmlDomU')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mStoreDomUInterconnectIps')
   @patch('exabox.ovm.csstep.cs_util.csUtil.mInstallAhfonDomU')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mSetOraInventoryPermissions')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateRpm')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCopySAPfile')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mAddUserPubKey')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCopyVmexacsRpm')
   @patch('exabox.ovm.csstep.cs_util.csUtil.mExecuteOEDAStep')
   @patch('exabox.ovm.cluencryption.isEncryptionRequested', return_value=False)
   @patch('exabox.ovm.cluencryption.resizeEncryptedVolume')
   @patch('exabox.ovm.csstep.exascale.cs_exascale_complete.expand_domu_filesystem')
   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mCreateDefaultAcfs')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mCheckCrsIsUp')
   def test_doExecute(self, mock_mCreateDefaultAcfs, mock_expand_domu_filesystem, mock_resizeEncryptedVolume, 
            mock_isEncryptionRequested, mock_mExecuteOEDAStep, mock_mCopyVmexacsRpm, mock_mAddUserPubKey,
            mock_mCopySAPfile, mock_mUpdateRpm, mock_mSetOraInventoryPermissions, mock_mInstallAhfonDomU,
            mock_mStoreDomUInterconnectIps, mock_mRemoveDatabaseMachineXmlDomU, mock_mSaveClusterDomUList,
            mock_mUpdateHugepagesForCluster, mock_mMakeFipsCompliant, mock_mResetClusterSSHKeys,
            mock_mHandlerGenerateSwitchesKeys, mock_mCopyCreateVIP, mock_mCopyOneoffZipToDomus,
            mock_mSetWalletEntry, mock_mUpdateCloudUser, mock_mEnableRemotePwdChange,
            mock_mATPUnlockListeners, mock_mEnableTFABlackout,
            mock_mRemoveCloudPropertiesPayload, mock_mUpdateVmetrics, mock_mStartVMExacsService, 
            mock_mUpdateListenerPort, mock_mConfigureEDVbackup, mock_mUpdateACL, mock_mAlterVolumeAccess, mock_mCheckCrsIsUp):
      _ebox = self.mGetClubox()
      _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
      _step_list = ["ESTP_EXASCALE_COMPLETE"]
      _ebox.mSetEnableKVM(True)
      _ebox.mSetCmd("createservice")
      _cmds = {
                    self.mGetRegexVm():
                        [
                            [
                                exaMockCommand(re.escape("/var/opt/oracle/dbaas_acfs"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/usr/bin/dbaascli admin initializeCluster"), aRc=0, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/usr/bin/dbaascli admin initializeCluster"), aRc=0, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/usr/bin/dbaascli admin initializeCluster"), aRc=0, aPersist=True)
                            ]
                        ]
                }
      self.mPrepareMockCommands(_cmds)

      get_gcontext().mSetConfigOption('enable_vmexacs_kvm',"True")

      with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleLinuxVersion', return_value="OL8"):
          _handler = csExaScaleComplete()
          _handler.doExecute(_ebox, _options, _step_list)

      _ebox.mSetCmd("vmgi_reshape")
      _cmds = {
                    self.mGetRegexVm():
                        [
                            [
                                exaMockCommand(re.escape("/var/opt/oracle/dbaas_acfs"), aRc=0, aPersist=True),
                                exaMockCommand(re.escape("/usr/bin/dbaascli admin initializeCluster"), aRc=0, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/usr/bin/dbaascli admin initializeCluster"), aRc=0, aPersist=True)
                            ],
                            [
                                exaMockCommand(re.escape("/usr/bin/dbaascli admin initializeCluster"), aRc=0, aPersist=True)
                            ]
                        ]
                }
      self.mPrepareMockCommands(_cmds)

      with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleLinuxVersion', return_value="OL8"):
          _handler = csExaScaleComplete()
          _handler.doExecute(_ebox, _options, _step_list)

   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateRpm')
   @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost')
   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mRemoveACFS')
   @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mRemoveDefaultAcfsVolume')
   def test_undoExecute(self, mock_mRemoveDefaultAcfsVolume, mock_mRemoveACFS, mock_mPingHost,
                        mock_mUpdateRpm):
      _ebox = self.mGetClubox()
      _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
      _step_list = ["ESTP_EXASCALE_COMPLETE"]

      with patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleLinuxVersion', return_value="OL8"):
         _handler = csExaScaleComplete()
         _handler.undoExecute(_ebox, _options, _step_list)

if __name__ == '__main__':
    unittest.main()
