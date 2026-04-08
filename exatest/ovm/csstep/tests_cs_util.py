#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/csstep/tests_cs_util.py /main/4 2025/10/27 04:36:02 pbellary Exp $
#
# tests_cs_util.py
#
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
#
#    NAME
#      tests_cs_util.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    03/13/26 - Bug 39002144 - EXADB-XS-PP: VMC PROVISION GOT STUCK
#                           AT THE STEP OF AWAIT_ADD_SSH_KEYS | EXACLOUD DOES
#                           NOT ENSURE AGENT SYSTEMD SERVICE IS UP AFTER
#                           PROVISIONING
#    rajsag      07/21/25 - Creation
#
import json
import copy
import unittest
from unittest.mock import Mock, patch
from exabox.core.MockCommand import exaMockCommand
from exabox.ovm.csstep.cs_util import csUtil
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.csstep.exascale.exascaleutils import ebExascaleUtils
from exabox.ovm.csstep.cs_constants import csConstants, csXSConstants, csXSEighthConstants, csBaseDBXSConstants, csAsmEDVConstants
from exabox.utils.node import connect_to_host
from exabox.core.Context import get_gcontext

CREATE_SERVICE_PAYLOAD = """ 
{
   "exascale":{
      "network_services":{
         "dns":[
            "169.254.169.254"
         ],
         "ntp":[
            "169.254.169.254"
         ]
      },
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
    },
   "rack":{
      "storageType":"XS",
      "xsVmImage": "True",
      "xsVmBackup": "True",
      "system_vault": [
            {
                "vault_type":"image",
                "name":"imagevault"
            },
             {
                "vault_type":"backup",
                "name":"backupvault",
                "xsVmBackupRetentionNum": "2"
            }
      ]
   }
}
"""

class TestCsUtil(ebTestClucontrol):

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mIsXS', return_value=True)
    @patch('exabox.ovm.csstep.exascale.exascaleutils.ebExascaleUtils.mGetRackSize', return_value="eighthrack")
    def test_mGetConstants_xs_eighth(self, mock_mGetRackSize, mock_mIsXS):
        # Arrange
        ebox = self.mGetClubox()
        ebox.mSetEnableKVM(True)
        cs_util = csUtil()

        # Act
        result = cs_util.mGetConstants(ebox)

        # Assert
        self.assertEqual(result, csXSEighthConstants)

    def test_mGetConstants_asm_edv(self):
        # Arrange
        _ebox = self.mGetClubox()
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = json.loads(CREATE_SERVICE_PAYLOAD)
        _ebox.mSetEnableKVM(True)

        _utils = ebExascaleUtils(_ebox)
        _status = _utils.mIsEDVImageSupported(_options)
        cs_util = csUtil()

        # Act
        result = cs_util.mGetConstants(_ebox, _options)

        # Assert
        self.assertEqual(result, csAsmEDVConstants)

    def test_mGetConstants_xs_not_eighth(self):
        # Arrange
        ebox = Mock()
        ebox.mIsXS.return_value = True
        ebox.mGetRackSize.return_value = 'not_eighth'
        cs_util = csUtil()

        # Act
        result = cs_util.mGetConstants(ebox)

        # Assert
        self.assertEqual(result, csXSConstants)

    def test_mGetConstants_base_db(self):
        # Arrange
        ebox = Mock()
        ebox.mIsXS.return_value = False
        ebox.isBaseDB.return_value = True
        ebox.isExacomputeVM.return_value = False
        base_db = Mock()
        ebox.mGetBaseDB.return_value = base_db
        cs_util = csUtil()

        # Act
        result = cs_util.mGetConstants(ebox)

        # Assert
        self.assertEqual(result, csBaseDBXSConstants)
        base_db.mUpdateOedaPropertiesInterface.assert_called_once()

    def test_mGetConstants_exacompute_vm(self):
        # Arrange
        ebox = Mock()
        ebox.mIsXS.return_value = False
        ebox.isBaseDB.return_value = False
        ebox.isExacomputeVM.return_value = True
        base_db = Mock()
        ebox.mGetBaseDB.return_value = base_db
        cs_util = csUtil()

        # Act
        result = cs_util.mGetConstants(ebox)

        # Assert
        self.assertEqual(result, csBaseDBXSConstants)
        base_db.mUpdateOedaPropertiesInterface.assert_called_once()

    def test_mGetConstants_default(self):
        # Arrange
        ebox = Mock()
        ebox.mIsXS.return_value = False
        ebox.isBaseDB.return_value = False
        ebox.isExacomputeVM.return_value = False
        cs_util = csUtil()

        # Act
        result = cs_util.mGetConstants(ebox)

        # Assert
        self.assertEqual(result, csConstants)

    def test_mGetConstants_check_base_db_false(self):
        # Arrange
        ebox = Mock()
        ebox.mIsXS.return_value = False
        ebox.isBaseDB.return_value = True
        ebox.isExacomputeVM.return_value = False
        base_db = Mock()
        ebox.mGetBaseDB.return_value = base_db
        cs_util = csUtil()

        # Act
        result = cs_util.mGetConstants(ebox, aCheckBaseDb=False)

        # Assert
        self.assertEqual(result, csConstants)
        base_db.mUpdateOedaPropertiesInterface.assert_not_called()

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mOEDASkipPassProperty')
    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mUpdateOEDAProperties')
    def test_mUpdateOEDAConfiguration(self, mock_mUpdateOEDAProperties, mock_mOEDASkipPassProperty):
        _ebox = self.mGetClubox()
        cs_util = csUtil()
        cs_util.mUpdateOEDAConfiguration(_ebox, self.mGetClubox().mGetArgsOptions())

    @patch('exabox.ovm.csstep.cs_util.time.sleep')
    def test_mStartServiceInNode_restarts_service(self, aMockSleep):
        cs_util = csUtil()
        service_name = "unit-test-service"

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/test -e /sbin/systemctl", aPersist=True),
                    exaMockCommand(f"systemctl stop {service_name}", aPersist=True),
                    exaMockCommand(f"systemctl start {service_name}", aPersist=True),
                    exaMockCommand(f"systemctl is-active {service_name}", aPersist=True),
                ],
            ],
        }


        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _domU = _ebox.mReturnDom0DomUPair()[0][1]

        with connect_to_host(_domU, get_gcontext()) as _node:
            _res = cs_util.mStartServiceInNode(_node, service_name)

        self.assertTrue(aMockSleep.called)
        self.assertIsNone(_res)

    def test_mSetupDBCSAgentAuth(self):
        cs_util = csUtil()

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/opt/oracle/dcs/bin/setupAuthDcs.py"),
                    exaMockCommand("/bin/test -e /sbin/systemctl", aPersist=True),
                    exaMockCommand(f"systemctl stop dbcsagent", aPersist=True),
                    exaMockCommand(f"systemctl start dbcsagent", aPersist=True),
                    exaMockCommand(f"systemctl is-active dbcsagent", aPersist=True),
                    exaMockCommand(f"systemctl stop dbcsadmin", aPersist=True),
                    exaMockCommand(f"systemctl start dbcsadmin", aPersist=True),
                    exaMockCommand(f"systemctl is-active dbcsadmin", aPersist=True),
                ],
            ],
        }


        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _dom0_domU_pairs = _ebox.mReturnDom0DomUPair()

        _res = cs_util.mSetupDBCSAgentAuth(_dom0_domU_pairs)

        self.assertIsNone(_res)

    def test_mSetupDBCSAgentAuth_first_start_fails(self):
        cs_util = csUtil()

        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/opt/oracle/dcs/bin/setupAuthDcs.py"),
                    exaMockCommand("/bin/test -e /sbin/systemctl", aPersist=True),
                    exaMockCommand(f"systemctl stop dbcsagent", aPersist=True),
                    exaMockCommand(f"systemctl start dbcsagent", aPersist=True),
                    exaMockCommand(f"systemctl is-active dbcsagent", aPersist=True),

                    exaMockCommand(f"systemctl stop dbcsadmin", aPersist=True),
                    exaMockCommand(f"systemctl start dbcsadmin", aPersist=True),
                    exaMockCommand(f"systemctl is-active dbcsadmin", aRc=1),## Here we mock an error
                    exaMockCommand(f"systemctl is-active dbcsadmin", aRc=0), ## Here we mock a subsequent success
                ],
            ],
        }


        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _dom0_domU_pairs = _ebox.mReturnDom0DomUPair()

        _res = cs_util.mSetupDBCSAgentAuth(_dom0_domU_pairs)

        self.assertIsNone(_res)

if __name__ == '__main__':
    unittest.main()
